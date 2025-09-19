#!/usr/bin/env python3
"""
创建 PasteBar 兼容的备份文件

将 EcoPaste 和 Ditto 数据库转换为 PasteBar 可以导入的备份格式

使用方法:
python3 create_pastebar_backup.py --ecopaste /path/to/EcoPaste.db --ditto /path/to/Ditto.db --output /path/to/output.zip
"""

import sqlite3
import sys
import os
import hashlib
import time
import argparse
import zipfile
import tempfile
import shutil
from datetime import datetime
import uuid

def generate_uuid():
    """生成唯一ID"""
    return str(uuid.uuid4())

def calculate_hash(content):
    """计算内容哈希"""
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def get_preview_text(text, max_length=150):
    """生成预览文本"""
    if not text:
        return None
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def parse_ecopaste_time(time_str):
    """解析 EcoPaste 时间格式"""
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return int(dt.timestamp() * 1000)
    except:
        return int(time.time() * 1000)

def parse_ditto_time(timestamp):
    """解析 Ditto 时间戳"""
    try:
        return int(timestamp * 1000)
    except:
        return int(time.time() * 1000)

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

    # 插入所有必要的迁移记录
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

    conn.commit()
    return conn

def import_ecopaste_to_temp_db(ecopaste_db_path, temp_cursor):
    """将 EcoPaste 数据导入临时数据库"""
    print("处理 EcoPaste 数据...")
    
    eco_conn = sqlite3.connect(ecopaste_db_path)
    eco_cursor = eco_conn.cursor()
    
    try:
        eco_cursor.execute("""
            SELECT id, type, value, search, count, width, height, 
                   favorite, createTime, note, subtype
            FROM history 
            ORDER BY createTime DESC
        """)
        
        eco_records = eco_cursor.fetchall()
        print(f"找到 {len(eco_records)} 条 EcoPaste 记录")
        
        imported_count = 0
        skipped_count = 0
        
        for record in eco_records:
            eco_id, content_type, value, search, count, width, height, favorite, create_time, note, subtype = record
            
            if not value or value.strip() == "":
                skipped_count += 1
                continue
            
            # 检测内容类型
            is_text = content_type in ['text', 'html', 'rtf']
            is_image = content_type == 'image'
            is_link = 'http' in str(value).lower() if value else False
            
            # 生成数据
            history_id = generate_uuid()
            created_timestamp = parse_ecopaste_time(create_time)
            value_hash = calculate_hash(value)
            value_preview = get_preview_text(value)
            title = search if search else value_preview
            
            insert_data = {
                'history_id': history_id,
                'title': title,
                'value': value,
                'value_preview': value_preview,
                'value_hash': value_hash,
                'is_image': is_image,
                'image_width': width,
                'image_height': height,
                'is_text': is_text,
                'is_link': is_link,
                'is_favorite': bool(favorite),
                'created_at': created_timestamp,
                'updated_at': created_timestamp,
                'created_date': datetime.fromtimestamp(created_timestamp / 1000),
                'updated_date': datetime.fromtimestamp(created_timestamp / 1000),
                'copied_from_app': 'EcoPaste'
            }
            
            try:
                temp_cursor.execute("""
                    INSERT INTO clipboard_history (
                        history_id, title, value, value_preview, value_hash,
                        is_image, image_width, image_height, is_text, is_link,
                        is_favorite, created_at, updated_at, created_date, updated_date,
                        copied_from_app
                    ) VALUES (
                        :history_id, :title, :value, :value_preview, :value_hash,
                        :is_image, :image_width, :image_height, :is_text, :is_link,
                        :is_favorite, :created_at, :updated_at, :created_date, :updated_date,
                        :copied_from_app
                    )
                """, insert_data)
                
                imported_count += 1
                
                if imported_count % 1000 == 0:
                    print(f"EcoPaste: 已处理 {imported_count} 条记录...")
                    
            except sqlite3.IntegrityError:
                skipped_count += 1
            except Exception as e:
                print(f"EcoPaste 处理记录失败 {eco_id}: {e}")
                skipped_count += 1
        
        print(f"EcoPaste 处理完成: 成功 {imported_count} 条, 跳过 {skipped_count} 条")
        return imported_count, skipped_count
        
    finally:
        eco_conn.close()

