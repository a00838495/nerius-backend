from datetime import datetime

import httpx

from src.core.config import settings

_EMAILJS_URL = "https://api.emailjs.com/api/v1.0/email/send"


def _format_duration(minutes: int | None) -> str:
    if not minutes:
        return "No especificada"
    if minutes < 60:
        return f"{minutes} minutos"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}min" if m else f"{h} hora{'s' if h > 1 else ''}"


def _format_due_date(due_date: datetime) -> str:
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    return f"{due_date.day} de {months[due_date.month - 1]} de {due_date.year}"


def send_assignment_email(
    *,
    employee_name: str,
    employee_email: str,
    course_title: str,
    course_description: str | None,
    estimated_minutes: int | None,
    due_date: datetime,
    assigned_by: str,
) -> None:
    """Send a course assignment notification email via EmailJS REST API."""
    if not all([
        settings.emailjs_service_id,
        settings.emailjs_template_id,
        settings.emailjs_public_key,
        settings.emailjs_private_key,
    ]):
        return

    payload = {
        "service_id": settings.emailjs_service_id,
        "template_id": settings.emailjs_template_id,
        "user_id": settings.emailjs_public_key,
        "accessToken": settings.emailjs_private_key,
        "template_params": {
            "to_email": employee_email,
            "employee_name": employee_name,
            "course_title": course_title,
            "course_description": course_description or "Sin descripción.",
            "estimated_duration": _format_duration(estimated_minutes),
            "due_date": _format_due_date(due_date),
            "assigned_by": assigned_by,
        },
    }

    try:
        response = httpx.post(_EMAILJS_URL, json=payload, timeout=10)
        response.raise_for_status()
    except Exception:
        pass
