#!/usr/bin/env python3
"""
数据库初始化脚本
使用 Mock 数据填充 MySQL 数据库
"""

import pymysql
from app import create_app, db
from app.services.mock_data import mock_data_service
from app.config import Config

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
    """初始化数据库并填充 Mock 数据"""

    # 创建应用实例
    app = create_app()

    # 先创建数据库
    print("检查数据库是否存在...")
    if not create_database_if_not_exists():
        print("无法创建数据库，退出")
        return

    with app.app_context():
        print("开始初始化数据库...")

        # 1. 重置数据库 - 删除所有表并重新创建
        print("正在重置数据库...")
        db.drop_all()
        db.create_all()

        # 2. 插入 Users
        print("正在插入 Users 数据...")
        for user in mock_data_service.users.values():
            db.session.add(user)
        db.session.commit()
        print(f"已插入 {len(mock_data_service.users)} 个用户")

        # 3. 插入 Venues
        print("正在插入 Venues 数据...")
        for venue in mock_data_service.venues.values():
            db.session.add(venue)
        db.session.commit()
        print(f"已插入 {len(mock_data_service.venues)} 个场地")

        # 4. 插入 Materials
        print("正在插入 Materials 数据...")
        for material in mock_data_service.materials.values():
            db.session.add(material)
        db.session.commit()
        print(f"已插入 {len(mock_data_service.materials)} 个物资")

        # 5. 插入 Applications (包含 ApplicationMaterial 关联)
        print("正在插入 Applications 数据...")
        for application in mock_data_service.applications.values():
            # 设置 application_id 关联
            for material in application.materials:
                material.application_id = application.id
            db.session.add(application)
        db.session.commit()
        print(f"已插入 {len(mock_data_service.applications)} 个申请")

        print("Database initialized with mock data successfully!")

if __name__ == '__main__':
    init_database()
