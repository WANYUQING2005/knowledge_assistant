from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from account.models.user_models import User
from .models.knowledge_base_models import KnowledgeBase
from .models.document_models import Document
import uuid

class KnowledgeAPITest(TestCase):
    def setUp(self):
        # 创建测试用户并获取认证令牌
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!'
        )
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }, format='json')
        self.token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 基础URL
        self.kb_url = reverse('knowledge-base-list')
        self.doc_url = reverse('document-list')

    def test_create_knowledge_base(self):
        """测试创建知识库"""
        data = {
            'name': '测试知识库',
            'description': '用于测试的知识库'
        }
        response = self.client.post(self.kb_url, data, format='json')

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(KnowledgeBase.objects.count(), 1)
        self.assertEqual(KnowledgeBase.objects.get().name, '测试知识库')
        self.assertEqual(KnowledgeBase.objects.get().owner_user_id, self.user.id)

    def test_upload_document_without_creater_id(self):
        """测试上传带1000个字符的文件（无creater_id）"""
        # 先创建知识库
        kb = KnowledgeBase.objects.create(
            name='测试知识库',
            owner_user_id=self.user.id,
            description='测试'
        )

        # 创建1000个'1'的文件
        file_content = '1' * 1000
        file = SimpleUploadedFile(
            '我的一天.docx',
            file_content.encode('utf-8'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

        # 上传文件（不提供creater_id）
        data = {
            'knowledge_base_id': kb.id,
            'file': file
        }
        response = self.client.post(self.doc_url, data, format='multipart')

        # 验证响应和数据库记录
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.get()
        self.assertEqual(doc.name, '我的一天.docx')
        # 验证creater_id自动设为知识库所有者ID
        self.assertEqual(doc.creater_id, kb.owner_user_id)

    def test_upload_empty_document_with_creater_id(self):
        """测试上传空文件（有creater_id=AAA）"""
        # 先创建知识库
        kb = KnowledgeBase.objects.create(
            name='测试知识库',
            owner_user_id=self.user.id,
            description='测试'
        )

        # 创建空文件
        file = SimpleUploadedFile(
            '我的两天.docx',
            b'',  # 空内容
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

        # 上传文件（提供creater_id）
        data = {
            'knowledge_base_id': kb.id,
            'file': file,
            'creater_id': 'AAA'
        }
        response = self.client.post(self.doc_url, data, format='multipart')

        # 验证响应和数据库记录
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.get()
        self.assertEqual(doc.name, '我的两天.docx')
        # 验证creater_id使用提供的值
        self.assertEqual(doc.creater_id, 'AAA')