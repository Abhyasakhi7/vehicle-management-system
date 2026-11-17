function initRecordPage(config) {
  const body = document.getElementById(config.tableBodyId || "records-body");
  const form = document.getElementById(config.formId || "record-form");
  const modalId = config.modalId || "record-modal";
  const modalTitle = document.getElementById(
    config.modalTitleId || "record-modal-title"
  );
  const searchInput = document.getElementById(config.searchId || "record-search");
  const vehicleFilter = document.getElementById(
    config.vehicleFilterId || "vehicle-filter"
  );
  const addButton = document.getElementById(config.addBtnId || "add-record-btn");
  const colspan = config.colspan || 6;
  const vehicleSelect = form ? form.querySelector('[name="vehicle"]') : null;

  const state = {
    items: [],
    editingId: null,
    query: new URLSearchParams(window.location.search).get("vehicle") || "",
  };

  if (!body || !form) {
    return null;
  }

  async function load() {
    const params = new URLSearchParams();
    if (searchInput && searchInput.value.trim()) {
      params.set("search", searchInput.value.trim());
    }
    if (vehicleFilter && vehicleFilter.value) {
      params.set("vehicle", vehicleFilter.value);
    }
    const query = params.toString();

    try {
      const data = await api(`${config.endpoint}${query ? `?${query}` : ""}`);
      state.items = data.results || [];
      render();
    } catch (error) {
      body.innerHTML = `<tr><td colspan="${colspan}"><div class="empty-state">${escapeHtml(
        errorText(error)
      )}</div></td></tr>`;
    }
  }

  function render() {
    if (!state.items.length) {
      body.innerHTML = `<tr><td colspan="${colspan}"><div class="empty-state">${escapeHtml(
        config.emptyText || "Belum ada data."
      )}</div></td></tr>`;
      return;
    }
    body.innerHTML = state.items.map(config.renderRow).join("");
  }

  async function openCreate() {
    state.editingId = null;
    form.reset();
    clearFormErrors(form);
    if (modalTitle) {
      modalTitle.textContent = config.createTitle || "Tambah Data";
    }
    if (vehicleSelect) {
      await loadVehicleOptions(
        vehicleSelect,
        (vehicleFilter && vehicleFilter.value) || state.query || null
      );
      if (!vehicleSelect.options.length) {
        showToast("Tambahkan kendaraan terlebih dahulu.", "danger");
        return;
      }
    }
    if (config.onOpen) {
      config.onOpen(form, null);
    }
    showModal(modalId);
  }

  async function openEdit(item) {
    state.editingId = item.id;
    form.reset();
    clearFormErrors(form);
    if (modalTitle) {
      modalTitle.textContent = config.editTitle || "Edit Data";
    }
    if (vehicleSelect) {
      await loadVehicleOptions(vehicleSelect, item.vehicle);
    }
    fillForm(form, item);
    if (config.onOpen) {
      config.onOpen(form, item);
    }
    showModal(modalId);
  }

  async function submit(event) {
    event.preventDefault();
    clearFormErrors(form);
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const data = formData(form);
    const payload = config.formToPayload ? config.formToPayload(data, form) : data;
    const isEdit = state.editingId != null;

    try {
      await api(`${config.endpoint}${isEdit ? `${state.editingId}/` : ""}`, {
        method: isEdit ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      });
      hideModal(modalId);
      showToast(
        isEdit
          ? config.updatedMessage || config.savedMessage || "Data diperbarui."
          : config.savedMessage || "Data tersimpan."
      );
      await load();
      if (config.onSaved) {
        await config.onSaved();
      }
    } catch (error) {
      showFormErrors(form, error.data || error.message);
    }
  }

  async function remove(item) {
    if (!window.confirm(config.deleteConfirm || "Hapus data ini?")) {
      return;
    }
    try {
      await api(`${config.endpoint}${item.id}/`, { method: "DELETE" });
      showToast(config.deletedMessage || "Data dihapus.");
      await load();
      if (config.onSaved) {
        await config.onSaved();
      }
    } catch (error) {
      showToast(errorText(error), "danger");
    }
  }

  body.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) {
      return;
    }
    const item = state.items.find(
      (candidate) => String(candidate.id) === button.dataset.id
    );
    if (!item) {
      return;
    }

    const action = button.dataset.action;
    if (
      config.onAction &&
      (await config.onAction(action, item, { load, state }))
    ) {
      return;
    }
    if (action === "edit") {
      await openEdit(item);
    } else if (action === "delete") {
      await remove(item);
    }
  });

  if (addButton) {
    addButton.addEventListener("click", openCreate);
  }
  form.addEventListener("submit", submit);
  if (searchInput) {
    searchInput.addEventListener("input", debounce(load, 300));
  }
  if (vehicleFilter) {
    vehicleFilter.addEventListener("change", () => {
      state.query = vehicleFilter.value;
      load();
    });
  }

  (async () => {
    if (vehicleFilter) {
      try {
        const data = await api("/vehicles/");
        vehicleFilter.innerHTML = `<option value="">Semua kendaraan</option>${data.results
          .map(
            (vehicle) =>
              `<option value="${vehicle.id}">${escapeHtml(vehicle.name)} (${escapeHtml(
                vehicle.plate_number
              )})</option>`
          )
          .join("")}`;
        if (state.query) {
          vehicleFilter.value = state.query;
        }
      } catch (error) {
        showToast(errorText(error), "danger");
      }
    }
    await load();
  })();

  return { load, openCreate, state };
}
