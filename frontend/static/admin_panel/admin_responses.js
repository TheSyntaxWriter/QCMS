(() => {
  const cfg = window.responsePageConfig;
  if (!cfg) return;
  const chartData = JSON.parse(document.getElementById('response-chart-data').textContent);

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

  const qs = new URLSearchParams(window.location.search);
  [['responseProjectFilter','project'],['responseDepartmentFilter','department'],['responseStatusFilter','status'],['dateFromFilter','date_from'],['dateToFilter','date_to'],['responseSearch','search']]
    .forEach(([id,key]) => {
      const el = document.getElementById(id); if (!el) return;
      el.onchange = () => { if (el.value) qs.set(key, el.value); else qs.delete(key); window.location.search = qs.toString(); };
    });

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
    fd.append('role', document.getElementById('permissionRole').value);
    fd.append('visible_columns', document.getElementById('visibleColumnsInput').value || '[]');
    fd.append('allowed_actions', document.getElementById('allowedActionsInput').value || '[]');
    fd.append('csrfmiddlewaretoken', cfg.csrfToken);
    await fetch(cfg.actionUrl, { method: 'POST', body: fd });
    alert('Role permissions saved');
  });
})();
