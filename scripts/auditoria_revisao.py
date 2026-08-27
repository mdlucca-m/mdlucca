#!/usr/bin/env python3
"""Auditoria de consistencia do protocolo de revisao sistematica (handebol).

Confere o manuscrito ABNT (.docx) contra a biblioteca curada (.sqlite) e a
planilha de exportacao (.xlsx), e reporta divergencias numericas, violacoes de
elegibilidade, problemas de integridade de metadados e desvios de formato ABNT.

Uso:
    python3 scripts/auditoria_revisao.py ESTUDO.docx BIBLIOTECA.sqlite [BIBLIOTECA.xlsx]

Sai com codigo 1 se algum achado BLOQUEADOR for encontrado.
"""
from __future__ import annotations

import collections
import re
import sqlite3
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Sub-variaveis da base que constituem construto psicologico.
SUBVAR_PSICOLOGICAS = {
    "Ansiedade", "Estresse", "Motivacao", "Cognicao / Tomada de decisao",
    "Bem-estar", "Enfrentamento (coping)", "Percepcao de esforco",
    "Autoconfianca / Autoeficacia", "Habilidades mentais",
    "Engajamento / satisfacao", "Coesao / Lideranca", "Humor / Afeto",
    "Saude mental", "Personalidade", "Depressao",
    "Resiliencia / Mental toughness", "Burnout", "Sono / Sonolencia",
    "Medo de re-lesao / prontidao", "Imagem corporal / alimentar",
}
# Construtos "brandos": psicofisicos ou perifericos ao objeto da revisao.
SUBVAR_BRANDAS = {
    "Percepcao de esforco", "Bem-estar", "Sono / Sonolencia",
    "Cognicao / Tomada de decisao",
}
# Familias da Tabela 4 do manuscrito -> sub-variaveis correspondentes na base.
FAMILIAS = {
    "ansiedade e estresse": ({"Ansiedade", "Estresse"}, 95),
    "motivacao": ({"Motivacao"}, 50),
    "cognicao e atencao": ({"Cognicao / Tomada de decisao"}, 43),
    "burnout e saude mental": ({"Burnout", "Saude mental", "Depressao"}, 35),
    "coping e resiliencia": ({"Enfrentamento (coping)", "Resiliencia / Mental toughness"}, 26),
    "sono e recuperacao": ({"Sono / Sonolencia"}, 24),
    "autoeficacia e confianca": ({"Autoconfianca / Autoeficacia"}, 21),
    "humor e afeto": ({"Humor / Afeto"}, 16),
    "personalidade": ({"Personalidade"}, 13),
    "coesao e grupo": ({"Coesao / Lideranca"}, 13),
}
TERMOS_HANDEBOL = ("handball", "handebol", "balonmano", "andebol", "handboll", "handbal")
JANELA = (2006, 2026)

achados: list[tuple[str, str, str]] = []


def reportar(nivel: str, codigo: str, msg: str) -> None:
    achados.append((nivel, codigo, msg))


# --------------------------------------------------------------------------- docx
def ler_docx(caminho: str) -> tuple[str, list[list[list[str]]], dict]:
    """Devolve (texto_dos_paragrafos, tabelas, propriedades_de_secao)."""
    z = zipfile.ZipFile(caminho)
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{W}body")
    paragrafos, tabelas = [], []
    for el in body:
        if el.tag == f"{W}p":
            paragrafos.append(" ".join("".join(t.text or "" for t in el.iter(f"{W}t")).split()))
        elif el.tag == f"{W}tbl":
            tabelas.append([
                [" ".join("".join(t.text or "" for t in tc.iter(f"{W}t")).split())
                 for tc in tr.findall(f"{W}tc")]
                for tr in el.findall(f"{W}tr")
            ])
    sect = body.find(f"{W}sectPr")
    props = {}
    if sect is not None:
        for filho in sect:
            props[filho.tag.split("}")[1]] = {k.split("}")[1]: v for k, v in filho.attrib.items()}
    # itálico/negrito em qualquer run da secao de referencias
    texto = "\n".join(paragrafos)
    corte = texto.find("REFERÊNCIAS")
    destaque = 0
    for el in body:
        if el.tag != f"{W}p":
            continue
        t = "".join(x.text or "" for x in el.iter(f"{W}t"))
        if " DOI: " not in t:
            continue
        for r in el.findall(f"{W}r"):
            rPr = r.find(f"{W}rPr")
            if rPr is not None and (rPr.find(f"{W}i") is not None or rPr.find(f"{W}b") is not None):
                destaque += 1
                break
    props["_refs_com_destaque"] = destaque
    return texto, tabelas, props


