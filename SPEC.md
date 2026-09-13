# rencode Data Format Specification (Version 2)

## 1. Overview

`rencode` Version 2 is a compact, high-performance binary object serialization format. It is designed to be space-efficient by embedding values and lengths directly into single-byte typecodes, while maintaining high throughput, predictable framing, full type fidelity, and strong security properties.

Version 2 establishes the following core principles:
- **Clean Opcode Space**: All 256 single-byte opcodes (`0x00`–`0xFF`) are systematically partitioned with zero unused opcodes and no legacy ASCII length parsing.
- **Type Separation**: Distinct, first-class types for UTF-8 text (`str`) and raw binary (`bytes`).
- **Collection Fidelity**: Lists (`list`) and tuples (`tuple`) maintain their distinct identities across serialization.
- **Count-Prefixed Framing**: All variable-length sequences, strings, and maps are count- or length-prefixed using LEB128 varints. No terminator scanning or delimiter searching is required.
- **Float Precision**: Floating point numbers default to IEEE 754 64-bit double precision.
- **Arbitrary Precision Integers**: Big integers beyond 64-bit bounds are encoded as compact binary two's-complement byte sequences without arbitrary decimal character limits.
- **Native Little-Endian**: Multi-byte integers and floating point numbers are encoded in little-endian byte order, matching modern CPU architectures (x86_64, ARM64, RISC-V).

---

## 2. Byte Order

All multi-byte integer types (`int16`, `int32`, `int64`) and floating-point types (`float32`, `float64`) are serialized in **little-endian** byte order.

---

## 3. Variable-Length Integers (LEB128 Varint)

For lengths and item counts that exceed fixed opcode limits, unsigned LEB128 (Little-Endian Base 128) encoding is used:
- Each byte contains 7 bits of value (bits 0–6, least significant first).
- Bit 7 is the continuation bit (`1` indicates more bytes follow, `0` indicates the final byte).
- Values from `0` to `127` take 1 byte (`0x00`–`0x7F`).
- Values from `128` to `16,383` take 2 bytes (e.g. `300` -> `0xAC 0x02`).

---

## 4. Opcode Allocation Map

The 256 single-byte opcodes (`0x00`–`0xFF`) are organized as follows:

| Opcode Range | Count | Type | Encoding Format |
| :--- | :--- | :--- | :--- |
| `0x00`–`0x3F` | 64 | Fixed Positive Int | Direct value: `0` to `63` |
| `0x40`–`0x5F` | 32 | Fixed Negative Int | Direct value: `-1` to `-32` (value = `-(opcode - 0x40 + 1)`) |
| `0x60`–`0x7F` | 32 | Fixed UTF-8 String | Length: `0` to `31` bytes (`0x60 + length`), followed by UTF-8 bytes |
| `0x80`–`0x9F` | 32 | Fixed Binary Bytes | Length: `0` to `31` bytes (`0x80 + length`), followed by raw bytes |
| `0xA0`–`0xBF` | 32 | Fixed List | Count: `0` to `31` items (`0xA0 + count`), followed by serialized items |
| `0xC0`–`0xDF` | 32 | Fixed Dictionary | Count: `0` to `31` pairs (`0xC0 + count`), followed by key/value pairs |
| `0xE0`–`0xEF` | 16 | Fixed Tuple | Count: `0` to `15` items (`0xE0 + count`), followed by serialized items |
| `0xF0` | 1 | `None` / Null | 1-byte opcode (`0xF0`) |
| `0xF1` | 1 | `False` | 1-byte opcode (`0xF1`) |
| `0xF2` | 1 | `True` | 1-byte opcode (`0xF2`) |
| `0xF3` | 1 | `int8` | Opcode followed by 1 byte signed integer (-128 to 127) |
| `0xF4` | 1 | `int16` | Opcode followed by 2 bytes signed integer (little-endian) |
| `0xF5` | 1 | `int32` | Opcode followed by 4 bytes signed integer (little-endian) |
| `0xF6` | 1 | `int64` | Opcode followed by 8 bytes signed integer (little-endian) |
| `0xF7` | 1 | `float32` | Opcode followed by 4 bytes IEEE 754 single-precision float (little-endian) |
| `0xF8` | 1 | `float64` | Opcode followed by 8 bytes IEEE 754 double-precision float (little-endian) |
| `0xF9` | 1 | Variable UTF-8 String | Opcode followed by LEB128 byte length, then UTF-8 bytes |
| `0xFA` | 1 | Variable Binary Bytes | Opcode followed by LEB128 byte length, then raw bytes |
| `0xFB` | 1 | Variable List | Opcode followed by LEB128 item count, then serialized items |
| `0xFC` | 1 | Variable Dictionary | Opcode followed by LEB128 pair count, then serialized key/value pairs |
| `0xFD` | 1 | Variable Tuple | Opcode followed by LEB128 item count, then serialized items |
| `0xFE` | 1 | Big Integer | Opcode followed by LEB128 byte length, then two's complement signed bytes (little-endian) |
| `0xFF` | 1 | Extension (`EXT`) | Opcode followed by LEB128 extension tag, LEB128 byte length, then payload |

