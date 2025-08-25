# MiBotsito-MailDispatch

## Usage
### Write a manifest.md

``` md
---

subject: <Subject of this mail>
account_name: <Who will send this message>
to_recipients: 
    - <List of recipients (Just write each email)>
cc_recipients:
    - <Optional | Same as "to_recipients">

attachments:
    - <Optional | List of attachments for this mail>
    (each attachment is a dictionary):
        - file_path: <Path to the attached file>
        - filename: <Rename of the attached file>
        - cid: <Optional | The cid to refer this attachment (only for images)>
send_at: <Optional | When this mail will be sent>
use_signature: <Optional | As null or False, this boolean flag will omit the signature in this mail>

---

Your email body (HTML, Markdown, Plain text, or everything together)
```

```bash
pyinstaller --noconsole --onefile --name "MiBotsito-MailDispatch" ^
--add-data ".env;." ^
--add-data "mail_dispatch;mail_dispatch" ^
--distpath "MiBotsito-MailDispatch-build" ^
api.py
```
