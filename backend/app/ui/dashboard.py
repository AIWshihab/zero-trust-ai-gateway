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
    .card { min-height: 230px; display: flex; flex-direction: column; }
    .card h2 { margin: 0 0 8px; color: var(--amber); text-transform: uppercase; letter-spacing: .08em; font-size: 16px; }
    .card p { margin: 0; color: var(--soft); font-size: 13px; }
    .card .meta { margin-top: 12px; color: var(--muted); font-size: 12px; line-height: 1.45; min-height: 48px; }
    .card .actions { margin-top: auto; padding-top: 16px; }
    .locked { opacity: .58; }
    .admin { color: var(--green); }
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
    @media (max-width: 760px) { header, .grid, .stats { grid-template-columns: 1fr; } }
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
      <div class="stat"><div class="inner"><div class="label">Models</div><div id="modelsValue" class="value">--</div></div></div>
      <div class="stat"><div class="inner"><div class="label">Controls</div><div id="controlsValue" class="value">--</div></div></div>
      <div class="stat"><div class="inner"><div class="label">Rules</div><div id="rulesValue" class="value">--</div></div></div>
      <div class="stat"><div class="inner"><div class="label">Logs</div><div id="logsValue" class="value">--</div></div></div>
      <div class="stat"><div class="inner"><div class="label">Threat Events</div><div id="eventsValue" class="value">--</div></div></div>
    </section>
    <section id="options" class="grid"></section>
    <pre id="status">Loading gateway options...</pre>
  </main>
  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    const $ = (id) => document.getElementById(id);
    if (!token) location.href = "/login?next=/dashboard";
    const authHeaders = () => ({ Authorization: `Bearer ${token}` });
    async function request(path) {
      const res = await fetch(path, { headers: authHeaders() });
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) {
        sessionStorage.removeItem("zta_token");
        location.href = "/login?next=/dashboard";
        throw new Error("Session expired");
      }
      return data;
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
            <h2>${item.title}</h2>
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
      $("status").textContent = "Ready.";
    }
    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      location.href = "/login";
    });
    request(`${api}/navigation/options`).then(render).catch((err) => { $("status").textContent = String(err.message || err); });
  </script>
</body>
</html>
"""
