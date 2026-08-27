/* ==========================================================================
   LAPE — painel de indicadores
   Navegação por abas: cada aba é plotada quando você entra nela, sempre
   contra o recorte atual dos filtros. Servido pela API, o painel reconfere
   os dados sozinho e redesenha sem piscar. Exportado como arquivo único,
   tudo continua funcionando — inclusive o explorador, que então calcula
   as agregações no próprio navegador.
   ========================================================================== */
"use strict";

let D = JSON.parse(document.getElementById("payload").textContent);
const LIVE = !!(D.session && D.session.live);
const USER = (D.session && D.session.user) || null;
const C = Charts;
const el = C.el;

const STATUS_LABEL = {
  em_producao: "Em produção", submetido: "Submetido", em_revisao: "Em revisão",
  aceito: "Aceito", publicado: "Publicado", rejeitado: "Rejeitado", arquivado: "Arquivado",
};
const STATUS_ORDER = ["em_producao", "submetido", "em_revisao", "aceito", "publicado",
  "rejeitado", "arquivado"];
const DECISION_LABEL = {
  em_avaliacao: "Em avaliação", revisao_solicitada: "Revisão solicitada", aceito: "Aceito",
  rejeitado: "Rejeitado", desk_reject: "Recusa sem revisão", retirado: "Retirado",
  sem_registro: "Sem registro",
};
const KIND_LABEL = {
  reuniao: "Reunião", coleta: "Coleta de dados", defesa: "Defesa", qualificacao: "Qualificação",
  congresso: "Congresso", curso: "Curso/oficina", seminario: "Seminário",
  visita_tecnica: "Visita técnica", extensao: "Extensão", outro: "Outro",
};
const PROJECT_LABEL = {
  em_andamento: "Em andamento", planejado: "Planejado", concluido: "Concluído", suspenso: "Suspenso",
};
const DOW = ["D", "S", "T", "Q", "Q", "S", "S"];

const STATE = { linha: "", ano: "", integrante: "", status: "", busca: "", segmento: "status" };
/* Toda dimensão que o explorador sabe recortar aparece aqui: o seletor
   "Segmentar por" é a porta de entrada de quem não vai abrir o explorador,
   e não faz sentido que ele conheça menos cortes do que o motor. */
const SEGMENTOS = [
  { id: "status", label: "Situação" },
  { id: "linha", label: "Linha de pesquisa" },
  { id: "ano", label: "Ano (início ou publicação)" },
  { id: "ano_publicacao", label: "Ano de publicação" },
  { id: "responsavel", label: "Responsável" },
  { id: "periodico", label: "Periódico" },
  { id: "tipo_estudo", label: "Tipo de estudo" },
  { id: "qualis", label: "Estrato Qualis" },
  { id: "idioma", label: "Idioma" },
  { id: "fonte", label: "Origem do registro" },
];

/* ---------------------------------------------------------------- texto */
function dt(iso) {
  if (!iso) return "—";
  const p = String(iso).slice(0, 10).split("-");
  return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : String(iso);
}
function dtm(iso) {
  if (!iso) return "—";
  const str = String(iso);
  return str.length > 10 ? dt(str) + " · " + str.slice(11, 16) : dt(str);
}
function dur(days) {
  if (days === null || days === undefined) return "—";
  const d = Math.round(days);
  if (Math.abs(d) < 45) return d + " d";
  if (Math.abs(d) < 730) return (d / 30.44).toFixed(1).replace(".", ",") + " meses";
  return (d / 365.25).toFixed(1).replace(".", ",") + " anos";
}
function dec(v, n) {
  return (v === null || v === undefined) ? "—"
    : Number(v).toFixed(n === undefined ? 1 : n).replace(".", ",");
}
function cut(text, n) {
  if (!text) return "—";
  return text.length > n ? text.slice(0, n - 1) + "…" : text;
}
function daysSince(iso) {
  if (!iso) return null;
  return (Date.now() - new Date(String(iso).slice(0, 10) + "T00:00:00").getTime()) / 86400000;
}
function badge(status) {
  const node = el("span", { class: "badge s-" + String(status || "").replace("em_", "") });
  node.appendChild(el("span", { class: "dot" }));
  node.appendChild(document.createTextNode(STATUS_LABEL[status] || status || "—"));
  return node;
}
function bestCitations(a) {
  return Math.max(a.openalex_citations || 0, a.scopus_citations || 0, a.wos_citations || 0);
}
function median(values) {
  const data = values.filter(function (v) { return v !== null && v !== undefined; })
    .map(Number).sort(function (a, b) { return a - b; });
  if (!data.length) return null;
  const mid = Math.floor(data.length / 2);
  return data.length % 2 ? data[mid] : (data[mid - 1] + data[mid]) / 2;
}
function counter(list, key) {
  const map = new Map();
  list.forEach(function (item) {
    const k = typeof key === "function" ? key(item) : item[key];
    if (k === null || k === undefined || k === "") return;
    map.set(k, (map.get(k) || 0) + 1);
  });
  return Array.from(map, function (pair) { return { label: String(pair[0]), value: pair[1] }; })
    .sort(function (a, b) { return b.value - a.value; });
}
/* nunca gerar uma nona cor: o excedente vira "Outros" */
function topN(items, n) {
  if (items.length <= n) return items;
  const head = items.slice(0, n);
  const tail = items.slice(n).reduce(function (a, b) { return a + b.value; }, 0);
  if (tail) head.push({ label: "Outros (" + (items.length - n) + ")", value: tail, muted: true });
  return head;
}

/* ------------------------------------------------------------- recortes */
const MEMBER_ARTICLES = new Map();
function indexAuthorship() {
  MEMBER_ARTICLES.clear();
  (D.authorship || []).forEach(function (link) {
    if (!MEMBER_ARTICLES.has(link.m)) MEMBER_ARTICLES.set(link.m, new Set());
    MEMBER_ARTICLES.get(link.m).add(link.a);
  });
}
indexAuthorship();

function articles() {
  const set = STATE.integrante ? MEMBER_ARTICLES.get(Number(STATE.integrante)) : null;
  return (D.articles || []).filter(function (a) {
    if (STATE.linha && a.research_line !== STATE.linha) return false;
    if (STATE.ano && String(a.year_published) !== STATE.ano) return false;
    if (STATE.status && a.status !== STATE.status) return false;
    if (set && !set.has(a.id)) return false;
    if (STATE.busca) {
      const hay = ((a.title || "") + " " + (a.authors || "") + " " + (a.journal || "")
        + " " + (a.research_line || "")).toLowerCase();
      if (!hay.includes(STATE.busca)) return false;
    }
    return true;
  });
}
function filtersActive() {
  return !!(STATE.linha || STATE.ano || STATE.integrante || STATE.status || STATE.busca);
}
function segmentOf(article) {
  return DIM_ACCESSOR[STATE.segmento] ? DIM_ACCESSOR[STATE.segmento](article)
    : (STATUS_LABEL[article.status] || article.status);
}

/* ==================================================================== */
/* explorador: as mesmas medidas e dimensões da camada ouro              */
/* ==================================================================== */
const DIM_ACCESSOR = {
  linha: function (a) { return a.research_line || "Sem linha"; },
  status: function (a) { return STATUS_LABEL[a.status] || a.status; },
  ano: function (a) { return a.year_published ? String(a.year_published)
    : (a.started_on ? String(a.started_on).slice(0, 4) : "Sem ano"); },
  ano_publicacao: function (a) { return a.year_published ? String(a.year_published) : "Sem ano"; },
  periodico: function (a) { return a.journal || "Sem periódico"; },
  qualis: function (a) { return a.qualis || "Sem Qualis"; },
  tipo_estudo: function (a) { return a.study_type || "Não informado"; },
  responsavel: function (a) {
    return a.lead_name || (a.authors || "").split(";")[0].trim() || "Sem responsável"; },
  idioma: function (a) { return a.language || "Não informado"; },
  fonte: function (a) { return a.source || "planilha"; },
};
const MEASURE_FN = {
  artigos: function (list) { return list.length; },
  publicados: function (list) {
    return list.filter(function (a) { return a.status === "publicado"; }).length; },
  submetidos: function (list) {
    return list.filter(function (a) { return a.status === "submetido" || a.status === "em_revisao"; }).length; },
  em_producao: function (list) {
    return list.filter(function (a) { return a.status === "em_producao"; }).length; },
  citacoes: function (list) {
    return list.reduce(function (acc, a) { return acc + bestCitations(a); }, 0); },
  citacoes_media: function (list) {
    return list.length ? Math.round(100 * list.reduce(function (acc, a) {
      return acc + bestCitations(a); }, 0) / list.length) / 100 : 0; },
  tentativas: function (list) {
    return list.reduce(function (acc, a) { return acc + (a.submission_attempts || 0); }, 0); },
  recusas: function (list) {
    return list.reduce(function (acc, a) { return acc + (a.rejections || 0); }, 0); },
  dias_ate_publicar: function (list) {
    const v = list.map(function (a) { return a.days_start_to_publication; })
      .filter(function (x) { return x !== null && x !== undefined; });
    return v.length ? Math.round(10 * v.reduce(function (a, b) { return a + b; }, 0) / v.length) / 10 : null; },
  dias_ate_aceite: function (list) {
    const v = list.map(function (a) { return a.days_submission_to_acceptance; })
      .filter(function (x) { return x !== null && x !== undefined; });
    return v.length ? Math.round(10 * v.reduce(function (a, b) { return a + b; }, 0) / v.length) / 10 : null; },
  autores_medio: function (list) {
    return list.length ? Math.round(100 * list.reduce(function (acc, a) {
      return acc + (a.authors ? a.authors.split(";").length : 0); }, 0) / list.length) / 100 : 0; },
};

/* Mesma resposta da rota /api/query, calculada aqui — usada na exportação
   estática e como reserva quando a rede falha. */
function localQuery(measure, by, split) {
  const rows = articles();
  const dimA = DIM_ACCESSOR[by] || DIM_ACCESSOR.linha;
  const fn = MEASURE_FN[measure] || MEASURE_FN.artigos;
  const buckets = new Map();
  rows.forEach(function (a) {
    const k1 = dimA(a);
    const k2 = split ? (DIM_ACCESSOR[split] || DIM_ACCESSOR.status)(a) : null;
    const key = k1 + " " + (k2 === null ? "" : k2);
    if (!buckets.has(key)) buckets.set(key, { dim1: k1, dim2: k2, items: [] });
    buckets.get(key).items.push(a);
  });
  const out = Array.from(buckets.values()).map(function (b) {
    const row = { dim1: b.dim1, valor: fn(b.items) };
    if (split) row.dim2 = b.dim2;
    return row;
  }).sort(function (a, b) { return (b.valor || 0) - (a.valor || 0); });
  const cat = (D.catalog && D.catalog.measures || []).find(function (m) { return m.id === measure; });
  const dimCat = (D.catalog && D.catalog.dimensions || []).find(function (m) { return m.id === by; });
  const splitCat = (D.catalog && D.catalog.dimensions || []).find(function (m) { return m.id === split; });
  return {
    measure: measure, measure_label: cat ? cat.label : measure, unit: cat ? cat.unit : "",
    by: by, by_label: dimCat ? dimCat.label : by,
    split: split, split_label: splitCat ? splitCat.label : null,
    rows: out, total: out.reduce(function (a, r) { return a + (r.valor || 0); }, 0),
    local: true,
  };
}

/* ==================================================================== */
/* peças de UI                                                           */
/* ==================================================================== */
function card(title, hint, kids) {
  return el("div", { class: "card" }, [
    title ? el("h3", { text: title }) : null,
    hint ? el("div", { class: "hint", text: hint }) : null,
    el("div", { style: title || hint ? "margin-top:14px" : null },
      Array.isArray(kids) ? kids : [kids]),
  ]);
}
/* {texto, sinal: "sobe"|"desce"|"parado", forte: "trecho em destaque"} */
function leituraDe(spec) {
  if (typeof spec === "string") spec = { texto: spec };
  const node = el("div", { class: "leitura" });
  if (spec.sinal) {
    node.appendChild(el("span", { class: "sinal " + spec.sinal,
      text: spec.sinal === "sobe" ? "▲ " : (spec.sinal === "desce" ? "▼ " : "■ ") }));
  }
  if (spec.forte) node.appendChild(el("b", { text: spec.forte + " " }));
  node.appendChild(document.createTextNode(spec.texto));
  return node;
}

function kpi(spec) {
  const node = el("div", { class: "kpi" + (spec.hero ? " hero" : "")
    + (spec.tone ? " t-" + spec.tone : "") });
  const label = el("div", { class: "label" });
  /* o ícone é decorativo: quem nomeia o indicador é o rótulo ao lado */
  if (spec.icon) label.appendChild(Icons.badge(spec.icon,
    spec.tone === "good" ? "bom" : (spec.tone === "bad" ? "critico" : null), null));
  label.appendChild(el("span", { text: spec.label }));
  node.appendChild(label);
  node.appendChild(el("div", { class: "value", text: spec.value }));
  if (spec.delta !== undefined && spec.delta !== null && spec.delta !== 0) {
    const up = spec.delta > 0;
    const good = spec.lowerIsBetter ? !up : up;
    node.appendChild(el("span", {
      class: "delta " + (good ? "up" : "down"),
      text: (up ? "▲ " : "▼ ") + dec(Math.abs(spec.delta), spec.deltaDecimals === undefined ? 0 : spec.deltaDecimals)
        + (spec.deltaNote ? " " + spec.deltaNote : ""),
    }));
  }
  if (spec.foot) node.appendChild(el("div", { class: "foot", text: spec.foot }));
  /* minigráfico só quando ele diz alguma coisa: uma linha reta em zero é ruído */
  const spark = spec.spark || [];
  if (spark.length > 1 && Math.max.apply(null, spark) > 0) {
    node.appendChild(el("div", { class: "spark" }, C.sparkline(spark, { color: spec.sparkColor })));
  }
  /* A leitura fecha o cartão. É a frase curta que diz o que o número quer
     dizer — sem ela, cada pessoa que olha o painel interpreta por conta
     própria, e cada uma interpreta de um jeito. */
  if (spec.leitura) node.appendChild(leituraDe(spec.leitura));
  return node;
}

