"""Conteúdo do relatório de auditoria das classificações de perfil de humor.

Restrições de redação: nenhum travessão, nenhum traço de meia risca e nenhum
gerúndio.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reconciliar import (N_A, SERIE_A, SERIE_B, SERIE_C, br, faixas,
                         sinal)  # noqa: E402

TITULO = ("Auditoria das classificações de perfil de humor no projeto de "
          "handebol")
SUBTITULO = ("Três séries divergentes, a origem de cada uma e qual delas deve "
             "prevalecer")

ABERTURA = [
 ("O QUE MOTIVOU ESTA AUDITORIA",
  "O orientador questionou o valor de prevalência do perfil iceberg no dia de "
  "repouso. Os manuscritos em circulação relatam 71,4%, e a lembrança dele "
  "apontava para algo entre 40% e 42%, com queda para cerca de 19% no último "
  "dia. A auditoria varreu os dezoito documentos do projeto e confirma que a "
  "objeção procede: existem três séries distintas, o número correto do perfil "
  "iceberg no dia 1 é 40,5%, e o valor de 71,4% pertence a outro critério de "
  "classificação, que foi indevidamente misturado à narrativa dos seis "
  "perfis."),
]

FONTE_TABELA = "Fonte: auditoria dos documentos do projeto (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."

_fa = faixas(SERIE_A, 1, 3)
_fb = faixas(SERIE_B, 0, 1)

TABELAS = {

"series": {
 "numero": 1,
 "titulo": ("As três séries de classificação encontradas, com a regra de cada "
            "uma e o documento de origem"),
 "cabecalho": ["Série", "Regra de classificação", "Documento de origem",
               "Iceberg no dia 1", "Iceberg no dia 7"],
 "linhas": [
  ["A", "Escores convertidos em T, com média 50 e desvio 10, e atribuição "
        "pela forma do perfil",
   "Artigo_Perfil_de_humor__handebol.docx, Tabela 12",
   f"{br(SERIE_A['Iceberg'][1])}%", f"{br(SERIE_A['Iceberg'][3])}%"],
  ["B", "Padronização dentro da própria amostra e atribuição ao centroide "
        "canônico mais próximo",
   "Artigo_Final_.docx, Tabela 21, e duas cópias",
   f"{br(SERIE_B['Iceberg'][0])}%", f"{br(SERIE_B['Iceberg'][1])}%"],
  ["C", "Critério de Morgan sobre escores brutos: vigor acima das cinco "
        "subescalas negativas",
   "Artigo_Final_.docx, Tabela 20",
   f"{br(SERIE_C['Perfil iceberg'][0])}%",
   f"{br(SERIE_C['Perfil iceberg'][1])}%"],
 ],
 "nota": ("Nota: a série C não classifica nos seis perfis. Ela apenas separa "
          "iceberg de não iceberg pela ordem entre o vigor e as cinco "
          "negativas, sobre escores brutos. Como quatro dessas subescalas têm "
          "mediana zero nesta amostra, a condição é satisfeita com "
          "facilidade, e por isso a série C produz o valor mais alto das "
          "três. Ela não é comparável às séries A e B."),
},

"comparacao": {
 "numero": 2,
 "titulo": ("Comparação perfil a perfil entre a série A e a série B, no "
            "primeiro e no último dia"),
 "cabecalho": ["Perfil", "Dia 1, série A", "Dia 1, série B", "Diferença",
               "Dia 7, série A", "Dia 7, série B", "Diferença"],
 "linhas": [
  [p, f"{br(SERIE_A[p][1])}%", f"{br(SERIE_B[p][0])}%",
   sinal(SERIE_A[p][1] - SERIE_B[p][0]),
   f"{br(SERIE_A[p][3])}%", f"{br(SERIE_B[p][1])}%",
   sinal(SERIE_A[p][3] - SERIE_B[p][1])]
  for p in sorted(SERIE_A, key=lambda x: -SERIE_A[x][1])
 ],
 "nota": ("Nota: submerso e iceberg invertido são idênticos nas duas séries, "
          "nos dois dias. Toda a divergência se concentra em quatro perfis. "
          "Isso indica que os dados de entrada são os mesmos e que a "
          "diferença está na regra de fronteira, não na coleta."),
},

"faixas": {
 "numero": 3,
 "titulo": ("Faixas de significado nas duas séries: a conclusão substantiva "
            "se inverte"),
 "cabecalho": ["Faixa", "Série A, dia 1", "Série A, dia 7",
               "Série A, diferença", "Série B, dia 1", "Série B, dia 7",
               "Série B, diferença"],
 "linhas": [
  [nome, f"{br(_fa[nome][0])}%", f"{br(_fa[nome][1])}%",
   sinal(_fa[nome][1] - _fa[nome][0]),
   f"{br(_fb[nome][0])}%", f"{br(_fb[nome][1])}%",
   sinal(_fb[nome][1] - _fb[nome][0])]
  for nome in ("Favorável", "Neutro", "De risco")
 ],
 "nota": ("Nota: a faixa favorável reúne o perfil iceberg; a neutra reúne "
          "superfície e submerso; a de risco reúne barbatana de tubarão, "
          "iceberg invertido e Everest invertido, que são os três perfis que "
          "a literatura associa a risco à saúde mental. Pela série A a faixa "
          "de risco sobe 17,3 pontos percentuais ao longo da semana; pela "
          "série B ela cai 2,1 pontos. As duas séries levam a recomendações "
          "opostas."),
},

"denominadores": {
 "numero": 4,
 "titulo": "Denominadores declarados em cada fonte, e a incoerência entre eles",
 "cabecalho": ["Fonte", "Dia 1", "Dia 7", "Observação"],
 "linhas": [
  ["Tabela 12, série A", f"{N_A[0]} observações", f"{N_A[1]} observações",
   "Base das percentagens da série A"],
  ["Tabela 52 do relatório completo", "27 atletas", "21 atletas",
   "Contagem de atletas com coleta válida no dia"],
  ["Esquema do delineamento", "27 atletas, 1 coleta",
   "27 atletas, 2 coletas",
   "Máximo teórico de 27 no dia 1 e de 54 no dia 7"],
  ["Resumo do manuscrito", "456 observações no total", "",
   "O desenho comporta no máximo 351"],
 ],
 "nota": ("Nota: nenhuma das combinações fecha. Se o dia 1 é de coleta única, "
          "o máximo é 27 observações e não 42. Se o dia 7 tem 21 atletas, o "
          "máximo é 42 observações e não 46. A auditoria não consegue "
          "resolver isso sem a planilha de fluxo de dados, e por isso as "
          "percentagens de qualquer série permanecem provisórias até que o "
          "denominador seja publicado."),
},
}

BLOCOS = [

("h1", "1 A RESPOSTA CURTA"),
("p", "**O perfil iceberg no dia de repouso é de 40,5%, e não de 71,4%.** No "
      "último dia ele cai para 17,4%. Os dois números vêm da Tabela 12 do "
      "documento Artigo_Perfil_de_humor__handebol.docx, que classifica os "
      "seis perfis sobre escores T, conforme o procedimento da literatura. A "
      "lembrança do orientador, de algo entre 40% e 42% na partida e cerca de "
      "19% na chegada, está correta."),
("p", "O valor de 71,4% que circula nos manuscritos pertence a outro "
      "critério. Ele é o critério de Morgan aplicado sobre escores brutos, "
      "que apenas verifica se o vigor supera as cinco subescalas negativas. "
      "Nesta amostra, quatro dessas subescalas têm mediana zero, de modo que "
      "a condição é satisfeita com facilidade e o percentual infla. Esse "
      "critério não classifica nos seis perfis e não deveria ter sido "
      "apresentado ao lado deles como se fosse a mesma coisa."),
("p", "**A consequência é séria e vai além do número.** A conclusão que os "
      "manuscritos sustentavam até aqui, a de que a faixa de risco permanece "
      "estável ao longo da semana, decorre da série errada. Pela "
      "classificação correta, a faixa de risco sobe de 26,2% para 43,5% das "
      "observações, um ganho de 17,3 pontos percentuais, com o perfil "
      "barbatana de tubarão a saltar de 2,4% para 28,3%. A equipe não apenas "
      "perde o padrão favorável: ela migra para os perfis que a literatura "
      "associa a risco."),

("h1", "2 O QUE A AUDITORIA VARREU"),
("p", "Foram varridos dezoito documentos, entre os sete gerados neste "
      "projeto e os onze enviados originalmente, mais o organograma em "
      "página web. O procedimento extrai cada parágrafo e cada linha de "
      "tabela, recorta os trechos que citam um perfil junto de um número e "
      "os agrupa por documento. O código está em "
      "scripts/auditoria/perfis.py e pode ser executado de novo a qualquer "
      "momento."),
("p", "A varredura encontrou três séries distintas de classificação, e não "
      "duas. Elas estão na Tabela 1, com a regra de cada uma e o documento "
      "de origem."),
("tab", "series"),

("h1", "3 ONDE AS DUAS CLASSIFICAÇÕES DIVERGEM"),
("p", "A Tabela 2 compara perfil a perfil. O detalhe mais informativo dela é "
      "o que não diverge: submerso e iceberg invertido têm exatamente os "
      "mesmos valores nas duas séries, nos dois dias. Isso demonstra que os "
      "dados de entrada são os mesmos e que a divergência está na regra de "
      "fronteira entre perfis, não na coleta nem no cálculo dos escores."),
("tab", "comparacao"),
("p", "A divergência se concentra em quatro perfis. A série B empurra 21,4 "
      "pontos percentuais a mais para o perfil superfície no dia 1 e 32,6 "
      "pontos a mais no dia 7, e retira essa massa sobretudo do iceberg, do "
      "Everest invertido e, no dia 7, da barbatana de tubarão. Esse é o "
      "comportamento esperado de uma atribuição por centroide mais próximo "
      "sobre escores padronizados internamente: a média do próprio grupo "
      "passa a ser a linha de água e as observações se comprimem em direção "
      "ao centro, que é justamente onde fica o centroide do perfil "
      "superfície."),

("h1", "4 POR QUE A SÉRIE A DEVE PREVALECER"),
("lista", [
 "**Ela segue o procedimento da literatura.** O método declarado converte os "
 "escores em T, com média 50 e desvio 10, que é a escala sobre a qual os seis "
 "perfis foram definidos. A série B abandona essa escala por não haver normas "
 "populacionais e substitui a regra de forma por proximidade a centroide.",
 "**Ela reproduz a forma esperada dos perfis.** A prevalência do iceberg em "
 "repouso, de 40,5%, é da mesma ordem dos 29,4% da amostra normativa. A série "
 "B produz 21,4% de iceberg e 47,6% de superfície, contra 14,8% de superfície "
 "na norma, o que é um afastamento de 32,8 pontos percentuais sem explicação "
 "substantiva.",
 "**Ela mostra o perfil que a teoria prevê para o fim de uma semana de "
 "carga.** A barbatana de tubarão, definida pelo vigor mais baixo de todos os "
 "perfis com fadiga alta, salta de 2,4% para 28,3% e se torna o perfil mais "
 "frequente do último dia, empatado com superfície. É exatamente o desfecho "
 "que o eixo vigor e fadiga desta amostra faz esperar, com o vigor em queda "
 "de 7,61 para 4,49 e a fadiga em alta de 3,96 para 7,46.",
 "**A comparação externa fica coerente.** A faixa de risco no dia 1 é de "
 "26,2%, quase idêntica aos 26,5% relatados na amostra brasileira de 898 "
 "atletas classificada pelos mesmos seis perfis. Pela série B a faixa de "
 "risco seria de 23,8% e a comparação também funcionaria, mas ao custo de uma "
 "distribuição interna que não se parece com nenhuma amostra publicada.",
]),
("tab", "faixas"),
("p", "A Tabela 3 mostra por que a escolha da série não é um detalhe de "
      "método. Pela série A a equipe termina a semana com 43,5% das "
      "observações em perfil de risco, quase o dobro do início. Pela série B "
      "a faixa de risco fica estável e a conclusão vira outra, a de que a "
      "semana apenas dissolve o padrão favorável na indiferenciação. A "
      "primeira leitura pede intervenção na carga e conversa individual com "
      "quase metade do elenco na véspera do jogo. A segunda pede ajuste "
      "fino. São recomendações opostas a partir do mesmo conjunto de dados."),

("h1", "5 O QUE AINDA NÃO FECHA"),
("p", "A auditoria resolve a pergunta sobre qual série usar, mas não resolve "
      "os denominadores. A Tabela 4 reúne o que cada fonte declara."),
("tab", "denominadores"),
("p", "Enquanto o fluxo de dados não for publicado, com atletas por dia e por "
      "coleta, qualquer percentual permanece provisório na terceira casa. A "
      "ordem de grandeza e a direção do movimento, porém, não dependem disso: "
      "a contagem bruta da série A é de 17 observações em iceberg no dia 1 "
      "contra 8 no dia 7, e de 1 observação em barbatana de tubarão no dia 1 "
      "contra 13 no dia 7. Essa mudança de contagem é grande demais para ser "
      "artefato de denominador."),
("p", "Há ainda um quarto conjunto de valores que a auditoria não conseguiu "
      "localizar. A captura de tela enviada pelo orientador menciona iceberg "
      "de 48% para 22% e barbatana de tubarão de 4% para 22%. Nenhum "
      "documento do projeto contém esses valores. A direção do movimento "
      "coincide com a série A, mas os números não. É preciso saber de qual "
      "análise essa tela saiu antes de considerá-la uma quarta série."),

("h1", "6 O QUE FOI CORRIGIDO E O QUE FALTA"),
("lista", [
 "**Corrigido.** Os manuscritos passam a usar a série A para os seis perfis, "
 "com iceberg de 40,5% para 17,4% e barbatana de tubarão de 2,4% para 28,3%.",
 "**Corrigido.** A conclusão sobre a faixa de risco foi invertida: ela sobe "
 "17,3 pontos percentuais, e não permanece estável.",
 "**Corrigido.** O critério de Morgan passa a aparecer apenas como "
 "contraponto declarado, com a ressalva de que o efeito piso o infla, e "
 "nunca ao lado dos seis perfis como se fosse equivalente.",
 "**Falta.** A série A só existe para o dia 1 e para o dia 7. Não há "
 "classificação por perfil nos dias 2 a 6 nem separação entre dias com e sem "
 "HIIT. A curva diária dos perfis exige recomputar a classificação a partir "
 "dos dados brutos.",
 "**Falta.** O denominador de cada dia, que a Tabela 4 mostra incoerente "
 "entre as fontes.",
 "**Falta.** A origem dos valores de 48% e 22% da captura de tela.",
]),
]
