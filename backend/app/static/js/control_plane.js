const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    let isAdmin = false;
    let controlsCache = [];
    let rulesCache = [];
    let clientsCache = [];
    let editingControlId = null;
    let editingRuleId = null;
    let editingClientId = null;
    const authHeaders = () => ({ Authorization: `Bearer ${$("token").value.trim()}` });
    const csv = (value) => value.split(",").map((x) => x.trim()).filter(Boolean);
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    function hydrateSession() {
      const token = sessionStorage.getItem("zta_token");
      if (!token) {
        window.location.href = "/login?next=/dashboard/policy";
        return;
      }
      $("token").value = token;
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
    async function loadControls() {
      const rows = await request(`${api}/security/controls?include_disabled=true`, { headers: authHeaders() });
      controlsCache = rows;
      $("controlsList").innerHTML = rows.map((c) => `<article class="card">
        <div class="card-head">
          <div><span class="card-id">${c.control_id}</span> <span class="card-name">${c.name}</span></div>
          <span class="badge ${c.enabled ? c.coverage : "disabled"}">${c.enabled ? c.coverage : "disabled"}</span>
        </div>
        <div class="card-desc">${c.description || ""}</div>
        <div class="card-caps">${(c.mapped_capabilities || []).join(", ")}</div>
        ${isAdmin ? `<div class="card-actions"><button onclick="editControl(${c.id})">Edit</button>${c.enabled ? `<button class="danger" onclick="disableControl(${c.id})">Disable</button>` : ""}</div>` : ""}
      </article>`).join("");
    }
    async function loadRules() {
      const rows = await request(`${api}/security/detection-rules?include_disabled=true`, { headers: authHeaders() });
      rulesCache = rows;
      $("rulesList").innerHTML = rows.map((r) => `<article class="card">
        <div class="card-head">
          <div><span class="card-id">#${r.id}</span> <span class="card-name">${r.name}</span></div>
          <span class="badge ${r.enabled ? r.severity : "disabled"}">${r.enabled ? r.decision : "disabled"}</span>
        </div>
        <div class="card-desc">${r.target} ${r.match_type}: <code style="font-family:var(--mono);font-size:11px">${r.pattern}</code></div>
        <div class="card-desc">${r.description || ""}</div>
        ${isAdmin ? `<div class="card-actions"><button onclick="editRule(${r.id})">Edit</button>${r.enabled ? `<button class="danger" onclick="disableRule(${r.id})">Disable</button>` : ""}</div>` : ""}
      </article>`).join("");
    }
    async function loadClients() {
      if (!isAdmin) return;
      const rows = await request(`${api}/firewall/clients`, { headers: authHeaders() });
      clientsCache = rows;
      $("clientsList").innerHTML = rows.map((c) => `<article class="card">
        <div class="card-head">
          <div><span class="card-id">${c.client_id}</span> <span class="card-name">${c.name}</span></div>
          <span class="badge ${c.is_active ? "strong" : "disabled"}">${c.is_active ? "active" : "inactive"}</span>
        </div>
        <div class="card-desc">Rate ${c.rate_limit}/${c.rate_window_seconds}s · trust ${Number(c.trust_score).toFixed(2)} · signing ${c.require_signature ? "required" : "optional"}</div>
        ${c.api_key ? `<pre>New API key: ${c.api_key}</pre>` : ""}
        <div class="card-actions">
          <button onclick="editClient('${c.client_id}')">Edit</button>
          <button class="danger" onclick="toggleClient('${c.client_id}', ${c.is_active ? "false" : "true"})">${c.is_active ? "Disable" : "Enable"}</button>
        </div>
      </article>`).join("") || `<article class="card"><span class="card-name">No gateway clients yet.</span></article>`;
    }
    async function refreshAll() { await loadRole(); await Promise.all([loadControls(), loadRules(), loadClients()]); }
    async function saveControl() {
      const body = {
        control_id: $("control_id").value,
        name: $("control_name").value,
        description: $("control_description").value,
        coverage: $("control_coverage").value,
        status: $("control_status").value,
        control_family: $("control_family").value,
        mapped_capabilities: csv($("control_capabilities").value),
        recommended_actions: csv($("control_actions").value),
        enabled: true
      };
      const path = editingControlId ? `${api}/security/controls/${editingControlId}` : `${api}/security/controls`;
      await request(path, { method: editingControlId ? "PATCH" : "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) });
      editingControlId = null;
      $("saveControl").textContent = "Save Control";
      await loadControls();
    }
    async function saveRule() {
      const body = {
        name: $("rule_name").value,
        description: $("rule_description").value,
        target: $("rule_target").value,
        match_type: $("rule_match_type").value,
        pattern: $("rule_pattern").value,
        severity: $("rule_severity").value,
        decision: $("rule_decision").value,
        risk_delta: Number($("rule_risk_delta").value),
        enabled: true
      };
      const path = editingRuleId ? `${api}/security/detection-rules/${editingRuleId}` : `${api}/security/detection-rules`;
      await request(path, { method: editingRuleId ? "PATCH" : "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) });
      editingRuleId = null;
      $("saveRule").textContent = "Save Rule";
      await loadRules();
    }
    async function saveClient() {
      const body = {
        client_id: $("fw_client_id").value,
        name: $("fw_name").value,
        api_key: $("fw_api_key").value || null,
        rate_limit: Number($("fw_rate_limit").value),
        rate_window_seconds: Number($("fw_rate_window").value),
        trust_score: Number($("fw_trust").value),
        require_signature: $("fw_require_signature").value === "true",
        hmac_secret: $("fw_hmac_secret").value || null,
        is_active: true
      };
      const path = editingClientId ? `${api}/firewall/clients/${encodeURIComponent(editingClientId)}` : `${api}/firewall/clients`;
      if (editingClientId) delete body.client_id;
      const saved = await request(path, { method: editingClientId ? "PATCH" : "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) });
      editingClientId = null;
      $("fw_client_id").disabled = false;
      $("saveClient").textContent = "Save Client";
      await loadClients();
      if (saved.api_key) $("clientsList").insertAdjacentHTML("afterbegin", `<article class="card"><span class="card-name">Copy this key now</span><pre>${saved.api_key}</pre></article>`);
    }
    function editControl(id) {
      const c = controlsCache.find((item) => item.id === id);
      if (!c) return;
      editingControlId = id;
      $("control_id").value = c.control_id;
      $("control_name").value = c.name;
      $("control_description").value = c.description || "";
      $("control_coverage").value = c.coverage;
      $("control_status").value = c.status;
      $("control_family").value = c.control_family || "";
      $("control_capabilities").value = (c.mapped_capabilities || []).join(", ");
      $("control_actions").value = (c.recommended_actions || []).join(", ");
      $("saveControl").textContent = "Update Control";
    }
    function editRule(id) {
      const r = rulesCache.find((item) => item.id === id);
      if (!r) return;
      editingRuleId = id;
      $("rule_name").value = r.name;
      $("rule_description").value = r.description || "";
      $("rule_target").value = r.target;
      $("rule_match_type").value = r.match_type;
      $("rule_pattern").value = r.pattern;
      $("rule_severity").value = r.severity;
      $("rule_decision").value = r.decision;
      $("rule_risk_delta").value = r.risk_delta;
      $("saveRule").textContent = "Update Rule";
    }
    function editClient(clientId) {
      const c = clientsCache.find((item) => item.client_id === clientId);
      if (!c) return;
      editingClientId = clientId;
      $("fw_client_id").value = c.client_id;
      $("fw_client_id").disabled = true;
      $("fw_name").value = c.name;
      $("fw_api_key").value = "";
      $("fw_rate_limit").value = c.rate_limit;
      $("fw_rate_window").value = c.rate_window_seconds;
      $("fw_trust").value = c.trust_score;
      $("fw_require_signature").value = String(c.require_signature);
      $("fw_hmac_secret").value = "";
      $("saveClient").textContent = "Update Client";
    }
    async function disableControl(id) { await request(`${api}/security/controls/${id}`, { method: "DELETE", headers: authHeaders() }); await loadControls(); }
    async function disableRule(id) { await request(`${api}/security/detection-rules/${id}`, { method: "DELETE", headers: authHeaders() }); await loadRules(); }
    async function toggleClient(clientId, active) { await request(`${api}/firewall/clients/${encodeURIComponent(clientId)}`, { method: "PATCH", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify({ is_active: active }) }); await loadClients(); }
    async function simulate() {
      const body = { model_id: Number($("sim_model_id").value), prompt: $("sim_prompt").value };
      const data = await request(`${api}/security/policy/simulate`, { method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: JSON.stringify(body) });
      $("simResult").textContent = JSON.stringify(data, null, 2);
    }
    document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
      tab.classList.add("active");
      const key = tab.dataset.tab;
      $("controlsTab").style.display = key === "controls" ? "block" : "none";
      $("rulesTab").style.display = key === "rules" ? "block" : "none";
      $("simulationTab").style.display = key === "simulation" ? "block" : "none";
      $("firewallTab").style.display = key === "firewall" ? "block" : "none";
      $("controlForm").style.display = key === "controls" ? "block" : "none";
      $("ruleForm").style.display = key === "rules" ? "block" : "none";
      $("clientForm").style.display = key === "firewall" ? "block" : "none";
      $("formPanel").style.display = ["controls", "rules", "firewall"].includes(key) && isAdmin ? "block" : "none";
      const titles = { controls: "Add Control", rules: "Add Detection Rule", firewall: "Add Gateway Client" };
      $("formTitle").textContent = titles[key] || "Add Control";
    }));
    $("loginBtn").addEventListener("click", login);
    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      window.location.href = "/login";
    });
    $("saveControl").addEventListener("click", saveControl);
    $("saveRule").addEventListener("click", saveRule);
    $("saveClient").addEventListener("click", saveClient);
    $("simulateBtn").addEventListener("click", simulate);
    window.disableControl = disableControl;
    window.disableRule = disableRule;
    window.editControl = editControl;
    window.editRule = editRule;
    window.editClient = editClient;
    window.toggleClient = toggleClient;
    hydrateSession();
    refreshAll().catch((err) => {
      $("simResult").textContent = String(err.message || err);
    });