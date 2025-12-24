from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import token_required, get_current_user_id, is_admin
from datetime import datetime
from app import db
from app.models.user import User
from app.models.venue import Venue
from app.models.material import Material
from app.models.application import Application, ApplicationMaterial


class ApplicationListResource(Resource):
    """申请列表资源 - 用于创建申请"""

    @jwt_required()
    def post(self):
        """创建申请"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            data = request.get_json()
            if not data:
                return error_response(400, "请提供申请信息")

            # 验证必填字段
            required_fields = ['activityName', 'activityDescription', 'venueId', 'startTime', 'endTime']
            for field in required_fields:
                if not data.get(field):
                    return error_response(400, f"{field} 不能为空")

            # 验证时间格式
            try:
                start_dt = datetime.fromisoformat(data['startTime'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(data['endTime'].replace('Z', '+00:00'))
            except ValueError:
                return error_response(400, "时间格式错误，请使用ISO 8601格式")

            # 验证时间逻辑
            if start_dt >= end_dt:
                return error_response(400, "开始时间必须早于结束时间")

            if start_dt <= datetime.utcnow().replace(tzinfo=start_dt.tzinfo):
                return error_response(400, "申请时间不能是过去时间")

            # 获取当前用户
            user = db.session.get(User, current_user_id)
            if not user:
                return error_response(404, "用户不存在")

            # 基于角色的差异化审批流
            if user.role == 'user':
                initial_status = 'pending_reviewer'
            else:
                initial_status = 'pending_admin'

            # 验证场地是否存在且可用
            venue = db.session.get(Venue, data['venueId'])
            if not venue:
                return error_response(404, "场地不存在")

            if not venue.is_available():
                return error_response(400, "场地当前不可用")

            # 检查场地时间冲突
            conflicting_apps = db.session.query(Application).filter(
                Application.venue_id == venue.id,
                Application.status.in_(['pending_reviewer', 'pending_admin', 'approved'])
            ).all()

            for app in conflicting_apps:
                if app.has_time_conflict(data['startTime'], data['endTime']):
                    return error_response(400, "该时间段场地已被预约")

            # 验证物资并扣减库存
            materials_data = data.get('materials', [])
            if not materials_data:
                return error_response(400, "请至少申请一个物资")

            app_materials_list = []
            for material_item in materials_data:
                material_id = material_item.get('materialId')
                quantity = material_item.get('quantity')

                if not material_id or not quantity:
                    return error_response(400, "物资ID和数量不能为空")

                if not isinstance(quantity, int) or quantity <= 0:
                    return error_response(400, "物资数量必须是正整数")

                material = db.session.get(Material, material_id)
                if not material:
                    return error_response(404, f"物资ID {material_id} 不存在")

                if not material.is_available():
                    return error_response(400, f"物资 {material.name} 当前不可用")

                if material.available_quantity < quantity:
                    return error_response(400, f"物资 {material.name} 库存不足，当前可用数量: {material.available_quantity}")

                # 扣减库存
                material.available_quantity -= quantity

                app_material = ApplicationMaterial(
                    material_id=material_id,
                    quantity=quantity
                )
                app_materials_list.append(app_material)

            # 创建申请
            application = Application(
                id=None,
                user_id=current_user_id,
                activity_name=data['activityName'],
                activity_description=data['activityDescription'],
                venue_id=data['venueId'],
                start_time=data['startTime'],
                end_time=data['endTime'],
                materials=app_materials_list,
                status=initial_status
            )

            db.session.add(application)
            db.session.commit()

            return success_response({
                'id': application.id,
                'activityName': application.activity_name,
                'status': application.status,
                'createdAt': application.created_at.isoformat()
            }, "申请提交成功")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建申请错误: {str(e)}")
            import traceback
            current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return error_response(500, f"服务器内部错误: {str(e)}")


class ApplicationResource(Resource):
    """申请详情资源"""

    @jwt_required()
    def get(self, application_id):
        """获取申请详情"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            application = db.session.get(Application, application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 权限检查：只有申请人、管理员可以查看
            if (application.user_id != current_user_id and not is_admin()):
                return error_response(403, "权限不足")

            # 获取详细信息
            user = db.session.get(User, application.user_id)
            venue = db.session.get(Venue, application.venue_id)

            # 构建物资详细信息
            material_details = []
            for app_material in application.materials:
                material = db.session.get(Material, app_material.material_id)
                if material:
                    material_details.append({
                        'materialId': material.id,
                        'materialName': material.name,
                        'quantity': app_material.quantity,
                        'unit': material.unit
                    })

            application_data = application.to_dict_with_details(
                user_info=user.to_dict_safe() if user else {},
                venue_info=venue.to_dict() if venue else {},
                material_details=material_details
            )

            return success_response(application_data)

        except Exception as e:
            current_app.logger.error(f"获取申请详情错误: {str(e)}")
            return error_response(500, "服务器内部错误")


