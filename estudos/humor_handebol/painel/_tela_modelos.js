/* ==================== modelos · CRISP-DM e árvores ==================== */
const ML=D.ml, ML2=D.ml2, ML3=D.ml3, CD=D.crispdm;
const CFASE=['#2166AC','#1A9070','#E0952B','#C1440E','#8A4FBF','#A31E52'];
const estadoMod={sec:'CRISP-DM'};
const LEG='font-family:var(--dado);font-size:10.5px;color:var(--ink-3);line-height:1.5';
const NOTA='font-size:12.5px;color:var(--ink-2);line-height:1.5';

/* ---- barra horizontal de AUC com intervalo de confiança ---- */
function grafAUC(itens,{larg=560,ref=null,rotRef=''}={}){
  const M={t:16,r:60,b:26,l:186}, hl=30, H=M.t+M.b+itens.length*hl, W=larg;
  const lo=0.40, hi=1.0, px=v=>M.l+(v-lo)/(hi-lo)*(W-M.l-M.r);
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g'});
  [0.5,0.6,0.7,0.8,0.9,1.0].forEach(v=>{
    g.append(s('line',{x1:px(v),x2:px(v),y1:M.t-6,y2:H-M.b,stroke:'#E4E9E7','stroke-width':1}));
    stx(g,{x:px(v),y:H-M.b+15,'text-anchor':'middle',class:'eixo'},nb(v,1));
  });
  if(ref!=null){
    g.append(s('line',{x1:px(ref),x2:px(ref),y1:M.t-8,y2:H-M.b,stroke:'#B3341A','stroke-width':1.6,'stroke-dasharray':'4 3'}));
    stx(g,{x:px(ref),y:M.t-12,'text-anchor':'middle',class:'eixo',fill:'#B3341A'},rotRef);
  }
  itens.forEach((it,i)=>{
    const y=M.t+i*hl+hl/2, c=it.cor||'#2166AC';
    stx(g,{x:M.l-10,y:y+4,'text-anchor':'end',style:`font-family:var(--disp);font-size:12px;fill:${it.base?'#87968F':'#25332F'};font-weight:${it.base?400:600}`},it.nome);
    if(it.ic) g.append(s('line',{x1:px(it.ic[0]),x2:px(it.ic[1]),y1:y,y2:y,stroke:c,'stroke-width':2,opacity:.42,'stroke-linecap':'round'}));
    const r=s('circle',{cx:px(it.valor),cy:y,r:6,fill:c,stroke:'#FBFCFB','stroke-width':2});
    comDica(r,`<b>${it.nome}</b><br>AUC ${nb(it.valor,3)}${it.ic?`<br>IC 95% [${nb(it.ic[0],3)}, ${nb(it.ic[1],3)}]`:''}`);
    g.append(r);
    stx(g,{x:W-M.r+8,y:y+4,style:'font-family:var(--dado);font-size:11.5px;font-variant-numeric:tabular-nums',fill:c},nb(it.valor,3));
  });
  return g;
}

