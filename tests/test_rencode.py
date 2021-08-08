# -*- coding: utf-8 -*-
#
# test_rencode.py
#
# Copyright (C) 2010 Andrew Resch <andrewresch@gmail.com>
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
from rencode import rencode_orig


class TestRencode(unittest.TestCase):

    def _cmp(self, *values):
        for v in values:
            self.assertEqual(rencode.dumps(v), rencode_orig.dumps(v))

    def _reload(self, *values):
        for v in values:
            self.assertEqual(rencode.loads(rencode.dumps(v)), v)


    def test_encode_fixed_pos_int(self):
        self._cmp(1, 40)

    def test_encode_fixed_neg_int(self):
        self._cmp(-10, -29)

    def test_encode_int_char_size(self):
        self._cmp(100, -100)

    def test_encode_int_short_size(self):
        self._cmp(27123, -27123)

    def test_encode_int_int_size(self):
        self._cmp(7483648, -7483648)

    def test_encode_int_long_long_size(self):
        self._cmp(8223372036854775808, -8223372036854775808)

    def test_encode_int_big_number(self):
        n = int("9"*62)
        self._cmp(n)
        self.assertRaises(ValueError, rencode.dumps, int("9"*65))

    def test_encode_float_32bit(self):
        self._cmp(1234.56)

    def test_encode_float_64bit(self):
        self.assertEqual(rencode.dumps(1234.56, 64), rencode_orig.dumps(1234.56, 64))

    def test_encode_float_invalid_size(self):
        self.assertRaises(ValueError, rencode.dumps, 1234.56, 36)

    def test_encode_fixed_str(self):
        self._cmp(b"foobarbaz")

    def test_encode_str(self):
        self._cmp(b"f"*255, b"\0")

    def test_encode_unicode(self):
        self._cmp(u"fööbar")

    def test_encode_none(self):
        self._cmp(None)

    def test_encode_bool(self):
        self._cmp(True, False)

    def test_encode_fixed_list(self):
        l = [100, -234.01, b"foobar", u"bäz"]*4
        self._cmp(l)

    def test_encode_list(self):
        l = [100, -234.01, b"foobar", u"bäz"]*80
        self._cmp(l)

    def test_encode_fixed_dict(self):
        s = b"abcdefghijk"
        d = dict(zip(s, [1234]*len(s)))
        self._cmp(d)

    def test_encode_dict(self):
        s = b"abcdefghijklmnopqrstuvwxyz1234567890"
        d = dict(zip(s, [1234]*len(s)))
        self._cmp(d)


    def test_decode_fixed_pos_int(self):
        self._reload(10)

    def test_decode_fixed_neg_int(self):
        self._reload(-10)

    def test_decode_char(self):
        self._reload(100, -100, bytes(bytearray([62])))

    def test_decode_short(self):
        self._reload(27123, -27123, bytes(bytearray([63])))

    def test_decode_int(self):
        self._reload(7483648, -7483648, bytes(bytearray([64])))

    def test_decode_long_long(self):
        self._reload(8223372036854775808, -8223372036854775808, bytes([65]))

    def test_decode_int_big_number(self):
        n = int(b"9"*62)
        toobig = '={x}\x7f'.format(x='9'*65).encode()
        self._reload(n)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([61])))
        self.assertRaises(ValueError, rencode.loads, toobig)

    def test_decode_float_32bit(self):
        f = rencode.dumps(1234.56)
        self.assertEqual(rencode.loads(f), rencode_orig.loads(f))
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([66])))

    def test_decode_float_64bit(self):
        f = rencode.dumps(1234.56, 64)
        self.assertEqual(rencode.loads(f), rencode_orig.loads(f))
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([44])))

    def test_decode_fixed_str(self):
        self._reload(b"foobarbaz")
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([130])))

    def test_decode_str(self):
        self._reload(b"f"*255)
        self.assertRaises(IndexError, rencode.loads, b"50")

    def test_decode_unicode(self):
        self.assertEqual(rencode.loads(rencode.dumps(u"fööbar")), "fööbar".encode("utf8"))

    def test_decode_none(self):
        self._reload(None)

    def test_decode_bool(self):
        self._reload(True, False)

    def test_decode_fixed_list(self):
        l = [100, False, b"foobar", u"bäz".encode("utf8")]*4
        self.assertEqual(rencode.loads(rencode.dumps(l)), tuple(l))
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([194])))

    def test_decode_list(self):
        l = [100, False, b"foobar", u"bäz".encode("utf8")]*80
        self.assertEqual(rencode.loads(rencode.dumps(l)), tuple(l))
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([59])))

    def test_decode_fixed_dict(self):
        s = b"abcdefghijk"
        d = dict(zip(s, [1234]*len(s)))
        self._reload(d)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([104])))

    def test_decode_dict(self):
        s = b"abcdefghijklmnopqrstuvwxyz1234567890"
        d = dict(zip(s, [b"foo"*120]*len(s)))
        d2 = {b"foo": d, b"bar": d, b"baz": d}
        self._reload(d2)
        self.assertRaises(IndexError, rencode.loads, bytes(bytearray([60])))

    def test_decode_str_bytes(self):
        b = [202, 132, 100, 114, 97, 119, 1, 0, 0, 63, 1, 242, 63]
        d = bytes(bytearray(b))
        self._reload(d)

    def test_decode_str_nullbytes(self):
        b = (202, 132, 100, 114, 97, 119, 1, 0, 0, 63, 1, 242, 63, 1, 60, 132, 120, 50, 54, 52, 49, 51, 48, 58, 0, 0, 0, 1, 65, 154, 35, 215, 48, 204, 4, 35, 242, 3, 122, 218, 67, 192, 127, 40, 241, 127, 2, 86, 240, 63, 135, 177, 23, 119, 63, 31, 226, 248, 19, 13, 192, 111, 74, 126, 2, 15, 240, 31, 239, 48, 85, 238, 159, 155, 197, 241, 23, 119, 63, 2, 23, 245, 63, 24, 240, 86, 36, 176, 15, 187, 185, 248, 242, 255, 0, 126, 123, 141, 206, 60, 188, 1, 27, 254, 141, 169, 132, 93, 220, 252, 121, 184, 8, 31, 224, 63, 244, 226, 75, 224, 119, 135, 229, 248, 3, 243, 248, 220, 227, 203, 193, 3, 224, 127, 47, 134, 59, 5, 99, 249, 254, 35, 196, 127, 17, 252, 71, 136, 254, 35, 196, 112, 4, 177, 3, 63, 5, 220)
        d = bytes(bytearray(b))
        self._reload(d)

    def test_decode_utf8(self):
        s = b"foobarbaz"
        #no assertIsInstance with python2.6
        d = rencode.loads(rencode.dumps(s), decode_utf8=True)
        if not isinstance(d, str):
            self.fail('%s is not an instance of %r' % (repr(d), unicode))
        s = rencode.dumps(b"\x56\xe4foo\xc3")
        self.assertRaises(UnicodeDecodeError, rencode.loads, s, decode_utf8=True)

    def test_version_exposed(self):
        assert rencode.__version__
        assert rencode_orig.__version__
        self.assertEqual(rencode.__version__[1:], rencode_orig.__version__[1:], "version number does not match")

    def test_invalidtypecode(self):
        s = b';\x2f\x7f'
        try:
            rencode.loads(s)
        except Exception:
            pass
        else:
            raise Exception("invalid typecode should raise an Exception")

if __name__ == '__main__':
    unittest.main()
