(function () {
  function showFieldErrors(form, fields) {
    $$(".is-invalid", form).forEach((el) => el.classList.remove("is-invalid"));
    Object.entries(fields || {}).forEach(([path, msg]) => {
      const el = form.querySelector(`[data-path="${path}"]`);
      if (!el) return;
      el.classList.add("is-invalid");
      const fb = el.parentElement.querySelector(".invalid-feedback");
      if (fb) fb.textContent = msg;
    });
  }

  function showError(form, message) {
    const box = $("#form-error", form);
    box.textContent = message;
    box.classList.remove("d-none");
  }

  async function submit(form, url, body, fallbackRedirect) {
    const button = $("button[type=submit]", form);
    $("#form-error", form).classList.add("d-none");
    button.disabled = true;
    try {
      const data = await api(url, { method: "POST", body });
      const next = form.dataset.next;
      window.location.href = next || data.redirect || fallbackRedirect;
    } catch (e) {
      showFieldErrors(form, e.fields);
      showError(form, e.message);
      button.disabled = false;
    }
  }

  const login = $("#login-form");
  if (login) {
    login.addEventListener("submit", (e) => {
      e.preventDefault();
      submit(login, "/api/auth/login", {
        email: $("#email").value, password: $("#password").value,
      }, "/dashboard");
    });
  }

  const reg = $("#register-form");
  if (reg) {
    reg.addEventListener("submit", (e) => {
      e.preventDefault();
      const confirm = $("#confirm");
      confirm.classList.remove("is-invalid");
      if ($("#password").value !== confirm.value) {
        confirm.classList.add("is-invalid");
        confirm.parentElement.querySelector(".invalid-feedback").textContent = "Passwords do not match";
        return;
      }
      submit(reg, "/api/auth/register", {
        name: $("#name").value, usn: $("#usn").value, email: $("#email").value,
        department: $("#department").value, year: $("#year").value, password: $("#password").value,
      }, "/dashboard");
    });
  }
})();
