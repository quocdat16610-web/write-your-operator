"""API key storage via keyring (Windows Credential Manager on Windows)."""
from __future__ import annotations

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

SERVICE_NAME = "MyOSAcademy"
ACCOUNT_NAME = "anthropic_api_key"


class CredentialError(Exception):
    """Raised with a Vietnamese message the UI can show directly."""


def get_api_key() -> str | None:
    try:
        return keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
    except KeyringError as exc:
        raise CredentialError(f"Không đọc được API key từ Credential Manager: {exc}") from exc


def set_api_key(api_key: str) -> None:
    try:
        keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, api_key)
    except KeyringError as exc:
        raise CredentialError(f"Không lưu được API key vào Credential Manager: {exc}") from exc


def delete_api_key() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except PasswordDeleteError:
        pass  # nothing stored, nothing to delete
    except KeyringError as exc:
        raise CredentialError(f"Không xoá được API key: {exc}") from exc


def mask(api_key: str) -> str:
    """Show only the start and end of a key, e.g. sk-ant-a…9xQ2."""
    if len(api_key) <= 12:
        return "•" * len(api_key)
    return f"{api_key[:8]}…{api_key[-4:]}"
