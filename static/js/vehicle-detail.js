const DETAIL_SERVICE_TYPE_LABELS = {
  OIL_CHANGE: "Ganti Oli",
  TIRE: "Ganti Ban",
  BRAKES: "Servis Rem",
  BATTERY: "Baterai",
  GENERAL_SERVICE: "Servis Umum",
  REPAIR: "Perbaikan",
  OTHER: "Lainnya",
};

const DETAIL_EXPENSE_CATEGORY_LABELS = {
  TAX: "Pajak",
  INSURANCE: "Asuransi",
  PARKING: "Parkir",
  TOLL: "Tol",
  WASH: "Cuci Kendaraan",
  OTHER: "Lainnya",
};

const DETAIL_VEHICLE_TYPE_LABELS = {
  CAR: "Mobil",
  MOTORCYCLE: "Motor",
  OTHER: "Lainnya",
};

const DETAIL_FUEL_TYPE_LABELS = {
  PETROL: "Bensin",
  DIESEL: "Diesel",
  ELECTRIC: "Listrik",
  HYBRID: "Hybrid",
};

const DETAIL_TRANSMISSION_LABELS = {
  MANUAL: "Manual",
  AUTOMATIC: "Otomatis",
  CVT: "CVT",
  OTHER: "Lainnya",
};

