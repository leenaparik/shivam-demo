const API_BASE = `http://${window.location.hostname}:5000/api`;

const els = {
  apiBase: document.getElementById("api-base"),
  message: document.getElementById("message"),
  tbody: document.getElementById("employees-body"),
  btnRefresh: document.getElementById("btn-refresh"),
  btnLogout: document.getElementById("btn-logout"),
  btnHome: document.getElementById("btn-home"),
};

els.apiBase.textContent = API_BASE;

function showMessage(text, kind) {
  if (!text) {
    els.message.classList.add("hidden");
    els.message.textContent = "";
    els.message.classList.remove("error", "ok");
    return;
  }
  els.message.classList.remove("hidden");
  els.message.textContent = text;
  els.message.classList.toggle("error", kind === "error");
  els.message.classList.toggle("ok", kind === "ok");
}

async function api(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
    credentials: "include",
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // ignore
  }

  if (!res.ok) {
    const msg = (data && data.error) || `${res.status} ${res.statusText}`;
    throw new Error(msg);
  }
  return data;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderEmployees(employees) {
  els.tbody.innerHTML = employees
    .map(
      (e) => `
      <tr>
        <td>${escapeHtml(e.id)}</td>
        <td>${escapeHtml(e.first_name)}</td>
        <td>${escapeHtml(e.last_name)}</td>
        <td>${escapeHtml(e.email)}</td>
        <td>${escapeHtml(e.department)}</td>
        <td>${escapeHtml(e.phone)}</td>
      </tr>
    `,
    )
    .join("");
}

async function requireLogin() {
  try {
    await api("/me");
    return true;
  } catch {
    // Not logged in → go back to main login page.
    window.location.href = "/";
    return false;
  }
}

async function loadEmployees() {
  showMessage("", "");
  els.tbody.innerHTML = "";
  try {
    const payload = await api("/employees");
    const employees = (payload.data && payload.data.employees) || [];
    renderEmployees(employees);
    showMessage(`Loaded ${employees.length} employees.`, "ok");
  } catch (err) {
    showMessage(err.message, "error");
  }
}

els.btnRefresh.addEventListener("click", loadEmployees);
els.btnHome.addEventListener("click", () => {
  window.location.href = "/";
});

els.btnLogout.addEventListener("click", async () => {
  try {
    await api("/logout", { method: "POST", body: "{}" });
  } finally {
    window.location.href = "/";
  }
});

(async function init() {
  const ok = await requireLogin();
  if (!ok) return;
  await loadEmployees();
})();


