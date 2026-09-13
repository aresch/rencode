# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False, nonecheck=False
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

from cython cimport likely, unlikely
from cpython.ref cimport PyObject
from cpython.buffer cimport PyObject_GetBuffer, PyBuffer_Release, Py_buffer, PyBUF_SIMPLE

cdef extern from "Python.h":
    # References & Singletons
    void Py_INCREF(PyObject *o)
    void Py_DECREF(PyObject *o)
    PyObject* Py_None
    PyObject* Py_False
    PyObject* Py_True

    # Type Checks
    bint PyBool_Check(PyObject *op)
    bint PyLong_Check(PyObject *op)
    bint PyLong_CheckExact(PyObject *op)
    bint PyFloat_Check(PyObject *op)
    bint PyFloat_CheckExact(PyObject *op)
    bint PyUnicode_Check(PyObject *op)
    bint PyUnicode_CheckExact(PyObject *op)
    bint PyBytes_Check(PyObject *op)
    bint PyBytes_CheckExact(PyObject *op)
    bint PyByteArray_Check(PyObject *op)
    bint PyByteArray_CheckExact(PyObject *op)
    bint PyList_Check(PyObject *op)
    bint PyList_CheckExact(PyObject *op)
    bint PyTuple_Check(PyObject *op)
    bint PyTuple_CheckExact(PyObject *op)
    bint PyDict_Check(PyObject *op)
    bint PyDict_CheckExact(PyObject *op)
    bint PyMemoryView_Check(PyObject *op)

    # Int & Float API
    PyObject* PyLong_FromLong(long v)
    PyObject* PyLong_FromLongLong(long long v)
    long long PyLong_AsLongLongAndOverflow(PyObject *pylong, int *overflow)
    PyObject* _PyLong_FromByteArray(const unsigned char* bytes, size_t n, int little_endian, int is_signed)
    PyObject* PyFloat_FromDouble(double v)
    double PyFloat_AS_DOUBLE(PyObject *op)

    # String & Bytes API
    PyObject* PyUnicode_FromStringAndSize(const char *u, Py_ssize_t size)
    const char* PyUnicode_AsUTF8AndSize(PyObject *unicode, Py_ssize_t *size)
    PyObject* PyBytes_FromStringAndSize(const char *v, Py_ssize_t len)
    char* PyBytes_AS_STRING(PyObject *string)
    Py_ssize_t PyBytes_GET_SIZE(PyObject *string)
    char* PyByteArray_AS_STRING(PyObject *op)
    Py_ssize_t PyByteArray_GET_SIZE(PyObject *op)

    # Containers
    PyObject* PyList_New(Py_ssize_t len)
    void PyList_SET_ITEM(PyObject *list, Py_ssize_t i, PyObject *o)
    Py_ssize_t PyList_GET_SIZE(PyObject *list)
    PyObject* PyList_GET_ITEM(PyObject *list, Py_ssize_t i)

    PyObject* PyTuple_New(Py_ssize_t len)
    void PyTuple_SET_ITEM(PyObject *p, Py_ssize_t pos, PyObject *o)
    Py_ssize_t PyTuple_GET_SIZE(PyObject *p)
    PyObject* PyTuple_GET_ITEM(PyObject *p, Py_ssize_t pos)

    PyObject* PyDict_New()
    int PyDict_SetItem(PyObject *p, PyObject *key, PyObject *val)
    Py_ssize_t PyDict_Size(PyObject *p)
    int PyDict_Next(PyObject *p, Py_ssize_t *ppos, PyObject **pkey, PyObject **pvalue)
    PyObject* _PyDict_NewPresized(Py_ssize_t minused)

    void PyErr_Clear()

cdef extern from *:
    """
    static CYTHON_INLINE PyObject* _steal_ref(PyObject *o) { return o; }
    """
    object _steal_ref(PyObject *o)

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
    STACK_BUF_SIZE = 2048

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

cdef PyObject *EMPTY_STR = NULL
cdef PyObject *EMPTY_BYTES = NULL
cdef PyObject *BYTE_INTS[256]

cdef void _init_singletons():
    global EMPTY_STR, EMPTY_BYTES
    EMPTY_STR = <PyObject*>""
    EMPTY_BYTES = <PyObject*>b""
    cdef int i
    cdef int8_t s8
    for i in range(256):
        s8 = <int8_t><uint8_t>i
        BYTE_INTS[i] = PyLong_FromLong(s8)

_init_singletons()

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

