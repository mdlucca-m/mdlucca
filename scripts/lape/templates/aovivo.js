/* LAPE ao vivo -- o Observatório dentro do LAPE.
 *
 * O desenho é o do Observatório de Evidências que o laboratório montou no
 * Lovable: menu lateral, cartões de vidro, néon, funil em camadas, mapa
 * de calor com lacuna hachurada, insights numerados. Aqui ele é
 * reescrito sem React e sem dependência, e passa a ler os números REAIS
 * do LAPE em vez de um JSON estático.
 *
 * A régua do arquivo continua a mesma: cada número vem com o do período
 * anterior ao lado, cada gráfico responde uma pergunta escrita em cima
 * dele, e as leituras do fim são calculadas -- a tela diz isso, e cada
 * uma traz a regra de onde saiu. O servidor faz a conta toda
 * (`/api/aovivo`); aqui só se desenha. */
"use strict";

const C = Charts;
const el = C.el;

const D = { pronto: false };
const ST = { periodo: "ano", aba: "painel", menuAberto: false, apresentando: false, auto: false };

/* As paletas de fundo. A escolha vai para `lape-paleta` no navegador, que
   é o mesmo lugar que o mural lê: quem escolhe aqui escolhe lá. */
const PALETAS = [
  ["marinho", "Marinho", "#0b1533"], ["aurora", "Aurora", "#1d1440"], ["oceano", "Oceano", "#0a3140"],
  ["grafite", "Grafite", "#1a1e28"], ["brasa", "Brasa", "#2f170e"],
];

/* O que cada página apresenta -- a caixa de texto do modo apresentação.
   É texto de apresentação, e não leitura dos dados: os números da tela
   continuam vindo do banco, e a frase só diz o que se está olhando. */
const APRESENTACAO = {
  painel: ["Visão geral", "Os quatro números do período, comparados com o anterior; a evolução mês a mês; a fatia de cada linha; onde os artigos estão agora; e o que os números dizem, calculado do banco."],
  acervos: ["Bibliotecas", "Cada acervo do laboratório: quantos registros, em que segmentos, que bases responderam, e o mapa segmento por base — onde há número, onde deu erro e onde a busca ainda não rodou."],
  triagens: ["Triagens", "Cada revisão com o fluxograma PRISMA contado do banco, as decisões, os motivos de exclusão, quem está triando e o kappa entre as duas pessoas que mais triaram."],
  bases: ["Bases de dados", "Cada base com o estado da última rodada, o que trouxe, e — nas que o sistema não alcança sozinho — o que fazer para colar a estratégia."],
  caminho: ["O caminho do artigo", "Seis etapas, da pesquisa bibliográfica à publicação: o que há em cada uma agora e a tela do LAPE que a faz."],
  doze: ["Doze olhares", "Os mesmos dados por doze gráficos diferentes, cada um respondendo uma pergunta escrita em cima dele."],
};
const AUTO_SEGUNDOS = 25;

/* As páginas, na ordem do menu. O id é o que vai no #hash. */
const ABAS = [
  ["painel", "Visão geral", "painel"],
  ["acervos", "Bibliotecas", "livro"],
  ["triagens", "Triagens", "submissao"],
  ["bases", "Bases", "qualidade"],
  ["caminho", "Caminho do artigo", "producao"],
  ["doze", "Doze olhares", "explorar"],
];

const NEON = {
  orange: "#FF7A18", magenta: "#FF3D9A", purple: "#8B5CF6", blue: "#3B82F6",
  cyan: "#22D3EE", green: "#34D399", yellow: "#FACC15", red: "#F43F5E", amber: "#F59E0B",
};
const NEON_SEQ = [NEON.orange, NEON.yellow, NEON.green, NEON.cyan, NEON.blue, NEON.purple, NEON.magenta];

/* As etapas do caminho ganham uma cor cada, na ordem do funil colorido
   do modelo: laranja, amarelo, verde, ciano, azul, roxo. */
const TOM_DA_ETAPA = [NEON.orange, NEON.yellow, NEON.green, NEON.cyan, NEON.blue, NEON.purple];

const TOM_DO_ESTADO = { ok: NEON.green, erro: NEON.red, pronta: NEON.cyan, "nunca rodou": NEON.yellow };
const ROTULO_DO_ESTADO = { ok: "ok", erro: "com erro", pronta: "estratégia pronta", "nunca rodou": "nunca rodou" };

async function api(caminho) {
  const r = await fetch(caminho);
  if (r.status === 401) { location.href = "/entrar?next=/aovivo"; throw new Error("entre"); }
  const dados = await r.json().catch(function () { return {}; });
  if (!r.ok) throw new Error(dados.error || ("erro " + r.status));
  return dados;
}

function aviso(texto) {
  const c = document.getElementById("aviso");
  c.textContent = texto;
  c.style.transform = "translateX(-50%) translateY(0)";
  clearTimeout(aviso._t);
  aviso._t = setTimeout(function () {
    c.style.transform = "translateX(-50%) translateY(140%)"; }, 2800);
}

function icone(nome, tamanho) {
  return (typeof Icons !== "undefined" && Icons.get) ? Icons.get(nome, tamanho === undefined ? null : tamanho)
    : el("span");
}

function pct(v) {
  if (v === null || v === undefined) return "";
  return (v > 0 ? "+" : "") + String(Math.round(v * 10) / 10).replace(".", ",") + "%";
}

function cortar(t, n) {
  const s = String(t || "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function rotuloDoPeriodo(de, ate) {
  return de === ate ? String(de) : de + "–" + ate;
}

function data(iso) {
  if (!iso) return "não informado";
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}:\d{2}))?/.exec(String(iso));
  if (!m) return String(iso);
  return m[3] + "/" + m[2] + "/" + m[1] + (m[4] ? " " + m[4] : "");
}

