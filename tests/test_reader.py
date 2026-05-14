"""
tests/test_reader.py

Tests for desksor/reader.py

Tests use real Windows applications (Notepad, Calculator) which are
available on every Windows installation. Run with:
    python -m pytest tests/test_reader.py -v
"""

import subprocess
import time
import pytest

from desksor.reader import Reader


@pytest.fixture(scope="module")
def reader():
    return Reader()


@pytest.fixture(scope="module", autouse=True)
def open_notepad():
    """Open Notepad at start of module, close it at end."""
    proc = subprocess.Popen("notepad.exe", shell=True)
    time.sleep(2)  # Wait for Notepad to fully open
    yield proc
    try:
        proc.terminate()
    except Exception:
        pass


# ─── get_all_windows ─────────────────────────────────────────────────────────

class TestGetAllWindows:
    def test_returns_list(self, reader):
        """get_all_windows should always return a list."""
        result = reader.get_all_windows()
        assert isinstance(result, list)

    def test_list_is_not_empty(self, reader):
        """There should always be at least one window open (Explorer, etc.)."""
        result = reader.get_all_windows()
        assert len(result) > 0, "Expected at least one open window"

    def test_window_has_required_fields(self, reader):
        """Each window dict must have name, title, pid, handle."""
        windows = reader.get_all_windows()
        for w in windows:
            assert "name" in w
            assert "title" in w
            assert "pid" in w
            assert "handle" in w

    def test_notepad_is_visible(self, reader):
        """Notepad should appear in the window list."""
        windows = reader.get_all_windows()
        names_lower = [(w.get("name") or "").lower() for w in windows]
        assert any("notepad" in n for n in names_lower), (
            f"Notepad not found in window list: {names_lower[:10]}"
        )

    def test_pids_are_integers(self, reader):
        """All PIDs should be valid non-negative integers."""
        windows = reader.get_all_windows()
        for w in windows:
            assert isinstance(w["pid"], int), f"PID should be int, got {type(w['pid'])}"
            assert w["pid"] >= 0


# ─── read_app_tree ───────────────────────────────────────────────────────────

class TestReadAppTree:
    def test_notepad_found(self, reader):
        """Should successfully read Notepad's tree."""
        result = reader.read_app_tree("Notepad")
        assert result["found"] is True, f"Expected found=True, error: {result.get('error')}"
        assert result["window_title"] is not None
        assert result["tree"] is not None

    def test_tree_has_required_structure(self, reader):
        """Tree root should have all required keys."""
        result = reader.read_app_tree("Notepad")
        assert result["found"] is True
        tree = result["tree"]
        assert "name" in tree
        assert "control_type" in tree
        assert "value" in tree
        assert "enabled" in tree
        assert "visible" in tree
        assert "rectangle" in tree
        assert "children" in tree

    def test_rectangle_has_required_fields(self, reader):
        """Rectangle should have left, top, right, bottom, width, height."""
        result = reader.read_app_tree("Notepad")
        assert result["found"] is True
        rect = result["tree"]["rectangle"]
        assert "left" in rect
        assert "top" in rect
        assert "right" in rect
        assert "bottom" in rect
        assert "width" in rect
        assert "height" in rect

    def test_app_not_found_returns_helpful_error(self, reader):
        """Reading a non-existent app should return success=False with helpful error."""
        result = reader.read_app_tree("ThisAppDoesNotExist_xyz_12345")
        assert result["found"] is False
        assert result["error"] is not None
        assert len(result["error"]) > 10, "Error message should be descriptive"
        # Should list available apps in the error
        assert "open" in result["error"].lower() or "found" in result["error"].lower()

    def test_never_raises_exceptions(self, reader):
        """read_app_tree should never raise — always return a dict."""
        # Even with weird input
        result = reader.read_app_tree("")
        assert isinstance(result, dict)
        assert "found" in result

        result = reader.read_app_tree("   ")
        assert isinstance(result, dict)
        assert "found" in result

    def test_partial_name_match(self, reader):
        """Partial name 'Note' should match 'Notepad'."""
        result = reader.read_app_tree("Note")
        assert result["found"] is True

    def test_case_insensitive_match(self, reader):
        """App name matching should be case-insensitive."""
        result_upper = reader.read_app_tree("NOTEPAD")
        result_lower = reader.read_app_tree("notepad")
        assert result_upper["found"] == result_lower["found"]


# ─── find_element ────────────────────────────────────────────────────────────

class TestFindElement:
    def test_find_existing_element(self, reader):
        """Should find an element that exists in Notepad."""
        result = reader.find_element("Notepad", "Notepad")
        # Window title contains 'Notepad' — should find it
        # (exact elements vary by Windows version, so we check structure)
        assert "found" in result
        assert "matches" in result
        assert "error" in result

    def test_find_nonexistent_element_returns_helpful_error(self, reader):
        """Should return found=False with a list of available elements."""
        result = reader.find_element("Notepad", "ElementThatDefinitelyDoesNotExist_xyz")
        assert result["found"] is False
        assert result["error"] is not None
        # Error should list available elements
        assert "available" in result["error"].lower() or "elements" in result["error"].lower()

    def test_matches_have_required_fields(self, reader):
        """Each match should have name, control_type, value, rectangle, path."""
        result = reader.find_element("Notepad", "File")
        if result["found"]:
            for match in result["matches"]:
                assert "name" in match
                assert "control_type" in match
                assert "value" in match
                assert "rectangle" in match
                assert "path" in match

    def test_find_is_case_insensitive(self, reader):
        """Search query should be case-insensitive."""
        result_upper = reader.find_element("Notepad", "FILE")
        result_lower = reader.find_element("Notepad", "file")
        # Both should return same found status
        assert result_upper["found"] == result_lower["found"]

    def test_find_in_nonexistent_app(self, reader):
        """Should return helpful error for non-existent app."""
        result = reader.find_element("AppThatDoesNotExist_xyz", "anything")
        assert result["found"] is False
        assert result["error"] is not None


# ─── Speed tests ─────────────────────────────────────────────────────────────

class TestSpeed:
    def test_get_all_windows_under_2_seconds(self, reader):
        """get_all_windows should complete in under 2 seconds."""
        start = time.perf_counter()
        reader.get_all_windows()
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"get_all_windows took {elapsed:.2f}s — too slow"

    def test_read_app_tree_under_3_seconds(self, reader):
        """read_app_tree should complete in under 3 seconds."""
        start = time.perf_counter()
        reader.read_app_tree("Notepad")
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0, f"read_app_tree took {elapsed:.2f}s — too slow"
