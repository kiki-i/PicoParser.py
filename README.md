# PicoParser.py

Convert PicoScenes `.csi` file to numpy `.npy` file with multithreaded parsing. Provides **faster** parsing with significantly **lower memory usage** compared to [PicoScenes-Python-Toolbox](https://github.com/wifisensing/PicoScenes-Python-Toolbox).

An example using the [libpico](https://codeberg.org/kiki-i/libpico) dynamic link library.

## Usage

```Shell
pip install picoparser-***-none-linux_x86_64.whl (picoparser-***-none-win_amd64.whl)
```

* Replace `***` with the corresponding version in the release

Example:

```Python
from picoparser import PicoParser

with PicoParser(filePath, 4) as parser:
  tstampNdarray, csiNdarray, magNdarray, phaseNdarray = parser.getNdarray(
    True,
    True,
    True,
    True,
    False,
  )
```

PicoParser's available methods:

```Python
def __init__(self, filePath: Path, nWorker: int):
  """
  Initialize PicoParser with file path and number of workers.

  Args:
    filePath: Path to the PicoScenes .csi file.
    nWorker: Desired number of workers, greater than the number of CPUs will be ignored.
  """

def iterFrameIdx(self) -> Iterator[tuple[int, int]]:
  """
  Yield frame start offsets and lengths from the mapped file.

  Yields:
    Tuples of frame start index and length.
  """

def iterFrame(self) -> Iterator[memoryview]:
  """
  Yield memoryview slices for each frame in the mapped file.

  Yields:
    A view of the bytes for the next frame.
  """

def iterFrameNdarray(self, interp: bool) -> Iterator[FrameNdarray]:
  """
  Yield frame data Ndarrays.

  Args:
    interp: Whether to apply interpolation along subcarrier.

  Yields:
    Processed frame ndarrays
  """

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
```

## Dependencies

* [libpico](https://codeberg.org/kiki-i/libpico)
* numpy

## License

[![AGPLv3](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://www.gnu.org/licenses/agpl-3.0.html)

Licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html).
