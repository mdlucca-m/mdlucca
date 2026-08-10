# -*- coding: utf-8 -*-
"""Painel de monitoramento e visualizações (gauge · radar · monitoramento · bolhas 4D)
para a Central e o Documento. Reproduz os quatro gráficos da aba "Monitoramento" do
dashboard, como figura estática. Fonte: dashboard_data.json (bloco viz), computado de
base_modelagem.csv.
Uso: python monitoramento_viz.py  (executar de dentro de tese/figuras/)"""
import json, os, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
from matplotlib.gridspec import GridSpec

HERE=os.path.dirname(os.path.abspath(__file__))
D=json.load(open(os.path.join(HERE,'..','dashboard_data.json'),encoding='utf-8'))
V=D['viz']

TEAL='#0e9c90'; CORAL='#c0392b'; GOLD='#b0790f'; BLUE='#245c8b'; VIOLET='#7a4fb0'
FAINT='#8595ad'; INK='#16273d'; LINE='#d6deea'
CMAP={'teal':TEAL,'coral':CORAL,'gold':GOLD,'blue':BLUE,'violet':VIOLET,'faint':FAINT}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':INK,
 'axes.edgecolor':LINE,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})

fig=plt.figure(figsize=(13.2,10.4),dpi=150)
fig.patch.set_facecolor('white')
gs=GridSpec(2,2,figure=fig,hspace=0.32,wspace=0.22,left=0.06,right=0.97,top=0.9,bottom=0.07)

# ---------------- A. GAUGES ----------------
axg=fig.add_subplot(gs[0,0]); axg.set_xlim(0,4); axg.set_ylim(-0.15,1.35); axg.axis('off')
axg.set_title('A · Medidores dos indicadores-chave',loc='left',fontweight='bold',fontsize=12,color=INK)
def draw_gauge(ax,cx,g):
    R=0.42; cy=0.28
    a0,a1=200,-20  # degrees, left-to-right sweep (>180°)
    def T(v):
        t=(v-g['min'])/(g['max']-g['min'] or 1); t=min(1,max(0,t))
        return a0+t*(a1-a0)
    for z in g['zones']:
        ax.add_patch(Wedge((cx,cy),R,T(z[1]),T(z[0]),width=R*0.34,facecolor=CMAP[z[2]],alpha=0.9,edgecolor='none'))
    # needle
    ang=np.radians(T(min(g['max'],max(g['min'],g['v']))))
    ax.plot([cx,cx+np.cos(ang)*R*0.82],[cy,cy+np.sin(ang)*R*0.82],color=INK,lw=2.2,solid_capstyle='round')
    ax.add_patch(Circle((cx,cy),0.022,color=INK,zorder=5))
    disp={'pct':f"{g['v']:.0f}%".replace('.',','),'auc':f"{g['v']:.2f}".replace('.',','),
          'd3':f"{g['v']:.3f}".replace('.',','),'d':f"{g['v']:.2f}".replace('.',',')}[g['fmt']]
    ax.text(cx,cy+R*0.62,disp,ha='center',va='center',fontsize=16,fontweight='bold',color=INK)
    ax.text(cx,cy-0.16,g['label'],ha='center',va='center',fontsize=8.6,fontweight='bold',color=INK)
    SUB={'dz fadiga física':'efeito agudo (Cohen)','AUC diagnóstica':'pós vs. pré','perfil iceberg (pós)':'vigor no topo','HTMT máximo':'fatores < 0,85'}
    ax.text(cx,cy-0.29,SUB.get(g['label'],g['sub']),ha='center',va='center',fontsize=7.2,color=FAINT)
for i,g in enumerate(V['gauges']): draw_gauge(axg,i+0.5,g)

# ---------------- B. RADAR ----------------
axr=fig.add_subplot(gs[0,1],projection='polar')
subs=V['radar']['subs']; N=len(subs); mx=V['radar']['max']
ang=[n/N*2*np.pi for n in range(N)]; ang+=ang[:1]
axr.set_theta_offset(np.pi/2); axr.set_theta_direction(-1)
axr.set_ylim(0,mx); axr.set_xticks(ang[:-1]); axr.set_xticklabels(subs,fontsize=9.5)
axr.set_yticks([2,4,6,8]); axr.set_yticklabels(['2','4','6','8'],fontsize=7,color=FAINT)
axr.grid(color=LINE); axr.spines['polar'].set_color(LINE)
for vals,col,lab in [(V['radar']['pre'],TEAL,'pré'),(V['radar']['pos'],CORAL,'pós')]:
    v=vals+vals[:1]
    axr.plot(ang,v,color=col,lw=2,label=lab); axr.fill(ang,v,color=col,alpha=0.15)
