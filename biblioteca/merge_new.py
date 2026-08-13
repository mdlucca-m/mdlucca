#!/usr/bin/env python3
"""Mescla novos artigos (biblioteca/_new-*.json) na biblioteca, sem duplicar DOIs.
- Atualiza biblioteca/biblioteca-enriched.json (schema completo) e biblioteca/biblioteca.json (schema base).
- Ordena por ano desc.  Remove os arquivos _new-*.json após mesclar.
Uso:  python3 biblioteca/merge_new.py   (depois rode build.py)
"""
import glob, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_FIELDS = ["authors", "year", "title", "journal", "doi", "citations", "sport", "topic", "finding"]
CANON_MODS = {'Ginástica rítmica', 'Ginástica artística', 'Ginástica aeróbica', 'Patinação artística', 'Nado artístico',
              'Dança', 'Ginástica acrobática', 'Proxy não-estético', 'Outro'}
CANON_VARS = {'Neuro', 'Psico', 'Performance', 'Fadiga'}
PYTHEME = {'motor-pattern': 'Neuro', 'emg-activation': 'Neuro', 'motor-unit': 'Neuro', 'firing-rate': 'Neuro', 'rfd-neural': 'Neuro', 'motor-learning': 'Neuro',
    'anxiety': 'Psico', 'perfectionism': 'Psico', 'body-image': 'Psico', 'disordered-eating': 'Psico', 'motivation': 'Psico', 'self-confidence': 'Psico',
    'stress-coping': 'Psico', 'burnout': 'Psico', 'mental-toughness': 'Psico', 'flow': 'Psico', 'attentional-focus': 'Psico',
    'self-talk': 'Psico', 'motivational-climate': 'Psico', 'resilience': 'Psico', 'well-being': 'Psico', 'passion': 'Psico', 'emotion-regulation': 'Psico', 'coping': 'Psico', 'mental-health': 'Psico', 'self-esteem': 'Psico', 'fear-of-failure': 'Psico', 'imagery': 'Psico',
    'physical-determinants': 'Performance', 'biomechanics-technique': 'Performance', 'anthropometry-maturation': 'Performance', 'talent-prediction': 'Performance', 'judging-scoring': 'Performance',
    'muscular-power': 'Performance', 'plyometrics': 'Performance', 'physiological': 'Performance', 'physical-capacities': 'Performance', 'neuromuscular-capacity': 'Neuro',
    'neuromuscular-fatigue': 'Fadiga', 'training-load': 'Fadiga', 'overtraining': 'Fadiga', 'recovery-readiness': 'Fadiga', 'red-s': 'Fadiga', 'menstrual-hormonal': 'Fadiga', 'perceived-fatigue': 'Fadiga'}

def canon_modalities(sport):
    s = (sport or "").lower(); out = []
    def add(x):
        if x not in out: out.append(x)
    if 'rítmica' in s or 'ritmica' in s: add('Ginástica rítmica')
    if 'aeróbic' in s or 'aerobic' in s: add('Ginástica aeróbica')
    if 'artística' in s or 'artistica' in s: add('Nado artístico' if 'nado' in s else 'Ginástica artística')
    if 'acrobática' in s or 'acrobatica' in s: add('Ginástica acrobática')
    if 'patinação' in s or 'patinacao' in s: add('Patinação artística')
    if 'nado' in s or 'sincronizado' in s: add('Nado artístico')
    if 'balé' in s or 'bale' in s or 'dança' in s or 'danca' in s or 'cheer' in s: add('Dança')
    if 'proxy' in s or 'saudáveis' in s or 'master' in s: add('Proxy não-estético')
    if 'estéticos' in s or 'esteticos' in s: [add(x) for x in ('Patinação artística', 'Dança', 'Ginástica artística')]
    if not out: add('Ginástica artística' if 'ginástica' in s or 'ginastica' in s else 'Outro')
    return out

def canonize(e):
    mods = []
    for m in (e.get("modalities") or []):
        for c in ([m] if m in CANON_MODS else canon_modalities(m)):
            if c not in mods: mods.append(c)
    e["modalities"] = mods or canon_modalities(e.get("sport", ""))
    e["n_modalities"] = len(e["modalities"])
    vs, seen = [v for v in (e.get("variables") or []) if v in CANON_VARS], []
    [seen.append(v) for v in vs if v not in seen]
    e["variables"] = seen or [PYTHEME.get(e.get("topic", ""), "Performance")]
    return e

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
    # canonicalize modalities/variables across all entries (idempotent)
    enriched = [canonize(e) for e in enriched]
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
