import ipaddress

from typing import List, Union, Tuple
try:
    from mypy_extensions import TypedDict # <=3.7
except ImportError:
    pass
try:
    from typing import TypedDict # type: ignore # >=3.8
except ImportError:
    from mypy_extensions import TypedDict # <=3.7

class LoadBalancingDict(TypedDict):
    frontend: Tuple[str, str]
    backend: List[Tuple[str, str, str]]

class SelfLoadBalancingFrontendDict(TypedDict):
    ipaddress: Union[ipaddress.IPv4Network, ipaddress.IPv6Network, None]
    port: str


class SelfLoadBalancingBackendDict(TypedDict):
    destination_ip: str
    destination_port: str
    access_rate: float
    access_count: int


class SelfLoadBalancingDict(TypedDict):
    frontend: SelfLoadBalancingFrontendDict
    backend: List[SelfLoadBalancingBackendDict]
