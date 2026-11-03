/* Shared helpers: API calls, toasts, escaping, pager. */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

class ApiError extends Error {
  constructor(message, status, fields) {
    super(message);
    this.status = status;
    this.fields = fields || {};
  }
}

async function api(path, { method = "GET", body, form } = {}) {
  const headers = { "X-Requested-With": "fetch" };
  let payload;
  if (form) {
    payload = form;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, { method, headers, body: payload, credentials: "same-origin" });
  } catch (e) {
    throw new ApiError("Cannot reach the server. Check that it is running.", 0);
  }
  let data = null;
  try { data = await res.json(); } catch (e) { /* non-JSON response */ }
  if (!res.ok) {
    throw new ApiError((data && data.error) || `Request failed (${res.status})`, res.status, data && data.fields);
  }
  return data;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function initials(name) {
  return String(name).split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]).join("").toUpperCase() || "?";
}

function hue(name) {
  let h = 0;
  for (const ch of String(name)) h += ch.codePointAt(0);
  return h % 360;
}

function avatarHtml(s, cls = "") {
  if (s.has_photo) {
    return `<img class="avatar ${cls}" src="/photo/${esc(s.id)}?v=${Number(s.updated_at) || 0}" alt="">`;
  }
  return `<span class="avatar ${cls}" style="--h:${hue(s.name)}">${esc(initials(s.name))}</span>`;
}

function debounce(fn, ms = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function toast(message, type = "success") {
  const box = $("#toasts");
  if (!box) return;
  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${type} border-0`;
  el.setAttribute("role", "status");
  el.innerHTML = `<div class="d-flex"><div class="toast-body"></div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>`;
  $(".toast-body", el).textContent = message;
  box.appendChild(el);
  const t = new bootstrap.Toast(el, { delay: 3500 });
  el.addEventListener("hidden.bs.toast", () => el.remove());
  t.show();
}

function renderPager(el, page, total, perPage, onPage) {
  const pages = Math.max(1, Math.ceil(total / perPage));
  if (pages <= 1) { el.innerHTML = ""; return; }
  const items = [];
  const add = (label, p, active = false, disabled = false) => items.push(
    `<li class="page-item ${active ? "active" : ""} ${disabled ? "disabled" : ""}">
       <button type="button" class="page-link" data-p="${p}">${label}</button></li>`);
  add("&lsaquo;", page - 1, false, page === 1);
  for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++) add(p, p, p === page);
  add("&rsaquo;", page + 1, false, page === pages);
  el.innerHTML = `<ul class="pagination pagination-sm justify-content-center mb-0">${items.join("")}</ul>`;
  $$("button[data-p]", el).forEach((b) => b.addEventListener("click", () => onPage(Number(b.dataset.p))));
}

document.addEventListener("DOMContentLoaded", () => {
  const logout = $("#logout-btn");
  if (logout) {
    logout.addEventListener("click", async () => {
      try { await api("/api/auth/logout", { method: "POST" }); } catch (e) { /* ignore */ }
      window.location.href = "/";
    });
  }
  const copy = $("#copy-link");
  if (copy && !copy.dataset.custom) {
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(window.location.origin + (copy.dataset.path || window.location.pathname));
        toast("Link copied");
      } catch (e) { toast("Copy failed. Copy the address from your browser instead.", "danger"); }
    });
  }
});
