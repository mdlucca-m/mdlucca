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
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app import analyses as A
from app import db

app = FastAPI(
    title="mdlucca — API Biomecanica (Landmine Clean & Press)",
    version="1.0.0",
    description=(
        "Backend da Etapa 1: serve os dados de pose/analise antes embutidos no "
        "dashboard HTML e recomputa as analises 'padrao-ouro' com rigor "
        "estatistico (numpy/scipy). Fonte de pose atual: MediaPipe (monocular). "
        "Etapa 2 (roadmap): fonte de pose de alta qualidade."
    ),
)


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
def query_metrics(analysis: str = Query(...), name: Optional[str] = None):
    con = db.connect()
    try:
        sql = ("SELECT m.submovement_id, sm.label, m.analysis, m.name, m.value_num, m.value_text, m.unit "
               "FROM metric m LEFT JOIN submovement sm ON sm.id=m.submovement_id WHERE m.analysis=?")
        params: tuple = (analysis,)
        if name:
            sql += " AND m.name=?"
            params += (name,)
        return db.rows(con, sql + " ORDER BY sm.ordinal, m.name", params)
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