/* ---- a árvore desenhada ---- */
function grafArvore(){
  const W=880, H=330, g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g',style:'max-width:880px'});
  const nos=ML2.ARVORE;
  const porProf={}; nos.forEach(n=>{(porProf[n.prof]=porProf[n.prof]||[]).push(n);});
  const maxP=Math.max(...nos.map(n=>n.prof));
  const pos=new Map();
  Object.keys(porProf).forEach(p=>{
    const fila=porProf[p], y=28+ (+p)*((H-70)/maxP);
    fila.forEach((n,i)=>pos.set(n,{x:(W/(fila.length+1))*(i+1), y}));
  });
  /* ligações: um nó filho compartilha o caminho do pai mais o próprio corte */
  nos.forEach(n=>{
    if(!n.caminho.length) return;
    const pai=nos.find(m=>m.caminho.length===n.caminho.length-1 &&
      m.caminho.every((c,i)=>c===n.caminho[i]));
    if(!pai) return;
    const a=pos.get(pai), b=pos.get(n);
    g.append(s('path',{d:`M${a.x},${a.y+16} C${a.x},${(a.y+b.y)/2} ${b.x},${(a.y+b.y)/2} ${b.x},${b.y-18}`,
      fill:'none',stroke:'#CDD6D2','stroke-width':1.6}));
    const corte=n.caminho[n.caminho.length-1];
    const lado=corte.includes('≤')?'sim':'não';
    stx(g,{x:(a.x+b.x)/2+(b.x<a.x?-14:14),y:(a.y+b.y)/2+3,'text-anchor':'middle',class:'eixo'},lado);
  });
  nos.forEach(n=>{
    const p=pos.get(n), risco=n.p, c=risco>=.66?'#B3341A':risco<=.20?'#1A7F5A':'#E0952B';
    if(n.tipo==='no'){
      const w=Math.max(126,n.var.length*6.4+16);
      g.append(s('rect',{x:p.x-w/2,y:p.y-18,width:w,height:36,rx:8,fill:'#FFFFFF',stroke:'#CDD6D2','stroke-width':1.4}));
      stx(g,{x:p.x,y:p.y-2,'text-anchor':'middle',style:'font-size:11.5px;font-weight:600;fill:#25332F'},n.var);
      stx(g,{x:p.x,y:p.y+11,'text-anchor':'middle',class:'eixo'},'corte em '+nb(n.limiar,1));
    }else{
      const w=104;
      const r=s('rect',{x:p.x-w/2,y:p.y-19,width:w,height:38,rx:8,fill:c,opacity:.13,stroke:c,'stroke-width':1.6});
      comDica(r,`<b>Folha</b><br>${n.n} pares atleta-dia<br>risco previsto ${(risco*100).toFixed(0)}%<br><i>${n.caminho.join(' e ')}</i>`);
      g.append(r);
      stx(g,{x:p.x,y:p.y-1,'text-anchor':'middle',style:`font-family:var(--dado);font-size:15px;font-weight:600;fill:${c}`},(risco*100).toFixed(0)+'%');
      stx(g,{x:p.x,y:p.y+13,'text-anchor':'middle',class:'eixo'},'n = '+n.n);
    }
  });
  return g;
}

/* ---- organograma das seis fases ---- */
function fluxoCrisp(){
  const box=el('div',{class:'fluxo',style:'gap:0;align-items:stretch;flex-wrap:wrap'});
  CD.FASES.forEach((f,i)=>{
    const c=CFASE[i];
    const b=el('button',{style:`flex:1 1 150px;text-align:left;border:0;cursor:pointer;padding:12px 14px;
      background:${estadoMod.fase===f.id?c:'var(--card)'};color:${estadoMod.fase===f.id?'#fff':'var(--ink)'};
      border-top:3px solid ${c};border-right:1px solid var(--rule);transition:background .16s,color .16s`,
      onclick:()=>{estadoMod.fase=(estadoMod.fase===f.id?null:f.id); render('modelos');}});
    b.append(el('div',{style:`font-family:var(--dado);font-size:9.5px;letter-spacing:.13em;
      color:${estadoMod.fase===f.id?'rgba(255,255,255,.75)':c}`,txt:'FASE '+f.n}),
      el('div',{style:'font-size:12.5px;font-weight:600;margin-top:3px;line-height:1.3',txt:f.nome}));
    box.append(b);
  });
  return el('div',{style:'border:1px solid var(--rule);border-radius:var(--r);overflow:hidden;box-shadow:var(--sombra)'},box);
}

const SECMOD={};

