# -*- coding: utf-8 -*-
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
# along with rencode.    If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#

import sys

import unittest
from rencode import _rencode as rencode


class TestRencode(unittest.TestCase):
    def test_encode_fixed_pos_int(self):
        self.assertEqual(rencode.dumps(1), b'\x01')
        self.assertEqual(rencode.dumps(40), b'\x28')

    def test_encode_fixed_neg_int(self):
        self.assertEqual(rencode.dumps(-10), b'O')
        self.assertEqual(rencode.dumps(-29), b'b')

    def test_encode_int_char_size(self):
        self.assertEqual(rencode.dumps(100), b'\x3e\x64')
        self.assertEqual(rencode.dumps(-100), b'>\x9c')

    def test_encode_int_short_size(self):
        self.assertEqual(rencode.dumps(27123), b'\x3f\x69\xf3')
        self.assertEqual(rencode.dumps(-27123), b'?\x96\r')

    def test_encode_int_int_size(self):
        self.assertEqual(rencode.dumps(7483648), b'@\x00r1\x00')
        self.assertEqual(rencode.dumps(-7483648), b'@\xff\x8d\xcf\x00')

    def test_encode_int_long_long_size(self):
        self.assertEqual(
            rencode.dumps(8223372036854775808), b'Ar\x1fILX\x9c\x00\x00'
        )
        self.assertEqual(
            rencode.dumps(-8223372036854775808),
            b'A\x8d\xe0\xb6\xb3\xa7d\x00\x00',
        )

    def test_encode_int_big_number(self):
        n = int("9" * 62)
        self.assertEqual(rencode.dumps(n), b'=' + str(n).encode() + b'\x7f')
        self.assertRaises(ValueError, rencode.dumps, int("9" * 65))

    def test_encode_float_32bit(self):
        self.assertEqual(rencode.dumps(1234.56), b'BD\x9aQ\xec')

    def test_encode_float_64bit(self):
        self.assertEqual(rencode.dumps(1234.56, 64), b',@\x93J=p\xa3\xd7\n')

    def test_encode_float_invalid_size(self):
        self.assertRaises(ValueError, rencode.dumps, 1234.56, 36)

    def test_encode_fixed_str(self):
        self.assertEqual(rencode.dumps(b"foobarbaz"), b'\x89foobarbaz')

    def test_encode_bytes(self):
        self.assertEqual(rencode.dumps(b"f" * 255), b'255:' + b'f' * 255)
        self.assertEqual(rencode.dumps(b"\0"), b'\x81\x00')

    def test_encode_str(self):
        self.assertEqual(rencode.dumps("fööbar"), b'\x88' + "fööbar".encode('utf-8'))

    def test_encode_none(self):
        self.assertEqual(rencode.dumps(None), b'E')

    def test_encode_bool(self):
        self.assertEqual(rencode.dumps(True), b'C')
        self.assertEqual(rencode.dumps(False), b'D')

    def test_encode_fixed_list(self):
        l = [100, -234.01, b"foobar", "bäz"] * 4
        self.assertEqual(rencode.dumps(l), b'\xd0' + b''.join([
            b'\x3e\x64',  # 100
            b'B\xc3j\x02\x8f',  # -234.01
            b'\x86foobar',  # "foobar"
            b'\x84' + "bäz".encode('utf-8')  # "bäz"
        ]) * 4)

    def test_encode_list(self):
        l = [100, -234.01, b"foobar", "bäz"] * 80
        self.assertEqual(rencode.dumps(l), b';' + b''.join([
            b'\x3e\x64',  # 100
            b'B\xc3j\x02\x8f',  # -234.01
            b'\x86foobar',  # "foobar"
            b'\x84' + "bäz".encode('utf-8')  # "bäz"
        ]) * 80 + b'\x7f')

    def test_encode_fixed_dict(self):
        s = b"abcdefghijk"
        d = dict(zip(s, [1234] * len(s)))
        self.assertEqual(rencode.dumps(d), b'q' + b''.join(
            b'>' + bytes([i]) + b'?\x04\xd2' for i in range(ord('a'), ord('k') + 1)
        ))

    def test_encode_dict(self):
        s = b"abcdefghijklmnopqrstuvwxyz1234567890"
        d = dict(zip(s, [1234] * len(s)))
        self.assertEqual(rencode.dumps(d), b'<' + b''.join(
            b'>' + bytes([i]) + b'?\x04\xd2' for i in range(ord('a'), ord('z') + 1)
        ) + b''.join(
            b'>' + bytes([i]) + b'?\x04\xd2' for i in range(ord('1'), ord('9') + 1)
        ) + b'>0?\x04\xd2' + b'\x7f')

    def test_decode_fixed_pos_int(self):
        self.assertEqual(rencode.loads(rencode.dumps(10)), 10)

    def test_decode_fixed_neg_int(self):
        self.assertEqual(rencode.loads(rencode.dumps(-10)), -10)

    def test_decode_char(self):
        self.assertEqual(rencode.loads(rencode.dumps(100)), 100)
        self.assertEqual(rencode.loads(rencode.dumps(-100)), -100)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([62])))

    def test_decode_short(self):
        self.assertEqual(rencode.loads(rencode.dumps(27123)), 27123)
        self.assertEqual(rencode.loads(rencode.dumps(-27123)), -27123)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([63])))

    def test_decode_int(self):
        self.assertEqual(rencode.loads(rencode.dumps(7483648)), 7483648)
        self.assertEqual(rencode.loads(rencode.dumps(-7483648)), -7483648)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([64])))

    def test_decode_long_long(self):
        self.assertEqual(
            rencode.loads(rencode.dumps(8223372036854775808)), 8223372036854775808
        )
        self.assertEqual(
            rencode.loads(rencode.dumps(-8223372036854775808)), -8223372036854775808
        )
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([65])))

    def test_decode_int_big_number(self):
        n = int(b"9" * 62)
        toobig = "={x}\x7f".format(x="9" * 65).encode()
        self.assertEqual(rencode.loads(rencode.dumps(n)), n)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([61])))
        self.assertRaises(ValueError, rencode.loads, toobig)

    def test_decode_float_32bit(self):
        f = rencode.dumps(1234.5)
        self.assertEqual(rencode.loads(f), 1234.5)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([66])))

    def test_decode_float_64bit(self):
        f = rencode.dumps(1234.5, 64)
        self.assertEqual(rencode.loads(f), 1234.5)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([44])))

    def test_decode_fixed_bytes(self):
        self.assertEqual(rencode.loads(rencode.dumps(b"foobarbaz")), b"foobarbaz")
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([130])))

    def test_decode_bytes(self):
        self.assertEqual(rencode.loads(rencode.dumps(b"f" * 255)), b"f" * 255)
        self.assertRaises(IndexError, rencode.loads, b"50")

    def test_decode_str(self):
        self.assertEqual(
            rencode.loads(rencode.dumps("fööbar")), "fööbar".encode("utf8")
        )

    def test_decode_none(self):
        self.assertEqual(rencode.loads(rencode.dumps(None)), None)

    def test_decode_bool(self):
        self.assertEqual(rencode.loads(rencode.dumps(True)), True)
        self.assertEqual(rencode.loads(rencode.dumps(False)), False)

    def test_decode_fixed_list(self):
        l = [100, False, b"foobar", "bäz".encode("utf8")] * 4
        self.assertEqual(rencode.loads(rencode.dumps(l)), tuple(l))
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([194])))

    def test_decode_list(self):
        l = [100, False, b"foobar", "bäz".encode("utf8")] * 80
        self.assertEqual(rencode.loads(rencode.dumps(l)), tuple(l))
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([59])))

    def test_decode_fixed_dict(self):
        s = b"abcdefghijk"
        d = dict(zip(s, [1234] * len(s)))
        self.assertEqual(rencode.loads(rencode.dumps(d)), d)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([104])))

    def test_decode_dict(self):
        s = b"abcdefghijklmnopqrstuvwxyz1234567890"
        d = dict(zip(s, [b"foo" * 120] * len(s)))
        d2 = {b"foo": d, b"bar": d, b"baz": d}
        self.assertEqual(rencode.loads(rencode.dumps(d2)), d2)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([60])))

    def test_decode_str_bytes(self):
        b = [202, 132, 100, 114, 97, 119, 1, 0, 0, 63, 1, 242, 63]
        d = bytes(bytearray(b))
        self.assertEqual(rencode.loads(rencode.dumps(d)), d)

    def test_decode_str_nullbytes(self):
        b = (
            202,
            132,
            100,
            114,
            97,
            119,
            1,
            0,
            0,
            63,
            1,
            242,
            63,
            1,
            60,
            132,
            120,
            50,
            54,
            52,
            49,
            51,
            48,
            58,
            0,
            0,
            0,
            1,
            65,
            154,
            35,
            215,
            48,
            204,
            4,
            35,
            242,
            3,
            122,
            218,
            67,
            192,
            127,
            40,
            241,
            127,
            2,
            86,
            240,
            63,
            135,
            177,
            23,
            119,
            63,
            31,
            226,
            248,
            19,
            13,
            192,
            111,
            74,
            126,
            2,
            15,
            240,
            31,
            239,
            48,
            85,
            238,
            159,
            155,
            197,
            241,
            23,
            119,
            63,
            2,
            23,
            245,
            63,
            24,
            240,
            86,
            36,
            176,
            15,
            187,
            185,
            248,
            242,
            255,
            0,
            126,
            123,
            141,
            206,
            60,
            188,
            1,
            27,
            254,
            141,
            169,
            132,
            93,
            220,
            252,
            121,
            184,
            8,
            31,
            224,
            63,
            244,
            226,
            75,
            224,
            119,
            135,
            229,
            248,
            3,
            243,
            248,
            220,
            227,
            203,
            193,
            3,
            224,
            127,
            47,
            134,
            59,
            5,
            99,
            249,
            254,
            35,
            196,
            127,
            17,
            252,
            71,
            136,
            254,
            35,
            196,
            112,
            4,
            177,
            3,
            63,
            5,
            220,
        )
        d = bytes(bytearray(b))
        self.assertEqual(rencode.loads(rencode.dumps(d)), d)

    def test_decode_utf8(self):
        s = b"foobarbaz"
        d = rencode.loads(rencode.dumps(s), decode_utf8=True)
        self.assertIsInstance(d, str)
        s = rencode.dumps(b"\x56\xe4foo\xc3")
        self.assertRaises(UnicodeDecodeError, rencode.loads, s, decode_utf8=True)

    def test_version_exposed(self):
        self.assertEqual(
            rencode.__version__[1:],
            ("Cython", 1, 0, 8)[1:],
        )

    def test_invalid_typecode(self):
        s = b";\x2f\x7f"
        self.assertRaises(ValueError, rencode.loads, s)


if __name__ == "__main__":
    unittest.main()
