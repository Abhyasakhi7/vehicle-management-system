const SERVICE_TYPE_LABELS = {
  OIL_CHANGE: "Ganti Oli",
  TIRE: "Ganti Ban",
  BRAKES: "Servis Rem",
  BATTERY: "Baterai",
  GENERAL_SERVICE: "Servis Umum",
  REPAIR: "Perbaikan",
  OTHER: "Lainnya",
};

function shortMoney(value) {
  const amount = Number(value || 0);
  if (amount >= 1000000) {
    return `${(amount / 1000000).toLocaleString("id-ID", {
      maximumFractionDigits: 1,
    })} jt`;
  }
  if (amount >= 1000) {
    return `${Math.round(amount / 1000).toLocaleString("id-ID")} rb`;
  }
  return amount.toLocaleString("id-ID");
}

function monthLabel(month) {
  const date = new Date(`${month}-01T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return month;
  }
  return date.toLocaleDateString("id-ID", { month: "short" });
}

function renderStats(data) {
  document.getElementById("stat-cost").textContent = formatMoney(data.total_cost);
  document.getElementById("stat-maintenance").textContent = formatMoney(
    data.cost_breakdown.maintenance
  );
  document.getElementById("stat-fuel").textContent = formatMoney(
    data.cost_breakdown.fuel
  );
  document.getElementById("stat-expenses").textContent = formatMoney(
    data.cost_breakdown.expenses
  );
  document.getElementById("stat-vehicles").textContent =
    `${data.total_vehicles.toLocaleString("id-ID")} kendaraan`;

  const period = data.period || {};
  const periodLabel = period.start_date || period.end_date
    ? `${period.start_date ? formatDate(period.start_date) : "Awal"} – ${
        period.end_date ? formatDate(period.end_date) : "Sekarang"
      }`
    : "Semua waktu";
  document.getElementById("stat-period").textContent = periodLabel;

  const distance = Number(data.total_distance || 0).toLocaleString("id-ID");
  document.getElementById("dashboard-summary").textContent =
    `${data.total_vehicles.toLocaleString("id-ID")} kendaraan • ${distance} km tercatat`;
}

function renderChart(months) {
  const container = document.getElementById("monthly-chart");
  const totals = months.map((month) => Number(month.total || 0));
  const maxTotal = Math.max(...totals, 1);

  container.innerHTML = months
    .map((month) => {
      const total = Number(month.total || 0);
      const height = Math.max((total / maxTotal) * 170, total > 0 ? 6 : 2);
      const breakdown = [
        `Maintenance: ${formatMoney(month.maintenance)}`,
        `BBM: ${formatMoney(month.fuel)}`,
        `Lainnya: ${formatMoney(month.expenses)}`,
      ].join("\n");
      return `
        <div class="chart-column">
          <div class="chart-value" title="${escapeHtml(breakdown)}">${escapeHtml(
        shortMoney(total)
      )}</div>
          <div class="chart-bar" style="height: ${height}px" title="${escapeHtml(
        breakdown
      )}"></div>
          <div class="chart-label">${escapeHtml(monthLabel(month.month))}</div>
        </div>
      `;
    })
    .join("");
}

function renderRecentActivity(items) {
  const container = document.getElementById("recent-activity");
  if (!items.length) {
    container.innerHTML =
      '<div class="empty-state">Belum ada aktivitas tercatat.</div>';
    return;
  }

  const icons = { maintenance: "🛠", fuel: "⛽", expense: "💳" };
  const labels = { maintenance: "Maintenance", fuel: "BBM", expense: "Pengeluaran" };

  container.innerHTML = items
    .map(
      (item) => `
        <div class="activity-item">
          <div class="activity-icon ${escapeHtml(item.type)}">${icons[item.type] || "•"}</div>
          <div class="activity-body">
            <div class="activity-title">${escapeHtml(item.description || labels[item.type] || "")}</div>
            <div class="activity-meta">${escapeHtml(item.vehicle.name)} (${escapeHtml(
        item.vehicle.plate_number
      )}) • ${escapeHtml(formatDate(item.date))}</div>
          </div>
          <div class="activity-amount">${escapeHtml(formatMoney(item.amount))}</div>
        </div>
      `
    )
    .join("");
}

function renderUpcomingMaintenance(items) {
  const body = document.getElementById("upcoming-maintenance-body");
  if (!items.length) {
    body.innerHTML =
      '<tr><td colspan="6"><div class="empty-state">Tidak ada jadwal servis mendatang.</div></td></tr>';
    return;
  }

  body.innerHTML = items
    .map(
      (item) => `
        <tr>
          <td>${escapeHtml(item.vehicle.name)}<div class="text-muted">${escapeHtml(
        item.vehicle.plate_number
      )}</div></td>
          <td><span class="badge badge-type">${escapeHtml(
            SERVICE_TYPE_LABELS[item.service_type] || item.service_type
          )}</span></td>
          <td>${escapeHtml(formatDate(item.service_date))}</td>
          <td>${escapeHtml(formatDate(item.next_service_date))}</td>
          <td>${escapeHtml(Number(item.mileage).toLocaleString("id-ID"))} km</td>
          <td>${escapeHtml(formatMoney(item.cost))}</td>
        </tr>
      `
    )
    .join("");
}

async function loadDashboard() {
  const params = new URLSearchParams();
  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;
  if (startDate) {
    params.set("start_date", startDate);
  }
  if (endDate) {
    params.set("end_date", endDate);
  }

  const query = params.toString();
  try {
    const data = await api(`/dashboard/${query ? `?${query}` : ""}`);
    renderStats(data);
    renderChart(data.monthly_expenses || []);
    renderRecentActivity(data.recent_activity || []);
    renderUpcomingMaintenance(data.upcoming_maintenance || []);
  } catch (error) {
    showToast(errorText(error), "danger");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!requireAuth()) {
    return;
  }

  document.getElementById("dashboard-filter").addEventListener("submit", (event) => {
    event.preventDefault();
    loadDashboard();
  });

  document.getElementById("reset-filter").addEventListener("click", () => {
    document.getElementById("start-date").value = "";
    document.getElementById("end-date").value = "";
    loadDashboard();
  });

  loadDashboard();
});
