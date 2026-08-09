import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from matplotlib.path import Path
import matplotlib.patches as mpatches

C=dict(dark='#16273D',green='#2C7A4B',gray='#5B6B82',blue='#245C8B',teal='#0E8C86',gold='#C7871B',purple='#7A5AA8',
       ink='#16273D',mut='#5B6B82',edge='#AEB9C7',bg='#F7F9FC',card='#FFFFFF')
# header row (triggers/setup) — no number, icon glyph
header=[('▶','Início','',C['dark']),('↻','Cron 06:00','',C['green']),('⚙','Configuração','',C['gray']),('↓','Setup deps','',C['gray'])]
# numbered analysis/export chain
nodes=[('Ingestão','',C['dark']),
('Descritivas','medida',C['blue']),('Confiabilidade','medida',C['blue']),('Correlações','medida',C['blue']),
('Efeito do dia','resposta',C['teal']),('Resposta aguda','resposta',C['teal']),('HIIT × técnico','resposta',C['teal']),('Multivariada','resposta',C['teal']),
('Variância','integração',C['gold']),('Complementares','integração',C['gold']),('Carga interna','FC & PSE',C['teal']),
('Gráficos','',C['purple']),('Excel','exportação',C['gold']),('PDF','exportação',C['gold']),('Publicar HTML','exportação',C['purple']),
('App analista','regenera',C['purple']),('Relatório','',C['dark'])]

PERROW=4; W,H=3.05,1.32; GX,GY=0.55,0.72
fig,ax=plt.subplots(figsize=(15.2,15.8),dpi=135); ax.set_facecolor(C['bg']); fig.patch.set_facecolor(C['bg'])
ax.set_xlim(0,PERROW*(W+GX)+0.3); ax.axis('off')

def cellpos(i):  # serpentine
    r=i//PERROW; cinrow=i%PERROW
    c=cinrow if r%2==0 else (PERROW-1-cinrow)
    x=0.4+c*(W+GX); return x,r,c

# total rows
all_items=header+[(None,)]*0
totrows=1+ (len(nodes)+PERROW-1)//PERROW
TOP=totrows*(H+GY)+1.0
ax.set_ylim(0,TOP)

def ytop(r): return TOP-1.4-r*(H+GY)

def card(x,ytopv,glyph,title,sub,col,numbered=None):
    y=ytopv-H
    box=FancyBboxPatch((x,y),W,H,boxstyle='round,pad=0.02,rounding_size=0.14',
        linewidth=2.2,edgecolor=col,facecolor=C['card']); box.set_zorder(3); ax.add_patch(box)
    cc=Circle((x+0.42,y+H/2),0.28,color=col,zorder=4); ax.add_patch(cc)
    if numbered is not None:
        ax.text(x+0.42,y+H/2,str(numbered),ha='center',va='center',color='white',fontsize=15,fontweight='bold',zorder=5)
    else:
        ax.text(x+0.42,y+H/2,glyph,ha='center',va='center',color='white',fontsize=16,zorder=5)
    ax.text(x+0.86,y+H/2+(0.16 if sub else 0),title,ha='left',va='center',color=C['ink'],fontsize=13.5,fontweight='bold')
    if sub: ax.text(x+0.86,y+H/2-0.24,sub,ha='left',va='center',color=C['mut'],fontsize=10.5)

def harrow(x0,y0,x1,y1):
    a=FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=16,lw=2,color=C['edge'],
        connectionstyle='arc3,rad=0',zorder=2); ax.add_patch(a)
def varrow(x0,y0,x1,y1,rad):
    a=FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=16,lw=2,color=C['edge'],
        connectionstyle=f'arc3,rad={rad}',zorder=2); ax.add_patch(a)

# draw header row (row -1, at very top)
hy=TOP-1.4+ (H+GY)  # place above row 0? Instead treat header as row0 and shift nodes to row1+
# Simpler: header occupies row 0, nodes start at row 1
def ytop_r(r): return TOP-1.4-r*(H+GY)
for i,(g,t,s,col) in enumerate(header):
    x=0.4+i*(W+GX); card(x,ytop_r(0),g,t,s,col,numbered=None)
    if i>0:
        px=0.4+(i-1)*(W+GX); harrow(px+W,ytop_r(0)-H/2,x,ytop_r(0)-H/2)
# connect header end -> node1 (serpentine down): header row is L→R, so ends at col3; node row1 also starts... 
# nodes row starts at r=1; row1 (odd) goes R→L, so node index0 sits at col3 (under Setup deps)
def npos(i):
    r=1+i//PERROW; cinrow=i%PERROW
    c=cinrow if (r%2==0) else (PERROW-1-cinrow)
    x=0.4+c*(W+GX); return x,r,c
# vertical from Setup deps down to Ingestão
x0,_,_=(0.4+3*(W+GX),0,3); 
xi,ri,ci=npos(0)
varrow(x0+W/2,ytop_r(0)-H,xi+W/2,ytop_r(ri),-0.25)
for i,(t,s,col) in enumerate(nodes):
    x,r,c=npos(i); card(x,ytop_r(r),'',t,s,col,numbered=i+1)
    if i>0:
        px,pr,pc=npos(i-1)
        if pr==r:
            if c>pc: harrow(px+W,ytop_r(r)-H/2,x,ytop_r(r)-H/2)
            else: harrow(px,ytop_r(r)-H/2,x+W,ytop_r(r)-H/2)
        else:
            # row change: vertical curve
            varrow(px+W/2,ytop_r(pr)-H,x+W/2,ytop_r(r),0.25 if (pr%2==0) else -0.25)
plt.title('')
ax.text(0.4,TOP-0.5,'PIPELINE AUTOMATIZADO — BRUMS × HIIT (estilo N8N, com Cron)',fontsize=20,fontweight='bold',color=C['ink'],ha='left')
ax.text(0.4,TOP-0.92,'dispara manual ou por agendamento → ingestão → análises → carga interna → gráficos → exportação (Excel/PDF/HTML) → app analista → relatório',
        fontsize=12.5,color=C['mut'],style='italic',ha='left')
fig.savefig('/home/user/mdlucca/HANDEBOL/pipeline/workflow_diagram.png',facecolor=C['bg'],bbox_inches='tight',pad_inches=0.25)
print('diagram written')
