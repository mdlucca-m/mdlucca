/* Painel LAPE - renderizacao sem dependencias externas. */
"use strict";
const D = JSON.parse(document.getElementById("payload").textContent);
const NS = "http://www.w3.org/2000/svg";
const PAL = ["--c1","--c2","--c3","--c4","--c5","--c6"];
const MONTHS = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];
const DOW = ["D","S","T","Q","Q","S","S"];
const STATUS_LABEL = {em_producao:"Em produção", submetido:"Submetido", em_revisao:"Em revisão",
  aceito:"Aceito", publicado:"Publicado", rejeitado:"Rejeitado", arquivado:"Arquivado"};
const DECISION_LABEL = {em_avaliacao:"Em avaliação", revisao_solicitada:"Revisão solicitada",
  aceito:"Aceito", rejeitado:"Rejeitado", desk_reject:"Desk rejection", retirado:"Retirado",
  sem_registro:"Sem registro"};
const KIND_LABEL = {reuniao:"Reunião", coleta:"Coleta de dados", defesa:"Defesa",
  qualificacao:"Qualificação", congresso:"Congresso", curso:"Curso/oficina",
  seminario:"Seminário", visita_tecnica:"Visita técnica", extensao:"Extensão", outro:"Outro"};

/* ---------- utilitarios ---------- */
function h(tag, attrs, kids){
  const node = document.createElement(tag);
  for (const k in (attrs||{})){
    const v = attrs[k];
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  (Array.isArray(kids) ? kids : (kids ? [kids] : [])).forEach(function(kid){
    if (kid === null || kid === undefined || kid === false) return;
    node.appendChild(typeof kid === "string" || typeof kid === "number"
      ? document.createTextNode(String(kid)) : kid);
  });
  return node;
}
function s(tag, attrs){
  const node = document.createElementNS(NS, tag);
  for (const k in (attrs||{})) if (attrs[k] !== null && attrs[k] !== undefined)
    node.setAttribute(k, attrs[k]);
  return node;
}
function css(name){ return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function color(i){ return css(PAL[i % PAL.length]); }
function num(v){ return (v === null || v === undefined || v === "") ? "—" : String(v); }
function dec(v, n){ return (v === null || v === undefined) ? "—" : Number(v).toFixed(n === undefined ? 1 : n).replace(".", ","); }
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
function badge(status){
  const key = (status || "").replace("em_", "").replace("revisao", "submetido");
  return h("span", {class: "badge b-" + (STATUS_LABEL[status] ? key : "neutro"),
    text: STATUS_LABEL[status] || status || "—"});
}
function truncate(text, n){
  if (!text) return "—";
  return text.length > n ? text.slice(0, n - 1) + "…" : text;
}

/* ---------- tooltip ---------- */
const TIP = document.getElementById("tip");
function tipOn(node, html){
  node.addEventListener("mousemove", function(ev){
    TIP.innerHTML = html;
    TIP.classList.add("on");
    const box = TIP.getBoundingClientRect();
    let x = ev.clientX + 14, y = ev.clientY - box.height - 10;
    if (x + box.width > innerWidth - 8) x = ev.clientX - box.width - 14;
    if (y < 8) y = ev.clientY + 18;
    TIP.style.left = x + "px"; TIP.style.top = y + "px";
  });
  node.addEventListener("mouseleave", function(){ TIP.classList.remove("on"); });
}

/* ---------- blocos ---------- */
const APP = document.getElementById("app");
function section(id, title, count, lead){
  const body = h("div");
  APP.appendChild(h("section", {id: id}, [
    h("h2", {}, [title, count !== null && count !== undefined ? h("span", {class: "n", text: count}) : null]),
    lead ? h("p", {class: "lead", text: lead}) : null,
    body
  ]));
  return body;
}
function card(title, hint, kids){
  return h("div", {class: "card"}, [
    title ? h("h3", {text: title}) : null,
    hint ? h("div", {class: "hint", text: hint}) : null
  ].concat(Array.isArray(kids) ? kids : [kids]));
}
function kpi(label, value, foot, accent){
  return h("div", {class: "kpi" + (accent ? " accent" : "")}, [
    h("div", {class: "label", text: label}),
    h("div", {class: "value", text: value}),
    foot ? h("div", {class: "foot", text: foot}) : null
  ]);
}
function table(cols, rows, emptyMsg){
  if (!rows || !rows.length) return h("div", {class: "tw"}, h("div", {class: "empty", text: emptyMsg || "Sem registros."}));
  const head = h("tr", {}, cols.map(function(c){ return h("th", {class: c.num ? "num" : null, text: c.label}); }));
  const body = rows.map(function(row){
    return h("tr", {}, cols.map(function(c){
      const value = c.render ? c.render(row) : row[c.k];
      const cell = h("td", {class: [c.num ? "num" : "", c.wide ? "title" : ""].join(" ").trim() || null});
      if (value instanceof Node) cell.appendChild(value);
      else cell.textContent = (value === null || value === undefined || value === "") ? "—" : String(value);
      return cell;
    }));
  });
  return h("div", {class: "tw"}, h("table", {}, [h("thead", {}, head), h("tbody", {}, body)]));
}
function tabs(items){
  const nav = h("div", {class: "tabs"});
  const wrap = h("div");
  items.forEach(function(item, i){
    const pane = h("div", {class: "tabpane" + (i === 0 ? " active" : "")}, item.content);
    const btn = h("button", {class: i === 0 ? "active" : null, text: item.label, onclick: function(){
      nav.querySelectorAll("button").forEach(function(b){ b.classList.remove("active"); });
      wrap.querySelectorAll(".tabpane").forEach(function(p){ p.classList.remove("active"); });
      btn.classList.add("active"); pane.classList.add("active");
    }});
    nav.appendChild(btn); wrap.appendChild(pane);
  });
  return h("div", {}, [nav, wrap]);
}

/* ---------- graficos ---------- */
function barChart(items, opts){
  opts = opts || {};
  const W = 640, H = opts.height || 220, ML = 42, MR = 10, MT = 14, MB = 34;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, role: "img"});
  if (!items.length){ svg.appendChild(s("text", {x: W/2, y: H/2, "text-anchor": "middle", class: "vlab"})).textContent = "sem dados"; return svg; }
  const max = Math.max.apply(null, items.map(function(d){ return d.value; }).concat([1]));
  const iw = W - ML - MR, ih = H - MT - MB;
  const bw = iw / items.length;
  const g = s("g"); svg.appendChild(g);
  const ticks = Math.min(4, Math.max(1, max));  // evita rotulos repetidos em series pequenas
  for (let t = 0; t <= ticks; t++){
    const y = MT + ih - ih * t / ticks;
    g.appendChild(s("line", {x1: ML, x2: W - MR, y1: y, y2: y, class: "gl"}));
    const lab = s("text", {x: ML - 7, y: y + 3.5, "text-anchor": "end", class: "vlab"});
    lab.textContent = Math.round(max * t / ticks); g.appendChild(lab);
  }
  items.forEach(function(d, i){
    const bh = Math.max(d.value > 0 ? 2 : 0, ih * d.value / max);
    const x = ML + i * bw + bw * 0.16, w = bw * 0.68, y = MT + ih - bh;
    const rect = s("rect", {x: x, y: y, width: w, height: bh, rx: 3, class: "bar",
      fill: d.color || opts.color || color(0)});
    tipOn(rect, "<b>" + d.label + "</b>" + (opts.tipLabel || "") + d.value);
    g.appendChild(rect);
    const val = s("text", {x: x + w/2, y: y - 5, "text-anchor": "middle", class: "vlab"});
    val.textContent = d.value || ""; g.appendChild(val);
    const lab = s("text", {x: x + w/2, y: H - MB + 15, "text-anchor": "middle", class: "vlab"});
    lab.textContent = d.label; g.appendChild(lab);
  });
  return svg;
}
function hbarChart(items, opts){
  opts = opts || {};
  const rowH = opts.rowH || 24, W = 640, ML = opts.labelWidth || 150, MR = 44;
  const H = Math.max(items.length * rowH + 10, 40);
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, role: "img"});
  if (!items.length){ const t = s("text", {x: 10, y: 22, class: "vlab"}); t.textContent = "sem dados"; svg.appendChild(t); return svg; }
  const max = Math.max.apply(null, items.map(function(d){ return d.value; }).concat([1]));
  const iw = W - ML - MR;
  items.forEach(function(d, i){
    const y = i * rowH + 5, bw = Math.max(d.value > 0 ? 2 : 0, iw * d.value / max);
    const lab = s("text", {x: ML - 8, y: y + rowH * 0.62, "text-anchor": "end", class: "vlab"});
    lab.textContent = truncate(d.label, opts.labelChars || 22); svg.appendChild(lab);
    const rect = s("rect", {x: ML, y: y + 3, width: bw, height: rowH - 10, rx: 3, class: "bar",
      fill: d.color || opts.color || color(0)});
    tipOn(rect, "<b>" + d.label + "</b>" + (opts.tipLabel || "") + d.value + (d.note ? "<br>" + d.note : ""));
    svg.appendChild(rect);
    const val = s("text", {x: ML + bw + 7, y: y + rowH * 0.62, class: "vlab"});
    val.textContent = d.value; svg.appendChild(val);
  });
  return svg;
}
function donut(items){
  const W = 240, R = 92, r = 58, cx = W/2, cy = W/2;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + W, style: "max-width:240px;margin:0 auto"});
  const total = items.reduce(function(a, b){ return a + b.value; }, 0);
  if (!total){ const t = s("text", {x: cx, y: cy, "text-anchor": "middle", class: "vlab"}); t.textContent = "sem dados"; svg.appendChild(t); return svg; }
  let angle = -Math.PI / 2;
  items.forEach(function(d, i){
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
    svg.appendChild(path);
    angle += span;
  });
  const big = s("text", {x: cx, y: cy - 2, "text-anchor": "middle",
    style: "font-size:26px;font-weight:700;fill:" + css("--text")});
  big.textContent = total; svg.appendChild(big);
  const sub = s("text", {x: cx, y: cy + 16, "text-anchor": "middle", class: "vlab"});
  sub.textContent = "artigos"; svg.appendChild(sub);
  return svg;
}
function legend(items){
  return h("div", {class: "legend"}, items.map(function(d, i){
    return h("span", {}, [h("i", {style: "background:" + (d.color || color(i))}), d.label]);
  }));
}
function heatGrid(years, months, values, label){
  const cell = 30, ML = 42, MT = 20;
  const W = ML + 12 * cell + 8, H = MT + years.length * cell + 8;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, style: "max-width:" + W + "px"});
  const max = Math.max.apply(null, values.concat([1]));
  MONTHS.forEach(function(m, i){
    const t = s("text", {x: ML + i * cell + cell/2, y: MT - 6, "text-anchor": "middle", class: "vlab"});
    t.textContent = m; svg.appendChild(t);
  });
  years.forEach(function(year, r){
    const t = s("text", {x: ML - 8, y: MT + r * cell + cell * 0.65, "text-anchor": "end", class: "vlab"});
    t.textContent = year; svg.appendChild(t);
    for (let c = 0; c < 12; c++){
      const idx = r * 12 + c, v = values[idx] || 0;
      const rect = s("rect", {x: ML + c * cell + 1, y: MT + r * cell + 1, width: cell - 3,
        height: cell - 3, rx: 4,
        fill: v ? color(0) : css("--surface-2"), "fill-opacity": v ? (0.22 + 0.78 * v / max) : 1,
        stroke: css("--border"), "stroke-width": v ? 0 : 1});
      tipOn(rect, "<b>" + MONTHS[c] + "/" + year + "</b>" + v + " " + label);
      svg.appendChild(rect);
      if (v){
        const t2 = s("text", {x: ML + c * cell + cell/2, y: MT + r * cell + cell * 0.66,
          "text-anchor": "middle", style: "font-size:11px;font-weight:600;fill:" + css("--text")});
        t2.textContent = v; svg.appendChild(t2);
      }
    }
  });
  return svg;
}
function forceLayout(nodes, edges, W, H, iterations){
  const k = Math.sqrt(W * H / Math.max(nodes.length, 1));
  const pos = new Map();
  nodes.forEach(function(n, i){
    const a = 2 * Math.PI * i / nodes.length;
    pos.set(n.id, {x: W/2 + Math.cos(a) * W * 0.32, y: H/2 + Math.sin(a) * H * 0.32, dx: 0, dy: 0});
  });
  let temp = W * 0.11;
  for (let it = 0; it < iterations; it++){
    pos.forEach(function(p){ p.dx = 0; p.dy = 0; });
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++){
      const a = pos.get(nodes[i].id), b = pos.get(nodes[j].id);
      let dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy) || 0.01;
      const rep = k * k / d;
      a.dx += dx/d * rep; a.dy += dy/d * rep; b.dx -= dx/d * rep; b.dy -= dy/d * rep;
    }
    edges.forEach(function(e){
      const a = pos.get(e.source), b = pos.get(e.target);
      if (!a || !b) return;
      let dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy) || 0.01;
      const att = d * d / k * (1 + Math.log(1 + e.weight)) * 0.55;
      a.dx -= dx/d * att; a.dy -= dy/d * att; b.dx += dx/d * att; b.dy += dy/d * att;
    });
    pos.forEach(function(p){
      const d = Math.hypot(p.dx, p.dy) || 0.01;
      p.x += p.dx/d * Math.min(d, temp); p.y += p.dy/d * Math.min(d, temp);
      p.x = Math.max(26, Math.min(W - 26, p.x)); p.y = Math.max(26, Math.min(H - 26, p.y));
    });
    temp *= 0.965;
  }
  return pos;
}
function networkChart(net){
  const W = 720, H = 460;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H, style: "max-height:520px"});
  if (!net.nodes.length){ const t = s("text", {x: W/2, y: H/2, "text-anchor": "middle", class: "vlab"}); t.textContent = "sem coautoria registrada"; svg.appendChild(t); return svg; }
  const pos = forceLayout(net.nodes, net.edges, W, H, 380);
  const maxW = Math.max.apply(null, net.edges.map(function(e){ return e.weight; }).concat([1]));
  const maxA = Math.max.apply(null, net.nodes.map(function(n){ return n.articles; }).concat([1]));
  const gEdges = s("g"); svg.appendChild(gEdges);
  net.edges.forEach(function(e){
    const a = pos.get(e.source), b = pos.get(e.target);
    if (!a || !b) return;
    gEdges.appendChild(s("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y,
      stroke: css("--border"), "stroke-width": 0.8 + 3.2 * e.weight / maxW, "stroke-opacity": 0.85}));
  });
  net.nodes.forEach(function(n){
    const p = pos.get(n.id);
    const r = 7 + 15 * Math.sqrt(n.articles / maxA);
    const g = s("g");
    const circle = s("circle", {cx: p.x, cy: p.y, r: r, class: "bar",
      fill: n.is_external ? css("--c3") : css("--c1"), "fill-opacity": 0.85,
      stroke: css("--surface"), "stroke-width": 2});
    tipOn(circle, "<b>" + n.full_name + "</b>" + n.articles + " artigo(s) · " +
      n.degree + " coautor(es)" + (n.role ? "<br>" + n.role : ""));
    g.appendChild(circle);
    const label = s("text", {x: p.x, y: p.y + r + 12, "text-anchor": "middle", class: "vlab"});
    label.textContent = truncate(n.name, 16); g.appendChild(label);
    svg.appendChild(g);
  });
  return svg;
}
function mapChart(places){
  const pts = places.filter(function(p){ return p.latitude !== null && p.longitude !== null; });
  const W = 640, H = 380, pad = 46;
  const svg = s("svg", {viewBox: "0 0 " + W + " " + H});
  if (!pts.length){ const t = s("text", {x: W/2, y: H/2, "text-anchor": "middle", class: "vlab"});
    t.textContent = "sem coordenadas cadastradas"; svg.appendChild(t); return svg; }
  let latMin = Math.min.apply(null, pts.map(function(p){ return p.latitude; }));
  let latMax = Math.max.apply(null, pts.map(function(p){ return p.latitude; }));
  let lonMin = Math.min.apply(null, pts.map(function(p){ return p.longitude; }));
  let lonMax = Math.max.apply(null, pts.map(function(p){ return p.longitude; }));
  const spanLat = Math.max(latMax - latMin, 1.5), spanLon = Math.max(lonMax - lonMin, 1.5);
  latMin -= spanLat * 0.18; latMax += spanLat * 0.18;
  lonMin -= spanLon * 0.18; lonMax += spanLon * 0.18;
  const X = function(lon){ return pad + (lon - lonMin) / (lonMax - lonMin) * (W - 2 * pad); };
  const Y = function(lat){ return pad + (latMax - lat) / (latMax - latMin) * (H - 2 * pad); };
  const grid = s("g"); svg.appendChild(grid);
  for (let i = 0; i <= 4; i++){
    const lat = latMin + (latMax - latMin) * i / 4, lon = lonMin + (lonMax - lonMin) * i / 4;
    grid.appendChild(s("line", {x1: pad, x2: W - pad, y1: Y(lat), y2: Y(lat), class: "gl"}));
    grid.appendChild(s("line", {y1: pad, y2: H - pad, x1: X(lon), x2: X(lon), class: "gl"}));
    const ty = s("text", {x: pad - 6, y: Y(lat) + 3, "text-anchor": "end", class: "vlab"});
    ty.textContent = lat.toFixed(1) + "°"; grid.appendChild(ty);
    const tx = s("text", {x: X(lon), y: H - pad + 15, "text-anchor": "middle", class: "vlab"});
    tx.textContent = lon.toFixed(1) + "°"; grid.appendChild(tx);
  }
  if (D.geo && D.geo.length){
    const gg = s("g"); svg.appendChild(gg);
    D.geo.forEach(function(ring){
      const dpath = ring.map(function(pt, i){ return (i ? "L" : "M") + X(pt[0]) + " " + Y(pt[1]); }).join(" ");
      gg.appendChild(s("path", {d: dpath + "Z", fill: css("--surface-2"), "fill-opacity": 0.7,
        stroke: css("--border"), "stroke-width": 1}));
    });
  }
  const maxN = Math.max.apply(null, pts.map(function(p){ return p.n_events; }).concat([1]));
  pts.forEach(function(p){
    const r = 6 + 16 * Math.sqrt(p.n_events / maxN);
    const c = s("circle", {cx: X(p.longitude), cy: Y(p.latitude), r: r, fill: css("--c1"),
      "fill-opacity": 0.55, stroke: css("--c1"), "stroke-width": 1.5, class: "bar"});
    tipOn(c, "<b>" + p.city + (p.state ? " / " + p.state : "") + "</b>" + p.n_events + " atividade(s)");
    svg.appendChild(c);
    const t = s("text", {x: X(p.longitude), y: Y(p.latitude) - r - 5, "text-anchor": "middle", class: "vlab"});
    t.textContent = p.city; svg.appendChild(t);
  });
  return svg;
}
function statBox(label, stat){
  if (!stat || !stat.n) return card(label, "Sem dados suficientes.", h("div", {class: "empty", text: "—"}));
  return card(label, stat.n + " artigo(s) com as duas datas registradas", [
    h("div", {class: "grid g3"}, [
      kpi("Mediana", dur(stat.median)), kpi("Média", dur(stat.mean)),
      kpi("Mín – Máx", dur(stat.min) + " – " + dur(stat.max))
    ]),
    h("div", {class: "hint", style: "margin-top:12px",
      text: "Intervalo interquartil: " + dur(stat.p25) + " a " + dur(stat.p75) + " · desvio-padrão " + dur(stat.sd)})
  ]);
}

