from pathlib import Path
import ctypes
import sys

from .libpicoframe import LibpicoRaw

ext = "dll" if sys.platform == "win32" else "so"
libpico = ctypes.CDLL(Path(__file__).parent / "_native" / f"libpico.{ext}")

libpico.getLibpicoFrameFromBuffer.restype = ctypes.POINTER(LibpicoRaw)
libpico.getLibpicoFrameFromBuffer.argtypes = [
  ctypes.POINTER(ctypes.c_uint8),
  ctypes.c_uint32,
  ctypes.c_bool,
]

libpico.freeLibpicoFrame.restype = ctypes.c_bool
libpico.freeLibpicoFrame.argtypes = [ctypes.POINTER(LibpicoRaw)]
