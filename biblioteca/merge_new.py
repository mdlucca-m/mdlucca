#!/usr/bin/env python3
"""Mescla novos artigos (biblioteca/_new-*.json) na biblioteca, sem duplicar DOIs.
- Atualiza biblioteca/biblioteca-enriched.json (schema completo) e biblioteca/biblioteca.json (schema base).
- Ordena por ano desc.  Remove os arquivos _new-*.json após mesclar.
Uso:  python3 biblioteca/merge_new.py   (depois rode build.py)
"""
import glob, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_FIELDS = ["authors", "year", "title", "journal", "doi", "citations", "sport", "topic", "finding"]

def norm_doi(d):
    return (d or "").strip().lower().rstrip(".")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def main():
    enriched = load(os.path.join(ROOT, "biblioteca-enriched.json"))
    seen = {norm_doi(e.get("doi")) for e in enriched}
    news = sorted(glob.glob(os.path.join(ROOT, "_new-*.json")))
    added, files_used = [], []
    for nf in news:
        try:
            entries = load(nf)
        except Exception as ex:
            print(f"skip {os.path.basename(nf)}: {ex}"); continue
        files_used.append(nf)
        for e in entries:
            dk = norm_doi(e.get("doi"))
            if not dk or dk in seen:
                continue
            seen.add(dk)
            enriched.append(e)
            added.append((e.get("year"), e.get("doi"), e.get("sport"), e.get("title", "")[:60]))
    # sort by year desc, then title
    enriched.sort(key=lambda x: (-(x.get("year") or 0), str(x.get("title", ""))))
    # write enriched (full)
    with open(os.path.join(ROOT, "biblioteca-enriched.json"), "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=1)
    # derive base
    base = [{k: e.get(k) for k in BASE_FIELDS} for e in enriched]
    with open(os.path.join(ROOT, "biblioteca.json"), "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    # cleanup temp files
    for nf in files_used:
        os.remove(nf)
    print(f"merged {len(added)} new → total {len(enriched)}")
    for y, doi, sport, title in sorted(added, key=lambda x: -(x[0] or 0)):
        print(f"  +{y} · {sport} · {doi} · {title}")

if __name__ == "__main__":
    main()
