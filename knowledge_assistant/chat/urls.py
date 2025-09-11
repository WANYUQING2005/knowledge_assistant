from django.urls import path
from .views import CreateChatSessionView, ChatMessageView, EndChatSessionView

urlpatterns = [
    path('sessions/create/', CreateChatSessionView.as_view(), name='create_chat_session'),
    path('messages/send/', ChatMessageView.as_view(), name='send_message'),
    path('sessions/end/', EndChatSessionView.as_view(), name='end_chat_session'),

]
