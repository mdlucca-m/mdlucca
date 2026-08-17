# Template plotly compartilhado — estilo MDPI Sports (limpo, tipo periódico).
# Importar em cada script de figura: 'import mdpi_style' (registra e torna padrão).
import plotly.io as pio
import plotly.graph_objects as go
import copy

_base = pio.templates['plotly_white']
t = copy.deepcopy(_base)

# tipografia sans-serif, texto escuro — fontes maiores para escalas mais visíveis
t.layout.font = dict(family='Arial, Helvetica, sans-serif', size=16, color='#2b2b2b')
t.layout.title = dict(font=dict(family='Arial, Helvetica, sans-serif', size=18, color='#1f1f1f'))
t.layout.paper_bgcolor = 'white'
t.layout.plot_bgcolor = 'white'

# eixos: grade nítida + linha de eixo grossa com ticks maiores para fora (escalas visíveis)
_axis = dict(showgrid=True, gridcolor='#dfe3e8', gridwidth=1.2,
             showline=True, linecolor='#4d5259', linewidth=2,
             ticks='outside', tickcolor='#4d5259', ticklen=7, tickwidth=1.6,
             tickfont=dict(size=15), zeroline=False, automargin=True)
t.layout.xaxis = _axis
t.layout.yaxis = copy.deepcopy(_axis)

# paleta qualitativa consistente e contrastante (só afeta traços sem cor explícita)
t.layout.colorway = ['#2f9e44', '#e03131', '#f0a020', '#1c7ed6', '#8a6d3b', '#7048e8', '#e8590c']

# traços mais grossos por padrão (traços sem largura explícita)
t.data.scatter = (go.Scatter(line=dict(width=4.5), marker=dict(size=10, line=dict(color='white', width=1.5))),)

# legenda com moldura discreta e fonte maior
t.layout.legend = dict(bgcolor='rgba(255,255,255,0.95)', bordercolor='#c4c9d0', borderwidth=1.2,
                       font=dict(size=14))

pio.templates['mdpi'] = t
pio.templates.default = 'mdpi'
