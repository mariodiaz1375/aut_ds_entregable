"""
Parser: TRANSFORMA los datos crudos de la API en filas limpias.
Está separado de la descarga a propósito: si mañana cambia la API,
solo tocamos este archivo (y viceversa).
"""
from datetime import datetime

UMBRAL_STOCK_BAJO = 10  # menos de 10 unidades = alerta de reposición


def limpiar_productos(productos_crudos: list[dict]) -> list[dict]:
    """Se queda solo con las columnas que le sirven al equipo comercial."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = []

    for p in productos_crudos:
        precio = p["price"]
        descuento = p.get("discountPercentage", 0)
        filas.append({
            "id": p["id"],
            "producto": p["title"],
            "categoria": p["category"],
            "marca": p.get("brand", "Sin marca"),  # algunos productos no traen marca
            "precio": precio,
            "descuento_pct": descuento,
            "precio_final": round(precio * (1 - descuento / 100), 2),
            "stock": p["stock"],
            "alerta_stock_bajo": p["stock"] < UMBRAL_STOCK_BAJO,
            "rating": p.get("rating"),
            "fecha_descarga": fecha,
        })
    return filas