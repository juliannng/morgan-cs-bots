"""YouTube-video discovery tool for the tutor agent.

Uses Tavily search restricted to youtube.com to find one relevant tutorial
video for a given topic. Returns a normalized dict including a thumbnail
URL so the agent can render a clickable thumbnail in markdown:

    [![<title>](<thumbnail_url>)](<watch_url>)

Most markdown renderers (adk web, GitHub, Slack, Discord, etc.) render
that as an inline clickable thumbnail that opens the video in a new tab.
"""

import os
import re
from typing import Any

from tavily import TavilyClient

_YOUTUBE_ID_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")


def _get_client() -> TavilyClient:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY not set. Add it to .env. "
            "Get a free key at https://app.tavily.com."
        )
    return TavilyClient(api_key=api_key)


def _extract_video_id(url: str) -> str | None:
    """Pull the 11-char video id out of a youtube.com/watch?v=... or youtu.be/... URL."""
    if not url:
        return None
    match = _YOUTUBE_ID_RE.search(url)
    return match.group(1) if match else None


def find_video(topic: str) -> dict[str, Any]:
    """Find one relevant YouTube tutorial video for a CS or Math topic.

    Use this in CS TUTOR and MATH TUTOR modes AFTER giving a conceptual
    explanation, to offer the student a short video deep-dive. Do NOT
    call this when debugging code, walking through a specific problem,
    or running a quiz.

    Args:
        topic: The concept to find a video for, e.g. "recursion", "how
            derivatives work", "binary search trees". Be specific but
            short. Two to five words.

    Returns:
        A dict with:
          title:         video title
          video_id:      11-char YouTube id
          watch_url:     https://youtube.com/watch?v=<id>
          thumbnail_url: https://img.youtube.com/vi/<id>/mqdefault.jpg
          description:   one-line snippet from the result
        On failure (no results, missing API key, network error), returns
        {"error": "...", "title": "", ...} with empty fields so the agent
        can gracefully skip the video.
    """
    try:
        client = _get_client()
        raw = client.search(
            query=f"{topic} tutorial explanation",
            max_results=5,
            search_depth="basic",
            include_answer=False,
            include_domains=["youtube.com"],
        )
    except Exception as exc:
        return {
            "error": str(exc),
            "title": "",
            "video_id": "",
            "watch_url": "",
            "thumbnail_url": "",
            "description": "",
        }

    for result in raw.get("results", []):
        url = result.get("url", "")
        video_id = _extract_video_id(url)
        if not video_id:
            continue
        return {
            "title": result.get("title", "") or "Video",
            "video_id": video_id,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
            "description": (result.get("content") or "")[:200],
        }

    return {
        "error": "no matching YouTube video found",
        "title": "",
        "video_id": "",
        "watch_url": "",
        "thumbnail_url": "",
        "description": "",
    }
