const DEFAULT_DAEMON_WS_URL = "ws://127.0.0.1:8765";

const appendToken = (baseWsUrl, token) => {
  if (!token) {
    return baseWsUrl;
  }

  try {
    const url = new URL(baseWsUrl);
    url.searchParams.set("token", token);
    return url.toString();
  } catch {
    return baseWsUrl;
  }
};

export async function loadDaemonIpcSettings() {
  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const runtimeSettings = await invoke("get_daemon_settings");
    const wsUrl = runtimeSettings?.ws_url || DEFAULT_DAEMON_WS_URL;
    const token = runtimeSettings?.token || "";
    return { wsUrl: appendToken(wsUrl, token) };
  } catch {
    const wsUrl = import.meta.env.VITE_NEON_DAEMON_URL || DEFAULT_DAEMON_WS_URL;
    const token = import.meta.env.VITE_NEON_DAEMON_TOKEN || "";
    return { wsUrl: appendToken(wsUrl, token) };
  }
}

export async function launchPrivilegedDaemon(password) {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke("launch_privileged_daemon", { password });
}

export async function stopPrivilegedDaemon() {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke("stop_privileged_daemon");
}
