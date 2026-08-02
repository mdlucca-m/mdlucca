# -*- coding: utf-8 -*-
"""Renderiza os dashboards/KPIs/gráficos/analíticos em altíssima resolução (4K,
3840×2160) e em 3D. Gera:
  - Dashboard_4K.png        painel executivo 4K (KPIs + gráficos)
  - Graficos_3D_4K.png      painel de gráficos 3D reais (barras 3D, dispersão 3D
                            do mapa 4D, superfície da trajetória)
  - BRUMS_HIIT_4K_3D.pdf    os dois painéis num PDF
Fonte: tese/dashboard_data.json (reproduzível). Uso: python build_4k_3d.py"""
import os, json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import cm
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(ROOT, 'tese', 'dashboard_data.json'), encoding='utf-8'))
V = D['viz']

# palette (dark premium)
BG='#0b1220'; CARD='#141f34'; LINE='#243449'; INK='#eaf0f9'; MUT='#9fb0ca'; FAINT='#67789a'
TEAL='#2fd0c0'; CORAL='#ff8080'; GOLD='#f2bd52'; BLUE='#54a8e6'; VIOLET='#b394ff'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,
 'axes.labelcolor':MUT,'xtick.color':MUT,'ytick.color':MUT,'axes.facecolor':CARD,
 'figure.facecolor':BG,'savefig.facecolor':BG})

DPI=200  # 19.2x10.8in * 200 = 3840x2160

def card(ax):
    ax.set_facecolor(CARD)
    for s in ax.spines.values(): s.set_color(LINE)