cdef int _buf_grow(Buffer *buf, size_t need) except -1:
    if need > (<size_t>-1) - buf.pos - 1024:
        raise MemoryError("Buffer size overflow")
    cdef size_t new_cap = buf.capacity * 2
    if new_cap < buf.pos + need:
        new_cap = buf.pos + need + 1024
    cdef char *new_data
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

cdef inline int buf_ensure(Buffer *buf, size_t need) except -1:
    if unlikely(buf.pos + need > buf.capacity):
        return _buf_grow(buf, need)
    return 0

cdef inline int buf_write_byte(Buffer *buf, uint8_t b) except -1:
    if unlikely(buf.pos >= buf.capacity):
        _buf_grow(buf, 1)
    buf.data[buf.pos] = <char>b
    buf.pos += 1
    return 0

cdef inline int buf_write_bytes(Buffer *buf, const void *src, size_t n) except -1:
    if n > 0:
        if unlikely(buf.pos + n > buf.capacity):
            _buf_grow(buf, n)
        memcpy(&buf.data[buf.pos], src, n)
        buf.pos += n
    return 0

cdef inline void buf_write_leb128_nocheck(Buffer *buf, uint64_t val):
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

cdef inline int buf_write_leb128(Buffer *buf, uint64_t val) except -1:
    if unlikely(buf.pos + 10 > buf.capacity):
        _buf_grow(buf, 10)
    buf_write_leb128_nocheck(buf, val)
    return 0

cdef inline int _encode_int(Buffer *buf, PyObject *data) except -1:
    cdef int overflow = 0
    cdef long long val = PyLong_AsLongLongAndOverflow(data, &overflow)
    cdef size_t byte_len
    cdef object py_int, raw
    cdef Py_ssize_t raw_len
    cdef uint16_t v16
    cdef uint32_t v32
    cdef uint64_t v64
    if likely(overflow == 0):
        if unlikely(buf.pos + 9 > buf.capacity):
            _buf_grow(buf, 9)
        if 0 <= val <= 63:
            buf.data[buf.pos] = <char>(OP_POS_INT_START + <uint8_t>val)
            buf.pos += 1
        elif -32 <= val <= -1:
            buf.data[buf.pos] = <char>(OP_NEG_INT_START + <uint8_t>(-val - 1))
            buf.pos += 1
        elif -128 <= val <= 127:
            buf.data[buf.pos] = <char>OP_INT8
            buf.data[buf.pos + 1] = <char>val
            buf.pos += 2
        elif -32768 <= val <= 32767:
            buf.data[buf.pos] = <char>OP_INT16
            if not RENCODE_BIG_ENDIAN:
                memcpy(&buf.data[buf.pos + 1], &val, 2)
            else:
                v16 = bswap_16(<uint16_t>val)
                memcpy(&buf.data[buf.pos + 1], &v16, 2)
            buf.pos += 3
        elif -2147483648 <= val <= 2147483647:
            buf.data[buf.pos] = <char>OP_INT32
            if not RENCODE_BIG_ENDIAN:
                memcpy(&buf.data[buf.pos + 1], &val, 4)
            else:
                v32 = bswap_32(<uint32_t>val)
                memcpy(&buf.data[buf.pos + 1], &v32, 4)
            buf.pos += 5
        else:
            buf.data[buf.pos] = <char>OP_INT64
            if not RENCODE_BIG_ENDIAN:
                memcpy(&buf.data[buf.pos + 1], &val, 8)
            else:
                v64 = bswap_64(<uint64_t>val)
                memcpy(&buf.data[buf.pos + 1], &v64, 8)
            buf.pos += 9
    else:
        # Big integer
        py_int = <object>data
        byte_len = ((py_int + 1).bit_length() + 8) // 8 if py_int < 0 else (py_int.bit_length() + 8) // 8
        raw = py_int.to_bytes(byte_len, byteorder="little", signed=True)
        raw_len = PyBytes_GET_SIZE(<PyObject*>raw)
        buf_write_byte(buf, OP_BIGINT)
        buf_write_leb128(buf, <uint64_t>raw_len)
        buf_write_bytes(buf, PyBytes_AS_STRING(<PyObject*>raw), raw_len)
    return 0

