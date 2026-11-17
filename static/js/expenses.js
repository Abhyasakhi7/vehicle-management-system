const EXPENSE_CATEGORY_LABELS = {
  TAX: "Pajak",
  INSURANCE: "Asuransi",
  PARKING: "Parkir",
  TOLL: "Tol",
  WASH: "Cuci Kendaraan",
  OTHER: "Lainnya",
};

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireAuth()) {
    return;
  }

  await loadVehicleCache();

  initRecordPage({
    endpoint: "/expenses/",
    colspan: 6,
    emptyText: "Belum ada pengeluaran tercatat.",
    createTitle: "Tambah Pengeluaran",
    editTitle: "Edit Pengeluaran",
    savedMessage: "Pengeluaran tersimpan.",
    updatedMessage: "Pengeluaran diperbarui.",
    deletedMessage: "Pengeluaran dihapus.",
    renderRow: (item) => `
      <tr>
        <td>${escapeHtml(formatDate(item.date))}</td>
        <td>${escapeHtml(vehicleLabel(item.vehicle))}</td>
        <td><span class="badge badge-type">${escapeHtml(
          EXPENSE_CATEGORY_LABELS[item.category] || item.category
        )}</span></td>
        <td>${escapeHtml(item.description)}</td>
        <td>${escapeHtml(formatMoney(item.amount))}</td>
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
      category: data.category,
      description: data.description,
      amount: data.amount,
      date: data.date,
    }),
  });
});
