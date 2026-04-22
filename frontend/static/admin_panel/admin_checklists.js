(() => {
  const cfg = window.checklistPageConfig;
  if (!cfg) return;
  const modal = document.getElementById('checklistBuilderModal');
  const openBtn = document.getElementById('openChecklistBuilder');
  const closeBtn = document.getElementById('closeChecklistBuilder');
  const container = document.getElementById('questionBuilderContainer');
  const addQuestionBtn = document.getElementById('addQuestionBtn');
  const addSectionBtn = document.getElementById('addSectionBtn');
  const form = document.getElementById('checklistForm');
  const questionsJson = document.getElementById('questionsJson');
  const deletePopup = document.getElementById('deletePopup');
  const deleteChecklistIdInput = document.getElementById('deleteChecklistId');
  let sectionName = 'Section 1';

  const qTypes = JSON.parse(document.getElementById('checklist-question-types').textContent).types;

  const questionNode = (section = sectionName) => {
    const wrap = document.createElement('div');
    wrap.className = 'question-item';
    wrap.innerHTML = `
      <div class="question-row">
        <input type="text" class="q-text" placeholder="Question text" required>
        <select class="q-type">${qTypes.map(t => `<option value="${t.value}">${t.label}</option>`).join('')}</select>
        <input type="text" class="q-options" placeholder="Options (comma separated)">
        <label><input type="checkbox" class="q-required"> Required</label>
      </div>
      <div style="margin-top:8px;display:flex;gap:8px;">
        <button type="button" class="btn btn-edit duplicate-q">Duplicate</button>
        <button type="button" class="btn btn-delete delete-q">Delete</button>
        <button type="button" class="btn btn-view move-up">↑</button>
        <button type="button" class="btn btn-view move-down">↓</button>
      </div>
      <input type="hidden" class="q-section" value="${section}">
    `;

    wrap.querySelector('.duplicate-q').onclick = () => container.insertBefore(questionNode(section), wrap.nextSibling);
    wrap.querySelector('.delete-q').onclick = () => wrap.remove();
    wrap.querySelector('.move-up').onclick = () => wrap.previousElementSibling && container.insertBefore(wrap, wrap.previousElementSibling);
    wrap.querySelector('.move-down').onclick = () => wrap.nextElementSibling && container.insertBefore(wrap.nextElementSibling, wrap);
    return wrap;
  };

  addQuestionBtn.onclick = () => container.appendChild(questionNode());
  addSectionBtn.onclick = () => { sectionName = `Section ${container.querySelectorAll('.question-item').length + 1}`; container.appendChild(questionNode(sectionName)); };

  openBtn.onclick = () => modal.classList.add('is-open');
  closeBtn.onclick = () => modal.classList.remove('is-open');

  function closeDeletePopup() {
    if (deletePopup) {
      deletePopup.style.display = 'none';
    }
    if (deleteChecklistIdInput) {
      deleteChecklistIdInput.value = '';
    }
  }
  window.closeDeletePopup = closeDeletePopup;

  document.querySelectorAll('.checklist-action').forEach(btn => {
    btn.onclick = async () => {
      const action = btn.dataset.action;
      if (action === 'view' || action === 'edit') return;
    }
  });

  document.querySelectorAll('.delete-btn').forEach((btn) => {
    btn.onclick = () => {
      if (deleteChecklistIdInput) {
        deleteChecklistIdInput.value = btn.dataset.checklistId;
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
  };

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      closeDeletePopup();
    }
  });

  form.onsubmit = async (event) => {
    event.preventDefault();
    const questionPayload = [...container.querySelectorAll('.question-item')].map((node, index) => ({
      question_text: node.querySelector('.q-text').value,
      type: node.querySelector('.q-type').value,
      options: (node.querySelector('.q-options').value || '').split(',').map(s => s.trim()).filter(Boolean),
      required: node.querySelector('.q-required').checked,
      section: node.querySelector('.q-section').value,
      order: index + 1,
    }));
    questionsJson.value = JSON.stringify(questionPayload);
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', cfg.csrfToken);
    await fetch(cfg.actionUrl, { method: 'POST', body: formData });
    location.reload();
  };
})();
