# -*- coding: utf-8 -*-
"""Auditoria e testes do lakehouse — torna TODAS as análises verificáveis.

Roda sem dependências (nem pytest): `python tests/audit.py`.
Cada checagem é uma função test_*; o runner reporta PASS/FAIL e sai com código
!=0 se algo falhar (pronto p/ CI). As funções também são coletáveis pelo pytest.

Grupos de checagem:
  A. Esquema & contagens (coorte de grupo único, 27 atletas)
  B. Reprodução dos números do estudo/painel (valores conhecidos)
  C. Consistência interna entre camadas
  D. Governança & qualidade (anonimização, dedup, nulos)
"""
from __future__ import annotations
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import lh

def _near(a, b, tol): assert abs(float(a) - float(b)) <= tol, f"{a} ≠ {b} (tol {tol})"
def _row(df, key, val): return df[df[key] == val].iloc[0]

# ---------------- A. Esquema & contagens ----------------
def test_coorte_27_atletas_grupo_unico():
    mood = lh.read_delta("silver", "mood")
    assert mood.ID.nunique() == 27, f"esperado 27 atletas, obtido {mood.ID.nunique()}"
    assert sorted(mood.dia.unique()) == [1, 2, 3, 4, 5, 6, 7], "dias devem ser 1..7"
    assert len(mood) == 456, f"esperado 456 observações, obtido {len(mood)}"

def test_sem_grupo_controle():
    phys = lh.read_delta("silver", "physical")
    grupos = set(phys["grupo_estudo"].unique())
    assert grupos == {"unico"}, f"desenho é grupo único; encontrado {grupos}"

def test_gold_contagens():
    assert len(lh.read_delta("gold", "athlete_day")) == 166
    assert len(lh.read_delta("gold", "daily_group")) == 7
    assert len(lh.read_delta("gold", "athlete_day_unified")) == 166

# ---------------- B. Reprodução dos números conhecidos ----------------
def test_trajetoria_diaria_bate_com_painel():
    dg = lh.read_delta("gold", "daily_group").set_index("dia")
    _near(dg.loc[1, "vigor"], 7.6, 0.1); _near(dg.loc[7, "vigor"], 4.5, 0.1)
    _near(dg.loc[1, "fadiga"], 4.0, 0.1); _near(dg.loc[7, "fadiga"], 7.5, 0.1)
    _near(dg.loc[1, "pth"], 2.5, 0.1);   _near(dg.loc[7, "pth"], 8.3, 0.1)

def test_efeitos_d1_d7_dz():
    d = lh.read_delta("gold", "an_d17").set_index("var")
    _near(d.loc["vigor", "dz"], -0.95, 0.02);  _near(d.loc["fadiga", "dz"], 0.72, 0.02)
    _near(d.loc["tensao", "dz"], -0.59, 0.02);  _near(d.loc["confusao", "dz"], -0.46, 0.02)
    _near(d.loc["pth", "dz"], 0.41, 0.02)
    assert bool(d.loc["vigor", "sig"]) and not bool(d.loc["raiva", "sig"])

def test_friedman_casos_completos():
    f = lh.read_delta("gold", "an_friedman").set_index("var")
    assert (f["n"] == 19).all(), "Friedman deve usar casos completos (n=19)"
    _near(f.loc["vigor", "chi2"], 14.7, 0.2); _near(f.loc["vigor", "W"], 0.13, 0.02)
    _near(f.loc["confusao", "chi2"], 25.8, 0.2)

def test_snr_decomposicao():
    s = lh.read_delta("gold", "an_snr").set_index("var")
    _near(s.loc["fadiga", "snr"], 6.2, 0.15); _near(s.loc["vigor", "snr"], 2.0, 0.15)
    _near(s.loc["pth", "snr"], 2.6, 0.15)
    for v in s.index:  # partição da variância soma ~100%
        _near(s.loc[v, "tendencia"] + s.loc[v, "hiit"] + s.loc[v, "ruido"], 100.0, 0.5)

def test_perfis_prevalencia():
    p = lh.read_delta("gold", "an_profiles").set_index("perfil")
    _near(p.loc["Iceberg", "prevalencia"], 31.6, 0.2)
    _near(p["prevalencia"].sum(), 100.0, 0.5)
    assert int(p["n"].sum()) == 456
    dom = lh.read_delta("gold", "an_profiles_byday").set_index("dia")
    assert dom.loc[1, "dominante"] == "Iceberg"
    assert dom.loc[7, "dominante"] == "Barbatana de tubarao"

