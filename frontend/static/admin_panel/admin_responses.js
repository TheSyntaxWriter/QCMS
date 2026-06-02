(() => {
  const cfg = window.responsePageConfig;
  if (!cfg) return;

  const chartData = JSON.parse(document.getElementById('response-chart-data').textContent);
  const rolePermissionData = JSON.parse(document.getElementById('role-permission-data')?.textContent || '{}');

  const deletePopup = document.getElementById('deletePopup');
  const deleteResponseIdInput = document.getElementById('deleteResponseId');

  const permissionEditPopup = document.getElementById('permissionEditPopup');
  const permissionPopupTitle = document.getElementById('permissionPopupTitle');
  const permissionColumnsList = document.getElementById('permissionColumnsList');
  const permissionActionsList = document.getElementById('permissionActionsList');
  const permissionPopupClose = document.getElementById('permissionPopupClose');
  const permissionPopupCancel = document.getElementById('permissionPopupCancel');
  const permissionPopupSave = document.getElementById('permissionPopupSave');

  const ROLE_ORDER = ['User', 'HOD', 'Management', 'Admin'];
  const RESPONSE_COLUMNS = [
    { key: 'checklist_id', label: 'Checklist ID' },
    { key: 'checklist_name', label: 'Checklist Name' },
    { key: 'checklist_type', label: 'Checklist Type' },
    { key: 'submitted_by', label: 'Submitted By' },
    { key: 'project', label: 'Project' },
    { key: 'department', label: 'Department' },
    { key: 'hod_name', label: 'HOD Name' },
    { key: 'submission_datetime', label: 'Submission DateTime' },
    { key: 'status', label: 'Status' },
    { key: 'last_updated_by', label: 'Last Updated By' },
    { key: 'last_updated', label: 'Last Updated' },
    { key: 'actions', label: 'Actions' },
  ];
  const RESPONSE_ACTIONS = [
    { key: 'view', label: 'View' },
    { key: 'edit', label: 'Edit' },
    { key: 'approve', label: 'Approve' },
    { key: 'reject', label: 'Reject' },
    { key: 'delete', label: 'Delete' },
    { key: 'toggle', label: 'Toggle' },
  ];

  let editingRole = null;

  function parseArraySafe(value, fallback = []) {
    if (Array.isArray(value)) return value;
    try {
      const parsed = JSON.parse(value || '[]');
      return Array.isArray(parsed) ? parsed : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function csvDisplay(values) {
    return Array.isArray(values) && values.length ? values.join(', ') : '-';
  }

  function getRolePermissions(role) {
    const permission = rolePermissionData[role] || {};
    return {
      visible_columns: parseArraySafe(permission.visible_columns),
      allowed_actions: parseArraySafe(permission.allowed_actions),
    };
  }

  function renderRoleTable() {
    ROLE_ORDER.forEach((role) => {
      const row = document.querySelector(`tr[data-role="${role}"]`);
      if (!row) return;
      const data = getRolePermissions(role);
      const columnsCell = row.querySelector('.role-columns-csv');
      const actionsCell = row.querySelector('.role-actions-csv');
      if (columnsCell) columnsCell.textContent = csvDisplay(data.visible_columns);
      if (actionsCell) actionsCell.textContent = csvDisplay(data.allowed_actions);
    });
  }

  function renderCheckboxList(container, options, selectedValues) {
    const selected = new Set(selectedValues);
    container.innerHTML = options.map((item) => `
      <label class="selection-item">
        <input type="checkbox" value="${item.key}" ${selected.has(item.key) ? 'checked' : ''}>
        <span>${item.label}</span>
      </label>
    `).join('');
  }

  function getCheckedValues(container) {
    return [...container.querySelectorAll('input[type="checkbox"]:checked')].map((el) => el.value);
  }

  function openPermissionPopup(role) {
    const roleData = getRolePermissions(role);
    editingRole = role;
    permissionPopupTitle.textContent = `Edit Permissions - ${role}`;
    renderCheckboxList(permissionColumnsList, RESPONSE_COLUMNS, roleData.visible_columns);
    renderCheckboxList(permissionActionsList, RESPONSE_ACTIONS, roleData.allowed_actions);
    permissionEditPopup.style.display = 'flex';
  }

  function closePermissionPopup() {
    permissionEditPopup.style.display = 'none';
    editingRole = null;
  }

  async function saveRolePermissions() {
    if (!editingRole) return;
    const visibleColumns = getCheckedValues(permissionColumnsList);
    const allowedActions = getCheckedValues(permissionActionsList);

    const fd = new FormData();
    fd.append('action', 'save_permissions');
    fd.append('role', editingRole);
    fd.append('visible_columns', JSON.stringify(visibleColumns));
    fd.append('allowed_actions', JSON.stringify(allowedActions));
    fd.append('csrfmiddlewaretoken', cfg.csrfToken);

    await fetch(cfg.actionUrl, { method: 'POST', body: fd });

    rolePermissionData[editingRole] = {
      ...(rolePermissionData[editingRole] || {}),
      visible_columns: visibleColumns,
      allowed_actions: allowedActions,
    };

    renderRoleTable();
    closePermissionPopup();
  }

  const lineCtx = document.getElementById('responseLineChart');
  if (lineCtx) {
    new Chart(lineCtx.getContext('2d'), {
      type: 'line',
      data: {
        labels: chartData.day_labels,
        datasets: [{ label: 'Day-wise submissions', data: chartData.day_values, borderColor: '#080870', backgroundColor: 'rgba(8,8,112,.1)', fill: true }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  const statusModal = document.getElementById('statusChartModal');
  const closeStatus = document.getElementById('closeStatusChart');
  let popupChart;

  document.querySelectorAll('[data-stat-chart]').forEach((btn) => {
    btn.onclick = () => {
      statusModal.classList.add('is-open');
      if (popupChart) popupChart.destroy();
      popupChart = new Chart(document.getElementById('statusPopupChart').getContext('2d'), {
        type: 'bar',
        data: {
          labels: chartData.project_labels,
          datasets: [
            { label: 'Project-wise', data: chartData.project_values, backgroundColor: '#6366f1' },
            { label: 'Department-wise', data: chartData.department_values, backgroundColor: '#22c55e' }
          ]
        },
        options: { plugins: { legend: { position: 'bottom' } } }
      });
    };
  });

  closeStatus.onclick = () => statusModal.classList.remove('is-open');

  document.querySelectorAll('.role-edit-btn').forEach((btn) => {
    btn.addEventListener('click', () => openPermissionPopup(btn.dataset.role));
  });

  permissionPopupClose?.addEventListener('click', closePermissionPopup);
  permissionPopupCancel?.addEventListener('click', closePermissionPopup);
  permissionPopupSave?.addEventListener('click', saveRolePermissions);

  function closeDeletePopup() {
    if (deletePopup) {
      deletePopup.style.display = 'none';
    }
    if (deleteResponseIdInput) {
      deleteResponseIdInput.value = '';
    }
  }

  window.closeDeletePopup = closeDeletePopup;

  document.querySelectorAll('.response-action').forEach((btn) => {
    btn.onclick = async () => {
      const action = btn.dataset.action;
      const responseId = btn.dataset.id;
      if (action === 'view') {
        const res = await fetch(`${cfg.actionUrl}?action=view&response_id=${responseId}`);
        const data = await res.json();
        const modal = document.getElementById('responseViewModal');
        const body = document.getElementById('responseViewContent');
        body.innerHTML = `<h4>${data.checklist_id} - ${data.checklist_name}</h4>` + data.answers.map((a) => `<div class='question-item'><strong>${a.question}</strong><p>${a.answer_text || '-'}</p>${a.file_url ? `<a href='${a.file_url}' target='_blank'>View</a> | <a href='${a.file_url}' download>Download</a>` : ''}</div>`).join('');
        modal.classList.add('is-open');
        document.getElementById('closeResponseView').onclick = () => modal.classList.remove('is-open');
        return;
      }
      if (action === 'edit') {
        const checklistId = btn.dataset.checklistId;
        if (checklistId && responseId && cfg.editFillUrlTemplate) {
          const baseFillUrl = cfg.editFillUrlTemplate.replace('/0/fill/', `/${checklistId}/fill/`);
          window.location.href = `${baseFillUrl}?response_id=${encodeURIComponent(responseId)}`;
        }
        return;
      }
      if (['approve','reject','toggle'].includes(action)) {
        const fd = new FormData();
        fd.append('action', action);
        fd.append('response_id', responseId);
        fd.append('csrfmiddlewaretoken', cfg.csrfToken);
        await fetch(cfg.actionUrl, { method: 'POST', body: fd });
        location.reload();
      }
    };
  });

  document.querySelectorAll('.delete-btn').forEach((btn) => {
    btn.onclick = () => {
      if (deleteResponseIdInput) {
        deleteResponseIdInput.value = btn.dataset.responseId;
      }
      if (deletePopup) {
        deletePopup.style.display = 'flex';
      }
    };
  });

  window.onclick = (event) => {
    if (event.target === deletePopup) {
      closeDeletePopup();
    }
    if (event.target === permissionEditPopup) {
      closePermissionPopup();
    }
  };

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeDeletePopup();
      closePermissionPopup();
    }
  });

  renderRoleTable();
})();
