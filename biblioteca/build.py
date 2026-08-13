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

# --- normalize: ensure every entry has all fields even if enrichment absent ---
PYTHEME = {  # topic -> variable
    'motor-pattern':'Neuro','emg-activation':'Neuro','motor-unit':'Neuro','firing-rate':'Neuro','rfd-neural':'Neuro','motor-learning':'Neuro',
    'anxiety':'Psico','perfectionism':'Psico','body-image':'Psico','disordered-eating':'Psico','motivation':'Psico','self-confidence':'Psico',
    'stress-coping':'Psico','burnout':'Psico','mental-toughness':'Psico','flow':'Psico','attentional-focus':'Psico',
    'self-talk':'Psico','motivational-climate':'Psico','resilience':'Psico','well-being':'Psico','passion':'Psico','emotion-regulation':'Psico','coping':'Psico','mental-health':'Psico','self-esteem':'Psico','fear-of-failure':'Psico','imagery':'Psico',
    'physical-determinants':'Performance','biomechanics-technique':'Performance','anthropometry-maturation':'Performance','talent-prediction':'Performance','judging-scoring':'Performance',
    'muscular-power':'Performance','plyometrics':'Performance','physiological':'Performance','physical-capacities':'Performance','neuromuscular-capacity':'Neuro',
    'neuromuscular-fatigue':'Fadiga','training-load':'Fadiga','overtraining':'Fadiga','recovery-readiness':'Fadiga','red-s':'Fadiga','menstrual-hormonal':'Fadiga','perceived-fatigue':'Fadiga',
}
def canon_modalities(sport):
    s = (sport or "").lower()
    out = []
    def add(x):
        if x not in out: out.append(x)
    if 'rítmica' in s or 'ritmica' in s: add('Ginástica rítmica')
    if 'aeróbic' in s or 'aerobic' in s: add('Ginástica aeróbica')
    if 'artística' in s or 'artistica' in s:
        add('Nado artístico' if 'nado' in s else 'Ginástica artística')
    if 'acrobática' in s or 'acrobatica' in s: add('Ginástica acrobática')
    if 'patinação' in s or 'patinacao' in s: add('Patinação artística')
    if 'nado' in s or 'sincronizado' in s: add('Nado artístico')
    if 'balé' in s or 'bale' in s or 'dança' in s or 'danca' in s or 'cheer' in s: add('Dança')
    if 'proxy' in s or 'saudáveis' in s or 'master' in s: add('Proxy não-estético')
    if 'estéticos' in s or 'esteticos' in s: [add(x) for x in ('Patinação artística','Dança','Ginástica artística')]
    if not out: add('Outro')
    return out
CANON_MODS = {'Ginástica rítmica','Ginástica artística','Ginástica aeróbica','Patinação artística','Nado artístico',
              'Dança','Ginástica acrobática','Proxy não-estético','Outro'}
CANON_VARS = {'Neuro','Psico','Performance','Fadiga'}
def canonize_mods(mods, sport):
    out = []
    for m in (mods or []):
        for c in ([m] if m in CANON_MODS else canon_modalities(m)):
            if c not in out:
                out.append(c)
    if not out:
        out = canon_modalities(sport)
    return out