def test_spearman_nivel_atleta_sem_pth():
    sp = lh.read_delta("gold", "an_spearman")
    pares = " ".join(sp["par"])
    assert "pth" not in pares, "correlações entre dimensões não devem incluir o composto PTH"
    assert len(sp) >= 3, "esperadas correlações significativas entre as dimensões"
    assert (sp["p"] <= 0.05).all(), "só pares significativos (p<0,05; arredondado)"

def test_perfil_grupo():
    g = lh.read_delta("gold", "an_profile_group").iloc[0]
    assert g["perfil_mais_prevalente"] == "Iceberg"
    _near(g["prevalencia_pct"], 31.6, 0.2)

def test_perfil_byday_trajetoria():
    t = lh.read_delta("gold", "an_profiles_byday_t").set_index("dia")
    # D1 = forma de iceberg (vigor alto, fadiga baixa); D7 = vigor baixo, fadiga alta
    assert t.loc[1, "vigor"] > t.loc[1, "fadiga"], "D1 deve ter vigor > fadiga (iceberg)"
    assert t.loc[7, "fadiga"] > t.loc[7, "vigor"], "D7 deve ter fadiga > vigor (erosão)"
    _near(t.loc[1, "vigor"], 56.1, 0.2); _near(t.loc[7, "fadiga"], 54.7, 0.2)

def test_perfil_individual_27_atletas():
    a = lh.read_delta("gold", "an_profile_athlete")
    assert len(a) == 27, f"esperado 1 perfil por atleta (27), obtido {len(a)}"
    assert int(a["n_obs"].sum()) == 456, "soma de respostas deve ser 456"
    validos = {"Iceberg", "Superficie", "Submerso", "Everest invertido",
               "Barbatana de tubarao", "Iceberg invertido"}
    assert set(a["perfil_medio"]).issubset(validos), "perfil_medio fora da taxonomia"
    for c in ["vigor", "fadiga", "tensao"]:
        assert a[c].between(25, 95).all(), f"T-score {c} fora de faixa plausível"

def test_wellbeing_epworth_sobe():
    w = lh.read_delta("gold", "an_wellbeing").set_index("var")
    assert w.loc["epworth", "dz"] > 0.3, "sonolência (Epworth) deve subir D1→D7"
    assert abs(w.loc["pss", "dz"]) < 0.3, "estresse (PSS) deve ficar estável"

def test_tcar_adaptacao_pico_velocidade():
    ad = lh.read_delta("gold", "an_tcar_adapt").set_index("var")
    assert int(ad.loc["tcarpv", "n"]) == 24, "coorte física T-CAR = 24 atletas"
    _near(ad.loc["tcarpv", "pre"], 14.88, 0.02); _near(ad.loc["tcarpv", "pos"], 15.66, 0.02)
    _near(ad.loc["tcarpv", "dz"], 0.93, 0.02)   # PV sobe pré→pós (adaptação aeróbia)
    _near(ad.loc["bksoma", "dz"], -1.08, 0.02)  # Baker soma melhora (tempo cai)

def test_pv_mood_fadiga_fisica_sobrevive_fdr():
    pm = lh.read_delta("gold", "an_pv_mood").set_index("dim")
    assert len(pm) == 9, "9 dimensões de humor no bloco PV×humor"
    _near(pm.loc["FadFisica", "r"], -0.54, 0.02)   # mais apto → menos fadiga física
    assert pm.loc["FadFisica", "fdr"] < 0.05, "PV×fadiga física deve sobreviver ao FDR"
    _near(pm.loc["Vigor", "r"], 0.48, 0.02)        # mais apto → mais vigor
    # negativas do BRUMS não se associam ao PV
    for d in ["Tensao", "Depressao", "Raiva", "Confusao"]:
        assert pm.loc[d, "p"] > 0.05, f"{d} não deveria se associar ao PV"

def test_pv_threshold_e_bandas():
    th = lh.read_delta("gold", "an_pv_threshold").set_index("dim")
    _near(th.loc["Vigor", "median"], 14.9, 0.05)
    assert th.loc["FadFisica", "hi"] < th.loc["FadFisica", "lo"], "acima da mediana → menos fadiga física"
    assert th.loc["Vigor", "hi"] > th.loc["Vigor", "lo"], "acima da mediana → mais vigor"
    bd = lh.read_delta("gold", "an_pv_bands")
    n = bd[bd.dim == "Vigor"].sort_values("band")["n"].tolist()
    assert n == [6, 10, 9] and sum(n) == 25, f"tercis de PV devem cobrir os 25 pares, obtido {n}"
    vig = bd[bd.dim == "Vigor"].sort_values("band")["mean"].tolist()
    assert vig[2] > vig[0], "vigor cresce do tercil baixo para o alto de aptidão"

