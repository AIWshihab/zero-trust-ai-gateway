const EXTENSION_VERSION = chrome.runtime.getManifest().version;

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["gatewayApiUrl"], (state) => {
    if (!state.gatewayApiUrl) {
      chrome.storage.local.set({ gatewayApiUrl: "http://localhost:8000", modelId: "1" });
    }
  });
});

async function autoRegister({ gatewayApiUrl, pairingToken, setupSessionId, deviceLabel }) {
  const base = String(gatewayApiUrl || "http://localhost:8000").replace(/\/+$/, "");
  const response = await fetch(`${base}/api/v1/extension/register-device`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pairing_token: pairingToken,
      setup_session_id: setupSessionId || null,
      browser_name: "Chrome",
      extension_version: EXTENSION_VERSION,
      user_agent: "Chrome Extension / Zero Trust AI Gateway",
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
      platform: "Chrome Extension",
      device_label: deviceLabel || "Browser extension"
    })
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Pairing failed");
  await chrome.storage.local.set({
    gatewayApiUrl: base,
    accessToken: data.access_token,
    deviceId: data.device_id,
    modelId: "1"
  });
  return { success: true, deviceId: data.device_id };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "ZTA_AUTO_REGISTER") {
    autoRegister(message)
      .then(result => sendResponse(result))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }
});
