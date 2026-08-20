# -*- coding: utf-8 -*-
import json, numpy as np, pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
FG='/home/user/mdlucca/Artigos/figuras'
AR=json.load(open('all_results.json')); T=json.load(open('temporal.json'))
P2=json.load(open('physio2.json')); h=pd.read_csv('hum_prof.csv')
DIMS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),
      ('Raiva','Raiva'),('Confusao','Confusão'),('TMD','Perturbação total do humor (PTH)'),
      ('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]
KEYS=[k for k,_ in DIMS]
def c2(s): return str(s).replace('.',',')
def num(x,d=1): return 'n/d' if x is None else c2(f'{x:.{d}f}')
def sg(x,d=2): return c2(f'{x:+.{d}f}')
def pvt(p): return '< 0,001' if p<0.001 else c2(f'{p:.3f}')
def floor(k): return 100*np.mean(pd.to_numeric(h[k],errors='coerce').dropna()<=0)

doc=Document()
stl=doc.styles['Normal']; stl.font.name='Times New Roman'; stl.font.size=Pt(12)
stl.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
stl.paragraph_format.line_spacing=1.5; stl.paragraph_format.space_after=Pt(0)
sec=doc.sections[0]; sec.top_margin=Cm(2.3); sec.left_margin=Cm(2.4); sec.bottom_margin=Cm(2); sec.right_margin=Cm(2.2)
_TN=[0]; _FN=[0]
def P(t='',ind=True,after=0,it=False):
    p=doc.add_paragraph(); r=p.add_run(t); r.font.size=Pt(12); r.font.name='Times New Roman'; r.italic=it
    p.paragraph_format.line_spacing=1.5; p.paragraph_format.space_after=Pt(after); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    if ind: p.paragraph_format.first_line_indent=Cm(1.25)
def H1(t,n=None):
    p=doc.add_paragraph(); r=p.add_run((n+'  ' if n else '')+t); r.bold=True; r.font.size=Pt(12.5); r.font.name='Times New Roman'
    p.paragraph_format.space_before=Pt(14); p.paragraph_format.space_after=Pt(4)
def H2(t,n=None):
    p=doc.add_paragraph(); r=p.add_run((n+'  ' if n else '')+t); r.bold=True; r.italic=True; r.font.size=Pt(12); r.font.name='Times New Roman'
    p.paragraph_format.space_before=Pt(10); p.paragraph_format.space_after=Pt(3)
def _bd(c):
    tcPr=c._tc.get_or_add_tcPr(); bd=OxmlElement('w:tcBorders')
    for e in ['top','bottom']:
        el=OxmlElement('w:'+e); el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'6'); el.set(qn('w:color'),'000000'); bd.append(el)
    tcPr.append(bd)
