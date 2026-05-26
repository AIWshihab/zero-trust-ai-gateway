// Zero Trust AI Gateway — Background Service Worker
// Cross-browser: works in Chrome, Edge, Brave, and Firefox 128+

const B = globalThis.browser ?? globalThis.chrome;
const MANIFEST = B.runtime.getManifest();
const EXTENSION_VERSION = MANIFEST.version;

// ── Detect browser ───────────────────────────────────────────────────────────
function detectBrowser() {
  const ua = (typeof navigator !== 'undefined' ? navigator.userAgent : '') || '';
  if (typeof browser !== 'undefined' && browser.runtime) return 'Firefox';
  if (ua.includes('Edg/')) return 'Edge';
  if (ua.includes('Brave') || ua.includes('brave')) return 'Brave';
  if (ua.includes('OPR/') || ua.includes('Opera')) return 'Opera';
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Safari')) return 'Safari';
  return 'Unknown';
}

B.runtime.onInstalled.addListener(() => {
  B.storage.local.get(['gatewayApiUrl'], (state) => {
    if (!state.gatewayApiUrl) {
      B.storage.local.set({ gatewayApiUrl: 'http://localhost:8000', modelId: '1' });
    }
  });
});

// ── Register device ──────────────────────────────────────────────────────────
async function autoRegister({ gatewayApiUrl, pairingToken, setupSessionId, deviceLabel }) {
  const base = String(gatewayApiUrl || 'http://localhost:8000').replace(/\/+$/, '');
  const browserName = detectBrowser();
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : '';

  const res = await fetch(`${base}/api/v1/extension/register-device`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pairing_token: pairingToken,
      setup_session_id: setupSessionId || null,
      browser_name: browserName,
      extension_version: EXTENSION_VERSION,
      user_agent: ua,
      timezone: (typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : '') || 'UTC',
      platform: (typeof navigator !== 'undefined' ? navigator.platform : '') || '',
      device_label: deviceLabel || `${browserName} Extension`,
    }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Pairing failed');

  await B.storage.local.set({
    gatewayApiUrl: base,
    accessToken: data.access_token,
    deviceId: data.device_id,
    modelId: '1',
    browserName,
  });
  return { success: true, deviceId: data.device_id };
}

// ── Gateway ZT check for intercepted browser requests ────────────────────────
async function checkRequestWithGateway({ gatewayApiUrl, accessToken, extractedPrompt, url }) {
  const base = String(gatewayApiUrl || 'http://localhost:8000').replace(/\/+$/, '');
  try {
    const res = await fetch(`${base}/api/v1/gateway/check`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        target_url: url || '',
        extracted_prompt: extractedPrompt || '',
        source: 'browser_intercept',
      }),
    });
    const data = await res.json().catch(() => ({}));
    return { decision: data.decision || 'allow', reason: data.reason || '', risk_score: data.risk_score || 0 };
  } catch {
    return { decision: 'allow', reason: 'Gateway unreachable — fail open' };
  }
}

// ── Message router ───────────────────────────────────────────────────────────
B.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ZTA_AUTO_REGISTER') {
    autoRegister(message)
      .then(result => sendResponse(result))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'ZTA_CHECK_REQUEST') {
    checkRequestWithGateway(message)
      .then(result => sendResponse(result))
      .catch(() => sendResponse({ decision: 'allow' }));
    return true;
  }
});
