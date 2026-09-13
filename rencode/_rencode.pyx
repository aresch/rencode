# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
#
# _rencode.pyx
#
# Copyright (C) 2026 Andrew Resch <andrewresch@gmail.com>
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

from cpython.ref cimport PyObject, Py_INCREF
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AS_STRING, PyBytes_GET_SIZE, PyBytes_Check
from cpython.bytearray cimport PyByteArray_Check, PyByteArray_AS_STRING, PyByteArray_GET_SIZE
from cpython.unicode cimport PyUnicode_DecodeUTF8, PyUnicode_AsUTF8AndSize
from cpython.list cimport PyList_New, PyList_SET_ITEM, PyList_GET_ITEM
from cpython.tuple cimport PyTuple_New, PyTuple_SET_ITEM, PyTuple_GET_ITEM
from cpython.dict cimport PyDict_New, PyDict_SetItem, PyDict_Next
from cpython.buffer cimport PyObject_GetBuffer, PyBuffer_Release, Py_buffer, PyBUF_SIMPLE

cdef extern from "Python.h":
    object _PyDict_NewPresized(Py_ssize_t minused)
    long long PyLong_AsLongLongAndOverflow(object pylong, int *overflow)
    void PyErr_Clear()
    object _PyLong_FromByteArray(const unsigned char* bytes, size_t n, int little_endian, int is_signed)

from libc.stdlib cimport malloc, realloc, free
from libc.string cimport memcpy
from libc.stdint cimport int8_t, int16_t, int32_t, int64_t, uint8_t, uint16_t, uint32_t, uint64_t

cdef class Ext:
    """
    Container for Rencode v2 Extension type (opcode 0xFF).
    """
    cdef public uint64_t tag
    cdef public bytes data

    def __init__(self, object tag, object data):
        if not isinstance(tag, int) or isinstance(tag, bool):
            raise TypeError("Extension tag must be an integer")
        if tag < 0:
            raise ValueError("Extension tag must be non-negative")
        if tag > 18446744073709551615:
            raise ValueError("Extension tag exceeds 64-bit bounds")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("Extension data must be bytes-like")
        self.tag = <uint64_t>tag
        self.data = bytes(data) if not isinstance(data, bytes) else data

    def __repr__(self):
        return f"Ext(tag={self.tag}, data={self.data!r})"

    def __eq__(self, object other):
        if isinstance(other, Ext):
            return self.tag == (<Ext>other).tag and self.data == (<Ext>other).data
        return False

    def __hash__(self):
        return hash((self.tag, self.data))

    def __reduce__(self):
        return (Ext, (self.tag, self.data))


__version__ = ("Cython", 2, 0, 0)
__all__ = ("dumps", "loads", "Ext")

# Opcode definitions for Rencode v2
cdef enum:
    DEFAULT_FLOAT_BITS = 64
    MAX_RECURSION_DEPTH = 1000
    STACK_BUF_SIZE = 512

    # Fixed ranges
    OP_POS_INT_START  = 0x00   # 0x00 - 0x3F (0 to 63)
    OP_POS_INT_COUNT  = 64
    OP_NEG_INT_START  = 0x40   # 0x40 - 0x5F (-1 to -32)
    OP_NEG_INT_COUNT  = 32
    OP_STR_FIXED_START= 0x60   # 0x60 - 0x7F (length 0 to 31)
    OP_STR_FIXED_COUNT= 32
    OP_BIN_FIXED_START= 0x80   # 0x80 - 0x9F (length 0 to 31)
    OP_BIN_FIXED_COUNT= 32
    OP_LIST_FIXED_START = 0xA0 # 0xA0 - 0xBF (count 0 to 31)
    OP_LIST_FIXED_COUNT = 32
    OP_DICT_FIXED_START = 0xC0 # 0xC0 - 0xDF (count 0 to 31)
    OP_DICT_FIXED_COUNT = 32
    OP_TUPLE_FIXED_START= 0xE0 # 0xE0 - 0xEF (count 0 to 15)
    OP_TUPLE_FIXED_COUNT= 16

    # Scalar and variable opcodes
    OP_NONE    = 0xF0
    OP_FALSE   = 0xF1
    OP_TRUE    = 0xF2
    OP_INT8    = 0xF3
    OP_INT16   = 0xF4
    OP_INT32   = 0xF5
    OP_INT64   = 0xF6
    OP_FLOAT32 = 0xF7
    OP_FLOAT64 = 0xF8
    OP_STR_V   = 0xF9
    OP_BIN_V   = 0xFA
    OP_LIST_V  = 0xFB
    OP_DICT_V  = 0xFC
    OP_TUPLE_V = 0xFD
    OP_BIGINT  = 0xFE
    OP_EXT     = 0xFF

