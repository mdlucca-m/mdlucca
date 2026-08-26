/* Painel LAPE - renderizacao interativa, sem dependencias externas. */
"use strict";
const D = JSON.parse(document.getElementById("payload").textContent);
const LIVE = !!(D.session && D.session.live);
const USER = (D.session && D.session.user) || null;
const NS = "http://www.w3.org/2000/svg";
const PAL = ["--c1", "--c2", "--c3", "--c4", "--c5", "--c6"];
const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const DOW = ["D", "S", "T", "Q", "Q", "S", "S"];
const STATUS_LABEL = {em_producao: "Em produção", submetido: "Submetido", em_revisao: "Em revisão",
  aceito: "Aceito", publicado: "Publicado", rejeitado: "Rejeitado", arquivado: "Arquivado"};
const DECISION_LABEL = {em_avaliacao: "Em avaliação", revisao_solicitada: "Revisão solicitada",
  aceito: "Aceito", rejeitado: "Rejeitado", desk_reject: "Desk rejection", retirado: "Retirado",
  sem_registro: "Sem registro"};
const KIND_LABEL = {reuniao: "Reunião", coleta: "Coleta de dados", defesa: "Defesa",
  qualificacao: "Qualificação", congresso: "Congresso", curso: "Curso/oficina",
  seminario: "Seminário", visita_tecnica: "Visita técnica", extensao: "Extensão", outro: "Outro"};
const PROJECT_LABEL = {em_andamento: "Em andamento", planejado: "Planejado",
  concluido: "Concluído", suspenso: "Suspenso"};

/* Filtros ativos. Valem para os blocos derivados de artigos. */
const STATE = {linha: "", ano: "", integrante: "", busca: ""};
const DYNAMIC = [];   /* seções que se redesenham quando o filtro muda */

