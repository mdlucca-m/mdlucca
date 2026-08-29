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
from dados import DIAS, N_DIA, PARSONS, PERFIL_DIA  # noqa: E402

NORMATIVO = {"Iceberg": 29.4, "Submerso": 25.5, "Barbatana tubarão": 17.3,
             "Superfície": 14.8, "Iceberg invertido": 10.3,
             "Everest invertido": 2.7}

TITULO = ("Perfil de humor em atletas de handebol de elite na última semana "
          "de pré-temporada: os seis perfis e suas características")
SUBTITULO = ("Estudo observacional descritivo de um microciclo de sete dias "
             "com duas coletas diárias")

_RISCO = sum(PARSONS[k][0] for k in
             ("Barbatana tubarão", "Iceberg invertido", "Everest invertido"))

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
  "nesta população. Os três perfis de risco somaram 19,9% das observações, "
  "contra 26,5% da única amostra brasileira classificada pelo mesmo critério. "
  "A proporção de atletas em perfil iceberg caiu de 71,4% para 32,6% ao longo "
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
               "Correlatos descritos", "Norma (%)", "Amostra (%)"],
 "linhas": [
  ["Iceberg",
   "Vigor alto; tensão, depressão, raiva, fadiga e confusão baixas",
   "Funcionamento cognitivo saudável e desempenho físico alto; padrão típico "
   "de atletas, o que reduz o seu poder discriminativo",
   F.br(29.4, 1), F.br(PARSONS["Iceberg"][0], 1)],
  ["Submerso",
   "Tensão, depressão, raiva, fadiga e confusão baixas, como no iceberg, mas "
   "com o vigor também abaixo da média",
   "Ausência de sofrimento declarado com baixa disponibilidade energética",
   F.br(25.5, 1), F.br(PARSONS["Submerso"][0], 1)],
  ["Barbatana de tubarão",
   "O vigor mais baixo de todos os perfis, com fadiga superior à de qualquer "
   "outro perfil exceto o Everest invertido",
   "Combinação de fadiga alta e vigor baixo, associada a prejuízo de "
   "funcionamento em ambientes que exigem energia e alerta",
   F.br(17.3, 1), F.br(PARSONS["Barbatana tubarão"][0], 1)],
  ["Superfície", "As seis subescalas próximas da média",
   "Estado indiferenciado, sem sinal claro em nenhuma direção",
   F.br(14.8, 1), F.br(PARSONS["Superfície"][0], 1)],
  ["Iceberg invertido",
   "Vigor abaixo da média com tensão, depressão, raiva, fadiga e confusão "
   "acima da média",
   "Prejuízo de desempenho; indicador clássico de síndrome de overtraining, "
   "risco de transtorno alimentar e queda de desempenho físico",
   F.br(10.3, 1), F.br(PARSONS["Iceberg invertido"][0], 1)],
  ["Everest invertido",
   "Vigor baixo, tensão e fadiga altas, e depressão, raiva e confusão muito "
   "altas",
   "O perfil mais negativo; compartilha sintomas de quadros clínicos e "
   "associa-se a déficit cognitivo e a desempenho debilitado",
   F.br(2.7, 1), F.br(PARSONS["Everest invertido"][0], 1)],
 ],
 "nota": ("Nota: definições, correlatos e prevalências normativas conforme a "
          "amostra A de Parsons-Smith, Terry e Machin (2017), sobre escores "
          "T de população geral. A prevalência desta amostra usa padronização "
          "dentro da própria amostra, na ausência de normas de escore T para "
          "handebol, e por isso não é diretamente comparável à norma; a "
          "Figura 3 quantifica essa diferença. Os três últimos perfis são os "
          "associados a risco à saúde mental."),
},