const SEM_MOVIMENTO = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* O número sobe até o valor em meio segundo. É o que faz o painel parecer
   vivo ao abrir -- e é só isso: o valor final é o do servidor, e quem tem
   movimento reduzido no sistema vê o número pronto. */
function contar(alvo, valor) {
  const fim = Number(valor) || 0;
  if (SEM_MOVIMENTO || fim < 2) { alvo.textContent = C.fmt(fim); return; }
  const t0 = performance.now(), dur = 650;
  function passo(t) {
    const k = Math.min(1, (t - t0) / dur);
    const suave = 1 - Math.pow(1 - k, 3);
    alvo.textContent = C.fmt(Math.round(fim * suave));
    if (k < 1) requestAnimationFrame(passo);
  }
  requestAnimationFrame(passo);
}

/* ------------------------------------------------------- peças de vidro */
function glass(filhos, opts) {
  opts = opts || {};
  const n = el("section", { class: "glass" + (opts.class ? " " + opts.class : ""),
    style: "--i:" + (opts.i || 0) + (opts.style ? ";" + opts.style : "") }, filhos);
  /* o clique faz o cartão surgir de novo: cresce e brilha por um instante.
     Um clique num botão ou num link dentro dele é do botão, não do cartão. */
  n.addEventListener("click", function (ev) {
    if (ev.target.closest("a, button, input, select")) return;
    n.classList.remove("surgiu");
    void n.offsetWidth;
    n.classList.add("surgiu");
  });
  return n;
}

function chip(tom, texto, semPonto) {
  return el("span", { class: "chip", style: "--tom:" + tom }, [semPonto ? null : el("i"), document.createTextNode(texto)]);
}

function cabecalho(titulo, sub, direita) {
  return el("div", { class: "cabecalho" }, [
    el("div", {}, [el("h3", { text: titulo }), sub ? el("div", { class: "sub", text: sub }) : null]),
    direita || null,
  ]);
}

function cabeca(icon, titulo, sub) {
  return el("div", { class: "cabeca" }, [
    el("div", { class: "brasao" }, [icone(icon)]),
    el("div", {}, [el("h1", { text: titulo }), el("p", { text: sub })]),
  ]);
}

function kpiNeon(o) {
  const valor = el("div", { class: "valor" });
  const n = glass([
    el("div", { class: "blob", style: "--tom:" + (o.tom || NEON.blue) }),
    el("div", { class: "rotulo", style: "--tom:" + (o.tom || NEON.blue) }, [o.icon ? icone(o.icon) : null, document.createTextNode(o.rotulo)]),
    valor,
    o.extra || null,
    el("div", { class: "pe" }, [o.pe || el("span"), o.chip || null]),
  ], { i: o.i || 0, class: "kpi-neon" });
  if (typeof o.valor === "number") contar(valor, o.valor); else valor.textContent = o.valor;
  return n;
}

/* barras horizontais com trilho, degradê e brilho -- animadas na chegada */
function hbars(itens, opts) {
  opts = opts || {};
  const max = opts.max || Math.max(1, ...itens.map(function (i) { return Number(i.valor) || 0; }));
  const lista = el("ul", { class: "hbars" + (opts.icones ? " com-icone" : ""),
    style: "--c:" + (opts.cor || NEON.blue) + ";--c2:" + (opts.cor2 || opts.cor || NEON.blue) });
  itens.forEach(function (i, n) {
    const w = Math.round(100 * (Number(i.valor) || 0) / max);
    lista.appendChild(el("li", { style: "--w:" + w + "%", title: i.nome }, [
      opts.icones ? Icons.tema(i.nome, { tam: 28, tom: opts.cor, icone: i.icone }) : null,
      el("span", { class: "nome", text: i.nome }),
      el("div", { class: "trilho" }, [el("div", { class: "barra" })]),
      el("span", { class: "n", text: opts.fmt ? opts.fmt(i.valor) : C.fmt(i.valor) }),
    ]));
  });
  /* a largura entra no quadro seguinte, para a transição acontecer */
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      lista.querySelectorAll("li").forEach(function (li) { li.classList.add("pronta"); });
    });
  });
  return lista;
}

/* o funil em camadas: cada degrau mais estreito, cada um com a sua cor */
function funil(passos, cores) {
  cores = cores || NEON_SEQ;
  const lista = el("ol", { class: "funil" });
  const n = passos.length;
  passos.forEach(function (p, i) {
    const w = Math.max(44, 100 - i * (52 / Math.max(1, n - 1)));
    const anterior = i ? passos[i - 1].valor : null;
    const parte = anterior ? Math.round(100 * p.valor / anterior) + "% do anterior" : null;
    lista.appendChild(el("li", { style: "--w:" + w + "%;--i:" + i + ";--c:" + cores[i % cores.length] }, [
      el("div", { class: "camada" }, [
        el("span", { class: "rot", text: p.rotulo }),
        el("span", { class: "val", text: C.fmt(p.valor) }),
      ]),
      parte ? el("span", { class: "pct", text: parte }) : null,
    ]));
  });
  return lista;
}

/* mapa de calor em tabela: número, "erro" ou lacuna hachurada */
function calor(d, cor) {
  const max = Math.max(1, ...d.values.flat().filter(function (v) { return typeof v === "number"; }));
  const cab = el("tr", {}, [el("th")].concat(d.cols.map(function (c) { return el("th", { text: c }); })));
  const corpo = d.rows.map(function (r, ri) {
    return el("tr", {}, [el("th", { class: "linha", text: r, title: r })].concat(d.values[ri].map(function (v) {
      if (v === "erro") return el("td", { class: "erro", text: "erro", title: "a base respondeu erro nesta busca" });
      if (v === null || v === undefined) return el("td", { class: "lacuna", text: "lacuna", title: "esta busca nunca rodou aqui" });
      const t = v / max;
      return el("td", { class: t > 0.6 ? "quente" : "", style: "--c:" + cor + ";--p:" + Math.round(12 + t * 78) + "%",
        text: C.fmt(v) });
    })));
  });
  return el("div", { style: "overflow-x:auto" }, [
    el("table", { class: "calor", style: "--c:" + cor }, [el("thead", {}, [cab]), el("tbody", {}, corpo)])]);
}

