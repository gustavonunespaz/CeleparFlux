from __future__ import annotations

from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def create_firefox_driver(profile_path: Optional[Path] = None, headless: bool = False) -> webdriver.Firefox:
    """Create a configured Firefox WebDriver instance."""

    options = FirefoxOptions()
    options.headless = headless

    if profile_path is not None:
        options.profile = str(profile_path)

    driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    return driver
