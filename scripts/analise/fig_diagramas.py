import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import plotly.graph_objects as go
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'

def box(f,x,y,w,h,text,fill,line,tcolor='#1a1a1a',fs=13,bold=True):
    f.add_shape(type='rect',x0=x-w/2,y0=y-h/2,x1=x+w/2,y1=y+h/2,
        line=dict(color=line,width=2.2),fillcolor=fill,layer='below')
    f.add_annotation(x=x,y=y,text=('<b>%s</b>'%text) if bold else text,showarrow=False,
        font=dict(size=fs,color=tcolor,family='Arial'),align='center')
def arrow(f,x0,y0,x1,y1,color='#495057',w=2.4):
    f.add_annotation(x=x1,y=y1,ax=x0,ay=y0,xref='x',yref='y',axref='x',ayref='y',
        showarrow=True,arrowhead=3,arrowsize=1.3,arrowwidth=w,arrowcolor=color,text='')
def base(f,ttl,h=940):
    f.update_layout(template='mdpi',title=dict(text='<b>%s</b>'%ttl,x=0.5,xanchor='center',font=dict(size=18)),
        paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=10,r=10,t=64,b=10),showlegend=False)
    f.update_xaxes(range=[0,100],showgrid=False,zeroline=False,showticklabels=False,visible=False)
    f.update_yaxes(range=[0,100],showgrid=False,zeroline=False,showticklabels=False,visible=False)

# ===================== 1) ORGANOGRAMA (delineamento do estudo) =====================
C_ATL='#dbe4ff'; L_ATL='#4263eb'   # azul
C_COL='#e6fcf5'; L_COL='#0ca678'   # verde-agua
C_OBS='#fff3bf'; L_OBS='#f08c00'   # ambar
PAL=[('#e7f5ff','#1971c2'),('#fff0f6','#c2255c'),('#f3f0ff','#7048e8'),('#ebfbee','#2f9e44'),('#fff4e6','#e8590c')]
f=go.Figure()
box(f,50,93,58,10,'27 atletas de handebol de elite (sexo masculino)<br><span style="font-size:11px">idade 25,9 ± 4,4 anos; 12,8 ± 4,6 anos de prática</span>',C_ATL,L_ATL,fs=13)
arrow(f,50,88,50,84)
box(f,50,79,50,9,'Microciclo pré-competitivo · 7 dias',C_ATL,L_ATL,fs=13)
arrow(f,50,74.5,30,69); arrow(f,50,74.5,70,69)
box(f,27,64,38,10,'Dia 1: linha de base<br><span style="font-size:11px">1 coleta</span>',C_COL,L_COL,fs=12)
box(f,73,64,42,10,'Dias 2–7: pré e pós-treino<br><span style="font-size:11px">2 coletas por dia</span>',C_COL,L_COL,fs=12)
arrow(f,27,59,50,53.5); arrow(f,73,59,50,53.5)
box(f,50,49,60,10,'286 observações · BRUMS-24<br><span style="font-size:11px">6 dimensões + perturbação total do humor (PTH)</span>',C_OBS,L_OBS,fs=13)
arrow(f,50,44,50,39)
f.add_annotation(x=50,y=36.5,text='<b>Plano de análise (com tamanho e magnitude do efeito)</b>',showarrow=False,font=dict(size=13,color='#343a40'))
labs=['Descritiva e psicometria<br><span style="font-size:10px">ICC · α de Cronbach<br>MDC / SWC</span>',
      'Não paramétrica<br><span style="font-size:10px">Wilcoxon · Friedman<br>W de Kendall · Spearman</span>',
      'Multivariada<br><span style="font-size:10px">MANOVA (escores T)<br>PCA</span>',
      'Perfis de humor<br><span style="font-size:10px">classificação · qui-quadrado<br>regressão logística</span>',
      'Trajetórias<br><span style="font-size:10px">spline · 2ª derivada<br>polinômio · cruzamentos</span>']
xs=[11,30.5,50,69.5,89]; ww=18.5
for xc,lab,(cf,cl) in zip(xs,labs,PAL):
    arrow(f,50,33.5,xc,29.5,color=cl,w=1.8)
    box(f,xc,21,ww,15,lab,cf,cl,fs=11.5)
base(f,'Organograma do delineamento do estudo')
f.write_image(f'{OUT}/organograma.png',width=1640,height=980,scale=3)
print('OK organograma.png')

# ===================== 2) FRAMEWORK CONCEITUAL (eixo energia-fadiga) =====================
f=go.Figure()
# cadeia horizontal
steps=[
 (13,'Carga do microciclo<br><span style="font-size:11px">handebol intermitente<br>de alta intensidade</span>','#e7f5ff','#1971c2'),
 (30.4,'BRUMS-24<br><span style="font-size:11px">6 dimensões do humor</span>','#f3f0ff','#7048e8'),
 (47.8,'Eixo energia–fadiga<br><span style="font-size:11px">vigor ↓ · fadiga ↑ · PTH ↑</span>','#ebfbee','#2f9e44'),
 (65.2,'Migração de perfis<br><span style="font-size:11px">iceberg → barbatana<br>de tubarão</span>','#fff4e6','#e8590c'),
 (82.6,'Sobre-esforço<br>funcional<br><span style="font-size:11px">janela monitorável</span>','#fff0f6','#c2255c'),
]
yc=62; wb=15.5; hb=17
for i,(x,txt,cf,cl) in enumerate(steps):
    box(f,x,yc,wb,hb,txt,cf,cl,fs=12)
    if i>0: arrow(f,steps[i-1][0]+wb/2,yc,x-wb/2,yc,color='#495057',w=2.6)
# saida: decisao
box(f,82.6,32,26,12,'Decisão de treino<br>e recuperação','#e9ecef','#495057',fs=12.5)
arrow(f,82.6,yc-hb/2,82.6,38,color='#c2255c',w=2.6)
# alca de retroalimentacao (feedback) da decisao de volta a carga
f.add_annotation(x=13,y=44,ax=69.6,ay=32,xref='x',yref='y',axref='x',ayref='y',
    showarrow=True,arrowhead=3,arrowsize=1.3,arrowwidth=2.4,arrowcolor='#1971c2',text='')
f.add_annotation(x=41,y=27,text='<b>ajuste da carga (retroalimentação)</b>',showarrow=False,font=dict(size=12,color='#1971c2'))
arrow(f,13,38,13,yc-hb/2,color='#1971c2',w=2.4)
# faixa de leitura
f.add_annotation(x=50,y=86,text='monitoramento subjetivo, sensível e de baixo custo, complementar às medidas fisiológicas',
    showarrow=False,font=dict(size=12.5,color='#868e96'))
base(f,'Framework conceitual do monitoramento do humor no eixo energia–fadiga',h=760)
f.update_yaxes(range=[10,95])
f.write_image(f'{OUT}/framework.png',width=1640,height=760,scale=3)
print('OK framework.png')
