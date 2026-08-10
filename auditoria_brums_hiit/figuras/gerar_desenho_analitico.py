# -*- coding: utf-8 -*-
"""Desenho do estudo ANALÍTICO — visual abstract: desenho + pipeline + achado por etapa."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
P=dict(bg='#f4f7fb',navy='#122438',blue='#245C8B',teal='#0E8C86',gold='#C7871B',red='#C0392B',mut='#5B6B82',vio='#7A5AA8',line='#D7E0EC',ink='#16273D',lite='#eef4fb')
plt.rcParams.update({'font.family':'DejaVu Sans'})
mod=json.load(open('modelagem/resultados_modelagem.json')); adv=json.load(open('analises_avancadas/resultados.json'))
inf=json.load(open('estatistica_inferencial/resultados_inferencia.json')); ex=json.load(open('/tmp/figextra.json'))
SUBS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; SH=['Ten','Dep','Rai','Vig','Fad','Con']

W,H=142,116
fig=plt.figure(figsize=(14.2,11.6),dpi=160); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off'); fig.patch.set_facecolor('white')
def box(x,y,w,h,fc='white',ec=P['line'],lw=1.4,r=1.4,z=2): ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.1,rounding_size={r}',fc=fc,ec=ec,lw=lw,zorder=z))
def txt(x,y,s,size=11,c=P['ink'],w='normal',ha='left',va='center'): ax.text(x,y,s,fontsize=size,color=c,fontweight=w,ha=ha,va=va,zorder=6)
def inset(x,y,w,h):  # main-coords -> figure fraction
    a=fig.add_axes([x/W,y/H,w/W,h/H]); a.set_zorder(4); return a
def clean(a):
    for s in a.spines.values(): s.set_visible(False)
    a.tick_params(length=0,labelsize=6.5,colors=P['mut'])

# ===== header =====
txt(5,111,'DESENHO ANALÍTICO DO ESTUDO',9.5,P['teal'],'bold')
txt(5,106.5,'Humor e carga interna no HIIT — handebol',22,P['navy'],'bold')
txt(5,101.8,'Do desenho experimental à decisão de modelagem, com o achado-chave de cada etapa. 27 atletas · microciclo de 7 dias · atleta como unidade.',11,P['mut'])
ax.plot([5,137],[98.5,98.5],color=P['line'],lw=1.2,zorder=1)

# ===== BAND A: amostra + timeline =====
box(5,80,32,15,fc=P['lite'],ec=P['blue']); txt(8,92,'AMOSTRA',8.5,P['blue'],'bold')
txt(8,88,'27',24,P['blue'],'bold'); txt(19,88.7,'atletas de',10.5,P['ink']); txt(19,86,'handebol de elite',10.5,P['ink'],'bold')
txt(8,82.5,'21–27/abr/2024 · medidas repetidas',8,P['mut'])
txt(41,95.5,'MICROCICLO DE 7 DIAS',8.5,P['navy'],'bold')
days=[('D1','Repouso',0),('D2','HIIT',1),('D3','Téc-tát',0),('D4','HIIT',1),('D5','Téc-tát',0),('D6','Téc-tát',0),('D7','HIIT',1)]
x0=41; bw=13.4; gap=0.7
for i,(dd,lb,h) in enumerate(days):
    x=x0+i*(bw+gap); box(x,80,bw,12,fc='#fbeceb' if h else '#eef2f7',ec=P['red'] if h else P['blue'],lw=1.7,r=1)
    if h: txt(x+bw/2,93.1,'● HIIT',7,P['red'],'bold',ha='center')
    txt(x+bw/2,88.5,dd,12,P['navy'],'bold',ha='center'); txt(x+bw/2,84.7,lb,8,(P['red'] if h else P['blue']),'bold',ha='center')
    ax.add_patch(Circle((x+bw*0.34,81.6),0.5,color=P['navy'],zorder=6)); ax.add_patch(Circle((x+bw*0.66,81.6),0.5,color=P['teal'],zorder=6))
txt(41,77.5,'● pré-treino   ● pós-treino — coletas pareadas (manhã/tarde)',8,P['mut'])

# ===== BAND B: instrumentos + fluxo =====
box(5,58,60,16.5,fc='white',ec=P['teal']); txt(8,72,'INSTRUMENTOS (por coleta)',8.5,P['teal'],'bold')
txt(8,68.5,'BRUMS · 24 itens → 6 subescalas:',8.5,P['ink'],'bold')
txt(8,65.6,'Tensão · Depressão · Raiva · Vigor · Fadiga · Confusão',8,P['mut'])
txt(8,62.6,'PTH (TMD) = Σ negativas − vigor',8.5,P['navy'],'bold')
txt(8,60,'+ fadiga física/mental, estado, PSE; HIIT: FC pré/pós de cada série',8,P['mut'])
# fluxo funnel
txt(70,72,'FLUXO DE DADOS',8.5,P['navy'],'bold')
fun=[('27','atletas',P['blue']),('456','observações',P['teal']),('135','pares pré→pós',P['gold'])]
for i,(n,l,c) in enumerate(fun):
    x=70+i*22.5; box(x,58,20,10,fc=c,ec='none',r=1)
    txt(x+2.3,63.6,n,16,'white','bold'); txt(x+2.3,60.2,l,8,'white')
    if i<2: ax.add_patch(FancyArrowPatch((x+20,63),(x+22.5,63),arrowstyle='-|>',mutation_scale=12,color=P['mut'],lw=2,zorder=7))
txt(70,55.6,'Carga interna: 26 atletas · 520 registros (FC/PSE em 5 fases × 4 sessões)',8,P['mut'])

# ===== BAND C: pipeline analítico (6 etapas com mini-gráfico) =====
txt(5,51.5,'PIPELINE ANALÍTICO — método e achado por etapa',10.5,P['vio'],'bold')
cols=[5,52,99]; rowy=[28.5,4.5]; cw,ch=41,20
stages=[]  # (col,row,badge,title,color,resulttext)
def card(cx,cy,badge,title,c,lines):
    box(cx,cy,cw,ch,fc='white',ec=P['line']); ax.add_patch(Circle((cx+3.4,cy+ch-3.2),1.7,color=c,zorder=6)); txt(cx+3.4,cy+ch-3.2,badge,10,'white','bold',ha='center')
    txt(cx+6.4,cy+ch-3.2,title,10,P['ink'],'bold')
    for i,ln in enumerate(lines): txt(cx+2.2,cy+ch-6.6-i*2.6,ln,8,P['mut'])
# 1 Medida
card(cols[0],rowy[0],'1','Qualidade da medida',P['blue'],['CFA: CFI 0,92','RMSEA 0,055','HTMT máx 0,85','metade com piso'])
a=inset(cols[0]+23,rowy[0]+2.6,15.5,11); clean(a)
fl=[ex['floor'][s] for s in SUBS]; a.barh(range(6),fl,color=[P['red'] if v>=40 else P['teal'] for v in fl]); a.set_yticks(range(6)); a.set_yticklabels(SH); a.invert_yaxis(); a.set_title('% no piso',fontsize=7,color=P['navy'],loc='left',pad=2); a.set_xlim(0,100)
# 2 Resposta aguda
card(cols[1],rowy[0],'2','Resposta aguda',P['red'],['misto + FDR','sobrevivem 4','(fad.fís, PTH,','fadiga, vigor)'])
a=inset(cols[1]+23,rowy[0]+2.6,15.5,11); clean(a)
A=sorted([r for r in inf['A_aguda']],key=lambda r:r['dz'])[-5:]; a.barh(range(5),[r['dz'] for r in A],color=[P['red'] if r['dz']>=0 else P['teal'] for r in A]); a.set_yticks(range(5)); a.set_yticklabels([r['label'][:8] for r in A]); a.set_title('dz agudo',fontsize=7,color=P['navy'],loc='left',pad=2); a.axvline(0,color=P['mut'],lw=.6)
# 3 Acúmulo
card(cols[2],rowy[0],'3','Acúmulo (microciclo)',P['gold'],['fad. física','+0,34/dia','iceberg','71%→33%'])
a=inset(cols[2]+23,rowy[0]+2.6,15.5,11); clean(a)
dd=[ex['iceberg'][str(k)] for k in range(1,8)]; a.plot(range(1,8),dd,'-o',color=P['teal'],lw=2,ms=3); a.fill_between(range(1,8),dd,color=P['teal'],alpha=.15); a.set_title('% iceberg',fontsize=7,color=P['navy'],loc='left',pad=2); a.set_xticks([1,4,7]); a.set_ylim(0,80)
# 4 HIIT
card(cols[0],rowy[1],'4','Efeito do HIIT',P['vio'],['ΔPTH +2,43','(p=0,003)','interação nula','(pós×HIIT 0,91)'])
a=inset(cols[0]+23,rowy[1]+2.6,15.5,11); clean(a)
a.bar([0,1],[0,2.43],color=[P['blue'],P['red']],width=.6); a.set_xticks([0,1]); a.set_xticklabels(['sem','HIIT']); a.set_title('Δ PTH (dia)',fontsize=7,color=P['navy'],loc='left',pad=2)
# 5 Multivariada & Bayes
card(cols[1],rowy[1],'5','Multivariada & Bayes',P['teal'],['Hotelling F=5,6','(vigor+fadiga)','fad.fís BF≈2444','confusão BF≈0,23'])
a=inset(cols[1]+23,rowy[1]+2.6,15.5,11); clean(a)
bf=adv['bayes_JZS_agregado_por_atleta']; bn={'FadFis':'FadFís','esc_vigor':'Vigor','PTH':'PTH','esc_fadiga':'Fadiga','esc_confusao':'Confus'}
sel=[('FadFis'),('PTH'),('esc_fadiga'),('esc_vigor'),('esc_confusao')]; vals=[np.log10(bf[k]['BF10']) for k in sel]
a.barh(range(len(sel)),vals,color=[P['red'] if bf[k]['BF10']>=3 else (P['teal'] if bf[k]['BF10']<=1/3 else P['gold']) for k in sel]); a.set_yticks(range(len(sel))); a.set_yticklabels([bn[k] for k in sel]); a.axvline(0,color=P['mut'],lw=.6); a.set_title('log BF₁₀',fontsize=7,color=P['navy'],loc='left',pad=2)
# 6 Tipologia
card(cols[2],rowy[1],'6','Segmentação (Ward)',P['navy'],['Ward ≈ k-médias','21 / 5 / 1','A06 extremo','(outlier)'])
a=inset(cols[2]+23,rowy[1]+2.6,15.5,11); clean(a)
a.bar([0,1,2],[21,5,1],color=[P['teal'],P['gold'],P['red']],width=.62); a.set_xticks([0,1,2]); a.set_xticklabels(['Resil','Pert','Extr']); a.set_title('n por grupo',fontsize=7,color=P['navy'],loc='left',pad=2)
for i,v in enumerate([21,5,1]): a.text(i,v+0.6,v,ha='center',fontsize=7,color=P['ink'])

fig.savefig('figuras/desenho_analitico.png',facecolor='white'); plt.close(); print('desenho_analitico.png salvo')
