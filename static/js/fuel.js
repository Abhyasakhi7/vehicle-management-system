document.addEventListener("DOMContentLoaded", async () => {
  if (!requireAuth()) {
    return;
  }

  await loadVehicleCache();

  const form = document.getElementById("record-form");
  const preview = document.getElementById("fuel-total-preview");

  function updatePreview() {
    if (!preview || !form) {
      return;
    }
    const liters = Number(form.elements.liters.value || 0);
    const price = Number(form.elements.price_per_liter.value || 0);
    preview.value = formatMoney(liters * price);
  }

  initRecordPage({
    endpoint: "/fuel/",
    colspan: 9,
    emptyText: "Belum ada catatan pengisian BBM.",
    createTitle: "Tambah Pengisian BBM",
    editTitle: "Edit Pengisian BBM",
    savedMessage: "Catatan BBM tersimpan.",
    updatedMessage: "Catatan BBM diperbarui.",
    deletedMessage: "Catatan BBM dihapus.",
    onOpen: updatePreview,
    renderRow: (item) => `
      <tr>
        <td>${escapeHtml(formatDate(item.date))}</td>
        <td>${escapeHtml(vehicleLabel(item.vehicle))}</td>
        <td>${escapeHtml(Number(item.mileage).toLocaleString("id-ID"))} km</td>
        <td>${escapeHtml(Number(item.liters).toLocaleString("id-ID"))} L</td>
        <td>${escapeHtml(formatMoney(item.price_per_liter))}</td>
        <td>${escapeHtml(formatMoney(item.total_cost))}</td>
        <td>${
          item.is_full_tank
            ? '<span class="badge badge-status-COMPLETED">Ya</span>'
            : '<span class="text-muted">Tidak</span>'
        }</td>
        <td>${escapeHtml(item.station_name || "-")}</td>
        <td class="table-actions">
          <button class="btn btn-outline-muted btn-sm" type="button" data-action="edit" data-id="${
            item.id
          }">Edit</button>
          <button class="btn btn-outline-danger btn-sm" type="button" data-action="delete" data-id="${
            item.id
          }">Hapus</button>
        </td>
      </tr>
    `,
    formToPayload: (data, element) => ({
      vehicle: Number(data.vehicle),
      date: data.date,
      mileage: Number(data.mileage),
      liters: data.liters,
      price_per_liter: data.price_per_liter,
      is_full_tank: element.elements.is_full_tank.checked,
      station_name: data.station_name,
    }),
  });

  if (form) {
    form.addEventListener("input", updatePreview);
  }
});
