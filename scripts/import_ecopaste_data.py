#!/usr/bin/env python3
"""
EcoPaste 数据导入 PasteBar 脚本

使用方法:
1. 解压 EcoPaste 备份文件
2. 运行此脚本导入数据到 PasteBar

python3 import_ecopaste_data.py /path/to/EcoPaste.db /path/to/pastebar.db
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

def parse_ecopaste_time(time_str):
    """解析 EcoPaste 时间格式"""
    try:
        # EcoPaste 时间格式: "2025-04-30 15:00:17"
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return int(dt.timestamp() * 1000)  # 转换为毫秒时间戳
    except:
        return int(time.time() * 1000)  # 如果解析失败，使用当前时间

def calculate_hash(content):
    """计算内容哈希"""
    if not content:
        return None
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def detect_content_type(eco_type, value):
    """根据 EcoPaste 类型检测内容类型"""
    type_mapping = {
        'text': {'is_text': True, 'is_image': False, 'is_link': False},
        'html': {'is_text': True, 'is_image': False, 'is_link': True},
        'image': {'is_text': False, 'is_image': True, 'is_link': False},
        'files': {'is_text': True, 'is_image': False, 'is_link': False},
        'rtf': {'is_text': True, 'is_image': False, 'is_link': False}
    }
    
    return type_mapping.get(eco_type, {'is_text': True, 'is_image': False, 'is_link': False})

def import_ecopaste_to_pastebar(ecopaste_db_path, pastebar_db_path):
    """导入 EcoPaste 数据到 PasteBar"""
    
    if not os.path.exists(ecopaste_db_path):
        print(f"错误: EcoPaste 数据库文件不存在: {ecopaste_db_path}")
        return False
    
    if not os.path.exists(pastebar_db_path):
        print(f"错误: PasteBar 数据库文件不存在: {pastebar_db_path}")
        return False
    
    # 连接数据库
    eco_conn = sqlite3.connect(ecopaste_db_path)
    paste_conn = sqlite3.connect(pastebar_db_path)
    
    try:
        eco_cursor = eco_conn.cursor()
        paste_cursor = paste_conn.cursor()
        
        # 查询 EcoPaste 历史记录
        eco_cursor.execute("""
            SELECT id, type, value, search, count, width, height, 
                   favorite, createTime, note, subtype
            FROM history 
            ORDER BY createTime DESC
        """)
        
        records = eco_cursor.fetchall()
        print(f"找到 {len(records)} 条 EcoPaste 记录")
        
        imported_count = 0
        skipped_count = 0
        
        for record in records:
            (eco_id, eco_type, value, search, count, width, height, 
             favorite, create_time, note, subtype) = record
            
            # 跳过空内容
            if not value or value.strip() == '':
                skipped_count += 1
                continue
            
            # 跳过文件类型（暂不支持）
            if eco_type == 'files':
                skipped_count += 1
                continue
            
            # 生成新的 history_id
            history_id = generate_uuid()
            
            # 解析时间
            created_at = parse_ecopaste_time(create_time)
            updated_at = created_at
            
            # 创建时间对象
            created_date = datetime.fromtimestamp(created_at / 1000)
            updated_date = created_date
            
            # 检测内容类型
            content_types = detect_content_type(eco_type, value)
            
            # 计算哈希
            value_hash = calculate_hash(value)
            
            # 生成预览文本
            value_preview = value[:150] if value else None
            
            # 准备插入数据
            insert_data = {
                'history_id': history_id,
                'title': search[:255] if search else None,  # 使用搜索文本作为标题
                'value': value,
                'value_preview': value_preview,
                'value_hash': value_hash,
                'is_image': content_types['is_image'],
                'image_width': width if eco_type == 'image' else None,
                'image_height': height if eco_type == 'image' else None,
                'is_text': content_types['is_text'],
                'is_link': content_types['is_link'],
                'is_favorite': bool(favorite) if favorite else False,
                'created_at': created_at,
                'updated_at': updated_at,
                'created_date': created_date.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': updated_date.strftime('%Y-%m-%d %H:%M:%S'),
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
                print(f"跳过重复记录: {eco_id}")
                skipped_count += 1
            except Exception as e:
                print(f"导入记录失败 {eco_id}: {e}")
                skipped_count += 1
        
        # 提交事务
        paste_conn.commit()
        
        print(f"\n导入完成!")
        print(f"成功导入: {imported_count} 条记录")
        print(f"跳过记录: {skipped_count} 条记录")
        print(f"总计处理: {len(records)} 条记录")
        
        return True
        
    except Exception as e:
        print(f"导入过程中发生错误: {e}")
        paste_conn.rollback()
        return False
        
    finally:
        eco_conn.close()
        paste_conn.close()

def main():
    if len(sys.argv) != 3:
        print("使用方法: python3 import_ecopaste_data.py <EcoPaste.db路径> <PasteBar.db路径>")
        print("示例: python3 import_ecopaste_data.py ~/Downloads/EcoPaste.db ~/Library/Application\\ Support/app.anothervision.pasteBar/pastebar.db")
        sys.exit(1)
    
    ecopaste_db = sys.argv[1]
    pastebar_db = sys.argv[2]
    
    print("开始导入 EcoPaste 数据到 PasteBar...")
    print(f"源数据库: {ecopaste_db}")
    print(f"目标数据库: {pastebar_db}")
    
    success = import_ecopaste_to_pastebar(ecopaste_db, pastebar_db)
    
    if success:
        print("\n✅ 数据导入成功!")
        print("请重启 PasteBar 应用以查看导入的数据。")
    else:
        print("\n❌ 数据导入失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
