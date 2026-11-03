"""Trocas de termos técnicos por explicações simples (versões artigo, documento e ABNT da revisão do humor).
Aplicadas ao código montado; a ordem importa (frases específicas antes das palavras isoladas)."""
TROCAS = [
    ("Metanálises associaram vigor", "Revisões que combinaram estatisticamente os resultados de vários estudos associaram vigor"),
    ("(concordância de 0,988; κ = 0,959) {R.cite('cohen1960', 'landis1977')}. Esse coeficiente expressa a consistência",
     "(concordância de 98,8% entre as duas passagens). Essa concordância expressa a consistência"),
    ("A síntese foi narrativa e estruturada conforme a diretriz SWiM {R.cite('campbell2020')}, com agrupamento por ",
     "A síntese foi narrativa, isto é, descrita em texto, tabelas e figuras, conforme as recomendações para revisões "
     "sem combinação estatística dos resultados {R.cite('campbell2020')}, com agrupamento por "),
    ("com a direção do achado como métrica padronizada. A metanálise \"\n  f\"não foi realizada, por decisão anterior à inspeção dos dados,",
     "com a direção do achado como critério comum de comparação. Os resultados \"\n  f\"não foram combinados em uma "
     "única estimativa estatística, decisão tomada antes da análise dos dados,"),
    ("efeito por variável relacionada ao humor, conforme a diretriz SWiM; um estudo", "efeito por variável relacionada ao humor; um estudo"),
    ("\"Síntese estruturada dos achados por grupo de variáveis (diretriz SWiM)\"", "\"Síntese dos achados por grupo de variáveis\""),
    ("esse grupo partiu de valores piores, o que favorece a \"\n  f\"regressão à média {c('H15')}.",
     "esse grupo partiu de valores piores, e valores extremos tendem a se aproximar da média na medida seguinte, \"\n  "
     "f\"mesmo sem efeito da intervenção {c('H15')}."),
    ("sem grupo controle, o que favorece a regressão à média, e \"",
     "sem grupo controle, e escores extremos tendem a melhorar na medida seguinte mesmo sem tratamento; além disso, \""),
    ("Na metanálise de \"\n  f\"{R.autor('reinebo2024')}, o treino",
     "Na revisão de \"\n  f\"{R.autor('reinebo2024')}, que combinou estatisticamente os resultados dos estudos, o treino"),
    ("na metanálise sobre a ansiedade, a escolha", "na revisão sobre a ansiedade, que também combinou os resultados, a escolha"),
    ("A heterogeneidade impediu a metanálise {R.cite('hopkins2009')}, e a síntese seguiu a diretriz SWiM \"\n  f\"{R.cite('campbell2020')}.",
     "As diferenças entre os estudos impediram a combinação estatística dos resultados {R.cite('hopkins2009')}, e a "
     "síntese seguiu \"\n  f\"as recomendações para revisões sem essa combinação {R.cite('campbell2020')}."),
    ("a heterogeneidade impediu a síntese quantitativa", "as diferenças entre os estudos impediram a combinação estatística dos resultados"),
    ("instrumentos heterogêneos", "instrumentos diferentes"),
    ("versões heterogêneas", "versões diferentes"),
    ("dados heterogêneos", "dados muito diferentes entre si"),
    ("medidas heterogêneas", "medidas diferentes"),
    ("heterogêneos {R.cite('henze2025athmon')}", "muito diferentes entre si {R.cite('henze2025athmon')}"),
    ("evidência limitada e heterogênea", "evidência limitada e variada"),
    ("escassa, heterogênea e raramente experimental", "escassa, variada e raramente experimental"),
]


def aplicar(txt):
    for a, b in TROCAS:
        txt = txt.replace(a, b)
    return txt
