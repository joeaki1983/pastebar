#!/usr/bin/env python3
"""
基于成功案例的 Ditto 到 PasteBar 数据转换脚本
参考可成功导入的备份文件格式
"""

import sqlite3
import os
import sys
import time
import hashlib
import argparse
import zipfile
import tempfile
from datetime import datetime
import uuid

def generate_short_uuid():
    """生成类似成功案例的短UUID"""
    return str(uuid.uuid4()).replace('-', '')[:21]

def create_pastebar_database(temp_db_path):
    """创建完全匹配的 PasteBar 数据库结构"""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    
    # 直接使用真实的schema文件内容
    schema_sql = """
CREATE TABLE __diesel_schema_migrations (
       version VARCHAR(50) PRIMARY KEY NOT NULL,
       run_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE collections (
    collection_id VARCHAR(50) PRIMARY KEY NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    is_selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    created_date TIMESTAMP NOT NULL,
    updated_date TIMESTAMP NOT NULL
);

CREATE TABLE items (
    item_id VARCHAR(50) PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    value VARCHAR(255),
    color VARCHAR(50),
    border_width INT DEFAULT 0,
    is_image BOOLEAN DEFAULT FALSE,
    image_path_full_res VARCHAR(255),
    image_preview_height INT DEFAULT 0,
    image_height INT DEFAULT 0,
    image_width INT DEFAULT 0,
    image_data_url VARCHAR(255),
    image_type VARCHAR(255),
    image_hash VARCHAR(255),
    image_scale INT DEFAULT 1,
    is_image_data BOOLEAN DEFAULT FALSE,
    is_masked BOOLEAN DEFAULT FALSE,
    is_text BOOLEAN DEFAULT FALSE,
    is_form BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,
    is_code BOOLEAN DEFAULT FALSE,
    is_link BOOLEAN DEFAULT FALSE,
    is_path BOOLEAN DEFAULT FALSE,
    is_file BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_protected BOOLEAN DEFAULT FALSE,
    is_command BOOLEAN DEFAULT FALSE,
    is_web_request BOOLEAN DEFAULT FALSE,
    is_web_scraping BOOLEAN DEFAULT FALSE,
    is_video BOOLEAN DEFAULT FALSE,
    has_emoji BOOLEAN DEFAULT FALSE,
    has_masked_words BOOLEAN DEFAULT FALSE,
    path_type VARCHAR(20),
    icon VARCHAR(20),
    icon_visibility VARCHAR(20),
    command_request_output TEXT,
    command_request_last_run_at BIGINT,
    request_options TEXT,
    form_template_options TEXT,
    links TEXT,
    detected_language VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_folder BOOLEAN NOT NULL DEFAULT FALSE,
    is_separator BOOLEAN NOT NULL DEFAULT FALSE,
    is_board BOOLEAN NOT NULL DEFAULT FALSE,
    is_menu BOOLEAN NOT NULL DEFAULT FALSE,
    is_clip BOOLEAN NOT NULL DEFAULT FALSE,
    size VARCHAR(10),
    layout VARCHAR(10),
    layout_items_max_width VARCHAR(10),
    layout_split INT NOT NULL DEFAULT 1,
    show_description BOOLEAN DEFAULT TRUE,
    pinned_order_number INT DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    created_date TIMESTAMP NOT NULL,
    updated_date TIMESTAMP NOT NULL,
    item_options TEXT
);

CREATE TABLE tabs (
    tab_id VARCHAR(50) PRIMARY KEY NOT NULL,
    collection_id VARCHAR(50) NOT NULL,
    tab_name VARCHAR(255) NOT NULL,
    tab_is_active BOOLEAN NOT NULL DEFAULT TRUE,
    tab_is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    tab_order_number INT NOT NULL DEFAULT 0,
    tab_color VARCHAR(50),
    tab_layout VARCHAR(10),
    tab_layout_split INT NOT NULL DEFAULT 2,
    tab_is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id) ON DELETE CASCADE
);

CREATE TABLE collection_menu (
    collection_id VARCHAR(50) NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    parent_id VARCHAR(50),
    order_number INT NOT NULL DEFAULT 0,
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES items(item_id) ON DELETE SET NULL,
    PRIMARY KEY (collection_id, item_id)
);

CREATE TABLE collection_clips (
    collection_id VARCHAR(50) NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    tab_id VARCHAR(50) NOT NULL,
    parent_id VARCHAR(50),
    order_number INT NOT NULL DEFAULT 0,
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE,
    FOREIGN KEY (tab_id) REFERENCES tabs(tab_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES items(item_id) ON DELETE SET NULL,
    PRIMARY KEY (collection_id, item_id, tab_id)
);

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
    is_pinned BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    links TEXT,
    detected_language VARCHAR(20),
    pinned_order_number INT DEFAULT 0,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    created_date TIMESTAMP NOT NULL,
    updated_date TIMESTAMP NOT NULL,
    history_options TEXT, 
    copied_from_app VARCHAR(255)
);

CREATE TABLE settings (
    name TEXT PRIMARY KEY NOT NULL UNIQUE,
    value_text TEXT,
    value_bool BOOLEAN,
    value_int INTEGER
);

CREATE TABLE link_metadata (
    metadata_id VARCHAR(50) PRIMARY KEY NOT NULL,
    history_id VARCHAR(50) UNIQUE,
    item_id VARCHAR(50) UNIQUE,
    link_url VARCHAR(255),
    link_title VARCHAR(255),
    link_description TEXT,
    link_image VARCHAR(255),
    link_domain VARCHAR(255),
    link_favicon TEXT, 
    link_track_artist VARCHAR(255), 
    link_track_title VARCHAR(255), 
    link_track_album VARCHAR(255), 
    link_track_year VARCHAR(4), 
    link_is_track BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (history_id) REFERENCES clipboard_history(history_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
);

CREATE INDEX idx_image_hash ON clipboard_history(image_hash);
CREATE INDEX idx_value_hash ON clipboard_history(value_hash);
"""
    
    # 执行schema创建
    cursor.executescript(schema_sql)
    
    # 插入所有必要的迁移记录 - 使用与成功案例相同的时间戳
    migrations = [
        ('20230805153510', '2025-07-25 09:29:30'),
        ('20230805230732', '2025-07-25 09:29:30'), 
        ('20230807141400', '2025-07-25 09:29:30'),
        ('20231024164344', '2025-07-25 09:29:30'),
        ('20240626160020', '2025-07-25 09:29:30'),
        ('20240629010924', '2025-07-25 09:29:30'),
        ('20240730220029', '2025-07-25 09:29:30')
    ]
    
    for version, run_on in migrations:
        cursor.execute("INSERT INTO __diesel_schema_migrations (version, run_on) VALUES (?, ?)", (version, run_on))
    
    conn.commit()
    return conn