# Endianness detection
cdef extern from *:
    """
    #if defined(__BYTE_ORDER__) && __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
    #define RENCODE_BIG_ENDIAN 1
    #else
    #define RENCODE_BIG_ENDIAN 0
    #endif

    #if defined(_MSC_VER)
    #include <stdlib.h>
    #define bswap_16(x) _byteswap_ushort(x)
    #define bswap_32(x) _byteswap_ulong(x)
    #define bswap_64(x) _byteswap_uint64(x)
    #elif defined(__GNUC__) || defined(__clang__)
    #define bswap_16(x) __builtin_bswap16(x)
    #define bswap_32(x) __builtin_bswap32(x)
    #define bswap_64(x) __builtin_bswap64(x)
    #endif
    """
    int RENCODE_BIG_ENDIAN
    uint16_t bswap_16(uint16_t)
    uint32_t bswap_32(uint32_t)
    uint64_t bswap_64(uint64_t)


cdef struct Buffer:
    char *data
    size_t pos
    size_t capacity
    char stack_buf[STACK_BUF_SIZE]

cdef inline int buf_init(Buffer *buf) except -1:
    buf.pos = 0
    buf.capacity = STACK_BUF_SIZE
    buf.data = buf.stack_buf
    return 0

cdef inline int buf_ensure(Buffer *buf, size_t need) except -1:
    cdef size_t new_cap
    cdef char *new_data
    if need > (<size_t>-1) - buf.pos - 1024:
        raise MemoryError("Buffer size overflow")
    if buf.pos + need > buf.capacity:
        new_cap = buf.capacity * 2
        if new_cap < buf.pos + need:
            new_cap = buf.pos + need + 1024
        if buf.data == buf.stack_buf:
            new_data = <char*>malloc(new_cap)
            if new_data == NULL:
                raise MemoryError(f"Failed to allocate {new_cap} bytes")
            memcpy(new_data, buf.stack_buf, buf.pos)
            buf.data = new_data
        else:
            new_data = <char*>realloc(buf.data, new_cap)
            if new_data == NULL:
                raise MemoryError(f"Failed to expand buffer to {new_cap} bytes")
            buf.data = new_data
        buf.capacity = new_cap
    return 0

cdef inline int buf_write_byte(Buffer *buf, uint8_t b) except -1:
    buf_ensure(buf, 1)
    buf.data[buf.pos] = <char>b
    buf.pos += 1
    return 0

cdef inline int buf_write_bytes(Buffer *buf, const void *src, size_t n) except -1:
    if n > 0:
        buf_ensure(buf, n)
        memcpy(&buf.data[buf.pos], src, n)
        buf.pos += n
    return 0

cdef inline int buf_write_leb128(Buffer *buf, uint64_t val) except -1:
    buf_ensure(buf, 10)
    cdef uint8_t byte
    while True:
        byte = <uint8_t>(val & 0x7F)
        val >>= 7
        if val != 0:
            buf.data[buf.pos] = <char>(byte | 0x80)
            buf.pos += 1
        else:
            buf.data[buf.pos] = <char>byte
            buf.pos += 1
            break
    return 0

cdef inline int buf_write_int8_entry(Buffer *buf, int8_t val) except -1:
    buf_ensure(buf, 2)
    buf.data[buf.pos] = <char>OP_INT8
    buf.data[buf.pos + 1] = <char>val
    buf.pos += 2
    return 0

cdef inline int buf_write_int16_entry(Buffer *buf, int16_t val) except -1:
    buf_ensure(buf, 3)
    buf.data[buf.pos] = <char>OP_INT16
    cdef uint16_t v = <uint16_t>val
    if RENCODE_BIG_ENDIAN:
        v = bswap_16(v)
    memcpy(&buf.data[buf.pos + 1], &v, 2)
    buf.pos += 3
    return 0

