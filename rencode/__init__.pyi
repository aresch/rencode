from typing import Any, BinaryIO, Callable, Optional

from rencode._rencode import Ext as Ext
from rencode._rencode import __version__ as __version__
from rencode._rencode import dumps as dumps
from rencode._rencode import loads as loads

__all__ = ["Ext", "__version__", "dump", "dumps", "load", "loads"]

def dump(
    data: Any,
    fp: BinaryIO,
    float_bits: int = 64,
    max_depth: int = 1000,
    default: Optional[Callable[[Any], Any]] = None,
) -> None: ...
def load(
    fp: BinaryIO,
    decode_utf8: Optional[bool] = None,
    max_depth: int = 1000,
    ext_hook: Optional[Callable[[int, bytes], Any]] = None,
) -> Any: ...
