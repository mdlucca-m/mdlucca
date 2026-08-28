"""Um instantaneo do painel: uma pagina so, sem servidor, para abrir longe.

O painel vive de um servidor Python e de um banco SQLite. Quem esta longe
da maquina do laboratorio -- num celular, na casa de alguem, numa banca --
nao tem nem um nem outro. Este modulo escreve TUDO numa pagina unica: o
estilo, os icones, a biblioteca de graficos, a tela e os dados ja
calculados, gravados dentro do arquivo.

O que ele NAO e, e a pagina diz isso em cima:

  - nao e ao vivo. E o retrato de um instante, com a data escrita nele;
  - nao grava nada. Bater ponto, marcar variavel, importar da PubMed --
    tudo isso precisa do servidor, e aqui os botoes explicam em vez de
    falhar;
  - nao substitui o sistema. Serve para olhar e mostrar.

A alternativa seria mandar prints de tela. Prints nao tem os graficos
interativos, nao tem a tabela por tras de cada um, e envelhecem sem
avisar -- pelo menos aqui a data esta no cabecalho.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from . import analise, config, versao
from .db import Database

TEMPLATES = Path(__file__).resolve().parent / "templates"


def _dados(db: Database) -> dict[str, Any]:
    """O mesmo conteudo que a rota do painel serve, calculado aqui."""
    from . import ponto, variaveis
    from .api import _artigos_do_panorama

    panorama = analise.panorama(db)
    return {
        "panorama": panorama,
        "incidencia": analise.incidencia(db, panorama["janela"]["anos"]),
        "prevalencia": analise.prevalencia(db, panorama["janela"]["anos"]),
        "triangulacao": analise.triangulacao(db),
        "projetos": analise.projetos(db),
        "sintese": analise.sintese(db, panorama),
        "lacunas": analise.lacunas(db, panorama),
        "artigos": _artigos_do_panorama(db),
        "linhas": db.dicts(
            "SELECT rl.code, rl.name, rl.description, rl.keywords,"
            "       (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id) AS n"
            "  FROM research_lines rl ORDER BY n DESC"),
        "laboratorio": {
            "nome": config.LAB_NAME, "instituicao": config.LAB_INSTITUTION,
            "site": getattr(config, "LAB_SITE", None),
            "integrantes": int(db.scalar("SELECT COUNT(*) FROM members") or 0),
            "projetos": int(db.scalar("SELECT COUNT(*) FROM projects") or 0),
            "eventos": int(db.scalar("SELECT COUNT(*) FROM events") or 0),
        },
        "vocabulario": variaveis.lista(db),
        # Quem abre um instantaneo esta olhando, nao mandando. O papel de
        # leitura esconde os botoes que gravam em vez de deixa-los falhar.
        "usuario": {"papel": "leitura", "nome": None},
        "producao": {"pesquisadores": [], "artigos_de_base": 0, "paises_marcados": 0},
        "equipe": {
            "dias": 30,
            "pessoas": ponto.por_pessoa(db, dias=30),
            "agora": ponto.agora(db),
            "serie": ponto.serie(db, None, dias=30),
            "resumo": ponto.resumo(db, None),
            "producao": ponto.producao_no_periodo(db, None, dias=30),
        },
    }


def _ler(nome: str) -> str:
    return (TEMPLATES / nome).read_text(encoding="utf-8")


def _mundo() -> str:
    arquivo = config.GEO_DIR / "mundo.json"
    return arquivo.read_text(encoding="utf-8") if arquivo.exists() else '{"paises":[]}'


AVISO = """
<div class="instantaneo-aviso">
  <b>Isto é um instantâneo.</b> Retrato do painel em {quando} — não está ao
  vivo e não grava nada. Bater ponto, marcar variável ou importar das bases
  pede o sistema no computador do laboratório. Tudo o que é <i>olhar</i>
  funciona aqui: as abas, os gráficos, as tabelas por trás deles e os links
  para as bases.
</div>
"""

# A ponte entre a tela, que pede dados por HTTP, e o arquivo, que os tem
# dentro. Responder o GET conhecido e recusar o resto COM MOTIVO e o que
# separa "não dá para gravar aqui" de um botão que não faz nada.
PONTE = """
<style>
/* O selo "ao vivo" some: num retrato ele só poderia mentir. O aviso do
   topo já diz o que esta página é. */
