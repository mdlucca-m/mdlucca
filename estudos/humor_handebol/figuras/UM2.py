# -*- coding: utf-8 -*-
"""M3 e M4 — organograma do processo e framework do estudo de modelagem."""
exec(open(__file__.replace('UM2.py','UVh.py')).read())
QA=json.load(open(f"{S}/V2_qual.json")); CF=json.load(open(f"{S}/V2_conf.json"))
ML=json.load(open(f"{S}/V2_ml.json")); ML2=json.load(open(f"{S}/V2_ml2.json"))
ML3=json.load(open(f"{S}/V2_ml3.json")); OT=json.load(open(f"{S}/V2_otim.json"))
TEJ=json.load(open(f"{S}/V2_te.json"))

def caixa(a, x, y, w, h, titulo, linhas, cor, fs=8.6, ft=9.4, alpha=.10):
    a.add_patch(FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.006,rounding_size=0.012',
                fc=cor, ec=cor, lw=1.6, alpha=1, zorder=3, mutation_aspect=1))
    a.add_patch(FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.006,rounding_size=0.012',
                fc=SURF, ec='none', zorder=4))
    a.add_patch(FancyBboxPatch((x,y), w, h, boxstyle='round,pad=0.006,rounding_size=0.012',
                fc=cor, ec=cor, lw=1.6, alpha=alpha, zorder=5))
    nlin=titulo.count('\n')+1
    a.text(x+w/2, y+h-0.030, titulo, ha='center', va='top', fontsize=ft, fontweight='bold',
           color=cor, zorder=6, linespacing=1.35)
    y0=y+h-0.030-0.040-(nlin-1)*0.036
    for i,l in enumerate(linhas):
        a.text(x+w/2, y0-i*0.033, l, ha='center', va='top', fontsize=fs, color=INK, zorder=6)
def seta(a, x1, y1, x2, y2, cor=MUT, lw=1.8, rad=0.0):
    a.add_patch(FancyArrowPatch((x1,y1),(x2,y2), arrowstyle='-|>', mutation_scale=13,
                color=cor, lw=lw, zorder=2, connectionstyle=f'arc3,rad={rad}',
                shrinkA=3, shrinkB=3))
def etapa(a, x, w, rot, cor):
    a.add_patch(Rectangle((x,0.955), w, 0.038, fc=cor, ec='none', alpha=.16, zorder=1))
    a.text(x+w/2, 0.974, rot, ha='center', va='center', fontsize=9.6, fontweight='bold', color=cor, zorder=2)

# ---------------- M3: organograma do processo ----------------
fig,a=plt.subplots(figsize=(15.6,8.2))
a.set_xlim(0,1); a.set_ylim(0,1); a.axis('off')
COL=[0.005,0.205,0.405,0.605,0.805]; W=0.185
ETP=[('1 · FONTE','#87968F'),('2 · LIMPEZA E AUDITORIA','#C1440E'),('3 · UNIDADES','#E0952B'),
     ('4 · PAREAMENTOS','#2166AC'),('5 · ANÁLISES E SAÍDAS','#0F6E5C')]
for (r,c),x in zip(ETP,COL): etapa(a,x,W,r,c)

nq=sum(c['n_comparado'] for c in QA['CONFRONTO'])
caixa(a, COL[0], 0.72, W, 0.20, 'Export do formulário',
      ['457 linhas · 79 colunas','24 itens do BRUMS','6 de Epworth · 14 da PSS',
       'fadiga física e mental, TQR'], '#87968F')
caixa(a, COL[0], 0.45, W, 0.17, 'Planejamento do microciclo',
      ['7 dias · 21 a 27/04/2024','4 tipos de estímulo','23,0 h acumuladas'], '#87968F', ft=9.0)
caixa(a, COL[0], 0.20, W, 0.17, 'Dicionário de atletas',
      ['variantes de grafia do nome','usado só para reconciliar','órfãos de identificação'], '#87968F')

caixa(a, COL[1], 0.70, W, 0.22, 'Auditoria de procedência',
      ['dia pelo carimbo, virada 4h','4 órfãos devolvidos','fonte-verdade fixada',
       'D1 a D6 registrados'], '#C1440E', ft=9.0)
caixa(a, COL[1], 0.41, W, 0.24, 'Auditoria de qualidade',
      [f'{nq:,} escores reconstruídos'.replace(',','.'),'0 divergência de fórmula','100% de completude no item',
       '0 valor fora do domínio'], '#C1440E', ft=9.0)
