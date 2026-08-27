"""Seções cujo texto é gerado dos dados, para que prosa e tabela não possam
divergir — a origem dos achados B1, B2 e G3.
"""
from __future__ import annotations

import sqlite3

from curadoria.elegibilidade import JANELA, fluxo_prisma
from curadoria.extracao import diagnostico
from curadoria.referencias import auditar


def _n(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def resultados(con: sqlite3.Connection, decisoes: list, linhas_extracao: list) -> list[tuple[str, str]]:
    """Devolve [(estilo, texto)] para a seção 4."""
    f = fluxo_prisma(decisoes)
    inc = [d for d in decisoes if d.incluido]
    m = f["por_motivo"]
    ev = f["por_evidencia"]
    total_base = con.execute("SELECT COUNT(*) FROM artigo").fetchone()[0]
    aud = auditar(con, {d.id for d in inc})
    diag = diagnostico(linhas_extracao)

    familias = {}
    for d in inc:
        for fam in d.familias:
            familias[fam] = familias.get(fam, 0) + 1
    top = sorted(familias.items(), key=lambda x: -x[1])[:3]

    anos = {}
    for (i, ano) in con.execute("SELECT id, ano FROM artigo"):
        if any(d.id == i for d in inc) and (ano or "").isdigit():
            anos[int(ano)] = anos.get(int(ano), 0) + 1
    recentes = sum(v for k, v in anos.items() if k >= 2016)
    antigos = sum(v for k, v in anos.items() if k < 2016)

    return [
        ("Título 1", "4 RESULTADOS"),
        ("Corpo", "Os resultados desta seção referem-se aos registros que "
                  "satisfazem os critérios dos Quadros 1 e 2 aplicados à "
                  "biblioteca curada. Toda contagem declara a base sobre a qual "
                  "recai, e toda tabela é gerada diretamente dos dados, de modo "
                  "que texto e tabela não possam divergir."),

        ("Título 2", "4.1 Triagem e definição do corpus"),
        ("Corpo", f"A biblioteca curada reúne {_n(total_base)} registros. A "
                  f"aplicação dos critérios de elegibilidade excluiu "
                  f"{_n(f['excluidos'])} e reteve {_n(f['incluidos'])}, que "
                  "constituem o corpus analisado. Cada exclusão recebeu um único "
                  "motivo, o primeiro aplicável na ordem do Quadro 2, conforme o "
                  "diagrama de fluxo exige."),
        ("Corpo", f"O motivo mais frequente foi a ausência de aferição de "
                  f"variável psicológica ({_n(m['não mede variável psicológica'])} "
                  "registros): a biblioteca cobre cinco famílias de variável, das "
                  "quais a psicológica é uma, e a maioria dos registros afere "
                  "apenas desfechos físicos, fisiológicos ou biomecânicos. "
                  f"Seguiram-se {m['fora da janela temporal']} registros fora da "
                  f"janela {JANELA[0]}–{JANELA[1]}, "
                  f"{m['população não é de handebol']} sem menção ao handebol em "
                  "título, resumo ou palavras-chave, "
                  f"{m['delineamento inelegível']} com delineamento excluído pelo "
                  f"Quadro 2 e {m['fora de treinamento ou competição']} em "
                  "contexto exclusivamente clínico, escolar ou laboratorial."),
        ("Corpo", "Registra-se uma distinção que a leitura dos resultados exige. "
                  f"Dos {_n(f['incluidos'])} registros elegíveis, "
                  f"{ev['instrumento nomeado']} nomeiam um instrumento "
                  "psicométrico já no título, no resumo ou nas palavras-chave, e "
                  f"{ev['construto no resumo']} declaram o construto sem nomear o "
                  "instrumento. Nestes últimos a elegibilidade quanto ao eixo "
                  "Conceito permanece a confirmar contra o texto completo, e as "
                  "tabelas assinalam essa condição em vez de dissolvê-la na "
                  "contagem."),
        ("Tabela", "3"),

        ("Título 2", "4.2 Caracterização do corpus"),
        ("Corpo", f"A produção concentra-se na década mais recente: "
                  f"{recentes} dos {_n(f['incluidos'])} registros elegíveis foram "
                  f"publicados entre 2016 e {JANELA[1]}, contra {antigos} entre "
                  f"{JANELA[0]} e 2015. As duas contagens somam o total do "
                  "corpus, sem resto."),
        ("Corpo", "A distribuição por família de construto aparece na Tabela 4. "
                  "As três famílias mais frequentes são "
                  + ", ".join(f"{k} ({v} registros)" for k, v in top)
                  + ". Um registro pode figurar em mais de uma família, de modo "
                    "que a soma das linhas excede a base declarada e os "
                    "percentuais não somam cem."),
        ("Tabela", "4"),
        ("Corpo", "A Tabela 5 lista os instrumentos psicométricos efetivamente "
                  "nomeados. Ela substitui a versão anterior, que agregava o "
                  "campo de instrumentos da biblioteca e por isso trazia testes "
                  "de agilidade, saltos verticais, coleta salivar e "
                  "posicionamento por satélite sob o rótulo de instrumentos "
                  "psicométricos. Escalas de percepção de esforço não constam: "
                  "são medidas psicofísicas de intensidade percebida, não "
                  "psicometria de construto, e tratá-las como esta última é o "
                  "que faz um estudo de carga de treino parecer um estudo de "
                  "motivação."),
        ("Tabela", "5"),
        ("Tabela", "6"),

        ("Título 2", "4.3 Práticas de relato"),
        ("Corpo", "A Tabela 7 reporta as práticas de relato detectáveis nos "
                  "resumos e no campo de análise estatística dos registros "
                  "elegíveis. Os valores são um piso, e não uma estimativa da "
                  "prevalência: o resumo omite rotineiramente a estatística, de "
                  "modo que a não detecção indica ausência de relato recuperável "
                  "nesses campos, não ausência da prática no estudo. A versão "
                  "desta tabela sobre os textos completos depende de nova "
                  "mineração e a substitui quando disponível."),
        ("Tabela", "7"),

        ("Título 2", "4.4 Integridade dos metadados"),
        ("Corpo", f"A auditoria dos identificadores dos {_n(f['incluidos'])} "
                  f"registros elegíveis encontrou {aud['com_problema']} com "
                  "alguma pendência: "
                  + "; ".join(f"{v} {k}" for k, v in aud["por_tipo"].items())
                  + ". A pendência mais grave é a divergência entre o ano do "
                    "registro e o ano embutido no identificador digital, que "
                    "indica identificador apontando para outro artigo. Como as "
                    "referências são geradas desses campos, cada divergência "
                    "produziria uma referência incorreta, e por isso a geração "
                    "de referência fica bloqueada para os registros afetados até "
                    "a conferência contra o Crossref."),
        ("Corpo", f"A tabela de extração do Apêndice B assinala "
                  f"{diag['com_alerta']} das {diag['linhas']} linhas com ao menos "
                  "um alerta de conferência: "
                  f"{diag['sem_delineamento']} sem delineamento declarado no "
                  f"resumo, {diag['n_a_conferir']} com tamanho amostral "
                  "coincidente com um ano-calendário e "
                  f"{diag['idade_incoerente']} com idade média incompatível com o "
                  "nível competitivo declarado. Os alertas são deliberados: um "
                  "campo duvidoso sinalizado é conferível, ao passo que um campo "
                  "duvidoso apresentado como valor não é."),
    ]


def discussao(con: sqlite3.Connection, decisoes: list) -> list[tuple[str, str]]:
    f = fluxo_prisma(decisoes)
    ev = f["por_evidencia"]
    return [
        ("Título 1", "5 DISCUSSÃO"),
        ("Corpo", "Três elementos decorrem da estrutura da literatura e não da "
                  "composição do corpus, e por isso permanecem válidos "
                  "independentemente do que a conferência dos textos completos "
                  "vier a alterar."),
        ("Corpo", "O primeiro refere-se à recuperabilidade. A inexistência de "
                  "descritor controlado para handebol impõe dependência integral "
                  "de termos livres no bloco de população. Estudos que não "
                  "empreguem o termo no título, no resumo ou nas palavras-chave "
                  "permanecem irrecuperáveis por busca sistemática — limitação "
                  "estrutural da indexação que qualquer revisão na modalidade "
                  "compartilha e que raramente é declarada."),
        ("Corpo", "O segundo diz respeito à cobertura. A concentração de parcela "
                  "relevante da produção em periódicos ibero-americanos e do "
                  "leste europeu indica que revisões apoiadas em fonte única "
                  "subestimam sistematicamente o campo. O acréscimo obtido pela "
                  "interrogação de bases regionais confirma essa leitura e "
                  "recomenda cautela na interpretação de mapeamentos "
                  "anglófonos."),
        ("Corpo", "O terceiro concerne ao que se pode afirmar a partir de "
                  f"resumos. Em {ev['construto no resumo']} dos "
                  f"{f['incluidos']} registros elegíveis o construto é declarado "
                  "sem que o instrumento seja nomeado, e as práticas de relato "
                  "estatístico aparecem em minoria dos resumos. Disso não se "
                  "conclui que os estudos não relatem nem meçam: conclui-se que "
                  "o resumo não é substrato suficiente para o objetivo "
                  "específico (b), e que a correspondência entre instrumento e "
                  "construto declarado — que a revisão se propõe a verificar — "
                  "só pode ser estabelecida sobre o texto completo. É a razão "
                  "pela qual a etapa de elegibilidade por texto completo não "
                  "pode ser abreviada."),
        ("Corpo", "[A PREENCHER: Discussão dos achados] Interpretar os estudos "
                  "após a conferência dos textos completos: construtos com maior "
                  "concentração de evidência, construtos sub-representados, "
                  "coerência entre instrumento e construto declarado, e "
                  "comparação com revisões conduzidas em outras modalidades "
                  "coletivas. Depende de: conclusão da triagem em duplicata."),
    ]


def conclusao(decisoes: list) -> list[tuple[str, str]]:
    f = fluxo_prisma(decisoes)
    return [
        ("Título 1", "7 CONCLUSÃO"),
        ("Corpo", "A pergunta de revisão indaga quais variáveis psicológicas são "
                  "investigadas em atletas e praticantes de handebol nos "
                  "contextos de treinamento e de competição. O mapeamento de "
                  f"{f['incluidos']} registros elegíveis permite três respostas "
                  "parciais, cuja consolidação depende da conferência dos textos "
                  "completos."),
        ("Corpo", "Primeira: a produção concentra-se em ansiedade e estresse, "
                  "motivação e cognição, ao passo que emoção, personalidade e "
                  "coesão de grupo permanecem sub-representadas, apesar de a "
                  "literatura de esportes coletivos situar parcela relevante da "
                  "variância psicológica no nível do grupo. Segunda: os "
                  "instrumentos efetivamente nomeados concentram-se em poucas "
                  "escalas, o que sugere que a diversidade de construtos "
                  "declarados não corresponde a uma diversidade equivalente de "
                  "aferição. Terceira: a fração do corpus em que o construto é "
                  "declarado sem que o instrumento seja nomeado é grande o "
                  "bastante para que o mapa produzido a partir de resumos seja "
                  "tratado como delimitação do campo, e não como sua descrição."),
        ("Corpo", "[A PREENCHER: Conclusão definitiva] Redigir após a síntese "
                  "dos estudos incluídos, respondendo à pergunta de revisão e "
                  "explicitando as lacunas que orientam investigações futuras. "
                  "Depende de: conclusão da triagem e da extração."),
    ]


def limitacoes(decisoes: list, con: sqlite3.Connection) -> list[tuple[str, str]]:
    f = fluxo_prisma(decisoes)
    ev = f["por_evidencia"]
    itens = [
        "A ausência de descritor controlado para handebol restringe a "
        "recuperação da população a termos livres.",
        "Bases que exigem credencial institucional específica, entre elas o "
        "SPORTDiscus, não foram interrogadas, de modo que a cobertura "
        "permanece incompleta.",
        "A literatura cinza foi contemplada apenas parcialmente, por meio de "
        "preprints indexados; teses e anais não foram varridos sistematicamente.",
        f"Em {ev['construto no resumo']} dos {f['incluidos']} registros "
        "elegíveis o instrumento psicométrico não é nomeado no resumo, de modo "
        "que a Tabela 5 é um piso e não uma estimativa de prevalência de uso.",
        "As práticas de relato da Tabela 7 foram aferidas sobre resumos, que "
        "omitem rotineiramente a estatística; os percentuais subestimam a "
        "prática real e não devem ser lidos como sua medida.",
        "A extração automatizada de campos foi calibrada em inglês e português, "
        "o que reduz a sensibilidade em textos redigidos em outros idiomas, e "
        "os campos assim extraídos trazem os alertas registrados na seção 4.4.",
    ]
    return [("Título 1", "6 LIMITAÇÕES")] + [("Marcador", i) for i in itens]
