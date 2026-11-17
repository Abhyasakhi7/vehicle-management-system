document.addEventListener("DOMContentLoaded", async () => {
  if (!requireAuth()) {
    return;
  }

  const logoutButton = document.getElementById("settings-logout-btn");
  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }

  function detailItem(label, value) {
    return `
      <div class="detail-item">
        <div class="detail-label">${escapeHtml(label)}</div>
        <div class="detail-value">${escapeHtml(value || "-")}</div>
      </div>
    `;
  }

  try {
    const user = await api("/auth/me/");
    localStorage.setItem("user", JSON.stringify(user));

    const displayName =
      [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;
    const userName = document.getElementById("user-name");
    if (userName) {
      userName.textContent = displayName;
    }

    document.getElementById("profile-details").innerHTML = [
      detailItem("Username", user.username),
      detailItem("Email", user.email),
      detailItem("Nama Depan", user.first_name),
      detailItem("Nama Belakang", user.last_name),
      detailItem("Terdaftar", formatDate(user.date_joined)),
    ].join("");
  } catch (error) {
    showToast(errorText(error), "danger");
  }
});