/* ---------------------------------------------------------------- */
/* utilitários                                                        */
/* ---------------------------------------------------------------- */
function h(tag, attrs, kids){
  const node = document.createElement(tag);
  for (const k in (attrs || {})){
    const v = attrs[k];
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  (Array.isArray(kids) ? kids : (kids ? [kids] : [])).forEach(function (kid){
    if (kid === null || kid === undefined || kid === false) return;
    node.appendChild(typeof kid === "object" ? kid : document.createTextNode(String(kid)));
  });
  return node;
}
function s(tag, attrs){
  const node = document.createElementNS(NS, tag);
  for (const k in (attrs || {})) if (attrs[k] !== null && attrs[k] !== undefined)
    node.setAttribute(k, attrs[k]);
  return node;
}
function css(name){
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
function color(i){ return css(PAL[i % PAL.length]); }
function num(v){ return (v === null || v === undefined || v === "") ? "—" : String(v); }
function dec(v, n){
  return (v === null || v === undefined) ? "—"
    : Number(v).toFixed(n === undefined ? 1 : n).replace(".", ",");
}
function dt(iso){
  if (!iso) return "—";
  const p = String(iso).slice(0, 10).split("-");
  return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : String(iso);
}
function dtm(iso){
  if (!iso) return "—";
  const str = String(iso);
  return str.length > 10 ? dt(str) + " · " + str.slice(11, 16) : dt(str);
}
function dur(days){
  if (days === null || days === undefined) return "—";
  const d = Math.round(days);
  if (Math.abs(d) < 45) return d + " d";
  if (Math.abs(d) < 730) return (d / 30.44).toFixed(1).replace(".", ",") + " meses";
  return (d / 365.25).toFixed(1).replace(".", ",") + " anos";
}
function truncate(text, n){
  if (!text) return "—";
  return text.length > n ? text.slice(0, n - 1) + "…" : text;
}
function badge(status){
  const map = {publicado: "publicado", aceito: "aceito", rejeitado: "rejeitado",
    em_producao: "producao", submetido: "submetido", em_revisao: "submetido"};
  return h("span", {class: "badge b-" + (map[status] || "neutro"),
    text: STATUS_LABEL[status] || status || "—"});
}
function median(values){
  const data = values.filter(function (v){ return v !== null && v !== undefined; })
    .map(Number).sort(function (a, b){ return a - b; });
  if (!data.length) return null;
  const mid = Math.floor(data.length / 2);
  return data.length % 2 ? data[mid] : (data[mid - 1] + data[mid]) / 2;
}
function bestCitations(article){
  return Math.max(article.openalex_citations || 0, article.scopus_citations || 0,
                  article.wos_citations || 0);
}

/* ---------------------------------------------------------------- */
/* tooltip e gaveta                                                   */
/* ---------------------------------------------------------------- */
const TIP = document.getElementById("tip");
function tipOn(node, html){
  node.addEventListener("mousemove", function (ev){
    TIP.innerHTML = html;
    TIP.classList.add("on");
    const box = TIP.getBoundingClientRect();
    let x = ev.clientX + 14, y = ev.clientY - box.height - 10;
    if (x + box.width > innerWidth - 8) x = ev.clientX - box.width - 14;
    if (y < 8) y = ev.clientY + 18;
    TIP.style.left = x + "px"; TIP.style.top = y + "px";
  });
  node.addEventListener("mouseleave", function (){ TIP.classList.remove("on"); });
}

const DRAWER = document.getElementById("drawer");
const DRAWER_BODY = document.getElementById("drawerBody");
function openDrawer(title, content){
  DRAWER_BODY.innerHTML = "";
  DRAWER_BODY.appendChild(h("h3", {text: title}));
  (Array.isArray(content) ? content : [content]).forEach(function (node){
    if (node) DRAWER_BODY.appendChild(node);
  });
  DRAWER.classList.add("on");
  document.getElementById("scrim").classList.add("on");
}
function closeDrawer(){
  DRAWER.classList.remove("on");
  document.getElementById("scrim").classList.remove("on");
}

/* ---------------------------------------------------------------- */
/* blocos de UI                                                       */
/* ---------------------------------------------------------------- */
const APP = document.getElementById("app");
function section(id, title, count, lead, opts){
  const body = h("div");
  const node = h("section", {id: id}, [
    h("h2", {}, [
      title,
      (count !== null && count !== undefined) ? h("span", {class: "n", text: count}) : null,
      (opts && opts.filtered) ? h("span", {class: "chip-f", title:
        "Este bloco responde aos filtros da barra superior.", text: "filtrável"}) : null,
    ]),
    lead ? h("p", {class: "lead", text: lead}) : null,
    body,
  ]);
  APP.appendChild(node);
  return body;
}
function card(title, hint, kids){
  return h("div", {class: "card"}, [
    title ? h("h3", {text: title}) : null,
    hint ? h("div", {class: "hint", text: hint}) : null,
  ].concat(Array.isArray(kids) ? kids : [kids]));
}
function kpi(label, value, foot, accent){
  return h("div", {class: "kpi" + (accent ? " accent" : "")}, [
    h("div", {class: "label", text: label}),
    h("div", {class: "value", text: value}),
    foot ? h("div", {class: "foot", text: foot}) : null,
  ]);
}
function table(cols, rows, emptyMsg, opts){
  opts = opts || {};
  if (!rows || !rows.length)
    return h("div", {class: "tw"}, h("div", {class: "empty",
      text: emptyMsg || "Sem registros."}));
  const state = {key: opts.sortKey || null, dir: opts.sortDir || -1};
  const wrap = h("div", {class: "tw"});
  const tbody = h("tbody");

  function paint(){
    let data = rows.slice();
    if (state.key){
      const col = cols.find(function (c){ return (c.k || c.label) === state.key; });
      data.sort(function (a, b){
        const va = col.sortValue ? col.sortValue(a) : a[col.k];
        const vb = col.sortValue ? col.sortValue(b) : b[col.k];
        if (va === vb) return 0;
        if (va === null || va === undefined) return 1;
        if (vb === null || vb === undefined) return -1;
        return (va > vb ? 1 : -1) * state.dir;
      });
    }
    tbody.innerHTML = "";
    data.forEach(function (row){
      const tr = h("tr", cols.some(function (c){ return c.onRow; })
        ? {class: "clickable", onclick: function (){
            const col = cols.find(function (c){ return c.onRow; });
            col.onRow(row);
          }} : {});
      cols.forEach(function (c){
        const value = c.render ? c.render(row) : row[c.k];
        const cell = h("td", {class: [c.num ? "num" : "", c.wide ? "title" : ""]
          .join(" ").trim() || null});
        if (value instanceof Node) cell.appendChild(value);
        else cell.textContent = (value === null || value === undefined || value === "")
          ? "—" : String(value);
        tr.appendChild(cell);
      });
      tbody.appendChild(tr);
    });
  }

  const head = h("tr", {}, cols.map(function (c){
    const key = c.k || c.label;
    const th = h("th", {class: (c.num ? "num " : "") + (opts.sortable === false ? "" : "sortable"),
      text: c.label});
    if (opts.sortable !== false && (c.k || c.sortValue)){
      th.addEventListener("click", function (){
        state.dir = state.key === key ? -state.dir : -1;
        state.key = key;
        head.querySelectorAll("th").forEach(function (x){ x.classList.remove("asc", "desc"); });
        th.classList.add(state.dir === 1 ? "asc" : "desc");
        paint();
      });
    }
    return th;
  }));
  paint();
  wrap.appendChild(h("table", {}, [h("thead", {}, head), tbody]));
  return wrap;
}
function tabs(items){
  const nav = h("div", {class: "tabs"});
  const wrap = h("div");
  items.forEach(function (item, i){
    const pane = h("div", {class: "tabpane" + (i === 0 ? " active" : "")}, item.content);
    const btn = h("button", {class: i === 0 ? "active" : null, text: item.label,
      onclick: function (){
        nav.querySelectorAll("button").forEach(function (b){ b.classList.remove("active"); });
        wrap.querySelectorAll(".tabpane").forEach(function (p){ p.classList.remove("active"); });
        btn.classList.add("active");
        pane.classList.add("active");
      }});
    nav.appendChild(btn);
    wrap.appendChild(pane);
  });
  return h("div", {}, [nav, wrap]);
}
function searchBox(placeholder, onInput){
  return h("input", {class: "search", type: "search", placeholder: placeholder,
    oninput: function (ev){ onInput(ev.target.value.toLowerCase()); }});
}

/* ---------------------------------------------------------------- */
/* gráficos                                                           */
/* ---------------------------------------------------------------- */
function emptyChart(message){
  const svg = s("svg", {viewBox: "0 0 640 120"});
  const t = s("text", {x: 320, y: 62, "text-anchor": "middle", class: "vlab"});
  t.textContent = message || "sem dados";
  svg.appendChild(t);
  return svg;
}
function barChart(items, opts){
  opts = opts || {};
  const W = 640, H = opts.height || 220, ML = 42, MR = 10, MT = 16, MB = 34;
  if (!items.length) return emptyChart();
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, role: "img"});
  const max = Math.max.apply(null, items.map(function (d){ return d.value; }).concat([1]));
  const iw = W - ML - MR, ih = H - MT - MB, bw = iw / items.length;
  const g = s("g");
  svg.appendChild(g);
  const ticks = Math.min(4, Math.max(1, max));
  for (let t = 0; t <= ticks; t++){
    const y = MT + ih - ih * t / ticks;
    g.appendChild(s("line", {x1: ML, x2: W - MR, y1: y, y2: y, class: "gl"}));
    const lab = s("text", {x: ML - 7, y: y + 3.5, "text-anchor": "end", class: "vlab"});
    lab.textContent = Math.round(max * t / ticks);
    g.appendChild(lab);
  }
  items.forEach(function (d, i){
    const bh = Math.max(d.value > 0 ? 2 : 0, ih * d.value / max);
    const x = ML + i * bw + bw * 0.16, w = bw * 0.68, y = MT + ih - bh;
    const rect = s("rect", {x: x, y: y, width: w, height: bh, rx: 3, class: "bar",
      fill: d.color || opts.color || color(0)});
    tipOn(rect, "<b>" + d.label + "</b>" + (opts.tipLabel || "") + d.value);
    if (opts.onClick) {
      rect.style.cursor = "pointer";
      rect.addEventListener("click", function (){ opts.onClick(d); });
    }
    g.appendChild(rect);
    const val = s("text", {x: x + w / 2, y: y - 5, "text-anchor": "middle", class: "vlab"});
    val.textContent = d.value || "";
    g.appendChild(val);
    const lab = s("text", {x: x + w / 2, y: H - MB + 15, "text-anchor": "middle", class: "vlab"});
    lab.textContent = d.label;
    g.appendChild(lab);
  });
  return svg;
}
function hbarChart(items, opts){
  opts = opts || {};
  if (!items.length) return emptyChart();
  const rowH = opts.rowH || 24, W = 640, ML = opts.labelWidth || 150, MR = 46;
  const H = Math.max(items.length * rowH + 10, 40);
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, role: "img"});
  const max = Math.max.apply(null, items.map(function (d){ return d.value; }).concat([1]));
  const iw = W - ML - MR;
  items.forEach(function (d, i){
    const y = i * rowH + 5, bw = Math.max(d.value > 0 ? 2 : 0, iw * d.value / max);
    const lab = s("text", {x: ML - 8, y: y + rowH * 0.62, "text-anchor": "end", class: "vlab"});
    lab.textContent = truncate(d.label, opts.labelChars || 22);
    svg.appendChild(lab);
    const rect = s("rect", {x: ML, y: y + 3, width: bw, height: rowH - 10, rx: 3, class: "bar",
      fill: d.color || opts.color || color(0)});
    tipOn(rect, "<b>" + d.label + "</b>" + (opts.tipLabel || "") + d.value
      + (d.note ? "<br>" + d.note : ""));
    if (opts.onClick){
      rect.style.cursor = "pointer";
      lab.style.cursor = "pointer";
      rect.addEventListener("click", function (){ opts.onClick(d); });
      lab.addEventListener("click", function (){ opts.onClick(d); });
    }
    svg.appendChild(rect);
    const val = s("text", {x: ML + bw + 7, y: y + rowH * 0.62, class: "vlab"});
    val.textContent = d.value;
    svg.appendChild(val);
  });
  return svg;
}
function lineChart(series, opts){
  opts = opts || {};
  const W = 640, H = opts.height || 230, ML = 44, MR = 14, MT = 16, MB = 34;
  const labels = opts.labels || [];
  if (!labels.length) return emptyChart();
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H});
  const all = series.reduce(function (acc, x){ return acc.concat(x.values); }, []);
  const max = Math.max.apply(null, all.concat([1]));
  const iw = W - ML - MR, ih = H - MT - MB;
  const X = function (i){
    return ML + (labels.length === 1 ? iw / 2 : iw * i / (labels.length - 1));
  };
  const Y = function (v){ return MT + ih - ih * v / max; };
  const ticks = Math.min(4, Math.max(1, max));  // evita rotulos repetidos
  for (let t = 0; t <= ticks; t++){
    const y = MT + ih - ih * t / ticks;
    svg.appendChild(s("line", {x1: ML, x2: W - MR, y1: y, y2: y, class: "gl"}));
    const lab = s("text", {x: ML - 7, y: y + 3.5, "text-anchor": "end", class: "vlab"});
    lab.textContent = Math.round(max * t / ticks);
    svg.appendChild(lab);
  }
  labels.forEach(function (label, i){
    const lab = s("text", {x: X(i), y: H - MB + 16, "text-anchor": "middle", class: "vlab"});
    lab.textContent = label;
    svg.appendChild(lab);
  });
  series.forEach(function (serie, si){
    const stroke = serie.color || color(si);
    const path = serie.values.map(function (v, i){
      return (i ? "L" : "M") + X(i) + " " + Y(v);
    }).join(" ");
    if (serie.area){
      svg.appendChild(s("path", {fill: stroke, "fill-opacity": 0.13,
        d: path + " L" + X(labels.length - 1) + " " + Y(0) + " L" + X(0) + " " + Y(0) + " Z"}));
    }
    svg.appendChild(s("path", {d: path, fill: "none", stroke: stroke, "stroke-width": 2.4,
      "stroke-linejoin": "round", "stroke-linecap": "round"}));
    serie.values.forEach(function (v, i){
      const dot = s("circle", {cx: X(i), cy: Y(v), r: 4, fill: stroke,
        stroke: css("--surface"), "stroke-width": 1.6});
      tipOn(dot, "<b>" + serie.label + " · " + labels[i] + "</b>" + v);
      svg.appendChild(dot);
    });
  });
  return svg;
}
function donut(items){
  const W = 240, R = 92, r = 58, cx = W / 2, cy = W / 2;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + W, style: "max-width:240px;margin:0 auto"});
  const total = items.reduce(function (a, b){ return a + b.value; }, 0);
  if (!total){
    const t = s("text", {x: cx, y: cy, "text-anchor": "middle", class: "vlab"});
    t.textContent = "sem dados";
    svg.appendChild(t);
    return svg;
  }
  let angle = -Math.PI / 2;
  items.forEach(function (d, i){
    const span = 2 * Math.PI * d.value / total;
    const x1 = cx + R * Math.cos(angle), y1 = cy + R * Math.sin(angle);
    const x2 = cx + R * Math.cos(angle + span), y2 = cy + R * Math.sin(angle + span);
    const x3 = cx + r * Math.cos(angle + span), y3 = cy + r * Math.sin(angle + span);
    const x4 = cx + r * Math.cos(angle), y4 = cy + r * Math.sin(angle);
    const large = span > Math.PI ? 1 : 0;
    const path = s("path", {class: "bar", fill: d.color || color(i), d:
      "M" + x1 + " " + y1 + "A" + R + " " + R + " 0 " + large + " 1 " + x2 + " " + y2 +
      "L" + x3 + " " + y3 + "A" + r + " " + r + " 0 " + large + " 0 " + x4 + " " + y4 + "Z"});
    tipOn(path, "<b>" + d.label + "</b>" + d.value + " (" + Math.round(100 * d.value / total) + "%)");
    if (d.onClick){
      path.style.cursor = "pointer";
      path.addEventListener("click", d.onClick);
    }
    svg.appendChild(path);
    angle += span;
  });
  const big = s("text", {x: cx, y: cy - 2, "text-anchor": "middle",
    style: "font-size:26px;font-weight:700;fill:" + css("--text")});
  big.textContent = total;
  svg.appendChild(big);
  const sub = s("text", {x: cx, y: cy + 16, "text-anchor": "middle", class: "vlab"});
  sub.textContent = "artigos";
  svg.appendChild(sub);
  return svg;
}
function funnel(steps){
  const W = 640, rowH = 46, H = steps.length * rowH + 8;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H});
  const max = Math.max.apply(null, steps.map(function (x){ return x.value; }).concat([1]));
  steps.forEach(function (step, i){
    const w = Math.max(4, (W - 180) * step.value / max);
    const y = i * rowH + 6;
    const lab = s("text", {x: 132, y: y + rowH * 0.55, "text-anchor": "end", class: "vlab"});
    lab.textContent = step.label;
    svg.appendChild(lab);
    const rect = s("rect", {x: 142, y: y, width: w, height: rowH - 14, rx: 5, class: "bar",
      fill: color(i), "fill-opacity": 0.85});
    tipOn(rect, "<b>" + step.label + "</b>" + step.value + " artigo(s)"
      + (i ? "<br>" + Math.round(100 * step.value / (steps[i - 1].value || 1))
             + "% da etapa anterior" : ""));
    svg.appendChild(rect);
    const val = s("text", {x: 142 + w + 9, y: y + rowH * 0.55, class: "vlab",
      style: "font-weight:600;fill:" + css("--text")});
    val.textContent = step.value;
    svg.appendChild(val);
    if (i){
      const pct = s("text", {x: 142 + w + 9 + 26, y: y + rowH * 0.55, class: "vlab"});
      pct.textContent = "(" + Math.round(100 * step.value / (steps[i - 1].value || 1)) + "%)";
      svg.appendChild(pct);
    }
  });
  return svg;
}
function heatGrid(years, months, values, label){
  const cell = 30, ML = 42, MT = 20;
  const W = ML + 12 * cell + 8, H = MT + years.length * cell + 8;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, style: "max-width:" + W + "px"});
  const max = Math.max.apply(null, values.concat([1]));
  MONTHS.forEach(function (m, i){
    const t = s("text", {x: ML + i * cell + cell / 2, y: MT - 6, "text-anchor": "middle",
      class: "vlab"});
    t.textContent = m;
    svg.appendChild(t);
  });
  years.forEach(function (year, r){
    const t = s("text", {x: ML - 8, y: MT + r * cell + cell * 0.65, "text-anchor": "end",
      class: "vlab"});
    t.textContent = year;
    svg.appendChild(t);
    for (let c = 0; c < 12; c++){
      const v = values[r * 12 + c] || 0;
      const rect = s("rect", {x: ML + c * cell + 1, y: MT + r * cell + 1, width: cell - 3,
        height: cell - 3, rx: 4, fill: v ? color(0) : css("--surface-2"),
        "fill-opacity": v ? (0.22 + 0.78 * v / max) : 1,
        stroke: css("--border"), "stroke-width": v ? 0 : 1});
      tipOn(rect, "<b>" + MONTHS[c] + "/" + year + "</b>" + v + " " + label);
      svg.appendChild(rect);
      if (v){
        const t2 = s("text", {x: ML + c * cell + cell / 2, y: MT + r * cell + cell * 0.66,
          "text-anchor": "middle",
          style: "font-size:11px;font-weight:600;fill:" + css("--text")});
        t2.textContent = v;
        svg.appendChild(t2);
      }
    }
  });
  return svg;
}
function forceLayout(nodes, edges, W, H, iterations){
  const k = Math.sqrt(W * H / Math.max(nodes.length, 1));
  const pos = new Map();
  nodes.forEach(function (n, i){
    const a = 2 * Math.PI * i / nodes.length;
    pos.set(n.id, {x: W / 2 + Math.cos(a) * W * 0.32, y: H / 2 + Math.sin(a) * H * 0.32,
      dx: 0, dy: 0});
  });
  let temp = W * 0.11;
  for (let it = 0; it < iterations; it++){
    pos.forEach(function (p){ p.dx = 0; p.dy = 0; });
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++){
      const a = pos.get(nodes[i].id), b = pos.get(nodes[j].id);
      let dx = a.x - b.x, dy = a.y - b.y;
      const d = Math.hypot(dx, dy) || 0.01, rep = k * k / d;
      a.dx += dx / d * rep; a.dy += dy / d * rep;
      b.dx -= dx / d * rep; b.dy -= dy / d * rep;
    }
    edges.forEach(function (e){
      const a = pos.get(e.source), b = pos.get(e.target);
      if (!a || !b) return;
      let dx = a.x - b.x, dy = a.y - b.y;
      const d = Math.hypot(dx, dy) || 0.01;
      const att = d * d / k * (1 + Math.log(1 + e.weight)) * 0.55;
      a.dx -= dx / d * att; a.dy -= dy / d * att;
      b.dx += dx / d * att; b.dy += dy / d * att;
    });
    pos.forEach(function (p){
      const d = Math.hypot(p.dx, p.dy) || 0.01;
      p.x += p.dx / d * Math.min(d, temp);
      p.y += p.dy / d * Math.min(d, temp);
      p.x = Math.max(26, Math.min(W - 26, p.x));
      p.y = Math.max(26, Math.min(H - 26, p.y));
    });
    temp *= 0.965;
  }
  return pos;
}
function networkChart(net){
  const W = 720, H = 460;
  if (!net.nodes.length) return emptyChart("sem coautoria registrada");
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, style: "max-height:520px"});
  const pos = forceLayout(net.nodes, net.edges, W, H, 380);
  const maxW = Math.max.apply(null, net.edges.map(function (e){ return e.weight; }).concat([1]));
  const maxA = Math.max.apply(null, net.nodes.map(function (n){ return n.articles; }).concat([1]));
  const gEdges = s("g");
  svg.appendChild(gEdges);
  net.edges.forEach(function (e){
    const a = pos.get(e.source), b = pos.get(e.target);
    if (!a || !b) return;
    gEdges.appendChild(s("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: css("--border"),
      "stroke-width": 0.8 + 3.2 * e.weight / maxW, "stroke-opacity": 0.85}));
  });
  net.nodes.forEach(function (n){
    const p = pos.get(n.id);
    const r = 7 + 15 * Math.sqrt(n.articles / maxA);
    const g = s("g");
    const circle = s("circle", {cx: p.x, cy: p.y, r: r, class: "bar",
      fill: n.is_external ? css("--c3") : css("--c1"), "fill-opacity": 0.85,
      stroke: css("--surface"), "stroke-width": 2, style: "cursor:pointer"});
    tipOn(circle, "<b>" + n.full_name + "</b>" + n.articles + " artigo(s) · "
      + n.degree + " coautor(es)" + (n.role ? "<br>" + n.role : ""));
    circle.addEventListener("click", function (){ showResearcher(n.id); });
    g.appendChild(circle);
    const label = s("text", {x: p.x, y: p.y + r + 12, "text-anchor": "middle", class: "vlab"});
    label.textContent = truncate(n.name, 16);
    g.appendChild(label);
    svg.appendChild(g);
  });
  return svg;
}
function mapChart(places){
  const pts = places.filter(function (p){
    return p.latitude !== null && p.longitude !== null;
  });
  const W = 640, H = 380, pad = 46;
  if (!pts.length) return emptyChart("sem coordenadas cadastradas");
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H});
  let latMin = Math.min.apply(null, pts.map(function (p){ return p.latitude; }));
  let latMax = Math.max.apply(null, pts.map(function (p){ return p.latitude; }));
  let lonMin = Math.min.apply(null, pts.map(function (p){ return p.longitude; }));
  let lonMax = Math.max.apply(null, pts.map(function (p){ return p.longitude; }));
  const spanLat = Math.max(latMax - latMin, 1.5), spanLon = Math.max(lonMax - lonMin, 1.5);
  latMin -= spanLat * 0.18; latMax += spanLat * 0.18;
  lonMin -= spanLon * 0.18; lonMax += spanLon * 0.18;
  const X = function (lon){ return pad + (lon - lonMin) / (lonMax - lonMin) * (W - 2 * pad); };
  const Y = function (lat){ return pad + (latMax - lat) / (latMax - latMin) * (H - 2 * pad); };
  const grid = s("g");
  svg.appendChild(grid);
  for (let i = 0; i <= 4; i++){
    const lat = latMin + (latMax - latMin) * i / 4;
    const lon = lonMin + (lonMax - lonMin) * i / 4;
    grid.appendChild(s("line", {x1: pad, x2: W - pad, y1: Y(lat), y2: Y(lat), class: "gl"}));
    grid.appendChild(s("line", {y1: pad, y2: H - pad, x1: X(lon), x2: X(lon), class: "gl"}));
    const ty = s("text", {x: pad - 6, y: Y(lat) + 3, "text-anchor": "end", class: "vlab"});
    ty.textContent = lat.toFixed(1) + "°";
    grid.appendChild(ty);
    const tx = s("text", {x: X(lon), y: H - pad + 15, "text-anchor": "middle", class: "vlab"});
    tx.textContent = lon.toFixed(1) + "°";
    grid.appendChild(tx);
  }
  if (D.geo && D.geo.length){
    const gg = s("g");
    svg.appendChild(gg);
    D.geo.forEach(function (ring){
      const path = ring.map(function (pt, i){
        return (i ? "L" : "M") + X(pt[0]) + " " + Y(pt[1]);
      }).join(" ");
      gg.appendChild(s("path", {d: path + "Z", fill: css("--surface-2"), "fill-opacity": 0.7,
        stroke: css("--border"), "stroke-width": 1}));
    });
  }
  const maxN = Math.max.apply(null, pts.map(function (p){ return p.n_events; }).concat([1]));
  pts.forEach(function (p){
    const r = 6 + 16 * Math.sqrt(p.n_events / maxN);
    const c = s("circle", {cx: X(p.longitude), cy: Y(p.latitude), r: r, fill: css("--c1"),
      "fill-opacity": 0.55, stroke: css("--c1"), "stroke-width": 1.5, class: "bar"});
    tipOn(c, "<b>" + p.city + (p.state ? " / " + p.state : "") + "</b>"
      + p.n_events + " atividade(s)");
    svg.appendChild(c);
    const t = s("text", {x: X(p.longitude), y: Y(p.latitude) - r - 5, "text-anchor": "middle",
      class: "vlab"});
    t.textContent = p.city;
    svg.appendChild(t);
  });
  return svg;
}
function legend(items){
  return h("div", {class: "legend"}, items.map(function (d, i){
    return h("span", {}, [h("i", {style: "background:" + (d.color || color(i))}), d.label]);
  }));
}
function statBox(label, stat){
  if (!stat || !stat.n)
    return card(label, "Sem dados suficientes.", h("div", {class: "empty", text: "—"}));
  return card(label, stat.n + " artigo(s) com as duas datas registradas", [
    h("div", {class: "grid g3"}, [
      kpi("Mediana", dur(stat.median)), kpi("Média", dur(stat.mean)),
      kpi("Mín – Máx", dur(stat.min) + " – " + dur(stat.max)),
    ]),
    h("div", {class: "hint", style: "margin-top:12px",
      text: "Intervalo interquartil: " + dur(stat.p25) + " a " + dur(stat.p75)
        + " · desvio-padrão " + dur(stat.sd)}),
  ]);
}

