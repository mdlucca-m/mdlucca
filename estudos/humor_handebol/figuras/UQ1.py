# -*- coding: utf-8 -*-
"""Q1 a Q4 — qualidade dos dados e otimização da carga."""
exec(open(__file__.replace('UQ1.py','UVh.py')).read())
QQ=json.load(open(f"{S}/V2_qual.json")); OT=json.load(open(f"{S}/V2_otim.json"))
CF=json.load(open(f"{S}/V2_conf.json"))
UNI={u['variavel']:u for u in QQ['UNI']}

# ---------------- Q1: caixa e bigodes das sete variáveis do BRUMS ----------------
import importlib.util, io, contextlib
spec=importlib.util.spec_from_file_location("v2q", os.path.join(RAIZ,"analise","V2_qual.py"))
mq=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(mq)
DENTRO=mq.DENTRO
fig,axs=plt.subplots(1,3,figsize=(14.2,4.6),gridspec_kw=dict(width_ratios=[1.10,.26,1.00],wspace=.30))
a=axs[0]
dados=[[x['calc'][v] for x in DENTRO] for v in SUB]
bp=a.boxplot(dados, vert=True, widths=.55, patch_artist=True, showfliers=True,
             flierprops=dict(marker='o',ms=3.4,mfc='none',mec='#B3341A',alpha=.55),
             medianprops=dict(color=SURF,lw=1.8), whiskerprops=dict(color=MUT,lw=1.1),
             capprops=dict(color=MUT,lw=1.1))
for p,v in zip(bp['boxes'],SUB): p.set(facecolor=CV[v],alpha=.78,lw=0)
for i,v in enumerate(SUB):
    u=UNI[v]
    a.text(i+1, 16.9, f"n={u['n_tukey_moderado']}", ha='center', fontsize=8.4,
           color='#B3341A' if u['n_tukey_moderado']>20 else MUT)
a.set_xticks(range(1,7)); a.set_xticklabels(SUB, fontsize=9.6, rotation=18, ha='right')
a.set_ylim(-1,18.6); a.set_yticks(range(0,17,4)); a.set_ylabel('escore bruto (0 a 16)'); gy(a)
a.set_title('a) Seis subescalas do BRUMS, na escala comum de 0 a 16', fontsize=10.6, loc='left',
            pad=8, fontweight='bold')

ap=axs[1]
bp2=ap.boxplot([[x['calc']['TMD'] for x in DENTRO]], widths=.5, patch_artist=True, showfliers=True,
    flierprops=dict(marker='o',ms=3.4,mfc='none',mec='#B3341A',alpha=.55),
    medianprops=dict(color=SURF,lw=1.8), whiskerprops=dict(color=MUT,lw=1.1), capprops=dict(color=MUT,lw=1.1))
bp2['boxes'][0].set(facecolor=CV['TMD'],alpha=.82,lw=0)
ap.text(1, 56, f"n={UNI['TMD']['n_tukey_moderado']}", ha='center', fontsize=8.4, color=MUT)
ap.set_xticks([1]); ap.set_xticklabels(['PTH'], fontsize=9.6)
ap.set_ylim(-18,62); ap.set_ylabel('escore composto (−16 a 80)'); gy(ap)
ap.set_title('b) PTH,\n    escala própria', fontsize=10.6, loc='left', pad=8, fontweight='bold')

b=axs[2]
ordem=[v for v in V7]
mod=[UNI[v]['n_tukey_moderado'] for v in ordem]
ext=[UNI[v]['n_tukey_extremo'] for v in ordem]
y=np.arange(len(ordem))[::-1]
b.barh(y, mod, height=.56, color='#E0952B', label='cerca de 1,5 × IQR', zorder=3)
b.barh(y, ext, height=.30, color='#B3341A', label='cerca de 3,0 × IQR', zorder=4)
for yy,v,m in zip(y,ordem,mod):
    b.text(m+2, yy, f"{m}  ({100*m/UNI[v]['n']:.1f}%)", va='center', fontsize=9, color=INK)
    if UNI[v]['iqr_nulo']:
        b.text(m+31, yy, '← IQR = 0', va='center', fontsize=8.8, color='#B3341A', style='italic')
