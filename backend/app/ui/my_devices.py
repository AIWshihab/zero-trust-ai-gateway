from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS

MY_DEVICES_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>My Devices — Zero Trust AI Gateway</title>
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
    body { margin: 0; }
    .shell { padding: 20px clamp(12px,3vw,32px) 40px; max-width: 1100px; }
    .page-eyebrow { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 5px; }
    .page-eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    h1 { font-size: clamp(22px,4vw,36px); font-weight: 700; color: var(--text); margin-bottom: 6px; }
    .page-sub { font-size: 14px; color: var(--muted); margin-bottom: 20px; }
    .section-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 24px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
    .section-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .top-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 20px; }
    .btn { border: 1px solid var(--b2); border-radius: 7px; padding: 8px 14px; background: var(--bg-2); color: var(--text); cursor: pointer; font-size: 13px; font-weight: 600; font: inherit; transition: border-color .18s, background .18s; }
    .btn:hover { border-color: var(--cyan); background: var(--bg-3); }
    .btn.danger { border-color: rgba(255,77,109,.3); color: #ffb3c1; background: rgba(255,77,109,.08); }
    .btn.danger:hover { background: rgba(255,77,109,.14); }
    .last-updated { font-size: 11px; color: var(--muted); }

    .this-device { border: 1px solid rgba(0,212,255,.25); border-radius: 8px; padding: 20px; background: var(--cyan-d); margin-bottom: 8px; position: relative; overflow: hidden; }
    .this-device-head { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
    .this-device-title { font-size: 16px; font-weight: 700; color: var(--text); }
    .badge-current { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(0,212,255,.4); color: var(--cyan); background: rgba(0,212,255,.08); font-weight: 700; }
    .pulse-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 8px var(--cyan); animation: pulse 1.8s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.75)} }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
    .info-cell { display: flex; flex-direction: column; gap: 3px; }
    .info-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
    .info-value { font-size: 13px; font-weight: 600; color: var(--text); word-break: break-all; }
    .info-value.ip { font-family: var(--mono); font-size: 13px; color: var(--cyan); }
    .info-value.ua { font-size: 11px; color: var(--muted); font-family: var(--mono); }
    .trust-wrap { margin-top: 14px; }
    .trust-label-row { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); margin-bottom: 5px; }
    .trust-track { height: 5px; border-radius: 99px; background: var(--bg-3); overflow: hidden; }
    .trust-fill { height: 100%; border-radius: 99px; transition: width .6s cubic-bezier(.2,.8,.2,1); }
    .device-warning { margin-top: 12px; padding: 10px 12px; border: 1px solid rgba(245,166,35,.25); border-radius: 7px; background: rgba(245,166,35,.06); color: var(--amber); font-size: 12px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 8px; }
    .card { border: 1px solid var(--border); border-radius: 8px; padding: 14px; background: var(--bg-1); transition: border-color .2s; }
    .card:hover { border-color: rgba(0,212,255,.2); }
    .card.is-current { border-color: rgba(0,212,255,.25); background: var(--cyan-d); }
    .card-head { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
    .device-name { font-weight: 700; font-size: 14px; color: var(--text); }
    .badge { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; padding: 3px 8px; border-radius: 999px; border: 1px solid var(--b2); background: var(--bg-2); color: var(--muted); white-space: nowrap; font-weight: 700; }
    .badge.trusted   { border-color: rgba(34,211,160,.35); color: var(--green); }
    .badge.new       { border-color: rgba(245,166,35,.35); color: var(--amber); }
    .badge.suspicious{ border-color: rgba(255,77,109,.4);  color: var(--red); }
    .badge.revoked   { border-color: rgba(255,77,109,.4);  color: var(--red); background: rgba(255,77,109,.08); }
    .badge.low       { border-color: rgba(34,211,160,.3);  color: var(--green); }
    .badge.medium    { border-color: rgba(245,166,35,.3);  color: var(--amber); }
    .badge.high, .badge.critical { border-color: rgba(255,77,109,.3); color: var(--red); }
    .meta-row { font-size: 12px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; border: 1px solid var(--b2); border-radius: 8px; margin-bottom: 8px; background: var(--bg-1); }
    table { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 520px; }
    th { padding: 10px 12px; text-align: left; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); background: var(--bg-2); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; white-space: nowrap; }
    td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; word-break: break-word; color: var(--text); }
    tr:last-child td { border-bottom: none; }
    tr.current-row td { background: var(--cyan-d); }
    .sev { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 5px; flex-shrink: 0; }
    .sev.info     { background: var(--green); }
    .sev.warning  { background: var(--amber); }
    .sev.high, .sev.critical { background: var(--red); animation: pulse 1.2s ease-in-out infinite; }
    .time-full { color: var(--muted); font-size: 11px; }
    .time-rel  { color: var(--text); font-weight: 600; }
    .empty-state { padding: 28px 20px; text-align: center; color: var(--muted); font-size: 13px; }
    .revoked-msg { color: var(--red); font-size: 12px; margin-top: 8px; }
    @media (max-width: 540px) { .cards { grid-template-columns: 1fr; } .info-grid { grid-template-columns: 1fr 1fr; } }
  </style>
