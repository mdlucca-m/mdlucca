import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv'); ext=pd.read_csv(f'{SC}/ext_load.csv')
hr=pd.read_csv(f'{SC}/hr_series.csv'); wcsv=pd.read_csv(f'{SC}/wellness_all.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

# ============ A. BASELINE 21/04 (dia 1, repouso) ============
p("="*70); p("A. BASELINE (21/04 — dia 1, repouso/linha de base)"); p("="*70)
b=hum[hum.dia==1]
p(f"  n obs baseline = {len(b)}  ({b.ID.nunique()} atletas)")
for v,lab in [('Vigor','Vigor'),('Fadiga','Fadiga(BRUMS)'),('FadFisica','Fadiga fisica'),
              ('FadMental','Fadiga mental'),('TMD','TMD'),('Tensao','Tensao'),
              ('Depressao','Depressao'),('Raiva','Raiva'),('Confusao','Confusao')]:
    p(f"    {lab:14s} = {b[v].mean():5.2f} ± {b[v].std():4.2f}")
neg=b[['Tensao','Depressao','Raiva','Fadiga','Confusao']].mean(axis=1)
p(f"  % perfil iceberg (baseline) = {100*(b['Vigor']>neg).mean():.0f}%")
# baseline wellness
wb=wcsv.copy(); wb['date']=pd.to_datetime(wb['datadia'],errors='coerce')
b1=wb[wb['date']==pd.Timestamp(2024,4,21)]
for v in ['TQR','Epworth','PSS']:
    s=pd.to_numeric(b1[v],errors='coerce').dropna()
    if len(s): p(f"    {v:14s} = {s.mean():5.2f} (baseline)")

# ============ C. CARGA EXTERNA (derivada do T-CAR, 104% PV) ============
p("\n"+"="*70); p("C. CARGA EXTERNA HIIT (4x4min @ 104% PV do T-CAR)"); p("="*70)
e=ext[ext.vel_kmh>0]   # exclude missing
p(f"  n atletas com dado = {len(e)}")
p(f"  Protocolo: 4 series x 4 min (240s); esforco intermitente 12s corrida/6s pausa")
p(f"             13,3 reps/bloco; tempo efetivo de corrida = 4x13,3x12s = 640 s (~10,7 min)")
p(f"  Velocidade media (=104% PV): {e.vel_kmh.mean():.2f} km/h ({e.vel_ms.mean():.2f} m/s)  [{e.vel_kmh.min():.1f}-{e.vel_kmh.max():.1f}]")
p(f"    -> PV do T-CAR implicada (vel/1,04): {e.vel_kmh.mean()/1.04:.2f} km/h")
p(f"  Distancia por esforco (12s): {e.dist_esforco.mean():.0f} m")
p(f"  Distancia por bloco (4 min): {e.dist_bloco.mean():.0f} m")
p(f"  Distancia por SESSAO: {e.dist_sessao.mean():.0f} m  [{e.dist_sessao.min():.0f}-{e.dist_sessao.max():.0f}]")
p(f"  Distancia TOTAL (3 sessoes): {e.dist_total3.mean():.0f} m (~{e.dist_total3.mean()/1000:.1f} km)")
p("  NOTA: prescricao relativa (104% PV) => carga externa IGUAL nas 3 sessoes por atleta.")

# ============ B. CARGA INTERNA por sessao (FC, PSE, TRIMP) ============
p("\n"+"="*70); p("B. CARGA INTERNA HIIT por sessao (S1=22/04, S2=24/04, S3=27/04)"); p("="*70)
def banister(hrmean, hrrest=60, hrmax=195, D=16):
    hrr=(hrmean-hrrest)/(hrmax-hrrest)
    return D*hrr*0.64*np.exp(1.92*hrr)
rows_int=[]
for s in ['S1','S2','S3']:
    g=hr[hr.sessao==s]
    hm=g.HRmean.mean(); hp=g.HRpico.mean(); pse=g.PSE.mean()
    tb=banister(hm); srpe=pse*26  # session-RPE = PSE * duracao (~26 min)
    rows_int.append((s,hm,hp,pse,tb,srpe))
    p(f"  {s}: FC media={hm:.1f}  FC pico={hp:.1f}  PSE(media series)={pse:.2f}  TRIMP-Banister={tb:.1f}  sRPE={srpe:.0f}")
# trends
fcp=[r[2] for r in rows_int]; tri=[r[4] for r in rows_int]; ps=[r[3] for r in rows_int]
p(f"  Tendencia S1->S3:  FC pico {fcp[0]:.1f}->{fcp[2]:.1f} (queda={fcp[0]-fcp[2]:.1f})  |  PSE {ps[0]:.1f}->{ps[2]:.1f} (sobe)  |  TRIMP {tri[0]:.1f}->{tri[2]:.1f} (queda)")
p("  => DISSOCIACAO: carga externa fixa; FC pico e TRIMP CAEM (supressao cardiaca sob fadiga),")
p("     enquanto PSE SOBE -> a fadiga acumulada e captada pela percepcao, nao pelo TRIMP cardiaco.")

# ============ D. VARIAVEIS PSICOLOGICAS nos dias de HIIT ============
p("\n"+"="*70); p("D. VARIAVEIS PSICOLOGICAS nos dias de HIIT (D2/D4/D7)"); p("="*70)
hd=hum[hum.dia.isin([2,4,7])].groupby('dia')[['TMD','Vigor','Fadiga','FadFisica']].mean()
for dia,lab in [(2,'S1 (D2)'),(4,'S2 (D4)'),(7,'S3 (D7)')]:
    r=hd.loc[dia]; p(f"  {lab}: TMD={r.TMD:.2f}  Vigor={r.Vigor:.2f}  Fadiga={r.Fadiga:.2f}  FadFisica={r.FadFisica:.2f}")
p("  Baseline (D1) p/ referencia: TMD=%.2f Vigor=%.2f FadFisica=%.2f"%(b.TMD.mean(),b.Vigor.mean(),b.FadFisica.mean()))

open(f'{SC}/res_load.txt','w').write('\n'.join(out)); print("\n[saved res_load.txt]")
