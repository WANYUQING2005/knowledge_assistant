# Media 目录

## 简介

Media目录用于存储用户上传的文件和系统生成的媒体内容。此目录主要由Django的媒体文件管理系统使用，负责保存知识库中的文档、用户头像等文件资源。

## 目录结构

```
media/
└── documents/       # 上传的文档文件
    ├── pdf/         # PDF文件
    ├── word/        # Word文档
    ├── markdown/    # Markdown文件
    └── other/       # 其他格式文件
```

## 主要功能

- **文档存储**：保存用户上传的各种格式文档
- **媒体管理**：由Django的媒体文件系统自动管理
- **资源服务**：通过Web服务提供这些文件的访问

## 使用注意事项

1. **文件安全**：
   - 生产环境中应确保适当的访问权限控制
   - 定期备份此目录内容

2. **存储管理**：
   - 监控磁盘空间使用情况
   - 考虑实现文件过期或清理策略

3. **部署考虑**：
   - 在生产环境中可能需要使用专门的静态文件服务器或云存储服务
   - 可配置使用Amazon S3或其他云存储解决方案

## 相关配置

在Django的settings.py中配置：

```python
# 媒体文件路径配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 文件上传处理
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# 最大上传文件大小限制
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

## 开发与生产环境差异

- **开发环境**：通常直接使用Django开发服务器提供媒体文件
- **生产环境**：应使用专门的静态文件服务器（如Nginx）或云存储服务
