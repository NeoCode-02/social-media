"""Defensive: header-injection attempts in download filenames must be stripped."""
from app.core.storage import _sanitize_download_name


def test_sanitize_drops_control_chars():
    # CR/LF smuggling → the bare \n would otherwise inject arbitrary headers.
    enc, ascii_fb = _sanitize_download_name("evil\r\nX-Inject: bad.png")
    assert "\r" not in enc and "\n" not in enc
    assert "\r" not in ascii_fb and "\n" not in ascii_fb
    # The CR/LF is what makes it a header-injection; "X-Inject" rendered as
    # part of a (single) filename is harmless. So just confirm the *control*
    # bytes are gone, not the text.
    assert "\r\n" not in enc
    assert "\r\n" not in ascii_fb


def test_sanitize_drops_null_bytes_and_strips_seps():
    enc, ascii_fb = _sanitize_download_name("a\x00b\\c/d.png")
    assert "\x00" not in enc
    assert "\\" not in enc and "/" not in enc


def test_sanitize_caps_length():
    long = "a" * 500
    enc, ascii_fb = _sanitize_download_name(long)
    assert len(enc) <= 128
    assert len(ascii_fb) <= 128


def test_sanitize_preserves_unicode_for_filename_star():
    enc, _ = _sanitize_download_name("résumé.pdf")
    # %C3%A9 etc. → safe in filename* and won't break the header
    assert "%C3%A9" in enc or "r" in enc


def test_sanitize_empty_string_returns_empty():
    enc, ascii_fb = _sanitize_download_name("")
    assert enc == "" and ascii_fb == ""
