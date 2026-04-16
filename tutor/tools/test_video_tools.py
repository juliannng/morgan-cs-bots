"""Unit tests for the YouTube video discovery tool."""

from unittest.mock import MagicMock, patch


def test_find_video_returns_normalized_dict_on_hit(monkeypatch):
    """Happy path: Tavily returns a YouTube URL, tool returns normalized fields."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-key")

    fake_tavily_response = {
        "results": [
            {
                "title": "Recursion Explained Simply",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "content": "A clear, short introduction to recursion for CS students.",
            }
        ]
    }

    with patch(
        "tutor.tools.video_tools.TavilyClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.search.return_value = fake_tavily_response
        mock_client_cls.return_value = mock_client

        from tutor.tools.video_tools import find_video

        result = find_video("recursion")

    assert result["video_id"] == "dQw4w9WgXcQ"
    assert result["watch_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert result["thumbnail_url"] == "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg"
    assert result["title"] == "Recursion Explained Simply"
    assert "error" not in result


def test_find_video_handles_youtu_be_short_links(monkeypatch):
    """The id regex works for youtu.be/<id> too, not just youtube.com/watch?v=."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-key")

    fake_tavily_response = {
        "results": [
            {"title": "Short link video", "url": "https://youtu.be/abcdEFGHijk", "content": "..."}
        ]
    }

    with patch("tutor.tools.video_tools.TavilyClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.search.return_value = fake_tavily_response
        mock_client_cls.return_value = mock_client

        from tutor.tools.video_tools import find_video

        result = find_video("anything")

    assert result["video_id"] == "abcdEFGHijk"
    assert "youtu.be" not in result["watch_url"]  # we normalize to youtube.com form


def test_find_video_skips_non_video_youtube_urls(monkeypatch):
    """A youtube.com channel or playlist URL without a video id should be skipped."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-key")

    fake_tavily_response = {
        "results": [
            {"title": "A channel page", "url": "https://www.youtube.com/@3blue1brown", "content": "..."},
            {"title": "A real video", "url": "https://www.youtube.com/watch?v=XYZ12345abc", "content": "..."},
        ]
    }

    with patch("tutor.tools.video_tools.TavilyClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.search.return_value = fake_tavily_response
        mock_client_cls.return_value = mock_client

        from tutor.tools.video_tools import find_video

        result = find_video("neural networks")

    assert result["video_id"] == "XYZ12345abc"
    assert result["title"] == "A real video"


def test_find_video_returns_error_when_api_key_missing(monkeypatch):
    """Missing TAVILY_API_KEY returns an error dict instead of raising."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    from tutor.tools.video_tools import find_video

    result = find_video("anything")

    assert result["video_id"] == ""
    assert "error" in result
    assert "TAVILY_API_KEY" in result["error"]


def test_find_video_returns_error_when_no_youtube_results(monkeypatch):
    """Tavily returns results but none are YouTube video URLs - return error dict."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-key")

    fake_tavily_response = {
        "results": [
            {"title": "Not a video", "url": "https://example.com/article", "content": "..."}
        ]
    }

    with patch("tutor.tools.video_tools.TavilyClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.search.return_value = fake_tavily_response
        mock_client_cls.return_value = mock_client

        from tutor.tools.video_tools import find_video

        result = find_video("anything")

    assert result["video_id"] == ""
    assert "error" in result


def test_find_video_returns_error_on_tavily_exception(monkeypatch):
    """Network or rate-limit exceptions from Tavily are swallowed into an error dict."""
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-key")

    with patch("tutor.tools.video_tools.TavilyClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.search.side_effect = RuntimeError("Rate limited")
        mock_client_cls.return_value = mock_client

        from tutor.tools.video_tools import find_video

        result = find_video("anything")

    assert result["video_id"] == ""
    assert "Rate limited" in result["error"]