---

## 5. Detailed Type Specifications

### 5.1 Integers
Integers are serialized using the smallest representation that can losslessly represent the value:
1. `0 <= x <= 63`: 1 byte (`0x00` to `0x3F`).
2. `-32 <= x <= -1`: 1 byte (`0x40` to `0x5F`).
3. `-128 <= x <= 127`: `0xF3` (`int8`) + 1 byte.
4. `-32,768 <= x <= 32,767`: `0xF4` (`int16`) + 2 bytes (little-endian).
5. `-2,147,483,648 <= x <= 2,147,483,647`: `0xF5` (`int32`) + 4 bytes (little-endian).
6. `-9,223,372,036,854,775,808 <= x <= 9,223,372,036,854,775,807`: `0xF6` (`int64`) + 8 bytes (little-endian).
7. Integers exceeding 64 bits: `0xFE` (`BIGINT`) + LEB128 byte length + two's complement signed little-endian bytes.

### 5.2 Floating Point Numbers
- Standard Python `float` values are serialized as `0xF8` (`float64`, 8-byte IEEE 754, little-endian).
- If `float_bits=32` is explicitly requested, values are serialized as `0xF7` (`float32`, 4-byte IEEE 754, little-endian).

### 5.3 Strings (`str`)
Strings represent UTF-8 encoded Unicode text:
- Length `0 <= L <= 31` bytes: `0x60 + L`, followed immediately by `L` UTF-8 bytes.
- Length `L >= 32` bytes: `0xF9`, followed by LEB128 encoded byte length `L`, followed by `L` UTF-8 bytes.
- String decoding validates UTF-8 validity.

### 5.4 Binary Data (`bytes`)
Binary data represents arbitrary byte sequences:
- Length `0 <= L <= 31` bytes: `0x80 + L`, followed immediately by `L` raw bytes.
- Length `L >= 32` bytes: `0xFA`, followed by LEB128 encoded byte length `L`, followed by `L` raw bytes.

### 5.5 Lists (`list`)
- Count `0 <= C <= 31` items: `0xA0 + C`, followed by `C` serialized elements.
- Count `C >= 32` items: `0xFB`, followed by LEB128 encoded count `C`, followed by `C` serialized elements.
- Decoded strictly as Python `list`.

### 5.6 Tuples (`tuple`)
- Count `0 <= C <= 15` items: `0xE0 + C`, followed by `C` serialized elements.
- Count `C >= 16` items: `0xFD`, followed by LEB128 encoded count `C`, followed by `C` serialized elements.
- Decoded strictly as Python `tuple`.

### 5.7 Dictionaries (`dict`)
- Count `0 <= C <= 31` key-value pairs: `0xC0 + C`, followed by `C` serialized pairs (key followed by value).
- Count `C >= 32` pairs: `0xFC`, followed by LEB128 encoded count `C`, followed by `C` serialized pairs.
- Keys may be any serializable and hashable type.

### 5.8 Constants
- `None`: `0xF0`
- `False`: `0xF1`
- `True`: `0xF2`

### 5.9 Extensions (`EXT`)
Opcode `0xFF` provides an open extension mechanism:
- Format: `0xFF` + LEB128 `tag` + LEB128 `byte_length` + `payload_bytes`.
- Tags `0x00`–`0x7F` are reserved for future standardization (e.g. timestamps, UUIDs, decimals).
- Tags `>= 0x80` are available for application-specific custom types.

---

## 6. Security and Validation Guarantees

1. **Recursion Limit**: Decoders must enforce a maximum nesting depth (default: 1000) to protect against stack exhaustion attacks. Exceeding this depth raises `ValueError`.
2. **Trailing Data**: By default, `loads()` strictly validates that all input bytes are consumed. If unconsumed bytes remain, `ValueError` is raised.
3. **No Unbounded Pre-allocation**: Varint lengths for strings and containers are checked against the remaining payload size before allocation. If a declared container size or byte length exceeds the remaining payload, `ValueError` or `IndexError` is raised immediately.

---

## 7. Examples

```
# Integers
0               -> 0x00
63              -> 0x3F
-1              -> 0x40
-32             -> 0x5F
100             -> 0xF3 0x64
-100            -> 0xF3 0x9C
1000            -> 0xF4 0xE8 0x03
-1000           -> 0xF4 0x18 0xFC
1000000         -> 0xF5 0x40 0x42 0x0F 0x00
2**64           -> 0xFE 0x09 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x01

# Floats
1.0             -> 0xF8 0x00 0x00 0x00 0x00 0x00 0x00 0xF0 0x3F

# Booleans & None
None            -> 0xF0
False           -> 0xF1
True            -> 0xF2

# Strings and Bytes
"hi"            -> 0x62 0x68 0x69
b"hi"           -> 0x82 0x68 0x69
""              -> 0x60
b""             -> 0x80

# List and Tuple
[1, 2]          -> 0xA2 0x01 0x02
(1, 2)          -> 0xE2 0x01 0x02

# Dict
{"a": 1}        -> 0xC1 0x61 0x61 0x01
```
