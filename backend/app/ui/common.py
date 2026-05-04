CYBER_UI_CSS = """

    /* Shared premium AI security UI primitives. These classes intentionally
       decorate the existing HTML structure without changing data flow. */
    :root {
      --zt-bg: #050505;
      --zt-panel: rgba(255, 255, 255, .055);
      --zt-panel-strong: rgba(255, 255, 255, .09);
      --zt-border: rgba(255, 255, 255, .11);
      --zt-border-hot: rgba(34, 211, 238, .46);
      --zt-text: #f8fbff;
      --zt-muted: #9ca8bd;
      --zt-cyan: #22d3ee;
      --zt-purple: #a855f7;
      --zt-blue: #3b82f6;
      --zt-green: #34d399;
      --zt-yellow: #fbbf24;
      --zt-red: #fb7185;
      --zt-radius: 24px;
      --zt-fast: 220ms cubic-bezier(.2, .8, .2, 1);
      --zt-sidebar-w: 248px;
      --zt-topbar-h: 60px;
    }
    html { background: var(--zt-bg); }
    body {
      background:
        radial-gradient(circle at 16% 10%, rgba(34, 211, 238, .18), transparent 32%),
        radial-gradient(circle at 78% 4%, rgba(168, 85, 247, .22), transparent 30%),
        radial-gradient(circle at 62% 88%, rgba(59, 130, 246, .12), transparent 34%),
        linear-gradient(135deg, #06111f 0%, #160724 44%, #050505 100%) !important;
      color: var(--zt-text) !important;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background-image:
        linear-gradient(rgba(34,211,238,.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(168,85,247,.08) 1px, transparent 1px) !important;
      background-size: 72px 72px !important;
      opacity: .42 !important;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.82), rgba(0,0,0,.08)) !important;
    }
    body::after {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background:
        linear-gradient(110deg, transparent 0 36%, rgba(34,211,238,.06) 46%, transparent 56%),
        linear-gradient(290deg, transparent 0 54%, rgba(168,85,247,.06) 62%, transparent 72%) !important;
      animation: ztSweep 9s ease-in-out infinite alternate !important;
      opacity: .75 !important;
    }
    .shell, .app { position: relative; z-index: 1; animation: ztFadeIn .28s ease both; }
    body.zt-with-shell .shell,
    body.zt-with-shell .app {
      margin-left: calc(var(--zt-sidebar-w) + 12px) !important;
      margin-top: calc(var(--zt-topbar-h) + 14px) !important;
      width: calc(100% - var(--zt-sidebar-w) - 24px) !important;
    }
    body.zt-with-shell .app {
      height: calc(100vh - var(--zt-topbar-h) - 24px) !important;
    }
    .zt-sidebar {
      position: fixed;
      left: 12px;
      top: 12px;
      bottom: 12px;
      width: var(--zt-sidebar-w);
      z-index: 20;
      border: 1px solid var(--zt-border);
      border-radius: 22px;
      background: rgba(7, 12, 22, .72);
      backdrop-filter: blur(14px);
      box-shadow: 0 20px 60px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.08);
      display: grid;
      grid-template-rows: auto 1fr auto;
      padding: 14px 10px;
      gap: 12px;
    }
    .zt-brand {
      padding: 6px 10px 10px;
      border-bottom: 1px solid rgba(255,255,255,.08);
    }
    .zt-brand b {
      display: block;
      font-size: 13px;
      color: #c4b5fd;
      letter-spacing: .02em;
    }
    .zt-brand span {
      display: block;
      color: var(--zt-muted);
      font-size: 11px;
      margin-top: 4px;
    }
    .zt-nav { display: grid; gap: 6px; align-content: start; padding: 0 4px; }
    .zt-nav a {
      display: flex;
      align-items: center;
      gap: 9px;
      border-radius: 12px !important;
      padding: 9px 10px !important;
      font-size: 13px;
      border: 1px solid rgba(255,255,255,.1) !important;
      background: rgba(255,255,255,.03) !important;
      box-shadow: none !important;
      transform: none !important;
      text-decoration: none;
    }
    .zt-nav a.zt-active {
      border-color: rgba(34,211,238,.45) !important;
      background: rgba(34,211,238,.16) !important;
      box-shadow: 0 0 24px rgba(34,211,238,.15) !important;
    }
    .zt-status {
      margin: 0 4px;
      padding: 10px;
      border-top: 1px solid rgba(255,255,255,.08);
      display: grid;
      gap: 8px;
    }
    .zt-status .zt-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 6px;
      box-shadow: 0 0 14px currentColor;
    }
    .zt-status .good { color: var(--zt-green); }
    .zt-status .warn { color: var(--zt-yellow); }
    .zt-status .bad { color: var(--zt-red); }
    .zt-topbar {
      position: fixed;
      left: calc(var(--zt-sidebar-w) + 24px);
      right: 12px;
      top: 12px;
      height: var(--zt-topbar-h);
      z-index: 19;
      border: 1px solid var(--zt-border);
      border-radius: 16px;
      background: rgba(7, 12, 22, .72);
      backdrop-filter: blur(14px);
      box-shadow: 0 12px 36px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.07);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 8px 12px;
    }
    .zt-topbar h3 { margin: 0; font-size: 15px; color: #e2e8f0; font-weight: 700; }
    .zt-topbar .meta { display: flex; gap: 8px; flex-wrap: wrap; }
    .zt-chip {
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 11px;
      color: #cbd5e1;
      background: rgba(255,255,255,.05);
      white-space: nowrap;
    }
    header, .chat-head {
      border: 1px solid var(--zt-border) !important;
      border-radius: var(--zt-radius) !important;
      background: rgba(5, 5, 5, .48) !important;
      backdrop-filter: blur(20px) !important;
      box-shadow: 0 22px 90px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.08) !important;
      padding: 16px !important;
    }
    .panel, .stat, .card, .metric, .status-card, .session, .bubble, pre, input, textarea, select, .pill {
      border: 1px solid var(--zt-border) !important;
      border-radius: var(--zt-radius) !important;
      background: var(--zt-panel) !important;
      box-shadow: 0 18px 70px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.06) !important;
    }
    .panel, header, .chat-head { backdrop-filter: blur(14px) !important; }
    .card, .stat, .metric, .status-card, .session, .bubble, pre, input, textarea, select, .pill {
      backdrop-filter: none !important;
    }
    .panel::after, .stat::after, .card::after {
      background:
        linear-gradient(135deg, rgba(255,255,255,.08), transparent 32%, transparent 76%, rgba(34,211,238,.05)) !important;
      opacity: .72 !important;
    }
    .card, .stat, .metric, .status-card, .session, .bubble {
      transition: transform var(--zt-fast), border-color var(--zt-fast), box-shadow var(--zt-fast), background var(--zt-fast);
    }
    .card:hover, .stat:hover, .metric:hover, .status-card:hover, .session:hover {
      transform: translateY(-2px) !important;
      border-color: var(--zt-border-hot) !important;
      box-shadow: 0 0 0 1px rgba(34,211,238,.12), 0 0 22px rgba(34,211,238,.10), 0 18px 58px rgba(0,0,0,.34) !important;
    }
    .session.active, .tab.active {
      border-color: rgba(168,85,247,.62) !important;
      background: rgba(168,85,247,.13) !important;
      box-shadow: 0 0 28px rgba(168,85,247,.16), inset 0 1px 0 rgba(255,255,255,.08) !important;
    }
    h1, h2, .eyebrow, .label, .id {
      text-shadow: none !important;
      letter-spacing: 0 !important;
    }
    h1 {
      background: linear-gradient(90deg, #f8fbff, #93c5fd 38%, #c084fc 74%, #f8fbff);
      -webkit-background-clip: text;
      color: transparent !important;
      text-transform: none !important;
    }
    h2, .eyebrow, .label, .id { color: #93c5fd !important; }
    p, .muted, small, .meta { color: var(--zt-muted) !important; }
    a, button {
      border: 1px solid rgba(34,211,238,.22) !important;
      border-radius: 999px !important;
      background: linear-gradient(135deg, rgba(34,211,238,.16), rgba(168,85,247,.16)) !important;
      color: var(--zt-text) !important;
      box-shadow: 0 0 20px rgba(34,211,238,.08), inset 0 1px 0 rgba(255,255,255,.08) !important;
      transition: transform var(--zt-fast), box-shadow var(--zt-fast), border-color var(--zt-fast), filter var(--zt-fast) !important;
    }
    a:hover, button:hover {
      transform: translateY(-1px) !important;
      border-color: rgba(34,211,238,.62) !important;
      box-shadow: 0 0 20px rgba(34,211,238,.14) !important;
    }
    button.primary, #sendBtn, .actions button:not(.secondary) {
      background: linear-gradient(135deg, rgba(34,211,238,.94), rgba(168,85,247,.86)) !important;
      color: #020617 !important;
      font-weight: 900 !important;
    }
    .danger {
      border-color: rgba(251,113,133,.42) !important;
      background: rgba(251,113,133,.12) !important;
      color: #fecdd3 !important;
    }
    input:focus, textarea:focus, select:focus {
      border-color: rgba(34,211,238,.68) !important;
      box-shadow: 0 0 0 3px rgba(34,211,238,.12), 0 0 30px rgba(34,211,238,.12) !important;
    }
    .badge, .pill, .status-badge {
      border: 1px solid rgba(255,255,255,.14) !important;
      border-radius: 999px !important;
      background: rgba(255,255,255,.06) !important;
      color: var(--zt-text) !important;
    }
    .allow, [data-decision="allow"], .badge.allow {
      color: var(--zt-green) !important;
      border-color: rgba(52,211,153,.45) !important;
      box-shadow: 0 0 22px rgba(52,211,153,.16) !important;
    }
    .challenge, [data-decision="challenge"], .badge.challenge {
      color: var(--zt-yellow) !important;
      border-color: rgba(251,191,36,.48) !important;
      box-shadow: 0 0 22px rgba(251,191,36,.16) !important;
    }
    .block, [data-decision="block"], .badge.block, .bad {
      color: var(--zt-red) !important;
      border-color: rgba(251,113,133,.5) !important;
      box-shadow: 0 0 24px rgba(251,113,133,.2) !important;
      animation: ztPulse 1.8s ease-in-out infinite;
    }
    .ready { border-color: rgba(52,211,153,.44) !important; }
    .warn, .medium { border-color: rgba(251,191,36,.5) !important; }
    .high, .critical { border-color: rgba(251,113,133,.55) !important; animation: ztPulse 1.8s ease-in-out infinite; }
    .value, .metric strong, .metric b {
      color: #f8fbff !important;
      font-variant-numeric: tabular-nums;
    }
    pre {
      color: #dbeafe !important;
      line-height: 1.55 !important;
    }
    .zt-trace-step {
      display: block;
      opacity: 0;
      transform: translateY(4px);
      animation: ztStep .24s ease forwards;
    }
    .zt-log-card { animation: ztFadeIn .18s ease both; }
    .dot { box-shadow: 0 0 18px currentColor !important; }
    @keyframes ztFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes ztStep { to { opacity: 1; transform: translateY(0); } }
    @keyframes ztPulse {
      0%, 100% { box-shadow: 0 0 18px rgba(251,113,133,.13), inset 0 1px 0 rgba(255,255,255,.06) !important; }
      50% { box-shadow: 0 0 34px rgba(251,113,133,.34), 0 0 56px rgba(251,113,133,.16) !important; }
    }
    @keyframes ztSweep { to { transform: translate3d(24px, -18px, 0); } }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: .001ms !important; transition-duration: .001ms !important; }
    }
    @media (max-width: 980px) {
      :root { --zt-sidebar-w: 86px; }
      .zt-brand b, .zt-brand span, .zt-nav a span { display: none; }
      .zt-topbar { left: calc(var(--zt-sidebar-w) + 24px); }
      body.zt-with-shell .shell, body.zt-with-shell .app {
        width: calc(100% - var(--zt-sidebar-w) - 24px) !important;
      }
    }
"""


