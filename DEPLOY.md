# Deploy — colocar o sistema online

O mesmo código Python roda local e online. O **motor de análise não muda**;
online só muda o comando de start (usa `$PORT`, sem `--reload`) e o banco fica
num **disco persistente** para não apagar os alunos cadastrados a cada deploy.

## Como o banco é tratado

- O arquivo `data/dashboard_extracted.json` (versionado) é a semente.
- No 1º start, `scripts/start.sh` cria o banco em `MDLUCCA_DB` (ex.:
  `/data/db.sqlite`) rodando `scripts/ingest.py`.
- Nos deploys seguintes, se o banco **já existe** no disco persistente, ele é
  **preservado** — os alunos, sessões e links cadastrados online continuam lá.

---

## Opção A — Render (mais fácil)

1. Suba este repo no GitHub (já está).
2. Em https://render.com → **New → Blueprint** e aponte para o repo. O
   `render.yaml` já configura tudo (Docker, `/health`, disco `/data`).
3. **Licença (obrigatório para os endpoints do produto).** `data/license.key`
   não vai no build (é segredo). No painel da Render → **Environment**, defina:
   - `MDLUCCA_LICENSE` = o token assinado (gere com
     `python3 scripts/make_license.py issue --licensee "..." --plan owner`), **ou**
   - `MDLUCCA_DEV` = `1` na SUA instância dona (libera tudo, sem checagem).
   Sem um dos dois, cadastro/upload/laudo respondem **402** (só `/health`,
   `/license`, `/docs` e `/app` ficam abertos).
4. Deploy. A URL pública sai pronta (ex.: `https://mdlucca-biomecanica.onrender.com`).

Abra:
- `…/app/gerir.html` — cadastro + gerar link
- `…/app/checklist.html` — o que o sistema analisa
- `…/docs` — API

> **Disco persistente exige plano pago (starter).** No plano free (sem disco), o
> banco é recriado a cada deploy — serve para demonstração, mas não guarda os
> alunos entre deploys. Para produção, use o starter (o `render.yaml` já pede).

---

## Opção B — Docker (qualquer VPS/servidor)

```bash
docker build -t mdlucca .
# -v monta um volume persistente para o banco
docker run -d -p 8000:8000 -v mdlucca_data:/data --name mdlucca mdlucca
```
Acesse `http://SEU_IP:8000/app/gerir.html`.

Para HTTPS/domínio, coloque um proxy reverso (Caddy/Nginx) na frente.

---

## Opção C — Fly.io

```bash
fly launch --dockerfile Dockerfile        # gera o fly.toml
fly volumes create dados --size 1         # disco persistente
# no fly.toml: mount source="dados" destination="/data"
fly deploy
```

---

## Variáveis de ambiente

| Var | Default | Uso |
|-----|---------|-----|
| `MDLUCCA_DB` | `/data/db.sqlite` | caminho do banco (no disco persistente) |
| `PORT` | `8000` | porta do servidor (a plataforma injeta) |

## Escala / produção

- SQLite + disco persistente atende bem uso de leitura/análise (1 instância).
- Para multi-instância ou muita escrita concorrente, migrar o `app/db.py` para
  Postgres depois — sem tocar no motor de análise.
