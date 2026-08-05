import json, plotly.offline, plotly
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
DATA=open(f'{SC}/app_data.json',encoding='utf-8').read()
plotlyjs=plotly.offline.get_plotlyjs()

APP=r'''<div id="app">
<header>
  <h1>Central Analítica — Microciclo de choque de HIIT · Handebol de elite</h1>
  <p class="sub">21–28/04/2024 · 27 atletas · 456 observações · reanálise independente (Python). Clique nos botões para gerar cada bloco analítico automaticamente.</p>
  <nav id="nav">
    <button data-v="descritiva" class="active">📊 Descritiva</button>
    <button data-v="brums">🧠 BRUMS</button>
    <button data-v="interna">❤️ Carga interna</button>
    <button data-v="externa">🏃 Carga externa</button>
    <button data-v="correl">🔗 Correlações</button>
  </nav>
  <div id="subnav" class="subnav" style="display:none"></div>
</header>
<main id="content"></main>
<footer>Atletas anonimizados (A01–A27). KPIs: dz D1→D7, dz agudo pré→pós, %piso, ICC de traço. Reprodutibilidade: <code>scripts/analise/</code>.</footer>
</div>

<style>
:root{--bg:#0b0f15;--card:#141c27;--bd:#243040;--fg:#e6edf3;--mut:#93a1b1;--red:#f03e3e;--blue:#4dabf7;--org:#ff922b;--pink:#e64980;--grn:#51cf66;--vio:#9775fa}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,Segoe UI,Roboto,sans-serif}
#app{max-width:1280px;margin:0 auto;padding:22px 18px 70px}
header h1{font-size:1.5rem;margin:0 0 4px;color:#fff}.sub{color:var(--mut);margin:0 0 14px;font-size:.9rem}
nav{display:flex;gap:10px;flex-wrap:wrap}
nav button{background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:10px;padding:11px 18px;font-size:.98rem;font-weight:600;cursor:pointer;transition:.15s}
nav button:hover{border-color:#3a4a60;background:#1a2432}
nav button.active{background:#1b3a5b;border-color:var(--blue);color:#fff}
.subnav{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.subnav button{background:#0d1520;color:var(--mut);border:1px solid var(--bd);border-radius:20px;padding:8px 15px;font-size:.9rem;cursor:pointer}
.subnav button.active{background:var(--pink);color:#fff;border-color:var(--pink)}
main{margin-top:20px}
.explain{background:linear-gradient(90deg,#16202e,#131a24);border-left:4px solid var(--blue);border-radius:10px;padding:14px 18px;margin:16px 0;color:#cdd8e3;line-height:1.55;font-size:.98rem}
.explain b{color:#fff}
h2.sec{font-size:1.25rem;margin:26px 0 6px;color:#fff;border-bottom:1px solid var(--bd);padding-bottom:6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}
.kpi .v{font-size:1.6rem;font-weight:700}.kpi .l{color:var(--mut);font-size:.76rem;margin-top:3px}.kpi .ci{color:var(--mut);font-size:.7rem}
.chart{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:14px 16px;margin:16px 0}
.chart h3{margin:0 0 4px;font-size:1.05rem;color:#eaf1f8}.chart .note{color:var(--mut);font-size:.84rem;margin:0 0 8px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tbl{width:100%;border-collapse:collapse;font-size:.88rem}
.tbl th,.tbl td{padding:7px 9px;border-bottom:1px solid var(--bd);text-align:right}
.tbl th:first-child,.tbl td:first-child{text-align:left;color:#dfe7ef}
.tbl th{color:var(--mut);font-weight:600}
code{background:#1c2530;padding:2px 6px;border-radius:5px}
footer{margin-top:34px;color:#7d8896;font-size:.8rem;border-top:1px solid var(--bd);padding-top:14px}
@media(max-width:820px){.row2{grid-template-columns:1fr}}
</style>

<script>
const D=__DATA__;
const T={paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:'#c9d4df',size:13},margin:{l:56,r:20,t:20,b:48}};
const cfg={displaylogo:false,responsive:true,toImageButtonOptions:{format:'png',width:3840,height:2160,scale:1}};
const HIIT=[2,4,7];
const CC={FadFisica:'#f03e3e',Fadiga:'#ff922b',Vigor:'#4dabf7',TMD:'#e64980',Tensao:'#9775fa',Depressao:'#5c7cfa',Raiva:'#e8590c',Confusao:'#22b8cf',FadMental:'#ffd43b'};
const POSC={Armador:'#4dabf7',Ala:'#51cf66',['Pivô']:'#ff922b',Goleiro:'#e64980'};
function bands(){return HIIT.map(d=>({type:'rect',xref:'x',yref:'paper',x0:d-0.15,x1:d+0.15,y0:0,y1:1,fillcolor:'#ff6b6b',opacity:0.09,line:{width:0}}));}
function el(h){const d=document.createElement('div');d.innerHTML=h;return d.firstElementChild;}
function chart(id,title,note){return `<div class="chart"><h3>${title}</h3>${note?`<p class="note">${note}</p>`:''}<div id="${id}"></div></div>`;}
function kpi(v,l,ci){return `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div>${ci?`<div class="ci">${ci}</div>`:''}</div>`;}

// ---------- DESCRITIVA ----------
function viewDescritiva(){
  const s=D.socio,a=s.agg,C=content();
  C.innerHTML=`
  <div class="explain"><b>O que foi feito.</b> Caracterização da amostra (sociodemográfica, antropométrica e de aptidão) e análise exploratória das distribuições de todas as variáveis: tendência central (média, mediana), dispersão (DP, IQR), forma (assimetria, curtose), efeito piso, teste de normalidade (Shapiro–Wilk), histogramas, dispersões/regressão e matriz de correlação. Os sociodemográficos são apresentados em gráficos 3D e de proporção.</div>
  <h2 class="sec">1 · Caracterização da amostra</h2>
  <div class="kpis">
   ${kpi(a.idade[0]+'±'+a.idade[1],'Idade (anos)','amplitude '+a.idade[2]+'–'+a.idade[3])}
   ${kpi(a.exp[0]+'±'+a.exp[1],'Experiência (anos)','')}
   ${kpi(a.estatura[0]+'±'+a.estatura[1],'Estatura (cm)','')}
   ${kpi(a.massa[0]+'±'+a.massa[1],'Massa (kg)','')}
   ${kpi(a.pG[0]+'±'+a.pG[1],'Gordura (%)','')}
   ${kpi(a.PV[0]+'±'+a.PV[1],'PV T-CAR (km/h)','')}
  </div>
  <div class="row2">
   ${chart('d_pos','Distribuição por posição','proporção de cada posição na amostra')}
   ${chart('d_3d','Sociodemográfico 3D — idade × massa × estatura','cor = posição · gire com o mouse')}
  </div>
  <h2 class="sec">2 · Distribuições e normalidade</h2>
  ${chart('d_norm','Normalidade (Shapiro–Wilk) e efeito piso por variável','barras = valor-p do Shapiro (linha = 0,05); nenhuma variável é normal')}
  <div class="row2">
   ${chart('d_hist','Histogramas das variáveis-chave','')}
   ${chart('d_reg','Regressão: oposição energia–fadiga (Vigor × Fadiga física)','reta OLS com dispersão')}
  </div>
  <h2 class="sec">3 · Tabela descritiva completa</h2>
  <div class="chart">${descTable()}</div>`;
  // pos donut
  const pc=s.pos_counts,labels=Object.keys(pc),vals=Object.values(pc);
  Plotly.newPlot('d_pos',[{type:'pie',hole:.55,labels,values:vals,marker:{colors:labels.map(l=>POSC[l]||'#888')},
    textinfo:'label+percent',textfont:{size:14}}],Object.assign({},T,{height:360,showlegend:false}),cfg);
  // 3d
  const A=s.athletes;
  const traces=Object.keys(POSC).map(p=>{const g=A.filter(x=>x.pos===p);return{
    type:'scatter3d',mode:'markers',name:p,x:g.map(x=>x.idade),y:g.map(x=>x.massa),z:g.map(x=>x.estatura),
    marker:{size:5,color:POSC[p],opacity:.85},text:g.map(x=>x.id),
    hovertemplate:'%{text}<br>idade %{x} · massa %{y}kg · alt %{z}cm<extra>'+p+'</extra>'};});
  Plotly.newPlot('d_3d',traces,Object.assign({},T,{height:400,scene:{xaxis:{title:'Idade'},yaxis:{title:'Massa'},zaxis:{title:'Estatura'},
    bgcolor:'rgba(0,0,0,0)'},legend:{orientation:'h'}}),cfg);
  // normality bars + floor
  const order=D.order,sh=order.map(v=>D.vars[v].desc.shapiro),fl=order.map(v=>D.vars[v].desc.floor);
  Plotly.newPlot('d_norm',[
    {x:order.map(v=>D.lab[v]),y:sh,type:'bar',name:'Shapiro p',marker:{color:'#4dabf7'}},
    {x:order.map(v=>D.lab[v]),y:fl,type:'bar',name:'% piso',marker:{color:'#f03e3e'},yaxis:'y2'}],
    Object.assign({},T,{height:380,barmode:'group',yaxis:{title:'Shapiro p'},
     yaxis2:{title:'% piso',overlaying:'y',side:'right',range:[0,100]},
     shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:.05,y1:.05,line:{color:'#ffd43b',dash:'dot'}}],
     legend:{orientation:'h',y:1.12}}),cfg);
  // histograms overlay (key vars)
  const kv=['FadFisica','Vigor','Fadiga','Depressao'];
  Plotly.newPlot('d_hist',kv.map(v=>{const h=D.vars[v].hist;const cx=h.edges.slice(0,-1).map((e,i)=>(e+h.edges[i+1])/2);
    return{x:cx,y:h.counts,type:'bar',name:D.lab[v],marker:{color:CC[v],opacity:.6}};}),
    Object.assign({},T,{height:380,barmode:'overlay',xaxis:{title:'Escore'},yaxis:{title:'Frequência'},legend:{orientation:'h',y:1.12}}),cfg);
  // regression vigor vs fadfisica (athlete weekly means)
  const L=D.vars['FadFisica'].load; // not ideal; use obs-level via corr slope approximation
  regScatter('d_reg');
  Plotly.newPlot;
}
function regScatter(id){
  // scatter of per-athlete weekly Vigor vs FadFisica from ath data
  const vf=D.vars['FadFisica'].ath, vv=D.vars['Vigor'].ath;
  const x=[],y=[];
  vf.ids.forEach((id2,i)=>{const mf=avg(vf.z[i]),mv=avg(vv.z[i]);if(mf!=null&&mv!=null){x.push(mf);y.push(mv);}});
  const fit=ols(x,y);const xs=lin(Math.min(...x),Math.max(...x),40);
  Plotly.newPlot(id,[{x,y,mode:'markers',type:'scatter',marker:{color:'#f03e3e',size:9,opacity:.7},name:'atletas'},
    {x:xs,y:xs.map(v=>fit.a+fit.b*v),mode:'lines',line:{color:'#4dabf7',width:3},name:'OLS r='+fit.r.toFixed(2)}],
    Object.assign({},T,{height:380,xaxis:{title:'Fadiga física (média)'},yaxis:{title:'Vigor (média)'},legend:{orientation:'h',y:1.12}}),cfg);
}
function descTable(){
  let h='<table class="tbl"><tr><th>Variável</th><th>n</th><th>Média</th><th>DP</th><th>Mediana</th><th>IQR</th><th>Assim.</th><th>Curtose</th><th>% piso</th><th>Shapiro p</th></tr>';
  D.order.forEach(v=>{const d=D.vars[v].desc;h+=`<tr><td>${D.lab[v]}</td><td>${d.n}</td><td>${d.mean}</td><td>${d.sd}</td><td>${d.median}</td><td>${d.iqr}</td><td>${d.skew}</td><td>${d.kurt}</td><td>${d.floor}</td><td>${d.shapiro}</td></tr>`;});
  return h+'</table>';
}
const avg=a=>{const f=a.filter(x=>x!=null);return f.length?f.reduce((s,x)=>s+x,0)/f.length:null;};
function ols(x,y){const n=x.length,mx=avg(x),my=avg(y);let sxy=0,sxx=0,syy=0;for(let i=0;i<n;i++){sxy+=(x[i]-mx)*(y[i]-my);sxx+=(x[i]-mx)**2;syy+=(y[i]-my)**2;}const b=sxy/sxx;return{a:my-b*mx,b,r:sxy/Math.sqrt(sxx*syy)};}
const lin=(a,b,n)=>Array.from({length:n},(_,i)=>a+(b-a)*i/(n-1));

// ---------- VARIABLE (BRUMS drill-down) ----------
function viewVar(v){
  const V=D.vars[v],k=V.kpi,C=content();
  const contrib=V.corr_others['TMD']!=null?V.corr_others['TMD']:(V.corr_others['Fadiga']||0);
  C.innerHTML=`
  <div class="explain"><b>${V.lab}.</b> Aqui reunimos <b>tudo</b> o que ocorreu com esta variável no microciclo e como ela se conecta às demais: como se comportou ao longo da semana (grupo e por atleta), quanto responde ao treino (agudo e acúmulo), quanto influencia a perturbação total do humor, e qual a relação com a carga interna (FC/PSE) e externa (velocidade/distância).</div>
  <div class="kpis">
   ${kpi((k.dz_week>0?'+':'')+(k.dz_week??'–'),'Acúmulo D1→D7 (dz)','')}
   ${kpi((k.dz_acute>0?'+':'')+(k.dz_acute??'–'),'Resposta aguda pré→pós (dz)','')}
   ${kpi(k.floor+'%','Efeito piso','')}
   ${kpi(k.icc,'ICC de traço','fração entre-atletas')}
   ${kpi((contrib>0?'+':'')+contrib,'Associação com o PTH/TMD','ρ de Spearman')}
  </div>
  <h2 class="sec">1 · Como se comportou ao longo da semana</h2>
  ${chart('v_traj','Trajetória semanal — grupo (linha grossa ± EP) e cada atleta (linhas finas)','faixas vermelhas = dias de HIIT')}
  ${chart('v_heat','Perfil individual — '+V.lab+' por atleta × dia','cada célula = escore do atleta no dia')}
  <h2 class="sec">2 · Relação com a carga interna e externa</h2>
  <div class="row2">
   ${chart('v_fc','× Carga interna (FC de pico da sessão)','dias de HIIT · ρ='+(V.load.FC.r??'–'))}
   ${chart('v_pv','× Aptidão / carga externa (velocidade de pico do T-CAR)','entre atletas · ρ='+(V.load.PV.r??'–'))}
  </div>
  <h2 class="sec">3 · Associação com as outras variáveis</h2>
  ${chart('v_corr','Correlação com as demais variáveis do humor e fadiga','ρ de Spearman · destaque para o PTH/TMD')}`;
  // trajectory group + spaghetti
  const x=[1,2,3,4,5,6,7];const tr=V.traj;
  const traces=[];
  V.ath.z.forEach(row=>traces.push({x,y:row,mode:'lines',line:{color:CC[v],width:1},opacity:.18,showlegend:false,hoverinfo:'skip'}));
  const up=tr.mean.map((m,i)=>m==null?null:m+tr.se[i]),lo=tr.mean.map((m,i)=>m==null?null:m-tr.se[i]);
  traces.push({x:x.concat(x.slice().reverse()),y:up.concat(lo.slice().reverse()),fill:'toself',fillcolor:CC[v],opacity:.25,line:{width:0},showlegend:false,hoverinfo:'skip'});
  traces.push({x,y:tr.mean,mode:'lines+markers',line:{color:CC[v],width:4},marker:{size:10},name:'grupo'});
  Plotly.newPlot('v_traj',traces,Object.assign({},T,{shapes:bands(),height:440,xaxis:{title:'Dia',dtick:1},yaxis:{title:V.lab}}),cfg);
  // heatmap
  Plotly.newPlot('v_heat',[{z:V.ath.z,x,y:V.ath.ids,type:'heatmap',colorscale:'Viridis',colorbar:{title:''}}],
    Object.assign({},T,{height:Math.max(320,V.ath.ids.length*15+90),xaxis:{title:'Dia',dtick:1}}),cfg);
  // vs FC
  scatterFit('v_fc',V.load.FC.x,V.load.FC.y,'FC de pico (bpm)',V.lab,CC[v]);
  scatterFit('v_pv',V.load.PV.x,V.load.PV.y,'PV do T-CAR (km/h)',V.lab+' (média semana)',CC[v]);
  // corr others
  const os=Object.keys(V.corr_others).filter(o=>D.lab[o]);
  Plotly.newPlot('v_corr',[{x:os.map(o=>D.lab[o]),y:os.map(o=>V.corr_others[o]),type:'bar',
    marker:{color:os.map(o=>o==='TMD'?'#ffd43b':CC[o])}}],
    Object.assign({},T,{height:380,yaxis:{title:'ρ de Spearman',range:[-1,1]},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{color:'#666'}}]}),cfg);
}
function scatterFit(id,x,y,xl,yl,c){
  const xs2=[],ys2=[];x.forEach((v,i)=>{if(v!=null&&y[i]!=null){xs2.push(v);ys2.push(y[i]);}});
  const t=[{x:xs2,y:ys2,mode:'markers',type:'scatter',marker:{color:c,size:9,opacity:.55},showlegend:false}];
  if(xs2.length>3){const f=ols(xs2,ys2),xr=lin(Math.min(...xs2),Math.max(...xs2),40);
    t.push({x:xr,y:xr.map(v=>f.a+f.b*v),mode:'lines',line:{color:'#e6edf3',width:3},showlegend:false});}
  Plotly.newPlot(id,t,Object.assign({},T,{height:360,xaxis:{title:xl},yaxis:{title:yl}}),cfg);
}

// ---------- CARGA INTERNA ----------
function viewInterna(){
  const L=D.intload,C=content();
  C.innerHTML=`
  <div class="explain"><b>O que foi feito.</b> Análise da carga interna das três sessões de HIIT (S1=22/04, S2=24/04, S3=27/04): frequência cardíaca de pico e média, percepção de esforço (PSE), TRIMP cardíaco (Banister) e session-RPE. Como a carga <b>externa é fixa</b> (104% da PV), a carga interna revela a fadiga acumulada.</div>
  ${chart('i_diss','Dissociação da carga interna (padronizado z) — FC/TRIMP ↓ vs PSE/sRPE ↑','mesma carga externa; a FC de pico cai enquanto a PSE sobe = assinatura de fadiga acumulada')}
  <div class="row2">
   ${chart('i_fc','Frequência cardíaca por sessão (bpm)','')}
   ${chart('i_pse','Percepção de esforço e cargas por sessão','')}
  </div>`;
  const S=L.sessions;const z=a=>{const m=avg(a),sd=Math.sqrt(avg(a.map(x=>(x-m)**2)));return a.map(x=>(x-m)/sd);};
  Plotly.newPlot('i_diss',[
   {x:S,y:z(L.FCpico),mode:'lines+markers',name:'FC pico',line:{color:'#f03e3e',width:3},marker:{size:11},customdata:L.FCpico,hovertemplate:'%{x}: %{customdata} bpm<extra>FC pico</extra>'},
   {x:S,y:z(L.TRIMP),mode:'lines+markers',name:'TRIMP',line:{color:'#ff922b',width:3},marker:{size:11},customdata:L.TRIMP,hovertemplate:'%{x}: %{customdata}<extra>TRIMP</extra>'},
   {x:S,y:z(L.PSE),mode:'lines+markers',name:'PSE',line:{color:'#4dabf7',width:3},marker:{size:11},customdata:L.PSE,hovertemplate:'%{x}: %{customdata}<extra>PSE</extra>'},
   {x:S,y:z(L.sRPE),mode:'lines+markers',name:'session-RPE',line:{color:'#51cf66',width:3},marker:{size:11},customdata:L.sRPE,hovertemplate:'%{x}: %{customdata}<extra>sRPE</extra>'}],
   Object.assign({},T,{height:420,yaxis:{title:'z padronizado'},legend:{orientation:'h',y:1.12}}),cfg);
  Plotly.newPlot('i_fc',[{x:S,y:L.FCpico,type:'bar',name:'FC pico',marker:{color:'#f03e3e'}},
   {x:S,y:L.FCmedia,type:'bar',name:'FC média',marker:{color:'#ff8787'}}],
   Object.assign({},T,{height:360,barmode:'group',yaxis:{title:'bpm',range:[150,190]},legend:{orientation:'h',y:1.12}}),cfg);
  Plotly.newPlot('i_pse',[{x:S,y:L.PSE,type:'bar',name:'PSE',marker:{color:'#4dabf7'}},
   {x:S,y:L.TRIMP,type:'bar',name:'TRIMP',marker:{color:'#ff922b'},yaxis:'y2'}],
   Object.assign({},T,{height:360,yaxis:{title:'PSE (0–10)'},yaxis2:{title:'TRIMP',overlaying:'y',side:'right'},legend:{orientation:'h',y:1.12}}),cfg);
}

// ---------- CARGA EXTERNA ----------
function viewExterna(){
  const L=D.extload,C=content();
  C.innerHTML=`
  <div class="explain"><b>O que foi feito.</b> Carga externa derivada do T-CAR: protocolo <b>4 séries × 4 min a 104% da velocidade de pico (PV)</b> individual (esforço intermitente 12 s corrida / 6 s pausa). Velocidade média de trabalho e distância percorrida por sessão. Prescrição relativa ⇒ carga externa individualizada, mas equalizada em custo interno.</div>
  <div class="kpis">
   ${kpi(L.vel_mean+' km/h','Velocidade média (104% PV)','')}
   ${kpi(Math.round(L.dist_mean)+' m','Distância por sessão','')}
   ${kpi(Math.round(L.dist_total)+' m','Distância total (3 sessões)','~'+(L.dist_total/1000).toFixed(1)+' km')}
  </div>
  <div class="row2">
   ${chart('e_dist','Distribuição da distância por sessão entre atletas','')}
   ${chart('e_vel','Distribuição da velocidade (104% PV)','')}
  </div>
  ${chart('e_pvdist','Aptidão × carga externa — PV do T-CAR × distância por sessão','o mais apto cobre mais distância pela prescrição relativa')}`;
  Plotly.newPlot('e_dist',[{x:L.dist_vals,type:'histogram',marker:{color:'#51cf66'},nbinsx:12}],
   Object.assign({},T,{height:360,xaxis:{title:'Distância/sessão (m)'},yaxis:{title:'nº atletas'}}),cfg);
  Plotly.newPlot('e_vel',[{x:L.vel_vals,type:'histogram',marker:{color:'#4dabf7'},nbinsx:12}],
   Object.assign({},T,{height:360,xaxis:{title:'Velocidade (km/h)'},yaxis:{title:'nº atletas'}}),cfg);
  scatterFit('e_pvdist',L.pv_dist.x,L.pv_dist.y,'PV do T-CAR (km/h)','Distância/sessão (m)','#51cf66');
}

// ---------- CORRELAÇÕES ----------
function viewCorrel(){
  const C=content();
  C.innerHTML=`<div class="explain"><b>O que foi feito.</b> Matriz de correlação (ρ de Spearman) entre as subescalas do BRUMS e as medidas de fadiga, evidenciando o eixo energia–fadiga: vigor opõe-se à fadiga e ao PTH; as subescalas negativas correlacionam-se entre si.</div>
  ${chart('c_mat','Matriz de correlação (ρ de Spearman)','')}`;
  Plotly.newPlot('c_mat',[{z:D.corr.z,x:D.corr.labels,y:D.corr.labels,type:'heatmap',colorscale:'RdBu',zmid:0,zmin:-1,zmax:1,
    text:D.corr.z,texttemplate:'%{text}',textfont:{size:12}}],Object.assign({},T,{height:560}),cfg);
}

// ---------- router ----------
function content(){return document.getElementById('content');}
const SUB=D.order;
function setSub(active){
  const sn=document.getElementById('subnav');sn.style.display='flex';
  sn.innerHTML=SUB.map(v=>`<button data-sv="${v}" class="${v===active?'active':''}">${D.lab[v]}</button>`).join('');
  sn.querySelectorAll('button').forEach(b=>b.onclick=()=>{setSub(b.dataset.sv);viewVar(b.dataset.sv);window.scrollTo({top:0,behavior:'smooth'});});
}
function route(v){
  document.querySelectorAll('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.v===v));
  const sn=document.getElementById('subnav');
  if(v==='descritiva'){sn.style.display='none';viewDescritiva();}
  else if(v==='brums'){setSub('FadFisica');viewVar('FadFisica');}
  else if(v==='interna'){sn.style.display='none';viewInterna();}
  else if(v==='externa'){sn.style.display='none';viewExterna();}
  else if(v==='correl'){sn.style.display='none';viewCorrel();}
}
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>route(b.dataset.v));
route('descritiva');
</script>'''

body='<script>'+plotlyjs+'</script>\n'+APP.replace('__DATA__',DATA)
html='<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Central Analítica — Microciclo HIIT</title></head><body>'+body+'</body></html>'
open('/home/user/mdlucca/Artigos/App_Analitico.html','w',encoding='utf-8').write(html)
print('App salvo:',round(len(html)/1024,1),'KB')
