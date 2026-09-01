/* ==================== qualidade e otimização ==================== */
const QA=D.qual, CO=D.conf, OT=D.otim;
const UNIQ=Object.fromEntries(QA.UNI.map(u=>[u.variavel,u]));
const estadoQ={sec:'Qualidade', freq:Object.keys(QA.FREQ)[0], caixa:'Tensão'};
const LEGQ='font-family:var(--dado);font-size:10.5px;color:var(--ink-3);line-height:1.5';
const GRAV={'nenhuma':'#1A7F5A','baixa':'#87968F','média':'#E0952B','alta':'#B3341A',
            'crítica':'#8B1A1A','método':'#8A4FBF'};

/* ---- caixa e bigodes de uma variável, a partir dos quantis já calculados ---- */
function grafCaixa(u,{larg=520,alt=132,cor='#2166AC'}={}){
  const M={t:16,r:24,b:34,l:24}, W=larg, H=alt;
  const lo=Math.min(u.minimo,u.tukey_moderado[0]), hi=Math.max(u.maximo,u.tukey_moderado[1]);
  const px=v=>M.l+(v-lo)/(hi-lo||1)*(W-M.l-M.r), y=M.t+26, h=34;
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g'});
  const cerca=s('rect',{x:px(u.tukey_moderado[0]),y:y-8,width:Math.max(px(u.tukey_moderado[1])-px(u.tukey_moderado[0]),1),
    height:h+16,fill:'#B3341A',opacity:.05});
  g.append(cerca);
  g.append(s('line',{x1:px(u.minimo),x2:px(u.maximo),y1:y+h/2,y2:y+h/2,stroke:'#87968F','stroke-width':1.4}));
  [u.minimo,u.maximo].forEach(v=>g.append(s('line',{x1:px(v),x2:px(v),y1:y+6,y2:y+h-6,stroke:'#87968F','stroke-width':1.4})));
  const cx0=px(u.q1), cw=Math.max(px(u.q3)-px(u.q1),2);
  const bx=s('rect',{x:cx0,y,width:cw,height:h,rx:4,fill:cor,opacity:.82});
  comDica(bx,`<b>${rot(u.variavel)}</b><br>Q1 ${nb(u.q1)} · Md ${nb(u.mediana)} · Q3 ${nb(u.q3)}<br>`+
    `IQR ${nb(u.iqr)}${u.iqr_nulo?' — nulo':''}<br>cerca de Tukey [${nb(u.tukey_moderado[0])}, ${nb(u.tukey_moderado[1])}]`);
  g.append(bx);
  g.append(s('line',{x1:px(u.mediana),x2:px(u.mediana),y1:y,y2:y+h,stroke:'#FBFCFB','stroke-width':2.4}));
  g.append(s('circle',{cx:px(u.media),cy:y+h/2,r:4,fill:'#FBFCFB',stroke:cor,'stroke-width':2}));
  // âncoras que caem no mesmo ponto (piso da escala) são fundidas, para não colidirem
  const anc=[];
  [['mín',u.minimo],['Q1',u.q1],['Md',u.mediana],['Q3',u.q3],['máx',u.maximo]].forEach(([r,v])=>{
    const perto=anc.find(a=>Math.abs(px(a.v)-px(v))<16);
    if(perto) perto.rot.push(r); else anc.push({v, rot:[r]});
  });
  anc.forEach(a=>{
    stx(g,{x:px(a.v),y:H-12,'text-anchor':'middle',class:'eixo'},nb(a.v,1));
    stx(g,{x:px(a.v),y:M.t-2,'text-anchor':'middle',class:'eixo'},a.rot.join(' = '));
  });
  return g;
}