.pulso { display: none !important; }
</style>
<script>
(function () {
  const EMBUTIDO = window.__LAPE__;
  window.fetch = function (url) {
    const caminho = String(url).split("?")[0];
    if (caminho === "/api/geo/mundo.json") {
      return Promise.resolve({ ok: true, json: function () {
        return Promise.resolve(EMBUTIDO.mundo); } });
    }
    return Promise.reject(new Error(
      "Este é um instantâneo: só o sistema no computador do laboratório grava."));
  };
})();
</script>
"""


# O que so existe com o servidor atras, e que num arquivo solto viraria
# porta que da na parede.
LINKS_MORTOS = (
    ('  nav.appendChild(el("div", { class: "grupo", text: "Ir para" }));\n'
     '  [["Painel de indicadores", "/painel", "barras"],\n'
     '   ["Triagem de revisão", "/triagem", "filtro"],\n'
     '   ["Área do integrante", "/app", "pessoa"]].forEach(function (x) {',
     '  [].forEach(function (x) {'),
    ('    [seloAoVivo(),\n'
     '     el("a", { class: "botao-destino", href: "/painel", text: "Indicadores" })]));',
     '    []));'),
)


def montar(db: Database, quando: datetime | None = None) -> str:
    """O miolo da pagina -- estilo, scripts e dados, sem as tags externas."""
    quando = quando or datetime.now()
    dados = _dados(db)
    marca = versao.resumo()
    corpo = _ler("panorama.html")

    # A pagina do painel e um documento inteiro; aqui interessa o miolo,
    # para ele caber tanto num arquivo solto quanto num Artifact.
    inicio = corpo.index("<style>")
    fim = corpo.index("</body>")
    miolo = corpo[inicio:fim]

    miolo = miolo.replace("__BASE_CSS__", _ler("theme.css"))
    miolo = miolo.replace("__ICONS_JS__", _ler("icons.js"))
    miolo = miolo.replace("__CHARTS_JS__", _ler("charts.js"))
    # O marcador da tela sai do miolo: a versao remendada dela entra
    # depois, ja com os dados dentro. Deixar os dois faria o original
    # rodar primeiro e estourar em `__PANORAMA_JS__ is not defined`.
    miolo = miolo.replace("__PANORAMA_JS__", "")

    tela = _ler("panorama.js")
    # A tela pede o painel ao servidor no arranque e a cada evento. Aqui
    # o painel ja esta na pagina: trocar a busca pela constante evita a
    # tela abrir vazia e depois nao encher nunca.
    tela = tela.replace('const dados = await api("/api/panorama");',
                        'const dados = window.__LAPE__.painel;')
    tela = tela.replace('api("/api/ponto/equipe").then(function (dados) {',
                        'Promise.resolve(window.__LAPE__.painel.equipe)'
                        '.then(function (dados) {')
    # Sem servidor nao ha fluxo de eventos: deixar ligado so acenderia um
    # selo "ao vivo" mentindo, e tentaria reconectar para sempre.
    tela = tela.replace("let aoVivo = true;", "let aoVivo = false;")
    tela = tela.replace("function ligarAoVivo() {",
                        "function ligarAoVivo() {\n  return;")

    # Links para outras telas do sistema (painel, triagem, area do
    # integrante) nao existem num arquivo solto. Deixa-los seria oferecer
    # portas que dao na parede -- pior que nao oferecer porta nenhuma.
    for trecho, troca in LINKS_MORTOS:
        tela = tela.replace(trecho, troca)

    dentro = json.dumps({"painel": dados, "mundo": json.loads(_mundo())},
                        ensure_ascii=False, default=str)
    cabeca = AVISO.format(quando=quando.strftime("%d/%m/%Y às %H:%M"))
    return (miolo
            + "<script>window.__LAPE__ = " + dentro + ";</script>\n"
            + PONTE
            + "<script>\n" + tela + "\n</script>\n"
            + '<div class="marca-versao">instantâneo · '
            + quando.strftime("%d/%m/%Y %H:%M") + " · " + marca + "</div>\n"
            ).replace('<div class="casca">', cabeca + '<div class="casca">')


def escrever(db: Database, destino: Path,
             quando: datetime | None = None) -> dict[str, Any]:
    """Grava o instantaneo como pagina completa, para abrir de um clique."""
    miolo = montar(db, quando)
    pagina = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n'
              '<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
              "<title>Panorama do LAPE — instantâneo</title>\n</head>\n<body>\n"
              + miolo + "\n</body>\n</html>\n")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    return {"arquivo": str(destino), "bytes": len(pagina.encode("utf-8"))}
