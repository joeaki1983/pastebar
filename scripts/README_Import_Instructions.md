# PasteBar 数据导入说明

## 📦 已创建的备份文件

**文件位置**: `/Users/joe/Downloads/pastebar-import-backup.zip`  
**文件大小**: 20MB  
**包含数据**: 79,170 条剪贴板记录

### 数据来源统计

| 来源 | 成功导入 | 跳过记录 | 总计 |
|------|----------|----------|------|
| **EcoPaste** | 13,872 条 | 4 条 | 13,876 条 |
| **Ditto** | 65,298 条 | 151 条 | 65,449 条 |
| **总计** | **79,170 条** | **155 条** | **79,325 条** |

## 🔧 手动导入步骤

### 方法一：使用 PasteBar 内置恢复功能（推荐）

1. **打开 PasteBar 应用**

2. **进入设置页面**
   - 点击应用右上角的设置图标
   - 或使用快捷键打开设置

3. **找到备份和恢复选项**
   - 在设置页面中找到 "备份和恢复" (Backup and Restore) 选项
   - 点击进入备份恢复页面

4. **选择恢复选项**
   - 点击 "从文件恢复..." (Restore from File...) 按钮
   - 在文件选择对话框中导航到 `/Users/joe/Downloads/`
   - 选择 `pastebar-import-backup.zip` 文件

5. **确认恢复操作**
   - 系统会询问是否要在恢复前创建当前数据的备份
   - 建议选择 "是" 以保护现有数据
   - 确认恢复操作

6. **等待完成**
   - 恢复过程可能需要几分钟时间
   - 完成后应用会自动重启

7. **验证导入结果**
   - 重启后检查剪贴板历史
   - 应该能看到所有导入的记录

### 方法二：手动替换数据库文件（高级用户）

⚠️ **警告**: 此方法会完全替换现有数据，请先备份！

1. **关闭 PasteBar 应用**

2. **备份现有数据库**
   ```bash
   cp ~/Library/Application\ Support/app.anothervision.pasteBar/pastebar-db.data \
      ~/Library/Application\ Support/app.anothervision.pasteBar/pastebar-db.data.backup
   ```

3. **解压备份文件**
   ```bash
   cd ~/Downloads
   unzip pastebar-import-backup.zip
   ```

4. **替换数据库文件**
   ```bash
   cp pastebar-db.data ~/Library/Application\ Support/app.anothervision.pasteBar/
   ```

5. **重启 PasteBar 应用**

## 📊 导入的数据类型

### ✅ 完全支持的数据类型
- **纯文本内容**: 所有文本剪贴板内容
- **HTML 内容**: 富文本和网页内容  
- **RTF 内容**: 富文本格式
- **链接内容**: 自动识别的 HTTP/HTTPS 链接
- **收藏状态**: 保留原有的收藏/重要标记
- **创建时间**: 保留原始时间戳
- **来源标识**: 标记数据来源 (EcoPaste/Ditto)

### ⚠️ 部分支持的数据类型
- **图片记录**: 导入元数据（尺寸、类型），但图片文件需要单独处理
- **特殊格式**: 某些特殊剪贴板格式可能显示为文本

### ❌ 不支持的数据类型
- **文件记录**: 跳过文件类型的剪贴板内容
- **空记录**: 自动跳过空白或无效记录

## 🔍 数据映射关系

### EcoPaste → PasteBar
| EcoPaste 字段 | PasteBar 字段 | 说明 |
|---------------|---------------|------|
| `id` | `history_id` | 重新生成 UUID |
| `value` | `value` | 剪贴板内容 |
| `search` | `title` | 搜索文本作为标题 |
| `type` | `is_text/is_image/is_link` | 内容类型标志 |
| `width/height` | `image_width/image_height` | 图片尺寸 |
| `favorite` | `is_favorite` | 收藏状态 |
| `createTime` | `created_at` | 创建时间戳 |

### Ditto → PasteBar
| Ditto 字段 | PasteBar 字段 | 说明 |
|------------|---------------|------|
| `lID` | `history_id` | 重新生成 UUID |
| `mText` | `value` | 剪贴板内容 |
| `QuickPasteText` | `title` | 快速粘贴文本作为标题 |
| `lDate` | `created_at` | Unix 时间戳转换 |
| `lDontAutoDelete` | `is_favorite` | 重要标记转为收藏 |

## 🛠️ 故障排除

### 常见问题

1. **导入后看不到数据**
   - 确保完全重启了 PasteBar 应用
   - 检查剪贴板历史页面的筛选设置
   - 尝试搜索已知的剪贴板内容

2. **恢复失败**
   - 确保备份文件完整且未损坏
   - 检查 PasteBar 应用版本兼容性
   - 尝试重新下载备份文件

3. **数据不完整**
   - 检查原始数据库文件是否完整
   - 查看导入日志中的跳过记录统计
   - 某些特殊格式可能无法完全转换

### 联系支持

如果遇到问题，请提供以下信息：
- PasteBar 应用版本
- 操作系统版本
- 具体错误信息
- 导入的数据量

## 📝 注意事项

1. **数据安全**: 导入前建议备份现有 PasteBar 数据
2. **性能影响**: 大量数据可能影响应用启动速度
3. **存储空间**: 确保有足够的磁盘空间存储导入的数据
4. **时间戳**: 导入的记录会保持原始创建时间
5. **去重**: 系统会自动跳过重复的记录

---

**创建时间**: 2025-07-26  
**脚本版本**: 1.0  
**支持的格式**: EcoPaste, Ditto → PasteBar
