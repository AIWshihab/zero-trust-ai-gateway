const $ = (id) => document.getElementById(id);
const EXTENSION_VERSION = chrome.runtime.getManifest().version;

function normalizeBaseUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function setStatus(connected, text) {
  $("statusDot").classList.toggle("off", !connected);
  $("statusText").textContent = text;
}

function applyConnectUrl(value) {
  const raw = String(value || "").trim();
  if (!raw) return false;
  try {
    const parsed = new URL(raw);
    const token = parsed.searchParams.get("token") || parsed.searchParams.get("pairing_token");
    const gatewayApiUrl = parsed.searchParams.get("gateway_api_url") || parsed.origin;
    const setupSessionId = parsed.searchParams.get("setup_session_id") || "";
    if (!token || !gatewayApiUrl) return false;
    $("connectUrl").value = raw;
    $("gatewayUrl").value = normalizeBaseUrl(gatewayApiUrl);
    $("pairingToken").value = token;
    $("setupSessionId").value = setupSessionId;
    return true;
  } catch {
    return false;
  }
}

async function prefillFromActiveTab() {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const activeUrl = tabs?.[0]?.url || "";
    if (activeUrl.includes("/dashboard/extension/connect")) {
      const filled = applyConnectUrl(activeUrl);
      if (filled) {
        // Auto-connect: no user paste needed
        setTimeout(connect, 300);
      }
    }
  } catch {
    // The popup still supports manual paste when tab URL access is unavailable.
  }
}

function decisionClass(decision) {
  const value = String(decision || "").toLowerCase();
  if (value === "allow") return "allow";
  if (value === "challenge") return "challenge";
  if (value === "block") return "block";
  return "";
}

async function loadState() {
  const data = await chrome.storage.local.get(["gatewayApiUrl", "accessToken", "deviceId", "modelId"]);
  if (data.gatewayApiUrl) $("gatewayUrl").value = data.gatewayApiUrl;
  if (data.modelId) $("modelId").value = data.modelId;
  setStatus(Boolean(data.accessToken), data.accessToken ? `Connected · device ${data.deviceId}` : "Not connected");
  if (!data.accessToken) {
    setStatus(false, "Connect to Zero Trust Gateway");
  }
}

async function connect() {
  const gatewayApiUrl = normalizeBaseUrl($("gatewayUrl").value);
  const pairingToken = $("pairingToken").value.trim();
  const setupSessionId = $("setupSessionId").value.trim();
  if (!gatewayApiUrl || !pairingToken) {
    $("output").textContent = "Enter Gateway API URL and pairing token.";
    return;
  }

  $("connectBtn").disabled = true;
  try {
    const response = await fetch(`${gatewayApiUrl}/api/v1/extension/register-device`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pairing_token: pairingToken,
        setup_session_id: setupSessionId || null,
        browser_name: "Chrome",
        extension_version: EXTENSION_VERSION,
        user_agent: navigator.userAgent,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "",
        platform: navigator.platform || "",
        device_label: $("deviceLabel").value.trim() || "Browser extension"
      })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Pairing failed");
    await chrome.storage.local.set({
      gatewayApiUrl,
      accessToken: data.access_token,
      deviceId: data.device_id,
      modelId: $("modelId").value || "1"
    });
    $("pairingToken").value = "";
    $("connectUrl").value = "";
    $("setupSessionId").value = "";
    setStatus(true, `Connected · device ${data.device_id}`);
    $("output").textContent = "Connected. Prompts will now route through the gateway.";
  } catch (err) {
    $("output").textContent = err.message || "Connection failed.";
    setStatus(false, "Not connected");
  } finally {
    $("connectBtn").disabled = false;
  }
}

async function disconnect() {
  await chrome.storage.local.remove(["accessToken", "deviceId"]);
  setStatus(false, "Not connected");
  $("output").textContent = "Disconnected locally. Revoke the device/session in the gateway dashboard if needed.";
}

async function sendPrompt() {
  const state = await chrome.storage.local.get(["gatewayApiUrl", "accessToken", "deviceId"]);
  const gatewayApiUrl = normalizeBaseUrl($("gatewayUrl").value || state.gatewayApiUrl);
  const accessToken = state.accessToken;
  const deviceId = state.deviceId;
  const prompt = $("prompt").value.trim();
  const modelId = Number($("modelId").value || 1);
  if (!gatewayApiUrl || !accessToken || !deviceId) {
    $("output").textContent = "Connect the extension first.";
    return;
  }
  if (!prompt) {
    $("output").textContent = "Enter a prompt.";
    return;
  }

  $("sendBtn").disabled = true;
  $("decisionLine").textContent = "Evaluating...";
  $("output").textContent = "";
  await chrome.storage.local.set({ gatewayApiUrl, modelId: String(modelId) });
  try {
    const response = await fetch(`${gatewayApiUrl}/api/v1/usage/infer`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${accessToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model_id: modelId,
        prompt,
        messages: [{ role: "user", content: prompt }],
        parameters: {
          gateway_context: {
            source: "browser_extension",
            device_id: deviceId,
            extension_version: EXTENSION_VERSION,
            browser_name: "Chrome",
            user_agent: navigator.userAgent,
            timestamp: new Date().toISOString()
          }
        }
      })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail?.explanation || data.detail?.reason || data.detail || "Gateway request failed");
    const decision = String(data.decision || "unknown").toUpperCase();
    $("decisionLine").innerHTML = `<span class="decision ${decisionClass(data.decision)}">${decision}</span> · risk ${Math.round(Number(data.effective_risk || data.prompt_risk_score || 0) * 100)}%`;
    $("output").textContent = data.output || data.reason || "No model output returned.";
  } catch (err) {
    $("decisionLine").textContent = "Request failed";
    $("output").textContent = err.message || "Gateway request failed.";
  } finally {
    $("sendBtn").disabled = false;
  }
}

$("connectBtn").addEventListener("click", connect);
$("disconnectBtn").addEventListener("click", disconnect);
$("sendBtn").addEventListener("click", sendPrompt);
$("connectUrl").addEventListener("input", (event) => applyConnectUrl(event.target.value));
loadState().then(prefillFromActiveTab);
