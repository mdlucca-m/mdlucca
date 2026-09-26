/* ===================================================================
   SLIDES AVANÇADOS 3D - LAPE
   Gráficos 3D, animações n8n-style, indicador de ponto em tempo real
   Para modo painel 4K com efeitos profissionais
   =================================================================== */
"use strict";

/* Duração de uma sessão de ponto aberta, em horas fracionárias (vem de
   ponto.agora() no servidor) -- "há 45min" para quem acabou de bater
   entrada, "há 2h30" para quem já está há um tempo. */
function porHoras(horas) {
  if (horas === null || horas === undefined || !isFinite(horas)) return "pouco tempo";
  const totalMin = Math.round(horas * 60);
  if (totalMin < 1) return "menos de 1 min";
  if (totalMin < 60) return totalMin + " min";
  const h = Math.floor(totalMin / 60), m = totalMin % 60;
  return h + "h" + (m ? String(m).padStart(2, "0") : "");
}

/* el() (de Charts.el) cria elementos com document.createElement -- serve
   para HTML, mas não para SVG: sem o namespace certo, <circle>/<path>/
   <text> viram elementos HTML desconhecidos, sem geometria nenhuma (o
   navegador ignora cx/cy/r/d e faz o texto fluir em linha, um atrás do
   outro). Foi exatamente isso que quebrava o grafo de linhas de
   pesquisa: os rótulos apareciam todos amontoados numa linha só, e os
   nós/conexões não apareciam de jeito nenhum. */
const SVG_NS = "http://www.w3.org/2000/svg";
function elSvg(tag, attrs, kids) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const k in (attrs || {})) {
    const v = attrs[k];
    if (v === null || v === undefined || v === false) continue;
    node.setAttribute(k, v);
  }
  (Array.isArray(kids) ? kids : (kids === undefined || kids === null ? [] : [kids]))
    .forEach(function (kid) {
      if (kid === null || kid === undefined || kid === false) return;
      node.appendChild(typeof kid === "object" ? kid : document.createTextNode(String(kid)));
    });
  return node;
}

/* Distância de um planeta ao centro: mais impacto (artigos + citações,
   os dois eixos que a própria lâmina já mostra em cada nó), órbita mais
   fechada -- o mesmo raciocínio "gravitacional" que já fazia o nó em si
   crescer com `n_artigos`, aqui aplicado à distância também, reforçando
   a mesma leitura em vez de competir com ela. Fora como função pura,
   testável sem montar o SVG inteiro. */
function raioOrbitaLinha(linha, maiorImpacto, raioMin, raioMax) {
  const impacto = (linha.artigos || 0) + (linha.citacoes || 0);
  const fracao = Math.max(0, Math.min(1, impacto / Math.max(1, maiorImpacto)));
  return raioMin + (raioMax - raioMin) * (1 - fracao);
}

/* ==================== LINHAS DE PESQUISA 3D ==================== */
/* Nome da linha em até 2 linhas, quebrado por PALAVRA (nunca cortado no
   meio) -- "Psicologia do exercício e saúde mental" virando "Psicologia
   do exerc…" na parede era exatamente o "pouca informação" que o
   laboratório reclamou: o dado mais básico do nó (seu próprio nome) nem
   dava para ler. Uma palavra sozinha maior que o limite ainda usa `cortar`
   como último recurso, para não estourar o nó. */
function quebrarEmDuasLinhas(texto, maxPorLinha) {
  const nome = String(texto || "").trim();
  if (nome.length <= maxPorLinha) return [nome, ""];
  const palavras = nome.split(" ");
  // Quebra pela PALAVRA mais perto do meio do texto (a que mais equilibra
  // o tamanho das duas linhas) -- não "enche a linha 1 até o limite e o
  // resto vai para a linha 2": um corte guloso deixava a linha 2 com o
  // restante inteiro, que às vezes estourava o MESMO limite do outro
  // lado e caía no `cortar` de qualquer jeito (voltando ao problema
  // original: nome cortado no meio, com "…").
  let melhorIdx = 1, melhorDelta = Infinity;
  for (let i = 1; i < palavras.length; i++) {
    const delta = Math.abs(palavras.slice(0, i).join(" ").length - palavras.slice(i).join(" ").length);
    if (delta < melhorDelta) { melhorDelta = delta; melhorIdx = i; }
  }
  const linha1 = palavras.slice(0, melhorIdx).join(" ");
  let linha2 = palavras.slice(melhorIdx).join(" ");
  // Só corta em último caso -- um nome tão comprido que nem um split
  // equilibrado cabe em linhas razoáveis (raríssimo, mas não pode
  // quebrar a lâmina se acontecer).
  const capMax = Math.round(maxPorLinha * 1.6);
  if (linha2.length > capMax) linha2 = cortar(linha2, capMax);
  return [linha1, linha2];
}