/* ---- fronteira eficiente: carga da semana contra o pior dia de vigor ---- */
function grafFronteira({larg=540,alt=250}={}){
  const FR=OT.FRONTEIRA.filter(x=>x.viavel!==false);
  const INV=OT.FRONTEIRA.filter(x=>x.viavel===false);
  const M={t:16,r:22,b:38,l:52}, W=larg, H=alt;
  const xs=OT.FRONTEIRA.map(f=>f.carga).concat([OT.OBSERVADO.total]);
  const ys=FR.map(f=>f.vigor_minimo).concat([OT.OBSERVADO.vigor_minimo]);
  const x0=Math.min(...xs)-1, x1=Math.max(...xs)+1;
  const pad=(Math.max(...ys)-Math.min(...ys))*0.22 || 0.02;
  const y0=Math.min(...ys)-pad, y1=Math.max(...ys)+pad;
  const px=v=>M.l+(v-x0)/(x1-x0)*(W-M.l-M.r), py=v=>H-M.b-(v-y0)/(y1-y0)*(H-M.t-M.b);
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g'});
  if(INV.length){
    const lim=OT.CARGA_MINIMA_ESTRUTURAL;
    g.append(s('rect',{x:M.l,y:M.t,width:Math.max(px(lim)-M.l,0),height:H-M.t-M.b,fill:'#B3341A',opacity:.05}));
    g.append(s('line',{x1:px(lim),x2:px(lim),y1:M.t,y2:H-M.b,stroke:'#B3341A','stroke-width':1.5,'stroke-dasharray':'4 3'}));
    stx(g,{x:px(lim)-6,y:M.t+13,'text-anchor':'end',class:'eixo',fill:'#B3341A'},'inviável');
    stx(g,{x:px(lim)-6,y:M.t+25,'text-anchor':'end',class:'eixo',fill:'#B3341A'},`abaixo de ${nb(lim)} h`);
  }
  for(let i=0;i<=4;i++){
    const v=y0+(y1-y0)*i/4;
    g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(v),y2:py(v),stroke:'#E4E9E7','stroke-width':1}));
    stx(g,{x:M.l-8,y:py(v)+4,'text-anchor':'end',class:'eixo'},nb(v,3));
  }
  FR.forEach(f=>stx(g,{x:px(f.carga),y:H-M.b+16,'text-anchor':'middle',class:'eixo'},nb(f.carga,0)));
  stx(g,{x:(M.l+W-M.r)/2,y:H-6,'text-anchor':'middle',class:'eixo'},'carga da semana (horas)');
  g.append(s('path',{d:FR.map((f,i)=>`${i?'L':'M'}${px(f.carga)},${py(f.vigor_minimo)}`).join(''),
    fill:'none',stroke:'#0F6E5C','stroke-width':2.4,'stroke-linejoin':'round'}));
  FR.forEach(f=>{
    const c=s('circle',{cx:px(f.carga),cy:py(f.vigor_minimo),r:5.5,fill:'#0F6E5C',stroke:'#FBFCFB','stroke-width':2});
    comDica(c,`<b>${nb(f.carga,0)} h de carga semanal</b><br>pior dia de vigor ${nb(f.vigor_minimo,3)}`+
      `<br>fadiga máxima ${nb(f.fadiga_maxima)}<br>distribuição ${f.horas.map(v=>nb(v,1)).join(' · ')}`);
    g.append(c);
  });
  const ob=s('path',{d:`M${px(OT.OBSERVADO.total)},${py(OT.OBSERVADO.vigor_minimo)-6.5}`+
    `L${px(OT.OBSERVADO.total)+6.5},${py(OT.OBSERVADO.vigor_minimo)}`+
    `L${px(OT.OBSERVADO.total)},${py(OT.OBSERVADO.vigor_minimo)+6.5}`+
    `L${px(OT.OBSERVADO.total)-6.5},${py(OT.OBSERVADO.vigor_minimo)}Z`,
    fill:'#87968F',stroke:'#FBFCFB','stroke-width':2});
  comDica(ob,`<b>calendário observado</b><br>${nb(OT.OBSERVADO.total,1)} h · pior dia de vigor `+
    `${nb(OT.OBSERVADO.vigor_minimo,3)}`);
  g.append(ob);
  stx(g,{x:px(OT.OBSERVADO.total)+11,y:py(OT.OBSERVADO.vigor_minimo)+4,class:'eixo'},'observado');
  stx(g,{x:M.l-8,y:M.t-4,'text-anchor':'end',class:'eixo'},'vigor');
  return g;
}

const SECQ={};

