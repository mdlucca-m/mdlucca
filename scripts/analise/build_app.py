import json, plotly.offline, plotly
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
DATA=open(f'{SC}/app_data.json',encoding='utf-8').read()
plotlyjs=plotly.offline.get_plotlyjs()

APP=r'''<div id="app">
<header>
  <h1>Central Analítica — Microciclo de choque de HIIT · Handebol de elite</h1>
  <p class="sub">21–28/04/2024 · 27 atletas · 456 observações · reanálise independente (Python). Clique nos botões para gerar cada bloco analítico automaticamente.</p>
  <nav id="nav">
    <button data-v="geral" class="active">📌 Visão Geral</button>
    <button data-v="descritiva">📊 Descritiva</button>
    <button data-v="brums">🧠 BRUMS</button>
    <button data-v="interna">❤️ Carga interna</button>
    <button data-v="externa">🏃 Carga externa</button>
    <button data-v="normalidade">🔬 Normalidade</button>
    <button data-v="correl">🔗 Correlações</button>
    <button data-v="segmentado">🧩 Segmentado</button>
    <button data-v="modelos">📐 Modelos</button>
  </nav>
  <div id="subnav" class="subnav" style="display:none"></div>
  <div id="segbar" class="segbar" style="display:none">
    <span>🧩 Segmento:</span>
    <label>Dimensão <select id="segdim"><option value="">Nenhuma (todos)</option></select></label>
    <label>Grupo <select id="segsel"></select></label>
    <span id="segn" class="segn"></span>
  </div>
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
.segbar{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:12px;background:#0f1722;border:1px solid var(--bd);border-radius:10px;padding:10px 14px;font-size:.85rem;color:var(--mut)}
.segbar label{display:flex;gap:6px;align-items:center;color:var(--mut);font-weight:600}
.segbar select{background:#0b0f15;color:var(--fg);border:1px solid var(--bd);border-radius:8px;padding:6px 9px;font-size:.9rem}
.segbar .segn{color:var(--grn);font-weight:600}
main{margin-top:20px}
.explain{background:linear-gradient(90deg,#16202e,#131a24);border-left:4px solid var(--blue);border-radius:10px;padding:14px 18px;margin:16px 0;color:#cdd8e3;line-height:1.55;font-size:.98rem}
.explain b{color:#fff}
h2.sec{font-size:1.25rem;margin:26px 0 6px;color:#fff;border-bottom:1px solid var(--bd);padding-bottom:6px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:14px 0}
.kpi{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px}
.kpi .v{font-size:1.6rem;font-weight:700}.kpi .l{color:var(--mut);font-size:.76rem;margin-top:3px}.kpi .ci{color:var(--mut);font-size:.7rem}
.kpi .ic{font-size:1.15rem;float:right;opacity:.85}
.hls{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;margin:14px 0}
.hl{border-radius:14px;padding:16px 18px;border:1px solid var(--bd);background:var(--card);position:relative;overflow:hidden}
.hl .ic{font-size:1.7rem}.hl .v{font-size:1.75rem;font-weight:800;margin:6px 0 2px;color:#fff}
.hl .l{font-size:.85rem;color:#dbe4ee;font-weight:600}.hl .d{font-size:.76rem;color:var(--mut);margin-top:4px}
.hl.red{border-left:5px solid var(--red)}.hl.blue{border-left:5px solid var(--blue)}.hl.org{border-left:5px solid var(--org)}
.hl.grn{border-left:5px solid var(--grn)}.hl.vio{border-left:5px solid var(--vio)}
.interp{background:#0f1a14;border:1px solid #1e3a2a;border-left:4px solid var(--grn);border-radius:10px;padding:12px 16px;margin:8px 0 16px;font-size:.92rem;line-height:1.55;color:#c7dcd0}
.interp b{color:#fff}.interp .sig{font-weight:700}.interp .yes{color:#51cf66}.interp .no{color:#ffa94d}
.evid{background:#141024;border:1px solid #2a2140;border-left:4px solid var(--vio);border-radius:10px;padding:12px 16px;margin:8px 0;font-size:.9rem;line-height:1.5;color:#d5cdea}
.evid a{color:#b197fc;text-decoration:none}.evid a:hover{text-decoration:underline}.evid .q{color:#fff}
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
const EVID={
 axis:{q:'Vigor e fadiga são as dimensões do POMS/BRUMS mais sensíveis à carga de treino.',c:'Beedie, Terry & Lane (2000) — meta-análises do POMS e desempenho, J Appl Sport Psychol.',doi:'10.1080/10413200008404213'},
 iceberg:{q:'O perfil "iceberg" (vigor alto sobre dimensões negativas baixas) caracteriza atletas e achata-se sob fadiga acumulada.',c:'Bonfim et al. (2023) — Human Movement.',doi:'10.5114/hm.2023.132709'},
 tqr:{q:'TQR e o índice de energia (vigor−fadiga) monitoram a recuperação e respondem à carga de treino.',c:'Horta et al. (2020) — Rev Bras Med Esporte.',doi:'10.1590/1517-869220202602209364'},
 trimp:{q:'A correlação sRPE–TRIMP enfraquece na alta intensidade (r≈0,31 no HIT); o session-RPE supre a FC quando esta falha ou é suprimida.',c:'Yang et al. (2024) — Frontiers in Neuroscience.',doi:'10.3389/fnins.2024.1341972'},
 srpe:{q:'O session-RPE tem validade de critério forte com a FC (r≈0,74) e funciona como medida autônoma de carga interna.',c:'Liu et al. (2023) — meta-análise, BMC Sports Sci Med Rehabil.',doi:'10.1186/s13102-023-00712-5'},
};
function evidCard(k){const e=EVID[k];return `<div class="evid">📚 <span class="q">${e.q}</span><br>${e.c} · <a href="https://doi.org/${e.doi}" target="_blank">doi:${e.doi}</a></div>`;}
function bands(){return HIIT.map(d=>({type:'rect',xref:'x',yref:'paper',x0:d-0.15,x1:d+0.15,y0:0,y1:1,fillcolor:'#ff6b6b',opacity:0.09,line:{width:0}}));}
function el(h){const d=document.createElement('div');d.innerHTML=h;return d.firstElementChild;}
function chart(id,title,note){return `<div class="chart"><h3>${title}</h3>${note?`<p class="note">${note}</p>`:''}<div id="${id}"></div></div>`;}
function kpi(v,l,ci){return `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div>${ci?`<div class="ci">${ci}</div>`:''}</div>`;}

// ---------- VISÃO GERAL ----------
function tileI(ic,v,l,ci){return `<div class="kpi"><span class="ic">${ic}</span><div class="v">${v}</div><div class="l">${l}</div>${ci?`<div class="ci">${ci}</div>`:''}</div>`;}
function viewGeral(){
  const C=content(),bm=D.brums_means,w=D.well,e=D.extload,is=D.int_summary;
  const H=D.highlights.map(h=>`<div class="hl ${h.c}"><div class="ic">${h.icon}</div><div class="v">${h.v}</div><div class="l">${h.l}</div><div class="d">${h.d}</div></div>`).join('');
  C.innerHTML=`
  <div class="explain"><b>Panorama do grupo.</b> Síntese dos dados gerais do microciclo (27 atletas, 456 observações): os resultados mais significativos em destaque e as médias da semana (± DP) de cada domínio — humor (BRUMS), fadiga, bem-estar (recuperação, sonolência, estresse) e carga externa/interna — com gráficos robustos. Cada ícone resume um indicador do grupo.</div>
  <h2 class="sec">⭐ Resultados mais significativos</h2>
  <div class="hls">${H}</div>
  <h2 class="sec">🧠 Perfil BRUMS do grupo — média da semana (± DP)</h2>
  <div class="kpis">
   ${tileI('💪',bm.Vigor.mean+'±'+bm.Vigor.sd,'Vigor','')}
   ${tileI('🔋',bm.Fadiga.mean+'±'+bm.Fadiga.sd,'Fadiga (BRUMS)','')}
   ${tileI('🏋️',bm.FadFisica.mean+'±'+bm.FadFisica.sd,'Fadiga física (0–10)','')}
   ${tileI('🧠',bm.FadMental.mean+'±'+bm.FadMental.sd,'Fadiga mental (0–10)','')}
   ${tileI('🌀',bm.TMD.mean+'±'+bm.TMD.sd,'PTH/TMD','')}
   ${tileI('😟',bm.Tensao.mean+'±'+bm.Tensao.sd,'Tensão','')}
   ${tileI('😔',bm.Depressao.mean+'±'+bm.Depressao.sd,'Depressão','')}
   ${tileI('😠',bm.Raiva.mean+'±'+bm.Raiva.sd,'Raiva','')}
   ${tileI('😵',bm.Confusao.mean+'±'+bm.Confusao.sd,'Confusão','')}
  </div>
  ${chart('g_brums','Médias das subescalas na semana (barras com DP)','barra = média · haste = ± desvio-padrão do grupo')}
  ${chart('g_radar','Perfil de humor do grupo (radar padronizado)','forma do perfil médio nas seis subescalas')}
  <h2 class="sec">🛌 Bem-estar do grupo — média da semana (± DP)</h2>
  <div class="kpis">
   ${tileI(w.TQR.icon,w.TQR.mean+'±'+w.TQR.sd,w.TQR.lab,'alto = melhor recuperação')}
   ${tileI(w.Epworth.icon,w.Epworth.mean+'±'+w.Epworth.sd,w.Epworth.lab,'alto = mais sono')}
   ${tileI(w.PSS.icon,w.PSS.mean+'±'+w.PSS.sd,w.PSS.lab,'alto = mais estresse')}
  </div>
  ${chart('g_well','Bem-estar do grupo (média ± DP, padronizado para comparação)','')}
  <h2 class="sec">🏃 Carga externa do grupo (4×4 min a 104% da PV)</h2>
  <div class="kpis">
   ${tileI('⚡',e.vel_mean+'±'+e.vel_sd,'Velocidade média (km/h)','= 104% da PV do T-CAR')}
   ${tileI('📏',Math.round(e.dist_mean)+'±'+Math.round(e.dist_sd),'Distância média/sessão (m)','')}
   ${tileI('🗺️',Math.round(e.dist_total)+'±'+Math.round(e.dist_total_sd),'Distância total 3 sessões (m)','~'+(e.dist_total/1000).toFixed(1)+' km')}
  </div>
  <h2 class="sec">❤️ Carga interna do grupo (sessões de HIIT)</h2>
  <div class="kpis">
   ${tileI('❤️',is.FCpico,'FC de pico média (bpm)','')}
   ${tileI('🗣️',is.PSE,'PSE média (0–10)','')}
   ${tileI('📊',is.TRIMP,'TRIMP (Banister)','')}
   ${tileI('🔥',is.sRPE,'session-RPE','')}
  </div>
  ${chart('g_dist','Distribuição da distância percorrida por sessão (grupo)','')}`;
  // BRUMS bar with error bars
  const subs=['Vigor','Fadiga','FadFisica','FadMental','TMD','Tensao','Depressao','Raiva','Confusao'];
  Plotly.newPlot('g_brums',[{x:subs.map(s=>D.lab[s]),y:subs.map(s=>bm[s].mean),type:'bar',
    marker:{color:subs.map(s=>CC[s]||'#888')},error_y:{type:'data',array:subs.map(s=>bm[s].sd),color:'#aab',thickness:1.5}}],
    Object.assign({},T,{height:400,yaxis:{title:'Escore médio (± DP)'}}),cfg);
  // radar (6 subscales standardized within their scale range 0-16, vigor & fadiga fisica scaled)
  const rs=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao'];
  const rv=rs.map(s=>bm[s].mean/16*100);
  Plotly.newPlot('g_radar',[{type:'scatterpolar',r:rv.concat([rv[0]]),theta:rs.map(s=>D.lab[s]).concat([D.lab[rs[0]]]),
    fill:'toself',fillcolor:'rgba(77,171,247,.25)',line:{color:'#4dabf7',width:2}}],
    Object.assign({},T,{height:400,polar:{bgcolor:'rgba(0,0,0,0)',radialaxis:{visible:true,range:[0,40]}}}),cfg);
  // wellness standardized bars
  const wl=[['TQR',w.TQR],['Epworth',w.Epworth],['PSS',w.PSS]];
  Plotly.newPlot('g_well',[{x:wl.map(a=>a[1].lab),y:wl.map(a=>a[1].mean),type:'bar',marker:{color:['#51cf66','#ffd43b','#e64980']},
    error_y:{type:'data',array:wl.map(a=>a[1].sd),color:'#aab',thickness:1.5}}],
    Object.assign({},T,{height:360,yaxis:{title:'média (± DP)'}}),cfg);
  // distance distribution
  Plotly.newPlot('g_dist',[{x:e.dist_vals,type:'histogram',marker:{color:'#51cf66'},nbinsx:12}],
    Object.assign({},T,{height:340,xaxis:{title:'Distância/sessão (m)'},yaxis:{title:'nº atletas'}}),cfg);
}

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
// ===== segmentation state + helpers (client-side recompute) =====
let SEG={dim:'',grp:''};
function segIdx(){ // indices of athlete rows matching current segment
  const n=D.seg.order_ids.length; if(!SEG.dim||!SEG.grp) return [...Array(n).keys()];
  const arr=SEG.dim==='Aptidão'?D.seg.apt:D.seg.pos;
  return [...Array(n).keys()].filter(i=>arr[i]===SEG.grp);
}
function colVals(z,idx,c){return idx.map(i=>z[i][c]).filter(x=>x!=null);}
function segTraj(V,idx){const m=[],se=[];for(let c=0;c<7;c++){const v=colVals(V.ath.z,idx,c);
  const mu=avg(v);m.push(mu==null?null:round(mu,2));
  se.push(v.length>1?round(Math.sqrt(v.reduce((s,x)=>s+(x-mu)**2,0)/(v.length-1))/Math.sqrt(v.length),2):0);}
  return{mean:m,se};}
function segDz(V,idx){const d=[];idx.forEach(i=>{const a=V.ath.z[i][0],b=V.ath.z[i][6];if(a!=null&&b!=null)d.push(b-a);});
  if(d.length<3)return null;const mu=avg(d),sd=Math.sqrt(d.reduce((s,x)=>s+(x-mu)**2,0)/(d.length-1));return sd>0?round(mu/sd,2):null;}
function segMeanD7(V,idx){return round(avg(colVals(V.ath.z,idx,6)),2);}
const round=(x,n=2)=>x==null?null:Math.round(x*10**n)/10**n;
function fillSegBar(){const dd=document.getElementById('segdim'),ss=document.getElementById('segsel');
  if(dd.options.length<=1)Object.keys(D.seg.dims).forEach(d=>dd.add(new Option(d,d)));
  dd.value=SEG.dim;
  ss.innerHTML='';if(SEG.dim){D.seg.dims[SEG.dim].forEach(g=>ss.add(new Option(g,g)));ss.value=SEG.grp||D.seg.dims[SEG.dim][0];SEG.grp=ss.value;ss.disabled=false;}else{ss.add(new Option('—',''));ss.disabled=true;}
  const idx=segIdx();document.getElementById('segn').textContent=(SEG.dim?`n=${idx.length} atletas`:`todos (n=${idx.length})`);
}
document.getElementById('segdim').onchange=e=>{SEG.dim=e.target.value;SEG.grp='';fillSegBar();rerender();};
document.getElementById('segsel').onchange=e=>{SEG.grp=e.target.value;fillSegBar();rerender();};
let CURV=null; // current BRUMS variable
function rerender(){const a=document.querySelector('#nav .active')?.dataset.v;if(a==='segmentado')viewSegmentado();else if(a==='modelos')viewModelos();else if(CURV)viewVar(CURV);}
function ols(x,y){const n=x.length,mx=avg(x),my=avg(y);let sxy=0,sxx=0,syy=0;for(let i=0;i<n;i++){sxy+=(x[i]-mx)*(y[i]-my);sxx+=(x[i]-mx)**2;syy+=(y[i]-my)**2;}const b=sxy/sxx;return{a:my-b*mx,b,r:sxy/Math.sqrt(sxx*syy)};}
const lin=(a,b,n)=>Array.from({length:n},(_,i)=>a+(b-a)*i/(n-1));

// ---------- VARIABLE (BRUMS drill-down) ----------
function viewVar(v){
  CURV=v;const V=D.vars[v],k=V.kpi,C=content();const idx=segIdx();
  const segLbl=SEG.grp?` · <span style="color:#51cf66">${SEG.grp} (n=${idx.length})</span>`:' · todos os atletas';
  const contrib=V.corr_others['TMD']!=null?V.corr_others['TMD']:(V.corr_others['Fadiga']||0);
  const dzw=segDz(V,idx), d7=segMeanD7(V,idx);
  C.innerHTML=`
  <div class="explain"><b>${V.lab}${segLbl}.</b> Aqui reunimos <b>tudo</b> o que ocorreu com esta variável no microciclo e como ela se conecta às demais: como se comportou ao longo da semana (grupo e por atleta), quanto responde ao treino (agudo e acúmulo), quanto influencia a perturbação total do humor, e qual a relação com a carga interna (FC/PSE) e externa (velocidade/distância). Use a barra <b>🧩 Segmento</b> para recalcular por aptidão ou posição.</div>
  <div class="kpis">
   ${kpi((dzw>0?'+':'')+(dzw??'–'),'Acúmulo D1→D7 (dz)',SEG.grp?'no segmento':'amostra total')}
   ${kpi(d7??'–','Escore no D7 (média)',SEG.grp?'no segmento':'amostra total')}
   ${kpi((k.dz_acute>0?'+':'')+(k.dz_acute??'–'),'Resposta aguda pré→pós (dz)','amostra total')}
   ${kpi(k.floor+'%','Efeito piso','amostra total')}
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
  // trajectory group + spaghetti (segment-aware)
  const x=[1,2,3,4,5,6,7];const tr=segTraj(V,idx);
  const traces=[];
  idx.forEach(i=>traces.push({x,y:V.ath.z[i],mode:'lines',line:{color:CC[v],width:1},opacity:.18,showlegend:false,hoverinfo:'skip'}));
  const up=tr.mean.map((m,i)=>m==null?null:m+tr.se[i]),lo=tr.mean.map((m,i)=>m==null?null:m-tr.se[i]);
  traces.push({x:x.concat(x.slice().reverse()),y:up.concat(lo.slice().reverse()),fill:'toself',fillcolor:CC[v],opacity:.25,line:{width:0},showlegend:false,hoverinfo:'skip'});
  traces.push({x,y:tr.mean,mode:'lines+markers',line:{color:CC[v],width:4},marker:{size:10},name:SEG.grp||'grupo'});
  Plotly.newPlot('v_traj',traces,Object.assign({},T,{shapes:bands(),height:440,xaxis:{title:'Dia',dtick:1},yaxis:{title:V.lab}}),cfg);
  // heatmap (segment-aware)
  Plotly.newPlot('v_heat',[{z:idx.map(i=>V.ath.z[i]),x,y:idx.map(i=>V.ath.ids[i]),type:'heatmap',colorscale:'Viridis',colorbar:{title:''}}],
    Object.assign({},T,{height:Math.max(320,idx.length*15+90),xaxis:{title:'Dia',dtick:1}}),cfg);
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

// ---------- NORMALIDADE ----------
let NVAR='FadFisica';
function viewNormalidade(){
  const N=D.norm,C=content();const s=N.summary;
  const pfmt=p=>p<0.001?p.toExponential(1):p.toFixed(3);
  let t1='<table class="tbl"><tr><th>Variável</th><th>nível</th><th>n</th><th>W</th><th>Shapiro p</th><th>Assim.</th><th>Curtose</th><th>Normal?</th><th>Família</th></tr>';
  N.dist.forEach(r=>{t1+=`<tr><td>${r.lab}</td><td>${r.level}</td><td>${r.n}</td><td>${r.W}</td><td>${pfmt(r.p)}</td><td>${r.skew}</td><td>${r.kurt}</td><td style="color:${r.normal?'#51cf66':'#f03e3e'}">${r.normal?'sim':'NÃO'}</td><td>${r.normal?'paramétrica':'<b style="color:#ffd43b">não paramétrica</b>'}</td></tr>`;});
  t1+='</table>';
  let t2='<table class="tbl"><tr><th>Variável</th><th>n</th><th>W</th><th>Shapiro p</th><th>Assim.</th><th>Normal?</th><th>Teste pareado</th></tr>';
  N.change.forEach(r=>{t2+=`<tr><td>${r.lab}</td><td>${r.n}</td><td>${r.W}</td><td>${pfmt(r.p)}</td><td>${r.skew}</td><td style="color:${r.normal?'#51cf66':'#f03e3e'}">${r.normal?'sim':'NÃO'}</td><td>${r.normal?'t pareado':'<b style="color:#ffd43b">Wilcoxon</b>'}</td></tr>`;});
  t2+='</table>';
  C.innerHTML=`
  <div class="explain"><b>O que foi feito.</b> Teste de normalidade de todas as variáveis por Shapiro–Wilk (complementado por assimetria/curtose), em dois níveis: a <b>distribuição bruta</b> (base de descritivas e correlações) e os <b>escores de mudança por atleta</b> (base dos testes pareados). A decisão de via — paramétrica vs não paramétrica — segue diretamente destes resultados: onde a variável é não normal, adotam-se métodos não paramétricos e <b>os resultados paramétricos não são reportados</b>.</div>
  <div class="hls">
   <div class="hl red"><div class="ic">🔬</div><div class="v">${s.nn_obs}/${s.tot_obs}</div><div class="l">Variáveis NÃO normais (distribuição)</div><div class="d">Shapiro–Wilk p<0,05</div></div>
   <div class="hl org"><div class="ic">🔁</div><div class="v">${s.nn_ch}/${s.tot_ch}</div><div class="l">Mudança por atleta NÃO normal</div><div class="d">subescalas negativas</div></div>
   <div class="hl grn"><div class="ic">✅</div><div class="v">Não paramétrica</div><div class="l">Rota adotada (humor/bem-estar)</div><div class="d">Spearman · Wilcoxon · Kruskal-Wallis · PERMANOVA · bootstrap</div></div>
  </div>
  <h2 class="sec">Inspeção visual por variável — histograma, curva normal, densidade e box plot</h2>
  <div class="subnav" id="nvars">${Object.keys(N.raw).map(v=>`<button data-nv="${v}" class="${v===NVAR?'active':''}">${N.raw[v].lab}</button>`).join('')}</div>
  <div class="row2">
   ${chart('n_hist','Histograma + curva normal + densidade','barras = dados · linha branca = normal teórica (mesma média/DP) · linha colorida = densidade empírica')}
   ${chart('n_box','Box plot (mediana, IQR, outliers)','pontos = observações')}
  </div>
  ${chart('n_qqv','Gráfico Q–Q (quantil–quantil)','desvio da diagonal = não normalidade (degraus/curvatura = piso e assimetria)')}
  <h2 class="sec">1 · Normalidade da distribuição (todas as variáveis)</h2>
  <div class="chart">${t1}</div>
  <h2 class="sec">2 · Normalidade dos escores de mudança (D7−D1) — base dos testes pareados</h2>
  <div class="chart"><p class="note">Aqui o eixo energia–fadiga tem mudança aproximadamente normal, mas as subescalas negativas não — por isso os contrastes pareados usam Wilcoxon/bootstrap.</p>${t2}</div>
  <div class="explain"><b>Conclusão da rota.</b> As variáveis de humor e bem-estar são não normais ⇒ descritivas por <b>mediana (IQR)</b>, associações por <b>Spearman</b>, contrastes por <b>Wilcoxon/Mann-Whitney</b>, comparação de grupos por <b>Kruskal-Wallis</b>, multivariada por <b>PERMANOVA</b> e intervalos por <b>bootstrap</b>. Variáveis contínuas normais (velocidade, distância, T-CAR PV, CMJ) admitem via paramétrica.</div>`;
  document.querySelectorAll('#nvars button').forEach(b=>b.onclick=()=>{NVAR=b.dataset.nv;viewNormalidade();window.scrollTo({top:120,behavior:'smooth'});});
  renderNormVar();
}
function normpdf(x,m,s){return Math.exp(-0.5*((x-m)/s)**2)/(s*Math.sqrt(2*Math.PI));}
function kde(vals,xs){const n=vals.length,m=avg(vals),sd=Math.sqrt(avg(vals.map(v=>(v-m)**2)));
  const h=1.06*sd*Math.pow(n,-0.2)||1;return xs.map(x=>avg(vals.map(v=>normpdf(x,v,h))));}
function renderNormVar(){
  const R=D.norm.raw[NVAR];const v=R.vals;const m=R.mean,s=R.sd,cc=CC[NVAR]||'#4dabf7';
  const lo=Math.min(...v),hi=Math.max(...v);const xs=lin(lo,hi,80);
  const hist={x:v,type:'histogram',histnorm:'probability density',marker:{color:cc,opacity:.55},name:'dados',nbinsx:14};
  const nrm={x:xs,y:xs.map(x=>normpdf(x,m,s)),mode:'lines',line:{color:'#ffffff',width:3,dash:'dash'},name:'normal teórica'};
  const dens={x:xs,y:kde(v,xs),mode:'lines',line:{color:cc,width:3},name:'densidade empírica'};
  Plotly.newPlot('n_hist',[hist,nrm,dens],Object.assign({},T,{height:420,barmode:'overlay',
    xaxis:{title:R.lab},yaxis:{title:'densidade'},legend:{orientation:'h',y:1.13},
    annotations:[{x:.98,y:.95,xref:'paper',yref:'paper',align:'right',showarrow:false,font:{size:12,color:'#9aa7b4'},
      text:`média ${m} · mediana ${R.median} · DP ${s}<br>${R.normal?'<b style=color:#51cf66>normal</b>':'<b style=color:#f03e3e>não normal</b>'}`}]}),cfg);
  Plotly.newPlot('n_box',[{y:v,type:'box',boxpoints:'all',jitter:.4,pointpos:0,marker:{color:cc,size:4,opacity:.5},line:{color:cc},name:R.lab,boxmean:'sd'}],
    Object.assign({},T,{height:420,yaxis:{title:R.lab}}),cfg);
  const sv=v.slice().sort((a,b)=>a-b),n=sv.length;const theo=sv.map((_,i)=>jstat_ppf((i+0.5)/n));
  const ss=sv.map(x=>(x-m)/s);
  Plotly.newPlot('n_qqv',[{x:theo,y:ss,mode:'markers',marker:{color:cc,size:5,opacity:.6},name:'amostra'},
    {x:[Math.min(...theo),Math.max(...theo)],y:[Math.min(...theo),Math.max(...theo)],mode:'lines',line:{color:'#fff',dash:'dash',width:2},name:'normal'}],
    Object.assign({},T,{height:420,xaxis:{title:'Quantis teóricos (normal)'},yaxis:{title:'Quantis da amostra (z)'},legend:{orientation:'h',y:1.13}}),cfg);
}
// inverse normal CDF (Acklam approximation) for QQ theoretical quantiles
function jstat_ppf(p){const a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00];
  const b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01];
  const c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00];
  const d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00];
  const pl=0.02425,ph=1-pl;let q,r;
  if(p<pl){q=Math.sqrt(-2*Math.log(p));return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}
  if(p<=ph){q=p-0.5;r=q*q;return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);}
  q=Math.sqrt(-2*Math.log(1-p));return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}

// ---------- SEGMENTADO (comparação entre grupos) ----------
let SEGV='FadFisica';
function idxOf(dim,grp){const arr=dim==='Aptidão'?D.seg.apt:D.seg.pos;return [...Array(arr.length).keys()].filter(i=>arr[i]===grp);}
function viewSegmentado(){
  const dim=SEG.dim||'Aptidão';const groups=D.seg.dims[dim];const v=SEGV;const V=D.vars[v];const C=content();
  const segcol=['#4dabf7','#ffd43b','#f03e3e','#51cf66','#e64980'];
  C.innerHTML=`
  <div class="explain"><b>Análise segmentada e automatizada.</b> Comparação dos grupos de <b>${dim.toLowerCase()}</b> na variável selecionada: trajetória semanal por grupo, acúmulo D1→D7 (dz) por grupo, escore no D7 e tamanho de efeito entre o grupo extremo e o de referência. Troque a <b>Dimensão</b> na barra 🧩 (Aptidão ou Posição) e a variável abaixo.</div>
  <div class="subnav" id="segvars">${D.order.map(x=>`<button data-sgv="${x}" class="${x===v?'active':''}">${D.lab[x]}</button>`).join('')}</div>
  ${chart('s_traj',`Trajetória semanal por grupo — ${V.lab}`,'faixas = dias de HIIT · uma linha por grupo (± EP)')}
  <div class="row2">
   ${chart('s_dz','Acúmulo D1→D7 (dz) por grupo','magnitude da resposta em cada grupo')}
   ${chart('s_d7','Escore no D7 por grupo','estado no pior dia do microciclo')}
  </div>
  <div class="chart"><h3>Resumo estatístico por grupo (${dim})</h3><div id="s_tbl"></div></div>`;
  document.querySelectorAll('#segvars button').forEach(b=>b.onclick=()=>{SEGV=b.dataset.sgv;viewSegmentado();});
  const x=[1,2,3,4,5,6,7];
  // trajectory overlay
  const tr=[];
  groups.forEach((g,gi)=>{const idx=idxOf(dim,g);if(!idx.length)return;const t=segTraj(V,idx);
    const up=t.mean.map((m,i)=>m==null?null:m+t.se[i]),lo=t.mean.map((m,i)=>m==null?null:m-t.se[i]);
    tr.push({x:x.concat(x.slice().reverse()),y:up.concat(lo.slice().reverse()),fill:'toself',fillcolor:segcol[gi],opacity:.12,line:{width:0},showlegend:false,hoverinfo:'skip'});
    tr.push({x,y:t.mean,mode:'lines+markers',line:{color:segcol[gi],width:3},marker:{size:8},name:`${g} (n=${idx.length})`});});
  Plotly.newPlot('s_traj',tr,Object.assign({},T,{shapes:bands(),height:440,xaxis:{title:'Dia',dtick:1},yaxis:{title:V.lab},legend:{orientation:'h',y:1.13}}),cfg);
  // dz + d7 by group
  const stats=groups.map(g=>{const idx=idxOf(dim,g);return{g,n:idx.length,dz:segDz(V,idx),d7:segMeanD7(V,idx),d1:round(avg(colVals(V.ath.z,idx,0)),2)};});
  Plotly.newPlot('s_dz',[{x:stats.map(s=>s.g),y:stats.map(s=>s.dz),type:'bar',marker:{color:segcol}}],
    Object.assign({},T,{height:340,yaxis:{title:'dz D1→D7'}}),cfg);
  Plotly.newPlot('s_d7',[{x:stats.map(s=>s.g),y:stats.map(s=>s.d7),type:'bar',marker:{color:segcol}}],
    Object.assign({},T,{height:340,yaxis:{title:V.lab+' (D7)'}}),cfg);
  // table + between-group effect size (extreme vs first)
  let h='<table class="tbl"><tr><th>Grupo</th><th>n</th><th>D1</th><th>D7</th><th>dz D1→D7</th></tr>';
  stats.forEach(s=>h+=`<tr><td>${s.g}</td><td>${s.n}</td><td>${s.d1??'–'}</td><td>${s.d7??'–'}</td><td>${s.dz==null?'–':(s.dz>0?'+':'')+s.dz}</td></tr>`);
  // Hedges-like g between extreme groups at D7
  const gA=idxOf(dim,groups[0]),gB=idxOf(dim,groups[groups.length-1]);
  const a=colVals(V.ath.z,gA,6),b=colVals(V.ath.z,gB,6);
  let gtxt='';
  if(a.length>1&&b.length>1){const ma=avg(a),mb=avg(b);const va=a.reduce((s,x)=>s+(x-ma)**2,0)/(a.length-1),vb=b.reduce((s,x)=>s+(x-mb)**2,0)/(b.length-1);
    const sp=Math.sqrt(((a.length-1)*va+(b.length-1)*vb)/(a.length+b.length-2));const g=(mb-ma)/sp;
    gtxt=`<p class="note">Tamanho de efeito no D7 entre <b>${groups[0]}</b> e <b>${groups[groups.length-1]}</b>: g = ${round(g,2)} (${Math.abs(g)<0.5?'pequeno':Math.abs(g)<0.8?'médio':'grande'}).</p>`;}
  // Kruskal-Wallis (não paramétrico) no D7 entre grupos
  const kw=D.seg_kw?.[dim]?.[v];
  let kwtxt='';
  if(kw){const sig=kw.p<0.05;kwtxt=`<p class="note">🔬 <b>Kruskal–Wallis</b> (não paramétrico) no D7 entre os ${kw.k} grupos: H = ${kw.H}, p = ${kw.p<0.001?kw.p.toExponential(1):kw.p.toFixed(3)} — <b style="color:${sig?'#51cf66':'#ff922b'}">${sig?'diferença significativa':'sem diferença significativa'}</b>. (via não paramétrica, coerente com a não normalidade das variáveis de humor.)</p>`;}
  document.getElementById('s_tbl').innerHTML=h+'</table>'+gtxt+kwtxt;
}

// ===== MODELOS: solvers estatísticos client-side =====
function gauss(A,b){const n=b.length;for(let i=0;i<n;i++){let p=i;for(let r=i+1;r<n;r++)if(Math.abs(A[r][i])>Math.abs(A[p][i]))p=r;[A[i],A[p]]=[A[p],A[i]];[b[i],b[p]]=[b[p],b[i]];for(let r=i+1;r<n;r++){const f=A[r][i]/A[i][i];for(let c=i;c<n;c++)A[r][c]-=f*A[i][c];b[r]-=f*b[i];}}const x=new Array(n).fill(0);for(let i=n-1;i>=0;i--){let s=b[i];for(let c=i+1;c<n;c++)s-=A[i][c]*x[c];x[i]=s/A[i][i];}return x;}
function polyfit(x,y,d){const m=d+1,A=[],b=[];for(let i=0;i<m;i++){b.push(0);A.push(new Array(m).fill(0));}for(let k=0;k<x.length;k++){for(let i=0;i<m;i++){for(let j=0;j<m;j++)A[i][j]+=Math.pow(x[k],i+j);b[i]+=y[k]*Math.pow(x[k],i);}}return gauss(A,b);}
function polyval(c,x){let s=0;for(let i=c.length-1;i>=0;i--)s=s*x+c[i];return s;}
function polyder(c){const d=[];for(let i=1;i<c.length;i++)d.push(i*c[i]);return d;}
function aic(y,yh,k){const n=y.length;let rss=0;for(let i=0;i<n;i++)rss+=(y[i]-yh[i])**2;return n*Math.log(rss/n)+2*k;}
function r2(y,yh){const my=avg(y);let ss=0,sr=0;for(let i=0;i<y.length;i++){ss+=(y[i]-my)**2;sr+=(y[i]-yh[i])**2;}return 1-sr/ss;}
function betacf(a,b,x){const qab=a+b,qap=a+1,qam=a-1;let c=1,d=1-qab*x/qap;if(Math.abs(d)<1e-30)d=1e-30;d=1/d;let h=d;for(let m=1;m<200;m++){const m2=2*m;let aa=m*(b-m)*x/((qam+m2)*(a+m2));d=1+aa*d;if(Math.abs(d)<1e-30)d=1e-30;c=1+aa/c;if(Math.abs(c)<1e-30)c=1e-30;d=1/d;h*=d*c;aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2));d=1+aa*d;if(Math.abs(d)<1e-30)d=1e-30;c=1+aa/c;if(Math.abs(c)<1e-30)c=1e-30;d=1/d;const del=d*c;h*=del;if(Math.abs(del-1)<3e-7)break;}return h;}
function gammln(x){const c=[76.18009172947146,-86.50532032941677,24.01409824083091,-1.231739572450155,0.1208650973866179e-2,-0.5395239384953e-5];let y=x,t=x+5.5;t-=(x+0.5)*Math.log(t);let s=1.000000000190015;for(let j=0;j<6;j++){y++;s+=c[j]/y;}return -t+Math.log(2.5066282746310005*s/x);}
function betai(a,b,x){if(x<=0)return 0;if(x>=1)return 1;const bt=Math.exp(gammln(a+b)-gammln(a)-gammln(b)+a*Math.log(x)+b*Math.log(1-x));return x<(a+1)/(a+b+2)?bt*betacf(a,b,x)/a:1-bt*betacf(b,a,1-x)/b;}
function tpval2(t,df){if(df<=0)return NaN;return betai(df/2,0.5,df/(df+t*t));}  // two-sided
function pairedT(a,b){const d=[];for(let i=0;i<a.length;i++)if(a[i]!=null&&b[i]!=null)d.push(a[i]-b[i]);const n=d.length;if(n<3)return null;const m=avg(d),sd=Math.sqrt(d.reduce((s,x)=>s+(x-m)**2,0)/(n-1));if(sd===0)return{t:0,p:1,n};const t=m/(sd/Math.sqrt(n));return{t,p:tpval2(t,n-1),n,mean:m};}
function holm(ps){const idx=ps.map((p,i)=>[p,i]).sort((a,b)=>a[0]-b[0]);const adj=new Array(ps.length);let run=0;idx.forEach((pi,r)=>{run=Math.max(run,(ps.length-r)*pi[0]);adj[pi[1]]=Math.min(run,1);});return adj;}
function rocCurve(scores,labels){const pairs=scores.map((s,i)=>[s,labels[i]]).filter(p=>p[0]!=null).sort((a,b)=>b[0]-a[0]);const P=pairs.filter(p=>p[1]===1).length,N=pairs.length-P;let tp=0,fp=0;const fpr=[0],tpr=[0];pairs.forEach(p=>{if(p[1]===1)tp++;else fp++;tpr.push(tp/P);fpr.push(fp/N);});let auc=0;for(let i=1;i<fpr.length;i++)auc+=(fpr[i]-fpr[i-1])*(tpr[i]+tpr[i-1])/2;return{fpr,tpr,auc};}
function bfBIC(t,n){if(!isFinite(t)||n<3)return null;const bf01=Math.sqrt(n)*Math.pow(1+t*t/(n-1),-n/2);return 1/bf01;}
function bfLabel(bf){if(bf==null)return'–';if(bf>100)return'extrema (H1)';if(bf>30)return'muito forte (H1)';if(bf>10)return'forte (H1)';if(bf>3)return'moderada (H1)';if(bf>1)return'anedótica (H1)';if(bf>1/3)return'anedótica (H0)';if(bf>1/10)return'moderada (H0)';return'forte (H0)';}

// ---------- MODELOS (tudo, segmentado) ----------
let MVAR='FadFisica';
function viewModelos(){
  const C=content();const idx=segIdx();const V=D.vars[MVAR];
  const segLbl=SEG.grp?`<span style="color:#51cf66">${SEG.grp} (n=${idx.length})</span>`:'amostra total (n='+idx.length+')';
  C.innerHTML=`
  <div class="explain"><b>Modelos — tudo em um clique.</b> Para a variável selecionada e o segmento ativo (${segLbl}), gera: ajustes linear/quadrático/cúbico (AIC/R²), limites e derivadas (velocidade e aceleração), curva ROC, post-hoc par a par entre dias, análise bayesiana (fator de Bayes) e estrutura multivariada. Troque o segmento na barra 🧩 e a variável abaixo — tudo recalcula.</div>
  <div class="subnav" id="mvars">${D.order.map(x=>`<button data-mv="${x}" class="${x===MVAR?'active':''}">${D.lab[x]}</button>`).join('')}</div>
  <h2 class="sec">▶️ Trajetória em tempo real</h2>
  ${chart('m_anim','Reprodução dia a dia — clique em ▶ Reproduzir','a linha corre pela semana; a bola marca o dia atual')}
  <h2 class="sec">📈 Ajustes lineares e não lineares (polinomial)</h2>
  ${chart('m_fit','Ajustes à trajetória diária — linear · quadrático · cúbico','melhor modelo por AIC destacado na legenda')}
  <div class="chart"><div id="m_fittbl"></div></div>
  <div class="interp" id="i_fit"></div>
  <h2 class="sec">🧮 Limites e derivadas</h2>
  ${chart('m_der','Velocidade (dy/dt) e aceleração (d²y/dt²) do ajuste cúbico','onde a mudança é mais rápida e onde acelera/desacelera')}
  <div class="interp" id="i_der"></div>
  <h2 class="sec">🎯 Curva ROC</h2>
  <div class="row2">${chart('m_roc','ROC: a variável discrimina o dia de acúmulo (D7) do baseline (D1)?','')}
  ${chart('m_roc2','ROC: discrimina dia de fadiga física alta?','')}</div>
  <div class="interp" id="i_roc"></div>
  <h2 class="sec">🔬 Post-hoc — comparações par a par entre dias</h2>
  ${chart('m_post','Significância (−log₁₀ p, Holm) dos contrastes entre dias','quanto mais claro, mais significativo · pareado por atleta')}
  <div class="chart"><div id="m_posttbl"></div></div>
  <div class="interp" id="i_post"></div>
  <h2 class="sec">📊 Análise bayesiana (fator de Bayes, aproximação BIC)</h2>
  ${chart('m_bayes','Evidência bayesiana da mudança D1→D7 por variável','BF₁₀>3 favorece efeito; <1/3 favorece nulo')}
  <div class="interp" id="i_bayes"></div>
  <h2 class="sec">🔗 Estrutura multivariada</h2>
  ${chart('m_mv','Correlação entre-atletas (segmento)','PERMANOVA/Hotelling na amostra total: ver relatório multivariado')}
  <div class="interp" id="i_mv"></div>
  <h2 class="sec">📚 Evidências científicas</h2>
  <div id="m_evid"></div>`;
  document.querySelectorAll('#mvars button').forEach(b=>b.onclick=()=>{MVAR=b.dataset.mv;viewModelos();window.scrollTo({top:120,behavior:'smooth'});});
  renderModelos(idx);
}
function renderModelos(idx){
  const V=D.vars[MVAR];const x=[1,2,3,4,5,6,7];const t=segTraj(V,idx);
  const xs=lin(1,7,120);const valid=x.filter((_,i)=>t.mean[i]!=null);const yv=t.mean.filter(m=>m!=null);
  // fits
  const fits={};['1','2','3'].forEach(d=>{const c=polyfit(valid,yv,+d);fits[d]={c,aic:aic(yv,valid.map(xx=>polyval(c,xx)),+d+1),r2:r2(yv,valid.map(xx=>polyval(c,xx)))};});
  const best=['1','2','3'].reduce((a,b)=>fits[a].aic<fits[b].aic?a:b);const nm={'1':'linear','2':'quadrático','3':'cúbico'};
  const ftr=[{x:valid,y:yv,mode:'markers',marker:{color:'#fff',size:9},name:'média diária'}];
  const fcol={'1':'#4dabf7','2':'#ffd43b','3':'#f03e3e'};
  ['1','2','3'].forEach(d=>ftr.push({x:xs,y:xs.map(v=>polyval(fits[d].c,v)),mode:'lines',line:{color:fcol[d],width:d===best?4:2,dash:d===best?'solid':'dot'},name:nm[d]+(d===best?' ✓ (melhor AIC)':'')}));
  Plotly.newPlot('m_fit',ftr,Object.assign({},T,{shapes:bands(),height:420,xaxis:{title:'Dia',dtick:1},yaxis:{title:V.lab},legend:{orientation:'h',y:1.13}}),cfg);
  document.getElementById('m_fittbl').innerHTML='<table class="tbl"><tr><th>Modelo</th><th>AIC</th><th>R²</th><th>Melhor?</th></tr>'+['1','2','3'].map(d=>`<tr><td>${nm[d]}</td><td>${round(fits[d].aic,1)}</td><td>${round(fits[d].r2,3)}</td><td>${d===best?'✓':''}</td></tr>`).join('')+'</table>';
  // derivatives (cubic)
  const c3=fits['3'].c,d1=polyder(c3),d2=polyder(d1);
  Plotly.newPlot('m_der',[
    {x:xs,y:xs.map(v=>polyval(d1,v)),mode:'lines',line:{color:'#4dabf7',width:3},name:'velocidade dy/dt'},
    {x:xs,y:xs.map(v=>polyval(d2,v)),mode:'lines',line:{color:'#f03e3e',width:3},name:'aceleração d²y/dt²'}],
    Object.assign({},T,{shapes:bands().concat([{type:'line',xref:'paper',x0:0,x1:1,y0:0,y1:0,line:{color:'#666',dash:'dot'}}]),height:400,xaxis:{title:'Dia',dtick:1},legend:{orientation:'h',y:1.13}}),cfg);
  // ROC accumulation D7 vs D1
  const inv=(MVAR==='Vigor')?-1:1;
  const sc=[],lb=[];idx.forEach(i=>{const a=V.ath.z[i][0],b=V.ath.z[i][6];if(a!=null){sc.push(inv*a);lb.push(0);}if(b!=null){sc.push(inv*b);lb.push(1);}});
  const rc=rocCurve(sc,lb);
  Plotly.newPlot('m_roc',[{x:rc.fpr,y:rc.tpr,mode:'lines',line:{color:'#f03e3e',width:3},name:`AUC = ${round(rc.auc,2)}`},{x:[0,1],y:[0,1],mode:'lines',line:{color:'#666',dash:'dash'},name:'acaso'}],Object.assign({},T,{height:360,xaxis:{title:'1−especificidade'},yaxis:{title:'sensibilidade'},legend:{orientation:'h',y:1.13}}),cfg);
  // ROC high fatigue day (FadFisica top tertile) — using this var to discriminate
  const ff=D.vars['FadFisica'].ath.z;const allf=[];idx.forEach(i=>ff[i].forEach(x2=>{if(x2!=null)allf.push(x2);}));allf.sort((a,b)=>a-b);const thr=allf[Math.floor(allf.length*2/3)]||7;
  const sc2=[],lb2=[];idx.forEach(i=>{for(let c=0;c<7;c++){const val=V.ath.z[i][c],f=ff[i][c];if(val!=null&&f!=null){sc2.push(inv*val);lb2.push(f>=thr?1:0);}}});
  const rc2=rocCurve(sc2,lb2);
  Plotly.newPlot('m_roc2',[{x:rc2.fpr,y:rc2.tpr,mode:'lines',line:{color:'#ff922b',width:3},name:`AUC = ${round(rc2.auc,2)}`},{x:[0,1],y:[0,1],mode:'lines',line:{color:'#666',dash:'dash'},name:'acaso'}],Object.assign({},T,{height:360,xaxis:{title:'1−especificidade'},yaxis:{title:'sensibilidade'},legend:{orientation:'h',y:1.13}}),cfg);
  // post-hoc pairwise days
  const cols=[0,1,2,3,4,5,6];const raw=[],pairsL=[];
  for(let i=0;i<7;i++)for(let j=i+1;j<7;j++){const a=idx.map(k=>V.ath.z[k][i]),b=idx.map(k=>V.ath.z[k][j]);const r=pairedT(a,b);if(r){raw.push(r.p);pairsL.push([i,j,r]);}}
  const adj=holm(raw);const Z=Array.from({length:7},()=>new Array(7).fill(null));
  pairsL.forEach((pl,q)=>{const val=-Math.log10(Math.max(adj[q],1e-6));Z[pl[0]][pl[1]]=val;Z[pl[1]][pl[0]]=val;});
  Plotly.newPlot('m_post',[{z:Z,x:['D1','D2','D3','D4','D5','D6','D7'],y:['D1','D2','D3','D4','D5','D6','D7'],type:'heatmap',colorscale:'Viridis',colorbar:{title:'−log₁₀ p'}}],Object.assign({},T,{height:400}),cfg);
  const sig=pairsL.map((pl,q)=>({d:`D${pl[0]+1}×D${pl[1]+1}`,dif:round(pl[2].mean,2),p:adj[q]})).filter(o=>o.p<0.05).sort((a,b)=>a.p-b.p);
  document.getElementById('m_posttbl').innerHTML='<h3>Pares significativos (Holm p<0,05): '+sig.length+' de 21</h3><table class="tbl"><tr><th>Par</th><th>Δ</th><th>p (Holm)</th></tr>'+sig.slice(0,12).map(o=>`<tr><td>${o.d}</td><td>${o.dif>0?'+':''}${o.dif}</td><td>${o.p<0.001?o.p.toExponential(1):o.p.toFixed(3)}</td></tr>`).join('')+'</table>';
  // bayesian: BF10 (BIC approx) for change D1->D7 per variable in segment
  const bvars=D.order;const bf=bvars.map(v=>{const V2=D.vars[v];const d=[];idx.forEach(i=>{const a=V2.ath.z[i][0],b=V2.ath.z[i][6];if(a!=null&&b!=null)d.push(b-a);});if(d.length<3)return null;const m=avg(d),sd=Math.sqrt(d.reduce((s,x)=>s+(x-m)**2,0)/(d.length-1));if(sd===0)return null;const t=m/(sd/Math.sqrt(d.length));return bfBIC(t,d.length);});
  Plotly.newPlot('m_bayes',[{x:bvars.map(v=>D.lab[v]),y:bf.map(b=>b==null?0:Math.log10(Math.max(b,1e-3))),type:'bar',marker:{color:bf.map(b=>b==null?'#555':b>3?'#f03e3e':b<1/3?'#4dabf7':'#ffd43b')},
    text:bf.map(b=>b==null?'–':(b>=1?b.toFixed(1):'1/'+(1/b).toFixed(1))),textposition:'outside'}],
    Object.assign({},T,{height:400,yaxis:{title:'log₁₀ BF₁₀'},shapes:[{type:'line',xref:'paper',x0:0,x1:1,y0:Math.log10(3),y1:Math.log10(3),line:{color:'#f03e3e',dash:'dot'}},{type:'line',xref:'paper',x0:0,x1:1,y0:Math.log10(1/3),y1:Math.log10(1/3),line:{color:'#4dabf7',dash:'dot'}}]}),cfg);
  // multivariate corr in segment
  const TR=['FadFisica','Fadiga','TMD','Vigor'];const M=TR.map(a=>TR.map(b=>{const xa=[],ya=[];idx.forEach(i=>{const va=avg(D.vars[a].ath.z[i].filter(z=>z!=null)),vb=avg(D.vars[b].ath.z[i].filter(z=>z!=null));if(va!=null&&vb!=null){xa.push(va);ya.push(vb);}});return round(ols(xa,ya).r,2);}));
  Plotly.newPlot('m_mv',[{z:M,x:TR.map(v=>D.lab[v]),y:TR.map(v=>D.lab[v]),type:'heatmap',colorscale:'RdBu',zmid:0,zmin:-1,zmax:1,text:M,texttemplate:'%{text}'}],Object.assign({},T,{height:380}),cfg);
  // ===== animação em tempo real =====
  const ym=t.mean.map(m=>m==null?null:m);const yr=[Math.min(...ym.filter(x=>x!=null))-1,Math.max(...ym.filter(x=>x!=null))+1];
  const frames=[];for(let k=1;k<=7;k++){const mk=ym[k-1];frames.push({name:''+k,data:[{x:x.slice(0,k),y:ym.slice(0,k)},{x:mk==null?[]:[k],y:mk==null?[]:[mk]}]});}
  Plotly.newPlot('m_anim',[{x:[x[0]],y:[ym[0]],mode:'lines+markers',line:{color:CC[MVAR],width:4},marker:{size:8},name:V.lab},{x:[x[0]],y:[ym[0]],mode:'markers',marker:{color:'#fff',size:16,line:{color:CC[MVAR],width:3}},showlegend:false}],
    Object.assign({},T,{shapes:bands(),height:400,xaxis:{title:'Dia',dtick:1,range:[0.8,7.2]},yaxis:{title:V.lab,range:yr},
     updatemenus:[{type:'buttons',showactive:false,x:0,y:1.18,buttons:[
       {label:'▶ Reproduzir',method:'animate',args:[null,{frame:{duration:650,redraw:true},transition:{duration:300},fromcurrent:true}]},
       {label:'⏸ Pausar',method:'animate',args:[[null],{frame:{duration:0,redraw:false},mode:'immediate'}]}]}]}),cfg);
  Plotly.addFrames('m_anim',frames);
  // ===== interpretações automáticas (por que sig/não sig) =====
  const set=(id,html)=>{const e=document.getElementById(id);if(e)e.innerHTML=html;};
  set('i_fit',`<b>Resultado:</b> melhor ajuste = <b>${nm[best]}</b> (AIC ${round(fits[best].aic,1)}; R² ${round(fits[best].r2,3)}). `+
    (best==='3'?`<b class="sig">Por que não-linear:</b> a curva sobe no início, alivia no meio da semana e <b>precipita-se no Dia 7</b> — um padrão em três fases que a reta (R² ${round(fits['1'].r2,3)}) não capta; o ganho de R² até o cúbico e a queda do AIC confirmam a curvatura. ${evidCard('axis')}`
    :`<b class="sig">Por que ${nm[best]}:</b> a trajetória é bem descrita por esse grau; graus maiores não reduzem o AIC.`));
  const gx=lin(1,7,120),vv=gx.map(g=>polyval(d1,g)),aa=gx.map(g=>polyval(d2,g));
  const ivmax=gx[vv.map(Math.abs).indexOf(Math.max(...vv.map(Math.abs)))];let cross=null;for(let i=1;i<aa.length;i++)if(aa[i-1]*aa[i]<0)cross=gx[i];
  set('i_der',`<b>Resultado:</b> a <b>velocidade da mudança</b> é máxima por volta do <b>Dia ${round(ivmax,1)}</b>${cross?`, e a <b>aceleração</b> muda de sinal perto do Dia ${round(cross,1)}`:''}. <b class="sig">Interpretação:</b> a deterioração não é uniforme — ela ${ivmax>5?'<b>se precipita no fim do microciclo</b> (acúmulo)':'é mais rápida no início'}, coerente com a fadiga acumulada. ${evidCard('iceberg')}`);
  const aw=a=>a>=.9?'excelente':a>=.8?'boa':a>=.7?'aceitável':a>=.6?'fraca':'ao acaso';
  set('i_roc',`<b>Resultado:</b> AUC do acúmulo (D7 vs D1) = <b>${round(rc.auc,2)}</b> (${aw(rc.auc)}). <b class="sig ${rc.auc>=.7?'yes':'no'}">${rc.auc>=.7?'Discrimina bem':'Discrimina pouco'}:</b> ${rc.auc>=.7?`o estado do Dia 7 separa-se do baseline — o <b>sinal está no acúmulo</b>. Em contraste, discriminar a sessão isolada costuma dar AUC≈0,5 (não distingue), o que reposiciona o monitoramento na <b>tendência</b>, não no evento.`:`o dia isolado não se separa bem — reforça monitorar por tendência.`} ${evidCard('tqr')}`);
  set('i_post',`<b>Resultado:</b> <b>${sig.length} de 21</b> pares de dias significativos (Holm). <b class="sig">Por que estes e não os outros:</b> os contrastes que sobrevivem à correção envolvem sobretudo o <b>Dia 7</b> (efeito grande, acúmulo máximo); os do meio da semana não sobrevivem porque o efeito é pequeno e a variância entre atletas é alta — a correção de Holm penaliza o excesso de comparações e só mantém os contrastes robustos.`);
  const bi=D.order.indexOf(MVAR);const bfv=bf[bi];
  set('i_bayes',`<b>Resultado (${V.lab}):</b> BF₁₀ ≈ <b>${bfv==null?'–':(bfv>=1?bfv.toFixed(1):'1/'+(1/bfv).toFixed(1))}</b> — evidência ${bfLabel(bfv)}. <b class="sig">Por quê:</b> ${bfv==null?'amostra insuficiente':bfv>3?'a mudança D1→D7 é consistente e grande, então os dados favorecem o efeito.':bfv<1/3?'a mudança é pequena/instável (efeito piso), então os dados favorecem a <b>ausência</b> de efeito — não é só "p>0,05", é evidência a favor do nulo.':'a evidência é ambígua (nem efeito nem nulo demonstrados) — tipicamente falta de poder.'} As subescalas negativas tendem a BF₁₀<1/3 pelo efeito piso. ${evidCard('axis')}`);
  const vf=M[3][1];// Vigor x Fadiga in TR order [FadFisica,Fadiga,TMD,Vigor]
  set('i_mv',`<b>Resultado:</b> no nível do atleta, vigor e fadiga correlacionam-se <b>${vf}</b> (oposição), e fadiga↔fadiga física/TMD são positivas. <b class="sig">Interpretação:</b> as variáveis não são independentes — formam um <b>eixo bipolar energia↔fadiga</b>, justificando tratá-lo como a dimensão-alvo do monitoramento. ${evidCard('iceberg')}`);
  set('m_evid',[evidCard('axis'),evidCard('iceberg'),evidCard('tqr'),evidCard('srpe'),evidCard('trimp')].join(''));
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
  const sn=document.getElementById('subnav'),sb=document.getElementById('segbar');
  const showSeg=(v==='brums'||v==='segmentado'||v==='modelos');
  sb.style.display=showSeg?'flex':'none';
  if(v==='segmentado'&&!SEG.dim){SEG.dim='Aptidão';SEG.grp='';}
  if(showSeg)fillSegBar();
  if(v==='geral'){sn.style.display='none';viewGeral();}
  else if(v==='descritiva'){sn.style.display='none';viewDescritiva();}
  else if(v==='brums'){setSub(CURV||'FadFisica');viewVar(CURV||'FadFisica');}
  else if(v==='interna'){sn.style.display='none';viewInterna();}
  else if(v==='externa'){sn.style.display='none';viewExterna();}
  else if(v==='normalidade'){sn.style.display='none';viewNormalidade();}
  else if(v==='correl'){sn.style.display='none';viewCorrel();}
  else if(v==='segmentado'){sn.style.display='none';viewSegmentado();}
  else if(v==='modelos'){sn.style.display='none';viewModelos();}
}
document.querySelectorAll('#nav button').forEach(b=>b.onclick=()=>route(b.dataset.v));
route('geral');
</script>'''

body='<script>'+plotlyjs+'</script>\n'+APP.replace('__DATA__',DATA)
html='<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Central Analítica — Microciclo HIIT</title></head><body>'+body+'</body></html>'
open('/home/user/mdlucca/Artigos/App_Analitico.html','w',encoding='utf-8').write(html)
print('App salvo:',round(len(html)/1024,1),'KB')
