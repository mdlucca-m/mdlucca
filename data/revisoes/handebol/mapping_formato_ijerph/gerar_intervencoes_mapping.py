"""Tabela e texto dos estudos de intervenção da revisão de mapeamento (documentos Word separados).

    python3 gerar_intervencoes_mapping.py   (executar duas vezes: letras de ano repetido nas citações)
"""
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

os.environ["CITE"] = "autor"
os.environ["CITADOS_FILE"] = "citados_intervencoes_mapping.json"
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from refs import R
from intervencoes_detalhe import EST, TIPOS

AQ = Path(__file__).parent
FONTE = "Times New Roman"
ORDEM = sorted(EST, key=lambda n: (TIPOS.index(EST[n]["tipo"]), int(re.search(r"\((\d{4})", R.autor(f"e{n}")).group(1)), n))
AUT = {n: R.autor(f"e{n}").replace(" & ", " e ") for n in ORDEM}
CIT = {n: R.cite(f"e{n}") for n in ORDEM}


def novo_doc(paisagem=False):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONTE, Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    s = doc.sections[0]
    s.page_height, s.page_width = Cm(29.7), Cm(21.0)
    if paisagem:
        s.orientation = WD_ORIENT.LANDSCAPE
        s.page_width, s.page_height = s.page_height, s.page_width
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(1.5)
    else:
        s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3), Cm(2), Cm(3), Cm(2)
    return doc


def par(doc, txt, tam=12, negrito=False, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=True, linha=1.5, antes=0, depois=6):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment, pf.line_spacing, pf.space_before, pf.space_after = alinhar, linha, Pt(antes), Pt(depois)
    if recuo:
        pf.first_line_indent = Cm(1.25)
    for i, parte in enumerate(re.split(r"\*\*", txt)):
        r = p.add_run(parte)
        r.font.name, r.font.size = FONTE, Pt(tam)
        r.bold = negrito or (i % 2 == 1)
    return p


def sombrear(cel, cor="E8ECF2"):
    tcPr = cel._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), cor)
    tcPr.append(sh)


def repetir_cab(linha):
    trPr = linha._tr.get_or_add_trPr()
    e = OxmlElement("w:tblHeader")
    e.set(qn("w:val"), "true")
    trPr.append(e)


def referencias(doc, tam=12):
    par(doc, "**Referências**", alinhar=WD_ALIGN_PARAGRAPH.LEFT, recuo=False, antes=12)
    for t in R.lista():
        p = par(doc, t, tam=tam, alinhar=WD_ALIGN_PARAGRAPH.LEFT, recuo=False, linha=1.0, depois=6)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)