SECQ['Qualidade']=()=>{
  const f=document.createDocumentFragment();
  const kp=el('div',{class:'grade',style:'grid-template-columns:repeat(auto-fit,minmax(172px,1fr));margin-bottom:14px'});
  const totConf=QA.CONFRONTO.reduce((a,c)=>a+c.n_comparado,0);
  const divConf=QA.CONFRONTO.reduce((a,c)=>a+c.n_divergente,0);
  const faltItens=QA.FALTA_ITEM.reduce((a,c)=>a+c.faltantes,0);
  const foraDom=QA.UNI.reduce((a,u)=>a+(u.fora_do_dominio||0),0);
  [['Escores conferidos',String(totConf),`${divConf} divergência${divConf===1?'':'s'} contra a fórmula`,'#1A7F5A'],
   ['Itens do instrumento','100,0<small> %</small>',`completude · ${faltItens} célula ausente`,'#1A7F5A'],
   ['Fora do domínio',String(foraDom),'nenhum escore impossível','#1A7F5A'],
   ['Grafias do nome',String(QA.CATEG[0].grafias),`para ${QA.CATEG[0].niveis_canonicos} nomes canônicos`,'#B3341A'],
   ['Reconferência',`${CO.ok}/${CO.total}`,'os três documentos batem','#1A7F5A']]
   .forEach(([r,v,n,c])=>kp.append(el('div',{class:'kpi',style:`--k:${c}`},
     el('div',{class:'rot',txt:r}),el('div',{class:'val',html:v}),el('div',{class:'nota',txt:n}))));
  f.append(kp);

  const g=el('div',{class:'grade',style:'grid-template-columns:1.15fr 1fr'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'Escore reconstruído por fórmula contra a coluna da planilha'}),
    el('p',{class:'leg',txt:'Cada subescala é a soma de quatro itens; o PTH é a soma das cinco negativas menos o vigor; '+
      'a PSS soma catorze itens com sete invertidos. Tudo foi recalculado desde o item.'}));
  const tw=el('div',{class:'tabwrap',style:'max-height:none'}), t=el('table');
  t.append(el('thead',{},el('tr',{},...['Variável','Comparações','Divergências','Maior diferença'].map(h=>el('th',{txt:h})))));
  const tb=el('tbody');
  QA.CONFRONTO.forEach(c=>tb.append(el('tr',{},
    el('td',{style:'font-weight:600',txt:rot(c.variavel)}), el('td',{class:'num',txt:c.n_comparado}),
    el('td',{class:'num'},el('span',{class:'pill '+(c.n_divergente?'cr':'bom'),txt:String(c.n_divergente)})),
    el('td',{class:'num',txt:nb(c.max_dif,0)}))));
  t.append(tb); tw.append(t); c1.append(tw);
  c1.append(el('div',{class:'prosa',style:'margin-top:11px;font-size:13.5px;max-width:none'},
    el('p',{html:`<strong>${divConf} divergência em ${totConf} conferências.</strong> A pontuação da planilha está `+
      'correta. As sete versões do manuscrito divergiam pela unidade de análise — agora se sabe que não '+
      'divergiam também por erro de escore.'})));

  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Achados da auditoria de qualidade'}));
  QA.INCONS.forEach((i,k)=>{
    const cor=GRAV[i.gravidade]||'#87968F';
    c2.append(el('div',{style:`border-left:2.5px solid ${cor};padding-left:11px;margin-top:${k?12:8}px`},
      el('div',{style:'display:flex;align-items:center;gap:8px'},
        el('span',{style:`font-family:var(--dado);font-size:10px;letter-spacing:.1em;color:${cor}`,txt:i.id}),
        el('span',{class:'tag',style:`background:${cor}1F;color:${cor}`,txt:i.gravidade}),
        el('span',{style:'font-family:var(--dado);font-size:10px;color:var(--ink-3)',txt:`${i.n} de ${i.de}`})),
      el('div',{style:'font-size:12.5px;font-weight:600;margin:3px 0 2px',txt:i.titulo}),
      el('div',{style:'font-size:12px;line-height:1.55;color:var(--ink-2)',txt:i.achado}),
      el('div',{style:'font-size:12px;line-height:1.55;color:var(--sinal);margin-top:3px',txt:'→ '+i.correcao})));
  });
  g.append(c1,c2); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1fr 1fr;margin-top:14px'});
  const c3=el('div',{class:'cartao'});
  c3.append(el('h3',{txt:'Cobertura da grade atleta × dia'}),
    el('p',{class:'leg',txt:'Nenhum item ficou em branco. A falta não é de item: é de comparecimento. '+
      'Cobertura de registros acima de 100% indica envio além do previsto.'}));
  const tw3=el('div',{class:'tabwrap',style:'max-height:none'}), t3=el('table');
  t3.append(el('thead',{},el('tr',{},...['Dia','Atletas','Cobertura','Registros','Previstos','Cobertura'].map(h=>el('th',{txt:h})))));
  const tb3=el('tbody');
  QA.GRADE.forEach(r=>{
    const ca=r.cobertura_atleta, cr=r.cobertura_registro;
    tb3.append(el('tr',{},
      el('td',{style:`font-weight:600;color:${CEST[dia(r.dia).tipo_estimulo]}`,txt:'D'+r.dia}),
      el('td',{class:'num',txt:`${r.atletas_com_registro}/${r.atletas_esperados}`}),
      el('td',{class:'num',style:`color:${ca<85?'#B3341A':'var(--ink)'}`,txt:nb(ca,1)+'%'}),
      el('td',{class:'num',txt:r.registros}), el('td',{class:'num',txt:r.registros_esperados}),
      el('td',{class:'num',style:`color:${cr>110?'#E0952B':'var(--ink)'}`,txt:nb(cr,1)+'%'})));
  });
  t3.append(tb3); tw3.append(t3); c3.append(tw3);

  const c4=el('div',{class:'cartao'});
  const R=QA.REPETICAO;
  c4.append(el('h3',{txt:'Registros no mesmo par atleta-dia'}),
    el('p',{class:'leg',txt:'O protocolo previa até dois por dia. A distribuição vai a seis.'}));
  const tot=Object.values(R.distribuicao).reduce((a,b)=>a+b,0);
  const barras=el('div',{style:'display:flex;align-items:flex-end;gap:10px;height:150px;margin:12px 0 6px'});
  Object.entries(R.distribuicao).forEach(([k,v])=>{
    const alt=Math.max(6, v/Math.max(...Object.values(R.distribuicao))*116);
    const col=el('div',{style:'flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;justify-content:flex-end'});
    col.append(el('div',{style:'font-family:var(--dado);font-size:11px;color:var(--ink-2)',txt:v}),
      el('div',{style:`width:100%;height:${alt}px;border-radius:5px 5px 0 0;background:${+k<=2?'#1A9070':'#E0952B'}`}),
      el('div',{style:'font-family:var(--dado);font-size:10.5px;color:var(--ink-3)',txt:k}));
    barras.append(col);
  });
  c4.append(barras, el('div',{style:'font-family:var(--dado);font-size:10.5px;color:var(--ink-3);text-align:center',
    txt:'registros no mesmo dia'}));
  c4.append(el('div',{class:'prosa',style:'margin-top:11px;font-size:13px;max-width:none'},
    el('p',{html:`Intervalo mediano entre registros consecutivos: <strong>${nb(R.intervalo.mediana,0)} min</strong>. `+
      `Apenas ${R.ate_30min} dos ${R.pares_consecutivos} pares ocorrem em 30 min ou menos, e em nenhum deles os `+
      '24 itens se repetem por inteiro — são reenvios com alteração, não duplicatas.'})));
  g2.append(c3,c4); f.append(g2);
  return f;
};

