from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


TESTING_DASHBOARD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>System Self-Test</title>
  <style>
    :root {
      color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui;
      --good:#34d399; --bad:#fb7185; --warn:#fbbf24; --muted:#9ca8bd;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: #050505; color: #f8fbff; }
    .shell { padding: 20px; display: grid; gap: 16px; }

    /* Header */
    .top { display:flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:space-between; }
    .top-left h1 { margin:4px 0 0; font-size:26px; font-weight:800; }
    .top-left .eyebrow { font-size:11px; color:#93c5fd; text-transform:uppercase; letter-spacing:.1em; }
    .top-right { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }

    /* Nav links */
    a { border:1px solid rgba(255,255,255,.14); border-radius:999px; padding:7px 14px;
        background:rgba(255,255,255,.05); color:#f8fbff; text-decoration:none; font-size:12px; }

    /* Run button */
    #runBtn {
      border:1px solid rgba(34,211,238,.4); border-radius:999px; padding:9px 20px;
      background:linear-gradient(135deg,rgba(34,211,238,.18),rgba(168,85,247,.18));
      color:#f8fbff; cursor:pointer; font-size:13px; font-weight:700;
      transition:all .22s; display:inline-flex; align-items:center; gap:7px;
    }
    #runBtn:hover { border-color:rgba(34,211,238,.75); box-shadow:0 0 18px rgba(34,211,238,.2); }
    #runBtn:disabled { opacity:.55; cursor:wait; }

    /* Status badge */
    .badge {
      display:inline-flex; align-items:center; gap:6px;
      border-radius:999px; padding:6px 12px; font-size:12px; font-weight:700;
    }
    .badge-good { color:var(--good); border:1px solid rgba(52,211,153,.45); background:rgba(52,211,153,.1); }
    .badge-warn { color:var(--warn); border:1px solid rgba(251,191,36,.45); background:rgba(251,191,36,.1); }
    .badge-bad  { color:var(--bad);  border:1px solid rgba(251,113,133,.45); background:rgba(251,113,133,.1); animation:bpulse 1.8s infinite; }
    .badge-idle { color:var(--muted);border:1px solid rgba(255,255,255,.15); background:rgba(255,255,255,.05); }
    .badge-run  { color:#93c5fd; border:1px solid rgba(147,197,253,.45); background:rgba(147,197,253,.08); }
    .badge-dot { width:7px; height:7px; border-radius:50%; background:currentColor; box-shadow:0 0 8px currentColor; }
    @keyframes bpulse { 0%,100%{box-shadow:0 0 0 rgba(251,113,133,0)} 50%{box-shadow:0 0 14px rgba(251,113,133,.3)} }

    /* Metric cards */
    .metrics { display:grid; grid-template-columns:repeat(4, minmax(130px,1fr)); gap:12px; }
    .metric {
      border:1px solid rgba(255,255,255,.12); border-radius:16px;
      background:rgba(255,255,255,.05); padding:16px 14px;
      transition:border-color .3s, box-shadow .3s;
    }
    .metric:hover { border-color:rgba(34,211,238,.35); box-shadow:0 0 20px rgba(34,211,238,.08); }
    .metric .label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; }
    .metric .value { font-size:28px; font-weight:800; margin-top:6px; font-variant-numeric:tabular-nums; transition:color .3s; }
    .metric .sub { font-size:11px; color:var(--muted); margin-top:4px; }
    .metric.loading .value { opacity:.35; }

    /* Progress bar */
    .prog-wrap { margin-top:8px; }
    .prog-track { height:5px; background:rgba(255,255,255,.1); border-radius:5px; overflow:hidden;
      border:none !important; box-shadow:none !important; }
    .prog-fill { height:100%; border-radius:5px; width:0%; transition:width .6s cubic-bezier(.2,.8,.2,1); }
    .prog-label { font-size:11px; color:var(--muted); margin-top:5px; }

    /* Test log panel */
    .log-panel {
      border:1px solid rgba(255,255,255,.1); border-radius:16px;
      background:rgba(0,0,0,.35); padding:16px; font-family:'JetBrains Mono',monospace,ui-monospace;
      min-height:180px; max-height:380px; overflow-y:auto;
    }
    .log-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
    .log-title { font-size:11px; color:#93c5fd; text-transform:uppercase; letter-spacing:.08em; font-family:Inter,ui-sans-serif; }
    .log-count { font-size:11px; color:var(--muted); font-family:Inter,ui-sans-serif; }
    .log-line {
      display:flex; align-items:center; gap:10px; padding:5px 0;
      border-bottom:1px solid rgba(255,255,255,.04); font-size:12px;
      opacity:0; transform:translateY(4px); animation:lineIn .18s ease forwards;
    }
    .log-line:last-child { border-bottom:none; }
    @keyframes lineIn { to { opacity:1; transform:translateY(0); } }
    .log-icon { flex-shrink:0; font-size:13px; width:18px; text-align:center; }
    .log-name { flex:1; color:#cbd5e1; font-size:11.5px; word-break:break-word; }
    .log-dur { font-size:11px; color:var(--muted); flex-shrink:0; min-width:46px; text-align:right; }
    .log-pass .log-name { color:#86efac; }
    .log-fail .log-name { color:#fca5a5; }
    .log-skip .log-name { color:var(--muted); }
    .log-run  .log-name { color:#93c5fd; }
    .log-cursor { display:inline-block; width:8px; height:14px; background:#93c5fd;
      animation:blink .7s step-end infinite; vertical-align:middle; margin-left:2px; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

    /* Failures panel */
    .failures-panel { border:1px solid rgba(255,255,255,.1); border-radius:16px; background:rgba(255,255,255,.04); padding:16px; }
    .panel-title { font-size:11px; color:#93c5fd; text-transform:uppercase; letter-spacing:.08em; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
    .failures-list { display:grid; gap:8px; }
    .failure-item {
      display:flex; align-items:flex-start; gap:10px;
      border:1px solid rgba(251,113,133,.28); border-radius:12px;
      padding:10px 12px; background:rgba(251,113,133,.06);
      animation:lineIn .22s ease both;
    }
    .failure-icon { font-size:14px; flex-shrink:0; margin-top:1px; }
    .failure-name { font-size:13px; font-weight:700; color:#fca5a5; word-break:break-word; }
    .failure-err { font-size:11px; color:var(--muted); margin-top:4px; white-space:pre-wrap; word-break:break-word; }
    .all-passed {
      display:flex; align-items:center; gap:10px;
      border:1px solid rgba(52,211,153,.28); border-radius:12px;
      padding:12px 14px; background:rgba(52,211,153,.07); color:#86efac;
      font-weight:700; font-size:13px;
    }

    /* Error banner */
    .error-banner {
      border:1px solid rgba(251,191,36,.35); border-radius:12px;
      padding:12px 14px; background:rgba(251,191,36,.07); color:var(--warn);
      font-size:13px; display:none;
    }

    /* Spinner */
    .spinner {
      width:13px; height:13px; border-radius:50%;
      border:2px solid rgba(255,255,255,.18); border-top-color:#34d399;
      animation:spin .65s linear infinite; flex-shrink:0;
    }
    @keyframes spin { to { transform:rotate(360deg); } }

    /* Last run */
    .last-run { font-size:11px; color:var(--muted); }

    @media(max-width:700px) {
      .metrics { grid-template-columns: repeat(2, 1fr); }
      .top { flex-direction: column; align-items: flex-start; gap: 10px; }
      .top-right { flex-wrap: wrap; }
    }
    @media(max-width:420px) {
      .metrics { grid-template-columns: 1fr; }
      .failure-item { flex-direction: column; gap: 6px; }
    }
  </style>
</head>
<body>
  <main class="shell">

    <!-- Header -->
    <section class="top">
      <div class="top-left">
        <div class="eyebrow">Zero Trust AI Gateway</div>
        <h1>System Self-Test</h1>
      </div>
      <div class="top-right">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/soc">SOC</a>
        <a href="/dashboard/security">Security Suite</a>
        <button id="runBtn"><span id="btnIcon">▶</span><span id="btnText">Run Tests</span></button>
        <span class="badge badge-idle" id="statusBadge"><span class="badge-dot"></span><span id="statusText">Not run</span></span>
        <span class="last-run" id="lastRun"></span>
      </div>
    </section>

    <!-- Error banner -->
    <div class="error-banner" id="errorBanner"></div>

    <!-- Metrics -->
    <section class="metrics">
      <article class="metric loading" id="cardTotal">
        <div class="label">Total Tests</div>
        <div class="value" id="total">—</div>
        <div class="sub" id="subTotal">waiting</div>
      </article>
      <article class="metric loading" id="cardPassed">
        <div class="label">Passed</div>
        <div class="value" id="passed" style="color:var(--good)">—</div>
        <div class="prog-wrap">
          <div class="prog-track"><div class="prog-fill" id="passBar" style="background:var(--good)"></div></div>
          <div class="prog-label" id="passRate">—</div>
        </div>
      </article>
      <article class="metric loading" id="cardFailed">
        <div class="label">Failed</div>
        <div class="value" id="failed" style="color:var(--bad)">—</div>
        <div class="sub" id="subFailed">—</div>
      </article>
      <article class="metric loading" id="cardDur">
        <div class="label">Duration</div>
        <div class="value" id="duration" style="font-size:22px">—</div>
        <div class="sub">seconds</div>
      </article>
    </section>

    <!-- Test log -->
    <section class="log-panel">
      <div class="log-header">
        <div class="log-title">Test Log</div>
        <div class="log-count" id="logCount"></div>
      </div>
      <div id="logLines">
        <div class="log-line log-run">
          <span class="log-icon">◌</span>
          <span class="log-name">Press "Run Tests" to execute the live self-test suite<span class="log-cursor"></span></span>
        </div>
      </div>
    </section>

    <!-- Failures -->
    <section class="failures-panel">
      <div class="panel-title">
        <span id="failuresPanelIcon">⚑</span>
        <span id="failuresPanelTitle">Failures</span>
      </div>
      <div id="failures" class="failures-list">
        <div class="log-line" style="opacity:.5;font-size:13px;color:var(--muted)">No results yet. Run the test suite above.</div>
      </div>
    </section>

  </main>

  <script>
    const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/testing";
    const H = () => ({ Authorization: "Bearer " + token, "Content-Type": "application/json" });
    const $ = (id) => document.getElementById(id);

    function esc(v) {
      return String(v ?? "").replace(/[&<>"']/g, (c) =>
        ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;" }[c]));
    }

    function animCount(id, target, decimals) {
      const el = $(id); if (!el) return;
      const from = parseFloat(el.textContent) || 0;
      const dur = 420, start = performance.now();
      const tick = (now) => {
        const p = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        const val = from + (target - from) * eased;
        el.textContent = decimals ? val.toFixed(decimals) : Math.round(val);
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }

    function setLoading(yes) {
      ["cardTotal","cardPassed","cardFailed","cardDur"].forEach(id => {
        $(id).classList.toggle("loading", yes);
      });
    }

    function setBadge(state) {
      const el = $("statusBadge");
      const txt = $("statusText");
      el.className = "badge";
      if (state === "running") {
        el.classList.add("badge-run"); txt.textContent = "Running…";
      } else if (state === "all_pass") {
        el.classList.add("badge-good"); txt.textContent = "All Passed";
      } else if (state === "partial") {
        el.classList.add("badge-warn"); txt.textContent = "Partial Failure";
      } else if (state === "all_fail") {
        el.classList.add("badge-bad"); txt.textContent = "Tests Failed";
      } else if (state === "empty") {
        el.classList.add("badge-idle"); txt.textContent = "No tests run";
      } else {
        el.classList.add("badge-idle"); txt.textContent = "Not run";
      }
    }

    function addLogLine(name, state, delay, durMs) {
      const icon  = state === "pass" ? "✓" : state === "fail" ? "✗" : state === "skip" ? "⊘" : "◌";
      const cls   = state === "pass" ? "log-pass" : state === "fail" ? "log-fail" : state === "skip" ? "log-skip" : "log-run";
      // Show duration in ms if available
      const durTxt = (durMs != null && durMs >= 0) ? durMs + "ms" : "";
      // Strip file path prefix for display, keep function name
      const shortName = name.replace(/^[^:]+::/g, "");
      const line  = document.createElement("div");
      line.className = `log-line ${cls}`;
      line.style.animationDelay = delay + "ms";
      line.title = name; // full node ID on hover
      line.innerHTML = `<span class="log-icon">${icon}</span><span class="log-name">${esc(shortName)}</span><span class="log-dur">${esc(durTxt)}</span>`;
      $("logLines").appendChild(line);
      const panel = $("logLines").closest(".log-panel");
      if (panel) panel.scrollTop = panel.scrollHeight;
    }

    function renderResult(data) {
      const total   = Number(data.total    ?? 0);
      const passed  = Number(data.passed   ?? 0);
      const failed  = Number(data.failed   ?? 0);
      const dur     = Number(data.duration ?? 0);
      const rate    = total > 0 ? Math.round((passed / total) * 100) : 0;

      setLoading(false);
      animCount("total",    total);
      animCount("passed",   passed);
      animCount("failed",   failed);
      animCount("duration", dur, 3);

      $("subTotal").textContent  = total + " test" + (total !== 1 ? "s" : "") + " executed";
      $("subFailed").textContent = failed > 0 ? failed + " need attention" : "none";
      $("passRate").textContent  = rate + "% pass rate";
      setTimeout(() => { $("passBar").style.width = rate + "%"; }, 120);

      const state = total === 0 ? "empty" : failed === 0 ? "all_pass" : failed < total ? "partial" : "all_fail";
      setBadge(state);
      $("lastRun").textContent = "Last run: " + new Date().toLocaleTimeString();

      // Render test log with real node IDs
      $("logLines").innerHTML = "";
      const tests = Array.isArray(data.tests) ? data.tests : [];
      tests.forEach((t, i) => {
        addLogLine(t.test || "unknown", t.state || "run", i * 30, t.duration_ms ?? null);
      });

      // Update log count
      $("logCount").textContent = total > 0 ? total + " tests" : "";

      // Summary line
      if (tests.length > 0) {
        setTimeout(() => {
          const sumLine = document.createElement("div");
          sumLine.className = "log-line";
          sumLine.style.borderTop = "1px solid rgba(255,255,255,.1)";
          sumLine.style.marginTop = "6px";
          sumLine.style.paddingTop = "10px";
          const col = failed === 0 ? "var(--good)" : failed < total ? "var(--warn)" : "var(--bad)";
          sumLine.innerHTML = `<span class="log-icon" style="color:${col}">⬡</span><span class="log-name" style="color:${col};font-weight:700">Suite complete — ${passed}/${total} passed in ${dur.toFixed(3)}s</span>`;
          $("logLines").appendChild(sumLine);
        }, tests.length * 30 + 80);
      }

      // Failures panel
      const failures = Array.isArray(data.failures) ? data.failures : [];
      if (failures.length === 0) {
        $("failuresPanelTitle").textContent = "Failures";
        $("failures").innerHTML = `
          <div class="all-passed">
            <span style="font-size:18px">✓</span>
            All ${total} tests passed — system is healthy
          </div>`;
      } else {
        $("failuresPanelTitle").textContent = "Failures (" + failures.length + ")";
        $("failures").innerHTML = failures.map((f, i) => `
          <div class="failure-item" style="animation-delay:${i * 60}ms">
            <span class="failure-icon">✗</span>
            <div style="min-width:0;flex:1">
              <div class="failure-name">${esc(f.test)}</div>
              <div class="failure-err">${esc(f.error || "Test failed")}</div>
            </div>
          </div>`).join("");
      }
    }

    async function runTests() {
      const btn = $("runBtn");
      btn.disabled = true;
      $("btnIcon").innerHTML = `<span class="spinner"></span>`;
      $("btnText").textContent = "Running…";
      setLoading(true);
      setBadge("running");
      $("errorBanner").style.display = "none";

      $("logLines").innerHTML = "";
      $("logCount").textContent = "";
      addLogLine("Launching self-test suite…", "run", 0);

      try {
        const r = await fetch(`${api}/testing/run-soc-tests`, {
          headers: H(),
          signal: AbortSignal.timeout(180000), // 3 min max
        });
        if (!r.ok) {
          const txt = await r.text().catch(() => r.status);
          throw new Error(`HTTP ${r.status}: ${txt}`);
        }
        const data = await r.json();
        renderResult(data);
      } catch (err) {
        setLoading(false);
        setBadge("idle");
        $("errorBanner").textContent = "Test run failed: " + (err.message || String(err));
        $("errorBanner").style.display = "block";
        $("logLines").innerHTML = "";
        addLogLine("Test run error — check server logs", "fail", 0);
        $("failures").innerHTML = `<div class="failure-item"><span class="failure-icon">✗</span><div><div class="failure-name">Runner Error</div><div class="failure-err">${esc(String(err))}</div></div></div>`;
      }

      btn.disabled = false;
      $("btnIcon").textContent = "▶";
      $("btnText").textContent = "Run Tests";
    }

    $("runBtn").addEventListener("click", runTests);

    window.addEventListener("DOMContentLoaded", () => {
      setTimeout(runTests, 600);
    });
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
