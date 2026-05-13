from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS

MY_MODELS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>My Models — Zero Trust AI Gateway</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; }
    body { margin: 0; }
    .shell { padding: 20px clamp(12px, 3vw, 32px) 40px; max-width: 960px; }
    .eyebrow { font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: .1em; color: #93c5fd; margin-bottom: 6px; }
    h1 { margin: 0 0 6px; font-size: clamp(26px, 5vw, 48px); }
    p.sub { margin: 0 0 20px; font-size: 14px; }
    .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 20px; }
    .limit-bar { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 14px; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.05); font-size: 13px; }
    .limit-dots { display: flex; gap: 6px; }
    .limit-dot { width: 14px; height: 14px; border-radius: 50%; background: rgba(255,255,255,.15); }
    .limit-dot.used { background: #22d3ee; box-shadow: 0 0 8px rgba(34,211,238,.5); }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-bottom: 24px; }
    .model-card { border: 1px solid rgba(255,255,255,.12); border-radius: 16px; padding: 16px; background: rgba(255,255,255,.04); transition: border-color .2s, box-shadow .2s; }
    .model-card:hover { border-color: rgba(34,211,238,.4); box-shadow: 0 0 20px rgba(34,211,238,.1); }
    .model-name { font-weight: 700; font-size: 15px; margin-bottom: 4px; word-break: break-word; }
    .model-meta { font-size: 12px; color: #9ca8bd; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
    .badge { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; padding: 3px 8px; border-radius: 999px; border: 1px solid rgba(255,255,255,.15); background: rgba(255,255,255,.06); }
    .badge.openai { border-color: rgba(74,222,128,.4); color: #86efac; }
    .badge.huggingface { border-color: rgba(251,191,36,.4); color: #fde68a; }
    .badge.local, .badge.ollama { border-color: rgba(167,139,250,.4); color: #c4b5fd; }
    .badge.custom_api { border-color: rgba(251,113,133,.4); color: #fda4af; }
    .badge.private { border-color: rgba(255,255,255,.15); color: #9ca8bd; }
    .badge.shared { border-color: rgba(34,211,238,.35); color: #67e8f9; }
    .badge.pending { color: #fbbf24; }
    .badge.ready { color: #34d399; }
    .model-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .btn { border: 1px solid rgba(255,255,255,.15); border-radius: 999px; padding: 7px 14px; background: rgba(255,255,255,.06); color: #f8fbff; cursor: pointer; font-size: 12px; }
    .btn:hover { border-color: rgba(34,211,238,.5); background: rgba(34,211,238,.1); }
    .btn.danger { border-color: rgba(251,113,133,.4); color: #fda4af; }
    .btn.danger:hover { background: rgba(251,113,133,.12); }
    .empty-state { text-align: center; padding: 48px 20px; border: 1px dashed rgba(255,255,255,.15); border-radius: 20px; }
    .empty-icon { font-size: 40px; margin-bottom: 12px; opacity: .6; }
    .empty-state h3 { margin: 0 0 8px; font-size: 18px; }
    .empty-state p { margin: 0; font-size: 13px; color: #9ca8bd; }
    .add-form { border: 1px solid rgba(255,255,255,.12); border-radius: 16px; padding: 18px; background: rgba(255,255,255,.03); margin-bottom: 20px; }
    .add-form h3 { margin: 0 0 14px; font-size: 15px; color: #93c5fd; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
    label { display: grid; gap: 5px; font-size: 12px; color: #9ca8bd; }
    input, select, textarea { border: 1px solid rgba(255,255,255,.15); border-radius: 10px; background: rgba(0,0,0,.3); color: #f8fbff; padding: 9px 11px; font: inherit; width: 100%; }
    input:focus, select:focus { border-color: rgba(34,211,238,.6); outline: none; box-shadow: 0 0 0 3px rgba(34,211,238,.1); }
    .form-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
    .btn-primary { border: 1px solid rgba(34,211,238,.4); border-radius: 999px; padding: 10px 20px; background: linear-gradient(135deg, rgba(34,211,238,.2), rgba(168,85,247,.2)); color: #f8fbff; cursor: pointer; font-weight: 700; font-size: 13px; }
    .btn-primary:hover { border-color: rgba(34,211,238,.7); background: linear-gradient(135deg, rgba(34,211,238,.3), rgba(168,85,247,.3)); }
    .btn-primary:disabled { opacity: .45; cursor: not-allowed; }
    .notice { padding: 12px 16px; border-radius: 12px; font-size: 13px; margin-bottom: 14px; }
    .notice.error { border: 1px solid rgba(251,113,133,.4); background: rgba(251,113,133,.08); color: #fda4af; }
    .notice.success { border: 1px solid rgba(52,211,153,.4); background: rgba(52,211,153,.08); color: #6ee7b7; }
    .notice.warn { border: 1px solid rgba(251,191,36,.4); background: rgba(251,191,36,.08); color: #fde68a; }
    @media (max-width: 540px) {
      .form-grid { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
<main class="shell">
  <div class="eyebrow">Model Management</div>
  <h1>My Models</h1>
  <p class="sub">Add and manage your own AI model connections. Maximum 3 active models per account.</p>

  <div id="notice" style="display:none" class="notice"></div>

  <div class="limit-bar">
    <div class="limit-dots" id="limitDots">
      <div class="limit-dot"></div>
      <div class="limit-dot"></div>
      <div class="limit-dot"></div>
    </div>
    <span id="limitText">Loading…</span>
  </div>

  <div class="add-form" id="addForm">
    <h3>Add a Model</h3>
    <div class="form-grid">
      <label>Name <input id="mName" placeholder="My GPT-4o" /></label>
      <label>Provider
        <select id="mType">
          <option value="openai">OpenAI</option>
          <option value="huggingface">HuggingFace</option>
          <option value="ollama">Ollama</option>
          <option value="local">Local</option>
          <option value="custom_api">Custom API</option>
        </select>
      </label>
      <label>Endpoint URL <input id="mEndpoint" placeholder="https://api.openai.com/v1/..." /></label>
      <label>Provider Name <input id="mProvider" placeholder="OpenAI, Mistral, etc." /></label>
      <label>HuggingFace Model ID <input id="mHfId" placeholder="mistralai/Mistral-7B-v0.1" /></label>
      <label>Visibility
        <select id="mVisibility">
          <option value="private">Private (only me)</option>
          <option value="shared">Shared (all users)</option>
        </select>
      </label>
    </div>
    <div style="margin-top:10px">
      <label>Description <textarea id="mDesc" rows="2" placeholder="Optional short description" style="resize:vertical"></textarea></label>
    </div>
    <div class="form-actions">
      <button class="btn-primary" id="addBtn">Add Model</button>
      <button class="btn" id="cancelBtn" style="display:none">Cancel</button>
    </div>
  </div>

  <div id="modelGrid" class="grid">
    <div style="grid-column:1/-1;text-align:center;padding:20px;color:#9ca8bd;font-size:13px">Loading…</div>
  </div>
</main>
<script>
  const api = "/api/v1";
  const token = sessionStorage.getItem("zta_token");
  if (!token) location.href = "/login?next=/my-models";
  const headers = () => ({ Authorization: `Bearer ${token}`, "Content-Type": "application/json" });
  const $ = id => document.getElementById(id);

  const MODEL_LIMIT = 3;
  let models = [];

  function showNotice(msg, type = "error") {
    const el = $("notice");
    el.textContent = msg;
    el.className = `notice ${type}`;
    el.style.display = "";
    setTimeout(() => { el.style.display = "none"; }, 6000);
  }

  function updateLimitBar(count) {
    const dots = document.querySelectorAll(".limit-dot");
    dots.forEach((d, i) => d.classList.toggle("used", i < count));
    $("limitText").textContent = `${count} / ${MODEL_LIMIT} models used`;
    const addBtn = $("addBtn");
    if (count >= MODEL_LIMIT) {
      addBtn.disabled = true;
      addBtn.textContent = "Limit reached — delete a model to add another";
    } else {
      addBtn.disabled = false;
      addBtn.textContent = "Add Model";
    }
  }

  function renderModels(list) {
    const grid = $("modelGrid");
    if (!list.length) {
      grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">◎</div>
        <h3>No models yet</h3>
        <p>Add your first model above to start using it in Gateway Chat.</p>
      </div>`;
      return;
    }
    const typeColor = { openai: "openai", huggingface: "huggingface", ollama: "ollama", local: "local", custom_api: "custom_api" };
    grid.innerHTML = list.map(m => `
      <div class="model-card">
        <div class="model-name">${escHtml(m.name)}</div>
        <div class="model-meta">
          <span class="badge ${typeColor[m.model_type] || ''}">${escHtml(m.model_type || "—")}</span>
          <span class="badge ${m.visibility || 'private'}">${m.visibility || "private"}</span>
          <span class="badge ${m.scan_status === 'pending' ? 'pending' : 'ready'}">${escHtml(m.scan_status || "pending")}</span>
        </div>
        ${m.endpoint ? `<div style="font-size:11px;color:#9ca8bd;word-break:break-all;margin-bottom:6px">${escHtml(m.endpoint)}</div>` : ""}
        ${m.description ? `<div style="font-size:12px;color:#9ca8bd;margin-bottom:6px">${escHtml(m.description)}</div>` : ""}
        <div class="model-actions">
          <button class="btn danger" onclick="deleteModel(${m.id})">Remove</button>
        </div>
      </div>
    `).join("");
  }

  function escHtml(s) {
    return String(s || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  }

  async function loadModels() {
    try {
      const res = await fetch(`${api}/models/my`, { headers: headers() });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to load");
      models = await res.json();
      const active = models.filter(m => m.is_active !== false);
      renderModels(active);
      updateLimitBar(active.length);
    } catch (e) {
      showNotice(e.message || "Could not load models.");
    }
  }

  async function deleteModel(id) {
    if (!confirm("Remove this model? It will no longer appear in Chat.")) return;
    try {
      const res = await fetch(`${api}/models/my/${id}`, { method: "DELETE", headers: headers() });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to delete");
      showNotice("Model removed.", "success");
      await loadModels();
    } catch (e) {
      showNotice(e.message || "Could not remove model.");
    }
  }

  $("addBtn").addEventListener("click", async () => {
    const name = $("mName").value.trim();
    if (!name) { showNotice("Name is required."); return; }
    const body = {
      name,
      description: $("mDesc").value.trim() || null,
      model_type: $("mType").value,
      endpoint: $("mEndpoint").value.trim() || null,
      provider_name: $("mProvider").value.trim() || null,
      hf_model_id: $("mHfId").value.trim() || null,
      visibility: $("mVisibility").value,
    };
    $("addBtn").disabled = true;
    try {
      const res = await fetch(`${api}/models/my`, { method: "POST", headers: headers(), body: JSON.stringify(body) });
      const data = await res.json();
      if (!res.ok) {
        const msg = typeof data.detail === "object" ? data.detail.message : (data.detail || "Failed to add model");
        showNotice(msg, res.status === 403 ? "warn" : "error");
        return;
      }
      showNotice(`Model "${data.name}" added successfully.`, "success");
      ["mName","mDesc","mEndpoint","mProvider","mHfId"].forEach(id => $(id).value = "");
      await loadModels();
    } catch (e) {
      showNotice(e.message || "Could not add model.");
    } finally {
      $("addBtn").disabled = false;
    }
  });

  loadModels();
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
