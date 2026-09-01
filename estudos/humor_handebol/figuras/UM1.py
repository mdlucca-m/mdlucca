# -*- coding: utf-8 -*-
"""M1 e M2 — figuras da trilha de modelagem."""
exec(open(__file__.replace('UM1.py','UVh.py')).read())
ML=json.load(open(f"{S}/V2_ml.json")); ML2=json.load(open(f"{S}/V2_ml2.json"))
ML3=json.load(open(f"{S}/V2_ml3.json"))

# ---------------- M1: desempenho contra as linhas de base ----------------
ordem=['XGBoost','Árvore de decisão','Random Forest','Regressão logística',
       'Regra: já estava em risco','Classe majoritária']
fig,axs=plt.subplots(1,2,figsize=(13.4,4.4),gridspec_kw=dict(width_ratios=[1.30,1],wspace=.46))

a=axs[0]
trivial=ML['RES']['Regra: já estava em risco']['auc']
for i,k in enumerate(ordem):
    r=ML['RES'][k]; y=len(ordem)-1-i
    base=k.startswith('Regra') or k.startswith('Classe')
    c='#8A9299' if k.startswith('Regra') else '#C3C9CC' if k.startswith('Classe') else CAT[i]
    a.plot(r['ic'],[y,y],color=c,lw=2.6,solid_capstyle='round',alpha=.42,zorder=2)
    a.plot([r['auc']],[y],'o',ms=9,color=c,mec=SURF,mew=1.8,zorder=3)
    a.text(1.005,y,vg(r['auc'],3),va='center',ha='left',fontsize=9.6,color=c,
           fontweight='normal' if base else 'bold')
a.axvline(trivial,color='#B3341A',lw=1.5,ls=(0,(4,3)),zorder=1)
a.text(trivial,len(ordem)-.30,'regra trivial',color='#B3341A',fontsize=8.8,ha='center',va='bottom')
a.axvline(.5,color=GRID,lw=1.1,zorder=1)
a.set_yticks(range(len(ordem))); a.set_yticklabels(list(reversed(ordem)),fontsize=10)
for t,k in zip(a.get_yticklabels(),reversed(ordem)):
    if k.startswith('Regra') or k.startswith('Classe'): t.set_color(MUT)
    else: t.set_fontweight('bold')
a.set_xlim(.40,1.06); a.set_ylim(-.62,len(ordem)-.10); a.set_xticks(np.arange(.5,1.01,.1))
a.set_xlabel('área sob a curva ROC, com intervalo de confiança de 95%')
gx(a); a.spines['left'].set_visible(False); a.tick_params(axis='y',length=0)
a.set_title('a) Amostra completa: 119 pares, 27 atletas',fontsize=10.6,loc='left',pad=10,fontweight='bold')

b=axs[1]
sg=ML2['SUBGRUPO']; ks=list(sg)
for i,k in enumerate(ks):
    r=sg[k]; y=len(ks)-1-i; c=CAT[i]
    b.plot(r['ic'],[y,y],color=c,lw=2.6,solid_capstyle='round',alpha=.42,zorder=2)
    b.plot([r['auc']],[y],'o',ms=9,color=c,mec=SURF,mew=1.8,zorder=3)
    b.text(1.005,y,vg(r['auc'],3),va='center',ha='left',fontsize=9.6,color=c,fontweight='bold')
b.axvline(.5,color='#B3341A',lw=1.5,ls=(0,(4,3)),zorder=1)
b.text(.5,len(ks)-.26,'acaso',color='#B3341A',fontsize=8.8,ha='center',va='bottom')
b.set_yticks(range(len(ks))); b.set_yticklabels(list(reversed(ks)),fontsize=10,fontweight='bold')
b.set_xlim(.40,1.06); b.set_ylim(-.62,len(ks)-.10); b.set_xticks(np.arange(.5,1.01,.1))
b.set_xlabel('área sob a curva ROC, com intervalo de confiança de 95%')
gx(b); b.spines['left'].set_visible(False); b.tick_params(axis='y',length=0)
b.set_title(f"b) Subgrupo acionável: {sg[ks[0]]['n']} pares que amanhecem fora da faixa de risco",
            fontsize=10.6,loc='left',pad=10,fontweight='bold')
