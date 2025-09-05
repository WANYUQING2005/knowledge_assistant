from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models.session_models import ChatSession
from .serializers import ChatSessionSerializer

class CreateChatSessionView(APIView):
    
    def post(self, request):
        # 使用序列化器验证和处理请求数据
        serializer = ChatSessionSerializer(data=request.data)
        
        if serializer.is_valid():
            # 保存新的ChatSession实例
            chat_session = serializer.save()
            
            # 返回创建成功的响应，包含新创建的ChatSession的信息
            return Response({
                'status': 'success',
                'message': '会话创建成功',
                'data': {
                    'session_id': chat_session.id,
                    'user_id': chat_session.user_id,
                    'ai_type': chat_session.ai_type,
                    'kb_id': chat_session.kb_id,
                    'title': chat_session.title,
                    'chat_count': chat_session.chat_count,
                    'create_at': chat_session.create_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'update_at': chat_session.update_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=status.HTTP_201_CREATED)
        
        # 如果序列化器验证失败，返回错误信息
        return Response({
            'status': 'error',
            'message': '会话创建失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)