function slidePesquisasLinhas3D() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Linhas de pesquisa ainda não carregadas.")));

  const todasLinhas = t.linhas || [];
  if (!todasLinhas.length) return escalonar(el("div", { class: "slide" }, vazio("Nenhuma linha de pesquisa cadastrada.")));

  /* O grafo mostra só quem TEM produção -- metade das linhas cadastradas
     costuma estar em 0 artigo ainda, e um nó do mesmo tamanho/cor para
     "0 artigos" e para "45 artigos" era exatamente o "gráfico pobre e
     desorganizado" apontado: a atenção se diluía entre nós que não
     diziam nada. As linhas sem produção continuam listadas (nunca
     escondidas), só não competem por espaço no grafo -- mesmo raciocínio
     já usado na lâmina de citações (ver `slideCitacoesBases`). */
  const linhas = todasLinhas.filter((l) => (l.artigos || 0) > 0);
  const semProducao = todasLinhas.filter((l) => !((l.artigos || 0) > 0));

  const container = el("div", { class: "slide slide-pesquisas-3d moldura-viva" });

  const svg = elSvg("svg", {
    class: "grafo-linhas-3d",
    viewBox: "0 0 1200 800",
    style: "width:100%;height:100%;position:relative;",
  });

  /* Um único filtro de glow, compartilhado por todos os nós -- antes cada
     nó apontava para "glow-linha-{idx}", mas só o filtro do idx 0 era de
     fato criado; todo nó com idx >= 1 referenciava um id inexistente. */
  const glowId = "glow-linha-pesquisa";
  const defs = elSvg("defs");
  const filtroGlow = elSvg("filter", { id: glowId, x: "-50%", y: "-50%", width: "200%", height: "200%" });
  filtroGlow.appendChild(elSvg("feGaussianBlur", { "in": "SourceGraphic", stdDeviation: "5" }));
  defs.appendChild(filtroGlow);
  svg.appendChild(defs);

  const centerX = 600, centerY = 400;
  /* O raio MÁXIMO cresce com o número de linhas cadastradas -- fixo em
     200px, o espaçamento angular entre nós encolhia conforme mais linhas
     de pesquisa eram criadas, até os rótulos se sobreporem. Limitado a
     300 para não estourar o viewBox (o centro está a 400px da borda). */
  const raioMax = Math.min(300, Math.max(160, 26 * linhas.length));
  /* A distância de cada planeta ao centro é o que faltava para bater com
     o pedido original ("planetas orbitando em distâncias controladas
     pelo volume de impacto"): antes só o ÂNGULO variava, todo nó no
     mesmo raio fixo. Impacto = artigos + citações -- os dois eixos que a
     tela já mostra em cada nó (badge de artigos, sub-rótulo de citações),
     então a órbita não inventa um critério novo, só desenha o que os
     números já diziam. Mais impacto, órbita mais fechada: o mesmo
     raciocínio "gravitacional" que já fazia o nó em si crescer com
     `n_artigos` -- aqui os dois reforçam a mesma leitura (quem lidera é
     maior E mais central), em vez de competir. */
  const raioMin = raioMax * 0.45;
  const maiorImpacto = Math.max(1, ...linhas.map((l) => (l.artigos || 0) + (l.citacoes || 0)));
  /* Fonte do rótulo também encolhe com muitos nós, para caber no espaço
     angular menor entre eles -- e cresce quando sobram poucos nós (o caso
     mais comum agora que os de produção zero saem do grafo), porque
     "de longe" pequeno é sempre pequeno demais. */
  const fontLabel = linhas.length > 12 ? 9 : linhas.length > 8 ? 10 : linhas.length > 5 ? 12 : 13;
  const maxCharsLabel = linhas.length > 8 ? 14 : linhas.length > 5 ? 18 : 22;
  /* A atividade de cada linha é relativa às outras -- sem isso, "quem
     lidera" nunca aparece: com uma linha só, ela sempre pareceria "no
     máximo". As partículas e o ritmo do pulso vêm desta razão. */
  const maiorArtigos = Math.max(1, ...linhas.map((l) => l.artigos || 0));

  /* Uma trilha pontilhada por raio distinto -- não um raio só: com órbita
     variável, cada anel de verdade merece sua própria faixa, senão a
     "leitura de órbita" (mesmo parada) mentiria mostrando um raio que
     nenhum planeta usa. */
  const raiosUsados = new Set();
  linhas.forEach((linha) => {
    const raio = Math.round(raioOrbitaLinha(linha, maiorImpacto, raioMin, raioMax));
    if (raiosUsados.has(raio)) return;
    raiosUsados.add(raio);
    svg.appendChild(elSvg("circle", {
      cx: centerX, cy: centerY, r: raio, class: "trilha-orbita",
      fill: "none", "stroke-dasharray": "2 10",
    }));
  });

  /* Todo o anel (raios + nós) gira em torno do centro -- antes só o hub
     central tinha `rotacao-3d`; o resto do grafo ficava parado. Cada nó
     mora dentro de um `<g>` próprio que gira na direção oposta, à mesma
     velocidade, em torno do seu PRÓPRIO ponto (não do centro) -- assim a
     posição orbita, mas o rótulo/ícone/badges continuam de pé, legíveis. */
  const anel = elSvg("g", { class: "anel-orbita" });
  const particulas = [];

  linhas.forEach((linha, idx) => {
    const angle = (idx / linhas.length) * Math.PI * 2;
    const radiusDoNo = raioOrbitaLinha(linha, maiorImpacto, raioMin, raioMax);
    const x = centerX + radiusDoNo * Math.cos(angle);
    const y = centerY + radiusDoNo * Math.sin(angle);
    const n_artigos = linha.artigos || 0;
    const taxa_pub = linha.taxa_publicacao || 0;
    const atividade = n_artigos / maiorArtigos;

    const nodeRadius = Math.max(20, Math.min(60, 20 + (n_artigos / 5)));
    /* Cor por IDENTIDADE da linha (categórica, uma por linha, igual ao
       resto do mural -- ver .cartao-pessoa/.fatia-hexagono), não mais
       por taxa de publicação: com só 3 cores por faixa, linhas
       diferentes na mesma faixa ficavam indistinguíveis no grafo. A taxa
       de publicação continua visível, mas como número (badgeTaxa
       abaixo), sua própria informação. */
    const corLinha = `var(--series-${(idx % 8) + 1})`;
    const corTaxa = taxa_pub > 0.8 ? "var(--good)" : taxa_pub > 0.5 ? "var(--warning)" : "var(--critical)";
    const nomeIcone = (typeof Icons !== "undefined" && Icons.tematico) ? Icons.tematico(linha.nome) : null;

    /* Linha do centro até o nó (Bezier com animação) */
    const caminho = `M ${centerX} ${centerY} Q ${(centerX + x) / 2} ${(centerY + y) / 2} ${x} ${y}`;
    const line = elSvg("path", {
      d: caminho,
      class: "conexao-linha-pesquisa",
      style: `--index:${idx};--total:${linhas.length};`,
      stroke: corLinha,
      "stroke-width": "2",
      fill: "none",
      "stroke-dasharray": "400",
      "stroke-dashoffset": "400",
      "vector-effect": "non-scaling-stroke",
    });
    anel.appendChild(line);

    /* Partículas correndo do centro até o nó: mais partículas, e mais
       rápidas, para quem lidera em artigos -- o fluxo mostra pra onde a
       produção está indo, não só quem já chegou lá. `begin` escalonado
       espaça as partículas de uma mesma linha ao longo do trajeto, em
       vez de nascerem todas grudadas. */
    const qtdParticulas = 1 + Math.round(atividade * 2);
    const duracao = 3.2 - atividade * 1.8;
    for (let p = 0; p < qtdParticulas; p++) {
      const particula = elSvg("circle", {
        r: "3.5", class: "particula-fluxo", fill: corLinha,
        filter: `url(#${glowId})`,
      });
      const motion = elSvg("animateMotion", {
        path: caminho, dur: duracao.toFixed(2) + "s",
        begin: (p * (duracao / qtdParticulas)).toFixed(2) + "s",
        repeatCount: "indefinite", rotate: "auto",
      });
      particula.appendChild(motion);
      particulas.push(particula);
    }

    const publicados = linha.publicados || 0;
    const citacoes = linha.citacoes || 0;

    /* Grupo do nó: gira ao contrário do anel, em torno do seu próprio
       centro (x,y), para orbitar sem virar de cabeça pra baixo.
       `data-linha`/`data-citacoes-atual`/`data-x`/`data-y` são o gancho
       para `atualizarConstelacaoAoVivo` (mural.js) comparar, a cada
       nova busca de /api/tv, se a citação daquela linha subiu -- e
       disparar a micro-explosão nesse ponto exato, sem recalcular nada
       aqui de novo. */
    const grupoNo = elSvg("g", {
      class: "grupo-no-orbita",
      style: `--index:${idx};transform-origin:${x.toFixed(1)}px ${y.toFixed(1)}px;`,
      "data-linha": linha.nome, "data-citacoes-atual": String(citacoes),
      "data-x": x.toFixed(1), "data-y": y.toFixed(1), "data-cor": corLinha,
    });
    const titulo = elSvg("title");
    titulo.textContent = `${linha.nome} — ${n_artigos} artigo${n_artigos === 1 ? "" : "s"}, `
      + `${publicados} publicado${publicados === 1 ? "" : "s"} (${Math.round(taxa_pub * 100)}%), `
      + `${citacoes} citaç${citacoes === 1 ? "ão" : "ões"}`;
    grupoNo.appendChild(titulo);

    /* Nó central (círculo com glow) */
    const circle = elSvg("circle", {
      cx: x,
      cy: y,
      r: nodeRadius,
      class: "nodo-linha-pesquisa",
      style: `--index:${idx};--radius:${nodeRadius};--cor:${corLinha};`
        + `--pulso-duracao:${(2.6 - atividade * 1).toFixed(2)}s;`,
      fill: "currentColor",
      filter: `url(#${glowId})`,
      opacity: "0.85",
    });
    circle.addEventListener("mouseenter", function () {
      this.style.opacity = "1";
      this.style.r = nodeRadius + 10;
    });
    circle.addEventListener("mouseleave", function () {
      this.style.opacity = "0.85";
      this.style.r = nodeRadius;
    });
    grupoNo.appendChild(circle);

    /* Ícone temático da área, centrado dentro do nó -- em branco, para
       destacar sobre a cor própria da linha. */
    if (nomeIcone && typeof Icons !== "undefined" && Icons.get) {
      const iconSize = Math.max(16, Math.min(30, nodeRadius * 0.75));
      const icone = Icons.get(nomeIcone, iconSize);
      icone.setAttribute("x", (x - iconSize / 2).toFixed(1));
      icone.setAttribute("y", (y - iconSize / 2).toFixed(1));
      icone.style.color = "#fff";
      icone.style.pointerEvents = "none";
      icone.setAttribute("filter", "drop-shadow(0 1px 2px rgba(0,0,0,.45))");
      grupoNo.appendChild(icone);
    }

    /* Label do nó, em até 2 linhas -- nunca mais "Psicologia do exerc…" */
    const [nomeLinha1, nomeLinha2] = quebrarEmDuasLinhas(linha.nome, maxCharsLabel);
    const alturaLinha = fontLabel + 3;
    const yLabel = y + nodeRadius + 22;
    const label = elSvg("text", {
      x: x,
      y: yLabel,
      class: "label-linha-pesquisa",
      "text-anchor": "middle",
      fill: "currentColor",
      "font-size": fontLabel + "px",
      "font-weight": "600",
      style: `--index:${idx};`,
    });
    label.appendChild(elSvg("tspan", { x: x, dy: "0" }, nomeLinha1));
    if (nomeLinha2) label.appendChild(elSvg("tspan", { x: x, dy: alturaLinha + "px" }, nomeLinha2));
    grupoNo.appendChild(label);

    /* Citações totais da linha, uma informação nova sob o nome -- só
       aparece quando há alguma (mesma lógica de "não decorar com zero"
       da lâmina de citações: um "0 citações" embaixo de toda linha só
       teria virado ruído visual, não informação). */
    if (citacoes > 0) {
      const linhasDeTexto = nomeLinha2 ? 2 : 1;
      const subLabel = elSvg("text", {
        x: x,
        y: yLabel + linhasDeTexto * alturaLinha + 2,
        class: "label-citacoes-linha",
        "text-anchor": "middle",
        "font-size": Math.max(8, fontLabel - 2) + "px",
        "font-weight": "600",
      });
      subLabel.textContent = fmt(citacoes) + (citacoes === 1 ? " citação" : " citações");
      grupoNo.appendChild(subLabel);
    }

    /* Badge com número de artigos (identidade da linha) */
    const badge = elSvg("text", {
      x: x + nodeRadius + 5,
      y: y - nodeRadius - 5,
      class: "badge-artigos",
      fill: corLinha,
      "font-size": "13px",
      "font-weight": "700",
      "dominant-baseline": "middle",
    });
    badge.textContent = n_artigos;
    grupoNo.appendChild(badge);

    /* Badge com a taxa de publicação, do outro lado -- antes essa
       informação só existia implícita na cor do nó; agora é um número
       lido direto, com sua própria cor de status (bom/alerta/crítico). */
    const badgeTaxa = elSvg("text", {
      x: x - nodeRadius - 5,
      y: y - nodeRadius - 5,
      class: "badge-taxa",
      fill: corTaxa,
      "font-size": "11px",
      "font-weight": "700",
      "text-anchor": "end",
      "dominant-baseline": "middle",
    });
    badgeTaxa.textContent = Math.round(taxa_pub * 100) + "%";
    grupoNo.appendChild(badgeTaxa);

    anel.appendChild(grupoNo);
  });

  /* As partículas entram por cima de todas as linhas e nós -- por
     último no documento, para não ficarem escondidas atrás deles. */
  particulas.forEach((p) => anel.appendChild(p));
  svg.appendChild(anel);

  /* Centro: nó principal girando (fica de fora do anel -- já gira por
     conta própria, e sua etiqueta "LAPE" precisa continuar de pé). */
  const centerCircle = elSvg("circle", {
    cx: centerX,
    cy: centerY,
    r: "40",
    class: "centro-rotacao-3d",
    fill: "url(#gradCentro)",
    "filter": "drop-shadow(0 0 12px currentColor)",
  });
  const gradCentro = elSvg("radialGradient", { id: "gradCentro" });
  gradCentro.appendChild(elSvg("stop", { offset: "0%", "stop-color": "var(--accent)" }));
  gradCentro.appendChild(elSvg("stop", { offset: "100%", "stop-color": "var(--accent-strong)" }));
  defs.appendChild(gradCentro);
  svg.appendChild(centerCircle);

  /* Rótulo central */
  const centrLabel = elSvg("text", {
    x: centerX,
    y: centerY,
    class: "label-centro",
    "text-anchor": "middle",
    "dominant-baseline": "middle",
    fill: "white",
    "font-size": "14px",
    "font-weight": "700",
  });
  centrLabel.textContent = "LAPE";
  svg.appendChild(centrLabel);

  container.appendChild(svg);

  /* Linhas sem produção ainda: uma frase, não um nó vazio no grafo -- a
     mesma resolução usada na lâmina de citações (ver `slideCitacoesBases`)
     para o mesmo problema: metade das linhas sem nenhum dado ainda não
     pode consumir a mesma atenção visual das que já produzem. */
  if (semProducao.length) {
    container.appendChild(el("p", { class: "linhas-pesquisa-vazias" }, [
      el("b", { text: semProducao.length + " linha(s) sem produção registrada ainda: " }),
      el("span", { text: semProducao.map((l) => l.nome).join(" · ") }),
    ]));
  }

  const totalCitacoes = todasLinhas.reduce((a, b) => a + (b.citacoes || 0), 0);
  const info = el("div", { class: "info-linhas-3d" }, [
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Linhas ativas:" }),
      el("span", { class: "info-value", text: String(todasLinhas.length) }),
    ]),
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Total de artigos:" }),
      el("span", { class: "info-value", text: String(todasLinhas.reduce((a, b) => a + (b.artigos || 0), 0)) }),
    ]),
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Taxa média:" }),
      el("span", { class: "info-value", text: fmt(todasLinhas.reduce((a, b) => a + (b.taxa_publicacao || 0), 0) / Math.max(1, todasLinhas.length) * 100) + "%" }),
    ]),
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Citações totais:" }),
      el("span", { class: "info-value", text: fmt(totalCitacoes) }),
    ]),
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Linha líder:" }),
      el("span", { class: "info-value", text: cortar(todasLinhas.reduce((a, b) => (b.artigos || 0) > (a.artigos || 0) ? b : a, todasLinhas[0]).nome, 26) }),
    ]),
  ]);

  container.appendChild(info);

  return escalonar(container);
}

