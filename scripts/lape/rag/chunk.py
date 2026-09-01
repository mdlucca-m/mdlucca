"""Extracao de texto e divisao em trechos.

A extracao cobre os formatos que aparecem numa tese: pdf, docx, markdown,
html e texto puro. O docx e lido direto do XML, sem dependencia externa; o
pdf usa pypdf quando disponivel e avisa com clareza quando nao esta.

A divisao respeita a estrutura do texto. O algoritmo quebra primeiro em
paragrafos, agrupa paragrafos ate o limite de caracteres e so parte uma
frase quando um paragrafo isolado ja excede o limite. Cada trecho carrega a
secao a que pertence, o que permite citar "Metodo, paragrafo 3" em vez de
"trecho 47".
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from . import config

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Titulos de secao reconheciveis num texto academico, em portugues e ingles.
SECTION_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\s+)?("
    r"resumo|abstract|introdu[cç][aã]o|introduction|referencial|fundamenta[cç][aã]o|"
    r"revis[aã]o(?: de literatura)?|m[eé]todos?|metodologia|methods?|materiais e m[eé]todos|"
    r"resultados?|results?|discuss[aã]o|discussion|conclus[aã]o|conclusions?|"
    r"considera[cç][oõ]es finais|refer[eê]ncias|references|ap[eê]ndice|anexo|"
    r"limita[cç][oõ]es|agradecimentos)\b.*$",
    re.IGNORECASE,
)


class ExtractionError(RuntimeError):
    """O arquivo existe mas o texto nao pode ser lido."""


@dataclass
class Chunk:
    ordinal: int
    text: str
    section: str | None = None
    char_start: int = 0
    char_end: int = 0
    n_tokens: int = 0


@dataclass
class Document:
    uri: str
    text: str
    kind: str = "externo"
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    source: str | None = None
    doi: str | None = None
    lang: str | None = None
    ref_table: str | None = None
    ref_id: int | None = None
    meta: dict = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- extracao
def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("­", "")          # hifen de silabacao invisivel
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Palavra partida no fim da linha, tipica de pdf de duas colunas.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    return text.strip()


def from_docx(path: Path) -> str:
    """Le o texto de um .docx direto do XML, sem biblioteca externa."""
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ExtractionError(f"{path.name}: docx ilegivel ({exc})") from exc
    root = ElementTree.fromstring(xml)
    linhas: list[str] = []
    for par in root.iter(f"{W}p"):
        pedacos = [no.text or "" for no in par.iter(f"{W}t")]
        texto = "".join(pedacos).strip()
        if not texto:
            continue
        estilo = par.find(f"{W}pPr/{W}pStyle")
        nome = estilo.get(f"{W}val", "") if estilo is not None else ""
        if nome.lower().startswith("heading") or nome.lower().startswith("titulo"):
            linhas.append("\n" + texto + "\n")
        else:
            linhas.append(texto)
    return _norm("\n\n".join(linhas))


def from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:                      # pragma: no cover
        raise ExtractionError(
            f"{path.name}: leitura de pdf exige o pacote pypdf "
            "(pip install pypdf)"
        ) from exc
    try:
        leitor = PdfReader(str(path))
        paginas = [pagina.extract_text() or "" for pagina in leitor.pages]
    except Exception as exc:                        # pragma: no cover
        raise ExtractionError(f"{path.name}: pdf ilegivel ({exc})") from exc
    texto = _norm("\n\n".join(paginas))
    if len(texto) < 200:
        raise ExtractionError(
            f"{path.name}: o pdf devolveu quase nenhum texto; "
            "provavelmente e digitalizado e precisa de OCR"
        )
    return texto


def from_html(path_or_text: Path | str) -> str:
    from html.parser import HTMLParser

    class Coletor(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.partes: list[str] = []
            self.pular = 0

        def handle_starttag(self, tag, attrs):
            if tag in {"script", "style"}:
                self.pular += 1
            elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"}:
                self.partes.append("\n")

        def handle_endtag(self, tag):
            if tag in {"script", "style"} and self.pular:
                self.pular -= 1

        def handle_data(self, data):
            if not self.pular:
                self.partes.append(data)

    bruto = (path_or_text.read_text(encoding="utf-8", errors="replace")
             if isinstance(path_or_text, Path) else path_or_text)
    coletor = Coletor()
    coletor.feed(bruto)
    return _norm("".join(coletor.partes))


def from_path(path: Path) -> str:
    """Despacha para o extrator do formato."""
    suf = path.suffix.lower()
    if suf == ".docx":
        return from_docx(path)
    if suf == ".pdf":
        return from_pdf(path)
    if suf in {".html", ".htm"}:
        return from_html(path)
    if suf in {".txt", ".md", ".markdown"}:
        return _norm(path.read_text(encoding="utf-8", errors="replace"))
    raise ExtractionError(f"{path.name}: formato {suf or 'sem extensao'} nao suportado")


# ---------------------------------------------------------------- divisao
def _estimar_tokens(texto: str) -> int:
    """Estimativa barata: portugues academico gira em torno de 4 caracteres
    por token. Serve para orcamento de contexto, nao para faturamento."""
    return max(1, len(texto) // 4)


def _partir_paragrafo(texto: str, limite: int) -> list[str]:
    """Quebra um paragrafo longo em frases, sem estourar o limite."""
    frases = re.split(r"(?<=[.!?;])\s+", texto)
    saida: list[str] = []
    atual = ""
    for frase in frases:
        if len(atual) + len(frase) + 1 <= limite or not atual:
            atual = f"{atual} {frase}".strip()
        else:
            saida.append(atual)
            atual = frase
        while len(atual) > limite:                  # frase unica gigante
            saida.append(atual[:limite])
            atual = atual[limite:]
    if atual:
        saida.append(atual)
    return saida


def split(texto: str,
          limite: int = config.CHUNK_CHARS,
          sobreposicao: int = config.CHUNK_OVERLAP,
          minimo: int = config.CHUNK_MIN) -> list[Chunk]:
    """Divide o texto em trechos com sobreposicao e rotulo de secao."""
    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks: list[Chunk] = []
    buffer: list[str] = []
    secao: str | None = None
    secao_do_buffer: str | None = None
    cursor = 0
    inicio = 0

    def fechar(fim: int) -> None:
        nonlocal buffer, inicio
        if not buffer:
            return
        corpo = "\n\n".join(buffer).strip()
        if len(corpo) >= minimo or not chunks:
            chunks.append(Chunk(ordinal=len(chunks), text=corpo,
                                section=secao_do_buffer, char_start=inicio,
                                char_end=fim, n_tokens=_estimar_tokens(corpo)))
        elif chunks:                                 # cauda curta: gruda no anterior
            anterior = chunks[-1]
            anterior.text = f"{anterior.text}\n\n{corpo}"
            anterior.char_end = fim
            anterior.n_tokens = _estimar_tokens(anterior.text)
        buffer = []

    for par in paragrafos:
        pos = texto.find(par, cursor)
        if pos < 0:
            pos = cursor
        cursor = pos + len(par)

        cabecalho = SECTION_RE.match(par) if len(par) < 120 else None
        if cabecalho:
            fechar(pos)
            secao = par.strip()
            secao_do_buffer = secao
            inicio = pos
            continue

        pedacos = [par] if len(par) <= limite else _partir_paragrafo(par, limite)
        for pedaco in pedacos:
            atual = sum(len(b) + 2 for b in buffer)
            if buffer and atual + len(pedaco) > limite:
                fechar(pos)
                if sobreposicao > 0 and chunks:
                    cauda = chunks[-1].text[-sobreposicao:]
                    corte = cauda.find(" ")
                    buffer = [cauda[corte + 1:] if corte >= 0 else cauda]
                inicio = pos
                secao_do_buffer = secao
            if not buffer:
                secao_do_buffer = secao
                inicio = pos
            buffer.append(pedaco)
    fechar(len(texto))
    for i, c in enumerate(chunks):
        c.ordinal = i
    return chunks


def load(path: Path, kind: str = "externo", **meta) -> Document:
    """Le um arquivo e devolve o documento pronto para indexar."""
    texto = from_path(path)
    titulo = meta.pop("title", None) or _titulo_provavel(texto, path)
    return Document(uri=str(path.resolve()), text=texto, kind=kind,
                    title=titulo, source=path.parent.name, **meta)


def _titulo_provavel(texto: str, path: Path) -> str:
    for linha in texto.split("\n"):
        linha = linha.strip()
        if 12 <= len(linha) <= 220 and not SECTION_RE.match(linha):
            return linha
    return path.stem.replace("_", " ")
