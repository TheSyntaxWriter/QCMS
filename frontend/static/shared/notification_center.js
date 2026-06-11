(() => {
  const root = document.getElementById('notificationCenter');
  if (!root) return;

  const bell = document.getElementById('notificationBell');
  const count = document.getElementById('notificationCount');
  const drawerCount = document.getElementById('notificationDrawerCount');
  const drawer = document.getElementById('notificationDrawer');
  const list = document.getElementById('notificationList');
  const popups = document.getElementById('notificationPopups');
  const tabs = [...document.querySelectorAll('[data-notification-tab]')];
  let activeTab = 'all';
  let colors = { Low: '#6B7280', Medium: '#2563EB', High: '#EA580C', Critical: '#DC2626' };

  function csrfToken() {
    return document.cookie.split('; ').find((item) => item.startsWith('csrftoken='))?.split('=')[1] || '';
  }

  async function post(url) {
    return fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest' } });
  }

  function relativeTime(value) {
    const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  }

  function updateCount(value) {
    count.textContent = value > 99 ? '99+' : String(value);
    count.hidden = value === 0;
    drawerCount.textContent = `${value} unread`;
  }

  function row(item) {
    const wrapper = document.createElement('article');
    wrapper.className = `notification-row${item.is_read ? '' : ' is-unread'}`;
    const indicator = document.createElement('div');
    indicator.className = 'notification-row__indicator';
    indicator.style.setProperty('--notification-priority', colors[item.priority] || colors.Low);
    const main = document.createElement('div');
    const content = document.createElement('div');
    content.className = 'notification-row__content';
    const title = document.createElement('h3');
    title.className = 'notification-row__title';
    title.textContent = item.title;
    const message = document.createElement('p');
    message.className = 'notification-row__message';
    message.textContent = item.message;
    const meta = document.createElement('div');
    meta.className = 'notification-row__meta';
    const time = document.createElement('span');
    time.textContent = `${item.priority} · ${relativeTime(item.created_at)}`;
    const actions = document.createElement('div');
    actions.className = 'notification-row__actions';
    if (!item.is_read) {
      const read = document.createElement('button');
      read.type = 'button';
      read.textContent = 'Mark read';
      read.addEventListener('click', async (event) => { event.stopPropagation(); await markRead(item); await loadList(); await poll(); });
      actions.appendChild(read);
    }
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.textContent = 'Delete';
    remove.addEventListener('click', async (event) => { event.stopPropagation(); await post(root.dataset.deleteUrlTemplate.replace('/0/', `/${item.id}/`)); await loadList(); await poll(); });
    actions.appendChild(remove);
    meta.append(time, actions);
    content.append(title, message);
    content.addEventListener('click', async () => { await markRead(item); if (item.related_url) window.location.assign(item.related_url); else { await loadList(); await poll(); } });
    main.append(content, meta);
    wrapper.append(indicator, main);
    return wrapper;
  }

  async function markRead(item) {
    if (!item.is_read) await post(root.dataset.readUrlTemplate.replace('/0/', `/${item.id}/`));
  }

  async function loadList() {
    const response = await fetch(`${root.dataset.listUrl}?tab=${encodeURIComponent(activeTab)}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!response.ok) return;
    const data = await response.json();
    list.replaceChildren();
    if (!data.notifications.length) {
      const empty = document.createElement('div');
      empty.className = 'notification-empty';
      empty.textContent = 'No notifications in this view.';
      list.appendChild(empty);
      return;
    }
    data.notifications.forEach((item) => list.appendChild(row(item)));
  }

  function playSound() {
    try {
      const context = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.frequency.value = 660;
      gain.gain.setValueAtTime(0.04, context.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.18);
      oscillator.connect(gain).connect(context.destination);
      oscillator.start(); oscillator.stop(context.currentTime + 0.18);
    } catch (_) { /* Browser audio may require a user gesture. */ }
  }

  function showPopup(item) {
    const popup = document.createElement('div');
    popup.className = 'notification-popup';
    popup.style.setProperty('--notification-priority', colors[item.priority] || colors.High);
    const title = document.createElement('strong'); title.textContent = item.title;
    const message = document.createElement('p'); message.textContent = item.message;
    const close = document.createElement('button'); close.type = 'button'; close.textContent = '\u00d7'; close.setAttribute('aria-label', 'Dismiss popup'); close.addEventListener('click', () => popup.remove());
    popup.append(title, message, close); popups.appendChild(popup);
    setTimeout(() => popup.remove(), item.priority === 'Critical' ? 12000 : 8000);
  }

  async function poll() {
    if (document.hidden) return;
    const response = await fetch(root.dataset.pollUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!response.ok) return;
    const data = await response.json();
    colors = data.colors || colors;
    bell.hidden = data.bell_enabled === false;
    updateCount(data.unread_count || 0);
    (data.popups || []).forEach(showPopup);
    if (data.sound_enabled && data.popups?.length) playSound();
  }

  bell.addEventListener('click', async () => { drawer.classList.toggle('is-open'); const open = drawer.classList.contains('is-open'); drawer.setAttribute('aria-hidden', String(!open)); bell.setAttribute('aria-expanded', String(open)); if (open) await loadList(); });
  document.getElementById('notificationClose').addEventListener('click', () => { drawer.classList.remove('is-open'); drawer.setAttribute('aria-hidden', 'true'); bell.setAttribute('aria-expanded', 'false'); });
  document.getElementById('notificationMarkAll').addEventListener('click', async () => { await post(root.dataset.readAllUrl); await loadList(); await poll(); });
  tabs.forEach((tab) => tab.addEventListener('click', async () => { activeTab = tab.dataset.notificationTab; tabs.forEach((item) => item.classList.toggle('is-active', item === tab)); await loadList(); }));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
  poll(); setInterval(poll, 45000);
})();
