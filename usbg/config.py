import json
from pathlib import Path
from typing import Optional
import os

class Config:
    DEFAULT_CONFIG = {
        'waybar': {
            'update_interval': 2,
            'show_tooltip': True,
            'show_notifications': True,
        },
        'gui': {
            'start_minimized': False,
            'enable_system_tray': True,
        },
        'usbguard': {
            'auto_allow_known': False,
            'notification_on_block': True,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            config_dir = Path(os.environ.get('XDG_CONFIG_HOME', 
                                            Path.home() / '.config'))
            self.config_path = config_dir / 'usbg' / 'config.json'
        
        self.config = self.load()
    
    def load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, section: str, key: str, default=None):
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()
