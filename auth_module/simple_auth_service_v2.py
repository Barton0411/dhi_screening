"""
极简认证服务 - 直接连接阿里云数据库，不需要创建新表
"""

import pymysql
import uuid
import json
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

# 阿里云数据库配置
ALIYUN_DB_CONFIG = {
    'host': 'defectgene-new.mysql.polardb.rds.aliyuncs.com',
    'port': 3306,
    'user': 'defect_genetic_checking',
    'password': 'Jaybz@890411',
    'database': 'bull_library',
    'charset': 'utf8mb4'
}

class SimpleAuthService:
    """极简认证服务 - 不实现单设备限制"""
    
    def __init__(self):
        """初始化认证服务"""
        self.device_id = self._get_or_create_device_id()
        self.username = None
        
        # 用于本地凭证加密
        self.cipher_suite = self._init_cipher()
        
    def _init_cipher(self) -> Fernet:
        """初始化加密器"""
        key_file = Path.home() / ".protein_screening" / "key.key"
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            
        return Fernet(key)
    
    def _get_or_create_device_id(self) -> str:
        """获取或创建设备ID"""
        device_file = Path.home() / ".protein_screening" / "device_id"
        device_file.parent.mkdir(exist_ok=True)
        
        if device_file.exists():
            return device_file.read_text().strip()
        else:
            device_id = str(uuid.uuid4())
            device_file.write_text(device_id)
            return device_id
    
    def _get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**ALIYUN_DB_CONFIG)
    
    def register(self, employee_id: str, password: str, invite_code: str, name: str) -> Tuple[bool, str]:
        """注册新用户"""
        connection = None
        try:
            connection = self._get_db_connection()
            
            with connection.cursor() as cursor:
                # 检查用户是否已存在
                sql = "SELECT ID FROM `id-pw` WHERE ID=%s"
                cursor.execute(sql, (employee_id,))
                if cursor.fetchone():
                    return False, "用户名已存在"
                
                # 检查邀请码
                sql = """
                    SELECT code, status, max_uses, current_uses, expire_time 
                    FROM invitation_codes 
                    WHERE code = %s
                """
                cursor.execute(sql, (invite_code,))
                invite = cursor.fetchone()
                
                if not invite:
                    return False, "邀请码不存在"
                
                # 检查状态
                if invite[1] != 1:  # status
                    return False, "邀请码已失效"
                
                # 检查过期时间
                if invite[4] and datetime.now() > invite[4]:
                    return False, "邀请码已过期"
                
                # 检查使用次数
                if invite[3] >= invite[2]:  # current_uses >= max_uses
                    return False, "邀请码使用次数已达上限"
                
                # 创建用户
                sql = "INSERT INTO `id-pw` (ID, PW, name) VALUES (%s, %s, %s)"
                cursor.execute(sql, (employee_id, password, name))
                
                # 更新邀请码使用次数
                sql = """
                    UPDATE invitation_codes 
                    SET current_uses = current_uses + 1
                    WHERE code = %s
                """
                cursor.execute(sql, (invite_code,))
                
                connection.commit()
                return True, "注册成功"
                
        except Exception as e:
            logging.error(f"注册失败: {e}")
            return False, f"注册失败: {str(e)}"
        finally:
            if connection:
                connection.close()
    
    def login(self, username: str, password: str, force: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """用户登录 - 简化版，不检查单设备限制"""
        connection = None
        try:
            connection = self._get_db_connection()
            
            with connection.cursor() as cursor:
                # 验证用户名密码
                sql = "SELECT * FROM `id-pw` WHERE ID=%s AND PW=%s"
                cursor.execute(sql, (username, password))
                if not cursor.fetchone():
                    return False, "用户名或密码错误", None
                
                # 登录成功
                self.username = username
                return True, "登录成功", None
                
        except Exception as e:
            logging.error(f"登录失败: {e}")
            return False, f"登录失败: {str(e)}", None
        finally:
            if connection:
                connection.close()
    
    def heartbeat(self) -> bool:
        """心跳 - 简化版，总是返回True"""
        return self.username is not None
    
    def logout(self):
        """登出"""
        self.username = None
    
    def save_credentials(self, username: str, password: str, remember: bool = True):
        """保存登录凭证"""
        cred_file = Path.home() / ".protein_screening" / "credentials.enc"
        
        if remember:
            data = {
                "username": username,
                "password": password,
                "remember": True
            }
            encrypted = self.cipher_suite.encrypt(json.dumps(data).encode())
            cred_file.write_bytes(encrypted)
        else:
            # 只保存用户名
            data = {
                "username": username,
                "password": "",
                "remember": False
            }
            encrypted = self.cipher_suite.encrypt(json.dumps(data).encode())
            cred_file.write_bytes(encrypted)
    
    def load_credentials(self) -> Optional[Dict]:
        """加载保存的凭证"""
        cred_file = Path.home() / ".protein_screening" / "credentials.enc"
        
        if cred_file.exists():
            try:
                encrypted = cred_file.read_bytes()
                decrypted = self.cipher_suite.decrypt(encrypted)
                return json.loads(decrypted.decode())
            except Exception as e:
                logging.error(f"加载凭证失败: {str(e)}")
                return None
        return None
    
    def clear_credentials(self):
        """清除保存的凭证"""
        cred_file = Path.home() / ".protein_screening" / "credentials.enc"
        if cred_file.exists():
            cred_file.unlink()
    
    def check_server_health(self) -> bool:
        """检查数据库连接"""
        try:
            connection = self._get_db_connection()
            connection.close()
            return True
        except:
            return False