#
# rencode.pyx
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

cdef extern from "string.h":
    void *memcpy(void*, void*, size_t)
cdef extern from "stdlib.h":
    void *realloc(void*, size_t)

# Determine host byte-order
cdef bool big_endian = False
cdef unsigned long number = 1
cdef char *s = <char *>&number
if s[0] == 0:
    big_endian = True

cdef enum:
    # Default number of bits for serialized floats, either 32 or 64 (also a parameter for dumps()).
    DEFAULT_FLOAT_BITS = 32
    # Maximum length of integer when written as base 10 string.
    MAX_INT_LENGTH = 64
    # The bencode 'typecodes' such as i, d, etc have been extended and
    # relocated on the base-256 character set.
    CHR_LIST    = 59
    CHR_DICT    = 60
    CHR_INT     = 61
    CHR_INT1    = 62
    CHR_INT2    = 63
    CHR_INT4    = 64
    CHR_INT8    = 65
    CHR_FLOAT32 = 66
    CHR_FLOAT64 = 44
    CHR_TRUE    = 67
    CHR_FALSE   = 68
    CHR_NONE    = 69
    CHR_TERM    = 127
    # Positive integers with value embedded in typecode.
    INT_POS_FIXED_START = 0
    INT_POS_FIXED_COUNT = 44
    # Dictionaries with length embedded in typecode.
    DICT_FIXED_START = 102
    DICT_FIXED_COUNT = 25
    # Negative integers with value embedded in typecode.
    INT_NEG_FIXED_START = 70
    INT_NEG_FIXED_COUNT = 32
    # Strings with length embedded in typecode.
    STR_FIXED_START = 128
    STR_FIXED_COUNT = 64
    # Lists with length embedded in typecode.
    LIST_FIXED_START = STR_FIXED_START+STR_FIXED_COUNT
    LIST_FIXED_COUNT = 64

cdef char _float_bits

cdef swap_byte_order_short(short *s):
    s[0] = (s[0] >> 8) | (s[0] << 8)

cdef swap_byte_order_uint(int *i):
    i[0] = (i[0] >> 24) | ((i[0] << 8) & 0x00FF0000) | ((i[0] >> 8) & 0x0000FF00) | (i[0] << 24)

cdef swap_byte_order_int(char *c):
    cdef int i
    cdef char *p = <char *>&i
    p[0] = c[3]
    p[1] = c[2]
    p[2] = c[1]
    p[3] = c[0]
    return i

cdef swap_byte_order_ulong_long(long long *l):
    l[0] = (l[0] >> 56) | \
           ((l[0] << 40) & 0x00FF000000000000) | \
           ((l[0] << 24) & 0x0000FF0000000000) | \
           ((l[0] << 8) & 0x000000FF00000000) | \
           ((l[0] >> 8) & 0x00000000FF000000) | \
           ((l[0] >> 24) & 0x0000000000FF0000) | \
           ((l[0] >> 40) & 0x000000000000FF00) | \
           (l[0] << 56)

cdef swap_byte_order_long_long(char *c):
    cdef long long l
    cdef char *p = <char *>&l
    p[0] = c[7]
    p[1] = c[6]
    p[2] = c[5]
    p[3] = c[4]
    p[4] = c[3]
    p[5] = c[2]
    p[6] = c[1]
    p[7] = c[0]
    return l

cdef swap_byte_order_float(char *c):
    cdef float f
    cdef char *p = <char *>&f
    p[0] = c[3]
    p[1] = c[2]
    p[2] = c[1]
    p[3] = c[0]
    return f

cdef swap_byte_order_double(char *c):
    cdef double d
    cdef char *p = <char *>&d
    p[0] = c[7]
    p[1] = c[6]
    p[2] = c[5]
    p[3] = c[4]
    p[4] = c[3]
    p[5] = c[2]
    p[6] = c[1]
    p[7] = c[0]
    return d

cdef write_buffer_char(char **buf, int *pos, char c):
    buf[0] = <char*>realloc(buf[0], pos[0] + 1)
    memcpy(&buf[0][pos[0]], &c, 1)
    pos[0] += 1

cdef write_buffer(char **buf, int *pos, void* data, int size):
    buf[0] = <char*>realloc(buf[0], pos[0] + size)
    memcpy(&buf[0][pos[0]], data, size)
    pos[0] += size

cdef encode_char(char **buf, int *pos, signed char x):
    if 0 <= x < INT_POS_FIXED_COUNT:
        write_buffer_char(buf, pos, INT_POS_FIXED_START + x)
    elif -INT_NEG_FIXED_COUNT <= x < 0:
        write_buffer_char(buf, pos, INT_NEG_FIXED_START - 1 - x)
    elif -128 <= x < 128:
        write_buffer_char(buf, pos, CHR_INT1)
        write_buffer_char(buf, pos, x)

