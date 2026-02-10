"""
证书工具：生成自签名证书、更新 hosts 文件等通用逻辑。

此模块提供跨平台共享函数：`generate_self_signed_cert`、`generate_cert`、`configure_hosts`。
使用时平台模块可以传入平台特有的 subject 字段（如 state/locality）。
"""
import enum
import os
import platform
import shutil
import logging
import datetime
from typing import List, Optional

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID

logger = logging.getLogger(__name__)

def generate_self_signed_cert(
    hosts: List[str],
    key_path: str = "key.pem",
    cert_path: str = "cert.pem",
    pfx_path: str = "certificate.pfx",
    pfx_password: Optional[bytes] = b"password123",
    country: str = "US",
    state: str = "Local",
    locality: str = "Local",
    organization: str = "Local Dev",
):
    """生成自签名证书并写入磁盘，返回包含路径的字典或抛出异常。

    使用时可以传入平台特有的 state/locality 等字段以保留平台差异。
    """
    if not hosts:
        hosts = ["localhost"]

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, "ai-proxy"),
    ])

    san = x509.SubjectAlternativeName([x509.DNSName(h) for h in hosts])

    now = datetime.datetime.now(datetime.timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(san, critical=False)
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # 写入私钥和证书
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    if pfx_password:
        pfx = pkcs12.serialize_key_and_certificates(name=hosts[0].encode('utf-8'),
                                                    key=private_key,
                                                    cert=cert,
                                                    cas=None,
                                                    encryption_algorithm=serialization.BestAvailableEncryption(pfx_password))
        with open(pfx_path, "wb") as f:
            f.write(pfx)

    return {"key": os.path.abspath(key_path), "cert": os.path.abspath(cert_path), "pfx": os.path.abspath(pfx_path) if pfx_password else None}


def generate_cert(hosts: Optional[List[str]] = None, **kwargs):
    """兼容调用点：返回generate_self_signed_cert的结果或None并记录错误。"""
    try:
        return generate_self_signed_cert(hosts or ["localhost"], **kwargs)
    except Exception:
        logger.exception("generate_cert failed")
        return None


def configure_hosts(hosts: List[str], path: str) -> bool:
    """将 hosts 添加到指定的 hosts 文件路径，返回 True/False。会创建备份文件 path.bak。"""
    try:
        if not os.path.exists(path):
            logger.debug("hosts 文件不存在: %s", path)
            return False

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        changed = False
        for h in hosts:
            entry = f"127.0.0.1 {h.strip()}\n"
            if entry not in lines:
                lines.append(entry)
                changed = True

        if changed:
            backup = path + ".bak"
            try:
                shutil.copyfile(path, backup)
            except Exception:
                logger.debug("hosts backup failed", exc_info=True)

            with open(path, "w", encoding="utf-8", errors="ignore") as f:
                f.writelines(lines)

        return True
    except Exception:
        logger.exception("configure_hosts failed")
        return False

class Platform(enum.Enum):
    WINDOWS = 'windows'
    LINUX = 'linux'
    DARWIN = 'darwin'
    UNKNOWN = 'unknown'

def detect_platform() -> Platform:
    """返回平台标识：'windows'|'linux'|'darwin'|'unknown'。"""
    sys = platform.system()
    if sys == 'Windows':
        return Platform.WINDOWS
    if sys == 'Linux':
        return Platform.LINUX
    if sys == 'Darwin':
        return Platform.DARWIN
    return Platform.UNKNOWN

def has_command(cmd: str) -> bool:
    """检查命令是否在 PATH 中可用。"""
    return shutil.which(cmd) is not None