import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv')
VARS=[('Vigor','Vigor'),('Fadiga','Fadiga BRUMS'),('TMD','PTH/TMD'),('FadMental','Fadiga mental')]
keys=[v for v,_ in VARS]; labs={v:l for v,l in VARS}
out=[]; P=lambda *a:(out.append(' '.join(str(x) for x in a)),print(*a))

# ---- reliability of a single observation = 1 - noise fraction (from atleta+dia decomposition) ----
rel={}; etm={}; snr_raw={}; sigamp={}
for v,_ in VARS:
    d=hum.dropna(subset=[v])
    m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); a=anova_lm(m,typ=1)
    ss=a['sum_sq']; tot=ss['C(ID)']+ss['C(dia)']+ss['Residual']
    rel[v]=1-ss['Residual']/tot
    etm[v]=np.sqrt(a.loc['Residual','mean_sq'])
    dm=d.groupby('dia')[v].mean(); sigamp[v]=dm.max()-dm.min(); snr_raw[v]=sigamp[v]/etm[v]
P("RELIABILIDADE de 1 medida (1 - fração de ruído):")
for v,_ in VARS: P(f"  {labs[v]:<14s} r_xx={rel[v]:.2f}  ETM={etm[v]:.2f}")

# ---- CORRELATIONS: observed (raw obs) vs disattenuated vs denoised (daily group means) ----
P("\nCORRELAÇÕES entre as 4 variáveis — antes e depois de remover o ruído")
raw=hum[keys].dropna()
Robs=raw.corr(method='pearson')
# disattenuated
Rdis=Robs.copy()
for x in keys:
    for y in keys:
        if x==y: Rdis.loc[x,y]=1.0
        else: Rdis.loc[x,y]=Robs.loc[x,y]/np.sqrt(rel[x]*rel[y])
# denoised at group level: correlate daily group means (noise averaged out by ~n/day)
gm=hum.groupby('dia')[keys].mean()
Rden=gm.corr(method='pearson')
def show(M,title):
    P(f"  {title}")
    P("            "+" ".join(f"{labs[k][:8]:>9s}" for k in keys))
    for x in keys:
        P(f"  {labs[x][:10]:<10s}"+" ".join(f"{M.loc[x,y]:>9.2f}" for y in keys))
show(Robs,"Observada (medidas brutas, com ruído):")
show(Rdis,"Desatenuada (corrigida pela confiabilidade):")
show(Rden,"Denoised (médias diárias do grupo — ruído agregado):")

# summary of key pairs
P("\n  Pares-chave (observada -> desatenuada -> nível-grupo):")
for x,y in [('Vigor','Fadiga'),('Fadiga','TMD'),('Vigor','TMD'),('FadMental','Fadiga')]:
    P(f"    {labs[x]} × {labs[y]}: {Robs.loc[x,y]:+.2f} -> {Rdis.loc[x,y]:+.2f} -> {Rden.loc[x,y]:+.2f}")

# ---- EFFECT SIZE D1->D7 corrected for attenuation ----
P("\nTAMANHO DE EFEITO D1->D7 (agregado por atleta): observado vs corrigido pela confiabilidade")
for v,_ in VARS:
    d1=hum[hum.dia==1].groupby('ID')[v].mean(); d7=hum[hum.dia==7].groupby('ID')[v].mean()
    common=d1.index.intersection(d7.index); a,b=d1.loc[common],d7.loc[common]
    diff=b-a; dz=diff.mean()/diff.std()
    dz_corr=dz/np.sqrt(rel[v])   # attenuation correction
    P(f"  {labs[v]:<14s} dz={dz:+.2f} -> corrigido={dz_corr:+.2f}")

# ---- INDIVIDUAL MONITORING: MDC shrinks with k collections; when does signal emerge? ----
P("\nDECISÃO INDIVIDUAL: MDC95 cai com k coletas (ruído/√k). Quando o sinal semanal supera o MDC?")
kmdc={}
for v,_ in VARS:
    P(f"  {labs[v]} (amplitude do sinal={sigamp[v]:.2f}):")
    row={}
    for k in [1,2,3,5,7]:
        mdc_k=1.96*np.sqrt(2)*etm[v]/np.sqrt(k); row[k]=mdc_k
        ok='SIM' if sigamp[v]>mdc_k else 'não'
        P(f"      k={k}: MDC95={mdc_k:.2f}  sinal>MDC? {ok}")
    kmdc[v]=row

# ---- HONEST CAVEAT: negatives stay flat even denoised ----
P("\nRESSALVA: remover ruído NÃO cria sinal onde não há (subescalas de piso)")
for v,lab in [('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]:
    d=hum.dropna(subset=[v]); dm=d.groupby('dia')[v].mean(); amp=dm.max()-dm.min()
    floor=100*(d[v]==0).mean()
    P(f"  {lab:<10s} amplitude do sinal (denoised)={amp:.2f}  | % no piso(0)={floor:.0f}%")

json.dump({'rel':rel,'etm':etm,'sigamp':sigamp,'snr_raw':snr_raw,
    'Robs':Robs.round(3).to_dict(),'Rdis':Rdis.round(3).to_dict(),'Rden':Rden.round(3).to_dict(),
    'kmdc':{v:{str(k):float(x) for k,x in r.items()} for v,r in kmdc.items()}},
    open(f'{SC}/denoise.json','w'),indent=1)
open(f'{SC}/res_denoise.txt','w').write('\n'.join(out))
print("\n[saved denoise.json]")
