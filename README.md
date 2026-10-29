# XOR Linked List

Python implementation for the Itransition practice exercise on data structures and unit testing.

Each node uses two unsigned 32-bit words: its value and the XOR of its neighbors' addresses. Nodes live in a contiguous buffer. An address is a word offset in that buffer, not an actual pointer to a Python object.

## Run the tests

Use CPython 3.10 or newer. The list itself uses only the standard library. The supplied tests also require `forbiddenfruit` and `timeout-decorator`.

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run_tests.py
```

Linux / WSL:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v test_xor_linked_list test_extra
```

The expected result is **72 tests, OK**: 60 supplied tests and 12 additional tests.

The supplied test file is unchanged. Four original tests use a 0.01-second `SIGALRM` timeout, which is available on Unix. On Windows, `run_tests.py` reads those same limits and checks elapsed wall-clock time with `perf_counter`. It runs the same test bodies and retains every assertion and deadline. The portable check reports a late completion after the test returns; unlike a Unix alarm, it cannot interrupt a stuck test. Linux uses the original signal timers by default. The portable path can also be checked with `python run_tests.py --portable-timers`.

The timing limits are very short and include the whole test body. A busy machine, debugger, tracing or coverage can affect their results. The limits have not been increased or disabled.

## Example

```python
from xor_linked_list import XorLinkedList

items = XorLinkedList()
first = items.append(10)
last = items.append(30)
middle = items.insert_between(20, first, last)

print(list(items))                 # [10, 20, 30]
print(items[middle])               # 20
print(list(items.reverse()))       # [30, 20, 10]
items.append(0)
print(list(items))                 # [30, 20, 10, 0]
```

## Storage and operations

- `buffer` is a `memoryview` over an `array('I')`. Each node occupies 8 bytes: a 4-byte value and a 4-byte XOR link. This does not include the fixed Python object overhead.
- Node addresses are 0, 2, 4, ... . Zero is a valid address. `NOT_FOUND = 0xFFFFFFFF` represents a missing neighbor.
- Traversal keeps the previous address and recovers the next with `stored_link ^ previous`.
- Reversal swaps `first` and `last`; it does not visit nodes or rewrite links.
- Capacity starts at 8 nodes and doubles when needed. Growing copies the buffer, so the numeric addresses remain valid. A separately retained old `buffer` view does not follow a later reallocation.
- The bounded arena supports up to 65,536 nodes (512 KiB of node storage at full capacity). `MAX_CAPACITY` defines this exercise's allocation limit; an overflow raises `RuntimeError` without changing existing nodes.

`append`, `prepend` and `insert_between` return an address. `items[address]` reads the value at that address, not at a logical list index. `address(value)` returns the first match in the current traversal order or `NOT_FOUND`.

For an interior `insert_between`, callers must supply two adjacent nodes in the current traversal order. Reversing changes that order. Checking arbitrary interior adjacency would require traversal, so this is a caller precondition. Address validity and identical neighbors are checked.

A `NOT_FOUND` predecessor requests insertion at the current beginning; otherwise a `NOT_FOUND` successor requests insertion at the current end. The other argument is not used in these boundary cases. This also supports the nested insertion scenario in the supplied tests.

`allocate(value, before, after)` is the low-level storage helper exposed for the supplied tests. It writes a node and increases `size`, but does not connect the neighbors or update the endpoints. Use the insertion methods to construct a traversable list. Do not modify a list during iteration or write directly to its buffer.

| Operation | Time |
| --- | --- |
| Size, empty, value by address, reverse | O(1) |
| Append, prepend, insertion between supplied neighbors | Amortized O(1); O(n) when the buffer grows |
| Search by value, full traversal | O(n) |

## Additional tests

`test_extra.py` checks insertion after reversal, stable addresses and actual XOR links after buffer growth, duplicate search in reversed order, boundary insertion, failed operations without partial mutation, invalid values at full capacity, capacity exhaustion, independent instances, and 500 deterministic mixed operations compared with a regular Python list.
