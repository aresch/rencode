# -*- coding: utf-8 -*-
#
# timetest.py
#
# Copyright (C) 2025 Andrew Resch <andrewresch@gmail.com>
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

from rencode import _rencode as rencode
from rencode import rencode_orig
import sys
import json
import os
from datetime import datetime
import platform

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


bn = int("9" * 62)


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
    rencode.dumps(b"foobarbaz")


def test_encode_fixed_str_orig():
    rencode_orig.dumps(b"foobarbaz")


s = b"f" * 255


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


ll = [None] * 80


def test_encode_list():
    rencode.dumps(ll)


def test_encode_list_orig():
    rencode_orig.dumps(ll)


keys = b"abcdefghijk"
d = dict(zip(keys, [None] * len(keys)))


def test_encode_fixed_dict():
    rencode.dumps(d)


def test_encode_fixed_dict_orig():
    rencode_orig.dumps(d)


keys2 = b"abcdefghijklmnopqrstuvwxyz1234567890"
d2 = dict(zip(keys2, [None] * len(keys2)))


def test_encode_dict():
    rencode.dumps(d2)


def test_encode_dict_orig():
    rencode_orig.dumps(d2)


# Decode functions


def test_decode_fixed_pos_int():
    rencode.loads(b"(")


def test_decode_fixed_pos_int_orig():
    rencode_orig.loads(b"(")


def test_decode_fixed_neg_int():
    rencode.loads(b"b")


def test_decode_fixed_neg_int_orig():
    rencode_orig.loads(b"b")


def test_decode_int_char_size():
    rencode.loads(b">d")
    rencode.loads(b">\x9c")


def test_decode_int_char_size_orig():
    rencode_orig.loads(b">d")
    rencode_orig.loads(b">\x9c")


def test_decode_int_short_size():
    rencode.loads(b"?i\xf3")
    rencode.loads(b"?\x96\r")


def test_decode_int_short_size_orig():
    rencode_orig.loads(b"?i\xf3")
    rencode_orig.loads(b"?\x96\r")


def test_decode_int_int_size():
    rencode.loads(b"@\x00r1\x00")
    rencode.loads(b"@\xff\x8d\xcf\x00")


def test_decode_int_int_size_orig():
    rencode_orig.loads(b"@\x00r1\x00")
    rencode_orig.loads(b"@\xff\x8d\xcf\x00")


def test_decode_int_long_long_size():
    rencode.loads(b"Ar\x1fILX\x9c\x00\x00")
    rencode.loads(b"A\x8d\xe0\xb6\xb3\xa7d\x00\x00")


def test_decode_int_long_long_size_orig():
    rencode_orig.loads(b"Ar\x1fILX\x9c\x00\x00")
    rencode_orig.loads(b"A\x8d\xe0\xb6\xb3\xa7d\x00\x00")


def test_decode_int_big_number():
    rencode.loads(
        b"=99999999999999999999999999999999999999999999999999999999999999\x7f"
    )


def test_decode_int_big_number_orig():
    rencode_orig.loads(
        b"=99999999999999999999999999999999999999999999999999999999999999\x7f"
    )


def test_decode_float_32bit():
    rencode.loads(b"BD\x9aQ\xec")


def test_decode_float_32bit_orig():
    rencode_orig.loads(b"BD\x9aQ\xec")


def test_decode_float_64bit():
    rencode.loads(b",@\x93J=p\xa3\xd7\n")


def test_decode_float_64bit_orig():
    rencode_orig.loads(b",@\x93J=p\xa3\xd7\n")


def test_decode_fixed_str():
    rencode.loads(b"\x89foobarbaz")


def test_decode_fixed_str_orig():
    rencode_orig.loads(b"\x89foobarbaz")


