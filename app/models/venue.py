from datetime import datetime
from typing import Optional, Dict, Any, List
from app import db

class Venue(db.Model):
    """场地模型"""
    __tablename__ = 'venues'

    # SQLAlchemy 字段定义
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    location = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available')
    description = db.Column(db.Text, nullable=False)
    equipment = db.Column(db.Text)  # JSON string of equipment list
    image_url = db.Column(db.String(256))  # NEW - nullable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, id: int, name: str, location: str, capacity: int,
                 description: str, equipment: List[str], status: str = 'available'):
        self.id = id
        self.name = name
        self.location = location
        self.capacity = capacity
        self.description = description
        # Store equipment list as JSON string
        import json
        self.equipment = json.dumps(equipment) if equipment else None
        self.status = status  # available, maintenance
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'capacity': self.capacity,
            'description': self.description,
            'equipment': json.loads(self.equipment) if self.equipment else [],
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
                # Convert equipment list to JSON if needed
                if key == 'equipment' and isinstance(value, list):
                    import json
                    value = json.dumps(value)
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
