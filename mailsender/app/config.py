from typing import *

from dotenv import load_dotenv
from pydantic import BaseModel, AnyUrl, FilePath, DirectoryPath, EmailStr

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

class GeneralConfigValid(BaseModel):
    maxAntiquityBeforeDelete: int = 43200
    maxActionsHistoryLength: int = 1000

class AccountValid(BaseModel):
    email: EmailStr
    password: str
    signature_path: Optional[FilePath] = None

class AppSettingsValid(BaseModel):
    general: GeneralConfigValid
    mail_input_dirs: List[DirectoryPath]
    mail_accounts: Dict[str, AccountValid]

class UserSettings(BaseModel):
    url_app_database: AnyUrl
    manifest_extension: str
    app_settings: AppSettingsValid

class ConfigSettings:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = current_dir

            while True:
                if os.path.exists(os.path.join(project_root, ".env")) or \
                   os.path.exists(os.path.join(project_root, ".git")):
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
        self.app_settings_path = str(os.environ["PATH_APP_SETTINGS_JSON"]).format(base_dir=self.base_dir)
        self.vars = UserSettings(
            url_app_database=str(os.environ["URL_APP_DATABASE"]).format(base_dir=self.base_dir),
            manifest_extension=str(os.environ["MANIFEST_EXTENSION"]),
            app_settings=AppSettingsValid.model_validate(load_json(self.app_settings_path))
        )

config = ConfigSettings()