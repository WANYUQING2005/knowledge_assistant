from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models.knowledge_base_models import KnowledgeBase
from .serializers import KnowledgeBaseSerializer
from django.conf import settings
from .models.document_models import Document
from .serializers import DocumentSerializer
from django.db import transaction
from .models.markdown_models import Markdown
from rest_framework.permissions import IsAuthenticated
from .models.knowledge_base_models import KnowledgeBase
from .serializers import KnowledgeBaseSerializer
from .serializers import DocumentDetailSerializer
from .serializers import MarkdownSerializer
import os
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
class CreateKnowledgeBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = KnowledgeBaseSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            # 设置所有者ID
            serializer.save(owner_user_id=str(request.user.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 支持文件上传的解析器

    def post(self, request):
        # 1. 验证必要参数
        knowledge_base_id = request.data.get('knowledge_base_id')
        file = request.FILES.get('file')
        if not all([knowledge_base_id, file]):
            return Response(
                {'error': 'knowledge_base_id和file为必填项'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 验证知识库所有权
        try:
            knowledge_base = KnowledgeBase.objects.get(
                id=knowledge_base_id,
                owner_user_id=str(request.user.id)
            )
        except KnowledgeBase.DoesNotExist:
            return Response(
                {'error': '知识库不存在或无访问权限'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. 处理文件存储
        # 创建存储目录（确保Windows路径正确）
        storage_dir = os.path.join(settings.MEDIA_ROOT, 'documents', str(request.user.id))
        os.makedirs(storage_dir, exist_ok=True)

        # 生成唯一文件名
        file_ext = os.path.splitext(file.name)[1]
        file_type = file_ext
 
        # 校验文件类型是否支持
        if file_type not in settings.SUPPORTED_FILE_TYPES:
            return Response(
                {'error': '不支持该类型文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        storage_path = os.path.join(storage_dir, unique_filename)

        # 保存文件到本地系统（可替换为文档数据库API）
        with open(storage_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # 4. 构建并保存Document对象
        document = Document(
            knowledge_base_id=knowledge_base_id,
            title=request.data.get('title', os.path.splitext(file.name)[0]),  # 从文件名提取标题
            file_type=file.content_type.split('/')[-1],  # 提取MIME类型后缀
            storage_uri=storage_path.replace('\\', '/'),  # 统一使用Unix风格路径
            chunk_count=0  # 初始化为0，后续可通过异步任务更新
        )
        document.save()

        # 5. 返回创建结果
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
class DeleteKnowledgeBaseView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        knowledge_base_id = request.data.get('knowledge_base_id')
        if not knowledge_base_id:
            return Response(
                {'error': 'knowledge_base_id为必填项'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证知识库所有权
        try:
            knowledge_base = KnowledgeBase.objects.get(
                id=knowledge_base_id,
                owner_user_id=str(request.user.id)
            )
        except KnowledgeBase.DoesNotExist:
            return Response(
                {'error': '知识库不存在或无访问权限'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # 级联删除关联文档及Markdown
        documents = Document.objects.filter(knowledge_base_id=knowledge_base_id)
        for doc in documents:
            Markdown.objects.filter(document_id=doc.id).delete()
            doc.delete()

        # 删除知识库
        knowledge_base.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        document_id = request.data.get('document_id')
        if not document_id:
            return Response(
                {'error': 'document_id为必填项'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证文档所有权
        try:
            document = Document.objects.get(id=document_id)
            # 验证文档所属知识库的所有权
            KnowledgeBase.objects.get(
                id=document.knowledge_base_id,
                owner_user_id=str(request.user.id)
            )
        except (Document.DoesNotExist, KnowledgeBase.DoesNotExist):
            return Response(
                {'error': '文档不存在或无访问权限'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # 级联删除Markdown
        Markdown.objects.filter(document_id=document_id).delete()
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
class KnowledgeBaseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取请求中的userid参数
        user_id = request.query_params.get('userid')
        if not user_id:
            return Response(
                {'error': 'userid为必填参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 查询用户所有知识库
        knowledge_bases = KnowledgeBase.objects.filter(owner_user_id=user_id)
        serializer = KnowledgeBaseSerializer(knowledge_bases, many=True)

        return Response(serializer.data)
class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        document_id = request.query_params.get('documentid')
        if not document_id:
            return Response(
                {'error': 'documentid为必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 获取文档信息
            document = Document.objects.get(id=document_id)
            # 序列化返回文档详情及正文
            serializer = DocumentDetailSerializer(document)
            return Response(serializer.data)

        except (Document.DoesNotExist, KnowledgeBase.DoesNotExist):
            return Response(
                {'error': '文档不存在或已被删除'},
                status=status.HTTP_404_NOT_FOUND
            )
class MarkdownDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        markdown_id = request.query_params.get('markdownid')
        if not markdown_id:
            return Response(
                {'error': 'markdownid为必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            markdown = Markdown.objects.get(id=markdown_id)
            serializer = MarkdownSerializer(markdown)
            return Response(serializer.data)

        except (Markdown.DoesNotExist, Document.DoesNotExist, KnowledgeBase.DoesNotExist):
            return Response(
                {'error': 'markdown不存在或已被删除'},
                status=status.HTTP_404_NOT_FOUND
            )

class MarkdownByDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        document_id = request.query_params.get('documentid')
        number = request.query_params.get('number')

        if not all([document_id, number]):
            return Response(
                {'error': 'documentid和number为必填参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 验证number为整数
            number = int(number)
            # 查询markdown
            markdown = Markdown.objects.get(document_id=document_id, number=number)

            serializer = MarkdownSerializer(markdown)
            return Response(serializer.data)

        except ValueError:
            return Response(
                {'error': 'number必须为整数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (Markdown.DoesNotExist, Document.DoesNotExist, KnowledgeBase.DoesNotExist):
            return Response(
                {'error': 'markdown不存在或已被删除'},
                status=status.HTTP_404_NOT_FOUND
            )