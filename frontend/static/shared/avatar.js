(() => {
  if (window.__qcmsAvatarFallbackBound) return;
  window.__qcmsAvatarFallbackBound = true;
  const showFallback = image => {
    image.hidden = true;
    const fallback = image.nextElementSibling;
    if (fallback) fallback.hidden = false;
  };
  document.querySelectorAll('[data-avatar] .qcms-avatar__image').forEach(image => {
    image.addEventListener('error', () => showFallback(image));
  });
  window.addEventListener('error', event => {
    const image = event.target;
    if (image instanceof HTMLImageElement && image.matches('[data-avatar] .qcms-avatar__image')) {
      showFallback(image);
    }
  }, true);
})();
