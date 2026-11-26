"""
Cliente de ingesta: su ÚNICO trabajo es DESCARGAR datos de la API.
No limpia ni guarda nada (eso lo hacen parser.py y storage.py).
"""
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

# Códigos HTTP que suelen ser problemas PASAJEROS: vale la pena reintentar.
# 429 = "demasiadas consultas", 5xx = el servidor tuvo un problema momentáneo.
CODIGOS_TRANSITORIOS = {429, 500, 502, 503, 504}


class DataCollector:
    """
    Gestiona la conexión con la API de productos (DummyJSON).

    Se usa con "async with", que abre la conexión al entrar
    y la cierra sola al salir (aunque haya errores):

        async with DataCollector(base_url="https://dummyjson.com") as collector:
            productos = await collector.obtener_categoria("laptops")
    """

    def __init__(self, base_url: str, timeout: float = 10, max_reintentos: int = 3, delay_ms: int = 0):
        self.base_url = base_url
        self.timeout = timeout                # segundos máximos de espera por respuesta
        self.max_reintentos = max_reintentos  # cuántas veces intentamos ante un error pasajero
        self.delay_ms = delay_ms              # demora artificial de DummyJSON (para simular una API lenta)
        self.client = None

    async def __aenter__(self):
        # Abrimos UNA sesión y la reutilizamos para todas las consultas
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        logger.info(f"Sesión abierta con {self.base_url} (timeout={self.timeout}s)")
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()
        logger.info("Sesión cerrada")

    async def obtener_categoria(self, categoria: str) -> list[dict]:
        """
        Descarga todos los productos de UNA categoría.
        Si algo falla, lo registra en el log y devuelve una lista vacía:
        el programa NUNCA se corta por un error de red.
        """
        url = f"/products/category/{categoria}"
        parametros = {"limit": 0}  # limit=0 -> DummyJSON devuelve todos los productos
        if self.delay_ms > 0:
            parametros["delay"] = self.delay_ms

        for intento in range(1, self.max_reintentos + 1):
            try:
                logger.info(f"Descargando '{categoria}' (intento {intento}/{self.max_reintentos})")
                respuesta = await self.client.get(url, params=parametros)
                respuesta.raise_for_status()  # si el código es 4xx o 5xx, lanza HTTPStatusError
                productos = respuesta.json()["products"]
                logger.info(f"'{categoria}': {len(productos)} productos descargados")
                return productos

            # --- ERRORES TRANSITORIOS: reintentamos ---
            except httpx.TimeoutException:
                logger.warning(f"'{categoria}': la API tardó más de {self.timeout}s (timeout)")
            except httpx.TransportError as error:  # sin internet, DNS, conexión rechazada...
                logger.warning(f"'{categoria}': problema de conexión -> {error!r}")

            except httpx.HTTPStatusError as error:
                codigo = error.response.status_code
                if codigo in CODIGOS_TRANSITORIOS:
                    logger.warning(f"'{categoria}': el servidor respondió {codigo}, reintentando")
                else:
                    # --- ERROR PERMANENTE (404, 401, 403...): reintentar no sirve ---
                    logger.error(f"'{categoria}': error permanente {codigo}. Se saltea esta categoría")
                    return []

            # Esperamos un poco antes de reintentar (1s, 2s, 4s...)
            if intento < self.max_reintentos:
                await asyncio.sleep(2 ** (intento - 1))

        logger.error(f"'{categoria}': no se pudo descargar después de {self.max_reintentos} intentos")
        return []