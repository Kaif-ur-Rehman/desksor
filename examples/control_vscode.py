"""
examples/control_vscode.py

Control VS Code using Desksor — read open files, find elements, trigger commands.
"""

import asyncio
from desksor import Agent


async def main():
    agent = Agent()

    print("=== Desksor VS Code Control Example ===\n")
    print("Make sure VS Code is open before running this.")
    print()

    # ── 1. Check if VS Code is open ───────────────────────────────────────────
    apps_result = await agent.get_open_apps()
    vscode_title = None
    if apps_result["success"]:
        for app in apps_result["data"]["apps"]:
            name = (app.get("name") or "").lower()
            if "visual studio code" in name or "code" in name:
                vscode_title = app["name"]
                break

    if not vscode_title:
        print("VS Code is not open. Opening it...")
        open_result = await agent.open_app("vscode")
        if not open_result["success"]:
            print(f"  Could not open VS Code: {open_result['error']}")
            print("  Install VS Code from https://code.visualstudio.com/")
            return
        await asyncio.sleep(3)
        print("  VS Code opened.")
        vscode_title = "Visual Studio Code"
    else:
        print(f"VS Code is open: {vscode_title}")
    print()

    # ── 2. Read VS Code accessibility tree ───────────────────────────────────
    print("Reading VS Code structure...")
    # VS Code's window title includes the open file/folder
    read_result = await agent.read("Visual Studio Code")
    if not read_result["success"]:
        # Try just "Code"
        read_result = await agent.read("Code")

    if read_result["success"]:
        print(f"  Window: {read_result['data']['window_title']}")
        print("  VS Code structure loaded successfully.")
    else:
        print(f"  Could not read VS Code: {read_result['error']}")
        print("  Try running VS Code and opening a file first.")
        return
    print()

    # ── 3. Find the command palette button ───────────────────────────────────
    print("Looking for Command Palette trigger...")
    find_result = await agent.find("Visual Studio Code", "Command Palette")
    if not find_result["success"]:
        find_result = await agent.find("Code", "Command Palette")

    if find_result["success"]:
        matches = find_result["data"]["matches"]
        print(f"  Found {len(matches)} element(s) matching 'Command Palette'")
    else:
        print(f"  Not found directly — using keyboard shortcut instead.")
    print()

    # ── 4. Open Command Palette with keyboard ────────────────────────────────
    print("Opening Command Palette (Ctrl+Shift+P)...")
    kp_result = await agent.key_press("ctrl+shift+p")
    if kp_result["success"]:
        print(f"  Command Palette opened in {kp_result['time_ms']}ms")
    else:
        print(f"  Key press failed: {kp_result['error']}")

    await asyncio.sleep(0.5)

    # ── 5. Close Command Palette ─────────────────────────────────────────────
    await agent.key_press("escape")
    print("  (Closed Command Palette)")
    print()

    # ── 6. Find Explorer sidebar elements ────────────────────────────────────
    print("Searching for Explorer sidebar...")
    explorer_result = await agent.find("Visual Studio Code", "Explorer")
    if not explorer_result["success"]:
        explorer_result = await agent.find("Code", "Explorer")

    if explorer_result["success"]:
        matches = explorer_result["data"]["matches"]
        print(f"  Found {len(matches)} Explorer element(s)")
        for match in matches[:3]:
            print(f"    • {match['name']} [{match['control_type']}]")
    else:
        print(f"  {explorer_result['error']}")
    print()

    # ── 7. Read system info ───────────────────────────────────────────────────
    print("System info while VS Code is running...")
    sys_result = await agent.system_info()
    if sys_result["success"]:
        info = sys_result["data"]
        print(f"  CPU:  {info['cpu_percent']}%")
        print(f"  RAM:  {info['ram_used_gb']}GB / {info['ram_total_gb']}GB ({info['ram_percent']}%)")
    print()

    print("=== Done! ===")
    print("VS Code is fully controllable through Desksor's accessibility tree.")


if __name__ == "__main__":
    asyncio.run(main())
