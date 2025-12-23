from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from app.config import config

def create_app(config_name='default'):
    """
    Flask应用工厂函数

    Args:
        config_name: 配置名称

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化扩展
    CORS(app, origins=app.config['CORS_ORIGINS'])
    jwt = JWTManager(app)
    api = Api(app)

    # 注册蓝图
    from app.api import auth_bp, venues_bp, materials_bp, applications_bp, approvals_bp, dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(venues_bp, url_prefix='/api/venues')
    app.register_blueprint(materials_bp, url_prefix='/api/materials')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # 注册API资源到对应的蓝图
    from app.api.auth import LoginResource, LogoutResource, ProfileResource
    from app.api.venues import VenueListResource, VenueResource, VenueAvailableResource
    from app.api.materials import MaterialListResource, MaterialResource
    from app.api.applications import ApplicationListResource, ApplicationResource, MyApplicationResource, ApplicationCancelResource
    from app.api.approvals import PendingApprovalResource, ApplicationApproveResource, ApplicationRejectResource
    from app.api.dashboard import DashboardStatsResource, DashboardTrendsResource

    # 认证相关API
    api.add_resource(LoginResource, '/api/auth/login')
    api.add_resource(LogoutResource, '/api/auth/logout')
    api.add_resource(ProfileResource, '/api/auth/profile')

    # 场地管理API
    api.add_resource(VenueListResource, '/api/venues')
    api.add_resource(VenueResource, '/api/venues/<int:venue_id>')
    api.add_resource(VenueAvailableResource, '/api/venues/available')

    # 物资管理API
    api.add_resource(MaterialListResource, '/api/materials')
    api.add_resource(MaterialResource, '/api/materials/<int:material_id>')

    # 申请管理API
    api.add_resource(ApplicationListResource, '/api/applications')
    api.add_resource(ApplicationResource, '/api/applications/<int:application_id>')
    api.add_resource(MyApplicationResource, '/api/applications/my')
    api.add_resource(ApplicationCancelResource, '/api/applications/<int:application_id>/cancel')

    # 审批管理API
    api.add_resource(PendingApprovalResource, '/api/approvals/pending')
    api.add_resource(ApplicationApproveResource, '/api/applications/<int:application_id>/approve')
    api.add_resource(ApplicationRejectResource, '/api/applications/<int:application_id>/reject')

    # 统计分析API
    api.add_resource(DashboardStatsResource, '/api/dashboard/stats')
    api.add_resource(DashboardTrendsResource, '/api/dashboard/trends')

    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'code': 404, 'message': '接口不存在', 'data': None}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'code': 500, 'message': '服务器内部错误', 'data': None}, 500

    @app.errorhandler(400)
    def bad_request(error):
        return {'code': 400, 'message': '请求参数错误', 'data': None}, 400

    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'code': 401, 'message': '访问令牌已过期', 'data': None}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'code': 401, 'message': '无效的访问令牌', 'data': None}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'code': 401, 'message': '需要提供访问令牌', 'data': None}, 401

    return app