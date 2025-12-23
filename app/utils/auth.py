from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.utils.response import error_response

def token_required(f):
    """
    JWT Token验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return error_response(401, "未提供有效的访问令牌")
    return decorated_function

def role_required(*allowed_roles):
    """
    角色权限验证装饰器

    Args:
        allowed_roles: 允许的角色列表
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()

                # 这里需要从数据库或缓存中获取用户信息
                # 为了简化，暂时从JWT claims中获取角色
                claims = get_jwt()
                user_role = claims.get('role', 'user')

                if user_role not in allowed_roles:
                    return error_response(403, "权限不足")

                return f(*args, **kwargs)
            except Exception as e:
                return error_response(401, "认证失败")
        return decorated_function
    return decorator

def admin_required(f):
    """
    管理员权限装饰器
    """
    return role_required('admin')(f)

def reviewer_required(f):
    """
    审批员权限装饰器
    """
    return role_required('reviewer', 'admin')(f)

def get_current_user_id():
    """
    获取当前用户ID
    """
    try:
        return get_jwt_identity()
    except:
        return None

def get_current_user_role():
    """
    获取当前用户角色
    """
    try:
        claims = get_jwt()
        return claims.get('role', 'user')
    except:
        return None

def is_admin():
    """
    检查当前用户是否为管理员
    """
    return get_current_user_role() == 'admin'

def is_reviewer():
    """
    检查当前用户是否为审批员
    """
    role = get_current_user_role()
    return role == 'reviewer' or role == 'admin'