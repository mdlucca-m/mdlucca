# De Lucca Content Engine

Produto de **geração automatizada de carrosséis científicos** — do dado (metodologia)
à lâmina pronta para postar. O conteúdo é a fonte da verdade; o código renderiza,
verifica as referências e exporta em 1080, 4K e PDF.

---

## 1. O caminho lógico do treino (a "análise robusta")

O conteúdo modela a progressão **do geral ao específico** — a lógica de que toda
especificidade nasce de uma base. Cada etapa eleva o *índice de especificidade* (1→5):

```
 BASE ───────────────────────────────────────────────► COMPETIÇÃO
 (1) Aptidão geral   →  base aeróbia e neuromuscular      · baixa especificidade
 (2) Força de base   →  força máxima relativa
 (3) Conversão       →  potência / RFD (força→potência)
 (4) Específico      →  correspondência dinâmica ao gesto
 (5) Competição      →  tática/decisão + gestão de carga  · alta especificidade
        estrutura no tempo:  BLOCO (acíclicos)  ·  PIRAMIDAL (cíclicos/base)
```

Cada etapa carrega **objetivo · o que treinar · por quê · referência (DOI)**.
Ver `content/caminho.json` — trocar/duplicar esse arquivo gera novos decks.

## 2. Arquitetura (os caminhos que o dado percorre)

```
 content/*.json ─┐
                 ▼
        [verify_refs]  → confirma cada DOI no Crossref (integração)
                 ▼
          [render]     → JSON + base.css + fontes(base64) → HTML autossuficiente
                 ▼
          [export]     → Playwright → PNG 1080 + PNG 4K   → Pillow → PDF
                 ▼
          [pipeline]   → orquestra tudo + report.json
                 ▼
     n8n (automation/) → agenda → gera → publica no Instagram
```

| Módulo | Papel | Dependência |
|---|---|---|
| `engine/render.py` | dados → HTML | nenhuma (stdlib) |
| `engine/verify_refs.py` | DOI → Crossref | nenhuma (stdlib) |
| `engine/export.py` | HTML → PNG/4K/PDF | Playwright · Pillow |
| `engine/pipeline.py` | orquestração (CLI) | — |

## 3. Como rodar

```bash
# uma vez
pip install -r requirements.txt
npx playwright install chromium

# gerar o carrossel "caminho" (HTML + PNG 1080/4K + PDF)
python -m engine.pipeline --content content/caminho.json --out dist/caminho

# flags: --no-verify (pula Crossref) · --no-4k · --no-pdf
```

Saída em `dist/<deck>/`:
- `<deck>.html` — carrossel autossuficiente (fontes embutidas)
- `png-1080/` e `png-4k/` — lâminas
- `<deck>.pdf` — uma lâmina por página
- `report.json` — resumo da execução

### Módulos avulsos
```bash
python -m engine.render   content/caminho.json dist/caminho/caminho.html
python -m engine.verify_refs content/caminho.json
```

## 4. Novo deck
Copie `content/caminho.json`, ajuste `cover/funnel/stages/periodization/refs`
e rode o pipeline apontando `--content` para o novo arquivo. Nenhuma mudança de
código é necessária.

## 5. Automação (n8n)
`automation/delucca-pipeline.n8n.json` importa um fluxo:
**agenda → config → verificar DOIs → gerar (Execute Command chama este pipeline)
→ ler lâminas → publicar no Instagram (Graph API) → notificar.**
Ver `automation/README.md`.

> Nota: em redes que bloqueiam `api.crossref.org` (ex.: sandbox com proxy restrito),
> a verificação retorna "não verificado" sem quebrar o pipeline — rode em um ambiente
> com saída para o Crossref para obter os ✓.
