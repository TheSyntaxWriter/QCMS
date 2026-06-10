(() => {
  // Parse dashboard configuration emitted via json_script from Django.
  const rawConfig = document.getElementById('admin-dashboard-config');
  if (!rawConfig) return;

  const dashboardConfig = JSON.parse(rawConfig.textContent);
  const modal = document.getElementById('dashboardChartModal');
  const closeBtn = document.getElementById('dashboardModalClose');
  const titleElement = document.getElementById('dashboardChartTitle');
  const canvas = document.getElementById('dashboardChartCanvas');

  if (!modal || !closeBtn || !titleElement || !canvas) return;

  let activeChart = null;

  // Shared dataset styling requested for all chart types.
  const withBorder = (dataset) => ({
    borderColor: '#000000',
    borderWidth: 1,
    ...dataset,
  });

  // Define all card-driven chart mappings in one place for maintainability.
  const chartMap = {
    users: {
      title: 'Users Breakdown (Active vs Inactive)',
      type: 'pie',
      data: {
        labels: ['Active', 'Inactive'],
        datasets: [
          withBorder({
            data: [dashboardConfig.charts.users.active, dashboardConfig.charts.users.inactive],
            backgroundColor: ['#22c55e', '#ef4444'],
          }),
        ],
      },
    },
    checklists: {
      title: 'Checklists Breakdown (Active vs Inactive)',
      type: 'pie',
      data: {
        labels: ['Active', 'Inactive'],
        datasets: [
          withBorder({
            data: [dashboardConfig.charts.checklists.active, dashboardConfig.charts.checklists.inactive],
            backgroundColor: ['#10b981', '#f97316'],
          }),
        ],
      },
    },
    departments: {
      title: 'Users per Department (Active / Inactive)',
      type: 'bar',
      data: {
        labels: dashboardConfig.charts.departments.labels,
        datasets: [
          withBorder({
            label: 'Active Users',
            data: dashboardConfig.charts.departments.activeUsers,
            backgroundColor: '#3b82f6',
          }),
          withBorder({
            label: 'Inactive Users',
            data: dashboardConfig.charts.departments.inactiveUsers,
            backgroundColor: '#f43f5e',
          }),
        ],
      },
      options: {
        scales: {
          x: { stacked: false },
          y: { beginAtZero: true },
        },
      },
    },
    projects: {
      title: 'Users per Project (Active / Inactive)',
      type: 'bar',
      data: {
        labels: dashboardConfig.charts.projects.labels,
        datasets: [
          withBorder({
            label: 'Active Users',
            data: dashboardConfig.charts.projects.activeUsers,
            backgroundColor: '#6366f1',
          }),
          withBorder({
            label: 'Inactive Users',
            data: dashboardConfig.charts.projects.inactiveUsers,
            backgroundColor: '#fb7185',
          }),
        ],
      },
      options: {
        scales: {
          x: { stacked: false },
          y: { beginAtZero: true },
        },
      },
    },
    submittedChecklists: {
      title: 'Submitted Checklists Status Split',
      type: 'pie',
      data: {
        labels: ['Approved', 'Pending for Approval', 'Pending (Legacy)', 'WIP', 'Rejected'],
        datasets: [
          withBorder({
            data: [
              dashboardConfig.charts.submittedChecklists.approved,
              dashboardConfig.charts.submittedChecklists.pendingApproval,
              dashboardConfig.charts.submittedChecklists.legacyPending,
              dashboardConfig.charts.submittedChecklists.wip,
              dashboardConfig.charts.submittedChecklists.rejected,
            ],
            backgroundColor: ['#16a34a', '#f59e0b', '#64748b', '#0ea5e9', '#dc2626'],
          }),
        ],
      },
    },
  };

  const openChart = (chartKey) => {
    const chartDefinition = chartMap[chartKey];
    if (!chartDefinition) return;

    if (activeChart) {
      activeChart.destroy();
      activeChart = null;
    }

    titleElement.textContent = chartDefinition.title;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');

    activeChart = new Chart(canvas.getContext('2d'), {
      type: chartDefinition.type,
      data: chartDefinition.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' },
        },
        ...chartDefinition.options,
      },
    });
  };

  const closeModal = () => {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');

    if (activeChart) {
      activeChart.destroy();
      activeChart = null;
    }
  };

  document.querySelectorAll('.dashboard-mini-card').forEach((card) => {
    card.addEventListener('click', () => openChart(card.dataset.chartKey));
  });

  closeBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) closeModal();
  });
})();
