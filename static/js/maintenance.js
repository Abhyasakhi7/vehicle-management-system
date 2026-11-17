const MAINTENANCE_TYPE_LABELS = {
  OIL_CHANGE: "Ganti Oli",
  TIRE: "Ganti Ban",
  BRAKES: "Servis Rem",
  BATTERY: "Baterai",
  GENERAL_SERVICE: "Servis Umum",
  REPAIR: "Perbaikan",
  OTHER: "Lainnya",
};

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireAuth()) {
    return;
  }

  await loadVehicleCache();

  initRecordPage({
    endpoint: "/maintenance/",
    colspan: 8,
    emptyText: "Belum ada catatan servis.",
    createTitle: "Tambah Catatan Servis",
    editTitle: "Edit Catatan Servis",
    savedMessage: "Catatan servis tersimpan.",
    updatedMessage: "Catatan servis diperbarui.",
    deletedMessage: "Catatan servis dihapus.",
    renderRow: (item) => `
      <tr>
        <td>${escapeHtml(formatDate(item.service_date))}</td>
        <td>${escapeHtml(vehicleLabel(item.vehicle))}</td>
        <td><span class="badge badge-type">${escapeHtml(
          MAINTENANCE_TYPE_LABELS[item.service_type] || item.service_type
        )}</span></td>
        <td>${escapeHtml(item.description || "-")}${
          item.workshop_name
            ? `<div class="text-muted">${escapeHtml(item.workshop_name)}</div>`
            : ""
        }</td>
        <td>${escapeHtml(Number(item.mileage).toLocaleString("id-ID"))} km</td>
        <td>${escapeHtml(formatMoney(item.cost))}</td>
        <td>${
          item.next_service_date ? escapeHtml(formatDate(item.next_service_date)) : "-"
        }${
          item.next_service_mileage
            ? `<div class="text-muted">${escapeHtml(
                Number(item.next_service_mileage).toLocaleString("id-ID")
              )} km</div>`
            : ""
        }</td>
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
    formToPayload: (data) => ({
      vehicle: Number(data.vehicle),
      service_type: data.service_type,
      description: data.description,
      service_date: data.service_date,
      mileage: Number(data.mileage),
      cost: data.cost,
      workshop_name: data.workshop_name,
      next_service_date: data.next_service_date || null,
      next_service_mileage:
        data.next_service_mileage === "" ? null : Number(data.next_service_mileage),
    }),
  });
});
