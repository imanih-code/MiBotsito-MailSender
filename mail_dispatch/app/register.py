from typing import *

from app.config import config

from functools import lru_cache

import json
import os
import platform
import sys

@lru_cache(maxsize=1)
def get_appdata_path():
    if platform.system() == "Windows":
        return os.getenv('LOCALAPPDATA')
    elif platform.system() == "Darwin":
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        return os.path.join(os.path.expanduser('~'), '.local', 'share')

def ensure_1_process_only():
    app_status_file_path = os.path.join(
        get_appdata_path(), config.vars.appdata_register
    )

    try:
        with open(app_status_file_path, "r") as f:
            api_status_data: Dict[str, Any] = json.load(f)

        if api_status_data.get("is_active"):
            sys.exit(0)

    except (FileNotFoundError, json.JSONDecodeError):
        pass

def update_api_status_file(host, port, is_active):
    app_status_file_path = os.path.join(
        get_appdata_path(), config.vars.appdata_register
    )

    os.makedirs(os.path.dirname(app_status_file_path), exist_ok=True)

    api_status_data = {
        "host": host,
        "port": port,
        "is_active": is_active
    }
    
    with open(app_status_file_path, "w") as f:
        json.dump(api_status_data, f, indent=4)