for d in data:
    d.setdefault("design", "—")
    d.setdefault("design_conf", "média")
    d.setdefault("subvar", d.get("topic", "—"))
    d.setdefault("n", None)
    d.setdefault("biomech", False)
    d.setdefault("methods", [])
    d.setdefault("stats_approach", "n/d")
    d.setdefault("effect_size", False)
    d.setdefault("es_note", "")
    d.setdefault("roc", False)
    d.setdefault("derivatives", False)
    d.setdefault("idioma", "en")
    # canonicalize variables to the 4 themes (drop stray predictor names)
    vs = [v for v in (d.get("variables") or []) if v in CANON_VARS]
    seen = []
    [seen.append(v) for v in vs if v not in seen]
    d["variables"] = seen or [PYTHEME.get(d.get("topic", ""), "Performance")]
    # canonicalize modalities to the fixed set
    d["modalities"] = canonize_mods(d.get("modalities"), d.get("sport", ""))
    d["n_modalities"] = len(d["modalities"])

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
/* ---- analytics (KPIs + botões) ---- */
.anbar{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 16px}
.anbtn{font-family:var(--cond);font-weight:600;font-size:12.5px;letter-spacing:.04em;color:var(--mid);background:var(--ink-2);border:1px solid var(--line);border-radius:99px;padding:9px 14px;cursor:pointer;transition:.18s;display:flex;align-items:center;gap:8px}
.anbtn:hover{color:var(--hi);border-color:var(--gold)}
.anbtn[aria-pressed=true]{color:#0a0b10;background:var(--gold);border-color:var(--gold)}
.anbtn .k{font-family:var(--disp);font-size:13px;opacity:.85}
.anbtn[aria-pressed=true] .k{opacity:1}
.anbtn.clr{color:var(--low)}
.kpi{display:flex;flex-direction:column;gap:14px}
.kpi .top{display:flex;align-items:baseline;gap:16px}
.kpi .num{font-family:var(--disp);font-size:clamp(46px,9vw,74px);line-height:.82;color:var(--gold);text-shadow:0 3px 0 #0006}
.kpi .pct{font-family:var(--disp);font-size:26px;color:var(--hi);line-height:1}
.kpi .cap{font-family:var(--cond);font-weight:600;font-size:12.5px;letter-spacing:.05em;color:var(--mid);text-transform:uppercase;margin-top:3px}
.kpi .desc{color:var(--mid);font-size:13.5px;margin:0}
.mini{display:flex;flex-direction:column;gap:8px}
.mini .r{display:grid;grid-template-columns:100px 1fr 34px;align-items:center;gap:10px}
.mini .r .nm{font-size:12px;color:var(--mid);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mini .r .bar{height:14px;border-radius:5px;width:0;transition:width .85s cubic-bezier(.2,.8,.2,1)}
.mini .r .v{font-family:var(--disp);font-size:13px;color:var(--hi)}
.uni{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:720px){.uni{grid-template-columns:1fr}}
.uni h4{font-family:var(--cond);font-weight:700;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--gold);margin:0 0 10px}
.uni ol{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:9px}
.uni li{font-size:12.5px;color:var(--mid);border-bottom:1px dashed var(--line);padding-bottom:8px;line-height:1.35}
.uni li b{color:var(--hi);font-family:var(--cond);font-weight:600}
.uni .tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:5px}
.uni .tag{font-size:10px;letter-spacing:.02em;color:#0a0b10;border-radius:5px;padding:2px 7px;font-weight:600}
.drillrow{border:1px solid var(--line);border-radius:12px;padding:13px 16px;margin-bottom:10px;background:var(--ink-2);cursor:pointer;transition:.15s}
.drillrow:hover{border-color:#e3a94255}
.drillrow .h{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.drillrow .h .mn{font-family:var(--cond);font-weight:700;font-size:15px;color:var(--hi)}
.drillrow .h .meta{font-size:12px;color:var(--mid)}
.drillrow .h .bio{font-family:var(--disp);font-size:15px;color:var(--gold)}
.stack{display:flex;height:15px;border-radius:5px;overflow:hidden;margin:10px 0 7px;background:#ffffff08}
.stack span{height:100%;width:0;transition:width .85s cubic-bezier(.2,.8,.2,1)}
.subtop{display:flex;flex-wrap:wrap;gap:6px}
.subtop span{font-size:11px;color:var(--mid);background:#ffffff0c;border:1px solid var(--line);border-radius:99px;padding:3px 9px}
/* ---- psicologia ---- */
.pgrid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:820px){.pgrid{grid-template-columns:1fr}}
.pcard{background:linear-gradient(180deg,var(--ink-2),var(--ink-1));border:1px solid #ffffff0e;border-left:3px solid var(--t-psico);border-radius:14px;padding:16px 18px;box-shadow:0 22px 50px -40px #000}
.pcard .ph{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.pcard h3{font-family:var(--cond);font-weight:700;letter-spacing:.02em;margin:0;color:var(--t-psico);font-size:16px}
.pcard .tot{font-family:var(--disp);font-size:24px;color:var(--hi);line-height:1}
.pcard .pv{cursor:pointer}
.pcard .pv:hover .nm{color:var(--hi)}
.pcard .empty0{color:var(--low);font-size:12.5px;font-style:italic;margin:10px 0 0}
/* ---- linha do tempo ---- */
.tlwrap{position:relative;width:100%;overflow-x:auto}
svg.tl{display:block;width:100%;min-width:680px;height:auto}
.tl .axis{stroke:var(--line);stroke-width:1}
.tl .grid{stroke:#ffffff08;stroke-width:1}
.tl text{fill:var(--mid);font-family:var(--sans)}
.tl .lbl{fill:var(--low);font-size:10px}
.tl path.series{fill:none;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round;filter:drop-shadow(0 3px 6px #0006)}
.tl circle.dot{stroke:var(--ink-1);stroke-width:1.4}
.tllegend{display:flex;flex-wrap:wrap;gap:12px;margin-top:12px}
.tllegend .it{display:flex;align-items:center;gap:7px;font-size:12px;color:var(--mid)}
.tllegend .sw{width:16px;height:3px;border-radius:2px}
/* ---- ficha (detalhe do artigo) ---- */
tr.arow{cursor:pointer}
tr.arow.open{background:#e3a9420d}
tr.detail td{background:var(--ink-1);border-bottom:1px solid var(--line);padding:4px 14px 14px}
.ficha{display:grid;grid-template-columns:repeat(3,1fr);gap:12px 22px;padding:8px 2px}
@media(max-width:820px){.ficha{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.ficha{grid-template-columns:1fr}}
.ficha .f{border-left:2px solid var(--line);padding-left:12px}
.ficha .f.full{grid-column:1/-1}
.ficha .k{font-family:var(--cond);font-weight:600;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin:0 0 3px}
.ficha .v{font-size:13px;color:var(--hi);margin:0;line-height:1.45}
.ficha .v.mut{color:var(--low)}
"""

BODY = r"""
<div class="wrap">
  <p class="eyebrow">Base Científica · Biblioteca Virtual</p>
  <h1>Esportes estéticos<br>femininos</h1>
  <p class="lede">Acervo internacional com DOI verificado — catalogado e segmentado por <b>esporte</b>, <b>variável</b> e <b>subvariável</b>, com desenho de estudo e uma base metodológica para revisão sistemática.</p>

  <div class="stats" id="stats"></div>

  <nav class="jump">
    <a href="#setores">Setores</a>
    <a href="#linha">Linha do tempo</a>
    <a href="#tipos">Tipos de estudo</a>
    <a href="#analises">Análises</a>
    <a href="#psico">Psicologia</a>
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
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Por modalidade</h3>
        <p class="hint">Volume de evidência por modalidade estética (dança unificada). Clique para filtrar.</p>
        <div id="sportbars"></div>
      </div>
    </div>
  </section>

  <!-- LINHA DO TEMPO -->
  <section class="block" id="linha">
    <h2 class="sec">Linha do tempo</h2>
    <p class="sub">Evolução espaço-temporal · clique para plotar</p>
    <div class="anbar" id="tlbar"></div>
    <div class="card">
      <div class="tlwrap"><svg class="tl" id="tlsvg" viewBox="0 0 1000 380" preserveAspectRatio="xMidYMid meet"></svg></div>
      <div class="tllegend" id="tllegend"></div>
      <p class="hint" id="tlhint"></p>
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
    <div class="card" style="margin-top:18px">
      <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Revisões por modalidade</h3>
      <p class="hint">Segmente por tipo de revisão (sistemática · integrativa · narrativa · meta-análise). Clique numa barra para filtrar o acervo.</p>
      <div class="anbar" id="revbar"></div>
      <div id="revchart"></div>
    </div>
  </section>

  <!-- ANÁLISES ESTATÍSTICAS -->
  <section class="block" id="analises">
    <h2 class="sec">Análises estatísticas</h2>
    <p class="sub">Botões · KPIs segmentados · mineração da biblioteca</p>
    <div class="anbar" id="anbar"></div>
    <div class="grid2">
      <div class="card kpi" id="kpi"></div>
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Segmentação por subvariável</h3>
        <p class="hint">Percentuais do recorte selecionado — clique um botão acima.</p>
        <div id="anseg"></div>
      </div>
    </div>
    <div class="grid2" style="margin-top:18px">
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Cruzamento modalidade × método</h3>
        <p class="hint">Quantos estudos de cada modalidade usam cada método. Clique para filtrar.</p>
        <div class="matx"><table class="mx" id="crosstab"></table></div>
      </div>
      <div class="card">
        <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 10px;font-size:16px">Estudos que unem mais modalidades / variáveis</h3>
        <div id="uniao"></div>
      </div>
    </div>
    <div class="card" style="margin-top:18px">
      <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Por modalidade — quanto é biomecânica e as variáveis (%)</h3>
      <p class="hint">Ex.: dos estudos de ginástica rítmica, quantos são de biomecânica e como se distribuem as variáveis/subvariáveis. Clique para filtrar o acervo.</p>
      <div id="drill"></div>
    </div>
  </section>

  <!-- VARIÁVEIS PSICOLÓGICAS -->
  <section class="block" id="psico">
    <h2 class="sec">Variáveis psicológicas</h2>
    <p class="sub">Subcategorias · por modalidade</p>
    <div class="pgrid" id="psicocards"></div>
    <div class="card" style="margin-top:18px">
      <h3 style="font-family:var(--cond);font-weight:700;margin:0 0 4px;font-size:16px">Subcategoria psicológica × modalidade</h3>
      <p class="hint">Onde a pesquisa psicológica se concentra. Clique numa célula para filtrar o acervo.</p>
      <div class="matx"><table class="mx" id="psicomatrix"></table></div>
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
        <select id="sport"><option value="">Todas as modalidades</option></select>
        <select id="design"><option value="">Todos os desenhos</option></select>
        <select id="idioma"><option value="">Todos os idiomas</option></select>
        <select id="sort">
          <option value="year">Ordenar: ano ↓</option>
          <option value="cit">Ordenar: citações ↓</option>
          <option value="auth">Ordenar: autor A–Z</option>
        </select>
      </div>
      <div class="chips" id="chips"></div>
    </div>
    <p class="hint">Clique numa linha para abrir a <b>ficha completa</b>: amostra, resumo, variáveis biodinâmicas, delineamento, análise estatística e síntese.</p>
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
  'self-talk':['Psico','--t-psico'],'motivational-climate':['Psico','--t-psico'],'resilience':['Psico','--t-psico'],'well-being':['Psico','--t-psico'],'passion':['Psico','--t-psico'],'emotion-regulation':['Psico','--t-psico'],'coping':['Psico','--t-psico'],'mental-health':['Psico','--t-psico'],'self-esteem':['Psico','--t-psico'],'fear-of-failure':['Psico','--t-psico'],'imagery':['Psico','--t-psico'],
  'physical-determinants':['Performance','--t-perf'],'biomechanics-technique':['Performance','--t-perf'],
  'anthropometry-maturation':['Performance','--t-perf'],'talent-prediction':['Performance','--t-perf'],'judging-scoring':['Performance','--t-perf'],
  'muscular-power':['Performance','--t-perf'],'plyometrics':['Performance','--t-perf'],'physiological':['Performance','--t-perf'],'physical-capacities':['Performance','--t-perf'],'neuromuscular-capacity':['Neuro','--t-neuro'],
  'neuromuscular-fatigue':['Fadiga','--t-fadiga'],'training-load':['Fadiga','--t-fadiga'],'overtraining':['Fadiga','--t-fadiga'],
  'recovery-readiness':['Fadiga','--t-fadiga'],'red-s':['Fadiga','--t-fadiga'],'menstrual-hormonal':['Fadiga','--t-fadiga'],'perceived-fatigue':['Fadiga','--t-fadiga']
};
const TEMAS=['Neuro','Psico','Performance','Fadiga'];
const TCOLOR={Neuro:'--t-neuro',Psico:'--t-psico',Performance:'--t-perf',Fadiga:'--t-fadiga'};
const LANG={en:'Inglês',pt:'Português',es:'Espanhol'};
const cssvar=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const theme=t=>THEME[t]?THEME[t][0]:'—';
const tcolor=t=>THEME[t]?cssvar(THEME[t][1]):'#888';
const num=v=>{const n=parseInt(String(v).replace(/\D/g,''));return isNaN(n)?-1:n;};
const state={q:'',sport:'',design:'',idioma:'',sort:'year',themes:new Set(),subvar:'',analysis:'',modality:'',methodcol:'',topic:'',psicogroup:'',reviewsOnly:false};

// shade a base color by index (lighter/darker variants for subvariables)
function shade(hex,f){const c=hex.replace('#','');const r=parseInt(c.substr(0,2),16),g=parseInt(c.substr(2,2),16),b=parseInt(c.substr(4,2),16);
  const m=(x)=>Math.max(0,Math.min(255,Math.round(f<0?x*(1+f):x+(255-x)*f)));
  return `rgb(${m(r)},${m(g)},${m(b)})`;}

/* ---------- stats ---------- */
function buildStats(){
  const themes={};DATA.forEach(d=>{const th=theme(d.topic);themes[th]=(themes[th]||0)+1;});
  const st=document.getElementById('stats');
  const bio=DATA.filter(d=>d.biomech).length;
  st.innerHTML=`<div class="stat"><b data-count="${DATA.length}">0</b><span>artigos</span></div>`+
    TEMAS.map(k=>`<div class="stat"><b data-count="${themes[k]||0}">0</b><span>${k}</span></div>`).join('')+
    `<div class="stat"><b data-count="${new Set(DATA.map(d=>d.sport)).size}">0</b><span>esportes</span></div>`+
    `<div class="stat"><b data-count="${new Set(DATA.map(d=>d.subvar)).size}">0</b><span>subvariáveis</span></div>`+
    `<div class="stat"><b data-count="${bio}">0</b><span>biomecânica</span></div>`;
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
  const mods=modalityList();const c={};mods.forEach(m=>c[m]=DATA.filter(d=>inMod(d,m)).length);
  const arr=Object.entries(c).sort((a,b)=>b[1]-a[1]);const max=arr[0][1];
  const host=document.getElementById('sportbars');
  host.innerHTML=arr.map(([m,v])=>`<div class="hbar"><div class="nm" title="${m}">${m}</div>
      <div class="bar" data-w="${(v/max*100).toFixed(1)}" data-mod="${m}" style="background:${modColor(m)}"></div>
      <div class="c">${v}</div></div>`).join('');
  host.querySelectorAll('.bar').forEach(b=>b.onclick=()=>{clearAllFilters();state.modality=b.dataset.mod;applyKPI();render();scrollAcervo();});
}
function animSport(){document.querySelectorAll('#sportbars .bar').forEach(b=>b.style.width=b.dataset.w+'%');}

/* ---------- design chart ---------- */
const DCOLOR={'Revisão sistemática':'#8a7bd8','Meta-análise':'#b06de0','Revisão narrativa':'#6d8ce0','Revisão integrativa':'#7d8ae0',
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

/* ---------- REVISÕES por modalidade ---------- */
const REVIEW_KINDS=['Revisão sistemática','Revisão integrativa','Revisão narrativa','Meta-análise'];
const REVIEW_TYPES=[
  {k:'all',lab:'Todas as revisões',test:d=>REVIEW_KINDS.includes(d.design)},
  {k:'Revisão sistemática',lab:'Sistemática',test:d=>d.design==='Revisão sistemática'},
  {k:'Revisão integrativa',lab:'Integrativa',test:d=>d.design==='Revisão integrativa'},
  {k:'Revisão narrativa',lab:'Narrativa',test:d=>d.design==='Revisão narrativa'},
  {k:'Meta-análise',lab:'Meta-análise',test:d=>d.design==='Meta-análise'}
];
let REV_ACTIVE='all';
function buildReviews(){
  const bar=document.getElementById('revbar');
  bar.innerHTML=REVIEW_TYPES.map((r,i)=>`<button class="anbtn" data-k="${r.k}" aria-pressed="${i===0}"><span class="k">${DATA.filter(r.test).length}</span>${r.lab}</button>`).join('');
  bar.querySelectorAll('.anbtn').forEach(b=>b.onclick=()=>{
    bar.querySelectorAll('.anbtn').forEach(x=>x.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');
    REV_ACTIVE=b.dataset.k;plotReviews(b.dataset.k);
    clearAllFilters();
    if(b.dataset.k==='all')state.reviewsOnly=true; else state.design=b.dataset.k;
    render();scrollAcervo();});
  plotReviews('all');
}
function plotReviews(k){
  const r=REVIEW_TYPES.find(x=>x.k===k)||REVIEW_TYPES[0];const set=DATA.filter(r.test);
  const mods=modalityList();const c={};mods.forEach(m=>c[m]=set.filter(d=>inMod(d,m)).length);
  const arr=Object.entries(c).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]);const max=arr.length?arr[0][1]:1;
  const host=document.getElementById('revchart');
  if(!arr.length){host.innerHTML=`<p class="hint">Nenhuma revisão deste tipo no acervo ainda — alvo de busca automatizada.</p>`;return;}
  host.innerHTML=arr.map(([m,v])=>`<div class="hbar"><div class="nm" title="${m}">${m}</div>
    <div class="bar" data-w="${(v/max*100).toFixed(1)}" data-mod="${m}" style="background:${modColor(m)}"></div>
    <div class="c">${v}</div></div>`).join('')+`<p class="hint">${set.length} revisão(ões) · ${arr.length} modalidade(s).</p>`;
  requestAnimationFrame(()=>host.querySelectorAll('.bar').forEach(b=>b.style.width=b.dataset.w+'%'));
  host.querySelectorAll('.bar').forEach(b=>b.onclick=()=>{clearAllFilters();
    if(k==='all')state.reviewsOnly=true; else state.design=k;
    state.modality=b.dataset.mod;render();scrollAcervo();});
}

/* ---------- VARIÁVEIS PSICOLÓGICAS ---------- */
const PSICO_GROUPS=[
  {key:'corpo',label:'Pressão estética & corpo',topics:['body-image','disordered-eating','perfectionism','self-esteem','fear-of-failure']},
  {key:'ansiedade',label:'Ansiedade & autoconfiança',topics:['anxiety','self-confidence','self-talk','imagery']},
  {key:'motivacao',label:'Motivação & engajamento',topics:['motivation','motivational-climate','passion','attentional-focus']},
  {key:'resiliencia',label:'Resiliência & saúde mental',topics:['mental-toughness','resilience','stress-coping','coping','burnout','flow','well-being','emotion-regulation','mental-health']}
];
const PSUB={anxiety:'Ansiedade competitiva',perfectionism:'Perfeccionismo',
  'body-image':'Imagem corporal','disordered-eating':'Transtorno alimentar',motivation:'Motivação',
  'self-confidence':'Autoconfiança','stress-coping':'Estresse & coping',burnout:'Burnout',
  'mental-toughness':'Resiliência mental',flow:'Flow','attentional-focus':'Foco atencional',
  'self-talk':'Autofala','motivational-climate':'Clima motivacional',resilience:'Resiliência',
  'well-being':'Bem-estar',passion:'Paixão','emotion-regulation':'Regulação emocional',
  coping:'Coping','mental-health':'Saúde mental','self-esteem':'Autoestima','fear-of-failure':'Medo de falhar',imagery:'Imagética'};
const plabel=t=>PSUB[t]||t;
function clearAllFilters(){state.analysis='';state.modality='';state.methodcol='';state.subvar='';state.topic='';state.psicogroup='';state.themes.clear();state.sport='';state.design='';state.idioma='';state.reviewsOnly=false;
  const sp=document.getElementById('sport'),dg=document.getElementById('design'),ln=document.getElementById('idioma');if(sp)sp.value='';if(dg)dg.value='';if(ln)ln.value='';
  syncAnbar();document.querySelectorAll('#chips .chip[data-t]').forEach(x=>x.setAttribute('aria-pressed','false'));
  const all=document.querySelector('#chips .all');if(all)all.setAttribute('aria-pressed','true');applyKPI();}
function buildPsico(){
  const ps=DATA.filter(d=>theme(d.topic)==='Psico');const col=cssvar('--t-psico');
  document.getElementById('psicocards').innerHTML=PSICO_GROUPS.map(g=>{
    const gs=ps.filter(d=>g.topics.includes(d.topic));
    const byT={};gs.forEach(d=>byT[d.topic]=(byT[d.topic]||0)+1);
    const items=Object.entries(byT).sort((a,b)=>b[1]-a[1]);const maxT=items.length?items[0][1]:1;
    const mods=[...new Set(gs.flatMap(d=>modsOf(d)))];
    const body=items.length?`<div class="mini" style="margin-top:10px">`+items.map(([t,v])=>`<div class="r pv" data-topic="${t}" style="grid-template-columns:150px 1fr 30px"><div class="nm" title="${plabel(t)}">${plabel(t)}</div>
      <div class="bar" data-w="${(v/maxT*100).toFixed(0)}" style="background:${col}"></div><div class="v">${v}</div></div>`).join('')+`</div>
      <div class="subtop" style="margin-top:10px">${mods.map(m=>`<span style="color:${modColor(m)}">${m}</span>`).join('')}</div>`
      :`<p class="empty0">Sem estudos ainda — alvo prioritário da busca automatizada.</p>`;
    return `<div class="pcard"><div class="ph"><h3>${g.label}</h3><span class="tot">${gs.length}</span></div>${body}</div>`;
  }).join('');
  document.querySelectorAll('#psicocards .pv').forEach(r=>r.onclick=()=>{clearAllFilters();state.topic=r.dataset.topic;render();scrollAcervo();});
  buildPsicoMatrix(ps);
}
function buildPsicoMatrix(ps){
  const mods=modalityList().filter(m=>ps.some(d=>inMod(d,m)));
  const tbl=document.getElementById('psicomatrix');let max=0;const grid={};
  PSICO_GROUPS.forEach(g=>{grid[g.key]={};mods.forEach(m=>{const n=ps.filter(d=>g.topics.includes(d.topic)&&inMod(d,m)).length;grid[g.key][m]=n;if(n>max)max=n;});});
  let html='<thead><tr><th class="rh">Subcategoria \\ Modalidade</th>'+mods.map(m=>`<th style="color:${modColor(m)}">${m}</th>`).join('')+'</tr></thead><tbody>';
  PSICO_GROUPS.forEach(g=>{html+=`<tr><th class="rh">${g.label}</th>`+mods.map(m=>{const n=grid[g.key][m];
    return `<td data-grp="${g.key}" data-mod="${m}" data-c="${n}"><div class="cell" data-fill="${n?(0.3+0.7*n/max).toFixed(2):0}" style="background:${n?cssvar('--t-psico'):'transparent'}">${n||''}</div></td>`;}).join('')+'</tr>';});
  html+='</tbody>';tbl.innerHTML=html;
  tbl.querySelectorAll('td').forEach(td=>{if(+td.dataset.c>0)td.onclick=()=>{clearAllFilters();state.psicogroup=td.dataset.grp;state.modality=td.dataset.mod;render();scrollAcervo();};});
}
function animPsico(){document.querySelectorAll('#psicomatrix .cell').forEach((c,i)=>{const f=+c.dataset.fill;setTimeout(()=>{c.style.opacity=f>0?f:0;c.style.transform='scale(1)';},i*18);});
  document.querySelectorAll('#psicocards .mini .bar').forEach(b=>b.style.width=b.dataset.w+'%');}

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

/* ---------- ANÁLISES ESTATÍSTICAS ---------- */
const ANALYSES=[
  {k:'biomech',lab:'Biomecânica / Cinemática',test:d=>!!d.biomech,desc:'estudos que medem cinemática, cinética, EMG ou sinergias musculares'},
  {k:'derivatives',lab:'Derivadas & RFD',test:d=>!!d.derivatives,desc:'medidas de taxa/derivada: RFD, velocidade e aceleração angular, impulso, taxa de carga'},
  {k:'effect',lab:'Tamanho de efeito',test:d=>!!d.effect_size,desc:'reportam tamanho de efeito padronizado (d, g, η², r)'},
  {k:'roc',lab:'ROC / curva',test:d=>!!d.roc,desc:'classificação por curva ROC / AUC / sensibilidade-especificidade'},
  {k:'bayes',lab:'Bayesiano',test:d=>d.stats_approach==='Bayesiano'||d.stats_approach==='Misto'||(d.methods||[]).includes('Bayesiano'),desc:'estatística bayesiana'},
  {k:'multimod',lab:'Multimodalidade',test:d=>modsOf(d).length>=2,desc:'unem 2+ modalidades estéticas'},
  {k:'multivar',lab:'Multivariável',test:d=>(d.variables||[]).length>=2,desc:'cobrem 2+ variáveis (Neuro/Psico/Performance/Fadiga)'}
];
const METHODCOLS=[
  {k:'Biomecânica',test:d=>!!d.biomech},
  {k:'Derivadas',test:d=>!!d.derivatives},
  {k:'Efeito',test:d=>!!d.effect_size},
  {k:'ROC',test:d=>!!d.roc},
  {k:'Bayesiano',test:d=>d.stats_approach==='Bayesiano'||(d.methods||[]).includes('Bayesiano')}
];
const MODCOLOR={'Ginástica rítmica':'#e8c24a','Ginástica artística':'#33b98a','Ginástica aeróbica':'#e2853a','Patinação artística':'#4f93d6','Nado artístico':'#4fb0c8','Dança':'#b06de0','Ginástica acrobática':'#e0a24a','Proxy não-estético':'#7a8698','Outro':'#7a8698'};
const modColor=m=>MODCOLOR[m]||'#8a94a6';
const modsOf=d=>(Array.isArray(d.modalities)&&d.modalities.length)?d.modalities:[d.sport];
const inMod=(d,m)=>modsOf(d).includes(m);
const varsOf=d=>(d.variables&&d.variables.length)?d.variables:[theme(d.topic)];
const shortAuth=a=>String(a).split(',')[0];
function modalityList(){const c={};DATA.forEach(d=>modsOf(d).forEach(m=>c[m]=(c[m]||0)+1));
  return Object.entries(c).sort((a,b)=>b[1]-a[1]).map(x=>x[0]);}

function buildAnbar(){
  const bar=document.getElementById('anbar');
  bar.innerHTML=ANALYSES.map(a=>{const n=DATA.filter(a.test).length;
    return `<button class="anbtn" data-k="${a.k}" aria-pressed="false"><span class="k">${n}</span>${a.lab}</button>`;}).join('')+
    `<button class="anbtn clr" data-k="__clr">Limpar</button>`;
  bar.querySelectorAll('.anbtn').forEach(b=>b.onclick=()=>{
    if(b.dataset.k==='__clr'){clearAnalysis();return;}
    state.analysis=(state.analysis===b.dataset.k)?'':b.dataset.k;state.modality='';state.methodcol='';
    syncAnbar();applyKPI();render();});
}
function syncAnbar(){document.querySelectorAll('#anbar .anbtn[data-k]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.k===state.analysis&&state.analysis!==''));}
function clearAnalysis(){state.analysis='';state.modality='';state.methodcol='';syncAnbar();applyKPI();render();}

function applyKPI(){
  let set,label;
  if(state.modality||state.methodcol){set=DATA.filter(d=>(!state.modality||inMod(d,state.modality))&&(!state.methodcol||(METHODCOLS.find(c=>c.k===state.methodcol)||{test:()=>true}).test(d)));
    label={lab:[state.modality,state.methodcol].filter(Boolean).join(' · '),desc:'recorte do cruzamento modalidade × método'};}
  else if(state.analysis){const a=ANALYSES.find(x=>x.k===state.analysis);set=DATA.filter(a.test);label=a;}
  else {set=DATA;label=null;}
  renderKPI(label,set);
}
function renderKPI(a,set){
  const pct=Math.round(set.length/DATA.length*100);
  const byVar={};TEMAS.forEach(t=>byVar[t]=0);
  set.forEach(d=>varsOf(d).forEach(v=>{if(byVar[v]!=null)byVar[v]++;}));
  const maxV=Math.max(1,...Object.values(byVar));
  const kpi=document.getElementById('kpi');
  kpi.innerHTML=`<div class="top"><div class="num" data-count="${set.length}">0</div>
    <div><div class="pct">${pct}%</div><div class="cap">${a?a.lab:'Biblioteca completa'}</div></div></div>
    <p class="desc">${a?a.desc:'todos os estudos catalogados'} — <b style="color:var(--hi)">${set.length}</b> de ${DATA.length} estudos.</p>
    <div class="mini">`+TEMAS.map(t=>`<div class="r"><div class="nm" style="color:${cssvar(TCOLOR[t])}">${t}</div>
      <div class="bar" data-w="${(byVar[t]/maxV*100).toFixed(1)}" style="background:${cssvar(TCOLOR[t])}"></div>
      <div class="v">${byVar[t]}</div></div>`).join('')+`</div>`;
  countUp(kpi.querySelector('.num'));
  requestAnimationFrame(()=>kpi.querySelectorAll('.mini .bar').forEach(b=>b.style.width=b.dataset.w+'%'));
  // subvariáveis
  const bySub={};set.forEach(d=>bySub[d.subvar]=(bySub[d.subvar]||0)+1);
  const subs=Object.entries(bySub).sort((a,b)=>b[1]-a[1]).slice(0,10);const maxS=subs.length?subs[0][1]:1;
  const seg=document.getElementById('anseg');
  seg.innerHTML=`<div class="mini">`+subs.map(([s,v])=>`<div class="r" style="grid-template-columns:160px 1fr 34px"><div class="nm" title="${s}">${s}</div>
    <div class="bar" data-w="${(v/maxS*100).toFixed(1)}" style="background:var(--gold)"></div><div class="v">${v}</div></div>`).join('')+`</div>`+
    `<p class="hint">${subs.length} subvariável(is) no recorte · ${pct}% do acervo.</p>`;
  requestAnimationFrame(()=>seg.querySelectorAll('.bar').forEach(b=>b.style.width=b.dataset.w+'%'));
}
function buildCrosstab(){
  const mods=modalityList();const tbl=document.getElementById('crosstab');let max=0;const grid={};
  mods.forEach(m=>{grid[m]={};METHODCOLS.forEach(c=>{const n=DATA.filter(d=>inMod(d,m)&&c.test(d)).length;grid[m][c.k]=n;if(n>max)max=n;});});
  let html='<thead><tr><th class="rh">Modalidade \\ Método</th>'+METHODCOLS.map(c=>`<th>${c.k}</th>`).join('')+'</tr></thead><tbody>';
  mods.forEach(m=>{html+=`<tr><th class="rh" style="color:${modColor(m)}">${m}</th>`+METHODCOLS.map(c=>{const n=grid[m][c.k];
    return `<td data-mod="${m}" data-method="${c.k}" data-c="${n}"><div class="cell" data-fill="${n?(0.3+0.7*n/max).toFixed(2):0}" style="background:${n?cssvar('--gold'):'transparent'}">${n||''}</div></td>`;}).join('')+'</tr>';});
  html+='</tbody>';tbl.innerHTML=html;
  tbl.querySelectorAll('td').forEach(td=>{if(+td.dataset.c>0)td.onclick=()=>{state.analysis='';state.modality=td.dataset.mod;state.methodcol=td.dataset.method;syncAnbar();applyKPI();render();scrollAcervo();};});
}
function animCrosstab(){document.querySelectorAll('#crosstab .cell').forEach((c,i)=>{const f=+c.dataset.fill;
  setTimeout(()=>{c.style.opacity=f>0?f:0;c.style.transform='scale(1)';},i*20);});}
function buildUniao(){
  const mm=DATA.filter(d=>modsOf(d).length>=2).sort((a,b)=>modsOf(b).length-modsOf(a).length);
  const mv=DATA.filter(d=>varsOf(d).length>=2).sort((a,b)=>varsOf(b).length-varsOf(a).length);
  const li=(d,tags)=>`<li><b>${d.year} · ${shortAuth(d.authors)}</b> — ${d.title}<div class="tags">${tags}</div></li>`;
  const modTag=m=>`<span class="tag" style="background:${modColor(m)}">${m}</span>`;
  const varTag=v=>`<span class="tag" style="background:${cssvar(TCOLOR[v])}">${v}</span>`;
  document.getElementById('uniao').innerHTML=`<div class="uni">
    <div><h4>+ modalidades (${mm.length})</h4><ol>${mm.length?mm.slice(0,6).map(d=>li(d,modsOf(d).map(modTag).join(''))).join(''):'<li>Nenhum estudo multimodalidade.</li>'}</ol></div>
    <div><h4>+ variáveis (${mv.length})</h4><ol>${mv.length?mv.slice(0,6).map(d=>li(d,varsOf(d).map(varTag).join(''))).join(''):'<li>Nenhum estudo multivariável.</li>'}</ol></div></div>`;
}
function buildDrill(){
  const mods=modalityList();const host=document.getElementById('drill');
  host.innerHTML=mods.map(m=>{
    const set=DATA.filter(d=>inMod(d,m));const bio=set.filter(d=>d.biomech).length;
    const byVar={};TEMAS.forEach(t=>byVar[t]=0);set.forEach(d=>varsOf(d).forEach(v=>{if(byVar[v]!=null)byVar[v]++;}));
    const totV=Object.values(byVar).reduce((a,b)=>a+b,0)||1;
    const bySub={};set.forEach(d=>bySub[d.subvar]=(bySub[d.subvar]||0)+1);
    const subs=Object.entries(bySub).sort((a,b)=>b[1]-a[1]).slice(0,4);
    const stack=TEMAS.filter(t=>byVar[t]>0).map(t=>`<span data-w="${(byVar[t]/totV*100).toFixed(1)}" style="background:${cssvar(TCOLOR[t])}" title="${t}: ${byVar[t]} (${Math.round(byVar[t]/totV*100)}%)"></span>`).join('');
    return `<div class="drillrow" data-mod="${m}"><div class="h"><span class="mn" style="color:${modColor(m)}">${m}</span>
      <span class="meta">${set.length} estudo(s) · biomecânica <span class="bio">${bio}</span> (${set.length?Math.round(bio/set.length*100):0}%)</span></div>
      <div class="stack">${stack}</div>
      <div class="subtop">`+TEMAS.filter(t=>byVar[t]>0).map(t=>`<span style="color:${cssvar(TCOLOR[t])}">${t} ${Math.round(byVar[t]/totV*100)}%</span>`).join('')+`</div>
      <div class="subtop" style="margin-top:6px">${subs.map(([s,v])=>`<span>${s} · ${v}</span>`).join('')}</div></div>`;
  }).join('');
  host.querySelectorAll('.drillrow').forEach(r=>r.onclick=()=>{state.analysis='';state.methodcol='';state.modality=r.dataset.mod;syncAnbar();applyKPI();render();scrollAcervo();});
}
function animDrill(){document.querySelectorAll('#drill .stack span').forEach(s=>s.style.width=s.dataset.w+'%');}

/* ---------- LINHA DO TEMPO (espaço-temporal) ---------- */
const TL_VIEWS=[
  {k:'modalidade',lab:'Por modalidade',series:()=>modalityList().map(m=>({name:m,color:modColor(m),test:d=>inMod(d,m)}))},
  {k:'variavel',lab:'Por variável',series:()=>TEMAS.map(t=>({name:t,color:cssvar(TCOLOR[t]),test:d=>varsOf(d).includes(t)}))},
  {k:'desenho',lab:'Por delineamento',series:()=>[
    {name:'Observacional',color:cssvar('--t-neuro'),test:d=>['Transversal','Longitudinal'].includes(d.design)},
    {name:'Experimental/ECR',color:cssvar('--t-psico'),test:d=>['Experimental','ECR'].includes(d.design)},
    {name:'Revisão',color:'#b06de0',test:d=>String(d.design).startsWith('Revis')||d.design==='Meta-análise'}]},
  {k:'biopsi',lab:'Biomecânica vs Psicologia',series:()=>[
    {name:'Biomecânica',color:cssvar('--t-neuro'),test:d=>d.biomech},
    {name:'Psicologia',color:cssvar('--t-psico'),test:d=>theme(d.topic)==='Psico'}]},
  {k:'total',lab:'Acumulado total',series:()=>[{name:'Todos os estudos',color:cssvar('--gold'),test:d=>true}]}
];
let TL_ACTIVE='modalidade';
function yearsRange(){const ys=DATA.map(d=>+d.year).filter(Boolean);return [Math.min(...ys),Math.max(...ys)];}
function buildTimeline(){
  const bar=document.getElementById('tlbar');
  bar.innerHTML=TL_VIEWS.map((v,i)=>`<button class="anbtn" data-k="${v.k}" aria-pressed="${i===0}">${v.lab}</button>`).join('');
  bar.querySelectorAll('.anbtn').forEach(b=>b.onclick=()=>{bar.querySelectorAll('.anbtn').forEach(x=>x.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');TL_ACTIVE=b.dataset.k;plotTimeline(b.dataset.k);});
  plotTimeline('modalidade');
}
function plotTimeline(k){
  const view=TL_VIEWS.find(v=>v.k===k)||TL_VIEWS[0];const series=view.series();
  const [y0,y1]=yearsRange();const W=1000,H=380,ML=44,MR=16,MT=18,MB=34;
  const yrs=[];for(let y=y0;y<=y1;y++)yrs.push(y);
  const data=series.map(s=>{let c=0;return yrs.map(y=>{c+=DATA.filter(d=>+d.year===y&&s.test(d)).length;return c;});});
  const maxY=Math.max(1,...data.flat());
  const X=i=>ML+(W-ML-MR)*(yrs.length<=1?0.5:i/(yrs.length-1));
  const Y=v=>H-MB-(H-MT-MB)*(v/maxY);
  let g='';const ticks=4;
  for(let t=0;t<=ticks;t++){const val=Math.round(maxY*t/ticks);const yy=Y(val);
    g+=`<line class="grid" x1="${ML}" y1="${yy}" x2="${W-MR}" y2="${yy}"/><text class="lbl" x="${ML-6}" y="${yy+3}" text-anchor="end">${val}</text>`;}
  const step=Math.max(1,Math.ceil(yrs.length/10));
  yrs.forEach((y,i)=>{if(i%step===0||i===yrs.length-1)g+=`<text class="lbl" x="${X(i)}" y="${H-MB+16}" text-anchor="middle">${y}</text>`;});
  g+=`<line class="axis" x1="${ML}" y1="${H-MB}" x2="${W-MR}" y2="${H-MB}"/><line class="axis" x1="${ML}" y1="${MT}" x2="${ML}" y2="${H-MB}"/>`;
  series.forEach((s,si)=>{
    const pts=data[si].map((v,i)=>`${X(i).toFixed(1)},${Y(v).toFixed(1)}`);
    g+=`<path class="series" data-si="${si}" d="M${pts.join(' L')}" style="stroke:${s.color}"/>`;
    data[si].forEach((v,i)=>{g+=`<circle class="dot" data-si="${si}" cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="2.6" style="fill:${s.color};opacity:0"><title>${s.name} · ${yrs[i]}: ${v}</title></circle>`;});
  });
  document.getElementById('tlsvg').innerHTML=g;
  document.getElementById('tllegend').innerHTML=series.map(s=>`<div class="it"><span class="sw" style="background:${s.color}"></span>${s.name}</div>`).join('');
  document.getElementById('tlhint').textContent=`Contagem acumulada de ${y0} a ${y1} · ${series.length} série(s) · ${DATA.length} estudos.`;
  animTimeline();
}
function animTimeline(){
  document.querySelectorAll('#tlsvg path.series').forEach((p,i)=>{const L=p.getTotalLength();
    p.style.transition='none';p.style.strokeDasharray=L;p.style.strokeDashoffset=L;p.getBoundingClientRect();
    setTimeout(()=>{p.style.transition='stroke-dashoffset 1.2s cubic-bezier(.4,.1,.2,1)';p.style.strokeDashoffset=0;},i*130);});
  document.querySelectorAll('#tlsvg circle.dot').forEach(c=>{const si=+c.dataset.si;c.style.opacity=0;
    setTimeout(()=>{c.style.transition='opacity .4s ease';c.style.opacity=1;},520+si*130);});
}

/* ---------- FICHA (análise completa por artigo) ---------- */
function fichaHTML(d){
  const F=(k,v,full)=>`<div class="f${full?' full':''}"><p class="k">${k}</p><p class="v${(v&&v!=='—'&&v!=='n/d')?'':' mut'}">${v||'—'}</p></div>`;
  const amostra=d.amostra||(d.n?`${d.n} participantes`:'n/d');
  const resumo=d.resumo||d.finding||'—';
  const bio=d.variaveis_biodinamicas||(d.biomech?((d.methods||[]).join(', ')||'—'):'—');
  const ana=d.analise_estatistica||((d.methods||[]).filter(m=>/ANOVA|Regress|SPM|NMF|PCA|Bayes|ROC|SEM|Descritivo/.test(m)).join(', ')||d.stats_approach||'n/d');
  const sint=d.sintese||d.subvar||'—';
  return `<div class="ficha">
    ${F('Modalidade',modsOf(d).join(' · '))}
    ${F('Tipo de estudo · ano',`${d.design} · ${d.year}`)}
    ${F('Amostra',amostra)}
    ${F('Delineamento',`${d.design}${d.design_conf?' ('+d.design_conf+')':''}`)}
    ${F('Análise estatística',ana)}
    ${F('Idioma',LANG[d.idioma]||d.idioma||'—')}
    ${F('Variáveis biodinâmicas',bio,true)}
    ${F('Resumo',resumo,true)}
    ${F('Síntese',sint,true)}
  </div>`;
}
function wireRows(){
  document.querySelectorAll('#rows tr.arow').forEach(tr=>tr.onclick=e=>{
    if(e.target.closest('a'))return;
    const next=tr.nextElementSibling;
    const isOpen=next&&next.classList.contains('detail');
    document.querySelectorAll('#rows tr.detail').forEach(x=>x.remove());
    document.querySelectorAll('#rows tr.arow.open').forEach(x=>x.classList.remove('open'));
    if(isOpen)return;
    const d=DATA.find(x=>x.doi===tr.dataset.doi);if(!d)return;
    tr.classList.add('open');
    const det=document.createElement('tr');det.className='detail';
    det.innerHTML=`<td colspan="9">${fichaHTML(d)}</td>`;tr.after(det);
  });
}

/* ---------- filters wiring from charts ---------- */
function scrollAcervo(){document.getElementById('acervo').scrollIntoView({behavior:'smooth'});}
function syncChips(){document.querySelector('#chips .all').setAttribute('aria-pressed',state.themes.size===0);
  document.querySelectorAll('#chips .chip[data-t]').forEach(x=>x.setAttribute('aria-pressed',state.themes.has(x.dataset.t)));}
function filterToSub(tema,sub){state.themes=new Set([tema]);state.subvar=sub;state.modality='';state.design='';
  document.getElementById('sport').value='';document.getElementById('design').value='';syncChips();render();scrollAcervo();}
function filterToDesign(d){state.design=d;state.subvar='';document.getElementById('design').value=d;render();scrollAcervo();}
function filterToCell(d,tema){state.design=d;state.themes=new Set([tema]);state.subvar='';state.modality='';
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
  document.getElementById('sport').insertAdjacentHTML('beforeend',modalityList().map(s=>`<option>${s}</option>`).join(''));
  const designs=[...new Set(DATA.map(d=>d.design))].filter(d=>d&&d!=='—').sort();
  document.getElementById('design').insertAdjacentHTML('beforeend',designs.map(s=>`<option>${s}</option>`).join(''));
  const langs=[...new Set(DATA.map(d=>d.idioma||'en'))];
  document.getElementById('idioma').insertAdjacentHTML('beforeend',langs.map(l=>`<option value="${l}">${LANG[l]||l}</option>`).join(''));
}
function render(){
  let rows=DATA.filter(d=>{
    if(state.themes.size && !state.themes.has(theme(d.topic)))return false;
    if(state.reviewsOnly && !REVIEW_KINDS.includes(d.design))return false;
    if(state.design && d.design!==state.design)return false;
    if(state.idioma && (d.idioma||'en')!==state.idioma)return false;
    if(state.subvar && d.subvar!==state.subvar)return false;
    if(state.topic && d.topic!==state.topic)return false;
    if(state.psicogroup){const g=PSICO_GROUPS.find(x=>x.key===state.psicogroup);if(g&&!g.topics.includes(d.topic))return false;}
    if(state.analysis){const a=ANALYSES.find(x=>x.k===state.analysis);if(a&&!a.test(d))return false;}
    if(state.modality && !inMod(d,state.modality))return false;
    if(state.methodcol){const c=METHODCOLS.find(x=>x.k===state.methodcol);if(c&&!c.test(d))return false;}
    if(state.q){const s=(d.authors+' '+d.title+' '+d.journal+' '+d.finding+' '+d.doi+' '+d.subvar+' '+(d.methods||[]).join(' ')).toLowerCase();if(!s.includes(state.q))return false;}
    return true;});
  rows.sort((a,b)=> state.sort==='cit'?(num(b.citations)-num(a.citations)):state.sort==='auth'?a.authors.localeCompare(b.authors):(b.year-a.year));
  document.getElementById('rows').innerHTML=rows.map(d=>`<tr class="arow" data-doi="${d.doi}">
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
  wireRows();
  const flt=[state.analysis&&(ANALYSES.find(x=>x.k===state.analysis)||{}).lab,state.reviewsOnly&&'Revisões',state.topic&&(PSUB[state.topic]||state.topic),state.psicogroup&&(PSICO_GROUPS.find(x=>x.key===state.psicogroup)||{}).label,state.modality,state.methodcol,state.subvar,state.design,[...state.themes].join('+')].filter(Boolean).join(' · ');
  document.getElementById('note').textContent=`Exibindo ${rows.length} de ${DATA.length} artigos`+(flt?` · filtro: ${flt}`:'')+` · DOI verificado.`;
}

/* ---------- events ---------- */
document.getElementById('q').oninput=e=>{state.q=e.target.value.toLowerCase().trim();render();};
document.getElementById('sport').onchange=e=>{state.modality=e.target.value;render();};
document.getElementById('design').onchange=e=>{state.design=e.target.value;render();};
document.getElementById('idioma').onchange=e=>{state.idioma=e.target.value;render();};
document.getElementById('sort').onchange=e=>{state.sort=e.target.value;render();};
document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;
  if(k==='citations')state.sort='cit';else if(k==='authors')state.sort='auth';else if(k==='year')state.sort='year';
  document.getElementById('sort').value=state.sort;render();});

/* ---------- init + reveal-on-scroll (real-time plotting) ---------- */
buildStats();buildSeg();buildSport();buildTimeline();buildDesign();buildReviews();buildAnbar();buildCrosstab();buildUniao();buildDrill();applyKPI();buildPsico();buildPrisma();buildMatrix();buildReviewMeta();buildSynth();buildControls();render();
const REVEAL={setores:()=>{animSeg();animSport();},linha:()=>plotTimeline(TL_ACTIVE),tipos:()=>{animDesign();plotReviews(REV_ACTIVE);},analises:()=>{animCrosstab();animDrill();},psico:animPsico,revisao:animMatrix};
const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){
  if(REVEAL[e.target.id]){REVEAL[e.target.id]();}
  e.target.querySelectorAll?e.target.querySelectorAll('.stat b[data-count]').forEach(countUp):0;
  }});},{threshold:.25});
['setores','linha','tipos','analises','psico','revisao'].forEach(id=>io.observe(document.getElementById(id)));
document.querySelectorAll('.stat b[data-count]').forEach(el=>io.observe(el.closest('.stats')||el));
// stats + permanova count-up
const io2=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting){
  e.target.querySelectorAll('b[data-count]').forEach(countUp);}}),{threshold:.3});
io2.observe(document.getElementById('stats'));
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
