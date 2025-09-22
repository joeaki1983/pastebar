use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use chrono::{DateTime, Local};
use once_cell::sync::Lazy;

// 全局日志文件句柄
static LOG_FILE: Lazy<Mutex<Option<fs::File>>> = Lazy::new(|| Mutex::new(None));
static LOG_PATH: Lazy<Mutex<Option<PathBuf>>> = Lazy::new(|| Mutex::new(None));

#[derive(Debug, Clone, Copy)]
pub enum LogLevel {
    Debug,
    Info,
    Warn,
    Error,
    Fatal,
}

impl std::fmt::Display for LogLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LogLevel::Debug => write!(f, "DEBUG"),
            LogLevel::Info => write!(f, "INFO"),
            LogLevel::Warn => write!(f, "WARN"),
            LogLevel::Error => write!(f, "ERROR"),
            LogLevel::Fatal => write!(f, "FATAL"),
        }
    }
}

/// 初始化日志系统
pub fn init_logger(data_dir: &PathBuf) -> Result<(), String> {
    // 创建日志目录
    let log_dir = data_dir.join("logs");
    fs::create_dir_all(&log_dir).map_err(|e| format!("Failed to create log directory: {}", e))?;

    // 创建日志文件名（带日期）
    let now: DateTime<Local> = Local::now();
    let log_filename = format!("pastebar_{}.log", now.format("%Y%m%d"));
    let log_path = log_dir.join(&log_filename);

    // 打开日志文件（追加模式）
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
        .map_err(|e| format!("Failed to open log file: {}", e))?;

    // 保存日志文件句柄和路径
    *LOG_FILE.lock().unwrap() = Some(file);
    *LOG_PATH.lock().unwrap() = Some(log_path.clone());

    // 写入启动日志
    log(LogLevel::Info, "PasteBar application started");
    log(LogLevel::Info, &format!("Log file: {}", log_path.display()));

    // 清理旧日志文件（保留最近7天）
    cleanup_old_logs(&log_dir);

    Ok(())
}

/// 写入日志
pub fn log(level: LogLevel, message: &str) {
    log_with_context(level, message, None);
}

/// 带上下文的日志
pub fn log_with_context(level: LogLevel, message: &str, context: Option<&str>) {
    let now: DateTime<Local> = Local::now();
    let timestamp = now.format("%Y-%m-%d %H:%M:%S%.3f");

    let context_str = if let Some(ctx) = context {
        format!(" [{}]", ctx)
    } else {
        String::new()
    };

    let log_line = format!("[{}] [{}]{} {}\n", timestamp, level, context_str, message);

    // 输出到控制台（debug 模式或错误级别）
    #[cfg(debug_assertions)]
    {
        match level {
            LogLevel::Error | LogLevel::Fatal => eprintln!("{}", log_line.trim()),
            _ => println!("{}", log_line.trim()),
        }
    }

    #[cfg(not(debug_assertions))]
    {
        match level {
            LogLevel::Error | LogLevel::Fatal => eprintln!("{}", log_line.trim()),
            _ => {}
        }
    }

    // 写入日志文件
    if let Ok(mut file_guard) = LOG_FILE.lock() {
        if let Some(ref mut file) = *file_guard {
            let _ = file.write_all(log_line.as_bytes());
            let _ = file.flush();
        }
    }
}

/// 记录错误并返回错误字符串
pub fn log_error<E: std::fmt::Display>(context: &str, error: E) -> String {
    let error_msg = format!("{}: {}", context, error);
    log_with_context(LogLevel::Error, &error_msg, Some(context));
    error_msg
}

/// 清理旧日志文件
fn cleanup_old_logs(log_dir: &PathBuf) {
    let retention_days = 7;
    let now = Local::now();

    if let Ok(entries) = fs::read_dir(log_dir) {
        for entry in entries.flatten() {
            if let Ok(metadata) = entry.metadata() {
                if let Ok(modified) = metadata.modified() {
                    let modified_datetime: DateTime<Local> = modified.into();
                    let age = now.signed_duration_since(modified_datetime);

                    if age.num_days() > retention_days {
                        let path = entry.path();
                        if path.extension().and_then(|s| s.to_str()) == Some("log") {
                            if let Err(e) = fs::remove_file(&path) {
                                eprintln!("Failed to remove old log file {:?}: {}", path, e);
                            } else {
                                log(LogLevel::Debug, &format!("Removed old log file: {:?}", path));
                            }
                        }
                    }
                }
            }
        }
    }
}

/// 获取当前日志文件路径
pub fn get_log_path() -> Option<PathBuf> {
    LOG_PATH.lock().ok()?.clone()
}

/// 记录 panic 信息到日志
pub fn log_panic(info: &std::panic::PanicInfo) {
    let msg = if let Some(s) = info.payload().downcast_ref::<&str>() {
        s.to_string()
    } else if let Some(s) = info.payload().downcast_ref::<String>() {
        s.clone()
    } else {
        "Unknown panic".to_string()
    };

    let location = if let Some(location) = info.location() {
        format!(" at {}:{}:{}", location.file(), location.line(), location.column())
    } else {
        String::new()
    };

    log_with_context(LogLevel::Fatal, &format!("PANIC: {}{}", msg, location), Some("PANIC"));

    // 同时写入独立的 panic 日志文件
    if let Ok(mut file) = OpenOptions::new()
        .create(true)
        .append(true)
        .open("pastebar-panic.log")
    {
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S");
        let _ = writeln!(file, "[{}] Panic: {}{}", timestamp, msg, location);
    }
}

// 便捷宏
#[macro_export]
macro_rules! log_debug {
    ($($arg:tt)*) => {
        $crate::logger::log($crate::logger::LogLevel::Debug, &format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_info {
    ($($arg:tt)*) => {
        $crate::logger::log($crate::logger::LogLevel::Info, &format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_warn {
    ($($arg:tt)*) => {
        $crate::logger::log($crate::logger::LogLevel::Warn, &format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_error {
    ($($arg:tt)*) => {
        $crate::logger::log($crate::logger::LogLevel::Error, &format!($($arg)*))
    };
}