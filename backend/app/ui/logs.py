from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


LOGS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Audit Trail — Zero Trust AI Gateway</title>
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
    .shell { padding: 20px clamp(14px,3vw,32px) 32px; }
    .page-header {
      display: grid;
      grid-template-columns: minmax(280px,1fr) auto;
      gap: 16px;
      align-items: start;
      margin-bottom: 20px;
    }
    .page-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
    .page-eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .page-header h1 { font-size: clamp(22px,3vw,34px); font-weight: 700; color: var(--text); line-height: 1.1; }
    .page-header p { font-size: 14px; color: var(--muted); line-height: 1.6; max-width: 640px; margin-top: 6px; }
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
    button:disabled { opacity: .5; cursor: wait; }
    button.primary { background: var(--cyan); color: #000; border-color: var(--cyan); font-weight: 700; }
    button.primary:hover { background: #00bde8; }
    .stats-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
    .metric {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      background: var(--bg-1);
      transition: border-color .2s;
    }
    .metric:hover { border-color: rgba(0,212,255,.18); }
    .metric-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
    .metric-value { font-size: 24px; font-weight: 700; margin-top: 5px; color: var(--text); }
    .panel {
      border: 1px solid var(--b2);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 16px;
      margin-bottom: 16px;
    }
    .panel-hdr { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; }
    .panel-title { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
    .panel-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    input, select {
      border: 1px solid var(--b2);
      border-radius: 7px;
      background: var(--bg-3);
      color: var(--text);
      padding: 8px 12px;
      font: inherit;
      font-size: 13px;
      outline: none;
      transition: border-color .18s;
    }
    input:focus, select:focus { border-color: rgba(0,212,255,.42); }
    input::placeholder { color: var(--muted); }
    select option { background: var(--bg-3); }
    .cards { display: grid; gap: 10px; }
    .card {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      background: var(--bg-2);
      display: grid;
      gap: 8px;
      animation: rise .25s ease both;
      transition: border-color .2s;
    }
    .card:hover { border-color: rgba(0,212,255,.18); }
    .card-head { display: flex; justify-content: space-between; gap: 10px; align-items: start; }
    .card-title-wrap strong { display: block; font-size: 14px; font-weight: 700; color: var(--text); }
    .card-meta { font-size: 12px; color: var(--muted); margin-top: 2px; font-family: var(--mono); }
    .badge { border: 1px solid var(--b2); border-radius: 999px; padding: 4px 8px; font-size: 11px; font-weight: 700; background: var(--bg-3); white-space: nowrap; color: var(--muted); }
    .allow     { color: var(--green); border-color: rgba(34,211,160,.3); background: rgba(34,211,160,.08); }
    .challenge { color: var(--amber); border-color: rgba(245,166,35,.3); background: rgba(245,166,35,.08); }
    .block     { color: var(--red);   border-color: rgba(255,77,109,.3); background: rgba(255,77,109,.08); }
    .score-row { display: flex; gap: 6px; flex-wrap: wrap; }
    .card-reason { font-size: 13px; color: var(--muted); line-height: 1.45; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 240px;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 7px;
      padding: 10px;
      background: var(--bg-3);
      color: var(--muted);
      font-family: var(--mono);
      font-size: 11px;
      line-height: 1.5;
    }
    .hidden { display: none; }
    @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 920px) { .page-header { grid-template-columns: 1fr; } .stats-strip { grid-template-columns: repeat(2,1fr); } }
    @media (max-width: 600px) { .filter-row { flex-direction: column; align-items: stretch; } .card-head { flex-direction: column; align-items: flex-start; gap: 6px; } }
    @media (max-width: 420px) { .stats-strip { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Audit Trail</div>
        <h1>Request Audit Log</h1>
        <p>Structured audit record of every enforcement decision: request risk score, model used, policy controls triggered, trust state at decision time, and enforcement outcome.</p>
      </div>
      <div class="hdr-row">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/models">Models</a>
        <a href="/dashboard/policy">Policy Engine</a>
        <button id="logoutBtn">Logout</button>
      </div>
    </div>
    <section style="display:none">
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:14px;background:var(--bg-1);border:1px solid var(--b2);border-radius:8px;margin-bottom:16px">
        <input id="token" placeholder="Paste bearer token or login below" style="flex:1;min-width:240px" />
        <input id="username" placeholder="username" />
        <input id="password" type="password" placeholder="password" />
        <button id="loginBtn" class="primary">Login</button>
        <span id="roleBadge" class="badge">viewer</span>
      </div>
    </section>
    <section class="stats-strip">
      <div class="metric"><div class="metric-label">Total Requests</div><div class="metric-value" id="totalRequests">--</div></div>
      <div class="metric"><div class="metric-label">Blocked</div><div class="metric-value" id="blockedRequests">--</div></div>
      <div class="metric"><div class="metric-label">Challenged</div><div class="metric-value" id="challengedRequests">--</div></div>
      <div class="metric"><div class="metric-label">Block Rate</div><div class="metric-value" id="blockRate">--</div></div>
    </section>
    <section class="panel">
      <div class="panel-hdr">
        <div class="panel-title">Request Trace</div>
        <div class="filter-row">
          <select id="decision">
            <option value="">All decisions</option>
            <option value="allow">Allow</option>
            <option value="challenge">Challenge</option>
            <option value="block">Block</option>
          </select>
          <input id="modelId" type="number" min="1" placeholder="model id" style="width:100px" />
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
      const username = profile.user?.username || "";
      $("roleBadge").textContent = username ? `${username} · my audit trail` : "my audit trail";
    }
    async function loadMetrics() {
      const data = await request(`${api}/monitoring/metrics`, { headers: authHeaders() });
      $("totalRequests").textContent = data.total_requests ?? 0;
      $("blockedRequests").textContent = data.blocked_requests ?? 0;
      $("challengedRequests").textContent = data.challenged_requests ?? 0;
      $("blockRate").textContent = `${data.block_rate ?? 0}%`;
    }
    async function loadLogs() {
      const params = new URLSearchParams();
      params.set("limit", $("limit").value);
      if ($("decision").value) params.set("decision", $("decision").value);
      if ($("modelId").value) params.set("model_id", $("modelId").value);
      const path = `${api}/monitoring/logs?${params.toString()}`;
      const data = await request(path, { headers: authHeaders() });
      const rows = data.logs || [];
      $("logs").innerHTML = rows.map((log) => {
        const trace = log.decision_trace || {};
        const snapshot = log.decision_input_snapshot || {};
        const title = `${log.model_name || "Model " + log.model_id} — ${log.username || "user " + log.user_id}`;
        return `<article class="card">
          <div class="card-head">
            <div class="card-title-wrap"><strong>${title}</strong><div class="card-meta">${log.timestamp || ""} · prompt hash ${log.prompt_hash || ""}</div></div>
            <span class="badge ${log.decision}">${log.decision}</span>
          </div>
          <div class="score-row">
            <span class="badge">security ${Number(log.security_score || 0).toFixed(3)}</span>
            <span class="badge">prompt ${Number(log.prompt_risk_score || 0).toFixed(3)}</span>
            <span class="badge">output ${Number(log.output_risk_score || 0).toFixed(3)}</span>
            <span class="badge">${Number(log.latency_ms || 0).toFixed(1)} ms</span>
            <span class="badge">${log.secure_mode_enabled ? "secure mode" : "standard mode"}</span>
          </div>
          <div class="card-reason">${log.reason || "No decision reason captured."}</div>
          <pre>${JSON.stringify({ trace, snapshot }, null, 2)}</pre>
        </article>`;
      }).join("") || `<div class="card"><strong>No logs yet.</strong><div class="card-reason">Run a pre-screen or safe inference request to generate audit events.</div></div>`;
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
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
