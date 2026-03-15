from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Iterable
import ctypes
import mmap
import os
import struct

import numpy as np

from .libpico import libpico
from .PicoParserFrame import PicoParserFrame, libpicoFrameToPicoParserFrame


@dataclass
class FrameNdarray:
  tstamp: np.datetime64
  csi: np.ndarray
  mag: np.ndarray
  phase: np.ndarray


class PicoParser:
  __maxWorker = os.cpu_count()

  def __init__(self, filePath: Path, nWorker: int = 1):
    """
    Initialize PicoParser with file path and number of workers.

    Args:
      filePath: Path to the PicoScenes .csi file.
      nWorker: Desired number of workers, greater than the number of CPUs will be ignored.
    """

    self.__entered = False
    self.__filePath = filePath
    self.__nWorker = self.__limitWorker(nWorker)

  def __enter__(self):
    self.__entered = True
    self.__file = open(self.__filePath, "rb")
    self.__fileMmap = mmap.mmap(self.__file.fileno(), 0, access=mmap.ACCESS_COPY)
    self.__fileMmapView = memoryview(self.__fileMmap)
    self.__executor: ThreadPoolExecutor = ThreadPoolExecutor(self.__nWorker)
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if self.__entered:
      self.__executor.shutdown()
      self.__fileMmapView.release()
      self.__fileMmap.close()
      self.__file.close()

  def __limitWorker(self, n: int) -> int:
    if n < 1 or self.__maxWorker is None:
      return 1
    else:
      return min(n, self.__maxWorker)

  def iterFrameIndices(self) -> Iterator[tuple[int, int]]:
    """
    Yield frame start offsets and lengths from the mapped file.

    Yields:
      Tuples of frame start index and length.
    """

    fileSize = os.path.getsize(self.__filePath)
    mmView = self.__fileMmapView

    idx = 0
    while idx + 4 <= fileSize:
      payloadLen = struct.unpack("<I", mmView[idx : idx + 4])[0]
      if payloadLen <= 0 or idx + (frameLength := 4 + payloadLen) > fileSize:
        break
      yield (idx, frameLength)
      idx += frameLength

  def iterFramesRaw(self) -> Iterator[memoryview]:
    """
    Yield memoryview slices for each frame in the memory mapped file.

    Yields:
      A view of the bytes for frames.
    """

    for idx, length in self.iterFrameIndices():
      yield self.__fileMmapView[idx : idx + length]

  def iterFrames(self, interp: bool = False) -> Iterator[PicoParserFrame]:
    """
    Yield frame data.

    Args:
      interp: Whether to apply interpolation along subcarrier.

    Yields:
      Processed frames.
    """

    for idx in self.iterFrameIndices():
      yield self.__getFrame(idx, interp)

  def getFramesByIndices(
    self,
    frameIndices: Iterable[tuple[int, int]],
    interp: bool = False,
  ) -> Iterator[PicoParserFrame]:
    """
    Return frames concurrently for provided indices.

    Args:
      frameIndices: Frame start offsets and lengths.
      interp: Whether to apply interpolation along subcarrier.

    Yields:
      Processed frames.
    """

    return self.__executor.map(
      lambda x: self.__getFrame(x, interp),
      frameIndices,
    )

  def getNdarray(
    self,
    enableTs: bool,
    enableCsi: bool,
    enableMag: bool,
    enablePhase: bool,
    interp: bool = False,
  ) -> tuple[
    np.ndarray | None, np.ndarray | None, np.ndarray | None, np.ndarray | None
  ]:
    """
    Return the whole file's ndarrays according to requested data types. (Only use on single pair of RX and TX NIC)

    Args:
      enableTs: Include timestamp data if True.
      enableCsi: Include CSI data if True.
      enableMag: Include magnitude data if True.
      enablePhase: Include phase data if True.
      interp: Whether to apply interpolation along subcarrier.

    Returns:
      Ndarray for timestamp, CSI, magnitude, and phase. None for non-requested component.
    """

    tstampList = []
    csiList = []
    magList = []
    phaseList = []

    for frame in self.getFramesByIndices(self.iterFrameIndices(), interp):
      if enableTs:
        tstampList.append(frame.rxSBasic.tstamp)
      if enableCsi:
        csiList.append(frame.csi.csi)
      if enableMag:
        magList.append(frame.csi.magnitude)
      if enablePhase:
        phaseList.append(frame.csi.phase)

    tstamp = np.array(tstampList) if enableTs else None
    csi = np.array(csiList) if enableCsi else None
    mag = np.array(magList) if enableMag else None
    phase = np.array(phaseList) if enablePhase else None

    return tstamp, csi, mag, phase

  def __getFrame(
    self,
    frameIdx: tuple[int, int],
    interpolate: bool,
  ) -> PicoParserFrame:
    idx, length = frameIdx

    buffer = (ctypes.c_ubyte * length).from_buffer(
      self.__fileMmapView[idx : idx + length]
    )
    libpicoRawPtr = libpico.getLibpicoFrameFromBuffer(buffer, length, True)

    frame = libpicoFrameToPicoParserFrame(libpicoRawPtr.contents, interpolate)
    libpico.freeLibpicoFrame(libpicoRawPtr)
    return frame
