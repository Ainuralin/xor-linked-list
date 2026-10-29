"""Run the supplied and additional tests, including deadlines on Windows."""

import argparse
import ast
from functools import wraps
from pathlib import Path
import signal
import sys
from time import perf_counter
import unittest

import test_extra
import test_xor_linked_list


def timed_check(function, seconds):
    @wraps(function)
    def check(self):
        start = perf_counter()
        result = function(self)
        elapsed = perf_counter() - start
        self.assertLessEqual(
            elapsed, seconds,
            f"{function.__name__} took {elapsed:.6f}s; limit is {seconds:.6f}s.",
        )
        return result
    return check


def use_portable_timers():
    """Read each existing timeout instead of changing or duplicating its value."""
    source = Path(test_xor_linked_list.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "timeout_decorator"
                and decorator.func.attr == "timeout"
            ):
                continue
            seconds = ast.literal_eval(decorator.args[0])
            test_class = test_xor_linked_list.TestXorLinkedList
            original = getattr(test_class, node.name).__wrapped__
            setattr(test_class, node.name, timed_check(original, seconds))
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--portable-timers", action="store_true",
        help="Use elapsed-time checks instead of Unix signals; deadlines stay unchanged.",
    )
    args = parser.parse_args()
    if args.portable_timers or not hasattr(signal, "SIGALRM"):
        count = use_portable_timers()
        print(f"Portable timers: {count} tests; original deadlines retained.", flush=True)
    else:
        print("Original Unix signal timers enabled.", flush=True)
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite([
        loader.loadTestsFromModule(test_xor_linked_list),
        loader.loadTestsFromModule(test_extra),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
