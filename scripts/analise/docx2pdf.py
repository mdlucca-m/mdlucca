# -*- coding: utf-8 -*-
# Converte o .docx do artigo em PDF, relendo o próprio documento (texto,
# formatação, tabelas e figuras) e reemitindo com reportlab. Preserva a
# estrutura e a formatação ABNT (Times, 1,5, margens 3/3/2/2, recuo de parágrafo).
import io, sys
from docx import Document
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape

SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/user/mdlucca/Artigos/Artigo_humor_HANDEBOL.docx'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/home/user/mdlucca/Artigos/Artigo_humor_HANDEBOL.pdf'
doc = Document(SRC)

FONT = 'Times-Roman'; FONTB = 'Times-Bold'
def style(name, size=12, align=TA_JUSTIFY, bold=False, indent=0, sb=0, sa=6, lead=None):
    return ParagraphStyle(name, fontName=FONTB if bold else FONT, fontSize=size,
        leading=lead or size*1.5, alignment=align, firstLineIndent=indent,
        spaceBefore=sb, spaceAfter=sa)

S_TITLE = style('title', 13, TA_CENTER, bold=True, sa=10)
S_H     = style('h', 12, TA_LEFT, bold=True, sb=10, sa=4)
S_BODY  = style('body', 12, TA_JUSTIFY, indent=1.25*cm, sa=6)
S_BODY0 = style('body0', 12, TA_JUSTIFY, indent=0, sa=6)
S_CAPT  = style('capt', 11, TA_LEFT, sa=2, sb=8)
S_CAPTC = style('captc', 11, TA_CENTER, sa=2)
S_SRC   = style('src', 9, TA_LEFT, sa=6)
S_SRCC  = style('srcc', 9, TA_CENTER, sa=6)
S_NOTE  = style('note', 8.5, TA_LEFT, sa=0)
S_CELL  = style('cell', 9, TA_LEFT, lead=11, sa=0)
S_CELLC = style('cellc', 9, TA_CENTER, lead=11, sa=0)
S_CELLH = style('cellh', 9, TA_CENTER, bold=True, lead=11, sa=0)

def san(t):
    """Substitui caracteres sem glifo na fonte Times padrão do PDF."""
    return (t or '').replace('ₚ', 'p')   # subscrito ₚ (η²ₚ) -> p

def runs_to_html(p):
    """Converte os 'runs' do parágrafo em texto com <b>...</b> preservando negrito."""
    out = []
    for r in p.runs:
        t = escape(san(r.text or ''))
        if not t:
            continue
        if r.bold:
            t = '<b>%s</b>' % t
        out.append(t)
    return ''.join(out)

def emu_to_pt(v):
    return int(v) / 914400.0 * 72.0

def para_images(p):
    """Extrai (blob, largura_pt) de cada imagem embutida no parágrafo, na ordem."""
    imgs = []
    for dr in p._p.findall('.//' + qn('w:drawing')):
        blip = dr.find('.//' + qn('a:blip'))
        ext = dr.find('.//' + qn('wp:extent'))
        if blip is None:
            continue
        rid = blip.get(qn('r:embed'))
        blob = doc.part.related_parts[rid].blob
        w = emu_to_pt(ext.get('cx')) if ext is not None else 400
        imgs.append((blob, w))
    return imgs

def build_table(tbl):
    """Constrói uma tabela reportlab a partir de uma tabela do docx (1ª linha = cabeçalho)."""
    data = []
    for ri, row in enumerate(tbl.rows):
        cells = []
        for cell in row.cells:
            txt = escape(san(cell.text or ''))
            st = S_CELLH if ri == 0 else (S_CELLC if _is_num(cell.text) else S_CELL)
            cells.append(Paragraph(txt, st))
        data.append(cells)
    ncol = len(data[0])
    avail = A4[0] - 3*cm - 2*cm
    # 1ª coluna mais larga (rótulos), demais iguais
    w0 = avail * (0.30 if ncol > 2 else 0.5)
    rest = (avail - w0) / (ncol - 1) if ncol > 1 else avail
    colw = [w0] + [rest] * (ncol - 1)
    t = Table(data, colWidths=colw, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEABOVE', (0,0), (-1,0), 0.8, colors.black),
        ('LINEBELOW', (0,0), (-1,0), 0.8, colors.black),
        ('LINEBELOW', (0,-1), (-1,-1), 0.8, colors.black),
    ]))
    return t

def _is_num(s):
    s = (s or '').strip().replace('*','').replace('±','').replace('%','')
    s = s.replace(',', '.').replace('–','-').split()[0] if s.split() else s
    try:
        float(s.replace('(','').replace(')','')); return True
    except: return False

# ---- percorre o corpo do documento na ordem original ----
story = []
body = doc.element.body
from docx.text.paragraph import Paragraph as DPar
from docx.table import Table as DTab
first_title_done = False
for child in body.iterchildren():
    if child.tag == qn('w:p'):
        p = DPar(child, doc)
        text = p.text.strip()
        imgs = para_images(p)
        # imagens (figuras)
        for blob, w in imgs:
            try:
                img = Image(io.BytesIO(blob))
                maxw = A4[0] - 3*cm - 2*cm
                w = min(w, maxw)
                ratio = img.imageHeight / float(img.imageWidth)
                img.drawWidth = w; img.drawHeight = w * ratio
                story.append(Spacer(1, 6)); story.append(img)
            except Exception:
                pass
        if not text:
            continue
        al = p.alignment
        html = runs_to_html(p) or escape(san(text))
        # heurística de estilo
        allbold = all((r.bold or not (r.text or '').strip()) for r in p.runs) and any((r.text or '').strip() for r in p.runs)
        if al == AL.CENTER and allbold and not first_title_done:
            story.append(Paragraph(html, S_TITLE)); first_title_done = True
        elif text.startswith(('Tabela ', 'Figura ')):
            story.append(Paragraph(html, S_CAPT if text.startswith('Tabela ') else S_CAPTC))
        elif text.startswith('Fonte:'):
            story.append(Paragraph(html, S_SRC if 'pesquisa' in text else S_SRCC))
        elif allbold:
            story.append(Paragraph(html, S_H))
        elif al == AL.CENTER:
            story.append(Paragraph(html, S_CAPTC))
        else:
            indent = p.paragraph_format.first_line_indent
            story.append(Paragraph(html, S_BODY if (indent and indent > 0) else S_BODY0))
    elif child.tag == qn('w:tbl'):
        tbl = DTab(child, doc)
        story.append(Spacer(1, 4))
        story.append(build_table(tbl))

pdf = SimpleDocTemplate(OUT, pagesize=A4,
    topMargin=3*cm, leftMargin=3*cm, rightMargin=2*cm, bottomMargin=2*cm,
    title='Perfil de humor de atletas de handebol de elite')
pdf.build(story)
print('SALVO', OUT)
