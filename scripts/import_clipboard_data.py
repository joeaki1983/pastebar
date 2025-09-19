#!/usr/bin/env python3
"""
剪贴板管理器数据导入 PasteBar 统一脚本

支持导入:
- EcoPaste 数据库
- Ditto 数据库

使用方法:
python3 import_clipboard_data.py --ecopaste /path/to/EcoPaste.db --pastebar /path/to/pastebar.db
python3 import_clipboard_data.py --ditto /path/to/Ditto.db --pastebar /path/to/pastebar.db
python3 import_clipboard_data.py --ecopaste /path/to/EcoPaste.db --ditto /path/to/Ditto.db --pastebar /path/to/pastebar.db
"""

import sqlite3
import sys
import os
import hashlib
import time
import argparse
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

def import_ecopaste_data(ecopaste_db_path, paste_cursor):
    """导入 EcoPaste 数据"""
    print("开始导入 EcoPaste 数据...")
    
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
                'updated_date': datetime.fromtimestamp(created_timestamp / 1000)
            }
            
            try:
                paste_cursor.execute("""
                    INSERT INTO clipboard_history (
                        history_id, title, value, value_preview, value_hash,
                        is_image, image_width, image_height, is_text, is_link,
                        is_favorite, created_at, updated_at, created_date, updated_date
                    ) VALUES (
                        :history_id, :title, :value, :value_preview, :value_hash,
                        :is_image, :image_width, :image_height, :is_text, :is_link,
                        :is_favorite, :created_at, :updated_at, :created_date, :updated_date
                    )
                """, insert_data)
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"EcoPaste: 已导入 {imported_count} 条记录...")
                    
            except sqlite3.IntegrityError:
                skipped_count += 1
            except Exception as e:
                print(f"EcoPaste 导入记录失败 {eco_id}: {e}")
                skipped_count += 1
        
        print(f"EcoPaste 导入完成: 成功 {imported_count} 条, 跳过 {skipped_count} 条")
        return imported_count, skipped_count
        
    finally:
        eco_conn.close()

def import_ditto_data(ditto_db_path, paste_cursor):
    """导入 Ditto 数据"""
    print("开始导入 Ditto 数据...")
    
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
                'updated_date': datetime.fromtimestamp(created_timestamp / 1000)
            }
            
            try:
                paste_cursor.execute("""
                    INSERT INTO clipboard_history (
                        history_id, title, value, value_preview, value_hash,
                        is_image, image_width, image_height, is_text, is_link,
                        is_favorite, created_at, updated_at, created_date, updated_date
                    ) VALUES (
                        :history_id, :title, :value, :value_preview, :value_hash,
                        :is_image, :image_width, :image_height, :is_text, :is_link,
                        :is_favorite, :created_at, :updated_at, :created_date, :updated_date
                    )
                """, insert_data)
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"Ditto: 已导入 {imported_count} 条记录...")
                    
            except sqlite3.IntegrityError:
                skipped_count += 1
            except Exception as e:
                print(f"Ditto 导入记录失败 {ditto_id}: {e}")
                skipped_count += 1
        
        print(f"Ditto 导入完成: 成功 {imported_count} 条, 跳过 {skipped_count} 条")
        return imported_count, skipped_count
        
    finally:
        ditto_conn.close()

def main():
    parser = argparse.ArgumentParser(description='导入剪贴板管理器数据到 PasteBar')
    parser.add_argument('--ecopaste', help='EcoPaste 数据库路径')
    parser.add_argument('--ditto', help='Ditto 数据库路径')
    parser.add_argument('--pastebar', required=True, help='PasteBar 数据库路径')
    
    args = parser.parse_args()
    
    if not args.ecopaste and not args.ditto:
        print("错误: 必须指定至少一个源数据库 (--ecopaste 或 --ditto)")
        sys.exit(1)
    
    if not os.path.exists(args.pastebar):
        print(f"错误: PasteBar 数据库文件不存在: {args.pastebar}")
        sys.exit(1)
    
    # 连接 PasteBar 数据库
    paste_conn = sqlite3.connect(args.pastebar)
    paste_cursor = paste_conn.cursor()
    
    total_imported = 0
    total_skipped = 0
    
    try:
        # 导入 EcoPaste 数据
        if args.ecopaste:
            if os.path.exists(args.ecopaste):
                imported, skipped = import_ecopaste_data(args.ecopaste, paste_cursor)
                total_imported += imported
                total_skipped += skipped
            else:
                print(f"警告: EcoPaste 数据库文件不存在: {args.ecopaste}")
        
        # 导入 Ditto 数据
        if args.ditto:
            if os.path.exists(args.ditto):
                imported, skipped = import_ditto_data(args.ditto, paste_cursor)
                total_imported += imported
                total_skipped += skipped
            else:
                print(f"警告: Ditto 数据库文件不存在: {args.ditto}")
        
        # 提交事务
        paste_conn.commit()
        
        print(f"\n🎉 所有数据导入完成!")
        print(f"总计成功导入: {total_imported} 条记录")
        print(f"总计跳过: {total_skipped} 条记录")
        print("请重启 PasteBar 应用以查看导入的数据。")
        
    except Exception as e:
        print(f"导入过程中发生错误: {e}")
        paste_conn.rollback()
        sys.exit(1)
        
    finally:
        paste_conn.close()

if __name__ == "__main__":
    main()