/* Tabela dinâmica: ordena, busca, pagina e exporta. */
function dataTable(spec) {
  const cols = spec.cols;
  const all = spec.rows || [];
  if (!all.length) return el("div", { class: "tw" }, C.empty(spec.emptyMessage));
  const state = { key: spec.sortKey || null, dir: spec.sortDir || -1, page: 0,
    size: spec.pageSize || 25, term: "" };
  const wrap = el("div");
  const tableBox = el("div", { class: "tw" });
  const tbody = el("tbody");
  const foot = el("div", { class: "tfoot" });

  function filtered() {
    if (!state.term) return all;
    return all.filter(function (row) {
      return cols.some(function (c) {
        const v = c.sortValue ? c.sortValue(row) : row[c.k];
        return v !== null && v !== undefined && String(v).toLowerCase().includes(state.term);
      });
    });
  }
  function sorted(rows) {
    if (!state.key) return rows;
    const col = cols.find(function (c) { return (c.k || c.label) === state.key; });
    return rows.slice().sort(function (a, b) {
      const va = col.sortValue ? col.sortValue(a) : a[col.k];
      const vb = col.sortValue ? col.sortValue(b) : b[col.k];
      if (va === vb) return 0;
      if (va === null || va === undefined) return 1;
      if (vb === null || vb === undefined) return -1;
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * state.dir;
      return String(va).localeCompare(String(vb), "pt-BR") * state.dir;
    });
  }
  function paint() {
    const rows = sorted(filtered());
    const pages = Math.max(1, Math.ceil(rows.length / state.size));
    state.page = Math.min(state.page, pages - 1);
    const slice = rows.slice(state.page * state.size, (state.page + 1) * state.size);
    tbody.innerHTML = "";
    slice.forEach(function (row, i) {
      const tr = el("tr", spec.onRow ? { class: "clickable", tabindex: "0" } : {});
      if (spec.onRow) {
        tr.addEventListener("click", function () { spec.onRow(row); });
        tr.addEventListener("keydown", function (ev) {
          if (ev.key === "Enter") { ev.preventDefault(); spec.onRow(row); }
        });
      }
      cols.forEach(function (c) {
        const td = el("td", { class: [c.num ? "num" : "", c.wide ? "title" : ""].join(" ").trim() || null });
        const value = c.render ? c.render(row, state.page * state.size + i) : row[c.k];
        if (value instanceof Node) td.appendChild(value);
        else td.textContent = (value === null || value === undefined || value === "") ? "—" : String(value);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    foot.innerHTML = "";
    foot.appendChild(el("span", {
      text: rows.length + (rows.length === 1 ? " registro" : " registros")
        + (pages > 1 ? " · página " + (state.page + 1) + " de " + pages : ""),
    }));
    const pager = el("div", { class: "pager" });
    if (pages > 1) {
      pager.appendChild(el("button", { type: "button", text: "‹", disabled: state.page === 0,
        "aria-label": "Página anterior", onclick: function () { state.page -= 1; paint(); } }));
      pager.appendChild(el("button", { type: "button", text: "›", disabled: state.page >= pages - 1,
        "aria-label": "Próxima página", onclick: function () { state.page += 1; paint(); } }));
    }
    pager.appendChild(el("button", {
      type: "button", text: "CSV", class: "no-print",
      onclick: function () {
        C.csv((spec.file || "lape") + ".csv", cols.map(function (c) {
          return { label: c.label, get: c.sortValue || function (row) { return row[c.k]; } };
        }), rows);
      },
    }));
    foot.appendChild(pager);
  }

  const head = el("tr", {}, cols.map(function (c) {
    const key = c.k || c.label;
    const th = el("th", { class: (c.num ? "num " : "") + (c.k || c.sortValue ? "sortable" : "") });
    th.appendChild(document.createTextNode(c.label));
    const dirMark = el("span", { class: "dir", text: "" });
    th.appendChild(dirMark);
    if (c.k || c.sortValue) {
      th.addEventListener("click", function () {
        state.dir = state.key === key ? -state.dir : -1;
        state.key = key;
        head.querySelectorAll(".dir").forEach(function (x) { x.textContent = ""; });
        dirMark.textContent = state.dir === 1 ? "▲" : "▼";
        paint();
      });
    }
    return th;
  }));
  tableBox.appendChild(el("table", {}, [el("thead", {}, head), tbody]));

  if (spec.search !== false) {
    wrap.appendChild(el("div", { class: "rowbar" }, [
      spec.title ? el("h3", { text: spec.title }) : el("span"),
      el("input", { class: "search no-print", type: "search",
        placeholder: spec.searchPlaceholder || "Filtrar nesta tabela…",
        "aria-label": "Filtrar tabela",
        oninput: function (ev) { state.term = ev.target.value.toLowerCase(); state.page = 0; paint(); } }),
    ]));
  }
  wrap.appendChild(tableBox);
  wrap.appendChild(foot);
  paint();
  return wrap;
}

/* ------------------------------------------------------------- gaveta */
const DRAWER = document.getElementById("drawer");
const DRAWER_BODY = document.getElementById("drawerBody");
let lastFocus = null;
function openDrawer(title, content) {
  lastFocus = document.activeElement;
  DRAWER_BODY.innerHTML = "";
  DRAWER_BODY.appendChild(el("h3", { text: title }));
  (Array.isArray(content) ? content : [content]).forEach(function (node) {
    if (node) DRAWER_BODY.appendChild(node);
  });
  DRAWER.classList.add("on");
  document.getElementById("scrim").classList.add("on");
  document.getElementById("drawerClose").focus();
}
function closeDrawer() {
  DRAWER.classList.remove("on");
  document.getElementById("scrim").classList.remove("on");
  C.hideTip();
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}

function showResearcher(id) {
  const person = (D.researchers || []).find(function (r) { return r.id === id; });
  if (!person) return;
  const content = [
    el("div", { class: "drawer-sub", text: [person.role, person.degree, person.research_line]
      .filter(Boolean).join(" · ") || "Integrante do LAPE" }),
    el("div", { class: "grid g4", style: "margin:16px 0" }, [
      kpi({ label: "Artigos", value: C.fmt(person.n_articles) }),
      kpi({ label: "Publicados", value: C.fmt(person.n_published) }),
      kpi({ label: "Projetos", value: C.fmt(person.n_projects) }),
      kpi({ label: "Índice h", value: person.h_index === null ? "—" : C.fmt(person.h_index) }),
    ]),
  ];
  if (person.h_index_source) {
    content.push(el("p", { class: "hint", text:
      "Índice h a partir de " + (person.h_index_source === "openalex_author"
        ? "perfil público do OpenAlex (carreira completa)" : "artigos deste banco")
      + (person.metrics_updated_at ? " · atualizado em " + dt(person.metrics_updated_at) : "") }));
  }
  if (person.bio) content.push(el("p", { class: "hint", text: person.bio }));

  const contacts = [];
  if (person.email) contacts.push(el("span", { text: "E-mail: " + person.email }));
  if (person.orcid) {
    const line = el("span", { text: "ORCID: " });
    line.appendChild(el("a", { href: "https://orcid.org/" + person.orcid, target: "_blank",
      rel: "noopener", text: person.orcid }));
    contacts.push(line);
  }
  if (person.lattes_id) {
    const line = el("span", { text: "Lattes: " });
    line.appendChild(el("a", { href: "http://lattes.cnpq.br/" + person.lattes_id, target: "_blank",
      rel: "noopener", text: person.lattes_id }));
    contacts.push(line);
  }
  if (person.institution) contacts.push(el("span", { text: "Instituição: " + person.institution }));
  if (contacts.length) content.push(el("div", { class: "contacts" }, contacts));

  const own = person.articles_recent || [];
  const byStatus = counter(own, function (a) { return STATUS_LABEL[a.status] || a.status; });
  if (byStatus.length) {
    content.push(el("h4", { text: "Produção por etapa" }));
    content.push(C.bars({ items: byStatus, labelWidth: 140, unit: "artigo(s)", rowH: 24 }));
  }
  if (person.project_list && person.project_list.length) {
    content.push(el("h4", { text: "Projetos" }));
    content.push(C.table([
      { label: "Projeto", k: "name" }, { label: "Papel", k: "role" },
      { label: "Situação", get: function (r) { return PROJECT_LABEL[r.status] || r.status; } },
    ], person.project_list));
  }
  content.push(el("h4", { text: "Artigos (" + own.length + ")" }));
  content.push(dataTable({
    search: false, pageSize: 12, sortKey: "year_published",
    file: "artigos-" + (person.short_name || person.full_name),
    cols: [
      { k: "title", label: "Título", wide: true, render: function (r) {
        return el("div", {}, [cut(r.title, 68),
          el("small", { text: [r.journal, r.year_published].filter(Boolean).join(" · ") })]);
      } },
      { k: "status", label: "Situação", render: function (r) { return badge(r.status); } },
      { label: "Citações", num: true, sortValue: bestCitations,
        render: function (r) { return bestCitations(r) || "—"; } },
    ],
    rows: own, emptyMessage: "Sem artigos registrados.",
  }));
  if (person.coauthors && person.coauthors.length) {
    content.push(el("h4", { text: "Coautores mais frequentes" }));
    content.push(C.bars({
      items: person.coauthors.slice(0, 10).map(function (c) {
        return { label: c.full_name, value: c.n }; }),
      labelWidth: 160, mono: true, unit: "artigo(s) em comum", rowH: 24,
    }));
  }
  content.push(el("div", { class: "drawer-actions" }, [
    el("button", { class: "primary", type: "button", text: "Filtrar o painel por esta pessoa",
      onclick: function () {
        STATE.integrante = String(person.id);
        buildToolbar();
        closeDrawer();
        go("producao");
      } }),
  ]));
  openDrawer(person.full_name, content);
}

function showArticle(article) {
  const content = [
    el("div", { class: "drawer-sub", text: article.authors || "—" }),
    el("div", { style: "margin:12px 0;display:flex;gap:6px;flex-wrap:wrap" }, [
      badge(article.status),
      article.research_line ? el("span", { class: "badge", text: article.research_line }) : null,
      article.qualis ? el("span", { class: "badge", text: "Qualis " + article.qualis }) : null,
    ]),
    el("div", { class: "grid g4", style: "margin:14px 0" }, [
      kpi({ label: "Tentativas", value: C.fmt(article.submission_attempts || 0) }),
      kpi({ label: "Recusas", value: C.fmt(article.rejections || 0) }),
      kpi({ label: "Citações", value: bestCitations(article) || "—" }),
      kpi({ label: "Início→pub.", value: dur(article.days_start_to_publication) }),
    ]),
  ];
  const marcos = [
    ["Início", article.started_on], ["1ª submissão", article.first_submission_on],
    ["Aceite", article.accepted_on], ["Publicação", article.published_on],
  ].filter(function (p) { return p[1]; });
  if (marcos.length > 1) {
    const first = new Date(marcos[0][1]).getTime();
    content.push(el("h4", { text: "Linha do tempo do manuscrito" }));
    content.push(C.bars({
      items: marcos.map(function (m, i) {
        return { label: m[0], value: Math.round((new Date(m[1]).getTime() - first) / 86400000),
          note: dt(m[1]), color: C.ord(i) };
      }),
      labelWidth: 140, unit: "dias desde o início", rowH: 26,
      caption: "Dias decorridos desde o início do artigo.",
    }));
  }
  const facts = [
    ["Código interno", article.internal_code], ["Periódico", article.journal],
    ["Fator de impacto", article.impact_factor], ["Tipo de estudo", article.study_type],
    ["Responsável", article.lead_name], ["Início", dt(article.started_on)],
    ["1ª submissão", dt(article.first_submission_on)], ["Aceite", dt(article.accepted_on)],
    ["Publicação", dt(article.published_on)], ["WoS", article.wos_citations],
    ["Scopus", article.scopus_citations], ["OpenAlex", article.openalex_citations],
  ].filter(function (p) { return p[1] !== null && p[1] !== undefined && p[1] !== "—" && p[1] !== ""; });
  const dl = el("dl", { class: "facts" });
  facts.forEach(function (pair) {
    dl.appendChild(el("dt", { text: pair[0] }));
    dl.appendChild(el("dd", { text: String(pair[1]) }));
  });
  content.push(el("h4", { text: "Ficha" }));
  content.push(dl);
  if (article.doi) {
    content.push(el("p", { style: "margin-top:16px" },
      el("a", { href: "https://doi.org/" + article.doi, target: "_blank", rel: "noopener",
        text: "Abrir pelo DOI: " + article.doi })));
  }
  openDrawer(cut(article.title, 90), content);
}

/* ==================================================================== */
/* barra de filtros                                                      */
/* ==================================================================== */
function buildToolbar() {
  const bar = document.getElementById("toolbar");
  bar.innerHTML = "";
  const years = Array.from(new Set((D.articles || [])
    .map(function (a) { return a.year_published; }).filter(Boolean)))
    .sort(function (a, b) { return b - a; });
  const lines = (D.research_lines || []).map(function (l) { return l.name; });
  const people = (D.researchers || []).filter(function (r) { return r.n_articles > 0; });

  function select(placeholder, options, key, label) {
    const node = el("select", { "aria-label": label,
      onchange: function (ev) { STATE[key] = ev.target.value; render(); } });
    node.appendChild(el("option", { value: "", text: placeholder }));
    options.forEach(function (opt) {
      const value = typeof opt === "object" ? opt.value : opt;
      const text = typeof opt === "object" ? opt.label : opt;
      node.appendChild(el("option", { value: value, text: text }));
    });
    node.value = STATE[key];
    return node;
  }

  /* o ano é o filtro que todo mundo procura primeiro: fica em botões */
  const yearGroup = el("div", { class: "segmented", role: "group", "aria-label": "Ano" });
  [{ value: "", label: "Todos" }].concat(years.slice(0, 6).map(function (y) {
    return { value: String(y), label: String(y) };
  })).forEach(function (opt) {
    yearGroup.appendChild(el("button", {
      type: "button", text: opt.label, class: STATE.ano === opt.value ? "on" : null,
      "aria-pressed": String(STATE.ano === opt.value),
      onclick: function () { STATE.ano = opt.value; buildToolbar(); render(); },
    }));
  });

  bar.appendChild(el("span", { class: "flabel", text: "Ano" }));
  bar.appendChild(yearGroup);
  bar.appendChild(select("Todas as linhas", lines, "linha", "Linha de pesquisa"));
  bar.appendChild(select("Todas as situações",
    STATUS_ORDER.map(function (x) { return { value: x, label: STATUS_LABEL[x] }; }),
    "status", "Situação"));
  bar.appendChild(select("Todos os integrantes",
    people.map(function (p) { return { value: String(p.id), label: p.short_name || p.full_name }; }),
    "integrante", "Integrante"));
  const campoBusca = el("input", {
    class: "search", id: "busca", type: "search", value: STATE.busca, "aria-label": "Buscar",
    placeholder: "Buscar título, autor, revista…",
    oninput: function (ev) { STATE.busca = ev.target.value.toLowerCase(); render(); },
  });
  bar.appendChild(el("div", { class: "buscabox" }, [
    Icons.get("explorar", 15), campoBusca,
    el("kbd", { class: "atalho", text: "/" }),
  ]));
  bar.appendChild(el("button", { class: "clear", type: "button", text: "Limpar",
    disabled: !filtersActive(),
    onclick: function () {
      STATE.linha = STATE.ano = STATE.integrante = STATE.status = STATE.busca = "";
      buildToolbar();
      render();
    } }));

  const segSelect = select("", SEGMENTOS.map(function (x) {
    return { value: x.id, label: x.label }; }), "segmento", "Segmentar por");
  segSelect.value = STATE.segmento;
  bar.appendChild(el("div", { class: "segwrap" }, [
    el("span", { class: "flabel", text: "Segmentar por" }), segSelect]));
  bar.appendChild(el("span", { class: "fcount", id: "fcount" }));
  updateCount();
}
function updateCount() {
  const node = document.getElementById("fcount");
  if (node) node.textContent = articles().length + " de " + (D.articles || []).length + " artigos";
  const clear = document.querySelector("#toolbar button.clear");
  if (clear) clear.disabled = !filtersActive();
}

/* ==================================================================== */
/* abas                                                                  */
/* ==================================================================== */
const VIEWS = [];
function view(id, label, group, lead, render) {
  VIEWS.push({ id: id, label: label, group: group, lead: lead, render: render });
}

view("visao", "Painel", "", "Retrato do laboratório no recorte atual.", function (host) {
  const o = D.overview;
  const rows = articles();
  const published = rows.filter(function (a) { return a.status === "publicado"; });
  const currentYear = new Date().getFullYear();
  const years = [];
  for (let y = currentYear - o.window + 1; y <= currentYear; y++) years.push(y);
  const perYear = years.map(function (y) {
    return published.filter(function (a) { return a.year_published === y; }).length; });
  const windowTotal = perYear.reduce(function (a, b) { return a + b; }, 0);
  const media = windowTotal / o.window;
  const hist = (D.history && D.history.series) || {};
  const measured = function (metric) {
    return hist[metric] && hist[metric].delta_30d ? hist[metric].delta_30d : null; };
  const sparkOf = function (metric) {
    return hist[metric] && hist[metric].values.length > 1 ? hist[metric].values : null; };

  /* ---- leituras: o que cada número quer dizer -----------------------
     Todas saem do recorte atual, não de constante escrita à mão. Um painel
     que só mostra número obriga cada pessoa a interpretar sozinha. */
  const emProducao = rows.filter(function (a) { return a.status === "em_producao"; });
  const emAvaliacao = rows.filter(function (a) {
    return a.status === "submetido" || a.status === "em_revisao"; });
  const esperaMaxima = Math.max.apply(null, (D.submitted || [])
    .map(function (a) { return daysSince(a.last_submitted_on || a.first_submission_on) || 0; })
    .concat([0]));
  const publicadosNoAno = published.filter(function (a) {
    return Number(a.year_published) === currentYear; }).length;
  const ritmo = media > 0 ? publicadosNoAno / media : 0;
  const escritaLonga = median(emProducao.map(function (a) { return daysSince(a.started_on); })
    .filter(function (d) { return d !== null; }));
  const publicaram = new Set((D.authorship || []).filter(function (l) {
    const artigo = (D.articles || []).find(function (a) { return a.id === l.a; });
    return artigo && Number(artigo.year_published) >= currentYear - 1;
  }).map(function (l) { return l.m; })).size;
  const terminando = ((D.projects && D.projects.items) || []).filter(function (pj) {
    const d = daysSince(pj.ended_on);
    return pj.status === "em_andamento" && d !== null && d > -366 && d < 0;
  }).length;
  const hMediano = median((D.researchers || []).filter(function (m) { return !m.is_external; })
    .map(function (m) { return m.h_index; }));
  const comFomento = ((D.projects && D.projects.items) || [])
    .filter(function (pj) { return pj.funder; }).length;

  host.appendChild(el("div", { class: "grid g4 fixed4" }, [
    kpi({ label: "Artigos no recorte", value: C.fmt(rows.length), icon: "producao",
      foot: (D.articles || []).length + " no banco todo",
      delta: measured("artigos"), deltaNote: "em 30 dias", spark: sparkOf("artigos"),
      leitura: rows.length ? {
        texto: "estão publicados; " + C.fmt(emProducao.length + emAvaliacao.length)
          + " ainda em curso.",
        forte: Math.round(100 * published.length / rows.length) + "%",
      } : null }),
    kpi({ label: "Em produção", icon: "linha", value: C.fmt(emProducao.length),
      foot: "manuscritos em escrita", delta: measured("em_producao"), deltaNote: "em 30 dias",
      leitura: escritaLonga !== null ? {
        texto: "é o tempo mediano de escrita já decorrido neste grupo.",
        forte: dur(escritaLonga),
      } : null }),
    kpi({ label: "Submetidos", icon: "submissao", value: C.fmt(emAvaliacao.length),
      foot: "aguardando parecer", delta: measured("submetidos"), deltaNote: "em 30 dias",
      leitura: esperaMaxima > 0 ? {
        sinal: esperaMaxima > 180 ? "desce" : "parado",
        forte: dur(esperaMaxima),
        texto: "é a espera do mais antigo — o que decide se é hora de cobrar.",
      } : null }),
    kpi({ label: "Publicados", icon: "livro", value: C.fmt(published.length),
      foot: windowTotal + " nos últimos " + o.window + " anos",
      delta: measured("publicados"), deltaNote: "em 30 dias",
      spark: sparkOf("publicados") || perYear, sparkColor: C.token("--series-1"),
      leitura: media > 0 ? {
        sinal: ritmo >= 1 ? "sobe" : (ritmo >= 0.6 ? "parado" : "desce"),
        forte: C.fmt(publicadosNoAno) + " em " + currentYear,
        texto: "contra média de " + dec(media, 1) + " por ano na janela.",
      } : null }),
    kpi({ label: "Média por ano", icon: "subida", value: dec(media, 2),
      foot: "publicações/ano na janela",
      leitura: { texto: "Mede o ritmo da janela inteira; um ano fraco não a derruba, "
        + "e é por isso que ela serve de régua." } }),
    kpi({ label: "Pesquisadores", icon: "pessoas", value: C.fmt(o.n_members),
      foot: o.n_collaborators + " colaboradores externos",
      leitura: publicaram ? {
        forte: C.fmt(publicaram),
        texto: "assinaram algo publicado nos últimos dois anos.",
      } : null }),
    kpi({ label: "Projetos", icon: "projeto", value: C.fmt(o.n_projects),
      foot: o.n_projects_active + " em andamento",
      leitura: terminando ? {
        sinal: "desce",
        forte: C.fmt(terminando),
        texto: "termina" + (terminando > 1 ? "m" : "") + " nos próximos doze meses.",
      } : (comFomento ? {
        forte: C.fmt(comFomento),
        texto: "com financiadora declarada; nenhum vence nos próximos doze meses.",
      } : null) }),
    kpi({ label: "Maior índice h", icon: "alvo", value: C.fmt(o.best_h_index),
      foot: "entre os integrantes",
      leitura: hMediano !== null ? {
        forte: dec(hMediano, 0),
        texto: "é a mediana da equipe — o topo diz menos do que ela.",
      } : null }),
  ]));
  if (D.history && !D.history.available) {
    host.appendChild(el("div", { class: "note info", style: "margin-top:14px", html:
      "As setas de variação aparecem depois da segunda execução do lakehouse — é dele que "
      + "vem o histórico medido. Rode <span class='mono'>lape_agent.py lake</span>." }));
  }

  const segItems = topN(counter(rows, segmentOf), 7);
  const segLabel = (SEGMENTOS.find(function (x) { return x.id === STATE.segmento; }) || {}).label || "";
  host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
    card("Produção por " + segLabel.toLowerCase(),
      "Muda com o seletor “Segmentar por” na barra de filtros.",
      C.donut({ items: segItems, unit: "artigos", file: "producao-por-segmento",
        onSelect: function (item) { aplicarSegmento(item.label); },
        table: { cols: [{ label: segLabel, k: "label" }, { label: "Artigos", k: "value", num: true }],
          rows: segItems } })),
    card("Publicações por ano", "Coluna: publicações do ano. Régua: média da janela.",
      C.columns({
        labels: years.map(String),
        series: [{ label: "Publicações", values: perYear, color: C.token("--series-1") }],
        reference: media > 0 ? Math.round(media * 10) / 10 : null, referenceLabel: "média",
        file: "publicacoes-por-ano",
        onSelect: function (label) { STATE.ano = label; buildToolbar(); render(); },
        table: { cols: [{ label: "Ano", k: "ano" }, { label: "Publicações", k: "n", num: true }],
          rows: years.map(function (y, i) { return { ano: y, n: perYear[i] }; }) } })),
  ]));

  const submetidos = rows.filter(function (a) {
    return ["submetido", "em_revisao", "aceito", "publicado", "rejeitado"].indexOf(a.status) >= 0;
  }).length;
  const aceitos = rows.filter(function (a) {
    return a.status === "aceito" || a.status === "publicado"; }).length;
  const steps = [
    { label: "Iniciados", value: rows.length },
    { label: "Submetidos", value: submetidos },
    { label: "Aceitos", value: aceitos },
    { label: "Publicados", value: published.length },
  ];
  /* composição da produção ao longo da janela: o total e de que ele é feito */
  const comp = STATUS_ORDER.filter(function (st) {
    return rows.some(function (a) { return a.status === st; });
  }).map(function (st, i) {
    return {
      label: STATUS_LABEL[st] || st, color: C.token("--series-" + ((i % 8) + 1)),
      values: years.map(function (y) {
        return rows.filter(function (a) {
          return a.status === st && String(DIM_ACCESSOR.ano(a)) === String(y);
        }).length;
      }),
    };
  });
  const noAno = perYear[perYear.length - 1] || 0;
  const teto = Math.max(Math.max.apply(null, perYear.concat([1])), Math.ceil(media) || 1);
  host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
    card("Ritmo do ano corrente", "Publicações de " + currentYear
      + " contra o melhor ano da janela. A marca externa é a média.",
      C.gauge({
        value: noAno, max: teto, unit: "publicações em " + currentYear,
        bands: media > 0 ? [{ to: media, color: C.token("--warning") },
          { to: teto, color: C.token("--good") }] : [],
        caption: null, file: "ritmo",
        table: { cols: [{ label: "Ano", k: "ano" }, { label: "Publicações", k: "n", num: true }],
          rows: years.map(function (y, i) { return { ano: y, n: perYear[i] }; }) },
      })),
    card("Composição da produção por ano", "Cada faixa é um estágio do ciclo; o topo é o total do ano.",
      comp.length ? C.area({
        labels: years.map(String), series: comp, height: 250, file: "composicao",
        table: {
          cols: [{ label: "Ano", k: "ano" }].concat(comp.map(function (c) {
            return { label: c.label, k: c.label, num: true }; })),
          rows: years.map(function (y, i) {
            const row = { ano: y };
            comp.forEach(function (c) { row[c.label] = c.values[i]; });
            return row;
          }),
        },
      }) : C.empty("Sem produção na janela.")),
  ]));

  const linhas = topN(counter(rows, function (a) { return a.research_line || "Sem linha"; }), 8);
  host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
    card("Funil da produção", "Quantos manuscritos chegam a cada etapa do ciclo.",
      C.funnel({ steps: steps, file: "funil",
        table: { cols: [{ label: "Etapa", k: "label" }, { label: "Artigos", k: "value", num: true }],
          rows: steps } })),
    card("Peso de cada linha de pesquisa", "Área proporcional ao número de artigos.",
      C.treemap({ items: linhas, unit: "artigos", height: 300, file: "linhas",
        onSelect: function (item) {
          if (!item.muted) { STATE.linha = item.label; buildToolbar(); render(); } },
        table: { cols: [{ label: "Linha", k: "label" }, { label: "Artigos", k: "value", num: true }],
          rows: linhas } })),
  ]));
});