SECQ['Univariada']=()=>{
  const f=document.createDocumentFragment();
  const g=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-bottom:14px'});
  const c=el('div',{class:'cartao'});
  c.append(el('h3',{txt:'Posição, dispersão e forma, por tipo de mensuração'}),
    el('p',{class:'leg',txt:'Escores de subescala são discretos: dezessete valores inteiros possíveis. '+
      'Mediana e intervalo interquartil são as medidas de referência; a média entra como complemento.'}));
  const tw=el('div',{class:'tabwrap',style:'max-height:460px'}), t=el('table');
  t.append(el('thead',{},el('tr',{},...['Variável','Tipo','n','Mín','Q1','Md','Q3','Máx','Média','DP','CV %',
    'Assim.','Curt.','Shapiro p'].map(h=>el('th',{txt:h})))));
  const tb=el('tbody');
  QA.UNI.forEach(u=>tb.append(el('tr',{},
    el('td',{style:'font-weight:600',txt:rot(u.variavel)}),
    el('td',{},el('span',{class:'tag',txt:u.tipo})),
    el('td',{class:'num',txt:u.n}), el('td',{class:'num',txt:nb(u.minimo,1)}),
    el('td',{class:'num',txt:nb(u.q1,1)}), el('td',{class:'num',txt:nb(u.mediana,1)}),
    el('td',{class:'num',txt:nb(u.q3,1)}), el('td',{class:'num',txt:nb(u.maximo,1)}),
    el('td',{class:'num',txt:nb(u.media)}), el('td',{class:'num',txt:nb(u.desvio)}),
    el('td',{class:'num',txt:u.cv==null?'—':nb(u.cv,1)}),
    el('td',{class:'num',txt:nb(u.assimetria)}), el('td',{class:'num',txt:nb(u.curtose)}),
    el('td',{class:'num',style:'color:#B3341A',txt:pb(u.shapiro_p).replace('p ','')}))));
  t.append(tb); tw.append(t); c.append(tw);
  c.append(el('div',{style:LEGQ+';margin:8px 0 0',
    txt:'Nenhuma variável passa no teste de normalidade, o que sustenta a via não paramétrica como rota '+
        'principal do Artigo 2. A assimetria de depressão, raiva e confusão vem do piso da escala.'}));
  g.append(c); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1.1fr 1fr'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'Caixa e bigodes'}),
    el('p',{class:'leg',txt:'A faixa avermelhada é a cerca de Tukey; o ponto branco é a média. Escolha a variável.'}));
  const chips=el('div',{style:'display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px'});
  QA.UNI.filter(u=>u.tipo!=='contínua'||u.variavel==='Hora do registro').forEach(u=>
    chips.append(el('button',{class:'chip','aria-pressed':String(u.variavel===estadoQ.caixa),
      onclick:()=>{estadoQ.caixa=u.variavel; render('qualidade');}},
      el('i',{style:`--cc:${CV[u.variavel]||'#87968F'}`}), rot(u.variavel))));
  c1.append(chips);
  const u=UNIQ[estadoQ.caixa];
  c1.append(grafCaixa(u,{cor:CV[u.variavel]||'#2166AC'}));
  const gr=el('div',{class:'grade',style:'grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px'});
  [['IQR',nb(u.iqr)],['MAD',nb(u.mad)],['Amplitude',nb(u.amplitude,1)],
   ['Assimetria',nb(u.assimetria)],['Curtose',nb(u.curtose)],['CV',u.cv==null?'—':nb(u.cv,1)+'%'],
   ['Classes · Sturges',String(u.k_sturges)],['Classes · Freedman-Diaconis',u.k_fd==null?'—':String(u.k_fd)],
   ['No valor mínimo',nb(u.pct_no_piso,1)+'%']]
   .forEach(([r,v])=>gr.append(el('div',{style:'border-left:2px solid var(--rule-2);padding-left:9px'},
     el('div',{style:LEGQ,txt:r}),
     el('div',{style:'font-family:var(--dado);font-size:15px;font-weight:600',txt:v}))));
  c1.append(gr);

  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Tabela de frequência das categóricas'}),
    el('p',{class:'leg',txt:'Frequência simples, acumulada e entropia normalizada — 1 é uniforme, 0 é degenerada.'}));
  const seg=el('div',{class:'seg',style:'margin-bottom:12px;flex-wrap:wrap'});
  Object.keys(QA.FREQ).forEach(k=>seg.append(el('button',{txt:k,'aria-pressed':String(k===estadoQ.freq),
    onclick:()=>{estadoQ.freq=k; render('qualidade');}})));
  c2.append(seg);
  const ft=QA.FREQ[estadoQ.freq];
  const tw2=el('div',{class:'tabwrap',style:'max-height:none'}), t2=el('table');
  t2.append(el('thead',{},el('tr',{},...['Nível','f','%','f acum.','% acum.',''].map(h=>el('th',{txt:h})))));
  const tb2=el('tbody');
  const mx=Math.max(...ft.linhas.map(l=>l.f));
  ft.linhas.forEach(l=>tb2.append(el('tr',{},
    el('td',{style:'white-space:normal',txt:l.nivel}), el('td',{class:'num',txt:l.f}),
    el('td',{class:'num',txt:nb(l.pct,1)}), el('td',{class:'num',txt:l.f_acum}),
    el('td',{class:'num',txt:nb(l.pct_acum,1)}),
    el('td',{style:'width:96px'},el('div',{style:`height:9px;border-radius:3px;background:#2166AC;opacity:.75;width:${mx?l.f/mx*88:0}px`})))));
  t2.append(tb2); tw2.append(t2); c2.append(tw2);
  c2.append(el('div',{style:LEGQ+';margin:8px 0 0',
    txt:`n = ${ft.n} · moda «${ft.moda}» · entropia normalizada H* = ${nb(ft.entropia_normalizada,3)}`}));
  g2.append(c1,c2); f.append(g2);
  return f;
};

