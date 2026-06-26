from __future__ import annotations

import subprocess


def read_keychain_secret(service: str, account: str) -> str:
    """Read a generic password from macOS Keychain.

    Returns empty string if the item is missing or unreadable.
    """
    if not service or not account:
        return ""

    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                service,
                "-a",
                account,
                "-w",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""
