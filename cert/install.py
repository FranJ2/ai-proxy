"""
提供自动检测系统并安装证书的工具函数。

此模块会检测当前平台并将证书安装流程委托给相应的模块：
- Windows: `cert.windows.install_certificate_windows`
- Linux: `cert.linux.install_certificate_linux`
- macOS: 使用 `security` 命令将证书加入系统信任（如果可用）

所有操作均尽量以无交互方式执行并返回布尔结果与诊断信息。
"""
import os
import subprocess
import logging
from typing import Tuple

from cert.utils import Platform, detect_platform, has_command

logger = logging.getLogger(__name__)

def install_on_macos(cert_path: str) -> Tuple[bool, str]:
    """尝试在 macOS 上通过 `security` 命令安装证书到 System 根证书（需要管理员）。"""
    if not os.path.exists(cert_path):
        return False, f"certificate not found: {cert_path}"

    if not has_command('security'):
        return False, 'security command not available'

    # 尝试将证书添加到系统 keychain（会要求管理员权限）
    try:
        subprocess.run(['sudo', 'security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', cert_path], check=True)
        return True, 'installed via security'
    except subprocess.CalledProcessError as e:
        logger.debug('macOS security command failed', exc_info=True)
        return False, f'security failed: {e}'
    except Exception:
        logger.exception('install_on_macos failed')
        return False, 'install_on_macos exception'


def install_certificate_auto(cert_path: str) -> Tuple[bool, str]:
    """自动检测平台并尝试安装证书，返回 (成功?, 描述)。"""
    plat = detect_platform()

    try:
        if plat == Platform.WINDOWS:
            # 延迟导入，避免在非目标平台导入 Windows 特定模块时出错
            from cert.windows import install_certificate_windows

            ok = install_certificate_windows(cert_path)
            return bool(ok), 'windows installer result' if ok else 'windows installer failed'

        if plat == Platform.LINUX:
            from cert.linux import install_certificate_linux

            ok = install_certificate_linux(cert_path)
            return bool(ok), 'linux installer result' if ok else 'linux installer failed'

        if plat == Platform.DARWIN:
            return install_on_macos(cert_path)

        return False, f'unsupported platform: {plat}'
    except Exception:
        logger.exception('install_certificate_auto failed')
        return False, 'exception during install'

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('usage: python -m cert.install /path/to/cert.pem')
        raise SystemExit(2)

    cert_file = sys.argv[1]
    ok, msg = install_certificate_auto(cert_file)
    print(msg)
    raise SystemExit(0 if ok else 2)
