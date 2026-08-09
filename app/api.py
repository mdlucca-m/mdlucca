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
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import analyses as A
from app import biomech as Bio
from app import calibration as Cal
from app import fvp as FVP
from app import samozino as SMZ
from app import db
from app import kinematics as Kin
from app import phases as Ph
from app import reference_values as Ref
from app import segments as Seg
from app import signals as Sig
from app import licensing as Lic
from app import branding as Brand
from app import classify as Clf
from app import quality as Qual

ALGO_VERSION = ("mdlucca-1.0 · De Leva 1996; Winter 2009; ISB Wu 2002/2005; "
                "Sánchez-Medina 2011; Samozino 2012; Jaric 2002")

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

# ---- Gate de LICENCA -------------------------------------------------------
# Sem licenca valida, so respondem os caminhos "abertos" (saude, licenca, marca,
# docs e a interface web, que mostra o estado de licenca). Todo o resto exige
# uma licenca emitida por voce. Em dev, MDLUCCA_DEV=1 libera tudo.
_OPEN_EXACT = {"/", "/health", "/license", "/branding", "/openapi.json",
               "/docs", "/redoc", "/favicon.ico"}
_OPEN_PREFIX = ("/app", "/static", "/docs", "/redoc")


@app.middleware("http")
async def _license_gate(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or path in _OPEN_EXACT \
            or any(path.startswith(p) for p in _OPEN_PREFIX):
        return await call_next(request)
    if Lic.is_valid():
        return await call_next(request)
    st = Lic.status()
    return JSONResponse(status_code=402, content={
        "detail": "Licenca necessaria para usar este recurso.",
        "license": {"valid": False, "mode": st.get("mode"), "reason": st.get("reason")},
        "como_ativar": "defina MDLUCCA_LICENSE (token) ou coloque o arquivo em "
                       "data/license.key. Solicite uma licenca ao fornecedor.",
    })

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


@app.get("/license", tags=["licenca"])
def license_status():
    """Estado da licenca de acesso (aberto, para a interface e diagnostico)."""
    return Lic.status()


@app.get("/branding", tags=["licenca"])
def branding():
    """Identidade visual do produto (white-label)."""
    return Brand.brand()


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
# AVALIACAO COMPLETA (unifica: classificacao + qualidade + analises +
# checagens de literatura + proveniencia) — "gera tudo" numa chamada
# ==========================================================================
def _full_series(con, sub_id, name):
    r = con.execute("SELECT samples FROM series WHERE submovement_id=? AND name=?",
                    (sub_id, name)).fetchone()
    return json.loads(r["samples"]) if r else None


def _build_assessment(session_id: int, deep: bool = False) -> dict:
    con = db.connect()
    try:
        ses = db.one(con, "SELECT * FROM session WHERE id=?", (session_id,))
        if not ses:
            raise HTTPException(404, "sessao nao encontrada")
        ses = db.parse_json_fields(ses, ["meta"])
        ath = db.one(con, "SELECT * FROM athlete WHERE id=?", (ses["athlete_id"],))
        subs = db.rows(con, "SELECT id,ordinal,label,n_frames,dt FROM submovement "
                       "WHERE session_id=? ORDER BY ordinal", (session_id,))
        if not subs:
            raise HTTPException(404, "sessao sem submovimentos")
        full = max(subs, key=lambda s: s["n_frames"] or 0)
        hip = _full_series(con, full["id"], "hip_angle")
        t = _full_series(con, full["id"], "t")
        reps = [s for s in subs if s["id"] != full["id"]] or subs

        meta = ses.get("meta") or {}
        fps = meta.get("fps")
        detected = meta.get("pose_detected_frames")
        n_frames = full["n_frames"]
        det_ratio = (detected / n_frames) if (detected and n_frames) else 1.0
        is_cal = bool((meta.get("calibration")) or meta.get("is_calibrated"))

        classification = (Clf.classify_movement(
            hip, t, load_kg=ses.get("load_kg"),
            body_mass_kg=(ath or {}).get("body_mass_kg"),
            exercise_hint=ses.get("exercise")) if (hip and t) else
            {"pattern": "indefinido", "confidence": 0.0,
             "description": "Sem série de ângulo para classificar."})
        quality = Qual.quality_report(n_frames=n_frames, fps=fps,
                                      is_calibrated=is_cal, detected_ratio=det_ratio)

        # checagens de literatura (extensao de quadril/joelho/cotovelo + CV entre reps)
        checks = []
        for sname, key in [("hip_angle", "hip_extension_deg"),
                           ("knee_angle", "knee_extension_deg"),
                           ("elbow_angle", "elbow_extension_deg")]:
            s = _full_series(con, full["id"], sname)
            if s:
                checks.append(Ref.evaluate(key, round(float(max(s)), 1)))
        # CV% do pico de potencia entre as reps
        pk = []
        for r in reps:
            m = con.execute("SELECT value_num FROM metric WHERE submovement_id=? AND "
                            "analysis='peaks' AND name IN ('power_peak','P_peak')",
                            (r["id"],)).fetchone()
            if m and m["value_num"]:
                pk.append(float(m["value_num"]))
        if len(pk) >= 2:
            cv = A.coefficient_of_variation(pk).get("cv_pct")
            if cv is not None:
                checks.append(Ref.evaluate("cv_pct", round(cv, 1)))

        # resumo de metricas por rep (headline)
        HL = [("power_peak", "P_peak"), ("F_peak",), ("v_peak",),
              ("RFD_peak",), ("hip_angvel_peak",)]
        rep_summary = []
        for r in reps:
            vals = {}
            for names in HL:
                q = ",".join("?" * len(names))
                row = con.execute(f"SELECT name,value_num FROM metric WHERE submovement_id=? "
                                  f"AND analysis='peaks' AND name IN ({q})",
                                  (r["id"], *names)).fetchone()
                if row and row["value_num"] is not None:
                    vals[names[0]] = round(float(row["value_num"]), 1)
            rep_summary.append({"rep": r["label"], **vals})

        provenance = {
            "data_source": ses.get("pose_source"),
            "pose_model": ses.get("pose_model"),
            "algorithm_version": ALGO_VERSION,
            "frame_count": n_frames, "fps": fps,
            "detected_ratio": round(det_ratio, 3),
            "calibrated": is_cal, "calibration": meta.get("calibration"),
            "camera_view": meta.get("camera_view", "sagital"),
        }
        out = {
            "session_id": session_id, "exercise": ses.get("exercise"),
            "athlete": (ath or {}).get("name"), "load_kg": ses.get("load_kg"),
            "algorithm_version": ALGO_VERSION,
            "classification": classification, "quality": quality,
            "literature_checks": checks, "reps": rep_summary,
            "n_reps": len(reps), "provenance": provenance,
        }
        if deep:
            out["deep"] = [{"rep": s["label"], "analysis": deep_panel(s["id"])}
                           for s in reps]
        return out
    finally:
        con.close()


@app.get("/sessions/{session_id}/assessment", tags=["avaliacao"])
def session_assessment(session_id: int, deep: bool = Query(False)):
    """Avaliacao COMPLETA da sessao numa chamada: classificacao do movimento,
    score de qualidade, checagens de literatura, resumo por rep e proveniencia.
    `deep=true` inclui o painel biomecanico completo por repeticao."""
    return _build_assessment(session_id, deep=deep)


def _persist_assessment(session_id: int) -> dict:
    """Constroi e grava a avaliacao como AnalysisRun; devolve com o id."""
    a = _build_assessment(session_id, deep=False)
    con = db.connect_rw()
    try:
        cur = con.execute(
            "INSERT INTO analysis_run (session_id, algorithm_version, classification, "
            "quality_score, quality_level, warnings, metrics, literature_checks, "
            "provenance, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (session_id, ALGO_VERSION, json.dumps(a["classification"], ensure_ascii=False),
             a["quality"]["score"], a["quality"]["level"],
             json.dumps(a["quality"]["warnings"], ensure_ascii=False),
             json.dumps(a["reps"], ensure_ascii=False),
             json.dumps(a["literature_checks"], ensure_ascii=False),
             json.dumps(a["provenance"], ensure_ascii=False),
             datetime.now(timezone.utc).isoformat()))
        con.commit()
        a["analysis_run_id"] = cur.lastrowid
        return a
    finally:
        con.close()


