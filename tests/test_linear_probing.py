import unittest

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class LinearProbingHashTableTests(unittest.TestCase):
    def test_put_get_and_len(self):
        table = LinearProbingHashTable(initial_capacity=8, auto_resize=False)

        table.put("alpha", 1)
        table.put("beta", 2)

        self.assertEqual(table.get("alpha"), 1)
        self.assertEqual(table.get("beta"), 2)
        self.assertEqual(len(table), 2)

    def test_duplicate_key_updates_value_without_increasing_length(self):
        table = LinearProbingHashTable(initial_capacity=8, auto_resize=False)
        table.put("key", "old")

        table.put("key", "new")

        self.assertEqual(table.get("key"), "new")
        self.assertEqual(len(table), 1)

    def test_colliding_keys_are_found(self):
        table = LinearProbingHashTable(initial_capacity=8, auto_resize=False)
        table.put("a", "first")
        table.put("i", "second")

        self.assertEqual(table._hash("a"), table._hash("i"))
        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.get("i"), "second")

    def test_missing_key_raises_key_error(self):
        table = LinearProbingHashTable(initial_capacity=8, auto_resize=False)

        with self.assertRaises(KeyError):
            table.get("missing")

    def test_probe_sequence_wraps_from_last_slot_to_first(self):
        table = LinearProbingHashTable(initial_capacity=5, auto_resize=False)
        keys = ("c", "h", "m")
        self.assertEqual([table._hash(key) for key in keys], [4, 4, 4])

        for index, key in enumerate(keys):
            table.put(key, index)

        self.assertEqual(
            [entry.key if entry is not None else None for entry in table.slots],
            ["h", "m", None, None, "c"],
        )
        for index, key in enumerate(keys):
            self.assertEqual(table.get(key), index)

    def test_full_table_rejects_new_key_without_changing_contents(self):
        table = LinearProbingHashTable(initial_capacity=3, auto_resize=False)
        for index in range(3):
            table.put(f"key-{index}", index)

        with self.assertRaises(OverflowError):
            table.put("extra", 3)

        self.assertEqual(len(table), 3)
        for index in range(3):
            self.assertEqual(table.get(f"key-{index}"), index)

    def test_full_table_search_checks_at_most_capacity_slots(self):
        table = LinearProbingHashTable(initial_capacity=4, auto_resize=False)
        for index in range(4):
            table.put(f"key-{index}", index)

        with self.assertRaises(KeyError):
            table.get("missing")

        self.assertEqual(table.last_probe_count, table.capacity)

    def test_fixed_capacity_when_auto_resize_is_disabled(self):
        table = LinearProbingHashTable(initial_capacity=4, auto_resize=False)
        for index in range(3):
            table.put(f"key-{index}", index)

        self.assertFalse(table.auto_resize)
        self.assertEqual(table.capacity, 4)

    def test_matches_chaining_table_key_value_behavior(self):
        linear = LinearProbingHashTable(initial_capacity=8, auto_resize=False)
        chaining = HashTable(initial_capacity=8, auto_resize=False)
        entries = (("a", 10), ("i", 20), ("q", 30), ("other", 40))

        for key, value in entries:
            linear.put(key, value)
            chaining.put(key, value)
        linear.put("i", 200)
        chaining.put("i", 200)

        self.assertEqual(len(linear), len(chaining))
        for key, _ in entries:
            self.assertEqual(linear.get(key), chaining.get(key))
        with self.assertRaises(KeyError):
            linear.get("absent")
        with self.assertRaises(KeyError):
            chaining.get("absent")


if __name__ == "__main__":
    unittest.main()
