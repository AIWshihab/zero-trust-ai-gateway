from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


CHAT_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Secure Chat — Zero Trust AI Gateway</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
  <style>
    :root {
      color-scheme: dark;
      --bg:    #08080a;
      --bg-1:  #0d0f14;
      --bg-2:  #111420;
      --bg-3:  #181b28;
      --border: rgba(255,255,255,.07);
      --b2:    rgba(255,255,255,.12);
      --cyan:  #00d4ff;
      --cyan-d: rgba(0,212,255,.09);
      --green: #22d3a0;
      --amber: #f5a623;
      --red:   #ff4d6d;
      --text:  #edf2ff;
      --muted: #7c8499;
      --muted2: #9aa0b4;
      --mono:  'JetBrains Mono', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { width: 100vw; height: 100vh; background: var(--bg); color: var(--text); overflow: hidden; }
    /* Prevent common.py CYBER_UI_JS from injecting duplicate sidebar — chat has its own .rail */

    /* ── App shell: rail + chat ── */
    .chat-app { height: 100vh; display: grid; grid-template-columns: 272px minmax(0,1fr); }

    /* ── Sidebar rail ── */
    .rail {
      border-right: 1px solid var(--border);
      background: var(--bg-1);
      display: grid;
      grid-template-rows: auto auto minmax(0,1fr) auto;
      overflow: hidden;
    }
    .rail-head {
      padding: 14px 14px 12px;
      border-bottom: 1px solid var(--border);
      display: grid;
      gap: 10px;
    }
    .brand-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .brand-name {
      font-size: 13px;
      font-weight: 700;
      color: var(--cyan);
      font-family: var(--mono);
      letter-spacing: .02em;
    }
    .brand-name span { color: var(--muted); font-weight: 400; }
    .new-btn {
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid var(--b2);
      background: var(--cyan);
      color: #000;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: background .15s;
    }
    .new-btn:hover { background: #00bde8; }
    .user-line { font-size: 12px; color: var(--muted); }
    .nav-links { display: flex; gap: 5px; overflow-x: auto; padding-bottom: 2px; scrollbar-width: none; }
    .nav-links a {
      white-space: nowrap; text-decoration: none;
      color: var(--muted); border: 1px solid var(--border);
      border-radius: 999px; padding: 5px 10px;
      background: transparent; font-size: 11px;
      transition: color .15s, border-color .15s;
    }
    .nav-links a:hover { color: var(--cyan); border-color: rgba(0,212,255,.28); }

    /* ── Model picker ── */
    .picker {
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      display: grid;
      gap: 8px;
    }
    .picker label { font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); display: grid; gap: 5px; }
    select {
      width: 100%; padding: 8px 10px; border-radius: 7px;
      border: 1px solid var(--b2); background: var(--bg-3);
      color: var(--text); font: inherit; font-size: 13px; outline: none;
    }
    select:focus { border-color: rgba(0,212,255,.42); }
    .runtime-box {
      border: 1px solid var(--b2); border-radius: 7px;
      padding: 9px 11px; background: var(--bg-3);
      display: grid; gap: 3px;
    }
    .runtime-box.ready  { border-color: rgba(34,211,160,.36); }
    .runtime-box.warn   { border-color: rgba(245,166,35,.36); }
    .runtime-box.bad    { border-color: rgba(255,77,109,.36); }
    .runtime-box b { font-size: 13px; color: var(--text); }
    .runtime-box small { font-size: 11px; color: var(--muted); line-height: 1.4; }

    /* ── Sessions list ── */
    .sessions { overflow: auto; padding: 8px; display: grid; gap: 4px; align-content: start; }
    .session {
      text-align: left; width: 100%; border-radius: 7px;
      border: 1px solid transparent; background: transparent;
      padding: 9px 11px; cursor: pointer; display: grid; gap: 3px;
      transition: background .15s, border-color .15s;
    }
    .session:hover { background: var(--bg-2); border-color: var(--border); }
    .session.active { background: var(--cyan-d); border-color: rgba(0,212,255,.28); }
    .session span { font-size: 13px; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .session small { font-size: 11px; color: var(--muted); }

    /* ── Rail footer ── */
    .rail-foot { padding: 10px 14px; border-top: 1px solid var(--border); display: grid; gap: 7px; }
    .danger-btn {
      width: 100%; padding: 9px; border-radius: 7px;
      border: 1px solid rgba(255,77,109,.3); background: rgba(255,77,109,.08);
      color: var(--red); font-size: 13px; font-weight: 600; cursor: pointer;
      transition: border-color .15s;
    }
    .danger-btn:hover { border-color: rgba(255,77,109,.55); }
    .ghost-btn {
      width: 100%; padding: 8px; border-radius: 7px;
      border: 1px solid var(--border); background: transparent;
      color: var(--muted); font-size: 12px; cursor: pointer;
      transition: color .15s, border-color .15s;
    }
    .ghost-btn:hover { color: var(--text); border-color: var(--b2); }

    /* ── Main chat pane ── */
    .chat { display: grid; grid-template-rows: auto minmax(0,1fr) auto; height: 100vh; overflow: hidden; }
    .topbar {
      padding: 12px 18px;
      border-bottom: 1px solid var(--border);
      display: grid;
      grid-template-columns: minmax(0,1fr) auto;
      gap: 12px;
      align-items: center;
      background: var(--bg-1);
    }
    .chat-title strong { font-size: 15px; font-weight: 700; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .chat-title small  { font-size: 12px; color: var(--muted); display: block; margin-top: 2px; }
    .top-pills { display: flex; gap: 7px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
    .pill {
      border: 1px solid var(--b2); border-radius: 999px;
      padding: 5px 10px; color: var(--muted); font-size: 11px; font-weight: 600; white-space: nowrap;
    }
    .pill.allow     { color: var(--green); border-color: rgba(34,211,160,.38); background: rgba(34,211,160,.08); }
    .pill.block     { color: var(--red);   border-color: rgba(255,77,109,.38);  background: rgba(255,77,109,.08); }
    .pill.challenge { color: var(--amber); border-color: rgba(245,166,35,.38);  background: rgba(245,166,35,.08); }
    .inspector-toggle {
      padding: 6px 12px; border-radius: 6px; border: 1px solid var(--b2);
      background: var(--bg-3); color: var(--muted2); font-size: 12px; cursor: pointer;
      transition: border-color .15s, color .15s;
    }
    .inspector-toggle:hover { border-color: rgba(0,212,255,.36); color: var(--cyan); }

    /* ── Messages ── */
    .messages { overflow: auto; padding: 24px 18px 16px; background: var(--bg); }
    .thread { width: min(860px, 100%); margin: 0 auto; display: grid; gap: 20px; }
    .empty {
      min-height: 55vh; display: grid; place-content: center;
      gap: 10px; text-align: center; color: var(--muted);
    }
    .empty strong {
      font-size: clamp(24px, 5vw, 42px); font-weight: 800;
      color: var(--text); letter-spacing: -.5px; display: block;
    }
    .empty span { font-size: 14px; color: var(--muted); max-width: 420px; display: block; margin: 0 auto; }
    .msg { display: grid; grid-template-columns: 34px minmax(0,1fr); gap: 12px; }
    .avatar {
      width: 30px; height: 30px; border-radius: 999px;
      display: grid; place-items: center;
      font-size: 11px; font-weight: 800;
      border: 1px solid var(--b2); background: var(--bg-2); color: var(--muted);
    }
    .msg.user   .avatar { background: rgba(0,212,255,.12); color: var(--cyan); border-color: rgba(0,212,255,.28); }
    .msg.system .avatar { background: rgba(255,77,109,.1); color: var(--red); border-color: rgba(255,77,109,.28); }
    .content {
      min-width: 0; line-height: 1.65; padding-top: 4px;
      white-space: pre-wrap; overflow-wrap: anywhere; font-size: 14px;
    }
    .assistant .content { white-space: normal; }
    .content p { margin: 0 0 10px; }
    .content p:last-child { margin-bottom: 0; }
    .content pre {
      overflow: auto; padding: 12px; border-radius: 8px;
      background: var(--bg-1); border: 1px solid var(--b2);
      font-family: var(--mono); font-size: 13px; white-space: pre;
    }
    .content code { background: var(--bg-2); border: 1px solid var(--border); border-radius: 4px; padding: 1px 5px; font-family: var(--mono); font-size: 13px; }
    .content pre code { background: transparent; border: 0; padding: 0; }
    .msg.warming .content { color: var(--amber); font-style: italic; }
    .cursor { display: inline-block; width: 2px; height: 14px; background: var(--cyan); border-radius: 1px; margin-left: 2px; vertical-align: middle; animation: blink .8s step-end infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

    /* ── Composer ── */
    .composer-wrap { padding: 12px 18px 16px; background: var(--bg-1); border-top: 1px solid var(--border); }
    .composer {
      width: min(860px, 100%); margin: 0 auto;
      display: grid; grid-template-columns: minmax(0,1fr) auto auto;
      gap: 8px; align-items: end;
      border: 1px solid var(--b2); border-radius: 10px;
      padding: 8px; background: var(--bg-2);
      transition: border-color .18s;
    }
    .composer:focus-within { border-color: rgba(0,212,255,.36); }
    textarea {
      min-height: 44px; max-height: 160px; resize: none;
      width: 100%; border: 0; background: transparent;
      color: var(--text); outline: none; padding: 9px;
      line-height: 1.5; font: inherit; font-size: 14px;
    }
    textarea::placeholder { color: var(--muted); }
    .stop-btn {
      padding: 9px 13px; border-radius: 7px;
      border: 1px solid rgba(255,77,109,.3); background: rgba(255,77,109,.08);
      color: var(--red); font-size: 13px; font-weight: 700; cursor: pointer;
    }
    .send-btn {
      padding: 9px 16px; border-radius: 7px;
      border: 0; background: var(--cyan); color: #000;
      font-size: 13px; font-weight: 700; cursor: pointer;
      transition: background .15s;
    }
    .send-btn:hover { background: #00bde8; }
    .send-btn:disabled { opacity: .5; cursor: wait; background: var(--cyan); }

    /* ── Inspector panel ── */
    .inspector {
      position: fixed; right: 12px; top: 60px; bottom: 80px;
      width: min(360px, calc(100vw - 24px)); z-index: 10;
      transform: translateX(calc(100% + 16px));
      transition: transform .22s ease;
      border: 1px solid var(--b2); border-radius: 10px;
      background: var(--bg-1);
      display: grid; grid-template-rows: auto minmax(0,1fr);
    }
    .inspector.open { transform: translateX(0); }
    .inspector-head {
      padding: 12px 14px; border-bottom: 1px solid var(--border);
      display: flex; justify-content: space-between; align-items: center; gap: 8px;
    }
    .inspector-head b { font-size: 13px; font-weight: 700; color: var(--text); }
    .inspector-close {
      padding: 4px 10px; border-radius: 6px; border: 1px solid var(--border);
      background: transparent; color: var(--muted); font-size: 12px; cursor: pointer;
    }
    .inspector-body { overflow: auto; padding: 12px; display: grid; gap: 10px; align-content: start; }
    .metrics-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 8px; }
    .metric-card {
      border: 1px solid var(--b2); border-radius: 8px;
      padding: 10px 12px; background: var(--bg-2);
    }
    .metric-label { font-size: 10px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
    .metric-val   { font-size: 20px; font-weight: 800; color: var(--text); margin-top: 4px; }
    .decision-box {
      border: 1px solid var(--b2); border-radius: 8px; padding: 12px; background: var(--bg-2);
    }
    .decision-box.ready  { border-color: rgba(34,211,160,.36); }
    .decision-box.warn   { border-color: rgba(245,166,35,.36); }
    .decision-box.bad    { border-color: rgba(255,77,109,.36); }
    .decision-box b { font-size: 14px; font-weight: 700; display: block; margin-bottom: 4px; }
    .decision-box small { font-size: 12px; color: var(--muted); line-height: 1.5; }
    .trace-box {
      border: 1px solid var(--border); border-radius: 8px;
      background: var(--bg); padding: 10px;
      white-space: pre-wrap; word-break: break-word;
      max-height: 260px; overflow: auto;
      color: var(--muted2); font-size: 11px;
      font-family: var(--mono); line-height: 1.5;
    }
    @media (max-width: 860px) {
      .chat-app { grid-template-columns: 1fr; height: auto; min-height: 100vh; }
      .rail { max-height: 44vh; border-right: 0; border-bottom: 1px solid var(--border); }
      .chat { height: 60vh; min-height: 600px; }
      .topbar { grid-template-columns: 1fr; }
      .top-pills { justify-content: flex-start; }
    }
  </style>
</head>
<body class="no-shell">
  <main class="chat-app">
    <!-- Rail (sidebar) -->
    <aside class="rail">
      <div class="rail-head">
        <div class="brand-row">
          <span class="brand-name">GT <span>// Chat</span></span>
          <button class="new-btn" id="newBtn">+ New</button>
        </div>
        <div class="user-line" id="userLine">Checking session...</div>
        <div class="nav-links" id="navLinks"></div>
      </div>
      <div class="picker">
        <label>Model
          <select id="modelSelect"><option>Loading models...</option></select>
        </label>
        <div id="runtimeBox" class="runtime-box warn">
          <b>Select a model</b>
          <small>Runtime readiness will appear here.</small>
        </div>
      </div>
      <div id="sessions" class="sessions"></div>
      <div class="rail-foot">
        <button class="danger-btn" id="deleteBtn">Delete Chat</button>
        <button class="ghost-btn" id="logoutBtn">Logout</button>
      </div>
    </aside>

    <!-- Main chat area -->
    <section class="chat">
      <header class="topbar">
        <div class="chat-title">
          <strong id="chatTitle">New chat</strong>
          <small id="modelLine">Choose a model and start a protected conversation.</small>
        </div>
        <div class="top-pills">
          <span id="ztaPill" class="pill">Zero Trust</span>
          <span id="decisionPill" class="pill">No decision</span>
          <button class="inspector-toggle" id="inspectorBtn">Inspector</button>
        </div>
      </header>
      <div id="messages" class="messages"><div class="thread"></div></div>
      <div class="composer-wrap">
        <div class="composer">
          <textarea id="prompt" placeholder="Message Gateway Chat — your prompt is screened before it reaches the model"></textarea>
          <button class="stop-btn" id="stopBtn" style="display:none">Stop</button>
          <button class="send-btn" id="sendBtn">Send</button>
        </div>
      </div>
    </section>
  </main>

  <!-- Inspector panel -->
  <aside id="inspector" class="inspector">
    <div class="inspector-head">
      <b>Zero Trust Inspector</b>
      <button class="inspector-close" id="closeInspector">Close</button>
    </div>
    <div class="inspector-body">
      <div class="metrics-grid">
        <div class="metric-card"><div class="metric-label">Prompt Risk</div><div class="metric-val" id="promptRisk">--</div></div>
        <div class="metric-card"><div class="metric-label">Security Score</div><div class="metric-val" id="securityScore">--</div></div>
        <div class="metric-card"><div class="metric-label">Trust</div><div class="metric-val" id="trustScore">--</div></div>
        <div class="metric-card"><div class="metric-label">Penalty</div><div class="metric-val" id="penaltyState">--</div></div>
      </div>
      <div id="decisionReason" class="decision-box">
        <b>Waiting</b>
        <small>Send a message to inspect the Zero Trust decision.</small>
      </div>
      <pre id="traceBox" class="trace-box">{}</pre>
    </div>
  </aside>

  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/chat";
    const authHeaders = () => ({ Authorization: `Bearer ${token}` });

    let currentUser = { is_admin: false };
    let sessions = [];
    let activeId = null;
    let models = [];
    let abortController = null;
    let streaming = false;

    const nav = [
      ["Dashboard", "/dashboard"],
      ["Models", "/dashboard/models"],
      ["Monitor", "/dashboard/security-monitor"],
      ["Policy", "/dashboard/policy"],
      ["Research", "/dashboard/research"],
    ];

    function esc(v) {
      return String(v ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
    }
    function markdown(v) {
      if (!v) return "";
      if (typeof marked === "undefined") return esc(v);
      try { return marked.parse(v); } catch { return esc(v); }
    }
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data = {};
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) {
        const detail = data.detail || data;
        throw new Error(typeof detail === "string" ? detail : (detail.explanation || detail.reason || detail.message || JSON.stringify(detail)));
      }
      return data;
    }
    function activeSession() { return sessions.find(s => String(s.id) === String(activeId)); }
    function selectedModel() {
      const session = activeSession();
      const id = $("modelSelect").value || session?.model_id;
      return models.find(m => String(m.id) === String(id));
    }
    function messageRows(session) {
      return (session?.messages || []).map(m => ({ role: m.role, content: m.content, gateway: m.gateway_trace, id: m.id }));
    }
    function decisionClass(decision) {
      const d = String(decision || "").toLowerCase();
      return d === "allow" ? "allow" : d === "block" ? "block" : d === "challenge" ? "challenge" : "";
    }
    function setDecision(data) {
      const d = String(data.decision || "unknown").toUpperCase();
      $("decisionPill").textContent = d;
      $("decisionPill").className = `pill ${decisionClass(d)}`;
      $("promptRisk").textContent = data.prompt_risk_score == null ? "--" : `${Math.round(data.prompt_risk_score * 100)}%`;
      $("securityScore").textContent = data.security_score == null ? "--" : `${Math.round(data.security_score * 100)}%`;
      const cls = d === "BLOCK" ? "bad" : d === "CHALLENGE" ? "warn" : "ready";
      $("decisionReason").className = `decision-box ${cls}`;
      $("decisionReason").innerHTML = `<b>${esc(d)}</b><small>${esc(data.explanation || data.reason || "Decision complete.")}</small>`;
      $("traceBox").textContent = JSON.stringify(data.decision_trace || data, null, 2);
    }
    function renderNav() {
      $("navLinks").innerHTML = nav.map(([label, href]) => `<a href="${href}">${esc(label)}</a>`).join("");
    }
    function renderRuntime() {
      const model = selectedModel();
      if (!model) {
        $("runtimeBox").className = "runtime-box warn";
        $("runtimeBox").innerHTML = `<b>No model selected</b><small>Choose a model to start chatting.</small>`;
        $("sendBtn").disabled = true;
        return;
      }
      const runtime = model.runtime || {};
      const ready = runtime.runtime_ready !== false;
      const canPrescreen = runtime.can_prescreen !== false;
      $("runtimeBox").className = `runtime-box ${ready ? "ready" : canPrescreen ? "warn" : "bad"}`;
      $("runtimeBox").innerHTML = `<b>${esc(runtime.label || (ready ? "Ready" : "Needs setup"))}</b><small>${esc(runtime.explanation || runtime.message || "Runtime status unknown.")}</small>`;
      $("modelLine").textContent = `${model.name} · ${model.model_type} · ${runtime.label || (ready ? "Ready" : "Needs setup")}`;
      $("sendBtn").disabled = !canPrescreen || streaming;
    }
    function renderSessions() {
      $("sessions").innerHTML = sessions.map(s => {
        const count = (s.messages || []).length;
        return `<button class="session ${String(s.id) === String(activeId) ? "active" : ""}" data-id="${s.id}"><span>${esc(s.title || "New chat")}</span><small>${count} message${count !== 1 ? "s" : ""}</small></button>`;
      }).join("");
      document.querySelectorAll(".session").forEach(btn => btn.onclick = () => { activeId = Number(btn.dataset.id); render(); });
    }
    function renderMessages(extraRows = null) {
      const session = activeSession();
      $("chatTitle").textContent = session?.title || "New chat";
      const rows = extraRows || messageRows(session);
      const thread = rows.length ? rows.map(m => {
        const role = m.role === "assistant" ? "assistant" : m.role === "user" ? "user" : "system";
        const who = role === "assistant" ? "AI" : role === "user" ? "You" : "ZT";
        const body = role === "assistant" && !m.warming ? markdown(m.content || "") : esc(m.content || "");
        const warmingClass = m.warming ? " warming" : "";
        return `<article class="msg ${role}${warmingClass}"><div class="avatar">${who}</div><div class="content">${body}${m.streaming ? '<span class="cursor"></span>' : ""}</div></article>`;
      }).join("") : `<div class="empty"><strong>Gateway Chat</strong><span>Ask normally. The gateway persists the conversation, screens the full context, and records every Zero Trust decision.</span></div>`;
      $("messages").innerHTML = `<div class="thread">${thread}</div>`;
      $("messages").scrollTop = $("messages").scrollHeight;
      renderRuntime();
    }
    function render(extraRows = null) { renderNav(); renderSessions(); renderMessages(extraRows); }

    async function loadProfile() {
      const data = await request(`${api}/auth/me/profile`, { headers: authHeaders() });
      currentUser = { is_admin: Boolean((data.user?.scopes || []).includes("admin")) };
      $("userLine").textContent = `${data.user?.username || "User"} · trust ${data.trust?.trust_score ?? "--"}`;
      $("trustScore").textContent = data.trust?.trust_score ?? "--";
      $("penaltyState").textContent = data.rate?.penalty_active ? `${data.rate.cooldown_remaining_seconds}s` : "Clear";
      renderNav();
    }
    async function loadModels() {
      const [modelRows, readinessRows] = await Promise.all([
        request(`${api}/models/`, { headers: authHeaders() }),
        request(`${api}/models/runtime-readiness`, { headers: authHeaders() }),
      ]);
      const runtimeById = new Map((readinessRows || []).map(item => [String(item.model_id), item]));
      models = (modelRows || []).map(m => ({ ...m, runtime: runtimeById.get(String(m.id)) || null }));
      $("modelSelect").innerHTML = models.map(m => `<option value="${m.id}">${esc(m.name)} · ${esc(m.runtime?.label || "Ready")}</option>`).join("") || `<option value="">No models</option>`;
    }
    async function loadSessions() {
      sessions = await request(`${api}/chat/sessions`, { headers: authHeaders() });
      if (!sessions.length) {
        const model = models.find(m => m.runtime?.runtime_ready !== false) || models[0];
        const created = await request(`${api}/chat/sessions`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ model_id: model?.id || null }),
        });
        sessions = [created];
      }
      if (!activeId || !sessions.some(s => String(s.id) === String(activeId))) activeId = sessions[0]?.id;
      const session = activeSession();
      if (session?.model_id) $("modelSelect").value = String(session.model_id);
      else if (models[0]) $("modelSelect").value = String(models[0].id);
    }
    async function refreshSessions() {
      const previous = activeId;
      sessions = await request(`${api}/chat/sessions`, { headers: authHeaders() });
      activeId = sessions.some(s => String(s.id) === String(previous)) ? previous : sessions[0]?.id;
      render();
    }
    async function newChat() {
      const modelId = Number($("modelSelect").value || 0) || null;
      const created = await request(`${api}/chat/sessions`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId }),
      });
      sessions.unshift(created);
      activeId = created.id;
      render();
    }
    async function deleteChat() {
      if (!activeId) return;
      await request(`${api}/chat/sessions/${activeId}`, { method: "DELETE", headers: authHeaders() });
      await loadSessions();
      render();
    }
    function setStreaming(active) {
      streaming = active;
      $("sendBtn").style.display = active ? "none" : "";
      $("stopBtn").style.display = active ? "" : "none";
      renderRuntime();
    }
    async function sendMessage() {
      const text = $("prompt").value.trim();
      const session = activeSession();
      const modelId = Number($("modelSelect").value || session?.model_id);
      if (!text || !session || !modelId) return;

      const baseRows = messageRows(session);
      const optimistic = [...baseRows, { role: "user", content: text }, { role: "assistant", content: "", streaming: true }];
      const outboundMessages = [...baseRows.filter(m => m.role === "user" || m.role === "assistant").map(m => ({ role: m.role, content: m.content })), { role: "user", content: text }];
      $("prompt").value = "";
      render(optimistic);
      setStreaming(true);
      abortController = new AbortController();

      let assistantText = "";
      let decision = null;
      try {
        const response = await fetch(`${api}/usage/stream-infer`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: session.id, model_id: modelId, prompt: text, messages: outboundMessages, parameters: { temperature: 0.7, max_tokens: 700 } }),
          signal: abortController.signal,
        });
        if (!response.ok) throw new Error(await response.text());
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\\n\\n");
          buffer = events.pop() || "";
          for (const raw of events) {
            if (!raw.startsWith("data: ")) continue;
            let evt;
            try { evt = JSON.parse(raw.slice(6)); } catch { continue; }
            if (evt.type === "decision") {
              decision = evt;
              setDecision(evt);
            } else if (evt.type === "warming") {
              optimistic[optimistic.length - 1] = { role: "assistant", content: evt.message || "Model warming up...", streaming: true, warming: true };
              renderMessages(optimistic);
            } else if (evt.type === "content_delta") {
              assistantText += evt.text || "";
              optimistic[optimistic.length - 1] = { role: "assistant", content: assistantText, streaming: true };
              renderMessages(optimistic);
            } else if (evt.type === "output_guard") {
              assistantText = evt.text || evt.reason || assistantText;
              optimistic[optimistic.length - 1] = { role: evt.blocked ? "system" : "assistant", content: assistantText, gateway: decision };
              renderMessages(optimistic);
            } else if (evt.type === "error") {
              optimistic[optimistic.length - 1] = { role: "system", content: evt.message || "Gateway error" };
              renderMessages(optimistic);
            } else if (evt.type === "done") {
              optimistic[optimistic.length - 1].streaming = false;
            }
          }
        }
        await refreshSessions();
        await loadProfile();
      } catch (err) {
        if (err.name !== "AbortError") {
          optimistic[optimistic.length - 1] = { role: "system", content: err.message || "Gateway error" };
          renderMessages(optimistic);
        }
      } finally {
        abortController = null;
        setStreaming(false);
      }
    }

    async function boot() {
      await Promise.all([loadProfile(), loadModels()]);
      await loadSessions();
      render();
      try {
        const zta = await request(`${api}/monitoring/zta/status`, { headers: authHeaders() });
        $("ztaPill").textContent = zta.enabled ? "Protected" : "Unprotected";
        $("ztaPill").className = `pill ${zta.enabled ? "allow" : "block"}`;
      } catch {}
    }

    $("newBtn").onclick = newChat;
    $("deleteBtn").onclick = deleteChat;
    $("logoutBtn").onclick = () => { sessionStorage.removeItem("zta_token"); location.href = "/login"; };
    $("sendBtn").onclick = sendMessage;
    $("stopBtn").onclick = () => abortController?.abort();
    $("inspectorBtn").onclick = () => $("inspector").classList.toggle("open");
    $("closeInspector").onclick = () => $("inspector").classList.remove("open");
    $("modelSelect").onchange = async () => {
      const session = activeSession();
      if (session) {
        session.model_id = Number($("modelSelect").value);
        await request(`${api}/chat/sessions/${session.id}`, {
          method: "PATCH",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ model_id: session.model_id }),
        }).catch(() => {});
      }
      render();
    };
    $("prompt").addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    boot().catch(() => { sessionStorage.removeItem("zta_token"); location.href = "/login?next=/dashboard/chat"; });
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