/* ---------------------------------------------------------------- */
/* filtros                                                            */
/* ---------------------------------------------------------------- */
const MEMBER_ARTICLES = new Map();
(D.authorship || []).forEach(function (link){
  if (!MEMBER_ARTICLES.has(link.m)) MEMBER_ARTICLES.set(link.m, new Set());
  MEMBER_ARTICLES.get(link.m).add(link.a);
});

function articlesFiltered(){
  const memberSet = STATE.integrante ? MEMBER_ARTICLES.get(Number(STATE.integrante)) : null;
  return (D.articles || []).filter(function (a){
    if (STATE.linha && a.research_line !== STATE.linha) return false;
    if (STATE.ano && String(a.year_published) !== STATE.ano) return false;
    if (memberSet && !memberSet.has(a.id)) return false;
    if (STATE.busca){
      const hay = ((a.title || "") + " " + (a.authors || "") + " " + (a.journal || "")).toLowerCase();
      if (!hay.includes(STATE.busca)) return false;
    }
    return true;
  });
}
function filtersActive(){
  return !!(STATE.linha || STATE.ano || STATE.integrante || STATE.busca);
}
function buildToolbar(){
  const bar = document.getElementById("toolbar");
  const years = Array.from(new Set((D.articles || [])
    .map(function (a){ return a.year_published; })
    .filter(Boolean))).sort(function (a, b){ return b - a; });
  const lines = (D.research_lines || []).map(function (l){ return l.name; });
  const people = (D.researchers || []).filter(function (r){ return r.n_articles > 0; });

  function select(label, options, key){
    const el = h("select", {onchange: function (ev){
      STATE[key] = ev.target.value;
      refresh();
    }});
    el.appendChild(h("option", {value: "", text: label}));
    options.forEach(function (opt){
      const value = typeof opt === "object" ? opt.value : opt;
      const text = typeof opt === "object" ? opt.label : opt;
      el.appendChild(h("option", {value: value, text: text}));
    });
    el.value = STATE[key];
    return el;
  }

  bar.innerHTML = "";
  bar.appendChild(h("span", {class: "flabel", text: "Filtrar:"}));
  bar.appendChild(select("Todas as linhas", lines, "linha"));
  bar.appendChild(select("Todos os anos", years.map(String), "ano"));
  bar.appendChild(select("Todos os integrantes", people.map(function (p){
    return {value: String(p.id), label: p.short_name || p.full_name};
  }), "integrante"));
  const search = h("input", {class: "search", type: "search",
    placeholder: "Buscar título, autor ou revista…", value: STATE.busca,
    oninput: function (ev){ STATE.busca = ev.target.value.toLowerCase(); refresh(); }});
  bar.appendChild(search);
  bar.appendChild(h("button", {class: "clear", text: "Limpar",
    disabled: !filtersActive(), onclick: function (){
      STATE.linha = STATE.ano = STATE.integrante = STATE.busca = "";
      buildToolbar();
      refresh();
    }}));
  const count = articlesFiltered().length;
  bar.appendChild(h("span", {class: "fcount",
    text: count + " de " + (D.articles || []).length + " artigos"}));
}
function refresh(){
  DYNAMIC.forEach(function (fn){ fn(); });
  const bar = document.getElementById("toolbar");
  const clear = bar.querySelector("button.clear");
  if (clear) clear.disabled = !filtersActive();
  const count = bar.querySelector(".fcount");
  if (count) count.textContent = articlesFiltered().length + " de "
    + (D.articles || []).length + " artigos";
}
function dynamicSection(id, title, lead, renderer, opts){
  /* Seção que se redesenha a cada mudança de filtro.
     O renderer devolve o número a mostrar ao lado do título. */
  const body = section(id, title, "", lead, Object.assign({filtered: true}, opts || {}));
  const counter = document.querySelector("#" + id + " > h2 > .n");
  const paint = function (){
    body.innerHTML = "";
    const total = renderer(body, articlesFiltered());
    if (counter) counter.textContent = (total === undefined || total === null) ? "" : total;
  };
  DYNAMIC.push(paint);
  paint();
}

