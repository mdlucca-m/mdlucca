#!/usr/bin/env python3
"""Painel 4K do LAPE — Streamlit, modo Cyberpunk/Sci-Fi.

Um painel standalone para telas grandes (TV 4K de parede), lendo o MESMO
banco SQLite da produção (via SQLAlchemy, só leitura). É um app separado
do sistema principal (que roda num servidor HTTP próprio, sem Streamlit)
-- pensado para rodar ao lado dele, apontando pro mesmo `db.sqlite`.

Como rodar:

    pip install streamlit sqlalchemy plotly pandas
    streamlit run scripts/lape_streamlit_4k.py -- --db /caminho/para/db.sqlite

Sem `--db`, cai no mesmo padrão do resto do sistema: a variável de
ambiente `LAPE_DB`, ou `data/db.sqlite` na raiz do repositório.

--------------------------------------------------------------------------
"IA Central do LAPE" (projeção e alertas)
--------------------------------------------------------------------------
Este painel também calcula, a partir dos MESMOS dados reais do banco (não
de um número digitado à mão):

  - Alerta de latência: toda submissão parada (sem decisão) há mais de
    `LATENCIA_CRITICA_MESES` meses vira um cartão piscando com o artigo e
    a revista -- sem esperar por um pipeline externo (n8n, etc.) para
    calcular o que o próprio banco já sabe.
  - Sugestão metodológica quando a taxa de aceite do período está em 0%:
    compara com as linhas de pesquisa historicamente mais aceitas.
  - Projeção de ritmo: uma ESTIMATIVA (não uma meta) de quantos artigos o
    ritmo atual deve produzir até o fim do ano, mostrada ao lado da meta
    de verdade quando a coordenação já declarou uma (tabela `goals`).
    Esta distinção importa: quem decide quanto o laboratório QUER
    publicar é a coordenação, nunca o painel -- o painel só projeta o que
    o ritmo atual, se mantido, deve render.
  - Diagnóstico + intervenção (4 passos): diagnóstico frio do banco,
    correlação com a presença COLETIVA da semana (agregada do laboratório
    inteiro, via tabela `ponto` -- nunca por pesquisador), tendência a 6
    meses contra a média histórica real do laboratório, e uma técnica de
    psicologia esportiva (metas SMART, regulação de ansiedade, biofeedback)
    cujo gatilho bate com o padrão encontrado. É apoio para a conversa da
    próxima reunião de coordenação, não um diagnóstico individual --
    cruzar ponto de pessoa específica com "aplique esta técnica nela"
    seria vigilância de desempenho, não IA Central.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import MetaData, create_engine, func, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lape.config import DB_PATH as DB_PATH_PADRAO  # noqa: E402

# ==========================================================================
# Configuração
# ==========================================================================
LATENCIA_CRITICA_MESES = 6.0
REFRESH_MS = 90_000  # recarrega a página sozinha, para uso como painel de TV
DIAS_POR_MES = 30.44


def _resolver_db() -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--db", type=Path, default=None)
    args, _ = parser.parse_known_args(sys.argv[1:])
    if args.db:
        return args.db
    if os.environ.get("LAPE_DB"):
        return Path(os.environ["LAPE_DB"])
    return DB_PATH_PADRAO


DB_PATH = _resolver_db()

st.set_page_config(
    page_title="LAPE — Painel 4K",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================================================
# CSS — Glassmorphism + Cyberpunk + responsivo 4K
# ==========================================================================
CSS = """
<style>
:root{
  --bg-fundo: #04060c;
  --bg-fundo-2: #070c18;
  --neon-cyan: #00f6ff;
  --neon-blue: #3987e5;
  --neon-magenta: #ff2bd6;
  --neon-verde: #16f2b3;
  --critico: #ff2b57;
  --alerta: #ffb020;
  --vidro: rgba(10, 18, 36, 0.55);
  --vidro-2: rgba(6, 10, 22, 0.72);
  --borda: rgba(0, 246, 255, 0.22);
  --texto: #eaf6ff;
  --texto-2: #8fa3c4;
}

/* fundo geral: radial escuro com leve vinheta azul, textura de "sala de
   servidor" em vez de um preto chapado */
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(ellipse 1400px 900px at 15% -10%, rgba(0,246,255,0.10), transparent 60%),
    radial-gradient(ellipse 1200px 800px at 110% 10%, rgba(255,43,214,0.08), transparent 55%),
    linear-gradient(180deg, var(--bg-fundo) 0%, var(--bg-fundo-2) 100%);
  color: var(--texto);
}
[data-testid="stHeader"]{ background: transparent; }
[data-testid="stSidebar"]{ background: var(--vidro-2); border-right: 1px solid var(--borda); }
.block-container{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 100%; }

h1, h2, h3, h4 { color: var(--texto) !important; letter-spacing: .02em; }
p, span, div, label { color: var(--texto); }

/* ---------------------------------------------------------------- */
/* Scanline -- varredura horizontal sutil de tela militar/laboratório */
/* ---------------------------------------------------------------- */
.scanlines{
  position: fixed; inset: 0; pointer-events: none; z-index: 9998;
  background: repeating-linear-gradient(
    to bottom, rgba(255,255,255,0.020) 0px, rgba(255,255,255,0.020) 1px,
    transparent 2px, transparent 4px);
  mix-blend-mode: overlay;
}
.scanlines::after{
  content: ""; position: absolute; left: 0; right: 0; height: 140px; top: -140px;
  background: linear-gradient(to bottom, transparent, rgba(0,246,255,0.07), transparent);
  animation: varrer-tela 7s linear infinite;
}
@keyframes varrer-tela{ from{ top:-140px; } to{ top:100%; } }

/* ---------------------------------------------------------------- */
/* Cartões KPI -- Glassmorphism com feixe de luz girando na borda      */
/* ---------------------------------------------------------------- */
.kpi-card{
  position: relative;
  background: linear-gradient(160deg, var(--vidro), var(--vidro-2));
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  border: 1px solid var(--borda);
  border-radius: 18px;
  padding: 1.3rem 1.5rem 1.1rem;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.55), 0 0 24px -8px rgba(0,246,255,0.35);
  animation: respirar 3.6s ease-in-out infinite;
  height: 100%;
}
@keyframes respirar{
  0%, 100% { box-shadow: 0 8px 32px rgba(0,0,0,0.55), 0 0 20px -8px rgba(0,246,255,0.30); }
  50%      { box-shadow: 0 8px 36px rgba(0,0,0,0.60), 0 0 34px -6px rgba(0,246,255,0.55); }
}
/* feixe de luz correndo pelo perímetro -- conic-gradient mascarado só na
   borda (mask-composite: exclude deixa só o "anel", não o miolo) */
