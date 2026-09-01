# -*- coding: utf-8 -*-
"""P7 e P8 — o filtro e a anatomia dos cruzamentos.

P7 responde à pergunta do que a suavização remove e com que direito: a
resposta em frequência do núcleo, a série antes e depois, e o resíduo lido
contra o piso de ruído da própria série.
P8 abre cada cruzamento em três camadas: as duas séries, a diferença contra o
limiar combinado com a zona de indecisão, e as duas derivadas da diferença.
"""
exec(open(__file__.replace('UP3.py','UVh.py')).read())
CZ=json.load(open(f"{S}/V2_cruz.json"))
FIL=CZ['FILTRO']; RESP=CZ['RESPOSTA']; CRUZ=CZ['CRUZ']
VAR=['Vigor','Fadiga','TMD']
CURTOEST={'Basal':'basal','HIIT':'HIIT','Amistoso':'amist.','Técnico/força':'téc/for'}

# ================= P7: o filtro, o ruído e o sinal =================
fig=plt.figure(figsize=(15.0,8.4))
gs=fig.add_gridspec(2,3,height_ratios=[1,1],hspace=.46,wspace=.24,
                    left=.050,right=.988,top=.870,bottom=.135)

# a) resposta em frequência
a=fig.add_subplot(gs[0,0])
w=np.array(RESP['w']); H=np.array(RESP['H']); HM=np.array(RESP['H_media_movel'])
a.axhline(0,color=MUT,lw=1.0,zorder=2)
a.fill_between(w/np.pi, 0, H, color='#2166AC', alpha=.14, lw=0, zorder=2)
a.plot(w/np.pi, H, '-', lw=3.0, color='#2166AC', zorder=5, label='binomial 1-2-1')
a.plot(w/np.pi, HM, lw=2.0, color='#B3341A', ls=(0,(4,3)), zorder=4,
       label='média móvel 1-1-1')
a.plot([1],[0],'o',ms=11,mfc=SURF,mec='#2166AC',mew=2.4,zorder=7)
a.annotate('anula-se em Nyquist:\na oscilação de um dia para o\noutro é removida por construção',
           xy=(1,0), xytext=(.40,-.30), ha='center', va='center', fontsize=8.8,
           color='#2166AC', fontweight='bold', zorder=8,
           arrowprops=dict(arrowstyle='->', color='#2166AC', lw=1.2,
                           connectionstyle='arc3,rad=-.25', shrinkB=8),
           bbox=dict(fc=SURF, ec='none', alpha=.9, pad=2))
a.set_xticks([0,.25,.5,.75,1]); a.set_xticklabels(['0','π/4','π/2','3π/4','π'])
a.set_xlabel('frequência ω'); a.set_ylabel('ganho H(ω)')
a.set_ylim(-.42,1.10); gy(a)
a.legend(frameon=False, fontsize=9.0, loc='upper right', bbox_to_anchor=(1.01,1.02))
a.set_title('a) O que o núcleo [¼, ½, ¼] deixa passar',
            fontsize=11.2, loc='left', pad=10, fontweight='bold')

# b) observado contra suavizado
b=fig.add_subplot(gs[0,1:]); marcar(b,alpha=.85)
for v in VAR:
    ob=np.array(FIL[v]['observado']); sm=np.array(FIL[v]['suavizado'])
    b.plot(x7, ob, 'o--', ms=5.4, lw=1.2, color=CV[v], alpha=.45, mec=SURF, mew=1.0, zorder=4)
    b.plot(x7, sm, '-', lw=3.2, color=CV[v], zorder=5)
    b.annotate(L(v), (7, sm[-1]), textcoords='offset points', xytext=(10,0),
               ha='left', va='center', fontsize=10.4, color=CV[v], fontweight='bold')
b.set_xticks(x7); b.set_xticklabels([f"D{d}\n{CURTOEST[TIPO[d]]}" for d in x7], fontsize=8.6)
b.set_xlim(.55,7.85); gy(b); b.set_ylabel('pontos da escala')
b.set_title('b) A série observada (pontilhada) e a suavizada (cheia)',
            fontsize=11.2, loc='left', pad=10, fontweight='bold')

