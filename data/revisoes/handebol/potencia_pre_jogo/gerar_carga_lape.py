"""Gera carga_lape_potencia_pre_jogo.sql (tabelas reviews, review_searches e refs de sql/schema.sql)."""
import re

s = open("gerar_protocolo_potencia.py", encoding="utf-8").read()
refs = re.findall(r'^    "([A-ZÁÉÍ].*?)",$', s.split("REFS = [")[1].split("]\nfor ref")[0], re.M)
Q = ('("handball"[tiab] OR "team handball"[tiab]) AND ("Warm-Up Exercise"[Mesh] OR "warm-up"[tiab] OR "warm up"[tiab] '
     'OR "post-activation"[tiab] OR "postactivation"[tiab] OR potentiation[tiab] OR "conditioning activity"[tiab]) AND '
     '(jump*[tiab] OR sprint*[tiab] OR throw*[tiab] OR "change of direction"[tiab] OR power[tiab])')
esc = lambda x: x.replace("'", "''")


def partes(r):
    ps = re.split(r"(?<=[.?]) ", r)
    ps = [p[:-1] if p.endswith(".") else p for p in ps]
    i = 0
    while re.search(r"(?:(?:^|[ ,;.])[A-Z]|et al)$", ps[i]):
        i += 1
    aut = ". ".join(ps[:i])
    tit = ps[i]
    while tit.endswith(" vs"):
        i += 1
        tit += ". " + ps[i]
    return aut, tit, ps[i + 1].split(",")[0]


L = ["-- Carga do tema 'Potência pré-jogo no handebol' no banco do Lape (tabelas de sql/schema.sql).",
     "-- Uso: sqlite3 <banco.db> < carga_lape_potencia_pre_jogo.sql", "BEGIN;",
     "INSERT OR IGNORE INTO reviews (code, title, tipo, question, population, intervention, comparison, outcome, "
     "study_designs, status) VALUES ('HB-POT-PREJOGO', 'Potência de membros inferiores e superiores no aquecimento "
     "pré-jogo do handebol', 'escopo', 'Quais estratégias de aquecimento e de potencialização pós-ativação melhoram salto, "
     "sprint, mudança de direção e arremesso antes do jogo de handebol?', 'Atletas de handebol', 'Aquecimento ou atividade "
     "de condicionamento pré-jogo', 'Aquecimento habitual ou controle', 'Salto, sprint, mudança de direção, velocidade de "
     "arremesso, esforço percebido', 'Experimentais agudos e revisões sistemáticas', 'extracao');",
     f"INSERT INTO review_searches (review_id, base, query, searched_on, n_retrieved) SELECT id, 'PubMed', '{esc(Q)}', "
     "'2026-11-21', 37 FROM reviews WHERE code='HB-POT-PREJOGO';"]
for r in refs:
    aut, tit, rev = partes(r)
    m = re.search(r"DOI: https://doi.org/(\S+)\.$", r)
    doi = f"'{m.group(1)}'" if m else "NULL"
    ano = re.findall(r", (\d{4})\.", r)[-1]
    L.append("INSERT INTO refs (review_id, title, authors, journal, year, doi, stage, decision, notes, origem) SELECT id, "
             f"'{esc(tit)}', '{esc(aut)}', '{esc(rev)}', {ano}, {doi}, 'texto_completo', 'incluido', "
             f"'Lido pelo resumo. ABNT: {esc(r)}', 'protocolo_potencia_pre_jogo' FROM reviews WHERE code='HB-POT-PREJOGO';")
L.append("COMMIT;")
open("carga_lape_potencia_pre_jogo.sql", "w", encoding="utf-8").write("\n".join(L) + "\n")
print(len(refs))
