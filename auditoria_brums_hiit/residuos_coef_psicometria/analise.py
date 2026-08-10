# -*- coding: utf-8 -*-
"""Análises mais robustas: (A) coeficientes e diagnóstico de RESÍDUOS dos
modelos mistos (efeitos fixos com IC, componentes de variância, ICC, resíduos
condicionais, normalidade e heterocedasticidade, BLUPs por atleta); e
(B) PSICOMETRIA robusta por subescala (α de Cronbach, α ordinal por correlação
policórica/Spearman, ω de McDonald, AVE, confiabilidade composta CR, correlação
item-total corrigida) e validade discriminante de Fornell–Larcker.
Reproduzível: python analise.py  (de dentro de residuos_coef_psicometria/).
Fontes: modelagem/base_modelagem.csv e analises_avancadas/itens_brums.csv."""
import os, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import scipy.stats as st
import statsmodels.formula.api as smf
from factor_analyzer import FactorAnalyzer

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
base=pd.read_csv(os.path.join(ROOT,'modelagem','base_modelagem.csv'))
itd=pd.read_csv(os.path.join(ROOT,'analises_avancadas','itens_brums.csv'))

TEAL='#0e9c90'; CORAL='#c0392b'; GOLD='#b0790f'; BLUE='#245c8b'; VIOLET='#7a4fb0'
INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,
 'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})

