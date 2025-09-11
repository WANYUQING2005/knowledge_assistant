from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

import re
from django.core import validators

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # 验证邮箱
        if not email:
            raise ValueError('The Email field must be set')
        try:
            validators.validate_email(email)
        except validators.ValidationError:
            raise ValueError('The Email field must be a valid email address')
        email = self.normalize_email(email)

        # 验证用户名
        username = extra_fields.get('username')
        if not username:
            raise ValueError('The Username field must be set')
        if len(username) < 1 or len(username) > 150:
            raise ValueError('Username must be between 1 and 150 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        # 检查用户名是否已存在于数据库
        if self.model.objects.filter(username=username).exists():
            raise ValueError('Username already exists')

        user = self.model(email=email,** extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password,** extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=128)  # 存储的是哈希值，用户密码对开发者不透明
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email