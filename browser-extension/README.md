# Zero Trust AI Gateway Browser Extension

Manifest V3 Chrome extension for sending browser prompts through the Zero Trust AI Gateway.

## Security Model

- Do not put model provider API keys in this extension.
- Do not put gateway secrets in this extension.
- The extension stores only a gateway-issued access token and device id in `chrome.storage.local`.
- The extension is an untrusted client. All policy, prompt inspection, model routing, and output decisions happen in the backend.
- Revoke extension access from the gateway device/session controls if a browser is lost or compromised.

## Load In Chrome Developer Mode

1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select this `browser-extension` folder.
5. Pin the extension from the Chrome toolbar.

## Connect To Local Backend

1. Start the backend, for example:
   ```bash
   cd backend
   ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Open `http://localhost:8000/dashboard/extension/install`.
3. Copy the generated connect URL.
4. Open the extension popup.
5. Paste the connect URL and click **Connect**.

## Connect To Live Backend

1. Open your deployed gateway at `https://your-gateway.example.com/dashboard/extension/install`.
2. Use **Add to Chrome** to open the Chrome Web Store listing.
3. Open the extension popup.
4. Paste the dashboard connect URL and click **Connect**.

If your live backend is not reachable from the extension, verify CORS and host permissions. This MVP manifest allows localhost and HTTPS origins.

## Sending A Prompt

1. Enter a model id visible to your account.
2. Enter a prompt.
3. Click **Send Prompt**.
4. The extension calls `/api/v1/usage/infer` and displays the gateway decision, risk score, and model output when allowed.

Every request includes extension metadata in `gateway_context`, including `device_id`, extension version, user agent, timestamp, and `source = browser_extension`.

## Chrome Web Store Publishing

Chrome inline installation is not supported for normal websites, and the dashboard cannot silently install this extension. When this extension is published, set `CHROME_EXTENSION_STORE_URL` so the dashboard's **Add to Chrome** button opens the public listing. Until then, use Developer Mode for testing.