/* ==================== IMPACTO x ESFORÇO DAS LINHAS DE PESQUISA ==================== */
/* O corte que separa "alto" de "baixo" em cada eixo -- a MEDIANA das
   próprias linhas plotadas, nunca um número fixo cravado no código: uma
   mediana chumbada quando o laboratório tinha 5 linhas nunca
   acompanharia o dia em que tivesse 20. Fora como função pura para poder
   testar a matemática sem montar a lâmina inteira. */
function medianaDe(valores) {
  const s = [...valores].sort((a, b) => a - b), m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/* Pedido explícito (referência de matriz 2x2): cada linha de pesquisa
   como um ponto, impacto (citações por artigo -- o quanto o que sai
   dali costuma repercutir, não o total bruto que só premia quem é
   antigo) no eixo vertical, esforço (artigos em produção AGORA, ver
   `_linhas_pesquisa` em tv.py) no eixo horizontal. Os quatro quadrantes
   nascem do corte pela mediana (`medianaDe`) das próprias linhas. */
function slideImpactoEsforco() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Linhas de pesquisa ainda não carregadas.")));

  const todasLinhas = t.linhas || [];
  /* Impacto por artigo só existe para quem já publicou algo -- dividir
     por zero linha sem nenhum artigo inventaria um ponto no meio do
     nada. A mesma regra de sempre: sem dado, fora do gráfico, nunca um
     zero forçado. */
  const linhas = todasLinhas
    .filter((l) => (l.artigos || 0) > 0)
    .map((l) => ({ ...l, impacto: (l.citacoes || 0) / l.artigos }));
  if (linhas.length < 2) {
    return escalonar(el("div", { class: "slide" },
      vazio("Poucas linhas com produção para comparar impacto x esforço ainda.")));
  }

  const medianaImpacto = medianaDe(linhas.map((l) => l.impacto));
  const medianaEsforco = medianaDe(linhas.map((l) => l.em_producao || 0));
  const maiorImpacto = Math.max(medianaImpacto * 2, ...linhas.map((l) => l.impacto), 1);
  const maiorEsforco = Math.max(medianaEsforco * 2, ...linhas.map((l) => l.em_producao || 0), 1);

  const container = el("div", { class: "slide slide-impacto-esforco moldura-viva" });
  const w = 720, h = 560, m = 56;
  const x0 = m, x1 = w - m, y0 = m, y1 = h - m;
  const xDe = (esforco) => x0 + (esforco / maiorEsforco) * (x1 - x0);
  const yDe = (impacto) => y1 - (impacto / maiorImpacto) * (y1 - y0);
  const xMediana = xDe(medianaEsforco), yMediana = yDe(medianaImpacto);

  const svg = elSvg("svg", { viewBox: `0 0 ${w} ${h}`, class: "plot impacto-esforco" });

  /* Os quatro quadrantes, cada um com a própria cor e legenda -- a
     mesma leitura da referência ("priorize isso" / "esqueça disso"),
     adaptada para linha de pesquisa em vez de projeto genérico. */
  const QUADRANTES = [
    { x: x0, y: y0, xf: xMediana, yf: yMediana, tom: "azul", legenda: "Priorize" },
    { x: xMediana, y: y0, xf: x1, yf: yMediana, tom: "bom", legenda: "Grande aposta" },
    { x: x0, y: yMediana, xf: xMediana, yf: y1, tom: "ambar", legenda: "Efeito marginal" },
    { x: xMediana, y: yMediana, xf: x1, yf: y1, tom: "alerta", legenda: "Reavalie" },
  ];
  QUADRANTES.forEach(function (q) {
    svg.appendChild(elSvg("rect", {
      x: q.x, y: q.y, width: q.xf - q.x, height: q.yf - q.y,
      class: "quadrante-fundo", "data-tom": q.tom,
    }));
    const cxq = (q.x + q.xf) / 2, cyq = q.y < yMediana ? q.y + 20 : q.yf - 12;
    svg.appendChild(elSvg("text", { x: cxq, y: cyq, "text-anchor": "middle",
      class: "quadrante-legenda", "data-tom": q.tom }, q.legenda));
  });

  // Eixos e linhas de mediana (tracejadas: são um corte estatístico, não
  // uma fronteira física como o contorno do plano).
  svg.appendChild(elSvg("line", { x1: xMediana, y1: y0, x2: xMediana, y2: y1, class: "linha-mediana" }));
  svg.appendChild(elSvg("line", { x1: x0, y1: yMediana, x2: x1, y2: yMediana, class: "linha-mediana" }));
  svg.appendChild(elSvg("rect", { x: x0, y: y0, width: x1 - x0, height: y1 - y0, class: "moldura-plano", fill: "none" }));
  svg.appendChild(elSvg("text", { x: (x0 + x1) / 2, y: h - 16, "text-anchor": "middle", class: "eixo-rotulo" },
    "Esforço agora (artigos em produção) →"));
  svg.appendChild(elSvg("text", { x: 18, y: (y0 + y1) / 2, "text-anchor": "middle", class: "eixo-rotulo",
    transform: `rotate(-90 18 ${(y0 + y1) / 2})` }, "↑ Impacto (citações por artigo)"));

  const raio = (l) => 6 + 10 * Math.sqrt((l.artigos || 0) / Math.max(1, ...linhas.map((x) => x.artigos || 0)));
  linhas.forEach(function (l) {
    const px = xDe(l.em_producao || 0), py = yDe(l.impacto);
    const ponto = elSvg("circle", { cx: px, cy: py, r: raio(l), class: "ponto-impacto-esforco" });
    ponto.appendChild(elSvg("title", {},
      `${l.nome}: ${fmt(Math.round(l.impacto * 10) / 10)} citações/artigo, `
      + `${l.em_producao || 0} em produção agora`));
    svg.appendChild(ponto);
    svg.appendChild(elSvg("text", { x: px, y: py - raio(l) - 6, "text-anchor": "middle",
      class: "rotulo-impacto-esforco" }, cortar(l.nome, 20)));
  });

  container.appendChild(el("div", { class: "impacto-esforco-caixa" }, [(function () {
    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");
    fig.appendChild(svg);
    return fig;
  })()]));

  return escalonar(container);
}

