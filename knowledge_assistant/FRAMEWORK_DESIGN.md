# Chat应用框架设计

## 项目概述
创建一个chat应用，用于保存用户与AI的对话记录，并能够在需要时提供聊天记录作为上下文发送给AI。

## 目录结构
```
chat/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── session_models.py
│   └── message_models.py
├── serializers.py
├── views.py
├── urls.py
├── services/
│   ├── __init__.py
│   ├── chat_service.py
│   ├── message_service.py
│   └── ai_service.py
└── tests.py
```

## 数据模型设计

### 1. ChatSession模型 (session_models.py)
```python
from django.db import models
import uuid

class ChatSession(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=36)
    title = models.CharField(max_length=200, default="新对话")
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    # 用户要求：增加chat_count表示对话总条数
    chat_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title
```

### 2. ChatMessage模型 (message_models.py)
```python
from django.db import models
import uuid

class ChatMessage(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=36)
    sender = models.CharField(max_length=20, choices=[('user', '用户'), ('ai', 'AI')])
    # 用户要求：不直接存储content，而是存储chunk_count
    chunk_count = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    # 用户要求：增加chat_number表示是对话中的第几条消息
    chat_number = models.IntegerField()
    # 用于存储消息的元数据
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.sender} - 第{self.chat_number}条消息"
```

### 3. 模型初始化文件 (__init__.py)
```python
from .session_models import ChatSession
from .message_models import ChatMessage

__all__ = ['ChatSession', 'ChatMessage']
```

## 序列化器设计 (serializers.py)
```python
from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'user_id', 'title', 'create_at', 'update_at', 'is_active', 'chat_count']
        read_only_fields = ['id', 'create_at', 'update_at', 'chat_count']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session_id', 'sender', 'chunk_count', 'create_at', 'chat_number', 'metadata']
        read_only_fields = ['id', 'create_at', 'chat_number']

class ChatMessageCreateSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=36)
    sender = serializers.ChoiceField(choices=[('user', '用户'), ('ai', 'AI')])
    content = serializers.CharField(allow_blank=False)
    metadata = serializers.JSONField(required=False, allow_null=True)

class ChatContextSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=36)
    num_messages = serializers.IntegerField(default=5, min_value=1, max_value=50)
```

## 服务层设计

### 1. 聊天服务 (chat_service.py)
```python
from ..models import ChatSession
import uuid

class ChatService:
    @staticmethod
    def create_chat_session(user_id, title="新对话"):
        """创建新的聊天会话"""
        session = ChatSession.objects.create(
            user_id=user_id,
            title=title
        )
        return session
    
    @staticmethod
    def get_chat_session(session_id):
        """获取聊天会话"""
        try:
            return ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return None
    
    @staticmethod
    def list_chat_sessions(user_id):
        """列出用户的所有聊天会话"""
        return ChatSession.objects.filter(user_id=user_id).order_by('-update_at')
    
    @staticmethod
    def update_chat_session(session_id, title=None, is_active=None):
        """更新聊天会话"""
        session = ChatService.get_chat_session(session_id)
        if not session:
            return None
        
        if title is not None:
            session.title = title
        if is_active is not None:
            session.is_active = is_active
        
        session.save()
        return session
    
    @staticmethod
    def delete_chat_session(session_id):
        """删除聊天会话"""
        session = ChatService.get_chat_session(session_id)
        if not session:
            return False
        
        session.delete()
        return True
    
    @staticmethod
    def update_chat_count(session_id):
        """更新会话的聊天消息数量"""
        from .message_service import MessageService
        
        session = ChatService.get_chat_session(session_id)
        if not session:
            return False
        
        session.chat_count = MessageService.get_message_count(session_id)
        session.save()
        return True
```

