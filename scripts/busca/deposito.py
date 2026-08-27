"""Gravação incremental na biblioteca SQLite e registro de proveniência.

Um `upsert` por registro: novos entram, conhecidos têm apenas os campos vazios
completados — nunca se sobrescreve curadoria manual com metadado de API.

Toda execução grava uma linha em `busca_execucao` e uma por base em
`busca_rendimento`, de onde a Tabela 1 do manuscrito passa a ser gerada em vez
de digitada.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .normalizar import CAMPOS, chave_titulo

# Campos que a busca alimenta. Os demais (variaveis, instrumentos, sintese...)
# pertencem às rotinas de enriquecimento e nunca são tocados aqui.
CAMPOS_BUSCA = [c for c in CAMPOS if c != "idioma"]

SCHEMA_PROVENIENCIA = """
CREATE TABLE IF NOT EXISTS busca_execucao (
    id INTEGER PRIMARY KEY,
    quando TEXT NOT NULL,
    janela TEXT,
    identificados INTEGER,
    duplicatas INTEGER,
    unicos INTEGER,
    novos INTEGER,
    atualizados INTEGER,
    duracao_s INTEGER,
    consultas TEXT
);
CREATE TABLE IF NOT EXISTS busca_rendimento (
    execucao_id INTEGER NOT NULL REFERENCES busca_execucao(id),
    base TEXT NOT NULL,
    declarados INTEGER,
    recuperados INTEGER,
    erro TEXT,
    PRIMARY KEY (execucao_id, base)
);
CREATE TABLE IF NOT EXISTS busca_duplicata (
    execucao_id INTEGER NOT NULL REFERENCES busca_execucao(id),
    criterio TEXT NOT NULL,
    fonte TEXT,
    doi TEXT,
    pmid TEXT,
    titulo TEXT
);
CREATE VIEW IF NOT EXISTS v_rendimento_por_base AS
    SELECT e.quando, r.base, r.declarados, r.recuperados, r.erro
    FROM busca_rendimento r JOIN busca_execucao e ON e.id = r.execucao_id
    ORDER BY e.quando DESC, r.recuperados DESC;
