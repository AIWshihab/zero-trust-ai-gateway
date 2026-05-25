from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard — Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --bg:    #08080a; --bg-1: #0d0f14; --bg-2: #111420; --bg-3: #181b28;
      --border: rgba(255,255,255,.08); --b2: rgba(255,255,255,.13);
      --cyan: #00d4ff; --cyan-d: rgba(0,212,255,.1);
      --green: #22d3a0; --amber: #f5a623; --red: #ff4d6d;
      --text: #edf2ff; --muted: #7c8499; --muted2: #9aa0b4;
      --mono: 'JetBrains Mono', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--text); }
    .shell { padding: 22px clamp(14px,3vw,32px) 36px; }
    /* ── Header ── */
    .page-header {
      margin-bottom: 24px;
    }
    .gt-label {
      font-size: 11px; font-weight: 600; letter-spacing: .1em;
      text-transform: uppercase; color: var(--muted); margin-bottom: 8px; display: block;
    }
    .gt-label::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    h1 { font-size: clamp(26px, 4vw, 42px); font-weight: 800; color: var(--text); margin: 0 0 6px; letter-spacing: -.3px; }
    .page-desc { color: var(--muted); font-size: 14px; line-height: 1.6; max-width: 700px; }
    /* ── Stats strip ── */
    .stats { display: grid; grid-template-columns: repeat(5, minmax(130px, 1fr)); gap: 10px; margin-bottom: 20px; }
    .stat {
      border: 1px solid var(--b2); border-radius: 8px; background: var(--bg-2);
      padding: 14px; cursor: pointer; transition: border-color .18s;
    }
    .stat:hover { border-color: rgba(0,212,255,.36); }
    .stat .label { font-size: 11px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
    .stat .value { margin-top: 8px; font-size: 28px; font-weight: 800; color: var(--text); font-variant-numeric: tabular-nums; }
    .stat .hint  { margin-top: 4px; font-size: 11px; color: var(--cyan); opacity: 0; transition: opacity .15s; }
    .stat:hover .hint { opacity: 1; }
    /* ── Two-column soc section ── */
    .soc-grid { display: grid; grid-template-columns: 1.1fr .9fr; gap: 14px; margin-bottom: 20px; }
    .card {
      border: 1px solid var(--b2); border-radius: 8px; background: var(--bg-2);
      padding: 18px; transition: border-color .18s;
    }
    .card:hover { border-color: rgba(0,212,255,.28); }
    .card-title { font-size: 12px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--cyan); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
    .metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 14px; }
    .metric { border: 1px solid var(--border); border-radius: 7px; padding: 10px; background: var(--bg-3); text-align: center; }
    .metric .mlabel { font-size: 10px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
    .metric strong { display: block; font-size: 20px; font-weight: 800; color: var(--text); margin-top: 4px; }
    .mini-bars { display: grid; gap: 7px; }
    .bar { display: grid; grid-template-columns: 100px 1fr 40px; gap: 8px; align-items: center; font-size: 12px; color: var(--muted2); }
    .track { height: 6px; border-radius: 999px; background: var(--bg-3); overflow: hidden; }
    .fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--green), var(--amber), var(--red)); }
    /* ── Live feed ── */
    .feed-section { margin-bottom: 20px; }
    .feed-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
    .live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse 1.8s ease-in-out infinite; }
    .live-dot.stale { background: var(--muted); box-shadow: none; animation: none; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.45} }
    .feed-status { font-size: 11px; color: var(--muted); }
    .feed-list { display: grid; gap: 5px; }
    .feed-entry {
      display: grid; grid-template-columns: 10px 90px 1fr auto auto;
      gap: 8px; align-items: center;
      border: 1px solid var(--border); border-radius: 7px;
      padding: 8px 12px; background: var(--bg-2); font-size: 12px;
      animation: slideIn .2s ease both;
      transition: border-color .15s;
    }
    .feed-entry:hover { border-color: rgba(0,212,255,.28); }
    @keyframes slideIn { from{opacity:0;transform:translateY(-3px)} to{opacity:1;transform:translateY(0)} }
    .feed-dot { width: 8px; height: 8px; border-radius: 50%; }
    .feed-dot.allow     { background: var(--green); }
    .feed-dot.challenge { background: var(--amber); }
    .feed-dot.block     { background: var(--red); }
    .feed-time { color: var(--muted); font-size: 11px; white-space: nowrap; }
    .feed-who  { color: var(--muted2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .feed-dec  { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }
    .feed-dec.allow     { color: var(--green); border: 1px solid rgba(34,211,160,.3); background: rgba(34,211,160,.08); }
    .feed-dec.challenge { color: var(--amber); border: 1px solid rgba(245,166,35,.3); background: rgba(245,166,35,.08); }
    .feed-dec.block     { color: var(--red);   border: 1px solid rgba(255,77,109,.3); background: rgba(255,77,109,.08); }
    .feed-risk { color: var(--muted); font-size: 11px; white-space: nowrap; }
    .feed-empty { padding: 24px; text-align: center; color: var(--muted); font-size: 13px; border: 1px dashed var(--border); border-radius: 8px; }
    /* ── Option cards ── */
    .options-grid { display: grid; grid-template-columns: repeat(3, minmax(240px, 1fr)); gap: 12px; }
    .option-card {
      border: 1px solid var(--b2); border-radius: 8px; background: var(--bg-2);
      padding: 20px; display: flex; flex-direction: column; gap: 8px;
      transition: border-color .18s;
    }
    .option-card:hover { border-color: rgba(0,212,255,.32); }
    .option-card.locked { opacity: .5; pointer-events: none; }
    .option-cat  { font-size: 10px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--cyan); }
    .option-name { font-size: 16px; font-weight: 700; color: var(--text); }
    .option-desc { font-size: 13px; color: var(--muted); line-height: 1.55; }
    .option-meta { font-size: 12px; color: var(--muted); line-height: 1.45; flex: 1; }
    .option-btn  {
      margin-top: 10px; padding: 9px 14px; border-radius: 7px;
      border: 1px solid var(--b2); background: var(--bg-3); color: var(--muted2);
      font-size: 13px; font-weight: 600; cursor: pointer; text-align: center;
      transition: border-color .15s, color .15s;
    }
    .option-btn:hover { border-color: rgba(0,212,255,.36); color: var(--cyan); }
    /* ── Extension card ── */
    .ext-panel {
      border: 1px solid var(--b2); border-radius: 8px; background: var(--bg-2);
      padding: 18px; margin-bottom: 20px;
    }
    .ext-panel:hover { border-color: rgba(0,212,255,.28); }
    .ext-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
    .ext-info { flex: 1; min-width: 0; }
    .ext-title { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
    .ext-status { font-size: 12px; color: var(--muted); display: flex; align-items: center; gap: 6px; }
    .ext-status .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
    .ext-status .dot.on  { background: var(--green); box-shadow: 0 0 6px var(--green); }
    .ext-status .dot.off { background: var(--muted); }
    .ext-status .dot.spin { background: var(--cyan); box-shadow: 0 0 6px var(--cyan); animation: pulse 1.2s ease-in-out infinite; }
    .ext-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .ext-connect-btn {
      padding: 9px 18px; border-radius: 7px; border: 1px solid var(--cyan);
      background: var(--cyan); color: #000; font-size: 13px; font-weight: 700;
      cursor: pointer; transition: background .15s;
    }
    .ext-connect-btn:hover { background: #00bde8; border-color: #00bde8; }
    .ext-connect-btn:disabled { opacity: .55; cursor: wait; }
    .ext-connect-btn.secondary {
      background: var(--bg-3); color: var(--muted2); border-color: var(--b2); font-weight: 600;
    }
    .ext-connect-btn.secondary:hover { border-color: var(--cyan); color: var(--cyan); background: var(--bg-3); }
    .ext-progress {
      font-size: 13px; color: var(--muted); padding: 10px 12px;
      border-radius: 7px; border: 1px solid var(--border); background: var(--bg-3);
      display: none; margin-top: 10px;
    }
    .ext-progress.ok  { color: var(--green); border-color: rgba(34,211,160,.28); background: rgba(34,211,160,.06); }
    .ext-progress.err { color: var(--red);   border-color: rgba(255,77,109,.28); background: rgba(255,77,109,.06); }
    /* ── Status note ── */
    .note {
      border: 1px solid var(--b2); border-radius: 8px; padding: 14px;
      background: var(--bg-2); color: var(--muted2); font-size: 13px; line-height: 1.55;
    }
    .note.warn { border-color: rgba(245,166,35,.32); background: rgba(245,166,35,.06); }
    .note.bad  { border-color: rgba(255,77,109,.32);  background: rgba(255,77,109,.06); color: var(--text); }
    .note ol   { margin: 8px 0 0 18px; display: grid; gap: 5px; }
    @media (max-width: 1100px) { .stats { grid-template-columns: repeat(3, 1fr); } .options-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 800px)  { .stats { grid-template-columns: repeat(2, 1fr); } .soc-grid { grid-template-columns: 1fr; } .options-grid { grid-template-columns: 1fr; } }
    @media (max-width: 500px)  { .stats { grid-template-columns: 1fr; } .metrics-row { grid-template-columns: repeat(2,1fr); } }
  </style>
</head>
<body>
  <main class="shell">
    <div class="page-header">
      <span class="gt-label">Behaviour-Aware Secure AI Inference</span>
      <h1>Zero Trust AI Gateway</h1>
      <p class="page-desc">A research-grade Zero Trust gateway for secure AI model serving. Every inference request is screened by the policy engine before it reaches a model.</p>
    </div>

    <section class="stats">
      <div class="stat" data-href="/dashboard/models"><div class="label">Active Models</div><div id="modelsValue" class="value">--</div><div class="hint">View models →</div></div>
      <div class="stat" data-href="/dashboard/security-monitor"><div class="label">Total Requests</div><div id="controlsValue" class="value">--</div><div class="hint">View decisions →</div></div>
      <div class="stat" data-href="/dashboard/security-monitor"><div class="label">Blocked / Challenged</div><div id="rulesValue" class="value">--</div><div class="hint">View threats →</div></div>
      <div class="stat" data-href="/dashboard/security-monitor"><div class="label">Average Risk</div><div id="logsValue" class="value">--</div><div class="hint">View trace →</div></div>
      <div class="stat" data-href="/dashboard/models"><div class="label">Runtime-Ready</div><div id="eventsValue" class="value">--</div><div class="hint">Check readiness →</div></div>
    </section>

    <section class="soc-grid">
      <article class="card">
        <div class="card-title"><span class="live-dot" id="liveDot"></span>Gateway Decisions</div>
        <div class="metrics-row">
          <div class="metric"><div class="mlabel">Allowed</div><strong id="socAllowed">--</strong></div>
          <div class="metric"><div class="mlabel">Challenged</div><strong id="socChallenged">--</strong></div>
          <div class="metric"><div class="mlabel">Blocked</div><strong id="socBlocked">--</strong></div>
          <div class="metric"><div class="mlabel">Alerts</div><strong id="socAlerts">--</strong></div>
        </div>
        <div id="socBars" class="mini-bars"></div>
      </article>
      <article class="card">
        <div class="card-title">Model Readiness</div>
        <div id="socAlertList" style="font-size:13px;color:var(--muted);line-height:1.6">Loading readiness notes...</div>
      </article>
    </section>

    <section class="feed-section">
      <div class="feed-head">
        <span class="gt-label" style="margin-bottom:0">Recent Security Decisions</span>
        <span class="live-dot" id="feedDot"></span>
        <span class="feed-status" id="feedStatus">Connecting...</span>
      </div>
      <div id="liveFeed" class="feed-list"><div class="feed-empty">No log entries yet. Send a chat message to generate logs.</div></div>
    </section>

    <div id="welcomePanel" class="note warn" style="margin-bottom:16px;display:none"></div>

    <!-- Extension Widget -->
    <div class="ext-panel" id="extPanel">
      <div class="ext-header">
        <div class="ext-info">
          <div class="gt-label" style="margin-bottom:4px">Browser Protection</div>
          <div class="ext-title">Browser Extension</div>
          <div class="ext-status" id="extStatus">
            <span class="dot spin" id="extDot"></span>
            <span id="extStatusText">Detecting extension...</span>
          </div>
        </div>
        <div class="ext-actions">
          <button class="ext-connect-btn" id="extConnectBtn">⚡ Quick Connect</button>
          <a href="/dashboard/extension/install" class="ext-connect-btn secondary">Setup Guide</a>
        </div>
      </div>
      <div class="ext-progress" id="extProgress"></div>
    </div>

    <div style="margin-bottom:12px">
      <span class="gt-label">Gateway Modules</span>
    </div>
    <section id="options" class="options-grid"></section>
    <div id="status" class="note" style="margin-top:14px">Loading gateway modules...</div>
  </main>

  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    const $ = (id) => document.getElementById(id);
    if (!token) location.href = "/login?next=/dashboard";
    const authHeaders = () => ({ Authorization: `Bearer ${token}` });

    function parseApiError(data, status) {
      const detail = typeof data === "object" ? data?.detail : data;
      if (detail && typeof detail === "object") {
        if (detail.title) return `${detail.title}${detail.explanation ? ": " + detail.explanation : ""}`;
        if (detail.message) return detail.message;
      }
      if (typeof detail === "string" && detail.trim()) return detail;
      if (status === 401 || status === 403) return "Your session expired. Please log in again.";
      if (status >= 500) return "Gateway services are temporarily unavailable.";
      return "Unable to load dashboard data.";
    }
    async function request(path) {
      const res = await fetch(path, { headers: authHeaders() });
      const text = await res.text();
      let data; try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) { sessionStorage.removeItem("zta_token"); location.href = "/login?next=/dashboard"; throw new Error(parseApiError(data, res.status)); }
      return data;
    }
    async function softRequest(path) {
      const res = await fetch(path, { headers: authHeaders() });
      const text = await res.text();
      let data; try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(parseApiError(data, res.status));
      return data;
    }
    function isAdmin(user) { return Boolean(user?.is_admin); }

    function renderWelcome(data) {
      const panel = $("welcomePanel");
      const readyModelCount = Number(data.runtime?.ready_models || 0);
      const canChatNow = readyModelCount > 0;
      const lines = [
        canChatNow
          ? "Secure Chat is available. Each inference request is verified against the behavioural risk engine and policy controls."
          : "No model is runtime-ready yet. Register and activate a model to begin protected inference.",
        "Use Research Evaluation to replay decisions, compare models, and inspect control effectiveness.",
        isAdmin(data.user)
          ? "Policy Engine, Model Registry, and Research Evaluation tools are available below."
          : "Register your own model endpoints in Models to use them through the Zero Trust enforcement pipeline."
      ];
      panel.style.display = "block";
      panel.innerHTML = `<strong style="color:var(--text)">Enforcement Status</strong><div style="margin-top:6px">Runtime-ready models: <b style="color:var(--cyan)">${readyModelCount}</b></div><ol>${lines.map(l => `<li>${l}</li>`).join("")}</ol>`;
      const params = new URLSearchParams(location.search);
      if (params.get("welcome") === "1") {
        params.delete("welcome");
        history.replaceState({}, document.title, `${location.pathname}${params.toString() ? "?" + params.toString() : ""}`);
      }
    }
    function render(data) {
      $("modelsValue").textContent = data.overview.active_models;
      $("controlsValue").textContent = data.overview.request_logs;
      $("options").innerHTML = data.options.map(item => `
        <article class="option-card ${item.requires_admin && !data.user.is_admin ? "locked" : ""}" data-href="${item.href}">
          <div class="option-cat">${item.category}</div>
          <div class="option-name">${item.title}${item.requires_admin ? " <span style='font-size:10px;color:var(--amber)'>[Admin]</span>" : ""}</div>
          <div class="option-desc">${item.description}</div>
          <div class="option-meta">${item.summary}</div>
          <div class="option-btn">Open ${item.title} →</div>
        </article>`).join("");
      document.querySelectorAll(".option-card[data-href]").forEach(el =>
        el.addEventListener("click", () => location.href = el.dataset.href));
      document.querySelectorAll(".stat[data-href]").forEach(el =>
        el.addEventListener("click", () => location.href = el.dataset.href));
      const hiddenAdmin = Number(data.overview?.admin_hidden_options || 0);
      $("status").className = "note";
      $("status").textContent = hiddenAdmin > 0
        ? `Gateway active. ${hiddenAdmin} policy workspace${hiddenAdmin === 1 ? "" : "s"} restricted to admin accounts.`
        : "Gateway active. All modules loaded.";
      renderWelcome(data);
    }
    async function loadSoc() {
      try {
        const [metrics, alerts, heatmap] = await Promise.all([
          softRequest(`${api}/monitoring/metrics`),
          softRequest(`${api}/monitoring/soc/alerts`),
          softRequest(`${api}/monitoring/soc/threat-heatmap`)
        ]);
        $("socAllowed").textContent = metrics.allowed_requests ?? 0;
        $("socChallenged").textContent = metrics.challenged_requests ?? 0;
        $("socBlocked").textContent = metrics.blocked_requests ?? 0;
        $("socAlerts").textContent = alerts.total ?? 0;
        $("controlsValue").textContent = metrics.total_requests ?? 0;
        $("rulesValue").textContent = `${Number(metrics.blocked_requests ?? 0) + Number(metrics.challenged_requests ?? 0)}`;
        const avgRisk = metrics.average_risk ?? metrics.avg_prompt_risk_score;
        $("logsValue").textContent = avgRisk != null ? `${Math.round(Number(avgRisk) * 100)}%` : "--";
        $("eventsValue").textContent = `${Number(metrics.ready_models ?? 0) || $("modelsValue").textContent}`;
        const cells = (heatmap.cells || []).slice(0, 5);
        const max = Math.max(1, ...cells.map(c => c.count || 0));
        $("socBars").innerHTML = cells.map(cell => `
          <div class="bar">
            <span>${cell.attack_stage}</span>
            <div class="track"><div class="fill" style="width:${Math.max(4, ((cell.count || 0) / max) * 100)}%"></div></div>
            <b style="color:var(--text)">${cell.count}</b>
          </div>`).join("") || `<div style="color:var(--muted);font-size:13px">No attack timeline data yet.</div>`;
        $("socAlertList").innerHTML = (alerts.alerts || []).slice(0, 4).map(a => {
          const cls = a.severity === "high" ? "color:var(--red)" : "color:var(--amber)";
          return `<div style="display:flex;gap:8px;align-items:start;margin:6px 0"><span style="${cls};font-size:12px;font-weight:700">${a.type}</span><span style="color:var(--muted);font-size:12px">${a.message}</span></div>`;
        }).join("") || "<span>No readiness or policy flags.</span>";
      } catch {
        $("socAlertList").innerHTML = `<span style="color:var(--muted)">Security telemetry unavailable or no decisions yet.</span>`;
      }
    }
    let liveLogIds = new Set();
    function fmtTime(iso) {
      if (!iso) return "—";
      const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
      const abs = new Date(iso).toLocaleString([], { month:"short", day:"numeric", hour:"2-digit", minute:"2-digit" });
      const rel = diff < 60 ? `${diff}s ago` : diff < 3600 ? `${Math.floor(diff/60)}m ago` : diff < 86400 ? `${Math.floor(diff/3600)}h ago` : `${Math.floor(diff/86400)}d ago`;
      return `<span title="${abs}">${rel}</span>`;
    }
    function esc(s) { return String(s||"—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]); }
    function riskLabel(score) {
      if (score == null) return "—";
      const pct = Math.round(score * 100);
      const color = pct >= 75 ? "var(--red)" : pct >= 50 ? "var(--amber)" : "var(--green)";
      return `<span style="color:${color}">${pct}%</span>`;
    }
    async function loadLiveLogs() {
      try {
        const data = await softRequest(`${api}/monitoring/logs?limit=25`);
        const logs = data.logs || [];
        const dot = $("feedDot"); const status = $("feedStatus");
        if (dot) dot.classList.remove("stale");
        if (status) status.textContent = `${logs.length} entries · ${new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"})}`;
        if (!logs.length) { $("liveFeed").innerHTML = '<div class="feed-empty">No log entries yet. Send a chat message to generate logs.</div>'; return; }
        const newEntries = logs.filter(l => !liveLogIds.has(l.id));
        newEntries.forEach(l => liveLogIds.add(l.id));
        const dec = d => d === "block" ? "block" : d === "challenge" ? "challenge" : "allow";
        $("liveFeed").innerHTML = logs.map(l => {
          const d = dec(l.decision);
          return `<div class="feed-entry">
            <span class="feed-dot ${d}"></span>
            <span class="feed-time">${fmtTime(l.timestamp)}</span>
            <span class="feed-who">${esc(l.username)} · ${esc(l.model_name)}</span>
            <span class="feed-dec ${d}">${d.toUpperCase()}</span>
            <span class="feed-risk">${riskLabel(l.prompt_risk_score)}</span>
          </div>`;
        }).join("");
      } catch {
        const dot = $("feedDot"); const status = $("feedStatus");
        if (dot) dot.classList.add("stale");
        if (status) status.textContent = "Feed unavailable";
      }
    }
    async function loadRuntimeOverview(navData) {
      try {
        const readiness = await request(`${api}/models/runtime-readiness`);
        const ready = (readiness || []).filter(item => item.runtime_ready !== false).length;
        navData.runtime = { ready_models: ready };
      } catch {
        navData.runtime = { ready_models: 0 };
      }
      navData.overview.admin_hidden_options = isAdmin(navData.user) ? 0 : Number(navData.overview?.admin_option_count || 0);
      return navData;
    }
    request(`${api}/navigation/options`)
      .then(data => loadRuntimeOverview(data))
      .then(data => { render(data); loadSoc(); loadLiveLogs(); })
      .catch(err => {
        $("status").className = "note bad";
        $("status").textContent = "Could not load dashboard. Please refresh and try again.";
      });
    setInterval(loadLiveLogs, 5000);

    /* ── Extension Widget ── */
    function pingExtension() {
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
        }, 1000);
        window.addEventListener("message", handler);
        window.postMessage({ type: "ZTA_GATEWAY_EXTENSION_PING", nonce }, "*");
      });
    }

    function setExtStatus(text, dotClass) {
      $("extStatusText").textContent = text;
      $("extDot").className = "dot " + (dotClass || "off");
    }

    function setExtProgress(text, cls) {
      const el = $("extProgress");
      el.style.display = text ? "block" : "none";
      el.className = "ext-progress" + (cls ? " " + cls : "");
      el.innerHTML = text || "";
    }

    async function quickConnect() {
      const btn = $("extConnectBtn");
      btn.disabled = true;
      setExtProgress("Generating secure pairing token...");

      try {
        const res = await fetch(`${api}/extension/setup-session`, {
          method: "POST", headers: authHeaders()
        });
        if (!res.ok) throw new Error("Failed to create pairing session");
        const session = await res.json();

        setExtProgress("Pinging extension...");
        const ext = await pingExtension();

        if (!ext.detected) {
          setExtProgress(
            'Extension not detected. <a href="/downloads/browser-extension.zip" style="color:var(--cyan)">Download extension</a>, load it in Chrome (Developer Mode → Load unpacked), then click Quick Connect again.',
            "err"
          );
          btn.disabled = false;
          return;
        }

        setExtProgress("Connecting to extension...");
        const parsed = new URL(session.connect_url);
        const pairingToken = parsed.searchParams.get("token");
        const gatewayApiUrl = parsed.searchParams.get("gateway_api_url");
        const setupSessionId = parsed.searchParams.get("setup_session_id");

        const result = await new Promise((resolve, reject) => {
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
            reject(new Error("Timeout — extension did not respond. Try the Setup Guide."));
          }, 12000);
          window.addEventListener("message", handler);
          window.postMessage({
            type: "ZTA_AUTOCONNECT_REQUEST",
            gatewayApiUrl, pairingToken, setupSessionId,
            deviceLabel: "Dashboard auto-connect"
          }, "*");
        });

        setExtStatus(`Connected · Device ${result.deviceId} · v${ext.version}`, "on");
        setExtProgress(`Extension paired successfully. Device ID: ${result.deviceId}. All prompts are now protected.`, "ok");
        btn.textContent = "✓ Connected";
        btn.style.background = "var(--green)";
        btn.style.borderColor = "var(--green)";
        btn.disabled = false;

      } catch (err) {
        setExtProgress("Connection failed: " + err.message, "err");
        setExtStatus("Not connected", "off");
        btn.disabled = false;
      }
    }

    $("extConnectBtn").addEventListener("click", quickConnect);

    pingExtension().then(ext => {
      if (ext.detected) {
        setExtStatus(`Extension v${ext.version} detected — ready to connect`, "on");
      } else {
        setExtStatus("Extension not installed", "off");
        const btn = $("extConnectBtn");
        btn.textContent = "Download Extension";
        btn.style.background = "var(--bg-3)";
        btn.style.color = "var(--cyan)";
        btn.style.borderColor = "var(--b2)";
        btn.style.fontWeight = "600";
        btn.addEventListener("click", () => { location.href = "/downloads/browser-extension.zip"; }, { once: true });
      }
    });
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
