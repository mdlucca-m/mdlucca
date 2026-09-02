/* ============ séries · filtro, cruzamentos e decomposições ============ */
const CZ=D.cruz, DK=D.decomp, PR=D.proto;
const estadoS={sec:'Filtro e ruído', par:Object.keys(CZ.CRUZ)[0]};
const LEGS='font-family:var(--dado);font-size:10.5px;color:var(--ink-3);line-height:1.5';
const NOTAS='font-size:12.5px;color:var(--ink-2);line-height:1.55';
const CPAR={'Vigor×Fadiga':'#C1440E','Vigor×TMD':'#2166AC','Fadiga×TMD':'#8A4FBF'};
const rotPar=k=>k.split('×').map(rot).join(' × ');

/* ---- resposta em frequência do núcleo ---- */
function grafResposta({larg=760,alt=300}={}){
  const M={t:16,r:18,b:34,l:44}, W=larg, H=alt;
  const w=CZ.RESPOSTA.w, Hb=CZ.RESPOSTA.H, Hm=CZ.RESPOSTA.H_media_movel;
  const px=v=>M.l+(v/Math.PI)*(W-M.l-M.r), py=v=>M.t+(1.08-v)/(1.08+0.42)*(H-M.t-M.b);
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g',style:`max-width:${W}px`});
  [1,.5,0,-.25].forEach(v=>{
    g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(v),y2:py(v),stroke:'#E4E9E7','stroke-width':1}));
    stx(g,{x:M.l-8,y:py(v)+4,'text-anchor':'end',class:'eixo'},nb(v,1));
  });
  g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(0),y2:py(0),stroke:'#87968F','stroke-width':1.2}));
  const cam=(arr,cor,tra)=>{
    const d=arr.map((v,i)=>`${i?'L':'M'}${px(w[i])},${py(v)}`).join(' ');
    g.append(s('path',{d,fill:'none',stroke:cor,'stroke-width':tra?2:3,
      'stroke-dasharray':tra?'5 4':'','stroke-linejoin':'round'}));
  };
  cam(Hm,'#B3341A',true); cam(Hb,'#2166AC',false);
  const nq=s('circle',{cx:px(Math.PI),cy:py(0),r:6,fill:'#FBFCFB',stroke:'#2166AC','stroke-width':2.4});
  comDica(nq,'<b>frequência de Nyquist</b><br>ganho zero: a oscilação que alterna a cada dia é removida por construção');
  g.append(nq);
  [['0',0],['π/2',Math.PI/2],['π',Math.PI]].forEach(([r,v])=>
    stx(g,{x:px(v),y:H-M.b+16,'text-anchor':'middle',class:'eixo'},r));
  stx(g,{x:(M.l+W-M.r)/2,y:H-6,'text-anchor':'middle',class:'eixo'},'frequência ω');
  return g;
}

/* ---- resíduo do filtro, em unidades do piso ---- */
function grafResiduo(v,{larg=300,alt=150}={}){
  const M={t:14,r:14,b:26,l:34}, W=larg, H=alt, f=DK.FILTRO[v], fl=CZ.FILTRO[v];
  const r=fl.residuo_em_pisos, lo=-2.1, hi=2.1;
  const px=i=>M.l+(i+.5)/7*(W-M.l-M.r), py=y=>M.t+(hi-y)/(hi-lo)*(H-M.t-M.b);
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g',style:`max-width:${W}px`});
  g.append(s('rect',{x:M.l,y:py(1),width:W-M.l-M.r,height:py(-1)-py(1),fill:CV[v]||'#2A2F33',opacity:.10}));
  [1,-1].forEach(k=>g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(k),y2:py(k),
    stroke:CV[v]||'#2A2F33','stroke-width':1.2,'stroke-dasharray':'4 3'})));
  g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(0),y2:py(0),stroke:'#25332F','stroke-width':1.2}));
  r.forEach((y,i)=>{
    const bw=(W-M.l-M.r)/7*.5;
    const b=s('rect',{x:px(i)-bw/2,y:Math.min(py(y),py(0)),width:bw,
      height:Math.abs(py(y)-py(0))||1,fill:CV[v]||'#2A2F33',opacity:.85});
    comDica(b,`<b>D${i+1}</b><br>resíduo ${nb(y)} piso`);
    g.append(b);
    stx(g,{x:px(i),y:H-8,'text-anchor':'middle',class:'eixo'},'D'+(i+1));
  });
  [2,0,-2].forEach(k=>stx(g,{x:M.l-6,y:py(k)+4,'text-anchor':'end',class:'eixo'},nb(k,0)));
  return g;
}

