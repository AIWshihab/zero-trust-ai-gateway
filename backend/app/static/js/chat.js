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
    let sessionStats = { allowed: 0, challenged: 0, blocked: 0 };

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
    function showZTModal(decision, data) {
      const isBlock = decision === "BLOCK";
      const box = $("ztModalBox");
      box.className = `zt-modal ${isBlock ? "block" : "challenge"}`;
      $("ztModalIcon").textContent = isBlock ? "🚫" : "⚠️";
      $("ztModalTitle").textContent = isBlock ? "Request Blocked" : "Challenge Decision";
      const riskPct = data.prompt_risk_score != null ? `${Math.round(data.prompt_risk_score * 100)}%` : "—";
      const cls = isBlock ? "block" : "challenge";
      $("ztDecPill").textContent = decision;
      $("ztDecPill").className = `zt-risk-pill ${cls}`;
      $("ztRiskPill").textContent = `Risk: ${riskPct}`;
      $("ztRiskPill").className = `zt-risk-pill ${cls}`;
      const reason = data.explanation || data.reason || "";
      if (isBlock) {
        $("ztModalBody").textContent = reason
          ? `This request was blocked by the Zero Trust policy engine. Reason: ${reason}`
          : "This request was blocked by the Zero Trust policy engine. Your prompt risk score or security posture exceeded the block threshold.";
        $("ztModalOk").textContent = "Understood";
        $("ztModalOk").className = "zt-btn ok block-ok";
      } else {
        $("ztModalBody").textContent = reason
          ? `Challenge: ${reason} — The gateway allowed the request but risk has been recorded against your trust profile.`
          : "This prompt was flagged as potentially risky. It was allowed, but your behaviour pattern has been recorded. Repeated risky prompts will escalate to blocks.";
        $("ztModalOk").textContent = "Acknowledge";
        $("ztModalOk").className = "zt-btn ok";
      }
      $("ztModal").classList.remove("hidden");
    }

    function updateSessionStats(decision) {
      const d = String(decision || "").toLowerCase();
      if (d === "allow")     sessionStats.allowed++;
      else if (d === "block")     sessionStats.blocked++;
      else if (d === "challenge") sessionStats.challenged++;
      $("srAllowed").textContent   = sessionStats.allowed;
      $("srChallenged").textContent = sessionStats.challenged;
      $("srBlocked").textContent   = sessionStats.blocked;
      $("sessionRiskBar").classList.remove("hidden");
    }

    function setDecision(data) {
      const d = String(data.decision || "unknown").toUpperCase();
      $("decisionPill").textContent = d;
      $("decisionPill").className = `pill ${decisionClass(d)}`;
      const riskPct = data.prompt_risk_score != null ? `${Math.round(data.prompt_risk_score * 100)}%` : null;
      $("promptRisk").textContent = riskPct || "--";
      $("securityScore").textContent = data.security_score == null ? "--" : `${Math.round(data.security_score * 100)}%`;
      if (riskPct) {
        $("riskPill").textContent = `Risk ${riskPct}`;
        $("riskPill").className = `pill ${decisionClass(d)}`;
        $("riskPill").classList.remove("hidden");
      }
      const cls = d === "BLOCK" ? "bad" : d === "CHALLENGE" ? "warn" : "ready";
      $("decisionReason").className = `decision-box ${cls}`;
      $("decisionReason").innerHTML = `<b>${esc(d)}</b><small>${esc(data.explanation || data.reason || "Decision complete.")}</small>`;
      $("traceBox").textContent = JSON.stringify(data.decision_trace || data, null, 2);
      updateSessionStats(d);
      if (d === "BLOCK" || d === "CHALLENGE") showZTModal(d, data);
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

    $("ztModalOk").onclick = () => $("ztModal").classList.add("hidden");
    $("ztModal").addEventListener("click", (e) => { if (e.target === $("ztModal")) $("ztModal").classList.add("hidden"); });
    $("newBtn").onclick = () => { sessionStats = { allowed: 0, challenged: 0, blocked: 0 }; $("sessionRiskBar").classList.add("hidden"); $("riskPill").classList.add("hidden"); newChat(); };
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