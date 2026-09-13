# rencode

`rencode` is a fast, compact binary object serialization library for Python. It is designed to be space-efficient by packing type information, small integer values, and short container lengths directly into single-byte opcodes.

Originally derived from BitTorrent's `bencode` algorithm, **Rencode Version 2** modernizes the format into a high-throughput, clean binary protocol with full type fidelity, native little-endian encoding, count-prefixed framing, and strong security guarantees.

```python
import rencode

payload = {
    "user_id": 42,
    "username": "aresch",
    "active": True,
    "scores": [98.5, 99.1, 100.0],
    "avatar_jpeg": b"\xff\xd8\xff\xe0\x00\x10JFIF",
}

encoded = rencode.dumps(payload)
decoded = rencode.loads(encoded)

assert decoded == payload
assert isinstance(decoded["username"], str)
assert isinstance(decoded["avatar_jpeg"], bytes)
```

---

## What's New in Version 2

- **Type Separation**: First-class, distinct encodings for UTF-8 text (`str`) and raw binary (`bytes`). `loads()` seamlessly preserves both without ambiguous `decode_utf8` flags.
- **Collection Fidelity**: Lists (`list`) and tuples (`tuple`) maintain their distinct types across serialization (`loads(dumps([1, 2])) == [1, 2]`).
- **Framing & Delimiter Elimination**: All variable-length sequences, strings, and maps are count- or length-prefixed with LEB128 varints. The legacy bencode ASCII string length parsing (`255:data`) and container terminator scanning (`0x7F`) have been completely eliminated.
- **Up to 5.38x Faster Serialization**: A geometric buffer growth strategy eliminates the $O(N^2)$ reallocation bottlenecks of v1.
- **Up to 1.59x Faster Deserialization**: Pre-sized container allocation (`PyList_New`, `_PyDict_NewPresized`) replaces dynamic array resizing.
- **50% Smaller Big Integers**: Large integers ($\ge 2^{64}$) encode as raw two's-complement bytes rather than ASCII decimal strings, removing the 64-character limit and supporting arbitrary cryptographic numbers ($> 256$ bits).
- **IEEE 754 64-Bit Float Precision**: Floating point numbers default to full 64-bit double precision, avoiding the silent truncation of v1.
- **Native Little-Endian**: Multi-byte numbers and floats serialize in little-endian byte order, matching modern CPU architectures (x86_64, ARM64, Apple Silicon, RISC-V).
- **Security Safeguards**: Decoders enforce a recursion depth limit (default: 1000) to protect against stack exhaustion crashes, and strictly reject unconsumed trailing bytes.

For the complete wire format specification, see [SPEC.md](SPEC.md).

---

## Benchmark Comparison: Version 1 (`master`) vs Version 2 (`v2`)

Benchmarks were measured on Linux x86_64 using Python 3.13.12, executing both versions compiled as native Cython C-extensions over identical test payloads.

### 1. Performance & Speedup

Execution time is measured in **microseconds ($\mu s$) per operation** (lower is better):

| Benchmark Payload | Encode v1 | Encode v2 | Encode Speedup | Decode v1 | Decode v2 | Decode Speedup |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `small_int_42` | 0.07 $\mu s$ | 0.06 $\mu s$ | **1.11x** | 0.05 $\mu s$ | 0.04 $\mu s$ | **1.09x** |
| `int_200` | 0.10 $\mu s$ | 0.10 $\mu s$ | **1.04x** | 0.05 $\mu s$ | 0.04 $\mu s$ | **1.05x** |
| `int_65000` | 0.11 $\mu s$ | 0.10 $\mu s$ | **1.08x** | 0.08 $\mu s$ | 0.06 $\mu s$ | **1.27x** |
| `int_3_billion` | 0.37 $\mu s$ | 0.11 $\mu s$ | **3.42x** | 0.08 $\mu s$ | 0.06 $\mu s$ | **1.32x** |
| `str_64_chars` | 0.34 $\mu s$ | 0.10 $\mu s$ | **3.29x** | 0.13 $\mu s$ | 0.10 $\mu s$ | **1.41x** |
| `str_1000_chars` | 0.45 $\mu s$ | 0.17 $\mu s$ | **2.71x** | 0.17 $\mu s$ | 0.24 $\mu s$ | 0.70x |
| `bytes_1000` | 0.34 $\mu s$ | 0.16 $\mu s$ | **2.19x** | 0.16 $\mu s$ | 0.13 $\mu s$ | **1.29x** |
| `small_list_5` | 0.29 $\mu s$ | 0.13 $\mu s$ | **2.26x** | 0.15 $\mu s$ | 0.11 $\mu s$ | **1.35x** |
| `list_1000_ints` | 42.81 $\mu s$ | 27.68 $\mu s$ | **1.55x** | 25.97 $\mu s$ | 16.38 $\mu s$ | **1.59x** |
| `small_dict_5` | 0.96 $\mu s$ | 0.28 $\mu s$ | **3.48x** | 0.22 $\mu s$ | 0.21 $\mu s$ | **1.04x** |
| `dict_1000_pairs` | 179.29 $\mu s$ | 54.06 $\mu s$ | **3.32x** | 87.71 $\mu s$ | 81.04 $\mu s$ | **1.08x** |
| `nested_rpc_payload` | 29.80 $\mu s$ | 5.54 $\mu s$ | **5.38x** | 8.01 $\mu s$ | 8.09 $\mu s$ | 0.99x |
| `torrent_metadata` | 28.63 $\mu s$ | 5.93 $\mu s$ | **4.83x** | 8.44 $\mu s$ | 8.20 $\mu s$ | **1.03x** |

