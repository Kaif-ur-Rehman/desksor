"""
desksor/reader.py

Reads the Windows UI Automation (UIA) accessibility tree using pywinauto.
Never crashes — always returns a valid response dict.
"""

import json
import time
import logging
from typing import Optional

logger = logging.getLogger("desksor.reader")


class Reader:
    """
    Reads the Windows accessibility tree for any open application.
    Uses pywinauto with the UIA backend.
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds between retries

    def get_all_windows(self) -> list:
        """
        Return a list of all currently open top-level windows.

        Returns:
            list of dicts: [{name, title, pid, handle}]
        """
        try:
            from pywinauto import Desktop

            desktop = Desktop(backend="uia")
            windows = desktop.windows()
            result = []
            for w in windows:
                try:
                    result.append(
                        {
                            "name": self._safe_str(w.window_text()),
                            "title": self._safe_str(w.window_text()),
                            "pid": self._safe_int(w.process_id()),
                            "handle": self._safe_int(w.handle),
                            "class_name": self._safe_str(w.class_name()),
                        }
                    )
                except Exception:
                    pass  # skip windows we can't read
            return result
        except Exception as exc:
            logger.error("get_all_windows failed: %s", exc)
            return []

    def read_app_tree(self, app_name: str) -> dict:
        """
        Read the full accessibility tree of an open application.

        Args:
            app_name: Partial or full name of the target application window.

        Returns:
            dict with keys:
                found (bool), window_title (str), tree (dict), error (str)
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                from pywinauto import Desktop

                desktop = Desktop(backend="uia")
                window = self._find_window(desktop, app_name)

                if window is None:
                    available = self._get_window_names(desktop)
                    if attempt < self.MAX_RETRIES:
                        logger.debug(
                            "App '%s' not found on attempt %d/%d, retrying…",
                            app_name,
                            attempt,
                            self.MAX_RETRIES,
                        )
                        time.sleep(self.RETRY_DELAY)
                        continue
                    return {
                        "found": False,
                        "window_title": None,
                        "tree": {},
                        "error": (
                            f"Could not find app '{app_name}'. "
                            f"Currently open apps: {', '.join(available) or 'none detected'}. "
                            f"Make sure the app is open and visible on screen."
                        ),
                    }

                tree = self._build_tree(window)
                return {
                    "found": True,
                    "window_title": self._safe_str(window.window_text()),
                    "tree": tree,
                    "error": None,
                }

            except Exception as exc:
                logger.warning(
                    "read_app_tree attempt %d/%d failed: %s",
                    attempt,
                    self.MAX_RETRIES,
                    exc,
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)

        return {
            "found": False,
            "window_title": None,
            "tree": {},
            "error": f"Failed to read app '{app_name}' after {self.MAX_RETRIES} attempts.",
        }

    def find_element(self, app_name: str, query: str) -> dict:
        """
        Search for elements whose name contains `query` (case-insensitive).

        Args:
            app_name: Target application name.
            query: Partial element name to search for.

        Returns:
            dict with keys:
                found (bool), matches (list), app_title (str), error (str)
        """
        tree_result = self.read_app_tree(app_name)

        if not tree_result["found"]:
            return {
                "found": False,
                "matches": [],
                "app_title": None,
                "error": tree_result["error"],
            }

        matches = []
        self._search_tree(tree_result["tree"], query.lower(), [], matches)

        if not matches:
            # Collect all available names for a helpful error
            all_names = []
            self._collect_names(tree_result["tree"], all_names)
            visible_names = [n for n in all_names if n][:20]
            return {
                "found": False,
                "matches": [],
                "app_title": tree_result["window_title"],
                "error": (
                    f"Could not find element '{query}' in {app_name}. "
                    f"Available elements: {', '.join(visible_names)}. "
                    f"Tip: use a partial name match — e.g. 'Save' matches 'Save As'."
                ),
            }

        return {
            "found": True,
            "matches": matches,
            "app_title": tree_result["window_title"],
            "error": None,
        }

    def get_window_object(self, app_name: str):
        """
        Return the raw pywinauto window object for an app.
        Used internally by executor.py.

        Returns None if not found.
        """
        try:
            from pywinauto import Desktop

            desktop = Desktop(backend="uia")
            return self._find_window(desktop, app_name)
        except Exception as exc:
            logger.error("get_window_object failed: %s", exc)
            return None

    # ─── Private helpers ────────────────────────────────────────────────────

    def _find_window(self, desktop, app_name: str):
        """
        Find a window whose title contains app_name (case-insensitive).
        Returns the pywinauto window wrapper or None.
        """
        app_lower = app_name.lower()
        try:
            windows = desktop.windows()
        except Exception:
            return None

        for w in windows:
            try:
                title = w.window_text().lower()
                if app_lower in title:
                    return w
            except Exception:
                pass
        return None

    def _get_window_names(self, desktop) -> list:
        """Return list of readable window titles."""
        names = []
        try:
            for w in desktop.windows():
                try:
                    name = w.window_text().strip()
                    if name:
                        names.append(name)
                except Exception:
                    pass
        except Exception:
            pass
        return names

    def _build_tree(self, wrapper, depth: int = 0, max_depth: int = 12) -> dict:
        """
        Recursively build a JSON-serialisable tree from a pywinauto wrapper.
        """
        if depth > max_depth:
            return {}

        try:
            rect = None
            try:
                r = wrapper.rectangle()
                rect = {
                    "left": r.left,
                    "top": r.top,
                    "right": r.right,
                    "bottom": r.bottom,
                    "width": r.right - r.left,
                    "height": r.bottom - r.top,
                }
            except Exception:
                rect = {"left": 0, "top": 0, "right": 0, "bottom": 0, "width": 0, "height": 0}

            value = ""
            try:
                value = self._safe_str(wrapper.get_value()) if hasattr(wrapper, "get_value") else ""
            except Exception:
                pass
            if not value:
                try:
                    value = self._safe_str(wrapper.window_text())
                except Exception:
                    value = ""

            enabled = True
            try:
                enabled = bool(wrapper.is_enabled())
            except Exception:
                pass

            visible = True
            try:
                visible = bool(wrapper.is_visible())
            except Exception:
                pass

            ctrl_type = ""
            try:
                ctrl_type = self._safe_str(wrapper.element_info.control_type)
            except Exception:
                try:
                    ctrl_type = self._safe_str(wrapper.friendly_class_name())
                except Exception:
                    ctrl_type = "Unknown"

            name = ""
            try:
                name = self._safe_str(wrapper.element_info.name)
            except Exception:
                try:
                    name = self._safe_str(wrapper.window_text())
                except Exception:
                    name = ""

            children = []
            try:
                for child in wrapper.children():
                    child_tree = self._build_tree(child, depth + 1, max_depth)
                    if child_tree:
                        children.append(child_tree)
            except Exception:
                pass

            return {
                "name": name,
                "control_type": ctrl_type,
                "value": value,
                "enabled": enabled,
                "visible": visible,
                "rectangle": rect,
                "children": children,
            }

        except Exception as exc:
            logger.debug("_build_tree error at depth %d: %s", depth, exc)
            return {}

    def _search_tree(self, node: dict, query_lower: str, path: list, results: list):
        """Recursively search the tree for nodes whose name contains query."""
        if not node:
            return

        name = node.get("name", "")
        if name and query_lower in name.lower():
            results.append(
                {
                    "name": name,
                    "control_type": node.get("control_type", ""),
                    "value": node.get("value", ""),
                    "enabled": node.get("enabled", True),
                    "visible": node.get("visible", True),
                    "rectangle": node.get("rectangle", {}),
                    "path": " > ".join(path + [name]),
                }
            )

        for child in node.get("children", []):
            self._search_tree(child, query_lower, path + [name], results)

    def _collect_names(self, node: dict, names: list):
        """Collect all non-empty element names from the tree."""
        if not node:
            return
        name = node.get("name", "")
        if name:
            names.append(name)
        for child in node.get("children", []):
            self._collect_names(child, names)

    @staticmethod
    def _safe_str(value) -> str:
        try:
            return str(value) if value is not None else ""
        except Exception:
            return ""

    @staticmethod
    def _safe_int(value) -> int:
        try:
            return int(value) if value is not None else 0
        except Exception:
            return 0
