import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
# ---- medias diarias (7 pontos, dia 1..7) e ajuste cubico por variavel ----
dm=h.dropna(subset=['dia']).groupby('dia').agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean')).reset_index()
x=dm.dia.values.astype(float)
xx=np.linspace(1,7,600)
COEF={}; CURVE={}
for k in ['V','F','P']:
    a,b,c,d=np.polyfit(x,dm[k].values,3); COEF[k]=(a,b,c,d); CURVE[k]=np.polyval([a,b,c,d],xx)
LAB={'V':'Vigor','F':'Fadiga','P':'PTH'}; COL={'V':'#2f9e44','F':'#e8590c','P':'#7048e8'}

def crossings(k1,k2):
    diff=CURVE[k1]-CURVE[k2]; s=np.sign(diff); idx=np.where(np.diff(s)!=0)[0]; out=[]
    for j in idx:
        # interpola linearmente o zero da diferenca entre xx[j] e xx[j+1]
        x0,x1=xx[j],xx[j+1]; d0,d1=diff[j],diff[j+1]
        xc=x0-d0*(x1-x0)/(d1-d0); yc=float(np.polyval(np.polyfit(x,dm[k1].values,3),xc))
        out.append((float(xc),yc))
    return out

CR={}
for pair in [('V','F'),('V','P'),('F','P')]:
    CR['%s%s'%pair]=crossings(*pair)
json.dump({'coef':{k:list(map(float,COEF[k])) for k in COEF},'cross':CR},open('cross_pts.json','w'),ensure_ascii=False,indent=1)
for p in CR: print(p,'->',[(round(a,2),round(b,2)) for a,b in CR[p]])

# ================= FIGURA =================
ylo=min(CURVE['V'].min(),CURVE['F'].min(),CURVE['P'].min())
yhi=max(CURVE['V'].max(),CURVE['F'].max(),CURVE['P'].max()); pad=(yhi-ylo)*0.16+0.8
f=go.Figure()
f.add_vrect(x0=1,x1=4,fillcolor='#1971c2',opacity=0.05,line_width=0,layer='below')
f.add_vrect(x0=4,x1=7,fillcolor='#e8590c',opacity=0.06,line_width=0,layer='below')
f.add_annotation(x=2.5,y=yhi+pad*0.62,text='início',showarrow=False,font=dict(size=12,color='#1864ab'))
f.add_annotation(x=5.5,y=yhi+pad*0.62,text='acúmulo',showarrow=False,font=dict(size=12,color='#c0410b'))
for k in ['V','F','P']:
    f.add_trace(go.Scatter(x=x,y=dm[k].values,mode='markers',
        marker=dict(size=9,color=COL[k],opacity=0.35,line=dict(color='white',width=1)),showlegend=False))
    f.add_trace(go.Scatter(x=xx,y=CURVE[k],mode='lines',line=dict(color=COL[k],width=7),name=LAB[k]))
# marcar cruzamentos (etiquetas com deslocamentos explicitos: VF acima, VP abaixo, FP acima-direita)
OFF={'VF':(0,-52),'VP':(0,54),'FP':(52,-52)}
for pair,lbl in [('VF','Vigor × Fadiga'),('VP','Vigor × PTH'),('FP','Fadiga × PTH')]:
    ax,ay=OFF[pair]
    for xc,yc in CR[pair]:
        f.add_trace(go.Scatter(x=[xc],y=[yc],mode='markers',
            marker=dict(symbol='diamond',size=15,color='#212529',line=dict(color='white',width=2)),showlegend=False))
        f.add_annotation(x=xc,y=yc,text='<b>%s</b><br>dia %.1f · escore %.1f'%(lbl,xc,yc),showarrow=True,
            arrowhead=0,arrowwidth=1.2,arrowcolor='#868e96',ax=ax,ay=ay,
            font=dict(size=10.5,color='#212529'),bgcolor='rgba(255,255,255,0.92)',bordercolor='#212529',borderwidth=1,borderpad=3)
f.update_layout(template='mdpi',title=dict(text='<b>Cruzamentos das trajetórias de vigor, fadiga e PTH</b>',font=dict(size=17)),
    font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=62,r=24,t=66,b=86),legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=13),
        bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))
f.update_yaxes(title='Escore',range=[ylo-pad*0.5,yhi+pad],showgrid=False,zeroline=False)
f.update_xaxes(title='Dia do microciclo',dtick=1,range=[0.9,7.1],showgrid=False,zeroline=False)
f.write_image(f'{OUT}/cross_traj.png',width=1560,height=940,scale=3)
print('OK cross_traj.png')
