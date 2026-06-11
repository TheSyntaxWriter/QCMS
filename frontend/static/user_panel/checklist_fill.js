(() => {
  const form = document.getElementById('checklistFillForm');
  if (!form || form.dataset.geolocationEnabled !== 'true') return;

  const latitude = document.getElementById('submissionLatitude');
  const longitude = document.getElementById('submissionLongitude');
  const accuracy = document.getElementById('submissionAccuracy');
  const status = document.getElementById('geolocationStatus');
  let locationAttempted = false;

  form.addEventListener('submit', (event) => {
    const submitter = event.submitter;
    if (!submitter || submitter.value !== 'submit' || locationAttempted) return;

    event.preventDefault();
    locationAttempted = true;
    if (status) status.textContent = 'Requesting location...';

    const continueSubmission = () => {
      if (status && !latitude.value) status.textContent = 'Location unavailable. Submitting without coordinates.';
      form.requestSubmit(submitter);
    };

    if (!navigator.geolocation) {
      continueSubmission();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        latitude.value = String(position.coords.latitude);
        longitude.value = String(position.coords.longitude);
        accuracy.value = String(position.coords.accuracy);
        if (status) status.textContent = `Location captured (accuracy ${Math.round(position.coords.accuracy)} m).`;
        continueSubmission();
      },
      continueSubmission,
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  });
})();
