"""Convite de defesa e dossiê para a banca: motivação autodeterminada de atletas adolescentes de handebol.

    python3 gerar_banca.py <apA.json> <pasta_saida>

apA.json: Quadro A1 (extração dos 199 estudos) lido do MAPPING REVIEW revisado.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

APA, OUT = Path(sys.argv[1]), Path(sys.argv[2])
R = {r["Nº"]: r for r in json.load(open(APA, encoding="utf-8"))}
FONTE = "Times New Roman"

TITULO = "Motivação autodeterminada de atletas adolescentes de handebol: uma revisão sistemática"
DATA, HORA, LOCAL = "17 de novembro de 2026 (terça-feira)", "11h", "Auditório"
BANCA = [("Orientador", "Prof. Dr. Alexandro Andrade"), ("Coorientador", "Prof. Mestrando Henrique Oliveira"),
         ("Membro", "Prof. Ms. Mateus De Luca"), ("Membro", "Prof. Ms. Thiago Caescaes")]
CANDIDATO = "[nome do(a) candidato(a)]"

# ------------------------------------------------------------------ estudos
NUCLEO = {"5": "Guillet et al. (2002)", "6": "Sarrazin et al. (2002)", "14": "Oliva et al. (2010)",
          "20": "Li et al. (2011)", "21": "Lukwu e Guzmán (2011)", "22": "Lukwu (2011)",
          "23": "Autoria a conferir* (2012)", "53": "Martínez-Moreno e Alfonso (2017)", "70": "Alesi et al. (2019)",
          "79": "Gómez-López et al. (2019)", "99": "Gómez-López, Courel-Ibáñez e Granero-Gallegos (2021)",
          "118": "Freire et al. (2023)", "149": "Gómez-López et al. (2024)", "160": "Bugten et al. (2025a)",
          "171": "Malfa et al. (2025)", "185": "Bugten et al. (2025b)", "184": "Bugten et al. (2026)",
          "196": "Saket et al. (2026)"}
RELAC = {"7": "Rascle e Coulomb (2003)", "8": "Guillet et al. (2006)", "9": "Li e Chi (2007)",
         "12": "Miguel et al. (2009)", "26": "Isoard-Gautheur, Guillet-Descas e Duda (2012)",
         "36": "De Backer et al. (2015)", "49": "Granero-Gallegos et al. (2017)", "55": "Ruiz-Sánchez et al. (2017)",
         "60": "Gómez-López et al. (2018)", "80": "Gómez-López, Ruiz-Sánchez e Granero-Gallegos (2019)",
         "87": "Gómez-López et al. (2020)", "100": "Gómez-López, González-Hernández e Granero-Gallegos (2021)",
         "104": "Gómez-López et al.* (2021)", "105": "Gómez-López et al.* (2021)",
         "125": "Kristjánsdóttir, Matthíasdóttir e Saavedra (2021)", "128": "Sánchez-Sáez et al. (2022)",
         "137": "Karacsony e Krupanszki (2023)", "164": "Coutinho et al. (2025)",
         "187": "Greblo Jurakić, Bojić-Ćaćić e Ljubičić (2026)"}
QUAL = {"171": "Moderada (EPHPP): confusão controlada, perdas não relatadas",
        "196": "Moderada (EPHPP): diferenças iniciais sem ajuste; inconsistências entre texto e tabelas"}

# ================================================================== convite (imagem e documento)
plt.rcParams["font.family"] = "Liberation Serif"
fig = plt.figure(figsize=(10.8, 13.5), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")
ax.add_patch(plt.Rectangle((0, 0), 1, 1, color="#F6F3EC", transform=ax.transAxes))
ax.add_patch(plt.Rectangle((0, 0.84), 1, 0.16, color="#1F3B57", transform=ax.transAxes))
ax.text(0.5, 0.935, "CONVITE", ha="center", va="center", color="white", fontsize=44, fontweight="bold")
ax.text(0.5, 0.875, "Defesa pública de trabalho acadêmico", ha="center", va="center", color="#DCE6F0", fontsize=22)
ax.text(0.5, 0.75, "MOTIVAÇÃO AUTODETERMINADA DE ATLETAS\nADOLESCENTES DE HANDEBOL:\nUMA REVISÃO SISTEMÁTICA",
        ha="center", va="center", color="#1F3B57", fontsize=30, fontweight="bold", linespacing=1.35)
ax.text(0.5, 0.635, CANDIDATO, ha="center", va="center", color="#333333", fontsize=22, style="italic")
ax.plot([0.2, 0.8], [0.585, 0.585], color="#C8A24A", lw=2.5)
ax.text(0.5, 0.545, "BANCA EXAMINADORA", ha="center", va="center", color="#1F3B57", fontsize=20, fontweight="bold")
for i, (papel, nome) in enumerate(BANCA):
    ax.text(0.5, 0.49 - i * 0.05, f"{nome}  ({papel.lower()})", ha="center", va="center", color="#222222",
            fontsize=20)
ax.plot([0.2, 0.8], [0.27, 0.27], color="#C8A24A", lw=2.5)
for i, (rot, val) in enumerate([("Data", "17 de novembro de 2026, terça-feira"), ("Horário", "11h"),
                                ("Local", LOCAL)]):
    ax.text(0.33, 0.22 - i * 0.055, rot, ha="right", va="center", color="#1F3B57", fontsize=22, fontweight="bold")
    ax.text(0.36, 0.22 - i * 0.055, val, ha="left", va="center", color="#222222", fontsize=22)
ax.text(0.5, 0.045, "Laboratório de Psicologia do Esporte e do Exercício (Lape)", ha="center", va="center",
        color="#1F3B57", fontsize=17)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
fig.savefig(OUT / "convite_defesa_motivacao.png", dpi=100)
plt.close(fig)


def fmt(p, tam=12, neg=False, ita=False, cor=None):
    for r in p.runs:
        r.font.name, r.font.size, r.bold, r.italic = FONTE, Pt(tam), neg, ita
        if cor:
            r.font.color.rgb = RGBColor.from_string(cor)
    return p


def par(doc, txt, tam=12, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=True, antes=0, depois=6, linha=1.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment, pf.line_spacing, pf.space_before, pf.space_after = alinhar, linha, Pt(antes), Pt(depois)
    if recuo:
        pf.first_line_indent = Cm(1.25)
    for i, parte in enumerate(re.split(r"\*\*", txt)):
        r = p.add_run(parte)
        r.font.name, r.font.size, r.bold = FONTE, Pt(tam), bool(i % 2)
    return p


def novo_doc():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONTE, Pt(12)
    s = doc.sections[0]
    s.page_height, s.page_width = Cm(29.7), Cm(21.0)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(3), Cm(2), Cm(3), Cm(2)
    return doc


def pdf(arq):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT), str(arq)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)


doc = novo_doc()
doc.add_picture(str(OUT / "convite_defesa_motivacao.png"), width=Cm(15.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.save(OUT / "CONVITE DEFESA MOTIVACAO.docx")
pdf(OUT / "CONVITE DEFESA MOTIVACAO.docx")

# ================================================================== dossiê
doc = novo_doc()
par(doc, "**DOSSIÊ PARA A BANCA**", 16, WD_ALIGN_PARAGRAPH.CENTER, False, depois=4)
par(doc, f"**{TITULO}**", 13, WD_ALIGN_PARAGRAPH.CENTER, False, depois=10, linha=1.15)
par(doc, f"Defesa: {DATA}, às {HORA}, no {LOCAL}. Banca: " +
    "; ".join(f"{n} ({p.lower()})" for p, n in BANCA) + ".", 11, WD_ALIGN_PARAGRAPH.CENTER, False, depois=14,
    linha=1.15)


def h(txt):
    par(doc, f"**{txt}**", 12, WD_ALIGN_PARAGRAPH.LEFT, False, antes=10, depois=4)


def bul(txt):
    p = par(doc, "•  " + txt, 12, recuo=False, depois=3)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.first_line_indent = Cm(-0.4)


h("1. Origem das informações")
par(doc, "Este dossiê reúne o que a base do grupo já contém sobre motivação autodeterminada em atletas adolescentes de "
    "handebol. A fonte é a revisão de mapeamento sobre variáveis psicológicas no treinamento e na competição do "
    "handebol, com 199 estudos identificados em oito bases de dados (Crossref, Europe PMC, LILACS, OpenAlex, PubMed, "
    "SciELO, Scopus e Web of Science), sem restrição de data e com publicações até setembro de 2026. Cada resultado da "
    "extração está vinculado a um trecho literal da fonte, e os estudos de intervenção tiveram leitura integral "
    "adicional e avaliação da qualidade pelo EPHPP em novembro de 2026.")
par(doc, "Dos 199 estudos, 68 mediram variáveis motivacionais e 48 deles avaliaram amostras juvenis ou infantis. Desses "
    "48, foram separados dois grupos: (a) **18 estudos centrais**, que mediram construções da teoria da "
    "autodeterminação, como motivação intrínseca, regulações, amotivação, índice de autodeterminação, necessidades "
    "psicológicas básicas e apoio à autonomia ou estilo controlador do treinador (Quadro 1); e (b) **19 estudos "
    "relacionados**, sobre clima motivacional, orientações de meta, competência percebida e motivos de participação, "
    "que costumam aparecer em revisões sobre o tema (Quadro 2). Os demais tratavam de outras variáveis com menção "
    "secundária à motivação. O texto do trabalho em defesa não foi lido; o dossiê serve de referência para a "
    "comparação com o que a revisão em defesa incluiu.")

h("2. Panorama dos 18 estudos centrais")
for b in ["Publicados entre 2002 e 2026; mais da metade (10) a partir de 2019, com um núcleo recente de estudos noruegueses com "
          "medidas diárias (Bugten et al., 2025a, 2025b, 2026).",
          "Pelo país de afiliação dos autores, Espanha com 8 estudos, Noruega com 3, França e Brasil com 2 cada (Lukwu e "
          "Guzmán, 2011, e Freire et al., 2023) e Taiwan, Itália e Tunísia com 1 cada.",
          "Amostras exclusivamente femininas em 6 estudos, mistas em 6 e sem informação de sexo em 6.",
          "Delineamentos: 5 coortes ou longitudinais, 5 transversais, 6 observacionais sem desenho especificado e 2 "
          "quase-experimentais; nenhum ensaio randomizado em adolescentes.",
          "Soma de 5.174 participantes, mas com provável repetição de amostras: o mesmo número de participantes (479) e a "
          "mesma equipe de autores aparecem em três estudos centrais (Alesi et al., 2019; Gómez-López et al., 2019, 2021) e em dois relacionados (Ruiz-Sánchez "
          "et al., 2017; Gómez-López et al., 2020); 302 jogadores aparecem em Lukwu e Guzmán (2011) e Lukwu (2011); e 50 "
          "jogadoras, em Bugten et al. (2025b, 2026). Descontadas as repetições, restam cerca de 3,9 mil participantes "
          "distintos.",
          "Direção dos achados: efeito ou associação em 15 estudos, resultados mistos em 2 e descrição em 1."]:
    bul(b)

h("3. O que os estudos mostram")
par(doc, "**Motivação, persistência e abandono.** Nas coortes francesas, as jogadoras que abandonaram o handebol tinham, "
    "21 meses antes, menos motivação intrínseca e mais amotivação que as persistentes, além de menor percepção de "
    "competência, autonomia e pertencimento; a baixa motivação autodeterminada associou-se à intenção de abandonar, e "
    "esta predisse o abandono real (Sarrazin et al., 2002). As que abandonaram também se percebiam menos competentes, "
    "autônomas e apoiadas pelo treinador (Guillet et al., 2002). Em 302 jogadores, o clima de maestria e o "
    "compromisso esportivo distinguiram os que permaneceram no esporte (Lukwu e Guzmán, 2011).")
par(doc, "**A sequência clima, necessidades e motivação.** Os modelos estruturais sustentam a sequência proposta pela "
    "teoria: o clima orientado à tarefa ou à maestria prediz a satisfação das necessidades psicológicas básicas, que "
    "prediz o índice de autodeterminação, e este prediz desfechos como o compromisso (Alesi et al., 2019) e a "
    "deportividade (Lukwu, 2011). O clima orientado ao ego não predisse as necessidades (Alesi et al., 2019).")
par(doc, "**Estilo do treinador e experiência diária.** Nos estudos com medidas a cada treino, o apoio do treinador às "
    "necessidades associou-se a mais prazer, e a frustração das necessidades, a menos prazer; das necessidades, só a "
    "competência associou-se ao prazer (Bugten et al., 2025b). O uso controlador de recompensas aumentou o risco de "
    "faltar ao treino seguinte (Bugten et al., 2025a), e a satisfação das necessidades associou-se ao prazer e à "
    "carga física da sessão (Bugten et al., 2026). No Brasil, a relação de alta qualidade entre treinador e atleta "
    "associou-se a mais regulações autônomas e a mais coesão (Freire et al., 2023).")
par(doc, "**Perfis motivacionais.** Os jogadores espanhóis apresentaram perfil predominantemente autodeterminado "
    "(Martínez-Moreno e Alfonso, 2017). As análises de agrupamento reuniram, de um lado, motivação autodeterminada, "
    "autoconfiança e clima de maestria e, de outro, amotivação, motivação extrínseca, medo do fracasso, maior ansiedade "
    "e clima de desempenho (Gómez-López et al., 2019, 2021). A orientação ao ego relacionou-se à motivação extrínseca "
    "e à amotivação (estudo de 2012 com autoria a conferir), e as metas de aproximação à maestria predisseram a "
    "motivação intrínseca (Li et al., 2011). A autonomia e a motivação intrínseca associaram-se a condutas de "
    "deportividade, e a regulação externa, à crítica negativa (Oliva et al., 2010).")
par(doc, "**Intervenções.** Apenas dois estudos testaram intervenções com desfecho motivacional em adolescentes, ambos "
    "quase-experimentais e de qualidade moderada pelo EPHPP. O relaxamento progressivo com imagética, em 8 semanas, "
    "aumentou a motivação intrínseca para realização e para estimulação de jogadoras cadetes tunisianas (Saket et al., "
    "2026), mas o artigo apresenta diferenças iniciais entre os grupos e divergências entre texto e tabelas. O ensino "
    "pelo modelo ludocompreensivo, em 17 sessões, aumentou o apoio à autonomia percebido, mas reduziu a motivação "
    "autônoma, o índice de autodeterminação e a satisfação de relação no grupo experimental (Malfa et al., 2025). O "
    "ensaio dinamarquês com handebol recreativo e aumento da motivação intrínseca (Hornstrup et al., 2018) avaliou "
    "mulheres de 20 a 30 anos, e não adolescentes, embora a base o classifique como juvenil.")

h("4. Instrumentos encontrados")
for b in ["Sport Motivation Scale (SMS ou SMS-28): Li et al. (2011), estudo de 2012, Gómez-López et al. (2019, 2021), "
          "Alesi et al. (2019), Oliva et al. (2010) e Saket et al. (2026); SMS-II: Freire et al. (2023).",
          "Behavioral Regulation in Sport Questionnaire (BRSQ): Martínez-Moreno e Alfonso (2017).",
          "BREQ-2, questionário de regulação no exercício físico, aplicado ao handebol: Malfa et al. (2025).",
          "Necessidades psicológicas básicas: BPNES (Alesi et al., 2019), escala de necessidades na educação física "
          "(Malfa et al., 2025) e medidas breves por sessão (Bugten et al., 2025b, 2026).",
          "Índice de autodeterminação calculado a partir das regulações: Lukwu (2011), Lukwu e Guzmán (2011), Alesi et "
          "al. (2019) e Malfa et al. (2025).",
          "Clima motivacional (PMCSQ-2) e clima entre pares (PeerMCYSQ), presentes nos estudos que combinam a teoria "
          "da autodeterminação com a teoria das metas de realização."]:
    bul(b)

h("5. Pontos de atenção para a arguição")
for b in ["**Definição de adolescente e de atleta.** Verificar a faixa etária adotada (por exemplo, 10 a 19 anos) e se "
          "foram incluídos escolares, praticantes amadores e categorias de formação; Li et al. (2011) e Freire et al. "
          "(2023) avaliaram escolares.",
          "**Fronteira teórica.** Verificar se a revisão separou os estudos da teoria da autodeterminação dos estudos "
          "sobre clima motivacional e orientações de meta, que pertencem à teoria das metas de realização e aparecem "
          "misturados na literatura do handebol.",
          "**Amostras repetidas.** Conferir se o grupo de 479 jogadores espanhóis, o de 302 jogadores e o de 50 "
          "jogadoras norueguesas foram tratados como uma única amostra, para não inflar o número de participantes nem "
          "a consistência dos achados.",
          "**Instrumentos.** Discutir a equivalência entre SMS, SMS-II, BRSQ e BREQ-2, este último construído para o "
          "exercício físico, e o uso do índice de autodeterminação no lugar das regulações separadas.",
          "**Delineamento e qualidade.** Predominam estudos transversais ou sem desenho especificado; perguntar qual "
          "ferramenta de qualidade foi usada para os estudos observacionais e como a qualidade entrou na síntese.",
          "**Intervenções.** Só há duas intervenções com desfecho motivacional em adolescentes, ambas não "
          "randomizadas e com resultados que exigem cautela; verificar se a revisão as interpretou com essa ressalva.",
          "**Cobertura da busca.** Estudos recentes com medidas diárias (Bugten et al., 2025a, 2025b, 2026) e o estudo "
          "brasileiro de Freire et al. (2023) são bons testes da atualidade da busca.",
          "**Lacunas.** Nenhum estudo central com amostra exclusivamente masculina, poucos fora da Europa, nenhum "
          "ensaio randomizado e nenhuma intervenção conduzida pelo treinador com desfecho de motivação autodeterminada "
          "em adolescentes."]:
    bul(b)

h("6. Perguntas sugeridas")
for i, q in enumerate([
        "Qual pergunta de pesquisa e qual estratégia PICO ou PECOS orientaram a revisão, e por que a faixa etária "
        "escolhida representa a adolescência no handebol?",
        "Quais bases foram consultadas, até que data, e por que estudos como os de Bugten et al. (2025, 2026) e Freire "
        "et al. (2023) entraram ou não entraram?",
        "Como foram tratados os estudos que mediram apenas o clima motivacional ou as orientações de meta?",
        "Como a revisão lidou com os artigos que usam a mesma amostra de 479 jogadores espanhóis?",
        "Qual instrumento de avaliação da qualidade foi usado e como ele foi adaptado aos estudos transversais?",
        "Que conclusão prática a revisão permite para o treinador de categorias de base, se a evidência "
        "é quase toda observacional?",
        "Que estudo experimental a revisão recomenda, com qual população, intervenção, desfecho e duração?",
        "Como os achados sobre abandono esportivo (Sarrazin et al., 2002; Guillet et al., 2002) se aplicam ao "
        "contexto brasileiro?"], 1):
    bul(f"{i}. {q}")

par(doc, "* Registro incompleto na base; a autoria precisa ser conferida na fonte original.", 10, recuo=False,
    antes=8)

# quadros em paisagem
sec = doc.add_section()
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2)


def quadro(titulo, ids, rotulos, extra=False):
    par(doc, f"**{titulo}**", 11, WD_ALIGN_PARAGRAPH.LEFT, False, antes=6, depois=4, linha=1.15)
    cab = ["Estudo", "País", "Amostra", "Delineamento e contexto", "Variáveis e medidas", "Principais resultados"]
    if extra:
        cab.append("Qualidade (intervenções)")
    larg = [3.2, 2.0, 2.8, 2.8, 5.2, 9.7] if not extra else [3.0, 1.8, 2.6, 2.6, 4.6, 8.2, 2.9]
    t = doc.add_table(rows=1, cols=len(cab))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    def cel(c, txt, neg=False):
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(txt)
        r.font.name, r.font.size, r.bold = FONTE, Pt(8), neg

    for i, x in enumerate(cab):
        cel(t.rows[0].cells[i], x, True)
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear")
        sh.set(qn("w:fill"), "E8ECF2")
        t.rows[0].cells[i]._tc.get_or_add_tcPr().append(sh)
    tr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    tr.append(th)
    for n in ids:
        r = R[n]
        vals = [rotulos[n], r["País"], r["Amostra"], r["Delineamento e contexto"], r["Variáveis e medidas"],
                r["Principais resultados"]]
        if extra:
            vals.append(QUAL.get(n, "Não se aplica"))
        lin = t.add_row().cells
        for i, v in enumerate(vals):
            cel(lin[i], v)
    for i, w in enumerate(larg):
        t.columns[i].width = Cm(w)
    for row in t.rows:
        for i, w in enumerate(larg):
            row.cells[i].width = Cm(w)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(lay)
    par(doc, "Fonte: extração da revisão de mapeamento (Quadro A1), com resultados vinculados ao trecho literal da "
        "fonte. s.i.: sem informação; n.r.: não relatado.", 9, recuo=False, antes=4, linha=1.0)


ordem = lambda d: sorted(d, key=lambda n: (re.search(r"\((\d{4})", d[n]).group(1), d[n]))
quadro("Quadro 1: Estudos centrais sobre motivação autodeterminada em atletas adolescentes de handebol (n = 18)",
       ordem(NUCLEO), NUCLEO, extra=True)
doc.add_page_break()
quadro("Quadro 2: Estudos relacionados: clima motivacional, orientações de meta, competência percebida e motivos de "
       "participação em atletas jovens de handebol (n = 19)", ordem(RELAC), RELAC)
doc.save(OUT / "DOSSIE BANCA MOTIVACAO AUTODETERMINADA.docx")
pdf(OUT / "DOSSIE BANCA MOTIVACAO AUTODETERMINADA.docx")
print("ok")
