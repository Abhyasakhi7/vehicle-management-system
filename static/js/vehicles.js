const VEHICLE_TYPE_LABELS = {
  CAR: "Mobil",
  MOTORCYCLE: "Motor",
  OTHER: "Lainnya",
};

const VEHICLE_FUEL_LABELS = {
  PETROL: "Bensin",
  DIESEL: "Diesel",
  ELECTRIC: "Listrik",
  HYBRID: "Hybrid",
};

const VEHICLE_TRANSMISSION_LABELS = {
  MANUAL: "Manual",
  AUTOMATIC: "Otomatis",
  CVT: "CVT",
  OTHER: "Lainnya",
};

document.addEventListener("DOMContentLoaded", () => {
  if (!requireAuth()) {
    return;
  }

  const body = document.getElementById("vehicles-body");
  const form = document.getElementById("vehicle-form");
  const modalId = "vehicle-modal";
  const modalTitle = document.getElementById("vehicle-modal-title");
  const searchInput = document.getElementById("vehicle-search");
  const addButton = document.getElementById("add-vehicle-btn");
  const countLabel = document.getElementById("vehicle-count");

  let items = [];
  let editingId = null;

  function render() {
    if (!items.length) {
      body.innerHTML =
        '<tr><td colspan="7"><div class="empty-state">Belum ada kendaraan. Tambahkan kendaraan pertama Anda.</div></td></tr>';
      return;
    }

    body.innerHTML = items
      .map(
        (item) => `
          <tr>
            <td><a class="text-accent" href="/vehicles/${item.id}/">${escapeHtml(
          item.name
        )}</a><div class="text-muted">${escapeHtml(
          VEHICLE_FUEL_LABELS[item.fuel_type] || item.fuel_type
        )} • ${escapeHtml(
          VEHICLE_TRANSMISSION_LABELS[item.transmission] || item.transmission
        )}</div></td>
            <td>${escapeHtml(item.brand)} ${escapeHtml(item.model)}</td>
            <td>${escapeHtml(item.year)}</td>
            <td>${escapeHtml(item.plate_number)}</td>
            <td><span class="badge badge-type">${escapeHtml(
              VEHICLE_TYPE_LABELS[item.vehicle_type] || item.vehicle_type
            )}</span></td>
            <td>${escapeHtml(Number(item.mileage).toLocaleString("id-ID"))} km</td>
            <td class="table-actions">
              <a class="btn btn-outline-muted btn-sm" href="/vehicles/${item.id}/">Detail</a>
              <button class="btn btn-outline-muted btn-sm" type="button" data-action="edit" data-id="${
                item.id
              }">Edit</button>
              <button class="btn btn-outline-danger btn-sm" type="button" data-action="delete" data-id="${
                item.id
              }">Hapus</button>
            </td>
          </tr>
        `
      )
      .join("");
  }

  async function load() {
    const params = new URLSearchParams();
    if (searchInput.value.trim()) {
      params.set("search", searchInput.value.trim());
    }
    const query = params.toString();

    try {
      const data = await api(`/vehicles/${query ? `?${query}` : ""}`);
      items = data.results || [];
      countLabel.textContent = `${data.count.toLocaleString("id-ID")} kendaraan`;
      render();
    } catch (error) {
      body.innerHTML = `<tr><td colspan="7"><div class="empty-state">${escapeHtml(
        errorText(error)
      )}</div></td></tr>`;
    }
  }

  function openCreate() {
    editingId = null;
    form.reset();
    clearFormErrors(form);
    modalTitle.textContent = "Tambah Kendaraan";
    showModal(modalId);
  }

  function openEdit(item) {
    editingId = item.id;
    form.reset();
    clearFormErrors(form);
    modalTitle.textContent = "Edit Kendaraan";
    fillForm(form, item);
    showModal(modalId);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearFormErrors(form);
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const data = formData(form);
    const payload = {
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
    };
    const isEdit = editingId != null;

    try {
      await api(`/vehicles/${isEdit ? `${editingId}/` : ""}`, {
        method: isEdit ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      });
      hideModal(modalId);
      showToast(isEdit ? "Kendaraan diperbarui." : "Kendaraan ditambahkan.");
      await loadVehicleCache();
      await load();
    } catch (error) {
      showFormErrors(form, error.data || error.message);
    }
  });

  body.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) {
      return;
    }
    const item = items.find(
      (candidate) => String(candidate.id) === button.dataset.id
    );
    if (!item) {
      return;
    }

    if (button.dataset.action === "edit") {
      openEdit(item);
      return;
    }

    if (button.dataset.action === "delete") {
      if (!window.confirm(`Hapus kendaraan "${item.name}"?`)) {
        return;
      }
      try {
        await api(`/vehicles/${item.id}/`, { method: "DELETE" });
        showToast("Kendaraan dihapus.");
        await loadVehicleCache();
        await load();
      } catch (error) {
        showToast(errorText(error), "danger");
      }
    }
  });

  addButton.addEventListener("click", openCreate);
  searchInput.addEventListener("input", debounce(load, 300));

  load();
});