SECMOD['CRISP-DM']=()=>{
  const f=document.createDocumentFragment();
  const c0=el('div',{class:'cartao',style:'margin-bottom:14px;background:linear-gradient(120deg,#FBFCFB 0%,#F0F6F3 100%)'});
  c0.append(el('div',{style:'font-family:var(--dado);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--sinal)',txt:'Trilha metodológica'}),
    el('h2',{style:'margin:6px 0 4px;font-size:20px;font-weight:600;letter-spacing:-.3px;max-width:58ch',
      txt:'O estudo inteiro sobre as seis fases do CRISP-DM'}),
    el('div',{class:'prosa',style:'margin-top:8px'},
      el('p',{html:'Cada fase declara o que foi feito, o que a inteligência artificial fez como copiloto e o que ficou sob decisão humana. '+
        'A separação é o ponto: <strong>o que o modelo decide sozinho não é achado</strong>. Clique em uma fase para abrir o detalhe.'})));
  f.append(c0, fluxoCrisp());
  const alvo=CD.FASES.find(x=>x.id===estadoMod.fase);
  if(alvo){
    const i=CD.FASES.indexOf(alvo), c=CFASE[i];
    const g=el('div',{class:'grade',style:'grid-template-columns:1.4fr 1fr;margin-top:14px'});
    const c1=el('div',{class:'cartao',style:`border-left:3px solid ${c}`});
    c1.append(el('h3',{txt:alvo.pergunta}), el('p',{class:'leg',txt:'O que foi feito de fato'}));
    const ul=el('ul',{style:'margin:0;padding-left:18px;font-size:13.5px;line-height:1.75;color:var(--ink-2)'});
    alvo.feito.forEach(t=>ul.append(el('li',{txt:t})));
    c1.append(ul);
    const art=el('div',{style:'margin-top:12px;display:flex;flex-wrap:wrap;gap:6px'});
    alvo.artefatos.forEach(a=>art.append(el('span',{class:'tag',txt:a})));
    c1.append(el('div',{style:LEG+';margin:12px 0 0',txt:'Artefatos no repositório'}),art);
    const c2=el('div',{class:'cartao'});
    c2.append(el('h3',{txt:'Divisão de trabalho'}),
      el('div',{style:'margin-top:8px'},
        el('div',{style:`font-family:var(--dado);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:${c}`,txt:'IA como copiloto'}),
        el('div',{style:'font-size:13px;line-height:1.6;color:var(--ink-2);margin:4px 0 14px',txt:alvo.copiloto}),
        el('div',{style:'font-family:var(--dado);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3)',txt:'Decisão humana'}),
        el('div',{style:'font-size:13px;line-height:1.6;color:var(--ink);margin-top:4px',txt:alvo.humano})));
    g.append(c1,c2); f.append(g);
  }
  const cr=el('div',{class:'cartao',style:'margin-top:14px'});
  cr.append(el('h3',{txt:'As seis regras que atravessam todas as fases'}),
    el('p',{class:'leg',txt:'Cada uma nasceu de um erro real cometido e corrigido neste estudo.'}));
  const gr=el('div',{class:'grade',style:'grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px'});
  CD.REGRAS.forEach((r,i)=>gr.append(el('div',{style:`border-left:2.5px solid ${CFASE[i]};padding-left:11px`},
    el('div',{style:'font-size:12.5px;font-weight:600;margin-bottom:3px',txt:r.t}),
    el('div',{style:'font-size:12px;line-height:1.55;color:var(--ink-2)',txt:r.d}))));
  cr.append(gr); f.append(cr);
  return f;
};

