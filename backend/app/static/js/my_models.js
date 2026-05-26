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