@app.post("/sessions/{session_id}/assessment", tags=["avaliacao"])
def create_assessment(session_id: int):
    """Gera e PERSISTE a avaliacao como um AnalysisRun (com proveniencia)."""
    return _persist_assessment(session_id)


@app.get("/assessments", tags=["avaliacao"])
def list_assessments(session_id: Optional[int] = None):
    con = db.connect_rw()
    try:
        sql = "SELECT id,session_id,algorithm_version,quality_score,quality_level,created_at FROM analysis_run"
        params: tuple = ()
        if session_id is not None:
            sql += " WHERE session_id=?"; params = (session_id,)
        return db.rows(con, sql + " ORDER BY id DESC", params)
    finally:
        con.close()


def _run_row(con, rid):
    r = con.execute("SELECT * FROM analysis_run WHERE id=?", (rid,)).fetchone()
    if not r:
        raise HTTPException(404, "avaliacao nao encontrada")
    d = dict(r)
    for f in ("classification", "warnings", "metrics", "literature_checks", "provenance"):
        if d.get(f):
            d[f] = json.loads(d[f])
    return d


@app.get("/assessments/{rid}", tags=["avaliacao"])
def get_assessment(rid: int):
    con = db.connect_rw()
    try:
        return _run_row(con, rid)
    finally:
        con.close()