.kpi-card::before{
  content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1.5px;
  background: conic-gradient(from 0deg, transparent 0%, var(--neon-cyan) 6%, transparent 16%, transparent 100%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  animation: girar-feixe 4s linear infinite;
  pointer-events: none;
}
@keyframes girar-feixe{ to{ transform: rotate(360deg); } }

.kpi-card.critico{
  border-color: rgba(255,43,87,0.55);
  animation: pulso-critico 1.15s ease-in-out infinite;
}
.kpi-card.critico::before{
  background: conic-gradient(from 0deg, transparent 0%, var(--critico) 6%, transparent 16%, transparent 100%);
  animation: girar-feixe 1.4s linear infinite;
}
@keyframes pulso-critico{
  0%, 100% { box-shadow: 0 0 18px -4px rgba(255,43,87,0.55); border-color: rgba(255,43,87,0.5); }
  50%      { box-shadow: 0 0 46px 6px rgba(255,43,87,0.85); border-color: rgba(255,43,87,0.95); }
}

.kpi-rotulo{
  font-size: clamp(.72rem, .8vw, .95rem); text-transform: uppercase; letter-spacing: .09em;
  color: var(--texto-2); font-weight: 600; margin-bottom: .35rem;
}
.kpi-valor{
  font-size: clamp(1.9rem, 3.1vw, 3.4rem); font-weight: 800; line-height: 1;
  font-variant-numeric: tabular-nums; color: var(--neon-cyan);
  text-shadow: 0 0 18px rgba(0,246,255,0.55);
}
.kpi-card.critico .kpi-valor{ color: var(--critico); text-shadow: 0 0 18px rgba(255,43,87,0.7); }
.kpi-sub{ font-size: clamp(.68rem, .75vw, .85rem); color: var(--texto-2); margin-top: .3rem; }

/* "odômetro": leve glitch RGB-split no instante em que o número muda */
.kpi-valor.glitch{ animation: glitch-num .5s steps(2, end) 1; }
@keyframes glitch-num{
  0%   { text-shadow: 2px 0 var(--neon-magenta), -2px 0 var(--neon-cyan); transform: translateX(0); }
  30%  { text-shadow: -3px 0 var(--neon-magenta), 3px 0 var(--neon-cyan); transform: translateX(1px); }
  60%  { text-shadow: 3px 0 var(--neon-magenta), -3px 0 var(--neon-cyan); transform: translateX(-1px); }
  100% { text-shadow: 0 0 18px rgba(0,246,255,0.55); transform: translateX(0); }
}
/* explosão discreta de partículas quando o número sobe */
.particulas{ position: absolute; inset: 0; pointer-events: none; overflow: visible; }
.particula{
  position: absolute; width: 4px; height: 4px; border-radius: 50%;
  background: var(--neon-cyan); box-shadow: 0 0 6px 1px var(--neon-cyan);
  left: var(--px, 50%); top: var(--py, 30%);
  animation: explodir 0.9s ease-out forwards;
}
@keyframes explodir{
  0%   { opacity: 1; transform: translate(0,0) scale(1); }
  100% { opacity: 0; transform: translate(var(--dx,0), var(--dy,-24px)) scale(.3); }
}

/* ---------------------------------------------------------------- */
/* Alerta crítico -- pisca de verdade, cor de emergência              */
/* ---------------------------------------------------------------- */
.alerta-critico{
  position: relative;
  background: linear-gradient(160deg, rgba(60,8,18,0.55), rgba(20,4,10,0.75));
  border: 1px solid rgba(255,43,87,0.6);
  border-radius: 14px;
  padding: .9rem 1.2rem;
  margin-bottom: .6rem;
  backdrop-filter: blur(14px);
  animation: piscar-alerta 1.1s ease-in-out infinite;
}
@keyframes piscar-alerta{
  0%, 100% { box-shadow: 0 0 16px -2px rgba(255,43,87,0.5); opacity: 1; }
  50%      { box-shadow: 0 0 44px 6px rgba(255,43,87,0.95); opacity: .88; }
}
.alerta-critico b{ color: #ffdfe6; }
.alerta-critico small{ color: rgba(255,223,230,.75); }

.sugestao-card{
  background: linear-gradient(160deg, rgba(20,20,50,0.55), rgba(8,8,26,0.75));
  border: 1px solid rgba(123,79,247,0.45);
  border-radius: 14px; padding: 1rem 1.3rem; backdrop-filter: blur(14px);
}

.secao-titulo{
  display: flex; align-items: center; gap: .5rem;
  font-size: clamp(1rem, 1.3vw, 1.5rem); font-weight: 700; margin: 1.1rem 0 .6rem;
  color: var(--neon-cyan); text-shadow: 0 0 12px rgba(0,246,255,0.4);
}
.pulso-vivo{
  width: 10px; height: 10px; border-radius: 50%; background: var(--neon-verde);
  box-shadow: 0 0 8px 2px var(--neon-verde); animation: respirar-ponto 1.8s ease-in-out infinite;
  display: inline-block;
}
@keyframes respirar-ponto{ 0%,100%{opacity:1;} 50%{opacity:.4;} }

/* 4K: tudo cresce quando a tela é grande de verdade */
@media (min-width: 2560px){
  .kpi-valor{ font-size: 4.2rem; }
  .kpi-rotulo{ font-size: 1.1rem; }
  .secao-titulo{ font-size: 1.9rem; }
}
@media (min-width: 3840px){
  .kpi-valor{ font-size: 5.6rem; }
  .kpi-rotulo{ font-size: 1.35rem; }
  .kpi-sub{ font-size: 1.05rem; }
  .secao-titulo{ font-size: 2.4rem; }
  .block-container{ padding-left: 2.5rem; padding-right: 2.5rem; }
}
</style>
<div class="scanlines"></div>
"""


# ==========================================================================
# Camada de dados -- SQLAlchemy Core sobre o schema JÁ existente
# ==========================================================================
# Reflexão (Table(..., autoload_with=engine)) em vez de modelos declarados à
# mão: o dono deste schema é o sistema principal (sql/schema.sql). Escrever
# 30 colunas de novo aqui seria a mesma informação duplicada, um jeito a
# mais de ficar desatualizado. Este painel só LÊ -- nenhuma escrita.
@st.cache_resource(show_spinner=False)
def obter_engine(caminho_db: str):
    return create_engine(f"sqlite:///{caminho_db}", future=True)


@st.cache_resource(show_spinner=False)
def obter_tabelas(_engine):
    md = MetaData()
    md.reflect(bind=_engine, only=["articles", "research_lines", "submissions", "goals", "ponto"])
    return md.tables


@st.cache_data(ttl=60, show_spinner=False)
def carregar_artigos(caminho_db: str) -> pd.DataFrame:
    engine = obter_engine(caminho_db)
    t = obter_tabelas(engine)
    artigos, linhas = t["articles"], t["research_lines"]
    consulta = select(
        artigos.c.id, artigos.c.title, artigos.c.status,
        artigos.c.research_line_id, linhas.c.name.label("linha"),
        artigos.c.started_on, artigos.c.first_submission_on,
        artigos.c.accepted_on, artigos.c.published_on, artigos.c.year_published,
        artigos.c.journal, artigos.c.study_type,
        artigos.c.wos_citations, artigos.c.scopus_citations, artigos.c.openalex_citations,
    ).select_from(artigos.outerjoin(linhas, artigos.c.research_line_id == linhas.c.id))
    df = pd.read_sql(consulta, engine)
    for col in ("started_on", "first_submission_on", "accepted_on", "published_on"):
        df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
    for col in ("wos_citations", "scopus_citations", "openalex_citations"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["linha"] = df["linha"].fillna("Sem linha declarada")
    return df


@st.cache_data(ttl=60, show_spinner=False)
def carregar_submissoes(caminho_db: str) -> pd.DataFrame:
    engine = obter_engine(caminho_db)
    t = obter_tabelas(engine)
    subs, artigos = t["submissions"], t["articles"]
    consulta = select(
        subs.c.id, subs.c.article_id, subs.c.journal, subs.c.submitted_on,
        subs.c.decision, subs.c.decision_on,
        artigos.c.title, artigos.c.internal_code, artigos.c.research_line_id,
    ).select_from(subs.join(artigos, subs.c.article_id == artigos.c.id))
    df = pd.read_sql(consulta, engine)
    df["submitted_on"] = pd.to_datetime(df["submitted_on"], errors="coerce", format="mixed")
    df["decision_on"] = pd.to_datetime(df["decision_on"], errors="coerce", format="mixed")
    return df


@st.cache_data(ttl=60, show_spinner=False)
def carregar_ponto(caminho_db: str) -> pd.DataFrame:
    """Sessões de ponto do LABORATÓRIO INTEIRO, sem member_id na saída --
    de propósito. O que este painel faz com isto é uma leitura AGREGADA de
    presença coletiva (ver `calcular_correlacao_presenca`), nunca por
    pessoa: cruzar hora de ponto individual com "o coordenador deve aplicar
    esta técnica psicológica nesta pessoa" é vigilância de desempenho, não
    IA Central -- por isso a consulta nem carrega `member_id`."""
    engine = obter_engine(caminho_db)
    t = obter_tabelas(engine)
    ponto = t["ponto"]
    consulta = select(ponto.c.entrada, ponto.c.saida, ponto.c.visto_em)
    df = pd.read_sql(consulta, engine)
    df["entrada"] = pd.to_datetime(df["entrada"], errors="coerce", format="mixed")
    fim = pd.to_datetime(df["saida"], errors="coerce", format="mixed")
    fim = fim.fillna(pd.to_datetime(df["visto_em"], errors="coerce", format="mixed"))
    df["horas"] = (fim - df["entrada"]).dt.total_seconds() / 3600
    # sessao aberta sem nenhum sinal de vida ainda, ou dado corrompido
    df = df[df["entrada"].notna() & df["horas"].notna() & (df["horas"] > 0)]
    # teto de sanidade -- uma sessao mal fechada de dias nao vira "presenca"
    df["horas"] = df["horas"].clip(upper=16)
    return df[["entrada", "horas"]]


@st.cache_data(ttl=60, show_spinner=False)
def carregar_meta_do_ano(caminho_db: str, ano: int) -> pd.DataFrame:
    engine = obter_engine(caminho_db)
    t = obter_tabelas(engine)
    goals = t["goals"]
    consulta = select(goals.c.code, goals.c.target).where(goals.c.year == ano)
    return pd.read_sql(consulta, engine)


# ==========================================================================
# "IA Central" -- alertas, sugestão metodológica, projeção de ritmo
# ==========================================================================
def _garantir_datetime(df: pd.DataFrame, *colunas: str) -> pd.DataFrame:
    """Converte para datetime64 se ainda não for -- idempotente em coluna
    já convertida, e não quebra em coluna vazia/toda nula (dtype object),
    que é exatamente o estado de um laboratório recém-instalado, sem
    submissão nenhuma ainda. As funções de IA Central chamam isto pra não
    depender de quem carregou o DataFrame já ter feito essa conversão."""
    df = df.copy()
    for col in colunas:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
    return df


def calcular_kpis(artigos: pd.DataFrame, submissoes: pd.DataFrame) -> dict:
    artigos = _garantir_datetime(artigos, "started_on", "first_submission_on", "published_on")
    submissoes = _garantir_datetime(submissoes, "submitted_on", "decision_on")
    agora = pd.Timestamp.now()
    total = len(artigos)
    em_producao = int((artigos["status"] == "em_producao").sum())

    # tempo de escrita: do início até a primeira submissão (ou, faltando
    # essa data, até a publicação) -- só onde as duas pontas existem.
    fim_escrita = artigos["first_submission_on"].fillna(artigos["published_on"])
    dias_escrita = (fim_escrita - artigos["started_on"]).dt.days
    dias_escrita = dias_escrita[(dias_escrita.notna()) & (dias_escrita > 0)]
    tempo_escrita_meses = float(dias_escrita.median() / DIAS_POR_MES) if len(dias_escrita) else None

    # espera na revisão: submissões AINDA sem decisão, até agora
    pendentes = submissoes[submissoes["decision"].isna() & submissoes["submitted_on"].notna()].copy()
    pendentes["meses_de_espera"] = (agora - pendentes["submitted_on"]).dt.days / DIAS_POR_MES
    espera_mediana_meses = float(pendentes["meses_de_espera"].median()) if len(pendentes) else None

    # taxa de aceite: decisões JÁ tomadas (aceite ou rejeição), ano corrente
    decididas = submissoes[submissoes["decision"].isin(["aceito", "rejeitado"])]
    decididas_ano = decididas[decididas["decision_on"].dt.year == agora.year]
    base_taxa = decididas_ano if len(decididas_ano) else decididas
    if len(base_taxa):
        taxa_aceite = float((base_taxa["decision"] == "aceito").mean())
    else:
        taxa_aceite = None  # sem decisão nenhuma ainda -- não é "0%", é "sem dado"

    publicados_ano = int(((artigos["status"] == "publicado") & (artigos["year_published"] == agora.year)).sum())

    return {
        "total_artigos": total,
        "em_producao": em_producao,
        "tempo_escrita_meses": tempo_escrita_meses,
        "espera_mediana_meses": espera_mediana_meses,
        "taxa_aceite": taxa_aceite,
        "publicados_ano": publicados_ano,
        "pendentes": pendentes,
    }


def gerar_alertas_latencia(pendentes: pd.DataFrame, limite_meses: float) -> list[dict]:
    """Uma submissão por alerta -- artigo e revista de verdade, não um
    "Artigo X" genérico: é exatamente esse dado que faz a cobrança ser
    possível de fazer."""
    criticas = pendentes[pendentes["meses_de_espera"] >= limite_meses].sort_values(
        "meses_de_espera", ascending=False)
    alertas = []
    for _, linha in criticas.iterrows():
        titulo = linha["title"] or linha["internal_code"] or f"artigo #{linha['article_id']}"
        revista = linha["journal"] or "revista não registrada"
        alertas.append({
            "mensagem": f"⚠️ ALERTA DE LATÊNCIA ACADÊMICA: {titulo} requer cobrança na revista {revista}",
            "meses": round(float(linha["meses_de_espera"]), 1),
            "submetido_em": linha["submitted_on"],
        })
    return alertas


def sugerir_mudanca_metodologica(artigos: pd.DataFrame, submissoes: pd.DataFrame) -> dict | None:
    """Só dispara quando a taxa de aceite do período é 0% DE VERDADE (há
    decisão tomada, e nenhuma foi aceite) -- nunca quando simplesmente não
    há decisão nenhuma ainda, que é "sem dado", não "reprovação"."""
    submissoes = _garantir_datetime(submissoes, "submitted_on", "decision_on")
    agora = pd.Timestamp.now()
    decididas = submissoes[submissoes["decision"].isin(["aceito", "rejeitado"])]
    decididas_ano = decididas[decididas["decision_on"].dt.year == agora.year]
    if not len(decididas_ano) or (decididas_ano["decision"] == "aceito").any():
        return None

    historico = submissoes.merge(
        artigos[["id", "linha", "study_type"]], left_on="article_id", right_on="id", how="left")
    aceites_historicos = historico[
        (historico["decision"] == "aceito")
        & ~historico.index.isin(decididas_ano.index)]
    if not len(aceites_historicos):
        return None

    por_linha = (aceites_historicos.groupby("linha").size()
                 .sort_values(ascending=False).head(3))
    return {
        "linhas_mais_aceitas": list(por_linha.items()),
        "total_rejeicoes_no_periodo": int(len(decididas_ano)),
    }


def projetar_ritmo(artigos: pd.DataFrame, meta_ano: pd.DataFrame, ano: int) -> dict:
    """Estimativa de ritmo -- NUNCA uma meta. A meta é o que a coordenação
    declarou (tabela `goals`); isto aqui é só "no ritmo atual, dá pra
    chegar em quanto", pra comparar com o que foi decidido."""
    agora = pd.Timestamp.now()
    publicados_ano = artigos[
        (artigos["status"] == "publicado") & (artigos["year_published"] == ano)]
    meses_passados = max(1.0, agora.dayofyear / (365.25 / 12))
    ritmo_mensal = len(publicados_ano) / meses_passados
    projecao_fim_de_ano = round(ritmo_mensal * 12)

    alvo_declarado = None
    if len(meta_ano):
        linha_artigos = meta_ano[meta_ano["code"].astype(str).str.contains("artig", case=False)]
        if len(linha_artigos):
            alvo_declarado = int(linha_artigos.iloc[0]["target"])

    return {
        "publicados_ate_agora": len(publicados_ano),
        "ritmo_mensal": round(ritmo_mensal, 2),
        "projecao_fim_de_ano": projecao_fim_de_ano,
        "meta_declarada": alvo_declarado,
    }


def calcular_correlacao_presenca(ponto: pd.DataFrame) -> dict:
    """Presença COLETIVA do laboratório na semana atual, contra a média das
    últimas semanas -- nunca por pessoa (ver o porquê em `carregar_ponto`).
    Sem pelo menos 2 semanas anteriores fechadas para comparar, não há
    baseline: retorna `variacao_pct=None` em vez de inventar uma linha de
    base a partir de quase nada."""
    if not len(ponto):
        return {"horas_semana_atual": 0.0, "horas_media_semanal": None, "variacao_pct": None, "semanas_com_dado": 0}

    semana = ponto["entrada"].dt.isocalendar()
    ponto = ponto.assign(ano_iso=semana["year"], semana_iso=semana["week"])
    agora = pd.Timestamp.now().isocalendar()

    por_semana = ponto.groupby(["ano_iso", "semana_iso"])["horas"].sum()
    chave_atual = (agora.year, agora.week)
    horas_semana_atual = float(por_semana.get(chave_atual, 0.0))

    anteriores = por_semana.drop(index=chave_atual, errors="ignore").tail(8)
    if len(anteriores) < 2:
        return {"horas_semana_atual": round(horas_semana_atual, 1), "horas_media_semanal": None,
                "variacao_pct": None, "semanas_com_dado": len(anteriores)}

    media = float(anteriores.mean())
    variacao_pct = ((horas_semana_atual - media) / media * 100) if media > 0 else None
    return {
        "horas_semana_atual": round(horas_semana_atual, 1),
        "horas_media_semanal": round(media, 1),
        "variacao_pct": round(variacao_pct, 1) if variacao_pct is not None else None,
        "semanas_com_dado": len(anteriores),
    }


# Técnicas de psicologia esportiva -- ancoradas na literatura da área, cada
# uma associada ao padrão de dado que a torna pertinente. Isto é apoio à
# decisão para a REUNIÃO de coordenação (um ponto de partida para discutir
# com a equipe), nunca um diagnóstico clínico nem um veredito automático.
_TECNICAS_INTERVENCAO = {
    "metas_smart": {
        "titulo": "Definição de metas SMART",
        "descricao": ("Presença em queda e ritmo abaixo do necessário juntos costumam indicar "
                       "falta de clareza de objetivo, não falta de esforço. Vale pautar metas "
                       "específicas e com prazo por artigo em produção na próxima reunião."),
    },
    "regulacao_ansiedade": {
        "titulo": "Regulação de ansiedade (respiração/exposição gradual à escrita)",
        "descricao": ("Presença mantida ou em alta com ritmo de publicação abaixo da média "
                       "histórica sugere esforço que não está virando entrega -- um padrão "
                       "comum de bloqueio de escrita ou perfeccionismo, não de desengajamento."),
    },
    "biofeedback_espera": {
        "titulo": "Biofeedback / manejo da frustração com a espera editorial",
        "descricao": ("A espera mediana na revisão já está no território crítico -- frustração "
                       "com um processo fora do controle do laboratório pode estar drenando o "
                       "ritmo em outras frentes. Técnicas de regulação fisiológica ajudam a "
                       "equipe a seguir produzindo enquanto espera, em vez de travar."),
    },
    "reforco_positivo": {
        "titulo": "Reforço positivo -- manter o que está funcionando",
        "descricao": ("Nenhum dos sinais acompanhados aponta alerta no momento. Vale nomear "
                       "isso explicitamente na reunião: reconhecer o que está indo bem sustenta "
                       "o padrão, tanto quanto corrigir o que não está."),
    },
}


def gerar_diagnostico_intervencao(kpis: dict, projecao: dict, presenca: dict,
                                   artigos: pd.DataFrame, ano_atual: int) -> dict:
    """Ana, protocolo de 4 passos: monta o raciocínio completo (para quem
    quiser abrir e ver cada etapa) e resume no final numa técnica só, para
    o cartão simplificado do painel.

    Passo 1 -- diagnóstico frio: publicados vs. em andamento, direto do banco.
    Passo 2 -- correlação coletiva: presença da semana (agregada, nunca por
               pessoa -- ver `calcular_correlacao_presenca`) contra o ritmo.
    Passo 3 -- tendência: projeção para 6 meses a partir do ritmo atual,
               contra a média histórica ANUAL de fato calculada dos anos
               anteriores do próprio laboratório (não um número fixo).
    Passo 4 -- intervenção: a técnica de `_TECNICAS_INTERVENCAO` cujo
               gatilho bate com o padrão encontrado nos passos 1-3.
    """
    publicados_total = int((artigos["status"] == "publicado").sum())
    em_andamento_total = int(len(artigos) - publicados_total)

    anos_anteriores = artigos[
        (artigos["status"] == "publicado") & (artigos["year_published"].notna())
        & (artigos["year_published"] < ano_atual)
    ]
    media_historica_anual = None
    if len(anos_anteriores):
        por_ano = anos_anteriores.groupby("year_published").size()
        if len(por_ano) >= 2:
            media_historica_anual = float(por_ano.mean())

    projecao_6_meses = round(projecao["ritmo_mensal"] * 6, 1)
    esperado_historico_6_meses = round(media_historica_anual / 2, 1) if media_historica_anual else None

    variacao = presenca["variacao_pct"]
    ritmo_abaixo_da_media = (
        media_historica_anual is not None and projecao["ritmo_mensal"] * 12 < media_historica_anual
    )
    espera_critica = kpis["espera_mediana_meses"] is not None and kpis["espera_mediana_meses"] >= LATENCIA_CRITICA_MESES

    if variacao is not None and variacao <= -10 and ritmo_abaixo_da_media:
        chave_tecnica = "metas_smart"
    elif variacao is not None and variacao >= 0 and ritmo_abaixo_da_media:
        chave_tecnica = "regulacao_ansiedade"
    elif espera_critica:
        chave_tecnica = "biofeedback_espera"
    else:
        chave_tecnica = "reforco_positivo"

    return {
        "passo1_diagnostico": {"publicados": publicados_total, "em_andamento": em_andamento_total},
        "passo2_correlacao": presenca,
        "passo3_tendencia": {
            "ritmo_mensal_atual": projecao["ritmo_mensal"],
            "projecao_6_meses": projecao_6_meses,
            "media_historica_anual": round(media_historica_anual, 1) if media_historica_anual else None,
            "esperado_historico_6_meses": esperado_historico_6_meses,
        },
        "passo4_tecnica": chave_tecnica,
        "tecnica": _TECNICAS_INTERVENCAO[chave_tecnica],
    }


# ==========================================================================
# Gráfico 1 — Dispersão 3D por linha de pesquisa
# ==========================================================================
def montar_dispersao_3d(artigos: pd.DataFrame) -> go.Figure:
    fim_escrita = artigos["first_submission_on"].fillna(artigos["published_on"])
    artigos = artigos.assign(
        dias_escrita=(fim_escrita - artigos["started_on"]).dt.days,
        citacoes=artigos["wos_citations"] + artigos["scopus_citations"],
    )
    por_linha = artigos.groupby("linha").agg(
        artigos_publicados=("status", lambda s: int((s == "publicado").sum())),
        citacoes_totais=("citacoes", "sum"),
        tempo_escrita_meses=("dias_escrita", lambda s: (s[(s.notna()) & (s > 0)].median() / DIAS_POR_MES)
                              if s[(s.notna()) & (s > 0)].size else 0),
        total_artigos=("status", "size"),
    ).reset_index()
    por_linha["tempo_escrita_meses"] = por_linha["tempo_escrita_meses"].fillna(0)
    por_linha = por_linha[por_linha["total_artigos"] > 0]

    paleta = ["#00f6ff", "#3987e5", "#ff2bd6", "#16f2b3", "#ffb020",
              "#7b4ff7", "#ff5a5f", "#4ade80"]
    cores = [paleta[i % len(paleta)] for i in range(len(por_linha))]

    # Amplitude de pulsação por esfera, proporcional ao IMPACTO da linha
    # (citações) -- não ao volume (que já governa o tamanho). Fica no
    # customdata, não no marker.size: o JS de animação (ver
    # `renderizar_grafico_3d_animado`) lê isto para saber o quanto cada
    # esfera deve "respirar" em tempo real, sem o servidor recalcular nada.
    maior_citacao = max(1, int(por_linha["citacoes_totais"].max()))
    impacto_norm = (por_linha["citacoes_totais"] / maior_citacao).tolist()

    fig = go.Figure(data=[go.Scatter3d(
        x=por_linha["artigos_publicados"],
        y=por_linha["citacoes_totais"],
        z=por_linha["tempo_escrita_meses"],
        mode="markers+text",
        text=por_linha["linha"],
        textposition="top center",
        textfont=dict(color="#eaf6ff", size=11),
        marker=dict(
            size=np.clip(por_linha["total_artigos"] * 3.2, 10, 40),
            color=cores,
            opacity=0.88,
            line=dict(color="rgba(255,255,255,0.55)", width=1),
        ),
        customdata=impacto_norm,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Artigos publicados: %{x}<br>"
            "Citações totais (WoS+Scopus): %{y}<br>"
            "Tempo médio de escrita: %{z:.1f} meses"
            "<extra></extra>"
        ),
    )])
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
        scene=dict(
            xaxis=dict(title="Artigos publicados", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgba(0,246,255,0.15)", zerolinecolor="rgba(0,246,255,0.25)"),
            yaxis=dict(title="Citações totais (WoS/Scopus)", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgba(0,246,255,0.15)", zerolinecolor="rgba(0,246,255,0.25)"),
            zaxis=dict(title="Tempo médio de escrita (meses)", backgroundcolor="rgba(0,0,0,0)",
                       gridcolor="rgba(0,246,255,0.15)", zerolinecolor="rgba(0,246,255,0.25)"),
            camera=dict(eye=dict(x=1.6, y=1.5, z=1.0)),
        ),
        showlegend=False,
    )
    return fig


# ==========================================================================
# Gráfico 2 — Funil cilíndrico 3D (Em Escrita -> Submetidos -> Publicados)
# ==========================================================================
def _malha_frustum(z0: float, z1: float, r0: float, r1: float, n: int = 64):
    """Vértices/faces de um segmento cilíndrico (cone truncado) entre duas
    alturas, com tampas -- o bloco de construção do funil. `r0 == r1`
    produz um cilindro reto; raios diferentes produzem o afunilamento
    entre um estágio e o próximo, sem costura entre eles."""
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    bx, by, bz = r0 * np.cos(theta), r0 * np.sin(theta), np.full(n, z0)
    tx, ty, tz = r1 * np.cos(theta), r1 * np.sin(theta), np.full(n, z1)
    xs = np.concatenate([bx, tx, [0.0], [0.0]])
    ys = np.concatenate([by, ty, [0.0], [0.0]])
    zs = np.concatenate([bz, tz, [z0], [z1]])
    centro_baixo, centro_cima = 2 * n, 2 * n + 1

    i, j, k = [], [], []
    for idx in range(n):
        nxt = (idx + 1) % n
        # parede lateral (dois triângulos por segmento do anel)
        i += [idx, idx]
        j += [nxt, n + nxt]
        k += [n + nxt, n + idx]
        # tampas
        i += [centro_baixo, centro_cima]
        j += [nxt, n + idx]
        k += [idx, n + nxt]
    return xs, ys, zs, np.array(i), np.array(j), np.array(k)


def _particulas_do_funil(estagios: list[dict]) -> go.Scatter3d:
    """Partículas de luz fluindo por dentro de cada estágio do funil.

    Não são um evento "este artigo mudou de status agora" -- o Painel 4K
    recarrega a página inteira a cada `REFRESH_MS` (sem canal permanente
    com o servidor), então não há como saber, no navegador, o instante
    exato de uma mudança real no banco. O que dá pra fazer com honestidade
    aqui é uma densidade de partículas PROPORCIONAL ao volume real de cada
    estágio (mais partículas onde há mais artigos), caindo em looping
    contínuo -- uma leitura visual do RITMO de produção, não um replay
    evento a evento.
    """
    rng = np.random.default_rng(7)
    maior = max(1, max(e["n"] for e in estagios))
    xs, ys, zs, cores, meta = [], [], [], [], []
    for e in estagios:
        qtd = int(np.clip(round(2 + 8 * e["n"] / maior), 2, 10))
        for _ in range(qtd):
            ang = rng.uniform(0, 2 * np.pi)
            r = rng.uniform(0.25, 0.85) * e["raio"]
            xs.append(r * np.cos(ang))
            ys.append(r * np.sin(ang))
            zs.append(rng.uniform(e["z1"], e["z0"]))
            cores.append(e["cor"])
            meta.append((e["z0"], e["z1"], float(rng.uniform(0, 1))))
    return go.Scatter3d(
        x=xs, y=ys, z=zs, mode="markers",
        marker=dict(size=4, color=cores, opacity=0.9,
                    line=dict(color="rgba(255,255,255,0.6)", width=0.5)),
        customdata=meta,
        hoverinfo="skip", showlegend=False, name="fluxo",
    )


def montar_funil_cilindrico(contagens: dict[str, int]) -> go.Figure:
    etapas = [("Em Escrita", contagens.get("em_escrita", 0), "#00f6ff"),
              ("Submetidos", contagens.get("submetidos", 0), "#3987e5"),
              ("Publicados", contagens.get("publicados", 0), "#16f2b3")]
    maior = max(1, max(n for _, n, _ in etapas))
    raio_min, raio_max = 0.9, 3.0

    def raio(n: int) -> float:
        # area (nao o raio) proporcional a contagem -- raio linear
        # exageraria a diferenca visual entre etapas
        return raio_min + (raio_max - raio_min) * np.sqrt(n / maior)

    fig = go.Figure()
    altura_etapa = 2.6
    z_atual = 0.0
    estagios_geo = []
    for idx, (nome, n, cor) in enumerate(etapas):
        r_topo = raio(etapas[idx - 1][1]) if idx > 0 else raio(n)
        r_base = raio(n)
        z0, z1 = z_atual, z_atual - altura_etapa
        xs, ys, zs, i, j, k = _malha_frustum(z0, z1, r_topo, r_base, n=64)
        fig.add_trace(go.Mesh3d(
            x=xs, y=ys, z=zs, i=i, j=j, k=k,
            color=cor, opacity=0.72, flatshading=False,
            lighting=dict(ambient=0.55, diffuse=0.7, specular=0.9, roughness=0.35, fresnel=0.3),
            lightposition=dict(x=100, y=200, z=150),
            hoverinfo="skip",
            name=nome,
        ))
        # anel luminoso na fronteira de baixo do estagio, com o rotulo de verdade
        theta = np.linspace(0, 2 * np.pi, 64)
        pct = f"{n / etapas[0][1] * 100:.0f}%" if etapas[0][1] else "—"
        fig.add_trace(go.Scatter3d(
            x=r_base * np.cos(theta), y=r_base * np.sin(theta), z=np.full(64, z1),
            mode="lines", line=dict(color=cor, width=6),
            hovertemplate=f"<b>{nome}</b><br>{n} artigo(s)<br>{pct} do topo do funil<extra></extra>",
            name=nome, showlegend=False,
        ))
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[z1 - 0.35], mode="text",
            text=[f"<b>{nome}</b><br>{n}"], textfont=dict(color=cor, size=15),
            hoverinfo="skip", showlegend=False,
        ))
        estagios_geo.append({"nome": nome, "cor": cor, "z0": z0, "z1": z1,
                              "raio": max(r_topo, r_base), "n": n})
        z_atual = z1

    fig.add_trace(_particulas_do_funil(estagios_geo))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="manual", aspectratio=dict(x=1, y=1, z=1.5),
            camera=dict(eye=dict(x=1.9, y=1.9, z=0.6)),
        ),
        showlegend=False,
    )
    return fig


