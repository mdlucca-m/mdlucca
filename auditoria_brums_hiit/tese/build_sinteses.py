# -*- coding: utf-8 -*-
"""Reconstrói os artefatos data-driven (dashboard + página de síntese) a partir
dos templates e do dashboard_data.json / referencias.json.
Uso: python build_sinteses.py  (executar de dentro de tese/)"""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__))
DATA=json.load(open(os.path.join(HERE,'dashboard_data.json'),encoding='utf-8'))
REFS=json.load(open(os.path.join(HERE,'referencias.json'),encoding='utf-8'))
dj=json.dumps(DATA,ensure_ascii=False)
rj=json.dumps(REFS,ensure_ascii=False)

def build(template,out,subs):
    html=open(os.path.join(HERE,template),encoding='utf-8').read()
    for a,b in subs.items(): html=html.replace(a,b)
    open(os.path.join(HERE,out),'w',encoding='utf-8').write(html)
    print(f'{out}: {os.path.getsize(os.path.join(HERE,out))//1024} KB')

import base64
def _b64(p):
    with open(p,'rb') as f: return 'data:image/jpeg;base64,'+base64.b64encode(f.read()).decode()
FIGS={'descr':_b64('/tmp/docimg/descrfig.jpg'),'hiit':_b64('/tmp/docimg/hiitprot.jpg')}
for _k,_f in {'rci':'17_rci.png','tost':'18_tost.png','rede':'19_rede.png','intradia':'20_intradia.png'}.items():
    _p=os.path.join(HERE,'showcase_figs',_f)
    with open(_p,'rb') as _fh: FIGS[_k]='data:image/png;base64,'+base64.b64encode(_fh.read()).decode()
build('dashboard_template.html','Dashboard_analitico_BRUMS_HIIT.html',{'%%DATA%%':dj,'%%FIGS%%':json.dumps(FIGS)})
build('sintese_template.html','Sintese_achados_BRUMS_HIIT.html',{'%%DATA%%':dj,'%%REFS%%':rj})
