import cert.utils
import config
from server.handler import ProxyHandler
from server import server
from cert.install import install_certificate_auto
from cert.utils import Platform, detect_platform, generate_cert
import cert.windows
import cert.linux

PORT = 443

def configure_cert(cert_path: str, key_path: str):
    generate_cert(config.config.hosts())
    
    if cert_path and key_path:
        install_certificate_auto(cert_path)
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
        configure_cert(cert_path, key_path)
    
    update_hosts()

    server.start(PORT, ProxyHandler, certfile=cert_path, keyfile=key_path)

    remove_hosts()