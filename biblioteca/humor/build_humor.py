#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builder (estilo n8n): humor-data.json -> triangulacao-humor.html
Gera a ferramenta interativa de revisão sistemática: triangulação de variáveis
psicológicas de HUMOR por esporte/modalidade, ano e variável, com tabela de
extração sinalizada por ícones. Reprodutível: rode após extract_humor.py.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "humor-data.json")
OUT  = os.path.join(HERE, "triangulacao-humor.html")

# Metadados das variáveis (ordem, ícone, grupo). Mesmo conjunto do extractor.
VARS = [
 dict(key="ansiedade",           label="Ansiedade",                 icon="😰", grupo="nucleo"),
 dict(key="depressao",           label="Depressão",                 icon="😔", grupo="nucleo"),
 dict(key="humor_poms",          label="Estados de humor",          icon="🎭", grupo="nucleo"),
 dict(key="estresse",            label="Estresse",                  icon="😣", grupo="nucleo"),
 dict(key="afeto",               label="Afeto +/−",                 icon="⚖️", grupo="nucleo"),
 dict(key="bem_estar",           label="Bem-estar / QoL",           icon="🌱", grupo="nucleo"),
 dict(key="reg_emocional",       label="Regulação emocional",       icon="🧘", grupo="nucleo"),
 dict(key="saude_mental",        label="Saúde mental",              icon="🧠", grupo="nucleo"),
 dict(key="burnout",             label="Burnout",                   icon="🔥", grupo="nucleo"),
 dict(key="autoestima",          label="Autoestima",                icon="💗", grupo="correlato"),
 dict(key="imagem_corporal",     label="Imagem corporal",           icon="🪞", grupo="correlato"),
 dict(key="transtorno_alimentar",label="Transtorno alimentar",      icon="🍽️", grupo="correlato"),
 dict(key="perfeccionismo",      label="Perfeccionismo",            icon="🎯", grupo="correlato"),
]

def slim(recs):
    out=[]
    for r in recs:
        out.append(dict(
            doi=r.get("doi"), authors=r.get("authors"), year=r.get("year"),
            journal=(r.get("journal") or "").replace("&amp;","&"),
            title=(r.get("title") or "").replace("&amp;","&"),
            sport=r.get("sport"), modalities=r.get("modalities") or [],
            design=r.get("design"), n=r.get("n"), topic=r.get("topic"),
            finding=r.get("finding"), fulltext=r.get("fulltext","abstract"),
            vars=[dict(k=v["key"], nivel=v["nivel"]) for v in r.get("mood_vars",[])],
        ))
    return out

def main():
    recs = json.load(open(DATA, encoding="utf-8"))
    payload = dict(records=slim(recs), vars=VARS)
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(payload, ensure_ascii=False))
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"built {OUT} · {len(recs)} artigos · {len(html)} bytes")

