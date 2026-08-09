# Imagem da API biomecanica (leve — so numpy/scipy/fastapi; sem mediapipe/opencv).
# O processamento de video (pose) e feito localmente pelo pipeline, nao no servidor.
FROM python:3.11-slim

WORKDIR /srv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MDLUCCA_DB=/data/db.sqlite

# Dependencias primeiro (cache de camada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo
COPY . .

# O banco vive no volume persistente /data (ver render.yaml / docker run -v)
VOLUME ["/data"]
EXPOSE 8000

CMD ["sh", "scripts/start.sh"]
