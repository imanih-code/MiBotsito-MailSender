from typing import *
from pydantic import *

from app.config import config
from app.core.enums import *

from sqlalchemy import (
    event, ForeignKey, Column, 
    Integer, Boolean, String, Text, 
    DateTime, JSON, Enum, func, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

from cryptography.fernet import Fernet
from datetime import datetime

import json
import uuid

Base = declarative_base()

class RegisteredAccount(Base):
    __tablename__ = "registered_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_name = Column(String(50), nullable=False, unique=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(500), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def set_password(self, plain_password: str):
        fernet = Fernet(config.vars.account_secrets_fernet_key.encode())
        self.password = fernet.encrypt(plain_password.encode())

    def get_password(self):
        fernet = Fernet(config.vars.account_secrets_fernet_key.encode())
        return fernet.decrypt(self.password).decode()
    
class AccountSignature(Base):
    __tablename__ = "account_signatures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    account_id = Column(Integer, ForeignKey("registered_accounts.id"), nullable=False)
    account = relationship("RegisteredAccount", backref="signatures")

    signature_key = Column(String(150), nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("account_id", "signature_key", name="uq_account_signature_key"),
    )

    def __repr__(self):
        return f"<AccountSignature(id={self.id}, account_id={self.account_id}, key='{self.signature_key}')>"

@event.listens_for(Session, "before_flush")
def ensure_single_enabled_signature(session, flush_context, instances):
    for obj in session.new.union(session.dirty):
        if isinstance(obj, AccountSignature) and obj.enabled:
            session.query(AccountSignature).filter(
                AccountSignature.account_id == obj.account_id,
                AccountSignature.id != obj.id
            ).update({AccountSignature.enabled: False})

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hash_value = Column(String(64), nullable=False, unique=True)
    account_name = Column(String(150), nullable=False)
    subject = Column(String(512), nullable=False)
    to_recipients = Column(JSON, nullable=False)
    cc_recipients = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    
    html_body = Column(Text, nullable=False)
    use_signature = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    logs = relationship("MessageLog", back_populates="message")

    def __repr__(self):
        return f"<Message(id={self.id}, subject='{self.subject}', status='{self.status}')>"

class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=True)
    details = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    message = relationship("Message", back_populates="logs")

    def __repr__(self):
        return f"<MessageLog(id={self.id}, message_id={self.message_id}, details='{self.details}')>"

class ConfigVariable(Base):
    __tablename__ = "config_variables"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)
    var_type = Column(Enum(ConfigVarType), nullable=False, default=ConfigVarType.STRING)
    description = Column(String(300), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def get_var(self):
        if self.var_type == ConfigVarType.STRING:
            return self.value
        elif self.var_type == ConfigVarType.INTEGER:
            return int(self.value)
        elif self.var_type == ConfigVarType.FLOAT:
            return float(self.value)
        elif self.var_type == ConfigVarType.BOOLEAN:
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.var_type == ConfigVarType.JSON:
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return None
        else:
            return self.value

    def __repr__(self):
        return f"<ConfigVariable(key={self.key}, value={self.value}, type={self.var_type})>"