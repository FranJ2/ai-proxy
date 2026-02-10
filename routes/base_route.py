import http.server
from typing import Any, Callable, Dict

class BaseRoute[T,K]:
    def __init__(self, path: str, handler: Callable[[T,http.server.BaseHTTPRequestHandler], K]) -> None:
        self.path = path
        self.handler = handler

class ChatRoute(BaseRoute[Dict[str,Any],None]):
    pass

class ModelRoute(BaseRoute[None,Dict[str,Any]]):
    pass