# ==========================================================================
# Animação 3D client-side (órbita + pulsação + fluxo de partículas)
# ==========================================================================
def renderizar_grafico_3d_animado(fig: go.Figure, div_id: str, modo: str, altura: int = 520):
    """Publica a figura como HTML autocontido -- Plotly.js embutido no
    próprio HTML (`include_plotlyjs=True`, lido do pacote Python instalado
    localmente), não carregado de um CDN. Essencial aqui: esta tela roda
    numa TV de parede que pode estar numa rede de laboratório sem internet
    confiável, e não pode ficar em branco por causa disso.

    Por cima da figura estática, injeta uma animação contínua em
    JavaScript puro (órbita de câmera + pulsação de esferas para a
    dispersão 3D, ou fluxo de partículas para o funil) que roda inteiramente
    no navegador via `Plotly.restyle`/`Plotly.relayout` -- sem round-trip
    com o servidor a cada quadro. "Tempo real" aqui é isso: a MOLDURA
    (câmera, brilho, partículas) se move sozinha; o DADO por trás dela só
    atualiza quando a página inteira recarrega, a cada `REFRESH_MS`.
    """
    import plotly.io as pio

    corpo = pio.to_html(fig, include_plotlyjs=True, full_html=False,
                         div_id=div_id, config={"displayModeBar": False})

    if modo == "dispersao":
        script_animacao = """
          var base = paraArray(gd.data[0].marker.size);
          var impactoBruto = paraArray(gd.data[0].customdata);
          var impacto = impactoBruto.length ? impactoBruto : base.map(function () { return 0.4; });
          var t0 = Date.now();
          setInterval(function () {
            var t = (Date.now() - t0) / 1000;
            var novo = base.map(function (s, i) {
              var amp = impacto[i] || 0.25;
              return Math.max(6, s + s * 0.32 * amp * (0.5 + 0.5 * Math.sin(t * 1.7 + i * 1.3)));
            });
            var angulo = 1.6 + t * 0.06;
            Plotly.restyle(gd, {'marker.size': [novo]}, [0]);
            Plotly.relayout(gd, {'scene.camera.eye': {x: 1.9 * Math.cos(angulo), y: 1.9 * Math.sin(angulo), z: 1.0}});
          }, 90);
        """
    else:
        script_animacao = """
          var idx = gd.data.length - 1;
          var trace = gd.data[idx];
          var z0s = trace.customdata.map(function (cd) { return cd[0]; });
          var z1s = trace.customdata.map(function (cd) { return cd[1]; });
          var fases = trace.customdata.map(function (cd) { return cd[2]; });
          var t0 = Date.now();
          setInterval(function () {
            var t = (Date.now() - t0) / 1000;
            var novoZ = z0s.map(function (z0, i) {
              var z1 = z1s[i], fase = fases[i];
              var progresso = (t * 0.35 + fase) % 1;
              return z0 - progresso * (z0 - z1);
            });
            Plotly.restyle(gd, {z: [novoZ]}, [idx]);
          }, 90);
        """

    script = f"""
    <script>
    (function () {{
      // marker.size (e outros campos vindos de um array numpy) chegam do
      // Plotly.py mais recente como {{dtype, bdata, _inputArray}} em vez de
      // um array JS puro -- .slice()/.map() direto nisso falha calado.
      // Esta função normaliza qualquer um dos formatos para array simples.
      function paraArray(v) {{
        if (Array.isArray(v)) return v.slice();
        if (v && Array.isArray(v._inputArray)) return v._inputArray.slice();
        if (v && v.bdata && v.dtype) {{
          var bin = atob(v.bdata);
          var bytes = new Uint8Array(bin.length);
          for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
          var Ctor = {{f8: Float64Array, f4: Float32Array, i4: Int32Array,
                       i2: Int16Array, i1: Int8Array, u4: Uint32Array,
                       u2: Uint16Array, u1: Uint8Array}}[v.dtype] || Float64Array;
          return Array.from(new Ctor(bytes.buffer));
        }}
        return [];
      }}

      function aguardar(tentativas) {{
        var gd = document.getElementById('{div_id}');
        if (gd && gd.data) {{ {script_animacao} return; }}
        if (tentativas <= 0) return;
        setTimeout(function () {{ aguardar(tentativas - 1); }}, 150);
      }}
      aguardar(40);
    }})();
    </script>
    """
    st.components.v1.html(corpo + script, height=altura + 10, scrolling=False)


