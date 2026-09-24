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
function slidePesquisasLinhas3D() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Linhas de pesquisa ainda não carregadas.")));

  const linhas = t.linhas || [];
  if (!linhas.length) return escalonar(el("div", { class: "slide" }, vazio("Nenhuma linha de pesquisa cadastrada.")));

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
  filtroGlow.appendChild(elSvg("feGaussianBlur", { "in": "SourceGraphic", stdDeviation: "4" }));
  defs.appendChild(filtroGlow);
  svg.appendChild(defs);

  const centerX = 600, centerY = 400;
  /* O raio cresce com o número de linhas cadastradas -- fixo em 200px,
     o espaçamento angular entre nós encolhia conforme mais linhas de
     pesquisa eram criadas, até os rótulos se sobreporem. Limitado a
     300 para não estourar o viewBox (o centro está a 400px da borda). */
  const radius = Math.min(300, Math.max(160, 26 * linhas.length));
  /* Fonte do rótulo também encolhe com muitos nós, para caber no espaço
     angular menor entre eles. */
  const fontLabel = linhas.length > 12 ? 9 : linhas.length > 8 ? 10 : 11;

  linhas.forEach((linha, idx) => {
    const angle = (idx / linhas.length) * Math.PI * 2;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    const n_artigos = linha.artigos || 0;
    const taxa_pub = linha.taxa_publicacao || 0;

    const nodeRadius = Math.max(20, Math.min(60, 20 + (n_artigos / 5)));
    const strokeColor = taxa_pub > 0.8 ? "var(--good)" : taxa_pub > 0.5 ? "var(--warning)" : "var(--critical)";

    /* Linha do centro até o nó (Bezier com animação) */
    const line = elSvg("path", {
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

    /* Nó central (círculo com glow) */
    const circle = elSvg("circle", {
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
    const label = elSvg("text", {
      x: x,
      y: y + nodeRadius + 25,
      class: "label-linha-pesquisa",
      "text-anchor": "middle",
      fill: "currentColor",
      "font-size": fontLabel + "px",
      "font-weight": "600",
      style: `--index:${idx};`,
    });
    label.textContent = cortar(linha.nome, 20);
    svg.appendChild(label);

    /* Badge com número de artigos */
    const badge = elSvg("text", {
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
  const org = t && t.organograma;
  if (!org || !(org.people || []).length) {
    return escalonar(el("div", { class: "slide" }, vazio("Nenhuma pessoa do LAPE cadastrada.")));
  }

  const container = el("div", { class: "slide slide-organograma-3d" });

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

  const porId = {};
  (org.people || []).forEach(function (p) { porId[p.id] = p; });
  const filhosDe = {};
  (org.edges || []).forEach(function (e) {
    if (!porId[e.from] || !porId[e.to]) return;
    (filhosDe[e.from] = filhosDe[e.from] || []).push({ to: e.to, kind: e.kind });
  });

  // A mesma ordem de VINCULOS_ICONE, nomeada: e a ordem em que os grupos
  // aparecem quando um galho vira secao tematica em vez de fileira.
  const ORDEM_VINCULO = Object.keys(VINCULOS_ICONE);

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

  /* Um galho pequeno continua árvore, com o conector visual clássico (ver
     CSS .ramo-organograma) -- é o que deixa visível QUEM orienta QUEM.
     Um galho grande (a coordenação com doze orientandos, por exemplo) vira
     seções por vínculo -- doutorando, mestrando, bolsista... -- porque
     doze cartões numa fileira só é exatamente o que saía da tela: em vez
     de cortar ou empurrar pra rolagem horizontal, agrupa por tema, que é
     como a própria equipe se entende. Cinco é o limite: menos que isso, a
     linha de conexão ainda cabe; mais, quebra em grupo. Quem tem
     orientando próprio dentro de um grupo (a coorientação de mestrando
     com bolsista) continua a árvore dali, então a coorientação não
     desaparece dentro do agrupamento. */
  const LIMITE_FILEIRA = 5;

  function noArvore(id, profundidade) {
    const pessoa = porId[id];
    if (!pessoa) return null;
    const filhos = (filhosDe[id] || []).map(function (f) { return porId[f.to]; }).filter(Boolean);
    const no = el("div", { class: "no-organograma" }, [cartaoPessoa(pessoa)]);
    if (!filhos.length || profundidade >= 3) return no;
    if (filhos.length > LIMITE_FILEIRA) {
      no.appendChild(agruparPorVinculo(filhos, profundidade));
    } else {
      const galhos = el("div", { class: "ramo-organograma" },
        filhos.map(function (p) { return noArvore(p.id, profundidade + 1); }).filter(Boolean));
      no.appendChild(galhos);
    }
    return no;
  }

  /* As pessoas de um galho grande (ou os avulsos), em seções por vínculo
     -- cada uma com ícone, tom e legenda temática, no mesmo formato que
     "Sem orientador declarado" já usava. */
  function agruparPorVinculo(pessoas, profundidade) {
    const porRole = {};
    pessoas.forEach(function (p) {
      const r = p.role || "sem_vinculo";
      (porRole[r] = porRole[r] || []).push(p);
    });
    const grupos = ORDEM_VINCULO.filter(function (r) { return (porRole[r] || []).length; })
      .map(function (r) {
        const [icone, tom] = VINCULOS_ICONE[r] || VINCULOS_ICONE.sem_vinculo;
        const gente = porRole[r];
        return el("div", { class: "grupo-vinculo-organograma", "data-tom": tom }, [
          el("div", { class: "titulo-grupo" }, [
            Icons.badge(icone, tom, 20),
            el("span", { text: (gente[0].role_label || r) + " (" + gente.length + ")" }),
          ]),
          el("div", { class: "pessoas-container" }, gente.map(function (p) {
            // continua a arvore se a pessoa do grupo tambem orienta alguem
            // (coorientacao), em vez de esconder o galho dela por estar
            // dentro de um agrupamento
            return (filhosDe[p.id] || []).length && profundidade + 1 < 3
              ? noArvore(p.id, profundidade + 1)
              : el("div", { class: "no-organograma" }, [cartaoPessoa(p)]);
          })),
        ]);
      });
    return el("div", { class: "grupos-vinculo-organograma" }, grupos);
  }

  const raizes = (org.roots || []).map(function (id) { return noArvore(id, 0); }).filter(Boolean);
  const arvore = el("div", { class: "arvore-organograma" }, raizes);
  container.appendChild(arvore);

  /* Quem não tem vínculo declarado nem aparece como raiz nem como galho
     (perfil sem role e sem orientador) ainda tem de aparecer em algum
     lugar -- um organograma que descarta gente por falta de campo mente
     por omissão. */
  const naArvore = new Set();
  function marcar(id) {
    naArvore.add(id);
    (filhosDe[id] || []).forEach(function (f) { marcar(f.to); });
  }
  (org.roots || []).forEach(marcar);
  const avulsos = (org.people || []).filter(function (p) { return !naArvore.has(p.id); });
  if (avulsos.length) {
    container.appendChild(el("div", { class: "avulsos-organograma" }, [
      el("div", { class: "titulo-secao-avulsos" }, [
        Icons.badge("pessoas", "azul", 18),
        el("span", { text: "Sem orientador declarado" }),
      ]),
      agruparPorVinculo(avulsos, 3),
    ]));
  }

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
  const linhas = (cit.linhas || []).slice().sort(function (a, b) {
    return (b.media_citacoes || 0) - (a.media_citacoes || 0);
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
      el("div", { class: "metric-value", text: C.fmt(resumo.total_citacoes) }),
      el("div", { class: "metric-meta", text: C.fmt(resumo.total_artigos) + " artigo(s) com dados" }),
    ]),
    el("div", { class: "metric-card metric-media" }, [
      el("div", { class: "metric-label", text: "Média por artigo" }),
      el("div", { class: "metric-value", text: C.fmt(resumo.media_citacoes) }),
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

  if (linhas.length) {
    const grid = el("div", { class: "bases-linhas" });
    linhas.forEach(function (linha) {
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

  const artigos = [];
  linhas.forEach(function (l) {
    (l.artigos || []).forEach(function (a) { artigos.push(Object.assign({}, a, { linha: l.nome })); });
  });
  artigos.sort(function (a, b) { return (b.citacoes || 0) - (a.citacoes || 0); });
  const top = artigos.slice(0, 5);

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
