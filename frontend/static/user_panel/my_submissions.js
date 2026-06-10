(() => {
  const cfg = window.userSubmissionConfig;
  if (!cfg) return;

  const modal = document.getElementById('responseViewModal');
  const body = document.getElementById('responseViewContent');
  const closeBtn = document.getElementById('closeResponseView');

  function closeModal() { modal?.classList.remove('is-open'); }

  function safeFileUrl(rawUrl) {
    if (!rawUrl) return '';
    try {
      const parsed = new URL(rawUrl, window.location.origin);
      if (!['http:', 'https:'].includes(parsed.protocol)) return '';
      if (parsed.origin !== window.location.origin) return '';
      return parsed.href;
    } catch (_error) {
      return '';
    }
  }

  function renderResponseDetail(data) {
    if (!body) return;
    body.replaceChildren();

    const title = document.createElement('h4');
    title.textContent = `${data.checklist_id || ''} - ${data.checklist_name || ''}`;
    body.appendChild(title);

    (data.answers || []).forEach((answer) => {
      const item = document.createElement('div');
      item.className = 'question-item';

      const question = document.createElement('strong');
      question.textContent = answer.question || '';
      item.appendChild(question);

      const answerText = document.createElement('p');
      answerText.textContent = answer.answer_text || '-';
      item.appendChild(answerText);

      const fileUrl = safeFileUrl(answer.file_url);
      if (fileUrl) {
        const viewLink = document.createElement('a');
        viewLink.href = fileUrl;
        viewLink.target = '_blank';
        viewLink.rel = 'noopener noreferrer';
        viewLink.textContent = 'View';

        const separator = document.createTextNode(' | ');

        const downloadLink = document.createElement('a');
        downloadLink.href = fileUrl;
        downloadLink.download = '';
        downloadLink.textContent = 'Download';

        item.appendChild(viewLink);
        item.appendChild(separator);
        item.appendChild(downloadLink);
      }

      body.appendChild(item);
    });
  }

  document.querySelectorAll('.response-action').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const action = btn.dataset.action;
      if (action !== 'view') {
        if (action === 'edit') {
          const checklistId = btn.dataset.checklistId;
          const responseId = btn.dataset.id;
          if (checklistId && responseId && cfg.editFillUrlTemplate) {
            const baseFillUrl = cfg.editFillUrlTemplate.replace('/0/fill/', `/${checklistId}/fill/`);
            window.location.href = `${baseFillUrl}?response_id=${encodeURIComponent(responseId)}`;
          }
          return;
        }
        if (['approve','reject'].includes(action)) {
          const fd = new FormData();
          fd.append('action', action);
          fd.append('response_id', btn.dataset.id);
          fd.append('csrfmiddlewaretoken', cfg.csrfToken);
          const res = await fetch(cfg.actionUrl, { method: 'POST', body: fd });
          if (res.ok) location.reload();
        }
        return;
      }
      const responseId = btn.dataset.id;
      const res = await fetch(`${cfg.actionUrl}?action=view&response_id=${responseId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (!data.ok) return;
      renderResponseDetail(data);
      modal?.classList.add('is-open');
    });
  });

  closeBtn?.addEventListener('click', closeModal);
  window.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
})();