/* ---------------------------------------------------------------- */
/* detalhes (gaveta)                                                  */
/* ---------------------------------------------------------------- */
function showResearcher(id){
  const person = (D.researchers || []).find(function (r){ return r.id === id; });
  if (!person) return;
  const content = [
    h("div", {class: "drawer-sub", text: [person.role, person.degree, person.research_line]
      .filter(Boolean).join(" · ") || "Integrante do LAPE"}),
    h("div", {class: "grid g4", style: "margin:14px 0"}, [
      kpi("Artigos", person.n_articles),
      kpi("Publicados", person.n_published),
      kpi("Projetos", person.n_projects),
      kpi("Índice h", person.h_index === null ? "—" : person.h_index),
    ]),
  ];
  if (person.h_index_source) content.push(h("p", {class: "hint", text:
    "Índice h de " + (person.h_index_source === "openalex_author"
      ? "perfil OpenAlex (carreira completa)" : "artigos deste banco")
    + (person.metrics_updated_at ? " · atualizado em " + dt(person.metrics_updated_at) : "")}));
  if (person.bio) content.push(h("p", {class: "hint", text: person.bio}));

  const contacts = [
    person.email ? h("span", {}, [h("b", {text: "E-mail: "}), person.email]) : null,
    person.orcid ? h("span", {}, [h("b", {text: "ORCID: "}),
      h("a", {href: "https://orcid.org/" + person.orcid, target: "_blank", rel: "noopener",
        text: person.orcid})]) : null,
    person.lattes_id ? h("span", {}, [h("b", {text: "Lattes: "}),
      h("a", {href: "http://lattes.cnpq.br/" + person.lattes_id, target: "_blank",
        rel: "noopener", text: person.lattes_id})]) : null,
    person.institution ? h("span", {}, [h("b", {text: "Instituição: "}), person.institution]) : null,
  ].filter(Boolean);
  if (contacts.length) content.push(h("div", {class: "contacts"}, contacts));

  if (person.project_list && person.project_list.length){
    content.push(h("h4", {text: "Projetos"}));
    content.push(table([
      {k: "name", label: "Projeto"},
      {k: "role", label: "Papel"},
      {k: "status", label: "Situação", render: function (r){
        return h("span", {class: "badge b-neutro",
          text: PROJECT_LABEL[r.status] || r.status}); }},
    ], person.project_list, null, {sortable: false}));
  }
  const articles = person.articles_recent || [];
  content.push(h("h4", {text: "Artigos (" + articles.length + ")"}));
  content.push(table([
    {k: "title", label: "Título", wide: true, render: function (r){
      return h("div", {}, [truncate(r.title, 74),
        h("small", {text: [r.journal, r.year_published].filter(Boolean).join(" · ")})]); }},
    {k: "status", label: "Situação", render: function (r){ return badge(r.status); }},
    {label: "Citações", num: true, sortValue: bestCitations,
      render: function (r){ return bestCitations(r) || "—"; }},
  ], articles, "Sem artigos registrados."));

  if (person.coauthors && person.coauthors.length){
    content.push(h("h4", {text: "Coautores mais frequentes"}));
    content.push(table([{k: "full_name", label: "Coautor"},
      {k: "n", label: "Artigos", num: true}], person.coauthors, null, {sortable: false}));
  }
  content.push(h("div", {class: "drawer-actions"}, [
    h("button", {class: "primary", text: "Filtrar o painel por esta pessoa",
      onclick: function (){
        STATE.integrante = String(person.id);
        buildToolbar();
        refresh();
        closeDrawer();
        document.getElementById("producao").scrollIntoView({block: "start"});
      }}),
  ]));
  openDrawer(person.full_name, content);
}

function showArticle(article){
  const content = [
    h("div", {class: "drawer-sub", text: article.authors || "—"}),
    h("div", {style: "margin:12px 0"}, [badge(article.status),
      article.research_line ? h("span", {class: "badge b-neutro", style: "margin-left:6px",
        text: article.research_line}) : null]),
    h("div", {class: "grid g4", style: "margin:14px 0"}, [
      kpi("Tentativas", article.submission_attempts || 0),
      kpi("Recusas", article.rejections || 0),
      kpi("Citações", bestCitations(article) || "—"),
      kpi("Início→pub.", dur(article.days_start_to_publication)),
    ]),
  ];
  const facts = [
    ["Código interno", article.internal_code], ["Periódico", article.journal],
    ["Qualis", article.qualis], ["Fator de impacto", article.impact_factor],
    ["Tipo de estudo", article.study_type], ["Responsável", article.lead_name],
    ["Início", dt(article.started_on)], ["1ª submissão", dt(article.first_submission_on)],
    ["Aceite", dt(article.accepted_on)], ["Publicação", dt(article.published_on)],
    ["WoS", num(article.wos_citations)], ["Scopus", num(article.scopus_citations)],
    ["OpenAlex", num(article.openalex_citations)],
  ].filter(function (pair){ return pair[1] !== null && pair[1] !== undefined && pair[1] !== "—"; });
  content.push(h("dl", {class: "facts"}, facts.reduce(function (acc, pair){
    acc.push(h("dt", {text: pair[0]}));
    acc.push(h("dd", {text: String(pair[1])}));
    return acc;
  }, [])));
  if (article.doi) content.push(h("p", {}, h("a", {href: "https://doi.org/" + article.doi,
    target: "_blank", rel: "noopener", text: "Abrir no DOI: " + article.doi})));
  openDrawer(truncate(article.title, 90), content);
}

/* ---------------------------------------------------------------- */
/* seções                                                             */
/* ---------------------------------------------------------------- */
function renderHeader(){
  const o = D.overview;
  document.getElementById("labName").textContent = o.lab_name;
  const meta = document.getElementById("labMeta");
  meta.innerHTML = "";
  [o.institution, "Atualizado em " + o.generated_at, "Janela: " + o.window + " anos",
   LIVE ? "dados ao vivo do banco" : "exportação estática"].forEach(function (text){
    meta.appendChild(h("span", {class: "pill", text: text}));
  });

  const actions = document.getElementById("actions");
  actions.innerHTML = "";
  if (LIVE){
    actions.appendChild(h("a", {href: "/app"},
      h("button", {class: "primary", text: USER ? "Área do integrante" : "Entrar"})));
    actions.appendChild(h("button", {text: "Atualizar", title: "Recarrega direto do banco",
      onclick: function (){ location.reload(); }}));
  }
  actions.appendChild(h("button", {text: "Imprimir", onclick: function (){ print(); }}));
  if (USER) actions.appendChild(h("span", {class: "pill", text: USER.full_name}));

  document.getElementById("foot").textContent =
    "Painel do " + o.lab_name + " gerado em " + o.generated_at
    + ". Fontes: planilhas do laboratório, Currículo Lattes, OpenAlex, Crossref, Scopus"
    + " e Web of Science.";
}

