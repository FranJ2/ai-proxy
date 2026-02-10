import http.server
import json
from typing import Any, Callable, Dict

class BaseRoute[K]:
    def __init__(self, path: str, handler: Callable[[http.server.BaseHTTPRequestHandler], K]) -> None:
        self.path = path
        self.handler = handler

class ChatRoute(BaseRoute[None]):
    def __init__(self, path: str, handler: Callable[[Dict[str,Any],http.server.BaseHTTPRequestHandler], None]) -> None:
        self.handler = handler
        def wrapper(request: http.server.BaseHTTPRequestHandler) -> None:
            content_length = int(request.headers.get('Content-Length', 0))
            body = request.rfile.read(content_length)
            json_data = json.loads(body.decode('utf-8'))
            
            self.handler(json_data, request)
        super().__init__(path, wrapper)

class ModelRoute(BaseRoute[Dict[str,Any]]):
    def __init__(self, path: str, list_handler: Callable[[http.server.BaseHTTPRequestHandler], Dict[str,Any]], model_handler: Callable[[str,http.server.BaseHTTPRequestHandler], Dict[str,Any]]) -> None:
        self.list_handler = list_handler
        self.model_handler = model_handler
        super().__init__(path, list_handler)