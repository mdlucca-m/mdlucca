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

    // Altura do triângulo equilátero
    const triH = h - 2 * margin;
    const triW = triH * Math.sqrt(3) / 2;

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "chart ternario");

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

    const w = 800, h = 400;
    const margin = { top: 40, right: 40, bottom: 40, left: 60 };
    const fig = document.createElement("figure");

    // Ordena por valor decrescente
    const sorted = [...dados].sort((a, b) => (b.valor || 0) - (a.valor || 0));
    const total = sorted.reduce((s, d) => s + (d.valor || 0), 0);

    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "chart pareto");

    const chartW = w - margin.left - margin.right;
    const chartH = h - margin.top - margin.bottom;

    // Escala
    const maxVal = sorted[0]?.valor || 1;
    const scaleX = chartW / sorted.length;
    const scaleY = chartH / maxVal;

    // Grupo para barras
    const barsGroup = document.createElementNS(NS, "g");
    barsGroup.setAttribute("transform", `translate(${margin.left},${margin.top})`);

    let acumulado = 0;
    sorted.forEach((d, i) => {
      const val = d.valor || 0;
      const barH = val * scaleY;
      const x = i * scaleX;
      const y = chartH - barH;

      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", x + 2);
      rect.setAttribute("y", y);
      rect.setAttribute("width", scaleX - 4);
      rect.setAttribute("height", barH);
      rect.setAttribute("fill", corSerie(i));
      rect.setAttribute("opacity", "0.8");
      barsGroup.appendChild(rect);

      acumulado += val;
      const pct = Math.round((acumulado / total) * 100);
      if (pct === 80) {
        // Marca a linha 80/20
        const line = document.createElementNS(NS, "line");
        line.setAttribute("x1", x);
        line.setAttribute("y1", 0);
        line.setAttribute("x2", x);
        line.setAttribute("y2", chartH);
        line.setAttribute("stroke", "var(--warning)");
        line.setAttribute("stroke-width", "2");
        line.setAttribute("stroke-dasharray", "5,5");
        barsGroup.appendChild(line);
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
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "chart sunburst");

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

  /* ======================== Scatter 3D (projeção isométrica) ======================== */
  function scatter3d(dados) {
    /**
     * Dispersão em 3D projetada isometricamente
     * x, y, z como variáveis numéricas
     * tamanho proporcional a uma quarta variável
     */
    if (!dados || dados.length === 0) return null;

    const w = 600, h = 600;
    const fig = document.createElement("figure");
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("class", "chart scatter3d");

    const margin = 60;
    const scale = (w - 2 * margin) / 3;

    const cx = w / 2, cy = h / 2;

    // Desenha eixos isométricos
    const axes = [
      { x: cx, y: cy, dx: scale * 0.866, dy: -scale * 0.5, label: "X" },
      { x: cx, y: cy, dx: -scale * 0.866, dy: -scale * 0.5, label: "Y" },
      { x: cx, y: cy, dx: 0, dy: scale, label: "Z" },
    ];

    axes.forEach(axis => {
      const line = document.createElementNS(NS, "line");
      line.setAttribute("x1", axis.x);
      line.setAttribute("y1", axis.y);
      line.setAttribute("x2", axis.x + axis.dx);
      line.setAttribute("y2", axis.y + axis.dy);
      line.setAttribute("stroke", "var(--border-strong)");
      line.setAttribute("stroke-width", "1");
      svg.appendChild(line);

      const text = document.createElementNS(NS, "text");
      text.setAttribute("x", axis.x + axis.dx + 10);
      text.setAttribute("y", axis.y + axis.dy + 5);
      text.setAttribute("font-size", "12");
      text.setAttribute("font-weight", "bold");
      text.setAttribute("fill", "var(--ink)");
      text.textContent = axis.label;
      svg.appendChild(text);
    });

    // Normaliza dados
    const xs = dados.map(d => d.x || 0);
    const ys = dados.map(d => d.y || 0);
    const zs = dados.map(d => d.z || 0);
    const maxX = Math.max(...xs) || 1;
    const maxY = Math.max(...ys) || 1;
    const maxZ = Math.max(...zs) || 1;

    // Plota pontos
    dados.forEach((d, i) => {
      const nx = (d.x || 0) / maxX;
      const ny = (d.y || 0) / maxY;
      const nz = (d.z || 0) / maxZ;

      // Isométrica
      const px = nx * scale * 0.866 - ny * scale * 0.866;
      const py = nx * scale * 0.5 + ny * scale * 0.5 - nz * scale;

      const x = cx + px;
      const y = cy + py;
      const r = Math.sqrt(d.tamanho || 1) * 3;

      const circle = document.createElementNS(NS, "circle");
      circle.setAttribute("cx", x);
      circle.setAttribute("cy", y);
      circle.setAttribute("r", r);
      circle.setAttribute("fill", corSerie(i));
      circle.setAttribute("opacity", "0.7");
      circle.setAttribute("stroke", "var(--surface)");
      circle.setAttribute("stroke-width", "2");

      const title = document.createElementNS(NS, "title");
      title.textContent = `${d.nome || "Item"}: (${d.x}, ${d.y}, ${d.z})`;
      circle.appendChild(title);

      svg.appendChild(circle);
    });

    fig.appendChild(svg);
    return fig;
  }

  return {
    ternario,
    pareto,
    sunburst,
    scatter3d,
    destacarFatiaSunburst,
  };
})();