CYBER_UI_JS = """
  <script>
    (() => {
      const numericIds = new Set([
        "modelsValue", "controlsValue", "rulesValue", "logsValue", "eventsValue",
        "totalRequests", "blockedRequests", "challengedRequests", "blockRate",
        "trustScore", "promptRisk", "securityScore"
      ]);
      const decisionClass = (value) => {
        const text = String(value || "").toLowerCase();
        if (text.includes("block")) return "block";
        if (text.includes("challenge")) return "challenge";
        if (text.includes("allow") || text.includes("protected") || text.includes("ready")) return "allow";
        return "";
      };
      const NAV_ITEMS = [
        { href: "/dashboard", label: "Dashboard", icon: "⌂" },
        { href: "/chat", label: "Chat", icon: "◉" },
        { href: "/dashboard/soc", label: "SOC", icon: "◈" },
        { href: "/dashboard/firewall", label: "Firewall", icon: "◍" },
        { href: "/dashboard/models/compare", label: "Compare", icon: "◎" },
        { href: "/dashboard/security", label: "Tests", icon: "◌" },
        { href: "/dashboard/demo", label: "Demo", icon: "◇" },
        { href: "/dashboard/evaluation", label: "Evaluate", icon: "▧" },
        { href: "/dashboard/testing", label: "Self-Test", icon: "◫" }
      ];
      const decorateDecision = (node) => {
        if (!node) return;
        node.classList.remove("allow", "challenge", "block");
        const cls = decisionClass(node.textContent);
        if (cls) {
          node.classList.add(cls);
          node.dataset.decision = cls;
        }
      };
      const animateNumber = (node, value) => {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
        const raw = String(value || "").trim();
        const match = raw.match(/^([0-9]+(?:\\.[0-9]+)?)(%)?$/);
        if (!match) return;
        if (node.dataset.ztAnimating === "1" || node.dataset.ztLastValue === raw) return;
        const target = Number(match[1]);
        const suffix = match[2] || "";
        const start = Number(node.dataset.currentValue || 0);
        const startTime = performance.now();
        const duration = 180;
        node.dataset.ztAnimating = "1";
        const tick = (time) => {
          const t = Math.min(1, (time - startTime) / duration);
          const eased = 1 - Math.pow(1 - t, 3);
          const next = start + (target - start) * eased;
          node.textContent = `${target % 1 ? next.toFixed(2) : Math.round(next)}${suffix}`;
          if (t < 1) requestAnimationFrame(tick);
          else {
            node.textContent = raw;
            node.dataset.currentValue = String(target);
            node.dataset.ztLastValue = raw;
            node.dataset.ztAnimating = "0";
          }
        };
        requestAnimationFrame(tick);
      };
      const revealTrace = (node) => {
        if (!node || node.dataset.ztRevealing === "1") return;
        if (node.querySelector && node.querySelector(".zt-trace-step")) return;
        const text = node.textContent || "";
        if (!text || text.length > 3500 || text.includes("<span")) return;
        node.dataset.ztRevealing = "1";
        const lines = text.split("\\n").slice(0, 80);
        node.innerHTML = lines.map((line, index) => {
          const safe = line.replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[ch]));
          return `<span class="zt-trace-step" style="animation-delay:${Math.min(index * 12, 120)}ms">${safe || "&nbsp;"}</span>`;
        }).join("");
        setTimeout(() => { node.dataset.ztRevealing = "0"; }, 320);
      };
      const activeHref = () => window.location.pathname || "/";
      const topbarTitle = () => {
        const h1 = document.querySelector("h1");
        return (h1 && h1.textContent && h1.textContent.trim()) || "Zero Trust AI Gateway";
      };
      const injectShell = () => {
        if (document.getElementById("ztSidebar")) return;
        document.body.classList.add("zt-with-shell");
        const sidebar = document.createElement("aside");
        sidebar.id = "ztSidebar";
        sidebar.className = "zt-sidebar";
        const nav = NAV_ITEMS.map((item) => `<a href="${item.href}" class="${activeHref() === item.href ? "zt-active" : ""}"><b>${item.icon}</b><span>${item.label}</span></a>`).join("");
        sidebar.innerHTML = `
          <div class="zt-brand"><b>Zero Trust AI</b><span>Adaptive Firewall Platform</span></div>
          <nav class="zt-nav">${nav}</nav>
          <div class="zt-status">
            <div class="zt-chip"><span class="zt-dot good"></span><span id="ztSysHealth">System online</span></div>
            <div class="zt-chip"><span class="zt-dot warn"></span><span id="ztThreatState">Threats: --</span></div>
          </div>`;
        document.body.appendChild(sidebar);

        const top = document.createElement("section");
        top.id = "ztTopbar";
        top.className = "zt-topbar";
        top.innerHTML = `<h3>${topbarTitle()}</h3><div class="meta"><span class="zt-chip">Secure Mode ON</span><span class="zt-chip" id="ztReqChip">Req: --</span><span class="zt-chip" id="ztBlockChip">Blocked: --</span></div>`;
        document.body.appendChild(top);
      };
      const refreshTopbarStats = async () => {
        const token = sessionStorage.getItem("zta_token");
        if (!token) return;
        try {
          const res = await fetch("/api/v1/monitoring/metrics", { headers: { Authorization: `Bearer ${token}` } });
          if (!res.ok) return;
          const data = await res.json();
          const req = document.getElementById("ztReqChip");
          const blk = document.getElementById("ztBlockChip");
          const threat = document.getElementById("ztThreatState");
          if (req) req.textContent = `Req: ${data.total_requests ?? 0}`;
          if (blk) blk.textContent = `Blocked: ${data.blocked_requests ?? 0}`;
          if (threat) {
            const level = Number(data.block_rate || 0) >= 40 ? "High" : Number(data.block_rate || 0) >= 15 ? "Medium" : "Low";
            threat.textContent = `Threats: ${level}`;
          }
        } catch {}
      };
      const decorate = (root = document) => {
        if (!root.querySelectorAll) return;
        document.querySelectorAll(".card").forEach((node) => node.classList.add("glass-card"));
        document.querySelectorAll("button, a").forEach((node) => node.classList.add("glow-button"));
        document.querySelectorAll(".badge, .pill").forEach(decorateDecision);
        document.querySelectorAll("#decisionTrace, #simResult").forEach(revealTrace);
        document.querySelectorAll("#logs .card").forEach((node, index) => {
          node.classList.add("zt-log-card");
          node.style.animationDelay = `${Math.min(index * 22, 220)}ms`;
        });
      };
      const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          const target = mutation.target;
          if (target.nodeType !== 1) continue;
          if (target.id && numericIds.has(target.id)) animateNumber(target, target.textContent);
          if (target.matches && (target.matches(".badge, .pill") || target.id === "decisionPill" || target.id === "ztaStatus")) decorateDecision(target);
          if (target.id === "decisionTrace" || target.id === "simResult") revealTrace(target);
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType !== 1) return;
            if (node.matches && node.matches(".badge, .pill")) decorateDecision(node);
            if (node.querySelectorAll) node.querySelectorAll(".badge, .pill").forEach(decorateDecision);
          });
        }
      });
      window.addEventListener("DOMContentLoaded", () => {
        injectShell();
        document.body.classList.add("zt-ready");
        decorate();
        refreshTopbarStats();
        observer.observe(document.body, { childList: true, subtree: true });
      });
    })();
  </script>
"""
