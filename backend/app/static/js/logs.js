const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    const authHeaders = () => ({ Authorization: `Bearer ${$("token").value.trim()}` });
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    function hydrateTokenFromUrl() {
      const params = new URLSearchParams(window.location.search);
      const token = params.get("token") || sessionStorage.getItem("zta_token");
      if (token) {
        $("token").value = token;
        window.history.replaceState({}, document.title, window.location.pathname);
      } else {
        window.location.href = "/login?next=/logs";
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
      const username = profile.user?.username || "";
      $("roleBadge").textContent = username ? `${username} · my audit trail` : "my audit trail";
    }
    async function loadMetrics() {
      const data = await request(`${api}/monitoring/metrics`, { headers: authHeaders() });
      $("totalRequests").textContent = data.total_requests ?? 0;
      $("blockedRequests").textContent = data.blocked_requests ?? 0;
      $("challengedRequests").textContent = data.challenged_requests ?? 0;
      $("blockRate").textContent = `${data.block_rate ?? 0}%`;
    }
    async function loadLogs() {
      const params = new URLSearchParams();
      params.set("limit", $("limit").value);
      if ($("decision").value) params.set("decision", $("decision").value);
      if ($("modelId").value) params.set("model_id", $("modelId").value);
      const path = `${api}/monitoring/logs?${params.toString()}`;
      const data = await request(path, { headers: authHeaders() });
      const rows = data.logs || [];
      $("logs").innerHTML = rows.map((log) => {
        const trace = log.decision_trace || {};
        const snapshot = log.decision_input_snapshot || {};
        const title = `${log.model_name || "Model " + log.model_id} — ${log.username || "user " + log.user_id}`;
        return `<article class="card">
          <div class="card-head">
            <div class="card-title-wrap"><strong>${title}</strong><div class="card-meta">${log.timestamp || ""} · prompt hash ${log.prompt_hash || ""}</div></div>
            <span class="badge ${log.decision}">${log.decision}</span>
          </div>
          <div class="score-row">
            <span class="badge">security ${Number(log.security_score || 0).toFixed(3)}</span>
            <span class="badge">prompt ${Number(log.prompt_risk_score || 0).toFixed(3)}</span>
            <span class="badge">output ${Number(log.output_risk_score || 0).toFixed(3)}</span>
            <span class="badge">${Number(log.latency_ms || 0).toFixed(1)} ms</span>
            <span class="badge">${log.secure_mode_enabled ? "secure mode" : "standard mode"}</span>
          </div>
          <div class="card-reason">${log.reason || "No decision reason captured."}</div>
          <pre>${JSON.stringify({ trace, snapshot }, null, 2)}</pre>
        </article>`;
      }).join("") || `<div class="card"><strong>No logs yet.</strong><div class="card-reason">Run a pre-screen or safe inference request to generate audit events.</div></div>`;
    }
    async function refreshAll() {
      await loadRole();
      await Promise.all([loadMetrics(), loadLogs()]);
    }
    $("loginBtn").addEventListener("click", login);
    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      window.location.href = "/login";
    });
    $("refreshBtn").addEventListener("click", async () => {
      $("refreshBtn").disabled = true;
      try { await refreshAll(); } catch (err) { $("logs").innerHTML = `<pre>${String(err.message || err)}</pre>`; }
      finally { $("refreshBtn").disabled = false; }
    });
    hydrateTokenFromUrl();
    if ($("token").value.trim()) refreshAll().catch((err) => { $("logs").innerHTML = `<pre>${String(err.message || err)}</pre>`; });