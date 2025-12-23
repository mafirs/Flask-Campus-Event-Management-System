from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.services.mock_data import mock_data_service
from app.models.venue import Venue
from app.models.material import Material
from app.models.application import Application

class BusinessLogicService:
    """业务逻辑服务层"""

    @staticmethod
    def validate_application_time_conflict(venue_id: int, start_time: str, end_time: str,
                                         exclude_application_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        验证场地时间冲突

        Args:
            venue_id: 场地ID
            start_time: 开始时间
            end_time: 结束时间
            exclude_application_id: 排除的申请ID（用于更新时）

        Returns:
            Tuple[bool, str]: (是否冲突, 冲突原因)
        """
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            return False, "时间格式错误"

        if start_dt >= end_dt:
            return False, "开始时间必须早于结束时间"

        if start_dt <= datetime.utcnow():
            return False, "申请时间不能是过去时间"

        # 检查场地是否存在
        venue = mock_data_service.get_venue_by_id(venue_id)
        if not venue:
            return False, "场地不存在"

        if not venue.is_available():
            return False, "场地当前不可用"

        # 检查时间冲突
        applications = mock_data_service.get_all_applications()
        for app in applications:
            if (app.venue_id == venue_id and
                app.status in ['pending', 'approved'] and
                app.id != exclude_application_id and
                app.has_time_conflict(start_time, end_time)):
                return False, f"该时间段与申请 {app.id} ({app.activity_name}) 时间冲突"

        return True, "验证通过"

    @staticmethod
    def validate_material_availability(material_requests: List[Dict[str, int]],
                                     auto_reserve: bool = False) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        验证物资可用性

        Args:
            material_requests: 物资请求列表 [{'materialId': 1, 'quantity': 2}]
            auto_reserve: 是否自动预留库存

        Returns:
            Tuple[bool, List[Dict]]: (是否验证通过, 物资详细信息列表)
        """
        if not material_requests:
            return False, "请至少申请一个物资"

        material_details = []

        for request in material_requests:
            material_id = request.get('materialId')
            quantity = request.get('quantity')

            if not material_id or not quantity:
                return False, "物资ID和数量不能为空"

            if not isinstance(quantity, int) or quantity <= 0:
                return False, "物资数量必须是正整数"

            # 检查物资是否存在
            material = mock_data_service.get_material_by_id(material_id)
            if not material:
                return False, f"物资ID {material_id} 不存在"

            if not material.is_available():
                return False, f"物资 {material.name} 当前不可用"

            # 检查库存
            if material.available_quantity < quantity:
                return False, f"物资 {material.name} 库存不足，当前可用数量: {material.available_quantity}"

            # 构建物资详细信息
            material_details.append({
                'materialId': material.id,
                'materialName': material.name,
                'requestedQuantity': quantity,
                'availableQuantity': material.available_quantity,
                'totalQuantity': material.total_quantity,
                'unit': material.unit,
                'stockStatus': material.get_stock_status(quantity)
            })

            # 自动预留库存
            if auto_reserve:
                material.reserve(quantity)

        return True, material_details

    @staticmethod
    def get_available_venues(start_time: str, end_time: str) -> List[Venue]:
        """
        获取指定时间段的可用场地

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            List[Venue]: 可用场地列表
        """
        is_valid, message = BusinessLogicService.validate_application_time_conflict(
            0, start_time, end_time
        )
        if not is_valid:
            return []

        # 获取所有可用场地
        all_venues = mock_data_service.get_all_venues()
        available_venues = []

        for venue in all_venues:
            if not venue.is_available():
                continue

            # 检查时间冲突
            has_conflict = False
            applications = mock_data_service.get_all_applications()

            for app in applications:
                if (app.venue_id == venue.id and
                    app.status in ['pending', 'approved'] and
                    app.has_time_conflict(start_time, end_time)):
                    has_conflict = True
                    break

            if not has_conflict:
                available_venues.append(venue)

        return available_venues

    @staticmethod
    def calculate_usage_statistics() -> Dict[str, Any]:
        """
        计算使用统计数据

        Returns:
            Dict[str, Any]: 使用统计数据
        """
        venues = mock_data_service.get_all_venues()
        materials = mock_data_service.get_all_materials()
        applications = mock_data_service.get_all_applications()

        # 基础统计
        total_venues = len(venues)
        total_materials = len(materials)
        pending_applications = len([app for app in applications if app.status == 'pending'])
        approved_applications = len([app for app in applications if app.status == 'approved'])

        # 今日申请
        today = datetime.utcnow().date()
        today_applications = len([
            app for app in applications
            if app.created_at.date() == today
        ])

        # 场地使用率
        available_venues = [v for v in venues if v.is_available()]
        total_capacity = sum(venue.capacity for venue in available_venues)
        used_capacity = 0

        for app in applications:
            if app.status == 'approved':
                venue = next((v for v in available_venues if v.id == app.venue_id), None)
                if venue:
                    used_capacity += venue.capacity

        venue_utilization = used_capacity / total_capacity if total_capacity > 0 else 0

        # 物资使用率
        available_materials = [m for m in materials if m.is_available()]
        total_material_qty = sum(m.total_quantity for m in available_materials)
        used_material_qty = sum(m.total_quantity - m.available_quantity for m in available_materials)
        material_utilization = used_material_qty / total_material_qty if total_material_qty > 0 else 0

        return {
            'totalVenues': total_venues,
            'totalMaterials': total_materials,
            'pendingApplications': pending_applications,
            'approvedApplications': approved_applications,
            'todayApplications': today_applications,
            'venueUtilization': round(venue_utilization, 2),
            'materialUtilization': round(material_utilization, 2),
            'totalCapacity': total_capacity,
            'usedCapacity': used_capacity,
            'totalMaterialQuantity': total_material_qty,
            'usedMaterialQuantity': used_material_qty
        }

    @staticmethod
    def get_user_statistics(user_id: int) -> Dict[str, Any]:
        """
        获取用户个人统计

        Args:
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 用户统计数据
        """
        user_applications = mock_data_service.get_applications_by_user(user_id)

        return {
            'total': len(user_applications),
            'pending': len([app for app in user_applications if app.status == 'pending']),
            'approved': len([app for app in user_applications if app.status == 'approved']),
            'rejected': len([app for app in user_applications if app.status == 'rejected']),
            'cancelled': len([app for app in user_applications if app.status == 'cancelled'])
        }

    @staticmethod
    def generate_trend_data(start_date: datetime, end_date: datetime,
                           trend_type: str = 'weekly') -> Dict[str, Any]:
        """
        生成趋势数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            trend_type: 趋势类型 (weekly/monthly)

        Returns:
            Dict[str, Any]: 趋势数据
        """
        applications = mock_data_service.get_all_applications()

        # 过滤时间范围内的申请
        filtered_applications = [
            app for app in applications
            if start_date <= app.created_at <= end_date
        ]

        # 这里可以实现更复杂的趋势分析逻辑
        # 简化实现，按状态统计
        status_counts = {}
        for app in filtered_applications:
            status_counts[app.status] = status_counts.get(app.status, 0) + 1

        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'type': trend_type
            },
            'totalApplications': len(filtered_applications),
            'statusBreakdown': status_counts,
            'avgApplicationsPerPeriod': len(filtered_applications) / 4 if trend_type == 'weekly' else len(filtered_applications) / 6
        }

# 全局业务逻辑服务实例
business_service = BusinessLogicService()