axr.set_title('B · Perfil de humor (radar) — pré vs. pós',loc='left',fontweight='bold',fontsize=12,color=INK,pad=18)
axr.legend(loc='upper right',bbox_to_anchor=(1.14,1.14),fontsize=9,frameon=False)

# ---------------- C. MONITORAMENTO ----------------
axm=fig.add_subplot(gs[1,0])
days=sorted(int(d) for d in V['mon']['PTH'].keys())
cols={'PTH':VIOLET,'FadFis':CORAL,'Fadiga':GOLD,'Vigor':TEAL}
labs={'PTH':'PTH','FadFis':'Fad. física','Fadiga':'Fadiga','Vigor':'Vigor'}
for lo,hi,c in [(0,4,TEAL),(4,7,GOLD),(7,10,CORAL)]:
    axm.axhspan(lo,hi,color=c,alpha=0.08,zorder=0)
for d in V['hiit_days']:
    if d in days: axm.axvline(d,color=CORAL,ls='--',lw=1,alpha=0.35,zorder=1)
for v in V['mon_vars']:
    y=[V['mon'][v][str(d)] for d in days]
    axm.plot(days,y,'-o',color=cols[v],lw=2,ms=4.5,label=labs[v],zorder=3)
axm.set_xlim(days[0]-0.2,days[-1]+0.2); axm.set_ylim(0,10)
axm.set_xticks(days); axm.set_xticklabels([f'D{d}'+('▲' if d in V['hiit_days'] else '') for d in days],fontsize=9)
axm.set_ylabel('escore (0–10)',fontsize=9.5)
axm.set_title('C · Monitoramento diário da carga de humor (D1→D7)',loc='left',fontweight='bold',fontsize=12,color=INK)
axm.legend(loc='lower right',fontsize=8.5,ncol=2,frameon=True,framealpha=0.9)
for sp in ['top','right']: axm.spines[sp].set_visible(False)
axm.grid(axis='y',color=LINE,alpha=0.6)

# ---------------- D. BOLHAS 4D ----------------
axb=fig.add_subplot(gs[1,1])
B=V['bubble']
xs=[b['dz'] for b in B]; ys=[b['slope'] for b in B]; ss=[b['entre'] for b in B]; gsz=[b['pos'] for b in B]
smx=max(ss)
sizes=[300+ (s/smx)*2600 for s in ss]
# two-hue diverging teal->coral by pos%
def mix(t):
    a=np.array([14,156,144]); b=np.array([192,57,43]); c=(a+(b-a)*t).astype(int); return '#%02x%02x%02x'%tuple(c)
gmn,gmx=min(gsz),max(gsz)
colors=[mix((g-gmn)/(gmx-gmn or 1)) for g in gsz]
axb.axhline(0,color=LINE,lw=1,zorder=0); axb.axvline(0,color=LINE,lw=1,zorder=0)
axb.scatter(xs,ys,s=sizes,c=colors,alpha=0.55,edgecolors=colors,linewidths=1.5,zorder=2)
short={'Fadiga física':'Fad.fís.','Fadiga mental':'Fad.men.','PTH (TMD)':'PTH','Fadiga':'Fadiga','Vigor':'Vigor'}
for b,px,py,sz in zip(B,xs,ys,sizes):
    r=np.sqrt(sz)/1000
    axb.annotate(short.get(b['var'],b['var']),(px,py),textcoords='offset points',xytext=(0,11+ r*8),
                 ha='center',fontsize=9,fontweight='bold',color=INK)
axb.set_xlabel('resposta aguda (dz pré→pós) →',fontsize=9.5)
axb.set_ylabel('acúmulo (inclinação/dia) →',fontsize=9.5)
axb.set_title('D · Mapa 4D — resposta × acúmulo × individualidade × consenso',loc='left',fontweight='bold',fontsize=11.5,color=INK)
axb.set_xlim(-0.9,1.35); axb.set_ylim(-0.42,0.72)
for sp in ['top','right']: axb.spines[sp].set_visible(False)
axb.grid(color=LINE,alpha=0.5)
# colour + size legend note
axb.text(0.02,0.02,'tamanho = % variância entre atletas · cor = % de atletas que acumulam (verde→coral)',
         transform=axb.transAxes,fontsize=7.6,color=FAINT,va='bottom')

fig.suptitle('Monitoramento e visualizações — BRUMS × HIIT',x=0.06,ha='left',fontsize=15,fontweight='bold',color=INK,y=0.965)
fig.text(0.06,0.925,'Painel visual das três conclusões-âncora: medidores dos indicadores, perfil iceberg (pré vs. pós), '
 'monitoramento diário da carga de humor e o mapa 4D por variável.',ha='left',fontsize=9.5,color=FAINT)

out=os.path.join(HERE,'monitoramento_viz.png')
fig.savefig(out,dpi=150,facecolor='white',bbox_inches='tight')
print('saved',out, os.path.getsize(out)//1024,'KB')