function miudos(pares) {
  return el("dl", { class: "miudos" }, pares.map(function (p) {
    return el("div", {}, [el("dt", { text: p[0] }), el("dd", { text: typeof p[1] === "number" ? C.fmt(p[1]) : String(p[1]) })]);
  }));
}

/* ------------------------------------------------------------- casca */
function desenharLado() {
  const lado = document.getElementById("lado");
  lado.innerHTML = "";
  lado.className = "lado" + (ST.menuAberto ? " aberto" : "");
  lado.appendChild(el("div", { class: "marca" }, [
    el("div", { class: "selo", text: "LP" }),
    el("div", {}, [el("b", { text: "LAPE ao vivo" }), el("small", { text: "Observatório do laboratório" })]),
  ]));
  const contagem = {
    acervos: D.acervos ? D.acervos.length : null,
    triagens: D.triagens ? D.triagens.length : null,
    bases: D.bases ? D.bases.length : null,
    doze: D.doze ? D.doze.length : null,
  };
  const paginas = el("div", { class: "paginas" });
  ABAS.forEach(function (aba) {
    paginas.appendChild(el("button", {
      type: "button", class: ST.aba === aba[0] ? "on" : "",
      onclick: function () { ST.aba = aba[0]; ST.menuAberto = false; location.hash = aba[0]; desenhar(); },
    }, [icone(aba[2]), document.createTextNode(aba[1]),
      contagem[aba[0]] ? el("span", { class: "n", text: String(contagem[aba[0]]) }) : null]));
  });
  lado.appendChild(paginas);
  const ligacoes = el("div", { class: "ligacoes" });
  [["/", "Painel completo"], ["/panorama", "Panorama"], ["/triagem", "Triagem"], ["/app", "Área do integrante"]].forEach(function (par) {
    const a = el("a", { href: par[0] });
    a.appendChild(el("button", { type: "button", text: par[1] }));
    ligacoes.appendChild(a);
  });
  lado.appendChild(ligacoes);

  /* a paleta de fundo -- a mesma escolha vale para o mural */
  const paletas = el("div", { class: "paletas", role: "group", "aria-label": "Paleta de fundo" });
  PALETAS.forEach(function (p) {
    paletas.appendChild(el("button", { type: "button", title: p[1], "aria-label": "Paleta " + p[1],
      class: paletaAtual() === p[0] ? "on" : "", style: "--amostra:" + p[2],
      onclick: function () { trocarPaleta(p[0]); } }));
  });
  lado.appendChild(el("div", { class: "rodape-lado" }, [
    el("b", { text: "Fundo" }), paletas]));
  lado.appendChild(el("button", { type: "button", class: "apresentar" + (ST.apresentando ? " on" : ""),
    text: ST.apresentando ? "Sair da apresentação" : "Apresentar ▶",
    style: "width:100%;font-size:12.5px;padding:9px 12px;background:var(--grad-accent);border:none;color:#fff;font-weight:700;box-shadow:0 0 18px -4px var(--accent-strong)",
    onclick: function () { ST.apresentando = !ST.apresentando; if (!ST.apresentando) ST.auto = false; desenhar(); } }));
  lado.appendChild(el("div", { class: "rodape-lado" }, [
    el("b", { text: "Gerado em" }),
    document.createTextNode(D.gerado_em ? data(D.gerado_em) : "…"),
  ]));
}

function desenharTopo() {
  const topo = document.getElementById("topo");
  topo.innerHTML = "";
  topo.appendChild(el("button", { class: "menu", type: "button", text: "☰", "aria-label": "Abrir menu",
    onclick: function () { ST.menuAberto = !ST.menuAberto; desenharLado(); } }));
  topo.appendChild(el("div", { class: "titulo" }, [
    el("b", { text: "Laboratório de Psicologia do Esporte e do Exercício" }),
    el("small", { text: "UDESC / CEFID · os números de agora, comparados com o período anterior" }),
  ]));
  const chips = el("div", { class: "chips", role: "tablist", "aria-label": "Período" });
  (D.periodos || []).forEach(function (p) {
    chips.appendChild(el("button", {
      type: "button", text: p.rotulo, class: ST.periodo === p.code ? "on" : "",
      onclick: function () { ST.periodo = p.code; carregar(); },
    }));
  });
  topo.appendChild(chips);
  topo.appendChild(el("span", { class: "pulso on", id: "pulso" }, [el("i"), document.createTextNode("ao vivo")]));
}

/* ------------------------------------------------------- visão geral */
function cartaoKpi(k, i) {
  const per = D.periodo;
  const tom = { publicacoes: NEON.blue, submissoes: NEON.cyan, aceites: NEON.green, citacoes: NEON.purple }[k.code] || NEON.blue;
  let pe;
  if (k.pct !== null && k.pct !== undefined) {
    const seta = k.pct > 0 ? "↑" : (k.pct < 0 ? "↓" : "→");
    const classe = k.pct > 0 ? "up" : (k.pct < 0 ? "down" : "flat");
    const contra = k.code === "citacoes" ? k.nota
      : "vs " + C.fmt(k.anterior) + " em " + rotuloDoPeriodo(per.anterior[0], per.anterior[1]);
    pe = el("span", { class: "delta " + classe }, [document.createTextNode(seta + " " + pct(k.pct) + " "),
      el("span", { class: "vs", text: contra })]);
  } else if (k.anterior !== null && k.anterior !== undefined) {
    /* anterior igual a zero: a seta não existe, e o número diz por quê */
    pe = el("span", { text: "o período anterior teve 0 — sem base para comparar" });
  } else {
    pe = el("span", { text: k.nota || "sem período anterior para comparar" });
  }
  const faisca = el("span", { class: "spark" });
  faisca.appendChild(C.sparkline(k.faisca, { color: tom, accent: tom }));
  return kpiNeon({ rotulo: k.rotulo, valor: k.valor, tom: tom, i: i,
    icon: { publicacoes: "livro", submissoes: "submissao", aceites: "aceite", citacoes: "citacao" }[k.code],
    pe: pe, extra: faisca });
}

