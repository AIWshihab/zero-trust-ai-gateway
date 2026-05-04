from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


EVALUATION_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Evaluation System</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; --muted:#9ca8bd; --good:#34d399; --warn:#fbbf24; --bad:#fb7185; --blue:#93c5fd; }
    * { box-sizing: border-box; }
    body { margin:0; background:#050505; color:#f8fbff; }
    .shell { padding:18px; display:grid; gap:14px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .grid { display:grid; grid-template-columns: repeat(2, minmax(300px,1fr)); gap:14px; }
    .metrics { display:grid; grid-template-columns: repeat(4, minmax(130px,1fr)); gap:10px; }
    .card { border:1px solid rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.05); padding:12px; }
    .metric strong { display:block; font-size:24px; margin-top:4px; }
    .muted { color:var(--muted); font-size:12px; line-height:1.45; }
    .badge { border:1px solid rgba(255,255,255,.16); border-radius:999px; padding:4px 8px; font-size:11px; }
    .allow { color:var(--good); border-color:rgba(52,211,153,.48); }
    .challenge { color:var(--warn); border-color:rgba(251,191,36,.52); }
    .block { color:var(--bad); border-color:rgba(251,113,133,.52); }
    .missing_evidence { color:var(--blue); border-color:rgba(147,197,253,.44); }
    select { border:1px solid rgba(255,255,255,.16); border-radius:12px; background:rgba(0,0,0,.26); color:#f8fbff; padding:9px 10px; }
    a, button { border:1px solid rgba(255,255,255,.15); border-radius:999px; padding:9px 12px; background:rgba(255,255,255,.06); color:#f8fbff; text-decoration:none; cursor:pointer; }
    .timeline { display:grid; gap:10px; }
    .step { border:1px solid rgba(255,255,255,.11); border-radius:14px; padding:10px; background:rgba(0,0,0,.22); animation: rise .22s ease both; }
    .stop { border-color:rgba(251,113,133,.65); box-shadow:0 0 22px rgba(251,113,133,.16); }
    .bar { height:10px; border-radius:999px; background:rgba(255,255,255,.08); overflow:hidden; margin-top:8px; }
    .fill { height:100%; width:0; transition:width .28s ease; background:linear-gradient(90deg,var(--good),var(--warn),var(--bad)); }
    pre { white-space:pre-wrap; word-break:break-word; max-height:320px; overflow:auto; }
    @keyframes rise { from { opacity:0; transform:translateY(7px); } to { opacity:1; transform:translateY(0); } }
    @media (max-width: 1080px) { .grid, .metrics { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<main class="shell">
  <section class="row">
    <a href="/dashboard">Dashboard</a>
    <a href="/dashboard/demo">Demo</a>
    <a href="/logs">Logs</a>
    <button id="exportJsonBtn">Export JSON</button>
    <button id="exportSummaryBtn">Export Summary</button>
  </section>
  <div>
    <div class="muted">Deterministic comparison using scenario dataset + existing gateway logs</div>
    <h1 style="margin:0">Evaluation System</h1>
  </div>

  <article class="card">
    <div class="row">
      <label class="muted">Scenario <select id="scenarioSelect"></select></label>
      <button id="runBtn">Evaluate</button>
      <span id="state" class="muted">Loading scenarios...</span>
    </div>
  </article>

  <section class="metrics">
    <article class="card metric"><span class="muted">Detection improvement</span><strong id="detectDelta">--</strong></article>
    <article class="card metric"><span class="muted">Risk reduction</span><strong id="riskReduction">--</strong></article>
    <article class="card metric"><span class="muted">Block improvement</span><strong id="blockDelta">--</strong></article>
    <article class="card metric"><span class="muted">Stopped at</span><strong id="stopStep">--</strong></article>
  </section>

  <section class="grid">
    <article class="card">
      <h2 style="margin:0 0 10px">Baseline: weak system</h2>
      <div id="baselineMetrics" class="timeline muted">No evaluation yet.</div>
    </article>
    <article class="card">
      <h2 style="margin:0 0 10px">Gateway: Zero Trust controls</h2>
      <div id="gatewayMetrics" class="timeline muted">No evaluation yet.</div>
    </article>
  </section>

  <section class="card">
    <h2 style="margin:0 0 10px">Attack Progression</h2>
    <div id="timeline" class="timeline muted">Select a scenario to compare attack progression.</div>
  </section>

  <section class="grid">
    <article class="card">
      <h2 style="margin:0 0 10px">Policy Impact</h2>
      <div id="policyImpact" class="timeline muted">No policy impact yet.</div>
    </article>
    <article class="card">
      <h2 style="margin:0 0 10px">Raw Evidence</h2>
      <pre id="raw" class="muted">No report loaded.</pre>
    </article>
  </section>
</main>
<script>
const api = "/api/v1";
const token = sessionStorage.getItem("zta_token");
if (!token) location.href = "/login?next=/dashboard/evaluation";
const headers = () => ({ Authorization: `Bearer ${token}` });
const $ = (id) => document.getElementById(id);
let report = null;

async function req(path) {
  const res = await fetch(path, { headers: headers() });
  const text = await res.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
  if (!res.ok) throw new Error((data.detail && data.detail.message) || data.detail || `Request failed (${res.status})`);
  return data;
}
function esc(v) { return String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;" }[c])); }
function pct(v) { return `${Math.round(Number(v || 0) * 100)}%`; }
function cls(decision) {
  const d = String(decision || "").toLowerCase();
  if (d.includes("block")) return "block";
  if (d.includes("challenge")) return "challenge";
  if (d.includes("missing")) return "missing_evidence";
  return "allow";
}
function metricBlock(metrics) {
  return `<div class="metrics">
    <div class="card metric"><span class="muted">Detection</span><strong>${pct(metrics.detection_rate)}</strong><div class="bar"><div class="fill" style="width:${pct(metrics.detection_rate)}"></div></div></div>
    <div class="card metric"><span class="muted">Block</span><strong>${pct(metrics.block_rate)}</strong><div class="bar"><div class="fill" style="width:${pct(metrics.block_rate)}"></div></div></div>
    <div class="card metric"><span class="muted">Challenge</span><strong>${pct(metrics.challenge_rate)}</strong><div class="bar"><div class="fill" style="width:${pct(metrics.challenge_rate)}"></div></div></div>
    <div class="card metric"><span class="muted">False positives</span><strong>${pct(metrics.false_positive_rate)}</strong><div class="bar"><div class="fill" style="width:${pct(metrics.false_positive_rate)}"></div></div></div>
  </div>`;
}
function stepCard(base, gate) {
  const stopped = gate.expected_malicious && gate.stopped;
  return `<article class="step ${stopped ? "stop" : ""}">
    <div class="row"><strong>Step ${gate.step}: ${esc(gate.tactic)}</strong>${stopped ? `<span class="badge block">gateway stopped here</span>` : ""}</div>
    <div class="muted" style="margin-top:6px">${esc(gate.prompt)}</div>
    <div class="row" style="margin-top:8px">
      <span class="badge ${cls(base.decision)}">baseline ${esc(base.decision)}</span>
      <span class="badge ${cls(gate.decision)}">gateway ${esc(gate.decision)}</span>
      <span class="badge">gateway risk ${pct(gate.risk_score)}</span>
      <span class="badge">trust ${gate.trust_score == null ? "n/a" : pct(gate.trust_score)}</span>
    </div>
    <div class="muted" style="margin-top:7px">${esc(gate.reason || base.reason)}</div>
  </article>`;
}
function renderReport(data) {
  report = data;
  $("state").textContent = `${data.scenario.name} loaded`;
  $("detectDelta").textContent = pct(data.improvement.detection_rate_delta);
  $("riskReduction").textContent = pct(Math.max(0, -Number(data.improvement.risk_score_delta || 0)));
  $("blockDelta").textContent = pct(data.improvement.block_rate_delta);
  $("stopStep").textContent = data.policy_impact.gateway_stop_step ? `Step ${data.policy_impact.gateway_stop_step}` : "n/a";
  $("baselineMetrics").classList.remove("muted");
  $("gatewayMetrics").classList.remove("muted");
  $("baselineMetrics").innerHTML = metricBlock(data.baseline.metrics);
  $("gatewayMetrics").innerHTML = metricBlock(data.gateway.metrics);
  $("timeline").classList.remove("muted");
  $("timeline").innerHTML = data.gateway.results.map((gate, index) => stepCard(data.baseline.results[index], gate)).join("");
  $("policyImpact").classList.remove("muted");
  $("policyImpact").innerHTML = `
    <div class="step"><strong>Trust scoring</strong><div class="muted">${esc(data.policy_impact.trust_scoring)}</div></div>
    <div class="step"><strong>Cross-model detection</strong><div class="muted">${esc(data.policy_impact.cross_model_detection)}</div></div>
    <div class="step"><strong>Adaptive penalties</strong><div class="muted">${esc(data.policy_impact.adaptive_penalties)}</div></div>
    <div class="step"><strong>Conclusion</strong><div class="muted">${esc(data.policy_impact.summary)}</div></div>`;
  $("raw").textContent = JSON.stringify(data, null, 2);
}
async function loadScenarios() {
  const data = await req(`${api}/evaluation/scenarios`);
  $("scenarioSelect").innerHTML = data.scenarios.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join("");
  $("state").textContent = "Ready";
}
async function evaluate() {
  $("runBtn").disabled = true;
  $("state").textContent = "Evaluating existing evidence...";
  try {
    renderReport(await req(`${api}/evaluation/compare/${encodeURIComponent($("scenarioSelect").value)}`));
  } catch (e) {
    $("state").textContent = e.message;
  } finally {
    $("runBtn").disabled = false;
  }
}
function download(name, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
function exportJson() {
  if (!report) return;
  download(`evaluation-${report.scenario.id}.json`, JSON.stringify(report, null, 2), "application/json");
}
function exportSummary() {
  if (!report) return;
  const lines = [
    `Evaluation Report: ${report.scenario.name}`,
    `Objective: ${report.scenario.objective}`,
    `Detection improvement: ${pct(report.improvement.detection_rate_delta)}`,
    `Block improvement: ${pct(report.improvement.block_rate_delta)}`,
    `Gateway stopped attack: ${report.policy_impact.gateway_stop_step ? `step ${report.policy_impact.gateway_stop_step}` : "not proven from current logs"}`,
    "",
    "Policy impact:",
    `- Trust scoring: ${report.policy_impact.trust_scoring}`,
    `- Cross-model detection: ${report.policy_impact.cross_model_detection}`,
    `- Adaptive penalties: ${report.policy_impact.adaptive_penalties}`,
    "",
    "Timeline:",
    ...report.gateway.results.map((r) => `Step ${r.step}: ${r.decision} | risk ${pct(r.risk_score)} | ${r.reason}`)
  ];
  download(`evaluation-${report.scenario.id}.txt`, lines.join("\\n"), "text/plain");
}
$("runBtn").onclick = evaluate;
$("exportJsonBtn").onclick = exportJson;
$("exportSummaryBtn").onclick = exportSummary;
loadScenarios().then(evaluate).catch((e) => { $("state").textContent = e.message; });
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
