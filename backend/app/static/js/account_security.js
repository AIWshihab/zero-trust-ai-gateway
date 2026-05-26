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