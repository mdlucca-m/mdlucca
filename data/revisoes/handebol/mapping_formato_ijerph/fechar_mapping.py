"""Fechamento do mapping review: Figuras 3 e 7, Tomar e Allen (2021) e conferência dos números.

    python3 fechar_mapping.py <entrada.docx> <pasta_figuras> <saida.docx>

A pasta de figuras deve conter figura3_mapa_tematico.png, figura7a_delineamentos.png e figura7b_mapa_intervencoes.png.
"""
import copy
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ENT, FIG, SAI = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
d = Document(ENT)
body = d.element.body
W = qn("w:p")


def paragrafos():
    return list(body.iter(W))


def texto(p):
    return "".join(t.text or "" for t in p.iter(qn("w:t")))


def troca_em(p, a, b):
    """Troca a por b no parágrafo, preservando a formatação da primeira run atingida."""
    ts = list(p.iter(qn("w:t")))
    full = "".join(t.text or "" for t in ts)
    i = full.find(a)
    if i < 0:
        return False
    pos = 0
    ini = fim = None
    for k, t in enumerate(ts):
        n = len(t.text or "")
        if ini is None and i < pos + n:
            ini, off_ini = k, i - pos
        if ini is not None and i + len(a) <= pos + n:
            fim, off_fim = k, i + len(a) - pos
            break
        pos += n
    if ini == fim:
        s = ts[ini].text
        ts[ini].text = s[:off_ini] + b + s[off_fim:]
    else:
        ts[ini].text = ts[ini].text[:off_ini] + b
        for k in range(ini + 1, fim):
            ts[k].text = ""
        ts[fim].text = ts[fim].text[off_fim:]
    for t in (ts[ini], ts[fim]):
        t.set(qn("xml:space"), "preserve")
    return True


def troca(a, b, n=1):
    feitos = 0
    for p in paragrafos():
        while a in texto(p) and feitos < n + 5:
            assert troca_em(p, a, b)
            feitos += 1
    assert feitos == n, (a, feitos)


def troca_par(inicio, novo):
    """Substitui todo o texto do parágrafo que começa com `inicio`."""
    ach = [p for p in paragrafos() if texto(p).startswith(inicio)]
    assert len(ach) == 1, (inicio, len(ach))
    troca_em(ach[0], texto(ach[0]), novo)


def troca_celula(rotulo, ordem, novo):
    """Na linha da tabela cuja primeira célula é `rotulo`, troca o texto da célula de índice `ordem`."""
    feitos = 0
    for tbl in body.iter(qn("w:tbl")):
        for tr in tbl.iter(qn("w:tr")):
            tcs = tr.findall(qn("w:tc"))
            if tcs and texto(tcs[0]).strip() == rotulo:
                ps = list(tcs[ordem].iter(W))
                for extra in ps[1:]:
                    extra.getparent().remove(extra)
                troca_em(ps[0], texto(ps[0]), novo) if texto(ps[0]) else None
                feitos += 1
    return feitos


# ---------------- figuras
def parte_da_imagem(nome):
    for rel in d.part.rels.values():
        if "image" in rel.reltype and rel.target_part.partname.endswith(nome):
            return rel.target_part
    raise KeyError(nome)


parte_da_imagem("/image3.png")._blob = (FIG / "figura3_mapa_tematico.png").read_bytes()
p7a, p7b = parte_da_imagem("/image14.png"), parte_da_imagem("/image15.png")
p7a._blob = (FIG / "figura7a_delineamentos.png").read_bytes()
p7b._blob = (FIG / "figura7b_mapa_intervencoes.png").read_bytes()

# a Figura 7 passa de duas imagens lado a lado para duas imagens empilhadas, na largura do texto
tab7 = None
for tbl in body.iter(qn("w:tbl")):
    if len(tbl.xpath(".//a:blip")) == 2:
        tab7 = tbl
assert tab7 is not None
LARG = 5760000
for tc, (lw, lh) in zip(tab7.iter(qn("w:tc")), [(2000, 1120), (2400, 1480)]):
    pdraw = [p for p in tc.iter(W) if p.xpath(".//a:blip")][0]
    novo_p = copy.deepcopy(pdraw)
    for ext in novo_p.xpath(".//wp:extent") + novo_p.xpath(".//a:xfrm/a:ext"):
        ext.set("cx", str(LARG))
        ext.set("cy", str(int(LARG * lh / lw)))
    tab7.addprevious(novo_p)
tab7.getparent().remove(tab7)