caixa(a, COL[1], 0.14, W, 0.22, 'Anonimização',
      ['A01 a A27 na importação','nenhum nome sai do script','raspagem verificada no acervo'], '#C1440E')

caixa(a, COL[2], 0.70, W, 0.22, 'As quatro unidades',
      ['U-R · 456 registros','U-286 · 285 pares','U-PAR · 143 pares',
       'U-AD · 166 ← adotada'], '#E0952B', ft=9.0)
caixa(a, COL[2], 0.41, W, 0.24, 'Por que a U-AD',
      ['um valor por atleta e dia','elimina pseudorreplicação','cada atleta pesa igual',
       '3 de 7 vereditos mudam'], '#E0952B', ft=9.0)
caixa(a, COL[2], 0.14, W, 0.22, 'Regras declaradas',
      ['valor diário = média do dia','pré = 1º · pós = último','nenhum registro descartado'], '#E0952B')

caixa(a, COL[3], 0.70, W, 0.22, 'Pareamentos',
      ['166 pares atleta-dia','119 pares manhã e noite','21 com D1 e D7',
       '19 completos nos 7 dias'], '#2166AC', ft=9.0)
caixa(a, COL[3], 0.41, W, 0.24, 'Separação temporal',
      ['preditor = medida da manhã','desfecho = faixa da noite','previsão não circular',
       'validação agrupada por atleta'], '#2166AC', ft=9.0)
caixa(a, COL[3], 0.14, W, 0.22, 'Limiares de leitura',
      ['piso de ruído do grupo','erro típico do atleta','menor mudança relevante',
       'mudança mínima ancorada'], '#2166AC')

caixa(a, COL[4], 0.70, W, 0.22, 'Três vias e séries',
      ['não paramétrica · paramétrica','modelo linear misto','piso, derivadas e choques',
       'teste formal de cruzamento'], '#0F6E5C', ft=9.0)
caixa(a, COL[4], 0.41, W, 0.24, 'Modelagem e otimização',
      ['árvore · floresta · XGBoost','2 linhas de base obrigatórias','diagnóstico de reversão',
       'programa linear da carga'], '#0F6E5C', ft=9.0)
caixa(a, COL[4], 0.14, W, 0.22, 'Saídas',
      ['3 documentos e 1 anexo','base única consultável','painel e automação'], '#0F6E5C')

for i in range(4):
    c=ETP[i+1][1]
    for yy in (0.81, 0.53, 0.25):
        seta(a, COL[i]+W+0.002, yy, COL[i+1]-0.002, yy, cor=c, lw=2.2)
seta(a, COL[0]+W*0.5, 0.72, COL[0]+W*0.5, 0.62, cor='#87968F', lw=1.4)
seta(a, COL[0]+W*0.5, 0.45, COL[0]+W*0.5, 0.37, cor='#87968F', lw=1.4)
a.add_patch(FancyArrowPatch((0.90,0.100),(0.10,0.100), arrowstyle='-|>', mutation_scale=15,
            color='#8A4FBF', lw=2.0, ls=(0,(6,3)), zorder=2, connectionstyle='arc3,rad=-0.03'))
a.text(0.5, 0.014, 'reconferência independente', ha='center', fontsize=9.6, color='#8A4FBF',
       fontweight='bold')
rod(fig, 'A reconferência fecha o circuito: todos os valores dos três documentos foram recalculados por um '
    f"segundo caminho de código, partindo do item do formulário — {CF['ok']} de {CF['total']} conferências coincidem.",
    y=.005)
fig.suptitle('Do formulário ao resultado: o processo completo de coleta, tratamento, pareamento e análise',
             fontsize=12.6, fontweight='bold', x=.005, ha='left', y=1.00)
plt.tight_layout(rect=[0,.02,1,.985])
salvar(fig,'M3fig')

# ---------------- M4: framework do estudo de modelagem ----------------
fig,a=plt.subplots(figsize=(15.0,6.9))
a.set_xlim(0,1); a.set_ylim(0,1); a.axis('off')
a.add_patch(Rectangle((0.02,0.695),0.96,0.29, fc='#F0F6F3', ec='#CDD6D2', lw=1.2, zorder=0))
a.text(0.03,0.968,'EIXO TEMPORAL DO DIA — a separação que torna a previsão não circular',
       fontsize=10.2, fontweight='bold', color='#0F6E5C', va='top')
caixa(a, 0.045, 0.725, 0.245, 0.20, 'MANHÃ · preditores',
      ['6 subescalas do BRUMS','PTH, fadiga física e mental','Epworth e estresse percebido',
       'já estava em risco?'], '#2166AC', ft=9.2)
