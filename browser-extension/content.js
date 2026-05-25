window.addEventListener("message", (event) => {
  if (event.source !== window) return;

  if (event.data?.type === "ZTA_GATEWAY_EXTENSION_PING") {
    window.postMessage({
      type: "ZTA_GATEWAY_EXTENSION_DETECTED",
      nonce: event.data.nonce,
      extensionVersion: chrome.runtime.getManifest().version
    }, "*");
    return;
  }

  if (event.data?.type === "ZTA_AUTOCONNECT_REQUEST") {
    chrome.runtime.sendMessage({
      type: "ZTA_AUTO_REGISTER",
      gatewayApiUrl: event.data.gatewayApiUrl,
      pairingToken: event.data.pairingToken,
      setupSessionId: event.data.setupSessionId,
      deviceLabel: event.data.deviceLabel || "Dashboard auto-connect"
    }, (response) => {
      if (chrome.runtime.lastError) {
        window.postMessage({ type: "ZTA_AUTOCONNECT_RESPONSE", success: false, error: chrome.runtime.lastError.message }, "*");
        return;
      }
      window.postMessage({
        type: "ZTA_AUTOCONNECT_RESPONSE",
        success: Boolean(response?.success),
        deviceId: response?.deviceId,
        error: response?.error
      }, "*");
    });
    return;
  }

  if (event.data?.type === "ZTA_GATEWAY_SELECTED_TEXT_REQUEST") {
    const selection = window.getSelection()?.toString() || "";
    window.postMessage({ type: "ZTA_GATEWAY_SELECTED_TEXT_RESPONSE", selection }, "*");
  }
});
