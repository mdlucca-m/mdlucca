#!/usr/bin/env python3
"""
scripts/ingest.py

ETL: le data/dashboard_extracted.json (saida de extract_dashboard.py) e
popula o SQLite conforme sql/schema.sql. Idempotente: recria o banco do
zero a cada execucao (com backup do anterior).

Uso:
  python3 scripts/ingest.py \
      --json data/dashboard_extracted.json \
      --schema sql/schema.sql \
      --db data/db.sqlite
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

# Series por-frame que NAO sao numericas continuas (tratadas a parte).
NON_NUMERIC_SERIES = {"phases_sequence"}

# Unidades por serie (fallback quando VAR_CONFIG nao cobre).
SERIES_UNIT_FALLBACK = {
    "t": "s",
    "force_angle": "deg",
    "tangential_accel": "m/s^2",
    "propulsive_velocity": "m/s",
    "force_gravity": "N",
    "force_dynamic": "N",
    "cog_y": "m",
    "cog_speed": "m/s",
    "bar_height_rel_hip": "m",
    "body_speed": "m/s",
    "bar_speed_rel_body": "m/s",
    "hip_3d": "deg",
    "knee_3d": "deg",
    "ankle_3d": "deg",
}

# const de lista-por-rep -> nome da analise em `metric` (chave 'rep').
METRIC_LISTS = {
    "MOMENTS": "moments",
    "ANGVEL_CONSOL": "angular_velocity",
    "BALLISTIC": "ballistic",
    "PROPULSIVE": "propulsive",
    "TDF_RESULTS": "tdf",
    "FORCE_DECOMP": "force_decomposition",
    "VEL_DECOMP": "velocity_decomposition",
    "DERIVADAS": "derivatives",
    "EFFICIENCY": "efficiency",
    "BARBODY": "bar_vs_body",
    "COG_RESULTS": "cog",
    "VBT_ZONES": "vbt",
    "NORMALIZED": "normalized",
    "SSC_RESULTS": "ssc",
    "POWERLAW_PRED": "powerlaw_pred",
    "JOINT_POWER": "joint_power",   # aninhado por articulacao
    "EXTREMES": "extremes",         # aninhado
    "VEL_PHASE": "vel_phase",       # aninhado por fase
}

KIND_BY_LABEL = {
    "Rep 2C (Press)": "press",
    "Rep 2 (completa)": "composite",
}


def flatten(prefix: str, obj) -> list[tuple[str, object]]:
    """Achata dicts aninhados em pares (nome.pontilhado, escalar)."""
    out: list[tuple[str, object]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            name = f"{prefix}.{k}" if prefix else str(k)
            out.extend(flatten(name, v))
    elif isinstance(obj, list):
        # listas escalares viram JSON textual sob o proprio nome
        out.append((prefix, obj))
    else:
        out.append((prefix, obj))
    return out


def add_metric(rows, session_id, sub_id, analysis, name, value):
    if isinstance(value, bool):
        rows.append((session_id, sub_id, analysis, name, None, str(value).lower(), None))
    elif isinstance(value, (int, float)):
        rows.append((session_id, sub_id, analysis, name, float(value), None, None))
    elif isinstance(value, str):
        rows.append((session_id, sub_id, analysis, name, None, value, None))
    elif isinstance(value, list):
        rows.append((session_id, sub_id, analysis, name, None, json.dumps(value), None))
    # None -> ignora


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default="data/dashboard_extracted.json")
    ap.add_argument("--source", default=None,
                    help="fonte de pose (mediapipe|highquality). Ignora --json quando dado.")
    ap.add_argument("--schema", default="sql/schema.sql")
    ap.add_argument("--db", default="data/db.sqlite")
    args = ap.parse_args()

    # Proveniencia: via adaptador de fonte (Etapa 2-ready) ou JSON extraido.
    if args.source:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from importlib import import_module
        from app.sources.highquality import SOURCES
        modpath, clsname = SOURCES[args.source].split(":")
        Source = getattr(import_module(modpath), clsname)()
        d = Source.bundle()
        overrides = Source.session_overrides()
    else:
        d = json.loads(Path(args.json).read_text(encoding="utf-8"))
        overrides = {"pose_source": "mediapipe",
                     "pose_model": "MediaPipe Pose (BlazePose GHUM 3D, monocular)",
                     "is_calibrated": False, "coordinate_system": "image_normalized"}
    schema = Path(args.schema).read_text(encoding="utf-8")

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        bak = db_path.with_suffix(db_path.suffix + f".bak_{ts}")
        shutil.copy2(db_path, bak)
        db_path.unlink()
        print(f"Backup do banco anterior: {bak}")

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(schema)
    cur = con.cursor()

    DATA = d["DATA"]
    LOADCTX = d.get("LOADCTX", {})

    # ---- athlete ----------------------------------------------------------
    cur.execute(
        "INSERT INTO athlete(ext_key,name,body_mass_kg,height_m,bmi) VALUES (?,?,?,?,?)",
        ("atleta2", "Atleta 2", LOADCTX.get("body_mass_kg"),
         LOADCTX.get("height_m"), LOADCTX.get("bmi")),
    )
    athlete_id = cur.lastrowid

    # ---- session ----------------------------------------------------------
    session_meta = {
        "methodology_3d": DATA.get("methodology_3d"),
        "camera_correction": DATA.get("camera_correction"),
        "filter_note": DATA.get("filter_note"),
        "torque_method": DATA.get("torque_method"),
        "cluster_results": DATA.get("cluster_results"),
        "phase_colors": DATA.get("phase_colors"),
        "n_movs": DATA.get("n_movs"),
        "barbell_weight_N": DATA.get("gravity_constant"),
        "is_calibrated": overrides.get("is_calibrated"),
        "coordinate_system": overrides.get("coordinate_system"),
    }
    cur.execute(
        """INSERT INTO session(athlete_id,exercise,load_kg,pct_bodyweight,load_per_height,
               gravity,pose_source,pose_model,n_submovements,captured_at,meta,notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (athlete_id, "Landmine Clean & Press", LOADCTX.get("load_kg"),
         LOADCTX.get("pct_bw"), LOADCTX.get("load_per_height"), 9.81,
         overrides.get("pose_source"), overrides.get("pose_model"),
         len(DATA["efforts"]), None, json.dumps(session_meta, ensure_ascii=False),
         "Dados originados de pose monocular MediaPipe (Etapa 1). Fonte de pose de "
         "alta qualidade planejada para a Etapa 2 (ver README)."),
    )
    session_id = cur.lastrowid

    # ---- variable + variable_series --------------------------------------
    for vkey, cfg in d.get("VAR_CONFIG", {}).items():
        cur.execute(
            "INSERT INTO variable(key,title,unit,multi_axis) VALUES (?,?,?,?)",
            (vkey, cfg.get("title"), cfg.get("unit"), 1 if cfg.get("multiAxis") else 0),
        )
        for i, s in enumerate(cfg.get("series", [])):
            cur.execute(
                "INSERT INTO variable_series(variable_key,series_key,label,color,ord) VALUES (?,?,?,?,?)",
                (vkey, s.get("key"), s.get("label"), s.get("color"), i),
            )
    # mapa serie->unidade a partir do VAR_CONFIG
    unit_map = dict(SERIES_UNIT_FALLBACK)
    for cfg in d.get("VAR_CONFIG", {}).values():
        for s in cfg.get("series", []):
            unit_map.setdefault(s.get("key"), cfg.get("unit"))

    # ---- phase (lookup de cores) -----------------------------------------
    for name, color in (DATA.get("phase_colors") or {}).items():
        cur.execute("INSERT OR IGNORE INTO phase(name,color) VALUES (?,?)", (name, color))

    # ---- submovements + series + peaks + phase_segment -------------------
    sub_id_by_ordinal: dict[int, int] = {}
    metric_rows: list[tuple] = []
    for ef in DATA["efforts"]:
        ordinal = ef["esforco"]
        kind = KIND_BY_LABEL.get(ef["label"], "pull")
        cur.execute(
            """INSERT INTO submovement(session_id,ordinal,label,kind,frame_start,frame_end,
                   n_frames,dt,is_slowmo_2x,idx_transicao,meta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (session_id, ordinal, ef["label"], kind, ef.get("frame_start"),
             ef.get("frame_end"), ef.get("n_frames"), ef.get("dt"),
             1 if ef.get("is_slowmo_2x") else 0, ef.get("idx_transicao"), None),
        )
        sub_id = cur.lastrowid
        sub_id_by_ordinal[ordinal] = sub_id

        for key, val in ef.items():
            if not isinstance(val, list):
                continue
            if key in NON_NUMERIC_SERIES:
                cur.execute(
                    "INSERT INTO dataset(session_id,submovement_id,kind,name,payload) VALUES (?,?,?,?,?)",
                    (session_id, sub_id, "phase_sequence", key, json.dumps(val)),
                )
                continue
            cur.execute(
                "INSERT INTO series(submovement_id,name,unit,n,samples) VALUES (?,?,?,?,?)",
                (sub_id, key, unit_map.get(key), len(val), json.dumps(val)),
            )

        for pk, pv in (ef.get("peaks") or {}).items():
            add_metric(metric_rows, session_id, sub_id, "peaks", pk, pv)

        for i, (pname, pinfo) in enumerate((ef.get("phase_breakdown") or {}).items()):
            cur.execute(
                "INSERT INTO phase_segment(submovement_id,phase,frames,pct,duration_s,ord) VALUES (?,?,?,?,?,?)",
                (sub_id, pname, pinfo.get("frames"), pinfo.get("pct"),
                 pinfo.get("duration_s"), i),
            )

    def sub_of(rep) -> int | None:
        return sub_id_by_ordinal.get(rep)

    # ---- metrics escalares por rep ---------------------------------------
    for const_name, analysis in METRIC_LISTS.items():
        for row in d.get(const_name, []):
            sub = sub_of(row.get("rep"))
            for k, v in row.items():
                if k in ("rep", "label"):
                    continue
                for name, scalar in flatten(k, v):
                    add_metric(metric_rows, session_id, sub, analysis, name, scalar)

    # global_kpis + allometric params (escopo de sessao) --------------------
    for k, v in (DATA.get("global_kpis") or {}).items():
        add_metric(metric_rows, session_id, None, "global_kpi", k, v)
    ALLO = d.get("ALLO", {})
    for k in ("body_mass", "b_force", "b_torque", "force_scale", "torque_scale"):
        if k in ALLO:
            add_metric(metric_rows, session_id, None, "allometric_params", k, ALLO[k])
    for row in ALLO.get("per_rep", []):
        sub = sub_of(row.get("rep"))
        for k, v in row.items():
            if k in ("rep", "label"):
                continue
            add_metric(metric_rows, session_id, sub, "allometric", k, v)

    cur.executemany(
        "INSERT INTO metric(session_id,submovement_id,analysis,name,value_num,value_text,unit) "
        "VALUES (?,?,?,?,?,?,?)",
        metric_rows,
    )

    # ---- fit --------------------------------------------------------------
    fit_rows: list[tuple] = []
    for row in d.get("LOGISTIC", []):
        params = {k: row[k] for k in ("limite_inferior", "limite_superior",
                                      "peak_angvel_analytic", "aic_simples", "aic_dupla")
                  if k in row}
        fit_rows.append((session_id, sub_of(row["rep"]), "logistic", row.get("model"),
                         row.get("r2"), None, json.dumps(params),
                         json.dumps({"fit_ok": row.get("fit_ok")})))
    for row in d.get("ANGULAR_COEF", []):
        params = {"slope": row.get("slope"), "intercept": row.get("intercept")}
        fit_rows.append((session_id, sub_of(row["rep"]), "angular_coef", "linear",
                         row.get("r2"), None, json.dumps(params), None))
    for model, p in (d.get("POWERLAW") or {}).items():
        if not isinstance(p, dict):
            continue  # chaves escalares (n, limitation_note) nao sao modelos
        params = {"a": p.get("a"), "b": p.get("b"), "eq": p.get("eq")}
        fit_rows.append((session_id, None, "powerlaw", model, p.get("r2"),
                         p.get("p"), json.dumps(params), None))
    for model, p in (d.get("BOOTSTRAP_CI") or {}).items():
        params = {"slope_median": p.get("slope_median"), "ci95_low": p.get("ci95_low"),
                  "ci95_high": p.get("ci95_high"),
                  "n_bootstrap_valid": p.get("n_bootstrap_valid"),
                  "includes_zero": p.get("includes_zero")}
        fit_rows.append((session_id, None, "bootstrap_ci", model, None, None,
                         json.dumps(params), None))
    FV = d.get("FV", {})
    if FV:
        fit_rows.append((session_id, None, "force_velocity", "linear", FV.get("r2"),
                         None, json.dumps({"slope": FV.get("slope"),
                                           "intercept": FV.get("intercept")}),
                         json.dumps({"points": FV.get("points")})))
    cur.executemany(
        "INSERT INTO fit(session_id,submovement_id,analysis,model,r2,p_value,params,meta) "
        "VALUES (?,?,?,?,?,?,?,?)",
        fit_rows,
    )

    # ---- sequencing_event -------------------------------------------------
    seq_rows: list[tuple] = []
    for row in d.get("SEQUENCING", []):
        sub = sub_of(row["rep"])
        for phase in ("subida", "descida"):
            for i, pair in enumerate(row.get(phase, [])):
                joint, angvel = pair[0], pair[1]
                seq_rows.append((sub, phase, joint, angvel, i))
    cur.executemany(
        "INSERT INTO sequencing_event(submovement_id,phase,joint,peak_angvel,ord) VALUES (?,?,?,?,?)",
        seq_rows,
    )

    # ---- joint_confidence -------------------------------------------------
    conf_rows: list[tuple] = []
    for row in d.get("CONFIDENCE", []):
        sub = sub_of(row["rep"])
        for joint, c in (row.get("joints") or {}).items():
            conf_rows.append((sub, joint, c.get("mean"), c.get("min"),
                              c.get("pct_low_confidence")))
    cur.executemany(
        "INSERT INTO joint_confidence(submovement_id,joint,mean_vis,min_vis,pct_low_confidence) "
        "VALUES (?,?,?,?,?)",
        conf_rows,
    )

    # ---- literature_reference --------------------------------------------
    lit_rows: list[tuple] = []
    for metric_name, info in (d.get("LITERATURE") or {}).items():
        lit_rows.append((session_id, metric_name, info.get("nosso"), info.get("lit"),
                         info.get("fonte"), info.get("avaliacao"), info.get("cor"),
                         info.get("nota")))
    cur.executemany(
        "INSERT INTO literature_reference(session_id,metric_name,ours,literature,source,rating,color,note) "
        "VALUES (?,?,?,?,?,?,?,?)",
        lit_rows,
    )

    # ---- consistency_source (para recomputo CV/Grubbs/bootstrap) ---------
    cons_rows: list[tuple] = []
    for row in d.get("CV_RESULTS", []):
        cons_rows.append((session_id, "cv", row["metric"], "original_5seg",
                          json.dumps(["Rep 1", "Rep 2A", "Rep 2B", "Rep 3", "Rep 2C"]),
                          json.dumps(row["values"]), row.get("mean"), None, row.get("cv_pct")))
    for row in d.get("CV_CORRECTED", []):
        cons_rows.append((session_id, "cv", row["metric"], "corrected_4seg", None,
                          json.dumps(row["values"]), None, None, row.get("cv_pct")))
    for row in d.get("CV_TODO_VS_PARTES", []):
        cons_rows.append((session_id, "cv", row["metric"], "3reps",
                          json.dumps(["Rep 1", "Rep 2", "Rep 3"]),
                          json.dumps(row["vals_3reps"]), None, None, row.get("cv_3reps")))
        cons_rows.append((session_id, "cv", row["metric"], "5seg", None,
                          json.dumps(row["vals_5seg"]), None, None, row.get("cv_5seg")))
    for row in d.get("OUTLIER_TEST", []):
        cons_rows.append((session_id, "outlier", row["metric"], "grubbs_5seg", None,
                          json.dumps(row["values"]), row.get("mean"), row.get("std"), None))
    cur.executemany(
        "INSERT INTO consistency_source(session_id,analysis,metric_name,scope,labels,values_json,mean,std,cv_pct) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        cons_rows,
    )

    # ---- dataset (estruturas ricas em JSON) ------------------------------
    ds_rows: list[tuple] = []
    for row in d.get("SKELETON", []):
        ds_rows.append((session_id, sub_of(row["rep"]), "skeleton", "skeleton", json.dumps(row)))
    for row in d.get("TRAJ3D", []):
        ds_rows.append((session_id, sub_of(row["rep"]), "trajectory3d", "trajectory3d", json.dumps(row)))
    for row in d.get("LOGISTIC_CURVES", []):
        ds_rows.append((session_id, sub_of(row["rep"]), "logistic_fit_curve", "logistic_curve", json.dumps(row)))
    for name in ("POWERLAW_CURVES", "NORM_CURVES", "MULTIVAR_OPTIONS", "REP2_SPLIT", "SSC_CORRECTED"):
        if name in d:
            ds_rows.append((session_id, None, "meta", name.lower(), json.dumps(d[name], ensure_ascii=False)))
    cur.executemany(
        "INSERT INTO dataset(session_id,submovement_id,kind,name,payload) VALUES (?,?,?,?,?)",
        ds_rows,
    )

    # ---- schema_meta ------------------------------------------------------
    now = datetime.now(timezone.utc).isoformat()
    for k, v in {
        "schema_version": SCHEMA_VERSION,
        "ingested_at": now,
        "source": "Dashboard_Atleta2.html (extract_dashboard.py)",
        "stage": "1 (backend a partir de pose MediaPipe)",
    }.items():
        cur.execute("INSERT OR REPLACE INTO schema_meta(key,value) VALUES (?,?)", (k, v))

    con.commit()

    # ---- relatorio --------------------------------------------------------
    print(f"Banco criado: {db_path}")
    for t in ("athlete", "session", "submovement", "series", "metric", "fit",
              "sequencing_event", "joint_confidence", "phase", "phase_segment",
              "literature_reference", "consistency_source", "dataset",
              "variable", "variable_series"):
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:22s} {n:6d}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
