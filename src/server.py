"""HTTP interface for the in-memory URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

from src.shortener import URLShortener


class ShortenerRequestHandler(BaseHTTPRequestHandler):
    def _send_html(self, status, content):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _error_page(self, status, message):
        self._send_html(
            status,
            "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
            "<title>요청 오류</title><body><h1>요청을 처리할 수 없습니다</h1>"
            f"<p>{html.escape(message)}</p><p><a href=\"/\">처음으로</a></p>"
            "</body></html>",
        )

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(
                200,
                "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
                "<title>URL 단축기</title><body><h1>URL 단축기</h1>"
                "<p>한국어 URL 입력 양식: HTTP 또는 HTTPS 주소를 입력하세요.</p>"
                "<form action=\"/shorten\" method=\"post\">"
                "<label for=\"url\">단축할 URL</label>"
                "<input id=\"url\" name=\"url\" type=\"url\" required>"
                "<button type=\"submit\">단축하기</button></form></body></html>",
            )
            return

        if path == "/table":
            self._send_html(200, self._render_table_page())
            return

        if not path.startswith("/") or "/" in path[1:] or not path[1:]:
            self._error_page(404, "요청한 경로를 찾을 수 없습니다.")
            return

        code = path[1:]
        try:
            url = self.server.shortener.expand(code)
        except ValueError:
            self._error_page(400, "단축 코드 형식이 올바르지 않습니다.")
            return
        except KeyError:
            self._error_page(404, "등록된 단축 URL이 없습니다.")
            return

        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if urlsplit(self.path).path != "/shorten":
            self._error_page(404, "요청한 경로를 찾을 수 없습니다.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error_page(400, "요청 본문 길이가 올바르지 않습니다.")
            return
        if content_length < 0:
            self._error_page(400, "요청 본문 길이가 올바르지 않습니다.")
            return

        try:
            form_body = self.rfile.read(content_length).decode("utf-8")
            fields = parse_qsl(form_body, keep_blank_values=True, strict_parsing=False)
        except (UnicodeDecodeError, ValueError):
            self._error_page(400, "폼 입력을 읽을 수 없습니다.")
            return

        url = None
        for name, value in fields:
            if name == "url":
                url = value
                break
        if url is None:
            self._error_page(400, "url 입력이 필요합니다.")
            return

        try:
            code = self.server.shortener.shorten(url)
        except ValueError:
            self._error_page(400, "URL 형식이 올바르지 않습니다.")
            return

        escaped_url = html.escape(url, quote=True)
        escaped_code = html.escape(code, quote=True)
        path = f"/{escaped_code}"
        self._send_html(
            201,
            "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
            "<title>단축 URL 생성</title><body><h1>단축 URL 생성 완료</h1>"
            f"<p>원본 URL: <code>{escaped_url}</code></p>"
            f"<p>단축 코드: <code>{escaped_code}</code></p>"
            f"<p>단축 경로: <a href=\"{path}\">{path}</a></p>"
            "<p><a href=\"/\">다른 URL 단축하기</a></p></body></html>",
        )

    def send_error(self, code, message=None, explain=None):
        if code == 501:
            self._error_page(405, "지원하지 않는 HTTP 메서드입니다.")
            return
        super().send_error(code, message, explain)

    def _render_table_page(self):
        parts = [
            "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
            "<title>해시 테이블 시각화</title><body>"
            "<h1>개별 체이닝 해시 테이블과 연결 리스트</h1>"
            "<p>호너 해시: h = (31 * h + ord(c)) % M</p>"
        ]
        tables = (
            ("URL → 단축 코드", self.server.shortener._url_to_code),
            ("단축 코드 → URL", self.server.shortener._code_to_url),
        )
        for title, table in tables:
            parts.append(f"<h2>{html.escape(title)}</h2>")
            parts.append(
                f"<p>칸 수 M: {table.capacity}; 적재율: "
                f"{len(table) / table.capacity:.6f}</p><ol>"
            )
            for bucket_index, head in enumerate(table.buckets):
                parts.append(f"<li>버킷 {bucket_index}: ")
                node = head
                if node is None:
                    parts.append("비어 있음")
                else:
                    parts.append('<span class="chain">')
                    first = True
                    while node is not None:
                        if not first:
                            parts.append(" → ")
                        key = html.escape(node.key, quote=True)
                        parts.append(f"<code>{key}</code>")
                        hash_value = 0
                        trace = ["h=0"]
                        for character in node.key:
                            previous_hash = hash_value
                            hash_value = (
                                31 * hash_value + ord(character)
                            ) % table.capacity
                            trace.append(
                                f"(31 * {previous_hash} + ord({character!r})) "
                                f"% {table.capacity} = {hash_value}"
                            )
                        parts.append(
                            f" <small>호너 해시 계산: "
                            f"{html.escape('; '.join(trace))}; "
                            f"최종 인덱스 {hash_value}</small>"
                        )
                        first = False
                        node = node.next
                    parts.append("</span>")
                parts.append("</li>")
            parts.append("</ol>")
        parts.append('<p><a href="/">처음으로</a></p></body></html>')
        return "".join(parts)


def make_server(host="127.0.0.1", port=8000, shortener=None):
    server = ThreadingHTTPServer((host, port), ShortenerRequestHandler)
    server.shortener = shortener if shortener is not None else URLShortener()
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="URL 단축 웹 서버")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args(argv)
    server = make_server(host="0.0.0.0", port=arguments.port)
    try:
        print(f"URL 단축 서버 실행 중: http://0.0.0.0:{arguments.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
