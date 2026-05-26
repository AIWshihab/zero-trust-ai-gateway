(() => {
      const UI = {
        page: "zt-page-wrapper mx-auto w-full max-w-screen-2xl px-4 pb-10 text-slate-100 sm:px-6 lg:px-8",
        sectionCard: "zt-section-card rounded-xl border border-white/10 bg-white/5 text-slate-100 shadow-none",
        metricCard: "zt-metric-card rounded-xl border border-white/10 bg-white/5 p-4 text-slate-100",
        sidebarItem: "rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 transition hover:bg-white/10",
        sidebarItemActive: "zt-active border-cyan-400/40 bg-cyan-400/10 text-slate-100",
        buttonPrimary: "zt-btn-primary inline-flex items-center justify-center rounded-lg border border-cyan-400 px-3 py-2 text-sm font-semibold text-black",
        buttonSecondary: "zt-btn-secondary inline-flex items-center justify-center rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 hover:bg-white/10",
        buttonGhost: "zt-btn-ghost inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/10",
        buttonDanger: "zt-btn-danger inline-flex items-center justify-center rounded-lg border border-rose-400/30 px-3 py-2 text-sm text-rose-300",
        input: "zt-input rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400/60 focus:outline-none",
        tab: "zt-tab rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 hover:bg-white/10",
        badge: "inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300",
        table: "zt-table w-full border-collapse text-sm text-slate-300",
        empty: "zt-empty-state rounded-xl border border-dashed border-white/15 bg-white/5 p-4 text-slate-400"
      };
      const addClasses = (node, classText) => {
        if (!node || !classText) return;
        node.classList.add(...classText.split(/\\s+/).filter(Boolean));
      };
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
      const parseJwt = (token) => {
        try {
          const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
          return JSON.parse(atob(b64));
        } catch { return {}; }
      };
      const getTokenPayload = () => {
        const t = sessionStorage.getItem("zta_token");
        return t ? parseJwt(t) : {};
      };
      const isAdmin = () => (getTokenPayload().scopes || []).includes("admin");

      const NAV_ITEMS_ALL = [
        { href: "/dashboard",                  label: "Dashboard",           icon: "⌂", adminOnly: false },
        { href: "/dashboard/getting-started",  label: "Guide",               icon: "?", adminOnly: false },
        { href: "/dashboard/chat",             label: "Secure Chat",         icon: "◉", adminOnly: false },
        { href: "/dashboard/models",           label: "Models",              icon: "▦", adminOnly: false },
        { href: "/dashboard/security-monitor", label: "Monitor",             icon: "◈", adminOnly: false },
        { href: "/dashboard/policy",           label: "Policy",              icon: "⚙", adminOnly: false },
        { href: "/dashboard/research",         label: "Research",            icon: "▧", adminOnly: false },
        { href: "/dashboard/account",          label: "Account",             icon: "◐", adminOnly: false },
      ];
      const NAV_ITEMS = NAV_ITEMS_ALL.filter(item => !item.adminOnly || isAdmin());
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
            node.textContent = `${target}${suffix}`;
            node.dataset.currentValue = String(target);
            node.dataset.ztLastValue = raw;
            delete node.dataset.ztAnimating;
          }
        };
        requestAnimationFrame(tick);
      };

      function injectShell() {
        if (document.body.classList.contains("no-shell")) return;
        document.body.classList.add("zt-with-shell");
        const currentPath = location.pathname;

        /* Sidebar */
        const sidebar = document.createElement("aside");
        sidebar.id = "ztSidebar";
        sidebar.className = "zt-sidebar";
        sidebar.innerHTML = `
          <div class="zt-brand">
            <b>ZT // Gateway</b>
            <span>Zero Trust AI Gateway</span>
          </div>
          <nav class="zt-nav" id="ztNav">
            ${NAV_ITEMS.map(item => `
              <a href="${item.href}" class="${item.href === currentPath || (item.href !== '/dashboard' && currentPath.startsWith(item.href)) ? 'zt-active' : ''}">
                <b>${item.icon}</b><span>${item.label}</span>
              </a>`).join("")}
          </nav>
          <div class="zt-status" id="ztStatus">
            <div style="font-size:11px;color:var(--zt-muted)">
              <span class="zt-dot" style="background:var(--zt-green);box-shadow:0 0 8px var(--zt-green)"></span>Gateway online
            </div>
          </div>`;
        document.body.prepend(sidebar);

        /* Topbar */
        const topbar = document.createElement("div");
        topbar.id = "ztTopbar";
        topbar.className = "zt-topbar";
        const pageLabel = NAV_ITEMS.find(i => i.href === currentPath || (i.href !== "/dashboard" && currentPath.startsWith(i.href)))?.label || "Zero Trust AI Gateway";
        topbar.innerHTML = `
          <h3 id="ztPageTitle">${pageLabel}</h3>
          <div class="meta" id="ztTopMeta">
            <span class="zt-chip" id="ztUserChip">...</span>
            <span class="zt-chip allow" id="ztZtaChip">Protected</span>
            <a href="/login" id="ztLogoutLink" style="padding:5px 10px;font-size:12px;border-radius:6px">Logout</a>
          </div>`;
        document.body.prepend(topbar);

        /* Populate user chip & logout */
        const token = sessionStorage.getItem("zta_token");
        if (token) {
          const payload = parseJwt(token);
          if (payload.sub) document.getElementById("ztUserChip").textContent = payload.sub;
        }
        document.getElementById("ztLogoutLink")?.addEventListener("click", (e) => {
          e.preventDefault();
          sessionStorage.removeItem("zta_token");
          location.href = "/login";
        });

        /* ZTA status */
        const ztaChip = document.getElementById("ztZtaChip");
        if (token) {
          fetch("/api/v1/monitoring/zta/status", { headers: { Authorization: `Bearer ${token}` } })
            .then(r => r.json())
            .then(d => {
              if (ztaChip) {
                ztaChip.textContent = d.enabled ? "Protected" : "Unprotected";
                ztaChip.className = `zt-chip ${d.enabled ? "allow" : "block"}`;
              }
            }).catch(() => {});
        }

        /* Decorate decisions & animate numbers */
        const observer = new MutationObserver(() => {
          document.querySelectorAll("[data-decision]").forEach(decorateDecision);
          numericIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) animateNumber(el, el.textContent);
          });
        });
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      }

      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", injectShell);
      } else {
        injectShell();
      }
    })();