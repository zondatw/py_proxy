import socket
import unittest
from unittest.mock import Mock, patch, call

from zoxy.server import ProxyServer

class ServerSocketTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "0.0.0.0",
            "port": 9999,
        }
        self.proxy_server = ProxyServer(**self.config)

    def tearDown(self):
        self.proxy_server.close()

    def test_parse_dest_url(self):
        testee = "http://test.org/"
        self.assertEqual(
            self.proxy_server._parse_dest_url(testee),
            ("test.org", 80)
        )
        testee = "https://test.org/"
        self.assertEqual(
            self.proxy_server._parse_dest_url(testee),
            ("test.org", 443)
        )
        testee = "test.org:443"
        self.assertEqual(
            self.proxy_server._parse_dest_url(testee),
            ("test.org", 443)
        )

    @patch("socket.socket", return_value=Mock())
    def test_get_dest_socket(self, mock_socket: unittest.mock.MagicMock):
        testee = ("127.0.0.1", 8000)
        dest_socket = self.proxy_server.get_dest_socket(*testee)
        mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
        dest_socket.connect.assert_called_with(testee)
        dest_socket.settimeout.assert_called_with(self.proxy_server._ProxyServer__dest_connection_timeout)

    @patch("zoxy.server.ProxyServer.pipe_data", return_value=None)
    def test_pipe(self, mock_pipe_data: unittest.mock.MagicMock):
        mock_src_socket = Mock()
        mock_dest_socket = Mock()
        test_request = b"Test requests\r\n"

        # is_https_tunnel: False
        self.proxy_server.pipe(mock_src_socket, test_request, mock_dest_socket, False)
        self.assertEqual(mock_src_socket.sendall.call_count, 0)
        mock_dest_socket.sendall.assert_called_with(test_request)
        mock_pipe_data.assert_called_with(mock_src_socket, mock_dest_socket)

        mock_src_socket.reset_mock()
        mock_dest_socket.reset_mock()
        mock_pipe_data.reset_mock()
        # is_https_tunnel: True
        self.proxy_server.pipe(mock_src_socket, test_request, mock_dest_socket, True)
        self.assertEqual(mock_dest_socket.sendall.call_count, 0)
        mock_src_socket.sendall.assert_called_with(b"HTTP/1.1 200 Connection established\r\n\r\n")
        mock_pipe_data.assert_called_with(mock_src_socket, mock_dest_socket)

    def test_pipe_data(self):
        mock_src_socket = Mock()
        mock_dest_socket = Mock()
        test_src_data = [b"Test src data\r\n"] + [b""] * self.proxy_server._ProxyServer__max_pipe_timeout
        test_dest_data = [b"Test dest data\r\n"] + [b""] * self.proxy_server._ProxyServer__max_pipe_timeout

        mock_src_socket.recv.side_effect = iter(test_src_data)
        mock_dest_socket.recv.side_effect = iter(test_dest_data)
        response_data = self.proxy_server.pipe_data(mock_src_socket, mock_dest_socket)
        self.assertEqual(mock_src_socket.sendall.mock_calls, [call(data) for data in test_dest_data])
        self.assertEqual(mock_dest_socket.sendall.call_args_list, [call(data) for data in test_src_data])
        self.assertEqual(b"".join(test_dest_data), response_data)

class ServerTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "0.0.0.0",
            "port": 9999,
            "allowed_accesses": [
                ["127.0.1.1", "8080"],
                ["127.0.2.0/24", "1234"],
                ["127.0.0.0/24", "*"],
            ],
            "blocked_accesses": [
                ["192.0.1.1", "8080"],
                ["192.0.2.0/24", "1234"],
                ["192.0.0.0/24", "*"],
            ],
            "forwarding": [
                ["196.168.2.1", "1234", "127.0.2.1", "8000"],
                ["196.168.1.0/24", "1234", "127.0.0.1", "8000"],
                ["196.168.0.0/24", "*", "127.0.0.2", "*"],
            ],
        }
        self.proxy_server = ProxyServer(**self.config)

    def tearDown(self):
        self.proxy_server.close()

    @patch("zoxy.server.ProxyServer.pipe", return_value=Mock())
    @patch("zoxy.server.ProxyServer.get_dest_socket", return_value=Mock())
    def test_proxy_thread(self, mock_get_dest_socket, mock_pipe):
        mock_src_socket = Mock()
        src_address = ("127.0.0.1", 8000)
        mock_src_socket.recv.side_effect = iter([(
            b'POST http://127.1.0.1/ HTTP/1.1\r\n'
            b'Host: 127.1.0.1\r\n'
            b'Content-Length: 17\r\n'
            b'Content-Type: application/json\r\n'
            b'\r\n'
            b'{"test": "value"}'
        ), socket.timeout])
        self.proxy_server.proxy_thread(mock_src_socket, src_address)
        mock_get_dest_socket.assert_called_with("127.1.0.1", 80)

    @patch("zoxy.server.ProxyServer.pipe", return_value=Mock())
    @patch("zoxy.server.ProxyServer.get_dest_socket", return_value=Mock())
    def test_proxy_thread_with_not_allowed_access(self, mock_get_dest_socket, mock_pipe):
        mock_src_socket = Mock()
        src_address = ("111.0.0.1", 8000)
        mock_src_socket.recv.side_effect = iter([(
            b'POST http://127.1.0.1/ HTTP/1.1\r\n'
            b'Host: 127.1.0.1\r\n'
            b'Content-Length: 17\r\n'
            b'Content-Type: application/json\r\n'
            b'\r\n'
            b'{"test": "value"}'
        ), socket.timeout])
        self.proxy_server.proxy_thread(mock_src_socket, src_address)
        self.assertEqual(mock_get_dest_socket.call_count, 0)

    @patch("zoxy.server.ProxyServer.pipe", return_value=Mock())
    @patch("zoxy.server.ProxyServer.get_dest_socket", return_value=Mock())
    def test_proxy_thread_with_blocked_access(self, mock_get_dest_socket, mock_pipe):
        mock_src_socket = Mock()
        src_address = ("192.0.0.1", 8000)
        mock_src_socket.recv.side_effect = iter([(
            b'POST http://127.1.0.1/ HTTP/1.1\r\n'
            b'Host: 127.1.0.1\r\n'
            b'Content-Length: 17\r\n'
            b'Content-Type: application/json\r\n'
            b'\r\n'
            b'{"test": "value"}'
        ), socket.timeout])
        self.proxy_server.proxy_thread(mock_src_socket, src_address)
        self.assertEqual(mock_get_dest_socket.call_count, 0)

    @patch("zoxy.server.ProxyServer.pipe", return_value=Mock())
    @patch("zoxy.server.ProxyServer.get_dest_socket", return_value=Mock())
    def test_proxy_thread_with_forwarding(self, mock_get_dest_socket, mock_pipe):
        mock_src_socket = Mock()
        src_address = ("127.0.0.1", 8000)
        mock_src_socket.recv.side_effect = iter([(
            b'POST http://196.168.0.1/ HTTP/1.1\r\n'
            b'Host: 196.168.0.1\r\n'
            b'Content-Length: 17\r\n'
            b'Content-Type: application/json\r\n'
            b'\r\n'
            b'{"test": "value"}'
        ), socket.timeout])
        self.proxy_server.proxy_thread(mock_src_socket, src_address)
        mock_get_dest_socket.assert_called_with("127.0.0.2", 80)