#!/usr/bin/env python3
"""Builder da Biblioteca Virtual — De Lucca.
Monta biblioteca/biblioteca.html a partir de:
  - biblioteca/_fontface.css        (fontes woff2 base64)
  - biblioteca/biblioteca.json      (acervo; enriquecido com design/subvar/n quando disponível)
  - biblioteca/synth.json           (4 cartões de síntese)
  - biblioteca/metodologia.json     (PERMANOVA, desenhos, PRISMA — para a base de revisão)
Executar:  python3 biblioteca/build.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

def load(name, default):
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f) if name.endswith(".json") else f.read()

fontface = load("_fontface.css", "")
# prefer enriched file if the agent produced one; else the canonical json
enriched = os.path.join(ROOT, "biblioteca-enriched.json")
data = json.load(open(enriched, encoding="utf-8")) if os.path.exists(enriched) else load("biblioteca.json", [])
synth = load("synth.json", [])
meto = load("metodologia.json", {})

# --- normalize: ensure every entry has design/subvar even if enrichment absent ---
for d in data:
    d.setdefault("design", "—")
    d.setdefault("design_conf", "média")
    d.setdefault("subvar", d.get("topic", "—"))
    d.setdefault("n", None)

# metodologia defaults (graceful if agent file missing)
meto.setdefault("permanova", {"count_found": 0, "in_library": 0, "studies": [],
    "verdict": "Não localizamos estudos de PERMANOVA em esportes estéticos femininos; o método é raro nessa área.",
    "dominant_methods": ["ANOVA de medidas repetidas / modelos mistos", "SPM1d (Statistical Parametric Mapping)", "PCA / NMF (sinergias)", "Correlação / regressão", "SEM / mediação (psicologia)"]})
meto.setdefault("gaps", [])
meto.setdefault("prisma", {"databases": ["PubMed", "Scopus", "Web of Science", "SPORTDiscus"],
    "pico": {"P": "", "I": "", "C": "", "O": "", "S": ""},
    "risk_of_bias": {}, "synthesis": ""})

CSS = r"""
:root{
  --ink-0:#0a0b10;--ink-1:#0d0f16;--ink-2:#141824;--ink-3:#1b2130;--line:#252c3b;
  --gold:#e3a942;--gold-b:#efc471;--hi:#f4f2ea;--mid:#a7b0c0;--low:#6b7486;
  --t-neuro:#4f93d6;--t-psico:#33b98a;--t-perf:#e8c24a;--t-fadiga:#e2853a;
  --sans:'Barlow',system-ui,sans-serif;--cond:'Oswald',var(--sans);--disp:'Anton',var(--cond);--serif:'Playfair Display',Georgia,serif;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 700px at 50% -10%,#12151f,transparent 60%),var(--ink-0);
  color:var(--hi);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:40px 20px 90px}
