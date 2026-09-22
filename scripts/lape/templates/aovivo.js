/* LAPE ao vivo.
 *
 * Uma tela, os números de agora, e o que mudou. A régua deste arquivo:
 * cada número vem com o do período anterior ao lado, cada gráfico
 * responde uma pergunta escrita em cima dele, e as leituras do fim são
 * calculadas -- a tela diz isso, e cada uma traz a regra de onde saiu.
 *
 * O servidor faz a conta toda (`/api/aovivo`); aqui só se desenha. É o
 * que permite testar os números sem navegador e a tela sem banco. */
"use strict";

const C = Charts;
const el = C.el;

const D = { pronto: false };
const ST = { periodo: "ano", aba: "painel" };

const ABAS = [
  ["painel", "Painel", "painel"],
  ["caminho", "Caminho do artigo", "producao"],
  ["doze", "Doze olhares", "explorar"],
];

/* As etapas do caminho ganham uma cor cada, na ordem da paleta ordinal:
   é a mesma sequência que o funil do painel usa, para a etapa ter a
   mesma cor nas duas telas. */
const TOM_DA_ETAPA = ["--series-1", "--series-7", "--series-3", "--series-4", "--series-2", "--series-6"];

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

/* ------------------------------------------------------------ topo */
function desenharTopo() {
  const topo = document.getElementById("topo");
  topo.innerHTML = "";
  topo.appendChild(el("div", { class: "marca" }, [
    el("div", { class: "selo", text: "LP" }),
    el("div", {}, [el("b", { text: "LAPE ao vivo" }),
      el("small", { text: "Laboratório de Psicologia do Esporte e do Exercício" })]),
  ]));

  const chips = el("div", { class: "chips", role: "tablist", "aria-label": "Período" });
  (D.periodos || []).forEach(function (p) {
    chips.appendChild(el("button", {
      type: "button", text: p.rotulo, class: ST.periodo === p.code ? "on" : "",
      onclick: function () { ST.periodo = p.code; carregar(); },
    }));
  });
  topo.appendChild(chips);

  const abas = el("nav", { class: "abas" });
  ABAS.forEach(function (aba) {
    abas.appendChild(el("button", {
      type: "button", class: ST.aba === aba[0] ? "on" : "",
      onclick: function () { ST.aba = aba[0]; location.hash = aba[0]; desenhar(); },
    }, [icone(aba[2]), document.createTextNode(aba[1])]));
  });
  topo.appendChild(abas);

  topo.appendChild(el("span", { class: "pulso on", id: "pulso" }, [el("i"), document.createTextNode("ao vivo")]));

  const ligacoes = el("div", { class: "ligacoes" });
  ligacoes.appendChild(el("button", { type: "button", text: "Tema", title: "Claro ou escuro",
    onclick: trocarTema }));
  [["/", "Painel completo"], ["/panorama", "Panorama"], ["/app", "Área do integrante"]].forEach(function (par) {
    const a = el("a", { href: par[0] });
    a.appendChild(el("button", { type: "button", text: par[1] }));
    ligacoes.appendChild(a);
  });
  topo.appendChild(ligacoes);
}

/* ---------------------------------------------------------- painel */
function cartaoKpi(k) {
  const tom = k.pct === null || k.pct === undefined ? "" : (k.pct > 0 ? " t-good" : (k.pct < 0 ? " t-bad" : ""));
  const per = D.periodo;
  const filhos = [
    el("div", { class: "label" }, [icone({ publicacoes: "livro", submissoes: "submissao",
      aceites: "aceite", citacoes: "citacao" }[k.code] || "painel"), document.createTextNode(k.rotulo)]),
    el("div", { class: "value", text: C.fmt(k.valor) }),
  ];
  if (k.pct !== null && k.pct !== undefined) {
    const seta = k.pct > 0 ? "↑" : (k.pct < 0 ? "↓" : "→");
    const classe = k.pct > 0 ? "up" : (k.pct < 0 ? "down" : "flat");
    const contra = k.code === "citacoes"
      ? k.nota
      : "vs " + C.fmt(k.anterior) + " em " + rotuloDoPeriodo(per.anterior[0], per.anterior[1]);
    filhos.push(el("div", { class: "delta " + classe }, [
      document.createTextNode(seta + " " + pct(k.pct)),
      el("span", { class: "vs", text: contra }),
    ]));
  } else if (k.anterior !== null && k.anterior !== undefined) {
    /* anterior igual a zero: a seta não existe, e o número diz por quê */
    filhos.push(el("div", { class: "semseta", text: "o período anterior teve 0 — sem base para comparar" }));
  } else {
    filhos.push(el("div", { class: "semseta", text: k.nota || "sem período anterior para comparar" }));
  }
  const faisca = el("div", { class: "spark" });
  faisca.appendChild(C.sparkline(k.faisca, { color: C.token("--accent-strong") }));
  filhos.push(faisca);
  filhos.push(el("div", { class: "foot", text: k.code === "citacoes"
    ? "melhor base por artigo · últimos instantâneos"
    : "por ano, " + k.faisca_de + "–" + per.ate }));
  return el("div", { class: "kpi" + tom }, filhos);
}

