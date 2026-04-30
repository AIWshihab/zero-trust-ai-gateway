MODEL_MANAGER_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Model Registry Manager</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #090806;
      --panel: rgba(20, 18, 16, .9);
      --text: #fff7ea;
      --muted: #d3b99a;
      --green: #73e28b;
      --cyan: #8ce9ff;
      --amber: #ff9f1c;
      --red: #ff4d3d;
      --blue: #6fb0ff;
      --ink: #080604;
      --cream: #fff1d5;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 14% 10%, rgba(255,159,28,.28), transparent 28%),
        radial-gradient(circle at 85% 3%, rgba(255,77,61,.17), transparent 30%),
        linear-gradient(120deg, rgba(255,255,255,.035) 0 1px, transparent 1px 72px),
        linear-gradient(135deg, #090806, #15100b 50%, #2b1207);
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
        radial-gradient(circle, rgba(255,255,255,.16) 1px, transparent 1.5px);
      background-size: 118px 66px, 118px 66px, 9px 9px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), rgba(0,0,0,.12));
    }
    body::after {
      content: "";
      position: fixed;
      inset: -18% -8%;
      pointer-events: none;
      background: repeating-linear-gradient(112deg, transparent 0 24px, rgba(255,255,255,.08) 25px 27px, transparent 28px 56px);
      opacity: .5;
      transform: skewY(-5deg);
      animation: rush 12s linear infinite;
    }
    .shell { position: relative; z-index: 1; padding: 22px clamp(14px, 3vw, 34px) 34px; }
    header {
      display: grid;
      grid-template-columns: minmax(300px, 1fr) auto;
      gap: 18px;
      align-items: start;
      margin-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: clamp(30px, 4.2vw, 58px);
      letter-spacing: 0;
      line-height: .94;
      text-transform: uppercase;
      text-shadow: 4px 4px 0 var(--ink), 7px 7px 0 rgba(255,159,28,.34);
    }
    p { margin: 10px 0 0; color: var(--cream); line-height: 1.55; max-width: 890px; font-weight: 680; }
    a, button {
      border: 2px solid var(--ink);
      border-radius: 7px;
      padding: 10px 12px;
      color: var(--cream);
      background: rgba(255,241,213,.08);
      font-weight: 840;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      box-shadow: 4px 4px 0 rgba(0,0,0,.65);
      transition: transform .18s ease, filter .18s ease, opacity .18s ease;
    }
    a:hover, button:hover { transform: translate(-1px, -2px); filter: brightness(1.08); }
    button:disabled { opacity: .55; cursor: wait; transform: none; }
    button.primary { background: linear-gradient(135deg, #ffd164, #ff7a1a 52%, #f0441f); color: #150905; border: 2px solid var(--ink); }
    button.danger { background: rgba(255,77,61,.18); color: #ffd6d6; border-color: rgba(255,77,61,.42); }
    .row { display: flex; gap: 9px; flex-wrap: wrap; align-items: center; }
    .layout { display: grid; grid-template-columns: minmax(320px, 430px) 1fr; gap: 16px; align-items: start; }
    .panel {
      border: 2px solid var(--ink);
      border-radius: 6px;
      background: var(--panel);
      box-shadow: 7px 7px 0 rgba(0,0,0,.72), 0 24px 80px rgba(0,0,0,.36);
      backdrop-filter: blur(22px);
      padding: 16px;
      position: relative;
      overflow: hidden;
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
    .panel > * { position: relative; z-index: 1; }
    h2 { margin: 0 0 12px; font-size: 14px; text-transform: uppercase; letter-spacing: .08em; color: var(--amber); text-shadow: 2px 2px 0 #000; }
    label { display: grid; gap: 6px; font-size: 12px; font-weight: 780; color: var(--cream); margin-bottom: 10px; }
    input, textarea, select {
      width: 100%;
      border: 2px solid rgba(255,178,77,.34);
      background: rgba(8,6,4,.82);
      color: var(--text);
      border-radius: 7px;
      padding: 10px 11px;
      font: inherit;
      outline: none;
    }
    input:focus, textarea:focus, select:focus { border-color: var(--amber); box-shadow: 0 0 0 3px rgba(255,159,28,.17); }
    textarea { min-height: 86px; resize: vertical; line-height: 1.48; }
    .cards { display: grid; gap: 10px; }
    .card {
      border: 2px solid rgba(255,178,77,.2);
      border-radius: 8px;
      padding: 12px;
      background: linear-gradient(135deg, rgba(255,159,28,.09), rgba(255,255,255,.03));
      display: grid;
      gap: 9px;
      animation: rise .28s ease both;
      box-shadow: 4px 4px 0 rgba(0,0,0,.42);
    }
    .card-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
    .card-title { min-width: 0; }
    .card-title strong { display: block; font-size: 16px; overflow-wrap: anywhere; }
    .muted { color: var(--muted); font-size: 12px; line-height: 1.45; }
    .badge { border: 1px solid rgba(255,255,255,.18); border-radius: 999px; padding: 5px 7px; font-size: 11px; font-weight: 850; background: rgba(0,0,0,.42); white-space: nowrap; }
    .badge.active { color: var(--green); }
    .badge.inactive, .badge.failed { color: var(--red); }
    .badge.pending, .badge.in_progress { color: var(--amber); }
    .badge.completed, .badge.protected { color: var(--cyan); }
    .hint {
      border: 2px solid rgba(255,178,77,.22);
      border-radius: 8px;
      padding: 10px;
      background: rgba(8,6,4,.58);
      color: var(--cream);
      font-size: 12px;
      line-height: 1.45;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 112px;
      max-height: 320px;
      overflow: auto;
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(8,6,4,.82);
      color: var(--cream);
      font-size: 12px;
      line-height: 1.45;
    }
    .admin-only.hidden { display: none; }
    .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin-bottom: 12px; }
    .metric { border: 2px solid rgba(255,178,77,.2); border-radius: 8px; padding: 10px; background: rgba(8,6,4,.52); }
    .metric strong { display: block; font-size: 22px; margin-top: 5px; }
    @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes rush { to { transform: skewY(-5deg) translateX(-120px); } }
    @media (max-width: 920px) { header, .layout { grid-template-columns: 1fr; } .stats { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div>
        <h1>Model Registry Manager</h1>
        <p>Add AI models from Hugging Face, model URLs, OpenAI-compatible APIs, custom APIs, or local endpoints. The gateway scans each new target before it joins the protected AI window.</p>
      </div>
      <div class="row"><a href="/dashboard">Dashboard</a><a href="/control-plane">Control Plane</a><a href="/logs">Logs</a><button id="logoutBtn">Logout</button></div>
    </header>
    <section class="panel" style="margin-bottom:16px;display:none">
      <div class="row">
        <input id="token" placeholder="Paste bearer token or login below" style="flex:1;min-width:280px" />
        <input id="username" placeholder="username" />
        <input id="password" type="password" placeholder="password" />
        <button id="loginBtn" class="primary">Login</button>
        <span id="roleBadge" class="badge">viewer</span>
      </div>
    </section>
    <div class="layout">
      <section class="panel admin-only hidden" id="addPanel">
        <h2>Add Internet Model</h2>
        <div class="hint">Hugging Face needs either an HF model ID or source URL. Local and custom API models need an endpoint. OpenAI-compatible models can use an endpoint plus provider name.</div>
        <label>Name <input id="name" placeholder="Mistral Guarded Assistant" /></label>
        <label>Type
          <select id="model_type">
            <option value="huggingface">Hugging Face</option>
            <option value="openai">OpenAI / compatible</option>
            <option value="custom_api">Custom API</option>
            <option value="local">Local endpoint</option>
          </select>
        </label>
        <label>Provider <input id="provider_name" placeholder="huggingface, openai, together, local" /></label>
        <label>Hugging Face model ID <input id="hf_model_id" placeholder="mistralai/Mistral-7B-Instruct-v0.3" /></label>
        <label>Source URL <input id="source_url" placeholder="https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3" /></label>
        <label>Endpoint <input id="endpoint" placeholder="https://api.example.com/v1/chat/completions" /></label>
        <label>Description <textarea id="description" placeholder="What this model is used for, owner, data sensitivity, and safety notes."></textarea></label>
        <div class="row">
          <button id="scanBtn" class="primary">Scan And Register</button>
          <button id="clearBtn">Clear</button>
        </div>
        <pre id="result">Ready to onboard a model.</pre>
      </section>
      <section class="panel">
        <div class="row" style="justify-content:space-between;margin-bottom:12px">
          <h2 style="margin:0">Registered Models</h2>
          <button id="refreshBtn">Refresh</button>
        </div>
        <div class="stats">
          <div class="metric"><span class="muted">Total</span><strong id="totalCount">--</strong></div>
          <div class="metric"><span class="muted">Active</span><strong id="activeCount">--</strong></div>
          <div class="metric"><span class="muted">Protected</span><strong id="protectedCount">--</strong></div>
        </div>
        <div id="modelList" class="cards"></div>
      </section>
    </div>
  </div>
  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    let isAdmin = false;
    let models = [];
    const authHeaders = () => ({ Authorization: `Bearer ${$("token").value.trim()}` });
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    function show(value) {
      $("result").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }
    function hydrateTokenFromUrl() {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token") || sessionStorage.getItem("zta_token");
      if (token) {
        $("token").value = token;
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        window.location.href = "/login?next=/models-manager";
      }
    }
    async function login() {
      const form = new URLSearchParams();
      form.set("username", $("username").value);
      form.set("password", $("password").value);
      const data = await request(`${api}/auth/token`, { method: "POST", body: form });
      $("token").value = data.access_token;
      sessionStorage.setItem("zta_token", data.access_token);
      await refreshAll();
    }
    async function loadRole() {
      const profile = await request(`${api}/auth/me/profile`, { headers: authHeaders() });
      isAdmin = (profile.user.scopes || []).includes("admin");
      $("roleBadge").textContent = isAdmin ? "admin editor" : "viewer";
      document.querySelectorAll(".admin-only").forEach((el) => el.classList.toggle("hidden", !isAdmin));
    }
    function statusClass(model) {
      if (!model.is_active) return "inactive";
      return model.scan_status || "pending";
    }
    function renderModels() {
      $("totalCount").textContent = models.length;
      $("activeCount").textContent = models.filter((m) => m.is_active).length;
      $("protectedCount").textContent = models.filter((m) => m.secure_mode_enabled || m.scan_status === "protected").length;
      $("modelList").innerHTML = models.map((m) => {
        const badge = m.is_active ? (m.scan_status || "pending") : "inactive";
        const runtime = m.runtime;
        const runtimeReady = runtime?.runtime_ready !== false;
        const runtimeText = runtimeReady ? "runtime ready" : `needs ${runtime?.missing?.join(", ") || "setup"}`;
        const provider = [m.provider_name, m.hf_model_id].filter(Boolean).join(" / ") || m.source_url || m.endpoint || "registry";
        const trust = m.base_trust_score == null ? "--" : Math.round(m.base_trust_score);
        const risk = m.base_risk_score == null ? "--" : Math.round(m.base_risk_score);
        return `<article class="card">
          <div class="card-head">
            <div class="card-title"><strong>${m.name}</strong><span class="muted">#${m.id} - ${m.model_type} - ${provider}</span></div>
            <span class="badge ${statusClass(m)}">${badge}</span>
          </div>
          <div class="muted">${m.description || "No description yet."}</div>
          <div class="row"><span class="badge">trust ${trust}</span><span class="badge">risk ${risk}</span><span class="badge">${m.sensitivity_level} sensitivity</span><span class="badge ${runtimeReady ? "protected" : "inactive"}">${runtimeText}</span></div>
          ${runtimeReady ? "" : `<div class="hint">${runtime?.message || "Runtime configuration is incomplete."} ${runtime?.next_step || ""}</div>`}
          ${isAdmin ? `<div class="row"><button onclick="rescanModel(${m.id})">Rescan</button>${m.is_active ? `<button class="danger" onclick="deactivateModel(${m.id})">Deactivate</button>` : ""}</div>` : ""}
        </article>`;
      }).join("") || `<div class="hint">No models registered yet.</div>`;
    }
    async function loadModels() {
      const [modelRows, readinessRows] = await Promise.all([
        request(`${api}/models/?include_inactive=true`, { headers: authHeaders() }),
        request(`${api}/models/runtime-readiness?include_inactive=true`, { headers: authHeaders() })
      ]);
      const runtimeById = new Map((readinessRows || []).map((item) => [String(item.model_id), item]));
      models = modelRows.map((model) => ({ ...model, runtime: runtimeById.get(String(model.id)) || null }));
      renderModels();
    }
    function payload() {
      const body = {
        name: $("name").value.trim(),
        model_type: $("model_type").value,
        provider_name: $("provider_name").value.trim() || null,
        hf_model_id: $("hf_model_id").value.trim() || null,
        source_url: $("source_url").value.trim() || null,
        endpoint: $("endpoint").value.trim() || null,
        description: $("description").value.trim() || null
      };
      if (body.model_type === "huggingface" && !body.provider_name) body.provider_name = "huggingface";
      return body;
    }
    async function scanAndRegister() {
      $("scanBtn").disabled = true;
      show("Scanning model posture and registering it...");
      try {
        const data = await request(`${api}/assessment/scan`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify(payload())
        });
        show(data);
        await loadModels();
      } catch (err) {
        show(String(err.message || err));
      } finally {
        $("scanBtn").disabled = false;
      }
    }
    async function deactivateModel(id) {
      if (!confirm("Deactivate this model from the registry? Existing history stays intact.")) return;
      await request(`${api}/models/${id}`, { method: "DELETE", headers: authHeaders() });
      await loadModels();
    }
    async function rescanModel(id) {
      show(`Rescanning model ${id}...`);
      const data = await request(`${api}/assessment/${id}/scan`, { method: "POST", headers: authHeaders() });
      show(data);
      await loadModels();
    }
    function clearForm() {
      for (const id of ["name", "provider_name", "hf_model_id", "source_url", "endpoint", "description"]) $(id).value = "";
      $("model_type").value = "huggingface";
      show("Ready to onboard a model.");
    }
    async function refreshAll() {
      await loadRole();
      await loadModels();
    }
    $("loginBtn").addEventListener("click", login);
    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      window.location.href = "/login";
    });
    $("scanBtn").addEventListener("click", scanAndRegister);
    $("clearBtn").addEventListener("click", clearForm);
    $("refreshBtn").addEventListener("click", async () => {
      $("refreshBtn").disabled = true;
      try { await refreshAll(); } catch (err) { show(String(err.message || err)); }
      finally { $("refreshBtn").disabled = false; }
    });
    window.deactivateModel = deactivateModel;
    window.rescanModel = rescanModel;
    hydrateTokenFromUrl();
    if ($("token").value.trim()) refreshAll().catch((err) => show(String(err.message || err)));
  </script>
</body>
</html>
"""
