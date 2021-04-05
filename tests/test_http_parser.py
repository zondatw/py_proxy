import unittest

from zoxy.http import HTTPRequest, http_request_parse, HTTPResponse, http_response_parse

class HTTPRequestTest(unittest.TestCase):
    def test_httprequest_class(self):
        request = (
            b'POST http://test.org/ HTTP/1.1\r\n'
            b'Host: test.org\r\n'
            b'Content-Length: 17\r\n'
            b'Content-Type: application/json\r\n'
            b'\r\n'
            b'{"test": "value"}'
        )
        http_request = HTTPRequest()
        http_request.parse(request)

        self.assertEqual(http_request.method, "POST")
        self.assertEqual(http_request.request_target, "http://test.org/")
        self.assertEqual(http_request.http_version, "HTTP/1.1")
        self.assertEqual(http_request.header.__getattribute__("Host"), "test.org")
        self.assertEqual(http_request.header.__getattribute__("Content-Length"), "17")
        self.assertEqual(http_request.header.__getattribute__("Content-Type"), "application/json")
        self.assertEqual(http_request.body, b'{"test": "value"}')

    def test_http_request_parse(self):
        request = (
            b'POST http://test.org/ HTTP/1.1\r\n'
            b'Host: test.org\r\n'
            b'Content-Length: 17\r\n'
            b'Content-Type: application/json\r\n'
            b'\r\n'
            b'{"test": "value"}'
        )
        http_request = http_request_parse(request)

        self.assertEqual(http_request.method, "POST")
        self.assertEqual(http_request.request_target, "http://test.org/")
        self.assertEqual(http_request.http_version, "HTTP/1.1")
        self.assertEqual(http_request.header.__getattribute__("Host"), "test.org")
        self.assertEqual(http_request.header.__getattribute__("Content-Length"), "17")
        self.assertEqual(http_request.header.__getattribute__("Content-Type"), "application/json")
        self.assertEqual(http_request.body, b'{"test": "value"}')


class HTTPResponseTest(unittest.TestCase):
    def test_httpresponse_class(self):
        request = (
            b'HTTP/1.0 200 OK\r\n'
            b'Server: BaseHTTP/0.6 Python/3.7.3\r\n'
            b'Date: Mon, 05 Apr 2021 13:49:57 GMT\r\n'
            b'Content-type: text/html\r\n'
            b'\r\n'
            b'SUCCESS'
        )
        http_response = HTTPResponse()
        http_response.parse(request)

        self.assertEqual(http_response.http_version, "HTTP/1.0")
        self.assertEqual(http_response.status_code, "200")
        self.assertEqual(http_response.status_msg, "OK")
        self.assertEqual(http_response.header.__getattribute__("Server"), "BaseHTTP/0.6 Python/3.7.3")
        self.assertEqual(http_response.header.__getattribute__("Date"), "Mon, 05 Apr 2021 13:49:57 GMT")
        self.assertEqual(http_response.header.__getattribute__("Content-type"), "text/html")
        self.assertEqual(http_response.body, b'SUCCESS')

    def test_http_response_parse(self):
        request = (
            b'HTTP/1.0 200 OK\r\n'
            b'Server: BaseHTTP/0.6 Python/3.7.3\r\n'
            b'Date: Mon, 05 Apr 2021 13:49:57 GMT\r\n'
            b'Content-type: text/html\r\n'
            b'\r\n'
            b'SUCCESS'
        )
        http_response = http_response_parse(request)

        self.assertEqual(http_response.http_version, "HTTP/1.0")
        self.assertEqual(http_response.status_code, "200")
        self.assertEqual(http_response.status_msg, "OK")
        self.assertEqual(http_response.header.__getattribute__("Server"), "BaseHTTP/0.6 Python/3.7.3")
        self.assertEqual(http_response.header.__getattribute__("Date"), "Mon, 05 Apr 2021 13:49:57 GMT")
        self.assertEqual(http_response.header.__getattribute__("Content-type"), "text/html")
        self.assertEqual(http_response.body, b'SUCCESS')