/* ---------- secoes ---------- */
function renderOverview(){
  const o = D.overview;
  document.getElementById("labName").textContent = o.lab_name;
  document.getElementById("labMeta").innerHTML =
    '<span class="pill">' + o.institution + "</span>" +
    '<span class="pill">Atualizado em ' + o.generated_at + "</span>" +
    '<span class="pill">Janela de análise: ' + o.window + " anos</span>";
  document.getElementById("foot").textContent =
    "Painel gerado automaticamente a partir do banco de dados do LAPE em " + o.generated_at +
    ". Fontes: planilhas do laboratório, Currículo Lattes, Scopus e Web of Science.";

  const body = section("visao-geral", "Visão geral", null,
    "Retrato do laboratório na data de geração deste painel.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Artigos no banco", o.n_articles, o.n_research_lines + " linhas de pesquisa", true),
    kpi("Em produção", o.n_in_progress, "manuscritos em escrita"),
    kpi("Submetidos", o.n_submitted, "aguardando parecer"),
    kpi("Publicados", o.n_published, o.published_window + " nos últimos " + o.window + " anos"),
    kpi("Média/ano", dec(o.mean_per_year, 2), "publicações por ano (" + o.window + " anos)"),
    kpi("Integrantes", o.n_members, o.n_collaborators + " colaboradores externos"),
    kpi("Citações Scopus", o.scopus_total, "WoS: " + o.wos_total),
    kpi("Atividades", o.n_events, "reuniões, coletas, eventos")
  ]));
  const statusItems = o.status_counts.map(function(d, i){
    return {label: STATUS_LABEL[d.status] || d.status, value: d.n, color: color(i)};
  });
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Situação dos artigos", "Distribuição por etapa do ciclo editorial.",
      [donut(statusItems), legend(statusItems)]),
    card("Publicações por ano", "Últimos " + o.window + " anos.",
      barChart(D.publications.series.map(function(d){
        return {label: d.year, value: d.n_articles};
      }), {tipLabel: ": ", color: css("--c2")}))
  ]));
}

