"""
app/api.py — API REST (FastAPI) do backend biomecanico.

Duas familias de endpoints:
  * Leitura de dados:   /athletes, /sessions, /submovements, /series, /metrics,
                        /fits, /literature, /variables, /datasets ...
  * Analises padrao-ouro recomputadas sob demanda (app.analyses):
                        /compute/* e atalhos como /submovements/{id}/logistic.

Rodar:  uvicorn app.api:app --reload
Docs :  http://localhost:8000/docs   (OpenAPI gerado automaticamente)
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import analyses as A
from app import biomech as Bio
from app import calibration as Cal
from app import db
from app import kinematics as Kin
from app import phases as Ph
from app import reference_values as Ref
from app import segments as Seg
from app import signals as Sig

app = FastAPI(
    title="mdlucca — API Biomecanica (Landmine Clean & Press)",
    version="2.0.0",
    description=(
        "Backend biomecanico: serve os dados de pose/analise antes embutidos no "
        "dashboard HTML e **recomputa as analises padrao-ouro direto das series "
        "brutas** com rigor numerico (numpy/scipy) — integracao trapezoidal, "
        "Savitzky-Golay, bootstrap, nls. Fonte de pose atual: MediaPipe "
        "(monocular). Etapa 2 (roadmap): fonte de pose de alta qualidade."
    ),
)

# CORS liberado para permitir que o cliente web (web/index.html) consuma a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

JOINT_SERIES = {  # articulacao -> (torque, velocidade angular, angulo)
    "hip": ("tau_hip", "hip_angvel", "hip_angle"),
    "knee": ("tau_knee", "knee_angvel", "knee_angle"),
    "elbow": ("tau_elbow", "elbow_angvel", "elbow_angle"),
}


@app.exception_handler(FileNotFoundError)
async def _db_missing_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(status_code=500,
                        content={"detail": f"{type(exc).__name__}: {exc}"})


def _series_map(con, sub_id: int, names: Optional[list[str]] = None) -> dict[str, list]:
    """Carrega as series de um submovimento como {nome: lista}."""
    sql = "SELECT name, samples FROM series WHERE submovement_id=?"
    params: tuple = (sub_id,)
    if names:
        placeholders = ",".join("?" * len(names))
        sql += f" AND name IN ({placeholders})"
        params += tuple(names)
    return {r["name"]: json.loads(r["samples"]) for r in con.execute(sql, params)}


def _session_constants(con, sub_id: int) -> tuple[float, float]:
    """(massa de referencia [kg], g) da sessao dona do submovimento. Usa a
    carga (load_kg) quando existe; senao a massa corporal do atleta (ex.:
    sessoes derivadas de video, cinetica pelo metodo do CoM)."""
    row = con.execute(
        "SELECT COALESCE(s.load_kg, a.body_mass_kg, 0) AS mass, s.gravity "
        "FROM submovement sm JOIN session s ON s.id=sm.session_id "
        "JOIN athlete a ON a.id=s.athlete_id WHERE sm.id=?", (sub_id,)).fetchone()
    if not row:
        raise HTTPException(404, "submovimento nao encontrado")
    return float(row["mass"]), float(row["gravity"])


def _require(sm: dict, *names: str):
    missing = [n for n in names if n not in sm]
    if missing:
        raise HTTPException(422, f"series ausentes para este submovimento: {missing}")


# ==========================================================================
# Meta / navegacao
# ==========================================================================
@app.get("/", tags=["meta"])
def root():
    return {
        "name": "mdlucca biomechanics API",
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": [
            "/health", "/athletes", "/sessions", "/sessions/{id}",
            "/sessions/{id}/submovements", "/submovements/{id}",
            "/submovements/{id}/series", "/submovements/{id}/series/{name}",
            "/submovements/{id}/metrics", "/submovements/{id}/logistic",
            "/submovements/{id}/peak", "/submovements/{id}/sequencing",
            "/submovements/{id}/confidence", "/variables", "/analyses",
            "/metrics", "/fits", "/literature", "/consistency",
            "/datasets", "/datasets/{kind}",
            "/compute/cv", "/compute/grubbs", "/compute/force-velocity",
            "/compute/logistic", "/compute/powerlaw", "/compute/bootstrap-slope",
        ],
        "deep_analysis": [
            "/submovements/{id}/analysis  (painel completo)",
            "/sessions/{id}/analysis",
            "/submovements/{id}/compute/impulse-work",
            "/submovements/{id}/compute/efficiency",
            "/submovements/{id}/compute/rfd-tdf",
            "/submovements/{id}/compute/velocity",
            "/submovements/{id}/compute/ballistic",
            "/submovements/{id}/compute/jerk",
            "/submovements/{id}/compute/joint-power?joint=hip|knee|elbow",
            "/submovements/{id}/compute/ssc?joint=hip|knee|elbow",
            "/submovements/{id}/compute/sequencing",
            "/submovements/{id}/compute/normalized-cycle?series=hip_angle",
        ],
        "kinematics": [
            "/submovements/{id}/kinematics/angles?aspect=auto  (recomputa dos landmarks)",
            "/submovements/{id}/kinematics/cog?aspect=auto",
        ],
        "web_client": "/app",
    }


@app.get("/health", tags=["meta"])
def health():
    try:
        con = db.connect()
        meta = {r["key"]: r["value"] for r in con.execute("SELECT key,value FROM schema_meta")}
        con.close()
        return {"status": "ok", "schema": meta}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"banco indisponivel: {exc}")


# ==========================================================================
# Dimensoes
# ==========================================================================
@app.get("/athletes", tags=["dados"])
def list_athletes():
    con = db.connect()
    try:
        return db.rows(con, "SELECT * FROM athlete ORDER BY id")
    finally:
        con.close()


@app.get("/sessions", tags=["dados"])
def list_sessions():
    con = db.connect()
    try:
        return [db.parse_json_fields(s, ["meta"])
                for s in db.rows(con, "SELECT * FROM session ORDER BY id")]
    finally:
        con.close()


@app.get("/sessions/{session_id}", tags=["dados"])
def get_session(session_id: int):
    con = db.connect()
    try:
        s = db.one(con, "SELECT * FROM session WHERE id=?", (session_id,))
        if not s:
            raise HTTPException(404, "sessao nao encontrada")
        s = db.parse_json_fields(s, ["meta"])
        s["athlete"] = db.one(con, "SELECT * FROM athlete WHERE id=?", (s["athlete_id"],))
        s["submovements"] = db.rows(
            con, "SELECT id,ordinal,label,kind,n_frames,dt FROM submovement "
            "WHERE session_id=? ORDER BY ordinal", (session_id,))
        return s
    finally:
        con.close()


@app.get("/sessions/{session_id}/submovements", tags=["dados"])
def session_submovements(session_id: int):
    con = db.connect()
    try:
        return db.rows(con, "SELECT * FROM submovement WHERE session_id=? ORDER BY ordinal",
                       (session_id,))
    finally:
        con.close()


@app.get("/submovements/{sub_id}", tags=["dados"])
def get_submovement(sub_id: int):
    con = db.connect()
    try:
        s = db.one(con, "SELECT * FROM submovement WHERE id=?", (sub_id,))
        if not s:
            raise HTTPException(404, "submovimento nao encontrado")
        s = db.parse_json_fields(s, ["meta"])
        s["series_available"] = [r["name"] for r in
                                 con.execute("SELECT name FROM series WHERE submovement_id=? ORDER BY name", (sub_id,))]
        return s
    finally:
        con.close()


# ==========================================================================
# Series temporais
# ==========================================================================
@app.get("/submovements/{sub_id}/series", tags=["series"])
def list_series(sub_id: int):
    con = db.connect()
    try:
        return db.rows(con, "SELECT name,unit,n FROM series WHERE submovement_id=? ORDER BY name",
                       (sub_id,))
    finally:
        con.close()


@app.get("/submovements/{sub_id}/series/{name}", tags=["series"])
def get_series(sub_id: int, name: str, with_time: bool = Query(True, description="incluir vetor de tempo 't'")):
    con = db.connect()
    try:
        r = db.one(con, "SELECT name,unit,n,samples FROM series WHERE submovement_id=? AND name=?",
                   (sub_id, name))
        if not r:
            raise HTTPException(404, f"serie '{name}' nao encontrada")
        out = {"submovement_id": sub_id, "name": r["name"], "unit": r["unit"],
               "n": r["n"], "samples": json.loads(r["samples"])}
        if with_time and name != "t":
            t = db.one(con, "SELECT samples FROM series WHERE submovement_id=? AND name='t'", (sub_id,))
            if t:
                out["t"] = json.loads(t["samples"])
        return out
    finally:
        con.close()


# ==========================================================================
# Metricas / fits / literatura / etc.
# ==========================================================================
@app.get("/submovements/{sub_id}/metrics", tags=["metricas"])
def submovement_metrics(sub_id: int, analysis: Optional[str] = None):
    con = db.connect()
    try:
        sql = "SELECT analysis,name,value_num,value_text,unit FROM metric WHERE submovement_id=?"
        params: tuple = (sub_id,)
        if analysis:
            sql += " AND analysis=?"
            params += (analysis,)
        return db.rows(con, sql + " ORDER BY analysis,name", params)
    finally:
        con.close()


@app.get("/metrics", tags=["metricas"])
def query_metrics(analysis: str = Query(...), name: Optional[str] = None,
                  session_id: Optional[int] = None,
                  limit: int = Query(500, ge=1, le=5000), offset: int = Query(0, ge=0)):
    con = db.connect()
    try:
        sql = ("SELECT m.submovement_id, sm.label, m.analysis, m.name, m.value_num, m.value_text, m.unit "
               "FROM metric m LEFT JOIN submovement sm ON sm.id=m.submovement_id WHERE m.analysis=?")
        params: tuple = (analysis,)
        if name:
            sql += " AND m.name=?"
            params += (name,)
        if session_id is not None:
            sql += " AND m.session_id=?"
            params += (session_id,)
        cnt = "SELECT COUNT(*) FROM metric WHERE analysis=?" + (" AND name=?" if name else "") \
            + (" AND session_id=?" if session_id is not None else "")
        total = con.execute(cnt, params).fetchone()[0]
        data = db.rows(con, sql + " ORDER BY sm.ordinal, m.name LIMIT ? OFFSET ?",
                       params + (limit, offset))
        return {"total": total, "limit": limit, "offset": offset, "items": data}
    finally:
        con.close()


@app.get("/analyses", tags=["metricas"])
def list_analyses():
    con = db.connect()
    try:
        return {
            "metric_namespaces": [r["analysis"] for r in
                                  con.execute("SELECT DISTINCT analysis FROM metric ORDER BY analysis")],
            "fit_namespaces": [r["analysis"] for r in
                               con.execute("SELECT DISTINCT analysis FROM fit ORDER BY analysis")],
            "compute_endpoints": ["/compute/cv", "/compute/grubbs", "/compute/force-velocity",
                                  "/compute/logistic", "/compute/powerlaw", "/compute/bootstrap-slope"],
        }
    finally:
        con.close()


@app.get("/fits", tags=["metricas"])
def list_fits(analysis: Optional[str] = None):
    con = db.connect()
    try:
        sql = "SELECT * FROM fit"
        params: tuple = ()
        if analysis:
            sql += " WHERE analysis=?"
            params = (analysis,)
        return [db.parse_json_fields(f, ["params", "meta"])
                for f in db.rows(con, sql + " ORDER BY analysis, submovement_id", params)]
    finally:
        con.close()


@app.get("/literature", tags=["metricas"])
def literature():
    con = db.connect()
    try:
        return db.rows(con, "SELECT metric_name,ours,literature,source,rating,note FROM literature_reference")
    finally:
        con.close()


@app.get("/variables", tags=["metricas"])
def variables():
    con = db.connect()
    try:
        vs = db.rows(con, "SELECT * FROM variable ORDER BY key")
        for v in vs:
            v["series"] = db.rows(
                con, "SELECT series_key,label,color,ord FROM variable_series "
                "WHERE variable_key=? ORDER BY ord", (v["key"],))
        return vs
    finally:
        con.close()


@app.get("/consistency", tags=["metricas"])
def consistency(analysis: Optional[str] = None):
    con = db.connect()
    try:
        sql = "SELECT * FROM consistency_source"
        params: tuple = ()
        if analysis:
            sql += " WHERE analysis=?"
            params = (analysis,)
        return [db.parse_json_fields(c, ["labels", "values_json"])
                for c in db.rows(con, sql + " ORDER BY metric_name, scope", params)]
    finally:
        con.close()


@app.get("/submovements/{sub_id}/sequencing", tags=["metricas"])
def sequencing(sub_id: int):
    con = db.connect()
    try:
        return db.rows(con, "SELECT phase,joint,peak_angvel,ord FROM sequencing_event "
                       "WHERE submovement_id=? ORDER BY phase,ord", (sub_id,))
    finally:
        con.close()


@app.get("/submovements/{sub_id}/confidence", tags=["metricas"])
def confidence(sub_id: int):
    con = db.connect()
    try:
        return db.rows(con, "SELECT joint,mean_vis,min_vis,pct_low_confidence FROM joint_confidence "
                       "WHERE submovement_id=?", (sub_id,))
    finally:
        con.close()


@app.get("/datasets", tags=["dados"])
def list_datasets():
    con = db.connect()
    try:
        return db.rows(con, "SELECT id,kind,name,submovement_id FROM dataset ORDER BY kind,id")
    finally:
        con.close()


@app.get("/datasets/{kind}", tags=["dados"])
def get_datasets(kind: str, name: Optional[str] = None):
    con = db.connect()
    try:
        sql = "SELECT id,kind,name,submovement_id,payload FROM dataset WHERE kind=?"
        params: tuple = (kind,)
        if name:
            sql += " AND name=?"
            params += (name,)
        out = db.rows(con, sql, params)
        if not out:
            raise HTTPException(404, "dataset nao encontrado")
        return [db.parse_json_fields(o, ["payload"]) for o in out]
    finally:
        con.close()


# ==========================================================================
# Analises padrao-ouro recomputadas sob demanda
# ==========================================================================
class ValuesBody(BaseModel):
    values: list[float] = Field(..., min_length=2)
    alpha: float = 0.05


class XYBody(BaseModel):
    x: list[float] = Field(..., min_length=2)
    y: list[float] = Field(..., min_length=2)


class LogisticBody(BaseModel):
    t: list[float] = Field(..., min_length=4)
    theta: list[float] = Field(..., min_length=4)


class BootstrapBody(BaseModel):
    x: list[float] = Field(..., min_length=3)
    y: list[float] = Field(..., min_length=3)
    space: str = "loglog"
    n_boot: int = 5000


def _consistency_values(metric: str, scope: Optional[str]) -> list[float]:
    con = db.connect()
    try:
        sql = "SELECT values_json FROM consistency_source WHERE metric_name=? AND analysis IN ('cv','outlier')"
        params: tuple = (metric,)
        if scope:
            sql += " AND scope=?"
            params += (scope,)
        r = con.execute(sql + " LIMIT 1", params).fetchone()
        if not r:
            raise HTTPException(404, f"sem valores para metric='{metric}' scope='{scope}'")
        return json.loads(r["values_json"])
    finally:
        con.close()


@app.get("/compute/cv", tags=["analises"])
def compute_cv(metric: str = Query(..., description="metric_name em consistency_source"),
               scope: Optional[str] = None):
    """CV% + IC bootstrap recomputados a partir dos valores-fonte armazenados."""
    return {"metric": metric, "scope": scope,
            "result": A.coefficient_of_variation(_consistency_values(metric, scope))}


@app.get("/compute/grubbs", tags=["analises"])
def compute_grubbs(metric: str = Query(...), scope: Optional[str] = None, alpha: float = 0.05):
    """Teste de Grubbs bilateral com valor critico exato (via distribuicao t)."""
    return {"metric": metric, "scope": scope,
            "result": A.grubbs_test(_consistency_values(metric, scope), alpha=alpha)}


@app.get("/compute/force-velocity", tags=["analises"])
def compute_force_velocity(n_boot: int = 5000):
    """Perfil Forca-Velocidade: lei de potencia F=a*v^b + IC bootstrap do
    expoente, recomputados a partir dos pontos (v, F) por repeticao."""
    con = db.connect()
    try:
        r = con.execute("SELECT meta FROM fit WHERE analysis='force_velocity' LIMIT 1").fetchone()
        if not r:
            raise HTTPException(404, "pontos F-V nao encontrados")
        pts = json.loads(r["meta"])["points"]
    finally:
        con.close()
    v = [p["v"] for p in pts]
    f = [p["f"] for p in pts]
    return {
        "points": pts,
        "linear": A.linear_regression(v, f),
        "powerlaw": A.powerlaw_fit(v, f),
        "bootstrap_slope_loglog": A.bootstrap_slope_ci(v, f, space="loglog", n_boot=n_boot),
    }


@app.get("/submovements/{sub_id}/logistic", tags=["analises"])
def submovement_logistic(sub_id: int, series: str = "hip_angle"):
    """Ajuste logistico (nls) da fase concentrica de uma serie angular,
    recomputado da serie bruta. Janela concentrica = do minimo ao maximo."""
    con = db.connect()
    try:
        y = db.one(con, "SELECT samples FROM series WHERE submovement_id=? AND name=?", (sub_id, series))
        t = db.one(con, "SELECT samples FROM series WHERE submovement_id=? AND name='t'", (sub_id,))
        if not y or not t:
            raise HTTPException(404, "serie ou vetor de tempo ausente")
    finally:
        con.close()
    yv = json.loads(y["samples"])
    tv = json.loads(t["samples"])
    lo = yv.index(min(yv))
    hi = lo + yv[lo:].index(max(yv[lo:]))
    if hi - lo < 3:
        raise HTTPException(422, "janela concentrica curta demais para ajuste")
    res = A.logistic_fit(tv[lo:hi + 1], yv[lo:hi + 1])
    res["window_index"] = [lo, hi]
    res["series"] = series
    return res


@app.get("/submovements/{sub_id}/peak", tags=["analises"])
def submovement_peak(sub_id: int, series: str = "force", half_window: int = 2):
    con = db.connect()
    try:
        r = db.one(con, "SELECT samples,unit FROM series WHERE submovement_id=? AND name=?", (sub_id, series))
        if not r:
            raise HTTPException(404, f"serie '{series}' nao encontrada")
    finally:
        con.close()
    res = A.robust_peak(json.loads(r["samples"]), half_window=half_window)
    res["unit"] = r["unit"]
    res["series"] = series
    return res


# ==========================================================================
# Analises PROFUNDAS recomputadas a partir das series brutas
# ==========================================================================
@app.get("/submovements/{sub_id}/compute/impulse-work", tags=["analises-profundas"])
def deep_impulse_work(sub_id: int):
    con = db.connect()
    try:
        mass, g = _session_constants(con, sub_id)
        sm = _series_map(con, sub_id, ["force", "speed", "power", "t"])
    finally:
        con.close()
    _require(sm, "force", "speed", "power", "t")
    return Bio.impulse_work(sm["force"], sm["speed"], sm["power"], sm["t"], mass, g)


@app.get("/submovements/{sub_id}/compute/efficiency", tags=["analises-profundas"])
def deep_efficiency(sub_id: int, height_series: str = "bar_height_rel_hip"):
    con = db.connect()
    try:
        mass, g = _session_constants(con, sub_id)
        sm = _series_map(con, sub_id, ["power", height_series, "t"])
    finally:
        con.close()
    _require(sm, "power", height_series, "t")
    return Bio.efficiency(sm["power"], sm[height_series], sm["t"], mass, g)


@app.get("/submovements/{sub_id}/compute/rfd-tdf", tags=["analises-profundas"])
def deep_rfd_tdf(sub_id: int, onset: Literal["bottom", "threshold"] = "bottom"):
    """RFD de pico + TDF (0-50/100/150/200ms). onset='bottom' usa o fundo do
    movimento (min do angulo de quadril) como inicio da fase concentrica."""
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, ["force", "hip_angle", "t"])
    finally:
        con.close()
    _require(sm, "force", "t")
    onset_idx = None
    if onset == "bottom" and "hip_angle" in sm:
        onset_idx = int(Sig.as_array(sm["hip_angle"]).argmin())
    return Bio.rfd_tdf(sm["force"], sm["t"], onset_index=onset_idx)


@app.get("/submovements/{sub_id}/compute/velocity", tags=["analises-profundas"])
def deep_velocity(sub_id: int):
    con = db.connect()
    try:
        _, g = _session_constants(con, sub_id)
        sm = _series_map(con, sub_id, ["speed", "tangential_accel", "t"])
    finally:
        con.close()
    _require(sm, "speed", "tangential_accel", "t")
    return Bio.velocity_metrics(sm["speed"], sm["tangential_accel"], sm["t"], g)


@app.get("/submovements/{sub_id}/compute/ballistic", tags=["analises-profundas"])
def deep_ballistic(sub_id: int):
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, ["tangential_accel", "force", "t"])
    finally:
        con.close()
    _require(sm, "tangential_accel", "force", "t")
    return Bio.ballistic(sm["tangential_accel"], sm["force"], sm["t"])


@app.get("/submovements/{sub_id}/compute/jerk", tags=["analises-profundas"])
def deep_jerk(sub_id: int, smooth_window: int = 21):
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, ["accel", "t"])
    finally:
        con.close()
    _require(sm, "accel", "t")
    return Bio.jerk(sm["accel"], sm["t"], smooth_window=smooth_window)


@app.get("/submovements/{sub_id}/compute/joint-power", tags=["analises-profundas"])
def deep_joint_power(sub_id: int, joint: Literal["hip", "knee", "elbow"] = "hip"):
    tau, angvel, _ = JOINT_SERIES[joint]
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, [tau, angvel, "t"])
    finally:
        con.close()
    _require(sm, tau, angvel, "t")
    return {"joint": joint, **Bio.joint_power(sm[tau], sm[angvel], sm["t"])}


@app.get("/submovements/{sub_id}/compute/ssc", tags=["analises-profundas"])
def deep_ssc(sub_id: int, joint: Literal["hip", "knee", "elbow"] = "hip"):
    _, angvel, angle = JOINT_SERIES[joint]
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, [angle, angvel, "speed", "t"])
    finally:
        con.close()
    _require(sm, angle, angvel, "speed", "t")
    return {"joint": joint, **Bio.ssc(sm[angle], sm[angvel], sm["speed"], sm["t"])}


@app.get("/submovements/{sub_id}/compute/sequencing", tags=["analises-profundas"])
def deep_sequencing(sub_id: int):
    con = db.connect()
    try:
        sm = _series_map(con, sub_id,
                         ["hip_angvel", "knee_angvel", "elbow_angvel", "ankle_angvel",
                          "wrist_angvel", "hip_angle", "t"])
    finally:
        con.close()
    _require(sm, "hip_angvel", "t")
    joints = {j: sm[f"{j}_angvel"] for j in ("hip", "knee", "elbow", "ankle", "wrist")
              if f"{j}_angvel" in sm}
    window = None
    if "hip_angle" in sm:  # janela concentrica (fundo -> extensao)
        window = Sig.concentric_window(sm["hip_angle"])
    return {"concentric_window_index": window, **Bio.sequencing(joints, sm["t"], window)}


@app.get("/submovements/{sub_id}/compute/normalized-cycle", tags=["analises-profundas"])
def deep_normalized_cycle(sub_id: int, series: str = "hip_angle", n: int = 101):
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, [series])
    finally:
        con.close()
    _require(sm, series)
    return {"series": series, "n": n, "x_pct": [round(i * 100 / (n - 1), 2) for i in range(n)],
            "y": Bio.normalized_cycle(sm[series], n)}


@app.get("/submovements/{sub_id}/analysis", tags=["analises-profundas"])
def deep_panel(sub_id: int):
    """Painel completo: roda TODAS as analises profundas disponiveis para o
    submovimento, recomputadas das series brutas."""
    con = db.connect()
    try:
        mass, g = _session_constants(con, sub_id)
        sm = _series_map(con, sub_id)
        label = db.one(con, "SELECT label,kind FROM submovement WHERE id=?", (sub_id,))
    finally:
        con.close()
    if not sm:
        raise HTTPException(404, "submovimento sem series")
    t = sm.get("t")
    panel: dict = {"submovement_id": sub_id, **(label or {})}

    def safe(name, fn):
        try:
            panel[name] = fn()
        except Exception as exc:  # noqa: BLE001
            panel[name] = {"error": f"{type(exc).__name__}: {exc}"}

    if all(k in sm for k in ("force", "speed", "power")):
        safe("impulse_work", lambda: Bio.impulse_work(sm["force"], sm["speed"], sm["power"], t, mass, g))
    if "power" in sm and "bar_height_rel_hip" in sm:
        safe("efficiency", lambda: Bio.efficiency(sm["power"], sm["bar_height_rel_hip"], t, mass, g))
    if "force" in sm:
        onset = int(Sig.as_array(sm["hip_angle"]).argmin()) if "hip_angle" in sm else None
        safe("rfd_tdf", lambda: Bio.rfd_tdf(sm["force"], t, onset_index=onset))
    if "speed" in sm and "tangential_accel" in sm:
        safe("velocity", lambda: Bio.velocity_metrics(sm["speed"], sm["tangential_accel"], t, g))
        safe("ballistic", lambda: Bio.ballistic(sm["tangential_accel"], sm["force"], t))
    if "accel" in sm:
        safe("jerk", lambda: Bio.jerk(sm["accel"], t))
    panel["joint_power"] = {}
    for j, (tau, angvel, _a) in JOINT_SERIES.items():
        if tau in sm and angvel in sm:
            try:
                panel["joint_power"][j] = Bio.joint_power(sm[tau], sm[angvel], t)
            except Exception as exc:  # noqa: BLE001
                panel["joint_power"][j] = {"error": str(exc)}
    if all(k in sm for k in ("hip_angle", "hip_angvel", "speed")):
        safe("ssc_hip", lambda: Bio.ssc(sm["hip_angle"], sm["hip_angvel"], sm["speed"], t))
    if "hip_angvel" in sm:
        joints = {jj: sm[f"{jj}_angvel"] for jj in ("hip", "knee", "elbow", "ankle", "wrist")
                  if f"{jj}_angvel" in sm}
        win = Sig.concentric_window(sm["hip_angle"]) if "hip_angle" in sm else None
        safe("sequencing", lambda: Bio.sequencing(joints, t, win))
    return panel


@app.get("/sessions/{session_id}/analysis", tags=["analises-profundas"])
def session_panel(session_id: int):
    """Agrega o painel profundo de todos os submovimentos da sessao."""
    con = db.connect()
    try:
        subs = db.rows(con, "SELECT id,ordinal,label FROM submovement WHERE session_id=? ORDER BY ordinal",
                       (session_id,))
    finally:
        con.close()
    if not subs:
        raise HTTPException(404, "sessao sem submovimentos")
    return {"session_id": session_id,
            "submovements": [{**s, "analysis": deep_panel(s["id"])} for s in subs]}


# ==========================================================================
# Cinematica: recomputa angulos/CoG a partir dos LANDMARKS (ponte Etapa 2)
# ==========================================================================
def _skeleton(con, sub_id: int) -> dict:
    r = con.execute("SELECT payload FROM dataset WHERE submovement_id=? AND kind='skeleton'",
                    (sub_id,)).fetchone()
    if not r:
        raise HTTPException(404, "esqueleto (landmarks) nao disponivel para este submovimento")
    return json.loads(r["payload"])


def _resolve_aspect(con, sub_id: int, aspect: str, skeleton: dict):
    """aspect='auto' recupera o fator ajustando aos angulos armazenados;
    caso contrario usa o float informado."""
    if aspect != "auto":
        try:
            return float(aspect), None
        except ValueError:
            raise HTTPException(422, "aspect deve ser 'auto' ou um numero")
    ref = {}
    for j in ("hip", "knee", "elbow"):
        row = con.execute("SELECT samples FROM series WHERE submovement_id=? AND name=?",
                          (sub_id, f"{j}_angle")).fetchone()
        if row:
            ref[j] = json.loads(row["samples"])
    fit = Kin.fit_aspect(skeleton, ref) if ref else {"aspect": 1.0}
    return fit["aspect"], (ref or None)


@app.get("/submovements/{sub_id}/kinematics/angles", tags=["cinematica"])
def kinematics_angles(sub_id: int, aspect: str = "auto", validate: bool = True):
    """Recomputa os angulos articulares a partir dos landmarks de pose.
    aspect='auto' recupera o aspect ratio faltante (calibracao) ajustando aos
    angulos armazenados; retorna correlacao/RMSE vs armazenado quando validate."""
    con = db.connect()
    try:
        sk = _skeleton(con, sub_id)
        asp, ref = _resolve_aspect(con, sub_id, aspect, sk)
        angles = Kin.angles_from_landmarks(sk, asp)
        out = {"submovement_id": sub_id, "aspect": asp, "source": "landmarks (MediaPipe)",
               "angles": angles}
        if validate and ref:
            out["validation_vs_stored"] = Kin.validate_against(sk, ref, asp)
        return out
    finally:
        con.close()


@app.get("/submovements/{sub_id}/kinematics/cog", tags=["cinematica"])
def kinematics_cog(sub_id: int, aspect: str = "auto"):
    """Trajetoria do centro de gravidade (De Leva 1996) a partir dos landmarks."""
    con = db.connect()
    try:
        sk = _skeleton(con, sub_id)
        asp, _ = _resolve_aspect(con, sub_id, aspect, sk)
        return {"submovement_id": sub_id, **Kin.center_of_mass(sk, asp)}
    finally:
        con.close()


# ==========================================================================
# Automacao (estilo n8n): dispara o pipeline video->analises via API
# ==========================================================================
_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE = _ROOT / "scripts" / "pipeline.py"
_JOBS: dict[str, dict] = {}


class PipelineReq(BaseModel):
    video: str                                   # caminho do arquivo de video
    athlete: str = "Atleta"
    exercise: str = "Video"
    mass: float = 80.0
    model: Optional[str] = None                  # pose_landmarker_*.task (ou env MDLUCCA_POSE_MODEL)
    legs3d: bool = False
    key: Optional[str] = None


@app.post("/pipeline/run", tags=["pipeline"])
def pipeline_run(body: PipelineReq):
    """Dispara o pipeline completo em background e devolve um job_id.
    Node n8n: HTTP Request POST -> depois faz polling em /pipeline/jobs/{id}."""
    video = Path(body.video)
    if not video.exists():
        raise HTTPException(422, f"video nao encontrado: {body.video}")
    model = body.model or os.environ.get("MDLUCCA_POSE_MODEL")
    if not model or not Path(model).exists():
        raise HTTPException(422, "modelo de pose ausente (body.model ou env MDLUCCA_POSE_MODEL)")
    job_id = uuid.uuid4().hex[:12]
    key = body.key or video.stem.split("_")[0][:12]
    out = _ROOT / "data" / "out"
    cmd = [sys.executable, str(_PIPELINE), "--video", str(video), "--model", model,
           "--athlete", body.athlete, "--exercise", body.exercise, "--mass", str(body.mass),
           "--out", str(out), "--key", key, "--db", str(db.db_path())]
    if body.legs3d:
        cmd.append("--legs3d")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    _JOBS[job_id] = {"proc": proc, "video": str(video), "key": key,
                     "manifest": str(out / f"manifest_{key}.json"), "started": time.time()}
    return {"job_id": job_id, "status": "running", "manifest": _JOBS[job_id]["manifest"]}


@app.get("/pipeline/jobs", tags=["pipeline"])
def pipeline_jobs():
    res = []
    for jid, j in _JOBS.items():
        rc = j["proc"].poll()
        res.append({"job_id": jid, "key": j["key"], "video": j["video"],
                    "status": "running" if rc is None else ("done" if rc == 0 else "error"),
                    "elapsed_s": round(time.time() - j["started"], 1)})
    return res


@app.get("/pipeline/jobs/{job_id}", tags=["pipeline"])
def pipeline_job(job_id: str):
    j = _JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "job nao encontrado")
    rc = j["proc"].poll()
    status = "running" if rc is None else ("done" if rc == 0 else "error")
    out = {"job_id": job_id, "status": status, "returncode": rc,
           "elapsed_s": round(time.time() - j["started"], 1)}
    mp = Path(j["manifest"])
    if status != "running" and mp.exists():
        out["manifest"] = json.loads(mp.read_text())
    return out


# ==========================================================================
# Calibracao metrica, filtragem/ruido e ajuste alometrico
# ==========================================================================
class RefBody(BaseModel):
    p1: list[float]; p2: list[float]; known_length_m: float; ground_px: Optional[float] = None


class StatBody(BaseModel):
    nose: list[float]; ankle: list[float]; stature_m: float; ground_px: Optional[float] = None


def _cal_out(c: Cal.Calibration) -> dict:
    return {"m_per_px": round(c.m_per_px, 6), "cm_per_px": round(c.m_per_px * 100, 4),
            "source": c.source, "ground_px": c.ground_px, "detail": c.detail}


@app.post("/calibrate/reference", tags=["calibracao"])
def calibrate_reference(b: RefBody):
    """Escala metrica por objeto de tamanho conhecido no quadro (regua/barra)."""
    try:
        return _cal_out(Cal.from_reference(b.p1, b.p2, b.known_length_m, b.ground_px))
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/calibrate/stature", tags=["calibracao"])
def calibrate_stature(b: StatBody):
    """Escala metrica pela estatura real do atleta (nariz->tornozelo em px)."""
    try:
        return _cal_out(Cal.from_stature(b.nose, b.ankle, b.stature_m, b.ground_px))
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/submovements/{sub_id}/filtered", tags=["sinais"])
def filtered_series(sub_id: int, series: str = "hip_angle", cutoff: float = 6.0):
    """Serie bruta x filtrada (Butterworth passa-baixa, fase zero) + metricas
    de ruido e analise de residuo para escolher a frequencia de corte."""
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, [series, "t"])
    finally:
        con.close()
    _require(sm, series, "t")
    t = Sig.as_array(sm["t"]); raw = Sig.as_array(sm[series])
    dt = float(np.median(np.diff(t))) if t.size > 1 else 0.033
    fs = 1.0 / dt if dt > 0 else 30.0
    filt = Sig.butter_lowpass(raw, fs, cutoff)
    return {
        "series": series, "fs_hz": round(fs, 2), "cutoff_hz": cutoff, "n": int(raw.size),
        "raw": [round(float(x), 4) for x in raw],
        "filtered": [round(float(x), 4) for x in filt],
        "noise": Sig.noise_metrics(raw, fs, cutoff),
        "residual_analysis": Sig.residual_analysis(raw, fs),
    }


@app.get("/sessions/{session_id}/allometric", tags=["analises"])
def session_allometric(session_id: int, b_force: float = 0.67, b_power: float = 1.0):
    """Ajuste alometrico (Jaric, 2002): normaliza forca e potencia de pico pela
    massa corporal elevada ao expoente alometrico, permitindo comparar atletas
    de tamanhos diferentes de forma justa."""
    con = db.connect()
    try:
        s = db.one(con, "SELECT s.id, a.body_mass_kg, a.name FROM session s "
                   "JOIN athlete a ON a.id=s.athlete_id WHERE s.id=?", (session_id,))
        if not s:
            raise HTTPException(404, "sessao nao encontrada")
        kpis = {r["name"]: r["value_num"] for r in con.execute(
            "SELECT name, value_num FROM metric WHERE session_id=? AND analysis='global_kpi'", (session_id,))}
    finally:
        con.close()
    mass = s["body_mass_kg"]
    if not mass:
        raise HTTPException(422, "massa corporal do atleta desconhecida")
    out = {"session_id": session_id, "athlete": s["name"], "body_mass_kg": mass,
           "exponents": {"force": b_force, "power": b_power}, "normalized": {}}
    if kpis.get("peak_force") is not None:
        out["normalized"]["force_allo_N_per_kg^b"] = round(
            A.allometric_scale(kpis["peak_force"], mass, b_force), 3)
    if kpis.get("peak_power") is not None:
        out["normalized"]["power_allo_W_per_kg^b"] = round(
            A.allometric_scale(kpis["peak_power"], mass, b_power), 3)
    out["raw_peaks"] = {k: kpis.get(k) for k in ("peak_force", "peak_power", "peak_speed")}
    return out


# ==========================================================================
# Padroes de literatura e valores de referencia
# ==========================================================================
class RefCheckBody(BaseModel):
    measurements: dict[str, float]           # {"knee_extension_deg": 175, "split_angle_deg": 146, ...}


@app.get("/standards", tags=["referencia"])
def standards():
    """Padroes metodologicos de literatura internacional que o sistema segue
    (filtragem, antropometria, angulos ISB, alometria, amostragem, VBT, RFD)."""
    return {"standards": Ref.STANDARDS, "reference_bands": list(Ref.BANDS.keys())}


@app.get("/reference-bands", tags=["referencia"])
def reference_bands():
    return Ref.BANDS


@app.post("/reference-check", tags=["referencia"])
def reference_check(body: RefCheckBody):
    """Compara medicoes com as faixas de referencia (criterio tecnico/indicativo)
    e devolve status por metrica com a fonte."""
    return {"results": [Ref.evaluate(k, v) for k, v in body.measurements.items()]}


# ==========================================================================
# Configuravel: segmentos, fases (concentrica/excentrica), elastico, medir
# ==========================================================================
@app.get("/segments", tags=["configuravel"])
def segments_catalog():
    """Vocabulario de segmentos/pontos anatomicos e grupos (ex.: 'sem_bracos')
    para escolher o que incluir na analise/desenho."""
    return Seg.catalog()


@app.get("/submovements/{sub_id}/phases", tags=["configuravel"])
def submovement_phases(sub_id: int, series: str = "cog_y",
                       vmin_frac: float = 0.08, min_dur: float = 0.10):
    """Transicoes concentrica<->excentrica ao longo do movimento (robusto)."""
    con = db.connect()
    try:
        sm = _series_map(con, sub_id, [series, "t"])
    finally:
        con.close()
    _require(sm, series, "t")
    return Ph.detect_phases(sm[series], sm["t"], vmin_frac=vmin_frac, min_dur=min_dur)


@app.get("/submovements/{sub_id}/elastic", tags=["configuravel"])
def submovement_elastic(sub_id: int, series: str = "cog_y", power: str = "power"):
    """Componente elastico (SSC): amortizacao, trabalho excentrico x concentrico
    e razao de utilizacao elastica (EUR) por transicao."""
    con = db.connect()
    try:
        names = [series, "t"] + ([power] if power else [])
        sm = _series_map(con, sub_id, names)
    finally:
        con.close()
    _require(sm, series, "t")
    ph = Ph.detect_phases(sm[series], sm["t"])
    return {"phases": ph, "elastic": Ph.elastic_metrics(sm[series], sm["t"], ph, sm.get(power))}


class MeasureBody(BaseModel):
    include_segments: Optional[object] = None       # str (grupo) ou lista de segmentos
    measures: list[str] = ["impulso_trabalho", "velocidade_angular", "fases", "elastico"]
    joint: str = "hip"
    phase_series: str = "cog_y"


MEASURE_CATALOG = ["impulso_trabalho", "velocidade_angular", "velocidade", "balistico",
                   "jerk", "potencia_articular", "ssc", "fases", "elastico", "sequenciamento"]


@app.post("/submovements/{sub_id}/measure", tags=["configuravel"])
def submovement_measure(sub_id: int, body: MeasureBody):
    """Roda SOMENTE as medidas escolhidas, sobre os segmentos escolhidos.
    'com ou sem bracos' + 'o que medir' como opcao, num unico endpoint."""
    sel = Seg.resolve(body.include_segments)
    con = db.connect()
    try:
        mass, g = _session_constants(con, sub_id)
        sm = _series_map(con, sub_id)
    finally:
        con.close()
    if not sm:
        raise HTTPException(404, "submovimento sem series")
    t = sm.get("t")
    out = {"submovement_id": sub_id, "segmentos": sel["segments"],
           "articulacoes_disponiveis": sel["joints"], "resultados": {}}
    want = set(body.measures)

    def has(*names):
        return all(nm in sm for nm in names)

    if "impulso_trabalho" in want and has("force", "speed", "power"):
        out["resultados"]["impulso_trabalho"] = Bio.impulse_work(sm["force"], sm["speed"], sm["power"], t, mass, g)
    if "velocidade_angular" in want:
        out["resultados"]["velocidade_angular"] = {
            j: round(float(np.nanmax(np.abs(sm[f"{j}_angvel"]))), 1)
            for j in ("hip", "knee", "elbow", "ankle") if f"{j}_angvel" in sm}
    if "velocidade" in want and has("speed", "tangential_accel"):
        out["resultados"]["velocidade"] = Bio.velocity_metrics(sm["speed"], sm["tangential_accel"], t, g)
    if "balistico" in want and has("tangential_accel", "force"):
        out["resultados"]["balistico"] = Bio.ballistic(sm["tangential_accel"], sm["force"], t)
    if "jerk" in want and has("accel"):
        out["resultados"]["jerk"] = Bio.jerk(sm["accel"], t)
    if "potencia_articular" in want:
        j = body.joint
        tau, angvel = f"tau_{j}", f"{j}_angvel"
        if has(tau, angvel):
            out["resultados"]["potencia_articular"] = {"joint": j, **Bio.joint_power(sm[tau], sm[angvel], t)}
    if "ssc" in want and has(f"{body.joint}_angle", f"{body.joint}_angvel", "speed"):
        j = body.joint
        out["resultados"]["ssc"] = Bio.ssc(sm[f"{j}_angle"], sm[f"{j}_angvel"], sm["speed"], t)
    if "fases" in want and body.phase_series in sm:
        out["resultados"]["fases"] = Ph.detect_phases(sm[body.phase_series], t)
    if "elastico" in want and body.phase_series in sm:
        ph = Ph.detect_phases(sm[body.phase_series], t)
        out["resultados"]["elastico"] = Ph.elastic_metrics(sm[body.phase_series], t, ph, sm.get("power"))
    if "sequenciamento" in want:
        joints = {j: sm[f"{j}_angvel"] for j in ("hip", "knee", "elbow", "ankle") if f"{j}_angvel" in sm}
        if joints:
            out["resultados"]["sequenciamento"] = Bio.sequencing(joints, t)
    out["medidas_disponiveis"] = MEASURE_CATALOG
    return out


@app.post("/compute/cv", tags=["analises"])
def post_cv(body: ValuesBody):
    return A.coefficient_of_variation(body.values, alpha=body.alpha)


@app.post("/compute/grubbs", tags=["analises"])
def post_grubbs(body: ValuesBody):
    return A.grubbs_test(body.values, alpha=body.alpha)


@app.post("/compute/powerlaw", tags=["analises"])
def post_powerlaw(body: XYBody):
    return A.powerlaw_fit(body.x, body.y)


@app.post("/compute/logistic", tags=["analises"])
def post_logistic(body: LogisticBody):
    return A.logistic_fit(body.t, body.theta)


@app.post("/compute/bootstrap-slope", tags=["analises"])
def post_bootstrap(body: BootstrapBody):
    return A.bootstrap_slope_ci(body.x, body.y, space=body.space, n_boot=body.n_boot)


# ==========================================================================
# Camada de PRODUTO: cadastro de alunos, sessoes e links compartilhaveis
# (escrita no banco via db.connect_rw). Nao altera o motor de analise.
# ==========================================================================
class AthleteIn(BaseModel):
    name: str = Field(..., min_length=1)
    body_mass_kg: Optional[float] = None
    height_m: Optional[float] = None
    sex: Optional[str] = None
    notes: Optional[str] = None


class SessionIn(BaseModel):
    athlete_id: int
    exercise: str = Field(..., min_length=1)
    load_kg: Optional[float] = None
    notes: Optional[str] = None


class ShareIn(BaseModel):
    kind: Literal["session", "submovement"] = "session"
    ref_id: int
    audience: Literal["atleta", "treinador", "ambos"] = "ambos"
    title: Optional[str] = None


def _bmi(mass: Optional[float], height: Optional[float]) -> Optional[float]:
    if mass and height and height > 0:
        return round(mass / (height * height), 1)
    return None


@app.post("/athletes", tags=["cadastro"])
def create_athlete(a: AthleteIn):
    con = db.connect_rw()
    try:
        cur = con.execute(
            "INSERT INTO athlete (name, body_mass_kg, height_m, bmi, sex, notes) "
            "VALUES (?,?,?,?,?,?)",
            (a.name, a.body_mass_kg, a.height_m, _bmi(a.body_mass_kg, a.height_m),
             a.sex, a.notes),
        )
        con.commit()
        new_id = cur.lastrowid
        return dict(con.execute("SELECT * FROM athlete WHERE id=?", (new_id,)).fetchone())
    finally:
        con.close()


@app.post("/athletes/{athlete_id}/update", tags=["cadastro"])
def update_athlete(athlete_id: int, a: AthleteIn):
    con = db.connect_rw()
    try:
        if not con.execute("SELECT 1 FROM athlete WHERE id=?", (athlete_id,)).fetchone():
            raise HTTPException(404, "aluno nao encontrado")
        con.execute(
            "UPDATE athlete SET name=?, body_mass_kg=?, height_m=?, bmi=?, sex=?, notes=? "
            "WHERE id=?",
            (a.name, a.body_mass_kg, a.height_m, _bmi(a.body_mass_kg, a.height_m),
             a.sex, a.notes, athlete_id),
        )
        con.commit()
        return dict(con.execute("SELECT * FROM athlete WHERE id=?", (athlete_id,)).fetchone())
    finally:
        con.close()


@app.post("/athletes/{athlete_id}/delete", tags=["cadastro"])
def delete_athlete(athlete_id: int):
    con = db.connect_rw()
    try:
        n = con.execute("SELECT COUNT(*) FROM session WHERE athlete_id=?",
                        (athlete_id,)).fetchone()[0]
        if n:
            raise HTTPException(409, f"aluno tem {n} sessao(oes); remova-as antes")
        con.execute("DELETE FROM athlete WHERE id=?", (athlete_id,))
        con.commit()
        return {"deleted": athlete_id}
    finally:
        con.close()


@app.post("/sessions", tags=["cadastro"])
def create_session(s: SessionIn):
    con = db.connect_rw()
    try:
        ath = con.execute("SELECT body_mass_kg FROM athlete WHERE id=?",
                          (s.athlete_id,)).fetchone()
        if not ath:
            raise HTTPException(404, "aluno nao encontrado")
        pct = None
        if s.load_kg and ath["body_mass_kg"]:
            pct = round(100.0 * s.load_kg / ath["body_mass_kg"], 1)
        cur = con.execute(
            "INSERT INTO session (athlete_id, exercise, load_kg, pct_bodyweight, "
            "gravity, pose_source, n_submovements, captured_at, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (s.athlete_id, s.exercise, s.load_kg, pct, 9.81, "manual", 0,
             datetime.now(timezone.utc).isoformat(), s.notes),
        )
        con.commit()
        return dict(con.execute("SELECT * FROM session WHERE id=?",
                                (cur.lastrowid,)).fetchone())
    finally:
        con.close()


@app.post("/shares", tags=["compartilhar"])
def create_share(s: ShareIn, request: Request):
    con = db.connect_rw()
    try:
        tbl = "session" if s.kind == "session" else "submovement"
        if not con.execute(f"SELECT 1 FROM {tbl} WHERE id=?", (s.ref_id,)).fetchone():
            raise HTTPException(404, f"{s.kind} {s.ref_id} nao encontrado")
        token = secrets.token_urlsafe(8)
        con.execute(
            "INSERT INTO share (token, kind, ref_id, title, audience, created_at, views) "
            "VALUES (?,?,?,?,?,?,0)",
            (token, s.kind, s.ref_id, s.title, s.audience,
             datetime.now(timezone.utc).isoformat()),
        )
        con.commit()
        base = str(request.base_url).rstrip("/")
        return {"token": token, "url": f"{base}/r/{token}",
                "kind": s.kind, "ref_id": s.ref_id, "audience": s.audience}
    finally:
        con.close()


@app.get("/shares", tags=["compartilhar"])
def list_shares():
    con = db.connect_rw()
    try:
        return db.rows(con, "SELECT * FROM share ORDER BY created_at DESC")
    finally:
        con.close()


# --- Renderizacao do relatorio compartilhavel (HTML autossuficiente) --------
# Cada coluna tenta uma lista de nomes candidatos (varia entre sessoes) e usa
# o primeiro que existir. Robusto p/ sessoes de dashboard e de video.
_HEADLINE = [
    ("Potencia pico", [("peaks", "power_peak"), ("peaks", "P_peak")]),
    ("Forca pico", [("peaks", "F_peak"), ("peaks", "force_dynamic_peak")]),
    ("Velocidade pico", [("peaks", "v_peak"), ("derivatives", "v_peak")]),
    ("RFD pico", [("peaks", "RFD_peak")]),
    ("Vel.ang. quadril", [("peaks", "hip_angvel_peak"), ("angular_velocity", "hip")]),
    ("Impulso prop.", [("ballistic", "impulso_propulsivo"), ("tdf", "impulse_200ms")]),
]
_POWER_CANDIDATES = [("peaks", "power_peak"), ("peaks", "P_peak")]


def _fmt(v):
    try:
        return f"{float(v):.1f}"
    except (TypeError, ValueError):
        return str(v)


def _report_html(con, kind: str, ref_id: int, title, audience) -> str:
    if kind == "submovement":
        srow = con.execute("SELECT session_id FROM submovement WHERE id=?",
                           (ref_id,)).fetchone()
        if not srow:
            raise HTTPException(404, "submovimento nao encontrado")
        session_id = srow["session_id"]
        sub_filter = " AND id=?"
        sub_params = (session_id, ref_id)
    else:
        session_id = ref_id
        sub_filter = ""
        sub_params = (session_id,)
    ses = con.execute("SELECT * FROM session WHERE id=?", (session_id,)).fetchone()
    if not ses:
        raise HTTPException(404, "sessao nao encontrada")
    ath = con.execute("SELECT * FROM athlete WHERE id=?", (ses["athlete_id"],)).fetchone()
    subs = con.execute(
        "SELECT * FROM submovement WHERE session_id=?" + sub_filter +
        " ORDER BY ordinal", sub_params).fetchall()

    def metrics_for(sub_id):
        out = {}
        for r in con.execute(
                "SELECT analysis,name,value_num,unit FROM metric WHERE submovement_id=?",
                (sub_id,)):
            out[(r["analysis"], r["name"])] = (r["value_num"], r["unit"])
        return out

    ath_name = escape(ath["name"] if ath else "Atleta")
    exercise = escape(ses["exercise"] or "")
    load = ses["load_kg"]
    mass = ath["body_mass_kg"] if ath else None
    height = ath["height_m"] if ath else None
    bmi = ath["bmi"] if ath else None
    aud_label = {"atleta": "Atleta", "treinador": "Treinador",
                 "ambos": "Atleta e Treinador"}.get(audience, "")

    def pick(m, candidates):
        for key in candidates:
            if key in m and m[key][0] is not None:
                return m[key]
        return None

    rep_rows = []
    powers = []
    for sub in subs:
        m = metrics_for(sub["id"])
        cells = []
        for _lab, candidates in _HEADLINE:
            val = pick(m, candidates)
            cells.append(f"<td>{_fmt(val[0])}"
                         f"<span class='u'>{escape(val[1]) if val[1] else ''}</span></td>"
                         if val else "<td>—</td>")
        pk = pick(m, _POWER_CANDIDATES)
        powers.append((escape(sub["label"]), float(pk[0]) if pk and pk[0] else 0.0))
        dur = (sub["n_frames"] * sub["dt"]) if (sub["n_frames"] and sub["dt"]) else None
        rep_rows.append(
            f"<tr><td class='lab'>{escape(sub['label'])}</td>"
            f"<td>{sub['n_frames'] or '—'}</td>"
            f"<td>{_fmt(dur) if dur else '—'}s</td>" + "".join(cells) + "</tr>")

    # mini bar chart (SVG inline) — potencia pico por repeticao
    bars = ""
    if powers:
        pmax = max(p for _, p in powers) or 1.0
        bw = 46
        gap = 18
        w = len(powers) * (bw + gap) + gap
        h = 180
        for i, (lab, p) in enumerate(powers):
            bh = (p / pmax) * 120
            x = gap + i * (bw + gap)
            y = 150 - bh
            bars += (f"<rect x='{x}' y='{y:.0f}' width='{bw}' height='{bh:.0f}' rx='4' "
                     f"fill='#2a9d8f'/>"
                     f"<text x='{x + bw/2:.0f}' y='{y-6:.0f}' text-anchor='middle' "
                     f"class='bv'>{p:.0f}</text>"
                     f"<text x='{x + bw/2:.0f}' y='168' text-anchor='middle' "
                     f"class='bx'>{lab[:8]}</text>")
        chart = (f"<svg viewBox='0 0 {w} {h}' class='chart' role='img' "
                 f"aria-label='Potencia pico por repeticao'>{bars}</svg>")
    else:
        chart = "<p class='muted'>Sem repeticoes.</p>"

    header_cells = "".join(f"<th>{escape(l)}</th>" for l, _ in _HEADLINE)
    date = escape((ses["captured_at"] or "")[:10])
    return f"""<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatorio — {ath_name}</title>
