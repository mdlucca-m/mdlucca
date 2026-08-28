"""O fluxograma PRISMA 2020, desenhado a partir do banco.

Toda revisao sistematica publica esse desenho, e quase todo mundo o faz a
mao num editor de imagem -- copiando numeros de uma planilha. E dai que
vem o erro classico: o fluxograma nao fecha com a tabela, porque foram
digitados em momentos diferentes.

Aqui ele e desenhado dos mesmos numeros que o painel mostra, na hora do
clique. Se um numero mudar, o desenho muda junto. Nao ha o que conferir.

SVG e nao PNG de proposito: entra no Word e no LaTeX sem serrilhar, e
continua sendo texto -- da para abrir e corrigir uma palavra sem
redesenhar nada.
"""
from __future__ import annotations

from typing import Any

# A largura de uma coluna e a distancia entre caixas. Tudo o mais e
# derivado disto, para o desenho continuar equilibrado quando um texto
# crescer.
LARGURA = 300
ALTURA_CAIXA = 78
ESPACO = 34
MARGEM = 26
COLUNA_LATERAL = 300
VAO = 58                 # entre a coluna principal e a lateral


def _quebrar(texto: str, largura: int = 40) -> list[str]:
    """Quebra o texto em linhas curtas, sem cortar palavra ao meio."""
    linhas: list[str] = []
    atual = ""
    for palavra in str(texto).split():
        if len(atual) + len(palavra) + 1 > largura and atual:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    if atual:
        linhas.append(atual)
    return linhas


def _escapar(texto: Any) -> str:
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _caixa(x: int, y: int, largura: int, titulo: str, valor: Any,
           detalhe: str = "", tom: str = "normal") -> tuple[str, int]:
    """Uma caixa do fluxograma. Devolve (svg, altura usada).

    Titulo em cima, contagem embaixo -- e nao lado a lado. Encostados na
    mesma linha, um titulo longo passa por cima do "(n = ...)", e o
    desenho sai com os numeros ilegiveis: foi o que aconteceu na primeira
    versao, e nao ha largura fixa que resolva, porque o rotulo muda de
    tamanho conforme a revisao.
    """
    por_linha = max(18, int(largura / 6.9))
    linhas_titulo = _quebrar(titulo, por_linha)
    linhas_detalhe = _quebrar(detalhe, int(largura / 5.9)) if detalhe else []
    altura = (16 + len(linhas_titulo) * 16 + (26 if valor is not None else 0)
              + len(linhas_detalhe) * 15 + 14)
    preenchimento = {"normal": "#ffffff", "destaque": "#eaf4fa",
                     "lateral": "#f7f7f5"}[tom]
    borda = {"normal": "#333333", "destaque": "#12799f", "lateral": "#8a8a85"}[tom]
    partes = [
        f'<rect x="{x}" y="{y}" width="{largura}" height="{altura}" rx="3" '
        f'fill="{preenchimento}" stroke="{borda}" stroke-width="1.4"/>',
    ]
    linha_y = y + 22
    for texto in linhas_titulo:
        partes.append(
            f'<text x="{x + 14}" y="{linha_y}" font-size="12.5" font-weight="700" '
            f'fill="#1a1a1a">{_escapar(texto)}</text>')
        linha_y += 16
    if valor is not None:
        linha_y += 6
        partes.append(
            f'<text x="{x + 14}" y="{linha_y}" font-size="17" font-weight="800" '
            f'fill="#12799f">(n = {_escapar(valor)})</text>')
        linha_y += 18
    for texto in linhas_detalhe:
        partes.append(
            f'<text x="{x + 14}" y="{linha_y}" font-size="11.5" '
            f'fill="#4a4a4a">{_escapar(texto)}</text>')
        linha_y += 15
    return "\n".join(partes), altura


def _seta(x1: int, y1: int, x2: int, y2: int) -> str:
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333333" '
            f'stroke-width="1.4" marker-end="url(#ponta)"/>')


def _fase(x: int, y: int, altura: int, rotulo: str) -> str:
    """A faixa vertical da esquerda: Identificacao, Triagem, Incluidos."""
    meio = y + altura / 2
    return (
        f'<rect x="{x}" y="{y}" width="30" height="{altura}" rx="3" fill="#12799f"/>'
        f'<text x="{x + 15}" y="{meio}" font-size="12" font-weight="700" fill="#ffffff" '
        f'text-anchor="middle" transform="rotate(-90 {x + 15} {meio})">'
        f'{_escapar(rotulo)}</text>')


