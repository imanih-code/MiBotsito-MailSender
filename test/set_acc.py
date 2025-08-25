import requests
import json
from typing import List, Optional, Any

payload = {
    "account_name": "botaper",
    "email": "botaper@cajaarequipa.pe",
    "password": "Ap2r$7hn7750"
}

url = "http://127.0.0.1:62889/set-acc"

print(f"Enviando petición POST a: {url}")
print(f"Con los siguientes datos: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload)

    response.raise_for_status()

    print("\nPetición exitosa! ✅")
    print(f"Código de estado: {response.status_code}")
    print(f"Respuesta del servidor: {response.json()}")

except requests.exceptions.HTTPError as errh:
    print(f"\nError HTTP: {errh}")
except requests.exceptions.ConnectionError as errc:
    print(f"\nError de Conexión: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"\nError de Tiempo de Espera: {errt}")
except requests.exceptions.RequestException as err:
    print(f"\nError Inesperado: {err}")