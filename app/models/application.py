from datetime import datetime
from typing import Optional, Dict, Any, List

class ApplicationMaterial:
    """申请物资关联模型"""

    def __init__(self, material_id: int, quantity: int):
        self.material_id = material_id
        self.quantity = quantity

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'materialId': self.material_id,
            'quantity': self.quantity
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ApplicationMaterial':
        """从字典创建申请物资对象"""
        return ApplicationMaterial(
            material_id=data['materialId'],
            quantity=data['quantity']
        )

class Application:
    """申请模型"""

    def __init__(self, id: int, user_id: int, activity_name: str,
                 activity_description: str, venue_id: int,
                 start_time: str, end_time: str,
                 materials: List[ApplicationMaterial], status: str = 'pending'):
        self.id = id
        self.user_id = user_id
        self.activity_name = activity_name
        self.activity_description = activity_description
        self.venue_id = venue_id
        self.start_time = start_time  # ISO 8601格式
        self.end_time = end_time  # ISO 8601格式
        self.materials = materials
        self.status = status  # pending, approved, rejected, cancelled
        self.rejection_reason = None
        self.reviewer_id = None
        self.created_at = datetime.utcnow()
        self.reviewed_at = None
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'activityName': self.activity_name,
            'activityDescription': self.activity_description,
            'venueId': self.venue_id,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'materials': [material.to_dict() for material in self.materials],
            'status': self.status,
            'rejectionReason': self.rejection_reason,
            'reviewerId': self.reviewer_id,
            'createdAt': self.created_at.isoformat(),
            'reviewedAt': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'updatedAt': self.updated_at.isoformat()
        }

    def to_dict_with_details(self, user_info: Dict[str, Any], venue_info: Dict[str, Any],
                           material_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """转换为包含详细信息的字典格式"""
        return {
            'id': self.id,
            'activityName': self.activity_name,
            'activityDescription': self.activity_description,
            'venue': venue_info,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'status': self.status,
            'applicant': user_info,
            'materials': material_details,
            'rejectionReason': self.rejection_reason,
            'reviewerId': self.reviewer_id,
            'createdAt': self.created_at.isoformat(),
            'reviewedAt': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'updatedAt': self.updated_at.isoformat()
        }

    def approve(self, reviewer_id: int):
        """审批通过"""
        self.status = 'approved'
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reject(self, reviewer_id: int, reason: str):
        """审批驳回"""
        self.status = 'rejected'
        self.reviewer_id = reviewer_id
        self.rejection_reason = reason
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self):
        """取消申请"""
        if self.status in ['pending', 'approved']:
            self.status = 'cancelled'
            self.updated_at = datetime.utcnow()
            return True
        return False

    def is_pending(self) -> bool:
        """检查是否为待审批状态"""
        return self.status == 'pending'

    def is_approved(self) -> bool:
        """检查是否已通过审批"""
        return self.status == 'approved'

    def is_rejected(self) -> bool:
        """检查是否被驳回"""
        return self.status == 'rejected'

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self.status == 'cancelled'

    def can_be_cancelled(self) -> bool:
        """检查是否可以取消"""
        return self.status in ['pending', 'approved']

    def can_be_reviewed(self) -> bool:
        """检查是否可以审批"""
        return self.status == 'pending'

    def has_time_conflict(self, other_start: str, other_end: str) -> bool:
        """检查时间冲突"""
        # 简单的时间冲突检查，实际应用中需要更精确的时间处理
        start_dt = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
        other_start_dt = datetime.fromisoformat(other_start.replace('Z', '+00:00'))
        other_end_dt = datetime.fromisoformat(other_end.replace('Z', '+00:00'))

        return not (end_dt <= other_start_dt or start_dt >= other_end_dt)

    @staticmethod
    def from_dict(data: Dict[str, Any], application_id: int, user_id: int) -> 'Application':
        """从字典创建申请对象"""
        materials = [
            ApplicationMaterial.from_dict(material_data)
            for material_data in data.get('materials', [])
        ]

        return Application(
            id=application_id,
            user_id=user_id,
            activity_name=data['activityName'],
            activity_description=data['activityDescription'],
            venue_id=data['venueId'],
            start_time=data['startTime'],
            end_time=data['endTime'],
            materials=materials,
            status=data.get('status', 'pending')
        )