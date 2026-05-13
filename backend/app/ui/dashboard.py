from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Zero Trust AI Gateway Dashboard</title>
  <style>
    :root {
      color-scheme: dark;
      --text: #fff7ea;
      --muted: #d4c0a4;
      --soft: #aab3bf;
      --amber: #ffb13b;
      --red: #ff4d3d;
      --green: #78e08f;
      --ink: #080604;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        linear-gradient(118deg, rgba(255,255,255,.035) 0 1px, transparent 1px 70px),
        radial-gradient(circle at 18% 10%, rgba(255,159,28,.25), transparent 30%),
        linear-gradient(140deg, #070706 0%, #15110d 45%, #2b1207 82%, #070706 100%);
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,241,213,.07) 2px, transparent 2px),
        linear-gradient(90deg, rgba(255,241,213,.07) 2px, transparent 2px);
      background-size: 116px 64px, 116px 64px;
      opacity: .45;
    }
    .shell { position: relative; z-index: 1; padding: 20px clamp(14px, 3vw, 34px) 34px; }
    header {
      display: grid;
      grid-template-columns: minmax(280px, 1fr) auto;
      gap: 18px;
      align-items: start;
      margin-bottom: 18px;
    }
    .eyebrow { color: var(--amber); text-transform: uppercase; letter-spacing: .12em; font-weight: 950; font-size: 12px; }
    h1 {
      margin: 6px 0 10px;
      font-size: clamp(34px, 5vw, 66px);
      line-height: .92;
      text-transform: uppercase;
      text-shadow: 4px 4px 0 #000, 8px 8px 0 rgba(244,123,32,.34);
    }
    p { color: #ffe9c5; line-height: 1.55; font-weight: 720; max-width: 860px; }
    button, a {
      border: 2px solid var(--ink);
      border-radius: 7px;
      padding: 10px 12px;
      color: #150905;
      background: linear-gradient(135deg, #ffd164, #ff7a1a 52%, #f0441f);
      font-weight: 900;
      cursor: pointer;
      text-decoration: none;
      box-shadow: 4px 4px 0 rgba(0,0,0,.75);
      font: inherit;
    }
    a.secondary, button.secondary { color: var(--text); background: rgba(255,241,213,.08); border-color: rgba(255,178,77,.42); }
    .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .stats { display: grid; grid-template-columns: repeat(5, minmax(130px, 1fr)); gap: 10px; margin-bottom: 16px; }
    .stat, .card {
      border: 2px solid var(--ink);
      border-radius: 7px;
      background: rgba(18,18,16,.94);
      box-shadow: 6px 6px 0 rgba(0,0,0,.72), 0 22px 70px rgba(0,0,0,.34);
      position: relative;
      overflow: hidden;
    }
    .stat::after, .card::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: repeating-linear-gradient(-12deg, transparent 0 19px, rgba(255,159,28,.05) 20px 22px);
    }
    .inner { position: relative; z-index: 1; padding: 14px; }
    .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 900; }
    .value { margin-top: 7px; font-size: 26px; font-weight: 950; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(260px, 1fr)); gap: 14px; }
    .soc-grid { display: grid; grid-template-columns: 1.1fr .9fr; gap: 14px; margin: 16px 0; }
    .mini-bars { display: grid; gap: 8px; margin-top: 12px; }
    .bar { display:grid; grid-template-columns: 110px 1fr 44px; gap: 8px; align-items:center; color: var(--soft); font-size: 12px; }
    .track { height: 9px; border-radius:999px; background: rgba(255,255,255,.08); overflow:hidden; }
    .fill { height:100%; border-radius:999px; background: linear-gradient(90deg, var(--green), var(--amber), var(--red)); }
    .card { min-height: 230px; display: flex; flex-direction: column; }
    .card h2 { margin: 0 0 8px; color: var(--amber); text-transform: uppercase; letter-spacing: .08em; font-size: 16px; }
    .card p { margin: 0; color: var(--soft); font-size: 13px; }
    .card .meta { margin-top: 12px; color: var(--muted); font-size: 12px; line-height: 1.45; min-height: 48px; }
    .card .actions { margin-top: auto; padding-top: 16px; }
    .locked { opacity: .58; }
    .admin { color: var(--green); }
    /* Clickable stat cards */
    .stat[data-href] { cursor: pointer; transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease; }
    .stat[data-href]:hover { transform: translateY(-2px); border-color: rgba(255,178,77,.65); box-shadow: 6px 6px 0 rgba(0,0,0,.72), 0 0 22px rgba(255,178,77,.18); }
    .stat[data-href]:active { transform: translateY(0); }
    .stat-arrow { font-size: 11px; color: var(--muted); margin-top: 6px; opacity: 0; transition: opacity .15s; letter-spacing: .04em; }
    .stat[data-href]:hover .stat-arrow { opacity: 1; }
    /* Live log feed */
    .feed-section { margin: 16px 0; }
    .feed-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
    .feed-head h2 { margin: 0; color: var(--amber); text-transform: uppercase; letter-spacing: .08em; font-size: 15px; }
    .live-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); animation: livePulse 1.6s ease-in-out infinite; flex-shrink: 0; }
    .live-dot.stale { background: var(--muted); box-shadow: none; animation: none; }
    @keyframes livePulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
    .feed-status { font-size: 11px; color: var(--muted); }
    .feed-list { display: grid; gap: 5px; }
    .feed-entry { display: grid; grid-template-columns: 10px 90px 1fr auto auto; gap: 8px; align-items: center; border: 1px solid rgba(255,178,77,.12); border-radius: 7px; padding: 7px 10px; background: rgba(18,18,16,.82); font-size: 12px; animation: fadeSlide .2s ease both; }
    @keyframes fadeSlide { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
    .feed-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .feed-dot.allow { background: var(--green); box-shadow: 0 0 6px var(--green); }
    .feed-dot.challenge { background: var(--amber); box-shadow: 0 0 6px var(--amber); }
    .feed-dot.block { background: var(--red); box-shadow: 0 0 6px var(--red); animation: livePulse 1.2s ease-in-out infinite; }
    .feed-time { color: var(--muted); font-size: 11px; white-space: nowrap; }
    .feed-who { color: var(--soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .feed-dec { font-weight: 900; font-size: 11px; padding: 2px 7px; border-radius: 4px; white-space: nowrap; letter-spacing: .05em; }
    .feed-dec.allow { color: var(--green); border: 1px solid rgba(120,224,143,.3); background: rgba(120,224,143,.08); }
    .feed-dec.challenge { color: var(--amber); border: 1px solid rgba(255,177,59,.3); background: rgba(255,177,59,.08); }
    .feed-dec.block { color: var(--red); border: 1px solid rgba(255,77,61,.3); background: rgba(255,77,61,.1); }
    .feed-risk { color: var(--muted); font-size: 11px; white-space: nowrap; }
    .feed-empty { padding: 20px; text-align: center; color: var(--muted); font-size: 13px; border: 1px dashed rgba(255,178,77,.2); border-radius: 7px; }
    .note {
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(8,6,4,.82);
      color: #fff1d5;
      line-height: 1.5;
    }
    .note.warn {
      border-color: rgba(255,178,77,.52);
      background: rgba(255,159,28,.08);
    }
    .note.bad {
      border-color: rgba(255,77,61,.48);
      background: rgba(255,77,61,.1);
      color: #ffe0dc;
    }
    .next-steps {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 6px;
      color: var(--soft);
      font-size: 13px;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(8,6,4,.82);
      color: #fff1d5;
      min-height: 90px;
    }
    @media (max-width: 1050px) { .grid, .stats { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 760px) {
      header { grid-template-columns: 1fr; }
      .grid, .stats { grid-template-columns: 1fr; }
      .soc-grid { grid-template-columns: 1fr; }
      /* Inline 4-col metric strip inside cards → 2-col */
      .stats[style*="repeat(4"] { grid-template-columns: repeat(2, 1fr) !important; }
      .bar { grid-template-columns: 80px 1fr 36px; font-size: 11px; }
      h1 { font-size: clamp(28px, 9vw, 54px); }
    }
    @media (max-width: 420px) {
      .stats[style*="repeat(4"] { grid-template-columns: repeat(2, 1fr) !important; }
      .bar { grid-template-columns: 70px 1fr 32px; font-size: 10px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <div class="eyebrow">System Home</div>
        <h1>Gateway Dashboard</h1>
        <p>Select what you want to do. This page is an overview and launcher; each feature opens in its own focused workspace.</p>
      </div>
      <div class="row">
        <span id="userPill" class="secondary" style="padding:10px 12px;border:2px solid rgba(255,178,77,.42);border-radius:7px">Loading...</span>
        <button id="logoutBtn" class="secondary">Logout</button>
      </div>
    </header>
    <section class="stats">
      <div class="stat" id="statModels" data-href="/models-manager"><div class="inner"><div class="label">Models</div><div id="modelsValue" class="value">--</div><div class="stat-arrow">View all →</div></div></div>
      <div class="stat" data-href="/dashboard/security"><div class="inner"><div class="label">Controls</div><div id="controlsValue" class="value">--</div><div class="stat-arrow">View all →</div></div></div>
      <div class="stat" data-href="/control-plane"><div class="inner"><div class="label">Rules</div><div id="rulesValue" class="value">--</div><div class="stat-arrow">View all →</div></div></div>
      <div class="stat" data-href="/logs"><div class="inner"><div class="label">Logs</div><div id="logsValue" class="value">--</div><div class="stat-arrow">View all →</div></div></div>
      <div class="stat" data-href="/dashboard/soc"><div class="inner"><div class="label">Threat Events</div><div id="eventsValue" class="value">--</div><div class="stat-arrow">View SOC →</div></div></div>
    </section>
    <section class="soc-grid">
      <article class="card"><div class="inner">
        <div class="label">SOC Command</div>
        <h2>Live Threat Posture</h2>
        <div class="stats" style="grid-template-columns:repeat(4,1fr);margin:12px 0">
          <div class="metric"><span class="muted">Allowed</span><strong id="socAllowed">--</strong></div>
          <div class="metric"><span class="muted">Challenged</span><strong id="socChallenged">--</strong></div>
          <div class="metric"><span class="muted">Blocked</span><strong id="socBlocked">--</strong></div>
          <div class="metric"><span class="muted">Alerts</span><strong id="socAlerts">--</strong></div>
        </div>
        <div id="socBars" class="mini-bars"></div>
      </div></article>
      <article class="card"><div class="inner">
        <div class="label">Threat Feed</div>
        <h2>Active Alerts</h2>
        <div id="socAlertList" class="meta">Loading SOC alerts...</div>
      </div></article>
    </section>
    <section class="feed-section">
      <div class="feed-head">
        <h2>Live System Logs</h2>
        <span class="live-dot" id="liveDot"></span>
        <span class="feed-status" id="liveStatus">Connecting…</span>
        <a href="/logs" style="margin-left:auto;font-size:12px;padding:5px 10px" class="secondary">Full log →</a>
      </div>
      <div id="liveFeed" class="feed-list"><div class="feed-empty">No log entries yet.</div></div>
    </section>
    <section id="welcomePanel" class="note warn" style="margin-bottom:14px;display:none"></section>
    <section id="options" class="grid"></section>
    <section id="status" class="note">Loading gateway options...</section>
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
        if (detail.title) return `${detail.title}${detail.explanation ? `: ${detail.explanation}` : ""}`;
        if (detail.message) return detail.message;
      }
      if (typeof detail === "string" && detail.trim()) return detail;
      if (status === 401 || status === 403) return "Your session expired. Please log in again.";
      if (status >= 500) return "Gateway services are temporarily unavailable.";
      return "Unable to load dashboard data right now.";
    }
    async function request(path) {
      const res = await fetch(path, { headers: authHeaders() });
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) {
        sessionStorage.removeItem("zta_token");
        location.href = "/login?next=/dashboard";
        throw new Error(parseApiError(data, res.status));
      }
      return data;
    }
    async function softRequest(path) {
      const res = await fetch(path, { headers: authHeaders() });
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(parseApiError(data, res.status));
      return data;
    }
    function isAdmin(user) {
      return Boolean(user?.is_admin);
    }
    function renderWelcome(data) {
      const panel = $("welcomePanel");
      const params = new URLSearchParams(location.search);
      const isFirstVisit = params.get("welcome") === "1";
      const readyModelCount = Number(data.runtime?.ready_models || 0);
      const canChatNow = readyModelCount > 0;
      const lines = [
        canChatNow
          ? "Open Gateway Chat to start protected inference with a runtime-ready model."
          : "No model is runtime-ready yet. You can review dashboards while an admin finishes model setup.",
        "Use Model Compare or Security Tests to inspect protection behavior with existing telemetry.",
        isAdmin(data.user)
          ? "Admin tools are available below for model onboarding and policy operations."
          : "Admin tools stay hidden for standard accounts."
      ];
      panel.style.display = "block";
      panel.innerHTML = `
        <strong>${isFirstVisit ? "Account Ready" : "Gateway Status"}</strong>
        <div style="margin-top:6px;color:var(--soft)">Runtime-ready models: <b style="color:var(--text)">${readyModelCount}</b></div>
        <ol class="next-steps">${lines.map((line) => `<li>${line}</li>`).join("")}</ol>
      `;
      if (isFirstVisit) {
        params.delete("welcome");
        history.replaceState({}, document.title, `${location.pathname}${params.toString() ? `?${params.toString()}` : ""}`);
      }
    }
    function openOption(item) {
      location.href = item.href;
    }
    function render(data) {
      $("userPill").textContent = `${data.user.username || "user"} · ${data.user.is_admin ? "admin" : "user"}`;
      $("userPill").classList.toggle("admin", Boolean(data.user.is_admin));
      $("modelsValue").textContent = data.overview.active_models;
      $("controlsValue").textContent = data.overview.enabled_controls;
      $("rulesValue").textContent = data.overview.enabled_detection_rules;
      $("logsValue").textContent = data.overview.request_logs;
      $("eventsValue").textContent = data.overview.attack_sequence_events;
      $("options").innerHTML = data.options.map((item) => `
        <article class="card ${item.requires_admin && !data.user.is_admin ? "locked" : ""}">
          <div class="inner">
            <div class="label">${item.category}</div>
            <h2>${item.title}${item.requires_admin ? ' <span class="badge" style="margin-left:6px">Admin Only</span>' : ''}</h2>
            <p>${item.description}</p>
            <div class="meta">${item.summary}</div>
            <div class="actions"><button data-id="${item.id}">Open ${item.title}</button></div>
          </div>
        </article>
      `).join("");
      document.querySelectorAll("[data-id]").forEach((button) => {
        button.addEventListener("click", () => {
          const item = data.options.find((candidate) => candidate.id === button.dataset.id);
          if (item) openOption(item);
        });
      });
      const hiddenAdmin = Number(data.overview?.admin_hidden_options || 0);
      $("status").className = "note";
      $("status").textContent = hiddenAdmin > 0
        ? `Ready. ${hiddenAdmin} admin-only workspace${hiddenAdmin === 1 ? "" : "s"} hidden for this account.`
        : "Ready.";
      renderWelcome(data);

      // Make stat cards clickable — adjust Models href based on role
      if (!isAdmin(data.user)) {
        const statModels = $("statModels");
        if (statModels) statModels.dataset.href = "/my-models";
      }
      document.querySelectorAll(".stat[data-href]").forEach((el) => {
        el.addEventListener("click", () => { location.href = el.dataset.href; });
      });
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
        const cells = (heatmap.cells || []).slice(0, 6);
        const max = Math.max(1, ...cells.map((c) => c.count || 0));
        $("socBars").innerHTML = cells.map((cell) => `<div class="bar"><span>${cell.attack_stage}</span><div class="track"><div class="fill" style="width:${Math.max(4, ((cell.count || 0) / max) * 100)}%"></div></div><b>${cell.count}</b></div>`).join("") || `<div class="muted">No attack timeline yet.</div>`;
        $("socAlertList").innerHTML = (alerts.alerts || []).slice(0, 4).map((alert) => `<div class="badge ${alert.severity === "high" ? "block" : "challenge"}" style="display:block;margin:7px 0">${alert.type}: ${alert.message}</div>`).join("") || "No active alerts.";
      } catch (err) {
        $("socAlertList").innerHTML = `<div class="note bad">SOC feeds are unavailable for this account or no telemetry is present yet.</div>`;
      }
    }
    // ── Live log feed ──────────────────────────────────────────────────────
    let liveLogIds = new Set();
    function fmtTime(iso) {
      if (!iso) return "—";
      const d = new Date(iso);
      const now = Date.now();
      const diff = Math.floor((now - d.getTime()) / 1000);
      const rel = diff < 60 ? `${diff}s ago`
                : diff < 3600 ? `${Math.floor(diff/60)}m ago`
                : diff < 86400 ? `${Math.floor(diff/3600)}h ago`
                : `${Math.floor(diff/86400)}d ago`;
      const abs = d.toLocaleString([], { month:"short", day:"numeric", hour:"2-digit", minute:"2-digit", second:"2-digit" });
      return `<span title="${abs}">${rel}</span>`;
    }
    function escHtml(s) {
      return String(s || "—").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
    }
    function riskLabel(score) {
      if (score == null) return "—";
      const pct = Math.round(score * 100);
      const color = pct >= 75 ? "var(--red)" : pct >= 50 ? "var(--amber)" : "var(--green)";
      return `<span style="color:${color}">${pct}%</span>`;
    }
    async function loadLiveLogs() {
      try {
        const data = await softRequest(`${api}/monitoring/logs?limit=25`);
        const logs = (data.logs || []);
        const dot = $("liveDot");
        const status = $("liveStatus");
        if (dot) dot.classList.remove("stale");
        if (status) status.textContent = `${logs.length} entries · updated ${new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"})}`;
        if (!logs.length) {
          $("liveFeed").innerHTML = '<div class="feed-empty">No log entries yet. Send a chat message to generate logs.</div>';
          return;
        }
        const newEntries = logs.filter((l) => !liveLogIds.has(l.id));
        newEntries.forEach((l) => liveLogIds.add(l.id));
        const dec = (d) => {
          if (d === "block") return "block";
          if (d === "challenge") return "challenge";
          return "allow";
        };
        $("liveFeed").innerHTML = logs.map((l, i) => {
          const d = dec(l.decision);
          const isNew = newEntries.includes(l);
          return `<div class="feed-entry" style="${isNew && i === 0 ? "border-color:rgba(255,178,77,.35);" : ""}">
            <span class="feed-dot ${d}"></span>
            <span class="feed-time">${fmtTime(l.timestamp)}</span>
            <span class="feed-who">${escHtml(l.username)} · ${escHtml(l.model_name)}</span>
            <span class="feed-dec ${d}">${d.toUpperCase()}</span>
            <span class="feed-risk">${riskLabel(l.prompt_risk_score)}</span>
          </div>`;
        }).join("");
      } catch {
        const dot = $("liveDot");
        const status = $("liveStatus");
        if (dot) dot.classList.add("stale");
        if (status) status.textContent = "Feed unavailable";
      }
    }

    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      location.href = "/login";
    });
    async function loadRuntimeOverview(navData) {
      try {
        const readiness = await request(`${api}/models/runtime-readiness`);
        const ready = (readiness || []).filter((item) => item.runtime_ready !== false).length;
        navData.runtime = { ready_models: ready };
      } catch {
        navData.runtime = { ready_models: 0 };
      }
      const totalAdmin = Number(navData.overview?.admin_option_count || 0);
      navData.overview.admin_hidden_options = isAdmin(navData.user) ? 0 : totalAdmin;
      return navData;
    }
    request(`${api}/navigation/options`)
      .then((data) => loadRuntimeOverview(data))
      .then((data) => { render(data); loadSoc(); loadLiveLogs(); })
      .catch((err) => {
        $("status").className = "note bad";
        $("status").textContent = "We couldn't load your dashboard right now. Please refresh and try again.";
      });

    // Poll live logs every 5 seconds
    setInterval(loadLiveLogs, 5000);
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
