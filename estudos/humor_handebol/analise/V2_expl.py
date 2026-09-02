# -*- coding: utf-8 -*-
"""Análises exploratórias que faltavam ao relatório descritivo: transição
individual de perfil entre o primeiro e o sétimo dia, classificação de risco
por atleta, magnitude de mudança dia a dia, comportamento intradiário agregado
de todas as variáveis, e ranking de sensibilidade.

Escreve dados/V2_expl.json.
"""
import json, os, collections, numpy as np
from scipy import stats

RAIZ = os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
jd = lambda n: json.load(open(f"{DADOS}/{n}.json", encoding="utf-8"))
Q = jd("V2_perfis"); A1 = jd("V2_a1"); B = jd("V2_base")

NOMES = Q['NOMES']  # Iceberg, Superfície, Submerso, Barbatana de tubarão, Iceberg invertido, Everest invertido
FAIXA_DE = {0: 'Favorável', 1: 'Neutra', 2: 'Neutra', 3: 'De risco', 4: 'De risco', 5: 'De risco'}
a_AD = np.array(Q['a_AD']); dia_AD = np.array(Q['dia_AD']); lab_AD = np.array(Q['lab_AD'])
V7 = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão', 'TMD']
V11 = V7 + ['Fad.Física', 'Fad.Mental', 'Epworth', 'PSS']

# ---------- A. transição individual de perfil entre D1 e D7 ----------
d1 = {a: lab_AD[(a_AD == a) & (dia_AD == 1)][0] for a in set(a_AD) if (dia_AD[(a_AD == a) & (dia_AD == 1)]).size}
d7 = {a: lab_AD[(a_AD == a) & (dia_AD == 7)][0] for a in set(a_AD) if (dia_AD[(a_AD == a) & (dia_AD == 7)]).size}
pareados = sorted(set(d1) & set(d7))
MATRIZ = [[0] * 6 for _ in range(6)]
for a in pareados:
    MATRIZ[d1[a]][d7[a]] += 1
TRANS = {}
for i, nome in enumerate(NOMES):
    total = sum(MATRIZ[i])
    ficou = MATRIZ[i][i]
    destino = collections.Counter()
    for j, n in enumerate(MATRIZ[i]):
        if n and j != i: destino[NOMES[j]] = n
    TRANS[nome] = dict(n_d1=total, ficou=ficou,
                        pct_ficou=(100 * ficou / total if total else None),
                        destinos=dict(destino))
print(f"transição de perfil, {len(pareados)} atletas pareados em D1 e D7")
for nome, t in TRANS.items():
    print(f"  {nome:22} n={t['n_d1']:>2}  ficou={t['ficou']}  foi para: {t['destinos']}")

# ---------- B. classificação de risco por atleta ----------
RISCO = []
for a in sorted(set(a_AD)):
    m = a_AD == a
    dias = dia_AD[m]; labs = lab_AD[m]
    faixas = [FAIXA_DE[int(k)] for k in labs]
    n_risco = sum(1 for f in faixas if f == 'De risco')
    n_fav = sum(1 for f in faixas if f == 'Favorável')
    ult = int(dias.max())
    faixa_ult = FAIXA_DE[int(labs[list(dias).index(ult)])]
    perfil_ult = NOMES[int(labs[list(dias).index(ult)])]
    if n_risco == 0: classe = 'nunca em risco'
    elif n_risco == len(dias): classe = 'sempre em risco'
    else: classe = 'risco intermitente'
    RISCO.append(dict(atleta=a, n_dias=len(dias), n_risco=n_risco, n_favoravel=n_fav,
                       pct_risco=100 * n_risco / len(dias), ultimo_dia=ult,
                       faixa_ultimo=faixa_ult, perfil_ultimo=perfil_ult, classe=classe))
