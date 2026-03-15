# PicoParser.py

Convert PicoScenes `.csi` file to numpy `.npy` file with multithreaded parsing. Provides **faster** parsing with significantly **lower memory usage** compared to [PicoScenes-Python-Toolbox](https://github.com/wifisensing/PicoScenes-Python-Toolbox).

An example using the [libpico](https://codeberg.org/kiki-i/libpico) dynamic link library.

## Usage

```Shell
pip install picoparser
```

or

```Shell
pip install picoparser-***-py3-none-***.whl
```

* Replace `***` with the corresponding version in the releases (Or build yourself).

Example:

```Python
from picoparser import PicoParser

with PicoParser(filePath, 4) as parser:

  # Only works on single pair of RX and TX NIC
  tstampNdarray, csiNdarray, magNdarray, phaseNdarray = parser.getNdarray(
    True,
    True,
    True,
    True,
  )

  # Iterate each frame for further processing
  for x in parser.iterFrames():
    print(x.standardHeader.addr1)
```

PicoParser's available methods:

```Python
def __init__(self, filePath: Path, nWorker: int = 1):
  """
  Initialize PicoParser with file path and number of workers.

  Args:
    filePath: Path to the PicoScenes .csi file.
    nWorker: Desired number of workers, greater than the number of CPUs will be ignored.
  """

def iterFrameIndices(self) -> Iterator[tuple[int, int]]:
  """
  Yield frame start offsets and lengths from the mapped file.

  Yields:
    Tuples of frame start index and length.
  """

def iterFramesRaw(self) -> Iterator[memoryview]:
  """
  Yield memoryview slices for each frame in the memory mapped file.

  Yields:
    A view of the bytes for frames.
  """

def iterFrames(self, interp: bool = False) -> Iterator[PicoParserFrame]:
  """
  Yield frame data.

  Args:
    interp: Whether to apply interpolation along subcarrier.

  Yields:
    Processed frames.
  """

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
  Return the whole file's ndarrays according to requested data types. (Only works on single pair of RX and TX NIC)

  Args:
    enableTs: Include timestamp data if True.
    enableCsi: Include CSI data if True.
    enableMag: Include magnitude data if True.
    enablePhase: Include phase data if True.
    interp: Whether to apply interpolation along subcarrier.

  Returns:
    Ndarrays for each requested component.
  """
```

## Build

1. Build [libpico](https://codeberg.org/kiki-i/libpico) according its `README.md`.

2. Move `libpico.so` (`libpico.dll` on Windows) to `src/picoparser/_native/`.

3. Build wheels with `python -m build`.


## Dependencies

* [libpico](https://codeberg.org/kiki-i/libpico)
* numpy

## If you find this helpful

Please cite [**my works**](https://scholar.google.com/citations?user=XiudsEIAAAAJ).

## License

[![AGPLv3](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://www.gnu.org/licenses/agpl-3.0.html)

Licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html).
