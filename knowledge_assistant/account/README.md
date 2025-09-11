# Account 模块

## 简介

Account模块负责用户账户管理，包括用户注册、登录、认证以及个人资料管理等功能。该模块是系统的基础组件，提供了用户身份验证和授权服务。

## 目录结构

```
account/
├── migrations/       # 数据库迁移文件
├── models/           # 模型文件目录
│   ├── __init__.py
│   ├── profile_models.py  # 用户个人资料模型
│   └── user_models.py     # 用户模型
├── __init__.py       # 包初始化文件
├── admin.py          # Django管理后台配置
├── apps.py           # 应用程序配置
├── models.py         # 模型导入文件
├── serializers.py    # REST API序列化器
├── tests.py          # 测试代码
├── urls.py           # URL路由配置
└── views.py          # 视图处理函数
```

## 主要功能

- **用户管理**：注册、登录、登出、密码重置等
- **个人资料管理**：用户信息编辑与更新
- **认证与授权**：基于Token的身份验证机制
- **权限控制**：不同级别用户的权限管理

## API端点

- `/api/account/register/` - 用户注册
- `/api/account/login/` - 用户登录
- `/api/account/logout/` - 用户登出
- `/api/account/profile/` - 获取/更新用户资料
- `/api/account/change-password/` - 修改密码

## 使用示例

### 用户注册
```http
POST /api/account/register/
Content-Type: application/json

{
  "username": "example_user",
  "email": "user@example.com",
  "password": "secure_password",
  "password_confirm": "secure_password"
}
```

### 用户登录
```http
POST /api/account/login/
Content-Type: application/json

{
  "username": "example_user",
  "password": "secure_password"
}
```

## 数据模型

### User模型
扩展自Django的内置User模型，添加了额外的用户相关字段。

### Profile模型
与User模型关联，存储用户的额外信息，如头像、个人简介等。

## 依赖项

- Django认证系统
- Django REST Framework认证类
- Token认证机制