SECQ['Discrepantes']=()=>{
  const f=document.createDocumentFragment();
  const c0=el('div',{class:'cartao',style:'margin-bottom:14px;background:linear-gradient(120deg,#FBFCFB,#F0F6F3)'});
  c0.append(el('h3',{style:'font-size:16px',txt:'Nenhum valor fora do domínio, e uma regra que não se aplica'}),
    el('div',{class:'prosa',style:'margin-top:8px;max-width:80ch'},
      el('p',{html:'Antes de qualquer critério de dispersão vem a verificação de domínio: valor fora do intervalo '+
        'admissível da escala é erro, não discrepância. <strong>Nenhum dos 456 registros tem escore impossível.</strong>'}),
      el('p',{html:'Em Confusão o primeiro e o terceiro quartis coincidem no piso. O intervalo interquartil é zero, '+
        'a cerca de Tukey colapsa, e a regra passa a rotular como discrepante toda resposta diferente de zero — '+
        'quase um quinto da amostra. O escore z modificado falha pelo mesmo motivo, porque o desvio absoluto '+
        'mediano também é zero. Nessas subescalas a triagem tem de ser feita pelo domínio e pela comparação de '+
        'cada atleta consigo mesmo.'})));
  f.append(c0);

  const g=el('div',{class:'grade',style:'grid-template-columns:1fr'});
  const c=el('div',{class:'cartao'});
  c.append(el('h3',{txt:'Três critérios, e a verificação de domínio'}),
    el('p',{class:'leg',txt:'Cerca de Tukey: Q1 − 1,5·IQR e Q3 + 1,5·IQR. Escore z: |z| > 3. '+
      'Escore z modificado: 0,6745·(x − Md) ÷ MAD, com corte em 3,5.'}));
  const tw=el('div',{class:'tabwrap',style:'max-height:none'}), t=el('table');
  t.append(el('thead',{},el('tr',{},...['Variável','Domínio','Fora do domínio','Tukey 1,5','Tukey 3,0',
    '|z| > 3','|z modif.| > 3,5'].map(h=>el('th',{txt:h})))));
  const tb=el('tbody');
  QA.UNI.forEach(u=>tb.append(el('tr',{},
    el('td',{style:'font-weight:600',txt:rot(u.variavel)}),
    el('td',{class:'num',txt:u.dominio?`${nb(u.dominio[0],0)} a ${nb(u.dominio[1],0)}`:'—'}),
    el('td',{class:'num'},u.fora_do_dominio==null?'—':el('span',{class:'pill '+(u.fora_do_dominio?'cr':'bom'),
      txt:String(u.fora_do_dominio)})),
    el('td',{class:'num',style:u.iqr_nulo?'color:#B3341A;font-weight:600':''},
      u.n_tukey_moderado+(u.iqr_nulo?'  ⚠':'')),
    el('td',{class:'num',txt:u.n_tukey_extremo}), el('td',{class:'num',txt:u.n_z3}),
    el('td',{class:'num',style:u.n_zmod==null?'color:#B3341A':'',txt:u.n_zmod==null?'MAD = 0':String(u.n_zmod)}))));
  t.append(tb); tw.append(t); c.append(tw);
  c.append(el('div',{style:LEGQ+';margin:8px 0 0',
    txt:'⚠ marca a variável em que o intervalo interquartil é zero, o que torna a cerca de Tukey inaplicável.'}));
  g.append(c); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-top:14px'});
  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Discrepantes intraindividuais: o atleta contra a própria série'}),
    el('p',{class:'leg',txt:'Escore z modificado calculado dentro da série de cada atleta, entre os que têm quatro '+
      'dias ou mais. Um caso destes não é erro: é o dia fora do padrão que o monitoramento existe para detectar.'}));
  const tw2=el('div',{class:'tabwrap',style:'max-height:none'}), t2=el('table');
  t2.append(el('thead',{},el('tr',{},...['Variável','Atletas avaliados','Casos','Caso mais extremo'].map(h=>el('th',{txt:h})))));
  const tb2=el('tbody');
  QA.INTRA.forEach(i=>{
    const c0=i.casos[0];
    tb2.append(el('tr',{},
      el('td',{style:'font-weight:600',txt:rot(i.variavel)}),
      el('td',{class:'num',txt:i.atletas_avaliados}), el('td',{class:'num',txt:i.n_discrepantes}),
      el('td',{style:'white-space:normal',txt:c0?`${c0.atleta} em D${c0.dia}: ${nb(c0.valor,0)} contra mediana `+
        `própria ${nb(c0.mediana_do_atleta,0)}  (z_M = ${nb(c0.z_mod,1)})`:'—'})));
  });
  t2.append(tb2); tw2.append(t2); c2.append(tw2);
  g2.append(c2); f.append(g2);
  return f;
};