"distribuicao": {
 "numero": 7,
 "titulo": ("Distribuição dos perfis no primeiro e no último dia do "
            "microciclo e nos dois tipos de dia"),
 "cabecalho": ["Perfil", "Global (%)", "Dia 1 (%)", "Dia 7 (%)",
               "Diferença (p.p.)", "Dias de HIIT (%)", "Dias sem HIIT (%)"],
 "linhas": [[nome, F.br(v[0], 1), F.br(v[1], 1), F.br(v[2], 1),
             F.sinal(v[2] - v[1], 1), F.br(v[3], 1), F.br(v[4], 1)]
            for nome, v in PARSONS.items()],
 "nota": ("Nota: pelo critério de Morgan, aplicado em paralelo, a proporção "
          f"de atletas em perfil iceberg passa de {F.br(PERFIL_DIA[1][0], 1)}% "
          f"no dia 1 para {F.br(PERFIL_DIA[7][0], 1)}% no dia 7, e a de humor "
          f"perturbado de {F.br(PERFIL_DIA[1][1], 1)}% para "
          f"{F.br(PERFIL_DIA[7][1], 1)}%. Os dois critérios não são "
          "equivalentes: o de Morgan exige apenas que o vigor supere as cinco "
          "negativas, enquanto o de Parsons-Smith exige proximidade a um "
          "centroide específico das seis dimensões. Fonte primária: Tabelas "
          "20 e 21 do relatório completo."),
},

