const token = sessionStorage.getItem("zta_token");
    if (!token) location.href = "/login?next=/dashboard/getting-started";