import React, { useState, useEffect, useRef } from "react";
import { 
  Shield, 
  Terminal as TermIcon, 
  Settings, 
  Wifi, 
  Users, 
  Activity, 
  Key, 
  Play, 
  Square, 
  RefreshCw, 
  AlertTriangle, 
  Copy, 
  Search, 
  Check, 
  Trash2, 
  Layers 
} from "lucide-react";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast] = useState(null);
  
  // System State (from Daemon)
  const [sysInfo, setSysInfo] = useState({
    interface: "unknown",
    gateway_ip: "unknown",
    local_ip: "127.0.0.1",
    cidr: "127.0.0.1/24"
  });
  const [mitmRunning, setMitmRunning] = useState(false);
  const [runningProcessName, setRunningProcessName] = useState(null);
  const [stateInfo, setStateInfo] = useState(null);
  
  // Logs & History
  const [trafficLog, setTrafficLog] = useState([]);
  const [credsLog, setCredsLog] = useState([]);
  const [terminalLines, setTerminalLines] = useState([]);
  
  // Scan / Discovery
  const [scanning, setScanning] = useState(false);
  const [discoveredHosts, setDiscoveredHosts] = useState([]);
  const [selectedTargets, setSelectedTargets] = useState([]);
  
  // Configuration Settings
  const [config, setConfig] = useState({
    interface: "",
    targets: "",
    gateway_ip: "",
    dns_enabled: false,
    dns_redirects: {},
    enable_image_swap: true,
    enable_html_banner: true,
    banner_text: "⚡ NEON-SHIELD LAB: traffic intercepted for authorized research."
  });

  // UI States
  const [terminalCollapsed, setTerminalCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTrafficItem, setSelectedTrafficItem] = useState(null);
  
  // Phase 1 WiFi Attack States
  const [wifiIface, setWifiIface] = useState("wlan0");
  const [apSsid, setApSsid] = useState("Starbucks_WiFi");
  const [apChannel, setApChannel] = useState(6);
  const [deauthTargetMac, setDeauthTargetMac] = useState("");
  const [deauthGatewayMac, setDeauthGatewayMac] = useState("");
  const [deauthSsid, setDeauthSsid] = useState("");

  const ws = useRef(null);
  const terminalEndRef = useRef(null);
  const pendingRequests = useRef({});
  const requestIdCounter = useRef(0);

  // Show dynamic toast notifications
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Helper to send action with request-response tracking over WS
  const sendAction = (action, params = {}) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      showToast("Not connected to background daemon", "error");
      return Promise.reject("Not connected");
    }
    const id = requestIdCounter.current++;
    const payload = { id, action, params };
    
    return new Promise((resolve, reject) => {
      pendingRequests.current[id] = { resolve, reject };
      ws.current.send(jsonStringify(payload));
    });
  };

  const jsonStringify = (obj) => {
    try {
      return JSON.stringify(obj);
    } catch (e) {
      return "";
    }
  };

  // WebSocket Connection Lifecycle
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    console.log("Connecting to daemon...");
    ws.current = new WebSocket("ws://127.0.0.1:8765");

    ws.current.onopen = () => {
      setWsConnected(true);
      showToast("Connected to NEON-SHIELD Daemon", "success");
      // Query config and initial status
      sendAction("get_config").then(res => {
        if (res.status === "success") {
          setConfig(res.config);
        }
      });
    };

    ws.current.onclose = () => {
      setWsConnected(false);
      // Try to reconnect in 3s
      setTimeout(connectWebSocket, 3000);
    };

    ws.current.onerror = (err) => {
      console.error("WS connection error:", err);
      setWsConnected(false);
    };

    ws.current.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        
        // Handle Request-Response matching
        if (payload.id !== undefined && pendingRequests.current[payload.id]) {
          const { resolve } = pendingRequests.current[payload.id];
          delete pendingRequests.current[payload.id];
          resolve(payload);
          return;
        }

        // Handle Broadcast messages
        const { type, data } = payload;
        switch (type) {
          case "init":
            setSysInfo(data.sys_info);
            setMitmRunning(data.running);
            setRunningProcessName(data.process);
            setStateInfo(data.state);
            if (data.traffic_history) setTrafficLog(data.traffic_history.reverse());
            if (data.creds_history) setCredsLog(data.creds_history.reverse());
            break;
            
          case "status":
            setMitmRunning(data.running);
            setRunningProcessName(data.process);
            setStateInfo(data.state);
            break;
            
          case "traffic":
            setTrafficLog(prev => [data, ...prev].slice(0, 500));
            break;
            
          case "creds":
            setCredsLog(prev => [data, ...prev].slice(0, 200));
            showToast("⚠️ CREDENTIALS CAPTURED!", "error");
            break;
            
          case "terminal":
            setTerminalLines(prev => [...prev, `[${data.process}] ${data.text}`].slice(-200));
            break;
            
          default:
            break;
        }
      } catch (e) {
        console.error("Failed to parse websocket message:", e);
      }
    };
  };

  // Scroll terminal to bottom
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [terminalLines]);

  // Command handlers
  const handleStartMITM = () => {
    sendAction("start_mitm", {
      targets: config.targets,
      interface: config.interface,
      dns_redirect: Object.entries(config.dns_redirects || {})
        .map(([k, v]) => `${k}:${v}`)
        .join(",")
    }).then(res => {
      if (res.status === "success") {
        showToast(res.message);
        setMitmRunning(true);
        setRunningProcessName("mitm");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  const handleStopMITM = () => {
    sendAction("stop_mitm").then(res => {
      if (res.status === "success") {
        showToast("MITM Lab stopped and firewall restored");
        setMitmRunning(false);
        setRunningProcessName(null);
      } else {
        showToast(res.message, "error");
      }
    });
  };

  const handleScanSubnet = () => {
    setScanning(true);
    setDiscoveredHosts([]);
    sendAction("scan_network").then(res => {
      setScanning(false);
      if (res.status === "success") {
        setDiscoveredHosts(res.hosts);
        showToast(`Discovered ${res.hosts.length} live hosts.`);
      } else {
        showToast(res.message, "error");
      }
    }).catch(() => setScanning(false));
  };

  const handleToggleTarget = (ip) => {
    if (selectedTargets.includes(ip)) {
      setSelectedTargets(prev => prev.filter(t => t !== ip));
    } else {
      setSelectedTargets(prev => [...prev, ip]);
    }
  };

  const handleApplyDiscoveredTargets = () => {
    const targetsStr = selectedTargets.join(",");
    setConfig(prev => ({ ...prev, targets: targetsStr }));
    showToast(`Targets set to: ${targetsStr}`);
    setActiveTab("dashboard");
  };

  const handleSaveConfig = () => {
    sendAction("save_config", { config }).then(res => {
      if (res.status === "success") {
        showToast("Configuration saved to neon-shield.yml");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  // Phase 1 Commands
  const handleStartAP = () => {
    sendAction("start_ap", {
      interface: wifiIface,
      ssid: apSsid,
      channel: apChannel
    }).then(res => {
      if (res.status === "success") {
        showToast("Rogue AP (Evil Twin) active!");
        setMitmRunning(true);
        setRunningProcessName("ap");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  const handleStartWiFiScan = () => {
    sendAction("scan_wifi", { interface: wifiIface }).then(res => {
      if (res.status === "success") {
        showToast("WiFi Scanning active. Inspect terminal output.");
        setMitmRunning(true);
        setRunningProcessName("scan");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  const handleStartDeauth = () => {
    if (!deauthTargetMac) {
      showToast("Target MAC Address is required", "error");
      return;
    }
    sendAction("start_deauth", {
      interface: wifiIface,
      target_mac: deauthTargetMac,
      gateway_mac: deauthGatewayMac,
      ssid: deauthSsid
    }).then(res => {
      if (res.status === "success") {
        showToast("Deauth flood started!");
        setMitmRunning(true);
        setRunningProcessName("deauth");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  const handleEmergencyCleanup = () => {
    sendAction("stop_all").then(res => {
      showToast("Emergency cleanup complete.");
      setMitmRunning(false);
      setRunningProcessName(null);
    });
  };

  // Helper copy function
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    showToast("Copied to clipboard");
  };

  // Filter traffic log
  const filteredTraffic = trafficLog.filter(item => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      (item.host && item.host.toLowerCase().includes(query)) ||
      (item.path && item.path.toLowerCase().includes(query)) ||
      (item.method && item.method.toLowerCase().includes(query)) ||
      (item.src_ip && item.src_ip.toLowerCase().includes(query))
    );
  });

  return (
    <div className="app-container">
      <div className="glow-effect"></div>
      
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Shield className="logo-glow" size={24} />
          <h2>NEON-SHIELD</h2>
        </div>
        
        <nav className="nav-links">
          <div 
            className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <Activity size={18} />
            Control Center
          </div>
          
          <div 
            className={`nav-item ${activeTab === "discovery" ? "active" : ""}`}
            onClick={() => setActiveTab("discovery")}
          >
            <Users size={18} />
            Device Discovery
          </div>
          
          <div 
            className={`nav-item ${activeTab === "traffic" ? "active" : ""}`}
            onClick={() => setActiveTab("traffic")}
          >
            <Layers size={18} />
            Traffic Inspector
          </div>
          
          <div 
            className={`nav-item ${activeTab === "credentials" ? "active" : ""}`}
            onClick={() => setActiveTab("credentials")}
          >
            <Key size={18} />
            Credentials Vault
          </div>
          
          <div 
            className={`nav-item ${activeTab === "wifi" ? "active" : ""}`}
            onClick={() => setActiveTab("wifi")}
          >
            <Wifi size={18} />
            WiFi Attacks (P1)
          </div>
          
          <div 
            className={`nav-item ${activeTab === "config" ? "active" : ""}`}
            onClick={() => setActiveTab("config")}
          >
            <Settings size={18} />
            Lab Configuration
          </div>
        </nav>
        
        <div className="sidebar-footer">
          <div className="status-badge">
            <span className={`dot ${wsConnected ? "running" : "stopped"}`}></span>
            Daemon: {wsConnected ? "Online" : "Offline"}
          </div>
          
          <div className="status-badge">
            <span className={`dot ${mitmRunning ? "running" : "stopped"}`}></span>
            MITM: {mitmRunning ? `Active (${runningProcessName})` : "Inactive"}
          </div>
        </div>
      </aside>
      
      {/* Main Container */}
      <main className="main-content">
        {/* Header */}
        <header className="main-header">
          <div className="header-title">
            <h1>
              {activeTab === "dashboard" && "Control Center"}
              {activeTab === "discovery" && "Subnet Discovery"}
              {activeTab === "traffic" && "Traffic Inspector"}
              {activeTab === "credentials" && "Credentials Vault"}
              {activeTab === "wifi" && "Phase 1 WiFi Attacks"}
              {activeTab === "config" && "Configuration Profiles"}
            </h1>
          </div>
          
          <div className="system-stats">
            <div className="stat-item">
              <span className="stat-label">Interface</span>
              <span className="stat-val">{sysInfo.interface}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Local IP</span>
              <span className="stat-val">{sysInfo.local_ip}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Gateway IP</span>
              <span className="stat-val">{sysInfo.gateway_ip}</span>
            </div>
          </div>
        </header>
        
        {/* Workspace views */}
        <div className="workspace">
          
          {/* Global warning banner */}
          <div className="legal-warning">
            <AlertTriangle size={18} />
            <span>
              <strong>AUTHORIZED EDUCATIONAL USE ONLY.</strong> Intercepting network traffic without explicit consent is illegal.
            </span>
          </div>

          {/* DASHBOARD TAB */}
          {activeTab === "dashboard" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div className="grid-col-2">
                
                {/* Attack Activation Card */}
                <div className="card">
                  <div className="card-header">
                    <h3><Shield size={18} className="logo-glow" /> MITM Proxy Control</h3>
                  </div>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                      Run transparency rules and ARP spoofing to intercept devices on the current network profile.
                    </p>
                    
                    <div style={{ background: "rgba(255, 255, 255, 0.02)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-muted)" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "0.5rem" }}>
                        <div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>TARGET DEVICES</div>
                          <div style={{ fontFamily: "monospace", fontSize: "0.9rem", fontWeight: "bold" }}>
                            {config.targets ? config.targets : "Auto-discover subnet"}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>ACTIVE ROUTE</div>
                          <div style={{ fontFamily: "monospace", fontSize: "0.9rem", fontWeight: "bold" }}>
                            {sysInfo.gateway_ip} ({sysInfo.interface})
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div style={{ display: "flex", gap: "1rem" }}>
                      {mitmRunning ? (
                        <button className="btn btn-danger" style={{ flex: 1 }} onClick={handleStopMITM}>
                          <Square size={16} /> Stop Interception
                        </button>
                      ) : (
                        <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleStartMITM} disabled={!wsConnected}>
                          <Play size={16} /> Start Interception
                        </button>
                      )}
                      
                      <button className="btn btn-secondary" onClick={handleEmergencyCleanup}>
                        <RefreshCw size={16} /> Force Cleanup
                      </button>
                    </div>
                  </div>
                </div>

                {/* Lab Info Card */}
                <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                  <div className="card-header">
                    <h3>🛡️ MITM Status Panel</h3>
                  </div>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem", fontSize: "0.85rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Spoofer state:</span>
                      <span style={{ color: mitmRunning ? "var(--neon-green)" : "var(--neon-red)", fontWeight: "bold" }}>
                        {mitmRunning ? "SPOOFING ACTIVE" : "IDLE"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Intercepted Connections:</span>
                      <span style={{ fontFamily: "monospace" }}>{trafficLog.length}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Captured Logins:</span>
                      <span style={{ color: credsLog.length > 0 ? "var(--neon-yellow)" : "var(--text-primary)", fontWeight: "bold", fontFamily: "monospace" }}>
                        {credsLog.length}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Subnet CIDR:</span>
                      <span style={{ fontFamily: "monospace" }}>{sysInfo.cidr}</span>
                    </div>
                  </div>
                  
                  <div style={{ marginTop: "1rem", borderTop: "1px solid var(--border-muted)", paddingTop: "1rem", display: "flex", justifyContent: "space-between" }}>
                    <button className="btn btn-secondary" style={{ width: "100%", padding: "0.5rem" }} onClick={() => setActiveTab("config")}>
                      Modify Network Config
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick statistics */}
              <div className="card">
                <div className="card-header">
                  <h3>Real-time Activities</h3>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
                  <div style={{ padding: "1rem", background: "rgba(255,255,255,0.02)", borderRadius: "8px", border: "1px solid var(--border-muted)" }}>
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.75rem", textTransform: "uppercase" }}>Intercept rate</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "800", marginTop: "0.25rem", color: "var(--neon-cyan)" }}>
                      {mitmRunning ? "Active" : "0/s"}
                    </div>
                  </div>
                  <div style={{ padding: "1rem", background: "rgba(255,255,255,0.02)", borderRadius: "8px", border: "1px solid var(--border-muted)" }}>
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.75rem", textTransform: "uppercase" }}>Credentials Leak Index</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "800", marginTop: "0.25rem", color: credsLog.length > 0 ? "var(--neon-red)" : "var(--neon-green)" }}>
                      {credsLog.length > 0 ? "HIGH RISK" : "SECURE"}
                    </div>
                  </div>
                  <div style={{ padding: "1rem", background: "rgba(255,255,255,0.02)", borderRadius: "8px", border: "1px solid var(--border-muted)" }}>
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.75rem", textTransform: "uppercase" }}>LAN Dashboard</div>
                    <div style={{ fontSize: "0.9rem", fontFamily: "monospace", marginTop: "0.5rem", color: "var(--neon-blue)" }}>
                      http://{sysInfo.local_ip}:8080
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* DEVICE DISCOVERY TAB */}
          {activeTab === "discovery" && (
            <div className="card">
              <div className="card-header">
                <h3><Users size={18} /> Subnet Host Discovery (ARP Scan)</h3>
                <button className="btn btn-primary" onClick={handleScanSubnet} disabled={scanning || !wsConnected}>
                  {scanning ? <RefreshCw className="animate-spin" size={16} /> : "Scan Network"}
                </button>
              </div>

              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
                Scan the local IP block <strong>{sysInfo.cidr}</strong> via interface <strong>{sysInfo.interface}</strong>. Select specific hosts to execute targeted ARP spoofing.
              </p>

              {discoveredHosts.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div className="table-container">
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th style={{ width: "50px" }}>Target</th>
                          <th>IP Address</th>
                          <th>MAC Address</th>
                          <th>Identity</th>
                        </tr>
                      </thead>
                      <tbody>
                        {discoveredHosts.map((host) => {
                          const isGateway = host.ip === sysInfo.gateway_ip;
                          const isSelf = host.ip === sysInfo.local_ip;
                          return (
                            <tr key={host.ip}>
                              <td>
                                <input
                                  type="checkbox"
                                  disabled={isGateway || isSelf}
                                  checked={selectedTargets.includes(host.ip)}
                                  onChange={() => handleToggleTarget(host.ip)}
                                  style={{ cursor: "pointer", width: "16px", height: "16px" }}
                                />
                              </td>
                              <td style={{ fontFamily: "monospace", fontWeight: "bold" }}>
                                {host.ip} 
                                {isGateway && <span style={{ color: "var(--neon-yellow)", fontSize: "0.75rem", marginLeft: "0.5rem" }}>(Gateway)</span>}
                                {isSelf && <span style={{ color: "var(--neon-cyan)", fontSize: "0.75rem", marginLeft: "0.5rem" }}>(You)</span>}
                              </td>
                              <td style={{ fontFamily: "monospace" }}>{host.mac}</td>
                              <td>
                                {isGateway ? "Subnet Route Gateway" : isSelf ? "NEON-SHIELD Host Machine" : "Interception Target"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
                    <button className="btn btn-secondary" onClick={() => setSelectedTargets([])}>
                      Clear Selection
                    </button>
                    <button 
                      className="btn btn-primary" 
                      onClick={handleApplyDiscoveredTargets}
                      disabled={selectedTargets.length === 0}
                    >
                      Target Selected Devices ({selectedTargets.length})
                    </button>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <Users size={48} />
                  <p>{scanning ? "ARP query scanning subnet..." : "No scan data loaded yet. Run a network scan to discover target devices."}</p>
                </div>
              )}
            </div>
          )}

          {/* TRAFFIC INSPECTOR TAB */}
          {activeTab === "traffic" && (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div className="card-header">
                <h3>Live HTTP/HTTPS Traffic Stream</h3>
                <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
                  <div style={{ position: "relative" }}>
                    <Search style={{ position: "absolute", left: "10px", top: "10px", color: "var(--text-muted)" }} size={16} />
                    <input
                      type="text"
                      placeholder="Filter hosts..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ paddingLeft: "2.25rem", width: "220px", background: "var(--bg-input)", border: "1px solid var(--border-muted)", color: "#fff", borderRadius: "8px", height: "36px" }}
                    />
                  </div>
                  <button className="btn btn-secondary" style={{ padding: "0.5rem 1rem" }} onClick={() => setTrafficLog([])}>
                    <Trash2 size={14} /> Clear logs
                  </button>
                </div>
              </div>

              {filteredTraffic.length > 0 ? (
                <div className="table-container" style={{ maxHeight: "450px" }}>
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Source</th>
                        <th>Method</th>
                        <th>Host</th>
                        <th>Path</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTraffic.map((item, idx) => {
                        const m = (item.method || "").toUpperCase();
                        let badgeClass = "badge-get";
                        if (m === "POST") badgeClass = "badge-post";
                        if (m === "PUT" || m === "PATCH") badgeClass = "badge-put";
                        if (m === "DELETE") badgeClass = "badge-delete";
                        
                        const timeStr = new Date(item.ts * 1000).toLocaleTimeString();
                        
                        return (
                          <tr 
                            key={idx} 
                            onClick={() => setSelectedTrafficItem(item)}
                            style={{ cursor: "pointer" }}
                          >
                            <td style={{ whiteSpace: "nowrap", fontFamily: "monospace" }}>{timeStr}</td>
                            <td style={{ fontFamily: "monospace" }}>{item.src_ip}</td>
                            <td>
                              <span className={`badge ${badgeClass}`}>{m || "REQ"}</span>
                            </td>
                            <td style={{ fontWeight: "600", color: "var(--neon-cyan)" }}>{item.host}</td>
                            <td style={{ fontFamily: "monospace", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {item.path}
                            </td>
                            <td>
                              {item.intercepted ? (
                                <span style={{ color: "var(--neon-red)", fontSize: "0.75rem", fontWeight: "bold" }}>DECRYPTED</span>
                              ) : (
                                <span style={{ color: "var(--neon-green)", fontSize: "0.75rem" }}>FORWARDED</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <Activity size={48} />
                  <p>Awaiting network logs. Start interception to see live traffic.</p>
                </div>
              )}

              {/* Traffic Item Modal Detail Sidebar */}
              {selectedTrafficItem && (
                <div style={{ position: "fixed", right: 0, top: 0, bottom: 0, width: "450px", background: "var(--bg-panel)", borderLeft: "1px solid var(--border-cyan)", zIndex: 1000, padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem", boxShadow: "-5px 0 25px rgba(0,0,0,0.5)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h3>Request Detail</h3>
                    <button className="btn btn-secondary" style={{ padding: "0.25rem 0.5rem" }} onClick={() => setSelectedTrafficItem(null)}>Close</button>
                  </div>
                  
                  <div style={{ overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "1rem", fontSize: "0.85rem" }}>
                    <div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>URL</div>
                      <div style={{ fontFamily: "monospace", wordBreak: "break-all", color: "var(--neon-cyan)", fontWeight: "bold", marginTop: "0.25rem" }}>
                        {selectedTrafficItem.method} {selectedTrafficItem.host}{selectedTrafficItem.path}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>SOURCE IP</div>
                      <div style={{ fontFamily: "monospace", marginTop: "0.25rem" }}>{selectedTrafficItem.src_ip}</div>
                    </div>

                    <div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>TIMESTAMP</div>
                      <div style={{ fontFamily: "monospace", marginTop: "0.25rem" }}>
                        {new Date(selectedTrafficItem.ts * 1000).toLocaleString()}
                      </div>
                    </div>

                    {selectedTrafficItem.headers && (
                      <div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>HEADERS</div>
                        <pre style={{ background: "rgba(0,0,0,0.3)", padding: "0.75rem", borderRadius: "6px", fontFamily: "monospace", fontSize: "0.75rem", overflowX: "auto" }}>
                          {jsonStringify(selectedTrafficItem.headers)}
                        </pre>
                      </div>
                    )}

                    {selectedTrafficItem.body && (
                      <div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>INTERCEPTED PAYLOAD (POST BODY)</div>
                        <pre style={{ background: "rgba(255, 59, 48, 0.05)", border: "1px solid var(--border-red)", padding: "0.75rem", borderRadius: "6px", fontFamily: "monospace", fontSize: "0.75rem", color: "#ff8888", overflowX: "auto" }}>
                          {selectedTrafficItem.body}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* CREDENTIALS TAB */}
          {activeTab === "credentials" && (
            <div className="card">
              <div className="card-header">
                <h3><Key size={18} style={{ color: "var(--neon-red)" }} /> Captured Credentials Vault</h3>
                <button className="btn btn-secondary" onClick={() => setCredsLog([])}>
                  Clear Vault
                </button>
              </div>

              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
                Active login form and HTTP authentication captures are saved here in plaintext. Review intercepted passwords and secure variables.
              </p>

              {credsLog.length > 0 ? (
                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Source IP</th>
                        <th>Domain / Host</th>
                        <th>Method</th>
                        <th>Intercepted Plaintext Info</th>
                        <th style={{ textAlign: "right" }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {credsLog.map((cred, idx) => {
                        const timeStr = new Date(cred.ts * 1000).toLocaleTimeString();
                        return (
                          <tr key={idx} style={{ background: "rgba(255, 59, 48, 0.02)" }}>
                            <td style={{ fontFamily: "monospace" }}>{timeStr}</td>
                            <td style={{ fontFamily: "monospace" }}>{cred.src_ip}</td>
                            <td style={{ fontWeight: "bold" }}>{cred.host}</td>
                            <td>
                              <span className="badge badge-post">{cred.method || "POST"}</span>
                            </td>
                            <td style={{ fontFamily: "monospace", color: "#ff6b6b", fontWeight: "600" }}>
                              {cred.creds_summary || jsonStringify(cred.credentials || {})}
                            </td>
                            <td style={{ textAlign: "right" }}>
                              <button 
                                className="btn btn-secondary" 
                                style={{ padding: "0.25rem 0.5rem" }}
                                onClick={() => copyToClipboard(jsonStringify(cred.credentials || {}))}
                              >
                                <Copy size={12} /> Copy JSON
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <Key size={48} />
                  <p>Plaintext credentials vault is empty. No passwords or authentication cookies intercepted yet.</p>
                </div>
              )}
            </div>
          )}

          {/* WIFI ATTACKS TAB */}
          {activeTab === "wifi" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              
              {/* Settings Card */}
              <div className="card">
                <div className="card-header">
                  <h3><Wifi size={18} /> WiFi Attack Configuration</h3>
                </div>
                
                <div className="control-grid">
                  <div className="form-group">
                    <label>WiFi Interface</label>
                    <input 
                      type="text" 
                      value={wifiIface} 
                      onChange={(e) => setWifiIface(e.target.value)} 
                      placeholder="e.g. wlan0, wlan0mon"
                    />
                  </div>
                </div>
              </div>

              {/* Rogue AP Evil Twin Card */}
              <div className="card">
                <div className="card-header">
                  <h3> Rogue AP (Evil Twin Network)</h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Create a fake rogue Access Point broadcast matching a target SSID. Nearby clients will connect automatically.
                  </p>
                  
                  <div className="control-grid">
                    <div className="form-group">
                      <label>SSID Name</label>
                      <input 
                        type="text" 
                        value={apSsid} 
                        onChange={(e) => setApSsid(e.target.value)} 
                        placeholder="e.g., Starbucks_WiFi"
                      />
                    </div>
                    <div className="form-group">
                      <label>Channel (1-11)</label>
                      <input 
                        type="number" 
                        min="1" 
                        max="11" 
                        value={apChannel} 
                        onChange={(e) => setApChannel(parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                  
                  <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
                    {runningProcessName === "ap" ? (
                      <button className="btn btn-danger" onClick={handleEmergencyCleanup} style={{ flex: 1 }}>
                        <Square size={16} /> Stop Rogue AP
                      </button>
                    ) : (
                      <button className="btn btn-primary" onClick={handleStartAP} style={{ flex: 1 }} disabled={mitmRunning}>
                        <Play size={16} /> Deploy Rogue AP
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* WiFi Network Scanner */}
              <div className="card">
                <div className="card-header">
                  <h3> WiFi Vulnerability Scanner</h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Scan and record surrounding access points, detecting encryption vulnerability profiles (open, WEP, weak WPA).
                  </p>
                  
                  <div>
                    {runningProcessName === "scan" ? (
                      <button className="btn btn-danger" onClick={handleEmergencyCleanup} style={{ width: "100%" }}>
                        <Square size={16} /> Stop Scanner
                      </button>
                    ) : (
                      <button className="btn btn-primary" onClick={handleStartWiFiScan} style={{ width: "100%" }} disabled={mitmRunning}>
                        <Play size={16} /> Run AP Air Scan
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Deauth Flooder */}
              <div className="card">
                <div className="card-header">
                  <h3> WiFi Deauth Attack</h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Transmit standard deauthentication frames to sever target client connections, forcing them to reconnect to our rogue AP.
                  </p>
                  
                  <div className="control-grid">
                    <div className="form-group">
                      <label>Target MAC Address (Station)</label>
                      <input 
                        type="text" 
                        value={deauthTargetMac} 
                        onChange={(e) => setDeauthTargetMac(e.target.value)} 
                        placeholder="AA:BB:CC:DD:EE:FF"
                      />
                    </div>
                    <div className="form-group">
                      <label>Gateway MAC Address (BSSID - Optional)</label>
                      <input 
                        type="text" 
                        value={deauthGatewayMac} 
                        onChange={(e) => setDeauthGatewayMac(e.target.value)} 
                        placeholder="11:22:33:44:55:66"
                      />
                    </div>
                    <div className="form-group">
                      <label>Access Point SSID (Optional)</label>
                      <input 
                        type="text" 
                        value={deauthSsid} 
                        onChange={(e) => setDeauthSsid(e.target.value)} 
                        placeholder="e.g. Starbucks_WiFi"
                      />
                    </div>
                  </div>
                  
                  <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
                    {runningProcessName === "deauth" ? (
                      <button className="btn btn-danger" onClick={handleEmergencyCleanup} style={{ flex: 1 }}>
                        <Square size={16} /> Stop Deauth flood
                      </button>
                    ) : (
                      <button className="btn btn-primary" onClick={handleStartDeauth} style={{ flex: 1 }} disabled={mitmRunning}>
                        <Play size={16} /> Start Deauth Flood
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* CONFIGURATION PROFILE TAB */}
          {activeTab === "config" && (
            <div className="card">
              <div className="card-header">
                <h3><Settings size={18} /> Configuration Settings Profile</h3>
                <button className="btn btn-primary" onClick={handleSaveConfig} disabled={!wsConnected}>
                  Save Settings
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                
                <div className="control-grid">
                  <div className="form-group">
                    <label>Network Interface</label>
                    <input 
                      type="text" 
                      value={config.interface || ""} 
                      onChange={(e) => setConfig(prev => ({ ...prev, interface: e.target.value }))}
                      placeholder="(Auto-discover)"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Targets (IPs comma-separated)</label>
                    <input 
                      type="text" 
                      value={config.targets || ""} 
                      onChange={(e) => setConfig(prev => ({ ...prev, targets: e.target.value }))}
                      placeholder="e.g. 192.168.1.50, 192.168.1.102"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Default Route Gateway</label>
                    <input 
                      type="text" 
                      value={config.gateway_ip || ""} 
                      onChange={(e) => setConfig(prev => ({ ...prev, gateway_ip: e.target.value }))}
                      placeholder="(Auto-discover)"
                    />
                  </div>
                </div>

                <div style={{ borderTop: "1px solid var(--border-muted)", paddingTop: "1.5rem" }}>
                  <h4 style={{ marginBottom: "1rem" }}>Content Rules & Injection</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    <label className="checkbox-group">
                      <input 
                        type="checkbox" 
                        checked={config.enable_html_banner || false}
                        onChange={(e) => setConfig(prev => ({ ...prev, enable_html_banner: e.target.checked }))}
                      />
                      <span>Inject HTML Warning Warning banner into intercepted websites</span>
                    </label>

                    {config.enable_html_banner && (
                      <div className="form-group" style={{ marginLeft: "1.75rem" }}>
                        <label>Warning Banner Text HTML</label>
                        <input 
                          type="text" 
                          value={config.banner_text || ""} 
                          onChange={(e) => setConfig(prev => ({ ...prev, banner_text: e.target.value }))}
                        />
                      </div>
                    )}

                    <label className="checkbox-group">
                      <input 
                        type="checkbox" 
                        checked={config.enable_image_swap || false}
                        onChange={(e) => setConfig(prev => ({ ...prev, enable_image_swap: e.target.checked }))}
                      />
                      <span>Enable Image replacement rules (Swap unencrypted HTTP images)</span>
                    </label>

                    <label className="checkbox-group">
                      <input 
                        type="checkbox" 
                        checked={config.dns_enabled || false}
                        onChange={(e) => setConfig(prev => ({ ...prev, dns_enabled: e.target.checked }))}
                      />
                      <span>Enable DNS Hijacking/Spoofing rules</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Terminal log drawer */}
        <footer className={`terminal-drawer ${terminalCollapsed ? "collapsed" : ""}`}>
          <div className="terminal-header" onClick={() => setTerminalCollapsed(!terminalCollapsed)}>
            <h4><TermIcon size={14} /> LIVE STDOUT TERMINAL</h4>
            <span style={{ fontSize: "0.8rem" }}>{terminalCollapsed ? "Expand ▲" : "Collapse ▼"}</span>
          </div>
          
          <div className="terminal-content">
            {terminalLines.length > 0 ? (
              terminalLines.map((line, idx) => (
                <div className="terminal-line" key={idx}>{line}</div>
              ))
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                Awaiting terminal logs...
              </div>
            )}
            <div ref={terminalEndRef} />
          </div>
        </footer>
      </main>

      {/* Toast popup */}
      {toast && (
        <div className="toast-msg">
          <Check size={16} style={{ color: toast.type === "error" ? "var(--neon-red)" : "var(--neon-cyan)" }} />
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

export default App;
