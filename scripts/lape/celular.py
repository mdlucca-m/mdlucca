"""O painel em forma de aplicativo de celular, para mostrar a alguem.

O instantaneo (`instantaneo.py`) e o painel inteiro numa pagina: serve
para TRABALHAR longe da maquina. Este e outro proposito -- serve para
MOSTRAR. Quem recebe abre no celular, num elevador, sem contexto nenhum,
e precisa entender o laboratorio em trinta segundos.

Por isso as duas telas nao sao a mesma coisa encolhida:

  - a navegacao vai embaixo, ao alcance do polegar, e nao numa coluna
    lateral que no celular vira uma tira de rolagem horizontal;
  - cada aba e uma TELA, nao uma secao -- rolar quinze cartoes atras de
    um numero e o que faz alguem fechar a pagina;
  - o numero vem antes da explicacao, e a explicacao vem antes da
    tabela. Quem quiser o detalhe desce; quem quiser a ideia nao precisa.

E, como o instantaneo, este arquivo e um RETRATO: nao esta ao vivo, nao
grava, e diz isso na tela de abertura e na aba "Sobre".
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from . import analise, config, versao
from .db import Database

TEMPLATES = Path(__file__).resolve().parent / "templates"


def _e(valor: Any) -> str:
    """Escapa para HTML. Titulo de artigo tem `&`, `<` e aspas."""
    return html.escape("" if valor is None else str(valor), quote=True)


def _icone(nome: str, tamanho: int = 20) -> str:
    """Um lugar para o icone; o `icons.js` do sistema preenche no arranque.

    Guardar os tracos aqui tambem duplicaria a biblioteca -- e um dia as
    duas copias divergiriam sem ninguem perceber.
    """
    return f'<i class="ic" data-icone="{nome}" data-tam="{tamanho}"></i>'


def _curto(nome: Any) -> str:
    """"LAPE - Laboratorio de ..." vira "LAPE".

    No topo de um celular cabem trinta caracteres; o nome inteiro empurra
    a data para fora e nao sobra nem um nem outro.
    """
    texto = str(nome or "").strip()
    for corte in (" - ", " — ", " – ", ": "):
        if corte in texto:
            return texto.split(corte, 1)[0].strip()
    return texto[:34]


def _numero(valor: Any) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


# ----------------------------------------------------------------------
# Os dados que cabem numa tela de celular
# ----------------------------------------------------------------------
def reunir(db: Database) -> dict[str, Any]:
    """So o que as cinco telas usam -- nem tudo o que o painel calcula."""
    from .api import _artigos_do_panorama

    p = analise.panorama(db)
    tri = analise.triangulacao(db)
    prev = analise.prevalencia(db, p["janela"]["anos"])
    artigos = _artigos_do_panorama(db)
    hoje = prev["hoje"] or {"estados": {}, "total": 0}

    por_ano: dict[int, int] = {}
    for artigo in artigos:
        if artigo.get("ano"):
            por_ano[artigo["ano"]] = por_ano.get(artigo["ano"], 0) + 1

    return {
        "lab": {"nome": config.LAB_NAME, "instituicao": config.LAB_INSTITUTION,
                "site": getattr(config, "LAB_SITE", None)},
        "janela": p["janela"],
        "total": len(artigos),
        "integrantes": int(db.scalar("SELECT COUNT(*) FROM members") or 0),
        "projetos": int(db.scalar("SELECT COUNT(*) FROM projects") or 0),
        "estados": hoje["estados"],
        "variaveis": sorted(p["variaveis"], key=lambda v: -v["total_geral"]),
        "por_ano": dict(sorted(por_ano.items())),
        "triangulacao": tri,
        "artigos": sorted(artigos, key=lambda a: (-(a.get("ano") or 0),
                                                  a.get("title") or "")),
        "sintese": analise.sintese(db, p),
    }


# ----------------------------------------------------------------------
# Pecas de tela
# ----------------------------------------------------------------------
def _cartao(titulo: str, icone: str, corpo: str, dica: str = "") -> str:
    return (f'<section class="cartao"><h2>{_icone(icone, 17)}'
            f"<span>{_e(titulo)}</span></h2>"
            + (f'<p class="dica">{dica}</p>' if dica else "")
            + corpo + "</section>")


def _barras(valores: dict[Any, int], unidade: str = "artigo(s)") -> str:
    """Barras horizontais: um so matiz, porque e uma so medida.

    No celular a barra deitada e a unica que aceita rotulo legivel -- em
    pe, o nome da variavel vira texto girado de 8px.
    """
    if not valores:
        return '<p class="vazio">Sem dados ainda.</p>'
    teto = max(valores.values()) or 1
    linhas = []
    for rotulo, n in valores.items():
        largura = max(2, round(n / teto * 100))
        linhas.append(
            '<li><span class="rot">' + _e(rotulo) + "</span>"
            f'<span class="trilho"><i style="width:{largura}%"></i></span>'
            f'<b>{_numero(n)}</b></li>')
    return (f'<ul class="barras" aria-label="{_e(unidade)}">'
            + "".join(linhas) + "</ul>")


MIN_ANOS_PARA_CURVA = 3


def _colunas_por_ano(por_ano: dict[int, int]) -> str:
    """A producao no tempo. Coluna por ano, com o ano so onde cabe.

    Com um ou dois anos nao ha curva: uma coluna sozinha ocupa a largura
    inteira e vira um bloco azul que parece defeito. Nesse caso a frase
    diz mais que o desenho -- e diz a verdade, que e nao haver serie.
    """
    if not por_ano:
        return '<p class="vazio">Nenhum artigo com ano de referência.</p>'
    if len(por_ano) < MIN_ANOS_PARA_CURVA:
        partes = ", ".join(f"<b>{_numero(n)}</b> em {ano}"
                           for ano, n in sorted(por_ano.items()))
        return ('<p class="texto">Toda a produção cadastrada está em '
                f"{'um ano' if len(por_ano) == 1 else 'dois anos'}: {partes}. "
                "Não há série para desenhar — e desenhar mesmo assim daria "
                "uma barra sozinha ocupando a tela inteira.</p>"
                '<p class="pe">Os anos vêm das datas do cadastro. A história '
                "mais antiga do laboratório está no Lattes da equipe, que o "
                "sistema importa.</p>")
    anos = list(por_ano)
    teto = max(por_ano.values()) or 1
    passo = max(1, len(anos) // 6)
    colunas = []
    for i, ano in enumerate(anos):
        n = por_ano[ano]
        alt = max(3, round(n / teto * 100))
        mostra = (i % passo == 0) or i == len(anos) - 1
        colunas.append(
            f'<li title="{ano}: {n} artigo(s)">'
            f'<span class="col"><i style="height:{alt}%"></i></span>'
            f'<span class="ano">{ano if mostra else ""}</span></li>')
    return ('<ul class="colunas">' + "".join(colunas) + "</ul>"
            f'<p class="pe">Pico de {_numero(teto)} num ano.</p>')


def _selo(rotulo: str, tom: str = "") -> str:
    return f'<span class="selo{tom}">{_e(rotulo)}</span>'


def _links_do_artigo(a: dict[str, Any]) -> str:
    """So os destinos que existem. Link quebrado custa mais que a ausencia."""
    doi = str(a.get("doi") or "").replace("https://doi.org/", "").strip()
    fora = []
    if doi:
        fora.append(("DOI", f"https://doi.org/{doi}", ""))
    if a.get("pmc"):
        fora.append(("PMC · texto livre",
                     f"https://www.ncbi.nlm.nih.gov/pmc/articles/{a['pmc']}/", " livre"))
    if a.get("pmid"):
        fora.append(("PubMed", f"https://pubmed.ncbi.nlm.nih.gov/{a['pmid']}/", ""))
    if not fora:
        return ""
    return ('<div class="fora">' + "".join(
        f'<a class="base{tom}" href="{_e(url)}" target="_blank" rel="noopener">'
        f"{_e(rotulo)}</a>" for rotulo, url, tom in fora) + "</div>")


# ----------------------------------------------------------------------
# As cinco telas
# ----------------------------------------------------------------------
def _tela_visao(d: dict[str, Any]) -> str:
    estados = d["estados"]
    publicados = estados.get("publicado", 0)
    avaliando = estados.get("em avaliação", 0)
    escrevendo = estados.get("em produção", 0)
    ativas = sum(1 for v in d["variaveis"] if v["total_geral"])

    grade = "".join(
        f'<div class="mini"><span class="rotulo">{_e(rotulo)}</span>'
        f'<b>{_numero(valor)}</b><small>{_e(pe)}</small></div>'
        for rotulo, valor, pe in (
            ("Publicados", publicados, "já saíram"),
            ("Em avaliação", avaliando, "com as revistas"),
            ("Em escrita", escrevendo, "na bancada"),
            ("Variáveis", ativas, "temas ativos"),
        ))

    topo = (
        '<section class="heroi">'
        f'<span class="rotulo">Acervo · {d["janela"]["de"]}–{d["janela"]["ate"]}</span>'
        f'<b class="grandao">{_numero(d["total"])}</b>'
        '<span class="sub">artigos do laboratório</span>'
        f'<div class="grade2">{grade}</div>'
        "</section>")

    principais = {v["label"]: v["total_geral"] for v in d["variaveis"][:6]
                  if v["total_geral"]}
    return topo + _cartao(
        "O que o laboratório mais estuda", "alvo", _barras(principais),
        "As seis variáveis com mais artigos. A lista inteira está em Temas.")


def _tela_temas(d: dict[str, Any]) -> str:
    tri = d["triangulacao"]
    todas = {v["label"]: v["total_geral"] for v in d["variaveis"] if v["total_geral"]}

    falta = len(tri["faltando"].get("desfecho", []))
    resumo = (
        '<section class="cartao destaque">'
        f'<h2>{_icone("hierarquia", 17)}<span>Em quem, com o quê, medindo o quê</span></h2>'
        '<p class="dica">Todo artigo de intervenção responde três perguntas. '
        "Fechar as três é o que separa um achado de uma descrição.</p>"
        f'<div class="par"><div><b>{_numero(tri["completos"])}</b>'
        f'<small>fecham as três</small></div>'
        f'<div><b>{_numero(falta)}</b><small>sem desfecho declarado</small></div></div>'
        + (f'<p class="pe aviso">{_numero(falta)} artigo(s) dizem o que fizeram e não '
           "dizem o que mediram — é por aí que se continua.</p>" if falta else "")
        + "</section>")

    # Agrupado pela condicao: repetir "Fibromialgia" em cada linha nao e
    # hierarquia, e uma lista com recuo. O que faz o degrau dizer alguma
    # coisa e a condicao aparecer uma vez e abrir as intervencoes.
    por_condicao: dict[str, list[dict[str, Any]]] = {}
    for t in tri["trios"][:8]:
        por_condicao.setdefault(t["aplicacao"], []).append(t)

    trios = ""
    for condicao, lista in por_condicao.items():
        degraus = ""
        for t in lista:
            artigos = "".join(f"<li>{_e(a['titulo'])}</li>" for a in t["artigos"][:2])
            degraus += (
                f'<span class="perna p2">{_icone("experimento", 13)}'
                f'{_e(t["intervencao"])}</span>'
                f'<span class="perna p3">{_icone("qualidade", 13)}{_e(t["desfecho"])}'
                f'<em>{t["n"]}</em></span>'
                f'<ul class="quais">{artigos}</ul>')
        trios += (
            '<li class="trio">'
            f'<span class="perna p1">{_icone("alvo", 13)}{_e(condicao)}</span>'
            + degraus + "</li>")
    caminhos = (_cartao("Os caminhos que se fecham", "rede",
                        f'<ul class="trios">{trios}</ul>',
                        "Condição → intervenção → desfecho.")
                if trios else "")

    return resumo + caminhos + _cartao(
        "Todas as variáveis", "alvo", _barras(todas),
        "Quantos artigos tocam cada tema. Um artigo pode contar em vários.")


def _tela_curva(d: dict[str, Any]) -> str:
    leitura = ""
    achados = (d["sintese"] or {}).get("achados") or []
    if achados:
        leitura = "".join(
            f'<li>{_e(a.get("texto") or a.get("titulo") or "")}</li>'
            for a in achados[:4])
        leitura = f'<ul class="leitura">{leitura}</ul>'
    return (_cartao("Produção ano a ano", "linhas",
                    _colunas_por_ano(d["por_ano"]),
                    f'Recorte de {d["janela"]["de"]} a {d["janela"]["ate"]}.')
            + (_cartao("O que a curva diz", "achado", leitura) if leitura else ""))


def _tela_artigos(d: dict[str, Any]) -> str:
    itens = []
    for a in d["artigos"]:
        selos = "".join(_selo(v["label"]) for v in (a.get("variaveis") or [])[:4])
        meta = " · ".join(x for x in [str(a.get("ano") or ""), a.get("journal")] if x)
        itens.append(
            '<li class="artigo">'
            f'<h3>{_e(a.get("title"))}</h3>'
            + (f'<p class="meta">{_e(meta)}</p>' if meta else "")
            + (f'<div class="selos">{selos}</div>' if selos else "")
            + _links_do_artigo(a)
            + "</li>")
    return _cartao(
        f"Artigos ({len(d['artigos'])})", "producao",
        f'<ul class="artigos">{"".join(itens)}</ul>',
        "Do mais recente ao mais antigo. Onde há identificador, o botão abre "
        "o artigo na base.")


def _tela_sobre(d: dict[str, Any], quando: datetime) -> str:
    lab = d["lab"]
    site = (f'<a href="{_e(lab["site"])}" target="_blank" rel="noopener">'
            f'{_e(lab["site"])}</a>') if lab.get("site") else ""
    return (
        _cartao("O laboratório", "instituicao",
                f'<p class="texto"><b>{_e(lab["nome"])}</b><br>{_e(lab["instituicao"])}'
                + (f"<br>{site}" if site else "") + "</p>"
                f'<div class="par"><div><b>{_numero(d["integrantes"])}</b>'
                f'<small>integrantes</small></div>'
                f'<div><b>{_numero(d["projetos"])}</b><small>projetos</small></div></div>')
        + _cartao(
            "Sobre estes números", "aviso",
            '<p class="texto">Este arquivo é um <b>retrato</b> do sistema do '
            f'laboratório, tirado em {quando.strftime("%d/%m/%Y às %H:%M")}. '
            "Não está ao vivo e não grava nada: o sistema fica no computador "
            "do laboratório, e é lá que se cadastra e se atualiza.</p>"
            '<p class="texto">O recorte é de <b>'
            f'{d["janela"]["de"]}–{d["janela"]["ate"]}</b>. Produção mais antiga foi '
            "feita com outra equipe e outra pergunta, e misturar tudo numa curva "
            "só faz a curva não significar nada.</p>"
            f'<p class="pe">versão {_e(versao.resumo())}</p>'))


ABAS = (
    ("visao", "Visão", "painel"),
    ("temas", "Temas", "alvo"),
    ("curva", "Curva", "linhas"),
    ("artigos", "Artigos", "producao"),
    ("sobre", "Sobre", "instituicao"),
)

ESTILO = """
:root {
  color-scheme: dark;
  --fundo: #05070d; --superficie: #0b1018; --alta: #141d29;
  --tinta: #eaf0fa; --tinta2: #a7b4c9; --fraca: #77869b;
  --borda: #1c2634; --borda-forte: #2a3648;
  --tom: #5ec8f2; --tom-forte: #2fa8dd; --tom-lavado: #0c2735;
  --bom: #34c759; --alerta: #fab219;
  --raio: 16px;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
body {
  margin: 0; background: var(--fundo); color: var(--tinta);
  font: 15px/1.55 var(--sans); font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
  padding-bottom: calc(74px + env(safe-area-inset-bottom));
}
.ic { display: inline-flex; }
svg { display: block; }

/* ---- barra de cima: quem é, e de quando ---- */
header {
  position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; gap: 11px;
  padding: calc(10px + env(safe-area-inset-top)) 16px 10px;
  background: color-mix(in srgb, var(--superficie) 92%, transparent);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--borda);
}
header .marca {
  width: 34px; height: 34px; border-radius: 10px; flex: none;
  display: grid; place-items: center; font-weight: 800; font-size: 12.5px;
  background: linear-gradient(150deg, var(--tom-forte), #1b6ea8); color: #04121a;
}
header b { display: block; font-size: 14.5px; letter-spacing: -.01em; }
header small { display: block; font-size: 11.5px; color: var(--fraca); }

main { max-width: 560px; margin: 0 auto; padding: 14px 14px 24px; }
[hidden] { display: none !important; }

/* ---- o número que abre a tela ---- */
.heroi {
  position: relative; overflow: hidden;
  padding: 22px 18px 18px; margin-bottom: 14px;
  border-radius: var(--raio); border: 1px solid var(--borda-forte);
  background:
    radial-gradient(420px 220px at 18% -30%, rgba(94,200,242,.20), transparent 66%),
    var(--superficie);
}
.rotulo {
  font-size: 10.5px; text-transform: uppercase; letter-spacing: .09em;
  font-weight: 700; color: var(--fraca);
}
.grandao {
  display: block; font-size: 58px; line-height: 1; font-weight: 800;
  letter-spacing: -.045em; margin: 6px 0 2px;
}
.heroi .sub { font-size: 14px; color: var(--tinta2); }
.grade2 {
  display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 18px;
}
.mini {
  padding: 11px 12px; border-radius: 12px;
  background: var(--alta); border: 1px solid var(--borda);
}
.mini b {
  display: block; font-size: 25px; font-weight: 750; letter-spacing: -.03em;
  margin-top: 3px;
}
.mini small { font-size: 11.5px; color: var(--fraca); }

/* ---- cartões ---- */
.cartao {
  padding: 16px; margin-bottom: 13px; border-radius: var(--raio);
  background: var(--superficie); border: 1px solid var(--borda);
}
.cartao.destaque { border-color: color-mix(in srgb, var(--tom) 45%, transparent); }
.cartao h2 {
  /* alinhado ao topo: com título de duas linhas, `center` joga o ícone
     para o meio do bloco e ele deixa de apontar para o começo do texto */
  display: flex; align-items: flex-start; gap: 9px; margin: 0;
  font-size: 15.5px; letter-spacing: -.01em; text-wrap: balance;
}
.cartao h2 .ic { margin-top: 3px; flex: none; }
.cartao h2 .ic { color: var(--tom); }
.dica { margin: 7px 0 12px; font-size: 12.5px; color: var(--tinta2); }
.texto { margin: 10px 0 0; font-size: 13.5px; color: var(--tinta2); }
.texto b { color: var(--tinta); }
.texto a { color: var(--tom); }
.pe { margin: 12px 0 0; font-size: 12px; color: var(--fraca); }
.pe.aviso { color: var(--alerta); }
.vazio { color: var(--fraca); font-size: 13px; margin: 4px 0 0; }

.par { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px; }
.par > div {
  padding: 11px 12px; border-radius: 12px; background: var(--alta);
  border: 1px solid var(--borda);
}
.par b {
  display: block; font-size: 29px; font-weight: 780; letter-spacing: -.035em;
}
.par small { font-size: 11.5px; color: var(--fraca); }

/* ---- barras deitadas: uma medida, um matiz ---- */
.barras { list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: 10px; }
.barras li {
  display: grid; grid-template-columns: 1fr auto; align-items: center;
  gap: 3px 10px; grid-template-areas: "rot num" "trilho num";
}
.barras .rot { grid-area: rot; font-size: 13px; color: var(--tinta2); }
.barras .trilho {
  grid-area: trilho; height: 9px; border-radius: 99px; background: var(--alta);
  overflow: hidden;
}
.barras .trilho i {
  display: block; height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, var(--tom-forte), var(--tom));
}
.barras b { grid-area: num; font-size: 15px; font-weight: 750; }

