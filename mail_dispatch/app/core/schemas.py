from typing import *
from pydantic import *

from app.core.enums import *
from app.json.schemas import MessageData

from datetime import datetime

class RegisteredAccountSchema(BaseModel):
    id: int
    account_name: str
    email: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def _ser_dt(self, v):
        return v.isoformat() if v else None

class AccountSignatureSchema(BaseModel):
    id: int
    account_id: int
    signature_key: str
    enabled: Optional[bool] = False
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("updated_at")
    def _ser_dt(self, v):
        return v.isoformat() if v else None

class MessageSchema(MessageData):
    account_name: str
    subject: str
    to_recipients: List[str]
    cc_recipients: Optional[List[str]] = None
    attachments: Optional[List[Any]] = None
    html_body: str
    use_signature: Optional[bool] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def _ser_dt(self, v):
        return v.isoformat() if v else None

class MessageLogSchema(BaseModel):
    id: int
    message_id: Optional[str] = None
    details: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("timestamp")
    def _ser_dt(self, v):
        return v.isoformat() if v else None

class ConfigVariableSchema(BaseModel):
    key: str
    value: str
    var_type: ConfigVarType
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("updated_at")
    def _ser_dt(self, v):
        return v.isoformat() if v else None
