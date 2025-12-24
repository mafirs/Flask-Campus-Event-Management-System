#!/usr/bin/env python3
"""
Seed Data Script
Populates database with initial demo data for testing
"""

from app import create_app, db
from app.models.user import User
from app.models.venue import Venue
from app.models.material import Material


def seed_data():
    """Seed the database with demo data"""
    app = create_app()

    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("开始注入演示数据...")

        # Create users (password: 123456)
        admin = User(
            id=1,
            username='admin',
            password='123456',
            real_name='系统管理员',
            role='admin',
            email='admin@test.com'
        )

        reviewer = User(
            id=2,
            username='reviewer',
            password='123456',
            real_name='张导员',
            role='reviewer',
            email='reviewer@test.com'
        )

        student = User(
            id=3,
            username='student',
            password='123456',
            real_name='李同学',
            role='user',
            email='student@test.com'
        )

        teacher = User(
            id=4,
            username='teacher',
            password='123456',
            real_name='王教授',
            role='teacher',
            email='teacher@test.com'
        )

        # Create venues
        venue1 = Venue(
            id=1,
            name='第一报告厅',
            location='主楼一层',
            capacity=200,
            description='大型报告厅，配备多媒体设备',
            equipment=['投影仪']
        )

        venue2 = Venue(
            id=2,
            name='302研讨室',
            location='主楼三层',
            capacity=20,
            description='小型研讨室',
            equipment=[]
        )

        # Create materials
        mic = Material(
            id=1,
            name='无线麦克风',
            category='电子设备',
            total_quantity=10,
            unit='个',
            description='无线麦克风，适用于演讲和会议'
        )

        chairs = Material(
            id=2,
            name='折叠椅',
            category='家具',
            total_quantity=50,
            unit='把',
            description='可折叠椅，方便布置活动场地'
        )

        # Add all to session and commit
        db.session.add_all([admin, reviewer, student, teacher])
        db.session.add_all([venue1, venue2])
        db.session.add_all([mic, chairs])
        db.session.commit()

        print("演示数据注入成功！")


if __name__ == '__main__':
    seed_data()
