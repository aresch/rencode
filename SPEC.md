# rencode Data Format Specification

## Overview

rencode uses a single-byte type code system to identify different data types, with some types having their values embedded directly in the type code for space efficiency. The format is designed to be compact while maintaining good performance.

## Type Codes

### Fixed Integers (Positive)
- Range: 0 to 43
- Type code: `0x00` to `0x2B` (INT_POS_FIXED_START to INT_POS_FIXED_START + INT_POS_FIXED_COUNT - 1)
- Value is embedded in type code

### Fixed Integers (Negative)
- Range: -1 to -32
- Type code: `0x46` to `0x65` (INT_NEG_FIXED_START to INT_NEG_FIXED_START + INT_NEG_FIXED_COUNT - 1)
- Value is embedded in type code

### Variable Length Integers
- 8-bit signed integer: `0x3E` (CHR_INT1) followed by 1 byte
- 16-bit signed integer: `0x3F` (CHR_INT2) followed by 2 bytes
- 32-bit signed integer: `0x40` (CHR_INT4) followed by 4 bytes
- 64-bit signed integer: `0x41` (CHR_INT8) followed by 8 bytes
- Big number: `0x3D` (CHR_INT) followed by ASCII string and `0x7F` (CHR_TERM)

### Floating Point Numbers
- 32-bit float: `0x42` (CHR_FLOAT32) followed by 4 bytes
- 64-bit float: `0x2C` (CHR_FLOAT64) followed by 8 bytes

### Strings
- Fixed length strings (1-64 bytes): `0x80` to `0xBF` (STR_FIXED_START to STR_FIXED_START + STR_FIXED_COUNT - 1)
- Variable length strings: ASCII length followed by `:` and string data

### Lists
- Fixed length lists (1-64 items): `0xC0` to `0xFF` (LIST_FIXED_START to LIST_FIXED_START + LIST_FIXED_COUNT - 1)
- Variable length lists: `0x3B` (CHR_LIST) followed by items and `0x7F` (CHR_TERM)

### Dictionaries
- Fixed length dictionaries (1-25 items): `0x66` to `0x7E` (DICT_FIXED_START to DICT_FIXED_START + DICT_FIXED_COUNT - 1)
- Variable length dictionaries: `0x3C` (CHR_DICT) followed by key-value pairs and `0x7F` (CHR_TERM)

### Special Values
- `None`: `0x45` (CHR_NONE)
- `True`: `0x43` (CHR_TRUE)
- `False`: `0x44` (CHR_FALSE)

## Byte Order

All multi-byte values (integers, floats) are stored in network byte order (big-endian). The implementation automatically handles byte order conversion on little-endian systems.

## String Encoding

- By default, strings (str) are stored as UTF-8 encoded bytes
- When `decode_utf8=True` is specified, bytes are decoded from UTF-8 to Python strings (str) during decoding

## Limitations

- Maximum integer length when written as ASCII string: 64 characters
- Maximum fixed string length: 64 bytes
- Maximum fixed list length: 64 items
- Maximum fixed dictionary length: 25 items

## Examples

```
1           -> 0x01
40          -> 0x28
-10         -> 0x4F
-29         -> 0x62
100         -> 0x3E 0x64
-100        -> 0x3E 0x9C
27123       -> 0x3F 0x69 0xF3
-27123      -> 0x3F 0x96 0x0D
7483648     -> 0x40 0x00 0x72 0x31 0x00
-7483648    -> 0x40 0xFF 0x8D 0xCF 0x00
1234.56     -> 0x42 0x44 0x9A 0x51 0xEC
"foobar"    -> 0x86 0x66 0x6F 0x6F 0x62 0x61 0x72
"f" * 255   -> "255:" + "f" * 255

# Fixed length list (3 items)
[1, 2, 3]   -> 0xC3 0x01 0x02 0x03

# Variable length list (terminated)
[1, 2, 3]   -> 0x3B 0x01 0x02 0x03 0x7F

# Fixed length dict (1 item)
{"a": 1}    -> 0x67 0x81 0x61 0x01

# Variable length dict (terminated)
{"a": 1}    -> 0x3C 0x81 0x61 0x01 0x7F

None        -> 0x45
True        -> 0x43
False       -> 0x44
```

