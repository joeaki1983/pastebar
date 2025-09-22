use crate::logger;
use std::fs;
use std::path::PathBuf;

#[tauri::command]
pub fn get_logs(lines: Option<usize>) -> Result<String, String> {
    if let Some(log_path) = logger::get_log_path() {
        match fs::read_to_string(&log_path) {
            Ok(content) => {
                if let Some(line_count) = lines {
                    // Return last N lines
                    let all_lines: Vec<&str> = content.lines().collect();
                    let start = if all_lines.len() > line_count {
                        all_lines.len() - line_count
                    } else {
                        0
                    };
                    Ok(all_lines[start..].join("\n"))
                } else {
                    Ok(content)
                }
            }
            Err(e) => Err(format!("Failed to read log file: {}", e))
        }
    } else {
        Err("Log file not initialized".to_string())
    }
}

#[tauri::command]
pub fn get_log_path() -> Result<String, String> {
    logger::get_log_path()
        .map(|p| p.to_string_lossy().to_string())
        .ok_or_else(|| "Log path not available".to_string())
}

#[tauri::command]
pub fn clear_logs() -> Result<(), String> {
    if let Some(log_path) = logger::get_log_path() {
        // Backup current log before clearing
        let backup_path = log_path.with_extension("log.bak");
        fs::copy(&log_path, backup_path)
            .map_err(|e| format!("Failed to backup log: {}", e))?;

        // Clear the log file
        fs::write(&log_path, "")
            .map_err(|e| format!("Failed to clear log file: {}", e))?;

        logger::log(logger::LogLevel::Info, "Logs cleared by user");
        Ok(())
    } else {
        Err("Log file not initialized".to_string())
    }
}

#[tauri::command]
pub fn get_panic_logs() -> Result<String, String> {
    let panic_log_path = PathBuf::from("pastebar-panic.log");
    if panic_log_path.exists() {
        fs::read_to_string(&panic_log_path)
            .map_err(|e| format!("Failed to read panic log: {}", e))
    } else {
        Ok("No panic logs found".to_string())
    }
}