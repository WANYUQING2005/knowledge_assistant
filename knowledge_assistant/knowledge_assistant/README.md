# Knowledge Assistant 核心配置目录

## 简介

此目录包含Django项目的核心配置文件，负责整个系统的设置、URL路由和WSGI/ASGI接口等基础功能。这是整个知识助手系统的核心配置中心。

## 目录结构

```
knowledge_assistant/
├── __init__.py      # 包初始化文件
├── asgi.py          # ASGI应用配置（支持异步Web服务器）
├── settings.py      # Django项目配置
├── urls.py          # URL路由配置
├── wsgi.py          # WSGI应用配置（支持传统Web服务器）
├── vector_store.py  # 向量存储实现
└── sql/             # 数据库相关SQL脚本
```

## 主要功能

- **项目配置**：在settings.py中定义项目的各种配置参数
- **URL路由**：在urls.py中管理整个项目的URL路由规则
- **WSGI/ASGI**：提供与Web服务器接口的入口点
- **向量存储**：实现向量数据库的访问和操作接口

## 核心配置详情

### settings.py

包含项目的核心配置：
- 已安装的应用
- 中间件设置
- 数据库配置
- 静态文件和媒体文件路径
- 认证和权限设置
- 国际化和本地化设置
- REST框架配置

### urls.py

定义项目的URL路由规则，包括：
- 各应用的URL命名空间
- API端点路由
- 静态文件和媒体文件的服务路由

### vector_store.py

提供向量数据库的抽象层：
- 向量存储和检索接口
- 索引创建和管理功能
- 向量相似度搜索实现

## 使用示例

### 添加新的应用到项目
在`settings.py`中的`INSTALLED_APPS`列表中添加新应用：

```python
INSTALLED_APPS = [
    # ...现有应用...
    'my_new_app',
]
```

### 添加新的URL路由
在`urls.py`中添加新的URL路由：

```python
urlpatterns = [
    # ...现有路由...
    path('new-feature/', include('my_new_app.urls')),
]
```

## 项目配置调整

在开发和生产环境之间切换可能需要不同的设置。建议使用环境变量或单独的设置文件来管理不同环境的配置。

例如，可以创建`settings_dev.py`和`settings_prod.py`，然后通过环境变量`DJANGO_SETTINGS_MODULE`来选择使用哪个设置文件。
