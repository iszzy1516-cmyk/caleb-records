use std::sync::Mutex;
use tauri::Manager;

struct AppState {
    backend: Mutex<Option<tokio::process::Child>>,
}

#[tauri::command]
async fn check_backend_status() -> bool {
    tokio::net::TcpStream::connect("culrecords.duckdns.org:443").await.is_ok()
}

#[tauri::command]
async fn open_staff_portal(app: tauri::AppHandle) -> Result<(), String> {
    if app.get_webview_window("staff").is_some() {
        if let Some(window) = app.get_webview_window("staff") {
            let _ = window.set_focus();
        }
        return Ok(());
    }

    tauri::WebviewWindowBuilder::new(
        &app,
        "staff",
        tauri::WebviewUrl::External("https://culrecords.duckdns.org/staff/".parse().unwrap()),
    )
    .title("Caleb Records — Staff Portal")
    .inner_size(1280.0, 800.0)
    .min_inner_size(800.0, 600.0)
    .build()
    .map_err(|e| e.to_string())?;

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            backend: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            check_backend_status,
            open_staff_portal,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