cdef inline int _encode_float(Buffer *buf, double val, int float_bits) except -1:
    cdef uint64_t v64
    cdef uint32_t v32
    cdef float f
    if unlikely(buf.pos + 9 > buf.capacity):
        _buf_grow(buf, 9)
    if likely(float_bits == 64):
        buf.data[buf.pos] = <char>OP_FLOAT64
        if not RENCODE_BIG_ENDIAN:
            memcpy(&buf.data[buf.pos + 1], &val, 8)
        else:
            v64 = 0
            memcpy(&v64, &val, 8)
            v64 = bswap_64(v64)
            memcpy(&buf.data[buf.pos + 1], &v64, 8)
        buf.pos += 9
    elif float_bits == 32:
        buf.data[buf.pos] = <char>OP_FLOAT32
        f = <float>val
        if not RENCODE_BIG_ENDIAN:
            memcpy(&buf.data[buf.pos + 1], &f, 4)
        else:
            v32 = 0
            memcpy(&v32, &f, 4)
            v32 = bswap_32(v32)
            memcpy(&buf.data[buf.pos + 1], &v32, 4)
        buf.pos += 5
    else:
        raise ValueError(f"Float bits ({float_bits}) is not 32 or 64")
    return 0

cdef inline int _encode_str(Buffer *buf, PyObject *data) except -1:
    cdef Py_ssize_t slen = 0
    cdef const char *str_data = PyUnicode_AsUTF8AndSize(data, &slen)
    if str_data == NULL:
        return -1
    if slen < OP_STR_FIXED_COUNT:
        if unlikely(buf.pos + 1 + slen > buf.capacity):
            _buf_grow(buf, 1 + slen)
        buf.data[buf.pos] = <char>(OP_STR_FIXED_START + <uint8_t>slen)
        if slen > 0:
            memcpy(&buf.data[buf.pos + 1], str_data, slen)
        buf.pos += 1 + slen
    else:
        if unlikely(buf.pos + 1 + 10 + slen > buf.capacity):
            _buf_grow(buf, 1 + 10 + slen)
        buf.data[buf.pos] = <char>OP_STR_V
        buf.pos += 1
        buf_write_leb128_nocheck(buf, <uint64_t>slen)
        memcpy(&buf.data[buf.pos], str_data, slen)
        buf.pos += slen
    return 0

cdef inline int _encode_bytes(Buffer *buf, PyObject *data) except -1:
    cdef Py_ssize_t slen = PyBytes_GET_SIZE(data)
    if slen < OP_BIN_FIXED_COUNT:
        if unlikely(buf.pos + 1 + slen > buf.capacity):
            _buf_grow(buf, 1 + slen)
        buf.data[buf.pos] = <char>(OP_BIN_FIXED_START + <uint8_t>slen)
        if slen > 0:
            memcpy(&buf.data[buf.pos + 1], PyBytes_AS_STRING(data), slen)
        buf.pos += 1 + slen
    else:
        if unlikely(buf.pos + 1 + 10 + slen > buf.capacity):
            _buf_grow(buf, 1 + 10 + slen)
        buf.data[buf.pos] = <char>OP_BIN_V
        buf.pos += 1
        buf_write_leb128_nocheck(buf, <uint64_t>slen)
        memcpy(&buf.data[buf.pos], PyBytes_AS_STRING(data), slen)
        buf.pos += slen
    return 0

cdef inline int _encode_bytearray(Buffer *buf, PyObject *data) except -1:
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
    cdef Py_ssize_t slen = PyBytes_GET_SIZE(<PyObject*>data_obj)
    buf_write_byte(buf, OP_EXT)
    buf_write_leb128(buf, tag)
    buf_write_leb128(buf, <uint64_t>slen)
    buf_write_bytes(buf, PyBytes_AS_STRING(<PyObject*>data_obj), slen)
    return 0

