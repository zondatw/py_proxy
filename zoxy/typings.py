from typing import List, Union, Tuple, Any, Optional
from mypy_extensions import TypedDict

class LoadBalancingDict(TypedDict, total=True):
    frontend: Tuple[str, str]
    backend: List[Tuple[str, str, str]]