SECQ['Reconferência']=()=>{
  const f=document.createDocumentFragment();
  const c0=el('div',{class:'cartao',style:'margin-bottom:14px;background:linear-gradient(120deg,#FBFCFB,#F0F6F3)'});
  c0.append(el('h3',{style:'font-size:16px',txt:'Os números dos três documentos, recalculados por outro caminho'}),
    el('div',{class:'prosa',style:'margin-top:8px;max-width:80ch'},
      el('p',{html:'A conferência foi feita por dois caminhos de código independentes. O primeiro parte das colunas '+
        'já pontuadas e é o que gerou a base canônica. O segundo parte do item do formulário e reconstrói tudo por '+
        `fórmula. <strong>As ${CO.total} conferências batem.</strong> Nada precisa ser corrigido no texto dos artigos.`})));
  f.append(c0);
  const g=el('div',{class:'grade',style:'grid-template-columns:1.25fr 1fr'});
  const c=el('div',{class:'cartao'});
  c.append(el('h3',{txt:'Conferência item a item'}),
    el('p',{class:'leg',txt:'Tolerância de 5 × 10⁻³ para médias e derivadas, e de 10⁻⁶ para valores de p.'}));
  const tw=el('div',{class:'tabwrap',style:'max-height:470px'}), t=el('table');
  t.append(el('thead',{},el('tr',{},...['Bloco','Item','Caminho A','Caminho B','Diferença',''].map(h=>el('th',{txt:h})))));
  const tb=el('tbody');
  CO.CONF.forEach(r=>tb.append(el('tr',{},
    el('td',{style:'white-space:normal;color:var(--ink-2)',txt:r.bloco}),
    el('td',{style:'white-space:normal;font-weight:600',txt:r.item}),
    el('td',{class:'num',txt:nb(r.caminho_a,4)}), el('td',{class:'num',txt:nb(r.caminho_b,4)}),
    el('td',{class:'num',txt:r.diferenca==null?'—':nb(r.diferenca,6)}),
    el('td',{},el('span',{class:'pill '+(r.confere?'bom':'cr'),txt:r.confere?'bate':'diverge'})))));
  t.append(tb); tw.append(t); c.append(tw);
  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Normalidade das médias diárias'}),
    el('p',{class:'leg',txt:'É este teste que decide a via principal do Artigo 2.'}));
  const tw2=el('div',{class:'tabwrap',style:'max-height:none'}), t2=el('table');
  t2.append(el('thead',{},el('tr',{},...['Variável','n','W','p','Distribuição'].map(h=>el('th',{txt:h})))));
  const tb2=el('tbody');
  CO.NORMALIDADE.forEach(n=>tb2.append(el('tr',{},
    el('td',{style:'font-weight:600',txt:rot(n.variavel)}), el('td',{class:'num',txt:n.n}),
    el('td',{class:'num',txt:nb(n.W,4)}), el('td',{class:'num',txt:pb(n.p).replace('p ','')}),
    el('td',{},el('span',{class:'pill '+(n.normal?'bom':'at'),txt:n.normal?'normal':'não normal'})))));
  t2.append(tb2); tw2.append(t2); c2.append(tw2);
  c2.append(el('div',{class:'prosa',style:'margin-top:11px;font-size:13px;max-width:none'},
    el('p',{html:'Sete de sete rejeitam a normalidade. A via não paramétrica é a rota principal, e a paramétrica '+
      'entra como conferência — que é exatamente o desenho do Artigo 2.'})));
  g.append(c,c2); f.append(g);
  return f;
};