cdef int encode_obj(Buffer *buf, PyObject *data, int float_bits, int depth, int max_depth, PyObject *default_fn) except -1:
    if unlikely(depth > max_depth):
        raise ValueError("Recursion limit exceeded while serializing")

    cdef size_t count, i
    cdef Py_ssize_t dict_pos = 0
    cdef PyObject *pk = NULL
    cdef PyObject *pv = NULL
    cdef object def_res

    # Fast-path standard exact types
    if data == Py_None:
        if unlikely(buf.pos >= buf.capacity):
            _buf_grow(buf, 1)
        buf.data[buf.pos] = <char>OP_NONE
        buf.pos += 1
        return 0
    if data == Py_False:
        if unlikely(buf.pos >= buf.capacity):
            _buf_grow(buf, 1)
        buf.data[buf.pos] = <char>OP_FALSE
        buf.pos += 1
        return 0
    if data == Py_True:
        if unlikely(buf.pos >= buf.capacity):
            _buf_grow(buf, 1)
        buf.data[buf.pos] = <char>OP_TRUE
        buf.pos += 1
        return 0
    if PyLong_CheckExact(data):
        return _encode_int(buf, data)
    if PyFloat_CheckExact(data):
        return _encode_float(buf, PyFloat_AS_DOUBLE(data), float_bits)
    if PyUnicode_CheckExact(data):
        return _encode_str(buf, data)
    if PyBytes_CheckExact(data):
        return _encode_bytes(buf, data)
    if PyList_CheckExact(data):
        count = <size_t>PyList_GET_SIZE(data)
        if count < OP_LIST_FIXED_COUNT:
            if unlikely(buf.pos >= buf.capacity):
                _buf_grow(buf, 1)
            buf.data[buf.pos] = <char>(OP_LIST_FIXED_START + <uint8_t>count)
            buf.pos += 1
        else:
            if unlikely(buf.pos + 11 > buf.capacity):
                _buf_grow(buf, 11)
            buf.data[buf.pos] = <char>OP_LIST_V
            buf.pos += 1
            buf_write_leb128_nocheck(buf, <uint64_t>count)
        depth += 1
        for i in range(count):
            encode_obj(buf, PyList_GET_ITEM(data, i), float_bits, depth, max_depth, default_fn)
        return 0
    if PyDict_CheckExact(data):
        count = <size_t>PyDict_Size(data)
        if count < OP_DICT_FIXED_COUNT:
            if unlikely(buf.pos >= buf.capacity):
                _buf_grow(buf, 1)
            buf.data[buf.pos] = <char>(OP_DICT_FIXED_START + <uint8_t>count)
            buf.pos += 1
        else:
            if unlikely(buf.pos + 11 > buf.capacity):
                _buf_grow(buf, 11)
            buf.data[buf.pos] = <char>OP_DICT_V
            buf.pos += 1
            buf_write_leb128_nocheck(buf, <uint64_t>count)
        depth += 1
        dict_pos = 0
        while PyDict_Next(data, &dict_pos, &pk, &pv):
            encode_obj(buf, pk, float_bits, depth, max_depth, default_fn)
            encode_obj(buf, pv, float_bits, depth, max_depth, default_fn)
        return 0
    if PyTuple_CheckExact(data):
        count = <size_t>PyTuple_GET_SIZE(data)
        if count < OP_TUPLE_FIXED_COUNT:
            if unlikely(buf.pos >= buf.capacity):
                _buf_grow(buf, 1)
            buf.data[buf.pos] = <char>(OP_TUPLE_FIXED_START + <uint8_t>count)
            buf.pos += 1
        else:
            if unlikely(buf.pos + 11 > buf.capacity):
                _buf_grow(buf, 11)
            buf.data[buf.pos] = <char>OP_TUPLE_V
            buf.pos += 1
            buf_write_leb128_nocheck(buf, <uint64_t>count)
        depth += 1
        for i in range(count):
            encode_obj(buf, PyTuple_GET_ITEM(data, i), float_bits, depth, max_depth, default_fn)
        return 0
    if PyByteArray_CheckExact(data):
        return _encode_bytearray(buf, data)
    if isinstance(<object>data, Ext):
        return _encode_ext(buf, <Ext>(<object>data))

    # Subclasses and fallback types
    if PyBool_Check(data):
        if unlikely(buf.pos >= buf.capacity):
            _buf_grow(buf, 1)
        buf.data[buf.pos] = <char>(OP_TRUE if data == Py_True else OP_FALSE)
        buf.pos += 1
        return 0
    if PyLong_Check(data):
        return _encode_int(buf, data)
    if PyFloat_Check(data):
        return _encode_float(buf, PyFloat_AS_DOUBLE(data), float_bits)
    if PyUnicode_Check(data):
        return _encode_str(buf, data)
    if PyBytes_Check(data):
        return _encode_bytes(buf, data)
    if PyByteArray_Check(data):
        return _encode_bytearray(buf, data)
    if PyList_Check(data):
        count = len(<object>data)
        if count < OP_LIST_FIXED_COUNT:
            buf_write_byte(buf, OP_LIST_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_LIST_V)
            buf_write_leb128(buf, <uint64_t>count)
        depth += 1
        for item in <object>data:
            encode_obj(buf, <PyObject*>item, float_bits, depth, max_depth, default_fn)
        return 0
    if PyTuple_Check(data):
        count = len(<object>data)
        if count < OP_TUPLE_FIXED_COUNT:
            buf_write_byte(buf, OP_TUPLE_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_TUPLE_V)
            buf_write_leb128(buf, <uint64_t>count)
        depth += 1
        for item in <object>data:
            encode_obj(buf, <PyObject*>item, float_bits, depth, max_depth, default_fn)
        return 0
    if PyDict_Check(data):
        count = len(<object>data)
        if count < OP_DICT_FIXED_COUNT:
            buf_write_byte(buf, OP_DICT_FIXED_START + <uint8_t>count)
        else:
            buf_write_byte(buf, OP_DICT_V)
            buf_write_leb128(buf, <uint64_t>count)
        depth += 1
        dict_pos = 0
        while PyDict_Next(data, &dict_pos, &pk, &pv):
            encode_obj(buf, pk, float_bits, depth, max_depth, default_fn)
            encode_obj(buf, pv, float_bits, depth, max_depth, default_fn)
        return 0
    if PyMemoryView_Check(data):
        return _encode_buffer(buf, <object>data)
    if default_fn != NULL:
        def_res = (<object>default_fn)(<object>data)
        return encode_obj(buf, <PyObject*>def_res, float_bits, depth + 1, max_depth, default_fn)
    if _encode_buffer(buf, <object>data) == 0:
        return 0

    raise TypeError(f"type {type(<object>data)} not handled")


