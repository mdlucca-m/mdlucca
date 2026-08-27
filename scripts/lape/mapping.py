"""Dicionarios de sinonimos: abas, colunas e vocabulario controlado.

O objetivo e absorver as planilhas do LAPE como elas ja existem, sem
exigir que o laboratorio renomeie colunas. Toda comparacao e feita sobre
a forma normalizada (sem acento, minuscula, separadores virando '_').
"""
from __future__ import annotations

from .util import norm_key

# ----------------------------------------------------------------------
# Abas
# ----------------------------------------------------------------------
SHEET_ALIASES: dict[str, tuple[str, ...]] = {
    "research_lines": ("linhas_de_pesquisa", "linhas_pesquisa", "linhas", "research_lines", "areas"),
    "institutions": ("instituicoes", "instituicao", "institutions", "parcerias", "unidades"),
    "members": ("integrantes", "membros", "equipe", "pesquisadores", "members", "colaboradores"),
    "articles": ("artigos", "producao", "publicacoes", "articles", "papers", "estudos", "manuscritos"),
    "authors": ("autoria", "autores", "authors", "artigo_autores", "coautoria"),
    "submissions": ("submissoes", "submissao", "submissions", "tentativas", "envios"),
    "rejection_reasons": ("motivos_de_recusa", "motivos_recusa", "motivos", "rejection_reasons"),
    "projects": ("projetos", "projeto", "projects", "pesquisas", "editais"),
    "project_members": ("equipe_do_projeto", "projeto_integrantes", "project_members",
                        "participacao_em_projetos"),
    "events": ("eventos", "atividades", "reunioes", "agenda", "calendario", "events"),
    "event_participants": ("participacao", "participantes", "presenca", "event_participants"),
}

