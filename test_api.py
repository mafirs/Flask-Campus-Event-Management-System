#!/usr/bin/env python3
"""
API测试脚本
用于测试校级活动场地与物资管理系统的各个API接口
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:5000"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def test_connection(self):
        """测试服务器连接"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            print("✓ 服务器连接正常")
            return True
        except requests.exceptions.RequestException as e:
            print(f"✗ 服务器连接失败: {e}")
            return False

    def login(self, username="admin", password="admin"):
        """登录测试"""
        print(f"\n=== 测试用户登录: {username} ===")
        try:
            data = {
                "username": username,
                "password": password
            }
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    self.token = result['data']['token']
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    print(f"✓ 登录成功: {result['data']['user']['realName']}")
                    return True
                else:
                    print(f"✗ 登录失败: {result.get('message')}")
                    return False
            else:
                print(f"✗ 登录请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 登录错误: {e}")
            return False

    def test_get_profile(self):
        """测试获取用户信息"""
        print("\n=== 测试获取用户信息 ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/profile",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    user = result['data']
                    print(f"✓ 用户信息获取成功: {user['realName']} ({user['role']})")
                    return True
                else:
                    print(f"✗ 获取用户信息失败: {result.get('message')}")
                    return False
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 获取用户信息错误: {e}")
            return False

    def test_get_venues(self):
        """测试获取场地列表"""
        print("\n=== 测试获取场地列表 ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/venues",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    venues = result['data']['list']
                    print(f"✓ 获取场地列表成功，共 {len(venues)} 个场地")
                    for venue in venues:
                        print(f"  - {venue['name']} ({venue['location']}) - {venue['status']}")
                    return True
                else:
                    print(f"✗ 获取场地列表失败: {result.get('message')}")
                    return False
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 获取场地列表错误: {e}")
            return False

    def test_get_materials(self):
        """测试获取物资列表"""
        print("\n=== 测试获取物资列表 ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/materials",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    materials = result['data']['list']
                    print(f"✓ 获取物资列表成功，共 {len(materials)} 种物资")
                    for material in materials:
                        print(f"  - {material['name']} ({material['category']}) - "
                              f"{material['availableQuantity']}/{material['totalQuantity']}{material['unit']}")
                    return True
                else:
                    print(f"✗ 获取物资列表失败: {result.get('message')}")
                    return False
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 获取物资列表错误: {e}")
            return False

    def test_create_application(self):
        """测试创建申请"""
        print("\n=== 测试创建申请 ===")
        try:
            # 准备测试数据
            start_time = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
            end_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat() + 'Z'

            data = {
                "activityName": "API测试活动",
                "activityDescription": "使用API创建的测试活动",
                "venueId": 1,
                "startTime": start_time,
                "endTime": end_time,
                "materials": [
                    {"materialId": 1, "quantity": 1},
                    {"materialId": 2, "quantity": 10}
                ]
            }

            response = requests.post(
                f"{self.base_url}/api/applications",
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    application = result['data']
                    print(f"✓ 申请创建成功: ID {application['id']}, 状态: {application['status']}")
                    return application['id']
                else:
                    print(f"✗ 申请创建失败: {result.get('message')}")
                    return None
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
        except Exception as e:
            print(f"✗ 创建申请错误: {e}")
            return None

    def test_get_my_applications(self):
        """测试获取我的申请列表"""
        print("\n=== 测试获取我的申请列表 ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/applications/my",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    applications = result['data']['list']
                    print(f"✓ 获取我的申请列表成功，共 {len(applications)} 个申请")
                    for app in applications:
                        print(f"  - {app['activityName']} ({app['status']}) - {app['createdAt']}")
                    return True
                else:
                    print(f"✗ 获取申请列表失败: {result.get('message')}")
                    return False
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 获取申请列表错误: {e}")
            return False

    def test_get_dashboard_stats(self):
        """测试获取统计数据"""
        print("\n=== 测试获取统计数据 ===")
        try:
            response = requests.get(
                f"{self.base_url}/api/dashboard/stats",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    stats = result['data']
                    print("✓ 获取统计数据成功:")
                    print(f"  - 总场地数: {stats['totalVenues']}")
                    print(f"  - 总物资数: {stats['totalMaterials']}")
                    print(f"  - 待审批申请: {stats['pendingApplications']}")
                    print(f"  - 今日申请: {stats['todayApplications']}")
                    print(f"  - 场地使用率: {stats['venueUtilization']}")
                    print(f"  - 物资使用率: {stats['materialUtilization']}")
                    return True
                else:
                    print(f"✗ 获取统计数据失败: {result.get('message')}")
                    return False
            else:
                print(f"✗ 请求失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 获取统计数据错误: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("开始API测试...")
        print("=" * 50)

        # 测试连接
        if not self.test_connection():
            print("\n请确保Flask服务器正在运行: python run.py")
            return

        # 测试登录
        if not self.login():
            return

        # 测试各种API
        self.test_get_profile()
        self.test_get_venues()
        self.test_get_materials()
        self.test_get_dashboard_stats()

        # 测试创建申请
        app_id = self.test_create_application()

        # 测试获取申请列表
        self.test_get_my_applications()

        print("\n" + "=" * 50)
        print("API测试完成！")

def main():
    """主函数"""
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()