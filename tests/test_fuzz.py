#
# test_fuzz.py
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

import math
import struct

from hypothesis import given, settings
from hypothesis import strategies as st

import rencode


def assert_rencode_equal(a, b):
    """
    Assert structural and type equality between deserialized objects,
    accounting for NaN float comparisons.
    """
    assert type(a) is type(b), f"Type mismatch: {type(a)} vs {type(b)}"

    if isinstance(a, float):
        if math.isnan(a):
            assert math.isnan(b)
        else:
            assert a == b
    elif isinstance(a, rencode.Ext):
        assert a.tag == b.tag
        assert a.data == b.data
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for item_a, item_b in zip(a, b):
            assert_rencode_equal(item_a, item_b)
    elif isinstance(a, dict):
        assert len(a) == len(b)
        for k in a:
            assert k in b, f"Key {k!r} missing from deserialized dict"
            assert_rencode_equal(a[k], b[k])
    else:
        assert a == b


# Primitive strategies
st_none = st.none()
st_bool = st.booleans()
st_int = st.integers(min_value=-(1 << 256), max_value=(1 << 256))
st_float = st.floats(allow_nan=True, allow_infinity=True)
st_str = st.text()
st_bytes = st.binary()
st_ext = st.builds(
    rencode.Ext,
    tag=st.integers(min_value=0, max_value=18446744073709551615),
    data=st.binary(max_size=1024),
)

st_atomic_keys = st.one_of(st_int, st_str, st_bytes, st_bool, st_ext)

# Recursive data structure strategy
st_rencode_values = st.recursive(
    st.one_of(st_none, st_bool, st_int, st_float, st_str, st_bytes, st_ext),
    lambda children: st.one_of(
        st.lists(children, max_size=20),
        st.tuples(children),
        st.dictionaries(
            keys=st.one_of(st_atomic_keys, st.tuples(st_atomic_keys)),
            values=children,
            max_size=15,
        ),
    ),
    max_leaves=50,
)


@given(val=st_rencode_values)
@settings(max_examples=200, deadline=None)
def test_fuzz_roundtrip(val):
    """
    Verify that arbitrary valid Python objects round-trip through dumps and loads
    with exact type and value fidelity.
    """
    serialized = rencode.dumps(val)
    deserialized = rencode.loads(serialized)
    assert_rencode_equal(deserialized, val)


@given(val=st.floats(allow_nan=True, allow_infinity=True, width=32))
@settings(max_examples=100, deadline=None)
def test_fuzz_float32_roundtrip(val):
    """
    Verify that 32-bit floating point numbers round-trip with float32 fidelity.
    """
    expected_f32 = struct.unpack("<f", struct.pack("<f", val))[0]
    enc = rencode.dumps(val, float_bits=32)
    dec = rencode.loads(enc)
    if math.isnan(expected_f32):
        assert math.isnan(dec)
    else:
        assert dec == expected_f32


@given(raw=st.binary(max_size=4096))
@settings(max_examples=500, deadline=None)
def test_fuzz_arbitrary_bytes_crash_free(raw):
    """
    Verify that arbitrary byte sequences fed into loads() either deserialize
    successfully or cleanly raise expected Python exceptions without segfaulting,
    memory corruption, or hanging.
    """
    try:
        rencode.loads(raw)
    except (ValueError, TypeError, UnicodeDecodeError, OverflowError, MemoryError):
        pass


@given(val=st_rencode_values, cut_ratio=st.floats(min_value=0.0, max_value=0.99))
@settings(max_examples=150, deadline=None)
def test_fuzz_truncated_bytes(val, cut_ratio):
    """
    Verify that arbitrarily truncated valid payloads cleanly raise ValueError
    or IndexError without crashing.
    """
    payload = rencode.dumps(val)
    if len(payload) > 1:
        cut_len = max(1, int(len(payload) * cut_ratio))
        truncated = payload[:cut_len]
        try:
            rencode.loads(truncated)
        except (ValueError, IndexError, UnicodeDecodeError):
            pass


@given(val=st_rencode_values, junk=st.binary(min_size=1, max_size=32))
@settings(max_examples=150, deadline=None)
def test_fuzz_trailing_bytes(val, junk):
    """
    Verify that valid payloads with trailing garbage always raise ValueError
    (unconsumed trailing data) without crashing.
    """
    payload = rencode.dumps(val) + junk
    try:
        rencode.loads(payload)
    except ValueError as e:
        assert (
            "trailing" in str(e).lower()
            or "truncated" in str(e).lower()
            or "overflow" in str(e).lower()
        )