troca_par("Nota: (A) distribuição dos estudos por delineamento; (B)",
          "Nota: (A) distribuição dos 199 estudos por delineamento, segundo a extração (Quadro A1); (B) mapa de "
          "evidências das 24 intervenções, tipo de intervenção × domínio do desfecho psicológico: o número indica os "
          "estudos de cada combinação, e um estudo pode contar em mais de um domínio; o verde mais escuro indica maior "
          "proporção de estudos com efeito; a borda preta indica que a combinação inclui ensaio com distribuição "
          "aleatória; o zero em vermelho indica combinação sem estudo. A última linha reúne as intervenções que "
          "avaliaram apenas o desempenho.")
troca("setas: tendência temporal (limiar de 2 p.p.); faixas: certeza da evidência; quadros vermelhos: principais lacunas.",
      "setas: tendência temporal (limiar de 2 p.p.); quadros vermelhos: principais lacunas.")

# ---------------- delineamentos dos 199 estudos (Quadro A1)
troca("Apenas 27 estudos adotaram delineamento experimental, e 24 testaram intervenções; 12 relataram efeito",
      "Apenas 28 estudos adotaram delineamento experimental, e 24 testaram intervenções; 13 relataram efeito")
troca("Only 27 studies used experimental designs and 24 tested interventions; 12 reported effects",
      "Only 28 studies used experimental designs and 24 tested interventions; 13 reported effects")
troca("Predominaram os delineamentos observacionais (142 estudos; 71,4%), e apenas 27 estudos (13,6%) foram experimentais.",
      "Predominaram os delineamentos observacionais (163 estudos; 81,9%), e apenas 28 estudos (14,1%) foram experimentais.")
troca("Predominaram delineamentos observacionais: 142 estudos (71,4%) não manipularam variáveis e 27 (13,6%) adotaram "
      "delineamento experimental (14 quase-experimentais, 10 ensaios clínicos randomizados e 3 cruzados); outros 24 "
      "estudos (12,1%) não informaram o delineamento.",
      "Predominaram delineamentos observacionais: 163 estudos (81,9%) não manipularam variáveis (87 sem desenho "
      "especificado, 51 transversais e 25 de coorte ou longitudinais), e 28 (14,1%) adotaram delineamento experimental "
      "(15 quase-experimentais, 10 ensaios clínicos randomizados e 3 cruzados); seis estudos (3,0%) foram qualitativos, "
      "de caso, de validação psicométrica ou de métodos mistos, e dois (1,0%) não informaram o delineamento. Essa "
      "classificação segue a extração; a leitura integral dos estudos de intervenção identificou distribuição aleatória "
      "em 14 deles.")
troca("142 estudos observacionais (71,4%) e 27 experimentais (13,6%)", "163 estudos observacionais (81,9%) e 28 experimentais (14,1%)")
troca("27 estudos adotaram delineamento experimental e apenas 24 avaliaram", "28 estudos adotaram delineamento experimental e apenas 24 avaliaram")
troca("apenas 27 estudos foram experimentais e 24 testaram", "apenas 28 estudos foram experimentais e 24 testaram")

# ---------------- direção dos achados com Tomar e Allen (2021) classificado
troca("124 (62,3%) relataram efeito ou associação, 44 (22,1%) resultados mistos, 10 (5,0%) ausência de efeito e 15 (7,5%) foram descritivos.",
      "125 (62,8%) relataram efeito ou associação, 44 (22,1%) resultados mistos, 10 (5,0%) ausência de efeito e 15 (7,5%) "
      "foram descritivos; em 5 (2,5%), a direção não pôde ser determinada.")
troca("A maioria dos estudos (62,3%) relatou", "A maioria dos estudos (62,8%) relatou")
troca("124 estudos (62,3%) com efeito ou associação; 12 intervenções com efeito", "125 estudos (62,8%) com efeito ou associação; 13 intervenções com efeito")
troca("12 relataram efeito, 10 resultados mistos, uma foi apenas descritiva e uma não teve resultados acessíveis",
      "13 relataram efeito, 10 resultados mistos e uma foi apenas descritiva", n=2)
troca("A prática do handebol teve efeito em 2 de 4 estudos, sobre a motivação e a diversão;",
      "A prática do handebol teve efeito em 3 de 4 estudos, sobre a motivação, a diversão e a qualidade do sono;")
troca("as amostras dos estudos com efeito (mediana de 35,5) foram maiores que as dos demais (mediana de 24,5)",
      "as amostras dos estudos com efeito (mediana de 35) foram maiores que as dos demais (mediana de 25)")
troca("nos estudos com distribuição aleatória (7 de 14) e nos demais (5 de 10)", "nos estudos com distribuição aleatória (7 de 14) e nos demais (6 de 10)")
troca("somente 12 relataram efeito", "somente 13 relataram efeito")
troca("três estudos de intervenção foram avaliados apenas pelo resumo, e um não foi localizado.",
      "três estudos de intervenção foram avaliados apenas pelo resumo, e um, cujo texto completo não foi obtido, teve os "
      "resultados extraídos da revisão sistemática que o incluiu (KHALEGHI et al., 2026) e não teve a qualidade avaliada.")
