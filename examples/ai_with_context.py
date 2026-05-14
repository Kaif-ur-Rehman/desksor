"""
examples/ai_with_context.py

Demonstrates what happens when you add Desksor to Claude Code through MCP.

This script simulates the experience from the developer's perspective.
When Claude Code has Desksor tools available, THIS is what it can do.

No copy-pasting. Ever.
"""

import asyncio
from desksor import Agent


# ─── Simulate Claude reading your environment ────────────────────────────────

async def claude_reads_your_environment(agent: Agent):
    """
    This is what Claude does automatically when you give it a task.
    Instead of you pasting context, Claude gathers it itself.
    """
    context = {}

    print("  Claude is reading your environment...")
    print()

    # 1. What apps are open?
    apps_result = await agent.get_open_apps()
    if apps_result["success"]:
        apps = apps_result["data"]["apps"]
        app_names = [a["name"] for a in apps if a.get("name")]
        context["open_apps"] = app_names
        print(f"  Claude sees: {len(app_names)} open applications")
        for name in app_names[:5]:
            print(f"    • {name}")

    # 2. Any browser console errors?
    console_result = await agent.browser_console()
    if console_result["success"]:
        messages = console_result["data"]["messages"]
        errors = [m for m in messages if m.get("level") in ("error", "warning")]
        context["console_errors"] = errors
        if errors:
            print(f"\n  Claude sees: {len(errors)} console error(s)")
            for err in errors[:3]:
                print(f"    [{err['level'].upper()}] {err['text'][:80]}")
                if err.get("url"):
                    print(f"             at {err['url']}:{err.get('line', '?')}")
        else:
            print("\n  Claude sees: Browser console is clean.")
    else:
        context["console_errors"] = []
        print(f"\n  Browser not in debug mode (that's OK for this example).")

    # 3. What's in the clipboard?
    clipboard_result = await agent.system_clipboard()
    if clipboard_result["success"]:
        content = clipboard_result["data"]["content"]
        if content:
            context["clipboard"] = content[:200]
            print(f"\n  Claude sees: Clipboard contains '{content[:60]}{'...' if len(content) > 60 else ''}'")
        else:
            context["clipboard"] = ""
            print("\n  Claude sees: Clipboard is empty.")

    # 4. System health
    sys_result = await agent.system_info()
    if sys_result["success"]:
        info = sys_result["data"]
        context["system"] = info
        print(f"\n  Claude sees: CPU {info['cpu_percent']}% | RAM {info['ram_percent']}%")

    return context


async def simulate_ai_debug_session():
    """
    Simulated conversation: Developer asks Claude to fix a bug.
    Claude reads everything itself. Developer pastes nothing.
    """
    agent = Agent()

    print()
    print("═" * 65)
    print("  WITHOUT DESKSOR — The old way")
    print("═" * 65)
    print()
    print("  You: 'Claude, my app has a bug.'")
    print()
    print("  Claude: 'What is the error?'")
    print("  You:    [copy error from console] [paste]")
    print()
    print("  Claude: 'What does the network request look like?'")
    print("  You:    [open DevTools] [copy request] [paste]")
    print()
    print("  Claude: 'What is the current state of the variable?'")
    print("  You:    [find variable in console] [copy] [paste]")
    print()
    print("  Claude: 'I think I understand... Line 42.'")
    print("  You:    [go to line 42] [verify] [fix] [test]")
    print()
    print("  Total time lost to context-switching: 15 minutes")
    print("  You did not write any code. You just moved text around.")
    print()

    print("═" * 65)
    print("  WITH DESKSOR — The new way")
    print("═" * 65)
    print()
    print("  You: 'Claude, fix the bug.'")
    print()
    print("  Claude (via Desksor MCP tools):")
    print("  →  Reading your environment...")
    print()

    context = await claude_reads_your_environment(agent)
    print()

    # Simulate Claude's response based on what it found
    print("  Claude's assessment:")
    print()

    if context.get("console_errors"):
        errors = context["console_errors"]
        print(f"  I can see {len(errors)} error(s) in your browser console.")
        for err in errors[:2]:
            print(f"    Error: {err['text'][:100]}")
            if err.get("url"):
                print(f"    File:  {err['url']}")
                print(f"    Line:  {err.get('line', 'unknown')}")
        print()
        print("  Fixing the issue now...")
        print("  [Claude reads the source file, identifies the bug, fixes it]")
        print("  Done. No copy-pasting required.")
    else:
        print("  I can see your environment:")

        if context.get("open_apps"):
            print(f"  • You have {len(context['open_apps'])} apps open")
            if any("excel" in a.lower() for a in context["open_apps"]):
                print("  • I see Excel is open — I can read its data directly")
            if any("chrome" in a.lower() or "edge" in a.lower() for a in context["open_apps"]):
                print("  • I see a browser is open — I can read the page structure")

        if context.get("clipboard"):
            clip = context["clipboard"]
            print(f"  • Your clipboard contains: '{clip[:60]}'")
            if clip.startswith("http"):
                print("    → That looks like a URL. Want me to analyze that page?")

        print()
        print("  Console is clean. No errors to fix right now.")
        print("  Try opening Chrome with --remote-debugging-port=9222")
        print("  to see the full power of Claude reading your browser.")

    print()
    print("═" * 65)
    print("  RESULT")
    print("═" * 65)
    print()
    print("  Without Desksor: 15+ minutes of copy-pasting context")
    print("  With Desksor:    Claude reads context in under 1 second")
    print()
    print("  To set this up for real:")
    print("  1. pip install desksor")
    print("  2. python -m desksor.server")
    print("  3. Add MCP config to Claude Desktop (see mcp/README.md)")
    print("  4. Say 'fix the bug' — Claude does the rest")
    print()


if __name__ == "__main__":
    asyncio.run(simulate_ai_debug_session())