function figuraDaEvolucao(ev, altura) {
  return C.lines({
    labels: ev.labels, height: altura || 250,
    series: ev.series.map(function (s, i) { return { label: s.label, values: s.values, color: [NEON.cyan, NEON.orange, NEON.green][i] }; }),
    table: { cols: ["período"].concat(ev.series.map(function (s) { return s.label; })),
      rows: ev.labels.map(function (l, i) { return [l].concat(ev.series.map(function (s) { return s.values[i]; })); }) },
    file: "evolucao",
  });
}

function desenharPainel(palco) {
  const per = D.periodo;
  palco.appendChild(cabeca("painel", per.rotulo + " · " + rotuloDoPeriodo(per.de, per.ate),
    per.anterior
      ? "comparado com " + rotuloDoPeriodo(per.anterior[0], per.anterior[1])
        + (per.meses_restantes ? " inteiro — " + per.ate + " ainda tem " + per.meses_restantes + " mês(es)" : "")
      : "sem período anterior: aqui só há o acumulado"));

  const kpis = el("div", { class: "grade kpis" });
  D.kpis.forEach(function (k, i) { kpis.appendChild(cartaoKpi(k, i)); });
  palco.appendChild(kpis);

  const ev = D.evolucao;
  const meio = el("div", { class: "grade meio" });
  meio.appendChild(glass([
    cabecalho("Evolução", ev.grao === "mes" ? "mês a mês em " + per.ate : "ano a ano"),
    figuraDaEvolucao(ev, 300),
    ev.sem_mes ? el("div", { class: "rodape", text: ev.sem_mes + " publicado(s) só têm o ano e não entram na conta por mês" }) : null,
  ], { i: 4 }));
  const itens = D.por_linha.items.map(function (i, n) { return { label: i.label, value: i.value, color: NEON_SEQ[n % NEON_SEQ.length] }; });
  const chipsDasLinhas = el("div", { class: "linhas-chips" }, D.por_linha.items.map(function (i, n) {
    return el("span", { class: "chip", style: "--tom:" + NEON_SEQ[n % NEON_SEQ.length] }, [
      Icons.tema(i.label, { icone: i.icone === "linha" ? undefined : i.icone, tom: NEON_SEQ[n % NEON_SEQ.length] }),
      document.createTextNode(i.label + " · " + i.value)]);
  }));
  meio.appendChild(glass([
    cabecalho("Por linha de pesquisa", D.por_linha.total + " publicado(s) em " + rotuloDoPeriodo(per.de, per.ate)),
    D.por_linha.total ? chipsDasLinhas : null,
    D.por_linha.total ? C.donut({ items: itens, caption: "publicados por linha" })
      : el("div", { class: "vazio", text: "nenhum publicado no período" }),
  ], { i: 5 }));
  palco.appendChild(meio);

  const baixo = el("div", { class: "grade baixo" });
  baixo.appendChild(glass([
    cabecalho("Onde os artigos estão agora", "todo o acervo, hoje — não depende do período"),
    hbars(D.por_situacao.map(function (s) { return { nome: s.label, valor: s.value }; }), { cor: NEON.blue, cor2: NEON.cyan }),
  ], { i: 6 }));
  const lista = el("ol", { class: "leituras" });
  D.leituras.forEach(function (l, i) {
    lista.appendChild(el("li", {}, [el("span", { class: "n", text: String(i + 1) }),
      el("div", {}, [el("p", { text: l.texto }), el("small", { text: "regra: " + l.regra })])]));
  });
  baixo.appendChild(glass([
    cabecalho("O que os números dizem", "calculado a partir do banco — sem modelo de linguagem", icone("achado")),
    D.leituras.length ? lista : el("div", { class: "vazio", text: "ainda não há o que ler: faltam dados com data" }),
  ], { i: 7 }));
  palco.appendChild(baixo);
}

