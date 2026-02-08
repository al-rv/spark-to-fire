"""
Color emoji images via Twemoji CDN. Caches PNGs locally so the board shows actual colored emojis
(Tkinter renders emoji text as black; images display in color).
"""
import os
import urllib.request

# Cache dir next to this file
_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".emoji_cache")
_TWEMOJI_BASE = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72"

# Our emojis -> Twemoji filename (hex codepoint, no variation selector for simplicity)
_EMOJI_CODEPOINTS = {
    "✨": "2728",
    "🔥": "1f525",
    "🗑️": "1f5d1",
    "✅": "2705",
    "📺": "1f4fa",
    "🎓": "1f393",
    "📚": "1f4da",
    "📝": "1f4dd",
    "🛠️": "1f6e0",
    "💡": "1f4a1",
    "📌": "1f4cc",
    "💾": "1f4be",
}


def _ensure_cache_dir():
    os.makedirs(_CACHE_DIR, exist_ok=True)


def emoji_to_path(emoji_char: str) -> str:
    """Return path to cached PNG for this emoji. Downloads from Twemoji CDN if needed."""
    code = _EMOJI_CODEPOINTS.get(emoji_char)
    if not code:
        # Fallback: single codepoint hex
        code = hex(ord(emoji_char))[2:]
    path = os.path.join(_CACHE_DIR, f"{code}.png")
    if not os.path.exists(path):
        _ensure_cache_dir()
        url = f"{_TWEMOJI_BASE}/{code}.png"
        try:
            urllib.request.urlretrieve(url, path)
        except Exception:
            pass  # If offline, path may not exist; caller can fall back to text
    return path if os.path.exists(path) else ""


def get_emoji_path(emoji_char: str) -> str:
    """Public: return path to PNG for emoji, or '' if not available."""
    return emoji_to_path(emoji_char)
