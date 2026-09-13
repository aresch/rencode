#
# test_rencode.py
#
# Copyright (C) 2025 Andrew Resch <andrewresch@gmail.com>
#
# rencode is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# rencode is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rencode. If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA 02110-1301, USA.
#

import collections
import io
import pickle
import struct
import unittest
from enum import IntEnum

import rencode


def leb128_encode(val: int) -> bytes:
    res = bytearray()
    while True:
        b = val & 0x7F
        val >>= 7
        if val != 0:
            res.append(b | 0x80)
        else:
            res.append(b)
            break
    return bytes(res)


class TestRencodeV2(unittest.TestCase):
    # ----------------------------------------------------------------------
    # Version & Basics
    # ----------------------------------------------------------------------
    def test_version(self):
        self.assertTrue(hasattr(rencode, "__version__"))
        self.assertEqual(rencode.__version__[0], "Cython")
        self.assertEqual(rencode.__version__[1], 2)

    # ----------------------------------------------------------------------
    # Fixed Positive Integers (0 to 63 -> 0x00 to 0x3F)
    # ----------------------------------------------------------------------
    def test_encode_fixed_pos_int(self):
        self.assertEqual(rencode.dumps(0), b"\x00")
        self.assertEqual(rencode.dumps(1), b"\x01")
        self.assertEqual(rencode.dumps(40), b"\x28")
        self.assertEqual(rencode.dumps(63), b"\x3f")

    def test_decode_fixed_pos_int(self):
        for i in (0, 1, 10, 42, 63):
            self.assertEqual(rencode.loads(rencode.dumps(i)), i)

    # ----------------------------------------------------------------------
    # Fixed Negative Integers (-1 to -32 -> 0x40 to 0x5F)
    # ----------------------------------------------------------------------
    def test_encode_fixed_neg_int(self):
        self.assertEqual(rencode.dumps(-1), b"\x40")
        self.assertEqual(rencode.dumps(-10), b"\x49")
        self.assertEqual(rencode.dumps(-32), b"\x5f")

    def test_decode_fixed_neg_int(self):
        for i in (-1, -5, -10, -20, -32):
            self.assertEqual(rencode.loads(rencode.dumps(i)), i)

    # ----------------------------------------------------------------------
    # Variable-Length Integers (int8, int16, int32, int64, BigInt)
    # ----------------------------------------------------------------------
    def test_encode_decode_int8(self):
        # -128 to -33 and 64 to 127
        self.assertEqual(rencode.dumps(64), b"\xf3\x40")
        self.assertEqual(rencode.dumps(100), b"\xf3\x64")
        self.assertEqual(rencode.dumps(-33), b"\xf3\xdf")
        self.assertEqual(rencode.dumps(-128), b"\xf3\x80")
        for i in (-128, -100, -33, 64, 100, 127):
            self.assertEqual(rencode.loads(rencode.dumps(i)), i)

    def test_encode_decode_int16(self):
        # 16-bit signed, little-endian: 0xF4 + 2 bytes
        self.assertEqual(rencode.dumps(1000), b"\xf4\xe8\x03")
        self.assertEqual(rencode.dumps(-1000), b"\xf4\x18\xfc")
        self.assertEqual(rencode.dumps(27123), b"\xf4" + struct.pack("<h", 27123))
        self.assertEqual(rencode.dumps(-27123), b"\xf4" + struct.pack("<h", -27123))
        for i in (-32768, -27123, -129, 128, 1000, 27123, 32767):
            self.assertEqual(rencode.loads(rencode.dumps(i)), i)

    def test_encode_decode_int32(self):
        # 32-bit signed, little-endian: 0xF5 + 4 bytes
        self.assertEqual(rencode.dumps(1000000), b"\xf5\x40\x42\x0f\x00")
        self.assertEqual(rencode.dumps(-1000000), b"\xf5\xc0\xbd\xf0\xff")
        self.assertEqual(rencode.dumps(7483648), b"\xf5" + struct.pack("<i", 7483648))
        self.assertEqual(rencode.dumps(-7483648), b"\xf5" + struct.pack("<i", -7483648))
        for i in (-2147483648, -7483648, -32769, 32768, 7483648, 2147483647):
            self.assertEqual(rencode.loads(rencode.dumps(i)), i)

    def test_encode_decode_int64(self):
        # 64-bit signed, little-endian: 0xF6 + 8 bytes
        big = 8223372036854775808
        self.assertEqual(rencode.dumps(big), b"\xf6" + struct.pack("<q", big))
        self.assertEqual(rencode.dumps(-big), b"\xf6" + struct.pack("<q", -big))
        for i in (
            -9223372036854775808,
            -8223372036854775808,
            -2147483649,
            2147483648,
            8223372036854775808,
            9223372036854775807,
        ):
            self.assertEqual(rencode.loads(rencode.dumps(i)), i)

    def test_encode_decode_bigint(self):
        # Arbitrary precision integers exceeding 64 bits: 0xFE + varint len + two's complement bytes
        big_pos = 2**64
        big_neg = -(2**64)
        crypto_int = 2**256 - 1
        crypto_int_neg = -(2**256)

        enc = rencode.dumps(big_pos)
        self.assertEqual(enc[0], 0xFE)
        self.assertEqual(rencode.loads(enc), big_pos)
        self.assertEqual(rencode.loads(rencode.dumps(big_neg)), big_neg)
        self.assertEqual(rencode.loads(rencode.dumps(crypto_int)), crypto_int)
        self.assertEqual(rencode.loads(rencode.dumps(crypto_int_neg)), crypto_int_neg)

        # Ensure massive integers (>64 characters) serialize without overflow
        huge = 10**100
        self.assertEqual(rencode.loads(rencode.dumps(huge)), huge)

    # ----------------------------------------------------------------------
    # Floating Point Numbers (float64 default, float32 optional)
    # ----------------------------------------------------------------------
    def test_encode_decode_float64(self):
        # Default Python float: 0xF8 + 8 bytes little-endian double
        v = 1.1
        enc = rencode.dumps(v)
        self.assertEqual(enc[0], 0xF8)
        self.assertEqual(enc[1:], struct.pack("<d", v))
        # Exact round-trip fidelity
        self.assertEqual(rencode.loads(enc), v)

        for f in (0.0, -0.0, 1234.56789, -9876.54321, 1e20, -1e-20):
            self.assertEqual(rencode.loads(rencode.dumps(f)), f)

    def test_encode_decode_float32(self):
        # Explicit 32-bit float: 0xF7 + 4 bytes little-endian single
        v = 1234.5
        enc = rencode.dumps(v, float_bits=32)
        self.assertEqual(enc[0], 0xF7)
        self.assertEqual(enc[1:], struct.pack("<f", v))
        self.assertAlmostEqual(rencode.loads(enc), v, places=4)

    def test_encode_float_invalid_size(self):
        with self.assertRaises(ValueError):
            rencode.dumps(1234.56, float_bits=36)

    # ----------------------------------------------------------------------
    # Constants: None and Booleans
    # ----------------------------------------------------------------------
    def test_encode_decode_constants(self):
        self.assertEqual(rencode.dumps(None), b"\xf0")
        self.assertEqual(rencode.loads(b"\xf0"), None)
        self.assertIsNone(rencode.loads(rencode.dumps(None)))

        self.assertEqual(rencode.dumps(False), b"\xf1")
        self.assertEqual(rencode.loads(b"\xf1"), False)
        self.assertIs(rencode.loads(rencode.dumps(False)), False)

        self.assertEqual(rencode.dumps(True), b"\xf2")
        self.assertEqual(rencode.loads(b"\xf2"), True)
        self.assertIs(rencode.loads(rencode.dumps(True)), True)

    # ----------------------------------------------------------------------
    # Strings (str / UTF-8)
    # ----------------------------------------------------------------------
    def test_encode_decode_fixed_str(self):
        # Length 0 to 31 -> 0x60 + length
        self.assertEqual(rencode.dumps(""), b"\x60")
        self.assertEqual(rencode.dumps("a"), b"\x61a")
        self.assertEqual(rencode.dumps("hello"), b"\x65hello")
        s31 = "x" * 31
        self.assertEqual(rencode.dumps(s31), b"\x7f" + s31.encode("utf-8"))

        res = rencode.loads(rencode.dumps("hello"))
        self.assertEqual(res, "hello")
        self.assertIsInstance(res, str)

        # Multi-byte UTF-8
        unicode_str = "fööbar"
        utf8_bytes = unicode_str.encode("utf-8")
        self.assertEqual(
            rencode.dumps(unicode_str), bytes([0x60 + len(utf8_bytes)]) + utf8_bytes
        )
        self.assertEqual(rencode.loads(rencode.dumps(unicode_str)), unicode_str)

    def test_encode_decode_variable_str(self):
        # Length >= 32 -> 0xF9 + LEB128 len + UTF-8 bytes
        s32 = "a" * 32
        self.assertEqual(rencode.dumps(s32), b"\xf9\x20" + s32.encode("utf-8"))
        self.assertEqual(rencode.loads(rencode.dumps(s32)), s32)

        s500 = "hello world! " * 40
        utf8 = s500.encode("utf-8")
        expected_prefix = b"\xf9" + leb128_encode(len(utf8))
        enc = rencode.dumps(s500)
        self.assertTrue(enc.startswith(expected_prefix))
        self.assertEqual(rencode.loads(enc), s500)

    # ----------------------------------------------------------------------
    # Binary Data (bytes)
    # ----------------------------------------------------------------------
    def test_encode_decode_fixed_bytes(self):
        # Length 0 to 31 -> 0x80 + length
        self.assertEqual(rencode.dumps(b""), b"\x80")
        self.assertEqual(rencode.dumps(b"\x00"), b"\x81\x00")
        self.assertEqual(rencode.dumps(b"hello"), b"\x85hello")
        b31 = b"\xff" * 31
        self.assertEqual(rencode.dumps(b31), b"\x9f" + b31)

        res = rencode.loads(rencode.dumps(b"hello"))
        self.assertEqual(res, b"hello")
        self.assertIsInstance(res, bytes)

    def test_encode_decode_variable_bytes(self):
        # Length >= 32 -> 0xFA + LEB128 len + raw bytes
        b32 = b"\x01" * 32
        self.assertEqual(rencode.dumps(b32), b"\xfa\x20" + b32)
        self.assertEqual(rencode.loads(rencode.dumps(b32)), b32)

        b1000 = bytes(range(256)) * 4
        enc = rencode.dumps(b1000)
        expected_prefix = b"\xfa" + leb128_encode(len(b1000))
        self.assertTrue(enc.startswith(expected_prefix))
        self.assertEqual(rencode.loads(enc), b1000)

    # ----------------------------------------------------------------------
    # Strict Type Separation: str vs bytes
    # ----------------------------------------------------------------------
    def test_str_and_bytes_distinct(self):
        payload = {
            "text": "Unicode: 🚀",
            "binary": b"\x80\x81\xff\xfe\x00\x01",
        }
        decoded = rencode.loads(rencode.dumps(payload))
        self.assertIsInstance(decoded["text"], str)
        self.assertEqual(decoded["text"], "Unicode: 🚀")
        self.assertIsInstance(decoded["binary"], bytes)
        self.assertEqual(decoded["binary"], b"\x80\x81\xff\xfe\x00\x01")

    # ----------------------------------------------------------------------
    # Lists (list)
    # ----------------------------------------------------------------------
    def test_encode_decode_fixed_list(self):
        # Count 0 to 31 -> 0xA0 + count
        self.assertEqual(rencode.dumps([]), b"\xa0")
        self.assertEqual(rencode.dumps([1, 2]), b"\xa2\x01\x02")

        l31 = [1] * 31
        self.assertEqual(rencode.dumps(l31), b"\xbf" + b"\x01" * 31)

        res = rencode.loads(rencode.dumps([1, 2, 3]))
        self.assertEqual(res, [1, 2, 3])
        self.assertIsInstance(res, list)

    def test_encode_decode_variable_list(self):
        # Count >= 32 -> 0xFB + LEB128 count + elements
        l32 = [1] * 32
        enc = rencode.dumps(l32)
        self.assertEqual(enc[:2], b"\xfb\x20")
        self.assertEqual(rencode.loads(enc), l32)

        l100 = list(range(100))
        res = rencode.loads(rencode.dumps(l100))
        self.assertEqual(res, l100)
        self.assertIsInstance(res, list)

    # ----------------------------------------------------------------------
    # Tuples (tuple)
    # ----------------------------------------------------------------------
    def test_encode_decode_fixed_tuple(self):
        # Count 0 to 15 -> 0xE0 + count
        self.assertEqual(rencode.dumps(()), b"\xe0")
        self.assertEqual(rencode.dumps((1, 2)), b"\xe2\x01\x02")

        t15 = tuple([1] * 15)
        self.assertEqual(rencode.dumps(t15), b"\xef" + b"\x01" * 15)

        res = rencode.loads(rencode.dumps((1, 2, 3)))
        self.assertEqual(res, (1, 2, 3))
        self.assertIsInstance(res, tuple)

    def test_encode_decode_variable_tuple(self):
        # Count >= 16 -> 0xFD + LEB128 count + elements
        t16 = tuple([1] * 16)
        enc = rencode.dumps(t16)
        self.assertEqual(enc[:2], b"\xfd\x10")
        self.assertEqual(rencode.loads(enc), t16)

        t100 = tuple(range(100))
        res = rencode.loads(rencode.dumps(t100))
        self.assertEqual(res, t100)
        self.assertIsInstance(res, tuple)

    def test_list_vs_tuple_fidelity(self):
        orig_list = [1, 2, 3]
        orig_tuple = (1, 2, 3)

        dec_list = rencode.loads(rencode.dumps(orig_list))
        dec_tuple = rencode.loads(rencode.dumps(orig_tuple))

        self.assertEqual(dec_list, orig_list)
        self.assertIsInstance(dec_list, list)
        self.assertNotEqual(dec_list, orig_tuple)

        self.assertEqual(dec_tuple, orig_tuple)
        self.assertIsInstance(dec_tuple, tuple)

    # ----------------------------------------------------------------------
    # Dictionaries / Maps (dict)
    # ----------------------------------------------------------------------
    def test_encode_decode_fixed_dict(self):
        # Count 0 to 31 -> 0xC0 + count
        self.assertEqual(rencode.dumps({}), b"\xc0")

        d1 = {"a": 1}
        enc = rencode.dumps(d1)
        self.assertEqual(enc, b"\xc1\x61a\x01")
        self.assertEqual(rencode.loads(enc), d1)

        d31 = {str(i): i for i in range(31)}
        res = rencode.loads(rencode.dumps(d31))
        self.assertEqual(res, d31)
        self.assertIsInstance(res, dict)

    def test_encode_decode_variable_dict(self):
        # Count >= 32 -> 0xFC + LEB128 count + key/value pairs
        d32 = {str(i): i for i in range(32)}
        enc = rencode.dumps(d32)
        self.assertEqual(enc[:2], b"\xfc\x20")
        self.assertEqual(rencode.loads(enc), d32)

        d100 = {f"key_{i}": i * 10 for i in range(100)}
        res = rencode.loads(rencode.dumps(d100))
        self.assertEqual(res, d100)

    def test_dict_with_tuple_and_mixed_keys(self):
        # Tuples as dict keys
        d = {
            (1, 2): "coordinates",
            42: "answer",
            "flag": True,
        }
        res = rencode.loads(rencode.dumps(d))
        self.assertEqual(res, d)
        self.assertEqual(res[(1, 2)], "coordinates")

    # ----------------------------------------------------------------------
    # Extensions (EXT: 0xFF)
    # ----------------------------------------------------------------------
    def test_ext_structure(self):
        # Opcode 0xFF + LEB128 tag + LEB128 length + payload
        tag = 0x85
        payload = b"custom-payload-bytes"
        raw = b"\xff" + leb128_encode(tag) + leb128_encode(len(payload)) + payload

        # Loading extension without ext_hook returns Ext object
        res = rencode.loads(raw)
        self.assertIsInstance(res, rencode.Ext)
        self.assertEqual(res.tag, tag)
        self.assertEqual(res.data, payload)
        self.assertEqual(res, rencode.Ext(tag, payload))

    def test_ext_roundtrip(self):
        ext = rencode.Ext(0x99, b"\x01\x02\x03\x04")
        enc = rencode.dumps(ext)
        self.assertEqual(enc[0], 0xFF)
        self.assertEqual(rencode.loads(enc), ext)

        # In nested structure
        nested = {"ext": ext, "list": [1, ext]}
        self.assertEqual(rencode.loads(rencode.dumps(nested)), nested)

        # Ext equality and repr
        self.assertEqual(repr(ext), "Ext(tag=153, data=b'\\x01\\x02\\x03\\x04')")
        self.assertEqual(ext, rencode.Ext(0x99, bytearray(b"\x01\x02\x03\x04")))
        self.assertNotEqual(ext, rencode.Ext(0x98, b"\x01\x02\x03\x04"))
        self.assertNotEqual(ext, "not an ext")

        # Ext pickle support
        pickled = pickle.dumps(ext)
        unpickled = pickle.loads(pickled)
        self.assertEqual(unpickled, ext)
        self.assertEqual(unpickled.tag, ext.tag)
        self.assertEqual(unpickled.data, ext.data)

    def test_ext_validation(self):
        with self.assertRaises(TypeError):
            rencode.Ext("not_an_int", b"abc")
        with self.assertRaises(TypeError):
            rencode.Ext(True, b"abc")
        with self.assertRaises(ValueError):
            rencode.Ext(-1, b"abc")
        with self.assertRaises(ValueError):
            rencode.Ext(2**64, b"abc")
        with self.assertRaises(TypeError):
            rencode.Ext(1, "not_bytes")

    def test_ext_hook(self):
        # Custom type deserialization via ext_hook
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y

            def __eq__(self, other):
                return (
                    isinstance(other, Point) and self.x == other.x and self.y == other.y
                )

        def ext_decoder(tag, data):
            if tag == 0x10:
                x, y = struct.unpack("<ii", data)
                return Point(x, y)
            return rencode.Ext(tag, data)

        pt_data = struct.pack("<ii", 10, -20)
        ext = rencode.Ext(0x10, pt_data)
        enc = rencode.dumps(ext)

        decoded = rencode.loads(enc, ext_hook=ext_decoder)
        self.assertEqual(decoded, Point(10, -20))

    def test_dumps_default(self):
        import datetime

        dt = datetime.datetime(2026, 9, 12, 12, 0, 0)

        def default_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            if isinstance(obj, set):
                return sorted(list(obj))
            raise TypeError(f"Cannot serialize {type(obj)}")

        payload = {"time": dt, "set": {3, 1, 2}}
        enc = rencode.dumps(payload, default=default_serializer)
        dec = rencode.loads(enc)
        self.assertEqual(dec, {"time": dt.isoformat(), "set": [1, 2, 3]})

    def test_dumps_buffer_protocol(self):
        ba = bytearray(b"bytearray_test")
        enc_ba = rencode.dumps(ba)
        self.assertEqual(rencode.loads(enc_ba), b"bytearray_test")

        # Variable-length bytearray >= 32
        ba_large = bytearray(b"X" * 120)
        enc_ba_large = rencode.dumps(ba_large)
        self.assertEqual(rencode.loads(enc_ba_large), b"X" * 120)

        mv = memoryview(b"memoryview_test")
        enc_mv = rencode.dumps(mv)
        self.assertEqual(rencode.loads(enc_mv), b"memoryview_test")

    def test_int64_and_bigint_boundaries(self):
        vals = [
            0,
            63,
            64,
            127,
            128,
            32767,
            32768,
            2147483647,
            2147483648,
            9223372036854775807,
            9223372036854775808,
            -1,
            -32,
            -33,
            -128,
            -129,
            -32768,
            -32769,
            -2147483648,
            -2147483649,
            -9223372036854775808,
            -9223372036854775809,
            -(1 << 71),
            (1 << 71),
            -(1 << 127),
            (1 << 127),
        ]
        for v in vals:
            self.assertEqual(rencode.loads(rencode.dumps(v)), v)

    def test_argument_validation(self):
        # float_bits must be 32 or 64 upfront
        with self.assertRaises(ValueError):
            rencode.dumps("no floats here", float_bits=42)

        # max_depth must be > 0
        with self.assertRaises(ValueError):
            rencode.dumps(1, max_depth=0)
        with self.assertRaises(ValueError):
            rencode.dumps(1, max_depth=-5)
        with self.assertRaises(ValueError):
            rencode.loads(b"\x01", max_depth=0)
        with self.assertRaises(ValueError):
            rencode.loads(b"\x01", max_depth=-1)

    # ----------------------------------------------------------------------
    # Security, Validation & Error Handling
    # ----------------------------------------------------------------------
    def test_trailing_data_raises_value_error(self):
        # Trailing garbage must be rejected
        payload = rencode.dumps(42) + b"EXTRA_GARBAGE"
        with self.assertRaises(ValueError):
            rencode.loads(payload)

    def test_truncated_data_raises_error(self):
        # Incomplete buffer
        with self.assertRaises((ValueError, IndexError)):
            rencode.loads(b"\xf5\x00")  # int32 opcode with only 1 byte

        with self.assertRaises((ValueError, IndexError)):
            rencode.loads(b"\x65abc")  # fixed string length 5 with only 3 bytes

        with self.assertRaises((ValueError, IndexError)):
            rencode.loads(b"\xa2\x01")  # fixed list count 2 with only 1 element

    def test_invalid_utf8_in_string_raises(self):
        # Fixed string with invalid UTF-8 bytes
        bad_utf8 = b"\x62\xff\xfe"
        with self.assertRaises(UnicodeDecodeError):
            rencode.loads(bad_utf8)

    def test_recursion_depth_limit(self):
        # Nesting past 1000 levels must raise ValueError, NOT crash with SIGSEGV
        depth = 1500
        nested_payload = b"\xa1" * depth + b"\x00"
        with self.assertRaises(ValueError):
            rencode.loads(nested_payload)

    def test_encode_recursion_depth_limit(self):
        # Test circular references
        a = []
        a.append(a)
        with self.assertRaises(ValueError):
            rencode.dumps(a)

        # Test deeply nested list
        nested = 0
        for _ in range(1500):
            nested = [nested]
        with self.assertRaises(ValueError):
            rencode.dumps(nested)

    def test_configurable_max_depth(self):
        # Low max_depth
        payload = [1, [2, [3, 4]]]
        with self.assertRaises(ValueError):
            rencode.dumps(payload, max_depth=2)

        enc = rencode.dumps(payload)
        with self.assertRaises(ValueError):
            rencode.loads(enc, max_depth=2)

        # High max_depth
        depth = 1200
        nested = 0
        for _ in range(depth):
            nested = [nested]
        enc_deep = rencode.dumps(nested, max_depth=2000)
        dec_deep = rencode.loads(enc_deep, max_depth=2000)
        self.assertIsInstance(dec_deep, list)

    def test_loads_buffer_protocol(self):
        data = {"key": "value", "list": [1, 2, 3], "bytes": b"bin"}
        enc = rencode.dumps(data)

        # bytearray
        ba = bytearray(enc)
        self.assertEqual(rencode.loads(ba), data)

        # memoryview
        mv = memoryview(enc)
        self.assertEqual(rencode.loads(mv), data)

        # sliced memoryview
        padded = b"PRE" + enc + b"POST"
        mv_slice = memoryview(padded)[3 : 3 + len(enc)]
        self.assertEqual(rencode.loads(mv_slice), data)

    def test_subclasses_serialization(self):
        class Status(IntEnum):
            ACTIVE = 1
            PENDING = 2

        Point = collections.namedtuple("Point", ["x", "y"])

        od = collections.OrderedDict([("b", 2), ("a", 1)])
        enc_od = rencode.dumps(od)
        dec_od = rencode.loads(enc_od)
        self.assertEqual(dec_od, {"b": 2, "a": 1})

        enc_enum = rencode.dumps(Status.ACTIVE)
        self.assertEqual(rencode.loads(enc_enum), 1)

        enc_nt = rencode.dumps(Point(10, 20))
        self.assertEqual(rencode.loads(enc_nt), (10, 20))

    def test_overflow_and_bounds_validation(self):
        # Dict count overflowing size_t when multiplied by 2
        # LEB128 for 2**63 + 1: 0x81 0x80 ... 0x01
        large_leb128 = leb128_encode(2**63 + 1)
        bad_dict_payload = b"\xfc" + large_leb128 + b"\x00\x00"
        with self.assertRaises(ValueError):
            rencode.loads(bad_dict_payload)

        # List count exceeding remaining buffer size
        bad_list_payload = b"\xfb" + leb128_encode(1000) + b"\x00\x01"
        with self.assertRaises(ValueError):
            rencode.loads(bad_list_payload)

        # Tuple count exceeding remaining buffer size
        bad_tuple_payload = b"\xfd" + leb128_encode(1000) + b"\x00\x01"
        with self.assertRaises(ValueError):
            rencode.loads(bad_tuple_payload)

        # String length exceeding remaining buffer size
        bad_str_payload = b"\xf9" + leb128_encode(1000) + b"short"
        with self.assertRaises(ValueError):
            rencode.loads(bad_str_payload)

        # Bytes length exceeding remaining buffer size
        bad_bin_payload = b"\xfa" + leb128_encode(1000) + b"short"
        with self.assertRaises(ValueError):
            rencode.loads(bad_bin_payload)

        # BigInt length exceeding remaining buffer size
        bad_bigint_payload = b"\xfe" + leb128_encode(1000) + b"\x00"
        with self.assertRaises(ValueError):
            rencode.loads(bad_bigint_payload)

        # Extension byte length exceeding remaining buffer size
        bad_ext_payload = b"\xff" + leb128_encode(1) + leb128_encode(1000) + b"short"
        with self.assertRaises(ValueError):
            rencode.loads(bad_ext_payload)

    def test_leb128_overflow_protection(self):
        # 10-byte LEB128 with bits in byte 10 exceeding 1 bit (0x02 has bit 1 set)
        overflow_leb = b"\xf9" + (b"\x80" * 9) + b"\x02"
        with self.assertRaises(ValueError):
            rencode.loads(overflow_leb)

        # 11-byte LEB128 (continuation bit set on 10th byte)
        overflow_leb_11 = b"\xf9" + (b"\x80" * 10) + b"\x01"
        with self.assertRaises(ValueError):
            rencode.loads(overflow_leb_11)

    def test_dump_and_load_streams(self):
        data = {"score": 99.5, "tags": ["fast", "compact"]}
        bio = io.BytesIO()
        rencode.dump(data, bio)
        bio.seek(0)
        loaded = rencode.load(bio)
        self.assertEqual(loaded, data)


if __name__ == "__main__":
    unittest.main()