/* ---- a diferença de um par contra o limiar, com a zona de indecisão ---- */
function grafDiferenca(k,{larg=900,alt=330}={}){
  const M={t:18,r:26,b:34,l:48}, W=larg, H=alt, c=CZ.CRUZ[k], co=CPAR[k], it=c.cruzamentos[0];
  const d=c.dif, lim=c.limiar;
  const lo=Math.min(...d,-lim)*1.18, hi=Math.max(...d,lim)*1.14;
  const px=x=>M.l+(x-1)/6*(W-M.l-M.r), py=y=>M.t+(hi-y)/(hi-lo)*(H-M.t-M.b);
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g',style:`max-width:${W}px`});
  /* zona de indecisão */
  const zi=s('rect',{x:px(it.zona_ini),y:M.t,width:Math.max(px(it.zona_fim)-px(it.zona_ini),1),
    height:H-M.t-M.b,fill:co,opacity:.10});
  comDica(zi,`<b>zona de indecisão</b><br>D${nb(it.zona_ini)} a D${nb(it.zona_fim)} · ${nb(it.zona_largura)} dia<br>`+
    'intervalo em que a diferença fica dentro do limiar, isto é, em que as duas séries não se distinguem');
  g.append(zi);
  /* faixa do limiar */
  g.append(s('rect',{x:M.l,y:py(lim),width:W-M.l-M.r,height:py(-lim)-py(lim),fill:'#DDE0E2',opacity:.55}));
  [lim,-lim].forEach(v=>g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(v),y2:py(v),
    stroke:'#87968F','stroke-width':1.1,'stroke-dasharray':'4 3'})));
  g.append(s('line',{x1:M.l,x2:W-M.r,y1:py(0),y2:py(0),stroke:'#25332F','stroke-width':1.3}));
  const cam=d.map((v,i)=>`${i?'L':'M'}${px(i+1)},${py(v)}`).join(' ');
  g.append(s('path',{d:cam,fill:'none',stroke:co,'stroke-width':3,'stroke-linejoin':'round'}));
  d.forEach((v,i)=>{
    const p=s('circle',{cx:px(i+1),cy:py(v),r:4.6,fill:co,stroke:'#FBFCFB','stroke-width':1.4});
    comDica(p,`<b>D${i+1}</b><br>diferença ${nb(v)} ponto`); g.append(p);
    stx(g,{x:px(i+1),y:H-M.b+16,'text-anchor':'middle',class:'eixo'},'D'+(i+1));
  });
  const cz=s('circle',{cx:px(it.abscissa),cy:py(0),r:8,fill:'#FBFCFB',stroke:co,'stroke-width':2.6});
  comDica(cz,`<b>cruzamento em D${nb(it.abscissa)}</b><br>velocidade ${nb(it.velocidade_em_limiares)} limiar/dia<br>`+
    `aceleração ${nb(it.aceleracao_em_limiares)} limiar/dia²`);
  g.append(cz);
  /* escala vertical: o limiar, o zero e os dois extremos observados da diferença */
  const mx=Math.max(...d), mn=Math.min(...d);
  [[lim,nb(lim,1)],[0,'0'],[-lim,nb(-lim,1)]].forEach(([v,t])=>
    stx(g,{x:M.l-8,y:py(v)+4,'text-anchor':'end',class:'eixo'},t));
  [mx,mn].forEach(v=>{ if(Math.abs(Math.abs(v)-lim)<lim*.45) return;
    stx(g,{x:M.l-8,y:py(v)+4,'text-anchor':'end',class:'eixo'},nb(v,1)); });
  return g;
}