# ==========================================================================
# Componentes de UI
# ==========================================================================
def cartao_kpi(rotulo: str, valor: str, sub: str = "", critico: bool = False, chave: str = ""):
    valor_anterior = st.session_state.get(f"kpi_{chave}")
    mudou = valor_anterior is not None and valor_anterior != valor
    st.session_state[f"kpi_{chave}"] = valor

    particulas_html = ""
    if mudou:
        rng = np.random.default_rng(abs(hash(chave)) % (2**32))
        pontos = []
        for _ in range(10):
            ang = rng.uniform(0, 2 * np.pi)
            dist = rng.uniform(18, 46)
            pontos.append(
                f'<span class="particula" style="--px:{rng.uniform(20,80):.0f}%;'
                f'--py:{rng.uniform(20,60):.0f}%;--dx:{dist*np.cos(ang):.0f}px;'
                f'--dy:{dist*np.sin(ang):.0f}px"></span>'
            )
        particulas_html = f'<div class="particulas">{"".join(pontos)}</div>'

    classe_cor = "critico" if critico else ""
    classe_glitch = "glitch" if mudou else ""
    st.markdown(f"""
        <div class="kpi-card {classe_cor}">
          {particulas_html}
          <div class="kpi-rotulo">{rotulo}</div>
          <div class="kpi-valor {classe_glitch}">{valor}</div>
          <div class="kpi-sub">{sub}</div>
        </div>
    """, unsafe_allow_html=True)


