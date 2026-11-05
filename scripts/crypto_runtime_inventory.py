#!/usr/bin/env python3
"""Capture non-invasive Python/OpenSSL runtime inventory for the crypto audit.

This script does not perform cryptographic operations and does not establish
FIPS validation or approval. It records observable environment metadata only.
"""
from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


def run_command(argv: list[str]) -> dict[str, Any]:
    executable = shutil.which(argv[0])
    if executable is None:
        return {"available": False, "command": argv, "status": "NOT_FOUND"}
    try:
        completed = subprocess.run(
            [executable, *argv[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return {
            "available": True,
            "command": argv,
            "executable": executable,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "status": "OK" if completed.returncode == 0 else "NONZERO_EXIT",
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": True,
            "command": argv,
            "executable": executable,
            "status": "ERROR",
            "error": str(exc),
        }


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def collect_inventory() -> dict[str, Any]:
    openssl_cli = run_command(["openssl", "version", "-a"])
    provider_list = run_command(["openssl", "list", "-providers", "-verbose"])
    return {
        "schema": "kmh-oia.crypto-runtime-inventory.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "python_packages": {
            "cryptography": package_version("cryptography"),
            "pyOpenSSL": package_version("pyOpenSSL"),
        },
        "python_ssl": {
            "openssl_version": ssl.OPENSSL_VERSION,
            "openssl_version_info": list(ssl.OPENSSL_VERSION_INFO),
        },
        "openssl_cli": openssl_cli,
        "openssl_providers": provider_list,
        "environment_hints": {
            "OPENSSL_CONF_set": bool(os.environ.get("OPENSSL_CONF")),
            "OPENSSL_MODULES_set": bool(os.environ.get("OPENSSL_MODULES")),
        },
        "limitations": [
            "Inventory only; no signing, verification, or provider approval test was run.",
            "CLI provider listing does not prove that an application uses that provider.",
            "This output does not establish CMVP certificate scope or FIPS-approved operation.",
            "Do not include secrets, private keys, or full environment dumps in evidence.",
        ],
        "fips_assessment": "NOT_ASSESSED",
    }


if __name__ == "__main__":
    print(json.dumps(collect_inventory(), indent=2, sort_keys=True))
