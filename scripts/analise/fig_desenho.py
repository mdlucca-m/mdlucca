import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
OUT='/home/user/mdlucca/Artigos/figuras'
plt.rcParams.update({'font.family':'DejaVu Sans'})

fig,ax=plt.subplots(figsize=(15,7.2)); ax.axis('off'); ax.set_xlim(0,100); ax.set_ylim(0,100)

def box(x,y,w,hh,title,sub,fc,tc='#111'):
    b=FancyBboxPatch((x,y),w,hh,boxstyle='round,pad=0.6,rounding_size=2.4',
        linewidth=1.6,edgecolor='#495057',facecolor=fc,mutation_aspect=0.6)
    ax.add_patch(b)
    ax.text(x+w/2,y+hh*0.66,title,ha='center',va='center',fontsize=11.5,fontweight='bold',color=tc)
    ax.text(x+w/2,y+hh*0.28,sub,ha='center',va='center',fontsize=9.2,color='#333')

def arrow(x0,y0,x1,y1):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=18,lw=1.8,color='#868e96'))

# ETAPA 1 — preparação
ax.text(2,95,'ETAPA 1  |  Preparação e avaliação inicial',fontsize=12.5,fontweight='bold',color='#1971c2')
box(1,78,20,11,'Primeiro contato','Reunião com a comissão\ntécnica e a equipe','#e7f5ff')
box(26,78,20,11,'Consentimento','Explicação dos procedimentos\ne assinatura do TCLE','#e7f5ff')
box(51,78,20,11,'Familiarização','Primeira coleta-piloto\ndo BRUMS (virtual)','#e7f5ff')
box(76,78,22,11,'Teste T-car (15/04/2024)','Teste de campo intermitente:\npico de velocidade','#d0ebff')
arrow(21,83.5,26,83.5); arrow(46,83.5,51,83.5); arrow(71,83.5,76,83.5)

# seta descendo
ax.add_patch(FancyArrowPatch((87,78),(87,66),arrowstyle='-|>',mutation_scale=18,lw=1.8,color='#868e96'))

# ETAPA 2 — semana de coletas
ax.text(2,60,'ETAPA 2  |  Última semana de pré-temporada (duas coletas por dia: manhã e fim de dia)',fontsize=12.5,fontweight='bold',color='#e8590c')
days=[('D1  21/04','BASELINE\nsem treino','#ffec99'),
      ('D2','manhã + fim\nHIIT','#ffd8a8'),
      ('D3','manhã + fim','#fff9db'),
      ('D4','manhã + fim\nHIIT','#ffd8a8'),
      ('D5','manhã + fim','#fff9db'),
      ('D6','manhã + fim','#fff9db'),
      ('D7','manhã + fim\nHIIT','#ffd8a8')]
x=1.0; w=12.6; gap=1.35
for i,(t,s,fc) in enumerate(days):
    box(x,42,w,12,t,s,fc)
    if i<len(days)-1: arrow(x+w,48,x+w+gap,48)
    x+=w+gap

ax.text(50,35,'HIIT = treino intervalado de alta intensidade (dias 2, 4 e 7).  '
        'Cada dia gerou um momento PRÉ (manhã) e um momento PÓS (fim do dia).',
        ha='center',fontsize=9.8,color='#495057',style='italic')

# ETAPA 3 — desfechos
ax.text(2,28,'ETAPA 3  |  Desfechos analisados',fontsize=12.5,fontweight='bold',color='#7048e8')
box(1,10,30,13,'Estados de humor (BRUMS)','6 dimensões (+ PTH),\nescores 0–16, Google Forms','#f3f0ff')
box(35,10,30,13,'Aptidão aeróbia (T-car)','Pico de velocidade\ncomo marcador de aptidão','#f3f0ff')
box(69,10,29,13,'Carga interna (HIIT)','Frequência cardíaca\ne percepção de esforço','#f3f0ff')

fig.suptitle('Desenho do estudo: fluxo das etapas, coletas e desfechos',fontsize=15,fontweight='bold',y=0.995)
fig.savefig(f'{OUT}/desenho_estudo.png',dpi=150,bbox_inches='tight',facecolor='white')
print('OK desenho_estudo.png')
