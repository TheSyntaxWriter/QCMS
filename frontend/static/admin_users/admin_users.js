document.addEventListener("DOMContentLoaded", function () {
  // ================= FILTER =================
  window.applyFilter = function () {
    let search = document.getElementById("search").value;
    let department = document.getElementById("department").value;
    let project = document.getElementById("project").value;
    let status = document.getElementById("status").value;

    let url = "?";

    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (department) url += `department=${department}&`;
    if (project) url += `project=${project}&`;
    if (status) url += `status=${status}&`;

    window.location.href = url;
  };

  // 🔥 REUSE FILTER DROPDOWN DATA
  function getDeptOptions() {
    return document
      .getElementById("department")
      .innerHTML.replace('<option value="">Dept</option>', "");
  }

  function getProjOptions() {
    return document
      .getElementById("project")
      .innerHTML.replace('<option value="">Project</option>', "");
  }

  // ================= ADD USER =================
  document.getElementById("addUserBtn").onclick = function () {
    document.getElementById("popup").style.display = "flex";
    document.getElementById("popup-title").innerText = "Add User";
    document.getElementById("saveBtn").style.display = "inline-block";

    document.getElementById("popup-body").innerHTML = `
      <form id="userForm" method="POST" action="/admin-create/">

        <input type="hidden" name="form_type" value="user">

        <label>Username</label>
        <input name="username" required>

        <label>Password</label>
        <input type="password" name="password" required>

        <label>First Name</label>
        <input name="first_name">

        <label>Last Name</label>
        <input name="last_name">

        <label>Role</label>
        <select name="role">
          <option>User</option>
          <option>HOD</option>
          <option>Management</option>
          <option>Admin</option>
        </select>

        <label>Department</label>
        <select name="department">
          ${getDeptOptions()}
        </select>

        <label>Project</label>
        <select name="project">
          ${getProjOptions()}
        </select>
      </form>
    `;
  };

  // ================= VIEW =================
  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.onclick = function () {
      document.getElementById("popup").style.display = "flex";
      document.getElementById("popup-title").innerText = "User Details";
      document.getElementById("saveBtn").style.display = "none";

      let status = this.dataset.status == "True" ? "Active" : "Inactive";

      document.getElementById("popup-body").innerHTML = `
        <p><b>Username:</b> ${this.dataset.username}</p>
        <p><b>Name:</b> ${this.dataset.first} ${this.dataset.last}</p>
        <p><b>Role:</b> ${this.dataset.role}</p>
        <p><b>Department:</b> ${this.dataset.dept}</p>
        <p><b>Project:</b> ${this.dataset.project} (${this.dataset.domain})</p>
        <p><b>Status:</b> ${status}</p>
      `;
    };
  });

  // ================= EDIT =================
  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.onclick = function () {
      document.getElementById("popup").style.display = "flex";
      document.getElementById("popup-title").innerText = "Edit User";
      document.getElementById("saveBtn").style.display = "inline-block";

      document.getElementById("popup-body").innerHTML = `
        <form id="userForm" method="POST" action="/admin-user-action/">

          <input type="hidden" name="edit_id" value="${this.dataset.id}">

          <label>Username</label>
          <input name="username" value="${this.dataset.username}">

          <label>First Name</label>
          <input name="first_name" value="${this.dataset.first}">

          <label>Last Name</label>
          <input name="last_name" value="${this.dataset.last}">

          <label>Role</label>
          <select name="role">
            <option ${this.dataset.role == "User" ? "selected" : ""}>User</option>
            <option ${this.dataset.role == "HOD" ? "selected" : ""}>HOD</option>
            <option ${this.dataset.role == "Management" ? "selected" : ""}>Management</option>
            <option ${this.dataset.role == "Admin" ? "selected" : ""}>Admin</option>
          </select>

          <label>Department</label>
          <select name="department" id="editDept">
            ${getDeptOptions()}
          </select>

          <label>Project</label>
          <select name="project" id="editProj">
            ${getProjOptions()}
          </select>
        </form>
      `;

      // 🔥 SET SELECTED VALUE
      document.getElementById("editDept").value = this.dataset.deptId;
      document.getElementById("editProj").value = this.dataset.projectId;
    };
  });

  // ================= SAVE =================
  document.getElementById("saveBtn").onclick = function () {
    let form = document.getElementById("userForm");
    if (form) form.submit();
  };

  // ================= CLOSE =================
  window.closePopup = function () {
    document.getElementById("popup").style.display = "none";
  };

  window.onclick = function (e) {
    if (e.target.id === "popup") closePopup();
  };

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closePopup();
  });
});