/* ==================== ORGANOGRAMA COM INDICADOR DE PONTO ==================== */
/* Ícone e tom temáticos por vínculo -- os 11 códigos que a coordenação usa
   (ver mapping.VINCULOS), mais o que não tem vínculo declarado. A mesma
   paleta de Icons.badge() pinta também o contorno do cartão. */
const VINCULOS_ICONE = {
  coordenacao: ["trofeu", "ambar"],
  professor: ["livro", "violeta"],
  pos_doutorado: ["achado", "magenta"],
  doutorando: ["tese", "azul"],
  mestrando: ["tese", "verde"],
  bolsista_ic: ["experimento", "laranja"],
  bolsista_extensao: ["projeto", "laranja"],
  voluntario: ["pessoas", "bom"],
  graduando: ["linha", "azul"],
  tecnico: ["qualidade", "verde"],
  colaborador: ["instituicao", "alerta"],
  sem_vinculo: ["pessoas", "azul"],
};

/* O organograma inteiro num slide só, com dez ou mais orientandos da
   coordenação, não cabia: virava fileira sem quebra de linha, cortada nas
   pontas. A resposta não é encolher o cartão -- de longe, pequeno não
   existe --, é separar em mais telas, cada uma com sua hierarquia
   horizontal de verdade (a linha que liga quem orienta a quem, sem
   agrupar em grade). Cada pessoa mora num balde só: o do PRIMEIRO cujo
   vínculo bate com o dela, ela ou algum ancestral dela -- é assim que a
   bolsista orientada por um mestrando aparece junto DELE, no balde da
   pós-graduação, em vez de solta no balde de bolsistas sem ninguém
   embaixo dela ali. */
const BALDES_ORGANOGRAMA = [
  { titulo: "Coordenação e Docentes", vinculos: ["coordenacao", "professor", "pos_doutorado"] },
  { titulo: "Pós-graduação", vinculos: ["doutorando", "mestrando"] },
  // ultimo balde: null vira "o que nao coube em nenhum dos de cima" --
  // ninguem some por causa de um codigo de vinculo novo que os baldes
  // acima nao previram.
  { titulo: "Bolsistas e Demais", vinculos: null },
];

function baldeDoRole(role) {
  const r = role || "sem_vinculo";
  for (let i = 0; i < BALDES_ORGANOGRAMA.length; i++) {
    const v = BALDES_ORGANOGRAMA[i].vinculos;
    if (v && v.indexOf(r) !== -1) return i;
  }
  return BALDES_ORGANOGRAMA.length - 1;
}

/* Quem TEM orientador/coorientador (uma aresta chegando, de alguém que
   também está na lista) nunca pode ser tratado como raiz solta -- só
   aparece como galho de quem a orienta. Sem isto, uma pessoa cuja
   orientadora está mais adiante em `pessoas` (a lista não vem ordenada
   por hierarquia) virava raiz por conta própria E, quando a orientadora
   enfim era processada, sua subárvore desenhava essa mesma pessoa DE NOVO
   como galho -- o mesmo cartão duplicado na tela, com toda a subárvore
   dela junto. Pego ao vivo com Playwright, não em teste: "Camila Deodoro
   Vasques" aparecia como raiz solta E como galho de "Marina Rossetto
   Cardoso", sua orientadora de verdade -- e os orientandos de Camila
   vinham triplicados atrás dela. */
function temOrientadorVisivel(pessoas, edges) {
  const porId = {};
  (pessoas || []).forEach(function (p) { porId[p.id] = p; });
  const resultado = new Set();
  (edges || []).forEach(function (e) {
    if (e.kind !== "orientacao" && e.kind !== "coorientacao") return;
    if (!porId[e.from] || !porId[e.to]) return;
    resultado.add(e.to);
  });
  return resultado;
}

