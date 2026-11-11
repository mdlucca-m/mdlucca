# Executado dentro de revisar.py, depois de extra_qualidade.py: aprofundamento da análise das intervenções.
from docx.shared import Cm as _Cm2
from docx.enum.text import WD_ALIGN_PARAGRAPH as _AL

FIG = "/tmp/claude-0/-home-user/0bcd0703-6a3e-5492-93df-26f74a3ac8bd/scratchpad/fig/qualidade_ephpp.png"


def _p_com(txt_ini):
    alvos = [p for p in body.iter(W("w:p")) if texto(p).startswith(txt_ini)]
    assert len(alvos) == 1, (txt_ini, len(alvos))
    return alvos[0]


# ------------------------------------------------------------------ Resultados: cruzamentos, Figura 8 e divergências
fonte_t3 = _p_com("Nota: classificação pelo EPHPP").getnext()
a = novo(CORPO, "Por tipo de intervenção, o treino de habilidades psicológicas, o tipo mais testado, teve qualidade forte "
         "em 1 dos 10 estudos, moderada em 3 e fraca em 6; o feedback e a ação do treinador tiveram qualidade moderada em "
         "3 de 4 estudos; e a nutrição (2 de 2) e a prática do handebol (2 de 3 estudos avaliados) reuniram 4 dos 5 "
         "estudos de qualidade forte (Figura 8B). Entre os 14 estudos com distribuição aleatória, a qualidade foi forte em "
         "5, moderada em 5 e fraca em 4; entre os 9 estudos sem distribuição aleatória, nenhum alcançou qualidade forte, 3 "
         "tiveram qualidade moderada e 6, fraca. A mediana da amostra foi de 25 participantes nos estudos de qualidade "
         "forte, de 37,5 nos de qualidade moderada e de 35 nos de qualidade fraca, o que indica que a qualidade não "
         "acompanhou o tamanho da amostra. Os três estudos avaliados apenas pelo resumo tiveram qualidade fraca, em parte "
         "pela falta de informação. A Figura 8 apresenta a distribuição das classificações por componente e por tipo de "
         "intervenção.", fonte_t3)
cap = copy.deepcopy(K[95])
set_text(cap, "Figura 8: Qualidade metodológica dos estudos de intervenção segundo o EPHPP (QP4)")
a.addnext(cap)
pimg = d.add_paragraph()
pimg.alignment = _AL.CENTER
pimg.add_run().add_picture(FIG, width=_Cm2(16))
cap.addnext(pimg._p)
nf = copy.deepcopy(K[97])
set_text(nf, "Nota: (A) número de estudos classificados como fortes, moderados ou fracos em cada componente e na qualidade "
         "global; (B) qualidade global por tipo de intervenção; 23 estudos avaliados.")
pimg._p.addnext(nf)
ff = copy.deepcopy(K[98])
set_text(ff, "Fonte: elaborada pelos autores (2026).")
nf.addnext(ff)
novo(CORPO, "A leitura integral identificou, ainda, divergências entre o resumo, o texto e as tabelas em dez estudos de "
     "intervenção. Entre elas, estão valores de correlação diferentes no resumo e nos resultados (NISHIDA et al., 2021), "
     "duração da intervenção de seis semanas no resumo e de oito no método (UPADHYAY et al., 2025), efeito sobre o afeto "
     "positivo descrito de forma oposta no resumo e nos resultados (SOTO; GARCÍA-HERRERO; CARCEDO, 2020), valores de p e "
     "de tamanho de efeito diferentes entre o texto e as tabelas (SAKET et al., 2026), resultado do não julgamento "
     "favorável ao grupo controle nos resultados e ao grupo experimental no resumo (MARTINY et al., 2024) e análise "
     "estatística anunciada no método diferente da apresentada nos resultados (KHAZDOZI; BAHARI; ASHAYERI, 2017). Nesses "
     "casos, foram adotados os valores das tabelas e da seção de resultados.", ff)

# ------------------------------------------------------------------ Discussão: componentes e relação com os resultados
dq = _p_com("A avaliação da qualidade reforça essa interpretação.")
d1 = novo(CORPO, "Os componentes fracos indicam onde a pesquisa pode avançar com mais facilidade. A falta de comparação "
          "dos grupos antes da intervenção, observada em 15 estudos, pode ser resolvida pela apresentação dos valores "
          "iniciais de cada grupo e pelo ajuste das diferenças na análise, como no ensaio de imagética e autodiálogo, que "
          "usou o pré-teste como covariável (UPADHYAY et al., 2025). O relato das perdas, ausente em 11 estudos, depende "
          "apenas da apresentação do fluxo dos participantes recomendada pelo CONSORT (SCHULZ; ALTMAN; MOHER, 2010), "
          "adotada em um dos ensaios (NUELL et al., 2025). O cegamento é mais difícil nas intervenções psicológicas, pois "
          "o atleta sabe que participa de um programa, mas a avaliação por pessoas que desconhecem o grupo e o uso de "
          "condições de controle ativas, como no ensaio de mindfulness com controle ativo (STAIANO et al., 2026) e no "
          "ensaio com placebo de cafeína (BOUGRINE et al., 2023), mostram que esse viés pode ser reduzido no handebol.", dq)
