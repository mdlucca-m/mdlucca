# -*- coding: utf-8 -*-
"""Modelo matemático teórico, R², erro-padrão, bayesiano e multivariada.

Formaliza a resposta de humor ao microciclo como um modelo hierárquico
(mistos), estimado por três vias que convergem:

  · MODELO TEÓRICO: impulso-resposta fitness–fadiga (Banister) → forma
    estimável (modelo linear de efeitos mistos com intercepto por atleta).
  · COEFICIENTE DE DETERMINAÇÃO: R² marginal (efeitos fixos) e condicional
    (fixos + aleatórios) de Nakagawa & Schielzeth — mostra o quanto a
    dimensão individual acrescenta.
  · ERRO-PADRÃO: β, SE, IC95% dos efeitos fixos (MixedLM/statsmodels).
  · BAYESIANO: amostrador de Gibbs (modelo hierárquico gaussiano conjugado)
    → média, SE bayesiano e intervalo de credibilidade 95% (converge com o
    frequentista).
  · MULTIVARIADA: MANOVA (Pillai/Wilks) e PERMANOVA pareada (Anderson, 2001)
    da mudança pré→pós no vetor das seis subescalas.

Autocontido: lê ../modelagem/base_modelagem.csv. Uso: python modelo_teorico.py
Dependências: numpy pandas scipy statsmodels matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.multivariate.manova import MANOVA
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
warnings.filterwarnings('ignore'); RS=np.random.RandomState(7)
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GREEN='#2E8B57',GRID='#E3E9F0')
df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
d=df[df.momento.isin(['pre','pos'])].copy()
d['pos']=(d.momento=='pos').astype(float)
LAB={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Vigor':'Vigor','Fadiga':'Fadiga'}
out={}

# ============ 1. MODELO MISTO: R² (Nakagawa) + erro-padrão ============
def fit_lmm(y):
    m=smf.mixedlm(f"{y} ~ pos + dia + hiit", d, groups=d['atleta'])
    r=m.fit(reml=True)
    b=r.fe_params; se=r.bse_fe; ci=r.conf_int().loc[b.index]
    Xf=r.model.exog @ b.values                     # preditor fixo
    var_f=float(np.var(Xf,ddof=1))
    var_u=float(r.cov_re.iloc[0,0]); var_e=float(r.scale)
    tot=var_f+var_u+var_e
    fixed=[]
    for name in b.index:
        fixed.append(dict(termo=name,beta=round(float(b[name]),3),SE=round(float(se[name]),3),
                          IC=[round(float(ci.loc[name,0]),3),round(float(ci.loc[name,1]),3)],
                          z=round(float(b[name]/se[name]),2),
                          p=round(float(2*(1-stats.norm.cdf(abs(b[name]/se[name])))),4)))
    return dict(R2_marginal=round(var_f/tot,3),R2_condicional=round((var_f+var_u)/tot,3),
                ICC=round(var_u/(var_u+var_e),3),var_entre=round(var_u,2),var_intra=round(var_e,2),
                fixos=fixed), r
LMM={}; FITS={}
for y in ['PTH','FadFis','Vigor','Fadiga']:
    res,r=fit_lmm(y); LMM[y]=dict(label=LAB[y],**res); FITS[y]=r
    print(f"1. [{LAB[y]:14s}] R²m={res['R2_marginal']:.3f} R²c={res['R2_condicional']:.3f} ICC={res['ICC']:.2f} · β(pós)={res['fixos'][1]['beta']} SE={res['fixos'][1]['SE']}")
out['mistos_R2_SE']=LMM

# ============ 2. BAYESIANO: Gibbs (random-intercept) ============
def gibbs(y, n_iter=6000, burn=1500):
    yv=d[y].values.astype(float)
    X=np.column_stack([np.ones(len(d)),d['pos'].values,d['dia'].values,d['hiit'].values])
    g=pd.Categorical(d['atleta']).codes; J=g.max()+1; nk=np.bincount(g)
    p=X.shape[1]
    beta=np.zeros(p); u=np.zeros(J); s2=np.var(yv); t2=s2/2
    XtX=X.T@X
    keep=[]
    for it in range(n_iter):
        # beta | . (prior plano)
        resid=yv-u[g]
        V=np.linalg.inv(XtX/s2 + np.eye(p)*1e-6); m=V@(X.T@resid/s2)
        beta=RS.multivariate_normal(m,V)
        # u_j | .
        r=yv-X@beta
        for j in range(J):
            vj=1/(nk[j]/s2 + 1/t2); mj=vj*(r[g==j].sum()/s2)
            u[j]=RS.normal(mj,np.sqrt(vj))
        # s2 | . (InvGamma)
        e=yv-X@beta-u[g]; a=1e-3+len(yv)/2; bb=1e-3+0.5*(e@e); s2=1/RS.gamma(a,1/bb)
        # t2 | .
        a=1e-3+J/2; bb=1e-3+0.5*(u@u); t2=1/RS.gamma(a,1/bb)
        if it>=burn: keep.append(np.concatenate([beta,[np.sqrt(t2),np.sqrt(s2)]]))
    K=np.array(keep); names=['b0','pos','dia','hiit','tau(entre)','sigma(intra)']
    post={}
    for i,nm in enumerate(names):
        post[nm]=dict(media=round(float(K[:,i].mean()),3),SE_bayes=round(float(K[:,i].std(ddof=1)),3),
                      ICr95=[round(float(np.percentile(K[:,i],2.5)),3),round(float(np.percentile(K[:,i],97.5)),3)])
    post['P(pos>0)']=round(float((K[:,1]>0).mean()),3)
    return post, K[:,1]
BAY={}; post_pth_pos=None
for y in ['PTH','FadFis']:
    post,chain=gibbs(y); BAY[y]=dict(label=LAB[y],posterior=post)
    if y=='PTH': post_pth_pos=chain
    pe=post['pos']; print(f"2. [{LAB[y]:14s}] Bayes β(pós)={pe['media']} SE={pe['SE_bayes']} ICr[{pe['ICr95'][0]};{pe['ICr95'][1]}] P(>0)={post['P(pos>0)']}")
out['bayesiano_gibbs']=BAY

# ============ 3. MULTIVARIADA: MANOVA + PERMANOVA pareada ============
SUBS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
man=MANOVA.from_formula(' + '.join(SUBS)+' ~ momento', data=d)
mt=man.mv_test(); tb=mt.results['momento']['stat']
pillai=float(tb.loc["Pillai's trace",'Value']); wilks=float(tb.loc["Wilks' lambda",'Value'])
Fman=float(tb.loc["Pillai's trace",'F Value']); pman=float(tb.loc["Pillai's trace",'Pr > F'])
# PERMANOVA pareada por atleta (vetores médios pré/pós; z-score)
PRE=d[d.momento=='pre'].groupby('atleta')[SUBS].mean(); POS=d[d.momento=='pos'].groupby('atleta')[SUBS].mean()
ath=PRE.index.intersection(POS.index); PRE=PRE.loc[ath]; POS=POS.loc[ath]
Z=pd.concat([PRE,POS]); Zs=(Z-Z.mean())/Z.std()
A0=Zs.iloc[:len(ath)].values; B0=Zs.iloc[len(ath):].values
# desenho pareado/bloqueado: centra cada atleta (remove a variância ENTRE atletas,
# que é o bloco) antes do pseudo-F — assim o denominador é a variância pareada.
mid=(A0+B0)/2; A=A0-mid; B=B0-mid
def pseudoF(A,B):
    X=np.vstack([A,B]); N=len(X); D2=((X[:,None,:]-X[None,:,:])**2).sum(-1)
    SST=D2.sum()/(2*N)
    def within(G):
        n=len(G); d2=((G[:,None,:]-G[None,:,:])**2).sum(-1); return d2.sum()/(2*n)
    SSW=within(A)+within(B); SSB=SST-SSW
    return (SSB/1)/(SSW/(N-2)), SSB/SST
Fobs,R2perm=pseudoF(A,B)
nperm=9999; cnt=1
for _ in range(nperm):
    sw=RS.rand(len(ath))<0.5
    A2=np.where(sw[:,None],B,A); B2=np.where(sw[:,None],A,B)
    Fp,_=pseudoF(A2,B2)
    if Fp>=Fobs: cnt+=1
pperm=cnt/(nperm+1)
out['multivariada']=dict(
  MANOVA=dict(pillai=round(pillai,3),wilks=round(wilks,3),F=round(Fman,2),p=round(pman,5)),
  PERMANOVA=dict(pseudo_F=round(float(Fobs),2),R2=round(float(R2perm),3),p=round(float(pperm),4),
                 nperm=nperm,permutacao='restrita (troca pré/pós dentro do atleta)'))
print(f"3. MANOVA Pillai={pillai:.3f} F={Fman:.2f} p={pman:.4f} · PERMANOVA pseudo-F={Fobs:.2f} R²={R2perm:.3f} p={pperm:.4f}")

# ============ modelo teórico (texto/equações) ============
out['modelo_teorico']=dict(
  fitness_fadiga="State(t)=p0 + k1·g(t) − k2·h(t); g,h = somas exponenciais das cargas (τ_fitness>τ_fatigue)",
  forma_estimavel="Y_ijt = β0 + β1·Pós + β2·Dia + β3·HIIT + u_i + ε_ijt ; u_i~N(0,τ²), ε~N(0,σ²)",
  ICC="τ²/(τ²+σ²)")

json.dump(out,open(os.path.join(HERE,'resultados_modelo_teorico.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= FIGURA analítica =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(13,9.5),dpi=150)
# A R² marginal vs condicional
ax=axs[0,0]; ys=['PTH','FadFis','Vigor','Fadiga']; yy=np.arange(len(ys))
rm=[LMM[y]['R2_marginal'] for y in ys]; rc=[LMM[y]['R2_condicional'] for y in ys]
ax.barh(yy,rm,color=P['BLUE'],label='R² marginal (efeitos fixos)')
ax.barh(yy,[c-m for c,m in zip(rc,rm)],left=rm,color=P['VIO'],label='+ aleatório (individual)')
ax.set_yticks(yy); ax.set_yticklabels([LAB[y] for y in ys]); ax.set_xlabel('R²'); ax.set_xlim(0,1)
for i,y in enumerate(ys): ax.text(rc[i]+.01,i,f"{rc[i]:.2f}".replace('.',','),va='center',fontsize=8,color=P['NAVY'])
ax.legend(frameon=False,fontsize=8,loc='lower right')
ax.set_title('A · Coeficiente de determinação\nmarginal vs. condicional (Nakagawa)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B coeficientes fixos ± IC (PTH)
ax=axs[0,1]; fx=[f for f in LMM['PTH']['fixos'] if f['termo']!='Intercept']
yy=np.arange(len(fx)); nm={'pos':'Pós (vs pré)','dia':'Dia','hiit':'HIIT'}
for i,f in enumerate(fx):
    ax.plot(f['IC'],[i,i],color=P['BLUE'],lw=2); ax.plot(f['beta'],i,'o',color=P['NAVY'],ms=7)
    ax.text(f['beta'],i-0.22,f"β={f['beta']}  SE={f['SE']}",ha='center',va='top',fontsize=8,color=P['MUT'])
ax.set_ylim(-0.6,len(fx)-0.4)
ax.axvline(0,ls='--',color=P['MUT'],lw=1); ax.set_yticks(yy); ax.set_yticklabels([nm.get(f['termo'],f['termo']) for f in fx])
ax.set_xlabel('coeficiente (unidades de PTH) ± IC95%')
ax.set_title('B · Efeitos fixos e erro-padrão — PTH',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C posterior bayesiano do efeito pós (PTH) + frequentista
ax=axs[1,0]
ax.hist(post_pth_pos,bins=45,color=P['GRID'],edgecolor='white',density=True)
bp=BAY['PTH']['posterior']['pos']; ax.axvline(bp['media'],color=P['VIO'],lw=2,label=f"posterior média={bp['media']}")
ax.axvspan(bp['ICr95'][0],bp['ICr95'][1],color=P['VIO'],alpha=.12,label=f"ICr95% [{bp['ICr95'][0]}; {bp['ICr95'][1]}]")
fpos=[f for f in LMM['PTH']['fixos'] if f['termo']=='pos'][0]
ax.axvline(fpos['beta'],color=P['RED'],ls='--',lw=1.5,label=f"frequentista β={fpos['beta']}")
ax.set_xlabel('efeito do pós no PTH'); ax.set_ylabel('densidade posterior')
ax.legend(frameon=False,fontsize=7.5); ax.set_title(f"C · Bayesiano (Gibbs) — P(efeito>0)={BAY['PTH']['posterior']['P(pos>0)']}",fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D PERMANOVA nula
ax=axs[1,1]; nullF=[]
for _ in range(4000):
    sw=RS.rand(len(ath))<0.5; A2=np.where(sw[:,None],B,A); B2=np.where(sw[:,None],A,B)
    nullF.append(pseudoF(A2,B2)[0])
ax.hist(nullF,bins=45,color=P['GRID'],edgecolor='white')
ax.axvline(Fobs,color=P['RED'],lw=2,label=f'pseudo-F obs={Fobs:.2f}')
ax.set_xlabel('pseudo-F sob H₀ (permutação restrita)'); ax.set_ylabel('frequência')
ax.legend(frameon=False,fontsize=8)
ax.set_title(f'D · Multivariada PERMANOVA — R²={R2perm:.3f}, p={pperm:.4f}',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'modelo_teorico_fig.png'),facecolor='white'); plt.close()

# ================= FIGURA framework (equações) =================
fig,ax=plt.subplots(figsize=(12.5,7.6),dpi=150); ax.axis('off'); ax.set_xlim(0,10); ax.set_ylim(0,10)
def box(x,y,w,h,fc,ec,title,lines,tc='#122438',dy=0.42,fs=9.3):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.06,rounding_size=0.12",fc=fc,ec=ec,lw=1.6))
    ax.text(x+w/2,y+h-0.32,title,ha='center',va='top',fontsize=11,fontweight='bold',color=ec)
    for i,ln in enumerate(lines): ax.text(x+w/2,y+h-0.82-i*dy,ln,ha='center',va='top',fontsize=fs,color=tc)
def arrow(x1,y1,x2,y2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=16,color=P['MUT'],lw=1.6))
ax.text(5,9.7,'Framework: do modelo teórico à estimativa',ha='center',fontsize=14,fontweight='bold',color=P['NAVY'])
box(0.3,7.0,4.5,2.2,'#EAF3F1',P['TEAL'],'1 · Modelo teórico (fitness–fadiga)',
    [r'$State(t)=p_0+k_1\,g(t)-k_2\,h(t)$',r'$g,h=\sum w_i\,e^{-(t-i)/\tau}$ (fitness, fadiga)','vigor↑ = fitness · fadiga↑ = custo agudo'])
box(5.2,7.0,4.5,2.2,'#EEF1FA',P['BLUE'],'2 · Forma estimável (mistos)',
    [r'$Y_{ijt}=\beta_0+\beta_1 P\acute{o}s+\beta_2 Dia+\beta_3 HIIT$',r'$\qquad +\,u_i+\varepsilon_{ijt}$',r'$u_i\sim N(0,\tau^2),\ \varepsilon\sim N(0,\sigma^2)$'])
box(0.3,4.0,3.0,2.2,'#F3EEFA',P['VIO'],'3a · R² (determinação)',
    [r'$R^2_m=\sigma^2_f\,/\,(\sigma^2_f+\tau^2+\sigma^2)$',r'$R^2_c=(\sigma^2_f+\tau^2)\,/\,(\cdots)$','marginal vs. condicional'],dy=0.5)
box(3.55,4.0,3.0,2.2,'#FBF1E5',P['GOLD'],'3b · Erro-padrão',
    [r'$\hat\beta\pm 1{,}96\cdot SE(\hat\beta)$','IC95% dos efeitos fixos','(REML, MixedLM)'])
box(6.8,4.0,2.9,2.2,'#F3EEFA',P['VIO'],'3c · Bayesiano',
    [r'$p(\beta,\tau,\sigma\mid y)$ via Gibbs','média, SE e ICr95%',r'$P(\mathrm{efeito}>0)$'])
box(2.0,1.0,6.0,2.0,'#FBEDEC',P['RED'],'4 · Multivariada (vetor das 6 subescalas)',
    ['MANOVA (Pillai/Wilks) · PERMANOVA pareada (Anderson, 2001)',r'pseudo-$F$, $R^2=SS_b/SS_t$, p por permutação restrita','a mudança pré→pós é um deslocamento multivariado'])
for x in [2.55,7.45]: arrow(x,7.0,x if x<5 else x,6.25) if False else None
arrow(2.55,6.98,1.8,6.22); arrow(5.05,6.98,5.05,6.22); arrow(7.9,6.98,8.25,6.22)
arrow(2.55,6.98,2.55,6.98)
arrow(5.0,3.98,5.0,3.02)
ax.text(5,0.45,'Três vias de estimação (R²/SE frequentista · Gibbs bayesiano · multivariada) convergem para o mesmo efeito no eixo energia–fadiga, dominado pela variância individual (τ²).',
        ha='center',fontsize=9,color=P['MUT'],style='italic')
fig.savefig(os.path.join(HERE,'framework_fig.png'),facecolor='white',bbox_inches='tight'); plt.close()
print("\nSalvo resultados_modelo_teorico.json + modelo_teorico_fig.png + framework_fig.png")
