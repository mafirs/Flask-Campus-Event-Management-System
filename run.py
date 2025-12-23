import os
from app import create_app

# 从环境变量获取配置，默认为开发环境
config_name = os.environ.get('FLASK_ENV', 'development')

# 创建应用实例
app = create_app(config_name)

if __name__ == '__main__':
    # 开发环境启动配置
    debug = app.config.get('DEBUG', False)
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))

    print(f"启动校级活动场地与物资管理系统...")
    print(f"环境: {config_name}")
    print(f"调试模式: {debug}")
    print(f"访问地址: http://{host}:{port}")
    print("=" * 50)

    app.run(debug=debug, host=host, port=port)