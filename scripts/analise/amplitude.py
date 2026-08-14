import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv')

VARS=[('FadFisica','Fadiga física (0–10)'),('Fadiga','Fadiga BRUMS (0–20)'),('Vigor','Vigor (0–20)'),
      ('TMD','PTH/TMD'),('FadMental','Fadiga mental (0–10)'),('Tensao','Tensão'),('Depressao','Depressão'),
      ('Raiva','Raiva'),('Confusao','Confusão')]
out=[]
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

p("="*90); p("AMPLITUDE (range) — total, sinal semanal (grupo) e intra-atleta"); p("="*90)
p(f"{'Variável':<20s}{'min':>5s}{'max':>6s}{'Ampl.tot':>9s}{'IQR':>6s}{'Ampl.sinal':>11s}{'Ampl.intra':>11s}")
amp={}
for v,lab in VARS:
    d=hum.dropna(subset=[v])
    lo,hi=d[v].min(),d[v].max(); tot=hi-lo
    iqr=d[v].quantile(.75)-d[v].quantile(.25)
    daym=d.groupby('dia')[v].mean(); sig=daym.max()-daym.min()   # amplitude do sinal (trajetória do grupo)
    intra=d.groupby('ID')[v].apply(lambda s:s.max()-s.min()).mean()  # amplitude média intra-atleta
    amp[v]=dict(min=float(lo),max=float(hi),tot=float(tot),iqr=float(iqr),sig=float(sig),intra=float(intra))
    p(f"{lab:<20s}{lo:>5.0f}{hi:>6.0f}{tot:>9.1f}{iqr:>6.1f}{sig:>11.2f}{intra:>11.2f}")

p("\n"+"="*90); p("SEPARAÇÃO RUÍDO × SINAL — decomposição de variância (atleta + dia)  y ~ C(ID)+C(dia)"); p("="*90)
p("  Sinal-dia = variância da trajetória do microciclo (efeito sistemático dos 7 dias)")
p("  Sinal-traço = variância entre atletas (diferenças individuais estáveis)")
p("  Ruído = resíduo (erro de medida + flutuação aleatória intra-atleta) → ETM")
p(f"\n{'Variável':<20s}{'%sinal-dia':>11s}{'%traço':>9s}{'%ruído':>9s}{'ETM(ruído)':>11s}{'MDC95':>8s}{'SWC':>7s}{'SNR':>7s}")
sn={}
for v,lab in VARS:
    d=hum.dropna(subset=[v]).copy()
    m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit()
    a=anova_lm(m,typ=1)
    ss_id=a.loc['C(ID)','sum_sq']; ss_day=a.loc['C(dia)','sum_sq']; ss_res=a.loc['Residual','sum_sq']
    tot=ss_id+ss_day+ss_res
    pday=100*ss_day/tot; ptrait=100*ss_id/tot; pnoise=100*ss_res/tot
    etm=np.sqrt(a.loc['Residual','mean_sq'])           # typical error (noise SD)
    mdc=1.96*np.sqrt(2)*etm                              # minimal detectable change
    sd_between=d.groupby('ID')[v].mean().std()          # trait SD
    swc=0.2*sd_between                                   # smallest worthwhile change (Cohen 0.2)
    sig_ampl=amp[v]['sig']
    snr=sig_ampl/etm                                    # amplitude do sinal em unidades de ruído
    sn[v]=dict(pday=pday,ptrait=ptrait,pnoise=pnoise,etm=etm,mdc=mdc,swc=swc,snr=snr,sig=sig_ampl,
               detect=sig_ampl>mdc, worth=sig_ampl>swc)
    p(f"{lab:<20s}{pday:>11.1f}{ptrait:>9.1f}{pnoise:>9.1f}{etm:>11.2f}{mdc:>8.2f}{swc:>7.2f}{snr:>7.2f}")

p("\n"+"="*90); p("VEREDITO em DOIS NÍVEIS: individual (1 medida) vs grupo (média de ~27/dia)"); p("="*90)
p("  MDC95 individual = limiar de mudança confiável para UM atleta com UMA coleta.")
p("  MDC95 grupo = MDC95/√n — o ruído da MÉDIA do grupo encolhe por √n (n≈27/dia).")
nday=hum.groupby('dia').size().mean()
for v,lab in VARS:
    s=sn[v]; mdc_g=s['mdc']/np.sqrt(nday)
    di='SIM' if s['sig']>s['mdc'] else 'NÃO'; dg='SIM' if s['sig']>mdc_g else 'NÃO'
    s['mdc_g']=mdc_g; s['detect_g']=bool(s['sig']>mdc_g)
    verdict='SINAL no grupo, RUÍDO no indivíduo' if (s['sig']>mdc_g and s['sig']<=s['mdc']) else ('SINAL nos dois níveis' if s['sig']>s['mdc'] else 'abaixo do detectável')
    p(f"  {lab:<22s} ampl={s['sig']:.2f} | MDC-indiv={s['mdc']:.2f}→{di} | MDC-grupo={mdc_g:.2f}→{dg}  →  {verdict}")

p("\n"+"="*90); p("RUÍDO INTRA-DIA vs DERIVA SEMANAL (quanto do movimento é aleatório vs direcional)"); p("="*90)
# For each athlete: within-day (pre->post) absolute fluctuation vs across-week net drift (D7-D1)
for v,lab in [('FadFisica','Fadiga física'),('Fadiga','Fadiga BRUMS'),('Vigor','Vigor'),('TMD','TMD')]:
    d=hum.dropna(subset=[v])
    # noise proxy: SD of residuals after removing athlete+day
    m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); noise_sd=np.std(m.resid)
    # weekly drift signal: |mean(D7)-mean(D1)|
    drift=abs(d[d.dia==7][v].mean()-d[d.dia==1][v].mean())
    ratio=drift/noise_sd
    p(f"  {lab:<16s} deriva semanal |D7-D1|={drift:.2f} | ruído(DP resid)={noise_sd:.2f} | deriva/ruído={ratio:.2f}")

json.dump({'amp':amp,'sn':{k:{kk:(float(vv) if isinstance(vv,(int,float,np.floating)) else bool(vv)) for kk,vv in val.items()} for k,val in sn.items()}},
          open(f'{SC}/amp_data.json','w'),indent=1)
open(f'{SC}/res_amplitude.txt','w').write('\n'.join(out))
print("\n[saved amp_data.json, res_amplitude.txt]")
