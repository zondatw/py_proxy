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
                ["127.0.1.1/32", "8080"],
                ["127.0.2.0/24", "1234"],
                ["127.0.0.0/24", "*"],
            ],
            "blocked_accesses": [
                ["192.0.1.1/32", "8080"],
                ["192.0.2.0/24", "1234"],
                ["192.0.0.0/24", "*"],
            ],
        }
        self.proxy_server = ProxyServer(**self.config)

    def tearDown(self):
        self.proxy_server.close()

    def test_get_access_table(self):
        access_list = [
            ["200.0.1.1/32", "8080"],
            ["200.0.2.0/24", "1234"],
            ["200.0.0.0/24", "*"],
        ]
        checker_access_table = defaultdict(list)
        for ip, port in access_list:
            checker_access_table[ipaddress.ip_network(ip)].append(str(port))
        access_table = self.proxy_server._ProxyServer__get_access_table(access_list)
        self.assertDictEqual(access_table, checker_access_table)

    def test_get_accesses_list(self):
        chcker_access_list = [
            ["200.0.1.1/32", "8080"],
            ["200.0.2.0/24", "1234"],
            ["200.0.0.0/24", "*"],
        ]
        checker_access_table = defaultdict(list)
        for ip, port in chcker_access_list:
            checker_access_table[ipaddress.ip_network(ip)].append(str(port))
        access_table = self.proxy_server._ProxyServer__get_access_table(chcker_access_list)
        access_list = self.proxy_server._ProxyServer__get_accesses_list(access_table)
        self.assertListEqual(access_list, chcker_access_list)

    def test_get_allowed_accesses(self):
        self.assertListEqual(self.proxy_server.allowed_accesses, self.config["allowed_accesses"])

    def test_set_allowed_accesses(self):
        allowed_access_list = self.config["allowed_accesses"]
        checker_allowed_accesses = defaultdict(list)
        for ip, port in allowed_access_list:
            checker_allowed_accesses[ipaddress.ip_network(ip)].append(str(port))
        self.proxy_server.allowed_accesses = allowed_access_list
        self.assertDictEqual(self.proxy_server._allowed_accesses, checker_allowed_accesses)
        self.assertTrue(self.proxy_server._ProxyServer__enable_allowed_access)

        # Clear
        self.proxy_server.allowed_accesses = []
        self.assertDictEqual(self.proxy_server._allowed_accesses, {})
        self.assertFalse(self.proxy_server._ProxyServer__enable_allowed_access)

    def test_get_blocked_accesses(self):
        self.assertListEqual(self.proxy_server.blocked_accesses, self.config["blocked_accesses"])

    def test_set_blocked_accesses(self):
        blocked_access_list = self.config["blocked_accesses"]
        checker_blocked_accesses = defaultdict(list)
        for ip, port in blocked_access_list:
            checker_blocked_accesses[ipaddress.ip_network(ip)].append(str(port))
        self.proxy_server.blocked_accesses = blocked_access_list
        self.assertDictEqual(self.proxy_server._blocked_accesses, checker_blocked_accesses)
        self.assertTrue(self.proxy_server._ProxyServer__enable_blocked_access)

        # Clear
        self.proxy_server.blocked_accesses = []
        self.assertDictEqual(self.proxy_server._blocked_accesses, {})
        self.assertFalse(self.proxy_server._ProxyServer__enable_blocked_access)

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

        self.proxy_server.allowed_accesses = [
            ["111.0.1.1/32", "8080"],
            ["111.0.2.0/24", "1234"],
            ["111.0.0.0/24", "*"],
        ]
        # Original result from True to False
        result = self.proxy_server.is_connection_allowed("127.0.1.1", 8080)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("127.0.2.1", 1234)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("127.0.0.1", 1234)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("127.0.0.50", 1111)
        self.assertFalse(result)
        # New setting
        result = self.proxy_server.is_connection_allowed("111.0.1.1", 8080)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_allowed("111.0.1.1", 8001)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("111.0.2.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_allowed("111.0.2.50", 1111)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_allowed("111.0.0.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_allowed("111.0.0.50", 1111)
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

        self.proxy_server.blocked_accesses = [
            ["111.0.1.1/32", "8080"],
            ["111.0.2.0/24", "1234"],
            ["111.0.0.0/24", "*"],
        ]
        # Original result from True to False
        result = self.proxy_server.is_connection_blocked("192.0.1.1", 8080)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("192.0.2.1", 1234)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("192.0.0.1", 1234)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("192.0.0.50", 1111)
        self.assertFalse(result)
        # New setting
        result = self.proxy_server.is_connection_blocked("111.0.1.1", 8080)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_blocked("111.0.1.1", 8001)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("111.0.2.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_blocked("111.0.2.50", 1111)
        self.assertFalse(result)
        result = self.proxy_server.is_connection_blocked("111.0.0.1", 1234)
        self.assertTrue(result)
        result = self.proxy_server.is_connection_blocked("111.0.0.50", 1111)
        self.assertTrue(result)