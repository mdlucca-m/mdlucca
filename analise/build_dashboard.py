import base64, json, pathlib
data=open('analise/data.json').read()

html = r'''<title>Painel — Carga, Humor e HIIT (Handebol)</title>
<style>
:root{
 --paper:#f6f7f9;--card:#ffffff;--ink:#141a22;--muted:#5a6572;--line:#e3e7ec;
 --pre:#2563eb;--pos:#d6323b;--rec:#0e9e6e;--accent:#4b47c9;--wash:#eef1f6;--chip:#eceff5;--grid:#e9edf2;
}
@media (prefers-color-scheme:dark){:root{--paper:#0d1117;--card:#141b24;--ink:#e7ecf2;--muted:#93a0b0;--line:#243040;--wash:#161f2b;--pre:#5b8bff;--pos:#f26169;--rec:#34c793;--accent:#8b88ff;--chip:#1c2634;--grid:#1e2836;}}
:root[data-theme=dark]{--paper:#0d1117;--card:#141b24;--ink:#e7ecf2;--muted:#93a0b0;--line:#243040;--wash:#161f2b;--pre:#5b8bff;--pos:#f26169;--rec:#34c793;--accent:#8b88ff;--chip:#1c2634;--grid:#1e2836;}
:root[data-theme=light]{--paper:#f6f7f9;--card:#fff;--ink:#141a22;--muted:#5a6572;--line:#e3e7ec;--pre:#2563eb;--pos:#d6323b;--rec:#0e9e6e;--accent:#4b47c9;--wash:#eef1f6;--chip:#eceff5;--grid:#e9edf2;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.6}
.wrap{max-width:960px;margin:0 auto;padding:0 22px 90px}
header{padding:60px 0 26px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 14px}
h1{font-family:Georgia,'Times New Roman',serif;font-weight:700;font-size:clamp(28px,5vw,44px);line-height:1.12;margin:0;text-wrap:balance;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:17px;margin:16px 0 0;max-width:62ch}
.meta{display:flex;flex-wrap:wrap;gap:26px;margin-top:24px}
.meta div{font-size:13px;color:var(--muted)}
.meta b{display:block;font-family:Georgia,serif;font-size:22px;color:var(--ink);font-weight:700}
h2{font-family:Georgia,serif;font-size:24px;margin:52px 0 4px;letter-spacing:-.01em}
h2 .n{color:var(--accent);font-size:15px;font-weight:700;margin-right:10px;font-family:-apple-system,sans-serif}
.lead{color:var(--muted);margin:0 0 18px;max-width:66ch}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:18px 0}
.ctl{margin:2px 0 16px}
.ctl .lbl{font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:700;margin-bottom:8px}
.btns{display:flex;flex-wrap:wrap;gap:8px}
button.chip{font:inherit;font-size:13.5px;font-weight:600;color:var(--ink);background:var(--chip);border:1px solid transparent;border-radius:999px;padding:7px 14px;cursor:pointer;transition:.15s;line-height:1}
button.chip:hover{border-color:var(--accent)}
button.chip[aria-pressed=true]{background:var(--accent);color:#fff}
button.chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.charthead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:6px 2px 2px;flex-wrap:wrap}
.chartttl{font-weight:700;font-size:15px}
.chartsub{color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums}
svg{width:100%;height:auto;display:block;overflow:visible}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:12.5px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{width:11px;height:11px;border-radius:3px;display:inline-block}
.note{font-size:12px;color:var(--muted);margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
ul.take{list-style:none;padding:0;margin:14px 0}
ul.take li{padding:11px 0 11px 28px;border-bottom:1px solid var(--line);position:relative;max-width:72ch}
ul.take li:before{content:'';position:absolute;left:3px;top:19px;width:9px;height:9px;border-radius:50%;background:var(--accent)}
.up{color:var(--pos);font-weight:700}.dn{color:var(--rec);font-weight:700}
.foot{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
code{background:var(--wash);padding:1px 6px;border-radius:5px;font-size:13px;font-family:ui-monospace,Menlo,monospace}
p{max-width:72ch}
</style>
<div class="wrap">
<header>
 <p class="eyebrow">Ciência do Esporte · Handebol de alto rendimento</p>
 <h1>Painel interativo — carga, humor e HIIT</h1>
 <p class="sub">Escolha a variável e o recorte. Os botões são gerados a partir dos próprios dados; os gráficos recalculam ao vivo por momento, dia, série ou sessão.</p>
 <div class="meta">
  <div><b>27</b>atletas</div><div><b>277</b>coletas de humor</div><div><b>8</b>dias de treino</div><div><b>4</b>sessões HIIT</div>
 </div>
</header>

<h2><span class="n">01</span>Explorador do humor (BRUMS)</h2>
<p class="lead">Média de cada subescala (escore T, população=50) segmentada como você escolher. A linha tracejada marca T=50.</p>
<div class="panel">
 <div class="ctl"><div class="lbl">Variável</div><div class="btns" id="bVar"></div></div>
 <div class="ctl"><div class="lbl">Segmentar por</div><div class="btns" id="bSeg"></div></div>
 <div class="charthead"><div class="chartttl" id="bTtl"></div><div class="chartsub" id="bSub"></div></div>
 <svg id="bChart" viewBox="0 0 720 340" role="img" aria-label="Gráfico BRUMS"></svg>
 <div class="legend" id="bLeg"></div>
 <div class="note" id="bNote"></div>
</div>

<h2><span class="n">02</span>Explorador do HIIT</h2>
<p class="lead">Frequência cardíaca e percepção de esforço, por série (média das 4 sessões) ou por sessão (média das 4 séries).</p>
<div class="panel">
 <div class="ctl"><div class="lbl">Variável</div><div class="btns" id="hVar"></div></div>
 <div class="ctl"><div class="lbl">Segmentar por</div><div class="btns" id="hSeg"></div></div>
 <div class="charthead"><div class="chartttl" id="hTtl"></div><div class="chartsub" id="hSub"></div></div>
 <svg id="hChart" viewBox="0 0 720 340" role="img" aria-label="Gráfico HIIT"></svg>
 <div class="note" id="hNote"></div>
</div>

<h2><span class="n">03</span>Leitura dos dados</h2>
<ul class="take">
 <li><b>Do Pré para o Pós-treino:</b> Vigor <span class="dn">cai</span> (43,8→40,7; d=−0,38) e Fadiga <span class="up">sobe</span> (49,9→54,1; d=+0,40), ambos p=0,002 — assinatura aguda da carga. Selecione <em>Vigor</em> e <em>Fadiga</em> por <em>Momento</em> para ver.</li>
 <li><b>A tensão diminui após treinar</b> (45,5→42,8; d=−0,45; p&lt;0,001): o treino regulou ansiedade, não gerou estresse.</li>
 <li><b>A fadiga comanda o TMD</b> (Spearman r=+0,74), à frente de Depressão (+0,63) e do Vigor (−0,61).</li>
 <li><b>HIIT com dose crescente:</b> escolha <em>PSE</em> por <em>Série</em> — sobe de 5,3 a 9,4; a FC pré-série cresce (112→132 bpm), sinal de recuperação incompleta.</li>
 <li><b>TMD acompanha a periodização:</b> por <em>Dia</em>, picos nos dias 4 e 7; alívio nos dias 5 e 8.</li>
</ul>

<div class="foot">
<p><b>Notas.</b> BRUMS-24 em escore T; TMD = (Tensão+Depressão+Raiva+Fadiga+Confusão) − Vigor. Recortes por momento (Pré/Pós/Rec), dia (1–8) ou perfil. HIIT: FC em bpm e PSE 0–10, sobre 27 atletas × 4 sessões; Δ FC = pós − pré por série. Eixo vertical com piso ajustado ao intervalo dos dados para destacar diferenças (valores rotulados). Fontes: <code>COLETAS.xlsx</code>, <code>HIIT_FC_PSE.xlsx</code>, <code>resultados_handebol.xlsx</code>.</p>
</div>
</div>
<script>
const DATA = __DATA__;
const $=id=>document.getElementById(id);
const mean=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:null;
const fmt=(x,d=1)=>x==null?'–':x.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
const NS='http://www.w3.org/2000/svg';
function el(t,a){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;}

// palette for segments
const MOMCOL={'Pré':'var(--pre)','Pós':'var(--pos)','Rec':'var(--rec)'};
function segColor(dim,key){ if(dim==='mom')return MOMCOL[key]||'var(--accent)'; return 'var(--accent)'; }

function drawBars(svg,cats,vals,colors,opts){
 opts=opts||{}; svg.innerHTML='';
 const W=720,H=340,mL=48,mR=14,mT=16,mB=54;
 const plotW=W-mL-mR, plotH=H-mT-mB;
 const nums=vals.filter(v=>v!=null);
 let vmax=Math.max(...nums), vmin=Math.min(...nums);
 let lo = opts.zero? 0 : Math.max(0, Math.floor((vmin-(vmax-vmin)*0.35)/ (opts.step||5))*(opts.step||5));
 if(opts.zero) lo=0;
 let hi = Math.ceil((vmax+(vmax-vmin)*0.15+0.0001)/(opts.step||5))*(opts.step||5);
 if(hi<=lo) hi=lo+(opts.step||5);
 const y=v=>mT+plotH-(v-lo)/(hi-lo)*plotH;
 // gridlines
 const ticks=4;
 for(let i=0;i<=ticks;i++){const val=lo+(hi-lo)*i/ticks; const yy=y(val);
  svg.appendChild(el('line',{x1:mL,y1:yy,x2:W-mR,y2:yy,stroke:'var(--grid)','stroke-width':1}));
  const tx=el('text',{x:mL-8,y:yy+4,'text-anchor':'end','font-size':11,fill:'var(--muted)'});tx.textContent=fmt(val,val%1?1:0);svg.appendChild(tx);}
 // ref line T=50
 if(opts.ref!=null && opts.ref>lo && opts.ref<hi){const yy=y(opts.ref);
  svg.appendChild(el('line',{x1:mL,y1:yy,x2:W-mR,y2:yy,stroke:'var(--muted)','stroke-dasharray':'4 4','stroke-width':1,opacity:.7}));}
 const n=cats.length, gap=plotW/n, bw=Math.min(74, gap*0.62);
 cats.forEach((c,i)=>{
  const cx=mL+gap*i+gap/2; const v=vals[i];
  if(v!=null){const yy=y(v),h=mT+plotH-yy;
   svg.appendChild(el('rect',{x:cx-bw/2,y:yy,width:bw,height:Math.max(0,h),rx:5,fill:colors[i]}));
   const vt=el('text',{x:cx,y:yy-6,'text-anchor':'middle','font-size':12,'font-weight':700,fill:'var(--ink)'});vt.textContent=fmt(v,opts.dec==null?1:opts.dec);svg.appendChild(vt);}
  const xt=el('text',{x:cx,y:H-mB+20,'text-anchor':'middle','font-size':12,fill:'var(--muted)'});xt.textContent=c;svg.appendChild(xt);
  if(opts.sub&&opts.sub[i]!=null){const st=el('text',{x:cx,y:H-mB+36,'text-anchor':'middle','font-size':10.5,fill:'var(--muted)'});st.textContent=opts.sub[i];svg.appendChild(st);}
 });
 svg.appendChild(el('line',{x1:mL,y1:mT+plotH,x2:W-mR,y2:mT+plotH,stroke:'var(--line)','stroke-width':1.5}));
}

// ---------- BRUMS ----------
const bVars=DATA.brumsVars;
const bSegs=[['mom','Momento'],['dia','Dia'],['perfil','Perfil']];
let bState={v:'Vigor',seg:'mom'};
function bAgg(v,dim){
 const g={};
 DATA.brums.forEach(r=>{const k=''+r[dim];(g[k]=g[k]||[]).push(r[v]);});
 let keys=Object.keys(g);
 if(dim==='mom')keys=['Pré','Pós','Rec'].filter(k=>g[k]); else keys.sort((a,b)=>(+a||a)-(+b||b));
 return keys.map(k=>({key:k,mean:mean(g[k]),n:g[k].length}));
}
function bRender(){
 const rows=bAgg(bState.v,bState.seg);
 const cats=rows.map(r=>bState.seg==='dia'?('Dia '+r.key):r.key);
 const vals=rows.map(r=>r.mean), cols=rows.map(r=>segColor(bState.seg,r.key));
 const sub=rows.map(r=>'n='+r.n);
 drawBars($('bChart'),cats,vals,cols,{ref:50,sub,step:2,dec:1});
 $('bTtl').textContent=bState.v+' — média por '+({mom:'momento',dia:'dia',perfil:'perfil'})[bState.seg];
 const mn=Math.min(...vals),mx=Math.max(...vals);
 $('bSub').textContent='amplitude '+fmt(mn)+' → '+fmt(mx)+'  ·  n='+DATA.brums.length;
 $('bLeg').innerHTML = bState.seg==='mom'
  ? Object.entries(MOMCOL).map(([k,c])=>`<span><i style="background:${c}"></i>${k}</span>`).join('')
  : '<span>Linha tracejada: T=50 (média populacional)</span>';
 $('bNote').textContent='Cada barra é a média de '+bState.v.toLowerCase()+' das coletas no segmento. Piso do eixo ajustado para destacar diferenças.';
}
function mkBtns(host,items,active,on){
 host.innerHTML='';
 items.forEach(([val,label])=>{const b=document.createElement('button');b.className='chip';b.textContent=label;
  b.setAttribute('aria-pressed',val===active());b.onclick=()=>{on(val);};host.appendChild(b);});
}
function bBuild(){
 mkBtns($('bVar'),bVars.map(v=>[v,v]),()=>bState.v,v=>{bState.v=v;bBuild();bRender();});
 mkBtns($('bSeg'),bSegs,()=>bState.seg,s=>{bState.seg=s;bBuild();bRender();});
}

// ---------- HIIT ----------
const hVars=[['fc_pos','FC pós (bpm)'],['fc_pre','FC pré (bpm)'],['delta','Δ FC (bpm)'],['pse','PSE (0–10)']];
const hSegs=[['bloco','Série / bloco'],['sessao','Sessão']];
let hState={v:'pse',seg:'bloco'};
const BLOCOS=['Aquecimento','Série 1','Série 2','Série 3','Série 4','Recuperação'];
function hVal(r,v){ if(v==='delta')return (r.fc_pos!=null&&r.fc_pre!=null)?r.fc_pos-r.fc_pre:null; return r[v]; }
function hAgg(v,dim){
 const g={};
 DATA.hiit.forEach(r=>{const val=hVal(r,v); if(val==null)return; const k=''+r[dim];(g[k]=g[k]||[]).push(val);});
 let keys=Object.keys(g);
 if(dim==='bloco')keys=BLOCOS.filter(k=>g[k]); else keys.sort((a,b)=>(+a)-(+b));
 return keys.map(k=>({key:k,mean:mean(g[k]),n:g[k].length}));
}
function hRender(){
 const dim=hState.seg;
 let rows=hAgg(hState.v,dim);
 // for delta/pse, recuperação/aquecimento can be noisy; keep all but label
 const cats=rows.map(r=>dim==='sessao'?('Sessão '+r.key):r.key.replace('Série ','S'));
 const vals=rows.map(r=>r.mean);
 const isPse=hState.v==='pse';
 const cols=rows.map(()=> hState.v==='delta'?'var(--rec)':(isPse?'var(--accent)':'var(--pos)'));
 drawBars($('hChart'),cats,vals,cols,{zero:isPse||hState.v==='delta',step:isPse?2:20,dec:isPse?1:0,sub:rows.map(r=>'n='+r.n)});
 const lab=hVars.find(x=>x[0]===hState.v)[1];
 $('hTtl').textContent=lab+' — por '+(dim==='bloco'?'série/bloco':'sessão');
 $('hSub').textContent = dim==='bloco'?'média das 4 sessões':'média das 4 séries';
 $('hNote').textContent = dim==='bloco'
  ? 'Inclui aquecimento e recuperação como referência. Na progressão Série 1→4, PSE sobe e Δ FC diminui (recuperação incompleta).'
  : 'Cada barra resume uma sessão do protocolo (22–29/abr/2024).';
}
function hBuild(){
 mkBtns($('hVar'),hVars,()=>hState.v,v=>{hState.v=v;hBuild();hRender();});
 mkBtns($('hSeg'),hSegs,()=>hState.seg,s=>{hState.seg=s;hBuild();hRender();});
}
bBuild();bRender();hBuild();hRender();
</script>'''
html = html.replace('__DATA__', data)
pathlib.Path('analise/painel.html').write_text(html,encoding='utf-8')
print('ok', len(html), 'bytes')
