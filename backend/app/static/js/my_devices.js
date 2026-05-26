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