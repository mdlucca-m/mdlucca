"""Correções de texto aplicadas ao manuscrito original.

Cada entrada é casada pelo início do parágrafo no documento de origem. O que
não estiver aqui é reaproveitado sem alteração — a revisão apontou problemas em
seções específicas, não na prosa inteira, e reescrever o que está correto só
introduziria risco novo.

    SUBSTITUIR   troca o parágrafo inteiro
    REMOVER      suprime o parágrafo
    INSERIR_APOS acrescenta parágrafos depois do casado
"""
from __future__ import annotations

# ── M1 · diretriz de relato ─────────────────────────────────────────────────
SUBSTITUIR: dict[str, str] = {
    "Revisão sistemática da literatura, conduzida e relatada conforme a diretriz PRISMA 2020":
        "Revisão de escopo, conduzida e relatada conforme a diretriz PRISMA "
        "Extension for Scoping Reviews (PRISMA-ScR). A escolha decorre do "
        "objetivo declarado: mapear a extensão, a variedade e a distribuição da "
        "produção sobre variáveis psicológicas no handebol, e não estimar o "
        "efeito de uma intervenção determinada. É esse objetivo que o acrônimo "
        "PCC estrutura, e é a PRISMA-ScR, não a PRISMA 2020, a diretriz que "
        "corresponde a ele. A revisão mantém, ainda assim, os procedimentos de "
        "rigor que a PRISMA 2020 exige e que a PRISMA-ScR não torna "
        "obrigatórios: triagem em duplicata com aferição de concordância, "
        "registro do motivo de cada exclusão e extração conferida por segundo "
        "revisor.",

    "[A PREENCHER: Registro no PROSPERO]":
        "[A PREENCHER: Registro do protocolo] O PROSPERO não aceita revisões de "
        "escopo, de modo que o registro deve ser feito no Open Science "
        "Framework, plataforma recomendada pelo JBI para esse desenho. Informar "
        "o identificador e a data de submissão. O registro prospectivo deve "
        "anteceder o início da triagem; registro retrospectivo precisa ser "
        "declarado como tal. Depende de: submissão do protocolo ao OSF.",

    "A avaliação do risco de viés é conduzida em duplicata":
        "A PRISMA-ScR não exige avaliação de risco de viés, uma vez que a "
        "revisão de escopo mapeia a produção em vez de sintetizar efeitos, e a "
        "apreciação da certeza da evidência pressupõe uma estimativa a apreciar. "
        "Registra-se, contudo, a caracterização metodológica dos estudos "
        "incluídos — delineamento, tamanho e composição da amostra, práticas de "
        "relato estatístico —, que sustenta o objetivo específico (e) e permite "
        "ao leitor julgar a solidez do conjunto sem que se afirme um nível de "
        "certeza que este desenho não autoriza.",

    "[A PREENCHER: Ferramentas de risco de viés]":
        "Caso a triagem revele um subconjunto homogêneo que comporte síntese "
        "quantitativa, a avaliação de risco de viés desse subconjunto passa a "
        "ser necessária, com ferramenta escolhida conforme o delineamento "
        "predominante, e a revisão desse recorte passa a reportar-se pela "
        "PRISMA 2020.",

    "Prevê-se heterogeneidade acentuada quanto a construtos":
        "Prevê-se heterogeneidade acentuada quanto a construtos, instrumentos e "
        "delineamentos, o que desaconselha agregação estatística "
        "indiscriminada e é, em si, um achado do mapeamento. A síntese é "
        "narrativa e estruturada por família de construto, acompanhada de "
        "tabelas de caracterização e de matrizes de cruzamento entre construto, "
        "instrumento e contexto de aferição. A realização de metanálise fica "
        "condicionada à identificação de um subconjunto homogêneo, e sua "
        "ausência não constitui limitação do desenho adotado.",

    # ── G1 · fontes de informação ───────────────────────────────────────────
    "Duas ausências devem ser declaradas.":
        "Três observações sobre a cobertura devem ser declaradas. A primeira: o "
        "Europe PMC indexa integralmente o MEDLINE, de modo que sua "
        "interrogação em paralelo ao PubMed produz sobreposição quase total; "
        "os dois constam separadamente na contagem de identificação porque o "
        "PRISMA a pede por base, e a deduplicação resolve a sobreposição, mas "
        "os totais por base não devem ser lidos como conjuntos independentes. A "
        "segunda: o SPORTDiscus, que indexa periódicos de psicologia do esporte "
        "não cobertos pelo MEDLINE, exige credencial institucional específica "
        "indisponível à equipe, e a cobertura permanece incompleta nessa frente. "
        "A terceira: o Google Scholar foi consultado apenas como verificação "
        "de sensibilidade da estratégia, não como fonte de identificação, uma "
        "vez que não oferece exportação estruturada nem consulta reexecutável; "
        "sua sintaxe consta do Apêndice A para permitir a reprodução dessa "
        "verificação, e nenhum registro dele integra a contagem do PRISMA.",

    # ── M5 · limiar de calibração ───────────────────────────────────────────
    "Recomenda-se calibração prévia sobre um subconjunto de registros.":
        "A calibração prévia é obrigatória e tem limiar declarado. Ambos os "
        "revisores triam os mesmos cinquenta registros, sorteados ao acaso, e a "
        "concordância é calculada. A triagem da fila completa só começa quando o "
        "coeficiente AC1 atingir 0,80 no lote de calibração; abaixo disso as "
        "divergências são discutidas, os critérios são explicitados no que se "
        "mostrarem ambíguos e novo lote de cinquenta é triado. O limiar vale "
        "para o AC1, e não para o kappa, pela razão exposta na seção 3.7: sob a "
        "distribuição desbalanceada esperada numa triagem, o kappa deprime a "
        "estimativa e não serve como critério de decisão.",
}

# Títulos de seção alterados pelas correções.
TITULOS: dict[str, str] = {
    "3.9 Risco de viés e certeza da evidência":
        "3.9 Caracterização metodológica dos estudos",
    "4 RESULTADOS PRELIMINARES": "4 RESULTADOS",
    "5 DISCUSSÃO PRELIMINAR": "5 DISCUSSÃO",
}

# ── Parágrafos suprimidos ───────────────────────────────────────────────────
# Os números de 4.1 a 4.4 e da discussão são regerados dos dados; os
# parágrafos que os afirmavam saem inteiros e dão lugar ao texto gerado.
REMOVER: tuple[str, ...] = (
    "A busca identificou 1527 registros nas cinco bases interrogadas.",
    "Foram recuperados 952 registros com conteúdo psicológico.",
    "A mineração dos 331 textos completos disponíveis",
    "Dos 952 registros no escopo da revisão",
    "Procedimento de varredura identificou 1 duplicata verdadeira",
    "O terceiro concerne às práticas de relato.",
    "[A PREENCHER: Resultados da triagem e caracterização dos estudos incluídos]",
)
