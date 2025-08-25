from typing import *
from app.core.schemas import *

from app.mail.send import send_message
from app.core.database_handler import DataBaseHandler, ConfigVarType
from app.markdown.format import render_mdx
from app.config import config

from datetime import datetime
from exchangelib import Account, Credentials

import socket

def find_available_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class MailDispatchKernel:
    def __init__(self):

        self.host = str(config.vars.app_host)
        self.port = int(find_available_port())

        self.db_handler = DataBaseHandler()

        self.set_initial_config_vars()

        self.opened_accounts: Dict[str, Account] = {}

    def get_addr(self):
        return self.host, self.port

    def check_health(self) -> Dict[str, Any]:
        health = {
            "database": False,
            "opened_accounts": len(self.opened_accounts),
            "timestamp": datetime.now().isoformat()
        }

        try:
            _ = self.db_handler.get_list_registered_accounts()
            health["database"] = True
        except Exception:
            health["database"] = False

        health["status"] = "ok" if (health["database"]) else "error"
        return health

    def set_initial_config_vars(self):
        self.db_handler.store_config_variable(
            "maxLogHistoryLength", "10000", ConfigVarType.INTEGER, 
            "Límite de registros en el historial de logs"
        )
        self.db_handler.store_config_variable(
            "maxMsgAntiquity", "43200", ConfigVarType.INTEGER, 
            "Límite de longevidad del mensaje mas antiguo guardado"
        )
    
    def load_account(self, account_name: str):
        open_account = self.opened_accounts.get(account_name)

        if open_account is None:
            account = self.db_handler.get_registered_account(
                account_name=account_name
            )

            if account is None:
                return None

            credentials = Credentials(
                username=account.email, 
                password=account.get_password()
            )
            open_account = Account(
                primary_smtp_address=account.email, 
                credentials=credentials, 
                autodiscover=True
            )

            self.opened_accounts[account_name] = open_account

        return open_account
    
    def get_message(self, message_id: str) -> MessageData:
        try:
            message = self.db_handler.get_message(message_id)
            if not message:
                raise ValueError(f"❌ No message found with ID '{message_id}'")
            
            self.db_handler.log_details(
                message_id=message_id,
                details="✅ Message retrieved from database"
            )

            return message

        except Exception as error:
            self.db_handler.log_details(
                message_id=message_id,
                details=error
            )
            raise

    def store_message(self, payload_data: MessageData):
        try:
            account_name = payload_data.account_name
            account = self.load_account(account_name)

            message = self.db_handler.store_new_message(payload_data)

            if account is None:
                raise ValueError(f"❌ Given mail account '{account_name}' does not exist")
            
            self.db_handler.log_details(
                message_id=message.id, 
                details="✅ Message stored for future dispatch"
            )

            return message
        
        except Exception as error:
            self.db_handler.log_details(
                message_id=message.id, 
                details=error
            )


    def send_message(self, message_id: str):
        try:
            message = self.db_handler.get_message(message_id)

            if message is None:
                raise ValueError(f"❌ Given message id '{message_id}' does not exist in the database")

            account_name = message.account_name
            account = self.load_account(account_name)

            signature_key = None

            if message.use_signature:
                signature_key = self.db_handler.get_account_signature(account_name)

            if account is None:
                raise ValueError(f"❌ Given mail account '{account_name}' does not exist")
            
            send_message(account, message, signature_key)

            self.db_handler.log_details(
                message_id=message.id, 
                details="✅ Sending success"
            )
        except Exception as error:
            self.db_handler.log_details(
                message_id=message.id, 
                details=error
            )

    def format_mdx(self, template: str, context: Dict[str, Any]):
        return render_mdx(template, context)