@app.get("/assessments/{rid}/report.md", response_class=PlainTextResponse, tags=["avaliacao"])
def assessment_report_md(rid: int):
    con = db.connect_rw()
    try:
        run = _run_row(con, rid)
        ses = db.one(con, "SELECT * FROM session WHERE id=?", (run["session_id"],))
        ath = db.one(con, "SELECT * FROM athlete WHERE id=?",
                     (ses["athlete_id"],)) if ses else None
        return PlainTextResponse(_report_markdown(run, ses, ath))
    finally:
        con.close()


@app.get("/assessments/{rid}/report.html", response_class=HTMLResponse, tags=["avaliacao"])
def assessment_report_html(rid: int):
    con = db.connect_rw()
    try:
        run = _run_row(con, rid)
        ses = db.one(con, "SELECT * FROM session WHERE id=?", (run["session_id"],))
        ath = db.one(con, "SELECT * FROM athlete WHERE id=?",
                     (ses["athlete_id"],)) if ses else None
        return HTMLResponse(_assessment_html(run, ses, ath))
    finally:
        con.close()


def _status_color(status: str) -> str:
    return {"otimo": "#2a9d8f", "adequado": "#e9c46a", "abaixo": "#e63946",
            "acima": "#e63946", "excelente": "#2a9d8f", "bom": "#2a9d8f",
            "aceitavel": "#e9c46a", "ruim": "#e63946"}.get(status, "#8b98a6")


def _assessment_html(run: dict, ses: dict, ath: Optional[dict]) -> str:
    b = Brand.brand()
    acc = escape(b.get("primary") or "#2a9d8f")
    name = escape(b["name"])
    cl = run.get("classification") or {}
    q_level = run.get("quality_level") or "—"
    q_score = run.get("quality_score")
    checks = run.get("literature_checks") or []
    reps = run.get("metrics") or []
    prov = run.get("provenance") or {}
    warns = run.get("warnings") or []
    ath_name = escape((ath or {}).get("name") or "Atleta")
    ex = escape((ses or {}).get("exercise") or "")
    load = (ses or {}).get("load_kg")

    kpis = "".join(
        f"<div class='kpi'><b>{v}</b><span>{escape(l)}</span></div>" for v, l in [
            (f"{cl.get('confidence',0):.0%}", "confiança"),
            (f"{q_score}%", f"qualidade · {escape(q_level)}"),
            (cl.get("n_ciclos", "—"), "repetições"),
            (f"{cl.get('rom_quadril_graus','—')}°", "ampl. quadril")])

    def check_rows():
        r = ""
        for c in checks:
            col = _status_color(c.get("status", ""))
            r += (f"<tr><td>{escape(str(c.get('metric','')))}</td>"
                  f"<td>{escape(str(c.get('value','')))} {escape(str(c.get('unit','')))}</td>"
                  f"<td><span class='tag' style='color:{col};border-color:{col}'>"
                  f"{escape(str(c.get('status','')))}</span></td>"
                  f"<td class='muted'>{escape(str(c.get('source','')))}</td></tr>")
        return r or "<tr><td colspan='4' class='muted'>—</td></tr>"

    rep_cols = [k for k in reps[0].keys() if k != "rep"] if reps else []
    rep_head = "".join(f"<th>{escape(c)}</th>" for c in rep_cols)
    rep_body = ""
    for r in reps:
        rep_body += ("<tr><td class='lab'>" + escape(r.get("rep", "")) + "</td>"
                     + "".join(f"<td>{escape(str(r.get(c,'—')))}</td>" for c in rep_cols) + "</tr>")
    warn_html = ("".join(f"<li>{escape(w)}</li>" for w in warns)
                 if warns else "<li class='muted'>Sem alertas de qualidade.</li>")
    qcol = _status_color(q_level)
    return f"""<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Avaliação — {ath_name}</title>
<style>
:root{{--bg:#0e1116;--card:#171b22;--ink:#e6edf3;--mut:#8b98a6;--acc:{acc};--line:#232a33}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:820px;margin:0 auto;padding:22px 16px 60px}}
.brand{{font-weight:700;color:var(--acc)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}}
h1{{font-size:22px;margin:.2em 0}} h2{{font-size:15px;margin:0 0 10px}}
.meta{{color:var(--mut);font-size:13px}}
.pattern{{display:inline-block;background:#0e1116;border:1px solid var(--acc);color:var(--acc);
border-radius:999px;padding:3px 12px;font-weight:600;font-size:14px}}
.grid{{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}}
.kpi{{background:#0e1116;border:1px solid var(--line);border-radius:10px;padding:8px 12px;min-width:110px}}
.kpi b{{display:block;font-size:20px}} .kpi span{{color:var(--mut);font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px;display:block;overflow-x:auto}}
th,td{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}
th{{color:var(--mut);font-size:12px}} td.lab{{font-weight:600}}
.tag{{border:1px solid;border-radius:999px;padding:1px 8px;font-size:12px}}
.muted{{color:var(--mut)}} ul{{margin:.3em 0;padding-left:1.1em}}
.qbadge{{display:inline-block;border:1px solid {qcol};color:{qcol};border-radius:999px;
padding:2px 10px;font-size:13px}}
footer{{color:var(--mut);font-size:12px;text-align:center;margin-top:22px}}
</style></head><body><div class="wrap">
<div class="brand">{name} — Avaliação Biomecânica</div>
<div class="card">
  <h1>{ath_name}</h1>
  <div class="meta">{ex}{(' • ' + str(load) + ' kg') if load else ''} •
    qualidade <span class="qbadge">{escape(q_level)} · {q_score}%</span></div>
  <div style="margin-top:10px"><span class="pattern">{escape(cl.get('pattern','—'))}</span>
    <span class="meta"> — {escape(cl.get('description',''))}</span></div>
  <div class="grid">{kpis}</div>
</div>
<div class="card"><h2>Checagens de literatura</h2>
  <table><thead><tr><th>Métrica</th><th>Valor</th><th>Status</th><th>Referência</th></tr></thead>
  <tbody>{check_rows()}</tbody></table></div>
<div class="card"><h2>Métricas por repetição</h2>
  <table><thead><tr><th>Rep</th>{rep_head}</tr></thead><tbody>{rep_body}</tbody></table></div>
<div class="card"><h2>Qualidade &amp; procedência</h2>
  <ul>{warn_html}</ul>
  <div class="meta">Fonte: {escape(str(prov.get('data_source','—')))}
    ({escape(str(prov.get('pose_model','—')))}) ·
    {escape(str(prov.get('frame_count','—')))} quadros @ {escape(str(prov.get('fps','—')))} fps ·
    calibrado: {'sim' if prov.get('calibrated') else 'não'}</div>
  <div class="meta" style="margin-top:6px">Algoritmo: {escape(str(prov.get('algorithm_version','')))}</div>
</div>
<footer>Relatório de avaliação gerado por {name} • padrões internacionais de biomecânica</footer>
</div></body></html>"""


