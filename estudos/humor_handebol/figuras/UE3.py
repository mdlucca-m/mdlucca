# -*- coding: utf-8 -*-
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UEh.py")).read())
DIV=LinearSegmentedColormap.from_list('div',['#17456F','#2166AC','#8FB4D4','#F2F3F4',
                                             '#E9A98D','#C1440E','#7E2C09'])
TIPOS=['HIIT','Amistoso','Técnico']

# ===================== E7: migração pré→pós por tipo de estímulo =====================
fig=plt.figure(figsize=(16.8,9.4)); gs=fig.add_gridspec(2,3,height_ratios=[1.32,1.0],hspace=.52,wspace=.30)
for j,t in enumerate(TIPOS):
    a=fig.add_subplot(gs[0,j]); d=E['PREV_PP'][t]
    pre=d['pre']; pos=d['pos']
    def dodge(vs,mind=3.1):
        idx=sorted(range(6),key=lambda i:vs[i]); out=[0.]*6; ult=None
        for i in idx:
            v=vs[i]
            if ult is not None and v-ult<mind: v=ult+mind
            out[i]=v; ult=v
        return out
    ype=dodge(pre); ypo=dodge(pos)
    for i,nm in enumerate(PERF):
        c=CPF[nm]
        a.plot([0,1],[pre[i],pos[i]],'-o',color=c,lw=3.4,ms=9,mfc='white',mew=2.6,zorder=4)
        a.annotate(f'{vg(pre[i])}',xy=(-.09,ype[i]),xytext=(0,0),textcoords='offset points',
                   ha='right',va='center',fontsize=9,color=c,fontweight='bold')
        a.annotate(f'{vg(pos[i])}',xy=(1.09,ypo[i]),xytext=(0,0),textcoords='offset points',
                   ha='left',va='center',fontsize=9,color=c,fontweight='bold')
    a.set_xlim(-.46,1.46); a.set_ylim(-6,56)
    a.set_xticks([0,1]); a.set_xticklabels(['PRÉ\n(manhã)','PÓS\n(noite)'],fontsize=10.5)
    if j==0: a.set_ylabel('Prevalência (%)',fontsize=11)
    a.set_title(f'({chr(65+j)}) {t} — {d["n"]} pares pré/pós',fontsize=12,loc='left',
                fontweight='bold',color=CEST[t])
    gy(a)
h=[Line2D([],[],color=CPF[nm],lw=3.4,marker='o',mfc='white',mew=2.6,ms=9,label=nm) for nm in PERF]
fig.legend(handles=h,fontsize=10,frameon=False,ncol=6,loc='upper center',bbox_to_anchor=(.5,.455))
aM=fig.add_subplot(gs[1,:])
yb=np.arange(3)[::-1]
for i,t in enumerate(TIPOS):
    m=E['MCN_EST'][t]
    aM.barh(yb[i]+.16,m['entra'],height=.30,color='#C1440E',alpha=.92,zorder=3,
            label='entra na faixa de risco' if i==0 else None)
    aM.barh(yb[i]-.16,-m['sai'],height=.30,color='#1A9070',alpha=.92,zorder=3,
            label='sai da faixa de risco' if i==0 else None)
    aM.annotate(str(m['entra']),xy=(m['entra'],yb[i]+.16),xytext=(7,0),textcoords='offset points',
                va='center',fontsize=11,fontweight='bold',color='#C1440E')
    aM.annotate(str(m['sai']),xy=(-m['sai'],yb[i]-.16),xytext=(-7,0),textcoords='offset points',
                va='center',ha='right',fontsize=11,fontweight='bold',color='#1A9070')
    txt=f'χ² = {vg(m["chi"],2)}; {pv(m["p"])}; Holm {pv(m["ph"])}'
    aM.annotate(txt,xy=(17.5,yb[i]),ha='left',va='center',fontsize=10.4,
                color=INK if m['p']<.05 else MUT,
                fontweight='bold' if m['p']<.05 else 'normal')