# ============================ DASHBOARD 4K ============================
def dashboard():
    fig=plt.figure(figsize=(19.2,10.8),dpi=DPI)
    gs=GridSpec(3,4,figure=fig,height_ratios=[0.62,1,1],hspace=0.42,wspace=0.22,
                left=0.035,right=0.975,top=0.9,bottom=0.06)
    fig.text(0.035,0.955,'BRUMS × HIIT — Dashboard analítico',fontsize=30,fontweight='bold',color=INK)
    fig.text(0.035,0.918,'Monitoramento do humor e da carga em 27 atletas de handebol · microciclo de 7 dias · 456 observações',
             fontsize=14,color=MUT)

    A={r['var']:r for r in D['inf']['A_aguda']}
    rocm={r['var']:r for r in D['roc']['pre_vs_pos']}
    pv=D['pv']['perfil']
    kpis=[('dz fadiga física',f"{A['FadFis']['dz']:.2f}".replace('.',','),CORAL,'efeito grande'),
          ('AUC diagnóstica',f"{rocm['FadFis']['AUC']:.2f}".replace('.',','),GOLD,'pós × pré'),
          ('CFI (CFA)',f"{D['adv']['CFA_DWLS']['CFI']:.3f}".replace('.',','),TEAL,'ajuste bom'),
          ('HTMT máx',f"{D['adv']['HTMT_max']:.3f}".replace('.',','),BLUE,'< 0,85'),
          ('Iceberg pós',f"{round(pv['iceberg_pos']*100):.0f}%",VIOLET,'71%→'),
          ('ΔPTH HIIT',"+2,43",GOLD,'nível do dia'),
          ('Tucker φ',f"{D['conf']['B_invariancia']['tucker_phi']:.3f}".replace('.',','),TEAL,'invariância'),
          ('Pares pré/pós','135',BLUE,'n=27')]
    # manual KPI tiles (8 across the top band)
    for i,(lab,val,col,sub) in enumerate(kpis):
        x=0.035+i*0.1185; w=0.108
        axk=fig.add_axes([x,0.70,w,0.135]); axk.axis('off')
        axk.add_patch(plt.Rectangle((0,0),1,1,transform=axk.transAxes,facecolor=CARD,
                     edgecolor=LINE,lw=1.2,zorder=0,clip_on=False))
        axk.text(0.5,0.62,val,ha='center',va='center',fontsize=27,fontweight='bold',color=col,transform=axk.transAxes)
        axk.text(0.5,0.24,lab,ha='center',va='center',fontsize=10.5,color=INK,transform=axk.transAxes)
        axk.text(0.5,0.06,sub,ha='center',va='center',fontsize=8.5,color=FAINT,transform=axk.transAxes)

    # (b) resposta aguda dz (barh + CI)
    ax=fig.add_subplot(gs[1,0:2]); card(ax)
    rows=sorted(D['inf']['A_aguda'],key=lambda r:r['dz'])
    y=np.arange(len(rows))
    for i,r in enumerate(rows):
        c=CORAL if r['dz']>=0 else TEAL
        ax.barh(i,r['dz'],color=c,height=0.6,zorder=3)
        ax.plot([r['ic'][0],r['ic'][1]],[i,i],color=c,lw=2,alpha=.6,zorder=2)
        ax.text(r['dz']+(0.03 if r['dz']>=0 else -0.03),i,f"{r['dz']:.2f}".replace('.',','),
                va='center',ha='left' if r['dz']>=0 else 'right',fontsize=9.5,color=INK)
    ax.set_yticks(y); ax.set_yticklabels([r['label'] for r in rows],fontsize=10)
    ax.axvline(0,color=LINE); ax.set_xlim(-1,1.8)
    ax.set_title('Resposta aguda pré→pós — dz (IC95%)',color=INK,fontsize=13,loc='left',pad=8)
    for s in ['top','right']: ax.spines[s].set_visible(False)

    # (c) trajetória diária
    ax=fig.add_subplot(gs[1,2:4]); card(ax)
    days=sorted(int(d) for d in V['mon']['PTH']); cols={'PTH':VIOLET,'FadFis':CORAL,'Fadiga':GOLD,'Vigor':TEAL}
    labs={'PTH':'PTH','FadFis':'Fad. física','Fadiga':'Fadiga','Vigor':'Vigor'}
    for lo,hi,c in [(0,4,TEAL),(4,7,GOLD),(7,10,CORAL)]: ax.axhspan(lo,hi,color=c,alpha=0.06)
    for d in V['hiit_days']: ax.axvline(d,color=CORAL,ls='--',lw=1,alpha=.4)
    for v in V['mon_vars']:
        ax.plot(days,[V['mon'][v][str(d)] for d in days],'-o',color=cols[v],lw=2.4,ms=6,label=labs[v])
    ax.set_xticks(days); ax.set_xticklabels([f'D{d}'+('▲' if d in V['hiit_days'] else '') for d in days],fontsize=10)
    ax.set_ylim(0,10); ax.legend(loc='lower right',ncol=2,fontsize=9,facecolor=CARD,edgecolor=LINE,labelcolor=INK)
    ax.set_title('Monitoramento diário da carga de humor (D1→D7)',color=INK,fontsize=13,loc='left',pad=8)
    for s in ['top','right']: ax.spines[s].set_visible(False)

    # (d) radar pré×pós
    ax=fig.add_subplot(gs[2,0],projection='polar'); ax.set_facecolor(CARD)
    subs=V['radar']['subs']; N=len(subs); ang=[n/N*2*np.pi for n in range(N)]+[0]
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1); ax.set_ylim(0,V['radar']['max'])
    ax.set_xticks(ang[:-1]); ax.set_xticklabels(subs,fontsize=9,color=MUT)
    ax.set_yticks([2,4,6,8]); ax.set_yticklabels(['2','4','6','8'],fontsize=7,color=FAINT); ax.grid(color=LINE)
    for vals,c,l in [(V['radar']['pre'],TEAL,'pré'),(V['radar']['pos'],CORAL,'pós')]:
        vv=vals+vals[:1]; ax.plot(ang,vv,color=c,lw=2.4,label=l); ax.fill(ang,vv,color=c,alpha=.16)
    ax.legend(loc='upper right',bbox_to_anchor=(1.18,1.14),fontsize=9,facecolor=CARD,edgecolor=LINE,labelcolor=INK)
    ax.set_title('Perfil de humor (radar) — pré vs. pós',color=INK,fontsize=13,pad=16)

    # (e) variância entre × intra (stacked %)
    ax=fig.add_subplot(gs[2,1:3]); card(ax)
    vb=sorted(D['pv']['variabilidade'],key=lambda r:r['pct_entre'])
    y=np.arange(len(vb)); pe=[r['pct_entre'] for r in vb]; pi=[100-p for p in pe]
    ax.barh(y,pe,color=VIOLET,height=0.62,label='entre atletas (traço)',zorder=3)
    ax.barh(y,pi,left=pe,color=GOLD,height=0.62,label='intra atleta (estado)',zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([r['var'] for r in vb],fontsize=10); ax.set_xlim(0,100)
    ax.axvline(50,color=INK,lw=1,alpha=.3,ls=':')
    ax.legend(loc='lower right',fontsize=9,facecolor=CARD,edgecolor=LINE,labelcolor=INK)
    ax.set_title('Decomposição da variância (% entre × intra atleta)',color=INK,fontsize=13,loc='left',pad=8)
    for s in ['top','right']: ax.spines[s].set_visible(False)

    # (f) ROC AUC bars
    ax=fig.add_subplot(gs[2,3]); card(ax)
    rr=sorted(D['roc']['pre_vs_pos'],key=lambda r:r['AUC'])
    y=np.arange(len(rr))
    ax.barh(y,[r['AUC'] for r in rr],color=[CORAL if r['AUC']>=0.7 else BLUE for r in rr],height=0.62,zorder=3)
    ax.axvline(0.5,color=INK,lw=1,alpha=.3,ls=':'); ax.set_xlim(0.5,0.8)
    ax.set_yticks(y); ax.set_yticklabels([r['label'] for r in rr],fontsize=8.5)
    ax.set_title('ROC — AUC (separar pós de pré)',color=INK,fontsize=13,loc='left',pad=8)
    for s in ['top','right']: ax.spines[s].set_visible(False)

    out=os.path.join(HERE,'Dashboard_4K.png')
    fig.savefig(out,dpi=DPI); plt.close(fig)
    print('saved',out)
    return out

# ============================ GRÁFICOS 3D 4K ============================
def graficos_3d():
    fig=plt.figure(figsize=(19.2,10.8),dpi=DPI)
    fig.text(0.035,0.955,'BRUMS × HIIT — Analíticos em 3D',fontsize=30,fontweight='bold',color=INK)
    fig.text(0.035,0.918,'Barras 3D da resposta aguda · dispersão 3D do mapa 4D · superfície 3D da trajetória semanal',
             fontsize=14,color=MUT)
    POS=[[0.005,0.04,0.33,0.86],[0.345,0.04,0.31,0.86],[0.665,0.04,0.33,0.86]]

    # (A) 3D bars: dz por variável
    ax=fig.add_axes(POS[0],projection='3d'); ax.set_facecolor(CARD)
    rows=sorted(D['inf']['A_aguda'],key=lambda r:r['dz'])
    n=len(rows); xs=np.arange(n); dz=[r['dz'] for r in rows]
    cols=[CORAL if v>=0 else TEAL for v in dz]
    ax.bar3d(xs,np.zeros(n),np.zeros(n),0.6,0.6,dz,color=cols,shade=True,edgecolor=BG,linewidth=0.3)
    ax.set_xticks(xs+0.3); ax.set_xticklabels([r['label'] for r in rows],rotation=55,ha='right',fontsize=8,color=MUT)
    ax.set_zlabel('dz (pré→pós)',color=MUT,fontsize=10); ax.set_yticks([])
    ax.set_title('A · Resposta aguda (barras 3D)',color=INK,fontsize=13,pad=2)
    _style3d(ax)

    # (B) 3D scatter: mapa 4D (x=dz, y=slope, z=%entre, cor=%pos, tamanho=|dz|)
    ax=fig.add_axes(POS[1],projection='3d'); ax.set_facecolor(CARD)
    B=D['viz']['bubble']
    x=[b['dz'] for b in B]; y=[b['slope'] for b in B]; z=[b['entre'] for b in B]; g=[b['pos'] for b in B]
    sizes=[400+abs(b['dz'])*900 for b in B]
    sc=ax.scatter(x,y,z,c=g,cmap='RdYlGn_r',s=sizes,depthshade=True,edgecolor=INK,linewidth=0.6,vmin=20,vmax=95)
    short={'Fadiga física':'Fad.fís.','Fadiga mental':'Fad.men.','PTH (TMD)':'PTH','Fadiga':'Fadiga','Vigor':'Vigor'}
    for b in B: ax.text(b['dz'],b['slope'],b['entre']+3,short.get(b['var'],b['var']),fontsize=8.5,color=INK)
    ax.set_xlabel('resposta dz',color=MUT,fontsize=10); ax.set_ylabel('acúmulo/dia',color=MUT,fontsize=10)
    ax.set_zlabel('% entre atletas',color=MUT,fontsize=10)
    cb=fig.colorbar(sc,ax=ax,shrink=0.5,pad=0.02); cb.set_label('% atletas que acumulam',color=MUT,fontsize=9)
    cb.ax.tick_params(colors=MUT); cb.outline.set_edgecolor(LINE)
    ax.set_title('B · Mapa 4D (dispersão 3D + cor)',color=INK,fontsize=13,pad=2)
    _style3d(ax)

    # (C) 3D surface: trajetória (variáveis × dias)
    ax=fig.add_axes(POS[2],projection='3d'); ax.set_facecolor(CARD)
    mv=V['mon_vars']; days=sorted(int(d) for d in V['mon']['PTH'])
    Z=np.array([[V['mon'][v][str(d)] for d in days] for v in mv])
    Xd,Yv=np.meshgrid(days,np.arange(len(mv)))
    surf=ax.plot_surface(Xd,Yv,Z,cmap='viridis',edgecolor=BG,linewidth=0.4,antialiased=True,alpha=0.95)
    labs={'PTH':'PTH','FadFis':'Fad.fís.','Fadiga':'Fadiga','Vigor':'Vigor'}
    ax.set_yticks(np.arange(len(mv))); ax.set_yticklabels([labs[v] for v in mv],fontsize=8,color=MUT)
    ax.set_xticks(days); ax.set_xticklabels([f'D{d}' for d in days],fontsize=8,color=MUT)
    ax.set_zlabel('escore (0–10)',color=MUT,fontsize=10)
    cb=fig.colorbar(surf,ax=ax,shrink=0.5,pad=0.02); cb.ax.tick_params(colors=MUT); cb.outline.set_edgecolor(LINE)
    ax.set_title('C · Trajetória semanal (superfície 3D)',color=INK,fontsize=13,pad=2)
    _style3d(ax)

    out=os.path.join(HERE,'Graficos_3D_4K.png')
    fig.savefig(out,dpi=DPI); plt.close(fig)
    print('saved',out)
    return out

def _style3d(ax):
    ax.xaxis.set_pane_color((0.08,0.12,0.20,1.0))
    ax.yaxis.set_pane_color((0.08,0.12,0.20,1.0))
    ax.zaxis.set_pane_color((0.08,0.12,0.20,1.0))
    for a in (ax.xaxis,ax.yaxis,ax.zaxis):
        a._axinfo['grid']['color']=LINE; a._axinfo['grid']['linewidth']=0.5
    ax.tick_params(colors=MUT)
    ax.view_init(elev=22,azim=-58)

if __name__=='__main__':
    p1=dashboard(); p2=graficos_3d()
    # combine into PDF
    ims=[Image.open(p1).convert('RGB'),Image.open(p2).convert('RGB')]
    pdf=os.path.join(HERE,'BRUMS_HIIT_4K_3D.pdf')
    ims[0].save(pdf,save_all=True,append_images=ims[1:])
    print('saved',pdf,'·',os.path.getsize(pdf)//1024,'KB')