def _report_markdown(run: dict, ses: dict, ath: Optional[dict]) -> str:
    b = Brand.brand()
    cl = run.get("classification") or {}
    ch = run.get("literature_checks") or []
    prov = run.get("provenance") or {}
    lines = [
        f"# {b['name']} — Relatório de Avaliação Biomecânica", "",
        f"**Atleta:** {(ath or {}).get('name','—')}  ",
        f"**Exercício:** {(ses or {}).get('exercise','—')}  ",
        f"**Carga:** {(ses or {}).get('load_kg') or '—'} kg  ",
        f"**Gerado:** {run.get('created_at','')[:19].replace('T',' ')}", "",
        "## Classificação do movimento",
        f"- Padrão: **{cl.get('pattern','—')}** (confiança {cl.get('confidence',0):.0%})",
        f"- {cl.get('description','')}",
        f"- Repetições: {cl.get('n_ciclos','—')} · Amplitude de quadril: "
        f"{cl.get('rom_quadril_graus','—')}° · Duração/ciclo: {cl.get('duracao_ciclo_s','—')} s", "",
        f"## Qualidade da análise: **{run.get('quality_level','—')}** "
        f"({run.get('quality_score','—')}%)",
    ]
    for w in (run.get("warnings") or []):
        lines.append(f"- ⚠ {w}")
    if not run.get("warnings"):
        lines.append("- Sem alertas de qualidade.")
    lines += ["", "## Checagens de literatura"]
    if ch:
        lines.append("| Métrica | Valor | Status | Referência |")
        lines.append("|---|---|---|---|")
        for c in ch:
            lines.append(f"| {c.get('metric','')} | {c.get('value','')} "
                         f"{c.get('unit','')} | {c.get('status','')} | {c.get('source','')} |")
    else:
        lines.append("- Sem checagens disponíveis.")
    lines += ["", "## Métricas por repetição"]
    reps = run.get("metrics") or []
    if reps:
        cols = [k for k in reps[0].keys() if k != "rep"]
        lines.append("| Rep | " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * (len(cols) + 1))
        for r in reps:
            lines.append("| " + r.get("rep", "") + " | "
                         + " | ".join(str(r.get(c, "—")) for c in cols) + " |")
    lines += ["", "## Procedência",
              f"- Fonte de pose: {prov.get('data_source','—')} ({prov.get('pose_model','—')})",
              f"- Quadros: {prov.get('frame_count','—')} @ {prov.get('fps','—')} fps "
              f"(detecção {prov.get('detected_ratio','—')})",
              f"- Calibrado: {'sim' if prov.get('calibrated') else 'não'}",
              f"- Algoritmo: {prov.get('algorithm_version','')}", "",
              f"_Relatório gerado por {b['name']} · padrões internacionais de biomecânica._"]
    return "\n".join(lines)


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
# Perfil Forca-Velocidade-Potencia (FVP) — teste de cargas
# ==========================================================================
class FVPBody(BaseModel):
    loads_kg: list[float] = Field(..., min_length=2)
    velocities: list[float] = Field(..., min_length=2)
    g: float = 9.81
    bodyweight_kg: Optional[float] = None
    v1rm: float = 0.30
    com_displacement_m: Optional[float] = None