/* ---- colunas por ano ---- */
.colunas {
  list-style: none; margin: 0; padding: 0; display: flex; align-items: flex-end;
  gap: 4px; height: 150px;
}
.colunas li { flex: 1; max-width: 64px; display: flex;
  flex-direction: column; height: 100%; }
.colunas .col { flex: 1; display: flex; align-items: flex-end; }
.colunas .col i {
  display: block; width: 100%; border-radius: 5px 5px 2px 2px;
  background: linear-gradient(180deg, var(--tom), var(--tom-forte));
}
.colunas .ano {
  font-size: 9.5px; color: var(--fraca); text-align: center; margin-top: 6px;
  white-space: nowrap;
}

/* ---- o triângulo, em três degraus ---- */
.trios { list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: 14px; }
.trio { border-left: 2px solid var(--tom-forte); padding-left: 12px; }
.perna {
  display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px;
  font-weight: 650; padding: 5px 10px; border-radius: 9px; margin: 0 0 5px;
  background: var(--alta); border: 1px solid var(--borda);
}
.perna.p1 { background: var(--tom-lavado); border-color: var(--tom-forte);
  color: var(--tom); }
.perna.p2 { margin-left: 12px; }
.perna.p3 { margin-left: 24px; font-weight: 550; }
.perna em {
  font-style: normal; font-size: 11px; padding: 0 6px; border-radius: 99px;
  background: var(--superficie); color: var(--tinta2);
}
.quais { list-style: none; margin: 2px 0 0 26px; padding: 0;
  font-size: 12px; color: var(--fraca); }
