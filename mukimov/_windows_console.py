"""Read Unicode console key events without the getwch() prefix ambiguity."""

from codecs import getincrementaldecoder
from contextlib import contextmanager


def _characters(records):
    decoder = getincrementaldecoder("utf-16-le")(errors="ignore")
    for code_unit, repeat in records:
        encoded = code_unit.to_bytes(2, "little")
        for _ in range(repeat):
            yield from decoder.decode(encoded)


@contextmanager
def console_keys(stream):
    import ctypes
    from ctypes import wintypes
    import msvcrt

    class KeyEvent(ctypes.Structure):
        _fields_ = [
            ("down", wintypes.BOOL),
            ("repeat", wintypes.WORD),
            ("virtual_key", wintypes.WORD),
            ("scan_code", wintypes.WORD),
            ("character", wintypes.WORD),
            ("control_state", wintypes.DWORD),
        ]

    class InputRecord(ctypes.Structure):
        # The KEY_EVENT_RECORD member determines the size and alignment of the union.
        _fields_ = [("kind", wintypes.WORD), ("key", KeyEvent)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_mode = kernel.GetConsoleMode
    get_mode.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    set_mode = kernel.SetConsoleMode
    set_mode.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    read = kernel.ReadConsoleInputW
    read.argtypes = (wintypes.HANDLE, ctypes.POINTER(InputRecord),
                     wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
    handle = msvcrt.get_osfhandle(stream.fileno())
    mode = wintypes.DWORD()
    if not get_mode(handle, ctypes.byref(mode)):
        raise ctypes.WinError(ctypes.get_last_error())
    # Turn off processed input (Ctrl+C), line input, echo and VT input.
    if not set_mode(handle, mode.value & ~0x207):
        raise ctypes.WinError(ctypes.get_last_error())

    def records():
        event = InputRecord()
        count = wintypes.DWORD()
        while True:
            if not read(handle, ctypes.byref(event), 1, ctypes.byref(count)):
                raise ctypes.WinError(ctypes.get_last_error())
            key = event.key
            # Alt+Numpad can deliver its character on the Alt key-up event.
            if count.value and event.kind == 1 and key.character and (key.down or key.virtual_key == 0x12):
                yield key.character, key.repeat

    try:
        yield _characters(records())
    finally:
        if not set_mode(handle, mode.value):
            raise ctypes.WinError(ctypes.get_last_error())
