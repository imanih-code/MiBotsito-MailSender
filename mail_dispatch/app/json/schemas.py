from typing import *
from pydantic import *

class MessageIdJSON(BaseModel):
    message_id: str

class MessageData(BaseModel):
    account_name: str
    subject: str
    to_recipients: List[str]
    cc_recipients: Optional[List[str]] = None
    attachments: Optional[List[Any]] = None
    html_body: str
    use_signature: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class PutConfigVariableJSON(BaseModel):
    key: str
    value: str

class GetAccountJSON(BaseModel):
    account_name: str

class GetMessageJSON(BaseModel):
    message_id: str

class GetListLogsJSON(BaseModel):
    w: PositiveInt
    y: Optional[int] = 0

class PostPutNewAccountJSON(BaseModel):
    account_name: str
    email: EmailStr
    password: str

class PostPutAccountSignatureJSON(BaseModel):
    account_name: str
    signature_key: str

class PostPutJust1FileJSON(BaseModel):
    path: FilePath

class PostPutJust1DirJSON(BaseModel):
    path: DirectoryPath

class PutEnableInputDirJSON(BaseModel):
    manifests_dir_id: int
    enabled: bool

class PostFormatMdxJSON(BaseModel):
    template: str
    context: Dict[str, Any]