@app.post("/compute/fvp", tags=["analises"])
def post_fvp(b: FVPBody):
    """Perfil Forca-Velocidade-Potencia de um teste de cargas (pares carga/vel)."""
    try:
        return FVP.full_profile(b.loads_kg, b.velocities, g=b.g,
                                bodyweight_kg=b.bodyweight_kg or 0.0, v1rm=b.v1rm,
                                com_displacement_m=b.com_displacement_m or 0.0)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


class SamozinoBody(BaseModel):
    bodyweight_kg: float = Field(..., gt=0)
    added_loads_kg: list[float] = Field(..., min_length=2)
    jump_heights_m: list[float] = Field(..., min_length=2)
    push_off_m: float = Field(..., gt=0)
    g: float = 9.81


@app.post("/compute/samozino", tags=["analises"])
def post_samozino(b: SamozinoBody):
    """Modelo balistico de Samozino: perfil F-V-P de saltos com cargas + FVimb
    (desequilibrio forca-velocidade vs perfil otimo)."""
    if len(b.added_loads_kg) != len(b.jump_heights_m):
        raise HTTPException(422, "added_loads_kg e jump_heights_m com tamanhos diferentes")
    masses = [b.bodyweight_kg + x for x in b.added_loads_kg]
    try:
        return SMZ.profile_from_jumps(masses, b.jump_heights_m, b.push_off_m,
                                      g=b.g, bodyweight_kg=b.bodyweight_kg)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@app.get("/athletes/{athlete_id}/samozino", tags=["analises"])
def athlete_samozino(athlete_id: int, exercise: Optional[str] = None,
                     push_off_m: Optional[float] = None):
    """Modo salto ligado ao atleta: monta o teste de Samozino a partir das
    sessoes de salto (altura + push-off lidos das metricas armazenadas).

    Altura do salto: jump.height (senao efficiency.delta_h).
    Push-off: parametro; senao jump.push_off; senao cog.y_excursion (medias).
    Carga adicionada: session.load_kg (NULL = 0). Massa = peso corporal + carga.
    """
    con = db.connect()
    try:
        ath = db.one(con, "SELECT * FROM athlete WHERE id=?", (athlete_id,))
        if not ath:
            raise HTTPException(404, "aluno nao encontrado")
        if not ath["body_mass_kg"]:
            raise HTTPException(422, "aluno sem massa corporal (necessaria p/ Samozino)")

        sql = "SELECT id, exercise, load_kg FROM session WHERE athlete_id=?"
        params: tuple = (athlete_id,)
        if exercise:
            sql += " AND exercise=?"
            params += (exercise,)
        sessions = db.rows(con, sql + " ORDER BY load_kg", params)

        def best_metric(sub_ids, candidates):
            q = ",".join("?" * len(sub_ids))
            for ns, nm in candidates:
                v = con.execute(
                    f"SELECT AVG(value_num) FROM metric WHERE submovement_id IN ({q}) "
                    f"AND analysis=? AND name=?", (*sub_ids, ns, nm)).fetchone()[0]
                if v is not None:
                    return float(v)
            return None

        masses, heights, pushoffs, used = [], [], [], []
        for s in sessions:
            subs = [r["id"] for r in con.execute(
                "SELECT id FROM submovement WHERE session_id=?", (s["id"],))]
            if not subs:
                continue
            h = best_metric(subs, [("jump", "height"), ("efficiency", "delta_h")])
            if h is None or h <= 0:
                continue
            po = best_metric(subs, [("jump", "push_off"), ("cog", "y_excursion")])
            added = float(s["load_kg"]) if s["load_kg"] is not None else 0.0
            masses.append(float(ath["body_mass_kg"]) + added)
            heights.append(h)
            if po:
                pushoffs.append(po)
            used.append({"session_id": s["id"], "exercise": s["exercise"],
                         "carga_adicionada_kg": added, "altura_m": round(h, 3),
                         "push_off_m": round(po, 3) if po else None})

        if len(masses) < 2:
            raise HTTPException(
                422, f"modo salto exige >= 2 sessoes de salto com altura; "
                     f"encontradas {len(masses)}. Cadastre saltos em cargas diferentes "
                     f"(altura em jump.height ou efficiency.delta_h).")
        hPO = push_off_m if push_off_m else (
            sum(pushoffs) / len(pushoffs) if pushoffs else None)
        if not hPO or hPO <= 0:
            raise HTTPException(
                422, "sem distancia de push-off: informe push_off_m ou grave "
                     "jump.push_off / cog.y_excursion nas sessoes.")
        try:
            prof = SMZ.profile_from_jumps(masses, heights, hPO,
                                          bodyweight_kg=float(ath["body_mass_kg"]))
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        prof["atleta"] = ath["name"]
        prof["sessoes_usadas"] = used
        return prof
    finally:
        con.close()


