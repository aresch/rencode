# -*- coding: utf-8 -*-
#
# test_rencode.py
#
# Copyright (C) 2010 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#

import unittest
import rencode
import rencode_orig

class TestRencode(unittest.TestCase):
    def test_encode_fixed_pos_int(self):
        self.assertEqual(rencode.dumps(1), rencode_orig.dumps(1))
        self.assertEqual(rencode.dumps(40), rencode_orig.dumps(40))

    def test_encode_fixed_neg_int(self):
        self.assertEqual(rencode.dumps(-10), rencode_orig.dumps(-10))
        self.assertEqual(rencode.dumps(-29), rencode_orig.dumps(-29))

    def test_encode_int_char_size(self):
        self.assertEqual(rencode.dumps(100), rencode_orig.dumps(100))
        self.assertEqual(rencode.dumps(-100), rencode_orig.dumps(-100))

    def test_encode_int_short_size(self):
        self.assertEqual(rencode.dumps(27123), rencode_orig.dumps(27123))
        self.assertEqual(rencode.dumps(-27123), rencode_orig.dumps(-27123))

    def test_encode_int_int_size(self):
        self.assertEqual(rencode.dumps(7483648), rencode_orig.dumps(7483648))
        self.assertEqual(rencode.dumps(-7483648), rencode_orig.dumps(-7483648))

    def test_encode_int_long_long_size(self):
        self.assertEqual(rencode.dumps(8223372036854775808), rencode_orig.dumps(8223372036854775808))
        self.assertEqual(rencode.dumps(-8223372036854775808), rencode_orig.dumps(-8223372036854775808))

    def test_encode_int_big_number(self):
        n = int("9"*62)
        self.assertEqual(rencode.dumps(n), rencode_orig.dumps(n))
        self.assertRaises(ValueError, rencode.dumps, int("9"*65))

    def test_encode_float_32bit(self):
        self.assertEqual(rencode.dumps(1234.56), rencode_orig.dumps(1234.56))

    def test_encode_float_64bit(self):
        self.assertEqual(rencode.dumps(1234.56, 64), rencode_orig.dumps(1234.56, 64))

    def test_encode_float_invalid_size(self):
        self.assertRaises(ValueError, rencode.dumps, 1234.56, 36)

    def test_encode_fixed_str(self):
        self.assertEqual(rencode.dumps("foobarbaz"), rencode_orig.dumps("foobarbaz"))

    def test_encode_str(self):
        self.assertEqual(rencode.dumps("f"*255), rencode_orig.dumps("f"*255))

    def test_encode_unicode(self):
        self.assertEqual(rencode.dumps(u"fööbar"), rencode_orig.dumps(u"fööbar"))

    def test_encode_none(self):
        self.assertEqual(rencode.dumps(None), rencode_orig.dumps(None))

    def test_encode_bool(self):
        self.assertEqual(rencode.dumps(True), rencode_orig.dumps(True))
        self.assertEqual(rencode.dumps(False), rencode_orig.dumps(False))

    def test_encode_fixed_list(self):
        l = [100, -234.01, "foobar", u"bäz"]*4
        self.assertEqual(rencode.dumps(l), rencode_orig.dumps(l))

    def test_encode_list(self):
        l = [100, -234.01, "foobar", u"bäz"]*80
        self.assertEqual(rencode.dumps(l), rencode_orig.dumps(l))

    def test_encode_fixed_dict(self):
        s = "abcdefghijk"
        d = dict(zip(s, [1234]*len(s)))
        self.assertEqual(rencode.dumps(d), rencode_orig.dumps(d))

    def test_encode_dict(self):
        s = "abcdefghijklmnopqrstuvwxyz1234567890"
        d = dict(zip(s, [1234]*len(s)))
        self.assertEqual(rencode.dumps(d), rencode_orig.dumps(d))

    def test_decode_fixed_pos_int(self):
        self.assertEqual(rencode.loads(rencode.dumps(10)), 10)

    def test_decode_fixed_neg_int(self):
        self.assertEqual(rencode.loads(rencode.dumps(-10)), -10)

    def test_decode_char(self):
        self.assertEqual(rencode.loads(rencode.dumps(100)), 100)
        self.assertEqual(rencode.loads(rencode.dumps(-100)), -100)

    def test_decode_short(self):
        self.assertEqual(rencode.loads(rencode.dumps(27123)), 27123)
        self.assertEqual(rencode.loads(rencode.dumps(-27123)), -27123)

    def test_decode_int(self):
        self.assertEqual(rencode.loads(rencode.dumps(7483648)), 7483648)
        self.assertEqual(rencode.loads(rencode.dumps(-7483648)), -7483648)

    def test_decode_long_long(self):
        self.assertEqual(rencode.loads(rencode.dumps(8223372036854775808)), 8223372036854775808)
        self.assertEqual(rencode.loads(rencode.dumps(-8223372036854775808)), -8223372036854775808)

    def test_decode_int_big_number(self):
        n = int("9"*62)
        self.assertEqual(rencode.loads(rencode.dumps(n)), n)

    def test_decode_float_32bit(self):
        f = rencode.dumps(1234.56)
        self.assertEqual(rencode.loads(f), rencode_orig.loads(f))

    def test_decode_float_64bit(self):
        f = rencode.dumps(1234.56, 64)
        self.assertEqual(rencode.loads(f), rencode_orig.loads(f))

    def test_decode_fixed_str(self):
        self.assertEqual(rencode.loads(rencode.dumps("foobarbaz")), "foobarbaz")

    def test_decode_str(self):
        self.assertEqual(rencode.loads(rencode.dumps("f"*255)), "f"*255)

    def test_decode_unicode(self):
        self.assertEqual(rencode.loads(rencode.dumps(u"fööbar")), u"fööbar")

    def test_decode_none(self):
        self.assertEqual(rencode.loads(rencode.dumps(None)), None)

    def test_decode_bool(self):
        self.assertEqual(rencode.loads(rencode.dumps(True)), True)
        self.assertEqual(rencode.loads(rencode.dumps(False)), False)

    def test_decode_fixed_list(self):
        l = [100, False, "foobar", u"bäz"]*4
        self.assertEqual(rencode.loads(rencode.dumps(l)), tuple(l))

    def test_decode_list(self):
        l = [100, False, "foobar", u"bäz"]*80
        self.assertEqual(rencode.loads(rencode.dumps(l)), tuple(l))

    def test_decode_fixed_dict(self):
        s = "abcdefghijk"
        d = dict(zip(s, [1234]*len(s)))
        self.assertEqual(rencode.loads(rencode.dumps(d)), d)

    def test_decode_dict(self):
        s = "abcdefghijklmnopqrstuvwxyz1234567890"
        d = dict(zip(s, ["foo"*120]*len(s)))
        d2 = {"foo": d, "bar": d, "baz": d}
        self.assertEqual(rencode.loads(rencode.dumps(d2)), d2)

if __name__ == '__main__':
    unittest.main()
