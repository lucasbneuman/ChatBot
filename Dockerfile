# Dockerfile para Lucas Benites Multi-Channel Server
FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements_production.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements_production.txt

# Copiar código fuente
COPY app/ ./app/
COPY static/ ./static/
COPY resources/ ./resources/
COPY server_widget.py .
COPY main.py .

# Crear directorio para base de datos
RUN mkdir -p /app/data

# Exponer puertos
EXPOSE 8000

# Variables de entorno por defecto
ENV PORT=8000
ENV HOST=0.0.0.0
ENV GRADIO_SERVER_NAME=0.0.0.0

# Comando de inicio
CMD ["python", "server_widget.py"]