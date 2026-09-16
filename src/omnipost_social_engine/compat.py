"""Multi-OS compatibility, UTF-8 safe I/O, path normalization, and platform diagnostics.

Provides zero-dependency standard library utilities for seamless operation across
Linux, macOS, Windows, Android, and Termux environments.
"""

from __future__ import annotations

import io
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, IO, List, Optional, Sequence, Union


def is_windows() -> bool:
    """Return True if running on Microsoft Windows."""
    return sys.platform.startswith("win") or os.name == "nt"


def is_macos() -> bool:
    """Return True if running on Apple macOS / Darwin."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Return True if running on Linux (including Android/Termux)."""
    return sys.platform.startswith("linux")


def is_android() -> bool:
    """Return True if running inside an Android environment."""
    return (
        "ANDROID_ROOT" in os.environ
        or "ANDROID_DATA" in os.environ
        or hasattr(sys, "getandroidapilevel")
        or "android" in sys.platform.lower()
    )


def is_termux() -> bool:
    """Return True if running inside Termux on Android."""
    if is_android():
        return True
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix:
        return True
    if "TERMUX_VERSION" in os.environ:
        return True
    if os.path.exists("/data/data/com.termux"):
        return True
    return False


def get_os_family() -> str:
    """Return a normalized string representing the operating system family."""
    if is_termux():
        return "termux"
    if is_android():
        return "android"
    if is_windows():
        return "windows"
    if is_macos():
        return "macos"
    if is_linux():
        return "linux"
    return sys.platform or "unknown"


def get_platform_diagnostics() -> Dict[str, Any]:
    """Gather comprehensive system, Python runtime, encoding, and path diagnostics."""
    stdout_enc = getattr(sys.stdout, "encoding", None) or "unknown"
    stderr_enc = getattr(sys.stderr, "encoding", None) or "unknown"
    stdin_enc = getattr(sys.stdin, "encoding", None) or "unknown"

    try:
        home_path = str(Path.home())
    except Exception:
        home_path = os.environ.get("HOME", os.environ.get("USERPROFILE", ""))

    return {
        "os_family": get_os_family(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_machine": platform.machine(),
        "platform_architecture": platform.architecture()[0],
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "is_windows": is_windows(),
        "is_macos": is_macos(),
        "is_linux": is_linux(),
        "is_android": is_android(),
        "is_termux": is_termux(),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "default_encoding": sys.getdefaultencoding(),
        "stdout_encoding": stdout_enc,
        "stderr_encoding": stderr_enc,
        "stdin_encoding": stdin_enc,
        "temp_dir": tempfile.gettempdir(),
        "home_dir": home_path,
        "cwd": str(Path.cwd()),
        "path_separator": os.sep,
        "line_separator": repr(os.linesep),
    }


def resolve_path(
    path_input: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None,
    expand_user: bool = True,
    strict: bool = False,
) -> Path:
    """Safely resolve relative and user paths across different operating systems.

    Args:
        path_input: Raw string or Path object to resolve.
        base_dir: Optional base directory to resolve relative paths against.
        expand_user: If True, expand '~' or '~user' prefixes.
        strict: If True, raise FileNotFoundError if path does not exist.

    Returns:
        A resolved, normalized absolute Path object.
    """
    p = Path(path_input)
    if expand_user:
        try:
            p = p.expanduser()
        except RuntimeError:
            # Can happen if home directory resolution fails
            pass

    if not p.is_absolute():
        base = Path(base_dir).resolve() if base_dir else Path.cwd()
        p = base / p

    try:
        if strict:
            return p.resolve(strict=True)
        return p.resolve(strict=False)
    except Exception:
        return p.absolute()


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, creating parent directories if needed."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_app_config_dir(app_name: str = "omnipost") -> Path:
    """Return the standard platform-specific configuration directory."""
    if is_windows():
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / app_name
    elif is_macos():
        return Path.home() / "Library" / "Application Support" / app_name
    elif is_termux():
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        return Path(prefix) / "etc" / app_name

    # Standard XDG base directory for Linux and other POSIX
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / app_name
    return Path.home() / ".config" / app_name


def get_app_cache_dir(app_name: str = "omnipost") -> Path:
    """Return the standard platform-specific cache directory."""
    if is_windows():
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP")
        if base:
            return Path(base) / app_name / "cache"
    elif is_macos():
        return Path.home() / "Library" / "Caches" / app_name
    elif is_termux():
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        return Path(prefix) / "tmp" / app_name / "cache"

    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / app_name
    return Path.home() / ".cache" / app_name


def safe_open(
    file_path: Union[str, Path],
    mode: str = "r",
    encoding: Optional[str] = "utf-8",
    errors: str = "replace",
    **kwargs: Any,
) -> IO[Any]:
    """Open a file with safe default UTF-8 encoding and robust error handling.

    For text modes, defaults to UTF-8 with 'replace' error handling to avoid
    crashing on corrupt or mis-encoded characters.
    For binary modes ('b' in mode), encoding and errors parameters are omitted.
    """
    path = Path(file_path)
    if "b" in mode:
        return open(path, mode=mode, **kwargs)
    return open(path, mode=mode, encoding=encoding, errors=errors, **kwargs)


def atomic_write_text(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    errors: str = "replace",
    make_parents: bool = True,
    newline: Optional[str] = None,
) -> Path:
    """Atomically write text to a file using a temporary file and atomic rename.

    Guarantees that readers never see a partially written file even in case
    of unexpected interruption, power loss, or crash.

    Args:
        file_path: Target destination path.
        content: String content to write.
        encoding: Text encoding (default: utf-8).
        errors: Error handling scheme for encoding.
        make_parents: If True, automatically create parent directories.
        newline: Controls how newline characters are handled.

    Returns:
        The resolved Path of the written file.
    """
    target = resolve_path(file_path)
    if make_parents:
        target.parent.mkdir(parents=True, exist_ok=True)

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding=encoding,
        errors=errors,
        newline=newline,
        dir=str(target.parent),
        prefix=f".{target.name}.tmp_",
        delete=False,
    )
    temp_path = Path(temp_file.name)

    try:
        temp_file.write(content)
        temp_file.flush()
        try:
            os.fsync(temp_file.fileno())
        except (AttributeError, OSError):
            pass
        temp_file.close()

        # Atomic replacement
        os.replace(temp_path, target)
        return target
    except Exception:
        temp_file.close()
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def atomic_write_json(
    file_path: Union[str, Path],
    data: Any,
    indent: int = 2,
    encoding: str = "utf-8",
    ensure_ascii: bool = False,
    make_parents: bool = True,
    default: Optional[Callable[[Any], Any]] = None,
    sort_keys: bool = False,
) -> Path:
    """Atomically serialize and write JSON data to file.

    Args:
        file_path: Target path.
        data: Python object to serialize.
        indent: JSON indentation spaces.
        encoding: Character encoding (default: utf-8).
        ensure_ascii: If False, emits raw UTF-8 characters rather than \\u escapes.
        make_parents: Whether to create missing parent directories.
        default: Custom JSON serializer callable for complex objects.
        sort_keys: If True, dictionary keys are sorted in output.

    Returns:
        The resolved Path of the written file.
    """
    json_text = json.dumps(
        data,
        indent=indent,
        ensure_ascii=ensure_ascii,
        default=default,
        sort_keys=sort_keys,
    )
    # Append trailing newline for POSIX compliance
    if not json_text.endswith("\n"):
        json_text += "\n"
    return atomic_write_text(
        file_path=file_path,
        content=json_text,
        encoding=encoding,
        make_parents=make_parents,
    )


