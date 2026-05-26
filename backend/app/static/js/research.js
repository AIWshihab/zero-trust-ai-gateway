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