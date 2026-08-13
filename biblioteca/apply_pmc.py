#!/usr/bin/env python3
"""Aplica o enriquecimento de MÉTODOS (texto completo PMC) do agente metodos-pmc.
Lê biblioteca/_pmc-*.json (arrays de {doi, pmcid, fulltext, populacao, amostra,
instrumentos, variaveis_analisadas, analise_estatistica}) e preenche esses campos
em biblioteca-enriched.json por DOI. Remove os _pmc-*.json após aplicar.
Uso:  python3 biblioteca/apply_pmc.py   (depois rode build.py)
"""
import glob, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
# campos que o texto completo pode preencher/refinar
FIELDS = ["populacao", "amostra", "instrumentos", "variaveis_analisadas", "analise_estatistica", "pmcid"]

def norm(d):
    return (d or "").strip().lower().rstrip(".")

def main():
    p = os.path.join(ROOT, "biblioteca-enriched.json")
    enriched = json.load(open(p, encoding="utf-8"))
    by_doi = {norm(e.get("doi")): e for e in enriched}
    files = sorted(glob.glob(os.path.join(ROOT, "_pmc-*.json")))
    patched, fulltext, used, unmatched = 0, 0, [], []
    for f in files:
        try:
            recs = json.load(open(f, encoding="utf-8"))
        except Exception as ex:
            print(f"skip {os.path.basename(f)}: {ex}"); continue
        used.append(f)
        for r in recs:
            e = by_doi.get(norm(r.get("doi")))
            if not e:
                unmatched.append(r.get("doi")); continue
            for k in FIELDS:
                v = r.get(k)
                if v not in (None, "", "—"):
                    e[k] = v
            if r.get("fulltext") == "PMC":
                e["fulltext"] = "PMC"; fulltext += 1
            patched += 1
    json.dump(enriched, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for f in used:
        os.remove(f)
    total_ft = sum(1 for e in enriched if e.get("fulltext") == "PMC")
    print(f"patched {patched} registros · com texto completo PMC nesta rodada: {fulltext} · total PMC no acervo: {total_ft}")
    if unmatched:
        print("DOIs não encontrados:", unmatched[:20])

if __name__ == "__main__":
    main()
