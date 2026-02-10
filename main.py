import config
from server.handler import ProxyHandler
from server import server
from cert.install import install_certificate_auto
from cert.utils import Platform, detect_platform, generate_cert , configure_hosts
import cert.windows
import cert.linux

PORT = 443

if __name__ == "__main__":
    cert_info = generate_cert(config.config.hosts())
    cert_path = cert_info.get('cert') if cert_info else 'cert.pem'
    key_path = cert_info.get('key') if cert_info else 'key.pem'
    install_certificate_auto(cert_path)
    plat = detect_platform()
    if plat == Platform.WINDOWS:
        configure_hosts(config.config.hosts(), cert.windows.DEFAULT_HOSTS_PATH)
    elif plat == Platform.LINUX:
        configure_hosts(config.config.hosts(), cert.linux.DEFAULT_HOSTS_PATH)
    else:
        raise ValueError(f"unsupported platform: {plat}")

    server.start(PORT, ProxyHandler, certfile=cert_path, keyfile=key_path)
