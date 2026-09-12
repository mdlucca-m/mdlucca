#!/usr/bin/env python3
"""Conteúdo do relatório de auditoria das duas revisões."""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigos"))
import dados_rs as D  # noqa: E402
import fonte as F  # noqa: E402

TITULO = "Auditoria dos oito documentos das revisões sobre humor no handebol"
SUBTITULO = ("Quatro corpora divergentes, o que confere em cada documento, o "
             "que não confere e o que decidir antes de submeter")

_INT = len(D.INTERSECAO)
_UNIAO = len(D.DOI_RS | D.DOI_BIB)
_JACCARD = 100.0 * _INT / _UNIAO

TABELAS = {

"corpora": {
 "numero": 1,
 "titulo": ("Os quatro conjuntos de estudos de humor no handebol, com a "
            "regra que define cada um"),
 "cabecalho": ["Conjunto", "n", "Anos", "Como o conjunto é formado",
               "Base de partida"],
 "linhas": [[nome, str(n), anos, regra, base]
            for nome, n, anos, regra, base in D.CORPORA],
 "nota": ("Nota: os quatro números descrevem a mesma literatura e não "
          "coincidem. A diferença entre 32 e 60 tem explicação conhecida: a "
          f"cópia do acervo neste repositório tem {D.N_BIBLIOTECA} artigos e "
          f"é de 27 de agosto, ao passo que a mapping review declara "
          f"{D.MAPPING['acervo']} artigos em 11 de setembro. O acervo "
          "quintuplicou no intervalo, e a contagem de humor acompanhou. Isso "
          "não é erro, é versão, mas exige que todo documento declare a data "
          "e o tamanho do acervo que usou."),
},

"sobreposicao": {
 "numero": 2,
 "titulo": ("Sobreposição entre a revisão sistemática e a marcação de humor "
            "da biblioteca, por DOI"),
 "cabecalho": ["Conjunto", "Estudos", "Com DOI", "Em comum",
               "Exclusivos do conjunto"],
 "linhas": [
  ["Revisão sistemática", str(len(D.ESTUDOS)), str(len(D.DOI_RS)),
   str(_INT), str(len(D.SO_RS))],
  ["Biblioteca, subvariável Humor", str(len(D.HUMOR_BIB)),
   str(len(D.DOI_BIB)), str(_INT), str(len(D.SO_BIB))],
  ["**União**", str(_UNIAO), str(_UNIAO), str(_INT),
   str(len(D.SO_RS) + len(D.SO_BIB))],
 ],
 "nota": ("Nota: a comparação é feita por DOI normalizado e ignora os três "
          "estudos da revisão sem DOI. O índice de Jaccard, que é a razão "
          f"entre a interseção e a união, vale {F.br(_JACCARD, 1)}%. Em "
          "outras palavras, os dois conjuntos que deveriam descrever a mesma "
          "literatura concordam em pouco mais de um terço dos estudos. Parte "
          "da diferença é de versão do acervo; parte é de critério, e essa "
          "parte precisa ser resolvida."),
},

"so_rs": {
 "numero": 3,
 "titulo": ("Estudos que a revisão sistemática inclui e que a marcação de "
            "humor da biblioteca não tem"),
 "cabecalho": ["Id", "Ano", "Estudo", "Instrumento", "Papel do humor"],
 "linhas": [[e["id"], str(e["ano"]), e["titulo"][:88],
             ", ".join(e.get("instrumento_familia") or ["não informado"]),
             e.get("papel_humor") or "não informado"]
            for e in sorted(D.SO_RS, key=lambda x: x["ano"])],
 "nota": ("Nota: onze estudos. A leitura de cada linha decide se a busca "
          "própria da revisão foi mais sensível que a marcação do acervo, "
          "caso em que a marcação precisa ser corrigida, ou se a revisão "
          "incluiu estudo que não mede humor por instrumento, caso em que a "
          "inclusão precisa ser revista. Os dois casos aparecem na lista."),
},

"so_bib": {
 "numero": 4,
 "titulo": ("Estudos marcados como humor na biblioteca e ausentes da revisão "
            "sistemática"),
 "cabecalho": ["Ano", "Estudo", "Motivo provável da ausência"],
 "linhas": [[str(a["ano"]), (a["titulo"] or "")[:96],
             ("Fora do critério: população de árbitros"
              if "referee" in (a["titulo"] or "").lower()
              else "Fora do critério: revisão de literatura"
              if "review" in (a["titulo"] or "").lower()
              else "A conferir")]
            for a in sorted(D.SO_BIB, key=lambda x: x["ano"])],
 "nota": ("Nota: treze estudos. Ao menos três sairiam pelos próprios "
          "critérios da revisão sistemática, dois por população de árbitros, "
          "que é a exclusão E1, e um por ser revisão de literatura, que é a "
          "exclusão E3. Os demais precisam de conferência: se medem humor "
          "por instrumento em jogadores, a busca da revisão os perdeu, e a "
          "estratégia precisa ser ampliada antes da submissão."),
},

"aritmetica": {
 "numero": 5,
 "titulo": ("Conferência aritmética dos números declarados em cada "
            "documento"),
 "cabecalho": ["Documento", "Afirmação", "Valor declarado", "Valor conferido",
               "Situação"],
 "linhas": [
  ["Revisão sistemática", "Fluxo PRISMA, registros triados", "85",
   f"{D.FLUXO['unicos_busca']} da busca mais "
   f"{D.FLUXO['outras_fontes']} de outras fontes, menos "
   f"{D.FLUXO['duplicatas_relato']} relato duplicado", "Confere"],
  ["Revisão sistemática", "Estudos incluídos", "30",
   f"{D.FLUXO['triados']} menos {D.FLUXO['excluidos_triagem']} da triagem, "
   f"{D.FLUXO['relatos_nao_recuperados']} não recuperados e "
   f"{D.FLUXO['excluidos_texto_completo']} do texto completo", "Confere"],
  ["Revisão sistemática", "Soma dos k do GRADE", "30", str(D.K_GRADE),
   "Confere"],
  ["Revisão sistemática", "Participantes somados", "2243",
   f"{D.N_GRADE} no GRADE e {D.N_SOMADO} na soma dos estudos",
   f"**Diverge em {D.N_SOMADO - D.N_GRADE}**"],
  ["Revisão de escopo", "Associação significativa entre instrumento e "
   "abordagem",
   f"χ² = {F.br(D.ESCOPO['qui2'], 2)}; p = {F.br(D.ESCOPO['qui2_p'], 3)}",
   "p acima de 0,05 e célula esperada abaixo de 5 nos quatro cruzamentos",
   "**Não confere**"],
  ["Revisão de escopo e bibliometria", "Ensaios randomizados entre os 60",
   f"{D.ESCOPO['randomizados_artigo']} no artigo e "
   f"{D.ESCOPO['randomizados_bibliometria']} na bibliometria",
   "Os dois documentos descrevem o mesmo conjunto", "**Diverge**"],
  ["Revisão de escopo e bibliometria", "Estudos com humor isolado",
   f"{D.ESCOPO['isolados']} no texto e "
   f"{D.ESCOPO['cluster_isolado']} na tabela de agrupamento",
   "Os dois valores estão no mesmo par de documentos",
   "**Diverge em 1**"],
  ["Bibliometria", "Citações totais do conjunto",
   f"{D.ESCOPO['citacoes_totais']} para {D.ESCOPO['estudos']} estudos",
   f"A média de 8,41 vezes {D.ESCOPO['n_com_citacao']} estudos com dado de "
   f"citação dá {D.ESCOPO['citacoes_totais']}",
   "**Denominador trocado**"],
  ["Revisão de escopo", "Primeiro registro do conjunto",
   str(D.ESCOPO["ano_inicial_declarado"]),
   f"A cópia da biblioteca não tem registro de humor antes de "
   f"{D.ANOS_BIB[0]}", "**A conferir**"],
  ["Mapping review", "Fluxo de triagem",
   f"{D.MAPPING['identificados']} identificados",
   f"{D.MAPPING['distintos']} distintos, {D.MAPPING['triados']} triados, "
   f"{D.MAPPING['inclusao']} de provável inclusão", "Confere"],
 ],
 "nota": ("Nota: cada valor conferido foi recalculado dos arquivos de origem "
          "por scripts/auditoria_rs/dados_rs.py. As linhas marcadas em "
          "negrito exigem decisão antes de submeter. Nenhuma delas invalida "
          "as revisões; todas alteram números que aparecem no resumo ou nos "
          "resultados."),
},

"registro": {
 "numero": 6,
 "titulo": "Qualidade do registro dos 30 estudos da revisão sistemática",
 "cabecalho": ["Item", "Valor", "Observação"],
 "linhas": [
  ["Estudos sem DOI", f"{len(D.SEM_DOI)} de {len(D.ESTUDOS)}",
   ", ".join(D.SEM_DOI) + ": impede a checagem por identificador"],
  ["Preprints", f"{len(D.PREPRINTS)} de {len(D.ESTUDOS)}",
   ", ".join(D.PREPRINTS) + ": entra na síntese sem revisão por pares"],
  ["Relatos não recuperados",
   f"{D.FLUXO['relatos_nao_recuperados']} de {D.FLUXO['relatos_buscados']} "
   "buscados",
   "28% do que foi procurado; é a limitação mais séria da revisão"],
  ["País não informado",
   f"{sum(1 for e in D.ESTUDOS if e.get('pais') == 'Não informado')} de "
   f"{len(D.ESTUDOS)}", "O resumo declara 14 países sobre 24 estudos"],
  ["Nível competitivo não informado",
   f"{sum(1 for e in D.ESTUDOS if e.get('nivel') == 'Não informado')} de "
   f"{len(D.ESTUDOS)}", "Limita a leitura por nível de prática"],
  ["Só humor global, sem as seis dimensões",
   f"{sum(1 for e in D.ESTUDOS if 'Humor global' in (e.get('dimensoes') or []))} "
   f"de {len(D.ESTUDOS)}",
   "É a razão pela qual a metanálise fica restrita a três ensaios"],
  ["Revisor 2 e revisor 3", "Assistidos por inteligência artificial",
   "Declarado no método; os índices de concordância são provisórios"],
 ],
 "nota": ("Nota: os itens vêm do próprio arquivo da revisão. O uso de "
          "inteligência artificial na triagem está declarado, o que é "
          "correto, e a confirmação humana pendente é a condição para que os "
          "índices deixem de ser provisórios."),
},
}