cdef inline int buf_write_int32_entry(Buffer *buf, int32_t val) except -1:
    buf_ensure(buf, 5)
    buf.data[buf.pos] = <char>OP_INT32
    cdef uint32_t v = <uint32_t>val
    if RENCODE_BIG_ENDIAN:
        v = bswap_32(v)
    memcpy(&buf.data[buf.pos + 1], &v, 4)
    buf.pos += 5
    return 0

cdef inline int buf_write_int64_entry(Buffer *buf, int64_t val) except -1:
    buf_ensure(buf, 9)
    buf.data[buf.pos] = <char>OP_INT64
    cdef uint64_t v = <uint64_t>val
    if RENCODE_BIG_ENDIAN:
        v = bswap_64(v)
    memcpy(&buf.data[buf.pos + 1], &v, 8)
    buf.pos += 9
    return 0

cdef inline int buf_write_float32_entry(Buffer *buf, float val) except -1:
    buf_ensure(buf, 5)
    buf.data[buf.pos] = <char>OP_FLOAT32
    cdef uint32_t v = 0
    memcpy(&v, &val, 4)
    if RENCODE_BIG_ENDIAN:
        v = bswap_32(v)
    memcpy(&buf.data[buf.pos + 1], &v, 4)
    buf.pos += 5
    return 0

cdef inline int buf_write_float64_entry(Buffer *buf, double val) except -1:
    buf_ensure(buf, 9)
    buf.data[buf.pos] = <char>OP_FLOAT64
    cdef uint64_t v = 0
    memcpy(&v, &val, 8)
    if RENCODE_BIG_ENDIAN:
        v = bswap_64(v)
    memcpy(&buf.data[buf.pos + 1], &v, 8)
    buf.pos += 9
    return 0


cdef inline int _encode_int(Buffer *buf, object data) except -1:
    cdef int overflow = 0
    cdef long long val = PyLong_AsLongLongAndOverflow(data, &overflow)
    cdef size_t byte_len
    cdef object raw
    if overflow == 0:
        if 0 <= val <= 63:
            buf_write_byte(buf, OP_POS_INT_START + <uint8_t>val)
        elif -32 <= val <= -1:
            buf_write_byte(buf, OP_NEG_INT_START + <uint8_t>(-val - 1))
        elif -128 <= val <= 127:
            buf_write_int8_entry(buf, <int8_t>val)
        elif -32768 <= val <= 32767:
            buf_write_int16_entry(buf, <int16_t>val)
        elif -2147483648 <= val <= 2147483647:
            buf_write_int32_entry(buf, <int32_t>val)
        else:
            buf_write_int64_entry(buf, <int64_t>val)
    else:
        # Big integer
        byte_len = ((data + 1).bit_length() + 8) // 8 if data < 0 else (data.bit_length() + 8) // 8
        raw = data.to_bytes(byte_len, byteorder="little", signed=True)
        buf_write_byte(buf, OP_BIGINT)
        buf_write_leb128(buf, len(raw))
        buf_write_bytes(buf, PyBytes_AS_STRING(raw), len(raw))
    return 0

cdef inline int _encode_float(Buffer *buf, double data, int float_bits) except -1:
    if float_bits == 64:
        buf_write_float64_entry(buf, data)
    elif float_bits == 32:
        buf_write_float32_entry(buf, <float>data)
    else:
        raise ValueError(f"Float bits ({float_bits}) is not 32 or 64")
    return 0

cdef inline int _encode_str(Buffer *buf, object data) except -1:
    cdef Py_ssize_t slen = 0
    cdef const char *str_data = PyUnicode_AsUTF8AndSize(data, &slen)
    if slen < OP_STR_FIXED_COUNT:
        buf_ensure(buf, 1 + slen)
        buf.data[buf.pos] = <char>(OP_STR_FIXED_START + <uint8_t>slen)
        if slen > 0:
            memcpy(&buf.data[buf.pos + 1], str_data, slen)
        buf.pos += 1 + slen
    else:
        buf_write_byte(buf, OP_STR_V)
        buf_write_leb128(buf, <uint64_t>slen)
        buf_write_bytes(buf, str_data, slen)
    return 0