def test_painel_desc_prepos_perfis():
    d = lh.read_delta("gold", "an_desc")
    assert len(d) == 7 and set(d["var"]) >= {"vigor", "fadiga", "pth"}
    _near(_row(d, "var", "vigor")["media"], 5.7, 0.1)
    pp = lh.read_delta("gold", "an_prepos_dim").set_index("var")
    assert len(pp) == 7
    assert pp.loc["fadiga", "dz"] > 0 and pp.loc["vigor", "dz"] < 0, "agudo: fadiga↑ vigor↓"
    assert pp.loc["pth", "pct"] > 0, "PTH sobe pré→pós"
    pf = lh.read_delta("gold", "an_perfis_byday_count")
    assert int(pf["d1"].sum()) == 27, "27 atletas classificados no D1"
    ice = _row(pf, "perfil", "Iceberg")
    assert ice["d1"] > ice["d7"], "Iceberg predomina no D1 e erode até o D7"

def test_painel_wellbeing_gold():
    byd = lh.read_delta("gold", "an_wellbeing_byday").sort_values("dia")
    assert len(byd) == 7
    assert byd.iloc[6]["epworth"] > byd.iloc[0]["epworth"], "sonolência sobe D1→D7"
    byt = lh.read_delta("gold", "an_wellbeing_bytype").set_index("cat")
    assert byt.loc["HIIT", "epworth"] >= byt.loc["Outro", "epworth"], "mais sonolento em dia de HIIT"
    cor = lh.read_delta("gold", "an_wellbeing_corr").set_index("par")
    assert cor.loc["epworth × fadiga", "rho"] > 0, "sonolência acompanha a fadiga"
    assert cor.loc["epworth × vigor", "rho"] < 0, "sonolência inversa ao vigor"

# ---------------- C. Consistência interna entre camadas ----------------
def test_daily_group_deriva_de_athlete_day():
    ad = lh.read_delta("gold", "athlete_day")
    dg = lh.read_delta("gold", "daily_group").set_index("dia")
    recomputed = ad.groupby("dia")["vigor"].mean().round(1)
    for d in range(1, 8):
        _near(dg.loc[d, "vigor"], recomputed.loc[d], 0.1)

def test_obt_alinha_com_athlete_day():
    ad = lh.read_delta("gold", "athlete_day")
    obt = lh.read_delta("gold", "athlete_day_unified")
    assert len(ad) == len(obt), "OBT deve ter uma linha por atleta-dia"
    assert {"epworth", "pss", "hiit_pse"}.issubset(obt.columns), "OBT deve integrar sono/estresse/HIIT"

def test_rotulos_de_risco_validos():
    rf = lh.read_delta("gold", "risk_features")
    vals = set(rf["risco_amanha"].dropna().unique())
    assert vals.issubset({0, 1}), f"rótulo de risco deve ser 0/1, obtido {vals}"

# ---------------- D. Governança & qualidade ----------------
def test_anonimizacao_A_codes():
    mood = lh.read_delta("silver", "mood")
    assert all(re.fullmatch(r"A\d{2}", str(i)) for i in mood.ID.unique()), "IDs devem ser A01–A27 (anonimizados)"

def test_dedup_chave_unica():
    mood = lh.read_delta("silver", "mood")
    assert not mood.duplicated(["ID", "dia", "seq"]).any(), "silver.mood deve ser único por (ID,dia,seq)"

def test_sem_nulos_em_chaves():
    mood = lh.read_delta("silver", "mood")
    for c in ["ID", "dia", "seq", "momento", "Vigor", "Fadiga"]:
        assert mood[c].notna().all(), f"coluna-chave {c} não pode ter nulos"

# ---------------- runner ----------------
def _all_tests():
    g = globals()
    return [(n, g[n]) for n in sorted(g) if n.startswith("test_") and callable(g[n])]

def main():
    fails = 0
    print("AUDITORIA DO LAKEHOUSE — análises verificáveis\n" + "=" * 48)
    for name, fn in _all_tests():
        try:
            fn(); print(f"  PASS  {name}")
        except Exception as e:
            fails += 1; print(f"  FAIL  {name}\n        → {e}")
    total = len(_all_tests())
    print("=" * 48)
    print(f"{total - fails}/{total} checagens OK" + ("" if not fails else f" · {fails} FALHA(S)"))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
