#!/usr/bin/env python3
"""Ficha de treino de força pura — 4 x 4, carga submáxima.

Feita para ser IMPRESSA e escrita à mão na sala: preto no branco, colunas
vazias para a carga de cada série, e as instruções na própria folha em vez de
na cabeça de quem entrega. O atleta vai ler isto sozinho, de pé, entre séries.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

SAIDA = "/home/user/mdlucca/docs/ELASE-treino-forca-pura.pdf"

AZUL = colors.HexColor("#1F4E79")
AZUL_CLARO = colors.HexColor("#E8F0F8")
CINZA = colors.HexColor("#5A6672")
LINHA = colors.HexColor("#B9C2CC")
LINHA_FORTE = colors.HexColor("#7E8A96")

MARGEM = 16 * mm
LARGURA = A4[0] - 2 * MARGEM


def est(nome, **kw):
    base = dict(fontName="Helvetica", fontSize=9.5, leading=12.5,
                textColor=colors.black, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(nome, **base)


TITULO = est("t", fontName="Helvetica-Bold", fontSize=20, leading=22,
             textColor=colors.black, spaceAfter=2)
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

# ── O treino ────────────────────────────────────────────────────────────────
# Cinco exercícios vieram pedidos. Os dois acrescentados fecham os padrões que
# faltavam: PUXAR HORIZONTAL e DOBRA DE QUADRIL. Sem eles, a sessão teria duas
# séries de empurrar para cada uma de puxar, e num atleta que ataca centenas de
# bolas por semana esse desequilíbrio escapular cobra caro.
EXERCICIOS = [
    ("Agachamento livre", "joelho — o mais neural, por isso vem primeiro", "85%"),
    ("Supino reto com barra", "empurrar horizontal", "85%"),
    ("Levantamento terra", "dobra de quadril — ACRESCENTADO", "80%"),
    ("Puxador frente (pegada aberta)", "puxar vertical", "85%"),
    ("Desenvolvimento com barra", "empurrar vertical", "85%"),
    ("Remada curvada com barra", "puxar horizontal — ACRESCENTADO", "85%"),
    ("Remada alta", "ombro e trapézio — ver a nota do verso", "80%"),
]

AQUECIMENTO = [
    ("Barra vazia", "1 \u00d7 8", "solta"),
    ("50% da carga de trabalho", "1 \u00d7 5", "1 min"),
    ("65% da carga de trabalho", "1 \u00d7 3", "1 min"),
    ("75% da carga de trabalho", "1 \u00d7 2", "2 min"),
]

PCT_RIR = [
    ("Sobrariam mais 3 repetições", "cerca de 80%", "leve para força pura"),
    ("Sobrariam mais 2 repetições", "cerca de 85%", "É AQUI que a sessão deve ficar"),
    ("Sobraria mais 1 repetição", "cerca de 88%", "pesado — só se o dia estiver bom"),
    ("Não sobraria nenhuma", "cerca de 91%", "falha técnica — não é submáxima"),
]

NOTAS = [
    ("Remada alta", "É o exercício de maior risco desta ficha para quem ataca. "
     "Pegada na largura dos ombros ou mais ABERTA, e o cotovelo não passa da "
     "linha do ombro. Se der dor ou pinçamento na frente do ombro, pare e troque "
     "por elevação lateral ou face pull — a perda de treino é zero e o ombro é "
     "o que te mantém em quadra."),
    ("Levantamento terra", "Vem depois do agachamento, então a lombar já chega "
     "cansada. Por isso ele está a 80% e não a 85%. Se a sessão estiver pesando, "
     "ele é o PRIMEIRO a reduzir — não o agachamento."),
    ("Supino", "Escápulas presas no banco e pés firmes no chão. Barra descendo "
     "até o peito com controle; quem quica a barra no peito treina outra coisa."),
    ("Desenvolvimento com barra", "Em pé, glúteo e abdômen apertados. A barra "
     "passa perto do rosto. Se a lombar arqueia para a barra subir, a carga está "
     "alta demais."),
    ("Agachamento", "Profundidade até onde o quadril desce SEM a lombar "
     "arredondar. Quem não desce por falta de tornozelo tem problema de "
     "mobilidade, não de força — e isso se resolve no aquecimento."),
]


def linha_tabela(dados, larguras, estilo_extra=None, altura=None):
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
    if estilo_extra:
        base += estilo_extra
    t.setStyle(TableStyle(base))
    return t


def caixa(texto, cor_fundo=AZUL_CLARO, cor_borda=AZUL):
    t = Table([[Paragraph(texto, P)]], colWidths=[LARGURA])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), cor_fundo),
        ("BOX", (0, 0), (-1, -1), 0.8, cor_borda),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


TOTAL_PAGINAS = [0]        # preenchido pela primeira passagem


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(MARGEM, 10 * mm,
                      "ELASE Voleibol Masculino \u00b7 Adulto  |  Preparação física")
    total = TOTAL_PAGINAS[0]
    canvas.drawRightString(A4[0] - MARGEM, 10 * mm,
                           "Página %d de %d" % (doc.page, total) if total
                           else "Página %d" % doc.page)
    canvas.setStrokeColor(LINHA)
    canvas.setLineWidth(0.5)
    canvas.line(MARGEM, 13 * mm, A4[0] - MARGEM, 13 * mm)
    canvas.restoreState()


def construir():
    doc = BaseDocTemplate(SAIDA, pagesize=A4,
                          leftMargin=MARGEM, rightMargin=MARGEM,
                          topMargin=14 * mm, bottomMargin=18 * mm,
                          title="ELASE - Treino de forca pura",
                          author="ELASE Voleibol - Preparacao fisica",
                          subject="Forca pura 4x4 com carga submaxima")
    quadro = Frame(MARGEM, 18 * mm, LARGURA, A4[1] - 14 * mm - 18 * mm, id="q")
    doc.addPageTemplates([PageTemplate(id="pad", frames=[quadro], onPage=rodape)])

    h = []

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    h.append(Paragraph("ELASE VOLEIBOL MASCULINO &nbsp;&middot;&nbsp; ADULTO", MARCA))
    h.append(Paragraph("Treino de força pura", TITULO))
    h.append(Paragraph("4 séries &times; 4 repetições &nbsp;&middot;&nbsp; "
                       "2 minutos entre séries &nbsp;&middot;&nbsp; carga submáxima", SUB))
    h.append(Spacer(1, 8))

    ident = Table([[Paragraph("<b>Atleta</b>", CEL_PQ), "",
                    Paragraph("<b>Data</b>", CEL_PQ), "",
                    Paragraph("<b>Duração</b>", CEL_PQ), ""]],
                  colWidths=[38, 190, 30, 90, 44, LARGURA - 392], rowHeights=[20])
    ident.setStyle(TableStyle([
        ("LINEBELOW", (1, 0), (1, 0), 0.8, LINHA_FORTE),
        ("LINEBELOW", (3, 0), (3, 0), 0.8, LINHA_FORTE),
        ("LINEBELOW", (5, 0), (5, 0), 0.8, LINHA_FORTE),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    h.append(ident)
    h.append(Spacer(1, 10))

    h.append(caixa(
        "<b>O que é carga submáxima.</b> É a carga com que você faz as 4 "
        "repetições e ainda <b>sobrariam 2</b> — cerca de 85% do seu máximo. "
        "Força pura não se treina indo até a falha: se a quarta repetição sai "
        "arrastando, a carga está alta demais e o treino virou outra coisa. "
        "Na dúvida, <b>fique leve</b>: o verso explica como achar a carga sem "
        "saber o seu 1RM."))
    h.append(Spacer(1, 12))

    # ── Aquecimento ────────────────────────────────────────────────────────
    h.append(Paragraph("Aquecimento — antes do primeiro exercício de cada padrão", H))
    h.append(Paragraph(
        "Quatro séries a 85% sem rampa é lesão esperando acontecer. Estas séries "
        "não contam como treino e não devem cansar.", PQ))
    h.append(Spacer(1, 4))
    dados = [[Paragraph("CARGA", CAB), Paragraph("SÉRIES", CAB), Paragraph("PAUSA", CAB)]]
    for carga, ser, pausa in AQUECIMENTO:
        dados.append([Paragraph(carga, CEL), Paragraph(ser, CEL), Paragraph(pausa, CEL)])
    h.append(linha_tabela(dados, [LARGURA * 0.56, LARGURA * 0.22, LARGURA * 0.22],
                          [("ROWBACKGROUNDS", (0, 1), (-1, -1),
                            [colors.white, colors.HexColor("#F4F7FA")])]))
    h.append(Spacer(1, 14))

    # ── A sessão ───────────────────────────────────────────────────────────
    h.append(Paragraph("A sessão — anote a carga de cada série", H))
    cab = [Paragraph("EXERCÍCIO", CAB), Paragraph("SÉRIES", CAB),
           Paragraph("PAUSA", CAB), Paragraph("% 1RM", CAB),
           Paragraph("1ª", CAB), Paragraph("2ª", CAB),
           Paragraph("3ª", CAB), Paragraph("4ª", CAB)]
    dados = [cab]
    for i, (nome, padrao, pct) in enumerate(EXERCICIOS, 1):
        dados.append([
            Paragraph("<b>%d. %s</b><br/><font size=7.6 color='#5A6672'>%s</font>"
                      % (i, nome, padrao), CEL),
            Paragraph("4 &times; 4", CEL_B), Paragraph("2 min", CEL),
            Paragraph("<b>%s</b>" % pct, CEL), "", "", "", ""])
    larg = [178, 46, 40, 40, 53.75, 53.75, 53.75, 53.75]
    t = linha_tabela(dados, larg, [
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (4, 1), (-1, -1), colors.HexColor("#FAFBFC")),
        ("LINEAFTER", (3, 0), (3, -1), 1.1, LINHA_FORTE),
        ("ROWBACKGROUNDS", (0, 1), (3, -1),
         [colors.white, colors.HexColor("#F4F7FA")]),
    ], altura=[16] + [30] * len(EXERCICIOS))
    h.append(t)
    h.append(Spacer(1, 7))
    h.append(Paragraph(
        "As colunas da direita são para você escrever a carga que <b>realmente</b> "
        "usou em cada série, em quilos. É esse número que vira a sua referência no "
        "próximo ciclo — sem ele, o treino da semana que vem repete o desta.", PQ))
    h.append(Spacer(1, 10))
    h.append(caixa(
        "<b>Duração prevista: 75 a 85 minutos</b> com o aquecimento. Se estiver "
        "muito mais rápido, a pausa de 2 minutos não está sendo respeitada — e a "
        "pausa é parte da prescrição, não um intervalo para conversa. É ela que "
        "permite a série seguinte sair com a mesma qualidade.",
        cor_fundo=colors.HexColor("#FFF6E5"), cor_borda=colors.HexColor("#C88A1E")))

    h.append(PageBreak())

    # ── Página 2 ───────────────────────────────────────────────────────────
    h.append(Paragraph("ELASE VOLEIBOL MASCULINO &nbsp;&middot;&nbsp; ADULTO", MARCA))
    h.append(Paragraph("Como usar esta ficha", TITULO))
    h.append(Spacer(1, 10))

    h.append(Paragraph("Achar a carga sem saber o seu 1RM", H))
    h.append(Paragraph(
        "Ninguém precisa ter feito teste de máximo para treinar hoje. Faça assim, "
        "no primeiro exercício:", P))
    h.append(Spacer(1, 5))
    passos = [
        "Depois do aquecimento, escolha uma carga que <b>pareça</b> dar para 6 "
        "repetições boas.",
        "Faça <b>4</b>. Se no fim da quarta você sentiu que ainda faria mais 2 com "
        "técnica limpa, é essa a carga. Mantenha nas quatro séries.",
        "Se sobraria mais de 2, <b>suba</b> de 5 em 5 kg na série seguinte. Se "
        "sobraria menos de 2, <b>desça</b>.",
        "Anote. Na semana que vem você começa daí, e não do zero.",
    ]
    for i, passo in enumerate(passos, 1):
        h.append(Paragraph("<b>%d.</b> &nbsp;%s" % (i, passo),
                           est("passo", fontSize=9.5, leading=13,
                               leftIndent=14, firstLineIndent=-14, spaceAfter=4)))
    h.append(Spacer(1, 8))

    dados = [[Paragraph("O QUE VOCÊ SENTE NO FIM DA 4ª", CAB),
              Paragraph("EQUIVALE A", CAB), Paragraph("LEITURA", CAB)]]
    for sente, pct, leitura in PCT_RIR:
        dados.append([Paragraph(sente, CEL), Paragraph("<b>%s</b>" % pct, CEL),
                      Paragraph(leitura, CEL_PQ)])
    h.append(linha_tabela(dados, [LARGURA * 0.38, LARGURA * 0.22, LARGURA * 0.40], [
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#E3F2E3")),
        ("BOX", (0, 2), (-1, 2), 1.1, colors.HexColor("#2E7D32")),
    ]))
    h.append(Spacer(1, 6))
    h.append(Paragraph(
        "Estes percentuais são orientação, não medida: o mesmo 85% rende diferente "
        "num dia de sono ruim. Quem manda é o que você sente na barra, e a regra "
        "de sobrar 2 repetições vale acima do número da tabela.", PQ))
    h.append(Spacer(1, 12))

    h.append(Paragraph("Execução — o que muda o resultado", H))
    for nome, texto in NOTAS:
        h.append(KeepTogether([Paragraph(
            "<b>%s.</b> %s" % (nome, texto),
            est("nota", fontSize=9, leading=12, leftIndent=8, spaceAfter=6))]))
    h.append(Spacer(1, 6))

    h.append(caixa(
        "<b>Por que dois exercícios a mais do que os cinco pedidos.</b> "
        "Supino e desenvolvimento são empurrar; puxador é puxar vertical; "
        "remada alta é ombro. Faltavam <b>puxar horizontal</b> (remada curvada) e "
        "<b>dobra de quadril</b> (levantamento terra). Sem eles a sessão teria duas "
        "séries de empurrar para cada uma de puxar, e num atleta que ataca centenas "
        "de bolas por semana esse desequilíbrio escapular cobra caro. "
        "Se precisar cortar para seis, corte a <b>remada alta</b> — é a que tem mais "
        "risco e menos transferência."))
    h.append(Spacer(1, 12))

    h.append(Paragraph("Depois do treino", H))
    h.append(Paragraph(
        "Mande a sua <b>PSE</b> — o quanto a sessão pesou, de 0 a 10 — e a duração. "
        "É com esses dois números que a comissão calcula a sua carga da semana e "
        "enxerga se você está sendo sobrecarregado antes de o corpo avisar. "
        "Um treino que ninguém registra é um treino que não existe na sua análise.", P))
    h.append(Spacer(1, 10))

    anot = Table([[Paragraph("<b>Como foi</b> (dor, sono, algo diferente)", CEL_PQ)],
                  [""], [""]],
                 colWidths=[LARGURA], rowHeights=[13, 19, 19])
    anot.setStyle(TableStyle([
        ("LINEBELOW", (0, 1), (0, -1), 0.6, LINHA),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    h.append(anot)

    doc.build(h)


def main():
    """Duas passagens: a primeira só para SABER quantas páginas saíram.

    O rodapé promete "Página 1 de 2", e prometer o número errado numa folha que
    vai para a mão do atleta é o tipo de detalhe que faz o resto parecer
    descuidado. Da primeira vez ele diz "de 3" — e eu tinha escrito 2 na mão.
    """
    TOTAL_PAGINAS[0] = 0
    construir()
    import pypdfium2
    TOTAL_PAGINAS[0] = len(pypdfium2.PdfDocument(SAIDA))
    construir()
    print("gerado: %s (%d páginas)" % (SAIDA, TOTAL_PAGINAS[0]))


if __name__ == "__main__":
    main()
