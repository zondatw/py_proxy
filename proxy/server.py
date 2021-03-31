import signal
import socket
import ssl
import threading
import logging
from urllib.parse import urlparse

from proxy.http import http_request_parse, http_response_parse, HTTPResponse

logger = logging.getLogger(__name__)


class ProxyServer:
    def __init__(self, config):
        self.__max_recv_len = 1024
        self.__default_socket_timeout = 1
        self.__dest_connection_timeout = 1
        self.__max_redirect_timeout = 10 // self.__dest_connection_timeout // 2
        self.__listen_flag = True

        socket.setdefaulttimeout(self.__default_socket_timeout)

        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((config["HOST_NAME"], config["BIND_PORT"]))
        
        self.server_socket.listen(10)

    def listen(self):
        while self.__listen_flag:
            try:
                (client_socket, client_address) = self.server_socket.accept() 
            except socket.timeout:
                continue

            client_thread = threading.Thread(
                name=self._get_client_name(client_address),
                target=self.proxy_thread,
                args=(client_socket, client_address)
            )
            client_thread.setDaemon(True)
            client_thread.start()
        self.server_socket.close()

    def proxy_thread(self, src_socket, src_address):
        self.redirect(src_socket, src_address)
        try:
            logger.debug("Shutdown src socket")
            src_socket.shutdown(socket.SHUT_RDWR)
        except socket.timeout:
            pass
        try:
            logger.debug("Close src socket")
            src_socket.close()
        except socket.timeout:
            pass

    def get_dest_socket(self, dest_domain, dest_port):
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_socket.connect((dest_domain, dest_port))
        dest_socket.settimeout(self.__dest_connection_timeout)
        return dest_socket

    def redirect(self, src_socket, src_address):
        request = src_socket.recv(self.__max_recv_len)
        logger.debug(request)
        http_request = http_request_parse(request)
        dest_url = http_request.request_target
        logger.info(f"{src_address[0]}:{src_address[1]} -> {dest_url}")

        logger.debug(f"HTTP request: {http_request}")
        is_https_tunnel = False
        if http_request.method == "CONNECT":
            is_https_tunnel = True

        # parse url
        dest_domain, dest_port = self._parse_dest_url(dest_url)
        dest_socket = self.get_dest_socket(dest_domain, dest_port)

        if is_https_tunnel:
            src_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        else:
            logger.debug(f"Request: {request}")
            dest_socket.sendall(request)

        # redirect data
        response_data = self.redirect_data(src_socket, dest_socket)
        logger.debug(f"Response: {response_data}")

        try:
            logger.debug("Shutdown dest socket")
            dest_socket.shutdown(socket.SHUT_RDWR)
        except socket.timeout:
            pass
        try:
            logger.debug("Close dest socket")
            dest_socket.close()
        except socket.timeout:
            pass

    def shutdown(self, singal, frame):
        self.__listen_flag = False
        exit(0)

    def _get_client_name(self, address):
        return f"proxy_{address}"

    def _parse_dest_url(self, dest_url):
        if "://" not in dest_url and ":443" in dest_url:
            dest_url = f"https://{dest_url}"

        uri = urlparse(dest_url)
        logger.debug(uri)
        scheme = uri.scheme
        host = uri.hostname
        port = uri.port
        if not port:
            if scheme == "http":
                port = 80
        return host, port

    def redirect_data(self, src_socket, dest_socket):
        response_data = b""
        count = 0
        try:
            while True:
                d_to_s_response_data = b""
                s_to_d_response_data = b""
                try:
                    d_to_s_response_data = dest_socket.recv(self.__max_recv_len)
                    src_socket.sendall(d_to_s_response_data)
                except socket.error as err:
                    pass
                try:
                    s_to_d_response_data = src_socket.recv(self.__max_recv_len)
                    dest_socket.sendall(s_to_d_response_data)
                except socket.error as err:
                    pass

                if d_to_s_response_data != b"":
                    response_data += d_to_s_response_data
                if d_to_s_response_data == b"" and s_to_d_response_data == b"":
                    count += 1
                    if count >= self.__max_redirect_timeout:
                        break
                else:
                    count = 0
        except Exception as err:
            logger.warning(f"Redirect data warning: {err}")
            response_data = b""
        
        return response_data