SECMOD['Árvore de decisão']=()=>{
  const f=document.createDocumentFragment();
  const g=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-bottom:14px'});
  const c=el('div',{class:'cartao'});
  c.append(el('h3',{txt:'A árvore lida: da medida da manhã ao estado da noite'}),
    el('p',{class:'leg',txt:'Profundidade 3, folha mínima de 12 pares. Verde é folha protegida, vermelho é folha de risco. '+
      'Passe o cursor sobre uma folha para ver o caminho completo.'}));
  c.append(grafArvore());
  g.append(c); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1fr 1fr'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'O que cada preditor acrescenta'}),
    el('p',{class:'leg',txt:'Queda de AUC quando a variável é embaralhada fora da amostra. Média de seis repetições.'}));
  c1.append(grafBarras(ML2.IMPORTANCIA.slice(0,8).map((e,i)=>({
    nome:e.var.replace(' (manhã)','').replace('Já estava em risco de manhã','Risco já pela manhã'), valor:e.media, rotulo:nb(e.media,3),
    dica:`<b>${e.var}</b><br>queda de AUC ${nb(e.media,3)} ± ${nb(e.dp,3)}`,
    cor:i<2?'#B3341A':'#2166AC'})), {larg:540}));
  c1.append(el('div',{style:LEG+';margin:6px 0 0',
    txt:'Todas as variáveis medidas pela manhã. As duas primeiras respondem por quase toda a informação útil.'}));
  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'As duas folhas que decidem'}));
  ML3.FOLHAS.forEach((fo,i)=>{
    const cor=fo.risco_noite>.5?'#B3341A':'#1A7F5A';
    const b=el('div',{style:`border-left:2.5px solid ${cor};padding-left:12px;margin-top:${i?14:8}px`});
    b.append(el('div',{style:'font-size:12.5px;font-weight:600;line-height:1.35',txt:fo.folha}),
      el('div',{style:`font-family:var(--dado);font-size:22px;font-weight:600;color:${cor};margin:5px 0 2px`,
        txt:(fo.risco_noite*100).toFixed(0)+'%'}),
      el('div',{style:LEG+';margin:0 0 6px',txt:`em risco à noite · n = ${fo.n} pares`}),
      el('div',{style:'font-size:12px;line-height:1.55;color:var(--ink-2)',
        txt:`manhã: vigor ${nb(fo.manha['Vigor'])} · fadiga ${nb(fo.manha['Fadiga'])} · tensão ${nb(fo.manha['Tensão'])} · PTH ${nb(fo.manha['TMD'])}`}),
      el('div',{style:'font-size:12px;line-height:1.55;color:var(--ink-2)',
        txt:`noite: vigor ${nb(fo.noite['Vigor'])} · fadiga ${nb(fo.noite['Fadiga'])} · tensão ${nb(fo.noite['Tensão'])} · PTH ${nb(fo.noite['TMD'])}`}));
    c2.append(b);
  });
  g2.append(c1,c2); f.append(g2);
  return f;
};

