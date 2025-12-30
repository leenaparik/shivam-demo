const API_BASE = `http://${window.location.hostname}:5000/api`;

const els = {
  apiBase: document.getElementById("api-base"),
  message: document.getElementById("message"),

  tabLogin: document.getElementById("tab-login"),
  tabRegister: document.getElementById("tab-register"),
  btnLogout: document.getElementById("btn-logout"),

  panelLogin: document.getElementById("panel-login"),
  panelRegister: document.getElementById("panel-register"),
  panelProfile: document.getElementById("panel-profile"),

  formLogin: document.getElementById("form-login"),
  formRegister: document.getElementById("form-register"),
  formAdd: document.getElementById("form-add"),

  welcome: document.getElementById("welcome"),
  pFirst: document.getElementById("p-first"),
  pLast: document.getElementById("p-last"),
  pAddress: document.getElementById("p-address"),
  pSsn: document.getElementById("p-ssn"),

  addResult: document.getElementById("add-result"),
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

function setTab(name) {
  showMessage("", "");
  const isLogin = name === "login";
  els.tabLogin.classList.toggle("active", isLogin);
  els.tabRegister.classList.toggle("active", !isLogin);
  els.panelLogin.classList.toggle("hidden", !isLogin);
  els.panelRegister.classList.toggle("hidden", isLogin);
}

function setLoggedIn(isLoggedIn) {
  els.btnLogout.classList.toggle("hidden", !isLoggedIn);
  els.panelProfile.classList.toggle("hidden", !isLoggedIn);
  els.panelLogin.classList.toggle("hidden", isLoggedIn);
  els.panelRegister.classList.toggle("hidden", true);
  if (!isLoggedIn && els.formAdd) {
    els.formAdd.reset();
    els.addResult.classList.add("hidden");
    els.addResult.classList.remove("error");
    els.addResult.textContent = "";
  }
  if (!isLoggedIn) setTab("login");
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

async function refreshMe() {
  try {
    const data = await api("/me");
    const u = data.user;
    els.welcome.textContent = `Welcome to my website, ${u.username}!`;
    els.pFirst.textContent = u.first_name;
    els.pLast.textContent = u.last_name;
    els.pAddress.textContent = u.address;
    els.pSsn.textContent = `***-**-${u.ssn_last4}`;
    setLoggedIn(true);
  } catch {
    setLoggedIn(false);
  }
}

els.tabLogin.addEventListener("click", () => setTab("login"));
els.tabRegister.addEventListener("click", () => {
  showMessage("", "");
  els.tabLogin.classList.remove("active");
  els.tabRegister.classList.add("active");
  els.panelLogin.classList.add("hidden");
  els.panelRegister.classList.remove("hidden");
});

els.formRegister.addEventListener("submit", async (e) => {
  e.preventDefault();
  showMessage("", "");
  const form = new FormData(els.formRegister);
  const payload = Object.fromEntries(form.entries());
  try {
    await api("/register", { method: "POST", body: JSON.stringify(payload) });
    // Redirect to the employees page after successful register/login.
    window.location.href = "/employees.html";
  } catch (err) {
    showMessage(err.message, "error");
  }
});

els.formLogin.addEventListener("submit", async (e) => {
  e.preventDefault();
  showMessage("", "");
  const form = new FormData(els.formLogin);
  const payload = Object.fromEntries(form.entries());
  try {
    await api("/login", { method: "POST", body: JSON.stringify(payload) });
    // Redirect to the employees page after successful login.
    window.location.href = "/employees.html";
  } catch (err) {
    showMessage(err.message, "error");
  }
});

els.btnLogout.addEventListener("click", async () => {
  showMessage("", "");
  try {
    await api("/logout", { method: "POST", body: "{}" });
    showMessage("Logged out.", "ok");
    await refreshMe();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

if (els.formAdd) {
  els.formAdd.addEventListener("submit", async (e) => {
    e.preventDefault();
    els.addResult.classList.add("hidden");
    els.addResult.classList.remove("error");
    els.addResult.textContent = "";

    const form = new FormData(els.formAdd);
    const a = (form.get("a") || "").toString().trim();
    const b = (form.get("b") || "").toString().trim();

    try {
      const data = await api(`/add?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
      els.addResult.textContent = `Result: ${data.sum}`;
      els.addResult.classList.remove("hidden");
    } catch (err) {
      els.addResult.textContent = err.message;
      els.addResult.classList.add("error");
      els.addResult.classList.remove("hidden");
    }
  });
}

refreshMe();