def titulo_secao(texto: str, com_pulso: bool = False):
    pulso = '<span class="pulso-vivo"></span>' if com_pulso else ""
    st.markdown(f'<div class="secao-titulo">{pulso} {texto}</div>', unsafe_allow_html=True)


def _renderizar_diagnostico_intervencao(diagnostico: dict):
    """Cartão do painel + os 4 passos do raciocínio, para quem quiser abrir
    e conferir de onde veio a sugestão -- nunca só o veredito final."""
    p1, p2, p3, p4 = (diagnostico["passo1_diagnostico"], diagnostico["passo2_correlacao"],
                       diagnostico["passo3_tendencia"], diagnostico["tecnica"])

    if p2["variacao_pct"] is not None:
        sinal = "+" if p2["variacao_pct"] >= 0 else ""
        presenca_txt = (f'{sinal}{p2["variacao_pct"]:.0f}% de presença coletiva esta semana '
                         f'vs. a média das últimas {p2["semanas_com_dado"]} semanas')
    else:
        presenca_txt = "ainda sem semanas anteriores suficientes para comparar a presença coletiva"

    tendencia_txt = f'ritmo atual projeta {p3["projecao_6_meses"]:.1f} artigo(s) em 6 meses'
    if p3["media_historica_anual"] is not None:
        tendencia_txt += f' (média histórica do laboratório: {p3["esperado_historico_6_meses"]:.1f} no mesmo período)'

    st.markdown(f"""
        <div class="sugestao-card" style="border-color: rgba(0,246,255,0.4);">
          <b>{p4['titulo']}</b><br>
          {p4['descricao']}
        </div>
    """, unsafe_allow_html=True)

    with st.expander("ver o raciocínio dos 4 passos"):
        st.markdown(f"""
            <ol style="margin:0; padding-left:1.2rem; color:var(--texto-2); line-height:1.7;">
              <li><b>Diagnóstico:</b> {p1['publicados']} publicado(s), {p1['em_andamento']} em andamento no banco.</li>
              <li><b>Correlação coletiva:</b> {presenca_txt}.</li>
              <li><b>Tendência:</b> {tendencia_txt}.</li>
              <li><b>Intervenção sugerida:</b> {p4['titulo']}.</li>
            </ol>
            <p style="color:var(--texto-2); font-size:0.82rem; margin-top:.6rem;">
              Leitura sempre AGREGADA do laboratório inteiro, nunca por pesquisador --
              é apoio para a conversa da coordenação, não um diagnóstico individual.
            </p>
        """, unsafe_allow_html=True)


