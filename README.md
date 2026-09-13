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
- **Up to 65x Faster Serialization**: Stack buffer allocation for small payloads, direct `PyDict_Next` iteration, indexed list/tuple access, C-register integer bounds extraction via `PyLong_AsLongLongAndOverflow`, coalesced multi-byte writes, and geometric buffer growth eliminate heap churn and the $O(N^2)$ reallocation bottlenecks of v1.
- **Up to 8.2x Faster Deserialization**: Pre-sized container allocation (`PyList_New`, `_PyDict_NewPresized`), SIMD-accelerated string decoding (`PyUnicode_FromStringAndSize`), inlined scalar parsers, and zero-exception-check bounds validation replace dynamic array resizing and abstract protocol dispatch.
- **Buffer Protocol & Subclass Support**: `loads()` and `dumps()` natively handle `bytes`, `bytearray`, and `memoryview` without copying; `dumps()` seamlessly serializes Python subclasses (`IntEnum`, `OrderedDict`, `namedtuple`).
- **Extensions & Custom Types**: Open extension mechanism (`OP_EXT = 0xFF`) with first-class `Ext(tag, data)` type, `dumps(..., default=...)` serialization callbacks, and `loads(..., ext_hook=...)` deserialization hooks.
- **File Stream APIs**: Standard `dump(obj, fp)` and `load(fp)` functions for file-like objects.
- **50% Smaller Big Integers**: Large integers ($\ge 2^{64}$) encode as raw two's-complement bytes rather than ASCII decimal strings, removing the 64-character limit and supporting arbitrary cryptographic numbers ($> 256$ bits).
- **IEEE 754 64-Bit Float Precision**: Floating point numbers default to full 64-bit double precision, avoiding the silent truncation of v1.
- **Native Little-Endian**: Multi-byte numbers and floats serialize in little-endian byte order, matching modern CPU architectures (x86_64, ARM64, Apple Silicon, RISC-V).
- **Security Safeguards**: Decoders enforce a recursion depth limit (default: 1000) to protect against stack exhaustion crashes, validate container sizes without integer overflow risks, and strictly reject unconsumed trailing bytes. Safe memory reallocation prevents leaks on memory pressure.

For the complete wire format specification, see [SPEC.md](SPEC.md).

---

## Space Usage Comparison

To evaluate wire-format efficiency, we compare Rencode v2 against Rencode v1 (`master`) and compact JSON (`separators=(',', ':')`) across realistic application workloads and datasets from `tests/timetest.py`:

| Dataset / Workload | Description | Rencode v2 (64-bit default) | Rencode v2 (32-bit mode) | Rencode v1 (master) | Compact JSON | Space Saved vs JSON |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`large_string_data`** | 10k repeated, unicode ("你好世界"), multi-line text | **48,934 B** | **48,934 B** | 48,947 B | 87,704 B | <font color="green">**+44.2%**</font> |
| **`nested_structure`** | Deeply nested hierarchy of dicts, lists, scalars | **288 B** | **264 B** | 264 B | 409 B | <font color="green">**+29.6%**</font> |
| **`complex_dict`** | Mixed keys (tuples, ints, bytes, bools, nested dicts) | **233 B** | **233 B** | 233 B | 326 B | <font color="green">**+28.5%**</font> |
| **`crypto_and_binary`** | 256-bit int, SHA-256 hashes, signatures, 1KB piece bytes | **1,596 B** | **1,596 B** | *Unsupported*\* | 2,160 B | <font color="green">**+26.1%**</font> |
| **`large_mixed_collection`**| 1,000 ints, floats, strings, booleans, mixed types | **31,329 B** | **25,997 B** | 26,018 B | 40,291 B | <font color="green">**+22.2%**</font> |
| **`geojson_gps_tracks`** | 500 GPS coordinate points with speed & sensor metadata | **72,536 B** | **64,536 B** | 64,535 B | 91,067 B | <font color="green">**+20.3%**</font> |
| **`deluge_torrent_rpc`** | Deluge RPC payload: 50 torrent status dicts (files, peers, rates) | **22,952 B** | **22,352 B** | 22,252 B | 26,551 B | <font color="green">**+13.6%**</font> |
| **`mixed_numeric_collection`**| 2,000 ints, 2,000 floats, special values (inf, nan, precision) | **35,731 B** | **23,659 B** | 23,686 B | 33,727 B | **-5.9%** (64-bit precision) |
| **TOTAL** | **Combined aggregate of all real-world workloads** | **213,599 B** | **187,571 B** | — | **282,235 B** | <font color="green">**+24.3%**</font> |