rod(fig,'Validação cruzada estratificada e agrupada por atleta: nenhum atleta aparece ao mesmo tempo no treino e no teste. '
        'Intervalos por reamostragem agrupada.\nNa amostra completa nenhum ganho sobre a regra trivial exclui zero; '
        'no subgrupo acionável os três modelos de árvore excluem o acaso.',y=-.02)
salvar(fig,'M1fig')

# ---------------- M2: reversão à média e modelos aninhados ----------------
fig,axs=plt.subplots(1,2,figsize=(13.4,4.2),gridspec_kw=dict(width_ratios=[1,1],wspace=.34))
a=axs[0]
rv=sorted(ML3['REVERSAO'],key=lambda e:e['rho'])
y=np.arange(len(rv))[::-1]
cores=['#C1440E' if e['mecanico'] else '#1A9070' for e in rv]
a.barh(y,[-e['rho'] for e in rv],height=.62,color=cores,zorder=3)
for yy,e in zip(y,rv):
    a.text(-e['rho']+.012,yy,vg(e['rho'],3),va='center',ha='left',fontsize=9.4,color=INK)
a.set_yticks(y); a.set_yticklabels([e['variavel'] for e in rv],fontsize=10)
a.set_xlim(0,.78); a.set_xlabel('|ρ| entre o valor da manhã e a variação da manhã para a noite')
gx(a); a.spines['left'].set_visible(False); a.tick_params(axis='y',length=0)
a.set_title('a) Reversão à média: o que é movimento mecânico',fontsize=10.6,loc='left',pad=10,fontweight='bold')
a.legend(handles=[Patch(fc='#C1440E',label='componente mecânico (p < 0,05)'),
                  Patch(fc='#1A9070',label='sem componente mecânico')],
         frameon=False,fontsize=9,loc='lower right',bbox_to_anchor=(1.0,-.02))

b=axs[1]
an=ML3['ANINHADOS']; y=np.arange(len(an))[::-1]
for i,(yy,e) in enumerate(zip(y,an)):
    b.plot([e['auc']-e['dp'],e['auc']+e['dp']],[yy,yy],color=CAT[i],lw=2.4,alpha=.40,solid_capstyle='round',zorder=2)
    b.plot([e['auc']],[yy],'o',ms=9,color=CAT[i],mec=SURF,mew=1.8,zorder=3)
    b.text(.905,yy,vg(e['auc'],3),va='center',ha='left',fontsize=9.6,color=CAT[i],fontweight='bold')
b.annotate('', xy=(an[1]['auc'],y[1]+.34), xytext=(an[0]['auc'],y[0]-.34),
           arrowprops=dict(arrowstyle='-|>',color='#1A9070',lw=1.5,
                           connectionstyle='arc3,rad=-.25',shrinkA=2,shrinkB=2))
b.text((an[0]['auc']+an[1]['auc'])/2-.055,(y[0]+y[1])/2,
       'a tensão\nacrescenta\n'+vg(an[1]['auc']-an[0]['auc'],3),
       fontsize=8.8,color='#1A9070',ha='right',va='center',linespacing=1.35)
b.set_yticks(y); b.set_yticklabels([e['modelo'] for e in an],fontsize=10)
b.set_xlim(.60,.98); b.set_ylim(-.62,len(an)-.38); b.set_xticks(np.arange(.65,.91,.05))
b.set_xlabel('área sob a curva ROC, agrupada por atleta')
gx(b); b.spines['left'].set_visible(False); b.tick_params(axis='y',length=0)
b.set_title('b) Modelos aninhados: o que a tensão matinal acrescenta',fontsize=10.6,loc='left',pad=10,fontweight='bold')
rod(fig,'A barra do painel b é o desvio entre oito repetições da validação, não um intervalo de confiança. '
        'O corte pelo PTH tem componente mecânico; o corte pela tensão não tem, e é o que sustenta a leitura clínica.',y=-.02)
salvar(fig,'M2fig')