view("explorar", "Explorar dados", "", "Escolha a medida, o recorte e a quebra: o gráfico e a tabela "
  + "se refazem na hora, direto da camada analítica.", function (host) {
    const cat = D.catalog || { measures: [], dimensions: [] };
    if (!cat.measures.length) {
      host.appendChild(el("div", { class: "note", text:
        "Camada analítica ainda não construída. Rode: python3 scripts/lape_agent.py lake" }));
      return;
    }
    const box = el("div", { class: "card" });
    const controls = el("div", { class: "explorer-controls" });
    const out = el("div", { style: "margin-top:18px" });
    const state = { medida: "artigos", por: "linha", quebra: "", forma: "colunas" };

    function pick(label, options, key, onChange) {
      const sel = el("select", { "aria-label": label, onchange: function (ev) {
        state[key] = ev.target.value; onChange(); } });
      options.forEach(function (opt) {
        sel.appendChild(el("option", { value: opt.id, text: opt.label }));
      });
      sel.value = state[key];
      return el("div", { class: "field" }, [el("label", { text: label }), sel]);
    }

    async function run() {
      out.classList.add("reloading");
      let result;
      if (LIVE) {
        const params = new URLSearchParams({ medida: state.medida, por: state.por, limite: "40" });
        if (state.quebra) params.set("quebra", state.quebra);
        if (STATE.linha) params.set("linha", STATE.linha);
        if (STATE.ano) params.set("ano", STATE.ano);
        if (STATE.status) params.set("status", STATE.status);
        if (STATE.integrante) params.set("integrante", STATE.integrante);
        try {
          const response = await fetch("/api/query?" + params.toString());
          result = response.ok ? await response.json() : localQuery(state.medida, state.por, state.quebra);
        } catch (err) {
          result = localQuery(state.medida, state.por, state.quebra);
        }
      } else {
        result = localQuery(state.medida, state.por, state.quebra);
      }
      draw(result);
      out.classList.remove("reloading");
    }

    function draw(result) {
      out.innerHTML = "";
      const rows = result.rows.filter(function (r) { return r.valor !== null; });
      if (!rows.length) {
        out.appendChild(C.empty("Nenhum resultado para esta combinação."));
        return;
      }
      const tableSpec = {
        cols: [{ label: result.by_label, k: "dim1" }]
          .concat(result.split ? [{ label: result.split_label, k: "dim2" }] : [])
          .concat([{ label: result.measure_label, k: "valor", num: true }]),
        rows: rows,
      };
      const file = "explorar-" + result.measure + "-por-" + result.by;

      if (result.split) {
        const dim1 = Array.from(new Set(rows.map(function (r) { return r.dim1; }))).slice(0, 12);
        const dim2 = Array.from(new Set(rows.map(function (r) { return r.dim2; }))).slice(0, 8);
        out.appendChild(C.columns({
          mode: state.forma === "barras" ? "agrupado" : "empilhado",
          labels: dim1.map(function (d) { return cut(String(d), 14); }),
          series: dim2.map(function (d2) {
            return { label: String(d2), values: dim1.map(function (d1) {
              const found = rows.find(function (r) { return r.dim1 === d1 && r.dim2 === d2; });
              return found ? Number(found.valor) || 0 : 0;
            }) };
          }),
          height: 320, file: file, table: tableSpec,
          caption: result.measure_label + " por " + result.by_label.toLowerCase()
            + ", quebrado por " + result.split_label.toLowerCase() + ".",
        }));
      } else if (state.forma === "barras") {
        out.appendChild(C.bars({
          items: rows.slice(0, 20).map(function (r, i) {
            return { label: String(r.dim1), value: Number(r.valor) || 0, rank: i + 1 }; }),
          mono: true, labelWidth: 230, labelChars: 34, unit: result.unit, file: file,
          table: tableSpec,
          caption: result.measure_label + " por " + result.by_label.toLowerCase() + ".",
        }));
      } else if (state.forma === "rosca") {
        out.appendChild(C.donut({
          items: topN(rows.map(function (r) {
            return { label: String(r.dim1), value: Number(r.valor) || 0 }; }), 7),
          unit: result.unit, file: file, table: tableSpec,
          caption: result.measure_label + " por " + result.by_label.toLowerCase() + ".",
        }));
      } else if (state.forma === "arvore") {
        out.appendChild(C.treemap({
          items: topN(rows.map(function (r) {
            return { label: String(r.dim1), value: Number(r.valor) || 0 }; }), 12),
          unit: result.unit, height: 320, file: file, table: tableSpec,
        }));
      } else {
        out.appendChild(C.columns({
          labels: rows.slice(0, 16).map(function (r) { return cut(String(r.dim1), 14); }),
          series: [{ label: result.measure_label,
            values: rows.slice(0, 16).map(function (r) { return Number(r.valor) || 0; }),
            color: C.token("--series-1") }],
          height: 320, file: file, table: tableSpec,
          caption: result.measure_label + " por " + result.by_label.toLowerCase() + ".",
        }));
      }
      out.appendChild(el("div", { class: "hint", style: "margin-top:12px",
        text: "Total no recorte: " + C.fmt(Math.round(result.total * 100) / 100) + " " + (result.unit || "")
          + (result.local ? " · calculado no navegador" : " · calculado na camada analítica") }));
    }

    controls.appendChild(pick("Medida", cat.measures, "medida", run));
    controls.appendChild(pick("Recortar por", cat.dimensions, "por", run));
    controls.appendChild(pick("Quebrar por",
      [{ id: "", label: "— sem quebra —" }].concat(cat.dimensions), "quebra", run));
    controls.appendChild(pick("Forma", [
      { id: "colunas", label: "Colunas" }, { id: "barras", label: "Barras" },
      { id: "rosca", label: "Rosca" }, { id: "arvore", label: "Treemap" },
    ], "forma", run));
    box.appendChild(controls);
    box.appendChild(out);
    host.appendChild(box);
    host.appendChild(el("div", { class: "note info", style: "margin-top:16px", html:
      "As mesmas combinações estão na API: <span class='mono'>GET /api/query?medida=publicados"
      + "&por=linha&quebra=ano</span> — útil para levar os números para o Excel, o R ou o Power BI." }));
    run();
  });

view("organograma", "Organograma", "Pessoas e projetos",
  "Quem orienta quem, e o que cada pessoa está tocando. O desenho sai do cadastro: "
  + "ninguém arrasta caixa.",
  function (host) {
    const org = D.org || {};
    const gente = org.people || [];
    if (!gente.length) {
      host.appendChild(el("div", { class: "note", html:
        "<b>Nenhum integrante cadastrado ainda.</b> Assim que alguém se cadastrar em "
        + "<a href='/app#perfil'>Área do integrante</a> apontando o orientador, "
        + "o organograma se monta sozinho." }));
      return;
    }

    /* Quantos há de cada vínculo. Ordinal, e não categórico: os vínculos têm
       ordem (coordenação, professor, doutorando, mestrando…), e a cor deve
       carregar essa ordem em vez de sortear um matiz para cada um. */
    host.appendChild(el("div", { class: "grid g4", style: "margin-bottom:18px" },
      (org.by_role || []).slice(0, 8).map(function (r, i) {
        return kpi({ label: r.label, value: C.fmt(r.n),
          icon: r.role === "sem_vinculo" ? "aviso" : "pessoa",
          tone: r.role === "sem_vinculo" ? "bad" : null });
      })));

    const pendencias = [];
    if ((org.sem_vinculo || []).length) {
      pendencias.push((org.sem_vinculo.length) + " sem vínculo declarado: "
        + org.sem_vinculo.slice(0, 4).map(function (p) { return p.full_name; }).join(", ")
        + (org.sem_vinculo.length > 4 ? " e outros" : ""));
    }
    if ((org.sem_orientador || []).length) {
      pendencias.push((org.sem_orientador.length) + " sem orientador apontado: "
        + org.sem_orientador.slice(0, 4).map(function (p) { return p.full_name; }).join(", ")
        + (org.sem_orientador.length > 4 ? " e outros" : ""));
    }
    if (pendencias.length) {
      host.appendChild(el("div", { class: "note", style: "margin-bottom:18px" }, [
        el("b", { text: "O desenho está incompleto. " }),
        el("span", { text: pendencias.join(" · ")
          + ". Quem preenche é a própria pessoa, na área do integrante." }),
      ]));
    }

    host.appendChild(card("Quem responde a quem",
      "Cada coluna é um orientador. Clique numa pessoa para abrir a ficha completa.",
      organogramaEmColunas(org)));

    if ((org.orientadores || []).length) {
      host.appendChild(el("div", { style: "margin-top:18px" }, card(
        "Carga de orientação", "Quantos orientandos cada professor acompanha.",
        C.bars({
          items: org.orientadores.map(function (o) {
            return { label: o.full_name, value: o.n,
              note: o.research_line || "sem linha declarada" };
          }),
          unit: "orientandos", mono: true, labelWidth: 220, file: "carga-de-orientacao",
          table: { cols: [{ label: "Orientador", k: "full_name" },
            { label: "Vínculo", k: "role_label" },
            { label: "Orientandos", k: "n", num: true }], rows: org.orientadores },
        }))));
    }

    const teses = org.teses || [];
    host.appendChild(el("div", { style: "margin-top:18px" }, card(
      "Teses, dissertações e planos de trabalho",
      "Prazo em branco é prazo que ninguém declarou — e prazo não declarado não cobra.",
      dataTable({
        cols: [
          { label: "Pessoa", k: "full_name" },
          { label: "Vínculo", k: "role_label" },
          { label: "Trabalho", k: "title", render: function (r) {
            return r.title ? cut(r.title, 60) : "título em definição"; } },
          { label: "Orientação", k: "advisor" },
          { label: "Situação", k: "status", render: function (r) {
            return TESE_SITUACAO[r.status] || r.status || "—"; } },
          { label: "Prazo", k: "due_on", render: function (r) { return dt(r.due_on); } },
        ],
        rows: teses, sortKey: "due_on", sortDir: 1, pageSize: 15,
        emptyMessage: "Ninguém declarou tese, dissertação ou plano de trabalho ainda.",
      }))));
  });