*\* Rencode v1 cannot serialize 256-bit integers (`ValueError: Number is longer than 64 characters`), whereas v2 natively encodes them in compact two's complement binary.*

### Why Rencode v2 Saves Space

1. **20% to 45% Smaller than Compact JSON**:
   - **Single-byte opcode packing**: Small integers ($-32$ to $63$), short strings ($\le 31$ bytes), and small containers ($\le 31$ items) encode type and length into a single byte, avoiding JSON's punctuation overhead (`"`, `:`, `,`, `{`, `}`, `[`, `]`).
   - **Raw Binary Efficiency**: Raw byte arrays (`bytes`) serialize 1:1 without the **+33.3% size penalty** of Base64 encoding required by JSON.
   - **Binary Numbers**: Floating-point values and large integers serialize directly in compact binary rather than verbose decimal strings.

2. **Where v2 Saves Space Over v1**:
   - **50% Smaller Big Integers**: A 64-bit integer ($2^{64}$) takes **11 bytes** in v2 (`0xFE` + length + 9 bytes two's complement) compared to **22 bytes** in v1 (`=18446744073709551616\x7f`).
   - **Varint Framing vs. ASCII Prefixes**: Large strings and byte sequences use LEB128 varints (e.g. `0xF9 \x40` = 2 bytes) instead of ASCII decimal prefixes with delimiters (`64:` = 3 bytes, `1000:` = 5 bytes).
   - **Terminator Elimination**: Collections $\ge 32$ items eliminate the trailing `0x7F` (`CHR_TERM`) byte.

3. **Floating-Point Precision Trade-off**:
   - In v1, floats defaulted to 32-bit single precision (`DEFAULT_FLOAT_BITS = 32`), silently discarding 29 bits of precision from Python's 64-bit floats (`1.1` $\to$ `1.10000002384185791`).
   - Rencode v2 defaults to full 64-bit IEEE 754 precision to guarantee exact numerical round-trips. For bandwidth-constrained applications (e.g., telemetry, games), passing `float_bits=32` achieves wire density equal to or smaller than v1.

---

## Performance Benchmark: Version 1 (`master`) vs Version 2 (`v2`)

Benchmarks were measured on Linux x86_64 using Python 3.13.12, executing both versions compiled as native Cython C-extensions over identical test payloads.

### 1. Representative Workloads & Microbenchmarks

Execution time is measured in **microseconds ($\mu s$) per operation** (lower is better):

| Benchmark Payload | Encode v1 | Encode v2 | Encode Speedup | Decode v1 | Decode v2 | Decode Speedup |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `small_int_42` | 0.07 $\mu s$ | 0.05 $\mu s$ | **1.31x** | 0.05 $\mu s$ | 0.04 $\mu s$ | **1.13x** |
| `int_200` | 0.10 $\mu s$ | 0.08 $\mu s$ | **1.23x** | 0.05 $\mu s$ | 0.04 $\mu s$ | **1.25x** |
| `int_65000` | 0.11 $\mu s$ | 0.08 $\mu s$ | **1.36x** | 0.08 $\mu s$ | 0.05 $\mu s$ | **1.60x** |
| `int_3_billion` | 0.37 $\mu s$ | 0.08 $\mu s$ | **4.43x** | 0.08 $\mu s$ | 0.06 $\mu s$ | **1.33x** |
| `str_64_chars` | 0.34 $\mu s$ | 0.08 $\mu s$ | **4.25x** | 0.13 $\mu s$ | 0.08 $\mu s$ | **1.63x** |
| `str_1000_chars` | 0.45 $\mu s$ | 0.13 $\mu s$ | **3.46x** | 0.17 $\mu s$ | 0.18 $\mu s$ | 0.94x |
| `bytes_1000` | 0.34 $\mu s$ | 0.11 $\mu s$ | **3.09x** | 0.16 $\mu s$ | 0.10 $\mu s$ | **1.60x** |
| `small_list_5` | 0.29 $\mu s$ | 0.12 $\mu s$ | **2.42x** | 0.15 $\mu s$ | 0.11 $\mu s$ | **1.36x** |
| `list_1000_ints` | 42.81 $\mu s$ | 7.37 $\mu s$ | **5.81x** | 25.97 $\mu s$ | 14.87 $\mu s$ | **1.75x** |
| `small_dict_5` | 0.96 $\mu s$ | 0.23 $\mu s$ | **4.17x** | 0.22 $\mu s$ | 0.21 $\mu s$ | **1.05x** |
| `dict_1000_pairs` | 179.29 $\mu s$ | 24.87 $\mu s$ | **7.21x** | 87.71 $\mu s$ | 74.28 $\mu s$ | **1.18x** |
| `nested_rpc_payload` | 29.80 $\mu s$ | 0.46 $\mu s$ | **64.78x** | 8.01 $\mu s$ | 0.98 $\mu s$ | **8.17x** |
| `torrent_metadata` | 28.63 $\mu s$ | 2.05 $\mu s$ | **13.97x** | 8.44 $\mu s$ | 4.82 $\mu s$ | **1.75x** |

### 2. Comprehensive Test Suite (`tests/timetest.py`)

Aggregate benchmark execution across 1,000,000 iterations per test comparing `v2` against the `master` (v1) baseline:

| Test Case | Description / Type | Encode v1 | Encode v2 | Encode Speedup | Decode v1 | Decode v2 | Decode Speedup |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `fixed_pos_int` | Single-byte positive int ($40$) | 0.148s | 0.071s | **2.1x** | 0.074s | 0.052s | **1.4x** |
| `fixed_neg_int` | Single-byte negative int ($-29$) | 0.147s | 0.075s | **2.0x** | 0.092s | 0.059s | **1.5x** |
| `int_char_size` | 8-bit integer ($100$) | 0.168s | 0.095s | **1.8x** | 0.074s | 0.052s | **1.4x** |
| `int_short_size` | 16-bit integer ($27,123$) | 0.208s | 0.094s | **2.2x** | 0.111s | 0.064s | **1.7x** |
| `int_int_size` | 32-bit integer ($7,483,648$) | 0.237s | 0.088s | **2.7x** | 0.116s | 0.066s | **1.7x** |
| `int_long_long_size`| 64-bit integer ($8.22 \times 10^{18}$) | 0.713s | 0.086s | **8.3x** | 0.128s | 0.069s | **1.9x** |
| `float_32bit` | 32-bit float value | 0.183s | 0.081s | **2.3x** | 0.096s | 0.060s | **1.6x** |
| `float_64bit` | 64-bit float value | 0.185s | 0.083s | **2.2x** | 0.096s | 0.059s | **1.6x** |
| `fixed_str` | Short string ($9$ bytes) | 0.178s | 0.080s | **2.2x** | 0.111s | 0.077s | **1.4x** |
| `str` | Variable string ($255$ bytes) | 0.330s | 0.086s | **3.8x** | 0.195s | 0.082s | **2.4x** |
| `none` | Singleton `None` | 0.147s | 0.065s | **2.3x** | 0.073s | 0.053s | **1.4x** |
| `bool` | Singleton `True` | 0.166s | 0.064s | **2.6x** | 0.073s | 0.052s | **1.4x** |
| `fixed_list` | Fixed list ($4$ elements) | 0.531s | 0.103s | **5.2x** | 0.184s | 0.112s | **1.6x** |
| `list` | Variable list ($80$ elements) | 5.388s | 0.330s | **16.3x** | 1.236s | 0.616s | **2.0x** |
| `fixed_dict` | Fixed dict ($11$ pairs) | 1.759s | 0.239s | **7.4x** | 0.626s | 0.361s | **1.7x** |
| `dict` | Variable dict ($36$ pairs) | 5.323s | 0.568s | **9.4x** | 1.658s | 0.970s | **1.7x** |
| `large_mixed_collection`\* | 6,000 mixed items | 5.896s | 0.366s | **16.1x** | 1.836s | 0.961s | **1.9x** |
| `nested_structure`\* | 5 levels nested hierarchy | 0.105s | 0.009s | **11.9x** | 0.036s | 0.023s | **1.6x** |
| `complex_dict`\* | Deeply nested mixed-key dict | 0.047s | 0.005s | **10.1x** | 0.014s | 0.011s | **1.2x** |
| `large_string_data`\* | Multi-line text & Unicode | 0.197s | 0.020s | **9.9x** | 0.023s | 0.134s | 0.2x\*\* |
| `mixed_numeric_collection`\* | 4,000 ints, floats, special nums | 4.791s | 0.389s | **12.3x** | 2.608s | 0.955s | **2.7x** |

*\* Scaled to 10,000 iterations for large payloads.*
*\*\* In v1, strings were decoded as unvalidated `bytes` by default; in v2, strings are validated UTF-8 and instantiated as Python `str` objects.*

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
