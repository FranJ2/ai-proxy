"""
Windows helper: generate and install local certs and update hosts file.
"""

import os
import sys
import subprocess
import platform
import logging

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

DEFAULT_HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
 
from cert import utils as cert_utils

def install_certificate_windows(cert_path: str):
    """尝试在Windows上将证书安装到受信任的根存储区。返回True/False。

    不进行交互或等待用户输入，仅记录异常。
    """
    try:
        if not os.path.exists(cert_path):
            logger.error("certificate not found: %s", cert_path)
            return False

        der_cert_path = cert_path
        # 如果是PEM，尝试转换为DER .crt
        try:
            with open(cert_path, 'rb') as f:
                pem_data = f.read()
            cert = x509.load_pem_x509_certificate(pem_data, default_backend())
            der_data = cert.public_bytes(encoding=serialization.Encoding.DER)
            der_cert_path = os.path.splitext(cert_path)[0] + '.crt'
            with open(der_cert_path, 'wb') as f:
                f.write(der_data)
        except Exception:
            logger.debug("PEM->DER conversion failed, trying openssl if available", exc_info=True)
            try:
                der_cert_path = os.path.splitext(cert_path)[0] + '.crt'
                subprocess.run(['openssl', 'x509', '-outform', 'der', '-in', cert_path, '-out', der_cert_path], check=True)
            except Exception:
                # 无法转换，继续使用原始文件
                der_cert_path = cert_path

        # 使用 certutil 安装到当前用户 Root
        try:
            subprocess.run(['certutil', '-user', '-addstore', 'Root', der_cert_path], check=True)
            installed_user = True
        except Exception:
            logger.debug("certutil user addstore failed", exc_info=True)
            installed_user = False

        # 尝试安装到本地计算机存储（需要管理员）
        try:
            subprocess.run(['certutil', '-addstore', 'Root', der_cert_path], check=True)
            installed_machine = True
        except Exception:
            logger.debug("certutil machine addstore failed", exc_info=True)
            installed_machine = False

        return bool(installed_user or installed_machine)
    except Exception:
        logger.exception("install_certificate_windows failed")
        return False

if __name__ == '__main__':
    # 简单命令行入口：生成证书（可选）并尝试安装与更新hosts
    cert_file = 'cert.pem'
    if len(sys.argv) > 1:
        cert_file = sys.argv[1]

    # 仅在Windows上执行安装/hosts更新
    if platform.system() == 'Windows':
        installed = install_certificate_windows(cert_file)
        # 本脚本默认会尝试写入hosts到本机hosts路径
        cert_utils.configure_hosts(['api.openai.com'], path=DEFAULT_HOSTS_PATH)
        sys.exit(0 if installed else 2)
    else:
        logger.info('Not running Windows: no installation performed')
        sys.exit(0)