def test_decode_str():
    rencode.loads(
        b"255:fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )


def test_decode_str_orig():
    rencode_orig.loads(
        b"255:fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )


def test_decode_none():
    rencode.loads(b"E")


def test_decode_none_orig():
    rencode_orig.loads(b"E")


def test_decode_bool():
    rencode.loads(b"C")


def test_decode_bool_orig():
    rencode_orig.loads(b"C")


def test_decode_fixed_list():
    rencode.loads(b"\xc4EEEE")


def test_decode_fixed_list_orig():
    rencode_orig.loads(b"\xc4EEEE")


def test_decode_list():
    rencode.loads(
        b";EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\x7f"
    )


def test_decode_list_orig():
    rencode_orig.loads(
        b";EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE\x7f"
    )


def test_decode_fixed_dict():
    rencode.loads(
        b"q\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE"
    )


def test_decode_fixed_dict_orig():
    rencode_orig.loads(
        b"q\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE"
    )


def test_decode_dict():
    rencode.loads(
        b"<\x811E\x810E\x813E\x812E\x815E\x814E\x817E\x816E\x819E\x818E\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE\x81mE\x81lE\x81oE\x81nE\x81qE\x81pE\x81sE\x81rE\x81uE\x81tE\x81wE\x81vE\x81yE\x81xE\x81zE\x7f"
    )


def test_decode_dict_orig():
    rencode_orig.loads(
        b"<\x811E\x810E\x813E\x812E\x815E\x814E\x817E\x816E\x819E\x818E\x81aE\x81cE\x81bE\x81eE\x81dE\x81gE\x81fE\x81iE\x81hE\x81kE\x81jE\x81mE\x81lE\x81oE\x81nE\x81qE\x81pE\x81sE\x81rE\x81uE\x81tE\x81wE\x81vE\x81yE\x81xE\x81zE\x7f"
    )


overall = [
    b"5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6",
    b"fixedlength",
    "unicodestring",
    "5ce750f0954ce1537676c7a5fe38b0de30ba7eb65ce750f0954ce1537676c7a5fe38b0de30ba7eb6",
    -10,
    10,
    120,
    15600,
    -15600,
    7483648,
    -7483648,
    8223372036854775808,
    -8223372036854775808,
    int("9" * 62),
    1227688834.643409,
    None,
    True,
]


def test_overall_encode():
    rencode.dumps(overall)


def test_overall_encode_orig():
    rencode_orig.dumps(overall)


overall_decode_str = rencode_orig.dumps(overall)


def test_overall_decode():
    rencode.loads(overall_decode_str)


def test_overall_decode_orig():
    rencode_orig.loads(overall_decode_str)


def get_version_info():
    """Get version information for both implementations."""
    try:
        cython_version = rencode.__version__
    except AttributeError:
        cython_version = "unknown"

    try:
        python_version = rencode_orig.__version__
    except AttributeError:
        python_version = "unknown"

    def convert_version(version):
        return ".".join(map(str, version[1:]))

    return {
        "cython": convert_version(cython_version),
        "python": convert_version(python_version),
    }


def save_results(results, filename, use_orig, iterations):
    """Save test results to a JSON file."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "implementation": "python" if use_orig else "cython",
        "versions": get_version_info(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "iterations": iterations,
        "results": results,
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_results(filename):
    """Load test results from a JSON file."""
    with open(filename, "r") as f:
        return json.load(f)


# Complex test data structures
def create_nested_structure(depth=5):
    """Create a deeply nested structure with mixed types."""
    if depth == 0:
        return [1, 2.5, "leaf", True, None]
    return {
        "list": [1, 2.5, "string", True, None],
        "dict": {"key": "value", "num": 42},
        "nested": create_nested_structure(depth - 1)
    }

nested_data = create_nested_structure()

def create_large_mixed_collection():
    """Create a large collection with mixed types."""
    return {
        "numbers": [i for i in range(1000)],
        "floats": [i * 1.5 for i in range(1000)],
        "strings": [f"string_{i}" for i in range(1000)],
        "booleans": [True if i % 2 == 0 else False for i in range(1000)],
        "none_values": [None] * 1000,
        "mixed": [i if i % 3 == 0 else f"str_{i}" if i % 3 == 1 else i * 1.5 for i in range(1000)]
    }

large_mixed_data = create_large_mixed_collection()

def create_complex_dict():
    """Create a complex dictionary with various key types."""
    return {
        "string_key": "value",
        42: "numeric_key",
        (1, 2, 3): "tuple_key",
        True: "boolean_key",
        None: "none_key",
        b"bytes_key": "bytes_value",
        -42: "negative_numeric_key",
        0: "zero_key",
        "nested": {
            "inner_string": "inner_value",
            123: "inner_numeric",
            (4, 5, 6): "inner_tuple",
            False: "inner_boolean",
            b"inner_bytes": "inner_bytes_value"
        }
    }

complex_dict_data = create_complex_dict()

def create_large_string_data():
    """Create large string data with various patterns."""
    return {
        "repeated": "a" * 10000,
        "pattern": "abc" * 1000,
        "unicode": "你好世界" * 1000,
        "mixed": "".join(chr(i % 256) for i in range(10000)),
        "lines": "\n".join(f"Line {i}" for i in range(1000))
    }

large_string_data = create_large_string_data()

def create_mixed_numeric_collection():
    """Create a collection with various numeric types."""
    return {
        "integers": [i for i in range(-1000, 1000)],
        "floats": [i * 1.5 for i in range(-1000, 1000)],
        "mixed": [i if i % 2 == 0 else i * 1.5 for i in range(-1000, 1000)],
        "large": [2**i for i in range(10)],
        "small": [2**-i for i in range(10)],
        "zero": [0, 0.0, -0.0],
        "infinity": [float('inf'), float('-inf')],
        "nan": [float('nan')],
        "precision": [1.23456789, -1.23456789, 0.00000001, -0.00000001]
    }

mixed_numeric_data = create_mixed_numeric_collection()

# Test functions for complex structures
def test_encode_nested_structure():
    rencode.dumps(nested_data)

def test_encode_nested_structure_orig():
    rencode_orig.dumps(nested_data)

def test_encode_large_mixed_collection():
    rencode.dumps(large_mixed_data)

def test_encode_large_mixed_collection_orig():
    rencode_orig.dumps(large_mixed_data)

def test_encode_complex_dict():
    rencode.dumps(complex_dict_data)

def test_encode_complex_dict_orig():
    rencode_orig.dumps(complex_dict_data)

def test_encode_large_string_data():
    rencode.dumps(large_string_data)

def test_encode_large_string_data_orig():
    rencode_orig.dumps(large_string_data)

def test_encode_mixed_numeric_collection():
    rencode.dumps(mixed_numeric_data)

def test_encode_mixed_numeric_collection_orig():
    rencode_orig.dumps(mixed_numeric_data)

# Pre-encode the test data for decode tests
nested_data_str = rencode_orig.dumps(nested_data)
large_mixed_data_str = rencode_orig.dumps(large_mixed_data)
complex_dict_data_str = rencode_orig.dumps(complex_dict_data)
large_string_data_str = rencode_orig.dumps(large_string_data)
mixed_numeric_data_str = rencode_orig.dumps(mixed_numeric_data)

def test_decode_nested_structure():
    rencode.loads(nested_data_str)

def test_decode_nested_structure_orig():
    rencode_orig.loads(nested_data_str)

def test_decode_large_mixed_collection():
    rencode.loads(large_mixed_data_str)

def test_decode_large_mixed_collection_orig():
    rencode_orig.loads(large_mixed_data_str)

def test_decode_complex_dict():
    rencode.loads(complex_dict_data_str)

def test_decode_complex_dict_orig():
    rencode_orig.loads(complex_dict_data_str)

def test_decode_large_string_data():
    rencode.loads(large_string_data_str)

def test_decode_large_string_data_orig():
    rencode_orig.loads(large_string_data_str)

def test_decode_mixed_numeric_collection():
    rencode.loads(mixed_numeric_data_str)

def test_decode_mixed_numeric_collection_orig():
    rencode_orig.loads(mixed_numeric_data_str)

if __name__ == "__main__":
    import timeit
    import argparse

    parser = argparse.ArgumentParser(description="Run rencode performance tests")
    parser.add_argument("--save", help="Save results to specified file")
    parser.add_argument("--compare", help="Compare against results from specified file")
    parser.add_argument(
        "--iterations", type=int, default=10000, help="Number of iterations per test"
    )
    parser.add_argument(
        "--use-orig", action="store_true", help="Use rencode_orig instead of rencode"
    )
    parser.add_argument("tests", nargs="*", help="Specific tests to run (default: all)")
    args = parser.parse_args()

    iterations = args.iterations
    old_results = None

    # Load comparison data early if specified
    if args.compare:
        try:
            old_results = load_results(args.compare)
            old_iterations = old_results.get("iterations", iterations)

            # If iterations differ, adjust current run
            if old_iterations != iterations:
                print(f"\nWarning: Iteration count mismatch!")
                print(f"Current: {iterations} iterations")
                print(f"Previous: {old_iterations} iterations")
                print("Adjusting current run to match previous iterations...")
                iterations = old_iterations
        except FileNotFoundError:
            print(f"Error: Comparison file {args.compare} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in comparison file {args.compare}")
            sys.exit(1)

    # ANSI escape codes
    CSI = "\x1b["
    reset = CSI + "m"

    def do_test(func):
        print("%s:" % func)
        time = timeit.Timer("%s()" % func, "from __main__ import %s" % func).timeit(
            iterations
        )
        print("\t%.3fs" % time)
        return time

    results = {}

    if args.tests:
        test_funcs = args.tests
    else:
        loc = list(locals().keys())
        if args.use_orig:
            test_funcs = [
                f for f in loc if f.startswith("test_") and f.endswith("_orig")
            ]
        else:
            test_funcs = [
                f for f in loc if f.startswith("test_") and not f.endswith("_orig")
            ]

    for t in ("encode", "decode", "overall"):
        print("*" * 79)
        print("%s functions:" % (t.title()))
        print("*" * 79)
        print("")

        total_time = 0.0
        category_results = {}

        for func in test_funcs:
            if func.startswith("test_%s" % t):
                time = do_test(func)
                total_time += time
                # Strip _orig from the function name when saving results
                result_name = func.removesuffix("_orig") if args.use_orig else func
                category_results[result_name] = time

        results[t] = category_results

        print("%s functions total: %.3fs" % (t.title(), total_time))
        print("")

    if args.save:
        save_results(results, args.save, args.use_orig, iterations)
        print(f"Results saved to {args.save}")

    if args.compare and old_results:
        print(f"\nComparing with {args.compare}:")
        print("*" * 79)

        # Print version information
        print("\nVersion Information:")
        print("-" * 40)
        current_impl = "python" if args.use_orig else "cython"
        current_versions = get_version_info()
        old_impl = old_results.get("implementation", "unknown")
        old_versions = old_results.get("versions", {})

        print(
            f"Current: {current_impl} {current_versions.get(current_impl, 'unknown')}"
        )
        print(f"Previous: {old_impl} {old_versions.get(old_impl, 'unknown')}")
        print("\nPlatform Information:")
        print(
            f"Current: {platform.system()} {platform.release()} ({platform.machine()})"
        )
        print(
            f"Previous: {old_results.get('platform', {}).get('system', 'unknown')} "
            f"{old_results.get('platform', {}).get('release', 'unknown')} "
            f"({old_results.get('platform', {}).get('machine', 'unknown')})"
        )
        print(f"\nIterations: {iterations}")
        print("\nResults Comparison:")
        print("-" * 79)
        print(
            f"{'Test Name':<40} {'Current':>10} {'Previous':>10} {'Diff':>10} {'%':>8} {'Speed':>8}"
        )
        print("-" * 79)

        old_results_data = old_results.get("results", {})
        for category in results:
            if category in old_results_data:
                print(f"\n{category.title()} functions:")
                print("-" * 79)
                for test in results[category]:
                    if test in old_results_data[category]:
                        old_time = old_results_data[category][test]
                        new_time = results[category][test]
                        diff = new_time - old_time
                        percent = (new_time / old_time) * 100
                        speed_ratio = old_time / new_time

                        # Format the test name to be more readable
                        test_name = test.removeprefix("test_")

                        if new_time > old_time:
                            print(
                                f"{test_name:<40} {CSI}31m{new_time:>10.3f}s{reset} {CSI}32m{old_time:>10.3f}s{reset} {CSI}34m+{diff:>9.3f}s{reset} {CSI}31m{percent:>7.1f}%{reset} {CSI}31m{speed_ratio:>7.1f}x{reset}"
                            )
                        else:
                            print(
                                f"{test_name:<40} {CSI}32m{new_time:>10.3f}s{reset} {CSI}31m{old_time:>10.3f}s{reset} {CSI}34m-{abs(diff):>9.3f}s{reset} {CSI}32m{percent:>7.1f}%{reset} {CSI}32m{speed_ratio:>7.1f}x{reset}"
                            )
