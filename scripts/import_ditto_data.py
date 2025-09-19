#!/usr/bin/env python3
"""
Ditto 数据导入 PasteBar 脚本

使用方法:
python3 import_ditto_data.py /path/to/Ditto.db /path/to/pastebar.db

Ditto 数据库结构:
- Main 表: 主要的剪贴板条目
- Data 表: 存储不同格式的剪贴板数据
- Types 表: 数据类型定义
"""

import sqlite3
import sys
import os
import hashlib
import time
from datetime import datetime
import uuid
import json

def generate_uuid():
    """生成唯一ID"""
    return str(uuid.uuid4())

def parse_ditto_time(timestamp):
    """解析 Ditto 时间戳 (Unix timestamp)"""
    try:
        return int(timestamp * 1000)  # 转换为毫秒时间戳
    except:
        return int(time.time() * 1000)  # 如果解析失败，使用当前时间

def calculate_hash(content):
    """计算内容哈希"""
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def detect_content_type(text, data_formats):
    """检测内容类型"""
    is_text = True
    is_image = False
    is_link = False
    
    # 检查是否是图片格式
    if any(fmt in ['CF_DIB', 'CF_BITMAP', 'PNG', 'JPEG'] for fmt in data_formats):
        is_image = True
        is_text = False
    
    # 检查是否是链接
    if text and (text.startswith('http://') or text.startswith('https://') or text.startswith('ftp://')):
        is_link = True
    
    return is_text, is_image, is_link

def get_preview_text(text, max_length=150):
    """生成预览文本"""
    if not text:
        return None
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def import_ditto_to_pastebar(ditto_db_path, pastebar_db_path):
    """导入 Ditto 数据到 PasteBar"""
    
    if not os.path.exists(ditto_db_path):
        print(f"错误: Ditto 数据库文件不存在: {ditto_db_path}")
        return False
    
    if not os.path.exists(pastebar_db_path):
        print(f"错误: PasteBar 数据库文件不存在: {pastebar_db_path}")
        return False
    
    # 连接数据库
    ditto_conn = sqlite3.connect(ditto_db_path)
    paste_conn = sqlite3.connect(pastebar_db_path)
    
    try:
        ditto_cursor = ditto_conn.cursor()
        paste_cursor = paste_conn.cursor()
        
        # 查询 Ditto 主表记录 (排除分组)
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
            
            # 跳过空记录
            if not text or text.strip() == "":
                skipped_count += 1
                continue
            
            # 获取该记录的所有数据格式
            ditto_cursor.execute("""
                SELECT strClipBoardFormat, ooData 
                FROM Data 
                WHERE lParentID = ?
            """, (ditto_id,))
            
            data_formats = []
            for format_record in ditto_cursor.fetchall():
                format_name, data_blob = format_record
                data_formats.append(format_name)
            
            # 检测内容类型
            is_text, is_image, is_link = detect_content_type(text, data_formats)
            
            # 生成 PasteBar 记录
            history_id = generate_uuid()
            created_timestamp = parse_ditto_time(date_timestamp)
            value_hash = calculate_hash(text)
            value_preview = get_preview_text(text)
            
            # 使用 QuickPasteText 作为标题，如果没有则使用预览文本
            title = quick_paste_text if quick_paste_text else value_preview
            
            # 是否收藏 (Ditto 的 lDontAutoDelete 可以理解为重要/收藏)
            is_favorite = bool(dont_auto_delete)
            
            # 创建插入数据
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
                'is_favorite': is_favorite,
                'created_at': created_timestamp,
                'updated_at': created_timestamp,
                'created_date': datetime.fromtimestamp(created_timestamp / 1000),
                'updated_date': datetime.fromtimestamp(created_timestamp / 1000)
            }
            
            # 插入到 PasteBar 数据库
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
                    print(f"已导入 {imported_count} 条记录...")
                    
            except sqlite3.IntegrityError as e:
                print(f"跳过重复记录: {ditto_id}")
                skipped_count += 1
            except Exception as e:
                print(f"导入记录失败 {ditto_id}: {e}")
                skipped_count += 1
        
        # 提交事务
        paste_conn.commit()
        
        print(f"\n导入完成!")
        print(f"成功导入: {imported_count} 条记录")
        print(f"跳过记录: {skipped_count} 条记录")
        
        return True
        
    except Exception as e:
        print(f"导入过程中发生错误: {e}")
        paste_conn.rollback()
        return False
        
    finally:
        ditto_conn.close()
        paste_conn.close()

def main():
    if len(sys.argv) != 3:
        print("使用方法: python3 import_ditto_data.py <Ditto.db路径> <PasteBar.db路径>")
        print("示例: python3 import_ditto_data.py ~/Downloads/Ditto.db ~/Library/Application\\ Support/app.anothervision.pasteBar/pastebar-db.data")
        sys.exit(1)
    
    ditto_db = sys.argv[1]
    pastebar_db = sys.argv[2]
    
    print("开始导入 Ditto 数据到 PasteBar...")
    print(f"源数据库: {ditto_db}")
    print(f"目标数据库: {pastebar_db}")
    
    success = import_ditto_to_pastebar(ditto_db, pastebar_db)
    
    if success:
        print("\n✅ 数据导入成功!")
        print("请重启 PasteBar 应用以查看导入的数据。")
    else:
        print("\n❌ 数据导入失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