# c) o resíduo do filtro, em unidades do piso
for i,v in enumerate(VAR):
    c=fig.add_subplot(gs[1,i])
    r=np.array(FIL[v]['residuo_em_pisos'])
    c.axhspan(-1,1,color=CV[v],alpha=.11,lw=0,zorder=1)
    c.axhline(0,color=INK,lw=1.2,zorder=3)
    for k in (1,-1):
        c.axhline(k,color=CV[v],lw=1.2,ls=(0,(4,3)),zorder=3)
    c.bar(x7, r, width=.55, color=CV[v], alpha=.85, zorder=4)
    c.set_xticks(x7); c.set_xticklabels([f"D{d}" for d in x7], fontsize=8.6)
    c.set_ylim(-2.1,2.1); c.set_yticks([-2,-1,0,1,2]); gy(c)
    if i==0: c.set_ylabel('resíduo ÷ piso de ruído')
    c.text(.02,.965, L(v), transform=c.transAxes, fontsize=10.6, fontweight='bold',
           color=CV[v], va='top')
    c.text(.02,.875, f"piso {vg(FIL[v]['piso'])}  ·  maior resíduo "
                     f"{vg(FIL[v]['max_residuo_em_pisos'])} piso",
           transform=c.transAxes, fontsize=8.6, color=MUT, va='top')
    if i==1:
        c.set_title('c) O que foi removido, lido contra o piso de ruído de cada série',
                    fontsize=11.2, loc='center', pad=10, fontweight='bold')
fig.suptitle('O filtro, o ruído e o sinal: o que a suavização remove e com que direito',
             fontsize=12.8, fontweight='bold', x=.006, ha='left', y=.972)
rod(fig,'Painel a: ganho do filtro por frequência. O núcleo binomial anula-se exatamente na frequência de '
        'Nyquist, ω = π, que corresponde à componente que alterna a cada dia; a média móvel simples não se '
        'anula ali e ainda\ninverte o sinal de parte da banda alta, o que a torna imprópria para série diária. '
        'Painel c: o resíduo é a diferença entre a série observada e a suavizada. A faixa sombreada marca uma '
        'unidade de piso de ruído para\ncima e para baixo: o resíduo cabe nela em vinte das vinte e uma '
        'células, o que mostra que o filtro removeu componente da ordem do ruído amostral, e não sinal.', y=.098)
salvar(fig,'P7fig')

