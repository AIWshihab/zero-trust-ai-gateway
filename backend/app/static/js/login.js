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