import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy.interpolate import UnivariateSpline
from scipy.stats import wilcoxon
h=pd.read_csv('hum_prof.csv')
VARS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),
      ('Raiva','Raiva'),('Confusao','Confusão'),('TMD','PTH')]
KEYS=[k for k,_ in VARS]
ADV={}

# ================= 1) TRANSIÇÕES SEQUENCIAIS (agudo pré->pós e recuperação pós->pré) =================
# sequência de coletas ordenadas: (dia, momento, x)
seq=[(1,'baseline',1.0)]
for d in range(2,8):
    seq+=[(d,'pre',d-0.2),(d,'pos',d+0.2)]
def vals(dia,mo,k):
    s=h[(h.dia==dia)&(h.momento==mo)][['ID',k]].dropna()
    return s.set_index('ID')[k]
trans=[]
for i in range(len(seq)-1):
    d0,m0,x0=seq[i]; d1,m1,x1=seq[i+1]
    tipo='Agudo (pré→pós)' if (d0==d1) else 'Recuperação (pós→pré)'
    lab='D%d %s → D%d %s'%(d0,{'baseline':'base','pre':'pré','pos':'pós'}[m0],d1,{'pre':'pré','pos':'pós'}[m1])
    row={'lab':lab,'tipo':tipo,'d0':d0,'m0':m0,'d1':d1,'m1':m1,'x0':x0,'x1':x1,'vars':{}}
    for k,_ in VARS:
        a=vals(d0,m0,k); b=vals(d1,m1,k); j=a.index.intersection(b.index)
        aa=a.loc[j].values.astype(float); bb=b.loc[j].values.astype(float); diff=bb-aa
        n=len(diff); dm=float(diff.mean()); sd=float(diff.std(ddof=1)) if n>1 else 0.0
        dz=dm/sd if sd>0 else 0.0
        try: p=float(wilcoxon(aa,bb,zero_method='wilcox').pvalue) if n>=6 and np.any(diff!=0) else 1.0
        except Exception: p=1.0
        mag='trivial' if abs(dz)<0.2 else 'pequeno' if abs(dz)<0.5 else 'médio' if abs(dz)<0.8 else 'grande'
        row['vars'][k]={'n':n,'dm':dm,'dz':dz,'p':p,'mag':mag,'sig':bool(p<0.05)}
    trans.append(row)
ADV['trans']=trans

# resumo por tipo e variável (média dos dz e nº de transições significativas)
resumo={}
for k,_ in VARS:
    for tipo in ['Agudo (pré→pós)','Recuperação (pós→pré)']:
        sub=[t['vars'][k] for t in trans if t['tipo']==tipo]
        dzs=[s['dz'] for s in sub]; nsig=sum(1 for s in sub if s['sig'])
        resumo[(k,tipo)]={'dz_med':float(np.mean(dzs)),'nsig':nsig,'ntot':len(sub)}
ADV['resumo']={'%s|%s'%(k,t):v for (k,t),v in resumo.items()}

# ================= 2) SINAL x RUÍDO + EFEITO PISO (por variável, 13 coletas) =================
xx13=np.array([x for _,_,x in seq])
def colmean(k):
    return np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m,_ in seq])
snr={}
xd=np.linspace(xx13.min(),xx13.max(),400)
for k,_ in VARS:
    y=colmean(k)
    s=UnivariateSpline(xx13,y,k=min(4,len(xx13)-1),s=len(xx13)*np.var(y)*0.85)
    ys=s(xd); resid=y-s(xx13)
    signal_amp=float(ys.max()-ys.min()); noise_sd=float(np.std(resid,ddof=1))
    var_sig=float(np.var(s(xx13))); var_noise=float(np.var(resid))
    snr_amp=signal_amp/noise_sd if noise_sd>0 else np.inf
    snr_var=var_sig/var_noise if var_noise>0 else np.inf
    obs=h[k].dropna().values.astype(float)
    floor0=float(100*np.mean(obs<=0)); floor1=float(100*np.mean(obs<=1))
    mn=float(np.mean(obs)); md=float(np.median(obs))
    d2=s.derivative(2)(xd); sign=np.sign(d2); idx=np.where(np.diff(sign)!=0)[0]
    infl=[float(xd[j]) for j in idx]
    snr[k]={'signal_amp':signal_amp,'noise_sd':noise_sd,'snr_amp':float(snr_amp),
            'snr_var':float(snr_var),'floor0':floor0,'floor1':floor1,'mean':mn,'median':md,
            'infl':infl,'ymin_x':float(xd[np.argmin(ys)]),'ymin':float(ys.min()),
            'ymax_x':float(xd[np.argmax(ys)]),'ymax':float(ys.max())}
ADV['snr']=snr

# ================= 3) CRUZAMENTO VIGOR x FADIGA (detalhe para zoom) =================
# curvas suavizadas de vigor e fadiga sobre as 13 coletas
yv=colmean('Vigor'); yf=colmean('Fadiga')
sv=UnivariateSpline(xx13,yv,k=4,s=len(xx13)*np.var(yv)*0.85)
sf=UnivariateSpline(xx13,yf,k=4,s=len(xx13)*np.var(yf)*0.85)
diff=sv(xd)-sf(xd); sg=np.sign(diff); zc=np.where(np.diff(sg)!=0)[0]
cross=[]
for j in zc:
    x0,x1=xd[j],xd[j+1]; d0,d1=diff[j],diff[j+1]
    xc=x0-d0*(x1-x0)/(d1-d0); yc=float(sv(xc))
    cross.append({'x':float(xc),'y':yc})
ADV['vf_cross']=cross
ADV['vf_last']=cross[-1] if cross else None

json.dump(ADV,open('adv.json','w'),ensure_ascii=False,indent=1)
print('OK adv.json')
print('transições:',len(trans))
print('cruzamentos V×F:',[(round(c['x'],2),round(c['y'],1)) for c in cross])
print('SNR (amplitude):',{k:round(snr[k]['snr_amp'],1) for k in KEYS})
print('efeito piso (% obs =0):',{k:round(snr[k]['floor0'],0) for k in KEYS})
# transições significativas
print('\nTransições significativas (p<0,05):')
for t in trans:
    sigs=[k for k in KEYS if t['vars'][k]['sig']]
    if sigs: print(' ',t['lab'],'[%s]'%t['tipo'].split()[0],'->',', '.join('%s dz=%+.2f'%(k,t['vars'][k]['dz']) for k in sigs))
