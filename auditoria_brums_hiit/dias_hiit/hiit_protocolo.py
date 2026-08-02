# -*- coding: utf-8 -*-
"""Caracterização do protocolo de HIIT (4 × 4 min a 104% da velocidade de pico
de um teste de campo, 3 min de intervalo) a partir da FC por fase e da PSE.
Descreve FC de recuperação, FC média, FC máxima e PSE por série.
Uso: python hiit_protocolo.py → hiit_protocolo_fig.png + resultados_hiit_protocolo.json"""
import os, json, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
fc=pd.read_csv(os.path.join(ROOT,'trimp','fc_fases.csv'))
fc=fc[fc['atleta'].str.startswith('A')].copy()
TEAL='#0e9c90'; CORAL='#c0392b'; INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'; BLUE='#245c8b'; GOLD='#b0790f'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,'axes.labelcolor':INK,
 'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})

FASES=['aquec','se1','se2','se3','se4']; ROT={'aquec':'Aquec.','se1':'Série 1','se2':'Série 2','se3':'Série 3','se4':'Série 4'}
# médias por fase (agrega sessões e atletas)
g=fc.groupby('fase').agg(fc_pre_m=('fc_pre','mean'),fc_pre_sd=('fc_pre','std'),
    fc_pos_m=('fc_pos','mean'),fc_pos_sd=('fc_pos','std'),pse_m=('pse','mean'),pse_sd=('pse','std')).reindex(FASES)

# métricas por atleta (só as 4 séries)
ser=fc[fc.fase.isin(['se1','se2','se3','se4'])]
per=ser.groupby('atleta').agg(fc_max=('fc_pos','max'),fc_media=('fc_pos','mean'),
    fc_recup=('fc_pre','mean'),pse=('pse','max')).reset_index()
resumo={'FC_maxima':[per['fc_max'].mean(),per['fc_max'].std()],
        'FC_media_series':[per['fc_media'].mean(),per['fc_media'].std()],
        'FC_recuperacao':[per['fc_recup'].mean(),per['fc_recup'].std()],
        'PSE_final':[per['pse'].mean(),per['pse'].std()],
        'n_atletas':int(per['atleta'].nunique())}
json.dump({'por_fase':g.round(1).reset_index().to_dict('records'),'resumo':{k:[round(float(v[0]),1),round(float(v[1]),1)] if isinstance(v,list) else v for k,v in resumo.items()},
    'protocolo':'4 × 4 min a 104% da velocidade de pico (teste de campo), 3 min de intervalo'},
    open(os.path.join(HERE,'resultados_hiit_protocolo.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

fig=plt.figure(figsize=(13.2,5.2),dpi=150)
fig.suptitle('Protocolo de HIIT: 4 × 4 min a 104% da velocidade de pico, 3 min de intervalo',x=0.06,ha='left',fontsize=14,fontweight='bold',y=0.98)
gs=fig.add_gridspec(1,3,width_ratios=[1.35,1,1],wspace=0.34,left=0.06,right=0.98,top=0.86,bottom=0.16)

# A — FC por fase: início (recuperação) e fim (pico)
axA=fig.add_subplot(gs[0,0]); x=np.arange(len(FASES))
axA.plot(x,g['fc_pos_m'],'-o',color=CORAL,lw=2.2,ms=7,label='FC ao fim da fase (pico)')
axA.fill_between(x,g['fc_pos_m']-g['fc_pos_sd'],g['fc_pos_m']+g['fc_pos_sd'],color=CORAL,alpha=0.12)
axA.plot(x,g['fc_pre_m'],'-o',color=BLUE,lw=2.2,ms=7,label='FC ao início (após recuperação)')
axA.fill_between(x,g['fc_pre_m']-g['fc_pre_sd'],g['fc_pre_m']+g['fc_pre_sd'],color=BLUE,alpha=0.12)
axA.set_xticks(x); axA.set_xticklabels([ROT[f] for f in FASES],fontsize=9)
axA.set_ylabel('frequência cardíaca (bpm)'); axA.legend(frameon=False,fontsize=8.5,loc='lower right')
axA.set_title('A · FC ao longo das séries',fontsize=11,loc='left')
for s in ['top','right']: axA.spines[s].set_visible(False)

# B — PSE por fase
axB=fig.add_subplot(gs[0,1])
axB.bar(x,g['pse_m'],yerr=g['pse_sd'],color=GOLD,alpha=0.8,edgecolor='white',capsize=3)
axB.set_xticks(x); axB.set_xticklabels([ROT[f] for f in FASES],rotation=30,fontsize=8.5)
axB.set_ylabel('PSE (0–10)'); axB.set_ylim(0,10.5); axB.set_title('B · Esforço percebido (PSE)',fontsize=11,loc='left')
for s in ['top','right']: axB.spines[s].set_visible(False)

# C — resumo de FC/PSE (barras horizontais)
axC=fig.add_subplot(gs[0,2])
labels=['FC máxima','FC média\n(séries)','FC recuperação','PSE final ×18']
vals=[resumo['FC_maxima'][0],resumo['FC_media_series'][0],resumo['FC_recuperacao'][0],resumo['PSE_final'][0]*18]
cols=[CORAL,'#d9744f',BLUE,GOLD]; yy=np.arange(len(labels))
axC.barh(yy,vals,color=cols,alpha=0.85,edgecolor='white')
for i,v in enumerate(vals):
    raw=resumo['PSE_final'][0] if i==3 else v
    axC.text(v+2,i,f'{raw:.1f}'+(' bpm' if i<3 else ''),va='center',fontsize=9,color=INK)
axC.set_yticks(yy); axC.set_yticklabels(labels,fontsize=9); axC.invert_yaxis()
axC.set_xlim(0,210); axC.set_title('C · Resumo da carga interna',fontsize=11,loc='left'); axC.set_xlabel('bpm (PSE reescalada ×18)')
for s in ['top','right']: axC.spines[s].set_visible(False)

fig.text(0.06,0.02,f"n={resumo['n_atletas']} atletas · 4 sessões. FC de recuperação = FC no início de cada série (após 3 min de intervalo); FC máxima/média = pico e média das 4 séries.",fontsize=8.3,color=MUT)
fig.savefig(os.path.join(HERE,'hiit_protocolo_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)
print('FC máx %.0f · média %.0f · recup %.0f · PSE %.1f'%(resumo['FC_maxima'][0],resumo['FC_media_series'][0],resumo['FC_recuperacao'][0],resumo['PSE_final'][0]))
print('salvo hiit_protocolo_fig.png + resultados_hiit_protocolo.json')