document.addEventListener("DOMContentLoaded", () => {
  if (!requireAuth()) {
    return;
  }

  const match = window.location.pathname.match(/\/vehicles\/(\d+)\//);
  if (!match) {
    window.location.href = "/vehicles/";
    return;
  }

  const vehicleId = Number(match[1]);
  const form = document.getElementById("vehicle-form");
  const modalId = "vehicle-modal";
  let vehicle = null;

  function detailItem(label, value) {
    return `
      <div class="detail-item">
        <div class="detail-label">${escapeHtml(label)}</div>
        <div class="detail-value">${escapeHtml(value == null || value === "" ? "-" : value)}</div>
      </div>
    `;
  }

  function renderVehicle() {
    document.title = `${vehicle.name} — Vehicle Management System`;
    document.getElementById("vehicle-title").textContent = vehicle.name;
    document.getElementById("vehicle-subtitle").textContent =
      `${vehicle.brand} ${vehicle.model} • ${vehicle.plate_number}`;

    document.getElementById("vehicle-details").innerHTML = [
      detailItem("Merek", vehicle.brand),
      detailItem("Model", vehicle.model),
      detailItem("Tahun", vehicle.year),
      detailItem("Plat Nomor", vehicle.plate_number),
      detailItem(
        "Tipe",
        DETAIL_VEHICLE_TYPE_LABELS[vehicle.vehicle_type] || vehicle.vehicle_type
      ),
      detailItem(
        "Bahan Bakar",
        DETAIL_FUEL_TYPE_LABELS[vehicle.fuel_type] || vehicle.fuel_type
      ),
      detailItem(
        "Transmisi",
        DETAIL_TRANSMISSION_LABELS[vehicle.transmission] || vehicle.transmission
      ),
      detailItem("Odometer", `${Number(vehicle.mileage).toLocaleString("id-ID")} km`),
      detailItem("Warna", vehicle.color),
      detailItem("Terdaftar", formatDate(vehicle.created_at)),
    ].join("");
  }

  async function loadVehicle() {
    try {
      vehicle = await api(`/vehicles/${vehicleId}/`);
      renderVehicle();
    } catch (error) {
      showToast(errorText(error), "danger");
      setTimeout(() => {
        window.location.href = "/vehicles/";
      }, 1200);
    }
  }

  function renderMaintenance(items) {
    const body = document.getElementById("detail-maintenance-body");
    if (!items.length) {
      body.innerHTML =
        '<tr><td colspan="4"><div class="empty-state">Belum ada riwayat servis.</div></td></tr>';
      return;
    }
    body.innerHTML = items
      .slice(0, 5)
      .map(
        (item) => `
          <tr>
            <td>${escapeHtml(formatDate(item.service_date))}</td>
            <td><span class="badge badge-type">${escapeHtml(
              DETAIL_SERVICE_TYPE_LABELS[item.service_type] || item.service_type
            )}</span></td>
            <td>${escapeHtml(Number(item.mileage).toLocaleString("id-ID"))} km</td>
            <td>${escapeHtml(formatMoney(item.cost))}</td>
          </tr>
        `
      )
      .join("");
  }

  function renderFuel(items) {
    const body = document.getElementById("detail-fuel-body");
    if (!items.length) {
      body.innerHTML =
        '<tr><td colspan="3"><div class="empty-state">Belum ada riwayat BBM.</div></td></tr>';
      return;
    }
    body.innerHTML = items
      .slice(0, 5)
      .map(
        (item) => `
          <tr>
            <td>${escapeHtml(formatDate(item.date))}</td>
            <td>${escapeHtml(Number(item.liters).toLocaleString("id-ID"))} L</td>
            <td>${escapeHtml(formatMoney(item.total_cost))}</td>
          </tr>
        `
      )
      .join("");
  }

  function renderExpenses(items) {
    const body = document.getElementById("detail-expenses-body");
    if (!items.length) {
      body.innerHTML =
        '<tr><td colspan="3"><div class="empty-state">Belum ada pengeluaran lain.</div></td></tr>';
      return;
    }
    body.innerHTML = items
      .slice(0, 5)
      .map(
        (item) => `
          <tr>
            <td>${escapeHtml(formatDate(item.date))}</td>
            <td><span class="badge badge-type">${escapeHtml(
              DETAIL_EXPENSE_CATEGORY_LABELS[item.category] || item.category
            )}</span></td>
            <td>${escapeHtml(formatMoney(item.amount))}</td>
          </tr>
        `
      )
      .join("");
  }

  async function loadRelated() {
    document.getElementById("maintenance-link").href =
      `/maintenance/?vehicle=${vehicleId}`;
    document.getElementById("fuel-link").href = `/fuel/?vehicle=${vehicleId}`;
    document.getElementById("expenses-link").href =
      `/expenses/?vehicle=${vehicleId}`;

    try {
      const [maintenance, fuel, expenses] = await Promise.all([
        api(`/maintenance/?vehicle=${vehicleId}`),
        api(`/fuel/?vehicle=${vehicleId}`),
        api(`/expenses/?vehicle=${vehicleId}`),
      ]);
      renderMaintenance(maintenance.results || []);
      renderFuel(fuel.results || []);
      renderExpenses(expenses.results || []);
    } catch (error) {
      showToast(errorText(error), "danger");
    }
  }

  document.getElementById("edit-vehicle-btn").addEventListener("click", () => {
    if (!vehicle) {
      return;
    }
    clearFormErrors(form);
    fillForm(form, vehicle);
    showModal(modalId);
  });

  document.getElementById("delete-vehicle-btn").addEventListener("click", async () => {
    if (!vehicle) {
      return;
    }
    if (!window.confirm(`Hapus kendaraan "${vehicle.name}"?`)) {
      return;
    }
    try {
      await api(`/vehicles/${vehicleId}/`, { method: "DELETE" });
      showToast("Kendaraan dihapus.");
      window.location.href = "/vehicles/";
    } catch (error) {
      showToast(errorText(error), "danger");
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFormErrors(form);
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const data = formData(form);
    try {
      vehicle = await api(`/vehicles/${vehicleId}/`, {
        method: "PATCH",
        body: JSON.stringify({
          name: data.name,
          brand: data.brand,
          model: data.model,
          year: Number(data.year),
          vehicle_type: data.vehicle_type,
          plate_number: data.plate_number,
          fuel_type: data.fuel_type,
          transmission: data.transmission,
          mileage: Number(data.mileage),
          color: data.color,
        }),
      });
      hideModal(modalId);
      showToast("Kendaraan diperbarui.");
      renderVehicle();
      await loadVehicleCache();
    } catch (error) {
      showFormErrors(form, error.data || error.message);
    }
  });

  loadVehicle();
  loadRelated();
});