def dumps(data, int float_bits=DEFAULT_FLOAT_BITS, int max_depth=MAX_RECURSION_DEPTH, default=None):
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
    cdef PyObject *def_fn = <PyObject*>default if default is not None else NULL
    try:
        encode_obj(&buf, <PyObject*>data, float_bits, 0, max_depth, def_fn)
        return _steal_ref(PyBytes_FromStringAndSize(buf.data, buf.pos))
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

cdef void _raise_truncated(size_t pos, size_t needed, size_t length) except *:
    raise ValueError(f"Truncated rencode payload: need {needed} bytes at pos {pos}, total length {length}")

cdef inline int dec_check_remaining(Decoder *d, size_t needed) except -1:
    if unlikely(d.length - d.pos < needed):
        _raise_truncated(d.pos, needed, d.length)
    return 0

cdef inline uint64_t dec_read_leb128(Decoder *d) except? 0xFFFFFFFFFFFFFFFFULL:
    if unlikely(d.pos >= d.length):
        _raise_truncated(d.pos, 1, d.length)
    cdef uint8_t byte = d.data[d.pos]
    d.pos += 1
    if (byte & 0x80) == 0:
        return byte

    cdef uint64_t result = <uint64_t>(byte & 0x7F)
    cdef int shift = 7
    while True:
        if unlikely(d.pos >= d.length):
            _raise_truncated(d.pos, 1, d.length)
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
        if unlikely(shift >= 64):
            raise ValueError("LEB128 integer overflow")
    return result