aM.axvline(0,color='#4A5257',lw=1.5,zorder=4)
aM.set_yticks(yb); aM.set_yticklabels([f'{t}\n(n = {E["MCN_EST"][t]["n"]})' for t in TIPOS],fontsize=11)
for tk,t in zip(aM.get_yticklabels(),TIPOS): tk.set_color(CEST[t]); tk.set_fontweight('bold')
aM.set_xlim(-11,33); aM.set_xticks([-10,-5,0,5,10,15])
aM.set_xticklabels(['10','5','0','5','10','15'],fontsize=10)
aM.set_xlabel('Número de pares atleta-dia que mudam de faixa entre a manhã e a noite',fontsize=11)
aM.set_title('(D) Teste de McNemar — migração para a faixa de risco dentro do dia, por estímulo',
             fontsize=12,loc='left',fontweight='bold')
aM.legend(fontsize=10,frameon=False,loc='upper center',ncol=2,bbox_to_anchor=(.5,-.20))
aM.grid(axis='x',color=GRID,lw=.8,zorder=0); aM.set_axisbelow(True)
rodape(fig,'Apenas o HIIT alcança significância bruta (p = 0,044) e ela não sobrevive à correção de Holm para três comparações.')
fig.savefig(f"{SAIDA}/E7fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E7 ok")