/* rótulo escuro sobre preenchimento claro, claro sobre escuro */
const claro=hex=>{const h=hex.replace('#',''); const n=parseInt(h.length===3?h.replace(/(.)/g,'$1$1'):h,16);
  return (0.2126*((n>>16)&255)+0.7152*((n>>8)&255)+0.0722*(n&255))/255 > 0.6;};

/* ---- barra empilhada horizontal genérica ---- */
function grafPilha(linhas,{larg=1000,rotulos=[],cores=[],unid='%'}={}){
  const M={t:16,r:64,b:26,l:112}, hl=30, H=M.t+M.b+linhas.length*hl, W=larg;
  const px=v=>M.l+v/100*(W-M.l-M.r);
  const g=s('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',class:'g',style:`max-width:${W}px`});
  [0,25,50,75,100].forEach(v=>{
    g.append(s('line',{x1:px(v),x2:px(v),y1:M.t-6,y2:H-M.b,stroke:'#E4E9E7','stroke-width':1}));
    stx(g,{x:px(v),y:H-M.b+15,'text-anchor':'middle',class:'eixo'},v+'');
  });
  linhas.forEach((L,i)=>{
    const y=M.t+i*hl+4, h=hl-12; let base=0;
    stx(g,{x:M.l-10,y:y+h/2+4,'text-anchor':'end',
      style:'font-family:var(--disp);font-size:12px;fill:#25332F;font-weight:600'},L.nome);
    L.val.forEach((v,j)=>{
      const b=s('rect',{x:px(base),y,width:Math.max(px(base+v)-px(base),0),height:h,fill:cores[j]});
      comDica(b,`<b>${L.nome}</b><br>${rotulos[j]}: ${nb(v,1)}${unid}`); g.append(b);
      if(v>=9) stx(g,{x:px(base+v/2),y:y+h/2+4,'text-anchor':'middle',
        style:`font-family:var(--dado);font-size:10.5px;font-weight:600;fill:${claro(cores[j])?'#25332F':'#FBFCFB'}`},nb(v,0)+'%');
      base+=v;
    });
    if(L.extra) stx(g,{x:W-M.r+8,y:y+h/2+4,style:'font-family:var(--dado);font-size:11px',fill:L.corExtra||'#6B7378'},L.extra);
  });
  return g;
}

const legenda=(itens)=>{const d=el('div',{class:'legenda'});
  itens.forEach(([c,t])=>d.append(el('span',{},el('i',{style:'background:'+c}),t))); return d;};

/* ============================== seções ============================== */
const SECSER={};

SECSER['Filtro e ruído']=()=>{
  const f=document.createDocumentFragment();
  f.append(el('div',{class:'prosa',style:'max-width:82ch;margin-bottom:14px'},
    el('p',{html:'Toda a leitura de séries deste estudo repousa sobre a série suavizada. Antes de usá-la, cabe '+
      'mostrar o que a suavização remove e com que direito. O núcleo é o binomial de três pontos, '+
      '<strong>[¼, ½, ¼]</strong>, aplicado aos pontos internos; os extremos conservam o valor observado, porque o '+
      'deslocamento total é medido entre eles.'})));
  const g=el('div',{class:'grade'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'O que o núcleo deixa passar'}),
    el('p',{class:'leg',txt:'Ganho por frequência. O binomial anula-se em Nyquist, que é a componente que alterna '+
      'a cada dia; a média móvel simples não se anula ali e ainda inverte o sinal de parte da banda alta.'}));
  c1.append(grafResposta());
  c1.append(legenda([['#2166AC','binomial 1-2-1'],['#B3341A','média móvel 1-1-1']]));
  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'A identidade da variância'}),
    el('p',{class:'leg',txt:'Var(observada) = Var(suavizada) + Var(resíduo) + 2·cov. As duas parcelas não são '+
      'ortogonais; onde a covariância é negativa, a parcela retida excede o total, o que significa que o filtro '+
      'retirou oscilação contrária à tendência.'}));
  const tb=el('table',{class:'tb'});
  tb.append(el('thead',{},el('tr',{},...['variável','Var obs.','retida','removida','2·cov'].map(h=>el('th',{txt:h})))));
  const tc=el('tbody');
  DK.V7.forEach(v=>{const x=DK.FILTRO[v];
    tc.append(el('tr',{},el('td',{txt:rot(v)}),el('td',{txt:nb(x.var_observada,3)}),
      el('td',{txt:nb(x.var_suavizada,3)}),el('td',{txt:nb(x.var_residuo,3)}),
      el('td',{txt:nb(2*x.covariancia,3),style:2*x.covariancia<0?'color:#B3341A':''})));});
  tb.append(tc); c2.append(tb);
  g.append(c1,c2); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:repeat(3,1fr);margin-top:14px'});
  ['Vigor','Fadiga','TMD'].forEach(v=>{
    const c=el('div',{class:'cartao'});
    const fl=CZ.FILTRO[v];
    c.append(el('h3',{txt:'Resíduo do filtro: '+rot(v)}),
      el('p',{class:'leg',html:`Piso de ruído <strong>${nb(fl.piso)}</strong>. A faixa marca uma unidade de piso `+
        `para cima e para baixo. Maior resíduo: <strong>${nb(fl.max_residuo_em_pisos)}</strong> piso.`}));
    c.append(grafResiduo(v));
    g2.append(c);
  });
  f.append(g2);
  f.append(el('div',{class:'prosa',style:'max-width:82ch;margin-top:14px'},
    el('p',{html:'O resíduo cabe dentro de uma unidade de piso em <strong>vinte das vinte e uma células</strong>. '+
      'O filtro removeu componente da ordem do ruído amostral, e não sinal, e é esse o direito com que a análise '+
      'prossegue sobre a série suavizada.'})));
  return f;
};

