/* =========================================================
   Pulse — api.js
   JWT + Refresh robusto (SIN race conditions)
   ========================================================= */

const API_BASE = "/api";

/* =========================
   AUTH
========================= */
const Auth = {
  getAccess() {
    return localStorage.getItem("pulse_access");
  },

  getRefresh() {
    return localStorage.getItem("pulse_refresh");
  },

  setTokens(access, refresh) {
    localStorage.setItem("pulse_access", access);
    if (refresh) localStorage.setItem("pulse_refresh", refresh);
  },

  clear() {
    localStorage.removeItem("pulse_access");
    localStorage.removeItem("pulse_refresh");
  },

  logout() {
    this.clear();
  },

  isLoggedIn() {
    return !!this.getAccess();
  },

  // FIX: faltaba este método — feed.html, profile.html y notifications.html lo llaman
  requireLogin() {
    if (!this.isLoggedIn()) {
      window.location.href = "/login/";
    }
  }
};

/* =========================
   REFRESH CONTROL
========================= */
let refreshPromise = null;

async function tryRefreshToken() {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const refresh = Auth.getRefresh();
      if (!refresh) return false;

      const res = await fetch(`${API_BASE}/users/login/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh })
      });

      if (!res.ok) {
        Auth.clear();
        return false;
      }

      const data = await res.json();

      if (!data.access) {
        Auth.clear();
        return false;
      }

      Auth.setTokens(data.access, null);
      return true;

    } catch (err) {
      Auth.clear();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/* =========================
   API FETCH
========================= */
async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const access = Auth.getAccess();
  if (access) {
    headers["Authorization"] = `Bearer ${access}`;
  }
  console.log("apiFetch:", path, "token:", Auth.getAccess() ? "OK" : "MISSING");
  
  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    const refreshed = await tryRefreshToken();

    if (!refreshed) {
      Auth.clear();
      window.location.href = "/login/";
      return res;
    }

    const newAccess = Auth.getAccess();
    if (newAccess) {
      headers["Authorization"] = `Bearer ${newAccess}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }

  return res;
}

/* =========================
   UI HELPERS
========================= */
function showToast(message) {
  let toast = document.querySelector(".toast");

  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add("is-visible");

  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.classList.remove("is-visible");
  }, 2500);
}

function initials(firstName = "", lastName = "") {
  return ((firstName[0] || "") + (lastName[0] || "")).toUpperCase();
}

function escapeHTML(str = "") {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function timeAgo(dateString) {
  const date = new Date(dateString);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  const steps = [
    [60, "s"],
    [60, "min"],
    [24, "h"],
    [7, "d"],
    [4.345, "sem"],
    [12, "mes"],
    [Infinity, "a"]
  ];

  let value = seconds;
  let unit = "s";

  for (const [div, label] of steps) {
    if (value < div) {
      unit = label;
      break;
    }
    value = Math.floor(value / div);
    unit = label;
  }

  if (unit === "s" && value < 5) return "ahora";
  return `${value}${unit}`;
}

/* =========================
   AVATAR
========================= */
function avatarHTML(user, size = 40) {
  const style = `width:${size}px;height:${size}px;font-size:${Math.round(size * 0.38)}px;`;

  if (user?.avatar) {
    return `<img class="avatar" src="${user.avatar}" style="${style}">`;
  }

  const ini =
    initials(user?.first_name, user?.last_name) ||
    (user?.username || "?")[0].toUpperCase();

  return `<div class="avatar avatar-placeholder" style="${style}">${ini}</div>`;
}

/* =========================
   NAV
========================= */
function logout() {
  Auth.clear();
  window.location.href = "/login/";
}

async function loadCurrentUserIntoNav() {
  const slot = document.querySelector("[data-current-user]");
  if (!slot) return null;

  try {
    const res = await apiFetch("/users/me/");
    if (!res.ok) return null;

    const me = await res.json();

    slot.innerHTML = `
      ${avatarHTML(me, 36)}
      <div>
        <div class="nav-account-name">
          ${escapeHTML(me.first_name)} ${escapeHTML(me.last_name)}
        </div>
        <div class="nav-account-role">
          ${escapeHTML(me.position || "Sin cargo")}
        </div>
      </div>
    `;

    return me;

  } catch (e) {
    return null;
  }
}