troca("o estudo de Tomar e Allen (2021) não foi avaliado, pois a fonte não foi localizada.",
      "o estudo de Tomar e Allen (2021) não foi avaliado, pois o texto completo não foi obtido.")
troca("A duração, informada em 10 das 24 intervenções, variou de 4 a 12 semanas (mediana de 6), e as amostras",
      "A duração foi informada em semanas em 13 das 24 intervenções e variou de 4 a 12 semanas (mediana de 7); seis "
      "intervenções foram de sessão única, e as demais adotaram outros formatos, como 28 dias de suplementação ou quatro "
      "sessões em duas semanas, ou não informaram a duração. As amostras")

# ---------------- quadros (Tomar e Allen, 2021)
REF_TOMAR = ("TOMAR, R.; ALLEN, J. A. Effect of recreational handball on sleep, well-being and psychological "
             "characteristics in untrained males. Medical Science, v. 25, n. 117, p. 2804-2812, 2021.")
RES_TOMAR = ("Segundo a revisão sistemática que incluiu o estudo (KHALEGHI et al., 2026), a qualidade do sono melhorou, "
             "com diferença significativa entre os grupos após a intervenção (t = 3,776; p = 0,001). Essa fonte não relata "
             "os resultados de bem-estar nem das características psicológicas, e o texto completo não foi obtido.")
assert troca_celula("111", 1, REF_TOMAR) == 1
assert troca_celula("111", 3, "n = 24; masculino; adulto (estudantes universitários); amador ou recreativo") == 1
assert troca_celula("111", 4, "Intervenção com grupo controle (quase-experimental); treinamento") == 1
assert troca_celula("111", 5, "qualidade do sono (PSQI); bem-estar; características psicológicas") == 1
assert troca_celula("111", 6, RES_TOMAR) == 1
assert troca_celula("111", 7, "Efeito ou associação") == 1
# Quadro B1 (5 células após o estudo) e Quadro B2
n_b1 = 0
for tbl in body.iter(qn("w:tbl")):
    for tr in tbl.iter(qn("w:tr")):
        tcs = tr.findall(qn("w:tc"))
        if tcs and texto(tcs[0]).strip() == "Tomar e Allen (2021)":
            if len(tcs) == 6:
                vals = ["Intervenção com grupo controle (quase-experimental, segundo a planilha de extração); 24 estudantes "
                        "universitários destreinados (14 no grupo de intervenção, 19,78 ± 1,05 anos; 10 no controle, "
                        "19,60 ± 0,96 anos)",
                        "Handebol recreativo em jogos reduzidos, comparado a um grupo controle; 12 semanas",
                        "Qualidade do sono (PSQI); bem-estar e características psicológicas (segundo o título)",
                        RES_TOMAR, "Efeito"]
                for tc, v in zip(tcs[1:], vals):
                    ps = list(tc.iter(W))
                    troca_em(ps[0], texto(ps[0]), v)
                n_b1 += 1
            elif len(tcs) == 3:
                ps = list(tcs[2].iter(W))
                troca_em(ps[0], texto(ps[0]),
                         "Texto completo não obtido; os dados disponíveis vêm da revisão sistemática que incluiu o estudo "
                         "(KHALEGHI et al., 2026) e não permitem avaliar os componentes")
                n_b1 += 1
assert n_b1 == 2, n_b1

# ---------------- referências
troca("TOMAR, R.; ALLEN, J. Effect of recreational handball on sleep, well-being and psychological characteristics in "
      "untrained males. Medical Sciences, 2021.", REF_TOMAR)
kh = [p for p in paragrafos() if texto(p).startswith("KHALIL, H. et al. Methodology for mapping reviews")]
assert len(kh) == 1
novo = copy.deepcopy(kh[0])
troca_em(novo, texto(novo),
         "KHALEGHI, M. M. et al. Effects of team sports on sleep quality: a systematic review. Frontiers in Sports and "
         "Active Living, v. 8, e1746309, 2026. DOI: https://doi.org/10.3389/fspor.2026.1746309.")
kh[0].addprevious(novo)

# ---------------- conferência de termos proibidos no corpo do texto
proib = ["certeza da evidência", "triangula", "metanálise —", " — "]
for p in paragrafos():
    t = texto(p)
    for w in proib:
        assert w not in t or t.startswith("NTOUMANIS"), (w, t[:120])
d.save(SAI)
print("ok", SAI)
