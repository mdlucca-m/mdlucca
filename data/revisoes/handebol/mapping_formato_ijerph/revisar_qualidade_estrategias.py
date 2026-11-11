# Executado dentro de revisar.py: avaliação da qualidade (EPHPP), estratégias de busca por base e protocolo.
from docx.shared import Pt as _Pt, Cm as _Cm
from qualidade_ephpp import Q as _Q, ROT as _ROT, global_ as _glob


def _tab(linhas, larg, tam=9):
    t = d.add_table(rows=len(linhas), cols=len(linhas[0]))
    t.autofit = False
    for i, lin in enumerate(linhas):
        for j, v in enumerate(lin):
            c = t.cell(i, j)
            c.width = _Cm(larg[j])
            p = c.paragraphs[0]
            p.paragraph_format.space_after = _Pt(0)
            p.paragraph_format.space_before = _Pt(0)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.first_line_indent = _Cm(0)
            r = p.add_run(v)
            r.font.size, r.font.name, r.bold = _Pt(tam), "Times New Roman", (i == 0)
    tbl = t._tbl
    pr = tbl.tblPr
    bd = OxmlElement("w:tblBorders")
    for lado in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{lado}")
        e.set(W("w:val"), "single" if lado != "insideH" else "single")
        e.set(W("w:sz"), "8" if lado != "insideH" else "2")
        e.set(W("w:color"), "000000" if lado != "insideH" else "BFBFBF")
        bd.append(e)
    pr.append(bd)
    lay = OxmlElement("w:tblLayout")
    lay.set(W("w:type"), "fixed")
    pr.append(lay)
    grid = tbl.find(W("w:tblGrid"))
    for gc, w in zip(grid.findall(W("w:gridCol")), larg):
        gc.set(W("w:w"), str(int(w * 567)))
    tr0 = tbl.findall(W("w:tr"))[0]
    trPr = tr0.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    trPr.append(th)
    return tbl


# rótulos dos estudos, tirados do Quadro B1
_ROTN = {}
for row in Table(K[430], d).rows:
    tcs = row._tr.findall(W("w:tc"))
    nome = "".join(x.text or "" for x in tcs[0].iter(W("w:t")))
    nn_ = next((v for k, v in NOMES.items() if nome.startswith(k)), None)
    if nn_:
        _ROTN[nn_] = nome
ORDEM_B = [2, 81, 127, 145, 153, 170, 173, 179, 196, 199, 16, 94, 119, 171, 61, 111, 128, 192, 89, 107, 174, 57, 132, 50]
assert set(ORDEM_B) == set(_ROTN), set(ORDEM_B) ^ set(_ROTN)

# ------------------------------------------------------------------ Método: 2.2 e nova seção 2.6
troca(K[69], "termos relacionados à modalidade e a pelo menos um dos domínios psicológicos definidos no protocolo.",
      "termos relacionados à modalidade e a pelo menos um dos domínios psicológicos definidos no protocolo. A "
      "estratégia completa adotada em cada base de dados, escrita na sintaxe própria de cada base, consta do Apêndice "
      "C, e o protocolo da revisão, elaborado com base no Template for a Mapping Study Protocol (EBSE-RG, 2009), "
      "consta do Apêndice D.")
