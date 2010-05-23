# -*- coding: utf-8 -*-
#
# timetest.py
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

import rencode
import rencode_orig

# Encode functions

def test_encode_fixed_pos_int():
    rencode.dumps(40)

def test_encode_fixed_pos_int_orig():
    rencode_orig.dumps(40)

def test_encode_fixed_neg_int():
    rencode.dumps(-29)

def test_encode_fixed_neg_int_orig():
    rencode_orig.dumps(-29)

def test_encode_int_char_size():
    rencode.dumps(100)
    rencode.dumps(-100)

def test_encode_int_char_size_orig():
    rencode_orig.dumps(100)
    rencode_orig.dumps(-100)

def test_encode_int_short_size():
    rencode.dumps(27123)
    rencode.dumps(-27123)

def test_encode_int_short_size_orig():
    rencode_orig.dumps(27123)
    rencode_orig.dumps(-27123)

def test_encode_int_int_size():
    rencode.dumps(7483648)
    rencode.dumps(-7483648)

def test_encode_int_int_size_orig():
    rencode_orig.dumps(7483648)
    rencode_orig.dumps(-7483648)

def test_encode_int_long_long_size():
    rencode.dumps(8223372036854775808)
    rencode.dumps(-8223372036854775808)

def test_encode_int_long_long_size_orig():
    rencode_orig.dumps(8223372036854775808)
    rencode_orig.dumps(-8223372036854775808)

bn = int("9"*62)
def test_encode_int_big_number():
    rencode.dumps(bn)

def test_encode_int_big_number_orig():
    rencode_orig.dumps(bn)

def test_encode_float_32bit():
    rencode.dumps(1234.56)

def test_encode_float_32bit_orig():
    rencode_orig.dumps(1234.56)

def test_encode_float_64bit():
    rencode.dumps(1234.56, 64)

def test_encode_float_64bit_orig():
    rencode_orig.dumps(1234.56, 64)

def test_encode_fixed_str():
    rencode.dumps("foobarbaz")

def test_encode_fixed_str_orig():
    rencode_orig.dumps("foobarbaz")

s = "f"*255
def test_encode_str():
    rencode.dumps(s)

def test_encode_str_orig():
    rencode_orig.dumps(s)

def test_encode_none():
    rencode.dumps(None)

def test_encode_none_orig():
    rencode_orig.dumps(None)

def test_encode_bool():
    rencode.dumps(True)

def test_encode_bool_orig():
    rencode_orig.dumps(True)

l = [None, None, None, None]
def test_encode_fixed_list():
    rencode.dumps(l)

def test_encode_fixed_list_orig():
    rencode_orig.dumps(l)

ll = [None]*80
def test_encode_list():
    rencode.dumps(ll)

def test_encode_list_orig():
    rencode_orig.dumps(ll)

keys = "abcdefghijk"
d = dict(zip(keys, [None]*len(keys)))

def test_encode_fixed_dict():
    rencode.dumps(d)

def test_encode_fixed_dict_orig():
    rencode_orig.dumps(d)

keys2 = "abcdefghijklmnopqrstuvwxyz1234567890"
d2 = dict(zip(keys2, [None]*len(keys2)))

def test_encode_dict():
    rencode.dumps(d2)

def test_encode_dict_orig():
    rencode_orig.dumps(d2)


# Decode functions

def test_decode_fixed_pos_int():
    rencode.loads('(')

def test_decode_fixed_pos_int_orig():
    rencode_orig.loads('(')

def test_decode_fixed_neg_int():
    rencode.loads('b')

def test_decode_fixed_neg_int_orig():
    rencode_orig.loads('b')

def test_decode_int_char_size():
    rencode.loads('>d')
    rencode.loads('>\x9c')

def test_decode_int_char_size_orig():
    rencode_orig.loads('>d')
    rencode_orig.loads('>\x9c')

def test_decode_int_short_size():
    rencode.loads('?i\xf3')
    rencode.loads('?\x96\r')

def test_decode_int_short_size_orig():
    rencode_orig.loads('?i\xf3')
    rencode_orig.loads('?\x96\r')

def test_decode_int_int_size():
    rencode.loads('@\x00r1\x00')
    rencode.loads('@\xff\x8d\xcf\x00')

def test_decode_int_int_size_orig():
    rencode_orig.loads('@\x00r1\x00')
    rencode_orig.loads('@\xff\x8d\xcf\x00')

def test_decode_int_long_long_size():
    rencode.loads('Ar\x1fILX\x9c\x00\x00')
    rencode.loads('A\x8d\xe0\xb6\xb3\xa7d\x00\x00')

def test_decode_int_long_long_size_orig():
    rencode_orig.loads('Ar\x1fILX\x9c\x00\x00')
    rencode_orig.loads('A\x8d\xe0\xb6\xb3\xa7d\x00\x00')

def test_decode_int_big_number():
    rencode.loads('=99999999999999999999999999999999999999999999999999999999999999\x7f')

def test_decode_int_big_number_orig():
    rencode_orig.loads('=99999999999999999999999999999999999999999999999999999999999999\x7f')

def test_decode_float_32bit():
    rencode.loads('BD\x9aQ\xec')

def test_decode_float_32bit_orig():
    rencode_orig.loads('BD\x9aQ\xec')

def test_decode_float_64bit():
    rencode.loads(',@\x93J=p\xa3\xd7\n')

def test_decode_float_64bit_orig():
    rencode_orig.loads(',@\x93J=p\xa3\xd7\n')

