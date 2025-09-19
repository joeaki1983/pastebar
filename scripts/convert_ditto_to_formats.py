#!/usr/bin/env python3
"""
Ditto 数据转换为多种格式脚本

将 Ditto 数据库转换为多种可导入格式:
- JSON 格式 (结构化数据)
- CSV 格式 (表格数据)
- TXT 格式 (纯文本列表)
- PasteBar 备份格式 (ZIP)

使用方法:
python3 convert_ditto_to_formats.py /path/to/Ditto.db /path/to/output_directory
"""

import sqlite3
import sys
import os
import json
import csv
import hashlib
import time
import zipfile
import tempfile
from datetime import datetime
import uuid

def generate_uuid():
    """生成唯一ID"""
    return str(uuid.uuid4())

def parse_ditto_time(timestamp):
    """解析 Ditto 时间戳"""
    try:
        return int(timestamp * 1000)
    except:
        return int(time.time() * 1000)

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

def extract_ditto_data(ditto_db_path):
    """从 Ditto 数据库提取数据"""
    print("正在读取 Ditto 数据库...")
    
    ditto_conn = sqlite3.connect(ditto_db_path)
    ditto_cursor = ditto_conn.cursor()
    
    try:
        # 查询主表记录
        ditto_cursor.execute("""
            SELECT lID, lDate, mText, lDontAutoDelete, bIsGroup, lParentID, 
                   QuickPasteText, lastPasteDate
            FROM Main 
            WHERE bIsGroup = 0 AND lParentID = -1
            ORDER BY lDate DESC
        """)
        
        ditto_records = ditto_cursor.fetchall()
        print(f"找到 {len(ditto_records)} 条 Ditto 记录")
        
        processed_data = []
        skipped_count = 0
        
        for record in ditto_records:
            ditto_id, date_timestamp, text, dont_auto_delete, is_group, parent_id, quick_paste_text, last_paste_date = record
            
            # 跳过空记录
            if not text or text.strip() == "":
                skipped_count += 1
                continue
            
            # 获取数据格式
            ditto_cursor.execute("""
                SELECT strClipBoardFormat FROM Data WHERE lParentID = ?
            """, (ditto_id,))
            
            data_formats = [row[0] for row in ditto_cursor.fetchall()]
            
            # 检测内容类型
            is_text, is_image, is_link = detect_content_type(text, data_formats)
            
            # 生成处理后的数据
            created_timestamp = parse_ditto_time(date_timestamp)
            created_date = datetime.fromtimestamp(created_timestamp / 1000)
            
            processed_record = {
                'id': generate_uuid(),
                'original_id': ditto_id,
                'title': quick_paste_text if quick_paste_text else get_preview_text(text),
                'content': text,
                'preview': get_preview_text(text),
                'content_hash': calculate_hash(text),
                'is_text': is_text,
                'is_image': is_image,
                'is_link': is_link,
                'is_favorite': bool(dont_auto_delete),
                'data_formats': data_formats,
                'created_timestamp': created_timestamp,
                'created_date': created_date.isoformat(),
                'created_date_readable': created_date.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Ditto'
            }
            
            processed_data.append(processed_record)
        
        print(f"成功处理 {len(processed_data)} 条记录，跳过 {skipped_count} 条空记录")
        return processed_data
        
    finally:
        ditto_conn.close()

