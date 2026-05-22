(() => {
  const cfg = window.userSubmissionConfig;
  if (!cfg) return;

  const modal = document.getElementById('responseViewModal');
  const body = document.getElementById('responseViewContent');
  const closeBtn = document.getElementById('closeResponseView');

  function closeModal() { modal?.classList.remove('is-open'); }

  document.querySelectorAll('.response-action').forEach((btn) => {
    btn.addEventListener('click', async () => {
      if (btn.dataset.action !== 'view') return;
      const responseId = btn.dataset.id;
      const res = await fetch(`${cfg.actionUrl}?action=view&response_id=${responseId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (!data.ok) return;
      body.innerHTML = `<h4>${data.checklist_id} - ${data.checklist_name}</h4>` + data.answers.map((a) => `<div class='question-item'><strong>${a.question}</strong><p>${a.answer_text || '-'}</p>${a.file_url ? `<a href='${a.file_url}' target='_blank'>View</a> | <a href='${a.file_url}' download>Download</a>` : ''}</div>`).join('');
      modal?.classList.add('is-open');
    });
  });

  closeBtn?.addEventListener('click', closeModal);
  window.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
})();