/* Organograma em colunas, e não em árvore SVG: com vinte pessoas, uma árvore
   desenhada fica com três mil pixels de largura, e a raiz — centrada sobre
   todos os filhos — vai parar no meio, fora da tela. Em colunas, cada
   orientador ocupa uma faixa com a sua gente embaixo, e o desenho cabe. */
function organogramaEmColunas(org) {
  const gente = org.people || [];
  const porId = new Map(gente.map(function (p) { return [p.id, p]; }));
  const filhos = new Map();
  (org.edges || []).forEach(function (e) {
    if (e.kind !== "orientacao") return;
    if (!filhos.has(e.from)) filhos.set(e.from, []);
    filhos.get(e.from).push(e.to);
  });

  function cartao(pessoa, classe) {
    const node = el("button", {
      class: classe, type: "button",
      title: "Abrir a ficha de " + pessoa.full_name,
      onclick: function () { showResearcher(pessoa.id); },
    }, [
      el("b", { text: pessoa.short_name || pessoa.full_name }),
      el("small", { text: [pessoa.role_label, pessoa.research_line
        ? cut(pessoa.research_line, 26) : null].filter(Boolean).join(" · ") }),
    ]);
    const marcas = el("span", { class: "org-marks" });
    if (pessoa.thesis_due_on) {
      marcas.appendChild(el("span", { class: "org-chip", text: dt(pessoa.thesis_due_on) }));
    }
    if (pessoa.scholarship) {
      marcas.appendChild(el("span", { class: "org-chip soft",
        text: cut(pessoa.scholarship, 18) }));
    }
    if (pessoa.co_advisor) {
      marcas.appendChild(el("span", { class: "org-chip soft",
        text: "coorient.: " + cut(pessoa.co_advisor, 16) }));
    }
    if (marcas.childNodes.length) node.appendChild(marcas);
    return node;
  }

  /* Um orientando que também orienta (o pós-doutorado, quase sempre) aparece
     uma vez só, com a sua gente recuada abaixo dele. */
  const desenhados = new Set();
  function ramo(id, nivel) {
    if (desenhados.has(id) || nivel > 3) return null;
    desenhados.add(id);
    const pessoa = porId.get(id);
    if (!pessoa) return null;
    const linha = el("li", { class: "org-kid n" + Math.min(nivel, 3) },
      cartao(pessoa, "org-card small"));
    const netos = (filhos.get(id) || []).map(function (f) { return ramo(f, nivel + 1); })
      .filter(Boolean);
    if (netos.length) linha.appendChild(el("ul", { class: "org-kids" }, netos));
    return linha;
  }

  const caixa = el("div", { class: "org" });
  const raiz = (org.roots || []).map(function (id) { return porId.get(id); })
    .find(function (p) { return p && p.role === "coordenacao"; });
  if (raiz) {
    desenhados.add(raiz.id);
    caixa.appendChild(el("div", { class: "org-top" }, cartao(raiz, "org-card boss")));
    caixa.appendChild(el("div", { class: "org-stem" }));
  }

  /* Uma coluna por quem orienta -- a coordenação inclusive: ela aparece no
     topo por coordenar, e ganha coluna própria por orientar, que são duas
     coisas diferentes. Sem essa coluna, quem ela orienta sumia do desenho. */
  const colunas = (org.orientadores || []).map(function (o) {
    const pessoa = porId.get(o.id);
    if (!pessoa) return null;
    const ehRaiz = raiz && o.id === raiz.id;
    if (!ehRaiz && desenhados.has(o.id)) return null;
    desenhados.add(o.id);
    const kids = (filhos.get(o.id) || []).map(function (f) { return ramo(f, 1); })
      .filter(Boolean);
    const cabeca = ehRaiz
      ? el("div", { class: "org-card ghost" }, [
        el("b", { text: "Orientação direta" }),
        el("small", { text: pessoa.short_name || pessoa.full_name }),
      ])
      : cartao(pessoa, "org-card");
    return el("div", { class: "org-branch" }, [
      cabeca,
      kids.length ? el("ul", { class: "org-kids" }, kids)
        : el("p", { class: "org-vazio", text: "sem orientandos declarados" }),
    ]);
  }).filter(Boolean);

  const sobra = gente.filter(function (p) { return !desenhados.has(p.id); });
  if (sobra.length) {
    colunas.push(el("div", { class: "org-branch solta" }, [
      el("div", { class: "org-card ghost" }, [
        el("b", { text: "Sem orientação declarada" }),
        el("small", { text: sobra.length + (sobra.length === 1 ? " pessoa" : " pessoas") }),
      ]),
      el("ul", { class: "org-kids" }, sobra.map(function (p) {
        return el("li", { class: "org-kid n1" }, cartao(p, "org-card small"));
      })),
    ]));
  }

  const trilho = el("div", { class: "org-branches" }, colunas);
  /* a barra horizontal precisa nascer no centro da primeira coluna e morrer
     no centro da última: sem saber quantas são, o CSS erraria as duas pontas */
  trilho.style.setProperty("--n", String(Math.max(colunas.length, 1)));
  if (!raiz) trilho.classList.add("sem-topo");
  caixa.appendChild(el("div", { class: "org-scroll" }, trilho));
  return caixa;
}

const TESE_SITUACAO = {
  em_andamento: "Em andamento", coleta: "Coleta de dados", analise: "Análise de dados",
  qualificacao: "Qualificação", defesa_marcada: "Defesa marcada", concluida: "Concluída",
  trancada: "Trancada",
};

view("linhas", "Linhas de pesquisa", "Pessoas e projetos",
  "Cada linha reúne artigos, pessoas, projetos e atividades. Clique para filtrar o painel.",
  function (host) {
    const rows = D.research_lines || [];
    if (!rows.length) {
      host.appendChild(el("div", { class: "note", html:
        "<b>Nenhuma linha cadastrada ainda.</b> Cadastre em <a href='/app#linhas'>Área do integrante "
        + "→ Linhas de pesquisa</a> ou na aba “Linhas de Pesquisa” da planilha de cadastros." }));
      return;
    }
    host.appendChild(el("div", { class: "grid g3" }, rows.map(function (line) {
      const node = el("div", { class: "card clickable", tabindex: "0" }, [
        el("h3", { text: line.name }),
        el("div", { class: "hint", text: line.description
          || (line.coordinator ? "Coordenação: " + line.coordinator : "—") }),
        el("div", { class: "grid g4", style: "gap:8px;margin-top:14px" }, [
          kpi({ label: "Artigos", value: C.fmt(line.n_articles) }),
          kpi({ label: "Publicados", value: C.fmt(line.n_published) }),
          kpi({ label: "Pessoas", value: C.fmt(line.n_members) }),
          kpi({ label: "Atividades", value: C.fmt(line.n_events) }),
        ]),
        line.keywords ? el("div", { class: "hint", style: "margin-top:12px", text: line.keywords }) : null,
      ]);
      const fire = function () { STATE.linha = line.name; buildToolbar(); go("producao"); };
      node.addEventListener("click", fire);
      node.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter") { ev.preventDefault(); fire(); } });
      return node;
    })));
    host.appendChild(el("div", { style: "margin-top:16px" }, card(
      "Comparativo entre linhas", "Em produção, submetidos e publicados, na mesma coluna.",
      C.columns({
        mode: "empilhado",
        labels: rows.map(function (l) { return cut(l.name, 20); }),
        series: [
          { label: "Em produção", values: rows.map(function (l) { return l.n_in_progress; }) },
          { label: "Submetidos", values: rows.map(function (l) { return l.n_submitted; }) },
          { label: "Publicados", values: rows.map(function (l) { return l.n_published; }) },
        ],
        height: 300, file: "linhas-comparativo",
        table: { cols: [{ label: "Linha", k: "name" }, { label: "Em produção", k: "n_in_progress", num: true },
          { label: "Submetidos", k: "n_submitted", num: true },
          { label: "Publicados", k: "n_published", num: true }], rows: rows },
      }))));

    /* Radar por ano. Todos os eixos são a mesma coisa — artigos num ano —,
       que é a única situação em que o radar não engana. */
    const anoAtual = new Date().getFullYear();
    const janela = [];
    for (let y = anoAtual - Math.min(D.overview.window, 6) + 1; y <= anoAtual; y++) janela.push(y);
    const todos = articles();
    const perfis = rows.slice(0, 4).map(function (line, i) {
      return {
        label: cut(line.name, 24), color: C.token("--series-" + ((i % 8) + 1)),
        values: janela.map(function (y) {
          return todos.filter(function (a) {
            return (a.research_line || "Sem linha") === line.name
              && String(DIM_ACCESSOR.ano(a)) === String(y);
          }).length;
        }),
      };
    }).filter(function (perfil) {
      return perfil.values.some(function (v) { return v > 0; });
    });
    if (perfis.length && janela.length >= 3) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Perfil de cada linha ao longo da janela",
        "Cada eixo é um ano e a unidade é a mesma em todos: artigos. "
        + "Quanto mais para fora, mais produção naquele ano.",
        C.radar({
          axes: janela.map(String), series: perfis, height: 360, file: "linhas-radar",
          table: {
            cols: [{ label: "Linha", k: "linha" }].concat(janela.map(function (y) {
              return { label: String(y), k: String(y), num: true }; })),
            rows: perfis.map(function (perfil) {
              const row = { linha: perfil.label };
              janela.forEach(function (y, i) { row[String(y)] = perfil.values[i]; });
              return row;
            }),
          },
        }))));
    }
  });

view("pesquisadores", "Pesquisadores", "Pessoas e projetos",
  "Nome, linha, projetos, artigos publicados e índice h. Clique numa linha para abrir a ficha.",
  function (host) {
    const rows = (D.researchers || []).filter(function (r) { return !r.is_external || r.n_articles > 0; });
    const ranked = rows.filter(function (r) { return (r.h_index || 0) > 0; })
      .sort(function (a, b) { return b.h_index - a.h_index; }).slice(0, 15);
    host.appendChild(el("div", { class: "grid g2" }, [
      card("Índice h por pesquisador", "Vem do perfil público do OpenAlex quando há ORCID cadastrado.",
        ranked.length ? C.bars({
          items: ranked.map(function (r, i) {
            return { label: r.short_name || r.full_name, value: r.h_index, rank: i + 1,
              note: (r.citations_total || 0) + " citações",
              onSelect: function () { showResearcher(r.id); } }; }),
          mono: true, labelWidth: 180, unit: "índice h", file: "indice-h",
          table: { cols: [{ label: "Pesquisador", k: "label" }, { label: "Índice h", k: "value", num: true }],
            rows: ranked.map(function (r) { return { label: r.full_name, value: r.h_index }; }) },
        }) : C.empty("Rode o rastreador (tarefa “perfis”) para trazer o índice h.")),
      card("Produção × impacto", "Cada ponto é um pesquisador: artigos no eixo horizontal, citações no vertical.",
        C.scatter({
          points: rows.filter(function (r) { return r.n_articles > 0; }).map(function (r) {
            return { x: r.n_articles, y: r.citations_total || 0, label: r.short_name || r.full_name,
              onSelect: function () { showResearcher(r.id); } }; }),
          xLabel: "artigos", yLabel: "citações", height: 310, file: "producao-impacto" })),
    ]));
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Pesquisadores (" + rows.length + ")", searchPlaceholder: "Buscar pesquisador…",
      sortKey: "n_articles", pageSize: 20, file: "pesquisadores",
      onRow: function (r) { showResearcher(r.id); },
      cols: [
        { k: "full_name", label: "Pesquisador", wide: true, render: function (r) {
          return el("div", {}, [r.full_name,
            el("small", { text: [r.role, r.degree].filter(Boolean).join(" · ") || "—" })]); } },
        { k: "research_line", label: "Linha de pesquisa" },
        { k: "n_projects", label: "Projetos", num: true },
        { k: "n_articles", label: "Artigos", num: true },
        { k: "n_published", label: "Publicados", num: true },
        { k: "n_submitted", label: "Submetidos", num: true },
        { k: "h_index", label: "Índice h", num: true },
        { k: "citations_total", label: "Citações", num: true },
      ],
      rows: rows, emptyMessage: "Nenhum pesquisador cadastrado.",
    })));
  });

view("projetos", "Projetos", "Pessoas e projetos",
  "Projetos de pesquisa e extensão, com equipe, financiamento e vigência.", function (host) {
    const data = D.projects || { items: [], total: 0 };
    if (!data.total) {
      host.appendChild(el("div", { class: "note", html:
        "<b>Nenhum projeto cadastrado.</b> Cadastre em <a href='/app#projetos'>Área do integrante "
        + "→ Projetos</a> ou na aba “Projetos” da planilha de cadastros." }));
      return;
    }
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Projetos", value: C.fmt(data.total), foot: "no banco" }),
      kpi({ label: "Em andamento", value: C.fmt(data.active), foot: "vigentes" }),
      kpi({ label: "Financiadores", value: C.fmt(data.by_funder.length), foot: "agências distintas" }),
      kpi({ label: "Recursos", value: data.total_amount ? "R$ " + C.compact(data.total_amount) : "—",
        foot: "somados" }),
    ]));
    const vigentes = data.items.filter(function (p) { return p.started_on && p.ended_on; });
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Projetos por financiador", null, C.bars({
        items: topN(data.by_funder.map(function (f) { return { label: f.funder, value: f.n }; }), 8),
        mono: true, labelWidth: 170, unit: "projeto(s)", file: "financiadores" })),
      card("Vigência", "Do início ao término previsto de cada projeto.",
        vigentes.length ? C.dumbbell({
          items: vigentes.map(function (p) {
            return { label: cut(p.name, 30), from: new Date(p.started_on).getFullYear(),
              to: new Date(p.ended_on).getFullYear() }; }),
          fromLabel: "início", toLabel: "término", labelWidth: 240, file: "vigencia",
        }) : C.empty("Nenhum projeto com início e término preenchidos.")),
    ]));
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Projetos", file: "projetos", sortKey: "started_on",
      cols: [
        { k: "code", label: "Código" },
        { k: "name", label: "Projeto", wide: true, render: function (r) {
          return el("div", {}, [r.name,
            el("small", { text: r.members ? cut(r.members, 80) : "sem equipe cadastrada" })]); } },
        { k: "coordinator", label: "Coordenação" },
        { k: "funder", label: "Financiador" },
        { k: "n_members", label: "Equipe", num: true },
        { k: "started_on", label: "Início", render: function (r) { return dt(r.started_on); } },
        { k: "ended_on", label: "Término", render: function (r) { return dt(r.ended_on); } },
        { k: "status", label: "Situação", render: function (r) {
          return el("span", { class: "badge " + (r.status === "em_andamento" ? "s-publicado" : ""),
            text: PROJECT_LABEL[r.status] || r.status }); } },
      ],
      rows: data.items,
    })));
  });

view("producao", "Em produção", "Produção",
  "Manuscritos em escrita, com início, equipe e tempo em aberto.", function (host) {
    const rows = articles().filter(function (a) { return a.status === "em_producao"; });
    const idade = rows.map(function (a) { return daysSince(a.started_on); })
      .filter(function (v) { return v !== null; });
    const carga = counter(rows, function (a) {
      return a.lead_name || (a.authors || "").split(";")[0].trim() || "Sem responsável"; });
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Em produção", value: C.fmt(rows.length), foot: "no recorte atual" }),
      kpi({ label: "Idade mediana", value: dur(median(idade)), foot: "desde o início" }),
      kpi({ label: "Mais antigo", value: dur(idade.length ? Math.max.apply(null, idade) : null),
        foot: "em aberto" }),
      kpi({ label: "Responsáveis", value: C.fmt(carga.length), foot: "com artigo em escrita" }),
    ]));
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Carga por responsável", "Artigos em escrita sob responsabilidade de cada pessoa.",
        C.bars({ items: topN(carga, 8), mono: true, labelWidth: 170, unit: "artigo(s)",
          file: "carga-responsavel" })),
      card("Há quanto tempo estão abertos", "Caixa: intervalo interquartil. Traço: mediana.",
        idade.length ? C.distribution({
          groups: [{ label: "Artigos em escrita",
            values: idade.map(function (v) { return Math.round(v); }) }],
          labelWidth: 160, file: "idade-artigos",
        }) : C.empty("Preencha a data de início dos artigos.")),
    ]));
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Artigos em produção", file: "em-producao", sortKey: "started_on", onRow: showArticle,
      cols: [
        { k: "internal_code", label: "ID" },
        { k: "title", label: "Título", wide: true, render: function (r) {
          return el("div", {}, [r.title,
            el("small", { text: r.research_line || "sem linha de pesquisa" })]); } },
        { k: "authors", label: "Autores", render: function (r) { return cut(r.authors, 50); } },
        { k: "started_on", label: "Início", render: function (r) { return dt(r.started_on); } },
        { label: "Em aberto", num: true, sortValue: function (r) { return daysSince(r.started_on) || -1; },
          render: function (r) { return dur(daysSince(r.started_on)); } },
      ],
      rows: rows, emptyMessage: "Nenhum artigo em produção neste recorte.",
    })));
  });