# ==========================================================================
# Layout
# ==========================================================================
def main():
    st.markdown(CSS, unsafe_allow_html=True)

    if not DB_PATH.exists():
        st.error(
            f"Banco não encontrado em `{DB_PATH}`. Rode com "
            f"`streamlit run scripts/lape_streamlit_4k.py -- --db /caminho/db.sqlite` "
            f"ou defina a variável de ambiente `LAPE_DB`."
        )
        st.stop()

    col_titulo, col_relogio = st.columns([3, 1])
    with col_titulo:
        st.markdown(
            '<div class="secao-titulo" style="font-size:clamp(1.4rem,2.2vw,2.4rem);margin-top:0;">'
            '🧠 LAPE — Painel 4K · IA Central</div>',
            unsafe_allow_html=True,
        )
    with col_relogio:
        st.markdown(
            f'<div style="text-align:right;color:var(--texto-2);font-variant-numeric:tabular-nums;">'
            f'{datetime.now().strftime("%d/%m/%Y  %H:%M:%S")}</div>',
            unsafe_allow_html=True,
        )

    artigos = carregar_artigos(str(DB_PATH))
    submissoes = carregar_submissoes(str(DB_PATH))
    ponto = carregar_ponto(str(DB_PATH))
    ano_atual = datetime.now().year
    meta_ano = carregar_meta_do_ano(str(DB_PATH), ano_atual)

    kpis = calcular_kpis(artigos, submissoes)
    alertas = gerar_alertas_latencia(kpis["pendentes"], LATENCIA_CRITICA_MESES)
    sugestao = sugerir_mudanca_metodologica(artigos, submissoes)
    projecao = projetar_ritmo(artigos, meta_ano, ano_atual)
    presenca = calcular_correlacao_presenca(ponto)
    diagnostico = gerar_diagnostico_intervencao(kpis, projecao, presenca, artigos, ano_atual)

    # ---------------- KPIs ----------------
    titulo_secao("Indicadores em tempo real", com_pulso=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        cartao_kpi("Total de artigos", str(kpis["total_artigos"]), chave="total")
    with c2:
        cartao_kpi("Em produção", str(kpis["em_producao"]), chave="producao")
    with c3:
        cartao_kpi(
            "Tempo mediano de escrita",
            f'{kpis["tempo_escrita_meses"]:.1f} meses' if kpis["tempo_escrita_meses"] is not None else "—",
            chave="escrita",
        )
    with c4:
        espera = kpis["espera_mediana_meses"]
        cartao_kpi(
            "Espera mediana na revisão",
            f"{espera:.1f} meses" if espera is not None else "—",
            sub=f"crítico acima de {LATENCIA_CRITICA_MESES:.0f} meses",
            critico=bool(espera and espera >= LATENCIA_CRITICA_MESES),
            chave="espera",
        )
    with c5:
        taxa = kpis["taxa_aceite"]
        cartao_kpi(
            "Taxa de aceite (ano)",
            f"{taxa*100:.0f}%" if taxa is not None else "sem dado",
            critico=(taxa == 0),
            chave="taxa",
        )

    # ---------------- Alertas críticos ----------------
    if alertas:
        titulo_secao(f"⚠ Alertas de latência acadêmica ({len(alertas)})")
        for a in alertas:
            st.markdown(f"""
                <div class="alerta-critico">
                  <b>{a['mensagem']}</b><br>
                  <small>parado há {a['meses']} meses · submetido em
                  {a['submetido_em'].strftime('%d/%m/%Y') if pd.notna(a['submetido_em']) else '—'}</small>
                </div>
            """, unsafe_allow_html=True)

    # ---------------- Sugestão metodológica ----------------
    if sugestao:
        titulo_secao("Sugestão da IA Central")
        linhas_txt = "".join(
            f"<li><b>{nome}</b> — {n} aceite(s) no histórico</li>"
            for nome, n in sugestao["linhas_mais_aceitas"]
        )
        st.markdown(f"""
            <div class="sugestao-card">
              A taxa de aceite deste ano está em <b>0%</b>
              ({sugestao['total_rejeicoes_no_periodo']} decisão(ões) no período, nenhuma aceita).
              Historicamente, as linhas de pesquisa com mais aceites foram:
              <ul>{linhas_txt}</ul>
              Vale revisar se os artigos em produção estão alinhados a essas linhas/metodologias
              antes da próxima rodada de submissão.
            </div>
        """, unsafe_allow_html=True)

    # ---------------- Projeção de ritmo ----------------
    titulo_secao("Projeção de ritmo (estimativa, não é meta)")
    p1, p2, p3 = st.columns(3)
    with p1:
        cartao_kpi("Publicados este ano", str(projecao["publicados_ate_agora"]), chave="pub_ano")
    with p2:
        cartao_kpi("Ritmo mensal atual", f'{projecao["ritmo_mensal"]:.1f}/mês', chave="ritmo")
    with p3:
        sub = (f'meta declarada: {projecao["meta_declarada"]}'
               if projecao["meta_declarada"] is not None else "sem meta declarada pela coordenação")
        cartao_kpi("Projeção para o fim do ano", str(projecao["projecao_fim_de_ano"]), sub=sub, chave="projecao")

    # ---------------- Diagnóstico + intervenção (visão coletiva) ----------------
    titulo_secao("Diagnóstico da IA Central — visão coletiva do laboratório")
    _renderizar_diagnostico_intervencao(diagnostico)

    # ---------------- Gráficos ----------------
    titulo_secao("Linhas de pesquisa — volume × impacto × tempo")
    st.markdown(
        '<div class="kpi-sub" style="margin:-.3rem 0 .5rem;">'
        'esferas maiores = mais artigos · pulsação = citações (impacto) · a câmera orbita sozinha</div>',
        unsafe_allow_html=True,
    )
    renderizar_grafico_3d_animado(montar_dispersao_3d(artigos), "grafico-dispersao-3d", "dispersao")

    titulo_secao("Funil de produção acadêmica")
    # Cada estágio é sempre um SUBCONJUNTO do anterior ("chegou pelo menos
    # até aqui"), não uma contagem de status simultânea e independente --
    # um artigo publicado ANO PASSADO não fica "parado" em nenhum balde
    # anterior, então comparar snapshots de status por status podia
    # colocar "Publicados" (acumulado de anos) maior que "Submetidos"
    # (só o que está em trâmite agora) e inverter o funil. Cumulativo
    # garante decrescente por construção, não por sorte dos dados.
    NAO_SUBMETIDO = {"planejado", "em_producao"}
    contagens = {
        "em_escrita": len(artigos),
        "submetidos": int((~artigos["status"].isin(NAO_SUBMETIDO)).sum()),
        "publicados": int((artigos["status"] == "publicado").sum()),
    }
    st.markdown(
        '<div class="kpi-sub" style="margin:-.3rem 0 .5rem;">'
        'partículas mais densas = estágio com mais artigos agora (o dado atualiza a cada recarga da tela)</div>',
        unsafe_allow_html=True,
    )
    renderizar_grafico_3d_animado(montar_funil_cilindrico(contagens), "grafico-funil-3d", "funil")

    # recarrega sozinho -- painel de TV, ninguém vai tocar
    st.components.v1.html(
        f"<script>setTimeout(function(){{ parent.window.location.reload(); }}, {REFRESH_MS});</script>",
        height=0,
    )


if __name__ == "__main__":
    main()
