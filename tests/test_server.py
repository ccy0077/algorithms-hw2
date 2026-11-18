import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import make_server


class URLServerTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def _request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read()
        connection.close()
        return result

    def _post_url(self, url):
        body = urlencode((("url", url),))
        return self._request(
            "POST",
            "/shorten",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def test_get_root_returns_html_input_form(self):
        status, headers, body = self._request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn("text/html", dict(headers)["Content-Type"])
        self.assertIn("한국어", body.decode("utf-8"))
        self.assertIn('action="/shorten"', body.decode("utf-8"))
        self.assertIn('name="url"', body.decode("utf-8"))

    def test_post_shorten_returns_created_code_and_path(self):
        status, _, body = self._post_url("https://example.com/path")
        rendered = body.decode("utf-8")

        self.assertEqual(status, 201)
        self.assertIn("1", rendered)
        self.assertIn('href="/1"', rendered)
        self.assertIn("/1", rendered)

    def test_invalid_url_returns_bad_request_without_changing_storage(self):
        before = len(self.server.shortener._url_to_code)

        status, _, _ = self._post_url("https://example.com/invalid path")

        self.assertEqual(status, 400)
        self.assertEqual(len(self.server.shortener._url_to_code), before)
        self.assertEqual(self.server.shortener.shorten("https://example.com/next"), "1")

    def test_get_short_code_redirects_to_original_url(self):
        url = "https://example.com/path?query=value#section"
        self._post_url(url)

        status, headers, _ = self._request("GET", "/1")

        self.assertEqual(status, 302)
        self.assertEqual(dict(headers)["Location"], url)

    def test_malformed_code_returns_bad_request(self):
        status, _, _ = self._request("GET", "/!")

        self.assertEqual(status, 400)

    def test_unknown_valid_code_returns_not_found(self):
        status, _, _ = self._request("GET", "/ZZ")

        self.assertEqual(status, 404)

    def test_unsupported_http_method_returns_method_not_allowed(self):
        status, _, _ = self._request("PUT", "/")

        self.assertEqual(status, 405)

    def test_table_page_visualizes_buckets_chains_and_hash_calculation(self):
        self._post_url("https://example.com/path")

        status, _, body = self._request("GET", "/table")
        rendered = body.decode("utf-8")

        self.assertEqual(status, 200)
        self.assertIn("버킷", rendered)
        self.assertIn("연결 리스트", rendered)
        self.assertIn("적재율", rendered)
        self.assertIn("(31 * h + ord(c)) % M", rendered)
        self.assertIn("최종 인덱스", rendered)
        self.assertIn("https://example.com/path", rendered)

    def test_html_special_characters_in_url_are_escaped(self):
        url = "https://example.com/?q=<script>&x=1"

        status, _, body = self._post_url(url)
        rendered = body.decode("utf-8")

        self.assertEqual(status, 201)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&amp;x=1", rendered)

    def test_server_restart_clears_shortened_url_data(self):
        status, _, _ = self._post_url("https://example.com/temporary")
        self.assertEqual(status, 201)

        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

        self.server = make_server(host="127.0.0.1", port=self.port)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

        status, _, _ = self._request("GET", "/1")

        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