</head>
<body>
<main class="shell">
  <div class="page-eyebrow">Device & Session Security</div>
  <h1>My Devices</h1>
  <p class="page-sub">Your registered devices, active sessions, and security events — all real data, updated live.</p>
  <div class="top-row">
    <button class="btn" id="refreshBtn">Refresh</button>
    <span class="last-updated" id="lastUpdated"></span>
  </div>

  <div class="section-title">This Device</div>
  <div id="thisDeviceCard"><div class="empty-state">Detecting your device…</div></div>

  <div class="section-title">All Registered Devices</div>
  <div class="cards" id="deviceCards"><div class="empty-state">Loading…</div></div>

  <div class="section-title">Sessions</div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>ID</th><th>Started</th><th>Last Active</th><th>Expires</th><th>Device</th><th>Status</th><th></th></tr></thead>
      <tbody id="sessionBody"><tr><td colspan="7" class="empty-state">Loading…</td></tr></tbody>
    </table>
  </div>

  <div class="section-title">Security Events</div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>When</th><th>Event</th><th>Severity</th><th>Browser · OS</th><th>Details</th></tr></thead>
      <tbody id="eventBody"><tr><td colspan="5" class="empty-state">Loading…</td></tr></tbody>
    </table>
  </div>
</main>
<script>
  const api = "/api/v1";
  const token = sessionStorage.getItem("zta_token");
  if (!token) location.href = "/login?next=/my-devices";
  const hdrs = () => ({ Authorization: `Bearer ${token}`, "Content-Type": "application/json" });
  const $ = id => document.getElementById(id);

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  }

  function fmtFull(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString([], {
        year: "numeric", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit", second: "2-digit"
      });
    } catch { return iso; }
  }

  function fmtRel(iso) {
    if (!iso) return "—";
    try {
      const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
      if (diff < 5)   return "just now";
      if (diff < 60)  return `${diff}s ago`;
      if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
      return `${Math.floor(diff/86400)}d ago`;
    } catch { return iso; }
  }

  function timeCell(iso) {
    if (!iso) return "—";
    return `<span class="time-rel" title="${esc(fmtFull(iso))}">${esc(fmtRel(iso))}</span><br><small class="time-full">${esc(fmtFull(iso))}</small>`;
  }

  function trustBar(score) {
    const pct = Math.min(100, Math.max(0, score || 0));
    const color = pct >= 80 ? "linear-gradient(90deg,#22d3a0,#00d4ff)"
                : pct >= 55 ? "linear-gradient(90deg,#00d4ff,#6fb0ff)"
                : pct >= 30 ? "linear-gradient(90deg,#f5a623,#ff7c4d)"
                :              "linear-gradient(90deg,#ff4d6d,#ff7c8a)";
    return `<div class="trust-wrap">
      <div class="trust-label-row"><span>Trust Score</span><span>${pct}/100</span></div>
      <div class="trust-track"><div class="trust-fill" style="width:${pct}%;background:${color}"></div></div>
    </div>`;
  }

  function renderThisDevice(info) {
    if (!info) {
      $("thisDeviceCard").innerHTML = '<div class="empty-state">Could not detect current device.</div>';
      return;
    }
    const d = info.device;
    $("thisDeviceCard").innerHTML = `
      <div class="this-device">
        <div class="this-device-head">
          <div class="this-device-title">${esc(d ? (d.device_name || `${info.browser} on ${info.os}`) : `${info.browser} on ${info.os}`)}</div>
          <span class="badge-current"><span class="pulse-dot"></span> Active Now</span>
        </div>
        <div class="info-grid">
          <div class="info-cell"><span class="info-label">IP Address</span><span class="info-value ip">${esc(info.ip)}</span></div>
          <div class="info-cell"><span class="info-label">Browser</span><span class="info-value">${esc(info.browser)}</span></div>
          <div class="info-cell"><span class="info-label">Operating System</span><span class="info-value">${esc(info.os)}</span></div>
          ${d ? `<div class="info-cell"><span class="info-label">Trust Score</span><span class="info-value">${d.trust_score}/100 &nbsp;<span class="badge ${d.risk_level}" style="font-size:10px">${d.risk_level}</span></span></div>` : ""}
          ${d ? `<div class="info-cell"><span class="info-label">Status</span><span class="badge ${d.status}">${d.status}</span></div>` : ""}
          ${d ? `<div class="info-cell"><span class="info-label">Logins</span><span class="info-value">${d.login_count} total</span></div>` : ""}
          ${d ? `<div class="info-cell"><span class="info-label">First Seen</span><span class="info-value">${esc(fmtFull(d.first_seen))}</span></div>` : ""}
          ${d ? `<div class="info-cell"><span class="info-label">Last Seen</span><span class="info-value">${esc(fmtRel(d.last_seen))}</span></div>` : ""}
          <div class="info-cell" style="grid-column:1/-1"><span class="info-label">User Agent</span><span class="info-value ua">${esc(info.user_agent || "—")}</span></div>
        </div>
        ${d ? trustBar(d.trust_score) : ""}
        ${!d ? `<div class="device-warning">This device has not been registered yet. Log out and back in to register it.</div>` : ""}
      </div>`;
  }

  function renderDevices(devices, currentId) {
    if (!devices.length) {
      $("deviceCards").innerHTML = '<div class="empty-state">No devices registered yet.</div>';
      return;
    }
    $("deviceCards").innerHTML = devices.map(d => `
      <div class="card${d.is_current ? " is-current" : ""}">
        <div class="card-head">
          <div class="device-name">${esc(d.device_name || `${d.browser} on ${d.os}`)}</div>
          <div style="display:flex;gap:5px;flex-wrap:wrap">
            ${d.is_current ? '<span class="badge" style="border-color:rgba(0,212,255,.4);color:var(--cyan)">Current</span>' : ""}
            <span class="badge ${esc(d.status)}">${esc(d.status)}</span>
          </div>
        </div>
        <div class="meta-row">
          <span>${esc(d.browser || "—")}</span>
          <span>${esc(d.os || "—")}</span>
          <span>${d.login_count} logins</span>
          ${d.failed_attempts > 0 ? `<span style="color:var(--red)">${d.failed_attempts} failed</span>` : ""}
        </div>
        <div class="meta-row"><span>First: ${esc(fmtFull(d.first_seen))}</span></div>
        <div class="meta-row"><span>Last: ${esc(fmtRel(d.last_seen))}</span></div>
        ${trustBar(d.trust_score)}
        <div style="display:flex;gap:6px;margin-top:10px;align-items:center;flex-wrap:wrap">
          <span class="badge ${esc(d.risk_level)}">${esc(d.risk_level)} risk</span>
        </div>
        ${d.is_revoked ? '<div class="revoked-msg">Revoked — contact admin</div>' : ""}
      </div>
    `).join("");
  }

  function renderSessions(sessions) {
    const tbody = $("sessionBody");
    if (!sessions.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No sessions found.</td></tr>';
      return;
    }
    tbody.innerHTML = sessions.map(s => `
      <tr class="${s.is_current ? "current-row" : ""}">
        <td>#${s.id}${s.is_current ? ' <span class="badge" style="border-color:rgba(0,212,255,.4);color:var(--cyan);font-size:10px">Current</span>' : ""}</td>
        <td>${timeCell(s.created_at)}</td>
        <td>${timeCell(s.last_active_at)}</td>
        <td style="color:${s.expires_at && new Date(s.expires_at) < new Date() ? "var(--red)" : "var(--muted)"}">${s.expires_at ? esc(fmtFull(s.expires_at)) : "Never"}</td>
        <td style="color:var(--muted)">${s.device_id ? `Device #${s.device_id}` : "—"}</td>
        <td><span class="badge ${s.is_active ? "trusted" : "revoked"}">${s.is_active ? "Active" : "Revoked"}</span></td>
        <td>${s.is_active && !s.is_current ? `<button class="btn danger" onclick="revokeSession(${s.id})">Revoke</button>` : ""}</td>
      </tr>
    `).join("");
  }

  function renderEvents(events) {
    const tbody = $("eventBody");
    if (!events.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No security events yet.</td></tr>';
      return;
    }
    tbody.innerHTML = events.map(e => `
      <tr>
        <td>${timeCell(e.timestamp)}</td>
        <td><span class="sev ${esc(e.severity)}"></span>${esc(e.event_type.replace(/_/g, " "))}</td>
        <td><span class="badge ${esc(e.severity)}">${esc(e.severity)}</span></td>
        <td style="color:var(--muted)">${esc([e.browser, e.os].filter(Boolean).join(" · ") || "—")}</td>
        <td style="color:var(--muted);font-size:11px">${esc(e.explanation || "—")}</td>
      </tr>
    `).join("");
  }

  async function revokeSession(id) {
    if (!confirm("Revoke this session? It will be signed out immediately.")) return;
    try {
      const res = await fetch(`${api}/devices/sessions/${id}/revoke`, { method: "POST", headers: hdrs() });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed");
      await loadAll();
    } catch (e) { alert(e.message); }
  }

  async function loadAll() {
    try {
      const [infoRes, devRes, sesRes, evtRes] = await Promise.all([
        fetch(`${api}/devices/me/current-info`, { headers: hdrs() }),
        fetch(`${api}/devices/me`, { headers: hdrs() }),
        fetch(`${api}/devices/me/sessions`, { headers: hdrs() }),
        fetch(`${api}/devices/me/events`, { headers: hdrs() }),
      ]);

      if (infoRes.ok)  renderThisDevice(await infoRes.json());
      if (devRes.ok)   renderDevices(await devRes.json());
      if (sesRes.ok)   renderSessions(await sesRes.json());
      if (evtRes.ok)   renderEvents(await evtRes.json());

      $("lastUpdated").textContent = "Updated " + new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"});
    } catch (e) {
      $("thisDeviceCard").innerHTML = `<div class="empty-state">Error: ${esc(e.message)}</div>`;
    }
  }

  $("refreshBtn").addEventListener("click", loadAll);
  loadAll();
  setInterval(loadAll, 30000);
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