n_nunca = sum(1 for r in RISCO if r['classe'] == 'nunca em risco')
n_sempre = sum(1 for r in RISCO if r['classe'] == 'sempre em risco')
n_interm = len(RISCO) - n_nunca - n_sempre
print(f"\nclassificação de risco, {len(RISCO)} atletas: nunca={n_nunca} sempre={n_sempre} intermitente={n_interm}")

# ---------- C. magnitude de mudança dia a dia (qual transição pesa mais) ----------
MUDANCA = []
for d in range(1, 7):
    soma_abs_piso = 0.0
    detalhe = {}
    for v in V7:
        s = A1['SER'][v]
        delta = s['d1'][d - 1]  # Δ(d) = suavizado(d+1) - suavizado(d), d=1..6
        piso = s['piso']
        detalhe[v] = dict(delta=delta, em_pisos=delta / piso)
        soma_abs_piso += abs(delta / piso)
    MUDANCA.append(dict(transicao=f"D{d}→D{d+1}", soma_abs_pisos=soma_abs_piso, detalhe=detalhe))
MUDANCA.sort(key=lambda x: -x['soma_abs_pisos'])
print("\nmagnitude de mudança por transição, soma dos módulos em pisos (sete variáveis)")
for m in MUDANCA: print(f"  {m['transicao']:8} {m['soma_abs_pisos']:.2f} pisos")

# ---------- D. comportamento intradiário agregado (pré×pós, todas as variáveis) ----------
PP = B['prepos']
INTRADIA = {}
for v in V11:
    pre = np.array([r[f'pre_{v}'] for r in PP], float)
    pos = np.array([r[f'pos_{v}'] for r in PP], float)
    dif = pos - pre
    try:
        w = stats.wilcoxon(pos, pre)
        stat, p = float(w.statistic), float(w.pvalue)
    except ValueError:
        stat, p = float('nan'), 1.0
    n = len(dif); z = stats.norm.isf(p / 2) if 0 < p < 1 else 0.0
    r = z / np.sqrt(n) if n else 0.0
    INTRADIA[v] = dict(n=n, media_pre=float(pre.mean()), media_pos=float(pos.mean()),
                        media_dif=float(dif.mean()), dp_dif=float(dif.std(ddof=1)),
                        estatistica=stat, p=p, efeito_r=float(r),
                        pioram=int((dif > 0).sum()) if v not in ('Vigor',) else int((dif < 0).sum()),
                        n_mudam=int((dif != 0).sum()))
print(f"\nintradia agregado (pré×pós, n={len(PP)} pares, todos os dias e estímulos)")
for v, d in INTRADIA.items():
    print(f"  {v:12} pré={d['media_pre']:6.2f} pós={d['media_pos']:6.2f} "
          f"Δ={d['media_dif']:+6.2f}  p={d['p']:.4f}  r={d['efeito_r']:.2f}")

# ---------- E. ranking de sensibilidade (variabilidade) ----------
SENSI = []
for v in V11:
    de = A1['DESC'][v]; se = A1['SER'][v]
    SENSI.append(dict(variavel=v, cv=de['cv'], razao_piso=se['razao'], piso=se['piso'],
                       dtot=se['dtot'], sinal=se['sinal']))
SENSI.sort(key=lambda x: -x['razao_piso'])
print("\nranking de sensibilidade (razão deslocamento/piso, decrescente)")
for s in SENSI: print(f"  {s['variavel']:12} razão={s['razao_piso']:5.1f}  CV={s['cv']:6.1f}%")

json.dump(dict(TRANS=TRANS, MATRIZ=MATRIZ, NOMES_MATRIZ=NOMES, n_pareados=len(pareados),
               RISCO=RISCO, n_nunca_risco=n_nunca, n_sempre_risco=n_sempre, n_intermitente=n_interm,
               MUDANCA=MUDANCA, INTRADIA=INTRADIA, SENSI=SENSI, V11=V11),
          open(f"{DADOS}/V2_expl.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"\nescrito: {DADOS}/V2_expl.json")
