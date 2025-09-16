from __future__ import annotations

import pytest
from selenium.common.exceptions import InvalidArgumentException

from gptpar.infrastructure.browser.selenium_driver_factory import create_firefox_driver


class DummyDriver:
    def __init__(self, *_, options=None, **__):
        self.options = options
        self.maximised = False

    def maximize_window(self) -> None:  # pragma: no cover - trivial
        self.maximised = True


def test_create_firefox_driver_uses_binary_from_env(monkeypatch, tmp_path):
    fake_firefox = tmp_path / "firefox"
    fake_firefox.write_text("#!/bin/sh\necho firefox")

    def fake_constructor(*args, **kwargs):
        driver = DummyDriver(*args, **kwargs)
        return driver

    monkeypatch.setenv("FIREFOX_BINARY", str(fake_firefox))
    monkeypatch.setattr(
        "gptpar.infrastructure.browser.selenium_driver_factory.webdriver.Firefox", fake_constructor
    )

    driver = create_firefox_driver()

    assert isinstance(driver, DummyDriver)
    assert driver.maximised is True
    assert driver.options._binary_location == str(fake_firefox)


def test_create_firefox_driver_invalid_binary_path(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing-firefox"
    monkeypatch.setenv("FIREFOX_BINARY", str(missing_path))

    with pytest.raises(RuntimeError) as excinfo:
        create_firefox_driver()

    assert "FIREFOX_BINARY" in str(excinfo.value)


def test_create_firefox_driver_translates_invalid_argument(monkeypatch, tmp_path):
    fake_firefox = tmp_path / "firefox"
    fake_firefox.write_text("#!/bin/sh\necho firefox")

    def fake_constructor(*args, **kwargs):
        raise InvalidArgumentException("binary is not a Firefox executable")

    monkeypatch.setenv("FIREFOX_BINARY", str(fake_firefox))
    monkeypatch.setattr(
        "gptpar.infrastructure.browser.selenium_driver_factory.webdriver.Firefox", fake_constructor
    )

    with pytest.raises(RuntimeError) as excinfo:
        create_firefox_driver()

    assert "executável válido" in str(excinfo.value)
