use std::sync::Mutex;
use tauri::Manager;

struct AppState {
    backend: Mutex<Option<tokio::process::Child>>,
}

#[tauri::command]
async fn check_backend_status() -> bool {
    tokio::net::TcpStream::connect("127.0.0.1:8000").await.is_ok()
}

fn parse_host_port(url: &str) -> Option<String> {
    let without_proto = url.strip_prefix("http://")
        .or_else(|| url.strip_prefix("https://"))?;
    Some(without_proto.split('/').next()?.to_string())
}

#[tauri::command]
async fn check_service_status(url: String) -> bool {
    if let Some(addr) = parse_host_port(&url) {
        tokio::net::TcpStream::connect(&addr).await.is_ok()
    } else {
        false
    }
}

fn find_backend_dir(app: &tauri::AppHandle) -> Option<std::path::PathBuf> {
    // Try from resource dir (src-tauri in dev)
    if let Ok(resource_dir) = app.path().resource_dir() {
        let candidates = [
            resource_dir.join("../../backend"),
            resource_dir.join("../backend"),
            resource_dir.join("backend"),
        ];
        for candidate in &candidates {
            if candidate.join("main.py").exists() {
                return Some(candidate.clone());
            }
        }
    }

    // Try from current working directory
    if let Ok(cwd) = std::env::current_dir() {
        let candidates = [
            cwd.join("backend"),
            cwd.join("../backend"),
            cwd.join("../../backend"),
        ];
        for candidate in &candidates {
            if candidate.join("main.py").exists() {
                return Some(candidate.clone());
            }
        }
    }

    // Try env var
    if let Ok(env_path) = std::env::var("CUL_BACKEND_PATH") {
        let path = std::path::PathBuf::from(env_path);
        if path.join("main.py").exists() {
            return Some(path);
        }
    }

    None
}

fn get_python_cmd(backend_dir: &std::path::Path) -> (std::path::PathBuf, Vec<&'static str>) {
    let venv_python = backend_dir.join("venv/bin/python");
    let venv_python3 = backend_dir.join("venv/bin/python3");
    let venv_py_win = backend_dir.join("venv/Scripts/python.exe");

    let args = vec!["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"];

    if venv_python.exists() {
        return (venv_python, args);
    }
    if venv_python3.exists() {
        return (venv_python3, args);
    }
    if venv_py_win.exists() {
        return (venv_py_win, args);
    }

    let py = if std::process::Command::new("python3").arg("--version").output().is_ok() {
        std::path::PathBuf::from("python3")
    } else {
        std::path::PathBuf::from("python")
    };
    (py, args)
}

#[tauri::command]
async fn start_backend(
    state: tauri::State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<String, String> {
    // Check if already running on port 8000
    if check_backend_status().await {
        return Ok("Backend is already running on port 8000".to_string());
    }

    // Check if we already started it
    {
        let existing = state.backend.lock().map_err(|e| e.to_string())?;
        if existing.is_some() {
            return Ok("Backend was already started by this app".to_string());
        }
    }

    let backend_dir = find_backend_dir(&app)
        .ok_or("Could not find backend directory. Set CUL_BACKEND_PATH env var.")?;
    let (python, args) = get_python_cmd(&backend_dir);

    let mut cmd = tokio::process::Command::new(&python);
    cmd.args(&args)
        .current_dir(&backend_dir)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null());

    let child = cmd
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;

    {
        let mut backend = state.backend.lock().map_err(|e| e.to_string())?;
        *backend = Some(child);
    }

    // Wait a moment for the server to start
    tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;

    if check_backend_status().await {
        Ok("Backend started successfully".to_string())
    } else {
        Ok("Backend process started, but not responding yet. It may still be initializing.".to_string())
    }
}

#[tauri::command]
async fn stop_backend(state: tauri::State<'_, AppState>) -> Result<String, String> {
    let child = {
        let mut backend = state.backend.lock().map_err(|e| e.to_string())?;
        backend.take()
    };
    if let Some(mut child) = child {
        let _ = child.kill().await;
        return Ok("Backend stopped".to_string());
    }
    Err("Backend was not started by this app. Stop it manually if needed.".to_string())
}

#[tauri::command]
async fn open_student_portal(app: tauri::AppHandle) -> Result<(), String> {
    if app.get_webview_window("student").is_some() {
        if let Some(window) = app.get_webview_window("student") {
            let _ = window.set_focus();
        }
        return Ok(());
    }

    tauri::WebviewWindowBuilder::new(
        &app,
        "student",
        tauri::WebviewUrl::External("http://localhost:5173".parse().unwrap()),
    )
    .title("Caleb Records — Student Portal")
    .inner_size(1280.0, 800.0)
    .min_inner_size(800.0, 600.0)
    .build()
    .map_err(|e| e.to_string())?;

    Ok(())
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
        tauri::WebviewUrl::External("http://localhost:5174".parse().unwrap()),
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
            check_service_status,
            start_backend,
            stop_backend,
            open_student_portal,
            open_staff_portal,
        ])
        .setup(|app| {
            #[cfg(desktop)]
            {
                if let Ok(tray_menu) = tauri::menu::MenuBuilder::new(app).build() {
                    let _ = tauri::tray::TrayIconBuilder::new()
                        .menu(&tray_menu)
                        .icon(app.default_window_icon().unwrap().clone())
                        .on_menu_event(|app, event| {
                            if event.id() == "show" {
                                if let Some(window) = app.get_webview_window("main") {
                                    let _ = window.show();
                                    let _ = window.set_focus();
                                }
                            }
                        })
                        .build(app);
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
