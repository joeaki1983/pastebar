# Ditto 数据导入 PasteBar 完整指南

## 📦 已生成的文件

我已经将您的 Ditto 数据库转换为多种格式，位于 `/Users/joe/Downloads/ditto_export/` 目录：

| 文件 | 大小 | 格式 | 用途 |
|------|------|------|------|
| `ditto_data.json` | 53MB | JSON | 结构化数据，适合程序处理 |
| `ditto_data.csv` | 23MB | CSV | 表格格式，可用 Excel 打开 |
| `ditto_data.txt` | 22MB | TXT | 纯文本格式，便于阅读 |
| `ditto_to_pastebar_backup.zip` | 11MB | ZIP | PasteBar 备份格式 |

**总记录数**: 65,298 条剪贴板记录

## 🔧 导入方法

### 方法一：使用 PasteBar 备份恢复（推荐）

**文件**: `ditto_to_pastebar_backup.zip`

1. **打开 PasteBar 应用**
2. **进入设置** → **备份和恢复**
3. **点击 "从文件恢复..."**
4. **选择文件**: `/Users/joe/Downloads/ditto_export/ditto_to_pastebar_backup.zip`
5. **确认恢复操作**
6. **等待完成并重启应用**

### 方法二：CSV 格式手动导入

**文件**: `ditto_data.csv`

1. **用 Excel 或 Numbers 打开 CSV 文件**
2. **查看和编辑数据**（可选）
3. **复制需要的内容**
4. **手动粘贴到 PasteBar**

**CSV 文件包含的列**：
- `id`: 唯一标识符
- `title`: 标题/描述
- `content`: 完整内容
- `preview`: 预览文本
- `is_text`: 是否为文本
- `is_image`: 是否为图片
- `is_link`: 是否为链接
- `is_favorite`: 是否收藏
- `created_date_readable`: 创建时间
- `source`: 数据来源 (Ditto)

### 方法三：JSON 格式程序化处理

**文件**: `ditto_data.json`

JSON 文件结构：
```json
{
  "metadata": {
    "source": "Ditto",
    "export_date": "2025-07-26T13:06:00",
    "total_records": 65298,
    "format_version": "1.0"
  },
  "clipboard_history": [
    {
      "id": "uuid",
      "title": "标题",
      "content": "完整内容",
      "preview": "预览文本",
      "is_text": true,
      "is_image": false,
      "is_link": false,
      "is_favorite": false,
      "created_date": "2023-06-21T10:33:17",
      "source": "Ditto"
    }
  ]
}
```

### 方法四：纯文本格式查看

**文件**: `ditto_data.txt`

- 便于直接阅读和查看内容
- 可以搜索特定的剪贴板记录
- 适合打印或分享

## 📊 数据统计和特性

### 数据类型分布
- **文本内容**: 大部分记录
- **链接内容**: 自动识别 HTTP/HTTPS 链接
- **图片记录**: 包含图片元数据
- **收藏记录**: 保留 Ditto 的重要标记

### 保留的信息
✅ **完全保留**:
- 原始剪贴板内容
- 创建时间戳
- 收藏/重要状态
- 快速粘贴文本（作为标题）
- 内容类型检测

⚠️ **部分保留**:
- 图片记录（仅元数据）
- 特殊格式数据

❌ **不包含**:
- 分组信息
- 使用统计
- 图片文件本身

## 🛠️ 高级使用

### 批量导入脚本

如果您需要批量导入，可以使用 JSON 格式编写自定义脚本：

```python
import json

# 读取 JSON 数据
with open('ditto_data.json', 'r') as f:
    data = json.load(f)

# 处理每条记录
for record in data['clipboard_history']:
    content = record['content']
    title = record['title']
    is_favorite = record['is_favorite']
    # 自定义处理逻辑
```

### 数据筛选

您可以根据需要筛选数据：

1. **按时间筛选**: 只导入特定时间段的记录
2. **按类型筛选**: 只导入文本或链接
3. **按收藏筛选**: 只导入收藏的记录
4. **按内容筛选**: 搜索包含特定关键词的记录

### Excel 处理技巧

使用 CSV 文件时的 Excel 技巧：

1. **筛选功能**: 使用 Excel 的筛选功能查找特定内容
2. **排序功能**: 按时间或类型排序
3. **搜索功能**: 使用 Ctrl+F 搜索特定内容
4. **导出功能**: 筛选后可以导出子集

## 🔍 故障排除

### 常见问题

1. **PasteBar 备份恢复失败**
   - 确保 PasteBar 应用已完全关闭
   - 检查备份文件是否完整
   - 尝试重新下载备份文件

2. **CSV 文件打开乱码**
   - 使用 UTF-8 编码打开
   - 在 Excel 中选择"数据" → "从文本/CSV"
   - 选择 UTF-8 编码

3. **JSON 文件过大**
   - 可以使用文本编辑器分段查看
   - 或编写脚本分批处理

4. **内容显示不完整**
   - 检查原始 Ditto 数据库
   - 某些特殊格式可能无法完全转换

### 性能建议

1. **大量数据导入**:
   - 分批导入，避免一次性导入所有数据
   - 先导入重要/收藏的记录

2. **存储空间**:
   - 确保有足够的磁盘空间
   - 导入后可以删除临时文件

3. **应用性能**:
   - 大量数据可能影响 PasteBar 启动速度
   - 考虑定期清理不需要的记录

## 📝 使用建议

### 推荐导入顺序

1. **首先尝试**: PasteBar 备份恢复（最简单）
2. **如果失败**: 使用 CSV 格式手动选择性导入
3. **特殊需求**: 使用 JSON 格式自定义处理

### 数据管理建议

1. **备份原始数据**: 保留原始 Ditto 数据库
2. **分类导入**: 可以分批导入不同类型的数据
3. **定期清理**: 导入后定期清理不需要的记录
4. **标签管理**: 在 PasteBar 中为导入的数据添加标签

---

**创建时间**: 2025-07-26  
**数据来源**: Ditto 剪贴板管理器  
**记录总数**: 65,298 条  
**支持格式**: JSON, CSV, TXT, PasteBar Backup
