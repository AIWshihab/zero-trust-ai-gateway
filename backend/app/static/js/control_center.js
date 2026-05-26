const ctrlState = {
      challengeMode: false, consensusOverride: true, adaptiveRisk: true,
      autoExplain: false, selfCritique: false
    };
    function onToggle(key, value) {
      ctrlState[key] = value;
      console.log('[ControlCenter] toggle', key, '→', value, ctrlState);
    }
    function resetSystem() {
      const btn = document.getElementById('resetBtn');
      btn.textContent = 'Resetting…';
      btn.disabled = true;
      btn.style.animation = 'ccReset .4s ease';
      console.log('[ControlCenter] Reset System State', ctrlState);
      setTimeout(() => {
        btn.textContent = 'Reset System State';
        btn.disabled = false;
        btn.style.animation = '';
        console.log('[ControlCenter] Reset complete');
      }, 1400);
    }
    function countUp(id, target) {
      const el = document.getElementById(id);
      if (!el) return;
      let n = 0;
      const step = Math.max(1, Math.ceil(target / 55));
      const t = setInterval(() => {
        n = Math.min(n + step, target);
        el.textContent = n.toLocaleString();
        if (n >= target) clearInterval(t);
      }, 22);
    }
    async function fetchMetrics() {
      const token = sessionStorage.getItem('zta_token');
      if (!token) { countUp('totalReqs', 14823); countUp('totalBlocks', 312); return; }
      try {
        const res = await fetch('/api/v1/monitoring/metrics', { headers: { Authorization: 'Bearer ' + token } });
        if (!res.ok) throw new Error();
        const d = await res.json();
        const req = Number(d.total_requests || 0);
        const blk = Number(d.blocked_requests || 0);
        document.getElementById('totalReqs').textContent = req.toLocaleString();
        document.getElementById('totalBlocks').textContent = blk.toLocaleString();
        const rate = Number(d.block_rate || 0);
        const lvl = rate >= 40 ? 'HIGH' : rate >= 15 ? 'MEDIUM' : 'LOW';
        const el = document.getElementById('threatLevel');
        if (el) { el.textContent = lvl; el.className = 'threat-badge threat-' + lvl.toLowerCase(); }
      } catch {
        countUp('totalReqs', 14823);
        countUp('totalBlocks', 312);
      }
    }
    window.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => { document.getElementById('trustFill').style.width = '82%'; }, 320);
      fetchMetrics();
    });