document.addEventListener("DOMContentLoaded", function () {
  const configScript = document.getElementById("admin-users-config");
  const config = configScript ? JSON.parse(configScript.textContent) : {};

  const popup = document.getElementById("popup");
  const popupBody = document.getElementById("popup-body");
  const popupTitle = document.getElementById("popup-title");
  const saveBtn = document.getElementById("saveBtn");

  const deletePopup = document.getElementById("deletePopup");
  const deleteUserIdInput = document.getElementById("deleteUserId");

  function escapeHtml(value) {
    const text = value == null ? "" : String(value);
    return text
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function renderRoleOptions(selectedRole) {
    const role = selectedRole || "User";
    return `
      <option ${role === "User" ? "selected" : ""}>User</option>
      <option ${role === "HOD" ? "selected" : ""}>HOD</option>
      <option ${role === "Management" ? "selected" : ""}>Management</option>
      <option ${role === "Admin" ? "selected" : ""}>Admin</option>
    `;
  }

  function renderDepartmentOptions(selectedDepartmentId) {
    const selected = String(selectedDepartmentId || "");
    const departmentOptions = (config.departments || [])
      .map((department) => {
        const isSelected = selected === String(department.id);
        return `<option value="${department.id}" ${isSelected ? "selected" : ""}>${department.name}</option>`;
      })
      .join("");

    return `<option value="">Select Dept</option>${departmentOptions}`;
  }

  function renderProjectOptions(selectedProjectId) {
    const selected = String(selectedProjectId || "");
    const projectOptions = (config.projects || [])
      .map((project) => {
        const isSelected = selected === String(project.id);
        return `<option value="${project.id}" ${isSelected ? "selected" : ""}>${project.name} (${project.domain})</option>`;
      })
      .join("");

    return `<option value="">Select Project</option>${projectOptions}`;
  }

  function renderHodOptions(selectedHodId) {
    const selected = String(selectedHodId || "");
    const hodOptions = (config.hodUsers || [])
      .map((hod) => {
        const isSelected = selected === String(hod.id);
        return `<option value="${hod.id}" ${isSelected ? "selected" : ""}>${escapeHtml(hod.name)}</option>`;
      })
      .join("");

    return `<option value="">Select HOD</option>${hodOptions}`;
  }

  function renderUserForm({
    mode,
    action,
    editId,
    username,
    firstName,
    lastName,
    email,
    role,
    departmentId,
    projectId,
    assignedHodId,
  }) {
    const isAdd = mode === "add";

    return `
      <form id="userForm" class="user-form-grid" method="POST" action="${action}">
        <input type="hidden" name="csrfmiddlewaretoken" value="${config.csrfToken || ""}">
        ${isAdd ? '<input type="hidden" name="form_type" value="user">' : `<input type="hidden" name="edit_id" value="${editId || ""}">`}
        <div class="form-field">
          <label>Username</label>
          <input name="username" class="form-control" value="${username || ""}" required>
        </div>
        <div class="form-field">
          <label>${isAdd ? "Password" : "Password (optional)"}</label>
          <input type="password" name="password" class="form-control" ${isAdd ? "required" : ""}>
        </div>
        <div class="form-field">
          <label>First Name</label>
          <input name="first_name" class="form-control" value="${firstName || ""}">
        </div>
        <div class="form-field">
          <label>Last Name</label>
          <input name="last_name" class="form-control" value="${lastName || ""}">
        </div>
        <div class="form-field">
          <label>Email</label>
          <input type="email" name="email" class="form-control" value="${email || ""}" required>
        </div>
        <div class="form-field">
          <label>Role</label>
          <select name="role" class="form-control">${renderRoleOptions(role)}</select>
        </div>
        <div class="form-field">
          <label>Department</label>
          <select name="department" class="form-control">${renderDepartmentOptions(departmentId)}</select>
        </div>
        <div class="form-field">
          <label>Project</label>
          <select name="project" class="form-control">${renderProjectOptions(projectId)}</select>
        </div>
        <div class="form-field">
          <label>Assigned HOD</label>
          <select name="assigned_hod" class="form-control">${renderHodOptions(assignedHodId)}</select>
        </div>
      </form>
    `;
  }

  function closePopup() {
    popup.style.display = "none";
  }

  function closeDeletePopup() {
    deletePopup.style.display = "none";
    if (deleteUserIdInput) {
      deleteUserIdInput.value = "";
    }
  }

  window.closePopup = closePopup;
  window.closeDeletePopup = closeDeletePopup;

  if (window.Chart) {
    const charts = config.charts || {};
    const pieCanvas = document.getElementById("paiChart");
    if (pieCanvas) {
      const pieCtx = pieCanvas.getContext("2d");
      new Chart(pieCtx, {
        type: "pie",
        data: {
          labels: ["Active", "Inactive"],
          datasets: [{
            data: [charts.active || 0, charts.inactive || 0],
            backgroundColor: ["#28a745", "#dc3545"],
            borderColor: "#170101",
            borderWidth: 1,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "right" } },
        },
      });
    }

    const stackedCanvas = document.getElementById("stackedChart");
    if (stackedCanvas) {
      const stackedCtx = stackedCanvas.getContext("2d");
      new Chart(stackedCtx, {
        type: "bar",
        data: {
          labels: charts.deptLabels || [],
          datasets: [
            { label: "Active", data: charts.deptActiveData || [], backgroundColor: "#28a745", borderColor: "#170101", borderWidth: 1 },
            { label: "Inactive", data: charts.deptInactiveData || [], backgroundColor: "#dc3545", borderColor: "#170101", borderWidth: 1 },
          ],
        },
        options: {
          scales: { x: { stacked: true }, y: { stacked: true } },
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
        },
      });
    }
  }

  const addUserBtn = document.getElementById("addUserBtn");
  if (addUserBtn) {
    addUserBtn.onclick = function () {
      popup.style.display = "flex";
      popupTitle.innerText = "Add New User";
      saveBtn.style.display = "inline-block";
      popupBody.innerHTML = renderUserForm({
        mode: "add",
        action: config.createUrl || "/admin-create/",
      });
    };
  }

  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.onclick = function () {
      popup.style.display = "flex";
      popupTitle.innerText = "Edit User";
      saveBtn.style.display = "inline-block";
      popupBody.innerHTML = renderUserForm({
        mode: "edit",
        action: config.editUrl || "/admin-user-action/",
        editId: this.dataset.id,
        username: this.dataset.username,
        firstName: this.dataset.first,
        lastName: this.dataset.last,
        email: this.dataset.email,
        role: this.dataset.role,
        departmentId: this.dataset.deptId,
        projectId: this.dataset.projectId,
        assignedHodId: this.dataset.assignedHodId,
      });
    };
  });

  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.onclick = function () {
      popup.style.display = "flex";
      popupTitle.innerText = "User Information";
      saveBtn.style.display = "none";
      const statusText = this.dataset.status === "True" ? "Active" : "Inactive";
      popupBody.innerHTML = `
        <div style="line-height: 2;">
          <p><b>Username:</b> ${escapeHtml(this.dataset.username)}</p>
          <p><b>Name:</b> ${escapeHtml(this.dataset.first)} ${escapeHtml(this.dataset.last)}</p>
          <p><b>Email:</b> ${escapeHtml(this.dataset.email || "-")}</p>
          <p><b>Role:</b> ${escapeHtml(this.dataset.role)}</p>
          <p><b>Department:</b> ${escapeHtml(this.dataset.dept)}</p>
          <p><b>Project:</b> ${escapeHtml(this.dataset.project)}</p>
          <p><b>Assigned HOD:</b> ${escapeHtml(this.dataset.assignedHod || "-")}</p>
          <p><b>Status:</b> ${statusText}</p>
        </div>`;
    };
  });

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.onclick = function () {
      if (deleteUserIdInput) {
        deleteUserIdInput.value = this.dataset.userId;
      }
      deletePopup.style.display = "flex";
    };
  });

  saveBtn.onclick = function () {
    const form = document.getElementById("userForm");
    if (form) {
      form.submit();
    }
  };

  window.onclick = function (event) {
    if (event.target === popup) {
      closePopup();
    }
    if (event.target === deletePopup) {
      closeDeletePopup();
    }
  };

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closePopup();
      closeDeletePopup();
    }
  });
});
