from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


RESEARCH_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Research Evaluation — Zero Trust AI Gateway</title>
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
      --soft: #9ca8bd;
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
    .page-header p { font-size: 14px; color: var(--muted); line-height: 1.6; max-width: 680px; margin-top: 6px; }
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
    .tab-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; padding: 4px; background: var(--bg-2); border-radius: 8px; border: 1px solid var(--border); width: fit-content; }
    .tab { padding: 8px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; color: var(--muted); background: transparent; border-color: transparent; }
    .tab:hover { color: var(--text); background: var(--bg-3); border-color: transparent; }
    .tab.active { background: var(--bg-3); border: 1px solid var(--b2); color: var(--text); }
    .kpi-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
    .kpi {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      background: var(--bg-1);
      transition: border-color .2s;
    }
    .kpi:hover { border-color: rgba(0,212,255,.2); }
    .kpi-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }
    .kpi-value { font-size: 26px; font-weight: 700; margin-top: 6px; color: var(--text); }
    .tab-panel { display: grid; grid-template-columns: 1.1fr .9fr; gap: 14px; }
    .tab-panel.hidden { display: none; }
    .card {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 16px;
      transition: border-color .2s;
    }
    .card:hover { border-color: rgba(0,212,255,.14); }
    .card-title { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 12px; }
    .card-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .evidence-list { display: grid; gap: 0; margin-top: 8px; }
    .evidence-row { display: flex; justify-content: space-between; gap: 12px; border-top: 1px solid var(--border); padding: 8px 0; color: var(--soft); font-size: 13px; }
    .evidence-row:first-child { border-top: none; }
    .evidence-row b { color: var(--text); font-variant-numeric: tabular-nums; }
    .badge { display: inline-flex; align-items: center; border: 1px solid var(--b2); border-radius: 999px; padding: 3px 8px; font-size: 11px; color: var(--muted); background: var(--bg-2); }
    .badge.good { color: var(--green); border-color: rgba(34,211,160,.3); }
    .badge.warn { color: var(--amber); border-color: rgba(245,166,35,.3); }
    .empty-state { display: none; margin-bottom: 14px; border: 1px dashed var(--border); border-radius: 8px; padding: 14px; color: var(--muted); background: var(--bg-1); text-align: center; font-size: 13px; }
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; color: var(--soft); }
    th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); vertical-align: top; }
    th { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; }
    .summary-copy { color: var(--soft); line-height: 1.55; margin: 8px 0 0; font-size: 13px; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      border: 1px solid var(--border);
      border-radius: 7px;
      padding: 12px;
      background: var(--bg-2);
      color: var(--muted);
      font-family: var(--mono);
      max-height: 400px;
      overflow: auto;
      font-size: 12px;
      line-height: 1.5;
    }
    ul { margin: 8px 0 0; padding-left: 18px; color: var(--soft); line-height: 1.6; font-size: 14px; }
    .evidence-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .section-label { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
    .section-label::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .mt-4 { margin-top: 14px; }
    .good { color: var(--green); }
    .bad  { color: var(--red); }
    #status { display: none; margin-bottom: 14px; border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; background: var(--bg-1); color: var(--muted); font-size: 13px; }
    @media (max-width: 1050px) { .kpi-strip { grid-template-columns: repeat(2,1fr); } }
    @media (max-width: 760px) { .page-header, .tab-panel, .evidence-grid { grid-template-columns: 1fr; } .tab-row { width: 100%; } }
  </style>
</head>
<body>
  <main class="shell">
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Research-Grade Evaluation</div>
        <h1>Replayable Security Evaluation</h1>
        <p>This system produces replayable, explainable security evidence: policy replay, counterfactuals, model comparison, and control effectiveness derived from audit decisions.</p>
      </div>
      <div class="hdr-row">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/security-monitor">Security Monitor</a>
        <button id="reloadBtn">Refresh</button>
      </div>
    </div>

    <div class="tab-row">
      <button class="tab active" data-tab="test-suite">Test Suite</button>
      <button class="tab" data-tab="policy-replay">Policy Replay</button>
      <button class="tab" data-tab="counterfactuals">Counterfactuals</button>
      <button class="tab" data-tab="model-comparison">Model Comparison</button>
      <button class="tab" data-tab="control-effectiveness">Control Effectiveness</button>
    </div>

    <section class="kpi-strip">
      <div class="kpi"><div class="kpi-label">Attack Block Rate</div><div id="blockRate" class="kpi-value">--</div></div>
      <div class="kpi"><div class="kpi-label">False Positive Rate</div><div id="falsePositiveRate" class="kpi-value">--</div></div>
      <div class="kpi"><div class="kpi-label">Allow / Challenge / Block</div><div id="distribution" class="kpi-value">--</div></div>
      <div class="kpi"><div class="kpi-label">Replay Evidence</div><div id="requests" class="kpi-value">--</div></div>
    </section>

    <section id="emptyState" class="empty-state">No evaluation evidence yet. Run secure inference or execute a test suite to generate replayable security data.</section>
    <section id="status">Loading research evaluation...</section>

    <div class="tab-panel" data-panel="test-suite">
      <article class="card"><div class="card-title">Research Findings</div><ul id="findings"><li>Loading...</li></ul></article>
      <article class="card"><div class="card-title">Test Summary</div><div id="testSummary" class="evidence-list"></div></article>
    </div>
    <div class="tab-panel hidden mt-4" data-panel="policy-replay">
      <article class="card"><div class="card-title">Policy Replay</div><div id="replay" class="table-wrap"></div></article>
      <article class="card"><div class="card-title">Dataset Export</div><div id="dataset" class="evidence-list"></div></article>
    </div>
    <div class="tab-panel hidden mt-4" data-panel="counterfactuals">
      <article class="card"><div class="card-title">Counterfactuals</div><div id="counterfactualDetails" class="table-wrap"></div></article>
      <article class="card"><div class="card-title">Replay Result</div><div id="replayResult" class="evidence-list"></div></article>
    </div>
    <div class="tab-panel hidden mt-4" data-panel="model-comparison">
      <article class="card"><div class="card-title">Model Comparison</div><p class="summary-copy" id="modelComparison">Compare owned models from Secure Chat or the model comparison API. Results are logged as replayable evidence.</p></article>
      <article class="card"><div class="card-title">Cross-Model Escalation Detection</div><div id="crossModel" class="evidence-list"></div></article>
    </div>
    <div class="tab-panel hidden mt-4" data-panel="control-effectiveness">
      <article class="card"><div class="card-title">Control Contribution</div><ul id="controls"><li>Loading...</li></ul></article>
      <article class="card"><div class="card-title">Effectiveness Summary</div><div id="effectiveness" class="evidence-list"></div></article>
    </div>

    <section class="card mt-4">
      <div class="card-title">Research Evidence Summary</div>
      <div class="evidence-grid">
        <div>
          <div class="section-label">Contribution</div>
          <p class="summary-copy">Behaviour-aware Zero Trust policy enforcement for secure AI model serving.</p>
        </div>
        <div>
          <div class="section-label">Privacy</div>
          <div id="privacySummary" class="evidence-list"></div>
        </div>
      </div>
      <div class="mt-4">
        <div class="section-label">Recommended Next Steps</div>
        <ul id="nextSteps"></ul>
      </div>
    </section>
  </main>
  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    const $ = (id) => document.getElementById(id);
    if (!token) location.href = "/login?next=/research";
    const authHeaders = () => ({ Authorization: `Bearer ${token}` });
    async function request(path) {
      const res = await fetch(path, { headers: authHeaders() });
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) {
        if (res.status === 401) location.href = "/dashboard";
        const detail = typeof data === "object" ? data.detail : data;
        const message = typeof detail === "object" ? (detail.message || detail.title || "Request failed.") : (detail || "Request failed.");
        throw new Error(message);
      }
      return data;
    }
    function pct(value) {
      const n = Number(value || 0);
      return `${Math.round(n * 100)}%`;
    }
    function escHtml(s) {
      return String(s ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
    }
    function evidenceRows(rows) {
      return rows.map(([label, value]) => `<div class="evidence-row"><span>${escHtml(label)}</span><b>${escHtml(value)}</b></div>`).join("");
    }
    function yesNo(value) {
      return value ? "Yes" : "No";
    }
    function renderReplayTable(modes = []) {
      if (!modes.length) return `<div class="summary-copy">No replay modes are available yet.</div>`;
      return `<table><thead><tr><th>Mode</th><th>Total</th><th>Allowed</th><th>Challenged</th><th>Blocked</th><th>Block Rate</th><th>Changed</th></tr></thead><tbody>
        ${modes.map((mode) => `<tr>
          <td><span class="badge">${escHtml(mode.mode)}</span></td>
          <td>${mode.total_requests || 0}</td>
          <td>${mode.allowed || 0}</td>
          <td>${mode.challenged || 0}</td>
          <td>${mode.blocked || 0}</td>
          <td>${pct(mode.block_rate)}</td>
          <td>${mode.difference_vs_original?.changed_decisions || 0}</td>
        </tr>`).join("")}
      </tbody></table>`;
    }
    function renderCounterfactualTable(summary = {}) {
      const counts = summary.difference_counts || {};
      const entries = Object.entries(counts);
      if (!entries.length) return `<div class="summary-copy">No counterfactual decision differences have been observed yet.</div>`;
      return `<table><thead><tr><th>Removed Layer</th><th>Changed Decisions</th><th>Interpretation</th></tr></thead><tbody>
        ${entries.map(([name, count]) => `<tr><td>${escHtml(name.replaceAll("_", " "))}</td><td>${count}</td><td>Decision changed when this adaptive layer was removed.</td></tr>`).join("")}
      </tbody></table>`;
    }
    function renderList(id, rows, mapper) {
      $(id).innerHTML = rows.length ? rows.map((row) => `<li>${mapper(row)}</li>`).join("") : "<li>No evidence yet.</li>";
    }
    function setTab(tabId) {
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabId));
      document.querySelectorAll(".tab-panel").forEach((panel) => {
        const active = panel.dataset.panel === tabId;
        panel.classList.toggle("hidden", !active);
        panel.style.display = active ? "" : "none";
      });
    }
    async function load() {
      $("status").textContent = "Loading research evaluation...";
      $("status").style.display = "block";
      const [report, replay, dataset] = await Promise.all([
        request(`${api}/research/evaluation-report`),
        request(`${api}/research/policy-replay`),
        request(`${api}/research/evaluation-dataset?limit=50`).catch((err) => ({
          row_count: 0,
          raw_prompt_text_included: false,
          columns: [],
          admin_only: true,
          message: err.message || "Dataset export is admin-only."
        }))
      ]);
      const sample = report.sample || {};
      const decisionCounts = sample.decision_counts || {};
      const requestCount = Number(sample.request_logs || 0);
      $("requests").textContent = requestCount;
      $("blockRate").textContent = pct(report.sample.block_rate);
      $("falsePositiveRate").textContent = pct(report.sample.false_positive_rate || 0);
      $("distribution").textContent = `${decisionCounts.allow || 0}/${decisionCounts.challenge || 0}/${decisionCounts.block || 0}`;
      $("emptyState").style.display = requestCount ? "none" : "block";
      renderList("findings", report.findings || [], (item) => item);
      renderList("controls", report.control_effectiveness_summary.top_controls || [], (item) => `${item.control_id} · ${item.control_name} · ${Math.round((item.contribution_percentage || 0) * 100)}%`);
      $("testSummary").innerHTML = evidenceRows([
        ["Sample Size", requestCount],
        ["Attack Block Rate", pct(sample.block_rate)],
        ["False Positive Rate", pct(sample.false_positive_rate || 0)],
        ["Research Readiness", pct(report.research_readiness?.score || 0)],
        ["Last Evaluation Run", new Date().toLocaleString()]
      ]);
      $("replay").innerHTML = renderReplayTable(replay.modes || []);
      $("counterfactualDetails").innerHTML = renderCounterfactualTable(report.counterfactual_summary || {});
      $("replayResult").innerHTML = evidenceRows([
        ["Replay Source", replay.source || "request_logs.decision_trace"],
        ["Inference Re-run", yesNo(Boolean(replay.inference_rerun))],
        ["Replay Modes", (replay.modes || []).map((mode) => mode.mode).join(", ") || "None"],
        ["Formal Risk Evaluation", replay.formal_risk_evaluation ? "Available" : "No evidence yet"]
      ]);
      const threat = report.threat_intelligence_metrics || {};
      $("crossModel").innerHTML = evidenceRows([
        ["Scope", report.scope === "global" ? "Global" : "Current user"],
        ["Cross-model abuse detections", threat.cross_model_abuse_detections ?? "Admin-only or no evidence"],
        ["Attack sequence count", threat.attack_sequence_count ?? sample.attack_sequence_events ?? 0],
        ["Average sequence severity", threat.average_sequence_severity ?? "No evidence yet"]
      ]);
      $("effectiveness").innerHTML = evidenceRows([
        ["Enforcement decisions", report.control_effectiveness_summary?.total_enforcement_decisions || 0],
        ["Top controls listed", (report.control_effectiveness_summary?.top_controls || []).length],
        ["Counterfactual examples", report.counterfactual_summary?.example_count || 0],
        ["Evaluated requests", report.counterfactual_summary?.total_requests_analyzed || 0]
      ]);
      $("dataset").innerHTML = evidenceRows([
        ["Dataset Rows", dataset.row_count || 0],
        ["Raw Prompt Text Included", yesNo(Boolean(dataset.raw_prompt_text_included))],
        ["Prompt-safe Export", dataset.admin_only ? "Admin-only" : "Available"],
        ["Columns", (dataset.columns || []).length]
      ]) + (dataset.message ? `<p class="summary-copy">${escHtml(dataset.message)}</p>` : "");
      const privacy = report.privacy || {};
      $("privacySummary").innerHTML = evidenceRows([
        ["Raw prompt text stored", yesNo(Boolean(privacy.raw_prompt_text_stored))],
        ["Prompt hashes used", yesNo(privacy.uses_prompt_hashes !== false)],
        ["Dataset export is prompt-safe", yesNo(privacy.dataset_export_is_prompt_safe !== false)]
      ]);
      const nextSteps = [
        "Run benign, suspicious, injection, extraction, jailbreak, and cross-model test suites.",
        "Export the research-safe evaluation dataset for dissertation tables.",
        "Compare current, stricter, and relaxed policy modes.",
        "Use counterfactual replay to measure adaptive controls."
      ];
      $("nextSteps").innerHTML = nextSteps.map((step) => `<li>${escHtml(step)}</li>`).join("");
      $("status").style.display = "none";
    }
    $("reloadBtn").addEventListener("click", load);
    document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => setTab(tab.dataset.tab)));
    setTab(new URLSearchParams(location.search).get("tab") || "test-suite");
    load().catch((err) => {
      $("status").style.display = "block";
      $("status").textContent = String(err.message || err);
    });
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