/* Antes a cor do cartão vinha do VÍNCULO (professor violeta, bolsista
   laranja...) -- e cada geração da árvore saía com um mosaico de cores
   soltas, sem nada dizendo "isto é uma hierarquia". Referências que o
   Mateus mandou (prints de organogramas de verdade) concordam num ponto:
   a cor marca o NÍVEL da árvore -- raiz, depois cada geração abaixo --
   e é isso que faz a hierarquia se ler de longe, antes mesmo de ler um
   nome. O ícone continua vindo do vínculo (`VINCULOS_ICONE`); só a cor
   do cartão passou a vir da profundidade. */
const NIVEL_COR = ["violeta", "laranja", "bom", "azul"];

/* O cartão de uma pessoa na árvore -- compartilhado pelas duas lâminas
   (`slideOrganograma3D` e `slideOrganogramaMetodologico`) que antes
   reescreviam a mesma função lado a lado. Achado ao vivo: o desenho
   anterior (cantos de HUD, halo pulsante, entrada saltitante) competia
   com a informação em vez de organizá-la -- "não dá para ver nada
   direito" era, em boa parte, isso. O cartão agora é só borda, ícone,
   nome e vínculo -- a cor de nível já diz "onde" a pessoa está na
   árvore, sem precisar de brilho. */
function cartaoPessoa(p, profundidade) {
  const [icone] = VINCULOS_ICONE[p.role || "sem_vinculo"] || VINCULOS_ICONE.sem_vinculo;
  const tom = NIVEL_COR[(profundidade || 0) % NIVEL_COR.length];
  const ativo = p.ativo_agora ? "ativo" : "inativo";
  const cartao = el("div", { class: `cartao-pessoa ${ativo}`, "data-tom": tom, "data-id": p.id });

  cartao.appendChild(Icons.badge(icone, tom, 30));

  const statusBolinha = el("div", { class: `status-bolinha ${ativo}` });
  if (p.ativo_agora) statusBolinha.classList.add("pulsante");
  cartao.appendChild(statusBolinha);

  cartao.appendChild(el("div", { class: "nome-pessoa", text: cortar(p.full_name, 25) }));
  cartao.appendChild(el("div", { class: "vinculo-pessoa", text: p.role_label }));

  if (p.ativo_agora && p.ha_horas !== null && p.ha_horas !== undefined) {
    cartao.appendChild(el("div", { class: "desde-pessoa", text: "há " + porHoras(p.ha_horas) }));
  }

  const nArtigos = p.n_articles || 0;
  cartao.appendChild(el("div", { class: "badge-artigos", text: nArtigos }));
  if (p.orientandos) {
    cartao.appendChild(el("div", { class: "badge-orientandos", title: p.orientandos + " orientando(s)" },
      [el("span", { text: "↳ " + p.orientandos })]));
  }

  const linhaPonto = p.ativo_agora
    ? "presente há " + porHoras(p.ha_horas) + (p.atividade ? " -- " + p.atividade : "")
    : "ausente agora";
  cartao.title = `${p.full_name}\n${p.role_label}\n${nArtigos} artigo(s)\n${linhaPonto}`;
  return cartao;
}

/* A árvore de verdade, vertical com uma coluna por ramo -- pedido
   explícito (referência de organograma com colunas). A raiz fica em
   cima; cada filho DIRETO da raiz vira o topo da própria coluna, lado a
   lado com as dos irmãos (fan-out horizontal, o conector clássico de
   sempre). A partir da SEGUNDA geração, os descendentes não ramificam
   de novo -- empilham retos na mesma coluna do próprio ramo.

   Achado ao vivo, motivo da mudança: o fan-out horizontal se repetindo
   a cada geração (uma coluna de colunas de colunas) é exatamente o que
   quebrava com dado real -- muitos netos por ramo, cada um com o
   próprio conector de irmãos, e a fileira de cima quebrando linha sem
   ninguém prever. Empilhar reto depois da raiz nunca quebra linha,
   nunca precisa medir posição: é só uma lista vertical dentro da
   própria coluna. Compartilhada pelas duas lâminas
   (`slideOrganograma3D` e `slideOrganogramaMetodologico`), que antes
   reescreviam a mesma função lado a lado.

   `mostrados`, quando passado, evita desenhar a mesma pessoa duas vezes
   quando duas raízes do mesmo laço a alcançam (coorientação) -- ver
   `slideOrganogramaMetodologico`. */
function noArvore(id, profundidade, porId, filhosDe, mostrados) {
  const pessoa = porId[id];
  if (!pessoa || (mostrados && mostrados.has(id))) return null;
  if (mostrados) mostrados.add(id);
  const filhos = (filhosDe[id] || []).map(function (f) { return porId[f.to]; }).filter(Boolean);
  const no = el("div", { class: "no-organograma" }, [cartaoPessoa(pessoa, profundidade)]);
  if (!filhos.length || profundidade >= 3) return no;
  if (profundidade === 0) {
    const colunas = el("div", { class: "ramo-organograma" },
      filhos.map(function (p) { return noArvore(p.id, profundidade + 1, porId, filhosDe, mostrados); }).filter(Boolean));
    no.appendChild(colunas);
  } else {
    const pilha = el("div", { class: "coluna-descendentes" },
      filhos.flatMap(function (p) { return descendentesEmPilha(p.id, profundidade + 1, porId, filhosDe, mostrados); }));
    if (pilha.children.length) no.appendChild(pilha);
  }
  return no;
}

function descendentesEmPilha(id, profundidade, porId, filhosDe, mostrados) {
  const pessoa = porId[id];
  if (!pessoa || profundidade >= 4 || (mostrados && mostrados.has(id))) return [];
  if (mostrados) mostrados.add(id);
  const filhos = (filhosDe[id] || []).map(function (f) { return porId[f.to]; }).filter(Boolean);
  const netos = filhos.flatMap(function (p) { return descendentesEmPilha(p.id, profundidade + 1, porId, filhosDe, mostrados); });
  return [cartaoPessoa(pessoa, profundidade)].concat(netos);
}

function slideOrganograma3D(baldeIndex) {
  const t = tv();
  const org = t && t.organograma;
  if (!org || !(org.people || []).length) {
    return escalonar(el("div", { class: "slide" }, vazio("Nenhuma pessoa do LAPE cadastrada.")));
  }

  const container = el("div", { class: "slide slide-organograma-3d" });

  const porId = {};
  (org.people || []).forEach(function (p) { porId[p.id] = p; });
  /* A aresta "coordenacao" (metrics.organograma) e sintetica: quando so
     sobra um chefe solto no topo, o backend pendura TODAS as outras
     raizes nele so pra desenhar uma arvore so, sem que isso signifique
     orientacao de verdade. Seguir essa aresta aqui faria o balde da
     coordenacao engolir todo mundo sem orientador -- exatamente o
     amontoado que vazava a tela. So orientacao/coorientacao de verdade
     formam galho; quem nao tem orientador vira raiz do proprio balde. */
  const filhosDe = {};
  (org.edges || []).forEach(function (e) {
    if (e.kind !== "orientacao" && e.kind !== "coorientacao") return;
    if (!porId[e.from] || !porId[e.to]) return;
    (filhosDe[e.from] = filhosDe[e.from] || []).push({ to: e.to, kind: e.kind });
  });

  const temOrientador = temOrientadorVisivel(org.people, org.edges);

  /* Cada pessoa mora no balde de quem a alcança primeiro -- o dela mesma,
     se o vínculo dela é deste balde, ou o de um ancestral já mostrado num
     balde anterior. Por isso é preciso saber quem os baldes ANTERIORES já
     mostraram (raiz e toda a descendência dela) antes de decidir quem é
     raiz aqui. */
  const mostrados = new Set();
  function marcarMostrado(id) {
    if (mostrados.has(id)) return;
    mostrados.add(id);
    (filhosDe[id] || []).forEach(function (f) { marcarMostrado(f.to); });
  }
  function candidatosDoBalde(indice) {
    return (org.people || []).filter(function (p) { return baldeDoRole(p.role) === indice; });
  }
  for (let i = 0; i < baldeIndex; i++) {
    candidatosDoBalde(i).forEach(function (p) { marcarMostrado(p.id); });
  }
  const locais = candidatosDoBalde(baldeIndex).filter(function (p) {
    return !mostrados.has(p.id) && !temOrientador.has(p.id);
  });

  if (!locais.length) {
    return escalonar(el("div", { class: "slide" }, vazio("Ninguém neste grupo ainda.")));
  }

  const raizes = [];
  locais.forEach(function (p) {
    if (mostrados.has(p.id)) return;
    const no = noArvore(p.id, 0, porId, filhosDe);
    if (no) raizes.push(no);
    marcarMostrado(p.id);
  });
  container.appendChild(el("div", { class: "arvore-organograma" }, raizes));

  /* Legenda de status */
  container.appendChild(el("div", { class: "legenda-ponto" }, [
    el("div", { class: "item-legenda" }, [el("div", { class: "bolinha verde" }), el("span", { text: "Presente agora" })]),
    el("div", { class: "item-legenda" }, [el("div", { class: "bolinha cinza" }), el("span", { text: "Ausente" })]),
  ]));

  return escalonar(container);
}

