from typing import Tuple
import cert.utils
import config
from server.handler import ProxyHandler
from server import server
from cert.install import install_certificate_auto
from cert.utils import Platform, detect_platform, generate_cert
import cert.windows
import cert.linux

PORT = 443

def configure_cert(cert_path: str, key_path: str) -> Tuple[str, str]:
    res = generate_cert(config.config.hosts())
    if not res:
        raise ValueError("generate cert failed")
    
    cert_path = res["cert"]
    key_path = res["key"]
    
    if cert_path and key_path:
        install_certificate_auto(cert_path)

        return cert_path, key_path
    else:
        raise ValueError("cert and key path must be provided")

def update_hosts():
    plat = detect_platform()
    if plat == Platform.WINDOWS:
        cert.utils.configure_hosts(config.config.hosts(), cert.windows.DEFAULT_HOSTS_PATH)
    elif plat == Platform.LINUX:
        cert.utils.configure_hosts(config.config.hosts(), cert.linux.DEFAULT_HOSTS_PATH)
    else:
        raise ValueError(f"unsupported platform: {plat}")
    
def remove_hosts():
    plat = detect_platform()
    if plat == Platform.WINDOWS:
        cert.utils.remove_hosts(config.config.hosts(), cert.windows.DEFAULT_HOSTS_PATH)
    elif plat == Platform.LINUX:
        cert.utils.remove_hosts(config.config.hosts(), cert.linux.DEFAULT_HOSTS_PATH)
    else:
        raise ValueError(f"unsupported platform: {plat}")

if __name__ == "__main__":
    cert_path = 'cert.pem'
    key_path = 'key.pem'

    if config.config.modified():
        cert_path, key_path = configure_cert(cert_path, key_path)
        config.config.update_lock()
    
    update_hosts()

    server.start(PORT, ProxyHandler, certfile=cert_path, keyfile=key_path)

    remove_hosts()