# ----------------------------------------------------------------------
# Colunas
# ----------------------------------------------------------------------
COLUMN_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "research_lines": {
        "code": ("codigo", "cod", "sigla", "code", "id"),
        "name": ("linha_de_pesquisa", "linha", "nome", "titulo", "name", "descricao_curta"),
        "description": ("descricao", "detalhamento", "ementa", "resumo", "description"),
        "coordinator": ("coordenador", "responsavel", "lider", "coordenacao"),
        "started_on": ("inicio", "data_de_inicio", "data_inicio", "desde", "ano_de_inicio"),
        "keywords": ("palavras_chave", "palavras", "keywords", "descritores"),
        "active": ("ativa", "ativo", "vigente", "em_andamento", "status"),
    },
    "institutions": {
        "name": ("instituicao", "nome", "name", "universidade", "orgao"),
        "acronym": ("sigla", "acronimo", "abreviacao", "acronym"),
        "city": ("cidade", "municipio", "city", "local"),
        "state": ("estado", "uf", "state", "provincia"),
        "country": ("pais", "country"),
        "latitude": ("latitude", "lat"),
        "longitude": ("longitude", "lon", "lng", "long"),
    },
    "members": {
        "full_name": ("nome", "nome_completo", "integrante", "membro", "pesquisador", "full_name", "autor"),
        "short_name": ("nome_curto", "apelido", "nome_de_citacao", "citacao", "short_name"),
        "aliases": ("variacoes", "outros_nomes", "aliases", "nomes_alternativos", "grafias"),
        "lattes_id": ("lattes", "id_lattes", "lattes_id", "curriculo_lattes"),
        "orcid": ("orcid", "orcid_id"),
        "email": ("email", "e_mail", "correio"),
        "role": ("funcao", "vinculo", "papel", "cargo", "categoria", "role", "nivel"),
        "degree": ("titulacao", "formacao", "grau", "degree", "escolaridade"),
        "phone": ("telefone", "fone", "celular", "contato", "phone"),
        "bio": ("resumo", "biografia", "minibio", "apresentacao", "bio", "sobre"),
        "photo_url": ("foto", "url_da_foto", "photo_url", "imagem"),
        "openalex_id": ("openalex", "openalex_id", "id_openalex"),
        "scopus_author_id": ("scopus_author_id", "id_scopus_autor", "author_id_scopus"),
        "research_line": ("linha_de_pesquisa", "linha", "area", "research_line"),
        "institution": ("instituicao", "universidade", "vinculo_institucional", "institution"),
        "joined_on": ("entrada", "data_de_entrada", "ingresso", "inicio", "desde"),
        "left_on": ("saida", "data_de_saida", "desligamento", "fim", "ate"),
        "is_external": ("externo", "colaborador_externo", "is_external"),
        "active": ("ativo", "ativa", "situacao", "status"),
        "advisor": ("orientador", "orientadora", "professor_responsavel", "supervisor",
                    "advisor", "responsavel"),
        "co_advisor": ("coorientador", "co_orientador", "coorientadora", "co_advisor",
                       "segundo_orientador"),
        "thesis_title": ("titulo_da_tese", "tese", "dissertacao", "titulo_do_trabalho",
                         "thesis_title", "titulo_da_dissertacao"),
        "thesis_kind": ("tipo_de_trabalho", "nivel_do_trabalho", "thesis_kind",
                        "tese_ou_dissertacao"),
        "thesis_status": ("situacao_da_tese", "andamento_da_tese", "thesis_status",
                          "estagio_da_tese"),
        "thesis_due_on": ("prazo_para_conclusao", "prazo", "previsao_de_defesa",
                          "data_de_defesa", "thesis_due_on", "conclusao_prevista"),
        "topics": ("temas", "modalidades", "objetos_de_estudo", "topics", "palavras_chave",
                   "assuntos"),
        "scholarship": ("bolsa", "tipo_de_bolsa", "agencia_de_fomento", "scholarship",
                        "financiadora_da_bolsa"),
        "scholarship_until": ("fim_da_bolsa", "vigencia_da_bolsa", "bolsa_ate",
                              "scholarship_until", "termino_da_bolsa"),
    },
    "articles": {
        "internal_code": ("codigo", "cod", "id", "codigo_interno", "id_artigo", "identificador"),
        "title": ("titulo", "titulo_do_artigo", "title", "artigo", "nome_do_artigo", "manuscrito"),
        "authors": ("autores", "autoria", "authors", "equipe", "autores_do_artigo", "coautores"),
        "status": ("status", "situacao", "estagio", "fase", "andamento", "etapa"),
        "research_line": ("linha_de_pesquisa", "linha", "area", "research_line", "tematica"),
        "study_type": ("tipo_de_estudo", "tipo", "delineamento", "desenho", "metodo", "study_type"),
        "language": ("idioma", "lingua", "language"),
        "started_on": ("data_de_inicio", "data_inicio", "inicio", "comeco", "started_on", "data_de_inicio_do_artigo"),
        "first_submission_on": (
            "data_de_submissao", "data_submissao", "submissao", "primeira_submissao",
            "data_da_primeira_submissao", "submitted_on",
        ),
        "accepted_on": ("data_do_aceite", "data_de_aceite", "data_aceite", "aceite", "accepted_on", "data_do_aceite_final"),
        "published_on": ("data_de_publicacao", "data_publicacao", "publicacao", "published_on", "data_pub"),
        "year_published": ("ano", "ano_de_publicacao", "ano_publicacao", "year", "ano_pub"),
        "journal": ("periodico", "revista", "journal", "periodico_revista", "veiculo"),
        "issn": ("issn",),
        "qualis": ("qualis", "estrato", "qualis_capes"),
        "impact_factor": ("fator_de_impacto", "fator_impacto", "impacto", "jif", "impact_factor", "if"),
        "doi": ("doi", "digital_object_identifier"),
        "url": ("link", "url", "endereco", "pagina"),
        "wos_id": ("wos_id", "ut_wos", "accession_number", "id_wos"),
        "scopus_id": ("scopus_id", "eid", "id_scopus"),
        "wos_citations": ("citacoes_wos", "wos", "citacoes_web_of_science", "wos_citacoes", "citations_wos"),
        "scopus_citations": ("citacoes_scopus", "scopus", "scopus_citacoes", "citations_scopus"),
        "open_access": ("acesso_aberto", "open_access", "oa"),
        "notes": ("observacoes", "obs", "notas", "comentarios", "notes"),
        "lead": ("responsavel", "lider", "autor_principal", "primeiro_autor", "responsavel_pelo_artigo"),
        "version_1": ("data_da_primeira_versao", "primeira_versao", "data_primeira_versao", "v1"),
        "version_2": ("data_segunda_versao", "data_da_segunda_versao", "segunda_versao", "v2"),
        "version_3": ("data_terceira_versao", "data_da_terceira_versao", "terceira_versao", "v3"),
        "version_4": ("data_quarta_versao", "data_da_quarta_versao", "quarta_versao", "v4"),
        "version_final": ("data_versao_final", "data_da_versao_final", "versao_final"),
        "internal_review": ("revisao_interna", "data_revisao_interna", "revisao_interna_em"),
        "rejection_reason": ("motivo_da_recusa", "motivo_recusa", "motivo", "razao_da_recusa"),
        "submission_journal": ("revista_submetida", "periodico_submetido", "revista_alvo"),
    },
    "authors": {
        "article": ("artigo", "titulo", "titulo_do_artigo", "codigo", "id_artigo", "article"),
        "author_name": ("autor", "nome", "autor_nome", "integrante", "author"),
        "author_order": ("ordem", "posicao", "ordem_de_autoria", "order", "n"),
        "is_corresponding": ("correspondente", "autor_correspondente", "corresponding"),
        "is_external": ("externo", "colaborador_externo", "is_external"),
    },
    "submissions": {
        "article": ("artigo", "titulo", "titulo_do_artigo", "codigo", "id_artigo", "article"),
        "attempt_no": ("tentativa", "n_tentativa", "numero_da_tentativa", "attempt", "rodada", "ordem"),
        "journal": ("periodico", "revista", "journal", "veiculo"),
        "issn": ("issn",),
        "submitted_on": ("data_de_submissao", "data_submissao", "submissao", "enviado_em", "submitted_on"),
        "decision": ("decisao", "resultado", "desfecho", "status", "situacao", "decision"),
        "decision_on": ("data_de_decisao", "data_da_decisao", "data_decisao", "data_do_resultado",
                        "resposta_em", "decision_on", "data_do_parecer"),
        "rejection_reason": ("motivo_observacao", "motivo_da_recusa", "motivo_recusa", "motivo",
                             "razao", "justificativa", "motivo_ou_observacao"),
        "rejection_notes": ("observacoes", "observacao", "obs", "detalhes", "parecer", "comentarios"),
        "desk_reject": ("desk_reject", "recusa_direta", "recusa_editorial", "sem_revisao"),
        "review_rounds": ("rodadas", "rodadas_de_revisao", "n_revisoes", "review_rounds"),
    },
    "rejection_reasons": {
        "code": ("codigo", "cod", "code"),
        "label": ("motivo", "descricao", "label", "nome", "razao"),
        "category": ("categoria", "grupo", "tipo", "category"),
    },
    "projects": {
        "code": ("codigo", "cod", "sigla", "id", "code"),
        "name": ("projeto", "titulo", "nome", "name", "titulo_do_projeto"),
        "description": ("descricao", "resumo", "objetivo", "description"),
        "research_line": ("linha_de_pesquisa", "linha", "area"),
        "coordinator": ("coordenador", "responsavel", "lider", "coordenacao"),
        "kind": ("tipo", "natureza", "modalidade", "kind"),
        "funder": ("financiador", "agencia", "fomento", "edital", "funder"),
        "grant_number": ("processo", "numero_do_processo", "grant", "termo"),
        "amount": ("valor", "recurso", "orcamento", "amount"),
        "started_on": ("inicio", "data_de_inicio", "data_inicio", "started_on"),
        "ended_on": ("termino", "fim", "data_de_termino", "data_fim", "ended_on"),
        "status": ("status", "situacao", "andamento"),
        "ethics_approval": ("parecer_etico", "caae", "comite_de_etica", "parecer"),
        "url": ("link", "url", "pagina"),
        "members": ("integrantes", "equipe", "participantes", "membros", "pesquisadores"),
    },
    "project_members": {
        "project": ("projeto", "codigo", "titulo", "project"),
        "member": ("integrante", "nome", "participante", "membro", "member"),
        "role": ("funcao", "papel", "role"),
        "joined_on": ("entrada", "desde", "inicio"),
    },
    "events": {
        "external_key": ("codigo", "id", "chave", "external_key"),
        "kind": ("tipo", "categoria", "natureza", "kind", "tipo_de_atividade"),
        "title": ("titulo", "atividade", "evento", "assunto", "descricao_curta", "nome", "title"),
        "description": ("descricao", "pauta", "detalhes", "observacoes", "description"),
        "start_at": ("data", "data_de_inicio", "inicio", "data_hora", "quando", "start_at", "data_inicio"),
        "end_at": ("data_de_termino", "fim", "termino", "end_at", "data_fim"),
        "all_day": ("dia_inteiro", "all_day", "dia_todo"),
        "status": ("status", "situacao", "confirmado"),
        "location_name": ("local", "sala", "localizacao", "location", "endereco"),
        "institution": ("instituicao", "universidade", "institution"),
        "city": ("cidade", "municipio", "city"),
        "state": ("estado", "uf", "state"),
        "country": ("pais", "country"),
        "latitude": ("latitude", "lat"),
        "longitude": ("longitude", "lon", "lng", "long"),
        "research_line": ("linha_de_pesquisa", "linha", "area"),
        "participants": ("participantes", "presentes", "integrantes", "equipe", "participants"),
        "url": ("link", "url", "ata", "registro"),
    },
    "event_participants": {
        "event": ("evento", "atividade", "titulo", "codigo", "event"),
        "member": ("integrante", "participante", "nome", "membro", "member"),
        "role": ("funcao", "papel", "role"),
        "attended": ("presente", "presenca", "compareceu", "attended"),
    },
}

