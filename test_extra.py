"""Additional behavior and storage checks for the XOR list."""

import random
import unittest
from unittest.mock import patch

from xor_linked_list import XorLinkedList


class ExtraTests(unittest.TestCase):
    def test_append_and_prepend_after_reverse(self):
        linked = XorLinkedList()
        addresses = [linked.append(value) for value in [10, 20, 30]]
        linked.reverse()
        linked.append(0)
        linked.prepend(40)
        self.assertEqual(list(linked), [40, 30, 20, 10, 0])
        self.assertEqual([linked[a] for a in addresses], [10, 20, 30])

    def test_insert_after_reverse(self):
        linked = XorLinkedList()
        a, b = linked.append(1), linked.append(3)
        linked.reverse()
        inserted = linked.insert_between(2, b, a)
        self.assertEqual(list(linked), [3, 2, 1])
        self.assertEqual(linked[inserted], 2)

    def test_growth_preserves_addresses_and_xor_links(self):
        linked = XorLinkedList()
        addresses = [linked.append(value) for value in range(200)]
        self.assertEqual(list(linked), list(range(200)))
        self.assertEqual([linked[a] for a in addresses], list(range(200)))
        sentinel = linked.NOT_FOUND
        for i, address in enumerate(addresses):
            before = addresses[i - 1] if i else sentinel
            after = addresses[i + 1] if i + 1 < len(addresses) else sentinel
            self.assertEqual(linked.buffer[address + linked.LINK_OFFSET], before ^ after)
        linked.reverse()
        self.assertEqual(list(linked), list(reversed(range(200))))

    def test_duplicate_search_follows_reversed_order(self):
        linked = XorLinkedList()
        first = linked.append(42)
        linked.append(7)
        last = linked.append(42)
        self.assertEqual(linked.address(42), first)
        linked.reverse()
        self.assertEqual(linked.address(42), last)

    def test_failed_value_insertion_leaves_list_unchanged(self):
        linked = XorLinkedList()
        linked.append(42)
        for value, exception in [(-1, OverflowError), (1 << 32, OverflowError), (1.5, TypeError), ("7", TypeError)]:
            with self.subTest(value=value):
                with self.assertRaises(exception):
                    linked.prepend(value)
                self.assertEqual(list(linked), [42])
                self.assertEqual(len(linked), 1)

    def test_invalid_addresses_and_sentinel_read(self):
        linked = XorLinkedList()
        linked.append(42)
        for address in [-2, 1, 2, 0.0, True, None, linked.NOT_FOUND]:
            with self.subTest(address=address), self.assertRaises(IndexError):
                linked[address]
        linked.check_address(linked.NOT_FOUND)

    def test_boundary_sentinel_selects_the_current_list_end(self):
        linked = XorLinkedList()
        a, b = linked.append(1), linked.append(2)
        linked.insert_between(0, linked.NOT_FOUND, b)
        linked.insert_between(3, a, linked.NOT_FOUND)
        self.assertEqual(list(linked), [0, 1, 2, 3])

    def test_invalid_interior_insertion_is_atomic(self):
        linked = XorLinkedList()
        a, b = linked.append(1), linked.append(2)
        for before, after in [(a, a), (a, 1), (100, b), (-2, b), (a, -2), (float(a), b), (a, True)]:
            exception = ValueError if before == after else IndexError
            with self.subTest(neighbors=(before, after)), self.assertRaises(exception):
                linked.insert_between(0, before, after)
            self.assertEqual(list(linked), [1, 2])

    def test_bad_value_at_full_capacity_does_not_grow_the_buffer(self):
        with patch.object(XorLinkedList, "INITIAL_CAPACITY", 2):
            linked = XorLinkedList()
            a, b = linked.append(1), linked.append(2)
            original = linked.buffer.tobytes()
            for value, exception in [(-1, OverflowError), (1 << 32, OverflowError), (1.5, TypeError), ("7", TypeError)]:
                with self.subTest(value=value), self.assertRaises(exception):
                    linked.insert_between(value, a, b)
                self.assertEqual(linked.capacity, 2)
                self.assertEqual(linked.buffer.tobytes(), original)
                self.assertEqual(list(linked), [1, 2])
            linked.insert_between(3, a, b)
            self.assertEqual(linked.capacity, 4)
            self.assertEqual(list(linked), [1, 3, 2])

    def test_overflow_preserves_existing_elements(self):
        with patch.object(XorLinkedList, "INITIAL_CAPACITY", 2), patch.object(XorLinkedList, "MAX_CAPACITY", 4):
            linked = XorLinkedList()
            for value in range(4):
                linked.append(value)
            with self.assertRaises(RuntimeError):
                linked.prepend(5)
            self.assertEqual(list(linked), [0, 1, 2, 3])
            self.assertEqual(len(linked), 4)
            self.assertEqual(linked.capacity, 4)

    def test_instances_have_independent_buffers(self):
        a, b = XorLinkedList(), XorLinkedList()
        a.append(42)
        b.prepend(7)
        a.reverse()
        self.assertEqual(list(a), [42])
        self.assertEqual(list(b), [7])

    def test_mixed_operations_match_python_list(self):
        rng = random.Random(42)
        linked, expected, addresses = XorLinkedList(), [], []
        for _ in range(500):
            operation = rng.choice(["append", "prepend", "insert", "reverse"])
            value = rng.randrange(1 << 32)
            if operation == "reverse":
                linked.reverse()
                expected.reverse()
                addresses.reverse()
            else:
                position = len(expected) if operation == "append" else 0 if operation == "prepend" else rng.randrange(len(expected) + 1)
                before = addresses[position - 1] if position else linked.NOT_FOUND
                after = addresses[position] if position < len(addresses) else linked.NOT_FOUND
                if operation == "append":
                    address = linked.append(value)
                elif operation == "prepend":
                    address = linked.prepend(value)
                else:
                    address = linked.insert_between(value, before, after)
                expected.insert(position, value)
                addresses.insert(position, address)
            self.assertEqual(list(linked), expected)
            self.assertEqual(len(linked), len(expected))


if __name__ == "__main__":
    unittest.main()
