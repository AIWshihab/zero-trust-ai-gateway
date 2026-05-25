from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


SOC_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Security Observability — Zero Trust AI Gateway</title>
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
    .shell { padding: 20px; display: grid; gap: 16px; }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }
    .page-title { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
    .page-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .page-header h1 { font-size: 22px; font-weight: 700; color: var(--text); }
    .hdr-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .live-badge { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-1); }
    .live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); animation: pulse-dot 1.4s infinite; }
    a, button {
      border: 1px solid var(--b2);
      border-radius: 7px;
      padding: 8px 14px;
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
    .kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .kpi {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      background: var(--bg-1);
      transition: border-color .2s;
    }
    .kpi:hover { border-color: rgba(0,212,255,.2); }
    .kpi-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }
    .kpi-value { font-size: 24px; font-weight: 700; margin-top: 6px; color: var(--text); }
    .main-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
    .card {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 14px;
      transition: border-color .2s;
    }
    .card:hover { border-color: rgba(0,212,255,.18); }
    .card-title { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
    .card-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .event-list { display: grid; gap: 8px; max-height: 320px; overflow: auto; }
    .event-item {
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      background: var(--bg-2);
      transition: border-color .18s, transform .18s;
    }
    .event-item:hover { border-color: rgba(0,212,255,.2); transform: translateX(2px); }
    .badge { border: 1px solid var(--b2); border-radius: 999px; padding: 3px 8px; font-size: 11px; font-weight: 700; }
    .high   { color: var(--red);   border-color: rgba(255,77,109,.4);  background: rgba(255,77,109,.08);  animation: pulse-red 1.8s infinite; }
    .medium { color: var(--amber); border-color: rgba(245,166,35,.4);  background: rgba(245,166,35,.08); }
    .low    { color: var(--cyan);  border-color: rgba(0,212,255,.3);   background: var(--cyan-d); }
    .heat { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
    .heat-cell { border-radius: 8px; padding: 10px; border: 1px solid var(--border); }
    .heat-cell .label { font-size: 11px; color: var(--muted); }
    .heat-cell strong { display: block; font-size: 18px; font-weight: 700; margin: 4px 0; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); vertical-align: top; }
    th { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; }
    canvas { width: 100%; height: 200px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-2); }
    .skeleton { height: 44px; border-radius: 6px; background: linear-gradient(90deg, var(--bg-2), var(--bg-3), var(--bg-2)); background-size: 200% 100%; animation: shimmer 1.2s infinite; margin-bottom: 8px; }
    .state { border: 1px dashed var(--border); border-radius: 8px; padding: 14px; color: var(--muted); text-align: center; font-size: 13px; }
    .fade { animation: fadein .22s ease; }
    .item-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
    .item-meta { font-size: 11px; color: var(--muted); margin-top: 4px; }
    @keyframes pulse-dot { 0%,100%{ opacity:1; } 50%{ opacity:.4; } }
    @keyframes pulse-red { 0%,100%{ box-shadow:none; } 50%{ box-shadow:0 0 10px rgba(255,77,109,.3); } }
    @keyframes shimmer { 0%{ background-position:200% 0 } 100%{ background-position:-200% 0 } }
    @keyframes fadein { from{ opacity:.4 } to{ opacity:1 } }
    @media (max-width: 980px) { .main-grid { grid-template-columns: 1fr; } .heat { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } .heat { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 420px) { .kpi-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="page-header">
      <div>
        <div class="page-title">Security Observability for AI Inference</div>
        <h1>Security Monitor</h1>
      </div>
      <div class="hdr-row">
        <span class="live-badge" id="liveStatus"><span class="live-dot"></span>Live DB</span>
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/policy">Policy Engine</a>
        <button id="refreshBtn">Refresh</button>
      </div>
    </section>

    <section>
      <div class="kpi-grid" id="kpiStrip">
        <div class="kpi"><div class="kpi-label">Attack Events</div><div class="kpi-value" id="kpiAttacks">--</div></div>
        <div class="kpi"><div class="kpi-label">Blocked</div><div class="kpi-value" id="kpiBlocked">--</div></div>
        <div class="kpi"><div class="kpi-label">High Risk</div><div class="kpi-value" id="kpiHighRisk">--</div></div>
        <div class="kpi"><div class="kpi-label">Total Requests</div><div class="kpi-value" id="kpiTotal">--</div></div>
        <div class="kpi"><div class="kpi-label">Allowed</div><div class="kpi-value" id="kpiAllowed">--</div></div>
        <div class="kpi"><div class="kpi-label">Avg Prompt Risk</div><div class="kpi-value" id="kpiAvgRisk">--</div></div>
      </div>
    </section>

    <section class="main-grid">
      <article class="card">
        <div class="card-title">Decision Trace Timeline</div>
        <canvas id="timelineCanvas" width="1200" height="400"></canvas>
      </article>
      <article class="card">
        <div class="card-title">Cross-Model Abuse Indicators</div>
        <div id="heatmap" class="heat"></div>
      </article>
      <article class="card">
        <div class="card-title">User Trust Anomalies</div>
        <div style="overflow:auto">
          <table><thead><tr><th>User</th><th>Trust Score</th><th>Flags</th></tr></thead><tbody id="anomalyRows"></tbody></table>
        </div>
      </article>
      <article class="card">
        <div class="card-title">Live Alerts</div>
        <div id="alerts" class="event-list"></div>
      </article>
      <article class="card">
        <div class="card-title">Browser Extension Activity</div>
        <div id="extensionEvents" class="event-list"></div>
      </article>
    </section>
  </main>
  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/security-monitor";
    const headers = () => ({ Authorization: `Bearer ${token}` });

    async function get(path) {
      const res = await fetch(path, { headers: headers() });
      const text = await res.text();
      let data; try { data = text ? JSON.parse(text) : {}; } catch { data = {}; }
      if (!res.ok) throw new Error((data.detail && data.detail.message) || data.detail || `Request failed (${res.status})`);
      return data;
    }
    async function getExtensionEvents() {
      try { return await get(`${api}/devices/admin/events?limit=100`); }
      catch { return await get(`${api}/devices/me/events?limit=50`); }
    }

    let lastHash = "";
    const orderWeight = (s) => { const v = String(s||"").toLowerCase(); return v==="critical"||v==="high"?0:v==="warning"||v==="medium"?1:2; };
    function sevClass(s) { const v = String(s||"").toLowerCase(); return v==="critical"||v==="high"?"high":v==="warning"||v==="medium"?"medium":"low"; }

    function drawTimeline(events) {
      const canvas = document.getElementById("timelineCanvas");
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const points = (events || []).slice(0, 60).reverse();
      if (!points.length) {
        ctx.fillStyle = "rgba(124,132,153,.8)";
        ctx.font = "22px Inter, sans-serif";
        ctx.fillText("No attack sequence events yet", 40, 80);
        ctx.font = "15px Inter, sans-serif";
        ctx.fillText("Send chat or gateway requests to generate telemetry.", 40, 110);
        return;
      }
      const values = points.map((e) => Number(e.sequence_severity || 0));
      const w = canvas.width, h = canvas.height, pad = 40;
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, "rgba(0,212,255,.28)");
      grad.addColorStop(1, "rgba(0,212,255,0)");
      ctx.beginPath();
      values.forEach((v, i) => {
        const x = pad + (i / Math.max(1, values.length - 1)) * (w - pad * 2);
        const y = h - pad - (Math.max(0, Math.min(1, v)) * (h - pad * 2));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.lineTo(pad + (values.length-1)/(Math.max(1,values.length-1))*(w-pad*2), h-pad);
      ctx.lineTo(pad, h-pad);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.beginPath();
      values.forEach((v, i) => {
        const x = pad + (i / Math.max(1, values.length - 1)) * (w - pad * 2);
        const y = h - pad - (Math.max(0, Math.min(1, v)) * (h - pad * 2));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = "rgba(0,212,255,.85)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    function setLoading() {
      document.getElementById("alerts").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>`;
      document.getElementById("extensionEvents").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div>`;
      document.getElementById("heatmap").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div>`;
      document.getElementById("anomalyRows").innerHTML = `<tr><td colspan="3"><div class="skeleton"></div></td></tr>`;
    }
    function setStatus(text, mode = "live") {
      const el = document.getElementById("liveStatus");
      if (!el) return;
      if (mode === "error") {
        el.innerHTML = `<span style="color:var(--red);font-size:12px">${text}</span>`;
      } else {
        el.innerHTML = `<span class="live-dot"></span>${text}`;
      }
    }
    function showError(err) {
      const message = String(err?.message || err || "Monitoring data unavailable");
      setStatus("Live data unavailable", "error");
      document.getElementById("alerts").innerHTML = `<div class="state">Could not load live monitoring data: ${message}</div>`;
      document.getElementById("extensionEvents").innerHTML = `<div class="state">Could not load browser extension events.</div>`;
      document.getElementById("heatmap").innerHTML = `<div class="state">Live endpoint failed. Fix the endpoint or generate real telemetry.</div>`;
      document.getElementById("anomalyRows").innerHTML = `<tr><td colspan="3" style="color:var(--muted)">Unavailable: ${message}</td></tr>`;
    }
    function animatedSet(id, next) {
      const el = document.getElementById(id);
      if (!el) return;
      const prev = Number(el.textContent || 0);
      const target = Number(next || 0);
      if (Number.isNaN(prev) || Number.isNaN(target) || prev === target) { el.textContent = String(next); return; }
      const start = performance.now(), dur = 220;
      const tick = (t) => {
        const p = Math.min(1, (t - start) / dur);
        el.textContent = String(Math.round(prev + (target - prev) * p));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }

    async function load() {
      const [metrics, timeline, heatmap, anomalies, alerts, extensionEvents] = await Promise.all([
        get(`${api}/monitoring/metrics`),
        get(`${api}/monitoring/soc/attack-timeline?limit=120`),
        get(`${api}/monitoring/soc/threat-heatmap`),
        get(`${api}/monitoring/soc/user-anomalies`),
        get(`${api}/monitoring/soc/alerts`),
        getExtensionEvents()
      ]);

      const currentHash = JSON.stringify({ metrics, timeline, heatmap, anomalies, alerts, extensionEvents });
      if (currentHash === lastHash) return;
      lastHash = currentHash;

      const events = timeline.events || [];
      const highRisk = events.filter((e) => Number(e.sequence_severity || 0) >= 0.7).length;
      animatedSet("kpiAttacks", events.length);
      animatedSet("kpiBlocked", metrics.blocked_requests ?? events.filter((e) => String(e.decision || "").toLowerCase() === "block").length);
      animatedSet("kpiHighRisk", highRisk);
      animatedSet("kpiTotal", metrics.total_requests ?? 0);
      animatedSet("kpiAllowed", metrics.allowed_requests ?? 0);
      document.getElementById("kpiAvgRisk").textContent = `${Math.round(Number(metrics.avg_prompt_risk_score || 0) * 100)}%`;

      drawTimeline(events);

      const max = Math.max(1, ...((heatmap.cells || []).map((c) => Number(c.count || 0))));
      document.getElementById("heatmap").innerHTML = (heatmap.cells || []).slice(0, 12).map((c) => {
        const ratio = Number(c.count || 0) / max;
        const alpha = (0.12 + ratio * 0.55).toFixed(2);
        return `<div class="heat-cell fade" style="background:rgba(255,77,109,${alpha});border-color:rgba(255,77,109,.25)"><div class="label">${c.attack_stage}</div><strong>${c.count}</strong><div class="label">model ${c.model_id ?? "-"}</div></div>`;
      }).join("") || `<div class="state">No live threat events recorded yet.</div>`;

      document.getElementById("anomalyRows").innerHTML = (anomalies.anomalies || []).map((a) =>
        `<tr class="fade"><td>${a.username}</td><td>${Number(a.trust_score || 0).toFixed(2)}</td><td style="color:var(--muted)">${(a.anomaly_flags || []).join(", ")}</td></tr>`
      ).join("") || `<tr><td colspan="3" style="color:var(--muted);padding:12px">No anomalies</td></tr>`;

      const sorted = (alerts.alerts || []).slice(0, 60).sort((a, b) => orderWeight(a.severity) - orderWeight(b.severity));
      document.getElementById("alerts").innerHTML = sorted.map((a) =>
        `<div class="event-item fade"><div class="item-row"><span class="badge ${sevClass(a.severity)}">${a.severity || "info"}</span><b>${a.type || "alert"}</b></div><div class="item-meta">${a.message || ""}</div><div class="item-meta">${a.timestamp || ""}</div></div>`
      ).join("") || `<div class="state">No live alerts from current telemetry.</div>`;

      const extensionRows = (extensionEvents || []).filter((event) => event.source_module === "browser_extension").slice(0, 20);
      document.getElementById("extensionEvents").innerHTML = extensionRows.map((event) =>
        `<div class="event-item fade"><div class="item-row"><span class="badge ${sevClass(event.severity)}">${event.severity || "info"}</span><b>${event.event_type}</b></div><div class="item-meta">${event.explanation || ""}</div><div class="item-meta">device ${event.device_id || "-"} · ${event.timestamp || ""}</div></div>`
      ).join("") || `<div class="state">No browser extension events yet.</div>`;

      setStatus(`Live DB · updated ${new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit", second:"2-digit" })}`);
    }

    let timer = null;
    async function refreshNow() {
      document.getElementById("refreshBtn").disabled = true;
      try { await load(); }
      catch (err) { showError(err); }
      finally { document.getElementById("refreshBtn").disabled = false; }
    }
    function boot() {
      setLoading();
      refreshNow();
      timer = setInterval(refreshNow, 2500);
    }
    document.getElementById("refreshBtn").addEventListener("click", refreshNow);
    window.addEventListener("beforeunload", () => { if (timer) clearInterval(timer); });
    boot();
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
