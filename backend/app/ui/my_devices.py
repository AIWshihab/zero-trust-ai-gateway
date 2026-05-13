from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS

MY_DEVICES_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>My Devices — Zero Trust AI Gateway</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; }
    body { margin: 0; }
    .shell { padding: 20px clamp(12px, 3vw, 32px) 40px; max-width: 1100px; }
    .eyebrow { font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: .1em; color: #93c5fd; margin-bottom: 6px; }
    h1 { margin: 0 0 6px; font-size: clamp(26px, 5vw, 44px); }
    p.sub { margin: 0 0 20px; font-size: 14px; color: #9ca8bd; }
    h2 { margin: 28px 0 12px; font-size: 13px; color: #93c5fd; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,.07); padding-bottom: 6px; }

    /* This Device Hero */
    .this-device { border: 1px solid rgba(34,211,238,.35); border-radius: 18px; padding: 20px; background: rgba(34,211,238,.05); margin-bottom: 8px; position: relative; overflow: hidden; }
    .this-device::before { content:""; position:absolute; inset:0; background: radial-gradient(circle at 80% 50%, rgba(34,211,238,.06), transparent 60%); pointer-events:none; }
    .this-device-head { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
    .this-device-title { font-size: 17px; font-weight: 800; }
    .badge-current { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(34,211,238,.45); color: #67e8f9; background: rgba(34,211,238,.1); }
    .pulse-dot { width: 7px; height: 7px; border-radius: 50%; background: #22d3ee; box-shadow: 0 0 8px #22d3ee; animation: pulse 1.8s ease-in-out infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.75)} }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
    .info-cell { display: flex; flex-direction: column; gap: 3px; }
    .info-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #9ca8bd; }
    .info-value { font-size: 13px; font-weight: 600; color: #f1f5f9; word-break: break-all; }
    .info-value.ip { font-family: monospace; font-size: 14px; color: #67e8f9; }
    .info-value.ua { font-size: 11px; color: #9ca8bd; font-family: monospace; }

    /* Trust bar */
    .trust-wrap { margin-top: 16px; }
    .trust-label-row { display: flex; justify-content: space-between; font-size: 12px; color: #9ca8bd; margin-bottom: 5px; }
    .trust-track { height: 6px; border-radius: 99px; background: rgba(255,255,255,.1); overflow: hidden; }
    .trust-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #22d3ee, #a855f7); transition: width .6s cubic-bezier(.2,.8,.2,1); }

    /* Device cards */
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 8px; }
    .card { border: 1px solid rgba(255,255,255,.1); border-radius: 14px; padding: 14px; background: rgba(255,255,255,.04); }
    .card.is-current { border-color: rgba(34,211,238,.3); background: rgba(34,211,238,.04); }
    .card-head { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
    .device-name { font-weight: 700; font-size: 14px; }
    .badge { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; padding: 3px 9px; border-radius: 999px; border: 1px solid rgba(255,255,255,.15); background: rgba(255,255,255,.06); white-space: nowrap; }
    .badge.trusted { border-color: rgba(52,211,153,.45); color: #6ee7b7; }
    .badge.new { border-color: rgba(251,191,36,.45); color: #fde68a; }
    .badge.suspicious { border-color: rgba(251,113,133,.5); color: #fda4af; }
    .badge.revoked { border-color: rgba(239,68,68,.5); color: #fca5a5; background: rgba(239,68,68,.08); }
    .badge.low { border-color: rgba(52,211,153,.35); color: #86efac; }
    .badge.medium { border-color: rgba(251,191,36,.35); color: #fde68a; }
    .badge.high { border-color: rgba(251,113,133,.4); color: #fda4af; }
    .badge.critical { border-color: rgba(239,68,68,.5); color: #fca5a5; }
    .meta-row { font-size: 12px; color: #9ca8bd; display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }

    /* Tables */
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; border: 1px solid rgba(255,255,255,.1); border-radius: 14px; margin-bottom: 8px; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 520px; }
    th { padding: 10px 12px; text-align: left; color: #9ca8bd; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,.1); background: rgba(255,255,255,.03); white-space: nowrap; }
    td { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,.06); vertical-align: middle; word-break: break-word; }
    tr:last-child td { border-bottom: none; }
    tr.current-row td { background: rgba(34,211,238,.04); }

    /* Severity dots */
    .sev { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; box-shadow: 0 0 6px currentColor; flex-shrink: 0; }
    .sev.info { color: #6ee7b7; background: currentColor; }
    .sev.warning { color: #fde68a; background: currentColor; }
    .sev.high { color: #fda4af; background: currentColor; }
    .sev.critical { color: #fca5a5; background: currentColor; animation: pulse 1.2s ease-in-out infinite; }

    .btn { border: 1px solid rgba(255,255,255,.15); border-radius: 999px; padding: 6px 14px; background: rgba(255,255,255,.06); color: #f8fbff; cursor: pointer; font-size: 12px; }
    .btn:hover { border-color: rgba(34,211,238,.5); }
    .btn.danger { border-color: rgba(251,113,133,.35); color: #fda4af; }
    .btn.danger:hover { background: rgba(251,113,133,.1); }
    .top-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 20px; }
    .empty-state { padding: 32px 20px; text-align: center; color: #9ca8bd; font-size: 13px; }
    .time-full { color: #9ca8bd; }
    .time-rel { color: #f1f5f9; font-weight: 600; }
    @media (max-width: 540px) { .cards { grid-template-columns: 1fr; } .info-grid { grid-template-columns: 1fr 1fr; } }
  </style>
</head>
<body>
<main class="shell">
  <div class="eyebrow">Device & Session Security</div>
  <h1>My Devices</h1>
  <p class="sub">Your registered devices, active sessions, and security events — all real data, updated live.</p>
  <div class="top-row">
    <button class="btn" id="refreshBtn">Refresh</button>
    <span id="lastUpdated" style="font-size:11px;color:#9ca8bd"></span>
  </div>

  <!-- This Device hero -->
  <h2>This Device</h2>
  <div id="thisDeviceCard"><div class="empty-state">Detecting your device…</div></div>

  <!-- All devices -->
  <h2>All Registered Devices</h2>
  <div class="cards" id="deviceCards"><div class="empty-state">Loading…</div></div>

  <!-- Sessions -->
  <h2>Sessions</h2>
  <div class="table-wrap">
    <table>
      <thead><tr><th>ID</th><th>Started</th><th>Last Active</th><th>Expires</th><th>Device</th><th>Status</th><th></th></tr></thead>
      <tbody id="sessionBody"><tr><td colspan="7" class="empty-state">Loading…</td></tr></tbody>
    </table>
  </div>

  <!-- Security events -->
  <h2>Security Events</h2>
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
    const color = pct >= 80 ? "linear-gradient(90deg,#22d3ee,#34d399)"
                : pct >= 55 ? "linear-gradient(90deg,#22d3ee,#a855f7)"
                : pct >= 30 ? "linear-gradient(90deg,#f59e0b,#fb923c)"
                :              "linear-gradient(90deg,#ef4444,#fb7185)";
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
          <div class="info-cell">
            <span class="info-label">IP Address</span>
            <span class="info-value ip">${esc(info.ip)}</span>
          </div>
          <div class="info-cell">
            <span class="info-label">Browser</span>
            <span class="info-value">${esc(info.browser)}</span>
          </div>
          <div class="info-cell">
            <span class="info-label">Operating System</span>
            <span class="info-value">${esc(info.os)}</span>
          </div>
          ${d ? `<div class="info-cell">
            <span class="info-label">Trust Score</span>
            <span class="info-value">${d.trust_score}/100 &nbsp;<span class="badge ${d.risk_level}" style="font-size:10px">${d.risk_level}</span></span>
          </div>` : ""}
          ${d ? `<div class="info-cell">
            <span class="info-label">Status</span>
            <span class="badge ${d.status}">${d.status}</span>
          </div>` : ""}
          ${d ? `<div class="info-cell">
            <span class="info-label">Logins</span>
            <span class="info-value">${d.login_count} total</span>
          </div>` : ""}
          ${d ? `<div class="info-cell">
            <span class="info-label">First Seen</span>
            <span class="info-value">${esc(fmtFull(d.first_seen))}</span>
          </div>` : ""}
          ${d ? `<div class="info-cell">
            <span class="info-label">Last Seen</span>
            <span class="info-value">${esc(fmtRel(d.last_seen))}</span>
          </div>` : ""}
          <div class="info-cell" style="grid-column:1/-1">
            <span class="info-label">User Agent</span>
            <span class="info-value ua">${esc(info.user_agent || "—")}</span>
          </div>
        </div>
        ${d ? trustBar(d.trust_score) : ""}
        ${!d ? `<div style="margin-top:14px;padding:10px 14px;border:1px solid rgba(251,191,36,.3);border-radius:10px;background:rgba(251,191,36,.06);color:#fde68a;font-size:12px">
          ⚠ This device has not been registered yet. Log out and back in to register it.
        </div>` : ""}
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
            ${d.is_current ? '<span class="badge" style="border-color:rgba(34,211,238,.45);color:#67e8f9">Current</span>' : ""}
            <span class="badge ${esc(d.status)}">${esc(d.status)}</span>
          </div>
        </div>
        <div class="meta-row">
          <span>🌐 ${esc(d.browser || "—")}</span>
          <span>💻 ${esc(d.os || "—")}</span>
          <span>🔑 ${d.login_count} logins</span>
          ${d.failed_attempts > 0 ? `<span style="color:#fda4af">⚠ ${d.failed_attempts} failed</span>` : ""}
        </div>
        <div class="meta-row">
          <span>First: ${esc(fmtFull(d.first_seen))}</span>
        </div>
        <div class="meta-row">
          <span>Last: ${esc(fmtRel(d.last_seen))}</span>
        </div>
        ${trustBar(d.trust_score)}
        <div style="display:flex;gap:6px;margin-top:10px;align-items:center;flex-wrap:wrap">
          <span class="badge ${esc(d.risk_level)}">${esc(d.risk_level)} risk</span>
        </div>
        ${d.is_revoked ? '<div style="color:#fca5a5;font-size:12px;margin-top:8px">⛔ Revoked — contact admin</div>' : ""}
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
        <td>#${s.id}${s.is_current ? ' <span class="badge" style="border-color:rgba(34,211,238,.45);color:#67e8f9;font-size:10px">Current</span>' : ""}</td>
        <td>${timeCell(s.created_at)}</td>
        <td>${timeCell(s.last_active_at)}</td>
        <td><span style="color:${s.expires_at && new Date(s.expires_at) < new Date() ? "#fda4af" : "#9ca8bd"}">${s.expires_at ? esc(fmtFull(s.expires_at)) : "Never"}</span></td>
        <td>${s.device_id ? `Device #${s.device_id}` : "—"}</td>
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
        <td style="color:#9ca8bd">${esc([e.browser, e.os].filter(Boolean).join(" · ") || "—")}</td>
        <td style="color:#9ca8bd;font-size:11px">${esc(e.explanation || "—")}</td>
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
