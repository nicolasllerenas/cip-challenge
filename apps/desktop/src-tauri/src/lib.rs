use std::sync::Mutex;

use tauri::{AppHandle, Manager, RunEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

const GATEWAY_URL: &str = "http://127.0.0.1:8000";
const EXPORTS_FOLDER: &str = "Asistente de Investigación";

#[derive(Default)]
struct Backend(Mutex<Option<CommandChild>>);

#[tauri::command]
fn gateway_url() -> &'static str {
    GATEWAY_URL
}

fn start_backend(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let data_dir = app.path().app_data_dir()?;
    let exports_dir = app.path().document_dir()?.join(EXPORTS_FOLDER);
    let (mut events, child) = app
        .shell()
        .sidecar("cip-backend")?
        .env("CIP_DATA_DIR", data_dir)
        .env("CIP_EXPORTS_DIR", exports_dir)
        .spawn()?;
    tauri::async_runtime::spawn(async move { while events.recv().await.is_some() {} });
    let state = app.state::<Backend>();
    let mut backend = state.0.lock().map_err(|_| "backend lock poisoned")?;
    *backend = Some(child);
    Ok(())
}

fn stop_backend(app: &AppHandle) {
    if let Ok(mut guard) = app.state::<Backend>().0.lock() {
        if let Some(child) = guard.take() {
            let _ = child.kill();
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .manage(Backend::default())
        .invoke_handler(tauri::generate_handler![gateway_url])
        .setup(|app| {
            if !cfg!(debug_assertions) {
                start_backend(app.handle())?;
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("failed to build the research assistant")
        .run(|app, event| {
            if let RunEvent::Exit = event {
                stop_backend(app);
            }
        });
}
