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
  /* O raio cresce com o número de linhas cadastradas -- fixo em 200px,
     o espaçamento angular entre nós encolhia conforme mais linhas de
     pesquisa eram criadas, até os rótulos se sobreporem. Limitado a
     300 para não estourar o viewBox (o centro está a 400px da borda). */
  const radius = Math.min(300, Math.max(160, 26 * linhas.length));
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

  /* Trilha pontilhada só decorativa, no raio dos nós -- dá a leitura de
     "órbita" mesmo no instante em que a rotação está parada (print,
     captura de tela, prefers-reduced-motion). */
  svg.appendChild(elSvg("circle", {
    cx: centerX, cy: centerY, r: radius, class: "trilha-orbita",
    fill: "none", "stroke-dasharray": "2 10",
  }));

  /* Todo o anel (raios + nós) gira em torno do centro -- antes só o hub
     central tinha `rotacao-3d`; o resto do grafo ficava parado. Cada nó
     mora dentro de um `<g>` próprio que gira na direção oposta, à mesma
     velocidade, em torno do seu PRÓPRIO ponto (não do centro) -- assim a
     posição orbita, mas o rótulo/ícone/badges continuam de pé, legíveis. */
  const anel = elSvg("g", { class: "anel-orbita" });
  const particulas = [];

  linhas.forEach((linha, idx) => {
    const angle = (idx / linhas.length) * Math.PI * 2;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    const n_artigos = linha.artigos || 0;
    const taxa_pub = linha.taxa_publicacao || 0;
    const atividade = n_artigos / maiorArtigos;

    const nodeRadius = Math.max(20, Math.min(60, 20 + (n_artigos / 5)));
    /* Cor por IDENTIDADE da linha (categórica, uma por linha, igual ao
       resto do mural -- ver .cartao-pessoa/.etapa-framework), não mais
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

    /* Grupo do nó: gira ao contrário do anel, em torno do seu próprio
       centro (x,y), para orbitar sem virar de cabeça pra baixo. */
    const grupoNo = elSvg("g", {
      class: "grupo-no-orbita",
      style: `--index:${idx};transform-origin:${x.toFixed(1)}px ${y.toFixed(1)}px;`,
    });

    const publicados = linha.publicados || 0;
    const citacoes = linha.citacoes || 0;
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

  function cartaoPessoa(p) {
    const [icone, tom] = VINCULOS_ICONE[p.role || "sem_vinculo"] || VINCULOS_ICONE.sem_vinculo;
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

  /* A árvore de verdade, sempre horizontal: raiz em cima, filhos numa
     fileira embaixo, ligados pelo conector clássico (CSS
     .ramo-organograma). Com o organograma agora separado em baldes por
     vínculo, cada slide só recebe as raízes DAQUELE balde -- a fileira de
     órfãos que vazava a tela não existe mais porque a coordenação, os
     professores e o resto não competem pelo mesmo slide. */
  function noArvore(id, profundidade) {
    const pessoa = porId[id];
    if (!pessoa) return null;
    const filhos = (filhosDe[id] || []).map(function (f) { return porId[f.to]; }).filter(Boolean);
    const no = el("div", { class: "no-organograma" }, [cartaoPessoa(pessoa)]);
    if (!filhos.length || profundidade >= 3) return no;
    const galhos = el("div", { class: "ramo-organograma" },
      filhos.map(function (p) { return noArvore(p.id, profundidade + 1); }).filter(Boolean));
    no.appendChild(galhos);
    return no;
  }

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
    const no = noArvore(p.id, 0);
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

/* ==================== FRAMEWORK DE PESQUISA (PIPELINE REAL) ==================== */
/* As fases batem exato com os status do banco (config.ARTICLE_STATUS) --
   nunca um estágio inventado que o sistema não consegue contar de verdade.
   Rejeitado/arquivado são desfechos, não um próximo passo: entram à parte,
   nunca escondidos, nunca forçados dentro do fluxo principal. */
function slideFrameworkN8n() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados do framework não disponíveis.")));

  const FASES = [
    { id: "em_producao", label: "Em Produção", icone: "producao", tom: "azul" },
    { id: "submetido", label: "Submetido", icone: "submissao", tom: "violeta" },
    { id: "em_revisao", label: "Em Revisão", icone: "processo", tom: "ambar" },
    { id: "aceito", label: "Aceito", icone: "aceite", tom: "bom" },
    { id: "publicado", label: "Publicado", icone: "livro", tom: "verde" },
  ];

  const contagem = {};
  FASES.forEach(f => { contagem[f.id] = 0; });
  let rejeitados = 0;
  artigos().forEach(function (a) {
    if (contagem.hasOwnProperty(a.status)) contagem[a.status]++;
    else if (a.status === "rejeitado" || a.status === "arquivado") rejeitados++;
  });

  const total = Object.values(contagem).reduce((a, b) => a + b, 0);
  if (!total && !rejeitados) {
    return escalonar(el("div", { class: "slide" }, vazio("Nenhum artigo cadastrado ainda.")));
  }

  /* Gargalo real: a etapa anterior à publicação com mais artigos parados. */
  const antesDePublicar = FASES.slice(0, -1);
  const gargalo = antesDePublicar.reduce((pior, f) =>
    contagem[f.id] > (contagem[pior.id] || 0) ? f : pior, antesDePublicar[0]);

  const container = el("div", { class: "slide slide-framework-n8n" });
  const pipeline = el("div", { class: "framework-pipeline" });

  FASES.forEach((fase, idx) => {
    const count = contagem[fase.id] || 0;
    const ehGargalo = fase.id === gargalo.id && count > 0;

    const card = el("div", {
      class: "etapa-framework" + (ehGargalo ? " gargalo" : ""),
      "data-tom": fase.tom,
      style: `--index:${idx};`,
    }, [
      Icons.badge(fase.icone, fase.tom, 30),
      el("div", { class: "etapa-numero", text: String(count) }),
      el("div", { class: "etapa-rotulo", text: fase.label }),
      ehGargalo ? el("div", { class: "etapa-flag", text: "gargalo" }) : null,
    ]);
    pipeline.appendChild(card);

    if (idx < FASES.length - 1) {
      pipeline.appendChild(el("div", { class: "conector-framework", style: `--index:${idx};` }, [
        el("span", { class: "seta-conector" }),
        el("span", { class: "particula-conector" }),
      ]));
    }
  });

  container.appendChild(pipeline);

  if (rejeitados > 0) {
    container.appendChild(el("div", { class: "framework-desfecho" }, [
      Icons.badge("aviso", "alerta", 18),
      el("span", { text: rejeitados + " manuscrito(s) rejeitado(s)/arquivado(s) -- fora do fluxo principal" }),
    ]));
  }

  /* Resumo textual */
  const resumo = el("div", { class: "resumo-workflow" }, [
    el("div", { class: "resumo-item" }, [
      el("span", { class: "resumo-label", text: "Total em fluxo:" }),
      el("span", { class: "resumo-valor", text: String(total) }),
    ]),
    el("div", { class: "resumo-item" }, [
      el("span", { class: "resumo-label", text: "Gargalo:" }),
      el("span", { class: "resumo-valor",
        text: gargalo && contagem[gargalo.id] > 0 ? gargalo.label + " (" + contagem[gargalo.id] + ")" : "nenhum" }),
    ]),
  ]);
  container.appendChild(resumo);

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
