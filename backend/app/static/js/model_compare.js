const api = "/api/v1";
  const token = sessionStorage.getItem("zta_token");
  if (!token) location.href = "/login?next=/dashboard/models/compare";
  const H = () => ({ Authorization: "Bearer " + token, "Content-Type": "application/json" });

  /* ---- helpers ---- */
  function esc(v) {
    return String(v ?? "").replace(/[&<>"']/g,
      c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
  }
  function riskClass(r) {
    return r < 0.35 ? "risk-low" : r < 0.65 ? "risk-mid" : "risk-high";
  }
  function decisionBadgeClass(d) {
    const v = String(d||"").toLowerCase();
    return v.includes("block") ? "badge-block" : v.includes("challenge") ? "badge-challenge" : "badge-allow";
  }
  function decisionLabel(d) {
    const v = String(d||"").toLowerCase();
    return v.includes("block") ? "Block" : v.includes("challenge") ? "Challenge" : "Allow";
  }
  function confPips(conf) {
    const v = String(conf||"").toLowerCase();
    const cls = v === "high" ? "on-high" : v === "medium" ? "on-medium" : "on-low";
    const count = v === "high" ? 3 : v === "medium" ? 2 : 1;
    return Array.from({length:3}, (_,i) =>
      `<span class="pip ${i < count ? cls : ''}"></span>`).join("");
  }
  function secToConf(sec) {
    const s = Number(sec || 0);
    return s >= 0.7 ? "high" : s >= 0.4 ? "medium" : "low";
  }

  /* ---- mock data ---- */
  const MODEL_PROFILES = [
    { name:"GPT-4o-mini",     baseRisk:0.14 },
    { name:"Claude-3-Haiku",  baseRisk:0.21 },
    { name:"Llama-3-8B",      baseRisk:0.44 },
    { name:"Mistral-7B",      baseRisk:0.37 },
    { name:"Gemma-2B",        baseRisk:0.58 },
    { name:"Phi-3-mini",      baseRisk:0.27 },
    { name:"Falcon-7B",       baseRisk:0.62 },
    { name:"MPT-7B",          baseRisk:0.51 },
  ];
  function generateMock(ids, prompt) {
    const snippet = prompt.substring(0, 50);
    return ids.map((id) => {
      const p = MODEL_PROFILES[(id - 1) % MODEL_PROFILES.length] || { name:`Model ${id}`, baseRisk: 0.4 };
      const risk = Math.min(0.97, Math.max(0.03, p.baseRisk + (Math.random() - 0.5) * 0.18));
      const decision = risk < 0.35 ? "allow" : risk < 0.65 ? "challenge" : "block";
      const sec  = parseFloat((1 - risk + (Math.random() - 0.5) * 0.1).toFixed(3));
      const conf = secToConf(sec);
      return {
        model_id:       id,
        model_name:     p.name,
        effective_risk: parseFloat(risk.toFixed(3)),
        decision,
        confidence:     conf,
        security_score: Math.min(1, Math.max(0, sec)),
        output:         `[Simulated] ${p.name} responded to: "${snippet}..." — output passed through gateway policy engine.`,
        explanation:    `Risk ${risk.toFixed(2)}. ${decision === "allow" ? "Content safe, no policy violations detected." : decision === "challenge" ? "Content requires additional verification before delivery." : "Content blocked — violates output safety policy."}`
      };
    });
  }

  /* ---- normalise API rows ---- */
  function normalise(row) {
    const risk = Number(row.effective_risk ?? row.risk ?? 0);
    const sec  = Number(row.security_score ?? (1 - risk));
    return {
      model_id:       row.model_id,
      model_name:     row.model_name || `Model ${row.model_id}`,
      effective_risk: parseFloat(risk.toFixed(3)),
      decision:       row.decision || "allow",
      confidence:     row.confidence || secToConf(sec),
      security_score: parseFloat(sec.toFixed(3)),
      output:         row.output || "",
      explanation:    row.explanation || row.reason || ""
    };
  }

  /* ---- view toggle ---- */
  let currentView = "cards";
  function setView(v) {
    currentView = v;
    document.getElementById("cardView").style.display  = v === "cards" ? "grid" : "none";
    document.getElementById("tableView").style.display = v === "table" ? "block" : "none";
    document.getElementById("btnCards").classList.toggle("active", v === "cards");
    document.getElementById("btnTable").classList.toggle("active", v === "table");
  }

  /* ---- render ---- */
  function renderCards(rows, safestId, riskiestId) {
    const container = document.getElementById("cardView");
    container.innerHTML = rows.map((r, i) => {
      const isSafest   = r.model_id === safestId;
      const isRiskiest = r.model_id === riskiestId;
      const outline    = isSafest ? "safest-outline" : isRiskiest ? "riskiest-outline" : "";
      const pct        = Math.round(r.effective_risk * 100);
      return `
        <article class="model-card ${outline}" style="animation-delay:${i * 60}ms">
          <div class="card-header">
            <strong>${esc(r.model_name)}</strong>
            <span class="decision-badge ${decisionBadgeClass(r.decision)}">${decisionLabel(r.decision)}</span>
            ${isSafest   ? `<span class="label-tag" style="color:var(--good)!important;border-color:rgba(52,211,153,.35)!important">safest</span>` : ""}
            ${isRiskiest ? `<span class="label-tag" style="color:var(--bad)!important;border-color:rgba(251,113,133,.35)!important">riskiest</span>` : ""}
          </div>
          <div class="risk-section">
            <div class="risk-header">
              <span>Risk Score</span>
              <span class="risk-val" style="color:${pct<35?"var(--good)":pct<65?"var(--warn)":"var(--bad)"}">${r.effective_risk.toFixed(3)}</span>
            </div>
            <div class="risk-track">
              <div class="risk-fill ${riskClass(r.effective_risk)}" data-pct="${pct}" style="width:0%"></div>
            </div>
          </div>
          <div class="confidence-row">
            <span class="conf-label">Confidence</span>
            <div class="conf-pips">${confPips(r.confidence)}</div>
            <span class="conf-label">${r.confidence}</span>
          </div>
          <div class="scores-row">
            <div class="score-box">
              <div class="score-label">Security Score</div>
              <div class="score-val" style="color:${r.security_score>=0.7?"var(--good)":r.security_score>=0.4?"var(--warn)":"var(--bad)"}">${r.security_score.toFixed(3)}</div>
            </div>
            <div class="score-box">
              <div class="score-label">Model ID</div>
              <div class="score-val" style="color:var(--muted)">#${r.model_id}</div>
            </div>
          </div>
          <div class="response-box">${esc(r.output || "No output")}</div>
          ${r.explanation ? `<div class="explanation">${esc(r.explanation)}</div>` : ""}
        </article>`;
    }).join("");

    /* animate risk bars after paint */
    requestAnimationFrame(() => requestAnimationFrame(() => {
      container.querySelectorAll(".risk-fill[data-pct]").forEach(el => {
        el.style.width = el.dataset.pct + "%";
      });
    }));
  }

  function renderTable(rows, safestId, riskiestId) {
    const tbody = document.getElementById("tableBody");
    tbody.innerHTML = rows.map(r => {
      const pct = Math.round(r.effective_risk * 100);
      const fillCls = riskClass(r.effective_risk);
      const isSafest   = r.model_id === safestId;
      const isRiskiest = r.model_id === riskiestId;
      return `
        <tr>
          <td class="tbl-model">
            ${esc(r.model_name)}
            ${isSafest   ? `<span class="label-tag" style="margin-left:6px;color:var(--good)!important;border-color:rgba(52,211,153,.3)!important;font-size:10px!important">safest</span>` : ""}
            ${isRiskiest ? `<span class="label-tag" style="margin-left:6px;color:var(--bad)!important;border-color:rgba(251,113,133,.3)!important;font-size:10px!important">riskiest</span>` : ""}
          </td>
          <td><span class="decision-badge ${decisionBadgeClass(r.decision)}">${decisionLabel(r.decision)}</span></td>
          <td style="font-variant-numeric:tabular-nums;font-weight:700;color:${pct<35?"var(--good)":pct<65?"var(--warn)":"var(--bad)"}">${r.effective_risk.toFixed(3)}</td>
          <td><div class="tbl-risk-track"><div class="tbl-risk-fill ${fillCls}" data-pct="${pct}" style="width:0%"></div></div></td>
          <td><div class="conf-pips" style="display:flex;gap:3px">${confPips(r.confidence)}</div></td>
          <td style="font-variant-numeric:tabular-nums">${r.security_score.toFixed(3)}</td>
          <td class="tbl-output" title="${esc(r.output)}">${esc(r.output)}</td>
        </tr>`;
    }).join("");

    requestAnimationFrame(() => requestAnimationFrame(() => {
      tbody.querySelectorAll(".tbl-risk-fill[data-pct]").forEach(el => {
        el.style.width = el.dataset.pct + "%";
      });
    }));
  }

  function renderSummary(rows) {
    const sorted    = [...rows].sort((a,b) => a.effective_risk - b.effective_risk);
    const safest    = sorted[0];
    const riskiest  = sorted[sorted.length - 1];
    const avgRisk   = rows.reduce((s,r) => s + r.effective_risk, 0) / rows.length;
    const blocked   = rows.filter(r => String(r.decision||"").toLowerCase().includes("block")).length;
    const allowed   = rows.filter(r => String(r.decision||"").toLowerCase().includes("allow")).length;

    document.getElementById("sumSafest").textContent    = safest?.model_name || "—";
    document.getElementById("sumSafestRisk").textContent = `Risk ${safest?.effective_risk.toFixed(3) || "—"}`;
    document.getElementById("sumRiskiest").textContent  = riskiest?.model_name || "—";
    document.getElementById("sumRiskiestRisk").textContent = `Risk ${riskiest?.effective_risk.toFixed(3) || "—"}`;

    const avgEl = document.getElementById("sumAvgRisk");
    avgEl.textContent = avgRisk.toFixed(3);
    avgEl.style.color = avgRisk < 0.35 ? "var(--good)" : avgRisk < 0.65 ? "var(--warn)" : "var(--bad)";

    document.getElementById("sumCount").textContent     = rows.length;
    document.getElementById("sumDecisions").textContent = `${allowed} allowed · ${blocked} blocked`;
    document.getElementById("summarySection").style.display = "grid";

    return { safestId: safest?.model_id, riskiestId: riskiest?.model_id };
  }

  /* ---- run comparison ---- */
  async function runComparison() {
    const raw    = document.getElementById("modelIds").value;
    const prompt = document.getElementById("promptInput").value.trim();
    const ids    = raw.split(",").map(x => Number(x.trim())).filter(Boolean);
    if (!ids.length || !prompt) return;

    const btn = document.getElementById("runBtn");
    btn.disabled = true;
    document.getElementById("btnIcon").innerHTML = `<span class="spinner"></span>`;
    document.getElementById("btnTxt").textContent = "Comparing…";
    document.getElementById("runMeta").textContent = "";
    document.getElementById("summarySection").style.display = "none";
    document.getElementById("cardView").innerHTML =
      `<div class="placeholder" style="grid-column:1/-1">Running security comparison across ${ids.length} model${ids.length>1?"s":""}…</div>`;
    document.getElementById("tableBody").innerHTML = "";

    let rows = [];
    let usedMock = false;
    try {
      const res  = await fetch(`${api}/security/models/compare`, {
        method: "POST", headers: H(),
        body: JSON.stringify({ model_ids: ids, prompt, parameters: { temperature: 0.2, max_tokens: 700 } })
      });
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      rows = (data.results || []).map(normalise);
      if (!rows.length) throw new Error("empty");
    } catch {
      usedMock = true;
      rows = generateMock(ids, prompt);
    }

    const { safestId, riskiestId } = renderSummary(rows);
    renderCards(rows, safestId, riskiestId);
    renderTable(rows, safestId, riskiestId);

    const ts = new Date().toLocaleTimeString();
    document.getElementById("runMeta").textContent =
      `${rows.length} model${rows.length>1?"s":""} compared · ${ts}${usedMock ? " · simulated" : ""}`;

    btn.disabled = false;
    document.getElementById("btnIcon").textContent = "▶";
    document.getElementById("btnTxt").textContent  = "Compare Models";

    /* keep active view */
    setView(currentView);
  }

  document.getElementById("runBtn").addEventListener("click", runComparison);

  /* auto-run on load */
  window.addEventListener("DOMContentLoaded", () => {
    setTimeout(runComparison, 400);
  });