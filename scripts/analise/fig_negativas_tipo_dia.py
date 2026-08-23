# -*- coding: utf-8 -*-
# Figura: comportamento das dimensoes negativas do humor por TIPO DE DIA (HIIT / Amistoso / Outro).
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Patch
h=pd.read_csv('humor_anon.csv')
R=json.load(open('negativas_tipo_dia.json'))
TIPO={1:'Outro',2:'HIIT',3:'Amistoso',4:'HIIT',5:'Amistoso',6:'Outro',7:'HIIT'}
NEG=['Tensao','Depressao','Raiva','Confusao']; LAB={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
COLt={'Outro':'#868e96','HIIT':'#e8590c','Amistoso':'#1971c2'}
ad=h.groupby(['ID','dia'])[NEG].mean().reset_index(); ad['tipo']=ad['dia'].map(TIPO)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(14,9),dpi=200)
gs=fig.add_gridspec(2,2,hspace=0.34,wspace=0.24,height_ratios=[1,1])

# A: media por tipo (barras agrupadas) com EP
axA=fig.add_subplot(gs[0,0]); order=['Outro','HIIT','Amistoso']; x=np.arange(len(NEG)); w=0.26
for i,t in enumerate(order):
    means=[ad[ad.tipo==t][k].mean() for k in NEG]; sems=[ad[ad.tipo==t][k].sem() for k in NEG]
    axA.bar(x+(i-1)*w,means,w,yerr=sems,capsize=3,color=COLt[t],alpha=.9,label=t,error_kw=dict(lw=1,ecolor='#444'))
axA.set_xticks(x); axA.set_xticklabels([LAB[k] for k in NEG]); axA.set_ylabel('Escore médio (± EP)')
axA.set_title('(A) Dimensões negativas por tipo de dia',fontweight='bold',loc='left',fontsize=12.5)
axA.legend(frameon=False,fontsize=10,ncol=3,loc='upper right')

# B: Amistoso vs HIIT meio-de-semana (dz + significancia)
axB=fig.add_subplot(gs[0,1]); dzs=[R['midweek'][k]['dz'] for k in NEG]; ps=[R['midweek'][k]['p'] for k in NEG]
cols=['#2f9e44' if p<0.05 else '#adb5bd' for p in ps]; y=np.arange(len(NEG))[::-1]
axB.barh(y,dzs,color=cols,height=.6,alpha=.92)
for yi,k,dz,p in zip(y,NEG,dzs,ps):
    star=' *' if p<0.05 else ''
    axB.text(0.03,yi,f'dz {dz:+.2f} · p={p:.3f}{star}',va='center',ha='left',fontsize=9.5,fontweight='bold',color='#212529')
axB.axvline(0,color='#adb5bd',lw=1); axB.set_yticks(y); axB.set_yticklabels([LAB[k] for k in NEG])
axB.set_xlabel('dz (Amistoso − HIIT) · < 0 = menor no dia de jogo'); axB.set_xlim(-0.75,0.55)
axB.set_title('(B) Amistoso (D3,D5) vs HIIT meio-de-semana (D2,D4)\ncontrolado pela posição na semana',fontweight='bold',loc='left',fontsize=12)

# C: efeito agudo pre->pos por tipo
axC=fig.add_subplot(gs[1,0]); hh=[R['acute'][k]['HIIT'] for k in NEG]; aa=[R['acute'][k]['Amistoso'] for k in NEG]
axC.bar(x-0.16,hh,0.32,color=COLt['HIIT'],alpha=.9,label='HIIT'); axC.bar(x+0.16,aa,0.32,color=COLt['Amistoso'],alpha=.9,label='Amistoso')
axC.axhline(0,color='#adb5bd',lw=1); axC.set_xticks(x); axC.set_xticklabels([LAB[k] for k in NEG])
axC.set_ylabel('Δ pré→pós (intradia)'); axC.legend(frameon=False,fontsize=10)
axC.set_title('(C) Resposta aguda (pré→pós) por tipo de dia',fontweight='bold',loc='left',fontsize=11.5)

# D: trajetoria semanal das negativas com faixas de tipo de dia
axD=fig.add_subplot(gs[1,1]); dm=ad.groupby('dia')[NEG].mean(); days=np.arange(1,8)
COLd={'Tensao':'#4d9de0','Depressao':'#c56bd6','Raiva':'#e0525b','Confusao':'#f0a848'}
for d in days:
    t=TIPO[d]
    if t!='Outro': axD.axvspan(d-.35,d+.35,color=COLt[t],alpha=.10,zorder=0)
for k in NEG:
    axD.plot(days,dm[k].values,'-o',color=COLd[k],lw=2.4,ms=5,label=LAB[k])
axD.set_xticks(days); axD.set_xlabel('Dia do microciclo'); axD.set_ylabel('Escore médio')
axD.legend(frameon=False,fontsize=9.5,ncol=2)
axD.set_title('(D) Trajetória semanal (faixa laranja = HIIT · azul = jogo)',fontweight='bold',loc='left',fontsize=11)
axD.text(3,axD.get_ylim()[1]*0.96,'jogo',color=COLt['Amistoso'],fontsize=8,ha='center'); axD.text(5,axD.get_ylim()[1]*0.96,'jogo',color=COLt['Amistoso'],fontsize=8,ha='center')

fig.suptitle('Dimensões negativas do humor são sensíveis ao TIPO de estímulo: menores no jogo amistoso, maiores no HIIT',
             fontweight='bold',fontsize=13.5,y=0.995)
fig.savefig('/home/user/mdlucca/Artigos/figuras/negativas_tipo_dia.png',bbox_inches='tight',facecolor='white')
import os; os.makedirs('/home/user/mdlucca/Artigos/figuras/paper1',exist_ok=True)
fig.savefig('/home/user/mdlucca/Artigos/figuras/paper1/negativas_tipo_dia.png',bbox_inches='tight',facecolor='white')
print('[figura salva: negativas_tipo_dia.png]')