"sinal": {
 "numero": 8,
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
("p", "O humor responde à carga de treino antes que o desempenho caia, tem "
      "custo de coleta próximo de zero e por isso ocupa lugar central no "
      "monitoramento psicológico de atletas há mais de quatro décadas. O "
      "modelo de saúde mental propôs que o bem-estar psicológico se associa "
      "ao êxito esportivo, e a psicopatologia ao fracasso (Morgan, 1985). A "
      "representação gráfica desse bem-estar recebeu o nome de perfil "
      "iceberg: o vigor emerge acima da linha de água formada pela média "
      "normativa, e tensão, depressão, raiva, fadiga e confusão permanecem "
      "submersas (Morgan, 1980). Uma versão mais pronunciada, com vigor acima "
      "do percentil 60 e as cinco negativas abaixo do percentil 40, recebeu o "
      "nome de perfil Everest, e o padrão oposto, com vigor baixo e negativas "
      "altas, o de iceberg invertido, associado a prejuízo de desempenho "
      "(Terry, 1995). Duas meta-análises confirmaram que a relação entre "
      "humor e desempenho existe, mas é modesta e depende do contexto "
      "(Beedie, Terry e Lane, 2000), e o modelo conceitual que se seguiu "
      "atribuiu ao humor deprimido o papel de moderador do efeito da raiva e "
      "da tensão sobre o desempenho (Lane e Terry, 2000)."),
("p", "A dicotomia entre o iceberg e o seu inverso, porém, tem um limite "
      "conhecido. O perfil iceberg é o padrão típico de atletas, "
      "bem-sucedidos ou não, e por isso discrimina desempenho menos do que se "
      "afirmou (Terry e Lane, 2000). Uma equipe apresenta, na mesma semana, "
      "estados que a oposição entre dois padrões não distingue. A resposta a "
      "esse limite veio da análise de agrupamento. Sobre três amostras "
      "independentes, com 2364, 2303 e 1865 respostas à Escala de Humor de "
      "Brunel, a análise hierárquica aglomerativa com distância euclidiana "
      "quadrática pelo método de Ward, refinada por k-médias e confirmada por "
      "análise discriminante, identificou seis agrupamentos distintos e "
      "teoricamente interpretáveis: iceberg, superfície, submerso, barbatana "
      "de tubarão, iceberg invertido e Everest invertido (Parsons-Smith, "
      "Terry e Machin, 2017). Os seis foram replicados em contexto esportivo "
      "e de exercício (Quartiroli e outros, 2018), em Singapura (Han e "
      "outros, 2020), em população lituana e grega (Terry e Parsons-Smith, "
      "2021, 2022) e, com a versão brasileira do instrumento, em 898 atletas "
      "de elite e de base de um clube do Rio de Janeiro (Rohlfs, Noce e "
      "Wilke, 2024). A estabilidade da solução de seis agrupamentos em "
      "populações tão distintas é o principal argumento a favor da adoção "
      "dela como linguagem comum do monitoramento."),
("p", "Cada perfil carrega correlatos próprios, físicos e psicológicos, e é "
      "isso que os torna úteis à comissão técnica. O iceberg associa-se a "
      "funcionamento cognitivo saudável e a desempenho físico alto. O perfil "
      "superfície descreve um estado indiferenciado, sem sinal em nenhuma "
      "direção. O perfil submerso compartilha com o iceberg as cinco "
      "subescalas negativas baixas, mas tem também o vigor abaixo da média, "
      "isto é, ausência de sofrimento com pouca energia disponível. A "
      "barbatana de tubarão reúne o vigor mais baixo de todos os perfis com "
      "fadiga superior à de qualquer outro, exceto o Everest invertido, e "
      "essa combinação de fadiga alta com vigor baixo é preocupação "
      "estabelecida em ambientes que exigem energia e alerta. O iceberg "
      "invertido é o indicador clássico da síndrome de overtraining "
      "(Budgett, 1998) e associa-se a risco de transtorno alimentar e a queda "
      "de desempenho físico. O Everest invertido, o mais negativo dos seis, "
      "acrescenta ao padrão anterior escores muito altos de depressão, raiva "
      "e confusão, compartilha sintomas de quadros clinicamente "
      "diagnosticáveis e associa-se a déficit cognitivo, com pensamento "
      "distorcido, concentração reduzida, tempo de reação mais lento e "
      "indecisão (Parsons-Smith, Terry e Machin, 2017). Os três últimos "
      "reúnem-se sob o rótulo de perfis de risco, e a prevalência deles é o "
      "indicador de triagem que interessa ao clube."),
("p", "O handebol permanece fora desse mapa, e a lacuna é dupla. O "
      "levantamento que conduzimos sobre a produção internacional em "
      "psicologia do esporte no handebol entre 2006 e 2026 reúne 525 estudos, "
      "dos quais apenas 32 aferem humor ou afeto, um único com desenho "
      "longitudinal, e nenhum aplica os seis perfis. O precedente mais "
      "próximo acompanha medidas biológicas e psicológicas ao longo de uma "
      "temporada em handebolistas, com o instrumento anterior e sem "
      "classificação por perfil (Bresciani e outros, 2010), e o estudo "
      "psicológico mais citado da modalidade descreve ansiedade competitiva e "
      "humor em atletas de handebol de areia, em corte único (Reigal e "
      "outros, 2019). Falta também o pressuposto de qualquer classificação: "
      "existem normas de escore para amostras esportivas heterogêneas (Terry "
      "e Lane, 2000), mas nenhuma específica do handebol, e a versão "
      "brasileira do instrumento foi validada em futebolistas (Rohlfs, Rotta "
      "e Luft, 2008). A ausência de norma obriga cada estudo a padronizar "
      "dentro da própria amostra, o que impede a comparação entre estudos e "
      "trava o acúmulo de conhecimento na modalidade."),
("p", "Some-se a isso o momento. A última semana de pré-temporada concentra "
      "a maior carga acumulada do ciclo preparatório e termina na véspera da "
      "estreia competitiva, quando o estado psicológico da equipe deixa de "
      "ser indicador de processo e passa a ser condição de partida. É "
      "justamente nesse intervalo que o monitoramento tem mais consequência "
      "prática e menos descrição publicada. Descrever quais perfis "
      "predominam nessa semana, quanto eles se deslocam e em que dias o "
      "deslocamento acontece é o que permite à comissão técnica agir antes da "
      "competição, e não depois dela."),

("h1", "2 OBJETIVO"),
("p", "Descrever o perfil de humor de atletas de handebol masculino de elite "
      "ao longo da última semana de pré-temporada. Especificamente, o estudo "
      "pretende: caracterizar o comportamento de cada subescala da Escala de "
      "Humor de Brunel nesta população, com atenção ao efeito piso, à "
      "consistência interna e à estabilidade da medida entre dias; descrever "
      "a distribuição dos seis perfis de humor e a proporção de observações "
      "em perfil de risco; quantificar a predominância diária dos perfis ao "
      "longo dos sete dias, com separação explícita entre sinal e ruído; e "
      "estabelecer percentis de referência do instrumento para a modalidade."),

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
      "Nesta amostra não há normas de escore T para handebol de elite, e 27 "
      "atletas não comportam a derivação de agrupamentos própria. As seis "
      "subescalas foram, portanto, padronizadas dentro da própria amostra, e "
      "cada observação foi atribuída ao agrupamento cujo centroide canônico "
      "está a menor distância euclidiana sobre as seis dimensões "
      "padronizadas. Essa decisão está declarada aqui porque afeta "
      "diretamente a prevalência relatada na seção 4.3, e é discutida na "
      "seção 5."),