function renderOverview(){
  const o = D.overview;
  const body = section("visao-geral", "Visão geral", null,
    "Retrato do laboratório na data de geração deste painel.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Artigos no banco", o.n_articles, o.n_research_lines + " linhas de pesquisa", true),
    kpi("Em produção", o.n_in_progress, "manuscritos em escrita"),
    kpi("Submetidos", o.n_submitted, "aguardando parecer"),
    kpi("Publicados", o.n_published, o.published_window + " nos últimos " + o.window + " anos"),
    kpi("Média/ano", dec(o.mean_per_year, 2), "publicações por ano"),
    kpi("Pesquisadores", o.n_members, o.n_collaborators + " colaboradores externos"),
    kpi("Projetos", o.n_projects, o.n_projects_active + " em andamento"),
    kpi("Maior índice h", o.best_h_index, "entre os integrantes"),
  ]));

  const statusItems = o.status_counts.map(function (d, i){
    return {label: STATUS_LABEL[d.status] || d.status, value: d.n, color: color(i),
      onClick: function (){
        STATE.busca = "";
        document.getElementById("producao").scrollIntoView({block: "start"});
      }};
  });
  const years = D.publications.series.map(function (d){ return d.year; });
  let running = 0;
  const cumulative = D.publications.series.map(function (d){
    running += d.n_articles;
    return running;
  });
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Situação dos artigos", "Distribuição por etapa do ciclo editorial.",
      [donut(statusItems), legend(statusItems)]),
    card("Publicações por ano", "Barras: por ano · linha: acumulado no período.", [
      barChart(D.publications.series.map(function (d){
        return {label: d.year, value: d.n_articles};
      }), {tipLabel: ": ", color: css("--c2")}),
      lineChart([{label: "Acumulado", values: cumulative, color: css("--c1"), area: true}],
        {labels: years, height: 150}),
    ]),
  ]));

  const funnelSteps = [
    {label: "Iniciados", value: o.n_articles},
    {label: "Submetidos", value: o.n_submitted + o.n_accepted + o.n_published + o.n_rejected},
    {label: "Aceitos", value: o.n_accepted + o.n_published},
    {label: "Publicados", value: o.n_published},
  ];
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Funil da produção", "Quantos manuscritos chegam a cada etapa.", funnel(funnelSteps)),
    card("Produção por linha de pesquisa", "Artigos vinculados a cada linha.",
      hbarChart((D.research_lines || []).map(function (l, i){
        return {label: l.name, value: l.n_articles, color: color(i),
          note: l.n_published + " publicado(s)"};
      }), {tipLabel: ": ", labelWidth: 190, labelChars: 28, onClick: function (d){
        STATE.linha = d.label;
        buildToolbar();
        refresh();
        document.getElementById("producao").scrollIntoView({block: "start"});
      }})),
  ]));
}

function renderLines(){
  const rows = D.research_lines;
  const body = section("linhas", "Índice de linhas de pesquisa", rows.length,
    "Cada linha reúne artigos, pessoas, projetos e atividades. Clique para filtrar o painel.");
  if (!rows.length){
    body.appendChild(h("div", {class: "note", html:
      "<b>Nenhuma linha cadastrada ainda.</b> Cadastre em <a href='/app#linhas'>"
      + "Área do integrante → Linhas de pesquisa</a> ou na aba “Linhas de Pesquisa” de "
      + "<span class='mono'>data/raw/LAPE_cadastros.xlsx</span>."}));
    return;
  }
  body.appendChild(h("div", {class: "grid g3"}, rows.map(function (line, i){
    return h("div", {class: "card clickable", onclick: function (){
      STATE.linha = line.name;
      buildToolbar();
      refresh();
      document.getElementById("producao").scrollIntoView({block: "start"});
    }}, [
      h("h3", {text: line.name}),
      h("div", {class: "hint", text: line.description
        || (line.coordinator ? "Coordenação: " + line.coordinator : "—")}),
      h("div", {class: "grid g4", style: "gap:8px"}, [
        kpi("Artigos", line.n_articles), kpi("Publicados", line.n_published),
        kpi("Pessoas", line.n_members), kpi("Atividades", line.n_events),
      ]),
      line.keywords ? h("div", {class: "hint", style: "margin-top:10px", text: line.keywords}) : null,
    ]);
  })));
}

function renderResearchers(){
  const rows = (D.researchers || []).filter(function (r){
    return !r.is_external || r.n_articles > 0;
  });
  const body = section("pesquisadores", "Banco de pesquisadores", rows.length,
    "Nome, linha de pesquisa, projetos, artigos publicados e índice h. Clique numa"
    + " linha para abrir a ficha completa.");
  const host = h("div");
  const cols = [
    {k: "full_name", label: "Pesquisador", wide: true, onRow: function (r){ showResearcher(r.id); },
      render: function (r){
        return h("div", {}, [r.full_name,
          h("small", {text: [r.role, r.degree].filter(Boolean).join(" · ") || "—"})]);
      }},
    {k: "research_line", label: "Linha de pesquisa"},
    {k: "n_projects", label: "Projetos", num: true, render: function (r){
      return r.projects
        ? h("span", {title: r.projects.replace(/ \| /g, "\n"), text: r.n_projects})
        : r.n_projects; }},
    {k: "n_articles", label: "Artigos", num: true},
    {k: "n_published", label: "Publicados", num: true},
    {k: "n_submitted", label: "Submetidos", num: true},
    {k: "h_index", label: "Índice h", num: true},
    {k: "citations_total", label: "Citações", num: true},
  ];
  function paint(term){
    host.innerHTML = "";
    host.appendChild(table(cols, rows.filter(function (r){
      return !term || JSON.stringify(r).toLowerCase().includes(term);
    }), "Nenhum pesquisador cadastrado.", {sortKey: "n_articles"}));
  }
  body.appendChild(h("div", {class: "rowbar"}, [
    h("div", {class: "hint",
      text: "Ordene clicando no cabeçalho. O índice h vem do OpenAlex quando há ORCID."}),
    searchBox("Buscar pesquisador…", paint),
  ]));
  paint("");
  body.appendChild(host);

  const ranked = rows.filter(function (r){ return (r.h_index || 0) > 0; })
    .sort(function (a, b){ return b.h_index - a.h_index; }).slice(0, 15);
  if (ranked.length) body.appendChild(h("div", {style: "margin-top:14px"},
    card("Índice h por pesquisador", null, hbarChart(ranked.map(function (r){
      return {label: r.short_name || r.full_name, value: r.h_index,
        note: (r.citations_total || 0) + " citações"};
    }), {tipLabel: ": ", labelWidth: 170, color: css("--c4"), onClick: function (d){
      const person = rows.find(function (r){
        return (r.short_name || r.full_name) === d.label;
      });
      if (person) showResearcher(person.id);
    }}))));
}

function renderProjects(){
  const data = D.projects || {items: [], total: 0};
  const body = section("projetos", "Projetos", data.total,
    "Projetos de pesquisa e extensão, com equipe, financiamento e vigência.");
  if (!data.total){
    body.appendChild(h("div", {class: "note", html:
      "<b>Nenhum projeto cadastrado.</b> Cadastre em <a href='/app#projetos'>"
      + "Área do integrante → Projetos</a> ou na aba “Projetos” da planilha de cadastros."}));
    return;
  }
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Projetos", data.total, "no banco", true),
    kpi("Em andamento", data.active, "vigentes"),
    kpi("Financiadores", data.by_funder.length, "agências distintas"),
    kpi("Recursos", data.total_amount ? "R$ " + dec(data.total_amount, 2) : "—", "somados"),
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"}, table([
    {k: "code", label: "Código"},
    {k: "name", label: "Projeto", wide: true, render: function (r){
      return h("div", {}, [r.name,
        h("small", {text: r.members ? truncate(r.members, 80) : "sem equipe cadastrada"})]); }},
    {k: "coordinator", label: "Coordenação"},
    {k: "funder", label: "Financiador"},
    {k: "n_members", label: "Equipe", num: true},
    {k: "started_on", label: "Início", render: function (r){ return dt(r.started_on); }},
    {k: "ended_on", label: "Término", render: function (r){ return dt(r.ended_on); }},
    {k: "status", label: "Situação", render: function (r){
      return h("span", {class: "badge " + (r.status === "em_andamento" ? "b-publicado" : "b-neutro"),
        text: PROJECT_LABEL[r.status] || r.status}); }},
  ], data.items)));
  if (data.by_funder.length) body.appendChild(h("div", {style: "margin-top:14px"},
    card("Projetos por financiador", null, hbarChart(data.by_funder.map(function (f, i){
      return {label: f.funder, value: f.n, color: color(i)};
    }), {tipLabel: ": ", labelWidth: 150}))));
}

function progressBar(row){
  const wrap = h("span", {class: "prog"});
  const done = row.versions_done || 0;
  for (let i = 0; i < 5; i++) wrap.appendChild(h("i", {class: i < done ? "on" : null}));
  if (row.submission_attempts) wrap.appendChild(h("i", {class: "sub"}));
  return wrap;
}

function renderInProgress(){
  dynamicSection("producao", "Artigos em produção",
    "Manuscritos em escrita, com data de início, equipe e tempo em aberto.",
    function (body, all){
      const rows = all.filter(function (a){ return a.status === "em_producao"; });
      body.appendChild(table([
        {k: "internal_code", label: "ID"},
        {k: "title", label: "Título", wide: true, onRow: showArticle, render: function (r){
          return h("div", {}, [r.title,
            h("small", {text: r.research_line || "sem linha de pesquisa"})]); }},
        {k: "authors", label: "Autores", render: function (r){ return truncate(r.authors, 55); }},
        {k: "started_on", label: "Início", render: function (r){ return dt(r.started_on); }},
        {label: "Em aberto", num: true, sortValue: function (r){
          return r.started_on ? Date.now() - new Date(r.started_on + "T00:00:00").getTime() : -1; },
          render: function (r){
            return r.started_on
              ? dur((Date.now() - new Date(r.started_on + "T00:00:00").getTime()) / 86400000)
              : "—"; }},
        {label: "Situação", render: function (r){ return badge(r.status); }},
      ], rows, "Nenhum artigo em produção com os filtros atuais."));

      const byLead = {};
      rows.forEach(function (r){
        const lead = r.lead_name || (r.authors || "").split(";")[0].trim() || "—";
        byLead[lead] = (byLead[lead] || 0) + 1;
      });
      const items = Object.keys(byLead).map(function (k){
        return {label: k, value: byLead[k]};
      }).sort(function (a, b){ return b.value - a.value; });
      if (items.length) body.appendChild(h("div", {style: "margin-top:14px"},
        card("Carga por responsável", "Artigos em produção sob responsabilidade de cada pessoa.",
          hbarChart(items, {tipLabel: ": ", color: css("--c1")}))));
      return rows.length;
    });
}

