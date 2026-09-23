/* ===================================================================
   SLIDES AVANÇADOS 3D - LAPE
   Gráficos 3D, animações n8n-style, indicador de ponto em tempo real
   Para modo painel 4K com efeitos profissionais
   =================================================================== */
"use strict";

/* ==================== LINHAS DE PESQUISA 3D ==================== */
function slidePesquisasLinhas3D() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Linhas de pesquisa ainda não carregadas.")));

  const linhas = t.linhas || [];
  if (!linhas.length) return escalonar(el("div", { class: "slide" }, vazio("Nenhuma linha de pesquisa cadastrada.")));

  const container = el("div", {
    class: "slide slide-pesquisas-3d",
    style: "--linhas-count:" + linhas.length,
  });

  const svg = el("svg", {
    class: "grafo-linhas-3d",
    viewBox: "0 0 1200 800",
    style: "width:100%;height:100%;position:relative;",
  });

  const centerX = 600, centerY = 400;
  const radius = 200;

  linhas.forEach((linha, idx) => {
    const angle = (idx / linhas.length) * Math.PI * 2;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    const n_artigos = linha.artigos || 0;
    const taxa_pub = linha.taxa_publicacao || 0;

    const nodeRadius = Math.max(20, Math.min(60, 20 + (n_artigos / 5)));
    const strokeColor = taxa_pub > 0.8 ? "#10b981" : taxa_pub > 0.5 ? "#f59e0b" : "#ef4444";

    /* Linha do centro até o nó (Bezier com animação) */
    const line = el("path", {
      d: `M ${centerX} ${centerY} Q ${(centerX + x) / 2} ${(centerY + y) / 2} ${x} ${y}`,
      class: "conexao-linha-pesquisa",
      style: `--index:${idx};--total:${linhas.length};`,
      stroke: strokeColor,
      "stroke-width": "2",
      fill: "none",
      "stroke-dasharray": "400",
      "stroke-dashoffset": "400",
      "vector-effect": "non-scaling-stroke",
    });
    svg.appendChild(line);

    /* Glow filter */
    const glowId = `glow-linha-${idx}`;
    if (idx === 0) {
      const defs = el("defs");
      const filter = el("filter", { id: glowId, x: "-50%", y: "-50%", width: "200%", height: "200%" });
      filter.appendChild(el("feGaussianBlur", { "in": "SourceGraphic", stdDeviation: "4" }));
      defs.appendChild(filter);
      svg.insertBefore(defs, svg.firstChild);
    }

    /* Nó central (círculo com glow) */
    const circle = el("circle", {
      cx: x,
      cy: y,
      r: nodeRadius,
      class: "nodo-linha-pesquisa",
      style: `--index:${idx};--radius:${nodeRadius};--cor:${strokeColor};`,
      fill: "currentColor",
      filter: `url(#${glowId})`,
      opacity: "0.8",
    });
    circle.addEventListener("mouseenter", function () {
      this.style.opacity = "1";
      this.style.r = nodeRadius + 10;
    });
    circle.addEventListener("mouseleave", function () {
      this.style.opacity = "0.8";
      this.style.r = nodeRadius;
    });
    svg.appendChild(circle);

    /* Label do nó */
    const label = el("text", {
      x: x,
      y: y + nodeRadius + 25,
      class: "label-linha-pesquisa",
      "text-anchor": "middle",
      fill: "currentColor",
      "font-size": "11px",
      "font-weight": "600",
      style: `--index:${idx};`,
    });
    label.textContent = cortar(linha.nome, 20);
    svg.appendChild(label);

    /* Badge com número de artigos */
    const badge = el("text", {
      x: x + nodeRadius + 5,
      y: y - nodeRadius - 5,
      class: "badge-artigos",
      fill: strokeColor,
      "font-size": "13px",
      "font-weight": "700",
      "dominant-baseline": "middle",
    });
    badge.textContent = n_artigos;
    svg.appendChild(badge);
  });

  /* Centro: nó principal girando */
  const centerCircle = el("circle", {
    cx: centerX,
    cy: centerY,
    r: "40",
    class: "centro-rotacao-3d",
    fill: "url(#gradCentro)",
    "filter": "drop-shadow(0 0 12px currentColor)",
  });
  const defs = svg.querySelector("defs") || el("defs");
  if (!svg.contains(defs)) svg.insertBefore(defs, svg.firstChild);
  const gradCentro = el("radialGradient", { id: "gradCentro" });
  gradCentro.appendChild(el("stop", { offset: "0%", "stop-color": "var(--accent)" }));
  gradCentro.appendChild(el("stop", { offset: "100%", "stop-color": "var(--accent-strong)" }));
  defs.appendChild(gradCentro);
  svg.appendChild(centerCircle);

  /* Rótulo central */
  const centrLabel = el("text", {
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

  const info = el("div", { class: "info-linhas-3d" }, [
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Linhas ativas:" }),
      el("span", { class: "info-value", text: String(linhas.length) }),
    ]),
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Total de artigos:" }),
      el("span", { class: "info-value", text: String(linhas.reduce((a, b) => a + (b.artigos || 0), 0)) }),
    ]),
    el("div", { class: "info-item" }, [
      el("span", { class: "info-label", text: "Taxa média:" }),
      el("span", { class: "info-value", text: fmt(linhas.reduce((a, b) => a + (b.taxa_publicacao || 0), 0) / Math.max(1, linhas.length) * 100) + "%" }),
    ]),
  ]);

  container.appendChild(info);

  return escalonar(container);
}

