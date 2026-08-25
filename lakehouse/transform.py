# -*- coding: utf-8 -*-
"""SILVER e GOLD — transformações declarativas em SQL (DuckDB) sobre o Delta.

SILVER: conformar, tipar e DEDUPLICAR (idempotente) a bronze append-only.
        Regra de negócio do estudo: pré = primeira resposta do dia (seq mínima),
        pós = última do dia (seq máxima). Dados já anonimizados (A01–A27).
GOLD:   tabelas prontas para análise/painel/ML — médias atleta-dia, trajetória
        diária do grupo, efeito agudo pré→pós e a tabela de features de risco.
"""
from __future__ import annotations
import lh

SESS2DIA = {"S1": 2, "S2": 4, "S3": 7}  # sessões de HIIT -> dias do microciclo

def _dedup(raw, keys):
    """Dedup idempotente nível-atleta: mantém a carga mais recente e remove metadados."""
    d = raw.sort_values("_ingested_at").drop_duplicates(keys, keep="last")
    return d[[c for c in d.columns if not c.startswith("_")]].reset_index(drop=True)

DAY_TYPE = """
  CASE dia WHEN 1 THEN 'Baseline' WHEN 2 THEN 'HIIT' WHEN 3 THEN 'Jogo'
           WHEN 4 THEN 'HIIT' WHEN 5 THEN 'Jogo' WHEN 6 THEN 'Forca'
           WHEN 7 THEN 'HIIT' END
"""

def build_silver():
    # ---- silver.mood: dedup por (ID,dia,seq) mantendo a carga mais recente ----
    brums = lh.read_delta("bronze", "brums_raw")
    mood = lh.sql(f"""
        WITH ranked AS (
          SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY ID, dia, seq ORDER BY _ingested_at DESC) AS rn
          FROM brums)
        SELECT ID, CAST(dia AS INT) dia, CAST(seq AS INT) seq, momento,
               CAST(HIIT AS INT) hiit_flag, {DAY_TYPE} AS day_type,
               Tensao, Depressao, Raiva, Vigor, Fadiga, Confusao,
               TMD AS PTH, FadFisica, FadMental,
               first_value(seq) OVER w AS _seq_min,
               last_value(seq)  OVER w AS _seq_max
        FROM ranked WHERE rn = 1
        WINDOW w AS (PARTITION BY ID, dia ORDER BY seq
                     ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    """, brums=brums)
    mood["is_pre"] = mood["seq"] == mood["_seq_min"]
    mood["is_pos"] = mood["seq"] == mood["_seq_max"]
    mood = mood.drop(columns=["_seq_min", "_seq_max"])
    # ---- REGRA DO ESTUDO (dono dos dados): observação VÁLIDA por atleta-dia =
    #   pré = primeira resposta da manhã (seq mínima) e pós = última do dia (seq máxima).
    #   As respostas intermediárias ("mid") e pré/pós repetidos são duplas/erradas → descartadas.
    #   D1 (21/04) é BASELINE: conta apenas a medida da manhã (pré); a pós de D1 é descartada.
    #   Resultado: 286 observações válidas = 27 baseline + 139 pré + 120 pós · 13 coletas.
    mood = mood[mood["is_pre"] | mood["is_pos"]].copy()                       # endpoints válidos (pré/pós)
    mood = mood[~((mood["dia"] == 1) & mood["is_pos"] & ~mood["is_pre"])].copy()  # D1 = só baseline
    mood["momento"] = mood["is_pre"].map({True: "pre", False: "pos"})          # rótulo = endpoint (seq)
    lh.write_delta("silver", "mood", mood, mode="overwrite")
    _nb = int((mood["dia"] == 1).sum())
    print(f"[silver] mood        {len(mood)} obs válidas · {mood.ID.nunique()} atletas · "
          f"{_nb} baseline + {int((mood.momento=='pre').sum())-_nb} pré + {int((mood.momento=='pos').sum())} pós · dias {sorted(mood.dia.unique())}")

    # ---- silver.wellbeing: Epworth/PSS por atleta-dia (dedup por ID,dia) ----
    wb = lh.read_delta("bronze", "wellbeing_raw")
    wb2 = lh.sql("""
        SELECT ID, CAST(dia AS INT) dia,
               AVG(Epworth) AS epworth, AVG(PSS) AS pss
        FROM wb GROUP BY ID, dia
    """, wb=wb)
    lh.write_delta("silver", "wellbeing", wb2, mode="overwrite")
    print(f"[silver] wellbeing   {len(wb2)} atleta-dias")

    # ---- silver.hiit: carga interna por sessão ----
    hiit = lh.read_delta("bronze", "hiit_raw")
    hiit2 = lh.sql("""
        SELECT ID, sessao, fase, FC_pre, FC_pos, dFC, PSE
        FROM (SELECT *, ROW_NUMBER() OVER (
                 PARTITION BY ID, sessao, fase ORDER BY _ingested_at DESC) rn FROM hiit)
        WHERE rn = 1
    """, hiit=hiit)
    lh.write_delta("silver", "hiit", hiit2, mode="overwrite")
    print(f"[silver] hiit        {len(hiit2)} registros")

    # ---- silver nível-atleta: rsa, mdc (A-code), physical (P-code) ----
    rsa = _dedup(lh.read_delta("bronze", "rsa_raw"), ["ID"])
    lh.write_delta("silver", "rsa", rsa, mode="overwrite"); print(f"[silver] rsa         {len(rsa)} atletas")
    mdc = _dedup(lh.read_delta("bronze", "mdc_raw"), ["ID"])
    lh.write_delta("silver", "mdc", mdc, mode="overwrite"); print(f"[silver] mdc         {len(mdc)} atletas")
    phys = _dedup(lh.read_delta("bronze", "physical_raw"), ["id"])
    # CORREÇÃO (dono dos dados): o desenho é de GRUPO ÚNICO — não há grupo controle.
    # O rótulo "Controle/Experimental" da fonte é artefato de template e é neutralizado.
    if "Grupo" in phys.columns:
        phys = phys.rename(columns={"Grupo": "grupo_origem"})
    phys["grupo_estudo"] = "unico"
    lh.write_delta("silver", "physical", phys, mode="overwrite")
    print(f"[silver] physical    {len(phys)} atletas (P-code · grupo ÚNICO, sem controle)")
    # ---- silver.brums_items: itens BRUMS (sem ID) — psicometria ----
    items = lh.read_delta("bronze", "brums_items_raw")
    items = items.drop_duplicates("_row_hash").reset_index(drop=True)
    items = items[[c for c in items.columns if not c.startswith("_")]]
    lh.write_delta("silver", "brums_items", items, mode="overwrite"); print(f"[silver] brums_items {len(items)} respostas × 24 itens")

