import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); A=json.load(open('adv.json'))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.edgecolor':'#333','axes.linewidth':1.0,
    'axes.grid':True,'grid.color':'#e6e6e6','grid.linewidth':0.8})
seq=[(1,'baseline')]+sum([[(d,'pre'),(d,'pos')] for d in range(2,8)],[])
x=np.array([d+(-0.2 if m=='pre' else 0.2 if m=='pos' else 0.0) for d,m in seq])
xx=np.linspace(x.min(),x.max(),400)
def sm(k):
    y=np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m in seq])
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85); return s(xx)

fig,ax=plt.subplots(figsize=(13.5,7.4))
series=[('Vigor','Vigor','#0f8b8d'),('Fadiga','Fadiga','#e8590c'),('FadFisica','Fadiga física','#0ca678')]
for k,lab,col in series:
    ax.plot(xx,sm(k),color=col,lw=3,label=lab)
for d in [2,4,7]: ax.axvline(d,color='#ccc',ls='--',lw=1)
# cruzamentos Vigor x Fadiga
vf=A['vf_cross']
for j,c in enumerate(vf):
    ax.plot(c['x'],c['y'],'o',ms=13,mfc='white',mec='#212529',mew=2,zorder=5)
    ax.annotate('cruzamento\ndia %.1f'%c['x'],(c['x'],c['y']),xytext=(c['x'],c['y']+1.6),
        ha='center',fontsize=9.5,fontweight='bold',color='#212529',
        arrowprops=dict(arrowstyle='->',color='#495057',lw=1.2))
ax.set_xlabel('Dia do microciclo'); ax.set_ylabel('Escore (0 a 16)')
ax.set_title('Cruzamentos das variáveis ao longo da semana: quando a fadiga supera o vigor',fontsize=14,fontweight='bold')
ax.legend(fontsize=11,loc='upper center',ncol=3,framealpha=0.9)
ax.text(0.5,-0.15,'A inversão do eixo energia-fadiga (fadiga acima do vigor) marca a transição do perfil de iceberg para a barbatana de tubarão.',
    transform=ax.transAxes,ha='center',fontsize=9.6,style='italic',color='#495057')
fig.savefig(f'{OUT}/cruzamentos_semana.png',dpi=150,bbox_inches='tight',facecolor='white')
print('OK cruzamentos_semana.png')
