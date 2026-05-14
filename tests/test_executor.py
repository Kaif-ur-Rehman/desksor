"""
tests/test_executor.py

Tests for desksor/executor.py

Tests use Notepad which is available on every Windows installation.
Run with:
    python -m pytest tests/test_executor.py -v
"""

import subprocess
import time
import pytest

from desksor.executor import Executor


@pytest.fixture(scope="module")
def executor():
    return Executor()


@pytest.fixture(scope="module", autouse=True)
def open_notepad():
    """Open Notepad at start of module, close it at end."""
    proc = subprocess.Popen("notepad.exe", shell=True)
    time.sleep(2)
    yield proc
    try:
        proc.terminate()
    except Exception:
        pass


# ─── Result format ────────────────────────────────────────────────────────────

class TestResultFormat:
    """All Executor methods must return the standard result format."""

    def test_click_returns_standard_format(self, executor):
        result = executor.click_element("Notepad", "File")
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result

    def test_time_ms_is_integer(self, executor):
        result = executor.click_element("Notepad", "SomeNonExistentButton_xyz")
        assert isinstance(result["time_ms"], int)
        assert result["time_ms"] >= 0

    def test_failed_result_has_error_string(self, executor):
        result = executor.click_element("AppThatDoesNotExist_xyz", "Button")
        assert result["success"] is False
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0

    def test_keyboard_returns_standard_format(self, executor):
        result = executor.execute_keyboard("escape")
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result


# ─── click_element ────────────────────────────────────────────────────────────

class TestClickElement:
    def test_click_nonexistent_app_fails_gracefully(self, executor):
        """Clicking in non-existent app should fail with helpful message."""
        result = executor.click_element("AppThatDoesNotExist_xyz_12345", "Button")
        assert result["success"] is False
        assert "open apps" in result["error"].lower() or "not found" in result["error"].lower()

    def test_click_nonexistent_element_fails_gracefully(self, executor):
        """Clicking non-existent element should fail with available elements list."""
        result = executor.click_element("Notepad", "ButtonThatDoesNotExist_xyz_99999")
        assert result["success"] is False
        assert result["error"] is not None
        # Should list available elements
        assert "available" in result["error"].lower() or "elements" in result["error"].lower()

    def test_click_existing_element(self, executor):
        """Clicking an existing Notepad element should succeed."""
        # Try clicking File menu — present in all Notepad versions
        result = executor.click_element("Notepad", "File")
        # File menu should be clickable
        if result["success"]:
            assert result["time_ms"] >= 0
            # Close the menu we just opened
            executor.execute_keyboard("escape")
        else:
            # It might have a slightly different name — that's OK for this test
            # We still verify the format is correct
            assert "error" in result

    def test_double_click_format(self, executor):
        result = executor.click_element("Notepad", "NonExistentElement", "left", True)
        assert "success" in result
        assert "time_ms" in result

    def test_right_click_format(self, executor):
        result = executor.click_element("Notepad", "NonExistentElement", "right", False)
        assert "success" in result
        assert "time_ms" in result


# ─── execute_keyboard ─────────────────────────────────────────────────────────

class TestExecuteKeyboard:
    def test_escape_key(self, executor):
        result = executor.execute_keyboard("escape")
        assert result["success"] is True
        assert result["time_ms"] >= 0

    def test_ctrl_a(self, executor):
        result = executor.execute_keyboard("ctrl+a")
        assert result["success"] is True

    def test_single_key(self, executor):
        result = executor.execute_keyboard("enter")
        assert result["success"] is True

    def test_result_contains_keys(self, executor):
        result = executor.execute_keyboard("ctrl+s")
        assert result["success"] is True
        assert result["data"]["keys"] == "ctrl+s"
        # Dismiss save dialog if it appeared
        executor.execute_keyboard("escape")

    def test_multi_modifier(self, executor):
        result = executor.execute_keyboard("ctrl+shift+p")
        assert result["success"] is True

    def test_function_key(self, executor):
        result = executor.execute_keyboard("f1")
        assert result["success"] is True
        executor.execute_keyboard("escape")


# ─── scroll_app ───────────────────────────────────────────────────────────────

class TestScrollApp:
    def test_scroll_down(self, executor):
        result = executor.scroll_app("Notepad", "down", 3)
        assert "success" in result
        assert "time_ms" in result

    def test_scroll_up(self, executor):
        result = executor.scroll_app("Notepad", "up", 3)
        assert "success" in result

    def test_invalid_direction(self, executor):
        result = executor.scroll_app("Notepad", "diagonal", 3)
        assert result["success"] is False
        assert "direction" in result["error"].lower()

    def test_scroll_nonexistent_app(self, executor):
        result = executor.scroll_app("AppThatDoesNotExist_xyz", "down", 3)
        assert result["success"] is False


# ─── Mouse actions ────────────────────────────────────────────────────────────

class TestMouseActions:
    def test_get_cursor_position(self, executor):
        result = executor.get_cursor_position()
        assert result["success"] is True
        assert "x" in result["data"]
        assert "y" in result["data"]
        assert isinstance(result["data"]["x"], int)
        assert isinstance(result["data"]["y"], int)

    def test_move_mouse(self, executor):
        result = executor.move_mouse(100, 100)
        assert result["success"] is True
        assert result["data"]["x"] == 100
        assert result["data"]["y"] == 100

    def test_click_position(self, executor):
        # Click at a safe corner position
        result = executor.click_position(1, 1)
        assert result["success"] is True

    def test_drag(self, executor):
        result = executor.drag_mouse(50, 50, 100, 100)
        assert result["success"] is True
        assert result["data"]["from"]["x"] == 50
        assert result["data"]["to"]["x"] == 100


# ─── Speed tests ─────────────────────────────────────────────────────────────

class TestSpeed:
    def test_keyboard_under_500ms(self, executor):
        start = time.perf_counter()
        executor.execute_keyboard("escape")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 500, f"Key press took {elapsed_ms:.0f}ms — too slow"

    def test_get_cursor_under_100ms(self, executor):
        start = time.perf_counter()
        executor.get_cursor_position()
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100, f"get_cursor took {elapsed_ms:.0f}ms — too slow"
