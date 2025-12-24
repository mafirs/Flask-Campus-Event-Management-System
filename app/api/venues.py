from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import admin_required, get_current_user_id
from datetime import datetime
from app import db
from app.models.venue import Venue
from app.models.application import Application


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

            # 构建查询
            query = Venue.query

            if status:
                query = query.filter_by(status=status)

            if search:
                search_pattern = f'%{search}%'
                query = query.filter(
                    db.or_(
                        Venue.name.ilike(search_pattern),
                        Venue.location.ilike(search_pattern),
                        Venue.description.ilike(search_pattern)
                    )
                )

            # 分页
            pagination = query.order_by(Venue.created_at.desc()).paginate(
                page=page, per_page=size, error_out=False
            )
            venues_page = pagination.items
            total = pagination.total

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
            venue = Venue(
                name=data['name'],
                location=data['location'],
                capacity=capacity,
                description=data['description'],
                status='available'
            )

            db.session.add(venue)
            db.session.commit()

            return success_response(venue.to_dict(), "场地创建成功")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")


class VenueResource(Resource):
    """单个场地资源"""

    @jwt_required()
    def get(self, venue_id):
        """获取场地详情"""
        try:
            venue = db.session.get(Venue, venue_id)
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
            venue = db.session.get(Venue, venue_id)
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

            # 更新字段
            if 'name' in data:
                venue.name = data['name']
            if 'location' in data:
                venue.location = data['location']
            if 'capacity' in data:
                venue.capacity = data['capacity']
            if 'description' in data:
                venue.description = data['description']
            if 'status' in data:
                venue.status = data['status']

            venue.updated_at = datetime.utcnow()
            db.session.commit()

            return success_response(venue.to_dict(), "场地更新成功")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def delete(self, venue_id):
        """删除场地"""
        try:
            venue = db.session.get(Venue, venue_id)
            if not venue:
                return error_response(404, "场地不存在")

            # 检查是否有相关申请
            has_applications = db.session.query(Application).filter(
                Application.venue_id == venue_id,
                Application.status.in_(['pending_reviewer', 'pending_admin', 'approved'])
            ).first() is not None

            if has_applications:
                return error_response(400, "该场地有待审批或已通过的申请，无法删除")

            # 删除场地
            db.session.delete(venue)
            db.session.commit()

            return success_response(None, "场地删除成功")

        except Exception as e:
            db.session.rollback()
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
            available_venues = []

            venues = Venue.query.filter_by(status='available').all()

            for venue in venues:
                # 检查时间冲突
                conflicting_apps = db.session.query(Application).filter(
                    Application.venue_id == venue.id,
                    Application.status.in_(['pending_reviewer', 'pending_admin', 'approved'])
                ).all()

                has_conflict = any(
                    app.has_time_conflict(start_time, end_time)
                    for app in conflicting_apps
                )

                if not has_conflict:
                    available_venues.append(venue)

            venues_data = [venue.to_dict_simple() for venue in available_venues]
            return success_response(venues_data)

        except Exception as e:
            current_app.logger.error(f"查询可用场地错误: {str(e)}")
            return error_response(500, "服务器内部错误")
