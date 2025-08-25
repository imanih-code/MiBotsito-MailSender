from typing import *

from app.core.database_handler import Message, AccountSignature
from exchangelib import (
    Message as ExMessage,
    HTMLBody,
    Mailbox,
    FileAttachment,
    Account
)
from app.mail.signature import load_signature
from pydantic import BaseModel, field_validator

import base64

class AttachmentManifest(BaseModel):
    content_bytes: str
    filename: str
    cid: Optional[str] = None

    @field_validator("filename")
    def must_have_extension(cls, v: str) -> str:
        if '.' not in v or v.startswith('.') or v.endswith('.'):
            raise ValueError("❌ Filename must have a valid extension")
        return v

    def decoded_content(self) -> bytes:
        try:
            return base64.b64decode(self.content_bytes)
        except Exception:
            raise ValueError("❌ Invalid base64 content in attachment")


def send_message(account: Account, message: Message, signature_key: Optional[AccountSignature] = None):
    msg_html_body: str = message.html_body
    msg_attachments: List[Dict[str, Any]] = message.attachments

    if signature_key is not None:
        signature_html, signature_attachments = load_signature(signature_key.signature_key)

        msg_html_body = f"{msg_html_body}<br><br>{signature_html}"

        msg_attachments += signature_attachments

    email = ExMessage(
        account=account,
        folder=account.sent,
        subject=message.subject,
        body=HTMLBody(msg_html_body),
        to_recipients=[Mailbox(email_address=addr) for addr in message.to_recipients],
        cc_recipients=[Mailbox(email_address=addr) for addr in (message.cc_recipients or [])]
    )

    for att_dict in msg_attachments:
        attachment = AttachmentManifest.model_validate(att_dict)

        filename = attachment.filename
        cid = attachment.cid
        content = attachment.decoded_content()

        file_attachment = FileAttachment(
            name=filename,
            content=content
        )

        if cid:
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
            if filename.lower().endswith(valid_extensions):
                file_attachment.is_inline = True
                file_attachment.content_id = cid
            else:
                raise TypeError(f"❌ File {filename} can not be inline image")

        email.attach(file_attachment)

    try:
        email.send()
    except Exception as e:
        raise SystemError(f"❌ Can not send the email: <{e}>")
