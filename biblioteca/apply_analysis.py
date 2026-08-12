#!/usr/bin/env python3
"""Aplica a análise estruturada (biblioteca/_ana-*.json) aos artigos existentes, por DOI.
Cada _ana-*.json é um array de {doi, amostra, resumo, variaveis_biodinamicas, analise_estatistica, sintese}.
Preenche esses 5 campos em biblioteca-enriched.json e remove os _ana-*.json.
Uso:  python3 biblioteca/apply_analysis.py   (depois rode build.py)
"""
import glob, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
ANA_FIELDS = ["amostra", "resumo", "variaveis_biodinamicas", "analise_estatistica", "sintese"]

def norm(d):
    return (d or "").strip().lower().rstrip(".")

def main():
    enr_path = os.path.join(ROOT, "biblioteca-enriched.json")
    enriched = json.load(open(enr_path, encoding="utf-8"))
    by_doi = {norm(e.get("doi")): e for e in enriched}
    files = sorted(glob.glob(os.path.join(ROOT, "_ana-*.json")))
    patched, unmatched, used = 0, [], []
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
            for k in ANA_FIELDS:
                if r.get(k) not in (None, ""):
                    e[k] = r[k]
            patched += 1
    json.dump(enriched, open(enr_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for f in used:
        os.remove(f)
    covered = sum(1 for e in enriched if e.get("resumo"))
    print(f"patched {patched} registros · cobertura de ficha: {covered}/{len(enriched)}")
    if unmatched:
        print("DOIs não encontrados:", unmatched)

if __name__ == "__main__":
    main()
