from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import admin_required, get_current_user_id
from app.services.mock_data import mock_data_service
from datetime import datetime
import re

class VenueListResource(Resource):
    """场地列表资源"""

    @jwt_required()
    def get(self):
        """获取场地列表"""
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))
            status = request.args.get('status')
            search = request.args.get('search', '').strip()

            # 获取所有场地
            venues = mock_data_service.get_all_venues()

            # 状态筛选
            if status:
                venues = [v for v in venues if v.status == status]

            # 搜索筛选
            if search:
                search_lower = search.lower()
                venues = [
                    v for v in venues
                    if search_lower in v.name.lower() or
                       search_lower in v.location.lower() or
                       search_lower in v.description.lower()
                ]

            # 分页
            total = len(venues)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            venues_page = venues[start_idx:end_idx]

            venues_data = [venue.to_dict() for venue in venues_page]

            return paginated_response(venues_data, total, page, size)

        except ValueError as e:
            return error_response(400, "参数格式错误")
        except Exception as e:
            current_app.logger.error(f"获取场地列表错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def post(self):
        """创建场地"""
        try:
            data = request.get_json()
            if not data:
                return error_response(400, "请提供场地信息")

            # 验证必填字段
            required_fields = ['name', 'location', 'capacity', 'description']
            for field in required_fields:
                if not data.get(field):
                    return error_response(400, f"{field} 不能为空")

            # 验证容量
            capacity = data.get('capacity')
            if not isinstance(capacity, int) or capacity <= 0:
                return error_response(400, "容量必须是正整数")

            # 创建场地
            venue = mock_data_service.create_venue(data)

            return success_response(venue.to_dict(), "场地创建成功")

        except Exception as e:
            current_app.logger.error(f"创建场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class VenueResource(Resource):
    """单个场地资源"""

    @jwt_required()
    def get(self, venue_id):
        """获取场地详情"""
        try:
            venue = mock_data_service.get_venue_by_id(venue_id)
            if not venue:
                return error_response(404, "场地不存在")

            return success_response(venue.to_dict())

        except Exception as e:
            current_app.logger.error(f"获取场地详情错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def put(self, venue_id):
        """更新场地"""
        try:
            venue = mock_data_service.get_venue_by_id(venue_id)
            if not venue:
                return error_response(404, "场地不存在")

            data = request.get_json()
            if not data:
                return error_response(400, "请提供更新信息")

            # 验证容量
            if 'capacity' in data:
                capacity = data.get('capacity')
                if not isinstance(capacity, int) or capacity <= 0:
                    return error_response(400, "容量必须是正整数")

            # 更新场地
            success = mock_data_service.update_venue(venue_id, data)
            if not success:
                return error_response(500, "更新场地失败")

            updated_venue = mock_data_service.get_venue_by_id(venue_id)
            return success_response(updated_venue.to_dict(), "场地更新成功")

        except Exception as e:
            current_app.logger.error(f"更新场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def delete(self, venue_id):
        """删除场地"""
        try:
            venue = mock_data_service.get_venue_by_id(venue_id)
            if not venue:
                return error_response(404, "场地不存在")

            # 检查是否有相关申请
            applications = mock_data_service.get_all_applications()
            has_applications = any(
                app.venue_id == venue_id and app.status in ['pending', 'approved']
                for app in applications
            )

            if has_applications:
                return error_response(400, "该场地有待审批或已通过的申请，无法删除")

            # 删除场地
            success = mock_data_service.delete_venue(venue_id)
            if not success:
                return error_response(500, "删除场地失败")

            return success_response(None, "场地删除成功")

        except Exception as e:
            current_app.logger.error(f"删除场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class VenueAvailableResource(Resource):
    """可用场地查询资源"""

    @jwt_required()
    def get(self):
        """获取指定时间段的可用场地"""
        try:
            start_time = request.args.get('startTime')
            end_time = request.args.get('endTime')

            if not start_time or not end_time:
                return error_response(400, "请提供开始时间和结束时间")

            # 验证时间格式
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                return error_response(400, "时间格式错误，请使用ISO 8601格式")

            if start_dt >= end_dt:
                return error_response(400, "开始时间必须早于结束时间")

            # 获取所有可用的场地
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

            venues_data = [venue.to_dict_simple() for venue in available_venues]
            return success_response(venues_data)

        except Exception as e:
            current_app.logger.error(f"查询可用场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")