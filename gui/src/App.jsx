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
  Layers,
  Globe,
  Database,
  Brain,
  Download,
  ChevronRight,
  Eye,
  Sliders,
  Cpu,
  Lock,
  Unlock,
  Bug,
  BookOpen
} from "lucide-react";
import "./App.css";

// Mock helper data for demo mode
const INITIAL_DEMO_HOSTS = [
  { ip: "192.168.1.1", mac: "00:11:22:33:44:55", vendor: "Cisco Systems", device: "Gateway Router", active: true, os: "Cisco IOS" },
  { ip: "192.168.1.100", mac: "00:0c:29:ab:cd:ef", vendor: "VMware", device: "NEON-SHIELD Host", active: true, os: "Kali Linux" },
  { ip: "192.168.1.105", mac: "a4:cf:99:12:34:56", vendor: "Apple Inc.", device: "Target iPhone 14", active: true, os: "iOS 16.4" },
  { ip: "192.168.1.112", mac: "bc:83:85:67:89:ab", vendor: "Dell Inc.", device: "Target Workstation", active: true, os: "Windows 11 Pro" },
  { ip: "192.168.1.115", mac: "70:ee:50:aa:bb:cc", vendor: "Hikvision", device: "IoT Security Camera", active: true, os: "Embedded Linux" }
];

const MOCK_TRAFFIC_POOL = [
  { method: "GET", host: "unsecure-bank.com", path: "/index.html", src_ip: "192.168.1.112", ts: 0, body: null, headers: { "User-Agent": "Mozilla/5.0", "Accept-Language": "en-US" }, intercepted: false },
  { method: "POST", host: "unsecure-bank.com", path: "/api/login", src_ip: "192.168.1.112", ts: 0, body: "username=jdoe%40megacorp.com&password=SuperSecurePass2026", headers: { "Content-Type": "application/x-www-form-urlencoded", "Cookie": "session_id=8923aed09f" }, intercepted: true },
  { method: "GET", host: "google.com", path: "/search?q=cybersecurity+training", src_ip: "192.168.1.105", ts: 0, body: null, headers: { "User-Agent": "Safari/iPhone", "Host": "www.google.com" }, intercepted: false },
  { method: "GET", host: "office365.corp-login.net", path: "/auth/sso", src_ip: "192.168.1.112", ts: 0, body: null, headers: { "User-Agent": "Chrome/Windows" }, intercepted: false },
  { method: "POST", host: "office365.corp-login.net", path: "/login/process", src_ip: "192.168.1.105", ts: 0, body: "login_hint=admin%40megacorp.com&passwd=WinterGlow%212026&flowToken=fe80", headers: { "Content-Type": "application/x-www-form-urlencoded" }, intercepted: true },
  { method: "GET", host: "company-wiki.local", path: "/wiki/secrets", src_ip: "192.168.1.112", ts: 0, body: null, headers: { "Authorization": "Basic YWRtaW46cGFzc3dvcmQxMjM=" }, intercepted: true },
  { method: "POST", host: "smart-camera-api.local", path: "/stream/snapshot", src_ip: "192.168.1.115", ts: 0, body: "action=capture&resolution=1080p", headers: { "X-API-Key": "cam_dev_key_889201" }, intercepted: true }
];

