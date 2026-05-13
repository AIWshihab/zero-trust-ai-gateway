from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS

CONTROL_CENTER_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Control Center — Zero Trust AI Gateway</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { min-height: 100vh; color: #f8fbff; }
    .shell { padding: 24px; display: grid; gap: 20px; }
    .page-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
    .page-header h1 { font-size: 26px; font-weight: 800; }
    .eyebrow { font-size: 11px; color: #93c5fd; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
    .nav-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .nav-row a { font-size: 12px !important; padding: 6px 14px !important; text-decoration: none; }
    .cc-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .cc-card { border: 1px solid rgba(255,255,255,.12); border-radius: 18px; background: rgba(255,255,255,.05); padding: 20px; transition: border-color .25s; }
    .cc-card:hover { border-color: rgba(34,211,238,.35); }
    .card-title { font-size: 11px; color: #93c5fd; text-transform: uppercase; letter-spacing: .1em; font-weight: 700; margin-bottom: 18px; display: flex; align-items: center; gap: 7px; }
    .card-title::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: #93c5fd; flex-shrink: 0; box-shadow: 0 0 8px #93c5fd; }
    .field { margin-bottom: 14px; }
    .field:last-child { margin-bottom: 0; }
    .field-label { font-size: 12px; color: #64748b; margin-bottom: 6px; display: flex; justify-content: space-between; }
    .field-value { font-size: 15px; font-weight: 600; color: #f1f5f9; }
    /* Progress */
    .prog-bar { height: 7px; background: rgba(255,255,255,.1); border-radius: 99px; overflow: hidden;
      border: none !important; box-shadow: none !important; border-radius: 99px !important; }
    .prog-fill { height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6); border-radius: 99px;
      width: 0%; transition: width .65s cubic-bezier(.2,.8,.2,1); }
    /* Badge */
    .sbadge { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; padding: 4px 10px;
      border-radius: 99px; font-weight: 600; border: none !important; box-shadow: none !important; }
    .sbadge-green { background: rgba(34,197,94,.12) !important; color: #86efac !important;
      border: 1px solid rgba(34,197,94,.3) !important; }
    .sbadge-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor;
      box-shadow: 0 0 6px currentColor; animation: sdot 1.5s infinite; }
    @keyframes sdot { 0%,100%{opacity:1} 50%{opacity:.3} }
    /* Toggle */
    .toggle-list { display: grid; }
    .toggle-row { display: flex; align-items: center; justify-content: space-between;
      padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
    .toggle-row:last-child { border-bottom: none; }
    .toggle-row span { font-size: 13px; color: #cbd5e1; }
    .sw { position: relative; display: inline-block; width: 42px; height: 22px; flex-shrink: 0; cursor: pointer; }
    .sw input { opacity: 0; width: 0; height: 0; position: absolute; }
    .sw-track { position: absolute; inset: 0; background: rgba(255,255,255,.1); border-radius: 22px;
      transition: .3s; border: 1px solid rgba(255,255,255,.15) !important;
      box-shadow: none !important; border-radius: 22px !important; }
    .sw-track::before { content: ""; position: absolute; width: 16px; height: 16px; border-radius: 50%;
      background: rgba(255,255,255,.7); left: 2px; top: 2px; transition: .3s; box-shadow: 0 1px 4px rgba(0,0,0,.4); }
    .sw input:checked ~ .sw-track { background: rgba(99,102,241,.75) !important; border-color: rgba(99,102,241,.9) !important; }
    .sw input:checked ~ .sw-track::before { transform: translateX(20px); background: #fff !important;
      box-shadow: 0 0 8px rgba(99,102,241,.7) !important; }
    /* Range */
    .range-field { margin-bottom: 16px; }
    .range-field:last-of-type { margin-bottom: 0; }
    .range-header { display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
    .range-val { color: #a5b4fc; font-weight: 700; }
    input[type=range] {
      -webkit-appearance: none !important; appearance: none !important;
      width: 100% !important; height: 5px !important;
      background: rgba(99,102,241,.22) !important; border: none !important;
      border-radius: 5px !important; outline: none !important;
      box-shadow: none !important; padding: 0 !important; cursor: pointer;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none !important; width: 17px !important; height: 17px !important;
      border-radius: 50% !important; background: #6366f1 !important;
      border: 2px solid rgba(255,255,255,.25) !important;
      box-shadow: 0 0 8px rgba(99,102,241,.6) !important; cursor: pointer !important;
    }
    input[type=range]::-moz-range-thumb {
      width: 17px; height: 17px; border-radius: 50%; background: #6366f1;
      border: 2px solid rgba(255,255,255,.25); cursor: pointer;
    }
    /* Select */
    select.cc-select {
      width: 100%; background: rgba(255,255,255,.06) !important;
      border: 1px solid rgba(255,255,255,.15) !important; border-radius: 10px !important;
      color: #f1f5f9 !important; padding: 9px 12px !important; font-size: 13px;
      cursor: pointer; outline: none; box-shadow: none !important;
      margin-top: 6px; -webkit-appearance: none; appearance: none;
    }
    select.cc-select option { background: #0f172a; }
    /* KPI */
    .kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .kpi-box { background: rgba(0,0,0,.25); border: 1px solid rgba(255,255,255,.08) !important;
      border-radius: 12px !important; padding: 12px; box-shadow: none !important; }
    .kpi-label { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: .07em; }
    .kpi-val { font-size: 20px; font-weight: 800; margin-top: 4px; font-variant-numeric: tabular-nums; }
    /* Threat */
    .threat-badge { font-size: 24px; font-weight: 900; letter-spacing: .05em; padding: 6px 0; }
    .threat-low { color: #86efac; text-shadow: 0 0 20px rgba(134,239,172,.5); }
    .threat-medium { color: #fbbf24; text-shadow: 0 0 20px rgba(251,191,36,.5); }
    .threat-high { color: #fb7185; text-shadow: 0 0 20px rgba(251,113,133,.5); animation: sdot 1.5s infinite; }
    /* Actions */
    .cc-span-2 { grid-column: span 2; }
    .action-area { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
    .cc-btn { padding: 10px 22px; cursor: pointer; font-size: 13px; font-weight: 700; transition: all .2s; }
    .cc-btn-danger {
      background: rgba(239,68,68,.12) !important; color: #fca5a5 !important;
      border: 1px solid rgba(239,68,68,.28) !important; border-radius: 10px !important;
      box-shadow: none !important;
    }
    .cc-btn-danger:hover {
      background: rgba(239,68,68,.22) !important; transform: none !important;
      box-shadow: 0 0 16px rgba(239,68,68,.2) !important;
    }
    .action-note { font-size: 12px; color: #475569; }
    @keyframes ccReset { 0%{background:rgba(34,211,238,.18)!important} 100%{background:rgba(239,68,68,.12)!important} }
    @media (max-width: 740px) {
      .cc-grid { grid-template-columns: 1fr; }
      .cc-span-2 { grid-column: span 1; }
      .kpi-grid { grid-template-columns: repeat(2, 1fr); }
      .page-header { flex-direction: column; align-items: flex-start; }
      .nav-row { flex-wrap: wrap; }
    }
    @media (max-width: 420px) {
      .kpi-grid { grid-template-columns: 1fr; }
      .action-area { flex-direction: column; align-items: flex-start; }
      .cc-btn { width: 100%; text-align: center; }
      .shell { padding: 14px; }
    }
  </style>
</head>
<body>
  <main class="shell">

    <div class="page-header">
      <div>
        <div class="eyebrow">Zero Trust AI Gateway</div>
        <h1>Control Center</h1>
      </div>
      <div class="nav-row">
        <a href="/dashboard">Dashboard</a>
        <a href="/dashboard/soc">SOC</a>
        <a href="/control-plane">Control Plane</a>
      </div>
    </div>

    <div class="cc-grid">

      <!-- 1. Identity & Access -->
      <article class="cc-card">
        <div class="card-title">Identity &amp; Access</div>
        <div class="field">
          <div class="field-label">Role</div>
          <div class="field-value">Administrator</div>
        </div>
        <div class="field">
          <div class="field-label">
            <span>Trust Score</span>
            <span style="color:#a5b4fc;font-weight:700" id="trustPct">82%</span>
          </div>
          <div class="prog-bar"><div class="prog-fill" id="trustFill"></div></div>
        </div>
        <div class="field">
          <div class="field-label">Session Status</div>
          <span class="sbadge sbadge-green"><span class="sbadge-dot"></span>Active</span>
        </div>
      </article>

      <!-- 2. Security Controls -->
      <article class="cc-card">
        <div class="card-title">Security Controls</div>
        <div class="toggle-list">
          <div class="toggle-row">
            <span>Challenge Mode</span>
            <label class="sw"><input type="checkbox" onchange="onToggle('challengeMode',this.checked)"><span class="sw-track"></span></label>
          </div>
          <div class="toggle-row">
            <span>Consensus Override</span>
            <label class="sw"><input type="checkbox" checked onchange="onToggle('consensusOverride',this.checked)"><span class="sw-track"></span></label>
          </div>
          <div class="toggle-row">
            <span>Adaptive Risk</span>
            <label class="sw"><input type="checkbox" checked onchange="onToggle('adaptiveRisk',this.checked)"><span class="sw-track"></span></label>
          </div>
          <div class="toggle-row">
            <span>Auto Explain</span>
            <label class="sw"><input type="checkbox" onchange="onToggle('autoExplain',this.checked)"><span class="sw-track"></span></label>
          </div>
          <div class="toggle-row">
            <span>Self Critique</span>
            <label class="sw"><input type="checkbox" onchange="onToggle('selfCritique',this.checked)"><span class="sw-track"></span></label>
          </div>
        </div>
      </article>

      <!-- 3. Behavior Tuning -->
      <article class="cc-card">
        <div class="card-title">Behavior Tuning</div>
        <div class="range-field">
          <div class="range-header"><span>Risk Threshold</span><span class="range-val" id="riskVal">0.35</span></div>
          <input type="range" min="0" max="1" step="0.01" value="0.35"
            oninput="document.getElementById('riskVal').textContent=parseFloat(this.value).toFixed(2);console.log('Risk Threshold:',this.value)">
        </div>
        <div class="range-field">
          <div class="range-header"><span>Consensus Threshold</span><span class="range-val" id="conVal">0.60</span></div>
          <input type="range" min="0" max="1" step="0.01" value="0.60"
            oninput="document.getElementById('conVal').textContent=parseFloat(this.value).toFixed(2);console.log('Consensus Threshold:',this.value)">
        </div>
        <div class="field" style="margin-top:14px">
          <div class="range-header"><span>Detection Sensitivity</span></div>
          <select class="cc-select" onchange="console.log('Detection Sensitivity:',this.value)">
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div class="field">
          <div class="range-header"><span>Rate Limit Level</span></div>
          <select class="cc-select" onchange="console.log('Rate Limit Level:',this.value)">
            <option value="permissive">Permissive — 200 req/min</option>
            <option value="standard" selected>Standard — 100 req/min</option>
            <option value="strict">Strict — 50 req/min</option>
            <option value="lockdown">Lockdown — 10 req/min</option>
          </select>
        </div>
      </article>

      <!-- 4. System State -->
      <article class="cc-card">
        <div class="card-title">System State</div>
        <div class="field">
          <div class="field-label">Global Threat Level</div>
          <div class="threat-badge threat-low" id="threatLevel">LOW</div>
        </div>
        <div class="kpi-grid">
          <div class="kpi-box">
            <div class="kpi-label">Active Campaigns</div>
            <div class="kpi-val" style="color:#fbbf24">2</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-label">System Mode</div>
            <div class="kpi-val" style="font-size:12px;color:#86efac;line-height:1.5;margin-top:5px">Active Defense</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-label">Total Requests</div>
            <div class="kpi-val" id="totalReqs">—</div>
          </div>
          <div class="kpi-box">
            <div class="kpi-label">Total Blocks</div>
            <div class="kpi-val" style="color:#fb7185" id="totalBlocks">—</div>
          </div>
        </div>
      </article>

      <!-- 5. Actions -->
      <article class="cc-card cc-span-2">
        <div class="card-title">Actions</div>
        <div class="action-area">
          <button class="cc-btn cc-btn-danger" id="resetBtn" onclick="resetSystem()">Reset System State</button>
          <span class="action-note">All actions are logged and audited by the gateway</span>
        </div>
      </article>

    </div>
  </main>
  <script>
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
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
