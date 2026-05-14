"""
desksor/server.py

WebSocket server for Desksor. Runs on ws://localhost:7823.
Accepts JSON commands, returns JSON results.

Run with:
    python -m desksor.server
"""

import asyncio
import json
import logging
import sys
import time

import websockets

from desksor.agent import Agent

logger = logging.getLogger("desksor.server")

HOST = "localhost"
PORT = 7823


async def handle_command(agent: Agent, message: str) -> dict:
    """
    Parse and dispatch a single command message.

    Expected format:
        {"action": "click", "app": "Excel", "element": "Save", "id": "req_123"}

    Returns:
        {"id": "req_123", "success": bool, "data": any, "error": str, "time_ms": int}
    """
    req_id = None
    try:
        cmd = json.loads(message)
        req_id = cmd.get("id", "unknown")
        action = (cmd.get("action") or "").lower()
        app = cmd.get("app", "")
        element = cmd.get("element", "")
        text = cmd.get("text", "")
        path = cmd.get("path", "")
        keys = cmd.get("keys", "")
        query = cmd.get("query", "")
        direction = cmd.get("direction", "down")
        amount = int(cmd.get("amount", 3))
        x = int(cmd.get("x", 0))
        y = int(cmd.get("y", 0))
        x2 = int(cmd.get("x2", 0))
        y2 = int(cmd.get("y2", 0))
        tab_id = cmd.get("tab_id", None)

        # ── Read actions ───────────────────────────────────────────────
        if action == "read":
            result = await agent.read(app)
        elif action == "find":
            result = await agent.find(app, query or element)
        elif action == "get_open_apps":
            result = await agent.get_open_apps()
        elif action == "read_element":
            result = await agent.read_element(app, element)

        # ── UI actions ─────────────────────────────────────────────────
        elif action == "click":
            result = await agent.click(app, element)
        elif action == "double_click":
            result = await agent.double_click(app, element)
        elif action == "right_click":
            result = await agent.right_click(app, element)
        elif action == "type":
            result = await agent.type(app, element, text)
        elif action == "key_press":
            result = await agent.key_press(keys or element)
        elif action == "scroll":
            result = await agent.scroll(app, direction, amount)
        elif action == "open_app":
            result = await agent.open_app(app)
        elif action == "close_app":
            result = await agent.close_app(app)
        elif action == "save_app":
            result = await agent.save_app(app)

        # ── Mouse actions ──────────────────────────────────────────────
        elif action == "move_mouse":
            result = await agent.move_mouse(x, y)
        elif action == "click_position":
            result = await agent.click_position(x, y)
        elif action == "drag":
            result = await agent.drag(x, y, x2, y2)
        elif action == "get_cursor_position":
            result = await agent.get_cursor_position()

        # ── Browser actions ────────────────────────────────────────────
        elif action == "browser_console":
            result = await agent.browser_console(tab_id)
        elif action == "browser_network":
            result = await agent.browser_network(tab_id)
        elif action == "browser_page":
            result = await agent.browser_page(tab_id)
        elif action == "browser_tabs":
            result = await agent.browser_tabs()

        # ── File system actions ────────────────────────────────────────
        elif action == "files_list":
            result = await asyncio.get_event_loop().run_in_executor(
                None, agent.files.list_directory, path
            )
        elif action == "files_read":
            result = await asyncio.get_event_loop().run_in_executor(
                None, agent.files.read_file, path
            )
        elif action == "files_write":
            content = cmd.get("content", "")
            result = await asyncio.get_event_loop().run_in_executor(
                None, agent.files.write_file, path, content
            )
        elif action == "files_find":
            pattern = cmd.get("pattern", "")
            result = await asyncio.get_event_loop().run_in_executor(
                None, agent.files.find_files, pattern, path or None
            )
        elif action == "files_search":
            result = await asyncio.get_event_loop().run_in_executor(
                None, agent.files.search_content, query, path or None
            )

        # ── System actions ─────────────────────────────────────────────
        elif action == "system_clipboard":
            result = await agent.system_clipboard()
        elif action == "system_processes":
            result = await agent.system_processes()
        elif action == "system_info":
            result = await agent.system_info()

        else:
            result = {
                "success": False,
                "data": None,
                "error": (
                    f"Unknown action '{action}'. "
                    f"Supported actions: read, find, get_open_apps, read_element, "
                    f"click, double_click, right_click, type, key_press, scroll, "
                    f"open_app, close_app, save_app, move_mouse, click_position, "
                    f"drag, get_cursor_position, browser_console, browser_network, "
                    f"browser_page, browser_tabs, files_list, files_read, files_write, "
                    f"files_find, files_search, system_clipboard, system_processes, system_info."
                ),
                "time_ms": 0,
            }

        return {"id": req_id, **result}

    except json.JSONDecodeError as exc:
        return {
            "id": req_id,
            "success": False,
            "data": None,
            "error": f"Invalid JSON: {exc}. Send valid JSON like {{\"action\": \"get_open_apps\", \"id\": \"1\"}}",
            "time_ms": 0,
        }
    except Exception as exc:
        logger.error("handle_command error: %s", exc, exc_info=True)
        return {
            "id": req_id,
            "success": False,
            "data": None,
            "error": str(exc),
            "time_ms": 0,
        }


async def ws_handler(websocket):
    """Handle a single WebSocket connection."""
    remote = websocket.remote_address
    logger.info("Client connected from %s", remote)
    agent = Agent()

    try:
        async for message in websocket:
            logger.debug("Received: %s", message[:200])
            response = await handle_command(agent, message)
            await websocket.send(json.dumps(response))
            logger.debug("Sent: %s", str(response)[:200])
    except websockets.exceptions.ConnectionClosedOK:
        logger.info("Client %s disconnected.", remote)
    except websockets.exceptions.ConnectionClosedError as exc:
        logger.warning("Client %s disconnected with error: %s", remote, exc)
    except Exception as exc:
        logger.error("ws_handler error for %s: %s", remote, exc)


async def run_server():
    """Start the Desksor WebSocket server."""
    print(f"\n{'═' * 56}")
    print(f"  Desksor running on ws://{HOST}:{PORT}")
    print(f"  Ready to receive commands from AI agents.")
    print(f"{'═' * 56}\n")
    logger.info("Desksor WebSocket server starting on ws://%s:%d", HOST, PORT)

    async with websockets.serve(ws_handler, HOST, PORT):
        await asyncio.Future()  # Run forever


def main():
    """Entry point for `python -m desksor.server` and the console script."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nDesksor server stopped.")


if __name__ == "__main__":
    main()
