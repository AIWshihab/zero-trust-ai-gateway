LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Login - Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --text: #fff7ea;
      --muted: #d4c0a4;
      --soft: #aab3bf;
      --amber: #ffb13b;
      --red: #ff4d3d;
      --ink: #080604;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      color: var(--text);
      background:
        linear-gradient(118deg, rgba(255,255,255,.035) 0 1px, transparent 1px 70px),
        radial-gradient(circle at 18% 12%, rgba(255,159,28,.28), transparent 30%),
        linear-gradient(135deg, #070706, #15100b 52%, #2b1207);
      display: grid;
      place-items: center;
      padding: 20px;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,241,213,.075) 2px, transparent 2px),
        linear-gradient(90deg, rgba(255,241,213,.075) 2px, transparent 2px);
      background-size: 116px 64px, 116px 64px;
      opacity: .45;
    }
    .wrap {
      width: min(1080px, 100%);
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: minmax(300px, 1fr) 430px;
      gap: 18px;
      align-items: stretch;
    }
    .hero, .card {
      border: 2px solid var(--ink);
      border-radius: 7px;
      background: rgba(18,18,16,.94);
      box-shadow: 7px 7px 0 rgba(0,0,0,.72), 0 22px 70px rgba(0,0,0,.34);
      overflow: hidden;
      position: relative;
    }
    .hero::after, .card::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: repeating-linear-gradient(-12deg, transparent 0 19px, rgba(255,159,28,.05) 20px 22px);
    }
    .inner { position: relative; z-index: 1; padding: clamp(20px, 4vw, 40px); }
    .eyebrow { color: var(--amber); text-transform: uppercase; letter-spacing: .12em; font-weight: 950; font-size: 12px; }
    h1 {
      margin: 8px 0 12px;
      font-size: clamp(38px, 6vw, 76px);
      line-height: .9;
      text-transform: uppercase;
      text-shadow: 4px 4px 0 #000, 8px 8px 0 rgba(244,123,32,.34);
    }
    p { color: #ffe9c5; line-height: 1.55; font-weight: 720; max-width: 680px; }
    .feature-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 24px; }
    .feature { border: 2px solid rgba(255,178,77,.24); border-radius: 7px; padding: 12px; background: rgba(0,0,0,.22); }
    .feature b { display: block; color: #fff1d5; margin-bottom: 5px; }
    .feature span { color: var(--soft); font-size: 12px; line-height: 1.4; }
    .tabs { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 16px; }
    button, a {
      border: 2px solid var(--ink);
      border-radius: 7px;
      padding: 11px 13px;
      color: #150905;
      background: linear-gradient(135deg, #ffd164, #ff7a1a 52%, #f0441f);
      font-weight: 900;
      cursor: pointer;
      text-decoration: none;
      box-shadow: 4px 4px 0 rgba(0,0,0,.75);
      font: inherit;
    }
    button.secondary, a.secondary { color: var(--text); background: rgba(255,241,213,.08); border-color: rgba(255,178,77,.42); }
    button.active { filter: brightness(1.12); }
    label { display: grid; gap: 6px; font-size: 12px; font-weight: 850; color: #dce5f1; margin-bottom: 12px; }
    input {
      width: 100%;
      border: 2px solid rgba(255,178,77,.34);
      background: rgba(8,6,4,.82);
      color: var(--text);
      border-radius: 7px;
      padding: 12px;
      font: inherit;
      outline: none;
    }
    input:focus { border-color: var(--amber); box-shadow: 0 0 0 3px rgba(255,159,28,.17); }
    .hidden { display: none; }
    .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    pre {
      margin: 14px 0 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: rgba(8,6,4,.82);
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      min-height: 84px;
      color: #fff1d5;
    }
    .error { color: var(--red); }
    @media (max-width: 880px) { .wrap { grid-template-columns: 1fr; } .feature-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="inner">
        <div class="eyebrow">Zero Trust AI Gateway</div>
        <h1>Secure AI Access</h1>
        <p>Login once, then use the gateway chat, model registry, control plane, logs, and research dashboards without repeating credentials on every page.</p>
        <div class="feature-grid">
          <div class="feature"><b>Gateway Chat</b><span>Chat with registered models through prompt guard and formal risk scoring.</span></div>
          <div class="feature"><b>Model Registry</b><span>Add, scan, protect, and manage OpenAI, Hugging Face, local, or custom models.</span></div>
          <div class="feature"><b>Control Plane</b><span>Dynamic OWASP LLM controls and detection rules.</span></div>
          <div class="feature"><b>Research Metrics</b><span>Policy replay, counterfactuals, control effectiveness, and risk drift.</span></div>
        </div>
      </div>
    </section>
    <section class="card">
      <div class="inner">
        <div class="tabs">
          <button id="loginTab" class="active">Login</button>
          <button id="signupTab" class="secondary">Sign Up</button>
        </div>
        <form id="loginForm">
          <label>Username <input id="loginUsername" autocomplete="username" placeholder="smash" /></label>
          <label>Password <input id="loginPassword" type="password" autocomplete="current-password" placeholder="Password" /></label>
          <button type="submit">Enter Gateway</button>
        </form>
        <form id="signupForm" class="hidden">
          <label>Email <input id="email" type="email" autocomplete="email" placeholder="you@example.com" /></label>
          <label>Username <input id="signupUsername" autocomplete="username" placeholder="hinata-sec" /></label>
          <label>Password <input id="signupPassword" type="password" autocomplete="new-password" placeholder="At least 6 characters" /></label>
          <button type="submit">Create Account</button>
        </form>
        <pre id="result">Ready.</pre>
      </div>
    </section>
  </main>
  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    const next = new URLSearchParams(location.search).get("next") || "/dashboard";
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    function setMode(mode) {
      $("loginForm").classList.toggle("hidden", mode !== "login");
      $("signupForm").classList.toggle("hidden", mode !== "signup");
      $("loginTab").classList.toggle("active", mode === "login");
      $("signupTab").classList.toggle("active", mode === "signup");
      $("loginTab").classList.toggle("secondary", mode !== "login");
      $("signupTab").classList.toggle("secondary", mode !== "signup");
      $("result").textContent = mode === "login" ? "Ready." : "Create an account to enter the gateway.";
      $("result").className = "";
    }
    async function login(username, password) {
      const form = new URLSearchParams();
      form.set("username", username);
      form.set("password", password);
      const data = await request(`${api}/auth/token`, { method: "POST", body: form });
      sessionStorage.setItem("zta_token", data.access_token);
      location.href = next;
    }
    $("loginTab").addEventListener("click", () => setMode("login"));
    $("signupTab").addEventListener("click", () => setMode("signup"));
    $("loginForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      try { await login($("loginUsername").value, $("loginPassword").value); }
      catch (err) { $("result").className = "error"; $("result").textContent = String(err.message || err); }
    });
    $("signupForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const body = { email: $("email").value, username: $("signupUsername").value, password: $("signupPassword").value };
        await request(`${api}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        await login(body.username, body.password);
      } catch (err) {
        $("result").className = "error";
        $("result").textContent = String(err.message || err);
      }
    });
    if (sessionStorage.getItem("zta_token")) location.href = next;
  </script>
</body>
</html>
"""