/* ------------------------------------------------------- bibliotecas */
function desenharAcervos(palco) {
  palco.appendChild(cabeca("livro", "Bibliotecas",
    (D.acervos.length ? D.acervos.length + " acervo(s) que você pode ver" : "nenhum acervo visível")
    + " · busca automática na PubMed, Scopus e Web of Science, estratégia guardada para as demais"));
  if (!D.acervos.length) {
    palco.appendChild(glass([el("div", { class: "vazio", text: "Nenhum acervo instalado. A Biblioteca, na área do integrante, monta o primeiro." })]));
    return;
  }
  D.acervos.forEach(function (a, ai) {
    const base = ai * 10;
    palco.appendChild(el("h2", { class: "secao" }, [Icons.tema(a.title, { tam: 34 }),
      document.createTextNode(a.title + " "),
      a.restrita ? chip(NEON.amber, "restrito") : null]));
    const ok = a.bases.filter(function (b) { return b.estado === "ok"; }).length;
    const kpis = el("div", { class: "grade kpis" }, [
      kpiNeon({ rotulo: "Registros", valor: a.total, tom: NEON.blue, i: base, icon: "livro",
        pe: el("span", { text: a.atualizada_em ? "atualizado em " + data(a.atualizada_em) : "ainda não rodou" }) }),
      kpiNeon({ rotulo: "Segmentos", valor: a.segmentos.length, tom: NEON.purple, i: base + 1, icon: "linhas",
        pe: el("span", { text: a.eixo ? "eixo: " + a.eixo : "" }) }),
      kpiNeon({ rotulo: "Bases que responderam", valor: ok, tom: NEON.cyan, i: base + 2, icon: "qualidade",
        pe: el("span", { text: "de " + a.bases.length + " com estratégia" }) }),
      kpiNeon({ rotulo: "Com DOI", valor: a.com_doi, tom: NEON.green, i: base + 3, icon: "aceite",
        pe: el("span", { text: a.total ? Math.round(100 * a.com_doi / a.total) + "% dos registros" : "" }) }),
      kpiNeon({ rotulo: "Acesso livre", valor: a.livres, tom: NEON.yellow, i: base + 4, icon: "achado",
        pe: el("span", { text: a.sem_ano ? a.sem_ano + " sem ano" : "texto completo ao alcance" }) }),
    ]);
    palco.appendChild(kpis);

    const meio = el("div", { class: "grade meio" });
    meio.appendChild(glass([
      cabecalho("Registros por ano", "últimos " + a.anos.labels.length + " anos"
        + (a.anos.antes ? " · " + a.anos.antes + " anteriores a " + a.anos.labels[0] : "")),
      a.total ? C.area({ labels: a.anos.labels, height: 230, caption: "registros por ano",
        series: [{ label: "registros", values: a.anos.values, color: NEON.cyan }] })
        : el("div", { class: "vazio", text: "sem registros ainda" }),
    ], { i: base + 5 }));
    meio.appendChild(glass([
      cabecalho("Por segmento", "um registro pode estar em mais de um segmento"),
      a.segmentos.length ? hbars(a.segmentos.map(function (s) { return { nome: s.segmento, valor: s.n }; }), { cor: NEON.purple, cor2: NEON.magenta, icones: true })
        : el("div", { class: "vazio", text: "sem segmentos" }),
    ], { i: base + 6 }));
    palco.appendChild(meio);

    const baixo = el("div", { class: "grade meio" });
    baixo.appendChild(glass([
      cabecalho("Mapa de calor segmento × base", "célula hachurada em laranja é busca que nunca rodou ali; vermelha é erro da base"),
      a.calor.rows.length && a.calor.cols.length ? calor(a.calor, NEON.blue)
        : el("div", { class: "vazio", text: "sem buscas por segmento" }),
    ], { i: base + 7 }));
    const listaBases = el("ul", { class: "equipe" });
    a.bases.forEach(function (b) {
      listaBases.appendChild(el("li", {}, [
        el("span", {}, [chip(TOM_DO_ESTADO[b.estado] || NEON.blue, ROTULO_DO_ESTADO[b.estado] || b.estado), document.createTextNode(" " + b.rotulo)]),
        el("span", { text: b.manual && !b.itens ? "colar na base" : C.fmt(b.itens) + " reg. · " + C.fmt(b.achados) + " achados" }),
      ]));
    });
    baixo.appendChild(glass([cabecalho("Bases", a.bases.length + " com estratégia guardada"), listaBases], { i: base + 8 }));
    palco.appendChild(baixo);
  });
}

