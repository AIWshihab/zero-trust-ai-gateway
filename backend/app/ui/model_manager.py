from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


MODEL_MANAGER_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Model Registry — Zero Trust AI Gateway</title>
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
    .shell { padding: 20px clamp(14px,3vw,32px) 32px; }
    .page-header {
      display: grid;
      grid-template-columns: minmax(280px,1fr) auto;
      gap: 16px;
      align-items: start;
      margin-bottom: 20px;
    }
    .page-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
    .page-eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .page-header h1 { font-size: clamp(22px,3vw,34px); font-weight: 700; color: var(--text); line-height: 1.1; }
    .page-header p { font-size: 14px; color: var(--muted); line-height: 1.6; max-width: 640px; margin-top: 6px; }
    .hdr-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    a, button {
      border: 1px solid var(--b2);
      border-radius: 7px;
      padding: 9px 14px;
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
    button.primary { background: var(--cyan); color: #000; border-color: var(--cyan); font-weight: 700; }
    button.primary:hover { background: #00bde8; border-color: #00bde8; }
    button.danger { background: rgba(255,77,109,.12); color: #ffb3c1; border-color: rgba(255,77,109,.3); }
    button.danger:hover { background: rgba(255,77,109,.2); border-color: rgba(255,77,109,.5); }
    .layout { display: grid; grid-template-columns: minmax(300px,400px) 1fr; gap: 16px; align-items: start; }
    .panel {
      border: 1px solid var(--b2);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 18px;
    }
    .panel-title { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
    .panel-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .hint {
      border: 1px solid var(--border);
      border-radius: 7px;
      padding: 10px 12px;
      background: var(--bg-2);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
      margin-bottom: 14px;
    }
    label { display: grid; gap: 5px; font-size: 12px; font-weight: 600; color: var(--muted); letter-spacing: .04em; text-transform: uppercase; margin-bottom: 12px; }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--b2);
      border-radius: 7px;
      background: var(--bg-3);
      color: var(--text);
      padding: 10px 12px;
      font: inherit;
      font-size: 14px;
      outline: none;
      transition: border-color .18s, box-shadow .18s;
      text-transform: none;
      letter-spacing: normal;
      font-weight: 400;
    }
    input:focus, textarea:focus, select:focus { border-color: rgba(0,212,255,.42); box-shadow: 0 0 0 3px rgba(0,212,255,.08); }
    input::placeholder { color: var(--muted); }
    textarea { min-height: 80px; resize: vertical; }
    select option { background: var(--bg-3); }
    .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
    pre {
      margin-top: 12px;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 80px;
      max-height: 280px;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 7px;
      padding: 12px;
      background: var(--bg-2);
      color: var(--muted);
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.5;
    }
    .stats-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
    .metric {
      border: 1px solid var(--border);
      border-radius: 7px;
      padding: 10px 12px;
      background: var(--bg-2);
    }
    .metric-label { font-size: 11px; color: var(--muted); }
    .metric-value { font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--text); }
    .panel-hdr { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .cards { display: grid; gap: 10px; }
    .card {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      background: var(--bg-2);
      display: grid;
      gap: 8px;
      animation: rise .25s ease both;
      transition: border-color .2s;
    }
    .card:hover { border-color: rgba(0,212,255,.18); }
    .card-head { display: flex; justify-content: space-between; gap: 10px; align-items: start; }
    .card-title { min-width: 0; }
    .card-title strong { display: block; font-size: 15px; font-weight: 700; color: var(--text); }
    .card-meta { font-size: 12px; color: var(--muted); margin-top: 2px; }
    .card-desc { font-size: 13px; color: var(--muted); line-height: 1.45; }
    .badge { border: 1px solid var(--b2); border-radius: 999px; padding: 4px 8px; font-size: 11px; font-weight: 700; background: var(--bg-3); white-space: nowrap; color: var(--muted); }
    .badge.active    { color: var(--green); border-color: rgba(34,211,160,.3); background: rgba(34,211,160,.08); }
    .badge.inactive, .badge.failed { color: var(--red); border-color: rgba(255,77,109,.3); background: rgba(255,77,109,.08); }
    .badge.pending, .badge.in_progress { color: var(--amber); border-color: rgba(245,166,35,.3); background: rgba(245,166,35,.08); }
    .badge.completed, .badge.protected { color: var(--cyan); border-color: rgba(0,212,255,.3); background: var(--cyan-d); }
    .card-badges { display: flex; gap: 6px; flex-wrap: wrap; }
    .runtime-hint { font-size: 12px; color: var(--amber); border: 1px solid rgba(245,166,35,.2); border-radius: 6px; padding: 8px 10px; background: rgba(245,166,35,.06); }
    .card-actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .no-content { border: 1px dashed var(--border); border-radius: 8px; padding: 16px; color: var(--muted); text-align: center; font-size: 13px; }
    .admin-only.hidden { display: none; }
    @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @media (max-width: 920px) { .page-header, .layout { grid-template-columns: 1fr; } .stats-strip { grid-template-columns: repeat(2,1fr); } }
    @media (max-width: 420px) { .stats-strip { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Model Registry & Readiness</div>
        <h1>Model Registry</h1>
        <p>Register AI model endpoints for gateway-protected inference. The gateway checks ownership, runtime readiness, model posture, and risk classification before inference is allowed.</p>
      </div>
      <div class="hdr-row">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/policy">Policy Engine</a>
        <a href="/dashboard/security-monitor">Security Monitor</a>
        <button id="logoutBtn">Logout</button>
      </div>
    </div>
    <section class="panel" style="display:none; margin-bottom:16px">
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <input id="token" style="flex:1;min-width:240px" placeholder="Paste bearer token or login below" />
        <input id="username" placeholder="username" />
        <input id="password" type="password" placeholder="password" />
        <button id="loginBtn" class="primary">Login</button>
        <span id="roleBadge" class="badge">viewer</span>
      </div>
    </section>
    <div class="layout">
      <section class="panel" id="addPanel">
        <div class="panel-title">Add Model Endpoint</div>
        <div class="hint">Users can add and manage owned models. Admins can also assess posture and manage any model.</div>
        <label>Name <input id="name" placeholder="Qwen 2.5 7B Instruct" /></label>
        <label>Type
          <select id="model_type">
            <option value="huggingface">Hugging Face</option>
            <option value="openai">OpenAI / compatible</option>
            <option value="custom_api">Custom API</option>
            <option value="local">Local endpoint</option>
          </select>
        </label>
        <label>Provider <input id="provider_name" placeholder="huggingface, openai, together, local" /></label>
        <label>HuggingFace Model ID <input id="hf_model_id" placeholder="Qwen/Qwen2.5-7B-Instruct" /></label>
        <label>Source URL <input id="source_url" placeholder="https://huggingface.co/..." /></label>
        <label>Endpoint <input id="endpoint" placeholder="https://api.example.com/v1/chat/completions" /></label>
        <label>Visibility <select id="visibility"><option value="private">Private</option><option value="shared">Shared</option></select></label>
        <label>Description <textarea id="description" placeholder="What this model is used for, owner, data sensitivity, and safety notes."></textarea></label>
        <div class="btn-row">
          <button id="scanBtn" class="primary">Add Model</button>
          <button id="clearBtn">Clear</button>
        </div>
        <pre id="result">Ready to add a model.</pre>
      </section>
      <section class="panel">
        <div class="panel-hdr">
          <div class="panel-title" style="margin:0">Models</div>
          <button id="refreshBtn">Refresh</button>
        </div>
        <div class="stats-strip">
          <div class="metric"><div class="metric-label">Total</div><div class="metric-value" id="totalCount">--</div></div>
          <div class="metric"><div class="metric-label">Active</div><div class="metric-value" id="activeCount">--</div></div>
          <div class="metric"><div class="metric-label">Protected</div><div class="metric-value" id="protectedCount">--</div></div>
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
    let editingOwnModelId = null;
    const authHeaders = () => ({ Authorization: `Bearer ${$("token").value.trim()}` });
    function friendlyError(data, status) {
      const detail = data && typeof data === "object" ? data.detail : data;
      if (typeof detail === "string") {
        if (status === 401) return "Your session expired. Please log in again.";
        if (status === 403) return "This action is only available to admin accounts.";
        if (status === 404) return "We couldn't find that model.";
        return detail;
      }
      if (detail && typeof detail === "object") {
        if (detail.message) return detail.message;
        if (detail.title) return `${detail.title}${detail.explanation ? `: ${detail.explanation}` : ""}`;
      }
      if (status === 401) return "Your session expired. Please log in again.";
      if (status === 403) return "This action is only available to admin accounts.";
      if (status === 422) return "Please check your model details and try again.";
      if (status >= 500) return "The model service is temporarily unavailable. Please try again.";
      return "Request failed. Please try again.";
    }
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(friendlyError(data, res.status));
      return data;
    }
    function show(value) {
      $("result").textContent = typeof value === "string" ? value : "Action completed successfully.";
    }
    function hydrateTokenFromUrl() {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token") || sessionStorage.getItem("zta_token");
      if (token) {
        $("token").value = token;
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        window.location.href = "/login?next=/dashboard/models";
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
      $("scanBtn").textContent = isAdmin ? "Assess And Register" : "Add Owned Model";
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
            <div class="card-title"><strong>${m.name}</strong><div class="card-meta">#${m.id} · ${m.model_type} · ${provider}</div></div>
            <span class="badge ${statusClass(m)}">${badge}</span>
          </div>
          <div class="card-desc">${m.description || "No description yet."}</div>
          <div class="card-badges">
            <span class="badge">trust ${trust}</span>
            <span class="badge">risk ${risk}</span>
            <span class="badge">${m.sensitivity_level} sensitivity</span>
            <span class="badge ${runtimeReady ? "protected" : "inactive"}">${runtimeText}</span>
          </div>
          ${runtimeReady ? "" : `<div class="runtime-hint">${runtime?.message || "Runtime configuration is incomplete."} ${runtime?.next_step || ""}</div>`}
          ${isAdmin ? `<div class="card-actions"><button onclick="rescanModel(${m.id})">Assess Posture</button>${m.is_active ? `<button class="danger" onclick="deactivateModel(${m.id})">Deactivate</button>` : ""}</div>` : (m.owner_user_id ? `<div class="card-actions"><button onclick="editOwnModel(${m.id})">Configure</button><button class="danger" onclick="deleteOwnModel(${m.id})">Delete</button></div>` : "")}
        </article>`;
      }).join("") || `<div class="no-content">No models are available yet. Add an owned model from the form.</div>`;
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
      show(isAdmin ? "Assessing model posture and registering it..." : "Adding owned model endpoint...");
      try {
        const body = payload();
        const path = isAdmin
          ? `${api}/assessment/scan`
          : editingOwnModelId
            ? `${api}/models/my/${editingOwnModelId}`
            : `${api}/models/my`;
        const method = editingOwnModelId ? "PATCH" : "POST";
        if (!isAdmin) {
          delete body.source_url;
          body.visibility = $("visibility").value;
        }
        const data = await request(path, {
          method,
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        show(data);
        editingOwnModelId = null;
        $("scanBtn").textContent = isAdmin ? "Assess And Register" : "Add Owned Model";
        for (const id of ["name", "provider_name", "hf_model_id", "source_url", "endpoint", "description"]) $(id).value = "";
        $("model_type").value = "huggingface";
        $("visibility").value = "private";
        await loadModels();
      } catch (err) {
        show(err?.message || "Model onboarding failed. Please try again.");
      } finally {
        $("scanBtn").disabled = false;
      }
    }
    async function deactivateModel(id) {
      if (!confirm("Deactivate this model from the registry? Existing history stays intact.")) return;
      await request(`${api}/models/${id}`, { method: "DELETE", headers: authHeaders() });
      await loadModels();
    }
    async function deleteOwnModel(id) {
      if (!confirm("Delete this owned model? Existing history stays intact.")) return;
      await request(`${api}/models/my/${id}`, { method: "DELETE", headers: authHeaders() });
      await loadModels();
    }
    function editOwnModel(id) {
      const model = models.find((item) => Number(item.id) === Number(id));
      if (!model || isAdmin) return;
      editingOwnModelId = id;
      $("name").value = model.name || "";
      $("model_type").value = String(model.model_type || "custom_api").toLowerCase();
      $("provider_name").value = model.provider_name || "";
      $("hf_model_id").value = model.hf_model_id || "";
      $("source_url").value = "";
      $("endpoint").value = model.endpoint || "";
      $("visibility").value = model.visibility === "shared" ? "shared" : "private";
      $("description").value = model.description || "";
      $("scanBtn").textContent = "Save Configuration";
      show(`Configuring ${model.name}. Changes will mark readiness as pending until reassessed.`);
      $("addPanel").scrollIntoView({ behavior: "smooth", block: "start" });
    }
    async function rescanModel(id) {
      show(`Rescanning model ${id}...`);
      const data = await request(`${api}/assessment/${id}/scan`, { method: "POST", headers: authHeaders() });
      show(data);
      await loadModels();
    }
    function clearForm(resetEdit = true) {
      for (const id of ["name", "provider_name", "hf_model_id", "source_url", "endpoint", "description"]) $(id).value = "";
      $("model_type").value = "huggingface";
      $("visibility").value = "private";
      if (resetEdit) {
        editingOwnModelId = null;
        $("scanBtn").textContent = isAdmin ? "Assess And Register" : "Add Owned Model";
      }
      show("Ready to add a model.");
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
      try { await refreshAll(); } catch (err) { show(err?.message || "Refresh failed. Please try again."); }
      finally { $("refreshBtn").disabled = false; }
    });
    window.deactivateModel = deactivateModel;
    window.deleteOwnModel = deleteOwnModel;
    window.editOwnModel = editOwnModel;
    window.rescanModel = rescanModel;
    hydrateTokenFromUrl();
    if ($("token").value.trim()) refreshAll().catch((err) => show(err?.message || "We couldn't load model data."));
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
