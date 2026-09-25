#!/usr/bin/env python3
"""Fichas de treino do ELASE, em PDF — feitas para IMPRIMIR.

Preto no branco, colunas vazias para a carga de cada série, e as instruções na
própria folha em vez de na cabeça de quem entrega. O atleta lê isto sozinho, de
pé, entre séries.

Um gerador só para todas as fichas: o desenho fica em um lugar, e cada sessão é
só o conteúdo. Duplicar o layout faria a segunda ficha divergir da primeira na
primeira correção que eu fizesse em uma e esquecesse na outra.

    python3 fichas_treino.py            # gera todas
    python3 fichas_treino.py potencia   # gera uma
"""

import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

PASTA = "/home/user/mdlucca/docs/"

AZUL = colors.HexColor("#1F4E79")
AZUL_CLARO = colors.HexColor("#E8F0F8")
VERDE = colors.HexColor("#2E7D32")
VERDE_CLARO = colors.HexColor("#E3F2E3")
AMBAR = colors.HexColor("#C88A1E")
AMBAR_CLARO = colors.HexColor("#FFF6E5")
CINZA = colors.HexColor("#5A6672")
LINHA = colors.HexColor("#B9C2CC")
LINHA_FORTE = colors.HexColor("#7E8A96")

MARGEM = 16 * mm
LARGURA = A4[0] - 2 * MARGEM
TOTAL_PAGINAS = [0]


