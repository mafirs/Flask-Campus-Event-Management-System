from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.utils.response import success_response, error_response
from app.utils.auth import get_current_user_id
from app.services.mock_data import mock_data_service

class LoginResource(Resource):
    """用户登录资源"""

    def post(self):
        """用户登录"""
        try:
            data = request.get_json()
            if not data:
                return error_response(400, "请提供用户名和密码")

            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return error_response(400, "用户名和密码不能为空")

            # 验证用户
            user = mock_data_service.get_user_by_username(username)
            if not user or not user.check_password(password):
                return error_response(401, "用户名或密码错误")

            if user.status != 'active':
                return error_response(401, "账户已被禁用")

            # 生成JWT Token
            additional_claims = {
                'role': user.role,
                'username': user.username
            }

            access_token = create_access_token(
                identity=user.id,
                additional_claims=additional_claims
            )

            return success_response({
                'token': access_token,
                'user': user.to_dict_safe()
            }, "登录成功")

        except Exception as e:
            current_app.logger.error(f"登录错误: {str(e)}")
            return error_response(500, "服务器内部错误")

class LogoutResource(Resource):
    """用户登出资源"""

    @jwt_required()
    def post(self):
        """用户登出"""
        # JWT是无状态的，客户端删除token即可
        # 这里可以添加token黑名单逻辑
        return success_response(None, "登出成功")

class ProfileResource(Resource):
    """获取当前用户信息资源"""

    @jwt_required()
    def get(self):
        """获取当前用户信息"""
        try:
            user_id = get_current_user_id()
            if not user_id:
                return error_response(401, "无效的用户信息")

            user = mock_data_service.get_user_by_id(user_id)
            if not user:
                return error_response(404, "用户不存在")

            return success_response(user.to_dict_safe())

        except Exception as e:
            current_app.logger.error(f"获取用户信息错误: {str(e)}")
            return error_response(500, "服务器内部错误")