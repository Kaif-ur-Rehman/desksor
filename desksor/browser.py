"""
desksor/browser.py

Reads Chrome/Edge browser state through the Chrome DevTools Protocol (CDP).
Chrome must be launched with --remote-debugging-port=9222.
"""

import json
import time
import asyncio
import logging
from typing import Optional

import requests

logger = logging.getLogger("desksor.browser")

CDP_HTTP = "http://localhost:9222"
CDP_TIMEOUT = 5  # seconds for HTTP requests

CHROME_LAUNCH_HINT = (
    "Chrome is not running in debug mode. "
    "Launch Chrome with:\n\n"
    "  chrome.exe --remote-debugging-port=9222\n\n"
    "Or Edge:\n\n"
    "  msedge.exe --remote-debugging-port=9222\n\n"
    "You can add this flag by creating a shortcut and editing its target."
)


class Browser:
    """
    Reads Chrome/Edge browser state via the Chrome DevTools Protocol.
    All methods return {success, data, error, time_ms}.
    """

    def read_tabs(self) -> dict:
        """
        Return a list of all open browser tabs.

        Returns: {success, data: [{id, title, url, type, active}], error, time_ms}
        """
        t0 = time.perf_counter()
        try:
            resp = requests.get(f"{CDP_HTTP}/json", timeout=CDP_TIMEOUT)
            resp.raise_for_status()
            tabs = resp.json()
            cleaned = []
            for t in tabs:
                cleaned.append(
                    {
                        "id": t.get("id", ""),
                        "title": t.get("title", ""),
                        "url": t.get("url", ""),
                        "type": t.get("type", ""),
                        "websocket_url": t.get("webSocketDebuggerUrl", ""),
                    }
                )
            return self._ok({"tabs": cleaned, "count": len(cleaned)}, t0)
        except requests.exceptions.ConnectionError:
            return self._err(CHROME_LAUNCH_HINT, t0)
        except Exception as exc:
            return self._err(str(exc), t0)

    def get_active_tab(self) -> dict:
        """
        Return the currently active/focused browser tab.

        Returns: {success, data: {id, title, url, websocket_url}, error, time_ms}
        """
        t0 = time.perf_counter()
        try:
            resp = requests.get(f"{CDP_HTTP}/json", timeout=CDP_TIMEOUT)
            resp.raise_for_status()
            tabs = resp.json()

            # Active tab is typically first in the list that is a 'page' type
            page_tabs = [t for t in tabs if t.get("type") == "page"]
            if not page_tabs:
                return self._err("No active browser page found.", t0)

            active = page_tabs[0]
            return self._ok(
                {
                    "id": active.get("id", ""),
                    "title": active.get("title", ""),
                    "url": active.get("url", ""),
                    "websocket_url": active.get("webSocketDebuggerUrl", ""),
                },
                t0,
            )
        except requests.exceptions.ConnectionError:
            return self._err(CHROME_LAUNCH_HINT, t0)
        except Exception as exc:
            return self._err(str(exc), t0)

    def read_console(self, tab_id: Optional[str] = None) -> dict:
        """
        Retrieve console messages from the browser via CDP.

        Returns: {success, data: {messages: [{level, text, url, line}]}, error, time_ms}
        """
        t0 = time.perf_counter()
        try:
            ws_url = self._get_ws_url(tab_id)
            if ws_url is None:
                return self._err(CHROME_LAUNCH_HINT, t0)

            messages = asyncio.run(self._cdp_get_console(ws_url))
            return self._ok({"messages": messages, "count": len(messages)}, t0)
        except requests.exceptions.ConnectionError:
            return self._err(CHROME_LAUNCH_HINT, t0)
        except Exception as exc:
            logger.error("read_console failed: %s", exc)
            return self._err(str(exc), t0)

    def read_network(self, tab_id: Optional[str] = None) -> dict:
        """
        Retrieve network requests captured since page load.

        Returns: {success, data: {requests: [{url, method, status, mime_type, time_ms}]}, error, time_ms}
        """
        t0 = time.perf_counter()
        try:
            ws_url = self._get_ws_url(tab_id)
            if ws_url is None:
                return self._err(CHROME_LAUNCH_HINT, t0)

            requests_list = asyncio.run(self._cdp_get_network(ws_url))
            return self._ok({"requests": requests_list, "count": len(requests_list)}, t0)
        except requests.exceptions.ConnectionError:
            return self._err(CHROME_LAUNCH_HINT, t0)
        except Exception as exc:
            logger.error("read_network failed: %s", exc)
            return self._err(str(exc), t0)

    def read_page(self, tab_id: Optional[str] = None) -> dict:
        """
        Get the full DOM structure and all interactive elements of the current page.

        Returns: {success, data: {title, url, elements: [...]}, error, time_ms}
        """
        t0 = time.perf_counter()
        try:
            ws_url = self._get_ws_url(tab_id)
            if ws_url is None:
                return self._err(CHROME_LAUNCH_HINT, t0)

            page_data = asyncio.run(self._cdp_get_page(ws_url))
            return self._ok(page_data, t0)
        except requests.exceptions.ConnectionError:
            return self._err(CHROME_LAUNCH_HINT, t0)
        except Exception as exc:
            logger.error("read_page failed: %s", exc)
            return self._err(str(exc), t0)

    # ─── CDP async helpers ───────────────────────────────────────────────────

    async def _cdp_send(self, ws, method: str, params: dict = None, msg_id: int = 1) -> dict:
        """Send a CDP command and await the response."""
        import websockets

        cmd = json.dumps({"id": msg_id, "method": method, "params": params or {}})
        await ws.send(cmd)

        # Wait for response matching our id
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
                msg = json.loads(raw)
                if msg.get("id") == msg_id:
                    return msg.get("result", {})
            except asyncio.TimeoutError:
                break
            except Exception:
                break
        return {}

    async def _cdp_get_console(self, ws_url: str) -> list:
        """Use CDP Runtime.evaluate to get console messages via injected listener."""
        import websockets

        messages = []
        try:
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                # Enable Runtime and Log domains
                await self._cdp_send(ws, "Runtime.enable", {}, msg_id=1)
                await self._cdp_send(ws, "Log.enable", {}, msg_id=2)

                # Get existing log entries
                result = await self._cdp_send(ws, "Log.entries", {}, msg_id=3)
                entries = result.get("entries", [])
                for entry in entries:
                    messages.append(
                        {
                            "level": entry.get("level", "info"),
                            "text": entry.get("text", ""),
                            "url": entry.get("url", ""),
                            "line": entry.get("lineNumber", 0),
                            "timestamp": entry.get("timestamp", 0),
                            "source": entry.get("source", ""),
                        }
                    )
        except Exception as exc:
            logger.debug("_cdp_get_console error: %s", exc)
        return messages

    async def _cdp_get_network(self, ws_url: str) -> list:
        """Use CDP to capture network activity. Returns requests collected over 1.5s."""
        import websockets

        collected = []
        try:
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                await self._cdp_send(ws, "Network.enable", {}, msg_id=1)

                # Collect events for 1.5 seconds
                deadline = time.time() + 1.5
                req_id = 10
                while time.time() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=0.2)
                        msg = json.loads(raw)
                        method = msg.get("method", "")
                        params = msg.get("params", {})

                        if method == "Network.responseReceived":
                            resp = params.get("response", {})
                            collected.append(
                                {
                                    "url": resp.get("url", ""),
                                    "method": params.get("type", ""),
                                    "status": resp.get("status", 0),
                                    "mime_type": resp.get("mimeType", ""),
                                    "time_ms": int(resp.get("timing", {}).get("receiveHeadersEnd", 0)),
                                    "request_id": params.get("requestId", ""),
                                }
                            )
                        elif method == "Network.requestWillBeSent":
                            req = params.get("request", {})
                            collected.append(
                                {
                                    "url": req.get("url", ""),
                                    "method": req.get("method", ""),
                                    "status": "pending",
                                    "mime_type": "",
                                    "time_ms": 0,
                                    "request_id": params.get("requestId", ""),
                                }
                            )
                    except asyncio.TimeoutError:
                        pass
        except Exception as exc:
            logger.debug("_cdp_get_network error: %s", exc)
        return collected

    async def _cdp_get_page(self, ws_url: str) -> dict:
        """Extract page title, URL, and interactive elements via Runtime.evaluate."""
        import websockets

        try:
            async with websockets.connect(ws_url, open_timeout=5) as ws:
                await self._cdp_send(ws, "Runtime.enable", {}, msg_id=1)

                # Get page title and URL
                title_result = await self._cdp_send(
                    ws,
                    "Runtime.evaluate",
                    {"expression": "document.title", "returnByValue": True},
                    msg_id=2,
                )
                title = title_result.get("result", {}).get("value", "")

                url_result = await self._cdp_send(
                    ws,
                    "Runtime.evaluate",
                    {"expression": "window.location.href", "returnByValue": True},
                    msg_id=3,
                )
                url = url_result.get("result", {}).get("value", "")

                # Get all interactive elements
                js = """
                (function() {
                    var selectors = 'a, button, input, select, textarea, [role="button"], [role="link"], [tabindex]';
                    var els = Array.from(document.querySelectorAll(selectors));
                    return els.slice(0, 200).map(function(el) {
                        var rect = el.getBoundingClientRect();
                        return {
                            tag: el.tagName.toLowerCase(),
                            type: el.type || '',
                            id: el.id || '',
                            name: el.name || '',
                            text: (el.innerText || el.value || el.placeholder || '').substring(0, 200),
                            href: el.href || '',
                            visible: rect.width > 0 && rect.height > 0,
                            rect: {left: Math.round(rect.left), top: Math.round(rect.top),
                                   width: Math.round(rect.width), height: Math.round(rect.height)}
                        };
                    });
                })()
                """
                els_result = await self._cdp_send(
                    ws,
                    "Runtime.evaluate",
                    {"expression": js, "returnByValue": True},
                    msg_id=4,
                )
                elements = els_result.get("result", {}).get("value", []) or []

                return {"title": title, "url": url, "elements": elements, "element_count": len(elements)}
        except Exception as exc:
            logger.debug("_cdp_get_page error: %s", exc)
            return {"title": "", "url": "", "elements": [], "element_count": 0}

    # ─── Private helpers ─────────────────────────────────────────────────────

    def _get_ws_url(self, tab_id: Optional[str] = None) -> Optional[str]:
        """Return WebSocket debugger URL for a tab. Defaults to first page tab."""
        try:
            resp = requests.get(f"{CDP_HTTP}/json", timeout=CDP_TIMEOUT)
            resp.raise_for_status()
            tabs = resp.json()
            page_tabs = [t for t in tabs if t.get("type") == "page"]
            if not page_tabs:
                return None
            if tab_id:
                for t in page_tabs:
                    if t.get("id") == tab_id:
                        return t.get("webSocketDebuggerUrl")
            return page_tabs[0].get("webSocketDebuggerUrl")
        except Exception:
            return None

    @staticmethod
    def _ok(data: dict, t0: float) -> dict:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"success": True, "data": data, "error": None, "time_ms": elapsed_ms}

    @staticmethod
    def _err(error: str, t0: float) -> dict:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"success": False, "data": None, "error": error, "time_ms": elapsed_ms}
