from io import BytesIO
from pathlib import Path
import zipfile

from django.core.exceptions import ValidationError
from pypdf import PdfReader
from PIL import Image, UnidentifiedImageError


MAX_CHECKLIST_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_IMAGE_UPLOAD_SIZE = 2 * 1024 * 1024

CHECKLIST_UPLOAD_TYPES = {
    '.pdf': {'application/pdf'},
    '.png': {'image/png'},
    '.jpg': {'image/jpeg'},
    '.jpeg': {'image/jpeg'},
    '.webp': {'image/webp'},
    '.txt': {'text/plain'},
    '.csv': {'text/csv', 'application/csv', 'text/plain'},
    '.doc': {'application/msword'},
    '.docx': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
    '.xls': {'application/vnd.ms-excel'},
    '.xlsx': {'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
}

IMAGE_UPLOAD_TYPES = {
    '.png': {'image/png'},
    '.jpg': {'image/jpeg'},
    '.jpeg': {'image/jpeg'},
    '.webp': {'image/webp'},
}

BRANDING_UPLOAD_TYPES = {
    **IMAGE_UPLOAD_TYPES,
    '.ico': {'image/x-icon', 'image/vnd.microsoft.icon'},
}


def _extension(uploaded_file):
    return Path(uploaded_file.name or '').suffix.lower()


def _content_type(uploaded_file):
    return (getattr(uploaded_file, 'content_type', '') or '').lower()


def _validate_uploaded_file(uploaded_file, *, allowed_types, max_size, label):
    if not uploaded_file:
        return

    ext = _extension(uploaded_file)
    if ext not in allowed_types:
        allowed = ', '.join(sorted(allowed_types))
        raise ValidationError(f'{label} type is not allowed. Allowed extensions: {allowed}.')

    content_type = _content_type(uploaded_file)
    if content_type not in allowed_types[ext]:
        raise ValidationError(f'{label} content type does not match the file extension.')

    if uploaded_file.size > max_size:
        limit_mb = max_size // (1024 * 1024)
        raise ValidationError(f'{label} must be {limit_mb}MB or smaller.')


def _read_upload_bytes(uploaded_file):
    current_position = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else None
    try:
        uploaded_file.seek(0)
        return uploaded_file.read()
    finally:
        if current_position is not None:
            uploaded_file.seek(current_position)


def _validate_pdf_bytes(data, label):
    if not data.startswith(b'%PDF-'):
        raise ValidationError(f'{label} is not a valid PDF file.')
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if len(reader.pages) < 1:
            raise ValidationError(f'{label} is not a readable PDF file.')
    except Exception as exc:
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError(f'{label} is not a readable PDF file.') from exc


def _validate_zip_office_bytes(data, expected_entry, label):
    try:
        with zipfile.ZipFile(BytesIO(data)) as archive:
            names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise ValidationError(f'{label} is not a valid Office document.') from exc
    if '[Content_Types].xml' not in names or expected_entry not in names:
        raise ValidationError(f'{label} does not match the expected Office document structure.')


def _validate_ole_bytes(data, label):
    if not data.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        raise ValidationError(f'{label} is not a valid legacy Office document.')


def _validate_text_bytes(data, label):
    try:
        decoded = data.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValidationError(f'{label} is not a valid text file.') from exc
    lowered = decoded[:4096].lower()
    if '<script' in lowered or '<html' in lowered or '<svg' in lowered:
        raise ValidationError(f'{label} contains HTML or script content.')


def _validate_checklist_signature(uploaded_file):
    ext = _extension(uploaded_file)
    data = _read_upload_bytes(uploaded_file)
    if ext == '.pdf':
        _validate_pdf_bytes(data, 'Checklist attachment')
    elif ext in {'.png', '.jpg', '.jpeg', '.webp'}:
        _validate_image_bytes(data, 'Checklist attachment')
    elif ext in {'.txt', '.csv'}:
        _validate_text_bytes(data, 'Checklist attachment')
    elif ext == '.docx':
        _validate_zip_office_bytes(data, 'word/document.xml', 'Checklist attachment')
    elif ext == '.xlsx':
        _validate_zip_office_bytes(data, 'xl/workbook.xml', 'Checklist attachment')
    elif ext in {'.doc', '.xls'}:
        _validate_ole_bytes(data, 'Checklist attachment')


def _validate_image_bytes(data, label):
    try:
        image = Image.open(BytesIO(data))
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(f'{label} is not a valid image.') from exc


def _validate_image_file(uploaded_file, *, allowed_types, max_size, label):
    _validate_uploaded_file(uploaded_file, allowed_types=allowed_types, max_size=max_size, label=label)
    _validate_image_bytes(_read_upload_bytes(uploaded_file), label)


def validate_checklist_upload(uploaded_file):
    _validate_uploaded_file(
        uploaded_file,
        allowed_types=CHECKLIST_UPLOAD_TYPES,
        max_size=MAX_CHECKLIST_UPLOAD_SIZE,
        label='Checklist attachment',
    )
    _validate_checklist_signature(uploaded_file)


def validate_branding_upload(uploaded_file):
    _validate_image_file(
        uploaded_file,
        allowed_types=BRANDING_UPLOAD_TYPES,
        max_size=MAX_IMAGE_UPLOAD_SIZE,
        label='Branding image',
    )


def validate_profile_image_bytes(image_bytes, declared_content_type):
    content_type = (declared_content_type or '').lower()
    if content_type not in {'image/png', 'image/jpeg', 'image/webp'}:
        raise ValidationError('Profile image must be PNG, JPG, or WEBP.')

    if len(image_bytes) > MAX_IMAGE_UPLOAD_SIZE:
        raise ValidationError('Profile image must be 2MB or smaller.')

    try:
        image = Image.open(BytesIO(image_bytes))
        if (image.format or '').upper() not in {'PNG', 'JPEG', 'WEBP'}:
            raise ValidationError('Profile image content is not a supported image.')
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError('Profile image is not a valid image.') from exc
