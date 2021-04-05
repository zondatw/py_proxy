import socket
import unittest
from unittest.mock import Mock, patch

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

    