@app.get("/athletes/{athlete_id}/fvp", tags=["analises"])
def athlete_fvp(athlete_id: int, exercise: Optional[str] = None,
                velocity_metric: str = "vbt.MPV", v1rm: float = 0.30,
                include_bodyweight: bool = False,
                com_displacement_m: Optional[float] = None):
    """Traca o perfil FVP a partir das SESSOES do atleta em cargas diferentes.

    Cada sessao (com load_kg) vira um ponto; a velocidade e o melhor valor da
    metrica escolhida entre as repeticoes (default vbt.MPV; senao peaks.v_peak).
    """
    con = db.connect()
    try:
        ath = db.one(con, "SELECT * FROM athlete WHERE id=?", (athlete_id,))
        if not ath:
            raise HTTPException(404, "aluno nao encontrado")
        sql = "SELECT id, exercise, load_kg FROM session WHERE athlete_id=? AND load_kg IS NOT NULL"
        params: tuple = (athlete_id,)
        if exercise:
            sql += " AND exercise=?"
            params += (exercise,)
        sessions = db.rows(con, sql + " ORDER BY load_kg", params)
        ns, nm = (velocity_metric.split(".", 1) + ["MPV"])[:2] if "." in velocity_metric \
            else ("vbt", velocity_metric)

        loads, vels, used = [], [], []
        for s in sessions:
            subs = [r["id"] for r in con.execute(
                "SELECT id FROM submovement WHERE session_id=?", (s["id"],))]
            if not subs:
                continue
            q = ",".join("?" * len(subs))
            best = con.execute(
                f"SELECT MAX(value_num) FROM metric WHERE submovement_id IN ({q}) "
                f"AND analysis=? AND name=?", (*subs, ns, nm)).fetchone()[0]
            if best is None:      # fallback: pico de velocidade linear
                best = con.execute(
                    f"SELECT MAX(value_num) FROM metric WHERE submovement_id IN ({q}) "
                    f"AND analysis='peaks' AND name='v_peak'", subs).fetchone()[0]
            if best is None:
                continue
            loads.append(float(s["load_kg"]))
            vels.append(float(best))
            used.append({"session_id": s["id"], "exercise": s["exercise"],
                         "load_kg": s["load_kg"], "velocity": round(float(best), 3)})

        if len(loads) < 2:
            raise HTTPException(
                422, f"teste de cargas exige >= 2 sessoes com carga e velocidade; "
                     f"encontradas {len(loads)}. Cadastre sessoes do mesmo exercicio "
                     f"em cargas diferentes.")
        bw = float(ath["body_mass_kg"]) if (include_bodyweight and ath["body_mass_kg"]) else 0.0
        # deslocamento do centro de massa: usa o parametro; senao tenta o CoG
        # armazenado (cog.y_excursion) medio das sessoes usadas.
        com_d = com_displacement_m
        if com_d is None:
            sids = [u["session_id"] for u in used]
            if sids:
                qs = ",".join("?" * len(sids))
                subq = (f"SELECT AVG(value_num) FROM metric WHERE analysis='cog' "
                        f"AND name='y_excursion' AND session_id IN ({qs})")
                v = con.execute(subq, sids).fetchone()[0]
                com_d = float(v) if v else None
        prof = FVP.full_profile(loads, vels, bodyweight_kg=bw, v1rm=v1rm,
                                com_displacement_m=com_d or 0.0)
        prof["atleta"] = ath["name"]
        prof["metrica_velocidade"] = velocity_metric
        prof["sessoes_usadas"] = used
        return prof
    finally:
        con.close()


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
    kind: Literal["session", "submovement", "assessment"] = "session"
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
        tbl = {"session": "session", "submovement": "submovement",
               "assessment": "analysis_run"}[s.kind]
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


class DemoSeedIn(BaseModel):
    athletes: int = Field(4, ge=1, le=6)
    reps: int = Field(5, ge=1, le=12)
    reset: bool = True


