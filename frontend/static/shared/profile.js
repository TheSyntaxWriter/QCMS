(() => {
  const page = document.querySelector('[data-profile-page]');
  if (!page) return;

  const fileInput = document.getElementById('imageInput');
  const chooseButton = document.getElementById('choosePhotoButton');
  const changeButton = document.getElementById('changePhotoButton');
  const saveButton = document.getElementById('savePhotoButton');
  const croppedInput = document.getElementById('croppedImage');
  const status = document.getElementById('profilePhotoStatus');
  const modal = document.getElementById('cropModal');
  const panel = modal.querySelector('.profile-crop-dialog__panel');
  const closeButton = document.getElementById('closeCropButton');
  const cancelButton = document.getElementById('cancelCropButton');
  const applyButton = document.getElementById('applyCropButton');
  const resetButton = document.getElementById('resetCropButton');
  const zoomInButton = document.getElementById('zoomInButton');
  const zoomOutButton = document.getElementById('zoomOutButton');
  const zoomControl = document.getElementById('zoomControl');
  const canvas = document.getElementById('cropCanvas');
  const context = canvas.getContext('2d');
  const preview = document.getElementById('avatarPreview');
  const cropSize = 264;
  const cropLeft = (canvas.width - cropSize) / 2;
  const cropTop = (canvas.height - cropSize) / 2;
  const image = new Image();
  let sourceUrl = '';
  let loaded = false;
  let dragging = false;
  let activePointer = null;
  let lastX = 0;
  let lastY = 0;
  let baseScale = 1;
  let zoom = 1;
  let offsetX = 0;
  let offsetY = 0;
  let returnFocus = null;

  const maxEnhancementDimension = 2048;

  function correctedLevels(data) {
    let luminanceTotal = 0;
    let luminanceSquaredTotal = 0;
    const pixelCount = data.length / 4;
    for (let index = 0; index < data.length; index += 4) {
      const luminance = data[index] * .2126 + data[index + 1] * .7152 + data[index + 2] * .0722;
      luminanceTotal += luminance;
      luminanceSquaredTotal += luminance * luminance;
    }
    const mean = luminanceTotal / pixelCount;
    const variance = Math.max(0, luminanceSquaredTotal / pixelCount - mean * mean);
    const deviation = Math.sqrt(variance);
    return {
      brightness: Math.max(-12, Math.min(12, 128 - mean)) * .45,
      contrast: Math.max(1, Math.min(1.16, 52 / Math.max(32, deviation))),
    };
  }

  function enhancePixels(imageData) {
    const { data, width, height } = imageData;
    const { brightness, contrast } = correctedLevels(data);
    const leveled = new Uint8ClampedArray(data.length);
    for (let index = 0; index < data.length; index += 4) {
      leveled[index] = (data[index] - 128) * contrast + 128 + brightness;
      leveled[index + 1] = (data[index + 1] - 128) * contrast + 128 + brightness;
      leveled[index + 2] = (data[index + 2] - 128) * contrast + 128 + brightness;
      leveled[index + 3] = data[index + 3];
    }

    const output = new Uint8ClampedArray(leveled);
    const amount = .12;
    for (let y = 1; y < height - 1; y += 1) {
      for (let x = 1; x < width - 1; x += 1) {
        const index = (y * width + x) * 4;
        for (let channel = 0; channel < 3; channel += 1) {
          const blurred = (
            leveled[index - width * 4 + channel] +
            leveled[index - 4 + channel] +
            leveled[index + channel] * 4 +
            leveled[index + 4 + channel] +
            leveled[index + width * 4 + channel]
          ) / 8;
          output[index + channel] = leveled[index + channel] + (leveled[index + channel] - blurred) * amount;
        }
      }
    }
    return new ImageData(output, width, height);
  }

  async function enhancedImageUrl(file) {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
    const scale = Math.min(1, maxEnhancementDimension / Math.max(bitmap.width, bitmap.height));
    const enhancementCanvas = document.createElement('canvas');
    enhancementCanvas.width = Math.max(1, Math.round(bitmap.width * scale));
    enhancementCanvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const enhancementContext = enhancementCanvas.getContext('2d', { willReadFrequently: true });
    enhancementContext.drawImage(bitmap, 0, 0, enhancementCanvas.width, enhancementCanvas.height);
    bitmap.close();
    const pixels = enhancementContext.getImageData(0, 0, enhancementCanvas.width, enhancementCanvas.height);
    enhancementContext.putImageData(enhancePixels(pixels), 0, 0);
    return enhancementCanvas.toDataURL('image/jpeg', .94);
  }

  const currentScale = () => baseScale * zoom;

  function clampOffsets() {
    if (!loaded) return;
    const scaledWidth = image.width * currentScale();
    const scaledHeight = image.height * currentScale();
    const maxX = Math.max(0, (scaledWidth - cropSize) / 2);
    const maxY = Math.max(0, (scaledHeight - cropSize) / 2);
    offsetX = Math.max(-maxX, Math.min(maxX, offsetX));
    offsetY = Math.max(-maxY, Math.min(maxY, offsetY));
  }

  function imageRect(scale = currentScale()) {
    const width = image.width * scale;
    const height = image.height * scale;
    return {
      x: (canvas.width - width) / 2 + offsetX,
      y: (canvas.height - height) / 2 + offsetY,
      width,
      height,
    };
  }

  function draw() {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = '#0f172a';
    context.fillRect(0, 0, canvas.width, canvas.height);
    if (!loaded) return;

    clampOffsets();
    const rect = imageRect();
    context.drawImage(image, rect.x, rect.y, rect.width, rect.height);

    context.save();
    context.fillStyle = 'rgba(2, 6, 23, .62)';
    context.beginPath();
    context.rect(0, 0, canvas.width, canvas.height);
    context.arc(canvas.width / 2, canvas.height / 2, cropSize / 2, 0, Math.PI * 2, true);
    context.fill('evenodd');
    context.strokeStyle = '#fff';
    context.lineWidth = 3;
    context.beginPath();
    context.arc(canvas.width / 2, canvas.height / 2, cropSize / 2, 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }

  function resetCrop() {
    if (!loaded) return;
    baseScale = Math.max(cropSize / image.width, cropSize / image.height);
    zoom = 1;
    offsetX = 0;
    offsetY = 0;
    zoomControl.value = '1';
    draw();
  }

  function setZoom(value) {
    zoom = Math.max(1, Math.min(3, Number(value) || 1));
    zoomControl.value = String(zoom);
    draw();
  }

  function focusableElements() {
    return [...panel.querySelectorAll('button:not([disabled]), input:not([disabled]), [tabindex="0"]')];
  }

  function openModal() {
    if (!loaded) return;
    returnFocus = document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    closeButton.focus();
    draw();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
    dragging = false;
    activePointer = null;
    if (returnFocus) returnFocus.focus();
  }

  async function loadSelectedFile(file) {
    if (!file) return;
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
      status.textContent = 'Choose a PNG, JPG, or WEBP image.';
      fileInput.value = '';
      return;
    }
    status.textContent = 'Optimizing photo...';
    if (sourceUrl && sourceUrl.startsWith('blob:')) URL.revokeObjectURL(sourceUrl);
    try {
      sourceUrl = await enhancedImageUrl(file);
    } catch (error) {
      sourceUrl = URL.createObjectURL(file);
    }
    image.onload = () => {
      loaded = true;
      resetCrop();
      status.textContent = '';
      openModal();
    };
    image.onerror = () => {
      loaded = false;
      status.textContent = 'The selected image could not be opened.';
      if (sourceUrl.startsWith('blob:')) URL.revokeObjectURL(sourceUrl);
      sourceUrl = '';
    };
    image.src = sourceUrl;
  }

  function applyCrop() {
    if (!loaded) return;
    clampOffsets();
    const rect = imageRect();
    const output = document.createElement('canvas');
    output.width = 512;
    output.height = 512;
    const outputContext = output.getContext('2d');
    outputContext.fillStyle = '#fff';
    outputContext.fillRect(0, 0, output.width, output.height);
    const ratio = output.width / cropSize;
    outputContext.drawImage(
      image,
      (rect.x - cropLeft) * ratio,
      (rect.y - cropTop) * ratio,
      rect.width * ratio,
      rect.height * ratio,
    );
    const dataUrl = output.toDataURL('image/png');
    croppedInput.value = dataUrl;
    preview.src = dataUrl;
    preview.hidden = false;
    if (preview.nextElementSibling) preview.nextElementSibling.hidden = true;
    saveButton.disabled = false;
    status.textContent = 'Photo ready to save.';
    closeModal();
  }

  function moveImage(deltaX, deltaY) {
    offsetX += deltaX;
    offsetY += deltaY;
    draw();
  }

  chooseButton.addEventListener('click', () => fileInput.click());
  changeButton.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => loadSelectedFile(fileInput.files[0]));
  closeButton.addEventListener('click', closeModal);
  cancelButton.addEventListener('click', closeModal);
  modal.querySelector('[data-crop-close]').addEventListener('click', closeModal);
  applyButton.addEventListener('click', applyCrop);
  resetButton.addEventListener('click', resetCrop);
  zoomControl.addEventListener('input', () => setZoom(zoomControl.value));
  zoomInButton.addEventListener('click', () => setZoom(zoom + .1));
  zoomOutButton.addEventListener('click', () => setZoom(zoom - .1));

  canvas.addEventListener('pointerdown', event => {
    dragging = true;
    activePointer = event.pointerId;
    lastX = event.clientX;
    lastY = event.clientY;
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', event => {
    if (!dragging || event.pointerId !== activePointer) return;
    const scaleX = canvas.width / canvas.getBoundingClientRect().width;
    const scaleY = canvas.height / canvas.getBoundingClientRect().height;
    moveImage((event.clientX - lastX) * scaleX, (event.clientY - lastY) * scaleY);
    lastX = event.clientX;
    lastY = event.clientY;
  });
  canvas.addEventListener('pointerup', event => {
    if (event.pointerId === activePointer) {
      dragging = false;
      activePointer = null;
      canvas.releasePointerCapture(event.pointerId);
    }
  });
  canvas.addEventListener('pointercancel', () => {
    dragging = false;
    activePointer = null;
  });
  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    setZoom(zoom + (event.deltaY < 0 ? .08 : -.08));
  }, { passive: false });
  canvas.addEventListener('keydown', event => {
    const distance = event.shiftKey ? 10 : 2;
    const moves = {
      ArrowLeft: [distance, 0],
      ArrowRight: [-distance, 0],
      ArrowUp: [0, distance],
      ArrowDown: [0, -distance],
    };
    if (!moves[event.key]) return;
    event.preventDefault();
    moveImage(...moves[event.key]);
  });

  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      closeModal();
      return;
    }
    if (event.key !== 'Tab') return;
    const items = focusableElements();
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  document.getElementById('profilePhotoForm').addEventListener('submit', event => {
    if (!croppedInput.value) {
      event.preventDefault();
      status.textContent = 'Choose and apply a photo before saving.';
    } else {
      saveButton.disabled = true;
      saveButton.textContent = 'Saving...';
    }
  });
})();
