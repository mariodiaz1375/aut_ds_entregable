import logging
from pathlib import Path

# Formato de cada línea del log. Ejemplo de salida:
# 2026-11-16 14:30:05 | INFO    | ingestion.client | Descargando 'laptops'...
FORMATO = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def configurar_logging(carpeta_logs: Path, nivel: str = "INFO") -> None:
    """Se llama UNA sola vez, al arrancar el programa (en main.py)."""
    carpeta_logs.mkdir(exist_ok=True)

    logging.basicConfig(
        level=nivel,
        format=FORMATO,
        datefmt=FORMATO_FECHA,
        handlers=[
            logging.StreamHandler(),  # muestra en la terminal
            logging.FileHandler(carpeta_logs / "ingesta.log", encoding="utf-8"),  # guarda en archivo
        ],
    )
    # httpx loguea cada request por su cuenta; lo silenciamos para que no ensucie
    logging.getLogger("httpx").setLevel(logging.WARNING)
