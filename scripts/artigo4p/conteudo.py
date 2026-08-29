"""Conteúdo do artigo sobre a resposta do humor ao tipo de estímulo.

Restrições de redação: nenhum travessão, nenhum traço de meia risca e nenhum
gerúndio. Verificadas por scripts/resultados/verificar_estilo.py.

Nenhum valor é inventado. As médias por condição saem de analise.py e os dados
de perfil de dados.py, ambos alimentados pelas tabelas do relatório completo.
A origem de cada estatística está declarada na nota da tabela.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dados  # noqa: E402
from analise import DIARIO, ORDEM, br, ranking, sensibilidade, sinal  # noqa: E402

DADOS = {x["dimensao"]: x for x in sensibilidade()}
_pth, _vig, _fad = DADOS["PTH"], DADOS["Vigor"], DADOS["Fadiga"]

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
    "Total do Humor subiu 86% nos dias de HIIT e permaneceu no valor de "
    "repouso nos dias de jogo, o que a torna a única variável capaz de "
    "distinguir os dois estímulos. Vigor e fadiga responderam com magnitude "
    "semelhante nas duas condições e sinalizam carga sem discriminação do "
    "tipo. Ao longo da semana, a proporção de atletas em perfil iceberg caiu "
    "de 71,4% para 32,6% e a de humor perturbado subiu de 47,6% para 71,7%."
)

PALAVRAS = ("Palavras-chave: humor; handebol; carga de treino; treinamento "
            "intervalado de alta intensidade; monitoramento.")

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."


# ══════════════════════════════════════════════════════════════ tabelas ═══
def _linha_dia(rotulo: str, dia: int) -> list[str]:
    return [rotulo] + [br(DIARIO[d][dia - 1], 2) for d in ORDEM]


TABELAS = {

"diario": {
 "numero": 1,
 "titulo": ("Média diária de cada dimensão do humor ao longo do microciclo e "
            "efeito do dia no modelo misto"),
 "cabecalho": ["Dia do microciclo"] + ORDEM,
 "linhas": [
  _linha_dia("1 Repouso", 1),
  _linha_dia("2 HIIT", 2),
  _linha_dia("3 Jogo", 3),
  _linha_dia("4 HIIT", 4),
  _linha_dia("5 Jogo", 5),
  _linha_dia("6 Técnico e tático", 6),
  _linha_dia("7 HIIT", 7),
  ["F do efeito do dia"] + [br(DADOS[d]["f_dia"], 2) for d in ORDEM],
  ["Eta² parcial"] + [br(DADOS[d]["eta"], 3) for d in ORDEM],
  ["Valor de p (FDR)"] + [DADOS[d]["p_dia"] for d in ORDEM],
 ],
 "nota": ("Nota: PTH é a Perturbação Total do Humor. Subescalas de 0 a 16 "
          "pontos. As médias vêm da estimativa em dois passos, que agrega "
          "primeiro por atleta e por isso corrige a pseudorreplicação. O "
          "efeito do dia é o do modelo misto com intercepto aleatório por "
          "atleta, com correção de Benjamini e Hochberg. Fonte primária: "
          "Tabelas 19 do relatório completo."),
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
   br(DADOS[d]["baseline"], 2),
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
            "com efeito piso e consistência entre dias"),
 "cabecalho": ["Dimensão", "dz [IC 95%]", "p (FDR)",
               "Significativo", "Piso (%)", "ICC(2,1)"],
 "linhas": [
  [d,
   f'{sinal(DADOS[d]["dz_agudo"], 2)} [{br(DADOS[d]["ic_inf"], 2)}; '
   f'{br(DADOS[d]["ic_sup"], 2)}]',
   DADOS[d]["p_agudo"],
   "Sim" if DADOS[d]["sobrevive"] else "Não",
   br(DADOS[d]["piso"], 1),
   br(DADOS[d]["icc"], 2)]
  for d in ["Fadiga", "PTH", "Vigor", "Depressão", "Tensão", "Raiva",
            "Confusão"]
 ],
 "nota": ("Nota: dz é o efeito para medidas pareadas, positivo para aumento "
          "após a sessão, já corrigido para a pseudorreplicação. "
          "Significância pela correção de Benjamini e Hochberg. Piso é o "
          "percentual de respostas no valor mínimo. Fonte primária: Tabelas "
          "24, 3 e 57 do relatório completo."),
},

"perfis": {
 "numero": 4,
 "titulo": ("Migração dos perfis de humor do primeiro ao último dia do "
            "microciclo e diferença entre dias de HIIT e dias sem HIIT"),
 "cabecalho": ["Critério e perfil", "Dia 1 (%)", "Dia 7 (%)",
               "Diferença (p.p.)", "Dias de HIIT (%)", "Dias sem HIIT (%)"],
 "linhas": (
  [["Morgan: perfil iceberg", br(dados.PERFIL_DIA[1][0], 1),
    br(dados.PERFIL_DIA[7][0], 1),
    sinal(dados.PERFIL_DIA[7][0] - dados.PERFIL_DIA[1][0], 1), "n.a.", "n.a."],
   ["Morgan: humor perturbado", br(dados.PERFIL_DIA[1][1], 1),
    br(dados.PERFIL_DIA[7][1], 1),
    sinal(dados.PERFIL_DIA[7][1] - dados.PERFIL_DIA[1][1], 1), "n.a.", "n.a."]]
  + [[f"Seis perfis: {nome.lower()}", br(v[1], 1), br(v[3], 1),
      sinal(v[3] - v[1], 1), "n.d.", "n.d."]
     for nome, v in dados.PERFIS_T.items()]
 ),
 "nota": ("Nota: o critério de Morgan classifica como iceberg a observação em "
          "que o vigor supera todas as cinco subescalas negativas, e como "
          "humor perturbado aquela com PTH maior que zero. A classificação de "
          "Parsons-Smith converte os escores em T e atribui a observação "
          "próximo, sobre subescalas padronizadas na amostra, na ausência de "
          "normas de escore T para esta população. Os dois critérios não são "
          "equivalentes. Fonte primária: Tabelas 20 e 21 do relatório "
          "completo."),
},

"sensibilidade": {
 "numero": 5,
 "titulo": ("Análise de sensibilidade: resposta de cada dimensão a cada tipo "
            "de estímulo e capacidade de separação entre os dois"),
 "cabecalho": ["Dimensão", "Resposta ao HIIT (%)", "Resposta ao jogo (%)",
               "Especificidade (%)", "Eta² do dia", "Piso (%)",
               "Leitura para o monitoramento"],
 "linhas": [
  [d,
   br(DADOS[d]["resposta_hiit"], 0),
   br(DADOS[d]["resposta_jogo"], 0),
   br(DADOS[d]["especificidade"], 0),
   br(DADOS[d]["eta"], 3),
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
          "o eta² do dia e o piso, sem teste adicional."),
},
}


# ══════════════════════════════════════════════════════════════ seções ═══
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
       "dois dias de jogo entre si e contra um dia de repouso, acompanha a "
       "migração dos perfis de humor ao longo da semana e identifica qual "
       "dimensão separa um estímulo do outro."),
]},

{"titulo": "2 MÉTODO", "nivel": 1, "blocos": [
 ("p", "Participaram 27 atletas de handebol masculino de primeira divisão, "
       "com idade média de 22,2 anos (desvio-padrão de 3,7) e 11,3 anos de "
       "experiência na modalidade; 19 atletas, 70% da amostra, completaram as "
       "sete coletas. O delineamento é observacional, longitudinal e "
       "prospectivo, com medidas repetidas intraindividuais e sem manipulação "
       "experimental da carga, o que restringe a leitura ao plano descritivo "
       "e associativo. O microciclo alterna, nos cinco primeiros dias, "
       "repouso (dia 1), HIIT (dias 2 e 4) e jogo (dias 3 e 5). O dia 6 foi "
       "de trabalho técnico e tático e o dia 7 repetiu o HIIT, já sob o "
       "acúmulo da semana. A comparação principal usa apenas o bloco "
       "alternado, porque nele os dois estímulos se intercalam sob acúmulo "
       "semelhante. O humor foi aferido pela Escala de Humor de Brunel, com "
       "24 itens e seis subescalas de 0 a 16 pontos, em duas coletas por dia "
       "de treino, a primeira tomada como pré-sessão e a última como "
       "pós-sessão. A Perturbação Total do Humor (PTH) soma as cinco "
       "subescalas negativas e subtrai o vigor, de modo que valores menores "
       "indicam humor mais favorável."),
 ("p", "As médias diárias vêm da estimativa em dois passos, que agrega "
       "primeiro por atleta e só depois por dia, e por isso já corrige a "
       "pseudorreplicação. O efeito do dia foi testado por modelo misto com "
       "intercepto aleatório por atleta, com eta² parcial como tamanho de "
       "efeito e correção de Benjamini e Hochberg. Cada condição é a média "
       "aritmética das médias diárias dos dias que a compõem, e o contraste "
       "com o repouso aparece em pontos da escala e em percentual. A resposta "
       "aguda usa o tamanho de efeito para medidas pareadas (dz) com "
       "intervalo de confiança de 95%. O perfil de humor foi classificado por "
       "dois critérios: o de Morgan, que exige vigor acima de todas as "
       "subescalas negativas, e o de Parsons-Smith, que atribui a observação "
       "ao centroide canônico mais próximo."),
 ("p", "A análise de sensibilidade combina três índices: a resposta ao HIIT e "
       "a resposta ao jogo, que são o afastamento absoluto de cada condição "
       "em relação ao repouso, e a especificidade, que é a diferença absoluta "
       "entre as duas condições, na mesma escala percentual. Os três são "
       "lidos junto ao eta² do dia e ao percentual de observações no piso da "
       "escala. O nível de significância adotado foi de 5%."),
]},

{"titulo": "3 RESULTADOS", "nivel": 1, "blocos": [
 ("h2", "3.1 Comportamento de cada variável ao longo da semana"),
 ("p", "O efeito do dia foi significativo em seis das sete dimensões (Tabela "
       "1). A maior magnitude está no vigor (eta² = 0,099) e na fadiga (eta² "
       "= 0,098), seguidas da PTH (eta² = 0,062), da raiva (0,048), da tensão "
       "(0,046) e da confusão (0,044). Apenas a depressão não variou (eta² = "
       "0,020; p = 0,160). Os tamanhos de efeito são pequenos: a variação "
       "existe, mas é modesta diante da diferença entre atletas."),
 ("tab", "diario"),
 ("fig", "fig_variaveis.png", 15.5,
  "Figura 1 - Comportamento diário de cada variável do humor, com a linha de "
  "base do dia 1, o sentido do desvio e o ajuste linear das médias diárias"),
 ("p", "A Figura 1 separa três padrões. Vigor, fadiga e fadiga física seguem "
       "trajetórias monotônicas e espelhadas: o vigor cai de 7,61 para 4,49 "
       "(inclinação de 0,33 ponto por dia) e a fadiga sobe de 3,96 para 7,46 "
       "(0,43 ponto por dia), sempre no sentido desfavorável. A PTH não sobe "
       "de forma contínua: oscila em dente de serra, com picos nos dias de "
       "HIIT e retorno ao valor de repouso nos dias de jogo, até o salto "
       "final de 8,28 no dia 7. Tensão, depressão, raiva e confusão "
       "permanecem próximas do mínimo da escala durante toda a semana, e três "
       "delas terminam abaixo do valor do dia 1."),
 ("h2", "3.2 HIIT comparado ao jogo e ao repouso"),
 ("p", "A PTH sobe de "
       f"{br(_pth['baseline'], 2)} no repouso para {br(_pth['hiit'], 2)} sob "
       f"HIIT ({sinal(_pth['p_hiit'], 0)}%) e permanece em "
       f"{br(_pth['jogo'], 2)} sob jogo ({sinal(_pth['p_jogo'], 0)}%), "
       "praticamente o valor do dia de repouso (Tabela 2). A fadiga sobe nas "
       f"duas condições, de {br(_fad['baseline'], 2)} para "
       f"{br(_fad['hiit'], 2)} sob HIIT e {br(_fad['jogo'], 2)} sob jogo, com "
       f"diferença de apenas {br(_fad['dif_hj'], 2)} ponto entre elas. O "
       f"vigor cai de {br(_vig['baseline'], 2)} para {br(_vig['hiit'], 2)} "
       f"sob HIIT e {br(_vig['jogo'], 2)} sob jogo, diferença de "
       f"{br(abs(_vig['dif_hj']), 2)} ponto. As quatro subescalas negativas "
       "restantes exibem médias menores sob jogo que sob repouso, resultado "
       "que opera sobre valores abaixo de 2,2 pontos e não sustenta "
       "interpretação clínica."),
 ("tab", "condicoes"),
 ("fig", "fig2_painel.png", 16.0,
  "Figura 2 - Média por condição (A), separação entre HIIT e jogo (B) e "
  "resposta aguda dentro da sessão (C)"),
 ("p", "No modelo misto, o dia de HIIT eleva a PTH em 2,70 pontos (IC 95% "
       "[1,12; 4,29]; p = 0,001), a fadiga em 0,80 ponto (IC 95% [0,20; "
       "1,40]; p = 0,009) e a fadiga física em 0,61 ponto (IC 95% [0,24; "
       "0,97]; p = 0,001), e reduz o vigor em 0,70 ponto (IC 95% [1,18; "
       "0,22]; p = 0,004). Sonolência, estresse percebido e fadiga mental têm "
       "intervalos que incluem o zero (Figura 3A). Do dia 1 ao dia 7, dois "
       "terços dos atletas registram aumento confiável de fadiga física e "
       "quase um quarto registra queda confiável de vigor, sempre acima do "
       "menor valor detectável (Figura 3B)."),
 ("fig", "fig_efeito.png", 16.0,
  "Figura 3 - Efeito do dia de HIIT por variável, com intervalo de confiança "
  "(A), e mudança confiável atleta a atleta do dia 1 ao dia 7 (B)"),
 ("p", "Os dias fora do bloco alternado confirmam o acúmulo. A PTH média dos "
       f"dias 6 e 7 é de {br(_pth['acumulo'], 2)}, valor superior ao das duas "
       "condições do bloco, e a fadiga média chega a "
       f"{br(_fad['acumulo'], 2)}. O dia 7 repete o protocolo de HIIT do dia "
       "2 e registra PTH de 8,28 contra 4,61 no dia 2: o mesmo estímulo "
       "externo produziu resposta psicológica quase duas vezes maior ao fim "
       "da semana."),
 ("h2", "3.3 Resposta aguda dentro da sessão"),
 ("p", "Cinco dimensões mudaram do momento pré para o momento pós após a "
       "correção para múltiplas comparações (Tabela 3). No núcleo do BRUMS, "
       "os efeitos são fadiga (dz = 0,45; IC 95% [0,23; 0,66]; p = 0,003), "
       "PTH (dz = 0,44; IC 95% [0,20; 0,70]; p = 0,004) e vigor (dz = −0,39; "
       "IC 95% [−0,61; −0,16]; p = 0,005). Tensão, depressão, raiva e "
       "confusão não atingiram significância, com efeitos abaixo de 0,20 em "
       "valor absoluto (Figura 2C). A mesma tabela explica o resultado: o "
       "percentual de observações no valor mínimo da escala é de 80,5% na "
       "confusão, 67,1% na depressão, 59,6% na raiva e 49,6% na tensão, "
       "contra 7,7% na fadiga e 8,6% no vigor. Uma subescala com dois terços "
       "das respostas no piso não tem margem estatística para registrar "
       "aumento de carga."),
 ("tab", "aguda"),
 ("h2", "3.4 Migração dos perfis de humor"),
 ("p", "A proporção de atletas em perfil iceberg cai de 71,4% no dia 1 para "
       "32,6% no dia 7, uma perda de 38,8 pontos percentuais, enquanto a "
       "proporção de humor perturbado sobe de 47,6% para 71,7%, ganho de 24,1 "
       "pontos (Tabela 4). A queda não é gradual: o iceberg despenca já no "
       "dia 2, primeiro dia de HIIT, recupera parte no dia 5 e volta a cair "
       "nos dois últimos dias. As duas curvas se cruzam entre os dias 4 e 5 "
       "(Figura 4A), momento em que a maioria da equipe deixa de apresentar "
       "perfil favorável."),
 ("tab", "perfis"),
 ("fig", "fig_perfis.png", 16.0,
  "Figura 4 - Migração diária pelo critério de Morgan (A), deslocamento entre "
  "os perfis de Parsons-Smith (B) e efeito do dia de HIIT sobre as métricas "
  "do perfil (C)"),
 ("p", "Pela classificação nos seis perfis, o deslocamento tem uma direção "
       "única: o perfil iceberg recua 23,1 pontos percentuais e a barbatana "
       "de tubarão avança 25,9 pontos (Figura 4B). A faixa de risco, que "
       "reúne barbatana de tubarão, iceberg invertido e Everest invertido, "
       "sobe de 26,2% para 43,5% das observações. O quadro é de migração para "
       "o esgotamento energético, e não para o sofrimento psíquico. Nos dias "
       "de HIIT, o índice iceberg cai (dz = −0,64; IC 95% [−1,10; −0,30]; p = "
       "0,004), o eixo vigor e fadiga se inverte (dz = −0,67; IC 95% [−1,22; "
       "−0,28]; p = 0,003) e a PTH sobe (dz = 0,54; IC 95% [0,19; 0,99]; p = "
       "0,012), com os três intervalos afastados do zero (Figura 4C)."),
 ("h2", "3.5 Análise de sensibilidade"),
 ("p", "Pela resposta ao HIIT, a ordem é "
       f"{', '.join(x.lower() for x in ranking('resposta_hiit')[:4])}; pela "
       "resposta ao jogo, "
       f"{', '.join(x.lower() for x in ranking('resposta_jogo')[:4])}; pela "
       "especificidade, isto é, pela capacidade de separar um estímulo do "
       f"outro, {', '.join(x.lower() for x in ranking('especificidade')[:4])} "
       "(Tabela 5). As posições da confusão, da tensão, da raiva e da "
       "depressão decorrem do efeito piso: variações de dois ou três décimos "
       "de ponto sobre uma base próxima de zero geram percentuais grandes sem "
       "significado prático."),
 ("tab", "sensibilidade"),
 ("p", "Excluídas as subescalas limitadas pelo piso, restam três candidatas. "
       f"A PTH reúne a maior resposta ao HIIT ({br(_pth['resposta_hiit'], 0)}"
       f"%), a maior especificidade ({br(_pth['especificidade'], 0)}%, mais "
       "do que o dobro da segunda colocada) e resposta aguda significativa "
       "(dz = 0,44). A fadiga responde às duas condições "
       f"({br(_fad['resposta_hiit'], 0)}% e {br(_fad['resposta_jogo'], 0)}%), "
       f"com especificidade de apenas {br(_fad['especificidade'], 0)}%. O "
       f"vigor cai {br(_vig['resposta_hiit'], 0)}% sob HIIT e "
       f"{br(_vig['resposta_jogo'], 0)}% sob jogo, com especificidade de "
       f"{br(_vig['especificidade'], 0)}%. A PTH é, portanto, a única "
       "variável que informa ao mesmo tempo a magnitude e o tipo do estímulo; "
       "vigor e fadiga informam a magnitude e não o tipo."),
]},

{"titulo": "4 DISCUSSÃO", "nivel": 1, "blocos": [
 ("p", "O resultado central é a dissociação entre magnitude e tipo de "
       "estímulo. Vigor e fadiga responderam de forma quase idêntica ao HIIT "
       "e ao jogo, o que os qualifica como marcadores de carga acumulada e os "
       "desqualifica como marcadores do que gerou essa carga. A PTH, por ser "
       "um índice composto, agrega variações pequenas de várias subescalas e "
       "preserva a informação de tipo que cada subescala isolada perde. O "
       "retorno da PTH ao valor de repouso nos dias de jogo, contra o salto "
       "nos dias de HIIT, sustenta a leitura de que os dois estímulos cobram "
       "custos psicológicos distintos."),
 ("p", "A migração dos perfis dá a esse achado uma tradução direta para a "
       "comissão técnica. A perda de 38,8 pontos percentuais no perfil "
       "iceberg é consequência da inversão do eixo vigor e fadiga, e não do "
       "aumento das subescalas negativas, que permanecem no piso. O padrão "
       "espelhado entre vigor e fadiga reproduz o perfil descrito na "
       "literatura e sustenta a validade do instrumento nesta amostra. A "
       "diferença entre o dia 2 e o dia 7, com protocolo idêntico e resposta "
       "quase duas vezes maior no segundo, indica que o custo psicológico de "
       "uma sessão depende do estado prévio do atleta."),
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
       "única capaz de separar o HIIT do jogo, com aumento de 86% nos dias de "
       "HIIT e permanência no valor de repouso nos dias de jogo. Vigor e "
       "fadiga acompanharam a carga com magnitude semelhante nas duas "
       "condições e servem ao controle do volume total, não à identificação "
       "do estímulo. Tensão, depressão, raiva e confusão não apresentaram "
       "margem de medida útil nesta amostra. Ao longo da semana, a equipe "
       "perdeu o perfil favorável sem migração para perfis clinicamente "
       "negativos. Para o monitoramento diário desta equipe, a recomendação é "
       "o acompanhamento conjunto de PTH, vigor e fadiga, com atenção ao "
       "acúmulo do fim da semana."),
]},
]