function cartao(titulo, sub, corpo, rodape) {
  return el("div", { class: "card" }, [
    el("h3", { text: titulo }), sub ? el("div", { class: "sub", text: sub }) : null,
    corpo, rodape ? el("div", { class: "rodape", text: rodape }) : null,
  ]);
}

function figuraDaEvolucao(ev, altura) {
  return C.lines({
    labels: ev.labels, height: altura || 250,
    series: ev.series.map(function (s, i) { return { label: s.label, values: s.values, color: C.serie(i) }; }),
    table: { cols: ["período"].concat(ev.series.map(function (s) { return s.label; })),
      rows: ev.labels.map(function (l, i) { return [l].concat(ev.series.map(function (s) { return s.values[i]; })); }) },
    file: "evolucao",
  });
}

function desenharPainel(palco) {
  const per = D.periodo;
  palco.appendChild(el("div", { class: "cabeca" }, [
    el("h1", { text: per.rotulo + " · " + rotuloDoPeriodo(per.de, per.ate) }),
    el("span", { class: "hint", text: per.anterior
      ? "comparado com " + rotuloDoPeriodo(per.anterior[0], per.anterior[1])
        + (per.meses_restantes ? " inteiro — " + per.ate + " ainda tem " + per.meses_restantes + " mês(es)" : "")
      : "sem período anterior: aqui só há o acumulado" }),
  ]));

  const kpis = el("div", { class: "grade kpis" });
  D.kpis.forEach(function (k) { kpis.appendChild(cartaoKpi(k)); });
  palco.appendChild(kpis);

  const ev = D.evolucao;
  const meio = el("div", { class: "grade meio" });
  meio.appendChild(cartao("Evolução",
    ev.grao === "mes" ? "mês a mês em " + per.ate : "ano a ano",
    figuraDaEvolucao(ev, 320),
    ev.sem_mes ? ev.sem_mes + " publicado(s) só têm o ano e não entram na conta por mês" : null));

  const rosca = el("div", { class: "rosca" });
  const itens = D.por_linha.items.map(function (i, n) { return { label: i.label, value: i.value, color: C.serie(n) }; });
  rosca.appendChild(C.donut({ items: itens, caption: "publicados por linha" }));
  meio.appendChild(cartao("Por linha de pesquisa", D.por_linha.total + " publicado(s) em " + rotuloDoPeriodo(per.de, per.ate),
    D.por_linha.total ? rosca : el("div", { class: "empty", text: "nenhum publicado no período" })));
  palco.appendChild(meio);

  const baixo = el("div", { class: "grade baixo" });
  baixo.appendChild(cartao("Onde os artigos estão agora", "todo o acervo, hoje — não depende do período",
    C.bars({ items: D.por_situacao.map(function (s, i) { return { label: s.label, value: s.value, color: C.ord(i) }; }),
      caption: "artigos por situação", labelWidth: 130 })));

  const lista2 = el("ol", { class: "leituras" });
  D.leituras.forEach(function (l, i) {
    lista2.appendChild(el("li", {}, [
      el("span", { class: "n", text: String(i + 1) }),
      el("div", {}, [el("p", { text: l.texto }), el("small", { text: "regra: " + l.regra })]),
    ]));
  });
  baixo.appendChild(cartao("O que os números dizem", "calculado a partir do banco — sem modelo de linguagem",
    D.leituras.length ? lista2 : el("div", { class: "empty", text: "ainda não há o que ler: faltam dados com data" })));
  palco.appendChild(baixo);
}

/* --------------------------------------------------------- caminho */
function desenharCaminho(palco) {
  palco.appendChild(el("div", { class: "cabeca" }, [
    el("h1", { text: "O caminho do artigo" }),
    el("span", { class: "hint", text: "seis etapas, o que há em cada uma agora, e a tela do LAPE que a faz" }),
  ]));
  const lista = el("div", { class: "caminho" });
  D.caminho.forEach(function (e, i) {
    const a = el("a", { href: e.href });
    a.appendChild(el("button", { type: "button", text: e.ferramenta + " →" }));
    lista.appendChild(el("div", { class: "etapa", style: "--tom:" + C.token(TOM_DA_ETAPA[i] || "--series-1") }, [
      el("div", { class: "num", text: String(i + 1) }),
      el("div", {}, [el("h4", { text: e.rotulo }),
        el("div", { class: "valor" }, [document.createTextNode(C.fmt(e.valor)),
          el("small", { text: e.unidade + (e.detalhe !== undefined ? " · " + C.fmt(e.detalhe) + " " + e.detalhe_rotulo : "") })])]),
      el("div", { class: "faz-col" }, [el("div", { class: "faz", text: "No LAPE: " + e.faz })]),
      a,
    ]));
  });
  palco.appendChild(lista);
  palco.appendChild(el("div", { class: "aviso-rodape",
    text: "Cada etapa conta uma coisa diferente — referência, registro triado, artigo — e por isso "
      + "não há porcentagem entre elas. O funil de verdade, com a mesma unidade em todos os degraus, "
      + "está em Doze olhares." }));
}

