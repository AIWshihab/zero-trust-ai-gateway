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