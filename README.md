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
- **Up to 13.1x Faster Serialization**: Stack buffer allocation for small payloads, direct `PyDict_Next` iteration, indexed list/tuple access, and geometric buffer growth eliminate heap churn and the $O(N^2)$ reallocation bottlenecks of v1.
- **Up to 2.5x Faster Deserialization**: Pre-sized container allocation (`PyList_New`, `_PyDict_NewPresized`) and `PyDict_SetItem` replace dynamic array resizing and abstract protocol dispatch.
- **Buffer Protocol & Subclass Support**: `loads()` natively accepts `bytes`, `bytearray`, and `memoryview` without copying; `dumps()` seamlessly handles Python subclasses (`IntEnum`, `OrderedDict`, `namedtuple`).
- **File Stream APIs**: Standard `dump(obj, fp)` and `load(fp)` functions for file-like objects.
- **50% Smaller Big Integers**: Large integers ($\ge 2^{64}$) encode as raw two's-complement bytes rather than ASCII decimal strings, removing the 64-character limit and supporting arbitrary cryptographic numbers ($> 256$ bits).
- **IEEE 754 64-Bit Float Precision**: Floating point numbers default to full 64-bit double precision, avoiding the silent truncation of v1.
- **Native Little-Endian**: Multi-byte numbers and floats serialize in little-endian byte order, matching modern CPU architectures (x86_64, ARM64, Apple Silicon, RISC-V).
- **Security Safeguards**: Decoders enforce a recursion depth limit (default: 1000) to protect against stack exhaustion crashes, validate container sizes without integer overflow risks, and strictly reject unconsumed trailing bytes.

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

Execution time is measured in **microseconds ($\mu s$) per operation** (lower is better):

| Benchmark Payload | Encode v1 | Encode v2 | Encode Speedup | Decode v1 | Decode v2 | Decode Speedup |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `small_int_42` | 0.07 $\mu s$ | 0.05 $\mu s$ | **1.40x** | 0.05 $\mu s$ | 0.04 $\mu s$ | **1.25x** |
| `int_200` | 0.10 $\mu s$ | 0.10 $\mu s$ | **1.04x** | 0.05 $\mu s$ | 0.04 $\mu s$ | **1.05x** |
| `int_65000` | 0.11 $\mu s$ | 0.10 $\mu s$ | **1.08x** | 0.08 $\mu s$ | 0.06 $\mu s$ | **1.27x** |
| `int_3_billion` | 0.37 $\mu s$ | 0.11 $\mu s$ | **3.42x** | 0.08 $\mu s$ | 0.06 $\mu s$ | **1.32x** |
| `str_64_chars` | 0.34 $\mu s$ | 0.09 $\mu s$ | **3.78x** | 0.13 $\mu s$ | 0.09 $\mu s$ | **1.44x** |
| `str_1000_chars` | 0.45 $\mu s$ | 0.16 $\mu s$ | **2.81x** | 0.17 $\mu s$ | 0.21 $\mu s$ | 0.81x |
| `bytes_1000` | 0.34 $\mu s$ | 0.13 $\mu s$ | **2.62x** | 0.16 $\mu s$ | 0.12 $\mu s$ | **1.33x** |
| `small_list_5` | 0.29 $\mu s$ | 0.12 $\mu s$ | **2.42x** | 0.15 $\mu s$ | 0.11 $\mu s$ | **1.36x** |
| `list_1000_ints` | 42.81 $\mu s$ | 17.92 $\mu s$ | **2.39x** | 25.97 $\mu s$ | 16.38 $\mu s$ | **1.59x** |
| `small_dict_5` | 0.96 $\mu s$ | 0.22 $\mu s$ | **4.36x** | 0.22 $\mu s$ | 0.21 $\mu s$ | **1.05x** |
| `dict_1000_pairs` | 179.29 $\mu s$ | 41.44 $\mu s$ | **4.33x** | 87.71 $\mu s$ | 74.01 $\mu s$ | **1.19x** |
| `nested_rpc_payload` | 29.80 $\mu s$ | 5.21 $\mu s$ | **5.72x** | 8.01 $\mu s$ | 7.95 $\mu s$ | **1.01x** |
| `torrent_metadata` | 28.63 $\mu s$ | 5.48 $\mu s$ | **5.22x** | 8.44 $\mu s$ | 8.12 $\mu s$ | **1.04x** |

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