### 2. 消息服务 (message_service.py)
```python
from ..models import ChatMessage
from knowledge.models.markdown_models import Markdown
import uuid

class MessageService:
    @staticmethod
    def create_message(session_id, sender, content, metadata=None):
        """创建新的聊天消息"""
        # 计算chat_number
        max_number = ChatMessage.objects.filter(session_id=session_id).aggregate(
            max_number=models.Max('chat_number')
        )['max_number'] or 0
        chat_number = max_number + 1
        
        # 创建消息记录
        message = ChatMessage.objects.create(
            session_id=session_id,
            sender=sender,
            chat_number=chat_number,
            metadata=metadata
        )
        
        # 将内容切分成Markdown记录
        MessageService._split_content_into_markdowns(message.id, content, message.session_id)
        
        # 更新chunk_count
        message.chunk_count = Markdown.objects.filter(document_id=message.id).count()
        message.save()
        
        # 更新会话的chat_count
        from .chat_service import ChatService
        ChatService.update_chat_count(session_id)
        
        return message
    
    @staticmethod
    def _split_content_into_markdowns(message_id, content, session_id):
        """将聊天内容切分成多个Markdown记录"""
        # 首先删除该消息已有的Markdown记录
        Markdown.objects.filter(document_id=message_id).delete()
        
        # 使用300字符作为固定分段大小
        chunk_size = 300
        chunks = []
        current_chunk = ""
        
        # 简单的分段逻辑，可以根据需要优化
        words = content.split()
        for word in words:
            if len(current_chunk) + len(word) + 1 > chunk_size:  # +1 是为了空格
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 创建Markdown记录
        markdowns = []
        for index, chunk in enumerate(chunks, start=1):
            # 用户要求：聊天记录的markdown的title都是-1
            markdown = Markdown(
                title="-1",  # 表示这是聊天记录
                content=chunk,
                vector_id=str(uuid.uuid4()),  # 为聊天记录生成新的向量ID
                number=index,
                word_count=len(chunk),
                document_id=message_id,  # 使用ChatMessage的ID作为document_id
                creater_id=session_id  # 使用session_id作为creater_id
            )
            markdowns.append(markdown)
        
        # 批量创建Markdown记录
        Markdown.objects.bulk_create(markdowns)
    
    @staticmethod
    def get_message(message_id):
        """获取聊天消息"""
        try:
            return ChatMessage.objects.get(id=message_id)
        except ChatMessage.DoesNotExist:
            return None
    
    @staticmethod
    def get_message_content(message_id):
        """获取聊天消息的完整内容"""
        # 查询所有相关的Markdown记录并按number排序
        markdowns = Markdown.objects.filter(document_id=message_id).order_by('number')
        
        # 拼接内容
        full_content = ""
        for markdown in markdowns:
            full_content += markdown.content
        
        return full_content
    
    @staticmethod
    def list_messages(session_id):
        """列出会话中的所有消息"""
        return ChatMessage.objects.filter(session_id=session_id).order_by('chat_number')
    
    @staticmethod
    def get_message_count(session_id):
        """获取会话中的消息数量"""
        return ChatMessage.objects.filter(session_id=session_id).count()
    
    @staticmethod
    def delete_message(message_id):
        """删除聊天消息"""
        message = MessageService.get_message(message_id)
        if not message:
            return False
        
        # 删除相关的Markdown记录
        Markdown.objects.filter(document_id=message_id).delete()
        
        # 删除消息记录
        session_id = message.session_id
        message.delete()
        
        # 更新会话的chat_count
        from .chat_service import ChatService
        ChatService.update_chat_count(session_id)
        
        return True
    
    @staticmethod
    def get_chat_context(session_id, num_messages=5):
        """获取聊天上下文"""
        # 查询最近的num_messages条消息
        messages = ChatMessage.objects.filter(session_id=session_id).order_by('-create_at')[:num_messages]
        
        # 按时间顺序重新排序
        messages = sorted(messages, key=lambda x: x.create_at)
        
        # 构建上下文
        context = ""
        for message in messages:
            sender = "用户" if message.sender == 'user' else "AI"
            content = MessageService.get_message_content(message.id)
            context += f"{sender}：{content}\n"
        
        return context
```

### 3. AI服务 (ai_service.py)
```python
# 这里实现与AI交互的逻辑
# 注意：实际实现时需要根据项目使用的AI API进行调整

class AIService:
    @staticmethod
    def generate_response(prompt, context=""):
        """生成AI回复"""
        # 这里是示例代码，实际实现时需要调用真实的AI API
        # response = some_ai_api.generate(prompt, context)
        
        # 示例响应
        response = f"这是AI对'{prompt}'的回复。上下文：{context}"
        return response
    
    @staticmethod
    def process_chat_message(user_message, session_id=None, context=None):
        """处理聊天消息并生成AI回复"""
        # 如果没有提供上下文，从会话中获取
        if not context and session_id:
            from .message_service import MessageService
            context = MessageService.get_chat_context(session_id)
        
        # 生成AI回复
        ai_response = AIService.generate_response(user_message, context)
        
        return ai_response
```

### 4. 服务层初始化文件 (__init__.py)
```python
from .chat_service import ChatService
from .message_service import MessageService
from .ai_service import AIService

__all__ = ['ChatService', 'MessageService', 'AIService']
```