def desenhar(dados: dict[str, Any], titulo: str = "") -> str:
    """O fluxograma inteiro, em SVG, a partir do que `revisao.prisma` devolve."""
    x_fase = MARGEM
    x = MARGEM + 30 + 16
    x_lateral = x + LARGURA + VAO
    y = MARGEM + (34 if titulo else 0)

    corpo: list[str] = []
    marcos: list[tuple[str, int, int]] = []   # (fase, y inicial, y final)

    def empilhar(titulo_caixa, valor, detalhe="", tom="normal"):
        nonlocal y
        svg, altura = _caixa(x, y, LARGURA, titulo_caixa, valor, detalhe, tom)
        corpo.append(svg)
        topo, base = y, y + altura
        y = base + ESPACO
        return topo, base

    def lateral(y_alvo, titulo_caixa, valor, detalhe=""):
        svg, altura = _caixa(x_lateral, y_alvo, COLUNA_LATERAL, titulo_caixa,
                             valor, detalhe, "lateral")
        corpo.append(svg)
        return altura

    # --- Identificacao ---
    inicio_ident = y
    por_base = ", ".join(
        f"{b['base']}: {b['n']}" for b in (dados.get("por_base") or [])[:6])
    _, base_ident = empilhar(
        "Registros identificados nas bases", dados.get("identificados", 0),
        por_base or "sem busca registrada", "destaque")
    fim_ident = base_ident
    marcos.append(("Identificação", inicio_ident, fim_ident))

    # a remocao de duplicados sai para o lado, como no PRISMA 2020
    if dados.get("duplicados"):
        altura_lateral = lateral(inicio_ident, "Registros removidos antes da triagem",
                                 dados["duplicados"], "duplicados entre bases")
        topo_ident_lateral = inicio_ident + altura_lateral // 2
        corpo.append(_seta(x + LARGURA, topo_ident_lateral, x_lateral - 4, topo_ident_lateral))

    corpo.append(_seta(x + LARGURA // 2, base_ident, x + LARGURA // 2, y - 6))

    # --- Triagem ---
    inicio_triagem = y
    topo_tri, base_tri = empilhar("Registros triados (título e resumo)",
                                  dados.get("triados", 0))
    motivos = "; ".join(f"{m['motivo']}: {m['n']}" for m in (dados.get("motivos") or [])[:6])
    if dados.get("excluidos_triagem"):
        altura_lat = lateral(topo_tri, "Registros excluídos na triagem",
                             dados["excluidos_triagem"], motivos or "sem motivo registrado")
        meio = topo_tri + altura_lat // 2
        corpo.append(_seta(x + LARGURA, meio, x_lateral - 4, meio))
    corpo.append(_seta(x + LARGURA // 2, base_tri, x + LARGURA // 2, y - 6))

    topo_txt, base_txt = empilhar("Textos completos avaliados",
                                  dados.get("texto_completo", 0))
    if dados.get("excluidos_texto"):
        altura_lat = lateral(topo_txt, "Textos completos excluídos", dados["excluidos_texto"],
                             "com motivo registrado")
        meio = topo_txt + altura_lat // 2
        corpo.append(_seta(x + LARGURA, meio, x_lateral - 4, meio))
    marcos.append(("Triagem", inicio_triagem, base_txt))
    corpo.append(_seta(x + LARGURA // 2, base_txt, x + LARGURA // 2, y - 6))

    # --- Incluidos ---
    inicio_inc = y
    _, base_inc = empilhar("Estudos incluídos na síntese",
                           dados.get("incluidos", 0), "", "destaque")
    marcos.append(("Incluídos", inicio_inc, base_inc))

    for rotulo, topo, base in marcos:
        corpo.append(_fase(x_fase, topo, base - topo, rotulo))

    largura_total = x_lateral + COLUNA_LATERAL + MARGEM
    altura_total = base_inc + MARGEM + 20
    cabecalho = ""
    if titulo:
        cabecalho = (f'<text x="{x_fase}" y="{MARGEM + 6}" font-size="15" '
                     f'font-weight="800" fill="#1a1a1a">{_escapar(titulo)}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura_total}" \
height="{altura_total}" viewBox="0 0 {largura_total} {altura_total}" \
font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">
<defs><marker id="ponta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" \
markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#333333"/></marker></defs>
<rect width="100%" height="100%" fill="#ffffff"/>
{cabecalho}
{chr(10).join(corpo)}
<text x="{x_fase}" y="{altura_total - 10}" font-size="10.5" fill="#6a6a6a">\
Fluxograma PRISMA 2020 — gerado pelo LAPE a partir do banco da revisão.</text>
</svg>'''


# ----------------------------------------------------------------------
# Semaforo de risco de vies
# ----------------------------------------------------------------------
# A figura que acompanha toda revisao com avaliacao de qualidade: estudos
# nas linhas, dominios nas colunas, um sinal por celula.
#
# O sinal nao e so a cor. Cada julgamento leva o seu simbolo dentro do
# circulo (+ - ? !), e a legenda traz os dois juntos. Uma figura em que a
# cor e a unica informacao vira uma coluna de circulos cinzentos quando
# impressa em preto e branco -- que e como metade das revistas ainda
# publica -- e nao diz nada a quem nao distingue verde de vermelho.
TONS = {
    "good":     ("#1a8a4a", "+"),
    "warning":  ("#e0a300", "?"),
    "serious":  ("#e06c2a", "!"),
    "critical": ("#c93a3a", "\u2212"),
    "neutro":   ("#b8b8b4", ""),
}
CELULA = 42
ROTULO = 250
CABECALHO = 130


def semaforo(dados: dict[str, Any], titulo: str = "") -> str:
    """O semaforo inteiro, em SVG, a partir do que `extracao.semaforo` devolve."""
    dominios = dados.get("dominios") or []
    estudos = dados.get("estudos") or []
    if not dominios:
        return _vazio("Nenhum domínio de risco de viés configurado.")
    if not estudos:
        return _vazio("Nenhum estudo incluído ainda — o semáforo aparece quando houver.")

    largura_grade = len(dominios) * CELULA
    julgamentos = list(dados.get("julgamentos") or [])
    largura = ROTULO + largura_grade + MARGEM * 2 + 10
    # Quantos itens de legenda cabem por linha na largura que a grade
    # determinou. Com um numero fixo, o ultimo item saia para fora do
    # desenho -- e um item de legenda que nao aparece e uma cor sem
    # significado no papel de quem le.
    LARGURA_ITEM = 176
    por_linha = max(1, (largura - MARGEM * 2) // LARGURA_ITEM)
    linhas_legenda = -(-len(julgamentos) // por_linha) if julgamentos else 0
    legenda_alt = 30 + 22 * linhas_legenda
    altura = (CABECALHO + len(estudos) * CELULA + legenda_alt + MARGEM * 2
              + (26 if titulo else 0))
    x0 = MARGEM + ROTULO
    y0 = MARGEM + (26 if titulo else 0) + CABECALHO

    partes: list[str] = []
    if titulo:
        partes.append(f'<text x="{MARGEM}" y="{MARGEM + 14}" font-size="14" '
                      f'font-weight="800" fill="#1a1a1a">{_escapar(titulo)}</text>')

    # cabecalho: o nome do dominio na vertical, senao nao cabe
    for i, dominio in enumerate(dominios):
        cx = x0 + i * CELULA + CELULA / 2
        rotulo = _encurtar(dominio["label"], 26)
        partes.append(
            f'<text x="{cx}" y="{y0 - 10}" font-size="11.5" fill="#3a3a3a" '
            f'text-anchor="start" transform="rotate(-55 {cx} {y0 - 10})">'
            f'{_escapar(rotulo)}</text>')

    for j, estudo in enumerate(estudos):
        cy = y0 + j * CELULA + CELULA / 2
        if j % 2 == 0:
            partes.append(
                f'<rect x="{MARGEM}" y="{y0 + j * CELULA}" '
                f'width="{ROTULO + largura_grade}" height="{CELULA}" fill="#f5f6f7"/>')
        partes.append(
            f'<text x="{MARGEM + ROTULO - 14}" y="{cy + 4}" font-size="12.5" '
            f'text-anchor="end" fill="#1a1a1a">'
            f'{_escapar(_encurtar(estudo["estudo"], 34))}</text>')
        for i, celula in enumerate(estudo["celulas"]):
            cx = x0 + i * CELULA + CELULA / 2
            cor, simbolo = TONS.get(celula.get("tom") or "neutro", TONS["neutro"])
            partes.append(
                f'<circle cx="{cx}" cy="{cy}" r="13" fill="{cor}" '
                f'stroke="#ffffff" stroke-width="2"><title>'
                f'{_escapar(celula.get("rotulo") or "Sem julgamento")}</title></circle>')
            if simbolo:
                partes.append(
                    f'<text x="{cx}" y="{cy + 5.5}" font-size="15" font-weight="800" '
                    f'text-anchor="middle" fill="#ffffff">{simbolo}</text>')

    # legenda: simbolo e palavra, nunca so a cor
    y_legenda = y0 + len(estudos) * CELULA + 28
    for k, julgamento in enumerate(julgamentos):
        col, lin = k % por_linha, k // por_linha
        lx = MARGEM + col * LARGURA_ITEM
        ly = y_legenda + lin * 22
        cor, simbolo = TONS.get(julgamento["tom"], TONS["neutro"])
        partes.append(f'<circle cx="{lx + 9}" cy="{ly - 4}" r="9" fill="{cor}"/>')
        if simbolo:
            partes.append(
                f'<text x="{lx + 9}" y="{ly}" font-size="11" font-weight="800" '
                f'text-anchor="middle" fill="#ffffff">{simbolo}</text>')
        partes.append(f'<text x="{lx + 24}" y="{ly}" font-size="11.5" fill="#3a3a3a">'
                      f'{_escapar(julgamento["rotulo"])}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" \
height="{altura}" viewBox="0 0 {largura} {altura}" \
font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">
<rect width="100%" height="100%" fill="#ffffff"/>
{chr(10).join(partes)}
<text x="{MARGEM}" y="{altura - 8}" font-size="10" fill="#6a6a6a">\
{_escapar(dados.get("ferramenta") or "")} — gerado pelo LAPE.</text>
</svg>'''


def _encurtar(texto: Any, n: int) -> str:
    t = str(texto or "")
    return t if len(t) <= n else t[:n - 1] + "\u2026"


def _vazio(mensagem: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="520" height="90" '
            f'viewBox="0 0 520 90" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">'
            f'<rect width="100%" height="100%" fill="#ffffff"/>'
            f'<text x="20" y="50" font-size="13" fill="#6a6a6a">{_escapar(mensagem)}</text>'
            f'</svg>')
