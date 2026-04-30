SIGNUP_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Join Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      --text: #fff7ea;
      --muted: #d3b99a;
      --amber: #ff9f1c;
      --red: #ff4d3d;
      --ink: #080604;
      --cream: #fff1d5;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 18% 12%, rgba(255,159,28,.28), transparent 28%),
        radial-gradient(circle at 86% 3%, rgba(255,77,61,.16), transparent 30%),
        linear-gradient(135deg, #090806, #15100b 52%, #2b1207);
      display: grid;
      place-items: center;
      padding: 22px;
      overflow-x: hidden;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,241,213,.08) 2px, transparent 2px),
        linear-gradient(90deg, rgba(255,241,213,.08) 2px, transparent 2px),
        radial-gradient(circle, rgba(255,255,255,.16) 1px, transparent 1.5px);
      background-size: 118px 66px, 118px 66px, 9px 9px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), transparent);
    }
    body::after {
      content: "";
      position: fixed;
      inset: -18% -8%;
      pointer-events: none;
      background: repeating-linear-gradient(112deg, transparent 0 24px, rgba(255,255,255,.08) 25px 27px, transparent 28px 56px);
      opacity: .5;
      transform: skewY(-5deg);
      animation: rush 12s linear infinite;
    }
    .wrap {
      position: relative;
      z-index: 1;
      width: min(1040px, 100%);
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 18px;
      align-items: stretch;
    }
    .hero, .card {
      border: 2px solid var(--ink);
      border-radius: 6px;
      background: rgba(20, 18, 16, .9);
      box-shadow: 8px 8px 0 rgba(0,0,0,.72), 0 24px 80px rgba(0,0,0,.36);
      overflow: hidden;
      position: relative;
    }
    .hero::after, .card::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: repeating-linear-gradient(-12deg, transparent 0 18px, rgba(255,159,28,.055) 19px 21px);
    }
    .inner { position: relative; z-index: 1; padding: clamp(20px, 4vw, 38px); }
    h1 {
      margin: 0;
      font-size: clamp(34px, 6vw, 74px);
      line-height: .9;
      text-transform: uppercase;
      letter-spacing: 0;
      text-shadow: 4px 4px 0 var(--ink), 8px 8px 0 rgba(255,159,28,.34);
    }
    h2 { margin: 0 0 14px; color: var(--amber); text-transform: uppercase; letter-spacing: .08em; text-shadow: 2px 2px 0 #000; }
    p { color: var(--cream); font-weight: 680; line-height: 1.55; max-width: 620px; }
    .ball {
      width: 108px;
      height: 108px;
      border-radius: 50%;
      margin-top: 30px;
      background:
        radial-gradient(circle at 35% 30%, #fff8e8 0 18%, transparent 19%),
        repeating-linear-gradient(45deg, transparent 0 16px, rgba(0,0,0,.82) 17px 20px, transparent 21px 34px),
        radial-gradient(circle, #fff1d5 0 36%, #ff9f1c 37% 66%, #111 67% 70%, rgba(255,159,28,.22) 71%);
      box-shadow: 0 0 44px rgba(255,159,28,.78), 7px 7px 0 rgba(0,0,0,.75);
      animation: serve 2.6s ease-in-out infinite;
    }
    label { display: grid; gap: 6px; font-size: 12px; font-weight: 800; color: var(--cream); margin-bottom: 12px; }
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
      display: inline-flex;
      justify-content: center;
    }
    a.secondary { color: var(--cream); background: rgba(255,241,213,.08); border-color: rgba(255,178,77,.42); }
    .row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
    pre {
      margin: 14px 0 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: rgba(8,6,4,.82);
      border: 2px solid rgba(255,178,77,.24);
      border-radius: 8px;
      padding: 12px;
      min-height: 90px;
      color: var(--cream);
    }
    .error { color: var(--red); }
    @keyframes rush { to { transform: skewY(-5deg) translateX(-120px); } }
    @keyframes serve { 0%, 100% { transform: translateY(0) rotate(-8deg); } 50% { transform: translateY(-14px) rotate(16deg); } }
    @media (max-width: 860px) { .wrap { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="inner">
        <h1>Join The Gateway</h1>
        <p>Create your account, build trust score from clean usage, and enter the protected AI court. Every request goes through prompt defense before it reaches a model.</p>
        <div class="ball" aria-hidden="true"></div>
      </div>
    </section>
    <section class="card">
      <div class="inner">
        <h2>Registration</h2>
        <label>Email <input id="email" type="email" autocomplete="email" placeholder="you@example.com" /></label>
        <label>Username <input id="username" autocomplete="username" placeholder="hinata-sec" /></label>
        <label>Password <input id="password" type="password" autocomplete="new-password" placeholder="At least 6 characters" /></label>
        <div class="row">
          <button id="signupBtn">Create Account</button>
          <a class="secondary" href="/dashboard">Back To Login</a>
        </div>
        <pre id="result">Ready for first serve.</pre>
      </div>
    </section>
  </main>
  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      return data;
    }
    async function login(username, password) {
      const form = new URLSearchParams();
      form.set("username", username);
      form.set("password", password);
      return request(`${api}/auth/token`, { method: "POST", body: form });
    }
    async function signup() {
      $("signupBtn").disabled = true;
      $("result").className = "";
      try {
        const body = { email: $("email").value, username: $("username").value, password: $("password").value };
        const user = await request(`${api}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        const token = await login(body.username, body.password);
        sessionStorage.setItem("zta_token", token.access_token);
        $("result").textContent = `Account created for ${user.username}. Opening dashboard...`;
        setTimeout(() => { window.location.href = `/dashboard?token=${encodeURIComponent(token.access_token)}`; }, 600);
      } catch (err) {
        $("result").className = "error";
        $("result").textContent = String(err.message || err);
      } finally {
        $("signupBtn").disabled = false;
      }
    }
    $("signupBtn").addEventListener("click", signup);
  </script>
</body>
</html>
"""
