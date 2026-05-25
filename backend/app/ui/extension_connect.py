from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


EXTENSION_CONNECT_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Connect Extension — Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #08080a; --bg-1: #0d0f14; --bg-2: #111420; --bg-3: #181b28;
      --border: rgba(255,255,255,.08); --b2: rgba(255,255,255,.13);
      --cyan: #00d4ff; --cyan-d: rgba(0,212,255,.1);
      --green: #22d3a0; --amber: #f5a623; --red: #ff4d6d;
      --text: #edf2ff; --muted: #7c8499;
      --mono: 'JetBrains Mono', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { min-height: 100vh; background: var(--bg); color: var(--text); display: grid; place-items: center; padding: 20px; }
    body::before {
      content: ""; position: fixed; inset: 0; pointer-events: none;
      background-image: linear-gradient(rgba(255,255,255,.028) 1px, transparent 1px);
      background-size: 100% 40px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.6), rgba(0,0,0,.02));
    }
    .wrap { position: relative; z-index: 1; width: min(520px, 100%); display: grid; gap: 16px; }
    .card { border: 1px solid var(--b2); border-radius: 10px; background: var(--bg-1); padding: 28px; }
    .eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
    .eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    h1 { font-size: 22px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
    .subtitle { font-size: 13px; color: var(--muted); line-height: 1.6; margin-bottom: 20px; }
    .status-block {
      border: 1px solid var(--border); border-radius: 8px;
      background: var(--bg-2); padding: 16px;
      display: grid; gap: 10px;
    }
    .step-row { display: flex; align-items: center; gap: 12px; font-size: 13px; }
    .step-icon {
      width: 28px; height: 28px; border-radius: 6px; display: grid; place-items: center;
      font-size: 13px; font-weight: 700; flex-shrink: 0;
    }
    .step-icon.pending  { background: var(--bg-3); color: var(--muted); border: 1px solid var(--border); }
    .step-icon.active   { background: var(--cyan); color: #000; }
    .step-icon.done     { background: rgba(34,211,160,.15); color: var(--green); border: 1px solid rgba(34,211,160,.3); }
    .step-icon.error    { background: rgba(255,77,109,.12); color: var(--red);   border: 1px solid rgba(255,77,109,.3); }
    .step-label { flex: 1; }
    .step-label b { display: block; color: var(--text); font-weight: 600; }
    .step-label span { font-size: 12px; color: var(--muted); }
    .url-box {
      border: 1px solid var(--b2); border-radius: 7px; background: var(--bg-3);
      padding: 10px 12px; font-family: var(--mono); font-size: 12px;
      color: var(--cyan); word-break: break-all; line-height: 1.5;
      display: none;
    }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
    .btn {
      padding: 9px 16px; border-radius: 7px; border: 1px solid var(--b2);
      background: var(--bg-2); color: var(--muted); font-size: 13px; font-weight: 600;
      cursor: pointer; text-decoration: none; font: inherit;
      transition: border-color .15s, color .15s;
    }
    .btn:hover { border-color: var(--cyan); color: var(--cyan); }
    .btn.primary { background: var(--cyan); color: #000; border-color: var(--cyan); font-weight: 700; }
    .btn.primary:hover { background: #00bde8; border-color: #00bde8; }
    .result-msg { font-size: 13px; padding: 12px; border-radius: 7px; border: 1px solid var(--border); background: var(--bg-2); color: var(--muted); line-height: 1.5; }
    .result-msg.ok  { color: var(--green); border-color: rgba(34,211,160,.28); background: rgba(34,211,160,.06); }
    .result-msg.err { color: var(--red);   border-color: rgba(255,77,109,.28); background: rgba(255,77,109,.06); }
    .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(0,212,255,.2); border-top-color: var(--cyan); border-radius: 50%; animation: spin .7s linear infinite; vertical-align: middle; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .no-ext-hint { font-size: 13px; color: var(--muted); line-height: 1.6; }
    .no-ext-hint a { color: var(--cyan); text-decoration: none; }
    .no-ext-hint a:hover { text-decoration: underline; }
  </style>
</head>
<body class="no-shell">
  <div class="wrap">
    <div class="card">
      <div class="eyebrow">Browser Extension</div>
      <h1>Connecting to Gateway</h1>
      <p class="subtitle">The dashboard is pairing your browser extension with this Zero Trust AI Gateway instance.</p>

      <div class="status-block">
        <div class="step-row" id="stepDetect">
          <div class="step-icon active" id="stepDetectIcon"><span class="spinner"></span></div>
          <div class="step-label"><b>Detecting extension</b><span id="stepDetectMsg">Checking if extension is installed...</span></div>
        </div>
        <div class="step-row" id="stepConnect">
          <div class="step-icon pending" id="stepConnectIcon">2</div>
          <div class="step-label"><b>Registering device</b><span id="stepConnectMsg">Waiting...</span></div>
        </div>
        <div class="step-row" id="stepDone">
          <div class="step-icon pending" id="stepDoneIcon">3</div>
          <div class="step-label"><b>Extension paired</b><span id="stepDoneMsg">Waiting...</span></div>
        </div>
      </div>

      <div id="urlBox" class="url-box"></div>
      <div id="resultMsg" class="result-msg" style="display:none;margin-top:12px"></div>

      <div id="noExtHint" class="no-ext-hint" style="display:none;margin-top:14px">
        Extension not detected. <a href="/downloads/browser-extension.zip">Download the extension</a>, then in Chrome open <code style="color:var(--cyan)">chrome://extensions</code>, enable Developer Mode, choose <strong>Load unpacked</strong>, and select the extracted folder.
        <div class="actions" style="margin-top:12px">
          <a href="/downloads/browser-extension.zip" class="btn primary">Download Extension</a>
          <a href="/dashboard/extension/install" class="btn">Full Setup Guide</a>
        </div>
      </div>

      <div id="successActions" class="actions" style="display:none;margin-top:14px">
        <a href="/dashboard" class="btn primary">Back to Dashboard</a>
        <a href="/dashboard/security-monitor" class="btn">View Monitor</a>
      </div>

      <div id="retryArea" class="actions" style="display:none;margin-top:12px">
        <a href="/dashboard/extension/install" class="btn">Setup Guide</a>
        <button class="btn" onclick="location.reload()">Retry</button>
      </div>
    </div>

    <div style="text-align:center;font-size:12px;color:var(--muted)">
      Need manual setup? <a href="/dashboard/extension/install" style="color:var(--cyan)">Open full extension setup</a>
    </div>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);

    function setStep(id, state, msg) {
      const icon = $(id + "Icon");
      const msgEl = $(id + "Msg");
      icon.className = "step-icon " + state;
      if (state === "active")  icon.innerHTML = '<span class="spinner"></span>';
      else if (state === "done")  icon.textContent = "✓";
      else if (state === "error") icon.textContent = "✗";
      else icon.textContent = id === "stepDetect" ? "1" : id === "stepConnect" ? "2" : "3";
      if (msg) msgEl.textContent = msg;
    }

    function ping() {
      return new Promise(resolve => {
        const nonce = Math.random().toString(36).slice(2);
        const handler = e => {
          if (e.data?.type === "ZTA_GATEWAY_EXTENSION_DETECTED" && e.data?.nonce === nonce) {
            window.removeEventListener("message", handler);
            clearTimeout(timer);
            resolve({ detected: true, version: e.data.extensionVersion });
          }
        };
        const timer = setTimeout(() => {
          window.removeEventListener("message", handler);
          resolve({ detected: false });
        }, 1200);
        window.addEventListener("message", handler);
        window.postMessage({ type: "ZTA_GATEWAY_EXTENSION_PING", nonce }, "*");
      });
    }

    function autoConnect(gatewayApiUrl, pairingToken, setupSessionId) {
      return new Promise((resolve, reject) => {
        const handler = e => {
          if (e.data?.type === "ZTA_AUTOCONNECT_RESPONSE") {
            window.removeEventListener("message", handler);
            clearTimeout(timer);
            if (e.data.success) resolve(e.data);
            else reject(new Error(e.data.error || "Connection failed"));
          }
        };
        const timer = setTimeout(() => {
          window.removeEventListener("message", handler);
          reject(new Error("Connection timed out — extension did not respond"));
        }, 12000);
        window.addEventListener("message", handler);
        window.postMessage({
          type: "ZTA_AUTOCONNECT_REQUEST",
          gatewayApiUrl,
          pairingToken,
          setupSessionId,
          deviceLabel: "Dashboard auto-connect"
        }, "*");
      });
    }

    async function run() {
      const params = new URLSearchParams(location.search);
      const pairingToken = params.get("token");
      const gatewayApiUrl = params.get("gateway_api_url") || location.origin;
      const setupSessionId = params.get("setup_session_id") || "";

      if (!pairingToken) {
        setStep("stepDetect", "error", "No pairing token in URL");
        $("resultMsg").style.display = "block";
        $("resultMsg").className = "result-msg err";
        $("resultMsg").textContent = "No pairing token found. Go back to the dashboard and click Quick Connect again.";
        $("retryArea").style.display = "flex";
        return;
      }

      $("urlBox").style.display = "block";
      $("urlBox").textContent = location.href;

      // Step 1: detect extension
      setStep("stepDetect", "active", "Checking if extension is installed...");
      const ext = await ping();

      if (!ext.detected) {
        setStep("stepDetect", "error", "Extension not found");
        setStep("stepConnect", "error", "Skipped");
        setStep("stepDone", "error", "Skipped");
        $("noExtHint").style.display = "block";
        return;
      }

      setStep("stepDetect", "done", `Extension v${ext.version} detected`);
      setStep("stepConnect", "active", "Sending credentials to extension...");

      try {
        const result = await autoConnect(gatewayApiUrl, pairingToken, setupSessionId);
        setStep("stepConnect", "done", "Device registered successfully");
        setStep("stepDone", "done", `Paired · Device ${result.deviceId}`);
        $("urlBox").style.display = "none";
        $("resultMsg").style.display = "block";
        $("resultMsg").className = "result-msg ok";
        $("resultMsg").textContent = `Extension connected. Device ID: ${result.deviceId}. All browser prompts are now protected by the gateway.`;
        $("successActions").style.display = "flex";
      } catch (err) {
        setStep("stepConnect", "error", err.message);
        setStep("stepDone", "error", "Not completed");
        $("resultMsg").style.display = "block";
        $("resultMsg").className = "result-msg err";
        $("resultMsg").textContent = "Auto-connect failed: " + err.message + ". Try opening the extension popup and pasting the URL manually.";
        $("retryArea").style.display = "flex";
      }
    }

    const tok = sessionStorage.getItem("zta_token");
    if (!tok) location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search);
    else run();
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