("h2", "3.8 Plano de análise"),
("h3", "3.8.1 Descrição das subescalas e propriedades da medida"),
("p", "As subescalas foram descritas por média, desvio-padrão, mediana, "
      "intervalo interquartil, assimetria, curtose e percentual de respostas "
      "no valor mínimo. Considera-se presente o efeito piso quando mais de "
      "15% das respostas caem no valor mínimo possível (Terwee e outros, "
      "2007). A confiabilidade interna foi estimada pelo alfa de Cronbach, "
      "pelo alfa e pelo ômega ordinais sobre matriz policórica e pelo método "
      "das duas metades, com correlação item-total corrigida por subescala. A "
      "estabilidade entre dias foi estimada pelo coeficiente de correlação "
      "intraclasse de uma coleta isolada, ICC(1,1), e da média de sete dias, "
      "ICC(1,7), esta pela fórmula de Spearman e Brown. A estrutura de seis "
      "fatores foi testada por análise fatorial confirmatória com estimador "
      "robusto para dados ordinais e erro-padrão agrupado por atleta."),
("h3", "3.8.2 Comparação entre o primeiro e o último dia"),
("p", "O contraste entre o dia 1 e o dia 7 é o de maior interesse prático, "
      "porque opõe o estado de repouso ao estado de véspera de competição. "
      "Para as proporções de cada perfil, o contraste é a diferença em pontos "
      "percentuais, acompanhada do erro-padrão binomial de cada proporção. "
      "Para os escores contínuos, o contraste usa o tamanho de efeito para "
      "medidas pareadas, restrito aos atletas com observação válida nos dois "
      "dias, o que evita a comparação entre composições amostrais "
      "diferentes."),
("h3", "3.8.3 Comparação entre os sete dias"),
("p", "O efeito do dia foi testado por modelo misto com intercepto aleatório "
      "por atleta, o que corrige a pseudorreplicação decorrente das múltiplas "
      "observações de cada participante, com eta² parcial como tamanho de "
      "efeito e correção de Benjamini e Hochberg para múltiplas comparações. "
      "As médias diárias reportadas vêm de estimativa em dois passos, que "
      "agrega primeiro por atleta e só depois por dia, de modo que atletas com "
      "mais observações não pesam mais na média do dia."),
("h3", "3.8.4 Comparação intradia, entre o momento pré e o pós-sessão"),
("p", "A variação dentro da sessão foi estimada pelo contraste entre a "
      "primeira e a última coleta de cada dia de treino. Para evitar que um "
      "atleta com seis pares contribua seis vezes e outro com um par "
      "contribua uma vez, as diferenças foram primeiro agregadas por atleta e "
      "só depois submetidas ao teste, com tamanho de efeito para medidas "
      "pareadas e intervalo de confiança de 95%. A significância considera a "
      "correção de Benjamini e Hochberg."),
