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

build('dashboard_template.html','Dashboard_analitico_BRUMS_HIIT.html',{'%%DATA%%':dj})
build('sintese_template.html','Sintese_achados_BRUMS_HIIT.html',{'%%DATA%%':dj,'%%REFS%%':rj})
