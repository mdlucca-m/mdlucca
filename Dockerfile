# Imagem do LAPE: painel + área do integrante + API, num contêiner só.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LAPE_HOST=0.0.0.0 \
    LAPE_PORT=8000 \
    LAPE_DB=/dados/db.sqlite \
    LAPE_BEHIND_HTTPS=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sql/ ./sql/
COPY scripts/ ./scripts/
COPY data/geo/ ./data/geo/

# O banco vive num volume para sobreviver a cada nova versão da imagem.
VOLUME ["/dados"]
RUN mkdir -p /dados /app/data/raw /app/docs

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=6s --start-period=20s \
  CMD python3 -c "import urllib.request,os,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('LAPE_PORT','8000')+'/api/health', timeout=5).status==200 else 1)"

CMD ["python3", "scripts/lape_agent.py", "api"]
