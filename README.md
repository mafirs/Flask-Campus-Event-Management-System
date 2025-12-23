# 校级活动场地与物资管理系统

基于Flask的校级活动场地与物资管理系统，提供完整的场地预约、物资管理、申请审批等功能。

## 项目概述

本系统是一个完整的校园活动管理平台，支持：
- 🏢 场地预约和管理
- 📦 物资借用和库存管理
- 📝 活动申请和审批流程
- 📊 数据统计和趋势分析
- 🔐 多级权限管理

## 技术栈

- **后端框架**: Flask 2.3.3 + Flask-RESTful 0.3.10
- **身份认证**: Flask-JWT-Extended 4.5.3
- **跨域支持**: Flask-CORS 4.0.0
- **数据存储**: Mock数据（内存存储，易于扩展）
- **Python版本**: 3.8+

## 项目结构

```
project/
├── README.md                   # 项目说明文档
├── front-to-back.txt          # 前后端接口文档
├── requirements.txt           # Python依赖包
├── run.py                     # 应用启动文件
├── test_api.py               # API测试脚本
└── app/                      # 主应用目录
    ├── __init__.py           # Flask应用工厂
    ├── config.py             # 配置文件
    ├── models/               # 数据模型
    │   ├── user.py          # 用户模型
    │   ├── venue.py         # 场地模型
    │   ├── material.py      # 物资模型
    │   └── application.py   # 申请模型
    ├── api/                  # API路由层
    │   ├── auth.py          # 认证API
    │   ├── venues.py        # 场地管理API
    │   ├── materials.py     # 物资管理API
    │   ├── applications.py  # 申请管理API
    │   ├── approvals.py     # 审批管理API
    │   └── dashboard.py     # 统计数据API
    ├── utils/               # 工具函数
    │   ├── auth.py          # JWT认证工具
    │   └── response.py      # 统一响应格式
    └── services/            # 业务逻辑层
        ├── mock_data.py     # Mock数据服务
        └── business_logic.py # 业务逻辑服务
```

## 快速开始

### 1. 环境准备

```bash
# 确保Python 3.8+已安装
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 启动开发服务器
python run.py

# 服务将在 http://localhost:5000 启动
```

### 3. 测试API

```bash
# 运行API测试脚本
python test_api.py
```

## 默认账户

系统预置了以下测试账户：

| 用户名 | 密码 | 角色 | 权限说明 |
|--------|------|------|----------|
| admin | admin | admin | 系统管理员 - 全部权限 |
| reviewer | reviewer | reviewer | 审批员 - 审批+查看权限 |
| user1 | user1 | user | 普通用户 - 张三 |
| user2 | user2 | user | 普通用户 - 李四 |

## API文档

### 认证接口

#### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}
```

#### 获取用户信息
```http
GET /api/auth/profile
Authorization: Bearer <token>
```

### 场地管理

#### 获取场地列表
```http
GET /api/venues?page=1&size=10&status=available&search=关键词
Authorization: Bearer <token>
```

#### 创建场地（管理员）
```http
POST /api/venues
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "新场地",
  "location": "E栋101",
  "capacity": 100,
  "description": "新创建的场地",
  "equipment": ["设备1", "设备2"]
}
```

### 物资管理

#### 获取物资列表
```http
GET /api/materials?page=1&size=10&category=电子设备&status=available
Authorization: Bearer <token>
```

### 申请管理

#### 创建申请
```http
POST /api/applications
Authorization: Bearer <token>
Content-Type: application/json

{
  "activityName": "活动名称",
  "activityDescription": "活动描述",
  "venueId": 1,
  "startTime": "2024-01-01T14:00:00Z",
  "endTime": "2024-01-01T16:00:00Z",
  "materials": [
    {"materialId": 1, "quantity": 2},
    {"materialId": 2, "quantity": 10}
  ]
}
```

### 审批管理

#### 获取待审批列表
```http
GET /api/approvals/pending?page=1&size=10
Authorization: Bearer <token>
```

#### 审批通过
```http
PUT /api/applications/{id}/approve
Authorization: Bearer <token>
```

### 统计分析

#### 获取首页统计
```http
GET /api/dashboard/stats
Authorization: Bearer <token>
```

## 响应格式

所有API接口都使用统一的响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 权限控制

| 角色 | 权限说明 |
|------|----------|
| admin | 全部权限（CRUD、审批、统计） |
| reviewer | 审批权限 + 查看权限 |
| user | 申请权限 + 查看权限 |

## 业务规则

1. **时间冲突**: 同一场地同一时间只能有一个通过审批的申请
2. **库存管理**: 物资申请不能超过可用数量，申请通过时占用库存
3. **申请状态**: pending → approved/rejected/cancelled
4. **审批流程**: 只有pending状态的申请可以审批
5. **取消规则**: 只有pending或approved状态的申请可以取消

## Mock数据

当前版本使用内存Mock数据，包含：

- **4个测试用户**: admin, reviewer, user1(张三), user2(李四)
- **4个测试场地**: 大学生活动中心、体育馆、图书馆报告厅、学生活动室
- **6种测试物资**: 投影仪、折叠椅、麦克风、折叠桌、音响设备、白板
- **2个测试申请**: 社团招新活动(pending)、学术讲座(approved)

## 开发指南

### 扩展数据库

要扩展到真实数据库，需要：

1. 安装数据库驱动（如PyMySQL）
2. 修改配置文件中的数据库连接
3. 将models转换为SQLAlchemy模型
4. 替换mock_data_service为数据库操作

### 添加新功能

1. 在`models/`中定义数据模型
2. 在`services/`中实现业务逻辑
3. 在`api/`中创建API接口
4. 更新权限装饰器
5. 添加测试用例

## 环境变量

```bash
# Flask环境
FLASK_ENV=development
DEBUG=True

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=24

# CORS配置
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# AI功能（可选）
DEEPSEEK_API_KEY=your-api-key
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 使用其他端口
   export PORT=5001
   python run.py
   ```

2. **依赖安装失败**
   ```bash
   # 创建虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

3. **CORS错误**
   - 确保前端地址在CORS_ORIGINS配置中
   - 检查请求头是否包含正确的Authorization

## 更新日志

### v1.0.0 (2024-01-20)
- ✅ 完整的Flask后端架构
- ✅ 用户认证和权限管理
- ✅ 场地和物资管理API
- ✅ 申请和审批流程
- ✅ 统计分析功能
- ✅ Mock数据和测试脚本
- ✅ 完整的API文档

## 许可证

MIT License

---

**开发团队**: 校级活动场地与物资管理系统开发组
**技术支持**: 基于Flask框架的企业级应用开发