@app.post("/demo/seed", tags=["cadastro"])
def demo_seed(body: DemoSeedIn, request: Request):
    """Gera MASSA DE TESTE (atletas/sessoes/metricas ficticias) e ja cria os
    links de relatorio. Usa scripts/seed_demo.py."""
    import importlib
    scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    seed_demo = importlib.import_module("seed_demo")
    con = db.connect_rw()
    try:
        removed = seed_demo.clear_demo(con) if body.reset else 0
        recs = seed_demo.seed(con, body.athletes, body.reps, make_shares=True)
        base = str(request.base_url).rstrip("/")
        for r in recs:
            if r.get("report_url"):
                r["report_url"] = base + r["report_url"]
        return {"removed": removed, "created": len(recs), "sessions": recs}
    finally:
        con.close()


# ==========================================================================
# Upload de video pelo ATLETA + fila de analise (o treinador analisa)
# ==========================================================================
_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = _ROOT / "data" / "uploads"
OUT_DIR = _ROOT / "data" / "out"


def _pose_model() -> Optional[str]:
    m = os.environ.get("MDLUCCA_POSE_MODEL")
    return m if (m and Path(m).exists()) else None


def _upload_row(con, uid):
    r = con.execute("SELECT * FROM upload WHERE id=?", (uid,)).fetchone()
    return dict(r) if r else None


def _analyze_worker(upload_id: int):
    """Roda pose->sessao para um upload e religa a sessao ao atleta dono."""
    con = db.connect_rw()
    row = _upload_row(con, upload_id)
    if not row:
        con.close(); return
    ath = con.execute("SELECT name FROM athlete WHERE id=?", (row["athlete_id"],)).fetchone()
    ath_name = ath["name"] if ath else f"Atleta {row['athlete_id']}"
    before_ath = con.execute("SELECT COALESCE(MAX(id),0) FROM athlete").fetchone()[0]
    before_ses = con.execute("SELECT COALESCE(MAX(id),0) FROM session").fetchone()[0]
    con.close()
    db_path = str(db.db_path())
    now = datetime.now(timezone.utc).isoformat()
    try:
        model = _pose_model()
        if not model:
            raise RuntimeError("modelo de pose nao configurado (defina MDLUCCA_POSE_MODEL)")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        pose_json = OUT_DIR / f"pose_upload_{upload_id}.json"
        subprocess.run([sys.executable, str(_ROOT / "scripts/pose_extract.py"),
                        "--video", row["path"], model, "-o", str(pose_json)],
                       check=True, capture_output=True, text=True, timeout=1800)
        cmd = [sys.executable, str(_ROOT / "scripts/build_session_from_pose.py"),
               "--pose", str(pose_json), "--db", db_path, "--athlete", ath_name,
               "--exercise", row["exercise"] or "Vídeo",
               "--mass", str(row["mass_kg"] or 80), "--append"]
        if row["stature_m"]:
            cmd += ["--stature", str(row["stature_m"])]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=900)
        con = db.connect_rw()
        new_ses = con.execute("SELECT COALESCE(MAX(id),0) FROM session").fetchone()[0]
        if new_ses > before_ses:
            pct = None
            am = con.execute("SELECT body_mass_kg FROM athlete WHERE id=?",
                             (row["athlete_id"],)).fetchone()
            if row["load_kg"] and am and am["body_mass_kg"]:
                pct = round(100 * row["load_kg"] / am["body_mass_kg"], 1)
            con.execute("UPDATE session SET athlete_id=?, load_kg=?, pct_bodyweight=? WHERE id=?",
                        (row["athlete_id"], row["load_kg"], pct, new_ses))
            con.execute("DELETE FROM athlete WHERE id>? AND id NOT IN "
                        "(SELECT DISTINCT athlete_id FROM session)", (before_ath,))
            con.execute("UPDATE upload SET status='done', session_id=?, analyzed_at=? WHERE id=?",
                        (new_ses, now, upload_id))
        else:
            con.execute("UPDATE upload SET status='error', error='nenhuma sessao criada' WHERE id=?",
                        (upload_id,))
        con.commit(); con.close()
        if new_ses > before_ses:
            try:                       # avaliacao automatica ao concluir a analise
                _persist_assessment(new_ses)
            except Exception:          # noqa: BLE001 - nao quebra o upload
                pass
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or exc.stdout or str(exc))[-500:]
        con = db.connect_rw(); con.execute(
            "UPDATE upload SET status='error', error=? WHERE id=?", (msg, upload_id))
        con.commit(); con.close()
    except Exception as exc:  # noqa: BLE001
        con = db.connect_rw(); con.execute(
            "UPDATE upload SET status='error', error=? WHERE id=?", (str(exc)[:500], upload_id))
        con.commit(); con.close()


