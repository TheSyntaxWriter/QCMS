(function () {
  const layout = document.querySelector('.app-layout');
  const sidebar = document.getElementById('appSidebar');
  const toggle = document.getElementById('sidebarToggle');
  if (!layout || !sidebar || !toggle) return;
  const storageKey = 'qcms-sidebar-collapsed';
  const mq = window.matchMedia('(max-width: 920px)');
  const setState = (collapsed) => {
    if (mq.matches) {
      layout.classList.remove('sidebar-collapsed');
      toggle.setAttribute('aria-expanded', 'true');
      return;
    }
    layout.classList.toggle('sidebar-collapsed', collapsed);
    toggle.setAttribute('aria-expanded', String(!collapsed));
  };
  setState(localStorage.getItem(storageKey) === 'true');
  toggle.addEventListener('click', () => {
    const collapsed = !layout.classList.contains('sidebar-collapsed');
    setState(collapsed);
    localStorage.setItem(storageKey, String(collapsed));
  });
  mq.addEventListener('change', () => setState(localStorage.getItem(storageKey) === 'true'));
})();
