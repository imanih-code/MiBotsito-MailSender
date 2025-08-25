from app.core.models import *
from app.core.schemas import *
from app.json.schemas import *

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.kernel import MailDispatchKernel
from app.register import ensure_1_process_only, update_api_status_file

import uvicorn

kernel = MailDispatchKernel()

@asynccontextmanager
async def lifespan(app: FastAPI): 
    host, port = kernel.get_addr()

    ensure_1_process_only()
    update_api_status_file(host, port, True)
    
    yield
    
    update_api_status_file(host, port, False)

app = FastAPI(title="MailDispatch API", version="1.0", lifespan=lifespan)

@app.get("/")
def check_health():
    return JSONResponse(
        content={"message": "Health check passed", "data": {"health": kernel.check_health()}},
        status_code=200
    )


@app.post("/jit-send-msg")
def send_message(data: MessageData, background_tasks: BackgroundTasks):
    message = kernel.store_message(data)

    background_tasks.add_task(kernel.send_message, message.id)

    return JSONResponse(
        content={"message": "Message stored and sent", "data": {"message_id": message.id}},
        status_code=201
    )


@app.post("/send-msg")
def send_message(data: MessageIdJSON, background_tasks: BackgroundTasks):
    background_tasks.add_task(kernel.send_message, data.message_id)

    return JSONResponse(
        content={"message": "Message sent", "data": {"message_id": data.message_id}},
        status_code=200
    )


@app.post("/store-msg")
def send_message(data: MessageData):
    message = kernel.store_message(data)

    return JSONResponse(
        content={"message": "Message stored successfully", "data": {"message_id": message.id}},
        status_code=201
    )


@app.get("/all-accounts")
def get_all_accounts():
    data = kernel.db_handler.get_list_registered_accounts()
    schemas = [RegisteredAccountSchema.model_validate(acc).model_dump() for acc in data]

    return JSONResponse(
        content={"message": "All accounts retrieved", "data": schemas},
        status_code=200
    )


@app.get("/account")
def get_1_account(data: GetAccountJSON):
    acc = kernel.db_handler.get_registered_account(data.account_name)

    if not acc:
        return JSONResponse(
            content={"message": "Account not found", "data": None},
            status_code=404
        )

    schema = RegisteredAccountSchema.model_validate(acc).model_dump()
    return JSONResponse(
        content={"message": f"Account '{data.account_name}' retrieved", "data": schema},
        status_code=200
    )


@app.get("/all-signatures")
def get_all_accounts():
    data = kernel.db_handler.get_list_signatures()

    return JSONResponse(
        content={"message": "All signatures retrieved", "data": {"signatures": data}},
        status_code=200
    )



@app.get("/all-messages")
def get_all_messages():
    data = kernel.db_handler.get_list_messages()
    schemas = [MessageSchema.model_validate(msg).model_dump() for msg in data]
    
    return JSONResponse(
        content={"message": "All messages retrieved", "data": schemas},
        status_code=200
    )


@app.get("/message")
def get_1_message(data: GetMessageJSON):
    msg = kernel.db_handler.get_message(data.message_id)

    if not msg:
        return JSONResponse(
            content={"message": "Message not found", "data": None},
            status_code=404
        )

    schema = MessageSchema.model_validate(msg).model_dump()
    return JSONResponse(
        content={"message": f"Message '{data.message_id}' retrieved", "data": schema},
        status_code=200
    )


@app.get("/logs")
def get_all_logs(data: GetListLogsJSON):
    data = kernel.db_handler.get_list_logs(w=data.w, y=data.y)
    schemas = [MessageLogSchema.model_validate(msg).model_dump() for msg in data]
    
    return JSONResponse(
        content={"message": "Logs retrieved", "data": schemas},
        status_code=200
    )


@app.post("/upd-confvar")
def update_config_variable(data: PutConfigVariableJSON):
    kernel.db_handler.update_config_variable(data.key, data.value)

    return JSONResponse(
        content={"message": f"Config variable '{data.key}' updated", "data": {"key": data.key, "value": data.value}},
        status_code=200
    )


@app.post("/set-acc")
def set_new_account(data: PostPutNewAccountJSON):
    kernel.db_handler.store_new_account(data.account_name, data.email, data.password)
    
    return JSONResponse(
        content={"message": f"Account '{data.account_name}' created", "data": {"account_name": data.account_name}},
        status_code=201
    )


@app.put("/upd-acc")
def update_account(data: PostPutNewAccountJSON):
    kernel.db_handler.update_registered_account(data.account_name, data.email, data.password)
    
    return JSONResponse(
        content={"message": f"Account '{data.account_name}' updated", "data": {"account_name": data.account_name}},
        status_code=200
    )


@app.post("/set-acc-sign")
def set_account_signature(data: PostPutAccountSignatureJSON):
    kernel.db_handler.store_new_account_signature(data.account_name, data.signature_key)
    
    return JSONResponse(
        content={"message": f"Signature key '{data.signature_key}' set for account '{data.account_name}'", "data": {"account_name": data.account_name, "signature_key": data.signature_key}},
        status_code=200
    )


@app.put("/enable-sign")
def enable_signature_for_account(data: PostPutAccountSignatureJSON):
    kernel.db_handler.enable_account_signature(data.account_name, data.signature_key)
    
    return JSONResponse(
        content={"message": f"Signature key '{data.signature_key}' enabled for account '{data.account_name}'", "data": {"account_name": data.account_name, "signature_key": data.signature_key}},
        status_code=200
    )


@app.post("/format-mdx")
def format_extended_markdown(data: PostFormatMdxJSON):
    mdx = kernel.format_mdx(data.template, data.context)

    return JSONResponse(
        content={"message": "Markdown formatted successfully", "data": {"content": mdx}},
        status_code=200
    )

if __name__ == "__main__":
    host, port = kernel.get_addr()
    uvicorn.run(app, host=host, port=port)