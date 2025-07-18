#!/usr/bin/env python3
"""
测试阿里云数据库连接
"""

import pymysql

# 阿里云数据库配置
ALIYUN_DB_CONFIG = {
    'host': 'defectgene-new.mysql.polardb.rds.aliyuncs.com',
    'port': 3306,
    'user': 'defect_genetic_checking',
    'password': 'Jaybz@890411',
    'database': 'bull_library',
    'charset': 'utf8mb4'
}

def test_connection():
    """测试数据库连接"""
    print("测试阿里云数据库连接...")
    
    try:
        # 连接数据库
        connection = pymysql.connect(**ALIYUN_DB_CONFIG)
        print("✅ 数据库连接成功！")
        
        with connection.cursor() as cursor:
            # 查询用户表结构
            cursor.execute("DESCRIBE `id-pw`")
            columns = cursor.fetchall()
            
            print("\n📋 用户表结构 (id-pw):")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")
            
            # 查询用户数量
            cursor.execute("SELECT COUNT(*) FROM `id-pw`")
            count = cursor.fetchone()[0]
            print(f"\n👥 当前用户数量: {count}")
            
            # 查询前5个用户（只显示用户名）
            cursor.execute("SELECT ID FROM `id-pw` LIMIT 5")
            users = cursor.fetchall()
            if users:
                print("\n📝 示例用户名:")
                for user in users:
                    print(f"   - {user[0]}")
        
        connection.close()
        print("\n✅ 测试完成！数据库可以正常使用。")
        return True
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        return False

def test_user_login(username, password):
    """测试用户登录"""
    print(f"\n测试用户登录: {username}")
    
    try:
        connection = pymysql.connect(**ALIYUN_DB_CONFIG)
        
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `id-pw` WHERE ID=%s AND PW=%s"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()
            
            if result:
                print("✅ 登录成功！")
                return True
            else:
                print("❌ 用户名或密码错误")
                return False
                
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    # 测试连接
    if test_connection():
        # 如果您有测试账号，可以在这里测试登录
        # test_user_login("your_username", "your_password")
        pass