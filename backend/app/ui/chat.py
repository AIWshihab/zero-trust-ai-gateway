CHAT_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Protected AI Chat</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #070706;
      --panel: rgba(18, 18, 16, .94);
      --panel-2: rgba(29, 26, 22, .94);
      --line: rgba(255, 178, 77, .34);
      --line-strong: rgba(255, 178, 77, .58);
      --text: #fff7ea;
      --muted: #d4c0a4;
      --soft: #aab3bf;
      --amber: #ffb13b;
      --red: #ff4d3d;
      --green: #78e08f;
      --cyan: #8ce9ff;
      --blue: #6fb0ff;
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
        radial-gradient(circle at 18% 10%, rgba(255, 159, 28, .25), transparent 28%),
        radial-gradient(circle at 92% 8%, rgba(140, 233, 255, .12), transparent 30%),
        linear-gradient(140deg, #070706 0%, #15110d 45%, #2b1207 82%, #070706 100%);
      overflow: hidden;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,241,213,.07) 2px, transparent 2px),
        linear-gradient(90deg, rgba(255,241,213,.07) 2px, transparent 2px),
        repeating-linear-gradient(105deg, transparent 0 28px, rgba(255,255,255,.065) 29px 31px);
      background-size: 116px 64px, 116px 64px, 220px 220px;
      opacity: .5;
      mask-image: linear-gradient(to bottom, #000, transparent 90%);
    }
    .app {
      position: relative;
      z-index: 1;
      height: 100vh;
      display: grid;
      grid-template-columns: 310px minmax(0, 1fr) 320px;
      gap: 12px;
      padding: 14px;
    }
    .panel {
      border: 2px solid var(--ink);
      border-radius: 7px;
      background: var(--panel);
      box-shadow: 6px 6px 0 rgba(0,0,0,.72), 0 22px 70px rgba(0,0,0,.34);
      overflow: hidden;
      min-height: 0;
      position: relative;
    }
    .panel::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(120deg, rgba(255,255,255,.07), transparent 28%, transparent 78%, rgba(255,255,255,.035)),
        repeating-linear-gradient(-12deg, transparent 0 19px, rgba(255,159,28,.05) 20px 22px);
      opacity: .7;
    }
    .inner { position: relative; z-index: 1; height: 100%; }
    .sidebar .inner, .inspector .inner {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 13px;
      min-height: 0;
    }
    .brand {
      display: grid;
      gap: 5px;
      padding-bottom: 8px;
      border-bottom: 2px solid rgba(255,178,77,.22);
    }
    .eyebrow { color: var(--amber); text-transform: uppercase; letter-spacing: .12em; font-weight: 950; font-size: 11px; }
    h1 {
      margin: 0;
      font-size: 25px;
      line-height: 1;
      text-transform: uppercase;
      text-shadow: 3px 3px 0 #000, 5px 5px 0 rgba(244, 123, 32, .34);
    }
    h2 {
      margin: 0;
      color: var(--amber);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: .1em;
      text-shadow: 2px 2px 0 #000;
    }
    .muted { color: var(--soft); font-size: 12px; line-height: 1.42; }
    a, button {
      border: 2px solid #050403;
      border-radius: 7px;
      padding: 10px 11px;
      color: #170b04;
      background: linear-gradient(135deg, #ffd164, #ff8128 54%, #ef3f20);
      box-shadow: 4px 4px 0 rgba(0,0,0,.72);
      font-weight: 900;
      text-decoration: none;
      cursor: pointer;
      font: inherit;
      transition: transform .16s ease, filter .16s ease, opacity .16s ease;
    }
    a:hover, button:hover { transform: translate(-1px, -2px); filter: brightness(1.08); }
    button:disabled { opacity: .55; cursor: wait; transform: none; }
    .secondary, a.secondary { background: rgba(255, 241, 213, .08); color: var(--text); border-color: rgba(255, 178, 77, .48); }
    .danger { color: #ffd6d6; background: rgba(255,77,61,.18); border-color: rgba(255,77,61,.44); }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    label { display: grid; gap: 6px; color: #dce5f1; font-weight: 850; font-size: 12px; }
    input, textarea, select {
      width: 100%;
      border: 2px solid rgba(255, 178, 77, .34);
      border-radius: 7px;
      background: rgba(8, 6, 4, .82);
      color: var(--text);
      padding: 10px 11px;
      font: inherit;
      outline: none;
    }
    textarea { resize: none; line-height: 1.48; }
    input:focus, textarea:focus, select:focus { border-color: var(--amber); box-shadow: 0 0 0 3px rgba(255, 159, 28, .16); }
    .sessions {
      display: grid;
      gap: 8px;
      overflow: auto;
      min-height: 100px;
      padding-right: 2px;
    }
    .session {
      text-align: left;
      color: var(--text);
      background: rgba(0,0,0,.28);
      border-color: rgba(255,178,77,.28);
      box-shadow: 3px 3px 0 rgba(0,0,0,.45);
      min-height: 64px;
    }
    .session.active { border-color: var(--amber); background: rgba(255,159,28,.14); }
    .session small { display: block; margin-top: 4px; color: var(--soft); font-weight: 750; }
    .chat {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      min-height: 0;
    }
    .chat-head {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 13px;
      border-bottom: 2px solid rgba(255,178,77,.22);
    }
    .chat-title { min-width: 0; }
    .chat-title strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      border: 2px solid #050403;
      border-radius: 999px;
      padding: 7px 9px;
      color: #fff0d5;
      background: rgba(0,0,0,.36);
      box-shadow: 3px 3px 0 rgba(0,0,0,.62);
      font-size: 12px;
      font-weight: 900;
      white-space: nowrap;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 16px var(--green); }
    .dot.bad { background: var(--red); box-shadow: 0 0 16px var(--red); }
    .messages {
      position: relative;
      z-index: 1;
      overflow: auto;
      min-height: 0;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .empty {
      margin: auto;
      max-width: 640px;
      text-align: center;
      color: #ffe9c5;
      display: grid;
      gap: 10px;
    }
    .empty strong {
      font-size: clamp(28px, 5vw, 54px);
      line-height: .96;
      text-transform: uppercase;
      text-shadow: 4px 4px 0 #000, 7px 7px 0 rgba(244,123,32,.34);
    }
    .bubble {
      width: min(820px, 92%);
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(0,0,0,.30);
      box-shadow: 4px 4px 0 rgba(0,0,0,.42);
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .bubble.user {
      align-self: flex-end;
      background: linear-gradient(135deg, rgba(255,159,28,.22), rgba(255,255,255,.04));
      border-color: rgba(255,178,77,.42);
    }
    .bubble.assistant { align-self: flex-start; }
    .bubble.system {
      align-self: center;
      width: min(720px, 94%);
      color: #ffe1df;
      border-color: rgba(255,77,61,.42);
      background: rgba(255,77,61,.10);
    }
    .bubble-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 6px;
      color: var(--amber);
      font-size: 12px;
      font-weight: 950;
      text-transform: uppercase;
      letter-spacing: .08em;
    }
    .composer {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      padding: 13px;
      border-top: 2px solid rgba(255,178,77,.22);
      background: rgba(0,0,0,.18);
    }
    .composer textarea { min-height: 54px; max-height: 170px; }
    .send-stack { display: grid; gap: 8px; align-content: end; min-width: 124px; }
    .card {
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 7px;
      padding: 10px;
      background: rgba(0,0,0,.24);
    }
    .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .metric { border: 2px solid rgba(255,178,77,.2); border-radius: 7px; padding: 9px; background: rgba(0,0,0,.24); min-height: 70px; }
    .metric b { display: block; font-size: 19px; margin-top: 5px; }
    .status-card {
      border: 2px solid rgba(255,178,77,.26);
      border-radius: 7px;
      padding: 10px;
      background: rgba(0,0,0,.22);
      display: grid;
      gap: 5px;
    }
    .status-card.ready { border-color: rgba(120,224,143,.42); }
    .status-card.warn { border-color: rgba(255,178,77,.58); }
    .status-card.bad { border-color: rgba(255,77,61,.48); background: rgba(255,77,61,.08); }
    .status-card strong { color: var(--text); }
    .status-card small { color: var(--soft); line-height: 1.35; }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 110px;
      max-height: 270px;
      overflow: auto;
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 7px;
      padding: 10px;
      background: rgba(8,6,4,.82);
      color: #fff1d5;
      font-size: 12px;
      line-height: 1.45;
    }
    .quick-grid { display: grid; gap: 8px; }
    .quick-grid button { text-align: left; color: var(--text); background: rgba(255,241,213,.08); border-color: rgba(255,178,77,.36); }
    @media (max-width: 1120px) {
      .app { grid-template-columns: 280px minmax(0, 1fr); }
      .inspector { display: none; }
    }
    @media (max-width: 780px) {
      body { overflow: auto; }
      .app { height: auto; min-height: 100vh; grid-template-columns: 1fr; }
      .sidebar { order: 1; }
      .chat { order: 2; }
      .inspector { order: 3; }
      .chat { min-height: 76vh; }
      .composer { grid-template-columns: 1fr; }
      .send-stack { grid-template-columns: repeat(2, 1fr); min-width: 0; }
      .chat-head { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main class="app">
    <aside class="panel sidebar">
      <div class="inner">
        <div class="brand">
          <div class="eyebrow">Protected AI Chat</div>
          <h1>Gateway Chat</h1>
          <div class="muted">Chat with registered models through the Zero Trust policy layer.</div>
        </div>
        <div class="row">
          <a class="secondary" href="/dashboard">Dashboard</a>
          <a class="secondary" href="/models-manager">Models</a>
          <button id="logoutBtn" class="secondary">Logout</button>
        </div>
        <div class="card"><div class="muted" id="userLine">Checking session...</div></div>
        <label>Model <select id="modelSelect"><option>Login to load models</option></select></label>
        <div id="modelStatus" class="status-card warn">
          <strong>Select a model</strong>
          <small>The gateway will show whether chat is ready, needs setup, or can only run a security pre-screen.</small>
        </div>
        <div class="row">
          <button id="newChatBtn">New Chat</button>
          <button id="deleteChatBtn" class="danger">Delete</button>
        </div>
        <h2>Conversations</h2>
        <div id="sessions" class="sessions"></div>
      </div>
    </aside>

    <section class="panel chat">
      <div class="chat-head">
        <div class="chat-title">
          <strong id="chatTitle">New protected conversation</strong>
          <div id="modelLine" class="muted">Select a model and start chatting.</div>
        </div>
        <div class="row">
          <span id="ztaStatus" class="pill"><span class="dot bad"></span>Login</span>
          <span id="decisionPill" class="pill">No decision</span>
        </div>
      </div>
      <div id="messages" class="messages"></div>
      <div class="composer">
        <textarea id="prompt" placeholder="Ask anything. The gateway will screen your message before sending it to the selected model."></textarea>
        <div class="send-stack">
          <button id="sendBtn">Send</button>
          <button id="clearBtn" class="secondary">Clear</button>
        </div>
      </div>
    </section>

    <aside class="panel inspector">
      <div class="inner">
        <h2>Safety Trace</h2>
        <div class="metric-grid">
          <div class="metric"><span class="muted">Trust</span><b id="trustScore">--</b></div>
          <div class="metric"><span class="muted">Penalty</span><b id="penaltyState">--</b></div>
          <div class="metric"><span class="muted">Prompt Risk</span><b id="promptRisk">--</b></div>
          <div class="metric"><span class="muted">Security</span><b id="securityScore">--</b></div>
        </div>
        <div class="card">
          <h2>Quick Starts</h2>
          <div class="quick-grid">
            <button class="quick">Explain this model's safety posture in simple terms.</button>
            <button class="quick">Draft a secure AI usage policy for my team.</button>
            <button class="quick">Help me test this model with a safe red-team checklist.</button>
          </div>
        </div>
        <h2>Latest Gateway Result</h2>
        <pre id="decisionTrace">No messages yet.</pre>
      </div>
    </aside>
  </main>

  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    const stateKey = "zta_chat_sessions_v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/chat";
    const authHeaders = () => ({ Authorization: `Bearer ${token}` });
    let sessions = [];
    let activeId = null;
    let models = [];

    function nowTime() {
      return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    function uid() {
      return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
    function save() {
      localStorage.setItem(stateKey, JSON.stringify({ sessions, activeId }));
    }
    function load() {
      try {
        const parsed = JSON.parse(localStorage.getItem(stateKey) || "{}");
        sessions = Array.isArray(parsed.sessions) ? parsed.sessions : [];
        activeId = parsed.activeId || null;
      } catch {
        sessions = [];
        activeId = null;
      }
      if (!sessions.length) createSession(false);
      if (!sessions.some((item) => item.id === activeId)) activeId = sessions[0].id;
    }
    function activeSession() {
      return sessions.find((item) => item.id === activeId);
    }
    function createSession(renderNow = true) {
      const session = { id: uid(), title: "New protected conversation", modelId: null, messages: [], createdAt: Date.now(), updatedAt: Date.now() };
      sessions.unshift(session);
      activeId = session.id;
      save();
      if (renderNow) render();
      return session;
    }
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) {
        const err = new Error(normalizeErrorMessage(data, res.status));
        err.status = res.status;
        err.payload = data;
        throw err;
      }
      return data;
    }
    function normalizeErrorMessage(data, status) {
      const detail = typeof data === "object" ? data.detail : data;
      if (detail && typeof detail === "object" && detail.title) return `${detail.title}: ${detail.explanation || detail.reason || detail.message || ""}`;
      if (detail && typeof detail === "object" && detail.message) return detail.message;
      const raw = typeof detail === "string" ? detail : JSON.stringify(detail || data || "");
      if (raw.includes("HF_TOKEN")) {
        return "This Hugging Face model is not available yet because the server is missing its Hugging Face token. Choose another ready model, or ask an admin to configure HF_TOKEN.";
      }
      if (status === 503) {
        return "The selected model is temporarily unavailable. Try another model or ask an admin to check the provider connection.";
      }
      if (status === 409) {
        return "This model is not ready for chat yet. Ask an admin to scan or protect it first, or choose another model.";
      }
      if (status === 401 || status === 403) {
        return "Your session is not authorized. Please log in again.";
      }
      return raw || "The gateway could not complete this request.";
    }
    function normalizeErrorDetail(data, status) {
      const detail = typeof data === "object" ? data.detail : data;
      if (detail && typeof detail === "object") return detail;
      return {
        code: status === 401 || status === 403 ? "auth_error" : "gateway_error",
        title: status === 401 || status === 403 ? "Session problem" : "Gateway error",
        reason: normalizeErrorMessage(data, status),
        explanation: normalizeErrorMessage(data, status),
        suggested_fix: status === 401 || status === 403 ? "Log in again from the login page." : "Try again or choose another model.",
        action_required: status === 401 || status === 403 ? "user" : "user"
      };
    }
    function compactContext(messages) {
      return messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .slice(-8)
        .map((m) => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`)
        .join("\\n\\n");
    }
    function buildPrompt(session, currentPrompt) {
      const context = compactContext(session.messages);
      if (!context) return currentPrompt;
      return `Continue this conversation. Use the prior messages only as context.\\n\\n${context}\\n\\nUser: ${currentPrompt}`;
    }
    function setDecision(data) {
      const decision = String(data.decision || "unknown").toUpperCase();
      $("decisionPill").textContent = decision;
      $("promptRisk").textContent = data.prompt_risk_score == null ? "--" : `${Math.round(data.prompt_risk_score * 100)}%`;
      $("securityScore").textContent = data.security_score == null ? "--" : `${Math.round(data.security_score * 100)}%`;
      showTrace(formatTrace(data));
    }
    function setUnavailableTrace(message, status) {
      $("decisionPill").textContent = "Unavailable";
      $("promptRisk").textContent = "--";
      $("securityScore").textContent = "--";
      showTrace({
        status: "model_unavailable",
        http_status: status || null,
        user_message: message,
        next_step: "Choose a runtime-ready model or ask an admin to configure the provider credentials."
      });
    }
    function setStructuredTrace(detail, status) {
      const policyText = detail.policy_decision ? String(detail.policy_decision).toUpperCase() : "";
      $("decisionPill").textContent = detail.status === "model_not_callable" && policyText ? `Pre-screen ${policyText}` : (policyText || "Unavailable");
      $("promptRisk").textContent = detail.prompt_risk_score == null ? "--" : `${Math.round(detail.prompt_risk_score * 100)}%`;
      $("securityScore").textContent = detail.security_score == null ? "--" : `${Math.round(detail.security_score * 100)}%`;
      showTrace({
        status: detail.status || "gateway_notice",
        code: detail.code,
        title: detail.title,
        reason: detail.reason,
        explanation: detail.explanation,
        suggested_fix: detail.suggested_fix,
        action_required: detail.action_required || "user",
        policy_decision: detail.policy_decision || null,
        prompt_risk: detail.prompt_risk_score == null ? null : `${Math.round(detail.prompt_risk_score * 100)}%`,
        security_score: detail.security_score == null ? null : `${Math.round(detail.security_score * 100)}%`
      });
    }
    function formatTrace(data) {
      return {
        decision: data.decision,
        blocked: data.blocked,
        prompt_risk: data.prompt_risk_score == null ? null : `${Math.round(data.prompt_risk_score * 100)}%`,
        security_score: data.security_score == null ? null : `${Math.round(data.security_score * 100)}%`,
        output_risk: data.output_risk_score,
        secure_mode: data.secure_mode_enabled ? "on" : "off",
        summary: data.reason || "Gateway decision completed.",
        cooldown: data.enforcement_profile?.penalty_active
          ? `${data.enforcement_profile.cooldown_remaining_seconds || 0}s remaining`
          : "clear"
      };
    }
    function showTrace(value) {
      $("decisionTrace").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }
    function renderSessions() {
      $("sessions").innerHTML = sessions.map((session) => {
        const count = session.messages.filter((m) => m.role !== "system").length;
        return `<button class="session ${session.id === activeId ? "active" : ""}" data-id="${session.id}">${escapeHtml(session.title)}<small>${count} messages</small></button>`;
      }).join("");
      document.querySelectorAll(".session").forEach((btn) => {
        btn.addEventListener("click", () => {
          activeId = btn.dataset.id;
          save();
          render();
        });
      });
    }
    function renderMessages() {
      const session = activeSession();
      $("chatTitle").textContent = session.title;
      const selected = models.find((m) => String(m.id) === String(session.modelId || $("modelSelect").value));
      const runtime = selected?.runtime;
      const runtimeLabel = runtime?.label || (runtime?.runtime_ready === false ? "Needs setup" : "Ready");
      $("modelLine").textContent = selected ? `${selected.name} · ${selected.model_type} · ${runtimeLabel}` : "Select a model and start chatting.";
      renderSelectedModelStatus(selected);
      if (session.modelId && $("modelSelect").value !== String(session.modelId)) $("modelSelect").value = String(session.modelId);

      if (!session.messages.length) {
        $("messages").innerHTML = `<div class="empty"><strong>Start A Protected Chat</strong><span>Choose a registered model, ask normally, and the gateway will keep the conversation screened with prompt guard, formal risk, trust scoring, and audit logging.</span></div>`;
        return;
      }
      $("messages").innerHTML = session.messages.map((message) => `
        <article class="bubble ${message.role}">
          <div class="bubble-head"><span>${message.role === "assistant" ? "AI" : message.role}</span><span>${message.time || ""}</span></div>
          <div>${escapeHtml(message.content)}</div>
        </article>
      `).join("");
      $("messages").scrollTop = $("messages").scrollHeight;
    }
    function render() {
      renderSessions();
      renderMessages();
      save();
    }
    function renderSelectedModelStatus(selected) {
      if (!selected) {
        $("modelStatus").className = "status-card warn";
        $("modelStatus").innerHTML = `<strong>No model selected</strong><small>Choose a registered model to see whether it can chat now.</small>`;
        $("sendBtn").textContent = "Send";
        $("sendBtn").disabled = true;
        return;
      }
      const runtime = selected.runtime || {};
      const ready = runtime.runtime_ready !== false;
      const canPrescreen = runtime.can_prescreen !== false;
      const severity = ready ? "ready" : (canPrescreen ? "warn" : "bad");
      $("modelStatus").className = `status-card ${severity}`;
      $("modelStatus").innerHTML = `
        <strong>${escapeHtml(runtime.label || (ready ? "Ready" : "Needs setup"))}</strong>
        <small>${escapeHtml(runtime.explanation || runtime.message || "Runtime status is not available.")}</small>
        <small><b>Next:</b> ${escapeHtml(runtime.suggested_fix || runtime.next_step || "Choose a ready model or ask an admin to check setup.")}</small>
      `;
      $("sendBtn").textContent = ready ? "Send" : (canPrescreen ? "Pre-screen" : "Unavailable");
      $("sendBtn").disabled = !canPrescreen;
    }
    function escapeHtml(value) {
      return String(value || "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[ch]));
    }
    async function afterAuth() {
      await Promise.all([loadProfile(), loadModels(), zta()]);
    }
    async function loadProfile() {
      const data = await request(`${api}/auth/me/profile`, { headers: authHeaders() });
      $("userLine").textContent = `${data.user?.username || "User"} · trust ${data.trust?.trust_score ?? "--"} · ${data.security_posture?.status || "active"}`;
      $("trustScore").textContent = data.trust?.trust_score ?? "--";
      $("penaltyState").textContent = data.rate?.penalty_active ? `${data.rate.cooldown_remaining_seconds}s` : "Clear";
    }
    async function loadModels() {
      const [modelRows, readinessRows] = await Promise.all([
        request(`${api}/models/`, { headers: authHeaders() }),
        request(`${api}/models/runtime-readiness`, { headers: authHeaders() })
      ]);
      const runtimeById = new Map((readinessRows || []).map((item) => [String(item.model_id), item]));
      models = modelRows.map((m) => ({ ...m, runtime: runtimeById.get(String(m.id)) || null }));
      $("modelSelect").innerHTML = models.map((m) => {
        const runtime = m.runtime;
        const label = runtime?.label || (runtime?.runtime_ready === false ? "Needs setup" : "Ready");
        return `<option value="${m.id}">${escapeHtml(m.name)} · ${escapeHtml(label)}</option>`;
      }).join("") || `<option value="">No models registered</option>`;
      const session = activeSession();
      const selected = models.find((m) => String(m.id) === String(session.modelId));
      const readyModel = models.find((m) => m.runtime?.runtime_ready !== false);
      if ((!session.modelId || selected?.runtime?.runtime_ready === false) && readyModel) session.modelId = readyModel.id;
      if (!session.modelId && models[0]) session.modelId = models[0].id;
      if (session.modelId) $("modelSelect").value = String(session.modelId);
      if (!readyModel) {
        setStructuredTrace({
          code: "no_ready_models",
          title: "No ready models",
          reason: "Every registered model needs setup before full chat.",
          explanation: "You can select a model and run the gateway pre-screen, but inference will not run until an admin fixes model setup.",
          suggested_fix: "Ask an admin to configure provider tokens, run assessments, or add a reachable local/custom endpoint.",
          action_required: "admin",
          status: "model_not_callable"
        }, 503);
      }
      render();
    }
    async function zta() {
      try {
        const data = await request(`${api}/monitoring/zta/status`, { headers: authHeaders() });
        $("ztaStatus").innerHTML = `<span class="dot ${data.enabled ? "" : "bad"}"></span>${data.enabled ? "Protected" : "Unprotected"}`;
      } catch {
        $("ztaStatus").innerHTML = `<span class="dot bad"></span>Login`;
      }
    }
    async function sendMessage() {
      const session = activeSession();
      const raw = $("prompt").value.trim();
      if (!raw) return;
      const modelId = Number($("modelSelect").value || session.modelId);
      if (!modelId) {
        showTrace("Select a model first.");
        return;
      }
      const selected = models.find((m) => Number(m.id) === modelId);
      session.modelId = modelId;
      if (session.title === "New protected conversation") session.title = raw.slice(0, 54) || session.title;
      session.messages.push({ role: "user", content: raw, time: nowTime() });
      $("prompt").value = "";
      render();
      $("sendBtn").disabled = true;

      try {
        const body = {
          model_id: modelId,
          prompt: buildPrompt(session, raw),
          parameters: { temperature: 0.2, max_tokens: 700 }
        };
        const data = await request(`${api}/usage/infer`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        setDecision(data);
        const content = data.output || friendlyBlockedMessage(data.reason) || "The gateway returned no model output.";
        session.messages.push({
          role: data.blocked ? "system" : "assistant",
          content,
          time: nowTime()
        });
        session.updatedAt = Date.now();
        await loadProfile();
      } catch (err) {
        const detail = normalizeErrorDetail(err.payload || err.message, err.status);
        setStructuredTrace(detail, err.status);
        session.messages.push({
          role: "system",
          content: `${detail.title || "Gateway notice"}\\n${detail.explanation || detail.reason || normalizeErrorMessage(err.payload || err.message, err.status)}\\nNext: ${detail.suggested_fix || "Try another model or ask an admin to check setup."}`,
          time: nowTime()
        });
      } finally {
        $("sendBtn").disabled = false;
        render();
      }
    }
    function friendlyBlockedMessage(reason) {
      if (!reason) return "";
      if (String(reason).includes("HF_TOKEN")) {
        return "This model is not available yet because its provider credentials are not configured.";
      }
      return reason;
    }
    function deleteChat() {
      if (sessions.length <= 1) {
        sessions = [];
        createSession(false);
      } else {
        sessions = sessions.filter((item) => item.id !== activeId);
        activeId = sessions[0].id;
      }
      render();
    }
    function clearCurrent() {
      const session = activeSession();
      session.messages = [];
      session.title = "New protected conversation";
      session.updatedAt = Date.now();
      render();
    }

    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      location.href = "/login";
    });
    $("sendBtn").addEventListener("click", sendMessage);
    $("newChatBtn").addEventListener("click", () => createSession(true));
    $("deleteChatBtn").addEventListener("click", deleteChat);
    $("clearBtn").addEventListener("click", clearCurrent);
    $("modelSelect").addEventListener("change", () => {
      const session = activeSession();
      session.modelId = Number($("modelSelect").value);
      render();
    });
    $("prompt").addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
      }
    });
    document.querySelectorAll(".quick").forEach((button) => {
      button.addEventListener("click", () => {
        $("prompt").value = button.textContent.trim();
        $("prompt").focus();
      });
    });

    load();
    render();
    afterAuth().catch((err) => {
      sessionStorage.removeItem("zta_token");
      location.href = "/login?next=/chat";
    });
    zta();
  </script>
</body>
</html>
"""