cdef encode_short(char **buf, int *pos, short x):
    write_buffer_char(buf, pos, CHR_INT2)
    if not big_endian:
        swap_byte_order_short(&x)
    write_buffer(buf, pos, &x, sizeof(x))

cdef encode_int(char **buf, int *pos, int x):
    write_buffer_char(buf, pos, CHR_INT4)
    if not big_endian:
        if x > 0:
            swap_byte_order_uint(&x)
        else:
            x = swap_byte_order_int(<char*>&x)
    write_buffer(buf, pos, &x, sizeof(x))

cdef encode_long_long(char **buf, int *pos, long long x):
    write_buffer_char(buf, pos, CHR_INT8)
    if not big_endian:
        if x > 0:
            swap_byte_order_ulong_long(&x)
        else:
            x = swap_byte_order_long_long(<char*>&x)
    write_buffer(buf, pos, &x, sizeof(x))

cdef encode_big_number(char **buf, int *pos, char *x):
    write_buffer_char(buf, pos, CHR_INT)
    write_buffer(buf, pos, x, len(x))
    write_buffer_char(buf, pos, CHR_TERM)

cdef encode_float32(char **buf, int *pos, float x):
    write_buffer_char(buf, pos, CHR_FLOAT32)
    if not big_endian:
        x = swap_byte_order_float(<char *>&x)
    write_buffer(buf, pos, &x, sizeof(x))

cdef encode_float64(char **buf, int *pos, double x):
    write_buffer_char(buf, pos, CHR_FLOAT64)
    if not big_endian:
        x = swap_byte_order_double(<char *>&x)
    write_buffer(buf, pos, &x, sizeof(x))

cdef encode_str(char **buf, int *pos, char* x):
    cdef char *p
    if len(x) < STR_FIXED_COUNT:
        write_buffer_char(buf, pos, STR_FIXED_START + len(x))
        write_buffer(buf, pos, x, len(x))
    else:
        s = str(len(x)) + ":"
        p = s
        write_buffer(buf, pos, p, len(s))
        write_buffer(buf, pos, x, len(x))

cdef encode_none(char **buf, int *pos):
    write_buffer_char(buf, pos, CHR_NONE)

cdef encode_list(char **buf, int *pos, x):
    if len(x) < LIST_FIXED_COUNT:
        write_buffer_char(buf, pos, LIST_FIXED_START + len(x))
        for i in x:
            encode(buf, pos, i)
    else:
        write_buffer_char(buf, pos, CHR_LIST)
        for i in x:
            encode(buf, pos, i)
        write_buffer_char(buf, pos, CHR_TERM)

cdef encode_dict(char **buf, int *pos, x):
    if len(x) < DICT_FIXED_COUNT:
        write_buffer_char(buf, pos, DICT_FIXED_START + len(x))
        for k, v in x.iteritems():
            encode(buf, pos, k)
            encode(buf, pos, v)
    else:
        write_buffer_char(buf, pos, CHR_DICT)
        for k, v in x.iteritems():
            encode(buf, pos, k)
            encode(buf, pos, v)
        write_buffer_char(buf, pos, CHR_TERM)

from types import StringType, IntType, LongType, DictType, ListType, TupleType, FloatType, NoneType, UnicodeType

cdef encode(char **buf, int *pos, data):
    t = type(data)
    if t == IntType or t == LongType:
        if -128 <= data < 128:
            encode_char(buf, pos, data)
        elif -32768 <= data < 32768:
            encode_short(buf, pos, data)
        elif -2147483648 <= data < 2147483648:
            encode_int(buf, pos, data)
        elif -9223372036854775808 <= data < 9223372036854775808:
            encode_long_long(buf, pos, data)
        else:
            s = str(data)
            if len(s) >= MAX_INT_LENGTH:
                raise ValueError("Number is longer than %d characters" % MAX_INT_LENGTH)
            encode_big_number(buf, pos, s)
    elif t == FloatType:
        if _float_bits == 32:
            encode_float32(buf, pos, data)
        elif _float_bits == 64:
            encode_float64(buf, pos, data)
        else:
            raise ValueError('Float bits (%d) is not 32 or 64' % _float_bits)

    elif t == StringType:
        encode_str(buf, pos, data)

    elif t == UnicodeType:
        u = data.encode("utf8")
        encode_str(buf, pos, u)

    elif t == NoneType:
        encode_none(buf, pos)

    elif t == ListType or t == TupleType:
        encode_list(buf, pos, data)

    elif t == DictType:
        encode_dict(buf, pos, data)


def dumps(data, float_bits=DEFAULT_FLOAT_BITS):
    """
    Encode the object data into a string.

    :param data: the object to encode
    :type data: object

    """
    global _float_bits
    _float_bits = float_bits
    cdef char *buf = NULL
    cdef int pos = 0
    encode(&buf, &pos, data)
    return buf[:pos]
