from rest_framework import serializers
from django.core.validators import MinLengthValidator
import re
from .models.user_models import User

def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True, 'validators': [MinLengthValidator(8)]}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
class UserUpdateSerializer(serializers.Serializer):
    userid = serializers.CharField(required=True)
    username = serializers.CharField(required=False, min_length=1, max_length=150)
    avatar = serializers.IntegerField(required=False)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_username(self, value):
        # 验证用户名格式
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError('用户名只能包含字母、数字和下划线')
        # 检查用户名是否已存在
        user_id = self.initial_data.get('userid')
        if User.objects.filter(username=value).exclude(id=user_id).exists():
            raise serializers.ValidationError('用户名已存在')
        return value
class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, help_text="旧密码")
    new_password = serializers.CharField(
    required=True, 
    validators=[MinLengthValidator(8)],
    help_text="新密码，至少8个字符"
)
    confirm_password = serializers.CharField(required=True, help_text="确认新密码")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise serializers.ValidationError("原密码不正确")
        return value

    def validate_new_password(self, value):
        # 密码复杂度验证：至少包含一个大写字母、一个小写字母、一个数字和一个特殊字符
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&*_])[A-Za-z\d@#$%^&*_]{8,}$', value):
            raise serializers.ValidationError(
                "密码必须至少包含一个大写字母、一个小写字母、一个数字和一个特殊字符(@#$%^&*_)"
            )
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        return data
class UserDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    bio = serializers.CharField(source='profile.bio', allow_null=True)
    avatar_url = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='date_joined')
    def get_avatar_url(self, obj):
        if obj.profile.avatar:
            return obj.profile.avatar.image.url
        return None