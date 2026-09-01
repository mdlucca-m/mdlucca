# -*- coding: utf-8 -*-
import json, numpy as np, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch, Rectangle, Circle, Wedge
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(DADOS, exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
S=DADOS
B=json.load(open(f"{S}/V2_base.json")); Q=json.load(open(f"{S}/V2_perfis.json"))
A1=json.load(open(f"{S}/V2_a1.json")); A2=json.load(open(f"{S}/V2_a2.json"))
A3=json.load(open(f"{S}/V2_a3.json")); AU=json.load(open(f"{S}/V2_audit.json"))
NORMA=B['NORMA']; CARGA=B['CARGA']
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
V7=SUB+['TMD']; LB={'TMD':'PTH'}
def L(k): return LB.get(k,k)
PERF=Q['NOMES']
CAT=['#2166AC','#1A9070','#E0952B','#C1440E','#8A4FBF','#A31E52']
CV={'Tensão':'#2166AC','Depressão':'#1A9070','Raiva':'#E0952B','Vigor':'#C1440E',
    'Fadiga':'#8A4FBF','Confusão':'#A31E52','TMD':'#2A2F33'}
CPF={PERF[i]:CAT[i] for i in range(6)}
CEST={'Basal':'#6B7378','HIIT':'#C1440E','Amistoso':'#2166AC','Técnico/força':'#1A9070','Técnico':'#1A9070'}
INK='#2A2F33'; MUT='#6B7378'; GRID='#DDE0E2'; SURF='#FFFFFF'
DIV=LinearSegmentedColormap.from_list('div',['#17456F','#2166AC','#8FB4D4','#F2F3F4',
                                             '#E9A98D','#C1440E','#7E2C09'])
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,
  'axes.spines.right':False,'figure.dpi':300,'savefig.dpi':300,'axes.linewidth':1.1,
  'axes.edgecolor':'#8A9299','text.color':INK,'axes.labelcolor':INK,
  'xtick.color':MUT,'ytick.color':MUT,'figure.facecolor':SURF,'axes.facecolor':SURF})
def vg(v,n=1):
    return f"{v:.{n}f}".replace('.',',').replace('-','−')
def pv(p,pref='p '):
    return (pref+'< 0,001' if p<0.001 else pref+'= '+f"{p:.3f}".replace('.',','))
def Tv(k,x):
    m,s=NORMA[k]; return (x-m)/s*10+50
x7=np.arange(1,8)
TIPO={d:CARGA[str(d)]['tipo'] for d in range(1,8)}
FUN={'Basal':'#F0F1F2','HIIT':'#FBEAE3','Amistoso':'#E7EFF7','Técnico/força':'#E4F1EC'}
def marcar(a,alpha=1.0):
    for d in range(1,8): a.axvspan(d-.5,d+.5,color=FUN[TIPO[d]],zorder=0,lw=0,alpha=alpha)
def gy(a):
    a.grid(axis='y',color=GRID,lw=.8,zorder=0); a.set_axisbelow(True)
def gx(a):
    a.grid(axis='x',color=GRID,lw=.8,zorder=0); a.set_axisbelow(True)
def rod(fig,txt,y=-0.03):
    fig.text(.008,y,txt,fontsize=8.6,color=MUT,style='italic',ha='left',va='top')
def salvar(fig,nome):
    fig.savefig(f"{SAIDA}/{nome}.png",bbox_inches='tight',facecolor=SURF); plt.close(fig); print(nome,"ok")