b.set_yticks(y); b.set_yticklabels([L(v) for v in ordem], fontsize=10)
b.set_xlim(0,132); b.set_xlabel('registros classificados como discrepantes'); gx(b)
b.spines['left'].set_visible(False); b.tick_params(axis='y',length=0)
b.legend(frameon=False, fontsize=9, loc='lower right', bbox_to_anchor=(1.0,-.02))
b.set_title('c) A cerca de Tukey aplicada a subescala com piso:\n'
            '    quando o IQR é zero, a regra rotula 20% da amostra',
            fontsize=10.6, loc='left', pad=8, fontweight='bold')
rod(fig,'Nível de registro, n = 456. Nenhum valor cai fora do domínio admissível de nenhuma escala. '
        'Em Confusão o primeiro e o terceiro quartis coincidem no piso,\nde modo que a cerca de Tukey passa a '
        'sinalizar toda resposta diferente de zero — o critério é inaplicável, e não há 89 erros de digitação.',y=-.02)
salvar(fig,'Q1fig')

# ---------------- Q2: completude ----------------
fig,axs=plt.subplots(1,2,figsize=(13.4,4.0),gridspec_kw=dict(width_ratios=[1,1.15],wspace=.26))
a=axs[0]
G=QQ['GRADE']; x=np.arange(1,8)
marcar(a)
a.plot(x,[g['cobertura_atleta'] for g in G],'-o',color='#2166AC',lw=2.4,ms=8,mec=SURF,mew=1.6,
       label='atletas com ao menos um registro', zorder=4)
a.plot(x,[min(g['cobertura_registro'],200) for g in G],'-s',color='#C1440E',lw=2.4,ms=7,mec=SURF,mew=1.6,
       label='registros contra o previsto no protocolo', zorder=4)
a.axhline(100,color=MUT,lw=1.2,ls=(0,(4,3)))
a.text(7.35,100,'protocolo',fontsize=8.4,color=MUT,va='center')
for g in G:
    yv=min(g['cobertura_registro'],200)
    a.annotate(f"{g['cobertura_registro']:.0f}%", (g['dia'],yv), textcoords='offset points',
               xytext=(0, 9 if yv>=105 else -19), ha='center', fontsize=8.2, color='#C1440E')
a.set_xticks(x); a.set_xticklabels([f"D{d}" for d in x]); a.set_ylim(60,200)
a.set_ylabel('% do previsto'); gy(a); a.legend(frameon=False,fontsize=9,loc='upper right')
a.set_title('a) Cobertura da grade atleta × dia', fontsize=10.6, loc='left', pad=8, fontweight='bold')

b=axs[1]
dist=QQ['REPETICAO']['distribuicao']
ks=sorted(dist, key=int); vs=[dist[k] for k in ks]
cores=['#87968F']+['#1A9070']+['#E0952B']*(len(ks)-2)
bars=b.bar(range(len(ks)), vs, color=cores[:len(ks)], width=.66, zorder=3)
for i,(k,v) in enumerate(zip(ks,vs)):
    b.text(i, v+1.4, f"{v}\n{100*v/sum(vs):.0f}%", ha='center', fontsize=9, color=INK, linespacing=1.25)
b.set_xticks(range(len(ks))); b.set_xticklabels([f"{k}" for k in ks])
b.set_xlabel('registros no mesmo par atleta-dia'); b.set_ylabel('pares atleta-dia')
b.set_ylim(0,max(vs)*1.30); gy(a); gy(b)
b.axvline(1.5,color='#B3341A',lw=1.4,ls=(0,(4,3)))
b.text(1.58,max(vs)*1.16,'o protocolo previa\naté dois por dia',fontsize=8.6,color='#B3341A',
       va='top',linespacing=1.35)
b.set_title('b) Quantos registros cada atleta enviou por dia', fontsize=10.6, loc='left', pad=8, fontweight='bold')
rod(fig,'Completude dos itens do instrumento: 100,00% — nenhuma célula ausente em 20.108 itens respondidos. '
        'A falta não está no item, e sim no comparecimento:\nde D4 em diante entre 78% e 85% do elenco registra no dia. '
        f"Em {sum(v for k,v in dist.items() if int(k)>2)} pares atleta-dia houve mais de dois envios.",y=-.04)
