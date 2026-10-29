"""A short example of insertion, address lookup and reversal."""

from xor_linked_list import XorLinkedList


def main():
    items = XorLinkedList()
    first = items.append(10)
    last = items.append(30)
    middle = items.insert_between(20, first, last)
    print("After insertion:", list(items))
    print("Value at the returned address:", items[middle])
    items.reverse()
    print("After reversal:", list(items))
    items.append(0)
    items.prepend(40)
    print("After adding to both ends:", list(items))
    print("Size:", len(items))
    print("Node storage (bytes):", items.buffer.nbytes)


if __name__ == "__main__":
    main()