cdef inline int _encode_bytes(Buffer *buf, object data) except -1:
    cdef Py_ssize_t slen = PyBytes_GET_SIZE(data)
    if slen < OP_BIN_FIXED_COUNT:
        buf_ensure(buf, 1 + slen)
        buf.data[buf.pos] = <char>(OP_BIN_FIXED_START + <uint8_t>slen)
        if slen > 0:
            memcpy(&buf.data[buf.pos + 1], PyBytes_AS_STRING(data), slen)
        buf.pos += 1 + slen
    else:
        buf_write_byte(buf, OP_BIN_V)
        buf_write_leb128(buf, <uint64_t>slen)
        buf_write_bytes(buf, PyBytes_AS_STRING(data), slen)
    return 0

cdef inline int _encode_bytearray(Buffer *buf, object data) except -1:
    cdef Py_ssize_t slen = PyByteArray_GET_SIZE(data)
    if slen < OP_BIN_FIXED_COUNT:
        buf_ensure(buf, 1 + slen)
        buf.data[buf.pos] = <char>(OP_BIN_FIXED_START + <uint8_t>slen)
        if slen > 0:
            memcpy(&buf.data[buf.pos + 1], PyByteArray_AS_STRING(data), slen)
        buf.pos += 1 + slen
    else:
        buf_write_byte(buf, OP_BIN_V)
        buf_write_leb128(buf, <uint64_t>slen)
        buf_write_bytes(buf, PyByteArray_AS_STRING(data), slen)
    return 0

cdef inline int _encode_buffer(Buffer *buf, object data) except -1:
    cdef Py_buffer view
    if PyObject_GetBuffer(data, &view, PyBUF_SIMPLE) != 0:
        PyErr_Clear()
        return -2  # Not a buffer object
    try:
        if view.len < OP_BIN_FIXED_COUNT:
            buf_ensure(buf, 1 + view.len)
            buf.data[buf.pos] = <char>(OP_BIN_FIXED_START + <uint8_t>view.len)
            if view.len > 0:
                memcpy(&buf.data[buf.pos + 1], view.buf, view.len)
            buf.pos += 1 + view.len
        else:
            buf_write_byte(buf, OP_BIN_V)
            buf_write_leb128(buf, <uint64_t>view.len)
            buf_write_bytes(buf, view.buf, view.len)
    finally:
        PyBuffer_Release(&view)
    return 0

cdef inline int _encode_ext(Buffer *buf, Ext ext_obj) except -1:
    cdef uint64_t tag = ext_obj.tag
    cdef bytes data_obj = ext_obj.data
    cdef Py_ssize_t slen = PyBytes_GET_SIZE(data_obj)
    buf_write_byte(buf, OP_EXT)
    buf_write_leb128(buf, tag)
    buf_write_leb128(buf, <uint64_t>slen)
    buf_write_bytes(buf, PyBytes_AS_STRING(data_obj), slen)
    return 0