/* Os três baldes (Coordenação e Docentes / Pós-graduação / Bolsistas e
   Demais) numa lâmina só, para o ciclo enxuto da parede -- em vez de três
   telas separadas. Reaproveita a mesma árvore e o mesmo `mostrados`
   (compartilhado entre os três baldes NUM SÓ laço, sem precisar
   "reencenar" quem os baldes anteriores já mostraram): cada pessoa segue
   morando no balde do primeiro vínculo que bate com ela, ou de um
   ancestral já mostrado, exatamente como em `slideOrganograma3D`. O
   `.slide-organograma-3d` já tem `overflow-y: auto` (a única lâmina do
   mural com essa válvula de escape) -- com os três baldes juntos, uma
   equipe grande rola em vez de cortar nas pontas. */
function slideOrganogramaMetodologico() {
  const t = tv();
  const org = t && t.organograma;
  if (!org || !(org.people || []).length) {
    return escalonar(el("div", { class: "slide" }, vazio("Nenhuma pessoa do LAPE cadastrada.")));
  }

  const container = el("div", { class: "slide slide-organograma-3d" });

  const porId = {};
  (org.people || []).forEach(function (p) { porId[p.id] = p; });
  const filhosDe = {};
  (org.edges || []).forEach(function (e) {
    if (e.kind !== "orientacao" && e.kind !== "coorientacao") return;
    if (!porId[e.from] || !porId[e.to]) return;
    (filhosDe[e.from] = filhosDe[e.from] || []).push({ to: e.to, kind: e.kind });
  });

  /* UM SÓ `mostrados`, atravessando os três baldes em ordem -- é o que
     substitui o "replay" que cada slide separada fazia sozinha. Marcado
     NA HORA em que o nó é desenhado (não só depois da árvore pronta):
     coorientação bota duas arestas chegando na mesma pessoa, então duas
     raízes do MESMO balde podem disputar o mesmo galho -- sem marcar
     durante a descida, a segunda raiz desenhava o galho de novo, e a
     pessoa aparecia duplicada na mesma seção. */
  const mostrados = new Set();

  const temOrientador = temOrientadorVisivel(org.people, org.edges);
  function candidatosDoBalde(indice) {
    return (org.people || []).filter(function (p) { return baldeDoRole(p.role) === indice; });
  }

  const secoes = [];
  BALDES_ORGANOGRAMA.forEach(function (balde, indice) {
    const locais = candidatosDoBalde(indice).filter(function (p) {
      return !mostrados.has(p.id) && !temOrientador.has(p.id);
    });
    const raizes = [];
    locais.forEach(function (p) {
      const no = noArvore(p.id, 0, porId, filhosDe, mostrados);
      if (no) raizes.push(no);
    });
    if (raizes.length) {
      secoes.push(el("div", { class: "organograma-secao" }, [
        el("h3", { class: "organograma-secao-titulo", text: balde.titulo }),
        el("div", { class: "arvore-organograma" }, raizes),
      ]));
    }
  });

  if (!secoes.length) {
    return escalonar(el("div", { class: "slide" }, vazio("Ninguém no organograma ainda.")));
  }
  secoes.forEach(function (secao) { container.appendChild(secao); });

  container.appendChild(el("div", { class: "legenda-ponto" }, [
    el("div", { class: "item-legenda" }, [el("div", { class: "bolinha verde" }), el("span", { text: "Presente agora" })]),
    el("div", { class: "item-legenda" }, [el("div", { class: "bolinha cinza" }), el("span", { text: "Ausente" })]),
  ]));

  return escalonar(container);
}

/* ==================== FRAMEWORK DE PESQUISA (PIPELINE REAL) ==================== */
/* O mesmo mapa tom -> variável de cor que `.cartao-pessoa[data-tom=...]`
   usa no CSS -- aqui reaproveitado para colorir a fatia de cada fase do
   hexágono. */
const TOM_VAR = {
  azul: "--series-1", laranja: "--series-2", verde: "--series-3", ambar: "--series-4",
  magenta: "--series-5", violeta: "--series-7", bom: "--good", alerta: "--warning",
};

/* Um ponto num círculo, a partir do centro, do raio e do ângulo em graus
   (0° = topo, sentido horário) -- a mesma trigonometria de sempre, só
   para não repeti-la em cada segmento do hexágono. */
function pontoNoCirculo(cx, cy, raio, anguloGraus) {
  const rad = (anguloGraus - 90) * Math.PI / 180;
  return { x: cx + raio * Math.cos(rad), y: cy + raio * Math.sin(rad) };
}

/* As fases batem exato com os status do banco (config.ARTICLE_STATUS) --
   nunca um estágio inventado que o sistema não consegue contar de
   verdade. Rejeitado/arquivado sempre foram um desfecho à parte do fluxo
   principal (nunca escondido, nunca forçado como "próximo passo") -- e é
   exatamente esse sexto estado real que fecha as 6 partes do hexágono
   pedido, sem inventar uma fase que não existe no banco.

   Referência que o Mateus mandou é um hexágono giratório, 6 pétalas ao
   redor de um centro. Aqui cada pétala é uma fatia de anel (SVG puro,
   sem lib nova): o miolo mostra o total em fluxo, e a fatia do gargalo
   (a etapa com mais manuscritos parados antes da publicação) pulsa uma
   borda -- um efeito só, não vários empilhados. */