/* ==================== ORGANOGRAMA COM INDICADOR DE PONTO ==================== */
function slideOrganograma3D() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados de organograma não disponíveis.")));

  const pessoas = t.pessoas || [];
  if (!pessoas.length) return escalonar(el("div", { class: "slide" }, vazio("Nenhuma pessoa cadastrada.")));

  const container = el("div", { class: "slide slide-organograma-3d" });

  /* Agrupar por vínculo */
  const vinculos = {};
  pessoas.forEach(p => {
    const v = p.vinculo || "sem_vinculo";
    if (!vinculos[v]) vinculos[v] = [];
    vinculos[v].push(p);
  });

  /* Hierarquia visual */
  const hierarchy = el("div", { class: "hierarchy-tree" });

  const VINCULOS_ORDEM = ["coordenacao", "professor", "pos_doutorado", "doutorando", "mestrando", "bolsista_ic", "voluntario", "colaborador"];
  const VINCULOS_NOME_MAP = {
    coordenacao: "Coordenação",
    professor: "Professores",
    pos_doutorado: "Pós-doutorado",
    doutorando: "Doutorando(a)",
    mestrando: "Mestrando(a)",
    bolsista_ic: "Bolsista de IC",
    voluntario: "Voluntário(a)",
    colaborador: "Colaborador(a) externo",
  };

  VINCULOS_ORDEM.forEach(vinculo => {
    const grupo = vinculos[vinculo];
    if (!grupo || !grupo.length) return;

    const grupoEl = el("div", { class: "grupo-vinculo", "data-vinculo": vinculo });
    const titulo = el("div", { class: "titulo-grupo" }, VINCULOS_NOME_MAP[vinculo] || vinculo);
    grupoEl.appendChild(titulo);

    const pessoasContainer = el("div", { class: "pessoas-container" });
    grupo.forEach(p => {
      const ativo = p.ativo_agora ? "ativo" : "inativo";
      const cartao = el("div", { class: `cartao-pessoa ${ativo}`, "data-id": p.id });

      /* Bolinha de status (ponto) */
      const statusBolinha = el("div", { class: `status-bolinha ${ativo}` });
      if (p.ativo_agora) {
        statusBolinha.classList.add("pulsante");
      }
      cartao.appendChild(statusBolinha);

      /* Nome e vínculo */
      const nome = el("div", { class: "nome-pessoa", text: cortar(p.nome, 25) });
      cartao.appendChild(nome);

      /* Número de artigos */
      const nArtigos = p.n_artigos || 0;
      const badge = el("div", { class: "badge-artigos", text: nArtigos });
      cartao.appendChild(badge);

      /* Tooltip ao hover */
      cartao.title = `${p.nome}\n${VINCULOS_NOME_MAP[vinculo]}\n${nArtigos} artigos\nÚltimo acesso: ${p.ultimo_acesso || 'nunca'}`;

      pessoasContainer.appendChild(cartao);
    });

    grupoEl.appendChild(pessoasContainer);
    hierarchy.appendChild(grupoEl);
  });

  container.appendChild(hierarchy);

  /* Legenda de status */
  const legenda = el("div", { class: "legenda-ponto" }, [
    el("div", { class: "item-legenda" }, [
      el("div", { class: "bolinha verde" }),
      el("span", { text: "Presente agora" }),
    ]),
    el("div", { class: "item-legenda" }, [
      el("div", { class: "bolinha cinza" }),
      el("span", { text: "Ausente" }),
    ]),
  ]);
  container.appendChild(legenda);

  return escalonar(container);
}

