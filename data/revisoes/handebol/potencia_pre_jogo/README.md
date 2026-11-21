# Protocolo de potência pré-jogo no handebol (21/11/2026)

- `PROTOCOLO POTENCIA PRE-JOGO HANDEBOL.docx` / `.pdf`: protocolo de 25 minutos (membros inferiores e superiores),
  com ficha de quadra, base de evidência, intervalo e reservas, adaptações, teste na equipe, lacunas, quadro de
  evidências e 26 referências conferidas no Crossref/PubMed.
- Evidência: busca no PubMed em 21/11/2026 (37 registros) e no Crossref; leitura dos resumos. Não é revisão
  sistemática. Doses marcadas como "sugestão prática" não vêm dos estudos.
- `gerar_protocolo_potencia.py`: gera o docx.
- `carga_lape_potencia_pre_jogo.sql` (gerado por `gerar_carga_lape.py`): registra o tema no banco do Lape (tabelas
  `reviews`, `review_searches` e `refs` de `sql/schema.sql`), código `HB-POT-PREJOGO`. Uso:
  `sqlite3 <banco.db> < carga_lape_potencia_pre_jogo.sql`.
