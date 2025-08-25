from typing import *
from pydantic import *
from app.core.models import *
from app.core.schemas import *

from app.config import config
from app.mail.signature import list_signatures

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import hashlib
import json

class DataBaseHandler:
    def __init__(self):
        engine = create_engine(config.vars.url_app_database)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def store_config_variable(self, key: str, value: str, 
                              var_type: ConfigVarType, 
                              description: Optional[str] = None):
        db = self.SessionLocal()

        try:
            new_config_var = ConfigVariable(
                key=key,
                value=value,
                var_type=var_type,
                description=description,
            )

            db.add(new_config_var)
            db.commit()
            db.refresh(new_config_var)

            return new_config_var
        except IntegrityError as error:
            pass
        finally:
            db.close()

    def store_new_account(self, account_name: str, email: EmailStr, plain_password: str):
        db = self.SessionLocal()

        try:
            new_account = RegisteredAccount(
                account_name=account_name,
                email=email
            )

            new_account.set_password(plain_password)

            db.add(new_account)
            db.commit()
            db.refresh(new_account)

            return new_account
        except Exception as error:
            self.log_details(
                details=f"❌ Can not save account '{account_name}' (email={email}): {error}"
            )
        finally:
            db.close()

    def store_new_account_signature(self, account_name: str, signature_key: str):
        db = self.SessionLocal()

        account = self.get_registered_account(account_name)

        try:
            new_signature = AccountSignature(
                account_id=account.id,
                signature_key=signature_key,
            )
            db.add(new_signature)
            db.commit()
            db.refresh(new_signature)

            return new_signature
        except Exception as error:
            self.log_details(
                details=f"❌ Can not save signature '{signature_key}' (account?={account.account_name}): {error}"
            )
        finally:
            db.close()

    def store_new_message(self, payload_data: MessageData):
        db = self.SessionLocal()
        try:
            header_dict = payload_data.model_dump()
            serialized_data = json.dumps(header_dict, sort_keys=True)
            
            hasher = hashlib.new("sha256")
            hasher.update(serialized_data.encode("utf-8"))
            hash_value = hasher.hexdigest()

            existing_message = db.query(Message).filter(Message.hash_value == hash_value).first()

            if existing_message:
                return existing_message

            header_dict["hash_value"] = hash_value
            
            new_message = Message(**header_dict)
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            return new_message
            
        except Exception as error:
            self.log_details(
                details=f"❌ Error saving the message: {error}"
            )
            db.rollback()
            return None
        finally:
            db.close()

    def update_config_variable(self, key: str, value: str, 
                               var_type: Optional[ConfigVarType] = None,
                               description: Optional[str] = None):
        db = self.SessionLocal()
        try:
            config_var = db.query(ConfigVariable).filter(ConfigVariable.key == key).first()
            if not config_var:
                self.log_details(
                    details=f"⚠️ Config variable not found (key?={key})"
                )

                return False

            config_var.value = value

            if var_type is not None:
                config_var.var_type = var_type

            if description is not None:
                config_var.description = description

            db.commit()
            return True
        finally:
            db.close()

    def update_registered_account(self, account_name: str, 
                                  email: Optional[EmailStr] = None, 
                                  plain_password: Optional[str] = None):
        db = self.SessionLocal()
        try:
            account = db.query(
                RegisteredAccount
            ).filter(RegisteredAccount.account_name == account_name).first()
            if not account:
                self.log_details(
                    details=f"⚠️ Account not found (name?={account_name})"
                )
                return False

            if email is not None:
                account.email = email

            if plain_password is not None:
                account.set_password(plain_password)

            db.commit()

            return True
        finally:
            db.close()

    def enable_account_signature(self, account_name: str, signature_key: str):
        account = self.get_registered_account(account_name)
        
        db = self.SessionLocal()
        try:
            sig = db.query(AccountSignature).filter_by(
                account_id=account.id,
                signature_key=signature_key
            ).first()

            if sig:
                sig.enabled = True
                db.commit()
                db.refresh(sig)
            return sig
        finally:
            db.close()

    def log_details(self, message_id: Optional[str] = None, details: str = "<Empty log>"):
        db = self.SessionLocal()

        try:
            log = MessageLog(
                message_id=message_id,
                details=details
            )
            db.add(log)
            db.commit()

            max_logs = self.get_config_variable("maxLogHistoryLength").get_var()

            total_logs = db.query(MessageLog).count()
            if total_logs > max_logs:
                excess = total_logs - max_logs
                oldest_logs = (
                    db.query(MessageLog)
                    .order_by(MessageLog.timestamp.asc())
                    .limit(excess)
                    .all()
                )
                for old_log in oldest_logs:
                    db.delete(old_log)
                db.commit()

            return log
        finally:
            db.close()

    def get_config_variable(self, key: str):
        db = self.SessionLocal()
        try:
            return db.query(ConfigVariable).filter(
                ConfigVariable.key == key
            ).first()
        finally:
            db.close()

    def get_list_registered_accounts(self):
        db = self.SessionLocal()
        try:
            query = db.query(
                RegisteredAccount
            ).order_by(RegisteredAccount.created_at)
            
            return query.all()
        finally:
            db.close()

    def get_registered_account(self, account_name: str):
        db = self.SessionLocal()
        try:
            return db.query(RegisteredAccount).filter(
                RegisteredAccount.account_name == account_name
            ).first()
        finally:
            db.close()

    def get_account_signature(self, account_name: str):
        db = self.SessionLocal()
        try:
            return (
                db.query(AccountSignature)
                .join(RegisteredAccount)
                .filter(
                    RegisteredAccount.account_name == account_name,
                    AccountSignature.enabled == True
                )
                .first()
            )
        finally:
            db.close()

    def get_list_signatures(self):
        return list_signatures()

    def get_list_messages(self):
        db = self.SessionLocal()
        try:
            query = db.query(Message).order_by(Message.created_at)
            
            return query.all()
        finally:
            db.close()

    def get_list_logs(self, w: PositiveInt = 50, y: int = 0):
        db = self.SessionLocal()
        try:
            query = db.query(MessageLog).order_by(
                MessageLog.timestamp.desc()
            ).offset(y).limit(w)
            
            results = query.all()

            return list(reversed(results))
        finally:
            db.close()

    def get_message(self, message_id: str):
        db = self.SessionLocal()
        try:
            return db.query(Message).filter(
                Message.id == message_id
            ).first()
        finally:
            db.close()

    def get_logs_for_message(self, message_id: str):
        db = self.SessionLocal()
        try:
            return db.query(MessageLog).filter(
                MessageLog.message_id == message_id
            ).order_by(MessageLog.timestamp).all()
        finally:
            db.close()
