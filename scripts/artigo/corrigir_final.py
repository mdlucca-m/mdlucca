#!/usr/bin/env python3
"""Aplica as correções auditadas ao Artigo_Final_ e grava a versão final.

Edita o .docx no lugar — descompacta, altera word/document.xml, recompacta —
para preservar as 67 imagens, as 73 tabelas e toda a formatação. Reconstruir
o documento do zero perderia tudo isso.

    python3 scripts/artigo/corrigir_final.py Artigo_Final_.docx -o VERSAO_FINAL.docx

Duas categorias de intervenção, deliberadamente separadas:

  CORRIGE  o que o próprio documento permite decidir. Cada correção abaixo é
           sustentada por outra passagem do mesmo artigo, citada no código.

  SINALIZA o que exige recomputar a partir dos dados brutos. Nada é inventado:
           insere-se uma nota de reconciliação que nomeia a pendência, mostra
           os valores em conflito e diz o que precisa ser feito.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import orientacoes  # noqa: E402

# ── 1 · Correções de texto ──────────────────────────────────────────────────
# (rótulo, trecho procurado, trecho novo, justificativa no próprio artigo)
SUBSTITUICOES: list[tuple[str, str, str, str]] = [
    (
        "resumo · confiabilidade",
        "mostraram boa confiabilidade; tensão (α = 0,43) não atingiu o critério "
        "de 0,70.",
        "mostraram boa confiabilidade. Pelo α de Cronbach, três das seis "
        "subescalas ficaram abaixo do critério de 0,70 — tensão (0,43), "
        "confusão (0,65) e vigor (0,68) —; pelo ω ordinal, coeficiente "
        "adequado a itens ordinais assimétricos e adotado neste estudo, as "
        "três alcançam o critério (0,79, 0,84 e 0,79).",
        "A Tabela 3 registra α = 0,68 para o vigor e 0,65 para a confusão, "
        "ambos abaixo de 0,70; o resumo mencionava apenas a tensão. Os valores "
        "de ω vêm da Tabela 43.",
    ),
    (
        "Tabela 3 · base do erro de medida",
        "Confiabilidade interna e erro de medida por subescala.",
        "Confiabilidade interna e erro de medida por subescala. O SEM e o "
        "MDC₉₅ desta tabela derivam do α de Cronbach; as Tabelas 43 e 56 "
        "reportam os mesmos indicadores a partir do ω e do ICC, com valores "
        "distintos — ver a Nota de reconciliação ao final da seção 4.",
        "Três tabelas reportam SEM e MDC₉₅ por subescala com valores "
        "diferentes, sem declarar a fonte de cada um.",
    ),
    (
        "Tabela 43 · base do erro de medida",
        "Erro-padrão de medida (SEM) e diferença mínima detectável (MDC₉₅) por "
        "subescala.",
        "Erro-padrão de medida (SEM) e diferença mínima detectável (MDC₉₅) por "
        "subescala, derivados do ômega de McDonald.",
        "Distingue esta tabela da Tabela 3 (α) e da Tabela 56 (ICC).",
    ),
    (
        "Tabela 56 · base do erro de medida",
        "Fiabilidade teste-reteste (ICC 2,1), erro-padrão de medida (SEM) e "
        "diferença mínima detectável (MDC₉₅).",
        "Fiabilidade teste-reteste (ICC 2,1), erro-padrão de medida (SEM) e "
        "diferença mínima detectável (MDC₉₅), derivados do ICC. Por partir da "
        "estabilidade das medidas repetidas, é este o MDC₉₅ recomendado como "
        "referência para decisão individual.",
        "O MDC₉₅ é um limiar de decisão prática; com três valores por "
        "subescala, o leitor não sabe qual aplicar.",
    ),
    (
        "Tabela 19 · método de estimação",
        "Média diária de cada variável (dois passos; * = dia de HIIT).",
        "Média diária de cada variável (estimativa em dois passos; * = dia de "
        "HIIT). Os valores divergem dos da Tabela 52, que reporta a média "
        "bruta por dia — ver a Nota de reconciliação ao final da seção 4.",
        "PTH no Dia 3: 2,87 nesta tabela e 4,5 na Tabela 52, sem explicação "
        "no texto; 'dois passos' não é definido em nenhum ponto.",
    ),
    (
        "Tabela 52 · método de estimação",
        "Nível médio por dia do microciclo (Dia 1 = baseline; * = dia de HIIT).",
        "Nível médio bruto por dia do microciclo (Dia 1 = baseline; * = dia de "
        "HIIT). Ver a Nota de reconciliação quanto à divergência com a "
        "Tabela 19.",
        "Mesma grandeza, valores diferentes.",
    ),
]

# ── 2 · Correção de célula: Tabela 35, linha do Vigor ──────────────────────
# O artigo afirma três vezes que o vigor sobrevive ao FDR:
#   · Tabela 23: p_FDR = 0,005;
#   · "quatro variáveis ... sobreviveram à correção e ao FDR — fadiga física,
#      fadiga, PTH e vigor —, todas na direção esperada (vigor: dz = −0,39;
#      p_FDR = 0,005)";
#   · "as quatro variáveis do eixo energia–fadiga (Fadiga física, PTH, Fadiga
#      e Vigor) sobrevivem".
# A célula "Não" da Tabela 35 é o único ponto discordante.
CELULA_VIGOR_FDR = ("Tabela 35", "Vigor", "Não", "Sim")

# ── 3 · Nota de reconciliação ──────────────────────────────────────────────
NOTA_TITULO = "4.16 Nota de reconciliação"

NOTA_PARAGRAFOS = [
    "Três pontos deste manuscrito não podem ser resolvidos sem retornar à base "
    "de dados, e ficam aqui registrados de forma explícita em vez de "
    "silenciados. Nenhum deles altera a direção dos achados; todos afetam a "
    "precisão do que se pode afirmar.",

    "Primeiro, o número de observações. O Esquema 1 descreve uma coleta no "
    "Dia 1 (baseline) e coletas pré e pós nos Dias 2 a 7, o que permite no "
    "máximo treze observações por atleta e, com 27 atletas, 351 observações. "
    "O manuscrito reporta 456. Mesmo tomando os 135 pares pré→pós declarados, "
    "chega-se a 270 observações pareadas mais os baselines, abaixo do total "
    "reportado. É preciso publicar o fluxo de dados — atletas × dias × coletas "
    "→ observações válidas — e reconciliar o denominador de todas as análises "
    "que o utilizam.",

    "Segundo, o erro de medida. As Tabelas 3, 43 e 56 reportam SEM e MDC₉₅ por "
    "subescala a partir de três coeficientes distintos (α, ω e ICC), o que "
    "produz limiares que chegam a diferir por um fator de dois: para a tensão, "
    "o MDC₉₅ varia de 1,83 a 3,69. As legendas passaram a declarar a origem de "
    "cada conjunto, e adota-se o da Tabela 56 como referência de decisão "
    "individual, por derivar da estabilidade teste-reteste. Cabe aos autores "
    "confirmar essa escolha e uniformizar as referências ao MDC₉₅ ao longo do "
    "texto.",

    "Terceiro, as médias diárias. As Tabelas 19 e 52 reportam a mesma "
    "grandeza — o nível médio de cada variável por dia — com valores "
    "diferentes: a perturbação total do humor no Dia 3 aparece como 2,87 e "
    "como 4,5. A Tabela 19 indica estimativa 'em dois passos', expressão não "
    "definida no manuscrito. É necessário declarar o estimador de cada uma "
    "(média marginal do modelo ou média bruta) e verificar se a divergência "
    "decorre disso.",

    "Registre-se ainda uma correção já aplicada: a Tabela 35 assinalava o "
    "vigor como não sobrevivente à correção FDR, em contradição com a "
    "Tabela 23 (p_FDR = 0,005), com a Figura 42 e com duas passagens do texto "
    "que o listam entre as quatro variáveis sobreviventes. A célula foi "
    "corrigida para 'Sim'.",
]


def escapar(t: str) -> str:
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def paragrafo(texto: str, *, negrito=False, titulo=False) -> str:
    ppr = ('<w:pPr><w:spacing w:before="240" w:after="120"/>'
           '<w:jc w:val="left"/></w:pPr>' if titulo else
           '<w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/>'
           '<w:jc w:val="both"/></w:pPr>')
    rpr = "<w:rPr>" + ('<w:b/>' if negrito or titulo else "") + "</w:rPr>"
    return (f'<w:p xmlns:w="{W}">{ppr}<w:r>{rpr}'
            f'<w:t xml:space="preserve">{escapar(texto)}</w:t></w:r></w:p>')


FONTE_TAB = ('<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
             'w:cs="Times New Roman"/><w:color w:val="000000"/><w:sz w:val="16"/>')


def _celula(texto: str, largura: int, negrito: bool) -> str:
    rpr = "<w:rPr>" + FONTE_TAB + ("<w:b/>" if negrito else "") + "</w:rPr>"
    return (f'<w:tc><w:tcPr><w:tcW w:w="{largura}" w:type="dxa"/>'
            '<w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr><w:spacing w:after="0"/><w:jc w:val="center"/>'
            f'<w:rPr>{FONTE_TAB}</w:rPr></w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">{escapar(texto)}</w:t>'
            "</w:r></w:p></w:tc>")


def tabela_ooxml(cabecalho: list[str], linhas: list[list[str]]) -> str:
    """Gera uma tabela com as mesmas bordas e margens das já existentes."""
    n = len(cabecalho)
    larg = max(600, 9060 // n)
    bordas = "".join(
        f'<w:{b} w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        for b in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{larg}"/>' for _ in range(n))
    cab = ('<w:tr><w:trPr><w:tblHeader/><w:jc w:val="center"/></w:trPr>'
           + "".join(_celula(c, larg, True) for c in cabecalho) + "</w:tr>")
    corpo = "".join(
        '<w:tr><w:trPr><w:jc w:val="center"/></w:trPr>'
        + "".join(_celula(c, larg, False) for c in linha) + "</w:tr>"
        for linha in linhas)
    return (f'<w:tbl xmlns:w="{W}"><w:tblPr>'
            '<w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
            f"<w:tblBorders>{bordas}</w:tblBorders>"
            '<w:tblCellMar><w:top w:w="40" w:type="dxa"/>'
            '<w:left w:w="90" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/>'
            '<w:right w:w="90" w:type="dxa"/></w:tblCellMar>'
            '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" '
            'w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
            f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{cab}{corpo}</w:tbl>")


def bloco_orientacoes() -> str:
    """Seções 4.17 e 4.18, com a Tabela 71, conforme as orientações."""
    o = orientacoes
    t = o.TABELA_CARGA
    partes = [paragrafo(o.SECAO_CARGA_TITULO, titulo=True)]
    partes.append(paragrafo(o.SECAO_CARGA[0]))
    partes.append(paragrafo(t["legenda"], negrito=False))
    partes.append(tabela_ooxml(t["cabecalho"], t["linhas"]))
    partes.append(paragrafo(t["fonte"]))
    partes.append(paragrafo(t["nota"]))
    partes += [paragrafo(p) for p in o.SECAO_CARGA[1:]]
    partes.append(paragrafo(o.SECAO_RECOMENDACOES_TITULO, titulo=True))
    partes += [paragrafo(p) for p in o.SECAO_RECOMENDACOES]
    return "".join(partes)


def corrigir_celula(xml: str, legenda: str, linha_rotulo: str,
                    de: str, para: str) -> tuple[str, bool]:
    """Troca o valor de uma célula na tabela que segue a legenda dada."""
    m = re.search(re.escape(legenda) + r"\s*(?:<[^>]+>\s*)*[–-]", xml)
    if not m:
        return xml, False
    ini = xml.find("<w:tbl", m.end())
    fim = xml.find("</w:tbl>", ini)
    if ini == -1 or fim == -1:
        return xml, False
    tabela = xml[ini:fim]
    # localizar a linha cujo primeiro texto é o rótulo
    novo_tab, trocou = [], False
    pos = 0
    for lm in re.finditer(r"<w:tr[ >].*?</w:tr>", tabela, re.S):
        tr = lm.group(0)
        textos = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", tr)
        if not trocou and textos and textos[0].strip() == linha_rotulo and de in textos:
            tr = re.sub(rf">{re.escape(de)}</w:t>", f">{para}</w:t>", tr, count=1)
            trocou = True
        novo_tab.append(tabela[pos:lm.start()] + tr)
        pos = lm.end()
    if not trocou:
        return xml, False
    return xml[:ini] + "".join(novo_tab) + tabela[pos:] + xml[fim:], True


def inserir_nota(xml: str) -> tuple[str, bool]:
    """Insere a nota logo antes do início da seção 5 (Conclusões/Considerações)."""
    alvo = None
    for pad in (r"<w:t[^>]*>\s*5\s+DISCUSS", r"<w:t[^>]*>\s*5\s+CONCLUS",
                r"<w:t[^>]*>\s*5\s+CONSIDERA", r"<w:t[^>]*>\s*5\s+LIMITA",
                r"<w:t[^>]*>\s*REFER[ÊE]NCIAS"):
        m = re.search(pad, xml)
        if m:
            alvo = m.start()
            break
    if alvo is None:
        return xml, False
    ini = xml.rfind("<w:p ", 0, alvo)
    if ini == -1:
        ini = xml.rfind("<w:p>", 0, alvo)
    if ini == -1:
        return xml, False
    bloco = paragrafo(NOTA_TITULO, titulo=True) + "".join(
        paragrafo(p) for p in NOTA_PARAGRAFOS)
    return xml[:ini] + bloco + xml[ini:], True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path)
    ap.add_argument("-o", "--saida", type=Path, required=True)
    ap.add_argument("--merge-runs", default="/mnt/skills/public/docx/scripts/merge_runs.py")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        unp = Path(tmp) / "unp"
        with zipfile.ZipFile(a.entrada) as z:
            z.extractall(unp)
        for l in unp.rglob("*"):
            if l.is_symlink():
                l.unlink()
        if Path(a.merge_runs).exists():
            subprocess.run([sys.executable, a.merge_runs, str(unp)],
                           check=True, capture_output=True)

        doc = unp / "word" / "document.xml"
        xml = doc.read_text(encoding="utf-8")
        antes = len(xml)

        print("── correções de texto ──")
        for rotulo, de, para, motivo in SUBSTITUICOES:
            n = xml.count(de)
            if n == 0:
                print(f"  ✗ {rotulo}: trecho não encontrado")
                continue
            xml = xml.replace(de, para, 1)
            print(f"  ✓ {rotulo}" + (f"  ({n} ocorrências, 1 alterada)" if n > 1 else ""))
            print(f"      motivo: {motivo}")

        print("\n── correção de célula ──")
        legenda, linha, de, para = CELULA_VIGOR_FDR
        xml, ok = corrigir_celula(xml, legenda, linha, de, para)
        print(f"  {'✓' if ok else '✗'} {legenda}, linha {linha}: "
              f"'{de}' → '{para}'" + ("" if ok else " (não localizada)"))

        print("\n── nota de reconciliação ──")
        xml, ok = inserir_nota(xml)
        print(f"  {'✓' if ok else '✗'} {NOTA_TITULO} "
              f"({len(NOTA_PARAGRAFOS)} parágrafos)")

        print("\n── orientações do orientador ──")
        for rotulo, de, para, motivo in orientacoes.AJUSTES:
            if de in xml:
                xml = xml.replace(de, para, 1)
                print(f"  ✓ {rotulo}")
                print(f"      pedido: {motivo}")
            else:
                print(f"  ✗ {rotulo}: trecho não encontrado")

        m = re.search(r"<w:t[^>]*>\s*5\s+DISCUSS", xml)
        if m:
            ini = xml.rfind("<w:p ", 0, m.start())
            if ini == -1:
                ini = xml.rfind("<w:p>", 0, m.start())
            xml = xml[:ini] + bloco_orientacoes() + xml[ini:]
            print(f"  ✓ §4.17 e §4.18 inseridas, com a Tabela "
                  f"{orientacoes.TABELA_CARGA['numero']} "
                  f"({len(orientacoes.TABELA_CARGA['linhas'])} dias)")
        else:
            print("  ✗ não localizei o início da seção 5")

        doc.write_text(xml, encoding="utf-8")
        print(f"\n  document.xml: {antes // 1024} KB → {len(xml) // 1024} KB")

        a.saida.parent.mkdir(parents=True, exist_ok=True)
        tmp_zip = Path(tmp) / "out.docx"
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for item in sorted(unp.rglob("*")):
                if item.is_file():
                    z.write(item, item.relative_to(unp).as_posix())
        shutil.move(tmp_zip, a.saida)

    with zipfile.ZipFile(a.saida) as z:
        imgs = sum(1 for n in z.namelist() if n.startswith("word/media/"))
    print(f"\ngerado: {a.saida}  ({a.saida.stat().st_size // 1024} KB, "
          f"{imgs} imagens preservadas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
