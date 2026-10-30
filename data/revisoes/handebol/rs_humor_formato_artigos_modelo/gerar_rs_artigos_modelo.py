"""Revisão sistemática do humor no handebol no formato dos artigos modelo do grupo (Atmosphere, 2025; MDPI).

    python3 gerar_rs_artigos_modelo.py      (executar duas vezes: letras de ano repetido)

Dados: rs_dados.py (extração conferida). Referências: refs.py (Crossref), autor-data.
"""
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

os.environ["CITE"] = "autor"
os.environ["CITADOS_FILE"] = "citados_rs_artigos_modelo.json"
import sys
sys.path.insert(0, "/home/user/corrigidos/modelo_mdpi")
from refs import R, MODO as _MODO
import rs_dados as RD

CITE_AUTOR = _MODO == "autor"

AQ = Path(__file__).parent
FIG = AQ / "figuras"
D = json.load(open("/home/user/corrigidos/revisada/dados_rev.json", encoding="utf-8"))
DESF = Path("/home/user/corrigidos/desfechos/DESFECHOS_199.xlsx")
ORI = False   # versão de leitura: Times 12, espaço 1,5, citações autor-data
NOME = "REVISAO_SISTEMATICA_HUMOR_FORMATO_ARTIGOS_MODELO"
N = 34
FONTE = "Times New Roman" if ORI else "Palatino Linotype"
RECUO = Cm(0) if ORI else Cm(4.2)          # coluna de texto do modelo (margem esquerda larga)
ESC_T = 1.2 if ORI else 1.0                 # escala das letras na versão de leitura


def br(x, c=1):
    return f"{x:.{c}f}".replace(".", ",")


def pc(v, n=N, c=1):
    return br(100 * v / n, c) + "%"


def mil(n):
    return f"{int(n):,}".replace(",", ".")


# ================================================================== documento
doc = Document()
st = doc.styles["Normal"]
st.font.name = FONTE
st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
for s in doc.sections:
    s.page_height, s.page_width = Cm(29.7), Cm(21.0)
    s.left_margin, s.right_margin = (Cm(3.0), Cm(2.0)) if ORI else (Cm(1.8), Cm(1.8))
    s.top_margin, s.bottom_margin = (Cm(3.0), Cm(2.0)) if ORI else (Cm(2.0), Cm(1.8))
    s.header_distance = Cm(1.0)


def fmt(par, recuo=True, primeira=0.75, antes=0, depois=0, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, linha=10.85):
    pf = par.paragraph_format
    pf.left_indent = RECUO if recuo else Cm(0)
    pf.first_line_indent = Cm(primeira)
    pf.space_before, pf.space_after = Pt(antes), Pt(depois)
    if ORI:
        pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE if linha >= 10.85 else WD_LINE_SPACING.SINGLE
        pf.space_before, pf.space_after = Pt(antes * 1.2), Pt(depois * 1.2)
    else:
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(linha)
    par.alignment = alinhar
    return par


def runs(par, texto, tam=10, cor=None, italico_base=False):
    """Marcação simples: **negrito**, *itálico*."""
    for parte in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", texto):
        if not parte:
            continue
        if parte.startswith("**"):
            r = par.add_run(parte[2:-2])
            r.bold = True
        elif parte.startswith("*"):
            r = par.add_run(parte[1:-1])
            r.italic = True
        else:
            r = par.add_run(parte)
            r.italic = italico_base
        r.font.size = Pt(round(tam * ESC_T * 2) / 2)
        r.font.name = FONTE
        if cor:
            r.font.color.rgb = RGBColor.from_string(cor)
    return par


def P(texto, **kw):
    tam = kw.pop("tam", 10)
    ital = kw.pop("italico", False)
    return runs(fmt(doc.add_paragraph(), **kw), texto, tam=tam, italico_base=ital)


def H1(texto):
    par = fmt(doc.add_paragraph(), primeira=0, antes=10, depois=4, alinhar=WD_ALIGN_PARAGRAPH.LEFT, linha=15)
    runs(par, f"**{texto}**", tam=12)
    par.paragraph_format.keep_with_next = True


def H2(texto):
    par = fmt(doc.add_paragraph(), primeira=0, antes=6, depois=2, alinhar=WD_ALIGN_PARAGRAPH.LEFT)
    runs(par, f"*{texto}*", tam=10)
    par.paragraph_format.keep_with_next = True


def QP(k, texto):
    P(f"**QP {k}.** {texto}")


def secao(paisagem):
    """Nova seção em página nova, em retrato ou paisagem; o cabeçalho continua."""
    from docx.enum.section import WD_ORIENT
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE if paisagem else WD_ORIENT.PORTRAIT
    sec.page_width, sec.page_height = (Cm(29.7), Cm(21.0)) if paisagem else (Cm(21.0), Cm(29.7))
    if ORI:
        sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3.0), Cm(2.0), Cm(3.0), Cm(2.0)
    else:
        sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.8), Cm(2.0), Cm(1.8)
    sec.header_distance = Cm(1.0)
    return sec


def figura(arq, legenda, larg=13.6, recuo=True, maxw=15.8):
    par = doc.add_paragraph()
    fmt(par, recuo=recuo, primeira=0, antes=6, depois=2, alinhar=WD_ALIGN_PARAGRAPH.CENTER, linha=12)
    par.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    par.paragraph_format.keep_with_next = True
    par.add_run().add_picture(str(FIG / arq), width=Cm(min(larg * 1.08, maxw) if ORI else larg))
    leg = fmt(doc.add_paragraph(), primeira=0, antes=2, depois=8, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, linha=10.8)
    runs(leg, legenda, tam=9)


def bordas(cel, top=None, bottom=None):
    tcPr = cel._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for lado, v in (("top", top), ("bottom", bottom)):
        e = OxmlElement(f"w:{lado}")
        if v:
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(v))
            e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")
        b.append(e)
    for lado in ("left", "right"):
        e = OxmlElement(f"w:{lado}")
        e.set(qn("w:val"), "nil")
        b.append(e)
    tcPr.append(b)


def tabela(legenda, cab, linhas, larguras, recuo=False, alinhar=None, grupos=None, tam=9, larg_max=15.9):
    if ORI:
        larguras = [w * min(1.0, larg_max / sum(larguras)) for w in larguras]
        tam = tam * 0.92
    """Tabela no padrão MDPI: legenda acima, regras só no topo, sob o cabeçalho e no fim; cabeçalho em negrito
    repetido nas páginas seguintes. 'grupos' = {índice da linha: título} para linhas-separadoras em negrito."""
    leg = fmt(doc.add_paragraph(), recuo=recuo or True, primeira=0, antes=8, depois=4, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY,
              linha=10.8)
    runs(leg, legenda, tam=9)
    leg.paragraph_format.keep_with_next = True
    grupos = grupos or {}
    total = len(linhas) + len(grupos) + 1
    t = doc.add_table(rows=total, cols=len(cab))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    alinhar = alinhar or ["c"] * len(cab)
    lin = 0
    for j, h in enumerate(cab):
        c = t.cell(0, j)
        c.width = Cm(larguras[j])
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(tam * ESC_T + 1.5)
        runs(p, f"**{h}**", tam=tam)
        bordas(c, top=8, bottom=6)
    tr = t.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    e = OxmlElement("w:tblHeader")
    e.set(qn("w:val"), "true")
    trPr.append(e)
    lin = 1
    for i, row in enumerate(linhas):
        if i in grupos:
            cel = t.cell(lin, 0).merge(t.cell(lin, len(cab) - 1))
            p = cel.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            p.paragraph_format.line_spacing = Pt(tam * ESC_T + 1.5)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            runs(p, f"**{grupos[i]}**", tam=tam)
            for j in range(len(cab)):
                bordas(t.cell(lin, j), top=4, bottom=4)
            lin += 1
        ultima = i == len(linhas) - 1
        for j, v in enumerate(row):
            c = t.cell(lin, j)
            c.width = Cm(larguras[j])
            p = c.paragraphs[0]
            p.alignment = {"c": WD_ALIGN_PARAGRAPH.CENTER, "l": WD_ALIGN_PARAGRAPH.LEFT,
                           "j": WD_ALIGN_PARAGRAPH.LEFT}[alinhar[j]]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            for k, pedaco in enumerate(str(v).split("\n")):
                if k:
                    p = c.add_paragraph()
                    p.alignment = {"c": WD_ALIGN_PARAGRAPH.CENTER, "l": WD_ALIGN_PARAGRAPH.LEFT,
                                   "j": WD_ALIGN_PARAGRAPH.LEFT}[alinhar[j]]
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                p.paragraph_format.line_spacing = Pt(tam * ESC_T + 1.5)
                if k:
                    p.paragraph_format.space_before = Pt(0)
                if k < len(str(v).split("\n")) - 1:
                    p.paragraph_format.space_after = Pt(0)
                runs(p, pedaco, tam=tam)
            bordas(c, top=4 if i else None, bottom=8 if ultima else 4)
        lin += 1
    # largura fixa: tblW, layout fixo e grade (o LibreOffice ignora a largura só das células)
    tblPr = t._tbl.tblPr
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(larguras) * 567)))
    tw.set(qn("w:type"), "dxa")
    for e in tblPr.findall(qn("w:tblW")):
        tblPr.remove(e)
    tblPr.append(tw)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    grid = t._tbl.tblGrid
    for k, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(larguras[k] * 567)))
    for row in t.rows:
        for k, cel in enumerate(row.cells[:len(larguras)]):
            tcPr = cel._tc.get_or_add_tcPr()
            for e in tcPr.findall(qn("w:tcW")):
                tcPr.remove(e)
            w_ = OxmlElement("w:tcW")
            w_.set(qn("w:w"), str(int(larguras[k] * 567)))
            w_.set(qn("w:type"), "dxa")
            tcPr.insert(0, w_)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


# ================================================================== cabeçalho e rodapé
sec = doc.sections[0]
hp = sec.header.paragraphs[0]
hp.text = ""
r = hp.add_run("Versão para leitura do orientador: variáveis psicológicas no handebol" if ORI else "Revisão sistemática: estados de humor no handebol")
r.italic, r.font.size, r.font.name = True, Pt(8.5), FONTE
hp.add_run("\t\t")
fld = OxmlElement("w:fldSimple")
fld.set(qn("w:instr"), "PAGE")
hp._p.append(fld)
pPr = hp._p.get_or_add_pPr()
bd = OxmlElement("w:pBdr")
e = OxmlElement("w:bottom")
e.set(qn("w:val"), "single")
e.set(qn("w:sz"), "4")
bd.append(e)
pPr.append(bd)



# ================================================================== adaptadores (assinatura da versão ABNT, aparência MDPI)
_fig_mdpi, _tab_mdpi = figura, tabela
ROT = {"Quadro 1": "Tabela 3", "Quadro A1": "Tabela A1", "Quadro C1": "Tabela B1", "Quadro D1": "Tabela C1"}


def figura(arq, rotulo, titulo, larg=13.6, nota=None):
    leg = f"**{rotulo}.** {titulo}."
    if nota:
        leg += " " + nota[0].upper() + nota[1:]
    _fig_mdpi(arq, leg, larg=min(larg, 25.5), recuo=larg <= 13.6, maxw=25.5)


def tabela(rotulo, titulo, cab, linhas, larguras, alinhar=None, grupos=None, tam=9, nota=None, quadro=False,
           larg_max=15.9):
    rotulo = ROT.get(rotulo, rotulo)
    t = _tab_mdpi(f"**{rotulo}.** {titulo}.", cab, linhas, larguras, alinhar=alinhar, grupos=grupos, tam=min(tam, 9))
    if nota:
        par = fmt(doc.add_paragraph(), primeira=0, antes=0, depois=8, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, linha=10)
        runs(par, nota[0].upper() + nota[1:], tam=8)
    return t


def tabela2(rotulo, titulo, grupos_cab, cab2, linhas, larguras, tam=9, nota=None, negrito_ult=True):
    """Tabela MDPI com cabeçalho em dois níveis (células mescladas), como a Tabela 3 do artigo modelo.
    grupos_cab: [(rótulo, número de colunas)] cobrindo todas as colunas; rótulo vazio = célula mesclada vertical."""
    leg = fmt(doc.add_paragraph(), primeira=0, antes=8, depois=4, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, linha=10.8)
    runs(leg, f"**{rotulo}.** {titulo}.", tam=9)
    leg.paragraph_format.keep_with_next = True
    nc = len(cab2)
    t = doc.add_table(rows=len(linhas) + 2, cols=nc)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    lead = Pt(tam + 1.5)

    def escreve(c, txt, b=False, al=WD_ALIGN_PARAGRAPH.CENTER):
        p = c.paragraphs[0]
        p.alignment = al
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = lead
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        runs(p, f"**{txt}**" if b and txt else txt, tam=tam)

    j = 0
    for rot, span in grupos_cab:
        if rot == "":
            cel = t.cell(0, j).merge(t.cell(1, j))
            escreve(cel, cab2[j], True)
            bordas(t.cell(0, j), top=8)
            bordas(t.cell(1, j), bottom=6)
        else:
            cel = t.cell(0, j).merge(t.cell(0, j + span - 1)) if span > 1 else t.cell(0, j)
            escreve(cel, rot, True)
            for k in range(j, j + span):
                bordas(t.cell(0, k), top=8, bottom=4)
                escreve(t.cell(1, k), cab2[k], True)
                bordas(t.cell(1, k), bottom=6)
        j += span
    for r in (0, 1):
        trPr = t.rows[r]._tr.get_or_add_trPr()
        e = OxmlElement("w:tblHeader")
        e.set(qn("w:val"), "true")
        trPr.append(e)
    for i, row in enumerate(linhas):
        ult = i == len(linhas) - 1
        for k, v in enumerate(row):
            c = t.cell(i + 2, k)
            escreve(c, str(v), b=ult and negrito_ult, al=WD_ALIGN_PARAGRAPH.LEFT if k == 0 else WD_ALIGN_PARAGRAPH.CENTER)
            bordas(c, top=4 if (ult and negrito_ult) else None, bottom=8 if ult else None)
    tblPr = t._tbl.tblPr
    for e in tblPr.findall(qn("w:tblW")):
        tblPr.remove(e)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), str(int(sum(larguras) * 567)))
    tw.set(qn("w:type"), "dxa")
    tblPr.append(tw)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for k, gc in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(larguras[k] * 567)))
    for row in t.rows:
        for k, cel in enumerate(row.cells[:len(larguras)]):
            tcPr = cel._tc.get_or_add_tcPr()
            for e in tcPr.findall(qn("w:tcW")):
                tcPr.remove(e)
            w_ = OxmlElement("w:tcW")
            w_.set(qn("w:w"), str(int(larguras[k] * 567)))
            w_.set(qn("w:type"), "dxa")
            tcPr.insert(0, w_)
    if nota:
        par = fmt(doc.add_paragraph(), primeira=0, antes=2, depois=8, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, linha=10)
        runs(par, nota, tam=8)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def BUL(texto, marca="-"):
    """Item com marcador e recuo deslocado, como as QP do artigo modelo."""
    par = fmt(doc.add_paragraph(), primeira=-0.45, antes=0, depois=1)
    par.paragraph_format.left_indent = RECUO + Cm(0.45)
    runs(par, marca + "\t" + texto)
    return par



# ================================================================== dados da revisão
INC = RD.INC
EST = [e for e in INC if e["id"] not in RD.MESMA_AMOSTRA]
NE, NR = len(EST), len(INC)
K = RD.CHAVE
NORM, REL = RD.NORM, RD.REL
cnt = lambda j: Counter(NORM[e["id"]][j] for e in EST)
PAIS, NIV, DEL, CTX, FAM = cnt(1), cnt(2), cnt(3), cnt(4), cnt(5)
SEXO = Counter(e["sexo"] for e in EST)
NS = [e["n"] for e in EST if isinstance(e["n"], int)]
import statistics as st_
MED, SOMA, N30 = st_.median(NS), sum(NS), sum(1 for x in NS if x < 30)
DIRC = Counter(RD.DIR_CURTA[e["direcao"]] for e in EST)
QUAL = Counter(RD.qualidade(e) for e in EST)
QI = {q: Counter(e["qualidade"][q] for e in EST) for q in ["q1", "q2", "q3", "q4", "q5", "q6"]}
FT = sum(1 for e in INC if e["fonte"] == "texto completo")
GR = Counter(v for e in EST for v in REL[e["id"]])
c = lambda *ids: R.cite(*[K[i] for i in ids])
a = lambda i: R.autor(K[i])


