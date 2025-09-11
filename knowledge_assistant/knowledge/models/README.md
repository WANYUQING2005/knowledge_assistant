# Knowledge 模型目录

## 简介

此目录包含与知识库系统相关的数据模型定义，负责存储和管理知识库、文档和文档片段等数据实体。模型被组织成不同的文件，以实现清晰的代码结构和关注点分离。

## 文件说明

### knowledge_base_models.py

此文件定义了与知识库相关的模型类：

- **KnowledgeBase**：表示一个完整的知识库集合，包含名称、描述、创建者等信息
- **KnowledgeBasePermission**：定义用户对知识库的访问权限
- **KnowledgeBaseTag**：知识库的标签，用于分类和检索

### document_models.py

此文件定义了与文档相关的模型类：

- **Document**：表示上传的文档，包含文件路径、元数据、上传时间等信息
- **DocumentChunk**：文档被分割后的文本片段，用于向量存储和精确检索
- **DocumentVector**：存储文档片段的向量表示，用于相似度检索
- **DocumentTag**：文档的标签，用于文档分类和组织

## 模型关系

- 一个`KnowledgeBase`包含多个`Document`（一对多关系）
- 一个`Document`被分割为多个`DocumentChunk`（一对多关系）
- 每个`DocumentChunk`对应一个`DocumentVector`（一对一关系）
- `KnowledgeBase`和`Document`可以有多个标签（多对多关系）

## 使用示例

```python
# 创建知识库并添加文档
knowledge_base = KnowledgeBase.objects.create(
    name="Python编程",
    description="Python相关教程和文档",
    creator=user
)

document = Document.objects.create(
    knowledge_base=knowledge_base,
    title="Python基础入门",
    file_path="documents/python_basics.pdf",
    file_type="pdf",
    uploader=user
)

# 为文档添加标签
tag = DocumentTag.objects.create(name="编程语言")
document.tags.add(tag)

# 获取知识库中的所有文档
documents = knowledge_base.document_set.all()

# 获取文档的所有文本片段
chunks = document.documentchunk_set.all()
```

## 数据迁移

当修改模型后，需要创建和应用迁移：

```bash
python manage.py makemigrations knowledge
python manage.py migrate knowledge
```