cdef int encode_obj(Buffer *buf, object data, int float_bits, int depth, int max_depth, object default_fn) except -1:
    if depth > max_depth:
        raise ValueError("Recursion limit exceeded while serializing")

    cdef size_t count, i
    cdef Py_ssize_t dict_pos = 0
    cdef PyObject *pk = NULL
    cdef PyObject *pv = NULL
    cdef list l_data
    cdef tuple t_data

    if data is None:
        buf_write_byte(buf, OP_NONE)
    elif data is False:
        buf_write_byte(buf, OP_FALSE)
    elif data is True:
        buf_write_byte(buf, OP_TRUE)
    elif type(data) is int:
        _encode_int(buf, data)
    elif type(data) is float:
        _encode_float(buf, <double>data, float_bits)
    elif type(data) is str:
        _encode_str(buf, data)
    elif type(data) is bytes:
        _encode_bytes(buf, data)
    elif type(data) is bytearray:
        _encode_bytearray(buf, data)
    elif type(data) is Ext:
        _encode_ext(buf, <Ext>data)
    elif type(data) is list:
        count = len(data)
        if count < OP_LIST_FIXED_COUNT:
            buf_write_byte(buf, OP_LIST_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_LIST_V)
            buf_write_leb128(buf, <uint64_t>count)
        l_data = <list>data
        for i in range(count):
            encode_obj(buf, <object>PyList_GET_ITEM(l_data, i), float_bits, depth + 1, max_depth, default_fn)
    elif type(data) is tuple:
        count = len(data)
        if count < OP_TUPLE_FIXED_COUNT:
            buf_write_byte(buf, OP_TUPLE_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_TUPLE_V)
            buf_write_leb128(buf, <uint64_t>count)
        t_data = <tuple>data
        for i in range(count):
            encode_obj(buf, <object>PyTuple_GET_ITEM(t_data, i), float_bits, depth + 1, max_depth, default_fn)
    elif type(data) is dict:
        count = len(data)
        if count < OP_DICT_FIXED_COUNT:
            buf_write_byte(buf, OP_DICT_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_DICT_V)
            buf_write_leb128(buf, <uint64_t>count)
        dict_pos = 0
        while PyDict_Next(data, &dict_pos, &pk, &pv):
            encode_obj(buf, <object>pk, float_bits, depth + 1, max_depth, default_fn)
            encode_obj(buf, <object>pv, float_bits, depth + 1, max_depth, default_fn)
    elif isinstance(data, bool):
        buf_write_byte(buf, OP_TRUE if data else OP_FALSE)
    elif isinstance(data, int):
        _encode_int(buf, data)
    elif isinstance(data, float):
        _encode_float(buf, <double>data, float_bits)
    elif isinstance(data, str):
        _encode_str(buf, data)
    elif isinstance(data, bytes):
        _encode_bytes(buf, data)
    elif isinstance(data, bytearray):
        _encode_bytearray(buf, data)
    elif isinstance(data, list):
        count = len(data)
        if count < OP_LIST_FIXED_COUNT:
            buf_write_byte(buf, OP_LIST_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_LIST_V)
            buf_write_leb128(buf, <uint64_t>count)
        for item in data:
            encode_obj(buf, item, float_bits, depth + 1, max_depth, default_fn)
    elif isinstance(data, tuple):
        count = len(data)
        if count < OP_TUPLE_FIXED_COUNT:
            buf_write_byte(buf, OP_TUPLE_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_TUPLE_V)
            buf_write_leb128(buf, <uint64_t>count)
        for item in data:
            encode_obj(buf, item, float_bits, depth + 1, max_depth, default_fn)
    elif isinstance(data, dict):
        count = len(data)
        if count < OP_DICT_FIXED_COUNT:
            buf_write_byte(buf, OP_DICT_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_DICT_V)
            buf_write_leb128(buf, <uint64_t>count)
        dict_pos = 0
        while PyDict_Next(data, &dict_pos, &pk, &pv):
            encode_obj(buf, <object>pk, float_bits, depth + 1, max_depth, default_fn)
            encode_obj(buf, <object>pv, float_bits, depth + 1, max_depth, default_fn)
    elif isinstance(data, memoryview):
        _encode_buffer(buf, data)
    elif isinstance(data, Ext):
        _encode_ext(buf, <Ext>data)
    elif default_fn is not None:
        encode_obj(buf, default_fn(data), float_bits, depth + 1, max_depth, default_fn)
    elif _encode_buffer(buf, data) == 0:
        return 0
    else:
        raise TypeError(f"type {type(data)} not handled")

    return 0


def dumps(data, float_bits=DEFAULT_FLOAT_BITS, int max_depth=MAX_RECURSION_DEPTH, default=None):
    """
    Encode Python object data into rencode v2 binary format.

    :param data: The object to serialize
    :param float_bits: Floating point precision (32 or 64, default 64)
    :param max_depth: Maximum recursion depth allowed (default 1000)
    :param default: Optional function called for objects that cannot otherwise be serialized
    :return: Serialized bytes
    """
    if float_bits != 32 and float_bits != 64:
        raise ValueError(f"Float bits ({float_bits}) is not 32 or 64")
    if max_depth <= 0:
        raise ValueError(f"max_depth must be positive, got {max_depth}")

    cdef Buffer buf
    buf_init(&buf)
    try:
        encode_obj(&buf, data, float_bits, 0, max_depth, default)
        return PyBytes_FromStringAndSize(buf.data, buf.pos)
    finally:
        if buf.data != buf.stack_buf:
            free(buf.data)


