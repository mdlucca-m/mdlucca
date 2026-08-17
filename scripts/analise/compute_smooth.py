import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
h=pd.read_csv(SC+'/hum_prof.csv'); days=np.arange(1,8)
ORD=[('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Vigor','Vigor'),
     ('Fadiga','Fadiga'),('Confusao','Confusão'),('TMD','PTH')]
GR=3
R={'grau':GR,'vars':{}}
for k,lab in ORD:
    y=h.groupby('dia')[k].mean().reindex(days).values      # trajetória diária (média já filtra ruído intradiário)
    sem=h.groupby('dia')[k].sem().reindex(days).values     # erro-padrão = ruído de medida por dia
    c=np.polyfit(days,y,GR); P=np.poly1d(c)
    sig=P(days)                                             # SINAL = componente suave (polinômio)
    noise=y-sig                                             # RUÍDO = resíduo em torno do sinal
    var_sig=float(np.var(sig,ddof=0)); var_noise=float(np.var(noise,ddof=0))
    r2=float(1-((y-sig)**2).sum()/((y-y.mean())**2).sum())
    snr=var_sig/var_noise if var_noise>1e-9 else float('inf')
    snr_db=10*np.log10(snr) if np.isfinite(snr) and snr>0 else float('inf')
    R['vars'][k]=dict(lab=lab,signal_pct=float(100*r2),noise_pct=float(100*(1-r2)),
        snr=float(snr) if np.isfinite(snr) else 999.0,
        snr_db=float(snr_db) if np.isfinite(snr_db) else 99.0,
        rmse=float(np.sqrt((noise**2).mean())),sem_mean=float(np.nanmean(sem)))
json.dump(R,open(SC+'/smooth.json','w'),indent=1,ensure_ascii=False)
print('Decomposição sinal–ruído (sinal = polinômio grau %d; ruído = resíduo):'%GR)
print('  %-9s %8s %8s %8s %8s'%('Var','sinal%','ruído%','SNR','SNR(dB)'))
for k,lab in ORD:
    v=R['vars'][k]
    print('  %-9s %7.0f%% %7.0f%% %8.1f %8.1f'%(lab,v['signal_pct'],v['noise_pct'],v['snr'],v['snr_db']))
