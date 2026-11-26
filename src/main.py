"""
Script principal de ingesta — TiendaNube Retail (caso de práctica)

Qué hace:
  1. Lee la configuración del archivo .env
  2. Descarga los productos de varias categorías, primero UNA POR UNA
     (secuencial) y después TODAS JUNTAS (en paralelo con asyncio.gather)
  3. Compara los tiempos de las dos formas
  4. Limpia los datos y los guarda en data/productos.csv

Cómo se ejecuta (desde la carpeta del proyecto):
    python src/main.py
"""
import asyncio
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from ingestion.client import DataCollector
from ingestion.parser import limpiar_productos
from ingestion.storage import guardar_csv
from utils.logger import configurar_logging

# Carpeta raíz del proyecto (rutas RELATIVAS: funciona en cualquier compu)
RAIZ = Path(__file__).resolve().parent.parent

logger = logging.getLogger("main")


def cargar_config() -> dict:
    """Lee las variables del archivo .env (nunca escribimos claves en el código)."""
    load_dotenv(RAIZ / ".env")
    return {
        "base_url": os.getenv("API_BASE_URL", "https://dummyjson.com"),
        "categorias": os.getenv("CATEGORIAS", "smartphones,laptops").split(","),
        "timeout": float(os.getenv("TIMEOUT_SEGUNDOS", "10")),
        "max_reintentos": int(os.getenv("MAX_REINTENTOS", "3")),
        "delay_ms": int(os.getenv("DELAY_MS", "0")),
        "nivel_log": os.getenv("LOG_LEVEL", "INFO"),
    }


async def descargar_secuencial(collector: DataCollector, categorias: list[str]) -> list[list[dict]]:
    """Forma LENTA: espera a que termine cada categoría antes de pedir la siguiente."""
    resultados = []
    for categoria in categorias:
        resultados.append(await collector.obtener_categoria(categoria))
    return resultados


async def descargar_en_paralelo(collector: DataCollector, categorias: list[str]) -> list[list[dict]]:
    """Forma RÁPIDA: lanza todos los pedidos a la vez y espera a que vuelvan todos."""
    tareas = [collector.obtener_categoria(categoria) for categoria in categorias]
    return await asyncio.gather(*tareas)


async def main() -> None:
    config = cargar_config()
    configurar_logging(RAIZ / "logs", config["nivel_log"])
    categorias = [c.strip() for c in config["categorias"] if c.strip()]
    logger.info(f"Inicio de la ingesta. Categorías: {categorias}")

    async with DataCollector(
        base_url=config["base_url"],
        timeout=config["timeout"],
        max_reintentos=config["max_reintentos"],
        delay_ms=config["delay_ms"],
    ) as collector:
        # 1) Secuencial (solo para comparar)
        inicio = time.perf_counter()
        await descargar_secuencial(collector, categorias)
        tiempo_secuencial = time.perf_counter() - inicio

        # 2) En paralelo (la que usamos de verdad)
        inicio = time.perf_counter()
        resultados = await descargar_en_paralelo(collector, categorias)
        tiempo_paralelo = time.perf_counter() - inicio

    # Comparamos tiempos solo si se descargó algo: si todo falló, la comparación no dice nada
    if any(resultados):
        logger.info(f"Tiempo secuencial: {tiempo_secuencial:.2f}s | en paralelo: {tiempo_paralelo:.2f}s")
        logger.info(f"La versión en paralelo fue {tiempo_secuencial / tiempo_paralelo:.1f} veces más rápida")
    else:
        logger.warning("No se descargó ninguna categoría: no tiene sentido comparar tiempos")

    # 3) Limpiar y guardar
    filas = []
    for productos in resultados:
        filas.extend(limpiar_productos(productos))
    guardar_csv(filas, RAIZ / "data" / "productos.csv")

    con_datos = sum(1 for productos in resultados if productos)
    logger.info(f"Fin de la ingesta: {con_datos}/{len(categorias)} categorías OK, {len(filas)} productos")


if __name__ == "__main__":
    asyncio.run(main())