h26 = next(p for p in body.iter(W("w:p")) if texto(p) == "2.6 Questões de pesquisa")
set_text(h26, "2.7 Questões de pesquisa")
for el in [("H", "2.6 Avaliação da qualidade metodológica dos estudos de intervenção"),
           ("P", "A qualidade metodológica dos estudos de intervenção foi avaliada pelo instrumento do Effective Public "
                 "Health Practice Project (EPHPP), indicado para estudos de intervenção randomizados e não randomizados "
                 "(ARMIJO-OLIVO et al., 2012; THOMAS et al., 2004). O instrumento examina seis componentes: (1) viés de "
                 "seleção, isto é, a probabilidade de os participantes representarem a população-alvo e a proporção dos "
                 "convidados que aceitaram participar; (2) delineamento do estudo; (3) fatores de confusão, isto é, "
                 "diferenças importantes entre os grupos antes da intervenção e seu controle na análise; (4) cegamento "
                 "dos avaliadores e dos participantes; (5) métodos de coleta de dados, quanto à validade e à "
                 "confiabilidade dos instrumentos; e (6) perdas e desistências. Cada componente foi classificado como "
                 "forte, moderado ou fraco, e a qualidade global foi considerada forte quando nenhum componente foi "
                 "fraco, moderada quando um componente foi fraco e fraca quando dois ou mais componentes foram fracos "
                 "(THOMAS et al., 2004)."),
           ("P", "A avaliação baseou-se no texto completo de acesso aberto de cada estudo e, quando ele não estava "
                 "disponível, no resumo. As informações não relatadas foram classificadas conforme o dicionário do "
                 "instrumento, que considera fraco o componente sem descrição suficiente nos casos de seleção, fatores de "
                 "confusão, coleta de dados e perdas, e moderado no caso do cegamento. Nos estudos sem grupo de "
                 "comparação, os fatores de confusão foram classificados como fracos, e nos estudos cruzados, em que cada "
                 "participante serve de controle para si mesmo, como fortes. Para cada classificação, registrou-se o "
                 "trecho da fonte que a justificou.")]:
    novo_el = copy.deepcopy(H2 if el[0] == "H" else CORPO)
    set_text(novo_el, el[1])
    h26.addprevious(novo_el)

# ------------------------------------------------------------------ Resultados (QP4): Tabela 3 de qualidade
_g = {n: _glob(q) for n, q in _Q.items() if q}
a = novo(CORPO, "Quanto à qualidade metodológica, avaliada pelo EPHPP em 23 dos 24 estudos de intervenção, 5 estudos "
         "tiveram qualidade forte, 8 moderada e 10 fraca (Tabela 3). O delineamento foi o componente mais bem avaliado, "
         "forte em 21 estudos, pois a maioria comparou a intervenção a um grupo controle ou a outra condição; a leitura "
         "integral mostrou, inclusive, que 14 intervenções empregaram distribuição aleatória, quatro delas em "
         "delineamento cruzado. As fragilidades concentraram-se nos fatores de confusão, fracos em 15 estudos, pela "
         "ausência de comparação dos grupos antes da intervenção ou pela falta de ajuste das diferenças encontradas, e "
         "nas perdas e desistências, fracas em 11 estudos, que não relataram quantos participantes concluíram o estudo. "
         "O cegamento foi forte em apenas um estudo, um ensaio duplo-cego com placebo (BOUGRINE et al., 2023), e "
         "moderado em 20, em geral por não ter sido descrito.", K[138])
a = novo(CORPO, "Os cinco estudos de qualidade forte foram o ensaio com suplementação de Syzygium cumini (ASSUNÇÃO "
         "CARVALHO et al., 2018), o ensaio de handebol recreativo com mulheres destreinadas (HORNSTRUP et al., 2018), o "
         "ensaio cruzado com cafeína no Ramadã (BOUGRINE et al., 2023), o ensaio de imagética e autodiálogo (UPADHYAY et "
         "al., 2025) e o ensaio cruzado do handebol caminhado (MARTINS et al., 2026); apenas um deles testou um programa "
         "psicológico, e com desfecho de desempenho. Relataram efeito quatro dos cinco estudos de qualidade forte, três "
         "dos oito de qualidade moderada e cinco dos dez de qualidade fraca.", a)
a = novo(LEG, "Tabela 3: Qualidade metodológica dos estudos de intervenção segundo o EPHPP", a)
_lin = [["Estudo", "Seleção", "Delineamento", "Confusão", "Cegamento", "Coleta de dados", "Perdas", "Qualidade global"]]
for n in ORDEM_B:
    q = _Q[n]
    if q is None:
        _lin.append([_ROTN[n], "–", "–", "–", "–", "–", "–", "Não avaliado"])
    else:
        _lin.append([_ROTN[n]] + [_ROT[q[k]] for k in ("sel", "del_", "conf", "ceg", "col", "perd")] + [_g[n]])
