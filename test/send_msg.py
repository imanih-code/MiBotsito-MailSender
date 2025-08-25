import requests
import json
from typing import List, Optional, Any

payload = {
    "account_name": "botaper",
    "subject": "Hello from my API!",
    "to_recipients": ["imamanih@cajaarequipa.pe"],
    "attachments": [
        {"filename": "README.md", "file_path": r"/home/frozonus/Documentos/Proyectos__imanih-dev/Pendings/MiBotsito-MailDispatch/README.md"}
    ],
    "html_body": "<html><body><h1>This is a test email</h1><p>Sent via a Python script 2.</p></body></html>",
    "use_signature": False
}

url = "http://127.0.0.1:55997/send-msg"

try:
    response = requests.post(url, json=payload)

    response.raise_for_status()

    print("Request successful!")
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")