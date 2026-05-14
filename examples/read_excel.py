"""
examples/read_excel.py

Read Excel data using Desksor — both the live app tree and direct file access.
"""

import asyncio
from desksor import Agent


async def main():
    agent = Agent()

    print("=== Desksor Excel Example ===\n")

    # ── Option 1: Read directly from an Excel file ────────────────────────────
    print("OPTION 1: Read Excel file directly (no Excel app needed)")
    print("-" * 50)

    # Change this path to an actual Excel file on your system
    excel_path = r"C:\Users\Public\Documents\sample.xlsx"

    read_result = agent.files.read_file(excel_path)
    if read_result["success"]:
        data = read_result["data"]
        print(f"File: {data['name']}")
        print(f"Size: {data['size_human']}")
        print(f"Content preview:")
        lines = data["content"].splitlines()
        for line in lines[:10]:
            print(f"  {line}")
        if len(lines) > 10:
            print(f"  ... ({len(lines) - 10} more lines)")
    else:
        print(f"  Note: {read_result['error']}")
        print(f"  (Create a sample.xlsx in C:/Users/Public/Documents to test this)")
    print()

    # ── Option 2: Read Excel's accessibility tree while it's open ─────────────
    print("OPTION 2: Read Excel app structure (Excel must be open)")
    print("-" * 50)

    # Check if Excel is already open
    apps_result = await agent.get_open_apps()
    excel_open = False
    if apps_result["success"]:
        for app in apps_result["data"]["apps"]:
            if "excel" in (app.get("name") or "").lower():
                excel_open = True
                print(f"  Excel is open: {app['name']}")
                break

    if not excel_open:
        print("  Excel is not open. Opening Excel...")
        open_result = await agent.open_app("excel")
        if open_result["success"]:
            print(f"  Excel opened in {open_result['time_ms']}ms")
            await asyncio.sleep(3)
            excel_open = True
        else:
            print(f"  Could not open Excel: {open_result['error']}")
            print("  Make sure Microsoft Excel is installed.")

    if excel_open:
        # Read Excel's full element tree
        print("\n  Reading Excel accessibility tree...")
        read_result = await agent.read("Excel")
        if read_result["success"]:
            print(f"  Window: {read_result['data']['window_title']}")
            print("  Excel structure loaded. AI can see all cells, toolbars, and menus.")

            # Find the Name Box (shows current cell reference like A1)
            find_result = await agent.find("Excel", "Name Box")
            if find_result["success"]:
                matches = find_result["data"]["matches"]
                if matches:
                    print(f"\n  Current cell: {matches[0].get('value', 'unknown')}")
        else:
            print(f"  Could not read Excel: {read_result['error']}")

    # ── Option 3: Find Excel files on disk ───────────────────────────────────
    print()
    print("OPTION 3: Find all Excel files on your system")
    print("-" * 50)

    find_result = agent.files.find_files("*.xlsx", r"C:\Users")
    if find_result["success"]:
        data = find_result["data"]
        print(f"Found {data['count']} Excel files:")
        for path in data["matches"][:5]:
            print(f"  {path}")
        if data["count"] > 5:
            print(f"  ... and {data['count'] - 5} more")
    else:
        print(f"  Search failed: {find_result['error']}")

    print()
    print("=== Done! ===")


if __name__ == "__main__":
    asyncio.run(main())
