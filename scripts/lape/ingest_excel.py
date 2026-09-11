"""Ingestao das planilhas do LAPE (.xlsx/.xls/.csv) para o banco SQLite."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from . import config
from .db import Database
from .mapping import (
    DECISION_MAP,
    PROJECT_STATUS_MAP,
    ROLE_MAP,
    SHEET_IGNORE,
    EVENT_KIND_MAP,
    STATUS_MAP,
    THESIS_KIND_MAP,
    THESIS_STATUS_MAP,
    build_column_map,
    desenho_de_estudo,
    map_value,
    resolve_sheet,
)
from .util import (
    author_key,
    clean_text,
    display_name,
    norm_key,
    parse_date,
    parse_datetime,
    split_authors,
    title_key,
    to_bool,
    to_float,
    to_int,
    norm_doi,
    year_of,
)

# Ordem de ingestao: catalogos antes das entidades que os referenciam.
SHEET_ORDER = (
    "research_lines",
    "institutions",
    "rejection_reasons",
    "members",
    "projects",
    "project_members",
    "articles",
    "authors",
    "submissions",
    "events",
    "event_participants",
)


# ----------------------------------------------------------------------
# Leitura de arquivos
# ----------------------------------------------------------------------
def read_source(path: Path) -> dict[str, pd.DataFrame]:
    """Le um arquivo e devolve {nome_da_aba: DataFrame}."""
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".txt"}:
        sep = "\t" if suffix == ".tsv" else None
        frame = pd.read_csv(path, sep=sep, engine="python", dtype=object)
        return {path.stem: frame}
    engine = "openpyxl" if suffix == ".xlsx" else None
    return pd.read_excel(path, sheet_name=None, dtype=object, engine=engine)


def discover_sources(raw_dir: Path = config.RAW_DIR) -> list[Path]:
    if not raw_dir.exists():
        return []
    patterns = ("*.xlsx", "*.xlsm", "*.xls", "*.csv", "*.tsv")
    files: list[Path] = []
    for pattern in patterns:
        files.extend(p for p in sorted(raw_dir.rglob(pattern)) if not p.name.startswith("~$"))
    return files


WIDE_BLOCK = re.compile(r"^(.*?)_(\d{1,2})$")


def explode_wide(frame: pd.DataFrame) -> pd.DataFrame | None:
    """Converte planilhas em formato largo para formato longo.

    A aba 'Tentativas de Submissao' do LAPE repete blocos numerados
    ('Revista 1', 'Data de submissao 1', ... 'Revista 3'). Aqui cada bloco
    vira uma linha, preservando as colunas compartilhadas (ID do artigo).
    """
    blocks: dict[int, dict[str, Any]] = {}
    shared: list[Any] = []
    for column in frame.columns:
        match = WIDE_BLOCK.match(norm_key(column))
        if match and match.group(1):
            blocks.setdefault(int(match.group(2)), {})[match.group(1)] = column
        else:
            shared.append(column)
    if len(blocks) < 2:
        return None

    records: list[dict[str, Any]] = []
    for _, raw in frame.iterrows():
        for number in sorted(blocks):
            record = {str(col): raw.get(col) for col in shared}
            for base, column in blocks[number].items():
                record[base] = raw.get(column)
            record["attempt_no"] = number
            records.append(record)
    return pd.DataFrame(records)


def rows_of(frame: pd.DataFrame, sheet: str) -> list[dict[str, Any]]:
    """Normaliza cabecalhos e devolve linhas nao vazias como dicionarios."""
    frame = frame.dropna(how="all")
    if frame.empty:
        return []
    if sheet == "submissions":
        wide = explode_wide(frame)
        if wide is not None:
            frame = wide
    column_map = build_column_map(sheet, list(frame.columns))
    records: list[dict[str, Any]] = []
    for _, raw in frame.iterrows():
        row: dict[str, Any] = {}
        for original, field in column_map.items():
            row[field] = raw.get(original)
        extras = {norm_key(c): raw.get(c) for c in frame.columns if c not in column_map}
        row["_extras"] = extras
        if any(clean_text(v) is not None for k, v in row.items() if k != "_extras"):
            records.append(row)
    return records


# ----------------------------------------------------------------------
# Resolucao de referencias
# ----------------------------------------------------------------------
def resolve_article(db: Database, value: Any) -> int | None:
    """Encontra um artigo por codigo interno, DOI ou titulo."""
    text = clean_text(value)
    if text is None:
        return None
    doi = norm_doi(text)
    if doi:
        row = db.query("SELECT id FROM articles WHERE doi = ?", (doi,))
        if row:
            return int(row[0]["id"])
    row = db.query("SELECT id FROM articles WHERE internal_code = ?", (text,))
    if row:
        return int(row[0]["id"])
    key = title_key(text)
    row = db.query("SELECT id FROM articles WHERE title_key = ?", (key,))
    if row:
        return int(row[0]["id"])
    row = db.query("SELECT id FROM articles WHERE title_key LIKE ? LIMIT 2", (key[:60] + "%",))
    return int(row[0]["id"]) if len(row) == 1 else None


def resolve_event(db: Database, value: Any) -> int | None:
    text = clean_text(value)
    if text is None:
        return None
    row = db.query(
        "SELECT id FROM events WHERE external_key = ? OR lower(title) = lower(?) LIMIT 1",
        (text, text),
    )
    return int(row[0]["id"]) if row else None


# ----------------------------------------------------------------------
# Handlers por aba
# ----------------------------------------------------------------------
def ingest_research_lines(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        name = clean_text(row.get("name"))
        if not name:
            continue
        code = norm_key(row.get("code") or name)
        gravar_registro(db, "research_lines", {
                "code": code,
                "name": name,
                "description": clean_text(row.get("description")),
                "coordinator": clean_text(row.get("coordinator")),
                "started_on": parse_date(row.get("started_on")),
                "keywords": clean_text(row.get("keywords")),
                "active": to_bool(row.get("active"), default=1),
            }, ("code",), row, origem=ORIGEM_DA_LINHA,
            sempre=("code", "name", "active"))
        written += 1
    return written


def ingest_institutions(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        name = clean_text(row.get("name"))
        if not name:
            continue
        db.institution_id(
            name,
            row.get("city"),
            acronym=clean_text(row.get("acronym")),
            state=clean_text(row.get("state")),
            country=clean_text(row.get("country")) or "Brasil",
            latitude=to_float(row.get("latitude")),
            longitude=to_float(row.get("longitude")),
        )
        written += 1
    return written


def ingest_rejection_reasons(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        label = clean_text(row.get("label"))
        if not label:
            continue
        db.upsert(
            "rejection_reasons",
            {
                "code": norm_key(row.get("code") or label)[:60],
                "label": label,
                "category": clean_text(row.get("category")),
            },
            conflict=("code",),
        )
        written += 1
    return written


MEMBER_PROFILE_FIELDS = ("short_name", "lattes_id", "orcid", "email", "role", "degree",
                         "phone", "bio", "photo_url", "openalex_id", "scopus_author_id",
                         "thesis_title", "topics", "scholarship")

# Papel dentro do projeto, deduzido do vinculo com o laboratorio. Serve so
# de ponto de partida: a coordenacao pode corrigir depois, e a correcao nao
# e desfeita, porque a ligacao automatica nunca sobrescreve o que ja existe.
PAPEL_NO_PROJETO = {
    "coordenacao": "coordenacao", "professor": "pesquisador",
    "pos_doutorado": "pesquisador", "doutorando": "pesquisador",
    "mestrando": "pesquisador", "tecnico": "apoio",
}


def _campos_de_formacao(db: Database, row: dict) -> dict[str, Any]:
    """Orientacao, tese e bolsa -- o que sustenta o organograma."""
    return {
        "advisor_id": db.member_id(row.get("advisor")) if clean_text(row.get("advisor")) else None,
        "co_advisor_id": (db.member_id(row.get("co_advisor"))
                          if clean_text(row.get("co_advisor")) else None),
        "thesis_title": clean_text(row.get("thesis_title")),
        "thesis_kind": map_value(row.get("thesis_kind"), THESIS_KIND_MAP),
        "thesis_status": map_value(row.get("thesis_status"), THESIS_STATUS_MAP),
        "thesis_due_on": parse_date(row.get("thesis_due_on")),
        "topics": clean_text(row.get("topics")),
        "scholarship": clean_text(row.get("scholarship")),
        "scholarship_until": parse_date(row.get("scholarship_until")),
    }


def ligar_ao_orientador(db: Database, member_id: int) -> list[str]:
    """Liga o orientando ao trabalho que ja esta em curso com o orientador.

    Foi o que o laboratorio pediu: quem se cadastra ja aparece ligado ao
    projeto e a rede se forma sozinha, sem ninguem repetir a mesma
    informacao em tres telas. A regra e conservadora de proposito --
    so projetos em andamento, so os da linha de pesquisa da pessoa, e
    nunca por cima de uma participacao ja registrada, que pode ter sido
    corrigida a mao.
    """
    pessoa = db.conn.execute(
        "SELECT id, role, advisor_id, research_line_id FROM members WHERE id = ?",
        (member_id,)).fetchone()
    if pessoa is None or not pessoa["advisor_id"]:
        return []
    orientador = db.conn.execute(
        "SELECT id, research_line_id FROM members WHERE id = ?",
        (pessoa["advisor_id"],)).fetchone()
    if orientador is None:
        return []

    # A linha de pesquisa desce do orientador quando a pessoa nao declarou a
    # sua: e a informacao que o orientando quase nunca sabe de cor.
    linha = pessoa["research_line_id"] or orientador["research_line_id"]
    if linha and not pessoa["research_line_id"]:
        db.execute("UPDATE members SET research_line_id = ? WHERE id = ?", (linha, member_id))

    # O orientador entra num projeto como membro da equipe ou como
    # coordenador; os dois casos valem.
    projetos = db.dicts(
        """
        SELECT DISTINCT p.id, p.name, p.research_line_id
        FROM projects p
        LEFT JOIN project_members pm ON pm.project_id = p.id
        WHERE p.status = 'em_andamento'
          AND (pm.member_id = ? OR p.coordinator_id = ?)
        ORDER BY COALESCE(p.started_on, '') DESC
        """,
        (orientador["id"], orientador["id"]))
    if linha:
        na_linha = [p for p in projetos if p["research_line_id"] == linha]
        # sem projeto na linha da pessoa, nao se inventa vinculo: um projeto
        # de outra area nao vira dela so porque o orientador e o mesmo
        projetos = na_linha
    if not projetos:
        return []

    papel = PAPEL_NO_PROJETO.get(pessoa["role"] or "", "bolsista")
    ligados = []
    for projeto in projetos:
        ja = db.conn.execute(
            "SELECT 1 FROM project_members WHERE project_id = ? AND member_id = ?",
            (projeto["id"], member_id)).fetchone()
        if ja:
            continue
        db.execute(
            "INSERT INTO project_members (project_id, member_id, role) VALUES (?, ?, ?)",
            (projeto["id"], member_id, papel))
        ligados.append(projeto["name"])
    db.conn.commit()
    return ligados


def ingest_members(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        name = clean_text(row.get("full_name"))
        existing_id = to_int(row.get("id"))
        if existing_id and not name:
            # edicao do proprio cadastro pela area do integrante
            db.update_row("members", existing_id, {
                **{field: clean_text(row.get(field)) for field in MEMBER_PROFILE_FIELDS},
                "role": map_value(row.get("role"), ROLE_MAP) or clean_text(row.get("role")),
                "research_line_id": db.research_line_id(row.get("research_line")),
                "institution_id": db.institution_id(row.get("institution")),
                **_campos_de_formacao(db, row),
            })
            db.conn.commit()
            ligar_ao_orientador(db, existing_id)
            written += 1
            continue
        if not name:
            continue
        member_id = db.member_id(
            name,
            short_name=clean_text(row.get("short_name")),
            lattes_id=clean_text(row.get("lattes_id")),
            orcid=clean_text(row.get("orcid")),
            email=clean_text(row.get("email")),
            role=map_value(row.get("role"), ROLE_MAP) or clean_text(row.get("role")),
            degree=clean_text(row.get("degree")),
            phone=clean_text(row.get("phone")),
            bio=clean_text(row.get("bio")),
            photo_url=clean_text(row.get("photo_url")),
            openalex_id=clean_text(row.get("openalex_id")),
            scopus_author_id=clean_text(row.get("scopus_author_id")),
            research_line_id=db.research_line_id(row.get("research_line")),
            institution_id=db.institution_id(row.get("institution")),
            joined_on=parse_date(row.get("joined_on")),
            left_on=parse_date(row.get("left_on")),
            is_external=to_bool(row.get("is_external")),
            active=to_bool(row.get("active"), default=1),
            **_campos_de_formacao(db, row),
        )
        if member_id:
            db.execute("UPDATE members SET full_name = ? WHERE id = ?", (name, member_id))
            # `in row`, e nao `row.get(...)`: a linha que NAO traz a coluna
            # nao mexe nas grafias; a que traz a coluna vazia apaga todas.
            # Sem essa distincao, gravar qualquer outro campo do cadastro
            # limparia as variacoes de nome sem ninguem pedir.
            if "aliases" in row:
                for alias in split_authors(row.get("aliases")):
                    duplicate = db.member_id(alias, create=False)
                    if duplicate and duplicate != member_id:
                        db.merge_members(duplicate, member_id)
                db.set_aliases(member_id, row.get("aliases"))
            ligar_ao_orientador(db, member_id)
            written += 1
    db.conn.commit()
    return written


# Marcos do ciclo de vida do manuscrito, na ordem em que acontecem.
MILESTONES: tuple[tuple[str, str, str], ...] = (
    ("started_on", "inicio", "Inicio"),
    ("version_1", "versao_1", "1a versao"),
    ("version_2", "versao_2", "2a versao"),
    ("version_3", "versao_3", "3a versao"),
    ("version_4", "versao_4", "4a versao"),
    ("version_final", "versao_final", "Versao final"),
    ("internal_review", "revisao_interna", "Revisao interna"),
    ("first_submission_on", "submissao", "1a submissao"),
    ("accepted_on", "aceite", "Aceite"),
    ("published_on", "publicacao", "Publicacao"),
)


def _save_milestones(db: Database, article_id: int, values: dict[str, str | None],
                     limpar: bool = False) -> None:
    """Grava as datas do artigo.

    `limpar` vale para a edicao na tela: apagar a data ali tem de apagar o
    marco. Na importacao de planilha e o contrario -- uma planilha que nao
    traz a coluna da 1a versao nao esta dizendo que ela nao existe.
    """
    for seq, (field, code, label) in enumerate(MILESTONES):
        occurred = values.get(field)
        if occurred is None:
            if limpar:
                db.execute("DELETE FROM article_milestones"
                           " WHERE article_id = ? AND milestone = ?", (article_id, code))
            continue
        db.upsert(
            "article_milestones",
            {
                "article_id": article_id,
                "milestone": code,
                "label": label,
                "occurred_on": occurred,
                "seq": seq,
            },
            conflict=("article_id", "milestone"),
        )


def ingest_projects(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        name = clean_text(row.get("name"))
        if not name:
            continue
        coordinator = clean_text(row.get("coordinator"))
        project_id = gravar_registro(db, "projects", {
                "code": norm_key(row.get("code") or name)[:60],
                "name": name,
                "description": clean_text(row.get("description")),
                "research_line_id": db.research_line_id(row.get("research_line")),
                "coordinator_id": db.member_id(coordinator, create=True) if coordinator else None,
                "coordinator_name": coordinator,
                "kind": clean_text(row.get("kind")),
                "funder": clean_text(row.get("funder")),
                "grant_number": clean_text(row.get("grant_number")),
                "amount": to_float(row.get("amount")),
                "started_on": parse_date(row.get("started_on")),
                "ended_on": parse_date(row.get("ended_on")),
                "status": map_value(row.get("status"), PROJECT_STATUS_MAP, default="em_andamento"),
                "ethics_approval": clean_text(row.get("ethics_approval")),
                "url": clean_text(row.get("url")),
            }, ("code",), row, origem=ORIGEM_DO_PROJETO,
            sempre=("code", "name", "status"))
        team = split_authors(row.get("members"))
        if coordinator and not any(clean_text(t) == coordinator for t in team):
            team = [coordinator, *team]
        for name_in_team in team:
            member_id = db.member_id(name_in_team, create=True)
            if member_id:
                db.execute(
                    "INSERT OR IGNORE INTO project_members (project_id, member_id, role)"
                    " VALUES (?, ?, ?)",
                    (project_id, member_id,
                     "Coordenacao" if clean_text(name_in_team) == coordinator else None),
                )
        written += 1
    return written


def ingest_project_members(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        reference = clean_text(row.get("project"))
        member_id = db.member_id(row.get("member"), create=True)
        if not reference or not member_id:
            continue
        project_id = db.scalar(
            "SELECT id FROM projects WHERE code = ? OR lower(name) = lower(?)",
            (norm_key(reference)[:60], reference))
        if not project_id:
            continue
        db.execute(
            "INSERT OR REPLACE INTO project_members (project_id, member_id, role, joined_on)"
            " VALUES (?, ?, ?, ?)",
            (project_id, member_id, clean_text(row.get("role")), parse_date(row.get("joined_on"))),
        )
        written += 1
    return written


def _article_status(row: dict, published_on: str | None, accepted_on: str | None,
                    submitted_on: str | None, year: int | None) -> str:
    status = map_value(row.get("status"), STATUS_MAP)
    if status:
        return status
    if published_on or year:
        return "publicado"
    if accepted_on:
        return "aceito"
    if submitted_on:
        return "submetido"
    return "em_producao"


# Coluna do banco -> chave que a alimenta no formulario e na planilha.
# Serve para distinguir "a tela apagou este campo" de "a planilha nem traz
# esta coluna". Sem a distincao, apagar um valor na tela nao apagava nada:
# o upsert descarta vazios de proposito, para que uma planilha com meia
# duzia de colunas nao limpe o cadastro inteiro -- regra certa para a
# importacao e errada para quem esta editando a ficha na tela.
ORIGEM_DO_CAMPO: dict[str, str] = {
    "internal_code": "internal_code",
    "research_line_id": "research_line",
    "study_type": "study_type",
    "language": "language",
    "started_on": "started_on",
    "first_submission_on": "first_submission_on",
    "accepted_on": "accepted_on",
    "published_on": "published_on",
    "journal": "journal",
    "issn": "issn",
    "qualis": "qualis",
    "impact_factor": "impact_factor",
    "doi": "doi",
    "url": "url",
    "wos_id": "wos_id",
    "scopus_id": "scopus_id",
    "wos_citations": "wos_citations",
    "scopus_citations": "scopus_citations",
    "open_access": "open_access",
    "notes": "notes",
    "lead_name": "lead",
    "lead_member_id": "lead",
    "internal_review_on": "internal_review",
}
ORIGEM_DO_PROJETO: dict[str, str] = {
    "description": "description", "research_line_id": "research_line",
    "coordinator_id": "coordinator", "coordinator_name": "coordinator",
    "kind": "kind", "funder": "funder", "grant_number": "grant_number",
    "amount": "amount", "started_on": "started_on", "ended_on": "ended_on",
    "ethics_approval": "ethics_approval", "url": "url",
}
ORIGEM_DA_LINHA: dict[str, str] = {
    "description": "description", "coordinator": "coordinator",
    "started_on": "started_on", "keywords": "keywords",
}
# Derivados: nao saem de um campo da tela, saem das datas e da situacao.
# Numa edicao sao sempre reescritos.
SEMPRE_NA_EDICAO = ("title", "title_key", "status", "status_locked", "year_published")


ROTULO_DA_TABELA = {"articles": "artigo", "projects": "projeto",
                    "research_lines": "linha de pesquisa", "events": "atividade"}


def _alvo_da_edicao(db: Database, tabela: str, row: dict) -> int | None:
    """O registro que a tela mandou alterar, quando mandou.

    Sem isto a identidade do registro era o proprio nome: renomear gerava
    uma chave nova, o upsert INSERIA um segundo registro e deixava o
    original intacto. A tela respondia "1 registro gravado", a lista
    continuava igual, e o trabalho de quem editou ia junto. Agora a tela
    manda o id da ficha que ela abriu.
    """
    alvo = to_int(row.get("registro_id"))
    if alvo is None:
        return None
    if not db.scalar(f"SELECT 1 FROM {tabela} WHERE id = ?", (alvo,)):
        raise ValueError(f"{ROTULO_DA_TABELA.get(tabela, 'registro')} {alvo} nao existe mais")
    return alvo


def _chave_cabe(db: Database, tabela: str, alvo: int, chave: str,
                valor: Any, rotulo: str) -> None:
    """Recusa a renomeacao que cairia em cima de outro registro.

    Deixar passar juntaria dois trabalhos num registro so, e desfazer isso
    depois exige saber qual dado era de qual -- que e exatamente o que a
    fusao apaga.
    """
    choque = db.scalar(
        f"SELECT {rotulo} FROM {tabela} WHERE {chave} = ? AND id <> ?", (valor, alvo))
    if choque:
        raise ValueError(
            f"ja existe outro(a) {ROTULO_DA_TABELA.get(tabela, 'registro')} com este nome:"
            f" \u201c{choque}\u201d. Renomeie um dos dois antes de continuar.")


def _atualizar(db: Database, tabela: str, alvo: int, dados: dict, row: dict,
               origem: dict[str, str], sempre: tuple[str, ...]) -> int:
    """Grava a edicao na ficha que a pessoa abriu -- vazio inclusive.

    `sempre` sao os campos derivados (a chave, a situacao calculada das
    datas): nao saem de um campo da tela e por isso sao sempre reescritos.
    Os demais so viram NULL quando a tela mandou a coluna vazia -- se a
    origem nem veio no pedido, nao ha nada sendo apagado.
    """
    escrever = {}
    for coluna, valor in dados.items():
        if coluna in sempre or valor is not None:
            escrever[coluna] = valor
        elif origem.get(coluna) in row:
            escrever[coluna] = None
    _anotar_o_que_foi_apagado(db, tabela, alvo, escrever)
    colunas = ", ".join(f"{c} = ?" for c in escrever)
    tem_updated = any(c["name"] == "updated_at"
                      for c in db.dicts(f"PRAGMA table_info({tabela})"))
    carimbo = ", updated_at = datetime('now')" if tem_updated else ""
    db.execute(f"UPDATE {tabela} SET {colunas}{carimbo} WHERE id = ?",
               [*escrever.values(), alvo])
    return alvo


def _anotar_o_que_foi_apagado(db: Database, tabela: str, alvo: int,
                              escrever: dict[str, Any]) -> None:
    """Guarda quais campos a pessoa esvaziou, e quais ela voltou a preencher.

    O agente rastreador preenche todo campo vazio que encontra. Sem esta
    anotacao ele nao distingue "ninguem soube este dado ainda" de "a
    coordenacao apagou este dado de proposito", e repoe o segundo no
    enriquecimento seguinte -- entao apagar na tela nao durava ate a
    proxima rodada, e quem apagou jurava que a tela nao salvava.
    """
    antes = db.dicts(f"SELECT * FROM {tabela} WHERE id = ?", (alvo,))
    if not antes:
        return
    antes = antes[0]
    for coluna, valor in escrever.items():
        tinha = antes.get(coluna) not in (None, "")
        if valor in (None, "") and tinha:
            db.execute(
                "INSERT OR REPLACE INTO cleared_fields (entity, record_id, field)"
                " VALUES (?, ?, ?)", (tabela, alvo, coluna))
        elif valor not in (None, ""):
            # voltou a ter valor: a decisao de apagar deixou de valer
            db.execute("DELETE FROM cleared_fields"
                       " WHERE entity = ? AND record_id = ? AND field = ?",
                       (tabela, alvo, coluna))


def gravar_registro(db: Database, tabela: str, dados: dict, conflito: tuple[str, ...],
                    row: dict, origem: dict[str, str] | None = None,
                    sempre: tuple[str, ...] = (), rotulo: str = "name") -> int:
    """Cadastra um registro novo ou edita o que a tela abriu.

    Sao dois caminhos de proposito. A planilha identifica pelo nome e nunca
    apaga com vazio -- uma planilha de meia duzia de colunas nao pode
    limpar o cadastro inteiro. A tela identifica pelo id e apaga com vazio
    -- quem apagou o campo ali queria apagar.
    """
    alvo = _alvo_da_edicao(db, tabela, row)
    if alvo is None:
        return db.upsert(tabela, dados, conflict=conflito)
    if len(conflito) == 1 and conflito[0] in dados:
        _chave_cabe(db, tabela, alvo, conflito[0], dados[conflito[0]], rotulo)
    return _atualizar(db, tabela, alvo, dados, row, origem or {}, sempre)


def ingest_articles(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        title = clean_text(row.get("title"))
        if not title:
            continue
        alvo = _alvo_da_edicao(db, "articles", row)
        published_on = parse_date(row.get("published_on"))
        accepted_on = parse_date(row.get("accepted_on"))
        submitted_on = parse_date(row.get("first_submission_on"))
        started_on = parse_date(row.get("started_on"))
        year = to_int(row.get("year_published")) or year_of(published_on)
        status = _article_status(row, published_on, accepted_on, submitted_on, year)
        status_locked = 1 if map_value(row.get("status"), STATUS_MAP) else 0
        lead_name = clean_text(row.get("lead"))
        lead_member_id = db.member_id(lead_name, create=True) if lead_name else None
        internal_review = parse_date(row.get("internal_review"))
        milestones = {
            "started_on": started_on,
            "version_1": parse_date(row.get("version_1")),
            "version_2": parse_date(row.get("version_2")),
            "version_3": parse_date(row.get("version_3")),
            "version_4": parse_date(row.get("version_4")),
            "version_final": parse_date(row.get("version_final")),
            "internal_review": internal_review,
            "first_submission_on": submitted_on,
            "accepted_on": accepted_on,
            "published_on": published_on,
        }

        dados = {
                "title": title,
                "title_key": title_key(title),
                "internal_code": clean_text(row.get("internal_code")),
                "status": status,
                "research_line_id": db.research_line_id(row.get("research_line")),
                "study_type": desenho_de_estudo(row.get("study_type")),
                "language": clean_text(row.get("language")),
                "started_on": started_on,
                "first_submission_on": submitted_on,
                "accepted_on": accepted_on,
                "published_on": published_on,
                "year_published": year if status == "publicado" else None,
                "journal": clean_text(row.get("journal")) or clean_text(row.get("submission_journal")),
                "issn": clean_text(row.get("issn")),
                "qualis": clean_text(row.get("qualis")),
                "impact_factor": to_float(row.get("impact_factor")),
                "doi": norm_doi(row.get("doi")),
                "url": clean_text(row.get("url")),
                "wos_id": clean_text(row.get("wos_id")),
                "scopus_id": clean_text(row.get("scopus_id")),
                "wos_citations": to_int(row.get("wos_citations")),
                "scopus_citations": to_int(row.get("scopus_citations")),
                "open_access": to_bool(row.get("open_access")) if clean_text(row.get("open_access")) else None,
                "notes": clean_text(row.get("notes")),
                "lead_name": lead_name,
                "lead_member_id": lead_member_id,
                "status_locked": status_locked,
                "internal_review_on": internal_review,
        }
        if alvo is None:
            dados["source"] = "planilha"
        article_id = gravar_registro(db, "articles", dados, ("title_key",), row,
                                     origem=ORIGEM_DO_CAMPO, sempre=SEMPRE_NA_EDICAO,
                                     rotulo="title")
        _save_milestones(db, article_id, milestones, limpar=alvo is not None)
        _link_authors(db, article_id, split_authors(row.get("authors")), lead=lead_name)
        _inline_submission(db, article_id, row, submitted_on, accepted_on, status)
        written += 1
    return written


def _link_authors(db: Database, article_id: int, authors: list[str],
                  replace: bool = True, lead: str | None = None) -> None:
    """Grava a autoria; o responsavel entra como 1o autor se ja nao estiver."""
    from .util import author_key

    if lead and not any(author_key(a) == author_key(lead) for a in authors):
        authors = [lead, *authors]
    if not authors:
        return
    if replace:
        db.execute("DELETE FROM article_authors WHERE article_id = ?", (article_id,))
    for order, raw_name in enumerate(authors, start=1):
        name = clean_text(raw_name)
        if not name:
            continue
        corresponding = 1 if "*" in name else 0
        name = name.replace("*", "").strip()
        # Assinar um artigo com o laboratorio nao torna ninguem integrante
        # do laboratorio. Antes a ficha nascia com is_external = 0, o padrao
        # da coluna, e o orientador de fora, o colega de outra universidade
        # e o estatistico convidado viravam "pesquisador do LAPE" -- inflando
        # a equipe no painel e no organograma. Quem so assina nasce coautor;
        # promover a integrante e ato da coordenacao, na aba de integrantes.
        member_id = db.member_id(name, create=True, ao_criar={"is_external": 1})
        is_external = db.scalar("SELECT is_external FROM members WHERE id = ?", (member_id,)) or 0
        db.execute(
            "INSERT OR REPLACE INTO article_authors"
            " (article_id, member_id, author_name, author_order, is_corresponding, is_external)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (article_id, member_id, display_name(name) or name, order, corresponding, is_external),
        )


def _inline_submission(db: Database, article_id: int, row: dict, submitted_on: str | None,
                       accepted_on: str | None, status: str) -> None:
    """Cria a 1a tentativa a partir da propria linha de 'artigos'.

    Serve para planilhas que registram submissao e recusa na mesma linha
    do artigo. Se a aba 'submissoes' trouxer a tentativa 1, ela prevalece.
    """
    reason = clean_text(row.get("rejection_reason"))
    if not submitted_on and not reason:
        return
    if db.scalar("SELECT COUNT(*) FROM submissions WHERE article_id = ?", (article_id,)):
        return
    decision = {"publicado": "aceito", "aceito": "aceito", "rejeitado": "rejeitado"}.get(status)
    db.upsert(
        "submissions",
        {
            "article_id": article_id,
            "attempt_no": 1,
            "journal": clean_text(row.get("submission_journal")) or clean_text(row.get("journal")),
            "submitted_on": submitted_on,
            "decision": "rejeitado" if reason else decision,
            "decision_on": accepted_on,
            "rejection_reason_id": db.rejection_reason_id(reason) if reason else None,
        },
        conflict=("article_id", "attempt_no"),
    )


def ingest_authors(db: Database, rows: list[dict]) -> int:
    """Aba de autoria explicita (um autor por linha)."""
    written = 0
    grouped: dict[int, list[dict]] = {}
    for row in rows:
        article_id = resolve_article(db, row.get("article"))
        if not article_id or not clean_text(row.get("author_name")):
            continue
        grouped.setdefault(article_id, []).append(row)

    for article_id, entries in grouped.items():
        entries.sort(key=lambda r: to_int(r.get("author_order")) or 999)
        db.execute("DELETE FROM article_authors WHERE article_id = ?", (article_id,))
        for order, row in enumerate(entries, start=1):
            name = clean_text(row.get("author_name"))
            # `to_bool(...) or None` dizia "externo" e engolia "nao
            # externo": 0 vira None e o None e descartado. Agora a coluna
            # ausente deixa o padrao decidir (coautor), e a coluna
            # preenchida vale como declaracao, inclusive quando diz 0.
            declarado = (to_bool(row.get("is_external"))
                         if clean_text(row.get("is_external")) is not None else None)
            member_id = db.member_id(name, create=True, is_external=declarado,
                                     ao_criar={"is_external": 1})
            db.execute(
                "INSERT OR REPLACE INTO article_authors"
                " (article_id, member_id, author_name, author_order, is_corresponding, is_external)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    article_id,
                    member_id,
                    display_name(name) or name,
                    to_int(row.get("author_order")) or order,
                    to_bool(row.get("is_corresponding")),
                    to_bool(row.get("is_external")),
                ),
            )
            written += 1
    return written


def ingest_submissions(db: Database, rows: list[dict], destravar: bool = False,
                       continuar: bool = False) -> int:
    """Registra tentativas de submissao e rededuz o status dos artigos.

    `destravar` existe por causa de um choque de duas verdades. O status que
    veio da planilha fica travado (status_locked), para que uma reimportacao
    nao apague o que o laboratorio escreveu a mao. So que registrar uma
    recusa pela area do integrante TAMBEM e escrever a mao -- e e a
    declaracao mais recente. Sem destravar, a pessoa registrava a recusa,
    via a tentativa aparecer na lista, e o artigo continuava "submetido"
    para sempre: teria de ir a outra tela mudar a situacao de novo.

    O caminho da planilha nao destrava: la a coluna de situacao e a
    declaracao, e ela continua mandando.

    `continuar` resolve outra diferenca entre os dois caminhos, e esta
    custava dado. A planilha e uma DECLARACAO COMPLETA do historico do
    artigo: as tentativas vem todas juntas, e numerar de 1 e o que faz
    reimportar a mesma planilha nao criar tentativa nova. Ja a area do
    integrante manda UMA tentativa por vez -- e numerar de 1 ali fazia a
    segunda submissao gravar POR CIMA da primeira, pela chave
    (artigo, tentativa). A pessoa registrava "ressubmeti a Rheumatology" e
    perdia a recusa da Pain: a linha ficava com a revista nova, a data de
    decisao antiga e um motivo de recusa que ja nao correspondia a nada.
    """
    written = 0
    destravados: set[int] = set()
    counters: dict[int, int] = {}
    ordered = sorted(rows, key=lambda r: (parse_date(r.get("submitted_on")) or "9999",
                                          to_int(r.get("attempt_no")) or 0))
    for row in ordered:
        article_id = resolve_article(db, row.get("article"))
        if not article_id:
            continue
        if not any(
            clean_text(row.get(field)) is not None
            for field in ("journal", "submitted_on", "decision", "decision_on", "rejection_reason")
        ):
            continue  # bloco de tentativa ainda em branco na planilha
        if article_id not in counters:
            counters[article_id] = int(db.scalar(
                "SELECT COALESCE(MAX(attempt_no), 0) FROM submissions"
                " WHERE article_id = ?", (article_id,)) or 0) if continuar else 0
        counters[article_id] += 1
        attempt = to_int(row.get("attempt_no")) or counters[article_id]
        counters[article_id] = max(counters[article_id], attempt)
        reason = clean_text(row.get("rejection_reason"))
        decision = map_value(row.get("decision"), DECISION_MAP)
        submitted_on = parse_date(row.get("submitted_on"))
        if reason and not decision:
            decision = "rejeitado"
        if not decision and submitted_on:
            decision = "em_avaliacao"  # enviado e ainda sem parecer registrado
        db.upsert(
            "submissions",
            {
                "article_id": article_id,
                "attempt_no": attempt,
                "journal": clean_text(row.get("journal")),
                "issn": clean_text(row.get("issn")),
                "submitted_on": submitted_on,
                "decision": decision,
                "decision_on": parse_date(row.get("decision_on")),
                "rejection_reason_id": db.rejection_reason_id(reason) if reason else None,
                "rejection_notes": clean_text(row.get("rejection_notes")),
                "desk_reject": to_bool(row.get("desk_reject")) or (1 if decision == "desk_reject" else 0),
                "review_rounds": to_int(row.get("review_rounds")),
            },
            conflict=("article_id", "attempt_no"),
        )
        # Declaracao feita agora vale mais do que status escrito na planilha
        # meses atras -- e registrar O ENVIO tambem e uma declaracao. Excluir
        # `em_avaliacao` daqui era o que fazia a pessoa registrar "submeti a
        # Pain", ver a tentativa aparecer na lista, e o artigo continuar "em
        # producao" para sempre. A tela prometia, em letras, que a situacao
        # tinha sido atualizada.
        if destravar and decision:
            destravados.add(article_id)
        written += 1
    for article_id in destravados:
        # `arquivado` e a unica situacao que o historico de submissoes nao
        # consegue deduzir: e uma decisao de quem coordena ("este nao vai
        # adiante"), e nenhuma tentativa a contradiz. Destravar aqui faria
        # um artigo engavetado voltar sozinho para "submetido".
        db.execute("UPDATE articles SET status_locked = 0"
                   " WHERE id = ? AND status <> 'arquivado'", (article_id,))
    _sync_article_dates(db)
    derive_status(db)
    return written


def _sync_article_dates(db: Database) -> None:
    """Deriva 1a submissao e aceite do historico de tentativas."""
    db.execute(
        "UPDATE articles SET first_submission_on = COALESCE(first_submission_on,"
        " (SELECT MIN(s.submitted_on) FROM submissions s WHERE s.article_id = articles.id))"
    )
    db.execute(
        "UPDATE articles SET accepted_on = COALESCE(accepted_on,"
        " (SELECT MIN(s.decision_on) FROM submissions s"
        "   WHERE s.article_id = articles.id AND s.decision = 'aceito'))"
    )


def derive_status(db: Database) -> None:
    """Deduz o status dos artigos a partir do historico de submissoes.

    So altera artigos cuja planilha nao trouxe um status explicito
    (status_locked = 0), preservando o que o laboratorio informou.
    """
    for article in db.dicts(
        "SELECT id, published_on, accepted_on FROM articles WHERE status_locked = 0"
    ):
        attempts = db.dicts(
            "SELECT decision, submitted_on FROM submissions WHERE article_id = ?"
            " ORDER BY attempt_no",
            (article["id"],),
        )
        decisions = [a["decision"] for a in attempts]
        last = decisions[-1] if decisions else None
        if article["published_on"]:
            status = "publicado"
        elif article["accepted_on"] or "aceito" in decisions:
            status = "aceito"
        elif last in ("rejeitado", "desk_reject"):
            status = "rejeitado"
        elif last == "revisao_solicitada":
            status = "em_revisao"
        elif attempts:
            status = "submetido"
        else:
            status = "em_producao"
        db.execute("UPDATE articles SET status = ? WHERE id = ?", (status, article["id"]))
    db.conn.commit()


def ingest_events(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        title = clean_text(row.get("title"))
        start_at = parse_datetime(row.get("start_at"))
        if not title or not start_at:
            continue
        institution_id = db.institution_id(row.get("institution"), row.get("city"))
        key = clean_text(row.get("external_key")) or f"{norm_key(title)[:60]}_{start_at[:10]}"
        event_id = db.upsert(
            "events",
            {
                "external_key": key,
                "kind": map_value(row.get("kind"), EVENT_KIND_MAP, default="reuniao"),
                "title": title,
                "description": clean_text(row.get("description")),
                "start_at": start_at,
                "end_at": parse_datetime(row.get("end_at")),
                "all_day": to_bool(row.get("all_day")),
                "status": clean_text(row.get("status")) or "confirmado",
                "location_name": clean_text(row.get("location_name")),
                "institution_id": institution_id,
                "city": clean_text(row.get("city")),
                "state": clean_text(row.get("state")),
                "country": clean_text(row.get("country")) or "Brasil",
                "latitude": to_float(row.get("latitude")),
                "longitude": to_float(row.get("longitude")),
                "research_line_id": db.research_line_id(row.get("research_line")),
                "url": clean_text(row.get("url")),
            },
            conflict=("external_key",),
        )
        for name in split_authors(row.get("participants")):
            member_id = db.member_id(name, create=True)
            if member_id:
                db.execute(
                    "INSERT OR IGNORE INTO event_participants (event_id, member_id, attended)"
                    " VALUES (?, ?, 1)",
                    (event_id, member_id),
                )
        written += 1
    _geocode_events(db)
    return written


def _geocode_events(db: Database) -> None:
    """Herda coordenadas da instituicao quando o evento nao as tiver."""
    db.execute(
        "UPDATE events SET latitude = (SELECT i.latitude FROM institutions i WHERE i.id = events.institution_id),"
        " longitude = (SELECT i.longitude FROM institutions i WHERE i.id = events.institution_id)"
        " WHERE latitude IS NULL AND institution_id IS NOT NULL"
    )
    db.execute(
        "UPDATE events SET city = (SELECT i.city FROM institutions i WHERE i.id = events.institution_id)"
        " WHERE city IS NULL AND institution_id IS NOT NULL"
    )


def ingest_event_participants(db: Database, rows: list[dict]) -> int:
    written = 0
    for row in rows:
        event_id = resolve_event(db, row.get("event"))
        member_id = db.member_id(row.get("member"), create=True)
        if not event_id or not member_id:
            continue
        db.execute(
            "INSERT OR REPLACE INTO event_participants (event_id, member_id, role, attended)"
            " VALUES (?, ?, ?, ?)",
            (event_id, member_id, clean_text(row.get("role")), to_bool(row.get("attended"), default=1)),
        )
        written += 1
    return written


HANDLERS: dict[str, Callable[[Database, list[dict]], int]] = {
    "research_lines": ingest_research_lines,
    "projects": ingest_projects,
    "project_members": ingest_project_members,
    "institutions": ingest_institutions,
    "rejection_reasons": ingest_rejection_reasons,
    "members": ingest_members,
    "articles": ingest_articles,
    "authors": ingest_authors,
    "submissions": ingest_submissions,
    "events": ingest_events,
    "event_participants": ingest_event_participants,
}


# ----------------------------------------------------------------------
# Orquestracao
# ----------------------------------------------------------------------
def ingest_all(db: Database, raw_dir: Path = config.RAW_DIR, verbose: bool = True) -> dict[str, int]:
    """Le todas as planilhas de `raw_dir` e grava no banco."""
    sources = discover_sources(raw_dir)
    if not sources:
        if verbose:
            print(f"  ! nenhuma planilha encontrada em {raw_dir}")
        return {}

    buckets: dict[str, list[dict]] = {}
    unmatched: list[str] = []
    for path in sources:
        try:
            sheets = read_source(path)
        except Exception as exc:  # planilha corrompida nao derruba o pipeline
            db.log_ingest("excel", file=path.name, status="erro", message=str(exc))
            if verbose:
                print(f"  ! erro lendo {path.name}: {exc}")
            continue
        for sheet_name, frame in sheets.items():
            table = resolve_sheet(str(sheet_name))
            if table is None:
                if norm_key(sheet_name) not in SHEET_IGNORE:
                    unmatched.append(f"{path.name}:{sheet_name}")
                continue
            records = rows_of(frame, table)
            buckets.setdefault(table, []).extend(records)
            db.log_ingest("excel", target=table, file=f"{path.name}:{sheet_name}",
                          rows_read=len(records))

    totals: dict[str, int] = {}
    for table in SHEET_ORDER:
        records = buckets.get(table)
        if not records:
            continue
        written = HANDLERS[table](db, records)
        totals[table] = written
        db.conn.commit()
        if verbose:
            print(f"  {table:20s} {len(records):5d} linhas lidas -> {written} gravadas")

    derive_status(db)
    if unmatched and verbose:
        print(f"  ! abas ignoradas (nome nao reconhecido): {', '.join(unmatched)}")
    return totals