view("submetidos", "Submetidos", "Produção",
  "Manuscritos sob avaliação, com a revista e o tempo desde o envio.", function (host) {
    const rows = articles().filter(function (a) {
      return a.status === "submetido" || a.status === "em_revisao"; });
    const espera = rows.map(function (a) { return daysSince(a.first_submission_on); })
      .filter(function (v) { return v !== null; });
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Sob avaliação", value: C.fmt(rows.length) }),
      kpi({ label: "Espera mediana", value: dur(median(espera)), foot: "desde a submissão" }),
      kpi({ label: "Espera máxima", value: dur(espera.length ? Math.max.apply(null, espera) : null) }),
      kpi({ label: "Revistas", value: C.fmt(counter(rows, "journal").length), foot: "distintas" }),
    ]));
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Submetidos", file: "submetidos", sortKey: "first_submission_on", onRow: showArticle,
      cols: [
        { k: "internal_code", label: "ID" },
        { k: "title", label: "Título", wide: true },
        { k: "authors", label: "Autores", render: function (r) { return cut(r.authors, 40); } },
        { k: "journal", label: "Revista" },
        { k: "first_submission_on", label: "Submissão",
          render: function (r) { return dt(r.first_submission_on); } },
        { k: "submission_attempts", label: "Tentativas", num: true },
        { label: "Em avaliação há", num: true,
          sortValue: function (r) { return daysSince(r.first_submission_on) || -1; },
          render: function (r) { return dur(daysSince(r.first_submission_on)); } },
      ],
      rows: rows, emptyMessage: "Nenhum artigo submetido neste recorte.",
    })));
  });

view("publicacoes", "Publicações", "Produção",
  "Estudos publicados, com total e média anual na janela de análise.", function (host) {
    const o = D.overview;
    const published = articles().filter(function (a) { return a.status === "publicado"; });
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let y = currentYear - o.window + 1; y <= currentYear; y++) years.push(y);
    const perYear = years.map(function (y) {
      return published.filter(function (a) { return a.year_published === y; }).length; });
    const total = perYear.reduce(function (a, b) { return a + b; }, 0);
    let running = 0;
    const cumulative = perYear.map(function (v) { running += v; return running; });
    const allYears = Array.from(new Set(published.map(function (a) { return a.year_published; })
      .filter(Boolean))).sort();

    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "No período", value: C.fmt(total), foot: "últimos " + o.window + " anos",
        spark: perYear }),
      kpi({ label: "Média por ano", value: dec(total / o.window, 2), foot: "artigos/ano" }),
      kpi({ label: "Total no recorte", value: C.fmt(published.length), foot: "todos os anos" }),
      kpi({ label: "Melhor ano",
        value: total ? years[perYear.indexOf(Math.max.apply(null, perYear))] : "—" }),
    ]));
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Por ano e acumulado", "Colunas: publicações do ano. Linha: acumulado no período.", [
        C.columns({ labels: years.map(String),
          series: [{ label: "Publicações", values: perYear, color: C.token("--series-1") }],
          file: "publicacoes-ano", height: 220,
          onSelect: function (label) { STATE.ano = label; buildToolbar(); render(); } }),
        C.lines({ labels: years.map(String),
          series: [{ label: "Acumulado", values: cumulative, color: C.token("--series-3"), area: true }],
          height: 170, file: "publicacoes-acumulado" }),
      ]),
      card("Série histórica completa", "Todos os anos com publicação registrada.",
        allYears.length ? C.columns({
          labels: allYears.map(String),
          series: [{ label: "Publicações", values: allYears.map(function (y) {
            return published.filter(function (a) { return a.year_published === y; }).length; }),
            color: C.token("--series-1") }],
          height: 300, file: "serie-historica",
        }) : C.empty("Importe o XML do Lattes ou cadastre publicações.")),
    ]));
    const revistas = counter(published, "journal");
    if (revistas.length) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Onde o laboratório publica", "Periódicos com mais artigos do LAPE.",
        C.bars({ items: topN(revistas, 12), mono: true, labelWidth: 260, labelChars: 38,
          unit: "artigo(s)", file: "periodicos" }))));
    }

    /* Quem esteve no topo em cada ano. O gráfico lê a inclinação: subiu, caiu
       ou sumiu do quadro. Sem posição num ano, a linha simplesmente não passa por lá. */
    const anosBump = years.filter(function (y, i) { return perYear[i] > 0; });
    if (anosBump.length >= 2) {
      const porAno = anosBump.map(function (y) {
        const doAno = published.filter(function (a) { return a.year_published === y; });
        const contagem = new Map();
        doAno.forEach(function (a) {
          (D.researchers || []).forEach(function (person) {
            const set = MEMBER_ARTICLES.get(person.id);
            if (set && set.has(a.id)) {
              contagem.set(person.id, (contagem.get(person.id) || 0) + 1);
            }
          });
        });
        return Array.from(contagem.entries()).sort(function (a, b) { return b[1] - a[1]; });
      });
      const noTopo = new Set();
      porAno.forEach(function (lista) {
        lista.slice(0, 5).forEach(function (par) { noTopo.add(par[0]); });
      });
      const pessoas = Array.from(noTopo).slice(0, 6).map(function (id, i) {
        const person = (D.researchers || []).find(function (r) { return r.id === id; }) || {};
        return {
          label: cut(person.short_name || person.full_name || "—", 22),
          color: C.token("--series-" + ((i % 8) + 1)),
          onClick: function () { showResearcher(id); },
          values: porAno.map(function (lista) {
            const pos = lista.findIndex(function (par) { return par[0] === id; });
            return pos >= 0 && pos < 6 ? pos + 1 : null;
          }),
        };
      }).filter(function (x) { return x.values.some(Boolean); });
      if (pessoas.length >= 2) {
        host.appendChild(el("div", { style: "margin-top:16px" }, card(
          "Quem publicou mais, ano a ano",
          "Posição no ano entre os integrantes com publicação. 1º fica no alto; "
          + "sem publicação naquele ano, a linha não passa por ele.",
          C.bump({
            labels: anosBump.map(String), series: pessoas, file: "ranking-anual",
            table: {
              cols: [{ label: "Integrante", k: "quem" }].concat(anosBump.map(function (y) {
                return { label: String(y), k: String(y) }; })),
              rows: pessoas.map(function (x) {
                const row = { quem: x.label };
                anosBump.forEach(function (y, i) {
                  row[String(y)] = x.values[i] ? x.values[i] + "º" : "—";
                });
                return row;
              }),
            },
          }))));
      }
    }
  });

view("citacoes", "Mais citados", "Produção",
  "Ranking por base. As contagens são atualizadas pelo DOI a cada execução do rastreador.",
  function (host) {
    const published = articles().filter(function (a) { return a.status === "publicado"; });
    const cited = published.filter(function (a) { return bestCitations(a) > 0; });
    const total = published.reduce(function (acc, a) { return acc + bestCitations(a); }, 0);
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Citações somadas", value: C.fmt(total), foot: "melhor base por artigo" }),
      kpi({ label: "Artigos citados", value: C.fmt(cited.length),
        foot: "de " + published.length + " publicados" }),
      kpi({ label: "Mediana", value: cited.length ? C.fmt(median(cited.map(bestCitations))) : "—",
        foot: "citações por artigo" }),
      kpi({ label: "Mais citado",
        value: cited.length ? C.fmt(Math.max.apply(null, cited.map(bestCitations))) : "—",
        foot: "citações" }),
    ]));
    const bases = [
      { key: "scopus_citations", label: "Scopus" },
      { key: "wos_citations", label: "Web of Science" },
      { key: "openalex_citations", label: "OpenAlex" },
    ];
    host.appendChild(el("div", { style: "margin-top:16px" }, card(null, null,
      tabbed(bases.map(function (base) {
        const top = published.filter(function (a) { return (a[base.key] || 0) > 0; })
          .sort(function (a, b) { return (b[base.key] || 0) - (a[base.key] || 0); }).slice(0, 12);
        return { label: base.label, content: [
          top.length ? C.bars({
            items: top.map(function (a, k) {
              return { label: cut(a.title, 44), value: a[base.key], rank: k + 1,
                note: [a.journal, a.year_published].filter(Boolean).join(" · "),
                onSelect: function () { showArticle(a); } }; }),
            mono: true, labelWidth: 300, labelChars: 44, unit: "citações",
            file: "mais-citados-" + base.label,
          }) : C.empty("Sem citações desta base no recorte atual."),
          dataTable({
            search: false, pageSize: 12, sortKey: base.key, file: "citacoes-" + base.label,
            onRow: showArticle,
            cols: [
              { k: "title", label: "Título", wide: true, render: function (r) {
                return el("div", {}, [
                  r.doi ? el("a", { href: "https://doi.org/" + r.doi, target: "_blank",
                    rel: "noopener", text: r.title }) : r.title,
                  el("small", { text: [r.journal, r.year_published].filter(Boolean).join(" · ") })]); } },
              { k: "year_published", label: "Ano", num: true },
              { k: "wos_citations", label: "WoS", num: true },
              { k: "scopus_citations", label: "Scopus", num: true },
              { k: "openalex_citations", label: "OpenAlex", num: true },
            ],
            rows: published.filter(function (a) { return (a[base.key] || 0) > 0; }),
            emptyMessage: "Sem citações desta base.",
          }),
        ] };
      })))));
    if (cited.length > 2) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Idade × impacto", "Artigos mais antigos tiveram mais tempo para acumular citações.",
        C.scatter({
          points: cited.map(function (a) {
            return { x: a.year_published, y: bestCitations(a), label: cut(a.title, 60),
              onSelect: function () { showArticle(a); } }; }),
          xLabel: "ano de publicação", yLabel: "citações", height: 300, file: "idade-impacto" }))));
    }
    host.appendChild(el("div", { class: "note info", style: "margin-top:16px", html:
      "<b>OpenAlex</b> é uma base aberta e não exige chave de API — serve de referência imediata "
      + "de impacto enquanto Scopus e Web of Science não estiverem configurados." }));
  });

view("equipe", "Por integrante", "Métricas internas",
  "Envolvimento de cada pessoa nos artigos do recorte atual.", function (host) {
    const rows = articles();
    const counts = (D.researchers || []).map(function (person) {
      const set = MEMBER_ARTICLES.get(person.id) || new Set();
      const own = rows.filter(function (a) { return set.has(a.id); });
      return Object.assign({}, person, {
        f_total: own.length,
        f_published: own.filter(function (a) { return a.status === "publicado"; }).length,
        f_progress: own.filter(function (a) { return a.status === "em_producao"; }).length,
        f_submitted: own.filter(function (a) {
          return a.status === "submetido" || a.status === "em_revisao"; }).length,
      });
    }).filter(function (p) { return p.f_total > 0; })
      .sort(function (a, b) { return b.f_total - a.f_total; });
    const top = counts.slice(0, 14);
    host.appendChild(card("Envolvimento por etapa",
      "Cada coluna é uma pessoa; as faixas mostram em que etapa estão os artigos dela.",
      C.columns({
        mode: "empilhado",
        labels: top.map(function (r) { return cut(r.short_name || r.full_name, 12); }),
        series: [
          { label: "Em produção", values: top.map(function (r) { return r.f_progress; }) },
          { label: "Submetidos", values: top.map(function (r) { return r.f_submitted; }) },
          { label: "Publicados", values: top.map(function (r) { return r.f_published; }) },
        ],
        height: 300, file: "equipe-etapas",
        onSelect: function (label) {
          const person = top.find(function (r) {
            return cut(r.short_name || r.full_name, 12) === label; });
          if (person) showResearcher(person.id);
        },
        table: { cols: [{ label: "Integrante", k: "full_name" },
          { label: "Em produção", k: "f_progress", num: true },
          { label: "Submetidos", k: "f_submitted", num: true },
          { label: "Publicados", k: "f_published", num: true }], rows: top },
      })));
    /* realizado contra a média do laboratório: quem está acima e quem está abaixo */
    if (counts.length > 1) {
      const meta = Math.round(10 * counts.reduce(function (acc, r) { return acc + r.f_total; }, 0)
        / counts.length) / 10;
      host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
        card("Cada um contra a média do laboratório",
          "A barra é o que a pessoa tem; o traço, a média de " + dec(meta, 1) + " artigo(s).",
          C.bullet({
            items: top.map(function (r) {
              return { label: r.short_name || r.full_name, value: r.f_total, target: meta,
                max: top[0].f_total, onClick: function () { showResearcher(r.id); } };
            }),
            file: "equipe-meta",
            table: { cols: [{ label: "Integrante", k: "full_name" },
              { label: "Artigos", k: "f_total", num: true }], rows: top },
          })),
        card("Índice h e produção", "Duas medidas que costumam andar juntas — quando não andam, vale olhar.",
          C.scatter({
            points: counts.filter(function (r) { return r.h_index; }).map(function (r) {
              return { x: r.f_total, y: r.h_index, label: r.short_name || r.full_name,
                onSelect: function () { showResearcher(r.id); } };
            }),
            xLabel: "artigos no recorte", yLabel: "índice h", height: 280, file: "h-producao",
            emptyMessage: "Nenhum índice h preenchido ainda. Rode o rastreador na tarefa 'perfis'.",
          })),
      ]));
    }
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Integrantes no recorte", file: "equipe", sortKey: "f_total",
      onRow: function (r) { showResearcher(r.id); },
      cols: [
        { k: "full_name", label: "Integrante", wide: true, render: function (r) {
          return el("div", {}, [r.full_name,
            el("small", { text: [r.role, r.research_line].filter(Boolean).join(" · ") || "—" })]); } },
        { k: "f_total", label: "Artigos", num: true },
        { k: "f_progress", label: "Em produção", num: true },
        { k: "f_submitted", label: "Submetidos", num: true },
        { k: "f_published", label: "Publicados", num: true },
        { k: "n_projects", label: "Projetos", num: true },
        { k: "h_index", label: "Índice h", num: true },
      ],
      rows: counts, emptyMessage: "Ninguém corresponde aos filtros atuais.",
    })));
  });

view("rede", "Colaboração", "Métricas internas",
  "Cada nó é um integrante; a espessura da linha é o número de artigos em coautoria.",
  function (host) {
    const net = D.network;
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Pessoas na rede", value: C.fmt(net.n_nodes), foot: "com ao menos um artigo" }),
      kpi({ label: "Pares em coautoria", value: C.fmt(net.n_edges), foot: "ligações distintas" }),
      kpi({ label: "Densidade", value: dec(net.density, 3), foot: "0 = isolados · 1 = todos com todos" }),
      kpi({ label: "Grau médio", value: dec(net.mean_degree, 2), foot: "coautores por pessoa" }),
    ]));
    host.appendChild(el("div", { style: "margin-top:16px" }, card(null, null, C.network({
      nodes: net.nodes.map(function (n) {
        return { id: n.id, label: n.name, weight: n.articles, degree: n.degree,
          group: n.is_external ? 1 : 0, onSelect: function () { showResearcher(n.id); } }; }),
      links: net.edges.map(function (e) {
        return { source: e.source, target: e.target, weight: e.weight }; }),
      groups: ["Integrante do LAPE", "Colaborador externo"], unit: "artigos", file: "rede",
    }))));
    if (net.top_pairs.length) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Duplas mais produtivas", "Pares com maior número de artigos em comum.",
        C.bars({
          items: net.top_pairs.map(function (p, i) {
            return { label: p.a + " + " + p.b, value: p.weight, rank: i + 1 }; }),
          mono: true, labelWidth: 260, labelChars: 34, unit: "artigo(s) em comum", file: "duplas",
        }))));
    }
  });