_t = _tab(_lin, [3.4, 1.75, 1.75, 1.75, 1.75, 1.75, 1.75, 2.0], tam=8)
a.addnext(_t)
a = _t
a = novo(NOTA, "Nota: classificação pelo EPHPP (THOMAS et al., 2004): forte, nenhum componente fraco; moderada, um "
         "componente fraco; fraca, dois ou mais componentes fracos. Os estudos de Paul Meeûs, Serpa e De Cuyper (2010), "
         "Norouzi et al. (2025) e Staiano et al. (2026) foram avaliados pelo resumo; o estudo de Tomar e Allen (2021) não "
         "foi avaliado, pois a fonte não foi localizada.", a)
a = novo(FONTE, "Fonte: elaborada pelos autores (2026).", a)

# ------------------------------------------------------------------ Discussão e limitações
novo(CORPO, "A avaliação da qualidade reforça essa interpretação. Menos de um quarto dos estudos de intervenção alcançou "
     "qualidade forte, e os programas psicológicos com desfechos psicológicos validados, como os de mindfulness, "
     "neurofeedback, treino de habilidades psicológicas e relaxamento com imagética (LEPIR et al., 2025; MARTINY et al., "
     "2024; METAN; KÜÇÜK, 2022; SAKET et al., 2026), ficaram entre a qualidade moderada e a fraca, sobretudo pela falta "
     "de comparação dos grupos antes da intervenção e pelo relato incompleto das perdas. Esse padrão coincide com o de "
     "revisões de intervenções psicológicas no esporte, cujos efeitos se atenuaram quando a análise se restringiu aos "
     "ensaios randomizados (REINEBO et al., 2024), e indica que os efeitos favoráveis relatados no handebol devem ser "
     "confirmados por ensaios com grupos equivalentes, cegamento dos avaliadores e relato das perdas.", K[162])
troca(K[171], "Por se tratar de uma revisão de mapeamento, não foram avaliadas a qualidade metodológica dos estudos nem a "
              "magnitude dos efeitos (KHALIL et al., 2025).",
      "Por se tratar de uma revisão de mapeamento, a qualidade metodológica foi avaliada apenas nos estudos de "
      "intervenção, e a magnitude dos efeitos não foi combinada entre os estudos (KHALIL et al., 2025); além disso, três "
      "estudos de intervenção foram avaliados apenas pelo resumo, e um não foi localizado.")

# ------------------------------------------------------------------ Apêndices C (estratégias) e D (protocolo)
B1 = "(handball OR \"team handball\" OR \"beach handball\" OR handebol OR balonmano)"
B2 = ("(mood OR affect OR emotion* OR anxiety OR stress OR \"self-confidence\" OR motivation OR \"self-efficacy\" OR "
      "\"motivational climate\" OR \"goal orientation\" OR \"psychological skills\" OR coping OR imagery OR mindfulness OR "
      "\"mental toughness\" OR sleep OR recovery OR \"well-being\" OR burnout OR \"mental health\")")
B3 = "(training OR competition OR match OR season OR game)"


def _campo(bloco, suf):
    termos = re.findall(r'"[^"]+"|[^() ]+', bloco)
    termos = [t for t in termos if t != "OR"]
    return "(" + " OR ".join(f"{t}{suf}" for t in termos) + ")"


def _ep(bloco):
    termos = [t for t in re.findall(r'"[^"]+"|[^() ]+', bloco) if t != "OR"]
    return "(" + " OR ".join(f"TITLE_ABS:{t}" for t in termos) + ")"


EST_B = [["Base de dados", "Campos pesquisados", "Estratégia de busca"],
         ["PubMed", "Título e resumo ([tiab])",
          f"{_campo(B1, '[tiab]')} AND {_campo(B2, '[tiab]')} AND {_campo(B3, '[tiab]')}"],
         ["Scopus", "Título, resumo e palavras-chave (TITLE-ABS-KEY)", f"TITLE-ABS-KEY({B1} AND {B2} AND {B3})"],
         ["Web of Science (Coleção Principal)", "Tópico (TS)", f"TS=({B1} AND {B2} AND {B3})"],
         ["Europe PMC", "Título e resumo (TITLE_ABS)", f"{_ep(B1)} AND {_ep(B2)} AND {_ep(B3)}"],
         ["OpenAlex", "Título e resumo (title_and_abstract.search)", f"{B1} AND {B2} AND {B3}"],
         ["LILACS (BVS)", "Palavras do título, do resumo e dos descritores (tw)", f"tw:{B1} AND tw:{B2} AND tw:{B3}"],
         ["SciELO", "Todos os índices", f"{B1} AND {B2} AND {B3}"],
         ["Crossref", "Metadados bibliográficos (query.bibliographic)",
          "Combinações de um termo do bloco 1 com um termo do bloco 2 (por exemplo, handball anxiety), pois a "
          "interface não aceita operadores booleanos"]]