function renderSubmitted(){
  dynamicSection("submetidos", "Artigos submetidos",
    "Manuscritos sob avaliação, com a revista e o tempo desde o envio.",
    function (body, all){
      const rows = all.filter(function (a){
        return a.status === "submetido" || a.status === "em_revisao";
      });
      body.appendChild(table([
        {k: "internal_code", label: "ID"},
        {k: "title", label: "Título", wide: true, onRow: showArticle},
        {k: "authors", label: "Autores", render: function (r){ return truncate(r.authors, 45); }},
        {k: "journal", label: "Revista"},
        {k: "first_submission_on", label: "Submissão", render: function (r){
          return dt(r.first_submission_on); }},
        {k: "submission_attempts", label: "Tentativas", num: true},
        {label: "Em avaliação há", num: true, sortValue: function (r){
          return r.first_submission_on
            ? Date.now() - new Date(r.first_submission_on + "T00:00:00").getTime() : -1; },
          render: function (r){
            return r.first_submission_on
              ? dur((Date.now() - new Date(r.first_submission_on + "T00:00:00").getTime())
                / 86400000) : "—"; }},
      ], rows, "Nenhum artigo submetido com os filtros atuais."));
      return rows.length;
    });
}

function renderPublications(){
  dynamicSection("publicacoes", "Publicações por ano",
    "Estudos publicados, com total e média anual na janela de análise.",
    function (body, all){
      const p = D.publications;
      const published = all.filter(function (a){ return a.status === "publicado"; });
      const currentYear = new Date().getFullYear();
      const years = [];
      for (let y = currentYear - p.window + 1; y <= currentYear; y++) years.push(y);
      const perYear = years.map(function (y){
        return published.filter(function (a){ return a.year_published === y; }).length;
      });
      const windowTotal = perYear.reduce(function (a, b){ return a + b; }, 0);
      const allYears = Array.from(new Set(published.map(function (a){ return a.year_published; })
        .filter(Boolean))).sort();

      body.appendChild(h("div", {class: "grid g4"}, [
        kpi("Total no período", windowTotal, "últimos " + p.window + " anos", true),
        kpi("Média por ano", dec(windowTotal / p.window, 2), "artigos/ano"),
        kpi("Total (filtro atual)", published.length, "todos os anos"),
        kpi("Melhor ano", (function (){
          const best = perYear.indexOf(Math.max.apply(null, perYear));
          return windowTotal ? years[best] : "—";
        })(), "no período analisado"),
      ]));
      body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
        card("Publicações por ano (janela de " + p.window + " anos)", null,
          barChart(years.map(function (y, i){
            return {label: y, value: perYear[i]};
          }), {tipLabel: ": ", color: css("--c2"), onClick: function (d){
            STATE.ano = String(d.label);
            buildToolbar();
            refresh();
          }})),
        card("Série histórica completa", "Todos os anos com publicações registradas.",
          barChart(allYears.map(function (y){
            return {label: y, value: published.filter(function (a){
              return a.year_published === y; }).length};
          }), {tipLabel: ": ", color: css("--c1")})),
      ]));

      const journals = {};
      published.forEach(function (a){
        if (a.journal) journals[a.journal] = (journals[a.journal] || 0) + 1;
      });
      const topJournals = Object.keys(journals).map(function (k){
        return {label: k, value: journals[k]};
      }).sort(function (a, b){ return b.value - a.value; }).slice(0, 12);
      if (topJournals.length) body.appendChild(h("div", {style: "margin-top:14px"},
        card("Periódicos onde o laboratório publica", null,
          hbarChart(topJournals, {tipLabel: ": ", labelWidth: 210, labelChars: 32,
            color: css("--c5")}))));

      if (!published.length) body.appendChild(h("div", {class: "note", style: "margin-top:14px",
        html: "<b>Sem publicações com os filtros atuais.</b> Importe o XML do Currículo Lattes "
          + "ou cadastre em <a href='/app#artigos'>Área do integrante → Artigos</a>."}));
      return published.length;
    });
}

function citationTable(rows){
  return table([
    {k: "title", label: "Título", wide: true, onRow: showArticle, render: function (r){
      return h("div", {}, [
        r.url || r.doi ? h("a", {href: r.url || ("https://doi.org/" + r.doi), target: "_blank",
          rel: "noopener", text: r.title}) : r.title,
        h("small", {text: [r.journal, r.year_published].filter(Boolean).join(" · ")}),
      ]);
    }},
    {k: "authors", label: "Autores", render: function (r){ return truncate(r.authors, 42); }},
    {k: "year_published", label: "Ano", num: true},
    {k: "wos_citations", label: "WoS", num: true},
    {k: "scopus_citations", label: "Scopus", num: true},
    {k: "openalex_citations", label: "OpenAlex", num: true},
  ], rows, "Sem citações coletadas para este recorte.", {sortKey: "scopus_citations"});
}

function renderCitations(){
  dynamicSection("citacoes", "Artigos mais citados",
    "Ranking por base. As contagens são atualizadas pelo DOI a cada execução do rastreador.",
    function (body, all){
      const published = all.filter(function (a){ return a.status === "publicado"; });
      const window = D.overview.window;
      const cutoff = new Date().getFullYear() - window + 1;
      function top(field, recent){
        return published
          .filter(function (a){ return (a[field] || 0) > 0
            && (!recent || (a.year_published || 0) >= cutoff); })
          .sort(function (a, b){ return (b[field] || 0) - (a[field] || 0); })
          .slice(0, 12);
      }
      body.appendChild(tabs([
        {label: "Scopus — geral", content: citationTable(top("scopus_citations"))},
        {label: "Scopus — " + window + " anos", content: citationTable(top("scopus_citations", true))},
        {label: "Web of Science — geral", content: citationTable(top("wos_citations"))},
        {label: "WoS — " + window + " anos", content: citationTable(top("wos_citations", true))},
        {label: "OpenAlex — geral", content: citationTable(top("openalex_citations"))},
        {label: "OpenAlex — " + window + " anos",
          content: citationTable(top("openalex_citations", true))},
      ]));
      const total = published.reduce(function (acc, a){ return acc + bestCitations(a); }, 0);
      const cited = published.filter(function (a){ return bestCitations(a) > 0; });
      body.appendChild(h("div", {class: "grid g4", style: "margin-top:14px"}, [
        kpi("Citações somadas", total, "melhor base por artigo"),
        kpi("Artigos citados", cited.length, "de " + published.length + " publicados"),
        kpi("Mediana", cited.length ? median(cited.map(bestCitations)) : "—", "citações por artigo"),
        kpi("Mais citado", cited.length ? Math.max.apply(null, cited.map(bestCitations)) : "—",
          "citações"),
      ]));
      body.appendChild(h("div", {class: "note", style: "margin-top:14px", html:
        "<b>OpenAlex</b> é uma base aberta e não exige chave de API — por isso serve de "
        + "referência imediata de impacto enquanto Scopus e Web of Science não estiverem"
        + " configurados."}));
      return cited.length;
    });
}

function renderMembers(){
  dynamicSection("equipe", "Artigos por integrante",
    "Envolvimento de cada pessoa nos artigos do recorte atual.",
    function (body, all){
      const counts = (D.researchers || []).map(function (person){
        const set = MEMBER_ARTICLES.get(person.id) || new Set();
        let total = 0, published = 0, progress = 0;
        all.forEach(function (a){
          if (!set.has(a.id)) return;
          total += 1;
          if (a.status === "publicado") published += 1;
          if (a.status === "em_producao") progress += 1;
        });
        return Object.assign({}, person, {f_total: total, f_published: published,
          f_progress: progress});
      }).filter(function (p){ return p.f_total > 0; })
        .sort(function (a, b){ return b.f_total - a.f_total; });

      body.appendChild(card("Envolvimento em artigos",
        "Barras laranja indicam colaboradores externos. Clique para abrir a ficha.",
        [hbarChart(counts.slice(0, 25).map(function (r){
          return {label: r.short_name || r.full_name, value: r.f_total,
            color: r.is_external ? css("--c3") : css("--c1"),
            note: r.f_published + " publicado(s) · " + r.f_progress + " em produção"};
        }), {tipLabel: ": ", labelWidth: 165, onClick: function (d){
          const person = counts.find(function (r){
            return (r.short_name || r.full_name) === d.label;
          });
          if (person) showResearcher(person.id);
        }}),
        legend([{label: "Integrante do LAPE", color: css("--c1")},
                {label: "Colaborador externo", color: css("--c3")}])]));

      body.appendChild(h("div", {style: "margin-top:14px"}, table([
        {k: "full_name", label: "Integrante", wide: true, onRow: function (r){
          showResearcher(r.id); }, render: function (r){
          return h("div", {}, [r.full_name, h("small", {text:
            [r.role, r.research_line].filter(Boolean).join(" · ") || "—"})]); }},
        {k: "f_total", label: "Artigos", num: true},
        {k: "f_progress", label: "Em produção", num: true},
        {k: "f_published", label: "Publicados", num: true},
        {k: "n_projects", label: "Projetos", num: true},
        {k: "h_index", label: "Índice h", num: true},
        {k: "citations_total", label: "Citações", num: true},
      ], counts, "Ninguém corresponde aos filtros atuais.", {sortKey: "f_total"})));
      return counts.length;
    });
}

function renderNetwork(){
  const net = D.network;
  const body = section("rede", "Rede de colaboração", net.n_nodes + " pessoas",
    "Cada nó é um integrante; a espessura da linha é o número de artigos em coautoria."
    + " Clique num nó para abrir a ficha.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Pessoas na rede", net.n_nodes, "com ao menos um artigo"),
    kpi("Pares em coautoria", net.n_edges, "ligações distintas"),
    kpi("Densidade", dec(net.density, 3), "0 = isolados, 1 = todos com todos"),
    kpi("Grau médio", dec(net.mean_degree, 2), "coautores por pessoa"),
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"}, card(null, null, networkChart(net))));
  if (net.top_pairs.length) body.appendChild(h("div", {style: "margin-top:14px"},
    card("Duplas mais produtivas", "Pares com maior número de artigos em comum.",
      hbarChart(net.top_pairs.map(function (p){
        return {label: p.a + " + " + p.b, value: p.weight};
      }), {tipLabel: ": ", labelWidth: 210, labelChars: 30, color: css("--c4")}))));
}

