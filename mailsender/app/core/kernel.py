from typing import *

from app.mail.send import send_email
from app.core.database_handler import DataBaseHandler, MessageStatus
from app.config import config, AppSettingsValid, write_json

from datetime import datetime
from exchangelib import Account, Credentials
from collections import deque

import os

class MailSenderKernel:
    def __init__(self):
        self.db_handler = DataBaseHandler()
        self.opened_accounts: Dict[str, Account] = {}

    def reset_settings(self, new_settings: Dict[str, Any]):
        validated_settings = AppSettingsValid.model_validate(new_settings)
        serialized_settings = validated_settings.model_dump()
        write_json(self.app_settings_path, serialized_settings)
        
        config.reload()

    def load_account(self, account_name):
        if account_name not in self.opened_accounts:
        
            mail_accounts = config.vars.app_settings.mail_accounts
            account = mail_accounts.get(account_name)

            if account is not None:
                credentials = Credentials(username=account.email, password=account.password)
                open_account = Account(account=account.email, credentials=credentials)

                self.opened_accounts["account_name"] = open_account

        return self.opened_accounts.get(account_name)

    def load_new_emails(self):
        manifest_extension = config.vars.manifest_extension
        input_dirs = config.vars.app_settings.mail_input_dirs

        if not input_dirs:
            return

        for input_path in input_dirs:
            if not os.path.isdir(input_path):
                continue

            for filename in os.listdir(input_path):
                if filename.endswith(manifest_extension):
                    manifest_full_path = os.path.join(input_path, filename)
                    try:
                        message_id = self.db_handler.store_new_message(manifest_full_path)
                        os.remove(manifest_full_path)
                    except Exception as error:
                        self.db_handler.log_event(
                            message_id, None,
                            details=f"❌ Error on message manifest handling: {error}"
                        )

    def send_emails(self):
        pending_emails = deque(self.db_handler.get_list_messages(MessageStatus.PENDING))

        while pending_emails:
            message = pending_emails.popleft()
            message_id = message.id
            account_name = message.account_name

            if message.send_at < datetime.now():
                continue

            account = self.load_account(account_name)

            try:
                if account is None:
                    raise ValueError(f"❌ Given mail account '{account_name}' does not exist")
                send_email(account, message)
                self.db_handler.log_event(
                    message_id, None,
                    details="✅ Sending success"
                )
            except Exception as error:
                self.db_handler.log_event(
                    message_id, None,
                    details=error
                )
            finally:
                self.db_handler.update_message_status(message_id, MessageStatus.USED)