salvar(fig,'Q2fig')

# ---------------- Q3: a resposta dose-humor e a solução ótima ----------------
M=OT['MODELO']; OB=OT['OBSERVADO']; P1=OT['PROGRAMA_I']
fig,axs=plt.subplots(1,2,figsize=(13.6,4.6),gridspec_kw=dict(width_ratios=[1,1.18],wspace=.26))
a=axs[0]
vs=['Fadiga','Vigor','TMD','Tensão']; y=np.arange(len(vs))[::-1]
for i,(yy,v) in enumerate(zip(y,vs)):
    for k,(b,se,p,dx,mk) in enumerate([('b1',M[v]['se1'],M[v]['p1'],+.17,'o'),
                                       ('b2',M[v]['se2'],M[v]['p2'],-.17,'s')]):
        c='#2166AC' if k==0 else '#C1440E'
        val=M[v][b]
        a.plot([val-1.96*se,val+1.96*se],[yy+dx]*2,color=c,lw=2.2,alpha=.42,solid_capstyle='round')
        a.plot([val],[yy+dx],mk,ms=8,color=c,mec=SURF,mew=1.6,
               alpha=1.0 if p<.05 else .38)
        a.text(val, yy+dx+.145, f"{vg(val,3)}"+("" if p<.05 else " n.s."), ha='center',
               fontsize=8.4, color=c if p<.05 else MUT)
a.axvline(0,color=MUT,lw=1.3)
a.set_yticks(y); a.set_yticklabels([L(v) for v in vs], fontsize=10.5)
a.set_xlabel('variação do escore por hora de treino (IC 95%)'); gx(a)
a.spines['left'].set_visible(False); a.tick_params(axis='y',length=0)
a.legend(handles=[Line2D([],[],marker='o',ls='',color='#2166AC',ms=8,label='β₁ · horas do próprio dia'),
                  Line2D([],[],marker='s',ls='',color='#C1440E',ms=8,label='β₂ · horas da véspera')],
         frameon=False, fontsize=9, ncol=2, loc='lower left', bbox_to_anchor=(0,1.005))
a.set_title('a) O humor do dia responde à véspera, não ao próprio dia',
            fontsize=10.6, loc='left', pad=26, fontweight='bold')

b=axs[1]
x=np.arange(1,8); larg=.38
marcar(b,alpha=.55)
b.bar(x-larg/2, OB['horas'], larg, color='#87968F', label='calendário observado', zorder=3)
b.bar(x+larg/2, P1['horas'], larg, color='#0F6E5C', label='distribuição ótima (mesmas 23 h)', zorder=3)
for d in range(1,8):
    b.text(d+larg/2, P1['horas'][d-1]+.12, f"{vg(P1['horas'][d-1],1)}", ha='center', fontsize=8.4, color='#0F6E5C')
    b.text(d-larg/2, OB['horas'][d-1]+.12, f"{vg(OB['horas'][d-1],1)}", ha='center', fontsize=8.4, color=MUT)
b.set_xticks(x)
b.set_xticklabels([(f"D{d}\namistoso" if d in (3,5) else f"D{d}") for d in x])
for t,d in zip(b.get_xticklabels(),x):
    if d in (3,5): t.set_color('#2166AC'); t.set_fontweight('bold')
b.set_ylim(0,5.9); b.set_ylabel('horas de treino'); gy(b)
b.legend(frameon=False, fontsize=9, ncol=2, loc='lower left', bbox_to_anchor=(0,1.005))
b.set_title(f"b) Mesma carga, arranjo que maximiza o pior dia de vigor  ·  "
            f"pior dia {vg(OB['vigor_minimo'],2)} → {vg(P1['vigor_minimo_garantido'],2)}",
            fontsize=10.6, loc='left', pad=26, fontweight='bold')
rod(fig,'Modelo misto com intercepto aleatório por atleta, 166 pares. O coeficiente das horas da véspera é '
        'significativo para fadiga, vigor e PTH; o das horas do próprio dia não é.\nO programa linear usa essa '
        'defasagem: a restrição de recuperação do dia d incide sobre a carga do dia d − 1.',y=-.02)
