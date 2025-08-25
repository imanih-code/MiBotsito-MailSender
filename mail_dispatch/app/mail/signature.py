import base64
import os
import re

def list_signatures():
    sig_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Signatures")
    if not os.path.exists(sig_dir):
        print("No signature directory found.")
        return []
    signatures = [f for f in os.listdir(sig_dir) if f.endswith(".htm")]
    return [os.path.splitext(sig)[0] for sig in signatures]

def replace_src_with_cid(html: str, res_folder: str, filename: str) -> str:
    pattern = re.compile(
        rf'(?i)\b((?:src|background)\s*=\s*)([\'"])'
        rf'([^\'"]*?\b{re.escape(res_folder)}[\\/]{re.escape(filename)})'
        rf'([\'"])'
    )

    def repl(m):
        attr_eq, quote_open, _, _ = m.groups()
        return f'{attr_eq}{quote_open}cid:{filename}{quote_open}'

    return pattern.sub(repl, html)

def load_signature(signature_key: str):
    sig_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Signatures")
    sig_file = os.path.join(sig_dir, f"{signature_key}.htm")

    if not os.path.exists(sig_file):
        raise FileNotFoundError(f"Signature '{signature_key}' not found")

    try:
        with open(sig_file, encoding="utf-8") as f:
            signature_html = f.read()
    except UnicodeDecodeError:
        with open(sig_file, encoding="latin-1") as f:
            signature_html = f.read()

    res_folder_path = None
    res_folder_name = None
    if os.path.isdir(sig_dir):
        candidates = [
            d for d in os.listdir(sig_dir)
            if os.path.isdir(os.path.join(sig_dir, d)) and d.lower().startswith(signature_key.lower())
        ]
        if candidates:
            res_folder_name = sorted(candidates, key=len, reverse=True)[0]
            res_folder_path = os.path.join(sig_dir, res_folder_name)

    attachments = []
    if res_folder_path and os.path.exists(res_folder_path):
        for resource_file in os.listdir(res_folder_path):
            if resource_file.lower().endswith((".xml", ".txt", ".htm", ".html")):
                continue

            file_path = os.path.join(res_folder_path, resource_file)
            if not os.path.isfile(file_path):
                continue

            with open(file_path, "rb") as f:
                content_bytes = base64.b64encode(f.read()).decode("utf-8")

            signature_html = replace_src_with_cid(signature_html, res_folder_name, resource_file)

            attachments.append({
                "filename": resource_file,
                "cid": resource_file,
                "content_bytes": content_bytes
            })

    return signature_html, attachments
