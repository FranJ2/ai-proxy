import ssl
import http.server
from typing import Optional, Type


class ReuseAddrHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True


def start(port: int, handler: Type[http.server.BaseHTTPRequestHandler], certfile: Optional[str] = None, keyfile: Optional[str] = None) -> None:
    with ReuseAddrHTTPServer(("", port), handler) as httpd:
        if certfile:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # load_cert_chain accepts keyfile optional if cert contains key
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            proto = 'https'
        else:
            proto = 'http'

        print(f"Serving {proto} on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()