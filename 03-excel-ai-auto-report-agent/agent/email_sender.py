from __future__ import annotations

import mimetypes
import socket
import smtplib
from email.message import EmailMessage
from pathlib import Path

from .config import Settings


def can_send_email(settings: Settings) -> bool:
    fields = [
        settings.smtp_host,
        settings.smtp_user,
        settings.smtp_password,
        settings.smtp_from,
        settings.smtp_to,
    ]
    return all(fields)


def _is_placeholder_smtp(settings: Settings) -> bool:
    placeholder_tokens = [
        "example.com",
        "replace_with_real_password",
    ]
    values = [
        settings.smtp_host,
        settings.smtp_user,
        settings.smtp_password,
        settings.smtp_from,
        settings.smtp_to,
    ]
    text = " ".join(values).lower()
    return any(token in text for token in placeholder_tokens)


def send_email(
    settings: Settings,
    subject: str,
    body: str,
    html_body: str | None = None,
    attachments: list[str] | None = None,
) -> None:
    if not can_send_email(settings):
        print("[WARN] SMTP is not configured. Skip sending email.")
        return
    if _is_placeholder_smtp(settings):
        print("[WARN] SMTP contains placeholder values. Update .env before sending email.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = settings.smtp_to
    msg.set_content(body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    for path_str in attachments or []:
        path = Path(path_str)
        if not path.exists():
            continue
        mime_type, _ = mimetypes.guess_type(path.name)
        if not mime_type:
            maintype, subtype = "application", "octet-stream"
        else:
            maintype, subtype = mime_type.split("/", 1)
        with path.open("rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=path.name,
            )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        print("[INFO] Email sent successfully.")
    except socket.gaierror:
        print(
            "[ERROR] SMTP host cannot be resolved. "
            f"Check SMTP_HOST value: {settings.smtp_host}"
        )
    except smtplib.SMTPAuthenticationError:
        print("[ERROR] SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD.")
    except smtplib.SMTPException as exc:
        print(f"[ERROR] SMTP send failed: {exc}")