function slideFrameworkN8n() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados do framework não disponíveis.")));

  const FASES = [
    { id: "em_producao", label: "Em Produção", tom: "azul" },
    { id: "submetido", label: "Submetido", tom: "violeta" },
    { id: "em_revisao", label: "Em Revisão", tom: "ambar" },
    { id: "aceito", label: "Aceito", tom: "bom" },
    { id: "publicado", label: "Publicado", tom: "verde" },
    { id: "rejeitado_arquivado", label: "Rejeitado/Arquivado", tom: "alerta" },
  ];

  const contagem = {};
  FASES.forEach(f => { contagem[f.id] = 0; });
  artigos().forEach(function (a) {
    if (contagem.hasOwnProperty(a.status)) contagem[a.status]++;
    else if (a.status === "rejeitado" || a.status === "arquivado") contagem.rejeitado_arquivado++;
  });

  const total = Object.values(contagem).reduce((a, b) => a + b, 0);
  if (!total) {
    return escalonar(el("div", { class: "slide" }, vazio("Nenhum artigo cadastrado ainda.")));
  }

  /* Gargalo real: a etapa anterior à publicação com mais artigos parados
     -- nunca o desfecho (rejeitado/arquivado não é "onde o fluxo travou",
     é onde ele terminou). */
  const antesDePublicar = FASES.filter(f => f.id !== "publicado" && f.id !== "rejeitado_arquivado");
  const gargalo = antesDePublicar.reduce((pior, f) =>
    contagem[f.id] > (contagem[pior.id] || 0) ? f : pior, antesDePublicar[0]);
  const gargaloId = gargalo && contagem[gargalo.id] > 0 ? gargalo.id : null;

  const container = el("div", { class: "slide slide-framework-n8n" });

  const w = 440, h = 440, cx = w / 2, cy = h / 2, rInt = 78, rExt = 186, vao = 360 / FASES.length, gap = 2.6;
  const svg = elSvg("svg", { viewBox: `0 0 ${w} ${h}`, class: "plot hexagono-framework" });

  FASES.forEach(function (fase, i) {
    const a0 = i * vao + gap / 2, a1 = (i + 1) * vao - gap / 2, meio = (a0 + a1) / 2;
    const pInt0 = pontoNoCirculo(cx, cy, rInt, a0), pExt0 = pontoNoCirculo(cx, cy, rExt, a0);
    const pExt1 = pontoNoCirculo(cx, cy, rExt, a1), pInt1 = pontoNoCirculo(cx, cy, rInt, a1);
    const d = `M ${pInt0.x} ${pInt0.y} L ${pExt0.x} ${pExt0.y} `
      + `A ${rExt} ${rExt} 0 0 1 ${pExt1.x} ${pExt1.y} L ${pInt1.x} ${pInt1.y} `
      + `A ${rInt} ${rInt} 0 0 0 ${pInt0.x} ${pInt0.y} Z`;
    svg.appendChild(elSvg("path", {
      d, fill: `var(${TOM_VAR[fase.tom]})`,
      class: "fatia-hexagono" + (fase.id === gargaloId ? " gargalo" : ""),
    }));

    const pMeio = pontoNoCirculo(cx, cy, (rInt + rExt) / 2, meio);
    svg.appendChild(elSvg("text", { x: pMeio.x, y: pMeio.y + 6, "text-anchor": "middle",
      class: "hex-numero" }, String(contagem[fase.id] || 0)));

    const pLabel = pontoNoCirculo(cx, cy, rExt + 22, meio);
    const ancora = Math.abs(pLabel.x - cx) < 8 ? "middle" : (pLabel.x < cx ? "end" : "start");
    svg.appendChild(elSvg("text", { x: pLabel.x, y: pLabel.y, "text-anchor": ancora,
      class: "hex-rotulo" }, fase.label));

    if (fase.id === gargaloId) {
      const pFlag = pontoNoCirculo(cx, cy, rExt + 40, meio);
      svg.appendChild(elSvg("text", { x: pFlag.x, y: pFlag.y, "text-anchor": ancora,
        class: "hex-flag" }, "GARGALO"));
    }
  });

  svg.appendChild(elSvg("circle", { cx, cy, r: rInt - 6, class: "hex-hub" }));
  svg.appendChild(elSvg("text", { x: cx, y: cy - 6, "text-anchor": "middle", class: "hex-hub-numero" }, String(total)));
  svg.appendChild(elSvg("text", { x: cx, y: cy + 16, "text-anchor": "middle", class: "hex-hub-rotulo" }, "em fluxo"));

  const fig = document.createElement("figure");
  fig.setAttribute("class", "chart");
  fig.appendChild(svg);
  container.appendChild(el("div", { class: "hexagono-caixa" }, [fig]));

  /* Resumo textual, embaixo do hexágono -- o mesmo par de fatos que o
     pipeline linear já mostrava. */
  container.appendChild(el("div", { class: "resumo-workflow" }, [
    el("div", { class: "resumo-item" }, [
      el("span", { class: "resumo-label", text: "Total em fluxo:" }),
      el("span", { class: "resumo-valor", text: String(total) }),
    ]),
    el("div", { class: "resumo-item" }, [
      el("span", { class: "resumo-label", text: "Gargalo:" }),
      el("span", { class: "resumo-valor",
        text: gargaloId ? gargalo.label + " (" + contagem[gargaloId] + ")" : "nenhum" }),
    ]),
  ]));

  return escalonar(container);
}

/* ==================== KPIs ANALÍTICOS 4K ==================== */
function slideKPIsAnalyticos() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados analíticos não disponíveis.")));

  /* Tudo aqui vem do banco, pelo payload da TV -- nada de série simulada.
     Sem número real, o cartão mostra "—" em vez de inventar tendência. */
  const kpisTemas = (t.temas && t.temas.kpis) || [];
  const porCodigo = {};
  kpisTemas.forEach(function (k) { porCodigo[k.code] = k; });
  const aceite = porCodigo.aceite;
  const tempo = porCodigo.tempo;
  const citRes = (t.citacoes && t.citacoes.resumo) || {};
  const equipeLape = (t.organograma && t.organograma.people) || [];
  const totalArtigosLinhas = (t.linhas || []).reduce(function (s, l) { return s + (l.artigos || 0); }, 0);
  const produtividade = equipeLape.length ? totalArtigosLinhas / equipeLape.length : null;
  const comp = t.comparacoes || {};

  const kpis = [
    { id: "aceite", titulo: "Taxa de Aceite", cor: "#10b981", icone: "✓",
      valor: aceite && aceite.valor !== null && aceite.valor !== undefined ? aceite.valor : null, unidade: "%",
      delta: comp.aceites ? comp.aceites.delta : null, deltaRotulo: "aceites vs. mês anterior" },
    { id: "dias", titulo: "Dias até Publicação", cor: "#3b82f6", icone: "⏱",
      valor: tempo && tempo.valor !== null && tempo.valor !== undefined ? tempo.valor : null, unidade: " dias",
      nota: tempo ? tempo.pe : null },
    { id: "citacoes", titulo: "Citações/Artigo", cor: "#8b5cf6", icone: "📊",
      valor: citRes.total_artigos ? citRes.media_citacoes : null, unidade: "",
      nota: citRes.total_artigos ? citRes.total_artigos + " artigo(s) com dados de citação" : "sincronização com as bases ainda pendente" },
    { id: "produtividade", titulo: "Produtividade Equipe", cor: "#f59e0b", icone: "👥",
      valor: produtividade, unidade: " art/pes",
      nota: equipeLape.length + " pessoa(s) do LAPE cadastrada(s)" },
  ];

  const container = el("div", { class: "slide slide-kpis-analytics-4k" });
  const grid = el("div", { class: "grid-kpis-4k" });

  kpis.forEach(function (kpi) {
    const card = el("div", { class: "card-kpi-4k", "data-kpi": kpi.id, style: "--cor-kpi:" + kpi.cor + ";" });

    card.appendChild(el("div", { class: "header-kpi" }, [
      el("span", { class: "icone-kpi", text: kpi.icone }),
      el("span", { class: "titulo-kpi", text: kpi.titulo }),
    ]));

    const temValor = kpi.valor !== null && kpi.valor !== undefined && isFinite(kpi.valor);
    const valueContainer = el("div", { class: "value-container-kpi" });
    const value = el("span", { class: "valor-kpi",
      "data-valor": temValor ? String(kpi.valor) : "", "data-unidade": kpi.unidade,
      text: temValor ? "0" + kpi.unidade : "—" });
    valueContainer.appendChild(value);
    card.appendChild(valueContainer);

    if (kpi.delta !== null && kpi.delta !== undefined && kpi.delta !== 0) {
      card.appendChild(el("div", { class: "tendencia-kpi", "data-tendencia": kpi.delta > 0 ? "up" : "down",
        text: (kpi.delta > 0 ? "↑ +" : "↓ ") + kpi.delta + " " + (kpi.deltaRotulo || "") }));
    } else if (kpi.nota) {
      card.appendChild(el("div", { class: "tendencia-kpi", "data-tendencia": "flat", text: kpi.nota }));
    }

    grid.appendChild(card);

    if (temValor) {
      setTimeout(function () {
        const target = kpi.valor;
        const duration = 900;
        const startTime = performance.now();
        (function animate(currentTime) {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const current = Math.round(progress * target * 10) / 10;
          value.textContent = C.fmt(current) + kpi.unidade;
          if (progress < 1) requestAnimationFrame(animate);
        })(startTime);
      }, 100);
    }
  });

  container.appendChild(grid);

  return escalonar(container);
}

