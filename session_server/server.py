"""
会话管理服务器 - 处理登录、注册、会话管理和邀请码功能
使用 FastAPI + SQLite（会话） + 阿里云MySQL（用户验证）
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sqlite3
import uuid
import hashlib
import secrets
import os
from contextlib import contextmanager
import pymysql
from urllib.parse import quote_plus

# FastAPI 应用
app = FastAPI(title="Protein Screening Session Server", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
DATABASE_PATH = "sessions.db"
SESSION_TIMEOUT_MINUTES = 3  # 3分钟没有心跳则认为掉线
INVITE_CODE_MAX_USES = 30  # 每个邀请码最多使用30次

# 阿里云数据库配置
ALIYUN_DB_CONFIG = {
    'host': 'defectgene-new.mysql.polardb.rds.aliyuncs.com',
    'port': 3306,
    'user': 'defect_genetic_checking',
    'password': 'Jaybz@890411',
    'database': 'bull_library',
    'charset': 'utf8mb4'
}

# 数据模型
class LoginRequest(BaseModel):
    username: str
    password: str
    device_id: str
    force_login: Optional[bool] = False

class RegisterRequest(BaseModel):
    username: str  # 工号作为用户名
    password: str
    invite_code: str
    name: str  # 姓名

class HeartbeatRequest(BaseModel):
    username: str
    device_id: str
    session_token: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    session_token: Optional[str] = None
    need_force_login: Optional[bool] = False
    existing_device: Optional[str] = None

class RegisterResponse(BaseModel):
    success: bool
    message: str

# 数据库连接管理
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 阿里云数据库连接
def get_aliyun_connection():
    """获取阿里云数据库连接"""
    print(f"正在连接阿里云数据库: {ALIYUN_DB_CONFIG['host']}, database: {ALIYUN_DB_CONFIG['database']}")
    try:
        connection = pymysql.connect(**ALIYUN_DB_CONFIG)
        print("成功连接到阿里云数据库")
        return connection
    except Exception as e:
        print(f"连接阿里云数据库失败: {e}")
        raise

def verify_aliyun_user(username: str, password: str) -> bool:
    """验证阿里云数据库中的用户"""
    connection = None
    try:
        print(f"尝试验证用户: {username}")
        connection = get_aliyun_connection()
        with connection.cursor() as cursor:
            # 查询 id-pw 表
            sql = "SELECT * FROM `id-pw` WHERE ID=%s AND PW=%s"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()
            if result:
                print(f"用户 {username} 验证成功")
                return True
            else:
                print(f"用户 {username} 验证失败：用户名或密码错误")
                return False
    except pymysql.err.OperationalError as e:
        print(f"数据库连接错误: {e}")
        print("请检查：")
        print("1. 网络是否可以访问阿里云")
        print("2. 数据库配置是否正确")
        print("3. 防火墙是否阻止了连接")
        return False
    except Exception as e:
        print(f"阿里云数据库查询错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if connection:
            connection.close()

# 初始化数据库
def init_database():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 会话表（只存储会话信息，用户信息从阿里云获取）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL,
                device_id VARCHAR(50) NOT NULL,
                session_token VARCHAR(64) NOT NULL,
                login_time DATETIME NOT NULL,
                last_heartbeat DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # 注意：邀请码相关表已迁移到阿里云数据库的 invitation_codes 表

# 辅助函数
def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token() -> str:
    """生成会话令牌"""
    return secrets.token_hex(32)

def check_session_timeout(last_heartbeat: str) -> bool:
    """检查会话是否超时"""
    last_time = datetime.fromisoformat(last_heartbeat)
    return datetime.now() - last_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES)

# API 端点
@app.on_event("startup")
async def startup_event():
    """启动时初始化数据库"""
    init_database()
    # 创建一些测试邀请码
    with get_db() as conn:
        cursor = conn.cursor()
        test_codes = ["TEST2024", "WELCOME123", "BETA2024"]
        for code in test_codes:
            cursor.execute(
                "INSERT OR IGNORE INTO invite_codes (code) VALUES (?)",
                (code,)
            )

@app.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """用户注册 - 在阿里云数据库中创建用户"""
    # 先检查阿里云数据库中是否已存在该用户
    connection = None
    try:
        connection = get_aliyun_connection()
        with connection.cursor() as cursor:
            # 检查用户名是否已存在
            sql = "SELECT ID FROM `id-pw` WHERE ID=%s"
            cursor.execute(sql, (request.username,))
            if cursor.fetchone():
                return RegisterResponse(success=False, message="用户名已存在")
        
        # 检查阿里云邀请码表
        with connection.cursor() as cursor:
            # 检查邀请码
            sql = """
                SELECT code, status, max_uses, current_uses, expire_time 
                FROM invitation_codes 
                WHERE code = %s
            """
            print(f"检查邀请码: {request.invite_code}")
            cursor.execute(sql, (request.invite_code,))
            invite = cursor.fetchone()
            
            if not invite:
                print(f"邀请码 {request.invite_code} 不存在")
                return RegisterResponse(success=False, message="邀请码不存在")
            
            print(f"邀请码信息: code={invite[0]}, status={invite[1]}, max_uses={invite[2]}, current_uses={invite[3]}, expire_time={invite[4]}")
            
            # 检查状态 (1-可用, 2-已使用, 3-已过期)
            if invite[1] != 1:  # status
                status_msg = {2: "已使用", 3: "已过期"}.get(invite[1], f"未知状态({invite[1]})")
                return RegisterResponse(success=False, message=f"邀请码已失效: 状态为{status_msg}")
            
            # 检查过期时间
            if invite[4] and datetime.now() > invite[4]:  # expire_time
                return RegisterResponse(success=False, message=f"邀请码已过期: 过期时间为{invite[4].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检查使用次数
            if invite[3] >= invite[2]:  # current_uses >= max_uses
                return RegisterResponse(success=False, message=f"邀请码使用次数已达上限: 已使用{invite[3]}次，最大使用次数为{invite[2]}次")
        
        # 在阿里云数据库中创建用户
        with connection.cursor() as cursor:
            sql = "INSERT INTO `id-pw` (ID, PW, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (request.username, request.password, request.name))
            connection.commit()
        
        # 更新阿里云邀请码使用记录
        with connection.cursor() as cursor:
            # 更新使用次数
            sql = """
                UPDATE invitation_codes 
                SET current_uses = current_uses + 1,
                    used_at = NOW()
                WHERE code = %s
            """
            cursor.execute(sql, (request.invite_code,))
            
            # 检查是否达到最大使用次数，如果是则更新状态
            sql = """
                UPDATE invitation_codes 
                SET status = 2 
                WHERE code = %s AND current_uses >= max_uses
            """
            cursor.execute(sql, (request.invite_code,))
            connection.commit()
        
        return RegisterResponse(success=True, message="注册成功")
        
    except Exception as e:
        print(f"注册失败: {e}")
        return RegisterResponse(success=False, message=f"注册失败: {str(e)}")
    finally:
        if connection:
            connection.close()

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录 - 使用阿里云数据库验证"""
    try:
        print(f"\n=== 登录请求 ===")
        print(f"用户名: {request.username}")
        print(f"设备ID: {request.device_id}")
        
        # 先验证阿里云数据库中的用户名密码
        if not verify_aliyun_user(request.username, request.password):
            return LoginResponse(success=False, message="用户名或密码错误")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 检查是否有活跃会话
            cursor.execute(
                """SELECT * FROM user_sessions 
                   WHERE username = ? AND is_active = 1""",
                (request.username,)
            )
            existing_session = cursor.fetchone()
            
            if existing_session:
                # 检查是否是同一设备
                if existing_session['device_id'] == request.device_id:
                    # 同一设备，更新会话
                    session_token = existing_session['session_token']
                    cursor.execute(
                        """UPDATE user_sessions 
                           SET last_heartbeat = ? 
                           WHERE id = ?""",
                        (datetime.now().isoformat(), existing_session['id'])
                    )
                    return LoginResponse(
                        success=True,
                        message="登录成功",
                        session_token=session_token
                    )
                else:
                    # 不同设备
                    if not request.force_login:
                        # 询问是否强制登录
                        return LoginResponse(
                            success=False,
                            message="该账号已在其他设备登录",
                            need_force_login=True,
                            existing_device=existing_session['device_id']
                        )
                    else:
                        # 强制登录，使旧会话失效
                        cursor.execute(
                            "UPDATE user_sessions SET is_active = 0 WHERE id = ?",
                            (existing_session['id'],)
                        )
            
            # 创建新会话
            session_token = generate_session_token()
            now = datetime.now().isoformat()
            cursor.execute(
                """INSERT INTO user_sessions 
                   (username, device_id, session_token, login_time, last_heartbeat) 
                   VALUES (?, ?, ?, ?, ?)""",
                (request.username, request.device_id, session_token, now, now)
            )
            
            print(f"登录成功: {request.username}")
            return LoginResponse(
                success=True,
                message="登录成功",
                session_token=session_token
            )
            
    except Exception as e:
        print(f"登录处理异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # 返回500错误而不是502
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@app.post("/heartbeat")
async def heartbeat(request: HeartbeatRequest):
    """心跳更新"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 验证会话
        cursor.execute(
            """SELECT * FROM user_sessions 
               WHERE username = ? AND device_id = ? AND session_token = ? AND is_active = 1""",
            (request.username, request.device_id, request.session_token)
        )
        session = cursor.fetchone()
        
        if not session:
            return {"success": False, "message": "会话无效或已过期", "need_relogin": True}
        
        # 更新心跳时间
        cursor.execute(
            "UPDATE user_sessions SET last_heartbeat = ? WHERE id = ?",
            (datetime.now().isoformat(), session['id'])
        )
        
        return {"success": True, "message": "心跳更新成功"}

@app.post("/logout")
async def logout(username: str, device_id: str, session_token: str):
    """用户登出"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE user_sessions SET is_active = 0 
               WHERE username = ? AND device_id = ? AND session_token = ?""",
            (username, device_id, session_token)
        )
        
        return {"success": True, "message": "登出成功"}

@app.get("/invite-codes")
async def get_invite_codes():
    """获取邀请码列表（管理接口）"""
    connection = None
    try:
        connection = get_aliyun_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT code, max_uses, current_uses, created_at, expire_time, status, remark
                FROM invitation_codes 
                WHERE status IN (1, 2)
                ORDER BY created_at DESC
            """
            cursor.execute(sql)
            codes = []
            for row in cursor.fetchall():
                codes.append({
                    "code": row[0],
                    "max_uses": row[1],
                    "used_count": row[2],
                    "created_at": row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None,
                    "expires_at": row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None,
                    "status": row[5],
                    "remark": row[6],
                    "remaining_uses": row[1] - row[2]
                })
            return {"codes": codes}
    except Exception as e:
        print(f"获取邀请码失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取邀请码失败: {str(e)}")
    finally:
        if connection:
            connection.close()

@app.post("/invite-codes")
async def create_invite_code(code: str, max_uses: int = 30, expires_days: Optional[int] = None, remark: str = ""):
    """创建新邀请码（管理接口）"""
    connection = None
    try:
        connection = get_aliyun_connection()
        with connection.cursor() as cursor:
            # 计算过期时间
            expire_time = None
            if expires_days:
                expire_time = datetime.now() + timedelta(days=expires_days)
            
            sql = """
                INSERT INTO invitation_codes (code, max_uses, expire_time, remark) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (code, max_uses, expire_time, remark))
            connection.commit()
            return {"success": True, "message": "邀请码创建成功"}
    except pymysql.err.IntegrityError:
        raise HTTPException(status_code=400, detail="邀请码已存在")
    except Exception as e:
        print(f"创建邀请码失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建邀请码失败: {str(e)}")
    finally:
        if connection:
            connection.close()

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 DHI筛查助手 - 认证服务器")
    print("=" * 60)
    print(f"服务器地址: http://localhost:8000")
    print(f"健康检查: http://localhost:8000/health")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")