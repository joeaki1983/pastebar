use once_cell::sync::OnceCell;
use std::fs;
use std::path::PathBuf;
use std::sync::Once;
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

static LOG_GUARD: OnceCell<WorkerGuard> = OnceCell::new();
static LOG_PATH: OnceCell<PathBuf> = OnceCell::new();
static PANIC_HOOK: Once = Once::new();

pub fn init_logging(app: &tauri::App) -> Option<PathBuf> {
  if let Some(existing) = LOG_PATH.get() {
    return Some(existing.clone());
  }

  let log_dir = match tauri::api::path::app_log_dir(&app.config()) {
    Some(dir) => dir,
    None => {
      eprintln!("PasteBar: unable to determine application log directory");
      return None;
    }
  };

  if let Err(err) = fs::create_dir_all(&log_dir) {
    eprintln!(
      "PasteBar: failed to create log directory {}: {}",
      log_dir.display(),
      err
    );
    return None;
  }

  let log_file_path = log_dir.join("pastebar.log");

  let file_appender = tracing_appender::rolling::daily(&log_dir, "pastebar.log");
  let (non_blocking, guard) = tracing_appender::non_blocking(file_appender);

  let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

  let file_layer = fmt::layer().with_ansi(false).with_writer(non_blocking);
  let stdout_layer = fmt::layer().with_ansi(cfg!(debug_assertions));

  let subscriber = tracing_subscriber::registry()
    .with(env_filter)
    .with(file_layer)
    .with(stdout_layer);

  if let Err(err) = subscriber.try_init() {
    eprintln!("PasteBar: failed to initialise logging: {}", err);
    return None;
  }

  let _ = LOG_GUARD.set(guard);
  let _ = LOG_PATH.set(log_file_path.clone());

  tracing::info!(
    "PasteBar logging initialised at {}",
    log_file_path.display()
  );

  Some(log_file_path)
}

pub fn install_panic_hook(log_path: Option<PathBuf>) {
  let log_hint = log_path.map(|path| path.display().to_string());

  PANIC_HOOK.call_once(move || {
    let hook_hint = log_hint.clone();
    std::panic::set_hook(Box::new(move |info| {
      let message = info
        .payload()
        .downcast_ref::<&str>()
        .map(|s| (*s).to_string())
        .or_else(|| info.payload().downcast_ref::<String>().cloned())
        .unwrap_or_else(|| "Unknown panic".to_string());

      let location = info
        .location()
        .map(|loc| format!("{}:{}:{}", loc.file(), loc.line(), loc.column()))
        .unwrap_or_else(|| "unknown location".to_string());

      let backtrace = std::backtrace::Backtrace::force_capture();

      tracing::error!(
        target: "panic",
        message = %message,
        location = %location,
        backtrace = %backtrace,
        "PasteBar encountered an unrecoverable error"
      );

      eprintln!("PasteBar panic at {location}: {message}\nBacktrace:\n{backtrace}");

      if let Some(path) = &hook_hint {
        eprintln!("Panic details were also logged to {path}");
      }
    }));
  });
}

pub fn log_file_path() -> Option<PathBuf> {
  LOG_PATH.get().cloned()
}