caixa(a, 0.375, 0.725, 0.245, 0.20, 'DIA · estímulo',
      ['tipo: HIIT, amistoso, técnico','horas e carga acumulada','dia do microciclo'], '#E0952B', ft=9.2)
caixa(a, 0.705, 0.725, 0.245, 0.20, 'NOITE · desfecho',
      ['perfil de humor classificado','faixa de risco: sim ou não',
       f"{ML['eventos']} eventos em {ML['n']} pares"], '#C1440E', ft=9.2)
seta(a, 0.290, 0.825, 0.375, 0.825, cor='#87968F', lw=2.2)
seta(a, 0.620, 0.825, 0.705, 0.825, cor='#87968F', lw=2.2)

a.text(0.03,0.660,'O QUE PROTEGE A INFERÊNCIA', fontsize=10.2, fontweight='bold', color='#8A4FBF', va='top')
prot=[('Validação agrupada','nenhum atleta no treino e\nno teste ao mesmo tempo','#8A4FBF'),
      ('Duas linhas de base','classe majoritária e a regra\n«já estava em risco»','#8A4FBF'),
      ('Sem busca de hiperparâmetro','fixados antes da avaliação,\npara não inflar o otimismo','#8A4FBF'),
      ('Reamostragem agrupada','o intervalo respeita a\ndependência entre registros','#8A4FBF')]
for i,(t,x_,c) in enumerate(prot):
    px=0.045+i*0.235
    a.add_patch(FancyBboxPatch((px,0.455), 0.205, 0.170, boxstyle='round,pad=0.006,rounding_size=0.012',
                fc=c, ec=c, lw=1.4, alpha=.10, zorder=3))
    a.text(px+0.1025, 0.600, t, ha='center', va='top', fontsize=9.2, fontweight='bold', color=c, zorder=4)
    a.text(px+0.1025, 0.553, x_, ha='center', va='top', fontsize=8.4, color=INK, zorder=4, linespacing=1.5)

a.text(0.03,0.400,'O QUE O RESULTADO PERMITE DIZER', fontsize=10.2, fontweight='bold', color=INK, va='top')
d5=[e for e in OT['EQ'] if e['restricao'].startswith('D5')][0]
fad=[m for m in TEJ['MMI'] if m['variavel']=='Fadiga'][0]
res=[('Amostra completa', f"ganho de AUC sobre a regra trivial\nnão exclui zero em nenhum modelo", '#B3341A'),
     ('Subgrupo acionável', f"quem amanhece fora do risco:\nAUC {vg(ML2['SUBGRUPO']['Random Forest']['auc'],3)}, o IC exclui o acaso", '#1A7F5A'),
     ('Diagnóstico', f"o corte pelo PTH é em parte reversão\nà média; o da tensão não é", '#E0952B'),
     ('Limiar operacional', f"+{vg(fad['corte'],0)} de fadiga no dia identifica a entrada\nem risco (sens. {vg(fad['sens'],2)}; espec. {vg(fad['espec'],2)})", '#0F6E5C')]
for i,(t,x_,c) in enumerate(res):
    px=0.045+i*0.235
    a.add_patch(FancyBboxPatch((px,0.190), 0.205, 0.180, boxstyle='round,pad=0.006,rounding_size=0.012',
                fc=c, ec=c, lw=1.4, alpha=.10, zorder=3))
    a.text(px+0.1025, 0.345, t, ha='center', va='top', fontsize=9.2, fontweight='bold', color=c, zorder=4)
    a.text(px+0.1025, 0.297, x_, ha='center', va='top', fontsize=8.2, color=INK, zorder=4, linespacing=1.5)
a.text(0.5, 0.075, 'Com uma equipe e sete dias, o efeito das horas não se separa do efeito do dia nem da carga '
       f"acumulada. Cada hora do amistoso de D5 custa {vg(abs(d5['preco_sombra']),3)} ponto do pior dia de vigor:\n"
       'o programa linear é instrumento de planejamento, não demonstração causal.',
       ha='center', fontsize=9.6, color=MUT, style='italic', linespacing=1.6)
fig.suptitle('Framework do estudo de modelagem: o que se mede, o que protege a inferência e o que ela permite dizer',
             fontsize=12.6, fontweight='bold', x=.005, ha='left', y=1.00)
plt.tight_layout(rect=[0,0,1,.985])
salvar(fig,'M4fig')
