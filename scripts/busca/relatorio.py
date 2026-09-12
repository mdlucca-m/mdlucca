#!/usr/bin/env python3
"""Relatório da busca complementar de 12 de setembro de 2026.

Documenta as bases acionadas, as que responderam, as que a política de saída
da organização bloqueou, o resultado da reexecução da string na única base
disponível e a adjudicação dos treze relatórios que a revisão sistemática
havia deixado como não recuperados.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "comum"))
import abnt  # noqa: E402

FT = "Fonte: elaborada pelos autores (2026)."

BASES = {
    "numero": 1,
    "titulo": "Bases e serviços acionados em 12 de setembro de 2026, via de "
              "acesso e desfecho da tentativa",
    "cabecalho": ["Base ou serviço", "Via", "Desfecho", "Registros"],
    "linhas": [
        ["PubMed", "interface programática", "respondeu", "16"],
        ["Consensus", "interface programática", "respondeu", "20"],
        ["Busca na web", "interface programática", "respondeu", "4 consultas"],
        ["Scite", "interface programática", "cota mensal esgotada", "0"],
        ["Scopus", "api.elsevier.com", "bloqueado pela política de saída", "0"],
        ["Web of Science", "api.clarivate.com", "bloqueado pela política de "
         "saída", "0"],
        ["OpenAlex", "api.openalex.org", "bloqueado pela política de saída",
         "0"],
        ["Crossref", "api.crossref.org", "bloqueado pela política de saída",
         "0"],
        ["Europe PMC", "www.ebi.ac.uk", "bloqueado pela política de saída",
         "0"],
        ["Semantic Scholar", "api.semanticscholar.org", "bloqueado pela "
         "política de saída", "0"],
    ],
    "larguras": [4.2, 4.0, 5.0, 2.4],
}

RECALL = {
    "numero": 2,
    "titulo": "Reexecução da string de busca no PubMed e conferência contra o "
              "registro da revisão",
    "cabecalho": ["Situação do registro recuperado", "n"],
    "linhas": [
        ["Estudos incluídos na revisão, com identificador PubMed", "11"],
        ["Relatórios já classificados como não recuperados", "2"],
        ["Registros já triados e excluídos, com motivo registrado", "3"],
        ["**Total recuperado", "16"],
        ["Registros fora do conjunto de 86 já triados", "0"],
    ],
    "larguras": [12.0, 2.0],
}

ADJUDICACAO = {
    "numero": 3,
    "titulo": "Adjudicação dos treze relatórios que permaneciam sem "
              "recuperação",
    "cabecalho": ["Código", "Identificação obtida", "Decisão", "Motivo"],
    "linhas": [
        ["RS041", "Erden e Emirzeoğlu (2020), 188 atletas de quatro "
         "modalidades, 34 de handebol",
         "excluído", "sem resultado separável para handebol"],
        ["RS079", "Bursik e outros (2025), 459 atletas alemães de elite, "
         "automedicação com analgésicos",
         "excluído", "sem medida de humor ou de afeto"],
        ["RS015", "Laborde e Raab (2013), indução de humor e geração de "
         "opções, amostra mista",
         "incerto", "exige texto completo para separar a subamostra"],
        ["RS002", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS006", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS007", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS011", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS012", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS024", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS026", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS042", "não localizado em nenhuma das bases que responderam",
         "não recuperado", "literatura cinzenta sem identificador"],
        ["RS037", "registro com identificador digital, texto completo não "
         "obtido", "não recuperado", "acesso restrito"],
        ["RS040", "registro com identificador digital, texto completo não "
         "obtido", "não recuperado", "acesso restrito"],
    ],
    "larguras": [1.6, 6.4, 2.4, 5.2],
}

INCORPORADAS = {
    "numero": 4,
    "titulo": "Referências verificadas nas bases e incorporadas ao Artigo 1",
    "cabecalho": ["Referência", "Contribuição ao texto", "Seção"],
    "linhas": [
        ["Zhang e outros (2014), Journal of Sports Sciences, v. 32, n. 15",
         "validade fatorial e invariância de medida em 2548 respondentes, "
         "dos quais 954 atletas", "3.5"],
        ["Hasan e Khan (2022), Heliyon, v. 8, n. 6",
         "estabilidade de reteste entre 0,71 e 0,91, condição para a leitura "
         "de sete medidas seguidas", "3.5"],
        ["Rohlfs e outros (2025), Sports, v. 13, n. 9",
         "dados conferidos no PubMed: 417 atletas, barbatana de tubarão em "
         "28,3% e razão de chances de 2,90 para lesão", "1, 5.6"],
    ],
    "larguras": [5.4, 7.4, 1.4],
}

BLOCOS = [
    ("h1", "1 OBJETIVO"),
    ("p", "Este relatório registra a execução das buscas pendentes declaradas "
          "na revisão sistemática, o desfecho de cada base acionada e a "
          "adjudicação dos treze relatórios que a revisão havia deixado sem "
          "recuperação. O registro é necessário porque parte das bases não "
          "pôde ser consultada, e a razão precisa constar do relato de "
          "método, e não ser omitida."),

    ("h1", "2 BASES ACIONADAS E O QUE FOI BLOQUEADO"),
    ("p", "Dez bases e serviços foram acionados. Três responderam, um estava "
          "com a cota mensal esgotada e seis foram recusados pela política de "
          "saída da rede desta sessão, que respondeu com código 403 à "
          "abertura do túnel de conexão. A recusa é de política, não de "
          "indisponibilidade do serviço, e por isso não foi contornada."),
    ("tab", BASES),
    ("p", "Scopus e Web of Science estão entre as bases recusadas. As duas "
          "exigiriam, além da liberação de rede, chave de acesso "
          "institucional, que esta sessão não possui. A consulta a elas "
          "permanece como tarefa a ser feita por acesso institucional "
          "direto, e o relato de método da revisão deve declarar que a "
          "reexecução nessas duas bases não foi realizada nesta rodada."),
    ("p", "A cobertura perdida é parcialmente compensada pelo Consensus, "
          "cujo índice reúne Semantic Scholar, PubMed, Scopus e repositórios "
          "de preprints. A compensação não é equivalente a uma consulta "
          "direta ao Scopus, porque não permite executar a string booleana "
          "no formato da base nem exportar o conjunto completo de "
          "resultados, e por isso não substitui a etapa pendente."),

    ("h1", "3 REEXECUÇÃO DA STRING NO PUBMED"),
    ("p", "A string de dois blocos da revisão excede o limite de operadores "
          "booleanos da interface disponível e foi partida em duas consultas "
          "complementares, uma para os termos de humor e instrumentos de "
          "humor e outra para os termos de afeto. A união das duas devolveu "
          "16 registros."),
    ("tab", RECALL),
    ("p", "O resultado é o achado mais relevante desta rodada. Nenhum dos 16 "
          "registros está fora do conjunto de 86 já triados pela revisão. Os "
          "11 estudos incluídos que possuem identificador PubMed foram todos "
          "recuperados, o que corresponde a sensibilidade de 100% da busca "
          "original em relação a essa base. Os três registros que à primeira "
          "vista pareciam novos já constavam do registro com exclusão "
          "motivada: RS061, RS051 e RS046."),
    ("p", "A conferência não se estende às demais bases. Ela sustenta a "
          "afirmação de que a busca não perdeu registro indexado no PubMed, e "
          "apenas essa."),

    ("h1", "4 BOLA DE NEVE"),
    ("p", "A bola de neve para trás continua pendente. O serviço que "
          "devolveria a lista de referências de cada estudo incluído, o "
          "Europe PMC, está entre as bases recusadas pela política de saída, "
          "e o grafo de citações do Scite, que seria a alternativa, atingiu a "
          "cota mensal de chamadas. A varredura terá de ser feita sobre o "
          "texto de cada um dos 30 incluídos, por leitura direta das listas "
          "de referências, e essa é a tarefa de maior retorno esperado entre "
          "as que permanecem abertas."),
    ("p", "A bola de neve para a frente permanece no estado em que a revisão "
          "a deixou, com 123 citações examinadas e nenhum estudo elegível "
          "acrescentado."),

    ("h1", "5 ADJUDICAÇÃO DOS RELATÓRIOS NÃO RECUPERADOS"),
    ("p", "Dos treze relatórios pendentes, dois foram resolvidos e excluídos "
          "com motivo, um permanece incerto e depende do texto completo, e "
          "dez seguem sem recuperação. Nove destes dez não têm identificador "
          "digital e correspondem a literatura cinzenta, anais e periódicos "
          "sem indexação nas bases que responderam."),
    ("tab", ADJUDICACAO),
    ("p", "O efeito sobre a revisão é pequeno e deve ser declarado. Nenhum "
          "dos dois relatórios resolvidos entra no corpus, de modo que o "
          "número de estudos incluídos permanece em 30. Os dez sem "
          "recuperação continuam a compor o item de relatórios não obtidos do "
          "fluxo, e a limitação correspondente já está declarada."),

    ("h1", "6 CANDIDATOS NOVOS EXAMINADOS"),
    ("p", "As buscas no Consensus e na web devolveram quatro registros que "
          "não constavam do conjunto de 86. Nenhum é elegível. Dois tratam de "
          "amostras multiesportivas sem resultado separável para handebol, um "
          "mede motivação e ansiedade competitiva sem instrumento de humor, e "
          "o quarto é uma revisão de humor em futebol. A ausência de "
          "candidato elegível, somada à sensibilidade de 100% no PubMed, é "
          "sinal convergente de que o corpus de 30 estudos está estável."),

    ("h1", "7 O QUE FOI INCORPORADO AO ARTIGO 1"),
    ("p", "Três referências foram conferidas nas bases que responderam e "
          "usadas no manuscrito. As duas primeiras são novas e sustentam a "
          "seção de instrumento; a terceira já era citada e teve os dados "
          "bibliográficos e os valores conferidos contra o registro do "
          "PubMed."),
    ("tab", INCORPORADAS),
    ("p", "A conferência da estabilidade de reteste responde a uma lacuna do "
          "método: o delineamento aplica o mesmo instrumento em sete dias "
          "seguidos, e até aqui o texto não apresentava evidência de que a "
          "variação observada fosse de estado e não de erro de medida. A "
          "ressalva conhecida sobre a distinção entre tensão e depressão foi "
          "verificada na própria amostra e não se confirma, com correlação "
          "de 0,18 entre as duas subescalas."),

    ("h1", "8 O QUE PERMANECE PENDENTE"),
    ("lista", [
        "Reexecutar a string no Scopus e na Web of Science por acesso "
        "institucional direto, fora desta rede.",
        "Reexecutar a string no OpenAlex, tarefa que a revisão já declarava "
        "pendente por limite de requisições e que agora acumula o bloqueio "
        "de rede.",
        "Fazer a bola de neve para trás por leitura das listas de "
        "referências dos 30 estudos incluídos.",
        "Obter o texto completo de RS015 para decidir entre inclusão e "
        "exclusão.",
        "Registrar no relato de método da revisão, de forma explícita, que "
        "a reexecução em Scopus, Web of Science e OpenAlex não foi feita, e "
        "por qual razão.",
    ]),
]


def main() -> None:
    saida = Path("data/BUSCA_COMPLEMENTAR_RS.docx")
    saida.parent.mkdir(parents=True, exist_ok=True)
    conta = abnt.montar(
        BLOCOS, saida,
        titulo="Busca complementar da revisão sistemática de humor em "
               "handebol: bases acionadas, cobertura obtida e pendências",
        subtitulo="Relatório de execução de 12 de setembro de 2026",
        fonte_tabela=FT, fonte_figura=FT)
    print(f"gerado: {saida}")
    for k, v in conta.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
