# Account 模型目录

## 简介

此目录包含与用户账户和个人资料相关的数据模型定义。模型被分为用户模型和个人资料模型两个文件，以实现关注点分离和代码组织。

## 文件说明

### user_models.py

此文件定义了与用户账户相关的模型类：

- **CustomUser**：扩展Django默认User模型，添加额外字段如电话号码、注册日期等
- **UserSettings**：存储用户偏好设置，如通知选项、界面主题等
- **VerificationToken**：用于邮箱验证和密码重置的令牌模型

### profile_models.py

此文件定义了与用户个人资料相关的模型类：

- **Profile**：存储用户个人详细信息，如头像、个人简介、专业背景等
- **Education**：用户教育经历记录
- **WorkExperience**：用户工作经历记录

## 模型关系

- 一个`CustomUser`对应一个`Profile`（一对一关系）
- 一个`CustomUser`对应多个`Education`和`WorkExperience`记录（一对多关系）
- 一个`CustomUser`对应一个`UserSettings`（一对一关系）

## 使用示例

```python
# 获取用户资料
user = CustomUser.objects.get(username='example_user')
profile = user.profile
education = user.education_set.all()

# 更新用户设置
user.settings.enable_notifications = False
user.settings.save()
```

## 数据迁移

当修改模型后，需要创建和应用迁移：

```bash
python manage.py makemigrations account
python manage.py migrate account
```
