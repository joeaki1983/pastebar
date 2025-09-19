#!/usr/bin/env python3
"""
Ditto 数据库转换为 PasteBar 可导入的备份文件

使用方法:
python3 convert_ditto_to_pastebar_backup.py /Users/joe/Downloads/Ditto.db
"""

import sqlite3
import os
import sys
import time
import hashlib
import zipfile
import tempfile
from datetime import datetime
import random
import string
import re

def generate_pastebar_uuid():
    """生成 PasteBar 兼容的 UUID 格式"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=21))

def parse_ditto_time(timestamp):
    """解析 Ditto 时间戳 (Windows FILETIME)"""
    try:
        # Windows FILETIME 转 Unix 时间戳
        unix_timestamp = (timestamp - 116444736000000000) / 10000000
        return int(unix_timestamp * 1000)  # 毫秒时间戳
    except:
        return int(time.time() * 1000)

def calculate_hash(content):
    """计算内容哈希"""
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def detect_content_type(text):
    """检测内容类型"""
    if not text:
        return False, False, False, False, False
    
    # 检测链接
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    is_link = bool(re.search(url_pattern, text))
    
    # 检测视频链接
    video_patterns = [r'youtube\.com/watch', r'youtu\.be/', r'vimeo\.com/', r'bilibili\.com/', r'\.mp4', r'\.avi', r'\.mov']
    is_video = any(re.search(pattern, text, re.IGNORECASE) for pattern in video_patterns)
    
    # 检测代码
    code_indicators = ['function ', 'def ', 'class ', 'import ', 'from ', '#!/', '<?php', '<html', '<script', 'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE TABLE', '```', 'console.log']
    is_code = any(indicator in text for indicator in code_indicators)
    
    # 检测 emoji
    emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
    has_emoji = bool(re.search(emoji_pattern, text))
    
    return True, is_code, is_link, is_video, has_emoji

def create_preview(text, max_length=150):
    """创建预览文本"""
    if not text:
        return None
    preview = re.sub(r'\s+', ' ', text.strip())
    return preview[:max_length] + "..." if len(preview) > max_length else preview

def create_pastebar_database(temp_db_path):
    """创建 PasteBar 兼容的数据库结构"""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 创建迁移表
    cursor.execute("""
        CREATE TABLE __diesel_schema_migrations (
            version VARCHAR(50) PRIMARY KEY NOT NULL,
            run_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 插入必要的迁移版本
    migrations = [
        '20230805153510',
        '20230805230732', 
        '20230807141400',
        '20231024164344',
        '20240626160020',
        '20240629010924',
        '20240730220029'
    ]
    
    for migration in migrations:
        cursor.execute("INSERT INTO __diesel_schema_migrations (version) VALUES (?)", (migration,))
    
    # 创建主要表结构
    cursor.execute("""
        CREATE TABLE collections (
            id VARCHAR(50) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(255),
            is_enabled BOOLEAN DEFAULT TRUE,
            is_default BOOLEAN DEFAULT FALSE,
            is_pinned BOOLEAN DEFAULT FALSE,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            created_date VARCHAR(255) NOT NULL,
            updated_date VARCHAR(255) NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE items (
            item_id VARCHAR(50) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(255),
            value VARCHAR(255),
            color VARCHAR(255),
            border_width INTEGER DEFAULT 1,
            is_separator BOOLEAN DEFAULT FALSE,
            is_disabled BOOLEAN DEFAULT FALSE,
            is_folder BOOLEAN DEFAULT FALSE,
            is_image BOOLEAN DEFAULT FALSE,
            is_text BOOLEAN DEFAULT FALSE,
            is_link BOOLEAN DEFAULT FALSE,
            is_video BOOLEAN DEFAULT FALSE,
            is_code BOOLEAN DEFAULT FALSE,
            has_emoji BOOLEAN DEFAULT FALSE,
            icon VARCHAR(255),
            icon_visibility BOOLEAN DEFAULT TRUE,
            layout_split VARCHAR(255) DEFAULT 'single',
            layout_split_value REAL DEFAULT 0.5,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            created_date VARCHAR(255) NOT NULL,
            updated_date VARCHAR(255) NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE tabs (
            tab_id VARCHAR(50) PRIMARY KEY NOT NULL,
            name VARCHAR(255) NOT NULL,
            color VARCHAR(255),
            is_active BOOLEAN DEFAULT FALSE,
            order_number INTEGER DEFAULT 0,
            collection_id VARCHAR(50) NOT NULL,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            created_date VARCHAR(255) NOT NULL,
            updated_date VARCHAR(255) NOT NULL,
            FOREIGN KEY (collection_id) REFERENCES collections (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE collection_menu (
            collection_id VARCHAR(50) NOT NULL,
            item_id VARCHAR(50) NOT NULL,
            parent_id VARCHAR(50),
            order_number INTEGER NOT NULL,
            PRIMARY KEY (collection_id, item_id),
            FOREIGN KEY (collection_id) REFERENCES collections (id),
            FOREIGN KEY (item_id) REFERENCES items (item_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE collection_clips (
            collection_id VARCHAR(50) NOT NULL,
            item_id VARCHAR(50) NOT NULL,
            tab_id VARCHAR(50) NOT NULL,
            parent_id VARCHAR(50),
            order_number INTEGER NOT NULL,
            PRIMARY KEY (collection_id, item_id),
            FOREIGN KEY (collection_id) REFERENCES collections (id),
            FOREIGN KEY (item_id) REFERENCES items (item_id),
            FOREIGN KEY (tab_id) REFERENCES tabs (tab_id)
        )
    """)
    
    # 创建剪贴板历史表 - 这是主要的数据表
    cursor.execute("""
        CREATE TABLE clipboard_history (
            history_id VARCHAR(50) PRIMARY KEY NOT NULL,
            title VARCHAR(255),
            value VARCHAR(255),
            value_preview VARCHAR(150),
            value_more_preview_lines INT DEFAULT 0,
            value_more_preview_chars INT DEFAULT 0,
            value_hash VARCHAR(255),
            is_image BOOLEAN DEFAULT FALSE,
            image_path_full_res VARCHAR(255),
            image_data_low_res BLOB,
            image_preview_height INT DEFAULT 0,
            image_height INT DEFAULT 0,
            image_width INT DEFAULT 0,
            image_data_url VARCHAR(255),
            image_hash VARCHAR(255),
            is_image_data BOOLEAN DEFAULT FALSE,
            is_masked BOOLEAN DEFAULT FALSE,
            is_text BOOLEAN DEFAULT FALSE,
            is_code BOOLEAN DEFAULT FALSE,
            is_link BOOLEAN DEFAULT FALSE,
            is_video BOOLEAN DEFAULT FALSE,
            has_emoji BOOLEAN DEFAULT FALSE,
            has_masked_words BOOLEAN DEFAULT FALSE,
            links VARCHAR(255),
            is_pinned BOOLEAN DEFAULT FALSE,
            is_favorite BOOLEAN DEFAULT FALSE,
            detected_language VARCHAR(255),
            pinned_order_number INT,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            created_date VARCHAR(255) NOT NULL,
            updated_date VARCHAR(255) NOT NULL,
            history_options VARCHAR(255),
            copied_from_app VARCHAR(255)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE settings (
            name VARCHAR(255) PRIMARY KEY NOT NULL,
            value_text VARCHAR(255),
            value_bool BOOLEAN,
            value_int INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE link_metadata (
            id VARCHAR(50) PRIMARY KEY NOT NULL,
            url VARCHAR(255) NOT NULL,
            title VARCHAR(255),
            description VARCHAR(255),
            image VARCHAR(255),
            favicon VARCHAR(255),
            domain VARCHAR(255),
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX idx_value_hash ON clipboard_history(value_hash)")
    cursor.execute("CREATE INDEX idx_image_hash ON clipboard_history(image_hash)")
    
    conn.commit()
    return conn

def convert_ditto_to_pastebar(ditto_db_path, output_path):
    """转换 Ditto 数据库为 PasteBar 备份文件"""
    
    if not os.path.exists(ditto_db_path):
        print(f"错误: Ditto 数据库文件不存在: {ditto_db_path}")
        return False
    
    print(f"开始转换 Ditto 数据库: {ditto_db_path}")
    
    # 连接 Ditto 数据库
    ditto_conn = sqlite3.connect(ditto_db_path)
    ditto_cursor = ditto_conn.cursor()
    
    # 查询 Ditto 数据
    print("正在查询 Ditto 数据...")
    ditto_cursor.execute("""
        SELECT lID, lDate, mText, bIsGroup, lParentID, lDontAutoDelete
        FROM Main 
        WHERE bIsGroup = 0 AND mText IS NOT NULL AND mText != ''
        ORDER BY lDate DESC
    """)
    
    ditto_records = ditto_cursor.fetchall()
    print(f"找到 {len(ditto_records)} 条 Ditto 记录")
    
    # 创建临时目录和 PasteBar 数据库
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "pastebar-db.data")
        
        print("创建 PasteBar 数据库结构...")
        pastebar_conn = create_pastebar_database(temp_db_path)
        pastebar_cursor = pastebar_conn.cursor()
        
        # 转换数据
        print("正在转换数据...")
        imported_count = 0
        skipped_count = 0
        
        for record in ditto_records:
            ditto_id, ditto_date, text, is_group, parent_id, dont_auto_delete = record
            
            if not text or text.strip() == '':
                skipped_count += 1
                continue
            
            # 生成新的 UUID
            history_id = generate_pastebar_uuid()
            
            # 转换时间戳
            created_at = parse_ditto_time(ditto_date)
            updated_at = created_at
            
            # 创建日期字符串
            created_date = datetime.fromtimestamp(created_at / 1000).strftime('%Y-%m-%d %H:%M:%S')
            updated_date = created_date
            
            # 计算哈希和检测类型
            value_hash = calculate_hash(text)
            is_text, is_code, is_link, is_video, has_emoji = detect_content_type(text)
            
            # 创建预览和标题
            value_preview = create_preview(text)
            title = create_preview(text, 50)
            
            # 计算预览统计
            lines = text.split('\n')
            value_more_preview_lines = max(0, len(lines) - 3) if len(lines) > 3 else 0
            value_more_preview_chars = max(0, len(text) - 150) if len(text) > 150 else 0
            
            # 收藏状态
            is_favorite = bool(dont_auto_delete)
            
            # 插入数据
            try:
                pastebar_cursor.execute("""
                    INSERT INTO clipboard_history (
                        history_id, title, value, value_preview, value_more_preview_lines,
                        value_more_preview_chars, value_hash, is_image, image_path_full_res,
                        image_data_low_res, image_preview_height, image_height, image_width,
                        image_data_url, image_hash, is_image_data, is_masked, is_text,
                        is_code, is_link, is_video, has_emoji, has_masked_words, links,
                        is_pinned, is_favorite, detected_language, pinned_order_number,
                        created_at, updated_at, created_date, updated_date, history_options,
                        copied_from_app
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    history_id, title, text, value_preview, value_more_preview_lines,
                    value_more_preview_chars, value_hash, False, None,
                    None, None, None, None,
                    None, None, False, False, is_text,
                    is_code, is_link, is_video, has_emoji, False, None,
                    False, is_favorite, None, None,
                    created_at, updated_at, created_date, updated_date, None,
                    'Ditto'
                ))
                
                imported_count += 1
                
                if imported_count % 1000 == 0:
                    print(f"已转换 {imported_count} 条记录...")
                    
            except Exception as e:
                print(f"转换记录失败 {ditto_id}: {e}")
                skipped_count += 1
        
        # 提交数据库更改
        pastebar_conn.commit()
        pastebar_conn.close()
        ditto_conn.close()
        
        # 创建 ZIP 备份文件
        print(f"创建备份文件: {output_path}")
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_db_path, "pastebar-db.data")
        
        print(f"\n转换完成!")
        print(f"成功转换: {imported_count} 条记录")
        print(f"跳过记录: {skipped_count} 条")
        print(f"备份文件: {output_path}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 convert_ditto_to_pastebar_backup.py <Ditto.db路径>")
        print("示例: python3 convert_ditto_to_pastebar_backup.py /Users/joe/Downloads/Ditto.db")
        sys.exit(1)
    
    ditto_db_path = sys.argv[1]
    
    # 生成输出文件名
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_path = f"/Users/joe/Downloads/ditto-pastebar-backup-{timestamp}.zip"
    
    print("Ditto 数据转换为 PasteBar 备份文件")
    print("=" * 50)
    print(f"源文件: {ditto_db_path}")
    print(f"输出文件: {output_path}")
    print()
    
    success = convert_ditto_to_pastebar(ditto_db_path, output_path)
    
    if success:
        print(f"\n✅ 转换成功!")
        print(f"📁 备份文件位置: {output_path}")
        print(f"📋 现在您可以在 PasteBar 中导入这个备份文件")
        print(f"💡 导入步骤: PasteBar 设置 → 备份和恢复 → 从文件恢复")
    else:
        print("\n❌ 转换失败!")

if __name__ == "__main__":
    main()
