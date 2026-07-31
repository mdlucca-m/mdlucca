import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.dpi':130,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.grid':True,'grid.alpha':.25,'font.family':'DejaVu Sans'})
C={'pre':'#2563eb','pos':'#dc2626','rec':'#059669','ac':'#6366f1'}
OUT='/home/user/mdlucca/analise/figs/'
p='/root/.claude/uploads/9415069c-cc7c-5eeb-b631-02958f369474/dee6d6e0-resultados_handebol.xlsx'
d=pd.read_excel(p,sheet_name='Dados Análise').iloc[:,:13].dropna(subset=['Grupo','Dia'])
d['Momento']=d['Grupo'].map({1:'Pré',2:'Pós',3:'Rec'})
TMD='TMD (Perturbação Total de Humor)'

# FIG1: Iceberg profile Pré vs Pós
subs=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
fig,ax=plt.subplots(figsize=(8,4.6))
pre=[d[d.Momento=='Pré'][s].mean() for s in subs]
pos=[d[d.Momento=='Pós'][s].mean() for s in subs]
x=np.arange(len(subs))
ax.plot(x,pre,'-o',color=C['pre'],lw=2.5,ms=8,label='Pré-treino')
ax.plot(x,pos,'-s',color=C['pos'],lw=2.5,ms=8,label='Pós-treino')
ax.axhline(50,color='gray',ls='--',lw=1,alpha=.6); ax.text(5.05,50,'T=50\n(média)',va='center',fontsize=8,color='gray')
ax.set_xticks(x); ax.set_xticklabels(subs); ax.set_ylabel('Escore T (BRUMS)')
ax.set_title('Perfil de humor "Iceberg" — Pré vs Pós-treino',fontweight='bold')
ax.legend(); plt.tight_layout(); plt.savefig(OUT+'fig1_iceberg.png'); plt.close()

# FIG2: TMD by day + moment
fig,ax=plt.subplots(figsize=(8.5,4.6))
piv=d.pivot_table(index='Dia',columns='Momento',values=TMD,aggfunc='mean')
for m,c in [('Pré',C['pre']),('Pós',C['pos']),('Rec',C['rec'])]:
    if m in piv: ax.plot(piv.index,piv[m],'-o',color=c,lw=2,ms=6,label=m)
ax.set_xlabel('Dia de treino'); ax.set_ylabel('TMD (Perturbação Total de Humor)')
ax.set_title('Evolução do TMD ao longo dos 8 dias',fontweight='bold'); ax.legend()
plt.tight_layout(); plt.savefig(OUT+'fig2_tmd_dia.png'); plt.close()

# FIG3: HIIT FC & PSE progression
h=pd.read_csv('/home/user/mdlucca/analise/hiit_long.csv')
ser=h[h.bloco.str.startswith('Série')]
g=ser.groupby('bloco').agg(fc_pre=('fc_pre','mean'),fc_pos=('fc_pos','mean'),pse=('pse','mean'))
fig,ax1=plt.subplots(figsize=(8.5,4.6))
xb=np.arange(len(g))
ax1.bar(xb-.19,g.fc_pre,.38,color=C['pre'],alpha=.85,label='FC pré-série')
ax1.bar(xb+.19,g.fc_pos,.38,color=C['pos'],alpha=.85,label='FC pós-série')
ax1.set_ylim(90,195); ax1.set_ylabel('Frequência cardíaca (bpm)')
ax1.set_xticks(xb); ax1.set_xticklabels(g.index)
ax2=ax1.twinx(); ax2.plot(xb,g.pse,'-D',color='#111827',lw=2.5,ms=8,label='PSE (0-10)')
ax2.set_ylabel('PSE (Percepção de Esforço)'); ax2.set_ylim(0,11); ax2.grid(False)
ax1.set_title('HIIT — FC e PSE ao longo das 4 séries',fontweight='bold')
l1,la1=ax1.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
ax1.legend(l1+l2,la1+la2,loc='lower right',fontsize=9)
plt.tight_layout(); plt.savefig(OUT+'fig3_hiit.png'); plt.close()

# FIG4: correlations bar with TMD
from scipy import stats
vs=['Fadiga','Depressão','Vigor','Raiva','Confusão','Fadiga_Mental','Fadiga_Física','Tensão']
rs=[stats.spearmanr(d[v],d[TMD])[0] for v in vs]
order=np.argsort(rs)
fig,ax=plt.subplots(figsize=(7.5,4.4))
cols=[('#059669' if r<0 else '#dc2626') for r in np.array(rs)[order]]
ax.barh(np.array(vs)[order],np.array(rs)[order],color=cols,alpha=.85)
ax.axvline(0,color='k',lw=.8); ax.set_xlabel('Correlação de Spearman com o TMD')
ax.set_title('O que mais move a perturbação de humor (TMD)',fontweight='bold')
plt.tight_layout(); plt.savefig(OUT+'fig4_corr.png'); plt.close()
print('figuras geradas')