function renderLines(){
  const rows = D.research_lines;
  const body = section("linhas", "Índice de linhas de pesquisa", rows.length,
    "Cada linha reúne artigos, integrantes e atividades. Cadastre as linhas na aba "
    + "“Linhas de Pesquisa” e use o mesmo nome nas demais planilhas.");
  if (!rows.length){
    body.appendChild(h("div", {class: "note", html:
      "<b>Nenhuma linha de pesquisa cadastrada ainda.</b> Preencha a aba “Linhas de Pesquisa” "
      + "em <span class='mono'>data/raw/LAPE_cadastros.xlsx</span> e rode o pipeline novamente."}));
  }
  body.appendChild(h("div", {class: "grid g3"}, rows.map(function(line, i){
    return h("div", {class: "card"}, [
      h("h3", {text: line.name}),
      h("div", {class: "hint", text: line.description || (line.coordinator ? "Coordenação: " + line.coordinator : "—")}),
      h("div", {class: "grid g3", style: "gap:8px"}, [
        kpi("Artigos", line.n_articles), kpi("Publicados", line.n_published),
        kpi("Integrantes", line.n_members)
      ]),
      line.keywords ? h("div", {class: "hint", style: "margin-top:10px", text: line.keywords}) : null
    ]);
  })));
  if (rows.length) body.appendChild(h("div", {style: "margin-top:14px"}, table([
    {k: "name", label: "Linha", wide: true},
    {k: "coordinator", label: "Coordenação"},
    {k: "n_articles", label: "Artigos", num: true},
    {k: "n_in_progress", label: "Em produção", num: true},
    {k: "n_submitted", label: "Submetidos", num: true},
    {k: "n_published", label: "Publicados", num: true},
    {k: "n_members", label: "Integrantes", num: true},
    {k: "n_events", label: "Atividades", num: true}
  ], rows)));
}