/* ------------------------------------------------------------ doze */
function figuraDoOlhar(o) {
  const d = o.dados;
  if (!d) return el("div", { class: "vazio", text: o.vazio || "sem dados" });
  switch (o.code) {
    case "calor":
      return C.heatmap({ years: d.years, values: d.values, unit: "publicados", caption: o.titulo });
    case "cascata":
      /* o nome da linha inteiro não cabe embaixo de uma coluna; a dica do
         mouse traz o nome completo, e o rótulo curto só localiza */
      return C.waterfall({ items: d.items.map(function (i) { return { label: cortar(i.label, 9), value: i.value, total: i.total, title: i.label }; }),
        caption: o.titulo, height: 260 });
    case "linhas":
      return figuraDaEvolucao(d, 230);
    case "empilhadas":
      return C.columns({ labels: d.labels, mode: "empilhado", height: 230, caption: o.titulo,
        series: d.series.map(function (s, i) { return { label: s.label, values: s.values, color: C.ord(i) }; }) });
    case "rosca":
      return C.donut({ items: d.items.map(function (i, n) { return { label: i.label, value: i.value, color: C.serie(n) }; }),
        caption: o.titulo });
    case "dispersao":
      return C.scatter({ points: d.points, xLabel: "anos desde a publicação", yLabel: "citações",
        height: 260, caption: o.titulo });
    case "histograma":
      return C.columns({ labels: d.labels, values: d.values, name: "artigos", height: 230, caption: o.titulo });
    case "caixa":
      return d.groups.length
        ? C.distribution({ groups: d.groups.map(function (g, i) { return { label: g.label, values: g.values, color: C.serie(i) }; }),
          caption: o.titulo, labelWidth: 150 })
        : el("div", { class: "vazio", text: "nenhuma submissão com data de envio e de decisão" });
    case "area":
      return C.area({ labels: d.labels, height: 230, caption: o.titulo,
        series: d.series.map(function (s, i) { return { label: s.label, values: s.values, color: C.serie(i) }; }) });
    case "bullet":
      return C.bullet({ items: d.items.map(function (i) { return { label: i.label + (i.referencia ? " (" + i.referencia + ")" : ""),
        value: i.value, target: i.target === null ? NaN : i.target, max: i.max }; }), caption: o.titulo, labelWidth: 200 });
    case "tendencia":
      return C.lines({ labels: d.labels, height: 230, caption: o.titulo,
        series: d.series.map(function (s, i) { return { label: s.label, values: s.values, color: C.serie(i) }; }) });
    case "funil":
      return C.funnel({ steps: d.steps, caption: o.titulo, unit: "artigos", rowH: 44 });
    default:
      return el("div", { class: "vazio", text: "olhar desconhecido: " + o.code });
  }
}

function desenharDoze(palco) {
  palco.appendChild(el("div", { class: "cabeca" }, [
    el("h1", { text: "Doze olhares sobre os mesmos dados" }),
    el("span", { class: "hint", text: "cada gráfico responde uma pergunta — a pergunta está em cima dele" }),
  ]));
  const grade = el("div", { class: "doze" });
  D.doze.forEach(function (o) {
    grade.appendChild(el("div", { class: "card olhar" }, [
      el("span", { class: "tipo", text: o.titulo }),
      el("div", { class: "pergunta", text: o.pergunta }),
      figuraDoOlhar(o),
      o.nota ? el("div", { class: "rodape", text: o.nota }) : null,
      o.code === "bullet" && o.dados ? el("div", { class: "rodape",
        text: "sem meta declarada, a referência é a média dos três anos anteriores — e o rótulo diz qual das duas é" }) : null,
    ]));
  });
  palco.appendChild(grade);
}

/* ---------------------------------------------------------- comum */
function desenhar() {
  desenharTopo();
  const palco = document.getElementById("palco");
  palco.innerHTML = "";
  if (!D.pronto) { palco.appendChild(el("div", { class: "empty", text: "carregando…" })); return; }
  if (ST.aba === "caminho") desenharCaminho(palco);
  else if (ST.aba === "doze") desenharDoze(palco);
  else desenharPainel(palco);
  palco.appendChild(el("div", { class: "aviso-rodape", text: D.aviso + " Gerado em " + D.gerado_em.replace("T", " ") + "." }));
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

function trocarTema() {
  const atual = document.documentElement.getAttribute("data-theme") || "light";
  const proximo = atual === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", proximo);
  try { localStorage.setItem("lape-theme", proximo); } catch (e) { /* janela privada */ }
  desenhar();
}

(function iniciar() {
  let guardado = null;
  try { guardado = localStorage.getItem("lape-theme"); } catch (e) { /* janela privada */ }
  if (guardado) document.documentElement.setAttribute("data-theme", guardado);
  const aba = location.hash.replace("#", "");
  if (ABAS.some(function (a) { return a[0] === aba; })) ST.aba = aba;
  desenhar();
  carregar();
  ligarAoVivo();
})();