# --------------------------------------------------------------------------
# Decoder
# --------------------------------------------------------------------------

cdef struct Decoder:
    const unsigned char *data
    size_t length
    size_t pos
    int depth
    int max_depth
    PyObject *ext_hook

cdef inline void dec_check_remaining(Decoder *d, size_t needed) except *:
    if d.pos + needed > d.length or d.pos + needed < d.pos:
        raise ValueError(f"Truncated rencode payload: need {needed} bytes at pos {d.pos}, total length {d.length}")

cdef inline uint64_t dec_read_leb128(Decoder *d) except *:
    dec_check_remaining(d, 1)
    cdef uint8_t byte = d.data[d.pos]
    d.pos += 1
    if (byte & 0x80) == 0:
        return byte

    cdef uint64_t result = <uint64_t>(byte & 0x7F)
    cdef int shift = 7
    while True:
        dec_check_remaining(d, 1)
        byte = d.data[d.pos]
        d.pos += 1
        if shift == 63:
            if (byte & 0x7E) != 0 or (byte & 0x80) != 0:
                raise ValueError("LEB128 integer overflow")
            result |= (<uint64_t>(byte & 0x01)) << 63
            break
        result |= (<uint64_t>(byte & 0x7F)) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
        if shift >= 64:
            raise ValueError("LEB128 integer overflow")
    return result

cdef inline int16_t dec_read_int16_le(Decoder *d) except *:
    dec_check_remaining(d, 2)
    cdef uint16_t v = 0
    memcpy(&v, &d.data[d.pos], 2)
    d.pos += 2
    if RENCODE_BIG_ENDIAN:
        v = bswap_16(v)
    return <int16_t>v

cdef inline int32_t dec_read_int32_le(Decoder *d) except *:
    dec_check_remaining(d, 4)
    cdef uint32_t v = 0
    memcpy(&v, &d.data[d.pos], 4)
    d.pos += 4
    if RENCODE_BIG_ENDIAN:
        v = bswap_32(v)
    return <int32_t>v

cdef inline int64_t dec_read_int64_le(Decoder *d) except *:
    dec_check_remaining(d, 8)
    cdef uint64_t v = 0
    memcpy(&v, &d.data[d.pos], 8)
    d.pos += 8
    if RENCODE_BIG_ENDIAN:
        v = bswap_64(v)
    return <int64_t>v

cdef inline float dec_read_float32_le(Decoder *d) except *:
    dec_check_remaining(d, 4)
    cdef uint32_t v = 0
    cdef float res = 0
    memcpy(&v, &d.data[d.pos], 4)
    d.pos += 4
    if RENCODE_BIG_ENDIAN:
        v = bswap_32(v)
    memcpy(&res, &v, 4)
    return res

cdef inline double dec_read_float64_le(Decoder *d) except *:
    dec_check_remaining(d, 8)
    cdef uint64_t v = 0
    cdef double res = 0
    memcpy(&v, &d.data[d.pos], 8)
    d.pos += 8
    if RENCODE_BIG_ENDIAN:
        v = bswap_64(v)
    memcpy(&res, &v, 8)
    return res