# Abas que sao painel/instrucao e nao devem virar dados: o pipeline
# recalcula esses indicadores a partir das tabelas primarias.
SHEET_IGNORE: tuple[str, ...] = (
    "metricas", "metrica", "indicadores", "historico_mensal", "historico",
    "como_usar", "instrucoes", "leia_me", "readme", "dashboard", "painel",
    "resumo", "graficos", "listas", "auxiliar", "aux", "config",
)

# ----------------------------------------------------------------------
# Vocabulario controlado
# ----------------------------------------------------------------------
PROJECT_STATUS_MAP: dict[str, str] = {
    "em_andamento": "em_andamento", "andamento": "em_andamento", "ativo": "em_andamento",
    "ativa": "em_andamento", "em_execucao": "em_andamento", "vigente": "em_andamento",
    "em_curso": "em_andamento",
    "concluido": "concluido", "concluida": "concluido", "finalizado": "concluido",
    "encerrado": "concluido", "encerrada": "concluido",
    "planejado": "planejado", "planejamento": "planejado", "submetido": "planejado",
    "aguardando": "planejado", "em_elaboracao": "planejado",
    "suspenso": "suspenso", "pausado": "suspenso", "cancelado": "suspenso",
    "interrompido": "suspenso",
}

STATUS_MAP: dict[str, str] = {
    "em_producao": "em_producao", "producao": "em_producao", "em_andamento": "em_producao",
    "andamento": "em_producao", "escrita": "em_producao", "em_escrita": "em_producao",
    "redacao": "em_producao", "em_redacao": "em_producao", "em_elaboracao": "em_producao",
    "elaboracao": "em_producao", "coleta": "em_producao", "analise": "em_producao",
    "em_analise_de_dados": "em_producao", "rascunho": "em_producao", "draft": "em_producao",
    "in_progress": "em_producao", "writing": "em_producao",
    "submetido": "submetido", "enviado": "submetido", "submitted": "submetido",
    "em_avaliacao": "submetido", "em_analise": "submetido", "under_review": "em_revisao",
    "em_revisao": "em_revisao", "revisao": "em_revisao", "revisao_solicitada": "em_revisao",
    "major_revision": "em_revisao", "minor_revision": "em_revisao", "em_correcao": "em_revisao",
    "aceito": "aceito", "aceite": "aceito", "aprovado": "aceito", "accepted": "aceito",
    "in_press": "aceito", "no_prelo": "aceito",
    "publicado": "publicado", "published": "publicado", "publicada": "publicado",
    "rejeitado": "rejeitado", "recusado": "rejeitado", "rejected": "rejeitado",
    "negado": "rejeitado", "reprovado": "rejeitado",
    "arquivado": "arquivado", "abandonado": "arquivado", "descontinuado": "arquivado",
    "cancelado": "arquivado", "suspenso": "arquivado", "parado": "arquivado",
}

