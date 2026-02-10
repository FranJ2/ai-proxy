import hashlib
import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

def calculate_md5(path: str) -> str:
    """计算文件的MD5值"""
    with open(path, 'rb') as f:
        content = f.read()

    return hashlib.md5(content).hexdigest()

class Config:
    def __init__(self, file: Optional[str] = None, lock_file: str = "config.lock") -> None:
        self._config_data : Dict[str,Any] = {}
        self._config_file = file

        if file:
            if Path(file).exists():
                self._load_config(file)
            else:
                self._load_default_config()
                with open(file, "w", encoding='utf-8') as f:
                    json.dump(self._config_data, f, ensure_ascii=False, indent=2)
        else:
            self._load_default_config()

        self._lock_file = lock_file

        if Path(lock_file).exists():
            self._last_md5 = Path(lock_file).read_text(encoding='utf-8')
        else:
            self._last_md5 = ""
            if file:
                Path(lock_file).write_text(calculate_md5(file), encoding='utf-8')

    @staticmethod
    def _get_resource_path(filename: str) -> Path:
        """
        Get the path to a resource file.
        Works both when running directly and when frozen by PyInstaller.
        """

        # 检查是否是 PyInstaller 打包的可执行文件
        meipass = getattr(sys, '_MEIPASS', None)
        if getattr(sys, 'frozen', False) and meipass:
            # 运行于 PyInstaller 打包的可执行文件中
            resource_dir = Path(meipass)
        else:
            # 直接运行 Python 脚本
            resource_dir = Path(__file__).parent
        
        return resource_dir / filename

    def _load_default_config(self) -> None:
        """Load default configuration from embedded default.json."""
        try:
            config_file = self._get_resource_path('default.json')
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
            else:
                print(f"Warning: default.json not found at {config_file}")
                self._config_data = {}
        except Exception as e:
            print(f"Warning: Failed to load default config: {e}")
            self._config_data = {}

    def _load_config(self, file: str) -> None:
        """Load configuration from a file."""
        with open(file, "r", encoding='utf-8') as f:
            self._config_data = json.load(f)

    def get[T](self, key: str, default: Optional[T] = None) -> T:
        return self._config_data.get(key, default)
    
    def api_key(self) -> str:
        return self.get("openai", {}).get("api_key", "")
    
    def base_url(self) -> str:
        return self.get("openai", {}).get("base_url", "https://api.openai.com/v1")

    def models(self) -> List[str]:
        return self.get("openai", {}).get("models", [])
    
    def hosts(self) -> List[str]:
        return self.get("proxy", {}).get("hosts", [])
    
    def modified(self) -> bool:
        if not self._config_file:
            return False

        current_md5 = calculate_md5(self._config_file)
        return current_md5 != self._last_md5
    
    def update_lock(self) -> None:
        if not self._config_file:
            return

        if self.modified():
            self._last_md5 = calculate_md5(self._config_file)
            Path(self._lock_file).write_text(self._last_md5, encoding='utf-8')
    
config = Config('config.json')