SECMOD['Desempenho']=()=>{
  const f=document.createDocumentFragment();
  const kp=el('div',{class:'grade',style:'grid-template-columns:repeat(auto-fit,minmax(178px,1fr));margin-bottom:14px'});
  [['Pares atleta-dia',String(ML.n),`${ML.atletas} atletas · ${ML.eventos} eventos`,'#2166AC'],
   ['Regra trivial',(ML.regra_trivial*100).toFixed(1).replace('.',',')+'<small> %</small>','já estava em risco de manhã','#87968F'],
   ['Melhor AUC',nb(ML.RES['XGBoost'].auc,3),'XGBoost · validação agrupada','#1A9070'],
   ['Ganho sobre a trivial',nb(ML.GANHO['XGBoost'].m,3),'IC 95% inclui zero','#E0952B'],
   ['Subgrupo acionável',nb(ML2.SUBGRUPO['Random Forest'].auc,3),'IC 95% exclui o acaso','#1A7F5A']]
   .forEach(([r,v,n,c])=>kp.append(el('div',{class:'kpi',style:`--k:${c}`},
     el('div',{class:'rot',txt:r}), el('div',{class:'val',html:v}), el('div',{class:'nota',txt:n}))));
  f.append(kp);

  const g=el('div',{class:'grade',style:'grid-template-columns:1fr'});
  const c=el('div',{class:'cartao'});
  c.append(el('h3',{txt:'Área sob a curva, com validação cruzada agrupada por atleta'}),
    el('p',{class:'leg',txt:'Ponto é a média de oito repetições; a barra é o intervalo de confiança de 95% por reamostragem agrupada. '+
      'A linha tracejada marca a regra trivial que qualquer preparador aplicaria de cabeça.'}));
  const ordem=['XGBoost','Árvore de decisão','Random Forest','Regressão logística','Regra: já estava em risco','Classe majoritária'];
  c.append(grafAUC(ordem.filter(k=>ML.RES[k]).map((k,i)=>({
      nome:k, valor:ML.RES[k].auc, ic:ML.RES[k].ic, base:k.startsWith('Regra')||k.startsWith('Classe'),
      cor:k.startsWith('Regra')?'#87968F':k.startsWith('Classe')?'#CDD6D2':CAT[i]})),
    {larg:640, ref:ML.RES['Regra: já estava em risco'].auc, rotRef:'regra trivial'}));
  g.append(c); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-top:14px'});
  const ct=el('div',{class:'cartao'});
  ct.append(el('h3',{txt:'Tabela completa de desempenho'}),
    el('p',{class:'leg',txt:'Acurácia balanceada, sensibilidade e especificidade no ponto de corte de 0,5. O escore de Brier mede calibração — menor é melhor.'}));
  const tw=el('div',{class:'tabwrap',style:'max-height:none'}), t=el('table');
  t.append(el('thead',{},el('tr',{},...['Modelo','AUC','IC 95%','Ac. balanc.','Sensib.','Especif.','Brier','Ganho sobre a trivial']
    .map(h=>el('th',{txt:h})))));
  const tb=el('tbody');
  ordem.filter(k=>ML.RES[k]).forEach(k=>{
    const r=ML.RES[k], gh=ML.GANHO[k];
    const base=k.startsWith('Regra')||k.startsWith('Classe');
    tb.append(el('tr',{style:base?'color:var(--ink-3)':''},
      el('td',{style:base?'':'font-weight:600',txt:k}),
      el('td',{class:'num',txt:nb(r.auc,3)}),
      el('td',{class:'num',txt:`[${nb(r.ic[0],3)}, ${nb(r.ic[1],3)}]`}),
      el('td',{class:'num',txt:nb(r.bacc,3)}), el('td',{class:'num',txt:nb(r.sens,3)}),
      el('td',{class:'num',txt:nb(r.espec,3)}), el('td',{class:'num',txt:nb(r.brier,3)}),
      el('td',{class:'num'},gh?el('span',{},nb(gh.m,3)+'  ',
        el('span',{class:'pill '+(gh.ic[0]>0?'bom':'neu'),txt:gh.ic[0]>0?'exclui zero':'inclui zero'})):'—')));
  });
  t.append(tb); tw.append(t); ct.append(tw);
  ct.append(el('div',{class:'prosa',style:'margin-top:12px;max-width:78ch'},
    el('p',{html:'Os três modelos de árvore superam a regra trivial em área sob a curva, mas <strong>o intervalo de confiança do ganho '+
      'não exclui zero</strong> em nenhum deles. Com 27 atletas e 119 pares, é o que a amostra permite afirmar. '+
      'O achado defensável está no subgrupo acionável, na aba de diagnóstico.'})));
  g2.append(ct); f.append(g2);
  return f;
};