SECSER['Cruzamentos']=()=>{
  const f=document.createDocumentFragment();
  f.append(el('div',{class:'prosa',style:'max-width:82ch;margin-bottom:12px'},
    el('p',{html:'Um cruzamento é um zero da série da diferença. Dizer em que abscissa ele ocorre não basta: '+
      'interessa <strong>com que velocidade</strong> a diferença atravessa o zero e <strong>em que intervalo</strong> '+
      'ela permanece dentro do limiar, isto é, indistinguível de zero. Esse intervalo é a zona de indecisão, e ela '+
      'mede a determinação da data, ao passo que o veredito de inversão mede apenas a separação nos extremos. '+
      'As duas coisas não coincidem.'})));
  /* tabela-resumo dos três pares */
  const c0=el('div',{class:'cartao',style:'margin-bottom:14px'});
  c0.append(el('h3',{txt:'Os três cruzamentos, lado a lado'}));
  const tb=el('table',{class:'tb'});
  tb.append(el('thead',{},el('tr',{},...['par','limiar','cruza em','velocidade','aceleração','zona de indecisão','veredito']
    .map(h=>el('th',{txt:h})))));
  const tc=el('tbody');
  Object.entries(CZ.CRUZ).forEach(([k,c])=>{
    const it=c.cruzamentos[0], co=CPAR[k];
    tc.append(el('tr',{},
      el('td',{txt:rotPar(k),style:`color:${co};font-weight:600`}),
      el('td',{txt:'±'+nb(c.limiar)}),
      el('td',{txt:'D'+nb(it.abscissa)}),
      el('td',{txt:nb(it.velocidade_em_limiares)+' limiar/dia'}),
      el('td',{txt:nb(it.aceleracao_em_limiares)+' limiar/dia²'}),
      el('td',{txt:`D${nb(it.zona_ini)} a D${nb(it.zona_fim)}  ·  ${nb(it.zona_largura)} dia`,
        style:it.nitido?'':'color:#B3341A'}),
      el('td',{txt:c.estabelecida?'inversão estabelecida':'divergência',
        style:c.estabelecida?'color:#1A7F5A;font-weight:600':'color:#87968F'})));
  });
  tb.append(tc); c0.append(tb);
  c0.append(el('p',{class:'leg',style:'margin-top:8px',
    txt:'A travessia é dita nítida quando a diferença atravessa o zero a pelo menos um limiar por dia. Abaixo disso, '+
        'a data do cruzamento é mal determinada, ainda que a inversão esteja estabelecida.'}));
  f.append(c0);

  /* o par selecionado, em detalhe */
  const chaves=Object.keys(CZ.CRUZ);
  const par=chaves.includes(estadoS.par)?estadoS.par:chaves[0];
  const sel=el('div',{class:'seg',style:'margin-bottom:12px'});
  chaves.forEach(k=>sel.append(el('button',{txt:rotPar(k),'aria-pressed':String(k===par),
    onclick:()=>{estadoS.par=k; render('series');}})));
  f.append(sel);
  const c=CZ.CRUZ[par], it=c.cruzamentos[0], co=CPAR[par];
  const g=el('div',{class:'grade'});
  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'A diferença contra o limiar'}),
    el('p',{class:'leg',html:`Faixa cinzenta: limiar combinado, ±${nb(c.limiar)}. Faixa colorida: zona de indecisão.`}));
  c1.append(grafDiferenca(par));
  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Como se lê este cruzamento'}));
  const kpi=(r,v,cor)=>el('div',{style:'margin-bottom:10px'},
    el('div',{style:'font-family:var(--dado);font-size:22px;font-weight:600;color:'+(cor||'#25332F'),txt:v}),
    el('div',{style:LEGS,txt:r}));
  c2.append(kpi('separação no primeiro dia', nb(c.d1_ini)+' pt', co),
            kpi('separação no sétimo dia', nb(c.d7_fim)+' pt', co),
            kpi('velocidade na travessia', nb(it.velocidade_em_limiares)+' limiar/dia', it.nitido?'#1A7F5A':'#B3341A'),
            kpi('largura da zona de indecisão', nb(it.zona_largura)+' dia', it.nitido?'#1A7F5A':'#B3341A'));
  c2.append(el('div',{class:'prosa',style:'font-size:13px'},
    el('p',{html: it.nitido
      ? `A diferença atravessa o zero depressa e a zona de indecisão dura pouco: <strong>a data está bem determinada</strong>.`
      : `A separação supera o limiar nos dois extremos, mas a travessia é lenta e a zona de indecisão cobre `+
        `<strong>${nb(it.zona_largura)} dia</strong>. A inversão é certa; a data não. Ler o cruzamento como um ponto `+
        `concede à estimativa precisão que os dados não sustentam.`})));
  g.append(c1,c2); f.append(g);
  return f;
};

