from django.urls import path
from .views import CreateKnowledgeBaseView
from .views import CreateKnowledgeBaseView, DocumentUploadView
from .views import DeleteKnowledgeBaseView, DeleteDocumentView
from .views import KnowledgeBaseListView
from .views import MarkdownDetailView, MarkdownByDocumentView

urlpatterns = [
    path('create/', CreateKnowledgeBaseView.as_view(), name='create-knowledge-base'),
    path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('delete/', DeleteKnowledgeBaseView.as_view(), name='delete-knowledge-base'),
    path('documents/delete/', DeleteDocumentView.as_view(), name='delete-document'),
    path('list/', KnowledgeBaseListView.as_view(), name='knowledge-base-list'),  # 新增查询路由
    path('markdown/detail/', MarkdownDetailView.as_view(), name='markdown-detail'),  # 新增路由
    path('markdown/detail-by-document/', MarkdownByDocumentView.as_view(), name='markdown-by-document'),
]