(() => {
  const cfg = window.checklistBuilderConfig;
  if (!cfg) return;

  const allowedTypes = new Set(['short_text','long_text','multiple_choice','checkbox','dropdown','file_upload','yes_no','date']);
  const optionTypes = new Set(['multiple_choice','checkbox','dropdown']);
  const typeIcons = {
    short_text: '📝', long_text: '📄', multiple_choice: '🔘', checkbox: '☑️', dropdown: '⬇️', file_upload: '📎', yes_no: '✅', date: '📅',
  };

  const els = {
    stateInput: document.getElementById('builderStateJson'),
    root: document.getElementById('builderRoot'),
    addSection: document.getElementById('addSectionBtn'),
    previewToggle: document.getElementById('togglePreviewBtn'),
    form: document.getElementById('checklistForm'),
    checklistName: document.getElementById('checklistNameInput'),
    checklistIdDisplay: document.getElementById('checklistIdDisplay'),
    checklistTypeInput: document.getElementById('checklistTypeInput'),
    checklistTypesSource: document.getElementById('checklistTypesSource'),
    projectsInput: document.getElementById('projectsInput'),
    departmentsInput: document.getElementById('departmentsInput'),
    selectedTypesCsv: document.getElementById('selectedTypesCsv'),
    selectedProjectsCsv: document.getElementById('selectedProjectsCsv'),
    selectedDepartmentsCsv: document.getElementById('selectedDepartmentsCsv'),
    checklistMetaModal: document.getElementById('checklistMetaModal'),
    openChecklistMetaEditor: document.getElementById('openChecklistMetaEditor'),
    closeChecklistMetaModal: document.getElementById('closeChecklistMetaModal'),
    cancelChecklistMetaModal: document.getElementById('cancelChecklistMetaModal'),
    saveChecklistMetaModal: document.getElementById('saveChecklistMetaModal'),
    metaTypeList: document.getElementById('metaTypeList'),
    metaProjectList: document.getElementById('metaProjectList'),
    metaDepartmentList: document.getElementById('metaDepartmentList'),
  };

  const uid = () => `tmp_${Math.random().toString(36).slice(2, 10)}`;
  const deepClone = (v) => JSON.parse(JSON.stringify(v));

  let state = { sections: [] };
  let previewMode = false;
  let dirty = false;

  const markDirty = () => { dirty = true; };

  const setState = (nextState) => {
    state = nextState;
    els.stateInput.value = JSON.stringify(state);
    render();
  };


  const nextChecklistId = () => {
    const ids = [...document.querySelectorAll('#checklistBody tr td:first-child')]
      .map((cell) => (cell.textContent || '').trim())
      .filter((value) => /^CL\d+$/i.test(value))
      .map((value) => parseInt(value.replace(/\D/g, ''), 10));
    const next = (ids.length ? Math.max(...ids) : 0) + 1;
    return `CL${String(next).padStart(2, '0')}`;
  };

  const renderCheckboxes = (target, sourceSelect) => {
    if (!target || !sourceSelect) return;
    target.innerHTML = [...sourceSelect.options].map((opt) =>
      `<label class="selection-item"><input type="checkbox" value="${opt.value}"> <span>${opt.textContent}</span></label>`).join('');
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

  const initial = JSON.parse(document.getElementById('builder-initial-state')?.textContent || '{"sections": []}');
  if (initial.sections?.length) {
    state = initial;
  } else {
    state = { sections: [{ id: uid(), title: 'Section 1', order: 1, collapsed: false, questions: [] }] };
  }

  const renderQuestionEditor = (q, si, qi) => `
    <div class="question-card" data-sindex="${si}" data-qindex="${qi}" draggable="true">
      <div class="question-top-row"><span>${typeIcons[q.type] || '❓'} Question ${qi + 1}</span>
        <div class="question-actions">
          <button type="button" class="btn btn-view" data-action="dup-question">Duplicate</button>
          <button type="button" class="btn btn-delete" data-action="del-question">Delete</button>
        </div>
      </div>
      <input class="q-text" type="text" value="${(q.text || '').replace(/"/g, '&quot;')}" placeholder="Question text" />
      <div class="question-meta">
        <select class="q-type">
          ${[...allowedTypes].map(t => `<option value="${t}" ${q.type===t?'selected':''}>${t.replace('_',' ')}</option>`).join('')}
        </select>
        <label><input type="checkbox" class="q-required" ${q.required?'checked':''}> Required</label>
      </div>
      <div class="q-options ${optionTypes.has(q.type) ? '' : 'hidden'}">
        ${(q.options || []).map((opt, oi) => `<div class="option-row"><input class="q-option" data-oi="${oi}" type="text" value="${String(opt).replace(/"/g, '&quot;')}" /><button type="button" class="btn btn-delete" data-action="del-option" data-oi="${oi}">×</button></div>`).join('')}
        <button type="button" class="btn btn-add" data-action="add-option">+ Add option</button>
      </div>
    </div>`;

  const renderQuestionPreview = (q) => {
    if (q.type === 'long_text') return '<textarea disabled placeholder="Long answer"></textarea>';
    if (q.type === 'multiple_choice') return (q.options || []).map(o => `<label><input type="radio" disabled> ${o}</label>`).join('');
    if (q.type === 'checkbox') return (q.options || []).map(o => `<label><input type="checkbox" disabled> ${o}</label>`).join('');
    if (q.type === 'dropdown') return `<select disabled>${(q.options||[]).map(o => `<option>${o}</option>`).join('')}</select>`;
    if (q.type === 'file_upload') return '<input type="file" disabled />';
    if (q.type === 'yes_no') return '<label><input type="radio" disabled> Yes</label> <label><input type="radio" disabled> No</label>';
    if (q.type === 'date') return '<input type="date" disabled />';
    return '<input type="text" disabled placeholder="Short answer" />';
  };

  const render = () => {
    els.stateInput.value = JSON.stringify(state);
    els.root.innerHTML = state.sections
      .sort((a,b) => a.order - b.order)
      .map((section, si) => `
      <section class="section-card" data-sindex="${si}" draggable="true">
        <header class="section-header">
          <input class="section-title" value="${(section.title||'').replace(/"/g,'&quot;')}" />
          <div class="section-actions">
            <button type="button" class="btn btn-view" data-action="toggle-collapse">${section.collapsed ? 'Expand' : 'Collapse'}</button>
            <button type="button" class="btn btn-delete" data-action="del-section">Delete</button>
          </div>
        </header>
        <div class="section-body ${section.collapsed ? 'hidden' : ''}">
          <div class="questions-wrap">
            ${section.questions.sort((a,b) => a.order - b.order).map((q, qi) => previewMode ? `<div class='question-card'>${q.text}${renderQuestionPreview(q)}</div>` : renderQuestionEditor(q, si, qi)).join('')}
          </div>
          <button type="button" class="btn btn-add" data-action="add-question">+ Add Question</button>
        </div>
      </section>
    `).join('');
  };

  const normalizeOrders = () => {
    state.sections.forEach((s, si) => { s.order = si + 1; s.questions.forEach((q, qi) => { q.order = qi + 1; }); });
  };

  const addQuestion = (si) => {
    state.sections[si].questions.push({ id: uid(), text: '', type: 'short_text', options: [], required: false, order: state.sections[si].questions.length + 1 });
    normalizeOrders(); markDirty(); render();
  };

  els.addSection.onclick = () => {
    state.sections.push({ id: uid(), title: `Section ${state.sections.length + 1}`, order: state.sections.length + 1, collapsed: false, questions: [] });
    markDirty(); render();
  };
  els.previewToggle.onclick = () => { previewMode = !previewMode; els.previewToggle.textContent = previewMode ? 'Edit Mode' : 'Preview Mode'; render(); };

  els.root.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const sectionCard = e.target.closest('.section-card');
    const questionCard = e.target.closest('.question-card');
    const si = Number(sectionCard?.dataset.sindex);
    const qi = Number(questionCard?.dataset.qindex);
    const action = btn.dataset.action;
    if (action === 'add-question') addQuestion(si);
    if (action === 'del-section' && confirm('Delete this section?')) { state.sections.splice(si, 1); normalizeOrders(); markDirty(); render(); }
    if (action === 'toggle-collapse') { state.sections[si].collapsed = !state.sections[si].collapsed; render(); }
    if (action === 'del-question' && confirm('Delete this question?')) { state.sections[si].questions.splice(qi, 1); normalizeOrders(); markDirty(); render(); }
    if (action === 'dup-question') { const clone = deepClone(state.sections[si].questions[qi]); clone.id = uid(); state.sections[si].questions.splice(qi + 1, 0, clone); normalizeOrders(); markDirty(); render(); }
    if (action === 'add-option') { state.sections[si].questions[qi].options.push(''); markDirty(); render(); }
    if (action === 'del-option') { state.sections[si].questions[qi].options.splice(Number(btn.dataset.oi), 1); markDirty(); render(); }
  });

  els.root.addEventListener('input', (e) => {
    const sectionCard = e.target.closest('.section-card');
    if (!sectionCard) return;
    const si = Number(sectionCard.dataset.sindex);
    const questionCard = e.target.closest('.question-card');
    const qi = questionCard ? Number(questionCard.dataset.qindex) : null;
    if (e.target.classList.contains('section-title')) state.sections[si].title = e.target.value;
    if (e.target.classList.contains('q-text')) state.sections[si].questions[qi].text = e.target.value;
    if (e.target.classList.contains('q-option')) state.sections[si].questions[qi].options[Number(e.target.dataset.oi)] = e.target.value;
    markDirty(); els.stateInput.value = JSON.stringify(state);
  });

  els.root.addEventListener('change', (e) => {
    const sectionCard = e.target.closest('.section-card'); if (!sectionCard) return;
    const si = Number(sectionCard.dataset.sindex);
    const questionCard = e.target.closest('.question-card');
    const qi = questionCard ? Number(questionCard.dataset.qindex) : null;
    if (e.target.classList.contains('q-type')) { state.sections[si].questions[qi].type = e.target.value; if (!optionTypes.has(e.target.value)) state.sections[si].questions[qi].options = []; render(); }
    if (e.target.classList.contains('q-required')) state.sections[si].questions[qi].required = e.target.checked;
    markDirty();
  });


  els.form.addEventListener('submit', async (event) => {
    event.preventDefault();
    normalizeOrders();
    els.stateInput.value = JSON.stringify(state);
    const formData = new FormData(els.form);
    formData.append('csrfmiddlewaretoken', cfg.csrfToken);
    const res = await fetch(cfg.actionUrl, { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) {
      alert((data.errors || ['Unable to save']).join('\n'));
      return;
    }
    dirty = false;
    window.location.href = '/admin-panel/checklists/';
  });

  window.addEventListener('beforeunload', (e) => { if (dirty) { e.preventDefault(); e.returnValue = ''; } });

  if (els.checklistIdDisplay && els.checklistIdDisplay.textContent.trim() === 'Auto') els.checklistIdDisplay.textContent = nextChecklistId();
  renderCheckboxes(els.metaTypeList, els.checklistTypesSource);
  renderCheckboxes(els.metaProjectList, els.projectsInput);
  renderCheckboxes(els.metaDepartmentList, els.departmentsInput);
  syncCsvDisplay();
  if (els.openChecklistMetaEditor) els.openChecklistMetaEditor.onclick = openMetaModal;
  if (els.closeChecklistMetaModal) els.closeChecklistMetaModal.onclick = () => { if (els.checklistMetaModal) els.checklistMetaModal.style.display = 'none'; };
  if (els.cancelChecklistMetaModal) els.cancelChecklistMetaModal.onclick = () => { if (els.checklistMetaModal) els.checklistMetaModal.style.display = 'none'; };
  if (els.saveChecklistMetaModal) els.saveChecklistMetaModal.onclick = () => {
    const selectedTypeIds = [...els.metaTypeList.querySelectorAll('input:checked')].map((input) => input.value);
    els.checklistTypeInput.value = selectedTypeIds.join(',');
    [...els.metaProjectList.querySelectorAll('input')].forEach((input) => { const option = [...els.projectsInput.options].find((opt) => opt.value === input.value); if (option) option.selected = input.checked; });
    [...els.metaDepartmentList.querySelectorAll('input')].forEach((input) => { const option = [...els.departmentsInput.options].find((opt) => opt.value === input.value); if (option) option.selected = input.checked; });
    syncCsvDisplay();
    if (els.checklistMetaModal) els.checklistMetaModal.style.display = 'none';
  };

  render();
})();
