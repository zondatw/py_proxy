# Zonda Python Proxy

## Quick start

Default server path: 127.0.0.1:8080  
`$ python main.py`

### Coustomize domain and port

Example: 0.0.0.0:9999  
`$ python main -d 0.0.0.0 -p 9999`

### Allowed access

Example:
 * 127.0.0.1, mask: 255.255.255.255, port 8080
 * 127.0.0.0, mask: 255.255.255.0, port: all

`$ python main.py --allowed_access 127.0.1.1 8080 --allowed_access 127.0.0.0/24 *`


### Blocked access

Example:
 * 127.0.0.1, mask: 255.255.255.255, port 8080
 * 127.0.0.0, mask: 255.255.255.0, port: all

`$ python main.py --blocked_access 127.0.1.1 8080 --blocked_access 127.0.0.0/24 *`

Note: Blocked access setting has higher priority than allowed access.  
