import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_default_capacity_is_eight(self):
        table = HashTable()

        self.assertEqual(table.capacity, 8)

    def test_horner_hash_calculation(self):
        table = HashTable(initial_capacity=8, auto_resize=False)

        # "abc": (((0 * 31 + 97) * 31 + 98) * 31 + 99) % 8 == 2
        self.assertEqual(table._hash("abc"), 2)

    def test_colliding_keys_can_both_be_retrieved(self):
        table = HashTable(initial_capacity=8, auto_resize=False)
        table.put("a", "first")
        table.put("i", "second")

        self.assertEqual(table._hash("a"), table._hash("i"))
        self.assertEqual(table.get("a"), "first")
        self.assertEqual(table.get("i"), "second")

    def test_duplicate_key_updates_value_without_increasing_length(self):
        table = HashTable()
        table.put("key", "old")
        table.put("key", "new")

        self.assertEqual(table.get("key"), "new")
        self.assertEqual(len(table), 1)

    def test_get_missing_key_raises_key_error(self):
        table = HashTable()

        with self.assertRaises(KeyError):
            table.get("missing")

    def test_load_factor_boundary_and_rehash(self):
        table = HashTable(initial_capacity=8)
        for index in range(6):
            table.put(f"key-{index}", index)

        self.assertEqual(table.capacity, 8)
        self.assertEqual(len(table), 6)

        table.put("key-6", 6)

        self.assertEqual(table.capacity, 16)
        self.assertEqual(len(table), 7)
        for index in range(7):
            with self.subTest(index=index):
                self.assertEqual(table.get(f"key-{index}"), index)

    def test_auto_resize_can_be_disabled(self):
        table = HashTable(initial_capacity=8, auto_resize=False)
        for index in range(12):
            table.put(f"key-{index}", index)

        self.assertEqual(table.capacity, 8)
        self.assertEqual(len(table), 12)
        for index in range(12):
            with self.subTest(index=index):
                self.assertEqual(table.get(f"key-{index}"), index)


if __name__ == "__main__":
    unittest.main()
