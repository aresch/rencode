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
    def test_fixed_pos_int(self):
        self.assertEqual(rencode.dumps(1), rencode_orig.dumps(1))
        self.assertEqual(rencode.dumps(40), rencode_orig.dumps(40))

    def test_fixed_neg_int(self):
        self.assertEqual(rencode.dumps(-10), rencode_orig.dumps(-10))
        self.assertEqual(rencode.dumps(-29), rencode_orig.dumps(-29))

    def test_int_char_size(self):
        self.assertEqual(rencode.dumps(100), rencode_orig.dumps(100))
        self.assertEqual(rencode.dumps(-100), rencode_orig.dumps(-100))

    def test_int_short_size(self):
        self.assertEqual(rencode.dumps(27123), rencode_orig.dumps(27123))

    def test_int_int_size(self):
        self.assertEqual(rencode.dumps(7483648), rencode_orig.dumps(7483648))
        self.assertEqual(rencode.dumps(-7483648), rencode_orig.dumps(-7483648))

    def test_int_long_long_size(self):
        self.assertEqual(rencode.dumps(8223372036854775808), rencode_orig.dumps(8223372036854775808))
        self.assertEqual(rencode.dumps(-8223372036854775808), rencode_orig.dumps(-8223372036854775808))

    def test_int_big_number(self):
        n = int("9"*62)
        self.assertEqual(rencode.dumps(n), rencode_orig.dumps(n))
        self.assertRaises(ValueError, rencode.dumps, int("9"*65))

    def test_float_32bit(self):
        self.assertEqual(rencode.dumps(1234.56), rencode_orig.dumps(1234.56))

    def test_float_64bit(self):
        self.assertEqual(rencode.dumps(1234.56, 64), rencode_orig.dumps(1234.56, 64))

    def test_float_invalid_size(self):
        self.assertRaises(ValueError, rencode.dumps, 1234.56, 36)

    def test_fixed_str(self):
        self.assertEqual(rencode.dumps("foobarbaz"), rencode_orig.dumps("foobarbaz"))

    def test_str(self):
        self.assertEqual(rencode.dumps("f"*255), rencode_orig.dumps("f"*255))

    def test_unicode(self):
        self.assertEqual(rencode.dumps(u"foobar"), rencode_orig.dumps(u"foobar"))

    def test_none(self):
        self.assertEqual(rencode.dumps(None), rencode_orig.dumps(None))

    def test_fixed_list(self):
        l = [100, -234.01, "foobar", u"baz"]*4
        self.assertEqual(rencode.dumps(l), rencode_orig.dumps(l))

    def test_list(self):
        l = [100, -234.01, "foobar", u"baz"]*80
        self.assertEqual(rencode.dumps(l), rencode_orig.dumps(l))

    def test_fixed_dict(self):
        s = "abcdefghijk"
        d = dict(zip(s, [1234]*len(s)))
        self.assertEqual(rencode.dumps(d), rencode_orig.dumps(d))
if __name__ == '__main__':
    unittest.main()
