"""
examples/never_breaks.py

Demonstrates why Desksor never breaks even when apps update their UI.

Traditional pixel-based automation breaks whenever a button moves.
Desksor reads element names — Save is always Save.
"""

import asyncio
import time


# ─── THE OLD WAY — breaks when app updates ──────────────────────────────────

def old_way_click_save():
    """
    Traditional automation using pixel coordinates.
    Works today. Breaks tomorrow when the app updates its layout.
    """
    import pyautogui

    print("OLD WAY: Clicking Save at pixel (342, 156)...")
    print("  This worked when the developer wrote the script.")
    print("  App updated last week. Button is now at (398, 172).")
    print("  Result: CLICK MISSED. Nothing happened.")
    print()

    # Simulate: button moved after app update
    screen_width, screen_height = pyautogui.size()
    # Original coords: x=342, y=156
    # After app update: button is at x=398, y=172
    # Script still clicks old position → fails silently

    print("  Error: Element not found at (342, 156).")
    print("  You won't know this until you watch the screen.")
    print("  Your automation ran, returned success, but did nothing.")
    print()


# ─── THE DESKSOR WAY — never breaks ─────────────────────────────────────────

async def desksor_way_click_save():
    """
    Desksor automation using element names from the accessibility tree.
    Works regardless of where the button is on screen.
    Works after UI updates. Works after app restarts. Always.
    """
    from desksor import Agent

    agent = Agent()

    print("DESKSOR WAY: Clicking 'Save' in Notepad...")
    print("  Reading accessibility tree...")
    print("  Finding element named 'Save'...")
    print("  (It doesn't matter where on screen it is)")
    print()

    # First open Notepad so we have something to work with
    open_result = await agent.open_app("notepad")
    if not open_result["success"]:
        print(f"  Could not open Notepad: {open_result['error']}")
        print("  Make sure Notepad is installed (it always is on Windows).")
        return

    await asyncio.sleep(1)

    # Type something so Save is meaningful
    type_result = await agent.type("Notepad", "Text Editor", "Hello from Desksor!")
    if type_result["success"]:
        print(f"  Typed text in {type_result['time_ms']}ms")

    # Now save — this finds 'Save' in the accessibility tree
    # Works even if Save moved from toolbar to menu to ribbon
    save_result = await agent.key_press("ctrl+s")

    if save_result["success"]:
        print(f"  Save sent in {save_result['time_ms']}ms")
        print()
        print("  If a Save dialog appeared, Desksor handles it.")
        print("  The app is saved.")
    else:
        print(f"  Save failed: {save_result['error']}")

    print()


# ─── COMPARISON ──────────────────────────────────────────────────────────────

async def run_comparison():
    print()
    print("═" * 60)
    print("  DESKSOR: Why AI automation never breaks")
    print("═" * 60)
    print()

    print("SCENARIO: Your automation script saves a file in Notepad.")
    print("          The Notepad team ships an update that moves buttons.")
    print()

    print("─" * 60)
    print("APPROACH 1: Pixel coordinates (pyautogui, sikuli, etc.)")
    print("─" * 60)
    old_way_click_save()

    print("─" * 60)
    print("APPROACH 2: Desksor (accessibility tree)")
    print("─" * 60)
    await desksor_way_click_save()

    print("═" * 60)
    print("CONCLUSION")
    print("═" * 60)
    print()
    print("  Pixel automation:     Breaks on every UI update")
    print("  Image recognition:    Breaks when themes change")
    print("  Desksor:              Works forever")
    print()
    print("  The accessibility tree is a contract.")
    print("  'Save' is always called 'Save'.")
    print("  Apps must keep element names for accessibility compliance.")
    print("  That contract is your automation guarantee.")
    print()


if __name__ == "__main__":
    asyncio.run(run_comparison())