view("tempos", "Tempos do ciclo", "Métricas internas",
  "Quanto tempo cada etapa leva, do início do artigo até a publicação.", function (host) {
    const rows = articles();
    const grupos = [
      { label: "Início → publicação", key: "days_start_to_publication" },
      { label: "Submissão → aceite", key: "days_submission_to_acceptance" },
      { label: "Aceite → publicação", key: "days_acceptance_to_publication" },
    ].map(function (g) {
      return { label: g.label, values: rows.map(function (a) { return a[g.key]; })
        .filter(function (v) { return v !== null && v !== undefined; }).map(Number) };
    });
    const comDados = grupos.filter(function (g) { return g.values.length; });
    const ICONE = ["relogio", "submissao", "aceite"];
    host.appendChild(el("div", { class: "grid g3" }, grupos.map(function (g, i) {
      return kpi({ label: g.label, icon: ICONE[i],
        value: g.values.length ? dur(median(g.values)) : "—",
        foot: g.values.length ? g.values.length + " artigo(s) com as duas datas" : "sem dados" });
    })));

    /* Cascata do ciclo. Só entram os artigos com as quatro datas: aí as médias
       das etapas somam exatamente a média do total, e a leitura fecha. */
    const completos = rows.filter(function (a) {
      return a.started_on && a.first_submission_on && a.accepted_on && a.published_on;
    });
    if (completos.length) {
      const dias = function (de, ate) {
        return Math.round((new Date(ate) - new Date(de)) / 86400000);
      };
      const medio = function (fn) {
        return Math.round(completos.reduce(function (acc, a) { return acc + fn(a); }, 0)
          / completos.length);
      };
      const etapas = [
        { label: "Escrita", value: medio(function (a) { return dias(a.started_on, a.first_submission_on); }) },
        { label: "Revisão", value: medio(function (a) { return dias(a.first_submission_on, a.accepted_on); }) },
        { label: "Produção", value: medio(function (a) { return dias(a.accepted_on, a.published_on); }) },
      ];
      etapas.push({ label: "Total", value: etapas.reduce(function (acc, e) { return acc + e.value; }, 0),
        total: true });
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Onde o tempo é gasto", "Média de dias por etapa nos " + completos.length
        + " artigo(s) com as quatro datas preenchidas — por isso as etapas somam o total.",
        C.waterfall({ items: etapas, height: 260, file: "cascata-do-ciclo",
          table: { cols: [{ label: "Etapa", k: "label" }, { label: "Dias", k: "value", num: true }],
            rows: etapas } }))));
    }
    host.appendChild(el("div", { style: "margin-top:16px" }, card(
      "Distribuição de cada etapa", "Caixa: intervalo interquartil. Traço: mediana. Pontos: artigos.",
      comDados.length ? C.distribution({ groups: comDados, labelWidth: 200, file: "tempos" })
        : C.empty("Preencha as datas de início, submissão, aceite e publicação."))));
    const valores = grupos[0].values;
    if (valores.length) {
      const bins = [[0, 180, "< 6 meses"], [180, 365, "6-12 meses"], [365, 730, "1-2 anos"],
        [730, 1095, "2-3 anos"], [1095, Infinity, "> 3 anos"]];
      host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
        card("Do início à publicação", "Quantos artigos em cada faixa de tempo.",
          C.columns({ labels: bins.map(function (b) { return b[2]; }),
            series: [{ label: "Artigos", values: bins.map(function (b) {
              return valores.filter(function (v) { return v >= b[0] && v < b[1]; }).length; }),
              color: C.token("--series-1") }],
            height: 240, file: "faixas-tempo" })),
        card("Tentativas × tempo", "Quantas submissões cada artigo exigiu e quanto tempo levou.",
          C.scatter({
            points: rows.filter(function (a) { return a.days_start_to_publication; })
              .map(function (a) {
                return { x: a.submission_attempts || 0, y: Math.round(a.days_start_to_publication),
                  label: cut(a.title, 60), onSelect: function () { showArticle(a); } }; }),
            xLabel: "tentativas de submissão", yLabel: "dias até publicar", height: 280,
            file: "tentativas-tempo" })),
      ]));
    }
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Artigos publicados ou aceitos", file: "tempos-artigos", sortKey: "published_on",
      onRow: showArticle,
      cols: [
        { k: "title", label: "Artigo", wide: true },
        { k: "journal", label: "Revista" },
        { k: "started_on", label: "Início", render: function (r) { return dt(r.started_on); } },
        { k: "first_submission_on", label: "1ª submissão",
          render: function (r) { return dt(r.first_submission_on); } },
        { k: "accepted_on", label: "Aceite", render: function (r) { return dt(r.accepted_on); } },
        { k: "published_on", label: "Publicação", render: function (r) { return dt(r.published_on); } },
        { k: "days_start_to_publication", label: "Início→pub.", num: true,
          render: function (r) { return dur(r.days_start_to_publication); } },
        { k: "submission_attempts", label: "Tentativas", num: true },
      ],
      rows: rows.filter(function (a) { return a.status === "publicado" || a.status === "aceito"; }),
      emptyMessage: "Nenhum artigo publicado ou aceito neste recorte.",
    })));
  });

view("submissoes", "Submissões e recusas", "Métricas internas",
  "Histórico de envios: quantas tentativas cada artigo exigiu, o intervalo entre elas e por que foi recusado.",
  function (host) {
    const sub = D.submissions;
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Submissões", value: C.fmt(sub.total), foot: "tentativas registradas" }),
      kpi({ label: "Taxa de aceite", value: dec(sub.acceptance_rate, 1) + "%",
        foot: sub.accepted + " aceite(s)" }),
      kpi({ label: "Taxa de recusa", value: dec(sub.rejection_rate, 1) + "%",
        foot: sub.rejected + " recusa(s)" }),
      kpi({ label: "Recusas sem revisão", value: C.fmt(sub.desk_rejects), foot: "desk rejection" }),
    ]));
    const fluxo = fluxoSubmissoes();
    if (fluxo) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "O caminho das submissões", "Da situação do artigo para a revista, e da revista para a decisão.",
        fluxo)));
    }
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Tentativas por artigo", "Quantos envios cada manuscrito exigiu.",
        C.columns({
          labels: sub.attempts_distribution.map(function (d) { return d.attempts + "×"; }),
          series: [{ label: "Artigos", values: sub.attempts_distribution.map(function (d) { return d.n; }),
            color: C.token("--series-1") }],
          height: 230, file: "tentativas" })),
      card("Decisões editoriais", null, C.donut({
        items: sub.decisions.map(function (d) {
          return { label: DECISION_LABEL[d.decision] || d.decision, value: d.n }; }),
        unit: "decisões", file: "decisoes" })),
    ]));
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Motivos das recusas", "Vem da coluna “Motivo/observação” das tentativas.",
        sub.rejection_reasons.length ? C.bars({
          items: sub.rejection_reasons.map(function (r, i) {
            return { label: r.reason, value: r.n, rank: i + 1, note: r.category }; }),
          mono: true, labelWidth: 260, labelChars: 36, unit: "recusa(s)", file: "motivos-recusa",
        }) : C.empty("Nenhuma recusa com motivo registrado.")),
      card("Intervalo entre submissões", "Quanto tempo entre uma decisão e o novo envio.",
        sub.gaps.length ? C.distribution({
          groups: [
            { label: "Entre submissões", values: sub.gaps.map(function (g) {
              return g.days_between_submissions; }).filter(Boolean) },
            { label: "Decisão → reenvio", values: sub.gaps.map(function (g) {
              return g.days_decision_to_resubmission; }).filter(Boolean) },
          ],
          labelWidth: 185, file: "intervalos",
        }) : C.empty("Registre ao menos duas tentativas para o mesmo artigo.")),
    ]));
    if (sub.per_journal.length) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Revistas mais utilizadas", "Aceites e recusas por periódico.",
        C.columns({
          mode: "agrupado",
          labels: sub.per_journal.slice(0, 8).map(function (j) { return cut(j.journal, 14); }),
          series: [
            { label: "Aceitas", values: sub.per_journal.slice(0, 8).map(function (j) { return j.accepted; }) },
            { label: "Recusadas", values: sub.per_journal.slice(0, 8).map(function (j) { return j.rejected; }) },
          ],
          height: 260, file: "revistas",
          table: { cols: [{ label: "Revista", k: "journal" }, { label: "Submissões", k: "n", num: true },
            { label: "Aceitas", k: "accepted", num: true }, { label: "Recusadas", k: "rejected", num: true }],
            rows: sub.per_journal },
        }))));
    }
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Tentativas por artigo", file: "tentativas-artigo", sortKey: "attempts",
      cols: [
        { k: "title", label: "Artigo", wide: true },
        { k: "attempts", label: "Tentativas", num: true },
        { k: "rejections", label: "Recusas", num: true },
        { k: "first_submitted_on", label: "1ª submissão",
          render: function (r) { return dt(r.first_submitted_on); } },
        { k: "last_submitted_on", label: "Última", render: function (r) { return dt(r.last_submitted_on); } },
        { k: "status", label: "Situação", render: function (r) { return badge(r.status); } },
      ],
      rows: sub.per_article, emptyMessage: "Nenhuma submissão registrada.",
    })));
  });

function fluxoSubmissoes() {
  const sub = D.submissions;
  if (!sub.per_journal.length) return null;
  const revistas = sub.per_journal.slice(0, 6);
  const nodes = [{ id: "envio", label: "Submissões", depth: 0, color: C.token("--series-1") }];
  const links = [];
  revistas.forEach(function (j, i) {
    nodes.push({ id: "j" + i, label: cut(j.journal, 24), depth: 1, color: C.serie(i % 8) });
    links.push({ source: "envio", target: "j" + i, value: j.n, group: i % 8 });
  });
  const desfechos = [
    { id: "aceito", label: "Aceito", color: C.token("--good"),
      get: function (j) { return j.accepted; } },
    { id: "recusado", label: "Recusado", color: C.token("--critical"),
      get: function (j) { return j.rejected; } },
    { id: "aguardando", label: "Em avaliação", color: C.token("--warning"),
      get: function (j) { return Math.max(0, j.n - j.accepted - j.rejected); } },
  ];
  desfechos.forEach(function (d) {
    if (revistas.reduce(function (a, j) { return a + d.get(j); }, 0) > 0) {
      nodes.push({ id: d.id, label: d.label, depth: 2, color: d.color });
    }
  });
  revistas.forEach(function (j, i) {
    desfechos.forEach(function (d) {
      const v = d.get(j);
      if (v > 0) links.push({ source: "j" + i, target: d.id, value: v, group: i % 8 });
    });
  });
  return C.sankey({ nodes: nodes, links: links, unit: "submissão(ões)", height: 330,
    file: "fluxo-submissoes",
    table: { cols: [{ label: "Revista", k: "journal" }, { label: "Submissões", k: "n", num: true },
      { label: "Aceitas", k: "accepted", num: true }, { label: "Recusadas", k: "rejected", num: true }],
      rows: sub.per_journal } });
}

view("aceites", "Aceites", "Métricas internas",
  "Aceites registrados, com o tempo decorrido desde a primeira submissão.", function (host) {
    const rows = D.acceptances || [];
    const comTempo = rows.filter(function (r) { return r.days_submission_to_acceptance; });
    if (comTempo.length) {
      host.appendChild(card("Da submissão ao aceite", "Cada linha é um artigo.",
        C.dumbbell({
          items: comTempo.slice(0, 14).map(function (r) {
            return { label: cut(r.title, 34), from: 0,
              to: Math.round(r.days_submission_to_acceptance) }; }),
          fromLabel: "submissão", toLabel: "aceite", labelWidth: 260, file: "aceites" })));
    }
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Aceites", file: "aceites", sortKey: "accepted_on",
      cols: [
        { k: "title", label: "Artigo", wide: true },
        { k: "authors", label: "Autores", render: function (r) { return cut(r.authors, 38); } },
        { k: "journal", label: "Revista" },
        { k: "first_submission_on", label: "1ª submissão",
          render: function (r) { return dt(r.first_submission_on); } },
        { k: "accepted_on", label: "Aceite", render: function (r) { return dt(r.accepted_on); } },
        { k: "published_on", label: "Publicação", render: function (r) { return dt(r.published_on); } },
        { k: "days_submission_to_acceptance", label: "Submissão→aceite", num: true,
          render: function (r) { return dur(r.days_submission_to_acceptance); } },
        { k: "submission_attempts", label: "Tentativas", num: true },
      ],
      rows: rows, emptyMessage: "Nenhum aceite registrado ainda.",
    })));
  });

view("calendario", "Calendário", "Espaço-temporal",
  "Reuniões, coletas, defesas e eventos científicos do laboratório.", function (host) {
    const ag = D.agenda;
    const state = { ref: new Date() };
    const calCard = el("div", { class: "card" });
    const byDay = {};
    ag.events.forEach(function (e) {
      const key = String(e.start_at).slice(0, 10);
      (byDay[key] = byDay[key] || []).push(e);
    });
    function drawCal() {
      calCard.innerHTML = "";
      const y = state.ref.getFullYear(), m = state.ref.getMonth();
      calCard.appendChild(el("div", { class: "calhead" }, [
        el("button", { type: "button", text: "‹", "aria-label": "Mês anterior",
          onclick: function () { state.ref = new Date(y, m - 1, 1); drawCal(); } }),
        el("h3", { text: C.MESES[m].toUpperCase() + " " + y }),
        el("button", { type: "button", text: "›", "aria-label": "Próximo mês",
          onclick: function () { state.ref = new Date(y, m + 1, 1); drawCal(); } }),
      ]));
      const grid = el("div", { class: "cal" });
      DOW.forEach(function (d) { grid.appendChild(el("div", { class: "dow", text: d })); });
      const first = new Date(y, m, 1).getDay();
      const daysInMonth = new Date(y, m + 1, 0).getDate();
      const prevDays = new Date(y, m, 0).getDate();
      const today = new Date();
      for (let i = 0; i < first; i++) {
        grid.appendChild(el("div", { class: "day out", text: String(prevDays - first + i + 1) }));
      }
      for (let d = 1; d <= daysInMonth; d++) {
        const key = y + "-" + String(m + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0");
        const evts = byDay[key] || [];
        const isToday = today.getFullYear() === y && today.getMonth() === m && today.getDate() === d;
        grid.appendChild(el("div", {
          class: "day" + (evts.length ? " has" : "") + (isToday ? " today" : ""),
          title: evts.length ? evts.map(function (e) {
            return (KIND_LABEL[e.kind] || e.kind) + ": " + e.title; }).join("\n") : null,
        }, [String(d), evts.length ? el("em", { text: "•".repeat(Math.min(evts.length, 3)) }) : null]));
      }
      calCard.appendChild(grid);
    }
    drawCal();
    const agendaList = el("ul", { class: "agenda" }, ag.upcoming.map(function (e) {
      const iso = String(e.start_at);
      return el("li", {}, [
        el("div", { class: "when" }, [el("b", { text: iso.slice(8, 10) }),
          C.MESES[Number(iso.slice(5, 7)) - 1]]),
        el("div", { class: "what" }, [e.title, el("small", { text:
          [KIND_LABEL[e.kind] || e.kind, dtm(e.start_at), e.location_name || e.city,
           e.n_participants ? e.n_participants + " participantes" : null]
            .filter(Boolean).join(" · ") })]),
      ]);
    }));
    host.appendChild(el("div", { class: "grid g2" }, [
      calCard,
      card("Próximas atividades", null, ag.upcoming.length ? agendaList
        : el("div", { class: "empty", html: "Nenhuma atividade futura. Cadastre em "
          + "<a href='/app#eventos'>Área do integrante → Atividades</a>." })),
    ]));
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Atividades por tipo", null, C.bars({
        items: ag.by_kind.map(function (d) {
          return { label: KIND_LABEL[d.kind] || d.kind, value: d.n }; }),
        labelWidth: 160, unit: "atividade(s)", file: "atividades-tipo" })),
      card("Atividades por ano", null, C.columns({
        labels: ag.by_year.map(function (d) { return d.year; }),
        series: [{ label: "Atividades", values: ag.by_year.map(function (d) { return d.n; }),
          color: C.token("--series-1") }],
        height: 240, file: "atividades-ano",
        onSelect: function (label) { anoCal(Number(label)); } })),
    ]));

    /* o ano inteiro numa tela só: onde o laboratório concentrou atividade */
    const anos = Array.from(new Set(ag.events.map(function (e) {
      return Number(String(e.start_at).slice(0, 4)); }))).filter(Boolean).sort();
    const heatBox = el("div", { style: "margin-top:16px" });
    host.appendChild(heatBox);
    let anoAtivo = anos.length ? anos[anos.length - 1] : new Date().getFullYear();
    function anoCal(ano) {
      if (ano) anoAtivo = ano;
      heatBox.innerHTML = "";
      const dias = {};
      ag.events.forEach(function (e) {
        const iso = String(e.start_at).slice(0, 10);
        if (Number(iso.slice(0, 4)) === anoAtivo) dias[iso] = (dias[iso] || 0) + 1;
      });
      const seletor = el("div", { class: "segmented" }, anos.map(function (a) {
        return el("button", { type: "button", text: String(a),
          class: a === anoAtivo ? "on" : null, onclick: function () { anoCal(a); } });
      }));
      heatBox.appendChild(card("O ano em um quadro",
        "Um quadrado por dia; quanto mais escuro, mais atividades naquele dia.",
        el("div", {}, [
          anos.length > 1 ? el("div", { style: "margin-bottom:12px" }, seletor) : null,
          C.calendarHeat({
            year: anoAtivo, days: dias, unit: "atividade(s)", file: "calendario-" + anoAtivo,
            onPick: function (iso) {
              const doDia = byDay[iso] || [];
              if (doDia.length) {
                openDrawer(dt(iso), el("div", {}, [
                  el("p", { class: "drawer-sub",
                    text: doDia.length + " atividade(s) neste dia." }),
                  el("ul", { class: "agenda" }, doDia.map(function (e) {
                    return el("li", {}, [
                      el("div", { class: "what" }, [e.title, el("small", { text:
                        [KIND_LABEL[e.kind] || e.kind, dtm(e.start_at),
                         e.location_name || e.city].filter(Boolean).join(" · ") })]),
                    ]);
                  })),
                ]));
              }
            },
            emptyMessage: "Nenhuma atividade registrada em " + anoAtivo + ".",
          }),
        ])));
    }
    if (anos.length) anoCal(null);
  });

