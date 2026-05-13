from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


ACCOUNT_SECURITY_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Account Security - Zero Trust AI Gateway</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --text: #eef5ff;
      --muted: #a7b4cb;
      --ok: #4ade80;
      --bad: #fb7185;
      --warn: #fbbf24;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100svh;
      color: var(--text);
      background: radial-gradient(circle at 18% 8%, rgba(56,189,248,.22), transparent 30%), linear-gradient(135deg, #05080f, #111827 50%, #020617);
      padding: 14px;
    }
    .shell {
      width: min(980px, 100%);
      margin: 0 auto;
      display: grid;
      gap: 12px;
    }
    .panel {
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, .28);
      background: rgba(3, 7, 18, .64);
      box-shadow: 0 20px 42px rgba(2, 6, 23, .45);
      padding: 16px;
    }
    h1 { margin: 0 0 8px; font-size: clamp(20px, 3.4vw, 30px); }
    p { margin: 0; color: var(--muted); }
    .grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
    }
    @media (min-width: 900px) {
      .grid { grid-template-columns: 1fr 1fr; }
    }
    label {
      display: grid;
      gap: 6px;
      margin-bottom: 10px;
      font-size: 12px;
      color: var(--muted);
      font-weight: 700;
    }
    input {
      width: 100%;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, .36);
      background: rgba(15, 23, 42, .82);
      color: var(--text);
      padding: 10px 12px;
      font: inherit;
    }
    button {
      border: 1px solid rgba(56, 189, 248, .6);
      background: rgba(56, 189, 248, .16);
      color: #e0f2fe;
      border-radius: 10px;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary {
      border-color: rgba(148,163,184,.44);
      background: rgba(148,163,184,.1);
      color: #dbeafe;
    }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .status {
      margin-top: 10px;
      min-height: 24px;
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid rgba(148,163,184,.28);
      color: #e2e8f0;
      background: rgba(15,23,42,.6);
      white-space: pre-wrap;
      word-break: break-word;
    }
    .status.ok { border-color: rgba(74,222,128,.5); color: var(--ok); }
    .status.bad { border-color: rgba(251,113,133,.5); color: var(--bad); }
    .hint { color: var(--muted); font-size: 12px; }
    .badge {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border: 1px solid rgba(148,163,184,.4);
      color: #cbd5e1;
    }
    .badge.admin { border-color: rgba(250, 204, 21, .45); color: #fde68a; }
    .hidden { display: none; }
  </style>
</head>
<body>
  <main class="shell">
    <section class="panel">
      <div class="row" style="justify-content:space-between">
        <h1>Account Security</h1>
        <span id="roleBadge" class="badge">user</span>
      </div>
      <p>Change your own password here. Admin users can also reset passwords for other accounts.</p>
    </section>

    <section class="grid">
      <article class="panel">
        <h2 style="margin-top:0">Change My Password</h2>
        <label>Current Password <input id="currentPassword" type="password" autocomplete="current-password" /></label>
        <label>New Password <input id="newPassword" type="password" autocomplete="new-password" /></label>
        <div class="row">
          <button id="changeBtn">Update Password</button>
          <button id="logoutBtn" class="secondary">Log Out</button>
        </div>
        <div class="hint">Use at least 6 characters.</div>
        <div id="selfStatus" class="status">Ready.</div>
      </article>

      <article id="adminPanel" class="panel hidden">
        <h2 style="margin-top:0">Admin Password Reset</h2>
        <label>Target Username <input id="targetUsername" placeholder="username" /></label>
        <label>New Password <input id="targetPassword" type="password" placeholder="new password" /></label>
        <div class="row">
          <button id="resetBtn">Reset User Password</button>
        </div>
        <div class="hint">Use this only for account recovery or access support.</div>
        <div id="adminStatus" class="status">Admin tools ready.</div>
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
      node.className = `status${kind ? ` ${kind}` : ""}`;
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
        location.href = "/login?next=/account-security";
        return;
      }
      const profile = await request(`${api}/auth/me/profile`, { headers: authHeaders() });
      const isAdmin = Boolean((profile.user?.scopes || []).includes("admin"));
      $("roleBadge").textContent = isAdmin ? "admin" : "user";
      $("roleBadge").classList.toggle("admin", isAdmin);
      $("adminPanel").classList.toggle("hidden", !isAdmin);
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
""".replace("</style>", f"{CYBER_UI_CSS}\\n  </style>").replace("</body>", f"{CYBER_UI_JS}\\n</body>")