("h3", "3.8.5 Nível de grupo e nível do atleta"),
("p", "Toda análise foi conduzida em dois níveis. No nível do grupo, o "
      "interesse é a média e a proporção, e a inferência responde se a equipe "
      "mudou. No nível do atleta, o interesse é quantos atletas mudaram, e a "
      "resposta exige um limiar de mudança confiável: a variação individual "
      "só é contada quando excede o menor valor detectável a 95%, calculado a "
      "partir do erro-padrão de medida e do coeficiente de correlação "
      "intraclasse da subescala. Os dois níveis podem divergir, e a "
      "divergência é informativa: uma média estável pode esconder metade do "
      "elenco em piora e a outra metade em melhora."),
("h3", "3.8.6 Predominância dos perfis ao longo da semana"),
("p", "A proporção diária de atletas em cada perfil constitui uma série "
      "temporal de sete pontos, e foi tratada como tal. O primeiro passo é a "
      "definição do piso de ruído. Cada proporção diária tem erro-padrão "
      "binomial dado pela raiz de p vezes um menos p sobre n, com o n de "
      "atletas daquele dia; a média desses erros-padrão ao longo da semana "
      f"define o piso, de {F.br(_PISO, 1)} pontos percentuais nesta amostra. "
      "Variação de magnitude inferior ao piso não é distinguível de flutuação "
      "amostral e não é interpretada."),
("p", "O segundo passo é a filtragem. Com apenas sete pontos, qualquer filtro "
      "pesado apaga o próprio sinal. Aplicou-se, por isso, o filtro binomial "
      "de três pontos com pesos 1, 2 e 1, que é o de menor ordem capaz de "
      "atenuar a oscilação ponto a ponto sem deslocar máximos e mínimos, com "
      "as extremidades preservadas sem suavização por falta de vizinho."),
("p", "O terceiro passo é a derivada. A diferença entre dias consecutivos da "
      "série suavizada estima a taxa de variação diária, em pontos "
      "percentuais por dia, e localiza os dias de inflexão. Uma derivada é "
      "interpretada apenas quando o valor absoluto dela supera o piso de "
      "ruído. Esse procedimento distingue duas hipóteses que a inspeção "
      "visual da curva bruta confunde: a erosão gradual, em que todas as "
      "derivadas são pequenas e do mesmo sinal, e o deslocamento por choques, "
      "em que poucas derivadas grandes concentram toda a mudança."),
("p", "O quarto passo é o limiar. Dois limiares foram definidos a priori: o "
      "de maioria, em 50%, que marca o dia em que o perfil deixa de "
      "caracterizar a maior parte do elenco; e o de inversão, no ponto em que "
      "as curvas de perfil iceberg e de humor perturbado se cruzam. O ponto "
      "de cruzamento foi obtido por interpolação linear entre os dois dias "
      "adjacentes das séries suavizadas. As análises foram conduzidas em R, "
      "com os pacotes psych, lavaan, semTools, lme4 e lmerTest. Não houve "
      "imputação: cada estimativa usa as observações disponíveis, e o "
      "denominador está declarado na nota da tabela correspondente."),
]

