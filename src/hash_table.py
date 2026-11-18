"""A string-key hash table using separate chaining."""


class _Node:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_node=None):
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    def __init__(self, initial_capacity=8, auto_resize=True):
        if not isinstance(initial_capacity, int) or initial_capacity < 1:
            raise ValueError("initial_capacity must be a positive integer")
        self.capacity = initial_capacity
        self.auto_resize = auto_resize
        self.buckets = [None] * self.capacity
        self._size = 0

    def _hash(self, key):
        value = 0
        for character in key:
            value = (31 * value + ord(character)) % self.capacity
        return value

    def put(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._hash(key)
        node = self.buckets[index]
        while node is not None:
            if node.key == key:
                node.value = value
                return
            node = node.next

        self.buckets[index] = _Node(key, value, self.buckets[index])
        self._size += 1
        if self.auto_resize and self._size / self.capacity > 0.75:
            self._resize(self.capacity * 2)

    def get(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        index = self._hash(key)
        node = self.buckets[index]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        raise KeyError(key)

    def _resize(self, new_capacity):
        old_buckets = self.buckets
        self.capacity = new_capacity
        self.buckets = [None] * self.capacity
        for head in old_buckets:
            node = head
            while node is not None:
                index = self._hash(node.key)
                self.buckets[index] = _Node(
                    node.key,
                    node.value,
                    self.buckets[index],
                )
                node = node.next

    def __len__(self):
        return self._size
