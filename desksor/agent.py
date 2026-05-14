"""
desksor/agent.py

Main Agent class — the primary interface developers use.

All methods are async and return:
    {"success": bool, "data": any, "error": str | None, "time_ms": int}

Nothing is ever raised to the caller — errors are captured and returned as
success:false with a helpful error message.
"""

import asyncio
import logging
import subprocess
import sys
import time
from typing import Any, Optional

import psutil
import pyautogui

from desksor.reader import Reader
from desksor.executor import Executor
from desksor.browser import Browser
from desksor.filesystem import FileSystem

# ─── Logging setup ──────────────────────────────────────────────────────────

_log_format = "[%(asctime)s] %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=_log_format,
    handlers=[
        logging.FileHandler("desksor.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("desksor.agent")


# ─── SystemInfo ─────────────────────────────────────────────────────────────


class SystemInfo:
    """Lightweight system information provider using psutil."""

    def get_info(self) -> dict:
        t0 = time.perf_counter()
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            return _ok(
                {
                    "cpu_percent": cpu,
                    "ram_total_gb": round(mem.total / 1e9, 2),
                    "ram_used_gb": round(mem.used / 1e9, 2),
                    "ram_percent": mem.percent,
                    "disk_total_gb": round(disk.total / 1e9, 2),
                    "disk_used_gb": round(disk.used / 1e9, 2),
                    "disk_percent": disk.percent,
                    "platform": sys.platform,
                    "python_version": sys.version,
                },
                t0,
            )
        except Exception as exc:
            return _err(str(exc), t0)

    def get_processes(self) -> dict:
        t0 = time.perf_counter()
        try:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
                try:
                    procs.append(
                        {
                            "pid": p.info["pid"],
                            "name": p.info["name"],
                            "cpu_percent": p.info["cpu_percent"],
                            "memory_percent": round(p.info["memory_percent"] or 0, 2),
                            "status": p.info["status"],
                        }
                    )
                except Exception:
                    pass
            procs.sort(key=lambda x: x["memory_percent"], reverse=True)
            return _ok({"processes": procs[:100], "total_count": len(procs)}, t0)
        except Exception as exc:
            return _err(str(exc), t0)

    def get_clipboard(self) -> dict:
        t0 = time.perf_counter()
        try:
            import ctypes

            CF_UNICODETEXT = 13
            ctypes.windll.user32.OpenClipboard(0)
            try:
                handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                if handle:
                    ptr = ctypes.cast(handle, ctypes.c_wchar_p)
                    content = ptr.value or ""
                else:
                    content = ""
            finally:
                ctypes.windll.user32.CloseClipboard()
            return _ok({"content": content, "length": len(content)}, t0)
        except Exception as exc:
            return _err(str(exc), t0)


# ─── Helpers ────────────────────────────────────────────────────────────────


def _ok(data: Any, t0: float) -> dict:
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    if elapsed_ms > 500:
        logger.warning("Action took %d ms — exceeds 500ms target.", elapsed_ms)
    return {"success": True, "data": data, "error": None, "time_ms": elapsed_ms}


def _err(error: str, t0: float) -> dict:
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {"success": False, "data": None, "error": error, "time_ms": elapsed_ms}


def _log_action(app: str, action: str, element: str, result: dict):
    status = "OK" if result["success"] else "FAIL"
    logger.info(
        "[%s] [%s] [%s] [%s] [%s] [%dms]",
        app or "system",
        action,
        element or "-",
        status,
        result.get("error") or "",
        result.get("time_ms", 0),
    )


# ─── Agent ──────────────────────────────────────────────────────────────────


class Agent:
    """
    Main Desksor agent. Gives AI agents eyes and hands on Windows.

    Usage:
        from desksor import Agent
        agent = Agent()
        result = await agent.click("Excel", "Save")
        # or synchronously:
        result = asyncio.run(agent.click("Excel", "Save"))
    """

    def __init__(self):
        self.reader = Reader()
        self.executor = Executor()
        self.browser = Browser()
        self.files = FileSystem()
        self.system = SystemInfo()
        logger.info("Desksor Agent initialized.")

    # ═══════════════════════════════════════════════════════════════════════
    # READ METHODS
    # ═══════════════════════════════════════════════════════════════════════

    async def read(self, app_name: str) -> dict:
        """
        Read the full accessibility tree of any open application.

        Args:
            app_name: Partial or full application name (e.g. "Excel", "Notepad")

        Returns:
            success: True with data containing the full element tree.
            success: False with helpful error listing available apps.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.reader.read_app_tree, app_name
            )
            if not result["found"]:
                r = _err(result["error"], t0)
                _log_action(app_name, "read", "", r)
                return r
            r = _ok(
                {
                    "app": app_name,
                    "window_title": result["window_title"],
                    "tree": result["tree"],
                },
                t0,
            )
            _log_action(app_name, "read", "", r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "read", "", r)
            return r

    async def find(self, app_name: str, query: str) -> dict:
        """
        Search for a specific element by name within an application.

        Args:
            app_name: Application name.
            query: Partial element name to search for.

        Returns:
            success: True with list of matching elements and their positions.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.reader.find_element, app_name, query
            )
            if not result["found"]:
                r = _err(result["error"], t0)
            else:
                r = _ok(
                    {
                        "app": app_name,
                        "query": query,
                        "matches": result["matches"],
                        "count": len(result["matches"]),
                    },
                    t0,
                )
            _log_action(app_name, "find", query, r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "find", query, r)
            return r

    async def get_open_apps(self) -> dict:
        """
        Return a list of all currently open applications.

        Returns:
            success: True with list of {name, title, pid, handle}.
        """
        t0 = time.perf_counter()
        try:
            windows = await asyncio.get_event_loop().run_in_executor(
                None, self.reader.get_all_windows
            )
            r = _ok({"apps": windows, "count": len(windows)}, t0)
            _log_action("system", "get_open_apps", "", r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action("system", "get_open_apps", "", r)
            return r

    async def read_element(self, app_name: str, element_name: str) -> dict:
        """
        Read the current value/text of a specific element.

        Args:
            app_name: Application name.
            element_name: Name of the element to read.

        Returns:
            success: True with element's current value/text/state.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.reader.find_element, app_name, element_name
            )
            if not result["found"]:
                r = _err(result["error"], t0)
            else:
                matches = result["matches"]
                r = _ok(
                    {
                        "app": app_name,
                        "element_name": element_name,
                        "elements": matches,
                        "value": matches[0].get("value", "") if matches else "",
                    },
                    t0,
                )
            _log_action(app_name, "read_element", element_name, r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "read_element", element_name, r)
            return r

    # ═══════════════════════════════════════════════════════════════════════
    # ACTION METHODS
    # ═══════════════════════════════════════════════════════════════════════

    async def click(self, app_name: str, element_name: str) -> dict:
        """
        Click an element in an application by name.

        Args:
            app_name: Application name (e.g. "Excel", "Notepad").
            element_name: Element to click (e.g. "Save", "File", "OK").

        Returns:
            success: True with time_ms it took.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.click_element, app_name, element_name, "left", False
            )
            _log_action(app_name, "click", element_name, result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "click", element_name, r)
            return r

    async def double_click(self, app_name: str, element_name: str) -> dict:
        """Double-click an element in an application by name."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.click_element, app_name, element_name, "left", True
            )
            _log_action(app_name, "double_click", element_name, result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "double_click", element_name, r)
            return r

    async def right_click(self, app_name: str, element_name: str) -> dict:
        """Right-click an element in an application by name."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.click_element, app_name, element_name, "right", False
            )
            _log_action(app_name, "right_click", element_name, result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "right_click", element_name, r)
            return r

    async def type(self, app_name: str, element_name: str, text: str) -> dict:
        """
        Type text into an element in an application.
        Clears any existing content first.

        Args:
            app_name: Application name.
            element_name: Element to type into (e.g. "Address Bar", "Search").
            text: Text to type.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.type_into_element, app_name, element_name, text
            )
            _log_action(app_name, "type", element_name, result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "type", element_name, r)
            return r

    async def key_press(self, keys: str) -> dict:
        """
        Press a keyboard shortcut.

        Args:
            keys: Key combination string, e.g. "ctrl+s", "alt+f4", "enter", "escape".

        Returns:
            success: True with the key combination that was pressed.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.execute_keyboard, keys
            )
            _log_action("system", "key_press", keys, result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action("system", "key_press", keys, r)
            return r

    async def scroll(self, app_name: str, direction: str, amount: int = 3) -> dict:
        """
        Scroll within an application.

        Args:
            app_name: Application name.
            direction: "up", "down", "left", or "right".
            amount: Number of scroll steps (default 3).
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.scroll_app, app_name, direction, amount
            )
            _log_action(app_name, "scroll", direction, result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "scroll", direction, r)
            return r

    async def open_app(self, app_name: str) -> dict:
        """
        Open an installed application and wait for it to be ready.

        Args:
            app_name: Application name (e.g. "notepad", "calc", "explorer").

        Returns:
            success: True once the app window is detected.
        """
        t0 = time.perf_counter()
        try:
            # Map common names to executable names
            exe_map = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "explorer": "explorer.exe",
                "wordpad": "wordpad.exe",
                "paint": "mspaint.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "edge": "msedge.exe",
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "excel": "excel.exe",
                "word": "winword.exe",
                "powerpoint": "powerpnt.exe",
                "outlook": "outlook.exe",
                "teams": "teams.exe",
                "vscode": "code.exe",
                "code": "code.exe",
            }

            exe = exe_map.get(app_name.lower(), f"{app_name}.exe")

            def _open():
                subprocess.Popen(exe, shell=True)
                # Wait up to 10s for the window to appear
                deadline = time.time() + 10
                while time.time() < deadline:
                    time.sleep(0.5)
                    windows = self.reader.get_all_windows()
                    for w in windows:
                        if app_name.lower() in (w.get("name") or "").lower():
                            return True
                return False

            found = await asyncio.get_event_loop().run_in_executor(None, _open)
            if found:
                r = _ok({"app": app_name, "exe": exe}, t0)
            else:
                r = _err(
                    f"Launched '{exe}' but window did not appear within 10 seconds. "
                    f"App may have opened in the background or under a different name.",
                    t0,
                )
            _log_action(app_name, "open_app", "", r)
            return r
        except FileNotFoundError:
            r = _err(
                f"Could not find '{app_name}'. Make sure the application is installed "
                f"and its executable is in your system PATH.",
                t0,
            )
            _log_action(app_name, "open_app", "", r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "open_app", "", r)
            return r

    async def close_app(self, app_name: str) -> dict:
        """
        Close an application gracefully using Alt+F4 after focusing it.

        Args:
            app_name: Application name.
        """
        t0 = time.perf_counter()
        try:
            def _close():
                window = self.reader.get_window_object(app_name)
                if window is None:
                    return False, f"App '{app_name}' is not currently open."
                try:
                    window.set_focus()
                    time.sleep(0.1)
                    window.close()
                    return True, None
                except Exception:
                    # Fallback: Alt+F4
                    import pyautogui
                    pyautogui.hotkey("alt", "f4")
                    return True, None

            success, error = await asyncio.get_event_loop().run_in_executor(None, _close)
            if success:
                r = _ok({"app": app_name}, t0)
            else:
                r = _err(error, t0)
            _log_action(app_name, "close_app", "", r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "close_app", "", r)
            return r

    async def save_app(self, app_name: str) -> dict:
        """
        Save the current document in any application using Ctrl+S.
        Handles save dialogs by pressing Enter if they appear.

        Args:
            app_name: Application name.
        """
        t0 = time.perf_counter()
        try:
            def _save():
                window = self.reader.get_window_object(app_name)
                if window is None:
                    return False, f"App '{app_name}' is not currently open."
                try:
                    window.set_focus()
                    time.sleep(0.05)
                except Exception:
                    pass

                import pyautogui
                pyautogui.hotkey("ctrl", "s")
                time.sleep(0.5)

                # Check for save dialog and dismiss with Enter
                windows = self.reader.get_all_windows()
                for w in windows:
                    wname = (w.get("name") or "").lower()
                    if any(word in wname for word in ("save as", "save", "overwrite")):
                        pyautogui.press("enter")
                        time.sleep(0.3)
                        break

                return True, None

            success, error = await asyncio.get_event_loop().run_in_executor(None, _save)
            if success:
                r = _ok({"app": app_name, "method": "ctrl+s"}, t0)
            else:
                r = _err(error, t0)
            _log_action(app_name, "save_app", "", r)
            return r
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action(app_name, "save_app", "", r)
            return r

    # ═══════════════════════════════════════════════════════════════════════
    # MOUSE METHODS
    # ═══════════════════════════════════════════════════════════════════════

    async def move_mouse(self, x: int, y: int) -> dict:
        """Move mouse to absolute screen coordinates."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.move_mouse, x, y
            )
            _log_action("system", "move_mouse", f"{x},{y}", result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action("system", "move_mouse", f"{x},{y}", r)
            return r

    async def click_position(self, x: int, y: int) -> dict:
        """
        Click at exact screen coordinates.
        Use only when the accessibility tree approach doesn't work.
        """
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.click_position, x, y, "left", False
            )
            _log_action("system", "click_position", f"{x},{y}", result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action("system", "click_position", f"{x},{y}", r)
            return r

    async def drag(self, x1: int, y1: int, x2: int, y2: int) -> dict:
        """Drag from (x1, y1) to (x2, y2)."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.drag_mouse, x1, y1, x2, y2
            )
            _log_action("system", "drag", f"{x1},{y1}→{x2},{y2}", result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action("system", "drag", f"{x1},{y1}→{x2},{y2}", r)
            return r

    async def get_cursor_position(self) -> dict:
        """Return the current x, y position of the mouse cursor."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.executor.get_cursor_position
            )
            _log_action("system", "get_cursor_position", "", result)
            return result
        except Exception as exc:
            r = _err(str(exc), t0)
            _log_action("system", "get_cursor_position", "", r)
            return r

    # ═══════════════════════════════════════════════════════════════════════
    # BROWSER METHODS (convenience pass-throughs)
    # ═══════════════════════════════════════════════════════════════════════

    async def browser_console(self, tab_id: Optional[str] = None) -> dict:
        """Read all console messages from the active browser tab."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.browser.read_console, tab_id
            )
            _log_action("browser", "console", "", result)
            return result
        except Exception as exc:
            return _err(str(exc), t0)

    async def browser_network(self, tab_id: Optional[str] = None) -> dict:
        """Read all network requests from the active browser tab."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.browser.read_network, tab_id
            )
            _log_action("browser", "network", "", result)
            return result
        except Exception as exc:
            return _err(str(exc), t0)

    async def browser_page(self, tab_id: Optional[str] = None) -> dict:
        """Read the DOM structure of the current browser page."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.browser.read_page, tab_id
            )
            _log_action("browser", "page", "", result)
            return result
        except Exception as exc:
            return _err(str(exc), t0)

    async def browser_tabs(self) -> dict:
        """Return a list of all open browser tabs."""
        t0 = time.perf_counter()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.browser.read_tabs
            )
            _log_action("browser", "tabs", "", result)
            return result
        except Exception as exc:
            return _err(str(exc), t0)

    # ═══════════════════════════════════════════════════════════════════════
    # SYSTEM METHODS (convenience pass-throughs)
    # ═══════════════════════════════════════════════════════════════════════

    async def system_info(self) -> dict:
        """Return CPU, RAM, disk info."""
        return await asyncio.get_event_loop().run_in_executor(None, self.system.get_info)

    async def system_processes(self) -> dict:
        """Return running processes sorted by memory usage."""
        return await asyncio.get_event_loop().run_in_executor(None, self.system.get_processes)

    async def system_clipboard(self) -> dict:
        """Return current clipboard content."""
        return await asyncio.get_event_loop().run_in_executor(None, self.system.get_clipboard)
