from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


TESTING_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>System Testing</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; --muted:#9ca8bd; --good:#34d399; --bad:#fb7185; --warn:#fbbf24; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #050505; color: #f8fbff; }
    .shell { padding: 18px; display: grid; gap: 14px; }
    .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .grid { display:grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap:10px; }
    .card { border:1px solid rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.05); padding:12px; transition: transform .22s ease, opacity .22s ease; }
    .card.fade { opacity:.78; transform: translateY(2px); }
    .metric strong { display:block; font-size:24px; margin-top:4px; }
    .muted { color: var(--muted); font-size:12px; line-height:1.45; }
    .status { border:1px solid rgba(255,255,255,.14); border-radius:999px; padding:6px 10px; font-size:12px; }
    .status.good { color: var(--good); border-color: rgba(52,211,153,.5); }
    .status.bad { color: var(--bad); border-color: rgba(251,113,133,.5); }
    .status.warn { color: var(--warn); border-color: rgba(251,191,36,.5); }
    .list { display:grid; gap:8px; }
    .item { border:1px solid rgba(255,255,255,.1); border-radius:12px; padding:10px; background:rgba(0,0,0,.22); }
    button, a { border:1px solid rgba(255,255,255,.15); border-radius:999px; padding:9px 12px; background:rgba(255,255,255,.06); color:#f8fbff; text-decoration:none; cursor:pointer; }
    button:disabled { opacity:.6; cursor:wait; }
    .spinner {
      width:14px; height:14px; border-radius:50%;
      border:2px solid rgba(255,255,255,.2); border-top-color:#34d399;
      display:inline-block; animation: spin .7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    @media (max-width: 980px) { .grid { grid-template-columns: repeat(2, minmax(140px,1fr)); } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="row">
      <a href="/dashboard">Dashboard</a>
      <a href="/dashboard/soc">SOC</a>
      <a href="/dashboard/security">Security Suite</a>
      <button id="runBtn">Run Tests</button>
      <span id="runState" class="status warn">No run yet</span>
    </section>

    <section class="grid">
      <article class="card metric"><span class="muted">Total</span><strong id="total">--</strong></article>
      <article class="card metric"><span class="muted">Passed</span><strong id="passed">--</strong></article>
      <article class="card metric"><span class="muted">Failed</span><strong id="failed">--</strong></article>
      <article class="card metric"><span class="muted">Duration</span><strong id="duration">--</strong></article>
    </section>

    <section class="card">
      <h2 style="margin:0 0 8px">Failures</h2>
      <div id="failures" class="list muted">No failures to show.</div>
    </section>
  </main>

  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/testing";
    const headers = () => ({ Authorization: `Bearer ${token}` });
    const $ = (id) => document.getElementById(id);

    function esc(v) {
      return String(v ?? "").replace(/[&<>\"']/g, (c) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "\\"":"&quot;", "'":"&#039;" }[c]));
    }
    function setCardsFading(fading) {
      document.querySelectorAll(".metric.card").forEach((el) => {
        if (fading) el.classList.add("fade");
        else el.classList.remove("fade");
      });
    }
    function statusClass(failed, total) {
      if (total === 0) return "warn";
      return failed > 0 ? "bad" : "good";
    }
    function statusText(failed, total) {
      if (total === 0) return "No tests executed";
      return failed > 0 ? "Failures detected" : "All tests passing";
    }
    function renderResult(data) {
      $("total").textContent = String(data.total ?? 0);
      $("passed").textContent = String(data.passed ?? 0);
      $("failed").textContent = String(data.failed ?? 0);
      $("duration").textContent = `${Number(data.duration ?? 0).toFixed(3)}s`;
      const failures = data.failures || [];
      $("failures").innerHTML = failures.length
        ? failures.map((f) => `<article class="item"><strong>${esc(f.test)}</strong><div class="muted" style="margin-top:5px">${esc(f.error)}</div></article>`).join("")
        : `<article class="item"><strong>No failures</strong><div class="muted">SOC endpoint tests passed successfully.</div></article>`;
      const cls = statusClass(Number(data.failed || 0), Number(data.total || 0));
      $("runState").className = `status ${cls}`;
      $("runState").textContent = statusText(Number(data.failed || 0), Number(data.total || 0));
    }
    async function runTests() {
      const btn = $("runBtn");
      btn.disabled = true;
      setCardsFading(true);
      $("runState").className = "status warn";
      $("runState").innerHTML = `<span class="spinner"></span> Running...`;
      try {
        const res = await fetch(`${api}/testing/run-soc-tests`, { headers: headers() });
        const text = await res.text();
        let data = {};
        try { data = text ? JSON.parse(text) : {}; } catch { data = { failures: [{ test: "parse", error: "Invalid JSON in response" }] }; }
        if (!res.ok) throw new Error((data.detail && data.detail.message) || data.detail || `Request failed (${res.status})`);
        renderResult(data);
      } catch (err) {
        renderResult({ total: 0, passed: 0, failed: 1, duration: 0.0, failures: [{ test: "run_soc_tests", error: String(err.message || err) }] });
      } finally {
        setCardsFading(false);
        btn.disabled = false;
      }
    }
    $("runBtn").addEventListener("click", runTests);
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\\n  </style>").replace("</body>", f"{CYBER_UI_JS}\\n</body>")