def read_text_safe(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    errors: str = "replace",
    fallback_encodings: Optional[Sequence[str]] = None,
) -> str:
    """Read full text content from file with fallback encoding support.

    Args:
        file_path: Path to file to read.
        encoding: Primary encoding to attempt.
        errors: Error handling mode ('replace', 'ignore', 'strict').
        fallback_encodings: Sequence of additional encodings to attempt if primary fails.

    Returns:
        The decoded string content of the file.
    """
    target = resolve_path(file_path)
    encodings_to_try = [encoding]
    if fallback_encodings:
        for enc in fallback_encodings:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)
    else:
        # Standard fallback list for cross-platform legacy files
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)

    last_error: Optional[Exception] = None
    for enc in encodings_to_try:
        try:
            with open(target, mode="r", encoding=enc, errors="strict") as f:
                return f.read()
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except Exception:
            raise

    # Fallback to primary encoding with user-specified error handling (e.g. 'replace')
    with open(target, mode="r", encoding=encoding, errors=errors) as f:
        return f.read()


def read_json_safe(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    default: Any = None,
) -> Any:
    """Read and parse JSON from a file, returning a default value if file is missing or invalid.

    Args:
        file_path: Path to the JSON file.
        encoding: File character encoding.
        default: Fallback value if reading or parsing fails (if None and file missing, returns None).

    Returns:
        Parsed JSON data structure or the default value.
    """
    target = resolve_path(file_path)
    if not target.exists():
        return default

    try:
        text = read_text_safe(target, encoding=encoding)
        return json.loads(text)
    except Exception:
        return default


def configure_utf8_streams() -> bool:
    """Reconfigure sys.stdout and sys.stderr to UTF-8 with replace error handler if supported.

    Returns:
        True if reconfigured successfully, False otherwise.
    """
    success = True
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                success = False
        else:
            success = False
    return success


def safe_print(
    *args: Any,
    sep: str = " ",
    end: str = "\n",
    file: Optional[IO[str]] = None,
    flush: bool = False,
) -> None:
    """Print text safely, preventing UnicodeEncodeError crashes on legacy or restricted consoles.

    If standard printing raises UnicodeEncodeError, replaces unprintable characters
    with ASCII approximations or replacement characters.
    """
    target_file = file or sys.stdout
    text = sep.join(str(a) for a in args) + end

    try:
        target_file.write(text)
        if flush and hasattr(target_file, "flush"):
            target_file.flush()
    except UnicodeEncodeError:
        target_encoding = getattr(target_file, "encoding", "utf-8") or "utf-8"
        sanitized_bytes = text.encode(target_encoding, errors="replace")
        sanitized_text = sanitized_bytes.decode(target_encoding, errors="replace")
        target_file.write(sanitized_text)
        if flush and hasattr(target_file, "flush"):
            target_file.flush()