/* ---------------------------------------------------------- triagens */
function desenharTriagens(palco) {
  palco.appendChild(cabeca("submissao", "Triagens",
    (D.triagens.length ? D.triagens.length + " revisão(ões)" : "nenhuma revisão aberta") + " · fluxograma contado do banco, nenhum número digitado"));
  if (!D.triagens.length) {
    palco.appendChild(glass([el("div", { class: "vazio", text: "Nenhuma revisão aberta. A Triagem cria a primeira." })]));
    return;
  }
  D.triagens.forEach(function (t, ti) {
    const base = ti * 10;
    const f = t.fluxo;
    palco.appendChild(el("h2", { class: "secao" }, [document.createTextNode(t.title + " "),
      chip(NEON.purple, t.tipo + " · " + t.padrao, true)]));
    const kappaChip = t.kappa && t.kappa.kappa !== null
      ? chip(t.kappa.kappa >= 0.8 ? NEON.green : (t.kappa.kappa >= 0.6 ? NEON.yellow : NEON.orange), t.kappa.leitura)
      : null;
    palco.appendChild(el("div", { class: "grade kpis" }, [
      kpiNeon({ rotulo: "Identificados nas bases", valor: f.identificados, tom: NEON.blue, i: base, icon: "explorar",
        pe: el("span", { text: f.registros + " registro(s) importados" }) }),
      kpiNeon({ rotulo: "Repetições removidas", valor: f.duplicados, tom: NEON.magenta, i: base + 1, icon: "qualidade",
        pe: el("span", { text: "o fluxograma cobra este número" }) }),
      kpiNeon({ rotulo: "Em triagem", valor: f.triados, tom: NEON.cyan, i: base + 2, icon: "submissao",
        pe: el("span", { text: f.pendentes + " ainda sem decisão" }) }),
      kpiNeon({ rotulo: "Incluídos", valor: f.incluidos, tom: NEON.green, i: base + 3, icon: "aceite",
        pe: el("span", { text: f.texto_completo + " em texto completo" }) }),
      kpiNeon({ rotulo: "Kappa da triagem", valor: t.kappa && t.kappa.kappa !== null ? String(t.kappa.kappa).replace(".", ",") : "—",
        tom: NEON.yellow, i: base + 4, icon: "achado",
        pe: el("span", { text: t.kappa ? "entre " + t.kappa.entre.join(" e ") + ", n = " + t.kappa.n : "precisa de duas pessoas triando" }),
        chip: kappaChip }),
    ]));

    const meio = el("div", { class: "grade meio" });
    meio.appendChild(glass([
      cabecalho("Funil PRISMA", "cada degrau contém o de baixo; a porcentagem é sobre o anterior"),
      funil([
        { rotulo: "Identificados", valor: f.identificados || f.registros },
        { rotulo: "Sem repetição", valor: f.triados },
        { rotulo: "Após título e resumo", valor: Math.max(0, f.triados - f.excluidos_triagem) },
        { rotulo: "Texto completo", valor: f.texto_completo },
        { rotulo: "Incluídos", valor: f.incluidos },
      ]),
      miudos([["Excluídos na triagem", f.excluidos_triagem], ["Excluídos no texto", f.excluidos_texto],
        ["Pendentes", f.pendentes], ["Avaliadores", t.avaliadores + (t.as_cegas ? " · às cegas" : "")]]),
    ], { i: base + 5 }));
    const dec = t.decisoes;
    meio.appendChild(glass([
      cabecalho("Decisões no título e resumo", "decisão consolidada de cada registro"),
      (dec.incluir + dec.excluir + dec.talvez + dec.pendente)
        ? C.donut({ caption: "decisões", items: [
          { label: "Incluir", value: dec.incluir, color: NEON.green },
          { label: "Excluir", value: dec.excluir, color: NEON.magenta },
          { label: "Em dúvida", value: dec.talvez, color: NEON.yellow },
          { label: "Pendente", value: dec.pendente, color: NEON.blue }] })
        : el("div", { class: "vazio", text: "nada importado ainda" }),
    ], { i: base + 6 }));
    palco.appendChild(meio);

    const baixo = el("div", { class: "grade tres" });
    baixo.appendChild(glass([
      cabecalho("Motivos de exclusão", "o fluxograma pede cada um"),
      t.motivos.length ? hbars(t.motivos.map(function (m) { return { nome: m.motivo, valor: m.n }; }), { cor: NEON.orange, cor2: NEON.magenta })
        : el("div", { class: "vazio", text: "ninguém excluído com motivo ainda" }),
    ], { i: base + 7 }));
    baixo.appendChild(glass([
      cabecalho("Registros por base", "com as repetições contadas"),
      t.por_base.length ? hbars(t.por_base.map(function (b) { return { nome: b.base, valor: b.n }; }), { cor: NEON.cyan, cor2: NEON.blue })
        : el("div", { class: "vazio", text: "nenhuma busca importada" }),
    ], { i: base + 8 }));
    const conf = t.conferencia;
    const total = conf.feito + conf.falta + conf.manual + conf.na || 1;
    const barra = el("div", { class: "conferencia" }, [
      el("i", { style: "width:" + (100 * conf.feito / total) + "%;background:" + NEON.green, title: conf.feito + " feito(s)" }),
      el("i", { style: "width:" + (100 * conf.falta / total) + "%;background:" + NEON.red, title: conf.falta + " faltando" }),
      el("i", { style: "width:" + (100 * conf.manual / total) + "%;background:" + NEON.yellow, title: conf.manual + " para conferir" }),
      el("i", { style: "width:" + (100 * conf.na / total) + "%;background:" + "rgba(255,255,255,.15)", title: conf.na + " não se aplica(m)" }),
    ]);
    const equipe = el("ul", { class: "equipe" });
    t.equipe.forEach(function (e) {
      equipe.appendChild(el("li", {}, [el("span", { text: e.quem }),
        el("span", { text: e.triadas + " triadas · " + e.incluiu + " incl. · " + e.excluiu + " excl." })]));
    });
    baixo.appendChild(glass([
      cabecalho("Padrão " + t.padrao, conf.feito + " feito(s) · " + conf.falta + " faltando · " + conf.manual + " para você conferir"),
      barra,
      el("div", { class: "sub", style: "margin-top:12px", text: "quem está triando" }),
      t.equipe.length ? equipe : el("div", { class: "vazio", text: "ninguém triou ainda" }),
    ], { i: base + 9 }));
    palco.appendChild(baixo);
  });
}

/* ------------------------------------------------------------- bases */
function desenharBases(palco) {
  palco.appendChild(cabeca("qualidade", "Bases de dados",
    D.bases.length + " base(s) com estratégia guardada · estado da última rodada, o que cada uma trouxe"));
  const estados = ["ok", "erro", "pronta", "nunca rodou"];
  const legenda = el("div", { class: "legenda-estados" });
  estados.forEach(function (e) {
    const n = D.bases.filter(function (b) { return b.estado === e; }).length;
    legenda.appendChild(chip(TOM_DO_ESTADO[e], ROTULO_DO_ESTADO[e] + " · " + n));
  });
  palco.appendChild(legenda);
  const grade = el("div", { class: "bases" });
  D.bases.forEach(function (b, i) {
    const tom = TOM_DO_ESTADO[b.estado] || NEON.blue;
    grade.appendChild(glass([
      el("div", { class: "blob", style: "--tom:" + tom + ";width:190px;height:190px;top:-64px;right:-64px" }),
      el("div", { class: "cabecalho" }, [el("h3", { text: b.rotulo }), chip(tom, ROTULO_DO_ESTADO[b.estado] || b.estado)]),
      el("div", { class: "desde", text: b.ultima ? "última rodada em " + data(b.ultima) : (b.manual ? "o sistema não a alcança sozinho" : "nunca rodou") }),
      el("dl", { class: "nums" }, [
        el("div", {}, [el("dt", { text: "registros" }), el("dd", { text: C.fmt(b.itens) })]),
        el("div", {}, [el("dt", { text: "achados" }), el("dd", { text: C.fmt(b.achados) })]),
        el("div", {}, [el("dt", { text: "acervos" }), el("dd", { text: C.fmt(b.acervos) })]),
      ]),
      b.ultimo_erro ? el("p", { class: "nota", text: "último erro: " + cortar(b.ultimo_erro, 160) }) : null,
      b.nota ? el("p", { class: "nota", text: b.nota }) : null,
    ], { i: i, class: "base" }));
  });
  palco.appendChild(D.bases.length ? grade : glass([el("div", { class: "vazio", text: "nenhuma base ainda — instale um acervo na Biblioteca" })]));
}

