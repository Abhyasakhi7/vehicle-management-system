function setAuthSubmitLoading(form, loading) {
  const button = form.querySelector('button[type="submit"]');
  if (!button) {
    return;
  }
  if (loading) {
    button.dataset.label = button.textContent;
    button.disabled = true;
    button.textContent = "Memproses...";
  } else {
    button.disabled = false;
    button.textContent = button.dataset.label || button.textContent;
  }
}

function initLoginForm() {
  const form = document.getElementById("login-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFormErrors(form);
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    setAuthSubmitLoading(form, true);

    const data = formData(form);
    try {
      const result = await api("/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          identifier: (data.identifier || "").trim(),
          password: data.password || "",
        }),
      });
      setAuth(result.token, result.user);
      window.location.href = "/dashboard/";
    } catch (error) {
      showFormErrors(form, error.data || error.message);
      setAuthSubmitLoading(form, false);
    }
  });
}

function initRegisterForm() {
  const form = document.getElementById("register-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFormErrors(form);
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    setAuthSubmitLoading(form, true);

    const data = formData(form);
    try {
      const result = await api("/auth/register/", {
        method: "POST",
        body: JSON.stringify({
          username: (data.username || "").trim(),
          email: (data.email || "").trim(),
          password: data.password || "",
          password_confirm: data.password_confirm || "",
        }),
      });
      setAuth(result.token, result.user);
      window.location.href = "/dashboard/";
    } catch (error) {
      showFormErrors(form, error.data || error.message);
      setAuthSubmitLoading(form, false);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (getToken()) {
    window.location.href = "/dashboard/";
    return;
  }
  initLoginForm();
  initRegisterForm();
});
