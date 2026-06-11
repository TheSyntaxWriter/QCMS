(() => {
  const cfg = window.responsePageConfig;
  if (!cfg) return;

  const chartData = JSON.parse(document.getElementById('response-chart-data').textContent);
  const rolePermissionData = JSON.parse(document.getElementById('role-permission-data')?.textContent || '{}');

  const deletePopup = document.getElementById('deletePopup');
  const deleteResponseIdInput = document.getElementById('deleteResponseId');
  const decisionModal = document.getElementById('responseDecisionModal');
  const decisionTitle = document.getElementById('responseDecisionTitle');
  const decisionLabel = document.getElementById('responseDecisionLabel');
  const decisionComment = document.getElementById('responseDecisionComment');
  const decisionError = document.getElementById('responseDecisionError');
  const decisionConfirm = document.getElementById('confirmResponseDecision');
  const decisionClose = document.getElementById('closeResponseDecision');
  const decisionCancel = document.getElementById('cancelResponseDecision');

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
  ];

  let editingRole = null;
  let pendingDecision = null;

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

  function safeFileUrl(rawUrl) {
    if (!rawUrl) return '';
    try {
      const parsed = new URL(rawUrl, window.location.origin);
      if (!['http:', 'https:'].includes(parsed.protocol)) return '';
      if (parsed.origin !== window.location.origin) return '';
      return parsed.href;
    } catch (_error) {
      return '';
    }
  }

  function renderResponseDetail(container, data) {
    container.replaceChildren();

    const title = document.createElement('h4');
    title.textContent = `${data.checklist_id || ''} - ${data.checklist_name || ''}`;
    container.appendChild(title);

    (data.answers || []).forEach((answer) => {
      const item = document.createElement('div');
      item.className = 'question-item';

      const question = document.createElement('strong');
      question.textContent = answer.question || '';
      item.appendChild(question);

      const answerText = document.createElement('p');
      answerText.textContent = answer.answer_text || '-';
      item.appendChild(answerText);

      const fileUrl = safeFileUrl(answer.file_url);
      if (fileUrl) {
        const viewLink = document.createElement('a');
        viewLink.href = fileUrl;
        viewLink.target = '_blank';
        viewLink.rel = 'noopener noreferrer';
        viewLink.textContent = 'View';

        const separator = document.createTextNode(' | ');

        const downloadLink = document.createElement('a');
        downloadLink.href = fileUrl;
        downloadLink.download = '';
        downloadLink.textContent = 'Download';

        item.appendChild(viewLink);
        item.appendChild(separator);
        item.appendChild(downloadLink);
      }

      container.appendChild(item);
    });

    const history = document.createElement('section');
    history.className = 'response-review-history';
    const historyTitle = document.createElement('h4');
    historyTitle.textContent = 'Approval and Rejection History';
    history.appendChild(historyTitle);

    if (!(data.decisions || []).length) {
      const empty = document.createElement('p');
      empty.textContent = 'No approval or rejection comments recorded.';
      history.appendChild(empty);
    }

    (data.decisions || []).forEach((decision) => {
      const item = document.createElement('div');
      item.className = `response-review-item ${decision.action === 'approve' ? 'is-approved' : 'is-rejected'}`;

      const heading = document.createElement('strong');
      heading.textContent = `${decision.is_override ? 'Override ' : ''}${decision.action_label || decision.action || 'Decision'}`;
      item.appendChild(heading);

      const meta = document.createElement('p');
      meta.className = 'response-review-meta';
      meta.textContent = `${decision.actor || 'Unknown'} (${decision.actor_role || 'Unknown role'}) - ${decision.created_at || ''}`;
      item.appendChild(meta);

      const comment = document.createElement('p');
      comment.className = 'response-review-comment';
      comment.textContent = decision.comment || 'No comment provided.';
      item.appendChild(comment);
      history.appendChild(item);
    });

    container.appendChild(history);
  }

  function closeDecisionModal() {
    decisionModal?.classList.remove('is-open');
    pendingDecision = null;
    if (decisionComment) decisionComment.value = '';
    if (decisionError) decisionError.textContent = '';
  }

  function openDecisionModal(action, responseId, label) {
    pendingDecision = { action, responseId };
    const isReject = action === 'reject';
    if (decisionTitle) decisionTitle.textContent = label || (isReject ? 'Reject Response' : 'Approve Response');
    if (decisionLabel) decisionLabel.textContent = isReject ? 'Rejection reason (required)' : 'Approval comment (optional)';
    if (decisionComment) {
      decisionComment.value = '';
      decisionComment.required = isReject;
      decisionComment.placeholder = isReject ? 'Explain why this response is being rejected.' : 'Add an optional approval comment.';
    }
    if (decisionError) decisionError.textContent = '';
    decisionModal?.classList.add('is-open');
    decisionComment?.focus();
  }

  async function submitDecision() {
    if (!pendingDecision) return;
    const comment = decisionComment?.value.trim() || '';
    if (pendingDecision.action === 'reject' && !comment) {
      decisionError.textContent = 'Rejection reason is required.';
      decisionComment?.focus();
      return;
    }

    decisionConfirm.disabled = true;
    const fd = new FormData();
    fd.append('action', pendingDecision.action);
    fd.append('response_id', pendingDecision.responseId);
    fd.append('comment', comment);
    fd.append('csrfmiddlewaretoken', cfg.csrfToken);
    try {
      const res = await fetch(cfg.actionUrl, { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        decisionError.textContent = data.error || 'Unable to update this response.';
        return;
      }
      location.reload();
    } catch (_error) {
      decisionError.textContent = 'Unable to update this response.';
    } finally {
      decisionConfirm.disabled = false;
    }
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
  decisionClose?.addEventListener('click', closeDecisionModal);
  decisionCancel?.addEventListener('click', closeDecisionModal);
  decisionConfirm?.addEventListener('click', submitDecision);

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
        renderResponseDetail(body, data);
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
      if (['approve','reject'].includes(action)) {
        openDecisionModal(action, responseId, btn.textContent.trim());
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
    if (event.target === decisionModal) {
      closeDecisionModal();
    }
  };

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeDeletePopup();
      closePermissionPopup();
      closeDecisionModal();
    }
  });

  renderRoleTable();
})();
