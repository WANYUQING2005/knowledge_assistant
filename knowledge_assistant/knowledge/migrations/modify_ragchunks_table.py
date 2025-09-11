from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0001_initial'),  # 替换为您最后一个迁移文件的名称
    ]

    operations = [
        # 1. 重命名已存在的表以备份
        migrations.RunSQL(
            "ALTER TABLE knowledge_ragchunks RENAME TO knowledge_ragchunks_backup;",
            "ALTER TABLE knowledge_ragchunks_new RENAME TO knowledge_ragchunks;"
        ),

        # 2. 创建具有新结构的表
        migrations.RunSQL("""
            CREATE TABLE knowledge_ragchunks (
                id varchar(36) PRIMARY KEY,
                title varchar(200),
                content varchar(350),
                vector_id varchar(36),
                number int,
                word_count int,
                document_id varchar(36),
                creater_id varchar(36),
                create_at datetime(6),
                kb_id varchar(36)
            );
        """),

        # 3. 从备份表复制数据（可根据实际情况调整）
        migrations.RunSQL("""
            INSERT INTO knowledge_ragchunks (
                id, 
                title, 
                content, 
                vector_id, 
                number, 
                word_count, 
                document_id, 
                creater_id, 
                create_at, 
                kb_id
            )
            SELECT 
                CAST(id AS CHAR(36)), 
                tag0, 
                content, 
                content_hash, 
                ord, 
                LENGTH(content), 
                CAST(doc_id AS CHAR(36)), 
                JSON_EXTRACT(metadata, '$.creater_id'), 
                created_at, 
                JSON_EXTRACT(metadata, '$.kb_id')
            FROM knowledge_ragchunks_backup;
        """, reverse_sql=""),
    ]
