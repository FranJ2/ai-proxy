import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


class Config:
    def __init__(self, file: Optional[str] = None) -> None:
        self._config_data : Dict[str,Any] = {}
        if file:
            if Path(file).exists():
                self._load_config(file)
            else:
                self._load_default_config()
                with open(file, "w", encoding='utf-8') as f:
                    json.dump(self._config_data, f, ensure_ascii=False, indent=2)
        else:
            self._load_default_config()

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
    
config = Config('config.json')