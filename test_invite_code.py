"""测试邀请码验证"""
import pymysql
from datetime import datetime

# 阿里云数据库配置
ALIYUN_DB_CONFIG = {
    'host': 'defectgene-new.mysql.polardb.rds.aliyuncs.com',
    'port': 3306,
    'user': 'defect_genetic_checking',
    'password': 'Jaybz@890411',
    'database': 'bull_library',
    'charset': 'utf8mb4'
}

def test_invite_code(code):
    """测试邀请码"""
    connection = None
    try:
        print(f"连接到数据库: {ALIYUN_DB_CONFIG['host']}")
        connection = pymysql.connect(**ALIYUN_DB_CONFIG)
        print("连接成功")
        
        with connection.cursor() as cursor:
            # 查询邀请码
            sql = """
                SELECT code, status, max_uses, current_uses, expire_time 
                FROM invitation_codes 
                WHERE code = %s
            """
            print(f"\n查询邀请码: {code}")
            cursor.execute(sql, (code,))
            result = cursor.fetchone()
            
            if result:
                print(f"找到邀请码:")
                print(f"  - code: {result[0]}")
                print(f"  - status: {result[1]} (1=可用, 2=已使用, 3=已过期)")
                print(f"  - max_uses: {result[2]}")
                print(f"  - current_uses: {result[3]}")
                print(f"  - expire_time: {result[4]}")
                
                # 检查是否可用
                if result[1] != 1:
                    print(f"  ❌ 邀请码状态不是可用状态")
                elif result[4] and datetime.now() > result[4]:
                    print(f"  ❌ 邀请码已过期")
                elif result[3] >= result[2]:
                    print(f"  ❌ 邀请码使用次数已达上限")
                else:
                    print(f"  ✅ 邀请码可以使用")
            else:
                print(f"❌ 未找到邀请码: {code}")
                
            # 列出所有邀请码
            print("\n所有邀请码:")
            cursor.execute("SELECT code, status, max_uses, current_uses FROM invitation_codes")
            all_codes = cursor.fetchall()
            for c in all_codes:
                print(f"  - {c[0]}: status={c[1]}, uses={c[3]}/{c[2]}")
                
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    # 测试你使用的邀请码
    test_code = input("请输入要测试的邀请码: ")
    test_invite_code(test_code)