DECISION_MAP: dict[str, str] = {
    "em_avaliacao": "em_avaliacao", "em_analise": "em_avaliacao", "aguardando": "em_avaliacao",
    "under_review": "em_avaliacao", "submetido": "em_avaliacao", "sem_resposta": "em_avaliacao",
    "revisao_solicitada": "revisao_solicitada", "revisao": "revisao_solicitada",
    "major_revision": "revisao_solicitada", "minor_revision": "revisao_solicitada",
    "revisar_e_reenviar": "revisao_solicitada", "revise_and_resubmit": "revisao_solicitada",
    "aceito": "aceito", "aceite": "aceito", "aprovado": "aceito", "accepted": "aceito",
    "rejeitado": "rejeitado", "recusado": "rejeitado", "rejected": "rejeitado", "negado": "rejeitado",
    "desk_reject": "desk_reject", "recusa_direta": "desk_reject", "recusa_editorial": "desk_reject",
    "rejeicao_sem_revisao": "desk_reject", "desk_rejection": "desk_reject",
    "retirado": "retirado", "withdrawn": "retirado", "cancelado": "retirado",
}

# Vinculo com o laboratorio. A lista e fechada de proposito: "IC",
# "iniciacao cientifica" e "bolsista de IC" sao a mesma coisa, e sem uma
# forma canonica o organograma ganharia tres caixas para um cargo so.
# A ordem e hierarquica -- e ela que empilha os niveis no desenho.
VINCULOS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("coordenacao", "Coordenação",
     ("coordenador", "coordenadora", "chefia", "direcao", "lider")),
    ("professor", "Professor(a)",
     ("professora", "docente", "orientador", "orientadora", "pesquisador_senior")),
    ("pos_doutorado", "Pós-doutorado",
     ("pos_doc", "posdoc", "pos_doutoral", "pd", "pos_doutoranda", "pos_doutorando")),
    ("doutorando", "Doutorando(a)",
     ("doutorado", "doutoranda", "aluno_de_doutorado", "aluna_de_doutorado", "phd")),
    ("mestrando", "Mestrando(a)",
     ("mestrado", "mestranda", "aluno_de_mestrado", "aluna_de_mestrado")),
    ("bolsista_ic", "Bolsista de IC",
     ("ic", "iniciacao_cientifica", "bolsista_de_iniciacao_cientifica", "pibic",
      "bolsista_ic", "bolsista_de_ic")),
    ("bolsista_extensao", "Bolsista de extensão",
     ("extensao", "bolsista_de_extensao", "pibex", "probolsa", "bolsista_extensao")),
    ("voluntario", "Voluntário(a)",
     ("voluntaria", "voluntariado", "sem_bolsa", "colaboracao_voluntaria")),
    ("graduando", "Graduando(a)",
     ("graduacao", "graduanda", "aluno_de_graduacao", "aluna_de_graduacao", "estagiario")),
    ("tecnico", "Técnico(a)",
     ("tecnica", "tecnico_administrativo", "apoio", "secretaria")),
    ("colaborador", "Colaborador(a) externo",
     ("colaboradora", "externo", "externa", "parceiro", "parceira", "convidado")),
)
ROLE_MAP: dict[str, str] = {
    codigo: codigo for codigo, _, _ in VINCULOS
}
for _codigo, _, _sinonimos in VINCULOS:
    for _sinonimo in _sinonimos:
        ROLE_MAP.setdefault(_sinonimo, _codigo)
