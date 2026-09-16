"""Unit tests for compat.py (Multi-OS compatibility, atomic I/O, diagnostics)."""

import io
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from omnipost_social_engine.compat import (
    atomic_write_json,
    atomic_write_text,
    configure_utf8_streams,
    ensure_directory,
    get_app_cache_dir,
    get_app_config_dir,
    get_os_family,
    get_platform_diagnostics,
    is_android,
    is_linux,
    is_macos,
    is_termux,
    is_windows,
    read_json_safe,
    read_text_safe,
    resolve_path,
    safe_open,
    safe_print,
)


def test_os_detection_functions():
    """Verify OS detection flags return boolean values."""
    win = is_windows()
    mac = is_macos()
    lin = is_linux()
    andr = is_android()
    term = is_termux()

    assert isinstance(win, bool)
    assert isinstance(mac, bool)
    assert isinstance(lin, bool)
    assert isinstance(andr, bool)
    assert isinstance(term, bool)

    family = get_os_family()
    assert isinstance(family, str)
    assert len(family) > 0


def test_platform_diagnostics():
    """Verify platform diagnostics dictionary contents and keys."""
    diag = get_platform_diagnostics()
    assert isinstance(diag, dict)

    required_keys = [
        "os_family",
        "platform_system",
        "platform_release",
        "platform_version",
        "platform_machine",
        "platform_architecture",
        "python_version",
        "python_implementation",
        "is_windows",
        "is_macos",
        "is_linux",
        "is_android",
        "is_termux",
        "filesystem_encoding",
        "default_encoding",
        "stdout_encoding",
        "temp_dir",
        "home_dir",
        "cwd",
    ]
    for key in required_keys:
        assert key in diag, f"Missing diagnostic key: {key}"

    assert diag["python_version"].count(".") >= 2


def test_resolve_path_relative_and_absolute(tmp_path):
    """Test resolve_path with relative, absolute, and custom base directories."""
    abs_path = tmp_path / "subdir" / "file.txt"
    resolved_abs = resolve_path(abs_path)
    assert resolved_abs.is_absolute()

    rel_name = "custom_file.json"
    resolved_rel = resolve_path(rel_name, base_dir=tmp_path)
    assert resolved_rel == (tmp_path / rel_name).resolve()

    # Expanduser test
    home_resolved = resolve_path("~")
    assert home_resolved.is_absolute()


def test_ensure_directory(tmp_path):
    """Test ensure_directory creates nested directories."""
    target_dir = tmp_path / "deep" / "nested" / "dir"
    assert not target_dir.exists()
    res = ensure_directory(target_dir)
    assert target_dir.exists()
    assert res == target_dir


def test_atomic_write_and_read_text(tmp_path):
    """Test atomic text writing with unicode and safe reading."""
    test_file = tmp_path / "nested" / "test_unicode.txt"
    unicode_content = "🚀 Rocket test with emojis 🧵 1/5 and math 𝐇𝐞𝐥𝐥𝐨 \nLine 2 with accents: café, naïve."

    written_path = atomic_write_text(test_file, unicode_content, make_parents=True)
    assert written_path == test_file.resolve()
    assert test_file.exists()

    read_back = read_text_safe(test_file)
    assert read_back == unicode_content


def test_atomic_write_and_read_json(tmp_path):
    """Test atomic JSON writing and reading."""
    json_file = tmp_path / "data" / "payload.json"
    payload = {
        "title": "Viral Post 🚀",
        "stats": {"views": 10500, "likes": 340},
        "tags": ["social", "growth", "automation"],
        "active": True,
    }

    atomic_write_json(json_file, payload, indent=2, ensure_ascii=False)
    assert json_file.exists()

    parsed = read_json_safe(json_file)
    assert parsed == payload
    assert parsed["title"] == "Viral Post 🚀"


def test_read_json_safe_fallback(tmp_path):
    """Test read_json_safe returns default value when file does not exist or has invalid JSON."""
    missing_file = tmp_path / "non_existent.json"
    assert read_json_safe(missing_file, default={"empty": True}) == {"empty": True}

    corrupt_file = tmp_path / "bad.json"
    atomic_write_text(corrupt_file, "{bad json: invalid", make_parents=True)
    assert read_json_safe(corrupt_file, default=None) is None


def test_safe_open(tmp_path):
    """Test safe_open context manager for text and binary files."""
    text_file = tmp_path / "safe.txt"
    with safe_open(text_file, mode="w") as f:
        f.write("Safe open test ⚡")

    with safe_open(text_file, mode="r") as f:
        content = f.read()
    assert content == "Safe open test ⚡"

    # Binary mode
    bin_file = tmp_path / "data.bin"
    with safe_open(bin_file, mode="wb") as f:
        f.write(b"\x00\x01\x02\x03")

    with safe_open(bin_file, mode="rb") as f:
        data = f.read()
    assert data == b"\x00\x01\x02\x03"


def test_app_config_and_cache_dirs():
    """Verify app config and cache paths are returned as valid Path objects."""
    config_dir = get_app_config_dir("test_app")
    cache_dir = get_app_cache_dir("test_app")

    assert isinstance(config_dir, Path)
    assert isinstance(cache_dir, Path)
    assert "test_app" in str(config_dir)
    assert "test_app" in str(cache_dir)


def test_safe_print_capture():
    """Test safe_print writes properly to custom stream buffer."""
    buf = io.StringIO()
    safe_print("Hello", "World", "🚀", file=buf, end="\n")
    output = buf.getvalue()
    assert "Hello World 🚀\n" == output


def test_configure_utf8_streams():
    """Verify configure_utf8_streams runs without error."""
    res = configure_utf8_streams()
    assert isinstance(res, bool)


def test_fallback_encodings_latin1(tmp_path):
    """Test read_text_safe handles non-utf8 files via fallback encodings."""
    latin1_file = tmp_path / "latin1.txt"
    # Write latin-1 bytes (e.g. 0xe9 is 'é' in latin-1)
    with open(latin1_file, "wb") as f:
        f.write(b"Caf\xe9 au lait")

    # Read using fallback
    content = read_text_safe(latin1_file, encoding="utf-8")
    assert "Caf" in content


def test_atomic_write_exception_handling(tmp_path, monkeypatch):
    """Verify temporary files are cleaned up if an exception occurs during replace."""
    target_file = tmp_path / "fail.txt"

    def fail_replace(src, dst):
        raise OSError("Disk simulated replace failure")

    with monkeypatch.context() as m:
        m.setattr("os.replace", fail_replace)
        with pytest.raises(OSError):
            atomic_write_text(target_file, "Some content")

    # Target should not exist
    assert not target_file.exists()
    # No dangling temp files in the directory
    temp_files = list(tmp_path.glob(".*tmp*"))
    assert len(temp_files) == 0

