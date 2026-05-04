from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


SOC_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SOC Dashboard</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; --muted:#9ca8bd; --good:#34d399; --warn:#fbbf24; --bad:#fb7185; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; color: #f8fbff; background: #050505; }
    .shell { padding: 18px; display: grid; gap: 14px; }
    .top { display:flex; gap:10px; flex-wrap:wrap; align-items:center; justify-content:space-between; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    a,button { border:1px solid rgba(255,255,255,.15); border-radius:999px; padding:9px 12px; color:#f8fbff; background:rgba(255,255,255,.06); text-decoration:none; cursor:pointer; }
    .grid { display:grid; grid-template-columns: repeat(2, minmax(280px, 1fr)); gap: 14px; }
    .summary { display:grid; grid-template-columns: repeat(3, minmax(140px,1fr)); gap:10px; }
    .kpi { border:1px solid rgba(255,255,255,.12); border-radius:14px; padding:10px; background:rgba(255,255,255,.04); }
    .kpi b { display:block; font-size:22px; margin-top:4px; }
    .card { border:1px solid rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.05); padding:12px; min-height:220px; }
    .title { font-size:13px; color:#93c5fd; text-transform:uppercase; letter-spacing:.06em; margin-bottom:8px; }
    .muted { color: var(--muted); font-size: 12px; }
    .list { display:grid; gap:8px; max-height:300px; overflow:auto; }
    .item { border:1px solid rgba(255,255,255,.11); border-radius:12px; padding:10px; background:rgba(0,0,0,.26); transition: transform .2s ease, opacity .2s ease; }
    .item:hover { transform: translateY(-2px); }
    .badge { border:1px solid rgba(255,255,255,.16); border-radius:999px; padding:4px 7px; font-size:11px; }
    .high { color: var(--bad); border-color: rgba(251,113,133,.6); background: rgba(251,113,133,.14); animation: pulse 1.8s infinite; }
    .medium { color: var(--warn); border-color: rgba(251,191,36,.55); background: rgba(251,191,36,.1); }
    .low { color: #93c5fd; border-color: rgba(147,197,253,.45); background: rgba(147,197,253,.1); }
    .live { display:inline-flex; align-items:center; gap:6px; font-size:12px; color:#86efac; }
    .live-dot { width:8px; height:8px; border-radius:50%; background:#22c55e; animation: pulse 1.4s infinite; }
    .skeleton { border-radius:12px; background: linear-gradient(90deg, rgba(255,255,255,.04), rgba(255,255,255,.1), rgba(255,255,255,.04)); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
    .skeleton.row { height: 44px; margin-bottom: 8px; }
    .state { border:1px dashed rgba(255,255,255,.18); border-radius:12px; padding:12px; color:var(--muted); text-align:center; }
    .fade { animation: fade .22s ease; }
    .heat { display:grid; grid-template-columns: repeat(6, minmax(90px,1fr)); gap:8px; }
    .heat-cell { border-radius:12px; padding:10px; border:1px solid rgba(255,255,255,.12); }
    .table { width:100%; border-collapse: collapse; font-size:12px; }
    .table th,.table td { text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,.08); vertical-align: top; }
    canvas { width:100%; height:200px; background:rgba(0,0,0,.18); border-radius:12px; border:1px solid rgba(255,255,255,.08); }
    @keyframes pulse { 0%,100%{ box-shadow:0 0 0 rgba(251,113,133,0);} 50%{ box-shadow:0 0 22px rgba(251,113,133,.25);} }
    @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
    @keyframes fade { from { opacity:.5; } to { opacity:1; } }
    @media (max-width: 980px) { .grid { grid-template-columns: 1fr; } .heat{ grid-template-columns: repeat(2, minmax(120px,1fr)); } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="top">
      <div>
        <div class="title">Live AI Security Operations</div>
        <h1 style="margin:0">SOC Dashboard</h1>
      </div>
      <div class="row">
        <span class="live"><span class="live-dot"></span>Live</span>
        <a href="/dashboard">Dashboard</a>
        <a href="/control-plane">Control Plane</a>
        <button id="refreshBtn">Refresh</button>
      </div>
    </section>

    <section class="grid">
      <article class="card" style="min-height:120px">
        <div class="title">Threat Summary</div>
        <div class="summary">
          <div class="kpi"><span class="muted">Total attacks</span><b id="kpiAttacks">--</b></div>
          <div class="kpi"><span class="muted">Blocked</span><b id="kpiBlocked">--</b></div>
          <div class="kpi"><span class="muted">High risk</span><b id="kpiHighRisk">--</b></div>
        </div>
      </article>
      <article class="card" style="min-height:120px">
        <div class="title">System Health</div>
        <div class="summary">
          <div class="kpi"><span class="muted">Last self-test</span><b id="kpiTestStatus">--</b></div>
          <div class="kpi"><span class="muted">Passed</span><b id="kpiTestPassed">--</b></div>
          <div class="kpi"><span class="muted">Failed</span><b id="kpiTestFailed">--</b></div>
        </div>
      </article>
      <article class="card">
        <div class="title">Attack Timeline</div>
        <canvas id="timelineCanvas" width="1200" height="400"></canvas>
      </article>
      <article class="card">
        <div class="title">Threat Heatmap</div>
        <div id="heatmap" class="heat muted"></div>
      </article>
      <article class="card">
        <div class="title">User Anomalies</div>
        <div style="overflow:auto;max-height:300px">
          <table class="table"><thead><tr><th>User</th><th>Trust</th><th>Flags</th></tr></thead><tbody id="anomalyRows"></tbody></table>
        </div>
      </article>
      <article class="card">
        <div class="title">Real-time Alerts</div>
        <div id="alerts" class="list muted"></div>
      </article>
    </section>
  </main>
  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/soc";
    const headers = () => ({ Authorization: `Bearer ${token}` });
    async function get(path) {
      const res = await fetch(path, { headers: headers() });
      const text = await res.text();
      let data; try { data = text ? JSON.parse(text) : {}; } catch { data = {}; }
      if (!res.ok) throw new Error((data.detail && data.detail.message) || data.detail || `Request failed (${res.status})`);
      return data;
    }
    let lastHash = "";
    const orderWeight = (severity) => {
      const s = String(severity || "").toLowerCase();
      if (s === "critical" || s === "high") return 0;
      if (s === "warning" || s === "medium") return 1;
      return 2;
    };
    function sevClass(severity) {
      const s = String(severity || "").toLowerCase();
      if (s === "critical" || s === "high") return "high";
      if (s === "warning" || s === "medium") return "medium";
      return "low";
    }
    function drawTimeline(events) {
      const canvas = document.getElementById("timelineCanvas");
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const points = (events || []).slice(0, 60).reverse();
      if (!points.length) return;
      const values = points.map((e) => Number(e.sequence_severity || 0));
      const w = canvas.width, h = canvas.height, pad = 40;
      ctx.strokeStyle = "rgba(147,197,253,.92)";
      ctx.lineWidth = 4;
      ctx.beginPath();
      values.forEach((v, i) => {
        const x = pad + (i / Math.max(1, values.length - 1)) * (w - (pad * 2));
        const y = h - pad - (Math.max(0, Math.min(1, v)) * (h - (pad * 2)));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }
    function setLoading() {
      document.getElementById("alerts").innerHTML = `<div class="skeleton row"></div><div class="skeleton row"></div><div class="skeleton row"></div>`;
      document.getElementById("heatmap").innerHTML = `<div class="skeleton row"></div><div class="skeleton row"></div>`;
      document.getElementById("anomalyRows").innerHTML = `<tr><td colspan="3"><div class="skeleton row"></div></td></tr>`;
    }
    function animatedSet(id, next) {
      const el = document.getElementById(id);
      if (!el) return;
      const prev = Number(el.textContent || 0);
      const target = Number(next || 0);
      if (Number.isNaN(prev) || Number.isNaN(target) || prev === target) {
        el.textContent = String(next);
        return;
      }
      const start = performance.now();
      const dur = 220;
      const tick = (t) => {
        const p = Math.min(1, (t - start) / dur);
        el.textContent = String(Math.round(prev + ((target - prev) * p)));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
    async function load() {
      const [timeline, heatmap, anomalies, alerts] = await Promise.all([
        get(`${api}/monitoring/soc/attack-timeline?limit=120`),
        get(`${api}/monitoring/soc/threat-heatmap`),
        get(`${api}/monitoring/soc/user-anomalies`),
        get(`${api}/monitoring/soc/alerts`)
      ]);
      const currentHash = JSON.stringify({ timeline, heatmap, anomalies, alerts });
      if (currentHash === lastHash) return;
      lastHash = currentHash;
      const events = timeline.events || [];
      const highRisk = events.filter((e) => Number(e.sequence_severity || 0) >= 0.7).length;
      animatedSet("kpiAttacks", events.length);
      animatedSet("kpiBlocked", events.filter((e) => String(e.decision || "").toLowerCase() === "block").length);
      animatedSet("kpiHighRisk", highRisk);
      drawTimeline(events);
      const max = Math.max(1, ...((heatmap.cells || []).map((c) => Number(c.count || 0))));
      document.getElementById("heatmap").innerHTML = (heatmap.cells || []).slice(0, 24).map((c) => {
        const ratio = Number(c.count || 0) / max;
        const alpha = (0.18 + (ratio * 0.7)).toFixed(2);
        return `<div class="heat-cell fade" style="background:rgba(251,113,133,${alpha})"><div class="muted">${c.attack_stage}</div><strong>${c.count}</strong><div class="muted">model ${c.model_id ?? "-"}</div></div>`;
      }).join("") || `<div class="state">No threats detected · System secure</div>`;
      document.getElementById("anomalyRows").innerHTML = (anomalies.anomalies || []).map((a) => `<tr class="fade"><td>${a.username}</td><td>${Number(a.trust_score || 0).toFixed(2)}</td><td>${(a.anomaly_flags || []).join(", ")}</td></tr>`).join("") || `<tr><td colspan="3" class="muted">No anomalies</td></tr>`;
      const sortedAlerts = (alerts.alerts || []).slice(0, 60).sort((a,b) => orderWeight(a.severity) - orderWeight(b.severity));
      document.getElementById("alerts").innerHTML = sortedAlerts.map((a) => `<div class="item fade"><div class="row"><span class="badge ${sevClass(a.severity)}">${a.severity || "info"}</span><b>${a.type || "alert"}</b></div><div class="muted" style="margin-top:6px">${a.message || ""}</div><div class="muted" style="margin-top:6px">${a.timestamp || ""}</div></div>`).join("") || `<div class="state">No threats detected · System secure</div>`;
    }
    async function refreshSelfTestHealth() {
      try {
        const data = await get(`${api}/testing/run-soc-tests`);
        const failed = Number(data.failed || 0);
        document.getElementById("kpiTestStatus").textContent = failed > 0 ? "Failing" : "Passing";
        document.getElementById("kpiTestPassed").textContent = String(data.passed ?? 0);
        document.getElementById("kpiTestFailed").textContent = String(data.failed ?? 0);
      } catch {
        document.getElementById("kpiTestStatus").textContent = "Unavailable";
        document.getElementById("kpiTestPassed").textContent = "--";
        document.getElementById("kpiTestFailed").textContent = "--";
      }
    }
    let timer = null;
    function showError(message) {
      document.getElementById("alerts").innerHTML = `<div class="state">${message}<div style="margin-top:8px"><button id="retryBtn">Retry</button></div></div>`;
      document.getElementById("heatmap").innerHTML = `<div class="state">${message}</div>`;
      const retry = document.getElementById("retryBtn");
      if (retry) retry.onclick = () => load().catch((e) => showError(e.message));
    }
    function boot() {
      setLoading();
      load().catch((e) => showError(e.message));
      refreshSelfTestHealth();
      timer = setInterval(() => load().catch(() => {}), 4000);
    }
    document.getElementById("refreshBtn").addEventListener("click", () => load().catch((e) => showError(e.message)));
    window.addEventListener("beforeunload", () => { if (timer) clearInterval(timer); });
    boot();
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
