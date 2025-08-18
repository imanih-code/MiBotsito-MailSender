from typing import *

from app.core.database_handler import Message
from exchangelib import (
    Message as ExMessage,
    HTMLBody,
    Mailbox,
    FileAttachment,
    Account
)
from pydantic import BaseModel, FilePath, field_validator

import os
import mimetypes

class AttachmentManifest(BaseModel):
    file_path: FilePath
    filename: str
    cid: Optional[str] = None

    @field_validator("filename")
    def must_have_extension(cls, v: str) -> str:
        if '.' not in v or v.startswith('.') or v.endswith('.'):
            raise ValueError("❌ Filename must have a valid extension")
        return v

def send_email(account: Account, message: Message):
    email = ExMessage(
        account=account,
        folder=account.sent,
        subject=message.subject,
        body=HTMLBody(message.html_body),
        to_recipients=[Mailbox(email_address=addr) for addr in message.to_recipients],
        cc_recipients=[Mailbox(email_address=addr) for addr in (message.cc_recipients or [])]
    )

    if message.attachments:
        attachments: List[Dict[str, Any]] = message.attachments

        for att_dict in attachments:
            attachment = AttachmentManifest.model_validate(att_dict)

            file_path = attachment.file_path
            filename = attachment.filename
            cid = attachment.cid

            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"❌ Attachment {file_path} does not exist")

            with open(file_path, "rb") as f:
                content = f.read()

            file_attachment = FileAttachment(
                name=filename,
                content=content
            )

            if cid:
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type and mime_type.startswith("image/"):
                    file_attachment.is_inline = True
                    file_attachment.content_id = cid
                else:
                    raise TypeError(f"❌ File {file_path} can not be inline image")

            email.attach(file_attachment)

    try:
        email.send()
    except Exception as e:
        raise SystemError(f"❌ Can not send the email: <{e}>")
