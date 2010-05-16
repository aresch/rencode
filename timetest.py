import rencode
import rencode_orig

d = [
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

def timetest1():
    rencode_orig.dumps(d)

def timetest2():
    rencode.dumps(d)

if __name__ == "__main__":
    import timeit
    print timeit.Timer("timetest1()", "from __main__ import timetest1").timeit(100000)
    print timeit.Timer("timetest2()", "from __main__ import timetest2").timeit(100000)
