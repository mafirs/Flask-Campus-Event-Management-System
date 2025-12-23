from typing import Dict, List, Optional
from datetime import datetime
from app.models.user import User
from app.models.venue import Venue
from app.models.material import Material
from app.models.application import Application, ApplicationMaterial

class MockDataService:
    """Mock数据服务类"""

    def __init__(self):
        self.users: Dict[int, User] = {}
        self.venues: Dict[int, Venue] = {}
        self.materials: Dict[int, Material] = {}
        self.applications: Dict[int, Application] = {}
        self.next_user_id = 1
        self.next_venue_id = 1
        self.next_material_id = 1
        self.next_application_id = 1

        self.initialize_mock_data()

    def initialize_mock_data(self):
        """初始化Mock数据"""
        self._create_mock_users()
        self._create_mock_venues()
        self._create_mock_materials()
        self._create_mock_applications()

    def _create_mock_users(self):
        """创建Mock用户数据"""
        mock_users = [
            {
                "username": "admin",
                "password": "admin",
                "realName": "系统管理员",
                "role": "admin",
                "email": "admin@example.com",
                "status": "active"
            },
            {
                "username": "reviewer",
                "password": "reviewer",
                "realName": "审核员",
                "role": "reviewer",
                "email": "reviewer@example.com",
                "status": "active"
            },
            {
                "username": "user1",
                "password": "user1",
                "realName": "张三",
                "role": "user",
                "email": "zhangsan@example.com",
                "status": "active"
            },
            {
                "username": "user2",
                "password": "user2",
                "realName": "李四",
                "role": "user",
                "email": "lisi@example.com",
                "status": "active"
            }
        ]

        for user_data in mock_users:
            user = User.from_dict(user_data, self.next_user_id)
            self.users[self.next_user_id] = user
            self.next_user_id += 1

    def _create_mock_venues(self):
        """创建Mock场地数据"""
        mock_venues = [
            {
                "name": "大学生活动中心",
                "location": "A栋101",
                "capacity": 200,
                "description": "大型活动场所，配备专业音响和投影设备",
                "equipment": ["投影仪", "音响设备", "麦克风", "空调"],
                "status": "available"
            },
            {
                "name": "体育馆",
                "location": "B栋201",
                "capacity": 500,
                "description": "室内体育活动场所",
                "equipment": ["篮球架", "音响设备", "计分器"],
                "status": "available"
            },
            {
                "name": "图书馆报告厅",
                "location": "C栋301",
                "capacity": 150,
                "description": "学术报告和讲座场所",
                "equipment": ["投影仪", "讲台", "麦克风", "空调"],
                "status": "maintenance"
            },
            {
                "name": "学生活动室",
                "location": "D栋101",
                "capacity": 50,
                "description": "小型社团活动场所",
                "equipment": ["桌子", "椅子", "白板"],
                "status": "available"
            }
        ]

        for venue_data in mock_venues:
            venue = Venue.from_dict(venue_data, self.next_venue_id)
            self.venues[self.next_venue_id] = venue
            self.next_venue_id += 1

    def _create_mock_materials(self):
        """创建Mock物资数据"""
        mock_materials = [
            {
                "name": "投影仪",
                "category": "电子设备",
                "totalQuantity": 10,
                "unit": "台",
                "description": "高清投影仪，支持HDMI和VGA输入",
                "status": "available"
            },
            {
                "name": "折叠椅",
                "category": "家具",
                "totalQuantity": 100,
                "unit": "把",
                "description": "可折叠塑料椅",
                "status": "available"
            },
            {
                "name": "麦克风",
                "category": "电子设备",
                "totalQuantity": 5,
                "unit": "个",
                "description": "无线手持麦克风",
                "status": "available"
            },
            {
                "name": "折叠桌",
                "category": "家具",
                "totalQuantity": 20,
                "unit": "张",
                "description": "可折叠会议桌",
                "status": "available"
            },
            {
                "name": "音响设备",
                "category": "电子设备",
                "totalQuantity": 3,
                "unit": "套",
                "description": "专业音响系统",
                "status": "available"
            },
            {
                "name": "白板",
                "category": "办公用品",
                "totalQuantity": 15,
                "unit": "块",
                "description": "移动式白板",
                "status": "available"
            }
        ]

        for material_data in mock_materials:
            material = Material.from_dict(material_data, self.next_material_id)
            self.materials[self.next_material_id] = material
            self.next_material_id += 1

    def _create_mock_applications(self):
        """创建Mock申请数据"""
        mock_applications = [
            {
                "activityName": "社团招新活动",
                "activityDescription": "春季学期社团招新活动，预计吸引新生200人",
                "venueId": 1,
                "startTime": "2024-01-15T14:00:00Z",
                "endTime": "2024-01-15T17:00:00Z",
                "materials": [
                    {"materialId": 1, "quantity": 1},
                    {"materialId": 2, "quantity": 20}
                ],
                "status": "pending"
            },
            {
                "activityName": "学术讲座",
                "activityDescription": "邀请专家学者进行学术分享",
                "venueId": 3,
                "startTime": "2024-01-20T19:00:00Z",
                "endTime": "2024-01-20T21:00:00Z",
                "materials": [
                    {"materialId": 1, "quantity": 1},
                    {"materialId": 3, "quantity": 2}
                ],
                "status": "approved"
            }
        ]

        # 用户ID 3 (张三) 创建申请
        for i, app_data in enumerate(mock_applications):
            application = Application.from_dict(app_data, self.next_application_id, 3)

            # 如果是已审批的申请，设置审批信息
            if app_data["status"] == "approved":
                application.approve(2)  # 审批员ID 2
                # 扣减物资库存
                for material in application.materials:
                    material_obj = self.materials.get(material.material_id)
                    if material_obj:
                        material_obj.reserve(material.quantity)

            self.applications[self.next_application_id] = application
            self.next_application_id += 1

    # 用户相关方法
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)

    # 场地相关方法
    def get_all_venues(self) -> List[Venue]:
        """获取所有场地"""
        return list(self.venues.values())

    def get_venue_by_id(self, venue_id: int) -> Optional[Venue]:
        """根据ID获取场地"""
        return self.venues.get(venue_id)

    def create_venue(self, venue_data: dict) -> Venue:
        """创建场地"""
        venue = Venue.from_dict(venue_data, self.next_venue_id)
        self.venues[self.next_venue_id] = venue
        self.next_venue_id += 1
        return venue

    def update_venue(self, venue_id: int, venue_data: dict) -> bool:
        """更新场地"""
        venue = self.venues.get(venue_id)
        if venue:
            venue.update(**venue_data)
            return True
        return False

    def delete_venue(self, venue_id: int) -> bool:
        """删除场地"""
        if venue_id in self.venues:
            del self.venues[venue_id]
            return True
        return False

    # 物资相关方法
    def get_all_materials(self) -> List[Material]:
        """获取所有物资"""
        return list(self.materials.values())

    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """根据ID获取物资"""
        return self.materials.get(material_id)

    def create_material(self, material_data: dict) -> Material:
        """创建物资"""
        material = Material.from_dict(material_data, self.next_material_id)
        self.materials[self.next_material_id] = material
        self.next_material_id += 1
        return material

    def update_material(self, material_id: int, material_data: dict) -> bool:
        """更新物资"""
        material = self.materials.get(material_id)
        if material:
            material.update(**material_data)
            return True
        return False

    def delete_material(self, material_id: int) -> bool:
        """删除物资"""
        if material_id in self.materials:
            del self.materials[material_id]
            return True
        return False

    # 申请相关方法
    def get_all_applications(self) -> List[Application]:
        """获取所有申请"""
        return list(self.applications.values())

    def get_application_by_id(self, application_id: int) -> Optional[Application]:
        """根据ID获取申请"""
        return self.applications.get(application_id)

    def get_applications_by_user(self, user_id: int) -> List[Application]:
        """获取用户的申请列表"""
        return [app for app in self.applications.values() if app.user_id == user_id]

    def get_pending_applications(self) -> List[Application]:
        """获取待审批申请列表"""
        return [app for app in self.applications.values() if app.status == 'pending']

    def create_application(self, application_data: dict, user_id: int) -> Application:
        """创建申请"""
        application = Application.from_dict(application_data, self.next_application_id, user_id)
        self.applications[self.next_application_id] = application
        self.next_application_id += 1

        # 预占物资库存
        for material in application.materials:
            material_obj = self.materials.get(material.material_id)
            if material_obj:
                material_obj.reserve(material.quantity)

        return application

    def update_application_status(self, application_id: int, status: str, **kwargs) -> bool:
        """更新申请状态"""
        application = self.applications.get(application_id)
        if not application:
            return False

        if status == 'approved':
            reviewer_id = kwargs.get('reviewer_id')
            if reviewer_id:
                application.approve(reviewer_id)
        elif status == 'rejected':
            reviewer_id = kwargs.get('reviewer_id')
            reason = kwargs.get('reason', '')
            if reviewer_id:
                application.reject(reviewer_id, reason)
                # 释放物资库存
                for material in application.materials:
                    material_obj = self.materials.get(material.material_id)
                    if material_obj:
                        material_obj.release(material.quantity)
        elif status == 'cancelled':
            if application.cancel():
                # 释放物资库存
                for material in application.materials:
                    material_obj = self.materials.get(material.material_id)
                    if material_obj:
                        material_obj.release(material.quantity)
            else:
                return False

        return True

# 全局Mock数据服务实例
mock_data_service = MockDataService()