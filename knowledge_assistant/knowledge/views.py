from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models.knowledge_base_models import KnowledgeBase
from .serializers import KnowledgeBaseSerializer
from django.conf import settings
from .models.document_models import Document
from .serializers import DocumentSerializer, DocumentListSerializer
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
import sys
from pathlib import Path
import json
from typing import List, Dict, Any, Set
from django.db import connection

# 可以根据需要调整导入路径
try:
    from rag_demo.tags_search import TagBasedSearch
except ImportError:
    # 如果直接导入失败，使用新的标签搜索服务
    pass

class CreateKnowledgeBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = KnowledgeBaseSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            # 设置所有者ID
            serializer.save(owner_user_id=request.user.id)  # 移除str()
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
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        storage_path = os.path.join(storage_dir, unique_filename)

        # 保存文件到本地系统（可替换为文档数据库API）
        with open(storage_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # 4. 构建并保存Document对象
        # 确定创建者ID：优先使用请求传入值，否则使用知识库所有者ID
        creater_id = request.data.get('creater_id', knowledge_base.owner_user_id)
        # 只存储相对路径，不包含MEDIA_ROOT
        relative_path = os.path.relpath(storage_path, settings.MEDIA_ROOT)
        document = Document(
            knowledge_base_id=knowledge_base_id,
            title=request.data.get('title', os.path.splitext(file.name)[0]),  # 从文件名提取标题
            file_type=file.content_type.split('/')[-1],  # 提取MIME类型后缀
            storage_uri=relative_path.replace('\\', '/'),  # 统一使用Unix风格路径
            chunk_count=0,  # 初始化为0，后续可通过异步任务更新
            creater_id=creater_id
        )
        # 移除这里的split_into_markdowns调用，因为save方法内部已经会调用
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
        knowledge_base_id = request.query_params.get('knowledge_base_id')
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
        return Response({'message': '删除成功'},status=status.HTTP_204_NO_CONTENT)

class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        document_id = request.query_params.get('document_id')
        if not document_id:
            return Response(
                {'error': 'document_id为必填项'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证文档所有权
        try:
            document = Document.objects.get(id=document_id)
            # 验证文档所属知识库的所有权
            knowledge_base = KnowledgeBase.objects.get(
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
        
        # 更新知识库的存储大小
        knowledge_base.update_storage_size()
        
        return Response({'message': '删除成功'},status=status.HTTP_204_NO_CONTENT)
class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取请求中的kb_id参数
        kb_id = request.query_params.get('kb_id')
        if not kb_id:
            return Response(
                {'error': 'kb_id为必填参数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 验证知识库是否存在
        try:
            knowledge_base = KnowledgeBase.objects.get(id=kb_id)
        except KnowledgeBase.DoesNotExist:
            return Response(
                {'error': '知识库不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 查询该知识库下的所有文档
        documents = Document.objects.filter(knowledge_base_id=kb_id)
        serializer = DocumentListSerializer(documents, many=True)

        return Response(serializer.data)


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

class TagSearchView(APIView):
    """基于标签的语义搜索视图"""

    def post(self, request):
        """处理标签搜索请求"""
        tag = request.data.get("tag")
        if not tag:
            return Response({"status": "error", "message": "缺少tag参数"},
                           status=status.HTTP_400_BAD_REQUEST)

        try:
            # 创建简化版标签搜索器实例，与当前数据库结构兼容
            searcher = SimplifiedTagBasedSearch()

            # 执行标签搜索
            results = searcher.search_by_tags(
                query=tag,
                topk_tags=int(request.data.get('topk_tags', 8)),
                limit_per_tag=int(request.data.get('limit_per_tag', 50))
            )

            # 构建响应
            response_data = {
                "status": "success",
                "query_tag": tag,
                "matched_tags": results.get("matched_tags", []),
                "chunks": results.get("chunks", []),
                "message": results.get("message", "")
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"标签搜索出错: {error_details}")
            return Response(
                {"status": "error", "message": f"标签搜索执行失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimplifiedTagBasedSearch:
    """简化版的标签搜索，直接使用SQL查询，适用于当前数据库结构"""

    def search_by_tags(self, query: str, topk_tags: int = 8, limit_per_tag: int = 50) -> Dict[str, Any]:
        """基于标签搜索知识块"""
        if not query or not query.strip():
            return {"status": "error", "message": "搜索词不能为空", "matched_tags": [], "chunks": []}

        # 步骤1: 获取所有标签
        all_tags = self._get_all_tags()
        print(f"[INFO] 标签总数：{len(all_tags)}")

        if not all_tags:
            return {"query": query, "matched_tags": [], "chunks": [], "message": "数据库中没有任何标签"}

        # 步骤2: 简单字符串匹配查找相关标签
        matched_tags = self._match_tags(query.lower().strip(), all_tags, topk_tags)
        print(f"[INFO] 匹配标签：{matched_tags}")

        if not matched_tags:
            return {
                "query": query,
                "matched_tags": [],
                "chunks": [],
                "message": "未匹配到相关标签"
            }

        # 步骤3: 获取匹配标签对应的知识块
        chunks = self._get_chunks_by_tags(matched_tags, limit_per_tag)
        print(f"[INFO] 命中知识块：{len(chunks)}")

        return {
            "query": query,
            "matched_tags": matched_tags,
            "chunks": chunks,
            "message": f"命中 {len(chunks)} 个知识块"
        }

    def _get_all_tags(self) -> Set[str]:
        """从数据库中获取所有标签"""
        tags = set()
        with connection.cursor() as cursor:
            # 从content字段获取标签（而不是title或tag0字段）
            cursor.execute("""
                SELECT DISTINCT content FROM knowledge_ragchunks
                WHERE content IS NOT NULL AND content != ''
            """)
            for row in cursor.fetchall():
                if row[0] and row[0].strip():
                    tags.add(row[0].strip())

            # 从chunk_tags JSON字段获取标签（如果存在的话）
            try:
                cursor.execute("""
                    SELECT chunk_tags FROM knowledge_ragchunks 
                    WHERE chunk_tags IS NOT NULL AND chunk_tags != ''
                """)
                for row in cursor.fetchall():
                    if row[0]:
                        try:
                            tag_list = json.loads(row[0])
                            if isinstance(tag_list, list):
                                for tag in tag_list:
                                    if isinstance(tag, str) and tag.strip():
                                        tags.add(tag.strip())
                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            print(f"提取标签时出错: {e}")
            except Exception as e:
                # 如果chunk_tags列不存在，忽略这部分
                print(f"获取chunk_tags时出错，可能列不存在: {e}")
        return tags

    def _match_tags(self, query: str, all_tags: Set[str], topk: int = 10) -> List[str]:
        """简单字符串匹配相关标签"""
        # 首先尝试精确匹配
        exact_matches = [tag for tag in all_tags if query == tag.lower()]

        # 然后尝试包含匹配
        contains_matches = [tag for tag in all_tags
                           if query in tag.lower() and tag not in exact_matches]

        # 最后尝试被包含匹配
        contained_matches = [tag for tag in all_tags
                            if tag.lower() in query and tag not in exact_matches
                            and tag not in contains_matches]

        # 按优先级合并结果
        result = exact_matches + contains_matches + contained_matches
        return result[:topk]

    def _get_chunks_by_tags(self, tags: List[str], limit_per_tag: int = 50) -> List[Dict[str, Any]]:
        """获取与标签相关的知识块"""
        if not tags:
            return []

        chunks = []
        with connection.cursor() as cursor:
            # 基于content内容匹配搜索标签
            for tag in tags:
                try:
                    cursor.execute("""
                        SELECT id, ord, content, content_hash, split, metadata, chunk_tags, created_at, tag0, document_id
                        FROM knowledge_ragchunks
                        WHERE content LIKE %s
                        LIMIT %s
                    """, [f"%{tag}%", limit_per_tag])

                    for row in cursor.fetchall():
                        metadata = {}
                        if row[5]:  # metadata (索引5)
                            try:
                                metadata = json.loads(row[5])
                            except (json.JSONDecodeError, TypeError):
                                pass

                        chunk = {
                            "id": row[0],
                            "number": row[1],      # ord
                            "content": row[2],     # content
                            "vector_id": row[3],   # content_hash
                            "split": row[4],       # split
                            "metadata": metadata,  # 解析后的metadata
                            "tags": json.loads(row[6]) if row[6] else [],  # chunk_tags解析为列表
                            "create_at": str(row[7]) if row[7] else "",   # created_at
                            "tag0": row[8] or "",  # tag0
                            "document_id": row[9]  # document_id
                        }
                        chunks.append(chunk)
                except Exception as e:
                    print(f"基于content搜索出错: {e}")

            # 尝试基于tag0字段搜索
            try:
                for tag in tags:
                    cursor.execute("""
                        SELECT id, ord, content, content_hash, split, metadata, chunk_tags, created_at, tag0, document_id
                        FROM knowledge_ragchunks
                        WHERE tag0 LIKE %s
                        LIMIT %s
                    """, [f"%{tag}%", limit_per_tag])

                    for row in cursor.fetchall():
                        chunk_id = row[0]
                        # 避免重复添加
                        if any(c["id"] == chunk_id for c in chunks):
                            continue

                        metadata = {}
                        if row[5]:  # metadata
                            try:
                                metadata = json.loads(row[5])
                            except (json.JSONDecodeError, TypeError):
                                pass

                        chunk = {
                            "id": chunk_id,
                            "number": row[1],      # ord
                            "content": row[2],     # content
                            "vector_id": row[3],   # content_hash
                            "split": row[4],       # split
                            "metadata": metadata,  # 解析后的metadata
                            "tags": json.loads(row[6]) if row[6] else [],  # chunk_tags解析为列表
                            "create_at": str(row[7]) if row[7] else "",   # created_at
                            "tag0": row[8] or "",  # tag0
                            "document_id": row[9]  # document_id
                        }
                        chunks.append(chunk)
            except Exception as e:
                print(f"基于tag0搜索出错: {e}")

            # 尝试基于chunk_tags JSON字段搜索
            try:
                for tag in tags:
                    cursor.execute("""
                        SELECT id, ord, content, content_hash, split, metadata, chunk_tags, created_at, tag0, document_id
                        FROM knowledge_ragchunks
                        WHERE chunk_tags LIKE %s
                        LIMIT %s
                    """, [f"%{tag}%", limit_per_tag])

                    for row in cursor.fetchall():
                        chunk_id = row[0]
                        # 避免重复添加
                        if any(c["id"] == chunk_id for c in chunks):
                            continue

                        metadata = {}
                        if row[5]:  # metadata
                            try:
                                metadata = json.loads(row[5])
                            except (json.JSONDecodeError, TypeError):
                                pass

                        chunk = {
                            "id": chunk_id,
                            "number": row[1],      # ord
                            "content": row[2],     # content
                            "vector_id": row[3],   # content_hash
                            "split": row[4],       # split
                            "metadata": metadata,  # 解析后的metadata
                            "tags": json.loads(row[6]) if row[6] else [],  # chunk_tags解析为列表
                            "create_at": str(row[7]) if row[7] else "",   # created_at
                            "tag0": row[8] or "",  # tag0
                            "document_id": row[9]  # document_id
                        }
                        chunks.append(chunk)
            except Exception as e:
                print(f"基于chunk_tags搜索出错: {e}")

        return chunks
