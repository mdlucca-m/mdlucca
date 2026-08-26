# Imagem do LAPE: painel, área do integrante e API num contêiner só.
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

# Usuário sem privilégios: o serviço fica exposto na internet.
# O chown precisa vir ANTES do VOLUME — o volume nomeado herda daí o dono.
RUN useradd --create-home --uid 10001 lape \
 && mkdir -p /dados /app/data/raw /app/docs \
 && chown -R lape:lape /dados /app

# O banco vive num volume para sobreviver a cada nova versão da imagem.
VOLUME ["/dados"]
USER lape

EXPOSE 8000

COPY --chown=lape:lape deploy/ ./deploy/
HEALTHCHECK --interval=60s --timeout=6s --start-period=20s \
  CMD ["python3", "/app/deploy/healthcheck.py"]

CMD ["python3", "scripts/lape_agent.py", "api"]
