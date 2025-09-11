from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.db import DatabaseError, transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# 修改导入语句，从tags_search模块中导入TagBasedSearch类
try:
    from rag_demo.tags_search import TagBasedSearch
except ImportError:
    import os, sys
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(root_dir)
    try:
        from rag_demo.tags_search import TagBasedSearch
    except ImportError:
        sys.path.append(os.path.join(root_dir, 'rag_demo'))
        from tags_search import TagBasedSearch

# 导入rag_demo模块中的问答逻辑
import os, sys


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 修改导入语句，增加更健壮的导入机制
try:
    # 尝试导入rag_qa模块
    from rag_demo import rag_qa
except ImportError:
    # 如果导入失败，尝试通过不同路径导入
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(root_dir)
    try:
        import rag_qa
    except ImportError:
        sys.path.append(os.path.join(root_dir, 'rag_demo'))
        import rag_qa

# 常量定义
SENDER_USER = 'user'
SENDER_AI = 'ai'

class CreateChatSessionView(APIView):
    """创建新的对话会话"""
    def post(self, request):
        serializer = ChatSessionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                chat_session = serializer.save()  # 保存会话
                # 可选：初始化rag_demo对话历史
                rag_qa.HISTORY.clear()  # 清空全局历史记录
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
                        'update_at': chat_session.update_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }, status=status.HTTP_201_CREATED)
            except DatabaseError as e:
                return Response({'status': 'error', 'message': f'数据库错误: {e}'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'status': 'error', 'message': '参数校验失败', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

class ChatMessageView(APIView):
    """发送消息获取AI回复，支持知识库检索和流式输出"""
    def get(self, request):
        """以流式(SSE)方式返回AI回答"""
        session_id = request.query_params.get('session_id')
        user_id = request.query_params.get('user_id')
        question = request.query_params.get('question')  # 用户问题
        kb_id = request.query_params.get('kb_id', "0")
        if not session_id or not question:
            return Response({'status': 'error', 'message': '缺少 session_id 或 question 参数'},
                            status=status.HTTP_400_BAD_REQUEST)
        # 验证会话存在且未结束
        try:
            session = ChatSession.objects.get(id=session_id, is_active=True)
        except ChatSession.DoesNotExist:
            return Response({'status': 'error', 'message': '会话不存在或已结束'},
                            status=status.HTTP_404_NOT_FOUND)
        if user_id and session.user_id != user_id:
            return Response({'status': 'error', 'message': '用户ID与会话不匹配'},
                            status=status.HTTP_403_FORBIDDEN)

        # 构建rag_demo上下文：加载历史对话
        history_msgs = ChatMessage.objects.filter(session_id=session_id).order_by('chat_number')
        # 将历史消息配对转成 (用户, AI) 对 元组列表
        history_pairs = []
        msg_iter = iter(history_msgs)
        for msg in msg_iter:
            if msg.sender == SENDER_USER:
                try:
                    ai_msg = next(msg_iter)
                except StopIteration:
                    break
                if ai_msg.sender == SENDER_AI:
                    history_pairs.append((msg.content, ai_msg.content))
        # 将历史对话填充到 rag_demo 全局 HISTORY（保留最近N轮对话）
        rag_qa.HISTORY.clear()
        # 只保留最近N轮对话（N=HISTORY_MAX_TURNS）
        max_turns = int(os.getenv("CHAT_HISTORY_TURNS", "6"))
        for user_text, ai_text in history_pairs[-max_turns:]:
            rag_qa.HISTORY.append((user_text, ai_text))

        # 利用rag_demo执行检索增强问答
        kb_id_str = str(kb_id)  # rag_qa 接口kb_id期望字符串
        # 1. 加载向量索引
        vector_store = rag_qa._load_vector_store()
        # 2. 检索相关文档
        docs_scores = rag_qa._search_relevant_docs(vector_store, question, k=6, kb_id=kb_id_str)
        docs = [doc for doc, _ in docs_scores]
        context_text = rag_qa._format_docs_for_llm(docs)
        # 3. 构造对话提示（包含系统提示、知识库上下文和历史）
        llm = rag_qa._build_language_model()
        # 使用rag_demo预定义的提示模板，将问题、知识上下文和历史格式化为消息
        messages = rag_qa.PROMPT.format_messages(
            question=question, context=context_text, history=rag_qa._history_text()
        )
        # 4. 定义生成器，将LLM输出流式发送
        import json
        def stream_answer():
            # 流式返回模型的回答部分
            for chunk in llm.stream(messages):
                token = getattr(chunk, "content", None)
                if token:
                    # SSE协议：data: 开头的行作为一次消息
                    yield f"data: {token}\n\n".encode('utf-8')
            # 循环结束，表示回答完整
            # 格式化知识来源信息为JSON字符串
            sources = rag_qa._format_sources(docs_scores)
            sources_json = json.dumps(sources, ensure_ascii=False)
            # 发送终止标志和来源数据
            yield f"event: done\ndata: {sources_json}\n\n".encode('utf-8')
            # 保存此次问答到数据库（最后执行）
            ChatMessage.objects.create(
                session_id=session_id, user_id=user_id, kb_id=kb_id,
                sender=SENDER_USER, content=question,
                create_at=timezone.now(), chat_number=session.chat_count+1, metadata={}
            )
            ChatMessage.objects.create(
                session_id=session_id, user_id=user_id, kb_id=kb_id,
                sender=SENDER_AI, content="".join([tok.get("content", "") for tok in llm.stream(messages)]),
                create_at=timezone.now(), chat_number=session.chat_count+2,
                metadata={'sources': sources}
            )
            session.chat_count += 1
            session.save()
        # 返回StreamingHttpResponse，设置content_type为text/event-stream以支持SSE
        return StreamingHttpResponse(stream_answer(), content_type='text/event-stream')

    def post(self, request):
        """以一次性JSON形式返回AI回答"""
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': '参数校验失败', 'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            session_id = serializer.validated_data['session_id']
            user_id = serializer.validated_data['user_id']
            kb_id = serializer.validated_data.get('kb_id', 0)
            question = serializer.validated_data['content']
            # 确认会话存在
            session = ChatSession.objects.get(id=session_id, is_active=True)
            if session.user_id != user_id:
                return Response({'status': 'error', 'message': '用户ID与会话不匹配'},
                                status=status.HTTP_403_FORBIDDEN)
            # 与 GET 相同的流程（检索 + LLM问答），但直接获取完整结果
            rag_qa.HISTORY.clear()
            history_msgs = ChatMessage.objects.filter(session_id=session_id).order_by('chat_number')
            history_pairs = []
            # 配对历史消息
            for i in range(0, len(history_msgs), 2):
                if i+1 < len(history_msgs):
                    u_msg, ai_msg = history_msgs[i], history_msgs[i+1]
                    if u_msg.sender == SENDER_USER and ai_msg.sender == SENDER_AI:
                        history_pairs.append((u_msg.content, ai_msg.content))
            for user_text, ai_text in history_pairs[-int(os.getenv("CHAT_HISTORY_TURNS", "6")):]:
                rag_qa.HISTORY.append((user_text, ai_text))
            kb_id_str = str(kb_id)
            vector_store = rag_qa._load_vector_store()
            docs_scores = rag_qa._search_relevant_docs(vector_store, question, k=6, kb_id=kb_id_str)
            docs = [doc for doc, _ in docs_scores]
            context_text = rag_qa._format_docs_for_llm(docs)
            llm = rag_qa._build_language_model()
            messages = rag_qa.PROMPT.format_messages(
                question=question, context=context_text, history=rag_qa._history_text()
            )
            # 调用LLM一次性获得完整回复
            resp = llm.invoke(messages)
            answer_text = resp.content if hasattr(resp, "content") else str(resp)
            sources = rag_qa._format_sources(docs_scores)
            # 保存消息到数据库
            ChatMessage.objects.create(
                session_id=session_id, user_id=user_id, kb_id=kb_id,
                sender=SENDER_USER, content=question,
                create_at=timezone.now(), chat_number=session.chat_count + 1, metadata={}
            )
            ChatMessage.objects.create(
                session_id=session_id, user_id=user_id, kb_id=kb_id,
                sender=SENDER_AI, content=answer_text,
                create_at=timezone.now(), chat_number=session.chat_count + 2,
                metadata={'sources': sources}
            )
            session.chat_count += 1
            session.save()
            # 返回JSON响应
            return Response({
                'status': 'success',
                'answer': answer_text,
                'sources': sources    # 包含知识来源信息
            }, status=status.HTTP_200_OK)
        except ChatSession.DoesNotExist:
            return Response({'status': 'error', 'message': '会话不存在或已关闭'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'status': 'error', 'message': f'处理请求出错: {e}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EndChatSessionView(APIView):
    """结束聊天会话"""
    def post(self, request):
        session_id = request.data.get('session_id')
        user_id = request.data.get('user_id')
        if not session_id or not user_id:
            return Response({'status': 'error', 'message': 'session_id和user_id为必填项'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response({'status': 'error', 'message': '会话不存在'},
                            status=status.HTTP_404_NOT_FOUND)
        if session.user_id != user_id:
            return Response({'status': 'error', 'message': '用户ID与会话不匹配'},
                            status=status.HTTP_403_FORBIDDEN)
        if not session.is_active:
            return Response({'status': 'success', 'message': '会话已结束'}, status=status.HTTP_200_OK)
        # 结束会话事务
        with transaction.atomic():
            session.is_active = False
            session.save()
            # 可选：清理rag_demo全局历史
            rag_qa.HISTORY.clear()
        # 返回统计信息或确认消息
        message_count = ChatMessage.objects.filter(session_id=session_id).count()
        return Response({
            'status': 'success',
            'message': '会话已成功结束',
            'data': {
                'message_count': message_count,
                'user_message_count': ChatMessage.objects.filter(session_id=session_id, sender=SENDER_USER).count(),
                'ai_message_count': ChatMessage.objects.filter(session_id=session_id, sender=SENDER_AI).count()
            }
        }, status=status.HTTP_200_OK)