## API视图设计 (views.py)
```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
    ChatContextSerializer
)
from .services import ChatService, MessageService, AIService

class ChatSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id=None):
        """获取单个会话或会话列表"""
        if session_id:
            # 获取单个会话
            session = ChatService.get_chat_session(session_id)
            if not session or session.user_id != request.user.id:
                return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ChatSessionSerializer(session)
            return Response(serializer.data)
        else:
            # 获取会话列表
            sessions = ChatService.list_chat_sessions(request.user.id)
            serializer = ChatSessionSerializer(sessions, many=True)
            return Response(serializer.data)
    
    def post(self, request):
        """创建新会话"""
        title = request.data.get('title', '新对话')
        session = ChatService.create_chat_session(request.user.id, title)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, session_id):
        """更新会话"""
        session = ChatService.get_chat_session(session_id)
        if not session or session.user_id != request.user.id:
            return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
        
        title = request.data.get('title')
        is_active = request.data.get('is_active')
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        
        session = ChatService.update_chat_session(session_id, title, is_active)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)
    
    def delete(self, request, session_id):
        """删除会话"""
        session = ChatService.get_chat_session(session_id)
        if not session or session.user_id != request.user.id:
            return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
        
        ChatService.delete_chat_session(session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, message_id=None, session_id=None):
        """获取单个消息或消息列表"""
        if message_id:
            # 获取单个消息
            message = MessageService.get_message(message_id)
            if not message:
                return Response({'error': '消息不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            # 验证用户权限
            session = ChatService.get_chat_session(message.session_id)
            if not session or session.user_id != request.user.id:
                return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)
            
            # 获取完整内容
            content = MessageService.get_message_content(message.id)
            message_data = ChatMessageSerializer(message).data
            message_data['content'] = content
            
            return Response(message_data)
        elif session_id:
            # 获取会话中的消息列表
            session = ChatService.get_chat_session(session_id)
            if not session or session.user_id != request.user.id:
                return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
            
            messages = MessageService.list_messages(session_id)
            result = []
            for message in messages:
                message_data = ChatMessageSerializer(message).data
                message_data['content'] = MessageService.get_message_content(message.id)
                result.append(message_data)
            
            return Response(result)
        else:
            return Response({'error': '缺少参数'}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """创建新消息"""
        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        session_id = serializer.validated_data['session_id']
        sender = serializer.validated_data['sender']
        content = serializer.validated_data['content']
        metadata = serializer.validated_data.get('metadata')
        
        # 验证会话权限
        session = ChatService.get_chat_session(session_id)
        if not session or session.user_id != request.user.id:
            return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
        
        # 创建消息
        message = MessageService.create_message(session_id, sender, content, metadata)
        
        # 获取完整内容
        message_data = ChatMessageSerializer(message).data
        message_data['content'] = content
        
        return Response(message_data, status=status.HTTP_201_CREATED)
    
    def delete(self, request, message_id):
        """删除消息"""
        message = MessageService.get_message(message_id)
        if not message:
            return Response({'error': '消息不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 验证用户权限
        session = ChatService.get_chat_session(message.session_id)
        if not session or session.user_id != request.user.id:
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)
        
        MessageService.delete_message(message_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

class ChatContextView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取聊天上下文"""
        serializer = ChatContextSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        session_id = serializer.validated_data['session_id']
        num_messages = serializer.validated_data['num_messages']
        
        # 验证会话权限
        session = ChatService.get_chat_session(session_id)
        if not session or session.user_id != request.user.id:
            return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取上下文
        context = MessageService.get_chat_context(session_id, num_messages)
        
        return Response({'context': context})

class AIChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """发送消息给AI并获取回复"""
        session_id = request.data.get('session_id')
        message = request.data.get('message')
        
        if not message:
            return Response({'error': '消息内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 如果没有会话ID，创建新会话
        if not session_id:
            session = ChatService.create_chat_session(request.user.id, f"与AI的对话 - {message[:20]}...")
            session_id = session.id
        else:
            # 验证会话权限
            session = ChatService.get_chat_session(session_id)
            if not session or session.user_id != request.user.id:
                return Response({'error': '会话不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
        
        # 保存用户消息
        user_message = MessageService.create_message(session_id, 'user', message)
        
        # 获取上下文并生成AI回复
        context = MessageService.get_chat_context(session_id)
        ai_response = AIService.process_chat_message(message, session_id, context)
        
        # 保存AI回复
        ai_message = MessageService.create_message(session_id, 'ai', ai_response)
        
        return Response({
            'session_id': session_id,
            'user_message_id': user_message.id,
            'ai_message_id': ai_message.id,
            'ai_response': ai_response
        }, status=status.HTTP_200_OK)
```

## URLs配置 (urls.py)
```python
from django.urls import path
from .views import (
    ChatSessionView,
    ChatMessageView,
    ChatContextView,
    AIChatView
)

urlpatterns = [
    # 会话相关接口
    path('sessions/', ChatSessionView.as_view(), name='chat-sessions'),
    path('sessions/<str:session_id>/', ChatSessionView.as_view(), name='chat-session-detail'),
    
    # 消息相关接口
    path('messages/', ChatMessageView.as_view(), name='chat-messages'),
    path('messages/<str:message_id>/', ChatMessageView.as_view(), name='chat-message-detail'),
    path('sessions/<str:session_id>/messages/', ChatMessageView.as_view(), name='session-messages'),
    
    # 上下文相关接口
    path('context/', ChatContextView.as_view(), name='chat-context'),
    
    # AI聊天接口
    path('ai-chat/', AIChatView.as_view(), name='ai-chat'),
]
```

## 应用配置 (apps.py)
```python
from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
```

## 初始化文件 (__init__.py)
```python
default_app_config = 'chat.apps.ChatConfig'
```

## 部署和配置说明
1. 将chat应用添加到settings.py中的INSTALLED_APPS
2. 运行数据库迁移命令：`python manage.py makemigrations chat` 和 `python manage.py migrate`
3. 根据实际需求配置AI服务的API连接信息
4. 确保knowledge应用的Markdown模型已正确配置

## 扩展建议
1. 添加消息搜索功能
2. 实现消息的导入导出功能
3. 添加消息的标签和分类功能
4. 优化大文本的分段策略
5. 添加对多媒体消息的支持