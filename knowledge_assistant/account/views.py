from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .models.user_models import User
from .models.profile_models import Profile
from rest_framework.permissions import IsAuthenticated
from .serializers import UserUpdateSerializer
from knowledge.models.knowledge_base_models import KnowledgeBase
from .models.profile_models import Profile, Image  # 添加Image导入
import os
from .serializers import UserSerializer, UserUpdateSerializer, PasswordUpdateSerializer, UserDetailSerializer
from django.db import models  # 添加这行
from knowledge.models.document_models import Document
from knowledge.models.markdown_models import Markdown


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'status': 'success',
                'token': token.key,
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_200_OK)
        
        return Response({
            'status': 'error',
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(APIView):
   def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # 检查用户名是否已存在
            username = serializer.validated_data.get('username')
            if User.objects.filter(username=username).exists():
                return Response({
                    'status': 'error',
                    'message': {'username': '用户名已存在'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 完善用户创建流程
            user = serializer.save()
            # 创建用户资料
            profile = Profile.objects.create(user=user, avatar=None)
            # 创建知识库
            knowledge_base = KnowledgeBase.objects.create(
                owner_user_id=str(user.id),
                name=f"{user.username}'s Knowledge Base",
                description='Default knowledge base'
            )
            # 生成令牌
            token, _ = Token.objects.get_or_create(user=user)
            # 返回成功响应
            return Response({
                'status': 'success',
                'token': token.key,
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        
        # 处理序列化器验证失败情况
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('userid')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserUpdateSerializer(user, data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': '无效的请求数据1',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return Response({
                'status': 'error',
                'message': '用户资料不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 直接处理已验证的序列化器数据
        # 更新用户名
        if 'username' in serializer.validated_data:
            user.username = serializer.validated_data['username']
            user.save()

            # 更新头像
            if 'avatar' in serializer.validated_data:
                avatar_id = serializer.validated_data['avatar']
                try:
                    image = Image.objects.get(id=avatar_id)
                    profile.avatar = image
                except Image.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': '头像图片不存在'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # 更新个人简介
            if 'bio' in serializer.validated_data:
                profile.bio = serializer.validated_data['bio']

            profile.save()
            return Response({
                'status': 'success',
                'message': '用户信息更新成功',
                'data': {
                    'username': user.username,
                    'avatar': profile.avatar.id if profile.avatar else None,
                    'bio': profile.bio
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'error',
            'message': '无效的请求数据2',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserDeleteView(APIView):
    #authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 使用认证用户直接进行操作，无需传递user_id
        user = request.user
        
        try:
            # 获取用户关联的Profile
            profile = user.profile
            # 删除userid引用
            
            # 1. 删除所有关联的知识库及其内容
            # 查询该用户拥有或创建的所有知识库
            knowledge_bases = KnowledgeBase.objects.filter(owner_user_id=user.id)
            if knowledge_bases.exists():
                for kb in knowledge_bases:
                # 删除知识库下的所有文档
                 documents = Document.objects.filter(knowledge_base_id=kb.id)
                for doc in documents:
                    # 删除文档下的所有Markdown片段
                    Markdown.objects.filter(document_id=doc.id).delete()
                    doc.delete()
                kb.delete()

           

            # 3. 最后删除用户（会自动级联删除Profile）
            user.delete()

            return Response({
                'status': 'success',
                'message': '账户已成功注销，所有关联数据已清除'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Profile.DoesNotExist:
            return Response({
                'status': 'error',
                'message': '用户资料不存在'
            }, status=status.HTTP_404_NOT_FOUND)

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class PasswordUpdateView(APIView):
    #authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get('userid')
        if not user_id:
            return Response({
                'status': 'error', 
                'message': '用户ID不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 转换user_id为整数
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({
                'status': 'error', 
                'message': '用户ID必须为整数'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'status': 'error', 
                'message': '用户不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 获取请求中的密码信息
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # 验证密码是否提供
        if not old_password or not new_password:
            return Response({
                'status': 'error', 
                'message': '旧密码和新密码均不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证旧密码是否正确
        if not user.check_password(old_password):
            return Response({
                'status': 'error', 
                'message': '旧密码不正确'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证新密码
        serializer = PasswordUpdateSerializer(data={
            'old_password': old_password,
            'new_password': new_password,
            'confirm_password': new_password
        }, user=user)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': '新密码验证失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # 更新密码
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # 更新密码后使旧token失效并生成新token
        Token.objects.filter(user=user).delete()
        new_token = Token.objects.create(user=user)

        return Response({
                'status': 'success',
                'message': '密码更新成功',
                'new_token': new_token.key
        }, status=status.HTTP_200_OK)

        
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)