def build_gold():
    mood = lh.read_delta("silver", "mood")
    VARS = ["Vigor", "Fadiga", "Tensao", "Depressao", "Raiva", "Confusao", "PTH"]
    avg = ", ".join(f"AVG({v}) AS {v.lower()}" for v in VARS)

    # gold.athlete_day — média atleta-dia (todos os momentos) = unidade de análise
    ad = lh.sql(f"""SELECT ID, dia, ANY_VALUE(day_type) day_type, ANY_VALUE(hiit_flag) hiit_flag,
                           {avg}, COUNT(*) n_obs
                    FROM mood GROUP BY ID, dia ORDER BY ID, dia""", mood=mood)
    lh.write_delta("gold", "athlete_day", ad, mode="overwrite")
    print(f"[gold]   athlete_day {len(ad)} atleta-dias")

    # gold.daily_group — trajetória diária do grupo (média das médias atleta-dia)
    davg = ", ".join(f"AVG({v.lower()}) AS {v.lower()}" for v in VARS)
    dg = lh.sql(f"""SELECT dia, ANY_VALUE(day_type) day_type, {davg}, COUNT(*) n_atletas
                    FROM ad GROUP BY dia ORDER BY dia""", ad=ad)
    lh.write_delta("gold", "daily_group", dg, mode="overwrite")
    print(f"[gold]   daily_group {len(dg)} dias")

    # gold.acute_prepos — efeito agudo pré→pós por atleta-dia
    ap = lh.sql("""
        WITH pre AS (SELECT ID,dia,Vigor v_pre,Fadiga f_pre,PTH p_pre FROM mood WHERE momento='pre' AND dia>1),
             pos AS (SELECT ID,dia,Vigor v_pos,Fadiga f_pos,PTH p_pos FROM mood WHERE momento='pos' AND dia>1)
        SELECT pre.ID, pre.dia,
               v_pos-v_pre AS d_vigor, f_pos-f_pre AS d_fadiga, p_pos-p_pre AS d_pth
        FROM pre JOIN pos USING (ID,dia) WHERE pre.ID IS NOT NULL
    """, mood=mood)
    lh.write_delta("gold", "acute_prepos", ap, mode="overwrite")
    print(f"[gold]   acute_prepos {len(ap)} transições intradia")

    # gold.risk_features — features de HOJE + rótulo de risco AMANHÃ (para ML/IoT)
    #   risco = PTH do dia seguinte no tercil superior da distribuição atleta-dia
    rf = lh.sql("""
        WITH t AS (
          SELECT ID, dia, day_type, hiit_flag, vigor, fadiga, pth,
                 QUANTILE_CONT(pth, 0.66) OVER () AS thr,
                 LEAD(pth) OVER (PARTITION BY ID ORDER BY dia) AS pth_amanha
          FROM ad)
        SELECT ID, dia, day_type, hiit_flag, vigor, fadiga, pth,
               CASE WHEN pth_amanha IS NULL THEN NULL
                    WHEN pth_amanha >= thr THEN 1 ELSE 0 END AS risco_amanha
        FROM t ORDER BY ID, dia
    """, ad=ad)
    lh.write_delta("gold", "risk_features", rf, mode="overwrite")
    lab = rf.dropna(subset=["risco_amanha"])
    print(f"[gold]   risk_features {len(rf)} linhas ({len(lab)} rotuladas p/ ML)")

    # ---- gold.athlete_day_unified — TABELA INTEGRADA (OBT) por atleta-dia (A-code) ----
    #   humor (todos os momentos) + sono/estresse (Epworth/PSS) + carga interna do HIIT do dia
    wb = lh.read_delta("silver", "wellbeing")
    hiit = lh.read_delta("silver", "hiit")
    hiit["dia"] = hiit["sessao"].map(SESS2DIA)
    hiit_day = lh.sql("""SELECT ID, dia, AVG(PSE) hiit_pse, AVG(dFC) hiit_dfc, MAX(FC_pos) hiit_fcmax
                         FROM hiit WHERE dia IS NOT NULL GROUP BY ID, dia""", hiit=hiit)
    obt = lh.sql("""
        SELECT ad.*, wb.epworth, wb.pss,
               hd.hiit_pse, hd.hiit_dfc, hd.hiit_fcmax
        FROM ad LEFT JOIN wb ON ad.ID=wb.ID AND ad.dia=wb.dia
                LEFT JOIN hd ON ad.ID=hd.ID AND ad.dia=hd.dia
        ORDER BY ad.ID, ad.dia
    """, ad=ad, wb=wb, hd=hiit_day)
    lh.write_delta("gold", "athlete_day_unified", obt, mode="overwrite")
    print(f"[gold]   athlete_day_unified {len(obt)} linhas × {obt.shape[1]} colunas (humor+sono+estresse+HIIT)")

    # ---- gold.athlete_profile — resumo por atleta (A-code): humor semanal + RSA + MDC ----
    rsa = lh.read_delta("silver", "rsa"); mdc = lh.read_delta("silver", "mdc")
    prof = lh.sql("""
        WITH m AS (SELECT ID, AVG(vigor) vigor_med, AVG(fadiga) fadiga_med, AVG(pth) pth_med,
                          COUNT(*) n_dias FROM ad GROUP BY ID)
        SELECT m.*, rsa.BkMel, rsa.BkSoma, rsa.BkF,
               mdc.clsVigor, mdc.clsFadiga
        FROM m LEFT JOIN rsa ON m.ID=rsa.ID LEFT JOIN mdc ON m.ID=mdc.ID
        ORDER BY m.ID
    """, ad=ad, rsa=rsa, mdc=mdc)
    lh.write_delta("gold", "athlete_profile", prof, mode="overwrite")
    print(f"[gold]   athlete_profile {len(prof)} atletas (humor + RSA + classificação MDC)")

def run():
    build_silver(); build_gold()

if __name__ == "__main__":
    run()
