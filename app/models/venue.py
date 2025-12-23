from datetime import datetime
from typing import Optional, Dict, Any, List

class Venue:
    """场地模型"""

    def __init__(self, id: int, name: str, location: str, capacity: int,
                 description: str, equipment: List[str], status: str = 'available'):
        self.id = id
        self.name = name
        self.location = location
        self.capacity = capacity
        self.description = description
        self.equipment = equipment
        self.status = status  # available, maintenance
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'capacity': self.capacity,
            'description': self.description,
            'equipment': self.equipment,
            'status': self.status,
            'createdAt': self.created_at.isoformat()
        }

    def to_dict_simple(self) -> Dict[str, Any]:
        """转换为简化字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'capacity': self.capacity,
            'status': self.status
        }

    def update(self, **kwargs):
        """更新场地信息"""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def is_available(self) -> bool:
        """检查场地是否可用"""
        return self.status == 'available'

    def set_maintenance(self):
        """设置为维护状态"""
        self.status = 'maintenance'
        self.updated_at = datetime.utcnow()

    def set_available(self):
        """设置为可用状态"""
        self.status = 'available'
        self.updated_at = datetime.utcnow()

    @staticmethod
    def from_dict(data: Dict[str, Any], venue_id: int) -> 'Venue':
        """从字典创建场地对象"""
        return Venue(
            id=venue_id,
            name=data['name'],
            location=data['location'],
            capacity=data['capacity'],
            description=data['description'],
            equipment=data.get('equipment', []),
            status=data.get('status', 'available')
        )