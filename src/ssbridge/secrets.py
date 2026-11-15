"""Шифрование паролей и токенов средствами Windows (DPAPI).

Секреты шифруются ключом текущей учётной записи Windows, поэтому файл
настроек бесполезен, если его скопировать на другой компьютер.
На других ОС (например, при запуске тестов) используется base64.
"""
from __future__ import annotations

import base64
import sys

_PREFIX_DPAPI = "dpapi:"
_PREFIX_PLAIN = "b64:"

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32
    _ENTROPY = b"SmartShellBridge/v2"

    def _to_blob(data: bytes) -> _Blob:
        buf = ctypes.create_string_buffer(data, len(data))
        return _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))

    def _from_blob(blob: _Blob) -> bytes:
        try:
            return ctypes.string_at(blob.pbData, blob.cbData)
        finally:
            _kernel32.LocalFree(blob.pbData)

    def _protect(data: bytes) -> bytes:
        src, ent, out = _to_blob(data), _to_blob(_ENTROPY), _Blob()
        if not _crypt32.CryptProtectData(ctypes.byref(src), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out)):
            raise OSError("CryptProtectData failed")
        return _from_blob(out)

    def _unprotect(data: bytes) -> bytes:
        src, ent, out = _to_blob(data), _to_blob(_ENTROPY), _Blob()
        if not _crypt32.CryptUnprotectData(ctypes.byref(src), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out)):
            raise OSError("CryptUnprotectData failed")
        return _from_blob(out)
else:  # pragma: no cover - не Windows
    _protect = _unprotect = None


def encrypt(value: str) -> str:
    if not value:
        return ""
    raw = value.encode("utf-8")
    if _protect:
        try:
            return _PREFIX_DPAPI + base64.b64encode(_protect(raw)).decode()
        except OSError:
            pass
    return _PREFIX_PLAIN + base64.b64encode(raw).decode()


def decrypt(value: str) -> str:
    """Расшифровать. Нешифрованные строки возвращаются как есть."""
    if not value:
        return ""
    try:
        if value.startswith(_PREFIX_DPAPI) and _unprotect:
            return _unprotect(base64.b64decode(value[len(_PREFIX_DPAPI):])).decode("utf-8")
        if value.startswith(_PREFIX_PLAIN):
            return base64.b64decode(value[len(_PREFIX_PLAIN):]).decode("utf-8")
    except Exception:
        return ""
    return value


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and (value.startswith(_PREFIX_DPAPI) or value.startswith(_PREFIX_PLAIN))