/* ==================== FRAMEWORK N8N (WORKFLOW) ==================== */
function slideFrameworkN8n() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados do framework não disponíveis.")));

  const container = el("div", { class: "slide slide-framework-n8n" });

  /* Definir as fases do workflow */
  const fases = [
    { id: "idea", label: "Ideia", icone: "bulb", cor: "#8b5cf6" },
    { id: "protocolo", label: "Protocolo", icone: "documento", cor: "#3b82f6" },
    { id: "coleta", label: "Coleta", icone: "dados", cor: "#06b6d4" },
    { id: "analise", label: "Análise", icone: "grafico", cor: "#14b8a6" },
    { id: "artigo", label: "Artigo", icone: "livro", cor: "#84cc16" },
    { id: "submissao", label: "Submissão", icone: "envio", cor: "#f59e0b" },
    { id: "publicacao", label: "Publicado", icone: "estrela", cor: "#10b981" },
  ];

  /* Simular contagem de artigos por fase (virá do backend) */
  const contagem = {
    idea: 8,
    protocolo: 15,
    coleta: 5,
    analise: 12,
    artigo: 7,
    submissao: 3,
    publicacao: 127,
  };

  const svg = el("svg", {
    class: "workflow-n8n",
    viewBox: "0 0 1400 600",
    style: "width:100%;height:100%;",
  });

  const boxWidth = 140, boxHeight = 100, spacing = 180, startX = 50, startY = 150;

  fases.forEach((fase, idx) => {
    const x = startX + idx * spacing;
    const y = startY;
    const count = contagem[fase.id] || 0;

    /* Caixa do nó */
    const box = el("rect", {
      x: x,
      y: y,
      width: boxWidth,
      height: boxHeight,
      class: "node-n8n",
      style: `--index:${idx};--cor:${fase.cor};`,
      fill: fase.cor,
      opacity: "0.15",
      stroke: fase.cor,
      "stroke-width": "2",
      rx: "8",
    });
    svg.appendChild(box);

    /* Icone (simulado com texto) */
    const icon = el("text", {
      x: x + boxWidth / 2,
      y: y + 25,
      class: "icon-node",
      "text-anchor": "middle",
      "font-size": "20px",
      fill: fase.cor,
    });
    icon.textContent = "📌";
    svg.appendChild(icon);

    /* Label */
    const label = el("text", {
      x: x + boxWidth / 2,
      y: y + 60,
      class: "label-node",
      "text-anchor": "middle",
      "font-size": "12px",
      "font-weight": "600",
      fill: "currentColor",
    });
    label.textContent = fase.label;
    svg.appendChild(label);

    /* Contagem */
    const contBadge = el("text", {
      x: x + boxWidth / 2,
      y: y + 85,
      class: "count-badge",
      "text-anchor": "middle",
      "font-size": "14px",
      "font-weight": "700",
      fill: fase.cor,
    });
    contBadge.textContent = count;
    svg.appendChild(contBadge);

    /* Conexão para próximo nó (se não é último) */
    if (idx < fases.length - 1) {
      const connX1 = x + boxWidth;
      const connX2 = x + spacing;
      const connY = y + boxHeight / 2;

      /* Seta Bezier animada */
      const path = el("path", {
        d: `M ${connX1} ${connY} Q ${(connX1 + connX2) / 2} ${connY} ${connX2} ${connY}`,
        class: "arrow-conexao",
        style: `--index:${idx};`,
        stroke: "url(#gradSeta)",
        "stroke-width": "2.5",
        fill: "none",
        "marker-end": "url(#arrowhead)",
        "stroke-dasharray": "100",
        "stroke-dashoffset": "100",
      });
      svg.appendChild(path);
    }
  });

  /* Definir gradientes e arrowhead */
  const defs = el("defs");
  const gradSeta = el("linearGradient", { id: "gradSeta", x1: "0%", y1: "0%", x2: "100%", y2: "0%" });
  gradSeta.appendChild(el("stop", { offset: "0%", "stop-color": "var(--accent)" }));
  gradSeta.appendChild(el("stop", { offset: "100%", "stop-color": "var(--accent-strong)" }));
  defs.appendChild(gradSeta);

  const arrowhead = el("marker", { id: "arrowhead", markerWidth: "10", markerHeight: "10", refX: "9", refY: "3", orient: "auto" });
  arrowhead.appendChild(el("polygon", { points: "0 0, 10 3, 0 6", fill: "var(--accent-strong)" }));
  defs.appendChild(arrowhead);

  svg.insertBefore(defs, svg.firstChild);

  container.appendChild(svg);

  /* Resumo textual */
  const resumo = el("div", { class: "resumo-workflow" }, [
    el("div", { class: "resumo-item" }, [
      el("span", { class: "resumo-label", text: "Total em fluxo:" }),
      el("span", { class: "resumo-valor", text: String(Object.values(contagem).reduce((a, b) => a + b, 0)) }),
    ]),
    el("div", { class: "resumo-item" }, [
      el("span", { class: "resumo-label", text: "Gargalo:" }),
      el("span", { class: "resumo-valor", text: "Protocolo (15)" }),
    ]),
  ]);
  container.appendChild(resumo);

  return escalonar(container);
}