view("temporal", "Linha do tempo", "Espaço-temporal",
  "Distribuição mês a mês de publicações, submissões e atividades.", function (host) {
    const t = D.temporal;
    const camadas = [
      { key: "publications", label: "Publicações", unit: "publicação(ões)" },
      { key: "submissions", label: "Submissões", unit: "submissão(ões)" },
      { key: "activities", label: "Atividades", unit: "atividade(s)" },
    ];
    host.appendChild(card("Mapa de calor ano × mês", null,
      tabbed(camadas.map(function (layer) {
        return { label: layer.label, content: C.heatmap({
          years: t.years, values: t[layer.key], unit: layer.unit, file: "calor-" + layer.key,
          caption: layer.label + " por mês. Tom mais escuro, mais registros.",
        }) };
      }))));
    const totais = camadas.map(function (layer) {
      return { label: layer.label, values: t.years.map(function (_, r) {
        return t[layer.key].slice(r * 12, r * 12 + 12)
          .reduce(function (a, b) { return a + b; }, 0); }) };
    });
    host.appendChild(el("div", { style: "margin-top:16px" }, card(
      "Evolução anual comparada", "As três séries no mesmo eixo, para comparação direta.",
      C.lines({ labels: t.years.map(String), series: totais, height: 280,
        file: "evolucao-anual" }))));

    const hist = (D.history && D.history.series) || {};
    const medidas = ["artigos", "publicados", "submissoes", "citacoes"]
      .filter(function (m) { return hist[m] && hist[m].values.length > 1; });
    if (medidas.length) {
      host.appendChild(el("div", { style: "margin-top:16px" }, card(
        "Histórico medido dos indicadores",
        "Cada ponto é uma execução do lakehouse — número medido, não estimado.",
        C.lines({
          labels: hist[medidas[0]].dates.map(function (d) { return dt(d).slice(0, 5); }),
          series: medidas.map(function (m) {
            return { label: m.charAt(0).toUpperCase() + m.slice(1), values: hist[m].values }; }),
          height: 260, file: "historico-indicadores" }))));
    }
  });

view("espacial", "Mapa", "Espaço-temporal",
  "Onde as atividades acontecem e de onde vêm as instituições parceiras.", function (host) {
    const sp = D.spatial;
    host.appendChild(el("div", { class: "grid g2" }, [
      card("Mapa de atividades", "O tamanho do círculo é o número de atividades no local.",
        C.geo({
          points: sp.geolocated.map(function (p) {
            return { lat: p.latitude, lon: p.longitude, value: p.n_events,
              label: p.city + (p.state ? "/" + p.state : "") }; }),
          outline: D.geo, unit: "atividade(s)", file: "mapa" })),
      card("Locais", "Cidades com atividades registradas.", dataTable({
        search: false, pageSize: 10, sortKey: "n_events", file: "locais",
        cols: [{ k: "city", label: "Cidade" }, { k: "state", label: "UF" },
          { k: "country", label: "País" }, { k: "n_events", label: "Atividades", num: true }],
        rows: sp.places, emptyMessage: "Nenhum local registrado." })),
    ]));
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Instituições", file: "instituicoes", sortKey: "n_articles",
      cols: [
        { k: "name", label: "Instituição", wide: true, render: function (r) {
          return el("div", {}, [r.name,
            el("small", { text: [r.city, r.state, r.country].filter(Boolean).join(" · ") })]); } },
        { k: "acronym", label: "Sigla" },
        { k: "n_members", label: "Integrantes", num: true },
        { k: "n_articles", label: "Artigos", num: true },
      ],
      rows: sp.institutions, emptyMessage: "Nenhuma instituição cadastrada.",
    })));
  });

view("descobertas", "Achados", "Governança",
  "Publicações encontradas nas bases externas que ainda não estão no banco.", function (host) {
    const rows = D.discoveries || [];
    if (!rows.length) {
      host.appendChild(el("div", { class: "note", html:
        "<b>Nenhum achado pendente.</b> Rode o rastreador em "
        + (LIVE ? "<a href='/app#admin'>Área do integrante → Administração</a>"
          : "<span class='mono'>python3 scripts/lape_agent.py rastreador descobrir</span>") + "." }));
      return;
    }
    host.appendChild(el("div", { class: "note", html: LIVE
      ? "Aprove ou descarte cada achado em <a href='/app#admin'>Administração</a>."
      : "Para aprovar: <span class='mono'>python3 scripts/lape_agent.py revisar --aceitar "
        + rows[0].id + "</span>" }));
    host.appendChild(el("div", { style: "margin-top:16px" }, dataTable({
      title: "Pendentes", file: "achados", sortKey: "citations",
      cols: [
        { k: "id", label: "ID", num: true },
        { k: "title", label: "Título", wide: true, render: function (r) {
          return el("div", {}, [
            r.url ? el("a", { href: r.url, target: "_blank", rel: "noopener", text: r.title }) : r.title,
            el("small", { text: [r.journal, r.authors ? cut(r.authors, 64) : null]
              .filter(Boolean).join(" · ") })]); } },
        { k: "year", label: "Ano", num: true },
        { k: "citations", label: "Citações", num: true },
        { k: "source", label: "Fonte" },
      ],
      rows: rows,
    })));
  });

view("qualidade", "Qualidade", "Governança",
  "Lacunas que limitam as análises e de onde veio cada carga.", function (host) {
    const q = D.quality;
    const pendentes = q.issues.filter(function (i) { return i.n > 0; });
    host.appendChild(el("div", { class: "grid g4" }, [
      kpi({ label: "Verificações", value: C.fmt(q.issues.length), foot: "campos monitorados" }),
      kpi({ label: "Sem pendência", value: C.fmt(q.issues.length - pendentes.length),
        foot: "de " + q.issues.length }),
      kpi({ label: "Com lacuna", value: C.fmt(pendentes.length), foot: "precisam de preenchimento" }),
      kpi({ label: "Medições no histórico",
        value: C.fmt((D.history && D.history.snapshots) || 0), foot: "execuções do lakehouse" }),
    ]));
    host.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
      card("Campos a completar", "Quanto menor, mais completo o banco.",
        pendentes.length ? C.bars({
          items: pendentes.map(function (i) { return { label: i.label, value: i.n }; }),
          mono: true, labelWidth: 290, labelChars: 42, unit: "registro(s)", file: "lacunas",
        }) : el("div", { class: "empty", text: "Nenhuma lacuna. Banco completo." })),
      card("Últimas cargas", "Cada leitura de arquivo e chamada de API.", C.table(
        [{ label: "Quando", get: function (r) { return dtm(r.run_at); } },
         { label: "Fonte", k: "source" }, { label: "Destino", k: "target" },
         { label: "Lidas", k: "rows_read", num: true },
         { label: "Gravadas", k: "rows_written", num: true },
         { label: "Status", k: "status" }],
        q.last_runs)),
    ]));
    if (LIVE) {
      const box = el("div", { style: "margin-top:16px" });
      host.appendChild(box);
      fetch("/api/lake/lineage?limite=40").then(function (r) {
        return r.ok ? r.json() : null;
      }).then(function (data) {
        if (!data || !data.items.length) return;
        box.appendChild(card("Linhagem — de onde veio cada arquivo",
          "A camada bronze guarda o arquivo cru com a impressão digital (sha256), "
          + "para que qualquer carga possa ser refeita.",
          dataTable({
            search: false, pageSize: 12, file: "linhagem",
            cols: [
              { k: "captured_at", label: "Quando", render: function (r) { return dtm(r.captured_at); } },
              { k: "layer", label: "Camada" },
              { k: "source_path", label: "Origem", wide: true },
              { k: "rows", label: "Linhas", num: true },
              { k: "bytes", label: "Bytes", num: true },
              { k: "sha256", label: "sha256", render: function (r) {
                return r.sha256 ? el("span", { class: "mono", text: r.sha256.slice(0, 12) }) : "—"; } },
            ],
            rows: data.items,
          })));
      }).catch(function () { /* sem linhagem, sem problema */ });
    }
  });