# ===================== E8: teste de cruzamento =====================
fig,ax=plt.subplots(1,3,figsize=(17.4,5.8))
a=ax[0]; marcar(a,alpha=.7)
FAV=np.array(Q['FAV']); RIS=np.array(Q['RIS']); NEU=np.array(Q['NEU'])
a.plot(x7,FAV,'-o',color='#1A9070',lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Faixa favorável (iceberg)')
a.plot(x7,NEU,'-o',color='#6B7378',lw=2.2,ms=7,mfc='white',mew=2.0,zorder=3,alpha=.75,label='Faixa neutra')
a.plot(x7,RIS,'-o',color='#C1440E',lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Faixa de risco')
cz=E['CRZ_P']['Favorável×De risco']['cross']
for i_,c in enumerate(cz):
    a.axvline(c,color='#2A2F33',lw=1.6,ls=(0,(3,2)),zorder=5)
    a.annotate(f'D{vg(c,2)}',xy=(c,[60,56,60][i_]),ha='center',va='center',fontsize=9,color=INK,
               fontweight='bold',zorder=6,
               bbox=dict(boxstyle='round,pad=.25',fc='white',ec='#8A9299',lw=1.0))
a.annotate('cruzamentos',xy=(.985,.985),xycoords='axes fraction',ha='right',va='top',
           fontsize=9,color=MUT,style='italic')
a.set_xlim(.5,7.5); a.set_ylim(0,64); a.set_xticks(x7)
a.set_xticklabels([f'D{d}' for d in x7],fontsize=10.5)
a.set_ylabel('Prevalência (%)',fontsize=11)
a.set_title('(A) Faixas de humor ao longo da semana',fontsize=12,loc='left',fontweight='bold')
a.legend(fontsize=9.6,frameon=False,loc='lower left')
gy(a)
a2=ax[1]; marcar(a2,alpha=.7)
d=E['CRZ_P']['Favorável×De risco']; dif=np.array(d['dif']); lim=d['lim']
a2.axhspan(-lim,lim,color='#6B7378',alpha=.16,zorder=1,lw=0)
a2.axhline(0,color='#2A2F33',lw=1.6,zorder=3)
a2.plot(x7,dif,'-o',color='#8A4FBF',lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4)
for c in cz:
    a2.plot([c],[0],marker='X',ms=13,color='#2A2F33',zorder=6,mec='white',mew=1.6)
a2.set_xlim(.5,7.5); a2.set_xticks(x7); a2.set_xticklabels([f'D{d_}' for d_ in x7],fontsize=10.5)
a2.set_ylabel('Favorável − De risco (p.p.)',fontsize=11)
a2.set_title('(B) Diferença entre as faixas e limiar de decisão',fontsize=12,loc='left',fontweight='bold')
a2.annotate(f'limiar = ±{vg(lim)} p.p.\ntrês cruzamentos (D1,49; D4,69; D5,24)\nnenhum ultrapassa o limiar dos dois lados\n→ divergência, não inversão estabelecida',
            xy=(.03,.045),xycoords='axes fraction',fontsize=9.4,color=INK,va='bottom',linespacing=1.5,
            bbox=dict(boxstyle='round,pad=.45',fc='#FFFFFF',ec='#8A9299',lw=1.2))
gy(a2)
a3=ax[2]; marcar(a3,alpha=.7)
vv=np.array(S2['SER']['Vigor']['sm']); ff=np.array(S2['SER']['Fadiga']['sm'])
a3.plot(x7,vv,'-o',color=CV['Vigor'],lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Vigor')
a3.plot(x7,ff,'-o',color=CV['Fadiga'],lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Fadiga')
cs=S2['CRZ']['Vigor×Fadiga']['cs'][0]; limv=S2['CRZ']['Vigor×Fadiga']['lim']
a3.axvline(cs,color='#2A2F33',lw=1.8,ls=(0,(3,2)),zorder=5)
a3.annotate(f'cruzamento em D{vg(cs,2)}',xy=(cs,7.8),xytext=(-8,0),textcoords='offset points',
            ha='right',fontsize=10,color=INK,fontweight='bold',
            bbox=dict(boxstyle='round,pad=.3',fc='white',ec='#8A9299',lw=1.1))
a3.fill_between(x7,vv,ff,where=(vv>=ff),color=CV['Vigor'],alpha=.11,zorder=1)
a3.fill_between(x7,vv,ff,where=(vv<ff),color=CV['Fadiga'],alpha=.11,zorder=1)
a3.set_xlim(.5,7.5); a3.set_ylim(3,8.6); a3.set_xticks(x7)
a3.set_xticklabels([f'D{d_}' for d_ in x7],fontsize=10.5)
a3.set_ylabel('Escore bruto suavizado (0–16)',fontsize=11)
a3.set_title('(C) Inversão estabelecida entre vigor e fadiga',fontsize=12,loc='left',fontweight='bold')
a3.legend(fontsize=10,frameon=False,loc='center left')
a3.annotate(f'limiar = ±{vg(limv,2)}; diferença em D1 = {vg(S2["CRZ"]["Vigor×Fadiga"]["d1"],2)}\n'
            f'e em D7 = {vg(S2["CRZ"]["Vigor×Fadiga"]["d7"],2)} → inversão estabelecida',
            xy=(.03,.045),xycoords='axes fraction',fontsize=9.4,color=INK,va='bottom',linespacing=1.5,
            bbox=dict(boxstyle='round,pad=.45',fc='#FFFFFF',ec='#8A9299',lw=1.2))
gy(a3)
fig.suptitle('Teste formal de cruzamento entre séries: quando uma troca de posição é real',
             fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.02)
fig.tight_layout()
fig.text(.011,-.035,'O limiar de cada par é o piso de ruído combinado das duas séries. Só se declara inversão quando a '
         'diferença ultrapassa o limiar antes e depois do cruzamento.',fontsize=8.8,color=MUT,style='italic'); fig.savefig(f"{SAIDA}/E8fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E8 ok")

# ===================== E9: estrutura de associação entre as variáveis =====================
V7=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','TMD']
L7=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','PTH']
MAT=B2['MAT']; DEC=B2['DEC']
def par(i,j):
    k=f'{V7[i]}×{V7[j]}'
    return MAT[k] if k in MAT else MAT[f'{V7[j]}×{V7[i]}']
def parD(i,j):
    k=f'{V7[i]}×{V7[j]}'
    return DEC[k] if k in DEC else DEC[f'{V7[j]}×{V7[i]}']
fig=plt.figure(figsize=(16.6,11.4))
gs=fig.add_gridspec(2,2,height_ratios=[1.14,1.0],width_ratios=[1.0,1.02],hspace=.34,wspace=.46)
a=fig.add_subplot(gs[0,0])
M=np.full((7,7),np.nan)
for i in range(7):
    for j in range(7):
        if i!=j: M[i,j]=par(i,j)['rho']
im=a.imshow(M,cmap=DIV,vmin=-.85,vmax=.85,aspect='equal')
for i in range(7):
    a.add_patch(Rectangle((i-.5,i-.5),1,1,fc='#F2F3F4',ec=SURF,lw=2.4,zorder=4))
    for j in range(7):
        if i==j: continue
        d=par(i,j); est='**' if d['ph']<.01 else ('*' if d['ph']<.05 else '')
        a.text(j,i,f"{vg(d['rho'],2)}{est}",ha='center',va='center',fontsize=9.4,
               color='white' if abs(d['rho'])>.55 else INK,
               fontweight='bold' if est else 'normal')
a.set_xticks(range(7)); a.set_xticklabels(L7,fontsize=9.8,rotation=40,ha='right')
a.set_yticks(range(7)); a.set_yticklabels(L7,fontsize=9.8)
for t,k in zip(a.get_xticklabels(),V7): t.set_color(CV[k]); t.set_fontweight('bold')
for t,k in zip(a.get_yticklabels(),V7): t.set_color(CV[k]); t.set_fontweight('bold')
a.set_xticks(np.arange(8)-.5,minor=True); a.set_yticks(np.arange(8)-.5,minor=True)
a.grid(which='minor',color=SURF,lw=2.4); a.tick_params(which='minor',length=0)
for sp in a.spines.values(): sp.set_visible(False)
a.set_title('(A) Correlação de Spearman entre as subescalas',fontsize=12,loc='left',fontweight='bold',pad=24)
a.annotate('* Holm p < 0,05      ** Holm p < 0,01',xy=(1.0,1.012),xycoords='axes fraction',
           ha='right',va='bottom',fontsize=9,color=MUT,style='italic')
cax=a.inset_axes([1.045,0.0,0.035,1.0])
cb=fig.colorbar(im,cax=cax); cb.set_label('ρ de Spearman',fontsize=9.8); cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=9)

a2=fig.add_subplot(gs[0,1])
pares=[(3,4),(3,6),(4,6),(0,2),(1,2),(1,5),(3,5),(4,5),(0,1),(0,3)]
nomes=[f'{L7[i]} × {L7[j]}' for i,j in pares]
wb=np.array([parD(i,j)['between'] for i,j in pares])
ww=np.array([parD(i,j)['within'] for i,j in pares])
pw=np.array([parD(i,j)['pw'] for i,j in pares]); pb=np.array([parD(i,j)['pb'] for i,j in pares])
yb=np.arange(len(pares))[::-1]
a2.axvline(0,color='#4A5257',lw=1.4,zorder=4)
a2.barh(yb+.19,wb,height=.34,color='#2166AC',alpha=.90,zorder=3,label='entre atletas (traço)')
a2.barh(yb-.19,ww,height=.34,color='#E0952B',alpha=.90,zorder=3,label='dentro do atleta (estado)')
for i_ in range(len(pares)):
    for v,off,pp,cc in [(wb[i_],.19,pb[i_],'#2166AC'),(ww[i_],-.19,pw[i_],'#E0952B')]:
        a2.annotate(vg(v,2)+('*' if pp<.05 else ''),xy=(v,yb[i_]+off),
                    xytext=(6 if v>=0 else -6,0),textcoords='offset points',
                    ha='left' if v>=0 else 'right',va='center',fontsize=9,
                    fontweight='bold' if pp<.05 else 'normal',color=cc)
a2.set_yticks(yb); a2.set_yticklabels(nomes,fontsize=9.6)
a2.set_xlim(-1.08,1.08); a2.set_ylim(-1.3,len(pares)-.3)
a2.set_xlabel('ρ de Spearman',fontsize=11)
a2.set_title('(B) Decomposição entre atletas e dentro do atleta',fontsize=12,loc='left',fontweight='bold')
a2.legend(fontsize=9.8,frameon=False,loc='lower center',ncol=2,bbox_to_anchor=(.5,-.005))
a2.grid(axis='x',color=GRID,lw=.8,zorder=0); a2.set_axisbelow(True)

a3=fig.add_subplot(gs[1,0])
au=[B2['AUTO'][k]['rho'] for k in V7]
yb3=np.arange(7)[::-1]
a3.barh(yb3,au,height=.55,color=[CV[k] for k in V7],alpha=.90,zorder=3)
for i_,k in enumerate(V7):
    a3.annotate(vg(au[i_],2),xy=(au[i_],yb3[i_]),xytext=(7,0),textcoords='offset points',
                va='center',fontsize=10,fontweight='bold',color=CV[k])
a3.set_yticks(yb3); a3.set_yticklabels(L7,fontsize=10)
for t,k in zip(a3.get_yticklabels(),V7): t.set_color(CV[k]); t.set_fontweight('bold')
a3.set_xlim(0,1.02); a3.set_xlabel('ρ entre o dia t e o dia t + 1',fontsize=11)
a3.set_title('(C) Persistência dia a dia — autocorrelação de defasagem 1',
             fontsize=12,loc='left',fontweight='bold')
a3.grid(axis='x',color=GRID,lw=.8,zorder=0); a3.set_axisbelow(True)
a3.annotate('todas as sete autocorrelações são significativas (p < 0,001): o humor de um dia prediz o do dia seguinte',
            xy=(.5,-.19),xycoords='axes fraction',ha='center',va='top',fontsize=9.2,color=MUT,
            style='italic')

a4=fig.add_subplot(gs[1,1])
CR=B2['CROSS']; kk=list(CR.keys())
yb4=np.arange(len(kk))[::-1]
cor4=[CV[k.split('→')[0]] for k in kk]
a4.axvline(0,color='#4A5257',lw=1.4,zorder=4)
a4.barh(yb4,[CR[k]['rho'] for k in kk],height=.55,color=cor4,alpha=.42,
        edgecolor=cor4,lw=1.8,zorder=3)
for i_,k in enumerate(kk):
    v=CR[k]['rho']
    a4.annotate(f"{vg(v,2)}  ({pv(CR[k]['p'])})",xy=(v,yb4[i_]),
                xytext=(7 if v>=0 else -7,0),textcoords='offset points',
                ha='left' if v>=0 else 'right',va='center',fontsize=9.4,color=MUT)
a4.set_yticks(yb4)
a4.set_yticklabels([k.replace('TMD','PTH') for k in kk],fontsize=10)
a4.set_xlim(-.42,.42); a4.set_xlabel('ρ parcial defasado (controlado pelo valor anterior do desfecho)',fontsize=10.4)
a4.set_title('(D) Precedência temporal entre variáveis',fontsize=12,loc='left',fontweight='bold')
a4.grid(axis='x',color=GRID,lw=.8,zorder=0); a4.set_axisbelow(True)
a4.annotate('nenhuma direção alcança significância: a estrutura é\nde covariação simultânea, não de precedência causal',
            xy=(.5,-.185),xycoords='axes fraction',ha='center',va='top',fontsize=9.4,color=INK,linespacing=1.45,
            bbox=dict(boxstyle='round,pad=.45',fc='#F7F8F8',ec='#8A9299',lw=1.2))
fig.suptitle('Como as variáveis do BRUMS se associam ao longo do ciclo',
             fontsize=13.5,fontweight='bold',x=.011,ha='left',y=.995)
fig.text(.011,-.045,'166 pares atleta-dia (painéis A e B); 133 pares de dias consecutivos (painéis C e D). '
         'A decomposição separa a covariação estável entre atletas da covariação diária dentro de cada atleta.',
         fontsize=8.8,color=MUT,style='italic')
fig.savefig(f"{SAIDA}/E9fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E9 ok")