def est(nome, **kw):
    base = dict(fontName="Helvetica", fontSize=9.5, leading=12.5,
                textColor=colors.black, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(nome, **base)


TITULO = est("t", fontName="Helvetica-Bold", fontSize=20, leading=22, spaceAfter=2)
MARCA = est("m", fontName="Helvetica-Bold", fontSize=8, leading=10,
            textColor=AZUL, spaceAfter=3)
SUB = est("s", fontSize=10, leading=13, textColor=CINZA)
H = est("h", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
        textColor=AZUL, spaceBefore=9, spaceAfter=4)
P = est("p", fontSize=9.5, leading=13)
PQ = est("pq", fontSize=8.2, leading=10.6, textColor=CINZA)
CEL = est("cel", fontSize=9.5, leading=11.5)
CEL_B = est("celb", fontName="Helvetica-Bold", fontSize=10, leading=12)
CEL_PQ = est("celpq", fontSize=7.6, leading=9, textColor=CINZA)
CAB = est("cab", fontName="Helvetica-Bold", fontSize=7.6, leading=9,
          textColor=colors.white)


# ── Peças ───────────────────────────────────────────────────────────────────
def tabela(dados, larguras, extra=None, altura=None):
    t = Table(dados, colWidths=larguras, rowHeights=altura)
    base = [
        ("GRID", (0, 0), (-1, -1), 0.6, LINHA),
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    t.setStyle(TableStyle(base + (extra or [])))
    return t


def caixa(texto, fundo=AZUL_CLARO, borda=AZUL):
    t = Table([[Paragraph(texto, P)]], colWidths=[LARGURA])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fundo),
        ("BOX", (0, 0), (-1, -1), 0.8, borda),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(MARGEM, 10 * mm,
                      "ELASE Voleibol Masculino · Adulto  |  Preparação física")
    total = TOTAL_PAGINAS[0]
    canvas.drawRightString(A4[0] - MARGEM, 10 * mm,
                           "Página %d de %d" % (doc.page, total) if total
                           else "Página %d" % doc.page)
    canvas.setStrokeColor(LINHA)
    canvas.setLineWidth(0.5)
    canvas.line(MARGEM, 13 * mm, A4[0] - MARGEM, 13 * mm)
    canvas.restoreState()


def cabecalho(h, titulo, subtitulo=None):
    h.append(Paragraph("ELASE VOLEIBOL MASCULINO &nbsp;&middot;&nbsp; ADULTO", MARCA))
    h.append(Paragraph(titulo, TITULO))
    if subtitulo:
        h.append(Paragraph(subtitulo, SUB))


def campos_identificacao():
    t = Table([[Paragraph("<b>Atleta</b>", CEL_PQ), "",
                Paragraph("<b>Data</b>", CEL_PQ), "",
                Paragraph("<b>Duração</b>", CEL_PQ), ""]],
              colWidths=[38, 190, 30, 90, 44, LARGURA - 392], rowHeights=[20])
    t.setStyle(TableStyle([
        ("LINEBELOW", (1, 0), (1, 0), 0.8, LINHA_FORTE),
        ("LINEBELOW", (3, 0), (3, 0), 0.8, LINHA_FORTE),
        ("LINEBELOW", (5, 0), (5, 0), 0.8, LINHA_FORTE),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def tabela_sessao(exercicios, rotulo_carga):
    """A tabela principal. Séries, reps e pausa vêm POR EXERCÍCIO: num treino de
    potência eles mudam de linha para linha, e uniformizar seria mentir."""
    cab = [Paragraph("EXERCÍCIO", CAB), Paragraph("SÉRIES", CAB),
           Paragraph("PAUSA", CAB), Paragraph(rotulo_carga, CAB),
           Paragraph("1ª", CAB), Paragraph("2ª", CAB),
           Paragraph("3ª", CAB), Paragraph("4ª", CAB)]
    dados = [cab]
    for i, (nome, padrao, serie, pausa, carga) in enumerate(exercicios, 1):
        dados.append([
            Paragraph("<b>%d. %s</b><br/><font size=7.6 color='#5A6672'>%s</font>"
                      % (i, nome, padrao), CEL),
            Paragraph("<b>%s</b>" % serie, CEL_B), Paragraph(pausa, CEL),
            Paragraph("<b>%s</b>" % carga, CEL), "", "", "", ""])
    # Altura AUTOMÁTICA nas linhas do corpo. Fixar em 30pt só era seguro
    # enquanto os nomes coubessem numa linha: nesta sessão eles são mais longos,
    # e o texto passou por cima da linha de baixo. O respiro mínimo vem do
    # padding, que dá altura de sobra para escrever a carga à mão.
    return tabela(dados, [206, 44, 38, 40, 47.75, 47.75, 47.75, 47.75], [
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (4, 1), (-1, -1), colors.HexColor("#FAFBFC")),
        ("LINEAFTER", (3, 0), (3, -1), 1.1, LINHA_FORTE),
        ("ROWBACKGROUNDS", (0, 1), (3, -1),
         [colors.white, colors.HexColor("#F4F7FA")]),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ], altura=[16] + [None] * len(exercicios))


def campo_anotacao():
    t = Table([[Paragraph("<b>Como foi</b> (dor, sono, algo diferente)", CEL_PQ)],
               [""], [""]], colWidths=[LARGURA], rowHeights=[13, 19, 19])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 1), (0, -1), 0.6, LINHA),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    return t


DEPOIS_DO_TREINO = (
    "Mande a sua <b>PSE</b> — o quanto a sessão pesou, de 0 a 10 — e a duração. "
    "É com esses dois números que a comissão calcula a sua carga da semana e "
    "enxerga se você está sendo sobrecarregado antes de o corpo avisar. "
    "Um treino que ninguém registra é um treino que não existe na sua análise.")


# ── Montagem ────────────────────────────────────────────────────────────────
def montar(f):
    h = []
    cabecalho(h, f["titulo"], f["protocolo"])
    h.append(Spacer(1, 7))
    h.append(campos_identificacao())
    h.append(Spacer(1, 8))
    h.append(caixa(f["abertura"]))
    h.append(Spacer(1, 10))

    h.append(Paragraph(f["aquecimento_titulo"], H))
    h.append(Paragraph(f["aquecimento_nota"], PQ))
    h.append(Spacer(1, 4))
    dados = [[Paragraph(c, CAB) for c in f["aquecimento_cab"]]]
    for linha in f["aquecimento"]:
        dados.append([Paragraph(x, CEL) for x in linha])
    h.append(tabela(dados, [LARGURA * 0.56, LARGURA * 0.22, LARGURA * 0.22],
                    [("ROWBACKGROUNDS", (0, 1), (-1, -1),
                      [colors.white, colors.HexColor("#F4F7FA")])]))
    h.append(Spacer(1, 11))

    h.append(Paragraph("A sessão — anote o que você usou em cada série", H))
    h.append(tabela_sessao(f["exercicios"], f["rotulo_carga"]))
    h.append(Spacer(1, 7))
    h.append(Paragraph(f["nota_tabela"], PQ))
    h.append(Spacer(1, 8))
    h.append(caixa(f["caixa_duracao"], fundo=AMBAR_CLARO, borda=AMBAR))

    h.append(PageBreak())

    cabecalho(h, f["titulo_verso"])
    h.append(Spacer(1, 10))
    for bloco in f["verso"]:
        if bloco[0] == "h":
            h.append(Paragraph(bloco[1], H))
        elif bloco[0] == "p":
            h.append(Paragraph(bloco[1], P))
        elif bloco[0] == "pq":
            h.append(Paragraph(bloco[1], PQ))
        elif bloco[0] == "espaco":
            h.append(Spacer(1, bloco[1]))
        elif bloco[0] == "caixa":
            h.append(caixa(bloco[1], *(bloco[2:] or [])))
        elif bloco[0] == "passos":
            for i, passo in enumerate(bloco[1], 1):
                h.append(Paragraph(
                    "<b>%d.</b> &nbsp;%s" % (i, passo),
                    est("passo", fontSize=9.5, leading=13, leftIndent=14,
                        firstLineIndent=-14, spaceAfter=4)))
        elif bloco[0] == "notas":
            for nome, texto in bloco[1]:
                h.append(KeepTogether([Paragraph(
                    "<b>%s.</b> %s" % (nome, texto),
                    est("nota", fontSize=9, leading=12, leftIndent=8, spaceAfter=6))]))
        elif bloco[0] == "tabela":
            dados = [[Paragraph(c, CAB) for c in bloco[1]]]
            for linha in bloco[2]:
                dados.append([Paragraph(linha[0], CEL),
                              Paragraph("<b>%s</b>" % linha[1], CEL),
                              Paragraph(linha[2], CEL_PQ)])
            h.append(tabela(dados,
                            [LARGURA * 0.38, LARGURA * 0.22, LARGURA * 0.40],
                            bloco[3] if len(bloco) > 3 else None))

    h.append(Paragraph("Depois do treino", H))
    h.append(Paragraph(DEPOIS_DO_TREINO, P))
    h.append(Spacer(1, 10))
    h.append(campo_anotacao())
    return h


def gerar(f):
    caminho = PASTA + f["arquivo"]

    def construir():
        doc = BaseDocTemplate(caminho, pagesize=A4,
                              leftMargin=MARGEM, rightMargin=MARGEM,
                              topMargin=14 * mm, bottomMargin=18 * mm,
                              title=f["meta_titulo"],
                              author="ELASE Voleibol - Preparacao fisica",
                              subject=f["meta_assunto"])
        quadro = Frame(MARGEM, 18 * mm, LARGURA, A4[1] - 32 * mm, id="q")
        doc.addPageTemplates([PageTemplate(id="pad", frames=[quadro], onPage=rodape)])
        doc.build(montar(f))

    # Duas passagens: a primeira só para SABER quantas páginas saíram. Prometer
    # "Página 1 de 2" numa folha de 3 é o tipo de detalhe que faz o resto
    # parecer descuidado — e foi exatamente o que aconteceu na primeira ficha.
    TOTAL_PAGINAS[0] = 0
    construir()
    import pypdfium2
    TOTAL_PAGINAS[0] = len(pypdfium2.PdfDocument(caminho))
    construir()
    print("gerado: %s (%d páginas)" % (caminho, TOTAL_PAGINAS[0]))
    return caminho
