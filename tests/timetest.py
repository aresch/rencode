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
import timeit
import argparse
import functools
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class TestCase:
    name: str
    data: Any
    scale_factor: float = 1.0


# Complex test data structures
def create_nested_structure(depth=5):
    """Create a deeply nested structure with mixed types."""
    if depth == 0:
        return [1, 2.5, "leaf", True, None]
    return {
        "list": [1, 2.5, "string", True, None],
        "dict": {"key": "value", "num": 42},
        "nested": create_nested_structure(depth - 1),
    }


def create_large_mixed_collection():
    """Create a large collection with mixed types."""
    return {
        "numbers": [i for i in range(1000)],
        "floats": [i * 1.5 for i in range(1000)],
        "strings": [f"string_{i}" for i in range(1000)],
        "booleans": [True if i % 2 == 0 else False for i in range(1000)],
        "none_values": [None] * 1000,
        "mixed": [
            i if i % 3 == 0 else f"str_{i}" if i % 3 == 1 else i * 1.5
            for i in range(1000)
        ],
    }


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
            b"inner_bytes": "inner_bytes_value",
        },
    }


def create_large_string_data():
    """Create large string data with various patterns."""
    return {
        "repeated": "a" * 10000,
        "pattern": "abc" * 1000,
        "unicode": "你好世界" * 1000,
        "mixed": "".join(chr(i % 256) for i in range(10000)),
        "lines": "\n".join(f"Line {i}" for i in range(1000)),
    }


def create_mixed_numeric_collection():
    """Create a collection with various numeric types."""
    return {
        "integers": [i for i in range(-1000, 1000)],
        "floats": [i * 1.5 for i in range(-1000, 1000)],
        "mixed": [i if i % 2 == 0 else i * 1.5 for i in range(-1000, 1000)],
        "large": [2**i for i in range(10)],
        "small": [2**-i for i in range(10)],
        "zero": [0, 0.0, -0.0],
        "infinity": [float("inf"), float("-inf")],
        "nan": [float("nan")],
        "precision": [1.23456789, -1.23456789, 0.00000001, -0.00000001],
    }


# Create test data
nested_data = create_nested_structure()
large_mixed_data = create_large_mixed_collection()
complex_dict_data = create_complex_dict()
large_string_data = create_large_string_data()
mixed_numeric_data = create_mixed_numeric_collection()

# Small test cases
SMALL_TESTS = [
    # Fixed positive integers
    TestCase("fixed_pos_int", 40),
    TestCase("fixed_neg_int", -29),
    TestCase("int_char_size", 100),
    TestCase("int_short_size", 27123),
    TestCase("int_int_size", 7483648),
    TestCase("int_long_long_size", 8223372036854775808),
    TestCase("float_32bit", 1234.56),
    TestCase("float_64bit", 1234.56),
    TestCase("fixed_str", b"foobarbaz"),
    TestCase("str", b"f" * 255),
    TestCase("none", None),
    TestCase("bool", True),
    TestCase("fixed_list", [None] * 4),
    TestCase("list", [None] * 80),
    TestCase("fixed_dict", dict(zip(b"abcdefghijk", [None] * 11))),
    TestCase("dict", dict(zip(b"abcdefghijklmnopqrstuvwxyz1234567890", [None] * 36))),
]

# Large test cases
LARGE_TESTS = [
    TestCase("large_mixed_collection", large_mixed_data, 0.01),
    TestCase("nested_structure", nested_data, 0.01),
    TestCase("complex_dict", complex_dict_data, 0.01),
    TestCase("large_string_data", large_string_data, 0.01),
    TestCase("mixed_numeric_collection", mixed_numeric_data, 0.01),
]


def create_test_functions(test_case: TestCase, use_orig: bool) -> Dict[str, Callable]:
    """Create encode and decode test functions for the given test case."""
    test_functions = {}

    # Create encode test
    def encode_test():
        if use_orig:
            rencode_orig.dumps(test_case.data)
        else:
            rencode.dumps(test_case.data)

    encode_test.is_large_test = test_case.scale_factor != 1.0
    encode_test.scale_factor = test_case.scale_factor
    encode_test.__name__ = f"test_encode_{test_case.name}"
    if use_orig:
        encode_test.__name__ += "_orig"
    test_functions["encode"] = encode_test

    # Pre-encode the data for decode test
    encoded_data = (
        rencode_orig.dumps(test_case.data)
        if use_orig
        else rencode.dumps(test_case.data)
    )

    # Create decode test
    def decode_test():
        if use_orig:
            rencode_orig.loads(encoded_data)
        else:
            rencode.loads(encoded_data)

    decode_test.is_large_test = test_case.scale_factor != 1.0
    decode_test.scale_factor = test_case.scale_factor
    decode_test.__name__ = f"test_decode_{test_case.name}"
    if use_orig:
        decode_test.__name__ += "_orig"
    test_functions["decode"] = decode_test

    return test_functions


def get_test_functions(use_orig: bool) -> Dict[str, List[Callable]]:
    """Get all test functions organized by category."""
    test_functions = {"encode": [], "decode": []}

    # Add small tests
    for test_case in SMALL_TESTS:
        funcs = create_test_functions(test_case, use_orig)
        test_functions["encode"].append(funcs["encode"])
        test_functions["decode"].append(funcs["decode"])

    # Add large tests
    for test_case in LARGE_TESTS:
        funcs = create_test_functions(test_case, use_orig)
        test_functions["encode"].append(funcs["encode"])
        test_functions["decode"].append(funcs["decode"])

    return test_functions


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


# Pre-encode the test data for decode tests
nested_data_str = rencode_orig.dumps(nested_data)
large_mixed_data_str = rencode_orig.dumps(large_mixed_data)
complex_dict_data_str = rencode_orig.dumps(complex_dict_data)
large_string_data_str = rencode_orig.dumps(large_string_data)
mixed_numeric_data_str = rencode_orig.dumps(mixed_numeric_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run rencode performance tests")
    parser.add_argument("--save", help="Save results to specified file")
    parser.add_argument("--compare", help="Compare against results from specified file")
    parser.add_argument(
        "--iterations", type=int, default=1000000, help="Number of iterations per test"
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
        print("%s:" % func.__name__)
        # Calculate iterations based on whether it's a large test
        test_iterations = iterations
        if hasattr(func, "is_large_test") and func.is_large_test:
            test_iterations = int(iterations * func.scale_factor)
            print(f"\tUsing {test_iterations} iterations (scaled from {iterations})")

        time = timeit.Timer(func).timeit(test_iterations)
        print("\t%.3fs" % time)
        return time

    results = {}
    total_time = 0.0

    # Get test functions
    test_functions = get_test_functions(args.use_orig)

    # Filter tests if specific tests are requested
    if args.tests:
        for category in test_functions:
            test_functions[category] = [
                f for f in test_functions[category] if f.__name__ in args.tests
            ]

    for category, funcs in test_functions.items():
        print("*" * 79)
        print("%s functions:" % (category.title()))
        print("*" * 79)
        print("")

        category_time = 0.0
        category_results = {}

        for func in funcs:
            time = do_test(func)
            category_time += time
            total_time += time
            category_results[func.__name__] = time

        results[category] = category_results

        print("%s functions total: %.3fs" % (category.title(), category_time))
        print("")

    print("*" * 79)
    print("Total time: %.3fs" % total_time)
    print("*" * 79)
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
