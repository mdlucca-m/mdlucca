import json, plotly.offline
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
DATA=open(f'{SC}/dash_data.json',encoding='utf-8').read()
# plotly.js inline
import plotly
plotlyjs=plotly.offline.get_plotlyjs()

HTML=r'''<div id="app">
<header>
  <h1>Painel analítico — Microciclo de choque de HIIT</h1>
  <p class="sub">Handebol de elite · 21–28/04/2024 · 27 atletas · 456 observações · analytics com segmentação · reanálise independente (Python)</p>
  <div class="controls">
    <label>Dimensão de segmentação
      <select id="dim"></select></label>
    <label>Segmento
      <select id="seg"></select></label>
    <label>Variável (trajetória)
      <select id="var"></select></label>
  </div>
</header>

<section class="kpis" id="kpis"></section>

<div class="grid">
  <div class="card"><h3>Trajetória semanal (segmento) — média ± EP</h3><div id="chartTraj"></div></div>
  <div class="card"><h3>Perfil iceberg por dia (%)</h3><div id="chartIce"></div></div>
  <div class="card"><h3>Segmentação: acúmulo D1→D7 (dz) por segmento</h3><div id="chartSeg"></div></div>
  <div class="card"><h3>Correlação entre-atletas (eixo energia–fadiga)</h3><div id="chartCorr"></div></div>
  <div class="card wide"><h3>Perfil individual — índice iceberg por atleta × dia (azul=saudável · vermelho=fadiga)</h3><div id="chartHeat"></div></div>
</div>
<footer>KPIs robustos (dz com IC95% bootstrap; ICC de traço). Atletas anonimizados (A01–A27). Segmentos pequenos (Pivô n=4, Goleiro n=3, tercis n≈8) têm IC amplo — interpretar com cautela. Reprodutibilidade: <code>scripts/analise/</code>.</footer>
</div>

<style>
:root{--bg:#0d1117;--card:#131a24;--bd:#222c3a;--fg:#e6edf3;--mut:#9aa7b4;--accent:#ff6b6b;--blue:#4dabf7;--red:#f03e3e;--green:#51cf66}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,Segoe UI,Roboto,sans-serif}
#app{max-width:1280px;margin:0 auto;padding:24px 18px 60px}
header h1{font-size:1.6rem;margin:0 0 4px;color:#fff}.sub{color:var(--mut);margin:2px 0 14px;font-size:.92rem}
.controls{display:flex;gap:16px;flex-wrap:wrap;background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 16px}
.controls label{display:flex;flex-direction:column;gap:5px;font-size:.8rem;color:var(--mut);font-weight:600}
.controls select{background:#0d1117;color:var(--fg);border:1px solid var(--bd);border-radius:8px;padding:8px 10px;font-size:.95rem;min-width:180px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px 16px}
.kpi .v{font-size:1.7rem;font-weight:700;line-height:1.1}.kpi .l{color:var(--mut);font-size:.78rem;margin-top:4px}.kpi .ci{color:var(--mut);font-size:.72rem;margin-top:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px 16px}
.card.wide{grid-column:1/-1}.card h3{margin:0 0 8px;font-size:.98rem;color:#dfe7ef}
footer{margin-top:26px;color:#7d8896;font-size:.8rem;border-top:1px solid var(--bd);padding-top:14px}
code{background:#1c2530;padding:2px 6px;border-radius:5px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
</style>

<script>
const DATA=__DATA__;
const T={paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:'#c9d4df'},
  margin:{l:48,r:16,t:10,b:40},colorway:['#f03e3e','#e64980','#4dabf7','#ff922b']};
const HIIT=[2,4,7];
const COL={FadFisica:'#f03e3e',TMD:'#e64980',Vigor:'#4dabf7',Fadiga:'#ff922b'};
function bands(){return HIIT.map(d=>({type:'rect',xref:'x',yref:'paper',x0:d-0.15,x1:d+0.15,y0:0,y1:1,fillcolor:'#ff6b6b',opacity:0.10,line:{width:0}}));}
const cfg={displaylogo:false,responsive:true,toImageButtonOptions:{format:'png',width:3840,height:2160,scale:1}};

const dimSel=document.getElementById('dim'),segSel=document.getElementById('seg'),varSel=document.getElementById('var');
Object.keys(DATA.dims).forEach(d=>dimSel.add(new Option(d,d)));
DATA.vars.forEach(v=>varSel.add(new Option(DATA.lab[v],v)));
varSel.value='FadFisica';
function fillSeg(){segSel.innerHTML='';DATA.dims[dimSel.value].forEach(s=>segSel.add(new Option(s,s)));}
fillSeg();

function kpiCard(v,l,ci){return `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div>${ci?`<div class="ci">${ci}</div>`:''}</div>`;}
function render(){
  const seg=DATA.segments[segSel.value]; const k=seg.kpi; const v=varSel.value;
  const dzf=k.FadFisica_dz, dzv=k.Vigor_dz;
  document.getElementById('kpis').innerHTML=
    kpiCard(seg.n_ath,'Atletas no segmento','')+
    kpiCard(seg.n_obs,'Observações','')+
    kpiCard((dzf[0]>0?'+':'')+dzf[0],'Fadiga física · dz D1→D7',dzf[1]!=null?`IC95% [${dzf[1]}, ${dzf[2]}]`:'')+
    kpiCard(dzv[0],'Vigor · dz D1→D7',dzv[1]!=null?`IC95% [${dzv[1]}, ${dzv[2]}]`:'')+
    kpiCard((k.iceberg_d1??'–')+'% → '+(k.iceberg_d7??'–')+'%','Perfil iceberg D1→D7','')+
    kpiCard(k.tmd_d7??'–','PTH/TMD no D7 (pico)','')+
    kpiCard(k.icc_tmd??'–','ICC de traço (TMD)','fração entre-atletas');

  // trajectory
  const tr=seg.traj[v]; const x=[1,2,3,4,5,6,7];
  const up=tr.mean.map((m,i)=>m==null?null:m+tr.se[i]), lo=tr.mean.map((m,i)=>m==null?null:m-tr.se[i]);
  Plotly.react('chartTraj',[
    {x:x.concat(x.slice().reverse()),y:up.concat(lo.slice().reverse()),fill:'toself',fillcolor:COL[v],opacity:0.15,line:{width:0},hoverinfo:'skip',showlegend:false},
    {x,y:tr.mean,mode:'lines+markers',line:{color:COL[v],width:3},marker:{size:8},name:DATA.lab[v]}
  ],Object.assign({},T,{shapes:bands(),xaxis:{title:'Dia',dtick:1},yaxis:{title:'Escore'},height:300,hovermode:'x'}),cfg);

  // iceberg by day
  Plotly.react('chartIce',[{x,y:seg.iceberg_by_day,type:'bar',marker:{color:x.map(d=>HIIT.includes(d)?'#ff6b6b':'#4dabf7')}}],
    Object.assign({},T,{xaxis:{title:'Dia',dtick:1},yaxis:{title:'% iceberg',range:[0,100]},height:300}),cfg);

  // segment comparison (dz D1->D7)
  const dim=dimSel.value;
  if(DATA.seg_compare[dim]){const sc=DATA.seg_compare[dim];
    Plotly.react('chartSeg',DATA.vars.map(vv=>({x:sc.segments,y:sc[vv],type:'bar',name:DATA.lab[vv],marker:{color:COL[vv]}})),
      Object.assign({},T,{barmode:'group',yaxis:{title:'dz D1→D7'},height:300,legend:{orientation:'h',y:1.15}}),cfg);
  } else {Plotly.react('chartSeg',[{x:['Geral'],y:[seg.kpi.FadFisica_dz[0]],type:'bar',marker:{color:'#f03e3e'}}],
      Object.assign({},T,{yaxis:{title:'dz D1→D7'},height:300,annotations:[{text:'Selecione Aptidão ou Posição para comparar segmentos',showarrow:false,xref:'paper',yref:'paper',x:0.5,y:0.5,font:{color:'#7d8896'}}]}),cfg);}

  // correlation heatmap
  Plotly.react('chartCorr',[{z:seg.corr.z,x:seg.corr.labels,y:seg.corr.labels,type:'heatmap',colorscale:'RdBu',zmid:0,zmin:-1,zmax:1,
    text:seg.corr.z,texttemplate:'%{text}',showscale:true}],Object.assign({},T,{height:300}),cfg);

  // individual heatmap
  Plotly.react('chartHeat',[{z:seg.heatmap.z,x,y:seg.heatmap.athletes,type:'heatmap',colorscale:'RdBu',reversescale:true,zmid:0,
    colorbar:{title:'índice<br>iceberg'}}],Object.assign({},T,{xaxis:{title:'Dia',dtick:1},height:Math.max(260,seg.heatmap.athletes.length*16+80)}),cfg);
}
dimSel.onchange=()=>{fillSeg();render();};segSel.onchange=render;varSel.onchange=render;
render();
</script>'''

body='<script>'+plotlyjs+'</script>\n'+HTML.replace('__DATA__',DATA)
html='<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Painel analítico — Microciclo HIIT</title></head><body>'+body+'</body></html>'
open('/home/user/mdlucca/Artigos/Painel_Interativo.html','w',encoding='utf-8').write(html)
print('Painel salvo:',round(len(html)/1024,1),'KB')
