const REMINDER_STATUS_LABELS = {
  PENDING: "Pending",
  COMPLETED: "Selesai",
  CANCELLED: "Dibatalkan",
};

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireAuth()) {
    return;
  }

  await loadVehicleCache();

  initRecordPage({
    endpoint: "/reminders/",
    colspan: 6,
    emptyText: "Belum ada reminder.",
    createTitle: "Tambah Reminder",
    editTitle: "Edit Reminder",
    savedMessage: "Reminder tersimpan.",
    updatedMessage: "Reminder diperbarui.",
    deletedMessage: "Reminder dihapus.",
    renderRow: (item) => `
      <tr>
        <td>${escapeHtml(item.title)}${
          item.description
            ? `<div class="text-muted">${escapeHtml(item.description)}</div>`
            : ""
        }</td>
        <td>${escapeHtml(vehicleLabel(item.vehicle))}</td>
        <td>${item.due_date ? escapeHtml(formatDate(item.due_date)) : "-"}</td>
        <td>${
          item.due_mileage
            ? `${escapeHtml(Number(item.due_mileage).toLocaleString("id-ID"))} km`
            : "-"
        }</td>
        <td><span class="badge badge-status-${escapeHtml(item.status)}">${escapeHtml(
          REMINDER_STATUS_LABELS[item.status] || item.status
        )}</span></td>
        <td class="table-actions">
          ${
            item.status === "PENDING"
              ? `<button class="btn btn-outline-muted btn-sm" type="button" data-action="complete" data-id="${item.id}">Selesai</button>`
              : ""
          }
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
      title: data.title,
      description: data.description,
      due_date: data.due_date || null,
      due_mileage: data.due_mileage === "" ? null : Number(data.due_mileage),
      status: data.status,
    }),
    onAction: async (action, item, { load }) => {
      if (action !== "complete") {
        return false;
      }
      try {
        await api(`/reminders/${item.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ status: "COMPLETED" }),
        });
        showToast("Reminder ditandai selesai.");
        await load();
      } catch (error) {
        showToast(errorText(error), "danger");
      }
      return true;
    },
  });
});
