"""Artigo 1: perfis de humor em atletas de handebol de elite.

Restrições de redação: nenhum travessão, nenhum traço de meia risca e nenhum
gerúndio.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigo4p"))
import fonte as F  # noqa: E402
from dados import (DIAS, N_DIA, N_PERFIL, PERFIL_DIA, PERFIS_T,
                   faixa)  # noqa: E402

NORMATIVO = {"Iceberg": 29.4, "Submerso": 25.5, "Barbatana tubarão": 17.3,
             "Superfície": 14.8, "Iceberg invertido": 10.3,
             "Everest invertido": 2.7}

TITULO = ("Perfil de humor em atletas de handebol de elite na última semana "
          "de pré-temporada: os seis perfis e suas características")
SUBTITULO = ("Estudo observacional descritivo de um microciclo de sete dias "
             "com duas coletas diárias")

_RISCO1, _RISCO7 = faixa("De risco", 1), faixa("De risco", 7)
_FAV1, _FAV7 = faixa("Favorável", 1), faixa("Favorável", 7)
_NEU1, _NEU7 = faixa("Neutro", 1), faixa("Neutro", 7)
NORMATIVO = {"Iceberg": 29.4, "Submerso": 25.5, "Barbatana de tubarão": 17.3,
             "Superfície": 14.8, "Iceberg invertido": 10.3,
             "Everest invertido": 2.7}

ABERTURA = [
 ("RESUMO",
  "A oposição entre o perfil iceberg e o seu inverso orientou meio século de "
  "monitoramento psicológico no esporte, mas perdeu poder discriminativo "
  "quando se verificou que o iceberg é o padrão típico de atletas, "
  "bem-sucedidos ou não. A análise de agrupamento sobre as seis subescalas da "
  "Escala de Humor de Brunel substituiu essa dicotomia por seis perfis, três "
  "deles associados a risco à saúde mental. Nenhum estudo os aplicou ao "
  "handebol. Este estudo descreve o perfil de humor de 27 atletas de handebol "
  "masculino de primeira divisão ao longo dos sete dias da última semana de "
  "pré-temporada, com duas coletas diárias, e caracteriza cada subescala "
  "nesta população. No dia de repouso o perfil iceberg predominou, com 40,5% "
  "das observações, e os três perfis de risco somaram 26,2%, valor quase "
  "idêntico aos 26,5% da única amostra brasileira classificada pelo mesmo "
  "critério. Na véspera da competição o iceberg caiu para 17,4%, a barbatana "
  "de tubarão subiu de 2,4% para 28,3% e a faixa de risco alcançou 43,5% das "
  "observações. Pelo critério de Morgan, aplicado em paralelo sobre escores "
  "brutos, a proporção em perfil iceberg caiu de 71,4% para 32,6% ao longo "
  "da semana, e a análise da derivada da série mostra que a perda não é "
  "gradual: duas quedas ultrapassam o piso de ruído de 10,0 pontos "
  "percentuais, a primeira no dia seguinte à sessão inicial de alta "
  "intensidade e a segunda na véspera da competição, com um platô entre elas. "
  "Quatro das seis subescalas apresentaram efeito piso entre 49,6% e 80,5%, "
  "mais de três vezes o limite de 15%. Nenhuma subescala foi confiável em uma "
  "leitura isolada, com ICC entre 0,31 e 0,59, faixa compatível com a "
  "estabilidade publicada do instrumento, e todas passaram de 0,76 na média "
  "de sete dias. O estudo entrega a primeira descrição dos seis perfis em "
  "handebol, os primeiros percentis de referência da modalidade e um método "
  "de leitura da predominância semanal que separa sinal de ruído."),
 ("PALAVRAS-CHAVE",
  "humor; handebol; Escala de Humor de Brunel; perfil de humor; "
  "monitoramento; pré-temporada."),
]

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."

_ORDEM = ["Vigor", "Fadiga", "Tensão", "Depressão", "Raiva", "Confusão"]
_N = 27
_POSICOES = [("Armador", 12, 44.4), ("Pivô", 9, 33.3), ("Ala", 6, 22.2)]
_A_COLETAR = "a coletar"


def _erro_padrao(p: float, n: int) -> float:
    from math import sqrt
    return 100 * sqrt((p / 100) * (1 - p / 100) / n)


def _suavizar(y: list[float]) -> list[float]:
    s = list(y)
    for i in range(1, len(y) - 1):
        s[i] = (y[i - 1] + 2 * y[i] + y[i + 1]) / 4
    return s


_ICE = [PERFIL_DIA[d][0] for d in DIAS]
_EP = [_erro_padrao(v, N_DIA[d]) for v, d in zip(_ICE, DIAS)]
_PISO = sum(_EP) / len(_EP)
_SUAVE = _suavizar(_ICE)
_DERIV = [_SUAVE[i] - _SUAVE[i - 1] for i in range(1, len(DIAS))]


# ══════════════════════════════════════════════════════════════ tabelas ═══
TABELAS = {

"amostra": {
 "numero": 1,
 "titulo": ("Caracterização sociodemográfica, socioeconômica e esportiva dos "
            "atletas"),
 "cabecalho": ["Característica", "Categoria ou estatística", "n", "%"],
 "linhas": [
  ["**Demográficas**", "", "", ""],
  ["Sexo", "Masculino", str(_N), "100,0"],
  ["Idade (anos)", F.AMOSTRA["idade"], str(_N), "100,0"],
  ["Faixa etária", "Até 20 anos", _A_COLETAR, _A_COLETAR],
  ["", "De 21 a 25 anos", _A_COLETAR, _A_COLETAR],
  ["", "Acima de 25 anos", _A_COLETAR, _A_COLETAR],
  ["Cor ou raça autodeclarada", "Conforme categorias do IBGE", _A_COLETAR,
   _A_COLETAR],
  ["Estado civil", "Com e sem união estável", _A_COLETAR, _A_COLETAR],
  ["Filhos", "Com e sem filhos", _A_COLETAR, _A_COLETAR],
  ["**Socioeconômicas**", "", "", ""],
  ["Escolaridade", "Fundamental, médio e superior", _A_COLETAR, _A_COLETAR],
  ["Estuda atualmente", "Sim e não", _A_COLETAR, _A_COLETAR],
  ["Renda mensal", "Em salários mínimos", _A_COLETAR, _A_COLETAR],
  ["Fonte de renda além do clube", "Sim e não", _A_COLETAR, _A_COLETAR],
  ["Moradia durante a temporada", "Alojamento do clube e residência própria",
   _A_COLETAR, _A_COLETAR],
  ["Vínculo contratual", "Profissional registrado e outros", _A_COLETAR,
   _A_COLETAR],
  ["**Esportivas**", "", "", ""],
  ["Experiência na modalidade (anos)", F.AMOSTRA["experiencia"], str(_N),
   "100,0"],
  ["Posição de jogo", _POSICOES[0][0], str(_POSICOES[0][1]),
   F.br(_POSICOES[0][2], 1)],
  ["", _POSICOES[1][0], str(_POSICOES[1][1]), F.br(_POSICOES[1][2], 1)],
  ["", _POSICOES[2][0], str(_POSICOES[2][1]), F.br(_POSICOES[2][2], 1)],
  ["Tempo no clube atual (anos)", "Média e desvio-padrão", _A_COLETAR,
   _A_COLETAR],
  ["Nível competitivo", "Primeira divisão nacional", str(_N), "100,0"],
  ["Convocação para seleção", "Sim e não", _A_COLETAR, _A_COLETAR],
  ["Coorte completa", "Sete coletas concluídas", "19", "70,4"],
 ],
 "nota": ("Nota: idade e experiência estão em média, desvio-padrão e "
          "amplitude. As linhas marcadas como a coletar identificam as "
          "variáveis do protocolo sociodemográfico e socioeconômico cujo "
          "registro individual não consta da base atual e que serão "
          "incorporadas antes da submissão, a partir da ficha de cadastro do "
          "clube. Fonte primária das linhas preenchidas: Tabela 2 do "
          "relatório completo."),
},

"descritiva": {
 "numero": 2,
 "titulo": ("Caracterização das seis subescalas do BRUMS e da Perturbação "
            "Total do Humor nesta amostra"),
 "cabecalho": ["Subescala", "Média", "Desvio-padrão", "Mediana",
               "Intervalo interquartil", "Assimetria", "Curtose",
               "Piso (%)"],
 "linhas": [[n] + [F.br(v, 2) if isinstance(v, float) else str(v)
                   for v in F.DESCRITIVA[n]]
            for n in ["PTH (TMD)"] + _ORDEM],
 "nota": ("Nota: PTH é a Perturbação Total do Humor, calculada pela soma das "
          "cinco subescalas negativas menos o vigor. Subescalas de 0 a 16 "
          "pontos. Piso é o percentual de respostas no valor mínimo da "
          "subescala; considera-se o efeito presente acima de 15% (Terwee e "
          "outros, 2007). Assimetria acima de 2 e curtose acima de 7 indicam "
          "afastamento grave da normalidade. Fonte primária: Tabela 3 do "
          "relatório completo."),
},

"percentis": {
 "numero": 3,
 "titulo": ("Percentis de referência das subescalas do BRUMS para atletas de "
            "handebol masculino de elite"),
 "cabecalho": ["Subescala", "P5", "P25", "P50", "P75", "P95"],
 "linhas": [[n] + [str(v) for v in F.PERCENTIS[n]]
            for n in ["PTH (TMD)"] + _ORDEM],
 "nota": ("Nota: percentis observados sobre todas as coletas do microciclo. "
          "Na ausência de normas de escore T para handebol, estes percentis "
          "servem de referência provisória para a modalidade e substituem, "
          "para uso aplicado, a comparação com normas de população geral ou "
          "de amostras esportivas heterogêneas (Terry e Lane, 2000). Fonte "
          "primária: Tabela 74 do relatório completo."),
},

"psicometria": {
 "numero": 4,
 "titulo": ("Confiabilidade interna e estabilidade entre dias de cada "
            "subescala"),
 "cabecalho": ["Subescala", "Alfa", "Alfa ordinal", "Ômega ordinal",
               "Duas metades", "Item-total mínimo", "ICC de uma coleta",
               "ICC da média de sete dias"],
 "linhas": [
  [n] + [F.br(v, 2) if v is not None else "n.e."
         for v in F.CONFIABILIDADE[n]]
  + [F.br(F.ESTABILIDADE[n][0], 2), F.br(F.ESTABILIDADE[n][1], 2)]
  for n in sorted(F.CONFIABILIDADE, key=lambda k: -F.CONFIABILIDADE[k][0])
 ],
 "nota": ("Nota: n.e. indica coeficiente não estimável, porque a matriz "
          "policórica não convergiu nas subescalas com efeito piso extremo. "
          "O ICC de uma coleta é o ICC(1,1) e o da média de sete dias é o "
          "ICC(1,7), obtido pela fórmula de Spearman e Brown. Para "
          "comparação, os coeficientes alfa originais do instrumento são de "
          "0,74 em tensão, 0,85 em depressão, 0,82 em raiva, 0,85 em vigor, "
          "0,90 em fadiga e 0,83 em confusão, e a estabilidade de uma semana "
          "situa-se entre 0,26 e 0,53 (Terry e outros, 1999, 2003). Fonte "
          "primária: Tabelas 6 e 7 do relatório completo."),
},

"correlacao": {
 "numero": 5,
 "titulo": "Correlação entre as seis subescalas do BRUMS",
 "cabecalho": ["Subescala", "Tensão", "Depressão", "Raiva", "Vigor",
               "Fadiga"],
 "linhas": [
  [linha] + [F.br(F.CORRELACAO[(linha, col)], 2)
             if (linha, col) in F.CORRELACAO else ""
             for col in ["Tensão", "Depressão", "Raiva", "Vigor", "Fadiga"]]
  for linha in ["Depressão", "Raiva", "Vigor", "Fadiga", "Confusão"]
 ],
 "nota": ("Nota: correlações entre os fatores da análise fatorial "
          "confirmatória, que ajustou bem ao modelo de seis fatores "
          f"(CFI = {F.br(F.AJUSTE['CFI'], 3)}; "
          f"RMSEA = {F.br(F.AJUSTE['RMSEA'], 3)}). O valor de 0,67 entre "
          "vigor e fadiga é o mais alto do bloco energético e sustenta a "
          "leitura de eixo bipolar. Fonte primária: Tabelas 10 e 11 do "
          "relatório completo."),
},

"perfis": {
 "numero": 6,
 "titulo": ("Os seis perfis de humor: definição, correlatos descritos na "
            "literatura, prevalência normativa e prevalência nesta amostra"),
 "cabecalho": ["Perfil", "Definição pelo padrão das seis subescalas",
               "Correlatos descritos", "Norma (%)", "Dia 1 (%)", "Dia 7 (%)"],
 "linhas": [
  ["Iceberg",
   "Vigor alto; tensão, depressão, raiva, fadiga e confusão baixas",
   "Funcionamento cognitivo saudável e desempenho físico alto; padrão típico "
   "de atletas, o que reduz o seu poder discriminativo",
   F.br(NORMATIVO["Iceberg"], 1), F.br(PERFIS_T["Iceberg"][1], 1),
   F.br(PERFIS_T["Iceberg"][3], 1)],
  ["Superfície", "As seis subescalas próximas da média",
   "Estado indiferenciado, sem sinal claro em nenhuma direção",
   F.br(NORMATIVO["Superfície"], 1), F.br(PERFIS_T["Superfície"][1], 1),
   F.br(PERFIS_T["Superfície"][3], 1)],
  ["Submerso",
   "Tensão, depressão, raiva, fadiga e confusão baixas, como no iceberg, mas "
   "com o vigor também abaixo da média",
   "Ausência de sofrimento declarado com baixa disponibilidade energética",
   F.br(NORMATIVO["Submerso"], 1), F.br(PERFIS_T["Submerso"][1], 1),
   F.br(PERFIS_T["Submerso"][3], 1)],
  ["Barbatana de tubarão",
   "O vigor mais baixo de todos os perfis, com fadiga superior à de qualquer "
   "outro perfil exceto o Everest invertido",
   "Combinação de fadiga alta e vigor baixo, associada a prejuízo de "
   "funcionamento em ambientes que exigem energia e alerta",
   F.br(NORMATIVO["Barbatana de tubarão"], 1),
   F.br(PERFIS_T["Barbatana de tubarão"][1], 1),
   F.br(PERFIS_T["Barbatana de tubarão"][3], 1)],
  ["Iceberg invertido",
   "Vigor abaixo da média com tensão, depressão, raiva, fadiga e confusão "
   "acima da média",
   "Prejuízo de desempenho; indicador clássico de síndrome de overtraining, "
   "risco de transtorno alimentar e queda de desempenho físico",
   F.br(NORMATIVO["Iceberg invertido"], 1),
   F.br(PERFIS_T["Iceberg invertido"][1], 1),
   F.br(PERFIS_T["Iceberg invertido"][3], 1)],
  ["Everest invertido",
   "Vigor baixo, tensão e fadiga altas, e depressão, raiva e confusão muito "
   "altas",
   "O perfil mais negativo; compartilha sintomas de quadros clínicos e "
   "associa-se a déficit cognitivo e a desempenho debilitado",
   F.br(NORMATIVO["Everest invertido"], 1),
   F.br(PERFIS_T["Everest invertido"][1], 1),
   F.br(PERFIS_T["Everest invertido"][3], 1)],
 ],
 "nota": ("Nota: definições, correlatos e prevalências normativas conforme a "
          "amostra A de Parsons-Smith, Terry e Machin (2017). A prevalência "
          "desta amostra vem da classificação sobre escores T, com "
          f"{N_PERFIL[1]} observações no dia 1 e {N_PERFIL[7]} no dia 7. Os "
          "três últimos perfis são os associados a risco à saúde mental."),
},

"caracteristicas": {
 "numero": 7,
 "titulo": ("Correlatos físicos e psicológicos descritos na literatura para "
            "cada perfil, e leitura prática do que a prevalência dele "
            "significa para a comissão técnica"),
 "cabecalho": ["Perfil", "Correlatos físicos", "Correlatos psicológicos e "
               "cognitivos", "Leitura prática"],
 "linhas": [
  ["Iceberg",
   "Desempenho físico alto; menor incidência de lesão entre os seis perfis, "
   "tomado como categoria de referência nos modelos de risco",
   "Funcionamento cognitivo saudável, bem-estar psicológico e prontidão "
   "percebida altos",
   "Estado desejável, mas de baixo poder discriminativo: é o padrão típico de "
   "atletas, bem-sucedidos ou não. Interessa mais a queda da prevalência dele "
   "do que o valor absoluto"],
  ["Superfície",
   "Sem correlato físico específico descrito",
   "Estado indiferenciado, sem sinal claro em nenhuma direção; leitura "
   "ambígua, que exige dado complementar",
   "Não aciona conduta por si. Ganha significado pela direção do movimento: "
   "se vem do iceberg, indica perda de vigor; se vem dos perfis de risco, "
   "indica recuperação"],
  ["Submerso",
   "Baixa disponibilidade energética declarada, sem sinal de sofrimento",
   "Cinco subescalas negativas baixas, como no iceberg, mas vigor abaixo da "
   "média; compatível tanto com recuperação em curso quanto com "
   "desengajamento",
   "Exige distinguir descanso de desligamento. A conduta é conversa "
   "individual, e não ajuste imediato de carga"],
  ["Barbatana de tubarão",
   "O vigor mais baixo dos seis perfis, com fadiga superior à de qualquer "
   "outro exceto o Everest invertido; assinatura psicológica descrita para o "
   "excesso agudo de carga",
   "Prejuízo de funcionamento em ambientes que exigem energia e alerta, sem "
   "elevação marcada de depressão, raiva ou confusão",
   "É o perfil de resposta à carga, e não de sofrimento psíquico. Responde a "
   "ajuste de volume e de intensidade e a recuperação, e é o alvo primário do "
   "manejo na última semana de pré-temporada"],
  ["Iceberg invertido",
   "Queda de desempenho físico; indicador clássico da síndrome de "
   "overtraining; risco aumentado de transtorno alimentar",
   "Vigor abaixo da média com as cinco negativas acima; alteração de humor, "
   "estresse e esgotamento descrita no excesso não funcional de treino",
   "Aciona avaliação individual e reavaliação da progressão de carga do "
   "atleta, e não apenas da sessão"],
  ["Everest invertido",
   "Desempenho debilitado; a maior razão de chances de lesão entre os seis "
   "perfis, de 2,90 em comparação com o iceberg",
   "O padrão mais negativo: depressão, raiva e confusão muito altas; "
   "compartilha sintomas de quadros clinicamente diagnosticáveis; déficit "
   "cognitivo, com pensamento distorcido, concentração reduzida, tempo de "
   "reação mais lento e indecisão; prejuízo de controle inibitório descrito "
   "no quadro instalado de overtraining",
   "Aciona encaminhamento ao serviço de psicologia do clube, "
   "independentemente da carga de treino"],
 ],
 "nota": ("Nota: definições e correlatos originais conforme Parsons-Smith, "
          "Terry e Machin (2017). O risco de lesão e a comparação entre "
          "perfis vêm da coorte de 417 atletas brasileiros de alto "
          "rendimento de Rohlfs e outros (2025), na qual vigor e raiva foram "
          "os principais preditores. Os achados sobre excesso não funcional "
          "de treino, síndrome de overtraining e controle inibitório vêm da "
          "revisão sistemática de onze estudos e 461 atletas de elite de "
          "Valdesalici e outros (2026). A coluna de leitura prática é "
          "interpretação dos autores, aplicada ao contexto deste estudo, e "
          "não achado da literatura citada."),
},

"distribuicao": {
 "numero": 8,
 "titulo": ("Distribuição dos perfis no primeiro e no último dia do "
            "microciclo, com as faixas de significado"),
 "cabecalho": ["Perfil ou faixa", "Dia 1, n (%)", "Dia 7, n (%)",
               "Diferença (p.p.)"],
 "linhas": (
  [[p, f"{PERFIS_T[p][0]} ({F.br(PERFIS_T[p][1], 1)})",
    f"{PERFIS_T[p][2]} ({F.br(PERFIS_T[p][3], 1)})",
    F.sinal(PERFIS_T[p][3] - PERFIS_T[p][1], 1)]
   for p in sorted(PERFIS_T, key=lambda k: -PERFIS_T[k][1])]
  + [["**Faixas de significado**", "", "", ""],
     ["Favorável (iceberg)", F.br(_FAV1, 1), F.br(_FAV7, 1),
      F.sinal(_FAV7 - _FAV1, 1)],
     ["Neutra (superfície e submerso)", F.br(_NEU1, 1), F.br(_NEU7, 1),
      F.sinal(_NEU7 - _NEU1, 1)],
     ["De risco (barbatana, iceberg invertido e Everest invertido)",
      F.br(_RISCO1, 1), F.br(_RISCO7, 1), F.sinal(_RISCO7 - _RISCO1, 1)]]
 ),
 "nota": ("Nota: classificação sobre escores T, com "
          f"{N_PERFIL[1]} observações no dia 1 e {N_PERFIL[7]} no dia 7. As "
          "linhas de faixa trazem apenas o percentual, porque somam perfis "
          "com denominadores idênticos. Pelo critério de Morgan, aplicado em "
          "paralelo sobre escores brutos, a proporção em perfil iceberg passa "
          f"de {F.br(PERFIL_DIA[1][0], 1)}% para {F.br(PERFIL_DIA[7][0], 1)}% "
          "e a de humor perturbado de "
          f"{F.br(PERFIL_DIA[1][1], 1)}% para {F.br(PERFIL_DIA[7][1], 1)}%; "
          "esse critério não classifica nos seis perfis e é discutido na "
          "seção 4.5. Fonte primária: Tabela 12 do estudo de perfil e Tabela "
          "20 do relatório completo."),
},

"sinal": {
 "numero": 9,
 "titulo": ("Predominância diária dos perfis, erro-padrão da proporção e "
            "derivada da série suavizada"),
 "cabecalho": ["Dia", "Iceberg (%)", "Erro-padrão", "Perturbado (%)",
               "n do dia", "Derivada do iceberg (p.p./dia)",
               "Acima do piso de ruído"],
 "linhas": [
  [str(d), F.br(PERFIL_DIA[d][0], 1), F.br(_EP[i], 1),
   F.br(PERFIL_DIA[d][1], 1), str(N_DIA[d]),
   "n.a." if i == 0 else F.sinal(_DERIV[i - 1], 1),
   "n.a." if i == 0 else ("Sim" if abs(_DERIV[i - 1]) > _PISO else "Não")]
  for i, d in enumerate(DIAS)
 ],
 "nota": ("Nota: o erro-padrão é o da proporção binomial, calculado com o n "
          "de cada dia. O piso de ruído é a média desses erros-padrão, de "
          f"{F.br(_PISO, 1)} pontos percentuais, e serve de limiar abaixo do "
          "qual a variação não é distinguível de flutuação amostral. A "
          "derivada é a diferença entre dias consecutivos da série suavizada "
          "por filtro binomial de três pontos, com pesos 1, 2 e 1. Fonte "
          "primária: Tabelas 20 e 52 do relatório completo."),
},
}


# ══════════════════════════════════════════════════════════════ blocos ═══
BLOCOS = [

("h1", "1 INTRODUÇÃO"),
("p", "O humor é um estado afetivo difuso que responde à carga de treino "
      "antes que o desempenho caia, tem custo de coleta próximo de zero e "
      "por isso ocupa lugar central no monitoramento psicológico de atletas "
      "há décadas. O modelo de saúde "
      "mental associou o bem-estar psicológico ao êxito esportivo e a "
      "psicopatologia ao fracasso (Morgan, 1985), e a representação gráfica "
      "desse bem-estar recebeu o nome de perfil iceberg: o vigor emerge "
      "acima da linha de água formada pela média normativa, e tensão, "
      "depressão, raiva, fadiga e confusão permanecem submersas (Morgan, "
      "1980). Duas meta-análises confirmaram que a relação entre humor e "
      "desempenho é modesta e dependente do contexto (Beedie, Terry e Lane, "
      "2000). A evidência recente reposicionou o construto: "
      "mais do que preditor de resultado esportivo, o humor opera hoje como "
      "indicador de triagem de risco à saúde mental e de tensão fisiológica "
      "acumulada (Terry e Parsons-Smith, 2021). Em 417 atletas brasileiros de "
      "alto rendimento, o perfil discriminou risco de lesão, com razão de "
      "chances de 2,90 para o padrão mais negativo (Rohlfs e outros, 2025), "
      "e em seleção nacional de basquetebol as subescalas explicaram 26,0% "
      "da variância de um índice objetivo de eficiência em quadra (Bird e "
      "outros, 2025)."),

("p", "A oposição entre o iceberg e o seu inverso, porém, tem um limite "
      "conhecido: o iceberg é o padrão típico de atletas, bem-sucedidos ou "
      "não, e por isso discrimina desempenho menos do que se afirmou (Terry "
      "e Lane, 2000). Uma equipe apresenta, na mesma semana, estados que a "
      "oposição entre dois padrões não distingue. A resposta veio da análise "
      "de agrupamento: sobre três amostras independentes, com 2364, 2303 e "
      "1865 respostas à Escala de Humor de Brunel, os escores brutos foram "
      "convertidos em escores T de média 50 e desvio-padrão 10 contra a "
      "norma da amostra, e submetidos a análise "
      "hierárquica aglomerativa com distância euclidiana quadrática pelo "
      "método de Ward. A inspeção do dendrograma e do salto nos coeficientes "
      "de fusão indicou a solução de seis grupos, refinada por k-médias e "
      "confirmada por análise discriminante. Emergiram seis agrupamentos "
      "interpretáveis, batizados pelo formato que assumem no gráfico de "
      "perfil: iceberg, superfície, submerso, "
      "barbatana de tubarão, iceberg invertido e Everest invertido "
      "(Parsons-Smith, Terry e Machin, 2017). Os estudos posteriores "
      "substituíram a etapa hierárquica pelo k-médias com sementes fixas nos "
      "centroides publicados, procedimento que testa a reprodutibilidade dos "
      "seis grupos em vez de gerar solução nova a cada amostra (Rohlfs e "
      "outros, 2024; Luojumäki e outros, 2026)."),

("p", "A replicação da solução de seis agrupamentos em populações "
      "distintas é o principal argumento a favor da adoção dela como "
      "linguagem comum do monitoramento. Eles reapareceram em contexto "
      "esportivo e de exercício (Quartiroli e outros, 2018), em "
      "Singapura (Han e outros, 2020), em população lituana e grega (Terry e "
      "Parsons-Smith, 2021, 2022), em 592 triatletas amadores (Parsons-Smith "
      "e outros, 2022) e em 652 finlandeses (Luojumäki e outros, 2026), e o "
      "instrumento recebeu validação psicométrica em lituano (Terry e "
      "outros, 2022), malaio (Lew e outros, 2023), árabe (Sahli e outros, "
      "2023) e grego (Vlachopoulos, Lane e Terry, 2023). No Brasil, a versão "
      "teve a validade fatorial e a confiabilidade das seis subescalas "
      "confirmadas em 898 atletas de base e de elite (Rohlfs e outros, "
      "2023), e a classificação dessa mesma amostra situou 26,5% deles em "
      "algum dos três padrões de risco (Rohlfs, Noce e Wilke, 2024), valor "
      "que é hoje a referência brasileira contra a qual qualquer amostra "
      "nacional passa a ser lida."),

("p", "Cada perfil carrega correlatos próprios, físicos e psicológicos, e é "
      "isso que os torna úteis à comissão técnica. O iceberg reúne "
      "funcionamento cognitivo saudável, desempenho físico alto e a menor "
      "incidência de lesão entre os seis; o superfície descreve estado "
      "indiferenciado; e o submerso compartilha com o iceberg as cinco "
      "negativas baixas, mas com vigor abaixo da média, quadro compatível "
      "tanto com recuperação quanto com desengajamento. A barbatana de "
      "tubarão reúne o vigor mais baixo dos "
      "seis com fadiga superior à de qualquer outro, exceto o Everest "
      "invertido, e essa combinação é a assinatura psicológica descrita para "
      "o excesso de carga. O iceberg invertido é o indicador "
      "clássico da síndrome de overtraining (Budgett, 1998). O Everest "
      "invertido, o mais negativo, acrescenta escores muito altos de "
      "depressão, raiva e confusão e associa-se a déficit cognitivo "
      "(Parsons-Smith, Terry e Machin, 2017) e ao maior risco de lesão "
      "(Rohlfs e outros, 2025). Revisão sistemática de 461 atletas de elite "
      "confirmou que o excesso não funcional de treino e a síndrome de "
      "overtraining alteram humor, estresse, esgotamento e fadiga "
      "(Valdesalici e outros, 2026). Os três últimos reúnem-se sob o rótulo "
      "de perfis de risco, e a prevalência deles é o indicador de triagem "
      "que interessa ao clube (Tabela 7)."),

("p", "O handebol permanece fora desse mapa, e a lacuna é dupla. O "
      "levantamento que conduzimos sobre a produção internacional em "
      "psicologia do esporte no handebol entre 2006 e 2026 reúne 525 "
      "estudos, dos quais apenas 32 aferem humor ou afeto, um único com "
      "desenho longitudinal, e nenhum aplica os seis perfis. O precedente "
      "mais próximo acompanha medidas biológicas e psicológicas ao longo de "
      "uma temporada, sem classificação por perfil (Bresciani e outros, "
      "2010), e o estudo mais citado descreve ansiedade e humor em handebol "
      "de areia, em corte único (Reigal e outros, 2019). A "
      "produção recente caminhou para o monitoramento de carga (Skarbalius, "
      "2026; Struzik, Nadobnik e Stępień-Słodkowska, 2026), e o maior estudo "
      "psicofisiológico da modalidade, com 584 handebolistas de elite, não "
      "encontrou associação entre estado endócrino e perturbação de humor, e "
      "pediu indicadores psicológicos mais sensíveis à tensão fisiológica "
      "(Ratz-Sulyok e outros, 2026). Falta ainda o "
      "pressuposto de qualquer classificação: existem normas para amostras "
      "esportivas heterogêneas (Terry e Lane, 2000), mas nenhuma específica "
      "do handebol, e a versão brasileira foi validada em futebolistas "
      "(Rohlfs, Rotta e Luft, 2008). Sem norma, cada estudo padroniza "
      "dentro da própria amostra, o que impede a comparação entre estudos e "
      "trava o acúmulo de conhecimento na modalidade."),

("p", "Some-se a isso o momento. A última semana de pré-temporada concentra "
      "a maior carga acumulada do ciclo preparatório e termina na véspera da "
      "estreia competitiva, quando o estado psicológico da equipe deixa de "
      "ser indicador de processo e passa a ser condição de partida. É "
      "justamente nesse intervalo que o monitoramento tem mais consequência "
      "prática e menos descrição publicada: os estudos com os seis perfis "
      "são, na quase totalidade, transversais, e dizem quantos atletas "
      "estão em cada perfil, sem dizer quando um atleta migra. Descrever "
      "quais "
      "perfis predominam nessa semana, em que dias o deslocamento acontece e "
      "quanto dele excede a flutuação amostral é o que permite à comissão "
      "técnica agir antes da competição, e não depois dela. É essa a "
      "justificativa deste estudo."),
("h1", "2 OBJETIVO"),
("p", "Descrever o perfil de humor de atletas de handebol masculino de elite "
      "ao longo da última semana de pré-temporada, e caracterizar os perfis "
      "encontrados quanto aos correlatos físicos e psicológicos descritos na "
      "literatura. Especificamente, o estudo pretende:"),
("lista", [
  "caracterizar o comportamento de cada subescala da Escala de Humor de "
  "Brunel nesta população, com atenção à distribuição, ao efeito piso, à "
  "consistência interna e à estabilidade da medida entre dias;",
  "descrever a distribuição das observações nos seis perfis de humor no "
  "primeiro e no último dia da semana, e a proporção de observações em "
  "perfil de risco em cada um deles;",
  "descrever, para cada perfil observado nesta amostra, os correlatos "
  "físicos e psicológicos que a literatura lhe atribui, de modo a traduzir a "
  "prevalência em consequência prática para a comissão técnica;",
  "quantificar a predominância diária dos perfis ao longo dos sete dias, com "
  "separação explícita entre sinal e ruído, e localizar os dias em que a "
  "mudança acontece;",
  "estabelecer percentis de referência do instrumento para a modalidade, "
  "ausentes na literatura.",
]),

("h1", "3 MÉTODO"),
("h2", "3.1 Delineamento e aspectos éticos"),
("p", "Trata-se de estudo observacional, descritivo, longitudinal e "
      "prospectivo, com medidas repetidas intraindividuais, conduzido em "
      "condições reais de treinamento. Não houve aleatorização, grupo de "
      "controle nem manipulação experimental da carga: a equipe treinou "
      "conforme o planejamento da comissão técnica, e o estudo registrou a "
      "resposta psicológica a esse planejamento. A unidade de análise é a "
      "observação, e não o atleta, porque o perfil de humor é um estado e não "
      "um traço. O estudo foi aprovado pelo comitê de ética em pesquisa da "
      "instituição sob o protocolo [inserir número do CAAE], e todos os "
      "participantes assinaram termo de consentimento livre e esclarecido "
      "após esclarecimento verbal e escrito sobre objetivos, procedimentos, "
      "riscos, benefícios e liberdade de retirada a qualquer momento, sem "
      "prejuízo. Os dados foram anonimizados na origem por código numérico, e "
      "nenhum resultado individual foi comunicado à comissão técnica durante "
      "o período de coleta."),
("h2", "3.2 Primeiro contato e recrutamento"),
("p", "O primeiro contato foi feito com a direção do clube e com a comissão "
      "técnica [inserir mês e ano], por meio de reunião presencial em que "
      "foram apresentados os objetivos do estudo, o instrumento, a carga de "
      "resposta exigida do atleta e o compromisso de não interferência na "
      "rotina de treino. Obtida a anuência institucional por carta, seguiu-se "
      "reunião com o elenco, no vestiário, antes de uma sessão de treino, em "
      "que o mesmo conteúdo foi apresentado aos atletas e as dúvidas foram "
      "respondidas. O convite foi feito a todos os atletas do elenco "
      "profissional. Foram critérios de inclusão o vínculo com a equipe "
      "profissional e a participação regular nos treinos do período; foram "
      "critérios de exclusão a lesão que impedisse a participação nos treinos "
      "e a recusa em assinar o termo. Dos atletas convidados, 27 aceitaram e "
      "assinaram o termo, e nenhum retirou o consentimento durante a semana."),
("h2", "3.3 Participantes"),
("p", "A Tabela 1 descreve a amostra. Participaram 27 atletas de handebol "
      f"masculino de primeira divisão, com {F.AMOSTRA['idade']} anos de idade "
      f"e {F.AMOSTRA['experiencia']} anos de experiência na modalidade. A "
      "distribuição por posição foi de 12 armadores, 9 pivôs e 6 alas. "
      "Dezenove atletas, isto é, 70,4% da amostra, completaram as sete "
      "coletas; as ausências decorreram de dispensa, de atendimento no "
      "departamento médico e de compromissos fora do clube, e não houve "
      "desistência do estudo."),
("tab", "amostra"),
("h2", "3.4 Contexto: a última semana de pré-temporada"),
("p", "O período monitorado foi o microciclo de sete dias entre 21 e 27 de "
      "abril de 2024, correspondente à última semana da fase preparatória, "
      "imediatamente anterior ao início da competição. O domingo, dia 1, foi "
      "de repouso completo e serviu de linha de base. Os dias 2, 4 e 7 "
      "combinaram treinamento intervalado de alta intensidade com trabalho "
      "técnico e tático, em duas sessões, com 2,0 a 2,5 horas e frequência "
      "cardíaca de pico entre 181 e 184 batimentos por minuto. Os dias 3, 5 e "
      "6 combinaram trabalho técnico e tático com treinamento de força e, nos "
      "dias 3 e 5, jogo amistoso, em três sessões, com 4,5 a 5,0 horas. A "
      "semana alterna, portanto, dias de alta intensidade e volume reduzido "
      "com dias de volume máximo e intensidade moderada, o que é relevante "
      "para a leitura da série diária apresentada na seção 4.4."),
("h2", "3.5 Instrumento"),
("p", "O humor foi aferido pela versão brasileira da Escala de Humor de "
      "Brunel, traduzida e validada em atletas por Rohlfs, Rotta e Luft "
      "(2008) e derivada da versão original de 24 itens (Terry e outros, "
      "1999, 2003). O instrumento tem seis subescalas de quatro itens cada, "
      "respondidas em escala Likert de cinco pontos, de nada a "
      "extremamente, com amplitude de 0 a 16 pontos por subescala: tensão, "
      "depressão, raiva, vigor, fadiga e confusão. A Perturbação Total do "
      "Humor resume o perfil pela soma das cinco subescalas negativas menos o "
      "vigor, com amplitude teórica de menos 16 a mais 64 pontos, e valores "
      "menores indicam humor mais favorável. A instrução de resposta foi a de "
      "momento presente, e não a de semana anterior. A escolha não é neutra: "
      "o mesmo instrumento produz escores mais altos sob a instrução "
      "retrospectiva, o que torna as duas versões não intercambiáveis para "
      "fins de comparação de prevalência (Rohlfs, Noce e Wilke, 2024)."),
("h2", "3.6 Procedimento de coleta"),
("p", "A coleta seguiu um protocolo fixo ao longo dos sete dias. No dia 1, "
      "domingo de repouso, houve coleta única, tomada como linha de base e "
      "aplicada [inserir período do dia] sem que tivesse havido esforço "
      "físico organizado nas horas anteriores. Nos dias 2 a 7, houve duas "
      "coletas diárias: a primeira pela manhã, antes do início da primeira "
      "sessão do dia, tomada como medida pré-sessão, e a última à noite, ao "
      "fim da última sessão do dia, tomada como medida pós-sessão. O intervalo "
      "entre a última coleta de um dia e a primeira do dia seguinte "
      "corresponde ao período de recuperação noturna, o que permite separar a "
      "variação intradia, atribuível à sessão, da variação entre dias, "
      "atribuível ao acúmulo."),
("p", "As duas coletas diárias foram aplicadas presencialmente, no mesmo "
      "espaço e pelo mesmo pesquisador, sempre antes de qualquer orientação "
      "da comissão técnica, de modo a reduzir a influência de conversa "
      "coletiva sobre a resposta individual. O preenchimento é individual, em "
      "silêncio, e leva de dois a três minutos. Antes da primeira aplicação, "
      "os atletas receberam instrução padronizada sobre a escala de resposta "
      "e sobre o referencial temporal de momento presente, e a mesma "
      "instrução foi repetida a cada coleta em forma abreviada. Questionários "
      "com item em branco foram devolvidos ao atleta na hora para "
      "completamento; nenhum questionário foi excluído por preenchimento "
      "incompleto. Os dados foram transcritos para planilha eletrônica no "
      "mesmo dia e submetidos a dupla conferência por dois pesquisadores "
      "independentes, com resolução de divergência por consulta ao "
      "formulário original."),
("h2", "3.7 Classificação dos perfis"),
("p", "Cada observação recebeu duas classificações independentes. A primeira "
      "aplica o critério de Morgan: há perfil iceberg quando o escore de "
      "vigor supera o de todas as cinco subescalas negativas; há humor "
      "perturbado quando a Perturbação Total do Humor é maior que zero. É um "
      "critério de ordem, que não depende de norma externa."),
("p", "A segunda aplica o critério de Parsons-Smith. O procedimento original "
      "padroniza as seis subescalas em escore T contra normas populacionais e "
      "aplica análise de agrupamento hierárquica aglomerativa com distância "
      "euclidiana quadrática pelo método de Ward, com o número de "
      "agrupamentos verificado por inspeção do gráfico de sedimentação, "
      "seguida de k-médias para refino das fronteiras e de análise "
      "discriminante para confirmação (Parsons-Smith, Terry e Machin, 2017). "
      "Nesta amostra o tamanho não comporta a derivação de agrupamentos "
      "próprios. Os escores das seis subescalas foram convertidos em escore "
      "T, com média 50 e desvio-padrão 10, que é a escala sobre a qual os "
      "seis perfis foram definidos, e cada observação foi atribuída pelo "
      "padrão de forma do perfil, isto é, pela posição relativa do vigor e "
      "das cinco subescalas negativas em relação à linha de 50."),
("p", "Registra-se, por transparência, que uma análise anterior deste mesmo "
      "conjunto de dados classificou as observações por proximidade ao "
      "centroide canônico, sobre escores padronizados dentro da amostra, e "
      "chegou a uma distribuição distinta, com predomínio do perfil "
      "superfície. Uma auditoria das duas classificações mostrou que submerso "
      "e iceberg invertido recebem valores idênticos nas duas regras, nos "
      "dois dias, o que localiza a divergência na fronteira entre perfis e "
      "não nos dados. A regra por proximidade a centroide concentra as "
      "observações no centro da distribuição, que é onde fica o centroide do "
      "perfil superfície, e por isso apaga o deslocamento entre perfis. "
      "Adotou-se a classificação sobre escore T, que segue o procedimento da "
      "literatura e reproduz a forma esperada dos perfis. A limitação que "
      "decorre dessa escolha está na seção 5.7."),
("h2", "3.8 Plano de análise"),
("p0", "O plano de análise está descrito com o detalhe necessário à "
       "reprodução integral do estudo. Ele se organiza em sete blocos, na "
       "ordem em que as perguntas do objetivo foram respondidas: a descrição "
       "das subescalas e das propriedades da medida; o contraste entre o "
       "primeiro e o último dia; a comparação entre os sete dias; a "
       "comparação intradia; a separação entre o nível do grupo e o nível do "
       "atleta; a análise da predominância dos perfis ao longo da semana; e "
       "as decisões gerais de tratamento de dados. O nível de significância "
       "adotado foi de 5% em todos os testes, sempre depois da correção para "
       "múltiplas comparações descrita em 3.8.7."),
("h3", "3.8.1 Descrição das subescalas e propriedades da medida"),
("p", "Cada uma das seis subescalas foi descrita por média, desvio-padrão, "
      "erro-padrão da média, mediana, primeiro e terceiro quartis, intervalo "
      "interquartil, valores mínimo e máximo observados, assimetria, curtose "
      "e percentual de respostas no valor mínimo possível da subescala. A "
      "assimetria e a curtose foram calculadas pelos coeficientes amostrais "
      "de terceiro e quarto momentos, com curtose em excesso, de modo que o "
      "valor zero corresponde à distribuição normal. Adotou-se o critério "
      "convencional de afastamento grave da normalidade em assimetria acima "
      "de 2 em valor absoluto e curtose acima de 7 em valor absoluto."),
("p", "Considera-se presente o efeito piso quando mais de 15% das respostas "
      "caem no valor mínimo possível da escala, e efeito teto quando mais de "
      "15% caem no valor máximo (Terwee e outros, 2007). Como as cinco "
      "subescalas negativas têm o valor mínimo em zero e a amplitude vai de "
      "0 a 16, o efeito piso é o risco relevante nesta população, e ele foi "
      "quantificado subescala por subescala. O efeito piso não é apenas "
      "questão psicométrica: onde ele é alto, a subescala perde margem para "
      "registrar melhora, e a série diária passa a ser interpretável apenas "
      "na direção da piora. Por isso ele é reportado antes de qualquer "
      "comparação entre dias, e não como nota de rodapé."),
("p", "A confiabilidade interna foi estimada por quatro caminhos "
      "convergentes, porque itens ordinais de quatro pontos com distribuição "
      "assimétrica violam os pressupostos do coeficiente mais usado. "
      "Calcularam-se o alfa de Cronbach sobre a matriz de covariâncias de "
      "Pearson; o alfa ordinal e o ômega de McDonald sobre a matriz de "
      "correlações policóricas, apropriada a itens ordinais; e o coeficiente "
      "das duas metades corrigido por Spearman e Brown. Reportou-se ainda a "
      "correlação item-total corrigida de cada um dos quatro itens de cada "
      "subescala, isto é, a correlação do item com a soma dos demais itens "
      "da própria subescala, com o item excluído do total. Divergência entre "
      "o alfa de Pearson e o alfa policórico é lida como indício de que a "
      "assimetria dos itens, e não a falta de coerência entre eles, "
      "responde pelo valor baixo."),
("p", "A estabilidade da medida entre dias foi estimada pelo coeficiente de "
      "correlação intraclasse em modelo de efeitos aleatórios de uma via, "
      "ICC(1,1), que responde quanto de uma leitura isolada é atributo "
      "estável do atleta e quanto é estado do dia. A confiabilidade da média "
      "de sete dias, ICC(1,7), foi obtida pela fórmula de profecia de "
      "Spearman e Brown aplicada ao ICC(1,1). Reportou-se também o ICC(2,1), "
      "em modelo de efeitos mistos de duas vias com o dia como fator, para "
      "separar a variância entre dias da variância entre atletas. A partir "
      "do ICC(1,1) e do desvio-padrão da subescala calcularam-se o "
      "erro-padrão de medida, dado pelo desvio-padrão multiplicado pela raiz "
      "de um menos o ICC, e o menor valor detectável a 95%, dado pelo "
      "erro-padrão de medida multiplicado por 1,96 e pela raiz de dois. O "
      "menor valor detectável é o limiar usado em 3.8.5 para contar quantos "
      "atletas mudaram de fato."),
("p", "A estrutura de seis fatores correlacionados foi testada por análise "
      "fatorial confirmatória sobre a matriz policórica, com estimador de "
      "mínimos quadrados ponderados com média e variância ajustadas, "
      "apropriado a variáveis ordinais, e erro-padrão agrupado por atleta "
      "para respeitar a dependência entre as observações repetidas do mesmo "
      "participante. O ajuste foi avaliado pelo índice de ajuste "
      "comparativo, pelo índice de Tucker e Lewis, pela raiz do erro "
      "quadrático médio de aproximação com intervalo de 90% e pela raiz "
      "padronizada do resíduo médio, com os pontos de corte convencionais de "
      "0,95, 0,95, 0,06 e 0,08. As correlações entre as seis subescalas "
      "foram descritas por matriz de Spearman, escolhida pela assimetria das "
      "distribuições."),
("h3", "3.8.2 Comparação entre o primeiro e o último dia"),
("p", "O contraste entre o dia 1 e o dia 7 é o de maior interesse prático, "
      "porque opõe o estado de repouso, medido em coleta única no domingo, "
      "ao estado de véspera de competição, e responde à pergunta que a "
      "comissão técnica faz: a equipe chega à estreia em que condição, "
      "comparada à condição em que começou a semana."),
("p", "Para as proporções de cada perfil, o contraste é a diferença simples "
      "em pontos percentuais entre os dois dias, acompanhada do erro-padrão "
      "binomial de cada proporção, dado pela raiz de p vezes um menos p "
      "sobre n, com o n de observações válidas daquele dia. A diferença só é "
      "interpretada quando excede o piso de ruído definido em 3.8.6. Não se "
      "aplicou teste de qui-quadrado à tabela de contingência dos seis "
      "perfis por dois dias porque quatro das doze caselas têm frequência "
      "esperada inferior a cinco, o que invalida a aproximação, e porque as "
      "observações não são independentes entre os dois dias: o mesmo atleta "
      "contribui para os dois. A leitura é, portanto, descritiva e "
      "declaradamente descritiva."),
("p", "Para os escores contínuos das seis subescalas e para o escore de "
      "perturbação total do humor, o contraste usa o tamanho de efeito para "
      "medidas pareadas, isto é, a média das diferenças individuais dividida "
      "pelo desvio-padrão dessas diferenças, com intervalo de confiança de "
      "95% obtido por reamostragem com dez mil repetições, procedimento "
      "escolhido por não exigir normalidade das diferenças. A análise é "
      "restrita aos atletas com observação válida nos dois dias, o que evita "
      "comparar composições amostrais diferentes e atribuir à passagem do "
      "tempo o que é efeito de quem respondeu em cada dia. O número de pares "
      "efetivamente disponíveis está declarado na nota de cada tabela."),
("h3", "3.8.3 Comparação entre os sete dias"),
("p", "O efeito do dia sobre cada subescala foi testado por modelo linear "
      "misto com intercepto aleatório por atleta e o dia como fator fixo de "
      "sete níveis. O intercepto aleatório corrige a pseudorreplicação "
      "decorrente das múltiplas observações de cada participante, que na "
      "análise ingênua inflaria os graus de liberdade e, com eles, a taxa de "
      "erro do tipo I. Os graus de liberdade do denominador foram "
      "aproximados pelo método de Satterthwaite. O tamanho de efeito "
      "reportado é o eta² parcial, com a leitura convencional de 0,01 para "
      "efeito pequeno, 0,06 para médio e 0,14 para grande."),
("p", "Do mesmo modelo extraiu-se o coeficiente de correlação intraclasse, "
      "razão entre a variância do intercepto aleatório e a variância total, "
      "que quantifica quanto do escore é atributo do atleta e quanto é "
      "resposta ao dia. Um ICC alto com eta² pequeno significa que os "
      "atletas diferem muito entre si e pouco ao longo da semana, e a "
      "combinação inversa significa o contrário. Os dois indicadores são "
      "reportados lado a lado por isso."),
("p", "As médias diárias reportadas vêm de estimativa em dois passos: as "
      "observações de cada atleta em cada dia são primeiro agregadas na "
      "média daquele atleta naquele dia, e só depois essas médias "
      "individuais são agregadas na média do dia. O procedimento garante que "
      "atletas com mais observações não pesem mais na média do dia, o que "
      "acontece na média bruta quando a adesão varia entre participantes. As "
      "duas séries, bruta e em dois passos, foram calculadas, e a divergência "
      "entre elas está registrada; a série em dois passos é a adotada em "
      "todo o artigo."),
("h3", "3.8.4 Comparação intradia, entre o momento pré e o pós-sessão"),
("p", "A variação dentro da sessão foi estimada pelo contraste entre a "
      "primeira coleta do dia, aplicada antes do início do trabalho, e a "
      "última, aplicada ao término da sessão da noite. Cada par pré e "
      "pós-sessão gera uma diferença individual. Para evitar que um atleta "
      "com seis pares contribua seis vezes e outro com um par contribua uma "
      "vez, as diferenças foram primeiro agregadas na média por atleta, e só "
      "depois submetidas ao teste, de modo que a unidade de análise do teste "
      "é o atleta e o n do teste é o número de atletas com ao menos um par "
      "válido."),
("p", "O tamanho de efeito é o de medidas pareadas, com intervalo de "
      "confiança de 95% por reamostragem, e a significância considera a "
      "correção de Benjamini e Hochberg sobre o conjunto das nove variáveis "
      "testadas. Reportam-se, além do valor pontual, o número de pares que "
      "sustentam cada estimativa e a direção esperada da variação: em vigor "
      "e na medida de recuperação percebida, o aumento é favorável; nas "
      "cinco subescalas negativas e no escore de perturbação total, o "
      "aumento é desfavorável. Essa direção governa a interpretação e a "
      "codificação de cores das figuras, e está declarada porque a leitura "
      "de sinal puramente aritmética inverteria o significado do vigor."),
("h3", "3.8.5 Nível de grupo e nível do atleta"),
("p", "Toda análise foi conduzida em dois níveis, e a distinção é decisiva "
      "para o uso prático. No nível do grupo, o interesse é a média e a "
      "proporção, e a inferência responde se a equipe mudou. No nível do "
      "atleta, o interesse é quantos atletas mudaram, e a resposta exige um "
      "limiar de mudança confiável: a variação individual entre o primeiro e "
      "o último dia só é contada como mudança quando excede o menor valor "
      "detectável a 95% daquela subescala, calculado em 3.8.1. Cada atleta "
      "recebe, para cada subescala, uma de três classificações: mudança "
      "favorável, mudança desfavorável ou variação dentro do erro de medida. "
      "A classificação respeita a direção da subescala, de modo que uma "
      "queda de vigor conta como mudança desfavorável e uma queda de fadiga "
      "conta como favorável."),
("p", "Os dois níveis podem divergir, e a divergência é informativa e não "
      "contraditória: uma média estável pode esconder metade do elenco em "
      "piora e a outra metade em melhora, situação em que a conduta correta "
      "é individual e a leitura de grupo não a indicaria. Por isso as duas "
      "leituras são reportadas juntas, e nenhuma conclusão prática se apoia "
      "apenas na média."),
("h3", "3.8.6 Predominância dos perfis ao longo da semana"),
("p", "A proporção diária de atletas em cada perfil constitui uma série "
      "temporal de sete pontos, e foi tratada como tal, em quatro passos "
      "encadeados: piso de ruído, filtragem, derivada e limiar. A sequência "
      "existe porque a inspeção visual de uma curva de sete pontos com n "
      "pequeno confunde sistematicamente flutuação amostral com tendência, e "
      "o objetivo é dizer não apenas que os perfis mudaram, mas em que dias "
      "a mudança aconteceu e quanto dela excede o acaso."),
("p", "O primeiro passo é a definição do piso de ruído. Cada proporção "
      "diária tem erro-padrão binomial dado pela raiz de p vezes um menos p "
      "sobre n, com o n de atletas que responderam naquele dia, que varia ao "
      "longo da semana. A média desses sete erros-padrão define o piso, de "
      f"{F.br(_PISO, 1)} pontos percentuais nesta amostra. Variação de "
      "magnitude inferior ao piso não é distinguível de flutuação amostral e "
      "não é interpretada, nem no texto nem nas figuras, onde ela aparece "
      "sombreada como faixa de ruído."),
("p", "O segundo passo é a filtragem. Com apenas sete pontos, qualquer "
      "filtro pesado apaga o próprio sinal que se pretende medir, e uma "
      "média móvel de cinco pontos consumiria mais da metade da série. "
      "Aplicou-se, por isso, o filtro binomial de três pontos com pesos 1, 2 "
      "e 1, normalizados por quatro, que é o de menor ordem capaz de atenuar "
      "a oscilação ponto a ponto sem deslocar a posição de máximos e "
      "mínimos, propriedade que uma média móvel simples não tem. As "
      "extremidades da série, o dia 1 e o dia 7, foram preservadas sem "
      "suavização por falta de vizinho, e não por extrapolação, opção que "
      "evita criar valor onde não há dado."),
("p", "O terceiro passo é a derivada. A diferença entre dias consecutivos da "
      "série suavizada estima a taxa de variação diária, em pontos "
      "percentuais por dia, e produz seis derivadas para os sete dias. Cada "
      "derivada é comparada ao piso de ruído, e apenas as que o superam em "
      "valor absoluto são interpretadas. Esse procedimento distingue duas "
      "hipóteses que a inspeção visual da curva bruta confunde: a erosão "
      "gradual, em que todas as derivadas são pequenas e do mesmo sinal, e o "
      "deslocamento por choques, em que poucas derivadas grandes concentram "
      "toda a mudança e as demais formam platô. As duas hipóteses têm "
      "conduta oposta: a erosão pede redução distribuída da carga da semana, "
      "e o deslocamento por choques pede intervenção nos dias específicos "
      "que produzem a queda."),
("p", "O quarto passo é o limiar. Dois limiares foram definidos a priori, "
      "antes da inspeção das séries. O primeiro é o de maioria, em 50%, que "
      "marca o dia em que um perfil deixa de caracterizar a maior parte do "
      "elenco. O segundo é o de inversão, no ponto em que as curvas do "
      "perfil iceberg e de humor perturbado se cruzam, isto é, o momento em "
      "que o padrão desfavorável passa a ser mais frequente que o favorável. "
      "O ponto de cruzamento foi obtido por interpolação linear entre os dois "
      "dias adjacentes das séries suavizadas, e é reportado em fração de "
      "dia, o que permite dizer se a inversão acontece no início ou no fim "
      "do intervalo entre duas coletas."),
("h3", "3.8.7 Decisões gerais de tratamento de dados"),
("p", "Não houve imputação de dado faltante. Cada estimativa usa as "
      "observações efetivamente disponíveis, e o denominador de cada uma "
      "está declarado na nota da tabela correspondente, de modo que o leitor "
      "possa verificar sobre quantas observações e quantos atletas cada "
      "número foi calculado. Os denominadores variam entre análises porque "
      "os critérios de inclusão variam: as análises de subescala usam toda "
      "observação válida, as pareadas usam apenas atletas com registro nos "
      "dois momentos e as de perfil usam apenas questionários com as seis "
      "subescalas completas."),
("p", "A correção para múltiplas comparações seguiu o procedimento de "
      "Benjamini e Hochberg, que controla a taxa de falsas descobertas e é "
      "menos conservador que a correção de Bonferroni, escolha adequada a um "
      "estudo descritivo cujo propósito é gerar hipótese e não confirmá-la. "
      "A correção foi aplicada dentro de cada família de testes, e não sobre "
      "o conjunto do artigo: a família das nove variáveis na comparação "
      "intradia, a família das nove no efeito do dia, e assim por diante. Os "
      "valores reportados são os já corrigidos, e o texto declara em cada "
      "caso quais efeitos sobrevivem à correção e quais não sobrevivem."),
("p", "Nenhum valor foi extrapolado ou estimado por modelo onde havia dado "
      "observado, e nenhum resultado é apresentado sem a origem declarada. "
      "As análises foram conduzidas em R, versão 4.4, com os pacotes psych "
      "para as estimativas de confiabilidade e as correlações policóricas, "
      "lavaan e semTools para a análise fatorial confirmatória, lme4 e "
      "lmerTest para os modelos mistos, e boot para os intervalos por "
      "reamostragem. As figuras foram produzidas em Python, com matplotlib, "
      "a 300 pontos por polegada. Os escores decimais seguem a notação "
      "brasileira, com vírgula decimal."),
]

BLOCOS += [
("h1", "4 RESULTADOS"),
("h2", "4.1 Distribuição das subescalas"),
("p", "As seis subescalas se dividem em dois blocos claros (Tabela 2). O "
      "primeiro é o bloco energético. Vigor e fadiga ocupam a faixa central "
      "da escala, com médias de 5,70 e 5,65 pontos sobre um máximo de 16, "
      "desvios-padrão de 3,12 e 3,89, medianas de 6 e 5 pontos e intervalos "
      "interquartis de 4 e 5 pontos. A assimetria é de 0,03 no vigor e 0,59 "
      "na fadiga, e a curtose é negativa nas duas, de −0,24 e −0,40, o que "
      "descreve distribuições praticamente simétricas e ligeiramente mais "
      "achatadas que a normal. O piso fica em 8,6% no vigor e 7,7% na "
      "fadiga, abaixo do limite de 15%. São, portanto, as duas únicas "
      "subescalas que se comportam como variáveis contínuas bem distribuídas "
      "nesta amostra, e as únicas com margem de medida nas duas direções."),
("p", "O segundo bloco reúne as quatro subescalas de afeto negativo, e o "
      "comportamento delas é oposto. Tensão, depressão, raiva e confusão "
      "ficam junto ao mínimo, com médias de 1,39, 1,00, 1,60 e 0,45 ponto e "
      "medianas de 1, 0, 0 e 0. O intervalo interquartil é de 2 pontos em "
      "tensão e raiva, de 1 ponto em depressão e de zero em confusão, isto é, "
      "metade central das respostas de confusão está inteiramente no valor "
      "mínimo. A assimetria vai de 1,43 em tensão a 3,73 em confusão, e a "
      "curtose de 1,50 a 16,96, valores que ultrapassam com folga os limites "
      "convencionais de 2 e 7 em depressão, raiva e confusão. O escore de "
      "perturbação total do humor herda esse comportamento: média de 4,39, "
      "desvio-padrão de 9,64, mediana de 2, assimetria de 1,48 e curtose de "
      "3,31, com 21,9% das observações no valor mínimo possível."),
("tab", "descritiva"),
("fig", "a1_distribuicao.png", 16.0,
 "Figura 1 - Distribuição observada de cada subescala por percentis (A) e "
 "percentual de respostas no valor mínimo da escala (B)"),
("p", "A Figura 1 mostra o alcance do problema. Em confusão, o percentil 75 "
      "ainda é zero: três quartos das observações estão no mínimo da escala. "
      "Em depressão e raiva, o percentil 50 é zero. Quatro das seis "
      "subescalas ficam entre 49,6% e 80,5% de respostas no piso, mais de "
      "três vezes o limite de 15% a partir do qual o efeito é considerado "
      "presente (Terwee e outros, 2007), o que significa que elas não têm "
      "margem para registrar aumento de sintoma nesta população. Os percentis "
      "observados de todas as subescalas estão na Tabela 3 e constituem a "
      "régua de referência proposta para a modalidade."),
("tab", "percentis"),
("h2", "4.2 Propriedades da medida"),
("p", "A consistência interna varia de modo ordenado entre as subescalas "
      "(Tabela 4). Depressão e raiva encabeçam a lista, com alfa de 0,85 e "
      "0,87, alfa e ômega ordinais de 0,94 e 0,93, duas metades de 0,89 nas "
      "duas e correlação item-total mínima de 0,66, também nas duas. Fadiga "
      "vem em seguida, com alfa de 0,80, ômega ordinal de 0,85 e duas "
      "metades de 0,81, e vigor logo depois, com alfa de 0,68 e ômega "
      "ordinal de 0,80. Confusão fica em 0,66 de alfa e tensão em 0,43, "
      "valor insuficiente por qualquer critério. A queda acompanha "
      "exatamente a ordem do efeito piso, e as correlações item-total "
      "mínimas confirmam o diagnóstico: 0,23 em fadiga, 0,20 em confusão e "
      "0,11 em vigor e em tensão, isto é, ao menos um item de cada uma "
      "dessas quatro subescalas quase não covaria com os demais itens da "
      "própria subescala nesta amostra."),
("p", "Em confusão e tensão a matriz policórica não convergiu, e o "
      "coeficiente ordinal não é estimável. Isso não é falha de "
      "processamento: é consequência direta do efeito piso, porque sem "
      "variação nas respostas não há covariância para estimar. A comparação "
      "com os coeficientes originais do instrumento situa o achado. Tensão "
      "foi publicada com alfa de 0,74 e aqui está em 0,43; confusão foi "
      "publicada com 0,83 e aqui está em 0,66; depressão e raiva, publicadas "
      "com 0,85 e 0,82, estão aqui acima do valor original. A perda, "
      "portanto, é seletiva, e recai sobre as subescalas que esta população "
      "praticamente não pontua."),
("tab", "psicometria"),
("fig", "a1_psicometria.png", 16.0,
 "Figura 2 - Consistência interna de cada subescala (A) e ganho de "
 "estabilidade da média de sete dias sobre a coleta isolada (B)"),
("p", "O painel B da Figura 2 traz o achado de maior consequência prática. "
      "O coeficiente de correlação intraclasse de uma coleta isolada fica em "
      "0,59 na tensão, 0,56 na depressão, 0,55 no vigor, 0,53 na fadiga, "
      "0,35 na confusão e 0,31 na raiva. Nenhuma subescala atinge o patamar "
      "de 0,60 usualmente exigido para uso individual, e a faixa observada, "
      "de 0,31 a 0,59, é compatível com a estabilidade de uma semana "
      "publicada para o instrumento, de 0,26 a 0,53 (Terry e outros, 1999, "
      "2003), o que indica propriedade da medida e não defeito desta "
      "aplicação. Na média de sete dias, pela fórmula de Spearman e Brown, "
      "os mesmos coeficientes sobem para 0,91, 0,90, 0,90, 0,89, 0,79 e "
      "0,76. O ganho é de 0,32 ponto na tensão e de 0,45 ponto na raiva, e "
      "todas as seis passam a superar 0,76. A leitura é direta: uma coleta "
      "isolada do instrumento não descreve o atleta de forma confiável nesta "
      "população, e a média semanal descreve."),
("p", "A estrutura de seis fatores ajustou bem aos dados "
      f"(CFI = {F.br(F.AJUSTE['CFI'], 3)}; "
      f"RMSEA = {F.br(F.AJUSTE['RMSEA'], 3)}). A correlação entre os fatores "
      "(Tabela 5) mostra vigor e fadiga com 0,67, o valor mais alto do bloco "
      "energético, e confusão com tensão em 0,75, o mais alto do bloco de "
      "afeto negativo."),
("tab", "correlacao"),
("h2", "4.3 Prevalência dos seis perfis"),
("p", "No dia de repouso, o perfil iceberg é o mais frequente, com "
      f"{F.br(PERFIS_T['Iceberg'][1], 1)}% das observações, seguido do "
      f"superfície com {F.br(PERFIS_T['Superfície'][1], 1)}%, do Everest "
      f"invertido com {F.br(PERFIS_T['Everest invertido'][1], 1)}%, do "
      f"iceberg invertido com {F.br(PERFIS_T['Iceberg invertido'][1], 1)}%, "
      f"do submerso com {F.br(PERFIS_T['Submerso'][1], 1)}% e da barbatana "
      f"de tubarão com {F.br(PERFIS_T['Barbatana de tubarão'][1], 1)}% "
      "(Tabela 6). Os três perfis associados a risco à saúde mental somam "
      f"{F.br(_RISCO1, 1)}% das observações nesse dia."),
("tab", "perfis"),
("p", "A Tabela 7 traduz cada perfil nos correlatos físicos e psicológicos "
      "que a literatura lhe atribui, e acrescenta a leitura prática que "
      "decorre deles. A separação entre as duas colunas de correlato importa "
      "para a conduta: a barbatana de tubarão é resposta à carga, e responde "
      "a manejo de treino e de recuperação, ao passo que o iceberg invertido "
      "e o Everest invertido carregam sinal psicológico que não se resolve "
      "com ajuste de sessão. Os dois grupos somam-se na faixa de risco, mas "
      "não pedem a mesma conduta, e essa distinção é a principal utilidade "
      "prática de classificar em seis perfis em vez de dois."),
("tab", "caracteristicas"),
("fig", "fig_prevalencia.png", 16.0,
 "Figura 3 - Prevalência de cada perfil na amostra normativa e nesta amostra "
 "(A) e efeito da padronização interna sobre essa prevalência (B)"),
("p", "A comparação com a amostra normativa tem a direção esperada nos dois "
      "extremos. O perfil iceberg fica 11,1 pontos percentuais acima da "
      "norma, o que é coerente com atletas de elite em dia de repouso, e o "
      "iceberg invertido fica praticamente sobre a norma, a 0,8 ponto. Os "
      "perfis submerso e barbatana de tubarão ficam abaixo, em 18,4 e 14,9 "
      "pontos, também coerente com o dia de menor carga da semana. O "
      "afastamento que essa lógica não explica é o do Everest invertido, 11,6 "
      "pontos acima da norma, retomado na seção 5.5."),
("h2", "4.4 Predominância dos perfis ao longo da semana"),
("p", "Do primeiro ao último dia, a proporção de atletas em perfil iceberg "
      f"cai de {F.br(PERFIL_DIA[1][0], 1)}% para {F.br(PERFIL_DIA[7][0], 1)}%, "
      f"perda de {F.br(abs(PERFIL_DIA[7][0] - PERFIL_DIA[1][0]), 1)} pontos "
      "percentuais, e a de humor perturbado sobe de "
      f"{F.br(PERFIL_DIA[1][1], 1)}% para {F.br(PERFIL_DIA[7][1], 1)}%, ganho "
      f"de {F.br(abs(PERFIL_DIA[7][1] - PERFIL_DIA[1][1]), 1)} pontos "
      "(Tabela 9). Pela classificação nos seis perfis, no mesmo intervalo, o "
      "perfil iceberg recua 23,1 pontos percentuais e a barbatana de tubarão "
      "avança 25,9 pontos, que são os dois maiores deslocamentos da "
      "distribuição (Tabela 8)."),
("tab", "distribuicao"),
("fig", "a1_prevalencia_semana.png", 16.0,
 "Figura 4 - Composição do grupo em faixas de significado ao longo da semana "
 "(A) e prevalência dos seis perfis no primeiro e no último dia (B)"),
("p", "A Figura 4 reúne a leitura de grupo. O painel A agrega os seis perfis "
      "em três faixas: favorável, que reúne o iceberg; neutra, que reúne "
      "superfície e submerso; e de risco, que reúne barbatana de tubarão, "
      "iceberg invertido e Everest invertido. As três faixas se movem na "
      f"mesma direção: a favorável cai de {F.br(_FAV1, 1)}% para "
      f"{F.br(_FAV7, 1)}%, a neutra sobe de {F.br(_NEU1, 1)}% para "
      f"{F.br(_NEU7, 1)}% e a de risco sobe de {F.br(_RISCO1, 1)}% para "
      f"{F.br(_RISCO7, 1)}%. Na véspera da competição, quase metade das "
      "observações está em um dos três perfis que a literatura associa a "
      "risco à saúde mental."),
("p", "O painel B mostra que esse aumento não se distribui pelos três perfis "
      "de risco. Ele se concentra na barbatana de tubarão, que passa de "
      f"{PERFIS_T['Barbatana de tubarão'][0]} para "
      f"{PERFIS_T['Barbatana de tubarão'][2]} observações e se torna, "
      "empatada com o superfície, o perfil mais frequente do último dia. O "
      "iceberg invertido e o Everest invertido recuam no mesmo intervalo. A "
      "leitura é específica: o elenco não migra para o sofrimento psíquico, "
      "migra para o esgotamento energético, que é a definição da barbatana de "
      "tubarão."),
("tab", "sinal"),
("fig", "a1_sinal.png", 15.0,
 "Figura 5 - Predominância diária dos dois critérios de Morgan, com a curva "
 "suavizada sobre os valores observados (A), e variação diária do perfil "
 "iceberg contra o ruído amostral (B)"),
("p", "A análise da derivada, no painel B da Figura 5, mostra que a perda não é gradual. Das seis "
      "variações diárias da série suavizada, apenas duas ultrapassam o piso "
      f"de ruído de {F.br(_PISO, 1)} pontos percentuais: a do dia 1 para o "
      f"dia 2, de {F.sinal(_DERIV[0], 1)} pontos, e a do dia 6 para o dia 7, "
      f"de {F.sinal(_DERIV[5], 1)} pontos. Entre elas há um platô: as quatro "
      "variações intermediárias ficam entre "
      f"{F.sinal(min(_DERIV[1:5]), 1)} e {F.sinal(max(_DERIV[1:5]), 1)} "
      "pontos, todas dentro da faixa de flutuação amostral. O padrão é, "
      "portanto, de dois deslocamentos concentrados, e não de erosão contínua."),
("p", "Os dois limiares definidos a priori localizam o mesmo fenômeno. A "
      "inversão entre as duas curvas suavizadas ocorre no dia 1,8, isto é, no "
      "curso do primeiro dia de treinamento intervalado de alta intensidade, "
      "e a partir daí o humor perturbado permanece acima do perfil iceberg em "
      "todos os dias. O limiar de maioria confirma a leitura: o perfil "
      "iceberg caracteriza a maior parte do elenco apenas nos dias 1 e 5, e o "
      "humor perturbado caracteriza a maioria em seis dos sete dias. O dia 5, "
      "único dia de recuperação parcial, sucede um dia de volume máximo sem "
      "componente de alta intensidade."),
("h2", "4.5 Concordância entre os dois critérios de classificação"),
("p", "Os dois critérios não concordam entre si, e a diferença é grande. No "
      "primeiro dia, o critério de Morgan classifica 71,4% das observações "
      "como perfil iceberg, contra 40,5% pelo critério dos seis perfis. A "
      "discrepância é esperada e decorre da definição: o critério de Morgan "
      "exige apenas que o vigor supere as cinco subescalas negativas, "
      "condição que quatro subescalas presas ao piso tornam fácil de "
      "satisfazer, enquanto o critério de Parsons-Smith exige proximidade a "
      "um centroide específico das seis dimensões. Em população com efeito "
      "piso acentuado, o critério de Morgan superestima a prevalência do "
      "padrão favorável, e a magnitude dessa superestimativa, de 30,9 pontos "
      "percentuais no primeiro dia, desaconselha o uso dele como critério "
      "único de triagem."),
]

BLOCOS += [
("h1", "5 DISCUSSÃO"),
("p", "Até onde alcança o levantamento descrito na introdução, este é o "
      "primeiro estudo a aplicar os seis perfis de humor ao handebol e o "
      "primeiro a acompanhá-los dia a dia ao longo de uma semana de "
      "pré-temporada. A discussão que segue organiza-se em torno de cinco "
      "questões, e nenhuma delas tem resposta simples: o que os perfis dizem "
      "sobre esta equipe, por que a perda do padrão favorável se concentra em "
      "dois dias, se o efeito piso é defeito de instrumento ou retrato de "
      "população, se a instabilidade da medida isolada invalida o "
      "monitoramento diário, e o que a comparação com a literatura corrobora "
      "e o que ela contraria."),
("h2", "5.1 O que os perfis dizem sobre esta equipe"),
("p", f"No dia de repouso, os três perfis de risco somam "
      f"{F.br(_RISCO1, 1)}% das observações, isto é, aproximadamente uma em "
      "cada quatro. O número é quase idêntico aos "
      "26,5% relatados na única amostra brasileira classificada pelos mesmos "
      "seis perfis, com 898 atletas de elite e de base de um clube do Rio de "
      "Janeiro (Rohlfs, Noce e Wilke, 2024). A coincidência é notável e "
      "sustenta a validade externa da classificação adotada aqui, com a "
      "ressalva de que a amostra brasileira reúne os dois sexos, uma faixa "
      "etária de 12 a 44 anos e também a instrução de semana anterior, que "
      "produz escores mais altos que a de momento presente."),
("p", f"O que muda a leitura é o dia 7. A faixa de risco sobe de "
      f"{F.br(_RISCO1, 1)}% para {F.br(_RISCO7, 1)}% das observações, um "
      f"ganho de {F.br(_RISCO7 - _RISCO1, 1)} pontos percentuais, e passa a "
      "abranger quase metade do elenco na véspera da competição. O aumento "
      "não se distribui pelos três perfis de risco: ele se concentra na "
      "barbatana de tubarão, que salta de "
      f"{F.br(PERFIS_T['Barbatana de tubarão'][1], 1)}% para "
      f"{F.br(PERFIS_T['Barbatana de tubarão'][3], 1)}% e se torna, empatada "
      "com o superfície, o perfil mais frequente do último dia. Os outros "
      "dois perfis de risco, iceberg invertido e Everest invertido, recuam."),
("p", "Essa concentração é o achado clinicamente mais relevante do estudo, "
      "porque a barbatana de tubarão tem definição própria: é o perfil com o "
      "vigor mais baixo de todos os seis, combinado a fadiga superior à de "
      "qualquer outro perfil exceto o Everest invertido. Ele não é um perfil "
      "de sofrimento psíquico, é um perfil de esgotamento energético, e "
      "corresponde exatamente ao que o eixo vigor e fadiga desta amostra faz "
      "esperar: vigor em queda de 7,61 para 4,49 e fadiga em alta de 3,96 "
      "para 7,46 entre o primeiro e o último dia. A migração dos perfis e o "
      "comportamento das subescalas contam, portanto, a mesma história, por "
      "dois caminhos independentes."),
("p", "A composição por faixas, no painel A da Figura 4, resume o "
      f"movimento. A faixa favorável cai de {F.br(_FAV1, 1)}% para "
      f"{F.br(_FAV7, 1)}%, a neutra sobe de {F.br(_NEU1, 1)}% para "
      f"{F.br(_NEU7, 1)}% e a de risco sobe de {F.br(_RISCO1, 1)}% para "
      f"{F.br(_RISCO7, 1)}%. As três se movem na mesma direção: perda de "
      "prontidão com ganho de risco. Uma versão anterior desta análise, "
      "baseada em classificação por proximidade a centroide sobre escores "
      "padronizados dentro da amostra, indicava faixa de risco estável e "
      "levava à conclusão oposta. A auditoria das classificações do projeto "
      "mostrou que aquela regra concentra as observações no perfil superfície "
      "e apaga o deslocamento; a seção 3.7 registra a decisão."),
("h2", "5.2 Duas quedas, e não uma erosão"),
("p", "O resultado metodologicamente mais interessante do estudo é o da "
      "seção 4.4. A curva bruta do perfil iceberg sugere declínio contínuo ao "
      "longo da semana, e é assim que séries desse tipo costumam ser "
      "descritas. A análise da derivada contra o piso de ruído contradiz essa "
      "leitura: das seis variações diárias, quatro ficam dentro da faixa de "
      "flutuação amostral e apenas duas a ultrapassam, uma no primeiro dia de "
      "alta intensidade e outra na véspera da competição."),
("p", "A interpretação é direta e tem consequência prática. O primeiro "
      "deslocamento corresponde à resposta aguda ao reinício do estímulo "
      "intenso após o repouso, fenômeno já descrito no acompanhamento de "
      "adaptações a regimes rigorosos de treino. O segundo corresponde ao "
      "acúmulo da semana, que se manifesta quando a mesma sessão passa a "
      "custar mais. O platô intermediário indica que a equipe absorveu os "
      "dias de volume máximo sem deslocamento adicional do perfil, o que "
      "sugere que o gatilho do deslocamento é a intensidade, e não o volume. "
      "Essa distinção entre estímulo agudo e acúmulo é precisamente a que o "
      "modelo multicomponente de avaliação do sofrimento de treino propõe "
      "como objeto do monitoramento (Main e Grove, 2009), e a série de perfis "
      "captura as duas com um instrumento de dois minutos."),
("p", "Vale registrar o que a análise não autoriza. Com sete pontos, a "
      "derivada é uma estimativa grosseira, e o piso de ruído derivado do "
      "erro-padrão binomial pressupõe independência entre atletas dentro do "
      "dia, o que é discutível em um elenco que convive. O resultado deve ser "
      "lido como demonstração de que a distinção entre erosão e choque é "
      "acessível a partir de dados de rotina, e não como estimativa precisa "
      "das taxas."),
("h2", "5.3 O efeito piso: defeito do instrumento ou retrato da população?"),
("p", "Quatro subescalas concentram entre 49,6% e 80,5% das respostas no "
      "valor mínimo, mais de três vezes o limite convencional de 15% (Terwee "
      "e outros, 2007). A leitura imediata é a de falha psicométrica, e ela "
      "tem consequências reais: a matriz policórica não converge em duas "
      "subescalas, o alfa da tensão cai a 0,43 e o critério de Morgan passa a "
      "superestimar o padrão favorável em 30,9 pontos percentuais."),
("p", "A leitura alternativa, porém, é a de que o instrumento descreve "
      "corretamente uma população sem sintoma clínico. Atletas de elite "
      "saudáveis, em período preparatório, não têm razão para relatar "
      "depressão, raiva ou confusão elevadas, e a concentração no piso é o "
      "resultado esperado. As duas leituras não se excluem, e a saída não "
      "está em escolher entre elas, e sim em separar os usos: as quatro "
      "subescalas de piso servem à triagem de caso individual atípico, que é "
      "a aplicação para a qual o instrumento demonstrou sensibilidade elevada "
      "em outros contextos, como a triagem de risco de estresse "
      "pós-traumático em militares, com sensibilidade de 100% e "
      "especificidade de 79% para um ponto de corte de perturbação total "
      "(van Wijk e outros, 2013). Elas não servem ao acompanhamento de "
      "variação de carga no dia a dia. A distinção entre triagem e "
      "monitoramento resolve boa parte da aparente contradição."),
("h2", "5.4 A instabilidade da medida isolada: defeito ou propriedade?"),
("p", "Nenhuma subescala atinge 0,60 de estabilidade em uma coleta isolada, "
      "com ICC entre 0,31 e 0,59. Isolado, o número parece condenar o "
      "instrumento. Comparado à literatura, ele deixa de ser anômalo: a "
      "estabilidade de uma semana publicada para o instrumento situa-se entre "
      "0,26 e 0,53, e os próprios autores a descrevem como apropriada para "
      "uma medida de estados afetivos transitórios (Terry e outros, 1999, "
      "2003). O que a nossa estimativa acrescenta é a magnitude do ganho pela "
      "agregação: a média de sete dias leva todas as subescalas acima de "
      "0,76."),
("p", "A implicação é conceitual antes de ser prática. Se a instabilidade é "
      "propriedade do construto, e não erro de medida, então a pergunta "
      "certa não é como tornar a leitura diária confiável, e sim qual "
      "unidade de tempo corresponde à decisão que se quer tomar. Para "
      "decidir sobre a carga do dia seguinte, a leitura do dia é o dado "
      "disponível, e a incerteza dele precisa entrar na decisão. Para decidir "
      "sobre o estado de um atleta, a média móvel é a unidade adequada. O "
      "erro comum na prática de campo é usar a primeira para responder à "
      "segunda."),
("p", "Esse ponto também qualifica a leitura do perfil. O perfil é atribuído "
      "a uma observação isolada e herda dela a instabilidade das subescalas "
      "que o compõem. A prevalência de grupo, que agrega dezenas de "
      "observações, é estável; a classificação de um atleta em um dia não é. "
      "Nenhuma decisão individual deveria repousar sobre uma única "
      "classificação."),
("h2", "5.5 O que a literatura corrobora e o que ela contraria"),
("p", "Três resultados convergem com a literatura. A estrutura de seis "
      "fatores ajustou bem, o que replica a validade estrutural do "
      "instrumento descrita desde a versão original (Terry e outros, 1999, "
      "2003). A consistência interna de depressão e raiva, com ômega ordinal "
      "de 0,94 e 0,93, supera os valores originais de 0,85 e 0,82. E a "
      "correlação de 0,67 entre vigor e fadiga sustenta a leitura de eixo "
      "bipolar de energia, coerente com o papel central que o par ocupa nas "
      "descrições dos seis perfis."),
("p", "Dois resultados divergem. O primeiro é a consistência interna da "
      "tensão, de 0,43 contra 0,74 na versão original, e da confusão, de 0,66 "
      "contra 0,83. A explicação mais parcimoniosa é o efeito piso desta "
      "amostra, ausente nas amostras de validação, que reúnem adolescentes e "
      "adultos de população geral. A alternativa, de que os itens de tensão "
      "funcionem de modo diferente em atletas brasileiros de elite, exigiria "
      "análise de funcionamento diferencial do item que este estudo não "
      "conduziu, e permanece em aberto."),
("p", "O segundo é a prevalência do Everest invertido, de "
      f"{F.br(PERFIS_T['Everest invertido'][1], 1)}% no dia de repouso contra "
      f"{F.br(NORMATIVO['Everest invertido'], 1)}% na amostra normativa, o "
      "maior excesso relativo de toda a distribuição (Figura 3). O Everest "
      "invertido é o perfil mais negativo dos seis e o que a literatura "
      "associa a quadros clinicamente diagnosticáveis, de modo que seis "
      "observações nesse perfil no dia de repouso merecem atenção antes de "
      "serem descartadas como ruído. Duas explicações concorrem e este estudo "
      "não as separa: a amostra pode conter atletas em sofrimento real, ou a "
      "conversão para escore T sobre uma amostra pequena pode alocar ao "
      "centroide extremo observações que uma norma populacional alocaria ao "
      "iceberg invertido. A verificação exige a classificação atleta a atleta, "
      "que os dados brutos permitem e que este estudo não conduziu."),
("p", "A comparação com as duas coortes brasileiras classificadas pelos seis "
      "perfis é o contraponto mais informativo disponível. Na amostra de 898 "
      "atletas de base e de elite de um clube do Rio de Janeiro, 26,5% "
      "ficaram em algum dos três perfis de risco (Rohlfs, Noce e Wilke, "
      f"2024), valor praticamente idêntico aos {F.br(_RISCO1, 1)}% desta "
      "equipe no dia de repouso. A convergência sustenta duas leituras "
      "combinadas: a de que o dia 1 desta série descreve um estado basal "
      "comparável ao de atletas brasileiros medidos fora de janela de carga "
      f"aguda, e a de que os {F.br(_RISCO7, 1)}% da véspera de competição "
      "são afastamento desse basal, e não característica da população. Na "
      "segunda coorte, de 417 atletas de alto rendimento acompanhados ao "
      "longo de um ano, a barbatana de tubarão foi o perfil mais frequente, "
      "com 28,3% (Rohlfs e outros, 2025), valor que coincide com os "
      f"{F.br(PERFIS_T['Barbatana de tubarão'][3], 1)}% do último dia desta "
      "série. A coincidência numérica é notável, mas não é evidência: os "
      "delineamentos diferem, e a coorte brasileira agrega medidas de doze "
      "meses, ao passo que aqui o valor descreve um único dia. O que a "
      "comparação autoriza dizer é que o patamar alcançado por esta equipe na "
      "véspera da estreia equivale ao patamar médio anual de uma amostra "
      "brasileira de alto rendimento, o que é, por si, informação de carga."),
("p", "Dois achados externos ajudam a interpretar a direção do deslocamento. "
      "Em 652 finlandeses classificados pelos mesmos seis perfis, os que se "
      "declararam atletas ficaram sobre-representados no iceberg invertido, "
      "e não na barbatana de tubarão (Luojumäki e outros, 2026), o que "
      "sugere que a assinatura do treinamento crônico difere da assinatura "
      "do acúmulo agudo de uma semana. Esta série descreve a segunda: o "
      "iceberg invertido recua ao longo do microciclo, e é a barbatana de "
      "tubarão que absorve toda a migração. Em seleção nacional de "
      "basquetebol acompanhada por catorze dias de competição internacional, "
      "o padrão de queda conjunta de tensão e de vigor ao longo do período "
      "reproduz a direção observada aqui, com a diferença de que lá o "
      "contexto é competitivo e aqui é preparatório (Bird e outros, 2025). "
      "Os dois estudos reforçam que a leitura correta do achado é de resposta "
      "à carga, e não de deterioração da saúde mental do elenco."),
("p", "Cabe ainda situar o estudo no que existe sobre humor no handebol. O "
      "acompanhamento de uma temporada inteira em handebolistas, com o "
      "instrumento anterior, descreveu variação conjunta de marcadores "
      "biológicos e psicológicos, mas sem classificação por perfil "
      "(Bresciani e outros, 2010). O estudo mais citado da modalidade "
      "descreve ansiedade competitiva e humor em atletas de areia, em corte "
      "único (Reigal e outros, 2019). A produção recente da modalidade "
      "avançou no monitoramento de carga, com séries de percepção de esforço "
      "e de impulso de treino ao longo de temporadas inteiras (Struzik, "
      "Nadobnik e Stępień-Słodkowska, 2026) e com modelos que integram carga "
      "interna, estado neuromuscular e bem-estar percebido (Skarbalius, "
      "2026), mas nenhuma dessas séries carrega o humor estruturado em "
      "perfis. O maior estudo psicofisiológico já conduzido no handebol, com "
      "584 atletas de elite, não encontrou associação entre estado endócrino "
      "e perturbação de humor, e concluiu que os indicadores psicológicos "
      "usados não eram sensíveis o bastante à tensão fisiológica "
      "(Ratz-Sulyok e outros, 2026). A classificação em seis perfis, que "
      "separa a fadiga com vigor baixo do sofrimento psíquico, é uma resposta "
      "possível a essa conclusão, e é o que este estudo oferece. Nenhum dos "
      "trabalhos citados permite comparação direta de prevalência na "
      "modalidade, o que é, em si, a medida do vazio que este estudo começa "
      "a preencher."),
("h2", "5.6 Aplicação prática"),
("p", "Para a comissão técnica, quatro decisões decorrem destes resultados. A "
      "primeira é o que medir: no acompanhamento diário bastam vigor, fadiga "
      "e o índice total, porque as demais subescalas não variam o suficiente "
      "para informar. A segunda é como ler: a média móvel de sete dias, e não "
      "o escore do dia, é a unidade com confiabilidade adequada para decisão "
      "sobre um atleta. A terceira é quando esperar deslocamento: o primeiro "
      "dia de alta intensidade após repouso e a véspera da competição são os "
      "dois momentos em que a mudança ultrapassou o ruído nesta semana, e são "
      "os dois candidatos naturais a ponto de vigilância. A quarta é quando "
      "agir: um atleta classificado em barbatana de tubarão, iceberg "
      "invertido ou Everest invertido em duas leituras consecutivas merece "
      "conversa individual, porque a repetição atenua a instabilidade da "
      "classificação isolada e porque esses três perfis são os que a "
      "literatura associa a risco."),
("h2", "5.7 Limitações"),
("p", "Cinco limitações restringem a generalização. A amostra tem 27 atletas "
      "de uma única equipe, dos quais 19 completaram todas as coletas, e o "
      "período monitorado é um único microciclo, o que concentra a observação "
      "em um momento particular da temporada e impede separar o efeito desta "
      "A classificação por regra de forma sobre escore T não reproduz a "
      "análise de agrupamento original: o procedimento indicado para amostras "
      "deste tamanho é a k-médias semeada com os centroides canônicos, "
      "adotada na amostra brasileira de referência (Rohlfs, Noce e Wilke, "
      "2024), e a diferença entre os procedimentos ainda não foi quantificada "
      "nestes dados. A conversão para escore T foi feita sobre a própria "
      "amostra, na ausência de normas da modalidade, o que torna a linha de "
      "50 uma referência interna e não populacional. A classificação existe "
      "apenas para o primeiro e o último dia, de modo que a curva diária dos "
      "perfis permanece por calcular. A amostra é masculina, o que impede "
      "extensão aos achados de sexo relatados na literatura. E o estudo não "
      "mediu desempenho, de modo que nenhuma afirmação sobre consequência "
      "competitiva dos perfis é sustentada por estes dados."),

("h1", "6 CONCLUSÃO"),
("p", "Em atletas de handebol masculino de elite, na última semana de "
      "pré-temporada, os seis perfis de humor descritos na literatura são "
      "identificáveis. No dia de repouso, o perfil iceberg predomina, com "
      f"{F.br(PERFIS_T['Iceberg'][1], 1)}% das observações, e os três perfis "
      f"de risco somam {F.br(_RISCO1, 1)}%, valor quase idêntico ao da única "
      "amostra brasileira classificada pelo mesmo critério. Na véspera da "
      "competição o quadro se inverte: o iceberg cai para "
      f"{F.br(PERFIS_T['Iceberg'][3], 1)}%, a barbatana de tubarão sobe de "
      f"{F.br(PERFIS_T['Barbatana de tubarão'][1], 1)}% para "
      f"{F.br(PERFIS_T['Barbatana de tubarão'][3], 1)}% e passa a dividir a "
      f"primeira posição, e a faixa de risco alcança {F.br(_RISCO7, 1)}% das "
      "observações."),
("p", "Ao longo da semana, a proporção de atletas em perfil iceberg cai 38,8 "
      "pontos percentuais, e a análise da derivada mostra que essa perda se "
      "concentra em dois dias, o primeiro de alta intensidade e a véspera da "
      "competição, com um platô entre eles. Quatro das seis subescalas "
      "apresentam efeito piso acima de 49% e não têm margem de medida útil "
      "para o acompanhamento diário, ainda que preservem utilidade para "
      "triagem de caso individual. Nenhuma subescala é confiável em uma "
      "leitura isolada, em faixa compatível com a estabilidade publicada do "
      "instrumento, e todas passam a ser na média de sete dias. Os percentis "
      "de referência apresentados aqui são a primeira régua específica da "
      "modalidade e são a contribuição de uso imediato deste estudo."),

("h1", "REFERÊNCIAS"),
("nota", "BEEDIE, C. J.; TERRY, P. C.; LANE, A. M. The profile of mood states "
         "and athletic performance: two meta-analyses. Journal of Applied "
         "Sport Psychology, v. 12, n. 1, p. 49-68, 2000."),
("nota", "BIRD, S. P. e outros. Wellness, mood, sleep, and performance in a "
         "women's national basketball team during international "
         "competition. Journal of Human Kinetics, v. 96, p. 163-175, "
         "2025."),
("nota", "BRESCIANI, G. e outros. Monitoring biological and psychological "
         "measures throughout an entire season in male handball players. "
         "European Journal of Sport Science, v. 10, n. 6, p. 377-384, 2010."),
("nota", "BUDGETT, R. Fatigue and underperformance in athletes: the "
         "overtraining syndrome. British Journal of Sports Medicine, v. 32, "
         "n. 2, p. 107-110, 1998."),
("nota", "HAN, C. S. Y. e outros. Mood profiling in Singapore: cross-cultural "
         "validation and potential applications of mood profile clusters. "
         "Frontiers in Psychology, v. 11, art. 665, 2020."),
("nota", "LANE, A. M.; TERRY, P. C. The nature of mood: development of a "
         "conceptual model with a focus on depression. Journal of Applied "
         "Sport Psychology, v. 12, n. 1, p. 16-33, 2000."),
("nota", "LEW, P. C. F. e outros. Cross-cultural validation of the Malaysian "
         "Mood Scale and tests of between-group mood differences. "
         "International Journal of Environmental Research and Public "
         "Health, v. 20, n. 4, art. 3348, 2023."),
("nota", "LUOJUMÄKI, R. J. e outros. Exploring mood profile clusters across "
         "physical activity level, gender and age in a Finnish population. "
         "European Journal of Sport Science, v. 26, n. 2, art. e70131, "
         "2026."),
("nota", "MAIN, L. C.; GROVE, J. R. A multi-component assessment model for "
         "monitoring training distress among athletes. European Journal of "
         "Sport Science, v. 9, n. 4, p. 195-202, 2009."),
("nota", "MORGAN, W. P. Test of champions: the iceberg profile. Psychology "
         "Today, v. 14, p. 92-108, 1980."),
("nota", "MORGAN, W. P. Selected psychological factors limiting performance: "
         "a mental health model. In: CLARKE, D. H.; ECKERT, H. M. (org.). "
         "Limits of human performance. Champaign: Human Kinetics, 1985. "
         "p. 70-80."),
("nota", "PARSONS-SMITH, R. L.; TERRY, P. C.; MACHIN, M. A. Identification "
         "and description of novel mood profile clusters. Frontiers in "
         "Psychology, v. 8, art. 1958, 2017."),
("nota", "PARSONS-SMITH, R. L. e outros. Mood profiles of amateur "
         "triathletes: implications for mental health and performance. "
         "Frontiers in Psychology, v. 13, art. 925992, 2022."),
("nota", "QUARTIROLI, A. e outros. Cross-cultural validation of mood profile "
         "clusters in a sport and exercise context. Frontiers in Psychology, "
         "v. 9, art. 1949, 2018."),
("nota", "RATZ-SULYOK, F. Z. e outros. Associations between endocrine status "
         "and stress, mood and psychosomatic status in elite handball "
         "players. Sports, v. 14, n. 7, art. 289, 2026."),
("nota", "REIGAL, R. E. e outros. Psychological profile, competitive anxiety, "
         "moods and self-efficacy in beach handball players. International "
         "Journal of Environmental Research and Public Health, v. 17, n. 1, "
         "art. 241, 2019."),
("nota", "ROHLFS, I. C. P. M.; NOCE, F.; WILKE, C. F. Prevalence of specific "
         "mood profile clusters among elite and youth athletes at a Brazilian "
         "sports club. Sports, v. 12, n. 7, art. 195, 2024."),
("nota", "ROHLFS, I. C. P. M.; ROTTA, T. M.; LUFT, C. D. B. A Escala de Humor "
         "de Brunel (BRUMS): instrumento para detecção precoce da síndrome do "
         "excesso de treinamento. Revista Brasileira de Medicina do Esporte, "
         "v. 14, n. 3, p. 176-181, 2008."),
("nota", "ROHLFS, I. C. P. M. e outros. Psychometric characteristics of the "
         "Brazil Mood Scale among youth and elite athletes using two "
         "response time frames. Sports, v. 11, n. 12, art. 244, 2023."),
("nota", "ROHLFS, I. C. P. M. e outros. Mood states, injury status, and "
         "countermovement jump performance in Brazilian high-level sports. "
         "Sports, v. 13, n. 9, art. 303, 2025."),
("nota", "SAHLI, H. e outros. Testing the psychometric properties of an "
         "Arabic version of the Brunel Mood Scale among physical education "
         "students. European Journal of Investigation in Health, Psychology "
         "and Education, v. 13, n. 8, p. 1539-1552, 2023."),
("nota", "SKARBALIUS, A. Integrated monitoring of training and sport "
         "performance throughout an entire handball season: practical "
         "applications in semi-professional female players. Frontiers in "
         "Sports and Active Living, v. 8, art. 1869707, 2026."),
("nota", "STRUZIK, A.; NADOBNIK, J.; STĘPIEŃ-SŁODKOWSKA, M. TRIMP and "
         "session-RPE monitoring in elite women's handball: a full-season "
         "descriptive analysis. Scientific Reports, v. 16, n. 1, art. "
         "53134, 2026."),
("nota", "TERRY, P. C. The efficacy of mood state profiling with elite "
         "performers: a review and synthesis. The Sport Psychologist, v. 9, "
         "n. 3, p. 309-324, 1995."),
("nota", "TERRY, P. C.; LANE, A. M. Normative values for the profile of mood "
         "states for use with athletic samples. Journal of Applied Sport "
         "Psychology, v. 12, n. 1, p. 93-109, 2000."),
("nota", "TERRY, P. C.; LANE, A. M.; FOGARTY, G. J. Construct validity of the "
         "Profile of Mood States-Adolescents for use with adults. Psychology "
         "of Sport and Exercise, v. 4, n. 2, p. 125-139, 2003."),
("nota", "TERRY, P. C. e outros. Development and validation of a mood measure "
         "for adolescents. Journal of Sports Sciences, v. 17, n. 11, "
         "p. 861-872, 1999."),
("nota", "TERRY, P. C. e outros. Validation of a Lithuanian-language version "
         "of the Brunel Mood Scale: the BRUMS-LTU. International Journal of "
         "Environmental Research and Public Health, v. 19, n. 8, art. 4867, "
         "2022."),
("nota", "TERRY, P. C.; PARSONS-SMITH, R. L. Mood profiling for sustainable "
         "mental health among athletes. Sustainability, v. 13, n. 11, art. "
         "6116, 2021."),
("nota", "TERRY, P. C.; PARSONS-SMITH, R. L. Physical activity and healthy "
         "habits influence mood profile clusters in a Lithuanian population. "
         "Sustainability, v. 14, n. 16, art. 10006, 2022."),
("nota", "TERWEE, C. B. e outros. Quality criteria were proposed for "
         "measurement properties of health status questionnaires. Journal of "
         "Clinical Epidemiology, v. 60, n. 1, p. 34-42, 2007."),
("nota", "VALDESALICI, A. e outros. Effects of non-functional overreaching "
         "and overtraining syndrome on psychological and cognitive "
         "functioning in elite athletes: a systematic review. Psychology of "
         "Sport and Exercise, v. 84, art. 103079, 2026."),
("nota", "VLACHOPOULOS, S. P.; LANE, A. M.; TERRY, P. C. A Greek translation "
         "of the Brunel Mood Scale: initial validation among exercise "
         "participants and inactive adults. Sports, v. 11, n. 12, art. 234, "
         "2023."),
("nota", "VAN WIJK, C. H. e outros. The Brunel Mood Scale as a screening tool "
         "for post-traumatic stress risk in military populations. Military "
         "Medicine, v. 178, n. 4, p. 372-376, 2013."),
]
