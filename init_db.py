#!/usr/bin/env python3
"""
数据库初始化脚本（幂等安全版本）
"""

import pymysql
from app import create_app, db
from app.config import Config
from app.models.user import User


def create_database_if_not_exists():
    """如果数据库不存在则创建"""
    # 解析数据库连接信息
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    # mysql+pymysql://root:password@host:port/database
    import re
    match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_uri)
    if not match:
        print(f"无法解析数据库URI: {db_uri}")
        return False

    user, password, host, port, database = match.groups()

    try:
        # 连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            charset='utf8mb4'
        )

        with connection.cursor() as cursor:
            # 检查数据库是否存在
            cursor.execute(f"SHOW DATABASES LIKE '{database}'")
            result = cursor.fetchone()

            if not result:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 '{database}' 创建成功")
            else:
                print(f"数据库 '{database}' 已存在")

        connection.commit()
        connection.close()
        return True

    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False


def init_database():
    """初始化数据库（幂等安全版本）"""

    # 创建应用实例
    app = create_app()

    # 先创建数据库
    print("检查数据库是否存在...")
    if not create_database_if_not_exists():
        print("无法创建数据库，退出")
        return

    with app.app_context():
        print("开始初始化数据库...")

        # 创建所有表（幂等 - 已存在的表会自动跳过）
        print("正在创建数据表...")
        db.create_all()

        # 安全创建管理员账号（幂等）
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                id=1,
                username='admin',
                password='123',
                real_name='系统管理员',
                role='admin',
                email='admin@example.com',
                status='active'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("默认管理员账号已创建: admin/123")
        else:
            print("管理员账号已存在，跳过创建")

        print("数据库初始化完成！")


if __name__ == '__main__':
    init_database()
