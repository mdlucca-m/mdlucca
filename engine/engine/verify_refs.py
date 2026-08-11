"""verify_refs.py — integração: verifica cada DOI no Crossref (api.crossref.org).

Confirma que a referência existe e devolve título/ano/periódico. Tolerante a rede:
se estiver offline, marca como não verificado sem quebrar o pipeline.
"""
from __future__ import annotations
import json, os, ssl, urllib.request, urllib.error, urllib.parse
from typing import Iterable

CROSSREF = "https://api.crossref.org/works/"
UA = "DeLuccaContentEngine/1.0 (mailto:mdlucca@gmail.com)"

# usa o CA bundle do ambiente (ex.: proxy corporativo/agente), se existir
_CA = next((p for p in (os.environ.get("SSL_CERT_FILE"), os.environ.get("REQUESTS_CA_BUNDLE"),
                        "/root/.ccr/ca-bundle.crt") if p and os.path.exists(p)), None)
_CTX = ssl.create_default_context(cafile=_CA) if _CA else None


def verify_doi(doi: str, timeout: float = 8.0) -> dict | None:
    """Consulta o Crossref. Retorna metadados mínimos ou None se falhar/não existir.

    Respeita HTTPS_PROXY/HTTP_PROXY do ambiente (urllib lê automaticamente) e o
    CA bundle configurado. Em redes que bloqueiam o Crossref, retorna None sem quebrar.
    """
    url = CROSSREF + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
            msg = json.loads(r.read().decode("utf-8")).get("message", {})
    except Exception:
        return None
    title = (msg.get("title") or [""])[0]
    journal = (msg.get("container-title") or [""])[0]
    year = (msg.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0]
    return {"doi": doi, "title": title, "journal": journal, "year": year}


def verify_all(dois: Iterable[str]) -> dict[str, dict | None]:
    seen: dict[str, dict | None] = {}
    for d in dois:
        if d not in seen:
            seen[d] = verify_doi(d)
    return seen


if __name__ == "__main__":
    import sys
    from pathlib import Path
    cp = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent.parent / "content/caminho.json")
    content = json.loads(Path(cp).read_text(encoding="utf-8"))
    dois = [r["doi"] for r in content["refs"]]
    res = verify_all(dois)
    ok = sum(1 for v in res.values() if v)
    for d, v in res.items():
        print(("✓" if v else "✗"), d, "—", (v["title"][:70] if v else "não verificado"))
    print(f"\n{ok}/{len(res)} DOIs verificados no Crossref.")
