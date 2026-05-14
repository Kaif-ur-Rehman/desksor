"""
tests/test_browser.py

Tests for desksor/browser.py

These tests verify correct behavior both when Chrome IS and IS NOT
running in debug mode.

Run with:
    python -m pytest tests/test_browser.py -v

For full browser tests, launch Chrome first:
    chrome.exe --remote-debugging-port=9222
"""

import pytest
from desksor.browser import Browser


@pytest.fixture(scope="module")
def browser():
    return Browser()


def is_chrome_debug_available() -> bool:
    """Check whether Chrome is running in debug mode."""
    import requests
    try:
        resp = requests.get("http://localhost:9222/json", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


# ─── Result format tests (always run) ────────────────────────────────────────

class TestResultFormat:
    """All Browser methods must return the standard result dict."""

    def test_read_tabs_returns_standard_format(self, browser):
        result = browser.read_tabs()
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result

    def test_get_active_tab_returns_standard_format(self, browser):
        result = browser.get_active_tab()
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result

    def test_read_console_returns_standard_format(self, browser):
        result = browser.read_console()
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result

    def test_read_network_returns_standard_format(self, browser):
        result = browser.read_network()
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result

    def test_read_page_returns_standard_format(self, browser):
        result = browser.read_page()
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "time_ms" in result

    def test_time_ms_is_integer(self, browser):
        result = browser.read_tabs()
        assert isinstance(result["time_ms"], int)
        assert result["time_ms"] >= 0


# ─── Error handling when Chrome is NOT in debug mode ─────────────────────────

class TestErrorsWithoutChrome:
    """When Chrome is not in debug mode, all methods should fail gracefully."""

    @pytest.mark.skipif(
        is_chrome_debug_available(),
        reason="Chrome IS running in debug mode — skip 'no chrome' tests",
    )
    def test_read_tabs_helpful_error(self, browser):
        """Without Chrome debug, should get a helpful error message."""
        result = browser.read_tabs()
        assert result["success"] is False
        assert result["error"] is not None
        # Error should mention how to fix it
        error_lower = result["error"].lower()
        assert "debug" in error_lower or "9222" in error_lower or "chrome" in error_lower

    @pytest.mark.skipif(
        is_chrome_debug_available(),
        reason="Chrome IS running in debug mode — skip 'no chrome' tests",
    )
    def test_read_console_helpful_error(self, browser):
        result = browser.read_console()
        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.skipif(
        is_chrome_debug_available(),
        reason="Chrome IS running in debug mode — skip 'no chrome' tests",
    )
    def test_read_page_helpful_error(self, browser):
        result = browser.read_page()
        assert result["success"] is False
        assert "9222" in result["error"] or "debug" in result["error"].lower()

    @pytest.mark.skipif(
        is_chrome_debug_available(),
        reason="Chrome IS running in debug mode — skip 'no chrome' tests",
    )
    def test_errors_mention_launch_command(self, browser):
        """Error messages should tell user exactly how to enable debug mode."""
        result = browser.read_tabs()
        assert result["success"] is False
        error = result["error"]
        # Should mention the launch flag
        assert "--remote-debugging-port" in error or "9222" in error


# ─── Tests when Chrome IS in debug mode ──────────────────────────────────────

class TestWithChrome:
    """These tests only run when Chrome is actually available in debug mode."""

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode — start with: chrome.exe --remote-debugging-port=9222",
    )
    def test_read_tabs_succeeds(self, browser):
        result = browser.read_tabs()
        assert result["success"] is True
        assert "tabs" in result["data"]
        assert isinstance(result["data"]["tabs"], list)

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode",
    )
    def test_tabs_have_required_fields(self, browser):
        result = browser.read_tabs()
        assert result["success"] is True
        for tab in result["data"]["tabs"]:
            assert "id" in tab
            assert "title" in tab
            assert "url" in tab
            assert "type" in tab

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode",
    )
    def test_get_active_tab_succeeds(self, browser):
        result = browser.get_active_tab()
        assert result["success"] is True
        data = result["data"]
        assert "id" in data
        assert "title" in data
        assert "url" in data

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode",
    )
    def test_read_console_returns_list(self, browser):
        result = browser.read_console()
        assert result["success"] is True
        assert "messages" in result["data"]
        assert isinstance(result["data"]["messages"], list)

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode",
    )
    def test_console_messages_have_fields(self, browser):
        result = browser.read_console()
        assert result["success"] is True
        for msg in result["data"]["messages"]:
            assert "level" in msg
            assert "text" in msg

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode",
    )
    def test_read_page_returns_elements(self, browser):
        result = browser.read_page()
        assert result["success"] is True
        data = result["data"]
        assert "title" in data
        assert "url" in data
        assert "elements" in data
        assert isinstance(data["elements"], list)

    @pytest.mark.skipif(
        not is_chrome_debug_available(),
        reason="Chrome not running in debug mode",
    )
    def test_read_network_returns_list(self, browser):
        result = browser.read_network()
        assert result["success"] is True
        assert "requests" in result["data"]
        assert isinstance(result["data"]["requests"], list)


# ─── Speed tests ─────────────────────────────────────────────────────────────

class TestSpeed:
    def test_read_tabs_under_5_seconds(self, browser):
        """Even without Chrome, should fail fast (not hang)."""
        import time
        start = time.perf_counter()
        browser.read_tabs()
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"read_tabs took {elapsed:.2f}s — should fail fast"
