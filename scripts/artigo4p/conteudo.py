"""Conteúdo do artigo curto sobre resposta do humor ao tipo de estímulo.

Restrições de redação: nenhum travessão, nenhum traço de meia risca e nenhum
gerúndio. Verificadas por scripts/resultados/verificar_estilo.py.

Nenhum valor é inventado. As médias por condição saem de analise.py, que as
calcula a partir das médias diárias já publicadas no conjunto de análises do
estudo. A origem de cada estatística está declarada na nota da tabela.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analise import ORDEM, br, ranking, sensibilidade, sinal  # noqa: E402

DADOS = {x["dimensao"]: x for x in sensibilidade()}

TITULO = ("Sensibilidade das dimensões do humor ao tipo de estímulo em "
          "atletas de handebol: HIIT e jogo comparados ao repouso")

SUBTITULO = ("Análise descritiva e estatística de um microciclo "
             "pré-competitivo de sete dias")

RESUMO = (
    "Este estudo descreve a resposta do humor de 27 atletas de handebol "
    "masculino de primeira divisão a dois tipos de estímulo, no microciclo de "
    "sete dias que antecede a competição. O humor foi aferido pela Escala de "
    "Humor de Brunel em todos os dias. Os cinco primeiros dias alternam "
    "repouso, HIIT, jogo, HIIT e jogo, o que permite comparar dois dias de "
    "HIIT e dois dias de jogo entre si e contra o repouso. O objetivo central "
    "foi a análise de sensibilidade: identificar qual dimensão responde mais "
    "a cada estímulo e qual delas separa um estímulo do outro. A Perturbação "
    "Total do Humor foi a mais responsiva ao HIIT e a única com separação "
    "ampla entre os dois tipos de dia. O vigor caiu na mesma magnitude nas "
    "duas condições, o que o torna indicador de carga sem valor "
    "discriminativo. Tensão, depressão, raiva e confusão apresentaram efeito "
    "piso elevado e não se mostraram úteis para o monitoramento diário."
)

PALAVRAS = ("Palavras-chave: humor; handebol; carga de treino; treinamento "
            "intervalado de alta intensidade; monitoramento.")

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."


# ══════════════════════════════════════════════════════════════ tabelas ═══
def _linha_dia(rotulo: str, dia: int) -> list[str]:
    from analise import DIARIO
    return [rotulo] + [br(DIARIO[d][dia - 1], 1) for d in ORDEM]


TABELAS = {

"diario": {
 "numero": 1,
 "titulo": ("Médias diárias das dimensões do humor ao longo do microciclo e "
            "teste de Friedman entre os sete dias"),
 "cabecalho": ["Dia do microciclo"] + ORDEM,
 "linhas": [
  _linha_dia("1 Repouso", 1),
  _linha_dia("2 HIIT", 2),
  _linha_dia("3 Jogo", 3),
  _linha_dia("4 HIIT", 4),
  _linha_dia("5 Jogo", 5),
  _linha_dia("6 Técnico e tático", 6),
  _linha_dia("7 HIIT", 7),
  ["Qui-quadrado de Friedman"] + [br(DADOS[d]["qui"], 1) for d in ORDEM],
  ["Valor de p"] + [DADOS[d]["p_friedman"] for d in ORDEM],
  ["W de Kendall"] + [br(DADOS[d]["w_kendall"], 2) for d in ORDEM],
 ],
 "nota": ("Nota: PTH é a Perturbação Total do Humor. Subescalas de 0 a 16 "
          "pontos. Friedman com 6 graus de liberdade; W de Kendall na escala "
          "de 0 a 1. Fonte primária: Tabela 6 do relatório de perfil."),
},

"condicoes": {
 "numero": 2,
 "titulo": ("Média de cada dimensão por condição e contraste com o repouso, "
            "no bloco alternado dos cinco primeiros dias"),
 "cabecalho": ["Dimensão", "Repouso (dia 1)", "HIIT (dias 2 e 4)",
               "Jogo (dias 3 e 5)", "HIIT contra repouso",
               "Jogo contra repouso", "HIIT contra jogo"],
 "linhas": [
  [d,
   br(DADOS[d]["baseline"], 1),
   br(DADOS[d]["hiit"], 2),
   br(DADOS[d]["jogo"], 2),
   f'{sinal(DADOS[d]["d_hiit"], 2)} ({sinal(DADOS[d]["p_hiit"], 0)}%)',
   f'{sinal(DADOS[d]["d_jogo"], 2)} ({sinal(DADOS[d]["p_jogo"], 0)}%)',
   sinal(DADOS[d]["dif_hj"], 2)]
  for d in ORDEM
 ],
 "nota": ("Nota: cada condição é a média aritmética das médias diárias dos "
          "dias que a compõem. O contraste aparece em pontos da escala e, "
          "entre parênteses, em percentual do repouso; valores positivos "
          "indicam escore maior que o do repouso. O dia 7 também é de HIIT, "
          "mas fica fora do bloco por acúmulo de carga."),
},

"aguda": {
 "numero": 3,
 "titulo": ("Resposta aguda dentro da sessão, do momento pré ao momento pós, "
            "e efeito piso de cada dimensão"),
 "cabecalho": ["Dimensão", "Tamanho de efeito (dz)", "Valor de p",
               "Significância após correção", "Observações no piso (%)",
               "Consistência entre dias (ICC)"],
 "linhas": [
  [d,
   sinal(DADOS[d]["dz_agudo"], 2),
   DADOS[d]["p_agudo"],
   "Sim" if DADOS[d]["sobrevive"] else "Não",
   br(DADOS[d]["piso"], 1),
   br(__import__("analise").ICC[d], 2) if d != "PTH" else "n.a."]
  for d in ["Fadiga", "PTH", "Vigor", "Depressão", "Tensão", "Raiva",
            "Confusão"]
 ],
 "nota": ("Nota: dz é o efeito para medidas pareadas, positivo para aumento "
          "após a sessão, já corrigido para a pseudorreplicação. "
          "Significância pela correção de Benjamini e Hochberg. Piso é o "
          "percentual de respostas no valor mínimo. Fonte primária: Tabelas "
          "23 e 2 do relatório completo."),
},

"sensibilidade": {
 "numero": 4,
 "titulo": ("Análise de sensibilidade: resposta de cada dimensão a cada tipo "
            "de estímulo e capacidade de separação entre os dois"),
 "cabecalho": ["Dimensão", "Resposta ao HIIT (%)", "Resposta ao jogo (%)",
               "Especificidade (%)", "W de Kendall", "Piso (%)",
               "Leitura para o monitoramento"],
 "linhas": [
  [d,
   br(DADOS[d]["resposta_hiit"], 0),
   br(DADOS[d]["resposta_jogo"], 0),
   br(DADOS[d]["especificidade"], 0),
   br(DADOS[d]["w_kendall"], 2),
   br(DADOS[d]["piso"], 1),
   leitura]
  for d, leitura in [
   ("PTH", "Sensor global e discriminante"),
   ("Vigor", "Sensor de carga, sem discriminação"),
   ("Fadiga", "Sensor de carga, sem discriminação"),
   ("Tensão", "Limitada pelo piso"),
   ("Depressão", "Limitada pelo piso"),
   ("Raiva", "Limitada pelo piso"),
   ("Confusão", "Limitada pelo piso"),
  ]
 ],
 "nota": ("Nota: resposta é o afastamento absoluto da condição em relação ao "
          "repouso, em percentual. Especificidade é a diferença absoluta "
          "entre HIIT e jogo, na mesma escala: quanto maior, mais a dimensão "
          "separa um estímulo do outro. A leitura combina os três índices com "
          "o W de Kendall e o piso, sem teste adicional."),
},
}


# ══════════════════════════════════════════════════════════════ seções ═══
_pth = DADOS["PTH"]
_fad = DADOS["Fadiga"]

SECOES: list[dict] = [

{"titulo": "1 INTRODUÇÃO", "nivel": 1, "blocos": [
 ("p", "O humor responde à carga de treino antes que o desempenho caia, e por "
       "isso é um dos indicadores mais usados no monitoramento de atletas. A "
       "maior parte dos estudos verifica apenas se o humor muda ao longo de "
       "um microciclo, o que responde a uma pergunta de magnitude. A pergunta "
       "prática do treinador é outra: qual dimensão do humor reage a qual "
       "tipo de estímulo. Uma sessão intervalada de alta intensidade e um "
       "jogo cobram demandas diferentes, e uma variável que se altera de "
       "forma idêntica nas duas situações sinaliza carga sem informar a "
       "origem dela. Este estudo descreve a trajetória do humor em um "
       "microciclo pré-competitivo de sete dias, compara dois dias de HIIT e "
       "dois dias de jogo entre si e contra um dia de repouso, e identifica "
       "qual dimensão responde mais a cada estímulo e qual delas separa um "
       "estímulo do outro."),
]},

{"titulo": "2 MÉTODO", "nivel": 1, "blocos": [
 ("p", "Participaram 27 atletas de handebol masculino de primeira divisão, "
       "com idade média de 22,2 anos (desvio-padrão de 3,7) e 11,3 anos de "
       "experiência na modalidade; 19 atletas, 70% da amostra, completaram as "
       "sete coletas. O delineamento é observacional, longitudinal e "
       "prospectivo, com medidas repetidas intraindividuais e sem "
       "manipulação experimental da carga, o que restringe a leitura ao "
       "plano descritivo e associativo. O microciclo alterna, nos cinco "
       "primeiros dias, repouso (dia 1), HIIT (dias 2 e 4) e jogo (dias 3 e "
       "5). O dia 6 foi de trabalho técnico e tático e o dia 7 repetiu o "
       "HIIT, já sob o acúmulo da semana. A comparação principal usa apenas o "
       "bloco alternado, porque nele os dois estímulos se intercalam sob "
       "acúmulo semelhante. O humor foi "
       "aferido pela Escala de Humor de Brunel, com 24 itens e seis "
       "subescalas de 0 a 16 pontos, em duas coletas por dia de treino, a "
       "primeira tomada como pré-sessão e a última como pós-sessão. A "
       "Perturbação Total do Humor (PTH) soma as cinco subescalas negativas e "
       "subtrai o vigor, de modo que valores menores indicam humor mais "
       "favorável."),
 ("p", "A descrição por dia usa média e teste de Friedman entre os sete dias, "
       "com o W de Kendall como tamanho de efeito. Cada condição é a média "
       "aritmética das médias diárias dos dias que a compõem, e o contraste "
       "com o repouso aparece em pontos da escala e em percentual. A resposta "
       "aguda usa o tamanho de efeito para medidas pareadas (dz), corrigido "
       "para a pseudorreplicação pela agregação prévia por atleta, com "
       "correção de Benjamini e Hochberg. A análise de sensibilidade combina "
       "três índices: a resposta ao HIIT e a resposta ao jogo, que são o "
       "afastamento absoluto de cada condição em relação ao repouso, e a "
       "especificidade, que é a diferença absoluta entre as duas condições, "
       "na mesma escala percentual. Os três índices são lidos junto ao W de "
       "Kendall e ao percentual de observações no piso da escala. O nível de "
       "significância adotado foi de 5%."),
]},

{"titulo": "3 RESULTADOS", "nivel": 1, "blocos": [
 ("h2", "3.1 Trajetória diária e contraste com o repouso"),
 ("p", "Quatro dimensões variaram de forma significativa ao longo do "
       "microciclo (Tabela 1): confusão (qui-quadrado de 25,8; p < 0,001; "
       "W = 0,23), vigor (14,7; p = 0,022; W = 0,13), tensão (13,2; p = "
       "0,039; W = 0,12) e fadiga (13,2; p = 0,040; W = 0,12). A raiva ficou "
       "no limiar (12,3; p = 0,056) e depressão e PTH não atingiram "
       "significância. Os tamanhos de efeito são pequenos: a variação existe, "
       "mas é modesta diante da diferença entre atletas."),
 ("tab", "diario"),
 ("fig", "fig1_grade.png", 14.0,
  "Figura 1 - Trajetória diária de cada dimensão do humor ao longo dos sete "
  "dias do microciclo"),
 ("p", "Vigor e fadiga seguem trajetórias espelhadas: o vigor cai de 7,5 no "
       "repouso para 4,7 no sétimo dia e a fadiga sobe de 3,7 para 7,5. No "
       "pós-teste do modelo misto, o vigor difere do repouso em todos os seis "
       "dias seguintes e a fadiga difere nos dias 3, 4, 6 e 7. As demais "
       "subescalas permanecem próximas do mínimo durante toda a semana, "
       "com médias entre 0,2 e 2,4 pontos."),
 ("h2", "3.2 HIIT comparado ao jogo e ao repouso"),
 ("p", "A PTH sobe de 2,0 no repouso para "
       f"{br(_pth['hiit'], 2)} sob HIIT ({sinal(_pth['p_hiit'], 0)}%) e para "
       f"{br(_pth['jogo'], 2)} sob jogo ({sinal(_pth['p_jogo'], 0)}%), com "
       f"diferença de {br(_pth['dif_hj'], 2)} ponto entre as duas condições, "
       "a maior separação observada (Tabela 2 e Figura 2). A fadiga sobe de 3,7 para "
       f"{br(_fad['hiit'], 2)} sob HIIT e {br(_fad['jogo'], 2)} sob jogo, com "
       f"diferença de apenas {br(_fad['dif_hj'], 2)} ponto. O vigor cai de "
       "7,5 para 5,55 nas duas condições, sem diferença alguma entre elas. As "
       "demais subescalas negativas exibem médias menores sob jogo que sob "
       "repouso, resultado que opera sobre valores abaixo de 2 pontos e não "
       "sustenta interpretação clínica."),
 ("tab", "condicoes"),
 ("fig", "fig2_painel.png", 16.0,
  "Figura 2 - Média por condição (A), separação entre HIIT e jogo (B) e "
  "resposta aguda dentro da sessão (C)"),
 ("p", "Os dias fora do bloco alternado confirmam o acúmulo. A PTH média dos "
       "dias 6 e 7 é de 6,25, valor superior ao das duas condições do bloco, "
       "e a fadiga média chega a 6,75. O dia 7 repete o protocolo de HIIT do "
       "dia 2 e registra PTH de 8,0 contra 4,7 no dia 2: o mesmo estímulo "
       "externo produziu resposta psicológica quase duas vezes maior ao fim "
       "da semana."),
 ("h2", "3.3 Resposta aguda dentro da sessão"),
 ("p", "Três dimensões mudaram do momento pré para o momento pós após a "
       "correção para múltiplas comparações (Tabela 3): fadiga (dz = 0,45; "
       "p = 0,003), PTH (dz = 0,44; p = 0,004) e vigor (dz = −0,39; p = "
       "0,005). Tensão, depressão, raiva e confusão não atingiram "
       "significância, com efeitos abaixo de 0,20 em valor absoluto (Figura 2C). A mesma "
       "tabela explica o resultado: o percentual de observações no valor "
       "mínimo da escala é de 80,5% na confusão, 67,1% na depressão, 59,6% na "
       "raiva e 49,6% na tensão, contra 7,7% na fadiga e 8,6% no vigor. Uma "
       "subescala com dois terços das respostas no piso não tem margem "
       "estatística para registrar aumento de carga."),
 ("tab", "aguda"),
 ("h2", "3.4 Análise de sensibilidade"),
 ("p", "Pela resposta ao HIIT, a ordem é PTH, fadiga, confusão e vigor; pela "
       "resposta ao jogo, confusão, PTH, fadiga e raiva; pela especificidade, "
       "PTH, depressão, raiva e confusão (Tabela 4 e Figura 2B). As posições da confusão, "
       "da depressão e da raiva decorrem do efeito piso: variações de dois ou "
       "três décimos de ponto sobre uma base próxima de zero geram "
       "percentuais grandes sem significado prático."),
 ("tab", "sensibilidade"),
 ("p", "Excluídas as subescalas limitadas pelo piso, restam três candidatas. "
       f"A PTH reúne a maior resposta ao HIIT ({br(_pth['resposta_hiit'], 0)}"
       f"%), a maior especificidade ({br(_pth['especificidade'], 0)}%) e "
       "resposta aguda significativa (dz = 0,44). A fadiga responde às duas "
       f"condições ({br(_fad['resposta_hiit'], 0)}% e "
       f"{br(_fad['resposta_jogo'], 0)}%), com especificidade de apenas "
       f"{br(_fad['especificidade'], 0)}%. O vigor cai 26% nas duas, com "
       "especificidade nula. A PTH é, portanto, a única variável que informa "
       "ao mesmo tempo a magnitude e o tipo do estímulo; vigor e fadiga "
       "informam a magnitude e não o tipo."),
]},

{"titulo": "4 DISCUSSÃO", "nivel": 1, "blocos": [
 ("p", "O resultado central é a dissociação entre magnitude e tipo de "
       "estímulo. Vigor e fadiga responderam de forma quase idêntica ao HIIT "
       "e ao jogo, o que os qualifica como marcadores de carga acumulada e os "
       "desqualifica como marcadores do que gerou essa carga. A PTH, por ser "
       "um índice composto, agrega variações pequenas de várias subescalas e "
       "preserva a informação de tipo que cada subescala isolada perde. O "
       "padrão espelhado entre vigor e fadiga reproduz o perfil iceberg "
       "descrito na literatura e sustenta a validade do instrumento nesta "
       "amostra. A diferença entre o dia 2 e o dia 7, com protocolo idêntico "
       "e resposta quase duas vezes maior no segundo, indica que o custo "
       "psicológico de uma sessão depende do estado prévio do atleta."),
 ("p", "O efeito piso de tensão, depressão, raiva e confusão é a principal "
       "limitação de medida: em atletas saudáveis no período pré-competitivo, "
       "essas subescalas concentram as respostas no valor mínimo e perdem a "
       "capacidade de registrar variação. Outras três limitações restringem a "
       "generalização. O delineamento é observacional, sem aleatorização, de "
       "modo que a atribuição do efeito a um tipo de estímulo permanece "
       "associativa. A amostra tem 27 atletas de uma única equipe, dos quais "
       "19 completaram todas as coletas. Cada condição reúne apenas dois "
       "dias, o que não separa por completo o efeito do tipo de estímulo do "
       "efeito da posição do dia no microciclo."),
]},

{"titulo": "5 CONCLUSÃO", "nivel": 1, "blocos": [
 ("p", "A Perturbação Total do Humor foi a variável mais sensível ao HIIT e a "
       "única capaz de separar o HIIT do jogo. Vigor e fadiga acompanharam a "
       "carga com magnitude semelhante nas duas condições e servem ao "
       "controle do volume total, não à identificação do estímulo. Tensão, "
       "depressão, raiva e confusão não apresentaram margem de medida útil "
       "nesta amostra. A recomendação para o monitoramento diário desta "
       "equipe é o acompanhamento conjunto de PTH, vigor e fadiga, com "
       "atenção ao acúmulo do fim da semana."),
]},
]