def auditar_docx(texto: str, tabelas: list, props: dict) -> dict:
    corte = texto.find("REFERÊNCIAS")
    corpo, refs = texto[:corte], texto[corte:texto.find("APÊNDICE A")]
    linhas_ref = [l for l in refs.split("\n") if " DOI: " in l]

    # --- ABNT: pagina e margens
    pg = props.get("pgSz", {})
    larg, alt = int(pg.get("w", 0)), int(pg.get("h", 0))
    if pg.get("orient") == "landscape" or larg > alt:
        reportar("ABNT", "A1", f"Pagina em paisagem ({larg/566.9:.1f} x {alt/566.9:.1f} cm); "
                               "NBR 14724 exige A4 retrato (21,0 x 29,7 cm).")
    elif (larg, alt) != (11906, 16838):
        reportar("ABNT", "A1", f"Pagina nao e A4: {larg/566.9:.1f} x {alt/566.9:.1f} cm.")
    mg = props.get("pgMar", {})
    if mg:
        esq, dir_, sup, inf = (int(mg.get(k, 0)) / 566.9 for k in ("left", "right", "top", "bottom"))
        if abs(esq - 3.0) > 0.15 or abs(sup - 3.0) > 0.15 or abs(dir_ - 2.0) > 0.15 or abs(inf - 2.0) > 0.15:
            reportar("ABNT", "A1", f"Margens esq={esq:.1f} sup={sup:.1f} dir={dir_:.1f} inf={inf:.1f} cm; "
                                   "NBR 14724 exige 3/3/2/2.")

    # --- ABNT: referencias
    dobrados = [l for l in linhas_ref if re.search(r"\.\.\s", l)]
    if dobrados:
        reportar("ABNT", "A2", f"{len(dobrados)}/{len(linhas_ref)} referencias com ponto duplo "
                               f"(ex.: {dobrados[0][:38]!r}).")
    if props.get("_refs_com_destaque", 0) == 0 and linhas_ref:
        reportar("ABNT", "A3", f"Nenhuma das {len(linhas_ref)} referencias traz o titulo do periodico "
                               "em destaque tipografico (NBR 6023).")

    # --- referencias nao citadas
    chaves = {}
    for l in linhas_ref:
        m = re.match(r"^([A-ZÀ-Ý][A-ZÀ-Ý'’\-]+)[,;]", l)
        a = re.search(r",\s*((?:19|20)\d{2})\.\s*DOI", l)
        if m and a:
            chaves[(m.group(1), a.group(1))] = l[:60]
    nao_citadas = [f"{s} ({y})" for (s, y) in chaves if s not in corpo]
    if nao_citadas:
        reportar("ABNT", "A4", f"{len(nao_citadas)} referencia(s) nunca citada(s) no corpo: "
                               + "; ".join(sorted(nao_citadas)))

    # --- estrutura obrigatoria
    faltando = [s for s in ("RESUMO", "ABSTRACT", "PALAVRAS-CHAVE", "SUMÁRIO", "CONCLUS")
                if s not in texto]
    if faltando:
        reportar("ABNT", "A6", "Secoes ausentes no documento: " + ", ".join(faltando))
    pend = re.findall(r"\[A PREENCHER: ([^\]]*)\]", texto)
    if pend:
        reportar("ABNT", "A8", f"{len(pend)} bloco(s) [A PREENCHER]: " + "; ".join(pend))
    for ph in ("[Autoria]", "[Instituição]", "[Cidade, ano]"):
        if ph in texto:
            reportar("ABNT", "A8", f"Folha de rosto com marcador nao preenchido: {ph}")

    # --- numeros declarados no corpo
    def num(padrao, grupo=1):
        m = re.search(padrao, corpo)
        return int(m.group(grupo).replace(".", "")) if m else None

    n = {
        "identificados": num(r"identificou (\d+) registros"),
        "duplicatas": num(r"remoção de (\d+) duplicatas"),
        "unicos": num(r"restaram (\d+) registros únicos"),
        "psico": num(r"Foram recuperados (\d+) registros com conteúdo psicológico"),
        "escopo": num(r"Dos (\d+) registros no escopo"),
        "triagem": num(r"(\d+) dispõem de material para triagem"),
        "analise": num(r"e (\d+) permanecem em análise"),
        "recentes": num(r"com (\d+) registros entre 2016"),
        "antigos": num(r"contra (\d+) (?:registros )?entre 2006"),
        "textos": num(r"mineração dos (\d+) textos completos"),
        "sem_resumo": num(r"desprovidos de resumo \((\d+)\)"),
        "fora_escopo": num(r"e (\d+) registros sem qualquer menção"),
    }

    if n["identificados"] and n["duplicatas"] and n["unicos"]:
        if n["identificados"] - n["duplicatas"] != n["unicos"]:
            reportar("GRAVE", "G3", f"PRISMA nao fecha: {n['identificados']} - {n['duplicatas']} "
                                    f"= {n['identificados'] - n['duplicatas']}, mas o texto diz {n['unicos']}.")
    if n["psico"] and n["unicos"] and n["psico"] > n["unicos"]:
        reportar("BLOQUEADOR", "B1",
                 f"O corpus reportado ({n['psico']} registros com conteudo psicologico) e MAIOR que o "
                 f"total de unicos do PRISMA ({n['unicos']}): as secoes 4.2-4.3 nao descrevem o fluxo "
                 "de busca, e sim outro corpus.")
    if n["recentes"] and n["antigos"] and n["psico"]:
        soma = n["recentes"] + n["antigos"]
        if soma != n["psico"]:
            reportar("BLOQUEADOR", "B2",
                     f"Distribuicao temporal nao cobre o corpus: {n['recentes']} + {n['antigos']} = {soma}, "
                     f"mas o corpus tem {n['psico']}; {n['psico'] - soma} registros ficam sem declaracao.")
    if n["sem_resumo"] and n["analise"] and n["sem_resumo"] != n["analise"]:
        reportar("GRAVE", "G3", f"Registros sem resumo: 3.11 diz {n['sem_resumo']}, 3.6 diz "
                                f"{n['analise']} 'em analise'.")

    # --- Tabela 1: soma por base
    t1 = next((t for t in tabelas if t and t[0][:1] == ["Base"]), None)
    if t1:
        soma = sum(int(r[3]) for r in t1[1:] if len(r) > 3 and r[3].isdigit())
        if n["identificados"] and soma != n["identificados"]:
            reportar("GRAVE", "G1", f"Tabela 1 soma {soma} recuperados, texto declara {n['identificados']}.")
        bases_docx = {r[0] for r in t1[1:] if r}
    else:
        bases_docx = set()

    # --- Tabela 4: base implicita das porcentagens
    t4 = next((t for t in tabelas if t and t[0][:1] == ["Família de construto"]), None)
    if t4:
        linhas = [(r[0], int(r[1]), float(r[2].replace(",", "."))) for r in t4[1:] if len(r) > 2]
        total = sum(x[1] for x in linhas)
        base = round(linhas[0][1] / (linhas[0][2] / 100))
        reportar("GRAVE", "G4", f"Tabela 4: as porcentagens implicam base n={base} (soma dos registros "
                                f"= {total}), numero que nao aparece em nenhum ponto do texto.")

    # --- referencia cruzada a tabelas
    for m in re.finditer(r"apresentadas na (Tabela \d+)|dados da (Tabela \d+) mostram", corpo):
        alvo = m.group(1) or m.group(2)
        if alvo == "Tabela 6":
            reportar("ABNT", "A5", "Texto remete a 'Tabela 6' (distribuicao geografica) para os dados "
                                   "de praticas de relato, que estao na Tabela 7.")
    return {"numeros": n, "bases_docx": bases_docx, "tabelas": tabelas}


