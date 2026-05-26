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