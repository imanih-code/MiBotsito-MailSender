from typing import *
from pydantic import *

from dotenv import load_dotenv
from pydantic import BaseModel

import json
import os
import sys

def load_json(filepath: str):
    with open(filepath, 'r') as file:
        return json.load(file)
    
def write_json(filepath: str, data: Dict[str, Any]):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

class EnvironmentVariables(BaseModel):
    app_host: IPvAnyAddress
    appdata_register: str
    account_secrets_fernet_key: str
    url_app_database: str

class ConfigSettings:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = current_dir

            while True:
                if os.path.exists(os.path.join(project_root, ".env")) or \
                   os.path.exists(os.path.join(project_root, ".exe")):
                    self.base_dir = project_root
                    break
                parent_dir = os.path.dirname(project_root)
                if parent_dir == project_root:
                    self.base_dir = current_dir
                    break
                project_root = parent_dir
        dotenv_path = os.path.join(self.base_dir, ".env")
        load_dotenv(dotenv_path, override=True)
        
        self.reload()

    def reload(self):
        self.vars = EnvironmentVariables(
            app_host=str(os.environ["APP_HOST"]),
            appdata_register=str(os.environ["APPDATA_PATH"]),
            account_secrets_fernet_key=str(os.environ["ACCOUNT_SECRETS_FERNET_KEY"]),
            url_app_database=str(os.environ["URL_APP_DATABASE"]).format(base_dir=self.base_dir)
        )

config = ConfigSettings()