BLOCOS += [
("h1", "4 RESULTADOS"),
("h2", "4.1 Distribuição das subescalas"),
("p", "As seis subescalas se dividem em dois blocos claros (Tabela 2). Vigor "
      "e fadiga ocupam a faixa central da escala, com médias de 5,70 e 5,65 "
      "pontos, assimetria próxima de zero e piso abaixo de 9%. Tensão, "
      "depressão, raiva e confusão ficam junto ao mínimo, com médias entre "
      "0,45 e 1,60 ponto, assimetria de até 3,73 e curtose de até 16,96."),
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
("p", "A consistência interna é alta em depressão e raiva, com ômega ordinal "
      "de 0,94 e 0,93, adequada em fadiga e vigor e insuficiente em tensão, "
      "com alfa de 0,43 (Tabela 4). Em confusão e tensão a matriz policórica "
      "não convergiu, o que é consequência direta do efeito piso: sem "
      "variação nas respostas não há covariância para estimar."),
("tab", "psicometria"),
("fig", "a1_psicometria.png", 16.0,
 "Figura 2 - Consistência interna de cada subescala (A) e ganho de "
 "estabilidade da média de sete dias sobre a coleta isolada (B)"),
("p", "O painel B da Figura 2 traz o achado de maior consequência prática. "
      "Nenhuma subescala atinge 0,60 de estabilidade em uma coleta isolada, e "
      "todas passam de 0,76 na média de sete dias. Uma leitura isolada do "
      "instrumento não descreve o atleta de forma confiável nesta população; "
      "a média semanal descreve."),
("p", "A estrutura de seis fatores ajustou bem aos dados "
      f"(CFI = {F.br(F.AJUSTE['CFI'], 3)}; "
      f"RMSEA = {F.br(F.AJUSTE['RMSEA'], 3)}). A correlação entre os fatores "
      "(Tabela 5) mostra vigor e fadiga com 0,67, o valor mais alto do bloco "
      "energético, e confusão com tensão em 0,75, o mais alto do bloco de "
      "afeto negativo."),
("tab", "correlacao"),
("h2", "4.3 Prevalência dos seis perfis"),
("p", "O perfil superfície reúne 56,8% das observações, seguido do iceberg "
      "com 13,8%, do submerso com 9,4%, do iceberg invertido com 9,0%, da "
      "barbatana de tubarão com 7,2% e do Everest invertido com 3,7% "
      "(Tabela 6). Os três perfis associados a risco à saúde mental somam "
      f"{F.br(_RISCO, 1)}% das observações."),
("tab", "perfis"),
("fig", "fig_prevalencia.png", 16.0,
 "Figura 3 - Prevalência de cada perfil na amostra normativa e nesta amostra "
 "(A) e efeito da padronização interna sobre essa prevalência (B)"),
("p", "A diferença mais visível é o excesso de perfil superfície, 42,0 pontos "
      "percentuais acima da norma, com déficit correspondente nos perfis "
      "iceberg, submerso e barbatana de tubarão. Essa diferença não é achado "
      "clínico: ela decorre da padronização dentro da amostra, que coloca a "
      "média do próprio grupo na linha de água e comprime as observações em "
      "direção ao centro. Os dois perfis mais negativos, iceberg invertido e "
      "Everest invertido, ficam a 1,3 e a 1,0 ponto percentual da norma, o "
      "que sugere que a compressão atinge sobretudo os perfis intermediários "
      "e preserva os extremos negativos."),
("h2", "4.4 Predominância dos perfis ao longo da semana"),
("p", "Do primeiro ao último dia, a proporção de atletas em perfil iceberg "
      f"cai de {F.br(PERFIL_DIA[1][0], 1)}% para {F.br(PERFIL_DIA[7][0], 1)}%, "
      f"perda de {F.br(abs(PERFIL_DIA[7][0] - PERFIL_DIA[1][0]), 1)} pontos "
      "percentuais, e a de humor perturbado sobe de "
      f"{F.br(PERFIL_DIA[1][1], 1)}% para {F.br(PERFIL_DIA[7][1], 1)}%, ganho "
      f"de {F.br(abs(PERFIL_DIA[7][1] - PERFIL_DIA[1][1]), 1)} pontos "
      "(Tabela 8). Pela classificação de Parsons-Smith, no mesmo intervalo, o "
      "perfil iceberg recua 14,9 pontos percentuais e o perfil superfície "
      "avança 13,3 pontos, enquanto os quatro perfis restantes se movem menos "
      "de 4 pontos (Tabela 7)."),
("tab", "distribuicao"),
("fig", "a1_prevalencia_semana.png", 16.0,
 "Figura 4 - Composição do grupo em faixas de significado ao longo da semana "
 "(A) e prevalência dos seis perfis no primeiro e no último dia (B)"),
("p", "A Figura 4 reúne a leitura de grupo. O painel A agrega os seis perfis "
      "em três faixas: favorável, que reúne o iceberg; neutra, que reúne "
      "superfície e submerso; e de risco, que reúne barbatana de tubarão, "
      "iceberg invertido e Everest invertido. A composição revela um "
      "movimento que a leitura perfil a perfil esconde. A faixa de risco "
      "praticamente não se altera entre o primeiro e o último dia, de 23,8% "
      "para 21,7%, enquanto a faixa favorável cai de 21,4% para 6,5% e a "
      "neutra sobe de 54,7% para 71,8%. A semana não empurra a equipe para o "
      "risco: ela dissolve o padrão favorável na indiferenciação."),
("p", "O mesmo painel separa os dois tipos de dia. Nos dias de HIIT a faixa "
      "de risco alcança 23,0% das observações, contra 16,4% nos dias sem "
      "HIIT, e a faixa favorável cai de 15,9% para 10,0%. A diferença de 6,6 "
      "pontos percentuais na faixa de risco entre os dois tipos de dia é a "
      "primeira indicação de que o deslocamento acompanha a intensidade, e "
      "não o volume, o que a análise da série diária confirma a seguir."),
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
      "como perfil iceberg, contra 21,4% pelo critério de Parsons-Smith. A "
      "discrepância é esperada e decorre da definição: o critério de Morgan "
      "exige apenas que o vigor supere as cinco subescalas negativas, "
      "condição que quatro subescalas presas ao piso tornam fácil de "
      "satisfazer, enquanto o critério de Parsons-Smith exige proximidade a "
      "um centroide específico das seis dimensões. Em população com efeito "
      "piso acentuado, o critério de Morgan superestima a prevalência do "
      "padrão favorável, e a magnitude dessa superestimativa, de 50 pontos "
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
("p", f"Os três perfis de risco somam {F.br(_RISCO, 1)}% das observações, "
      "isto é, aproximadamente uma em cada cinco. O número aproxima-se dos "
      "26,5% relatados na única amostra brasileira classificada pelos mesmos "
      "seis perfis, com 898 atletas de elite e de base de um clube do Rio de "
      "Janeiro (Rohlfs, Noce e Wilke, 2024). A diferença de seis pontos "
      "percentuais tem duas explicações plausíveis e não excludentes, e as "
      "duas empurram na mesma direção. A amostra brasileira reúne os dois "
      "sexos e uma faixa etária de 12 a 44 anos, e nela os perfis de risco "
      "foram mais frequentes entre mulheres, tendência que replica o achado "
      "original de sobre-representação feminina nos perfis negativos "
      "(Parsons-Smith, Terry e Machin, 2017); a nossa amostra é masculina e "
      "adulta. E a amostra brasileira empregou também a instrução de semana "
      "anterior, que produz escores mais altos que a de momento presente "
      "adotada aqui. A prevalência menor observada no handebol é, portanto, "
      "coerente com a literatura, e não contraditória."),
("p", "A leitura otimista desse número seria a de uma equipe psicologicamente "
      "saudável. A leitura cautelosa, que preferimos, observa que uma em cada "
      "cinco observações em perfil de risco, na semana que antecede a "
      "estreia, corresponde a cerca de cinco atletas do elenco em qualquer "
      "dia dado. Para uma modalidade coletiva com sete jogadores em quadra, "
      "essa fração não é residual."),
("p", "A composição por faixas, no painel A da Figura 4, acrescenta uma "
      "qualificação importante a esse quadro. A faixa de risco permanece "
      "estável ao longo da semana, de 23,8% no primeiro dia para 21,7% no "
      "último, e o que se desloca é a faixa favorável, que cai de 21,4% para "
      "6,5%, absorvida pela faixa neutra. A semana de pré-temporada não "
      "adoece a equipe: ela apaga o padrão de prontidão e deixa a maior parte "
      "do elenco em estado indiferenciado. A distinção não é semântica. Uma "
      "equipe com risco crescente exige encaminhamento clínico; uma equipe "
      "que perde prontidão exige ajuste de carga. As duas leituras levam a "
      "condutas diferentes, e só a composição por faixas as separa."),
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
      "superestimar o padrão favorável em 50 pontos percentuais."),
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
("p", "O segundo é a prevalência do perfil superfície, de 56,8% contra 14,8% "
      "na amostra normativa. Aqui a divergência é, com alta probabilidade, "
      "artefato de método, e não achado de população. A padronização dentro "
      "da amostra transforma a média do grupo na linha de água e comprime as "
      "observações em direção ao centro, e a Figura 3 mostra que a compressão "
      "atinge sobretudo os perfis intermediários e preserva os extremos "
      "negativos. A comparação com a literatura fica, portanto, restrita à "
      "soma dos perfis de risco, que é robusta a esse deslocamento, e não "
      "vale para a distribuição interna dos perfis intermediários."),
