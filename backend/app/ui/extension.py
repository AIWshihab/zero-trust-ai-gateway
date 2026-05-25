from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


EXTENSION_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Browser Extension — Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #08080a;
      --bg-1: #0d0f14;
      --bg-2: #111420;
      --bg-3: #181b28;
      --border: rgba(255,255,255,.08);
      --b2: rgba(255,255,255,.13);
      --cyan: #00d4ff;
      --cyan-d: rgba(0,212,255,.1);
      --green: #22d3a0;
      --amber: #f5a623;
      --red: #ff4d6d;
      --text: #edf2ff;
      --muted: #7c8499;
      --mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { min-height: 100vh; background: var(--bg); color: var(--text); }
    .shell { padding: 20px clamp(14px,3vw,32px) 32px; display: grid; gap: 16px; }
    .page-header { display: grid; grid-template-columns: minmax(280px,1fr) auto; gap: 16px; align-items: start; }
    .page-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
    .page-eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .page-header h1 { font-size: clamp(22px,3.5vw,36px); font-weight: 700; color: var(--text); line-height: 1.1; margin-bottom: 8px; }
    .page-header p { font-size: 14px; color: var(--muted); line-height: 1.6; max-width: 640px; }
    .hdr-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    a, button {
      border: 1px solid var(--b2);
      border-radius: 7px;
      padding: 9px 14px;
      color: var(--text);
      background: var(--bg-2);
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      transition: border-color .18s, background .18s;
    }
    a:hover, button:hover { border-color: var(--cyan); background: var(--bg-3); }
    a.primary { background: var(--cyan); color: #000; border-color: var(--cyan); font-weight: 700; }
    a.primary:hover { background: #00bde8; }
    .disabled { pointer-events: none; opacity: .52; }
    .info-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .card {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 16px;
      transition: border-color .2s;
    }
    .card:hover { border-color: rgba(0,212,255,.18); }
    .card-label { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
    .card-label::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .card-value { font-size: 15px; font-weight: 600; color: var(--text); overflow-wrap: anywhere; margin-bottom: 10px; }
    .card-desc { font-size: 12px; color: var(--muted); line-height: 1.5; }
    .badge { display: inline-flex; gap: 8px; align-items: center; border: 1px solid var(--b2); border-radius: 999px; padding: 7px 12px; color: var(--muted); background: var(--bg-2); font-size: 12px; font-weight: 700; }
    .badge.waiting   { border-color: rgba(245,166,35,.3); color: var(--amber); background: rgba(245,166,35,.06); }
    .badge.connected { border-color: rgba(34,211,160,.3); color: var(--green); background: rgba(34,211,160,.06); }
    .badge.revoked   { border-color: rgba(255,77,109,.3);  color: var(--red);   background: rgba(255,77,109,.06); }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }
    .wide { display: grid; grid-template-columns: 1.05fr .95fr; gap: 14px; }
    .card-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
    .card-head h2 { font-size: 15px; font-weight: 700; color: var(--text); }
    .steps { display: grid; gap: 12px; }
    .step { display: grid; grid-template-columns: 28px 1fr; gap: 12px; align-items: start; }
    .step-num { width: 26px; height: 26px; border-radius: 6px; display: grid; place-items: center; background: var(--cyan); color: #000; font-weight: 700; font-size: 12px; }
    .step h3 { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
    .step p { font-size: 13px; color: var(--muted); line-height: 1.55; }
    .step .step-actions { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; }
    .step-note { font-size: 12px; color: var(--muted); margin-top: 8px; }
    .code-block {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--bg-2);
      padding: 14px;
      margin-top: 12px;
    }
    .code-label { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
    input {
      width: 100%;
      border: 1px solid var(--b2);
      border-radius: 7px;
      background: var(--bg-3);
      color: var(--text);
      padding: 10px 12px;
      font: inherit;
      font-size: 13px;
      outline: none;
      transition: border-color .18s;
      margin-bottom: 10px;
    }
    input:focus { border-color: rgba(0,212,255,.42); }
    .btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .detail-block { border: 1px solid var(--border); border-radius: 7px; padding: 12px; background: var(--bg-2); margin-top: 12px; }
    .detail-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; font-weight: 600; margin-bottom: 4px; }
    .detail-value { font-size: 14px; font-weight: 600; color: var(--text); }
    .detail-meta { font-size: 12px; color: var(--muted); margin-top: 3px; }
    .notice { border: 1px solid rgba(245,166,35,.2); border-radius: 8px; padding: 12px 14px; background: rgba(245,166,35,.05); color: var(--muted); font-size: 12px; line-height: 1.5; margin-top: 12px; }
    .hidden { display: none !important; }
    @media (max-width: 980px) { .info-strip, .wide, .page-header { grid-template-columns: 1fr; } .info-strip { grid-template-columns: repeat(2,1fr); } }
    @media (max-width: 540px) { .info-strip { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="page-header">
      <div>
        <div class="page-eyebrow">Browser Extension</div>
        <h1>Add Browser Extension</h1>
        <p>The dashboard automates pairing with the Zero Trust AI Gateway. Chrome still controls installation, so production users are sent to the Chrome Web Store and developers can load the unpacked extension locally.</p>
      </div>
      <div class="hdr-row">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/security-monitor">Security Monitor</a>
      </div>
    </section>

    <section class="info-strip">
      <article class="card">
        <div class="card-label">Extension Status</div>
        <div class="card-value"><span id="installBadge" class="badge"><span class="dot"></span><span>Checking...</span></span></div>
        <div id="nextAction" class="card-desc">Creating secure setup session.</div>
      </article>
      <article class="card">
        <div class="card-label">Gateway API URL</div>
        <div id="apiUrl" class="card-value">Loading...</div>
        <div class="hdr-row" style="margin-top:8px"><button id="copyUrlBtn">Copy Gateway URL</button></div>
      </article>
      <article class="card">
        <div class="card-label">Setup Session</div>
        <div id="sessionLine" class="card-value">Creating...</div>
        <div id="expiryLine" class="card-desc">Pairing token expires quickly and is one-time use.</div>
      </article>
    </section>

    <section class="wide">
      <article class="card">
        <div class="card-head">
          <h2>Setup</h2>
          <span id="connectionBadge" class="badge waiting"><span class="dot"></span><span>Waiting for connection</span></span>
        </div>
        <div class="steps">
          <div class="step">
            <div class="step-num">1</div>
            <div>
              <h3>Step 1: Install</h3>
              <p id="installCopy" class="step-note">Choose the install option for this environment.</p>
              <div id="devActions" class="step-actions hidden">
                <a class="primary" href="/downloads/browser-extension.zip">Download Developer Extension</a>
                <button id="copyDevUrlBtn">Copy Gateway URL</button>
              </div>
              <div id="prodActions" class="step-actions hidden">
                <a id="storeLink" class="primary" href="#" target="_blank" rel="noreferrer">Add to Chrome</a>
                <span id="comingSoon" class="badge hidden">Coming soon</span>
              </div>
              <p id="devInstructions" class="step-note hidden">Open chrome://extensions, enable Developer Mode, choose Load unpacked, then select the browser-extension folder.</p>
            </div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div>
              <h3>Step 2: Connect</h3>
              <p class="step-note">Paste this setup link into the extension popup. The extension will read the gateway URL and pairing token automatically.</p>
              <div class="code-block">
                <div class="code-label">Connect URL</div>
                <input id="connectUrl" readonly placeholder="Creating connect URL" />
                <div class="btn-row">
                  <button id="copyConnectBtn">Copy Connect URL</button>
                  <button id="refreshSessionBtn">Refresh Token</button>
                </div>
              </div>
            </div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div>
              <h3>Step 3: Test</h3>
              <p class="step-note">After the extension connects, send a test prompt from the popup. The gateway will log extension activity in the Security Monitor.</p>
            </div>
          </div>
        </div>
      </article>

      <article class="card">
        <div class="card-label">Connection Details</div>
        <div class="detail-block">
          <div class="detail-label">Device</div>
          <div id="deviceLine" class="detail-value">Not connected yet</div>
          <div id="deviceMeta" class="detail-meta">Waiting for browser extension registration.</div>
        </div>
        <div class="notice">A website cannot silently install a Chrome extension. This page automates secure pairing, not Chrome's install confirmation.</div>
      </article>
    </section>
  </main>

  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/extension/install";

    const $ = (id) => document.getElementById(id);
    const headers = () => ({ Authorization: `Bearer ${token}` });
    const isDev = ["localhost", "127.0.0.1", "::1"].includes(location.hostname);
    let setupSessionId = null;
    let pollTimer = null;
    let extensionDetected = false;

    function setBadge(el, text, cls) {
      el.className = `badge ${cls || ""}`.trim();
      el.innerHTML = `<span class="dot"></span><span>${text}</span>`;
    }

    function setEnvironment(config) {
      $("apiUrl").textContent = config.gateway_api_base_url || location.origin;
      if (isDev) {
        $("devActions").classList.remove("hidden");
        $("devInstructions").classList.remove("hidden");
        $("installCopy").textContent = "Developer testing uses Chrome Developer Mode and the unpacked extension folder.";
        $("prodActions").classList.add("hidden");
      } else {
        $("prodActions").classList.remove("hidden");
        $("devActions").classList.add("hidden");
        $("devInstructions").classList.add("hidden");
        $("installCopy").textContent = "Production install opens the Chrome Web Store listing.";
        if (config.chrome_extension_store_url) {
          $("storeLink").href = config.chrome_extension_store_url;
          $("storeLink").classList.remove("disabled");
          $("comingSoon").classList.add("hidden");
        } else {
          $("storeLink").classList.add("hidden");
          $("comingSoon").classList.remove("hidden");
        }
      }
    }

    async function post(path) {
      const res = await fetch(path, { method: "POST", headers: headers() });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Request failed");
      return data;
    }

    async function get(path) {
      const res = await fetch(path, { headers: headers() });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Request failed");
      return data;
    }

    async function createSession() {
      $("sessionLine").textContent = "Creating...";
      const data = await post(`${api}/extension/setup-session`);
      setupSessionId = data.setup_session_id;
      setEnvironment(data);
      $("sessionLine").textContent = setupSessionId;
      $("connectUrl").value = data.connect_url;
      $("expiryLine").textContent = `Token expires ${new Date(data.expires_at).toLocaleString()}`;
      updateFromStatus(data);
      startPolling();
    }

    function updateFromStatus(data) {
      const status = data.status || "waiting_for_connection";
      if (status === "connected") {
        setBadge($("connectionBadge"), "Connected", "connected");
        setBadge($("installBadge"), "Connected", "connected");
        $("nextAction").textContent = "Extension connected. Send a test prompt from the popup.";
        $("deviceLine").textContent = `Device ${data.device_id}`;
        $("deviceMeta").textContent = `${data.browser_name || "Browser"} · extension ${data.extension_version || "unknown"} · ${data.last_connected_at ? new Date(data.last_connected_at).toLocaleString() : "just now"}`;
        if (pollTimer) clearInterval(pollTimer);
        return;
      }
      if (status === "revoked") {
        setBadge($("connectionBadge"), "Revoked", "revoked");
        setBadge($("installBadge"), "Revoked", "revoked");
        $("nextAction").textContent = "This extension device was revoked. Generate a new setup session after reviewing devices.";
        return;
      }
      if (status === "expired") {
        setBadge($("connectionBadge"), "Token expired", "revoked");
        $("nextAction").textContent = "The pairing token expired. Refresh the token and try again.";
        return;
      }
      setBadge($("connectionBadge"), "Waiting for connection", "waiting");
      if (extensionDetected) {
        setBadge($("installBadge"), "Installed but not connected", "waiting");
        $("nextAction").textContent = "Open the extension popup and paste the connect URL.";
        if (!isDev) {
          $("storeLink").textContent = "Connect Extension";
          $("storeLink").href = "#";
          $("storeLink").removeAttribute("target");
        }
      } else {
        setBadge($("installBadge"), "Not installed", "");
        $("nextAction").textContent = isDev ? "Download and load the developer extension." : "Install from Chrome Web Store, then connect.";
        if (!isDev) {
          $("storeLink").textContent = "Add to Chrome";
        }
      }
    }

    function startPolling() {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(async () => {
        if (!setupSessionId) return;
        try {
          updateFromStatus(await get(`${api}/extension/setup-session/${encodeURIComponent(setupSessionId)}`));
        } catch (err) {
          $("nextAction").textContent = err.message || "Could not check extension status.";
        }
      }, 2500);
    }

    function detectExtension() {
      const nonce = Math.random().toString(36).slice(2);
      const timeout = setTimeout(() => updateFromStatus({ status: "waiting_for_connection" }), 900);
      function onMessage(event) {
        if (event.source !== window) return;
        if (event.data?.type !== "ZTA_GATEWAY_EXTENSION_DETECTED") return;
        if (event.data?.nonce !== nonce) return;
        clearTimeout(timeout);
        window.removeEventListener("message", onMessage);
        extensionDetected = true;
        updateFromStatus({ status: "waiting_for_connection" });
      }
      window.addEventListener("message", onMessage);
      window.postMessage({ type: "ZTA_GATEWAY_EXTENSION_PING", nonce }, "*");
    }

    $("copyUrlBtn").onclick = () => navigator.clipboard.writeText($("apiUrl").textContent);
    $("copyDevUrlBtn").onclick = () => navigator.clipboard.writeText($("apiUrl").textContent);
    $("copyConnectBtn").onclick = () => navigator.clipboard.writeText($("connectUrl").value || "");
    $("refreshSessionBtn").onclick = createSession;
    $("storeLink").onclick = (event) => {
      if (extensionDetected) {
        event.preventDefault();
        navigator.clipboard.writeText($("connectUrl").value || "");
        $("nextAction").textContent = "Connect URL copied. Open the extension popup to finish pairing.";
      }
      setTimeout(startPolling, 700);
    };

    const incoming = new URLSearchParams(location.search);
    if (incoming.get("token")) {
      setupSessionId = incoming.get("setup_session_id");
      $("apiUrl").textContent = incoming.get("gateway_api_url") || location.origin;
      $("connectUrl").value = location.href;
      $("sessionLine").textContent = setupSessionId || "Connect URL";
      $("nextAction").textContent = "Copy this connect URL into the extension popup to finish pairing.";
      if (setupSessionId) {
        startPolling();
        get(`${api}/extension/setup-session/${encodeURIComponent(setupSessionId)}`)
          .then((data) => {
            setEnvironment(data);
            $("expiryLine").textContent = `Token expires ${new Date(data.expires_at).toLocaleString()}`;
            updateFromStatus(data);
          })
          .catch((err) => {
            $("expiryLine").textContent = err.message || "Could not load setup session.";
          });
      }
    } else {
      createSession().catch((err) => {
        $("sessionLine").textContent = "Setup failed";
        $("expiryLine").textContent = err.message || "Could not create setup session.";
      });
    }
    detectExtension();
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