<style>
:root{{--bg:#0e1116;--card:#171b22;--ink:#e6edf3;--mut:#8b98a6;--acc:#2a9d8f;--line:#232a33}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:820px;margin:0 auto;padding:22px 16px 60px}}
.brand{{font-weight:700;letter-spacing:.3px;color:var(--acc)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:18px 18px;margin:14px 0}}
h1{{font-size:22px;margin:.2em 0}}
.meta{{color:var(--mut);font-size:13px}}
.grid{{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}}
.kv{{background:#0e1116;border:1px solid var(--line);border-radius:10px;
padding:8px 12px;min-width:120px}}
.kv b{{display:block;font-size:18px}}
.kv span{{color:var(--mut);font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px;overflow-x:auto;display:block}}
th,td{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
th:first-child,td.lab,td:first-child{{text-align:left}}
th{{color:var(--mut);font-weight:600;font-size:12px}}
td.lab{{font-weight:600}}
.u{{color:var(--mut);font-size:10px;margin-left:2px}}
.chart{{width:100%;height:auto;max-width:100%}}
.bv{{fill:var(--ink);font-size:11px}} .bx{{fill:var(--mut);font-size:10px}}
.badge{{display:inline-block;background:#0e1116;border:1px solid var(--acc);
color:var(--acc);border-radius:999px;padding:2px 10px;font-size:12px}}
.muted{{color:var(--mut)}}
footer{{color:var(--mut);font-size:12px;text-align:center;margin-top:26px}}
</style></head><body><div class="wrap">
<div class="brand">De Lucca Esporte — Relatorio Biomecanico</div>
<div class="card">
  <h1>{ath_name}</h1>
  <div class="meta">{exercise}{(' • ' + str(load) + ' kg') if load else ''}
    {(' • ' + date) if date else ''} • <span class="badge">{aud_label}</span></div>
  <div class="grid">
    <div class="kv"><b>{_fmt(mass) if mass else '—'}</b><span>massa (kg)</span></div>
    <div class="kv"><b>{_fmt(height) if height else '—'}</b><span>estatura (m)</span></div>
    <div class="kv"><b>{_fmt(bmi) if bmi else '—'}</b><span>IMC</span></div>
    <div class="kv"><b>{len(subs)}</b><span>repeticoes</span></div>
  </div>
</div>
<div class="card">
  <h1 style="font-size:16px">Potencia pico por repeticao (W)</h1>
  {chart}
</div>
<div class="card">
  <h1 style="font-size:16px">Metricas por repeticao</h1>
  <table><thead><tr><th>Repeticao</th><th>Frames</th><th>Dur.</th>{header_cells}</tr></thead>
  <tbody>{''.join(rep_rows)}</tbody></table>
</div>
<footer>Gerado pelo sistema biomecanico De Lucca Esporte •
analises padrao-ouro (De Leva, Winter, ISB) • fonte de pose: {escape(ses['pose_source'] or '')}</footer>
</div></body></html>"""


@app.get("/r/{token}", response_class=HTMLResponse, tags=["compartilhar"])
def view_report(token: str):
    con = db.connect_rw()
    try:
        sh = con.execute("SELECT * FROM share WHERE token=?", (token,)).fetchone()
        if not sh:
            raise HTTPException(404, "link invalido ou expirado")
        con.execute("UPDATE share SET views=views+1 WHERE token=?", (token,))
        con.commit()
        html = _report_html(con, sh["kind"], sh["ref_id"], sh["title"], sh["audience"])
        return HTMLResponse(html)
    finally:
        con.close()


# ==========================================================================
# Cliente web estatico (web/) — servido em /app quando presente
# ==========================================================================
_WEB_DIR = Path(__file__).resolve().parents[1] / "web"
if _WEB_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
