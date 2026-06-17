(() => {
  const mobileNavigation = document.querySelector('[data-control-panel-mobile-nav]');
  if (mobileNavigation) {
    mobileNavigation.addEventListener('change', () => {
      window.location.assign(mobileNavigation.value);
    });
  }

  const colorInput = document.getElementById('global_theme_color');
  const colorValue = document.getElementById('themeColorValue');
  if (colorInput && colorValue) {
    const syncColor = () => { colorValue.textContent = colorInput.value; };
    colorInput.addEventListener('input', syncColor);
    syncColor();
  }

  const iconSearch = document.querySelector('[data-icon-gallery-search]');
  const iconCategory = document.querySelector('[data-icon-gallery-category]');
  const iconRows = Array.from(document.querySelectorAll('[data-icon-gallery-row]'));
  const filterIconRows = () => {
    const term = (iconSearch?.value || '').trim().toLowerCase();
    const category = iconCategory?.value || '';
    iconRows.forEach(row => {
      const select = row.querySelector('[data-icon-picker]');
      const selected = select?.selectedOptions?.[0];
      const matchesTerm = !term || (row.dataset.searchText || '').includes(term) || (selected?.textContent || '').toLowerCase().includes(term);
      const matchesCategory = !category || selected?.dataset.category === category;
      row.classList.toggle('is-hidden', !(matchesTerm && matchesCategory));
    });
  };
  iconSearch?.addEventListener('input', filterIconRows);
  iconCategory?.addEventListener('change', filterIconRows);
  document.querySelectorAll('[data-icon-reset]').forEach(button => {
    button.addEventListener('click', () => {
      const row = button.closest('[data-icon-gallery-row]');
      const select = row?.querySelector('[data-icon-picker]');
      if (select?.dataset.defaultIcon) select.value = select.dataset.defaultIcon;
      filterIconRows();
    });
  });
  document.querySelector('[data-icon-gallery-reset-all]')?.addEventListener('click', () => {
    const resetInput = document.getElementById('iconGalleryReset');
    if (resetInput) resetInput.value = '1';
  });

  const form = document.getElementById('controlForm');
  const modal = document.getElementById('passwordModal');
  if (!form || !modal) return;

  const password = document.getElementById('confirmPasswordField');
  const hiddenPassword = document.getElementById('confirmPasswordInput');
  const cancel = document.getElementById('cancelPasswordConfirmation');
  const confirm = document.getElementById('confirmPasswordConfirmation');
  let pendingSubmitter = null;

  const closeModal = () => {
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    if (pendingSubmitter) pendingSubmitter.focus();
  };

  form.addEventListener('submit', event => {
    if (hiddenPassword.value) return;
    event.preventDefault();
    pendingSubmitter = event.submitter;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    password.value = '';
    password.focus();
  });
  cancel.addEventListener('click', closeModal);
  confirm.addEventListener('click', () => {
    if (!password.value.trim()) {
      password.focus();
      return;
    }
    hiddenPassword.value = password.value;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    if (form.requestSubmit && pendingSubmitter) form.requestSubmit(pendingSubmitter);
    else form.submit();
  });
  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeModal();
  });
})();
