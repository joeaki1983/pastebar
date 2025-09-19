# PasteBar macOS 辅助功能权限问题解决方案

## 问题描述

即使在系统设置中重新添加了 PasteBar 的辅助功能权限，应用仍然会弹出权限请求窗口。

## 问题原因

1. **Bundle Identifier 变化**：应用的 bundle identifier 发生变化时，macOS 会将其视为新应用
2. **代码签名变化**：应用的代码签名发生变化时，系统要求重新授权
3. **权限缓存问题**：macOS 的辅助功能权限缓存可能存在问题
4. **权限检查逻辑**：应用启动时立即调用 `application_is_trusted_with_prompt()` 会弹出系统对话框

## 解决方案

### 方案1：使用安全权限重置脚本（推荐）

运行安全版本的脚本，只影响 PasteBar：

```bash
./scripts/reset-pastebar-permissions-safe.sh
```

这个脚本会：
- **只清理 PasteBar 的权限记录**
- **不影响其他应用的权限**
- 显示当前权限状态
- 提供确认提示

⚠️ **注意**：还有一个 `reset-accessibility-permissions.sh` 脚本，但它可能影响所有应用的权限，不推荐使用。

### 方案2：手动清理权限

1. **退出 PasteBar 应用**

2. **打开终端，运行以下命令**：
   ```bash
   # 清理系统级 TCC 数据库
   sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db "DELETE FROM access WHERE client='app.anothervision.pasteBar' AND service='kTCCServiceAccessibility';"
   
   # 清理用户级 TCC 数据库
   sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "DELETE FROM access WHERE client='app.anothervision.pasteBar' AND service='kTCCServiceAccessibility';"
   ```

3. **重启 macOS**（可选，但推荐）

4. **重新启动 PasteBar**

### 方案3：通过系统设置手动重置

1. 打开 **系统设置** > **隐私与安全性** > **辅助功能**
2. 如果看到 PasteBar 在列表中，将其移除
3. 重启 PasteBar 应用
4. 当提示权限时，点击"授予权限"按钮

## 代码改进

我们已经对代码进行了以下改进：

### 1. 修改启动时权限检查逻辑

```rust
// 之前：启动时就弹出系统对话框
is_permissions_trusted = macos_accessibility_client::accessibility::application_is_trusted_with_prompt();

// 现在：启动时只检查状态，不弹出对话框
is_permissions_trusted = macos_accessibility_client::accessibility::application_is_trusted();
```

### 2. 添加新的权限请求命令

```rust
#[tauri::command]
fn request_osx_accessibility_permissions() -> bool {
  #[cfg(target_os = "macos")]
  {
    macos_accessibility_client::accessibility::application_is_trusted_with_prompt()
  }
  // ...
}
```

### 3. 改进前端权限按钮逻辑

权限模态框中的"授予权限"按钮现在会：
1. 首先尝试请求权限
2. 如果失败，则打开系统设置页面

## 脚本安全性说明

### 安全脚本 vs 危险脚本

| 脚本 | 安全性 | 影响范围 | 推荐度 |
|------|--------|----------|--------|
| `reset-pastebar-permissions-safe.sh` | ✅ 安全 | 仅 PasteBar | ⭐⭐⭐⭐⭐ |
| `reset-accessibility-permissions.sh` | ⚠️ 危险 | 所有应用 | ❌ 不推荐 |

**安全脚本特点**：
- 只删除 PasteBar 的 TCC 记录
- 不清理全局辅助功能缓存
- 不影响其他应用的权限
- 提供详细的权限状态显示
- 需要用户确认才执行

## 预防措施

为了避免将来出现类似问题：

1. **保持 Bundle Identifier 稳定**：不要随意更改 `tauri.conf.json` 中的 `identifier`
2. **代码签名一致性**：确保发布版本使用一致的代码签名
3. **渐进式权限请求**：只在用户需要使用相关功能时才请求权限

## 调试信息

如果问题仍然存在，可以：

1. **查看控制台日志**：
   ```bash
   log show --predicate 'subsystem == "com.apple.TCC"' --last 1h
   ```

2. **检查 TCC 数据库**：
   ```bash
   sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db "SELECT * FROM access WHERE client='app.anothervision.pasteBar';"
   ```

3. **启用调试模式**：在开发模式下运行应用，查看详细的权限检查日志

## 联系支持

如果以上方案都无法解决问题，请：
1. 收集系统信息（macOS 版本、PasteBar 版本）
2. 提供控制台日志
3. 描述具体的重现步骤

---

**注意**：某些操作需要管理员权限，请确保您有足够的系统权限来执行这些命令。
