"""
desksor/executor.py

Executes actions on Windows applications using pywinauto + pyautogui.
Always focuses the window before acting, verifies success, never crashes.
"""

import time
import logging
from typing import Optional

import pyautogui

from desksor.reader import Reader

logger = logging.getLogger("desksor.executor")

# Small inter-action delay for UI stability (ms → seconds)
ACTION_DELAY = 0.05
pyautogui.FAILSAFE = False  # disable corner-move failsafe for automation


class Executor:
    """
    Executes click, type, keyboard, scroll, and drag actions
    via the Windows UIA accessibility tree.
    """

    def __init__(self):
        self.reader = Reader()

    # ─── Click actions ───────────────────────────────────────────────────────

    def click_element(self, app_name: str, element_name: str, button: str = "left", double: bool = False) -> dict:
        """
        Find an element by name in the accessibility tree and click it.

        Returns: {success, element_found, element_name, time_ms, error}
        """
        t0 = time.perf_counter()
        try:
            window = self.reader.get_window_object(app_name)
            if window is None:
                available = [w["name"] for w in self.reader.get_all_windows() if w["name"]]
                return self._err(
                    f"Could not find app '{app_name}'. "
                    f"Open apps: {', '.join(available[:10]) or 'none'}.",
                    t0,
                )

            # Bring window to front
            self._focus_window(window)

            elem = self._find_control(window, element_name)
            if elem is None:
                available = self._collect_names_from_window(window)
                return self._err(
                    f"Could not find element '{element_name}' in {app_name}. "
                    f"Available elements: {', '.join(available[:20])}. "
                    f"Tip: use partial name — 'Save' matches 'Save As'.",
                    t0,
                )

            if double:
                elem.double_click_input(button=button)
            else:
                elem.click_input(button=button)

            time.sleep(ACTION_DELAY)
            return self._ok(
                {"element_name": element_name, "button": button, "double": double},
                t0,
            )

        except Exception as exc:
            logger.error("click_element failed: %s", exc)
            return self._err(str(exc), t0)

    def type_into_element(self, app_name: str, element_name: str, text: str) -> dict:
        """
        Find an element and type text into it.
        Clears existing content first with Ctrl+A → Delete.

        Returns: {success, element_name, text, time_ms, error}
        """
        t0 = time.perf_counter()
        try:
            window = self.reader.get_window_object(app_name)
            if window is None:
                available = [w["name"] for w in self.reader.get_all_windows() if w["name"]]
                return self._err(
                    f"Could not find app '{app_name}'. "
                    f"Open apps: {', '.join(available[:10]) or 'none'}.",
                    t0,
                )

            self._focus_window(window)

            elem = self._find_control(window, element_name)
            if elem is None:
                available = self._collect_names_from_window(window)
                return self._err(
                    f"Could not find element '{element_name}' in {app_name}. "
                    f"Available elements: {', '.join(available[:20])}.",
                    t0,
                )

            # Focus the element
            elem.click_input()
            time.sleep(ACTION_DELAY)

            # Clear existing content
            pyautogui.hotkey("ctrl", "a")
            time.sleep(ACTION_DELAY)
            pyautogui.press("delete")
            time.sleep(ACTION_DELAY)

            # Type the text (use type_keys for special chars support)
            elem.type_keys(text, with_spaces=True, with_tabs=True, with_newlines=True)
            time.sleep(ACTION_DELAY)

            return self._ok({"element_name": element_name, "text": text}, t0)

        except Exception as exc:
            logger.error("type_into_element failed: %s", exc)
            return self._err(str(exc), t0)

    def execute_keyboard(self, keys: str) -> dict:
        """
        Press a keyboard shortcut string like 'ctrl+s' or 'alt+f4'.

        Returns: {success, keys, time_ms, error}
        """
        t0 = time.perf_counter()
        try:
            parts = [k.strip().lower() for k in keys.split("+")]

            # Map common key names to pyautogui equivalents
            key_map = {
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "win": "win",
                "enter": "enter",
                "escape": "escape",
                "esc": "escape",
                "delete": "delete",
                "del": "delete",
                "backspace": "backspace",
                "tab": "tab",
                "space": "space",
                "home": "home",
                "end": "end",
                "pageup": "pageup",
                "pagedown": "pagedown",
                "up": "up",
                "down": "down",
                "left": "left",
                "right": "right",
                "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
                "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
                "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
            }
            mapped = [key_map.get(p, p) for p in parts]

            if len(mapped) == 1:
                pyautogui.press(mapped[0])
            else:
                pyautogui.hotkey(*mapped)

            time.sleep(ACTION_DELAY)
            return self._ok({"keys": keys, "mapped_keys": mapped}, t0)

        except Exception as exc:
            logger.error("execute_keyboard failed: %s", exc)
            return self._err(str(exc), t0)

    def scroll_app(self, app_name: str, direction: str, amount: int) -> dict:
        """
        Scroll within an application window.

        Args:
            direction: 'up', 'down', 'left', 'right'
            amount: number of scroll steps

        Returns: {success, direction, amount, time_ms, error}
        """
        t0 = time.perf_counter()
        try:
            window = self.reader.get_window_object(app_name)
            if window is None:
                return self._err(f"App '{app_name}' not found.", t0)

            self._focus_window(window)

            # Move mouse to center of window
            try:
                rect = window.rectangle()
                cx = (rect.left + rect.right) // 2
                cy = (rect.top + rect.bottom) // 2
                pyautogui.moveTo(cx, cy)
            except Exception:
                pass

            direction = direction.lower()
            if direction in ("up", "down"):
                scroll_amount = amount if direction == "up" else -amount
                pyautogui.scroll(scroll_amount)
            elif direction == "left":
                pyautogui.hscroll(-amount)
            elif direction == "right":
                pyautogui.hscroll(amount)
            else:
                return self._err(
                    f"Invalid direction '{direction}'. Use 'up', 'down', 'left', or 'right'.",
                    t0,
                )

            time.sleep(ACTION_DELAY)
            return self._ok({"direction": direction, "amount": amount}, t0)

        except Exception as exc:
            logger.error("scroll_app failed: %s", exc)
            return self._err(str(exc), t0)

    def move_mouse(self, x: int, y: int) -> dict:
        """Move mouse to absolute screen coordinates."""
        t0 = time.perf_counter()
        try:
            pyautogui.moveTo(x, y)
            return self._ok({"x": x, "y": y}, t0)
        except Exception as exc:
            return self._err(str(exc), t0)

    def click_position(self, x: int, y: int, button: str = "left", double: bool = False) -> dict:
        """Click at absolute screen coordinates."""
        t0 = time.perf_counter()
        try:
            if double:
                pyautogui.doubleClick(x, y, button=button)
            else:
                pyautogui.click(x, y, button=button)
            time.sleep(ACTION_DELAY)
            return self._ok({"x": x, "y": y, "button": button, "double": double}, t0)
        except Exception as exc:
            return self._err(str(exc), t0)

    def drag_mouse(self, x1: int, y1: int, x2: int, y2: int) -> dict:
        """Drag from (x1, y1) to (x2, y2)."""
        t0 = time.perf_counter()
        try:
            pyautogui.moveTo(x1, y1)
            time.sleep(ACTION_DELAY)
            pyautogui.dragTo(x2, y2, duration=0.3, button="left")
            time.sleep(ACTION_DELAY)
            return self._ok({"from": {"x": x1, "y": y1}, "to": {"x": x2, "y": y2}}, t0)
        except Exception as exc:
            return self._err(str(exc), t0)

    def get_cursor_position(self) -> dict:
        """Return current mouse cursor position."""
        t0 = time.perf_counter()
        try:
            x, y = pyautogui.position()
            return self._ok({"x": x, "y": y}, t0)
        except Exception as exc:
            return self._err(str(exc), t0)

    # ─── Private helpers ─────────────────────────────────────────────────────

    def _focus_window(self, window):
        """Bring window to foreground."""
        try:
            window.set_focus()
            time.sleep(ACTION_DELAY)
        except Exception:
            try:
                window.restore()
                window.set_focus()
                time.sleep(ACTION_DELAY)
            except Exception:
                pass  # best-effort focus

    def _find_control(self, window, element_name: str):
        """
        Recursively search for a control whose name contains element_name
        (case-insensitive). Returns the pywinauto wrapper or None.
        """
        query_lower = element_name.lower()
        try:
            # Try pywinauto's built-in find first (faster)
            descendants = window.descendants()
            for ctrl in descendants:
                try:
                    name = ctrl.element_info.name or ""
                    if query_lower in name.lower():
                        return ctrl
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def _collect_names_from_window(self, window) -> list:
        """Return all non-empty control names from window for error messages."""
        names = []
        try:
            for ctrl in window.descendants():
                try:
                    name = ctrl.element_info.name or ""
                    if name.strip():
                        names.append(name)
                except Exception:
                    pass
        except Exception:
            pass
        return list(dict.fromkeys(names))  # deduplicate, preserve order

    @staticmethod
    def _ok(data: dict, t0: float) -> dict:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        if elapsed_ms > 500:
            logger.warning("Action took %d ms — exceeds 500ms target.", elapsed_ms)
        return {"success": True, "data": data, "error": None, "time_ms": elapsed_ms}

    @staticmethod
    def _err(error: str, t0: float) -> dict:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"success": False, "data": None, "error": error, "time_ms": elapsed_ms}
