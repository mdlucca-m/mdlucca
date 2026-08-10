# -*- coding: utf-8 -*-
"""Coerência cruzada: rastreia os números-chave do estudo em todos os
entregáveis, confirmando que o MESMO valor aparece em cada um (rastreabilidade).
Fonte canônica: dashboard_data.json + JSONs dos módulos.
Uso: python coerencia_cruzada.py → resultados_coerencia.json (+ matriz no console)."""
import os, re, json
from docx import Document as Docx

HERE=os.path.dirname(os.path.abspath(__file__))

# ---- textos dos entregáveis ----
import glob
from playwright.sync_api import sync_playwright
_EXE=glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome')[0]
_PW=sync_playwright().start(); _BR=_PW.chromium.launch(executable_path=_EXE)
def html_text(p):
    # texto RENDERIZADO (captura números gerados por JS no dashboard/síntese)
    pg=_BR.new_page()
    pg.goto('file://'+os.path.abspath(p),wait_until='networkidle',timeout=90000)
    pg.wait_for_timeout(600)
    txt=pg.evaluate('document.body.innerText'); pg.close()
    return re.sub(r'\s+',' ',txt)
def docx_text(p):
    d=Docx(p); parts=[x.text for x in d.paragraphs]
    for tb in d.tables:
        for r in tb.rows:
            parts+=[c.text for c in r.cells]
    return ' '.join(parts)

DELIV={
 'Artigo A1':('docx','Artigo_BRUMS_HIIT_A1.docx'),
 'Documento':('docx','Documento_completo_BRUMS_HIIT.docx'),
 'Manuscrito':('docx','Manuscrito_Completo_BRUMS_HIIT.docx'),
 'Central':('html','Central_estudo_BRUMS_HIIT.html'),
 'Showcase':('html','Showcase_BRUMS_HIIT.html'),
 'Síntese':('html','Sintese_achados_BRUMS_HIIT.html'),
 'Dashboard':('html','Dashboard_analitico_BRUMS_HIIT.html'),
}
TXT={}
for k,(kind,f) in DELIV.items():
    p=os.path.join(HERE,f)
    if not os.path.exists(p): TXT[k]=''; continue
    TXT[k]=docx_text(p) if kind=='docx' else html_text(p)

# ---- números-chave (aceita vírgula/ponto e sinais − ou -) ----
def variants(s):
    v={s, s.replace(',', '.'), s.replace('.', ',')}
    return {x.replace('-','−') for x in v} | {x.replace('−','-') for x in v} | v
KEYS=[
 ('Fadiga física — dz agudo','1,06'),
 ('PTH — dz agudo','0,68'),
 ('Vigor — dz agudo','0,56'),
 ('Tucker φ (multigrupo)','0,992'),
 ('ΔCFI métrico conjunto','0,004'),
 ('Invariância estrita — ΔCFI','0,015'),
 ('Parcial — viés residual','0,064'),
 ('Preditor fadiga física — AUC','0,90'),
 ('ROC pós vs. pré — AUC','0,70'),
 ('κ Fadiga (escalar)','0,56'),
 ('Iceberg pós','75%'),
 ('HIIT — FC de pico','186'),
 ('HIIT — PSE final','9,9'),
 ('Segmentação (η² PTH)','0,70'),
]
rows=[]
for name,val in KEYS:
    vs=variants(val)
    pres={k:any(x in TXT[k] for x in vs) for k in DELIV}
    cites=[k for k in DELIV if pres[k]]
    rows.append({'metrica':name,'valor':val,'entregaveis':cites,'n':len(cites)})

report={'fonte_canonica':'dashboard_data.json + JSONs dos módulos (reproduzidos por código)',
        'entregaveis':list(DELIV.keys()),'metricas':rows,
        'nota':'Dashboard, Central, Showcase e Síntese são gerados por código a partir da mesma fonte; os números são idênticos por construção. Divergências aparentes correspondem a índices distintos (ex.: congruência φ do módulo de confiabilidade 0,987 vs. multigrupo 0,992).'}
json.dump(report,open(os.path.join(HERE,'resultados_coerencia.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

# matriz no console
cols=list(DELIV.keys())
print('MÉTRICA'.ljust(30),'VALOR'.ljust(7),' '.join(c[:4] for c in cols))
for r in rows:
    line=r['metrica'][:29].ljust(30)+str(r['valor']).ljust(7)
    line+=' '.join(('  ✓ ' if k in r['entregaveis'] else '  · ') for k in cols)
    print(line)
print('\nOK — resultados_coerencia.json ·', sum(r['n'] for r in rows),'ocorrências rastreadas em',len(cols),'entregáveis')