SECQ['Otimização']=()=>{
  const f=document.createDocumentFragment();
  const M=OT.MODELO, OB=OT.OBSERVADO, P1=OT.PROGRAMA_I;
  const kp=el('div',{class:'grade',style:'grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin-bottom:14px'});
  const d5=OT.EQ.find(e=>e.restricao.startsWith('D5'));
  [['Efeito da véspera',nb(M.Fadiga.b2,3),'ponto de fadiga por hora de ontem','#8A4FBF'],
   ['Efeito do próprio dia',nb(M.Fadiga.b1,3),'não significativo (p = '+nb(M.Fadiga.p1,3)+')','#87968F'],
   ['Pior dia de vigor',nb(OB.vigor_minimo)+' → '+nb(P1.vigor_minimo_garantido),'com as mesmas 23 h','#1A7F5A'],
   ['Custo do amistoso',nb(d5.preco_sombra,3),'ponto de vigor por hora de jogo','#B3341A'],
   ['Carga mínima estrutural',nb(OT.CARGA_MINIMA_ESTRUTURAL)+'<small> h</small>','abaixo disso, inviável','#E0952B']]
   .forEach(([r,v,n,c])=>kp.append(el('div',{class:'kpi',style:`--k:${c}`},
     el('div',{class:'rot',txt:r}),el('div',{class:'val',html:v}),el('div',{class:'nota',txt:n}))));
  f.append(kp);

  const g=el('div',{class:'grade',style:'grid-template-columns:1fr 1.15fr'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'O humor do dia responde à véspera'}),
    el('p',{class:'leg',txt:'Modelo misto com intercepto aleatório por atleta: y = β₀ + β₁·h(d) + β₂·h(d−1) + u(a).'}));
  const tw=el('div',{class:'tabwrap',style:'max-height:none'}), t=el('table');
  t.append(el('thead',{},el('tr',{},...['Variável','β₀','β₁ · dia','p','β₂ · véspera','p'].map(h=>el('th',{txt:h})))));
  const tb=el('tbody');
  ['Fadiga','Vigor','TMD','Tensão'].forEach(v=>{const m=M[v];
    tb.append(el('tr',{},
      el('td',{style:'font-weight:600',txt:rot(v)}), el('td',{class:'num',txt:nb(m.b0,3)}),
      el('td',{class:'num',style:m.p1<.05?'':'color:var(--ink-3)',txt:nb(m.b1,4)}),
      el('td',{class:'num',style:m.p1<.05?'color:#B3341A':'color:var(--ink-3)',txt:pb(m.p1).replace('p ','')}),
      el('td',{class:'num',style:m.p2<.05?'font-weight:600':'color:var(--ink-3)',txt:nb(m.b2,4)}),
      el('td',{class:'num',style:m.p2<.05?'color:#B3341A':'color:var(--ink-3)',txt:pb(m.p2).replace('p ','')})));});
  t.append(tb); tw.append(t); c1.append(tw);
  c1.append(el('div',{class:'prosa',style:'margin-top:11px;font-size:13.5px;max-width:none'},
    el('p',{html:'As horas do próprio dia não têm efeito detectável; as da véspera têm. <strong>O humor medido hoje '+
      'é o eco do treino de ontem.</strong> A restrição de recuperação do programa é defasada em um dia.'}),
    el('p',{style:'font-size:12.5px;color:var(--ink-2)',
      html:'Com uma equipe e sete dias, o efeito das horas não se separa do efeito do dia nem da carga acumulada. '+
        'Os coeficientes são associativos, e o programa é instrumento de planejamento, não prova causal.'})));

  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Mesma carga, arranjo que maximiza o pior dia de vigor'}),
    el('p',{class:'leg',txt:'max t   sujeito a   vigor previsto no dia d ≥ t, para d = 1…7, com Σ h(d) = 23 h.'}));
  const tw2=el('div',{class:'tabwrap',style:'max-height:none'}), t2=el('table');
  t2.append(el('thead',{},el('tr',{},...['Dia','Estímulo','Observado','Ótimo','Δ','Fadiga prev.','Vigor prev.'].map(h=>el('th',{txt:h})))));
  const tb2=el('tbody');
  for(let d=1;d<=7;d++){
    const dif=P1.horas[d-1]-OB.horas[d-1];
    tb2.append(el('tr',{},
      el('td',{style:`font-weight:600;color:${CEST[OT.TIPO[d]]}`,txt:'D'+d}),
      el('td',{},el('span',{class:'tag',style:`background:${FUNDO[OT.TIPO[d]]};color:${CEST[OT.TIPO[d]]}`,txt:OT.TIPO[d]})),
      el('td',{class:'num',txt:nb(OB.horas[d-1],1)}),
      el('td',{class:'num',style:'font-weight:600',txt:nb(P1.horas[d-1])}),
      el('td',{class:'num',style:`color:${Math.abs(dif)<.05?'var(--ink-3)':(dif>0?'#1A7F5A':'#B3341A')}`,
        txt:(dif>=0?'+':'')+nb(dif)}),
      el('td',{class:'num',txt:nb(P1.fadiga[d-1])}), el('td',{class:'num',txt:nb(P1.vigor[d-1])})));
  }
  tb2.append(el('tr',{style:'font-weight:600;border-top:2px solid var(--rule-2)'},
    el('td',{txt:'Total'}), el('td',{}), el('td',{class:'num',txt:nb(OB.total,1)}),
    el('td',{class:'num',txt:nb(P1.total)}), el('td',{class:'num',txt:'0,00'}), el('td',{}), el('td',{})));
  t2.append(tb2); tw2.append(t2); c2.append(tw2);
  g.append(c1,c2); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1fr 1fr;margin-top:14px'});
  const c3=el('div',{class:'cartao'});
  c3.append(el('h3',{txt:'Quem segura a solução'}),
    el('p',{class:'leg',txt:'O preço-sombra é a variação do pior dia de vigor por unidade de afrouxamento da restrição.'}));
  const Rs=OT.ATIVAS.filter(r=>!r.restricao.includes('≥ t'))
    .concat(OT.EQ.map(e=>({restricao:e.restricao,preco_sombra:e.preco_sombra,folga:null})))
    .sort((a,b)=>Math.abs(b.preco_sombra)-Math.abs(a.preco_sombra)).slice(0,6);
  c3.append(grafBarras(Rs.map(r=>({nome:r.restricao.replace('vigor previsto ','vigor ').replace('polimento: ','polim. ')
      .replace(' pelo calendário','').replace('fixado em','fixo em').replace(/(\d)\.(\d)/g,'$1,$2'),
    valor:Math.abs(r.preco_sombra), rotulo:nb(r.preco_sombra,4),
    dica:`<b>${r.restricao}</b><br>preço-sombra ${nb(r.preco_sombra,4)} ponto de vigor`+
         (r.folga!=null?`<br>folga ${nb(r.folga,3)}`:'<br>restrição de igualdade'),
    cor:r.preco_sombra<0?'#B3341A':'#0F6E5C'})), {larg:560, dominio:0.5}));
  c3.append(el('div',{class:'legenda'},
    el('span',{},el('i',{style:'background:#B3341A'}),'custa ao objetivo: afrouxar melhoraria o pior dia'),
    el('span',{},el('i',{style:'background:#0F6E5C'}),'sustenta a solução')));
  c3.append(el('div',{class:'prosa',style:'margin-top:10px;font-size:13.5px;max-width:none'},
    el('p',{html:`O maior valor absoluto é o do amistoso de D5. <strong>Cada hora daquele jogo custa `+
      `${nb(Math.abs(d5.preco_sombra),3)} ponto do pior dia de vigor da semana</strong> — mais do que qualquer `+
      'decisão de treino disponível. Quem comprime este microciclo é o calendário de jogos, não o volume de treino.'})));

  const c4=el('div',{class:'cartao'});
  c4.append(el('h3',{txt:'Fronteira eficiente: o que a semana custa em vigor'}),
    el('p',{class:'leg',txt:'Para cada carga semanal exigida, o maior valor possível do pior dia de vigor.'}));
  c4.append(grafFronteira());
  c4.append(el('div',{class:'prosa',style:'margin-top:10px;font-size:13.5px;max-width:none'},
    el('p',{html:`A fronteira é quase horizontal, o que confirma a leitura dos preços-sombra. A informação prática `+
      `é a outra: com dois amistosos e a regra de variação máxima entre dias, a semana <strong>não pode ter menos `+
      `de ${nb(OT.CARGA_MINIMA_ESTRUTURAL)} horas</strong> — abaixo disso nenhuma distribuição é viável.`})));
  g2.append(c3,c4); f.append(g2);

  const g3=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-top:14px'});
  const c5=el('div',{class:'cartao'});
  c5.append(el('h3',{txt:'Sensibilidade dos parâmetros'}),
    el('p',{class:'leg',txt:'Carga semanal mantida em 23 h. «Inviável» indica que nenhuma distribuição satisfaz '+
      'todas as restrições com aquele valor.'}));
  const gs=el('div',{class:'grade',style:'grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px'});
  OT.SENSIBILIDADE.forEach((s_,i)=>{
    const box=el('div',{style:`border-left:2.5px solid ${CAT[i%6]};padding-left:11px`});
    box.append(el('div',{style:'font-size:12.5px;font-weight:600;margin-bottom:6px',txt:s_.parametro}));
    s_.pontos.forEach(p=>box.append(el('div',{style:'display:flex;justify-content:space-between;gap:10px;'+
      'font-family:var(--dado);font-size:11.5px;padding:2px 0;color:'+(p.viavel?'var(--ink)':'#B3341A')},
      el('span',{txt:nb(p.valor,2)}),
      el('span',{txt:p.viavel?nb(p.vigor_minimo,3):'inviável'}))));
    gs.append(box);
  });
  c5.append(gs);
  g3.append(c5); f.append(g3);
  return f;
};

TELAS.qualidade=()=>{
  segTopo.hidden=false; segTopo.innerHTML='';
  const f=document.createDocumentFragment();
  const sec=SECQ[estadoQ.sec]?estadoQ.sec:'Qualidade';
  Object.keys(SECQ).forEach(nome=>segTopo.append(el('button',{txt:nome,'aria-pressed':String(nome===sec),
    onclick:()=>{estadoQ.sec=nome; render('qualidade');}})));
  f.append(SECQ[sec]());
  return f;
};
