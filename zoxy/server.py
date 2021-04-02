import ipaddress
import signal
import socket
import inspect
import ssl
import threading
import logging
from collections import defaultdict
from typing import List
from urllib.parse import urlparse

from .http import http_request_parse, http_response_parse, HTTPResponse

logger = logging.getLogger(__name__)


class ProxyServer:
    def __init__(
        self,
        url: str,
        port: str,
        allowed_accesses: List[List] =[],
        blocked_accesses: List[List] =[],
        forwarding: List[List] =[],
    ):
        self.__max_recv_len = 1024 * 1024 * 1
        self.__default_socket_timeout = 1
        self.__dest_connection_timeout = 1
        self.__max_pipe_timeout = 4 // self.__dest_connection_timeout // 2
        self.__listen_flag = True
        self.__enable_allowed_access = True if allowed_accesses != [] else False
        self.__enable_blocked_access = True if blocked_accesses != [] else False
        self.__enable_forwarding = True if forwarding != [] else False

        if self.__enable_allowed_access:
            # format: {ipaddress.ip_network: [port]}
            self.allowed_accesses = self.__init_allowed_accesses(allowed_accesses)

        if self.__enable_blocked_access:
            # format: {ipaddress.ip_network: [port]}
            self.blocked_accesses = self.__init_blocked_accesses(blocked_accesses)

        if self.__enable_forwarding:
            # format: [{
            #       "original_ip": ipaddress.ip_network,
            #       "original_port": str,
            #       "destination_ip": str,
            #       "destination_port": str,
            # }]
            self.forwarding_list = self.__init_forwarding_list(forwarding)

        socket.setdefaulttimeout(self.__default_socket_timeout)

        # Shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((url, port))
        
        self.server_socket.listen(100)
        logger.info(f"Proxy server: {url}:{port}")

    def listen(self):
        while self.__listen_flag:
            try:
                (client_socket, client_address) = self.server_socket.accept() 
            except socket.timeout:
                continue

            logger.debug(f"Get new connect: {client_address}")
            if self.__enable_blocked_access:
                if self.is_connection_blocked(client_address[0], client_address[1]):
                    logger.warning(f"Blocked client: {client_address}")
                    client_socket.close()
                    continue
            if self.__enable_allowed_access:
                if not self.is_connection_allowed(client_address[0], client_address[1]):
                    logger.warning(f"Not allowed client: {client_address}")
                    client_socket.close()
                    continue

            client_thread = threading.Thread(
                name=self._get_client_name(client_address),
                target=self.proxy_thread,
                args=(client_socket, client_address)
            )
            client_thread.setDaemon(True)
            client_thread.start()
        self.server_socket.close()

    def proxy_thread(self, src_socket: socket, src_address: tuple):
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

        if self.__enable_forwarding:
            dest_domain, dest_port = self.get_forwarding_dest(dest_domain, dest_port)

        dest_socket = None
        try:
            dest_socket = self.get_dest_socket(dest_domain, dest_port)
            self.pipe(src_socket, request, dest_socket, is_https_tunnel)
        except socket.timeout:
            pass

        try:
            logger.debug("Shutdown dest socket")
            if dest_socket:
                dest_socket.shutdown(socket.SHUT_RDWR)
        except socket.timeout:
            pass
        try:
            logger.debug("Close dest socket")
            if dest_socket:
                dest_socket.close()
        except socket.timeout:
            pass

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

    def get_dest_socket(self, dest_domain: str, dest_port: str) -> socket:
        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_socket.connect((dest_domain, dest_port))
        dest_socket.settimeout(self.__dest_connection_timeout)
        return dest_socket

    def pipe(self, src_socket: socket, request: bin, dest_socket: socket, is_https_tunnel: bool):
        if is_https_tunnel:
            src_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        else:
            logger.debug(f"Request: {request}")
            dest_socket.sendall(request)

        # pipe data
        response_data = self.pipe_data(src_socket, dest_socket)
        logger.debug(f"Response: {response_data}")

    def shutdown(self, singal_handler: signal.Signals, frame: inspect.types.FrameType):
        self.__listen_flag = False
        exit(0)

    def _get_client_name(self, address: str) -> str:
        return f"proxy_{address}"

    def _parse_dest_url(self, dest_url: str) -> (str, int):
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

    def pipe_data(self, src_socket: socket, dest_socket: socket) -> bin:
        response_data = b""
        count = 0
        try:
            while True:
                d_to_s_response_data = b""
                s_to_d_response_data = b""
                try:
                    d_to_s_response_data = dest_socket.recv(self.__max_recv_len)
                    src_socket.sendall(d_to_s_response_data)
                except (socket.error, socket.timeout) as err:
                    pass
                try:
                    s_to_d_response_data = src_socket.recv(self.__max_recv_len)
                    dest_socket.sendall(s_to_d_response_data)
                except (socket.error, socket.timeout) as err:
                    pass

                if d_to_s_response_data != b"":
                    response_data += d_to_s_response_data
                if d_to_s_response_data == b"" and s_to_d_response_data == b"":
                    count += 1
                    if count >= self.__max_pipe_timeout:
                        break
                else:
                    count = 0
        except Exception as err:
            logger.warning(f"Pipe data warning: {err}")
            response_data = b""
        
        return response_data

    def __init_allowed_accesses(self, allowed_access: List[List]) -> defaultdict(list):
        allowed_accesses = self.__get_init_access_table(allowed_access)
        logger.debug(f"Initial allowed accessed: {allowed_accesses}")
        return allowed_accesses

    def __init_blocked_accesses(self, blocked_access: List[List]) -> defaultdict(list):
        blocked_accesses = self.__get_init_access_table(blocked_access)
        logger.debug(f"Initial blocked accessed: {blocked_accesses}")
        return blocked_accesses

    def __get_init_access_table(self, access_list: List[List]) -> defaultdict(list):
        accesses = defaultdict(list)
        for ip_adr, port in access_list:
            accesses[ipaddress.ip_network(ip_adr)].append(str(port))
        return accesses

    def __init_forwarding_list(self, forwarding: List[List]) -> List[dict]:
        forwarding_list = []
        for original_ip, original_port, destination_ip, destination_port in forwarding:
            forwarding_list.append({
                "original_ip": ipaddress.ip_network(original_ip),
                "original_port": str(original_port),
                "destination_ip": destination_ip,
                "destination_port": str(destination_port),
            })
        logger.debug(f"Initial forwarding list: {forwarding_list}")
        return forwarding_list

    def get_forwarding_dest(self, dest_domain: str, dest_port: int) -> (str, int):
        dest_ip_address = ipaddress.ip_network(socket.gethostbyname(dest_domain))
        forwarding_domain, forwarding_port = dest_domain, dest_port
        for forwarding in self.forwarding_list:
            original_ip = forwarding["original_ip"]
            original_port = forwarding["original_port"]
            destination_ip = forwarding["destination_ip"]
            destination_port = forwarding["destination_port"]
            if original_ip.supernet_of(dest_ip_address) and (original_port == "*" or str(dest_port) == original_port):
                if destination_port != "*":
                    forwarding_port = int(destination_port)
                forwarding_domain = destination_ip
                logger.info(f"Forward {dest_domain}:{dest_port} to {forwarding_domain}:{forwarding_port}")
                break
        return forwarding_domain, forwarding_port

    def is_connection_allowed(self, host: str, port: int) -> bool:
        return self.is_testee_in_access_table(self.allowed_accesses, host, port)

    def is_connection_blocked(self, host: str, port: int) -> bool:
        return self.is_testee_in_access_table(self.blocked_accesses, host, port)
    
    def is_testee_in_access_table(self, accesses: dict, host: str, port: int) -> bool:
        tested_ip_address = ipaddress.ip_network(host)
        for access_ip_address, access_port_list in accesses.items():
            for access_port in access_port_list:
                if access_ip_address.supernet_of(tested_ip_address) and (access_port == "*" or str(port) == access_port):
                    return True
        else:
            return False