/* ----------------------------------------------------------- caminho */
function desenharCaminho(palco) {
  palco.appendChild(cabeca("producao", "O caminho do artigo",
    "seis etapas, o que há em cada uma agora, e a tela do LAPE que a faz"));
  const lista = el("div", { class: "caminho" });
  D.caminho.forEach(function (e, i) {
    const a = el("a", { href: e.href });
    a.appendChild(el("button", { type: "button", text: e.ferramenta + " →" }));
    lista.appendChild(glass([
      el("div", { class: "num", text: String(i + 1) }),
      el("div", {}, [el("h4", { text: e.rotulo }),
        el("div", { class: "valor" }, [document.createTextNode(C.fmt(e.valor)),
          el("small", { text: e.unidade + (e.detalhe !== undefined ? " · " + C.fmt(e.detalhe) + " " + e.detalhe_rotulo : "") })])]),
      el("div", { class: "faz-col" }, [el("div", { class: "faz", text: "No LAPE: " + e.faz })]),
      a,
    ], { i: i, class: "etapa", style: "--tom:" + TOM_DA_ETAPA[i] }));
  });
  palco.appendChild(lista);
  palco.appendChild(el("div", { class: "aviso-rodape",
    text: "Cada etapa conta uma coisa diferente — referência, registro triado, artigo — e por isso "
      + "não há porcentagem entre elas. O funil de verdade, com a mesma unidade em todos os degraus, "
      + "está em Doze olhares e em Triagens." }));
}

/* -------------------------------------------------------------- doze */
function figuraDoOlhar(o) {
  const d = o.dados;
  if (!d) return el("div", { class: "vazio", text: o.vazio || "sem dados" });
  switch (o.code) {
    case "calor":
      return C.heatmap({ years: d.years, values: d.values, unit: "publicados", caption: o.titulo });
    case "cascata":
      /* o nome da linha inteiro não cabe embaixo de uma coluna; a dica do
         mouse traz o nome completo, e o rótulo curto só localiza */
      return C.waterfall({ items: d.items.map(function (i) { return { label: cortar(i.label, 7), value: i.value, total: i.total, title: i.label }; }),
        caption: o.titulo, height: 260 });
    case "linhas":
      return figuraDaEvolucao(d, 230);
    case "empilhadas":
      return C.columns({ labels: d.labels, mode: "empilhado", height: 230, caption: o.titulo,
        series: d.series.map(function (s, i) { return { label: s.label, values: s.values, color: NEON_SEQ[i % NEON_SEQ.length] }; }) });
    case "rosca":
      return C.donut({ items: d.items.map(function (i, n) { return { label: i.label, value: i.value, color: NEON_SEQ[n % NEON_SEQ.length] }; }),
        caption: o.titulo });
    case "dispersao":
      return C.scatter({ points: d.points.map(function (p) { return Object.assign({}, p, { color: NEON.cyan }); }),
        xLabel: "anos desde a publicação", yLabel: "citações", height: 260, caption: o.titulo });
    case "histograma":
      return C.columns({ labels: d.labels, values: d.values, name: "artigos", height: 230, caption: o.titulo });
    case "caixa":
      return d.groups.length
        ? C.distribution({ groups: d.groups.map(function (g, i) { return { label: g.label, values: g.values, color: NEON_SEQ[i % NEON_SEQ.length] }; }),
          caption: o.titulo, labelWidth: 150 })
        : el("div", { class: "vazio", text: "nenhuma submissão com data de envio e de decisão" });
    case "area":
      return C.area({ labels: d.labels, height: 230, caption: o.titulo,
        series: d.series.map(function (s, i) { return { label: s.label, values: s.values, color: NEON_SEQ[i % NEON_SEQ.length] }; }) });
    case "bullet":
      return C.bullet({ items: d.items.map(function (i) { return { label: i.label + (i.referencia ? " (" + i.referencia + ")" : ""),
        value: i.value, target: i.target === null ? NaN : i.target, max: i.max }; }), caption: o.titulo, labelWidth: 200 });
    case "tendencia":
      return C.lines({ labels: d.labels, height: 230, caption: o.titulo,
        series: d.series.map(function (s, i) { return { label: s.label, values: s.values, color: [NEON.cyan, NEON.orange][i] }; }) });
    case "funil":
      return funil(d.steps.map(function (s) { return { rotulo: s.label, valor: s.value }; }), [NEON.blue, NEON.cyan, NEON.green, NEON.yellow]);
    default:
      return el("div", { class: "vazio", text: "olhar desconhecido: " + o.code });
  }
}

function desenharDoze(palco) {
  palco.appendChild(cabeca("explorar", "Doze olhares sobre os mesmos dados",
    "cada gráfico responde uma pergunta — a pergunta está em cima dele"));
  const grade = el("div", { class: "doze" });
  D.doze.forEach(function (o, i) {
    grade.appendChild(glass([
      el("span", { class: "tipo", text: o.titulo }),
      el("div", { class: "pergunta", text: o.pergunta }),
      figuraDoOlhar(o),
      o.nota ? el("div", { class: "rodape", text: o.nota }) : null,
      o.code === "bullet" && o.dados ? el("div", { class: "rodape",
        text: "sem meta declarada, a referência é a média dos três anos anteriores — e o rótulo diz qual das duas é" }) : null,
    ], { i: i, class: "olhar" }));
  });
  palco.appendChild(grade);
}

/* ------------------------------------------------------------- comum */
function desenhar() {
  desenharLado();
  desenharTopo();
  const palco = document.getElementById("palco");
  palco.innerHTML = "";
  if (!D.pronto) { palco.appendChild(el("div", { class: "vazio", text: "carregando…" })); return; }
  if (ST.aba === "acervos") desenharAcervos(palco);
  else if (ST.aba === "triagens") desenharTriagens(palco);
  else if (ST.aba === "bases") desenharBases(palco);
  else if (ST.aba === "caminho") desenharCaminho(palco);
  else if (ST.aba === "doze") desenharDoze(palco);
  else desenharPainel(palco);
  palco.appendChild(el("div", { class: "aviso-rodape", text: D.aviso + " Gerado em " + data(D.gerado_em) + "." }));
  desenharApresentacao();
}

