import socketserver
from typing import Type


class ReuseAddrServer(socketserver.TCPServer):
    allow_reuse_address = True

def start(port: int, handler: Type[socketserver.BaseRequestHandler]) -> None:
    with ReuseAddrServer(("", port), handler) as httpd:
        print(f"Serving at port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()