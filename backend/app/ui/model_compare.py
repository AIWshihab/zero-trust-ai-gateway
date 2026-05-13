from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


MODEL_COMPARE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Model Security Comparison</title>
  <style>
    :root {
      color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui;
      --good:#34d399; --bad:#fb7185; --warn:#fbbf24; --muted:#9ca8bd;
      --c-allow:#34d399; --c-challenge:#fbbf24; --c-block:#fb7185;
    }
    * { box-sizing: border-box; }
    body { margin:0; background:#050505; color:#f8fbff; }
    .shell { padding:20px; display:grid; gap:16px; }

    /* Header */
    .top { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
    .top-left h1 { margin:4px 0 0; font-size:26px; font-weight:800; }
    .top-left .eyebrow { font-size:11px; color:#93c5fd; text-transform:uppercase; letter-spacing:.1em; }
    .top-right { display:flex; gap:8px; flex-wrap:wrap; }
    a.nav-link { border:1px solid rgba(255,255,255,.14); border-radius:999px; padding:7px 14px;
      background:rgba(255,255,255,.05); color:#f8fbff; text-decoration:none; font-size:12px; }

    /* Input card */
    .input-card { border:1px solid rgba(255,255,255,.12); border-radius:18px;
      background:rgba(255,255,255,.04); padding:18px; display:grid; gap:12px; }
    .input-row { display:grid; grid-template-columns:1fr 2fr; gap:12px; }
    .field-label { font-size:11px; color:var(--muted); text-transform:uppercase;
      letter-spacing:.07em; margin-bottom:6px; }
    input.cc, textarea.cc {
      width:100%; background:rgba(0,0,0,.3) !important; border:1px solid rgba(255,255,255,.15) !important;
      border-radius:12px !important; color:#f8fbff !important; padding:10px 12px !important;
      font-size:13px; outline:none; box-shadow:none !important; resize:vertical;
    }
    input.cc:focus, textarea.cc:focus { border-color:rgba(34,211,238,.55) !important; }
    .input-actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }

    /* Buttons */
    #runBtn {
      border:1px solid rgba(34,211,238,.4) !important; border-radius:999px !important;
      padding:9px 22px !important; background:linear-gradient(135deg,rgba(34,211,238,.18),rgba(168,85,247,.18)) !important;
      color:#f8fbff !important; cursor:pointer; font-size:13px; font-weight:700;
      display:inline-flex; align-items:center; gap:7px; transition:all .22s;
      box-shadow:none !important;
    }
    #runBtn:hover { border-color:rgba(34,211,238,.75) !important; box-shadow:0 0 18px rgba(34,211,238,.2) !important; }
    #runBtn:disabled { opacity:.5; cursor:wait; }
    .view-toggle { display:flex; gap:4px; border:1px solid rgba(255,255,255,.12);
      border-radius:999px; padding:3px; background:rgba(0,0,0,.3); }
    .view-btn { border:none !important; border-radius:999px !important; padding:5px 14px !important;
      font-size:12px; font-weight:600; cursor:pointer; transition:all .2s;
      background:transparent !important; color:var(--muted) !important; box-shadow:none !important; }
    .view-btn.active { background:rgba(34,211,238,.18) !important; color:#f8fbff !important;
      box-shadow:none !important; }

    /* Summary banner */
    .summary { display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; }
    .sum-card { border:1px solid rgba(255,255,255,.1); border-radius:14px;
      background:rgba(255,255,255,.04); padding:12px 14px; transition:border-color .3s; }
    .sum-card:hover { border-color:rgba(34,211,238,.3); }
    .sum-label { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; }
    .sum-value { font-size:18px; font-weight:800; margin-top:5px; font-variant-numeric:tabular-nums; }
    .sum-sub { font-size:11px; color:var(--muted); margin-top:3px; }
    .safest-card { border-color:rgba(52,211,153,.3) !important; background:rgba(52,211,153,.05) !important; }
    .riskiest-card { border-color:rgba(251,113,133,.3) !important; background:rgba(251,113,133,.05) !important; }

    /* Result cards */
    #cardView { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px,1fr)); gap:14px; }
    .model-card {
      border:1px solid rgba(255,255,255,.12); border-radius:18px;
      background:rgba(255,255,255,.05); padding:16px;
      animation:cardIn .3s ease both; transition:border-color .25s, box-shadow .25s;
    }
    .model-card:hover { border-color:rgba(34,211,238,.35); box-shadow:0 0 24px rgba(34,211,238,.08); }
    .model-card.safest-outline { border-color:rgba(52,211,153,.45) !important; box-shadow:0 0 20px rgba(52,211,153,.1) !important; }
    .model-card.riskiest-outline { border-color:rgba(251,113,133,.45) !important; box-shadow:0 0 20px rgba(251,113,133,.1) !important; }
    @keyframes cardIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

    .card-header { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
    .card-header strong { font-size:15px; font-weight:800; flex:1; }
    .decision-badge {
      border-radius:999px; padding:4px 10px; font-size:11px; font-weight:700;
      border:none !important; box-shadow:none !important;
    }
    .badge-allow    { background:rgba(52,211,153,.15) !important; color:var(--c-allow) !important; border:1px solid rgba(52,211,153,.35) !important; }
    .badge-challenge{ background:rgba(251,191,36,.12) !important; color:var(--c-challenge) !important; border:1px solid rgba(251,191,36,.35) !important; }
    .badge-block    { background:rgba(251,113,133,.12) !important; color:var(--c-block) !important; border:1px solid rgba(251,113,133,.35) !important; animation:bpulse 1.8s infinite; }
    @keyframes bpulse { 50%{box-shadow:0 0 10px rgba(251,113,133,.3) !important} }
    .label-tag { font-size:10px; padding:3px 8px; border-radius:999px;
      border:1px solid rgba(255,255,255,.15) !important; color:var(--muted) !important;
      background:rgba(255,255,255,.05) !important; box-shadow:none !important; }

    /* Risk bar */
    .risk-section { margin:10px 0; }
    .risk-header { display:flex; justify-content:space-between; font-size:11px; color:var(--muted); margin-bottom:5px; }
    .risk-val { font-weight:700; }
    .risk-track { height:8px; background:rgba(255,255,255,.08); border-radius:8px; overflow:hidden;
      border:none !important; box-shadow:none !important; }
    .risk-fill { height:100%; border-radius:8px; width:0%; transition:width .7s cubic-bezier(.2,.8,.2,1); }
    .risk-low  { background:linear-gradient(90deg,#059669,#34d399); }
    .risk-mid  { background:linear-gradient(90deg,#d97706,#fbbf24); }
    .risk-high { background:linear-gradient(90deg,#be123c,#fb7185); }

    /* Confidence pip */
    .confidence-row { display:flex; align-items:center; gap:6px; margin-top:8px; }
    .conf-label { font-size:11px; color:var(--muted); }
    .conf-pips { display:flex; gap:3px; }
    .pip { width:10px; height:10px; border-radius:3px; background:rgba(255,255,255,.12); }
    .pip.on-high   { background:#34d399; box-shadow:0 0 6px rgba(52,211,153,.6); }
    .pip.on-medium { background:#fbbf24; box-shadow:0 0 6px rgba(251,191,36,.6); }
    .pip.on-low    { background:#fb7185; box-shadow:0 0 6px rgba(251,113,133,.6); }

    /* Response */
    .response-box { font-size:12px; color:#cbd5e1; background:rgba(0,0,0,.3);
      border:1px solid rgba(255,255,255,.08) !important; border-radius:10px !important;
      padding:10px; margin-top:10px; line-height:1.55; max-height:120px; overflow-y:auto;
      box-shadow:none !important; }
    .explanation { font-size:11px; color:var(--muted); margin-top:8px; line-height:1.5; }

    /* Security score */
    .scores-row { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px; }
    .score-box { background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.08) !important;
      border-radius:10px !important; padding:8px; box-shadow:none !important; }
    .score-label { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
    .score-val { font-size:15px; font-weight:700; margin-top:2px; font-variant-numeric:tabular-nums; }

    /* Table view */
    #tableView { display:none; overflow-x:auto; }
    .comp-table { width:100%; border-collapse:collapse; font-size:13px; }
    .comp-table th { text-align:left; padding:10px 12px; font-size:11px; color:#93c5fd;
      text-transform:uppercase; letter-spacing:.07em; border-bottom:1px solid rgba(255,255,255,.1);
      white-space:nowrap; }
    .comp-table td { padding:10px 12px; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:middle; }
    .comp-table tr:hover td { background:rgba(255,255,255,.03); }
    .tbl-risk-track { height:6px; background:rgba(255,255,255,.08); border-radius:6px; width:80px; overflow:hidden; }
    .tbl-risk-fill  { height:100%; border-radius:6px; transition:width .7s ease; }
    .tbl-model { font-weight:700; }
    .tbl-output { color:var(--muted); max-width:240px; overflow:hidden;
      text-overflow:ellipsis; white-space:nowrap; font-size:12px; }

    /* Spinner */
    .spinner { width:13px; height:13px; border-radius:50%;
      border:2px solid rgba(255,255,255,.18); border-top-color:#34d399;
      animation:spin .65s linear infinite; }
    @keyframes spin { to{transform:rotate(360deg)} }

    /* Empty/skeleton */
    .placeholder { border:1px dashed rgba(255,255,255,.15); border-radius:16px;
      padding:28px; color:var(--muted); text-align:center; font-size:13px; }

    .muted { color:var(--muted); font-size:12px; }
    @media(max-width:700px) {
      .input-row { grid-template-columns: 1fr; }
      .summary { grid-template-columns: repeat(2, 1fr); }
      .top { flex-direction: column; align-items: flex-start; gap: 10px; }
      .top-right { flex-wrap: wrap; }
      .input-actions { flex-wrap: wrap; }
      .view-toggle { flex-wrap: wrap; }
    }
    @media(max-width:420px) {
      .summary { grid-template-columns: 1fr; }
      .input-card { padding: 12px; }
      #cardView { grid-template-columns: 1fr !important; }
    }
  </style>
</head>
<body>
<main class="shell">

  <!-- Header -->
  <section class="top">
    <div class="top-left">
      <div class="eyebrow">Zero Trust AI Gateway</div>
      <h1>Model Security Comparison</h1>
    </div>
    <div class="top-right">
      <a class="nav-link" href="/dashboard">Dashboard</a>
      <a class="nav-link" href="/chat">Chat</a>
      <a class="nav-link" href="/dashboard/evaluation">Evaluate</a>
    </div>
  </section>

  <!-- Input -->
  <article class="input-card">
    <div class="input-row">
      <div>
        <div class="field-label">Model IDs (comma-separated)</div>
        <input class="cc" id="modelIds" value="1,2,3" placeholder="e.g. 1,2,3" />
      </div>
      <div>
        <div class="field-label">Prompt</div>
        <input class="cc" id="promptInput" value="Explain zero trust architecture in plain language." />
      </div>
    </div>
    <div class="input-actions">
      <button id="runBtn"><span id="btnIcon">▶</span><span id="btnTxt">Compare Models</span></button>
      <div class="view-toggle">
        <button class="view-btn active" id="btnCards" onclick="setView('cards')">Cards</button>
        <button class="view-btn"        id="btnTable" onclick="setView('table')">Table</button>
      </div>
      <span class="muted" id="runMeta"></span>
    </div>
  </article>

  <!-- Summary -->
  <section class="summary" id="summarySection" style="display:none">
    <div class="sum-card safest-card">
      <div class="sum-label">Safest Model</div>
      <div class="sum-value" style="color:var(--good)" id="sumSafest">—</div>
      <div class="sum-sub" id="sumSafestRisk">—</div>
    </div>
    <div class="sum-card riskiest-card">
      <div class="sum-label">Most Risky</div>
      <div class="sum-value" style="color:var(--bad)" id="sumRiskiest">—</div>
      <div class="sum-sub" id="sumRiskiestRisk">—</div>
    </div>
    <div class="sum-card">
      <div class="sum-label">Average Risk</div>
      <div class="sum-value" id="sumAvgRisk">—</div>
      <div class="sum-sub">across all models</div>
    </div>
    <div class="sum-card">
      <div class="sum-label">Models Compared</div>
      <div class="sum-value" id="sumCount">—</div>
      <div class="sum-sub" id="sumDecisions">—</div>
    </div>
  </section>

  <!-- Card view -->
  <section id="cardView">
    <div class="placeholder">Enter model IDs above and press <strong>Compare Models</strong> to start.</div>
  </section>

  <!-- Table view -->
  <section id="tableView">
    <article style="border:1px solid rgba(255,255,255,.1);border-radius:16px;background:rgba(255,255,255,.04);padding:0;overflow:hidden">
      <table class="comp-table" id="compTable">
        <thead>
          <tr>
            <th>Model</th>
            <th>Decision</th>
            <th>Risk Score</th>
            <th>Risk Bar</th>
            <th>Confidence</th>
            <th>Security Score</th>
            <th>Response</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </article>
  </section>

</main>
<script>
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
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