ROLE_LABEL: dict[str, str] = {codigo: rotulo for codigo, rotulo, _ in VINCULOS}
# Quem orienta. Um mestrando nao aparece como orientador de ninguem no
# organograma, ainda que ajude a tocar o trabalho de um bolsista.
ORIENTAM: tuple[str, ...] = ("coordenacao", "professor", "pos_doutorado")
# Quem tem orientador. Nao e o complemento de ORIENTAM: tecnico e
# colaborador externo nao sao orientados por ninguem, e cobrar deles um
# orientador encheria a lista de pendencias com falso alarme.
ORIENTADOS: tuple[str, ...] = ("pos_doutorado", "doutorando", "mestrando", "bolsista_ic",
                               "bolsista_extensao", "voluntario", "graduando")

THESIS_KIND_MAP: dict[str, str] = {
    "tese": "tese", "doutorado": "tese", "tese_de_doutorado": "tese",
    "dissertacao": "dissertacao", "mestrado": "dissertacao",
    "dissertacao_de_mestrado": "dissertacao",
    "tcc": "tcc", "monografia": "tcc", "trabalho_de_conclusao": "tcc",
    "trabalho_de_conclusao_de_curso": "tcc",
    "relatorio": "relatorio", "relatorio_de_ic": "relatorio", "plano_de_trabalho": "relatorio",
    "projeto": "projeto", "projeto_de_pesquisa": "projeto",
}
THESIS_STATUS_MAP: dict[str, str] = {
    "em_andamento": "em_andamento", "andamento": "em_andamento", "escrita": "em_andamento",
    "em_escrita": "em_andamento", "em_desenvolvimento": "em_andamento",
    "coleta": "coleta", "coleta_de_dados": "coleta", "campo": "coleta",
    "analise": "analise", "analise_de_dados": "analise", "em_analise": "analise",
    "qualificacao": "qualificacao", "qualificado": "qualificacao",
    "em_qualificacao": "qualificacao",
    "defesa_marcada": "defesa_marcada", "defesa_agendada": "defesa_marcada",
    "concluida": "concluida", "concluido": "concluida", "defendida": "concluida",
    "defendido": "concluida", "finalizada": "concluida",
    "trancada": "trancada", "trancado": "trancada", "suspensa": "trancada",
}

