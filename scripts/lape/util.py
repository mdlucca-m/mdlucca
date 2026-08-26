"""Normalizacao de texto, datas e nomes de autores."""
from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from typing import Any, Iterable

_MONTHS_PT = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}

_TRUTHY = {"1", "sim", "s", "yes", "y", "true", "t", "verdadeiro", "x"}
_FALSY = {"0", "nao", "não", "n", "no", "false", "f", "falso", ""}


def is_na(value: Any) -> bool:
    """True para None, NaN e NaT (pandas/numpy) sem importar pandas."""
    if value is None:
        return True
    try:
        return bool(value != value)  # NaN e NaT sao diferentes de si mesmos
    except Exception:
        return False


def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def norm_key(value: Any) -> str:
    """Chave normalizada: sem acento, minuscula, separadores virando '_'."""
    if value is None:
        return ""
    text = strip_accents(str(value)).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def clean_text(value: Any) -> str | None:
    """Texto limpo ou None para vazios/NaN/NaT."""
    if is_na(value):
        return None
    text = str(value).replace("\xa0", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if text == "" or text.lower() in {"nan", "nat", "none", "null", "-", "--"}:
        return None
    return text


def to_bool(value: Any, default: int = 0) -> int:
    text = clean_text(value)
    if text is None:
        return default
    low = strip_accents(text).lower()
    if low in _TRUTHY:
        return 1
    if low in _FALSY:
        return 0
    return default


def to_int(value: Any) -> int | None:
    text = clean_text(value)
    if text is None:
        return None
    match = re.search(r"-?\d+", text.replace(".", "").replace(",", "."))
    return int(match.group()) if match else None


def to_float(value: Any) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    text = text.replace(".", "") if text.count(",") == 1 and text.count(".") > 1 else text
    text = text.replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def parse_date(value: Any) -> str | None:
    """Converte praticamente qualquer representacao de data para ISO YYYY-MM-DD.

    Aceita datetime/date, serial do Excel, dd/mm/aaaa, aaaa-mm-dd, mm/aaaa,
    'mar/2024', 'marco de 2024' e apenas o ano.
    """
    if is_na(value):
        return None
    if isinstance(value, _dt.datetime):
        return value.date().isoformat()
    if isinstance(value, _dt.date):
        return value.isoformat()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        serial = float(value)
        if 20000 < serial < 80000:  # serial do Excel (1900-2119)
            base = _dt.date(1899, 12, 30)
            return (base + _dt.timedelta(days=int(serial))).isoformat()
        if 1900 <= serial <= 2100:
            return f"{int(serial):04d}-01-01"
        return None

    text = clean_text(value)
    if text is None:
        return None

    iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if iso:
        return _safe_date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))

    br = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", text)
    if br:
        year = int(br.group(3))
        year += 2000 if year < 100 and year < 70 else (1900 if year < 100 else 0)
        return _safe_date(year, int(br.group(2)), int(br.group(1)))

    my = re.match(r"^(\d{1,2})[/.-](\d{4})$", text)
    if my:
        return _safe_date(int(my.group(2)), int(my.group(1)), 1)

    named = re.match(r"^([a-zA-Zçãéêó]{3,})\.?\s*(?:de\s+)?[/ -]?\s*(\d{4})$", text)
    if named:
        month = _MONTHS_PT.get(strip_accents(named.group(1)).lower()[:3])
        if month:
            return _safe_date(int(named.group(2)), month, 1)

    year_only = re.match(r"^(19|20)\d{2}$", text)
    if year_only:
        return f"{text}-01-01"

    return None


def _safe_date(year: int, month: int, day: int) -> str | None:
    try:
        return _dt.date(year, max(1, min(12, month)), max(1, min(31, day))).isoformat()
    except ValueError:
        try:
            return _dt.date(year, max(1, min(12, month)), 1).isoformat()
        except ValueError:
            return None


def year_of(iso_date: str | None) -> int | None:
    if not iso_date:
        return None
    try:
        return int(iso_date[:4])
    except (ValueError, TypeError):
        return None


