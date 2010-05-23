import rencode
import rencode_orig


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

def test_encode_unicode():
    rencode.dumps(u"foobar")

def test_encode_unicode_orig():
    rencode_orig.dumps(u"foobar")

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
d2 = dict(zip(keys, [None]*len(keys)))

def test_encode_dict():
    rencode.dumps(d2)

def test_encode_dict_orig():
    rencode_orig.dumps(d2)


overall = [
    "5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6",
    "fixedlength",
    u"unicodestring",
    u"5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6",
    -10,
    10,
    120,
    15600,
    7483648,
    8223372036854775808,
    int("9"*62),
    1227688834.643409,
    None
]

def test_overall():
    rencode.dumps(overall)

def test_overall_orig():
    rencode_orig.dumps(overall)


if __name__ == "__main__":
    import timeit

    iterations = 10000
    # ANSI escape codes
    CSI="\x1B["
    reset=CSI+"m"

    def do_test(func):
        print "%s:" % func
        new_time = timeit.Timer("%s()" % func, "from __main__ import %s" % func).timeit(iterations)
        orig_time = timeit.Timer("%s_orig()" % func, "from __main__ import %s_orig" % func).timeit(iterations)
        if new_time > orig_time:
            new = CSI + "31m%.3fs%s (+%.3fs)" % (new_time, reset, new_time-orig_time)
            orig = CSI + "32m%.3fs%s" % (orig_time, reset)
        else:
            new = CSI + "32m%.3fs%s (%s34m+%.3fs%s) %.2f%%" % (new_time, reset, CSI, orig_time-new_time, reset, (orig_time/new_time)*100)
            orig = CSI + "31m%.3fs%s" % (orig_time, reset)

        print "\trencode.pyx: %s" % new
        print "\trencode.py:  %s" % orig
        print ""
        return (new_time, orig_time)

    loc = locals().keys()

    print "Encoding functions:"
    print "*" * 79
    print ""

    total_new = 0.0
    total_orig = 0.0
    for func in loc:
        if func.startswith("test_encode_") and not func.endswith("_orig"):
            n, o = do_test(func)
            total_new += n
            total_orig += o

    print "Encoding functions totals:"
    if total_new > total_orig:
        pass
    else:
        new = "%s32m%.3fs%s (%s34m+%.3fs%s) %.2f%%" % (CSI, total_new, reset, CSI, total_orig-total_new, reset, (total_orig/total_new)*100)
        orig = CSI + "31m%.3fs%s" % (total_orig, reset)

    print "\trencode.pyx: %s" % new
    print "\trencode.py:  %s" % orig