"""

SCHEMA_ARTIGO = """
CREATE TABLE IF NOT EXISTS artigo (
    id INTEGER PRIMARY KEY, pmid TEXT, fonte TEXT, titulo TEXT, autores TEXT,
    pais TEXT, ano TEXT, revista TEXT, palavras_chave TEXT, instrumentos TEXT,
    variaveis_analisadas TEXT, populacao TEXT, amostra TEXT, estatistica TEXT,
    tipo_estudo TEXT, desenho_estudo TEXT, abordagem TEXT, pico_intervencao TEXT,
    pico_comparacao TEXT, pcc_conceito TEXT, pcc_contexto TEXT, sintese TEXT,
    resumo TEXT, doi TEXT, doi_suspeito INTEGER, citacoes INTEGER,
    fonte_metodos TEXT, link TEXT, volume TEXT, numero TEXT, paginas TEXT,
    referencia_abnt TEXT, referencia_vancouver TEXT, pmcid TEXT,
    tem_texto_completo INTEGER, texto_completo_arquivo TEXT, oa_status TEXT,
    oa_url TEXT
);
CREATE TABLE IF NOT EXISTS artigo_variavel (artigo_id INTEGER, variavel TEXT);
CREATE TABLE IF NOT EXISTS artigo_subvariavel (artigo_id INTEGER, subvariavel TEXT);
CREATE TABLE IF NOT EXISTS variavel (codigo TEXT PRIMARY KEY, rotulo TEXT, cor TEXT);
"""

INDICES = """
CREATE UNIQUE INDEX IF NOT EXISTS ix_artigo_doi  ON artigo(doi)  WHERE doi  IS NOT NULL AND doi  <> '';
CREATE UNIQUE INDEX IF NOT EXISTS ix_artigo_pmid ON artigo(pmid) WHERE pmid IS NOT NULL AND pmid <> '';
CREATE INDEX IF NOT EXISTS ix_artigo_ano ON artigo(ano);
"""


def conectar(caminho: str | Path) -> sqlite3.Connection:
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA_ARTIGO)
    con.executescript(SCHEMA_PROVENIENCIA)
    try:
        con.executescript(INDICES)
    except sqlite3.IntegrityError:
        # Biblioteca preexistente com duplicatas: indexa sem unicidade e avisa.
        con.execute("CREATE INDEX IF NOT EXISTS ix_artigo_doi_dup ON artigo(doi)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_artigo_pmid_dup ON artigo(pmid)")
    con.commit()
    return con


def _existente(con: sqlite3.Connection, r: dict) -> sqlite3.Row | None:
    if r.get("doi"):
        f = con.execute("SELECT * FROM artigo WHERE lower(doi)=?", (r["doi"],)).fetchone()
        if f:
            return f
    if r.get("pmid"):
        f = con.execute("SELECT * FROM artigo WHERE pmid=?", (r["pmid"],)).fetchone()
        if f:
            return f
    chave = chave_titulo(r.get("titulo"))
    if len(chave) > 15:
        for f in con.execute("SELECT * FROM artigo WHERE ano=?", (r.get("ano", ""),)):
            if chave_titulo(f["titulo"]) == chave:
                return f
    return None


def gravar(con: sqlite3.Connection, registros: list[dict]) -> tuple[int, int]:
    """Insere os novos e completa os campos vazios dos conhecidos.

    Devolve (novos, atualizados).
    """
    novos = atualizados = 0
    for r in registros:
        atual = _existente(con, r)
        if atual is None:
            cols = [c for c in CAMPOS_BUSCA if r.get(c) not in (None, "")]
            con.execute(
                f"INSERT INTO artigo ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                [r[c] for c in cols])
            novos += 1
            continue

        mudancas = {}
        for c in CAMPOS_BUSCA:
            novo = r.get(c)
            if novo in (None, ""):
                continue
            if atual[c] in (None, ""):
                mudancas[c] = novo
            elif c == "fonte":
                fontes = set(str(atual[c]).split("; ")) | set(str(novo).split("; "))
                if len(fontes) > len(str(atual[c]).split("; ")):
                    mudancas[c] = "; ".join(sorted(fontes))
            elif c == "citacoes" and isinstance(novo, int) and novo > (atual[c] or 0):
                mudancas[c] = novo
        if mudancas:
            con.execute(
                f"UPDATE artigo SET {','.join(f'{k}=?' for k in mudancas)} WHERE id=?",
                [*mudancas.values(), atual["id"]])
            atualizados += 1
    con.commit()
    return novos, atualizados


def registrar_execucao(con: sqlite3.Connection, *, janela: tuple[int, int],
                       rendimento: dict[str, dict], duplicatas: list[dict],
                       unicos: int, novos: int, atualizados: int,
                       duracao_s: int, consultas: dict[str, str]) -> int:
    identificados = sum(v.get("recuperados") or 0 for v in rendimento.values())
    cur = con.execute(
        "INSERT INTO busca_execucao (quando, janela, identificados, duplicatas, "
        "unicos, novos, atualizados, duracao_s, consultas) VALUES (?,?,?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"),
         f"{janela[0]}-{janela[1]}", identificados, len(duplicatas), unicos,
         novos, atualizados, duracao_s,
         json.dumps({k: {"caracteres": len(v), "consulta": v}
                     for k, v in consultas.items()}, ensure_ascii=False)))
    eid = cur.lastrowid
    con.executemany(
        "INSERT INTO busca_rendimento (execucao_id, base, declarados, recuperados, erro) "
        "VALUES (?,?,?,?,?)",
        [(eid, base, v.get("declarados"), v.get("recuperados"), v.get("erro"))
         for base, v in rendimento.items()])
    con.executemany(
        "INSERT INTO busca_duplicata (execucao_id, criterio, fonte, doi, pmid, titulo) "
        "VALUES (?,?,?,?,?,?)",
        [(eid, d["_criterio"], d.get("fonte"), d.get("doi"), d.get("pmid"),
          (d.get("titulo") or "")[:300]) for d in duplicatas])
    con.commit()
    return eid


def tabela_rendimento(con: sqlite3.Connection, execucao_id: int) -> str:
    """Gera a Tabela 1 do manuscrito em Markdown, a partir dos dados gravados."""
    linhas = con.execute(
        "SELECT base, declarados, recuperados, erro FROM busca_rendimento "
        "WHERE execucao_id=? ORDER BY recuperados DESC", (execucao_id,)).fetchall()
    out = ["| Base | Recuperados | Declarados pela base | Observação |",
           "|---|---:|---:|---|"]
    total = 0
    for l in linhas:
        rec = l["recuperados"]
        total += rec or 0
        out.append(f"| {l['base']} | {rec if rec is not None else '—'} "
                   f"| {l['declarados'] if l['declarados'] is not None else 'n.d.'} "
                   f"| {l['erro'] or ''} |")
    out.append(f"| **Total** | **{total}** | | |")
    return "\n".join(out)
