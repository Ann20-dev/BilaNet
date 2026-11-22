//! BilaNet desktop shell.
//!
//! On launch it starts the bundled Python backend (built with PyInstaller and shipped as a
//! resource) on a free local port, then opens the window and tells the page where the
//! backend is. User data (chat database, downloaded model, logs) lives in the per-user
//! app data folder. When the app exits the backend is stopped; if the app crashes, the
//! backend notices this process is gone and exits by itself.

use std::{
    fs,
    net::TcpListener,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
};
use tauri::{AppHandle, Manager, RunEvent, WebviewUrl, WebviewWindowBuilder};

struct Backend(Mutex<Option<Child>>);

fn free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .and_then(|l| l.local_addr())
        .map(|a| a.port())
        .unwrap_or(8765)
}

fn backend_exe(app: &AppHandle) -> tauri::Result<PathBuf> {
    let name = if cfg!(windows) { "bilanet-backend.exe" } else { "bilanet-backend" };
    Ok(app.path().resource_dir()?.join("backend").join(name))
}

fn spawn_backend(app: &AppHandle, port: u16) -> Result<Child, String> {
    let data = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let models = data.join("models");
    fs::create_dir_all(&models).map_err(|e| format!("cannot create {}: {e}", models.display()))?;
    let log = fs::File::create(data.join("backend.log")).map_err(|e| e.to_string())?;
    let log_err = log.try_clone().map_err(|e| e.to_string())?;
    let exe = backend_exe(app).map_err(|e| e.to_string())?;
    // SQLAlchemy wants forward slashes, also on Windows. Gives sqlite:////home/... or sqlite:///C:/Users/...
    let db = data.join("bilanet.db").to_string_lossy().replace('\\', "/");
    let db_url = format!("sqlite:///{db}");
    // llama.cpp runs best on physical cores; assume 2 logical threads per core.
    let threads = std::thread::available_parallelism()
        .map(|n| (n.get() / 2).clamp(2, 8))
        .unwrap_or(4);

    let mut cmd = Command::new(&exe);
    cmd.current_dir(&data)
        .env("AI_PROVIDER", "local")
        // The backend picks the model file in this folder (small or standard, chosen at first run).
        .env("MODELS_DIR", &models)
        .env("DB_URL", db_url)
        .env("PORT", port.to_string())
        .env("THREADS", threads.to_string())
        // The backend exits by itself when this process goes away (quit or crash).
        .env("BILANET_PARENT_PID", std::process::id().to_string())
        .stdin(Stdio::null())
        .stdout(log)
        .stderr(log_err);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }
    cmd.spawn().map_err(|e| format!("cannot start {}: {e}", exe.display()))
}

pub fn run() {
    let app = tauri::Builder::default()
        .setup(|app| {
            let port = free_port();
            let mut init = format!("window.__BILANET_API__ = {:?};", format!("http://127.0.0.1:{port}"));
            match spawn_backend(app.handle(), port) {
                Ok(child) => {
                    app.manage(Backend(Mutex::new(Some(child))));
                }
                Err(err) => {
                    eprintln!("BilaNet backend failed to start: {err}");
                    init.push_str(&format!("window.__BILANET_BACKEND_ERROR__ = {:?};", err));
                    app.manage(Backend(Mutex::new(None)));
                }
            }
            WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
                .title("BilaNet")
                .inner_size(1200.0, 800.0)
                .min_inner_size(800.0, 500.0)
                .initialization_script(&init)
                .build()?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building BilaNet");

    app.run(|handle, event| {
        if let RunEvent::Exit = event {
            if let Some(state) = handle.try_state::<Backend>() {
                if let Some(mut child) = state.0.lock().unwrap().take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
        }
    });
}