/* ------------------------------------------------------ apresentação */
/* A caixa de texto embaixo, com o que se está olhando, e o "Seguir" para
   a próxima página. "Auto" passa sozinho a cada AUTO_SEGUNDOS -- é o modo
   do projetor: a pessoa aperta uma vez e a tela conduz. */
let relogioAuto = null;
function desenharApresentacao() {
  let caixa = document.getElementById("apresentacao");
  clearInterval(relogioAuto); relogioAuto = null;
  document.body.classList.toggle("apresentando", ST.apresentando);
  if (!ST.apresentando) { if (caixa) caixa.remove(); return; }
  if (!caixa) { caixa = el("div", { class: "apresentacao", id: "apresentacao", role: "region", "aria-label": "Apresentação" }); document.body.appendChild(caixa); }
  caixa.innerHTML = "";
  const indice = ABAS.findIndex(function (a) { return a[0] === ST.aba; });
  const texto = APRESENTACAO[ST.aba] || [ST.aba, ""];
  caixa.appendChild(el("div", { class: "texto" }, [el("b", { text: (indice + 1) + " de " + ABAS.length + " · " + texto[0] }),
    el("p", { text: texto[1] })]));
  const pontos = el("span", { class: "pontos" }, ABAS.map(function (a, i) { return el("i", { class: i === indice ? "on" : "" }); }));
  caixa.appendChild(el("div", { class: "passos" }, [
    pontos,
    el("button", { type: "button", text: "◀ Anterior", onclick: function () { irPara(indice - 1); } }),
    el("button", { type: "button", class: "seguir", text: "Seguir ▶", onclick: function () { irPara(indice + 1); } }),
    el("button", { type: "button", class: ST.auto ? "on" : "", text: ST.auto ? "Auto: ligado" : "Auto (" + AUTO_SEGUNDOS + " s)",
      onclick: function () { ST.auto = !ST.auto; desenharApresentacao(); } }),
  ]));
  const barra = el("div", { class: "barra" }, [el("i")]);
  caixa.appendChild(barra);
  if (ST.auto) {
    const t0 = performance.now();
    relogioAuto = setInterval(function () {
      const k = Math.min(1, (performance.now() - t0) / (AUTO_SEGUNDOS * 1000));
      barra.firstChild.style.width = (k * 100).toFixed(1) + "%";
      if (k >= 1) irPara(indice + 1);
    }, 200);
  }
}

function irPara(indice) {
  const n = ABAS.length;
  ST.aba = ABAS[((indice % n) + n) % n][0];
  location.hash = ST.aba;
  window.scrollTo(0, 0);
  desenhar();
}

document.addEventListener("keydown", function (ev) {
  if (!ST.apresentando || ev.target.tagName === "INPUT" || ev.target.tagName === "SELECT") return;
  const indice = ABAS.findIndex(function (a) { return a[0] === ST.aba; });
  if (ev.key === "ArrowRight" || ev.key === " ") { ev.preventDefault(); irPara(indice + 1); }
  else if (ev.key === "ArrowLeft") irPara(indice - 1);
  else if (ev.key === "Escape") { ST.apresentando = false; ST.auto = false; desenhar(); }
});

/* ------------------------------------------------------------ paleta */
function paletaAtual() {
  return document.documentElement.getAttribute("data-paleta") || "marinho";
}
function trocarPaleta(code) {
  document.documentElement.setAttribute("data-paleta", code);
  try { localStorage.setItem("lape-paleta", code); } catch (e) { /* janela privada */ }
  desenhar();
}

async function carregar() {
  const rolagem = window.scrollY;
  try {
    const dados = await api("/api/aovivo?periodo=" + encodeURIComponent(ST.periodo));
    Object.assign(D, dados, { pronto: true });
    ST.periodo = D.periodo.code;
    desenhar();
    window.scrollTo(0, rolagem);
  } catch (erro) {
    if (erro.message !== "entre") aviso(erro.message);
  }
}

/* ao vivo: o servidor avisa a cada mudança, e a tela recarrega uma vez
   depois de um segundo de silêncio -- dez gravações seguidas viram um
   redesenho, e não dez */
let fonteDeEventos = null;
let recargaMarcada = null;

function ligarAoVivo() {
  if (typeof EventSource === "undefined") return;
  try { fonteDeEventos = new EventSource("/api/stream"); } catch (erro) { return; }
  fonteDeEventos.addEventListener("pronto", function () { marcarPulso("ao vivo", true); });
  fonteDeEventos.addEventListener("mudanca", function () {
    marcarPulso("mudou agora", true);
    clearTimeout(recargaMarcada);
    recargaMarcada = setTimeout(carregar, 1200);
  });
  fonteDeEventos.addEventListener("error", function () { marcarPulso("reconectando", false); });
}

function marcarPulso(texto, ligado) {
  const alvo = document.getElementById("pulso");
  if (!alvo) return;
  alvo.lastChild.textContent = texto;
  alvo.classList.toggle("on", !!ligado);
  alvo.classList.remove("batendo");
  void alvo.offsetWidth;
  alvo.classList.add("batendo");
}

(function iniciar() {
  let guardada = null;
  try { guardada = localStorage.getItem("lape-paleta"); } catch (e) { /* janela privada */ }
  if (guardada && PALETAS.some(function (p) { return p[0] === guardada; })) {
    document.documentElement.setAttribute("data-paleta", guardada);
  }
  const aba = location.hash.replace("#", "");
  if (ABAS.some(function (a) { return a[0] === aba; })) ST.aba = aba;
  desenhar();
  carregar();
  ligarAoVivo();
})();