.quais li { margin-bottom: 3px; }

.leitura { margin: 0; padding-left: 18px; font-size: 13.5px; color: var(--tinta2); }
.leitura li { margin-bottom: 8px; }

/* ---- artigos ---- */
.artigos { list-style: none; margin: 0; padding: 0; }
.artigo { padding: 14px 0; border-top: 1px solid var(--borda); }
.artigo:first-child { border-top: none; padding-top: 4px; }
.artigo h3 { margin: 0; font-size: 14px; line-height: 1.45; font-weight: 650;
  text-wrap: pretty; }
.artigo .meta { margin: 5px 0 0; font-size: 12px; color: var(--fraca); }
.selos { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
.selo {
  font-size: 11px; font-weight: 650; padding: 3px 9px; border-radius: 99px;
  background: var(--tom-lavado); color: var(--tom);
  border: 1px solid color-mix(in srgb, var(--tom) 34%, transparent);
}
.fora { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 9px; }
.base {
  font-size: 12.5px; font-weight: 650; text-decoration: none;
  padding: 7px 13px; border-radius: 9px; color: var(--tinta2);
  background: var(--alta); border: 1px solid var(--borda-forte);
}
.base.livre {
  color: var(--bom); background: color-mix(in srgb, var(--bom) 12%, transparent);
  border-color: color-mix(in srgb, var(--bom) 45%, transparent);
}
.base:active { transform: translateY(1px); }

/* ---- abas embaixo, no alcance do polegar ---- */
nav.abas {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 30;
  display: flex; justify-content: space-around;
  padding: 8px 4px calc(8px + env(safe-area-inset-bottom));
  background: color-mix(in srgb, var(--superficie) 94%, transparent);
  backdrop-filter: blur(14px); border-top: 1px solid var(--borda);
}
nav.abas button {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px;
  min-height: 52px; padding: 6px 2px; border: 0; border-radius: 12px;
  background: none; color: var(--fraca); font: inherit; font-size: 10.5px;
  font-weight: 650; cursor: pointer;
  transition: color .16s, background .16s;
}
nav.abas button .ic { transition: transform .18s cubic-bezier(.2,.9,.3,1.5); }
nav.abas button[aria-selected="true"] { color: var(--tom); background: var(--tom-lavado); }
nav.abas button[aria-selected="true"] .ic { transform: translateY(-1px) scale(1.12); }
nav.abas button:focus-visible { outline: 2px solid var(--tom); outline-offset: -2px; }

@media (prefers-reduced-motion: reduce) {
  nav.abas button .ic, .base { transition: none; }
  nav.abas button[aria-selected="true"] .ic { transform: none; }
}
@media (min-width: 640px) {
  .grandao { font-size: 66px; }
  body { padding-bottom: 40px; }
  nav.abas { position: sticky; top: 0; bottom: auto; border-top: 0;
    border-bottom: 1px solid var(--borda); }
}
"""

MOTOR = """
(function () {
  /* Os ícones são os mesmos do sistema: um lugar só para os traços. */
  document.querySelectorAll("i.ic[data-icone]").forEach(function (alvo) {
    const desenho = Icons.get(alvo.dataset.icone, Number(alvo.dataset.tam) || 20);
    if (desenho) alvo.appendChild(desenho);
  });

  const telas = Array.prototype.slice.call(document.querySelectorAll("[data-tela]"));
  const botoes = Array.prototype.slice.call(document.querySelectorAll("nav.abas button"));

  function abrir(id, empurrar) {
    const existe = telas.some(function (t) { return t.dataset.tela === id; });
    if (!existe) id = telas[0].dataset.tela;
    telas.forEach(function (t) { t.hidden = t.dataset.tela !== id; });
    botoes.forEach(function (b) {
      b.setAttribute("aria-selected", String(b.dataset.ir === id));
    });
    /* Trocar de aba volta ao topo: continuar na altura da aba anterior faz
       a tela nova abrir no meio, e parece que faltou conteúdo. */
    window.scrollTo(0, 0);
    if (empurrar && location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  }

  botoes.forEach(function (b) {
    b.addEventListener("click", function () { abrir(b.dataset.ir, true); });
  });
  window.addEventListener("hashchange", function () {
    abrir(location.hash.replace("#", ""), false);
  });
  abrir(location.hash.replace("#", "") || telas[0].dataset.tela, false);
})();
"""


def montar(db: Database, quando: datetime | None = None,
           dados: dict[str, Any] | None = None) -> str:
    """O miolo do aplicativo: estilo, telas, icones e o motor das abas."""
    quando = quando or datetime.now()
    # `reunir` percorre o banco inteiro; quem ja chamou passa o resultado
    # em vez de pagar a conta duas vezes.
    d = dados if dados is not None else reunir(db)
    telas = {
        "visao": _tela_visao(d),
        "temas": _tela_temas(d),
        "curva": _tela_curva(d),
        "artigos": _tela_artigos(d),
        "sobre": _tela_sobre(d, quando),
    }
    corpo = "".join(
        f'<div data-tela="{ident}" hidden>{telas[ident]}</div>'
        for ident, _, _ in ABAS)
    barra = "".join(
        f'<button type="button" role="tab" data-ir="{ident}" aria-selected="false">'
        f'{_icone(icone, 21)}<span>{_e(rotulo)}</span></button>'
        for ident, rotulo, icone in ABAS)

    icones_js = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
    return (
        "<style>" + ESTILO + "</style>\n"
        '<header><div class="marca">LP</div><div>'
        f'<b>{_e(_curto(d["lab"]["nome"]))}</b>'
        f'<small>{_e(d["lab"]["instituicao"])} · '
        f'{quando.strftime("%d/%m/%Y")}</small>'
        "</div></header>\n"
        f'<nav class="abas" role="tablist">{barra}</nav>\n'
        f"<main>{corpo}</main>\n"
        f"<script>{icones_js}</script>\n"
        f"<script>{MOTOR}</script>\n")


def escrever(db: Database, destino: Path,
             quando: datetime | None = None) -> dict[str, Any]:
    """Grava o aplicativo como pagina completa, pronta para mandar."""
    quando = quando or datetime.now()
    dados = reunir(db)
    miolo = montar(db, quando, dados)
    pagina = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n'
              '<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1,'
              ' viewport-fit=cover">\n'
              '<meta name="theme-color" content="#05070d">\n'
              '<meta name="apple-mobile-web-app-capable" content="yes">\n'
              "<title>Panorama do LAPE</title>\n</head>\n<body>\n"
              + miolo + "</body>\n</html>\n")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    return {"arquivo": str(destino), "bytes": len(pagina.encode("utf-8")),
            "artigos": dados["total"]}
