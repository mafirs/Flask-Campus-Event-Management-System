from datetime import datetime
from typing import Optional, Dict, Any
from app import db

class Material(db.Model):
    """物资模型"""
    __tablename__ = 'materials'

    # SQLAlchemy 字段定义
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    category = db.Column(db.String(64), nullable=False)  # KEPT from original
    total_quantity = db.Column(db.Integer, nullable=False)
    available_quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(256))  # NEW - nullable
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, id: int, name: str, category: str, total_quantity: int,
                 unit: str, description: str, available_quantity: Optional[int] = None,
                 status: str = 'available'):
        self.id = id
        self.name = name
        self.category = category
        self.total_quantity = total_quantity
        self.available_quantity = available_quantity if available_quantity is not None else total_quantity
        self.unit = unit
        self.description = description
        self.status = status  # available, unavailable
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'totalQuantity': self.total_quantity,
            'availableQuantity': self.available_quantity,
            'unit': self.unit,
            'description': self.description,
            'status': self.status,
            'createdAt': self.created_at.isoformat()
        }

    def to_dict_simple(self) -> Dict[str, Any]:
        """转换为简化字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'totalQuantity': self.total_quantity,
            'availableQuantity': self.available_quantity,
            'unit': self.unit,
            'status': self.status
        }

    def update(self, **kwargs):
        """更新物资信息"""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def is_available(self) -> bool:
        """检查物资是否可用"""
        return self.status == 'available' and self.available_quantity > 0

    def reserve(self, quantity: int) -> bool:
        """预留物资"""
        if self.available_quantity >= quantity:
            self.available_quantity -= quantity
            self.updated_at = datetime.utcnow()
            return True
        return False

    def release(self, quantity: int):
        """释放物资"""
        self.available_quantity = min(
            self.available_quantity + quantity,
            self.total_quantity
        )
        self.updated_at = datetime.utcnow()

    def get_stock_status(self, requested_quantity: int) -> str:
        """获取库存状态"""
        if self.available_quantity >= requested_quantity:
            return 'sufficient'
        elif self.available_quantity > 0:
            return 'low'
        else:
            return 'insufficient'

    def set_unavailable(self):
        """设置为不可用状态"""
        self.status = 'unavailable'
        self.updated_at = datetime.utcnow()

    def set_available(self):
        """设置为可用状态"""
        self.status = 'available'
        self.updated_at = datetime.utcnow()

    @staticmethod
    def from_dict(data: Dict[str, Any], material_id: int) -> 'Material':
        """从字典创建物资对象"""
        return Material(
            id=material_id,
            name=data['name'],
            category=data['category'],
            total_quantity=data['totalQuantity'],
            unit=data['unit'],
            description=data['description'],
            available_quantity=data.get('availableQuantity', data['totalQuantity']),
            status=data.get('status', 'available')
        )
