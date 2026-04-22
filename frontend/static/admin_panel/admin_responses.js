(() => {
  const cfg = window.responsePageConfig;
  if (!cfg) return;
  const chartData = JSON.parse(document.getElementById('response-chart-data').textContent);
  const rolePermissionData = JSON.parse(document.getElementById('role-permission-data')?.textContent || '{}');
  const projectsData = JSON.parse(document.getElementById('response-project-data')?.textContent || '[]');
  const deletePopup = document.getElementById('deletePopup');
  const deleteResponseIdInput = document.getElementById('deleteResponseId');
  const permissionRoleEl = document.getElementById('permissionRole');
  const visibleColumnsInput = document.getElementById('visibleColumnsInput');
  const selectedProjectsInput = document.getElementById('selectedProjectsInput');
  const allowedActionsInput = document.getElementById('allowedActionsInput');

  const selectionPopup = document.getElementById('selectionPopup');
  const selectionPopupTitle = document.getElementById('selectionPopupTitle');
  const selectionPopupList = document.getElementById('selectionPopupList');
  const selectionPopupClose = document.getElementById('selectionPopupClose');
  const selectionPopupCancel = document.getElementById('selectionPopupCancel');
  const selectionPopupSave = document.getElementById('selectionPopupSave');
  const selectColumnsBtn = document.getElementById('selectColumnsBtn');
  const selectProjectsBtn = document.getElementById('selectProjectsBtn');
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
  let selectionContext = null;

  function parseArraySafe(value, fallback = []) {
    try {
      const parsed = JSON.parse(value || '[]');
      return Array.isArray(parsed) ? parsed : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function setRoleInputs(role) {
    const rolePermission = rolePermissionData[role] || {};
    const visibleColumns = Array.isArray(rolePermission.visible_columns) ? rolePermission.visible_columns : [];
    const allowedActions = Array.isArray(rolePermission.allowed_actions) ? rolePermission.allowed_actions : [];
    const selectedProjects = Array.isArray(rolePermission.selected_projects) ? rolePermission.selected_projects : [];

    visibleColumnsInput.value = JSON.stringify(visibleColumns);
    allowedActionsInput.value = JSON.stringify(allowedActions);
    selectedProjectsInput.value = JSON.stringify(selectedProjects);
  }

  function openSelectionPopup({ type, title, options, selectedValues }) {
    if (!selectionPopup || !selectionPopupTitle || !selectionPopupList) return;
    selectionContext = { type, options };
    selectionPopupTitle.textContent = title;
    const selected = new Set(selectedValues.map(String));
    selectionPopupList.innerHTML = options.map((item) => `
      <label class="selection-item">
        <input type="checkbox" value="${item.value}" ${selected.has(String(item.value)) ? 'checked' : ''}>
        <span>${item.label}</span>
      </label>
    `).join('');
    selectionPopup.style.display = 'flex';
  }

  function closeSelectionPopup() {
    if (selectionPopup) {
      selectionPopup.style.display = 'none';
    }
    selectionContext = null;
  }

  const lineCtx = document.getElementById('responseLineChart');
  if (lineCtx) {
    new Chart(lineCtx.getContext('2d'), {
      type: 'line',
      data: { labels: chartData.day_labels, datasets: [{ label: 'Day-wise submissions', data: chartData.day_values, borderColor:'#080870', backgroundColor:'rgba(8,8,112,.1)', fill:true }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  const statusModal = document.getElementById('statusChartModal');
  const closeStatus = document.getElementById('closeStatusChart');
  let popupChart;
  document.querySelectorAll('[data-stat-chart]').forEach(btn => btn.onclick = () => {
    statusModal.classList.add('is-open');
    if (popupChart) popupChart.destroy();
    popupChart = new Chart(document.getElementById('statusPopupChart').getContext('2d'), {
      type: 'bar',
      data: {
        labels: chartData.project_labels,
        datasets: [{ label: 'Project-wise', data: chartData.project_values, backgroundColor:'#6366f1' }, { label: 'Department-wise', data: chartData.department_values, backgroundColor:'#22c55e' }]
      },
      options: { plugins: { legend: { position: 'bottom' } } }
    });
  });
  closeStatus.onclick = () => statusModal.classList.remove('is-open');

  setRoleInputs(permissionRoleEl?.value || 'User');
  permissionRoleEl?.addEventListener('change', () => setRoleInputs(permissionRoleEl.value));

  selectColumnsBtn?.addEventListener('click', () => {
    openSelectionPopup({
      type: 'columns',
      title: 'Select Columns',
      options: RESPONSE_COLUMNS.map((col) => ({ value: col.key, label: col.label })),
      selectedValues: parseArraySafe(visibleColumnsInput.value),
    });
  });

  selectProjectsBtn?.addEventListener('click', () => {
    openSelectionPopup({
      type: 'projects',
      title: 'Select Projects',
      options: projectsData.map((project) => ({ value: project.id, label: `${project.name} (${project.domain})` })),
      selectedValues: parseArraySafe(selectedProjectsInput.value),
    });
  });

  selectionPopupClose?.addEventListener('click', closeSelectionPopup);
  selectionPopupCancel?.addEventListener('click', closeSelectionPopup);

  selectionPopupSave?.addEventListener('click', () => {
    if (!selectionContext || !selectionPopupList) return;
    const selectedValues = [...selectionPopupList.querySelectorAll('input[type=\"checkbox\"]:checked')].map((checkbox) => checkbox.value);
    if (selectionContext.type === 'columns') {
      visibleColumnsInput.value = JSON.stringify(selectedValues);
    }
    if (selectionContext.type === 'projects') {
      selectedProjectsInput.value = JSON.stringify(selectedValues.map((value) => Number(value)));
    }
    closeSelectionPopup();
  });

  function closeDeletePopup() {
    if (deletePopup) {
      deletePopup.style.display = 'none';
    }
    if (deleteResponseIdInput) {
      deleteResponseIdInput.value = '';
    }
  }
  window.closeDeletePopup = closeDeletePopup;

  document.querySelectorAll('.response-action').forEach(btn => btn.onclick = async () => {
    const action = btn.dataset.action;
    const responseId = btn.dataset.id;
    if (action === 'view') {
      const res = await fetch(`${cfg.actionUrl}?action=view&response_id=${responseId}`);
      const data = await res.json();
      const modal = document.getElementById('responseViewModal');
      const body = document.getElementById('responseViewContent');
      body.innerHTML = `<h4>${data.checklist_id} - ${data.checklist_name}</h4>` + data.answers.map(a => `<div class='question-item'><strong>${a.question}</strong><p>${a.answer_text || '-'}</p>${a.file_url ? `<a href='${a.file_url}' target='_blank'>View</a> | <a href='${a.file_url}' download>Download</a>` : ''}</div>`).join('');
      modal.classList.add('is-open');
      document.getElementById('closeResponseView').onclick = () => modal.classList.remove('is-open');
      return;
    }
    if (action === 'approve' || action === 'reject') {
      const fd = new FormData(); fd.append('action', action); fd.append('response_id', responseId); fd.append('csrfmiddlewaretoken', cfg.csrfToken);
      await fetch(cfg.actionUrl, { method: 'POST', body: fd });
      location.reload();
    }
  });

  document.getElementById('savePermissionsBtn')?.addEventListener('click', async () => {
    const fd = new FormData();
    fd.append('action', 'save_permissions');
    fd.append('role', permissionRoleEl.value);
    fd.append('visible_columns', visibleColumnsInput.value || '[]');
    fd.append('selected_projects', selectedProjectsInput.value || '[]');
    fd.append('allowed_actions', allowedActionsInput.value || '[]');
    fd.append('csrfmiddlewaretoken', cfg.csrfToken);
    await fetch(cfg.actionUrl, { method: 'POST', body: fd });
    rolePermissionData[permissionRoleEl.value] = {
      ...(rolePermissionData[permissionRoleEl.value] || {}),
      visible_columns: parseArraySafe(visibleColumnsInput.value),
      selected_projects: parseArraySafe(selectedProjectsInput.value),
      allowed_actions: parseArraySafe(allowedActionsInput.value),
    };
    alert('Role permissions saved');
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

  window.onclick = function (event) {
    if (event.target === deletePopup) {
      closeDeletePopup();
    }
    if (event.target === selectionPopup) {
      closeSelectionPopup();
    }
  };

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      closeDeletePopup();
      closeSelectionPopup();
    }
  });
})();