EVENT_KIND_MAP: dict[str, str] = {
    "reuniao": "reuniao", "reunioes": "reuniao", "meeting": "reuniao", "encontro": "reuniao",
    "reuniao_de_equipe": "reuniao", "reuniao_geral": "reuniao",
    "coleta": "coleta", "coleta_de_dados": "coleta", "campo": "coleta", "trabalho_de_campo": "coleta",
    "defesa": "defesa", "banca": "defesa", "defesa_de_tese": "defesa", "defesa_de_dissertacao": "defesa",
    "qualificacao": "qualificacao", "exame_de_qualificacao": "qualificacao",
    "congresso": "congresso", "evento_cientifico": "congresso", "simposio": "congresso",
    "conferencia": "congresso", "apresentacao": "congresso",
    "curso": "curso", "capacitacao": "curso", "workshop": "curso", "oficina": "curso",
    "seminario": "seminario", "journal_club": "seminario", "clube_de_revista": "seminario",
    "visita_tecnica": "visita_tecnica", "visita": "visita_tecnica", "intercambio": "visita_tecnica",
    "extensao": "extensao", "acao_de_extensao": "extensao", "atendimento": "extensao",
}

# ----------------------------------------------------------------------
# Resolucao
# ----------------------------------------------------------------------
def resolve_sheet(sheet_name: str) -> str | None:
    """Descobre a qual tabela uma aba corresponde (None = ignorar)."""
    key = norm_key(sheet_name)
    if key in SHEET_IGNORE:
        return None
    for canonical, aliases in SHEET_ALIASES.items():
        if key == canonical or key in aliases:
            return canonical
    for canonical, aliases in SHEET_ALIASES.items():
        if any(alias in key or key in alias for alias in aliases if len(alias) > 4):
            return canonical
    return None


def build_column_map(sheet: str, headers: list) -> dict[str, str]:
    """Mapeia cabecalhos reais da planilha -> campos canonicos."""
    aliases = COLUMN_ALIASES.get(sheet, {})
    reverse: dict[str, str] = {}
    for field, names in aliases.items():
        reverse[field] = field
        for name in names:
            reverse.setdefault(name, field)

    mapping: dict[str, str] = {}
    used: set[str] = set()
    normalized = [(h, norm_key(h)) for h in headers]

    for original, key in normalized:  # 1a passada: correspondencia exata
        field = reverse.get(key)
        if field and field not in used:
            mapping[original] = field
            used.add(field)
    for original, key in normalized:  # 2a passada: correspondencia parcial
        if original in mapping or not key:
            continue
        for alias, field in reverse.items():
            if field in used or len(alias) < 4:
                continue
            if key.startswith(alias) or alias in key:
                mapping[original] = field
                used.add(field)
                break
    return mapping


def map_value(value, table: dict[str, str], default=None):
    key = norm_key(value)
    if not key:
        return default
    if key in table:
        return table[key]
    for candidate, mapped in table.items():
        if key.startswith(candidate) or candidate in key:
            return mapped
    return default