/* ==================== CITAÇÕES E BASES DE DADOS ==================== */
function slideCitacoesBases() {
  const t = tv();
  const cit = t && t.citacoes;
  if (!cit || !cit.resumo) {
    return escalonar(el("div", { class: "slide" }, vazio("Citações ainda não sincronizadas com as bases externas.")));
  }

  const resumo = cit.resumo;
  /* Por IMPACTO total, não média -- média favorece uma linha de um
     artigo só com sorte de citação, acima de uma linha com trinta
     artigos e resultado consistente. Total é a pergunta certa aqui. */
  const linhas = (cit.linhas || []).slice().sort(function (a, b) {
    return (b.total_citacoes || 0) - (a.total_citacoes || 0);
  });

  const container = el("div", { class: "slide slide-citacoes-bases" });
  const wrapper = el("div", { class: "bases-wrapper" });

  if (cit.gerado_em) {
    wrapper.appendChild(el("span", { class: "bases-timestamp",
      text: "sincronizado " + new Date(cit.gerado_em).toLocaleString("pt-BR") }));
  }

  wrapper.appendChild(el("div", { class: "bases-resumo" }, [
    el("div", { class: "metric-card metric-total" }, [
      el("div", { class: "metric-label", text: "Total de citações" }),
      el("div", { class: "metric-value", "data-metrica": "total_citacoes", text: C.fmt(resumo.total_citacoes) }),
      el("div", { class: "metric-meta", text: C.fmt(resumo.total_artigos) + " artigo(s) com dados" }),
    ]),
    el("div", { class: "metric-card metric-media" }, [
      el("div", { class: "metric-label", text: "Média por artigo" }),
      el("div", { class: "metric-value", "data-metrica": "media_citacoes", text: C.fmt(resumo.media_citacoes) }),
      el("div", { class: "metric-meta", text: C.fmt(resumo.linhas_ativas) + " linha(s) de pesquisa" }),
    ]),
    el("div", { class: "metric-card metric-fonte" }, [
      el("div", { class: "metric-label", text: "Fonte" }),
      el("div", { class: "metric-fonte-list" }, [
        el("span", { class: "fonte-badge openalex", text: "OpenAlex" }),
      ]),
    ]),
  ]));

  if (!resumo.total_artigos) {
    wrapper.appendChild(vazio("Nenhum artigo encontrado ainda nas bases externas — a sincronização roda por DOI e título."));
  }

  /* "Métricas de Impacto": o total de citações por linha, num gráfico de
     barras horizontais de verdade (C.bars) -- os cartões de progresso
     logo abaixo mostram COBERTURA (% de artigo com dado nas bases), que
     é outra pergunta. Impacto é este número, do maior para o menor. */
  const comCitacoes = linhas.filter(function (l) { return l.total_citacoes > 0; });
  if (comCitacoes.length) {
    const graficoImpacto = C.bars({
      items: comCitacoes.map(function (l) {
        const tom = l.media_citacoes > 5 ? "good" : l.media_citacoes > 2 ? "warning" : "critical";
        return { label: cortar(l.nome, 38), value: l.total_citacoes, color: "var(--" + tom + ")" };
      }),
      unit: "citações", labelWidth: 220, rowH: 26,
    });
    wrapper.appendChild(quadro("Métricas de impacto", "citacao", graficoImpacto,
      "citações totais por linha de pesquisa", "moldura-viva grafico-fluxo"));
  }

  /* Só ganham cartão as linhas com citação de verdade -- uma linha em
     0 não tem nada a mostrar além de zeros repetidos, e treze cartões
     (a maioria vazia) é o que fazia esta tela cortar embaixo da TV.
     As sem dado ainda entram numa linha de texto só, não somem. */
  if (comCitacoes.length) {
    const grid = el("div", { class: "bases-linhas" });
    comCitacoes.forEach(function (linha) {
      const cobertura = linha.total_artigos ? Math.round(100 * (linha.artigos_com_dados || 0) / linha.total_artigos) : 0;
      const tom = linha.media_citacoes > 5 ? "success" : linha.media_citacoes > 2 ? "warning" : "info";
      grid.appendChild(el("div", { class: "linha-card " + tom }, [
        el("div", { class: "linha-header" }, [
          el("h3", { text: linha.nome }),
          el("span", { class: "linha-cobertura", text: cobertura + "% coberto" }),
        ]),
        el("div", { class: "linha-metricas" }, [
          el("div", { class: "metrica-pequena" }, [el("span", { class: "label", text: "Artigos" }), el("span", { class: "valor", text: C.fmt(linha.total_artigos) })]),
          el("div", { class: "metrica-pequena" }, [el("span", { class: "label", text: "Citações" }), el("span", { class: "valor", text: C.fmt(linha.total_citacoes) })]),
          el("div", { class: "metrica-pequena" }, [el("span", { class: "label", text: "Média" }), el("span", { class: "valor", text: C.fmt(linha.media_citacoes) })]),
        ]),
        el("div", { class: "linha-progresso" }, [
          el("div", { class: "progresso-bar" }, [el("div", { class: "progresso-fill", style: "width:" + cobertura + "%" })]),
        ]),
      ]));
    });
    wrapper.appendChild(grid);
  }

  const semCitacoes = linhas.filter(function (l) { return !(l.total_citacoes > 0); });
  if (semCitacoes.length) {
    wrapper.appendChild(el("p", { class: "linhas-sem-citacao" }, [
      el("b", { text: semCitacoes.length + " linha(s) sem citação sincronizada ainda: " }),
      el("span", { text: semCitacoes.map(function (l) { return l.nome; }).join(" · ") }),
    ]));
  }

  const artigos = [];
  linhas.forEach(function (l) {
    (l.artigos || []).forEach(function (a) { artigos.push(Object.assign({}, a, { linha: l.nome })); });
  });
  artigos.sort(function (a, b) { return (b.citacoes || 0) - (a.citacoes || 0); });
  /* Dois, não cinco: com o resumo, o gráfico de impacto e os cartões de
     linha já ocupando a tela, mais que isso cortava o último item
     embaixo -- a TV não tem scroll para completar o que passou da borda. */
  const top = artigos.slice(0, 2);

  if (top.length) {
    const topBox = el("div", { class: "top-artigos" }, [el("h3", { text: "Mais citados" })]);
    const lista = el("div", { class: "artigos-lista" });
    top.forEach(function (a, i) {
      lista.appendChild(el("div", { class: "artigo-item rank-" + (i + 1) }, [
        el("span", { class: "rank", text: "#" + (i + 1) }),
        el("div", { class: "artigo-info" }, [
          el("div", { class: "artigo-titulo", text: a.titulo || "Sem título" }),
          el("div", { class: "artigo-meta" }, [
            el("span", { text: a.linha }),
            a.revista ? el("span", { text: a.revista }) : null,
            el("span", { text: String(a.ano_publicacao || "—") }),
          ]),
        ]),
        el("div", { class: "artigo-citacoes", text: C.fmt(a.citacoes || 0) }),
      ]));
    });
    topBox.appendChild(lista);
    wrapper.appendChild(topBox);
  }

  container.appendChild(wrapper);
  return escalonar(container);
}

/* Exportar funções para mural.js */
if (typeof window !== "undefined") {
  window.slidePesquisasLinhas3D = slidePesquisasLinhas3D;
  window.slideOrganograma3D = slideOrganograma3D;
  window.slideFrameworkN8n = slideFrameworkN8n;
  window.slideKPIsAnalyticos = slideKPIsAnalyticos;
  window.slideCitacoesBases = slideCitacoesBases;
}
