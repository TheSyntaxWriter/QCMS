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

  const checklistIdInput = document.getElementById('checklistIdInput');
  const checklistIdDisplay = document.getElementById('checklistIdDisplay');
  const checklistTypeInput = document.getElementById('checklistTypeInput');
  const checklistTypesSource = document.getElementById('checklistTypesSource');
  const projectsInput = document.getElementById('projectsInput');
  const departmentsInput = document.getElementById('departmentsInput');

  const selectedTypesCsv = document.getElementById('selectedTypesCsv');
  const selectedProjectsCsv = document.getElementById('selectedProjectsCsv');
  const selectedDepartmentsCsv = document.getElementById('selectedDepartmentsCsv');
  const checklistNameDisplay = document.getElementById('checklistNameDisplay');
  const checklistBuilderTitleInput = document.getElementById('checklistBuilderTitleInput');

  const checklistMetaModal = document.getElementById('checklistMetaModal');
  const openChecklistMetaEditor = document.getElementById('openChecklistMetaEditor');
  const closeChecklistMetaModal = document.getElementById('closeChecklistMetaModal');
  const cancelChecklistMetaModal = document.getElementById('cancelChecklistMetaModal');
  const saveChecklistMetaModal = document.getElementById('saveChecklistMetaModal');
  const metaTypeList = document.getElementById('metaTypeList');
  const metaProjectList = document.getElementById('metaProjectList');
  const metaDepartmentList = document.getElementById('metaDepartmentList');

  let sectionName = 'Section 1';
  const state = { checklist: { id: '', name: '', types: [], projects: [], departments: [] } };

  const qTypeNode = document.getElementById('checklist-question-types');
  const qTypes = qTypeNode ? JSON.parse(qTypeNode.textContent).types : [];
  const optionTypes = new Set(['checkbox', 'dropdown']);
  const checkpointType = 'checkpoint';

  const checkpointPreview = `
    <div class="checkpoint-preview">
      <label><input type="checkbox" disabled> Mark as Completed</label>
      <input type="file" disabled>
      <textarea rows="2" disabled placeholder="Remarks (optional)"></textarea>
    </div>
  `;

  const createOptionField = (value = '') => {
    const row = document.createElement('div');
    row.className = 'option-row';
    row.innerHTML = `
      <input type="text" class="q-option-input" placeholder="Option value" value="${value.replace(/"/g, '&quot;')}">
      <button type="button" class="btn btn-delete remove-option">Remove</button>
    `;
    row.querySelector('.remove-option').onclick = () => row.remove();
    return row;
  };

  const syncTypeVisibility = (wrap) => {
    const type = wrap.querySelector('.q-type').value;
    const optionsWrap = wrap.querySelector('.q-options-wrap');
    const checkpointWrap = wrap.querySelector('.checkpoint-preview-wrap');
    optionsWrap.style.display = optionTypes.has(type) ? 'block' : 'none';
    checkpointWrap.style.display = type === checkpointType ? 'block' : 'none';
  };

  const questionNode = (section = sectionName) => {
    const wrap = document.createElement('div');
    wrap.className = 'question-item question-card';
    wrap.innerHTML = `
      <div class="question-card-header">
        <strong>Question</strong>
        <div style="display:flex;gap:8px;">
          <button type="button" class="btn btn-edit duplicate-q">Duplicate</button>
          <button type="button" class="btn btn-view move-up">↑</button>
          <button type="button" class="btn btn-view move-down">↓</button>
          <button type="button" class="btn btn-delete delete-q">Delete</button>
        </div>
      </div>
      <div class="question-row">
        <input type="text" class="q-text" placeholder="Question text" required>
        <select class="q-type">${qTypes.map(t => `<option value="${t.value}">${t.label}</option>`).join('')}</select>
        <label><input type="checkbox" class="q-required"> Required</label>
      </div>
      <div class="q-options-wrap" style="display:none;margin-top:8px;">
        <div class="q-options-list"></div>
        <button type="button" class="btn btn-add add-option">+ Add option</button>
      </div>
      <div class="checkpoint-preview-wrap" style="display:none;margin-top:8px;">${checkpointPreview}</div>
      <input type="hidden" class="q-section" value="${section}">
    `;

    wrap.querySelector('.duplicate-q').onclick = () => container.insertBefore(questionNode(section), wrap.nextSibling);
    wrap.querySelector('.delete-q').onclick = () => wrap.remove();
    wrap.querySelector('.move-up').onclick = () => wrap.previousElementSibling && container.insertBefore(wrap, wrap.previousElementSibling);
    wrap.querySelector('.move-down').onclick = () => wrap.nextElementSibling && container.insertBefore(wrap.nextElementSibling, wrap);

    const optionsList = wrap.querySelector('.q-options-list');
    wrap.querySelector('.add-option').onclick = () => optionsList.appendChild(createOptionField());

    const typeSelect = wrap.querySelector('.q-type');
    typeSelect.onchange = () => syncTypeVisibility(wrap);
    syncTypeVisibility(wrap);
    return wrap;
  };

  const nextChecklistId = () => {
    const ids = [...document.querySelectorAll('#checklistBody tr td:first-child')]
      .map((cell) => (cell.textContent || '').trim())
      .filter((value) => /^CL\d+$/i.test(value))
      .map((value) => parseInt(value.replace(/\D/g, ''), 10));
    const next = (ids.length ? Math.max(...ids) : 0) + 1;
    return `CL${String(next).padStart(2, '0')}`;
  };
  const ensureChecklistId = () => {
    if (!checklistIdInput) return;
    if (!checklistIdInput.value) {
      checklistIdInput.value = nextChecklistId();
    }
    if (checklistIdDisplay) {
      checklistIdDisplay.textContent = checklistIdInput.value || '-';
    }
  };

  const renderCheckboxes = (target, sourceSelect) => {
    if (!target || !sourceSelect) return;
    target.innerHTML = [...sourceSelect.options].map((opt) =>
      `<label class="selection-item"><input type="checkbox" value="${opt.value}"> <span>${opt.textContent}</span></label>`).join('');
  };

  const syncCsvDisplay = () => {
    const selectedTypeIds = checklistTypeInput?.value ? checklistTypeInput.value.split(',').filter(Boolean) : [];
    const typeLabels = checklistTypesSource
      ? [...checklistTypesSource.options].filter((option) => selectedTypeIds.includes(option.value)).map((option) => option.textContent)
      : [];
    const projectLabels = projectsInput ? [...projectsInput.selectedOptions].map((o) => o.textContent) : [];
    const departmentLabels = departmentsInput ? [...departmentsInput.selectedOptions].map((o) => o.textContent) : [];

    selectedTypesCsv.textContent = typeLabels.length ? typeLabels.join(', ') : '-';
    selectedProjectsCsv.textContent = projectLabels.length ? projectLabels.join(', ') : '-';
    selectedDepartmentsCsv.textContent = departmentLabels.length ? departmentLabels.join(', ') : '-';
    state.checklist.types = selectedTypeIds;
    state.checklist.projects = [...projectsInput.selectedOptions].map((o) => o.value);
    state.checklist.departments = [...departmentsInput.selectedOptions].map((o) => o.value);
  };

  const openMetaModal = () => {
    ensureChecklistId();
    const selectedTypeIds = checklistTypeInput?.value ? checklistTypeInput.value.split(',').filter(Boolean) : [];
    [...metaTypeList.querySelectorAll('input[type="checkbox"]')].forEach((input) => {
      input.checked = selectedTypeIds.includes(input.value);
    });
    [...metaProjectList.querySelectorAll('input[type="checkbox"]')].forEach((input) => {
      const option = [...projectsInput.options].find((opt) => opt.value === input.value);
      input.checked = Boolean(option?.selected);
    });
    [...metaDepartmentList.querySelectorAll('input[type="checkbox"]')].forEach((input) => {
      const option = [...departmentsInput.options].find((opt) => opt.value === input.value);
      input.checked = Boolean(option?.selected);
    });
    if (checklistMetaModal) checklistMetaModal.style.display = 'flex';
  };
  const closeMetaModal = () => {
    if (checklistMetaModal) checklistMetaModal.style.display = 'none';
  };

  if (addQuestionBtn && container) addQuestionBtn.onclick = () => container.appendChild(questionNode());
  if (addSectionBtn && container) addSectionBtn.onclick = () => { sectionName = `Section ${container.querySelectorAll('.question-item').length + 1}`; container.appendChild(questionNode(sectionName)); };

  if (openBtn && modal) {
    openBtn.onclick = () => {
      ensureChecklistId();
      syncCsvDisplay();
      modal.classList.add('is-open');
    };
  }
  if (closeBtn && modal) closeBtn.onclick = () => modal.classList.remove('is-open');

  renderCheckboxes(metaTypeList, checklistTypesSource);
  renderCheckboxes(metaProjectList, projectsInput);
  renderCheckboxes(metaDepartmentList, departmentsInput);

  if (openChecklistMetaEditor) openChecklistMetaEditor.onclick = openMetaModal;
  document.addEventListener('click', (event) => {
    const editBtn = event.target.closest('#openChecklistMetaEditor');
    if (editBtn) {
      event.preventDefault();
      openMetaModal();
    }
  });
  if (closeChecklistMetaModal) closeChecklistMetaModal.onclick = closeMetaModal;
  if (cancelChecklistMetaModal) cancelChecklistMetaModal.onclick = closeMetaModal;

  if (saveChecklistMetaModal) {
    saveChecklistMetaModal.onclick = () => {
      const selectedTypeIds = [...metaTypeList.querySelectorAll('input:checked')].map((input) => input.value);
      checklistTypeInput.value = selectedTypeIds.join(',');
      [...metaProjectList.querySelectorAll('input')].forEach((input) => {
        const option = [...projectsInput.options].find((opt) => opt.value === input.value);
        if (option) option.selected = input.checked;
      });
      [...metaDepartmentList.querySelectorAll('input')].forEach((input) => {
        const option = [...departmentsInput.options].find((opt) => opt.value === input.value);
        if (option) option.selected = input.checked;
      });
      syncCsvDisplay();
      closeMetaModal();
    };
  }
  const filterSelectionList = (containerId, term) => {
    const termValue = (term || '').toLowerCase();
    const container = document.getElementById(containerId);
    if (!container) return;
    [...container.querySelectorAll('.selection-item')].forEach((item) => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(termValue) ? '' : 'none';
    });
  };
  document.getElementById('metaTypeSearch')?.addEventListener('input', (e) => filterSelectionList('metaTypeList', e.target.value));
  document.getElementById('metaProjectSearch')?.addEventListener('input', (e) => filterSelectionList('metaProjectList', e.target.value));
  document.getElementById('metaDepartmentSearch')?.addEventListener('input', (e) => filterSelectionList('metaDepartmentList', e.target.value));
  document.querySelectorAll('.selection-tools .mini-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const container = document.getElementById(btn.dataset.target);
      if (!container) return;
      [...container.querySelectorAll('input[type=\"checkbox\"]')].forEach((input) => {
        input.checked = btn.dataset.action === 'all';
      });
    });
  });

  function closeDeletePopup() {
    if (deletePopup) deletePopup.style.display = 'none';
    if (deleteChecklistIdInput) deleteChecklistIdInput.value = '';
  }
  window.closeDeletePopup = closeDeletePopup;

  document.querySelectorAll('.delete-btn').forEach((btn) => {
    btn.onclick = () => {
      if (deleteChecklistIdInput) deleteChecklistIdInput.value = btn.dataset.checklistId;
      if (deletePopup) deletePopup.style.display = 'flex';
    };
  });

  window.onclick = function (event) {
    if (event.target === deletePopup) closeDeletePopup();
    if (event.target === checklistMetaModal) closeMetaModal();
  };

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      closeDeletePopup();
      closeMetaModal();
    }
  });
  ensureChecklistId();
  syncCsvDisplay();
  state.checklist.id = checklistIdInput?.value || '';
  if (checklistBuilderTitleInput) {
    const syncName = () => {
      state.checklist.name = checklistBuilderTitleInput.value.trim();
      if (checklistNameDisplay) checklistNameDisplay.textContent = state.checklist.name || '-';
    };
    checklistBuilderTitleInput.addEventListener('input', syncName);
    syncName();
  }

  if (container) {
    const initialBuilderData = JSON.parse(document.getElementById('checklist-builder-initial-data')?.textContent || '{"questions": []}');
    if (Array.isArray(initialBuilderData.questions) && initialBuilderData.questions.length) {
      initialBuilderData.questions.forEach((question) => {
        const node = questionNode(question.section || sectionName);
        node.querySelector('.q-text').value = question.question_text || '';
        node.querySelector('.q-type').value = question.type || 'text';
        node.querySelector('.q-required').checked = Boolean(question.required);
        syncTypeVisibility(node);
        if (optionTypes.has(question.type) && Array.isArray(question.options)) {
          const list = node.querySelector('.q-options-list');
          question.options.forEach((opt) => list.appendChild(createOptionField(String(opt))));
        }
        container.appendChild(node);
      });
    }
  }

  if (form) form.onsubmit = async (event) => {
    event.preventDefault();
    const questionPayload = [...container.querySelectorAll('.question-item')].map((node, index) => {
      const type = node.querySelector('.q-type').value;
      const options = optionTypes.has(type)
        ? [...node.querySelectorAll('.q-option-input')].map((input) => input.value.trim()).filter(Boolean)
        : [];
      return {
        question_text: node.querySelector('.q-text').value,
        type,
        options,
        required: node.querySelector('.q-required').checked,
        section: node.querySelector('.q-section').value,
        order: index + 1,
      };
    });
    questionsJson.value = JSON.stringify(questionPayload);
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', cfg.csrfToken);
    const res = await fetch(cfg.actionUrl, { method: 'POST', body: formData });
    if (!res.ok) return;
    if (window.location.pathname.includes('/admin-panel/checklists/create/')) {
      window.location.href = '/admin-panel/checklists/';
      return;
    }
    location.reload();
  };
})();
