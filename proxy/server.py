import signal
import socket
import threading
import logging
from urllib.parse import urlparse

from proxy.http import http_request_parse, http_response_parse

logger = logging.getLogger(__name__)


class ProxyServer:
    def __init__(self, config):
        self.__max_recv_len = 1024
        self.__default_socket_timeout = 1
        self.__dest_connection_timeout = 5
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
        while True:
            http_response = self.redirect(src_socket, src_address)
            if http_response.status_code not in ["301"]:
                break
        try:
            src_socket.shutdown(socket.SHUT_RDWR)
        except socket.timeout:
            pass
        src_socket.close()

    def redirect(self, src_socket, src_address):
        request = src_socket.recv(self.__max_recv_len)
        http_request = http_request_parse(request)
        dest_url = http_request.request_target
        logger.info(f"{src_address[0]}:{src_address[1]} -> {dest_url}")

        # parse url
        dest_domain, dest_port = self._parse_dest_url(dest_url)

        # create new connection to destination
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        dest_socket.settimeout(self.__dest_connection_timeout)
        dest_socket.connect((dest_domain, dest_port))
        dest_socket.sendall(request)

        # redirect data
        response_data = b""
        while True:
            try:
                data = dest_socket.recv(self.__max_recv_len)
            except socket.timeout:
                data = b""

            if data:
                response_data += data
                src_socket.send(data)
            else:
                break
        http_response = http_response_parse(response_data)

        try:
            dest_socket.shutdown(socket.SHUT_RDWR)
        except socket.timeout:
            pass
        dest_socket.close()
        return http_response

    def shutdown(self, singal, frame):
        self.__listen_flag = False
        exit(0)

    def _get_client_name(self, address):
        return f"proxy_{address}"

    def _parse_dest_url(self, dest_url):
        uri = urlparse(dest_url)
        logger.debug(uri)
        scheme = uri.scheme
        host = uri.hostname
        port = uri.port
        if not port:
            if scheme == "http":
                port = 80
        return host, port