"""In-memory URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit

from src.base62 import decode, encode
from src.hash_table import HashTable


class URLShortener:
    def __init__(self):
        self._url_to_code = HashTable()
        self._code_to_url = HashTable()
        self._next_id = 1

    def shorten(self, url):
        self._validate_url(url)

        try:
            return self._url_to_code.get(url)
        except KeyError:
            pass

        while True:
            code = encode(self._next_id)
            self._next_id += 1
            if code != "table":
                break

        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code):
        if not isinstance(code, str):
            raise ValueError("code must be a base62 string")
        decode(code)
        return self._code_to_url.get(code)

    @staticmethod
    def _validate_url(url):
        if not isinstance(url, str) or not url:
            raise ValueError("url must be a non-empty string")
        if len(url) > 2048:
            raise ValueError("url must not exceed 2048 characters")
        if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
            raise ValueError("url must not contain whitespace or control characters")

        for index, character in enumerate(url):
            if character == "%":
                if (
                    index + 2 >= len(url)
                    or url[index + 1] not in "0123456789abcdefABCDEF"
                    or url[index + 2] not in "0123456789abcdefABCDEF"
                ):
                    raise ValueError("url contains an invalid percent escape")

        try:
            parts = urlsplit(url)
            hostname = parts.hostname
            parts.port
        except ValueError as error:
            raise ValueError("url has invalid syntax") from error

        if parts.scheme.lower() not in ("http", "https") or not parts.netloc or not hostname:
            raise ValueError("url must be an absolute HTTP or HTTPS URL with a host")