PROT = [["Item do protocolo", "Descrição nesta revisão"],
        ["Contexto e justificativa", "Variáveis psicológicas investigadas no treinamento e na competição do handebol; "
         "ausência de revisão abrangente que mapeie o tema (Seção 1)"],
        ["Questões de pesquisa", "QP1 a QP5 (Seção 2.7)"],
        ["Estratégia de busca", "Oito bases de dados (Crossref, Europe PMC, LILACS, OpenAlex, PubMed, SciELO, Scopus e "
         "Web of Science), sem restrição de data, com publicações até setembro de 2026; termos da Tabela 1 e sintaxe do "
         "Quadro C1; exame das listas de referências dos estudos incluídos"],
        ["Critérios de seleção", "Estratégia PECOS (Tabela 2): atletas ou praticantes de handebol; treinamento ou "
         "competição; ao menos uma variável psicológica; estudos originais em inglês, português ou espanhol, de qualquer "
         "delineamento"],
        ["Procedimento de seleção", "Remoção de duplicatas por DOI, identificador PubMed e título; pré-triagem por "
         "termos; triagem de títulos e resumos em duas passagens independentes, assistidas por modelo de linguagem, com "
         "terceira avaliação das divergências; leitura do texto completo (Figura 1)"],
        ["Extração dos dados", "Autor, ano, país, amostra, contexto, delineamento, variáveis, instrumentos, protocolos "
         "das intervenções e resultados, com o trecho literal da fonte (Apêndice A)"],
        ["Avaliação da qualidade", "EPHPP aplicado aos estudos de intervenção (Seção 2.6 e Tabela 3)"],
        ["Síntese e análise", "Estatística descritiva, análise de agrupamento (cluster) e evolução temporal da produção "
         "(Seções 2.4 e 2.5)"],
        ["Relato", "Itens aplicáveis do PRISMA-ScR (TRICCO et al., 2018)"]]
fim = K[432]
for titulo, leg, linhas, larg, nota in [
        ("APÊNDICE C: ESTRATÉGIAS DE BUSCA EM CADA BASE DE DADOS",
         "Quadro C1: Estratégia de busca adotada em cada base de dados", EST_B, [3.6, 4.4, 16.6],
         "Nota: termos e combinação da Tabela 1 (#1 AND #2 AND #3), escritos na sintaxe de cada base; sem restrição de "
         "data, com publicações até setembro de 2026."),
        ("APÊNDICE D: PROTOCOLO DA REVISÃO DE MAPEAMENTO",
         "Quadro D1: Protocolo da revisão de mapeamento segundo o Template for a Mapping Study Protocol", PROT,
         [5.0, 19.6], "Nota: modelo de protocolo de EBSE-RG (2009).")]:
    h = copy.deepcopy(K[428])
    set_text(h, titulo)
    _ppr = h.get_or_add_pPr()
    _ppr.insert(0, OxmlElement("w:pageBreakBefore"))
    fim.addnext(h)
    c_ = copy.deepcopy(K[429])
    set_text(c_, leg)
    h.addnext(c_)
    tb_ = _tab(linhas, larg, tam=9)
    c_.addnext(tb_)
    n_ = copy.deepcopy(K[431])
    set_text(n_, nota)
    tb_.addnext(n_)
    f_ = copy.deepcopy(K[432])
    set_text(f_, "Fonte: elaborada pelos autores (2026).")
    n_.addnext(f_)
    fim = f_
