import pymysql
from pymysql.cursors import DictCursor

# 从mcp.json获取配置
config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'user1',
    'password': 'Auser1111',
    'database': 'learning_system',
    'cursorclass': DictCursor
}

try:
    # 建立连接
    connection = pymysql.connect(**config)
    print("✅ MySQL连接成功!")
    
    # 执行简单查询
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"数据库中有 {len(tables)} 张表")
        
except Exception as e:
    print(f"❌ 连接失败: {e}")
finally:
    if 'connection' in locals():
        connection.close()