function App() {
  // Operational Modes: null (selector), "live", "demo"
  const [appMode, setAppMode] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [wsConnected, setWsConnected] = useState(false);
  const [toast, setToast] = useState(null);
  
  // System Info
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
    interface: "eth0",
    targets: "",
    gateway_ip: "192.168.1.1",
    dns_enabled: false,
    dns_redirects: { "google.com": "192.168.1.100", "office365.com": "192.168.1.100" },
    enable_image_swap: false,
    enable_html_banner: true,
    banner_text: "⚡ NEON-SHIELD EDUCATION LAB: Intercepted connection."
  });

  // UI Drawer/Filters
  const [terminalCollapsed, setTerminalCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTrafficItem, setSelectedTrafficItem] = useState(null);
  
  // WiFi Attack States
  const [wifiIface, setWifiIface] = useState("wlan0");
  const [apSsid, setApSsid] = useState("Corporate_Secure_5G");
  const [apChannel, setApChannel] = useState(6);
  const [deauthTargetMac, setDeauthTargetMac] = useState("");
  const [deauthGatewayMac, setDeauthGatewayMac] = useState("00:11:22:33:44:55");
  const [deauthSsid, setDeauthSsid] = useState("Starbucks_WiFi");

  // Web Vulnerability Auditor States
  const [auditorTarget, setAuditorTarget] = useState("http://testphp.vulnweb.com");
  const [auditorScanning, setAuditorScanning] = useState(false);
  const [auditorLogs, setAuditorLogs] = useState([]);
  const [auditorResults, setAuditorResults] = useState(null);
  const [auditorTab, setAuditorTab] = useState("overview");

  // Phishing Portal States
  const [phishingTemplate, setPhishingTemplate] = useState("m365");
  const [phishingRedirect, setPhishingRedirect] = useState("https://portal.office.com");
  const [phishingActive, setPhishingActive] = useState(false);
  const [payloadInjectJS, setPayloadInjectJS] = useState("console.log('Neon-Shield Keylogger Hooked!');");

  // AI Security Report States
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiReport, setAiReport] = useState("");

  // Network / Traffic Inspector States
  const [netInfo, setNetInfo] = useState(null);
  const [trafficStats, setTrafficStats] = useState(null);
  const [trafficProtocolFilter, setTrafficProtocolFilter] = useState("all");
  const [trafficMethodFilter, setTrafficMethodFilter] = useState("all");
  const [trafficInterceptFilter, setTrafficInterceptFilter] = useState("all");

  // Demo Simulation Settings Drawer State
  const [showDemoController, setShowDemoController] = useState(true);
  const [simPacketRate, setSimPacketRate] = useState(1); // packets per 2 seconds

  const ws = useRef(null);
  const terminalEndRef = useRef(null);
  const pendingRequests = useRef({});
  const requestIdCounter = useRef(0);
  const simTimerRef = useRef(null);

  // Show dynamic toast notifications
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Helper to send action with request-response tracking over WS
  const sendAction = (action, params = {}) => {
    if (appMode === "demo") {
      return handleSimulatedAction(action, params);
    }
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      showToast("Not connected to background daemon", "error");
      return Promise.reject("Not connected");
    }
    const id = requestIdCounter.current++;
    const payload = { id, action, params };
    
    return new Promise((resolve, reject) => {
      pendingRequests.current[id] = { resolve, reject };
      ws.current.send(JSON.stringify(payload));
    });
  };

  // WebSocket Connection Lifecycle (Live mode only)
  useEffect(() => {
    if (appMode === "live") {
      connectWebSocket();
    }
    return () => {
      if (ws.current) ws.current.close();
      if (simTimerRef.current) clearInterval(simTimerRef.current);
    };
  }, [appMode]);

  const connectWebSocket = () => {
    console.log("Connecting to daemon...");
    ws.current = new WebSocket("ws://127.0.0.1:8766");

    ws.current.onopen = () => {
      setWsConnected(true);
      showToast("Connected to NEON-SHIELD Daemon", "success");
      sendAction("get_config").then(res => {
        if (res.status === "success") {
          setConfig(res.config);
        }
      });
    };

    ws.current.onclose = () => {
      setWsConnected(false);
      // Try to reconnect in 3s
      setTimeout(() => {
        if (appMode === "live") connectWebSocket();
      }, 3000);
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
            if (data.net_info) setNetInfo(data.net_info);
            setMitmRunning(data.running);
            setRunningProcessName(data.process);
            setStateInfo(data.state);
            if (data.traffic_history) setTrafficLog(data.traffic_history.reverse());
            if (data.creds_history) setCredsLog(data.creds_history.reverse());
            if (data.phish_state) {
              setPhishingActive(!!data.phish_state.active);
              if (data.phish_state.template) {
                setPhishingTemplate(data.phish_state.template);
              }
              if (data.phish_state.redirect_url) {
                setPhishingRedirect(data.phish_state.redirect_url);
              }
            }
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
            showToast("⚠️ CREDENTIALS INTERCEPTED!", "error");
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

  // Demo Simulation Mode Background Loop
  useEffect(() => {
    if (appMode !== "demo") return;
    
    setWsConnected(true);
    setSysInfo({
      interface: "eth0 (simulated)",
      gateway_ip: "192.168.1.1",
      local_ip: "192.168.1.100",
      cidr: "192.168.1.0/24"
    });
    // Populate demo netInfo with realistic WiFi data
    setNetInfo({
      ssid: "Premium", bssid: "B8:85:7B:E8:35:F4", interface: "wlp2s0",
      frequency: "5.18 GHz", channel: "36", signal_dbm: -43,
      signal_quality: 96, bitrate: "585.1 Mb/s", security: "WPA2",
      tx_power: "21 dBm", local_ip: "192.168.1.100",
      gateway: "192.168.1.1", mode: "wifi"
    });
    setDiscoveredHosts(INITIAL_DEMO_HOSTS);

    // Periodic simulation runner
    simTimerRef.current = setInterval(() => {
      if (!mitmRunning) return;

      // Randomly decide to generate a simulated packet traffic
      const rateCheck = Math.random() * 5;
      if (rateCheck < simPacketRate * 2) {
        triggerSimulatedPacket();
      }
    }, 2000);

    return () => {
      if (simTimerRef.current) clearInterval(simTimerRef.current);
    };
  }, [appMode, mitmRunning, simPacketRate]);

  // Fetch fresh network info from daemon
  const fetchNetInfo = () => {
    if (appMode !== "live" || !wsConnected) return;
    sendAction("get_network_info").then(res => {
      if (res.status === "success") setNetInfo(res.data);
    }).catch(() => {});
  };

  // Fetch traffic stats from daemon
  const fetchTrafficStats = () => {
    if (appMode !== "live" || !wsConnected) return;
    sendAction("get_traffic_stats").then(res => {
      if (res.status === "success") setTrafficStats(res.stats);
    }).catch(() => {});
  };



  // Simulated Action Router
  const handleSimulatedAction = (action, params) => {
    console.log(`[SimEngine] Action: ${action}`, params);
    
    if (action === "get_config") {
      return Promise.resolve({ status: "success", config });
    }
    
    else if (action === "save_config") {
      setConfig(params.config);
      return Promise.resolve({ status: "success", message: "Simulated configuration saved" });
    }
    
    else if (action === "scan_network") {
      setScanning(true);
      return new Promise((resolve) => {
        setTimeout(() => {
          setScanning(false);
          resolve({ status: "success", hosts: discoveredHosts });
        }, 1500);
      });
    }

    else if (action === "start_mitm") {
      setMitmRunning(true);
      setRunningProcessName("mitm");
      addTerminalLine("mitm", "Starting ARP Spoofer thread on targets: " + (params.targets || "ALL"));
      addTerminalLine("mitm", "Enabled IP Forwarding rules in kernel (simulated)");
      addTerminalLine("mitm", "Intercept proxy engine listening on port 8080 (HTTP)");
      return Promise.resolve({ status: "success", message: "Simulated MITM Interception activated" });
    }

    else if (action === "stop_mitm" || action === "stop_all") {
      setMitmRunning(false);
      setRunningProcessName(null);
      addTerminalLine("sys", "Restored kernel ARP tables. Stopped proxy servers.");
      return Promise.resolve({ status: "success", message: "All simulated attacks stopped" });
    }

    else if (action === "start_ap") {
      setMitmRunning(true);
      setRunningProcessName("ap");
      addTerminalLine("ap", `Launching hostapd on interface ${params.interface}...`);
      addTerminalLine("ap", `Configuring Rogue BSSID AP broadcasting: SSID "${params.ssid}" on channel ${params.channel}`);
      addTerminalLine("ap", "DHCP Server listening on 192.168.2.1/24 allocating target leases");
      return Promise.resolve({ status: "success", message: "Rogue AP active" });
    }

    else if (action === "scan_wifi") {
      setMitmRunning(true);
      setRunningProcessName("scan");
      addTerminalLine("scan", `Putting ${params.interface} in monitor mode...`);
      addTerminalLine("scan", "Airodump-ng scanner listening for surround channels (1-11)");
      
      // Simulate periodic discoveries in terminal
      let count = 0;
      const scanTimer = setInterval(() => {
        if (runningProcessName !== "scan") {
          clearInterval(scanTimer);
          return;
        }
        count++;
        const ssids = ["Home_Router_Secure", "XfinityWifi_Open", "Netgear88_WPA2", "Starbucks_Att_Guest", "Office_Corporate_WiFi"];
        const randSsid = ssids[Math.floor(Math.random() * ssids.length)];
        const randMac = `00:14:6C:AB:CD:${Math.floor(Math.random() * 80 + 10)}`;
        addTerminalLine("scan", `[Scan AP] Found BSSID ${randMac} | Channel ${Math.floor(Math.random()*11 + 1)} | RSSI -${Math.floor(Math.random()*40 + 40)}dBm | SSID: "${randSsid}"`);
        if (count >= 10) clearInterval(scanTimer);
      }, 1000);

      return Promise.resolve({ status: "success", message: "WiFi scanning started" });
    }

    else if (action === "start_deauth") {
      setMitmRunning(true);
      setRunningProcessName("deauth");
      addTerminalLine("deauth", `Initializing Aireplay-ng deauth attack on target [${params.target_mac}]`);
      addTerminalLine("deauth", `Broadcasting spoofed disassociation frames through AP [${params.gateway_mac || "Any"}]`);
      return Promise.resolve({ status: "success", message: "WiFi deauth flood active" });
    }

    return Promise.reject("Simulated action not mapped: " + action);
  };

  // Helper to push stdout-like strings to the log console
  const addTerminalLine = (proc, text) => {
    setTerminalLines(prev => [...prev, `[${proc.toUpperCase()}] ${text}`].slice(-200));
  };

  // Trigger Simulated Events from the operator panel
  const triggerSimulatedPacket = () => {
    const item = { ...MOCK_TRAFFIC_POOL[Math.floor(Math.random() * MOCK_TRAFFIC_POOL.length)] };
    item.ts = Math.floor(Date.now() / 1000);
    
    // Randomize source IP from targets
    const hosts = discoveredHosts.filter(h => h.ip !== "192.168.1.1" && h.ip !== "192.168.1.100");
    if (hosts.length > 0) {
      item.src_ip = hosts[Math.floor(Math.random() * hosts.length)].ip;
    }

    setTrafficLog(prev => [item, ...prev].slice(0, 500));
    addTerminalLine("proxy", `Intercepted: ${item.method} http://${item.host}${item.path} from ${item.src_ip}`);

    // If it's a POST request that was decrypted, trigger a credential capture
    if (item.method === "POST" && item.intercepted) {
      setTimeout(() => {
        const credItem = {
          ts: Math.floor(Date.now() / 1000),
          src_ip: item.src_ip,
          host: item.host,
          method: "POST",
          creds_summary: item.body,
          credentials: {
            identity: item.body.includes("username=") ? decodeURIComponent(item.body.split("username=")[1].split("&")[0]) : "admin@megacorp.com",
            secret: item.body.includes("password=") ? decodeURIComponent(item.body.split("password=")[1].split("&")[0]) : "Welcome2026!",
            raw: item.body
          }
        };
        setCredsLog(prev => [credItem, ...prev].slice(0, 200));
        showToast(`⚠️ CREDENTIAL CAPTURED FROM ${credItem.host}!`, "error");
        addTerminalLine("creds", `Captured plaintext secret from ${item.src_ip} -> User: ${credItem.credentials.identity}`);
      }, 1500);
    }
  };

  const triggerSimulatedHost = () => {
    const ips = ["192.168.1.130", "192.168.1.144", "192.168.1.201"];
    const macs = ["80:ea:96:11:22:33", "2c:f0:ee:44:55:66", "b8:27:eb:77:88:99"];
    const devices = ["Android Tablet", "Google Pixel Phone", "Raspberry Pi Lab"];
    const vendors = ["Samsung", "Google Inc.", "Raspberry Pi Foundation"];
    const osList = ["Android 13", "Android 14", "Raspbian OS"];

    const activeIPs = discoveredHosts.map(h => h.ip);
    const availableIndex = ips.findIndex(ip => !activeIPs.includes(ip));
    
    if (availableIndex === -1) {
      showToast("All mock hosts already added", "error");
      return;
    }

    const newHost = {
      ip: ips[availableIndex],
      mac: macs[availableIndex],
      vendor: vendors[availableIndex],
      device: devices[availableIndex],
      active: true,
      os: osList[availableIndex]
    };

    setDiscoveredHosts(prev => [...prev, newHost]);
    showToast(`Discovered new host: ${newHost.ip} (${newHost.device})`, "success");
    addTerminalLine("arp", `Subnet Scan: Detected new node active at ${newHost.ip} [${newHost.mac}]`);
  };

  // Commands triggers
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
        showToast("MITM Interception stopped cleanly");
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
    showToast(`Interception target list set: ${targetsStr}`);
    setActiveTab("dashboard");
  };

  const handleSaveConfig = () => {
    sendAction("save_config", { config }).then(res => {
      if (res.status === "success") {
        showToast("Settings profiles successfully saved.");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  // WiFi Attack triggers
  const handleStartAP = () => {
    sendAction("start_ap", {
      interface: wifiIface,
      ssid: apSsid,
      channel: apChannel
    }).then(res => {
      if (res.status === "success") {
        showToast(`Rogue Access Point deployed: "${apSsid}"`);
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
        showToast("Air Monitor scan started. Inspect stdout console.");
        setMitmRunning(true);
        setRunningProcessName("scan");
      } else {
        showToast(res.message, "error");
      }
    });
  };

  const handleStartDeauth = () => {
    if (!deauthTargetMac) {
      showToast("Please enter target station MAC address", "error");
      return;
    }
    sendAction("start_deauth", {
      interface: wifiIface,
      target_mac: deauthTargetMac,
      gateway_mac: deauthGatewayMac,
      ssid: deauthSsid
    }).then(res => {
      if (res.status === "success") {
        showToast(`Deauth frame stream started on MAC ${deauthTargetMac}`);
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

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    showToast("Copied content to clipboard", "success");
  };

  // Web Vulnerability Auditor scan trigger
  const runWebAuditorScan = () => {
    if (!auditorTarget) {
      showToast("Please enter a valid website URL", "error");
      return;
    }
    setAuditorScanning(true);
    setAuditorLogs([]);
    setAuditorResults(null);
    setAuditorTab("overview");

    const steps = [
      `Initiating Web Auditor Scan on target: ${auditorTarget}...`,
      "Resolving DNS Records & testing ping responsiveness...",
      "Analyzing SSL/TLS Handshake protocols and cipher suites...",
      "Crawling index directories for hidden secrets, backups, and configs...",
      "Fuzzing forms for Cross-Site Scripting (XSS) payload reflections...",
      "Scanning API endpoints for SQL Injection vulnerabilities...",
      "Auditing HTTP Response headers (CSP, HSTS, CORS configuration)...",
      "Compiling final cybersecurity audit report..."
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        setAuditorLogs(prev => [...prev, `[AUDITOR] ${steps[currentStep]}`]);
        addTerminalLine("auditor", steps[currentStep]);
        currentStep++;
      } else {
        clearInterval(interval);
        
        if (appMode === "live" && wsConnected) {
          sendAction("scan_website", { target: auditorTarget })
            .then(res => {
              setAuditorScanning(false);
              if (res.status === "success") {
                setAuditorResults({
                  target: res.target,
                  score: res.score,
                  stats: res.stats,
                  vulnerabilities: res.vulnerabilities,
                  database_compromise: res.database_compromise,
                  report_text: res.report_text
                });
                showToast("Vulnerability scan complete!", "success");
              } else {
                showToast(res.message, "error");
              }
            })
            .catch(err => {
              setAuditorScanning(false);
              showToast("Backend scan failed: " + (err.message || err), "error");
            });
        } else {
          // Demo Mode fallback
          setAuditorScanning(false);
          setAuditorResults({
            target: auditorTarget,
            score: 34,
            stats: { critical: 2, high: 1, medium: 2, low: 3 },
            vulnerabilities: [
              {
                id: "vuln-01",
                severity: "critical",
                title: "SQL Injection (SQLi)",
                location: "GET /api/v1/products?category=",
                description: "Input parameter is not sanitized before database query assembly. Attacker can inject arbitrary SQL commands to dump user credentials and bypass OAuth profiles.",
                remediation: "Implement Prepared Statements / Parameterized Queries on API database connection adapters. Avoid direct raw string concatenation.",
                exploit_simulated: true,
                dump: [
                  { id: 1, username: "admin@megacorp.com", pass_hash: "$2y$12$R9h/lS7vL9aB9eB9dCeFgO12k34j56l78m90" },
                  { id: 2, username: "jdoe@megacorp.com", pass_hash: "$2y$12$K1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8" },
                  { id: 3, username: "operator_bill@megacorp.com", pass_hash: "$2y$12$P9q8r7s6t5u4v3w2x1y0z_auth_pass_hash" }
                ]
              },
              {
                id: "vuln-02",
                severity: "critical",
                title: "Hardcoded API Access Keys",
                location: "GET /js/app.min.js (Line 2450)",
                description: "Plaintext cloud credentials found in client-side script code.",
                remediation: "Revoke credentials immediately. Migrate cloud key parameters to environment configurations managed on secured gateway layers.",
                keys: [
                  { type: "AWS Access Key ID", key: "AKIAIOSFODNN7EXAMPLE" },
                  { type: "Supabase Service Role JWT", key: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVs" }
                ]
              },
              {
                id: "vuln-03",
                severity: "high",
                title: "Exposed Git Repository Configuration",
                location: "GET /.git/config",
                description: "Web server hosts development directory metadata. Exposure permits reconstruction of source code repository files.",
                remediation: "Configure nginx/apache rewrite profiles to return a 403 Forbidden index for all dot-prefix folders.",
              },
              {
                id: "vuln-04",
                severity: "medium",
                title: "Outdated JavaScript Library Dependencies",
                location: "jQuery v1.12.4",
                description: "Library contains multiple CVE advisories related to cross-site scripting (XSS) exploit vectors.",
                remediation: "Upgrade library dependencies to the latest stable packages."
              },
              {
                id: "vuln-05",
                severity: "medium",
                title: "Weak TLS Cipher Configuration",
                location: "TLS v1.0 & TLS v1.1 Enabled",
                description: "Server accepts deprecated SSL/TLS protocols subject to session spoofing attacks.",
                remediation: "Enforce TLS v1.2 and TLS v1.3 profiles on SSL configurations."
              },
              {
                id: "vuln-06",
                severity: "low",
                title: "Missing Security Headers",
                location: "HTTP/1.1 headers",
                description: "Response lacks X-Frame-Options, Content-Security-Policy (CSP), and Strict-Transport-Security (HSTS).",
                remediation: "Append security headers in proxy proxy configs."
              }
            ]
          });
          showToast("Vulnerability scan complete!", "success");
        }
      }
    }, 600);
  };

  // AI Security Report Generator
  const generateAIReport = () => {
    setAiAnalyzing(true);
    setAiReport("");
    
    // Simulate generation delay
    setTimeout(() => {
      setAiAnalyzing(false);
      const hostCount = discoveredHosts.length;
      const credCount = credsLog.length;
      const trafficCount = trafficLog.length;
      
      const markdown = `# NEON-SHIELD EXECUTIVE THREAT INTEL REPORT
**Generated:** ${new Date().toLocaleString()}
**Classification:** Restricted (Educational SOC)
**Platform Mode:** ${appMode.toUpperCase()}

## 1. Executive Summary
The security audit session analyzed local networks and active web domains. During the monitoring period, a total of **${hostCount} target hosts** were discovered on the active subnets. Active MitM proxying and Rogue Access Point spoofing intercepted **${trafficCount} packet streams** and harvested **${credCount} plaintext credential profiles**.

## 2. Threat Vector Topology Mapping
The active attack path demonstrates typical credential-harvesting vectors:
1. **WiFi Reconnaissance**: Scanner identified surround access points.
2. **Deauth Force-Disconnect**: Target hosts were disassociated from legitimate AP networks.
3. **Evil Twin Deployment**: A Rogue AP broadcasting target SSIDs captured connection routes.
4. **Credential Harvesting**: Target logged into cloned forms hosted at our phishing interface, capturing plaintext authorization keys.

## 3. Incident Findings & Metric Indicators
* **Network Intercept Level**: High (ARP tables fully spoofed)
* **Secret Leaks Indexed**: ${credCount > 0 ? "CRITICAL RISK - Plaintext passwords leaked in transit" : "LOW RISK - No credentials harvested yet"}
* **Vulnerable Protocols**: Unencrypted HTTP traffic discovered on target domain profiles.

## 4. Remediation Action Plan
* **Implement WPA3 Enterprise**: Protect client hosts from deauth vectors and fake access point associations.
* **Force HTTPS/HSTS Profiles**: Secure login packets using encryption ciphers, rendering local network sniffers ineffective.
* **Employee Security Awareness**: Educate operators to audit SSL certificate domains before inputting corporate passwords.

---
*Neon-Shield Cyber Analyst Engine v2.0*`;
      
      setAiReport(markdown);
      showToast("AI Threat Report successfully compiled", "success");
    }, 2000);
  };

  const downloadAIReport = () => {
    if (!aiReport) return;
    const element = document.createElement("a");
    const file = new Blob([aiReport], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = "neon_shield_threat_report.md";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    showToast("Report saved to downloads folder");
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

  // Main UI Screen Renderer
  return (
    <div className="app-container">
      <div className="glow-effect"></div>
      
      {/* Startup Boot Mode Overlay */}
      {appMode === null && (
        <div className="boot-modal-overlay">
          <div className="boot-modal-content">
            <div className="boot-logo-container">
              <div className="boot-logo-glow">
                <Shield size={36} />
              </div>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              <h2 style={{ fontSize: "1.5rem", fontWeight: "900", letterSpacing: "0.05em", color: "#fff" }}>NEON-SHIELD</h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Cybersecurity Operations Control Panel v2.0</p>
            </div>

            <div className="boot-options-grid">
              <div 
                className="boot-option-card"
                onClick={() => {
                  setAppMode("live");
                  showToast("Launching Live SOC operations...");
                }}
              >
                <div className="boot-option-title" style={{ color: "var(--neon-cyan)" }}>
                  <Activity size={16} className="logo-glow" /> LIVE OPERATIONS MODE
                </div>
                <div className="boot-option-desc">
                  Connect to local Python daemon (ws://127.0.0.1:8765) to run real-world network auditing, rogue AP scans, and deauth vectors. Requires sudo.
                </div>
              </div>

              <div 
                className="boot-option-card"
                onClick={() => {
                  setAppMode("demo");
                  showToast("Starting offline demonstration mode...");
                }}
              >
                <div className="boot-option-title" style={{ color: "var(--neon-rose)" }}>
                  <Play size={16} style={{ color: "var(--neon-rose)", filter: "drop-shadow(0 0 5px var(--neon-rose))" }} /> PRESENTATION & DEMO MODE
                </div>
                <div className="boot-option-desc">
                  Run simulated local networks, discovered targets, automated HTTP traffic logs, credential captures, and reports. No daemon required.
                </div>
              </div>
            </div>

            <div style={{ color: "var(--text-muted)", fontSize: "0.7rem", lineHeight: "1.4" }}>
              WARNING: This tool is intended for controlled academic demonstrations and authorized security audits only. Please read guidelines before use.
            </div>
          </div>
        </div>
      )}

      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header" onClick={() => setAppMode(null)} style={{ cursor: "pointer" }}>
          <Shield className="logo-glow" size={24} />
          <h2>NEON-SHIELD</h2>
          {appMode === "demo" && <span className="demo-control-badge">Demo</span>}
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
            className={`nav-item ${activeTab === "topology" ? "active" : ""}`}
            onClick={() => setActiveTab("topology")}
          >
            <Layers size={18} />
            Topology Map
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
            <Eye size={18} />
            Traffic Inspector
          </div>

          <div 
            className={`nav-item ${activeTab === "auditor" ? "active" : ""}`}
            onClick={() => setActiveTab("auditor")}
          >
            <Globe size={18} />
            Vulnerability Auditor
          </div>

          <div 
            className={`nav-item ${activeTab === "phishing" ? "active" : ""}`}
            onClick={() => setActiveTab("phishing")}
          >
            <Database size={18} />
            Payload & Phishing
          </div>
          
          <div 
            className={`nav-item ${activeTab === "wifi" ? "active" : ""}`}
            onClick={() => setActiveTab("wifi")}
          >
            <Wifi size={18} />
            WiFi Attack Hub
          </div>

          <div 
            className={`nav-item ${activeTab === "ai" ? "active" : ""}`}
            onClick={() => setActiveTab("ai")}
          >
            <Brain size={18} />
            AI Analyst Reports
          </div>
          
          <div 
            className={`nav-item ${activeTab === "config" ? "active" : ""}`}
            onClick={() => setActiveTab("config")}
          >
            <Settings size={18} />
            Settings
          </div>
        </nav>
        
        <div className="sidebar-footer">
          <div className="status-badge" onClick={() => setAppMode(null)} style={{ cursor: "pointer" }}>
            <span className={`dot ${wsConnected ? "running" : "stopped"}`}></span>
            SOC Mode: {appMode ? appMode.toUpperCase() : "BOOTING"}
          </div>
          
          <div className="status-badge">
            <span className={`dot ${mitmRunning ? "running" : "stopped"}`}></span>
            Attack Status: {mitmRunning ? `ACTIVE (${runningProcessName.toUpperCase()})` : "IDLE"}
          </div>
        </div>
      </aside>
      
      {/* Main Container */}
      <main className="main-content">
        {/* Header */}
        <header className="main-header">
          <div className="header-title">
            <h1 style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              {activeTab === "dashboard" && "Control Center Overview"}
              {activeTab === "topology" && "Interactive Network Topology"}
              {activeTab === "discovery" && "Subnet Host Discovery"}
              {activeTab === "traffic" && "HTTP/HTTPS Stream Inspector"}
              {activeTab === "auditor" && "Website Vulnerability Auditor"}
              {activeTab === "phishing" && "Payload Deployment & Phishing"}
              {activeTab === "wifi" && "WiFi Attack Interface"}
              {activeTab === "ai" && "AI Threat Intelligence Analyst"}
              {activeTab === "config" && "Configuration Profiles"}
            </h1>
          </div>
          
          <div className="system-stats">
            <div className="stat-item">
              <span className="stat-label">NIC Interface</span>
              <span className="stat-val">{sysInfo.interface}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Local Host IP</span>
              <span className="stat-val">{sysInfo.local_ip}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Route Gateway</span>
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
              <strong>EDUCATIONAL SANDBOX NOTIFICATION.</strong> Intercepting data or scanning assets without permission violates computing guidelines. Use this console in authorized lab setups only.
            </span>
          </div>

          {/* DASHBOARD CONTROL CENTER */}
          {activeTab === "dashboard" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div className="landing-grid">
                
                <div className="landing-card" onClick={() => setActiveTab("topology")}>
                  <div className="landing-card-header">
                    <span className="landing-card-title">Network Topology</span>
                    <span className="landing-card-icon"><Layers size={18} /></span>
                  </div>
                  <div>
                    <div className="landing-card-value">{discoveredHosts.length} Nodes</div>
                    <div className="landing-card-desc">Active target nodes discovered on network segments.</div>
                  </div>
                </div>

                <div className="landing-card" onClick={() => setActiveTab("traffic")}>
                  <div className="landing-card-header">
                    <span className="landing-card-title">Intercepted Traffic</span>
                    <span className="landing-card-icon"><Eye size={18} /></span>
                  </div>
                  <div>
                    <div className="landing-card-value">{trafficLog.length} Packets</div>
                    <div className="landing-card-desc">HTTP/HTTPS data requests captured.</div>
                  </div>
                </div>

                <div className="landing-card red-indicator" onClick={() => setActiveTab("traffic")}>
                  <div className="landing-card-header">
                    <span className="landing-card-title">Captured Credentials</span>
                    <span className="landing-card-icon" style={{ color: "var(--neon-rose)" }}><Key size={18} /></span>
                  </div>
                  <div>
                    <div className="landing-card-value" style={{ color: "var(--neon-rose)" }}>{credsLog.length} Plaintext</div>
                    <div className="landing-card-desc">Plaintext passwords harvested from login submissions.</div>
                  </div>
                </div>

                <div className="landing-card" onClick={() => setActiveTab("auditor")}>
                  <div className="landing-card-header">
                    <span className="landing-card-title">Vulnerability Auditor</span>
                    <span className="landing-card-icon"><Globe size={18} /></span>
                  </div>
                  <div>
                    <div className="landing-card-value">
                      {auditorResults ? `${auditorResults.score}/100 Score` : "Not Scanned"}
                    </div>
                    <div className="landing-card-desc">Website exploit metrics and SQLi scanners.</div>
                  </div>
                </div>
              </div>

              <div className="grid-col-2">
                {/* MITM Proxy Control Card */}
                <div className="card">
                  <div className="card-header">
                    <h3><Shield size={18} className="logo-glow" /> Interceptor Proxy Control</h3>
                  </div>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: "1.4" }}>
                      Run ARP spoof rules to poison router caches, routing data from selected target nodes through Neon-Shield.
                    </p>
                    
                    <div style={{ background: "rgba(255, 255, 255, 0.02)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-muted)" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "0.5rem" }}>
                        <div>
                          <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Target list</div>
                          <div style={{ fontFamily: "monospace", fontSize: "0.85rem", fontWeight: "bold" }}>
                            {config.targets ? config.targets : "Auto-routing all subnet"}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Gateway Target</div>
                          <div style={{ fontFamily: "monospace", fontSize: "0.85rem", fontWeight: "bold" }}>
                            {sysInfo.gateway_ip} ({sysInfo.interface})
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div style={{ display: "flex", gap: "1rem" }}>
                      {mitmRunning ? (
                        <button className="btn btn-danger" style={{ flex: 1 }} onClick={handleStopMITM}>
                          <Square size={16} /> Terminate Hijack
                        </button>
                      ) : (
                        <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleStartMITM} disabled={!wsConnected}>
                          <Play size={16} /> Execute ARP Spoof
                        </button>
                      )}
                      
                      <button className="btn btn-secondary" onClick={handleEmergencyCleanup}>
                        <RefreshCw size={16} /> Reset NIC
                      </button>
                    </div>
                  </div>
                </div>

                {/* Operations logs timeline */}
                <div className="card" style={{ display: "flex", flexDirection: "column", maxHeight: "310px" }}>
                  <div className="card-header">
                    <h3>🛡️ MITM Status Panel</h3>
                  </div>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem", fontSize: "0.825rem", overflowY: "auto", flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.02)", paddingBottom: "0.5rem" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Spoofer state:</span>
                      <span style={{ color: mitmRunning ? "var(--neon-green)" : "var(--neon-red)", fontWeight: "bold" }}>
                        {mitmRunning ? "ACTIVE MITM" : "IDLE"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.02)", paddingBottom: "0.5rem" }}>
                      <span style={{ color: "var(--text-secondary)" }}>DNS Spoof rules:</span>
                      <span style={{ color: config.dns_enabled ? "var(--neon-green)" : "var(--text-muted)" }}>
                        {config.dns_enabled ? "RESOLVED (SPOOFED)" : "FORWARDED (BYPASS)"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.02)", paddingBottom: "0.5rem" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Image Swapping:</span>
                      <span style={{ color: config.enable_image_swap ? "var(--neon-cyan)" : "var(--text-muted)" }}>
                        {config.enable_image_swap ? "ENABLED" : "DISABLED"}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid rgba(255,255,255,0.02)", paddingBottom: "0.5rem" }}>
                      <span style={{ color: "var(--text-secondary)" }}>HTML Inject warnings:</span>
                      <span style={{ color: config.enable_html_banner ? "var(--neon-cyan)" : "var(--text-muted)" }}>
                        {config.enable_html_banner ? "INJECTING" : "DISABLED"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* NETWORK TOPOLOGY TAB */}
          {activeTab === "topology" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div className="card">
                <div className="card-header">
                  <h3>Interactive Network Topology & Intercept Flow</h3>
                  <div>
                    {mitmRunning && <span className="demo-control-badge" style={{ background: "rgba(0,230,118,0.1)", color: "var(--neon-green)", borderColor: "rgba(0,230,118,0.3)" }}>Interception Stream Active</span>}
                  </div>
                </div>
                
                <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                  Visual mapping of local subnet hosts. Dynamic lines with flowing particles depict data packets moving to the gateway router, hijacked via ARP spoofing.
                </p>

                <div className="topology-container">
                  <div className="topology-radar-line"></div>
                  
                  <svg width="100%" height="100%" style={{ minHeight: "350px" }}>
                    {/* SVG Filters for Glow Effects */}
                    <defs>
                      <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                      </filter>
                      <filter id="glow-rose" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                      </filter>
                    </defs>

                    {/* Topology Links & Packets */}
                    {discoveredHosts.filter(h => h.ip !== "192.168.1.1" && h.ip !== "192.168.1.100").map((host, idx) => {
                      const angle = (idx * (Math.PI / 2.5)) + 0.5; // Spread targets in arc
                      const targetX = 180 + Math.cos(angle) * 160;
                      const targetY = 180 + Math.sin(angle) * 110;
                      
                      // Paths
                      const pathId = `path-host-${idx}`;
                      const reversePathId = `path-rev-${idx}`;

                      return (
                        <g key={idx}>
                          {/* Target to Attacker Link (Intercept Route) */}
                          <path
                            id={pathId}
                            d={`M ${targetX} ${targetY} Q ${(targetX + 450)/2} ${(targetY + 280)/2 - 30} 450 280`}
                            fill="none"
                            className={`topology-link ${mitmRunning ? "active-flow" : ""}`}
                          />
                          
                          {/* Attacker to Gateway Link */}
                          <path
                            id={reversePathId}
                            d={`M 450 280 Q 450 170 450 60`}
                            fill="none"
                            className={`topology-link ${mitmRunning ? "active-flow" : ""}`}
                          />

                          {/* Packet flows if MITM active */}
                          {mitmRunning && (
                            <>
                              <circle r="4" className="packet-dot">
                                <animateMotion dur="3s" repeatCount="indefinite" path={`M ${targetX} ${targetY} Q ${(targetX + 450)/2} ${(targetY + 280)/2 - 30} 450 280`} />
                              </circle>
                              <circle r="4" className="packet-dot" style={{ fill: "var(--neon-rose)" }}>
                                <animateMotion dur="2s" begin="1s" repeatCount="indefinite" path={`M 450 280 Q 450 170 450 60`} />
                              </circle>
                            </>
                          )}
                        </g>
                      );
                    })}

                    {/* Nodes Visual Elements */}
                    
                    {/* Gateway Node (Top Center) */}
                    <g transform="translate(450, 60)" className="topology-node">
                      <circle r="22" fill="#0c0e17" stroke="var(--neon-blue)" strokeWidth="2" filter="url(#glow-cyan)" />
                      <path d="M-8 -6 L8 -6 M-8 0 L8 0 M-8 6 L8 6" stroke="var(--neon-blue)" strokeWidth="2" fill="none" />
                      <text y="35" textAnchor="middle" fill="var(--text-primary)" fontSize="10.5" fontWeight="bold">Router Gateway</text>
                      <text y="48" textAnchor="middle" fill="var(--neon-cyan)" fontSize="9" fontFamily="monospace">192.168.1.1</text>
                    </g>

                    {/* Attacker Node (Bottom Center) */}
                    <g transform="translate(450, 280)" className="topology-node">
                      <circle r="26" fill="#0c0e17" stroke="var(--neon-rose)" strokeWidth="2.5" filter="url(#glow-rose)" />
                      <path d="M-10 -10 L10 10 M10 -10 L-10 10" stroke="var(--neon-rose)" strokeWidth="2" />
                      <text y="40" textAnchor="middle" fill="var(--text-primary)" fontSize="11" fontWeight="bold">NEON-SHIELD</text>
                      <text y="53" textAnchor="middle" fill="var(--neon-rose)" fontSize="9.5" fontFamily="monospace">192.168.1.100</text>
                    </g>

                    {/* Discovered Target Nodes */}
                    {discoveredHosts.filter(h => h.ip !== "192.168.1.1" && h.ip !== "192.168.1.100").map((host, idx) => {
                      const angle = (idx * (Math.PI / 2.5)) + 0.5;
                      const targetX = 180 + Math.cos(angle) * 160;
                      const targetY = 180 + Math.sin(angle) * 110;

                      return (
                        <g key={idx} transform={`translate(${targetX}, ${targetY})`} className="topology-node" onClick={() => {
                          showToast(`Selected Node: ${host.ip} (${host.device})`);
                        }}>
                          <circle r="18" fill="#0c0e17" stroke="var(--neon-cyan)" strokeWidth="1.5" />
                          <circle r="4" fill="var(--neon-green)" cx="10" cy="-10" />
                          <text y="28" textAnchor="middle" fill="var(--text-secondary)" fontSize="10">{host.device}</text>
                          <text y="38" textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontFamily="monospace">{host.ip}</text>
                        </g>
                      );
                    })}
                  </svg>
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

              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
                Scan the active CIDR segment <strong>{sysInfo.cidr}</strong> via interface <strong>{sysInfo.interface}</strong> to discover live targets.
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
                          <th>Vendor / Manufacture</th>
                          <th>Device Guess</th>
                          <th>OS Profile</th>
                        </tr>
                      </thead>
                      <tbody>
                        {discoveredHosts.map((host) => {
                          const isGateway = host.ip === "192.168.1.1";
                          const isSelf = host.ip === "192.168.1.100" || host.ip === sysInfo.local_ip;
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
                                {isGateway && <span style={{ color: "var(--neon-yellow)", fontSize: "0.7rem", marginLeft: "0.5rem" }}>(Gateway)</span>}
                                {isSelf && <span style={{ color: "var(--neon-cyan)", fontSize: "0.7rem", marginLeft: "0.5rem" }}>(Local Host)</span>}
                              </td>
                              <td style={{ fontFamily: "monospace" }}>{host.mac}</td>
                              <td>{host.vendor}</td>
                              <td>{host.device}</td>
                              <td style={{ color: "var(--neon-blue)", fontSize: "0.8rem", fontWeight: "600" }}>{host.os || "Unknown"}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
                    <button className="btn btn-secondary" onClick={() => setSelectedTargets([])}>
                      Reset Filters
                    </button>
                    <button 
                      className="btn btn-primary" 
                      onClick={handleApplyDiscoveredTargets}
                      disabled={selectedTargets.length === 0}
                    >
                      Targets Selected ({selectedTargets.length})
                    </button>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <Users size={48} />
                  <p>{scanning ? "ARP querying subnet packets..." : "No scan data loaded yet. Run a network scan to discover target devices."}</p>
                </div>
              )}
            </div>
          )}

          {/* TRAFFIC INSPECTOR TAB */}
          {activeTab === "traffic" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

              {/* WiFi / Network Context Banner */}
              {netInfo && (
                <div style={{ background: "linear-gradient(135deg, rgba(0,242,254,0.05), rgba(0,242,254,0.02))", border: "1px solid var(--border-cyan)", borderRadius: "12px", padding: "1rem 1.25rem", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <Wifi size={22} style={{ color: netInfo.ssid ? "var(--neon-cyan)" : "var(--text-muted)" }} />
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "1rem", color: netInfo.ssid ? "#fff" : "var(--text-secondary)" }}>
                        {netInfo.ssid || (netInfo.mode === "ethernet" ? "Ethernet" : "Not connected")}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", fontFamily: "monospace" }}>
                        {netInfo.bssid || "—"} {netInfo.channel ? `· Ch ${netInfo.channel}` : ""} {netInfo.frequency ? `· ${netInfo.frequency}` : ""}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                    {netInfo.signal_quality != null && (
                      <div style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.2rem" }}>Signal</div>
                        <div style={{ display: "flex", gap: "2px", alignItems: "flex-end", height: "18px" }}>
                          {[25, 50, 75, 100].map((t, i) => (
                            <div key={i} style={{ width: "5px", height: `${(i+1)*4+4}px`, borderRadius: "1px", background: netInfo.signal_quality >= t ? "var(--neon-cyan)" : "rgba(255,255,255,0.1)" }} />
                          ))}
                          <span style={{ marginLeft: "6px", fontFamily: "monospace", fontSize: "0.75rem", color: "var(--neon-cyan)" }}>{netInfo.signal_dbm} dBm</span>
                        </div>
                      </div>
                    )}
                    {netInfo.bitrate && (
                      <div style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.2rem" }}>Bitrate</div>
                        <div style={{ fontFamily: "monospace", fontSize: "0.8rem", color: "#fff", fontWeight: "600" }}>{netInfo.bitrate}</div>
                      </div>
                    )}
                    {netInfo.security && (
                      <div style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.2rem" }}>Security</div>
                        <span style={{ background: "rgba(0,230,118,0.1)", color: "var(--neon-green)", border: "1px solid rgba(0,230,118,0.3)", borderRadius: "4px", padding: "0.1rem 0.4rem", fontSize: "0.72rem", fontWeight: "700" }}>{netInfo.security}</span>
                      </div>
                    )}
                    {netInfo.local_ip && (
                      <div style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.2rem" }}>Local IP</div>
                        <div style={{ fontFamily: "monospace", fontSize: "0.78rem", color: "var(--neon-cyan)" }}>{netInfo.local_ip}</div>
                      </div>
                    )}
                    {netInfo.gateway && (
                      <div style={{ textAlign: "center" }}>
                        <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.2rem" }}>Gateway</div>
                        <div style={{ fontFamily: "monospace", fontSize: "0.78rem", color: "#fff" }}>{netInfo.gateway}</div>
                      </div>
                    )}
                    <button className="btn btn-secondary" style={{ padding: "0.25rem 0.6rem", fontSize: "0.7rem", alignSelf: "center" }} onClick={fetchNetInfo}>
                      <RefreshCw size={11} /> Refresh
                    </button>
                  </div>
                </div>
              )}

              {/* Live Stats Row */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem" }}>
                {[
                  { label: "Total Packets", value: trafficLog.length, color: "var(--neon-cyan)" },
                  { label: "Intercepted", value: trafficLog.filter(t => t.intercepted).length, color: "var(--neon-rose)" },
                  { label: "POST Requests", value: trafficLog.filter(t => (t.method || "").toUpperCase() === "POST").length, color: "#f59e0b" },
                  { label: "HTTPS Sessions", value: trafficLog.filter(t => t.protocol === "https").length, color: "var(--neon-green)" },
                  { label: "Data Captured", value: (() => { const b = trafficLog.reduce((s,t) => s + (t.size || 0), 0); return b > 1048576 ? (b/1048576).toFixed(1)+"MB" : (b/1024).toFixed(1)+"KB"; })(), color: "#a78bfa" },
                  { label: "Unique Hosts", value: new Set(trafficLog.map(t => t.host || t.domain)).size, color: "#38bdf8" },
                ].map(s => (
                  <div key={s.label} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-muted)", borderRadius: "10px", padding: "0.75rem 1rem" }}>
                    <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.25rem" }}>{s.label}</div>
                    <div style={{ fontFamily: "monospace", fontWeight: "800", fontSize: "1.3rem", color: s.color }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Filters + Search Row */}
              <div className="card" style={{ padding: "0.75rem 1rem" }}>
                <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
                  <div style={{ position: "relative" }}>
                    <Search style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} size={14} />
                    <input
                      type="text"
                      placeholder="Filter host, path, IP..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ paddingLeft: "2rem", width: "200px", background: "var(--bg-input)", border: "1px solid var(--border-muted)", color: "#fff", borderRadius: "8px", height: "34px", fontSize: "0.82rem" }}
                    />
                  </div>
                  <div style={{ display: "flex", gap: "0.4rem" }}>
                    {["all","http","https"].map(p => (
                      <button key={p} onClick={() => setTrafficProtocolFilter(p)}
                        style={{ padding: "0.2rem 0.65rem", borderRadius: "20px", fontSize: "0.72rem", fontWeight: "600", border: `1px solid ${trafficProtocolFilter === p ? "var(--neon-cyan)" : "var(--border-muted)"}`, background: trafficProtocolFilter === p ? "rgba(0,242,254,0.1)" : "transparent", color: trafficProtocolFilter === p ? "var(--neon-cyan)" : "var(--text-secondary)", cursor: "pointer" }}>
                        {p.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: "0.4rem" }}>
                    {["all","GET","POST","PUT","DELETE"].map(m => (
                      <button key={m} onClick={() => setTrafficMethodFilter(m)}
                        style={{ padding: "0.2rem 0.65rem", borderRadius: "20px", fontSize: "0.72rem", fontWeight: "600", border: `1px solid ${trafficMethodFilter === m ? "#f59e0b" : "var(--border-muted)"}`, background: trafficMethodFilter === m ? "rgba(245,158,11,0.1)" : "transparent", color: trafficMethodFilter === m ? "#f59e0b" : "var(--text-secondary)", cursor: "pointer" }}>
                        {m}
                      </button>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: "0.4rem" }}>
                    {[["all","All"],["intercepted","Intercepted"],["clean","Clean"]].map(([v,l]) => (
                      <button key={v} onClick={() => setTrafficInterceptFilter(v)}
                        style={{ padding: "0.2rem 0.65rem", borderRadius: "20px", fontSize: "0.72rem", fontWeight: "600", border: `1px solid ${trafficInterceptFilter === v ? "var(--neon-rose)" : "var(--border-muted)"}`, background: trafficInterceptFilter === v ? "rgba(255,59,48,0.1)" : "transparent", color: trafficInterceptFilter === v ? "var(--neon-rose)" : "var(--text-secondary)", cursor: "pointer" }}>
                        {l}
                      </button>
                    ))}
                  </div>
                  <div style={{ marginLeft: "auto", display: "flex", gap: "0.5rem" }}>
                    <button className="btn btn-secondary" style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }} onClick={() => setTrafficLog([])}>
                      <Trash2 size={12} /> Clear
                    </button>
                  </div>
                </div>
              </div>

              {/* Traffic Table */}
              {(() => {
                const filtered = trafficLog.filter(item => {
                  const q = searchQuery.toLowerCase();
                  const matchQ = !q || (item.host || item.domain || "").toLowerCase().includes(q) || (item.path || "").toLowerCase().includes(q) || (item.src_ip || item.source_ip || "").includes(q);
                  const matchP = trafficProtocolFilter === "all" || (item.protocol || "http") === trafficProtocolFilter;
                  const matchM = trafficMethodFilter === "all" || (item.method || "").toUpperCase() === trafficMethodFilter;
                  const matchI = trafficInterceptFilter === "all" || (trafficInterceptFilter === "intercepted" ? item.intercepted : !item.intercepted);
                  return matchQ && matchP && matchM && matchI;
                });
                return filtered.length > 0 ? (
                  <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                    <div style={{ overflowY: "auto", maxHeight: "440px" }}>
                      <table className="custom-table" style={{ width: "100%" }}>
                        <thead>
                          <tr>
                            <th style={{ width: "80px" }}>Time</th>
                            <th style={{ width: "110px" }}>Source IP</th>
                            <th style={{ width: "65px" }}>Proto</th>
                            <th style={{ width: "65px" }}>Method</th>
                            <th>Host</th>
                            <th>Path</th>
                            <th style={{ width: "55px" }}>Status</th>
                            <th style={{ width: "70px" }}>Size</th>
                            <th style={{ width: "110px" }}>Intercept</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filtered.map((item, idx) => {
                            const m = (item.method || "").toUpperCase();
                            const proto = (item.protocol || "http").toUpperCase();
                            const status = item.status;
                            const statusColor = !status ? "#888" : status >= 500 ? "#f87171" : status >= 400 ? "#f59e0b" : status >= 300 ? "#38bdf8" : "#4ade80";
                            const timeStr = item.ts ? new Date(item.ts * 1000).toLocaleTimeString() : "—";
                            const sizeStr = item.size ? (item.size > 1024 ? (item.size/1024).toFixed(0)+"K" : item.size+"B") : "—";
                            let mColor = "var(--neon-blue)";
                            if (m === "POST") mColor = "var(--neon-rose)";
                            else if (m === "PUT" || m === "PATCH") mColor = "#f59e0b";
                            else if (m === "DELETE") mColor = "#f87171";
                            return (
                              <tr key={idx} onClick={() => setSelectedTrafficItem(item)} style={{ cursor: "pointer", borderLeft: item.intercepted ? "2px solid var(--neon-rose)" : "2px solid transparent" }}>
                                <td style={{ fontFamily: "monospace", fontSize: "0.72rem", color: "var(--text-secondary)" }}>{timeStr}</td>
                                <td style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>{item.src_ip || item.source_ip || "—"}</td>
                                <td><span style={{ fontSize: "0.68rem", fontWeight: "700", color: proto === "HTTPS" ? "var(--neon-green)" : "var(--text-secondary)", background: proto === "HTTPS" ? "rgba(0,230,118,0.08)" : "transparent", borderRadius: "4px", padding: "1px 5px" }}>{proto}</span></td>
                                <td><span style={{ fontFamily: "monospace", fontSize: "0.72rem", fontWeight: "700", color: mColor }}>{m || "REQ"}</span></td>
                                <td style={{ fontWeight: "600", color: "var(--neon-cyan)", fontSize: "0.8rem", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.host || item.domain || "—"}</td>
                                <td style={{ fontFamily: "monospace", fontSize: "0.72rem", color: "var(--text-secondary)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.path || "/"}</td>
                                <td style={{ fontFamily: "monospace", fontSize: "0.78rem", fontWeight: "700", color: statusColor }}>{status || "—"}</td>
                                <td style={{ fontFamily: "monospace", fontSize: "0.72rem", color: "var(--text-secondary)" }}>{sizeStr}</td>
                                <td>{item.intercepted ? <span style={{ color: "var(--neon-rose)", fontSize: "0.68rem", fontWeight: "800" }}>🔓 DECRYPTED</span> : <span style={{ color: "var(--neon-green)", fontSize: "0.68rem" }}>✓ FORWARDED</span>}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="empty-state">
                    <Activity size={40} />
                    <p>{trafficLog.length > 0 ? "No packets match active filters." : "Awaiting traffic. Start MITM interception to see live packets."}</p>
                  </div>
                );
              })()}

              {/* Deep-Dive Side Panel */}
              {selectedTrafficItem && (
                <div style={{ position: "fixed", right: 0, top: 0, bottom: 0, width: "480px", background: "rgba(8,12,26,0.97)", borderLeft: "1px solid var(--border-cyan)", zIndex: 1000, padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1rem", boxShadow: "-8px 0 40px rgba(0,0,0,0.6)", backdropFilter: "blur(16px)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <h3 style={{ margin: 0 }}>Packet Inspector</h3>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>{selectedTrafficItem.intercepted ? "🔴 Decrypted & Intercepted" : "🟢 Forwarded (Passthrough)"}</div>
                    </div>
                    <button className="btn btn-secondary" style={{ padding: "0.3rem 0.75rem" }} onClick={() => setSelectedTrafficItem(null)}>✕ Close</button>
                  </div>

                  <div style={{ background: "rgba(0,242,254,0.04)", border: "1px solid var(--border-cyan)", borderRadius: "8px", padding: "0.75rem", fontFamily: "monospace", wordBreak: "break-all", fontSize: "0.78rem", color: "var(--neon-cyan)", fontWeight: "600" }}>
                    {selectedTrafficItem.method} {(selectedTrafficItem.protocol || "http")}://{selectedTrafficItem.host || selectedTrafficItem.domain}{selectedTrafficItem.path}
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.6rem" }}>
                    {[
                      ["Source IP", selectedTrafficItem.src_ip || selectedTrafficItem.source_ip, "#fff"],
                      ["Time", selectedTrafficItem.ts ? new Date(selectedTrafficItem.ts * 1000).toLocaleTimeString() : "—", "var(--text-secondary)"],
                      ["Protocol", (selectedTrafficItem.protocol || "http").toUpperCase(), selectedTrafficItem.protocol === "https" ? "var(--neon-green)" : "var(--neon-rose)"],
                      ["Status Code", selectedTrafficItem.status || "—", selectedTrafficItem.status >= 400 ? "var(--neon-rose)" : "var(--neon-green)"],
                      ["Response Size", selectedTrafficItem.size ? `${(selectedTrafficItem.size/1024).toFixed(1)} KB` : "—", "#a78bfa"],
                      ["Content-Type", (selectedTrafficItem.content_type || "—").split(";")[0], "var(--text-secondary)"],
                    ].map(([label, val, color]) => (
                      <div key={label} style={{ background: "rgba(0,0,0,0.2)", borderRadius: "6px", padding: "0.5rem" }}>
                        <div style={{ fontSize: "0.6rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.2rem" }}>{label}</div>
                        <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color, fontWeight: "600", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{val}</div>
                      </div>
                    ))}
                  </div>

                  <div style={{ overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "1rem" }}>
                    {selectedTrafficItem.headers && Object.keys(selectedTrafficItem.headers).length > 0 && (
                      <div>
                        <div style={{ fontSize: "0.68rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.5rem", fontWeight: "600" }}>Request Headers</div>
                        <div style={{ background: "rgba(0,0,0,0.3)", borderRadius: "6px", padding: "0.6rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                          {Object.entries(selectedTrafficItem.headers).map(([k, v]) => (
                            <div key={k} style={{ display: "flex", gap: "0.5rem", fontFamily: "monospace", fontSize: "0.7rem", borderBottom: "1px solid rgba(255,255,255,0.03)", paddingBottom: "0.2rem" }}>
                              <span style={{ color: "var(--neon-cyan)", minWidth: "130px", flexShrink: 0, fontWeight: "600" }}>{k}:</span>
                              <span style={{ color: "#ccc", wordBreak: "break-all" }}>{v}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedTrafficItem.body && (
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                          <div style={{ fontSize: "0.68rem", color: "var(--neon-rose)", textTransform: "uppercase", fontWeight: "800" }}>⚠️ Intercepted Request Body</div>
                          <button className="btn btn-secondary" style={{ padding: "0.15rem 0.5rem", fontSize: "0.65rem" }} onClick={() => copyToClipboard(selectedTrafficItem.body)}>Copy</button>
                        </div>
                        <pre style={{ background: "rgba(255,59,48,0.06)", border: "1px solid rgba(255,59,48,0.25)", padding: "0.75rem", borderRadius: "6px", fontFamily: "monospace", fontSize: "0.72rem", color: "#fca5a5", overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-all", margin: 0 }}>
                          {(() => {
                            try {
                              const d = decodeURIComponent(selectedTrafficItem.body.replace(/\+/g, " "));
                              return d.includes("&") ? d.split("&").map(p => p.replace("=", " = ")).join("\n") : d;
                            } catch { return selectedTrafficItem.body; }
                          })()}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}


          {/* VULNERABILITY AUDITOR TAB */}
          {activeTab === "auditor" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div className="card">
                <div className="card-header">
                  <h3><Globe size={18} /> Target Website Vulnerability Auditor</h3>
                </div>

                <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                  Audit internal target applications for secrets leaks, SQL Injection queries, and unhardened security header settings.
                </p>

                <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
                  <div style={{ flex: 1 }}>
                    <input
                      type="text"
                      className="form-group input"
                      value={auditorTarget}
                      onChange={(e) => setAuditorTarget(e.target.value)}
                      placeholder="e.g. http://192.168.1.112:3000 or http://company-portal.local"
                      style={{ width: "100%", height: "42px", background: "var(--bg-input)", border: "1px solid var(--border-muted)", color: "#fff", borderRadius: "8px", padding: "0.75rem" }}
                      disabled={auditorScanning}
                    />
                  </div>
                  <button className="btn btn-primary" onClick={runWebAuditorScan} disabled={auditorScanning}>
                    {auditorScanning ? <RefreshCw className="animate-spin" size={16} /> : "Audit Target Web App"}
                  </button>
                </div>

                {auditorScanning && (
                  <div className="radar-container" style={{ border: "1px solid var(--border-cyan)", borderRadius: "8px", background: "rgba(5,7,15,0.4)" }}>
                    <div className="radar-circle">
                      <div className="radar-sweep"></div>
                      <Globe className="radar-center-icon" size={32} />
                    </div>
                    <div style={{ marginTop: "1.5rem", width: "100%", maxWidth: "500px" }}>
                      <h4 style={{ fontSize: "0.8rem", color: "var(--neon-cyan)", textTransform: "uppercase", textAlign: "center", marginBottom: "0.5rem" }}>Auditing Subsystem Modules</h4>
                      <div style={{ background: "#05070f", padding: "0.75rem", borderRadius: "6px", fontFamily: "monospace", fontSize: "0.7rem", height: "120px", overflowY: "auto", color: "#38bdf8", border: "1px solid var(--border-muted)" }}>
                        {auditorLogs.map((log, i) => <div key={i}>{log}</div>)}
                      </div>
                    </div>
                  </div>
                )}

                {/* Audit Results Dashboard */}
                {auditorResults && !auditorScanning && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", marginTop: "1rem" }}>
                    
                    {/* Severity Summary */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
                      
                      <div className="severity-card critical">
                        <span className="severity-title">Critical severity</span>
                        <span className="severity-value">{auditorResults.stats.critical}</span>
                      </div>

                      <div className="severity-card high">
                        <span className="severity-title">High severity</span>
                        <span className="severity-value">{auditorResults.stats.high}</span>
                      </div>

                      <div className="severity-card medium">
                        <span className="severity-title">Medium severity</span>
                        <span className="severity-value">{auditorResults.stats.medium}</span>
                      </div>

                      <div className="severity-card low">
                        <span className="severity-title">Low / Info</span>
                        <span className="severity-value">{auditorResults.stats.low}</span>
                      </div>
                    </div>

                    {/* Results Details Tabs */}
                    <div style={{ borderTop: "1px solid var(--border-muted)", paddingTop: "1rem" }}>
                      <div style={{ display: "flex", gap: "1rem", borderBottom: "1px solid var(--border-muted)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>
                        <span 
                          style={{ cursor: "pointer", fontWeight: "bold", fontSize: "0.9rem", color: auditorTab === "overview" ? "var(--neon-cyan)" : "var(--text-secondary)", borderBottom: auditorTab === "overview" ? "2px solid var(--neon-cyan)" : "none", paddingBottom: "0.5rem" }}
                          onClick={() => setAuditorTab("overview")}
                        >
                          Vulnerability Findings List
                        </span>
                        <span 
                          style={{ cursor: "pointer", fontWeight: "bold", fontSize: "0.9rem", color: auditorTab === "sqldump" ? "var(--neon-cyan)" : "var(--text-secondary)", borderBottom: auditorTab === "sqldump" ? "2px solid var(--neon-cyan)" : "none", paddingBottom: "0.5rem" }}
                          onClick={() => setAuditorTab("sqldump")}
                        >
                          SQLi Database Dump
                        </span>
                        {auditorResults.report_text && (
                          <span 
                            style={{ cursor: "pointer", fontWeight: "bold", fontSize: "0.9rem", color: auditorTab === "rawreport" ? "var(--neon-cyan)" : "var(--text-secondary)", borderBottom: auditorTab === "rawreport" ? "2px solid var(--neon-cyan)" : "none", paddingBottom: "0.5rem" }}
                            onClick={() => setAuditorTab("rawreport")}
                          >
                            Technical Scan Report
                          </span>
                        )}
                      </div>

                      {auditorTab === "overview" && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                          {auditorResults.vulnerabilities.map((v) => (
                            <div key={v.id} style={{ border: "1px solid var(--border-muted)", padding: "1rem", borderRadius: "8px", background: "rgba(255,255,255,0.01)" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                                <h4 style={{ fontWeight: "750", fontSize: "0.95rem" }}>{v.title}</h4>
                                <span className={`badge ${v.severity === "critical" ? "badge-delete" : v.severity === "high" ? "badge-post" : v.severity === "medium" ? "badge-put" : "badge-get"}`}>
                                  {v.severity.toUpperCase()}
                                </span>
                              </div>
                              <div style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "var(--neon-cyan)", marginBottom: "0.5rem" }}>
                                Location: {v.location}
                              </div>
                              <p style={{ fontSize: "0.825rem", color: "var(--text-secondary)", marginBottom: "0.5rem", lineHeight: "1.4" }}>
                                {v.description}
                              </p>
                              <div style={{ background: "rgba(255,255,255,0.02)", padding: "0.5rem 0.75rem", borderRadius: "4px", fontSize: "0.8rem" }}>
                                <strong>Remediation:</strong> {v.remediation}
                              </div>

                              {v.keys && (
                                <div style={{ marginTop: "0.5rem" }}>
                                  <div style={{ fontSize: "0.7rem", color: "var(--neon-rose)", fontWeight: "bold", marginBottom: "0.25rem" }}>INSPECTED LEAKED KEYS:</div>
                                  {v.keys.map((k, i) => (
                                    <div key={i} style={{ fontFamily: "monospace", fontSize: "0.725rem", background: "rgba(0,0,0,0.3)", padding: "0.35rem", borderRadius: "4px", marginBottom: "0.25rem", display: "flex", justifyContent: "space-between" }}>
                                      <span>{k.type}: {k.key}</span>
                                      <button className="btn btn-secondary" style={{ padding: "0.1rem 0.35rem", fontSize: "0.6rem" }} onClick={() => copyToClipboard(k.key)}>Copy</button>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {auditorTab === "sqldump" && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                            A database dump obtained by executing blind SQL Injection payloads on category search inputs.
                          </p>
                          <div className="table-container">
                            <table className="custom-table" style={{ fontFamily: "monospace", fontSize: "0.775rem" }}>
                              <thead>
                                <tr>
                                  <th>ID</th>
                                  <th>Username Email</th>
                                  <th>SHA-256 Hash String</th>
                                </tr>
                              </thead>
                              <tbody>
                                {(auditorResults.vulnerabilities.find(v => v.id === "vuln-01")?.dump || []).map((row) => (
                                  <tr key={row.id}>
                                    <td>{row.id}</td>
                                    <td style={{ color: "var(--neon-cyan)", fontWeight: "bold" }}>{row.username}</td>
                                    <td style={{ color: "var(--neon-rose)" }}>{row.pass_hash}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {auditorTab === "rawreport" && auditorResults.report_text && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                            Raw CLI output report generated by the Reconnaissance & Site Exploitation Engine.
                          </p>
                          <pre style={{ background: "rgba(0, 0, 0, 0.4)", color: "#22c55e", padding: "1rem", borderRadius: "8px", fontFamily: "monospace", fontSize: "0.75rem", overflowX: "auto", border: "1px solid var(--border-muted)", lineHeight: "1.4", whiteSpace: "pre-wrap" }}>
                            {auditorResults.report_text}
                          </pre>
                        </div>
                      )}
                    </div>

                  </div>
                )}

              </div>
            </div>
          )}

          {/* PHISHING & PAYLOAD TAB */}
          {activeTab === "phishing" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div className="card">
                <div className="card-header">
                  <h3><Database size={18} /> Phishing Cloning Portal & Payload Injection</h3>
                </div>

                <div className="control-grid" style={{ marginBottom: "1.5rem" }}>
                  <div className="form-group">
                    <label>Phishing Form Template</label>
                    <select value={phishingTemplate} onChange={(e) => setPhishingTemplate(e.target.value)}>
                      <option value="m365">Microsoft 365 Cloud Login</option>
                      <option value="gmail">Google account Auth Interface</option>
                      <option value="generic">Generic LAN Router Admin SSO</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Redirect URL (After Submit)</label>
                    <input 
                      type="text" 
                      value={phishingRedirect} 
                      onChange={(e) => setPhishingRedirect(e.target.value)} 
                      placeholder="e.g. https://portal.office.com"
                    />
                  </div>
                </div>

                <div className="form-group" style={{ marginBottom: "1.5rem" }}>
                  <label>Inject Javascript Payload (Active JS Hooking)</label>
                  <textarea
                    rows={4}
                    value={payloadInjectJS}
                    onChange={(e) => setPayloadInjectJS(e.target.value)}
                    style={{ background: "var(--bg-input)", border: "1px solid var(--border-muted)", color: "#fff", borderRadius: "8px", padding: "0.75rem", fontFamily: "monospace", fontSize: "0.8rem", resize: "none" }}
                    placeholder="Enter payload javascript hook code..."
                  />
                </div>

                <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
                  {phishingActive ? (
                    <button className="btn btn-danger" style={{ flex: 1 }} onClick={() => {
                      sendAction("stop_phishing")
                        .then((res) => {
                          if (res.status === "success") {
                            setPhishingActive(false);
                            addTerminalLine("phish", "Stopped phishing server listener on port 8080");
                            showToast("Phishing portal disabled", "success");
                          } else {
                            showToast(res.message || "Failed to stop phishing portal", "error");
                          }
                        })
                        .catch((err) => {
                          showToast("WebSocket error calling stop_phishing", "error");
                        });
                    }}>
                      <Square size={16} /> Disable Phishing Server
                    </button>
                  ) : (
                    <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => {
                      sendAction("start_phishing", { template: phishingTemplate, redirect: phishingRedirect })
                        .then((res) => {
                          if (res.status === "success") {
                            setPhishingActive(true);
                            addTerminalLine("phish", `Starting phishing generator template [${phishingTemplate}] on port 8080`);
                            addTerminalLine("phish", `Routing completed submissions to redirect link: ${phishingRedirect}`);
                            showToast("Phishing portal deployed", "success");
                          } else {
                            showToast(res.message || "Failed to start phishing portal", "error");
                          }
                        })
                        .catch((err) => {
                          showToast("WebSocket error calling start_phishing", "error");
                        });
                    }}>
                      <Play size={16} /> Deploy Phishing Portal
                    </button>
                  )}
                </div>

                {phishingActive && (
                  <div style={{ background: "rgba(0, 242, 254, 0.05)", border: "1px solid var(--border-cyan)", padding: "1rem", borderRadius: "8px", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.8rem", fontWeight: "bold", color: "var(--neon-cyan)" }}>Portal Live Listener Address:</span>
                      <button className="btn btn-secondary" style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }} onClick={() => copyToClipboard(`http://${sysInfo.local_ip}:8080/auth/login`)}>
                        <Copy size={12} /> Copy URL
                      </button>
                    </div>
                    <div style={{ fontFamily: "monospace", fontSize: "0.85rem", color: "var(--text-primary)" }}>
                      http://{sysInfo.local_ip}:8080/auth/login
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      Devices routed via MITM spoof will automatically load this page if they visit any plain unencrypted HTTP portal.
                    </div>
                  </div>
                )}
              </div>

              {/* Harvested Credentials Vault */}
              <div className="card">
                <div className="card-header">
                  <h3><Key size={18} style={{ color: "var(--neon-rose)" }} /> Captured Plaintext Credentials Vault</h3>
                  <button className="btn btn-secondary" onClick={() => setCredsLog([])}>
                    Clear Vault
                  </button>
                </div>

                {credsLog.length > 0 ? (
                  <div className="table-container">
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Time</th>
                          <th>Target IP</th>
                          <th>Phishing Domain / Site</th>
                          <th>Harvested Credentials JSON / plain</th>
                          <th style={{ textAlign: "right" }}>Copy</th>
                        </tr>
                      </thead>
                      <tbody>
                        {credsLog.map((cred, idx) => {
                          const tsValue = cred.ts || cred.timestamp;
                          const timeStr = tsValue ? new Date(tsValue * 1000).toLocaleTimeString() : new Date().toLocaleTimeString();
                          const targetIp = cred.src_ip || cred.source_ip || "Unknown";
                          const domainHost = cred.host || cred.domain || "Phishing Portal";
                          const secretData = cred.credentials || cred.fields || {};
                          return (
                            <tr key={idx} style={{ background: "rgba(255, 59, 48, 0.02)" }}>
                              <td style={{ fontFamily: "monospace" }}>{timeStr}</td>
                              <td style={{ fontFamily: "monospace" }}>{targetIp}</td>
                              <td style={{ fontWeight: "bold" }}>{domainHost}</td>
                              <td style={{ fontFamily: "monospace", color: "#ff6b6b", fontWeight: "600" }}>
                                {cred.creds_summary || JSON.stringify(secretData)}
                              </td>
                              <td style={{ textAlign: "right" }}>
                                <button 
                                  className="btn btn-secondary" 
                                  style={{ padding: "0.25rem 0.5rem" }}
                                  onClick={() => copyToClipboard(JSON.stringify(secretData))}
                                >
                                  <Copy size={12} />
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
                    <p>Credentials vault empty. Activate a phishing template or MITM spoofing to harvest submitted login details.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* WIFI ATTACK HUB TAB */}
          {activeTab === "wifi" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              
              {/* Settings Card */}
              <div className="card">
                <div className="card-header">
                  <h3><Wifi size={18} /> WiFi NIC Monitor Configuration</h3>
                </div>
                
                <div className="control-grid">
                  <div className="form-group">
                    <label>Interface Name</label>
                    <input 
                      type="text" 
                      value={wifiIface} 
                      onChange={(e) => setWifiIface(e.target.value)} 
                      placeholder="e.g. wlan0mon or wlan1"
                    />
                  </div>
                </div>
              </div>

              {/* AP Deployer */}
              <div className="card">
                <div className="card-header">
                  <h3>Deploy Rogue AP (Evil Twin)</h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Configure and broadcast an open WiFi SSID. Client devices that have previously saved the SSID name will connect automatically.
                  </p>
                  
                  <div className="control-grid">
                    <div className="form-group">
                      <label>Broadcast SSID</label>
                      <input 
                        type="text" 
                        value={apSsid} 
                        onChange={(e) => setApSsid(e.target.value)} 
                        placeholder="SSID Name"
                      />
                    </div>
                    <div className="form-group">
                      <label>Radio Channel</label>
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

              {/* Air Scanner */}
              <div className="card">
                <div className="card-header">
                  <h3>WiFi Air Scan Auditor</h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Audit surrounding wireless networks for encryption configurations (WEP, WPA, open profiles).
                  </p>
                  
                  <div>
                    {runningProcessName === "scan" ? (
                      <button className="btn btn-danger" onClick={handleEmergencyCleanup} style={{ width: "100%" }}>
                        <Square size={16} /> Stop Scan
                      </button>
                    ) : (
                      <button className="btn btn-primary" onClick={handleStartWiFiScan} style={{ width: "100%" }} disabled={mitmRunning}>
                        <Play size={16} /> Run AP Air Scan
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Deauth Flood */}
              <div className="card">
                <div className="card-header">
                  <h3>WiFi Client Deauthentication Flood</h3>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Send deauth packets to a target station MAC address, forcing it to drop connection and attempt reconnect to our Rogue AP.
                  </p>
                  
                  <div className="control-grid">
                    <div className="form-group">
                      <label>Target Station MAC</label>
                      <input 
                        type="text" 
                        value={deauthTargetMac} 
                        onChange={(e) => setDeauthTargetMac(e.target.value)} 
                        placeholder="00:aa:bb:cc:dd:ee"
                      />
                    </div>
                    <div className="form-group">
                      <label>BSSID Gateway MAC</label>
                      <input 
                        type="text" 
                        value={deauthGatewayMac} 
                        onChange={(e) => setDeauthGatewayMac(e.target.value)} 
                        placeholder="00:11:22:33:44:55"
                      />
                    </div>
                    <div className="form-group">
                      <label>Network SSID Name</label>
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
                        <Square size={16} /> Stop Deauth Flood
                      </button>
                    ) : (
                      <button className="btn btn-primary" onClick={handleStartDeauth} style={{ flex: 1 }} disabled={mitmRunning}>
                        <Play size={16} /> Broadcast Deauth Floods
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI ANALYST & REPORTER TAB */}
          {activeTab === "ai" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div className="card">
                <div className="card-header">
                  <h3><Brain size={18} style={{ color: "var(--neon-cyan)" }} /> AI Threat Intelligence Analyst</h3>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button className="btn btn-primary" onClick={generateAIReport} disabled={aiAnalyzing}>
                      {aiAnalyzing ? <RefreshCw className="animate-spin" size={16} /> : "Generate SOC Report"}
                    </button>
                    {aiReport && (
                      <button className="btn btn-secondary" onClick={downloadAIReport}>
                        <Download size={16} /> Download
                      </button>
                    )}
                  </div>
                </div>

                <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "1rem" }}>
                  Analyze current network traffic, active rogue AP streams, and harvested accounts. Generates structured executive cybersecurity reports.
                </p>

                {aiAnalyzing && (
                  <div className="radar-container" style={{ padding: "4rem" }}>
                    <div className="radar-circle" style={{ borderColor: "var(--neon-rose)" }}>
                      <div className="radar-sweep" style={{ background: "conic-gradient(from 0deg, rgba(255, 42, 95, 0.25) 0deg, transparent 90deg, transparent 360deg)" }}></div>
                      <Brain size={36} style={{ color: "var(--neon-rose)", filter: "drop-shadow(0 0 8px var(--neon-rose))" }} />
                    </div>
                    <span style={{ color: "var(--neon-rose)", fontSize: "0.8rem", marginTop: "1rem", fontWeight: "bold" }}>COMPILING INTERCEPTED METRICS...</span>
                  </div>
                )}

                {aiReport && !aiAnalyzing && (
                  <div style={{ background: "#05070c", border: "1px solid var(--border-muted)", padding: "1.5rem", borderRadius: "8px", fontFamily: "monospace", fontSize: "0.8rem", lineHeight: "1.6", color: "#e2e8f0", overflowX: "auto" }}>
                    <pre style={{ whiteSpace: "pre-wrap" }}>{aiReport}</pre>
                  </div>
                )}

                {!aiReport && !aiAnalyzing && (
                  <div className="empty-state">
                    <Brain size={48} />
                    <p>No report compiled. Click the button above to generate AI threat intelligence documentation based on active session stats.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* LAB CONFIG PROFILE TAB */}
          {activeTab === "config" && (
            <div className="card">
              <div className="card-header">
                <h3><Settings size={18} /> Configuration Settings Profile</h3>
                <button className="btn btn-primary" onClick={handleSaveConfig} disabled={!wsConnected}>
                  Save Profile Configuration
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
                    <label>Target IP List (comma-separated)</label>
                    <input 
                      type="text" 
                      value={config.targets || ""} 
                      onChange={(e) => setConfig(prev => ({ ...prev, targets: e.target.value }))}
                      placeholder="e.g. 192.168.1.105,192.168.1.112"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Gateway Route IP</label>
                    <input 
                      type="text" 
                      value={config.gateway_ip || ""} 
                      onChange={(e) => setConfig(prev => ({ ...prev, gateway_ip: e.target.value }))}
                      placeholder="(Auto-discover)"
                    />
                  </div>
                </div>

                <div style={{ borderTop: "1px solid var(--border-muted)", paddingTop: "1.5rem" }}>
                  <h4 style={{ marginBottom: "1rem", fontSize: "0.9rem" }}>Content Rules & DNS Rules</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    <label className="checkbox-group">
                      <input 
                        type="checkbox" 
                        checked={config.enable_html_banner || false}
                        onChange={(e) => setConfig(prev => ({ ...prev, enable_html_banner: e.target.checked }))}
                      />
                      <span>Inject HTML Warning banner into unencrypted website packets</span>
                    </label>

                    {config.enable_html_banner && (
                      <div className="form-group" style={{ marginLeft: "1.75rem" }}>
                        <label>Warning Banner HTML Text</label>
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
                      <span>Enable Image Replacement rule mappings</span>
                    </label>

                    <label className="checkbox-group">
                      <input 
                        type="checkbox" 
                        checked={config.dns_enabled || false}
                        onChange={(e) => setConfig(prev => ({ ...prev, dns_enabled: e.target.checked }))}
                      />
                      <span>Enable DNS spoofing redirection rules</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Terminal Drawer */}
        <footer className={`terminal-drawer ${terminalCollapsed ? "collapsed" : ""}`}>
          <div className="terminal-header" onClick={() => setTerminalCollapsed(!terminalCollapsed)}>
            <h4><TermIcon size={14} /> LIVE SOC STDOUT LOGS</h4>
            <span style={{ fontSize: "0.75rem" }}>{terminalCollapsed ? "Expand ▲" : "Collapse ▼"}</span>
          </div>
          
          <div className="terminal-content">
            {terminalLines.length > 0 ? (
              terminalLines.map((line, idx) => (
                <div className="terminal-line" key={idx}>{line}</div>
              ))
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                Awaiting active stdout lines...
              </div>
            )}
            <div ref={terminalEndRef} />
          </div>
        </footer>
      </main>

      {/* Floating Demo Simulator Panel */}
      {appMode === "demo" && showDemoController && (
        <div className="demo-controller-floating">
          <div className="demo-controller-header">
            <span>Demo Control Board</span>
            <button style={{ background: "none", border: "none", color: "var(--neon-rose)", cursor: "pointer", fontSize: "0.8rem", fontWeight: "bold" }} onClick={() => setShowDemoController(false)}>Hide</button>
          </div>
          <div className="demo-controller-buttons">
            <button className="demo-btn" onClick={triggerSimulatedHost}>
              ⚡ Discover Target Node
            </button>
            <button className="demo-btn" onClick={triggerSimulatedPacket}>
              ⚡ Decrypt HTTP POST Packet
            </button>
            <button className="demo-btn" onClick={() => {
              const count = credsLog.length;
              const ip = discoveredHosts.find(h => h.ip !== "192.168.1.1" && h.ip !== "192.168.1.100")?.ip || "192.168.1.105";
              const fakeCred = {
                ts: Math.floor(Date.now() / 1000),
                src_ip: ip,
                host: "okta.megacorp-sso.net",
                method: "POST",
                creds_summary: `username=sec_lead%40megacorp.com&password=SpringBreakGlow%212026`,
                credentials: { identity: "sec_lead@megacorp.com", secret: "SpringBreakGlow!2026", raw: "password_form" }
              };
              setCredsLog(prev => [fakeCred, ...prev]);
              showToast("⚠️ CREDENTIALS HARVESTED FROM OKTA TEMPLATE!", "error");
              addTerminalLine("creds", `Harvester captured plaintext OKTA creds from ${ip}`);
            }}>
              ⚡ Simulate SSO Credential Capture
            </button>
            <div style={{ marginTop: "0.5rem" }}>
              <div style={{ fontSize: "0.65rem", color: "var(--text-secondary)", marginBottom: "0.25rem" }}>PACKET STREAM FREQUENCY:</div>
              <input 
                type="range" 
                min="0.5" 
                max="5" 
                step="0.5"
                value={simPacketRate}
                onChange={(e) => setSimPacketRate(parseFloat(e.target.value))}
                style={{ width: "100%" }} 
              />
            </div>
          </div>
        </div>
      )}

      {/* Floating Demo Trigger Show Button */}
      {appMode === "demo" && !showDemoController && (
        <button 
          style={{ position: "fixed", bottom: "220px", left: "20px", background: "rgba(12,16,32,0.95)", border: "1px solid var(--neon-rose)", color: "var(--neon-rose)", borderRadius: "8px", padding: "0.5rem 1rem", fontSize: "0.75rem", fontWeight: "bold", zIndex: 1000, cursor: "pointer", boxShadow: "0 0 10px rgba(255, 42, 95, 0.15)" }}
          onClick={() => setShowDemoController(true)}
        >
          Show Demo Control Board
        </button>
      )}

      {/* Toast popup */}
      {toast && (
        <div className="toast-msg">
          <Check size={16} style={{ color: toast.type === "error" ? "var(--neon-rose)" : "var(--neon-cyan)" }} />
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

export default App;
