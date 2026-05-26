const api = "/api/v1";
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/security-monitor";
    const headers = () => ({ Authorization: `Bearer ${token}` });

    async function get(path) {
      const res = await fetch(path, { headers: headers() });
      const text = await res.text();
      let data; try { data = text ? JSON.parse(text) : {}; } catch { data = {}; }
      if (!res.ok) throw new Error((data.detail && data.detail.message) || data.detail || `Request failed (${res.status})`);
      return data;
    }
    let lastHash = "";
    const orderWeight = (s) => { const v = String(s||"").toLowerCase(); return v==="critical"||v==="high"?0:v==="warning"||v==="medium"?1:2; };
    function sevClass(s) { const v = String(s||"").toLowerCase(); return v==="critical"||v==="high"?"high":v==="warning"||v==="medium"?"medium":"low"; }

    function drawTimeline(events) {
      const canvas = document.getElementById("timelineCanvas");
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const points = (events || []).slice(0, 60).reverse();
      if (!points.length) {
        ctx.fillStyle = "rgba(124,132,153,.8)";
        ctx.font = "22px Inter, sans-serif";
        ctx.fillText("No attack sequence events yet", 40, 80);
        ctx.font = "15px Inter, sans-serif";
        ctx.fillText("Send chat or gateway requests to generate telemetry.", 40, 110);
        return;
      }
      const values = points.map((e) => Number(e.sequence_severity || 0));
      const w = canvas.width, h = canvas.height, pad = 40;
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, "rgba(0,212,255,.28)");
      grad.addColorStop(1, "rgba(0,212,255,0)");
      ctx.beginPath();
      values.forEach((v, i) => {
        const x = pad + (i / Math.max(1, values.length - 1)) * (w - pad * 2);
        const y = h - pad - (Math.max(0, Math.min(1, v)) * (h - pad * 2));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.lineTo(pad + (values.length-1)/(Math.max(1,values.length-1))*(w-pad*2), h-pad);
      ctx.lineTo(pad, h-pad);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.beginPath();
      values.forEach((v, i) => {
        const x = pad + (i / Math.max(1, values.length - 1)) * (w - pad * 2);
        const y = h - pad - (Math.max(0, Math.min(1, v)) * (h - pad * 2));
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = "rgba(0,212,255,.85)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    function setLoading() {
      document.getElementById("alerts").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>`;
      document.getElementById("heatmap").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div>`;
      document.getElementById("anomalyRows").innerHTML = `<tr><td colspan="3"><div class="skeleton"></div></td></tr>`;
    }
    function setStatus(text, mode = "live") {
      const el = document.getElementById("liveStatus");
      if (!el) return;
      if (mode === "error") {
        el.innerHTML = `<span style="color:var(--red);font-size:12px">${text}</span>`;
      } else {
        el.innerHTML = `<span class="live-dot"></span>${text}`;
      }
    }
    function showError(err) {
      const message = String(err?.message || err || "Monitoring data unavailable");
      setStatus("Live data unavailable", "error");
      document.getElementById("alerts").innerHTML = `<div class="state">Could not load live monitoring data: ${message}</div>`;
      document.getElementById("heatmap").innerHTML = `<div class="state">Live endpoint failed. Fix the endpoint or generate real telemetry.</div>`;
      document.getElementById("anomalyRows").innerHTML = `<tr><td colspan="3" style="color:var(--muted)">Unavailable: ${message}</td></tr>`;
    }
    function animatedSet(id, next) {
      const el = document.getElementById(id);
      if (!el) return;
      const prev = Number(el.textContent || 0);
      const target = Number(next || 0);
      if (Number.isNaN(prev) || Number.isNaN(target) || prev === target) { el.textContent = String(next); return; }
      const start = performance.now(), dur = 220;
      const tick = (t) => {
        const p = Math.min(1, (t - start) / dur);
        el.textContent = String(Math.round(prev + (target - prev) * p));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }

    async function load() {
      const [metrics, timeline, heatmap, anomalies, alerts] = await Promise.all([
        get(`${api}/monitoring/metrics`),
        get(`${api}/monitoring/soc/attack-timeline?limit=120`),
        get(`${api}/monitoring/soc/threat-heatmap`),
        get(`${api}/monitoring/soc/user-anomalies`),
        get(`${api}/monitoring/soc/alerts`),
      ]);

      const currentHash = JSON.stringify({ metrics, timeline, heatmap, anomalies, alerts });
      if (currentHash === lastHash) return;
      lastHash = currentHash;

      const events = timeline.events || [];
      const highRisk = events.filter((e) => Number(e.sequence_severity || 0) >= 0.7).length;
      animatedSet("kpiAttacks", events.length);
      animatedSet("kpiBlocked", metrics.blocked_requests ?? events.filter((e) => String(e.decision || "").toLowerCase() === "block").length);
      animatedSet("kpiHighRisk", highRisk);
      animatedSet("kpiTotal", metrics.total_requests ?? 0);
      animatedSet("kpiAllowed", metrics.allowed_requests ?? 0);
      document.getElementById("kpiAvgRisk").textContent = `${Math.round(Number(metrics.avg_prompt_risk_score || 0) * 100)}%`;

      drawTimeline(events);

      const max = Math.max(1, ...((heatmap.cells || []).map((c) => Number(c.count || 0))));
      document.getElementById("heatmap").innerHTML = (heatmap.cells || []).slice(0, 12).map((c) => {
        const ratio = Number(c.count || 0) / max;
        const alpha = (0.12 + ratio * 0.55).toFixed(2);
        return `<div class="heat-cell fade" style="background:rgba(255,77,109,${alpha});border-color:rgba(255,77,109,.25)"><div class="label">${c.attack_stage}</div><strong>${c.count}</strong><div class="label">model ${c.model_id ?? "-"}</div></div>`;
      }).join("") || `<div class="state">No live threat events recorded yet.</div>`;

      document.getElementById("anomalyRows").innerHTML = (anomalies.anomalies || []).map((a) =>
        `<tr class="fade"><td>${a.username}</td><td>${Number(a.trust_score || 0).toFixed(2)}</td><td style="color:var(--muted)">${(a.anomaly_flags || []).join(", ")}</td></tr>`
      ).join("") || `<tr><td colspan="3" style="color:var(--muted);padding:12px">No anomalies</td></tr>`;

      const sorted = (alerts.alerts || []).slice(0, 60).sort((a, b) => orderWeight(a.severity) - orderWeight(b.severity));
      document.getElementById("alerts").innerHTML = sorted.map((a) =>
        `<div class="event-item fade"><div class="item-row"><span class="badge ${sevClass(a.severity)}">${a.severity || "info"}</span><b>${a.type || "alert"}</b></div><div class="item-meta">${a.message || ""}</div><div class="item-meta">${a.timestamp || ""}</div></div>`
      ).join("") || `<div class="state">No live alerts from current telemetry.</div>`;

      setStatus(`Live DB · updated ${new Date().toLocaleTimeString([], { hour:"2-digit", minute:"2-digit", second:"2-digit" })}`);
    }

    let timer = null;
    async function refreshNow() {
      document.getElementById("refreshBtn").disabled = true;
      try { await load(); }
      catch (err) { showError(err); }
      finally { document.getElementById("refreshBtn").disabled = false; }
    }
    function boot() {
      setLoading();
      refreshNow();
      timer = setInterval(refreshNow, 2500);
    }
    document.getElementById("refreshBtn").addEventListener("click", refreshNow);
    window.addEventListener("beforeunload", () => { if (timer) clearInterval(timer); });
    boot();