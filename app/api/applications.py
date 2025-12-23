from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import token_required, get_current_user_id, is_admin
from app.services.mock_data import mock_data_service
from datetime import datetime

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

            # 验证场地是否存在且可用
            venue = mock_data_service.get_venue_by_id(data['venueId'])
            if not venue:
                return error_response(404, "场地不存在")

            if not venue.is_available():
                return error_response(400, "场地当前不可用")

            # 检查场地时间冲突
            applications = mock_data_service.get_all_applications()
            for app in applications:
                if (app.venue_id == data['venueId'] and
                    app.status in ['pending', 'approved'] and
                    app.has_time_conflict(data['startTime'], data['endTime'])):
                    return error_response(400, "该时间段场地已被预约")

            # 验证物资
            materials_data = data.get('materials', [])
            if not materials_data:
                return error_response(400, "请至少申请一个物资")

            for material_item in materials_data:
                material_id = material_item.get('materialId')
                quantity = material_item.get('quantity')

                if not material_id or not quantity:
                    return error_response(400, "物资ID和数量不能为空")

                if not isinstance(quantity, int) or quantity <= 0:
                    return error_response(400, "物资数量必须是正整数")

                # 检查物资是否存在且可用
                material = mock_data_service.get_material_by_id(material_id)
                if not material:
                    return error_response(404, f"物资ID {material_id} 不存在")

                if not material.is_available():
                    return error_response(400, f"物资 {material.name} 当前不可用")

                # 检查库存是否充足
                if material.available_quantity < quantity:
                    return error_response(400, f"物资 {material.name} 库存不足，当前可用数量: {material.available_quantity}")

            # 创建申请（会自动预占库存）
            application = mock_data_service.create_application(data, current_user_id)

            return success_response({
                'id': application.id,
                'activityName': application.activity_name,
                'status': application.status,
                'createdAt': application.created_at.isoformat()
            }, "申请提交成功")

        except Exception as e:
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

            application = mock_data_service.get_application_by_id(application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 权限检查：只有申请人、管理员可以查看
            if (application.user_id != current_user_id and not is_admin()):
                return error_response(403, "权限不足")

            # 获取详细信息
            user = mock_data_service.get_user_by_id(application.user_id)
            venue = mock_data_service.get_venue_by_id(application.venue_id)

            # 构建物资详细信息
            material_details = []
            for app_material in application.materials:
                material = mock_data_service.get_material_by_id(app_material.material_id)
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

            # 获取用户的申请
            applications = mock_data_service.get_applications_by_user(current_user_id)

            # 状态筛选
            if status:
                applications = [app for app in applications if app.status == status]

            # 按创建时间倒序排列
            applications.sort(key=lambda x: x.created_at, reverse=True)

            # 分页
            total = len(applications)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            applications_page = applications[start_idx:end_idx]

            applications_data = []
            for app in applications_page:
                # 获取场地信息
                venue = mock_data_service.get_venue_by_id(app.venue_id)
                venue_info = venue.to_dict() if venue else {}

                # 获取物资信息
                material_details = []
                for app_material in app.materials:
                    material = mock_data_service.get_material_by_id(app_material.material_id)
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

            application = mock_data_service.get_application_by_id(application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 权限检查：只有申请人本人或管理员可以取消
            if (application.user_id != current_user_id and not is_admin()):
                return error_response(403, "权限不足")

            # 检查是否可以取消
            if not application.can_be_cancelled():
                return error_response(400, f"当前状态 {application.status} 的申请无法取消")

            # 取消申请（会自动释放库存）
            success = mock_data_service.update_application_status(application_id, 'cancelled')
            if not success:
                return error_response(500, "取消申请失败")

            updated_application = mock_data_service.get_application_by_id(application_id)

            return success_response({
                'id': updated_application.id,
                'status': updated_application.status,
                'updatedAt': updated_application.updated_at.isoformat()
            }, "申请已取消")

        except Exception as e:
            current_app.logger.error(f"取消申请错误: {str(e)}")
            return error_response(500, "服务器内部错误")