DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #090806;
      --panel: rgba(20, 18, 16, .88);
      --panel-strong: rgba(32, 27, 22, .98);
      --line: rgba(255, 178, 77, .34);
      --text: #fff7ea;
      --muted: #d3b99a;
      --green: #73e28b;
      --cyan: #8ce9ff;
      --amber: #ff9f1c;
      --red: #ff4d3d;
      --blue: #6fb0ff;
      --ink: #080604;
      --court: #f16a21;
      --cream: #fff1d5;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 17% 12%, rgba(255, 159, 28, .26), transparent 27%),
        radial-gradient(circle at 86% 4%, rgba(255, 77, 61, .16), transparent 28%),
        linear-gradient(120deg, rgba(255, 255, 255, .035) 0 1px, transparent 1px 72px),
        linear-gradient(150deg, #090806 0%, #15100b 46%, #2b1207 70%, #090806 100%);
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
        radial-gradient(circle, rgba(255,255,255,.18) 1px, transparent 1.5px);
      background-size: 120px 68px, 120px 68px, 9px 9px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), rgba(0,0,0,.12));
    }
    body::after {
      content: "";
      position: fixed;
      inset: -20% -8%;
      pointer-events: none;
      background:
        repeating-linear-gradient(112deg, transparent 0 26px, rgba(255,255,255,.08) 27px 29px, transparent 30px 58px),
        linear-gradient(90deg, transparent, rgba(255,159,28,.09), transparent);
      opacity: .58;
      transform: skewY(-5deg);
      animation: courtRush 12s linear infinite;
    }
    .shell { position: relative; z-index: 1; padding: 22px clamp(14px, 3vw, 34px) 34px; }
    header {
      display: grid;
      grid-template-columns: minmax(280px, 1fr) auto;
      gap: 18px;
      align-items: center;
      margin-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: clamp(30px, 4.4vw, 58px);
      letter-spacing: 0;
      line-height: .94;
      text-transform: uppercase;
      text-shadow: 4px 4px 0 var(--ink), 7px 7px 0 rgba(255,159,28,.34);
    }
    .subtitle { color: var(--cream); margin-top: 12px; max-width: 860px; line-height: 1.55; font-weight: 680; }
    .top-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 2px solid var(--ink);
      border-radius: 999px;
      padding: 8px 11px;
      color: var(--cream);
      background: linear-gradient(135deg, rgba(255,159,28,.16), rgba(0,0,0,.42));
      backdrop-filter: blur(18px);
      font-size: 13px;
      font-weight: 750;
      box-shadow: 3px 3px 0 rgba(0,0,0,.65);
    }
    .dot { width: 8px; height: 8px; border-radius: 999px; background: var(--green); box-shadow: 0 0 18px var(--green); }
    .dot.bad { background: var(--red); box-shadow: 0 0 18px var(--red); }
    .grid { display: grid; grid-template-columns: 380px minmax(420px, 1fr) 360px; gap: 16px; align-items: start; }
    .panel {
      position: relative;
      border: 2px solid var(--ink);
      border-radius: 6px;
      background: var(--panel);
      box-shadow: 7px 7px 0 rgba(0,0,0,.72), 0 24px 80px rgba(0,0,0,.36);
      backdrop-filter: blur(22px);
      overflow: hidden;
      transform: skewX(-.7deg);
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
    .panel-inner { position: relative; z-index: 1; padding: 16px; transform: skewX(.7deg); }
    .panel-title { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }
    h2 { font-size: 14px; text-transform: uppercase; letter-spacing: .08em; color: var(--amber); margin: 0; text-shadow: 2px 2px 0 #000; }
    .stack { display: grid; gap: 12px; }
    label { display: grid; gap: 6px; font-size: 12px; font-weight: 760; color: #cbd5e1; }
    input, textarea, select {
      width: 100%;
      border: 2px solid rgba(255, 178, 77, .34);
      background: rgba(8, 6, 4, .8);
      color: var(--text);
      border-radius: 7px;
      padding: 11px 12px;
      font: inherit;
      outline: none;
      transition: border-color .2s, box-shadow .2s, transform .2s;
    }
    textarea { min-height: 145px; resize: vertical; line-height: 1.48; }
    input:focus, textarea:focus, select:focus { border-color: var(--amber); box-shadow: 0 0 0 3px rgba(255, 159, 28, .17); }
    a.button-link, button {
      border: 2px solid var(--ink);
      border-radius: 7px;
      padding: 11px 13px;
      color: #150905;
      background: linear-gradient(135deg, #ffd164, #ff7a1a 52%, #f0441f);
      font-weight: 850;
      cursor: pointer;
      text-decoration: none;
      transition: transform .18s ease, filter .18s ease, opacity .18s ease;
      box-shadow: 4px 4px 0 rgba(0,0,0,.75);
    }
    a.button-link:hover, button:hover { transform: translate(-1px, -2px); filter: brightness(1.08); }
    button:disabled { opacity: .55; cursor: wait; transform: none; }
    a.secondary, button.secondary { background: rgba(255,241,213,.08); color: var(--cream); border: 2px solid rgba(255,178,77,.42); }
    button.warning { background: linear-gradient(135deg, #fff1d5, #ffb13b 44%, #ff7a1a); color: #1f1300; }
    .row { display: flex; gap: 9px; flex-wrap: wrap; align-items: center; }
    .metric-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; }
    .metric {
      border: 2px solid rgba(255, 178, 77, .28);
      border-radius: 8px;
      padding: 11px;
      background: linear-gradient(135deg, rgba(255,159,28,.11), rgba(255,255,255,.035));
      min-height: 78px;
      box-shadow: 4px 4px 0 rgba(0,0,0,.42);
    }
    .metric .value { font-size: 24px; font-weight: 860; margin-top: 8px; }
    .metric .label { color: var(--muted); font-size: 12px; }
    .orbital {
      height: 190px;
      position: relative;
      display: grid;
      place-items: center;
      margin: 4px 0 12px;
    }
    .ring {
      position: absolute;
      border: 2px solid rgba(255,241,213,.36);
      border-radius: 50%;
      animation: spin 12s linear infinite;
    }
    .ring.one { width: 178px; height: 178px; }
    .ring.two { width: 132px; height: 132px; animation-duration: 9s; animation-direction: reverse; border-color: rgba(255,159,28,.38); }
    .ring.three { width: 86px; height: 86px; animation-duration: 6s; border-color: rgba(255,77,61,.38); }
    .core {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background:
        radial-gradient(circle at 35% 30%, #fff8e8 0 18%, transparent 19%),
        repeating-linear-gradient(45deg, transparent 0 12px, rgba(0,0,0,.82) 13px 15px, transparent 16px 28px),
        radial-gradient(circle, #fff1d5 0 36%, #ff9f1c 37% 66%, #111 67% 70%, rgba(255,159,28,.22) 71%);
      box-shadow: 0 0 44px rgba(255,159,28,.78), 5px 5px 0 rgba(0,0,0,.75);
      animation: pulse 2.4s ease-in-out infinite;
    }
    .satellite { position: absolute; width: 10px; height: 10px; border-radius: 50%; background: var(--amber); top: -6px; left: 50%; box-shadow: 0 0 16px var(--amber); }
    .log, pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 130px;
      max-height: 340px;
      overflow: auto;
      border: 2px solid rgba(255, 178, 77, .24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(8, 6, 4, .82);
      color: var(--cream);
      font-size: 12px;
      line-height: 1.45;
    }
    .output { min-height: 260px; font-size: 14px; color: #f8fafc; }
    .control-list { display: grid; gap: 8px; }
    .control {
      display: grid;
      grid-template-columns: 64px 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 10px;
      border: 2px solid rgba(255, 178, 77, .18);
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(255,159,28,.08), rgba(255,255,255,.025));
    }
    .control strong { font-size: 13px; }
    .control span { color: var(--muted); font-size: 12px; }
    .badge { padding: 5px 7px; border-radius: 999px; font-size: 11px; font-weight: 850; border: 1px solid rgba(255,255,255,.18); background: rgba(0,0,0,.42); }
    .strong { color: var(--green); }
    .moderate { color: var(--amber); }
    .partial, .planned { color: var(--blue); }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes pulse { 0%, 100% { transform: scale(.95); } 50% { transform: scale(1.06); } }
    @keyframes courtRush { to { transform: skewY(-5deg) translateX(-120px); } }
    @media (max-width: 1180px) { .grid { grid-template-columns: 360px 1fr; } .right { grid-column: 1 / -1; } }
    @media (max-width: 820px) { header, .grid { grid-template-columns: 1fr; } .top-actions { justify-content: flex-start; } .metric-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>Zero Trust AI Gateway</h1>
        <div class="subtitle">Match-point AI defense: every prompt gets received, screened, and blocked before it can spike through your models.</div>
      </div>
      <div class="top-actions">
        <a class="button-link secondary" href="/control-plane">Manage Control Plane</a>
        <span id="ztaStatus" class="pill"><span class="dot bad"></span>Login required</span>
        <span id="maturityPill" class="pill">Maturity: --</span>
      </div>
    </header>
    <div class="grid">
      <section class="panel">
        <div class="panel-inner stack">
          <div class="panel-title"><h2>Identity</h2><span class="pill">User trust</span></div>
          <label>Username <input id="username" autocomplete="username" placeholder="kira" /></label>
          <label>Password <input id="password" type="password" autocomplete="current-password" placeholder="Password" /></label>
          <div class="row">
            <button id="loginBtn">Login</button>
            <button id="profileBtn" class="secondary">Refresh Profile</button>
            <button id="modelsBtn" class="secondary">Models</button>
          </div>
          <label>Access token <textarea id="token" spellcheck="false" placeholder="Paste or generate a bearer token"></textarea></label>
          <div class="metric-grid">
            <div class="metric"><div class="label">Trust</div><div id="trustScore" class="value">--</div></div>
            <div class="metric"><div class="label">Penalty</div><div id="penaltyState" class="value">--</div></div>
            <div class="metric"><div class="label">Rate</div><div id="rateState" class="value">--</div></div>
          </div>
          <pre id="profile">No profile loaded.</pre>
        </div>
      </section>
      <section class="panel">
        <div class="panel-inner stack">
          <div class="panel-title"><h2>Protected AI Window</h2><span class="pill"><span class="dot"></span>Policy enforced</span></div>
          <div class="orbital" aria-hidden="true">
            <div class="ring one"><span class="satellite"></span></div>
            <div class="ring two"><span class="satellite"></span></div>
            <div class="ring three"><span class="satellite"></span></div>
            <div class="core"></div>
          </div>
          <label>Model <select id="modelSelect"><option>Login and load models</option></select></label>
          <label>Prompt <textarea id="prompt">Explain zero-trust controls for AI gateways in simple terms.</textarea></label>
          <div class="row">
            <button id="detectBtn" class="warning">Pre-screen</button>
            <button id="simulateBtn" class="secondary">Simulate Policy</button>
            <button id="inferBtn">Send Safely</button>
          </div>
          <pre id="output" class="output">Model responses appear here after passing the gateway.</pre>
        </div>
      </section>
      <section class="panel right">
        <div class="panel-inner stack">
          <div class="panel-title"><h2>Control Plane</h2><button id="controlBtn" class="secondary">Refresh</button></div>
          <div id="controls" class="control-list"></div>
          <h2>Security Decision</h2>
          <pre id="decision">No decision yet.</pre>
        </div>
      </section>
    </div>
  </div>
  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    const authHeaders = () => ({ Authorization: `Bearer ${$("token").value.trim()}` });
    const show = (id, value) => { $(id).textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2); };
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    function setProfile(data) {
      $("trustScore").textContent = data.trust?.trust_score ?? "--";
      $("penaltyState").textContent = data.rate?.penalty_active ? `${data.rate.cooldown_remaining_seconds}s` : "Clear";
      $("rateState").textContent = data.rate ? `${data.rate.requests_in_window}/${data.rate.limit}` : "--";
      show("profile", data);
    }
    async function login() {
      const form = new URLSearchParams();
      form.set("username", $("username").value);
      form.set("password", $("password").value);
      const data = await request(`${api}/auth/token`, { method: "POST", body: form });
      $("token").value = data.access_token;
      await Promise.all([loadProfile(), loadModels(), loadControlPlane()]);
    }
    async function loadProfile() { setProfile(await request(`${api}/auth/me/profile`, { headers: authHeaders() })); }
    async function loadModels() {
      const models = await request(`${api}/models/`, { headers: authHeaders() });
      $("modelSelect").innerHTML = models.map((m) => `<option value="${m.id}">${m.name} - ${m.scan_status || "unscanned"} - ${m.model_type}</option>`).join("");
    }
    async function loadControlPlane() {
      const data = await request(`${api}/security/control-plane`, { headers: authHeaders() });
      $("maturityPill").textContent = `Maturity: ${Math.round(data.gateway_maturity * 100)}%`;
      $("controls").innerHTML = data.controls.map((c) => `<div class="control"><strong>${c.id}</strong><div><strong>${c.name}</strong><br><span>${c.controls.join(", ")}</span></div><span class="badge ${c.coverage}">${c.coverage}</span></div>`).join("");
    }
    async function detect() {
      const body = { model_id: Number($("modelSelect").value), prompt: $("prompt").value };
      show("decision", await request(`${api}/detect/`, { method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) }));
      await loadProfile();
    }
    async function simulate() {
      const body = { model_id: Number($("modelSelect").value), prompt: $("prompt").value };
      show("decision", await request(`${api}/security/policy/simulate`, { method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) }));
    }
    async function infer() {
      const body = { model_id: Number($("modelSelect").value), prompt: $("prompt").value, parameters: { temperature: 0.2, max_tokens: 512 } };
      const data = await request(`${api}/usage/infer`, { method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) });
      show("output", data.output || data.reason || "No output returned.");
      show("decision", data);
      await loadProfile();
    }
    async function zta() {
      try {
        const data = await request(`${api}/monitoring/zta/status`, { headers: authHeaders() });
        $("ztaStatus").innerHTML = `<span class="dot ${data.enabled ? "" : "bad"}"></span>${data.enabled ? "ZTA active" : "ZTA disabled"}`;
      } catch { $("ztaStatus").innerHTML = `<span class="dot bad"></span>Login required`; }
    }
    for (const [id, fn] of [["loginBtn", login], ["profileBtn", loadProfile], ["modelsBtn", loadModels], ["detectBtn", detect], ["simulateBtn", simulate], ["inferBtn", infer], ["controlBtn", loadControlPlane]]) {
      $(id).addEventListener("click", async () => {
        $(id).disabled = true;
        try { await fn(); await zta(); } catch (err) { show("decision", String(err.message || err)); }
        finally { $(id).disabled = false; }
      });
    }
    zta();
  </script>
</body>
</html>
"""
