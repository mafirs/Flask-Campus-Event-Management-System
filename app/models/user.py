from datetime import datetime
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    """用户模型 (使用内存存储，后续可迁移到数据库)"""

    def __init__(self, id: int, username: str, password: str, real_name: str,
                 role: str, email: str, status: str = 'active'):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.real_name = real_name
        self.role = role  # admin, reviewer, user
        self.email = email
        self.status = status
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'realName': self.real_name,
            'role': self.role,
            'email': self.email,
            'status': self.status,
            'createdAt': self.created_at.isoformat()
        }

    def to_dict_safe(self) -> Dict[str, Any]:
        """转换为字典格式（不包含敏感信息）"""
        return {
            'id': self.id,
            'username': self.username,
            'realName': self.real_name,
            'role': self.role,
            'email': self.email,
            'status': self.status
        }

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def update_password(self, password: str):
        """更新密码"""
        self.password_hash = generate_password_hash(password)

    @staticmethod
    def from_dict(data: Dict[str, Any], user_id: int) -> 'User':
        """从字典创建用户对象"""
        return User(
            id=user_id,
            username=data['username'],
            password=data['password'],
            real_name=data['realName'],
            role=data['role'],
            email=data['email'],
            status=data.get('status', 'active')
        )