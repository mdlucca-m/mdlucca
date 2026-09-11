/* Bandeiras desenhadas, e nao emoji.
 *
 * O Windows nao tem bandeira de pais no conjunto de emoji: o Segoe UI Emoji
 * desenha o par de indicadores regionais (BR = U+1F1E7 U+1F1F7) como as duas
 * LETRAS, e foi isso que apareceu na tela do laboratorio -- "US", "BR", "AU"
 * onde deviam estar as bandeiras. Nenhum ajuste de CSS muda isso, e nenhuma
 * fonte padrao do Windows traz esses simbolos.
 *
 * Entao o desenho e feito aqui, em SVG, sem rede e sem fonte externa: o
 * sistema roda numa maquina de laboratorio que pode estar sem internet, e
 * uma bandeira que depende de CDN e uma bandeira que some.
 *
 * As proporcoes reais variam (2:1 no Reino Unido, 3:2 na Franca, 1:1 na
 * Suica). Aqui todas saem em 3:2 de proposito: numa lista de trinta paises,
 * proporcao fiel faz cada pastilha ter uma largura, e a coluna vira serra.
 * E uma simplificacao deliberada, e nao um descuido.
 */
const Bandeiras = (function () {
  const NS = "http://www.w3.org/2000/svg";
  const W = 30, H = 20;

  function s(tag, attrs) {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs || {}).forEach(function (par) {
      if (par[1] !== null && par[1] !== undefined) node.setAttribute(par[0], String(par[1]));
    });
    return node;
  }
  function ret(x, y, w, h, cor) {
    return s("rect", { x: x, y: y, width: w, height: h, fill: cor });
  }

  /* ---- receitas ---- */
  function faixasH(cores) {
    return function (g) {
      const h = H / cores.length;
      cores.forEach(function (cor, i) { g.appendChild(ret(0, i * h, W, h, cor)); });
    };
  }
  function faixasV(cores) {
    return function (g) {
      const w = W / cores.length;
      cores.forEach(function (cor, i) { g.appendChild(ret(i * w, 0, w, H, cor)); });
    };
  }
  /* A cruz nordica e deslocada para a esquerda -- centrada, vira cruz suica */
  function nordica(fundo, cruz, contorno) {
    return function (g) {
      g.appendChild(ret(0, 0, W, H, fundo));
      const x = W * 0.36, e = contorno ? 6 : 4;
      if (contorno) {
        g.appendChild(ret(0, H / 2 - e / 2, W, e, contorno));
        g.appendChild(ret(x - e / 2, 0, e, H, contorno));
      }
      g.appendChild(ret(0, H / 2 - 2, W, 4, cruz));
      g.appendChild(ret(x - 2, 0, 4, H, cruz));
    };
  }
  function disco(fundo, cor, r) {
    return function (g) {
      g.appendChild(ret(0, 0, W, H, fundo));
      g.appendChild(s("circle", { cx: W / 2, cy: H / 2, r: r || 5.5, fill: cor }));
    };
  }
  function estrela(cx, cy, r, cor) {
    const pontos = [];
    for (let i = 0; i < 10; i++) {
      const raio = i % 2 ? r * 0.42 : r;
      const a = (Math.PI / 5) * i - Math.PI / 2;
      pontos.push((cx + raio * Math.cos(a)).toFixed(2) + "," + (cy + raio * Math.sin(a)).toFixed(2));
    }
    return s("polygon", { points: pontos.join(" "), fill: cor });
  }

  const DESENHOS = {
    /* faixas verticais */
    FR: faixasV(["#002395", "#fff", "#ed2939"]),
    IT: faixasV(["#008c45", "#f4f5f0", "#cd212a"]),
    IE: faixasV(["#169b62", "#fff", "#ff883e"]),
    BE: faixasV(["#000", "#fdda24", "#ef3340"]),
    RO: faixasV(["#002b7f", "#fcd116", "#ce1126"]),
    /* faixas horizontais */
    DE: faixasH(["#000", "#dd0000", "#ffce00"]),
    NL: faixasH(["#ae1c28", "#fff", "#21468b"]),
    AT: faixasH(["#ed2939", "#fff", "#ed2939"]),
    HU: faixasH(["#ce2939", "#fff", "#477050"]),
    CO: faixasH(["#fcd116", "#003893", "#ce1126"]),
    AR: faixasH(["#74acdf", "#fff", "#74acdf"]),
    PL: faixasH(["#fff", "#dc143c"]),
    ID: faixasH(["#ce1126", "#fff"]),
    UA: faixasH(["#0057b7", "#ffd700"]),
    /* cruz nordica */
    SE: nordica("#006aa7", "#fecc00"),
    /* A cruz da Noruega e AZUL sobre contorno branco. Passar branco nos
       dois deixava a bandeira idêntica à da Dinamarca -- e uma bandeira
       trocada por outra é pior do que nenhuma bandeira. */
    NO: nordica("#ba0c2f", "#00205b", "#fff"),
    DK: nordica("#c8102e", "#fff"),
    FI: nordica("#fff", "#003580"),
    IS: nordica("#02529c", "#dc1e35", "#fff"),
    /* disco */
    JP: disco("#fff", "#bc002d", 5),
    BD: disco("#006a4e", "#f42a41", 5),
    /* especiais */
    BR: function (g) {
      g.appendChild(ret(0, 0, W, H, "#009b3a"));
      g.appendChild(s("polygon", {
        points: "15,2.5 27.5,10 15,17.5 2.5,10", fill: "#fedf00" }));
      g.appendChild(s("circle", { cx: 15, cy: 10, r: 4, fill: "#002776" }));
    },
    US: function (g) {
      for (let i = 0; i < 13; i++) {
        g.appendChild(ret(0, i * (H / 13), W, H / 13, i % 2 ? "#fff" : "#b22234"));
      }
      g.appendChild(ret(0, 0, W * 0.42, H * 7 / 13, "#3c3b6e"));
      for (let l = 0; l < 4; l++) for (let c = 0; c < 5; c++) {
        g.appendChild(s("circle", {
          cx: 1.6 + c * 2.5, cy: 1.5 + l * 2.6, r: 0.55, fill: "#fff" }));
      }
    },
    GB: function (g) {
      g.appendChild(ret(0, 0, W, H, "#012169"));
      const diag = function (cor, largura) {
        [["0,0", W + "," + H], [W + ",0", "0," + H]].forEach(function (par) {
          g.appendChild(s("line", {
            x1: par[0].split(",")[0], y1: par[0].split(",")[1],
            x2: par[1].split(",")[0], y2: par[1].split(",")[1],
            stroke: cor, "stroke-width": largura }));
        });
      };
      diag("#fff", 5); diag("#c8102e", 2.2);
      g.appendChild(ret(0, H / 2 - 3.2, W, 6.4, "#fff"));
      g.appendChild(ret(W / 2 - 3.2, 0, 6.4, H, "#fff"));
      g.appendChild(ret(0, H / 2 - 1.8, W, 3.6, "#c8102e"));
      g.appendChild(ret(W / 2 - 1.8, 0, 3.6, H, "#c8102e"));
    },
    ES: function (g) {
      g.appendChild(ret(0, 0, W, H, "#aa151b"));
      g.appendChild(ret(0, H * 0.25, W, H * 0.5, "#f1bf00"));
    },
    PT: function (g) {
      g.appendChild(ret(0, 0, W, H, "#ff0000"));
      g.appendChild(ret(0, 0, W * 0.4, H, "#006600"));
      g.appendChild(s("circle", { cx: W * 0.4, cy: H / 2, r: 4,
        fill: "#ffff00", stroke: "#fff", "stroke-width": 0.6 }));
      g.appendChild(s("circle", { cx: W * 0.4, cy: H / 2, r: 2, fill: "#ff0000" }));
    },
    CH: function (g) {
      g.appendChild(ret(0, 0, W, H, "#d52b1e"));
      g.appendChild(ret(W / 2 - 2, H / 2 - 6, 4, 12, "#fff"));
      g.appendChild(ret(W / 2 - 6, H / 2 - 2, 12, 4, "#fff"));
    },
    CA: function (g) {
      g.appendChild(ret(0, 0, W, H, "#fff"));
      g.appendChild(ret(0, 0, W * 0.25, H, "#d80621"));
      g.appendChild(ret(W * 0.75, 0, W * 0.25, H, "#d80621"));
      /* a folha em traco simples: o desenho heraldico nao cabe em 30px */
      g.appendChild(s("polygon", {
        points: "15,3.5 16.2,7.5 19,6.5 17.6,10 20,11 15,13.5 10,11 12.4,10 11,6.5 13.8,7.5",
        fill: "#d80621" }));
    },
    CN: function (g) {
      g.appendChild(ret(0, 0, W, H, "#de2910"));
      g.appendChild(estrela(6, 6, 3.4, "#ffde00"));
      [[11.5, 2.6], [13.5, 5], [13.5, 8], [11.5, 10.4]].forEach(function (p) {
        g.appendChild(estrela(p[0], p[1], 1.2, "#ffde00"));
      });
    },
    AU: function (g) {
      g.appendChild(ret(0, 0, W, H, "#00008b"));
      g.appendChild(ret(0, 0, W * 0.45, H * 0.5, "#012169"));
      g.appendChild(ret(0, H * 0.25 - 1, W * 0.45, 2, "#fff"));
      g.appendChild(ret(W * 0.22 - 1, 0, 2, H * 0.5, "#fff"));
      g.appendChild(estrela(22, 12, 2.4, "#fff"));
      [[25, 4], [27, 9], [23, 6.5], [20, 16]].forEach(function (p) {
        g.appendChild(estrela(p[0], p[1], 1.3, "#fff"));
      });
    },
    NZ: function (g) {
      g.appendChild(ret(0, 0, W, H, "#00247d"));
      g.appendChild(ret(0, 0, W * 0.45, H * 0.5, "#012169"));
      g.appendChild(ret(0, H * 0.25 - 1, W * 0.45, 2, "#fff"));
      g.appendChild(ret(W * 0.22 - 1, 0, 2, H * 0.5, "#fff"));
      [[24, 5], [26, 10], [22, 12], [24, 16]].forEach(function (p) {
        g.appendChild(estrela(p[0], p[1], 1.6, "#cc142b"));
      });
    },
    TN: function (g) {
      g.appendChild(ret(0, 0, W, H, "#e70013"));
      g.appendChild(s("circle", { cx: 15, cy: 10, r: 6, fill: "#fff" }));
      g.appendChild(s("circle", { cx: 16.2, cy: 10, r: 4, fill: "#e70013" }));
      g.appendChild(s("circle", { cx: 17.6, cy: 10, r: 3.1, fill: "#fff" }));
      g.appendChild(estrela(16.6, 10, 2.4, "#e70013"));
    },
    QA: function (g) {
      g.appendChild(ret(0, 0, W, H, "#8a1538"));
      g.appendChild(s("polygon", {
        points: "0,0 9,0 12,1.7 9,3.4 12,5 9,6.7 12,8.4 9,10 12,11.7 9,13.4 12,15 9,16.7 12,18.3 9,20 0,20",
        fill: "#fff" }));
    },
    CL: function (g) {
      g.appendChild(ret(0, 0, W, H, "#fff"));
      g.appendChild(ret(0, H / 2, W, H / 2, "#d52b1e"));
      g.appendChild(ret(0, 0, W * 0.34, H / 2, "#0039a6"));
      g.appendChild(estrela(W * 0.17, H * 0.25, 2.6, "#fff"));
    },
    GR: function (g) {
      for (let i = 0; i < 9; i++) {
        g.appendChild(ret(0, i * (H / 9), W, H / 9, i % 2 ? "#fff" : "#0d5eaf"));
      }
      g.appendChild(ret(0, 0, H * 5 / 9, H * 5 / 9, "#0d5eaf"));
      g.appendChild(ret(0, H * 2 / 9, H * 5 / 9, H / 9, "#fff"));
      g.appendChild(ret(H * 2 / 9, 0, H / 9, H * 5 / 9, "#fff"));
    },
    ZA: function (g) {
      g.appendChild(ret(0, 0, W, H, "#002395"));
      g.appendChild(ret(0, 0, W, H / 2, "#de3831"));
      g.appendChild(s("polygon", { points: "0,0 12,10 0,20", fill: "#007a4d" }));
      g.appendChild(s("polygon", { points: "0,3 8,10 0,17", fill: "#ffb612" }));
    },
    IN: function (g) {
      g.appendChild(ret(0, 0, W, H / 3, "#ff9933"));
      g.appendChild(ret(0, H / 3, W, H / 3, "#fff"));
      g.appendChild(ret(0, 2 * H / 3, W, H / 3, "#138808"));
      g.appendChild(s("circle", { cx: 15, cy: 10, r: 2.6, fill: "none",
        stroke: "#000080", "stroke-width": 0.8 }));
    },
    KR: function (g) {
      g.appendChild(ret(0, 0, W, H, "#fff"));
      g.appendChild(s("path", {
        d: "M15,5.5 a4.5,4.5 0 0,1 0,9 a2.25,2.25 0 0,0 0,-4.5 a2.25,2.25 0 0,1 0,-4.5",
        fill: "#cd2e3a" }));
      g.appendChild(s("path", {
        d: "M15,5.5 a4.5,4.5 0 0,0 0,9 a2.25,2.25 0 0,1 0,-4.5 a2.25,2.25 0 0,0 0,-4.5",
        fill: "#0047a0" }));
    },
    TR: function (g) {
      g.appendChild(ret(0, 0, W, H, "#e30a17"));
      g.appendChild(s("circle", { cx: 12, cy: 10, r: 4.4, fill: "#fff" }));
      g.appendChild(s("circle", { cx: 13.6, cy: 10, r: 3.5, fill: "#e30a17" }));
      g.appendChild(estrela(17.5, 10, 2.2, "#fff"));
    },
    MX: function (g) {
      g.appendChild(ret(0, 0, W / 3, H, "#006847"));
      g.appendChild(ret(W / 3, 0, W / 3, H, "#fff"));
      g.appendChild(ret(2 * W / 3, 0, W / 3, H, "#ce1126"));
      g.appendChild(s("circle", { cx: 15, cy: 10, r: 2.4, fill: "none",
        stroke: "#8b5a2b", "stroke-width": 0.9 }));
    },
    IL: function (g) {
      g.appendChild(ret(0, 0, W, H, "#fff"));
      g.appendChild(ret(0, 2.5, W, 2.2, "#0038b8"));
      g.appendChild(ret(0, H - 4.7, W, 2.2, "#0038b8"));
      g.appendChild(s("polygon", { points: "15,6 18.5,12 11.5,12", fill: "none",
        stroke: "#0038b8", "stroke-width": 0.9 }));
      g.appendChild(s("polygon", { points: "15,14 18.5,8 11.5,8", fill: "none",
        stroke: "#0038b8", "stroke-width": 0.9 }));
    },
  };

  /* O que fazer quando nao ha desenho: a pastilha com o codigo, que e o que
     ja aparecia -- mas agora de proposito, e nao por a fonte ter falhado.
     Inventar um desenho parecido seria pior: bandeira errada e ofensa, e
     ninguem confere a bandeira de um pais que nao conhece. */
  function pastilha(iso) {
    const g = document.createElementNS(NS, "svg");
    g.setAttribute("viewBox", "0 0 " + W + " " + H);
    g.setAttribute("class", "bandeira-svg sem-desenho");
    g.appendChild(ret(0, 0, W, H, "var(--surface-raised)"));
    g.appendChild(s("rect", { x: 0.4, y: 0.4, width: W - 0.8, height: H - 0.8,
      fill: "none", stroke: "var(--border)", "stroke-width": 0.8, rx: 2 }));
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", W / 2); t.setAttribute("y", H / 2 + 3.6);
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("style", "font-size:9px;font-weight:700;fill:var(--ink-muted)");
    t.textContent = (iso || "??").toUpperCase();
    g.appendChild(t);
    return g;
  }

  function get(iso, nome) {
    const codigo = String(iso || "").toUpperCase();
    const desenho = DESENHOS[codigo];
    if (!desenho) return pastilha(codigo);
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("class", "bandeira-svg");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "bandeira" + (nome ? " do " + nome : ""));
    const g = document.createElementNS(NS, "g");
    desenho(g);
    svg.appendChild(g);
    /* uma borda fina por cima: bandeira com branco na beirada some sobre
       fundo claro, e a lista vira uma fila de retângulos invisíveis */
    svg.appendChild(s("rect", { x: 0.25, y: 0.25, width: W - 0.5, height: H - 0.5,
      fill: "none", stroke: "rgba(0,0,0,.22)", "stroke-width": 0.5 }));
    return svg;
  }

  function tem(iso) { return !!DESENHOS[String(iso || "").toUpperCase()]; }

  return { get: get, tem: tem, quantas: Object.keys(DESENHOS).length };
})();