function progressBar(row){
  const wrap = h("span", {class: "prog"});
  const done = row.versions_done || 0;
  for (let i = 0; i < 5; i++) wrap.appendChild(h("i", {class: i < done ? "on" : null}));
  if (row.submission_attempts) wrap.appendChild(h("i", {class: "sub"}));
  return wrap;
}

function renderInProgress(){
  const rows = D.in_progress;
  const body = section("producao", "Artigos em produção", rows.length,
    "Manuscritos em escrita, com data de início, equipe e progresso de versões.");
  body.appendChild(table([
    {k: "internal_code", label: "ID"},
    {k: "title", label: "Título", wide: true, render: function(r){
      return h("div", {}, [r.title, r.research_line ? h("small", {text: r.research_line}) : null]);
    }},
    {k: "authors", label: "Autores", render: function(r){ return truncate(r.authors, 60); }},
    {k: "started_on", label: "Início", render: function(r){ return dt(r.started_on); }},
    {k: "days_open", label: "Em aberto", num: true, render: function(r){ return dur(r.days_open); }},
    {label: "Versões", render: progressBar},
    {label: "Situação", render: function(r){ return badge(r.status); }}
  ], rows, "Nenhum artigo em produção registrado."));
  const byLead = {};
  rows.forEach(function(r){
    const a = (r.authors || "").split(";")[0].trim() || "—";
    byLead[a] = (byLead[a] || 0) + 1;
  });
  const items = Object.keys(byLead).map(function(k){ return {label: k, value: byLead[k]}; })
    .sort(function(a, b){ return b.value - a.value; });
  if (items.length) body.appendChild(h("div", {style: "margin-top:14px"},
    card("Carga por responsável", "Artigos em produção sob responsabilidade de cada integrante.",
      hbarChart(items, {tipLabel: ": ", color: css("--c1")}))));
}