SECSER['Decomposições']=()=>{
  const f=document.createDocumentFragment();
  const g=el('div',{class:'grade'});

  const c1=el('div',{class:'cartao'});
  c1.append(el('h3',{txt:'De onde vem a variância do par atleta-dia'}),
    el('p',{class:'leg',txt:'Componentes de um modelo de efeitos aleatórios cruzados, atleta e dia, por máxima '+
      'verossimilhança restrita sobre os 166 pares.'}));
  c1.append(grafPilha(DK.V7.map(v=>({nome:rot(v),
      val:[DK.COMPONENTES[v].p_atleta, DK.COMPONENTES[v].p_dia, DK.COMPONENTES[v].p_residual]})),
    {rotulos:['entre atletas','entre dias','residual'],cores:['#2166AC','#C1440E','#B8BEC3']}));
  c1.append(legenda([['#2166AC','entre atletas'],['#C1440E','entre dias'],['#B8BEC3','residual']]));
  c1.append(el('div',{class:'prosa',style:'margin-top:10px;font-size:13px'},
    el('p',{html:'A parcela que corresponde ao objeto deste estudo, o movimento do elenco de um dia para o outro, é '+
      `a <strong>menor das três em todas as sete variáveis</strong>, de ${nb(DK.COMPONENTES['Depressão'].p_dia,1)}% `+
      `na depressão a ${nb(DK.COMPONENTES['Vigor'].p_dia,1)}% no vigor. Raiva e confusão, com componente residual de `+
      `${nb(DK.COMPONENTES['Raiva'].p_residual,0)}% e ${nb(DK.COMPONENTES['Confusão'].p_residual,0)}%, comportam-se `+
      'como estado idiossincrático: neles a média do grupo informa pouco sobre o atleta.'})));

  const c2=el('div',{class:'cartao'});
  c2.append(el('h3',{txt:'Quanto da variação diária sobreviveria à medida sem erro'}),
    el('p',{class:'leg',txt:'A variância entre as sete médias diárias contém a variação verdadeira somada à média '+
      'dos erros-padrão ao quadrado. Subtraída a segunda parcela, resta a primeira; a razão entre ela e o total é a '+
      'fidedignidade da série.'}));
  c2.append(grafPilha(DK.V7.map(v=>{const x=DK.SERIE[v], t=Math.max(x.var_verdadeira+x.var_erro,1e-9);
      return {nome:rot(v), val:[100*x.var_verdadeira/t, 100*x.var_erro/t],
              extra:x.fidedignidade>0?('fid. '+nb(x.fidedignidade)):'fid. nula',
              corExtra:x.fidedignidade>=.5?'#1A7F5A':'#87968F'};}),
    {rotulos:['variação verdadeira','erro de amostragem'],cores:['#1A9070','#DDE0E2']}));
  c2.append(legenda([['#1A9070','variação verdadeira'],['#DDE0E2','erro de amostragem']]));
  c2.append(el('div',{class:'prosa',style:'margin-top:10px;font-size:13px'},
    el('p',{html:`Apenas o vigor (${nb(DK.SERIE['Vigor'].fidedignidade)}) e a fadiga `+
      `(${nb(DK.SERIE['Fadiga'].fidedignidade)}) têm série majoritariamente verdadeira. Na depressão a estimativa é `+
      `<strong>nula</strong>: a variância entre as sete médias, de ${nb(DK.SERIE['Depressão'].var_observada,3)}, é `+
      `menor do que a média dos erros-padrão ao quadrado, de ${nb(DK.SERIE['Depressão'].var_erro,3)}.`})));
  g.append(c1,c2); f.append(g);

  const g2=el('div',{class:'grade',style:'grid-template-columns:1fr;margin-top:14px'});
  const c3=el('div',{class:'cartao'});
  c3.append(el('h3',{txt:'O deslocamento da semana, separado em choque e deriva'}),
    el('p',{class:'leg',txt:'As seis transições da série suavizada são separadas conforme superem ou não o piso de '+
      'ruído. A coluna de referência é a do movimento absoluto, porque choque e deriva podem apontar em sentidos opostos.'}));
  const tb=el('table',{class:'tb'});
  tb.append(el('thead',{},el('tr',{},...['variável','Δ total','de choque','de deriva','nº de choques','% do |movimento|']
    .map(h=>el('th',{txt:h})))));
  const tc=el('tbody');
  DK.V7.forEach(v=>{const x=DK.DESLOCAMENTO[v];
    tc.append(el('tr',{},el('td',{txt:rot(v)}),el('td',{txt:nb(x.total)}),el('td',{txt:nb(x.choque)}),
      el('td',{txt:nb(x.deriva)}),el('td',{txt:String(x.n_choques)}),
      el('td',{txt:nb(x.p_choque_abs,1)+'%',style:x.p_choque_abs>=65?'color:#8A4FBF;font-weight:600':''})));});
  tb.append(tc); c3.append(tb);
  c3.append(el('div',{class:'prosa',style:'margin-top:10px;font-size:13px'},
    el('p',{html:`No vigor, <strong>${nb(DK.DESLOCAMENTO['Vigor'].p_choque_abs,1)}%</strong> do movimento está nas `+
      `transições de choque; na perturbação total, ${nb(DK.DESLOCAMENTO['TMD'].p_choque_abs,1)}%; na fadiga, `+
      `${nb(DK.DESLOCAMENTO['Fadiga'].p_choque_abs,1)}%. Na depressão, que não tem transição alguma acima do piso, a `+
      'totalidade do movimento é deriva. A semana move-se por eventos nas variáveis que se movem, e por deriva '+
      'naquela que quase não se move.'})));
  g2.append(c3); f.append(g2);
  return f;
};

TELAS.series=()=>{
  segTopo.hidden=false; segTopo.innerHTML='';
  const f=document.createDocumentFragment();
  const sec=SECSER[estadoS.sec]?estadoS.sec:'Filtro e ruído';
  Object.keys(SECSER).forEach(nome=>segTopo.append(el('button',{txt:nome,'aria-pressed':String(nome===sec),
    onclick:()=>{estadoS.sec=nome; render('series');}})));
  f.append(SECSER[sec]());
  return f;
};