class MyApplicationResource(Resource):
    """我的申请列表资源"""

    @jwt_required()
    def get(self):
        """获取我的申请列表"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))
            status = request.args.get('status')

            # 构建查询
            query = Application.query.filter_by(user_id=current_user_id)

            if status:
                query = query.filter_by(status=status)

            query = query.order_by(Application.created_at.desc())

            # 分页
            pagination = query.paginate(page=page, per_page=size, error_out=False)
            applications_page = pagination.items
            total = pagination.total

            applications_data = []
            for app in applications_page:
                venue = db.session.get(Venue, app.venue_id)
                venue_info = venue.to_dict() if venue else {}

                material_details = []
                for app_material in app.materials:
                    material = db.session.get(Material, app_material.material_id)
                    if material:
                        material_details.append({
                            'materialId': material.id,
                            'materialName': material.name,
                            'quantity': app_material.quantity,
                            'unit': material.unit
                        })

                app_data = {
                    'id': app.id,
                    'activityName': app.activity_name,
                    'activityDescription': app.activity_description,
                    'venueName': venue_info.get('name', ''),
                    'venueLocation': venue_info.get('location', ''),
                    'startTime': app.start_time,
                    'endTime': app.end_time,
                    'status': app.status,
                    'materials': material_details,
                    'rejectionReason': app.rejection_reason,
                    'createdAt': app.created_at.isoformat(),
                    'reviewedAt': app.reviewed_at.isoformat() if app.reviewed_at else None
                }
                applications_data.append(app_data)

            return paginated_response(applications_data, total, page, size)

        except ValueError as e:
            return error_response(400, "参数格式错误")
        except Exception as e:
            current_app.logger.error(f"获取我的申请列表错误: {str(e)}")
            return error_response(500, "服务器内部错误")


class ApplicationCancelResource(Resource):
    """申请取消资源"""

    @jwt_required()
    def put(self, application_id):
        """取消申请"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            application = db.session.get(Application, application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 权限检查：只有申请人本人或管理员可以取消
            if (application.user_id != current_user_id and not is_admin()):
                return error_response(403, "权限不足")

            # 检查是否可以取消（处理新旧状态值）
            if not application.can_be_cancelled() and application.status not in ['pending_reviewer', 'pending_admin']:
                return error_response(400, f"当前状态 {application.status} 的申请无法取消")

            # 更新状态
            application.status = 'cancelled'
            application.updated_at = datetime.utcnow()

            # 归还库存
            for app_material in application.materials:
                material = db.session.get(Material, app_material.material_id)
                if material:
                    material.available_quantity = min(
                        material.available_quantity + app_material.quantity,
                        material.total_quantity
                    )

            db.session.commit()

            return success_response({
                'id': application.id,
                'status': application.status,
                'updatedAt': application.updated_at.isoformat()
            }, "申请已取消")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"取消申请错误: {str(e)}")
            return error_response(500, "服务器内部错误")
