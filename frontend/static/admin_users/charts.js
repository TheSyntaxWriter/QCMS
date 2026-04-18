document.addEventListener("DOMContentLoaded", function () {
  // =====================================================
  // 1. PIE CHART (User Status - Active vs Inactive)
  // =====================================================

  const paiCtx = document.getElementById("paiChart");

  if (paiCtx) {
    new Chart(paiCtx, {
      type: "pie",
      data: {
        labels: ["Active", "Inactive"],
        datasets: [
          {
            // Data comes from HTML (window variables)
            data: [window.active_users || 0, window.inactive_users || 0],
            backgroundColor: ["#28a745", "#dc3545"],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
          },
        },
      },
    });
  }

  // =====================================================
  // 2. STACKED BAR CHART (Department-wise Data)
  // =====================================================

  const stackedCtx = document.getElementById("stackedChart");

  if (stackedCtx) {
    new Chart(stackedCtx, {
      type: "bar",
      data: {
        // Labels from backend
        labels: window.dept_labels || [],

        datasets: [
          {
            label: "Active",
            data: window.dept_active_data || [],
            backgroundColor: "#28a745",
          },
          {
            label: "Inactive",
            data: window.dept_inactive_data || [],
            backgroundColor: "#dc3545",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,

        // Enable stacked bars
        scales: {
          x: { stacked: true },
          y: { stacked: true },
        },

        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });
  }
});
