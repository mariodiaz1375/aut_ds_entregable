# syntax=docker/dockerfile:1
#
# Dockerfile de DESARROLLO - Checkpoint 1 (AI Automation para Data Scientists)
# Lo usan dos cosas: `docker build` (modo imagen) y el Dev Container de VS Code.

# 1) Imagen base: Python 3.11 en su variante "slim" (Debian minimo, ~120 MB).
FROM python:3.11-slim

# 2) Variables de entorno de la imagen.
#    - PYTHONUNBUFFERED=1: los print()/logs salen en tiempo real (clave para agentes).
#    - PYTHONDONTWRITEBYTECODE=1: no genera archivos .pyc dentro del contenedor.
#    - PIP_*: pip sin cache ni aviso de actualizacion (imagen mas chica y limpia).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3) Dependencias del SISTEMA OPERATIVO (no son librerias de Python).
#    build-essential trae gcc/make para compilar paquetes de IA que lo necesiten.
#    Todo en UN solo RUN = una sola capa; el rm final borra el cache de apt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

# 4) Usuario NO root (principio de minimo privilegio).
RUN useradd --create-home --uid 1000 --shell /bin/bash vscode

# 5) Carpeta de trabajo dentro de la imagen.
WORKDIR /app

# 6) Dependencias de Python. Se copia SOLO requirements.txt primero para que
#    Docker reutilice esta capa (cache) mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install -r requirements.txt

# 7) Recien ahora el resto del proyecto (cambia seguido; va al final).
#    Respeta .dockerignore (no entra .env, .git, data/, etc.).
COPY --chown=vscode:vscode . .

# 8) Desde aca todo corre como vscode, no como root.
USER vscode

# 9) Comando por defecto al hacer `docker run` (el Dev Container lo ignora).
CMD ["python", "src/check_env.py"]
