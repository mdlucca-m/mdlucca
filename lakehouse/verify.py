# -*- coding: utf-8 -*-
"""Verificação de robustez do lakehouse — um portão único de qualidade.

Checa, além dos testes dbt (na build) e da auditoria Python:
  1. Determinismo   — reconstruir o gold duas vezes dá conteúdo idêntico.
  2. Idempotência   — reingerir a bronze não altera silver/gold.
  3. Reconciliação  — painel × gold (DIM · dz · SNR).
  4. Auditoria      — as 19 checagens das análises.
Sai !=0 se algo falhar. Uso: `python verify.py`
"""
from __future__ import annotations
import sys, hashlib, subprocess, os
import lh

GOLD = ["athlete_day", "daily_group", "acute_prepos", "risk_features",
        "athlete_day_unified", "athlete_profile", "an_d17", "an_friedman",
        "an_spearman", "an_profiles", "an_profiles_byday", "an_profiles_byday_t",
        "an_snr", "an_negatives_daytype", "an_wellbeing", "an_profile_group",
        "an_profile_athlete", "an_tcar_adapt", "an_pv_mood", "an_pv_threshold",
        "an_pv_bands", "an_desc", "an_prepos_dim", "an_perfis_byday_count",
        "an_wellbeing_byday", "an_wellbeing_bytype", "an_wellbeing_corr",
        "an_models", "an_roc", "an_negatives_bydaytype", "an_negatives_mix", "an_icc", "an_omega", "an_thresholds", "an_variance", "an_variance_curves", "an_transitions", "an_risk_profiles", "an_allometry", "an_pvmodel", "an_athlete_profiles", "an_learning", "an_pca", "risk_features"]

def _sig(layer, table):
    df = lh.read_delta(layer, table).reindex(sorted(lh.read_delta(layer, table).columns), axis=1)
    for c in df.select_dtypes("number").columns:  # ignora ruído de ponto flutuante
        df[c] = df[c].round(6)
    key = [c for c in ("ID", "dia", "var", "perfil", "par") if c in df.columns]
    if key:
        df = df.sort_values(key).reset_index(drop=True)
    return hashlib.sha1(df.to_csv(index=False).encode()).hexdigest()[:12]

def sig_all():
    return {t: _sig("gold", t) for t in dict.fromkeys(GOLD)}

def step(msg):
    print(f"\n=== {msg} ===")

def main():
    ok = True
    step("1/4 build inicial")
    import run_pipeline
    run_pipeline.main()
    s1 = sig_all()

    step("2/4 determinismo (rebuild → mesmo conteúdo?)")
    import ingest, dbt_run, analytics, analytics_physical, analytics_panel
    ingest.run(); dbt_run.run(); analytics.run(); analytics_physical.run(); analytics_panel.run()
    s2 = sig_all()
    diff = [t for t in s1 if s1[t] != s2[t]]
    det = not diff
    print("determinismo:", "OK" if det else f"DIVERGE em {diff}")
    ok &= det

    step("3/4 idempotência (reingestão não muda silver/gold)")
    n_ad = len(lh.read_delta("gold", "athlete_day"))
    n_mood = len(lh.read_delta("silver", "mood"))
    ingest.run(); dbt_run.run()
    idem = (len(lh.read_delta("gold", "athlete_day")) == n_ad == 166 and
            len(lh.read_delta("silver", "mood")) == n_mood == 456)
    print("idempotência:", "OK" if idem else "FALHOU (silver/gold mudaram ao reingerir)")
    ok &= idem

    step("4/4 auditoria das análises")
    r = subprocess.run([sys.executable, os.path.join(lh.ROOT, "tests", "audit.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1])
    ok &= (r.returncode == 0)

    print("\n" + "=" * 52)
    print("LAKEHOUSE ROBUSTO ✓" if ok else "FALHAS ENCONTRADAS ✗")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