/* ==================== KPIs ANALÍTICOS 4K ==================== */
function slideKPIsAnalyticos() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados analíticos não disponíveis.")));

  const container = el("div", { class: "slide slide-kpis-analytics-4k" });

  /* Simular dados analíticos (virão do backend) */
  const kpis = [
    {
      id: "aceite",
      titulo: "Taxa de Aceite",
      valor: 68,
      unidade: "%",
      icone: "✓",
      serie: [45, 52, 48, 65, 71, 68],
      tendencia: "up",
      cor: "#10b981",
    },
    {
      id: "dias",
      titulo: "Dias até Publicação",
      valor: 187,
      unidade: "dias",
      icone: "⏱",
      serie: [245, 210, 198, 185, 190, 187],
      tendencia: "down",
      cor: "#3b82f6",
    },
    {
      id: "citacoes",
      titulo: "Citações/Artigo",
      valor: 12,
      unidade: "cit",
      icone: "📊",
      serie: [8, 9, 10, 11, 11.5, 12],
      tendencia: "up",
      cor: "#8b5cf6",
    },
    {
      id: "produtividade",
      titulo: "Produtividade Equipe",
      valor: 3.2,
      unidade: "art/pes",
      icone: "👥",
      serie: [2.1, 2.4, 2.7, 2.9, 3.1, 3.2],
      tendencia: "up",
      cor: "#f59e0b",
    },
  ];

  const grid = el("div", { class: "grid-kpis-4k" });

  kpis.forEach(kpi => {
    const card = el("div", { class: "card-kpi-4k", "data-kpi": kpi.id, style: `--cor-kpi:${kpi.cor};` });

    /* Header com ícone */
    const header = el("div", { class: "header-kpi" }, [
      el("span", { class: "icone-kpi", text: kpi.icone }),
      el("span", { class: "titulo-kpi", text: kpi.titulo }),
    ]);
    card.appendChild(header);

    /* Valor grande (CountUp animation) */
    const valueContainer = el("div", { class: "value-container-kpi" });
    const value = el("span", { class: "valor-kpi", "data-valor": kpi.valor, "data-unidade": kpi.unidade });
    value.textContent = "0" + kpi.unidade;
    valueContainer.appendChild(value);
    card.appendChild(valueContainer);

    /* Mini sparkline (gráfico de série) */
    const sparkSvg = el("svg", { class: "sparkline-kpi", viewBox: "0 0 120 40" });
    const points = kpi.serie.map((v, i) => {
      const minVal = Math.min(...kpi.serie);
      const maxVal = Math.max(...kpi.serie);
      const range = maxVal - minVal || 1;
      const x = (i / (kpi.serie.length - 1)) * 110 + 5;
      const y = 40 - ((v - minVal) / range) * 30 - 5;
      return `${x},${y}`;
    }).join(" ");
    const polyline = el("polyline", { points, class: "sparkline-line", fill: "none", stroke: kpi.cor, "stroke-width": "2" });
    sparkSvg.appendChild(polyline);
    card.appendChild(sparkSvg);

    /* Indicador de tendência */
    const tendencia = el("div", { class: "tendencia-kpi", "data-tendencia": kpi.tendencia });
    tendencia.textContent = kpi.tendencia === "up" ? "↑ +5%" : "↓ -3%";
    card.appendChild(tendencia);

    grid.appendChild(card);

    /* Disparar CountUp animation quando card entra na tela */
    setTimeout(() => {
      value.style.animation = `countup-kpi 1s ease-out`;
      value.addEventListener("animationstart", () => {
        let current = 0;
        const target = kpi.valor;
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          current = Math.round(progress * target * 10) / 10;
          value.textContent = current + kpi.unidade;
          if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
      });
    }, 100);
  });

  container.appendChild(grid);

  return escalonar(container);
}

/* Exportar funções para mural.js */
if (typeof window !== "undefined") {
  window.slidePesquisasLinhas3D = slidePesquisasLinhas3D;
  window.slideOrganograma3D = slideOrganograma3D;
  window.slideFrameworkN8n = slideFrameworkN8n;
  window.slideKPIsAnalyticos = slideKPIsAnalyticos;
}
