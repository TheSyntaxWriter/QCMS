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