def ext(n):
    return {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove",
            10: "dez", 11: "onze", 12: "doze", 13: "treze", 14: "catorze", 15: "quinze", 16: "dezesseis",
            17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte"}.get(n, str(n))



# ================================================================== página de rosto (estrutura do artigo modelo)
P("*Revisão*", recuo=False, primeira=0, antes=18, tam=10, alinhar=WD_ALIGN_PARAGRAPH.LEFT)
par = fmt(doc.add_paragraph(), recuo=False, primeira=0, antes=4, depois=10, alinhar=WD_ALIGN_PARAGRAPH.LEFT, linha=22)
runs(par, "**Estados de Humor em Atletas de Handebol no Treinamento e na Competição: Revisão Sistemática das "
          "Evidências e da Qualidade Metodológica dos Estudos**", tam=17)
_au = fmt(doc.add_paragraph(), recuo=False, primeira=0, depois=10, alinhar=WD_ALIGN_PARAGRAPH.LEFT)
_r = _au.add_run("[Autor 1] ¹,*, [Autor 2] ¹, [Autor 3] ¹ e [Autor 4] ¹")
_r.bold, _r.font.size, _r.font.name = True, Pt(11), FONTE
P("¹  Laboratório de Psicologia do Esporte e do Exercício (Lape), Centro de Ciências da Saúde e do Esporte, "
  "Universidade do Estado de Santa Catarina (UDESC), Florianópolis 88080-350, SC, Brasil", primeira=0, tam=8.5,
  alinhar=WD_ALIGN_PARAGRAPH.LEFT, linha=10.8)
P("*  Correspondência: [e-mail]", primeira=0, tam=8.5, alinhar=WD_ALIGN_PARAGRAPH.LEFT, depois=12, linha=10.8)
P(f"**Resumo:** Esta revisão investiga e analisa o estado da arte das evidências científicas sobre os estados de humor "
  f"em atletas de handebol no treinamento e na competição e avalia a qualidade metodológica dos estudos, por meio de uma "
  f"revisão sistemática. A revisão seguiu as recomendações para revisões sistemáticas, foi relatada conforme o PRISMA 2020 e teve a "
  f"pergunta estruturada pelo acrônimo PCC (população, conceito e contexto). A busca foi realizada nas bases Crossref, "
  f"Europe PMC, LILACS, OpenAlex, PubMed, SciELO, Scopus e Web of Science, sem restrição de data, entre maio e setembro "
  f"de 2026, e foi atualizada em outubro de 2026 em cinco fontes, com busca de citações. Três filtros foram aplicados: "
  f"busca, seleção com critérios de inclusão e de exclusão e extração dos dados, seguida da leitura integral de todos os "
  f"relatórios. A qualidade metodológica foi avaliada por seis itens, e a certeza da evidência, pelos domínios da "
  f"abordagem GRADE. {NE} estudos ({NR} relatórios) que atenderam aos critérios de elegibilidade foram incluídos, e cinco "
  f"questões de pesquisa foram respondidas. Os estudos foram publicados entre 2008 e 2026 e totalizaram {mil(SOMA)} "
  f"participantes, com mediana de {br(MED, 0)} por estudo. A distribuição geográfica concentrou-se na Espanha "
  f"({PAIS['Espanha']} estudos), na Tunísia ({PAIS['Tunísia']}) e no Brasil ({PAIS['Brasil']}), e houve predomínio de "
  f"amostras femininas e de delineamentos transversais. O Profile of Mood States foi utilizado em "
  f"{FAM['POMS e versões']} estudos, em versões de 30 a 65 itens e com momento da medida declarado em apenas "
  f"{QI['q4']['sim']}. Efeito ou associação foi relatado em {DIRC['Efeito ou associação']} estudos e resultados mistos "
  f"em {DIRC['Misto']}. Doze estudos testaram intervenções, e o encorajamento verbal e o feedback modificaram o humor "
  f"durante a prática, com certeza baixa em escolares e muito baixa em atletas. A qualidade foi alta em {QUAL['Alta']} "
  f"estudos, moderada em {QUAL['Moderada']} e baixa em {QUAL['Baixa']}, e a análise estatística foi adequada em apenas "
  f"{QI['q6']['sim']}. Conclui-se que o humor de atletas de handebol responde à carga, ao contexto competitivo e à "
  f"interação com treinador e colegas, mas a evidência é escassa, heterogênea e raramente experimental. Com base nas "
  f"evidências sintetizadas, técnicos, psicólogos do esporte e pesquisadores podem utilizar essas informações para "
  f"aprimorar o monitoramento do humor e planejar estudos experimentais no treinamento e na competição.",
  primeira=0, tam=9.5, antes=4, linha=11.5)
P("**Palavras-chave:** handebol; estados de humor; afeto; psicologia do esporte; revisão sistemática",
  primeira=0, tam=9.5, antes=6, depois=14, linha=11.5)
regra = doc.add_paragraph()
fmt(regra, primeira=0, depois=6)
_pPr = regra._p.get_or_add_pPr()
_bd = OxmlElement("w:pBdr")
_e = OxmlElement("w:bottom")
_e.set(qn("w:val"), "single")
_e.set(qn("w:sz"), "6")
_bd.append(_e)
_pPr.append(_bd)

H1("1. Introdução")
P(f"As variáveis psicológicas associam-se ao desempenho e à saúde do atleta e constituem objeto consolidado das ciências "
  f"do esporte {R.cite('reardon2019', 'henriksen2020')}. A prevalência de sintomas de transtornos mentais em atletas de "
  f"elite é comparável à da população geral {R.cite('gouttebarge2019', 'rice2016')}, com diferenças entre homens e "
  f"mulheres {R.cite('kew2025sex')}, e o consenso de 2026 do Comitê Olímpico Internacional recomendou o monitoramento "
  f"rotineiro da saúde mental com instrumentos validados {R.cite('reardon2026ioc', 'gouttebarge2026')}. Entre os "
  f"indicadores disponíveis para esse monitoramento, o estado de humor ocupa posição central, pois se situa entre a "
  f"resposta transitória à carga e o sinal precoce de sofrimento psicológico.")
P(f"O estado de humor designa uma disposição afetiva difusa, de intensidade moderada e duração variável, que persiste "
  f"além do evento desencadeador e influencia a avaliação dos acontecimentos subsequentes "
  f"{R.cite('lazarus2000', 'beedie2005')}. Diferentemente da emoção, que responde a um objeto identificável e se "
  f"extingue com ele, o humor é medido em dimensões separadas, como tensão, depressão, raiva, vigor, fadiga e confusão "
  f"{R.cite('lane2000', 'meyers2024')}. O modelo conceitual de {R.autor('lane2000')} situou a depressão no centro dessa "
  f"estrutura e deslocou a interpretação do escore isolado para a configuração do perfil, e a análise de agrupamentos "
  f"identificou seis perfis de humor, do iceberg ao submerso, cuja prevalência variou com o sexo, a idade e a condição "
  f"de atleta {R.cite('terry2021clusters', 'luojumaki2026clusters')}. Essa natureza multidimensional explica por que a "
  f"forma de medir o humor condiciona a interpretação dos resultados.")
P(f"A medida do humor no esporte originou-se, de fato, de um problema aplicado: a perturbação do perfil acompanhou o "
  f"aumento programado da carga de treinamento e regrediu com a recuperação {R.cite('morgan1987', 'raglin2001')}. "
  f"Seguiram-se a versão abreviada denominada Brunel Mood Scale {R.cite('terry2003')}, sua adaptação brasileira "
  f"{R.cite('rohlfs2008')}, normas que distinguem o sexo e a condição de atleta {R.cite('terry2021')} e validações "
  f"transculturais recentes {R.cite('terry2022ltu', 'vlachopoulos2023brums')}, embora a versão abreviada do POMS não "
  f"tenha mantido sua estrutura original em atletas chineses {R.cite('tan2024poms')}. As medidas autorrelatadas de humor "
  f"e de recuperação mostraram-se mais sensíveis à carga que muitos marcadores objetivos "
  f"{R.cite('saw2015', 'kellmann2018')}, e os métodos de amostragem de experiência ampliaram a resolução temporal desse "
  f"monitoramento {R.cite('majer2026esm')}. As escalas de afeto positivo e negativo {R.cite('watson1988')} e de valência "
  f"afetiva durante o esforço {R.cite('hardy1989', 'ekkekakis2019')} medem, contudo, construtos próprios, e tratá-las "
  f"como equivalentes ao perfil de humor compromete a síntese.")
P(f"Se a medida se consolidou, a relação entre humor e desempenho permanece em debate. Metanálises associaram vigor "
  f"elevado e baixos escores de tensão, depressão, raiva, fadiga e confusão a melhor desempenho, com efeitos pequenos a "
  f"moderados, dependentes do tipo de esporte e do momento da medida {R.cite('beedie2000', 'lochbaum2021', 'lochbaum2022')}. "
  f"Os perfis de humor revelaram padrões de risco em atletas de elite e de formação "
  f"{R.cite('parsonssmith2017', 'rohlfs2024')}, e o POMS foi examinado como preditor do desempenho em treinamento e em "
  f"competição de atletas profissionais {R.cite('avelino2023')}. O humor como sinal de sobrecarga carece, porém, de "
  f"confirmação, pois nenhum estudo documentou a transição até a síndrome de overtraining com queda prolongada do "
  f"desempenho {R.cite('weakley2022ots')}, e as alterações psicológicas no overreaching não funcional apoiam-se em "
  f"evidência limitada {R.cite('valdesalici2026nfor')}. Nos esportes coletivos, o humor individual tampouco se forma "
  f"isoladamente, pois as emoções coletivas da equipe após o jogo associaram-se às emoções de cada jogador "
  f"{R.cite('rumbold2022emocoes')}, e as emoções interpessoais constituem objeto próprio de estudo nessas modalidades "
  f"{R.cite('eldadi2023contagio')}.")
P(f"No handebol, essas questões assumem forma específica. A modalidade é intermitente, de alta intensidade e de contato "
  f"constante {R.cite('povoas2012', 'michalsik2012', 'karcher2014')}, com ações de alta intensidade repetidas ao longo das "
  f"partidas internacionais {R.cite('luteberget2017')} e demandas que variam conforme a posição e o sistema defensivo "
  f"{R.cite('wagner2025', 'saal2026')}. O regulamento impõe situações de pressão contínua, como o ataque com goleiro "
  f"substituído {R.cite('gumus2020', 'macedo2024')}, a inferioridade numérica nas exclusões {R.cite('trejo2025')} e o "
  f"tempo técnico em jogos equilibrados {R.cite('jetzke2022')}, e o jogador decide em frações de segundo sob oposição "
  f"direta do adversário {R.cite('raab2007', 'hinz2022')}. O clima criado pelo treinador e as interações do grupo modulam "
  f"as emoções dos atletas {R.cite('robazza2022', 'tamminen2019')}, e, em handebolistas jovens, o clima orientado à "
  f"tarefa associou-se a menos sintomas de ansiedade, depressão e estresse {R.cite('e187')}.")
P(f"Essas exigências, por sua vez, acumulam-se ao longo da temporada. As semanas com dois ou mais jogos ampliaram a "
  f"variação interindividual da carga acumulada {R.cite('buchel2026congestao')}, a incidência de lesões aumentou ao longo "
  f"de seis dias consecutivos do maior torneio juvenil da modalidade {R.cite('lindman2026juvenil')}, e quatro jogos de um "
  f"torneio elevaram o cortisol e reduziram o fator de crescimento semelhante à insulina tipo 1 de jogadoras "
  f"universitárias {R.cite('pancar2026torneio')}. Como o humor acompanha a carga e a recuperação "
  f"{R.cite('morgan1987', 'saw2015')}, é plausível que o estado afetivo do jogador oscile em intervalos curtos, o que "
  f"torna o humor um indicador potencialmente útil para técnicos e psicólogos do esporte da modalidade.")
P(f"Apesar dessa relevância, a evidência permanece dispersa. A revisão de mapeamento conduzida em paralelo por esta "
  f"equipe identificou o humor e o afeto entre os domínios psicológicos investigados no handebol, sem avaliar a "
  f"qualidade dos estudos. Há revisões sobre o humor no judô {R.cite('lakicevic2024')} e no futebol "
  f"{R.cite('selmi2023poms')}, mas as revisões em outras modalidades coletivas diluíram o humor em escores compostos de "
  f"bem-estar {R.cite('rebelo2024voleibol')} ou não lhe dedicaram eixo próprio {R.cite('veillette2025hoquei')}, e o "
  f"protocolo de revisão sobre o monitoramento de atletas de handebol antecipou poucos estudos elegíveis e dados "
  f"heterogêneos {R.cite('henze2025athmon')}. Até o momento, não foram identificadas revisões abrangentes na literatura "
  f"que reúnam as evidências sobre os estados de humor em atletas de handebol. Também não foram encontradas revisões que "
  f"formulem questões específicas sobre o tema e avaliem a qualidade metodológica dos estudos, como forma de elucidar o "
  f"estado da arte sobre o que foi estudado e quais lacunas permanecem, o que pode ser respondido por uma revisão "
  f"sistemática {R.cite('munn2018sr')}. Assim, o objetivo do presente estudo foi investigar e analisar o estado da arte "
  f"das evidências científicas sobre os estados de humor em atletas de handebol no treinamento e na competição, e "
  f"avaliar a qualidade metodológica dos estudos, por meio de uma revisão sistemática.")

H1("2. Métodos")
H2("2.1. Diretrizes")
P(f"A revisão sistemática foi realizada para analisar o estado da arte das evidências científicas sobre os estados "
  f"de humor em atletas de handebol no treinamento e na competição. Três filtros, para reunir (procedimento de "
  f"busca), selecionar (critérios de inclusão e de exclusão) e extrair (extração dos dados) as informações "
  f"relevantes da literatura, foram aplicados nesta revisão {R.cite('mcdaniel2017')}.")
P(f"A revisão sistemática seguiu o guia de {R.autor('galvao2019')} e foi relatada conforme o PRISMA 2020 "
  f"{R.cite('page2021')}, com o fluxo de seleção do modelo para revisões atualizadas, que distingue os estudos da versão "
  f"anterior dos identificados na nova busca. A pergunta foi estruturada pelo acrônimo PCC, recomendado para perguntas "
  f"de medida e de caracterização, sem intervenção atribuída nem comparação obrigatória "
  f"{R.cite('peters2020', 'munn2018tip')}, e a opção pela revisão sistemática seguiu o critério de "
  f"{R.autor('munn2018sr')}: a pergunta trata de um construto específico, medido em um conjunto delimitado de estudos, "
  f"com avaliação da qualidade metodológica. A busca compartilhou a infraestrutura da revisão de mapeamento conduzida "
  f"em paralelo pelo grupo, mas não seus critérios de elegibilidade. O protocolo foi redigido antes da busca, e seu "
  f"registro prospectivo no PROSPERO não foi concluído.")
H2("2.2. Estratégia de Busca")
P("A busca foi realizada nas bases Crossref, Europe PMC, LILACS, OpenAlex, PubMed, SciELO, Scopus e Web of Science "
  "(Coleção Principal), sem restrição de data, entre maio e setembro de 2026, com os descritores da Tabela 1, "
  "combinados em cinco estratégias e 45 consultas, e foi repetida na LILACS e na SciELO em português e em espanhol. As "
  "listas de referências dos estudos incluídos também foram examinadas. Os registros foram deduplicados pelo DOI, pelo "
  "identificador PubMed e pelo título normalizado.")
P("A busca foi atualizada em outubro de 2026, sem restrição de data, no PubMed, no Europe PMC, no Crossref, no "
  "Semantic Scholar e no Dialnet, com filtro automático que reteve os registros em que o termo handebol aparecia "
  "associado a termo de humor, de afeto ou psicológico. A busca de citações percorreu as referências e as citações dos "
  "estudos incluídos no OpenCitations e, em segunda rodada, no Crossref, no Europe PMC e no Semantic Scholar, com "
  "consultas complementares no DOAJ, no CORE, no Redalyc, na SciELO e no Consensus. A Scopus, a Web of Science e a "
  "LILACS não foram consultadas na atualização, por exigirem acesso institucional ou bloquearem o acesso automatizado.")
tabela("Tabela 1", "Estratégia de busca adotada na revisão sistemática",
       ["", "Termos de busca", "Descritores"],
       [["1", "Handebol", "“handball” OR “team handball” OR “beach handball” OR “wheelchair handball” OR “handebol” OR "
                          "“balonmano”"],
        ["2", "Humor e afeto", "“mood” OR “mood state*” OR “affect*” OR “affective response*” OR “positive affect” OR "
                               "“negative affect” OR “feeling” OR “humor” OR “estado de ánimo” OR “estados de humor”"],
        ["3", "Instrumentos", "“Profile of Mood States” OR “POMS” OR “Brunel Mood Scale” OR “BRUMS” OR “PANAS” OR "
                              "“Feeling Scale” OR “Self-Assessment Manikin”"],
        ["4", "Dimensões do humor", "“vigor” OR “tension” OR “anger” OR “depression” OR “confusion” OR “fatigue” OR "
                                    "“total mood disturbance”"],
        ["", "Combinação", "#1 AND (#2 OR #3 OR #4)"]],
       [0.8, 3.4, 11.8], alinhar=["c", "l", "l"], tam=10,
       nota="cada termo dos blocos 2 a 4 foi combinado com o bloco 1 em estratégias separadas, e uma quinta estratégia "
            "acrescentou o termo “review” à combinação #1 AND #2; as strings completas, base a base, constam do "
            "material suplementar.")
H2("2.3. Critérios de Elegibilidade")
P(f"Os critérios basearam-se no acrônimo PCC {R.cite('peters2020')} e estão descritos na Tabela 2. Foram aceitos "
  f"artigos completos publicados em periódicos, em inglês, português ou espanhol, de qualquer delineamento, com atletas "
  f"ou praticantes de handebol, que medissem o humor, o afeto ou o ânimo por instrumento declarado. A decisão de maior "
  f"consequência foi a definição explícita do que conta como medida de humor, pois a fronteira entre humor e carga é "
  f"tênue na literatura esportiva {R.cite('kellmann2018', 'saw2015')}. O critério de tipo de documento, explicitado na "
  f"revisão final, levou à exclusão de três relatórios antes incluídos: um preprint, um trabalho completo em anais e um "
  f"resumo de congresso.")
tabela("Tabela 2", "Critérios de inclusão e de exclusão segundo o acrônimo PCC",
       ["", "Critérios de inclusão", "Critérios de exclusão"],
       [["P", "Atletas ou praticantes de handebol de quadra, de praia ou em cadeira de rodas, de qualquer sexo, idade e "
              "nível competitivo",
         "Amostras sem handebol ou multiesporte sem separação dos dados; árbitros, treinadores ou torcedores"],
        ["C", "Humor, afeto ou ânimo medido por instrumento declarado (POMS e versões, BRUMS, PANAS, Feeling Scale, "
              "subescala afetiva do SAM ou dimensões isoladas do perfil de humor)",
         "Índice de Hooper ou escalas de bem-estar sem dimensão afetiva; esforço percebido; fadiga mental por tarefa; "
         "ansiedade ou depressão clínica medidas isoladamente"],
        ["C", "Treinamento, competição ou condição experimental, em qualquer país ou período da temporada",
         "Contexto exclusivamente clínico ou de reabilitação"],
        ["S", "Artigos completos publicados em periódicos, com dados primários, de qualquer delineamento, em inglês, "
              "português ou espanhol",
         "Teses, dissertações, trabalhos de conclusão de curso, livros e capítulos; trabalhos e resumos em anais; "
         "preprints; editoriais, protocolos, resenhas e revisões; outros idiomas"]],
       [0.8, 7.2, 8.0], alinhar=["c", "l", "l"], tam=10,
       nota="P: população; C: conceito; C: contexto; S: tipo de estudo (*study design*); POMS: Profile of Mood States; "
            "BRUMS: Brunel Mood Scale; PANAS: Positive and Negative Affect Schedule; SAM: Self-Assessment Manikin.")
H2("2.4. Extração e Análise dos Dados")
P(f"A triagem de títulos e resumos foi realizada em duas passagens independentes, assistidas por modelo de linguagem "
  f"submetido aos critérios do protocolo, com as categorias incluir, excluir e dúvida; os registros em dúvida seguiram "
  f"para o texto completo, e as divergências foram resolvidas por uma terceira avaliação {R.cite('ouzzani2016')} "
  f"(concordância de 0,988; κ = 0,959) {R.cite('cohen1960', 'landis1977')}. Esse coeficiente expressa a consistência "
  f"do procedimento, e não a concordância entre avaliadores humanos {R.cite('mchugh2012')}. Foram extraídos autoria, "
  f"ano, país, tamanho, sexo, idade e nível da amostra, delineamento, contexto e momento da medida, instrumento e "
  f"dimensões do humor, variáveis relacionadas, intervenção, resultados e direção do achado, e cada resultado foi "
  f"vinculado a um trecho literal da fonte (Apêndice A). Em segunda etapa, todos os relatórios foram relidos na íntegra "
  f"com ficha padronizada, que conferiu os números com o texto e as tabelas da fonte e registrou as limitações "
  f"declaradas pelos autores e as fragilidades observadas pelos revisores (Apêndice C). Quando o estudo relatava médias "
  f"e desvios-padrão de duas condições sem tamanho de efeito, os revisores calcularam o d de Cohen, sinalizado como "
  f"tal.")
P(f"A qualidade metodológica foi avaliada por seis itens adaptados de instrumentos para estudos observacionais e "
  f"transversais {R.cite('downes2016')}: (Q1) objetivo e população definidos; (Q2) amostra descrita; (Q3) instrumento "
  f"de humor validado e nomeado; (Q4) momento da medida declarado; (Q5) comparador, controle ou ajuste para "
  f"confundimento; e (Q6) análise estatística adequada, com medidas de variabilidade. A pontuação correspondeu ao "
  f"número de itens atendidos (0 a 6), com qualidade alta de 5 a 6, moderada de 3 a 4 e baixa de 0 a 2, e foi revista "
  f"na leitura integral. A certeza da evidência de cada achado principal foi julgada pelos domínios da abordagem GRADE "
  f"{R.cite('guyatt2008')} (consistência, precisão, validade interna e direcionalidade), sem atribuição de níveis "
  f"formais.")
P(f"A síntese foi narrativa e estruturada conforme a diretriz SWiM {R.cite('campbell2020')}, com agrupamento por "
  f"instrumento, variável relacionada e delineamento e com a direção do achado como métrica padronizada. A metanálise "
  f"não foi realizada, por decisão anterior à inspeção dos dados, pois os estudos diferem em instrumento, momento da "
  f"medida, delineamento e desfecho {R.cite('hopkins2009')}. A trajetória temporal da produção foi descrita por média "
  f"móvel centrada de três anos, com intervalo de confiança exato de Poisson {R.cite('garwood1936')}, procedimento que "
  f"reduz a variação aleatória e preserva a tendência {R.cite('cleveland1979', 'hyndman2011')}.")
P(f"Com base em {R.autor('fernandez2019')}, um aspecto metodológico fundamental para o êxito de uma revisão é a "
  f"definição das questões de pesquisa (QP) a serem respondidas. Para esta revisão sistemática, foram definidas cinco QP:")
QPS = {1: "Quais são as características dos estudos que investigaram o humor no handebol e de suas populações?",
       2: "Com quais instrumentos, em quais dimensões e em que momentos o humor foi medido?",
       3: "A que variáveis o humor foi relacionado (carga, recuperação, desempenho, marcadores biológicos, variáveis "
          "psicológicas, lesão e ciclo menstrual) e com que resultados?",
       4: "Quais intervenções foram testadas sobre o humor e com que efeitos?",
       5: "Qual é a qualidade metodológica dos estudos e quais lacunas persistem?"}
for k_, v_ in QPS.items():
    BUL(f"**QP{k_}.** {v_}", marca="-")


# ================================================================== 3 Resultados
H1("3. Resultados")
QE = {e["id"]: e for e in INC}
FTL = sum(1 for e in INC if (e.get("leitura") or {}).get("fonte") == "texto completo")
P(f"A busca na literatura identificou {mil(1423 + 4326)} registros relevantes, 1.423 na versão inicial e 4.326 na "
  f"atualização. Após a remoção das duplicatas e a triagem, os relatórios completos foram avaliados quanto à "
  f"elegibilidade, e {NE} estudos, descritos em {NR} relatórios, foram selecionados para a síntese (Figura 1).")
P(f"Na versão inicial, a busca identificou 1.423 registros, 1.421 nas bases e 2 nas listas de referências. Após a "
  f"remoção de 734 duplicatas, 689 registros seguiram para a triagem, que excluiu 576; dos 113 relatórios procurados, 54 "
  f"não foram recuperados, e os 59 avaliados na íntegra resultaram em 26 estudos, aos quais a revisão de mapeamento "
  f"paralela acrescentou um relatório. Na atualização, as cinco fontes retornaram 4.326 registros; após a remoção de 894 "
  f"duplicatas e de 2.708 registros pelo filtro automático, 724 foram triados, 22 relatórios foram avaliados na íntegra "
  f"e 7 foram incluídos, e a busca de citações acrescentou um estudo {c('N4')}. A segunda rodada de citações e as "
  f"consultas complementares não identificaram outros artigos elegíveis. O conjunto final reúne {NR} relatórios de {NE} "
  f"estudos, pois dois relatórios descrevem a mesma amostra {c('H31', 'H32')}. A releitura integral dos "
  f"relatórios da versão anterior alterou onze decisões, e os relatórios excluídos no texto completo constam do "
  f"Apêndice B.")
figura("Figura1_PRISMA_RS.png", "Figura 1", "Fluxograma PRISMA 2020 da seleção dos estudos", larg=11.5,
       nota="busca inicial entre maio e setembro de 2026 e atualização em outubro de 2026; modelo do PRISMA 2020 para revisões atualizadas.")
P("A seguir, as cinco questões de pesquisa são respondidas com base na síntese das análises.")
P(f"**QP1.** {QPS[1]}")
P(f"O estudo mais antigo foi publicado por {a('H2')}, com data provável de 2008, e o mais recente, em 2026 "
  f"{c('H34')}. Os {NE} estudos totalizaram {mil(SOMA)} participantes, com média de quase dois estudos por ano e maior concentração a partir de 2018 (Figura 2A). A produção distribuiu-se por {len([p for p in PAIS if p != 'Não relatado'])} países, com predomínio da Espanha ({PAIS['Espanha']} estudos), da Tunísia ({PAIS['Tunísia']}) e do Brasil ({PAIS['Brasil']}). {ext(SEXO['feminino']).capitalize()} estudos ({pc(SEXO['feminino'])}) investigaram apenas mulheres, {ext(SEXO['masculino'])} ({pc(SEXO['masculino'])}) apenas "
  f"homens e {ext(SEXO['misto'])} amostras mistas, enquanto {ext(SEXO['n.r.'])} não relataram o sexo. O nível de elite reuniu {NIV['Elite']} estudos, o de formação, {NIV['Formação']}, e o nacional, {NIV['Nacional']}; os demais envolveram atletas universitários, amadores e escolares. O tamanho da amostra, "
  f"relatado em {len(NS)} estudos, variou de {min(NS)} a {max(NS)} participantes, com mediana de {br(MED, 0)}, e "
  f"{ext(N30)} estudos reuniram menos de 30 atletas.")
P(f"Seis estudos avaliaram adolescentes {c('H25', 'H27', 'H29', 'N3', 'N5', 'U150')}, com médias de 13,81 ± 0,73 anos {c('N5')} a 17,4 ± 2,08 anos {c('H29')}, e dois descreveram a amostra apenas como adolescente {c('N1', 'N8')}. Entre os juniores, as médias foram de 18,6 ± 2,4 anos {c('H15')} e de 18,8 ± 0,20 anos {c('H11')}; nos adultos, de 19,8 ± 1,9 anos {c('N4')} a 30,46 ± 8,29 anos {c('H13')}. O estudo húngaro abrangeu atletas de 14 a 35 anos {c('H34')}, e quatro estudos não relataram a idade {c('H2', 'H4', 'H14', 'H30')}. "
  f"Os dois estudos de handebol de praia avaliaram 17 jogadoras da seleção brasileira, com 27,1 ± 3,8 anos {c('H17')}, e 181 atletas de ambos os sexos, com 25,68 ± 5,95 anos, de equipes classificadas para a Copa da Espanha de 2016 {c('H21')}. Seleções nacionais compuseram ainda a amostra de dois estudos, com 39 jogadoras das seleções adulta, júnior e juvenil do Chile {c('H22')} e 584 atletas húngaros das seleções sub-17, sub-19, sub-21 e adulta e do programa de talentos sub-15 {c('H34')}. Entre as maiores amostras estiveram também 407 adolescentes croatas, comparados a 349 inativos {c('H27')}, e 187 atletas federados, 77 deles profissionais {c('H20')}. No outro extremo, o programa de autorregulação do humor envolveu 6 jogadores, selecionados entre 20 pelos escores mais negativos {c('H10')}.")
P(f"Quanto ao delineamento, {ext(DEL['Transversal'])} estudos foram transversais, {ext(DEL['Longitudinal'])} "
  f"longitudinais, {ext(DEL['Quase-experimental'])} quase-experimentais, {ext(DEL['Cruzado'])} cruzados e "
  f"{ext(DEL['Ensaio randomizado'])} ensaios randomizados (Figura 2E). A medida ocorreu no treinamento em "
  f"{ext(CTX['Treinamento'])} estudos, em laboratório em {ext(CTX['Laboratório'])}, na competição oficial em "
  f"{ext(CTX['Competição oficial'])} e ao longo do período competitivo em {ext(CTX['Período competitivo'])}. Dois estudos avaliaram atletas durante o confinamento da pandemia de COVID-19 {c('H20', 'N3')}. A leitura integral apoiou-se no texto completo em "
  f"{FTL} relatórios e apenas no resumo em {NR - FTL}. O Apêndice A apresenta a extração completa de cada estudo.")
figura("Figura2_Caracteristicas_RS.png", "Figura 2", "Características dos estudos e das populações (QP1)", larg=14.5,
       nota="(A) estudos por ano, média móvel centrada de três anos com intervalo de confiança de Poisson exato e produção "
            "acumulada, com 2026 em curso; (B) país; (C) sexo da amostra; (D) nível competitivo; (E) delineamento; (F) "
            "contexto da medida; percentuais sobre os 34 estudos.")
P("A seguir, as demais questões de pesquisa são respondidas com base nos resultados das análises.")
P(f"**QP2.** {QPS[2]}")
P(f"O Profile of Mood States (POMS) e suas versões, com 30, 36, 48, 58 ou 65 itens, foram empregados em "
  f"{FAM['POMS e versões']} estudos ({pc(FAM['POMS e versões'])}); a Brunel Mood Scale, em três {c('H10', 'H29', 'N5')}; a escala de afeto positivo e negativo (PANAS), em quatro {c('H22', 'H23', 'H27', 'N2')}; a Feeling Scale, em dois {c('H4', 'H25')}; e a subescala afetiva do Self-Assessment Manikin, em dois {c('H13', 'N4')}. Cinco estudos usaram escalas menos difundidas: listas de adjetivos de estados de ânimo {c('H5')}, o método EMPA {c('H19')}, o questionário SAN, de bem-estar, atividade e humor {c('N8')}, uma lista de "
  f"padrões de humor próxima do temperamento {c('H30')} e um questionário de humor de validade incerta {c('H14')} "
  f"(Figura 3A). Em parte dos estudos com o POMS, apenas algumas dimensões foram relatadas, como a tensão ou a fadiga "
  f"{c('H9', 'H17')}; em outro, o escore total entrou em um modelo conjunto sem relato do efeito do humor "
  f"{c('H11')}. O momento da medida foi declarado com precisão em {QI['q4']['sim']} estudos e ficou incerto ou ausente "
  f"nos demais.")
P(f"Entre os estudos com o POMS, a versão de 65 itens foi usada em três {c('H3', 'H21', 'H34')}, a de 58 itens em dois estudos, descritos em três relatórios {c('H31', 'H32', 'N3')}, a de 48 itens em um {c('H11')}, a de 36 itens, atribuída a Raglin e Morgan, em um {c('H15')}, e a de 30 itens em dois {c('H20', 'H28')}. Duas versões reduzidas não declararam o número de itens {c('U049', 'U150')}, e seis estudos não relataram a versão {c('H2', 'H9', 'H17', 'H24', 'O1', 'N1')}. As adaptações declaradas foram sobretudo espanholas {c('H3', 'H11', 'H20', 'H21', 'H31', 'N3')}, e a escala de resposta de 0 a 4 foi informada em três estudos {c('H21', 'H28', 'U150')}. A perturbação total constou de sete estudos com o POMS {c('H3', 'H15', 'H17', 'H31', 'H34', 'N3', 'U150')}. Dois estudos incluíram a dimensão amizade {c('H11', 'H20')}, e dois denominaram a raiva de hostilidade {c('H15', 'U150')}.")
P(f"A Brunel Mood Scale teve versão árabe em dois estudos {c('H10', 'H29')} e forma de 24 itens nos três, com as seis dimensões. O PANAS foi aplicado na versão espanhola de 20 itens {c('H22', 'H23')}, na adaptação croata de 16 itens, com escala de 1 a 7 {c('H27')}, e na versão sérvia {c('N2')}. A Feeling Scale variou de -5 a +5 nos dois estudos, e o SAM teve escala de 9 pontos em um estudo {c('H13')}. Entre as demais escalas, a LEA-RI reuniu 14 adjetivos {c('H5')}, o questionário persa atribuído a Brooms, 32 itens e oito componentes {c('H14')}, e a lista de Allawi, 20 itens na forma final {c('H30')}.")
P(f"Em competição, o humor foi avaliado antes e depois do jogo {c('H2', 'U049')}, cerca de 45 min antes de cada jogo da semifinal {c('H5')}, 24 h antes do primeiro jogo da competição {c('H21')} e antes de cada um dos 10 jogos oficiais e de cada teste de campo {c('H31')}. Nas sessões, a medida ocorreu durante cada corrida de 20 min {c('H4')} e antes e depois de cada jogo, sessão ou tarefa {c('H22', 'H23', 'H29', 'N5')}. Ao longo da temporada, houve cinco medidas em 40 semanas {c('H3')}, medidas mensais de novembro de 2010 a maio de 2011 {c('H11')} e 11 ocasiões mensais de setembro a maio {c('N1')}. "
  f"Nos estudos sobre o ciclo menstrual, cada atleta foi avaliada uma vez na fase em que se encontrava {c('H19')}, ou foi medida em cada fase {c('H24')}, ou no início de seis sessões distribuídas por três fases em dois ciclos {c('N4')}. Durante o confinamento, as medidas ocorreram após cerca de 35 dias de isolamento {c('H20')} e nas semanas 1, 6 e 10 {c('N3')}, e um estudo comparou três horários do dia, às 10h, às 14h e às 18h {c('O1')}. No estudo húngaro, o POMS foi aplicado por entrevista, com referência à semana anterior e sem data declarada em relação à coleta de saliva {c('H34')}. O momento não foi relatado em três estudos {c('H16', 'H30', 'N8')} nem declarado explicitamente em um relatório {c('H32')}.")
figura("Figura3_Instrumentos_Relacoes_RS.png", "Figura 3", "Instrumentos, variáveis relacionadas ao humor e direção dos "
       "achados (QP2 a QP4)", larg=13.5,
       nota="(A) família de instrumento; (B) direção do achado por família de instrumento; (C) gráfico de direção do "
            "efeito por variável relacionada ao humor, conforme a diretriz SWiM; um estudo pode relacionar o humor a mais "
            "de uma variável.")

P(f"**QP3.** {QPS[3]}")
P(f"O humor relacionou-se a variáveis psicológicas em {GR['Variáveis psicológicas']} estudos, a intervenções verbais ou psicológicas em {GR['Intervenção psicológica ou verbal']}, à carga e à recuperação em {GR['Carga e recuperação']}, a marcadores biológicos em {GR['Marcadores biológicos']}, à competição e ao resultado do jogo e ao desempenho físico em {GR['Competição e resultado do jogo']} cada, e ao desempenho técnico em {GR['Desempenho técnico']} (Figura 3C). Entre os {NE} estudos, "
  f"{DIRC['Efeito ou associação']} relataram efeito ou associação, {DIRC['Misto']} resultados mistos e "
  f"{ext(DIRC['Sem efeito'])} ausência de efeito; um foi apenas descritivo, e em outro a direção não pôde ser "
  f"determinada. A Tabela 3 sintetiza os achados por grupo de variáveis; os parágrafos seguintes apresentam os valores "
  f"relatados e as divergências registradas na leitura integral.")
NJ = json.load(open(FIG / "ijrs_numeros.json", encoding="utf-8"))
P(f"Em termos proporcionais, {pc(DIRC['Efeito ou associação'], NE, 1)} dos estudos relataram efeito ou associação e "
  f"{pc(DIRC['Misto'], NE, 1)} resultados mistos. Entre os 12 estudos de intervenção, a classificação dos revisores "
  f"identificou efeito em {NJ['dir_int']['Efeito ou associação']}, resultados mistos em {NJ['dir_int']['Misto']} e "
  f"ausência de efeito em {NJ['dir_int']['Sem efeito']}, distribuição semelhante à do conjunto dos estudos. A Figura 4 "
  f"apresenta a direção dos achados no conjunto dos estudos e nos estudos de intervenção.")
figura("ijrs_direcao_pizza3d.png", "Figura 4", "Direção dos achados sobre o humor no conjunto dos estudos incluídos e "
       "nos estudos de intervenção", larg=15.0,
       nota=f"(A) {NE} estudos incluídos; (B) 12 estudos de intervenção; direção classificada pelos revisores na leitura "
            f"integral; os relatórios {c('H31', 'H32')} descrevem a mesma amostra e foram contados uma vez.")
P(f"**Competição e resultado do jogo.** Em 61 jogadores amadores, o humor avaliado pelo SAM foi mais positivo após a "
  f"partida vencida que após o treino (F(1,180) = 30,48; p < 0,001; η² = 0,34). Com o humor como covariável, as "
  f"diferenças de memória episódica e numérica deixaram de ser significativas, mas a memória visuoespacial permaneceu "
  f"significativa (F = 4,62; p = 0,04) {c('H13')}. Nas semifinais universitárias, as equipes vencedoras assinalaram "
  f"intensidade muito forte nos adjetivos positivos em 31% e 28% das respostas, contra 22% e 19% das adversárias, sem "
  f"teste estatístico {c('H5')}. Em jogadoras universitárias, o escore do POMS e o cortisol salivar aumentaram na "
  f"competição {c('H2')}. Após uma partida, 12 jogadores apresentaram mudança da fadiga (t = -4,408; p < 0,001) e do "
  f"vigor (t = -4,259; p < 0,001), sem alteração da tensão (t = -0,088; p = 0,931); o resumo descreve o vigor como "
  f"aumentado nos resultados e como diminuído na conclusão {c('U049')}. Em 16 jogadoras amadoras, o POMS foi aplicado "
  f"antes de cada teste de campo e de cada jogo oficial. O perfil anterior ao Yo-Yo IR1 apresentou mais depressão "
  f"(d = 0,18), mais fadiga (d = 0,30) e maior perturbação total (d = 0,22) que o perfil anterior aos jogos, com "
  f"perturbação de 139,13 ± 29,94 contra 127,12 ± 23,01 {c('H31')}. Na mesma amostra, as medidas associadas ao Wingate "
  f"e ao cicloergômetro registraram mais fadiga que as dos jogos (d = 0,16; p = 0,046), e a da esteira, maior vigor "
  f"(d = 0,23; p = 0,003), sem declaração explícita do momento de aplicação {c('H32')}.")
P(f"**Carga, recuperação e marcadores biológicos.** Em uma temporada de 40 semanas, a perturbação total permaneceu "
  f"entre 119,0 ± 27,3 e 129,0 ± 42,9, a raiva subiu para 14,1 ± 10,1 em T3, contra 8,7 ± 6,9 em T1 (p < 0,05), e o "
  f"vigor atingiu 20,6 ± 4,4 em T4 (p < 0,05); a fadiga de T1 (13,9 ± 4,0) superou a dos momentos seguintes (7,2 a "
  f"9,6) sem diferença sinalizada pelos autores {c('H3')}. Na seleção brasileira de handebol de praia, a fadiga passou "
  f"de 2,06 ± 2,61 para 4,82 ± 4,05 no 8º dia e para 5,5 ± 4,8 no 18º dia da intertemporada, sem alteração da "
  f"perturbação total {c('H17')}. Em uma equipe portuguesa, a tensão foi maior no início da temporada que nos dois "
  f"momentos seguintes {c('H9')}. Na corrida em esteira, as condições de informação sobre a duração do esforço foram "
  f"aplicadas de modo cego e aleatório após uma linha de base fixa; o afeto diferiu da linha de base após o 10º minuto "
  f"nas sessões fragmentada e superestimada, e a discussão descreve piora, ao passo que o resumo relata aumento "
  f"{c('H4')}. Em 584 atletas húngaros, a perturbação total diminuiu com a idade (η² = 0,033 nos homens e 0,101 nas "
  f"mulheres), embora nas mulheres a mediana tenha subido de 15,5 no sub-15 para 25,5 no sub-19 antes de cair para "
  f"-2,5 nas adultas. O POMS constou de 276 dos 584 atletas e não se associou aos hormônios salivares nos modelos "
  f"ajustados pela idade {c('H34')}. Em adolescentes altamente treinados, a sensibilidade das "
  f"medidas psicométricas mensais para mudanças do desempenho foi inferior a 20% {c('N1')}. Em sete jogadoras escolares, a perturbação total foi de "
  f"108,6 ± 14,71, sem diferença em relação à referência de 100 pontos (p = 0,1740) {c('U150')}.")
P(f"**Variáveis psicológicas, lesão e contexto.** No handebol de praia, o controle de enfrentamento negativo predisse "
  f"a tensão (β = -0,462; R² = 0,21), e a autoconfiança, a depressão (β = -0,275) e a fadiga (β = -0,317) {c('H21')}. "
  f"No confinamento, as mulheres relataram mais depressão (8,26 ± 3,64 contra 6,75 ± 4,00; p = 0,012) e mais fadiga "
  f"(p = 0,045), e os homens, mais vigor (p = 0,03). A depressão (β = 0,25), o vigor (β = 0,24) e a fadiga "
  f"(β = -0,28) predisseram os dias de treino (R² = 0,11; p < 0,001), e a tensão-ansiedade, menor qualidade do sono "
  f"(β = -0,25; p = 0,01) {c('H20')}. Jogadoras jovens confinadas apresentaram perturbação total de 135,54 ± 33,26 a "
  f"139,81 ± 32,33, maior que a do atletismo nas três medidas (pBonferroni = 0,024; 0,016; 0,013), além de mais "
  f"depressão, confusão e raiva. A equipe de handebol era inteiramente feminina, e a de atletismo, mista, e o efeito "
  f"do tempo não foi testado dentro do handebol {c('N3')}. Adolescentes praticantes relataram mais afeto positivo "
  f"(4,71 ± 1,06 contra 4,24 ± 1,10; d = 0,42) e menos afeto negativo (2,82 ± 1,03 contra 3,37 ± 1,17; d = 0,48) que "
  f"inativos {c('H27')}. Em 132 juniores, a solidão predisse o afeto positivo (β = 0,29 e β = -0,32) e o negativo "
  f"(β = 0,27 e β = -0,28), com sinais opostos entre os dois modelos; o resumo atribui 51% de variância explicada a um "
  f"valor que corresponde ao R múltiplo, com R² corrigido de 0,15 {c('N2')}. Jogadores de elite apresentaram mais estados negativos "
  f"pela manhã e mais vigor à noite {c('O1')}.")
P(f"Em jogadoras de elite, o humor foi menor nas fases menstrual, ovulatória e pré-menstrual (4,24 ± 0,10; "
  f"4,17 ± 0,14; 4,11 ± 0,16, média ± erro) que nas fases pós-menstrual e pós-ovulatória (5,31), sem teste entre as "
  f"fases {c('H19')}, e a ansiedade, a raiva e a confusão foram maiores na fase menstrual {c('H24')}. Em oito "
  f"jogadoras amadoras, a valência do SAM não diferiu entre as fases (p = 0,639) {c('N4')}. O escore global do POMS de "
  f"jogadores universitários de handebol foi de 85,12 ± 9,31, contra 80,23 ± 7,12 no voleibol (t = 4,52; p < 0,05); "
  f"esse valor de t não é reproduzido pelas médias e DP relatados {c('H16')}. Os padrões de humor não diferiram por "
  f"posição (F = 0,077; p = 0,926) nem por experiência (F = 0,432; p = 0,513) {c('H30')}. O modelo de predição de "
  f"lesões com o POMS classificou corretamente 88,89% dos casos, sem relato do efeito isolado do humor {c('H11')}.")
GRUPOS5 = [
    ("Competição e resultado do jogo", ["H2", "H5", "H13", "H21", "H31", "H32", "U049"],
     "Vitória associada a humor mais positivo; perfil anterior aos jogos menos perturbado que o anterior ao Yo-Yo IR1; fadiga e vigor alterados após a partida"),
    ("Carga, recuperação e marcadores biológicos", ["H3", "H4", "H9", "H15", "H17", "H34", "N1", "U150"],
     "Variação de dimensões isoladas com a carga; baixa sensibilidade do POMS mensal ao desempenho"),
    ("Variáveis psicológicas e contexto", ["H11", "H14", "H20", "H21", "H27", "H28", "H30", "H34", "N2", "N3"],
     "Habilidades psicológicas, autoconfiança e prática regular associadas a humor mais favorável; solidão e confinamento associados a afeto negativo"),
    ("Intervenções verbais e psicológicas", ["H4", "H10", "H14", "H22", "H23", "H25", "H29", "N5", "N8"],
     "Encorajamento verbal, individual ou combinado com instrução, associado a humor mais favorável; feedback negativo reduziu o afeto positivo; programas e música com protocolo pouco descrito"),
    ("Nutrição e suplementação", ["H15", "H28"], "Melhora apenas intragrupo com a suplementação; sem efeito de tempo nem interação com os planos alimentares"),
    ("Ciclo menstrual e horário do dia", ["H19", "H24", "N4", "O1"],
     "Humor mais negativo nas fases menstrual e pré-menstrual e pela manhã; valência afetiva sem diferença entre as fases em um estudo")]
lin5 = []
for g, ids, txt in GRUPOS5:
    dd = Counter(RD.DIR_CURTA[e["direcao"]] for e in INC if e["id"] in ids and e["id"] not in RD.MESMA_AMOSTRA)
    lin5.append([g, R.cite(*[K[i] for i in ids]).strip("()"), txt,
                 f"{dd['Efeito ou associação']} / {dd['Misto']} / {dd['Sem efeito'] + dd['Descritivo'] + dd['Não determinável']}"])
tabela("Quadro 1", "Síntese estruturada dos achados por grupo de variáveis (diretriz SWiM)",
       ["Grupo de variáveis", "Estudos", "Principais achados", "Efeito / misto / outros"], lin5, [3.2, 5.4, 5.4, 2.0],
       alinhar=["l", "l", "l", "c"], tam=8.5, quadro=True,
       nota="outros: sem efeito, descritivo ou não determinável; um estudo pode compor mais de um grupo.")
_g = NJ["grupos"]
P(f"Quanto à direção por grupo de variáveis, as intervenções verbais e psicológicas reuniram a maior proporção de estudos "
  f"com efeito ({_g['Intervenções verbais e psicológicas'][0]} de {sum(_g['Intervenções verbais e psicológicas'])}), "
  f"seguidas das variáveis psicológicas e do contexto ({_g['Variáveis psicológicas e contexto'][0]} de "
  f"{sum(_g['Variáveis psicológicas e contexto'])}) e do ciclo menstrual e do horário do dia "
  f"({_g['Ciclo menstrual e horário do dia'][0]} de {sum(_g['Ciclo menstrual e horário do dia'])}). Na carga, na "
  f"recuperação e nos marcadores biológicos, predominaram os resultados mistos "
  f"({_g['Carga, recuperação e marcadores biológicos'][1]} de {sum(_g['Carga, recuperação e marcadores biológicos'])}), "
  f"padrão compatível com a variação de dimensões isoladas sem alteração da perturbação total, e os dois estudos "
  f"nutricionais tiveram resultados mistos. A Figura 5 apresenta a frequência dos estudos segundo o grupo de variáveis e "
  f"a direção do achado.")
figura("ijrs_grupos_direcao.png", "Figura 5", "Número de estudos segundo o grupo de variáveis relacionadas ao humor e a "
       "direção do achado", larg=15.0,
       nota="barras empilhadas pela direção do achado, com o total à direita; um estudo pode compor mais de um grupo.")

DIMS6 = ["tensão", "depressão", "raiva", "vigor", "fadiga", "confusão", "PTH", "afeto positivo", "afeto negativo", "valência"]
CEL6 = {}
for e in EST:
    for x in (e.get("leitura") or {}).get("efeitos", []):
        if x.get("dimensao") in DIMS6:
            CEL6.setdefault((e["id"], x["dimensao"]), set()).add("nulo" if str(x.get("direcao", "")).startswith("sem") else "efeito")
MAP6 = {d: Counter(("misto" if len(s) == 2 else next(iter(s))) for (i, dd), s in CEL6.items() if dd == d) for d in DIMS6}
NMAP6 = len({i for i, d in CEL6})
D7 = [x for e in EST for x in (e.get("leitura") or {}).get("efeitos", [])
      if str(x.get("metrica", "")).startswith("d") and x.get("valor") is not None and x.get("dimensao") in DIMS6]
ND7 = len({i for e in EST for i in [e["id"]] for x in (e.get("leitura") or {}).get("efeitos", [])
           if str(x.get("metrica", "")).startswith("d") and x.get("valor") is not None and x.get("dimensao") in DIMS6})
VF6 = (f"{MAP6['vigor']['efeito']} cada" if MAP6["vigor"]["efeito"] == MAP6["fadiga"]["efeito"]
       else f"{MAP6['vigor']['efeito']} e {MAP6['fadiga']['efeito']}, respectivamente")
P(f"Nas fichas da leitura integral, {NMAP6} estudos registraram efeitos por dimensão do humor (Figura 6). O vigor e a "
  f"fadiga reuniram o maior número de estudos com mudança ou associação ({VF6}), seguidos da "
  f"depressão ({MAP6['depressão']['efeito']}); a perturbação total teve mais estudos com resultados mistos "
  f"({MAP6['PTH']['misto']}) que com mudança ({MAP6['PTH']['efeito']}). Apenas um estudo registrou mudança nas seis "
  f"dimensões do POMS ou da BRUMS {c('H29')}, e três não registraram diferença em nenhuma das dimensões relatadas "
  f"{c('H23', 'H28', 'N4')}.")
figura("Figura6_Mapa_Dimensoes_RS.png", "Figura 6", "Mapa dos resultados por estudo e dimensão do humor, segundo a "
       "leitura integral", larg=14.5,
       nota="azul: mudança ou associação relatada; laranja: comparações com e sem diferença na mesma dimensão; cinza: sem "
            "mudança ou associação; célula vazia: dimensão não medida ou sem efeito registrado na ficha; perturbação "
            "total: escore total do POMS ou da BRUMS; valência afetiva: Feeling Scale ou SAM; estudos em ordem "
            "cronológica.")
P(f"Por dimensão, a depressão, a raiva e a "
  f"confusão variaram com a modalidade no confinamento, com a fase do ciclo menstrual, com o horário e com o "
  f"encorajamento verbal {c('H24', 'H29', 'N3', 'O1')}, e a tensão não se alterou após a partida nem entre o jogo e os "
  f"testes de campo {c('U049', 'H31')}. A perturbação total variou com a idade, o tipo de teste, a suplementação e a "
  f"modalidade, mas permaneceu estável ao longo da temporada e da intertemporada {c('H3', 'H17')}. O afeto positivo e o "
  f"negativo diferiram entre praticantes e inativos e associaram-se à solidão {c('H27', 'N2')}, mas apenas o afeto "
  f"positivo respondeu ao feedback negativo {c('H22')}. A valência afetiva mudou em três estudos e não diferiu entre "
  f"as fases do ciclo menstrual em um {c('N4')}.")
P(f"A magnitude padronizada (d de Cohen) foi obtida em {ND7} estudos, com {len(D7)} comparações; a Figura 7 apresenta a de maior magnitude por estudo e dimensão. Três "
  f"estudos relataram o d {c('H27', 'H31', 'N5')}, e apenas um informou o intervalo de confiança {c('H31')}; nos "
  f"demais, o d foi calculado pelos revisores a partir de médias e DP. Os valores relatados variaram de 0,17 a 1,51, e "
  f"o maior deles corresponde ao vigor no jogo com encorajamento verbal {c('N5')}. Os maiores valores calculados "
  f"ocorreram em comparações não testadas ou sem significância segundo os autores, como a fadiga ao longo da "
  f"temporada {c('H3')} e a perturbação total entre modalidades {c('U150')}, e em comparações em que modalidade e "
  f"sexo se confundem {c('N3')}.")
figura("Figura7_Magnitude_Efeitos_RS.png", "Figura 7", "Magnitude dos efeitos padronizados por dimensão do humor",
       larg=14,
       nota="um ponto por estudo e dimensão, com o maior |d| entre as comparações; [k]: número de comparações; círculo "
            "cheio: d relatado pelos autores; círculo vazado: d calculado pelos revisores a partir de médias e DP, sem "
            "considerar a correlação entre medidas repetidas; barra horizontal: IC 95% relatado; linhas tracejadas: "
            "limiares de efeito pequeno, moderado e grande; cores conforme a direção do efeito sobre o humor; os "
            "relatórios " + c('H31', 'H32') + " descrevem a mesma amostra, e apenas o primeiro consta da figura.")

P(f"**QP4.** {QPS[4]}")
INTERV = [
    ("H4", "18 atletas adultos (9 homens e 9 mulheres)",
     "Informação sobre a duração da corrida (fragmentada, superestimada ou indefinida), em ordem cega e aleatória, contra linha de base com duração conhecida, sempre na 1ª sessão",
     "4 sessões de corrida de 20 min a 70% da velocidade de pico", "Feeling Scale durante a corrida",
     "Afeto diferente da linha de base após o 10º min nas sessões fragmentada e superestimada; piora na discussão e aumento no resumo; valores apenas em figura"),
    ("H10", "6 jogadores juvenis de 18 a 20 anos, selecionados entre 20 pelo humor mais negativo",
     "Programa de autorregulação do humor; delineamento A-B-A, sem grupo controle",
     "6 semanas; 2 sessões semanais de 30 a 45 min", "BRUMS árabe; 4 medidas em cada fase",
     "Queda das dimensões negativas e aumento do vigor; vigor sem mudança em 2 dos 6 jogadores e confusão em 1"),
    ("H14", "24 jogadoras da liga principal do Curdistão (12 por grupo)",
     "Aquecimento com música contra grupo controle", "n.r.", "Questionário persa de 32 itens; antes e depois do programa",
     "Diferença nas variações (U = 22; Z = -2,899; p = 0,003); médias praticamente inalteradas na figura e grupos diferentes no pré-teste"),
    ("H15", "25 jogadores juniores de elite (18,6 ± 2,4 anos)",
     "Néctar de jamelão (n = 12) contra placebo de maltodextrina (n = 13), duplo-cego",
     "28 dias; 10 mL/kg/dia", "POMS de 36 itens; início e após 28 dias",
     "Interação na perturbação total (F = 5,336; p = 0,030): queda só no grupo suplementado (100,7 ± 17,0 para 89,7 ± 11,6), sem diferença entre grupos"),
    ("H22", "39 jogadoras das seleções chilenas (13 por grupo)",
     "Feedback positivo, negativo ou ausente, pré-estabelecido", "Sessão única; 30 arremessos",
     "PANAS; imediatamente antes e depois da tarefa",
     "Interação no afeto positivo (F = 4,63; p < 0,05), com queda no feedback negativo (4,20 para 3,70; delta de Cliff = 0,36); afeto negativo sem efeito (F = 1,70)"),
    ("H23", "73 jogadoras da primeira divisão espanhola (70 analisadas)",
     "Feedback comparativo positivo, negativo ou ausente, dado pelos treinadores", "Sessão única; 21 arremessos",
     "PANAS; antes e depois da tarefa", "Sem efeito sobre o afeto positivo nem sobre o negativo"),
    ("H24", "14 jogadoras de 21 a 24 anos",
     "Música de 140 bpm contra ausência de música, em ordem aleatória", "Testes nas fases menstrual, lútea e folicular",
     "POMS em cada fase", "Ansiedade, raiva e confusão maiores na fase menstrual; análise do humor por condição de música n.r. no resumo"),
    ("H25", "20 escolares do sexo masculino (16 ± 1 anos)",
     "Encorajamento verbal com instrução técnica, instrução isolada e controle, em ordem aleatória",
     "3 sessões de 2 x 10 min; intervalo mínimo de 48 h", "Feeling Scale na recuperação e após o jogo",
     "Valência maior na condição combinada que no controle e estável nela, com queda nas demais; F relatado em bloco com a PSE (F ≥ 9,2; ηp² = 0,32)"),
    ("H28", "21 jogadoras profissionais (7 por grupo)",
     "Dieta mediterrânea ou rica em antioxidantes contra dieta livre com recomendações", "12 semanas",
     "POMS de 30 itens; início, meio e 12ª semana",
     "Sem efeito de tempo nem interação em nenhuma dimensão (interação: p de 0,069 a 0,430); resumo e conclusões relatam mudanças"),
    ("H29", "28 escolares com sobrepeso (17,4 ± 2,08 anos; 14 por sexo)",
     "Encorajamento verbal individual, antes e nos intervalos, contra coletivo, durante o jogo",
     "2 sessões de 2 x 12 min de jogo 7 contra 7", "BRUMS árabe; antes e depois, com descrições divergentes",
     "Interação grupo × tempo nas seis dimensões, nos dois sexos (η² de 0,18 a 0,55), favorável ao encorajamento individual"),
    ("N5", "16 escolares obesos (13,81 ± 0,73 anos)",
     "Jogo de passes com contra sem encorajamento verbal, em ordem contrabalançada",
     "2 sessões de 4 x 3 min; intervalo de uma semana", "BRUMS antes e depois de cada jogo",
     "Maior variação do vigor (p = 0,01; ES = -1,51) e menor da perturbação total (p = 0,02; ES = 0,78); demais dimensões sem diferença"),
    ("N8", "28 jogadoras adolescentes (14 por grupo)",
     "Programa de regulação psicoemocional contra grupo controle", "n.r.", "Questionário SAN; momentos n.r.",
     "Melhora de até 38% no bem-estar, na atividade e no humor, relatada apenas no resumo"),
]
P(f"Doze estudos manipularam uma condição e mediram o humor como desfecho (Tabela 4): encorajamento verbal em três "
  f"{c('H25', 'H29', 'N5')}, feedback em dois {c('H22', 'H23')}, programas psicológicos em dois {c('H10', 'N8')}, "
  f"música em dois {c('H14', 'H24')}, intervenção nutricional em dois {c('H15', 'H28')} e informação sobre a duração "
  f"do esforço em um {c('H4')}. Cinco compararam condições nos mesmos participantes {c('H4', 'H10', 'H24', 'H25', 'N5')}, "
  f"e os demais, grupos paralelos. A exposição limitou-se a uma a quatro sessões em metade dos estudos; apenas o "
  f"programa de autorregulação, a suplementação e os planos alimentares duraram semanas {c('H10', 'H15', 'H28')}, e "
  f"dois estudos não relataram a duração {c('H14', 'N8')}.")
lin6 = []
for i, part, interv, dur, med, res in sorted(INTERV, key=lambda x: (NORM[x[0]][0], x[0])):
    e = QE[i]
    lin6.append([R.autor(K[i]), part, interv, dur, med, res, f"{e['qualidade']['pontuacao']}\n({RD.qualidade(e).lower()})"])
tabela("Tabela 4", "Estudos de intervenção: participantes, intervenção e comparador, duração, medida de humor, resultado "
                   "principal e qualidade metodológica",
       ["Estudo", "Participantes", "Intervenção e comparador", "Duração", "Medida de humor e momento",
        "Principal resultado", "Qualidade (0 a 6)"], lin6, [1.9, 2.4, 3.2, 2.0, 2.3, 4.3, 1.2],
       alinhar=["l", "l", "l", "l", "l", "l", "c"], tam=7.5,
       nota="n.r.: não relatado; BRUMS: Brunel Mood Scale; PANAS: Positive and Negative Affect Schedule; POMS: Profile "
            "of Mood States; SAN: questionário de bem-estar, atividade e humor; PSE: percepção subjetiva de esforço; ES: "
            "tamanho de efeito relatado pelos autores.")
P(f"Os três estudos de encorajamento verbal, todos com escolares, relataram humor mais favorável na condição com "
  f"encorajamento. O maior conjunto de efeitos ocorreu na comparação entre encorajamento individual e coletivo, com "
  f"interação nas seis dimensões da BRUMS {c('H29')}; nesse estudo, as condições diferiram também no momento do "
  f"encorajamento, e a aprovação ética é posterior à coleta. No jogo de passes, os tamanhos de efeito do vigor e da "
  f"perturbação total coincidem numericamente com os de variáveis cardíacas, e o resumo traz -1,11 para o vigor "
  f"{c('N5')}. O feedback negativo reduziu o afeto positivo {c('H22')}, e o feedback comparativo não alterou o afeto "
  f"{c('H23')}. Nas intervenções nutricionais, a melhora da perturbação total restringiu-se à comparação intragrupo "
  f"{c('H15')}, e a tabela dos planos alimentares não mostra efeito de tempo nem interação, ao contrário do resumo "
  f"{c('H28')}. Os estudos com programas psicológicos e com música apresentaram protocolo pouco descrito, "
  f"delineamento sem grupo controle {c('H10')}, figura incompatível com a diferença relatada {c('H14')} ou dados "
  f"restritos ao resumo {c('H24', 'N8')}.")
_ti = NJ["int"]
P(f"Com mediana de {br(_ti['n_md'], 1)} participantes por estudo de intervenção (amplitude de {_ti['n_min']} a "
  f"{_ti['n_max']}), o tamanho da amostra associou-se positivamente, mas sem significância, à pontuação de "
  f"qualidade (ρ de Spearman = {br(_ti['rho_nq'], 2)}; p = {br(_ti['p_nq'], 3)}). Segundo os próprios autores, "
  f"{_ti['tot'][0]} dos {_ti['tot'][1]} estudos relataram efeito favorável ({pc(_ti['tot'][0], _ti['tot'][1], 0)}; IC 95% "
  f"de {_ti['tot'][2]}% a {_ti['tot'][3]}%), proporção que supera a obtida pela classificação dos revisores e que reflete "
  f"as divergências entre resumo e resultados registradas na leitura integral. Os intervalos de confiança por tipo de "
  f"intervenção foram amplos, pois nenhum tipo reuniu mais de três estudos. A Figura 8 apresenta a relação entre o "
  f"tamanho da amostra e a qualidade e a proporção de estudos com efeito relatado por tipo de intervenção.")
figura("ijrs_intervencoes_analise.png", "Figura 8", "Análise dos estudos de intervenção sobre o humor", larg=15.5,
       nota="(A) tamanho da amostra em escala logarítmica e pontuação de qualidade, com rótulo do primeiro autor e cor "
            "pelo tipo de intervenção; (B) proporção de estudos com efeito favorável relatado pelos autores, com "
            "intervalo de confiança de Wilson de 95%; n: número de estudos.")
P(f"**QP5.** {QPS[5]}")
RESQ = [QE[i]["qualidade"]["pontuacao"] for i in QE if i not in RD.MESMA_AMOSTRA and (QE[i].get("leitura") or {}).get("fonte") == "resumo"]
P(f"A qualidade foi reavaliada na leitura integral, e as contagens a seguir refletem essa revisão. A pontuação "
  f"diminuiu sobretudo pelo item Q6, por incoerências entre análise e dados relatados, como estatísticas não "
  f"reproduzíveis pelas médias e DP, graus de liberdade ou tamanhos de efeito incoerentes com as estatísticas relatadas, "
  f"estatísticas relatadas em bloco e divergências entre texto e tabelas {c('H16', 'H25', 'H28', 'H29', 'H34', 'N3')}, "
  f"e pelo item Q3, por instrumentos sem versão ou confiabilidade declarada {c('H15', 'H24', 'N8')}. Em um estudo, a leitura do texto completo elevou a pontuação {c('H10')}. A qualidade foi "
  f"alta em {QUAL['Alta']} estudos, moderada em {QUAL['Moderada']} e baixa em {QUAL['Baixa']} (Figura 9). Todos os "
  f"estudos definiram o objetivo e a população, mas a amostra foi descrita integralmente em {QI['q2']['sim']}, o "
  f"instrumento foi nomeado e validado em {QI['q3']['sim']}, o momento da medida foi declarado em {QI['q4']['sim']}, "
  f"houve comparador, controle ou ajuste de confusão em {QI['q5']['sim']}, e a análise estatística foi adequada, com "
  f"medidas de variabilidade, em {QI['q6']['sim']}.")
figura("Figura4_Qualidade_RS.png", "Figura 9", "Avaliação da qualidade metodológica dos estudos incluídos (QP5)",
       larg=13.5, nota="Q1 a Q6: itens adaptados para estudos observacionais e transversais; sim (+), incerto (?) e não "
                       "(−); pontuação de 5 a 6, qualidade alta; de 3 a 4, moderada; de 0 a 2, baixa.")
_q = NJ["qual"]
_it = _q["itens"]
P(f"Em termos proporcionais, o item Q1 foi atendido por todos os estudos, o Q3 por "
  f"{pc(_it['Q3. Instrumento validado e nomeado'][0], NE, 1)} (IC 95% de {_it['Q3. Instrumento validado e nomeado'][1]}% "
  f"a {_it['Q3. Instrumento validado e nomeado'][2]}%), o Q4 por {pc(_it['Q4. Momento da medida declarado'][0], NE, 1)}, "
  f"o Q2 e o Q5 por {pc(_it['Q2. Amostra descrita'][0], NE, 1)} cada, e o Q6 por apenas "
  f"{pc(_it['Q6. Análise estatística adequada'][0], NE, 1)} (IC 95% de {_it['Q6. Análise estatística adequada'][1]}% a "
  f"{_it['Q6. Análise estatística adequada'][2]}%). A pontuação mediana foi {br(_q['md'], 0)}, e a qualidade não "
  f"apresentou tendência temporal (ρ de Spearman = {br(_q['rho'], 2)}; p = {br(_q['p'], 3)}), o que indica que os "
  f"estudos recentes não superaram, em média, as fragilidades de relato dos anteriores. A Figura 10 apresenta a "
  f"proporção de atendimento de cada item e a relação entre a pontuação e o ano de publicação.")
figura("ijrs_qualidade_analise.png", "Figura 10", "Análise da qualidade metodológica dos estudos incluídos", larg=15.5,
       nota="(A) proporção de estudos que atenderam a cada item, com intervalo de confiança de Wilson de 95%; (B) "
            "pontuação de qualidade segundo o ano de publicação, com reta de regressão, faixa de confiança por bootstrap "
            "e área do círculo proporcional ao tamanho da amostra.")
P(f"As maiores pontuações concentraram-se nos ensaios randomizados e nos estudos cruzados e longitudinais publicados a "
  f"partir de 2020; as menores, nos estudos transversais e quase-experimentais e nos extraídos apenas do resumo, que "
  f"pontuaram de {min(RESQ)} a {max(RESQ)}. As três maiores amostras corresponderam a estudos transversais "
  f"{c('H20', 'H27', 'H34')}, e os estudos de intervenção reuniram de 6 a 73 participantes {c('H10', 'H23')}. Quanto às "
  f"lacunas, nenhuma intervenção testou estratégias de recuperação ou de sono, as intervenções verbais limitaram-se a "
  f"sessões isoladas, e apenas um estudo confirmou a fase do ciclo menstrual por teste hormonal {c('N4')}. As "
  f"fragilidades de cada estudo constam do Apêndice C, e as lacunas, da Tabela 5.")

H1("4. Discussão")
P(f"O objetivo desta revisão sistemática foi investigar e analisar o estado da arte das evidências científicas sobre os "
  f"estados de humor em atletas de handebol no treinamento e na competição e avaliar a qualidade metodológica dos "
  f"estudos. Até onde se tem conhecimento, esta é a primeira revisão sistemática a reunir as evidências publicadas sobre "
  f"o tema, com leitura integral dos estudos incluídos, como forma de reunir o estado da arte. {NE} estudos foram "
  f"selecionados; os resultados foram sintetizados e, com base neles, as questões levantadas na presente revisão foram "
  f"respondidas. Três constatações atravessam os tópicos: o humor responde à carga, ao contexto competitivo e à "
  f"interação com treinadores e colegas; o campo depende de um instrumento dominante, aplicado em momentos pouco "
  f"declarados; e a evidência é escassa, raramente experimental e afetada por falhas de relato. A seguir, os resultados "
  f"são discutidos por tópicos, de acordo com as questões abordadas.")
H2("4.1. Estados de Humor no Handebol, Características dos Estudos e das Populações Investigadas e Distribuição "
   "Geográfica das Pesquisas Realizadas")
P(f"A produção é recente e reduzida, com menos de dois estudos por ano. O predomínio de amostras femininas "
  f"contrasta com o desequilíbrio usual das ciências do esporte, mas convive com amostras pequenas, com mediana de {br(MED, 0)} participantes, e com a omissão do sexo em parte dos "
  f"estudos. Essa omissão é relevante, pois atletas de elite do sexo feminino relatam mais ansiedade e depressão que os do "
  f"sexo masculino {R.cite('kew2025sex', 'kuo2025covidsex')}, e, no handebol, as jogadoras confinadas relataram mais "
  f"depressão e fadiga que os jogadores {c('H20')}. Como os estudos sobre o ciclo menstrual divergem "
  f"{c('H19', 'H24', 'N4')}, a amostra mista sem análise por sexo impede justamente a comparação de interesse. A "
  f"divergência repete a literatura geral, em que apenas estudos isolados relataram efeitos do ciclo sobre o humor "
  f"{R.cite('paludo2022menstrual')} e em que os efeitos do ciclo sobre o desempenho de atletas de elite permanecem "
  f"inconclusivos {R.cite('meignie2021menstrual')}.")
P(f"Três estudos avaliaram escolares, e não atletas {c('H25', 'H29', 'N5')}. A concentração na Espanha, na Tunísia e no Brasil, somada a estudos do Irã, do Iraque e "
  f"da Jordânia, revela um campo internacional, porém apoiado em versões traduzidas cuja equivalência transcultural nem "
  f"sempre foi verificada {R.cite('han2020', 'terry2022ltu')}. Essa verificação é necessária, pois o POMS abreviado não "
  f"manteve sua estrutura original em atletas chineses {R.cite('tan2024poms')}.")
P(f"Esse quadro contrasta com o que a própria modalidade já demonstrou ser viável. Uma coorte prospectiva acompanhou "
  f"189 jogadores de elite durante 45 semanas, com registro semanal das cargas de treino, de competição, acadêmicas e "
  f"de trabalho e dos eventos de vida, e associou a carga de treino e os eventos de vida negativos ao risco de lesão e "
  f"de doença {R.cite('e166')}. Em jogadoras semiprofissionais, o monitoramento integrado de uma temporada inteira, "
  f"com 159 sessões de treino, relacionou a carga, o estado mental e os indicadores físicos ao desempenho em jogo "
  f"{R.cite('e198')}. Nenhum desses estudos aplicou instrumento de humor, mas ambos indicam que amostras maiores e "
  f"seguimentos longitudinais são exequíveis no handebol e poderiam incorporar o perfil de humor sem acréscimo "
  f"relevante de custo.")
H2("4.2. Instrumentos, Dimensões e Variáveis Relacionadas ao Humor Mais Investigados")
P(f"O POMS respondeu por pouco mais da metade dos estudos, em versões de 30 a 65 itens pouco comparáveis entre si. Sua versão abreviada, a Brunel Mood Scale, foi concebida para a aplicação repetida no treinamento "
  f"{R.cite('terry2003', 'rohlfs2008')}, mas apareceu em apenas três estudos. As escalas de afeto, como o PANAS e a Feeling "
  f"Scale, medem outro construto, a valência afetiva geral ou momentânea {R.cite('watson1988', 'hardy1989', 'ekkekakis2019')}, "
  f"e não devem ser somadas ao perfil de humor. Além disso, o momento de aplicação da Feeling Scale não é padronizado "
  f"{R.cite('bastos2023fs')}.")
P(f"A leitura integral revelou outros problemas de mensuração. Algumas versões não correspondem à referência citada "
  f"{c('H14', 'H15')}, e uma lista de padrões de humor mede construto próximo do temperamento {c('H30')}. A constante da "
  f"perturbação total {c('H3')} e a confiabilidade na amostra {c('H31', 'N3')} foram omitidas com frequência. No SAM, "
  f"valores baixos indicaram humor positivo, sentido inverso ao usual {c('H13')}, e um escore total maior do POMS foi "
  f"interpretado como humor melhor {c('H16')}. Os itens "
  f"únicos captam a variação momentânea, mas não as dimensões do perfil {c('H25', 'N4')}. As escalas de múltiplos "
  f"itens têm, em grande parte, propriedades de medida aceitáveis, ao passo que os itens únicos mais usados não foram "
  f"validados {R.cite('jeffries2020arom')}.")
P(f"O ponto mais crítico é o momento da medida. Um mesmo escore de vigor tem significados distintos antes de um jogo "
  f"decisivo, após uma sessão de carga elevada ou em um dia de descanso {R.cite('beedie2000', 'lochbaum2021')}. Na "
  f"comparação entre jogos oficiais e testes de campo, o POMS foi aplicado antes de cada teste e de cada jogo. O perfil "
  f"mais perturbado associado ao teste intermitente reflete, portanto, o estado prévio das jogadoras, e não a resposta ao "
  f"teste, como interpretado pelos autores {c('H31')}. No relatório complementar, o momento nem foi declarado {c('H32')}. O horário integra esse problema. Jogadores de elite tiveram mais estados "
  f"negativos pela manhã {c('O1')}, e o desempenho neuromuscular em esportes coletivos foi maior no fim da tarde ou no "
  f"início da noite {R.cite('martinlopez2025timeofday')}, mas os sinais do horário do exercício sobre o humor ainda não "
  f"sustentam recomendações definitivas {R.cite('hu2026timeofdaymood')}.")
P(f"A distinção entre os construtos afetivos ajuda a interpretar essa heterogeneidade. O modelo conceitual de "
  f"{R.autor('stevens2020ahbf')} separa a resposta afetiva ao exercício, avaliada durante ou logo após a tarefa, do afeto "
  f"incidental, que acompanha o dia independentemente do comportamento-alvo. A Feeling Scale aplicada durante a corrida "
  f"{c('H4')} ou na recuperação e após o jogo {c('H25')} mede a primeira; o POMS referido à semana anterior {c('H34')} aproxima-se "
  f"do segundo. A revisão sistemática sobre o modelo circumplexo do afeto em contextos de atividade física "
  f"{R.cite('evmenenko2022circ')} reforça que valência e ativação constituem eixos próprios, e não substitutos do perfil "
  f"de humor. Na dimensão social, a agregação emocional entre parceiros foi demonstrada em duplas de tênis de mesa, nas "
  f"quais a ansiedade, o desânimo e a raiva durante a partida predisseram pior desempenho subjetivo "
  f"{R.cite('freemantle2022dupla')}, mecanismo plausível para equipes de sete jogadores, mas ainda não testado no "
  f"handebol.")
P(f"A variação de dimensões isoladas sem alteração da perturbação total {c('H3', 'H9', 'H17')} é coerente com o uso "
  f"clássico do perfil de humor no monitoramento da carga {R.cite('morgan1987', 'raglin2001')} e com a superioridade das "
  f"medidas autorrelatadas na detecção de respostas ao treinamento {R.cite('saw2015', 'kellmann2018')}. Converge também "
  f"com o futebol, em que os escores do POMS se relacionaram à variação da carga {R.cite('selmi2023poms')}, e com o rúgbi "
  f"de elite, em que cargas diárias predisseram queda do humor com defasagens variáveis {R.cite('crewther2025rugby')}. O "
  f"escore total pode ocultar mudanças em dimensões específicas, e por isso a leitura do perfil tem sido preferida à da "
  f"soma {R.cite('lane2000', 'parsonssmith2017')}. Há, porém, explicações alternativas. A estabilidade da "
  f"perturbação total pode refletir falta de poder {c('H3')}, e o ajuste individual da carga pela comissão técnica impede "
  f"atribuí-la à boa adaptação {c('H17')}. As alterações de humor no overreaching não funcional ou no overtraining "
  f"apoiam-se, além disso, em evidência limitada e heterogênea {R.cite('valdesalici2026nfor')}, e nenhum estudo "
  f"documentou a transição até o overtraining com queda prolongada do desempenho {R.cite('weakley2022ots')}.")
P(f"Quanto ao desempenho, a ausência de correlação com a condição física {c('H9')} não permite conclusões, e as medidas "
  f"mensais do POMS tiveram sensibilidade inferior a 20% para mudanças do desempenho físico {c('N1')}. A resolução "
  f"temporal pode condicionar esse achado, mas a maior frequência de medida não basta, pois itens únicos de bem-estar, "
  f"entre eles o humor, associaram-se de modo predominantemente trivial a moderado à carga "
  f"{R.cite('duignan2020single')}.")
P(f"A vitória associou-se a humor mais positivo que o treino {c('H13')}, mas a mediação do humor sobre as diferenças de "
  f"memória foi inferida sem teste formal, e a diferença na memória visuoespacial persistiu após o ajuste. No futebol "
  f"profissional, a vitória também se associou a mais prazer e melhor bem-estar {R.cite('fessi2018matchoutcome')}, e, no "
  f"basquetebol 3 × 3, a derrota e o jogo equilibrado associaram-se a maior percepção de esforço "
  f"{R.cite('sansone2025basketball')}. No handebol, o bem-estar no dia do jogo, medido por questionário não validado, interagiu com o "
  f"tipo de partida sobre o resultado {R.cite('e189')}. A relação inversa, do humor "
  f"pré-jogo para o resultado, apoia-se apenas na comparação descritiva de duas semifinais {c('H5')}. Após uma partida, a "
  f"fadiga e o vigor variaram com o limiar de dor no ombro, mas o resumo descreve o vigor ora como aumento, ora como "
  f"diminuição {c('U049')}. Em atletas de praia, as habilidades psicológicas e a autoconfiança associaram-se a humor mais "
  f"favorável na véspera da competição {c('H21')}, em consonância com os modelos que vinculam a regulação emocional e o "
  f"clima social ao estado afetivo dos atletas {R.cite('robazza2022', 'tamminen2019', 'meyers2024')}.")
P(f"No confinamento pela pandemia, a perturbação do humor de jogadoras jovens superou a de atletas do atletismo "
  f"{c('N3')}, e a solidão predisse o afeto de jogadores juniores {c('N2')}. No primeiro estudo, porém, o grupo do "
  f"handebol era exclusivamente feminino, o que confunde modalidade e sexo, e, no segundo, o sinal do coeficiente da "
  f"solidão inverteu-se entre as tabelas. Os achados convergem, ainda assim, com a pior saúde mental de atletas na pandemia, atenuada pelo treino domiciliar "
  f"{R.cite('jia2023covid')}, com a associação do apoio social a menos ansiedade e depressão "
  f"{R.cite('luo2025apoiosocial')} e com a solidão como preditora de burnout em atletas adolescentes "
  f"{R.cite('pacewicz2025solidao')}.")
P(f"A pressão competitiva atua também antes do jogo. A ansiedade foi medida com o humor na véspera "
  f"{c('H21')}, mas sua evolução nas horas que antecedem a partida permanece pouco descrita. Em jovens "
  f"basquetebolistas, a ansiedade somática aumentou só após a partida {R.cite('garciaceberino2022ansiedade')}. Em atletas de diversas modalidades, a percepção de ameaça associou-se a mais "
  f"ansiedade esportiva, e o mindfulness, a menos {R.cite('karademir2026desafio')}, e, em esgrimistas de elite, a "
  f"avaliação do estresse, o enfrentamento, a emoção e o desempenho relacionaram-se de forma dinâmica "
  f"{R.cite('doron2021avaliacao')}. O humor pré-jogo deve, portanto, ser interpretado "
  f"com a ansiedade e com a avaliação de desafio ou de ameaça.")
P(f"Os estudos incluídos não testaram os mecanismos que ligam a carga, o contexto e o humor, mas a literatura permite "
  f"delimitar quatro vias, a serem tratadas como hipóteses. A primeira é endócrina. Em jogadoras de handebol, quatro jogos "
  f"de torneio elevaram o cortisol e a interleucina 6 e reduziram o IGF-1, padrão de ativação do eixo "
  f"hipotálamo-hipófise-adrenal e de desequilíbrio entre anabolismo e catabolismo {R.cite('pancar2026torneio')}. Três "
  f"estudos incluídos mediram o cortisol com o humor ou o afeto {c('H2', 'H4', 'H34')}, e, no maior deles, o humor não se "
  f"associou aos hormônios salivares nos modelos ajustados pela idade. No basquetebol profissional, testosterona, "
  f"cortisol e carga relacionaram-se apenas fracamente com o bem-estar {R.cite('kamarauskas2024hormonios')}, e, no "
  f"futebol de elite, o estresse, a fadiga e a dor muscular autorrelatados refletiram a queda da aptidão física no "
  f"período congestionado, ao passo que os marcadores bioquímicos não a refletiram {R.cite('saidi2022congestao')}.")
P(f"A segunda via envolve o sono e a recuperação. No rúgbi profissional, as viagens internacionais reduziram o sono e o "
  f"bem-estar, e o efeito dos jogos variou entre as equipes {R.cite('lo2022rugbisono')}. Na seleção feminina de "
  f"basquetebol, a duração do sono variou muito entre as atletas, e os autores indicaram sua otimização para atenuar "
  f"perturbações do humor {R.cite('bird2025basquete')}. Dado o efeito das intervenções de sono sobre o humor "
  f"{R.cite('gwyther2022', 'walsh2026sleep')} e as semanas com dois ou mais jogos, o sono é candidato natural a mediador. A terceira via é a da carga acumulada, cuja variação interindividual aumenta nas "
  f"semanas congestionadas {R.cite('buchel2026congestao')}, o que pode explicar por que as médias da equipe ocultam "
  f"respostas individuais.")
P(f"A quarta via é social e cognitiva. O contágio emocional pode explicar a sensibilidade do humor ao resultado {c('H13')} e "
  f"ao convívio da equipe {c('N2', 'N3')}, pois as emoções da equipe após o jogo associaram-se às emoções individuais no "
  f"futebol {R.cite('rumbold2022emocoes')}, e estados induzidos por colegas modificaram o esforço, a coesão e o "
  f"desempenho {R.cite('eldadi2023contagio')}. Segundo o modelo de Lazarus, a emoção decorre da avaliação da relação "
  f"entre as exigências da situação e os recursos do atleta {R.cite('lazarus2000')}, o que integra a avaliação de ameaça "
  f"discutida acima. As quatro vias não são excludentes, e nenhum estudo incluído testou essas mediações, o que "
  f"define uma prioridade de pesquisa.")
P(f"A comparação mostra convergências e uma diferença de método. No basquetebol, a Brunel Mood Scale explicou "
  f"49,0% da variância do bem-estar e 46,8% da prontidão, e suas subescalas, 26,0% da variância da eficiência das "
  f"jogadoras {R.cite('bird2025basquete')}. No "
  f"hóquei no gelo, o apoio social e o comportamento orientado à tarefa influenciaram o bem-estar e a saúde mental de "
  f"atletas de elite {R.cite('veillette2025hoquei')}, em consonância com o papel do clima de tarefa no handebol "
  f"{R.cite('e187')}. A diferença está no instrumento. No voleibol e no futebol predominam questionários compostos de "
  f"bem-estar, como o índice de Hooper, que reúnem fadiga, sono, dor muscular e estresse e, por vezes, um item de humor {R.cite('rebelo2024voleibol', 'saidi2022congestao')}, "
  f"ao passo que, no handebol, predominou o perfil multidimensional do POMS. Essa diferença favorece a leitura das "
  f"dimensões, mas dificulta a comparação com modalidades cujos achados se apoiam em itens únicos sem validação "
  f"demonstrada {R.cite('jeffries2020arom')}. As exigências do handebol, com contato frequente e intermitência "
  f"{R.cite('povoas2012', 'michalsik2012')}, aproximam-se das do rúgbi e do basquetebol, cuja literatura serve, porém, "
  f"como fonte de hipóteses, e não como substituto da evidência específica.")
H2("4.3. Métodos e Protocolos das Intervenções sobre o Humor")
P(f"O encorajamento verbal, individual ou combinado "
  f"com instrução técnica, melhorou o humor e a valência afetiva durante a prática {c('H25', 'H29', 'N5')}, e o feedback "
  f"negativo reduziu o afeto positivo {c('H22')}. No futebol, o encorajamento verbal elevou a carga interna e o "
  f"desempenho técnico na maioria dos estudos, sobretudo em jovens e amadores {R.cite('selmi2026encorajamento')}, e, no "
  f"basquetebol juvenil, aumentou o prazer e também a fadiga {R.cite('yilmaz2025basquete')}. A ausência de efeito do "
  f"feedback comparativo na primeira divisão {c('H23')} sugere que o nível competitivo e a relação com o treinador moderam "
  f"essa influência, hipótese compatível com a relação atenuada entre clima motivacional e afeto em atletas de elite "
  f"{R.cite('lochbaum2024clima')}. A falta de poder é explicação alternativa, pois os subgrupos com baixa satisfação "
  f"reuniram de seis a onze jogadoras.")
P(f"A leitura integral impõe ressalvas. No estudo com escolares com sobrepeso, os grupos diferiram também "
  f"no momento do encorajamento, os graus de liberdade são incompatíveis com a análise por sexo, e a aprovação ética é "
  f"posterior à coleta {c('H29')}. Com escolares obesos, os tamanhos de efeito do humor repetem os da frequência cardíaca, "
  f"embora os valores de p tenham sido reproduzidos com os dados suplementares {c('N5')}. "
  f"No jogo reduzido, as estatísticas da Feeling Scale foram relatadas em bloco com as da percepção de esforço "
  f"{c('H25')}, e o ensaio com feedback negativo, o mais rigoroso, tem resumo que inverte o resultado principal "
  f"{c('H22')}. A direção do efeito verbal é plausível, e sua magnitude, incerta.")
P(f"As intervenções nutricionais não sustentam efeito sobre o humor. Com néctar de jamelão, a perturbação total caiu "
  f"apenas no grupo suplementado, sem diferença entre os grupos, e esse grupo partiu de valores piores, o que favorece a "
  f"regressão à média {c('H15')}. Nos planos alimentares, a tabela não mostra efeito do tempo nem interação, embora o "
  f"resumo e as conclusões afirmem mudanças significativas {c('H28')}. O efeito da cafeína sobre o humor foi maior em "
  f"boxeadores de elite que em atletas recreacionais {R.cite('jodra2020caffeine')}, o que sugere modulação pelo nível do atleta.")
P(f"As intervenções psicológicas e musicais foram descritas de modo insuficiente. O programa de "
  f"autorregulação selecionou os seis jogadores com pior humor, sem grupo controle, o que favorece a regressão à média, e "
  f"a melhora mantida na fase sem tratamento não distingue o efeito do programa do efeito do tempo {c('H10')}. No "
  f"aquecimento com música, a figura mostra humor praticamente inalterado nos dois grupos, em contradição com a diferença "
  f"significativa informada {c('H14')}, e o programa de regulação psicoemocional só foi acessível pelo resumo, sem "
  f"estatísticas {c('N8')}. Na literatura geral, a música aumenta a valência afetiva no exercício agudo "
  f"{R.cite('he2025music')}. Nenhuma intervenção testou estratégias de recuperação ou de sono, embora as intervenções de "
  f"sono modifiquem o humor de atletas {R.cite('gwyther2022')}, sobretudo o afeto positivo, a ansiedade, a tensão e o "
  f"vigor {R.cite('walsh2026sleep')}.")
P(f"As intervenções psicológicas estruturadas, ainda raras no handebol {c('H10')}, têm evidência mais ampla em outras "
  f"modalidades. No futebol, um programa de 13 semanas melhorou o controle do estresse, a ansiedade cognitiva e a "
  f"autoconfiança {R.cite('dominguez2024intervencao')}, e o treino com restrições estressantes favoreceu a resiliência da "
  f"equipe, com tendência de aumento da ansiedade {R.cite('tassi2023restricoes')}. O mindfulness não teve efeito "
  f"significativo sobre a saúde mental em ensaios randomizados {R.cite('wang2023mindfulness')}, mas reduziu a ansiedade, a "
  f"depressão e a fadiga psicológica em atletas de alto nível {R.cite('zhang2025mindfulness')} e melhorou a regulação "
  f"emocional (g = 0,81, com sete estudos) {R.cite('li2026regulacao')}. No handebol de elite, reduziu a frustração "
  f"percebida {R.cite('e199')}, o que torna promissora a inclusão do humor como desfecho nesses ensaios.")
P(f"A literatura recente de outras modalidades contextualiza esses resultados. Na metanálise de "
  f"{R.autor('reinebo2024')}, o treino de habilidades psicológicas (g = 0,83), as abordagens baseadas em mindfulness e "
  f"aceitação (g = 0,67) e a imagética (g = 0,75) superaram os controles no desempenho, e, em 24 ensaios com 853 "
  f"atletas, as intervenções psicológicas reduziram a ansiedade-estado (SMD = −0,99), com maior efeito do treino de "
  f"habilidades psicológicas tradicional {R.cite('liansiedade2025')}. Nos esportes coletivos praticados por adultos sem "
  f"transtorno diagnosticado, a revisão de {R.autor('rocha2026coletivos')} reuniu seis estudos e destacou um ensaio em "
  f"que os jogos reduzidos combinados com encorajamento verbal reduziram a perturbação do humor, resultado coerente com "
  f"os três estudos de encorajamento verbal desta revisão {c('H25', 'H29', 'N5')}.")
P(f"No handebol, as intervenções psicológicas mais recentes não mediram o humor. O treino de imagética funcional, "
  f"testado em 36 jogadoras profissionais distribuídas aleatoriamente entre imagética funcional, imagética motora e "
  f"controle, reduziu a desregulação emocional, a ansiedade e o estresse percebido em todos os grupos ao longo do tempo, "
  f"e apenas o tempo de reação diferiu a favor das condições de imagética {R.cite('e173')}. Um programa breve de "
  f"compaixão e de terapia de aceitação e compromisso na seleção portuguesa sub-18 associou-se a mais atenção plena e "
  f"habilidades psicológicas e a menos estresse competitivo, sem grupo controle {R.cite('e163')}. A melhora do grupo "
  f"controle no primeiro ensaio e a ausência de comparador no segundo repetem as fragilidades observadas nos estudos "
  f"incluídos e mostram que a inclusão do perfil de humor como desfecho secundário desses protocolos é uma oportunidade "
  f"ainda não aproveitada.")
H2("4.4. Qualidade Metodológica e Certeza da Evidência")
P(f"{ext(QUAL['Alta']).capitalize()} estudos alcançaram qualidade alta, {ext(QUAL['Moderada'])}, moderada, e "
  f"{ext(QUAL['Baixa'])}, baixa, com falhas recorrentes na descrição da amostra, no momento da medida, no controle de "
  f"confusão e, sobretudo, na análise estatística. A leitura integral revelou problemas de integridade que a pontuação "
  f"não capta. O resumo, o texto ou as conclusões contradizem os resultados em vários estudos "
  f"{c('H4', 'H14', 'H20', 'H22', 'H28', 'N2', 'U049')}. Há valor de t que deixa de ser significativo quando recalculado a "
  f"partir das médias e dos desvios-padrão {c('H16')}, graus de liberdade incompatíveis com a amostra "
  f"{c('H13', 'H29')}, tamanhos de efeito incoerentes com os valores de F {c('H34')}, relato seletivo de dimensões "
  f"{c('H15', 'H21')}, circularidade entre preditor e desfecho {c('H11')} e aprovação ética posterior à coleta "
  f"{c('H29')}. A qualidade alta indica, portanto, relato e delineamento mais completos, e não ausência de viés. As "
  f"fragilidades de cada estudo constam do Apêndice C.")
P(f"A certeza de cada achado foi julgada, sem níveis formais, pelos domínios da abordagem GRADE {R.cite('guyatt2008')}: consistência, "
  f"precisão, validade interna e direcionalidade, isto é, a correspondência entre os estudos e a pergunta da revisão. Achados apoiados em estudos observacionais partiram de certeza baixa, e "
  f"os apoiados em ensaios, de certeza mais alta, rebaixada conforme as fragilidades identificadas na leitura.")
P(f"*Comunicação verbal.* O encorajamento verbal elevou o vigor ou preservou a valência afetiva em três estudos com "
  f"escolares {c('H25', 'H29', 'N5')}, e o feedback negativo reduziu o afeto positivo de jogadoras de seleções "
  f"{c('H22')}, mas o feedback comparativo não alterou o afeto na primeira divisão {c('H23')}. A direção é consistente, "
  f"mas as amostras são pequenas, sem intervalos de confiança, os ensaios não foram cegados, e um deles tem falhas de "
  f"integridade (seção 4.3). Como três dos cinco estudos avaliaram escolares em jogos adaptados, a evidência é indireta "
  f"para atletas. A certeza é baixa em contexto escolar e muito baixa para atletas federados.")
P(f"*Resultado do jogo.* A vitória associou-se a humor mais positivo em 61 jogadores amadores {c('H13')}, com apoio "
  f"apenas descritivo ou fragmentário de outros dois estudos {c('H5', 'H2')}. Graus de liberdade incompatíveis com a "
  f"amostra e a exclusão das equipes derrotadas ou empatadas comprometem a precisão e a validade interna. A certeza é "
  f"muito baixa.")
P(f"*Carga e temporada.* A fadiga aumentou em 18 dias de treinamento intenso, com d calculado pelos revisores de 0,81 e "
  f"0,89 {c('H17')}, e a raiva e o vigor variaram em uma temporada de 40 semanas, sem mudança da perturbação total "
  f"{c('H3')}. A consistência é parcial, pois a fadiga e a tensão foram maiores no início da temporada em dois estudos "
  f"{c('H3', 'H9')}. Grupos únicos de 14 a 17 atletas, sem controle, reduzem a precisão e a validade interna, "
  f"embora a evidência seja direta. A certeza é baixa.")
P(f"*Recursos psicológicos e convívio social.* As habilidades psicológicas e a autoconfiança correlacionaram-se "
  f"negativamente com as dimensões negativas do humor (r de −0,22 a −0,39) em 181 atletas {c('H21')}, a prática regular "
  f"associou-se a mais afeto positivo e a menos afeto negativo (d = 0,42 e 0,48) {c('H27')}, e a solidão predisse o afeto "
  f"de juniores {c('N2')}. As amostras são as maiores da revisão e a direção é consistente, mas os estudos são "
  f"transversais, sem ajuste para confundidores e com falhas de relato (início desta seção). A certeza é baixa para a associação e "
  f"muito baixa para sua direção causal.")
P(f"*Ciclo menstrual e horário do dia.* Os dois estudos favoráveis a variações com a fase do ciclo não testaram as fases "
  f"entre si ou foram lidos só no resumo {c('H19', 'H24')}, e o único com fases confirmadas por teste urinário de hormônio "
  f"luteinizante não encontrou diferença, com oito jogadoras {c('N4')}. O efeito do horário depende de um único resumo, "
  f"sem estatísticas {c('O1')}. A certeza é muito baixa.")
P(f"*Outras intervenções e marcadores biológicos.* Os ensaios nutricionais não mostraram diferença entre grupos "
  f"{c('H15', 'H28')}, e as intervenções psicológicas e musicais carecem de controle adequado e de descrição suficiente "
  f"{c('H10', 'H14', 'N8')}. A certeza é muito baixa em qualquer direção. Na maior amostra, a perturbação total não se associou aos hormônios salivares {c('H34')}, com certeza "
  f"baixa, pois só 276 dos 584 atletas tinham dados do POMS e vários tamanhos de efeito são incoerentes com as "
  f"estatísticas.")
P(f"A cautela no julgamento da certeza é coerente com a literatura metanalítica. Na síntese de "
  f"{R.autor('reinebo2024')}, os efeitos moderados das intervenções psicológicas sobre o desempenho deixaram de ser "
  f"significativos quando os ensaios não randomizados e os desfechos subjetivos foram removidos na análise de "
  f"sensibilidade, e, na metanálise sobre a ansiedade, a escolha do instrumento alterou a magnitude estimada "
  f"{R.cite('liansiedade2025')}. As duas condições, delineamento não randomizado e desfecho autorrelatado com "
  f"instrumentos heterogêneos, caracterizam a maior parte dos estudos desta revisão, o que justifica a certeza baixa ou "
  f"muito baixa atribuída aos achados principais.")

H2("4.5. Limitações e Estudos Futuros")
P(f"Embora {NE} estudos tenham sido publicados desde 2008, com maior ênfase nas publicações a partir de 2018, é "
  f"necessário desenvolver a produção de evidências científicas experimentais sobre os estados de humor no handebol, "
  f"pois, apesar do interesse crescente pelo tema, há uma vasta lacuna de conhecimento sobre as intervenções, tanto no "
  f"treinamento quanto na competição.")
P(f"Foram observadas limitações importantes nos estudos, especialmente quanto às populações menos investigadas, como "
  f"os atletas do sexo masculino em amostras exclusivas, os goleiros e as categorias de formação, e quanto ao momento "
  f"da medida, declarado com precisão em apenas {QI['q4']['sim']} estudos. Não apenas estudos observacionais precisam "
  f"ser realizados, mas também estudos experimentais bem desenvolvidos, com rigor metodológico, como ensaios "
  f"randomizados por equipes {R.cite('campbell2012')}, com cálculo de poder {R.cite('button2013', 'abt2020')}, relato "
  f"conforme o CONSORT {R.cite('schulz2010')} e descrição da intervenção conforme o TIDieR {R.cite('hoffmann2014')}.")
P(f"O delineamento da presente revisão sistemática também tem limitações. A triagem e a extração foram assistidas por modelo de linguagem, sem conferência "
  f"humana concluída. Nas duas etapas, 59 relatórios não foram recuperados, e {ext(NR - FT)} "
  f"foram extraídos apenas do resumo. A atualização restringiu-se a cinco fontes de acesso programático, sem a Scopus, a "
  f"Web of Science e a LILACS. O critério de tipo de documento, restrito a artigos completos publicados em periódicos, "
  f"foi explicitado apenas na revisão final e levou à exclusão de três relatórios antes incluídos, um preprint, um "
  f"trabalho completo em anais e um resumo de congresso, o que pode ter omitido evidência recente ainda não publicada "
  f"em periódico. O protocolo não foi registrado prospectivamente, a "
  f"avaliação com seis itens não substitui instrumentos formais de risco de viés, o julgamento da certeza não seguiu "
  f"perfil de evidência formal, e os tamanhos de efeito calculados pelos revisores dependem da exatidão dos dados "
  f"publicados. A heterogeneidade impediu a metanálise {R.cite('hopkins2009')}, e a síntese seguiu a diretriz SWiM "
  f"{R.cite('campbell2020')}. Entre os pontos fortes, estão a busca em oito bases sem restrição de data, a releitura integral dos relatórios, que corrigiu onze decisões anteriores e "
  f"revisou dados e pontuações de qualidade, e a rastreabilidade de cada resultado até o trecho literal da fonte.")
P("A Tabela 5 converte as lacunas identificadas em uma agenda de pesquisa sobre o humor no handebol.")
tabela("Tabela 5", "Agenda de pesquisa sobre o humor no handebol",
       ["Lacuna identificada", "Situação atual", "Recomendação"],
       [["Momento da medida", "Declarado com precisão em parte dos estudos; medidas prévias lidas como resposta",
         "Medidas antes e após jogos e sessões, com registro do horário e do contexto"],
        ["Instrumento", "POMS em versões de 30 a 65 itens; BRUMS pouco usada",
         f"BRUMS ou POMS abreviado validado no idioma, com todas as dimensões {R.cite('vlachopoulos2023brums')}"],
        ["Delineamento", "Predomínio de estudos transversais; poucos ensaios",
         f"Ensaios por equipes e medidas repetidas com modelos multivariados {R.cite('afonso2025futebol')}"],
        ["Integridade do relato", "Contradições entre resumo e resultados; estatísticas incompletas",
         "Médias, desvios-padrão, estatísticas e tamanhos de efeito completos, com protocolo registrado"],
        ["Sexo e ciclo menstrual", "Amostras mistas sem análise por sexo",
         f"Análise por sexo e registro preciso da fase do ciclo {R.cite('meignie2021menstrual')}"],
        ["Intervenções", "Comunicação verbal e feedback testados em sessões isoladas",
         "Programas de comunicação do treinador, clima de tarefa, sono e recuperação na temporada"],
        ["Nutrição e energia", "Efeitos inconsistentes em amostras pequenas",
         f"Considerar a relação entre saúde mental e deficiência energética relativa {R.cite('mountjoy2023reds')}"],
        ["Mecanismos", "Cortisol, sono e humor raramente medidos em conjunto",
         f"Medidas combinadas de marcadores endócrinos, sono e humor em semanas congestionadas {R.cite('pancar2026torneio', 'lo2022rugbisono')}"],
        ["Dinâmica da equipe", "Humor analisado no nível individual",
         f"Modelos multinível com emoções coletivas e contágio emocional {R.cite('rumbold2022emocoes')}"],
        ["Treino psicológico", "Habilidades psicológicas e mindfulness pouco testados",
         f"Ensaios com treino de habilidades psicológicas ou mindfulness e o humor como desfecho {R.cite('zhang2025mindfulness', 'dominguez2024intervencao')}"],
        ["Desempenho em jogo", "Poucos estudos relacionaram humor e rendimento",
         "Humor medido por instrumento validado e indicadores de jogo sob pressão"]],
       [3.4, 5.9, 7.6], alinhar=["l", "l", "l"], tam=9.5)
P(f"Além das lacunas da Tabela 5, convém adotar instrumentos comuns a outras modalidades coletivas, o que permitiria "
  f"comparar o handebol com o futebol, o basquetebol e o voleibol {R.cite('rebelo2024voleibol', 'bird2025basquete')}, e "
  f"considerar o calendário congestionado e a variação individual da carga como moderadores do humor "
  f"{R.cite('buchel2026congestao')}.")

H2("4.6. Inovações, Pontos Fortes e Aplicações Práticas")
P(f"Após extensa busca na literatura e em bases de dados internacionais, constatou-se que a presente revisão sistemática "
  f"é a primeira desenvolvida na literatura sobre os estados de humor no handebol. Além desse caráter relevante, uma vez "
  f"que o humor integra o monitoramento da saúde mental e da resposta à carga {R.cite('reardon2019', 'terry2021')}, e com "
  f"base nas evidências apresentadas, pouco se testou experimentalmente, e as evidências são limitadas. O presente "
  f"estudo é inovador ao trazer esses dados à luz com base nas evidências existentes e, assim, demonstra a necessidade "
  f"de investimento em novos estudos experimentais no treinamento e na competição do handebol.")
P(f"Realizou-se uma análise profunda, atual e inédita dos principais resultados dos estudos sobre o humor no handebol, "
  f"com releitura integral de todos os relatórios, conferência dos números com as tabelas das fontes, cálculo dos "
  f"tamanhos de efeito omitidos e rastreabilidade de cada resultado até o trecho literal da fonte (Apêndice A).")
P(f"No cenário pós-pandemia, em que a saúde mental e emocional dos atletas piorou {R.cite('jia2023covid')} e em que "
  f"as jogadoras confinadas relataram mais depressão e fadiga {c('H20', 'N3')}, percebe-se a real importância de "
  f"aprofundar o estudo do humor e das intervenções capazes de modificá-lo. Assim, a presente revisão demonstra diversos "
  f"pontos fortes e aplicações práticas que podem ser replicados e até aprimorados em novos estudos.")
P("Com base nas recomendações dos estudos incluídos nesta revisão, estratificaram-se informações relevantes para "
  "pesquisadores e gestores esportivos e para técnicos, psicólogos do esporte e atletas, a fim de orientar a prática e "
  "identificar lacunas a serem investigadas em pesquisas futuras. Dada a certeza baixa ou muito baixa, as recomendações "
  "constituem orientações prudentes. Os cuidados e as observações a serem considerados são apresentados na Tabela 6.")
REC_P = [f"Medidas repetidas por sessão ou registros momentâneos, com instrumento validado e horário fixo "
         f"{R.cite('majer2026esm', 'reifsteck2021')}.",
         f"Declaração do momento da medida em relação ao jogo, à sessão ou ao teste {R.cite('beedie2000', 'lochbaum2021')}.",
         f"BRUMS ou POMS abreviado validado no idioma, com todas as dimensões e confiabilidade na amostra "
         f"{R.cite('vlachopoulos2023brums')}.",
         f"Análise por sexo e registro preciso da fase do ciclo menstrual {R.cite('meignie2021menstrual')}.",
         f"Ensaios randomizados por equipes, com cálculo de poder {R.cite('campbell2012', 'button2013')}.",
         f"Relato completo de médias, desvios-padrão, estatísticas e tamanhos de efeito, conforme o CONSORT "
         f"{R.cite('schulz2010')} e o TIDieR {R.cite('hoffmann2014')}.",
         f"Medidas combinadas de marcadores endócrinos, sono e humor em semanas congestionadas "
         f"{R.cite('pancar2026torneio', 'lo2022rugbisono')}.",
         f"Modelos multinível com emoções coletivas e contágio emocional {R.cite('rumbold2022emocoes')}.",
         f"Perfil de humor como desfecho de programas de habilidades psicológicas, imagética e mindfulness "
         f"{R.cite('e173', 'zhang2025mindfulness')}."]
REC_T = [f"Monitoramento breve e regular do humor, com instrumento validado e em horário fixo "
         f"{R.cite('terry2021', 'rohlfs2024')}.",
         f"Atenção à fadiga e ao vigor ao longo da temporada e da intertemporada {c('H3', 'H17')}.",
         f"Encorajamento verbal individual nas sessões e nos jogos reduzidos {c('H25', 'H29', 'N5')}.",
         f"Cautela com a comunicação negativa, dada sua repercussão sobre o afeto positivo {c('H22')}.",
         f"Estímulo ao clima orientado à tarefa {R.cite('e187', 'lochbaum2024clima')}.",
         f"Consideração do horário do dia e do ciclo menstrual no planejamento de treinos e testes {c('O1', 'H19')}.",
         f"Educação e triagem do sono, com registro em viagens e torneios {R.cite('walsh2021', 'lo2022rugbisono')}.",
         f"Monitoramento individual nas semanas com dois ou mais jogos {R.cite('buchel2026congestao')}.",
         f"Música autosselecionada antes da tarefa, ainda não testada no handebol {R.cite('delleli2023pretaskmusic')}."]
lin6r = [[("•  " + a_) if a_ else "", ("•  " + b_) if b_ else ""] for a_, b_ in zip(REC_P, REC_T)]
assert len(REC_P) == len(REC_T)
tabela("Tabela 6", "Recomendações para pesquisadores e gestores esportivos e para técnicos, psicólogos do esporte e "
       "atletas", ["Pesquisadores e Gestores Esportivos", "Técnicos, Psicólogos do Esporte e Atletas"], lin6r, [8.0, 8.0],
       alinhar=["l", "l"], tam=9)

H1("5. Conclusões")
P("Conclui-se que as evidências científicas sobre os estados de humor em atletas de handebol no treinamento e na "
  "competição são escassas, recentes e predominantemente observacionais. Os principais pontos dos achados são:")
for _b in [f"Os {NE} estudos, publicados entre 2008 e 2026, concentraram-se na Espanha, na Tunísia e no Brasil, com "
           f"amostras pequenas, predominantemente femininas e, em parte, compostas por escolares;",
           f"O POMS e suas versões dominaram a medida, em versões heterogêneas e com momento da medida declarado em "
           f"apenas {QI['q4']['sim']} estudos;",
           "O humor associou-se à carga, sobretudo por meio de dimensões isoladas como a fadiga e o vigor, ao resultado "
           "do jogo, às habilidades psicológicas e ao convívio social, com certeza baixa a muito baixa;",
           "O encorajamento verbal e o feedback modificaram o humor durante a prática, com certeza baixa em escolares e "
           "muito baixa em atletas, e as intervenções nutricionais, psicológicas e musicais não demonstraram efeito "
           "consistente;",
           f"A qualidade foi alta em {QUAL['Alta']} dos {NE} estudos, mas falhas de integridade do relato atravessaram "
           f"todos os níveis de qualidade, e a heterogeneidade impediu a síntese quantitativa."]:
    BUL(_b, marca="•")
P("Com base nas evidências sintetizadas, técnicos e psicólogos do esporte podem priorizar o monitoramento regular do "
  "humor e a comunicação positiva do treinador, e os pesquisadores, medidas repetidas por sessão, momento declarado, "
  "análise por sexo, relato completo e delineamentos experimentais na rotina das equipes.")

# ================================================================== informações finais (padrão MDPI)
for _rot, _txt in [
        ("Materiais Suplementares", "As seguintes informações de apoio constam dos apêndices: Tabela A1: extração "
                                    "dos dados dos estudos incluídos; Tabela B1: relatórios excluídos no texto "
                                    "completo ou não recuperados; Tabela C1: limitações declaradas e fragilidades "
                                    "identificadas na leitura integral."),
        ("Contribuições dos Autores", "[a preencher pelos autores, segundo a taxonomia CRediT]."),
        ("Financiamento", "[a preencher pelos autores]."),
        ("Declaração de Consentimento Informado", "Não se aplica."),
        ("Declaração de Disponibilidade dos Dados", "Os dados extraídos dos estudos incluídos constam dos Apêndices A e C."),
        ("Conflitos de Interesse", "[a confirmar pelos autores].")]:
    P(f"**{_rot}:** {_txt}", primeira=0, tam=9, antes=4, linha=11)
H1("Referências")
for _ref in R.lista():
    par = fmt(doc.add_paragraph(), recuo=False, primeira=-0.6, linha=10.5, depois=2, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY)
    par.paragraph_format.left_indent = Cm(0.6)
    runs(par, _ref, tam=9)

# ================================================================== Apêndice A: extração completa (paisagem)
GER = [("quando", "quando")]


def limpo(v):
    t = "n.r." if v is None or (isinstance(v, float) and v != v) else str(v).strip()
    return re.sub(r"\s+", " ", t.replace(" — ", "; ").replace("—", ", ")).replace("**", "")


SIMB = {"sim": "+", "incerto": "?", "não": "−"}
secao(True)
H1("Apêndice A")
linA = []
for e in sorted(INC, key=lambda e: (NORM[e["id"]][0], e["id"])):
    i = e["id"]
    amostra = (f"n = {e['n'] if isinstance(e['n'], int) else 'n.r.'}; {limpo(e['sexo'])}; {limpo(e['idade'])}; "
               f"{limpo(e['nivel'])}; {limpo(e.get('modalidade', 'quadra'))}")
    delin = f"{limpo(e['delineamento'])}; {limpo(e['contexto'])}. Momento: {limpo(e['momento_medida'])}"
    instr = f"{limpo(e['instrumento_humor'])}. Dimensões: {limpo(e['dimensoes'])}"
    variav = f"{limpo(e['outras_variaveis'])}. Intervenção: {limpo(e['intervencao'])}"
    q = e["qualidade"]
    qtxt = " ".join(SIMB[q[k]] for k in ["q1", "q2", "q3", "q4", "q5", "q6"]) + f"\n{q['pontuacao']}/6"
    linA.append([limpo(R.lista_item(K[i])) if hasattr(R, "lista_item") else R.autor(K[i]), limpo(NORM[i][1]), amostra,
                 delin, instr, variav, limpo(e["resultados_humor"]) + f" Fonte: {limpo(e['fonte'])}.",
                 RD.DIR_CURTA[e["direcao"]], qtxt])
tabela("Quadro A1", "Extração dos dados dos estudos incluídos: identificação, país, amostra, delineamento, contexto e "
                    "momento, instrumento e dimensões, variáveis e intervenção, principais resultados, direção do achado "
                    "e qualidade metodológica",
       ["Estudo", "País", "Amostra", "Delineamento, contexto e momento", "Instrumento e dimensões",
        "Outras variáveis e intervenção", "Principais resultados sobre o humor", "Direção", "Qualidade Q1 a Q6"],
       linA, [2.4, 1.4, 2.8, 3.0, 2.8, 3.0, 6.0, 1.6, 1.7], alinhar=["l", "l", "l", "l", "l", "l", "l", "c", "c"], tam=7,
       quadro=True, larg_max=24.7,
       nota="n.r.: não relatado; qualidade: sim (+), incerto (?), não (−) nos itens Q1 a Q6 descritos na seção 2.4. A "
            "referência completa de cada estudo consta da lista de referências.")
# ================================================================== Apêndice C: relatórios reavaliados e excluídos
secao(True)
H1("Apêndice B")
MOT = {"H1": "Identificado na atualização como resumo de congresso (ISSP, 2001), estudo de caso sem versão aberta; não recuperado",
       "H6": "Identificado na atualização (International Journal of Sport Studies, 2012), sem resumo nem texto aberto; não recuperado",
       "H7": "Mede apenas a raiva estado-traço (STAS), fora do conceito de humor do protocolo",
       "H8": "Humor induzido sem instrumento nomeado; parte da amostra não praticava handebol",
       "H12": "O identificador digital corresponde a estudo sobre estatura e massa corporal, sem medida de humor",
       "H18": "O identificador digital corresponde a estudo sobre habilidades motoras de escolares, sem medida de humor",
       "H26": "Não localizado: sem título, identificador ou periódico verificáveis",
       "H33": "O artigo publicado mede apenas o prazer esportivo; a escala de afeto aparece somente no preprint",
       "H36": "Humor medido por item único de questionário de bem-estar, equivalente ao índice de Hooper",
       "O2": "Escala de distresse de treino sem dimensão de humor relatada no material acessível",
       "N6": "Atualização: preprint sem revisão por pares; excluído pelo critério de somente artigos completos em periódicos",
       "N9": "Atualização: resumo de congresso da amostra de Ratz-Sulyok et al. (2026); excluído pelo critério de somente artigos completos",
       "U107": "Atualização: trabalho completo em anais de congresso; excluído pelo critério de somente artigos em periódicos",
       "N7": "Atualização: afeto medido por 12 adjetivos, sem nome nem validação do instrumento; n do handebol não relatado"}
EXTRA = [  # atualização (outubro de 2026): excluídos no texto completo ou não recuperados
    ["Mubarak (2013)", "MUBARAK, E. J. Special resistance exercises for deception and accuracy of shooting and their impact on the "
     "emotional response of handball players. Modern Sport, v. 12, n. 20, p. 1-38, 2013. DOI: https://doi.org/10.54702/2708-3454.1372",
     "Atualização: o resumo descreve jogadoras de voleibol; resposta emocional sem instrumento nomeado"],
    ["Bauer et al. (2024)", "BAUER, J. et al. Interaction between the leg recovery test and subjective measures of fatigue "
     "in handball players: short-, mid-, and long-term assessment. Frontiers in Sports and Active Living, v. 6, 1474385, 2024. DOI: "
     "https://doi.org/10.3389/fspor.2024.1474385",
     "Atualização: escala curta de recuperação e estresse (KEB), não instrumento de humor"],
    ["Erden e Emirzeoğlu (2020)", "ERDEN, A.; EMIRZEOĞLU, M. Investigation of body awareness level and performance emotional status of "
     "athletes in different branches of sports. Journal of Sport Rehabilitation, v. 29, n. 1, p. 23-27, 2020. DOI: "
     "https://doi.org/10.1123/jsr.2018-0334",
     "Atualização: escala de estado emocional de desempenho (COPES-2), não instrumento de humor"],
    ["Suárez Iglesias et al. (2023)", "SUÁREZ IGLESIAS, D. et al. The impact of COVID-19 on healthy habits and psychological "
     "well-being of Chilean female handball players. E-balonmano.com: Journal of Sports Science, v. 19, n. 1, p. 1-12, 2023. DOI: https://doi.org/10.17398/1885-7019.19.1",
     "Atualização: não recuperado (acesso bloqueado); instrumento de bem-estar não identificável"],
    ["Bougrine et al. (2023)", "BOUGRINE, H. et al. Does Ramadan intermittent fasting affect the intraday variations of "
     "cognitive and high-intensity short-term maximal performances in young female handball players? Biological Rhythm "
     "Research, v. 54, n. 4, p. 399-418, 2023. DOI: https://doi.org/10.1080/09291016.2023.2198794",
     "Atualização: não recuperado (texto sob assinatura e sem resumo); medida de humor não identificável"]]
# segunda rodada da atualização: excluídos no texto completo ou pelo resumo e não recuperados
for r in json.load(open(AQ / "busca2" / "excluidos_texto2.json", encoding="utf-8")):
    EXTRA.append([r["autor_ano"], r["referencia"], "Atualização: " + r["motivo"]])
EXTRA += [
    ["Diachenko e Tyshchenko (2023)", "DIACHENKO, M. V.; TYSHCHENKO, V. O. Characteristics of the mental and emotional state of "
     "female handball players during the preparatory period. Olympicus, n. 3, p. 63-69, 2023. DOI: "
     "https://doi.org/10.24195/olympicus/2023-3.10",
     "Segunda busca de citações: mede o humor (SAN) de handebolistas, mas o texto completo está em ucraniano (idioma fora dos critérios)"],
    ["Dyadechko (2016)", "DYADECHKO, I. Influence of training loads on psychophysiological indicators of handball players in "
     "different phases of the menstrual cycle. Slobozhanskyi Herald of Science and Sport, n. 6, 2016. DOI: "
     "https://doi.org/10.15391/snsv.2016-6.007",
     "Segunda busca de citações: não recuperado (sem resumo e texto bloqueado); medida de humor não verificável"],
    ["Bursik et al. (2024)", "BURSIK, J. et al. Risk profiles for self-medication with analgesics among elite German handball "
     "players. International Review for the Sociology of Sport, 2024. DOI: https://doi.org/10.1177/10126902241280156",
     "Atualização, decisão pelo resumo (texto bloqueado): afetividade negativa como traço, sem escala de humor"],
    ["Klatt et al. (2021)", "KLATT, S. et al. Performance changes and recovery time in U20 and older handball players after "
     "a high-intensity sprint exercise. Applied Sciences, 2021. DOI: https://doi.org/10.3390/app11115301",
     "Atualização, decisão pelo resumo: mede esforço percebido, dor muscular e estresse, sem escala de humor"],
    ["Tese no Dialnet (2023)", "Factores físicos y psicológicos relacionados con la inestabilidad crónica de tobillo en "
     "jugadores de balonmano de categorías inferiores. Tese, 2023. Registro no Dialnet",
     "Atualização, decisão pelo resumo: ansiedade, personalidade, depressão e cinesiofobia, sem escala de humor"],
    ["Abbas, Zeghair e Hasan (2021)", "ABBAS, K. H.; ZEGHAIR, H. O.; HASAN, O. N. Analytical study on the effectiveness of "
     "psychological health among handball players of the premium class. 2021",
     "Atualização: não recuperado; sem resumo, DOI ou texto localizado e sem indicação de instrumento de humor"]]
linB = [[limpo(e["autor_ano"]), limpo(e.get("referencia_abnt", ""))[:260], MOT[e["id"]]]
        for e in RD.EXC] + EXTRA
tabela("Quadro C1", "Relatórios reavaliados no texto completo e excluídos ou não recuperados, com o motivo",
       ["Registro", "Referência recuperada", "Motivo da exclusão"], linB, [3.4, 11.8, 9.5],
       alinhar=["l", "l", "l"], tam=8, quadro=True, larg_max=24.7)

# ================================================================== Apêndice C (ex-D): leitura integral (paisagem)
secao(True)
H1("Apêndice C")
linC = []
for e in sorted(INC, key=lambda e: (NORM[e["id"]][0], e["id"])):
    f = e.get("leitura") or {}
    if e["id"] in RD.MESMA_AMOSTRA and e["id"] != "H32":
        continue
    linC.append([R.autor(K[e["id"]]), limpo(f.get("fonte", "")), limpo(f.get("limitacoes_autores", "n.r.")),
                 limpo(f.get("limitacoes_revisores", ""))])
tabela("Quadro D1", "Limitações declaradas pelos autores e fragilidades identificadas pelos revisores na leitura integral "
                    "de cada estudo",
       ["Estudo", "Fonte lida", "Limitações declaradas pelos autores", "Fragilidades identificadas na leitura"], linC,
       [3.0, 1.8, 7.4, 12.5], alinhar=["l", "l", "l", "l"], tam=7, quadro=True, larg_max=24.7,
       nota="n.r.: os autores não declararam limitações. A fonte lida indica se a leitura se apoiou no texto completo "
            "ou apenas no resumo.")


out = AQ / f"{NOME}.docx"
doc.save(out)
print("gravado", out, "referências:", len(R.ordem))
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(AQ), str(out)], capture_output=True,
               timeout=900)
print(subprocess.run(["pdfinfo", str(AQ / f"{NOME}.pdf")], capture_output=True, text=True).stdout)
