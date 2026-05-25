from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


GETTING_STARTED_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Getting Started — Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #08080a;
      --bg-1: #0d0f14;
      --bg-2: #111420;
      --bg-3: #181b28;
      --border: rgba(255,255,255,.08);
      --b2: rgba(255,255,255,.13);
      --cyan: #00d4ff;
      --cyan-d: rgba(0,212,255,.1);
      --green: #22d3a0;
      --red: #ff4d6d;
      --text: #edf2ff;
      --muted: #7c8499;
      --mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { min-height: 100vh; background: var(--bg); color: var(--text); }
    .shell { padding: 20px clamp(14px,3vw,32px) 32px; display: grid; gap: 16px; }
    .page-header { display: grid; grid-template-columns: minmax(280px,1fr) auto; gap: 16px; align-items: start; }
    .page-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
    .page-eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .page-header h1 { font-size: clamp(24px,4vw,40px); font-weight: 700; color: var(--text); line-height: 1.1; margin-bottom: 8px; }
    .page-header p { font-size: 14px; color: var(--muted); line-height: 1.6; max-width: 680px; }
    .hdr-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    a, button {
      border: 1px solid var(--b2);
      border-radius: 7px;
      padding: 9px 14px;
      color: var(--text);
      background: var(--bg-2);
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      transition: border-color .18s, background .18s;
    }
    a:hover, button:hover { border-color: var(--cyan); background: var(--bg-3); }
    a.primary { background: var(--cyan); color: #000; border-color: var(--cyan); font-weight: 700; }
    a.primary:hover { background: #00bde8; border-color: #00bde8; }
    .feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .card {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 16px;
      transition: border-color .2s;
    }
    .card:hover { border-color: rgba(0,212,255,.18); }
    .card-label { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
    .card-label::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .card h2 { font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
    .card p { font-size: 13px; color: var(--muted); line-height: 1.55; }
    .card .card-link { margin-top: 12px; }
    .wide { display: grid; grid-template-columns: 1.08fr .92fr; gap: 14px; }
    .steps { display: grid; gap: 10px; }
    .step { display: grid; grid-template-columns: 32px 1fr; gap: 12px; align-items: start; padding: 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-2); transition: border-color .2s; }
    .step:hover { border-color: rgba(0,212,255,.2); }
    .step-num { width: 28px; height: 28px; border-radius: 6px; display: grid; place-items: center; background: var(--cyan); color: #000; font-weight: 700; font-size: 13px; }
    .step h3 { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
    .step p { font-size: 13px; color: var(--muted); line-height: 1.5; }
    .quick-list { list-style: none; display: grid; gap: 0; }
    .quick-list li { display: grid; grid-template-columns: 120px 1fr; gap: 10px; padding: 9px 0; border-bottom: 1px solid var(--border); font-size: 13px; line-height: 1.45; color: var(--muted); }
    .quick-list li:last-child { border-bottom: none; }
    .quick-list b { color: var(--text); font-weight: 600; }
    .info-items { display: grid; gap: 10px; margin-top: 10px; }
    .info-item { border: 1px solid var(--border); border-radius: 7px; padding: 12px; background: var(--bg-2); }
    .info-item strong { display: block; font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
    .info-item span { font-size: 12px; color: var(--muted); line-height: 1.5; }
    .notice { border: 1px solid rgba(0,212,255,.2); border-radius: 8px; padding: 14px 16px; background: var(--cyan-d); }
    .notice h2 { font-size: 14px; color: var(--cyan); margin-bottom: 6px; }
    .notice p { font-size: 13px; color: var(--muted); }
    @media (max-width: 980px) { .feature-grid, .wide, .page-header { grid-template-columns: 1fr; } .feature-grid { grid-template-columns: repeat(2,1fr); } }
    @media (max-width: 560px) { .quick-list li { grid-template-columns: 1fr; } .feature-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="page-header">
      <div>
        <div class="page-eyebrow">Beginner Guide</div>
        <h1>Use The Gateway In 5 Minutes</h1>
        <p>This page is for non-technical users. Follow the steps in order: start with Secure Chat, check Security Monitor, then connect the browser extension if you want Chrome prompts protected by the gateway.</p>
      </div>
      <div class="hdr-row">
        <a class="primary" href="/dashboard/chat">Start Secure Chat</a>
        <a href="/dashboard/extension/install">Add Browser Extension</a>
      </div>
    </section>

    <section class="feature-grid">
      <article class="card">
        <div class="card-label">Start here</div>
        <h2>Secure Chat</h2>
        <p>Ask the AI through the gateway. The gateway checks risk first, then allows, challenges, or blocks the request.</p>
        <div class="card-link"><a href="/dashboard/chat">Open Secure Chat</a></div>
      </article>
      <article class="card">
        <div class="card-label">Watch activity</div>
        <h2>Security Monitor</h2>
        <p>See real requests, blocked prompts, device events, alerts, extension activity, and model/provider failures.</p>
        <div class="card-link"><a href="/dashboard/security-monitor">Open Security Monitor</a></div>
      </article>
      <article class="card">
        <div class="card-label">Browser protection</div>
        <h2>Browser Extension</h2>
        <p>Connect Chrome to the gateway. The dashboard automates pairing, but Chrome still requires user-approved installation.</p>
        <div class="card-link"><a href="/dashboard/extension/install">Open Extension Setup</a></div>
      </article>
    </section>

    <section class="wide">
      <article class="card">
        <div class="card-label">Simple Walkthrough</div>
        <div class="steps" style="margin-top:12px">
          <div class="step">
            <div class="step-num">1</div>
            <div><h3>Chat safely</h3><p>Open Secure Chat, pick a model, type a message, and send it. If the request is safe, the gateway lets it through.</p></div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div><h3>Check what happened</h3><p>Open Security Monitor. Look for Allowed, Challenged, Blocked, request risk, device events, and any provider errors.</p></div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div><h3>Connect Chrome</h3><p>Open Add Browser Extension. Local users download the developer extension; production users use the Chrome Web Store button.</p></div>
          </div>
          <div class="step">
            <div class="step-num">4</div>
            <div><h3>Paste the connect URL</h3><p>The setup page creates a one-time token. Paste the connect URL into the extension popup and click Connect.</p></div>
          </div>
          <div class="step">
            <div class="step-num">5</div>
            <div><h3>Test and monitor</h3><p>Send a prompt from the extension. Then check Security Monitor for browser extension activity and decisions.</p></div>
          </div>
        </div>
      </article>

      <article class="card">
        <div class="card-label">What The Buttons Mean</div>
        <ul class="quick-list" style="margin-top:12px">
          <li><b>Secure Chat</b><span>Main place to talk to AI through gateway protection.</span></li>
          <li><b>Models</b><span>Shows which AI models are available and whether they are ready.</span></li>
          <li><b>Security Monitor</b><span>Shows real security activity, not demo data.</span></li>
          <li><b>Policy Engine</b><span>Admin/security area for controls and rules.</span></li>
          <li><b>Account</b><span>Password, sessions, devices, and security settings.</span></li>
          <li><b>Add Extension</b><span>Connects Chrome to the gateway with a one-time setup token.</span></li>
        </ul>
      </article>
    </section>

    <section class="wide">
      <article class="card">
        <div class="card-label">Browser Extension Setup</div>
        <div class="info-items">
          <div class="info-item"><strong>Local development</strong><span>Click Download Developer Extension, open chrome://extensions, enable Developer Mode, choose Load unpacked, and select the browser-extension folder.</span></div>
          <div class="info-item"><strong>Production</strong><span>Click Add to Chrome. Chrome opens the Chrome Web Store. The user must approve installation there.</span></div>
          <div class="info-item"><strong>Connection</strong><span>Copy the connect URL from the setup page, paste it into the extension popup, and click Connect.</span></div>
          <div class="info-item"><strong>Important truth</strong><span>A website cannot silently install a Chrome extension. This dashboard automates pairing, not Chrome installation.</span></div>
        </div>
      </article>

      <article class="card">
        <div class="card-label">Fix Common Problems</div>
        <ul class="quick-list" style="margin-top:12px">
          <li><b>Cannot login</b><span>Create an account from the signup page or check the password.</span></li>
          <li><b>No chat reply</b><span>Check model readiness and provider API keys. Provider failure is shown honestly.</span></li>
          <li><b>Token expired</b><span>Go back to extension setup and click Refresh Token.</span></li>
          <li><b>Extension not detected</b><span>Reload the dashboard page after installing or loading the extension.</span></li>
          <li><b>Security Monitor empty</b><span>Send a chat or extension prompt first so the gateway has real events to show.</span></li>
          <li><b>Revoked device</b><span>That device is blocked. Admin/user must reconnect or allow a new device.</span></li>
        </ul>
      </article>
    </section>

    <section class="notice">
      <h2>// Remember</h2>
      <p>The extension stores only a gateway-issued token and device id. Model API keys and gateway secrets stay on the backend. All allow, challenge, and block decisions happen in the backend.</p>
    </section>
  </main>
  <script>
    const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/getting-started";
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