def process_ditto_data(ditto_db_path, pastebar_conn):
    """处理 Ditto 数据库并转换为 PasteBar 格式 - 基于成功案例"""
    ditto_conn = sqlite3.connect(ditto_db_path)
    ditto_cursor = ditto_conn.cursor()
    pastebar_cursor = pastebar_conn.cursor()

    # 查询 Ditto 数据
    ditto_cursor.execute("""
        SELECT lID, lDate, mText, lDontAutoDelete, bIsGroup, lParentID, QuickPasteText, lastPasteDate
        FROM Main
        WHERE bIsGroup = 0 AND lParentID = -1
        ORDER BY lDate DESC
    """)

    ditto_records = ditto_cursor.fetchall()
    print(f"从 Ditto 数据库读取到 {len(ditto_records)} 条记录")

    if not ditto_records:
        print("❌ 没有找到 Ditto 数据记录")
        return 0, 0

    processed_count = 0
    skipped_count = 0

    for record in ditto_records:
        ditto_id, date_timestamp, text, dont_auto_delete, is_group, parent_id, quick_paste_text, last_paste_date = record

        if not text or text.strip() == "":
            skipped_count += 1
            continue

        # 生成新的 UUID - 使用与成功案例相似的格式
        history_id = generate_short_uuid()

        # 转换时间戳 - 关键：使用与成功案例相同的格式
        if date_timestamp:
            # Ditto 的时间戳转换为毫秒
            if date_timestamp < 10000000000:  # 如果是秒
                created_at = date_timestamp * 1000
            else:
                created_at = date_timestamp
        else:
            created_at = int(time.time() * 1000)

        updated_at = created_at

        # 转换为 datetime 对象 - 使用与成功案例相同的格式
        dt = datetime.fromtimestamp(created_at / 1000)
        created_date = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        updated_date = created_date

        # 处理文本内容
        value = text[:255] if text else ""
        value_preview = text[:150] if text else ""

        # 计算更多预览信息
        value_more_preview_lines = max(0, text.count('\n') - 5) if text else 0
        value_more_preview_chars = max(0, len(text) - 150) if text else 0

        # 计算哈希值
        value_hash = hashlib.sha256(text.encode('utf-8')).hexdigest() if text else ""

        # 检测内容类型 - 与成功案例保持一致
        is_text = 1 if text else 0
        is_image = 0
        is_link = 1 if text and ('http://' in text or 'https://' in text) else 0
        is_code = 1 if text and any(keyword in text.lower() for keyword in ['function', 'class', 'def ', 'var ', 'const ', 'import ', 'export ']) else 0
        has_emoji = 1 if text and any(ord(char) > 127 for char in text if ord(char) > 1000) else 0

        # 设置收藏状态 (Ditto 的 lDontAutoDelete 表示重要)
        is_favorite = 1 if dont_auto_delete else 0

        # 使用快速粘贴文本作为标题，如果没有则使用内容开头
        if quick_paste_text and quick_paste_text.strip():
            title = quick_paste_text[:255]
        else:
            title = (text[:50] + "..." if len(text) > 50 else text) if text else ""

        # 插入到 PasteBar 数据库 - 使用完整的字段列表
        try:
            pastebar_cursor.execute("""
                INSERT INTO clipboard_history (
                    history_id, title, value, value_preview,
                    value_more_preview_lines, value_more_preview_chars, value_hash,
                    is_image, image_path_full_res, image_data_low_res,
                    image_preview_height, image_height, image_width,
                    image_data_url, image_hash,
                    is_image_data, is_masked, is_text, is_code, is_link,
                    is_video, has_emoji, has_masked_words, is_pinned, is_favorite,
                    links, detected_language, pinned_order_number,
                    created_at, updated_at, created_date, updated_date,
                    history_options, copied_from_app
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, title, value, value_preview,
                value_more_preview_lines, value_more_preview_chars, value_hash,
                is_image, None, None,
                0, 0, 0,
                None, None,
                0, 0, is_text, is_code, is_link,
                0, has_emoji, 0, 0, is_favorite,
                None, None, 0,
                created_at, updated_at, created_date, updated_date,
                None, "Ditto"
            ))

            processed_count += 1

            if processed_count % 1000 == 0:
                print(f"Ditto: 已处理 {processed_count} 条记录...")
                pastebar_conn.commit()

        except Exception as e:
            print(f"插入记录时出错: {e}")
            print(f"记录详情: ID={ditto_id}, 文本长度={len(text) if text else 0}")
            skipped_count += 1

    pastebar_conn.commit()
    ditto_conn.close()

    print(f"Ditto 处理完成: 成功 {processed_count} 条, 跳过 {skipped_count} 条")
    return processed_count, skipped_count

def main():
    parser = argparse.ArgumentParser(description='创建 PasteBar 兼容的备份文件 (基于成功案例)')
    parser.add_argument('--ditto', required=True, help='Ditto 数据库路径')
    parser.add_argument('--output', required=True, help='输出备份文件路径 (.zip)')

    args = parser.parse_args()

    if not os.path.exists(args.ditto):
        print(f"错误: Ditto 数据库文件不存在: {args.ditto}")
        sys.exit(1)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "pastebar-db.data")

        # 创建 PasteBar 数据库
        print("创建 PasteBar 数据库结构...")
        pastebar_conn = create_pastebar_database(temp_db_path)

        # 处理 Ditto 数据
        total_processed, total_skipped = process_ditto_data(args.ditto, pastebar_conn)

        pastebar_conn.close()

        # 创建备份 ZIP 文件
        print(f"创建备份文件: {args.output}")
        with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_db_path, "pastebar-db.data")

        print(f"\n🎉 备份文件创建完成!")
        print(f"文件位置: {args.output}")
        print(f"总计处理: {total_processed} 条记录")
        print(f"跳过记录: {total_skipped} 条记录")

        print(f"\n📋 使用方法:")
        print(f"1. 打开 PasteBar 应用")
        print(f"2. 进入 设置 > 备份和恢复")
        print(f"3. 点击 '从文件恢复...'")
        print(f"4. 选择文件: {args.output}")
        print(f"5. 确认恢复操作")

if __name__ == "__main__":
    main()
