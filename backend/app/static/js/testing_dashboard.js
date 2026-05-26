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