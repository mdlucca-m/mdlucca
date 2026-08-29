"""Conteúdo do plano editorial da série sobre humor em atletas de handebol.

Restrições de redação: nenhum travessão, nenhum traço de meia risca e nenhum
gerúndio. Verificadas por scripts/resultados/verificar_estilo.py.

Os números do panorama vêm de scripts/panorama/corpus.py, que os calcula sobre
data/BIBLIOTECA_HANDEBOL.sqlite. Os números do estudo vêm das tabelas do
relatório completo, com a tabela de origem declarada em cada nota.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts" / "artigo4p"))
from dados import PERFIS_T  # noqa: E402
from scripts.panorama.corpus import ORDEM_CATEGORIAS, levantar  # noqa: E402

P = levantar()

TITULO = ("Plano editorial da série sobre humor em atletas de handebol de "
          "elite")
SUBTITULO = ("Definição do primeiro artigo, cronograma, delimitação dos "
             "manuscritos e panorama da produção internacional")

ABERTURA = [
    ("PARA QUE SERVE ESTE DOCUMENTO",
     "Este documento decide qual manuscrito sai primeiro, fixa as datas de "
     "cada entrega e delimita o que entra e o que não entra em cada artigo da "
     "série. Ele também traz o panorama da produção internacional sobre "
     "psicologia do esporte no handebol, calculado sobre a biblioteca do "
     "projeto, e a lista das pendências que bloqueiam a submissão. A data de "
     "referência é 28 de agosto de 2026."),
]

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."


def _pct(n: int) -> str:
    return f"{100 * n / P['escopo']:.1f}".replace(".", ",")


def _cat(familia: str, categorias: list[str]) -> int:
    conta = P["familia_por_categoria"][familia]
    return sum(conta.get(c, 0) for c in categorias)


# ══════════════════════════════════════════════════════════════ tabelas ═══
TABELAS = {

"cronograma": {
 "numero": 1,
 "titulo": ("Cronograma da série, com a data limite de cada entrega e a "
            "condição que libera a etapa seguinte"),
 "cabecalho": ["Etapa", "Período", "Entrega", "Condição de saída"],
 "linhas": [
  ["**Bloco 1. Artigo 1**", "", "", ""],
  ["1.1 Reconciliar o denominador", "31/08 a 06/09",
   "Planilha de fluxo: atletas por dia por coleta", "456 contra 351 resolvido"],
  ["1.2 Recomputar os agrupamentos", "07/09 a 13/09",
   "Script de classificação e tabela de prevalência",
   "Seis perfis reproduzidos a partir dos dados brutos"],
  ["1.3 Congelar tabelas e figuras", "07/09 a 13/09",
   "Sete tabelas e cinco figuras do Artigo 1", "Nenhum número em aberto"],
  ["1.4 Redigir o Artigo 1", "14/09 a 20/09", "Manuscrito completo",
   "Texto fechado, com referências"],
  ["1.5 Revisão do orientador", "21/09 a 27/09", "Manuscrito comentado",
   "Parecer recebido"],
  ["1.6 Ajuste e submissão", "28/09 a 04/10", "Submissão do Artigo 1",
   "Protocolo de submissão emitido"],
  ["**Bloco 2. Artigo 2**", "", "", ""],
  ["2.1 Fechar os marcadores de fadiga", "05/10 a 11/10",
   "Tabela de mudança confiável e de acúmulo por sessão",
   "MDC de referência definido"],
  ["2.2 Congelar tabelas e figuras", "12/10 a 18/10",
   "Seis tabelas e quatro figuras do Artigo 2", "Nenhum número em aberto"],
  ["2.3 Redigir o Artigo 2", "19/10 a 01/11", "Manuscrito completo",
   "Texto fechado, com referências"],
  ["2.4 Revisão e submissão", "02/11 a 15/11", "Submissão do Artigo 2",
   "Protocolo de submissão emitido"],
  ["**Bloco 3. Revisão sistemática**", "", "", ""],
  ["3.1 Fechar o protocolo e registrar", "05/10 a 18/10",
   "Protocolo no PROSPERO ou no OSF", "Registro aceito"],
  ["3.2 Extração e síntese", "19/10 a 29/11", "Planilha de extração completa",
   "Dupla checagem concluída"],
  ["3.3 Redigir e submeter", "30/11 a 20/12", "Submissão da revisão",
   "Protocolo de submissão emitido"],
 ],
 "nota": ("Nota: os períodos são semanas cheias, de segunda a domingo. A "
          "etapa 1.1 é bloqueante para todo o Bloco 1: sem o fluxo de dados "
          "reconciliado, nenhuma tabela do Artigo 1 pode ser declarada final. "
          "Os Blocos 2 e 3 correm em paralelo a partir de outubro porque não "
          "compartilham gargalo."),
},

"delimitacao": {
 "numero": 2,
 "titulo": "Delimitação comparada dos três manuscritos da série",
 "cabecalho": ["Atributo", "Artigo 1", "Artigo 2", "Artigo 3"],
 "linhas": [
  ["Título de trabalho",
   "Análise do perfil de humor em atletas de handebol de elite: novos perfis "
   "e suas características",
   "Impacto da fadiga sobre os novos perfis de humor em atletas de handebol "
   "de elite: overreaching, overtraining e recomendações",
   "Produção internacional sobre psicologia do esporte no handebol: revisão "
   "de escopo"],
  ["Pergunta",
   "Como se distribuem os seis perfis de humor nesta população e o que "
   "caracteriza cada um",
   "Como a carga do microciclo desloca os perfis e que sinais de "
   "sobrecarga isso produz",
   "O que já foi estudado, com que delineamento e com que variável"],
  ["Desenho", "Observacional descritivo, de corte múltiplo",
   "Observacional longitudinal, medidas repetidas",
   "Revisão de escopo conforme PRISMA-ScR"],
  ["Unidade de análise", "A observação diária", "O atleta ao longo da semana",
   "O estudo"],
  ["Desfecho primário", "Prevalência de cada perfil",
   "Deslocamento do perfil e mudança confiável por atleta",
   "Contagem por delineamento e por variável"],
  ["Variáveis", "Seis subescalas do BRUMS e PTH",
   "BRUMS, PTH, fadiga física e mental, TQR, sonolência, PSE, FC de pico, "
   "recuperação da FC",
   "Família de variável psicológica e coocorrência com variável fisiológica"],
  ["Análises", "Classificação por centroide, prevalência, qui-quadrado, "
   "concordância entre critérios, percentis de referência",
   "Modelo misto, dz com IC, mudança confiável contra o MDC, inclinação por "
   "sessão, fator de Bayes",
   "Contagem, tabulação cruzada e mapa de lacunas"],
  ["O que não entra", "Carga de treino e inferência causal",
   "Definição dos perfis, que fica no Artigo 1",
   "Síntese de efeito, porque o escopo é de mapeamento"],
  ["Revista alvo",
   "Frontiers in Psychology ou Sports (MDPI)",
   "International Journal of Sports Physiology and Performance ou Journal of "
   "Sports Sciences",
   "Montenegrin Journal of Sports Science and Medicine ou BMC Sports Science"],
  ["Estado hoje", "Tabelas e figuras prontas, texto por escrever",
   "Tabelas e figuras prontas, texto por escrever",
   "Corpus triado, protocolo por registrar"],
 ],
 "nota": ("Nota: a ordem de submissão é a ordem da tabela. O Artigo 2 cita o "
          "Artigo 1 para a definição dos perfis, o que impede a inversão da "
          "ordem sem duplicação de método."),
},

"perfis": {
 "numero": 3,
 "titulo": ("Os seis perfis de humor de Parsons-Smith: definição, prevalência "
            "normativa e prevalência nesta amostra"),
 "cabecalho": ["Perfil", "Definição pelo escore T das seis subescalas",
               "Norma (%)", "Dia 1 (%)", "Leitura para o handebol"],
 "linhas": [
  ["Iceberg", "Vigor alto; tensão, depressão, raiva, fadiga e confusão baixas",
   "29,4", "40,5", "Prontidão competitiva"],
  ["Submerso", "As seis subescalas abaixo da média, o vigor incluído",
   "25,5", "7,1", "Apatia geral, sem sofrimento declarado"],
  ["Barbatana de tubarão",
   "O vigor mais baixo de todos os perfis, com fadiga superior à de qualquer "
   "outro perfil exceto o Everest invertido", "17,3", "2,4",
   "Risco por baixa energia em ambiente que exige alerta"],
  ["Superfície", "As seis subescalas próximas da média", "14,8", "26,2",
   "Estado indiferenciado"],
  ["Iceberg invertido",
   "Vigor baixo com tensão, depressão, raiva, fadiga e confusão altas",
   "10,3", "9,5", "Indicador clássico de síndrome de overtraining"],
  ["Everest invertido",
   "Vigor baixo, tensão e fadiga altas, e depressão, raiva e confusão muito "
   "altas", "2,7", "14,3", "O perfil mais negativo, com risco clínico"],
 ],
 "nota": ("Nota: as definições e as prevalências normativas são da amostra A "
          "de Parsons-Smith, Terry e Machin (2017), sobre escores T. A "
          "prevalência nesta amostra é a do dia de repouso, pela "
          "classificação sobre escores T adotada depois da auditoria "
          "registrada em data/AUDITORIA_PERFIS_HUMOR.docx. A Figura 1 "
          "compara as duas distribuições."),
},

"delineamento": {
 "numero": 4,
 "titulo": ("Panorama da produção internacional sobre psicologia do esporte "
            "no handebol, por delineamento"),
 "cabecalho": ["Delineamento", "Estudos", "% do escopo"],
 "linhas": [[cat.capitalize(), str(P["por_categoria"][cat]),
             _pct(P["por_categoria"][cat])]
            for cat in ORDEM_CATEGORIAS if P["por_categoria"].get(cat)],
 "nota": ("Nota: o escopo reúne os registros da biblioteca com população de "
          f"handebol, publicação entre 2006 e 2026 e construto psicológico "
          f"aferido, sem filtro de delineamento, o que totaliza {P['escopo']} "
          f"estudos de uma biblioteca de {P['biblioteca']}. A categoria não "
          "especificado agrupa os registros cujo resumo não declara o "
          "delineamento, e é a maior limitação deste panorama."),
},

"familia": {
 "numero": 5,
 "titulo": ("Família de variável psicológica por delineamento: onde o campo "
            "já produziu e onde está vazio"),
 "cabecalho": ["Família", "Revisão", "Ensaio contr.", "Experimental",
               "Transversal", "Longitudinal", "Outros", "Não espec.", "Total"],
 "linhas": [
  [fam.capitalize(),
   str(_cat(fam, ["revisão"])),
   str(_cat(fam, ["ensaio controlado"])),
   str(_cat(fam, ["experimental sem controle"])),
   str(_cat(fam, ["transversal"])),
   str(_cat(fam, ["longitudinal"])),
   str(_cat(fam, ["observacional", "estudo de caso", "validação", "outro"])),
   str(_cat(fam, ["não especificado"])),
   str(sum(P["familia_por_categoria"][fam].values()))]
  for fam in sorted(P["familia_por_categoria"],
                    key=lambda f: -sum(P["familia_por_categoria"][f].values()))
  if sum(P["familia_por_categoria"][fam].values()) >= 5
 ],
 "nota": ("Nota: um estudo pode aferir mais de uma família, de modo que a "
          "soma das linhas excede o total do escopo. Famílias com menos de "
          "cinco estudos foram omitidas. A coluna outros reúne observacional, "
          "estudo de caso, validação e demais delineamentos. A linha de humor "
          "e afeto é a penúltima em volume e a que concentra a lacuna "
          "descrita na seção 5."),
},

"validacao": {
 "numero": 6,
 "titulo": ("Variáveis que reforçam a medida de humor por validação cruzada, "
            "e o que o estudo já tem"),
 "cabecalho": ["Variável", "O que ela valida no humor", "Já coletada",
               "Onde está"],
 "linhas": [
  ["PSE da sessão e carga interna",
   "Confirma que a variação do humor acompanha a carga percebida e não o "
   "acaso", "Sim", "Tabelas 49 e 72"],
  ["FC de pico e percentual da FC máxima",
   "Separa o estímulo externo entregue do custo psicológico percebido",
   "Sim", "Tabela 49"],
  ["Recuperação da FC em um minuto e deriva cardíaca",
   "Marca o estado autonômico agudo, que antecede a queda de vigor",
   "Sim", "Tabela 49"],
  ["TQR, escala de recuperação total",
   "Valida a fadiga do BRUMS por um instrumento independente", "Sim",
   "Tabela 69"],
  ["Sonolência e sono",
   "Explica parte da queda de vigor que não vem da carga do dia", "Sim",
   "Tabela 69"],
  ["Fadiga física e fadiga mental em escala separada",
   "Distingue o componente somático do componente cognitivo da fadiga",
   "Sim", "Tabelas 20 e 65"],
  ["Estresse percebido (PSS-14)",
   "Controla o estresse de vida, que confunde a leitura da carga", "Sim",
   "Tabela 69"],
  ["Variabilidade da frequência cardíaca",
   "É a medida mais citada de convergência com a resposta psicométrica à "
   "sobrecarga", "Não", "Coleta futura"],
  ["Marcadores bioquímicos (cortisol, testosterona, creatina quinase)",
   "Ancora a resposta psicológica em substrato fisiológico", "Parcial",
   "Coleta salivar declarada, sem tabela de resultado"],
  ["Desempenho (salto, arremesso, teste de campo)",
   "Fecha o critério de overreaching funcional, que exige queda de "
   "desempenho", "Não", "Coleta futura, bloqueia o diagnóstico"],
 ],
 "nota": ("Nota: as três últimas linhas são as que faltam. A ausência de "
          "medida de desempenho impede o diagnóstico formal de overreaching "
          "funcional ou não funcional, que exige queda de desempenho seguida "
          "de recuperação, e por isso o Artigo 2 descreve assinatura de "
          "sobrecarga, nunca diagnóstico."),
},

"pendencias": {
 "numero": 7,
 "titulo": "Pendências que bloqueiam a submissão, com o responsável e a data",
 "cabecalho": ["Pendência", "Por que bloqueia", "O que resolve", "Data"],
 "linhas": [
  ["Número de observações",
   "O manuscrito reporta 456 observações, mas o desenho comporta no máximo "
   "351, isto é, 27 atletas por treze coletas",
   "Planilha de fluxo com atletas por dia por coleta e observações válidas",
   "06/09"],
  ["Duas séries de médias diárias",
   "A estimativa em dois passos e a média bruta divergem, e as duas circulam "
   "no mesmo relatório",
   "Adotar a estimativa em dois passos em toda a série e recalcular a média "
   "bruta apenas como anexo", "06/09"],
  ["Três valores de MDC",
   "O MDC derivado do alfa, o derivado do ômega e o derivado do ICC dão "
   "limites diferentes para a mesma decisão de mudança confiável",
   "Fixar o MDC do ICC(2,1) como referência e declarar os demais em nota",
   "11/10"],
  ["Normas de escore T",
   "Sem normas de handebol, a classificação por padronização interna infla o "
   "perfil superfície em 42 pontos percentuais",
   "Publicar percentis próprios no Artigo 1 e declarar a limitação",
   "13/09"],
  ["Registro do protocolo da revisão",
   "Revisão de escopo sem registro prévio perde pontos de avaliação e "
   "dificulta a publicação",
   "Registrar no PROSPERO ou no OSF antes da extração", "18/10"],
 ],
 "nota": ("Nota: as duas primeiras pendências são bloqueantes para o Artigo 1 "
          "e, por consequência, para toda a série."),
},
}


# ══════════════════════════════════════════════════════════════ blocos ═══
_h = P["humor"]

BLOCOS = [

("h1", "1 A DECISÃO: QUAL ARTIGO SAI PRIMEIRO"),
("p", "O primeiro artigo da série é o de perfis. A razão é de dependência, "
      "não de preferência. O segundo artigo usa o perfil como desfecho, e o "
      "perfil precisa estar definido, classificado e publicado antes que "
      "alguém possa medir o deslocamento dele. Se a ordem for invertida, o "
      "Artigo 2 carrega toda a seção de método da classificação, cresce além "
      "do formato de artigo empírico e enfraquece os dois manuscritos."),
("p", "A segunda razão é de risco. O Artigo 1 é descritivo e depende apenas "
      "de dados já coletados. O Artigo 2 depende de decisões que ainda estão "
      "em aberto, entre elas qual erro de medida serve de referência para a "
      "mudança confiável. Um manuscrito pronto e submetido em outubro vale "
      "mais que dois manuscritos parados à espera da mesma decisão."),
("p", "A terceira razão é de oportunidade. A literatura de agrupamentos de "
      "humor cresce desde 2017 e ainda não tem um estudo em handebol. Esse "
      "espaço fecha. O levantamento da seção 5 mostra que dos 32 estudos de "
      "humor em handebol nos últimos vinte anos, apenas um é longitudinal e "
      "nenhum aplica os seis perfis."),

("h1", "2 CRONOGRAMA"),
("p", "O cronograma abaixo tem oito semanas até a submissão do Artigo 1 e "
      "termina a série em dezembro. Ele é apertado de propósito: as tabelas e "
      "as figuras dos dois artigos empíricos já existem, e o que falta é "
      "decisão sobre os dados brutos e redação."),
("tab", "cronograma"),

("h1", "3 DELIMITAÇÃO DE CADA ARTIGO"),
("p", "A tabela a seguir fixa o que entra em cada manuscrito. A linha mais "
      "importante é a última do bloco de conteúdo, a do que não entra: é ela "
      "que impede a sobreposição entre os artigos, que é o motivo mais comum "
      "de recusa em série de publicações do mesmo conjunto de dados."),
("tab", "delimitacao"),

("h2", "3.1 Artigo 1, em detalhe"),
("p", "**Objetivo primário.** Descrever a distribuição dos seis perfis de "
      "humor em atletas de handebol de elite e caracterizar cada perfil pelo "
      "escore das seis subescalas. **Objetivos secundários.** Comparar a "
      "classificação pelo critério de Morgan e pelo de Parsons-Smith; "
      "estabelecer percentis de referência das seis subescalas para esta "
      "população; verificar a consistência interna e a estabilidade das "
      "medidas."),
("p", "**Amostra.** Vinte e sete atletas de handebol masculino de primeira "
      "divisão, com 22,2 anos de idade em média e 11,3 anos de experiência. "
      "**Instrumento.** Escala de Humor de Brunel, 24 itens, seis subescalas "
      "de 0 a 16 pontos. **Unidade de análise.** A observação diária, porque "
      "o perfil é um estado e não um traço."),
("p", "**Como o perfil é calculado.** O procedimento original padroniza as "
      "seis subescalas em escore T, aplica análise de agrupamento "
      "hierárquica aglomerativa com distância euclidiana quadrática pelo "
      "método de Ward para fixar o número de agrupamentos, refina as "
      "fronteiras por k-médias e confirma a classificação por análise "
      "discriminante. O número de seis agrupamentos foi verificado por "
      "inspeção do gráfico de sedimentação. Nesta amostra, sem normas de "
      "escore T para handebol, a padronização foi feita dentro da própria "
      "amostra e cada observação foi atribuída ao centroide canônico mais "
      "próximo. Essa decisão precisa ser declarada no método e discutida como "
      "limitação, porque ela sozinha explica o excesso de perfil superfície "
      "mostrado na Figura 1."),
("tab", "perfis"),
("fig", "fig_prevalencia.png", 16.0,
 "Figura 1 - Prevalência de cada perfil na amostra normativa e nesta amostra "
 "(A), e efeito da padronização interna sobre essa prevalência (B)"),
("p", "O painel B é o achado de método que o Artigo 1 precisa enfrentar de "
      "frente. A padronização dentro da amostra empurra 42 pontos percentuais "
      "para o perfil superfície e esvazia os perfis extremos, porque a média "
      "da amostra passa a ser a linha de água. A saída não é abandonar a "
      "classificação: é publicar os percentis próprios desta população, o que "
      "transforma a limitação em contribuição original e dá ao Artigo 2 uma "
      "régua estável."),

("h2", "3.2 Artigo 2, em detalhe"),
("p", "**Objetivo primário.** Quantificar o deslocamento dos perfis de humor "
      "ao longo de um microciclo pré-competitivo e relacionar esse "
      "deslocamento à carga do dia. **Objetivos secundários.** Identificar "
      "quais variáveis atingem mudança confiável atleta a atleta; descrever a "
      "progressão entre as três sessões de HIIT; propor recomendações de "
      "monitoramento."),
("p", "**O limite que o artigo não pode ultrapassar.** Overreaching funcional "
      "e não funcional são definidos por queda de desempenho seguida de "
      "recuperação em prazos distintos. O estudo não mediu desempenho depois "
      "do microciclo. O artigo descreve, portanto, uma assinatura de "
      "sobrecarga, composta por perda de vigor, acúmulo de fadiga, queda da "
      "recuperação percebida e dissociação entre estímulo externo e custo "
      "interno, e discute o risco. Ele não diagnostica. Essa distinção "
      "precisa aparecer no título, no resumo e na discussão, sob pena de "
      "recusa na primeira rodada de revisão."),
("p", "**O achado que sustenta o artigo.** Nas três sessões de HIIT, com "
      "protocolo equivalente, a frequência cardíaca de pico cai de 184 para "
      "181 batimentos por minuto enquanto o esforço percebido sobe de 8,5 "
      "para 9,1 e a perturbação total do humor sobe de 4,8 para 8,0, com "
      "inclinação de 1,76 ponto por sessão. O mesmo estímulo externo passa a "
      "custar mais. Essa dissociação é o marcador clássico de sobrecarga "
      "acumulada e é o que dá ao Artigo 2 uma tese própria, independente do "
      "Artigo 1."),

("h1", "4 PANORAMA DA PRODUÇÃO INTERNACIONAL"),
("p", f"O escopo do panorama reúne {P['escopo']} estudos de uma biblioteca de "
      f"{P['biblioteca']} registros: população de handebol, publicação entre "
      "2006 e 2026 e construto psicológico aferido. O filtro de delineamento "
      "da revisão não se aplica aqui de propósito, porque uma das perguntas é "
      "justamente quantas revisões já existem."),
("tab", "delineamento"),
("p", f"A resposta à pergunta sobre revisões é {P['por_categoria']['revisão']} "
      f"em {P['escopo']} estudos, isto é, "
      f"{_pct(P['por_categoria']['revisão'])}% do escopo. Nenhuma delas cobre "
      "psicologia do esporte no handebol como campo: a busca dirigida "
      "confirma revisões de análise de jogo no handebol e revisões de saúde "
      "mental no esporte em geral, mas nenhuma na interseção. Isso justifica "
      "uma revisão de escopo e explica por que ela deve mapear, e não "
      "sintetizar efeito."),
("p", f"Sobre os delineamentos primários, há {P['por_categoria']['ensaio controlado']}"
      f" ensaios controlados, {P['por_categoria']['experimental sem controle']}"
      f" estudos experimentais sem controle, {P['por_categoria']['transversal']}"
      f" transversais e {P['por_categoria']['longitudinal']} longitudinais. O "
      f"número mais relevante para o método da revisão é outro: "
      f"{P['por_categoria']['não especificado']} estudos, "
      f"{_pct(P['por_categoria']['não especificado'])}% do escopo, não "
      "declaram o delineamento no resumo. A revisão precisa prever leitura de "
      "texto completo para essa fatia, e o protocolo precisa dizer isso."),
("tab", "familia"),
("p", "A tabela cruzada mostra onde o campo já produziu e onde está vazio. "
      "Ansiedade e estresse concentram o maior volume, com 214 estudos. Humor "
      f"e afeto aparecem em apenas {_h['total']} estudos, "
      f"{_pct(_h['total'])}% do escopo, dos quais apenas "
      f"{_h['por_categoria'].get('longitudinal', 0)} é longitudinal e "
      f"{_h['por_categoria'].get('revisão', 0)} é revisão. Essa é a lacuna "
      "que os Artigos 1 e 2 ocupam."),
("p", f"Quanto ao cruzamento com variáveis não psicológicas, "
      f"{P['combinacao'].get('psicológica combinada com fisiológica ou física', 0)}"
      f" estudos do escopo, "
      f"{_pct(P['combinacao'].get('psicológica combinada com fisiológica ou física', 0))}"
      "%, combinam medida psicológica com medida fisiológica ou física. Entre "
      f"os estudos de humor, {_h['combinado_com'].get('fisicas', 0)} combinam "
      f"com variável física e {_h['combinado_com'].get('fisiologicas', 0)} com "
      "variável fisiológica. A combinação é, portanto, prática corrente e "
      "esperada pelo revisor, o que reforça a seção 6."),

("h1", "5 LACUNAS DA LITERATURA"),
("p", "A busca dirigida na literatura internacional, cruzada com o panorama "
      "acima, delimita quatro lacunas. Elas são o argumento de originalidade "
      "dos dois artigos e devem aparecer, nessa ordem, no último parágrafo da "
      "introdução de cada um."),
("lista", [
 "**Nenhum estudo aplica os seis perfis de humor ao handebol.** Os "
 "agrupamentos foram descritos em população geral (Parsons-Smith, Terry e "
 "Machin, 2017), validados em contexto esportivo geral (Quartiroli e outros, "
 "2018), em Singapura (Han e outros, 2020) e em atletas brasileiros de elite "
 "e de base (Rohlfs e outros, 2024). Nenhum desses recortes é de handebol.",
 "**Falta acompanhamento longitudinal do humor no handebol.** Dos 32 estudos "
 "de humor no escopo, um é longitudinal. O precedente mais próximo acompanha "
 "medidas biológicas e psicológicas ao longo de uma temporada em handebolistas "
 "(Bresciani e outros, 2010), com POMS e sem classificação por perfil.",
 "**Não há estudo que ligue o deslocamento do perfil ao tipo de carga.** A "
 "literatura de sobrecarga trabalha com escores contínuos de humor (Aubry e "
 "outros, 2014; Bellinger, 2020) ou com questionários de bem-estar (Nobari e "
 "outros, 2021), nunca com a migração entre perfis.",
 "**O BRUMS quase não é usado em handebol.** No escopo, dois estudos declaram "
 "BRUMS e os demais usam POMS ou escala genérica. Publicar percentis de "
 "referência do BRUMS para handebol de elite preenche uma lacuna "
 "instrumental, além da lacuna substantiva.",
]),

("h1", "6 VARIÁVEIS QUE FORTALECEM A MEDIDA DE HUMOR"),
("p", "O pedido é claro: identificar o que, medido junto do humor, torna o "
      "estudo mais forte, de modo que uma medida ajude a validar a outra. O "
      "princípio vem do modelo de avaliação multicomponente do sofrimento de "
      "treino (Main e Grove, 2009): nenhuma medida isolada distingue carga "
      "aguda de sobrecarga acumulada, e a convergência entre medidas de "
      "natureza diferente é o que sustenta a inferência."),
("tab", "validacao"),
("p", "A leitura da tabela é direta. O estudo já tem sete das dez variáveis, "
      "e as três que faltam têm pesos muito diferentes. A variabilidade da "
      "frequência cardíaca é a mais citada na literatura de convergência "
      "psicométrica com a sobrecarga (Flatt e outros, 2017) e seria um ganho "
      "grande em um estudo futuro, mas a ausência dela não invalida nada do "
      "que está escrito. A ausência de medida de desempenho, ao contrário, "
      "muda o que o Artigo 2 pode afirmar, e por isso aparece de novo na "
      "seção 7."),

("h1", "7 PENDÊNCIAS QUE BLOQUEIAM A SUBMISSÃO"),
("p", "Cinco pendências separam o material atual de um manuscrito submissível. "
      "Duas delas são bloqueantes e têm data na primeira semana do "
      "cronograma."),
("tab", "pendencias"),
("p", "Há ainda um item que não é pendência de dados e sim de material: a "
      "análise bibliométrica sobre qualidade do ar, de Fábio e Danilo, citada "
      "como referência de formato, não está no repositório do projeto e não "
      "foi localizada. Sem o arquivo não é possível espelhar a estrutura dela "
      "na revisão de escopo. Basta enviá-lo para que a seção de método da "
      "revisão seja ajustada ao mesmo padrão."),

("h1", "8 O QUE FAZER NA PRÓXIMA SEMANA"),
("lista", [
 "Levantar a planilha de fluxo de dados e fechar o número de observações "
 "válidas. Sem isso o Artigo 1 não fecha.",
 "Confirmar que a estimativa em dois passos é a série oficial da série de "
 "artigos, e arquivar a média bruta como anexo.",
 "Enviar a análise bibliométrica de referência.",
 "Decidir a revista alvo do Artigo 1 entre as duas propostas, porque o limite "
 "de palavras e o formato de tabela mudam a redação.",
 "Marcar a data da revisão do orientador dentro da semana de 21 a 27 de "
 "setembro, que é o gargalo do cronograma.",
]),

("h1", "REFERÊNCIAS"),
("nota", "AUBRY, A. e outros. Functional overreaching: the key to peak "
         "performance during the taper? Medicine & Science in Sports & "
         "Exercise, v. 46, n. 9, p. 1769-1777, 2014."),
("nota", "BELLINGER, P. Functional overreaching in endurance athletes: a "
         "necessity or cause for concern? Sports Medicine, v. 50, p. "
         "1059-1073, 2020."),
("nota", "BRESCIANI, G. e outros. Monitoring biological and psychological "
         "measures throughout an entire season in male handball players. "
         "European Journal of Sport Science, v. 10, n. 6, p. 377-384, 2010."),
("nota", "FLATT, A. A. e outros. Heart rate variability and psychometric "
         "responses to overload and tapering in collegiate sprint-swimmers. "
         "Journal of Science and Medicine in Sport, v. 20, n. 6, p. 606-610, "
         "2017."),
("nota", "HAN, C. S. Y. e outros. Mood profiling in Singapore: cross-cultural "
         "validation and potential applications of mood profile clusters. "
         "Frontiers in Psychology, v. 11, art. 665, 2020."),
("nota", "MAIN, L. C.; GROVE, J. R. A multi-component assessment model for "
         "monitoring training distress among athletes. European Journal of "
         "Sport Science, v. 9, n. 4, p. 195-202, 2009."),
("nota", "MORGAN, W. P. Test of champions: the iceberg profile. Psychology "
         "Today, v. 14, p. 92-108, 1980."),
("nota", "NOBARI, H. e outros. Weekly wellness variations to identify "
         "non-functional overreaching syndrome in Turkish national youth "
         "wrestlers. Sustainability, v. 13, n. 9, art. 4667, 2021."),
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
("nota", "ROHLFS, I. C. P. M. e outros. Prevalence of specific mood profile "
         "clusters among elite and youth athletes at a Brazilian sports "
         "club. Sports, v. 12, n. 7, art. 195, 2024."),
("nota", "TERRY, P. C.; PARSONS-SMITH, R. L. Mood profiling for sustainable "
         "mental health among athletes. Sustainability, v. 13, n. 11, art. "
         "6116, 2021."),
]
