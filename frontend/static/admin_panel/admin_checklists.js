(() => {
  const cfg = window.checklistPageConfig;
  if (!cfg) return;

  const deletePopup = document.getElementById('deletePopup');
  const deleteChecklistIdInput = document.getElementById('deleteChecklistId');

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

  const form = document.getElementById('checklistForm');
  const builderRoot = document.getElementById('questionBuilderContainer');
  if (!form || !builderRoot) {
    window.onclick = (event) => {
      if (event.target === deletePopup) closeDeletePopup();
    };
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeDeletePopup();
    });
    return;
  }

  const els = {
    stateInput: document.getElementById('builderStateJson'),
    addQuestionBtn: document.getElementById('addQuestionBtn'),
    addSectionBtn: document.getElementById('addSectionBtn'),
    togglePreviewBtn: document.getElementById('togglePreviewBtn'),
    checklistIdInput: document.getElementById('checklistIdInput'),
    checklistIdDisplay: document.getElementById('checklistIdDisplay'),
    checklistTypeInput: document.getElementById('checklistTypeInput'),
    checklistTypesSource: document.getElementById('checklistTypesSource'),
    projectsInput: document.getElementById('projectsInput'),
    departmentsInput: document.getElementById('departmentsInput'),
    selectedTypesCsv: document.getElementById('selectedTypesCsv'),
    selectedProjectsCsv: document.getElementById('selectedProjectsCsv'),
    selectedDepartmentsCsv: document.getElementById('selectedDepartmentsCsv'),
    checklistNameDisplay: document.getElementById('checklistNameDisplay'),
    checklistBuilderTitleInput: document.getElementById('checklistBuilderTitleInput'),
    checklistMetaModal: document.getElementById('checklistMetaModal'),
    openChecklistMetaEditor: document.getElementById('openChecklistMetaEditor'),
    closeChecklistMetaModal: document.getElementById('closeChecklistMetaModal'),
    cancelChecklistMetaModal: document.getElementById('cancelChecklistMetaModal'),
    saveChecklistMetaModal: document.getElementById('saveChecklistMetaModal'),
    metaTypeList: document.getElementById('metaTypeList'),
    metaProjectList: document.getElementById('metaProjectList'),
    metaDepartmentList: document.getElementById('metaDepartmentList'),
  };

  const qTypeNode = document.getElementById('checklist-question-types');
  const qTypes = qTypeNode ? JSON.parse(qTypeNode.textContent).types : [];
  const optionTypes = new Set(['multiple_choice', 'checkbox', 'dropdown']);
  const typeIcons = {
    short_text: '📝',
    long_text: '📄',
    multiple_choice: '🔘',
    checkbox: '☑️',
    dropdown: '⬇️',
    file_upload: '📎',
    yes_no: '✅',
    date: '📅',
  };

  const uid = () => `tmp_${Math.random().toString(36).slice(2, 10)}`;
  const deepClone = (value) => JSON.parse(JSON.stringify(value));
  const escapeHtml = (value = '') => String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  const blankQuestion = () => ({ id: uid(), text: '', type: 'short_text', options: [], required: false, order: 1 });
  const blankSection = (index) => ({ id: uid(), title: `Section ${index}`, order: index, collapsed: false, questions: [blankQuestion()] });

  const initialBuilderData = JSON.parse(document.getElementById('checklist-builder-initial-data')?.textContent || '{"sections": []}');
  let state = Array.isArray(initialBuilderData.sections) && initialBuilderData.sections.length
    ? initialBuilderData
    : { sections: [blankSection(1)] };
  let previewMode = false;
  let dirty = false;

  const normalizeOrders = () => {
    state.sections.forEach((section, sectionIndex) => {
      section.order = sectionIndex + 1;
      section.questions = section.questions || [];
      section.questions.forEach((question, questionIndex) => {
        question.order = questionIndex + 1;
      });
    });
  };

  const persistState = () => {
    normalizeOrders();
    if (els.stateInput) els.stateInput.value = JSON.stringify(state);
  };

  const markDirty = () => {
    dirty = true;
    persistState();
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
    if (!els.checklistIdInput) return;
    if (!els.checklistIdInput.value) els.checklistIdInput.value = nextChecklistId();
    if (els.checklistIdDisplay) els.checklistIdDisplay.textContent = els.checklistIdInput.value || '-';
  };

  const renderCheckboxes = (target, sourceSelect) => {
    if (!target || !sourceSelect) return;
    target.innerHTML = [...sourceSelect.options].map((opt) =>
      `<label class="selection-item"><input type="checkbox" value="${escapeHtml(opt.value)}"> <span>${escapeHtml(opt.textContent)}</span></label>`).join('');
  };

  const syncCsvDisplay = () => {
    const selectedTypeIds = els.checklistTypeInput?.value ? els.checklistTypeInput.value.split(',').filter(Boolean) : [];
    const typeLabels = els.checklistTypesSource
      ? [...els.checklistTypesSource.options].filter((option) => selectedTypeIds.includes(option.value)).map((option) => option.textContent)
      : [];
    const projectLabels = els.projectsInput ? [...els.projectsInput.selectedOptions].map((o) => o.textContent) : [];
    const departmentLabels = els.departmentsInput ? [...els.departmentsInput.selectedOptions].map((o) => o.textContent) : [];

    if (els.selectedTypesCsv) els.selectedTypesCsv.textContent = typeLabels.length ? typeLabels.join(', ') : '-';
    if (els.selectedProjectsCsv) els.selectedProjectsCsv.textContent = projectLabels.length ? projectLabels.join(', ') : '-';
    if (els.selectedDepartmentsCsv) els.selectedDepartmentsCsv.textContent = departmentLabels.length ? departmentLabels.join(', ') : '-';
  };

  const openMetaModal = () => {
    ensureChecklistId();
    const selectedTypeIds = els.checklistTypeInput?.value ? els.checklistTypeInput.value.split(',').filter(Boolean) : [];
    [...(els.metaTypeList?.querySelectorAll('input[type="checkbox"]') || [])].forEach((input) => {
      input.checked = selectedTypeIds.includes(input.value);
    });
    [...(els.metaProjectList?.querySelectorAll('input[type="checkbox"]') || [])].forEach((input) => {
      const option = [...els.projectsInput.options].find((opt) => opt.value === input.value);
      input.checked = Boolean(option?.selected);
    });
    [...(els.metaDepartmentList?.querySelectorAll('input[type="checkbox"]') || [])].forEach((input) => {
      const option = [...els.departmentsInput.options].find((opt) => opt.value === input.value);
      input.checked = Boolean(option?.selected);
    });
    if (els.checklistMetaModal) els.checklistMetaModal.style.display = 'flex';
  };

  const closeMetaModal = () => {
    if (els.checklistMetaModal) els.checklistMetaModal.style.display = 'none';
  };

  const renderQuestionPreview = (question) => {
    const options = question.options || [];
    if (question.type === 'long_text') return '<textarea disabled placeholder="Long answer"></textarea>';
    if (question.type === 'multiple_choice') return options.map((option) => `<label class="preview-option"><input type="radio" disabled> ${escapeHtml(option)}</label>`).join('');
    if (question.type === 'checkbox') return options.map((option) => `<label class="preview-option"><input type="checkbox" disabled> ${escapeHtml(option)}</label>`).join('');
    if (question.type === 'dropdown') return `<select disabled><option>Select</option>${options.map((option) => `<option>${escapeHtml(option)}</option>`).join('')}</select>`;
    if (question.type === 'file_upload') return '<input type="file" disabled />';
    if (question.type === 'yes_no') return '<label class="preview-option"><input type="radio" disabled> Yes</label><label class="preview-option"><input type="radio" disabled> No</label>';
    if (question.type === 'date') return '<input type="date" disabled />';
    return '<input type="text" disabled placeholder="Short answer" />';
  };

  const renderQuestionEditor = (question, sectionIndex, questionIndex) => {
    const options = question.options || [];
    return `
      <article class="question-card" data-section-index="${sectionIndex}" data-question-index="${questionIndex}">
        <div class="question-card-header">
          <strong>${typeIcons[question.type] || '❔'} Question ${questionIndex + 1}</strong>
          <div class="question-tools">
            <button type="button" class="btn btn-edit" data-action="duplicate-question">Duplicate</button>
            <button type="button" class="btn btn-view" data-action="move-question-up">↑</button>
            <button type="button" class="btn btn-view" data-action="move-question-down">↓</button>
            <button type="button" class="btn btn-delete" data-action="delete-question">Delete</button>
          </div>
        </div>
        <div class="question-row">
          <input type="text" class="form-control q-text" placeholder="Question text" value="${escapeHtml(question.text)}" required>
          <select class="form-control q-type">
            ${qTypes.map((type) => `<option value="${escapeHtml(type.value)}" ${question.type === type.value ? 'selected' : ''}>${escapeHtml(type.label)}</option>`).join('')}
          </select>
          <label class="required-toggle"><input type="checkbox" class="q-required" ${question.required ? 'checked' : ''}> Required</label>
        </div>
        <div class="q-options-wrap" style="display:${optionTypes.has(question.type) ? 'block' : 'none'};margin-top:8px;">
          <div class="q-options-list">
            ${options.map((option, optionIndex) => `
              <div class="option-row" data-option-index="${optionIndex}">
                <input type="text" class="form-control q-option-input" placeholder="Option value" value="${escapeHtml(option)}">
                <button type="button" class="btn btn-delete" data-action="delete-option" data-option-index="${optionIndex}">Remove</button>
              </div>`).join('')}
          </div>
          <button type="button" class="btn btn-add" data-action="add-option">+ Add option</button>
        </div>
      </article>
    `;
  };

  const render = () => {
    persistState();
    builderRoot.innerHTML = state.sections.map((section, sectionIndex) => `
      <section class="section-card question-card" data-section-index="${sectionIndex}">
        <div class="question-card-header section-header">
          <div class="section-title-wrap">
            <strong>Section ${sectionIndex + 1}</strong>
            ${previewMode
              ? `<h4>${escapeHtml(section.title)}</h4>`
              : `<input type="text" class="form-control section-title" value="${escapeHtml(section.title)}" placeholder="Section title" required>`}
          </div>
          <div class="question-tools">
            <button type="button" class="btn btn-view" data-action="toggle-section">${section.collapsed ? 'Expand' : 'Collapse'}</button>
            <button type="button" class="btn btn-view" data-action="move-section-up">↑ Section</button>
            <button type="button" class="btn btn-view" data-action="move-section-down">↓ Section</button>
            <button type="button" class="btn btn-delete" data-action="delete-section">Delete</button>
          </div>
        </div>
        <div class="section-body ${section.collapsed ? 'hidden-section' : ''}">
          <div class="questions-wrap">
            ${(section.questions || []).map((question, questionIndex) => previewMode
              ? `<article class="question-card preview-card"><strong>${questionIndex + 1}. ${escapeHtml(question.text || 'Untitled question')}</strong>${question.required ? '<span class="required-mark"> *</span>' : ''}<div class="preview-control">${renderQuestionPreview(question)}</div></article>`
              : renderQuestionEditor(question, sectionIndex, questionIndex)).join('')}
          </div>
          ${previewMode ? '' : `<button type="button" class="btn btn-add" data-action="add-question-to-section">+ Add Question</button>`}
        </div>
      </section>
    `).join('');
  };

  const addQuestionToSection = (sectionIndex) => {
    const section = state.sections[sectionIndex];
    if (!section) return;
    section.questions.push(blankQuestion());
    markDirty();
    render();
  };

  els.addSectionBtn.onclick = () => {
    state.sections.push(blankSection(state.sections.length + 1));
    markDirty();
    render();
  };

  els.addQuestionBtn.onclick = () => {
    if (!state.sections.length) state.sections.push(blankSection(1));
    addQuestionToSection(state.sections.length - 1);
  };

  els.togglePreviewBtn.onclick = () => {
    previewMode = !previewMode;
    els.togglePreviewBtn.textContent = previewMode ? 'Edit Mode' : 'Preview Mode';
    render();
  };

  builderRoot.addEventListener('click', (event) => {
    const btn = event.target.closest('button[data-action]');
    if (!btn || previewMode && btn.dataset.action !== 'toggle-section') return;
    const sectionCard = event.target.closest('.section-card');
    const questionCard = event.target.closest('.question-card[data-question-index]');
    const sectionIndex = Number(sectionCard?.dataset.sectionIndex);
    const questionIndex = Number(questionCard?.dataset.questionIndex);
    const action = btn.dataset.action;

    if (action === 'add-question-to-section') addQuestionToSection(sectionIndex);
    if (action === 'toggle-section') { state.sections[sectionIndex].collapsed = !state.sections[sectionIndex].collapsed; render(); }
    if (action === 'move-section-up' && sectionIndex > 0) { [state.sections[sectionIndex - 1], state.sections[sectionIndex]] = [state.sections[sectionIndex], state.sections[sectionIndex - 1]]; markDirty(); render(); }
    if (action === 'move-section-down' && sectionIndex < state.sections.length - 1) { [state.sections[sectionIndex + 1], state.sections[sectionIndex]] = [state.sections[sectionIndex], state.sections[sectionIndex + 1]]; markDirty(); render(); }
    if (action === 'delete-section') {
      if (state.sections.length === 1) {
        alert('At least one section is required.');
      } else if (confirm('Delete this section and all its questions?')) {
        state.sections.splice(sectionIndex, 1);
        markDirty();
        render();
      }
    }
    if (action === 'duplicate-question') { const clone = deepClone(state.sections[sectionIndex].questions[questionIndex]); clone.id = uid(); state.sections[sectionIndex].questions.splice(questionIndex + 1, 0, clone); markDirty(); render(); }
    if (action === 'move-question-up' && questionIndex > 0) { const questions = state.sections[sectionIndex].questions; [questions[questionIndex - 1], questions[questionIndex]] = [questions[questionIndex], questions[questionIndex - 1]]; markDirty(); render(); }
    if (action === 'move-question-down' && questionIndex < state.sections[sectionIndex].questions.length - 1) { const questions = state.sections[sectionIndex].questions; [questions[questionIndex + 1], questions[questionIndex]] = [questions[questionIndex], questions[questionIndex + 1]]; markDirty(); render(); }
    if (action === 'delete-question') {
      if (state.sections[sectionIndex].questions.length === 1) {
        alert('Each section must contain at least one question.');
      } else if (confirm('Delete this question?')) {
        state.sections[sectionIndex].questions.splice(questionIndex, 1);
        markDirty();
        render();
      }
    }
    if (action === 'add-option') { state.sections[sectionIndex].questions[questionIndex].options.push(''); markDirty(); render(); }
    if (action === 'delete-option') { state.sections[sectionIndex].questions[questionIndex].options.splice(Number(btn.dataset.optionIndex), 1); markDirty(); render(); }
  });

  builderRoot.addEventListener('input', (event) => {
    const sectionCard = event.target.closest('.section-card');
    if (!sectionCard) return;
    const sectionIndex = Number(sectionCard.dataset.sectionIndex);
    const questionCard = event.target.closest('.question-card[data-question-index]');
    const questionIndex = questionCard ? Number(questionCard.dataset.questionIndex) : null;

    if (event.target.classList.contains('section-title')) state.sections[sectionIndex].title = event.target.value;
    if (event.target.classList.contains('q-text')) state.sections[sectionIndex].questions[questionIndex].text = event.target.value;
    if (event.target.classList.contains('q-option-input')) {
      const optionIndex = Number(event.target.closest('.option-row').dataset.optionIndex);
      state.sections[sectionIndex].questions[questionIndex].options[optionIndex] = event.target.value;
    }
    markDirty();
  });

  builderRoot.addEventListener('change', (event) => {
    const sectionCard = event.target.closest('.section-card');
    const questionCard = event.target.closest('.question-card[data-question-index]');
    if (!sectionCard || !questionCard) return;
    const sectionIndex = Number(sectionCard.dataset.sectionIndex);
    const questionIndex = Number(questionCard.dataset.questionIndex);

    if (event.target.classList.contains('q-type')) {
      const question = state.sections[sectionIndex].questions[questionIndex];
      question.type = event.target.value;
      if (!optionTypes.has(question.type)) question.options = [];
      markDirty();
      render();
    }
    if (event.target.classList.contains('q-required')) {
      state.sections[sectionIndex].questions[questionIndex].required = event.target.checked;
      markDirty();
    }
  });

  const filterSelectionList = (containerId, term) => {
    const termValue = (term || '').toLowerCase();
    const container = document.getElementById(containerId);
    if (!container) return;
    [...container.querySelectorAll('.selection-item')].forEach((item) => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(termValue) ? '' : 'none';
    });
  };

  document.getElementById('metaTypeSearch')?.addEventListener('input', (event) => filterSelectionList('metaTypeList', event.target.value));
  document.getElementById('metaProjectSearch')?.addEventListener('input', (event) => filterSelectionList('metaProjectList', event.target.value));
  document.getElementById('metaDepartmentSearch')?.addEventListener('input', (event) => filterSelectionList('metaDepartmentList', event.target.value));
  document.querySelectorAll('.selection-tools .mini-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const container = document.getElementById(btn.dataset.target);
      if (!container) return;
      [...container.querySelectorAll('input[type="checkbox"]')].forEach((input) => {
        input.checked = btn.dataset.action === 'all';
      });
    });
  });

  if (els.openChecklistMetaEditor) els.openChecklistMetaEditor.onclick = openMetaModal;
  if (els.closeChecklistMetaModal) els.closeChecklistMetaModal.onclick = closeMetaModal;
  if (els.cancelChecklistMetaModal) els.cancelChecklistMetaModal.onclick = closeMetaModal;
  if (els.saveChecklistMetaModal) {
    els.saveChecklistMetaModal.onclick = () => {
      const selectedTypeIds = [...els.metaTypeList.querySelectorAll('input:checked')].map((input) => input.value);
      els.checklistTypeInput.value = selectedTypeIds[0] || '';
      [...els.metaTypeList.querySelectorAll('input[type="checkbox"]')].forEach((input) => {
        input.checked = selectedTypeIds.length ? input.value === selectedTypeIds[0] : false;
      });
      [...els.metaProjectList.querySelectorAll('input')].forEach((input) => {
        const option = [...els.projectsInput.options].find((opt) => opt.value === input.value);
        if (option) option.selected = input.checked;
      });
      [...els.metaDepartmentList.querySelectorAll('input')].forEach((input) => {
        const option = [...els.departmentsInput.options].find((opt) => opt.value === input.value);
        if (option) option.selected = input.checked;
      });
      syncCsvDisplay();
      closeMetaModal();
    };
  }

  window.onclick = (event) => {
    if (event.target === deletePopup) closeDeletePopup();
    if (event.target === els.checklistMetaModal) closeMetaModal();
  };
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeDeletePopup();
      closeMetaModal();
    }
  });

  if (els.checklistBuilderTitleInput) {
    const syncName = () => {
      if (els.checklistNameDisplay) els.checklistNameDisplay.textContent = els.checklistBuilderTitleInput.value.trim() || '-';
    };
    els.checklistBuilderTitleInput.addEventListener('input', syncName);
    syncName();
  }

  form.onsubmit = async (event) => {
    event.preventDefault();
    persistState();
    const formData = new FormData(form);
    formData.append('csrfmiddlewaretoken', cfg.csrfToken);
    const res = await fetch(cfg.actionUrl, {
      method: 'POST',
      body: formData,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    let data = {};
    try { data = await res.json(); } catch (error) { data = {}; }
    if (!res.ok) {
      alert((data.errors || ['Unable to save checklist. Please verify the highlighted checklist details and builder questions.']).join('\n'));
      return;
    }
    dirty = false;
    window.location.href = '/admin-panel/checklists/';
  };

  window.addEventListener('beforeunload', (event) => {
    if (!dirty) return;
    event.preventDefault();
    event.returnValue = '';
  });

  ensureChecklistId();
  renderCheckboxes(els.metaTypeList, els.checklistTypesSource);
  renderCheckboxes(els.metaProjectList, els.projectsInput);
  renderCheckboxes(els.metaDepartmentList, els.departmentsInput);
  syncCsvDisplay();
  render();
})();