.eyebrow{font-family:var(--cond);font-weight:600;font-size:13px;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);margin:0 0 10px;display:flex;align-items:center;gap:14px}
.eyebrow::after{content:"";height:1px;flex:1;background:linear-gradient(90deg,var(--gold),transparent)}
h1{font-family:var(--disp);font-weight:400;text-transform:uppercase;letter-spacing:.01em;font-size:clamp(32px,6vw,60px);line-height:.95;margin:0 0 10px;text-shadow:0 2px 0 #0006}
.lede{font-family:var(--serif);font-style:italic;color:var(--mid);font-size:clamp(15px,2vw,19px);max-width:70ch;margin:0}
h2.sec{font-family:var(--disp);font-weight:400;text-transform:uppercase;letter-spacing:.02em;font-size:clamp(20px,3vw,30px);margin:0 0 4px}
.sub{font-family:var(--cond);font-weight:600;font-size:12px;letter-spacing:.28em;text-transform:uppercase;color:var(--gold);margin:0 0 16px}
section.block{margin-top:52px;scroll-margin-top:78px}
/* ---- nav ---- */
nav.jump{position:sticky;top:0;z-index:20;display:flex;flex-wrap:wrap;gap:8px;padding:10px 0;margin:22px 0 0;
  background:linear-gradient(180deg,var(--ink-0),var(--ink-0) 60%,transparent);backdrop-filter:blur(4px)}
nav.jump a{font-family:var(--cond);font-weight:600;font-size:12px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mid);text-decoration:none;padding:7px 13px;border:1px solid var(--line);border-radius:99px;transition:.2s}
nav.jump a:hover{color:var(--hi);border-color:var(--gold);background:#e3a94214}
/* ---- stats ---- */
.stats{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0 8px}
.stat{background:var(--ink-2);border:1px solid #ffffff10;border-radius:10px;padding:12px 18px;box-shadow:0 12px 26px -18px #000;min-width:96px}
.stat b{font-family:var(--disp);font-size:26px;color:var(--gold);display:block;line-height:1.05}
.stat span{font-family:var(--cond);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--mid)}
/* ---- cards ---- */
.card{background:linear-gradient(180deg,var(--ink-2),var(--ink-1));border:1px solid #ffffff0e;border-radius:16px;padding:22px;box-shadow:0 26px 60px -40px #000}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
@media(max-width:820px){.grid2,.grid3{grid-template-columns:1fr}}
/* ---- segmented bars (real-time) ---- */
.segwrap{display:flex;flex-direction:column;gap:14px}
.segrow{display:grid;grid-template-columns:150px 1fr 46px;align-items:center;gap:12px}
.segrow .lab{font-family:var(--cond);font-weight:600;font-size:13px;letter-spacing:.05em;color:var(--hi);text-align:right}
.segrow .val{font-family:var(--disp);font-size:16px;color:var(--mid);text-align:left}
.track{position:relative;height:26px;border-radius:7px;background:#ffffff08;overflow:hidden;display:flex}
.seg{height:100%;width:0;transition:width .9s cubic-bezier(.2,.8,.2,1);cursor:pointer;position:relative;opacity:.92}
.seg:hover{filter:brightness(1.25);opacity:1}
.seg::after{content:attr(data-lab);position:absolute;left:50%;top:-30px;transform:translateX(-50%);white-space:nowrap;
  font-family:var(--sans);font-size:11px;background:#000d;color:#fff;padding:3px 8px;border-radius:6px;opacity:0;pointer-events:none;transition:.15s;z-index:5}
.seg:hover::after{opacity:1;top:-26px}
/* ---- sport bars ---- */
.hbar{display:grid;grid-template-columns:180px 1fr 40px;align-items:center;gap:10px;margin:7px 0}
.hbar .nm{font-size:12.5px;color:var(--mid);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hbar .bar{height:16px;border-radius:5px;width:0;transition:width 1s cubic-bezier(.2,.8,.2,1)}
.hbar .c{font-family:var(--disp);font-size:14px;color:var(--hi)}
/* ---- design chart ---- */
.dchart{display:flex;flex-direction:column;gap:10px}
.drow{display:grid;grid-template-columns:190px 1fr 60px;align-items:center;gap:10px}
.drow .dn{font-family:var(--cond);font-weight:600;font-size:12.5px;letter-spacing:.04em;color:var(--hi);text-align:right}
.drow .dt{height:22px;border-radius:6px;position:relative;background:#ffffff08;overflow:hidden}
.drow .df{height:100%;width:0;border-radius:6px;transition:width 1s cubic-bezier(.2,.8,.2,1)}
.drow .dv{font-family:var(--disp);font-size:15px;color:var(--mid)}
/* ---- PERMANOVA callout ---- */
.perm{display:flex;gap:22px;align-items:center;flex-wrap:wrap;border:1px solid #e2853a44;background:radial-gradient(600px 200px at 0% 0%,#e2853a1a,transparent)}
.perm .big{font-family:var(--disp);font-size:clamp(52px,10vw,88px);line-height:.9;color:var(--t-fadiga);text-shadow:0 3px 0 #0006}
.perm .txt{flex:1;min-width:260px}
.perm .txt h3{font-family:var(--cond);font-weight:700;letter-spacing:.03em;margin:0 0 6px;font-size:19px}
.perm .txt p{margin:0;color:var(--mid);font-size:14.5px}
.chips2{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.chips2 span{font-family:var(--cond);font-size:11px;letter-spacing:.06em;color:var(--hi);background:#ffffff10;border:1px solid var(--line);border-radius:99px;padding:5px 11px}
/* ---- PRISMA ---- */
.prisma{display:flex;flex-direction:column;gap:12px;counter-reset:pr}
.pbox{display:grid;grid-template-columns:210px 1fr;gap:14px;align-items:center}
.pbox .stage{font-family:var(--cond);font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:12px;color:var(--gold);
  border:1px solid #e3a94240;border-radius:10px;padding:12px;text-align:center;background:#e3a9420d}
.pbox .body{background:var(--ink-3);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font-size:14px;color:var(--mid)}
.pbox .body b{color:var(--hi);font-family:var(--disp);font-weight:400}
.pconn{height:14px;width:2px;background:linear-gradient(#e3a94288,transparent);margin:0 auto}
/* ---- matrix heatmap ---- */
.matx{overflow-x:auto}
table.mx{border-collapse:collapse;width:100%;min-width:640px}
table.mx th,table.mx td{border:1px solid var(--line);padding:0;text-align:center}
table.mx th{font-family:var(--cond);font-weight:600;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--mid);padding:8px 6px}
table.mx td{position:relative;height:44px;cursor:pointer}
table.mx td .cell{position:absolute;inset:3px;border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-family:var(--disp);font-size:15px;color:#0a0b10;transition:.2s;transform:scale(.6);opacity:0}
table.mx td:hover .cell{filter:brightness(1.12)}
table.mx th.rh{text-align:right;padding-right:12px;color:var(--hi);white-space:nowrap}
/* ---- pico ---- */
.pico{display:grid;grid-template-columns:56px 1fr;gap:0}
.pico .k{font-family:var(--disp);font-size:20px;color:var(--gold);border-bottom:1px solid var(--line);padding:10px 0}
.pico .v{border-bottom:1px solid var(--line);padding:11px 4px;color:var(--mid);font-size:14px}
.pico .k:last-of-type,.pico .v:last-of-type{border-bottom:0}
.rob{display:flex;flex-direction:column;gap:8px}
.rob div{display:flex;justify-content:space-between;gap:12px;border-bottom:1px dashed var(--line);padding:7px 0;font-size:13.5px}
.rob div span:first-child{color:var(--mid)}.rob div span:last-child{color:var(--hi);font-family:var(--cond);font-weight:600}
/* ---- synth ---- */
.synth{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
@media(max-width:820px){.synth{grid-template-columns:1fr}}
.scard{background:var(--ink-2);border:1px solid #ffffff0e;border-left:3px solid var(--c);border-radius:12px;padding:18px 20px}
.scard h3{font-family:var(--cond);font-weight:700;letter-spacing:.02em;margin:0 0 8px;color:var(--c);font-size:17px}
.scard p{margin:0;color:var(--mid);font-size:14px}
.scard b{color:var(--hi)}
/* ---- controls + table ---- */
.controls{margin-top:16px;display:flex;flex-direction:column;gap:12px}
.searchrow{display:flex;flex-wrap:wrap;gap:10px}
.search{flex:1;min-width:220px;display:flex;align-items:center;gap:8px;background:var(--ink-2);border:1px solid var(--line);border-radius:10px;padding:0 12px}
.search input{flex:1;background:none;border:0;color:var(--hi);font-family:var(--sans);font-size:14px;padding:11px 0;outline:none}
select{background:var(--ink-2);border:1px solid var(--line);color:var(--hi);border-radius:10px;padding:11px 12px;font-family:var(--sans);font-size:13.5px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-family:var(--cond);font-weight:600;font-size:12px;letter-spacing:.06em;color:var(--mid);background:var(--ink-2);border:1px solid var(--line);
  border-radius:99px;padding:7px 13px;cursor:pointer;display:flex;align-items:center;gap:7px;transition:.18s}
.chip i{width:9px;height:9px;border-radius:99px;background:var(--c,var(--gold))}
.chip[aria-pressed=true]{color:var(--hi);border-color:var(--c,var(--gold));background:#ffffff0d}
.chip.all[aria-pressed=true]{border-color:var(--gold);color:var(--gold)}
.tablewrap{margin-top:14px;border:1px solid var(--line);border-radius:14px;overflow:auto}
table.lib{border-collapse:collapse;width:100%;min-width:900px}
table.lib th,table.lib td{text-align:left;padding:11px 12px;border-bottom:1px solid #ffffff0a;font-size:13px;vertical-align:top}
table.lib th{position:sticky;top:0;background:var(--ink-3);font-family:var(--cond);font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-size:11px;color:var(--mid);cursor:pointer;z-index:2}
table.lib tbody tr:hover{background:#ffffff05}
.t-auth{color:var(--hi);max-width:180px}
.t-year{font-family:var(--disp);color:var(--gold)}
.t-title{color:var(--hi);font-weight:600;display:block;margin-bottom:3px}
.t-find{color:var(--mid);font-size:12.5px;display:block}
.badge{font-family:var(--cond);font-weight:600;font-size:11px;letter-spacing:.04em;color:#0a0b10;background:var(--c,#888);border-radius:6px;padding:3px 8px;white-space:nowrap}
.dpill{font-family:var(--cond);font-size:11px;letter-spacing:.03em;color:var(--hi);border:1px solid var(--line);border-radius:6px;padding:3px 7px;white-space:nowrap}
.subv{display:block;color:var(--low);font-size:11px;margin-top:4px}
.sport{color:var(--mid);font-size:12.5px;max-width:150px}
a.doi{font-family:var(--cond);font-size:11.5px;color:var(--gold);text-decoration:none;border:1px solid #e3a94240;border-radius:6px;padding:4px 8px;white-space:nowrap;transition:.18s;display:inline-block}
a.doi:hover{background:var(--gold);color:#0a0b10}
.empty{padding:26px;text-align:center;color:var(--low)}
.note{color:var(--low);font-size:12.5px;margin-top:10px}
footer{margin-top:64px;padding-top:22px;border-top:1px solid var(--line);display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap}
.name{font-family:var(--cond);font-weight:700;letter-spacing:.02em;margin:0;color:var(--hi)}
.role{margin:2px 0 0;color:var(--low);font-size:12.5px}
.wm{font-family:var(--disp);font-size:clamp(28px,7vw,64px);color:#ffffff08;letter-spacing:.04em;line-height:1}
.hint{color:var(--low);font-size:12px;margin:8px 0 0;font-style:italic}
"""

BODY = r"""
<div class="wrap">
  <p class="eyebrow">Base Científica · Biblioteca Virtual</p>
  <h1>Esportes estéticos<br>femininos</h1>
  <p class="lede">Acervo internacional com DOI verificado — catalogado e segmentado por <b>esporte</b>, <b>variável</b> e <b>subvariável</b>, com desenho de estudo e uma base metodológica para revisão sistemática.</p>

  <div class="stats" id="stats"></div>

  <nav class="jump">
    <a href="#setores">Setores</a>
    <a href="#tipos">Tipos de estudo</a>
    <a href="#permanova">PERMANOVA</a>
    <a href="#revisao">Base p/ revisão</a>
    <a href="#sintese">Síntese</a>
    <a href="#acervo">Acervo</a>
  </nav>

  <!-- SETORES: segmentação por variável × subvariável × esporte -->
  <section class="block" id="setores">
    <h2 class="sec">Setores da biblioteca</h2>
    <p class="sub">Segmentação · variável → subvariável → esporte</p>
    <div class="grid2">
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Por variável e subvariável</h3>
        <p class="hint">Cada barra é uma variável; os blocos internos são subvariáveis. Passe o mouse para ver — clique para filtrar o acervo.</p>
        <div class="segwrap" id="segvar"></div>
      </div>
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Por esporte</h3>
        <p class="hint">Volume de evidência por modalidade estética. Clique para filtrar.</p>
        <div id="sportbars"></div>
      </div>
    </div>
  </section>

  <!-- TIPOS DE ESTUDO -->
  <section class="block" id="tipos">
    <h2 class="sec">Tipos de estudo</h2>
    <p class="sub">Transversal · longitudinal · experimental · revisões</p>
    <div class="grid2">
      <div class="card"><div class="dchart" id="dchart"></div>
        <p class="hint" id="dhint"></p></div>
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 8px;font-size:16px">O que isso diz para a revisão</h3>
        <div class="rob" id="designnotes"></div>
      </div>
    </div>
  </section>

  <!-- PERMANOVA -->
  <section class="block" id="permanova">
    <h2 class="sec">Quantos estudos de PERMANOVA?</h2>
    <p class="sub">Resposta honesta com base no acervo e na literatura</p>
    <div class="card perm">
      <div class="big" id="permbig">0</div>
      <div class="txt">
        <h3 id="permhead"></h3>
        <p id="permverdict"></p>
        <div class="chips2" id="permmethods"></div>
      </div>
    </div>
  </section>

  <!-- BASE PARA REVISÃO SISTEMÁTICA -->
  <section class="block" id="revisao">
    <h2 class="sec">Base para revisão sistemática</h2>
    <p class="sub">PRISMA · PICOS · risco de viés · matriz de evidência</p>
    <div class="grid2">
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 12px;font-size:16px">Fluxo PRISMA (com este acervo)</h3>
        <div class="prisma" id="prisma"></div>
      </div>
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 10px;font-size:16px">Matriz de evidência · desenho × variável</h3>
        <p class="hint">Densidade de estudos por célula. Clique para filtrar o acervo.</p>
        <div class="matx"><table class="mx" id="matrix"></table></div>
      </div>
    </div>
    <div class="grid2" style="margin-top:18px">
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 10px;font-size:16px">Pergunta estruturada (PICOS)</h3>
        <div class="pico" id="pico"></div>
      </div>
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 10px;font-size:16px">Bases & risco de viés</h3>
        <div class="chips2" id="dbs" style="margin:0 0 14px"></div>
        <div class="rob" id="rob"></div>
        <p class="hint" id="synthesis"></p>
      </div>
    </div>
  </section>

  <!-- SÍNTESE -->
  <section class="block" id="sintese">
    <h2 class="sec">Síntese dos achados</h2>
    <p class="sub">Neurofisiologia · psicologia · performance · fadiga</p>
    <div class="synth" id="synth"></div>
  </section>

  <!-- ACERVO -->
  <section class="block" id="acervo">
    <h2 class="sec">Acervo completo</h2>
    <p class="sub">Filtrável · DOI verificado</p>
    <div class="controls">
      <div class="searchrow">
        <label class="search">🔎<input id="q" type="search" placeholder="Buscar por autor, título, periódico, achado, subvariável…"></label>
        <select id="sport"><option value="">Todos os esportes</option></select>
        <select id="design"><option value="">Todos os desenhos</option></select>
        <select id="sort">
          <option value="year">Ordenar: ano ↓</option>
          <option value="cit">Ordenar: citações ↓</option>
          <option value="auth">Ordenar: autor A–Z</option>
        </select>
      </div>
      <div class="chips" id="chips"></div>
    </div>
    <div class="tablewrap">
      <table class="lib">
        <thead><tr>
          <th data-k="authors">Autores</th>
          <th data-k="year">Ano</th>
          <th data-k="title">Título · achado</th>
          <th data-k="journal">Periódico</th>
          <th data-k="topic">Variável · subvariável</th>
          <th data-k="design">Desenho</th>
          <th data-k="sport">Esporte</th>
          <th data-k="citations">Cit.</th>
          <th data-k="doi">DOI</th>
        </tr></thead>
        <tbody id="rows"></tbody>
      </table>
      <div class="empty" id="empty" hidden>Nenhum artigo corresponde ao filtro.</div>
    </div>
    <p class="note" id="note"></p>
  </section>

  <footer>
    <div><p class="name">Prof. Me. Mateus de Lucca</p><p class="role">Doutorando CEFID/UDESC · biblioteca curada pelo agente <b>biblioteca-delucca</b></p></div>
    <span class="wm">DE LUCCA</span>
  </footer>
</div>
"""

JS = r"""
const DATA = /*DATA*/[];
const SYNTH = /*SYNTH*/[];
const META = /*META*/{};
const THEME={
  'motor-pattern':['Neuro','--t-neuro'],'emg-activation':['Neuro','--t-neuro'],'motor-unit':['Neuro','--t-neuro'],
  'firing-rate':['Neuro','--t-neuro'],'rfd-neural':['Neuro','--t-neuro'],'motor-learning':['Neuro','--t-neuro'],
  'anxiety':['Psico','--t-psico'],'perfectionism':['Psico','--t-psico'],'body-image':['Psico','--t-psico'],
  'disordered-eating':['Psico','--t-psico'],'motivation':['Psico','--t-psico'],'self-confidence':['Psico','--t-psico'],
  'stress-coping':['Psico','--t-psico'],'burnout':['Psico','--t-psico'],'mental-toughness':['Psico','--t-psico'],'flow':['Psico','--t-psico'],'attentional-focus':['Psico','--t-psico'],
  'physical-determinants':['Performance','--t-perf'],'biomechanics-technique':['Performance','--t-perf'],
  'anthropometry-maturation':['Performance','--t-perf'],'talent-prediction':['Performance','--t-perf'],'judging-scoring':['Performance','--t-perf'],
  'neuromuscular-fatigue':['Fadiga','--t-fadiga'],'training-load':['Fadiga','--t-fadiga'],'overtraining':['Fadiga','--t-fadiga'],
  'recovery-readiness':['Fadiga','--t-fadiga'],'red-s':['Fadiga','--t-fadiga'],'menstrual-hormonal':['Fadiga','--t-fadiga'],'perceived-fatigue':['Fadiga','--t-fadiga']
};
const TEMAS=['Neuro','Psico','Performance','Fadiga'];
const TCOLOR={Neuro:'--t-neuro',Psico:'--t-psico',Performance:'--t-perf',Fadiga:'--t-fadiga'};
const cssvar=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const theme=t=>THEME[t]?THEME[t][0]:'—';
const tcolor=t=>THEME[t]?cssvar(THEME[t][1]):'#888';
const num=v=>{const n=parseInt(String(v).replace(/\D/g,''));return isNaN(n)?-1:n;};
const state={q:'',sport:'',design:'',sort:'year',themes:new Set(),subvar:'',cell:null};

// shade a base color by index (lighter/darker variants for subvariables)
function shade(hex,f){const c=hex.replace('#','');const r=parseInt(c.substr(0,2),16),g=parseInt(c.substr(2,2),16),b=parseInt(c.substr(4,2),16);
  const m=(x)=>Math.max(0,Math.min(255,Math.round(f<0?x*(1+f):x+(255-x)*f)));
  return `rgb(${m(r)},${m(g)},${m(b)})`;}

/* ---------- stats ---------- */
function buildStats(){
  const themes={};DATA.forEach(d=>{const th=theme(d.topic);themes[th]=(themes[th]||0)+1;});
  const st=document.getElementById('stats');
  const perm=META.permanova?META.permanova.in_library??0:0;
  st.innerHTML=`<div class="stat"><b data-count="${DATA.length}">0</b><span>artigos</span></div>`+
    TEMAS.map(k=>`<div class="stat"><b data-count="${themes[k]||0}">0</b><span>${k}</span></div>`).join('')+
    `<div class="stat"><b data-count="${new Set(DATA.map(d=>d.sport)).size}">0</b><span>esportes</span></div>`+
    `<div class="stat"><b data-count="${new Set(DATA.map(d=>d.subvar)).size}">0</b><span>subvariáveis</span></div>`+
    `<div class="stat"><b data-count="${perm}">0</b><span>PERMANOVA</span></div>`;
}
/* count-up when visible */
function countUp(el){const tgt=+el.dataset.count;if(el._done)return;el._done=1;const t0=performance.now();const dur=900;
  (function step(t){const p=Math.min(1,(t-t0)/dur);el.textContent=Math.round(tgt*(1-Math.pow(1-p,3)));if(p<1)requestAnimationFrame(step);})(t0);}

/* ---------- segmented bars: variável × subvariável ---------- */
function subvarMap(){
  const m={};TEMAS.forEach(t=>m[t]={});
  DATA.forEach(d=>{const th=theme(d.topic);if(!m[th])m[th]={};m[th][d.subvar]=(m[th][d.subvar]||0)+1;});
  return m;
}
function buildSeg(){
  const m=subvarMap();const max=Math.max(...TEMAS.map(t=>Object.values(m[t]).reduce((a,b)=>a+b,0)));
  const host=document.getElementById('segvar');
  host.innerHTML=TEMAS.map(t=>{
    const subs=Object.entries(m[t]).sort((a,b)=>b[1]-a[1]);
    const tot=subs.reduce((a,[,v])=>a+v,0);const base=cssvar(TCOLOR[t]);
    const segs=subs.map(([s,v],i)=>{
      const col=shade(base,(i%2? .16:-.10)+(i*0.05));
      return `<div class="seg" data-tema="${t}" data-sub="${s}" data-lab="${s} · ${v}" title="${s}: ${v}"
        style="background:${col}" data-w="${(v/tot*100).toFixed(2)}"></div>`;}).join('');
    return `<div class="segrow"><div class="lab" style="color:${base}">${t}</div>
      <div class="track" data-scale="${(tot/max*100).toFixed(2)}">${segs}</div>
      <div class="val">${tot}</div></div>`;
  }).join('');
  host.querySelectorAll('.seg').forEach(s=>s.onclick=()=>{filterToSub(s.dataset.tema,s.dataset.sub);});
}
function animSeg(){document.querySelectorAll('#segvar .track').forEach(tr=>{
  const scale=+tr.dataset.scale/100;
  tr.querySelectorAll('.seg').forEach(s=>{s.style.width=(+s.dataset.w*scale).toFixed(2)+'%';});});}

/* ---------- sport bars ---------- */
function buildSport(){
  const c={};DATA.forEach(d=>c[d.sport]=(c[d.sport]||0)+1);
  const arr=Object.entries(c).sort((a,b)=>b[1]-a[1]);const max=arr[0][1];
  const host=document.getElementById('sportbars');
  host.innerHTML=arr.map(([s,v])=>{
    // color by dominant theme of that sport
    const th=domTheme(s);const col=cssvar(TCOLOR[th]||'--gold');
    return `<div class="hbar"><div class="nm" title="${s}">${s}</div>
      <div class="bar" data-w="${(v/max*100).toFixed(1)}" data-sport="${s}" style="background:${col}"></div>
      <div class="c">${v}</div></div>`;}).join('');
  host.querySelectorAll('.bar').forEach(b=>b.onclick=()=>{filterToSport(b.dataset.sport);});
}
function domTheme(sport){const c={};DATA.filter(d=>d.sport===sport).forEach(d=>{const t=theme(d.topic);c[t]=(c[t]||0)+1;});
  return Object.entries(c).sort((a,b)=>b[1]-a[1])[0][0];}
function animSport(){document.querySelectorAll('#sportbars .bar').forEach(b=>b.style.width=b.dataset.w+'%');}

/* ---------- design chart ---------- */
const DCOLOR={'Revisão sistemática':'#8a7bd8','Meta-análise':'#b06de0','Revisão narrativa':'#6d8ce0',
  'ECR':'#33b98a','Experimental':'#3fb0a6','Longitudinal':'#e8c24a','Transversal':'#4f93d6',
  'Estudo de caso':'#e2853a','Validação/Psicométrico':'#d86d9a','Qualitativo':'#7a8698','—':'#4a5468'};
function buildDesign(){
  const c={};DATA.forEach(d=>c[d.design]=(c[d.design]||0)+1);
  const arr=Object.entries(c).sort((a,b)=>b[1]-a[1]);const max=arr[0][1];
  const host=document.getElementById('dchart');
  host.innerHTML=arr.map(([d,v])=>`<div class="drow"><div class="dn">${d}</div>
    <div class="dt"><div class="df" data-w="${(v/max*100).toFixed(1)}" data-design="${d}" style="background:${DCOLOR[d]||'#4a5468'}"></div></div>
    <div class="dv">${v}</div></div>`).join('');
  host.querySelectorAll('.df').forEach(f=>f.onclick=()=>{filterToDesign(f.dataset.design);});
  const nExp=(c['Experimental']||0)+(c['ECR']||0);const nRev=(c['Revisão sistemática']||0)+(c['Meta-análise']||0)+(c['Revisão narrativa']||0);
  const nObs=(c['Transversal']||0)+(c['Longitudinal']||0);
  document.getElementById('dhint').innerHTML=`Predomínio <b>observacional</b> (${nObs} transversais/longitudinais) vs. <b>${nExp}</b> experimentais/ECR e <b>${nRev}</b> revisões — típico da área e um alvo de melhoria metodológica.`;
  // notes card
  const notes=[
    ['Transversal','Fotografa associações (EMG, antropometria, psicometria). Barato e comum — mas não estabelece causa.'],
    ['Longitudinal','Segue a atleta ao longo da temporada; captura carga, RED-S e adaptação. Escasso e valioso.'],
    ['Experimental / ECR','Testa intervenções (pliometria, treino de força reativa, cafeína). O que mais falta nesta população.'],
    ['Revisões','Consolidam lesão e transtorno alimentar; base para a introdução da revisão sistemática.']
  ];
  document.getElementById('designnotes').innerHTML=notes.map(([k,t])=>`<div><span>${k}</span><span style="max-width:60%;text-align:right;color:var(--mid);font-weight:400">${t}</span></div>`).join('');
}
function animDesign(){document.querySelectorAll('#dchart .df').forEach(f=>f.style.width=f.dataset.w+'%');}

/* ---------- PERMANOVA ---------- */
function buildPerm(){
  const p=META.permanova||{};
  document.getElementById('permbig').dataset.count=p.in_library??0;
  document.getElementById('permhead').textContent=
    `${p.in_library??0} no acervo · ${p.count_found??0} localizados na literatura de esportes estéticos femininos`;
  document.getElementById('permverdict').textContent=p.verdict||'';
  document.getElementById('permmethods').innerHTML='<span style="color:var(--gold)">Métodos que dominam:</span>'+
    (p.dominant_methods||[]).map(m=>`<span>${m}</span>`).join('');
}

/* ---------- PRISMA ---------- */
function buildPrisma(){
  const n=DATA.length;const dois=new Set(DATA.map(d=>d.doi)).size;
  const stages=[
    ['Identificação',`Registros nas bases (${(META.prisma&&META.prisma.databases||[]).join(', ')}) + curadoria do agente <b>biblioteca-delucca</b>.`],
    ['Triagem',`Títulos/resumos avaliados; filtro por <b>esportes estéticos femininos</b> e artigo internacional peer-reviewed.`],
    ['Elegibilidade',`Texto/registro verificado; <b>${dois}</b> DOIs únicos confirmados; duplicatas removidas.`],
    ['Incluídos',`<b>${n}</b> estudos catalogados por esporte × variável × subvariável × desenho.`]
  ];
  document.getElementById('prisma').innerHTML=stages.map((s,i)=>
    `<div class="pbox"><div class="stage">${s[0]}</div><div class="body">${s[1]}</div></div>`+
    (i<stages.length-1?'<div class="pconn"></div>':'')).join('');
}

/* ---------- matrix design × variável ---------- */
function buildMatrix(){
  const designs=[...new Set(DATA.map(d=>d.design))];
  // order by total desc
  const dtot={};designs.forEach(d=>dtot[d]=DATA.filter(x=>x.design===d).length);
  designs.sort((a,b)=>dtot[b]-dtot[a]);
  const grid={};let max=0;
  designs.forEach(d=>{grid[d]={};TEMAS.forEach(t=>{const c=DATA.filter(x=>x.design===d&&theme(x.topic)===t).length;grid[d][t]=c;if(c>max)max=c;});});
  const tbl=document.getElementById('matrix');
  let html='<thead><tr><th class="rh">Desenho \\ Variável</th>'+TEMAS.map(t=>`<th style="color:${cssvar(TCOLOR[t])}">${t}</th>`).join('')+'</tr></thead><tbody>';
  designs.forEach(d=>{html+=`<tr><th class="rh">${d}</th>`+TEMAS.map(t=>{
    const c=grid[d][t];const base=cssvar(TCOLOR[t]);
    return `<td data-design="${d}" data-tema="${t}" data-c="${c}"><div class="cell" data-fill="${c?(0.28+0.72*c/max).toFixed(2):0}" style="background:${c?base:'transparent'}">${c||''}</div></td>`;
  }).join('')+'</tr>';});
  html+='</tbody>';tbl.innerHTML=html;
  tbl.querySelectorAll('td').forEach(td=>{if(+td.dataset.c>0)td.onclick=()=>filterToCell(td.dataset.design,td.dataset.tema);});
}
function animMatrix(){document.querySelectorAll('#matrix .cell').forEach((c,i)=>{
  const f=+c.dataset.fill;setTimeout(()=>{c.style.opacity=f>0?f:0;c.style.transform='scale(1)';},i*22);});}

/* ---------- PICOS / dbs / rob ---------- */
function buildReviewMeta(){
  const pr=META.prisma||{};const pic=pr.pico||{};
  const order=[['P','População'],['I','Intervenção/Exposição'],['C','Comparador'],['O','Desfecho'],['S','Desenho']];
  document.getElementById('pico').innerHTML=order.map(([k,lab])=>
    `<div class="k">${k}</div><div class="v"><b style="color:var(--hi)">${lab}:</b> ${pic[k]||'—'}</div>`).join('');
  document.getElementById('dbs').innerHTML='<span style="color:var(--gold)">Bases:</span>'+(pr.databases||[]).map(d=>`<span>${d}</span>`).join('');
  const rob=pr.risk_of_bias||{};
  document.getElementById('rob').innerHTML=Object.entries(rob).map(([k,v])=>`<div><span>${k}</span><span>${v}</span></div>`).join('');
  document.getElementById('synthesis').textContent=pr.synthesis||'';
}

/* ---------- synth ---------- */
function buildSynth(){document.getElementById('synth').innerHTML=SYNTH.map(s=>
  `<div class="scard" style="--c:${cssvar(s.color)}"><h3>${s.title}</h3><p>${s.text}</p></div>`).join('');}

/* ---------- filters wiring from charts ---------- */
function scrollAcervo(){document.getElementById('acervo').scrollIntoView({behavior:'smooth'});}
function syncChips(){document.querySelector('#chips .all').setAttribute('aria-pressed',state.themes.size===0);
  document.querySelectorAll('#chips .chip[data-t]').forEach(x=>x.setAttribute('aria-pressed',state.themes.has(x.dataset.t)));}
function filterToSub(tema,sub){state.themes=new Set([tema]);state.subvar=sub;state.sport='';state.design='';
  document.getElementById('sport').value='';document.getElementById('design').value='';syncChips();render();scrollAcervo();}
function filterToSport(sport){state.sport=sport;state.subvar='';document.getElementById('sport').value=sport;render();scrollAcervo();}
function filterToDesign(d){state.design=d;state.subvar='';document.getElementById('design').value=d;render();scrollAcervo();}
function filterToCell(d,tema){state.design=d;state.themes=new Set([tema]);state.subvar='';state.sport='';
  document.getElementById('design').value=d;document.getElementById('sport').value='';syncChips();render();scrollAcervo();}

/* ---------- table ---------- */
function buildControls(){
  const chips=document.getElementById('chips');
  chips.innerHTML=`<button class="chip all" aria-pressed="true">Todos</button>`+
    TEMAS.map(t=>`<button class="chip" data-t="${t}" aria-pressed="false" style="--c:${cssvar(TCOLOR[t])}"><i></i>${t}</button>`).join('');
  chips.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{
    state.subvar='';
    if(c.classList.contains('all')){state.themes.clear();}
    else{const t=c.dataset.t;state.themes.has(t)?state.themes.delete(t):state.themes.add(t);}
    syncChips();render();});
  const sports=[...new Set(DATA.map(d=>d.sport))].sort();
  document.getElementById('sport').insertAdjacentHTML('beforeend',sports.map(s=>`<option>${s}</option>`).join(''));
  const designs=[...new Set(DATA.map(d=>d.design))].filter(d=>d&&d!=='—').sort();
  document.getElementById('design').insertAdjacentHTML('beforeend',designs.map(s=>`<option>${s}</option>`).join(''));
}
function render(){
  let rows=DATA.filter(d=>{
    if(state.themes.size && !state.themes.has(theme(d.topic)))return false;
    if(state.sport && d.sport!==state.sport)return false;
    if(state.design && d.design!==state.design)return false;
    if(state.subvar && d.subvar!==state.subvar)return false;
    if(state.q){const s=(d.authors+' '+d.title+' '+d.journal+' '+d.finding+' '+d.doi+' '+d.subvar).toLowerCase();if(!s.includes(state.q))return false;}
    return true;});
  rows.sort((a,b)=> state.sort==='cit'?(num(b.citations)-num(a.citations)):state.sort==='auth'?a.authors.localeCompare(b.authors):(b.year-a.year));
  document.getElementById('rows').innerHTML=rows.map(d=>`<tr>
    <td class="t-auth">${d.authors}</td>
    <td class="t-year">${d.year}</td>
    <td><span class="t-title">${d.title}</span><span class="t-find">${d.finding||''}</span></td>
    <td>${d.journal}</td>
    <td><span class="badge" style="--c:${tcolor(d.topic)}">${theme(d.topic)}</span><span class="subv">${d.subvar}</span></td>
    <td><span class="dpill">${d.design}</span></td>
    <td class="sport">${d.sport}</td>
    <td>${d.citations??'n/d'}</td>
    <td><a class="doi" href="https://doi.org/${d.doi}" target="_blank" rel="noopener">DOI ↗</a></td>
  </tr>`).join('');
  document.getElementById('empty').hidden=rows.length>0;
  const flt=[state.subvar,state.design,state.sport,[...state.themes].join('+')].filter(Boolean).join(' · ');
  document.getElementById('note').textContent=`Exibindo ${rows.length} de ${DATA.length} artigos`+(flt?` · filtro: ${flt}`:'')+` · DOI verificado.`;
}

/* ---------- events ---------- */
document.getElementById('q').oninput=e=>{state.q=e.target.value.toLowerCase().trim();render();};
document.getElementById('sport').onchange=e=>{state.sport=e.target.value;render();};
document.getElementById('design').onchange=e=>{state.design=e.target.value;render();};
document.getElementById('sort').onchange=e=>{state.sort=e.target.value;render();};
document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;
  if(k==='citations')state.sort='cit';else if(k==='authors')state.sort='auth';else if(k==='year')state.sort='year';
  document.getElementById('sort').value=state.sort;render();});

/* ---------- init + reveal-on-scroll (real-time plotting) ---------- */
buildStats();buildSeg();buildSport();buildDesign();buildPerm();buildPrisma();buildMatrix();buildReviewMeta();buildSynth();buildControls();render();
const REVEAL={setores:()=>{animSeg();animSport();},tipos:animDesign,revisao:animMatrix};
const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){
  if(REVEAL[e.target.id]){REVEAL[e.target.id]();}
  e.target.querySelectorAll?e.target.querySelectorAll('.stat b[data-count],#permbig').forEach(countUp):0;
  }});},{threshold:.25});
['setores','tipos','revisao'].forEach(id=>io.observe(document.getElementById(id)));
document.querySelectorAll('.stat b[data-count]').forEach(el=>io.observe(el.closest('.stats')||el));
// stats + permanova count-up
const io2=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting){
  e.target.querySelectorAll('b[data-count]').forEach(countUp);
  const pb=e.target.querySelector?document.getElementById('permbig'):null;}}),{threshold:.3});
io2.observe(document.getElementById('stats'));
const permObs=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting)countUp(document.getElementById('permbig'));}),{threshold:.4});
permObs.observe(document.getElementById('permanova'));
"""

def build():
    html = "<title>Biblioteca · Esportes Estéticos</title>\n"
    html += "<style>\n/* ==== embedded fonts ==== */\n" + fontface + "\n" + CSS + "\n</style>\n"
    html += BODY + "\n<script>\n"
    js = JS.replace("/*DATA*/[]", "/*DATA*/" + json.dumps(data, ensure_ascii=False))
    js = js.replace("/*SYNTH*/[]", "/*SYNTH*/" + json.dumps(synth, ensure_ascii=False))
    js = js.replace("/*META*/{}", "/*META*/" + json.dumps(meto, ensure_ascii=False))
    html += js + "\n</script>\n"
    out = os.path.join(ROOT, "biblioteca.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"built {out}  ·  {len(data)} artigos  ·  {len(html)} bytes")

if __name__ == "__main__":
    build()
