from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import reviewer_required, get_current_user_id
from app.services.mock_data import mock_data_service

class PendingApprovalResource(Resource):
    """待审批申请列表资源"""

    @reviewer_required
    def get(self):
        """获取待审批列表"""
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))

            # 获取待审批申请
            applications = mock_data_service.get_pending_applications()

            # 按创建时间倒序排列
            applications.sort(key=lambda x: x.created_at, reverse=True)

            # 分页
            total = len(applications)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            applications_page = applications[start_idx:end_idx]

            applications_data = []
            for app in applications_page:
                # 获取申请人信息
                user = mock_data_service.get_user_by_id(app.user_id)
                user_info = user.to_dict_safe() if user else {}

                # 获取场地信息
                venue = mock_data_service.get_venue_by_id(app.venue_id)
                venue_info = venue.to_dict() if venue else {}

                # 获取物资详细信息（包含库存状态）
                material_details = []
                for app_material in app.materials:
                    material = mock_data_service.get_material_by_id(app_material.material_id)
                    if material:
                        stock_status = material.get_stock_status(app_material.quantity)
                        material_details.append({
                            'materialId': material.id,
                            'materialName': material.name,
                            'requestedQuantity': app_material.quantity,
                            'availableQuantity': material.available_quantity,
                            'totalQuantity': material.total_quantity,
                            'unit': material.unit,
                            'stockStatus': stock_status
                        })

                app_data = {
                    'id': app.id,
                    'activityName': app.activity_name,
                    'activityDescription': app.activity_description,
                    'applicantName': user_info.get('realName', ''),
                    'applicantUsername': user_info.get('username', ''),
                    'venueName': venue_info.get('name', ''),
                    'venueLocation': venue_info.get('location', ''),
                    'venueCapacity': venue_info.get('capacity', 0),
                    'startTime': app.start_time,
                    'endTime': app.end_time,
                    'materials': material_details,
                    'createdAt': app.created_at.isoformat()
                }
                applications_data.append(app_data)

            return paginated_response(applications_data, total, page, size)

        except ValueError as e:
            return error_response(400, "参数格式错误")
        except Exception as e:
            current_app.logger.error(f"获取待审批列表错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class ApplicationApproveResource(Resource):
    """申请审批通过资源"""

    @reviewer_required
    def put(self, application_id):
        """审批申请通过"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            application = mock_data_service.get_application_by_id(application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 检查是否可以审批
            if not application.can_be_reviewed():
                return error_response(400, f"当前状态 {application.status} 的申请无法审批")

            # 再次检查场地和物资的可用性（防止审批期间被占用）
            venue = mock_data_service.get_venue_by_id(application.venue_id)
            if not venue or not venue.is_available():
                return error_response(400, "场地当前不可用，无法通过审批")

            # 检查物资库存
            for app_material in application.materials:
                material = mock_data_service.get_material_by_id(app_material.material_id)
                if not material or not material.is_available():
                    return error_response(400, f"物资 {material.name} 当前不可用，无法通过审批")

            # 审批通过（库存已经在申请时预占）
            success = mock_data_service.update_application_status(
                application_id, 'approved', reviewer_id=current_user_id
            )

            if not success:
                return error_response(500, "审批失败")

            updated_application = mock_data_service.get_application_by_id(application_id)

            return success_response({
                'id': updated_application.id,
                'status': updated_application.status,
                'reviewerId': updated_application.reviewer_id,
                'reviewedAt': updated_application.reviewed_at.isoformat()
            }, "申请已通过")

        except Exception as e:
            current_app.logger.error(f"审批申请错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class ApplicationRejectResource(Resource):
    """申请审批驳回资源"""

    @reviewer_required
    def put(self, application_id):
        """审批申请驳回"""
        try:
            current_user_id = get_current_user_id()
            if not current_user_id:
                return error_response(401, "无效的用户信息")

            data = request.get_json()
            if not data or not data.get('reason'):
                return error_response(400, "请提供驳回理由")

            reason = data.get('reason').strip()
            if not reason:
                return error_response(400, "驳回理由不能为空")

            application = mock_data_service.get_application_by_id(application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 检查是否可以审批
            if not application.can_be_reviewed():
                return error_response(400, f"当前状态 {application.status} 的申请无法审批")

            # 审批驳回（会自动释放预占的库存）
            success = mock_data_service.update_application_status(
                application_id, 'rejected',
                reviewer_id=current_user_id,
                reason=reason
            )

            if not success:
                return error_response(500, "审批失败")

            updated_application = mock_data_service.get_application_by_id(application_id)

            return success_response({
                'id': updated_application.id,
                'status': updated_application.status,
                'rejectionReason': updated_application.rejection_reason,
                'reviewerId': updated_application.reviewer_id,
                'reviewedAt': updated_application.reviewed_at.isoformat()
            }, "申请已驳回")

        except Exception as e:
            current_app.logger.error(f"驳回申请错误: {str(e)}")
            return error_response(500, "服务器内部错误")