BLOCOS = [

("h1", "1 O QUE FOI LIDO E A RESPOSTA CURTA"),
("p0", "Foram lidos oito arquivos: dois painéis em HTML, com os dados "
       "estruturados embutidos, dois manuscritos da revisão sistemática, em "
       "português e em inglês, a versão em Word do manuscrito em inglês, e "
       "três documentos sobre o mesmo tema em formato de revisão de escopo, "
       "bibliometria e mineração analítica. Os painéis foram abertos pelo "
       "objeto de dados que carregam, e não pelo texto renderizado, de modo "
       "que todos os números desta auditoria vêm da fonte e não da leitura "
       "de tela."),
("p", "A resposta curta tem duas partes. A primeira é que a revisão "
      "sistemática é internamente sólida: o fluxo PRISMA fecha, a soma dos "
      "estudos por desfecho do GRADE fecha, a metanálise exploratória está "
      "corretamente rotulada como exploratória, e as limitações estão "
      "declaradas com franqueza pouco comum, inclusive o uso de inteligência "
      "artificial na triagem. A segunda é que existem quatro contagens "
      "diferentes da literatura de humor no handebol nos oito "
      "documentos, e que dois deles reivindicam, cada um a seu modo, ser a "
      "primeira síntese do tema. Essa é a questão a decidir, e ela é "
      "editorial antes de ser estatística."),

("h1", "2 QUATRO CORPORA PARA A MESMA PERGUNTA"),
("tab", "corpora"),
("p", "A diferença entre 32 e 60 tem explicação e não é erro. A cópia do "
      f"acervo neste repositório é de 27 de agosto e tem {D.N_BIBLIOTECA} "
      "artigos; a mapping review declara "
      f"{D.MAPPING['acervo']} artigos em 11 de setembro. O acervo cresceu "
      "cerca de cinco vezes em duas semanas, e a marcação de humor "
      "acompanhou. O que a diferença exige é procedimento: todo documento "
      "precisa declarar a data e o tamanho do acervo sobre o qual foi "
      "construído, sob pena de dois textos do mesmo grupo apresentarem "
      "números incompatíveis sem explicação visível ao leitor."),
("p", "A diferença entre a revisão sistemática e a marcação de humor da "
      "biblioteca é de outra natureza, e é a que preocupa."),
("tab", "sobreposicao"),
("p", f"Os dois conjuntos compartilham {_INT} estudos e somam {_UNIAO} "
      f"distintos: o índice de Jaccard é de {F.br(_JACCARD, 1)}%. Uma busca "
      "dedicada e uma marcação de acervo sobre a mesma pergunta deveriam "
      "convergir muito mais que isso. As duas listas de estudos exclusivos "
      "mostram por quê."),
("tab", "so_rs"),
("tab", "so_bib"),
("p", "A leitura conjunta das duas tabelas dá o diagnóstico. A marcação da "
      "biblioteca é mais larga que o critério da revisão: ela inclui "
      "árbitros e ao menos uma revisão de literatura, que sairiam pelas "
      "exclusões E1 e E3 do próprio protocolo. A busca da revisão, por sua "
      "vez, encontrou onze estudos que a marcação não tem, o que indica que "
      "a marcação também é incompleta. Os dois instrumentos precisam ser "
      "reconciliados, e o mais econômico é usar a lista da revisão "
      "sistemática como referência e corrigir a marcação do acervo contra "
      "ela, e não o inverso."),

("h1", "3 O QUE CONFERE E O QUE NÃO CONFERE"),
("tab", "aritmetica"),
("p", "Quatro pontos merecem comentário. O primeiro é a diferença de "
      f"{D.N_SOMADO - D.N_GRADE} participantes entre a soma dos estudos e o "
      "total do GRADE. É pequena e provavelmente decorre de um estudo "
      "contado em dois desfechos ou de um n corrigido depois da montagem do "
      "GRADE, mas o resumo publica 2243 e a soma dá "
      f"{D.N_SOMADO}, e um revisor que somar vai encontrar a diferença."),
("p", "O segundo é o único que compromete uma afirmação. A revisão de "
      "escopo diz que a única associação estatisticamente significativa foi "
      f"a de instrumento por abordagem, com p de "
      f"{F.br(D.ESCOPO['qui2_p'], 3)}. Esse valor está acima de 0,05 e a "
      "afirmação de significância não se sustenta. Some-se que os quatro "
      "cruzamentos da tabela têm célula esperada abaixo de cinco, o que "
      "invalida a aproximação do qui-quadrado em todos eles. A correção é "
      "simples: trocar a afirmação por uma descrição da magnitude, que é o "
      "V de Cramér, e declarar que nenhum teste atende ao pressuposto."),
("p", "O terceiro é a contradição entre os dois documentos que descrevem o "
      "mesmo conjunto de 60 estudos: a bibliometria conta "
      f"{D.ESCOPO['randomizados_bibliometria']} ensaio randomizado e o "
      f"artigo conta {D.ESCOPO['randomizados_artigo']}. A tabela de tipos de "
      "estudo da bibliometria também mistura dimensões, porque estudo "
      "original empírico e artigo de periódico não são categorias "
      "excludentes. O quarto é o denominador das citações: a média de 8,41 "
      f"corresponde aos {D.ESCOPO['n_com_citacao']} estudos com dado de "
      f"citação, e não aos {D.ESCOPO['estudos']} do conjunto, mas a tabela "
      "apresenta o total como se fosse do conjunto inteiro."),
("p", "Há ainda uma frase que se contradiz sozinha e vale corrigir por ser "
      "de leitura imediata. A revisão de escopo abre um parágrafo com a "
      "afirmação de que o humor foi investigado majoritariamente de forma "
      f"combinada e, na mesma frase, informa que {D.ESCOPO['isolados']} "
      f"estudos, ou {F.br(D.ESCOPO['isolados_pct'], 1)}%, o tratam "
      "isoladamente. Os números dizem o contrário da abertura. O mesmo "
      "acontece na mineração analítica, cujo tópico conclui que o humor se "
      "comporta como marcador integrado a partir de "
      f"{F.br(D.ESCOPO['combinados_pct'], 1)}% de estudos combinados."),

("h1", "4 QUALIDADE DO REGISTRO DA REVISÃO SISTEMÁTICA"),
("tab", "registro"),
("p", "O item mais sério não é nenhum dos erros acima, e sim a taxa de "
      "recuperação. Dos "
      f"{D.FLUXO['relatos_buscados']} relatos procurados, "
      f"{D.FLUXO['relatos_nao_recuperados']} não foram recuperados, o que é "
      "28%. Uma revisão que perde mais de um quarto do que procurou tem o "
      "conjunto incluído em aberto, e a própria seção de limitações "
      "reconhece isso. Antes da submissão, vale esgotar as vias de "
      "recuperação: pedido direto aos autores, empréstimo entre "
      "bibliotecas e consulta às bases sem interface automática, que são "
      "justamente as duas de psicologia do esporte que ficaram de fora."),

("h1", "5 A DECISÃO EDITORIAL"),
("p0", "Dois dos oito documentos reivindicam primazia sobre o mesmo tema. A "
       "revisão sistemática conclui que é a primeira síntese dedicada ao "
       "humor no handebol. A revisão de escopo mapeia 60 estudos do mesmo "
       "tema, com a mesma biblioteca de origem e conclusões que se "
       "sobrepõem. Se os dois forem submetidos separadamente, o segundo a "
       "sair encontra o primeiro na literatura, e o par tem aparência de "
       "fatiamento de um único trabalho."),
("p", "Há três saídas, e a escolha entre elas é do orientador. A primeira é "
      "publicar apenas a revisão sistemática e usar a bibliometria como "
      "seção dela, o que é comum e resolve a sobreposição de uma vez. A "
      "segunda é separar por pergunta: a revisão sistemática responde como o "
      "humor responde a treino, competição e intervenção, e a revisão de "
      "escopo responde como o campo se organiza, com bibliometria, redes e "
      "agrupamento, sem repetir a síntese de efeito. A terceira é ampliar a "
      "revisão de escopo para todas as variáveis psicológicas, que é o "
      "recorte da mapping review, e deixar o humor apenas para a revisão "
      "sistemática. A terceira é a que menos desperdiça trabalho já feito, "
      "porque a mapping review já tem "
      f"{D.MAPPING['distintos']} registros distintos triados e "
      f"{D.MAPPING['inclusao']} candidatos de inclusão."),
("p", "Qualquer que seja a escolha, três providências valem para todas. "
      "Declarar em cada documento a data e o tamanho do acervo usado. "
      "Reconciliar a marcação de humor da biblioteca contra a lista da "
      "revisão sistemática. E registrar no PROSPERO antes da extração "
      "definitiva, o que o próprio protocolo recomenda e ainda está "
      "pendente."),

("h1", "6 O QUE CORRIGIR, POR PRIORIDADE"),
("lista", [
 "Corrigir a afirmação de significância do qui-quadrado na revisão de "
 "escopo, e declarar que os quatro cruzamentos têm célula esperada abaixo "
 "de cinco.",
 "Reconciliar a contagem de ensaios randomizados entre a revisão de escopo "
 "e a bibliometria, que hoje diverge, e refazer a tabela de tipos de estudo "
 "com categorias excludentes.",
 f"Explicar a diferença de {D.N_SOMADO - D.N_GRADE} participantes entre a "
 "soma dos estudos e o total do GRADE, e publicar um só valor.",
 "Corrigir o denominador das citações na bibliometria, que é o número de "
 f"estudos com dado de citação e não os {D.ESCOPO['estudos']} do conjunto.",
 "Reescrever as duas frases que se contradizem sobre humor isolado e "
 "combinado.",
 f"Conferir o primeiro ano do conjunto, declarado como "
 f"{D.ESCOPO['ano_inicial_declarado']}, que a cópia da biblioteca não "
 "reproduz.",
 "Esgotar a recuperação dos treze relatos pendentes antes de fechar o "
 "conjunto incluído.",
 "Decidir o recorte entre a revisão sistemática e a revisão de escopo, "
 "antes de submeter qualquer uma das duas.",
 "Fazer a confirmação humana da triagem, que hoje é assistida por "
 "inteligência artificial no revisor 2 e no terceiro revisor.",
 "Registrar o protocolo no PROSPERO.",
]),
]
