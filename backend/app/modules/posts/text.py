"""Parsing of #hashtags and @mentions out of post text."""

import re

# Hashtag: # then 1–50 word chars (letters/digits/underscore). Stored lowercased.
_HASHTAG_RE = re.compile(r"#(\w{1,50})", re.UNICODE)
# Mention: @ then a valid username (3–32 word chars, matching the user model).
_MENTION_RE = re.compile(r"@(\w{3,32})", re.UNICODE)


def extract_hashtags(text: str | None) -> list[str]:
    """Unique, lowercased hashtags in first-seen order."""
    if not text:
        return []
    seen: dict[str, None] = {}
    for m in _HASHTAG_RE.finditer(text):
        seen.setdefault(m.group(1).lower(), None)
    return list(seen.keys())


def extract_mentions(text: str | None) -> list[str]:
    """Unique, lowercased mentioned usernames in first-seen order."""
    if not text:
        return []
    seen: dict[str, None] = {}
    for m in _MENTION_RE.finditer(text):
        seen.setdefault(m.group(1).lower(), None)
    return list(seen.keys())
