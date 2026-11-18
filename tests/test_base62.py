import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_encode_known_values(self):
        cases = (
            (0, "0"),
            (61, "Z"),
            (62, "10"),
            (3843, "ZZ"),
            (3844, "100"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(encode(value), expected)

    def test_decode_known_values(self):
        cases = (
            ("0", 0),
            ("Z", 61),
            ("10", 62),
            ("ZZ", 3843),
            ("100", 3844),
        )
        for encoded, expected in cases:
            with self.subTest(encoded=encoded):
                self.assertEqual(decode(encoded), expected)

    def test_round_trip_large_integer(self):
        value = 10**100 + 98765432101234567890
        self.assertEqual(decode(encode(value)), value)

    def test_encode_rejects_negative_integer(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_encode_rejects_non_integer(self):
        with self.assertRaises(TypeError):
            encode(1.5)

    def test_decode_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            decode("")

    def test_decode_rejects_invalid_character(self):
        with self.assertRaises(ValueError):
            decode("a!")

    def test_decode_rejects_non_string(self):
        with self.assertRaises(TypeError):
            decode(123)


if __name__ == "__main__":
    unittest.main()