def export_to_json(data, output_path):
    """导出为 JSON 格式"""
    json_file = os.path.join(output_path, "ditto_data.json")
    
    export_data = {
        'metadata': {
            'source': 'Ditto',
            'export_date': datetime.now().isoformat(),
            'total_records': len(data),
            'format_version': '1.0'
        },
        'clipboard_history': data
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON 格式导出完成: {json_file}")
    return json_file

def export_to_csv(data, output_path):
    """导出为 CSV 格式"""
    csv_file = os.path.join(output_path, "ditto_data.csv")
    
    fieldnames = [
        'id', 'title', 'content', 'preview', 'is_text', 'is_image', 'is_link', 
        'is_favorite', 'created_date_readable', 'created_timestamp', 'source'
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # 只写入需要的字段
            csv_record = {field: record.get(field, '') for field in fieldnames}
            writer.writerow(csv_record)
    
    print(f"✅ CSV 格式导出完成: {csv_file}")
    return csv_file

def export_to_txt(data, output_path):
    """导出为纯文本格式"""
    txt_file = os.path.join(output_path, "ditto_data.txt")
    
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("Ditto 剪贴板历史数据\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总记录数: {len(data)}\n\n")
        
        for i, record in enumerate(data, 1):
            f.write(f"记录 #{i}\n")
            f.write("-" * 30 + "\n")
            f.write(f"ID: {record['id']}\n")
            f.write(f"标题: {record['title'] or '(无标题)'}\n")
            f.write(f"类型: {'文本' if record['is_text'] else '图片' if record['is_image'] else '其他'}\n")
            f.write(f"收藏: {'是' if record['is_favorite'] else '否'}\n")
            f.write(f"创建时间: {record['created_date_readable']}\n")
            f.write(f"内容:\n{record['content']}\n\n")
    
    print(f"✅ TXT 格式导出完成: {txt_file}")
    return txt_file

def create_pastebar_backup(data, output_path):
    """创建 PasteBar 兼容的备份文件"""
    backup_file = os.path.join(output_path, "ditto_to_pastebar_backup.zip")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "pastebar-db.data")
        
        # 创建数据库
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 创建表结构（简化版）
        cursor.execute("""
            CREATE TABLE clipboard_history (
                history_id VARCHAR(50) PRIMARY KEY NOT NULL,
                title VARCHAR(255),
                value TEXT,
                value_preview VARCHAR(150),
                value_hash VARCHAR(255),
                is_image BOOLEAN DEFAULT FALSE,
                is_text BOOLEAN DEFAULT FALSE,
                is_link BOOLEAN DEFAULT FALSE,
                is_favorite BOOLEAN DEFAULT FALSE,
                created_at BIGINT NOT NULL,
                updated_at BIGINT NOT NULL,
                created_date TIMESTAMP NOT NULL,
                updated_date TIMESTAMP NOT NULL,
                copied_from_app VARCHAR(255)
            )
        """)
        
        # 插入数据
        for record in data:
            cursor.execute("""
                INSERT INTO clipboard_history (
                    history_id, title, value, value_preview, value_hash,
                    is_image, is_text, is_link, is_favorite,
                    created_at, updated_at, created_date, updated_date, copied_from_app
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['id'],
                record['title'],
                record['content'],
                record['preview'],
                record['content_hash'],
                record['is_image'],
                record['is_text'],
                record['is_link'],
                record['is_favorite'],
                record['created_timestamp'],
                record['created_timestamp'],
                record['created_date'],
                record['created_date'],
                'Ditto'
            ))
        
        conn.commit()
        conn.close()
        
        # 创建 ZIP 文件
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(temp_db_path, "pastebar-db.data")
    
    print(f"✅ PasteBar 备份文件创建完成: {backup_file}")
    return backup_file

def main():
    if len(sys.argv) != 3:
        print("使用方法: python3 convert_ditto_to_formats.py <Ditto.db路径> <输出目录>")
        print("示例: python3 convert_ditto_to_formats.py ~/Downloads/Ditto.db ~/Downloads/ditto_export")
        sys.exit(1)
    
    ditto_db_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(ditto_db_path):
        print(f"错误: Ditto 数据库文件不存在: {ditto_db_path}")
        sys.exit(1)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始转换 Ditto 数据...")
    print(f"源文件: {ditto_db_path}")
    print(f"输出目录: {output_dir}")
    print()
    
    # 提取数据
    data = extract_ditto_data(ditto_db_path)
    
    if not data:
        print("没有找到可转换的数据")
        sys.exit(1)
    
    # 导出为各种格式
    print("\n开始导出为多种格式...")
    
    json_file = export_to_json(data, output_dir)
    csv_file = export_to_csv(data, output_dir)
    txt_file = export_to_txt(data, output_dir)
    backup_file = create_pastebar_backup(data, output_dir)
    
    print(f"\n🎉 转换完成!")
    print(f"共处理 {len(data)} 条记录")
    print(f"\n📁 生成的文件:")
    print(f"  📄 JSON 格式: {json_file}")
    print(f"  📊 CSV 格式: {csv_file}")
    print(f"  📝 TXT 格式: {txt_file}")
    print(f"  📦 PasteBar 备份: {backup_file}")
    
    print(f"\n💡 使用建议:")
    print(f"  • JSON 格式: 适合程序化处理和数据分析")
    print(f"  • CSV 格式: 可用 Excel 或其他表格软件打开")
    print(f"  • TXT 格式: 纯文本查看，便于阅读")
    print(f"  • PasteBar 备份: 可直接在 PasteBar 中恢复")

if __name__ == "__main__":
    main()
