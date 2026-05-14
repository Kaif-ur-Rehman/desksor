"""
examples/control_browser.py

Read Chrome browser state — console, network, and page DOM — using Desksor.

Prerequisites:
    Launch Chrome with: chrome.exe --remote-debugging-port=9222
"""

import asyncio
from desksor import Agent


async def main():
    agent = Agent()

    print("=== Desksor Browser Control Example ===\n")
    print("Prerequisites:")
    print("  Chrome must be running with --remote-debugging-port=9222")
    print("  Launch command: chrome.exe --remote-debugging-port=9222")
    print()

    # ── 1. List open tabs ─────────────────────────────────────────────────────
    print("1. Reading open browser tabs...")
    tabs_result = await agent.browser_tabs()
    if tabs_result["success"]:
        tabs = tabs_result["data"]["tabs"]
        print(f"   Found {len(tabs)} open tabs:")
        for tab in tabs[:5]:
            print(f"   [{tab['type']:6}] {tab['title'][:60]} — {tab['url'][:60]}")
    else:
        print(f"   Error: {tabs_result['error']}")
        print("   → Make sure Chrome is open with --remote-debugging-port=9222")
        print()
        return
    print()

    # ── 2. Read console messages ──────────────────────────────────────────────
    print("2. Reading browser console messages...")
    console_result = await agent.browser_console()
    if console_result["success"]:
        messages = console_result["data"]["messages"]
        if messages:
            print(f"   Found {len(messages)} console messages:")
            for msg in messages[:10]:
                level = msg.get("level", "info").upper()
                text = msg.get("text", "")[:100]
                url = msg.get("url", "")
                line = msg.get("line", 0)
                print(f"   [{level:7}] {text}")
                if url:
                    print(f"            at {url}:{line}")
        else:
            print("   Console is clear — no messages logged.")
    else:
        print(f"   Error: {console_result['error']}")
    print()

    # ── 3. Read current page structure ───────────────────────────────────────
    print("3. Reading current page DOM structure...")
    page_result = await agent.browser_page()
    if page_result["success"]:
        page = page_result["data"]
        print(f"   Page: {page.get('title', 'Unknown')}")
        print(f"   URL:  {page.get('url', 'Unknown')}")
        elements = page.get("elements", [])
        print(f"   Interactive elements: {len(elements)}")

        # Show buttons and links
        buttons = [e for e in elements if e.get("tag") in ("button",)]
        links = [e for e in elements if e.get("tag") in ("a",) and e.get("text")]
        inputs = [e for e in elements if e.get("tag") in ("input", "textarea")]

        if buttons:
            print(f"\n   Buttons ({len(buttons)}):")
            for b in buttons[:5]:
                print(f"     • {b.get('text', '[no text]')[:60]}")

        if links:
            print(f"\n   Links ({len(links)}):")
            for l in links[:5]:
                print(f"     • {l.get('text', '[no text]')[:60]}")

        if inputs:
            print(f"\n   Input fields ({len(inputs)}):")
            for i in inputs[:5]:
                print(f"     • [{i.get('type', 'text')}] {i.get('name', '') or i.get('id', '[unnamed]')}")
    else:
        print(f"   Error: {page_result['error']}")
    print()

    print("=== Done! ===")
    print("Your AI can now see everything in your browser without you copy-pasting.")


if __name__ == "__main__":
    asyncio.run(main())