### 2. Wire Size & Space Savings

| Benchmark Payload | Master (v1) | V2 (v2) | Size Difference | Space Savings % | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `small_int_42` | 1 B | 1 B | 0 B | **0.0%** | Embedded in 1-byte opcode |
| `int_200` | 3 B | 3 B | 0 B | **0.0%** | Small integer representation |
| `int_65000` | 5 B | 5 B | 0 B | **0.0%** | 16-bit integer representation |
| `int_3_billion` | 9 B | 9 B | 0 B | **0.0%** | 32-bit integer representation |
| `bigint_2_64` | 22 B | 11 B | **-11 B** | **+50.0%** | **2x smaller**: Raw binary vs ASCII decimal |
| `short_str` (`"hello world"`) | 12 B | 12 B | 0 B | **0.0%** | Fixed UTF-8 string (1-byte opcode prefix) |
| `str_64_chars` | 67 B | 66 B | **-1 B** | **+1.5%** | LEB128 varint vs `64:` ASCII prefix |
| `str_1000_chars` | 1,005 B | 1,003 B | **-2 B** | **+0.2%** | LEB128 varint vs `1000:` ASCII prefix |
| `str_64k_chars` | 65,542 B | 65,540 B | **-2 B** | **+0.0%** | LEB128 varint vs `65536:` ASCII prefix |
| `bytes_1000` | 1,005 B | 1,003 B | **-2 B** | **+0.2%** | Distinct binary type with varint length |
| `small_list_5` | 6 B | 6 B | 0 B | **0.0%** | Fixed list (1-byte opcode prefix) |
| `list_1000_ints` | 2,830 B | 2,811 B | **-19 B** | **+0.7%** | Count-prefixed, eliminates `0x7F` terminator |
| `small_dict_5` | 16 B | 16 B | 0 B | **0.0%** | Fixed dict (1-byte opcode prefix) |
| `dict_1000_pairs` | 9,830 B | 9,811 B | **-19 B** | **+0.2%** | Count-prefixed, eliminates `0x7F` terminator |
| `float_pi` | 5 B | 9 B | +4 B | -80.0% | **Full 64-bit IEEE 754 precision** |
| `nested_rpc_payload` | 1,008 B | 1,092 B | +84 B | -8.3% | Contains 21 floats stored as 64-bit doubles* |
| `torrent_metadata` | 2,046 B | 2,049 B | +3 B | -0.1% | Realistic torrent dictionary payload |

*\* In v1, floats defaulted to 32-bit (`DEFAULT_FLOAT_BITS = 32`), which truncated 64-bit Python floats and lost precision. In v2, floats default to full 64-bit double precision. Passing `float_bits=32` in v2 produces **1,008 B** for `nested_rpc_payload`, identical to v1.*

---

## Development

Use `uv` for all local environment and development workflows:

```bash
# Install and compile Cython extension in editable mode
uv sync --all-groups

# Run unit tests
uv run pytest

# Lint and format
uv run ruff check rencode tests
uv run ruff format rencode tests

# Run performance benchmark
uv run python tests/timetest.py
```

---

## Author
* Andrew Resch <andrewresch@gmail.com>
* Website: https://github.com/aresch/rencode

## License
See [COPYING](COPYING) for license information.
