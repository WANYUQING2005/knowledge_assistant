import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../rag_demo')))
import rag_qa
from chat.models.message_models import ChatMessage
from chat.models.session_models import ChatSession
from django.utils import timezone

# 为rag_qa模块添加ask函数，兼容现有调用方式
def add_ask_function():
    """为rag_qa模块动态添加ask函数，兼容现有调用方式"""
    if not hasattr(rag_qa, 'ask'):
        def ask(question, kb_id=0, history_list=None):
            # 配置rag_qa的历史记录
            if history_list:
                # 清空现有历史
                rag_qa.HISTORY.clear()
                # 添加历史记录（限制最大条数）
                max_hist = min(len(history_list), rag_qa.HISTORY_MAX_TURNS)
                for i in range(max_hist):
                    if i < len(history_list):
                        sender, content = history_list[i]
                        if sender == 'user' and i+1 < len(history_list) and history_list[i+1][0] == 'ai':
                            rag_qa.HISTORY.append((content, history_list[i+1][1]))

            # 调用实际的问答函数
            result = rag_qa.rag_answer_with_sources(question, kb_id=str(kb_id))
            return result["answer"], result["sources"]

        # 将函数动态添加到rag_qa模块
        setattr(rag_qa, 'ask', ask)

# 确保添加ask函数
add_ask_function()

class RagChatService:
    @staticmethod
    def ask(user_id, session_id, question, kb_id=0):
        # 设置正确的工作目录以访问索引文件
        original_dir = os.getcwd()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        os.chdir(project_root)  # 切换到项目根目录

        try:
            # 获取历史消息
            history = ChatMessage.objects.filter(session_id=session_id).order_by('chat_number')
            history_list = [(msg.sender, msg.content) for msg in history]

            # 调用 rag_qa 问答
            answer, context = rag_qa.ask(question, kb_id, history_list)

            # 保存用户消息
            user_msg = ChatMessage.objects.create(
                session_id=session_id,
                user_id=user_id,
                kb_id=kb_id,
                sender='user',
                content=question,
                create_at=timezone.now(),
                chat_number=history.count() + 1,
                metadata={}
            )
            # 保存AI消息
            ai_msg = ChatMessage.objects.create(
                session_id=session_id,
                user_id=user_id,
                kb_id=kb_id,
                sender='ai',
                content=answer,
                create_at=timezone.now(),
                chat_number=history.count() + 2,
                metadata={'context': context}
            )
            return answer, context
        finally:
            # 恢复原始工作目录
            os.chdir(original_dir)
