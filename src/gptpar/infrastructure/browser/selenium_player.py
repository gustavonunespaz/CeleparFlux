from __future__ import annotations

import logging
import time
from typing import Callable, List

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ...domain.models import MacroStep
from ...domain.services import MacroPlayer

LOGGER = logging.getLogger(__name__)


class SeleniumMacroPlayer(MacroPlayer):
    """Reproduces macros using Selenium and Firefox."""

    def __init__(
        self,
        driver_factory: Callable[[], WebDriver],
        wait_timeout: float = 10.0,
        typing_delay: float = 0.02,
    ) -> None:
        self._driver_factory = driver_factory
        self._wait_timeout = wait_timeout
        self._typing_delay = typing_delay

    def play(self, steps: List[MacroStep], start_url: str) -> None:
        driver = self._driver_factory()
        LOGGER.info("Opening Firefox to execute macro: %s", start_url)
        driver.get(start_url)
        wait = WebDriverWait(driver, self._wait_timeout)

        try:
            for step in steps:
                if not step.selector:
                    LOGGER.debug("Skipping step without selector: %s", step)
                    continue

                LOGGER.info("Executing step: %s", step)

                try:
                    if step.action == "click":
                        element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, step.selector)))
                        self._scroll_into_view(driver, element)
                        element.click()
                        time.sleep(0.1)
                    elif step.action in {"input", "change"}:
                        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, step.selector)))
                        self._scroll_into_view(driver, element)
                        self._apply_input(element, step)
                        time.sleep(0.1)
                    else:
                        LOGGER.warning("Unknown step action '%s' ignored.", step.action)
                except TimeoutException as exc:
                    raise RuntimeError(
                        f"Tempo esgotado ao localizar o seletor '{step.selector}' para a ação '{step.action}'."
                    ) from exc
                except WebDriverException as exc:
                    raise RuntimeError(
                        f"Falha do WebDriver ao executar a ação '{step.action}' no seletor '{step.selector}'."
                    ) from exc
        finally:
            try:
                driver.quit()
            except WebDriverException as exc:
                LOGGER.warning("Error closing Firefox after playback: %s", exc)

    def _apply_input(self, element, step: MacroStep) -> None:
        metadata = step.metadata or {}
        target_info = metadata.get("target", {}) if isinstance(metadata, dict) else {}
        tag = (target_info.get("tag") or "").lower()
        input_type = (target_info.get("inputType") or "").lower()

        if tag == "select":
            try:
                Select(element).select_by_value(step.value)
            except Exception as exc:  # noqa: BLE001 - we only log and continue
                LOGGER.warning("Unable to select value '%s': %s", step.value, exc)
            return

        if input_type in {"checkbox", "radio"}:
            target_checked = bool(target_info.get("checked"))
            current_checked = element.is_selected()
            if target_checked != current_checked:
                element.click()
            return

        try:
            element.clear()
        except WebDriverException:
            LOGGER.debug("Element does not support clear; continuing with send_keys.")

        if step.value:
            for character in step.value:
                element.send_keys(character)
                if self._typing_delay:
                    time.sleep(self._typing_delay)

    def _scroll_into_view(self, driver: WebDriver, element) -> None:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except WebDriverException:
            LOGGER.debug("Could not scroll element into view.")
