from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List, Optional

from selenium.common.exceptions import JavascriptException, WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver

from ...domain.models import MacroStep
from ...domain.services import MacroRecorder, RecordingResult

LOGGER = logging.getLogger(__name__)


class SeleniumMacroRecorder(MacroRecorder):
    """Records user interactions in Firefox using Selenium."""

    def __init__(
        self,
        driver_factory: Callable[[], WebDriver],
        polling_interval: float = 0.5,
    ) -> None:
        self._driver_factory = driver_factory
        self._polling_interval = polling_interval
        self._driver: Optional[WebDriver] = None
        self._recording = False
        self._events: List[MacroStep] = []
        self._lock = threading.Lock()
        self._polling_thread: Optional[threading.Thread] = None
        self._start_url: str = ""

    def start(self, url: str) -> None:
        with self._lock:
            if self._recording:
                raise RuntimeError("A recording session is already running.")
            LOGGER.info("Starting Firefox for recording: %s", url)
            self._driver = self._driver_factory()
            self._driver.get(url)
            self._start_url = self._driver.current_url
            self._events = []
            self._inject_recorder()
            self._recording = True
            self._polling_thread = threading.Thread(target=self._poll_events, daemon=True)
            self._polling_thread.start()

    def stop(self) -> RecordingResult:
        with self._lock:
            if not self._recording or self._driver is None:
                raise RuntimeError("Recorder is not active.")
            LOGGER.info("Stopping recording session.")
            self._recording = False

        if self._polling_thread:
            self._polling_thread.join(timeout=3)

        final_events = self._fetch_events()
        if final_events:
            with self._lock:
                self._events.extend(final_events)

        metadata = {"title": self._safe_execute("return document.title;")}

        try:
            if self._driver:
                self._driver.quit()
        except WebDriverException as exc:
            LOGGER.warning("Error closing Firefox: %s", exc)
        finally:
            self._driver = None

        with self._lock:
            recorded_steps = list(self._events)

        return RecordingResult(
            start_url=self._start_url,
            steps=recorded_steps,
            metadata=metadata,
        )

    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    # Internal helpers -------------------------------------------------

    def _inject_recorder(self) -> None:
        if self._driver is None:
            raise RuntimeError("Driver not initialised")

        script = """
        (function() {
            if (window._gptparRecorderActive) {
                return;
            }
            window._gptparRecorderActive = true;
            window._gptparEvents = [];

            function cssPath(el) {
                if (!el || !el.nodeName) {
                    return null;
                }
                const path = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let selector = el.nodeName.toLowerCase();
                    if (el.id) {
                        selector += '#' + CSS.escape(el.id);
                        path.unshift(selector);
                        break;
                    } else {
                        let sib = el;
                        let nth = 1;
                        while (sib = sib.previousElementSibling) {
                            if (sib.nodeName.toLowerCase() === selector) {
                                nth += 1;
                            }
                        }
                        if (nth !== 1) {
                            selector += `:nth-of-type(${nth})`;
                        }
                    }
                    path.unshift(selector);
                    el = el.parentElement;
                }
                return path.join(' > ');
            }

            function targetDetails(target) {
                if (!target) {
                    return { tag: null, inputType: null, checked: null };
                }
                return {
                    tag: target.tagName ? target.tagName.toLowerCase() : null,
                    inputType: target.type || null,
                    checked: typeof target.checked === 'boolean' ? target.checked : null,
                };
            }

            function pushEvent(event) {
                window._gptparEvents.push(event);
            }

            document.addEventListener('click', function(evt) {
                const selector = cssPath(evt.target);
                pushEvent({
                    type: 'click',
                    selector: selector,
                    value: null,
                    timestamp: Date.now(),
                    button: evt.button,
                    target: targetDetails(evt.target),
                });
            }, true);

            document.addEventListener('input', function(evt) {
                const selector = cssPath(evt.target);
                pushEvent({
                    type: 'input',
                    selector: selector,
                    value: evt.target && 'value' in evt.target ? evt.target.value : null,
                    timestamp: Date.now(),
                    target: targetDetails(evt.target),
                });
            }, true);

            document.addEventListener('change', function(evt) {
                const selector = cssPath(evt.target);
                pushEvent({
                    type: 'change',
                    selector: selector,
                    value: evt.target && 'value' in evt.target ? evt.target.value : null,
                    timestamp: Date.now(),
                    target: targetDetails(evt.target),
                });
            }, true);
        })();
        """

        try:
            self._driver.execute_script(script)
        except JavascriptException as exc:
            LOGGER.error("Failed to inject recorder script: %s", exc)
            raise

    def _poll_events(self) -> None:
        while True:
            with self._lock:
                if not self._recording or self._driver is None:
                    break
            events = self._fetch_events()
            if events:
                with self._lock:
                    self._events.extend(events)
            time.sleep(self._polling_interval)

    def _fetch_events(self) -> List[MacroStep]:
        driver = self._driver
        if driver is None:
            return []
        try:
            raw_events = driver.execute_script(
                """
                if (!window._gptparEvents) {
                    return [];
                }
                const events = window._gptparEvents.slice();
                window._gptparEvents.length = 0;
                return events;
                """
            )
        except JavascriptException as exc:
            LOGGER.warning("Could not fetch recorded events: %s", exc)
            return []

        macro_steps: List[MacroStep] = []
        for event in raw_events or []:
            if not isinstance(event, dict):
                continue
            macro_steps.append(self._convert_event(event))
        return macro_steps

    @staticmethod
    def _convert_event(event: dict) -> MacroStep:
        metadata = {
            key: value
            for key, value in event.items()
            if key not in {"type", "selector", "value"}
        }
        return MacroStep(
            action=event.get("type", "unknown"),
            selector=event.get("selector"),
            value=event.get("value"),
            metadata=metadata,
        )

    def _safe_execute(self, script: str) -> Optional[str]:
        driver = self._driver
        if driver is None:
            return None
        try:
            return driver.execute_script(script)
        except JavascriptException:
            return None
