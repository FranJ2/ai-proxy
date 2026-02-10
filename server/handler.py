import http.server
import json
import re
from typing import Any, Dict

import config
from routes import openai
from routes.base_route import ChatRoute, ModelRoute

chat_routes = [
    ChatRoute("/v1/chat/completions", openai.handle),
    ChatRoute("/chat/completions", openai.handle),
]

model_routes = [
    ModelRoute("/v1/models", openai.models),
    ModelRoute("/models", openai.models),
]

route_map = {}
for route in chat_routes + model_routes:
    route_map[route.path] = route.handler

def format_path(path: str) -> str:
    no_to_much_slash = re.sub(r"/+", "/", path)
    with_prefix = "/" + no_to_much_slash if not no_to_much_slash.startswith("/") else no_to_much_slash
    return with_prefix

def handle_404(request: http.server.BaseHTTPRequestHandler) -> None:
    request.send_response(404)
    request.send_header("Content-type", "application/json")
    request.end_headers()
    request.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Handle GET request.
        For model routes, return models.
        """
        path = format_path(self.path)
        
        handler = route_map.get(path)
        if not handler:
            return handle_404(self)
        
        models = handler(self)
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
        
        handler = route_map.get(path)
        if not handler:
            return handle_404(self)
        
        bytes = self.rfile.read(int(self.headers["Content-Length"]))
        json_data : Dict[str,Any] = json.loads(bytes)
        
        # Call handler with request context
        handler(self, json_data)

    def log_message(self, format: str, *args: Any) -> None:
        pass