# ============ P8: a anatomia dos três cruzamentos ============
PARES=[tuple(p) for p in CZ['PARES']]
CPAR={('Vigor','Fadiga'):'#C1440E',('Vigor','TMD'):'#2166AC',('Fadiga','TMD'):'#8A4FBF'}
def suav(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z
SM={v:suav(FIL[v]['observado']) for v in VAR}

fig,axs=plt.subplots(3,3,figsize=(15.2,11.4))
fig.subplots_adjust(left=.055,right=.988,top=.878,bottom=.088,hspace=.46,wspace=.25)
for r,(u,wv) in enumerate(PARES):
    key=f"{u}×{wv}"; C=CRUZ[key]; co=CPAR[(u,wv)]
    d=np.array(C['dif']); lim=C['limiar']
    it=C['cruzamentos'][0]

    # --- coluna 1: as duas séries
    a=axs[r][0]
    a.axvspan(it['zona_ini'], it['zona_fim'], color=co, alpha=.10, lw=0, zorder=1)
    for v in (u,wv):
        a.plot(x7, FIL[v]['observado'], 'o', ms=4.6, color=CV[v], alpha=.40, mec=SURF, mew=.9, zorder=3)
        a.plot(x7, SM[v], '-', lw=2.9, color=CV[v], zorder=5)
        a.annotate(L(v), (7, SM[v][-1]), textcoords='offset points', xytext=(8,0),
                   ha='left', va='center', fontsize=9.6, color=CV[v], fontweight='bold')
    k=int(np.floor(it['abscissa']))-1; t=it['abscissa']-np.floor(it['abscissa'])
    yv=SM[u][k]+t*(SM[u][k+1]-SM[u][k])
    a.plot([it['abscissa']],[yv],'o',ms=12,mfc=SURF,mec=co,mew=2.4,zorder=8)
    a.set_xticks(x7); a.set_xticklabels([f"D{dd}" for dd in x7], fontsize=8.4)
    a.set_xlim(.55,7.95); gy(a); a.set_ylabel('pontos')
    a.text(0,1.10, f"{L(u)} × {L(wv)}", transform=a.transAxes, fontsize=11.4,
           fontweight='bold', color=co, va='bottom')
    if r==0: a.text(1,1.21,'as duas séries', transform=a.transAxes, fontsize=10.4,
                    ha='right', va='bottom', color=MUT)

    # --- coluna 2: a diferença contra o limiar
    b=axs[r][1]
    b.axvspan(it['zona_ini'], it['zona_fim'], color=co, alpha=.10, lw=0, zorder=1)
    b.fill_between([1,7], -lim, lim, color=GRID, alpha=.55, lw=0, zorder=2)
    for kk in (lim,-lim):
        b.plot([1,7],[kk,kk], color=MUT, lw=1.1, ls=(0,(4,3)), zorder=3)
    b.axhline(0,color=INK,lw=1.3,zorder=4)
    b.plot(x7, d, '-', lw=3.0, color=co, zorder=6)
    b.plot(x7, d, 'o', ms=5.6, color=co, mec=SURF, mew=1.2, zorder=7)
    b.plot([it['abscissa']],[0],'o',ms=12,mfc=SURF,mec=co,mew=2.4,zorder=9)
    b.annotate(f"cruza em D{vg(it['abscissa'])}", (it['abscissa'],0), textcoords='offset points',
               xytext=(0,-26), ha='center', fontsize=8.8, color=co, fontweight='bold', zorder=10,
               bbox=dict(fc=SURF,ec=co,lw=.9,alpha=.95,boxstyle='round,pad=.26'))
    b.annotate(f"zona de indecisão\nD{vg(it['zona_ini'])} a D{vg(it['zona_fim'])}  ·  "
               f"{vg(it['zona_largura'])} dia",
               xy=(min(max((it['zona_ini']+it['zona_fim'])/2, 2.2), 5.8), .965),
               xycoords=('data','axes fraction'),
               ha='center', va='top', fontsize=8.4, color=co, zorder=10,
               bbox=dict(fc=SURF,ec='none',alpha=.85,pad=1.4))
    b.set_xticks(x7); b.set_xticklabels([f"D{dd}" for dd in x7], fontsize=8.4)
    b.set_xlim(.55,7.45); gy(b); b.set_ylabel('diferença (pontos)')
    b.text(0,1.10, ('inversão estabelecida' if C['estabelecida'] else 'divergência')
           + f"   ·   limiar ±{vg(lim,2)}", transform=b.transAxes, fontsize=9.6,
           fontweight='bold' if C['estabelecida'] else 'normal',
           color=co if C['estabelecida'] else MUT, va='bottom')
    if r==0: b.text(1,1.21,'a diferença e o limiar', transform=b.transAxes, fontsize=10.4,
                    ha='right', va='bottom', color=MUT)

    # --- coluna 3: as duas derivadas da diferença
    c=axs[r][2]
    d1=np.array(C['d1_em_limiares']); d2=np.array(C['d2_em_limiares'])
    x1=np.arange(1,7)+.5; x2=np.arange(2,7)
    c.axhline(0,color=INK,lw=1.2,zorder=4)
    for kk in (1,-1): c.axhline(kk,color=GRID,lw=1.0,ls=(0,(3,3)),zorder=3)
    c.bar(x1-.13, d1, width=.26, color=co, alpha=.90, zorder=5, label='velocidade  Δ′')
    c.bar(x2+.13, d2, width=.26, color=co, alpha=.38, zorder=5, label='aceleração  Δ″')
    c.axvline(it['abscissa'], color=co, lw=1.4, ls=(0,(4,3)), zorder=6)
    c.text(0, 1.10, f"velocidade na travessia {vg(it['velocidade_em_limiares'])} limiar/dia   ·   "
           f"aceleração {vg(it['aceleracao_em_limiares'])} limiar/dia²",
           transform=c.transAxes, fontsize=8.8, color=co, va='bottom', fontweight='bold')
    c.text(0, 1.02, f"travessia {'nítida' if it['nitido'] else 'lenta em relação ao ruído'}",
           transform=c.transAxes, fontsize=8.8,
           color=co if it['nitido'] else MUT, va='bottom',
           fontweight='bold' if it['nitido'] else 'normal')
    c.set_xticks(x7); c.set_xticklabels([f"D{dd}" for dd in x7], fontsize=8.4)
    c.set_xlim(.55,7.45); gy(c); c.set_ylabel('em unidades do limiar')
    if r==0:
        c.text(1,1.21,'as duas derivadas', transform=c.transAxes, fontsize=10.4,
               ha='right', va='bottom', color=MUT)
        c.legend(frameon=False, fontsize=8.8, ncol=2, loc='upper right', bbox_to_anchor=(1.01,1.02))
fig.suptitle('Anatomia dos três cruzamentos: as séries, a diferença contra o limiar e as duas derivadas',
             fontsize=12.8, fontweight='bold', x=.006, ha='left', y=.982)
rod(fig,'Coluna 1: séries observadas (pontos) e suavizadas (linha), com o cruzamento assinalado. Coluna 2: a '
        'diferença entre as duas séries; a faixa cinzenta é o limiar combinado, definido como a raiz da soma '
        'dos quadrados dos dois pisos de ruído.\nA zona de indecisão, sombreada nas duas primeiras colunas, é '
        'o intervalo contíguo em que a diferença permanece dentro do limiar, isto é, em que as duas séries não '
        'se distinguem uma da outra. Coluna 3: primeira e\nsegunda derivadas da diferença, ambas divididas '
        'pelo limiar. A travessia é dita nítida quando a diferença atravessa o zero a pelo menos um limiar por '
        'dia; abaixo disso, a data do cruzamento é mal determinada.', y=.062)
salvar(fig,'P8fig')

# ============ P9: as quatro decomposições ============
DC=json.load(open(f"{S}/V2_decomp.json"))
COMP=DC['COMPONENTES']; SER=DC['SERIE']; DES=DC['DESLOCAMENTO']; FI=DC['FILTRO']
VV=DC['V7']; ROT=[L(v) for v in VV]
yy=np.arange(len(VV))[::-1]
C_ATL='#2166AC'; C_DIA='#C1440E'; C_RES='#B8BEC3'
C_VER='#1A9070'; C_ERR='#D8DCDF'; C_CHO='#8A4FBF'; C_DER='#CBD1D6'

fig=plt.figure(figsize=(15.2,9.0))
gs=fig.add_gridspec(2,2,hspace=.52,wspace=.30,left=.088,right=.988,top=.860,bottom=.140)

# --- A) componentes de variância
a=fig.add_subplot(gs[0,0])
base=np.zeros(len(VV))
for chave,cor,rot in [('p_atleta',C_ATL,'entre atletas'),('p_dia',C_DIA,'entre dias'),
                      ('p_residual',C_RES,'residual')]:
    val=np.array([COMP[v][chave] for v in VV])
    a.barh(yy, val, left=base, height=.62, color=cor, zorder=3, label=rot)
    for i,x in enumerate(val):
        if x>=6: a.text(base[i]+x/2, yy[i], vg(x,0)+'%', ha='center', va='center',
                        fontsize=8.4, color=SURF if cor!=C_RES else INK, fontweight='bold', zorder=5)
    base=base+val
a.set_yticks(yy); a.set_yticklabels(ROT, fontsize=9.6); a.set_xlim(0,100)
a.set_xlabel('% da variância total'); gx(a)
a.legend(frameon=False, fontsize=8.8, ncol=3, loc='upper left', bbox_to_anchor=(-.005,1.20))
a.set_title('a) De onde vem a variância do par atleta-dia',
            fontsize=11.2, loc='left', pad=32, fontweight='bold')

# --- B) série diária: verdadeiro contra erro
b=fig.add_subplot(gs[0,1])
vv=np.array([SER[v]['var_verdadeira'] for v in VV])
ve=np.array([SER[v]['var_erro'] for v in VV])
tot=np.maximum(vv+ve,1e-9)
b.barh(yy, 100*vv/tot, height=.62, color=C_VER, zorder=3, label='variação verdadeira')
b.barh(yy, 100*ve/tot, left=100*vv/tot, height=.62, color=C_ERR, ec=MUT, lw=.7, zorder=3,
       label='erro de amostragem')
for i,v in enumerate(VV):
    f=SER[v]['fidedignidade']
    b.text(101, yy[i], ('fid. '+vg(f,2)) if f>0 else 'fid. nula', va='center',
           fontsize=8.6, color=C_VER if f>=.5 else MUT, fontweight='bold' if f>=.5 else 'normal')
b.set_yticks(yy); b.set_yticklabels(ROT, fontsize=9.6); b.set_xlim(0,128)
b.set_xticks([0,25,50,75,100]); b.set_xlabel('% da variância das sete médias diárias'); gx(b)
b.legend(frameon=False, fontsize=8.8, ncol=2, loc='upper left', bbox_to_anchor=(-.005,1.20))
b.set_title('b) Quanto da variação diária sobreviveria à medida sem erro',
            fontsize=11.2, loc='left', pad=32, fontweight='bold')

# --- C) deslocamento: choque contra deriva
c=fig.add_subplot(gs[1,0])
for i,v in enumerate(VV):
    d=DES[v]
    c.barh(yy[i]+.17, d['choque'], height=.32, color=C_CHO, zorder=3,
           label='de choque' if i==0 else None)
    c.barh(yy[i]-.17, d['deriva'], height=.32, color=C_DER, ec=MUT, lw=.7, zorder=3,
           label='de deriva' if i==0 else None)
    c.text(9.1, yy[i], f"{d['n_choques']} choque" + ('s' if d['n_choques']!=1 else ''),
           va='center', fontsize=8.4, color=C_CHO if d['n_choques'] else MUT,
           fontweight='bold' if d['n_choques'] else 'normal')
c.axvline(0,color=INK,lw=1.2,zorder=4)
c.set_yticks(yy); c.set_yticklabels(ROT, fontsize=9.6); c.set_xlim(-5.6,11.4)
c.set_xlabel('pontos da escala'); gx(c)
c.legend(frameon=False, fontsize=8.8, ncol=2, loc='upper left', bbox_to_anchor=(-.005,1.20))
c.set_title('c) O deslocamento da semana, separado em choque e deriva',
            fontsize=11.2, loc='left', pad=32, fontweight='bold')

# --- D) o filtro: identidade da variância
d_=fig.add_subplot(gs[1,1])
w_=.26
for i,v in enumerate(VV):
    f=FI[v]; vo=f['var_observada']
    d_.barh(yy[i]+.27, 100*f['var_suavizada']/vo, height=w_, color='#2166AC', zorder=3,
            label='retida (suavizada)' if i==0 else None)
    d_.barh(yy[i], 100*f['var_residuo']/vo, height=w_, color='#E0952B', zorder=3,
            label='removida (resíduo)' if i==0 else None)
    d_.barh(yy[i]-.27, 200*f['covariancia']/vo, height=w_, color=MUT, alpha=.55, zorder=3,
            label='2 × covariância' if i==0 else None)
d_.axvline(0,color=INK,lw=1.2,zorder=4)
d_.axvline(100,color=MUT,lw=1.1,ls=(0,(4,3)),zorder=4)
d_.text(100,len(VV)-.35,' 100%',fontsize=8.4,color=MUT,va='center')
d_.set_yticks(yy); d_.set_yticklabels(ROT, fontsize=9.6); d_.set_xlim(-32,120)
d_.set_xlabel('% da variância observada da série'); gx(d_)
d_.legend(frameon=False, fontsize=8.8, ncol=3, loc='upper left', bbox_to_anchor=(-.005,1.20))
d_.set_title('d) A identidade do filtro: retida + removida + 2·cov = observada',
             fontsize=11.2, loc='left', pad=32, fontweight='bold')

fig.suptitle('Quatro decomposições da variação do humor no microciclo',
             fontsize=12.8, fontweight='bold', x=.006, ha='left', y=.975)
rod(fig,'Painel a: componentes de variância de um modelo de efeitos aleatórios cruzados, atleta e dia, '
        'ajustado por máxima verossimilhança restrita sobre os 166 pares atleta-dia. Painel b: a variância '
        'observada entre as sete médias\ndiárias contém a variação verdadeira mais a média dos erros-padrão ao '
        'quadrado; subtraída a segunda parcela, resta a primeira, e a razão entre ela e o total é a '
        'fidedignidade da série. Painel c: as seis transições da série\nsuavizada são separadas conforme '
        'superem ou não o piso de ruído. Painel d: as duas parcelas do filtro não são ortogonais, e por isso a '
        'covariância entra na identidade em vez de ser omitida; onde ela é negativa, a\nparcela retida excede '
        'a variância observada.', y=.098)
salvar(fig,'P9fig')
