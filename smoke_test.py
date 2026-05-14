"""Quick smoke test for Desksor — run with: python smoke_test.py"""
import sys

print("Testing imports...")
try:
    import desksor
    print(f"  desksor version: {desksor.__version__}")

    from desksor.reader import Reader
    print("  Reader: OK")

    from desksor.executor import Executor
    print("  Executor: OK")

    from desksor.browser import Browser
    print("  Browser: OK")

    from desksor.filesystem import FileSystem
    print("  FileSystem: OK")

    from desksor.agent import Agent
    print("  Agent: OK")

except ImportError as e:
    print(f"  IMPORT ERROR: {e}")
    sys.exit(1)

print()
print("Testing Reader.get_all_windows()...")
r = Reader()
windows = r.get_all_windows()
print(f"  Found {len(windows)} windows")
for w in windows[:5]:
    name = w.get("name", "")
    if name:
        safe_name = name.encode("ascii", errors="replace").decode("ascii")
        print(f"    - {safe_name}")

print()
print("Testing FileSystem.list_directory()...")
fs = FileSystem()
result = fs.list_directory("C:\\Users")
if result["success"]:
    print(f"  C:\\Users has {result['data']['count']} items")
else:
    print(f"  Error: {result['error']}")

print()
print("Testing Browser error handling (no Chrome needed)...")
b = Browser()
tabs_result = b.read_tabs()
if not tabs_result["success"]:
    print(f"  Correctly returned error when Chrome not in debug mode.")
    print(f"  Error preview: {tabs_result['error'][:80]}")
else:
    count = tabs_result["data"]["count"]
    print(f"  Chrome IS in debug mode. Found {count} tabs.")

print()
print("Testing helpful error messages...")
result = r.read_app_tree("AppThatDefinitelyDoesNotExist_xyz_12345")
assert result["found"] is False
assert result["error"] is not None
print(f"  Not-found error: {result['error'][:80]}")

print()
print("=" * 50)
print("ALL SMOKE TESTS PASSED")
print("=" * 50)
print()
print("Next steps:")
print("  1. python -m desksor.server  (start WebSocket server)")
print("  2. python examples/basic_click.py  (open Notepad demo)")
print("  3. python -m pytest tests/ -v  (run full test suite)")