("p", "Cabe ainda situar o estudo no que existe sobre humor no handebol. O "
      "acompanhamento de uma temporada inteira em handebolistas, com o "
      "instrumento anterior, descreveu variação conjunta de marcadores "
      "biológicos e psicológicos, mas sem classificação por perfil "
      "(Bresciani e outros, 2010). O estudo mais citado da modalidade "
      "descreve ansiedade competitiva e humor em atletas de areia, em corte "
      "único (Reigal e outros, 2019). Nenhum dos dois permite comparação "
      "direta de prevalência, o que é, em si, a medida do vazio que este "
      "estudo começa a preencher."),
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
      "semana do efeito da fase. A classificação por proximidade a centroide "
      "não reproduz a análise de agrupamento original: o procedimento "
      "indicado para amostras deste tamanho é a k-médias semeada com os "
      "centroides canônicos, adotada na amostra brasileira de referência "
      "(Rohlfs, Noce e Wilke, 2024), e a diferença entre os dois "
      "procedimentos ainda não foi quantificada nestes dados. A ausência de "
      "normas de escore T para a modalidade obriga à padronização interna, "
      "cujo efeito a Figura 3 quantifica. A amostra é masculina, o que impede "
      "extensão aos achados de sexo relatados na literatura. E o estudo não "
      "mediu desempenho, de modo que nenhuma afirmação sobre consequência "
      "competitiva dos perfis é sustentada por estes dados."),