def parse_datetime(value: Any, default_time: str = "00:00") -> str | None:
    """Retorna 'YYYY-MM-DD HH:MM' a partir de data (+ hora opcional embutida)."""
    if is_na(value):
        return None
    if isinstance(value, _dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    text = clean_text(value)
    if text is None:
        return None
    time_match = re.search(r"(\d{1,2})[h:](\d{2})", text)
    date_part = parse_date(re.sub(r"\s*\d{1,2}[h:]\d{2}.*$", "", text).strip()) or parse_date(text)
    if date_part is None:
        return None
    if time_match:
        return f"{date_part} {int(time_match.group(1)):02d}:{time_match.group(2)}"
    return f"{date_part} {default_time}"


# ----------------------------------------------------------------------
# Nomes de autores
# ----------------------------------------------------------------------

_PARTICLES = {"de", "da", "do", "das", "dos", "e", "del", "della", "van", "von", "la", "le"}
_SUFFIXES = {"jr", "junior", "filho", "neto", "sobrinho", "ii", "iii", "iv"}


def split_authors(raw: Any) -> list[str]:
    """Divide uma celula com varios autores.

    Aceita ';' e '|' (preferidos) e tambem listas separadas por virgula,
    distinguindo 'Loiane, Vilarino, Andrade' (tres pessoas) de
    'ANDRADE, A.; VILARINO, G. T.' (sobrenome + iniciais).
    """
    text = clean_text(raw)
    if text is None:
        return []
    if ";" in text:
        parts = text.split(";")
    elif "|" in text:
        parts = text.split("|")
    elif "," in text:
        parts = _split_comma_list(text)
    elif re.search(r"\s+(?:e|and|&)\s+", text):
        parts = re.split(r"\s+(?:e|and|&)\s+", text)
    else:
        parts = [text]
    return [p.strip(" ,;|") for p in parts if clean_text(p)]


def _split_comma_list(text: str) -> list[str]:
    """Decide se as virgulas separam pessoas ou 'Sobrenome, Iniciais'."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) < 2:
        return parts
    initials_like = sum(1 for p in parts if _looks_like_initials(p))
    if initials_like * 2 >= len(parts):
        merged: list[str] = []
        for part in parts:
            if _looks_like_initials(part) and merged:
                merged[-1] = f"{merged[-1]}, {part}"
            else:
                merged.append(part)
        return merged
    return parts


def _looks_like_initials(part: str) -> bool:
    """'A.', 'G. T.', 'MS' parecem iniciais; 'Alexandro' nao."""
    compact = re.sub(r"[\s.]", "", part)
    return bool(compact) and compact.isalpha() and len(compact) <= 3 and (
        compact.isupper() or "." in part
    )


def author_key(name: Any) -> str:
    """Chave canonica de autor: 'sobrenome_iniciais'.

    'Alexandro Andrade', 'ANDRADE, A.', 'Andrade, Alexandro', 'Andrade A.'
    e 'ANDRADE A' produzem a mesma chave, permitindo casar a autoria vinda
    da planilha, do Lattes e das bases de citacao.
    """
    text = clean_text(name)
    if text is None:
        return ""
    raw = re.sub(r"[^A-Za-z,\s.'-]", " ", strip_accents(text))

    if "," in raw:
        last_raw, first_raw = raw.split(",", 1)
        surname = [t for t in _tokens(last_raw) if t.rstrip(".").lower() not in _SUFFIXES]
        surname = surname or _tokens(last_raw)
        given = _tokens(first_raw)
    else:
        tokens = _tokens(raw)
        if not tokens:
            return ""
        if len(tokens) == 1:
            return re.sub(r"[^a-z]", "", tokens[0].lower())

        end_i = len(tokens)
        while end_i > 1 and tokens[end_i - 1].rstrip(".").lower() in _SUFFIXES:
            end_i -= 1
        trailing: list[str] = []
        while end_i > 1 and _is_initial_group(tokens[end_i - 1]):
            end_i -= 1
            trailing.insert(0, tokens[end_i])

        idx = end_i - 1
        while idx > 0 and tokens[idx - 1].rstrip(".").lower() in _PARTICLES:
            idx -= 1
        surname = [tokens[idx]]
        given = tokens[:idx] + trailing

    last = re.sub(r"[^a-z]", "", surname[0].lower() if surname else "")
    initials = _initials(given)
    return f"{last}_{initials}" if initials else last


def _tokens(text: str) -> list[str]:
    """Tokens preservando caixa e o ponto final ('A.', 'GT', 'Andrade')."""
    return re.findall(r"[A-Za-z'-]+\.?", text)


def _is_initial_group(token: str) -> bool:
    """'A.', 'G', 'GT' sao iniciais; 'Sa', 'Ana', 'Wu' sao nomes."""
    had_dot = token.endswith(".")
    word = token.rstrip(".")
    if not word.isalpha():
        return False
    if len(word) == 1:
        return True
    if had_dot and len(word) <= 3:
        return True
    return len(word) == 2 and word.isupper()


def _initials(tokens: list[str]) -> str:
    """Primeira letra de cada prenome, expandindo grupos como 'GT' em 'g'+'t'."""
    out: list[str] = []
    for token in tokens:
        word = token.rstrip(".")
        low = word.lower()
        if not low or low in _PARTICLES or low in _SUFFIXES:
            continue
        if _is_initial_group(token) and len(word) > 1:
            out.extend(low)
        else:
            out.append(low[0])
    return "".join(out)


def display_name(name: Any) -> str:
    """Nome em caixa de titulo, preservando particulas."""
    text = clean_text(name)
    if text is None:
        return ""
    if "," in text and len(text.split(",")) == 2:
        last, first = (p.strip() for p in text.split(","))
        text = f"{first} {last}".strip()
    words = []
    for word in text.split():
        low = word.lower()
        if low in _PARTICLES and words:
            words.append(low)
        elif len(word) <= 2 and word.isupper():
            words.append(word)
        else:
            words.append(word.capitalize() if not word.isupper() or len(word) > 3 else word.capitalize())
    return " ".join(words)


def title_key(title: Any) -> str:
    """Chave de deduplicacao de artigos (titulo sem acento/pontuacao)."""
    text = clean_text(title)
    if text is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", strip_accents(text).lower())


def norm_doi(value: Any) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    text = re.sub(r"^\s*(https?://(dx\.)?doi\.org/|doi:\s*)", "", text, flags=re.I)
    text = text.strip().lower()
    return text if text.startswith("10.") else None


def first_present(row: dict, keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row and clean_text(row[key]) is not None:
            return row[key]
    return None
