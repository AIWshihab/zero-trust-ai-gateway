from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Login — Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --bg:     #08080a;
      --bg-1:   #0d0f14;
      --bg-2:   #111420;
      --bg-3:   #181b28;
      --border: rgba(255,255,255,.08);
      --b2:     rgba(255,255,255,.13);
      --cyan:   #00d4ff;
      --cyan-d: rgba(0,212,255,.1);
      --green:  #22d3a0;
      --red:    #ff4d6d;
      --text:   #edf2ff;
      --muted:  #7c8499;
      --mono:   'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      display: grid;
      place-items: center;
      padding: 20px;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image: linear-gradient(rgba(255,255,255,.028) 1px, transparent 1px);
      background-size: 100% 40px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.6), rgba(0,0,0,.02));
    }
    .wrap {
      position: relative;
      z-index: 1;
      width: min(1040px, 100%);
      display: grid;
      grid-template-columns: 1fr 400px;
      gap: 20px;
      align-items: stretch;
    }
    .hero {
      border: 1px solid var(--b2);
      border-radius: 10px;
      background: var(--bg-1);
      padding: 40px;
      display: flex;
      flex-direction: column;
      gap: 28px;
    }
    .logo-line { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
    .logo-line::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .hero h1 { font-size: clamp(28px,4.5vw,50px); font-weight: 800; line-height: 1.08; color: var(--text); letter-spacing: -.5px; }
    .hero h1 span { color: var(--cyan); }
    .hero-desc { font-size: 15px; line-height: 1.65; color: var(--muted); max-width: 520px; }
    .features { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: auto; }
    .feature { border: 1px solid var(--border); border-radius: 8px; padding: 14px; background: var(--bg-2); transition: border-color .2s; }
    .feature:hover { border-color: rgba(0,212,255,.28); }
    .feature b { display: block; font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 5px; }
    .feature span { font-size: 12px; line-height: 1.5; color: var(--muted); }
    .status-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 8px var(--green); }
    .auth-card {
      border: 1px solid var(--b2);
      border-radius: 10px;
      background: var(--bg-1);
      padding: 30px 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .auth-title p { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
    .auth-title p span { color: var(--cyan); font-family: var(--mono); }
    .auth-title h2 { font-size: 18px; font-weight: 700; color: var(--text); }
    .form-section { display: flex; flex-direction: column; gap: 14px; }
    label { display: grid; gap: 6px; font-size: 12px; font-weight: 600; color: var(--muted); letter-spacing: .04em; text-transform: uppercase; }
    input {
      width: 100%;
      border: 1px solid var(--b2);
      border-radius: 7px;
      background: var(--bg-3);
      color: var(--text);
      padding: 11px 13px;
      font: inherit;
      font-size: 14px;
      outline: none;
      transition: border-color .18s, box-shadow .18s;
      text-transform: none;
      letter-spacing: normal;
      font-weight: 400;
    }
    input:focus { border-color: rgba(0,212,255,.42); box-shadow: 0 0 0 3px rgba(0,212,255,.08); }
    input::placeholder { color: var(--muted); }
    .submit-btn {
      width: 100%;
      padding: 12px;
      border-radius: 7px;
      border: 0;
      background: var(--cyan);
      color: #000;
      font-weight: 700;
      font-size: 14px;
      cursor: pointer;
      transition: background .15s, opacity .15s;
    }
    .submit-btn:hover { background: #00bde8; }
    .submit-btn:disabled { opacity: .55; cursor: wait; }
    .alt-link { text-align: center; font-size: 13px; color: var(--muted); }
    .alt-link a { color: var(--cyan); text-decoration: none; }
    .alt-link a:hover { text-decoration: underline; }
    .result-box {
      font-size: 13px;
      line-height: 1.5;
      padding: 12px;
      border-radius: 7px;
      border: 1px solid var(--border);
      background: var(--bg-2);
      color: var(--muted);
      min-height: 52px;
      word-break: break-word;
    }
    .result-box.error { color: var(--red); border-color: rgba(255,77,109,.28); background: rgba(255,77,109,.06); }
    .result-box.ok    { color: var(--green); border-color: rgba(34,211,160,.28); background: rgba(34,211,160,.06); }
    @media (max-width: 860px) { .wrap { grid-template-columns: 1fr; max-width: 440px; } .hero { padding: 24px; } .features { grid-template-columns: 1fr; } }
  </style>
</head>
<body class="no-shell">
  <main class="wrap">
    <section class="hero">
      <div>
        <div class="logo-line">Zero Trust AI Gateway</div>
        <h1 style="margin-top:14px">Behaviour-Aware<br><span>Secure AI</span> Inference</h1>
        <p class="hero-desc" style="margin-top:14px">A research-grade Zero Trust gateway for secure AI model serving. Every request is screened, scored, and decided before inference runs.</p>
      </div>
      <div class="features">
        <div class="feature"><b>Prompt Defence</b><span>Injection detection and risk scoring before inference runs.</span></div>
        <div class="feature"><b>Behaviour Scoring</b><span>Trust score builds from request history and security events.</span></div>
        <div class="feature"><b>Policy Engine</b><span>Deterministic controls explain every allow / challenge / block.</span></div>
        <div class="feature"><b>Full Audit Trail</b><span>Structured record of every decision with risk metrics.</span></div>
      </div>
      <div class="status-row"><span class="dot"></span>Gateway online · MSc Dissertation Project</div>
    </section>

    <section class="auth-card">
      <div class="auth-title">
        <p><span>//</span> Authentication</p>
        <h2>Enter the Gateway</h2>
      </div>
      <form id="loginForm" class="form-section">
        <label>Username <input id="username" autocomplete="username" placeholder="your-username" /></label>
        <label>Password <input id="password" type="password" autocomplete="current-password" placeholder="••••••••" /></label>
        <button class="submit-btn" type="submit">Sign In</button>
      </form>
      <div class="alt-link">No account? <a href="/signup">Create one</a></div>
      <div id="result" class="result-box">Enter credentials to continue.</div>
    </section>
  </main>

  <script>
    const api = "/api/v1";
    const next = new URLSearchParams(location.search).get("next") || "/dashboard";
    const $ = (id) => document.getElementById(id);
    if (sessionStorage.getItem("zta_token")) location.href = next;

    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? (data.detail || JSON.stringify(data)) : data);
      return data;
    }

    $("loginForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector("button");
      btn.disabled = true;
      $("result").textContent = "Authenticating...";
      $("result").className = "result-box";
      try {
        const form = new URLSearchParams();
        form.set("username", $("username").value);
        form.set("password", $("password").value);
        const data = await request(`${api}/auth/token`, { method: "POST", body: form });
        sessionStorage.setItem("zta_token", data.access_token);
        $("result").className = "result-box ok";
        $("result").textContent = "Authenticated. Entering gateway...";
        setTimeout(() => { location.href = next; }, 400);
      } catch (err) {
        $("result").className = "result-box error";
        $("result").textContent = err?.message || "Login failed.";
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
