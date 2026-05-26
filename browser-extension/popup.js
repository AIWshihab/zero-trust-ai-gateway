// Zero Trust AI Gateway — Popup script
const B = globalThis.browser ?? globalThis.chrome;
const $ = (id) => document.getElementById(id);

function normalizeBase(v) { return String(v || '').trim().replace(/\/+$/, ''); }

function decCls(d) {
  const v = String(d || '').toLowerCase();
  return v === 'allow' ? 'allow' : v === 'block' ? 'block' : v === 'challenge' ? 'challenge' : '';
}

function fmtTime(iso) {
  try {
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

function esc(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

// ── Parse connect URL ────────────────────────────────────────────────────────
function applyConnectUrl(raw) {
  if (!raw) return false;
  try {
    const parsed = new URL(raw.trim());
    const token    = parsed.searchParams.get('token') || parsed.searchParams.get('pairing_token');
    const gUrl     = parsed.searchParams.get('gateway_api_url') || parsed.origin;
    const sessId   = parsed.searchParams.get('setup_session_id') || '';
    if (!token || !gUrl) return false;
    $('gatewayUrl').value    = normalizeBase(gUrl);
    $('pairingToken').value  = token;
    $('setupSessionId').value = sessId;
    return true;
  } catch { return false; }
}

// ── UI states ────────────────────────────────────────────────────────────────
function showConnected(state) {
  // Header pill
  const pill = $('statusPill');
  pill.className = 'status-pill connected';
  $('statusDot').className = 'dot live';
  $('statusText').textContent = 'Protected';

  // Device card
  $('deviceCard').classList.remove('hidden');
  $('deviceIdVal').textContent = state.deviceId ? `#${state.deviceId}` : '—';
  $('browserVal').textContent  = state.browserName || detectBrowser();
  $('gatewayVal').textContent  = (state.gatewayApiUrl || 'localhost:8000').replace(/https?:\/\//, '');

  // Stats + feed
  $('statsCard').classList.remove('hidden');
  $('feedCard').classList.remove('hidden');
  $('promptToggle').classList.remove('hidden');

  // Hide connect form
  $('connectCard').classList.add('hidden');
  $('disconnectRow').classList.remove('hidden');
}

function showDisconnected() {
  const pill = $('statusPill');
  pill.className = 'status-pill';
  $('statusDot').className = 'dot';
  $('statusText').textContent = 'Not connected';

  $('deviceCard').classList.add('hidden');
  $('statsCard').classList.add('hidden');
  $('feedCard').classList.add('hidden');
  $('promptToggle').classList.add('hidden');
  $('promptCard').classList.add('hidden');

  $('connectCard').classList.remove('hidden');
  $('disconnectRow').classList.add('hidden');
}

function detectBrowser() {
  const ua = navigator.userAgent;
  if (typeof globalThis.browser !== 'undefined') return 'Firefox';
  if (ua.includes('Edg/')) return 'Edge';
  if (ua.includes('Chrome')) return 'Chrome';
  return 'Browser';
}

// ── Render stats ─────────────────────────────────────────────────────────────
function renderStats(stats) {
  const s = stats || {};
  $('statAllowed').textContent   = s.allowed   || 0;
  $('statBlocked').textContent   = s.blocked   || 0;
  $('statChallenged').textContent = s.challenged || 0;
}

// ── Render recent decisions ──────────────────────────────────────────────────
function renderFeed(decisions) {
  const feed = $('decisionFeed');
  if (!decisions || !decisions.length) {
    feed.innerHTML = '<div class="feed-empty">No intercepted requests yet.</div>';
    return;
  }
  feed.innerHTML = decisions.slice(0, 15).map(d => {
    const cls = decCls(d.decision);
    return `<div class="decision-row">
      <span class="ddot ${cls}"></span>
      <span class="dec-url">${esc(d.host || d.url || '—')}</span>
      <span class="dec-label ${cls}">${esc(String(d.decision || '').toUpperCase())}</span>
    </div>`;
  }).join('');
}

// ── Load state ───────────────────────────────────────────────────────────────
async function loadState() {
  B.storage.local.get(['gatewayApiUrl', 'accessToken', 'deviceId', 'modelId', 'ztaStats', 'ztaDecisions', 'browserName'], (state) => {
    if (state.gatewayApiUrl) $('gatewayUrl').value = normalizeBase(state.gatewayApiUrl);
    if (state.modelId) $('modelId').value = state.modelId;

    if (state.accessToken) {
      showConnected(state);
      renderStats(state.ztaStats);
      renderFeed(state.ztaDecisions);
    } else {
      showDisconnected();
    }
  });
}

async function prefillFromTab() {
  try {
    const tabs = await B.tabs.query({ active: true, currentWindow: true });
    const url  = tabs?.[0]?.url || '';
    if (url.includes('/dashboard/extension/connect')) {
      if (applyConnectUrl(url)) setTimeout(connect, 300);
    }
  } catch { /* ignore */ }
}

// ── Connect ──────────────────────────────────────────────────────────────────
async function connect() {
  const gatewayApiUrl = normalizeBase($('gatewayUrl').value);
  const pairingToken  = $('pairingToken').value.trim();
  const setupSessionId = $('setupSessionId').value.trim();
  if (!gatewayApiUrl || !pairingToken) {
    alert('Enter the Gateway URL and pairing token.');
    return;
  }

  $('connectBtn').disabled = true;
  $('connectBtn').textContent = 'Connecting...';

  try {
    const browserName = detectBrowser();
    const res = await fetch(`${gatewayApiUrl}/api/v1/extension/register-device`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pairing_token: pairingToken,
        setup_session_id: setupSessionId || null,
        browser_name: browserName,
        extension_version: B.runtime.getManifest().version,
        user_agent: navigator.userAgent,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
        platform: navigator.platform || '',
        device_label: $('deviceLabel').value.trim() || `${browserName} Extension`,
      }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Pairing failed');

    await B.storage.local.set({
      gatewayApiUrl,
      accessToken: data.access_token,
      deviceId: data.device_id,
      modelId: $('modelId').value || '1',
      browserName,
      ztaStats: { total: 0, allowed: 0, blocked: 0, challenged: 0 },
      ztaDecisions: [],
    });

    $('pairingToken').value  = '';
    $('connectUrl').value    = '';
    $('setupSessionId').value = '';

    await loadState();
  } catch (err) {
    alert(err.message || 'Connection failed');
  } finally {
    $('connectBtn').disabled = false;
    $('connectBtn').textContent = 'Connect';
  }
}

// ── Disconnect ───────────────────────────────────────────────────────────────
async function disconnect() {
  await B.storage.local.remove(['accessToken', 'deviceId', 'ztaStats', 'ztaDecisions', 'browserName']);
  showDisconnected();
}

// ── Send prompt ──────────────────────────────────────────────────────────────
async function sendPrompt() {
  const state = await new Promise(r => B.storage.local.get(['gatewayApiUrl', 'accessToken', 'deviceId'], r));
  const gatewayApiUrl = normalizeBase($('gatewayUrl').value || state.gatewayApiUrl);
  const prompt  = $('prompt').value.trim();
  const modelId = Number($('modelId').value || 1);

  if (!state.accessToken) { alert('Connect to the gateway first.'); return; }
  if (!prompt)             { alert('Enter a prompt.'); return; }

  $('sendBtn').disabled = true;
  $('decisionLine').innerHTML = '<span style="color:var(--muted)">Evaluating...</span>';
  $('output').textContent = '';

  try {
    const res = await fetch(`${gatewayApiUrl}/api/v1/usage/infer`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${state.accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: modelId,
        prompt,
        messages: [{ role: 'user', content: prompt }],
        parameters: {
          gateway_context: {
            source: 'browser_extension',
            device_id: state.deviceId,
            extension_version: B.runtime.getManifest().version,
          },
        },
      }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail?.explanation || data.detail?.reason || data.detail || 'Gateway request failed');

    const cls = decCls(data.decision);
    const risk = Math.round(Number(data.effective_risk || data.prompt_risk_score || 0) * 100);
    $('decisionLine').innerHTML = `<span class="dec ${cls}">${String(data.decision || '').toUpperCase()}</span> &nbsp; risk: ${risk}%`;
    $('output').textContent = data.output || data.reason || 'No output.';

    // Save to local decisions log
    B.storage.local.get(['ztaDecisions'], (s) => {
      const decisions = s.ztaDecisions || [];
      decisions.unshift({ decision: data.decision, host: 'manual', ts: new Date().toISOString() });
      B.storage.local.set({ ztaDecisions: decisions.slice(0, 50) });
    });
  } catch (err) {
    $('decisionLine').innerHTML = '<span style="color:var(--red)">Request failed</span>';
    $('output').textContent = err.message || 'Error contacting gateway.';
  } finally {
    $('sendBtn').disabled = false;
  }
}

// ── Event wiring ─────────────────────────────────────────────────────────────
$('connectBtn').addEventListener('click', connect);
$('disconnectBtn').addEventListener('click', disconnect);
$('sendBtn').addEventListener('click', sendPrompt);
$('connectUrl').addEventListener('input', (e) => applyConnectUrl(e.target.value));
$('promptToggle').addEventListener('click', () => {
  const c = $('promptCard');
  const hidden = c.classList.toggle('hidden');
  $('promptToggle').textContent = hidden ? '▾ Send test prompt through gateway' : '▴ Hide test prompt';
});

loadState().then(prefillFromTab);
