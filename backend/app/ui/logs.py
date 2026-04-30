LOGS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Gateway Logs</title>
  <style>
    :root {
      color-scheme: dark;
      --panel: rgba(20, 18, 16, .9);
      --text: #fff7ea;
      --muted: #d3b99a;
      --green: #73e28b;
      --cyan: #8ce9ff;
      --amber: #ff9f1c;
      --red: #ff4d3d;
      --ink: #080604;
      --cream: #fff1d5;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 12% 8%, rgba(255,159,28,.26), transparent 28%),
        radial-gradient(circle at 88% 0%, rgba(255,77,61,.16), transparent 30%),
        linear-gradient(120deg, rgba(255,255,255,.035) 0 1px, transparent 1px 72px),
        linear-gradient(135deg, #090806, #15100b 50%, #2b1207);
      overflow-x: hidden;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,241,213,.08) 2px, transparent 2px),
        linear-gradient(90deg, rgba(255,241,213,.08) 2px, transparent 2px),
        radial-gradient(circle, rgba(255,255,255,.16) 1px, transparent 1.5px);
      background-size: 118px 66px, 118px 66px, 9px 9px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), rgba(0,0,0,.12));
    }
    body::after {
      content: "";
      position: fixed;
      inset: -18% -8%;
      pointer-events: none;
      background: repeating-linear-gradient(112deg, transparent 0 24px, rgba(255,255,255,.08) 25px 27px, transparent 28px 56px);
      opacity: .5;
      transform: skewY(-5deg);
      animation: rush 12s linear infinite;
    }
    .shell { position: relative; z-index: 1; padding: 22px clamp(14px, 3vw, 34px) 34px; }
    header {
      display: grid;
      grid-template-columns: minmax(300px, 1fr) auto;
      gap: 18px;
      align-items: start;
      margin-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: clamp(30px, 4.2vw, 58px);
      letter-spacing: 0;
      line-height: .94;
      text-transform: uppercase;
      text-shadow: 4px 4px 0 var(--ink), 7px 7px 0 rgba(255,159,28,.34);
    }
    p { margin: 10px 0 0; color: var(--cream); line-height: 1.55; max-width: 860px; font-weight: 680; }
    a, button {
      border: 2px solid var(--ink);
      border-radius: 7px;
      padding: 10px 12px;
      color: var(--cream);
      background: rgba(255,241,213,.08);
      font-weight: 840;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      box-shadow: 4px 4px 0 rgba(0,0,0,.65);
      transition: transform .18s ease, filter .18s ease, opacity .18s ease;
    }
    a:hover, button:hover { transform: translate(-1px, -2px); filter: brightness(1.08); }
    button:disabled { opacity: .55; cursor: wait; transform: none; }
    button.primary { background: linear-gradient(135deg, #ffd164, #ff7a1a 52%, #f0441f); color: #150905; border-color: var(--ink); }
    .row { display: flex; gap: 9px; flex-wrap: wrap; align-items: center; }
    .panel {
      border: 2px solid var(--ink);
      border-radius: 6px;
      background: var(--panel);
      box-shadow: 7px 7px 0 rgba(0,0,0,.72), 0 24px 80px rgba(0,0,0,.36);
      backdrop-filter: blur(22px);
      padding: 16px;
      position: relative;
      overflow: hidden;
      margin-bottom: 16px;
    }
    .panel::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(120deg, rgba(255,255,255,.08), transparent 22%, transparent 78%, rgba(255,255,255,.04)),
        repeating-linear-gradient(-12deg, transparent 0 18px, rgba(255,159,28,.055) 19px 21px);
      opacity: .72;
    }
    .panel > * { position: relative; z-index: 1; }
    h2 { margin: 0 0 12px; font-size: 14px; text-transform: uppercase; letter-spacing: .08em; color: var(--amber); text-shadow: 2px 2px 0 #000; }
    input, select {
      border: 2px solid rgba(255,178,77,.34);
      background: rgba(8,6,4,.82);
      color: var(--text);
      border-radius: 7px;
      padding: 10px 11px;
      font: inherit;
      outline: none;
    }
    input:focus, select:focus { border-color: var(--amber); box-shadow: 0 0 0 3px rgba(255,159,28,.17); }
    .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .metric { border: 2px solid rgba(255,178,77,.22); border-radius: 8px; padding: 11px; background: rgba(8,6,4,.54); }
    .metric span { color: var(--muted); font-size: 12px; }
    .metric strong { display: block; font-size: 24px; margin-top: 5px; }
    .cards { display: grid; gap: 10px; }
    .card {
      border: 2px solid rgba(255,178,77,.2);
      border-radius: 8px;
      padding: 12px;
      background: linear-gradient(135deg, rgba(255,159,28,.09), rgba(255,255,255,.03));
      display: grid;
      gap: 8px;
      animation: rise .28s ease both;
      box-shadow: 4px 4px 0 rgba(0,0,0,.42);
    }
    .card-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
    .muted { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .badge { border: 1px solid rgba(255,255,255,.18); border-radius: 999px; padding: 5px 7px; font-size: 11px; font-weight: 850; background: rgba(0,0,0,.42); white-space: nowrap; }
    .allow { color: var(--green); }
    .challenge { color: var(--amber); }
    .block { color: var(--red); }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 260px;
      overflow: auto;
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 10px;
      background: rgba(8,6,4,.82);
      color: var(--cream);
      font-size: 12px;
      line-height: 1.45;
    }
    .hidden { display: none; }
    @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes rush { to { transform: skewY(-5deg) translateX(-120px); } }
    @media (max-width: 920px) { header { grid-template-columns: 1fr; } .stats { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>Gateway Logs</h1>
        <p>Every protected request leaves an audit trail with decision, model, risk, latency, trust context, and policy trace from the live database.</p>
      </div>
      <div class="row"><a href="/dashboard">Dashboard</a><a href="/models-manager">Models</a><a href="/control-plane">Control Plane</a><button id="logoutBtn">Logout</button></div>
    </header>
    <section class="panel" style="display:none">
      <div class="row">
        <input id="token" placeholder="Paste bearer token or login below" style="flex:1;min-width:280px" />
        <input id="username" placeholder="username" />
        <input id="password" type="password" placeholder="password" />
        <button id="loginBtn" class="primary">Login</button>
        <span id="roleBadge" class="badge">viewer</span>
      </div>
    </section>
    <section class="panel">
      <div class="stats">
        <div class="metric"><span>Total requests</span><strong id="totalRequests">--</strong></div>
        <div class="metric"><span>Blocked</span><strong id="blockedRequests">--</strong></div>
        <div class="metric"><span>Challenged</span><strong id="challengedRequests">--</strong></div>
        <div class="metric"><span>Block rate</span><strong id="blockRate">--</strong></div>
      </div>
    </section>
    <section class="panel">
      <div class="row" style="justify-content:space-between;margin-bottom:12px">
        <h2 style="margin:0">Request Trace</h2>
        <div class="row">
          <select id="decision">
            <option value="">All decisions</option>
            <option value="allow">Allow</option>
            <option value="challenge">Challenge</option>
            <option value="block">Block</option>
          </select>
          <input id="modelId" type="number" min="1" placeholder="model id" />
          <select id="limit">
            <option>25</option>
            <option selected>50</option>
            <option>100</option>
            <option>250</option>
          </select>
          <button id="refreshBtn" class="primary">Refresh</button>
        </div>
      </div>
      <div id="logs" class="cards"></div>
    </section>
  </div>
  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    let isAdmin = false;
    const authHeaders = () => ({ Authorization: `Bearer ${$("token").value.trim()}` });
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    function hydrateTokenFromUrl() {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token") || sessionStorage.getItem("zta_token");
      if (token) {
        $("token").value = token;
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        window.location.href = "/login?next=/logs";
      }
    }
    async function login() {
      const form = new URLSearchParams();
      form.set("username", $("username").value);
      form.set("password", $("password").value);
      const data = await request(`${api}/auth/token`, { method: "POST", body: form });
      $("token").value = data.access_token;
      sessionStorage.setItem("zta_token", data.access_token);
      await refreshAll();
    }
    async function loadRole() {
      const profile = await request(`${api}/auth/me/profile`, { headers: authHeaders() });
      isAdmin = (profile.user.scopes || []).includes("admin");
      $("roleBadge").textContent = isAdmin ? "admin audit" : "my logs";
      $("decision").disabled = !isAdmin;
      $("modelId").disabled = !isAdmin;
      $("limit").disabled = !isAdmin;
    }
    async function loadMetrics() {
      const data = await request(`${api}/monitoring/metrics`, { headers: authHeaders() });
      $("totalRequests").textContent = data.total_requests ?? 0;
      $("blockedRequests").textContent = data.blocked_requests ?? 0;
      $("challengedRequests").textContent = data.challenged_requests ?? 0;
      $("blockRate").textContent = `${data.block_rate ?? 0}%`;
    }
    async function loadLogs() {
      let path = `${api}/monitoring/logs/me`;
      if (isAdmin) {
        const params = new URLSearchParams();
        params.set("limit", $("limit").value);
        if ($("decision").value) params.set("decision", $("decision").value);
        if ($("modelId").value) params.set("model_id", $("modelId").value);
        path = `${api}/monitoring/logs?${params.toString()}`;
      }
      const data = await request(path, { headers: authHeaders() });
      const rows = data.logs || [];
      $("logs").innerHTML = rows.map((log) => {
        const trace = log.decision_trace || {};
        const snapshot = log.decision_input_snapshot || {};
        const title = `${log.model_name || "Model " + log.model_id} - ${log.username || "user " + log.user_id}`;
        return `<article class="card">
          <div class="card-head">
            <div><strong>${title}</strong><div class="muted">${log.timestamp || ""} - prompt hash ${log.prompt_hash || ""}</div></div>
            <span class="badge ${log.decision}">${log.decision}</span>
          </div>
          <div class="row">
            <span class="badge">security ${Number(log.security_score || 0).toFixed(3)}</span>
            <span class="badge">prompt ${Number(log.prompt_risk_score || 0).toFixed(3)}</span>
            <span class="badge">output ${Number(log.output_risk_score || 0).toFixed(3)}</span>
            <span class="badge">${Number(log.latency_ms || 0).toFixed(1)} ms</span>
            <span class="badge">${log.secure_mode_enabled ? "secure mode" : "standard mode"}</span>
          </div>
          <div class="muted">${log.reason || "No decision reason captured."}</div>
          <pre>${JSON.stringify({ trace, snapshot }, null, 2)}</pre>
        </article>`;
      }).join("") || `<div class="card"><strong>No logs yet.</strong><div class="muted">Run a pre-screen or safe inference request to generate audit events.</div></div>`;
    }
    async function refreshAll() {
      await loadRole();
      await Promise.all([loadMetrics(), loadLogs()]);
    }
    $("loginBtn").addEventListener("click", login);
    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      window.location.href = "/login";
    });
    $("refreshBtn").addEventListener("click", async () => {
      $("refreshBtn").disabled = true;
      try { await refreshAll(); } catch (err) { $("logs").innerHTML = `<pre>${String(err.message || err)}</pre>`; }
      finally { $("refreshBtn").disabled = false; }
    });
    hydrateTokenFromUrl();
    if ($("token").value.trim()) refreshAll().catch((err) => { $("logs").innerHTML = `<pre>${String(err.message || err)}</pre>`; });
  </script>
</body>
</html>
"""
