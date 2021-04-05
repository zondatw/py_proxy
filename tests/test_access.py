import ipaddress
import unittest
from collections import defaultdict

from zoxy.server import ProxyServer

class ProxyServerAccessTest(unittest.TestCase):
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
        }
        self.proxy_server = ProxyServer(**self.config)

    def tearDown(self):
        self.proxy_server.close()

    def test_get_access_table(self):
        access_list = [
            ["200.0.1.1", "8080"],
            ["200.0.2.0/24", "1234"],
            ["200.0.0.0/24", "*"],
        ]
        checker_access_table = defaultdict(list)
        for ip, port in access_list:
            checker_access_table[ipaddress.ip_network(ip)].append(str(port))
        access_table = self.proxy_server._ProxyServer__get_init_access_table(access_list)
        self.assertDictEqual(access_table, checker_access_table)

    def test_init_allowed_accesses(self):
        allowed_access_list = self.config["allowed_accesses"]
        checker_allowed_accesses = defaultdict(list)
        for ip, port in allowed_access_list:
            checker_allowed_accesses[ipaddress.ip_network(ip)].append(str(port))
        allowed_access = self.proxy_server._ProxyServer__init_allowed_accesses(allowed_access_list)
        self.assertDictEqual(allowed_access, checker_allowed_accesses)
        self.assertDictEqual(self.proxy_server.allowed_accesses, checker_allowed_accesses)

    def test_init_blocked_accesses(self):
        blocked_access_list = self.config["blocked_accesses"]
        checker_blocked_accesses = defaultdict(list)
        for ip, port in blocked_access_list:
            checker_blocked_accesses[ipaddress.ip_network(ip)].append(str(port))
        blocked_access = self.proxy_server._ProxyServer__init_blocked_accesses(blocked_access_list)
        self.assertDictEqual(blocked_access, checker_blocked_accesses)
        self.assertDictEqual(self.proxy_server.blocked_accesses, checker_blocked_accesses)

    def test_is_testee_in_access_table(self):
        access_list = [
            ["200.0.1.1", "8080"],
            ["200.0.2.0/24", "1234"],
            ["200.0.0.0/24", "*"],
        ]
        checker_access_table = defaultdict(list)
        for ip, port in access_list:
            checker_access_table[ipaddress.ip_network(ip)].append(str(port))
        result = self.proxy_server.is_testee_in_access_table(checker_access_table, "200.0.1.1", 8080)
        self.assertTrue(result)
        result = self.proxy_server.is_testee_in_access_table(checker_access_table, "200.0.1.1", 8001)
        self.assertFalse(result)
        result = self.proxy_server.is_testee_in_access_table(checker_access_table, "200.0.2.50", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_testee_in_access_table(checker_access_table, "200.0.2.50", 1111)
        self.assertFalse(result)
        result = self.proxy_server.is_testee_in_access_table(checker_access_table, "200.0.0.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_testee_in_access_table(checker_access_table, "200.0.0.50", 1111)
        self.assertTrue(result)

    def test_is_connection_allowed(self):
        result = self.proxy_server.is_connection_allowed("127.0.1.1", 8080)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_allowed("127.0.1.1", 8001)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("127.0.2.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_allowed("127.0.2.50", 1111)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("127.0.0.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_allowed("127.0.0.50", 1111)
        self.assertTrue(result)

    def test_is_connection_blocked(self):
        result = self.proxy_server.is_connection_blocked("192.0.1.1", 8080)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_blocked("192.0.1.1", 8001)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("192.0.2.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_blocked("192.0.2.50", 1111)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("192.0.0.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_blocked("192.0.0.50", 1111)
        self.assertTrue(result)