from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def create_firefox_driver(
    profile_path: Optional[Path] = None,
    headless: bool = False,
    firefox_binary: Optional[Path] = None,
) -> webdriver.Firefox:
    """Create a configured Firefox WebDriver instance.

    Parameters
    ----------
    profile_path:
        Optional path to an existing Firefox profile directory.
    headless:
        Whether the browser should run in headless mode.
    firefox_binary:
        Explicit path to the Firefox executable. When provided (or when the
        ``FIREFOX_BINARY``/``FIREFOX_BIN`` environment variables are set), the
        path is validated before delegating to Selenium to avoid the less
        helpful ``InvalidArgumentException`` that Selenium would otherwise
        raise.
    """

    options = FirefoxOptions()
    options.headless = headless

    binary_location = _resolve_firefox_binary(firefox_binary)
    if binary_location is not None:
        options.binary_location = str(binary_location)

    if profile_path is not None:
        options.profile = str(profile_path)

    try:
        driver = webdriver.Firefox(options=options)
    except InvalidArgumentException as exc:
        message = str(exc)
        if "binary is not a firefox executable" in message.lower():
            raise RuntimeError(
                "O caminho configurado para o Firefox não aponta para um executável válido. "
                "Revise a variável de ambiente FIREFOX_BINARY ou a configuração utilizada."
            ) from exc
        raise

    driver.maximize_window()
    return driver


def _resolve_firefox_binary(explicit_path: Optional[Path]) -> Optional[Path]:
    """Return a validated Firefox binary path if one was provided.

    The lookup order prioritises the explicit ``firefox_binary`` argument,
    followed by the ``FIREFOX_BINARY`` and ``FIREFOX_BIN`` environment
    variables.  Each candidate is validated to ensure that we only forward
    existing executables to Selenium.
    """

    candidates: list[tuple[str, Path]] = []

    if explicit_path is not None:
        candidates.append(("firefox_binary parameter", explicit_path))

    for env_var in ("FIREFOX_BINARY", "FIREFOX_BIN"):
        env_value = os.environ.get(env_var)
        if env_value:
            candidates.append((f"environment variable {env_var}", Path(env_value)))

    for source, raw_path in candidates:
        resolved_path = _normalise_executable_path(raw_path)
        if not resolved_path.exists() or not resolved_path.is_file():
            raise RuntimeError(f"{source} aponta para um caminho inexistente: {resolved_path}")
        return resolved_path

    return None


def _normalise_executable_path(path: Path) -> Path:
    """Expand user home references and resolve relative executables."""

    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded

    found = shutil.which(str(expanded))
    if found:
        return Path(found)

    return expanded
