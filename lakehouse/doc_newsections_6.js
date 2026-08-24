// ====================== 6 MODELOS COMPLEMENTARES E ANÁLISE SEGMENTADA ======================
K.push(H1("6 Modelos complementares e análise segmentada"));
K.push(P("As seções anteriores estabeleceram a descrição, a triangulação e a robustez do achado central. Esta parte acrescenta cinco camadas de modelagem que refinam a leitura sem contradizê-la. A primeira examina se o efeito agudo depende do tipo de dia por meio de um modelo fatorial. A segunda descreve a dinâmica de um dia para o seguinte com um modelo autorregressivo de painel e com um modelo linear generalizado. A terceira audita a estrutura real das sessões de treino e normaliza a carga. A quarta repete a bateria dentro de cada estrato de estímulo. A quinta ajusta o humor pelo pico de velocidade e reúne as regressões. Todas as análises respeitam o mesmo desenho de grupo único, de modo que as leituras permanecem descritivas e de rastreio."));

// ---------- 6.1 Fatorial ----------
K.push(H2("6.1 Análise fatorial: momento e tipo de dia"));
K.push(P("Um modelo fatorial de dois fatores intra-sujeito pergunta se o efeito agudo do treino, medido do pré para o pós, depende do tipo de dia. O primeiro fator é o momento, com dois níveis, e o segundo é o tipo de dia, com três níveis, a saber, HIIT, jogo e força. Cabe uma ressalva de desenho: como o estudo é observacional, esta é uma análise fatorial de fatores observados, e não um experimento com alocação aleatória, razão pela qual o tipo de dia guarda confundimento com o dia e com a carga acumulada. A Figura 12 ilustra a interação para a perturbação total do humor, e a Tabela 19 resume os efeitos por dimensão."));
K.push(figCap("**Figura 12** – Interação Momento × Tipo de dia na perturbação total do humor. As linhas não paralelas sinalizam interação"));
K.push(figure("fig_fatorial.png", 520));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 19** – Análise fatorial Momento × Tipo de dia: tamanho de efeito (η²ₚ) por dimensão"));
(function(){
  var rm=d.fac.rm, MX={}; d.fac.mixed.forEach(function(x){MX[x.dim]=x;});
  var get=function(dim,fac){var r=rm.find(function(x){return x.dim===dim&&x.fator===fac;});return r||{};};
  var dims=d.fac.dims;
  var rows=dims.map(function(dm){
    var mo=get(dm.dim,"Momento (pré/pós)"),tp=get(dm.dim,"Tipo de dia"),it=get(dm.dim,"Momento × Tipo de dia"),mx=MX[dm.dim]||{};
    return [
      {t:dm.lab,bold:true,al:AL.L},
      {t:n(mo.eta2p,2)+(mo.sig?" *":""),al:AL.C,color:mo.sig?"1b7a3d":INK},
      {t:n(tp.eta2p,2)+(tp.sig?" *":""),al:AL.C,color:tp.sig?"1b7a3d":INK},
      {t:n(it.eta2p,2)+(it.sig?" *":""),al:AL.C,bold:it.sig,color:it.sig?"1b7a3d":INK},
      {t:(mx.p_interacao==null?"–":("p "+pf(mx.p_interacao)))+(mx.sig_interacao?" *":""),al:AL.C}
    ];
  });
  K.push(openTable([
    {t:"Dimensão",w:2505,al:AL.L},{t:"Momento",w:1750,al:AL.C},{t:"Tipo de dia",w:1750,al:AL.C},
    {t:"Interação",w:1750,al:AL.C},{t:"Misto p(int.)",w:1750,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: η²ₚ = eta quadrado parcial (rm-ANOVA, casos completos, n = " + d.fac.n_complete + "); p por correção de Greenhouse-Geisser; * indica p < 0,05. Última coluna: interação no modelo misto com os 27 atletas. " + FONTE_D));
K.push(P("O resultado desenha uma divisão nítida. O momento produz efeito forte e uniforme sobre o eixo físico, pois a fadiga física, a fadiga, o vigor e a perturbação total do humor pioram do pré para o pós de maneira semelhante em qualquer tipo de dia. Já a interação entre momento e tipo de dia concentra-se no eixo afetivo, uma vez que a depressão, a raiva e a perturbação do humor respondem de modo específico ao estímulo, com significância confirmada tanto na análise de casos completos quanto no modelo misto dos 27 atletas. Em síntese, o corpo paga um preço parecido em qualquer sessão, ao passo que o afeto reage conforme o tipo de dia, exatamente a leitura da triangulação, agora sob um único modelo."));

// ---------- 6.2 AR1 + GLM ----------
K.push(H2("6.2 Dinâmica de painel: persistência e razão de taxas"));
K.push(P("Dois modelos descrevem a dinâmica do estado ao longo dos dias. O primeiro é um autorregressivo de painel de defasagem um, com intercepto aleatório por atleta, cujo coeficiente mede a persistência, isto é, a fração do estado de um dia que se transfere para o dia seguinte. Convém registrar que, em painéis com poucas medidas no tempo, esse coeficiente tende a ser subestimado, razão pela qual a leitura vale pela ordem de grandeza. O segundo é um modelo linear generalizado de Poisson, ajustado por equações de estimação generalizadas com erros robustos por atleta, que trata as subescalas como contagens e informa a razão de taxas por tipo de dia e por momento. A Tabela 20 apresenta a persistência e a Tabela 21 as razões de taxas significativas."));
K.push(tblTitle("**Tabela 20** – Persistência de um dia para o seguinte (autorregressivo de painel, defasagem um)"));
(function(){
  var rows=d.dyn.ar1.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},{t:sgn(r.beta1),al:AL.C,bold:true},
    {t:"["+n(r.ic_lo,2)+"; "+n(r.ic_hi,2)+"]",al:AL.C},
    {t:"p "+pf(r.p),al:AL.C,color:r.sig?"1b7a3d":GREY},
    {t:r.icc==null?"–":n(r.icc,2),al:AL.C},{t:r.forca,al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2205,al:AL.L},{t:"β₁",w:1300,al:AL.C},{t:"IC 95%",w:2000,al:AL.C},
    {t:"p",w:1400,al:AL.C},{t:"ICC",w:1300,al:AL.C},{t:"Persistência",w:1300,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: β₁ = coeficiente de defasagem um; ICC = correlação intraclasse do intercepto aleatório. " + FONTE_D));
K.push(tblTitle("**Tabela 21** – Razão de taxas (IRR) do modelo linear generalizado de Poisson (efeitos significativos)"));
(function(){
  var rows=d.dyn.glm.filter(function(g){return g.sig;}).map(function(g){return [
    {t:g.dim_lab,bold:true,al:AL.L},{t:g.preditor,al:AL.L},
    {t:n(g.irr,2),al:AL.C,bold:true},{t:"["+n(g.ic_lo,2)+"; "+n(g.ic_hi,2)+"]",al:AL.C},
    {t:"p "+pf(g.p),al:AL.C,color:"1b7a3d"}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2005,al:AL.L},{t:"Preditor",w:2400,al:AL.L},{t:"IRR",w:1200,al:AL.C},
    {t:"IC 95%",w:2400,al:AL.C},{t:"p",w:1500,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: IRR = razão de taxas (referência: dia de jogo e momento pré); IRR acima de um indica taxa maior que a referência; erros-padrão robustos por atleta. " + FONTE_D));
K.push(P("Os dois modelos reforçam a estrutura de dois eixos. A persistência mais alta cabe à fadiga e à perturbação total do humor, o que traduz o acúmulo do cansaço de um dia para o outro e concorda com o efeito crônico já descrito. O vigor e as dimensões negativas reiniciam mais entre os dias, com persistência baixa. O modelo generalizado, por sua vez, mostra que o eixo afetivo responde de forma específica ao estímulo, pois o HIIT eleva a depressão, a raiva e a confusão em relação ao jogo, ao passo que o momento pós rebaixa o vigor e eleva a fadiga. Contagem, persistência e interação convergem para a mesma conclusão."));

// ---------- 6.3 Cargas segmentadas + dose ----------
K.push(H2("6.3 Segmentação das sessões e resposta à dose de carga"));
K.push(P("A auditoria da estrutura de treino corrigiu um ponto importante. O rótulo único por dia, tal como HIIT, jogo ou força, nomeia apenas a sessão definidora e colapsa os dias que reuniram mais de uma sessão em períodos diferentes. A Tabela 22 recompõe a estrutura real, confirmada na fonte, e informa a duração, a carga acumulada e a carga interna planejada por dia. A carga interna planejada seguiu o método da percepção de esforço da sessão, com o valor do HIIT ancorado no esforço percebido de fato medido e os demais tipos estimados por valores nominais ajustáveis, uma vez que o esforço percebido por sessão não foi coletado nas sessões técnicas, de força e de jogo."));
K.push(tblTitle("**Tabela 22** – Estrutura segmentada do microciclo e carga por dia"));
(function(){
  var rows=d.load.carga_raw.map(function(c){return [
    {t:"D"+c.dia,bold:true,al:AL.C},{t:c.data,al:AL.C},{t:String(c.n_sessoes),al:AL.C},
    {t:c.conteudo,al:AL.L},{t:n(c.horas,1)+" h",al:AL.C},{t:n(c.carga_acum_h,1)+" h",al:AL.C},
    {t:String(Math.round(c.srpe)),al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dia",w:705,al:AL.C},{t:"Data",w:1100,al:AL.C},{t:"Sessões",w:900,al:AL.C},
    {t:"Composição real",w:3400,al:AL.L},{t:"Horas",w:1000,al:AL.C},{t:"Acum.",w:1100,al:AL.C},{t:"sRPE",w:1300,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: composição confirmada na fonte; sRPE = carga interna planejada em unidades arbitrárias (duração × esforço percebido nominal); monotonia de Foster = " + n(d.load.monotonia,2) + "; strain = " + Math.round(d.load.strain) + ". " + FONTE_D));
K.push(P("Sobre essa base contínua, um modelo dose-resposta substitui o rótulo categórico por duas cargas interpretáveis, a saber, a carga aguda do próprio dia e a carga acumulada na semana, com intercepto aleatório por atleta. A Figura 13 e a Tabela 23 apresentam os coeficientes padronizados."));
K.push(figCap("**Figura 13** – Efeito da carga cumulativa sobre cada dimensão (coeficiente padronizado)"));
K.push(figure("fig_dose.png", 520));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 23** – Modelo dose-resposta: carga aguda e carga cumulativa por dimensão"));
(function(){
  var rows=d.dose.dose.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},
    {t:sgn(r.beta_agudo)+(r.sig_agudo?" *":""),al:AL.C,color:r.sig_agudo?"1b7a3d":INK},
    {t:sgn(r.beta_cum)+(r.sig_cum?" *":""),al:AL.C,bold:r.sig_cum,color:r.sig_cum?"1b7a3d":INK},
    {t:r.domina,al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2905,al:AL.L},{t:"β carga aguda",w:2200,al:AL.C},
    {t:"β carga cumulativa",w:2200,al:AL.C},{t:"Domina",w:2200,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: β = coeficiente padronizado por desvio padrão de carga; * indica p < 0,05. Validação: a qualidade total de recuperação cai quando a carga acumulada sobe (ρ de Spearman = " + n(d.dose.valid.rho_acum_tqr,2) + "). A razão aguda para crônica não foi calculada, pois a janela crônica de vinte e oito dias não cabe em sete dias. " + FONTE_D));
K.push(P("A leitura dose-resposta esclarece o mecanismo. O eixo físico e energético é governado pela carga cumulativa, pois o vigor cai e a fadiga e a perturbação do humor sobem à medida que a carga se acumula na semana, comportamento coerente com a persistência do modelo autorregressivo. O afeto, em contraste, responde mais ao componente agudo do dia. O ganho da segmentação está justamente nessa separação: em vez de tratar o dia como um rótulo, o modelo passa a ler o volume do dia e o acúmulo, o que distingue a carga aguda do custo crônico."));

// ---------- 6.4 Estratos ----------
K.push(H2("6.4 Análise estratificada: dias de HIIT e dias sem HIIT"));
K.push(P("A repetição da bateria dentro de cada estrato separa o que é próprio do HIIT do que é geral ao microciclo. O primeiro estrato reúne os três dias de HIIT e o segundo os quatro dias sem HIIT, e em cada um se compara o primeiro ao último dia com a mesma triangulação de três vias. A Figura 14 confronta os tamanhos de efeito e a Tabela 24 detalha a concordância entre as vias."));
K.push(figCap("**Figura 14** – Tamanho de efeito do primeiro ao último dia, por estrato de estímulo"));
K.push(figure("fig_estratos.png", 560));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 24** – Contraste primeiro para último dia por estrato, com triangulação de três vias"));
(function(){
  var tri=d.strata.tri, dims=d.strata.dims;
  var order=[]; dims.forEach(function(dm){ ["HIIT","SemHIIT"].forEach(function(es){ var r=tri.find(function(x){return x.dim===dm.dim&&x.estrato===es;}); if(r) order.push(r); }); });
  var rows=order.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},{t:r.estrato==="HIIT"?"HIIT":"sem HIIT",al:AL.C},
    {t:sgn(r.dz),al:AL.C,bold:true},{t:"["+n(r.ic[0],2)+"; "+n(r.ic[1],2)+"]",al:AL.C},
    {t:r.p_wilcoxon==null?"–":("p "+pf(r.p_wilcoxon)),al:AL.C},{t:"p "+pf(r.p_perm),al:AL.C},
    {t:r.concordam?"sim":"·",al:AL.C,bold:true,color:r.concordam?"1b7a3d":GREY}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:1905,al:AL.L},{t:"Estrato",w:1200,al:AL.C},{t:"dz",w:1000,al:AL.C},
    {t:"IC 95%",w:1800,al:AL.C},{t:"Wilcoxon",w:1300,al:AL.C},{t:"Permut.",w:1300,al:AL.C},{t:"3 vias",w:1000,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: dz positivo indica escore maior no último dia do estrato; IC 95% por bootstrap; três vias = concordância entre IC, Wilcoxon e permutação. " + FONTE_D));
K.push(P("A comparação revela o que muda ao isolar os estratos. O vigor cai nos dois grupos de dias, com confirmação das três vias, o que torna a queda de energia inespecífica ao estímulo. Já a subida da fadiga triangula apenas nos dias de HIIT, ao passo que nos dias sem HIIT permanece como tendência, o que reforça o HIIT como motor do eixo energia e fadiga. O afeto negativo não se altera do primeiro ao último dia dentro de nenhum estrato, coerente com a leitura de que o afeto separa tipos de dia, e não o curso ao longo deles. Quanto ao perfil dominante, os dias de HIIT concentram o perfil de superfície e os dias sem HIIT concentram o perfil iceberg."));

// ---------- 6.5 PV log + regressões ----------
K.push(H2("6.5 Ajuste pelo pico de velocidade e regressões"));
K.push(P("A última camada relaciona a aptidão aeróbia ao humor e reúne as regressões. O ajuste do humor pelo pico de velocidade do T-CAR foi conduzido em duas formas, a linear e a logarítmica, para verificar se a relação apresenta curvatura. A Tabela 25 confronta as duas. A regressão logística de duas caudas, por sua vez, testa quais marcadores discriminam o perfil de risco, e a Tabela 26 apresenta as razões de chance."));
K.push(tblTitle("**Tabela 25** – Ajuste do humor pelo pico de velocidade: linear versus logarítmico"));
(function(){
  var rows=d.strata.pv_log.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},{t:sgn(r.spearman),al:AL.C,bold:true},
    {t:n(r.r2_lin,2),al:AL.C},{t:n(r.r2_log,2),al:AL.C},{t:r.melhor,al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2505,al:AL.L},{t:"ρ (PV)",w:1600,al:AL.C},{t:"R² linear",w:1800,al:AL.C},
    {t:"R² log",w:1800,al:AL.C},{t:"Melhor",w:1800,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: ρ = correlação de Spearman entre pico de velocidade e humor (pares casados, n = 25); melhor = ajuste com menor critério de informação de Akaike. " + FONTE_D));
K.push(tblTitle("**Tabela 26** – Regressão logística de duas caudas: risco de perfil por marcador"));
(function(){
  var rows=d.strata.logit.map(function(r){return [
    {t:r.preditor,bold:true,al:AL.L},{t:n(r.OR,2),al:AL.C,bold:true},
    {t:"["+n(r.ic_lo,2)+"; "+n(r.ic_hi,2)+"]",al:AL.C},
    {t:"p "+pf(r.p),al:AL.C,color:r.sig?"1b7a3d":GREY}
  ];});
  K.push(openTable([
    {t:"Marcador",w:2905,al:AL.L},{t:"Razão de chance",w:1800,al:AL.C},
    {t:"IC 95%",w:2800,al:AL.C},{t:"p (bicaudal)",w:2000,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: razão de chance por desvio padrão do marcador; p de duas caudas; modelo com Epworth, PSS e fadiga padronizados. " + FONTE_D));
K.push(P("Os dois procedimentos fecham o quadro com coerência. O ajuste pelo pico de velocidade mostra-se essencialmente linear, uma vez que a forma logarítmica não melhora a explicação em nenhuma dimensão, e a relação mais forte confirma-se na fadiga física, que decresce de modo linear conforme a aptidão aeróbia aumenta. A regressão logística, por seu turno, aponta a fadiga como o marcador que discrimina o perfil de risco, ao passo que a sonolência e o estresse percebido não distinguem os grupos. O conjunto reitera a mensagem que atravessa todo o estudo: o sinal reside no eixo da energia e da fadiga, tanto para dosar a carga quanto para sinalizar o risco."));