function renderSubmitted(){
  const rows = D.submitted;
  const body = section("submetidos", "Artigos submetidos", rows.length,
    "Manuscritos sob avaliação, com a revista e a data da submissão corrente.");
  body.appendChild(table([
    {k: "internal_code", label: "ID"},
    {k: "title", label: "Título", wide: true},
    {k: "authors", label: "Autores", render: function(r){ return truncate(r.authors, 55); }},
    {k: "current_journal", label: "Revista atual"},
    {k: "last_submitted_on", label: "Submissão", render: function(r){ return dt(r.last_submitted_on || r.first_submission_on); }},
    {k: "submission_attempts", label: "Tentativas", num: true},
    {label: "Em avaliação há", num: true, render: function(r){
      const d = r.last_submitted_on || r.first_submission_on;
      if (!d) return "—";
      return dur((Date.now() - new Date(d + "T00:00:00").getTime()) / 86400000);
    }}
  ], rows, "Nenhum artigo submetido registrado."));
}

function renderPublications(){
  const p = D.publications;
  const body = section("publicacoes", "Publicações por ano", p.total_all_time,
    "Estudos publicados nos últimos " + p.window + " anos, com total e média anual.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Total no período", p.total_window, "últimos " + p.window + " anos", true),
    kpi("Média por ano", dec(p.mean_per_year, 2), "artigos/ano"),
    kpi("Total histórico", p.total_all_time, "todos os anos"),
    kpi("Melhor ano", (function(){
      const best = p.series.slice().sort(function(a, b){ return b.n_articles - a.n_articles; })[0];
      return best && best.n_articles ? best.year : "—";
    })(), "no período analisado")
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Publicações por ano (janela de " + p.window + " anos)", null,
      barChart(p.series.map(function(d){ return {label: d.year, value: d.n_articles}; }),
        {tipLabel: ": ", color: css("--c2")})),
    card("Série histórica completa", "Todos os anos com publicações registradas.",
      barChart(p.full_series.map(function(d){ return {label: d.year, value: d.n_articles}; }),
        {tipLabel: ": ", color: css("--c1")}))
  ]));
  if (!p.total_all_time) body.appendChild(h("div", {class: "note", style: "margin-top:14px", html:
    "<b>Sem publicações no banco.</b> Importe o XML do Currículo Lattes "
    + "(<span class='mono'>data/raw/lattes_*.zip</span>) ou preencha a aba “Publicações” "
    + "de <span class='mono'>LAPE_cadastros.xlsx</span>."}));
}

function citationTable(rows){
  return table([
    {k: "title", label: "Título", wide: true, render: function(r){
      return h("div", {}, [
        r.url || r.doi ? h("a", {href: r.url || ("https://doi.org/" + r.doi), target: "_blank",
          rel: "noopener", text: r.title}) : r.title,
        h("small", {text: [r.journal, r.year_published].filter(Boolean).join(" · ")})
      ]);
    }},
    {k: "authors", label: "Autores", render: function(r){ return truncate(r.authors, 45); }},
    {k: "year_published", label: "Ano", num: true},
    {k: "citations", label: "Citações", num: true},
    {label: "WoS / Scopus / OpenAlex", num: true, render: function(r){
      return num(r.wos_citations) + " / " + num(r.scopus_citations)
        + " / " + num(r.openalex_citations); }}
  ], rows, "Sem citações coletadas. Configure SCOPUS_API_KEY / WOS_API_KEY ou preencha as colunas de citações na planilha.");
}

