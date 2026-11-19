"""Remove da Figura 3 os selos de certeza da evidência e a legenda de triangulação e corrige o alerta de ansiedade."""
import sys
from PIL import Image, ImageDraw, ImageFont
im = Image.open(sys.argv[1]).convert("RGB"); px = im.load()
S = 2
def apaga(x0, y0, x1, y1, modo, off=6):
    x0, y0, x1, y1 = [v * S for v in (x0, y0, x1, y1)]
    for y in range(y0, y1):
        for x in range(x0, x1):
            if modo == "dir": px[x, y] = px[x1 + off, y]
            elif modo == "esq": px[x, y] = px[x0 - off, y]
            elif modo == "baixo": px[x, y] = px[x, y1 + off]
            elif modo == "cima": px[x, y] = px[x, y0 - off]
            else: px[x, y] = modo
apaga(908, 414, 1090, 458, "dir")
# selo verde: fundo da elipse (centro 390,485; semieixos 240,350) e reconstrução da linha do burnout e do círculo 14
tinta_v = px[500 * S, 700 * S]
for y in range(634 * S, 681 * S):
    for x in range(406 * S, 658 * S):
        if (x - 380 * S) ** 2 + (y - 662 * S) ** 2 <= (31 * S + 2) ** 2:
            continue
        dentro = x / S <= 606 - (y / S - 634) * 9 / 56
        px[x, y] = tinta_v if dentro else (255, 255, 255)
cor_linha = px[440 * S, 693 * S]
ImageDraw.Draw(im).line([(445 * S, 683 * S), (466 * S, 632 * S)], fill=cor_linha, width=5)
cx, cy, r = 380 * S, 662 * S, 31 * S
for y in range(cy - r - 4, cy + r + 4):
    for x in range(410 * S, cx + r + 6):
        if (x - cx) ** 2 + (y - cy) ** 2 <= (r + 2) ** 2:
            px[x, y] = px[2 * cx - x, y]
apaga(1376, 634, 1558, 681, "baixo")
apaga(671, 971, 903, 1018, "baixo")
tinta_t = px[1300 * S, 1025 * S]
for y in range(971 * S, 1018 * S):
    for x in range(1139 * S, 1392 * S):
        dentro = ((x / S - 1293) / 218) ** 2 + ((y / S - 893) / 140) ** 2 <= 1
        px[x, y] = tinta_t if dentro else (255, 255, 255)
apaga(478, 1200, 775, 1243, "esq")
apaga(1315, 1200, 1975, 1243, "esq")
apaga(745, 1130, 1300, 1170, "esq")
d = ImageDraw.Draw(im)
f = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 46)
d.text((750 * S, 1150 * S), "Ansiedade: 72 estudos e só 4 intervenções", font=f, fill=(30, 30, 30), anchor="lm")
im.save(sys.argv[2])
