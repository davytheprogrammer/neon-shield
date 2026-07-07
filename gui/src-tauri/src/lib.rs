use serde::Serialize;
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[derive(Serialize)]
struct DaemonSettings {
    ws_url: String,
    token: Option<String>,
}

#[derive(Serialize)]
struct DaemonLaunchResult {
    started: bool,
    pid: Option<u32>,
    message: String,
}

#[tauri::command]
fn get_daemon_settings() -> DaemonSettings {
    let ws_url =
        std::env::var("NEON_SHIELD_DAEMON_URL").unwrap_or_else(|_| "ws://127.0.0.1:8765".to_string());
    let token = std::env::var("NEON_SHIELD_DAEMON_TOKEN")
        .ok()
        .and_then(|value| {
            if value.trim().is_empty() {
                None
            } else {
                Some(value)
            }
        });

    DaemonSettings { ws_url, token }
}

fn project_root() -> PathBuf {
    std::env::var("NEON_SHIELD_PROJECT_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .and_then(|path| path.parent())
                .map(PathBuf::from)
                .unwrap_or_else(|| PathBuf::from("."))
        })
}

fn pid_file() -> PathBuf {
    std::env::temp_dir().join("neon_shield_daemon.pid")
}

#[tauri::command]
fn launch_privileged_daemon(password: String) -> Result<DaemonLaunchResult, String> {
    if password.trim().is_empty() {
        return Err("sudo password is required".into());
    }

    let root = project_root();
    let daemon_path = root.join("daemon.py");
    if !daemon_path.exists() {
        return Err(format!("daemon.py not found at {}", daemon_path.display()));
    }

    let mut verify = Command::new("sudo")
        .arg("-S")
        .arg("-p")
        .arg("")
        .arg("-v")
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|err| format!("Failed to validate sudo credentials: {err}"))?;

    if let Some(stdin) = verify.stdin.as_mut() {
        stdin
            .write_all(format!("{password}\n").as_bytes())
            .map_err(|err| format!("Failed to submit sudo password: {err}"))?;
    }

    let verify_status = verify
        .wait()
        .map_err(|err| format!("Failed to wait for sudo validation: {err}"))?;

    if !verify_status.success() {
        return Err("sudo authentication failed".into());
    }

    let pid_path = pid_file();
    let pid_path_arg = pid_path.display().to_string();
    let daemon_script = daemon_path.display().to_string();
    let command_line = format!(
        "cd '{}' && echo $$ > '{}' && exec env NEON_SHIELD_DAEMON_URL='ws://127.0.0.1:8765' python3 '{}'",
        root.display(),
        pid_path_arg,
        daemon_script
    );

    let child = Command::new("sudo")
        .arg("-n")
        .arg("bash")
        .arg("-lc")
        .arg(command_line)
        .current_dir(&root)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|err| format!("Failed to launch daemon: {err}"))?;

    Ok(DaemonLaunchResult {
        started: true,
        pid: Some(child.id()),
        message: "Privileged daemon launch requested".into(),
    })
}

#[tauri::command]
fn stop_privileged_daemon() -> Result<DaemonLaunchResult, String> {
    let pid_path = pid_file();
    let pid = fs::read_to_string(&pid_path)
        .ok()
        .and_then(|value| value.trim().parse::<u32>().ok());

    let Some(pid) = pid else {
        return Err("No daemon pid file was found".into());
    };

    let status = Command::new("sudo")
        .arg("-n")
        .arg("kill")
        .arg(pid.to_string())
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|err| format!("Failed to stop daemon: {err}"))?;

    if !status.success() {
        return Err("Failed to stop the daemon".into());
    }

    let _ = fs::remove_file(pid_path);

    Ok(DaemonLaunchResult {
        started: false,
        pid: Some(pid),
        message: "Privileged daemon stopped".into(),
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            get_daemon_settings,
            launch_privileged_daemon,
            stop_privileged_daemon
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