function renderCitations(){
  const body = section("citacoes", "Artigos mais citados", null,
    "Ranking por base. Os valores são atualizados automaticamente pelo DOI quando as chaves de API estão configuradas.");
  body.appendChild(tabs([
    {label: "Scopus — geral", content: citationTable(D.most_cited_scopus)},
    {label: "Scopus — últimos " + D.overview.window + " anos", content: citationTable(D.most_cited_scopus_recent)},
    {label: "Web of Science — geral", content: citationTable(D.most_cited_wos)},
    {label: "WoS — últimos " + D.overview.window + " anos", content: citationTable(D.most_cited_wos_recent)},
    {label: "OpenAlex — geral", content: citationTable(D.most_cited_openalex)},
    {label: "OpenAlex — últimos " + D.overview.window + " anos", content: citationTable(D.most_cited_openalex_recent)}
  ]));
  body.appendChild(h("div", {class: "note", style: "margin-top:14px", html:
    "<b>OpenAlex</b> é uma base aberta e não exige chave de API — por isso serve de "
    + "referência imediata de impacto enquanto Scopus e Web of Science não estiverem configurados."}));
}

function renderMembers(){
  const rows = D.members;
  const body = section("equipe", "Artigos por integrante", rows.length,
    "Número de artigos em que cada integrante está envolvido, por etapa.");
  const items = rows.filter(function(r){ return r.n_articles > 0; }).slice(0, 25).map(function(r){
    return {label: r.short_name || r.full_name, value: r.n_articles,
      color: r.is_external ? css("--c3") : css("--c1"),
      note: r.n_published + " publicado(s) · " + r.n_in_progress + " em produção"};
  });
  body.appendChild(card("Envolvimento em artigos", "Barras laranja indicam colaboradores externos.",
    [hbarChart(items, {tipLabel: ": ", labelWidth: 160}),
     legend([{label: "Integrante do LAPE", color: css("--c1")},
             {label: "Colaborador externo", color: css("--c3")}])]));
  body.appendChild(h("div", {style: "margin-top:14px"}, table([
    {k: "full_name", label: "Integrante", wide: true, render: function(r){
      return h("div", {}, [r.full_name, r.role || r.research_line
        ? h("small", {text: [r.role, r.research_line].filter(Boolean).join(" · ")}) : null]);
    }},
    {k: "n_articles", label: "Artigos", num: true},
    {k: "n_in_progress", label: "Em produção", num: true},
    {k: "n_submitted", label: "Submetidos", num: true},
    {k: "n_published", label: "Publicados", num: true},
    {k: "n_first_author", label: "1º autor", num: true},
    {k: "n_events", label: "Atividades", num: true},
    {k: "scopus_citations", label: "Citações Scopus", num: true}
  ], rows)));
}

function renderNetwork(){
  const net = D.network;
  const body = section("rede", "Rede de colaboração", net.n_nodes + " pessoas",
    "Cada nó é um integrante; a espessura da linha é o número de artigos em coautoria.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Pessoas na rede", net.n_nodes, "com ao menos um artigo"),
    kpi("Pares em coautoria", net.n_edges, "ligações distintas"),
    kpi("Densidade", dec(net.density, 3), "0 = isolados, 1 = todos com todos"),
    kpi("Grau médio", dec(net.mean_degree, 2), "coautores por pessoa")
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"},
    card(null, null, networkChart(net))));
  if (net.top_pairs.length) body.appendChild(h("div", {style: "margin-top:14px"},
    card("Duplas mais produtivas", "Pares com maior número de artigos em comum.",
      hbarChart(net.top_pairs.map(function(p){
        return {label: p.a + " + " + p.b, value: p.weight};
      }), {tipLabel: ": ", labelWidth: 210, labelChars: 30, color: css("--c4")}))));
}

function renderTimes(){
  const t = D.timeline;
  const body = section("tempos", "Tempos do ciclo editorial", null,
    "Quanto tempo cada etapa leva, do início do artigo até a publicação.");
  body.appendChild(h("div", {class: "grid g3"}, [
    statBox("Início → publicação", t.start_to_publication),
    statBox("Submissão → aceite", t.submission_to_acceptance),
    statBox("Aceite → publicação", t.acceptance_to_publication)
  ]));
  const hist = t.histogram_start_to_publication.filter(function(d){ return d.n; });
  if (hist.length) body.appendChild(h("div", {style: "margin-top:14px"},
    card("Distribuição do tempo início → publicação", null,
      barChart(hist.map(function(d){ return {label: d.label, value: d.n}; }),
        {tipLabel: ": ", color: css("--c5")}))));
  if (t.articles.length) body.appendChild(h("div", {style: "margin-top:14px"}, table([
    {k: "title", label: "Artigo", wide: true},
    {k: "journal", label: "Revista"},
    {k: "started_on", label: "Início", render: function(r){ return dt(r.started_on); }},
    {k: "first_submission_on", label: "1ª submissão", render: function(r){ return dt(r.first_submission_on); }},
    {k: "accepted_on", label: "Aceite", render: function(r){ return dt(r.accepted_on); }},
    {k: "published_on", label: "Publicação", render: function(r){ return dt(r.published_on); }},
    {label: "Início→pub.", num: true, render: function(r){ return dur(r.days_start_to_publication); }},
    {k: "submission_attempts", label: "Tentativas", num: true}
  ], t.articles, "Nenhum artigo publicado ou aceito com datas completas.")));
}

