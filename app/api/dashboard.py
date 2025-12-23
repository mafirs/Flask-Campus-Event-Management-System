from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response
from app.utils.auth import get_current_user_id, is_admin
from app.services.mock_data import mock_data_service
from datetime import datetime, timedelta
from collections import defaultdict

class DashboardStatsResource(Resource):
    """首页统计数据资源"""

    @jwt_required()
    def get(self):
        """获取首页统计数据"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            # 获取基础统计数据
            venues = mock_data_service.get_all_venues()
            materials = mock_data_service.get_all_materials()
            applications = mock_data_service.get_all_applications()

            # 计算统计数据
            total_venues = len(venues)
            total_materials = len(materials)
            pending_applications = len([app for app in applications if app.status == 'pending'])

            # 计算今日申请数
            today = datetime.utcnow().date()
            today_applications = len([
                app for app in applications
                if app.created_at.date() == today
            ])

            # 计算场地使用率
            approved_applications = [app for app in applications if app.status == 'approved']
            total_capacity = sum(venue.capacity for venue in venues if venue.is_available())
            used_capacity = sum(
                venue.capacity for app in approved_applications
                for venue in venues
                if venue.id == app.venue_id and venue.is_available()
            )
            venue_utilization = used_capacity / total_capacity if total_capacity > 0 else 0

            # 计算物资使用率
            total_material_qty = sum(material.total_quantity for material in materials if material.is_available())
            used_material_qty = sum(
                material.total_quantity - material.available_quantity
                for material in materials
                if material.is_available()
            )
            material_utilization = used_material_qty / total_material_qty if total_material_qty > 0 else 0

            # 获取用户个人申请统计
            user_applications = mock_data_service.get_applications_by_user(current_user_id)
            my_applications_stats = {
                'total': len(user_applications),
                'pending': len([app for app in user_applications if app.status == 'pending']),
                'approved': len([app for app in user_applications if app.status == 'approved']),
                'rejected': len([app for app in user_applications if app.status == 'rejected']),
                'cancelled': len([app for app in user_applications if app.status == 'cancelled'])
            }

            return success_response({
                'totalVenues': total_venues,
                'totalMaterials': total_materials,
                'pendingApplications': pending_applications,
                'todayApplications': today_applications,
                'venueUtilization': round(venue_utilization, 2),
                'materialUtilization': round(material_utilization, 2),
                'myApplications': my_applications_stats
            })

        except Exception as e:
            current_app.logger.error(f"获取统计数据错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class DashboardTrendsResource(Resource):
    """使用趋势数据资源"""

    @jwt_required()
    def get(self):
        """获取使用趋势数据"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            # 权限检查：只有管理员可以查看趋势数据
            if not is_admin():
                return error_response(403, "权限不足")

            # 获取查询参数
            trend_type = request.args.get('type', 'weekly')  # weekly, monthly
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')

            # 设置默认时间范围
            if not end_date:
                end_date = datetime.utcnow()
            else:
                try:
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except ValueError:
                    return error_response(400, "结束时间格式错误")

            if not start_date:
                if trend_type == 'monthly':
                    start_date = end_date - timedelta(days=180)  # 6个月
                else:
                    start_date = end_date - timedelta(days=28)  # 4周
            else:
                try:
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except ValueError:
                    return error_response(400, "开始时间格式错误")

            if start_date >= end_date:
                return error_response(400, "开始时间必须早于结束时间")

            # 获取申请数据
            applications = mock_data_service.get_all_applications()

            # 根据类型分组数据
            if trend_type == 'monthly':
                trend_data = self._get_monthly_trends(applications, start_date, end_date)
            else:
                trend_data = self._get_weekly_trends(applications, start_date, end_date)

            return success_response(trend_data)

        except Exception as e:
            current_app.logger.error(f"获取趋势数据错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    def _get_weekly_trends(self, applications, start_date, end_date):
        """获取周趋势数据"""
        # 按周分组统计
        venue_usage = defaultdict(int)
        material_usage = defaultdict(int)
        application_trends = defaultdict(lambda: {'pending': 0, 'approved': 0, 'rejected': 0})

        for app in applications:
            if start_date <= app.created_at <= end_date:
                # 获取周的开始日期（周一）
                week_start = app.created_at.date() - timedelta(days=app.created_at.weekday())
                date_str = week_start.isoformat()

                # 场地使用统计
                if app.status == 'approved':
                    venue_usage[date_str] += 1

                # 物资使用统计（按物资数量计算）
                if app.status == 'approved':
                    for material in app.materials:
                        material_usage[date_str] += material.quantity

                # 申请状态统计
                application_trends[date_str][app.status] += 1

        # 生成连续的日期序列
        trends = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            week_start = current_date - timedelta(days=current_date.weekday())
            date_str = week_start.isoformat()

            trends.append({
                'date': date_str,
                'venueUsage': venue_usage.get(date_str, 0),
                'materialUsage': material_usage.get(date_str, 0),
                'applicationTrends': application_trends.get(date_str, {'pending': 0, 'approved': 0, 'rejected': 0})
            })

            current_date += timedelta(days=7)

        return {
            'venueUsage': [
                {'date': item['date'], 'count': item['venueUsage']}
                for item in trends if item['venueUsage'] > 0
            ],
            'materialUsage': [
                {'date': item['date'], 'count': item['materialUsage']}
                for item in trends if item['materialUsage'] > 0
            ],
            'applicationTrends': [
                {'date': item['date'], **item['applicationTrends']}
                for item in trends if any(item['applicationTrends'].values())
            ]
        }

    def _get_monthly_trends(self, applications, start_date, end_date):
        """获取月趋势数据"""
        # 按月分组统计
        venue_usage = defaultdict(int)
        material_usage = defaultdict(int)
        application_trends = defaultdict(lambda: {'pending': 0, 'approved': 0, 'rejected': 0})

        for app in applications:
            if start_date <= app.created_at <= end_date:
                # 获取月份的开始日期
                month_start = app.created_at.date().replace(day=1)
                date_str = month_start.isoformat()

                # 场地使用统计
                if app.status == 'approved':
                    venue_usage[date_str] += 1

                # 物资使用统计
                if app.status == 'approved':
                    for material in app.materials:
                        material_usage[date_str] += material.quantity

                # 申请状态统计
                application_trends[date_str][app.status] += 1

        # 生成连续的月份序列
        trends = []
        current_date = start_date.date().replace(day=1)
        while current_date <= end_date.date():
            date_str = current_date.isoformat()

            trends.append({
                'date': date_str,
                'venueUsage': venue_usage.get(date_str, 0),
                'materialUsage': material_usage.get(date_str, 0),
                'applicationTrends': application_trends.get(date_str, {'pending': 0, 'approved': 0, 'rejected': 0})
            })

            # 移动到下个月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        return {
            'venueUsage': [
                {'date': item['date'], 'count': item['venueUsage']}
                for item in trends if item['venueUsage'] > 0
            ],
            'materialUsage': [
                {'date': item['date'], 'count': item['materialUsage']}
                for item in trends if item['materialUsage'] > 0
            ],
            'applicationTrends': [
                {'date': item['date'], **item['applicationTrends']}
                for item in trends if any(item['applicationTrends'].values())
            ]
        }