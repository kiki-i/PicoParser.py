from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Iterable
import ctypes
import mmap
import os
import struct

import numpy as np

from .libpico import libpico, LibpicoRaw


@dataclass
class FrameNdarray:
  tstamp: np.datetime64
  csi: np.ndarray
  mag: np.ndarray
  phase: np.ndarray


class PicoParser:
  __interpSubcarrierIdx = np.array([-1, 0, 1])
  __maxWorker = os.cpu_count()

  def __init__(self, filePath: Path, nWorker: int):
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
    if self.__maxWorker:
      return min(n, self.__maxWorker)
    return n

  def iterFrameIdx(self) -> Iterator[tuple[int, int]]:
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

  def iterFrameRaw(self) -> Iterator[memoryview]:
    """
    Yield memoryview slices for each frame in the mapped file.

    Yields:
      A view of the bytes for the next frame.
    """
    for idx, length in self.iterFrameIdx():
      yield self.__fileMmapView[idx : idx + length]

  def iterFrameNdarray(self, interp: bool) -> Iterator[FrameNdarray]:
    """
    Yield frame data Ndarrays.

    Args:
      interp: Whether to apply interpolation along subcarrier.

    Yields:
      Processed frame ndarrays
    """
    for idx in self.iterFrameIdx():
      yield self.__getFrameNdarray(idx, interp)

  def getNdarray(
    self,
    enableTs: bool,
    enableCsi: bool,
    enableMag: bool,
    enablePhase: bool,
    interp: bool,
  ) -> tuple[
    np.datetime64 | None, np.ndarray | None, np.ndarray | None, np.ndarray | None
  ]:
    """
    Return the whole file's ndarrays according to requested data types.

    Args:
      enableTs: Include timestamp data if True.
      enableCsi: Include CSI data if True.
      enableMag: Include magnitude data if True.
      enablePhase: Include phase data if True.
      interp: Whether to apply interpolation along subcarrier.
      nWorker: Number of worker threads to use.

    Returns:
      Ndarrays for each requested component.
    """

    tstampList = []
    csiList = []
    magList = []
    phaseList = []

    for frame in self.getFrameNdarrayByIndices(self.iterFrameIdx(), interp):
      if enableTs:
        tstampList.append(frame.tstamp)
      if enableCsi:
        csiList.append(frame.csi)
      if enableMag:
        magList.append(frame.mag)
      if enablePhase:
        phaseList.append(frame.phase)

    tstamp = np.array(tstampList) if enableTs else None
    csi = np.array(csiList) if enableCsi else None
    mag = np.array(magList) if enableMag else None
    phase = np.array(phaseList) if enablePhase else None

    return tstamp, csi, mag, phase

  def getFrameNdarrayByIndices(
    self,
    frameIndices: Iterable[tuple[int, int]],
    interp: bool,
  ) -> Iterator[FrameNdarray]:
    """
    Return frame ndarrays concurrently for provided indices.

    Args:
      frameIndices: Frame start offsets and lengths.
      interp: Whether to apply interpolation along subcarrier.
      nWorker: Number of worker threads to use.

    Returns:
      Iterator of processed frame ndarrays.
    """
    return self.__executor.map(
      lambda x: self.__getFrameNdarray(x, interp),
      frameIndices,
    )

  def __getFrameNdarray(
    self,
    frameIdx: tuple[int, int],
    interpolate: bool,
  ) -> FrameNdarray:
    idx, length = frameIdx

    buffer = (ctypes.c_ubyte * length).from_buffer(
      self.__fileMmapView[idx : idx + length]
    )
    libpicoRawPtr = libpico.getLibpicoFrameFromBuffer(buffer, length, True)

    frameNdarray = self.__libpicoFrameToNdarray(libpicoRawPtr.contents, interpolate)
    libpico.freeLibpicoFrame(libpicoRawPtr)
    return frameNdarray

  def __libpicoFrameToNdarray(
    self,
    raw: LibpicoRaw,
    interp: bool,
  ) -> FrameNdarray:
    tstamp = np.datetime64(raw.rxSBasic.systemTime, "ns")

    shape: tuple = (
      raw.csi.nTones,
      raw.csi.nTx,
      raw.csi.nRx,
      raw.csi.nCsi + raw.csi.nEss,
    )

    realNp = np.ctypeslib.as_array(raw.csi.csiRealPtr, shape)
    imgNp = np.ctypeslib.as_array(raw.csi.csiImagPtr, shape)
    csiNp = realNp + 1j * imgNp

    magNp = np.ctypeslib.as_array(raw.csi.magnitudePtr, shape)
    phaseNp = np.ctypeslib.as_array(raw.csi.phasePtr, shape)

    if not interp:
      subcarrierIdx = np.ctypeslib.as_array(
        raw.csi.subcarrierIndicesPtr, (raw.csi.subcarrierIndicesSize,)
      )
      csiNp = self.__removeInterp(csiNp, subcarrierIdx)
      magNp = self.__removeInterp(magNp, subcarrierIdx)
      phaseNp = self.__removeInterp(phaseNp, subcarrierIdx)
    else:
      csiNp = csiNp.copy()
      magNp = magNp.copy()
      phaseNp = phaseNp.copy()

    return FrameNdarray(tstamp, csiNp, magNp, phaseNp)

  def __removeInterp(self, csi: np.ndarray, subcarrierIdx: np.ndarray) -> np.ndarray:
    realSubcarrierIdx = np.nonzero(~np.isin(subcarrierIdx, self.__interpSubcarrierIdx))[
      0
    ]
    return csi[realSubcarrierIdx]
