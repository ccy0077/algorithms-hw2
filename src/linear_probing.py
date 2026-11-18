"""A string-key hash table using linear probing."""


class _Entry:
    __slots__ = ("key", "value")

    def __init__(self, key, value):
        self.key = key
        self.value = value


class LinearProbingHashTable:
    def __init__(self, initial_capacity=8, auto_resize=True):
        if not isinstance(initial_capacity, int) or initial_capacity < 1:
            raise ValueError("initial_capacity must be a positive integer")
        self.capacity = initial_capacity
        self.auto_resize = auto_resize
        self.slots = [None] * self.capacity
        self._size = 0
        self.last_probe_count = 0

    def _hash(self, key):
        value = 0
        for character in key:
            value = (31 * value + ord(character)) % self.capacity
        return value

    def _find_slot(self, key):
        index = self._hash(key)
        for offset in range(self.capacity):
            slot_index = (index + offset) % self.capacity
            self.last_probe_count = offset + 1
            entry = self.slots[slot_index]
            if entry is None:
                return slot_index, False
            if entry.key == key:
                return slot_index, True
        return None, False

    def put(self, key, value):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        slot_index, found = self._find_slot(key)
        if found:
            self.slots[slot_index].value = value
            return

        if self.auto_resize and (self._size + 1) / self.capacity > 0.75:
            self._resize(self.capacity * 2)
            slot_index, _ = self._find_slot(key)

        if slot_index is None:
            raise OverflowError("hash table is full")

        self.slots[slot_index] = _Entry(key, value)
        self._size += 1

    def get(self, key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

        slot_index, found = self._find_slot(key)
        if found:
            return self.slots[slot_index].value
        raise KeyError(key)

    def _resize(self, new_capacity):
        old_slots = self.slots
        self.capacity = new_capacity
        self.slots = [None] * self.capacity
        self._size = 0
        for entry in old_slots:
            if entry is None:
                continue
            slot_index, _ = self._find_slot(entry.key)
            self.slots[slot_index] = entry
            self._size += 1

    def __len__(self):
        return self._size
