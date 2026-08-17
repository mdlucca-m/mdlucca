# Template plotly compartilhado — estilo MDPI Sports (limpo, tipo periódico).
# Importar em cada script de figura: 'import mdpi_style' (registra e torna padrão).
import plotly.io as pio
import plotly.graph_objects as go
import copy

_base = pio.templates['plotly_white']
t = copy.deepcopy(_base)

# tipografia sans-serif, texto escuro
t.layout.font = dict(family='Arial, Helvetica, sans-serif', size=13, color='#333333')
t.layout.title = dict(font=dict(family='Arial, Helvetica, sans-serif', size=15, color='#222222'))
t.layout.paper_bgcolor = 'white'
t.layout.plot_bgcolor = 'white'

# eixos: grade cinza-clara + linha de eixo com ticks para fora (marca registrada MDPI/Excel)
_axis = dict(showgrid=True, gridcolor='#e6e8eb', gridwidth=1,
             showline=True, linecolor='#8a9099', linewidth=1,
             ticks='outside', tickcolor='#8a9099', ticklen=4,
             zeroline=False, automargin=True)
t.layout.xaxis = _axis
t.layout.yaxis = copy.deepcopy(_axis)

# paleta qualitativa consistente (só afeta traços sem cor explícita)
t.layout.colorway = ['#2f9e44', '#e03131', '#f0a020', '#1c7ed6', '#8a6d3b', '#7048e8', '#e8590c']

# legenda com moldura discreta
t.layout.legend = dict(bgcolor='rgba(255,255,255,0.92)', bordercolor='#d0d3d8', borderwidth=1,
                       font=dict(size=12))

pio.templates['mdpi'] = t
pio.templates.default = 'mdpi'
