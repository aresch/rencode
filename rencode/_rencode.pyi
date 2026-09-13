from typing import Any, Callable, Optional, Tuple, Union

__version__: Tuple[str, int, int, int]
__all__: Tuple[str, ...]

class Ext:
    tag: int
    data: bytes
    def __init__(self, tag: int, data: Union[bytes, bytearray, memoryview]) -> None: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...

def dumps(
    data: Any,
    float_bits: int = 64,
    max_depth: int = 1000,
    default: Optional[Callable[[Any], Any]] = None,
) -> bytes: ...
def loads(
    data: Union[bytes, bytearray, memoryview],
    decode_utf8: Optional[bool] = None,
    max_depth: int = 1000,
    ext_hook: Optional[Callable[[int, bytes], Any]] = None,
) -> Any: ...
