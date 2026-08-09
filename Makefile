.PHONY: help install extract migrate db ingest api test clean

HTML ?= data/raw/Dashboard_Atleta2.html
DB   ?= data/db.sqlite

help:
	@echo "Alvos:"
	@echo "  install   pip install -r requirements.txt"
	@echo "  extract   HTML=<arquivo>  extrai os dados embutidos -> data/dashboard_extracted.json"
	@echo "  migrate   aplica sql/schema.sql via R (scripts/migrate.R)"
	@echo "  db        recria o SQLite a partir do JSON extraido (scripts/ingest.py)"
	@echo "  api       sobe a API (uvicorn app.api:app --reload)"
	@echo "  test      roda a suite de validacao (pytest)"

install:
	pip install -r requirements.txt

# Etapa opcional: so necessaria para regenerar o JSON a partir do HTML original
# (que nao vai versionado por conter os videos em base64). Requer Node.js.
extract:
	python3 scripts/extract_dashboard.py "$(HTML)" -o data/dashboard_extracted.json

# Caminho R original (aplica somente o schema num banco vazio).
migrate:
	Rscript scripts/migrate.R

# Caminho Python: aplica schema + popula tudo a partir do JSON ja extraido.
db ingest:
	python3 scripts/ingest.py --db "$(DB)"

api:
	uvicorn app.api:app --reload

test:
	python3 -m pytest tests -q || python3 tests/test_analyses.py

clean:
	rm -f data/*.sqlite data/*.sqlite.bak_*
