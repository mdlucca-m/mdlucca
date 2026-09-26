/* ==========================================================================
   LAPE — Extensões de Gráficos Avançados
   Adiciona visualizações: Ternário, Sunburst, Pareto, Scatter 3D
   ========================================================================== */
"use strict";

const ChartsEnhanced = (function () {
  const NS = "http://www.w3.org/2000/svg";

  /* As mesmas 8 cores categóricas do resto do mural (theme.css), em vez de
     cores cruas geradas por hsl() -- senão esses 4 gráficos destoam do
     tema escolhido (claro/escuro/paleta) e do resto das telas. */
  const SERIES = ["--series-1", "--series-2", "--series-3", "--series-4",
    "--series-5", "--series-6", "--series-7", "--series-8"];
  function corSerie(i) { return `var(${SERIES[i % SERIES.length]})`; }

  /* ======================== Gráfico Ternário ======================== */
  function ternario(dados) {
    /**
     * Plota 3 dimensões num triangulo (condição × intervenção × desfecho)
     * Cada ponto tem tamanho proporcional ao número de artigos
     */
    if (!dados || dados.length === 0) return null;

    const w = 600, h = 520;
    const margin = 60;
    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");

    // Altura do triângulo equilátero
    const triH = h - 2 * margin;
    const triW = triH * Math.sqrt(3) / 2;

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "plot ternario");

    // Desenha triângulo base
    const cx = w / 2;
    const cy = h / 2 + margin / 2;
    const pontos = [
      [cx, cy - triH * 0.577],  // topo
      [cx - triW / 2, cy + triH * 0.289],  // esquerda
      [cx + triW / 2, cy + triH * 0.289],  // direita
    ];

    // Triângulo de fundo
    const triangle = document.createElementNS(NS, "polygon");
    triangle.setAttribute("points", pontos.map(p => p.join(",")).join(" "));
    triangle.setAttribute("fill", "none");
    triangle.setAttribute("stroke", "var(--border-strong)");
    triangle.setAttribute("stroke-width", "2");
    svg.appendChild(triangle);

    // Labels dos eixos
    const labels = ["Aplicação", "Intervenção", "Desfecho"];
    const labelPos = [
      [pontos[0][0], pontos[0][1] - 30],
      [pontos[1][0] - 50, pontos[1][1] + 20],
      [pontos[2][0] + 50, pontos[2][1] + 20],
    ];

    labelPos.forEach((pos, i) => {
      const text = document.createElementNS(NS, "text");
      text.setAttribute("x", pos[0]);
      text.setAttribute("y", pos[1]);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-weight", "bold");
      text.setAttribute("fill", "var(--ink)");
      text.textContent = labels[i];
      svg.appendChild(text);
    });

    // Plota pontos
    dados.forEach((d, i) => {
      // Normaliza baricêntricas
      const a = (d.aplicacao || 0) / 100;
      const b = (d.intervencao || 0) / 100;
      const c = (d.desfecho || 0) / 100;
      const sum = a + b + c || 1;
      const na = a / sum, nb = b / sum, nc = c / sum;

      // Converte para coordenadas Cartesianas
      const x = pontos[0][0] * na + pontos[1][0] * nb + pontos[2][0] * nc;
      const y = pontos[0][1] * na + pontos[1][1] * nb + pontos[2][1] * nc;

      const circle = document.createElementNS(NS, "circle");
      const r = Math.sqrt(d.artigos || 1) * 3;
      circle.setAttribute("cx", x);
      circle.setAttribute("cy", y);
      circle.setAttribute("r", r);
      circle.setAttribute("fill", corSerie(i));
      circle.setAttribute("opacity", "0.7");
      circle.setAttribute("stroke", "var(--surface)");
      circle.setAttribute("stroke-width", "2");

      circle.addEventListener("mouseenter", () => {
        circle.setAttribute("opacity", "1");
        circle.setAttribute("stroke-width", "3");
      });
      circle.addEventListener("mouseleave", () => {
        circle.setAttribute("opacity", "0.7");
        circle.setAttribute("stroke-width", "2");
      });

      const title = document.createElementNS(NS, "title");
      title.textContent = `${d.nome || "Item"}: ${d.artigos || 0} artigos`;
      circle.appendChild(title);

      svg.appendChild(circle);
    });

    fig.appendChild(svg);
    return fig;
  }

  /* ======================== Gráfico de Pareto ======================== */
  function pareto(dados) {
    /**
     * Mostra valores em barras (80/20 rule)
     * Linha de acumulada em cima
     */
    if (!dados || dados.length === 0) return null;

    const w = 800, h = 440;
    /* `bottom` maior: sobra espaço para o nome de cada linha, girado sob
       o eixo -- antes o gráfico não tinha rótulo NENHUM embaixo das
       barras, então não dava pra saber qual barra era qual linha sem
       adivinhar pela cor. */
    const margin = { top: 40, right: 40, bottom: 110, left: 60 };
    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");

    // Ordena por valor decrescente
    const sorted = [...dados].sort((a, b) => (b.valor || 0) - (a.valor || 0));
    const total = sorted.reduce((s, d) => s + (d.valor || 0), 0);

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "plot pareto");

    const chartW = w - margin.left - margin.right;
    const chartH = h - margin.top - margin.bottom;

    // Escala
    const maxVal = sorted[0]?.valor || 1;
    const scaleX = chartW / sorted.length;
    const scaleY = chartH / maxVal;

    // Grupo para barras
    const barsGroup = document.createElementNS(NS, "g");
    barsGroup.setAttribute("transform", `translate(${margin.left},${margin.top})`);

    /* Primeiro índice em que o acumulado CRUZA 80% -- um "=== 80" exato
       quase nunca acontece com contagens inteiras (112 de 160 é 70%; a
       próxima linha já pula para 86%, 80 nunca aparece no meio), e a
       "linha vermelha" que o texto ao lado promete nunca era desenhada.
       Cruzar o limiar, em vez de acertar o número exato, é a leitura
       correta da regra 80/20. */
    let acumulado = 0, corteIdx = -1;
    for (let i = 0; i < sorted.length; i++) {
      acumulado += sorted[i].valor || 0;
      if (corteIdx === -1 && acumulado / total >= 0.8) corteIdx = i;
    }

    acumulado = 0;
    sorted.forEach((d, i) => {
      const val = d.valor || 0;
      const barH = val * scaleY;
      const x = i * scaleX;
      const y = chartH - barH;
      const nome = d.nome || "Item";
      acumulado += val;
      const pctAqui = Math.round((acumulado / total) * 100);

      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", x + 2);
      rect.setAttribute("y", y);
      rect.setAttribute("width", scaleX - 4);
      rect.setAttribute("height", barH);
      rect.setAttribute("fill", corSerie(i));
      rect.setAttribute("opacity", "0.8");
      const dica = document.createElementNS(NS, "title");
      dica.textContent = `${nome}: ${val} artigo(s) — ${pctAqui}% acumulado`;
      rect.appendChild(dica);
      barsGroup.appendChild(rect);

      // valor em cima da barra -- sem isso, só dava pra estimar a
      // contagem pela régua do eixo Y, a olho, a três metros de distância
      const valorTxt = document.createElementNS(NS, "text");
      valorTxt.setAttribute("x", x + scaleX / 2);
      valorTxt.setAttribute("y", Math.max(14, y - 8));
      valorTxt.setAttribute("text-anchor", "middle");
      valorTxt.setAttribute("font-size", "15");
      valorTxt.setAttribute("font-weight", "700");
      valorTxt.setAttribute("fill", "var(--ink)");
      valorTxt.textContent = val;
      barsGroup.appendChild(valorTxt);

      // nome da linha, girado sob o eixo -- truncado só como ÚLTIMO
      // recurso (a dica do mouse sempre tem o nome inteiro)
      const rotuloTxt = nome.length > 26 ? nome.slice(0, 25) + "…" : nome;
      const rotulo = document.createElementNS(NS, "text");
      rotulo.setAttribute("x", x + scaleX / 2);
      rotulo.setAttribute("y", chartH + 16);
      rotulo.setAttribute("text-anchor", "end");
      rotulo.setAttribute("font-size", "12");
      rotulo.setAttribute("fill", "var(--ink-2)");
      rotulo.setAttribute("transform", `rotate(-40 ${x + scaleX / 2} ${chartH + 16})`);
      rotulo.textContent = rotuloTxt;
      const dicaRotulo = document.createElementNS(NS, "title");
      dicaRotulo.textContent = nome;
      rotulo.appendChild(dicaRotulo);
      barsGroup.appendChild(rotulo);

      if (i === corteIdx) {
        // Marca a linha 80/20, na fronteira direita da barra que cruzou
        const lineX = x + scaleX;
        const line = document.createElementNS(NS, "line");
        line.setAttribute("x1", lineX);
        line.setAttribute("y1", -12);
        line.setAttribute("x2", lineX);
        line.setAttribute("y2", chartH);
        line.setAttribute("stroke", "var(--critical)");
        line.setAttribute("stroke-width", "2");
        line.setAttribute("stroke-dasharray", "5,5");
        barsGroup.appendChild(line);

        const marca = document.createElementNS(NS, "text");
        marca.setAttribute("x", lineX);
        marca.setAttribute("y", -16);
        marca.setAttribute("text-anchor", "middle");
        marca.setAttribute("font-size", "12");
        marca.setAttribute("font-weight", "700");
        marca.setAttribute("fill", "var(--critical)");
        marca.textContent = "80%";
        barsGroup.appendChild(marca);
      }
    });

    // Linha acumulada
    const line = document.createElementNS(NS, "polyline");
    let points = [];
    acumulado = 0;
    sorted.forEach((d, i) => {
      acumulado += d.valor || 0;
      const pct = (acumulado / total) * 100;
      const x = i * scaleX + scaleX / 2;
      const y = chartH - (pct / 100) * chartH;
      points.push(`${x},${y}`);
    });
    line.setAttribute("points", points.join(" "));
    line.setAttribute("fill", "none");
    line.setAttribute("stroke", "var(--ink-2)");
    line.setAttribute("stroke-width", "3");
    barsGroup.appendChild(line);

    svg.appendChild(barsGroup);
    fig.appendChild(svg);
    return fig;
  }

  /* ======================== Sunburst ======================== */
  /* Anel oco (não mais uma pizza cheia) com o total real no centro,
     rótulo de porcentagem só nas fatias grandes o bastante pra não se
     sobrepor (era o "1% / 1%" ilegível de antes), e o nome das
     instituições reais de cada país na dica do mouse -- sem inventar
     proporção nenhuma entre elas, porque o dado que existe é só o
     nome, não a contagem por instituição. */
  function sunburst(dados, raio = 200) {
    if (!dados || dados.length === 0) return null;

    const w = 500, h = 500;
    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "plot sunburst");

    const cx = w / 2, cy = h / 2;
    const raioInterno = raio * 0.55;
    const total = dados.reduce((s, d) => s + (d.valor || 0), 0) || 1;

    const grupo = document.createElementNS(NS, "g");
    svg.appendChild(grupo);

    /* começa no topo (meio-dia do relógio) e anda em sentido horário --
       é a leitura que a maioria já treinou em qualquer pizza/donut */
    let angle = -Math.PI / 2;
    dados.forEach((d, i) => {
      const fatia = (d.valor / total) * Math.PI * 2;
      const meio = angle + fatia / 2;
      const largeArc = fatia > Math.PI ? 1 : 0;
      const cor = corSerie(i);

      const xOut1 = cx + raio * Math.cos(angle), yOut1 = cy + raio * Math.sin(angle);
      const xOut2 = cx + raio * Math.cos(angle + fatia), yOut2 = cy + raio * Math.sin(angle + fatia);
      const xIn1 = cx + raioInterno * Math.cos(angle + fatia), yIn1 = cy + raioInterno * Math.sin(angle + fatia);
      const xIn2 = cx + raioInterno * Math.cos(angle), yIn2 = cy + raioInterno * Math.sin(angle);

      const caminho = `M ${xOut1} ${yOut1} A ${raio} ${raio} 0 ${largeArc} 1 ${xOut2} ${yOut2} `
        + `L ${xIn1} ${yIn1} A ${raioInterno} ${raioInterno} 0 ${largeArc} 0 ${xIn2} ${yIn2} Z`;

      const path = document.createElementNS(NS, "path");
      path.setAttribute("d", caminho);
      path.setAttribute("fill", cor);
      path.setAttribute("stroke", "var(--surface)");
      path.setAttribute("stroke-width", "2");
      path.setAttribute("class", "fatia-sunburst");
      path.setAttribute("data-nome", d.nome || "");
      path.style.setProperty("--i", i);
      path.style.setProperty("--dx", (Math.cos(meio) * 7).toFixed(2));
      path.style.setProperty("--dy", (Math.sin(meio) * 7).toFixed(2));
      path.style.setProperty("--cor", cor);

      const pct = Math.round((d.valor / total) * 100);
      const instituicoes = (d.instituicoes || []).filter(Boolean);
      const dica = instituicoes.length
        ? `\nInstituições: ${instituicoes.slice(0, 3).join(", ")}${instituicoes.length > 3 ? "…" : ""}`
        : "";
      const title = document.createElementNS(NS, "title");
      title.textContent = `${d.nome || "Item"}: ${d.valor || 0} artigo(s) (${pct}%)${dica}`;
      path.appendChild(title);

      path.addEventListener("mouseenter", () => destacarFatiaSunburst(svg, d.nome, true));
      path.addEventListener("mouseleave", () => destacarFatiaSunburst(svg, d.nome, false));

      grupo.appendChild(path);

      /* rótulo só nas fatias com espaço de sobra -- abaixo de 6% dois
         rótulos vizinhos colidiam e viravam "1%1%" ilegível */
      if (pct >= 6) {
        const labelR = (raio + raioInterno) / 2;
        const text = document.createElementNS(NS, "text");
        text.setAttribute("x", cx + labelR * Math.cos(meio));
        text.setAttribute("y", cy + labelR * Math.sin(meio));
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dy", "0.32em");
        text.setAttribute("font-size", "13");
        text.setAttribute("fill", "white");
        text.setAttribute("font-weight", "700");
        text.setAttribute("class", "rotulo-sunburst");
        text.style.setProperty("--i", i);
        text.textContent = `${pct}%`;
        grupo.appendChild(text);
      }

      angle += fatia;
    });

    const centroNum = document.createElementNS(NS, "text");
    centroNum.setAttribute("x", cx); centroNum.setAttribute("y", cy - 6);
    centroNum.setAttribute("text-anchor", "middle");
    centroNum.setAttribute("class", "sunburst-centro-num");
    centroNum.textContent = String(total);
    svg.appendChild(centroNum);
    const centroRotulo = document.createElementNS(NS, "text");
    centroRotulo.setAttribute("x", cx); centroRotulo.setAttribute("y", cy + 17);
    centroRotulo.setAttribute("text-anchor", "middle");
    centroRotulo.setAttribute("class", "sunburst-centro-rot");
    centroRotulo.textContent = "artigos";
    svg.appendChild(centroRotulo);

    fig.appendChild(svg);
    return fig;
  }

  /* Realce cruzado: usado pelo hover interno da fatia, e também de fora
     (o mural liga isso ao passar o mouse na lista "Top 6", pra ligar a
     lista ao desenho). */
  function destacarFatiaSunburst(svg, nome, ligado) {
    svg.querySelectorAll(".fatia-sunburst").forEach(function (p) {
      const ehEsta = p.getAttribute("data-nome") === nome;
      p.classList.toggle("ativa", ehEsta && ligado);
      p.classList.toggle("apagada", !ehEsta && ligado);
    });
  }

  /* Gauge de diagnóstico: velocímetro de meia-lua, sem lib nenhuma -- virou
     o padrão do laboratório para "um número contra uma escala" (achado ao
     vivo, referência que o Mateus mandou de um painel de KPI real com
     faixas coloridas + ponteiro). Dois modos, escolhidos pelo CHAMADOR:

     - qualitativo (padrão): a escala inteira dividida em faixas de
       julgamento (Ruim/Regular/Bom/Muito Bom/Ótimo por padrão, ou
       `opts.faixas` customizado) -- serve para uma TAXA (aceite,
       cumprimento) que se lê como "bom ou ruim", não como progresso rumo a
       um alvo.
     - meta (`opts.meta` presente): a escala vira progresso (cor de destaque
       até o valor atual, cinza depois) com um marcador no valor da meta e
       a frase "faltam X% para a meta" -- serve para o que TEM alvo
       declarado (publicações do ano, banco de horas).

     Cada faixa/ponteiro é um arco calculado à mão (sem pathLength/dasharray
     -- que só serve para UM arco só): `ponto(t)` percorre a mesma
     parametrização de 0 (ponta esquerda) a 1 (ponta direita) usada tanto
     para desenhar as faixas quanto para posicionar a ponta do ponteiro,
     então os dois nunca desalinham entre si.
     `opts.critico` liga o pulso vermelho no ponteiro -- decidido pelo
     CHAMADOR, com um número real (ex.: 0% de aceite com decisões de
     verdade no período), nunca aqui dentro. */
  function gaugeDiagnostico(valor, opts) {
    const o = opts || {};
    const w = 320, h = 244, cx = w / 2, cy = 172, raio = 112, espessura = 24;
    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "plot gauge-diagnostico" + (o.critico ? " gauge-critico" : ""));

    function ponto(t, r) {
      const rr = r === undefined ? raio : r;
      return { x: cx - rr * Math.cos(Math.PI * t), y: cy - rr * Math.sin(Math.PI * t) };
    }
    function texto(x, y, conteudo, tamanho, cor, peso) {
      const el = document.createElementNS(NS, "text");
      el.setAttribute("x", x); el.setAttribute("y", y);
      el.setAttribute("text-anchor", "middle");
      el.setAttribute("font-size", String(tamanho));
      el.setAttribute("font-weight", String(peso || 600));
      el.setAttribute("fill", cor);
      el.textContent = conteudo;
      return el;
    }

    const temMeta = o.meta !== undefined && o.meta !== null && isFinite(o.meta);
    const faixasPadrao = [
      { ate: 20, cor: "var(--critical)", rotulo: "Ruim" },
      { ate: 40, cor: "var(--serious)", rotulo: "Regular" },
      { ate: 60, cor: "var(--warning)", rotulo: "Bom" },
      { ate: 80, cor: "var(--series-4)", rotulo: "Muito Bom" },
      { ate: 100, cor: "var(--good)", rotulo: "Ótimo" },
    ];
    const faixas = o.faixas || (temMeta
      ? [{ ate: Math.max(0, Math.min(100, o.meta)), cor: "var(--accent-strong)" },
        { ate: 100, cor: "var(--border)" }]
      : faixasPadrao);

    // faixas: arcos separados (não um só com dasharray) -- cada faixa tem
    // COR própria, então precisa ser um <path> próprio; um respiro de 2px
    // (mesma lógica angular da rosca em donut()) separa uma da seguinte.
    let cursor = 0;
    faixas.forEach(function (faixa) {
      const t0 = cursor / 100, t1raw = Math.max(cursor, faixa.ate) / 100;
      const pad = Math.min(0.008, (t1raw - t0) / 4);
      const t1 = Math.max(t0, t1raw - (t1raw < 1 ? pad : 0));
      const tIni = t0 + (t0 > 0 ? pad : 0);
      if (t1 > tIni) {
        const p0 = ponto(tIni), p1 = ponto(t1);
        const large = (t1 - tIni) > 0.5 ? 1 : 0;
        const arco = document.createElementNS(NS, "path");
        arco.setAttribute("d", `M ${p0.x} ${p0.y} A ${raio} ${raio} 0 ${large} 1 ${p1.x} ${p1.y}`);
        arco.setAttribute("fill", "none");
        arco.setAttribute("stroke", faixa.cor);
        arco.setAttribute("stroke-width", String(espessura));
        svg.appendChild(arco);
      }
      cursor = faixa.ate;
    });

    // rótulos das pontas da escala -- sem eles um velocímetro sozinho não
    // diz se a régua vai de 0 a 100 ou de 0 a outra coisa qualquer
    svg.appendChild(texto(ponto(0.02, raio + 20).x, cy + 16, "0%", 10, "var(--ink-muted)", 500));
    svg.appendChild(texto(ponto(0.98, raio + 20).x, cy + 16, "100%", 10, "var(--ink-muted)", 500));

    // a marca da meta só é desenhada longe da ponta direita -- rente à
    // ponta ela cairia em cima do rótulo "100%" que já está ali (meta ===
    // 100 é o caso comum de "a meta É o fim da escala", ex.: publicações
    // do ano expressas como % da própria meta).
    if (temMeta && o.meta < 98.5) {
      const tMeta = Math.max(0, Math.min(100, o.meta)) / 100;
      const p0 = ponto(tMeta, raio - espessura / 2 - 2), p1 = ponto(tMeta, raio + espessura / 2 + 8);
      const marca = document.createElementNS(NS, "line");
      marca.setAttribute("x1", p0.x); marca.setAttribute("y1", p0.y);
      marca.setAttribute("x2", p1.x); marca.setAttribute("y2", p1.y);
      marca.setAttribute("stroke", "var(--ink)"); marca.setAttribute("stroke-width", "2.5");
      marca.setAttribute("class", "gauge-marca-meta");
      svg.appendChild(marca);
      const pRotulo = ponto(tMeta, raio + espessura / 2 + 20);
      svg.appendChild(texto(pRotulo.x, pRotulo.y + 3, "meta " + fmt(o.meta) + "%", 10, "var(--ink)", 700));
    }

    const temValor = valor !== null && valor !== undefined && isFinite(valor);
    if (temValor) {
      const v = Math.max(0, Math.min(100, valor)) / 100;
      const ponta = ponto(v, raio - espessura / 2 - 14);
      const agulha = document.createElementNS(NS, "line");
      agulha.setAttribute("x1", cx); agulha.setAttribute("y1", cy);
      agulha.setAttribute("x2", ponta.x); agulha.setAttribute("y2", ponta.y);
      agulha.setAttribute("stroke", "var(--ink)"); agulha.setAttribute("stroke-width", "4");
      agulha.setAttribute("stroke-linecap", "round");
      agulha.setAttribute("class", "gauge-agulha");
      svg.appendChild(agulha);
      const cubo = document.createElementNS(NS, "circle");
      cubo.setAttribute("cx", cx); cubo.setAttribute("cy", cy); cubo.setAttribute("r", "7");
      cubo.setAttribute("fill", "var(--ink)"); cubo.setAttribute("class", "gauge-cubo");
      svg.appendChild(cubo);
    }

    svg.appendChild(texto(cx, cy - 20, temValor ? fmt(valor) + "%" : "sem dado", 38,
      o.critico ? "var(--critical)" : "var(--ink)", 800));

    if (temMeta && temValor) {
      // `opts.fraseMeta` sobrepõe a frase automática -- necessário quando o
      // valor real não é uma porcentagem "de verdade" (contagem contra uma
      // meta, ex.: publicações do ano): a diferença em PONTOS da escala do
      // mostrador não é a diferença em unidades reais, e escrever uma
      // sozinha inventaria uma conta que ninguém pediu.
      const falta = o.meta - valor;
      const frase = o.fraseMeta || (falta > 0.05 ? "faltam " + fmt(falta) + "% para a meta" : "meta atingida");
      const bateu = o.fraseMeta ? !!o.metaAtingida : falta <= 0.05;
      svg.appendChild(texto(cx, cy + 6, frase, 12, bateu ? "var(--good)" : "var(--ink-2)", 700));
    } else if (!temMeta) {
      // qualitativo: o nome da própria faixa em que o valor caiu -- "63%"
      // sozinho não diz se é bom ou ruim para quem olha de longe
      if (temValor) {
        const faixaAtual = faixas.find(function (f) { return valor <= f.ate; }) || faixas[faixas.length - 1];
        if (faixaAtual.rotulo) svg.appendChild(texto(cx, cy + 6, faixaAtual.rotulo, 13, faixaAtual.cor, 700));
      }
    }

    if (o.rotulo) svg.appendChild(texto(cx, cy + 26, o.rotulo, 12, "var(--ink-2)", 600));
    if (o.nota) svg.appendChild(texto(cx, cy + 44, o.nota, 11, "var(--ink-muted)", 500));

    fig.appendChild(svg);
    return fig;
  }

  /* Funil líquido: sem depender de nenhuma lib de gráfico -- N trapézios
     (as etapas reais do pipeline, quantas forem) desaguando num tanque com
     recorte (clipPath) e uma onda animada em CSS por dentro. `estagios` é
     [etapa1, etapa2, ..., tanque] (2 ou mais); só o último vira tanque, os
     anteriores viram trapézios em sequência. `tanque.total` é o total do
     acervo (não o topo do funil) contra o qual o nível é calculado.

     A altura de cada trapézio é a mesma fração da zona do funil -- achado
     ao vivo: com posições fixas (uma etapa em 220→244, 24px de altura) uma
     etapa no meio virava uma tira ilegível sempre que houvesse mais de 2
     etapas antes do tanque. Dividir a zona do funil por `N` etapas garante
     que cada uma tenha espaço para número + rótulo, não importa quantas. */
  function funilLiquido(estagios) {
    if (!estagios || estagios.length < 2) return null;
    const etapas = estagios.slice(0, -1);
    const e3 = estagios[estagios.length - 1];
    const maiorFunil = Math.max(1, ...etapas.map(function (e) { return e.valor || 0; }));
    const fracaoLargura = (v) => 0.3 + 0.7 * Math.sqrt(Math.max(0, v || 0) / maiorFunil);
    const w = 420, h = 560, largMax = 320, cx = w / 2;
    const margemTopo = 26, margemBase = 40;
    const wBocaTanque = Math.max(70, largMax * 0.36);

    const alturaUtil = h - margemTopo - margemBase;
    const alturaTanque = Math.max(220, alturaUtil * 0.5);
    const alturaFunil = alturaUtil - alturaTanque;
    const alturaEtapa = alturaFunil / etapas.length;
    const yTanque0 = margemTopo + alturaFunil, yTanque1 = yTanque0 + alturaTanque;

    // larguras nas N+1 fronteiras: do topo da 1a etapa até a boca do
    // tanque, cada etapa intermediária pesada pelo próprio valor.
    const larguras = etapas.map(function (e) { return largMax * fracaoLargura(e.valor); });
    larguras.push(wBocaTanque);

    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "plot funil-liquido");

    /* Era um trapézio com anel 3D (elipse de "aro" + brilho vertical
       translúcido, para parecer um cilindro empilhado) -- achado ao vivo
       (referência que o Mateus mandou de um funil de verdade): a faixa
       chapada, sólida, sem relevo, é o que se lê rápido numa parede. O
       efeito 3D saiu; o trapézio agora é só a própria cor da etapa. */
    function trapezio(yTop, yBot, wTop, wBot, cor, nome, valor) {
      const pontos = [[cx - wTop / 2, yTop], [cx + wTop / 2, yTop],
        [cx + wBot / 2, yBot], [cx - wBot / 2, yBot]]
        .map(function (p) { return p.join(","); }).join(" ");
      const poly = document.createElementNS(NS, "polygon");
      poly.setAttribute("points", pontos);
      poly.setAttribute("fill", cor);
      const dica = document.createElementNS(NS, "title");
      dica.textContent = `${nome}: ${fmt(valor)} artigo(s)`;
      poly.appendChild(dica);
      return poly;
    }

    function rotuloEtapa(yTop, yBot, nome, valor) {
      const g = document.createElementNS(NS, "g");
      const yMeioEtapa = (yTop + yBot) / 2;
      const numero = document.createElementNS(NS, "text");
      numero.setAttribute("x", cx); numero.setAttribute("y", yMeioEtapa - 6);
      numero.setAttribute("text-anchor", "middle");
      numero.setAttribute("font-size", "17"); numero.setAttribute("font-weight", "800");
      numero.setAttribute("fill", "#fff");
      numero.textContent = fmt(valor);
      g.appendChild(numero);
      const rotulo = document.createElementNS(NS, "text");
      rotulo.setAttribute("x", cx); rotulo.setAttribute("y", yMeioEtapa + 15);
      rotulo.setAttribute("text-anchor", "middle");
      rotulo.setAttribute("font-size", "12"); rotulo.setAttribute("fill", "rgba(255,255,255,.88)");
      rotulo.textContent = nome;
      g.appendChild(rotulo);
      return g;
    }

    etapas.forEach(function (etapa, i) {
      const yTop = margemTopo + i * alturaEtapa, yBot = margemTopo + (i + 1) * alturaEtapa;
      const faixa = trapezio(yTop, yBot, larguras[i], larguras[i + 1], etapa.cor, etapa.nome, etapa.valor);
      // Um traço fino na cor do fundo separa uma faixa da seguinte -- a
      // mesma leitura de "bandas distintas" da referência, sem precisar
      // de relevo nenhum para diferenciá-las.
      faixa.setAttribute("stroke", "var(--surface)");
      faixa.setAttribute("stroke-width", "3");
      svg.appendChild(faixa);
      svg.appendChild(rotuloEtapa(yTop, yBot, etapa.nome, etapa.valor));
    });

    // Tanque -- contorno e recorte para a onda nunca vazar por fora dele
    const tankX = cx - wBocaTanque / 2, tankW = wBocaTanque;
    const tankId = "tanque-" + Math.random().toString(36).slice(2, 9);
    const clip = document.createElementNS(NS, "clipPath");
    clip.setAttribute("id", tankId);
    const clipRect = document.createElementNS(NS, "rect");
    clipRect.setAttribute("x", tankX); clipRect.setAttribute("y", yTanque0);
    clipRect.setAttribute("width", tankW); clipRect.setAttribute("height", yTanque1 - yTanque0);
    clipRect.setAttribute("rx", "8");
    clip.appendChild(clipRect);
    svg.appendChild(clip);

    const contorno = document.createElementNS(NS, "rect");
    contorno.setAttribute("x", tankX); contorno.setAttribute("y", yTanque0);
    contorno.setAttribute("width", tankW); contorno.setAttribute("height", yTanque1 - yTanque0);
    contorno.setAttribute("rx", "8");
    contorno.setAttribute("fill", "rgba(255,255,255,.04)");
    contorno.setAttribute("stroke", "rgba(255,255,255,.25)");
    svg.appendChild(contorno);

    // Nível do líquido: fração do TOTAL do acervo (e3.total), não do topo
    // do funil -- "publicados" se acumula ao longo de anos, e comparar
    // com a safra atual de "em escrita" faria o tanque passar de 100%
    // cheio, uma leitura sem sentido.
    const fracaoNivel = Math.max(0.05, Math.min(1,
      (e3.valor || 0) / Math.max(1, e3.total || maiorFunil)));
    const nivelY = yTanque1 - fracaoNivel * (yTanque1 - yTanque0);

    const ondaGrupo = document.createElementNS(NS, "g");
    ondaGrupo.setAttribute("clip-path", `url(#${tankId})`);
    const larguraOnda = tankW * 2;
    const passoOnda = larguraOnda / 4;
    const amplitude = 5;
    let d = `M ${tankX - larguraOnda / 2} ${nivelY}`;
    for (let i = 0; i <= 8; i++) {
      const x = tankX - larguraOnda / 2 + i * passoOnda;
      const y = nivelY + (i % 2 === 0 ? -amplitude : amplitude);
      d += ` Q ${x - passoOnda / 2} ${y} ${x} ${nivelY}`;
    }
    d += ` V ${yTanque1 + 6} H ${tankX - larguraOnda / 2} Z`;
    const ondaPath = document.createElementNS(NS, "path");
    ondaPath.setAttribute("d", d);
    ondaPath.setAttribute("fill", e3.cor);
    ondaPath.setAttribute("opacity", "0.88");
    ondaPath.setAttribute("class", "onda-liquida");
    ondaPath.style.setProperty("--onda-passo", passoOnda + "px");
    const dicaOnda = document.createElementNS(NS, "title");
    dicaOnda.textContent = `${e3.nome}: ${fmt(e3.valor)} de ${fmt(e3.total || maiorFunil)} artigo(s)`;
    ondaPath.appendChild(dicaOnda);
    ondaGrupo.appendChild(ondaPath);
    svg.appendChild(ondaGrupo);

    const valorTanque = document.createElementNS(NS, "text");
    valorTanque.setAttribute("x", cx); valorTanque.setAttribute("y", (yTanque0 + yTanque1) / 2 - 4);
    valorTanque.setAttribute("text-anchor", "middle");
    valorTanque.setAttribute("font-size", "38"); valorTanque.setAttribute("font-weight", "800");
    valorTanque.setAttribute("fill", "#fff");
    valorTanque.setAttribute("style", "text-shadow:0 1px 3px rgba(0,0,0,.4)");
    valorTanque.textContent = fmt(e3.valor);
    svg.appendChild(valorTanque);

    const rotuloTanque = document.createElementNS(NS, "text");
    rotuloTanque.setAttribute("x", cx); rotuloTanque.setAttribute("y", (yTanque0 + yTanque1) / 2 + 22);
    rotuloTanque.setAttribute("text-anchor", "middle");
    rotuloTanque.setAttribute("font-size", "13"); rotuloTanque.setAttribute("fill", "rgba(255,255,255,.92)");
    rotuloTanque.textContent = e3.nome;
    svg.appendChild(rotuloTanque);

    fig.appendChild(svg);
    return fig;
  }

  /* Globo neon: projeção ortográfica de verdade (mesma matemática do globo
     do ao vivo, `Globo.prototype.projetar` em aovivo.js), centrada na
     sede -- mas parada, sem laço de animação em JS. A "girada" vem de
     CSS 3D puro (perspective + rotateY no grupo inteiro): sem
     requestAnimationFrame, sem canvas, sem depender de nada novo. O ao
     vivo tem o globo que voa até cada país e espera pousar -- na parede
     ninguém espera isso (ver `rankingDePaises`), então aqui é só rotação
     ambiente contínua, sem parar em lugar nenhum.

     `sede` é {nome, latitude, longitude}; `paises` é a lista real
     (pais, iso, n, latitude, longitude), já ordenada por quem chama. A
     espessura e o brilho do arco de cada país são proporcionais a `n`. */
  function globoNeon(sede, paises, opts) {
    if (!sede || !paises || !paises.length) return null;
    const o = opts || {};
    const w = 440, h = 440, cx = w / 2, cy = h / 2, R = 190;
    const fig = document.createElement("figure");
    fig.setAttribute("class", "chart");
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "plot globo-neon");

    const lon0 = sede.longitude || 0, lat0 = Math.max(-45, Math.min(45, sede.latitude || 0));
    function projetar(lon, lat) {
      const rad = Math.PI / 180;
      const dl = (lon - lon0) * rad, la = lat * rad, la0 = lat0 * rad;
      return {
        x: cx + R * Math.cos(la) * Math.sin(dl),
        y: cy - R * (Math.cos(la0) * Math.sin(la) - Math.sin(la0) * Math.cos(la) * Math.cos(dl)),
      };
    }

    // Grupo que gira em CSS (transform-style: preserve-3d no wrapper via CSS)
    const grupo = document.createElementNS(NS, "g");
    grupo.setAttribute("class", "globo-neon-esfera");

    const oceano = document.createElementNS(NS, "circle");
    oceano.setAttribute("cx", cx); oceano.setAttribute("cy", cy); oceano.setAttribute("r", R);
    oceano.setAttribute("class", "globo-neon-oceano");
    grupo.appendChild(oceano);

    // Meridianos/paralelos, só pra dar leitura de esfera -- mesmo raciocínio
    // visual do ao vivo, em poucas linhas fixas (sem recalcular por quadro).
    [-120, -60, 0, 60, 120].forEach(function (lon) {
      const pontos = [];
      for (let lat = -80; lat <= 80; lat += 10) pontos.push(projetar(lon, lat));
      const d = "M " + pontos.map(function (p) { return p.x + " " + p.y; }).join(" L ");
      const linha = document.createElementNS(NS, "path");
      linha.setAttribute("d", d); linha.setAttribute("class", "globo-neon-grade");
      grupo.appendChild(linha);
    });

    const maior = Math.max(1, ...paises.map(function (p) { return Number(p.n) || 0; }));
    const centroSede = projetar(lon0, lat0);

    paises.forEach(function (p, i) {
      if (p.latitude === undefined || p.latitude === null || p.longitude === undefined || p.longitude === null) return;
      const alvo = projetar(p.longitude, p.latitude);
      const n = Number(p.n) || 0;
      const forca = n / maior;

      // Arco de voo: bezier quadrático curvando "para fora" do centro da
      // esfera, com o ponto de controle puxado na direção perpendicular
      // ao segmento -- o mesmo truque visual de rota aérea em mapas.
      const mx = (centroSede.x + alvo.x) / 2, my = (centroSede.y + alvo.y) / 2;
      const dx = alvo.x - centroSede.x, dy = alvo.y - centroSede.y;
      const dist = Math.max(1, Math.hypot(dx, dy));
      const curva = Math.min(60, dist * 0.35);
      const cxArco = mx - (dy / dist) * curva, cyArco = my + (dx / dist) * curva;
      const arco = document.createElementNS(NS, "path");
      arco.setAttribute("d", `M ${centroSede.x} ${centroSede.y} Q ${cxArco} ${cyArco} ${alvo.x} ${alvo.y}`);
      arco.setAttribute("fill", "none");
      arco.setAttribute("stroke", "var(--accent-strong)");
      arco.setAttribute("stroke-width", String(0.6 + forca * 3.2));
      arco.setAttribute("opacity", String(0.35 + forca * 0.55));
      arco.setAttribute("class", "globo-neon-arco");
      arco.style.setProperty("--atraso-arco", (i * 120) + "ms");
      const dicaArco = document.createElementNS(NS, "title");
      dicaArco.textContent = `${sede.nome || "Sede"} → ${p.pais}: ${fmt(n)} artigo(s)`;
      arco.appendChild(dicaArco);
      grupo.appendChild(arco);

      const ponto = document.createElementNS(NS, "circle");
      ponto.setAttribute("cx", alvo.x); ponto.setAttribute("cy", alvo.y);
      ponto.setAttribute("r", String(3 + forca * 5));
      ponto.setAttribute("class", "globo-neon-pais");
      ponto.style.setProperty("--cor-esfera", "var(--accent-strong)");
      const dicaPonto = document.createElementNS(NS, "title");
      dicaPonto.textContent = p.pais + ": " + fmt(n) + " artigo(s)"
        + ((p.instituicoes || []).length ? " · " + p.instituicoes.slice(0, 3).join(", ") : "");
      ponto.appendChild(dicaPonto);
      grupo.appendChild(ponto);
    });

    const marcoSede = document.createElementNS(NS, "circle");
    marcoSede.setAttribute("cx", centroSede.x); marcoSede.setAttribute("cy", centroSede.y);
    marcoSede.setAttribute("r", "6");
    marcoSede.setAttribute("class", "globo-neon-sede");
    const dicaSede = document.createElementNS(NS, "title");
    dicaSede.textContent = sede.nome || "Sede";
    marcoSede.appendChild(dicaSede);
    grupo.appendChild(marcoSede);

    svg.appendChild(grupo);
    fig.appendChild(svg);
    return fig;
  }

  return {
    ternario,
    pareto,
    sunburst,
    funilLiquido,
    gaugeDiagnostico,
    globoNeon,
    destacarFatiaSunburst,
  };
})();
