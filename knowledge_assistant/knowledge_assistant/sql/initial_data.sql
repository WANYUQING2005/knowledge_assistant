-- 插入默认管理员用户（密码需使用Django加密格式）
INSERT INTO users (username, email, password, is_active, is_staff)
VALUES (
    'admin',
    'admin@example.com',
    'pbkdf2_sha256$600000$abc123...',  -- 实际项目中需替换为Django加密后的密码
    TRUE,
    TRUE
) ON DUPLICATE KEY UPDATE username=username;

-- 插入测试用户
INSERT INTO users (username, email, password, is_active)
VALUES
    ('testuser1', 'test1@example.com', 'pbkdf2_sha256$600000$def456...', TRUE),
    ('testuser2', 'test2@example.com', 'pbkdf2_sha256$600000$ghi789...', TRUE)
ON DUPLICATE KEY UPDATE username=username;