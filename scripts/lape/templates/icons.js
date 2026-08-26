/* ==========================================================================
   LAPE — ícones
   SVG inline, traço de 1.75px em currentColor, caixa de 24. Sem fonte de
   ícone e sem rede: o painel abre offline e o ícone acompanha a cor do texto.
   Todo ícone é decorativo (aria-hidden) — o rótulo ao lado é quem nomeia.
   ========================================================================== */
"use strict";

const Icons = (function () {
  const NS = "http://www.w3.org/2000/svg";

  /* Cada verbete é uma lista de primitivas: ["path", "M..."] , ["circle", cx, cy, r],
     ["line", x1, y1, x2, y2], ["rect", x, y, w, h, r]. Traço aberto, sem preenchimento. */
  const SET = {
    /* seções */
    painel: [["path", "M3 12a9 9 0 0 1 18 0"], ["path", "M12 12l4.5-3.5"],
      ["circle", 12, 12, 1.2], ["line", 3, 12, 5, 12], ["line", 19, 12, 21, 12]],
    producao: [["path", "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"],
      ["path", "M14 3v5h5"], ["line", 9, 13, 15, 13], ["line", 9, 17, 13, 17]],
    pessoas: [["circle", 9, 8, 3.2], ["path", "M3 20c0-3.2 2.7-5 6-5s6 1.8 6 5"],
      ["path", "M16.5 5.6a3.2 3.2 0 0 1 0 5.8"], ["path", "M18 15.4c2 .7 3 2.2 3 4.6"]],
    processo: [["path", "M21 12a9 9 0 0 1-14.7 7"], ["path", "M3 12a9 9 0 0 1 14.7-7"],
      ["path", "M17.7 2v3.4h-3.4"], ["path", "M6.3 22v-3.4h3.4"]],
    espaco: [["path", "M12 21s-6.5-5.6-6.5-10.2A6.5 6.5 0 0 1 12 4.3a6.5 6.5 0 0 1 6.5 6.5C18.5 15.4 12 21 12 21z"],
      ["circle", 12, 10.6, 2.4]],
    dados: [["ellipse", 12, 6, 7.5, 3], ["path", "M4.5 6v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"],
      ["path", "M4.5 12v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6"]],

    /* sub-abas e cartões */
    explorar: [["circle", 11, 11, 6.5], ["line", 15.8, 15.8, 21, 21]],
    barras: [["line", 3, 21, 21, 21], ["rect", 5, 12, 3.4, 9, 1], ["rect", 10.3, 7, 3.4, 14, 1],
      ["rect", 15.6, 3.5, 3.4, 17.5, 1]],
    linha: [["path", "M3 17l5-5 4 3 7-8"], ["circle", 8, 12, 1.4], ["circle", 12, 15, 1.4],
      ["circle", 19, 7, 1.4]],
    rede: [["circle", 12, 5, 2.3], ["circle", 5, 18, 2.3], ["circle", 19, 18, 2.3],
      ["line", 10.6, 6.9, 6.4, 15.8], ["line", 13.4, 6.9, 17.6, 15.8], ["line", 7.3, 18, 16.7, 18]],
    calendario: [["rect", 3.5, 5, 17, 16, 2.5], ["line", 3.5, 10, 20.5, 10],
      ["line", 8, 3, 8, 6.5], ["line", 16, 3, 16, 6.5], ["circle", 8.6, 14.5, 1],
      ["circle", 12.8, 14.5, 1]],
    relogio: [["circle", 12, 12, 8.5], ["path", "M12 7v5.3l3.4 2"]],
    submissao: [["path", "M21 3L10.5 13.5"], ["path", "M21 3l-6.8 18-3.7-7.5L3 9.8z"]],
    aceite: [["circle", 12, 12, 8.5], ["path", "M8.2 12.3l2.6 2.6 5-5.4"]],
    citacao: [["path", "M9 7.5C6.6 8.4 5 10.4 5 13.4V17h4.6v-4.4H7.4c0-1.7.7-2.8 2.2-3.4z"],
      ["path", "M18 7.5c-2.4.9-4 2.9-4 5.9V17h4.6v-4.4h-2.2c0-1.7.7-2.8 2.2-3.4z"]],
    projeto: [["path", "M3 7.5A1.5 1.5 0 0 1 4.5 6h4l2 2.5h7A1.5 1.5 0 0 1 19 10v7.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 3 17.5z"],
      ["line", 7, 13, 15, 13]],
    linhas: [["line", 4, 6.5, 20, 6.5], ["line", 4, 12, 20, 12], ["line", 4, 17.5, 14, 17.5],
      ["circle", 20, 17.5, 1.4]],
    achado: [["path", "M12 3l1.9 4.5 4.9.4-3.7 3.2 1.1 4.8L12 13.4 7.8 15.9l1.1-4.8L5.2 7.9l4.9-.4z"],
      ["line", 12, 18, 12, 21]],
    qualidade: [["path", "M12 3l7.5 3v5.4c0 4.4-3.1 8.1-7.5 9.6-4.4-1.5-7.5-5.2-7.5-9.6V6z"],
      ["path", "M9 12l2.2 2.2L15.4 10"]],
    automacao: [["rect", 4, 8.5, 16, 11, 3], ["circle", 9, 13.5, 1.2], ["circle", 15, 13.5, 1.2],
      ["path", "M12 8.5V5"], ["circle", 12, 3.6, 1.3], ["line", 8, 16.8, 16, 16.8]],
    mapa: [["path", "M3 6.5l6-2.5 6 2.5 6-2.5v14l-6 2.5-6-2.5-6 2.5z"], ["line", 9, 4, 9, 18.5],
      ["line", 15, 6.5, 15, 21]],
    tempo: [["line", 4, 12, 20, 12], ["circle", 7.5, 12, 2], ["circle", 13, 12, 2],
      ["circle", 18, 12, 2]],
    alvo: [["circle", 12, 12, 8.5], ["circle", 12, 12, 4.6], ["circle", 12, 12, 1]],
    subida: [["path", "M3 17l6-6 4 3.6L21 6"], ["path", "M15.5 6H21v5.3"]],
    livro: [["path", "M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5z"],
      ["path", "M20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5z"]],
    raio: [["path", "M13 2L4.5 13.5H11L10 22l8.5-11.5H12z"]],
    aviso: [["path", "M12 4l9 15.5H3z"], ["line", 12, 10, 12, 14.5], ["circle", 12, 17.2, 1]],
    baixar: [["path", "M12 3.5v11"], ["path", "M7.6 10.4L12 14.8l4.4-4.4"],
      ["path", "M4.5 18.5v1a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-1"]],
    atualizar: [["path", "M20.5 12a8.5 8.5 0 1 1-2.6-6.1"], ["path", "M20.5 4v4.6h-4.6"]],
    conectar: [["path", "M10.5 13.5l-2.6 2.6a3.7 3.7 0 0 1-5.2-5.2l2.6-2.6"],
      ["path", "M13.5 10.5l2.6-2.6a3.7 3.7 0 0 1 5.2 5.2l-2.6 2.6"], ["line", 9.5, 14.5, 14.5, 9.5]],
  };

  function draw(spec) {
    const kind = spec[0];
    const node = document.createElementNS(NS, kind === "ellipse" ? "ellipse" : kind);
    if (kind === "path") node.setAttribute("d", spec[1]);
    else if (kind === "circle") {
      node.setAttribute("cx", spec[1]); node.setAttribute("cy", spec[2]);
      node.setAttribute("r", spec[3]);
    } else if (kind === "ellipse") {
      node.setAttribute("cx", spec[1]); node.setAttribute("cy", spec[2]);
      node.setAttribute("rx", spec[3]); node.setAttribute("ry", spec[4]);
    } else if (kind === "line") {
      node.setAttribute("x1", spec[1]); node.setAttribute("y1", spec[2]);
      node.setAttribute("x2", spec[3]); node.setAttribute("y2", spec[4]);
    } else if (kind === "rect") {
      node.setAttribute("x", spec[1]); node.setAttribute("y", spec[2]);
      node.setAttribute("width", spec[3]); node.setAttribute("height", spec[4]);
      node.setAttribute("rx", spec[5] === undefined ? 2 : spec[5]);
    }
    return node;
  }

  /* Devolve um <svg class="icon">. Nome desconhecido não quebra o painel:
     vira um ponto discreto, e a aba continua legível pelo rótulo. */
  function get(name, size) {
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "icon");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", size || 18);
    svg.setAttribute("height", size || 18);
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.75");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    (SET[name] || [["circle", 12, 12, 2]]).forEach(function (spec) {
      svg.appendChild(draw(spec));
    });
    return svg;
  }

  function has(name) { return Object.prototype.hasOwnProperty.call(SET, name); }
  function names() { return Object.keys(SET); }

  return { get: get, has: has, names: names };
})();