SECMOD['Diagnóstico']=()=>{
  const f=document.createDocumentFragment();
  const c0=el('div',{class:'cartao',style:'margin-bottom:14px;background:linear-gradient(120deg,#FBFCFB,#FAF2EE)'});
  c0.append(el('h3',{style:'font-size:16px',txt:'A folha mais forte era contraintuitiva, e por isso foi diagnosticada antes de virar frase'}),
    el('div',{class:'prosa',style:'margin-top:8px;max-width:80ch'},
      el('p',{html:'A árvore corta primeiro pelo PTH e diz que <strong>quem amanhece muito favorável termina o dia em risco com maior frequência</strong>. '+
        'Isso pode ser reversão à média: quem começa no piso só tem para onde subir. O teste é direto — correlacionar o valor da manhã com a própria variação.'}),
      el('p',{html:ML3.VEREDICTO.texto})));
  f.append(c0);

  const g=el('div',{class:'grade',style:'grid-template-columns:1fr 1fr'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'Reversão à média por dimensão'}),
    el('p',{class:'leg',txt:'ρ de Spearman entre o valor da manhã e a variação manhã→noite. Todas as correlações são negativas; '+
      'a barra mostra a magnitude. Quanto mais longa, mais mecânico o movimento.'}));
  c1.append(grafBarras(ML3.REVERSAO.slice().sort((a,b)=>a.rho-b.rho).map(e=>({
    nome:e.variavel, valor:-e.rho, rotulo:nb(e.rho,3), cor:e.mecanico?'#B3341A':'#1A7F5A',
    dica:`<b>${e.variavel}</b><br>ρ = ${nb(e.rho,3)}<br>${pb(e.p)} · n = ${e.n}`})),
    {larg:540, dominio:0.72}));
  c1.append(el('div',{class:'legenda'},
    el('span',{},el('i',{style:'background:#B3341A'}),'componente mecânico (p < 0,05)'),
    el('span',{},el('i',{style:'background:#1A7F5A'}),'sem componente mecânico')));
  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Modelos aninhados: o que a tensão acrescenta'}),
    el('p',{class:'leg',txt:'AUC agrupada por atleta, acrescentando um preditor por vez. Ponto é a média de oito repetições; '+
      'o desvio entre repetições não passa de 0,024, de modo que a ordem é estável.'}));
  c2.append(grafAUC(ML3.ANINHADOS.map((e,i)=>({nome:e.modelo, valor:e.auc, cor:CAT[i]})),{larg:520}));
  c2.append(el('div',{class:'prosa',style:'margin-top:10px;font-size:13px'},
    el('p',{html:`A tensão matinal sozinha eleva a AUC em <strong>${nb(ML3.VEREDICTO.ganho_tensao,3)}</strong> sobre o PTH. `+
      'Acrescentar as outras quinze variáveis não melhora: com 119 observações, o modelo grande apenas memoriza.'})));
  g.append(c1,c2); f.append(g);

  const g3=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-top:14px'});
  const c3=el('div',{class:'cartao'});
  c3.append(el('h3',{txt:'O subgrupo acionável: quem começa o dia fora da faixa de risco'}),
    el('p',{class:'leg',txt:'Excluídos os pares que já amanhecem em risco — sobre os quais nenhuma previsão acrescenta decisão. '+
      'É aqui que o intervalo de confiança exclui o acaso.'}));
  const sg=ML2.SUBGRUPO, k0=Object.keys(sg)[0];
  c3.append(el('div',{style:NOTA+';margin-bottom:10px',
    txt:`${sg[k0].n} pares começam fora da faixa de risco; ${sg[k0].eventos} entram na faixa até a noite (${(sg[k0].eventos/sg[k0].n*100).toFixed(1).replace('.',',')}%).`}));
  c3.append(grafAUC(Object.entries(sg).map(([k,v],i)=>({nome:k, valor:v.auc, ic:v.ic, cor:CAT[i]})),
    {larg:620, ref:0.5, rotRef:'acaso'}));
  c3.append(el('div',{class:'prosa',style:'margin-top:12px;max-width:78ch'},
    el('p',{html:'A leitura prática é esta: a medida da manhã não acrescenta nada sobre quem já amanhece mal — a comissão técnica já sabe. '+
      'Ela acrescenta sobre <strong>quem amanhece bem e ainda assim vai terminar o dia em risco</strong>, e o marcador que separa esses dois grupos '+
      'não é a fadiga nem o vigor: é a ausência completa de tensão matinal, que converge com o achado dos dois artigos de que a tensão, '+
      'neste elenco, se comporta como ativação e não como sofrimento.'})));
  g3.append(c3); f.append(g3);
  return f;
};

TELAS.modelos=()=>{
  segTopo.hidden=false; segTopo.innerHTML='';
  const f=document.createDocumentFragment();
  const sec=SECMOD[estadoMod.sec]?estadoMod.sec:'CRISP-DM';
  Object.keys(SECMOD).forEach(nome=>segTopo.append(el('button',{txt:nome,'aria-pressed':String(nome===sec),
    onclick:()=>{estadoMod.sec=nome; render('modelos');}})));
  f.append(SECMOD[sec]());
  return f;
};
