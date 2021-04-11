import ipaddress
import unittest

from zoxy.server import ProxyServer

class ProxyServerForwardingTest(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "0.0.0.0",
            "port": 9999,
            "load_balancing": {
                "frontend": ["127.0.0.1/32", "8080"],
                "backend": [
                    ["127.0.0.1", "9090", "80"],
                    ["127.0.0.1", "9091", "20"],
                ],
            },
        }
        self.proxy_server = ProxyServer(**self.config)

    def tearDown(self):
        self.proxy_server.close()

    def test_get_forwarding(self):
        self.assertDictEqual(self.proxy_server.load_balancing, self.config["load_balancing"])

    def test_set_forwarding(self):
        checker_load_balancing = self.config["load_balancing"]
        checker_load_balancing_setting= {
            "frontend": {
                "ipaddress": "",
                "port": "",
            },
            "backend": [
            ],
        }
        checker_load_balancing_setting["frontend"]["ipaddress"] = ipaddress.ip_network(checker_load_balancing["frontend"][0])
        checker_load_balancing_setting["frontend"]["port"] = checker_load_balancing["frontend"][1]

        for backend_setting in checker_load_balancing["backend"]:
            checker_load_balancing_setting["backend"].append({
                "destination_ip": backend_setting[0],
                "destination_port": backend_setting[1],
                "access_rate": int(backend_setting[2]) / 100,
                "access_count": 0,
            })
        self.assertDictEqual(self.proxy_server._load_balancing, checker_load_balancing_setting)
        self.assertTrue(self.proxy_server._ProxyServer__enable_load_balancing)

        # Clear
        self.proxy_server.load_balancing = {
            "frontend": [],
            "backend": [],
        }
        self.assertDictEqual(self.proxy_server._load_balancing, {
            "frontend": {
                "ipaddress": None,
                "port": "",
            },
            "backend": [
            ],
        })
        self.assertFalse(self.proxy_server._ProxyServer__enable_load_balancing)

    def test_distribute_backend(self):
        backend_access_count = [0, 0]
        backend_access_rate = [0.8, 0.2]
        
        for ans in [0, 1, 0, 0, 0, 0, 1, 0, 0, 0]:
            backend_index = self.proxy_server.distribute_backend(backend_access_count, backend_access_rate)
            self.assertEqual(backend_index, ans)
            backend_access_count[backend_index] += 1

        for _ in range(90):
            backend_index = self.proxy_server.distribute_backend(backend_access_count, backend_access_rate)
            backend_access_count[backend_index] += 1
        self.assertEqual(backend_access_count, [80, 20])

        backend_access_count = [0, 0, 0]
        backend_access_rate = [0.7, 0.2, 0.1]

        for _ in range(100):
            backend_index = self.proxy_server.distribute_backend(backend_access_count, backend_access_rate)
            backend_access_count[backend_index] += 1
        self.assertEqual(backend_access_count, [70, 20, 10])

    def test_get_load_balancing_dest(self):
        forwarding_domain, forwarding_port = self.proxy_server.get_load_balancing_dest("192.0.0.1", 8080)
        self.assertEqual(forwarding_domain, "192.0.0.1")
        self.assertEqual(forwarding_port, 8080)
        for port in [9090, 9091, 9090, 9090, 9090, 9090, 9091, 9090, 9090, 9090]:
            forwarding_domain, forwarding_port = self.proxy_server.get_load_balancing_dest("127.0.0.1", 8080)
            self.assertEqual(forwarding_domain, "127.0.0.1")
            self.assertEqual(forwarding_port, port)

        self.proxy_server.load_balancing = {
                "frontend": ["192.0.0.1/32", "8080"],
                "backend": [
                    ["127.0.0.1", "9091", "20"],
                    ["127.0.0.1", "*", "80"],
                ],
            }
        # Original results do not forwarded
        forwarding_domain, forwarding_port = self.proxy_server.get_load_balancing_dest("127.0.0.1", 8080)
        self.assertEqual(forwarding_domain, "127.0.0.1")
        self.assertEqual(forwarding_port, 8080)

        # New setting
        for port in [9091, 8080, 8080, 8080, 8080, 9091, 8080, 8080, 8080, 8080]:
            forwarding_domain, forwarding_port = self.proxy_server.get_load_balancing_dest("192.0.0.1", 8080)
            self.assertEqual(forwarding_domain, "127.0.0.1")
            self.assertEqual(forwarding_port, port)