cdef PyObject* decode_obj(Decoder *d) except NULL:
    if unlikely(d.depth > d.max_depth):
        raise ValueError("Recursion limit exceeded while deserializing")

    if unlikely(d.pos >= d.length):
        _raise_truncated(d.pos, 1, d.length)
    cdef uint8_t opcode = d.data[d.pos]
    d.pos += 1

    cdef size_t count, slen, blen, i
    cdef uint64_t tag, ulen, ucount
    cdef uint16_t v16
    cdef uint32_t v32
    cdef uint64_t v64
    cdef float f32
    cdef double f64
    cdef PyObject *raw_obj = NULL
    cdef PyObject *item_obj = NULL
    cdef PyObject *k_obj = NULL
    cdef PyObject *v_obj = NULL
    cdef object hook_res, ext_instance

    # Fixed Positive Integers (0x00 - 0x3F: 0 to 63)
    if opcode < OP_POS_INT_START + OP_POS_INT_COUNT:
        raw_obj = BYTE_INTS[opcode]
        Py_INCREF(raw_obj)
        return raw_obj

    # Fixed Negative Integers (0x40 - 0x5F: -1 to -32)
    if opcode < OP_NEG_INT_START + OP_NEG_INT_COUNT:
        raw_obj = BYTE_INTS[<uint8_t>(-1 - (opcode - OP_NEG_INT_START))]
        Py_INCREF(raw_obj)
        return raw_obj

    # Fixed UTF-8 Strings (0x60 - 0x7F: 0 to 31 bytes)
    if opcode < OP_STR_FIXED_START + OP_STR_FIXED_COUNT:
        slen = opcode - OP_STR_FIXED_START
        if slen == 0:
            Py_INCREF(EMPTY_STR)
            return EMPTY_STR
        if unlikely(d.length - d.pos < slen):
            _raise_truncated(d.pos, slen, d.length)
        raw_obj = PyUnicode_FromStringAndSize(<const char*>&d.data[d.pos], slen)
        d.pos += slen
        return raw_obj

    # Fixed Binary Bytes (0x80 - 0x9F: 0 to 31 bytes)
    if opcode < OP_BIN_FIXED_START + OP_BIN_FIXED_COUNT:
        slen = opcode - OP_BIN_FIXED_START
        if slen == 0:
            Py_INCREF(EMPTY_BYTES)
            return EMPTY_BYTES
        if unlikely(d.length - d.pos < slen):
            _raise_truncated(d.pos, slen, d.length)
        raw_obj = PyBytes_FromStringAndSize(<const char*>&d.data[d.pos], slen)
        d.pos += slen
        return raw_obj

    # Fixed List (0xA0 - 0xBF: 0 to 31 items)
    if opcode < OP_LIST_FIXED_START + OP_LIST_FIXED_COUNT:
        count = opcode - OP_LIST_FIXED_START
        if unlikely(count > d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: need {count} bytes, {d.length - d.pos} remaining")
        raw_obj = PyList_New(count)
        if unlikely(raw_obj == NULL):
            return NULL
        d.depth += 1
        for i in range(count):
            item_obj = decode_obj(d)
            if unlikely(item_obj == NULL):
                d.depth -= 1
                Py_DECREF(raw_obj)
                return NULL
            PyList_SET_ITEM(raw_obj, i, item_obj)
        d.depth -= 1
        return raw_obj

    # Fixed Dictionary (0xC0 - 0xDF: 0 to 31 pairs)
    if opcode < OP_DICT_FIXED_START + OP_DICT_FIXED_COUNT:
        count = opcode - OP_DICT_FIXED_START
        if unlikely(count > (d.length - d.pos) / 2):
            raise ValueError(f"Truncated rencode payload: need {count * 2} bytes, {d.length - d.pos} remaining")
        raw_obj = _PyDict_NewPresized(count)
        if unlikely(raw_obj == NULL):
            return NULL
        d.depth += 1
        for i in range(count):
            k_obj = decode_obj(d)
            if unlikely(k_obj == NULL):
                d.depth -= 1
                Py_DECREF(raw_obj)
                return NULL
            v_obj = decode_obj(d)
            if unlikely(v_obj == NULL):
                d.depth -= 1
                Py_DECREF(k_obj)
                Py_DECREF(raw_obj)
                return NULL
            if unlikely(PyDict_SetItem(raw_obj, k_obj, v_obj) < 0):
                d.depth -= 1
                Py_DECREF(k_obj)
                Py_DECREF(v_obj)
                Py_DECREF(raw_obj)
                return NULL
            Py_DECREF(k_obj)
            Py_DECREF(v_obj)
        d.depth -= 1
        return raw_obj

    # Fixed Tuple (0xE0 - 0xEF: 0 to 15 items)
    if opcode < OP_TUPLE_FIXED_START + OP_TUPLE_FIXED_COUNT:
        count = opcode - OP_TUPLE_FIXED_START
        if unlikely(count > d.length - d.pos):
            raise ValueError(f"Truncated rencode payload: need {count} bytes, {d.length - d.pos} remaining")
        raw_obj = PyTuple_New(count)
        if unlikely(raw_obj == NULL):
            return NULL
        d.depth += 1
        for i in range(count):
            item_obj = decode_obj(d)
            if unlikely(item_obj == NULL):
                d.depth -= 1
                Py_DECREF(raw_obj)
                return NULL
            PyTuple_SET_ITEM(raw_obj, i, item_obj)
        d.depth -= 1
        return raw_obj

    # Opcodes 0xF0 - 0xFF
    if opcode == OP_NONE:
        Py_INCREF(Py_None)
        return Py_None
    elif opcode == OP_FALSE:
        Py_INCREF(Py_False)
        return Py_False
    elif opcode == OP_TRUE:
        Py_INCREF(Py_True)
        return Py_True
    elif opcode == OP_INT8:
        if unlikely(d.pos >= d.length):
            _raise_truncated(d.pos, 1, d.length)
        raw_obj = BYTE_INTS[d.data[d.pos]]
        d.pos += 1
        Py_INCREF(raw_obj)
        return raw_obj
    elif opcode == OP_INT16:
        if unlikely(d.length - d.pos < 2):
            _raise_truncated(d.pos, 2, d.length)
        memcpy(&v16, &d.data[d.pos], 2)
        d.pos += 2
        if RENCODE_BIG_ENDIAN:
            v16 = bswap_16(v16)
        if -128 <= (<int16_t>v16) <= 127:
            raw_obj = BYTE_INTS[<uint8_t>(<int16_t>v16)]
            Py_INCREF(raw_obj)
            return raw_obj
        return PyLong_FromLong(<int16_t>v16)
    elif opcode == OP_INT32:
        if unlikely(d.length - d.pos < 4):
            _raise_truncated(d.pos, 4, d.length)
        memcpy(&v32, &d.data[d.pos], 4)
        d.pos += 4
        if RENCODE_BIG_ENDIAN:
            v32 = bswap_32(v32)
        if -128 <= (<int32_t>v32) <= 127:
            raw_obj = BYTE_INTS[<uint8_t>(<int32_t>v32)]
            Py_INCREF(raw_obj)
            return raw_obj
        return PyLong_FromLong(<int32_t>v32)
    elif opcode == OP_INT64:
        if unlikely(d.length - d.pos < 8):
            _raise_truncated(d.pos, 8, d.length)
        memcpy(&v64, &d.data[d.pos], 8)
        d.pos += 8
        if RENCODE_BIG_ENDIAN:
            v64 = bswap_64(v64)
        if -128 <= (<int64_t>v64) <= 127:
            raw_obj = BYTE_INTS[<uint8_t>(<int64_t>v64)]
            Py_INCREF(raw_obj)
            return raw_obj
        return PyLong_FromLongLong(<int64_t>v64)
    elif opcode == OP_FLOAT32:
        if unlikely(d.length - d.pos < 4):
            _raise_truncated(d.pos, 4, d.length)
        if not RENCODE_BIG_ENDIAN:
            memcpy(&f32, &d.data[d.pos], 4)
        else:
            memcpy(&v32, &d.data[d.pos], 4)
            v32 = bswap_32(v32)
            memcpy(&f32, &v32, 4)
        d.pos += 4
        return PyFloat_FromDouble(f32)
    elif opcode == OP_FLOAT64:
        if unlikely(d.length - d.pos < 8):
            _raise_truncated(d.pos, 8, d.length)
        if not RENCODE_BIG_ENDIAN:
            memcpy(&f64, &d.data[d.pos], 8)
        else:
            memcpy(&v64, &d.data[d.pos], 8)
            v64 = bswap_64(v64)
            memcpy(&f64, &v64, 8)
        d.pos += 8
        return PyFloat_FromDouble(f64)
    elif opcode == OP_STR_V:
        ulen = dec_read_leb128(d)
        if unlikely(ulen > <uint64_t>(d.length - d.pos)):
            raise ValueError(f"Truncated rencode payload: string length {ulen} exceeds remaining buffer")
        slen = <size_t>ulen
        if slen == 0:
            Py_INCREF(EMPTY_STR)
            return EMPTY_STR
        raw_obj = PyUnicode_FromStringAndSize(<const char*>&d.data[d.pos], slen)
        d.pos += slen
        return raw_obj
    elif opcode == OP_BIN_V:
        ulen = dec_read_leb128(d)
        if unlikely(ulen > <uint64_t>(d.length - d.pos)):
            raise ValueError(f"Truncated rencode payload: bytes length {ulen} exceeds remaining buffer")
        slen = <size_t>ulen
        if slen == 0:
            Py_INCREF(EMPTY_BYTES)
            return EMPTY_BYTES
        raw_obj = PyBytes_FromStringAndSize(<const char*>&d.data[d.pos], slen)
        d.pos += slen
        return raw_obj
    elif opcode == OP_LIST_V:
        ucount = dec_read_leb128(d)
        if unlikely(ucount > <uint64_t>(d.length - d.pos)):
            raise ValueError(f"Truncated rencode payload: declared list count {ucount} exceeds remaining buffer")
        count = <size_t>ucount
        raw_obj = PyList_New(count)
        if unlikely(raw_obj == NULL):
            return NULL
        d.depth += 1
        for i in range(count):
            item_obj = decode_obj(d)
            if unlikely(item_obj == NULL):
                d.depth -= 1
                Py_DECREF(raw_obj)
                return NULL
            PyList_SET_ITEM(raw_obj, i, item_obj)
        d.depth -= 1
        return raw_obj
    elif opcode == OP_DICT_V:
        ucount = dec_read_leb128(d)
        if unlikely(ucount > <uint64_t>((d.length - d.pos) / 2)):
            raise ValueError(f"Truncated rencode payload: declared dict count {ucount} exceeds remaining buffer")
        count = <size_t>ucount
        raw_obj = _PyDict_NewPresized(count)
        if unlikely(raw_obj == NULL):
            return NULL
        d.depth += 1
        for i in range(count):
            k_obj = decode_obj(d)
            if unlikely(k_obj == NULL):
                d.depth -= 1
                Py_DECREF(raw_obj)
                return NULL
            v_obj = decode_obj(d)
            if unlikely(v_obj == NULL):
                d.depth -= 1
                Py_DECREF(k_obj)
                Py_DECREF(raw_obj)
                return NULL
            if unlikely(PyDict_SetItem(raw_obj, k_obj, v_obj) < 0):
                d.depth -= 1
                Py_DECREF(k_obj)
                Py_DECREF(v_obj)
                Py_DECREF(raw_obj)
                return NULL
            Py_DECREF(k_obj)
            Py_DECREF(v_obj)
        d.depth -= 1
        return raw_obj
    elif opcode == OP_TUPLE_V:
        ucount = dec_read_leb128(d)
        if unlikely(ucount > <uint64_t>(d.length - d.pos)):
            raise ValueError(f"Truncated rencode payload: declared tuple count {ucount} exceeds remaining buffer")
        count = <size_t>ucount
        raw_obj = PyTuple_New(count)
        if unlikely(raw_obj == NULL):
            return NULL
        d.depth += 1
        for i in range(count):
            item_obj = decode_obj(d)
            if unlikely(item_obj == NULL):
                d.depth -= 1
                Py_DECREF(raw_obj)
                return NULL
            PyTuple_SET_ITEM(raw_obj, i, item_obj)
        d.depth -= 1
        return raw_obj
    elif opcode == OP_BIGINT:
        ulen = dec_read_leb128(d)
        if unlikely(ulen > <uint64_t>(d.length - d.pos)):
            raise ValueError(f"Truncated rencode payload: bigint byte length {ulen} exceeds remaining buffer")
        blen = <size_t>ulen
        raw_obj = _PyLong_FromByteArray(<const unsigned char*>&d.data[d.pos], blen, 1, 1)
        d.pos += blen
        return raw_obj
    elif opcode == OP_EXT:
        tag = dec_read_leb128(d)
        ulen = dec_read_leb128(d)
        if unlikely(ulen > <uint64_t>(d.length - d.pos)):
            raise ValueError(f"Truncated rencode payload: extension byte length {ulen} exceeds remaining buffer")
        blen = <size_t>ulen
        raw_obj = PyBytes_FromStringAndSize(<const char*>&d.data[d.pos], blen)
        d.pos += blen
        if d.ext_hook != NULL:
            hook_res = (<object>d.ext_hook)(tag, _steal_ref(raw_obj))
            Py_INCREF(<PyObject*>hook_res)
            return <PyObject*>hook_res
        ext_instance = Ext(tag, _steal_ref(raw_obj))
        Py_INCREF(<PyObject*>ext_instance)
        return <PyObject*>ext_instance
    else:
        raise ValueError(f"Unknown opcode: 0x{opcode:02X}")


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
    cdef PyObject *res

    if PyBytes_CheckExact(<PyObject*>data):
        d.data = <const unsigned char*>PyBytes_AS_STRING(<PyObject*>data)
        d.length = <size_t>PyBytes_GET_SIZE(<PyObject*>data)
        d.pos = 0
        d.depth = 0
        d.max_depth = max_depth
        d.ext_hook = <PyObject*>ext_hook if ext_hook is not None else NULL
        res = decode_obj(&d)
        if res == NULL:
            return None
        if d.pos != d.length:
            Py_DECREF(res)
            raise ValueError(f"Unconsumed trailing data: {d.length - d.pos} bytes remaining")
        return _steal_ref(res)

    if PyObject_GetBuffer(data, &view, PyBUF_SIMPLE) != 0:
        raise TypeError(f"a bytes-like object is required, not '{type(data).__name__}'")
    try:
        d.data = <const unsigned char*>view.buf
        d.length = <size_t>view.len
        d.pos = 0
        d.depth = 0
        d.max_depth = max_depth
        d.ext_hook = <PyObject*>ext_hook if ext_hook is not None else NULL
        res = decode_obj(&d)
        if res == NULL:
            return None
        if d.pos != d.length:
            Py_DECREF(res)
            raise ValueError(f"Unconsumed trailing data: {d.length - d.pos} bytes remaining")
        return _steal_ref(res)
    finally:
        PyBuffer_Release(&view)