def salvar(doc, nome):
    arq = AQ / f"{nome}.docx"
    doc.save(arq)
    subprocess.run(["soffice", "-env:UserInstallation=file:///tmp/claude-0/-home-user/0bcd0703-6a3e-5492-93df-26f74a3ac8bd/scratchpad/lo_int", "--headless", "--convert-to", "pdf", "--outdir", str(AQ), str(arq)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    print("ok", arq.name)


# ------------------------------------------------------------------ números gerais
DIR = Counter(EST[n]["dir"] for n in ORDEM)
TIP = Counter(EST[n]["tipo"] for n in ORDEM)
ECR = [n for n in ORDEM if EST[n]["mod"].startswith(("Ensaio", "Experimental"))]
QE = [n for n in ORDEM if EST[n]["mod"].startswith("Quase")]
NN = {n: int(re.match(r"(\d+)", EST[n]["n"]).group(1)) for n in ORDEM if re.match(r"\d", EST[n]["n"])}
SEM = {n: int(re.match(r"(\d+) semanas", EST[n]["dur"]).group(1)) for n in ORDEM if re.match(r"\d+ semanas", EST[n]["dur"])}
UNICA = [n for n in ORDEM if EST[n]["dur"].startswith("Sessão única") or EST[n]["dur"].startswith("Sessões únicas")]
import statistics as st_
EXT = {1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
       11: "onze", 12: "doze", 13: "treze", 14: "catorze"}
ext = lambda k: EXT.get(k, str(k))
ROTT = {TIPOS[0]: "treino de habilidades psicológicas", TIPOS[1]: "feedback e ação do treinador",
        TIPOS[2]: "prática de handebol", TIPOS[3]: "recuperação e sono", TIPOS[4]: "nutrição e suplementação",
        TIPOS[5]: "música"}

# ================================================================== 1. tabela
doc = novo_doc(paisagem=True)
par(doc, "**Estudos de intervenção da revisão de mapeamento sobre as variáveis psicológicas no treinamento e na "
         "competição do handebol**", tam=13, alinhar=WD_ALIGN_PARAGRAPH.LEFT, recuo=False, linha=1.15, depois=4)
par(doc, f"A tabela reúne os {len(ORDEM)} estudos que testaram uma intervenção, organizados por tipo de intervenção e "
         f"por ano de publicação. Os resultados foram retirados da extração com citação literal conferida na fonte; "
         f"quando a leitura integral corrigiu a planilha (tamanho da amostra ou delineamento), prevaleceu a leitura "
         f"integral.", tam=10, recuo=False, linha=1.15, depois=8)
cab = ["Autores e ano", "País", "Tipo e descrição da intervenção", "Duração", "População e amostra",
       "Modelo do estudo", "Momentos de medida", "Desfechos e instrumentos", "Principais resultados", "Direção"]
larg = [2.2, 1.6, 3.0, 1.9, 2.6, 2.6, 2.1, 3.2, 5.8, 1.7]
t = doc.add_table(rows=1, cols=len(cab))
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False


def cel(c, txt, tam=7.5, negrito=False):
    c.text = ""
    p = c.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(txt)
    r.font.name, r.font.size, r.bold = FONTE, Pt(tam), negrito


for i, h in enumerate(cab):
    cel(t.rows[0].cells[i], h, 8, True)
    sombrear(t.rows[0].cells[i])
repetir_cab(t.rows[0])
tipo_atual = None
for n in ORDEM:
    e = EST[n]
    if e["tipo"] != tipo_atual:
        tipo_atual = e["tipo"]
        lin = t.add_row().cells
        m = lin[0].merge(lin[-1])
        cel(m, f"{tipo_atual} ({TIP[tipo_atual]} {'estudo' if TIP[tipo_atual] == 1 else 'estudos'})", 8, True)
        sombrear(m, "F4F6F9")
    lin = t.add_row().cells
    vals = [AUT[n], e["pais"], e["desc"], e["dur"], f"{e['pop']}; {e['n']}", e["mod"], e["tempo"], e["desf"],
            e["res"], e["dir"]]
    for i, v in enumerate(vals):
        cel(lin[i], v)
for i, w in enumerate(larg):
    t.columns[i].width = Cm(w)
for row in t.rows:
    for i, tc in enumerate(row._tr.tc_lst):
        if len(row._tr.tc_lst) == len(larg):
            tc.get_or_add_tcPr()
            from docx.table import _Cell
            _Cell(tc, t).width = Cm(larg[i])
_tblPr = t._tbl.tblPr
_lay = OxmlElement("w:tblLayout")
_lay.set(qn("w:type"), "fixed")
_tblPr.append(_lay)
par(doc, "Direção: efeito, efeito ou associação relatada pelos autores; misto, efeito em parte dos desfechos ou "
         "apenas dentro de um grupo; descritivo, sem teste do efeito; não determinável, fonte sem resultados. "
         "PSQI: Índice de Qualidade do Sono de Pittsburgh; POMS: Profile of Mood States; CSAI-2: Competitive State "
         "Anxiety Inventory-2; CBAS: Coaching Behavior Assessment System; SMS-28: Sport Motivation Scale; WBQ: "
         "Well-Being Questionnaire; PRS: Perceived Recovery Status; SART: Sustained Attention to Response Task; EEG: "
         "eletroencefalograma; η²: tamanho do efeito; g: tamanho do efeito de Hedges.", tam=8.5, recuo=False,
    linha=1.0, antes=4)
referencias(doc, tam=9)
salvar(doc, "TABELA ESTUDOS DE INTERVENCAO MAPPING")

# ================================================================== 2. texto
R2 = R
doc = novo_doc()
par(doc, "**Resultados dos estudos de intervenção da revisão de mapeamento sobre as variáveis psicológicas no "
         "treinamento e na competição do handebol**", tam=13, alinhar=WD_ALIGN_PARAGRAPH.CENTER, recuo=False,
    linha=1.15, depois=12)
dist = sorted(TIP.items(), key=lambda kv: (-kv[1], TIPOS.index(kv[0])))
txt_tip = ", ".join(f"{ROTT[k]} ({v})" for k, v in dist[:-1]) + f" e {ROTT[dist[-1][0]]} ({dist[-1][1]})"
par(doc, f"Dos 199 estudos incluídos na revisão de mapeamento, {len(ORDEM)} testaram uma intervenção. Os tipos de "
         f"intervenção foram {txt_tip}. Quanto ao modelo, {ext(len(ECR))} estudos foram ensaios ou experimentos "
         f"controlados, com distribuição aleatória dos participantes ou com todas as condições aplicadas aos mesmos "
         f"participantes, e {ext(len(QE))} foram quase-experimentais, parte deles sem grupo controle. A duração, "
         f"informada em semanas em {ext(len(SEM))} estudos, variou de {min(SEM.values())} a {max(SEM.values())} "
         f"semanas, e {ext(len(UNICA))} intervenções ocorreram em sessão única. As amostras, relatadas em "
         f"{len(NN)} estudos, variaram de {min(NN.values())} a {max(NN.values())} participantes, com mediana de "
         f"{st_.median(NN.values()):.0f}, e {sum(1 for v in NN.values() if v < 30)} estudos reuniram menos de 30 "
         f"participantes.")
par(doc, f"Quanto à direção dos achados, {ext(DIR['Efeito'])} estudos relataram efeito ou associação, "
         f"{ext(DIR['Misto'])} relataram resultados mistos, isto é, efeito em parte dos desfechos ou apenas dentro de "
         f"um grupo, {ext(DIR['Descritivo'])} foi apenas descritivo e {ext(DIR['Não determinável'])} não tiveram "
         f"resultados acessíveis. Três estudos mediram apenas o desempenho técnico, sem desfecho psicológico "
         f"{R.cite('e81', 'e145', 'e179')}. Os resultados de cada estudo são apresentados a seguir, por tipo de "
         f"intervenção e em ordem cronológica, com o tipo e a duração da intervenção, a população, a amostra, o modelo "
         f"do estudo, os momentos de medida, os desfechos e os resultados.")

PREP = {"Espanha": "na Espanha", "Irã": "no Irã", "Brasil": "no Brasil", "Dinamarca": "na Dinamarca",
        "Iraque": "no Iraque", "França": "na França", "Japão": "no Japão", "Arábia Saudita": "na Arábia Saudita",
        "Turquia": "na Turquia", "Tunísia": "na Tunísia", "Tchéquia": "na Tchéquia",
        "Bósnia e Herzegovina": "na Bósnia e Herzegovina", "Espanha e México": "na Espanha e no México",
        "Índia": "na Índia", "Portugal": "em Portugal", "Bélgica e outros países": "na Bélgica e em outros países"}
VERBOS = ["testaram", "avaliaram", "investigaram", "examinaram", "analisaram", "compararam"]
DUR = {2: "A intervenção foi aplicada ao longo de nove jogos de competição, após cinco jogos de linha de base",
       111: "A duração da intervenção não foi relatada",
       119: "A duração não foi relatada, pois o feedback foi uma manipulação experimental pontual",
       132: "A intervenção ocorreu durante o Ramadã, período de cerca de quatro semanas",
       145: "A intervenção foi aplicada uma única vez, segundo o objetivo do estudo",
       192: "Cada modalidade foi praticada em uma sessão, dividida em três períodos",
       174: "A intervenção durou 5 semanas, com uso diário",
       196: "A intervenção durou 8 semanas, com três sessões semanais"}
TEMPO = {2: "O rendimento foi registrado em cada jogo da linha de base e do tratamento",
         111: "Os momentos de medida não foram relatados",
         174: "A recuperação percebida foi registrada diariamente, com testes antes e depois das 5 semanas"}


ART = {"Programa": "um", "Feedback": "o", "Aquecimento": "o", "Suplementação": "a", "Handebol": "o", "Treino": "o",
       "Imersão": "a", "Cochilos": "os", "Prática": "a", "Treinos": "os", "Ingestão": "a", "Intervenção": "uma",
       "Ensino": "o", "Compressão": "a", "Imagética": "a", "Relaxamento": "o"}


def artigo(s):
    return f"{ART[s.split()[0]]} {minus(s)}"


def minus(s):
    return s[0].lower() + s[1:] if not re.match(r"[A-Z]{2}", s) else s


for k, tipo in enumerate(TIPOS):
    ids = [n for n in ORDEM if EST[n]["tipo"] == tipo]
    par(doc, f"**{k + 1}. {tipo}**", alinhar=WD_ALIGN_PARAGRAPH.LEFT, recuo=False, antes=10)
    for j, n in enumerate(ids):
        e = EST[n]
        v = VERBOS[(j + k) % len(VERBOS)]
        if v == "compararam":
            v = "testaram"
        if n in DUR:
            dur = DUR[n]
        elif e["dur"].startswith("Não relatada"):
            dur = "A duração da intervenção não foi relatada"
        elif e["dur"].startswith("Sessão única"):
            dur = "A intervenção ocorreu em sessão única" + e["dur"][len("Sessão única"):]
        else:
            dur = f"A intervenção durou {e['dur']}"
        tempo = TEMPO.get(n, f"As medidas ocorreram {minus(e['tempo'])}")
        amostra = "com amostra não relatada" if e["n"].startswith("Não") else f"com {e['n']}"
        amostra = "a amostra não foi relatada" if e["n"].startswith("Não") else f"a amostra reuniu {e['n']}"
        par(doc, f"{AUT[n]} {v} {artigo(e['desc'])}. O estudo foi realizado {PREP[e['pais']]}, com "
                 f"{minus(e['pop'])}, e {amostra}. O modelo foi {minus(e['mod'])}. {dur}. {tempo}, e os desfechos "
                 f"avaliados foram: {minus(e['desf'])}. {e['res']}")
    d = Counter(EST[n]["dir"] for n in ids)
    if len(ids) > 1:
        partes = []
        for chave, rot in [("Efeito", "efeito ou associação"), ("Misto", "resultados mistos"),
                           ("Descritivo", "apenas descrição"), ("Não determinável", "resultados não acessíveis")]:
            if d[chave]:
                partes.append(f"{ext(d[chave])} com {rot}")
        frase = ", ".join(partes[:-1]) + (" e " if len(partes) > 1 else "") + partes[-1]
        par(doc, f"Em síntese, entre os {ext(len(ids))} estudos de {ROTT[tipo]}, houve {frase}.")

par(doc, "**Síntese**", alinhar=WD_ALIGN_PARAGRAPH.LEFT, recuo=False, antes=10)
par(doc, f"O conjunto das intervenções mostra que o treino de habilidades psicológicas foi o tipo mais testado e o que "
         f"reuniu a maior parte dos efeitos relatados, sobretudo nos programas de mindfulness, de relaxamento com "
         f"imagética e de imagética com autodiálogo {R.cite('e153', 'e196', 'e199', 'e179')}. As intervenções de feedback "
         f"e de ação do treinador modificaram a ansiedade, o afeto e a motivação, mas os efeitos dependeram do tipo de "
         f"feedback e da satisfação com o treinador {R.cite('e16', 'e94', 'e119', 'e171')}. A prática de handebol "
         f"recreativo aumentou a motivação e a diversão {R.cite('e61', 'e192')}, e as intervenções de recuperação, sono, "
         f"nutrição e música tiveram efeitos sobre parte dos desfechos {R.cite('e89', 'e107', 'e174', 'e57', 'e50')}, e, no "
         f"estudo da cafeína, a piora do sono foi associada às fases do Ramadã, e não à suplementação {R.cite('e132')}. "
         f"As principais limitações foram as amostras pequenas, a ausência de grupo controle ou de distribuição "
         f"aleatória em parte dos estudos, a duração não relatada em vários protocolos e a variedade de desfechos e "
         f"instrumentos, que dificulta a comparação entre os estudos.")
referencias(doc)
salvar(doc, "TEXTO RESULTADOS ESTUDOS DE INTERVENCAO MAPPING")