novo(CORPO, "A relação entre qualidade e resultado também merece atenção. Os estudos de qualidade forte relataram efeito "
     "com maior frequência que os de qualidade moderada ou fraca, mas quatro dos cinco testaram intervenções não "
     "psicológicas, como a suplementação, a cafeína e a prática do handebol, e apenas um avaliou um programa psicológico, "
     "com desfecho de desempenho (UPADHYAY et al., 2025). Assim, os programas psicológicos com desfechos psicológicos, "
     "que interessam mais diretamente à psicologia do esporte, ainda não foram testados em estudo de qualidade forte no "
     "handebol. Somadas às divergências de relato encontradas em dez estudos, essas fragilidades indicam que a confiança "
     "nos efeitos relatados deve ser baixa e que os próximos estudos precisam combinar distribuição aleatória por equipes "
     "(CAMPBELL et al., 2012), cálculo do tamanho da amostra (ABT et al., 2020), descrição completa da intervenção "
     "(HOFFMANN et al., 2014) e relato transparente dos resultados.", d1)

# ------------------------------------------------------------------ Quadro B2: justificativa de cada classificação
_lin2 = [["Estudo", "Qualidade global", "Justificativa da classificação"]]
for n in ORDEM_B:
    q = _Q[n]
    if q is None:
        _lin2.append([_ROTN[n], "Não avaliado", "Fonte não localizada; o artigo de 2021 dos mesmos autores localizado nas "
                      "bases não mede sono, bem-estar nem variáveis psicológicas"])
    else:
        _lin2.append([_ROTN[n], _glob(q), q["j"][0].upper() + q["j"][1:]])
ant = K[432]
c2 = copy.deepcopy(K[429])
set_text(c2, "Quadro B2: Justificativa da classificação da qualidade metodológica de cada estudo de intervenção (EPHPP)")
ant.addnext(c2)
t2 = _tab(_lin2, [4.6, 2.6, 17.4], tam=9)
c2.addnext(t2)
n2 = copy.deepcopy(K[431])
set_text(n2, "Nota: forte, nenhum componente fraco; moderada, um componente fraco; fraca, dois ou mais componentes fracos "
         "(THOMAS et al., 2004). Os estudos de Paul Meeûs, Serpa e De Cuyper (2010), Norouzi et al. (2025) e Staiano et "
         "al. (2026) foram avaliados pelo resumo.")
t2.addnext(n2)
f2 = copy.deepcopy(K[432])
set_text(f2, "Fonte: elaborada pelos autores (2026).")
n2.addnext(f2)

# ------------------------------------------------------------------ autoria correta do estudo de 1998 (Psicothema)
GIL_REF = ("GIL MARTÍNEZ, J.; CAPAFONS BONET, A.; LABRADOR ENCINAS, F. Programa psicológico para mejorar los resultados "
           "de jugadores de balonmano. Psicothema, v. 10, n. 2, p. 271-280, 1998.")
for p in list(body.iter(W("w:p"))):
    t = texto(p)
    novo_t = t
    if t.startswith("MARTÍNEZ, M. et al. Psychological program"):
        set_text(p, GIL_REF)
        body.remove(p)
        refs_ = [r for r in body.iter(W("w:p")) if re.match(r"[A-ZÁÉÍÓÚÜ][A-ZÁÉÍÓÚÜ' -]+,", texto(r))
                 and "REFERÊNCIAS" not in texto(r)]
        alvo = next(r for r in refs_ if texto(r) > GIL_REF and texto(r).startswith(("G", "H")))
        alvo.addprevious(p)
        continue
    if "MARTINEZ; BONET, J.; ENCINAS, A. et al." in t:
        novo_t = re.sub(r"MARTINEZ; BONET, J\.; ENCINAS, A\. et al\. Psychological program to improve the output of "
                        r"handball players\. Psicothema, 1998\.", GIL_REF, t)
    novo_t = novo_t.replace("MARTÍNEZ et al., 1998", "GIL MARTÍNEZ; CAPAFONS BONET; LABRADOR ENCINAS, 1998")
    novo_t = novo_t.replace("Martínez et al. (1998)", "Gil Martínez, Capafons Bonet e Labrador Encinas (1998)")
    if novo_t != t:
        set_text(p, novo_t)
assert not any("Martínez et al. (1998)" in texto(p) or "MARTÍNEZ et al., 1998" in texto(p) for p in body.iter(W("w:p")))
