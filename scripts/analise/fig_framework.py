import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
OUT='/home/user/mdlucca/Artigos/figuras'
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,ax=plt.subplots(figsize=(14,8)); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100)

def box(x,y,w,hh,title,sub,fc,ec='#495057',ts=12):
    ax.add_patch(FancyBboxPatch((x,y),w,hh,boxstyle='round,pad=0.6,rounding_size=2.6',lw=1.8,edgecolor=ec,facecolor=fc,mutation_aspect=0.7))
    ax.text(x+w/2,y+hh*0.63,title,ha='center',va='center',fontsize=ts,fontweight='bold',color='#111')
    ax.text(x+w/2,y+hh*0.26,sub,ha='center',va='center',fontsize=9.4,color='#333')
def arrow(x0,y0,x1,y1,c='#495057',st='-|>',lw=2.0):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle=st,mutation_scale=20,lw=lw,color=c))

# ENTRADAS (esquerda)
box(1,64,27,16,'Aptidão aeróbia','Pico de velocidade no T-car\n(capacidade e potência aeróbia)','#d0ebff','#1971c2',12.5)
box(1,20,27,16,'Carga de treino','HIIT nos dias 2, 4 e 7\n(frequência cardíaca, PSE)','#ffd8a8','#e8590c',12.5)

# PROCESSO (centro)
box(37,42,26,17,'Estados de humor','BRUMS: 6 dimensões + PTH\n(perfil de iceberg)','#f3f0ff','#7048e8',13)

# SAÍDAS (direita)
box(72,64,27,16,'Nível do humor','Patamar geral na semana\n(H1: relação com a aptidão)','#e6fcf5','#0ca678',12.5)
box(72,20,27,16,'Deterioração do humor','Queda do vigor, acúmulo de\nfadiga (H2: independe da aptidão)','#fff0f6','#c2255c',12.5)

# setas de entrada
arrow(28,72,37,55,'#1971c2')
arrow(28,28,37,46,'#e8590c')
# setas de saída
arrow(63,53,72,72,'#0ca678')
arrow(63,48,72,28,'#c2255c')

# hipóteses
ax.text(50,12,'Hipótese central: a aptidão aeróbia define o PATAMAR do humor (nível), '
        'mas não a INCLINAÇÃO da resposta (deterioração) a uma semana de cargas elevadas.',
        ha='center',fontsize=10.6,style='italic',color='#212529',
        bbox=dict(boxstyle='round,pad=0.5',fc='#f8f9fa',ec='#ced4da'))
ax.text(14,86,'ENTRADAS',ha='center',fontsize=11,fontweight='bold',color='#868e96')
ax.text(50,86,'CONSTRUTO MONITORADO',ha='center',fontsize=11,fontweight='bold',color='#868e96')
ax.text(85,86,'DESFECHOS',ha='center',fontsize=11,fontweight='bold',color='#868e96')

fig.suptitle('Modelo conceitual (framework): aptidão, carga de treino e resposta do humor',fontsize=15,fontweight='bold',y=0.98)
fig.savefig(f'{OUT}/framework.png',dpi=150,bbox_inches='tight',facecolor='white')
print('OK framework.png')
