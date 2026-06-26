from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values
from dotenv import load_dotenv

from .secrets import read_keychain_secret


ROOT_DIR = Path(__file__).resolve().parent.parent


def _contains_placeholder_values(values: dict[str, str]) -> bool:
    tokens = [
        "example.com",
        "your_qq@qq.com",
        "your_qq_smtp_auth_code",
        "replace_with_real_password",
    ]
    text = " ".join(str(v).lower() for v in values.values() if v is not None)
    return any(token in text for token in tokens)


@dataclass
class Settings:
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    openai_api_keychain_service: str
    openai_api_keychain_account: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_password_keychain_service: str
    smtp_password_keychain_account: str
    smtp_from: str
    smtp_to: str


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env", override=True)

    local_values = dotenv_values(ROOT_DIR / ".env.local")
    if local_values and not _contains_placeholder_values(local_values):
        # Only apply non-empty local overrides so blank values do not wipe .env secrets.
        for key, value in local_values.items():
            if value is None:
                continue
            if str(value).strip() == "":
                continue
            os.environ[key] = str(value)

    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_api_keychain_service = os.getenv("OPENAI_API_KEYCHAIN_SERVICE", "")
    openai_api_keychain_account = os.getenv("OPENAI_API_KEYCHAIN_ACCOUNT", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_password_keychain_service = os.getenv("SMTP_PASSWORD_KEYCHAIN_SERVICE", "")
    smtp_password_keychain_account = os.getenv("SMTP_PASSWORD_KEYCHAIN_ACCOUNT", "")

    if not openai_api_key:
        openai_api_key = read_keychain_secret(
            openai_api_keychain_service,
            openai_api_keychain_account,
        )

    if not smtp_password:
        smtp_password = read_keychain_secret(
            smtp_password_keychain_service,
            smtp_password_keychain_account,
        )

    return Settings(
        openai_api_key=openai_api_key,
        openai_model=os.getenv("OPENAI_MODEL", "glm-4.6v"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
        openai_api_keychain_service=openai_api_keychain_service,
        openai_api_keychain_account=openai_api_keychain_account,
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=smtp_password,
        smtp_password_keychain_service=smtp_password_keychain_service,
        smtp_password_keychain_account=smtp_password_keychain_account,
        smtp_from=os.getenv("SMTP_FROM", ""),
        smtp_to=os.getenv("SMTP_TO", ""),
    )
