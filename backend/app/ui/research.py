RESEARCH_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Research Evaluation</title>
  <style>
    :root {
      color-scheme: dark;
      --text: #fff7ea;
      --muted: #d4c0a4;
      --soft: #aab3bf;
      --amber: #ffb13b;
      --green: #78e08f;
      --red: #ff4d3d;
      --ink: #080604;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background:
        linear-gradient(118deg, rgba(255,255,255,.035) 0 1px, transparent 1px 70px),
        radial-gradient(circle at 18% 10%, rgba(255,159,28,.25), transparent 30%),
        linear-gradient(140deg, #070706 0%, #15110d 45%, #2b1207 82%, #070706 100%);
    }
    .shell { padding: 20px clamp(14px, 3vw, 34px) 34px; }
    header { display: grid; grid-template-columns: minmax(280px, 1fr) auto; gap: 16px; align-items: start; margin-bottom: 16px; }
    .eyebrow { color: var(--amber); text-transform: uppercase; letter-spacing: .12em; font-weight: 950; font-size: 12px; }
    h1 { margin: 6px 0 10px; font-size: clamp(34px, 5vw, 62px); line-height: .92; text-transform: uppercase; text-shadow: 4px 4px 0 #000, 8px 8px 0 rgba(244,123,32,.34); }
    p { color: #ffe9c5; line-height: 1.55; font-weight: 720; max-width: 900px; }
    a, button {
      border: 2px solid var(--ink);
      border-radius: 7px;
      padding: 10px 12px;
      color: #150905;
      background: linear-gradient(135deg, #ffd164, #ff7a1a 52%, #f0441f);
      font-weight: 900;
      cursor: pointer;
      text-decoration: none;
      box-shadow: 4px 4px 0 rgba(0,0,0,.75);
      font: inherit;
    }
    a.secondary, button.secondary { color: var(--text); background: rgba(255,241,213,.08); border-color: rgba(255,178,77,.42); }
    .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; margin-bottom: 14px; }
    .wide { display: grid; grid-template-columns: 1.1fr .9fr; gap: 14px; }
    .card {
      border: 2px solid var(--ink);
      border-radius: 7px;
      background: rgba(18,18,16,.94);
      box-shadow: 6px 6px 0 rgba(0,0,0,.72), 0 22px 70px rgba(0,0,0,.34);
      position: relative;
      overflow: hidden;
    }
    .card::after { content: ""; position: absolute; inset: 0; pointer-events: none; background: repeating-linear-gradient(-12deg, transparent 0 19px, rgba(255,159,28,.05) 20px 22px); }
    .inner { position: relative; z-index: 1; padding: 14px; }
    .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 900; }
    .value { margin-top: 7px; font-size: 27px; font-weight: 950; }
    h2 { margin: 0 0 8px; color: var(--amber); text-transform: uppercase; letter-spacing: .08em; font-size: 16px; }
    ul { margin: 8px 0 0; padding-left: 18px; color: var(--soft); line-height: 1.5; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(8,6,4,.82);
      color: #fff1d5;
      max-height: 430px;
      overflow: auto;
    }
    .good { color: var(--green); }
    .bad { color: var(--red); }
    @media (max-width: 1050px) { .grid, .wide { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 760px) { header, .grid, .wide { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <div class="eyebrow">Research Workspace</div>
        <h1>Evaluation Lab</h1>
        <p>Policy replay, control effectiveness, counterfactual contribution, and risk drift without rerunning model inference or storing raw prompts.</p>
      </div>
      <div class="row">
        <a class="secondary" href="/dashboard">Dashboard</a>
        <a class="secondary" href="/logs">Logs</a>
        <button id="reloadBtn">Refresh</button>
      </div>
    </header>
    <section class="grid">
      <div class="card"><div class="inner"><div class="label">Requests</div><div id="requests" class="value">--</div></div></div>
      <div class="card"><div class="inner"><div class="label">Block Rate</div><div id="blockRate" class="value">--</div></div></div>
      <div class="card"><div class="inner"><div class="label">Readiness</div><div id="readiness" class="value">--</div></div></div>
      <div class="card"><div class="inner"><div class="label">Counterfactuals</div><div id="counterfactuals" class="value">--</div></div></div>
    </section>
    <section class="wide">
      <article class="card"><div class="inner"><h2>Research Findings</h2><ul id="findings"><li>Loading...</li></ul></div></article>
      <article class="card"><div class="inner"><h2>Top Controls</h2><ul id="controls"><li>Loading...</li></ul></div></article>
    </section>
    <section class="wide" style="margin-top:14px">
      <article class="card"><div class="inner"><h2>Policy Replay</h2><pre id="replay">Loading...</pre></div></article>
      <article class="card"><div class="inner"><h2>Dataset Export</h2><pre id="dataset">Loading...</pre></div></article>
    </section>
    <pre id="status">Loading research evaluation...</pre>
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
        if (res.status === 401 || res.status === 403) location.href = "/dashboard";
        throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : String(data));
      }
      return data;
    }
    function pct(value) {
      const n = Number(value || 0);
      return `${Math.round(n * 100)}%`;
    }
    function renderList(id, rows, mapper) {
      $(id).innerHTML = rows.length ? rows.map((row) => `<li>${mapper(row)}</li>`).join("") : "<li>No evidence yet.</li>";
    }
    async function load() {
      $("status").textContent = "Loading research evaluation...";
      const [report, replay, dataset] = await Promise.all([
        request(`${api}/research/evaluation-report`),
        request(`${api}/research/policy-replay`),
        request(`${api}/research/evaluation-dataset?limit=50`)
      ]);
      $("requests").textContent = report.sample.request_logs;
      $("blockRate").textContent = pct(report.sample.block_rate);
      $("readiness").textContent = pct(report.research_readiness.score);
      $("counterfactuals").textContent = Object.values(report.counterfactual_summary.difference_counts || {}).reduce((a, b) => a + Number(b || 0), 0);
      renderList("findings", report.findings || [], (item) => item);
      renderList("controls", report.control_effectiveness_summary.top_controls || [], (item) => `${item.control_id} · ${item.control_name} · ${Math.round((item.contribution_percentage || 0) * 100)}%`);
      $("replay").textContent = JSON.stringify(replay.modes, null, 2);
      $("dataset").textContent = JSON.stringify({
        row_count: dataset.row_count,
        raw_prompt_text_included: dataset.raw_prompt_text_included,
        columns: dataset.columns
      }, null, 2);
      $("status").textContent = JSON.stringify({
        contribution: report.research_contribution,
        inference_rerun: report.inference_rerun,
        privacy: report.privacy,
        next_steps: report.recommended_next_steps
      }, null, 2);
    }
    $("reloadBtn").addEventListener("click", load);
    load().catch((err) => { $("status").textContent = String(err.message || err); });
  </script>
</body>
</html>
"""
