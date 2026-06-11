(() => {
  const cfg = window.userSubmissionConfig;
  if (!cfg) return;

  const modal = document.getElementById('responseViewModal');
  const body = document.getElementById('responseViewContent');
  const closeBtn = document.getElementById('closeResponseView');
  const decisionModal = document.getElementById('responseDecisionModal');
  const decisionTitle = document.getElementById('responseDecisionTitle');
  const decisionLabel = document.getElementById('responseDecisionLabel');
  const decisionComment = document.getElementById('responseDecisionComment');
  const decisionError = document.getElementById('responseDecisionError');
  const decisionConfirm = document.getElementById('confirmResponseDecision');
  const decisionClose = document.getElementById('closeResponseDecision');
  const decisionCancel = document.getElementById('cancelResponseDecision');
  let pendingDecision = null;

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

    const location = data.location || {};
    const locationItem = document.createElement('div');
    locationItem.className = 'question-item response-location';
    const locationTitle = document.createElement('strong');
    locationTitle.textContent = 'Submission Location';
    locationItem.appendChild(locationTitle);
    const locationText = document.createElement('p');
    const hasCoordinates = Number.isFinite(location.latitude) && Number.isFinite(location.longitude);
    locationText.textContent = hasCoordinates
      ? `${location.latitude}, ${location.longitude}${Number.isFinite(location.accuracy) ? ` (accuracy ${Math.round(location.accuracy)} m)` : ''}`
      : 'Coordinates not captured.';
    locationItem.appendChild(locationText);
    const ipText = document.createElement('p');
    ipText.textContent = `Submission IP: ${location.submission_ip || 'Not recorded'}`;
    locationItem.appendChild(ipText);
    if (hasCoordinates) {
      const mapsLink = document.createElement('a');
      mapsLink.href = `https://www.google.com/maps?q=${encodeURIComponent(`${location.latitude},${location.longitude}`)}`;
      mapsLink.target = '_blank';
      mapsLink.rel = 'noopener noreferrer';
      mapsLink.textContent = 'Open in Google Maps';
      locationItem.appendChild(mapsLink);
    }
    body.appendChild(locationItem);

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

    const history = document.createElement('section');
    history.className = 'response-review-history';
    const historyTitle = document.createElement('h4');
    historyTitle.textContent = 'Approval and Rejection History';
    history.appendChild(historyTitle);

    if (!(data.decisions || []).length) {
      const empty = document.createElement('p');
      empty.textContent = 'No approval or rejection comments recorded.';
      history.appendChild(empty);
    }

    (data.decisions || []).forEach((decision) => {
      const item = document.createElement('div');
      item.className = `response-review-item ${decision.action === 'approve' ? 'is-approved' : 'is-rejected'}`;
      const heading = document.createElement('strong');
      heading.textContent = `${decision.is_override ? 'Override ' : ''}${decision.action_label || decision.action || 'Decision'}`;
      item.appendChild(heading);
      const meta = document.createElement('p');
      meta.className = 'response-review-meta';
      meta.textContent = `${decision.actor || 'Unknown'} (${decision.actor_role || 'Unknown role'}) - ${decision.created_at || ''}`;
      item.appendChild(meta);
      const comment = document.createElement('p');
      comment.className = 'response-review-comment';
      comment.textContent = decision.comment || 'No comment provided.';
      item.appendChild(comment);
      history.appendChild(item);
    });
    body.appendChild(history);
  }

  function closeDecisionModal() {
    decisionModal?.classList.remove('is-open');
    pendingDecision = null;
    if (decisionComment) decisionComment.value = '';
    if (decisionError) decisionError.textContent = '';
  }

  function openDecisionModal(action, responseId, label) {
    pendingDecision = { action, responseId };
    const isReject = action === 'reject';
    if (decisionTitle) decisionTitle.textContent = label || (isReject ? 'Reject Response' : 'Approve Response');
    if (decisionLabel) decisionLabel.textContent = isReject ? 'Rejection reason (required)' : 'Approval comment (optional)';
    if (decisionComment) {
      decisionComment.value = '';
      decisionComment.required = isReject;
      decisionComment.placeholder = isReject ? 'Explain why this response is being rejected.' : 'Add an optional approval comment.';
    }
    if (decisionError) decisionError.textContent = '';
    decisionModal?.classList.add('is-open');
    decisionComment?.focus();
  }

  async function submitDecision() {
    if (!pendingDecision) return;
    const comment = decisionComment?.value.trim() || '';
    if (pendingDecision.action === 'reject' && !comment) {
      decisionError.textContent = 'Rejection reason is required.';
      decisionComment?.focus();
      return;
    }

    decisionConfirm.disabled = true;
    const fd = new FormData();
    fd.append('action', pendingDecision.action);
    fd.append('response_id', pendingDecision.responseId);
    fd.append('comment', comment);
    fd.append('csrfmiddlewaretoken', cfg.csrfToken);
    try {
      const res = await fetch(cfg.actionUrl, { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        decisionError.textContent = data.error || 'Unable to update this response.';
        return;
      }
      location.reload();
    } catch (_error) {
      decisionError.textContent = 'Unable to update this response.';
    } finally {
      decisionConfirm.disabled = false;
    }
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
          openDecisionModal(action, btn.dataset.id, btn.textContent.trim());
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
  decisionClose?.addEventListener('click', closeDecisionModal);
  decisionCancel?.addEventListener('click', closeDecisionModal);
  decisionConfirm?.addEventListener('click', submitDecision);
  window.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  window.addEventListener('click', (e) => { if (e.target === decisionModal) closeDecisionModal(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      closeDecisionModal();
    }
  });
})();
