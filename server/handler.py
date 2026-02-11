import http.server
import json
import re
from typing import Any, Dict, Optional, Tuple, TypeVar

import config
from routes import openai
from routes.base_route import BaseRoute, ChatRoute, ModelRoute

chat_routes = [
    ChatRoute("/v1/chat/completions", openai.handle),
    ChatRoute("/chat/completions", openai.handle),
]

model_routes = [
    ModelRoute("/v1/models", openai.models, openai.model),
    ModelRoute("/models", openai.models, openai.model),
]

def format_path(path: str) -> str:
    no_to_much_slash = re.sub(r"/+", "/", path)
    with_prefix = "/" + no_to_much_slash if not no_to_much_slash.startswith("/") else no_to_much_slash
    return with_prefix

def handle_404(request: http.server.BaseHTTPRequestHandler) -> None:
    request.send_response(404)
    request.send_header("Content-type", "application/json")
    request.end_headers()
    request.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

route_type = TypeVar('route_type', bound=BaseRoute)

def match_route(routes: list[route_type], path: str) -> Tuple[Optional[route_type], Optional[str]]:
    for route in routes:
        if path == route.path:
            return route, None
        elif path.startswith(route.path + "/") and len(path) > len(route.path) + 1:
            return route, path[len(route.path) + 1:]
    
    return None, None

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Handle GET request.
        For model routes, return models.
        """
        path = format_path(self.path)

        route, id = match_route(model_routes, path)

        if not route:
            return handle_404(self)

        models = None
        if id:
            models = route.model_handler(id, self)
        else:
            models = route.list_handler(self)

        if not models:
            return handle_404(self)
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(models).encode("utf-8"))
        return
        

    def do_POST(self):
        """
        Handle POST request.
        For chat routes, return response from OpenAI API.
        """
        path = format_path(self.path)
        
        route, _ = match_route(chat_routes, path)
        if not route:
            return handle_404(self)

        # Call handler with request context
        route.handler(self)
