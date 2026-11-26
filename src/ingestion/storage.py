"""
Storage: GUARDA las filas limpias en un archivo CSV dentro de data/.
"""
import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def guardar_csv(filas: list[dict], ruta: Path) -> None:
    if not filas:
        logger.warning("No hay datos para guardar: no se generó el CSV")
        return

    ruta.parent.mkdir(exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=filas[0].keys())
        escritor.writeheader()
        escritor.writerows(filas)
    logger.info(f"Guardado: {ruta} ({len(filas)} filas)")