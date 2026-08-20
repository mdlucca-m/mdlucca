import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.interpolate import UnivariateSpline
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); T=json.load(open('temporal.json')); AR=json.load(open('all_results.json'))
seq=[(1,'baseline')]+sum([[(d,'pre'),(d,'pos')] for d in range(2,8)],[])
x=np.array([d+(-0.2 if m=='pre' else 0.2 if m=='pos' else 0.0) for d,m in seq])
xx=np.linspace(x.min(),x.max(),400)
DIMS=[('Vigor','Vigor','#0f8b8d'),('Fadiga','Fadiga','#e8590c'),('Tensao','Tensão','#1971c2'),
      ('Depressao','Depressão','#9c36b5'),('Raiva','Raiva','#e03131'),('Confusao','Confusão','#f08c00'),
      ('TMD','PTH','#7048e8'),('FadFisica','Fadiga física','#0ca678'),('FadMental','Fadiga mental','#c2255c')]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11.5,'axes.edgecolor':'#333','axes.linewidth':1.0,
    'axes.grid':True,'grid.color':'#dddddd','grid.linewidth':0.8})
CA='#e8590c'; CR='#1971c2'

def dash(k,lab,col):
    y=np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m in seq])
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85); ys=s(xx); d1=s.derivative(1)(xx); d2=s.derivative(2)(xx)
    dv=T['derivadas'][k]; ds=AR['desc_semana'][k]; ac=T['agudo_cronico'][k]; lim=T['limiares'].get(k,{})
    floor0=100*np.mean(pd.to_numeric(h[k],errors='coerce').dropna()<=0)
    fig=plt.figure(figsize=(13,17.5)); gs=GridSpec(5,2,figure=fig,height_ratios=[1.5,1.1,1.5,1.2,1.1],hspace=0.95,wspace=0.22)
    # A) trajetória + limites
    a=fig.add_subplot(gs[0,:])
    a.plot(x,y,'o',color=col,alpha=0.35,ms=6); a.plot(xx,ys,color=col,lw=3.2)
    a.axhline(ys.min(),ls=':',color=col,lw=1.6); a.axhline(ys.max(),ls=':',color=col,lw=1.6)
    for d in [2,4,7]: a.axvline(d,color='#999',ls='--',lw=1)
    if dv['inflexao']: a.axvline(dv['inflexao'][0],color='#212529',ls=':',lw=1.6)
    a.set_title('A) %s — trajetória e LIMITES (pontilhado=min/max; tracejado=HIIT; ponto=inflexão)'%lab.upper(),fontweight='bold',fontsize=12)
    a.set_xlabel('Dia do microciclo'); a.set_ylabel('Escore')
    # B) velocidade
    b=fig.add_subplot(gs[1,0]); b.plot(xx,d1,color=col,lw=2.4); b.axhline(0,color='#333',lw=1)
    b.set_title('B) Velocidade (1ª derivada)',fontweight='bold',fontsize=11.5); b.set_xlabel('Dia'); b.set_ylabel('d/dt (pts/dia)')
    # C) aceleração
    c=fig.add_subplot(gs[1,1]); c.plot(xx,d2,color=col,lw=2.4); c.axhline(0,color='#333',lw=1)
    c.set_title('C) Aceleração (2ª derivada)',fontweight='bold',fontsize=11.5); c.set_xlabel('Dia'); c.set_ylabel('d²/dt²')
    # D) transições sequenciais (dz) — agudo/recuperação
    dax=fig.add_subplot(gs[2,:]); tr=T['trans']
    xs=np.arange(len(tr)); dz=[t['vars'][k]['dz'] for t in tr]; cols=[CA if t['tipo']=='Agudo' else CR for t in tr]
    dax.bar(xs,dz,color=cols,edgecolor='white')
    for i,t in enumerate(tr):
        if t['vars'][k]['sig']: dax.text(i,dz[i]+(0.03 if dz[i]>=0 else -0.03),'*',ha='center',va='bottom' if dz[i]>=0 else 'top',fontsize=15,color='#212529')
    dax.axhline(0,color='#333',lw=1); dax.set_xticks(xs); dax.set_xticklabels([t['lab'].replace(' → ','→') for t in tr],rotation=45,ha='right',fontsize=8)
    dax.set_title('D) TRANSIÇÕES SEQUENCIAIS — tamanho de efeito (laranja=agudo pré→pós; azul=recuperação; * p<0,05)',fontweight='bold',fontsize=11.5); dax.set_ylabel('dz')
    # E) efeito agudo por dia
    e=fig.add_subplot(gs[3,0]); pp=T['prepos_dia']; days=list(range(2,8))
    dzs=[pp[str(d)][k]['dz'] for d in days]; sigd=[pp[str(d)][k]['sig'] for d in days]
    e.bar(days,dzs,color=[CA if sg else '#ced4da' for sg in sigd],edgecolor='white')
    for d,v,sg in zip(days,dzs,sigd):
        if sg: e.text(d,v+(0.02 if v>=0 else -0.02),'*',ha='center',va='bottom' if v>=0 else 'top',fontsize=13)
    e.axhline(0,color='#333',lw=1); e.set_xticks(days); e.set_title('E) Efeito agudo por dia (pré→pós)',fontweight='bold',fontsize=11.5); e.set_xlabel('Dia'); e.set_ylabel('dz')
    # F) caixa descritiva
    g=fig.add_subplot(gs[3,1]); g.axis('off')
    inf=('dia %.1f'%dv['inflexao'][0]) if dv['inflexao'] else 'n/d'
    txt=('DESCRITIVA — %s\n\n'
     'Média ± DP:  %.2f ± %.2f\n'
     'Mediana:     %.1f\n'
     'Mín–Máx:     %.0f – %.0f\n'
     'CV:          %.0f%%\n'
     'Piso (zeros):%.0f%%\n'
     'ICC:         %.2f\n'
     'MDC95:       %.1f pts\n\n'
     'D1 → D7:     %.1f → %.1f\n'
     'Δ (D1→D7):   %+.1f (dz=%+.2f%s)\n'
     'Inflexão:    %s\n'
     'Vel. pico:   %+.1f pts/dia (dia %.1f)\n'
     'Agudo médio: %+.2f | Crônico: %+.2f'%(
       lab,ds['m'],ds['sd'],ds['med'],ds['mn'],ds['mx'],ds['cv'] or 0,floor0,lim.get('icc',0),lim.get('mdc95',0),
       ac['cronico_delta']+0*0+ (AR['d1d7'][k]['d1']-AR['d1d7'][k]['d1']),  # placeholder to keep tuple len
       0,0,0,0,inf,dv['vel_pico'],dv['vel_pico_dia'],ac['agudo_medio'],ac['cronico_delta']))
    # rebuild cleanly (avoid the placeholder mess)
    d17=AR['d1d7'][k]
    txt=('DESCRITIVA — %s\n\n'
     'Média ± DP:  %.2f ± %.2f\n'
     'Mediana:     %.1f\n'
     'Mín – Máx:   %.0f – %.0f\n'
     'CV:          %.0f%%\n'
     'Piso (zeros): %.0f%%\n'
     'ICC:         %.2f\n'
     'MDC95:       %.1f pts\n\n'
     'D1 → D7:     %.1f → %.1f\n'
     'Δ (D1→D7):   %+.1f  (dz=%+.2f%s)\n'
     'Inflexão:    %s\n'
     'Vel. pico:   %+.1f pts/dia (dia %.1f)\n'
     'Agudo médio: %+.2f  |  Crônico: %+.2f')%(
       lab,ds['m'],ds['sd'],ds['med'],ds['mn'],ds['mx'],ds['cv'] or 0,floor0,lim.get('icc',0),lim.get('mdc95',0),
       d17['d1'],d17['d7'],d17['delta'],d17['dz'],'*' if d17['sig'] else '',inf,dv['vel_pico'],dv['vel_pico_dia'],
       ac['agudo_medio'],ac['cronico_delta'])
    g.text(0.0,0.98,txt,va='top',ha='left',family='DejaVu Sans Mono',fontsize=11.5)
    fig.suptitle('PAINEL DA VARIÁVEL: %s'%lab.upper(),fontweight='bold',fontsize=15,y=0.997,color=col)
    fn=k
    fig.savefig(f'{OUT}/vd_{fn}.png',dpi=140,bbox_inches='tight',facecolor='white'); plt.close(fig)
    print('OK vd_%s.png'%fn)

for k,lab,col in DIMS: dash(k,lab,col)