function renderTimes(){
  dynamicSection("tempos", "Tempos do ciclo editorial",
    "Quanto tempo cada etapa leva, do início do artigo até a publicação.",
    function (body, all){
      function stats(field){
        const values = all.map(function (a){ return a[field]; })
          .filter(function (v){ return v !== null && v !== undefined; }).map(Number)
          .sort(function (a, b){ return a - b; });
        if (!values.length) return {n: 0};
        const mean = values.reduce(function (a, b){ return a + b; }, 0) / values.length;
        const quantile = function (p){
          const pos = (values.length - 1) * p;
          const low = Math.floor(pos), high = Math.min(low + 1, values.length - 1);
          return values[low] + (values[high] - values[low]) * (pos - low);
        };
        const sd = values.length > 1 ? Math.sqrt(values.reduce(function (acc, v){
          return acc + (v - mean) * (v - mean); }, 0) / (values.length - 1)) : 0;
        return {n: values.length, min: values[0], max: values[values.length - 1], mean: mean,
          median: median(values), p25: quantile(0.25), p75: quantile(0.75), sd: sd};
      }
      const startToPub = stats("days_start_to_publication");
      body.appendChild(h("div", {class: "grid g3"}, [
        statBox("Início → publicação", startToPub),
        statBox("Submissão → aceite", stats("days_submission_to_acceptance")),
        statBox("Aceite → publicação", stats("days_acceptance_to_publication")),
      ]));

      const bins = [[0, 180, "< 6 meses"], [180, 365, "6-12 meses"], [365, 730, "1-2 anos"],
        [730, 1095, "2-3 anos"], [1095, Infinity, "> 3 anos"]];
      const values = all.map(function (a){ return a.days_start_to_publication; })
        .filter(function (v){ return v !== null && v !== undefined; });
      const hist = bins.map(function (b){
        return {label: b[2], value: values.filter(function (v){
          return v >= b[0] && v < b[1]; }).length};
      }).filter(function (d){ return d.value; });
      if (hist.length) body.appendChild(h("div", {style: "margin-top:14px"},
        card("Distribuição do tempo início → publicação", null,
          barChart(hist, {tipLabel: ": ", color: css("--c5")}))));

      const withDates = all.filter(function (a){
        return a.status === "publicado" || a.status === "aceito";
      });
      if (withDates.length) body.appendChild(h("div", {style: "margin-top:14px"}, table([
        {k: "title", label: "Artigo", wide: true, onRow: showArticle},
        {k: "journal", label: "Revista"},
        {k: "started_on", label: "Início", render: function (r){ return dt(r.started_on); }},
        {k: "first_submission_on", label: "1ª submissão", render: function (r){
          return dt(r.first_submission_on); }},
        {k: "accepted_on", label: "Aceite", render: function (r){ return dt(r.accepted_on); }},
        {k: "published_on", label: "Publicação", render: function (r){
          return dt(r.published_on); }},
        {k: "days_start_to_publication", label: "Início→pub.", num: true, render: function (r){
          return dur(r.days_start_to_publication); }},
        {k: "submission_attempts", label: "Tentativas", num: true},
      ], withDates, "Nenhum artigo publicado ou aceito no recorte.")));
      return startToPub.n;
    });
}

function renderSubmissions(){
  const sub = D.submissions;
  const body = section("submissoes", "Submissões, tentativas e recusas", sub.total,
    "Histórico de envios: quantas tentativas cada artigo exigiu, quanto tempo entre elas"
    + " e por que foi recusado.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Submissões", sub.total, "tentativas registradas", true),
    kpi("Taxa de aceite", dec(sub.acceptance_rate, 1) + "%", sub.accepted + " aceite(s)"),
    kpi("Taxa de recusa", dec(sub.rejection_rate, 1) + "%", sub.rejected + " recusa(s)"),
    kpi("Desk rejections", sub.desk_rejects, "recusadas sem revisão"),
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Tentativas por artigo", "Quantos envios cada manuscrito exigiu.",
      barChart(sub.attempts_distribution.map(function (d){
        return {label: d.attempts + "×", value: d.n};
      }), {tipLabel: " artigos: ", color: css("--c1")})),
    card("Decisões editoriais", null, barChart(sub.decisions.map(function (d, i){
      return {label: DECISION_LABEL[d.decision] || d.decision, value: d.n, color: color(i)};
    }), {tipLabel: ": ", height: 220})),
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    statBox("Intervalo entre submissões", sub.gap_summary),
    statBox("Decisão → nova submissão", sub.decision_to_resubmission),
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Motivos das recusas", "Alimentado pela coluna “Motivo/observação” das tentativas.",
    sub.rejection_reasons.length
      ? hbarChart(sub.rejection_reasons.map(function (r){
          return {label: r.reason, value: r.n, note: r.category};
        }), {tipLabel: ": ", labelWidth: 230, labelChars: 34, color: css("--c6")})
      : h("div", {class: "empty", text: "Nenhuma recusa com motivo registrado."}))));
  body.appendChild(h("div", {style: "margin-top:14px"}, table([
    {k: "title", label: "Artigo", wide: true},
    {k: "attempts", label: "Tentativas", num: true},
    {k: "rejections", label: "Recusas", num: true},
    {k: "first_submitted_on", label: "1ª submissão", render: function (r){
      return dt(r.first_submitted_on); }},
    {k: "last_submitted_on", label: "Última", render: function (r){
      return dt(r.last_submitted_on); }},
    {k: "status", label: "Situação", render: function (r){ return badge(r.status); }},
  ], sub.per_article, "Nenhuma submissão registrada.", {sortKey: "attempts"})));
  if (sub.gaps.length) body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Intervalos entre uma submissão e a ressubmissão", null, table([
      {k: "title", label: "Artigo", wide: true},
      {k: "attempt_no", label: "Tentativa", num: true},
      {k: "previous_submitted_on", label: "Submissão anterior", render: function (r){
        return dt(r.previous_submitted_on); }},
      {k: "previous_decision_on", label: "Decisão anterior", render: function (r){
        return dt(r.previous_decision_on); }},
      {k: "submitted_on", label: "Nova submissão", render: function (r){
        return dt(r.submitted_on); }},
      {k: "days_between_submissions", label: "Entre submissões", num: true,
        render: function (r){ return dur(r.days_between_submissions); }},
      {k: "days_decision_to_resubmission", label: "Decisão→reenvio", num: true,
        render: function (r){ return dur(r.days_decision_to_resubmission); }},
    ], sub.gaps))));
  if (sub.per_journal.length) body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Revistas mais utilizadas", null, table([
      {k: "journal", label: "Revista", wide: true},
      {k: "n", label: "Submissões", num: true},
      {k: "accepted", label: "Aceitas", num: true},
      {k: "rejected", label: "Recusadas", num: true},
    ], sub.per_journal, null, {sortKey: "n"}))));
}

function renderAcceptances(){
  const rows = D.acceptances;
  const body = section("aceites", "Datas de aceite", rows.length,
    "Aceites registrados, com o tempo decorrido desde a primeira submissão.");
  body.appendChild(table([
    {k: "title", label: "Artigo", wide: true},
    {k: "authors", label: "Autores", render: function (r){ return truncate(r.authors, 42); }},
    {k: "journal", label: "Revista"},
    {k: "first_submission_on", label: "1ª submissão", render: function (r){
      return dt(r.first_submission_on); }},
    {k: "accepted_on", label: "Aceite", render: function (r){ return dt(r.accepted_on); }},
    {k: "published_on", label: "Publicação", render: function (r){ return dt(r.published_on); }},
    {k: "days_submission_to_acceptance", label: "Submissão→aceite", num: true,
      render: function (r){ return dur(r.days_submission_to_acceptance); }},
    {k: "submission_attempts", label: "Tentativas", num: true},
  ], rows, "Nenhum aceite registrado ainda.", {sortKey: "accepted_on"}));
}

function renderCalendar(){
  const ag = D.agenda;
  const body = section("calendario", "Calendário e atividades", ag.total,
    "Reuniões, coletas, defesas e eventos científicos do laboratório.");
  const state = {ref: new Date()};
  const calCard = h("div", {class: "card"});
  const byDay = {};
  ag.events.forEach(function (e){
    const key = String(e.start_at).slice(0, 10);
    (byDay[key] = byDay[key] || []).push(e);
  });
  function drawCal(){
    calCard.innerHTML = "";
    const y = state.ref.getFullYear(), m = state.ref.getMonth();
    calCard.appendChild(h("div", {class: "calhead"}, [
      h("button", {text: "‹", title: "Mês anterior", onclick: function (){
        state.ref = new Date(y, m - 1, 1); drawCal(); }}),
      h("h3", {text: MONTHS[m].toUpperCase() + " " + y}),
      h("button", {text: "›", title: "Próximo mês", onclick: function (){
        state.ref = new Date(y, m + 1, 1); drawCal(); }}),
    ]));
    const grid = h("div", {class: "cal"});
    DOW.forEach(function (d){ grid.appendChild(h("div", {class: "dow", text: d})); });
    const first = new Date(y, m, 1).getDay();
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    const prevDays = new Date(y, m, 0).getDate();
    const today = new Date();
    for (let i = 0; i < first; i++)
      grid.appendChild(h("div", {class: "day out", text: prevDays - first + i + 1}));
    for (let d = 1; d <= daysInMonth; d++){
      const key = y + "-" + String(m + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0");
      const evts = byDay[key] || [];
      const isToday = today.getFullYear() === y && today.getMonth() === m && today.getDate() === d;
      const cell = h("div", {class: "day" + (evts.length ? " has" : "")
        + (isToday ? " today" : "")}, [
        String(d), evts.length ? h("em", {text: "●".repeat(Math.min(evts.length, 3))}) : null,
      ]);
      if (evts.length) tipOn(cell, "<b>" + dt(key) + "</b>" + evts.map(function (e){
        return (KIND_LABEL[e.kind] || e.kind) + ": " + e.title; }).join("<br>"));
      grid.appendChild(cell);
    }
    calCard.appendChild(grid);
  }
  drawCal();
  const agendaList = h("ul", {class: "agenda"}, ag.upcoming.map(function (e){
    const iso = String(e.start_at);
    return h("li", {}, [
      h("div", {class: "when"}, [h("b", {text: iso.slice(8, 10)}),
        MONTHS[Number(iso.slice(5, 7)) - 1]]),
      h("div", {class: "what"}, [e.title, h("small", {text:
        [KIND_LABEL[e.kind] || e.kind, dtm(e.start_at), e.location_name || e.city,
         e.n_participants ? e.n_participants + " participantes" : null]
          .filter(Boolean).join(" · ")})]),
    ]);
  }));
  body.appendChild(h("div", {class: "grid g2"}, [
    calCard,
    card("Próximas atividades", ag.upcoming.length ? null : null,
      ag.upcoming.length ? agendaList : h("div", {class: "empty", html:
        "Nenhuma atividade futura. Cadastre em <a href='/app#eventos'>"
        + "Área do integrante → Atividades</a>."})),
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Atividades por tipo", null, hbarChart(ag.by_kind.map(function (d, i){
      return {label: KIND_LABEL[d.kind] || d.kind, value: d.n, color: color(i)};
    }), {tipLabel: ": ", labelWidth: 140})),
    card("Atividades por ano", null, barChart(ag.by_year.map(function (d){
      return {label: d.year, value: d.n};
    }), {tipLabel: ": ", color: css("--c4")})),
  ]));
}

