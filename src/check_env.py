"""Verificacion del entorno (Checkpoint 1).

Imprime la version de Python, confirma si se ejecuta dentro de un contenedor
y comprueba que las variables de entorno esperadas esten accesibles.

Uso (desde la raiz del proyecto, dentro del contenedor):
    python src/check_env.py
"""
from __future__ import annotations

import getpass
import os
import platform
import socket
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv es opcional: sin el, solo se usa os.environ
    load_dotenv = None

# Raiz del proyecto calculada de forma RELATIVA a este archivo (sin rutas absolutas).
ROOT = Path(__file__).resolve().parent.parent

# Variables que declara .env.example y cuales son secretas (no se imprimen).
REQUIRED_VARS = ["OPENAI_API_KEY", "MLFLOW_TRACKING_URI", "DATABASE_URL"]
SECRET_VARS = {"OPENAI_API_KEY", "DATABASE_URL"}
PLACEHOLDERS = {"tu_api_key_aqui", "tu_url_aqui"}


def running_in_container() -> bool:
    """Docker crea el archivo /.dockerenv dentro de cada contenedor."""
    return Path("/.dockerenv").exists()


def describe(name: str, value: str | None) -> tuple[str, str]:
    """Devuelve (estado, detalle) sin exponer valores secretos."""
    if not value:
        return "FALTA", "no esta definida"
    if value in PLACEHOLDERS:
        return "AVISO", "sigue con el valor de ejemplo; completala en tu .env"
    if name in SECRET_VARS:
        return "OK", f"definida ({len(value)} caracteres, valor oculto)"
    return "OK", value


def main() -> int:
    # override=False: una variable ya definida en el entorno NO se pisa con el .env
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env", override=False)

    print("=" * 60)
    print("VERIFICACION DE ENTORNO")
    print("=" * 60)
    print(f"Python        : {sys.version.split()[0]}")
    print(f"Ejecutable    : {sys.executable}")
    print(f"Sistema       : {platform.system()} {platform.machine()}")
    print(f"Hostname      : {socket.gethostname()}")
    print(f"Usuario       : {getpass.getuser()}")
    print(f"Directorio    : {Path.cwd()}")
    print(f"En contenedor : {'SI' if running_in_container() else 'NO'}")
    print("-" * 60)

    missing = 0
    for name in REQUIRED_VARS:
        status, detail = describe(name, os.environ.get(name))
        print(f"[{status:<5}] {name:<20} {detail}")
        if status == "FALTA":
            missing += 1

    print("-" * 60)
    if missing:
        print(f"Resultado: FALLO ({missing} variable(s) sin definir)")
        return 1
    print("Resultado: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