function renderSubmissions(){
  const sub = D.submissions;
  const body = section("submissoes", "Submissões, tentativas e recusas", sub.total,
    "Histórico de envios: quantas tentativas cada artigo exigiu, quanto tempo entre elas e por que foi recusado.");
  body.appendChild(h("div", {class: "grid g4"}, [
    kpi("Submissões", sub.total, "tentativas registradas", true),
    kpi("Taxa de aceite", dec(sub.acceptance_rate, 1) + "%", sub.accepted + " aceite(s)"),
    kpi("Taxa de recusa", dec(sub.rejection_rate, 1) + "%", sub.rejected + " recusa(s)"),
    kpi("Desk rejections", sub.desk_rejects, "recusadas sem revisão")
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Tentativas por artigo", "Quantos envios cada manuscrito exigiu.",
      barChart(sub.attempts_distribution.map(function(d){
        return {label: d.attempts + "×", value: d.n};
      }), {tipLabel: " artigos: ", color: css("--c1")})),
    card("Decisões editoriais", null,
      barChart(sub.decisions.map(function(d, i){
        return {label: DECISION_LABEL[d.decision] || d.decision, value: d.n, color: color(i)};
      }), {tipLabel: ": ", height: 220}))
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    statBox("Intervalo entre submissões", sub.gap_summary),
    statBox("Decisão → nova submissão", sub.decision_to_resubmission)
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Motivos das recusas", "Catálogo alimentado pela coluna “Motivo/observação” das tentativas.",
    sub.rejection_reasons.length
      ? hbarChart(sub.rejection_reasons.map(function(r){
          return {label: r.reason, value: r.n, note: r.category};
        }), {tipLabel: ": ", labelWidth: 230, labelChars: 34, color: css("--c6")})
      : h("div", {class: "empty", text: "Nenhuma recusa com motivo registrado."})
  )));
  body.appendChild(h("div", {style: "margin-top:14px"}, table([
    {k: "title", label: "Artigo", wide: true},
    {k: "attempts", label: "Tentativas", num: true},
    {k: "rejections", label: "Recusas", num: true},
    {k: "first_submitted_on", label: "1ª submissão", render: function(r){ return dt(r.first_submitted_on); }},
    {k: "last_submitted_on", label: "Última submissão", render: function(r){ return dt(r.last_submitted_on); }},
    {label: "Situação", render: function(r){ return badge(r.status); }}
  ], sub.per_article, "Nenhuma submissão registrada.")));
  if (sub.gaps.length) body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Intervalos entre uma submissão e a ressubmissão", null,
    table([
      {k: "title", label: "Artigo", wide: true},
      {k: "attempt_no", label: "Tentativa", num: true},
      {k: "previous_submitted_on", label: "Submissão anterior", render: function(r){ return dt(r.previous_submitted_on); }},
      {k: "previous_decision_on", label: "Decisão anterior", render: function(r){ return dt(r.previous_decision_on); }},
      {k: "submitted_on", label: "Nova submissão", render: function(r){ return dt(r.submitted_on); }},
      {label: "Entre submissões", num: true, render: function(r){ return dur(r.days_between_submissions); }},
      {label: "Decisão→reenvio", num: true, render: function(r){ return dur(r.days_decision_to_resubmission); }}
    ], sub.gaps)
  )));
  if (sub.per_journal.length) body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Revistas mais utilizadas", null,
    table([
      {k: "journal", label: "Revista", wide: true},
      {k: "n", label: "Submissões", num: true},
      {k: "accepted", label: "Aceitas", num: true},
      {k: "rejected", label: "Recusadas", num: true}
    ], sub.per_journal)
  )));
}

function renderAcceptances(){
  const rows = D.acceptances;
  const body = section("aceites", "Datas de aceite", rows.length,
    "Aceites registrados, com o tempo decorrido desde a primeira submissão.");
  body.appendChild(table([
    {k: "title", label: "Artigo", wide: true},
    {k: "authors", label: "Autores", render: function(r){ return truncate(r.authors, 45); }},
    {k: "journal", label: "Revista"},
    {k: "first_submission_on", label: "1ª submissão", render: function(r){ return dt(r.first_submission_on); }},
    {k: "accepted_on", label: "Aceite", render: function(r){ return dt(r.accepted_on); }},
    {k: "published_on", label: "Publicação", render: function(r){ return dt(r.published_on); }},
    {label: "Submissão→aceite", num: true, render: function(r){ return dur(r.days_submission_to_acceptance); }},
    {k: "submission_attempts", label: "Tentativas", num: true}
  ], rows, "Nenhum aceite registrado ainda."));
}

function renderCalendar(){
  const ag = D.agenda;
  const body = section("calendario", "Calendário e atividades", ag.total,
    "Reuniões, coletas, defesas e eventos científicos do laboratório.");
  const state = {ref: new Date()};
  const calCard = h("div", {class: "card"});
  const byDay = {};
  ag.events.forEach(function(e){
    const key = String(e.start_at).slice(0, 10);
    (byDay[key] = byDay[key] || []).push(e);
  });
  function drawCal(){
    calCard.innerHTML = "";
    const y = state.ref.getFullYear(), m = state.ref.getMonth();
    const head = h("div", {class: "calhead"}, [
      h("button", {text: "‹", title: "Mês anterior", onclick: function(){
        state.ref = new Date(y, m - 1, 1); drawCal(); }}),
      h("h3", {text: MONTHS[m].toUpperCase() + " " + y}),
      h("button", {text: "›", title: "Próximo mês", onclick: function(){
        state.ref = new Date(y, m + 1, 1); drawCal(); }})
    ]);
    const grid = h("div", {class: "cal"});
    DOW.forEach(function(d){ grid.appendChild(h("div", {class: "dow", text: d})); });
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
      const cell = h("div", {class: "day" + (evts.length ? " has" : "") + (isToday ? " today" : "")}, [
        String(d), evts.length ? h("em", {text: "●".repeat(Math.min(evts.length, 3))}) : null
      ]);
      if (evts.length) tipOn(cell, "<b>" + dt(key) + "</b>" + evts.map(function(e){
        return (KIND_LABEL[e.kind] || e.kind) + ": " + e.title; }).join("<br>"));
      grid.appendChild(cell);
    }
    calCard.appendChild(head); calCard.appendChild(grid);
  }
  drawCal();
  const agendaList = h("ul", {class: "agenda"}, ag.upcoming.map(function(e){
    const iso = String(e.start_at);
    return h("li", {}, [
      h("div", {class: "when"}, [h("b", {text: iso.slice(8, 10)}), MONTHS[Number(iso.slice(5, 7)) - 1]]),
      h("div", {class: "what"}, [
        e.title,
        h("small", {text: [KIND_LABEL[e.kind] || e.kind, dtm(e.start_at),
          e.location_name || e.city, e.n_participants ? e.n_participants + " participantes" : null]
          .filter(Boolean).join(" · ")})
      ])
    ]);
  }));
  body.appendChild(h("div", {class: "grid g2"}, [
    calCard,
    card("Próximas atividades", ag.upcoming.length ? null : "Nenhuma atividade futura cadastrada.",
      ag.upcoming.length ? agendaList : h("div", {class: "empty", text: "Cadastre reuniões e eventos na aba “Eventos”."}))
  ]));
  body.appendChild(h("div", {class: "grid g2", style: "margin-top:14px"}, [
    card("Atividades por tipo", null, hbarChart(ag.by_kind.map(function(d, i){
      return {label: KIND_LABEL[d.kind] || d.kind, value: d.n, color: color(i)};
    }), {tipLabel: ": ", labelWidth: 140})),
    card("Atividades por ano", null, barChart(ag.by_year.map(function(d){
      return {label: d.year, value: d.n};
    }), {tipLabel: ": ", color: css("--c4")}))
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
      heatGrid(t.years, t.months, t.activities, "atividade(s)"))}
  ]));
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
      {k: "n_events", label: "Atividades", num: true}
    ], sp.places, "Nenhum local registrado."))
  ]));
  body.appendChild(h("div", {style: "margin-top:14px"}, card(
    "Instituições", "Vínculos institucionais dos integrantes e colaboradores.",
    table([
      {k: "name", label: "Instituição", wide: true, render: function(r){
        return h("div", {}, [r.name, h("small", {text: [r.city, r.state, r.country].filter(Boolean).join(" · ")})]);
      }},
      {k: "acronym", label: "Sigla"},
      {k: "n_members", label: "Integrantes", num: true},
      {k: "n_articles", label: "Artigos", num: true}
    ], sp.institutions, "Nenhuma instituição cadastrada.")
  )));
}

