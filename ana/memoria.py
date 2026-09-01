# -*- coding: utf-8 -*-
"""Memória da Ana: o pouco que ela precisa lembrar entre uma sessão e outra.

Não é histórico de conversa. É o que o pesquisador já decidiu e não quer
repetir: a unidade de análise canônica, o periódico-alvo, o padrão de escrita,
o número do CAAE quando ele existir. Cada lembrança tem escopo, data e origem.
"""
from __future__ import annotations
import os, sqlite3, datetime
from pathlib import Path

RAIZ = Path(os.environ.get("ANA_RAIZ") or Path(__file__).resolve().parent)
BANCO = Path(os.environ.get("ANA_MEMORIA") or RAIZ / "memoria.sqlite")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS lembranca(
  chave     TEXT PRIMARY KEY,
  valor     TEXT NOT NULL,
  escopo    TEXT NOT NULL DEFAULT 'geral',
  origem    TEXT,
  criada    TEXT NOT NULL,
  atualizada TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lembranca_escopo ON lembranca(escopo);
CREATE VIRTUAL TABLE IF NOT EXISTS lembranca_busca
  USING fts5(chave, valor, escopo, content='lembranca', content_rowid='rowid');
"""

def conectar(somente_leitura: bool = False) -> sqlite3.Connection:
    if somente_leitura and BANCO.exists():
        cx = sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True)
    else:
        BANCO.parent.mkdir(parents=True, exist_ok=True)
        cx = sqlite3.connect(BANCO)
        cx.executescript(ESQUEMA)
    cx.row_factory = sqlite3.Row
    return cx

def _agora() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")

def lembrar(chave: str, valor: str, escopo: str = "geral", origem: str | None = None) -> str:
    chave = chave.strip().lower()
    if not chave or not valor.strip():
        return "lembrança vazia: informe chave e valor."
    with conectar() as cx:
        antiga = cx.execute("SELECT valor FROM lembranca WHERE chave=?", (chave,)).fetchone()
        agora = _agora()
        cx.execute(
            "INSERT INTO lembranca(chave,valor,escopo,origem,criada,atualizada)"
            " VALUES(?,?,?,?,?,?)"
            " ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor, escopo=excluded.escopo,"
            " origem=excluded.origem, atualizada=excluded.atualizada",
            (chave, valor.strip(), escopo, origem, agora, agora))
        cx.execute("INSERT INTO lembranca_busca(lembranca_busca) VALUES('rebuild')")
    if antiga and antiga["valor"] != valor.strip():
        return f"lembrança «{chave}» atualizada.\n  antes: {antiga['valor']}\n  agora: {valor.strip()}"
    return f"lembrança «{chave}» guardada no escopo «{escopo}»."

def esquecer(chave: str) -> str:
    with conectar() as cx:
        n = cx.execute("DELETE FROM lembranca WHERE chave=?", (chave.strip().lower(),)).rowcount
        cx.execute("INSERT INTO lembranca_busca(lembranca_busca) VALUES('rebuild')")
    return f"lembrança «{chave}» apagada." if n else f"não havia lembrança «{chave}»."

def recordar(termo: str | None = None, escopo: str | None = None, limite: int = 40) -> list[sqlite3.Row]:
    cx = conectar(somente_leitura=True)
    try:
        if termo:
            try:
                return cx.execute(
                    "SELECT l.* FROM lembranca_busca b JOIN lembranca l ON l.rowid=b.rowid"
                    " WHERE lembranca_busca MATCH ? ORDER BY l.atualizada DESC LIMIT ?",
                    (termo, limite)).fetchall()
            except sqlite3.OperationalError:
                pass  # termo que o FTS não aceita: cai para o LIKE
            alvo = f"%{termo}%"
            return cx.execute(
                "SELECT * FROM lembranca WHERE chave LIKE ? OR valor LIKE ?"
                " ORDER BY atualizada DESC LIMIT ?", (alvo, alvo, limite)).fetchall()
        if escopo:
            return cx.execute("SELECT * FROM lembranca WHERE escopo=? ORDER BY chave LIMIT ?",
                              (escopo, limite)).fetchall()
        return cx.execute("SELECT * FROM lembranca ORDER BY escopo, chave LIMIT ?", (limite,)).fetchall()
    finally:
        cx.close()

def semear() -> int:
    """As decisões já tomadas neste projeto, para a Ana não perguntar de novo."""
    base = [
        ("unidade de análise canônica", "Par atleta-dia (U-AD), n = 166. As outras três — U-R (456 registros), "
         "U-286 (primeira e última) e U-PAR (143 pareados) — existem e devem ser declaradas, nunca misturadas.",
         "handebol"),
        ("faixa de risco", "Perfis 3, 4 e 5 da solução: barbatana de tubarão, iceberg invertido e everest invertido.",
         "handebol"),
        ("dia fisiológico", "A virada é às 4h: registro antes das 4h pertence ao dia anterior.", "handebol"),
        ("dados sensíveis", "Backup__Banco_de_dados.xlsx e o HIIT_FC_PSE.xlsx não anonimizado têm nomes reais "
         "ligados a humor e lesão. Não acompanham submissão nem repositório aberto. A anonimização A01–A27 "
         "acontece dentro da rotina de importação.", "handebol"),
        ("padrão de escrita", "Português culto brasileiro, padrão ouro da literatura. Sem gerúndio, sem conectivos "
         "de encadeamento vazios, sem hipérbole. Número sempre com vírgula decimal e sinal menos tipográfico.",
         "escrita"),
        ("regra dos números", "Nenhum número entra em texto sem vir de uma consulta à base ou a um JSON de análise. "
         "Memória não é fonte.", "escrita"),
        ("estudo em curso", "Perfis de humor (BRUMS) de atletas de handebol de elite na última semana de "
         "pré-temporada, 21 a 27 de abril de 2024, 27 atletas. Dois artigos: descritivo-analítico e inferencial.",
         "handebol"),
        ("pendências dos artigos", "Falta o número do CAAE, o financiamento e a contribuição dos autores. "
         "Cinco referências seguem sem DOI. A idade diverge entre 21,96 ± 3,81 e 22,2 ± 3,7.", "handebol"),
    ]
    for chave, valor, escopo in base:
        lembrar(chave, valor, escopo=escopo, origem="semeadura inicial")
    return len(base)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "semear":
        print(f"{semear()} lembranças semeadas em {BANCO}")
    else:
        for r in recordar():
            print(f"[{r['escopo']}] {r['chave']}\n    {r['valor']}")
