from django.db import models
from .user_models import User
import uuid  # 新增：用于生成唯一profileid

# 新增：图片存储模型
class Image(models.Model):
    image = models.ImageField(upload_to='avatars/')  # 存储图片文件
    uploaded_at = models.DateTimeField(auto_now_add=True)  # 自动记录上传时间

    def __str__(self):
        return f'Image {self.id}'

# 新增：生成UUID的命名函数
def generate_profile_id():
    return str(uuid.uuid4())

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # 保留现有bio字段（已符合text类型要求）
    bio = models.TextField(blank=True, null=True,default=None)
    # 修改：将直接存储图片改为关联Image模型的ID
    avatar = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=0

    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} Profile'