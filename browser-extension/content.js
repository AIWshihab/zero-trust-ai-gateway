// Zero Trust AI Gateway — Content Script (isolated world)
// Bridges the MAIN-world interceptor ↔ background service worker.
// Also injects a live status badge on popular AI sites.

const B = globalThis.browser ?? globalThis.chrome;

// ── AI site detection ────────────────────────────────────────────────────────
const AI_SITE_PATTERNS = [
  /chat\.openai\.com/i, /chatgpt\.com/i,
  /gemini\.google\.com/i,
  /copilot\.microsoft\.com/i,
  /perplexity\.ai/i,
  /you\.com/i,
  /poe\.com/i,
  /character\.ai/i,
  /huggingface\.co\/chat/i,
];
const isAISite = (url) => AI_SITE_PATTERNS.some(p => p.test(url));

// ── Badge injection ──────────────────────────────────────────────────────────
function injectBadge(connected, deviceId, stats) {
  const existing = document.getElementById('zta-status-badge');
  if (existing) existing.remove();

  const badge = document.createElement('div');
  badge.id = 'zta-status-badge';
  badge.style.cssText = [
    'position:fixed', 'bottom:18px', 'right:18px', 'z-index:2147483647',
    `background:${connected ? '#0d0f14' : '#1a0808'}`,
    `border:1px solid ${connected ? 'rgba(0,212,255,0.35)' : 'rgba(255,77,109,0.35)'}`,
    'border-radius:10px', 'padding:8px 13px',
    'font-family:Inter,ui-sans-serif,sans-serif', 'font-size:12px', 'font-weight:600',
    `color:${connected ? '#edf2ff' : '#ff4d6d'}`,
    'box-shadow:0 4px 24px rgba(0,0,0,0.6)',
    'display:flex', 'align-items:center', 'gap:8px',
    'cursor:pointer', 'transition:opacity 0.2s', 'user-select:none',
    'max-width:280px',
  ].join(';');

  const styleEl = document.createElement('style');
  styleEl.textContent = '@keyframes _ztapulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.45;transform:scale(.8)}}';
  document.head.appendChild(styleEl);

  const dot = document.createElement('span');
  dot.style.cssText = [
    'width:7px', 'height:7px', 'border-radius:50%', 'flex-shrink:0', 'display:inline-block',
    `background:${connected ? '#22d3a0' : '#ff4d6d'}`,
    connected ? 'box-shadow:0 0 8px #22d3a0;animation:_ztapulse 1.8s ease-in-out infinite' : '',
  ].join(';');
  badge.appendChild(dot);

  const label = document.createElement('span');
  const blocked = stats?.blocked || 0;
  const total   = stats?.total || 0;
  label.textContent = connected
    ? `ZT Protected · #${deviceId || '?'}${total ? ` · ${blocked}/${total} blocked` : ''}`
    : 'Zero Trust Gateway: Not connected';
  badge.appendChild(label);

  badge.addEventListener('click', () => { badge.style.opacity = '0'; setTimeout(() => badge.remove(), 200); });
  document.body.appendChild(badge);
}

function maybeInjectBadge() {
  if (!isAISite(window.location.href)) return;
  B.storage.local.get(['accessToken', 'deviceId', 'ztaStats'], (state) => {
    const stats = state.ztaStats || {};
    injectBadge(Boolean(state.accessToken), state.deviceId, stats);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', maybeInjectBadge);
} else {
  maybeInjectBadge();
}

// ── Bridge: MAIN world interceptor ↔ background ──────────────────────────────
window.addEventListener('message', function (event) {
  if (event.source !== window) return;
  const msg = event.data;
  if (!msg?.type) return;

  // Relay AI check requests from interceptor → background
  if (msg.type === 'ZTA_CHECK_AI_REQUEST') {
    B.storage.local.get(['gatewayApiUrl', 'accessToken', 'deviceId'], (state) => {
      if (!state.accessToken) {
        // Not connected — fail open, don't break the page
        window.postMessage({ type: 'ZTA_GATEWAY_DECISION', requestId: msg.requestId, decision: 'allow' }, '*');
        return;
      }
      B.runtime.sendMessage({
        type: 'ZTA_CHECK_REQUEST',
        requestId: msg.requestId,
        url: msg.url,
        method: msg.method,
        extractedPrompt: msg.extractedPrompt,
        gatewayApiUrl: state.gatewayApiUrl,
        accessToken: state.accessToken,
        deviceId: state.deviceId,
      }, (response) => {
        if (B.runtime.lastError) {
          window.postMessage({ type: 'ZTA_GATEWAY_DECISION', requestId: msg.requestId, decision: 'allow' }, '*');
          return;
        }
        // Update local stats
        B.storage.local.get(['ztaStats'], (s) => {
          const stats = s.ztaStats || { total: 0, blocked: 0, challenged: 0, allowed: 0 };
          stats.total += 1;
          const dec = response?.decision || 'allow';
          if (dec === 'block') stats.blocked += 1;
          else if (dec === 'challenge') stats.challenged += 1;
          else stats.allowed += 1;
          B.storage.local.set({ ztaStats: stats });
        });
        window.postMessage({
          type: 'ZTA_GATEWAY_DECISION',
          requestId: msg.requestId,
          decision: response?.decision || 'allow',
          reason: response?.reason || '',
        }, '*');
      });
    });
    return;
  }

  // Dashboard extension ping
  if (msg.type === 'ZTA_GATEWAY_EXTENSION_PING') {
    window.postMessage({
      type: 'ZTA_GATEWAY_EXTENSION_DETECTED',
      nonce: msg.nonce,
      extensionVersion: B.runtime.getManifest().version,
    }, '*');
    return;
  }

  // Dashboard quick-connect auto-register
  if (msg.type === 'ZTA_AUTOCONNECT_REQUEST') {
    B.runtime.sendMessage({
      type: 'ZTA_AUTO_REGISTER',
      gatewayApiUrl: msg.gatewayApiUrl,
      pairingToken: msg.pairingToken,
      setupSessionId: msg.setupSessionId,
      deviceLabel: msg.deviceLabel || 'Dashboard auto-connect',
    }, (response) => {
      if (B.runtime.lastError) {
        window.postMessage({ type: 'ZTA_AUTOCONNECT_RESPONSE', success: false, error: B.runtime.lastError.message }, '*');
        return;
      }
      window.postMessage({
        type: 'ZTA_AUTOCONNECT_RESPONSE',
        success: Boolean(response?.success),
        deviceId: response?.deviceId,
        error: response?.error,
      }, '*');
    });
    return;
  }

  // Text selection helper
  if (msg.type === 'ZTA_GATEWAY_SELECTED_TEXT_REQUEST') {
    window.postMessage({ type: 'ZTA_GATEWAY_SELECTED_TEXT_RESPONSE', selection: window.getSelection()?.toString() || '' }, '*');
  }
});
