from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


ACCOUNT_SECURITY_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Account — Zero Trust AI Gateway</title>
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
      --amber: #f5a623;
      --red: #ff4d6d;
      --text: #edf2ff;
      --muted: #7c8499;
      --mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { min-height: 100vh; background: var(--bg); color: var(--text); padding: 20px; }
    .shell { width: min(980px, 100%); margin: 0 auto; display: grid; gap: 14px; }
    .page-banner {
      border: 1px solid var(--b2);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 18px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .banner-left {}
    .page-eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; }
    .page-eyebrow::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    .page-banner h1 { font-size: 22px; font-weight: 700; color: var(--text); }
    .page-banner p { font-size: 13px; color: var(--muted); margin-top: 4px; }
    .badge { display: inline-flex; align-items: center; border: 1px solid var(--b2); border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 700; color: var(--muted); }
    .badge.admin { color: var(--amber); border-color: rgba(245,166,35,.4); background: rgba(245,166,35,.08); }
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
    .panel {
      border: 1px solid var(--b2);
      border-radius: 8px;
      background: var(--bg-1);
      padding: 18px;
    }
    .panel-title { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: 14px; }
    .panel-title::before { content: "// "; color: var(--cyan); font-family: var(--mono); }
    label {
      display: grid;
      gap: 5px;
      font-size: 12px;
      font-weight: 600;
      color: var(--muted);
      letter-spacing: .04em;
      text-transform: uppercase;
      margin-bottom: 12px;
    }
    input {
      width: 100%;
      border: 1px solid var(--b2);
      border-radius: 7px;
      background: var(--bg-3);
      color: var(--text);
      padding: 10px 12px;
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
    .btn-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    button {
      border: 1px solid var(--b2);
      border-radius: 7px;
      padding: 9px 14px;
      color: var(--text);
      background: var(--bg-2);
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      font: inherit;
      transition: border-color .18s, background .18s;
    }
    button:hover { border-color: var(--cyan); background: var(--bg-3); }
    button.primary { background: var(--cyan); color: #000; border-color: var(--cyan); font-weight: 700; }
    button.primary:hover { background: #00bde8; }
    button.secondary { border-color: var(--border); background: transparent; color: var(--muted); }
    button:disabled { opacity: .5; cursor: wait; }
    .hint { font-size: 12px; color: var(--muted); margin-top: 6px; }
    .status-box {
      margin-top: 12px;
      min-height: 40px;
      padding: 10px 12px;
      border-radius: 7px;
      border: 1px solid var(--border);
      color: var(--muted);
      background: var(--bg-2);
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 13px;
      line-height: 1.5;
    }
    .status-box.ok  { border-color: rgba(34,211,160,.3); color: var(--green); background: rgba(34,211,160,.06); }
    .status-box.bad { border-color: rgba(255,77,109,.3);  color: var(--red);   background: rgba(255,77,109,.06); }
    .hidden { display: none; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main class="shell">
    <section class="page-banner">
      <div class="banner-left">
        <div class="page-eyebrow">Account</div>
        <h1>Account Settings</h1>
        <p>Profile, role, trust state, owned models, API usage, and recent security outcomes.</p>
      </div>
      <span id="roleBadge" class="badge">user</span>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="panel-title">Profile</div>
        <div id="profileSummary" class="status-box">Loading profile...</div>
      </article>
      <article class="panel">
        <div class="panel-title">Usage & Outcomes</div>
        <div id="usageSummary" class="status-box">Loading usage...</div>
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="panel-title">Change My Password</div>
        <label>Current Password <input id="currentPassword" type="password" autocomplete="current-password" /></label>
        <label>New Password <input id="newPassword" type="password" autocomplete="new-password" /></label>
        <div class="btn-row">
          <button id="changeBtn" class="primary">Update Password</button>
          <button id="logoutBtn" class="secondary">Log Out</button>
        </div>
        <div class="hint">Use at least 6 characters.</div>
        <div id="selfStatus" class="status-box">Ready.</div>
      </article>

      <article id="adminPanel" class="panel hidden">
        <div class="panel-title">Admin Password Reset</div>
        <label>Target Username <input id="targetUsername" placeholder="username" /></label>
        <label>New Password <input id="targetPassword" type="password" placeholder="new password" /></label>
        <div class="btn-row">
          <button id="resetBtn" class="primary">Reset User Password</button>
        </div>
        <div class="hint">Use this only for account recovery or access support.</div>
        <div id="adminStatus" class="status-box">Admin tools ready.</div>
      </article>
    </section>
  </main>

  <script>
    const api = "/api/v1";
    const $ = (id) => document.getElementById(id);
    const token = () => sessionStorage.getItem("zta_token") || "";
    const authHeaders = () => ({ Authorization: `Bearer ${token()}` });

    function setStatus(id, message, kind = "") {
      const node = $(id);
      node.textContent = message;
      node.className = `status-box${kind ? ` ${kind}` : ""}`;
    }

    function friendlyError(data, status) {
      const detail = data && typeof data === "object" ? data.detail : data;
      if (typeof detail === "string") return detail;
      if (detail && typeof detail === "object") {
        if (detail.message) return detail.message;
        if (detail.title) return `${detail.title}${detail.explanation ? `: ${detail.explanation}` : ""}`;
      }
      if (status === 401) return "Please log in again.";
      if (status === 403) return "You don't have permission for this action.";
      if (status === 404) return "User account was not found.";
      if (status === 422) return "Please check the fields and try again.";
      if (status >= 500) return "Gateway is temporarily unavailable. Please try again.";
      return "Request failed. Please try again.";
    }

    async function request(path, options = {}) {
      const res = await fetch(path, options);
      const text = await res.text();
      let data;
      try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
      if (!res.ok) throw new Error(friendlyError(data, res.status));
      return data;
    }

    async function loadProfile() {
      if (!token()) {
        location.href = "/login?next=/dashboard/account";
        return;
      }
      const profile = await request(`${api}/auth/me/profile`, { headers: authHeaders() });
      const isAdmin = Boolean((profile.user?.scopes || []).includes("admin"));
      $("roleBadge").textContent = isAdmin ? "admin" : "user";
      $("roleBadge").classList.toggle("admin", isAdmin);
      $("adminPanel").classList.toggle("hidden", !isAdmin);
      $("profileSummary").textContent = [
        `Username: ${profile.user?.username || "unknown"}`,
        `Email: ${profile.user?.email || "not set"}`,
        `Role: ${isAdmin ? "admin" : "user"}`,
        `Trust score: ${profile.user?.trust_score ?? "tracked in gateway events"}`
      ].join("\n");
      await loadAccountEvidence();
    }

    async function loadAccountEvidence() {
      try {
        const [models, logs] = await Promise.all([
          request(`${api}/models/my`, { headers: authHeaders() }).catch(() => []),
          request(`${api}/monitoring/logs?limit=8`, { headers: authHeaders() }).catch(() => ({ logs: [] })),
        ]);
        const rows = logs.logs || [];
        const blocked = rows.filter((row) => String(row.decision || "").toLowerCase() === "block").length;
        const challenged = rows.filter((row) => String(row.decision || "").toLowerCase() === "challenge").length;
        $("usageSummary").textContent = [
          `Owned models: ${models.length}`,
          `Recent requests: ${rows.length}`,
          `Recent blocked: ${blocked}`,
          `Recent challenged: ${challenged}`,
          `Latest outcome: ${rows[0]?.decision || "none yet"}`
        ].join("\n");
      } catch {
        $("usageSummary").textContent = "Usage evidence is not available yet.";
      }
    }

    async function changeMyPassword() {
      $("changeBtn").disabled = true;
      setStatus("selfStatus", "Updating password...");
      try {
        await request(`${api}/auth/me/change-password`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            current_password: $("currentPassword").value,
            new_password: $("newPassword").value,
          }),
        });
        $("currentPassword").value = "";
        $("newPassword").value = "";
        setStatus("selfStatus", "Password updated successfully.", "ok");
      } catch (err) {
        setStatus("selfStatus", err?.message || "Password update failed.", "bad");
      } finally {
        $("changeBtn").disabled = false;
      }
    }

    async function adminResetPassword() {
      $("resetBtn").disabled = true;
      setStatus("adminStatus", "Resetting password...");
      try {
        await request(`${api}/auth/admin/reset-password`, {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({
            username: $("targetUsername").value.trim(),
            new_password: $("targetPassword").value,
          }),
        });
        $("targetPassword").value = "";
        setStatus("adminStatus", "User password reset completed.", "ok");
      } catch (err) {
        setStatus("adminStatus", err?.message || "Password reset failed.", "bad");
      } finally {
        $("resetBtn").disabled = false;
      }
    }

    $("changeBtn").addEventListener("click", changeMyPassword);
    $("resetBtn").addEventListener("click", adminResetPassword);
    $("logoutBtn").addEventListener("click", () => {
      sessionStorage.removeItem("zta_token");
      location.href = "/login";
    });

    loadProfile().catch((err) => {
      setStatus("selfStatus", err?.message || "Could not load account profile.", "bad");
    });
  </script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
