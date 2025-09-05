from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from account.models.user_models import User
from .models.session_models import ChatSession
from rest_framework.authtoken.models import Token
from account.models.profile_models import Profile
import uuid


class ChatSessionAPITest(TestCase):

    def setUp(self):
        # 初始化DRF APIClient
        self.client = APIClient()
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        # 创建关联的Profile
        self.profile = Profile.objects.create(
            user=self.user,
            avatar=None
        )
        # 获取认证令牌
        self.token = Token.objects.create(user=self.user)
        # 显式设置Authorization头
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        # 验证认证是否成功
        response = self.client.get(reverse('user-detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK, "初始认证失败，请检查令牌生成逻辑")
        
        # 设置测试用的URL
        self.create_session_url = reverse('create_chat_session')
        
        # 准备有效的测试数据（不再包含title字段）
        self.valid_data = {
            'user_id': str(self.user.id),
            'ai_type': 1,
            'kb_id': 0
        }

    def test_create_chat_session_success(self):
        """测试成功创建对话会话"""
        # 发送POST请求创建对话会话
        response = self.client.post(self.create_session_url, self.valid_data, format='json')
        print("Response data1 (without creater_id):", response.data)
        # 验证响应状态码和内容
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], '会话创建成功')
        
        # 验证响应数据中是否包含必要的字段
        self.assertIn('session_id', response.data['data'])
        self.assertEqual(response.data['data']['user_id'], str(self.user.id))
        self.assertEqual(response.data['data']['ai_type'], 1)
        self.assertEqual(response.data['data']['kb_id'], 0)
        self.assertIn('title', response.data['data'])  # 确保响应中仍然返回title字段
        self.assertEqual(response.data['data']['title'], '新对话')  # 验证默认标题
        
        # 验证数据库中是否创建了对应的记录
        self.assertEqual(ChatSession.objects.count(), 1)
        session = ChatSession.objects.get()
        self.assertEqual(session.user_id, str(self.user.id))
        self.assertEqual(session.ai_type, 1)
        self.assertEqual(session.kb_id, 0)
        self.assertEqual(session.title, '新对话')  # 验证默认标题
        self.assertEqual(session.chat_count, 0)  # 验证默认值

    def test_create_chat_session_missing_user_id(self):
        """测试缺少必填字段user_id的情况"""
        # 移除user_id字段
        invalid_data = self.valid_data.copy()
        del invalid_data['user_id']
        
        # 发送POST请求
        response = self.client.post(self.create_session_url, invalid_data, format='json')
        
        # 验证响应状态码和错误信息
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], '会话创建失败')
        self.assertIn('user_id', response.data['errors'])

    def test_create_chat_session_with_default_values(self):
        """测试使用默认值创建对话会话"""
        # 只提供必填字段user_id
        minimal_data = {
            'user_id': str(self.user.id)
        }
        
        # 发送POST请求
        response = self.client.post(self.create_session_url, minimal_data, format='json')
        
        # 验证响应状态码和内容
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['ai_type'], 1)  # 验证ai_type默认值
        self.assertEqual(response.data['data']['kb_id'], 0)  # 验证kb_id默认值
        self.assertEqual(response.data['data']['title'], '新对话')  # 验证默认标题
        
        # 验证数据库中是否创建了对应的记录
        session = ChatSession.objects.get()
        self.assertEqual(session.ai_type, 1)
        self.assertEqual(session.kb_id, 0)
        self.assertEqual(session.title, '新对话')  # 验证默认标题

    def test_create_chat_session_with_custom_ai_type(self):
        """测试使用自定义ai_type创建对话会话"""
        # 设置自定义的ai_type
        custom_data = self.valid_data.copy()
        custom_data['ai_type'] = 2
        
        # 发送POST请求
        response = self.client.post(self.create_session_url, custom_data, format='json')
        
        # 验证响应和数据库中的ai_type值
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['ai_type'], 2)
        
        session = ChatSession.objects.get()
        self.assertEqual(session.ai_type, 2)

    def test_create_chat_session_with_knowledge_base(self):
        """测试创建关联知识库的对话会话"""
        # 设置非零的kb_id
        kb_data = self.valid_data.copy()
        kb_data['kb_id'] = 123
        
        # 发送POST请求
        response = self.client.post(self.create_session_url, kb_data, format='json')
        
        # 验证响应和数据库中的kb_id值
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['kb_id'], 123)
        
        session = ChatSession.objects.get()
        self.assertEqual(session.kb_id, 123)

    def test_create_multiple_sessions(self):
        """测试创建多个对话会话"""
        # 创建第一个会话
        self.client.post(self.create_session_url, self.valid_data, format='json')
        
        # 创建第二个会话
        self.client.post(self.create_session_url, self.valid_data, format='json')
        
        # 验证数据库中是否有两个会话记录
        self.assertEqual(ChatSession.objects.count(), 2)

    # 移除了与title字段相关的测试用例，因为现在title由AI首次回答后生成