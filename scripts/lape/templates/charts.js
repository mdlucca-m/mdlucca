/* ==========================================================================
   LAPE — biblioteca de gráficos
   Sem dependências externas. Cada forma devolve um <figure> com:
     · o desenho em SVG
     · legenda, quando há duas séries ou mais
     · botões "Tabela" e "CSV" — todo valor é alcançável sem passar o mouse
   Especificação das marcas (fixa em todos os gráficos):
     barra <= 24px, ponta arredondada em 4px e reta na linha de base
     linha 2px, junta e ponta redondas · marcador r >= 4 com anel de 2px
     área a 10% de opacidade · grade em fio de cabelo, sólida, discreta
     2px de respiro entre marcas encostadas (empilhamento e barras vizinhas)
   ========================================================================== */
"use strict";

const Charts = (function () {
  const NS = "http://www.w3.org/2000/svg";
  const BAR_MAX = 24;        /* espessura máxima da barra */
  const GAP = 2;             /* respiro entre marcas encostadas */
  const R_END = 4;           /* raio da ponta da barra */

  /* ---------------------------------------------------------------- base */
  function token(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }
  function serie(i) { return token("--series-" + ((i % 8) + 1)); }
  function seq(step) { return token("--seq-" + step); }
  function ord(i) { return token("--ord-" + (Math.min(i, 3) + 1)); }
  const SEQ_STEPS = [100, 200, 300, 400, 500, 600, 700];

  function el(tag, attrs, kids) {
    const node = document.createElement(tag);
    apply(node, attrs);
    append(node, kids);
    return node;
  }
  function s(tag, attrs, kids) {
    const node = document.createElementNS(NS, tag);
    for (const k in (attrs || {})) {
      if (attrs[k] === null || attrs[k] === undefined || attrs[k] === false) continue;
      node.setAttribute(k, attrs[k]);
    }
    append(node, kids);
    return node;
  }
  function apply(node, attrs) {
    for (const k in (attrs || {})) {
      const v = attrs[k];
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;      /* nunca innerHTML com dado */
      else if (k === "html") node.innerHTML = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v);
    }
  }
  function append(node, kids) {
    (Array.isArray(kids) ? kids : (kids === undefined || kids === null ? [] : [kids]))
      .forEach(function (kid) {
        if (kid === null || kid === undefined || kid === false) return;
        node.appendChild(typeof kid === "object" ? kid : document.createTextNode(String(kid)));
      });
  }
  function txt(node, value) { node.textContent = value === null || value === undefined ? "" : String(value); return node; }

  /* ------------------------------------------------------------ formatos */
  function fmt(v) {
    if (v === null || v === undefined || v === "") return "—";
    if (typeof v !== "number") return String(v);
    if (!isFinite(v)) return "—";
    if (Number.isInteger(v)) return v.toLocaleString("pt-BR");
    return v.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  }
  function compact(v) {
    if (typeof v !== "number" || !isFinite(v)) return fmt(v);
    if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1).replace(".", ",") + " mi";
    if (Math.abs(v) >= 10000) return (v / 1000).toFixed(1).replace(".", ",") + " mil";
    return fmt(v);
  }
  /* eixo com números redondos */
  function niceTicks(max, wanted) {
    if (!(max > 0)) return { max: 1, ticks: [0, 1] };
    if (max <= (wanted || 4)) {
      const ticks = [];
      for (let i = 0; i <= Math.ceil(max); i++) ticks.push(i);
      return { max: Math.ceil(max), ticks: ticks };
    }
    const raw = max / (wanted || 4);
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map(function (m) { return m * mag; })
      .find(function (v) { return v >= raw; }) || 10 * mag;
    const top = Math.ceil(max / step) * step;
    const ticks = [];
    for (let v = 0; v <= top + 1e-9; v += step) ticks.push(Math.round(v * 1000) / 1000);
    return { max: top, ticks: ticks };
  }

  /* Eixo que atravessa o zero. `niceTicks` so sabe subir de 0 ate o
     maximo -- e velocidade e aceleracao sao grandezas COM SINAL: metade
     da informacao esta abaixo da linha. Com a escala so-positiva, o
     trecho negativo era desenhado fora da area do grafico, por cima da
     legenda, sem erro nenhum na tela. */
  function niceTicksSigned(min, max, wanted) {
    if (min >= 0) return { lo: 0, hi: niceTicks(max, wanted).max,
                           ticks: niceTicks(max, wanted).ticks };
    const alcance = niceTicks(Math.max(Math.abs(min), Math.abs(max), 1e-9), wanted);
    const passo = alcance.ticks.length > 1
      ? alcance.ticks[1] - alcance.ticks[0] : alcance.max;
    const lo = -Math.ceil(Math.abs(min) / passo) * passo;
    const hi = Math.ceil(Math.max(max, passo) / passo) * passo;
    const ticks = [];
    for (let v = lo; v <= hi + 1e-9; v += passo) ticks.push(Math.round(v * 1000) / 1000);
    return { lo: lo, hi: hi, ticks: ticks };
  }

  /* -------------------------------------------------------------- dica */
  let TIP = null;
  function tipNode() {
    if (!TIP) {
      TIP = el("div", { class: "tip", role: "status", "aria-live": "polite" });
      document.body.appendChild(TIP);
    }
    return TIP;
  }
  /* rows: [{name, value, color}] — valor em destaque, nome secundário */
  function showTip(ev, title, rows) {
    const tip = tipNode();
    tip.innerHTML = "";
    tip.appendChild(txt(el("div", { class: "tip-title" }), title));
    (rows || []).forEach(function (row) {
      const line = el("div", { class: "row" });
      if (row.color) line.appendChild(el("span", { class: "key", style: "background:" + row.color }));
      line.appendChild(txt(el("span", { class: "v" }), row.value));
      if (row.name) line.appendChild(txt(el("span", { class: "n" }), row.name));
      tip.appendChild(line);
    });
    tip.classList.add("on");
    place(tip, ev);
  }
  function place(tip, ev) {
    const box = tip.getBoundingClientRect();
    const source = ev.touches ? ev.touches[0] : ev;
    let x = (source.clientX || 0) + 16, y = (source.clientY || 0) - box.height - 12;
    if (x + box.width > innerWidth - 8) x = (source.clientX || 0) - box.width - 16;
    if (y < 8) y = (source.clientY || 0) + 20;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  function hideTip() { if (TIP) TIP.classList.remove("on"); }
  /* alvo de toque maior que a marca, e o mesmo conteúdo no foco do teclado */
  function hoverable(node, title, rows, onClick) {
    node.addEventListener("pointermove", function (ev) { showTip(ev, title, rows); });
    node.addEventListener("pointerleave", hideTip);
    node.setAttribute("tabindex", "0");
    node.setAttribute("role", "img");
    node.setAttribute("aria-label", title + ": "
      + (rows || []).map(function (r) { return r.value + " " + (r.name || ""); }).join(", "));
    node.addEventListener("focus", function () {
      const box = node.getBoundingClientRect();
      showTip({ clientX: box.left + box.width / 2, clientY: box.top }, title, rows);
    });
    node.addEventListener("blur", hideTip);
    if (onClick) {
      node.style.cursor = "pointer";
      node.addEventListener("click", onClick);
      node.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); onClick(); }
      });
    }
    return node;
  }

  /* ------------------------------------------------- caminhos das marcas */
  /* barra com a ponta arredondada e a base reta */
  function capTop(x, y, w, h, r) {
    r = Math.max(0, Math.min(r === undefined ? R_END : r, w / 2, h));
    return "M" + x + "," + (y + h) + " L" + x + "," + (y + r)
      + " Q" + x + "," + y + " " + (x + r) + "," + y
      + " L" + (x + w - r) + "," + y + " Q" + (x + w) + "," + y + " " + (x + w) + "," + (y + r)
      + " L" + (x + w) + "," + (y + h) + " Z";
  }
  function capRight(x, y, w, h, r) {
    r = Math.max(0, Math.min(r === undefined ? R_END : r, h / 2, w));
    return "M" + x + "," + y + " L" + (x + w - r) + "," + y
      + " Q" + (x + w) + "," + y + " " + (x + w) + "," + (y + r)
      + " L" + (x + w) + "," + (y + h - r)
      + " Q" + (x + w) + "," + (y + h) + " " + (x + w - r) + "," + (y + h)
      + " L" + x + "," + (y + h) + " Z";
  }

  /* ------------------------------------------------------------- moldura */
  function empty(message) {
    return el("div", { class: "empty", text: message || "Sem dados para este recorte." });
  }
  function legendOf(items, opts) {
    opts = opts || {};
    const box = el("div", { class: "legend" + (opts.onToggle ? " clickable" : "") });
    items.forEach(function (item, i) {
      const node = el("div", { class: "item", tabindex: opts.onToggle ? "0" : null });
      node.appendChild(el("span", {
        class: "swatch" + (opts.line ? " line" : ""),
        style: "background:" + (item.color || serie(i)),
      }));
      node.appendChild(txt(el("span", {}), item.label));
      if (opts.onToggle) {
        const fire = function () { node.classList.toggle("off"); opts.onToggle(item, node.classList.contains("off")); };
        node.addEventListener("click", fire);
        node.addEventListener("keydown", function (ev) {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); fire(); }
        });
      }
      box.appendChild(node);
    });
    return box;
  }
  function scaleLegend(min, max, from, to, unit) {
    const ramp = el("span", {
      class: "ramp",
      style: "background:linear-gradient(90deg," + from + "," + to + ")",
    });
    return el("div", { class: "scale" }, [txt(el("span", {}), fmt(min)), ramp,
      txt(el("span", {}), fmt(max) + (unit ? " " + unit : ""))]);
  }
  function csvEscape(v) {
    const text = v === null || v === undefined ? "" : String(v);
    return /[";\n]/.test(text) ? '"' + text.replace(/"/g, '""') + '"' : text;
  }
  function downloadCsv(name, cols, rows) {
    const head = cols.map(function (c) { return csvEscape(c.label); }).join(";");
    const body = rows.map(function (row) {
      return cols.map(function (c) { return csvEscape(c.get ? c.get(row) : row[c.k]); }).join(";");
    }).join("\n");
    /* BOM para o Excel abrir os acentos corretamente */
    const blob = new Blob(["﻿" + head + "\n" + body], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = el("a", { href: url, download: name });
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }
  function plainTable(cols, rows) {
    const head = s ? null : null;
    const thead = el("thead", {}, el("tr", {}, cols.map(function (c) {
      return txt(el("th", { class: c.num ? "num" : null }), c.label);
    })));
    const tbody = el("tbody", {}, rows.map(function (row) {
      return el("tr", {}, cols.map(function (c) {
        return txt(el("td", { class: c.num ? "num" : null }), c.get ? c.get(row) : row[c.k]);
      }));
    }));
    return el("div", { class: "tw" }, el("table", {}, [thead, tbody]));
  }

  /* Toda figura ganha o par gráfico/tabela: nenhum valor fica só na dica. */
  function figure(spec, plot, extras) {
    const fig = el("figure", { class: "chart" });
    if (spec.caption) fig.appendChild(txt(el("figcaption", {}), spec.caption));
    fig.appendChild(plot);
    (extras || []).forEach(function (node) { if (node) fig.appendChild(node); });
    if (spec.table && spec.table.rows && spec.table.rows.length) {
      const twin = el("div", { class: "table-twin" }, plainTable(spec.table.cols, spec.table.rows));
      const toggle = el("button", {
        class: "no-print", type: "button", text: "Tabela", "aria-expanded": "false",
        onclick: function () {
          const on = twin.classList.toggle("on");
          toggle.textContent = on ? "Gráfico" : "Tabela";
          toggle.setAttribute("aria-expanded", String(on));
        },
      });
      const csv = el("button", {
        class: "no-print", type: "button", text: "CSV", title: "Baixar em CSV",
        onclick: function () {
          downloadCsv((spec.file || "lape") + ".csv", spec.table.cols, spec.table.rows);
        },
      });
      fig.appendChild(el("div", { class: "chart-tools" }, [toggle, csv]));
      fig.appendChild(twin);
    }
    return fig;
  }
  function svgRoot(w, h, label) {
    return s("svg", {
      class: "plot", viewBox: "0 0 " + w + " " + h, role: "img",
      "aria-label": label || "gráfico", preserveAspectRatio: "xMidYMid meet",
    });
  }

  /* ==================================================================== */
  /* colunas verticais — magnitude por categoria                          */
  /* modo: "simples" | "empilhado" | "agrupado"                           */
  /* ==================================================================== */
  function columns(spec) {
    const labels = spec.labels || [];
    const series = spec.series || [{ label: spec.name || "", values: spec.values || [] }];
    if (!labels.length) return figure(spec, empty(spec.emptyMessage));

    const W = 760, MR = 16, MT = 20, ML = 52;
    /* rótulo que não cabe na faixa é girado; aí o rodapé precisa de mais altura */
    const maisLongo = labels.reduce(function (a, l) { return Math.max(a, String(l).length); }, 0);
    const girado = (W - ML - MR) / labels.length - 6 < maisLongo * 5.6;
    const MB = girado ? Math.min(84, 32 + maisLongo * 3.4) : 40;
    const H = (spec.height || 260) + (girado ? MB - 40 : 0);
    const iw = W - ML - MR, ih = H - MT - MB;
    const stacked = spec.mode === "empilhado";
    const grouped = spec.mode === "agrupado";

    const totals = labels.map(function (_, i) {
      return stacked ? series.reduce(function (a, x) { return a + (x.values[i] || 0); }, 0)
        : Math.max.apply(null, series.map(function (x) { return x.values[i] || 0; }));
    });
    const peak = Math.max.apply(null, totals.concat(spec.reference ? [spec.reference] : []).concat([0]));
    const scale = niceTicks(peak, 4);
    const Y = function (v) { return MT + ih - ih * v / scale.max; };

    const svg = svgRoot(W, H, spec.caption || "colunas");
    scale.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: ML, x2: W - MR, y1: Y(t), y2: Y(t) }));
      svg.appendChild(txt(s("text", { class: "tick", x: ML - 8, y: Y(t) + 3.5, "text-anchor": "end" }), fmt(t)));
    });
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: W - MR, y1: Y(0), y2: Y(0) }));

    const band = iw / labels.length;
    const bandInner = Math.min(band - 10, BAR_MAX * (grouped ? series.length : 1) + (grouped ? (series.length - 1) * GAP : 0));
    const barW = grouped ? Math.min(BAR_MAX, (bandInner - (series.length - 1) * GAP) / series.length)
      : Math.min(BAR_MAX, bandInner);

    labels.forEach(function (label, i) {
      const center = ML + band * i + band / 2;
      if (stacked) {
        let cursor = 0;
        series.forEach(function (serieSpec, si) {
          const v = serieSpec.values[i] || 0;
          if (!v) return;
          const y0 = Y(cursor + v), y1 = Y(cursor);
          const h = Math.max(1, y1 - y0 - (cursor > 0 ? GAP : 0));
          const x = center - barW / 2;
          const isTop = cursor + v >= totals[i] - 1e-9;
          const node = s("path", {
            class: "mark", d: isTop ? capTop(x, y0, barW, h) : capTop(x, y0, barW, h, 0),
            fill: serieSpec.color || serie(si),
          });
          hoverable(node, label, [{ value: fmt(v), name: serieSpec.label, color: serieSpec.color || serie(si) }],
            spec.onSelect && function () { spec.onSelect(label, serieSpec.label); });
          svg.appendChild(node);
          cursor += v;
        });
        if (totals[i]) {
          svg.appendChild(txt(s("text", { class: "val", x: center, y: Y(totals[i]) - 7, "text-anchor": "middle" }), fmt(totals[i])));
        }
      } else {
        series.forEach(function (serieSpec, si) {
          const v = serieSpec.values[i] || 0;
          const x = grouped
            ? center - bandInner / 2 + si * (barW + GAP)
            : center - barW / 2;
          const h = Math.max(v > 0 ? 2 : 0, Y(0) - Y(v));
          if (h <= 0) return;
          const node = s("path", {
            class: "mark", d: capTop(x, Y(v), barW, h), fill: serieSpec.color || serie(si),
          });
          hoverable(node, label, [{ value: fmt(v), name: serieSpec.label, color: serieSpec.color || serie(si) }],
            spec.onSelect && function () { spec.onSelect(label, serieSpec.label); });
          svg.appendChild(node);
          /* rótulo direto só quando há uma série — com várias, a legenda + dica carregam */
          if (series.length === 1 && v) {
            svg.appendChild(txt(s("text", { class: "val", x: x + barW / 2, y: Y(v) - 7, "text-anchor": "middle" }), fmt(v)));
          }
        });
      }
      const cabe = band - 6 >= String(label).length * 5.6;   /* ~5,6px por caractere em 10,5px */
      const eixo = txt(s("text", {
        class: "lab", x: center, y: H - MB + (cabe ? 16 : 13),
        "text-anchor": cabe ? "middle" : "end",
      }), label);
      if (!cabe) {
        eixo.setAttribute("transform", "rotate(-38 " + center + " " + (H - MB + 13) + ")");
      }
      svg.appendChild(eixo);
    });

    /* linha de referência (meta) — sólida, com rótulo à direita */
    if (spec.reference) {
      svg.appendChild(s("line", {
        class: "axis-line", x1: ML, x2: W - MR, y1: Y(spec.reference), y2: Y(spec.reference),
        stroke: token("--ink-muted"), "stroke-width": 1.5,
      }));
      svg.appendChild(txt(s("text", {
        class: "val", x: W - MR, y: Y(spec.reference) - 6, "text-anchor": "end",
      }), (spec.referenceLabel || "meta") + " " + fmt(spec.reference)));
    }

    const extras = series.length > 1
      ? [legendOf(series.map(function (x, i) { return { label: x.label, color: x.color || serie(i) }; }))]
      : [];
    return figure(spec, svg, extras);
  }

  /* ==================================================================== */
  /* barras horizontais — ranking                                          */
  /* ==================================================================== */
  function bars(spec) {
    const items = spec.items || [];
    if (!items.length) return figure(spec, empty(spec.emptyMessage));
    const rowH = spec.rowH || 26;
    const W = 760, ML = spec.labelWidth || 190, MR = 62;
    const H = items.length * rowH + 12;
    const iw = W - ML - MR;
    const peak = Math.max.apply(null, items.map(function (d) { return d.value; }).concat([0]));
    const scale = niceTicks(peak, 3);
    const svg = svgRoot(W, H, spec.caption || "ranking");

    scale.ticks.forEach(function (t) {
      const x = ML + iw * t / scale.max;
      svg.appendChild(s("line", { class: "grid-line", x1: x, x2: x, y1: 4, y2: H - 8 }));
    });
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: ML, y1: 4, y2: H - 8 }));

    items.forEach(function (item, i) {
      const y = i * rowH + 6;
      const barH = Math.min(BAR_MAX, rowH - 10);
      const w = Math.max(item.value > 0 ? 2 : 0, iw * item.value / scale.max);
      const color = item.color || serie(spec.mono ? 0 : i);
      const label = txt(s("text", {
        class: "lab", x: ML - 10, y: y + barH / 2 + 4, "text-anchor": "end",
      }), item.label.length > (spec.labelChars || 26) ? item.label.slice(0, (spec.labelChars || 26) - 1) + "…" : item.label);
      svg.appendChild(label);
      if (item.rank) {
        svg.appendChild(txt(s("text", { class: "tick", x: 6, y: y + barH / 2 + 4 }), item.rank + "º"));
      }
      const node = s("path", { class: "mark", d: capRight(ML, y, w, barH), fill: color });
      const rows = [{ value: fmt(item.value), name: spec.unit || "", color: color }];
      if (item.note) rows.push({ value: "", name: item.note });
      hoverable(node, item.label, rows, item.onSelect || (spec.onSelect && function () { spec.onSelect(item); }));
      svg.appendChild(node);
      svg.appendChild(txt(s("text", { class: "val", x: ML + w + 8, y: y + barH / 2 + 4 }), fmt(item.value)));
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* linhas — tendência, com mira que encontra o X                        */
  /* ==================================================================== */
  function lines(spec) {
    const labels = spec.labels || [];
    const series = spec.series || [];
    if (!labels.length || !series.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 250, ML = 52, MR = 20, MT = 18, MB = 38;
    const iw = W - ML - MR, ih = H - MT - MB;
    const all = series.reduce(function (acc, x) { return acc.concat(x.values); }, []);
    /* `spec.max` trava o topo do eixo. Sem ele, uma serie desenhada
       ponto a ponto reescala a cada quadro e a curva parece pular. */
    const scale = niceTicksSigned(
      Math.min.apply(null, all.concat([0])),
      Math.max.apply(null, all.concat([spec.max || 0, 0])), 4);
    const alcance = (scale.hi - scale.lo) || 1;
    const X = function (i) { return labels.length === 1 ? ML + iw / 2 : ML + iw * i / (labels.length - 1); };
    const Y = function (v) { return MT + ih - ih * (v - scale.lo) / alcance; };

    const svg = svgRoot(W, H, spec.caption || "linhas");
    scale.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: ML, x2: W - MR, y1: Y(t), y2: Y(t) }));
      svg.appendChild(txt(s("text", { class: "tick", x: ML - 8, y: Y(t) + 3.5, "text-anchor": "end" }), fmt(t)));
    });
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: W - MR, y1: Y(0), y2: Y(0) }));
    /* Trinta rótulos de data em 760px saem colados uns nos outros e viram
       uma tarja preta. Só cabe um rótulo a cada ~64px; os outros somem,
       e o primeiro e o último ficam sempre -- são eles que dizem o
       intervalo que a curva cobre.
       O viewBox tem sempre 760 de largura, mas o gráfico pode ser
       desenhado em metade disso quando está numa coluna. `larguraReal`
       é o espaço que ele vai ocupar de fato; sem essa dica, meia coluna
       recebe o desbaste de tela cheia e os anos voltam a se encavalar. */
    const encolhe = W / (spec.larguraReal || W);
    const cabem = Math.max(1, Math.ceil(labels.length / Math.max(1, Math.floor(iw / (64 * encolhe)))));
    labels.forEach(function (label, i) {
      if (cabem > 1 && i % cabem && i !== labels.length - 1) return;
      svg.appendChild(txt(s("text", { class: "lab", x: X(i), y: H - MB + 16, "text-anchor": "middle" }), label));
    });

    const crosshair = s("line", { class: "crosshair", y1: MT, y2: MT + ih, x1: -99, x2: -99 });
    svg.appendChild(crosshair);

    series.forEach(function (serieSpec, si) {
      const color = serieSpec.color || serie(si);
      const path = serieSpec.values.map(function (v, i) {
        return (i ? "L" : "M") + X(i) + " " + Y(v);
      }).join(" ");
      /* Faixa de variação da série: o alto e o baixo de um mesmo valor.
         Numa projeção ela é o que separa "vai dar 12" de "dá entre 9 e
         15" -- e a segunda frase é a única que se pode dizer. */
      if (serieSpec.band && serieSpec.band.alto && serieSpec.band.baixo) {
        const alto = serieSpec.band.alto, baixo = serieSpec.band.baixo;
        const n = Math.min(alto.length, baixo.length, labels.length);
        if (n > 1) {
          let d = "";
          for (let i = 0; i < n; i++) d += (i ? "L" : "M") + X(i) + " " + Y(alto[i]);
          for (let i = n - 1; i >= 0; i--) d += "L" + X(i) + " " + Y(baixo[i]);
          svg.appendChild(s("path", { d: d + " Z", fill: color,
            "fill-opacity": 0.16, stroke: "none" }));
        }
      }
      if (serieSpec.area || (spec.area && series.length === 1)) {
        svg.appendChild(s("path", {
          fill: gradFill(svg, color),
          d: path + " L" + X(serieSpec.values.length - 1) + " " + Y(0)
            + " L" + X(0) + " " + Y(0) + " Z",
        }));
      }
      svg.appendChild(s("path", {
        d: path, fill: "none", stroke: color,
        "stroke-width": serieSpec.width || 2,
        /* `dash`: o que ainda nao aconteceu nao pode ser desenhado com a
           mesma tinta do que aconteceu. */
        "stroke-dasharray": serieSpec.dash || null,
        "stroke-linejoin": "round", "stroke-linecap": "round",
      }));
      serieSpec.values.forEach(function (v, i) {
        if (serieSpec.dash) return;   /* projeção não ganha marcador de dado */
        svg.appendChild(s("circle", { class: "ring", cx: X(i), cy: Y(v), r: 4, fill: color }));
      });
      /* rótulo direto só na ponta da série — nunca em todos os pontos */
      const last = serieSpec.values[serieSpec.values.length - 1];
      if (series.length <= 4 && last !== undefined) {
        svg.appendChild(txt(s("text", {
          /* a ponta da serie e o fim DELA. Numa serie mais curta que o
             eixo -- e e o caso durante a plotagem quadro a quadro -- o
             rotulo ficava flutuando na borda direita, longe da linha. */
          class: "val", x: X(serieSpec.values.length - 1) + 8, y: Y(last) + 4,
        }), fmt(last)));
      }
    });

    /* Marcas anotadas sobre a curva: um ponto de inflexão, uma mudança de
       política, um corte de coleta. Vão DEPOIS de todas as séries, para
       ficarem por cima delas — uma marca escondida atrás de uma linha não
       marca nada. `marks: [{ serie, i, label, tone }]`. */
    (spec.marks || []).forEach(function (marca) {
      const serieAlvo = series[marca.serie || 0];
      if (!serieAlvo) return;
      const valor = serieAlvo.values[marca.i];
      if (valor === undefined || valor === null) return;
      const cor = marca.color || serieAlvo.color || serie(marca.serie || 0);
      const x = X(marca.i), y = Y(valor);
      const g = s("g", { class: "marca" });
      g.appendChild(s("line", {
        x1: x, x2: x, y1: y, y2: MT + ih, stroke: cor, "stroke-width": 1,
        "stroke-dasharray": "3 3", "stroke-opacity": 0.55,
      }));
      /* anel duplo: o de fora na cor do fundo, para a marca se destacar
         mesmo quando cai em cima de outra linha */
      g.appendChild(s("circle", { cx: x, cy: y, r: 7.5, fill: "none",
        stroke: token("--surface-raised"), "stroke-width": 3 }));
      g.appendChild(s("circle", { cx: x, cy: y, r: 6.5, fill: "none",
        stroke: cor, "stroke-width": 2.4 }));
      g.appendChild(s("circle", { cx: x, cy: y, r: 2.4, fill: cor }));
      if (marca.label) {
        const acima = y > MT + 30;
        const rotulo = txt(s("text", {
          class: "val", x: x, y: acima ? y - 14 : y + 22, "text-anchor": "middle",
          style: "font-size:10.5px;font-weight:700;fill:" + cor,
        }), marca.label);
        g.appendChild(rotulo);
      }
      if (marca.title) {
        const dica = s("title");
        dica.textContent = marca.title;
        g.appendChild(dica);
      }
      svg.appendChild(g);
    });

    /* uma dica por X, listando todas as séries */
    const hit = s("rect", { class: "hit", x: ML, y: MT, width: iw, height: ih });
    function readAt(ev) {
      const box = svg.getBoundingClientRect();
      const px = ((ev.touches ? ev.touches[0] : ev).clientX - box.left) / box.width * W;
      let idx = Math.round((px - ML) / (iw / Math.max(labels.length - 1, 1)));
      idx = Math.max(0, Math.min(labels.length - 1, idx));
      crosshair.setAttribute("x1", X(idx));
      crosshair.setAttribute("x2", X(idx));
      showTip(ev, labels[idx], series.map(function (x, si) {
        return { value: fmt(x.values[idx]), name: x.label, color: x.color || serie(si) };
      }));
    }
    hit.addEventListener("pointermove", readAt);
    hit.addEventListener("pointerleave", function () {
      hideTip();
      crosshair.setAttribute("x1", -99);
      crosshair.setAttribute("x2", -99);
    });
    svg.appendChild(hit);

    const extras = series.length > 1
      ? [legendOf(series.map(function (x, i) { return { label: x.label, color: x.color || serie(i) }; }), { line: true })]
      : [];
    return figure(spec, svg, extras);
  }

  /* ==================================================================== */
  /* rosca — parte-e-todo, no máximo 6 fatias                             */
  /* ==================================================================== */
  function donut(spec) {
    const items = (spec.items || []).filter(function (d) { return d.value > 0; });
    const total = items.reduce(function (a, b) { return a + b.value; }, 0);
    if (!total) return figure(spec, empty(spec.emptyMessage));
    const W = 300, H = 260, cx = W / 2, cy = H / 2, R = 94, r = 62;
    const svg = svgRoot(W, H, spec.caption || "distribuição");
    svg.setAttribute("class", "plot round");
    let angle = -Math.PI / 2;

    items.forEach(function (item, i) {
      const color = item.color || serie(i);
      const span = 2 * Math.PI * item.value / total;
      /* o respiro de 2px entre fatias é feito com um recorte angular */
      const pad = Math.min(GAP / R, span / 4);
      const a0 = angle + pad / 2, a1 = angle + span - pad / 2;
      const large = (a1 - a0) > Math.PI ? 1 : 0;
      const path = s("path", {
        class: "mark", fill: color,
        d: "M" + (cx + R * Math.cos(a0)) + "," + (cy + R * Math.sin(a0))
          + "A" + R + "," + R + " 0 " + large + " 1 " + (cx + R * Math.cos(a1)) + "," + (cy + R * Math.sin(a1))
          + "L" + (cx + r * Math.cos(a1)) + "," + (cy + r * Math.sin(a1))
          + "A" + r + "," + r + " 0 " + large + " 0 " + (cx + r * Math.cos(a0)) + "," + (cy + r * Math.sin(a0)) + "Z",
      });
      const pct = Math.round(100 * item.value / total);
      hoverable(path, item.label, [{ value: fmt(item.value) + " (" + pct + "%)", name: spec.unit || "", color: color }],
        item.onSelect || (spec.onSelect && function () { spec.onSelect(item); }));
      svg.appendChild(path);
      /* chamada só nas fatias que comportam o texto */
      if (pct >= 8) {
        const mid = (a0 + a1) / 2, rr = (R + r) / 2;
        svg.appendChild(txt(s("text", {
          x: cx + rr * Math.cos(mid), y: cy + rr * Math.sin(mid) + 4,
          "text-anchor": "middle", style: "font-size:11px;font-weight:700;fill:#fff",
        }), pct + "%"));
      }
      angle += span;
    });
    svg.appendChild(txt(s("text", {
      x: cx, y: cy - 2, "text-anchor": "middle",
      style: "font-size:30px;font-weight:650;fill:" + token("--ink"),
    }), compact(total)));
    svg.appendChild(txt(s("text", { class: "tick", x: cx, y: cy + 20, "text-anchor": "middle" }),
      spec.unit || "total"));

    return figure(spec, svg, [legendOf(items.map(function (d, i) {
      return { label: d.label + " · " + fmt(d.value), color: d.color || serie(i) };
    }))]);
  }

  /* ==================================================================== */
  /* funil — etapas ordenadas, rampa de um matiz                          */
  /* ==================================================================== */
  function funnel(spec) {
    const steps = spec.steps || [];
    if (!steps.length) return figure(spec, empty(spec.emptyMessage));
    /* rowH aberto: no mural, quatro etapas precisam ocupar a altura do quadro */
    const rowH = spec.rowH || 46;
    const W = 760, H = steps.length * rowH + 10, ML = 176, MR = 130;
    const peak = Math.max.apply(null, steps.map(function (x) { return x.value; }).concat([1]));
    const svg = svgRoot(W, H, spec.caption || "funil");
    steps.forEach(function (step, i) {
      const y = i * rowH + 6, h = rowH - 14;
      const w = Math.max(3, (W - ML - MR) * step.value / peak);
      const color = ord(i);
      svg.appendChild(txt(s("text", { class: "lab", x: ML - 12, y: y + h / 2 + 4, "text-anchor": "end" }), step.label));
      const node = s("path", { class: "mark", d: capRight(ML, y, w, h), fill: color });
      const share = i ? Math.round(100 * step.value / (steps[i - 1].value || 1)) : 100;
      hoverable(node, step.label, [
        { value: fmt(step.value), name: spec.unit || "artigos", color: color },
        i ? { value: share + "%", name: "da etapa anterior" } : null,
      ].filter(Boolean), step.onSelect);
      svg.appendChild(node);
      svg.appendChild(txt(s("text", { class: "val", x: ML + w + 9, y: y + h / 2 + 4 }), fmt(step.value)));
      if (i) {
        svg.appendChild(txt(s("text", { class: "tick", x: W - 8, y: y + h / 2 + 4, "text-anchor": "end" }),
          share + "% da etapa anterior"));
      }
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* dispersão — no máximo 3 séries (limite de "todos os pares")          */
  /* ==================================================================== */
  function scatter(spec) {
    const points = spec.points || [];
    if (!points.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 320, ML = 56, MR = 24, MT = 18, MB = 46;
    const iw = W - ML - MR, ih = H - MT - MB;
    const xs = points.map(function (p) { return p.x; }), ys = points.map(function (p) { return p.y; });
    const sx = niceTicks(Math.max.apply(null, xs.concat([0])), 4);
    const sy = niceTicks(Math.max.apply(null, ys.concat([0])), 4);
    const X = function (v) { return ML + iw * v / sx.max; };
    const Y = function (v) { return MT + ih - ih * v / sy.max; };
    const svg = svgRoot(W, H, spec.caption || "dispersão");

    sy.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: ML, x2: W - MR, y1: Y(t), y2: Y(t) }));
      svg.appendChild(txt(s("text", { class: "tick", x: ML - 8, y: Y(t) + 3.5, "text-anchor": "end" }), fmt(t)));
    });
    sx.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: X(t), x2: X(t), y1: MT, y2: MT + ih }));
      svg.appendChild(txt(s("text", { class: "tick", x: X(t), y: H - MB + 16, "text-anchor": "middle" }), fmt(t)));
    });
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: W - MR, y1: Y(0), y2: Y(0) }));
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: ML, y1: MT, y2: MT + ih }));
    if (spec.xLabel) svg.appendChild(txt(s("text", { class: "lab", x: ML + iw / 2, y: H - 6, "text-anchor": "middle" }), spec.xLabel));
    if (spec.yLabel) svg.appendChild(txt(s("text", {
      class: "lab", x: 12, y: MT + ih / 2, "text-anchor": "middle",
      transform: "rotate(-90 12 " + (MT + ih / 2) + ")",
    }), spec.yLabel));

    points.forEach(function (p) {
      const color = p.color || serie(p.group || 0);
      const g = s("g");
      /* alvo transparente de 24px: ninguém acerta um ponto de 8px no centro */
      g.appendChild(s("circle", { class: "hit", cx: X(p.x), cy: Y(p.y), r: 12 }));
      g.appendChild(s("circle", { class: "mark ring", cx: X(p.x), cy: Y(p.y), r: p.r || 5, fill: color }));
      hoverable(g, p.label, [
        { value: fmt(p.x), name: spec.xLabel || "x", color: color },
        { value: fmt(p.y), name: spec.yLabel || "y" },
      ], p.onSelect);
      svg.appendChild(g);
    });

    const groups = spec.groups || [];
    return figure(spec, svg, groups.length > 1
      ? [legendOf(groups.map(function (g, i) { return { label: g, color: serie(i) }; }))] : []);
  }

  /* ==================================================================== */
  /* halteres — antes → depois por item                                    */
  /* ==================================================================== */
  function dumbbell(spec) {
    const items = spec.items || [];
    if (!items.length) return figure(spec, empty(spec.emptyMessage));
    const rowH = 30, W = 760, ML = spec.labelWidth || 210, MR = 70;
    const H = items.length * rowH + 30;
    const iw = W - ML - MR;
    const peak = Math.max.apply(null, items.reduce(function (a, d) { return a.concat([d.from, d.to]); }, [0]));
    const scale = niceTicks(peak, 4);
    const X = function (v) { return ML + iw * v / scale.max; };
    const svg = svgRoot(W, H, spec.caption || "antes e depois");
    const cFrom = seq(200), cTo = seq(500);

    scale.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: X(t), x2: X(t), y1: 4, y2: H - 26 }));
      svg.appendChild(txt(s("text", { class: "tick", x: X(t), y: H - 10, "text-anchor": "middle" }), fmt(t)));
    });
    items.forEach(function (item, i) {
      const y = i * rowH + 18;
      svg.appendChild(txt(s("text", { class: "lab", x: ML - 12, y: y + 4, "text-anchor": "end" }),
        item.label.length > 30 ? item.label.slice(0, 29) + "…" : item.label));
      svg.appendChild(s("line", {
        x1: X(item.from), x2: X(item.to), y1: y, y2: y,
        stroke: token("--axis"), "stroke-width": 2, "stroke-linecap": "round",
      }));
      const g = s("g");
      g.appendChild(s("circle", { class: "hit", cx: (X(item.from) + X(item.to)) / 2, cy: y, r: 12 }));
      g.appendChild(s("circle", { class: "mark ring", cx: X(item.from), cy: y, r: 5, fill: cFrom }));
      g.appendChild(s("circle", { class: "mark ring", cx: X(item.to), cy: y, r: 5, fill: cTo }));
      hoverable(g, item.label, [
        { value: fmt(item.from), name: spec.fromLabel || "antes", color: cFrom },
        { value: fmt(item.to), name: spec.toLabel || "depois", color: cTo },
      ], item.onSelect);
      svg.appendChild(g);
      svg.appendChild(txt(s("text", { class: "val", x: W - MR + 10, y: y + 4 }), fmt(item.to - item.from)));
    });
    return figure(spec, svg, [legendOf([
      { label: spec.fromLabel || "antes", color: cFrom },
      { label: spec.toLabel || "depois", color: cTo },
    ])]);
  }

  /* ==================================================================== */
  /* mapa de calor ano × mês — magnitude, rampa de um matiz               */
  /* ==================================================================== */
  const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  function heatmap(spec) {
    const years = spec.years || [];
    const values = spec.values || [];
    if (!years.length) return figure(spec, empty(spec.emptyMessage));
    const cell = 42, ML = 46, MT = 24;
    const W = ML + 12 * cell + 8, H = MT + years.length * cell + 10;
    const peak = Math.max.apply(null, values.concat([1]));
    const svg = svgRoot(W, H, spec.caption || "mapa de calor");

    MESES.forEach(function (m, i) {
      svg.appendChild(txt(s("text", { class: "tick", x: ML + i * cell + cell / 2, y: MT - 8, "text-anchor": "middle" }), m));
    });
    years.forEach(function (year, r) {
      svg.appendChild(txt(s("text", { class: "tick", x: ML - 8, y: MT + r * cell + cell * 0.62, "text-anchor": "end" }), year));
      for (let c = 0; c < 12; c++) {
        const v = values[r * 12 + c] || 0;
        const stepIndex = v ? Math.min(SEQ_STEPS.length - 1, Math.round((v / peak) * (SEQ_STEPS.length - 1))) : -1;
        const fill = v ? seq(SEQ_STEPS[stepIndex]) : token("--surface-raised");
        const node = s("rect", {
          class: "mark", x: ML + c * cell + GAP / 2, y: MT + r * cell + GAP / 2,
          width: cell - GAP, height: cell - GAP, rx: 5, fill: fill,
          stroke: v ? "none" : token("--grid"), "stroke-width": v ? 0 : 1,
        });
        hoverable(node, MESES[c] + "/" + year,
          [{ value: fmt(v), name: spec.unit || "", color: v ? fill : token("--axis") }],
          spec.onSelect && function () { spec.onSelect(year, c + 1); });
        svg.appendChild(node);
        if (v) {
          /* texto branco ou tinta conforme a luminância do preenchimento */
          const light = stepIndex <= 2;
          svg.appendChild(txt(s("text", {
            x: ML + c * cell + cell / 2, y: MT + r * cell + cell * 0.62, "text-anchor": "middle",
            style: "font-size:11.5px;font-weight:700;fill:" + (light ? token("--ink") : "#fff"),
          }), v));
        }
      }
    });
    return figure(spec, svg, [scaleLegend(0, peak, seq(100), seq(700), spec.unit)]);
  }

  /* ==================================================================== */
  /* distribuição — quartis, mediana e extremos                           */
  /* ==================================================================== */
  function distribution(spec) {
    const groups = (spec.groups || []).filter(function (g) { return g.values && g.values.length; });
    if (!groups.length) return figure(spec, empty(spec.emptyMessage));
    const rowH = 54, W = 760, ML = spec.labelWidth || 180, MR = 26;
    const H = groups.length * rowH + 34;
    const iw = W - ML - MR;
    const peak = Math.max.apply(null, groups.reduce(function (a, g) { return a.concat(g.values); }, [0]));
    const scale = niceTicks(peak, 4);
    const X = function (v) { return ML + iw * v / scale.max; };
    const svg = svgRoot(W, H, spec.caption || "distribuição");

    scale.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: X(t), x2: X(t), y1: 6, y2: H - 28 }));
      svg.appendChild(txt(s("text", { class: "tick", x: X(t), y: H - 10, "text-anchor": "middle" }), fmt(t)));
    });

    groups.forEach(function (group, i) {
      const sorted = group.values.slice().sort(function (a, b) { return a - b; });
      const q = function (p) {
        const pos = (sorted.length - 1) * p;
        const low = Math.floor(pos), high = Math.min(low + 1, sorted.length - 1);
        return sorted[low] + (sorted[high] - sorted[low]) * (pos - low);
      };
      const y = i * rowH + 22, color = group.color || serie(i);
      const q1 = q(0.25), med = q(0.5), q3 = q(0.75);
      svg.appendChild(txt(s("text", { class: "lab", x: ML - 12, y: y + 4, "text-anchor": "end" }), group.label));
      /* bigodes */
      svg.appendChild(s("line", {
        x1: X(sorted[0]), x2: X(sorted[sorted.length - 1]), y1: y, y2: y,
        stroke: token("--axis"), "stroke-width": 1.5, "stroke-linecap": "round",
      }));
      /* caixa interquartil */
      svg.appendChild(s("rect", {
        class: "mark", x: X(q1), y: y - 9, width: Math.max(2, X(q3) - X(q1)), height: 18,
        rx: 4, fill: color, "fill-opacity": 0.28, stroke: color, "stroke-width": 1.5,
      }));
      /* mediana */
      svg.appendChild(s("line", { x1: X(med), x2: X(med), y1: y - 11, y2: y + 11, stroke: color, "stroke-width": 2.5 }));
      /* pontos individuais, discretos */
      sorted.forEach(function (v) {
        svg.appendChild(s("circle", { cx: X(v), cy: y + 17, r: 2.5, fill: color, "fill-opacity": 0.5 }));
      });
      const hit = s("rect", { class: "hit", x: ML, y: y - 20, width: iw, height: rowH - 6 });
      hoverable(hit, group.label, [
        { value: fmt(med), name: "mediana", color: color },
        { value: fmt(q1) + " – " + fmt(q3), name: "intervalo interquartil" },
        { value: fmt(sorted[0]) + " – " + fmt(sorted[sorted.length - 1]), name: "mín – máx" },
        { value: sorted.length, name: "observações" },
      ], group.onSelect);
      svg.appendChild(hit);
      svg.appendChild(txt(s("text", { class: "val", x: X(med), y: y - 15, "text-anchor": "middle" }), fmt(med)));
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* treemap — participação por área                                       */
  /* ==================================================================== */
  function treemap(spec) {
    const items = (spec.items || []).filter(function (d) { return d.value > 0; })
      .sort(function (a, b) { return b.value - a.value; });
    if (!items.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 300;
    const total = items.reduce(function (a, b) { return a + b.value; }, 0);
    const svg = svgRoot(W, H, spec.caption || "participação");

    /* fatiamento alternado: simples, estável e sem dependência externa */
    function layout(list, x, y, w, h, horizontal) {
      if (!list.length) return [];
      if (list.length === 1) return [{ item: list[0], x: x, y: y, w: w, h: h }];
      const sum = list.reduce(function (a, b) { return a + b.value; }, 0);
      let acc = 0, cut = 1;
      for (let i = 0; i < list.length; i++) {
        acc += list[i].value;
        if (acc >= sum / 2) { cut = i + 1; break; }
      }
      const share = list.slice(0, cut).reduce(function (a, b) { return a + b.value; }, 0) / sum;
      if (horizontal) {
        return layout(list.slice(0, cut), x, y, w * share, h, !horizontal)
          .concat(layout(list.slice(cut), x + w * share, y, w * (1 - share), h, !horizontal));
      }
      return layout(list.slice(0, cut), x, y, w, h * share, !horizontal)
        .concat(layout(list.slice(cut), x, y + h * share, w, h * (1 - share), !horizontal));
    }

    layout(items, 0, 0, W, H, true).forEach(function (box, i) {
      const color = box.item.color || serie(i);
      const node = s("rect", {
        class: "mark", x: box.x + GAP / 2, y: box.y + GAP / 2,
        width: Math.max(1, box.w - GAP), height: Math.max(1, box.h - GAP),
        rx: 6, fill: color, "fill-opacity": 0.9,
      });
      const pct = Math.round(100 * box.item.value / total);
      hoverable(node, box.item.label,
        [{ value: fmt(box.item.value) + " (" + pct + "%)", name: spec.unit || "", color: color }],
        box.item.onSelect || (spec.onSelect && function () { spec.onSelect(box.item); }));
      svg.appendChild(node);
      /* rótulo só quando cabe com folga; senão fica na dica e na tabela */
      if (box.w > 92 && box.h > 38) {
        svg.appendChild(txt(s("text", {
          x: box.x + 10, y: box.y + 22, style: "font-size:12px;font-weight:650;fill:#fff",
        }), box.item.label.length > box.w / 7 ? box.item.label.slice(0, Math.floor(box.w / 7)) + "…" : box.item.label));
        svg.appendChild(txt(s("text", {
          x: box.x + 10, y: box.y + 39, style: "font-size:11px;fill:#fff;fill-opacity:.85",
        }), fmt(box.item.value) + " · " + pct + "%"));
      }
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* Sankey — o caminho das submissões                                     */
  /* ==================================================================== */
  function sankey(spec) {
    const nodes = spec.nodes || [];
    const links = spec.links || [];
    if (!nodes.length || !links.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 340, PAD = 16, NODE_W = 14;
    const depths = Array.from(new Set(nodes.map(function (n) { return n.depth; }))).sort();
    const colX = {};
    depths.forEach(function (d, i) {
      colX[d] = depths.length === 1 ? PAD : PAD + (W - 2 * PAD - NODE_W) * i / (depths.length - 1);
    });

    const totals = {};
    nodes.forEach(function (n) {
      totals[n.id] = Math.max(
        links.filter(function (l) { return l.source === n.id; })
          .reduce(function (a, l) { return a + l.value; }, 0),
        links.filter(function (l) { return l.target === n.id; })
          .reduce(function (a, l) { return a + l.value; }, 0));
    });
    const byDepth = {};
    nodes.forEach(function (n) { (byDepth[n.depth] = byDepth[n.depth] || []).push(n); });
    const pos = {};
    Object.keys(byDepth).forEach(function (d) {
      const list = byDepth[d];
      const sum = list.reduce(function (a, n) { return a + totals[n.id]; }, 0) || 1;
      const gaps = (list.length - 1) * 10;
      let y = PAD;
      list.forEach(function (n) {
        const h = Math.max(6, (H - 2 * PAD - gaps) * totals[n.id] / sum);
        pos[n.id] = { x: colX[n.depth], y: y, h: h, out: y, in: y };
        y += h + 10;
      });
    });

    const svg = svgRoot(W, H, spec.caption || "fluxo");
    links.slice().sort(function (a, b) { return b.value - a.value; }).forEach(function (link) {
      const a = pos[link.source], b = pos[link.target];
      if (!a || !b) return;
      const sum = links.filter(function (l) { return l.source === link.source; })
        .reduce(function (acc, l) { return acc + l.value; }, 0) || 1;
      const inSum = links.filter(function (l) { return l.target === link.target; })
        .reduce(function (acc, l) { return acc + l.value; }, 0) || 1;
      const th1 = a.h * link.value / sum, th2 = b.h * link.value / inSum;
      const x1 = a.x + NODE_W, x2 = b.x, mid = (x1 + x2) / 2;
      const color = link.color || serie(link.group || 0);
      const path = s("path", {
        class: "mark",
        d: "M" + x1 + "," + a.out + " C" + mid + "," + a.out + " " + mid + "," + b.in + " " + x2 + "," + b.in
          + " L" + x2 + "," + (b.in + th2)
          + " C" + mid + "," + (b.in + th2) + " " + mid + "," + (a.out + th1) + " " + x1 + "," + (a.out + th1) + " Z",
        fill: color, "fill-opacity": 0.32,
      });
      const nameOf = function (id) {
        const found = nodes.find(function (n) { return n.id === id; });
        return found ? found.label : id;
      };
      hoverable(path, nameOf(link.source) + " → " + nameOf(link.target),
        [{ value: fmt(link.value), name: spec.unit || "", color: color }], link.onSelect);
      svg.appendChild(path);
      a.out += th1;
      b.in += th2;
    });

    nodes.forEach(function (n, i) {
      const p = pos[n.id];
      if (!p) return;
      const color = n.color || serie(i);
      svg.appendChild(s("rect", { class: "mark", x: p.x, y: p.y, width: NODE_W, height: p.h, rx: 3, fill: color }));
      const atEnd = n.depth === depths[depths.length - 1];
      /* auréola na cor da superfície: o rótulo cruza as faixas sem sumir */
      svg.appendChild(txt(s("text", {
        class: "lab", x: atEnd ? p.x - 8 : p.x + NODE_W + 8, y: p.y + p.h / 2 + 4,
        "text-anchor": atEnd ? "end" : "start",
        stroke: token("--surface"), "stroke-width": 3.5, "stroke-linejoin": "round",
        "paint-order": "stroke fill",
      }), n.label + " (" + fmt(totals[n.id]) + ")"));
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* rede de coautoria                                                     */
  /* ==================================================================== */
  function network(spec) {
    const nodes = spec.nodes || [], links = spec.links || [];
    if (!nodes.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 470;
    /* Fruchterman–Reingold determinístico: o mesmo dado gera o mesmo desenho */
    const k = Math.sqrt(W * H / nodes.length);
    const pos = new Map();
    nodes.forEach(function (n, i) {
      const a = 2 * Math.PI * i / nodes.length;
      pos.set(n.id, { x: W / 2 + Math.cos(a) * W * 0.33, y: H / 2 + Math.sin(a) * H * 0.33, dx: 0, dy: 0 });
    });
    let temp = W * 0.1;
    for (let it = 0; it < 400; it++) {
      pos.forEach(function (p) { p.dx = 0; p.dy = 0; });
      for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
        const a = pos.get(nodes[i].id), b = pos.get(nodes[j].id);
        const dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy) || 0.01, rep = k * k / d;
        a.dx += dx / d * rep; a.dy += dy / d * rep;
        b.dx -= dx / d * rep; b.dy -= dy / d * rep;
      }
      links.forEach(function (e) {
        const a = pos.get(e.source), b = pos.get(e.target);
        if (!a || !b) return;
        const dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy) || 0.01;
        const att = d * d / k * (1 + Math.log(1 + e.weight)) * 0.55;
        a.dx -= dx / d * att; a.dy -= dy / d * att;
        b.dx += dx / d * att; b.dy += dy / d * att;
      });
      pos.forEach(function (p) {
        const d = Math.hypot(p.dx, p.dy) || 0.01;
        p.x = Math.max(30, Math.min(W - 30, p.x + p.dx / d * Math.min(d, temp)));
        p.y = Math.max(30, Math.min(H - 30, p.y + p.dy / d * Math.min(d, temp)));
      });
      temp *= 0.965;
    }

    const svg = svgRoot(W, H, spec.caption || "rede");
    const maxW = Math.max.apply(null, links.map(function (e) { return e.weight; }).concat([1]));
    const maxA = Math.max.apply(null, nodes.map(function (n) { return n.weight; }).concat([1]));
    const edges = s("g");
    svg.appendChild(edges);
    links.forEach(function (e) {
      const a = pos.get(e.source), b = pos.get(e.target);
      if (!a || !b) return;
      edges.appendChild(s("line", {
        x1: a.x, y1: a.y, x2: b.x, y2: b.y,
        stroke: token("--axis"), "stroke-width": 1 + 3 * e.weight / maxW, "stroke-opacity": 0.7,
      }));
    });
    nodes.forEach(function (n) {
      const p = pos.get(n.id);
      const r = 8 + 15 * Math.sqrt(n.weight / maxA);
      const g = s("g");
      g.appendChild(s("circle", { class: "hit", cx: p.x, cy: p.y, r: Math.max(r, 14) }));
      g.appendChild(s("circle", {
        class: "mark ring", cx: p.x, cy: p.y, r: r,
        fill: n.color || serie(n.group || 0), "fill-opacity": 0.9,
      }));
      hoverable(g, n.label, [
        { value: fmt(n.weight), name: spec.unit || "artigos", color: n.color || serie(n.group || 0) },
        { value: fmt(n.degree), name: "coautores" },
      ], n.onSelect);
      svg.appendChild(g);
      svg.appendChild(txt(s("text", { class: "lab", x: p.x, y: p.y + r + 13, "text-anchor": "middle" }),
        n.label.length > 16 ? n.label.slice(0, 15) + "…" : n.label));
    });
    return figure(spec, svg, spec.groups && spec.groups.length > 1
      ? [legendOf(spec.groups.map(function (g, i) { return { label: g, color: serie(i) }; }))] : []);
  }

  /* ==================================================================== */
  /* bolhas geográficas — no máximo 3 categorias                          */
  /* ==================================================================== */
  function geo(spec) {
    const points = (spec.points || []).filter(function (p) {
      return p.lat !== null && p.lat !== undefined && p.lon !== null && p.lon !== undefined;
    });
    if (!points.length) return figure(spec, empty(spec.emptyMessage || "Sem coordenadas cadastradas."));
    const W = 760, H = spec.height || 400, pad = 54;
    let latMin = Math.min.apply(null, points.map(function (p) { return p.lat; }));
    let latMax = Math.max.apply(null, points.map(function (p) { return p.lat; }));
    let lonMin = Math.min.apply(null, points.map(function (p) { return p.lon; }));
    let lonMax = Math.max.apply(null, points.map(function (p) { return p.lon; }));
    const spanLat = Math.max(latMax - latMin, 2), spanLon = Math.max(lonMax - lonMin, 2);
    latMin -= spanLat * 0.2; latMax += spanLat * 0.2;
    lonMin -= spanLon * 0.2; lonMax += spanLon * 0.2;
    const X = function (lon) { return pad + (lon - lonMin) / (lonMax - lonMin) * (W - 2 * pad); };
    const Y = function (lat) { return pad + (latMax - lat) / (latMax - latMin) * (H - 2 * pad); };
    const svg = svgRoot(W, H, spec.caption || "mapa");

    for (let i = 0; i <= 4; i++) {
      const lat = latMin + (latMax - latMin) * i / 4, lon = lonMin + (lonMax - lonMin) * i / 4;
      svg.appendChild(s("line", { class: "grid-line", x1: pad, x2: W - pad, y1: Y(lat), y2: Y(lat) }));
      svg.appendChild(s("line", { class: "grid-line", y1: pad, y2: H - pad, x1: X(lon), x2: X(lon) }));
      svg.appendChild(txt(s("text", { class: "tick", x: pad - 8, y: Y(lat) + 3, "text-anchor": "end" }), lat.toFixed(1) + "°"));
      svg.appendChild(txt(s("text", { class: "tick", x: X(lon), y: H - pad + 16, "text-anchor": "middle" }), lon.toFixed(1) + "°"));
    }
    (spec.outline || []).forEach(function (ring) {
      const d = ring.map(function (pt, i) { return (i ? "L" : "M") + X(pt[0]) + " " + Y(pt[1]); }).join(" ");
      svg.appendChild(s("path", {
        d: d + "Z", fill: token("--surface-raised"), "fill-opacity": 0.8,
        stroke: token("--grid"), "stroke-width": 1,
      }));
    });

    const peak = Math.max.apply(null, points.map(function (p) { return p.value; }).concat([1]));
    points.forEach(function (p) {
      const r = 7 + 17 * Math.sqrt(p.value / peak);
      const color = p.color || serie(p.group || 0);
      const g = s("g");
      g.appendChild(s("circle", { class: "hit", cx: X(p.lon), cy: Y(p.lat), r: Math.max(r, 14) }));
      g.appendChild(s("circle", {
        class: "mark", cx: X(p.lon), cy: Y(p.lat), r: r,
        fill: color, "fill-opacity": 0.45, stroke: color, "stroke-width": 1.5,
      }));
      hoverable(g, p.label, [{ value: fmt(p.value), name: spec.unit || "", color: color }], p.onSelect);
      svg.appendChild(g);
      svg.appendChild(txt(s("text", { class: "lab", x: X(p.lon), y: Y(p.lat) - r - 6, "text-anchor": "middle" }), p.label));
    });
    return figure(spec, svg);
  }


  /* ==================================================================== */
  /* mapa-múndi — coroplético                                             */
  /*                                                                      */
  /* A versão anterior desenhava dez manchas à mão e espetava bolhas nelas.*/
  /* Continente irreconhecível e bolha sem território não dizem de onde    */
  /* vem a produção: dizem que alguém quis um mapa. Aqui o contorno é o    */
  /* de verdade (Natural Earth, simplificado) e a cor do país É o valor -- */
  /* um tom só, do claro ao escuro, que é como se lê magnitude num mapa.   */
  /* ==================================================================== */
  const PASSOS_MAPA = ["--seq-300", "--seq-400", "--seq-500", "--seq-600", "--seq-700"];

  /* Cortes por quantil, não por fatia igual do máximo. Com um país
     dominante -- e é sempre o caso aqui, o laboratório é brasileiro --
     a fatia igual pinta o Brasil no topo e joga o resto do mundo todo
     no primeiro tom: um mapa de duas cores que não separa ninguém. */
  function cortesQuantil(valores, n) {
    const ordenados = valores.slice().sort(function (a, b) { return a - b; });
    const unicos = ordenados.filter(function (v, i) { return i === 0 || v !== ordenados[i - 1]; });
    if (unicos.length <= n) return unicos;
    const cortes = [];
    for (let i = 1; i <= n; i++) {
      cortes.push(ordenados[Math.min(ordenados.length - 1,
        Math.ceil(i * ordenados.length / n) - 1)]);
    }
    return cortes.filter(function (v, i) { return i === 0 || v !== cortes[i - 1]; });
  }

  function faixaDe(valor, cortes) {
    for (let i = 0; i < cortes.length; i++) if (valor <= cortes[i]) return i;
    return cortes.length - 1;
  }

  function centroDoAnel(anel) {
    let x = 0, y = 0;
    anel.forEach(function (pt) { x += pt[0]; y += pt[1]; });
    return [x / anel.length, y / anel.length];
  }

  function mapaMundi(spec) {
    const mundo = spec.world || [];
    const valores = spec.values || {};
    /* O viewBox é grande de propósito: SVG não tem resolução, então o
       mesmo desenho serve a um monitor 4K e a um projetor de sala. */
    const W = 1600, H = 780;
    const LON0 = -180, LON1 = 180, LAT0 = -58, LAT1 = 84;
    const X = function (lon) { return (lon - LON0) / (LON1 - LON0) * W; };
    const Y = function (lat) { return H - (lat - LAT0) / (LAT1 - LAT0) * H; };
    const svg = svgRoot(W, H, spec.caption || "mapa-múndi da produção");

    if (!mundo.length) {
      const aviso = el("p", { class: "hint", text: spec.loadingMessage || "Carregando o mapa…" });
      return figure(spec, aviso);
    }

    svg.appendChild(s("rect", { x: 0, y: 0, width: W, height: H, rx: 8,
      fill: token("--surface-sunken") }));
    /* A Antartida fica abaixo do enquadramento e, sem recorte, era
       desenhada FORA da moldura -- uma faixa de terra solta embaixo do
       gráfico, que ninguém sabia o que era. */
    const idRecorte = "mapa-recorte-" + Math.random().toString(36).slice(2, 8);
    const defs = s("defs");
    const recorte = s("clipPath", { id: idRecorte });
    recorte.appendChild(s("rect", { x: 0, y: 0, width: W, height: H, rx: 8 }));
    defs.appendChild(recorte);
    svg.appendChild(defs);
    const terra = s("g", { "clip-path": "url(#" + idRecorte + ")" });
    svg.appendChild(terra);

    /* O país entra na conta pelo nome em português, pelo nome em inglês
       ou pelo código de três letras -- de onde vem o dado varia. */
    const porChave = {};
    Object.keys(valores).forEach(function (k) {
      porChave[String(k).toLowerCase()] = valores[k];
    });
    const valorDe = function (pais) {
      const chaves = [pais.nome, pais.en, pais.id];
      for (let i = 0; i < chaves.length; i++) {
        const v = porChave[String(chaves[i] || "").toLowerCase()];
        if (v !== undefined && v !== null) return v;
      }
      return null;
    };

    /* O nome do pais que mudou chega como veio do servidor; a comparacao
       aqui usa as mesmas tres chaves de `valorDe`, senao "Estados Unidos"
       nunca casaria com "United States". */
    const acesos = {};
    (spec.highlight || []).forEach(function (k) {
      acesos[String(k).toLowerCase()] = true; });
    const aceso = function (pais) {
      return [pais.nome, pais.en, pais.id].some(function (k) {
        return acesos[String(k || "").toLowerCase()]; });
    };

    /* `foco`: um pais escolhido a mao, que o mapa tem de LOCALIZAR. E outra
       coisa que `highlight` -- ali a marca dura um piscar e diz "isto mudou
       agora"; aqui ela fica, e diz "e este que voce esta olhando". Sem o
       foco, clicar num botao de pais mudava a tabela e deixava o mapa
       exatamente igual: quem estava a tres metros nao via nada acontecer. */
    const alvo = String(spec.foco || "").toLowerCase();
    const focado = function (pais) {
      return !!alvo && [pais.nome, pais.en, pais.id].some(function (k) {
        return String(k || "").toLowerCase() === alvo; });
    };

    const comDado = mundo.map(valorDe).filter(function (v) { return v !== null && v > 0; });
    const cortes = comDado.length ? cortesQuantil(comDado, PASSOS_MAPA.length) : [];
    const tons = PASSOS_MAPA.slice(PASSOS_MAPA.length - cortes.length).map(token);
    const neutro = token("--surface-raised");
    const contorno = token("--border-strong");

    const marcados = [];
    let noFoco = null;
    mundo.forEach(function (pais) {
      const valor = valorDe(pais);
      const d = pais.d.map(function (anel) {
        return anel.map(function (pt, i) {
          return (i ? "L" : "M") + X(pt[0]).toFixed(1) + " " + Y(pt[1]).toFixed(1);
        }).join(" ") + " Z";
      }).join(" ");
      const forma = s("path", {
        d: d, fill: valor ? tons[faixaDe(valor, cortes)] : neutro,
        stroke: contorno, "stroke-width": 0.8, "stroke-linejoin": "round",
      });
      if (valor) {
        const g = s("g");
        g.appendChild(forma);
        /* `highlight`: o pais que mudou desde o desenho anterior ganha um
           contorno aceso e pisca uma vez. Num painel de parede, "ao vivo"
           que nao se ve e o mesmo que parado -- a cor da faixa muda de um
           tom para o vizinho e ninguem percebe. Quem pediu menos
           movimento fica so com o contorno, que ja basta. */
        if (aceso(pais)) {
          forma.setAttribute("stroke", token("--accent-strong"));
          forma.setAttribute("stroke-width", 2.6);
          g.classList.add("acendeu");
        }
        const item = { pais: pais, valor: valor };
        if (focado(pais)) {
          forma.setAttribute("stroke", token("--ink"));
          forma.setAttribute("stroke-width", 3.4);
          g.classList.add("emfoco");
          /* o MESMO objeto que entra em `marcados`: com uma copia, o
             `indexOf` la embaixo devolveria -1 e o pais focado perderia a
             frente da fila de rotulos calado */
          noFoco = item;
        }
        hoverable(g, pais.nome,
          [{ value: fmt(valor), name: spec.unit || "artigos",
             color: tons[faixaDe(valor, cortes)] }],
          spec.onSelect ? function () { spec.onSelect(pais.nome); } : null);
        terra.appendChild(g);
        marcados.push(item);
      } else {
        terra.appendChild(forma);
      }
    });

    if (!marcados.length) {
      /* Sem país registrado, o mapa cheio de terra neutra ainda parece um
         resultado. Dizer que está vazio -- e por quê -- vale mais. */
      svg.appendChild(txt(s("text", {
        x: W / 2, y: H / 2, "text-anchor": "middle",
        style: "font-size:22px;font-weight:650;fill:" + token("--ink-2"),
      }), spec.emptyMessage || "Nenhum país registrado ainda."));
      if (spec.emptyHint) {
        svg.appendChild(txt(s("text", {
          x: W / 2, y: H / 2 + 30, "text-anchor": "middle",
          style: "font-size:15px;fill:" + token("--ink-muted"),
        }), spec.emptyHint));
      }
      return figure(spec, svg, [legendaDoMapa([], [], neutro, spec)]);
    }

    /* Rótulo direto só nos primeiros: um número em cada país devolveria
       a tabela que o mapa veio substituir. Portugal e Espanha são
       vizinhos e pequenos: sem desviar um do outro, os dois rótulos
       saíam impressos um por cima do outro, ilegíveis. */
    /* A MIRA no pais focado.
       So o contorno nao resolve: a Italia tem o tamanho de uma unha no
       mapa-mundi, e um traco em volta dela e invisivel a tres metros --
       era possivel clicar em "Italia" e nao ver nada acontecer no mapa. Um
       par de circulos concentricos no centro do pais tem tamanho proprio,
       independente do tamanho do pais, e por isso funciona igual para a
       Italia e para o Brasil. */
    const ocupados = [];
    if (noFoco) {
      const maiorAnel = noFoco.pais.d.slice().sort(function (a, b) {
        return b.length - a.length; })[0];
      const centro = centroDoAnel(maiorAnel);
      const cx = X(centro[0]), cy = Y(centro[1]);
      const acento = token("--accent-strong");
      const mira = s("g", { class: "mira-foco", "pointer-events": "none" });
      mira.appendChild(s("circle", { cx: cx, cy: cy, r: 26, fill: "none",
        stroke: acento, "stroke-width": 2.6, "stroke-opacity": 0.95 }));
      mira.appendChild(s("circle", { cx: cx, cy: cy, r: 40, fill: "none",
        stroke: acento, "stroke-width": 1.3, "stroke-opacity": 0.4 }));
      /* quatro riscos de mira, e nao um circulo cheio: o preenchimento
         esconderia justamente o pais que se quer olhar */
      [[0, -1], [0, 1], [-1, 0], [1, 0]].forEach(function (d) {
        mira.appendChild(s("line", {
          x1: cx + d[0] * 15, y1: cy + d[1] * 15,
          x2: cx + d[0] * 34, y2: cy + d[1] * 34,
          stroke: acento, "stroke-width": 2.2, "stroke-linecap": "round",
        }));
      });
      svg.appendChild(mira);
      /* a mira ocupa lugar: sem reservar, o rotulo do proprio pais focado
         era impresso por cima dela e os dois ficavam ilegiveis juntos */
      ocupados.push([cx - 44, cy - 44, cx + 44, cy + 44]);
    }

    marcados.sort(function (a, b) { return b.valor - a.valor; });
    /* o focado entra na frente da fila de rotulos: e o unico que a pessoa
       pediu para ver, e seria perverso ele ser o omitido por falta de lugar */
    if (noFoco) {
      const posicao = marcados.indexOf(noFoco);
      if (posicao > 0) {
        marcados.splice(posicao, 1);
        marcados.unshift(noFoco);
      }
    }
    const DESVIOS = [[0, 0], [0, -30], [0, 30], [0, -60], [0, 60], [0, -90], [0, 90]];
    const quantos = spec.labelCount || 5;
    marcados.slice(0, noFoco ? Math.max(quantos, 1) : quantos).forEach(function (item) {
      const maior = item.pais.d.slice().sort(function (a, b) {
        return b.length - a.length; })[0];
      const centro = centroDoAnel(maior);
      const rotulo = item.pais.nome + " · " + fmt(item.valor);
      const cx = X(centro[0]), cy = Y(centro[1]);
      const meia = rotulo.length * 4.6, alt = 11;
      let alvo = null;
      for (let i = 0; i < DESVIOS.length && !alvo; i++) {
        const x = cx + DESVIOS[i][0], y = cy + DESVIOS[i][1];
        const caixa = [x - meia, y - alt, x + meia, y + alt];
        const bate = ocupados.some(function (o) {
          return !(caixa[2] < o[0] || caixa[0] > o[2] || caixa[3] < o[1] || caixa[1] > o[3]);
        });
        if (!bate) alvo = { x: x, y: y, caixa: caixa, desviou: i > 0 };
      }
      if (!alvo) return;   /* sem lugar limpo: melhor sem rótulo que ilegível */
      ocupados.push(alvo.caixa);
      if (alvo.desviou) {
        svg.appendChild(s("line", { x1: cx, y1: cy, x2: alvo.x, y2: alvo.y,
          stroke: token("--ink-muted"), "stroke-width": 1.2, "stroke-opacity": 0.7 }));
        svg.appendChild(s("circle", { cx: cx, cy: cy, r: 3,
          fill: token("--ink-muted") }));
      }
      const t = s("text", {
        x: alvo.x, y: alvo.y + 5, "text-anchor": "middle",
        style: "font-size:17px;font-weight:750;fill:" + token("--ink")
             + ";paint-order:stroke;stroke:" + token("--surface-sunken")
             + ";stroke-width:5px;stroke-linejoin:round;pointer-events:none",
      });
      svg.appendChild(txt(t, rotulo));
    });

    return figure(spec, svg, [legendaDoMapa(cortes, tons, neutro, spec)]);
  }

  /* A legenda não é enfeite: sem ela a cor é só uma cor. */
  function legendaDoMapa(cortes, tons, neutro, spec) {
    const caixa = el("div", { class: "legenda-mapa" });
    let piso = 1;
    cortes.forEach(function (corte, i) {
      const rotulo = piso === corte ? fmt(corte) : fmt(piso) + "–" + fmt(corte);
      caixa.appendChild(el("span", { class: "chave" }, [
        el("i", { style: "background:" + tons[i] }),
        el("span", { text: rotulo }),
      ]));
      piso = corte + 1;
    });
    caixa.appendChild(el("span", { class: "chave" }, [
      el("i", { style: "background:" + neutro }),
      el("span", { text: "sem registro" }),
    ]));
    if (spec.unit) {
      caixa.appendChild(el("span", { class: "unidade", text: spec.unit }));
    }
    return caixa;
  }

  /* ==================================================================== */
  /* miniaturas: minigráfico e medidor                                     */
  /* ==================================================================== */
  function sparkline(values, opts) {
    opts = opts || {};
    const W = 132, H = 30;
    const svg = svgRoot(W, H, "tendência");
    svg.setAttribute("class", "plot spark");
    if (!values || values.length < 2) return svg;
    const peak = Math.max.apply(null, values.concat([1]));
    const X = function (i) { return W * i / (values.length - 1); };
    const Y = function (v) { return H - 4 - (H - 10) * v / peak; };
    const d = values.map(function (v, i) { return (i ? "L" : "M") + X(i) + " " + Y(v); }).join(" ");
    const color = opts.color || token("--ink-muted");
    svg.appendChild(s("path", {
      d: d + " L" + X(values.length - 1) + " " + H + " L0 " + H + " Z",
      fill: color, "fill-opacity": 0.1,
    }));
    svg.appendChild(s("path", {
      d: d, fill: "none", stroke: color, "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round",
    }));
    svg.appendChild(s("circle", {
      class: "ring", cx: X(values.length - 1), cy: Y(values[values.length - 1]), r: 3.5,
      fill: opts.accent || token("--accent-strong"),
    }));
    return svg;
  }
  function meter(value, limit, opts) {
    opts = opts || {};
    const share = limit ? Math.max(0, Math.min(1, value / limit)) : 0;
    const bar = el("i", { style: "width:" + (share * 100).toFixed(1) + "%" });
    if (opts.severity === "warning") bar.style.background = token("--warning");
    if (opts.severity === "critical") bar.style.background = token("--critical");
    return el("div", {
      class: "meter", role: "meter", "aria-valuenow": String(value),
      "aria-valuemin": "0", "aria-valuemax": String(limit),
      title: fmt(value) + " de " + fmt(limit),
    }, bar);
  }


  /* ==================================================================== */
  /* degradê de preenchimento — um tom só, do opaco ao transparente       */
  /* Usado apenas SOB a linha, nunca por baixo de outra marca: o degradê  */
  /* dá profundidade à área e não interfere no contraste já validado.     */
  /* ==================================================================== */
  let GRAD_SEQ = 0;
  function gradFill(svg, color, top, bottom) {
    const id = "lape-grad-" + (++GRAD_SEQ);
    const stop1 = s("stop", { offset: "0%", "stop-color": color,
      "stop-opacity": top === undefined ? 0.34 : top });
    const stop2 = s("stop", { offset: "100%", "stop-color": color,
      "stop-opacity": bottom === undefined ? 0.02 : bottom });
    const grad = s("linearGradient", { id: id, x1: "0", y1: "0", x2: "0", y2: "1" },
      [stop1, stop2]);
    let defs = svg.querySelector("defs");
    if (!defs) { defs = s("defs", {}); svg.insertBefore(defs, svg.firstChild); }
    defs.appendChild(grad);
    return "url(#" + id + ")";
  }

  /* ==================================================================== */
  /* área empilhada — composição ao longo do tempo                        */
  /* ==================================================================== */
  function area(spec) {
    const labels = spec.labels || [];
    const series = spec.series || [];
    if (!labels.length || !series.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 260, ML = 52, MR = 20, MT = 18, MB = 38;
    const iw = W - ML - MR, ih = H - MT - MB;

    /* pilha acumulada por índice */
    const stack = [];
    let peak = 0;
    labels.forEach(function (_, i) {
      let run = 0;
      const column = series.map(function (x) {
        const base = run;
        run += Number(x.values[i]) || 0;
        return [base, run];
      });
      peak = Math.max(peak, run);
      stack.push(column);
    });
    const scale = niceTicks(peak, 4);
    const X = function (i) { return labels.length === 1 ? ML + iw / 2 : ML + iw * i / (labels.length - 1); };
    const Y = function (v) { return MT + ih - ih * v / scale.max; };

    const svg = svgRoot(W, H, spec.caption || "área empilhada");
    scale.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: ML, x2: W - MR, y1: Y(t), y2: Y(t) }));
      svg.appendChild(txt(s("text", { class: "tick", x: ML - 8, y: Y(t) + 3.5, "text-anchor": "end" }), fmt(t)));
    });
    labels.forEach(function (label, i) {
      svg.appendChild(txt(s("text", { class: "lab", x: X(i), y: H - MB + 16, "text-anchor": "middle" }), label));
    });

    series.forEach(function (serieSpec, si) {
      const color = serieSpec.color || serie(si);
      const upper = labels.map(function (_, i) { return (i ? "L" : "M") + X(i) + " " + Y(stack[i][si][1]); });
      const lower = [];
      for (let i = labels.length - 1; i >= 0; i--) lower.push("L" + X(i) + " " + Y(stack[i][si][0]));
      svg.appendChild(s("path", {
        d: upper.join(" ") + " " + lower.join(" ") + " Z",
        fill: gradFill(svg, color), stroke: "none",
      }));
      svg.appendChild(s("path", {
        d: upper.join(" "), fill: "none", stroke: color, "stroke-width": 2,
        "stroke-linejoin": "round", "stroke-linecap": "round",
      }));
    });
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: W - MR, y1: Y(0), y2: Y(0) }));

    const crosshair = s("line", { class: "crosshair", y1: MT, y2: MT + ih, x1: -99, x2: -99 });
    svg.appendChild(crosshair);
    const hit = s("rect", { class: "hit", x: ML, y: MT, width: iw, height: ih });
    hit.addEventListener("pointermove", function (ev) {
      const box = svg.getBoundingClientRect();
      const px = ((ev.touches ? ev.touches[0] : ev).clientX - box.left) / box.width * W;
      let idx = Math.round((px - ML) / (iw / Math.max(labels.length - 1, 1)));
      idx = Math.max(0, Math.min(labels.length - 1, idx));
      crosshair.setAttribute("x1", X(idx));
      crosshair.setAttribute("x2", X(idx));
      const rows = series.map(function (x, si) {
        return { value: fmt(x.values[idx]), name: x.label, color: x.color || serie(si) };
      });
      rows.push({ value: fmt(stack[idx][series.length - 1][1]), name: "total" });
      showTip(ev, labels[idx], rows);
    });
    hit.addEventListener("pointerleave", function () {
      hideTip();
      crosshair.setAttribute("x1", -99);
      crosshair.setAttribute("x2", -99);
    });
    svg.appendChild(hit);

    const extras = series.length > 1
      ? [legendOf(series.map(function (x, i) { return { label: x.label, color: x.color || serie(i) }; }))]
      : [];
    return figure(spec, svg, extras);
  }

  /* ==================================================================== */
  /* radar — perfil de um mesmo conjunto de eixos comparáveis             */
  /* Só é honesto quando todos os eixos partilham a mesma unidade, ou     */
  /* quando cada um vem normalizado; nunca para grandezas de escala solta.*/
  /* ==================================================================== */
  function radar(spec) {
    const axes = spec.axes || [];
    const series = (spec.series || []).slice(0, 4);
    if (axes.length < 3 || !series.length) return figure(spec, empty(spec.emptyMessage));
    const W = 380, H = spec.height || 340, cx = W / 2, cy = H / 2 - 6, R = Math.min(W, H) / 2 - 54;
    const all = series.reduce(function (acc, x) { return acc.concat(x.values); }, []);
    const scale = niceTicks(Math.max.apply(null, all.concat([0])), 4);
    const step = function (i) { return -Math.PI / 2 + 2 * Math.PI * i / axes.length; };
    const point = function (i, v) {
      const r = R * Math.max(0, v) / scale.max, a = step(i);
      return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    };

    const svg = svgRoot(W, H, spec.caption || "radar");
    svg.setAttribute("class", "plot round");
    /* teias concêntricas em vez de círculos: a leitura segue os eixos */
    scale.ticks.slice(1).forEach(function (t) {
      const ring = axes.map(function (_, i) {
        const p = point(i, t);
        return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1);
      }).join(" ") + " Z";
      svg.appendChild(s("path", { class: "grid-line", d: ring, fill: "none" }));
    });
    axes.forEach(function (label, i) {
      const edge = point(i, scale.max);
      svg.appendChild(s("line", { class: "grid-line", x1: cx, y1: cy, x2: edge[0], y2: edge[1] }));
      const a = step(i);
      const lx = cx + (R + 18) * Math.cos(a), ly = cy + (R + 18) * Math.sin(a);
      const anchor = Math.abs(Math.cos(a)) < 0.2 ? "middle" : (Math.cos(a) > 0 ? "start" : "end");
      svg.appendChild(txt(s("text", { class: "lab", x: lx, y: ly + 4, "text-anchor": anchor }), label));
    });
    svg.appendChild(txt(s("text", { class: "tick", x: cx + 5, y: cy - R + 4 }), fmt(scale.max)));

    series.forEach(function (serieSpec, si) {
      const color = serieSpec.color || serie(si);
      const d = axes.map(function (_, i) {
        const p = point(i, Number(serieSpec.values[i]) || 0);
        return (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1);
      }).join(" ") + " Z";
      svg.appendChild(s("path", { d: d, fill: color, "fill-opacity": series.length > 1 ? 0.13 : 0.2,
        stroke: color, "stroke-width": 2, "stroke-linejoin": "round" }));
      axes.forEach(function (label, i) {
        const p = point(i, Number(serieSpec.values[i]) || 0);
        const dot = s("circle", { class: "ring mark", cx: p[0], cy: p[1], r: 4.5, fill: color });
        hoverable(dot, label, [{ value: fmt(serieSpec.values[i]), name: serieSpec.label, color: color }]);
        svg.appendChild(dot);
      });
    });

    const extras = series.length > 1
      ? [legendOf(series.map(function (x, i) { return { label: x.label, color: x.color || serie(i) }; }))]
      : [];
    return figure(spec, svg, extras);
  }

  /* ==================================================================== */
  /* medidor radial — um número só, com a faixa em que ele cai            */
  /* ==================================================================== */
  function gauge(spec) {
    const max = Number(spec.max) || 0;
    const value = Math.max(0, Number(spec.value) || 0);
    if (!max) return figure(spec, empty(spec.emptyMessage));
    const W = 260, H = 168, cx = W / 2, cy = 138, R = 96, thickness = 17;
    const share = Math.min(1, value / max);
    const arc = function (from, to, radius) {
      const a1 = Math.PI + Math.PI * from, a2 = Math.PI + Math.PI * to;
      const x1 = cx + radius * Math.cos(a1), y1 = cy + radius * Math.sin(a1);
      const x2 = cx + radius * Math.cos(a2), y2 = cy + radius * Math.sin(a2);
      /* meia-lua: a varredura vai no máximo a 180°, então o arco é sempre o curto */
      return "M" + x1.toFixed(1) + " " + y1.toFixed(1) + " A" + radius + " " + radius
        + " 0 0 1 " + x2.toFixed(1) + " " + y2.toFixed(1);
    };
    const svg = svgRoot(W, H, spec.caption || "medidor");
    svg.setAttribute("class", "plot round");
    svg.appendChild(s("path", {
      d: arc(0, 1, R), fill: "none", stroke: token("--grid"),
      "stroke-width": thickness, "stroke-linecap": "round",
    }));
    /* faixas opcionais: [{ até, cor }] — desenhadas por fora, finas */
    (spec.bands || []).forEach(function (band, i, list) {
      const from = i ? list[i - 1].to / max : 0;
      svg.appendChild(s("path", {
        d: arc(from, Math.min(1, band.to / max), R + thickness / 2 + 5), fill: "none",
        stroke: band.color || ord(i), "stroke-width": 3, "stroke-linecap": "butt",
      }));
    });
    const color = spec.color || token("--accent-strong");
    if (share > 0.002) {
      svg.appendChild(s("path", {
        d: arc(0, share, R), fill: "none", stroke: color,
        "stroke-width": thickness, "stroke-linecap": "round",
      }));
    }
    svg.appendChild(txt(s("text", { class: "hero", x: cx, y: cy - 14, "text-anchor": "middle" }),
      spec.display || fmt(spec.value)));
    if (spec.unit) {
      svg.appendChild(txt(s("text", { class: "lab", x: cx, y: cy + 6, "text-anchor": "middle" }), spec.unit));
    }
    svg.appendChild(txt(s("text", { class: "tick", x: cx - R, y: cy + 18, "text-anchor": "middle" }), "0"));
    svg.appendChild(txt(s("text", { class: "tick", x: cx + R, y: cy + 18, "text-anchor": "middle" }), fmt(max)));
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* cascata — de onde saiu e onde parou                                  */
  /* itens: [{ label, value, total }] — `total` desenha a barra desde 0    */
  /* ==================================================================== */
  function waterfall(spec) {
    const items = spec.items || [];
    if (!items.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, H = spec.height || 280, ML = 56, MR = 20, MT = 20, MB = 52;
    const iw = W - ML - MR, ih = H - MT - MB;

    let run = 0, low = 0, high = 0;
    const steps = items.map(function (item) {
      const v = Number(item.value) || 0;
      const from = item.total ? 0 : run;
      const to = item.total ? v : run + v;
      run = to;
      low = Math.min(low, from, to);
      high = Math.max(high, from, to);
      return { label: item.label, value: v, from: from, to: to, total: !!item.total };
    });
    const scale = niceTicks(high, 4);
    const top = scale.max, bottom = Math.min(0, low);
    const Y = function (v) { return MT + ih - ih * (v - bottom) / (top - bottom || 1); };
    const slot = iw / steps.length;
    const bw = Math.min(BAR_MAX * 1.6, slot - 14);

    const svg = svgRoot(W, H, spec.caption || "cascata");
    scale.ticks.forEach(function (t) {
      svg.appendChild(s("line", { class: "grid-line", x1: ML, x2: W - MR, y1: Y(t), y2: Y(t) }));
      svg.appendChild(txt(s("text", { class: "tick", x: ML - 8, y: Y(t) + 3.5, "text-anchor": "end" }), fmt(t)));
    });
    svg.appendChild(s("line", { class: "axis-line", x1: ML, x2: W - MR, y1: Y(0), y2: Y(0) }));

    steps.forEach(function (step, i) {
      const x = ML + slot * i + (slot - bw) / 2;
      const y = Y(Math.max(step.from, step.to));
      const h = Math.max(2, Math.abs(Y(step.to) - Y(step.from)));
      const color = step.total ? token("--accent-strong")
        : (step.value >= 0 ? token("--series-3") : token("--critical"));
      const bar = s("path", {
        class: "mark grow",
        d: capTop(x, y, bw, h, Math.min(R_END, h / 2)),
        fill: color,
      });
      hoverable(bar, step.label, [
        { value: (step.value > 0 && !step.total ? "+" : "") + fmt(step.value), name: "variação", color: color },
        { value: fmt(step.to), name: "acumulado" },
      ]);
      svg.appendChild(bar);
      /* fio ligando um degrau ao próximo — é ele que conta a história */
      if (i < steps.length - 1 && !steps[i + 1].total) {
        svg.appendChild(s("line", {
          x1: x + bw, x2: ML + slot * (i + 1) + (slot - bw) / 2,
          y1: Y(step.to), y2: Y(step.to), stroke: token("--axis"), "stroke-width": 1.5,
          "stroke-dasharray": "4 3",
        }));
      }
      svg.appendChild(txt(s("text", {
        class: "val", x: x + bw / 2, y: Y(Math.max(step.from, step.to)) - 6, "text-anchor": "middle",
      }), (step.value > 0 && !step.total ? "+" : "") + fmt(step.value)));
      svg.appendChild(txt(s("text", {
        class: "lab", x: x + bw / 2, y: H - MB + 16, "text-anchor": "middle",
      }), step.label.length > 14 ? step.label.slice(0, 13) + "…" : step.label));
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* bullet — realizado contra meta, uma linha por item                   */
  /* itens: [{ label, value, target, max }]                               */
  /* ==================================================================== */
  function bullet(spec) {
    const items = spec.items || [];
    if (!items.length) return figure(spec, empty(spec.emptyMessage));
    const W = 760, ML = spec.labelWidth || 190, MR = 58, MT = 8;
    const row = 34, H = MT + row * items.length + 10;
    const iw = W - ML - MR;
    const svg = svgRoot(W, H, spec.caption || "realizado contra meta");

    items.forEach(function (item, i) {
      const max = Number(item.max) || Math.max(Number(item.value) || 0, Number(item.target) || 0, 1);
      const y = MT + row * i + 8;
      const h = 14;
      const value = Math.max(0, Number(item.value) || 0);
      const target = Number(item.target);
      svg.appendChild(txt(s("text", {
        class: "lab", x: ML - 10, y: y + h - 2, "text-anchor": "end",
      }), item.label.length > 30 ? item.label.slice(0, 29) + "…" : item.label));
      /* trilho: o quanto caberia */
      svg.appendChild(s("rect", { x: ML, y: y, width: iw, height: h, rx: 4, fill: token("--grid") }));
      const w = iw * Math.min(1, value / max);
      const hit = value >= target;
      const color = item.color || (isFinite(target) ? (hit ? token("--good") : token("--warning"))
        : token("--accent-strong"));
      const bar = s("path", {
        class: "mark", d: capRight(ML, y + 3, Math.max(2, w), h - 6, 4), fill: color,
      });
      hoverable(bar, item.label, [{ value: fmt(item.value), name: "realizado", color: color }]
        .concat(isFinite(target) ? [{ value: fmt(target), name: "meta" }] : []), item.onClick);
      svg.appendChild(bar);
      if (isFinite(target) && target > 0) {
        const tx = ML + iw * Math.min(1, target / max);
        svg.appendChild(s("line", {
          x1: tx, x2: tx, y1: y - 2, y2: y + h + 2, stroke: token("--ink"), "stroke-width": 2,
        }));
      }
      svg.appendChild(txt(s("text", {
        class: "val", x: W - MR + 8, y: y + h - 2,
      }), fmt(item.value) + (isFinite(target) ? " / " + fmt(target) : "")));
    });

    const extras = items.some(function (x) { return isFinite(Number(x.target)); })
      ? [legendOf([{ label: "meta atingida", color: token("--good") },
        { label: "abaixo da meta", color: token("--warning") }])]
      : [];
    return figure(spec, svg, extras);
  }

  /* ==================================================================== */
  /* calendário-mapa — um ano inteiro, um quadrado por dia                */
  /* dias: { "2026-03-14": 2, ... }                                       */
  /* ==================================================================== */
  function calendarHeat(spec) {
    const days = spec.days || {};
    const year = Number(spec.year) || new Date().getFullYear();
    const values = Object.keys(days).map(function (k) { return days[k]; });
    const peak = Math.max.apply(null, values.concat([0]));
    if (!peak) return figure(spec, empty(spec.emptyMessage));

    const cell = 13, gap = 2, MT = 22, ML = 30;
    const start = new Date(Date.UTC(year, 0, 1));
    const firstDow = start.getUTCDay();
    const total = (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)) ? 366 : 365;
    const weeks = Math.ceil((firstDow + total) / 7);
    const W = ML + weeks * (cell + gap) + 8, H = MT + 7 * (cell + gap) + 20;
    const svg = svgRoot(W, H, spec.caption || "calendário do ano");
    const ramp = [seq(200), seq(400), seq(600), seq(700)];
    const shade = function (v) {
      if (!v) return token("--grid");
      return ramp[Math.min(ramp.length - 1, Math.floor((v - 1) / Math.max(1, peak / ramp.length)))];
    };

    ["S", "T", "Q", "Q", "S"].forEach(function (letter, i) {
      svg.appendChild(txt(s("text", {
        class: "tick", x: ML - 7, y: MT + (i + 1) * (cell + gap) + cell - 3, "text-anchor": "end",
      }), letter));
    });

    let lastMonth = -1;
    for (let d = 0; d < total; d++) {
      const date = new Date(Date.UTC(year, 0, 1 + d));
      const idx = firstDow + d;
      const wk = Math.floor(idx / 7), dow = idx % 7;
      const x = ML + wk * (cell + gap), y = MT + dow * (cell + gap);
      const iso = date.toISOString().slice(0, 10);
      const v = days[iso] || 0;
      const box = s("rect", {
        class: "mark", x: x, y: y, width: cell, height: cell, rx: 3, fill: shade(v),
      });
      if (v) {
        hoverable(box, date.toLocaleDateString("pt-BR", { timeZone: "UTC" }),
          [{ value: fmt(v), name: spec.unit || "registros", color: shade(v) }],
          spec.onPick ? function () { spec.onPick(iso); } : null);
      }
      svg.appendChild(box);
      if (date.getUTCMonth() !== lastMonth && dow <= 3) {
        lastMonth = date.getUTCMonth();
        svg.appendChild(txt(s("text", { class: "tick", x: x, y: MT - 7 }), MESES[lastMonth]));
      }
    }
    return figure(spec, svg, [scaleLegend(1, peak, ramp[0], ramp[ramp.length - 1], spec.unit)]);
  }

  /* ==================================================================== */
  /* bump — como as posições mudam de um período para o outro             */
  /* séries: [{ label, values: [posição por período] }] — 1 é o topo      */
  /* ==================================================================== */
  function bump(spec) {
    const labels = spec.labels || [];
    const series = (spec.series || []).slice(0, 8);
    if (labels.length < 2 || !series.length) return figure(spec, empty(spec.emptyMessage));
    const depth = series.reduce(function (acc, x) {
      return Math.max(acc, Math.max.apply(null, x.values.filter(function (v) { return v; })));
    }, 1);
    const W = 760, MT = 24, MB = 40, ML = 168, MR = 168;
    const H = MT + MB + depth * 30;
    const iw = W - ML - MR, ih = H - MT - MB;
    const X = function (i) { return ML + iw * i / (labels.length - 1); };
    const Y = function (rank) { return MT + ih * (rank - 1) / Math.max(1, depth - 1); };

    const svg = svgRoot(W, H, spec.caption || "mudança de posição");
    labels.forEach(function (label, i) {
      svg.appendChild(s("line", { class: "grid-line", x1: X(i), x2: X(i), y1: MT - 6, y2: MT + ih + 6 }));
      svg.appendChild(txt(s("text", { class: "lab", x: X(i), y: H - MB + 20, "text-anchor": "middle" }), label));
    });

    series.forEach(function (serieSpec, si) {
      const color = serieSpec.color || serie(si);
      const pts = [];
      serieSpec.values.forEach(function (rank, i) {
        if (rank) pts.push([X(i), Y(rank), rank, i]);
      });
      if (!pts.length) return;
      /* curva suave entre postos: a inclinação é o que se lê aqui */
      let d = "M" + pts[0][0] + " " + pts[0][1];
      for (let i = 1; i < pts.length; i++) {
        const a = pts[i - 1], b = pts[i], mx = (a[0] + b[0]) / 2;
        d += " C" + mx + " " + a[1] + " " + mx + " " + b[1] + " " + b[0] + " " + b[1];
      }
      svg.appendChild(s("path", { d: d, fill: "none", stroke: color, "stroke-width": 2.5,
        "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-opacity": 0.85 }));
      pts.forEach(function (p) {
        const dot = s("circle", { class: "ring mark", cx: p[0], cy: p[1], r: 5, fill: color });
        hoverable(dot, serieSpec.label, [
          { value: p[2] + "º", name: labels[p[3]], color: color },
        ], serieSpec.onClick);
        svg.appendChild(dot);
      });
      /* rótulo direto nas duas pontas: quem entrou, quem saiu */
      const head = pts[0], tail = pts[pts.length - 1];
      svg.appendChild(txt(s("text", { class: "lab", x: head[0] - 12, y: head[1] + 4, "text-anchor": "end" }),
        serieSpec.label.length > 22 ? serieSpec.label.slice(0, 21) + "…" : serieSpec.label));
      svg.appendChild(txt(s("text", { class: "val", x: tail[0] + 12, y: tail[1] + 4 }),
        tail[2] + "º"));
    });
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* dendrograma — em que ORDEM os assuntos se juntam, e a que custo      */
  /* ==================================================================== */
  /* A rede diz quais pares andam juntos; o dendrograma diz quando cada
     par se junta. Dois temas que se fundem perto de zero são o mesmo
     assunto com dois nomes; dois ramos que só se encontram no topo são
     duas agendas diferentes dentro do mesmo laboratório — e isso é
     invisível numa lista de pares.

     Uma cor só, com a intensidade seguindo a altura da fusão: a altura é
     grandeza contínua, e cor categórica aqui inventaria grupos que o
     algoritmo não decidiu. Onde cortar a árvore é escolha de quem lê.

     spec: { raiz, altura_maxima, corte?, height, unit } */
  function dendrograma(spec) {
    const raiz = spec.raiz;
    if (!raiz) return figure(spec, empty(spec.emptyMessage));

    /* Cada folha ganha uma faixa; cada nó interno senta na média dos
       filhos. É o que faz o desenho ler como árvore e não como escada. */
    const folhas = [];
    (function contar(no) {
      if (!no.filhos || !no.filhos.length) { folhas.push(no); return; }
      no.filhos.forEach(contar);
    })(raiz);
    if (folhas.length < 2) return figure(spec, empty(spec.emptyMessage));

    const linha = 26;
    const MT = 14, MB = 34, MR = 22;
    /* o rótulo é o dado mais longo aqui; a margem se ajusta a ele em vez
       de cortar "Exercício e atividade física" no meio */
    const maisLongo = folhas.reduce(function (a, f) {
      return Math.max(a, String(f.label || "").length); }, 0);
    const ML = Math.max(120, Math.min(250, maisLongo * 6.1 + 34));
    const W = 760, H = MT + MB + folhas.length * linha;
    const iw = W - ML - MR, ih = folhas.length * linha;
    const topo = spec.altura_maxima || 1;
    const X = function (d) { return ML + iw * (topo ? d / topo : 0); };

    const svg = svgRoot(W, H, spec.caption || "dendrograma");
    const cor = spec.color || seq(500);

    /* Eixo da distância, embaixo: sem ele a largura não significa nada.
       A escala aqui vai de 0 a 1 e o passo redondo do eixo comum devolve
       só "0" e "1" -- dois traços não deixam ninguém ler a que altura um
       ramo se fundiu. Cinco cortes iguais dão a régua. */
    for (let k = 0; k <= 4; k++) {
      const d = topo * k / 4;
      svg.appendChild(s("line", { class: "grid-line", x1: X(d), x2: X(d),
        y1: MT, y2: MT + ih }));
      svg.appendChild(txt(s("text", { class: "tick", x: X(d),
        y: MT + ih + 16, "text-anchor": "middle" }),
        (Math.round(d * 100) / 100).toString().replace(".", ",")));
    }
    svg.appendChild(txt(s("text", { class: "lab", x: ML + iw / 2,
      y: H - 4, "text-anchor": "middle" }),
      spec.unit || "distância (1 − Jaccard)"));

    let slot = 0;
    function desenhar(no) {
      if (!no.filhos || !no.filhos.length) {
        const y = MT + slot * linha + linha / 2;
        slot += 1;
        svg.appendChild(txt(s("text", {
          class: "lab", x: ML - 10, y: y + 3.5, "text-anchor": "end",
        }), no.label));
        const ponto = s("circle", { class: "ring mark", cx: ML, cy: y, r: 4, fill: cor });
        hoverable(ponto, no.label, [{ value: fmt(no.n), name: "artigo(s)", color: cor }]);
        svg.appendChild(ponto);
        return { y: y, x: ML };
      }
      const filhos = no.filhos.map(desenhar);
      const y = filhos.reduce(function (a, f) { return a + f.y; }, 0) / filhos.length;
      const x = X(no.altura || 0);
      /* o colchete: um traço horizontal por filho até a altura da fusão,
         e o vertical que os amarra */
      const ys = filhos.map(function (f) { return f.y; });
      svg.appendChild(s("path", {
        d: "M" + x + "," + Math.min.apply(null, ys) + " L" + x + "," + Math.max.apply(null, ys),
        stroke: cor, fill: "none", "stroke-width": 2, "stroke-linecap": "round",
      }));
      filhos.forEach(function (f) {
        svg.appendChild(s("path", {
          d: "M" + f.x + "," + f.y + " L" + x + "," + f.y,
          stroke: cor, fill: "none", "stroke-width": 2, "stroke-linecap": "round",
        }));
      });
      const junta = s("circle", { class: "ring mark", cx: x, cy: y, r: 4.5, fill: cor });
      hoverable(junta, "Fusão a " + String(no.altura).replace(".", ","), [
        { value: fmt(no.compartilham), name: "artigos em comum", color: cor },
        { value: fmt(no.n), name: "artigos no ramo" },
      ]);
      svg.appendChild(junta);
      return { y: y, x: x };
    }
    desenhar(raiz);

    /* linha de corte: acima dela os ramos são agendas separadas */
    if (spec.corte !== undefined && spec.corte !== null) {
      svg.appendChild(s("line", { x1: X(spec.corte), x2: X(spec.corte),
        y1: MT, y2: MT + ih, stroke: token("--warning"), "stroke-width": 1.5,
        "stroke-dasharray": "5 4" }));
      /* corte perto da borda direita: o rótulo vai para dentro, senão o
         texto sai do viewBox e some pela metade */
      const cabeDireita = X(spec.corte) < ML + iw * 0.7;
      svg.appendChild(txt(s("text", { class: "val", y: MT + 10,
        x: X(spec.corte) + (cabeDireita ? 6 : -6),
        "text-anchor": cabeDireita ? "start" : "end",
        style: "fill:" + token("--warning") }), spec.corteRotulo || "corte"));
    }
    return figure(spec, svg);
  }

  /* ==================================================================== */
  /* fluxo — organograma / árvore de decisão no formato de nós ligados    */
  /* ==================================================================== */
  /* O desenho de caixa-e-seta que qualquer pessoa que já viu um n8n ou um
     Node-RED lê sem legenda: cada passo é uma caixa com o seu valor
     dentro, e o fio curvo sai da direita de uma e entra na esquerda da
     seguinte. Serve para o método (uma corrente) e para a decisão (uma
     árvore que abre) porque a diferença entre os dois é só quantos fios
     saem de cada caixa.

     spec: { nodes: [{id, label, valor, nota, tom, coluna, icone}],
             links: [{de, para, rotulo, tom}], height } */
  const TOM_FLUXO = {
    entrada: "--series-1", passo: "--accent-strong", decisao: "--series-4",
    saida: "--good", descarte: "--ink-muted", alerta: "--warning",
  };
  function fluxo(spec) {
    const nodes = spec.nodes || [];
    const links = spec.links || [];
    if (!nodes.length) return figure(spec, empty(spec.emptyMessage));

    const porId = {};
    nodes.forEach(function (n) { porId[n.id] = n; });
    const saindo = {};
    links.forEach(function (l) { (saindo[l.de] = saindo[l.de] || []).push(l.para); });
    const temPai = {};
    links.forEach(function (l) { temPai[l.para] = true; });

    /* Cada folha ocupa uma faixa; o pai senta na média dos filhos. Sem
       isso a árvore vira uma lista com setas: o pai fica em cima do
       primeiro filho e a bifurcação não se vê. */
    const faixa = {};
    let livre = 0;
    const visitado = {};
    function situar(id) {
      if (visitado[id]) return faixa[id];
      visitado[id] = true;
      const filhos = (saindo[id] || []).filter(function (f) { return porId[f]; });
      if (!filhos.length) { faixa[id] = livre; livre += 1; return faixa[id]; }
      const ys = filhos.map(situar);
      faixa[id] = ys.reduce(function (a, y) { return a + y; }, 0) / ys.length;
      return faixa[id];
    }
    nodes.filter(function (n) { return !temPai[n.id]; })
      .forEach(function (n) { situar(n.id); });
    nodes.forEach(function (n) { if (faixa[n.id] === undefined) situar(n.id); });

    /* A caixa tem largura FIXA, e o desenho fica do tamanho que precisar.
       Espremer sete passos em 760px encolhe a letra até ninguém ler o
       rótulo -- e um fluxograma ilegível não é um fluxograma. Quando não
       cabe, a tira rola de lado. */
    const colunas = nodes.reduce(function (a, n) {
      return Math.max(a, n.coluna || 0); }, 0) + 1;
    const NW = 116, NH = 58, VGAP = 20, HGAP = 24;
    const W = 24 + colunas * NW + (colunas - 1) * HGAP;
    const H = 20 + Math.max(1, Math.round(livre)) * (NH + VGAP) + 8;
    const svg = svgRoot(W, H, spec.caption || "fluxo");
    svg.classList.add("fluxo");
    svg.setAttribute("width", W);
    svg.setAttribute("height", H);

    const px = function (n) { return 12 + (n.coluna || 0) * (NW + HGAP); };
    const py = function (n) { return 14 + faixa[n.id] * (NH + VGAP); };
    const cor = function (n) { return token(TOM_FLUXO[n.tom] || TOM_FLUXO.passo); };

    /* os fios primeiro, para as caixas ficarem por cima deles */
    links.forEach(function (l) {
      const a = porId[l.de], b = porId[l.para];
      if (!a || !b) return;
      const x1 = px(a) + NW, y1 = py(a) + NH / 2;
      const x2 = px(b), y2 = py(b) + NH / 2;
      const dx = Math.max(18, (x2 - x1) * 0.55);
      const tinta = token(TOM_FLUXO[l.tom] || TOM_FLUXO.descarte);
      svg.appendChild(s("path", {
        d: "M" + x1 + "," + y1 + " C" + (x1 + dx) + "," + y1
          + " " + (x2 - dx) + "," + y2 + " " + x2 + "," + y2,
        fill: "none", stroke: tinta, "stroke-width": 1.6, "stroke-opacity": 0.75,
      }));
      svg.appendChild(s("circle", { cx: x2 - 3, cy: y2, r: 2.6, fill: tinta }));
      if (l.rotulo) {
        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - 5;
        const largura = String(l.rotulo).length * 5.6 + 10;
        svg.appendChild(s("rect", { x: mx - largura / 2, y: my - 9, width: largura,
          height: 15, rx: 7, fill: token("--surface"), stroke: tinta,
          "stroke-width": 1, "stroke-opacity": 0.6 }));
        svg.appendChild(txt(s("text", { class: "val", x: mx, y: my + 2,
          "text-anchor": "middle", style: "font-size:9.5px;fill:" + tinta }), l.rotulo));
      }
    });

    nodes.forEach(function (n) {
      const x = px(n), y = py(n), tinta = cor(n);
      const g = s("g", { class: "mark" });
      g.appendChild(s("rect", {
        x: x, y: y, width: NW, height: NH, rx: 11,
        fill: token("--surface-raised"), stroke: tinta, "stroke-width": 1.5,
      }));
      /* a barrinha de cor à esquerda é o que dá o estado da caixa sem
         depender de o leitor separar o tom da borda do tom do fundo */
      g.appendChild(s("rect", { x: x, y: y + 10, width: 3.5, height: NH - 20,
        rx: 2, fill: tinta }));
      g.appendChild(txt(s("text", {
        x: x + 12, y: y + 20, style: "font-size:10px;font-weight:700;fill:"
          + token("--ink-2") + ";letter-spacing:.02em",
      }), recortar(n.label, Math.floor((NW - 18) / 5.4))));
      g.appendChild(txt(s("text", {
        x: x + 12, y: y + 38, style: "font-size:15px;font-weight:750;fill:" + tinta
          + ";font-variant-numeric:tabular-nums",
      }), n.valor === undefined || n.valor === null ? "—" : String(n.valor)));
      if (n.nota) {
        g.appendChild(txt(s("text", {
          x: x + 12, y: y + 49, style: "font-size:9px;fill:" + token("--ink-muted"),
        }), recortar(n.nota, Math.floor((NW - 18) / 4.7))));
      }
      hoverable(g, n.label, [
        { value: n.valor === undefined || n.valor === null ? "—" : String(n.valor),
          name: n.nota || "", color: tinta },
        n.dica ? { value: "", name: n.dica } : null,
      ].filter(Boolean), n.onClick);
      svg.appendChild(g);
    });

    /* uma tira com rolagem: o fluxo é largo por natureza e encolher tudo
       para caber deixaria a letra ilegível */
    return figure(spec, el("div", { class: "scrollx" }, svg));
  }
  function recortar(texto, n) {
    texto = String(texto === undefined || texto === null ? "" : texto);
    return texto.length > n ? texto.slice(0, Math.max(1, n - 1)) + "…" : texto;
  }

  /* --------------------------------------------------------------- API */
  return {
    columns: columns, bars: bars, lines: lines, donut: donut, funnel: funnel,
    scatter: scatter, dumbbell: dumbbell, heatmap: heatmap, distribution: distribution,
    treemap: treemap, sankey: sankey, network: network, geo: geo,
    mapaMundi: mapaMundi,
    dendrograma: dendrograma, fluxo: fluxo,
    sparkline: sparkline, meter: meter,
    area: area, radar: radar, gauge: gauge, waterfall: waterfall, bullet: bullet,
    calendarHeat: calendarHeat, bump: bump, gradFill: gradFill,
    legend: legendOf, scaleLegend: scaleLegend, table: plainTable, csv: downloadCsv,
    token: token, serie: serie, seq: seq, ord: ord, fmt: fmt, compact: compact,
    el: el, svg: s, txt: txt, hideTip: hideTip, empty: empty, MESES: MESES,
  };
})();