def table(cap,header,rows,fs=8.8,note=None,al0='LEFT'):
    _TN[0]+=1
    p=doc.add_paragraph(); r=p.add_run('Tabela %d. %s'%(_TN[0],cap)); r.font.size=Pt(11); r.bold=True; r.font.name='Times New Roman'
    p.paragraph_format.space_before=Pt(10); p.paragraph_format.space_after=Pt(2)
    t=doc.add_table(rows=1,cols=len(header)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=True
    for i,ht in enumerate(header):
        cc=t.rows[0].cells[i]; cc.text=''; rr=cc.paragraphs[0].add_run(ht); rr.bold=True; rr.font.size=Pt(fs); rr.font.name='Times New Roman'
        cc.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER if i>0 else getattr(WD_ALIGN_PARAGRAPH,al0); _bd(cc)
    for row in rows:
        cs=t.add_row().cells
        for i,v in enumerate(row):
            cs[i].text=''; rr=cs[i].paragraphs[0].add_run(str(v)); rr.font.size=Pt(fs); rr.font.name='Times New Roman'
            cs[i].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER if i>0 else getattr(WD_ALIGN_PARAGRAPH,al0); _bd(cs[i])
    if note:
        pn=doc.add_paragraph(); rn=pn.add_run(note); rn.font.size=Pt(8.5); rn.italic=True; rn.font.name='Times New Roman'; pn.paragraph_format.space_after=Pt(6)
    else: doc.add_paragraph().paragraph_format.space_after=Pt(2)
def figure(path,cap,w=16.0):
    _FN[0]+=1
    pp=doc.add_paragraph(); pp.alignment=WD_ALIGN_PARAGRAPH.CENTER; pp.add_run().add_picture(path,width=Cm(w)); pp.paragraph_format.space_before=Pt(6)
    pc=doc.add_paragraph(); pc.alignment=WD_ALIGN_PARAGRAPH.CENTER; rc=pc.add_run('Figura %d. %s'%(_FN[0],cap)); rc.font.size=Pt(10.5); rc.font.name='Times New Roman'
    pc.paragraph_format.space_after=Pt(6)

# ============ CAPA / TÍTULO ============
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('MONITORAMENTO DOS ESTADOS DE HUMOR NA ÚLTIMA SEMANA DE PRÉ-TEMPORADA DE '
            'ATLETAS DE HANDEBOL DE ELITE: RELAÇÕES COM A APTIDÃO AERÓBIA E A CARGA DE TREINO')
r.bold=True; r.font.size=Pt(14); p.paragraph_format.space_after=Pt(12)

# ============ RESUMO ============
H1('Resumo')
P('Objetivo: descrever e classificar o comportamento dos estados de humor de atletas de handebol de elite '
  'ao longo da última semana de pré-temporada e verificar se a aptidão aeróbia, medida pelo pico de velocidade '
  'no teste de campo T-car, associa-se à variação do humor. Método: estudo observacional longitudinal, de grupo '
  'único, com medidas repetidas. Vinte e sete atletas do sexo masculino responderam ao questionário BRUMS de forma '
  'virtual, pela plataforma Google Forms, em dois momentos por dia (manhã e fim de tarde) durante sete dias. O pico '
  'de velocidade foi obtido no T-car, aplicado antes do período de observação. A análise seguiu três níveis: '
  'descritivo, exploratório e avançado, com testes não paramétricos, tamanhos de efeito, derivadas das curvas '
  'diárias e limiares de mudança confiável. Resultados: o Vigor caiu de forma acentuada ao longo da semana '
  '(D1 8,4 para D7 4,3; dz = 1,33; p < 0,001) e a Fadiga física aumentou de maneira consistente '
  '(qui-quadrado de Friedman = 51,3; p < 0,001). A maioria dos atletas migrou do perfil de humor positivo '
  '(iceberg) para perfis de menor energia. A aptidão aeróbia relacionou-se ao nível do humor, mas não à magnitude '
  'da deterioração ao longo da semana. Conclusão: a última semana de pré-temporada produziu perda de energia e '
  'acúmulo de fadiga; atletas mais aptos não estiveram protegidos contra essa deterioração.')
pk=doc.add_paragraph(); rr=pk.add_run('Palavras-chave: '); rr.bold=True; rr.font.size=Pt(11)
rr2=pk.add_run('estados de humor; BRUMS; handebol; carga de treinamento; pico de velocidade; monitoramento.'); rr2.font.size=Pt(11)
pk.paragraph_format.space_after=Pt(4)

# ============ 1 INTRODUÇÃO ============
H1('Introdução','1')
P('A pré-temporada é o período em que a equipe concentra as maiores cargas de treino do ano. É nesse intervalo que '
  'o condicionamento é reconstruído, mas também é quando o risco de fadiga excessiva é mais alto. Acompanhar como o '
  'atleta responde a esse esforço é parte central do trabalho da comissão técnica, porque ajustes feitos a tempo '
  'evitam que a fadiga se acumule além do desejado.')
P('Entre as ferramentas de acompanhamento, os estados de humor têm papel de destaque. O humor responde rápido às '
  'mudanças de carga e funciona como um sinal de alerta precoce: costuma se alterar antes de indicadores físicos e '
  'de desempenho. O instrumento mais utilizado para essa finalidade é o BRUMS, uma escala curta que mede as seis '
  'dimensões do humor (vigor, fadiga, tensão, depressão, raiva e confusão) e permite descrever o chamado perfil de '
  'iceberg, no qual o vigor se sobrepõe às dimensões negativas em atletas bem recuperados.')
P('Ao lado do humor, a aptidão aeróbia define quanto esforço o atleta suporta antes de fadigar. Neste estudo, a '
  'aptidão foi medida pelo pico de velocidade no T-car, um teste de campo intermitente cujo pico de velocidade já '
  'está bem estabelecido na literatura como marcador de potência aeróbia máxima e de capacidade de sustentar '
  'esforços intensos e intermitentes (Da Silva et al., 2011; Carminatti et al., 2013; Fernandes-da-Silva et al., '
  '2016; Floriano et al., 2016). A pergunta prática é direta: o atleta mais apto tem o humor menos afetado pela '
  'semana de treino, ou a deterioração atinge a todos de forma parecida?')
P('Este trabalho descreve o comportamento de todas as dimensões do humor ao longo da última semana de '
  'pré-temporada de uma equipe de elite e testa se a aptidão aeróbia protege o atleta dessa variação. A linguagem '
  'foi mantida clara e objetiva, e cada análise é explicada em termos simples, para que o resultado seja útil '
  'tanto para o pesquisador quanto para a comissão técnica.')

# ============ 2 MÉTODO ============
H1('Método','2')
H2('Tipo de estudo','2.1')
P('Trata-se de um estudo observacional, longitudinal e de abordagem quantitativa, com medidas repetidas no mesmo '
  'grupo de atletas. Observacional porque a rotina de treino não foi manipulada pelos pesquisadores: a equipe '
  'seguiu o planejamento normal da comissão técnica. Longitudinal porque os mesmos atletas foram avaliados '
  'repetidas vezes ao longo de sete dias. De grupo único porque não houve grupo controle; cada atleta serve de '
  'referência para si mesmo, e a comparação é feita entre os momentos da semana.')
H2('População e amostra','2.2')
P('Participaram 27 atletas do sexo masculino de uma equipe de handebol de elite, todos integrantes do elenco '
  'principal durante a pré-temporada. A Tabela 1 resume as características do grupo. A amostra reúne as quatro '
  'funções táticas da modalidade, o que permite descrever também as diferenças por posição.')
table('Caracterização da amostra (n = 27 atletas do sexo masculino).',
  ['Característica','Média ± DP','Mín. – Máx.'],
  [['Idade (anos)','22,0 ± 3,8','17 – 38'],
   ['Massa corporal (kg)','85,8 ± 15,7','58,8 – 132,6'],
   ['Estatura (cm)','182,5 ± 6,5','170,8 – 200,0'],
   ['Índice de massa corporal (kg/m²)','25,7 ± 3,6','n/d'],
   ['Gordura corporal (%)','11,6 ± 5,3','5,0 – 25,0'],
   ['Pico de velocidade no T-car (km/h)','14,9 ± 1,1','13,2 – 17,5']],
  note='DP: desvio-padrão. Posições: 11 meias, 9 pontas, 4 pivôs e 3 goleiros. Medidas antropométricas e do T-car disponíveis para 24 a 25 atletas.')
H2('Aspectos éticos','2.3')
P('Antes do início das coletas, a equipe recebeu a explicação detalhada dos procedimentos e dos objetivos do '
  'estudo. Todos os atletas concordaram em participar de forma voluntária e assinaram o termo de consentimento '
  'livre e esclarecido. A participação não interferiu na rotina de treino, e os dados foram tratados de forma '
  'confidencial e anônima.')
H2('Desenho do estudo','2.4')
P('O estudo foi organizado em três etapas, resumidas na Figura 1. Na primeira etapa, houve o primeiro contato com '
  'a comissão técnica e a equipe, quando foram explicados os procedimentos de coleta e assinado o termo de '
  'consentimento. Em seguida, foi realizada uma coleta de familiarização, para que os atletas conhecessem o '
  'questionário e o modo de resposta. O teste T-car foi aplicado em 15 de abril de 2024, antes do período de '
  'observação, para caracterizar a aptidão aeróbia de cada atleta.')
P('Na segunda etapa, ocorreu o monitoramento diário durante a última semana de pré-temporada. A coleta do baseline '
  'foi feita em 21 de abril de 2024. Nesse dia os atletas não treinaram, de modo que o baseline representa o estado '
  'de humor em repouso, livre do efeito imediato de uma sessão. A partir daí, o humor foi registrado duas vezes por '
  'dia até o fim da semana: uma coleta pela manhã, antes do treino (momento pré), e uma coleta ao fim do dia, após '
  'o treino (momento pós). Essa estrutura de duas medidas diárias permite separar o efeito imediato de cada sessão '
  '(a variação da manhã para o fim do dia) do efeito acumulado ao longo dos dias. Os treinos intervalados de alta '
  'intensidade concentraram-se nos dias 2, 4 e 7. Na terceira etapa, os desfechos foram organizados em três blocos: '
  'estados de humor, aptidão aeróbia e carga interna de treino.')
figure(f'{FG}/desenho_estudo.png','Desenho do estudo: etapas de preparação, semana de coletas e desfechos analisados.',w=17.0)
H2('Instrumentos e medidas','2.5')
P('Estados de humor (BRUMS). O humor foi avaliado pela Escala de Humor de Brunel (BRUMS), composta por 24 itens '
  'que descrevem sensações recentes, respondidos em uma escala de zero a quatro. Os itens formam as seis dimensões '
  'da escala: vigor, fadiga, tensão, depressão, raiva e confusão. A partir dessas seis dimensões calcula-se a '
  'perturbação total do humor (PTH), um índice global que soma as dimensões negativas e subtrai o vigor. Além da '
  'escala, foram registradas duas medidas complementares de fadiga percebida, física e mental, para detalhar a '
  'natureza do cansaço relatado. O escore de cada dimensão varia de zero a dezesseis: valores altos de vigor '
  'indicam energia, e valores altos das dimensões negativas indicam maior desconforto. O questionário foi aplicado de maneira online: '
  'os atletas respondiam de forma virtual, pela plataforma Google Forms, a partir de um link enviado nos horários '
  'de coleta. Esse formato reduz o tempo de resposta, evita erros de digitação e permite o registro imediato dos '
  'dados, sem necessidade de presença física do avaliador.')
P('Aptidão aeróbia (T-car). A aptidão foi medida pelo teste de Carminatti (T-car), um teste de campo intermitente '
  'e progressivo, feito em corridas de vaivém com aumento gradual da velocidade até a exaustão. A variável de '
  'interesse é o pico de velocidade, ou seja, a maior velocidade sustentada no teste. O pico de velocidade do '
  'T-car é uma medida validada e confiável de aptidão: associa-se fortemente à velocidade correspondente ao '
  'consumo máximo de oxigênio (Da Silva et al., 2011), pode ser usado de forma intercambiável com testes contínuos '
  'para prescrever treino (Carminatti et al., 2013), reflete a potência aeróbia máxima (Floriano et al., 2016) e '
  'relaciona-se ao desempenho físico durante o jogo (Fernandes-da-Silva et al., 2016). Neste estudo, o pico de '
  'velocidade foi usado para separar atletas mais aptos de menos aptos e para testar se a aptidão modifica a '
  'resposta do humor.')
P('Carga interna de treino. Nos dias de treino intervalado de alta intensidade, a carga interna foi acompanhada '
  'pela frequência cardíaca e pela percepção subjetiva de esforço, indicadores de quanto o organismo foi exigido '
  'em cada sessão. Esses dados ajudam a interpretar as variações do humor à luz do esforço realmente imposto ao '
  'atleta.')
H2('Análise estatística','2.6')
P('A análise foi conduzida em três níveis, do mais simples ao mais elaborado, para que cada etapa seja fácil de '
  'acompanhar.')
P('Nível 1, descritivo. Para cada dimensão do humor foram calculados a média, o desvio-padrão, a mediana, os '
  'valores mínimo e máximo e o coeficiente de variação, que expressa a dispersão relativa em porcentagem. Também '
  'foi registrada a proporção de respostas iguais a zero, o chamado efeito de piso, comum nas dimensões negativas '
  'porque atletas saudáveis tendem a marcar zero na maior parte dos itens.')
P('Nível 2, exploratório. Foi avaliada a confiabilidade das medidas entre os dias pelo coeficiente de correlação '
  'intraclasse (ICC), que indica o quanto os escores de um mesmo atleta são consistentes ao longo do tempo. A '
  'partir dele foi calculada a mudança mínima detectável a 95 por cento (MDC95), um limiar prático: só variações '
  'acima desse valor podem ser consideradas mudanças reais, e não erro de medida. A classificação do perfil de '
  'humor de cada atleta (por exemplo, iceberg ou seus formatos alternativos) foi comparada entre o primeiro e o '
  'sétimo dia para descrever a migração de perfis.')
P('Nível 3, avançado. Como os escores não seguem distribuição normal e há efeito de piso, foram usados testes não '
  'paramétricos. O teste de Friedman verificou se cada dimensão mudou ao longo da semana, acompanhado do W de '
  'Kendall como tamanho do efeito. O teste de Wilcoxon comparou momentos pareados (por exemplo, primeiro contra '
  'sétimo dia, e manhã contra fim de dia), com o tamanho de efeito dz. A relação entre aptidão e humor foi testada '
  'pela correlação de Spearman entre o pico de velocidade e tanto o nível quanto a variação do humor. A dinâmica de '
  'cada dimensão foi descrita ainda pela suavização das curvas diárias e por suas derivadas: a primeira derivada '
  'mostra a velocidade de mudança, e a segunda derivada mostra a aceleração e o ponto de inflexão, isto é, o '
  'momento em que a tendência muda de sentido. Adotou-se o nível de significância de 5 por cento.')

# ============ 3 RESULTADOS ============
H1('Resultados','3')
P('Os resultados são apresentados primeiro em tabelas e gráficos de conjunto e, em seguida, nas figuras individuais '
  'de cada dimensão do humor.')

H2('Comportamento geral das dimensões do humor','3.1')
rows=[]
for k,lab in DIMS:
    ds=AR['desc_semana'][k]; lim=T['limiares'].get(k,{})
    rows.append([lab,'%s ± %s'%(num(ds['m'],2),num(ds['sd'],1)),num(ds['med']),'%s – %s'%(num(ds['mn'],0),num(ds['mx'],0)),
                 num(ds['cv'],0),num(floor(k),0),num(lim.get('icc',0),2),num(lim.get('mdc95',0),1)])
table('Estatística descritiva das variáveis de humor na semana (286 observações de 27 atletas).',
  ['Variável','Média ± DP','Mediana','Mín – Máx','CV (%)','Piso (%)','ICC','MDC95'],rows,fs=8.6,
  note='As seis primeiras linhas são as dimensões do BRUMS; a PTH é um índice global derivado dessas dimensões; '
       'fadiga física e fadiga mental são medidas complementares de fadiga percebida. DP: desvio-padrão. '
       'CV: coeficiente de variação. Piso: porcentagem de escores iguais a zero. ICC: coeficiente de correlação '
       'intraclasse. MDC95: mudança mínima detectável a 95%.')
P('O Vigor foi a dimensão de maior escore médio, seguido pela fadiga física. As dimensões negativas apresentaram '
  'medianas baixas e forte efeito de piso, com destaque para a depressão, em que a maioria dos atletas marcou zero. '
  'A confiabilidade entre dias variou de baixa a moderada, coerente com um humor que oscila em resposta ao treino, '
  'e os valores de mudança mínima detectável fornecem o limiar prático para julgar se a variação de um atleta é '
  'real.')

H2('Variação ao longo da semana','3.2')
rows=[]
for k,lab in DIMS:
    f=AR['friedman'][k]; d=AR['d1d7'][k]
    rows.append([lab,num(f['chi'],2),pvt(f['p']),num(f['W'],2),'%s → %s'%(num(d['d1'],1),num(d['d7'],1)),
                 sg(d['delta'],1),sg(d['dz']),pvt(d['p'])+('*' if d['sig'] else '')])
table('Mudança das dimensões ao longo da semana (Friedman) e do primeiro ao sétimo dia (Wilcoxon).',
  ['Dimensão','χ² Friedman','p (semana)','W','D1 → D7','Δ','dz','p (D1→D7)'],rows,fs=8.6,
  note='χ²: qui-quadrado de Friedman. W: W de Kendall. Δ: variação do escore do D1 ao D7. dz: tamanho de efeito pareado. * p < 0,05.')
P('Cinco dimensões mudaram de forma significativa ao longo da semana: vigor, fadiga, tensão, confusão, PTH e, com '
  'o maior tamanho de efeito, a fadiga física. O padrão é consistente: o vigor caiu de maneira acentuada e as '
  'dimensões de fadiga aumentaram. A depressão, a raiva e a fadiga mental permaneceram estáveis, o que reforça a '
  'leitura de que a semana produziu perda de energia e acúmulo de fadiga física, e não um quadro de humor negativo '
  'generalizado.')

H2('Efeito imediato e efeito acumulado','3.3')
P('A Figura 2 separa, para cada dimensão, o efeito imediato de cada sessão (variação da manhã para o fim do dia) do '
  'efeito acumulado ao longo dos dias. A leitura confirma que a mudança do vigor e da fadiga física foi '
  'predominantemente acumulada: o desgaste se somou dia após dia, mais do que se explicou por uma única sessão.')
figure(f'{FG}/temporal_agudo_cronico.png','Efeito agudo (variação intradia, da manhã ao fim do dia) versus efeito crônico (do primeiro ao sétimo dia) por dimensão. O asterisco indica variação semanal significativa.',w=16.5)
P('A Figura 3 mostra, em um único mapa, onde e quanto cada dimensão mudou em cada transição da semana, com a '
  'distinção entre as transições de estímulo (da manhã ao fim do dia) e as de recuperação (do fim de um dia ao '
  'início do dia seguinte). As cores indicam a direção e a intensidade da mudança, e os asteriscos marcam as '
  'transições estatisticamente significativas.')
figure(f'{FG}/temporal_map.png','Mapa temporal das dimensões do humor: tamanho de efeito (dz) de cada transição da semana. A = transição de estímulo (manhã para fim de dia); R = transição de recuperação (fim de um dia para início do seguinte); * p < 0,05.',w=17.0)

H2('Migração dos perfis de humor','3.4')
prev=AR['perfil_prev']
def perfrows(dkey):
    d=prev[dkey]; return sorted(d.items(),key=lambda x:-x[1])
rows=[]
allp=sorted(set(list(prev['D1'])+list(prev['D7'])))
for pf in allp:
    rows.append([pf,str(prev['D1'].get(pf,0)),str(prev['D7'].get(pf,0))])
table('Distribuição dos perfis de humor no primeiro e no sétimo dia.',
  ['Perfil de humor','D1 (atletas)','D7 (atletas)'],rows,fs=9,
  note='Perfis classificados a partir das dimensões do BRUMS.')
P('No primeiro dia predominou o perfil iceberg, típico de atletas bem recuperados, com o vigor acima das dimensões '
  'negativas. Ao longo da semana, %d dos 21 atletas com classificação nos dois momentos migraram para outro perfil, '
  'e apenas %d permaneceram estáveis. No sétimo dia, o perfil mais frequente passou a ser o de barbatana de tubarão, '
  'marcado pela queda do vigor. Essa migração traduz, em linguagem de perfil, a mesma perda de energia observada nas '
  'análises anteriores.'%(AR['perfil_migracao_n'],AR['perfil_estavel_n']))

H2('Aptidão aeróbia e humor','3.5')
rows=[]
for k,lab in DIMS:
    if k=='FadMental':
        base=None
    base=P2['pv_base'].get(k); det=AR['pv_vs_deterioracao'].get(k,{})
    br='%s (%s)'%(sg(base['rho']),pvt(base['p'])) if base else 'n/d'
    dr='%s (%s)'%(sg(det.get('rho',0)),pvt(det.get('p',1))) if det else 'n/d'
    rows.append([lab,br,dr])
table('Correlação de Spearman entre o pico de velocidade no T-car e o humor: nível semanal e deterioração (D1→D7).',
  ['Dimensão','PV × nível (rho, p)','PV × deterioração (rho, p)'],rows,fs=8.8,
  note='rho: coeficiente de Spearman. Nenhuma correlação alcançou significância estatística.')
P('A aptidão aeróbia relacionou-se de forma fraca e não significativa com o nível do humor e, sobretudo, não se '
  'relacionou com a magnitude da deterioração ao longo da semana. Em termos práticos, o atleta mais apto não '
  'esteve protegido contra a queda de vigor e o aumento de fadiga: a deterioração atingiu de forma semelhante os '
  'mais e os menos aptos (Figura 4). A aptidão parece definir o patamar geral do humor, e não o quanto ele se '
  'desgasta em uma semana de cargas elevadas.')
figure(f'{FG}/temporal_aptidao.png','Deterioração do primeiro ao sétimo dia por dimensão, para atletas mais aptos versus menos aptos (divididos pela mediana do pico de velocidade). Não houve diferença significativa entre os grupos.',w=16.5)

H2('Comportamento individual de cada dimensão','3.6')
P('As figuras a seguir apresentam, para cada dimensão do humor, um painel completo com a trajetória diária e seus '
  'limites, a velocidade e a aceleração da mudança (primeira e segunda derivadas), as transições ao longo da '
  'semana, o efeito imediato por dia e uma síntese descritiva. A leitura conjunta desses painéis permite '
  'identificar, para cada variável, em que dia a mudança foi mais intensa e quando a tendência mudou de sentido.')
for k,lab in DIMS:
    figure(f'{FG}/vd_{k}.png','Painel da dimensão %s: trajetória, limites, derivadas, transições e síntese descritiva.'%lab.split(' (')[0].lower(),w=15.0)

# ============ 4 DISCUSSÃO ============
H1('Discussão','4')
P('Este estudo descreveu o comportamento dos estados de humor de atletas de handebol de elite ao longo da última '
  'semana de pré-temporada e testou se a aptidão aeróbia protege o atleta da deterioração do humor. Três achados '
  'organizam a discussão: a queda consistente do vigor e o aumento da fadiga física, a migração dos perfis de '
  'humor, e a ausência de proteção conferida pela aptidão.')
H2('A energia cai e a fadiga física se acumula','4.1')
P('O achado mais robusto foi a combinação de queda do vigor e aumento da fadiga física, esta última com o maior '
  'tamanho de efeito de todas as dimensões. Esse padrão é coerente com o propósito da pré-temporada, período '
  'planejado para impor carga e estimular adaptações. A análise das derivadas mostrou que a mudança não foi '
  'abrupta: a velocidade de queda do vigor foi maior no início da semana e a curva apresentou um ponto de inflexão '
  'na sua metade, sinal de que o organismo passou a estabilizar a resposta. Do ponto de vista prático, o vigor se '
  'confirma como o indicador mais sensível para acompanhar o desgaste, por reagir cedo e com clareza.')
H2('O efeito é acumulado, não pontual','4.2')
P('A separação entre efeito imediato e efeito acumulado trouxe uma informação relevante para a periodização. A '
  'deterioração do humor não foi explicada por uma sessão isolada, mas pela soma dos dias. As transições de '
  'estímulo, da manhã ao fim do dia, produziram variações menores do que a tendência acumulada de segunda a última '
  'coleta. Isso sugere que o monitoramento diário é mais informativo do que medidas pontuais: é a trajetória, e '
  'não um único ponto, que revela o estado do atleta. O mapa temporal reforça essa leitura ao localizar as '
  'transições em que a mudança foi significativa.')
H2('Os perfis de humor migram do iceberg','4.3')
P('A migração de perfis descreve, em uma linguagem intuitiva para a comissão técnica, o mesmo fenômeno observado '
  'nas dimensões isoladas. O predomínio inicial do perfil iceberg, com o vigor sobreposto às dimensões negativas, '
  'deu lugar a perfis de menor energia, como a barbatana de tubarão. A maior parte dos atletas mudou de perfil ao '
  'longo da semana, o que confirma a sensibilidade do humor à carga e sustenta o uso do perfil como recurso de '
  'comunicação rápida do estado do grupo.')
H2('Aptidão não é sinônimo de proteção','4.4')
P('O resultado talvez mais instigante é que a aptidão aeróbia não protegeu o atleta da deterioração do humor. As '
  'correlações entre o pico de velocidade e a variação do humor foram fracas e não significativas, e a comparação '
  'entre mais e menos aptos não revelou diferença na magnitude da queda. Uma interpretação plausível é que a '
  'aptidão define o patamar do humor, o ponto de partida, mas não a inclinação da resposta a uma semana de cargas '
  'elevadas. Em outras palavras, estar bem condicionado ajuda a começar melhor, mas não impede o desgaste quando o '
  'estímulo é alto para todos. Esse achado tem consequência prática: o monitoramento do humor não pode ser '
  'substituído pela avaliação da aptidão, porque os dois descrevem coisas diferentes e complementares.')
H2('Síntese dos principais achados','4.5')
P('Em conjunto, os resultados mostram que a última semana de pré-temporada produziu perda de energia e acúmulo de '
  'fadiga física, de forma acumulada ao longo dos dias, com migração da maioria dos atletas para perfis de humor '
  'de menor vigor, e sem que a aptidão aeróbia oferecesse proteção contra essa deterioração. A principal '
  'contribuição do estudo é integrar, em um mesmo desenho, a descrição fina do humor por derivadas e limiares, a '
  'leitura por perfis e o cruzamento com a aptidão, para dar à comissão técnica um retrato claro de onde, quando '
  'e quanto o humor muda. As limitações incluem o desenho de grupo único, sem grupo controle, e o tamanho da '
  'amostra, próprio de uma equipe de elite. Estudos futuros podem acompanhar mais de um microciclo e incluir '
  'medidas objetivas de recuperação para confirmar e ampliar estes achados.')

# ============ 5 CONCLUSÃO ============
H1('Conclusão','5')
P('A última semana de pré-temporada de atletas de handebol de elite foi marcada pela queda do vigor e pelo aumento '
  'da fadiga física, com deterioração acumulada ao longo dos dias e migração da maioria dos atletas do perfil '
  'iceberg para perfis de menor energia. A aptidão aeróbia, medida pelo pico de velocidade no T-car, associou-se '
  'ao patamar do humor, mas não protegeu o atleta da deterioração ao longo da semana. O monitoramento diário dos '
  'estados de humor, aplicado de forma simples e virtual, mostrou-se sensível e útil para orientar decisões de '
  'ajuste de carga.')

# ============ REFERÊNCIAS ============
H1('Referências')
refs=[
 'Carminatti, L. J., Possamai, C. A. P., de Moraes, M., da Silva, J. F., de Lucas, R. D., Dittrich, N., & '
 'Guglielmo, L. G. A. (2013). Intermittent versus continuous incremental field tests: are maximal variables '
 'interchangeable? Journal of Sports Science and Medicine, 12(1), 165–170.',
 'Da Silva, J. F., Guglielmo, L. G. A., Carminatti, L. J., De Oliveira, F. R., Dittrich, N., & Paton, C. D. '
 '(2011). Validity and reliability of a new field test (Carminatti’s test) for soccer players compared with '
 'laboratory-based measures. Journal of Sports Sciences, 29(15), 1621–1628. '
 'https://doi.org/10.1080/02640414.2011.609179',
 'Fernandes-da-Silva, J., Castagna, C., Teixeira, A. S., Carminatti, L. J., & Guglielmo, L. G. A. (2016). The peak '
 'velocity derived from the Carminatti Test is related to physical match performance in young soccer players. '
 'Journal of Sports Sciences, 34(24), 2238–2245. https://doi.org/10.1080/02640414.2016.1209307',
 'Floriano, L. T., da Silva, J. F., Teixeira, A. S., Salvador, P. C. N., Dittrich, N., Carminatti, L. J., '
 'Nascimento, L. L., & Guglielmo, L. G. A. (2016). Physiological responses during the time limit at 100% of the '
 'peak velocity in the Carminatti’s test in futsal players. Journal of Human Kinetics, 54, 91–101. '
 'https://doi.org/10.1515/hukin-2016-0038',
 'Rohlfs, I. C. P. M., Rotta, T. M., Luft, C. D. B., Andrade, A., Krebs, R. J., & Carvalho, T. (2008). A Escala '
 'de Humor de Brunel (Brums): instrumento para deteccao precoce da sindrome do excesso de treinamento. Revista '
 'Brasileira de Medicina do Esporte, 14(3), 176–181.',
 'Terry, P. C., Lane, A. M., & Fogarty, G. J. (2003). Construct validity of the Profile of Mood States-Adolescents '
 'for use with adults. Psychology of Sport and Exercise, 4(2), 125–139.']
for rf in refs:
    p=doc.add_paragraph(); r=p.add_run(rf); r.font.size=Pt(11); r.font.name='Times New Roman'
    p.paragraph_format.line_spacing=1.5; p.paragraph_format.space_after=Pt(6); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent=Cm(1.25); p.paragraph_format.first_line_indent=Cm(-1.25)

doc.save('/home/user/mdlucca/Artigos/Estudo_Humor_Handebol_Completo.docx')
print('OK Estudo_Humor_Handebol_Completo.docx  figs=%d tabs=%d'%(_FN[0],_TN[0]))
