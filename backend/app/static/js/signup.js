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
    $("signupForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector("button");
      btn.disabled = true;
      $("result").textContent = "Creating account...";
      $("result").className = "result-box";
      try {
        const body = { email: $("email").value, username: $("username").value, password: $("password").value };
        const user = await request(`${api}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        const token = await login(body.username, body.password);
        sessionStorage.setItem("zta_token", token.access_token);
        $("result").className = "result-box ok";
        $("result").textContent = `Account created for ${user.username}. Opening dashboard...`;
        setTimeout(() => { window.location.href = "/dashboard"; }, 600);
      } catch (err) {
        $("result").className = "result-box error";
        $("result").textContent = String(err.message || err);
        btn.disabled = false;
      }
    });