# --------------------------------------------------------------------------- sqlite
def auditar_base(caminho: str, ctx: dict) -> None:
    con = sqlite3.connect(caminho)
    q1 = lambda s, p=(): con.execute(s, p).fetchone()[0]
    n_total = q1("SELECT COUNT(*) FROM artigo")
    psico = {r[0] for r in con.execute(
        "SELECT artigo_id FROM artigo_variavel WHERE variavel='psicologicas'")}
    marcas = ",".join("?" * len(psico))
    decl = ctx["numeros"]

    print(f"  base: {n_total} artigos; {len(psico)} marcados 'psicologicas'")
    if decl.get("psico") and len(psico) == decl["psico"]:
        reportar("BLOQUEADOR", "B1",
                 f"Confirmado: os {decl['psico']} registros das secoes 4.2-4.3 sao exatamente o recorte "
                 f"'psicologicas' da biblioteca de {n_total} artigos, e nao os "
                 f"{decl.get('unicos')} unicos da busca sistematica.")

    # janela temporal
    fora = q1(f"SELECT COUNT(*) FROM artigo WHERE id IN ({marcas}) AND "
              f"CAST(ano AS INTEGER) NOT BETWEEN {JANELA[0]} AND {JANELA[1]}", tuple(psico))
    if fora:
        amin = q1("SELECT MIN(CAST(ano AS INTEGER)) FROM artigo WHERE ano<>''")
        reportar("BLOQUEADOR", "B2", f"{fora} dos {len(psico)} registros reportados estao fora da janela "
                                     f"{JANELA[0]}-{JANELA[1]} declarada no Quadro 1 (a biblioteca comeca em {amin}).")

    # delineamentos inelegiveis (Quadro 2)
    inel = q1(f"SELECT COUNT(*) FROM artigo WHERE id IN ({marcas}) AND ("
              "tipo_estudo LIKE '%evis%' OR tipo_estudo LIKE '%apitulo%' OR "
              "tipo_estudo LIKE '%ditorial%' OR tipo_estudo LIKE '%rotocolo%' OR "
              "tipo_estudo LIKE '%anais%')", tuple(psico))
    if inel:
        reportar("BLOQUEADOR", "B3", f"{inel} registros do corpus reportado tem delineamento excluido "
                                     "pelo Quadro 2 (revisoes, capitulos de livro, anais).")

    # mencao a handebol
    cond = " AND ".join(
        f"LOWER(COALESCE(titulo,'')||' '||COALESCE(resumo,'')||' '||COALESCE(palavras_chave,'')) "
        f"NOT LIKE '%{t}%'" for t in TERMOS_HANDEBOL)
    sem_hb = q1(f"SELECT COUNT(*) FROM artigo WHERE id IN ({marcas}) AND {cond}", tuple(psico))
    if sem_hb:
        reportar("BLOQUEADOR", "B3", f"{sem_hb} registros do corpus reportado nao mencionam handebol em "
                                     "titulo, resumo ou palavras-chave, embora 3.11 afirme que a varredura "
                                     f"ja removeu {decl.get('fora_escopo')} registros nessa condicao.")

    # inflacao da marcacao psicologica
    sub = collections.defaultdict(set)
    for a, s in con.execute("SELECT artigo_id, subvariavel FROM artigo_subvariavel"):
        sub[a].add(s)
    sem_psi = sum(1 for a in psico if not (sub.get(a, set()) & SUBVAR_PSICOLOGICAS))
    so_brandas = sum(1 for a in psico
                     if (sub.get(a, set()) & SUBVAR_PSICOLOGICAS)
                     and (sub.get(a, set()) & SUBVAR_PSICOLOGICAS) <= SUBVAR_BRANDAS)
    if sem_psi:
        reportar("BLOQUEADOR", "B4",
                 f"{sem_psi} dos {len(psico)} registros marcados 'psicologicas' ({100*sem_psi/len(psico):.0f}%) "
                 "nao possuem NENHUMA sub-variavel psicologica na propria base; apenas "
                 f"{len(psico) - sem_psi - so_brandas} tem construto psicologico nao-psicofisico.")

    # instrumentos: a Tabela 5 e psicometrica?
    NAO_PSICOMETRICOS = ("agilidade", "jump", "sprint", "salivar", "lactato", "DXA", "bioimped",
                         "GPS", "LPS", "forca", "FC", "fotocelul", "1RM", "Optojump", "Yo-Yo",
                         "Wingate", "RAST", "Radar", "Dinamometro", "Eletromiografia", "Acelerometro")
    cnt = collections.Counter()
    for (s,) in con.execute(
            f"SELECT instrumentos FROM artigo WHERE id IN ({marcas}) AND COALESCE(instrumentos,'')<>''",
            tuple(psico)):
        for t in (x.strip() for x in s.split(",")):
            if t:
                cnt[t] += 1
    top12 = cnt.most_common(12)
    nao_psi = [k for k, _ in top12 if any(p.lower() in k.lower() for p in NAO_PSICOMETRICOS)]
    if nao_psi:
        reportar("BLOQUEADOR", "B5",
                 f"Tabela 5 rotulada 'instrumentos psicometricos': {len(nao_psi)} dos 12 itens mais "
                 "frequentes sao instrumentos fisicos/fisiologicos (" + ", ".join(nao_psi[:5]) + "...). "
                 "O campo `instrumentos` lista todos os instrumentos do artigo, nao os psicometricos.")

    # familias da Tabela 4
    print("  familias de construto: docx vs recontagem na base")
    for nome, (subs, docx_n) in FAMILIAS.items():
        base_n = sum(1 for a in psico if sub.get(a, set()) & subs)
        print(f"    {nome:26s} docx={docx_n:4d}  base={base_n:4d}")

    # integridade de metadados
    suspeitos = q1("SELECT COUNT(*) FROM artigo WHERE doi_suspeito=1")
    susp_psi = q1(f"SELECT COUNT(*) FROM artigo WHERE id IN ({marcas}) AND doi_suspeito=1", tuple(psico))
    if suspeitos:
        reportar("GRAVE", "G5", f"A base sinaliza doi_suspeito=1 em {suspeitos} registros "
                                f"({susp_psi} dentro do corpus reportado); o manuscrito nao os menciona.")
    incoerentes = []
    for ano, doi, tit in con.execute(
            "SELECT ano, doi, titulo FROM artigo WHERE COALESCE(doi,'')<>'' AND ano<>''"):
        m = re.search(r"\.((?:19|20)\d{2})\.", doi)
        if m and abs(int(m.group(1)) - int(ano)) >= 2:
            incoerentes.append((ano, m.group(1), doi, tit[:40]))
    if incoerentes:
        a = incoerentes[0]
        reportar("GRAVE", "G5", f"{len(incoerentes)} registros com ano do DOI divergente do campo `ano` "
                                f"em >=2 anos (ex.: ano={a[0]}, DOI {a[2]}).")

    # extracao com ruido
    ruido_n = q1("SELECT COUNT(*) FROM artigo WHERE amostra GLOB 'n = 19[0-9][0-9]' "
                 "OR amostra GLOB 'n = 20[0-2][0-9]'")
    if ruido_n:
        ex = con.execute("SELECT amostra, substr(titulo,1,45) FROM artigo WHERE "
                         "amostra GLOB 'n = 20[0-2][0-9]' LIMIT 1").fetchone()
        reportar("GRAVE", "G6", f"{ruido_n} registros com `amostra` no intervalo de anos-calendario "
                                f"(provavel ano lido como tamanho amostral; ex.: {ex[0]!r} em {ex[1]!r}).")
    nao_esp = q1("SELECT COUNT(*) FROM artigo WHERE desenho_estudo='Nao especificado no resumo'")
    if nao_esp / n_total > 0.4:
        reportar("GRAVE", "G6", f"`desenho_estudo` esta vazio de conteudo em {nao_esp}/{n_total} "
                                f"({100*nao_esp/n_total:.0f}%) dos registros, e e o campo que alimenta a "
                                "caracterizacao de delineamentos.")
    sem_vol = q1("SELECT COUNT(*) FROM artigo WHERE COALESCE(referencia_abnt,'')<>'' "
                 "AND referencia_abnt NOT LIKE '%v. %'")
    if sem_vol:
        reportar("GRAVE", "G5", f"{sem_vol} referencias ABNT geradas sem volume.")

    # fontes declaradas vs fontes da base
    fontes_base = dict(con.execute("SELECT fonte, COUNT(*) FROM artigo GROUP BY fonte"))
    print("  fontes na base:", fontes_base)
    if ctx["bases_docx"]:
        norm = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
        so_base = [f for f in fontes_base if not any(norm(f)[:6] in norm(b) for b in ctx["bases_docx"])]
        so_docx = [b for b in ctx["bases_docx"] if not any(norm(f)[:6] in norm(b) for f in fontes_base)]
        if so_base or so_docx:
            reportar("GRAVE", "G1", f"Tabela 1 e a base discordam sobre as fontes. So na base: {so_base}. "
                                    f"So na Tabela 1: {so_docx}.")

    # deduplicacao da biblioteca entregue
    def folda(t):
        t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
        return re.sub(r"[^a-z0-9]", "", t)
    tit = collections.Counter(folda(t) for (t,) in con.execute("SELECT titulo FROM artigo"))
    dup_tit = sum(v - 1 for v in tit.values() if v > 1)
    dup_doi = q1("SELECT COUNT(*) FROM (SELECT doi FROM artigo WHERE COALESCE(doi,'')<>'' "
                 "GROUP BY LOWER(doi) HAVING COUNT(*)>1)")
    print(f"  deduplicacao da biblioteca entregue: {dup_doi} DOIs repetidos, {dup_tit} titulos repetidos")

    # Apendice B contra a base
    t9 = next((t for t in ctx["tabelas"] if t and t[0][:1] == ["Estudo"]), None)
    if t9:
        divergentes = 0
        for linha in t9[1:]:
            titulo_trunc, n_docx = linha[0], linha[3]
            r = con.execute("SELECT amostra FROM artigo WHERE titulo LIKE ?",
                            (titulo_trunc + "%",)).fetchone()
            if r and r[0]:
                m = re.search(r"(\d+)", r[0])
                if m and n_docx.isdigit() and m.group(1) != n_docx:
                    divergentes += 1
        if divergentes:
            reportar("BLOQUEADOR", "B6", f"Apendice B (Tabela 9): {divergentes} de {len(t9)-1} linhas "
                                         "declaram um `n` diferente do campo `amostra` da base para o "
                                         "mesmo estudo.")
    con.close()


# --------------------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    print("== manuscrito ==")
    texto, tabelas, props = ler_docx(argv[1])
    ctx = auditar_docx(texto, tabelas, props)
    print(f"  {len(texto.splitlines())} paragrafos, {len(tabelas)} tabelas")
    print("== biblioteca ==")
    auditar_base(argv[2], ctx)

    print("\n== ACHADOS ==")
    ordem = {"BLOQUEADOR": 0, "GRAVE": 1, "ABNT": 2, "METODO": 3}
    vistos = set()
    for nivel, cod, msg in sorted(achados, key=lambda a: (ordem.get(a[0], 9), a[1])):
        if (cod, msg) in vistos:
            continue
        vistos.add((cod, msg))
        print(f"[{nivel:11s}] {cod}: {msg}")
    n_bloq = sum(1 for a in achados if a[0] == "BLOQUEADOR")
    print(f"\n{len(vistos)} achados ({n_bloq} bloqueadores).")
    return 1 if n_bloq else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
