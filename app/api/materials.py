from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.utils.response import success_response, error_response, paginated_response
from app.utils.auth import admin_required
from app.services.mock_data import mock_data_service

class MaterialListResource(Resource):
    """物资列表资源"""

    @jwt_required()
    def get(self):
        """获取物资列表"""
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))
            category = request.args.get('category')
            status = request.args.get('status')
            search = request.args.get('search', '').strip()

            # 获取所有物资
            materials = mock_data_service.get_all_materials()

            # 分类筛选
            if category:
                materials = [m for m in materials if m.category == category]

            # 状态筛选
            if status:
                materials = [m for m in materials if m.status == status]

            # 搜索筛选
            if search:
                search_lower = search.lower()
                materials = [
                    m for m in materials
                    if search_lower in m.name.lower() or
                       search_lower in m.description.lower() or
                       search_lower in m.category.lower()
                ]

            # 分页
            total = len(materials)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            materials_page = materials[start_idx:end_idx]

            materials_data = [material.to_dict() for material in materials_page]

            return paginated_response(materials_data, total, page, size)

        except ValueError as e:
            return error_response(400, "参数格式错误")
        except Exception as e:
            current_app.logger.error(f"获取物资列表错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def post(self):
        """创建物资"""
        try:
            data = request.get_json()
            if not data:
                return error_response(400, "请提供物资信息")

            # 验证必填字段
            required_fields = ['name', 'category', 'totalQuantity', 'unit', 'description']
            for field in required_fields:
                if not data.get(field):
                    return error_response(400, f"{field} 不能为空")

            # 验证数量
            total_quantity = data.get('totalQuantity')
            if not isinstance(total_quantity, int) or total_quantity <= 0:
                return error_response(400, "总数量必须是正整数")

            # 创建物资
            material = mock_data_service.create_material(data)

            return success_response(material.to_dict(), "物资创建成功")

        except Exception as e:
            current_app.logger.error(f"创建物资错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class MaterialResource(Resource):
    """单个物资资源"""

    @jwt_required()
    def get(self, material_id):
        """获取物资详情"""
        try:
            material = mock_data_service.get_material_by_id(material_id)
            if not material:
                return error_response(404, "物资不存在")

            return success_response(material.to_dict())

        except Exception as e:
            current_app.logger.error(f"获取物资详情错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def put(self, material_id):
        """更新物资"""
        try:
            material = mock_data_service.get_material_by_id(material_id)
            if not material:
                return error_response(404, "物资不存在")

            data = request.get_json()
            if not data:
                return error_response(400, "请提供更新信息")

            # 验证数量
            if 'totalQuantity' in data:
                total_quantity = data.get('totalQuantity')
                if not isinstance(total_quantity, int) or total_quantity <= 0:
                    return error_response(400, "总数量必须是正整数")

                # 确保总数量不小于已占用数量
                current_occupied = material.total_quantity - material.available_quantity
                if total_quantity < current_occupied:
                    return error_response(400, f"总数量不能小于已占用数量 {current_occupied}")

            # 更新可用数量（如果提供了）
            if 'availableQuantity' in data:
                available_quantity = data.get('availableQuantity')
                if not isinstance(available_quantity, int) or available_quantity < 0:
                    return error_response(400, "可用数量必须是非负整数")

                # 确保可用数量不超过总数量
                total_quantity = data.get('totalQuantity', material.total_quantity)
                if available_quantity > total_quantity:
                    return error_response(400, "可用数量不能超过总数量")

            # 更新物资
            success = mock_data_service.update_material(material_id, data)
            if not success:
                return error_response(500, "更新物资失败")

            updated_material = mock_data_service.get_material_by_id(material_id)
            return success_response(updated_material.to_dict(), "物资更新成功")

        except Exception as e:
            current_app.logger.error(f"更新物资错误: {str(e)}")
            return error_response(500, "服务器内部错误")

    @admin_required
    def delete(self, material_id):
        """删除物资"""
        try:
            material = mock_data_service.get_material_by_id(material_id)
            if not material:
                return error_response(404, "物资不存在")

            # 检查是否有相关申请
            applications = mock_data_service.get_all_applications()
            has_applications = any(
                any(m.material_id == material_id for m in app.materials)
                for app in applications
                if app.status in ['pending', 'approved']
            )

            if has_applications:
                return error_response(400, "该物资有待审批或已通过的申请，无法删除")

            # 删除物资
            success = mock_data_service.delete_material(material_id)
            if not success:
                return error_response(500, "删除物资失败")

            return success_response(None, "物资删除成功")

        except Exception as e:
            current_app.logger.error(f"删除物资错误: {str(e)}")
            return error_response(500, "服务器内部错误")