function renderDiscoveries(){
  const rows = D.discoveries || [];
  const body = section("descobertas", "Achados do rastreador", rows.length,
    "Publicações encontradas nas bases externas que ainda não estão no banco. "
    + "Cada uma precisa ser aprovada antes de entrar nos indicadores.");
  if (!rows.length){
    body.appendChild(h("div", {class: "note", html:
      "<b>Nenhum achado pendente.</b> Rode o agente rastreador para procurar produção nova: "
      + "<span class='mono'>python3 scripts/lape_agent.py rastreador descobrir</span>"}));
    return;
  }
  body.appendChild(h("div", {class: "note", html:
    "Para aprovar: <span class='mono'>python3 scripts/lape_agent.py revisar --aceitar "
    + rows[0].id + "</span> · para descartar, troque por <span class='mono'>--ignorar</span>."}));
  body.appendChild(table([
    {k: "id", label: "ID", num: true},
    {k: "title", label: "Título", wide: true, render: function(r){
      return h("div", {}, [
        r.url ? h("a", {href: r.url, target: "_blank", rel: "noopener", text: r.title}) : r.title,
        h("small", {text: [r.journal, r.authors ? truncate(r.authors, 70) : null]
          .filter(Boolean).join(" · ")})
      ]);
    }},
    {k: "year", label: "Ano", num: true},
    {k: "citations", label: "Citações", num: true},
    {k: "source", label: "Fonte"},
    {k: "found_at", label: "Encontrado em", render: function(r){ return dtm(r.found_at); }}
  ], rows));
}

function renderQuality(){
  const q = D.quality;
  const body = section("qualidade", "Qualidade dos dados", null,
    "Lacunas que limitam as análises. Cada item corresponde a um campo a preencher nas planilhas.");
  body.appendChild(h("div", {class: "grid g2"}, [
    card("Campos a completar", "Quanto menor, mais completo o banco.",
      h("ul", {class: "issues"}, q.issues.map(function(item){
        return h("li", {}, [item.label,
          h("span", {class: "n " + (item.n ? "some" : "zero"), text: item.n})]);
      }))),
    card("Últimas cargas", "Registro de cada leitura de arquivo e chamada de API.",
      table([
        {k: "run_at", label: "Quando", render: function(r){ return dtm(r.run_at); }},
        {k: "source", label: "Fonte"},
        {k: "target", label: "Destino"},
        {k: "rows_read", label: "Lidas", num: true},
        {k: "rows_written", label: "Gravadas", num: true},
        {k: "status", label: "Status"}
      ], q.last_runs, "Sem execuções registradas."))
  ]));
}

/* ---------- boot ---------- */
function boot(){
  renderOverview(); renderLines(); renderInProgress(); renderSubmitted();
  renderPublications(); renderCitations(); renderMembers(); renderNetwork();
  renderTimes(); renderSubmissions(); renderAcceptances();
  renderCalendar(); renderTemporal(); renderSpatial();
  renderDiscoveries(); renderQuality();

  const links = Array.prototype.slice.call(document.querySelectorAll("nav a"));
  const observer = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if (!entry.isIntersecting) return;
      links.forEach(function(a){
        a.classList.toggle("active", a.getAttribute("href") === "#" + entry.target.id);
      });
    });
  }, {rootMargin: "-15% 0px -75% 0px"});
  document.querySelectorAll("section").forEach(function(sec){ observer.observe(sec); });

  const toggle = document.getElementById("themeToggle");
  let stored = null;
  try { stored = localStorage.getItem("lape-theme"); } catch (e) {}
  if (stored) document.documentElement.setAttribute("data-theme", stored);
  toggle.addEventListener("click", function(){
    const dark = document.documentElement.getAttribute("data-theme") === "dark"
      || (!document.documentElement.getAttribute("data-theme")
          && matchMedia("(prefers-color-scheme:dark)").matches);
    const next = dark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("lape-theme", next); } catch (e) {}
    location.reload();
  });
}
boot();