TEMPLATE = r"""<title>Humor em Cena</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --bg:#F4F1F6; --surface:#FFFFFF; --surface-2:#EDE7F1; --surface-3:#F6F2F8;
  --ink:#221B29; --ink-soft:#5C5268; --ink-faint:#8A7E96;
  --line:#E2DAE8; --line-strong:#CFC3D8;
  --nucleo:#8A3F7A; --nucleo-soft:#F0DCEC;
  --correlato:#2F8A7B; --correlato-soft:#D6ECE6;
  --accent:#8A3F7A; --on-accent:#FFFFFF;
  --ramp0:#F6F2F8; --ramp-max:#8A3F7A;
  --shadow:0 1px 2px rgba(34,27,41,.06),0 8px 24px rgba(34,27,41,.06);
  --radius:14px;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#151019; --surface:#1E1824; --surface-2:#281F30; --surface-3:#221A29;
    --ink:#F2EAF4; --ink-soft:#B7A9C1; --ink-faint:#897C94;
    --line:#312639; --line-strong:#43364E;
    --nucleo:#CE84BD; --nucleo-soft:#3A2438;
    --correlato:#6FC1B1; --correlato-soft:#1E3A35;
    --accent:#CE84BD; --on-accent:#1A1020;
    --ramp0:#221A29; --ramp-max:#CE84BD;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --bg:#151019; --surface:#1E1824; --surface-2:#281F30; --surface-3:#221A29;
  --ink:#F2EAF4; --ink-soft:#B7A9C1; --ink-faint:#897C94;
  --line:#312639; --line-strong:#43364E;
  --nucleo:#CE84BD; --nucleo-soft:#3A2438;
  --correlato:#6FC1B1; --correlato-soft:#1E3A35;
  --accent:#CE84BD; --on-accent:#1A1020;
  --ramp0:#221A29; --ramp-max:#CE84BD;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1180px; margin:0 auto; padding:28px 22px 80px}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
.tnum{font-variant-numeric:tabular-nums}

/* Masthead */
header.mast{margin-bottom:22px}
.eyebrow{font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.16em;
  text-transform:uppercase; color:var(--ink-faint); display:flex; gap:10px; align-items:center}
.eyebrow .dot{width:6px;height:6px;border-radius:50%;background:var(--accent)}
h1{font-family:"Fraunces",Georgia,serif; font-weight:600; font-optical-sizing:auto;
  font-size:clamp(30px,5vw,46px); line-height:1.02; letter-spacing:-.01em;
  margin:.28em 0 .12em; text-wrap:balance}
h1 em{font-style:italic; color:var(--accent)}
.sub{color:var(--ink-soft); max-width:64ch; font-size:15.5px}

/* Toolbar */
.toolbar{position:sticky; top:0; z-index:20; margin:20px 0 18px; padding:12px;
  background:color-mix(in srgb,var(--surface) 88%,transparent); backdrop-filter:blur(8px);
  border:1px solid var(--line); border-radius:var(--radius); box-shadow:var(--shadow);
  display:flex; flex-wrap:wrap; gap:10px 14px; align-items:center}
.seg{display:inline-flex; background:var(--surface-2); border-radius:9px; padding:3px; gap:2px}
.seg button{font:inherit; font-size:13px; border:0; background:transparent; color:var(--ink-soft);
  padding:6px 11px; border-radius:7px; cursor:pointer; white-space:nowrap; transition:.15s}
.seg button[aria-pressed="true"]{background:var(--surface); color:var(--ink); box-shadow:0 1px 2px rgba(0,0,0,.08); font-weight:600}
.seg button:hover{color:var(--ink)}
.tlabel{font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-faint); margin-right:-4px}
.search{flex:1 1 190px; min-width:150px; display:flex; align-items:center; gap:8px;
  background:var(--surface-2); border:1px solid transparent; border-radius:9px; padding:7px 11px}
.search:focus-within{border-color:var(--line-strong); background:var(--surface)}
.search input{flex:1; border:0; background:transparent; color:var(--ink); font:inherit; font-size:14px; outline:none}
.search svg{flex:none; color:var(--ink-faint)}
.btn-clear{font:inherit; font-size:13px; border:1px solid var(--line-strong); background:transparent;
  color:var(--ink-soft); padding:7px 12px; border-radius:9px; cursor:pointer; transition:.15s}
.btn-clear:hover{color:var(--ink); border-color:var(--ink-soft)}
.btn-clear[hidden]{display:none}

/* active filter chips */
.actives{display:flex; flex-wrap:wrap; gap:7px; margin:-4px 0 18px; min-height:0}
.actives:empty{display:none}
.fchip{display:inline-flex; align-items:center; gap:6px; font-size:12.5px; padding:4px 8px 4px 10px;
  border-radius:20px; background:var(--nucleo-soft); color:var(--ink); border:1px solid transparent}
.fchip button{border:0;background:transparent;cursor:pointer;color:var(--ink-soft);font-size:14px;line-height:1;padding:0 1px}
.fchip button:hover{color:var(--ink)}

/* KPIs */
.kpis{display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:22px}
.kpi{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:14px 16px; box-shadow:var(--shadow)}
.kpi .v{font-family:"Fraunces",serif; font-weight:600; font-size:30px; line-height:1; letter-spacing:-.01em}
.kpi .l{font-size:12px; color:var(--ink-soft); margin-top:6px}
@media(max-width:640px){.kpis{grid-template-columns:repeat(2,1fr)}}

/* panels */
.grid{display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px}
.grid.tri{grid-template-columns:1fr}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
.panel{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:16px 18px; box-shadow:var(--shadow)}
.panel h2{margin:0 0 2px; font-family:"IBM Plex Sans",sans-serif; font-size:14px; font-weight:600; letter-spacing:.01em}
.panel .hint{font-size:11.5px; color:var(--ink-faint); margin:0 0 14px}

/* bar charts */
.bars{display:flex; flex-direction:column; gap:7px}
.bar-row{display:grid; grid-template-columns:150px 1fr 32px; align-items:center; gap:10px; cursor:pointer;
  padding:3px 4px; border-radius:8px; transition:background .12s}
.bar-row:hover{background:var(--surface-3)}
.bar-row .cap{font-size:12px; color:var(--ink-soft); display:flex; align-items:center; gap:6px; line-height:1.15}
.bar-row.on .cap{color:var(--ink); font-weight:600}
.bar-track{height:20px; background:var(--surface-2); border-radius:6px; overflow:hidden}
.bar-fill{display:block; height:100%; border-radius:6px; width:0; transition:width .5s cubic-bezier(.2,.7,.2,1)}
.bar-fill.nucleo{background:var(--nucleo)} .bar-fill.correlato{background:var(--correlato)}
.bar-fill.neutral{background:linear-gradient(90deg,var(--accent),color-mix(in srgb,var(--accent) 62%,var(--surface)))}
.bar-row .num{font-size:12.5px; text-align:right; color:var(--ink-soft)}
.bar-row.on{outline:1.5px solid var(--accent); outline-offset:1px}
.ic{font-size:14px; line-height:1; filter:saturate(1.05)}

/* year timeline */
.years{display:flex; align-items:flex-end; gap:3px; height:120px; padding-top:8px}
.ycol{flex:1; display:flex; flex-direction:column; align-items:center; gap:5px; cursor:pointer; min-width:0}
.ybar{width:100%; max-width:20px; background:var(--surface-2); border-radius:4px 4px 0 0; align-self:center; transition:height .5s cubic-bezier(.2,.7,.2,1),background .15s; min-height:2px}
.ycol:hover .ybar{background:var(--nucleo-soft)}
.ycol.on .ybar{background:var(--nucleo)}
.ylab{font-size:9px; color:var(--ink-faint); transform:rotate(-90deg); transform-origin:center; height:22px; white-space:nowrap}
.ycount{font-size:10px; color:var(--ink-soft); font-variant-numeric:tabular-nums; height:12px}

/* heatmap */
.hm-scroll{overflow-x:auto; margin:0 -4px; padding:0 4px}
.heat{display:grid; gap:3px; min-width:520px}
.heat .hcell{border-radius:6px; min-height:38px; display:flex; align-items:center; justify-content:center;
  font-size:13px; font-variant-numeric:tabular-nums; cursor:pointer; position:relative; transition:transform .1s, box-shadow .1s}
.heat .hcell.data:hover{transform:scale(1.06); box-shadow:0 0 0 2px var(--accent); z-index:2}
.heat .rowhead{display:flex; align-items:center; gap:7px; font-size:12px; color:var(--ink-soft); padding-right:8px; justify-content:flex-end; text-align:right; white-space:nowrap}
.heat .colhead{font-size:11px; color:var(--ink-soft); text-align:center; align-self:end; padding-bottom:4px; line-height:1.1; word-break:break-word}
.heat .corner{}
.hcell.on{box-shadow:0 0 0 2px var(--accent)}

/* extraction table */
.tablewrap{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); box-shadow:var(--shadow); overflow:hidden; margin-top:20px}
.tablewrap .thead{display:flex; align-items:baseline; justify-content:space-between; gap:12px; padding:16px 18px 8px; flex-wrap:wrap}
.tablewrap h2{margin:0; font-family:"Fraunces",serif; font-weight:600; font-size:20px}
.tcount{font-size:12.5px; color:var(--ink-soft)}
.sortbar{display:flex; gap:6px; padding:0 18px 12px; flex-wrap:wrap}
.sortbar button{font:inherit; font-size:12px; border:1px solid var(--line); background:var(--surface-2); color:var(--ink-soft); padding:5px 10px; border-radius:7px; cursor:pointer}
.sortbar button[aria-pressed="true"]{border-color:var(--accent); color:var(--ink); font-weight:600}
.t-scroll{overflow-x:auto}
table{border-collapse:collapse; width:100%; min-width:760px}
thead th{font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-faint); text-align:left; padding:10px 14px; border-bottom:1px solid var(--line); position:sticky; top:0; background:var(--surface); white-space:nowrap}
tbody td{padding:12px 14px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13.5px}
tbody tr:hover{background:var(--surface-3)}
tbody tr:last-child td{border-bottom:0}
.cell-study{max-width:340px}
.cell-study .ti{font-weight:600; line-height:1.25; color:var(--ink)}
.cell-study .au{color:var(--ink-soft); font-size:12px; margin-top:3px}
.cell-study .fi{color:var(--ink-soft); font-size:12px; margin-top:6px; line-height:1.4}
.cell-meta .j{font-style:italic; color:var(--ink); font-size:12.5px}
.cell-meta .m{color:var(--ink-soft); font-size:12px; margin-top:3px; display:flex; flex-wrap:wrap; gap:4px}
.pill{display:inline-block; font-size:11px; padding:2px 7px; border-radius:20px; background:var(--surface-2); color:var(--ink-soft); white-space:nowrap}
.yr{font-family:"IBM Plex Mono",monospace; font-weight:500; font-size:14px}
.doi{font-size:11.5px; color:var(--accent); text-decoration:none; word-break:break-all}
.doi:hover{text-decoration:underline}
.vchips{display:flex; flex-wrap:wrap; gap:5px; max-width:260px}
.vchip{display:inline-flex; align-items:center; gap:5px; font-size:11.5px; padding:3px 8px 3px 7px; border-radius:20px; border:1px solid; white-space:nowrap}
.vchip.nucleo{border-color:var(--nucleo); background:var(--nucleo-soft); color:var(--ink)}
.vchip.correlato{border-color:var(--correlato); background:var(--correlato-soft); color:var(--ink)}
.vchip.menc{border-style:dashed; background:transparent; opacity:.72}
.vchip .rng{width:5px;height:5px;border-radius:50%;flex:none}
.vchip.nucleo .rng{background:var(--nucleo)} .vchip.correlato .rng{background:var(--correlato)}
.vchip.menc .rng{background:transparent; border:1px solid currentColor}
.empty{padding:40px 18px; text-align:center; color:var(--ink-soft)}

/* legend */
.legend{display:flex; flex-wrap:wrap; gap:14px 20px; margin:6px 0 20px; font-size:12px; color:var(--ink-soft)}
.legend b{color:var(--ink); font-weight:600}
.lg{display:inline-flex; align-items:center; gap:7px}
.sw{width:12px;height:12px;border-radius:4px}
.sw.n{background:var(--nucleo)} .sw.c{background:var(--correlato)}
.sw.ring{background:transparent;border:1.5px dashed var(--ink-faint)}
.foot{margin-top:34px; padding-top:18px; border-top:1px solid var(--line); color:var(--ink-faint); font-size:12px; line-height:1.6}
.foot a{color:var(--accent); text-decoration:none}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
:focus-visible{outline:2px solid var(--accent); outline-offset:2px; border-radius:4px}
</style>

<div class="wrap">
  <header class="mast">
    <div class="eyebrow"><span class="dot"></span>Revisão sistemática · esportes estéticos femininos</div>
    <h1>Humor <em>em cena</em></h1>
    <p class="sub">Triangulação das variáveis psicológicas relacionadas ao <b>humor</b> (afetivas) estudadas nos esportes estéticos — cruzadas por modalidade, ano de publicação e construto. Clique em qualquer barra, célula ou chip para filtrar tudo em tempo real.</p>
  </header>

  <div class="toolbar" role="region" aria-label="Filtros">
    <span class="tlabel">Grupo</span>
    <div class="seg" id="seg-grupo">
      <button data-v="todos" aria-pressed="true">Todos</button>
      <button data-v="nucleo" aria-pressed="false">Núcleo afetivo</button>
      <button data-v="correlato" aria-pressed="false">Correlatos</button>
    </div>
    <span class="tlabel">Nível</span>
    <div class="seg" id="seg-nivel">
      <button data-v="todos" aria-pressed="true">Todos</button>
      <button data-v="medido" aria-pressed="false">Só medido</button>
    </div>
    <label class="search">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <input id="search" type="search" placeholder="Buscar autor, revista, achado…" aria-label="Buscar">
    </label>
    <button class="btn-clear" id="clear" hidden>Limpar filtros</button>
  </div>
  <div class="actives" id="actives" aria-live="polite"></div>

  <div class="kpis" id="kpis"></div>

  <div class="grid">
    <div class="panel">
      <h2>Por modalidade</h2>
      <p class="hint">Artigos que estudam ≥1 variável de humor, por esporte estético.</p>
      <div class="bars" id="chart-mod"></div>
    </div>
    <div class="panel">
      <h2>Por variável de humor</h2>
      <p class="hint">Quantos artigos abordam cada construto. <span style="color:var(--nucleo)">■</span> núcleo · <span style="color:var(--correlato)">■</span> correlato</p>
      <div class="bars" id="chart-var"></div>
    </div>
  </div>

  <div class="grid tri">
    <div class="panel">
      <h2>Por ano de publicação</h2>
      <p class="hint">Distribuição temporal do corpus filtrado.</p>
      <div class="years" id="chart-year"></div>
    </div>
  </div>

  <div class="grid tri">
    <div class="panel">
      <h2>Triangulação — variável × modalidade</h2>
      <p class="hint">Nº de artigos por cruzamento. Cor = intensidade. Clique numa célula para filtrar por essa variável e modalidade.</p>
      <div class="hm-scroll"><div class="heat" id="heat"></div></div>
    </div>
  </div>

  <div class="legend">
    <span class="lg"><span class="sw n"></span><b>Núcleo afetivo</b> — humor propriamente dito</span>
    <span class="lg"><span class="sw c"></span><b>Correlato</b> — autoavaliativo/comportamental ligado ao humor</span>
    <span class="lg"><span class="sw ring"></span>chip tracejado = <b>mencionado</b> (não medido diretamente)</span>
  </div>

  <div class="tablewrap">
    <div class="thead">
      <h2>Tabela de extração</h2>
      <span class="tcount" id="tcount"></span>
    </div>
    <div class="sortbar" id="sortbar">
      <span class="tlabel" style="align-self:center">Ordenar</span>
      <button data-s="year" aria-pressed="true">Ano ↓</button>
      <button data-s="modality" aria-pressed="false">Modalidade</button>
      <button data-s="nvars" aria-pressed="false">Nº variáveis ↓</button>
      <button data-s="journal" aria-pressed="false">Revista</button>
    </div>
    <div class="t-scroll">
      <table>
        <thead><tr>
          <th>Ano</th><th>Estudo</th><th>Revista / Modalidade</th><th>Desenho</th><th>Variáveis de humor</th><th>DOI</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="empty" id="empty" hidden>Nenhum artigo corresponde aos filtros. <a href="#" id="reset2" style="color:var(--accent)">Limpar</a></div>
  </div>

  <p class="foot">
    Gerado automaticamente a partir da Biblioteca De Lucca (<span id="ntot"></span> artigos com conteúdo psicológico triados; <span id="nmood"></span> com variável de humor). Pipeline reproduzível: <span class="mono">extract_humor.py → humor-data.json → build_humor.py</span>. Extração baseada em título, resumo e campos analíticos; o nível <b>“medido”</b> indica instrumento/variável analisada identificada, <b>“mencionado”</b> indica citação sem medição direta — confira o texto completo antes da síntese final. As modalidades de amostra mista estão sinalizadas no campo de esporte.
  </p>
</div>

<script>
const PAYLOAD = /*__DATA__*/;
const RECORDS = PAYLOAD.records, VMETA = PAYLOAD.vars;
const VMAP = {}; VMETA.forEach(v=>VMAP[v.key]=v);
const MOD_ORDER = ["Dança","Ginástica rítmica","Ginástica artística","Ginástica aeróbica","Ginástica acrobática","Patinação artística","Nado artístico","Outro"];
const MOD_SHORT = {"Dança":"Dança","Ginástica rítmica":"G. rítmica","Ginástica artística":"G. artística","Ginástica aeróbica":"G. aeróbica","Ginástica acrobática":"G. acrobática","Patinação artística":"Patinação","Nado artístico":"Nado art.","Outro":"Outro"};

const state = { grupo:"todos", nivel:"todos", search:"", mods:new Set(), years:new Set(), vars:new Set(), sort:"year" };

// --- helpers ---------------------------------------------------------------
function recVars(r){ // variáveis efetivas após filtros de grupo e nível
  return r.vars.filter(v=>{
    const m=VMAP[v.k]; if(!m) return false;
    if(state.grupo!=="todos" && m.grupo!==state.grupo) return false;
    if(state.nivel==="medido" && v.nivel!=="medido") return false;
    return true;
  });
}
function matchesSearch(r){
  if(!state.search) return true;
  const q=state.search.toLowerCase();
  return ((r.authors||"")+" "+(r.journal||"")+" "+(r.title||"")+" "+(r.finding||"")+" "+(r.sport||"")).toLowerCase().includes(q);
}
// passa nos filtros, opcionalmente ignorando uma dimensão ('mod'|'year'|'var')
function passes(r, except){
  if(recVars(r).length===0) return false;
  if(!matchesSearch(r)) return false;
  if(except!=="mod" && state.mods.size && !r.modalities.some(m=>state.mods.has(m))) return false;
  if(except!=="year" && state.years.size && !state.years.has(r.year)) return false;
  if(except!=="var" && state.vars.size && !recVars(r).some(v=>state.vars.has(v.k))) return false;
  return true;
}
function fullSet(){ return RECORDS.filter(r=>passes(r,null)); }

// --- charts ----------------------------------------------------------------
function renderMod(){
  const set = RECORDS.filter(r=>passes(r,"mod"));
  const counts={}; MOD_ORDER.forEach(m=>counts[m]=0);
  set.forEach(r=>r.modalities.forEach(m=>{ if(m in counts) counts[m]++; }));
  const max=Math.max(1,...Object.values(counts));
  const el=document.getElementById("chart-mod"); el.innerHTML="";
  MOD_ORDER.filter(m=>counts[m]>0).sort((a,b)=>counts[b]-counts[a]).forEach(m=>{
    const on=state.mods.has(m);
    const row=document.createElement("div"); row.className="bar-row"+(on?" on":"");
    row.innerHTML=`<span class="cap">${MOD_SHORT[m]||m}</span>
      <span class="bar-track"><span class="bar-fill neutral" style="width:${counts[m]/max*100}%"></span></span>
      <span class="num tnum">${counts[m]}</span>`;
    row.onclick=()=>toggle(state.mods,m); el.appendChild(row);
  });
}
function renderVar(){
  const set = RECORDS.filter(r=>passes(r,"var"));
  const counts={}; VMETA.forEach(v=>counts[v.key]=0);
  set.forEach(r=>{ const seen=new Set(recVars(r).map(v=>v.k)); seen.forEach(k=>counts[k]++); });
  const max=Math.max(1,...Object.values(counts));
  const el=document.getElementById("chart-var"); el.innerHTML="";
  VMETA.filter(v=>{ if(state.grupo!=="todos"&&v.grupo!==state.grupo) return false; return counts[v.key]>0; })
    .sort((a,b)=>counts[b.key]-counts[a.key]).forEach(v=>{
    const on=state.vars.has(v.key);
    const row=document.createElement("div"); row.className="bar-row"+(on?" on":"");
    row.innerHTML=`<span class="cap"><span class="ic">${v.icon}</span>${v.label}</span>
      <span class="bar-track"><span class="bar-fill ${v.grupo}" style="width:${counts[v.key]/max*100}%"></span></span>
      <span class="num tnum">${counts[v.key]}</span>`;
    row.onclick=()=>toggle(state.vars,v.key); el.appendChild(row);
  });
}
function renderYear(){
  const set = RECORDS.filter(r=>passes(r,"year"));
  const years=[...new Set(RECORDS.map(r=>r.year))].filter(Boolean).sort((a,b)=>a-b);
  const counts={}; years.forEach(y=>counts[y]=0);
  set.forEach(r=>{ if(r.year in counts) counts[r.year]++; });
  const max=Math.max(1,...Object.values(counts));
  const el=document.getElementById("chart-year"); el.innerHTML="";
  years.forEach(y=>{
    const on=state.years.has(y);
    const col=document.createElement("div"); col.className="ycol"+(on?" on":"");
    col.innerHTML=`<span class="ycount tnum">${counts[y]||""}</span>
      <span class="ybar" style="height:${8+counts[y]/max*90}px"></span>
      <span class="ylab">${y}</span>`;
    col.onclick=()=>toggle(state.years,y); el.appendChild(col);
  });
}
function rampColor(t){ // 0..1 -> mistura ramp0 -> ramp-max
  return t<=0 ? "var(--surface-2)" : `color-mix(in srgb, var(--ramp-max) ${Math.round(18+t*82)}%, var(--ramp0))`;
}
function renderHeat(){
  // aplica busca+grupo+nível+ano (não mod/var) para mostrar todo o cruzamento selecionável
  const set=RECORDS.filter(r=>{
    if(recVars(r).length===0) return false;
    if(!matchesSearch(r)) return false;
    if(state.years.size && !state.years.has(r.year)) return false;
    return true;
  });
  const vlist=VMETA.filter(v=>state.grupo==="todos"||v.grupo===state.grupo);
  const mlist=MOD_ORDER.filter(m=>set.some(r=>r.modalities.includes(m)));
  const grid={}; let gmax=1;
  vlist.forEach(v=>{ grid[v.key]={}; mlist.forEach(m=>grid[v.key][m]=0); });
  set.forEach(r=>{ const ks=new Set(recVars(r).map(x=>x.k));
    r.modalities.forEach(m=>{ if(!(m in (grid[vlist[0]?.key]||{}))) return; ks.forEach(k=>{ if(grid[k]) { grid[k][m]++; if(grid[k][m]>gmax)gmax=grid[k][m]; } }); }); });
  const el=document.getElementById("heat");
  el.style.gridTemplateColumns=`minmax(130px,auto) repeat(${mlist.length},1fr)`; el.innerHTML="";
  el.insertAdjacentHTML("beforeend",`<div class="corner"></div>`);
  mlist.forEach(m=>el.insertAdjacentHTML("beforeend",`<div class="colhead">${MOD_SHORT[m]||m}</div>`));
  vlist.forEach(v=>{
    el.insertAdjacentHTML("beforeend",`<div class="rowhead"><span class="ic">${v.icon}</span>${v.label}</div>`);
    mlist.forEach(m=>{
      const c=grid[v.key][m], t=c/gmax;
      const on=state.vars.has(v.key)&&state.mods.has(m);
      const cell=document.createElement("div");
      cell.className="hcell"+(c>0?" data":"")+(on?" on":"");
      cell.style.background=c>0?rampColor(t):"var(--surface-3)";
      cell.style.color = t>0.55 ? "var(--on-accent)" : "var(--ink-soft)";
      cell.textContent=c>0?c:"";
      if(c>0){ cell.title=`${v.label} · ${m}: ${c} artigo(s)`;
        cell.onclick=()=>{ state.vars=new Set([v.key]); state.mods=new Set([m]); render(); }; }
      el.appendChild(cell);
    });
  });
}
function renderKpis(){
  const set=fullSet();
  const nuc=new Set(), mods=new Set(); let ymin=9999,ymax=0;
  set.forEach(r=>{ r.modalities.forEach(m=>mods.add(m)); if(r.year){ymin=Math.min(ymin,r.year);ymax=Math.max(ymax,r.year);}
    recVars(r).forEach(v=>{ if(VMAP[v.k].grupo==="nucleo") nuc.add(v.k); }); });
  const varset=new Set(); set.forEach(r=>recVars(r).forEach(v=>varset.add(v.k)));
  const kpis=[["Artigos",set.length],["Variáveis de humor",varset.size],["Modalidades",mods.size],["Período", set.length?`${ymin}–${ymax}`:"—"]];
  document.getElementById("kpis").innerHTML=kpis.map(k=>`<div class="kpi"><div class="v tnum">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("");
}

// --- table -----------------------------------------------------------------
function renderTable(){
  const set=fullSet().slice();
  const s=state.sort;
  set.sort((a,b)=>{
    if(s==="year") return (b.year||0)-(a.year||0) || (a.journal||"").localeCompare(b.journal||"");
    if(s==="nvars") return recVars(b).length-recVars(a).length || (b.year||0)-(a.year||0);
    if(s==="journal") return (a.journal||"").localeCompare(b.journal||"");
    if(s==="modality") return (a.modalities[0]||"").localeCompare(b.modalities[0]||"") || (b.year||0)-(a.year||0);
    return 0;
  });
  const tb=document.getElementById("tbody"); tb.innerHTML="";
  document.getElementById("empty").hidden=set.length>0;
  set.forEach(r=>{
    const vs=recVars(r).map(v=>{ const m=VMAP[v.k]; const menc=v.nivel!=="medido";
      return `<span class="vchip ${m.grupo}${menc?" menc":""}" title="${m.label} — ${v.nivel}"><span class="rng"></span>${m.icon} ${m.label}</span>`;
    }).join("");
    const mods=r.modalities.map(m=>`<span class="pill">${MOD_SHORT[m]||m}</span>`).join(" ");
    const tr=document.createElement("tr");
    tr.innerHTML=`
      <td><span class="yr tnum">${r.year||"—"}</span></td>
      <td class="cell-study"><div class="ti">${r.title||""}</div><div class="au">${r.authors||""}</div>${r.finding?`<div class="fi">${r.finding}</div>`:""}</td>
      <td class="cell-meta"><div class="j">${r.journal||""}</div><div class="m">${mods}</div><div class="au" style="margin-top:4px">${r.sport||""}</div></td>
      <td><span class="pill">${r.design||"—"}</span>${r.n?`<div class="au" style="margin-top:5px">n=${r.n}</div>`:""}</td>
      <td><div class="vchips">${vs}</div></td>
      <td>${r.doi?`<a class="doi" href="https://doi.org/${r.doi}" target="_blank" rel="noopener">${r.doi}</a>`:"—"}</td>`;
    tb.appendChild(tr);
  });
  document.getElementById("tcount").textContent=`${set.length} artigo(s) · ${new Set(set.flatMap(r=>recVars(r).map(v=>v.k))).size} variáveis`;
}

// --- active filter chips ---------------------------------------------------
function renderActives(){
  const el=document.getElementById("actives"); el.innerHTML="";
  const add=(label,onx)=>{ const c=document.createElement("span"); c.className="fchip";
    c.innerHTML=`${label} <button aria-label="remover">×</button>`; c.querySelector("button").onclick=onx; el.appendChild(c); };
  state.mods.forEach(m=>add(`◆ ${MOD_SHORT[m]||m}`,()=>{state.mods.delete(m);render();}));
  state.vars.forEach(k=>add(`${VMAP[k].icon} ${VMAP[k].label}`,()=>{state.vars.delete(k);render();}));
  [...state.years].sort().forEach(y=>add(`${y}`,()=>{state.years.delete(y);render();}));
  if(state.grupo!=="todos") add(state.grupo==="nucleo"?"Núcleo afetivo":"Correlatos",()=>{setSeg("seg-grupo","todos");});
  if(state.nivel==="medido") add("Só medido",()=>{setSeg("seg-nivel","todos");});
  if(state.search) add(`“${state.search}”`,()=>{state.search="";document.getElementById("search").value="";render();});
  const any=state.mods.size||state.vars.size||state.years.size||state.grupo!=="todos"||state.nivel!=="medido"&&false||state.nivel==="medido"||state.search;
  document.getElementById("clear").hidden=!any;
}

// --- glue ------------------------------------------------------------------
function toggle(set,val){ set.has(val)?set.delete(val):set.add(val); render(); }
function setSeg(id,val){ const seg=document.getElementById(id);
  seg.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed", b.dataset.v===val));
  if(id==="seg-grupo") state.grupo=val; else state.nivel=val; render(); }
function render(){ renderKpis(); renderMod(); renderVar(); renderYear(); renderHeat(); renderTable(); renderActives(); }

document.getElementById("seg-grupo").addEventListener("click",e=>{const b=e.target.closest("button");if(b)setSeg("seg-grupo",b.dataset.v);});
document.getElementById("seg-nivel").addEventListener("click",e=>{const b=e.target.closest("button");if(b)setSeg("seg-nivel",b.dataset.v);});
document.getElementById("sortbar").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  state.sort=b.dataset.s; document.querySelectorAll("#sortbar button").forEach(x=>x.setAttribute("aria-pressed",x===b)); renderTable();});
let st; document.getElementById("search").addEventListener("input",e=>{clearTimeout(st);st=setTimeout(()=>{state.search=e.target.value.trim();render();},160);});
function clearAll(){ state.mods.clear();state.vars.clear();state.years.clear(); state.search="";document.getElementById("search").value="";
  setSeg("seg-grupo","todos"); document.getElementById("seg-nivel").querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.v==="todos")); state.nivel="todos"; render(); }
document.getElementById("clear").onclick=clearAll;
document.getElementById("reset2").onclick=e=>{e.preventDefault();clearAll();};

document.getElementById("ntot").textContent="90";
document.getElementById("nmood").textContent=RECORDS.length;
render();
</script>
"""

if __name__=="__main__":
    main()