salvar(fig,'Q3fig')

# ---------------- Q4: fronteira eficiente e preços-sombra ----------------
FR=[f for f in OT['FRONTEIRA'] if f.get('viavel') is not False]
INV=[f for f in OT['FRONTEIRA'] if f.get('viavel') is False]
fig,axs=plt.subplots(1,2,figsize=(14.4,4.4),gridspec_kw=dict(width_ratios=[1,1.10],wspace=.44))
a=axs[0]
cx_=[f['carga'] for f in FR]; cy=[f['vigor_minimo'] for f in FR]
a.plot(cx_,cy,'-o',color='#0F6E5C',lw=2.4,ms=8,mec=SURF,mew=1.6,zorder=4)
if INV:
    lim=OT['CARGA_MINIMA_ESTRUTURAL']
    a.axvspan(min(f['carga'] for f in INV)-1, lim, color='#FBEDE7', zorder=0)
    a.axvline(lim,color='#B3341A',lw=1.6,ls=(0,(4,3)),zorder=2)
    a.text(lim-.4, np.mean(cy), f'inviável abaixo de\n{vg(lim,2)} h', ha='right', va='center',
           fontsize=8.8, color='#B3341A', linespacing=1.35)
a.plot([OB['total']],[OB['vigor_minimo']],'D',ms=10,color='#87968F',mec=SURF,mew=1.6,zorder=5)
a.annotate('calendário observado', (OB['total'],OB['vigor_minimo']), textcoords='offset points',
           xytext=(-12,10), ha='right', fontsize=8.8, color=MUT)
a.set_xlabel('carga da semana (horas)'); a.set_ylabel('pior dia de vigor previsto'); gy(a); gx(a)
a.set_title('a) Fronteira eficiente: o que a semana custa em vigor',
            fontsize=10.6, loc='left', pad=8, fontweight='bold')

b=axs[1]
# a restrição «vigor ≥ t» é a própria definição do objetivo maximin: preço-sombra 1 por construção,
# e nada a afrouxar. Fica de fora do gráfico das restrições acionáveis.
CURTO=lambda r: (r.replace('polimento: ','polimento ').replace(' pelo calendário','')
                  .replace('fixado em ','fixo em ').replace('previsto ','').replace('.',','))
R=sorted([r for r in OT['ATIVAS'] if '≥ t' not in r['restricao']]
         +[dict(restricao=e['restricao'],preco_sombra=e['preco_sombra'],folga=None) for e in OT['EQ']],
         key=lambda r:-abs(r['preco_sombra']))[:6]
y=np.arange(len(R))[::-1]
cores=['#B3341A' if r['preco_sombra']<0 else '#0F6E5C' for r in R]
b.barh(y,[r['preco_sombra'] for r in R], height=.58, color=cores, zorder=3)
for yy,r in zip(y,R):
    v=r['preco_sombra']
    b.text(v+(.008 if v>=0 else -.008), yy, vg(v,3), va='center', ha='left' if v>=0 else 'right',
           fontsize=9, color=INK)
b.axvline(0,color=MUT,lw=1.3)
b.set_yticks(y); b.set_yticklabels([CURTO(r['restricao']) for r in R], fontsize=9)
b.set_xlim(-.58,.14); b.set_xlabel('preço-sombra, em pontos do pior dia de vigor'); gx(b)
b.spines['left'].set_visible(False); b.tick_params(axis='y',length=0)
b.set_title('b) Quem segura a solução, entre as restrições acionáveis', fontsize=10.6, loc='left', pad=8, fontweight='bold')
rod(fig,'O preço-sombra é a variação do pior dia de vigor por unidade de afrouxamento da restrição. '
        'O maior valor absoluto é o do amistoso de D5:\ncada hora daquele jogo custa '
        f"{vg(abs([e for e in OT['EQ'] if e['restricao'].startswith('D5')][0]['preco_sombra']),3)} ponto do pior dia da semana. "
        'Quem comprime o microciclo é o calendário de jogos, não o treino.',y=-.02)
salvar(fig,'Q4fig')
