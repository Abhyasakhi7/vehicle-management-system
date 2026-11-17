const API_BASE = "/api/v1";
let vehicleCache = {};

class ApiError extends Error {
  constructor(message, data, status) {
    super(message);
    this.data = data;
    this.status = status;
  }
}

function getToken() {
  return localStorage.getItem("token");
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("user"));
  } catch (error) {
    return null;
  }
}

function setAuth(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "/login/";
    return false;
  }
  return true;
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (
    response.status === 401 &&
    !path.startsWith("/auth/login") &&
    !path.startsWith("/auth/register") &&
    !path.startsWith("/auth/logout")
  ) {
    clearAuth();
    window.location.href = "/login/";
    throw new ApiError("Unauthorized", null, 401);
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(errorTextFromData(data, response.status), data, response.status);
  }
  return data;
}

function errorTextFromData(data, status) {
  if (data && typeof data === "object") {
    if (data.detail) {
      return data.detail;
    }
    return Object.entries(data)
      .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : value}`)
      .join("\n");
  }
  return `Request failed (${status})`;
}

function errorText(error) {
  if (error && error.data && typeof error.data === "object") {
    return errorTextFromData(error.data, error.status || 0);
  }
  return error && error.message ? error.message : "Terjadi kesalahan";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatMoney(value) {
  return `Rp ${Number(value || 0).toLocaleString("id-ID", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatDate(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function debounce(callback, wait = 300) {
  let timer;
  return function debounced(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => callback.apply(this, args), wait);
  };
}

function formData(form) {
  const data = {};
  new FormData(form).forEach((value, key) => {
    data[key] = value;
  });
  return data;
}

function fillForm(form, item) {
  Array.from(form.elements).forEach((field) => {
    if (!field.name) {
      return;
    }
    const value = item[field.name];
    if (field.type === "checkbox") {
      field.checked = Boolean(value);
    } else if (field.tagName === "SELECT") {
      field.value = value == null ? "" : String(value);
    } else {
      field.value = value == null ? "" : value;
    }
  });
}

function showFormErrors(form, data) {
  const container = form.querySelector(".form-errors");
  if (!container) {
    return;
  }
  let html = "";
  if (data && typeof data === "object") {
    if (data.detail) {
      html += `<div>${escapeHtml(data.detail)}</div>`;
    }
    Object.entries(data).forEach(([key, value]) => {
      if (key === "detail") {
        return;
      }
      const messages = Array.isArray(value) ? value.join(", ") : value;
      html += `<div><strong>${escapeHtml(key)}:</strong> ${escapeHtml(messages)}</div>`;
    });
  } else {
    html = escapeHtml(errorText(data));
  }
  container.innerHTML = html;
  container.classList.remove("d-none");
}

function clearFormErrors(form) {
  const container = form.querySelector(".form-errors");
  if (container) {
    container.innerHTML = "";
    container.classList.add("d-none");
  }
}

function showModal(id) {
  const element = document.getElementById(id);
  if (element && window.bootstrap) {
    window.bootstrap.Modal.getOrCreateInstance(element).show();
  }
}

function hideModal(id) {
  const element = document.getElementById(id);
  if (element && window.bootstrap) {
    window.bootstrap.Modal.getOrCreateInstance(element).hide();
  }
}

async function loadVehicleCache() {
  try {
    const data = await api("/vehicles/");
    vehicleCache = Object.fromEntries(data.results.map((vehicle) => [vehicle.id, vehicle]));
  } catch (error) {
    vehicleCache = {};
  }
}

function vehicleLabel(id) {
  const vehicle = vehicleCache[id];
  return vehicle ? `${vehicle.name} (${vehicle.plate_number})` : `#${id}`;
}

async function loadVehicleOptions(select, selectedId = null) {
  if (!select) {
    return;
  }
  try {
    const data = await api("/vehicles/");
    select.innerHTML = data.results
      .map(
        (vehicle) =>
          `<option value="${vehicle.id}">${escapeHtml(vehicle.name)} (${escapeHtml(
            vehicle.plate_number
          )})</option>`
      )
      .join("");
    if (selectedId != null) {
      select.value = String(selectedId);
    }
  } catch (error) {
    showToast(errorText(error), "danger");
  }
}

function showToast(message, type = "success") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-message">${escapeHtml(message)}</div>
    <button class="toast-close" type="button" aria-label="Tutup">×</button>
  `;
  toast.querySelector(".toast-close").addEventListener("click", () => toast.remove());
  container.appendChild(toast);

  setTimeout(() => toast.classList.add("show"), 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

async function logout() {
  try {
    await api("/auth/logout/", { method: "POST" });
  } catch (error) {
    // Token may already be invalid; continue clearing local auth.
  }
  clearAuth();
  window.location.href = "/login/";
}

function initNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll("[data-nav]").forEach((link) => {
    if (link.dataset.nav === page) {
      link.classList.add("active");
    }
  });

  const userName = document.getElementById("user-name");
  if (userName) {
    const user = getUser();
    userName.textContent = user ? user.username || user.email || "User" : "-";
  }

  const logoutButton = document.getElementById("logout-btn");
  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }

  const toggle = document.getElementById("sidebar-toggle");
  const overlay = document.getElementById("sidebar-overlay");
  if (toggle) {
    toggle.addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
  }
  if (overlay) {
    overlay.addEventListener("click", () => document.body.classList.remove("sidebar-open"));
  }
}

document.addEventListener("DOMContentLoaded", initNav);
