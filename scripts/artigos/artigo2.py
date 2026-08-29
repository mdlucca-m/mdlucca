"""Artigo 2: impacto da fadiga sobre os perfis de humor.

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
from dados import METRICAS_PERFIL, PERFIL_DIA, PERFIS_T  # noqa: E402

TITULO = ("Impacto da fadiga sobre os perfis de humor em atletas de handebol "
          "de elite: assinatura de sobrecarga e recomendações de "
          "monitoramento")
SUBTITULO = ("Estudo longitudinal de um microciclo pré-competitivo de sete "
             "dias")

ABERTURA = [
 ("RESUMO",
  "A perda do perfil de humor favorável é um dos sinais mais precoces de "
  "sobrecarga em atletas, mas nenhum estudo descreveu esse deslocamento no "
  "handebol. Este estudo acompanhou 27 atletas de handebol masculino de "
  "primeira divisão ao longo do microciclo de sete dias que antecede a "
  "competição, com três sessões equivalentes de treinamento intervalado de "
  "alta intensidade. A proporção de atletas em perfil iceberg caiu de 71,4% "
  "para 32,6% e a de humor perturbado subiu de 47,6% para 71,7%. Entre a "
  "primeira e a terceira sessão de HIIT, a frequência cardíaca de pico caiu "
  "de 184 para 181 batimentos por minuto enquanto o esforço percebido subiu "
  "de 8,5 para 9,1 e a perturbação total do humor subiu 1,76 ponto por "
  "sessão. O mesmo estímulo externo passou a custar mais. Mais da metade dos "
  "atletas ultrapassou o menor valor detectável em perturbação total, vigor e "
  "fadiga ao longo da semana, e a recuperação noturna devolveu cerca de dois "
  "terços da fadiga acumulada. O conjunto configura uma assinatura de "
  "sobrecarga. Sem medida de desempenho após o microciclo, o estudo não "
  "diagnostica overreaching funcional ou não funcional, e sim descreve o "
  "risco e propõe o monitoramento correspondente."),
 ("PALAVRAS-CHAVE",
  "handebol; carga de treino; perfil de humor; overreaching; monitoramento."),
]

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."

def _n(v: float) -> str:
    """Sem casa decimal quando o valor é inteiro, como na frequência
    cardíaca."""
    return F.br(v, 0 if float(v).is_integer() else 1)


_SESSAO = ["PTH (TMD)", "Fadiga (BRUMS)", "Fadiga física", "Fadiga mental",
           "Sonolência", "Vigor", "TQR (recuperação)", "PSS (estresse)"]

TABELAS = {

"carga": {
 "numero": 1,
 "titulo": "Carga de treino de cada dia do microciclo",
 "cabecalho": ["Dia", "Data", "Conteúdo", "Sessões", "Duração",
               "Volume relativo", "FC de pico", "PSE", "Exigência"],
 "linhas": [[str(d), data, conteudo, str(n), dur, vol, fc, pse, exig]
            for d, data, conteudo, n, dur, vol, fc, pse, exig in F.CARGA],
 "nota": ("Nota: volume relativo é a duração do dia em percentual do dia mais "
          "longo. PSE é o esforço percebido da sessão, de 0 a 10. Os dias 2, "
          "4 e 7 combinam treinamento intervalado de alta intensidade com "
          "trabalho técnico e tático, com metade do volume e a maior "
          "intensidade da semana. Fonte primária: Tabela 72 do relatório "
          "completo."),
},

"sessoes": {
 "numero": 2,
 "titulo": ("Progressão entre as três sessões equivalentes de HIIT: o que a "
            "sessão entregou e o que ela custou"),
 "cabecalho": ["Indicador", "Sessão 1 (dia 2)", "Sessão 2 (dia 4)",
               "Sessão 3 (dia 7)", "Tendência", "Teste"],
 "linhas": (
  [["**Estímulo externo entregue**", "", "", "", "", ""]]
  + [[nome, _n(v[0]), _n(v[1]), _n(v[2]),
      "queda" if v[2] < v[0] else "aumento", v[3]]
     for nome, v in F.ESTIMULO.items()]
  + [["**Custo interno percebido**", "", "", "", "", ""]]
  + [[nome, F.br(F.SESSOES[nome][0], 1), F.br(F.SESSOES[nome][1], 1),
      F.br(F.SESSOES[nome][2], 1),
      f"{F.sinal(F.SESSOES[nome][3], 2)} por sessão",
      "p < 0,05" if F.SESSOES[nome][4] else "n.s."]
     for nome in _SESSAO]
 ),
 "nota": ("Nota: as três sessões seguem o mesmo protocolo. O coeficiente de "
          "variação intraindividual da frequência cardíaca de pico entre elas "
          "é de 1,7%, o que confirma entrega consistente do estímulo externo. "
          "A tendência do custo interno é a inclinação por sessão do modelo "
          "misto. TQR é a escala de recuperação total e PSS é a escala de "
          "estresse percebido. Fonte primária: Tabelas 49 e 69 do relatório "
          "completo."),
},

"bayes": {
 "numero": 3,
 "titulo": ("Contraste entre a primeira e a terceira sessão de HIIT, com "
            "fator de Bayes"),
 "cabecalho": ["Variável", "Tamanho de efeito (dz)", "Fator de Bayes",
               "Força da evidência"],
 "linhas": [[nome, F.sinal(dz, 2), bf, forca]
            for nome, (dz, bf, forca) in
            sorted(F.BAYES.items(), key=lambda x: -abs(x[1][0]))],
 "nota": ("Nota: fator de Bayes a favor da diferença, salvo indicação "
          "contrária. Valores acima de 10 indicam evidência forte, entre 3 e "
          "10 moderada e entre 1 e 3 anedótica. O contraste de fadiga física "
          "é o único com evidência decisiva. Fonte primária: Tabela 71 do "
          "relatório completo."),
},

"mudanca": {
 "numero": 4,
 "titulo": ("Mudança confiável atleta a atleta do dia 1 ao dia 7 e proporção "
            "acima do menor valor detectável"),
 "cabecalho": ["Variável", "n", "Mudança desfavorável", "Sem mudança",
               "Mudança favorável", "MDC₉₅",
               "Acima do MDC na semana (%)"],
 "linhas": [
  [nome, str(n),
   str(aumento if F.AUMENTO_RUIM[nome] else reducao),
   str(estavel),
   str(reducao if F.AUMENTO_RUIM[nome] else aumento),
   F.br(mdc, 2),
   f"{F.MDC[chave][3]}" if chave else "n.d."]
  for (nome, (n, aumento, estavel, reducao, mdc)), chave in
  zip(F.MUDANCA.items(), ["", "Fadiga", "PTH (TMD)", "Vigor"])
 ],
 "nota": ("Nota: mudança confiável é a que excede o menor valor detectável a "
          "95%, calculado sobre o ICC(2,1) e o erro-padrão de medida. A "
          "direção desfavorável é o aumento em todas as variáveis, exceto no "
          "vigor, em que é a redução. A última coluna vem da Tabela 46 e usa "
          "o MDC derivado do ômega, o que explica a diferença em relação à "
          "contagem das colunas anteriores. Fonte primária: Tabelas 34 e 46 "
          "do relatório completo."),
},

"recuperacao": {
 "numero": 5,
 "titulo": ("Recuperação noturna média e deslocamento da linha de base ao "
            "longo do microciclo"),
 "cabecalho": ["Variável", "Recuperação noturna (%)",
               "Deslocamento do dia 1 ao dia 7"],
 "linhas": [[nome, F.br(rec, 1), F.sinal(desloc, 2)]
            for nome, (rec, desloc) in F.RECUPERACAO.items()],
 "nota": ("Nota: recuperação noturna é o percentual da variação da sessão que "
          "a medida da manhã seguinte reverte. Valor abaixo de 100% indica "
          "resíduo que se soma ao dia seguinte; acima de 100% indica "
          "sobrecompensação. Fonte primária: Tabela 33 do relatório "
          "completo."),
},

"perfis": {
 "numero": 6,
 "titulo": ("Deslocamento dos perfis de humor ao longo do microciclo e entre "
            "os dois tipos de dia"),
 "cabecalho": ["Critério e perfil", "Dia 1 (%)", "Dia 7 (%)",
               "Diferença (p.p.)", "Dias de HIIT (%)", "Dias sem HIIT (%)"],
 "linhas": (
  [["**Critério de Morgan**", "", "", "", "", ""],
   ["Perfil iceberg", F.br(PERFIL_DIA[1][0], 1), F.br(PERFIL_DIA[7][0], 1),
    F.sinal(PERFIL_DIA[7][0] - PERFIL_DIA[1][0], 1), "n.a.", "n.a."],
   ["Humor perturbado", F.br(PERFIL_DIA[1][1], 1), F.br(PERFIL_DIA[7][1], 1),
    F.sinal(PERFIL_DIA[7][1] - PERFIL_DIA[1][1], 1), "n.a.", "n.a."],
   ["**Critério de Parsons-Smith**", "", "", "", "", ""]]
  + [[nome, F.br(v[1], 1), F.br(v[3], 1), F.sinal(v[3] - v[1], 1),
      "n.d.", "n.d."] for nome, v in PERFIS_T.items()]
 ),
 "nota": ("Nota: os dois critérios não são equivalentes. Sobre as métricas "
          "contínuas do perfil, o dia de HIIT reduz o índice iceberg "
          f"(dz = {F.sinal(METRICAS_PERFIL['Índice iceberg (z)'][2], 2)}), "
          "inverte o eixo vigor e fadiga "
          f"(dz = {F.sinal(METRICAS_PERFIL['Eixo vigor e fadiga'][2], 2)}) e "
          "eleva a perturbação total "
          f"(dz = {F.sinal(METRICAS_PERFIL['PTH (TMD)'][2], 2)}), com os três "
          "intervalos de confiança afastados do zero. Fonte primária: Tabelas "
          "20, 21 e 22 do relatório completo."),
},
}

BLOCOS = [
("h1", "1 INTRODUÇÃO"),
("p", "A carga de treino cobra do atleta um custo psicológico que aparece "
      "antes da queda de desempenho, e o perfil de humor é a forma mais "
      "econômica de acompanhar esse custo. O perfil iceberg invertido é "
      "apontado desde os anos noventa como indicador de síndrome de "
      "overtraining (Budgett, 1998), e a literatura de sobrecarga usa o humor "
      "como um dos componentes centrais do monitoramento (Main e Grove, "
      "2009; Aubry e outros, 2014)."),
("p", "Essa literatura trabalha com escores contínuos ou com questionários de "
      "bem-estar (Nobari e outros, 2021), quase nunca com a migração entre "
      "perfis. E o handebol está fora dela: dos 32 estudos de humor em "
      "handebol publicados entre 2006 e 2026, apenas um tem desenho "
      "longitudinal, e nenhum relaciona o deslocamento do perfil ao tipo de "
      "carga."),
("p", "Este estudo acompanha o deslocamento dos perfis de humor ao longo de "
      "um microciclo pré-competitivo, quantifica a progressão do custo "
      "psicológico entre três sessões equivalentes de treinamento intervalado "
      "de alta intensidade e identifica quais variáveis atingem mudança "
      "confiável atleta a atleta."),

("h1", "2 MÉTODO"),
("h2", "2.1 Participantes e delineamento"),
("p", f"Participaram {F.AMOSTRA['atletas']} atletas de handebol masculino de "
      f"primeira divisão, com {F.AMOSTRA['idade']} anos de idade e "
      f"{F.AMOSTRA['experiencia']} anos de experiência. "
      f"{F.AMOSTRA['completos']} completaram as sete coletas. O delineamento "
      "é observacional, longitudinal e prospectivo, com medidas repetidas "
      "intraindividuais e sem manipulação experimental da carga. A equipe "
      "treinou conforme o planejamento da comissão técnica, e o estudo "
      "registrou a resposta psicológica a esse planejamento."),
("h2", "2.2 O microciclo e a carga"),
("p", "O microciclo de sete dias tem dois tipos de dia (Tabela 1). Os dias 2, "
      "4 e 7 combinam HIIT com trabalho técnico e tático, com duas sessões, "
      "2,0 a 2,5 horas e 47% do volume do dia mais longo, na maior "
      "intensidade da semana. Os dias 3, 5 e 6 combinam trabalho técnico e "
      "tático com força e, nos dias 3 e 5, jogo amistoso, com três sessões, "
      "4,5 a 5,0 horas e volume máximo. O dia 1 é de repouso e serve de linha "
      "de base."),
("tab", "carga"),
("h2", "2.3 Instrumentos"),
("p", "O humor foi aferido pela Escala de Humor de Brunel, com 24 itens e "
      "seis subescalas de 0 a 16 pontos, em duas coletas por dia de treino. A "
      "Perturbação Total do Humor soma as cinco subescalas negativas e "
      "subtrai o vigor. Foram registradas ainda a fadiga física e a fadiga "
      "mental em escalas de 0 a 10, a recuperação total percebida pela escala "
      "TQR, a sonolência, o estresse percebido pela escala PSS-14, o esforço "
      "percebido da sessão e, nos dias de HIIT, a frequência cardíaca de "
      "pico, a recuperação da frequência cardíaca em um minuto e a deriva "
      "cardíaca."),
("h2", "2.4 Análise"),
("p", "O efeito do dia e o efeito do dia de HIIT foram testados por modelo "
      "misto com intercepto aleatório por atleta. A progressão entre as três "
      "sessões de HIIT foi descrita pela inclinação por sessão e testada pelo "
      "teste de Friedman para as medidas fisiológicas. O contraste entre a "
      "primeira e a terceira sessão foi acompanhado do fator de Bayes com "
      "prior JZS, o que permite quantificar também a evidência a favor da "
      "ausência de diferença. A mudança individual foi classificada como "
      "confiável quando excedeu o menor valor detectável a 95%, calculado "
      "sobre o ICC(2,1) e o erro-padrão de medida. Os perfis foram "
      "classificados pelo critério de Morgan e pelo de Parsons-Smith, "
      "conforme descrito no primeiro artigo desta série."),

("h1", "3 RESULTADOS"),
("h2", "3.1 O estímulo entregue e o custo cobrado"),
("p", "As três sessões de HIIT seguiram o mesmo protocolo, com coeficiente de "
      "variação intraindividual de 1,7% na frequência cardíaca de pico. O que "
      "mudou foi o custo (Tabela 2). A frequência cardíaca de pico caiu de "
      "184 para 181 batimentos por minuto entre a primeira e a terceira "
      "sessão, com p = 0,001, enquanto o esforço percebido subiu de 8,5 para "
      "9,1, com p = 0,004."),
("tab", "sessoes"),
("fig", "a2_sessoes.png", 16.0,
 "Figura 1 - Estímulo externo entregue e esforço percebido ao longo das três "
 "sessões (A) e progressão do custo psicológico nas mesmas sessões (B)"),
("p", "A Figura 1 resume a dissociação. No painel A, as duas curvas divergem: "
      "o atleta alcança uma frequência cardíaca mais baixa e ainda assim "
      "percebe mais esforço. No painel B, as seis variáveis psicológicas "
      "pioram, sem exceção. A perturbação total sobe 1,76 ponto por sessão, a "
      "fadiga do BRUMS 1,08, a sonolência 1,05 e a fadiga física 1,01, "
      "enquanto o vigor cai 0,68 e a recuperação percebida cai 0,83. O "
      "estresse percebido é a única medida sem tendência, o que descarta "
      "estresse de vida como explicação."),
("p", "O contraste entre a primeira e a terceira sessão (Tabela 3) confirma a "
      "leitura e a gradua. A fadiga física tem efeito de 1,87 com evidência "
      "decisiva, o vigor 0,79 com evidência forte, a fadiga do BRUMS 0,65 e a "
      "sonolência 0,64 com evidência moderada. A perturbação total tem efeito "
      "de 0,40 com evidência ausente, o que decorre da variância alta desse "
      "índice composto e recomenda cautela no uso dele para decisão sobre um "
      "atleta isolado."),
("tab", "bayes"),
("h2", "3.2 Quem de fato mudou"),
("p", "A leitura de grupo esconde a distribuição individual. Do dia 1 ao dia "
      "7, quatorze dos vinte e um atletas com dados completos registram "
      "aumento confiável de fadiga física, oito registram aumento confiável "
      "de fadiga do BRUMS e de perturbação total, e cinco registram redução "
      "confiável de vigor (Tabela 4). Nenhum atleta melhora em fadiga física."),
("tab", "mudanca"),
("fig", "a2_mdc.png", 16.0,
 "Figura 2 - Proporção de atletas acima do menor valor detectável na sessão e "
 "na semana (A) e recuperação noturna média por variável (B)"),
("p", "O painel A da Figura 2 separa a resposta aguda da acumulada. Na sessão "
      "isolada, no máximo 22% dos atletas ultrapassam o erro de medida. Na "
      "semana, a proporção sobe para 62% em fadiga e 52% em perturbação total "
      "e em vigor. A carga de uma sessão é ruído para a maioria dos atletas; "
      "a carga da semana não é."),
("p", "O painel B explica o mecanismo. A noite devolve entre 66,8% e 69,3% da "
      "fadiga acumulada no dia, o que deixa um resíduo diário de cerca de um "
      "terço. O vigor recupera 113,2%, isto é, sobrecompensa, e ainda assim "
      "termina a semana 3,72 pontos abaixo da linha de base, porque a "
      "sobrecompensação parte de um patamar cada vez mais baixo."),
("tab", "recuperacao"),
("h2", "3.3 Migração dos perfis"),
("p", "A proporção de atletas em perfil iceberg cai de 71,4% no dia 1 para "
      "32,6% no dia 7, perda de 38,8 pontos percentuais, e a de humor "
      "perturbado sobe de 47,6% para 71,7%, ganho de 24,1 pontos (Tabela 6). "
      "A queda não é gradual: o iceberg despenca já no dia 2, primeiro dia de "
      "HIIT, recupera parte no dia 5 e volta a cair nos dois últimos dias. As "
      "duas curvas se cruzam entre os dias 4 e 5, momento em que a maioria da "
      "equipe deixa de apresentar perfil favorável."),
("tab", "perfis"),
("fig", "fig_perfis.png", 16.0,
 "Figura 3 - Migração diária pelo critério de Morgan (A), deslocamento entre "
 "os perfis de Parsons-Smith (B) e efeito do dia de HIIT sobre as métricas do "
 "perfil (C)"),
("p", "Pela classificação de Parsons-Smith, o deslocamento tem direção única: "
      "o perfil iceberg recua 23,1 pontos percentuais e a barbatana de tubarão "
      "avança 25,9 pontos, e passa a dividir com o superfície a primeira "
      "posição no último dia. A faixa de risco, que reúne barbatana de "
      "tubarão, iceberg invertido e Everest invertido, sobe de 26,2% para "
      "43,5% das observações. O quadro é de migração para o esgotamento "
      "energético, e não para o sofrimento psíquico: os outros dois perfis de "
      "risco recuam no mesmo intervalo."),

("h1", "4 DISCUSSÃO"),
("p", "O achado central é a dissociação entre o estímulo externo entregue e o "
      "custo interno cobrado. Três sessões com protocolo equivalente e "
      "frequência cardíaca de pico em queda produzem esforço percebido em "
      "alta e perturbação total quase duplicada. Essa dissociação é o "
      "marcador clássico de sobrecarga acumulada, descrito em corredores, "
      "nadadores e tenistas (Aubry e outros, 2014; Flatt e outros, 2017), e "
      "aparece aqui pela primeira vez em handebol."),
("p", "O conjunto reúne quatro elementos que a literatura associa ao "
      "overreaching: perda progressiva de vigor, acúmulo de fadiga, queda da "
      "recuperação percebida e aumento do esforço percebido para o mesmo "
      "trabalho externo. A esses soma-se a migração do perfil, com perda de "
      "38,8 pontos percentuais no padrão iceberg."),
("p", "**O que este estudo não pode afirmar.** Overreaching funcional e não "
      "funcional são definidos pela queda de desempenho seguida de "
      "recuperação em prazos distintos, de dias a semanas no primeiro caso e "
      "de semanas a meses no segundo (Bellinger, 2020). O estudo não mediu "
      "desempenho depois do microciclo, e por isso descreve uma assinatura de "
      "sobrecarga, não um diagnóstico. A distinção não é formalidade: sem o "
      "desfecho de desempenho, o mesmo padrão psicológico é compatível tanto "
      "com adaptação funcional planejada quanto com sobrecarga indesejada."),
("p", "A leitura prática, porém, independe do diagnóstico. O dia 7 repete o "
      "protocolo do dia 2 e custa quase o dobro em perturbação total. Esse "
      "dia é a véspera da competição. Uma equipe que chega ao primeiro jogo "
      "com dois terços dos atletas em humor perturbado e um terço em perfil "
      "favorável entra em desvantagem psicológica, qualquer que seja o rótulo "
      "fisiológico do estado."),
("p", "Três limitações restringem a generalização. O delineamento é "
      "observacional, sem aleatorização nem grupo de controle. A amostra tem "
      "27 atletas de uma única equipe, dos quais 19 completaram as sete "
      "coletas e 21 têm o par completo do dia 1 e do dia 7. E o período "
      "observado é um único microciclo, o que impede separar o efeito desta "
      "semana do efeito da fase da temporada."),

("h1", "5 RECOMENDAÇÕES PARA A COMISSÃO TÉCNICA"),
("lista", [
 "**Acompanhar a média móvel, não o valor do dia.** Nenhuma leitura isolada "
 "do BRUMS ultrapassa 0,59 de confiabilidade nesta população, e no máximo 22% "
 "dos atletas ultrapassam o erro de medida em uma sessão.",
 "**Vigiar a terceira sessão de alta intensidade da semana.** O custo "
 "psicológico do HIIT cresce 1,76 ponto de perturbação total por sessão, e a "
 "terceira sessão custa quase o dobro da primeira.",
 "**Usar a dissociação como gatilho.** Frequência cardíaca de pico em queda "
 "com esforço percebido em alta, na mesma sessão, é o sinal mais precoce "
 "disponível e não depende de questionário.",
 "**Proteger a véspera.** A carga da última sessão de alta intensidade antes "
 "da competição precisa considerar o resíduo da semana, e não apenas a "
 "prescrição isolada do dia.",
 "**Tratar a recuperação noturna como recurso limitado.** A noite devolve "
 "cerca de dois terços da fadiga do dia, o que faz o resíduo se acumular ao "
 "longo de dias consecutivos de treino.",
]),

("h1", "6 CONCLUSÃO"),
("p", "Ao longo de um microciclo pré-competitivo de sete dias, atletas de "
      "handebol de elite perderam o perfil de humor favorável em 38,8 pontos "
      "percentuais e passaram a apresentar humor perturbado em 71,7% das "
      "observações. Entre três sessões equivalentes de HIIT, o estímulo "
      "externo entregue caiu enquanto o custo psicológico quase dobrou. Mais "
      "da metade dos atletas ultrapassou o menor valor detectável em "
      "perturbação total, vigor e fadiga na escala da semana, e a recuperação "
      "noturna devolveu apenas dois terços da fadiga diária. O conjunto "
      "configura uma assinatura de sobrecarga que a comissão técnica pode "
      "monitorar com instrumentos de baixo custo, ainda que o diagnóstico de "
      "overreaching exija medida de desempenho que este estudo não coletou."),

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
("nota", "BUDGETT, R. Fatigue and underperformance in athletes: the "
         "overtraining syndrome. British Journal of Sports Medicine, v. 32, "
         "n. 2, p. 107-110, 1998."),
("nota", "FLATT, A. A. e outros. Heart rate variability and psychometric "
         "responses to overload and tapering in collegiate sprint-swimmers. "
         "Journal of Science and Medicine in Sport, v. 20, n. 6, p. 606-610, "
         "2017."),
("nota", "MAIN, L. C.; GROVE, J. R. A multi-component assessment model for "
         "monitoring training distress among athletes. European Journal of "
         "Sport Science, v. 9, n. 4, p. 195-202, 2009."),
("nota", "NOBARI, H. e outros. Weekly wellness variations to identify "
         "non-functional overreaching syndrome in Turkish national youth "
         "wrestlers. Sustainability, v. 13, n. 9, art. 4667, 2021."),
("nota", "PARSONS-SMITH, R. L.; TERRY, P. C.; MACHIN, M. A. Identification "
         "and description of novel mood profile clusters. Frontiers in "
         "Psychology, v. 8, art. 1958, 2017."),
("nota", "SCHMIKLI, S. L. e outros. Can we detect non-functional "
         "overreaching in young elite soccer players and middle-long distance "
         "runners using field performance tests? British Journal of Sports "
         "Medicine, v. 45, n. 8, p. 631-636, 2010."),
]