function renderTemporal(){
  const t = D.temporal;
  const body = section("temporal", "Linha do tempo", null,
    "Distribuição mês a mês de publicações, submissões e atividades nos últimos "
    + D.overview.window + " anos.");
  body.appendChild(tabs([
    {label: "Publicações", content: card(null, "Artigos publicados por mês.",
      heatGrid(t.years, t.months, t.publications, "publicação(ões)"))},
    {label: "Submissões", content: card(null, "Envios a revistas por mês.",
      heatGrid(t.years, t.months, t.submissions, "submissão(ões)"))},
    {label: "Atividades", content: card(null, "Reuniões, coletas e eventos por mês.",
      heatGrid(t.years, t.months, t.activities, "atividade(s)"))},
  ]));
  const totals = [
    {label: "Publicações", values: t.years.map(function (_, r){
      return t.publications.slice(r * 12, r * 12 + 12).reduce(function (a, b){ return a + b; }, 0);
    }), color: css("--c2")},
    {label: "Submissões", values: t.years.map(function (_, r){
      return t.submissions.slice(r * 12, r * 12 + 12).reduce(function (a, b){ return a + b; }, 0);
    }), color: css("--c3")},
    {label: "Atividades", values: t.years.map(function (_, r){
      return t.activities.slice(r * 12, r * 12 + 12).reduce(function (a, b){ return a + b; }, 0);
    }), color: css("--c1")},
  ];
  body.appendChild(h("div", {style: "margin-top:14px"},
    card("Evolução anual comparada", null,
      [lineChart(totals, {labels: t.years.map(String)}), legend(totals)])));
}

function renderSpatial(){
  const sp = D.spatial;
  const body = section("espacial", "Distribuição espacial", null,
    "Onde as atividades acontecem e de onde vêm as instituições parceiras.");
  body.appendChild(h("div", {class: "grid g2"}, [
    card("Mapa de atividades", "O tamanho do círculo é o número de atividades no local.",
      mapChart(sp.geolocated)),
    card("Locais", "Cidades com atividades registradas.", table([
      {k: "city", label: "Cidade"},
      {k: "state", label: "UF"},
      {k: "country", label: "País"},
      {k: "n_events", label: "Atividades", num: true},
    ], sp.places, "Nenhum local registrado.", {sortKey: "n_events"})),
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Instituições", "Vínculos institucionais dos integrantes e colaboradores.", table([
      {k: "name", label: "Instituição", wide: true, render: function (r){
        return h("div", {}, [r.name, h("small", {text:
          [r.city, r.state, r.country].filter(Boolean).join(" · ")})]); }},
      {k: "acronym", label: "Sigla"},
      {k: "n_members", label: "Integrantes", num: true},
      {k: "n_articles", label: "Artigos", num: true},
    ], sp.institutions, "Nenhuma instituição cadastrada.", {sortKey: "n_articles"}))));
}

function renderDiscoveries(){
  const rows = D.discoveries || [];
  const body = section("descobertas", "Achados do rastreador", rows.length,
    "Publicações encontradas nas bases externas que ainda não estão no banco.");
  if (!rows.length){
    body.appendChild(h("div", {class: "note", html:
      "<b>Nenhum achado pendente.</b> Rode o rastreador em "
      + (LIVE ? "<a href='/app#admin'>Área do integrante → Administração</a>"
              : "<span class='mono'>python3 scripts/lape_agent.py rastreador descobrir</span>")
      + "."}));
    return;
  }
  body.appendChild(h("div", {class: "note", html: LIVE
    ? "Aprove ou descarte cada achado em <a href='/app#admin'>Administração</a>."
    : "Para aprovar: <span class='mono'>python3 scripts/lape_agent.py revisar --aceitar "
      + rows[0].id + "</span>"}));
  body.appendChild(table([
    {k: "id", label: "ID", num: true},
    {k: "title", label: "Título", wide: true, render: function (r){
      return h("div", {}, [
        r.url ? h("a", {href: r.url, target: "_blank", rel: "noopener", text: r.title}) : r.title,
        h("small", {text: [r.journal, r.authors ? truncate(r.authors, 70) : null]
          .filter(Boolean).join(" · ")}),
      ]);
    }},
    {k: "year", label: "Ano", num: true},
    {k: "citations", label: "Citações", num: true},
    {k: "source", label: "Fonte"},
  ], rows, null, {sortKey: "citations"}));
}

function renderQuality(){
  const q = D.quality;
  const body = section("qualidade", "Qualidade dos dados", null,
    "Lacunas que limitam as análises. Cada item corresponde a um campo a preencher.");
  body.appendChild(h("div", {class: "grid g2"}, [
    card("Campos a completar", "Quanto menor, mais completo o banco.",
      h("ul", {class: "issues"}, q.issues.map(function (item){
        return h("li", {}, [item.label,
          h("span", {class: "n " + (item.n ? "some" : "zero"), text: item.n})]);
      }))),
    card("Últimas cargas", "Registro de cada leitura de arquivo e chamada de API.", table([
      {k: "run_at", label: "Quando", render: function (r){ return dtm(r.run_at); }},
      {k: "source", label: "Fonte"},
      {k: "target", label: "Destino"},
      {k: "rows_read", label: "Lidas", num: true},
      {k: "rows_written", label: "Gravadas", num: true},
      {k: "status", label: "Status"},
    ], q.last_runs, "Sem execuções registradas.", {sortable: false})),
  ]));
}

/* ---------------------------------------------------------------- */
/* navegação                                                          */
/* ---------------------------------------------------------------- */
function buildNav(){
  const sections = Array.prototype.slice.call(document.querySelectorAll("section"));
  const nav = document.getElementById("nav");
  const links = [];
  const GROUPS = {
    "visao-geral": "", linhas: "", pesquisadores: "Pessoas e projetos", projetos: null,
    producao: "Produção", submetidos: null, publicacoes: null, citacoes: null,
    equipe: "Métricas internas", rede: null, tempos: null, submissoes: null, aceites: null,
    calendario: "Espaço-temporal", temporal: null, espacial: null,
    descobertas: "Governança", qualidade: null,
  };
  sections.forEach(function (sec){
    const group = GROUPS[sec.id];
    if (group) nav.appendChild(h("div", {class: "group", text: group}));
    const title = sec.querySelector("h2").firstChild.textContent;
    const link = h("a", {href: "#" + sec.id, text: title});
    nav.appendChild(link);
    links.push(link);
  });

  sections.forEach(function (sec, i){
    const prev = sections[i - 1], next = sections[i + 1];
    sec.appendChild(h("div", {class: "secnav"}, [
      prev ? h("a", {href: "#" + prev.id, class: "navbtn",
        text: "← " + prev.querySelector("h2").firstChild.textContent}) : h("span"),
      h("a", {href: "#topo", class: "navbtn", text: "↑ Topo"}),
      next ? h("a", {href: "#" + next.id, class: "navbtn",
        text: next.querySelector("h2").firstChild.textContent + " →"}) : h("span"),
    ]));
  });

  const observer = new IntersectionObserver(function (entries){
    entries.forEach(function (entry){
      if (!entry.isIntersecting) return;
      links.forEach(function (a){
        a.classList.toggle("active", a.getAttribute("href") === "#" + entry.target.id);
      });
    });
  }, {rootMargin: "-12% 0px -78% 0px"});
  sections.forEach(function (sec){ observer.observe(sec); });
}

function setupTheme(){
  const toggle = document.getElementById("themeToggle");
  let stored = null;
  try { stored = localStorage.getItem("lape-theme"); } catch (e) {}
  if (stored) document.documentElement.setAttribute("data-theme", stored);
  toggle.addEventListener("click", function (){
    const dark = document.documentElement.getAttribute("data-theme") === "dark"
      || (!document.documentElement.getAttribute("data-theme")
          && matchMedia("(prefers-color-scheme:dark)").matches);
    const next = dark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("lape-theme", next); } catch (e) {}
    location.reload();
  });
}

/* ---------------------------------------------------------------- */
/* boot                                                               */
/* ---------------------------------------------------------------- */
function boot(){
  renderHeader();
  renderOverview();
  renderLines();
  renderResearchers();
  renderProjects();
  renderInProgress();
  renderSubmitted();
  renderPublications();
  renderCitations();
  renderMembers();
  renderNetwork();
  renderTimes();
  renderSubmissions();
  renderAcceptances();
  renderCalendar();
  renderTemporal();
  renderSpatial();
  renderDiscoveries();
  renderQuality();
  buildToolbar();
  buildNav();
  setupTheme();

  document.getElementById("drawerClose").addEventListener("click", closeDrawer);
  document.getElementById("scrim").addEventListener("click", closeDrawer);
  addEventListener("keydown", function (ev){ if (ev.key === "Escape") closeDrawer(); });
  const toTop = document.getElementById("toTop");
  addEventListener("scroll", function (){
    toTop.classList.toggle("on", scrollY > 700);
  });
  toTop.addEventListener("click", function (){ scrollTo({top: 0, behavior: "smooth"}); });
}
boot();