def import_ditto_to_temp_db(ditto_db_path, temp_cursor):
    """将 Ditto 数据导入临时数据库"""
    print("处理 Ditto 数据...")
    
    ditto_conn = sqlite3.connect(ditto_db_path)
    ditto_cursor = ditto_conn.cursor()
    
    try:
        ditto_cursor.execute("""
            SELECT lID, lDate, mText, lDontAutoDelete, bIsGroup, lParentID, 
                   QuickPasteText, lastPasteDate
            FROM Main 
            WHERE bIsGroup = 0 AND lParentID = -1
            ORDER BY lDate DESC
        """)
        
        ditto_records = ditto_cursor.fetchall()
        print(f"找到 {len(ditto_records)} 条 Ditto 记录")
        
        imported_count = 0
        skipped_count = 0
        
        for record in ditto_records:
            ditto_id, date_timestamp, text, dont_auto_delete, is_group, parent_id, quick_paste_text, last_paste_date = record
            
            if not text or text.strip() == "":
                skipped_count += 1
                continue
            
            # 获取数据格式
            ditto_cursor.execute("""
                SELECT strClipBoardFormat FROM Data WHERE lParentID = ?
            """, (ditto_id,))
            
            data_formats = [row[0] for row in ditto_cursor.fetchall()]
            
            # 检测内容类型
            is_image = any(fmt in ['CF_DIB', 'CF_BITMAP', 'PNG', 'JPEG'] for fmt in data_formats)
            is_text = not is_image
            is_link = text and (text.startswith('http://') or text.startswith('https://'))
            
            # 生成数据
            history_id = generate_uuid()
            created_timestamp = parse_ditto_time(date_timestamp)
            value_hash = calculate_hash(text)
            value_preview = get_preview_text(text)
            title = quick_paste_text if quick_paste_text else value_preview
            
            insert_data = {
                'history_id': history_id,
                'title': title,
                'value': text,
                'value_preview': value_preview,
                'value_hash': value_hash,
                'is_image': is_image,
                'image_width': None,
                'image_height': None,
                'is_text': is_text,
                'is_link': is_link,
                'is_favorite': bool(dont_auto_delete),
                'created_at': created_timestamp,
                'updated_at': created_timestamp,
                'created_date': datetime.fromtimestamp(created_timestamp / 1000),
                'updated_date': datetime.fromtimestamp(created_timestamp / 1000),
                'copied_from_app': 'Ditto'
            }
            
            try:
                temp_cursor.execute("""
                    INSERT INTO clipboard_history (
                        history_id, title, value, value_preview, value_hash,
                        is_image, image_width, image_height, is_text, is_link,
                        is_favorite, created_at, updated_at, created_date, updated_date,
                        copied_from_app
                    ) VALUES (
                        :history_id, :title, :value, :value_preview, :value_hash,
                        :is_image, :image_width, :image_height, :is_text, :is_link,
                        :is_favorite, :created_at, :updated_at, :created_date, :updated_date,
                        :copied_from_app
                    )
                """, insert_data)
                
                imported_count += 1
                
                if imported_count % 1000 == 0:
                    print(f"Ditto: 已处理 {imported_count} 条记录...")
                    
            except sqlite3.IntegrityError:
                skipped_count += 1
            except Exception as e:
                print(f"Ditto 处理记录失败 {ditto_id}: {e}")
                skipped_count += 1
        
        print(f"Ditto 处理完成: 成功 {imported_count} 条, 跳过 {skipped_count} 条")
        return imported_count, skipped_count
        
    finally:
        ditto_conn.close()

def main():
    parser = argparse.ArgumentParser(description='创建 PasteBar 兼容的备份文件')
    parser.add_argument('--ecopaste', help='EcoPaste 数据库路径')
    parser.add_argument('--ditto', help='Ditto 数据库路径')
    parser.add_argument('--output', required=True, help='输出备份文件路径 (.zip)')
    
    args = parser.parse_args()
    
    if not args.ecopaste and not args.ditto:
        print("错误: 必须指定至少一个源数据库 (--ecopaste 或 --ditto)")
        sys.exit(1)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "pastebar-db.data")
        
        # 创建 PasteBar 数据库
        temp_conn = create_pastebar_database(temp_db_path)
        temp_cursor = temp_conn.cursor()
        
        total_imported = 0
        total_skipped = 0
        
        try:
            # 处理 EcoPaste 数据
            if args.ecopaste and os.path.exists(args.ecopaste):
                imported, skipped = import_ecopaste_to_temp_db(args.ecopaste, temp_cursor)
                total_imported += imported
                total_skipped += skipped
            elif args.ecopaste:
                print(f"警告: EcoPaste 数据库文件不存在: {args.ecopaste}")
            
            # 处理 Ditto 数据
            if args.ditto and os.path.exists(args.ditto):
                imported, skipped = import_ditto_to_temp_db(args.ditto, temp_cursor)
                total_imported += imported
                total_skipped += skipped
            elif args.ditto:
                print(f"警告: Ditto 数据库文件不存在: {args.ditto}")
            
            # 提交数据库更改
            temp_conn.commit()
            temp_conn.close()
            
            # 创建 ZIP 备份文件
            print(f"创建备份文件: {args.output}")
            with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_db_path, "pastebar-db.data")
            
            print(f"\n🎉 备份文件创建完成!")
            print(f"文件位置: {args.output}")
            print(f"总计处理: {total_imported} 条记录")
            print(f"跳过记录: {total_skipped} 条记录")
            print("\n📋 使用方法:")
            print("1. 打开 PasteBar 应用")
            print("2. 进入 设置 > 备份和恢复")
            print("3. 点击 '从文件恢复...'")
            print(f"4. 选择文件: {args.output}")
            print("5. 确认恢复操作")
            
        except Exception as e:
            print(f"创建备份文件时发生错误: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
