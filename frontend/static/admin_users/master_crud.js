document.addEventListener("DOMContentLoaded", function () {
  const configScript = document.getElementById("entity-config");
  const config = configScript ? JSON.parse(configScript.textContent) : {};

  const popup = document.getElementById("popup");
  const popupBody = document.getElementById("popup-body");
  const popupTitle = document.getElementById("popup-title");
  const saveBtn = document.getElementById("saveBtn");
  const addBtn = document.getElementById("addEntityBtn");

  const deletePopup = document.getElementById("deletePopup");
  const deleteEntityIdInput = document.getElementById("deleteEntityId");

  const isProjectPage = window.location.pathname.includes("/admin-panel/projects/");

  function closePopup() {
    popup.style.display = "none";
  }

  function closeDeletePopup() {
    deletePopup.style.display = "none";
    if (deleteEntityIdInput) {
      deleteEntityIdInput.value = "";
    }
  }

  function renderDepartmentForm(mode, payload) {
    const isAdd = mode === "add";
    return `
      <form id="entityForm" class="user-form-grid" method="POST" action="${isAdd ? config.createUrl : config.actionUrl}">
        <input type="hidden" name="csrfmiddlewaretoken" value="${config.csrfToken || ""}">
        ${isAdd ? '<input type="hidden" name="form_type" value="department">' : '<input type="hidden" name="action" value="edit">'}
        ${isAdd ? "" : `<input type="hidden" name="department_id" value="${payload.id}">`}
        <div class="form-field">
          <label>Department Code</label>
          <input class="form-control" name="code" value="${payload.code || ""}" required>
        </div>
        <div class="form-field">
          <label>Department Name</label>
          <input class="form-control" name="name" value="${payload.name || ""}" required>
        </div>
        <div class="form-field">
          <label>Status</label>
          <select class="form-control" name="is_active">
            <option value="true" ${payload.isActive ? "selected" : ""}>Active</option>
            <option value="false" ${payload.isActive ? "" : "selected"}>Inactive</option>
          </select>
        </div>
      </form>
    `;
  }

  function renderProjectForm(mode, payload) {
    const isAdd = mode === "add";
    return `
      <form id="entityForm" class="user-form-grid" method="POST" action="${isAdd ? config.createUrl : config.actionUrl}">
        <input type="hidden" name="csrfmiddlewaretoken" value="${config.csrfToken || ""}">
        ${isAdd ? '<input type="hidden" name="form_type" value="project">' : '<input type="hidden" name="action" value="edit">'}
        ${isAdd ? "" : `<input type="hidden" name="project_id" value="${payload.id}">`}
        <div class="form-field">
          <label>Project Code</label>
          <input class="form-control" name="code" value="${payload.code || ""}" required>
        </div>
        <div class="form-field">
          <label>Project Name</label>
          <input class="form-control" name="name" value="${payload.name || ""}" required>
        </div>
        <div class="form-field">
          <label>Domain</label>
          <select class="form-control" name="domain">
            <option value="Corporate" ${payload.domain === "Corporate" ? "selected" : ""}>Corporate</option>
            <option value="Non-Corporate" ${payload.domain === "Non-Corporate" ? "selected" : ""}>Non-Corporate</option>
          </select>
        </div>
        <div class="form-field">
          <label>Status</label>
          <select class="form-control" name="is_active">
            <option value="true" ${payload.isActive ? "selected" : ""}>Active</option>
            <option value="false" ${payload.isActive ? "" : "selected"}>Inactive</option>
          </select>
        </div>
      </form>
    `;
  }

  window.closePopup = closePopup;
  window.closeDeletePopup = closeDeletePopup;

  if (addBtn) {
    addBtn.addEventListener("click", function () {
      popup.style.display = "flex";
      popupTitle.innerText = isProjectPage ? "Add New Project" : "Add New Department";
      popupBody.innerHTML = isProjectPage
        ? renderProjectForm("add", { isActive: true, domain: "Corporate" })
        : renderDepartmentForm("add", { isActive: true });
    });
  }

  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      popup.style.display = "flex";
      popupTitle.innerText = isProjectPage ? "Edit Project" : "Edit Department";
      const payload = {
        id: this.dataset.id,
        code: this.dataset.code,
        name: this.dataset.name,
        isActive: this.dataset.isActive === "true",
        domain: this.dataset.domain,
      };
      popupBody.innerHTML = isProjectPage
        ? renderProjectForm("edit", payload)
        : renderDepartmentForm("edit", payload);
    });
  });

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      if (deleteEntityIdInput) {
        deleteEntityIdInput.value = this.dataset.id;
      }
      deletePopup.style.display = "flex";
    });
  });

  if (saveBtn) {
    saveBtn.addEventListener("click", function () {
      const form = document.getElementById("entityForm");
      if (form) {
        form.submit();
      }
    });
  }

  window.addEventListener("click", function (event) {
    if (event.target === popup) {
      closePopup();
    }
    if (event.target === deletePopup) {
      closeDeletePopup();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closePopup();
      closeDeletePopup();
    }
  });
});
