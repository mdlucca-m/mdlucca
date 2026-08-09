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

# Pipeline de video: VIDEO=<arquivo> MODEL=<pose_landmarker.task>
# Extrai frames -> pose (MediaPipe) -> sessao no banco. Requer:
#   pip install mediapipe opencv-python-headless
#   modelo: https://storage.googleapis.com/mediapipe-models/pose_landmarker/
FRAMES ?= data/frames
video:
	@test -n "$(VIDEO)" || (echo "uso: make video VIDEO=arquivo.mkv MODEL=pose_landmarker_full.task"; exit 1)
	mkdir -p $(FRAMES)
	ffmpeg -loglevel error -i "$(VIDEO)" -vsync 0 "$(FRAMES)/f_%04d.png"
	python3 scripts/pose_extract.py "$(FRAMES)" "$(MODEL)" -o data/pose.json --fps 25
	python3 scripts/build_session_from_pose.py --pose data/pose.json --db "$(DB)" --mass $(MASS) --append
MASS ?= 80

# Video anotado (esqueleto + biomecanica ao vivo) pronto para postar.
# SESSION=<id da sessao derivada de video>  BRAND="..."
SESSION ?= 2
BRAND ?= De Lucca Esporte
overlay:
	python3 scripts/render_overlay.py --frames $(FRAMES) --pose data/pose.json \
	  --db "$(DB)" --session $(SESSION) --out data/overlay.mp4 --brand "$(BRAND)"

# Pipeline completo num comando (automacao): VIDEO=.. MODEL=..
pipeline:
	python3 scripts/pipeline.py --video "$(VIDEO)" --model "$(MODEL)" \
	  --athlete "$(BRAND)" --mass $(MASS) --out data/out --legs3d

# Gatilho estilo n8n: observa data/inbox e processa cada video novo
watch:
	MDLUCCA_POSE_MODEL="$(MODEL)" python3 scripts/watch_inbox.py --inbox data/inbox --out data/out --legs3d

# Massa de teste (dados ficticios) para testar cadastro + gerador de relatorio
seed:
	python3 scripts/seed_demo.py --db "$(DB)" --reset --athletes 4 --reps 5 --shares

api:
	uvicorn app.api:app --reload

test:
	python3 -m pytest tests -q || python3 tests/test_analyses.py

clean:
	rm -f data/*.sqlite data/*.sqlite.bak_*
