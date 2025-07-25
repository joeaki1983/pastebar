# EcoPaste 数据导入 PasteBar 指南

## 概述

这个脚本可以将 EcoPaste 的剪贴板历史数据导入到 PasteBar 中，让你无缝迁移数据。

## EcoPaste 备份文件格式

你的 `2025_07_26_07_19_20.EcoPaste-backup` 文件是一个完整的 EcoPaste 备份，包含：

- **格式**: gzip 压缩的 tar 归档文件
- **配置文件**: `.store-backup.json` (应用设置)
- **数据库**: `EcoPaste.db` (13,876 条剪贴板记录)
- **图片文件**: `images/` 目录中的 PNG 文件

### 数据统计
- 文本记录: 11,566 条
- 文件记录: 1,705 条
- HTML 记录: 369 条
- 图片记录: 195 条
- RTF 记录: 41 条

## 支持的数据类型

### ✅ 完全支持
- **文本内容**: 纯文本剪贴板内容
- **HTML 内容**: 富文本和网页内容
- **RTF 内容**: 富文本格式
- **收藏状态**: 收藏的剪贴板项目
- **创建时间**: 原始时间戳
- **使用统计**: 复制次数（转换为标题）

### ⚠️ 部分支持
- **图片记录**: 导入元数据（尺寸、类型），但图片文件需要手动处理
- **文件记录**: 暂时跳过，因为 PasteBar 的文件处理方式不同

### ❌ 不支持
- **备注信息**: PasteBar 没有对应的备注字段
- **分组信息**: PasteBar 使用不同的组织方式

## 使用步骤

### 1. 解压备份文件

```bash
cd ~/Downloads
gunzip -c 2025_07_26_07_19_20.EcoPaste-backup | tar -xf -
```

这会提取出：
- `EcoPaste.db` - 数据库文件
- `.store-backup.json` - 配置文件
- `images/` - 图片文件目录

### 2. 找到 PasteBar 数据库

PasteBar 数据库通常位于：
```bash
~/Library/Application Support/app.anothervision.pasteBar/pastebar.db
```

### 3. 备份 PasteBar 数据库（重要！）

```bash
cp "~/Library/Application Support/app.anothervision.pasteBar/pastebar.db" \
   "~/Library/Application Support/app.anothervision.pasteBar/pastebar.db.backup"
```

### 4. 运行导入脚本

```bash
cd /Users/joe/pastebar/PasteBarApp
python3 scripts/import_ecopaste_data.py \
    ~/Downloads/EcoPaste.db \
    "~/Library/Application Support/app.anothervision.pasteBar/pastebar.db"
```

### 5. 重启 PasteBar

导入完成后，重启 PasteBar 应用以查看导入的数据。

## 数据映射关系

| EcoPaste 字段 | PasteBar 字段 | 说明 |
|---------------|---------------|------|
| `id` | `history_id` | 重新生成 UUID |
| `value` | `value` | 剪贴板内容 |
| `search` | `title` | 搜索文本作为标题 |
| `type` | `is_text/is_image/is_link` | 内容类型标志 |
| `width/height` | `image_width/image_height` | 图片尺寸 |
| `favorite` | `is_favorite` | 收藏状态 |
| `createTime` | `created_at` | 创建时间戳 |
| `count` | - | 使用次数（暂不支持） |
| `note` | - | 备注（暂不支持） |

## 注意事项

1. **数据安全**: 导入前请务必备份 PasteBar 数据库
2. **图片文件**: 图片记录会导入元数据，但图片文件本身需要手动处理
3. **重复数据**: 脚本会自动跳过重复的记录
4. **性能**: 13,876 条记录的导入可能需要几分钟时间
5. **兼容性**: 确保 PasteBar 版本支持所有必要的数据库字段

## 故障排除

### 常见错误

1. **数据库文件不存在**
   - 检查文件路径是否正确
   - 确保已正确解压备份文件

2. **权限错误**
   - 确保对数据库文件有读写权限
   - 可能需要关闭 PasteBar 应用

3. **导入失败**
   - 检查 PasteBar 数据库结构是否匹配
   - 查看错误日志了解具体问题

### 验证导入结果

导入完成后，可以在 PasteBar 中：
1. 检查历史记录数量是否增加
2. 验证收藏的项目是否正确导入
3. 确认时间戳是否保持原始顺序

## 高级选项

如果需要自定义导入行为，可以修改脚本中的以下部分：
- 数据类型映射逻辑
- 时间格式解析
- 内容过滤条件
- 字段映射关系

## 支持

如果遇到问题，请检查：
1. Python 版本（建议 3.7+）
2. SQLite 版本兼容性
3. 数据库文件完整性
4. 系统权限设置
