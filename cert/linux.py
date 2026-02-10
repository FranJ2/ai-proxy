"""
Linux helper: generate self-signed cert, install into system trust store, update /etc/hosts.
"""

import os
import sys
import shutil
import subprocess
import platform
import logging
from typing import List

from cert.utils import configure_hosts

logger = logging.getLogger(__name__)

DEFAULT_HOSTS_PATH = "/etc/hosts"


def install_certificate_linux(cert_path: str):
    """安装证书到系统信任存储。返回 True/False。

    支持常见方案：Debian/Ubuntu (`/usr/local/share/ca-certificates` + `update-ca-certificates`)、
    RHEL/Fedora (`/etc/pki/ca-trust/source/anchors` + `update-ca-trust extract`)、
    或 `trust anchor`。函数不进行交互。
    """
    try:
        if not os.path.exists(cert_path):
            logger.error("certificate not found: %s", cert_path)
            return False

        basename = os.path.basename(cert_path)

        # Debian/Ubuntu path
        deb_target_dir = "/usr/local/share/ca-certificates"
        deb_target = os.path.join(deb_target_dir, os.path.splitext(basename)[0] + '.crt')

        # RHEL/Fedora path
        rhel_target_dir = "/etc/pki/ca-trust/source/anchors"
        rhel_target = os.path.join(rhel_target_dir, basename)

        copied = False

        # 尝试复制到 Debian 风格目录
        try:
            if os.path.isdir(deb_target_dir):
                shutil.copyfile(cert_path, deb_target)
                copied = True
        except Exception:
            logger.debug("copy to deb target failed", exc_info=True)

        # 尝试复制到 RHEL 风格目录
        try:
            if os.path.isdir(rhel_target_dir):
                shutil.copyfile(cert_path, rhel_target)
                copied = True
        except Exception:
            logger.debug("copy to rhel target failed", exc_info=True)

        # 运行系统命令来更新信任存储
        try:
            subprocess.run(["update-ca-certificates"], check=True)
            return True
        except Exception:
            logger.debug("update-ca-certificates failed", exc_info=True)

        try:
            subprocess.run(["update-ca-trust", "extract"], check=True)
            return True
        except Exception:
            logger.debug("update-ca-trust failed", exc_info=True)

        try:
            subprocess.run(["trust", "anchor", cert_path], check=True)
            return True
        except Exception:
            logger.debug("trust anchor failed", exc_info=True)

        return copied
    except Exception:
        logger.exception("install_certificate_linux failed")
        return False


if __name__ == '__main__':
    cert_file = 'cert.pem'
    if len(sys.argv) > 1:
        cert_file = sys.argv[1]

    if platform.system() != 'Linux':
        logger.info('Not running Linux: no installation performed')
        sys.exit(0)

    installed = install_certificate_linux(cert_file)
    configure_hosts(['api.openai.com'], path=DEFAULT_HOSTS_PATH)
    sys.exit(0 if installed else 2)