OUT={'coeficientes':{}, 'residuos':{}, 'psicometria':{}, 'discriminante':{}}
LAB={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Fadiga':'Fadiga','Vigor':'Vigor'}

# ============ A. MODELOS MISTOS: coeficientes + resíduos ============
d=base[base['momento'].isin(['pre','pos'])].copy()
d['pos']=(d['momento']=='pos').astype(float)
d['hiit']=d['hiit'].astype(float); d['dia']=d['dia'].astype(float)
outcomes=['PTH','FadFis','Fadiga','Vigor']
resid_store={}
for y in outcomes:
    dd=d[['atleta','pos','dia','hiit',y]].dropna().rename(columns={y:'yv'})
    dd['dia']=dd['dia']-dd['dia'].mean()  # centrar p/ convergência
    m=smf.mixedlm('yv ~ pos + dia + hiit', dd, groups=dd['atleta'])
    r=None
    for _meth in ('powell','bfgs','cg','nm'):
        try:
            r=m.fit(reml=True, method=_meth, maxiter=500);
            if r.converged: break
        except Exception: r=None
    if r is None: r=m.fit(reml=True)
    ci=r.conf_int()
    fixed=[]
    for term in ['Intercept','pos','dia','hiit']:
        fixed.append({'termo':term,'beta':float(r.params[term]),'EP':float(r.bse[term]),
                      'z':float(r.tvalues[term]),'p':float(r.pvalues[term]),
                      'ic':[float(ci.loc[term,0]),float(ci.loc[term,1])]})
    var_re=float(r.cov_re.iloc[0,0]); var_res=float(r.scale); icc=var_re/(var_re+var_res)
    # resíduos condicionais (y - Xβ - u_atleta)
    fe_pred=r.predict(dd)  # fixed effects prediction
    re=r.random_effects
    u=dd['atleta'].map(lambda g: float(re[g].iloc[0]))
    cond_pred=fe_pred+u
    resid=dd['yv'].values - cond_pred.values
    fitted=cond_pred.values
    sw=st.shapiro(resid) if len(resid)<=5000 else (np.nan,np.nan)
    # heterocedasticidade: correlação |resid| x fitted (Spearman)
    rho,ph=st.spearmanr(np.abs(resid),fitted)
    resid_store[y]={'resid':resid,'fitted':fitted,'re':{g:float(re[g].iloc[0]) for g in re},
                    're_se':getattr(r,'random_effects_cov',None)}
    OUT['coeficientes'][y]={'label':LAB[y],'fixos':fixed,'var_atleta':var_re,'var_residual':var_res,
        'ICC':icc,'n_obs':int(len(dd)),'n_atletas':int(dd['atleta'].nunique())}
    OUT['residuos'][y]={'shapiro_W':float(sw[0]),'shapiro_p':float(sw[1]),
        'resid_media':float(np.mean(resid)),'resid_dp':float(np.std(resid,ddof=1)),
        'hetero_spearman_rho':float(rho),'hetero_p':float(ph),
        'homocedastico':bool(ph>0.05),'residuos_normais':bool(sw[1]>0.05)}

# ============ B. PSICOMETRIA ROBUSTA ============
subs={'Tensão':'tensao','Depressão':'depressao','Raiva':'raiva','Vigor':'vigor','Fadiga':'fadiga','Confusão':'confusao'}
def cronbach(X):
    X=np.asarray(X,float); k=X.shape[1]; v=X.var(axis=0,ddof=1); t=X.sum(axis=1).var(ddof=1)
    return k/(k-1)*(1-v.sum()/t) if t>0 else np.nan
def std_alpha(C):
    k=C.shape[0]; rbar=(C.sum()-k)/(k*(k-1)); return k*rbar/(1+(k-1)*rbar)
def item_total_corr(X):
    X=np.asarray(X,float); rs=[]
    for j in range(X.shape[1]):
        rest=np.delete(X,j,axis=1).sum(axis=1)
        rs.append(np.corrcoef(X[:,j],rest)[0,1])
    return rs
sub_scores={}
for name,pre in subs.items():
    cols=[f'{pre}_{i}' for i in range(1,5)]
    X=itd[cols].dropna()
    sub_scores[name]=X.sum(axis=1)
    a=cronbach(X)
    # alpha ordinal via matriz de Spearman (proxy robusto para itens ordinais)
    Csp=X.corr(method='spearman').values; a_ord=std_alpha(Csp)
    # 1-fator: cargas padronizadas -> ω, AVE, CR
    fa=FactorAnalyzer(n_factors=1, rotation=None, method='minres')
    fa.fit(X.values)
    load=np.abs(fa.loadings_[:,0]); load=np.clip(load,0,0.999)
    err=1-load**2
    omega=(load.sum()**2)/((load.sum()**2)+err.sum())
    ave=float(np.mean(load**2)); cr=(load.sum()**2)/((load.sum()**2)+err.sum())
    it=item_total_corr(X)
    OUT['psicometria'][name]={'k':len(cols),'alpha':float(a),'alpha_ordinal':float(a_ord),
        'omega':float(omega),'AVE':ave,'CR':float(cr),'item_total_medio':float(np.mean(it)),
        'item_total_min':float(np.min(it)),'cargas':[float(x) for x in load]}
# validade discriminante Fornell-Larcker: sqrt(AVE) vs r entre subescalas
SS=pd.DataFrame(sub_scores); rmat=SS.corr().values; names=list(subs)
fl=[]
for i,ni in enumerate(names):
    row={'sub':ni,'sqrtAVE':float(np.sqrt(OUT['psicometria'][ni]['AVE']))}
    for j,nj in enumerate(names): row[nj]=float(rmat[i,j])
    fl.append(row)
OUT['discriminante']={'nomes':names,'linhas':fl,
    'nota':'Fornell–Larcker: √AVE (diagonal) deve exceder as correlações fora da diagonal.'}

# ============ C. ANÁLISE FATORIAL EXPLORATÓRIA (AFE) + cargas ============
from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity
itemcols=[f'{p}_{i}' for p in subs.values() for i in range(1,5)]
Xall=itd[itemcols].dropna()
chi2,bp=calculate_bartlett_sphericity(Xall.values)
kmo_item,kmo_all=calculate_kmo(Xall.values)
fa_all=FactorAnalyzer(n_factors=Xall.shape[1], rotation=None, method='minres'); fa_all.fit(Xall.values)
ev,_=fa_all.get_eigenvalues()
# análise paralela (média de autovalores de dados aleatórios)
rng=np.random.default_rng(20240421); nrep=100; n,p=Xall.shape; rand_ev=np.zeros((nrep,p))
for b in range(nrep):
    Z=rng.standard_normal((n,p)); fr=FactorAnalyzer(n_factors=p,rotation=None,method='minres'); fr.fit(Z)
    rand_ev[b],_=fr.get_eigenvalues()
pa=rand_ev.mean(axis=0)
n_kaiser=int((ev>1).sum()); n_pa=int((ev>pa).sum())
# AFE com 6 fatores, rotação oblíqua (promax)
fa6=FactorAnalyzer(n_factors=6, rotation='promax', method='minres'); fa6.fit(Xall.values)
load6=fa6.loadings_; var6=fa6.get_factor_variance()  # (var, prop, cum)
OUT['afe']={'n_itens':len(itemcols),'n_casos':int(n),'KMO':float(kmo_all),
    'bartlett_chi2':float(chi2),'bartlett_p':float(bp),
    'autovalores':[float(x) for x in ev],'paralela':[float(x) for x in pa],
    'n_fatores_kaiser':n_kaiser,'n_fatores_paralela':n_pa,
    'variancia_prop':[float(x) for x in var6[1]],'variancia_cum':[float(x) for x in var6[2]],
    'cargas':{itemcols[i]:[float(load6[i,j]) for j in range(6)] for i in range(len(itemcols))}}

# ---- FIGURA 3: AFE (scree/paralela + heatmap de cargas) ----
fig=plt.figure(figsize=(13.2,6.6),dpi=150); fig.patch.set_facecolor('white')
gs=GridSpec(1,2,figure=fig,width_ratios=[1,1.25],wspace=0.24,left=0.07,right=0.98,top=0.86,bottom=0.14)
fig.suptitle('Análise fatorial exploratória (AFE) e cargas',x=0.07,ha='left',fontsize=15,fontweight='bold',y=0.965)
fig.text(0.07,0.915,f'KMO={kmo_all:.2f} · Bartlett p={"<0,001" if bp<0.001 else format(bp,".3f")} · '
         f'Kaiser={n_kaiser} fatores · análise paralela={n_pa} fatores.',fontsize=9.5,color=MUT)
axs=fig.add_subplot(gs[0,0]); xs=np.arange(1,len(ev)+1)
axs.plot(xs,ev,'-o',color=BLUE,lw=2,ms=5,label='dados (autovalores)')
axs.plot(xs,pa,'--o',color=CORAL,lw=1.6,ms=4,label='análise paralela (aleatório)')
axs.axhline(1,color=MUT,ls=':',lw=1,label='Kaiser (>1)'); axs.set_xlabel('fator'); axs.set_ylabel('autovalor')
axs.set_title('Scree + análise paralela',fontsize=11,loc='left'); axs.legend(fontsize=8,frameon=False)
for s in ['top','right']: axs.spines[s].set_visible(False)
axh=fig.add_subplot(gs[0,1])
im=axh.imshow(load6,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
axh.set_xticks(range(6)); axh.set_xticklabels([f'F{i+1}' for i in range(6)],fontsize=9)
axh.set_yticks(range(len(itemcols))); axh.set_yticklabels(itemcols,fontsize=6.5)
for i in range(len(itemcols)):
    for j in range(6):
        v=load6[i,j]
        if abs(v)>=0.4: axh.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=6,color='white' if abs(v)>0.6 else INK)
axh.set_title('Matriz de cargas (promax, 6 fatores)',fontsize=11,loc='left')
cb=fig.colorbar(im,ax=axh,shrink=0.6,pad=0.02); cb.ax.tick_params(labelsize=7)
fig.savefig(os.path.join(HERE,'afe_cargas_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)
print('AFE: KMO %.2f · Kaiser %d · paralela %d fatores · var acum 6F %.1f%%'%(kmo_all,n_kaiser,n_pa,var6[2][5]*100))

# ============ D. BLAND–ALTMAN (limites de concordância) ============
# Concordância entre instrumentos do mesmo construto, reescalados a % do máximo.
ba_pairs=[('Fadiga física (externa) × Fadiga (BRUMS)','FadFis',10.0,'Fadiga',16.0,CORAL),
          ('Estado físico (externo) × Vigor (BRUMS)','EstFis',4.0,'Vigor',16.0,TEAL)]
OUT['bland_altman']=[]
ba_data=[]
for titulo,c1,mx1,c2,mx2,col in ba_pairs:
    dd=base[['atleta',c1,c2]].dropna().copy()
    a1=dd[c1].values/mx1*100.0; a2=dd[c2].values/mx2*100.0
    mean=(a1+a2)/2.0; diff=a1-a2
    bias=float(np.mean(diff)); sd=float(np.std(diff,ddof=1))
    loa=[bias-1.96*sd, bias+1.96*sd]
    # LoA ciente de medidas repetidas: decompõe a variância de d entre/intra atleta
    g=dd.assign(d=diff).groupby('atleta')['d']; k=g.count()
    ms_b=float(((g.mean()-bias)**2*k).sum()/(len(k)-1)) if len(k)>1 else np.nan
    within=float(((dd.assign(d=diff).groupby('atleta')['d'].transform(lambda x:x-x.mean()))**2).sum()/(len(diff)-len(k)))
    sd_rm=float(np.sqrt(max(ms_b,0)+within))
    loa_rm=[bias-1.96*sd_rm, bias+1.96*sd_rm]
    r=float(np.corrcoef(a1,a2)[0,1])
    OUT['bland_altman'].append({'par':titulo,'n':int(len(diff)),'bias':bias,'sd_dif':sd,
        'LoA':loa,'sd_rm':sd_rm,'LoA_rm':loa_rm,'r_pearson':r,
        'nota':'Escala % do máximo. LoA_rm corrige a SD das diferenças para medidas repetidas (Bland & Altman, 2007).'})
    ba_data.append((titulo,mean,diff,bias,loa_rm,col))

fig=plt.figure(figsize=(13.2,5.4),dpi=150); fig.patch.set_facecolor('white')
gs=GridSpec(1,2,figure=fig,wspace=0.22,left=0.07,right=0.97,top=0.82,bottom=0.15)
fig.suptitle('Bland–Altman — limites de concordância (LoA)',x=0.07,ha='left',fontsize=15,fontweight='bold',y=0.97)
fig.text(0.07,0.90,'Concordância entre instrumentos do mesmo construto (escala % do máximo). LoA ciente de medidas repetidas.',fontsize=9.5,color=MUT)
for i,(titulo,mean,diff,bias,loa,col) in enumerate(ba_data):
    ax=fig.add_subplot(gs[0,i])
    ax.scatter(mean,diff,s=16,color=col,alpha=.45,edgecolor='none')
    ax.axhline(bias,color=INK,lw=1.6,label='viés %.1f'%bias)
    ax.axhline(loa[0],color=CORAL,ls='--',lw=1.4); ax.axhline(loa[1],color=CORAL,ls='--',lw=1.4,label='LoA 95%% [%.1f; %.1f]'%(loa[0],loa[1]))
    ax.axhline(0,color=MUT,ls=':',lw=1)
    ax.set_xlabel('média dos dois (% do máximo)'); ax.set_ylabel('diferença (% do máximo)')
    ax.set_title(('A' if i==0 else 'B')+' · '+titulo,fontsize=10.5,loc='left')
    ax.legend(fontsize=8,frameon=False,loc='upper right')
    for s in ['top','right']: ax.spines[s].set_visible(False)
fig.savefig(os.path.join(HERE,'bland_altman_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)
print('Bland–Altman:', [(b['par'].split(' ×')[0], round(b['bias'],1), [round(x,1) for x in b['LoA_rm']]) for b in OUT['bland_altman']])

# ============ FIGURA 1: resíduos + coeficientes ============
fig=plt.figure(figsize=(13.2,9.2),dpi=150); fig.patch.set_facecolor('white')
gs=GridSpec(2,3,figure=fig,hspace=0.46,wspace=0.30,left=0.07,right=0.97,top=0.85,bottom=0.08)
fig.suptitle('Coeficientes e diagnóstico de resíduos dos modelos mistos',x=0.07,ha='left',
             fontsize=15,fontweight='bold',y=0.975)
fig.text(0.07,0.935,'Modelo: y ~ Pós + Dia + HIIT + (1|atleta). Resíduos condicionais (y − Xβ − u_atleta).',
         fontsize=9.5,color=MUT)
rr=resid_store['FadFis']; res=rr['resid']; fit=rr['fitted']
axA=fig.add_subplot(gs[0,0])
axA.scatter(fit,res,s=14,color=BLUE,alpha=.5,edgecolor='none'); axA.axhline(0,color=CORAL,lw=1.2)
axA.set_xlabel('valores ajustados'); axA.set_ylabel('resíduo'); axA.set_title('A · Resíduos vs. ajustados (Fadiga física)',fontsize=11,loc='left')
for s in ['top','right']: axA.spines[s].set_visible(False)
axB=fig.add_subplot(gs[0,1]); st.probplot(res,dist='norm',plot=axB)
axB.get_lines()[0].set(marker='o',ms=3.5,color=BLUE,alpha=.5); axB.get_lines()[1].set(color=CORAL,lw=1.2)
axB.set_title('')  # remove o título central "Probability Plot" do scipy
axB.set_title('B · Q–Q dos resíduos',fontsize=11,loc='left'); axB.set_xlabel('quantis teóricos'); axB.set_ylabel('quantis amostrais')
for s in ['top','right']: axB.spines[s].set_visible(False)
axC=fig.add_subplot(gs[0,2])
axC.scatter(fit,np.sqrt(np.abs(res)),s=14,color=VIOLET,alpha=.5,edgecolor='none')
axC.set_xlabel('valores ajustados'); axC.set_ylabel('√|resíduo|'); axC.set_title('C · Escala-locação (homocedasticidade)',fontsize=11,loc='left')
for s in ['top','right']: axC.spines[s].set_visible(False)
axD=fig.add_subplot(gs[1,0]); axD.hist(res,bins=20,color=TEAL,alpha=.85,edgecolor='white')
axD.set_xlabel('resíduo'); axD.set_ylabel('freq.'); axD.set_title('D · Histograma dos resíduos',fontsize=11,loc='left')
for s in ['top','right']: axD.spines[s].set_visible(False)
# E: forest do coeficiente Pós (β±IC) por desfecho
axE=fig.add_subplot(gs[1,1])
ys=np.arange(len(outcomes))
for i,y in enumerate(outcomes):
    f=[x for x in OUT['coeficientes'][y]['fixos'] if x['termo']=='pos'][0]
    c=CORAL if f['beta']>=0 else TEAL
    axE.plot(f['ic'],[i,i],color=c,lw=2.2); axE.plot(f['beta'],i,'o',color=c,ms=7)
axE.axvline(0,color=LINE); axE.set_yticks(ys); axE.set_yticklabels([LAB[y] for y in outcomes],fontsize=9)
axE.set_title('E · Coeficiente β(Pós) ± IC95%',fontsize=11,loc='left'); axE.set_xlabel('β (unidades da escala)')
for s in ['top','right']: axE.spines[s].set_visible(False)
# F: caterpillar dos interceptos aleatórios (BLUPs) da fadiga física
axF=fig.add_subplot(gs[1,2])
re=rr['re']; vals=np.array(sorted(re.values())); axF.plot(vals,np.arange(len(vals)),'o',color=GOLD,ms=4)
axF.axvline(0,color=CORAL,lw=1.2); axF.set_title('F · Interceptos aleatórios por atleta (BLUP)',fontsize=11,loc='left')
axF.set_xlabel('desvio do atleta'); axF.set_ylabel('atleta (ordenado)')
for s in ['top','right']: axF.spines[s].set_visible(False)
fig.savefig(os.path.join(HERE,'residuos_coef_fig.png'),dpi=150,facecolor='white',bbox_inches='tight')
plt.close(fig)

# ============ FIGURA 2: psicometria robusta ============
fig=plt.figure(figsize=(13.2,5.6),dpi=150); fig.patch.set_facecolor('white')
gs=GridSpec(1,2,figure=fig,wspace=0.28,left=0.08,right=0.97,top=0.84,bottom=0.16)
fig.suptitle('Psicometria robusta por subescala',x=0.08,ha='left',fontsize=15,fontweight='bold',y=0.96)
fig.text(0.08,0.905,'Confiabilidade (α, α ordinal, ω), variância extraída (AVE) e confiabilidade composta (CR).',fontsize=9.5,color=MUT)
names=list(subs); x=np.arange(len(names)); w=0.2
ax=fig.add_subplot(gs[0,0])
for k,(key,col,lab) in enumerate([('alpha',BLUE,'α'),('alpha_ordinal',VIOLET,'α ordinal'),('omega',TEAL,'ω'),('CR',GOLD,'CR')]):
    ax.bar(x+(k-1.5)*w,[OUT['psicometria'][n][key] for n in names],w,color=col,label=lab)
ax.axhline(0.70,color=CORAL,ls='--',lw=1); ax.set_xticks(x); ax.set_xticklabels(names,rotation=25,ha='right',fontsize=9)
ax.set_ylim(0,1); ax.set_title('Confiabilidade (linha prática 0,70)',fontsize=11,loc='left')
ax.legend(fontsize=8,ncol=4,loc='upper center',bbox_to_anchor=(0.5,-0.22),frameon=False)
for s in ['top','right']: ax.spines[s].set_visible(False)
ax2=fig.add_subplot(gs[0,1])
ax2.bar(x,[OUT['psicometria'][n]['AVE'] for n in names],0.6,color=[TEAL if OUT['psicometria'][n]['AVE']>=0.5 else CORAL for n in names])
ax2.axhline(0.50,color=CORAL,ls='--',lw=1); ax2.set_xticks(x); ax2.set_xticklabels(names,rotation=25,ha='right',fontsize=9)
ax2.set_ylim(0,1); ax2.set_title('Variância média extraída (AVE ≥ 0,50)',fontsize=11,loc='left')
for s in ['top','right']: ax2.spines[s].set_visible(False)
fig.savefig(os.path.join(HERE,'psicometria_robusta_fig.png'),dpi=150,facecolor='white',bbox_inches='tight')
plt.close(fig)

json.dump(OUT,open(os.path.join(HERE,'resultados.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('OK — resultados.json + 2 figuras')
print('ICC:', {y:round(OUT['coeficientes'][y]['ICC'],2) for y in outcomes})
print('resíduos normais?', {y:OUT['residuos'][y]['residuos_normais'] for y in outcomes})
print('homocedástico?', {y:OUT['residuos'][y]['homocedastico'] for y in outcomes})
for n in names: p=OUT['psicometria'][n]; print(n,'α',round(p['alpha'],2),'ω',round(p['omega'],2),'AVE',round(p['AVE'],2),'CR',round(p['CR'],2))
