from typing import *

from app.config import config

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import frontmatter
import hashlib
import json
import markdown

import enum
import uuid

Base = declarative_base()

class MessageStatus(enum.Enum):
    PENDING = "pending"
    USED = "used"

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hash_value = Column(String(64), nullable=False, unique=True)
    account_name = Column(String(150), nullable=False)
    subject = Column(String(512), nullable=False)
    to_recipients = Column(JSON, nullable=False)
    cc_recipients = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    constraints = Column(JSON, nullable=True)
    
    html_body = Column(Text, nullable=False)
    read_from_path = Column(String(1024), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    send_at = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Message(id={self.id}, subject='{self.subject}', status='{self.status}')>"

class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(36), nullable=True)
    manifest_path = Column(String(1024), nullable=True)
    event = Column(String(512), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<MessageLog(id={self.id}, message_id={self.message_id}, event='{self.event}')>"

class DataBaseHandler:
    def __init__(self):
        engine = create_engine(config.vars.url_app_database)
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def store_new_message(self, manifest_path: str):
        def calculate_hash(post: frontmatter.Post):
            hasher = hashlib.new("sha256")
            metadata_serialized = json.dumps(
                post.metadata,
                sort_keys=True,
                ensure_ascii=False
            )
            hasher.update(metadata_serialized.encode("utf-8"))
            hasher.update(b'---')
            content_encoded = post.content.encode("utf-8")
            hasher.update(content_encoded)
            return hasher.hexdigest()
        
        manifest = frontmatter.load(manifest_path)
        hash_value = calculate_hash(manifest)

        header = manifest.metadata
        html_body = markdown.markdown(manifest.content)

        db = self.SessionLocal()

        try:
            header_dict = {
                **header,
                "hash_value": hash_value,
                "read_from_path": manifest_path,
                "html_body": html_body
            }
            new_message = Message(**header_dict)
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            return new_message.id
        except TypeError as e:
            self.log_event(
                manifest_path=manifest_path,
                details=f"⚠️ Invalid fields in header: {e}"
            )
        finally:
            db.close()

    def update_message_status(self, message_id: str, new_status: MessageStatus):
        db = self.SessionLocal()
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            if not message:
                return False

            message.status = new_status
            db.commit()
            return True
        finally:
            db.close()

    def log_event(self, message_id: Optional[str] = None, manifest_path: Optional[str] = None, event: str = ""):
        if not message_id and not manifest_path:
            return None

        db = self.SessionLocal()

        try:
            log = MessageLog(
                message_id=message_id,
                manifest_path=manifest_path,
                event=event
            )
            db.add(log)
            db.commit()

            max_logs = config.vars.app_settings.general.maxActionsHistoryLength

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

    def get_list_messages(self, status: Optional[MessageStatus] = None):
        db = self.SessionLocal()
        try:
            query = db.query(Message).order_by(Message.created_at)
            
            if status is not None:
                query = query.filter(Message.status == status)

            return query.all()
        finally:
            db.close()

    def get_message(self, message_id: str):
        db = self.SessionLocal()
        try:
            return db.query(Message).filter(Message.id == message_id).first()
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
