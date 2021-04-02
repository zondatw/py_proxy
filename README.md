# Zonda Python Proxy

## Quick start for cli

Default server path: 127.0.0.1:8080  
`$ ./zoxy`

### Customize url and port

Example: 0.0.0.0:9999  
`$ ./zoxy -u 0.0.0.0 -p 9999`

### Allowed access

Example:

* 127.0.0.1, mask: 255.255.255.255, port 8080
* 127.0.0.0, mask: 255.255.255.0, port: all

`$ ./zoxy --allowed_access 127.0.1.1 8080 --allowed_access 127.0.0.0/24 *`

### Blocked access

Example:

* 127.0.0.1, mask: 255.255.255.255, port: 8080
* 127.0.0.0, mask: 255.255.255.0, port: all

`$ ./zoxy --blocked_access 127.0.1.1 8080 --blocked_access 127.0.0.0/24 *`

Note: Blocked access setting has higher priority than allowed access.  

### Forwarding

Example:

* 192.168.1.0, mask: 255.255.255.0, port: 1234 to 127.0.0.1, port: 8000
* 0.0.0.0, mask: 0.0.0.0, port: all to 127.0.0.2, port: all

`$ ./zoxy --forwarding 192.168.1.0/24 1234 127.0.0.1 8000 --forwarding 0.0.0.0/0 * 127.0.0.2 *`

## Quick start for program

```python
import zoxy.server

config = {
    "url": "0.0.0.0",
    "port": 9999,
    "allowed_accesses": [
        ["127.0.1.1", "8080"],
        ["127.0.0.0/24", "*"],
    ],
    "blocked_accesses": [
        ["127.0.1.1", "8080"],
        ["127.0.0.0/24", "*"],
    ],
    "forwarding": [
        ["192.168.1.0/24", "1234", "127.0.0.1", "8000"],
        ["0.0.0.0/0", "*", "127.0.0.2", "*"],
    ],
}
zoxy.server.ProxyServer(**config).listen()
```