cdef object decode_obj(Decoder *d):
    if d.depth > d.max_depth:
        raise ValueError("Recursion limit exceeded while deserializing")

    dec_check_remaining(d, 1)
    cdef uint8_t opcode = d.data[d.pos]
    d.pos += 1

    cdef size_t count, slen, i, blen
    cdef uint64_t tag, ulen, ucount
    cdef int8_t res_i8
    cdef object l, t, di, item, k, v, s, b, raw, res_int

    # Fixed Positive Integers (0x00 - 0x3F: 0 to 63)
    if opcode < OP_POS_INT_START + OP_POS_INT_COUNT:
        return opcode - OP_POS_INT_START

    # Fixed Negative Integers (0x40 - 0x5F: -1 to -32)
    if opcode < OP_NEG_INT_START + OP_NEG_INT_COUNT:
        return -1 - (opcode - OP_NEG_INT_START)

    # Fixed UTF-8 Strings (0x60 - 0x7F: 0 to 31 bytes)
    if opcode < OP_STR_FIXED_START + OP_STR_FIXED_COUNT:
        slen = opcode - OP_STR_FIXED_START
        if slen == 0:
            return ""
        dec_check_remaining(d, slen)
        s = PyUnicode_DecodeUTF8(<const char*>&d.data[d.pos], slen, "strict")
        d.pos += slen
        return s

    # Fixed Binary Bytes (0x80 - 0x9F: 0 to 31 bytes)
    if opcode < OP_BIN_FIXED_START + OP_BIN_FIXED_COUNT:
        slen = opcode - OP_BIN_FIXED_START
        if slen == 0:
            return b""
        dec_check_remaining(d, slen)
        b = PyBytes_FromStringAndSize(<const char*>&d.data[d.pos], slen)
        d.pos += slen
        return b

    # Fixed List (0xA0 - 0xBF: 0 to 31 items)
    if opcode < OP_LIST_FIXED_START + OP_LIST_FIXED_COUNT:
        count = opcode - OP_LIST_FIXED_START
        if count > d.length - d.pos:
            raise ValueError(f"Truncated rencode payload: need {count} bytes, {d.length - d.pos} remaining")
        l = PyList_New(count)
        d.depth += 1
        for i in range(count):
            item = decode_obj(d)
            Py_INCREF(item)
            PyList_SET_ITEM(l, i, item)
        d.depth -= 1
        return l

    # Fixed Dictionary (0xC0 - 0xDF: 0 to 31 pairs)
    if opcode < OP_DICT_FIXED_START + OP_DICT_FIXED_COUNT:
        count = opcode - OP_DICT_FIXED_START
        if count > (d.length - d.pos) / 2:
            raise ValueError(f"Truncated rencode payload: need {count * 2} bytes, {d.length - d.pos} remaining")
        di = _PyDict_NewPresized(count)
        d.depth += 1
        for i in range(count):
            k = decode_obj(d)
            v = decode_obj(d)
            PyDict_SetItem(di, k, v)
        d.depth -= 1
        return di

    # Fixed Tuple (0xE0 - 0xEF: 0 to 15 items)
    if opcode < OP_TUPLE_FIXED_START + OP_TUPLE_FIXED_COUNT:
        count = opcode - OP_TUPLE_FIXED_START
        if count > d.length - d.pos:
            raise ValueError(f"Truncated rencode payload: need {count} bytes, {d.length - d.pos} remaining")
        t = PyTuple_New(count)
        d.depth += 1
        for i in range(count):
            item = decode_obj(d)
            Py_INCREF(item)
            PyTuple_SET_ITEM(t, i, item)
        d.depth -= 1
        return t

    # Opcodes 0xF0 - 0xFF
    if opcode == OP_NONE:
        return None
    elif opcode == OP_FALSE:
        return False
    elif opcode == OP_TRUE:
        return True
    elif opcode == OP_INT8:
        dec_check_remaining(d, 1)
        res_i8 = <int8_t>d.data[d.pos]
        d.pos += 1
        return res_i8
    elif opcode == OP_INT16:
        return dec_read_int16_le(d)
    elif opcode == OP_INT32:
        return dec_read_int32_le(d)
    elif opcode == OP_INT64:
        return dec_read_int64_le(d)
    elif opcode == OP_FLOAT32:
        return dec_read_float32_le(d)
    elif opcode == OP_FLOAT64:
        return dec_read_float64_le(d)
    elif opcode == OP_STR_V:
        ulen = dec_read_leb128(d)
        if ulen > <uint64_t>(d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: string length {ulen} exceeds remaining buffer")
        slen = <size_t>ulen
        if slen == 0:
            return ""
        s = PyUnicode_DecodeUTF8(<const char*>&d.data[d.pos], slen, "strict")
        d.pos += slen
        return s
    elif opcode == OP_BIN_V:
        ulen = dec_read_leb128(d)
        if ulen > <uint64_t>(d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: bytes length {ulen} exceeds remaining buffer")
        slen = <size_t>ulen
        if slen == 0:
            return b""
        b = PyBytes_FromStringAndSize(<const char*>&d.data[d.pos], slen)
        d.pos += slen
        return b
    elif opcode == OP_LIST_V:
        ucount = dec_read_leb128(d)
        if ucount > <uint64_t>(d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: declared list count {ucount} exceeds remaining buffer")
        count = <size_t>ucount
        l = PyList_New(count)
        d.depth += 1
        for i in range(count):
            item = decode_obj(d)
            Py_INCREF(item)
            PyList_SET_ITEM(l, i, item)
        d.depth -= 1
        return l
    elif opcode == OP_DICT_V:
        ucount = dec_read_leb128(d)
        if ucount > <uint64_t>((d.length - d.pos) / 2):
            raise ValueError(f"Truncated rencode payload: declared dict count {ucount} exceeds remaining buffer")
        count = <size_t>ucount
        di = _PyDict_NewPresized(count)
        d.depth += 1
        for i in range(count):
            k = decode_obj(d)
            v = decode_obj(d)
            PyDict_SetItem(di, k, v)
        d.depth -= 1
        return di
    elif opcode == OP_TUPLE_V:
        ucount = dec_read_leb128(d)
        if ucount > <uint64_t>(d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: declared tuple count {ucount} exceeds remaining buffer")
        count = <size_t>ucount
        t = PyTuple_New(count)
        d.depth += 1
        for i in range(count):
            item = decode_obj(d)
            Py_INCREF(item)
            PyTuple_SET_ITEM(t, i, item)
        d.depth -= 1
        return t
    elif opcode == OP_BIGINT:
        ulen = dec_read_leb128(d)
        if ulen > <uint64_t>(d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: bigint byte length {ulen} exceeds remaining buffer")
        blen = <size_t>ulen
        res_int = _PyLong_FromByteArray(<const unsigned char*>&d.data[d.pos], blen, 1, 1)
        d.pos += blen
        return res_int
    elif opcode == OP_EXT:
        tag = dec_read_leb128(d)
        ulen = dec_read_leb128(d)
        if ulen > <uint64_t>(d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: extension byte length {ulen} exceeds remaining buffer")
        blen = <size_t>ulen
        raw = PyBytes_FromStringAndSize(<const char*>&d.data[d.pos], blen)
        d.pos += blen
        if d.ext_hook != NULL:
            return (<object>d.ext_hook)(tag, raw)
        return Ext(tag, raw)


def loads(object data, decode_utf8=None, int max_depth=MAX_RECURSION_DEPTH, ext_hook=None):
    """
    Decode rencode v2 binary data into Python objects.

    Supports any object adhering to the Python buffer protocol (bytes, bytearray, memoryview).

    :param data: The binary payload to decode
    :param decode_utf8: Deprecated / unused in v2 (text/binary distinction is preserved on wire)
    :param max_depth: Maximum recursion depth allowed (default 1000)
    :param ext_hook: Optional callable(tag: int, data: bytes) -> object for custom extension tags
    :return: The decoded Python object
    """
    if max_depth <= 0:
        raise ValueError(f"max_depth must be positive, got {max_depth}")

    cdef Decoder d
    cdef Py_buffer view
    cdef int has_buffer = 0

    if PyBytes_Check(data):
        d.data = <const unsigned char*>PyBytes_AS_STRING(data)
        d.length = PyBytes_GET_SIZE(data)
    else:
        if PyObject_GetBuffer(data, &view, PyBUF_SIMPLE) != 0:
            raise TypeError(f"a bytes-like object is required, not '{type(data).__name__}'")
        has_buffer = 1
        d.data = <const unsigned char*>view.buf
        d.length = <size_t>view.len

    d.pos = 0
    d.depth = 0
    d.max_depth = max_depth
    d.ext_hook = <PyObject*>ext_hook if ext_hook is not None else NULL

    try:
        res = decode_obj(&d)
        if d.pos != d.length:
            raise ValueError(f"Unconsumed trailing data: {d.length - d.pos} bytes remaining")
        return res
    finally:
        if has_buffer:
            PyBuffer_Release(&view)
