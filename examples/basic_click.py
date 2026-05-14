"""
examples/basic_click.py

Simplest possible Desksor usage — open Notepad and click elements by name.
"""

import asyncio
from desksor import Agent


async def main():
    agent = Agent()

    print("=== Desksor Basic Click Example ===\n")

    # 1. See what's open
    apps_result = await agent.get_open_apps()
    if apps_result["success"]:
        print(f"Open apps: {len(apps_result['data']['apps'])} found")
        for app in apps_result["data"]["apps"][:5]:
            print(f"  - {app['name']}")
    print()

    # 2. Open Notepad
    print("Opening Notepad...")
    open_result = await agent.open_app("notepad")
    if open_result["success"]:
        print(f"  Notepad opened in {open_result['time_ms']}ms")
    else:
        print(f"  Could not open Notepad: {open_result['error']}")
        return
    print()

    await asyncio.sleep(1)

    # 3. Read the full Notepad structure
    print("Reading Notepad accessibility tree...")
    read_result = await agent.read("Notepad")
    if read_result["success"]:
        print(f"  Window title: {read_result['data']['window_title']}")
        print(f"  Tree loaded successfully")
    else:
        print(f"  Read failed: {read_result['error']}")
    print()

    # 4. Type into Notepad
    print("Typing into Notepad text area...")
    type_result = await agent.type("Notepad", "Text Editor", "Hello from Desksor!\nThis text was typed by an AI agent.")
    if type_result["success"]:
        print(f"  Text typed in {type_result['time_ms']}ms")
    else:
        print(f"  Type failed: {type_result['error']}")
    print()

    # 5. Save with Ctrl+S
    print("Saving with Ctrl+S...")
    save_result = await agent.key_press("ctrl+s")
    if save_result["success"]:
        print(f"  Save command sent in {save_result['time_ms']}ms")
    else:
        print(f"  Save failed: {save_result['error']}")

    await asyncio.sleep(0.5)

    # 6. Close the save dialog if it appeared (press Escape to cancel for this demo)
    await agent.key_press("escape")
    print()

    print("=== Done! ===")
    print("Desksor clicked and typed in Notepad without any pixel coordinates.")
    print("This works regardless of screen resolution, DPI, or Notepad version.")


if __name__ == "__main__":
    asyncio.run(main())
