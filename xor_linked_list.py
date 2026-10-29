"""An XOR linked list of unsigned 32-bit values in a compact memory arena."""

from array import array
from operator import index


_ELEMENT_WORDS = 2
_LINK_WORD = 1
_NO_ADDRESS = (1 << 32) - 1
_ALIGNMENT_MASK = _ELEMENT_WORDS - 1


class XorLinkedList:
    # Addresses are word offsets, not Python object addresses.
    ELEMENT_SIZE = _ELEMENT_WORDS
    INITIAL_CAPACITY = 8
    MAX_CAPACITY = 1 << 16
    NOT_FOUND = _NO_ADDRESS
    MAX_VALUE = (1 << 32) - 1
    VALUE_OFFSET = 0
    LINK_OFFSET = _LINK_WORD

    __slots__ = ("buffer", "_storage", "size", "capacity", "first", "last")

    def __init__(self):
        self.size = 0
        self.capacity = self.INITIAL_CAPACITY
        self.first = self.last = self.NOT_FOUND
        storage = array("I", [0]) * (self.capacity * self.ELEMENT_SIZE)
        if storage.itemsize != 4:
            raise RuntimeError("This implementation requires 32-bit unsigned int storage.")
        self._storage = storage
        self.buffer = memoryview(storage)

    def __len__(self):
        return self.size

    @property
    def empty(self):
        return self.size == 0

    def check_address(self, address):
        if not isinstance(address, int) or isinstance(address, bool):
            raise IndexError("An address must be an integer word offset.")
        if address == self.NOT_FOUND:
            return
        if address < 0 or address % self.ELEMENT_SIZE or address >= self.size * self.ELEMENT_SIZE:
            raise IndexError("The address does not refer to an allocated element.")

    def ensure_capacity(self):
        if self.size >= self.MAX_CAPACITY:
            raise RuntimeError("The list has reached its maximum capacity.")
        if self.size < self.capacity:
            return
        capacity = min(self.capacity * 2, self.MAX_CAPACITY)
        expanded = array("I", [0]) * (capacity * self.ELEMENT_SIZE)
        expanded[:len(self._storage)] = self._storage
        self._storage = expanded
        self.buffer = memoryview(expanded)
        self.capacity = capacity

    def _grow_for_value(self, value):
        value = index(value)
        if not 0 <= value <= self.MAX_VALUE:
            raise OverflowError("Values must be unsigned 32-bit integers.")
        self.ensure_capacity()
        return value

    def _allocate(self, value, before, after):
        size = self.size
        if size >= self.capacity:
            value = self._grow_for_value(value)
        address = size * _ELEMENT_WORDS
        buffer = self._storage
        buffer[address] = value
        buffer[address + _LINK_WORD] = before ^ after
        self.size = size + 1
        return address

    def allocate(self, value, before, after):
        """Allocate storage only; insert_between also connects it to the list."""
        self.check_address(before)
        self.check_address(after)
        return self._allocate(value, before, after)

    def append(self, value):
        last = self.last
        address = self._allocate(value, last, _NO_ADDRESS)
        if last == _NO_ADDRESS:
            self.first = address
        else:
            self._storage[last + _LINK_WORD] ^= _NO_ADDRESS ^ address
        self.last = address
        return address

    def prepend(self, value):
        first = self.first
        address = self._allocate(value, _NO_ADDRESS, first)
        if first == _NO_ADDRESS:
            self.last = address
        else:
            self._storage[first + _LINK_WORD] ^= _NO_ADDRESS ^ address
        self.first = address
        return address

    def insert_between(self, value, before, after):
        """Insert between neighbors; a missing endpoint requests prepend/append."""
        if before == _NO_ADDRESS:
            return self.prepend(value)
        if after == _NO_ADDRESS:
            return self.append(value)
        size = self.size
        try:
            combined = before | after
        except TypeError:
            self.check_address(before)
            self.check_address(after)
            raise
        limit = size * _ELEMENT_WORDS
        # OR combines the sign and alignment checks for the two addresses.
        if (
            combined < 0
            or combined & _ALIGNMENT_MASK
            or before >= limit
            or after >= limit
            or before is False
            or after is False
        ):
            raise IndexError("The address does not refer to an allocated element.")
        if before == after:
            raise ValueError("Insertion requires two distinct neighbors.")
        if size >= self.capacity:
            value = self._grow_for_value(value)
        # Interior insertion has no endpoint work. Keep its writes together.
        address = size * _ELEMENT_WORDS
        buffer = self._storage
        buffer[address] = value
        buffer[address + _LINK_WORD] = before ^ after
        self.size = size + 1
        buffer[before + _LINK_WORD] ^= after ^ address
        buffer[after + _LINK_WORD] ^= before ^ address
        return address

    def __getitem__(self, address):
        self.check_address(address)
        if address == self.NOT_FOUND:
            raise IndexError("NOT_FOUND is not an element address.")
        return self.buffer[address + self.VALUE_OFFSET]

    def __iter__(self):
        before, current = self.NOT_FOUND, self.first
        while current != self.NOT_FOUND:
            after = self.buffer[current + self.LINK_OFFSET] ^ before
            yield self.buffer[current + self.VALUE_OFFSET]
            before, current = current, after

    def address(self, value):
        """Return the first matching address in the current traversal order."""
        before, current = self.NOT_FOUND, self.first
        while current != self.NOT_FOUND:
            if self.buffer[current + self.VALUE_OFFSET] == value:
                return current
            before, current = current, self.buffer[current + self.LINK_OFFSET] ^ before
        return self.NOT_FOUND

    def reverse(self):
        self.first, self.last = self.last, self.first
        return self
