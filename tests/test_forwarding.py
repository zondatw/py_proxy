import ipaddress
import unittest

from zoxy.server import ProxyServer

class ProxyServerAccessTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "0.0.0.0",
            "port": 9999,
            "forwarding": [
                ["196.168.2.1", "1234", "127.0.2.1", "8000"],
                ["196.168.1.0/24", "1234", "127.0.0.1", "8000"],
                ["0.0.0.0/0", "*", "127.0.0.2", "*"],
            ],
        }
        self.proxy_server = ProxyServer(**self.config)

    def tearDown(self):
        self.proxy_server.close()

    def test__init_forwarding_list(self):
        forwarding = self.config["forwarding"]
        checker_forwarding_list = []
        for original_ip, original_port, destination_ip, destination_port in forwarding:
            checker_forwarding_list.append({
                "original_ip": ipaddress.ip_network(original_ip),
                "original_port": str(original_port),
                "destination_ip": destination_ip,
                "destination_port": str(destination_port),
            })
        forwarding_list = self.proxy_server._ProxyServer__init_forwarding_list(forwarding)
        self.assertListEqual(forwarding_list, checker_forwarding_list)
        self.assertListEqual(self.proxy_server.forwarding_list, checker_forwarding_list)

    def test_get_forwarding_dest(self):
        forwarding_domain, forwarding_port = self.proxy_server.get_forwarding_dest("196.168.2.1", 1234)
        self.assertEqual(forwarding_domain, "127.0.2.1")
        self.assertEqual(forwarding_port, 8000)
        forwarding_domain, forwarding_port = self.proxy_server.get_forwarding_dest("196.168.1.1", 1234)
        self.assertEqual(forwarding_domain, "127.0.0.1")
        self.assertEqual(forwarding_port, 8000)
        forwarding_domain, forwarding_port = self.proxy_server.get_forwarding_dest("172.1.1.1", 1234)
        self.assertEqual(forwarding_domain, "127.0.0.2")
        self.assertEqual(forwarding_port, 1234)
        forwarding_domain, forwarding_port = self.proxy_server.get_forwarding_dest("172.1.1.1", 7777)
        self.assertEqual(forwarding_domain, "127.0.0.2")
        self.assertEqual(forwarding_port, 7777)