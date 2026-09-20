"""Lê a ficha que o atleta mandou pelo WhatsApp.

A página de cadastro (docs/index.html) monta uma mensagem numerada. Aqui ela
volta a ser uma ficha. O atleta responde como dá — às vezes devolve a lista
inteira com o rótulo, às vezes só "1. João" — e as duas formas têm de entrar.

Regra que vale para o arquivo inteiro: **o que não deu para entender fica em
branco e é reportado.** Chutar um valor aqui significa um atleta com a estatura
errada entrando no cálculo de salto e de carga, e ninguém percebendo.
"""

import re
import unicodedata

# a mesma ordem da página de cadastro; o número é o que liga os dois lados
CAMPOS = [
    (1, "nome", "Nome completo", "txt", True),
    (2, "apelido", "Como prefere ser chamado", "txt", False),
    (3, "nasc", "Data de nascimento", "data", True),
    (4, "posicao", "Posição", "opc", True),
    (5, "camisa", "Número da camisa", "int", False),
    (6, "telefone", "Telefone (WhatsApp)", "txt", False),
    (7, "estatura", "Estatura em cm", "num", True),
    (8, "massa", "Massa corporal em kg", "num", True),
    (9, "anos_pratica", "Anos de prática no voleibol", "int", True),
    (10, "dominancia", "Mão dominante", "opc", False),
    (11, "perna_impulsao", "Perna de impulsão", "opc", False),
    (12, "emergencia", "Contato de emergência", "txt", True),
    (13, "lesoes", "Lesões anteriores ou limitações", "txt", False),
    (14, "obs", "Algo mais que a comissão deva saber", "txt", False),
    (15, "escolaridade", "Escolaridade", "opc", False),
]

OPCOES = {
    "posicao": ["Levantador", "Oposto", "Ponteiro (Ponta)", "Central", "Líbero"],
    "dominancia": ["Destro", "Canhoto", "Ambidestro"],
    "perna_impulsao": ["Esquerda", "Direita", "Simétrica"],
    "escolaridade": ["Fundamental", "Médio completo", "Superior em andamento",
                     "Superior completo", "Pós-graduação"],
}

_NUMERADA = re.compile(r"^\s*(\d{1,2})\s*[.)\]\-–—:]")


def sem_acento(s):
    base = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def _limpar(bruto, rotulo):
    """Tira o número e, se sobrou, o rótulo."""
    t = re.sub(r"^\s*\d{1,2}\s*[.)\]\-–—:]?\s*", "", str(bruto or "").strip())
    # o separador que a página usa é o travessão; o último vale, porque o
    # próprio rótulo pode conter um
    i = t.rfind("—")
    if i >= 0:
        return t[i + 1:].strip()
    # sem travessão: "Nome completo: João" → "João"
    prim = sem_acento(rotulo).replace("(", " ").split()[0]
    if prim and sem_acento(t).startswith(prim):
        m = re.match(r"^[^:\-–]{0,70}[:\-–]\s*", t)
        return t[m.end():].strip() if m else ""
    return t.strip()


def separar(texto):
    """Uma colada pode trazer vários atletas. Cada linha que recomeça no item 1
    começa uma ficha nova."""
    blocos, atual = [], None
    for linha in str(texto or "").splitlines():
        if re.match(r"^\s*1\s*[.)\]\-–—:]", linha):
            atual = []
            blocos.append(atual)
        if atual is not None:
            atual.append(linha)
    return ["\n".join(b) for b in blocos if b]


def _data(s):
    """dd/mm/aaaa (ou com - e .) → aaaa-mm-dd."""
    m = re.search(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", str(s or ""))
    if not m:
        t = str(s or "").strip()
        return t if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t) else ""
    d, mes, a = m.groups()
    if len(a) == 2:
        a = ("19" if int(a) > 40 else "20") + a
    return f"{a}-{int(mes):02d}-{int(d):02d}"


def _numero(s):
    t = str(s or "").strip().replace(",", ".")
    m = re.search(r"-?\d+(\.\d+)?", t)
    return float(m.group(0)) if m else None


def _variantes(opcao):
    """Os nomes pelos quais uma opção pode ser escrita.

    "Ponteiro (Ponta)" é UMA posição com DOIS nomes de quadra, e o atleta
    escreve o que ele usa. Enquanto o que está entre parênteses não contava
    como nome próprio, "ponta" não casava com nada — e é o mais provável de vir.
    """
    base = sem_acento(opcao).strip()
    fora = [base, re.sub(r"\(.*?\)", "", base).strip()]
    dentro = re.search(r"\(([^)]*)\)", base)
    if dentro:
        fora.append(dentro.group(1).strip())
    return [x for x in fora if x]


def _casar(valor, opcoes):
    """"libero", "PONTEIRO", "ponta" caem todos na opção certa."""
    v = sem_acento(valor).strip()
    if not v:
        return None
    for o in opcoes:
        if v in _variantes(o):
            return o
    for o in opcoes:
        for s in _variantes(o):
            if s.startswith(v) or v.startswith(s.split()[0]):
                return o
    for o in opcoes:
        for s in _variantes(o):
            if v in s or s in v:
                return o
    return None


def ler(texto):
    """Uma ficha. Devolve {dados, faltam, nao_lidos, vazio}."""
    cru = {}
    for linha in str(texto or "").splitlines():
        m = _NUMERADA.match(linha)
        if not m:
            continue
        campo = next((c for c in CAMPOS if c[0] == int(m.group(1))), None)
        if campo and campo[1] not in cru:
            cru[campo[1]] = _limpar(linha, campo[2])

    dados, nao_lidos = {}, []
    for _n, chave, rotulo, tipo, _obr in CAMPOS:
        v = (cru.get(chave) or "").strip()
        if not v:
            dados[chave] = None if tipo in ("num", "int") else ""
            continue
        if tipo == "num":
            x = _numero(v)
            dados[chave] = x
            if x is None:
                nao_lidos.append(f"{rotulo} («{v}»)")
        elif tipo == "int":
            x = _numero(v)
            dados[chave] = int(x) if x is not None else None
            if x is None:
                nao_lidos.append(f"{rotulo} («{v}»)")
        elif tipo == "data":
            x = _data(v)
            dados[chave] = x
            if not x:
                nao_lidos.append(f"{rotulo} («{v}»)")
        elif tipo == "opc":
            x = _casar(v, OPCOES[chave])
            dados[chave] = x or ""
            if not x:
                nao_lidos.append(f"{rotulo} («{v}»)")
        else:
            dados[chave] = v

    faltam = [rot for _n, ch, rot, _t, obr in CAMPOS
              if obr and not str(dados.get(ch) or "").strip()]
    return {"dados": dados, "faltam": faltam, "nao_lidos": nao_lidos,
            "vazio": not any(str(v or "").strip() for v in cru.values())}


def ler_varias(texto):
    """Tudo que foi colado, separado em fichas. Conversa solta some."""
    blocos = separar(texto) or [texto]
    return [r for r in (ler(b) for b in blocos) if not r["vazio"]]