@app.post("/athletes/{athlete_id}/uploads", tags=["upload"])
async def create_upload(athlete_id: int, file: UploadFile = File(...),
                        exercise: str = Form("Vídeo"),
                        mass_kg: Optional[float] = Form(None),
                        stature_m: Optional[float] = Form(None),
                        load_kg: Optional[float] = Form(None)):
    """O ATLETA envia o proprio video; entra na fila 'queued' para o treinador analisar."""
    con = db.connect_rw()
    try:
        ath = con.execute("SELECT body_mass_kg, height_m FROM athlete WHERE id=?",
                          (athlete_id,)).fetchone()
        if not ath:
            raise HTTPException(404, "aluno nao encontrado")
        mass = mass_kg or ath["body_mass_kg"]
        stat = stature_m or ath["height_m"]
        cur = con.execute(
            "INSERT INTO upload (athlete_id, filename, exercise, mass_kg, stature_m, "
            "load_kg, status, created_at) VALUES (?,?,?,?,?,?,'queued',?)",
            (athlete_id, file.filename, exercise, mass, stat, load_kg,
             datetime.now(timezone.utc).isoformat()))
        uid = cur.lastrowid
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "video.mp4")
        dest = UPLOAD_DIR / f"{uid}_{safe}"
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        con.execute("UPDATE upload SET path=? WHERE id=?", (str(dest), uid))
        con.commit()
        return _upload_row(con, uid)
    finally:
        con.close()


@app.get("/uploads", tags=["upload"])
def list_uploads(status: Optional[str] = None):
    con = db.connect_rw()
    try:
        sql = ("SELECT u.*, a.name AS athlete_name FROM upload u "
               "LEFT JOIN athlete a ON a.id=u.athlete_id")
        params: tuple = ()
        if status:
            sql += " WHERE u.status=?"; params = (status,)
        return db.rows(con, sql + " ORDER BY u.id DESC", params)
    finally:
        con.close()


@app.get("/athletes/{athlete_id}/uploads", tags=["upload"])
def athlete_uploads(athlete_id: int):
    con = db.connect_rw()
    try:
        return db.rows(con, "SELECT * FROM upload WHERE athlete_id=? ORDER BY id DESC",
                       (athlete_id,))
    finally:
        con.close()


@app.get("/uploads/{uid}", tags=["upload"])
def get_upload(uid: int):
    con = db.connect_rw()
    try:
        row = _upload_row(con, uid)
        if not row:
            raise HTTPException(404, "upload nao encontrado")
        return row
    finally:
        con.close()


@app.post("/uploads/{uid}/analyze", tags=["upload"])
def analyze_upload(uid: int):
    """O TREINADOR dispara a analise do video enviado (pose -> sessao)."""
    con = db.connect_rw()
    try:
        row = _upload_row(con, uid)
        if not row:
            raise HTTPException(404, "upload nao encontrado")
        if row["status"] == "processing":
            raise HTTPException(409, "ja esta em analise")
        if not _pose_model():
            raise HTTPException(
                503, "modelo de pose nao configurado no servidor (MDLUCCA_POSE_MODEL)")
        con.execute("UPDATE upload SET status='processing', error=NULL WHERE id=?", (uid,))
        con.commit()
    finally:
        con.close()
    threading.Thread(target=_analyze_worker, args=(uid,), daemon=True).start()
    return {"upload_id": uid, "status": "processing"}


@app.post("/uploads/{uid}/delete", tags=["upload"])
def delete_upload(uid: int):
    con = db.connect_rw()
    try:
        row = _upload_row(con, uid)
        if not row:
            raise HTTPException(404, "upload nao encontrado")
        if row.get("path") and Path(row["path"]).exists():
            try:
                Path(row["path"]).unlink()
            except OSError:
                pass
        con.execute("DELETE FROM upload WHERE id=?", (uid,))
        con.commit()
        return {"deleted": uid}
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
    _b = Brand.brand()
    brand_name = escape(_b["name"])
    acc = escape(_b.get("primary") or "#2a9d8f")
    return f"""<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatorio — {ath_name}</title>
<style>
:root{{--bg:#0e1116;--card:#171b22;--ink:#e6edf3;--mut:#8b98a6;--acc:{acc};--line:#232a33}}
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
<div class="brand">{brand_name} — Relatorio Biomecanico</div>
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
<footer>Gerado pelo sistema biomecanico {brand_name} •
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
        if sh["kind"] == "assessment":
            run = _run_row(con, sh["ref_id"])
            ses = db.one(con, "SELECT * FROM session WHERE id=?", (run["session_id"],))
            ath = db.one(con, "SELECT * FROM athlete WHERE id=?",
                         (ses["athlete_id"],)) if ses else None
            return HTMLResponse(_assessment_html(run, ses, ath))
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
