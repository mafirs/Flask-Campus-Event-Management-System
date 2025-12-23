from flask import jsonify
from typing import Any, Optional

def success_response(data: Any = None, message: str = "success") -> tuple:
    """
    统一成功响应格式

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        "code": 200,
        "message": message,
        "data": data
    }
    return response, 200

def error_response(code: int, message: str, data: Any = None) -> tuple:
    """
    统一错误响应格式

    Args:
        code: 错误码
        message: 错误消息
        data: 额外数据

    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        "code": code,
        "message": message,
        "data": data
    }

    # 根据错误码确定HTTP状态码
    if 400 <= code < 500:
        status_code = 400
    elif 500 <= code < 600:
        status_code = 500
    else:
        status_code = 400

    return response, status_code

def paginated_response(items: list, total: int, page: int, size: int, message: str = "success") -> tuple:
    """
    分页响应格式

    Args:
        items: 数据列表
        total: 总数
        page: 当前页码
        size: 每页数量
        message: 响应消息

    Returns:
        tuple: (response_json, status_code)
    """
    data = {
        "list": items,
        "total": total,
        "page": page,
        "size": size
    }
    return success_response(data, message)