def test_decode_fixed_str():
    rencode.loads('\x89foobarbaz')

def test_decode_fixed_str_orig():
    rencode_orig.loads('\x89foobarbaz')

s = "f"*255
def test_decode_str():
    rencode.loads('255:fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')

def test_decode_str_orig():
    rencode_orig.loads('255:fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')

def test_decode_none():
    rencode.loads('E')

def test_decode_none_orig():
    rencode_orig.loads('E')

def test_decode_bool():
    rencode.loads('C')

def test_decode_bool_orig():
    rencode_orig.loads('C')

def test_decode_fixed_list():
    rencode.loads('\xc4EEEE')

def test_decode_fixed_list_orig():
    rencode_orig.loads('\xc4EEEE')

def test_decode_list():
    rencode.loads(';EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\x7f')

def test_decode_list_orig():
    rencode_orig.loads(';EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\x7f')

def test_decode_fixed_dict():
    rencode.loads('q\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE')

def test_decode_fixed_dict_orig():
    rencode_orig.loads('q\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE')

def test_decode_dict():
    rencode.loads('<\x811E\x810E\x813E\x812E\x815E\x814E\x817E\x816E\x819E\x818E\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE\x81mE\x81lE\x81oE\x81nE\x81qE\x81pE\x81sE\x81rE\x81uE\x81tE\x81wE\x81vE\x81yE\x81xE\x81zE\x7f')

def test_decode_dict_orig():
    rencode_orig.loads('<\x811E\x810E\x813E\x812E\x815E\x814E\x817E\x816E\x819E\x818E\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE\x81mE\x81lE\x81oE\x81nE\x81qE\x81pE\x81sE\x81rE\x81uE\x81tE\x81wE\x81vE\x81yE\x81xE\x81zE\x7f')


overall = [
    "5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6",
    "fixedlength",
    u"unicodestring",
    u"5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6",
    -10,
    10,
    120,
    15600,
    -15600,
    7483648,
    -7483648,
    8223372036854775808,
    -8223372036854775808,
    int("9"*62),
    1227688834.643409,
    None,
    True
]

def test_overall_encode():
    rencode.dumps(overall)

def test_overall_encode_orig():
    rencode_orig.dumps(overall)

def test_overall_decode():
    rencode.loads('\xd180:5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6\x8bfixedlength\x8dunicodestring80:5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6O\n>x?<\xf0?\xc3\x10@\x00r1\x00@\xff\x8d\xcf\x00Ar\x1fILX\x9c\x00\x00A\x8d\xe0\xb6\xb3\xa7d\x00\x00=99999999999999999999999999999999999999999999999999999999999999\x7fBN\x92Z\x17EC')

def test_overall_decode_orig():
    rencode_orig.loads('\xd180:5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6\x8bfixedlength\x8dunicodestring80:5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6O\n>x?<\xf0?\xc3\x10@\x00r1\x00@\xff\x8d\xcf\x00Ar\x1fILX\x9c\x00\x00A\x8d\xe0\xb6\xb3\xa7d\x00\x00=99999999999999999999999999999999999999999999999999999999999999\x7fBN\x92Z\x17EC')


if __name__ == "__main__":
    import timeit
    import sys

    iterations = 10000
    # ANSI escape codes
    CSI="\x1B["
    reset=CSI+"m"

    def do_test(func):
        print "%s:" % func
        new_time = timeit.Timer("%s()" % func, "from __main__ import %s" % func).timeit(iterations)
        orig_time = timeit.Timer("%s_orig()" % func, "from __main__ import %s_orig" % func).timeit(iterations)
        if new_time > orig_time:
            new = CSI + "31m%.3fs%s" % (new_time, reset)
            orig = CSI + "32m%.3fs%s (%s34m+%.3fs%s) %.2f%%" % (orig_time, reset, CSI, new_time-orig_time, reset, (new_time/orig_time)*100)
        else:
            new = CSI + "32m%.3fs%s (%s34m+%.3fs%s) %.2f%%" % (new_time, reset, CSI, orig_time-new_time, reset, (orig_time/new_time)*100)
            orig = CSI + "31m%.3fs%s" % (orig_time, reset)

        print "\trencode.pyx: %s" % new
        print "\trencode.py:  %s" % orig
        print ""
        return (new_time, orig_time)

    if len(sys.argv) == 1:
        loc = locals().keys()

        for t in ("encode", "decode", "overall"):
            print "*" * 79
            print "%s functions:" % (t.title())
            print "*" * 79
            print ""

            total_new = 0.0
            total_orig = 0.0
            for func in loc:
                if func.startswith("test_%s" % t) and not func.endswith("_orig"):
                    n, o = do_test(func)
                    total_new += n
                    total_orig += o

            print "%sing functions totals:" % (t[:-1].title())
            if total_new > total_orig:
                new = CSI + "31m%.3fs%s" % (total_new, reset)
                orig = "%s32m%.3fs%s (%s34m+%.3fs%s) %.2f%%" % (CSI, total_orig, reset, CSI, total_new-total_orig, reset, (total_new/total_orig)*100)
            else:
                new = "%s32m%.3fs%s (%s34m+%.3fs%s) %.2f%%" % (CSI, total_new, reset, CSI, total_orig-total_new, reset, (total_orig/total_new)*100)
                orig = CSI + "31m%.3fs%s" % (total_orig, reset)

            print "\trencode.pyx: %s" % new
            print "\trencode.py:  %s" % orig
            print ""
    else:
        for f in sys.argv[1:]:
            do_test(f)