("h1", "6 CONCLUSÃO"),
("p", "Em atletas de handebol masculino de elite, na última semana de "
      "pré-temporada, os seis perfis de humor descritos na literatura são "
      "identificáveis, e os três associados a risco à saúde mental somam "
      f"{F.br(_RISCO, 1)}% das observações, valor próximo ao da única amostra "
      "brasileira classificada pelo mesmo critério. A distribuição entre os "
      "perfis intermediários depende da régua: sem normas de escore da "
      "modalidade, a padronização interna concentra as observações no perfil "
      "superfície e não é comparável à norma."),
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
("nota", "QUARTIROLI, A. e outros. Cross-cultural validation of mood profile "
         "clusters in a sport and exercise context. Frontiers in Psychology, "
         "v. 9, art. 1949, 2018."),
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
("nota", "TERRY, P. C.; PARSONS-SMITH, R. L. Mood profiling for sustainable "
         "mental health among athletes. Sustainability, v. 13, n. 11, art. "
         "6116, 2021."),
("nota", "TERRY, P. C.; PARSONS-SMITH, R. L. Physical activity and healthy "
         "habits influence mood profile clusters in a Lithuanian population. "
         "Sustainability, v. 14, n. 16, art. 10006, 2022."),
("nota", "TERWEE, C. B. e outros. Quality criteria were proposed for "
         "measurement properties of health status questionnaires. Journal of "
         "Clinical Epidemiology, v. 60, n. 1, p. 34-42, 2007."),
("nota", "VAN WIJK, C. H. e outros. The Brunel Mood Scale as a screening tool "
         "for post-traumatic stress risk in military populations. Military "
         "Medicine, v. 178, n. 4, p. 372-376, 2013."),
]
