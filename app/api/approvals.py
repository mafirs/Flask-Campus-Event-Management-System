from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import reviewer_required, get_current_user_id
from datetime import datetime
from app import db
from app.models.user import User
from app.models.venue import Venue
from app.models.material import Material
from app.models.application import Application


class PendingApprovalResource(Resource):
    """待审批申请列表资源"""

    @reviewer_required
    def get(self):
        """获取待审批列表"""
        try:
            current_user_id = get_current_user_id()
            current_user = db.session.get(User, current_user_id)

            if not current_user:
                return error_response(401, "无效的用户信息")

            # 差异化查询：基于角色确定目标状态
            if current_user.role == 'reviewer':
                target_status = 'pending_reviewer'
            elif current_user.role == 'admin':
                target_status = 'pending_admin'
            else:
                return error_response(403, "权限不足")

            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))

            # 查询待审批申请
            query = Application.query.filter_by(status=target_status).order_by(
                Application.created_at.desc()
            )

            pagination = query.paginate(page=page, per_page=size, error_out=False)
            applications_page = pagination.items
            total = pagination.total

            applications_data = []
            for app in applications_page:
                # 获取申请人信息
                user = db.session.get(User, app.user_id)

                # 获取场地信息
                venue = db.session.get(Venue, app.venue_id)

                # 获取物资详细信息（包含库存状态）
                material_details = []
                for app_material in app.materials:
                    material = db.session.get(Material, app_material.material_id)
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
                    'applicantName': user.real_name if user else '',
                    'applicantUsername': user.username if user else '',
                    'venueName': venue.name if venue else '',
                    'venueLocation': venue.location if venue else '',
                    'venueCapacity': venue.capacity if venue else 0,
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
            current_user = db.session.get(User, current_user_id)

            if not current_user:
                return error_response(401, "无效的用户信息")

            application = db.session.get(Application, application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 导员审批流程
            if current_user.role == 'reviewer':
                if application.status != 'pending_reviewer':
                    return error_response(400, "非待导员审核状态")
                # 流转给管理员
                application.status = 'pending_admin'

            # 管理员审批流程
            elif current_user.role == 'admin':
                if application.status != 'pending_admin':
                    return error_response(400, "非待管理员审核状态")
                # 最终通过
                application.status = 'approved'

            else:
                return error_response(403, "权限不足")

            # 更新审批人和时间
            application.reviewer_id = current_user_id
            application.reviewed_at = datetime.utcnow()

            db.session.commit()

            return success_response({
                'id': application.id,
                'status': application.status,
                'reviewerId': application.reviewer_id,
                'reviewedAt': application.reviewed_at.isoformat()
            }, "申请已通过")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"审批申请错误: {str(e)}")
            return error_response(500, "服务器内部错误")


class ApplicationRejectResource(Resource):
    """申请审批驳回资源"""

    @reviewer_required
    def put(self, application_id):
        """审批申请驳回"""
        try:
            current_user_id = get_current_user_id()
            current_user = db.session.get(User, current_user_id)

            if not current_user:
                return error_response(401, "无效的用户信息")

            data = request.get_json()
            if not data or not data.get('rejectionReason'):
                return error_response(400, "请提供驳回理由")

            rejection_reason = data.get('rejectionReason').strip()
            if not rejection_reason:
                return error_response(400, "驳回理由不能为空")

            application = db.session.get(Application, application_id)
            if not application:
                return error_response(404, "申请不存在")

            # 检查状态：只允许驳回 pending_reviewer 或 pending_admin
            if application.status not in ['pending_reviewer', 'pending_admin']:
                return error_response(400, f"当前状态 {application.status} 的申请无法驳回")

            # 更新状态为 rejected
            application.status = 'rejected'
            application.rejection_reason = rejection_reason
            application.reviewer_id = current_user_id
            application.reviewed_at = datetime.utcnow()

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
                'rejectionReason': application.rejection_reason,
                'reviewerId': application.reviewer_id,
                'reviewedAt': application.reviewed_at.isoformat()
            }, "申请已驳回")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"驳回申请错误: {str(e)}")
            return error_response(500, "服务器内部错误")
