# PasteBar 日志系统说明

## 功能概述

PasteBar 现在具有完整的日志系统，可以记录应用运行时的所有重要事件和错误信息。

## 日志功能特性

### 1. **结构化日志系统**
- **日志级别**: Debug, Info, Warn, Error, Fatal
- **时间戳**: 每条日志都包含精确到毫秒的时间戳
- **上下文信息**: 支持添加上下文标签

### 2. **日志文件位置**
- **主日志文件**: `{数据目录}/logs/pastebar_YYYYMMDD.log`
- **崩溃日志**: `pastebar-panic.log`（应用根目录）
- 日志文件按日期命名，每天自动创建新文件
- 自动清理7天前的旧日志文件

### 3. **崩溃捕获**
- 所有 panic 都会被捕获并记录
- 包含崩溃位置（文件、行号、列号）
- 崩溃信息同时保存到：
  - 主日志文件
  - 独立的 `pastebar-panic.log` 文件

### 4. **错误追踪**
- 所有锁竞争失败都会记录
- QuickPaste 窗口事件都会记录
- 系统菜单构建错误会记录

## 已修复的问题

### 1. **锁竞争导致的崩溃**
- 替换所有 `lock().unwrap()` 为 `try_lock()`
- 失败时提供默认值，避免程序崩溃
- 所有锁错误都会记录到日志

### 2. **改进的错误处理**
- 窗口状态保存失败不会导致崩溃
- 设置读取失败使用默认值
- 所有错误都有详细的日志记录

## API 接口

### Rust 端日志记录
```rust
// 使用日志级别记录
logger::log(logger::LogLevel::Info, "消息");
logger::log(logger::LogLevel::Error, "错误消息");

// 带上下文的日志
logger::log_with_context(logger::LogLevel::Debug, "消息", Some("模块名"));

// 错误记录助手
logger::log_error("操作名称", error);
```

### Tauri 命令（前端可调用）
```typescript
// 获取日志内容
invoke('get_logs', { lines: 100 }); // 获取最后100行

// 获取日志文件路径
invoke('get_log_path');

// 清空日志
invoke('clear_logs');

// 获取崩溃日志
invoke('get_panic_logs');
```

## 日志示例

```
[2025-01-09 14:23:45.123] [INFO] PasteBar starting up...
[2025-01-09 14:23:45.456] [DEBUG] [QuickPaste] Opening quickpaste window
[2025-01-09 14:23:46.789] [ERROR] Failed to lock QuickPasteState: mutex already locked
[2025-01-09 14:23:47.012] [WARN] Failed to emit quickpaste window opened event: window not found
[2025-01-09 14:23:48.345] [FATAL] [PANIC] PANIC: attempt to divide by zero at src/main.rs:123:45
```

## 调试建议

1. **查看日志文件**
   - macOS: `~/Library/Application Support/app.anothervision.pasteBar/logs/`
   - Windows: `%APPDATA%/app.anothervision.pasteBar/logs/`
   - Linux: `~/.config/app.anothervision.pasteBar/logs/`

2. **实时监控日志**
   ```bash
   tail -f ~/Library/Application\ Support/app.anothervision.pasteBar/logs/pastebar_*.log
   ```

3. **检查崩溃日志**
   - 查看应用目录下的 `pastebar-panic.log` 文件

## 性能影响

- Debug 模式：所有日志都输出到控制台和文件
- Release 模式：只有 Error 和 Fatal 级别输出到控制台，所有级别都记录到文件
- 日志写入使用缓冲，对性能影响极小

## 未来改进建议

1. 添加日志轮转（按大小）
2. 支持远程日志上传（用于错误报告）
3. 添加日志查看器 UI 界面
4. 支持日志级别动态配置