view("automacao", "Automação", "Governança",
  "Os eventos que o LAPE emite, para onde eles vão e o que voltou de cada entrega.",
  function (host) {
    if (!LIVE) {
      host.appendChild(el("div", { class: "note",
        text: "Esta aba lê o servidor em tempo real. No arquivo exportado ela fica vazia — "
          + "abra o painel publicado para cadastrar e conferir os webhooks." }));
      return;
    }
    const box = el("div");
    host.appendChild(box);
    box.appendChild(el("div", { class: "empty", text: "Consultando a automação…" }));

    function post(url, body) {
      return fetch(url, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      }).then(function (r) {
        return r.json().then(function (data) {
          if (!r.ok) throw new Error(data.error || ("HTTP " + r.status));
          return data;
        });
      });
    }
    function load() {
      fetch("/api/automation?limite=60", { headers: { Accept: "application/json" } })
        .then(function (r) {
          if (r.status === 401 || r.status === 403) throw new Error("permissao");
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(draw)
        .catch(function (err) {
          box.innerHTML = "";
          box.appendChild(el("div", { class: "note", text: err.message === "permissao"
            ? "Só a coordenação vê a automação. Entre com um login de coordenação para cadastrar webhooks."
            : "Não foi possível ler a automação agora: " + err.message }));
        });
    }

    function draw(a) {
      box.innerHTML = "";
      const falhas = a.deliveries.filter(function (d) { return d.status !== "ok"; }).length;
      const ativos = a.webhooks.filter(function (w) { return w.active; }).length;
      box.appendChild(el("div", { class: "grid g4" }, [
        kpi({ label: "Destinos ativos", value: C.fmt(ativos), icon: "conectar",
          foot: a.webhooks.length + " cadastrado(s)" }),
        kpi({ label: "Eventos no catálogo", value: C.fmt(a.events.length), icon: "raio",
          foot: "assine '*' para receber todos" }),
        kpi({ label: "Entregas com erro", value: C.fmt(falhas), icon: "aviso",
          foot: "nas últimas " + a.deliveries.length + " tentativas",
          tone: falhas ? "bad" : "good" }),
        kpi({ label: "Painéis ao vivo", value: C.fmt(a.subscribers), icon: "atualizar",
          foot: a.signing ? "mensagens assinadas" : "sem segredo configurado" }),
      ]));

      /* cadastro — o mesmo que o curl do README faz, sem linha de comando */
      const nome = el("input", { class: "search", placeholder: "n8n — publicações", value: "n8n" });
      const url = el("input", { class: "search", placeholder: "https://n8n.exemplo/webhook/lape" });
      const evento = el("select", {}, [el("option", { value: "*", text: "* — todos os eventos" })]
        .concat(a.events.map(function (e) {
          return el("option", { value: e.id, text: e.id + " — " + e.label });
        })));
      const aviso = el("div", { class: "note", style: "display:none" });
      const enviar = el("button", { class: "primary", type: "button", text: "Cadastrar webhook",
        onclick: function () {
          if (!url.value.trim()) { url.focus(); return; }
          enviar.disabled = true;
          post("/api/webhooks", { nome: nome.value, url: url.value.trim(), evento: evento.value })
            .then(function () { url.value = ""; load(); })
            .catch(function (err) {
              aviso.style.display = "";
              aviso.textContent = "Não deu para cadastrar: " + err.message;
            })
            .finally(function () { enviar.disabled = false; });
        } });
      box.appendChild(el("div", { style: "margin-top:16px" }, card("Ligar o LAPE a um fluxo do n8n",
        "Copie a URL de produção do nó de webhook no n8n e cole aqui. "
        + "O corpo vai assinado em X-LAPE-Signature — confira a assinatura antes de agir.",
        el("div", {}, [
          el("div", { class: "explorer-controls" }, [
            el("div", { class: "field" }, [el("label", { text: "Nome" }), nome]),
            el("div", { class: "field", style: "flex:2" }, [el("label", { text: "URL do webhook" }), url]),
            el("div", { class: "field" }, [el("label", { text: "Evento" }), evento]),
            enviar,
          ]),
          aviso,
        ]))));

      const destinos = a.webhooks.length ? dataTable({
        search: false, pageSize: 10, file: "webhooks",
        cols: [
          { k: "name", label: "Nome" },
          { k: "url", label: "Destino", wide: true },
          { k: "event", label: "Evento" },
          { k: "deliveries", label: "Entregas", num: true },
          { k: "last_status", label: "Última", render: function (r) {
            return el("span", { class: "badge " + (r.last_status === "ok" ? "s-publicado" : "s-rejeitado"),
              text: r.last_status || "sem envio" });
          } },
          { k: "id", label: "", render: function (r) {
            return el("div", { style: "display:flex;gap:6px" }, [
              el("button", { type: "button", text: "Testar", onclick: function (ev) {
                ev.stopPropagation();
                ev.target.disabled = true;
                post("/api/webhooks/" + r.id + "/testar").then(load)
                  .catch(function () { ev.target.disabled = false; });
              } }),
              el("button", { type: "button", text: "Remover", onclick: function (ev) {
                ev.stopPropagation();
                if (!confirm("Remover o destino \"" + r.name + "\"?")) return;
                post("/api/webhooks/" + r.id + "/remover").then(load);
              } }),
            ]);
          } },
        ],
        rows: a.webhooks,
      }) : el("div", { class: "empty",
        text: "Nenhum destino cadastrado. O LAPE segue funcionando — o n8n é opcional." });

      /* o histórico auditável: é dele que o painel ao vivo se alimenta */
      const porEvento = counter(a.recent, "event");

      /* a tabela de destinos tem colunas demais para meia largura: fica inteira */
      box.appendChild(el("div", { style: "margin-top:16px" },
        card("Destinos cadastrados", "Para onde cada evento é enviado.", destinos)));
      box.appendChild(el("div", { class: "grid g2", style: "margin-top:16px" }, [
        card("Últimas entregas", "Três tentativas com espera crescente; falha não trava cadastro.",
          a.deliveries.length ? dataTable({
            search: false, pageSize: 10, file: "entregas",
            cols: [
              { k: "at", label: "Quando", render: function (r) { return dtm(r.at); } },
              { k: "webhook", label: "Destino" },
              { k: "event", label: "Evento" },
              { k: "status", label: "Status", render: function (r) {
                return el("span", { class: "badge " + (r.status === "ok" ? "s-publicado" : "s-rejeitado"),
                  text: r.status + (r.http_code ? " " + r.http_code : "") });
              } },
              { k: "attempt", label: "Tent.", num: true },
              { k: "duration_ms", label: "ms", num: true },
              { k: "error", label: "Erro", wide: true },
            ],
            rows: a.deliveries,
          }) : el("div", { class: "empty", text: "Nenhuma entrega ainda." })),
        card("Eventos mais frequentes", "No recorte que o servidor devolveu.",
          porEvento.length ? C.bars({
            items: topN(porEvento, 10), mono: true, labelWidth: 210, labelChars: 30,
            unit: "evento(s)", file: "eventos-frequentes",
          }) : el("div", { class: "empty", text: "Sem eventos registrados." })),
      ]));

      box.appendChild(el("div", { style: "margin-top:16px" },
        card("O que aconteceu no banco", "Cada linha é um evento registrado em change_log.",
          a.recent.length ? dataTable({
            search: true, pageSize: 12, file: "eventos",
            cols: [
              { k: "at", label: "Quando", render: function (r) { return dtm(r.at); } },
              { k: "event", label: "Evento" },
              { k: "entity", label: "Entidade" },
              { k: "detail", label: "Detalhe", wide: true },
              { k: "actor", label: "Quem" },
            ],
            rows: a.recent,
          }) : el("div", { class: "empty", text: "Sem eventos registrados." }))));

      box.appendChild(el("div", { style: "margin-top:16px" }, card("Catálogo de eventos",
        "O n8n pode assinar qualquer um destes nomes — ou '*' para todos.",
        C.table([{ label: "Evento", k: "id" }, { label: "Quando acontece", k: "label" }], a.events))));
    }

    load();
  });

/* abas internas de um cartão */
function tabbed(items) {
  const nav = el("div", { class: "tabs" });
  const panes = el("div");
  items.forEach(function (item, i) {
    const pane = el("div", { class: "tabpane" + (i === 0 ? " on" : "") },
      Array.isArray(item.content) ? item.content : [item.content]);
    const btn = el("button", { type: "button", text: item.label, class: i === 0 ? "on" : null,
      onclick: function () {
        nav.querySelectorAll("button").forEach(function (b) { b.classList.remove("on"); });
        panes.querySelectorAll(".tabpane").forEach(function (p) { p.classList.remove("on"); });
        btn.classList.add("on");
        pane.classList.add("on");
      } });
    nav.appendChild(btn);
    panes.appendChild(pane);
  });
  return el("div", {}, [nav, panes]);
}

function aplicarSegmento(label) {
  if (STATE.segmento === "linha") STATE.linha = label;
  else if (STATE.segmento === "ano" || STATE.segmento === "ano_publicacao") STATE.ano = label;
  else if (STATE.segmento === "status") {
    const found = Object.keys(STATUS_LABEL).find(function (k) { return STATUS_LABEL[k] === label; });
    if (found) STATE.status = found;
  } else return;
  buildToolbar();
  render();
}

/* ==================================================================== */
/* navegação: seis seções com ícone, cada uma com suas sub-abas          */
/* ==================================================================== */
/* Menos abas no primeiro nível e mais profundidade no segundo: a seção
   diz do que se trata, a sub-aba diz qual recorte. Cada sub-aba também
   aponta para as vizinhas de outras seções (ver RELATED), para que a
   leitura siga o assunto e não a estrutura do menu. */
const SECTIONS = [
  { id: "geral", label: "Visão geral", icon: "painel",
    views: ["visao", "explorar"] },
  { id: "producao", label: "Produção", icon: "producao",
    views: ["producao", "submetidos", "publicacoes", "citacoes"] },
  { id: "pessoas", label: "Pessoas", icon: "pessoas",
    views: ["pesquisadores", "organograma", "equipe", "rede", "linhas", "projetos"] },
  { id: "processo", label: "Processo", icon: "processo",
    views: ["tempos", "submissoes", "aceites"] },
  { id: "espaco", label: "Espaço-tempo", icon: "espaco",
    views: ["calendario", "temporal", "espacial"] },
  { id: "dados", label: "Dados", icon: "dados",
    views: ["descobertas", "qualidade", "automacao"] },
];
const VIEW_ICON = {
  visao: "painel", explorar: "explorar",
  producao: "producao", submetidos: "submissao", publicacoes: "livro", citacoes: "citacao",
  pesquisadores: "pessoas", organograma: "hierarquia", equipe: "barras", rede: "rede",
  linhas: "linhas", projetos: "projeto",
  tempos: "relogio", submissoes: "submissao", aceites: "aceite",
  calendario: "calendario", temporal: "tempo", espacial: "mapa",
  descobertas: "achado", qualidade: "qualidade", automacao: "automacao",
};
/* atalhos entre sub-abas de seções diferentes — a ponte que o menu não faz */
const RELATED = {
  visao: ["explorar", "publicacoes", "tempos"],
  explorar: ["equipe", "publicacoes", "qualidade"],
  producao: ["tempos", "equipe", "submetidos"],
  submetidos: ["submissoes", "tempos", "aceites"],
  publicacoes: ["citacoes", "temporal", "equipe"],
  citacoes: ["publicacoes", "pesquisadores", "descobertas"],
  pesquisadores: ["organograma", "equipe", "rede"],
  organograma: ["pesquisadores", "projetos", "linhas"],
  equipe: ["rede", "pesquisadores", "producao"],
  rede: ["equipe", "linhas", "projetos"],
  linhas: ["projetos", "publicacoes", "equipe"],
  projetos: ["linhas", "pesquisadores", "producao"],
  tempos: ["submissoes", "aceites", "producao"],
  submissoes: ["tempos", "aceites", "submetidos"],
  aceites: ["publicacoes", "tempos", "submissoes"],
  calendario: ["temporal", "espacial", "projetos"],
  temporal: ["publicacoes", "calendario", "espacial"],
  espacial: ["calendario", "temporal", "projetos"],
  descobertas: ["citacoes", "qualidade", "automacao"],
  qualidade: ["automacao", "descobertas", "explorar"],
  automacao: ["descobertas", "qualidade", "visao"],
};

/* ordem de leitura do painel inteiro — governa as setas "anterior/próxima" */
const ORDER = SECTIONS.reduce(function (acc, sec) { return acc.concat(sec.views); }, []);
function viewOf(id) { return VIEWS.find(function (v) { return v.id === id; }) || null; }
function sectionOf(id) {
  return SECTIONS.find(function (sec) { return sec.views.indexOf(id) >= 0; }) || SECTIONS[0];
}
function labelOf(id) { const v = viewOf(id); return v ? v.label : id; }

let current = ORDER[0];
const HOST = document.getElementById("view");

/* "/" põe o foco na busca e Esc a esvazia — o par que todo painel de dados
   tem, e que dispensa levar a mão ao mouse para filtrar. O atalho não rouba
   a tecla de quem já está escrevendo num campo. */
document.addEventListener("keydown", function (ev) {
  const alvo = ev.target;
  const escrevendo = alvo && (alvo.tagName === "INPUT" || alvo.tagName === "TEXTAREA"
    || alvo.tagName === "SELECT" || alvo.isContentEditable);
  const campo = document.getElementById("busca");
  if (ev.key === "/" && !escrevendo && campo) {
    ev.preventDefault();
    campo.focus();
    campo.select();
  } else if (ev.key === "Escape" && campo && document.activeElement === campo) {
    campo.value = "";
    STATE.busca = "";
    campo.blur();
    buildToolbar();
    render();
  }
});

function buildNav() {
  const nav = document.getElementById("nav");
  nav.querySelectorAll(".navitem, .railfoot").forEach(function (n) { n.remove(); });
  const active = sectionOf(current);
  SECTIONS.forEach(function (sec) {
    const on = sec.id === active.id;
    const btn = el("button", {
      class: "navitem" + (on ? " active" : ""), type: "button", "data-section": sec.id,
      title: sec.label, "aria-current": on ? "page" : null,
      onclick: function () { go(sec.views[0]); },
    });
    btn.appendChild(Icons.badge(sec.icon, null, null));
    btn.appendChild(el("span", { text: sec.label }));
    btn.appendChild(el("em", { text: String(sec.views.length) }));
    nav.appendChild(btn);
  });
  nav.appendChild(el("div", { class: "railfoot no-print",
    text: "Alt + 1…" + SECTIONS.length + " troca de seção." }));
}

function buildSubnav() {
  const bar = document.getElementById("subnav");
  bar.innerHTML = "";
  const sec = sectionOf(current);
  bar.appendChild(el("span", { class: "secname" }, [Icons.get(sec.icon, 15),
    el("b", { text: sec.label })]));
  sec.views.forEach(function (id) {
    const v = viewOf(id);
    if (!v) return;
    const on = id === current;
    const btn = el("button", {
      class: "subitem" + (on ? " on" : ""), type: "button", "data-view": id,
      "aria-current": on ? "page" : null,
      onclick: function () { go(id); },
    });
    btn.appendChild(Icons.get(VIEW_ICON[id] || "linha", 15));
    btn.appendChild(el("span", { text: v.label }));
    bar.appendChild(btn);
  });
}

function go(id) {
  if (!viewOf(id)) id = ORDER[0];
  current = id;
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  buildNav();
  buildSubnav();
  render();
  window.scrollTo({ top: 0, behavior: "auto" });
}

/* Plotagem sob demanda: só a sub-aba visível é desenhada, com o recorte atual. */
function render() {
  const v = viewOf(current) || VIEWS[0];
  C.hideTip();
  HOST.innerHTML = "";
  const title = el("h2", {});
  title.appendChild(Icons.badge(VIEW_ICON[v.id] || "linha", null, null));
  title.appendChild(el("span", { text: v.label }));
  HOST.appendChild(el("header", { class: "viewhead" }, [
    title,
    v.lead ? el("p", { class: "lead", text: v.lead }) : null,
  ]));
  const body = el("div");
  HOST.appendChild(body);
  try {
    v.render(body);
  } catch (err) {
    body.appendChild(el("div", { class: "note", text: "Falha ao desenhar esta aba: " + err.message }));
    if (window.console) console.error(err);
  }

  /* pontes para o mesmo assunto em outras seções */
  const related = (RELATED[v.id] || []).filter(function (id) { return id !== v.id && viewOf(id); });
  if (related.length) {
    const chips = el("div", { class: "related no-print" },
      [el("span", { class: "flabel", text: "Continue por" })]);
    related.forEach(function (id) {
      const chip = el("button", { type: "button", class: "chip", onclick: function () { go(id); } });
      chip.appendChild(Icons.get(VIEW_ICON[id] || "linha", 14));
      chip.appendChild(el("span", { text: labelOf(id) }));
      chips.appendChild(chip);
    });
    HOST.appendChild(chips);
  }

  const idx = ORDER.indexOf(v.id);
  const prev = ORDER[idx - 1], next = ORDER[idx + 1];
  const back = el("span"), fwd = el("span");
  const nav = el("nav", { class: "secnav no-print", "aria-label": "Navegar entre sub-abas" });
  if (prev) {
    const b = el("button", { type: "button", class: "navbtn",
      onclick: function () { go(prev); } });
    b.appendChild(el("span", { class: "arrow", text: "←" }));
    b.appendChild(el("span", { text: labelOf(prev) }));
    nav.appendChild(b);
  } else nav.appendChild(back);
  if (next) {
    const b = el("button", { type: "button", class: "navbtn",
      onclick: function () { go(next); } });
    b.appendChild(el("span", { text: labelOf(next) }));
    b.appendChild(el("span", { class: "arrow", text: "→" }));
    nav.appendChild(b);
  } else nav.appendChild(fwd);
  HOST.appendChild(nav);
  updateCount();
}

/* ==================================================================== */
/* tempo real                                                            */
/* ==================================================================== */
/* Dois caminhos, na ordem: o servidor empurra por SSE (/api/stream) e o
   painel redesenha no mesmo segundo; se o navegador ou um proxy no meio
   não segurar a conexão, cai para a conferência periódica em /api/state.
   A sondagem nunca é desligada de todo — ela é a rede de proteção. */
const REFRESH_MS = 25000;        /* sem SSE: confere a cada 25 s */
const REFRESH_SLOW_MS = 120000;  /* com SSE: só para não perder nada */
const SETTLE_MS = 700;           /* junta uma rajada de eventos num só redesenho */
let refreshTimer = null;
let settleTimer = null;
let stream = null;
let lastStamp = null;
let autoOn = LIVE;
let streamOn = false;
let lastEvent = null;

function stampOf(state) {
  return [state.articles, state.members, state.submissions, state.events, state.projects,
    state.pending_discoveries,
    (state.last_ingest && state.last_ingest[0] || {}).run_at].join("|");
}
async function checkForUpdates(force) {
  if (!LIVE) return;
  try {
    const response = await fetch("/api/state", { headers: { Accept: "application/json" } });
    if (!response.ok) return;
    const state = await response.json();
    const stamp = stampOf(state);
    if (!force && lastStamp !== null && stamp === lastStamp) { markFresh(state); return; }
    lastStamp = stamp;
    await reload(state);
  } catch (err) { /* rede instável: tenta no próximo ciclo */ }
}
async function reload(state) {
  const app = document.getElementById("app");
  app.classList.add("reloading");   /* segura o desenho anterior — sem esqueleto, sem salto */
  try {
    const response = await fetch("/api/metrics", { headers: { Accept: "application/json" } });
    if (!response.ok) return;
    const fresh = await response.json();
    fresh.session = D.session;
    fresh.geo = D.geo;
    D = fresh;
    indexAuthorship();
    buildToolbar();
    render();
    markFresh(state);
  } finally {
    app.classList.remove("reloading");
  }
}
function markFresh(state) {
  const node = document.getElementById("freshness");
  if (!node) return;
  const now = new Date();
  node.classList.toggle("push", streamOn);
  node.textContent = (streamOn ? "ao vivo" : "conferindo") + " · "
    + String(now.getHours()).padStart(2, "0") + ":"
    + String(now.getMinutes()).padStart(2, "0")
    + (lastEvent ? " · " + lastEvent : "")
    + (state && state.pending_discoveries
      ? " · " + state.pending_discoveries + " achados pendentes" : "");
}

/* Uma rajada (o curador cadastra dez artigos seguidos) vira um redesenho só. */
function settle() {
  clearTimeout(settleTimer);
  settleTimer = setTimeout(function () { checkForUpdates(true); }, SETTLE_MS);
}
function openStream() {
  if (!LIVE || !autoOn || typeof EventSource === "undefined") return;
  try { stream = new EventSource("/api/stream"); } catch (err) { return; }
  stream.addEventListener("pronto", function () {
    streamOn = true;
    startAuto();
    markFresh(null);
  });
  stream.addEventListener("mudanca", function (ev) {
    try {
      const data = JSON.parse(ev.data);
      lastEvent = data.event || null;
    } catch (err) { lastEvent = null; }
    pulse();
    settle();
  });
  stream.addEventListener("error", function () {
    /* o EventSource reconecta sozinho; o que muda aqui é o ritmo da sondagem */
    streamOn = false;
    startAuto();
    markFresh(null);
  });
}
function closeStream() {
  if (stream) { stream.close(); stream = null; }
  streamOn = false;
}
/* sinal de que algo chegou, antes mesmo do redesenho terminar */
function pulse() {
  const node = document.getElementById("freshness");
  if (!node) return;
  node.classList.remove("pulse");
  void node.offsetWidth;
  node.classList.add("pulse");
}

function buildHeader() {
  const o = D.overview;
  document.getElementById("labName").textContent = o.lab_name;
  const meta = document.getElementById("labMeta");
  meta.innerHTML = "";
  [o.institution, "Atualizado em " + o.generated_at, "Janela de " + o.window + " anos"]
    .forEach(function (text) { meta.appendChild(el("span", { class: "pill", text: text })); });
  if (LIVE) meta.appendChild(el("span", { class: "pill live", id: "freshness", text: "ao vivo" }));

  const actions = document.getElementById("actions");
  actions.innerHTML = "";
  if (LIVE) {
    const link = el("a", { href: "/app" });
    link.appendChild(el("button", { class: "primary", type: "button",
      text: USER ? "Área do integrante" : "Entrar" }));
    actions.appendChild(link);
    const tv = el("a", { href: "/mural", target: "_blank", rel: "noopener",
      title: "Tela para projetor ou TV da sala: gira sozinha" });
    tv.appendChild(el("button", { type: "button", text: "Modo mural" }));
    actions.appendChild(tv);
    actions.appendChild(el("button", { type: "button", text: "Atualizar agora",
      onclick: function (ev) {
        ev.target.disabled = true;
        checkForUpdates(true).finally(function () { ev.target.disabled = false; });
      } }));
    const auto = el("button", { type: "button", text: "Tempo real: ligado",
      title: "Receber as mudanças do servidor assim que acontecem",
      onclick: function () {
        autoOn = !autoOn;
        auto.textContent = autoOn ? "Tempo real: ligado" : "Tempo real: desligado";
        if (autoOn) { openStream(); startAuto(); }
        else { closeStream(); clearInterval(refreshTimer); }
        markFresh(null);
      } });
    auto.prepend(Icons.get("raio", 14));
    actions.appendChild(auto);
  }
  actions.appendChild(el("button", { type: "button", text: "Imprimir",
    onclick: function () { print(); } }));
  if (USER) actions.appendChild(el("span", { class: "pill", text: USER.full_name }));

  document.getElementById("foot").textContent =
    "Painel do " + o.lab_name + " gerado em " + o.generated_at
    + ". Fontes: planilhas do laboratório, Currículo Lattes, OpenAlex, Crossref, Scopus e Web of Science.";
}
function startAuto() {
  clearInterval(refreshTimer);
  if (!autoOn) return;
  refreshTimer = setInterval(function () {
    if (document.visibilityState === "visible") checkForUpdates(false);
  }, streamOn ? REFRESH_SLOW_MS : REFRESH_MS);
}

function setupTheme() {
  const toggle = document.getElementById("themeToggle");
  let stored = null;
  try { stored = localStorage.getItem("lape-theme"); } catch (e) { /* janela privada */ }
  if (stored) document.documentElement.setAttribute("data-theme", stored);
  toggle.addEventListener("click", function () {
    const dark = document.documentElement.getAttribute("data-theme") === "dark"
      || (!document.documentElement.getAttribute("data-theme")
        && matchMedia("(prefers-color-scheme:dark)").matches);
    const next = dark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("lape-theme", next); } catch (e) { /* ignora */ }
    render();   /* os gráficos leem as cores dos tokens: basta redesenhar */
  });
}

function boot() {
  buildHeader();
  buildToolbar();
  const asked = (location.hash || "").replace("#", "");
  current = viewOf(asked) ? asked : ORDER[0];
  buildNav();
  buildSubnav();
  render();
  setupTheme();

  document.getElementById("drawerClose").addEventListener("click", closeDrawer);
  document.getElementById("scrim").addEventListener("click", closeDrawer);
  addEventListener("keydown", function (ev) { if (ev.key === "Escape") closeDrawer(); });
  addEventListener("hashchange", function () {
    const id = (location.hash || "").replace("#", "");
    if (id && id !== current) go(id);
  });
  /* teclado: alterna a seção sem tirar a mão do teclado */
  addEventListener("keydown", function (ev) {
    if (ev.altKey && ev.key >= "1" && ev.key <= String(SECTIONS.length)) {
      ev.preventDefault();
      go(SECTIONS[Number(ev.key) - 1].views[0]);
    }
  });
  const toTop = document.getElementById("toTop");
  addEventListener("scroll", function () { toTop.classList.toggle("on", scrollY > 600); });
  toTop.addEventListener("click", function () { scrollTo({ top: 0, behavior: "smooth" }); });

  if (LIVE) { markFresh(null); openStream(); startAuto(); }
  addEventListener("beforeunload", closeStream);
}
boot();
