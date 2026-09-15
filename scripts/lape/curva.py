"""Calculo sobre as curvas do laboratorio: derivada, aceleracao, integral
e limiar.

A matematica mora em `estatistica.py` e foi escrita para a bancada -- uma
pessoa medida em varios momentos. Este modulo faz o outro lado: descobre
QUE curvas o banco tem para oferecer, e aplica a cada uma so a leitura
que ela sustenta.

FLUXO E ESTOQUE, e por que a diferenca decide o que se pode dizer:

  Uma serie de ESTOQUE e um nivel: o acervo tem 141 artigos hoje. A area
  sob ela e "artigo-ano" -- quanto de producao o laboratorio manteve de
  pe ao longo do tempo. E a leitura de EXPOSICAO da integral, a mesma que
  na bancada responde "quanto de dor a pessoa carregou".

  Uma serie de FLUXO e uma taxa: 12 publicacoes em 2026. A area sob ela
  nao e exposicao -- e o proprio estoque, e o estoque a gente SABE, pela
  soma. Apresentar o trapezio como total publicado seria trocar um numero
  exato por uma aproximacao e chamar a aproximacao de integral: o
  trapezio entre 9 e 12 devolve 10,5 onde a resposta e 12.

  Por isso a integral so e oferecida sobre estoque. Sobre fluxo, o que
  este modulo devolve e a soma exata, dita como soma.

A DERIVADA de um estoque e o fluxo, e vice-versa. Entao cada serie
aparece com a leitura que the cabe, e nao com as quatro de enfeite.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from . import estatistica
from .db import Database

# Um ano. As curvas do laboratorio sao anuais -- falar em "por dia" numa
# serie de producao daria numeros com quatro zeros depois da virgula.
POR = 1.0

# Menos de tres pontos nao sustentam aceleracao, e menos de dois nao
# sustentam nem derivada. A tela precisa saber disso ANTES de desenhar um
# ponteiro, senao desenha um ponteiro em zero -- que se le como "parado".
N_MINIMO_DA_CURVA = 3


def _anos_da_janela(db: Database, janela: int) -> list[int]:
    hoje = date.today().year
    return list(range(hoje - janela + 1, hoje + 1))


def _por_ano(db: Database, sql: str, anos: list[int]) -> list[float]:
    """Conta por ano, e devolve ZERO no ano sem nada -- nao um buraco.

    Ano vazio e informacao: um laboratorio que publicou em 2022 e 2024 e
    nada em 2023 tem uma queda a explicar. Pular o ano faria a derivada
    passar reto por cima dela, e a curva sairia mais lisa do que o
    trabalho foi.
    """
    contas = {int(r["ano"]): int(r["n"] or 0)
              for r in db.dicts(sql) if r["ano"] is not None}
    return [float(contas.get(a, 0)) for a in anos]


def series(db: Database, janela: int = 10) -> list[dict[str, Any]]:
    """As curvas que este banco tem, cada uma com o que ela e.

    `kind` decide a leitura: "estoque" ganha integral, "fluxo" ganha soma.

    Cada curva traz TRES unidades, e nao uma: a do nivel, a da derivada e
    a da aceleracao. Sao tres porque derivar muda a unidade, e a tela que
    reaproveita a unidade da derivada no acelerometro passa a rotular
    aceleracao com unidade de velocidade -- o medidor fica certo e o
    rotulo mente. Numa curva de FLUXO isso ja comeca um degrau adiante:
    "publicacoes por ano" e ela mesma um ritmo, logo a sua derivada e uma
    aceleracao (por ano quadrado) e a sua segunda derivada vai a ano cubo.
    """
    anos = _anos_da_janela(db, janela)

    publicadas = _por_ano(db, (
        "SELECT CAST(strftime('%Y', published_on) AS INTEGER) AS ano, COUNT(*) AS n"
        "  FROM articles WHERE status = 'publicado' AND published_on IS NOT NULL"
        "  GROUP BY ano"), anos)

    # O acervo e o estoque: quanto havia publicado AO FIM de cada ano.
    # Inclui o que foi publicado antes da janela, senao a curva comeca em
    # zero num laboratorio de vinte anos e a derivada do primeiro ano sai
    # gigante -- um artefato da janela, lido como um ano historico.
    antes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
        "   AND published_on IS NOT NULL"
        "   AND CAST(strftime('%Y', published_on) AS INTEGER) < ?",
        (anos[0],)) or 0)
    acervo, corrente = [], float(antes)
    for n in publicadas:
        corrente += n
        acervo.append(corrente)

    citadas = _por_ano(db, (
        "SELECT CAST(strftime('%Y', published_on) AS INTEGER) AS ano,"
        "       SUM(MAX(COALESCE(wos_citations, 0), COALESCE(scopus_citations, 0),"
        "               COALESCE(openalex_citations, 0))) AS n"
        "  FROM articles WHERE status = 'publicado' AND published_on IS NOT NULL"
        "  GROUP BY ano"), anos)

    return [
        {"code": "acervo", "rotulo": "Acervo publicado", "kind": "estoque",
         "unidade": "artigos", "unidade_taxa": "artigos/ano",
         "unidade_aceleracao": "artigos/ano²",
         "anos": anos, "valores": acervo,
         "explica": "Quantos artigos publicados o laboratório tinha ao fim de "
                    "cada ano. Sobe e nunca desce: é um nível, e não um ritmo.",
         "base_fora_da_janela": antes},
        {"code": "publicacoes", "rotulo": "Publicações por ano", "kind": "fluxo",
         "unidade": "publicações", "unidade_taxa": "publicações/ano²",
         "unidade_aceleracao": "publicações/ano³",
         "anos": anos, "valores": publicadas,
         "explica": "Quantos artigos saíram em cada ano. É a derivada do acervo "
                    "— por isso a derivada DESTA curva é a aceleração da produção."},
        {"code": "citacoes", "rotulo": "Citações por ano de publicação",
         "kind": "fluxo", "unidade": "citações", "unidade_taxa": "citações/ano²",
         "unidade_aceleracao": "citações/ano³",
         "anos": anos, "valores": citadas,
         "explica": "Citações somadas dos artigos publicados em cada ano, pela "
                    "melhor base de cada artigo. O ano recente aparece baixo por "
                    "ser recente: a citação chega com atraso."},
    ]


def _limiar_da_serie(db: Database, code: str, anos: list[int]) -> dict[str, Any] | None:
    """O limiar vem da META DECLARADA, e nunca de um palpite.

    Sem meta, nao ha limiar -- e a tela diz isso em vez de desenhar uma
    linha num numero redondo que ninguem escolheu. Uma linha de corte
    inventada e pior do que nenhuma: quem olha supoe que o laboratorio a
    declarou, e passa a se comparar com ela.
    """
    from . import metas

    if code != "publicacoes":
        return None
    declaradas = metas.metas_declaradas(db, anos[-1]) or {}
    alvo = declaradas.get("publicacoes")
    if not alvo:
        return None
    return {"valor": float(alvo), "menor_e_melhor": False,
            "de_onde": "meta declarada para " + str(anos[-1])}


def analisar(db: Database, code: str = "acervo",
             janela: int = 10) -> dict[str, Any]:
    """A curva pedida, com a leitura que ela sustenta."""
    todas = series(db, janela=janela)
    escolhida = next((s for s in todas if s["code"] == code), None)
    if escolhida is None:
        escolhida = todas[0]

    anos, valores = escolhida["anos"], escolhida["valores"]
    saida: dict[str, Any] = {
        "serie": escolhida,
        "disponiveis": [{"code": s["code"], "rotulo": s["rotulo"],
                         "kind": s["kind"]} for s in todas],
        "pontos": [{"t": a, "v": v} for a, v in zip(anos, valores)],
        "derivada": None, "aceleracao": None, "integral": None,
        "soma": None, "limiar": None, "aviso": None,
    }
    if len(anos) < 2:
        saida["aviso"] = "são precisos ao menos dois anos para haver curva"
        return saida

    saida["derivada"] = estatistica.taxa_de_variacao(anos, valores, por=POR)
    if len(anos) >= N_MINIMO_DA_CURVA:
        saida["aceleracao"] = estatistica.aceleracao(anos, valores, por=POR)

    if escolhida["kind"] == "estoque":
        # Area sob um NIVEL: exposicao. "Artigo-ano" -- quanto de producao
        # o laboratorio manteve de pe ao longo da janela.
        saida["integral"] = estatistica.area_sob_a_curva(anos, valores)
        saida["integral"]["unidade"] = escolhida["unidade"] + "-ano"
    else:
        # Fluxo: a area E o estoque, e o estoque se sabe pela soma. O
        # trapezio entre 9 e 12 devolve 10,5 onde a resposta e 12.
        saida["soma"] = {
            "total": round(sum(valores), 3),
            "unidade": escolhida["unidade"],
            "porque": "Numa curva de fluxo a área sob a curva é o próprio "
                      "acumulado, e o acumulado se sabe pela soma exata. O "
                      "trapézio daria uma aproximação, e chamá-la de integral "
                      "trocaria um número certo por uma aproximação.",
        }

    limiar = _limiar_da_serie(db, escolhida["code"], anos)
    if limiar:
        saida["limiar"] = estatistica.cruzamento_do_limiar(
            anos, valores, limiar["valor"],
            menor_e_melhor=limiar["menor_e_melhor"])
        saida["limiar"].update(limiar)
    return saida
