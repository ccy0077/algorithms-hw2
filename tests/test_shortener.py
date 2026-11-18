import unittest

from src.base62 import decode, encode
from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def setUp(self):
        self.shortener = URLShortener()

    def test_urls_receive_sequential_base62_codes(self):
        first_url = "https://example.com/one"
        second_url = "https://example.com/two"

        first_code = self.shortener.shorten(first_url)
        second_code = self.shortener.shorten(second_url)

        self.assertEqual(first_code, "1")
        self.assertEqual(second_code, "2")
        self.assertEqual(self.shortener.expand(first_code), first_url)
        self.assertEqual(self.shortener.expand(second_code), second_url)

    def test_url_path_query_and_fragment_are_preserved(self):
        url = "https://example.com/path?query=value#section"

        code = self.shortener.shorten(url)

        self.assertEqual(self.shortener.expand(code), url)

    def test_scheme_is_case_insensitive(self):
        url = "HTTPS://example.com/path"

        code = self.shortener.shorten(url)

        self.assertEqual(self.shortener.expand(code), url)

    def test_duplicate_url_returns_existing_code_without_consuming_serial(self):
        url = "https://example.com/path"

        first_code = self.shortener.shorten(url)
        duplicate_code = self.shortener.shorten(url)
        next_code = self.shortener.shorten("https://example.com/another")

        self.assertEqual(first_code, "1")
        self.assertEqual(duplicate_code, first_code)
        self.assertEqual(next_code, "2")
        self.assertEqual(self.shortener.expand(first_code), url)

    def test_distinct_url_strings_receive_distinct_codes(self):
        without_slash = "https://example.com/path"
        with_slash = "https://example.com/path/"

        self.assertNotEqual(
            self.shortener.shorten(without_slash),
            self.shortener.shorten(with_slash),
        )

    def test_invalid_urls_are_rejected(self):
        invalid_urls = (
            "",
            "   ",
            "example.com/path",
            "ftp://example.com/file",
            "http:///path",
            "http://example.com:invalid/path",
            "https://example.com/a b",
            "https://example.com/a\nb",
            "https://example.com/%ZZ",
            None,
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.shortener.shorten(url)

    def test_url_length_2048_is_accepted_and_2049_is_rejected(self):
        prefix = "http://example.com/"
        url_2048 = prefix + "x" * (2048 - len(prefix))
        url_2049 = prefix + "x" * (2049 - len(prefix))

        code = self.shortener.shorten(url_2048)

        self.assertEqual(code, "1")
        self.assertEqual(self.shortener.expand(code), url_2048)
        with self.assertRaises(ValueError):
            self.shortener.shorten(url_2049)

    def test_reserved_table_code_is_skipped(self):
        self.shortener._next_id = decode("table")
        url = "https://example.com/reserved-code-boundary"

        code = self.shortener.shorten(url)

        self.assertNotEqual(code, "table")
        self.assertEqual(code, encode(decode("table") + 1))
        self.assertEqual(self.shortener.expand(code), url)

    def test_missing_short_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.shortener.expand("doesnotexist")

    def test_empty_or_malformed_short_code_is_rejected(self):
        for code in ("", "a!"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    self.shortener.expand(code)

    def test_invalid_url_does_not_change_data_or_serial(self):
        original_url = "https://example.com/original"
        original_code = self.shortener.shorten(original_url)

        with self.assertRaises(ValueError):
            self.shortener.shorten("https://example.com/invalid path")

        next_code = self.shortener.shorten("https://example.com/next")

        self.assertEqual(self.shortener.expand(original_code), original_url)
        self.assertEqual(next_code, "2")

    def test_overlong_url_does_not_change_data_or_serial(self):
        original_url = "https://example.com/original"
        original_code = self.shortener.shorten(original_url)
        prefix = "http://example.com/"
        overlong_url = prefix + "x" * (2049 - len(prefix))

        with self.assertRaises(ValueError):
            self.shortener.shorten(overlong_url)

        next_code = self.shortener.shorten("https://example.com/next")

        self.assertEqual(self.shortener.expand(original_code), original_url)
        self.assertEqual(next_code, "2")


if __name__ == "__main__":
    unittest.main()
