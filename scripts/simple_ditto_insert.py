#!/usr/bin/env python3
"""
最简单的方法：直接在成功的数据库中插入Ditto数据
"""

import sqlite3
import hashlib
import random
import string
from datetime import datetime

def generate_uuid():
    """生成与成功案例相同格式的UUID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=21))

def main():
    # 连接数据库
    pastebar_conn = sqlite3.connect('/Users/joe/Downloads/pastebar-db.data')
    ditto_conn = sqlite3.connect('/Users/joe/Downloads/Ditto.db')
    
    pastebar_cursor = pastebar_conn.cursor()
    ditto_cursor = ditto_conn.cursor()
    
    # 查询Ditto数据
    ditto_cursor.execute("""
        SELECT lID, lDate, mText, lDontAutoDelete, QuickPasteText
        FROM Main 
        WHERE bIsGroup = 0 AND lParentID = -1 AND mText IS NOT NULL AND mText != ''
        ORDER BY lDate DESC
        LIMIT 1000
    """)
    
    records = ditto_cursor.fetchall()
    print(f"找到 {len(records)} 条记录")
    
    count = 0
    for record in records:
        ditto_id, date_timestamp, text, dont_auto_delete, quick_paste_text = record
        
        if not text or text.strip() == "":
            continue
            
        # 生成数据
        history_id = generate_uuid()
        
        # 时间戳转换
        if date_timestamp < 10000000000:
            created_at = date_timestamp * 1000
        else:
            created_at = date_timestamp
            
        dt = datetime.fromtimestamp(created_at / 1000)
        created_date = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # 处理文本
        value = text
        value_preview = text[:150] if text else ""
        value_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # 标题
        title = quick_paste_text if quick_paste_text else ""
        
        # 类型检测
        is_text = 1
        is_link = 1 if 'http' in text else 0
        is_favorite = 1 if dont_auto_delete else 0
        
        # 计算更多字段
        value_more_preview_lines = max(0, text.count('\n') - 5) if text else 0
        value_more_preview_chars = max(0, len(text) - 150) if text else 0
        has_emoji = 1 if text and any(ord(char) > 127 for char in text if ord(char) > 1000) else 0
        is_code = 1 if text and any(keyword in text.lower() for keyword in ['function', 'class', 'def ', 'var ', 'const ']) else 0

        # 插入数据 - 填充所有字段
        try:
            pastebar_cursor.execute("""
                INSERT INTO clipboard_history (
                    history_id, title, value, value_preview,
                    value_more_preview_lines, value_more_preview_chars, value_hash,
                    is_image, image_path_full_res, image_data_low_res,
                    image_preview_height, image_height, image_width,
                    image_data_url, image_hash, is_image_data, is_masked,
                    is_text, is_code, is_link, is_video, has_emoji,
                    has_masked_words, is_pinned, is_favorite, links,
                    detected_language, pinned_order_number,
                    created_at, updated_at, created_date, updated_date,
                    history_options, copied_from_app
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history_id, title, value, value_preview,
                value_more_preview_lines, value_more_preview_chars, value_hash,
                0, None, None, 0, 0, 0, None, None, 0, 0,
                is_text, is_code, is_link, 0, has_emoji,
                0, 0, is_favorite, None, None, 0,
                created_at, created_at, created_date, created_date,
                None, "Ditto"
            ))
            count += 1
            if count % 100 == 0:
                print(f"已插入 {count} 条记录")
        except Exception as e:
            print(f"插入失败: {e}")
    
    pastebar_conn.commit()
    pastebar_conn.close()
    ditto_conn.close()
    
    print(f"完成！共插入 {count} 条记录")

if __name__ == "__main__":
    main()
