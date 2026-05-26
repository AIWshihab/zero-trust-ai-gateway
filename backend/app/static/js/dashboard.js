(function () {
  var tok = sessionStorage.getItem("zta_token");
  if (!tok) { location.href = "/login?next=/dashboard"; return; }

  var API = "/api/v1";
  var $ = function(id) { return document.getElementById(id); };

  /* decode JWT for username + role — no API call */
  var jwt = (function() {
    try { return JSON.parse(atob(tok.split(".")[1].replace(/-/g,"+").replace(/_/g,"/"))); }
    catch(e) { return {}; }
  })();
  var username = jwt.sub || "";
  var isAdmin  = (jwt.scopes || []).indexOf("admin") !== -1;

  /* ── fetch with 12-second timeout; 401/403 → login ── */
  function api(path) {
    return new Promise(function(resolve, reject) {
      var ctrl = new AbortController();
      var tid  = setTimeout(function() { ctrl.abort(); reject(new Error("timeout")); }, 12000);
      fetch(API + path, { headers: { Authorization: "Bearer " + tok }, signal: ctrl.signal })
        .then(function(res) {
          clearTimeout(tid);
          if (res.status === 401 || res.status === 403) {
            sessionStorage.removeItem("zta_token");
            location.href = "/login?next=/dashboard";
            reject(new Error("auth")); return;
          }
          if (!res.ok) { reject(new Error("HTTP " + res.status)); return; }
          resolve(res.json());
        })
        .catch(function(e) { clearTimeout(tid); reject(e); });
    });
  }

  /* ── helpers ── */
  function esc(s) {
    return String(s || "—").replace(/[&<>"']/g, function(c) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }
  function pct(v, decimals)  { return v != null ? (Math.round(v * 100 * (decimals ? 10 : 1)) / (decimals ? 10 : 1)) + "%" : "—"; }
  function rcol(v) { return v >= .75 ? "var(--red)" : v >= .4 ? "var(--amber)" : "var(--green)"; }
  function age(iso) {
    if (!iso) return "—";
    var s = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (s < 60)    return s + "s ago";
    if (s < 3600)  return Math.floor(s/60) + "m ago";
    if (s < 86400) return Math.floor(s/3600) + "h ago";
    return Math.floor(s/86400) + "d ago";
  }
  function fmtUptime(sec) {
    if (sec < 60) return sec + "s";
    if (sec < 3600) return Math.floor(sec/60) + "m";
    if (sec < 86400) return Math.floor(sec/3600) + "h " + Math.floor((sec%3600)/60) + "m";
    return Math.floor(sec/86400) + "d " + Math.floor((sec%86400)/3600) + "h";
  }
  function setv(id, val, cls) {
    var el = $(id); if (!el) return;
    el.textContent = String(val != null ? val : "—");
    el.classList.remove("spin");
    if (cls) el.style.color = cls;
  }
  function setDot(id, color) {
    var el = $(id); if (!el) return;
    el.className = "dot";
    el.style.cssText = "background:" + color + (color === "var(--green)" ? ";box-shadow:0 0 6px var(--green)" : color === "var(--cyan)" ? ";box-shadow:0 0 6px var(--cyan)" : "") + ";width:7px;height:7px;border-radius:50%;flex-shrink:0";
  }

  /* ════════════════════════════════════════════
     1. CORE METRICS + RUNTIME READINESS
  ════════════════════════════════════════════ */
  function loadMetrics() {
    Promise.allSettled([
      api("/monitoring/metrics"),
      api("/models/runtime-readiness")
    ]).then(function(res) {
      /* metrics */
      if (res[0].status === "fulfilled") {
        var m   = res[0].value;
        var blk = m.blocked_requests    || 0;
        var chl = m.challenged_requests || 0;
        var tot = m.total_requests      || 0;
        var risk = m.avg_prompt_risk_score != null ? m.avg_prompt_risk_score : 0;

        setv("sModels",  m.active_models != null ? m.active_models : 0);
        $("sModelsSub").textContent = (m.total_models || 0) + " registered total";
        setv("sTotal", tot);
        $("sTotalSub").textContent = m.avg_latency_ms ? "avg " + Math.round(m.avg_latency_ms) + "ms latency" : "";
        setv("sBlocked", blk + chl, rcol(tot > 0 ? (blk+chl)/tot : 0));
        $("sBlockedSub").textContent = tot > 0 ? Math.round(((blk+chl)/tot)*100) + "% of total" : "none blocked";
        setv("sRisk", pct(risk), rcol(risk));
        $("sRiskSub").textContent = risk >= .75 ? "⚠ Elevated" : risk >= .4 ? "↑ Moderate" : "✓ Normal";

        $("dAllow").textContent = m.allowed_requests || 0;
        $("dChal").textContent  = chl;
        $("dBlock").textContent = blk;
        $("dRate").textContent  = (m.block_rate || 0) + "%";
        var dd = $("decDot"); dd.classList.remove("off");

        setv("pLatency",  m.avg_latency_ms  != null ? Math.round(m.avg_latency_ms) + "ms" : "—");
        setv("pSecScore", m.avg_security_score != null ? pct(m.avg_security_score, 1) : "—");
      }

      /* runtime readiness */
      if (res[1].status === "fulfilled") {
        var list  = res[1].value || [];
        var ready = list.filter(function(m) { return m.runtime_ready !== false; }).length;
        setv("sReady", ready + "/" + list.length);
        var sub = ready === list.length && list.length > 0 ? "All ready"
                : ready === 0 && list.length > 0 ? "None ready"
                : list.length === 0 ? "Register a model"
                : (list.length - ready) + " need attention";
        $("sReadySub").textContent = sub;
        renderModels(list);
      } else {
        setv("sReady", "—");
        $("mList").innerHTML = '<div class="empty-note">Could not load model data. <a href="/dashboard/models">Check models →</a></div>';
      }
    });
  }

  function renderModels(list) {
    if (!list.length) {
      $("mList").innerHTML = '<div class="empty-note">No models registered. <a href="/dashboard/models">Register your first model →</a></div>';
      return;
    }
    $("mList").innerHTML = list.map(function(m) {
      var r       = m.runtime_ready !== false;
      var partial = !r && (m.model_loaded || m.endpoint_reachable);
      var cls     = r ? "ready" : partial ? "partial" : "offline";
      var lbl     = r ? "Ready" : partial ? "Partial" : "Offline";
      return '<div class="mitem" onclick="location.href=\'/dashboard/models\'">' +
        '<span class="mdot ' + cls + '"></span>' +
        '<span class="mname" title="' + esc(m.name) + '">' + esc(m.name) + '</span>' +
        '<span class="mprov">' + esc(m.provider_name || m.hf_model_id || "") + '</span>' +
        '<span class="mbadge ' + cls + '">' + lbl + '</span>' +
        '</div>';
    }).join("");
  }

  /* ════════════════════════════════════════════
     2. SYSTEM HEALTH + ZTA + CONTROLS + RULES
  ════════════════════════════════════════════ */
  function loadSystemStatus() {
    Promise.allSettled([
      api("/monitoring/health"),
      api("/monitoring/zta/status"),
      api("/security/controls"),
      api("/security/detection-rules")
    ]).then(function(res) {
      /* health */
      if (res[0].status === "fulfilled") {
        var h   = res[0].value;
        var st  = h.status || "unknown";
        var col = st === "healthy" ? "var(--green)" : st === "degraded" ? "var(--amber)" : "var(--red)";
        setDot("healthDot", col);
        setv("healthStatus", st.charAt(0).toUpperCase() + st.slice(1), col);
        setv("uptime", fmtUptime(h.uptime_seconds || 0));
        setv("activeUsers", h.active_users != null ? h.active_users : "—");
      } else {
        setv("healthStatus", "Unknown");
      }

      /* ZTA status */
      if (res[1].status === "fulfilled") {
        var z = res[1].value;
        var en = z.enabled !== false;
        setDot("ztaDot", en ? "var(--green)" : "var(--amber)");
        var modeText = en ? "Strict" : "Permissive";
        setv("ztaMode", modeText, en ? "var(--green)" : "var(--amber)");
        setv("pZtaMode", en ? "Strict enforcement" : "⚠ Permissive (disabled)", en ? "var(--green)" : "var(--amber)");
      } else {
        setv("ztaMode", "Unknown");
      }

      /* controls */
      if (res[2].status === "fulfilled") {
        var controls = res[2].value || [];
        var active = controls.filter(function(c) { return c.enabled; }).length;
        setv("controlsCount", active);
      } else {
        setv("controlsCount", "—");
      }

      /* detection rules */
      if (res[3].status === "fulfilled") {
        var rules = res[3].value || [];
        var activeR = rules.filter(function(r) { return r.enabled; }).length;
        setv("rulesCount", activeR);
      } else {
        setv("rulesCount", "—");
      }
    });
  }

  /* ════════════════════════════════════════════
     3. USER TRUST + RATE PROFILE
  ════════════════════════════════════════════ */
  function loadUserPosture() {
    if (!username) { return; }
    Promise.allSettled([
      api("/monitoring/users/" + username + "/trust"),
      api("/monitoring/users/" + username + "/rate")
    ]).then(function(res) {
      /* trust */
      if (res[0].status === "fulfilled") {
        var t = res[0].value;
        var score = t.trust_score != null ? t.trust_score : 1.0;
        var level = t.trust_level || "unknown";
        var col   = score >= 0.7 ? "var(--green)" : score >= 0.4 ? "var(--amber)" : "var(--red)";
        setDot("trustDot", col);
        setv("myTrust",  pct(score), col);
        setv("pTrust",   pct(score), col);
        setv("pLevel",   level.charAt(0).toUpperCase() + level.slice(1), col);
        setv("pReqs",    t.total_requests     != null ? t.total_requests     : 0);
        setv("pBlocked", t.blocked_requests   != null ? t.blocked_requests   : 0, t.blocked_requests > 0 ? "var(--red)" : "var(--green)");
        $("pTrustPct").textContent = pct(score);
        var bar = $("pTrustBar");
        bar.style.width    = Math.round(score * 100) + "%";
        bar.style.background = col;
      } else {
        setv("myTrust", "—");
        setv("pTrust",  "—");
      }

      /* rate */
      if (res[1].status === "fulfilled") {
        var r = res[1].value;
        setv("pRate", r.requests_per_minute != null ? r.requests_per_minute.toFixed(1) + " / " + r.limit_per_minute.toFixed(0) : "—");
        var limited = r.is_rate_limited || r.penalty_active;
        setv("pRateLtd", limited ? "⚠ Rate limited" : "Normal", limited ? "var(--amber)" : "var(--green)");
      } else {
        setv("pRate",    "—");
        setv("pRateLtd", "—");
      }
    });
  }

  /* ════════════════════════════════════════════
     4. ATTACK HEATMAP
  ════════════════════════════════════════════ */
  function loadHeatmap() {
    api("/monitoring/soc/threat-heatmap").then(function(data) {
      var cells = (data.cells || []).slice(0, 7);
      if (!cells.length) {
        $("dBars").innerHTML = '<div class="empty-note">No attack sequence events yet.</div>';
        return;
      }
      var max = Math.max.apply(null, [1].concat(cells.map(function(c) { return c.count || 0; })));
      $("dBars").innerHTML = cells.map(function(c) {
        var w = Math.max(3, ((c.count || 0) / max) * 100);
        return '<div class="bar-r"><span>' + esc(c.attack_stage) + '</span>' +
          '<div class="track"><div class="fill" style="width:' + w + '%"></div></div>' +
          '<b>' + (c.count || 0) + '</b></div>';
      }).join("");
    }).catch(function() {
      $("dBars").innerHTML = '<div class="empty-note">No attack timeline data yet.</div>';
    });
  }

  /* ════════════════════════════════════════════
     5. ACTIVE ALERTS
  ════════════════════════════════════════════ */
  function loadAlerts() {
    api("/monitoring/soc/alerts").then(function(data) {
      var alerts = (data.alerts || []).slice(0, 5);
      if (!alerts.length) return;
      $("alertsSection").style.display = "block";
      $("alertsList").innerHTML = alerts.map(function(a) {
        var sev = a.severity || "medium";
        return '<div class="alert-card ' + sev + '">' +
          '<span class="alert-sev ' + sev + '">' + sev.toUpperCase() + '</span>' +
          '<div class="alert-msg"><span class="alert-type">' + esc(a.type || "alert") + '</span>' + esc(a.message || "") + '</div>' +
          '</div>';
      }).join("");
    }).catch(function() { /* no alerts, stay hidden */ });
  }

  /* ════════════════════════════════════════════
     6. LOG FEED + SSE
  ════════════════════════════════════════════ */
  var lastId  = 0;
  var sseCtrl = null;

  function mkEntry(l) {
    var d    = l.decision === "block" ? "block" : l.decision === "challenge" ? "challenge" : "allow";
    var risk = l.prompt_risk_score != null ? l.prompt_risk_score : l.security_score;
    var col  = risk != null ? rcol(risk) : "var(--muted)";
    return '<div class="fentry">' +
      '<span class="fdot ' + d + '"></span>' +
      '<span class="ftime">' + age(l.timestamp) + '</span>' +
      '<span class="fwho">' + esc(l.username) + ' &middot; ' + esc(l.model_name) + '</span>' +
      '<span class="fdec ' + d + '">' + d.toUpperCase() + '</span>' +
      '<span class="frisk" style="color:' + col + '">' + pct(risk) + '</span>' +
      '</div>';
  }

  function loadFeed() {
    api("/monitoring/logs?limit=20").then(function(data) {
      var logs = data.logs || [];
      if (logs.length) {
        $("liveFeed").innerHTML = logs.map(mkEntry).join("");
        lastId = Math.max.apply(null, logs.map(function(l) { return l.id || 0; }));
      }
      $("feedSt").textContent = logs.length + (logs.length === 1 ? " entry" : " entries") + " loaded";
    }).catch(function() {
      $("feedSt").textContent = "Could not load logs";
    }).finally(function() {
      connectSSE();
    });
  }

  function connectSSE() {
    if (sseCtrl) { try { sseCtrl.abort(); } catch(e) {} }
    sseCtrl = new AbortController();
    fetch(API + "/monitoring/logs/stream?since_id=" + lastId, {
      headers: { Authorization: "Bearer " + tok }, signal: sseCtrl.signal
    }).then(function(res) {
      if (!res.ok) { schedReconnect(4000); return; }
      $("feedDot").classList.remove("off");
      $("feedSt").textContent = "Live stream connected";
      var reader = res.body.getReader();
      var dec    = new TextDecoder();
      var buf    = "";
      (function read() {
        reader.read().then(function(chunk) {
          if (chunk.done) { schedReconnect(2000); return; }
          buf += dec.decode(chunk.value, { stream: true });
          var parts = buf.split("\n");
          buf = parts.pop();
          parts.forEach(function(line) {
            if (line.indexOf("data: ") !== 0) return;
            try {
              var e = JSON.parse(line.slice(6));
              if (!e || !e.id) return;
              if (e.id > lastId) lastId = e.id;
              var feed  = $("liveFeed");
              var empty = feed.querySelector(".fempty");
              if (empty) feed.innerHTML = "";
              feed.insertAdjacentHTML("afterbegin", mkEntry(e));
              var all = feed.querySelectorAll(".fentry");
              if (all.length > 25) all[all.length - 1].remove();
              $("feedSt").textContent = "Live · " + new Date().toLocaleTimeString();
              /* also refresh stats on new entry */
              loadMetrics();
              loadUserPosture();
            } catch(ex) {}
          });
          read();
        }).catch(function(err) { if (err && err.name !== "AbortError") schedReconnect(3000); });
      })();
    }).catch(function(err) { if (err && err.name !== "AbortError") schedReconnect(4000); });
  }

  function schedReconnect(ms) {
    $("feedDot").classList.add("off");
    $("feedSt").textContent = "Reconnecting…";
    setTimeout(connectSSE, ms);
  }

  /* ════════════════════════════════════════════
     7. MODULES (instant, no API)
  ════════════════════════════════════════════ */
  function renderModules() {
    var MODS = [
      { href:"/dashboard/chat",             cat:"Inference",     name:"Secure AI Inference",   desc:"Evaluate prompts through the behaviour-aware Zero Trust gateway with live risk scores, decision traces, and output guard results." },
      { href:"/dashboard/models",           cat:"Models",        name:"Model Registry",         desc:"Register model endpoints, inspect runtime readiness, and review model security posture before inference is permitted." },
      { href:"/dashboard/security-monitor", cat:"Observability", name:"Security Monitoring",    desc:"Real-time allow, challenge, and block decisions with user trust changes, risk events, and structured decision traces." },
      { href:"/dashboard/policy",           cat:"Policy",        name:"Policy Control Plane",   desc:"Configure enforcement mode, risk thresholds, detection rules, output guard settings, and explainability controls." },
      { href:"/dashboard/research",         cat:"Research",      name:"Replayable Evaluation",  desc:"Run behavioural test suites, policy replay, counterfactuals, model comparison, and control-effectiveness analysis from audit evidence." },
      { href:"/dashboard/account",          cat:"Trust",         name:"Account & Trust",        desc:"View trust score, rate profile, owned models, API usage summary, device sessions, and recent security outcomes." }
    ];
    $("mGrid").innerHTML = MODS.map(function(m) {
      return '<article class="mod" data-href="' + m.href + '">' +
        '<div class="mod-cat">' + m.cat + '</div>' +
        '<div class="mod-name">' + m.name + '</div>' +
        '<div class="mod-desc">' + m.desc + '</div>' +
        '<div class="mod-btn">Open ' + m.name + ' &rarr;</div>' +
        '</article>';
    }).join("");
    document.querySelectorAll(".mod[data-href], .stat[data-href]").forEach(function(el) {
      el.addEventListener("click", function() { location.href = el.dataset.href; });
    });
  }

  /* ════════════════════════════════════════════
     BOOT — all sections fire independently
  ════════════════════════════════════════════ */
  renderModules();        /* instant — no API */
  loadMetrics();          /* /monitoring/metrics + /models/runtime-readiness */
  loadSystemStatus();     /* /monitoring/health + /monitoring/zta/status + /security/controls + /security/detection-rules */
  loadUserPosture();      /* /monitoring/users/{me}/trust + /monitoring/users/{me}/rate */
  loadHeatmap();          /* /monitoring/soc/threat-heatmap */
  loadAlerts();           /* /monitoring/soc/alerts */
  loadFeed();             /* /monitoring/logs then connectSSE() */

  /* refresh key metrics every 10 seconds */
  setInterval(function() {
    loadMetrics();
    loadSystemStatus();
    loadUserPosture();
    loadHeatmap();
    loadAlerts();
  }, 10000);
})();