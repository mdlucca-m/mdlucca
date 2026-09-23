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
const ST = { periodo: "ano", aba: "painel", menuAberto: false, apresentando: false, auto: false,
  busca: "", analise: "curva", autoAnalise: false, explicadas: 0, pausada: false };

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
  temas: ["Temas e indicadores", "Os indicadores que os quatro números não contam: quanto tempo leva, quanto é aceito, quanto é aberto, com quem se publica e o que se publica — e seis gráficos novos: radar, haltere, corrida de posições, fluxo, mosaico e calendário."],
  sinais: ["Sinais e cálculo", "A curva mensal de publicações lida com cálculo: derivada, integral e área de crescimento, tendência separada da estação e do ruído, os pontos de inflexão e o limite à vista. Cada análise roda no seu botão, e a tela passa sozinha de uma para a outra."],
  mundo: ["Mapa-múndi ao vivo", "O globo gira e pousa em cada país que assina com o laboratório: o arco sai da UDESC, o país acende, e a ficha diz quantos artigos e quais instituições."],
  busca: ["Buscador temático", "Um campo para achar artigos, pessoas, projetos, linhas, acervos e temas — cada resultado com o seu ícone e os links para onde ele vive: painel, panorama e as bases."],
  acervos: ["Bibliotecas", "Cada acervo do laboratório: quantos registros, em que segmentos, que bases responderam, e o mapa segmento por base — onde há número, onde deu erro e onde a busca ainda não rodou."],
  triagens: ["Triagens", "Cada revisão com o fluxograma PRISMA contado do banco, as decisões, os motivos de exclusão, quem está triando e o kappa entre as duas pessoas que mais triaram."],
  bases: ["Bases de dados", "Cada base com o estado da última rodada, o que trouxe, e — nas que o sistema não alcança sozinho — o que fazer para colar a estratégia."],
  caminho: ["O caminho do artigo", "Seis etapas, da pesquisa bibliográfica à publicação: o que há em cada uma agora e a tela do LAPE que a faz."],
  doze: ["Doze olhares", "Os mesmos dados por doze gráficos diferentes, cada um respondendo uma pergunta escrita em cima dele."],
};
const AUTO_SEGUNDOS = 25;

/* O que a caixa explica quando se pede "mais": uma frase por clique. É
   texto de apresentação, e não leitura dos dados -- os números continuam
   vindo do banco. */
const EXPLICA = {
  painel: ["Cada número compara com o período anterior do mesmo tamanho: sem período anterior, a seta não aparece.",
    "Na evolução mês a mês só entra quem tem a data completa; quem só tem o ano é contado à parte e dito na legenda.",
    "As leituras são regras escritas, e cada uma diz de onde saiu — não há modelo de linguagem aqui."],
  temas: ["O tempo do início à publicação é a mediana, e não a média: um artigo que levou cinco anos não puxa os outros.",
    "Taxa de aceite conta só as decisões tomadas no período: aceite, rejeição e recusa de mesa.",
    "Colaboração internacional é artigo com ao menos um autor fora do Brasil — pelo cadastro ou pela afiliação que veio da base.",
    "O radar compara as quatro linhas mais produtivas em cinco eixos, todos em porcentagem dos artigos da linha."],
  sinais: ["A faixa em volta da tendência é o intervalo de confiança de 95%: onde a tendência de verdade provavelmente está.",
    "As linhas de controle são média e média + 2 desvios: um mês acima delas merece pergunta.",
    "A deriva é a reta de mínimos quadrados: quanto a produção muda por mês, com o intervalo de confiança da inclinação.",
    "A derivada é a diferença central mês a mês: quanto a produção acelera ou freia.",
    "A integral é a área sob o acumulado — artigo-mês: quanto de acervo ficou de pé ao longo da janela.",
    "A tendência é uma média móvel centrada de doze meses; a estação é o que sobra por mês do calendário; o ruído é o resto.",
    "Inflexão é onde a tendência troca de curvatura. O limite é o teto de uma logística ajustada ao acumulado — quando há um."],
  mundo: ["A cor do país é o número de artigos com ao menos um autor de lá: um artigo Brasil–Portugal conta para os dois.",
    "O arco sai da sede e chega ao país em foco; a ficha lista as instituições cadastradas.",
    "Clique num país da lista para ir direto a ele; o botão pausa e retoma o giro."],
  busca: ["A busca ignora caixa e acento: “motivacao” acha “Motivação”.",
    "Cada resultado tem os links para onde ele vive — painel, panorama — e para as bases, com o termo já montado.",
    "Sem texto no campo, a nuvem de temas mostra por onde começar: linhas, acervos e segmentos."],
  acervos: ["Um registro pode estar em mais de um segmento: segmento é recorte de leitura, não gaveta.",
    "Célula hachurada é busca que nunca rodou naquela base; vermelha é erro da base."],
  triagens: ["O fluxograma PRISMA é contado do banco, e não digitado.",
    "O kappa só aparece com duas pessoas que triaram as mesmas referências."],
  bases: ["As três com API rodam sozinhas; as demais têm a estratégia pronta para colar."],
  caminho: ["Seis etapas, e cada uma diz qual tela do LAPE a faz."],
  doze: ["Os mesmos dados por doze gráficos: cada um responde uma pergunta escrita em cima dele."],
};
const AUTO_ANALISE_SEGUNDOS = 12;

/* As páginas, na ordem do menu. O id é o que vai no #hash. */
const ABAS = [
  ["painel", "Visão geral", "painel"],
  ["temas", "Temas e KPIs", "achado"],
  ["sinais", "Sinais e cálculo", "subida"],
  ["mundo", "Mapa-múndi ao vivo", "mapa"],
  ["busca", "Buscador temático", "explorar"],
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
  const n = el(opts.tag || "section", { class: "glass" + (opts.class ? " " + opts.class : ""),
    href: opts.href || null,
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

/* Um KPI é um botão de navegação quando tem para onde ir: `href` leva a
   outra tela (o painel, o panorama); `ir` é uma função que muda esta
   (a aba do mapa, a análise do cálculo). O cartão inteiro é o botão, e a
   seta no pé diz para onde. */
function kpiNeon(o) {
  const valor = el("div", { class: "valor" });
  const navega = !!(o.href || o.ir);
  const n = glass([
    el("div", { class: "blob", style: "--tom:" + (o.tom || NEON.blue) }),
    el("div", { class: "rotulo", style: "--tom:" + (o.tom || NEON.blue) }, [o.icon ? icone(o.icon) : null, document.createTextNode(o.rotulo)]),
    valor,
    o.extra || null,
    el("div", { class: "pe" }, [o.pe || el("span"), o.chip || null,
      navega ? el("span", { class: "ir", style: "--tom:" + (o.tom || NEON.blue), text: (o.ir_rotulo || "abrir") + " ▸" }) : null]),
  ], { i: o.i || 0, class: "kpi-neon" + (navega ? " navegavel" : ""), tag: navega ? "a" : "section",
    href: o.href || (o.ir ? "#" : null) });
  if (o.ir) n.addEventListener("click", function (ev) { ev.preventDefault(); o.ir(); });
  if (navega) n.setAttribute("title", "abrir: " + (o.ir_rotulo || o.rotulo));
  if (typeof o.valor === "number") contar(valor, o.valor);
  else { valor.textContent = o.valor; if (String(o.valor).length > 6) valor.classList.add("texto"); }
  return n;
}

/* muda de página aqui dentro, sem recarregar */
function abrirAba(aba) {
  ST.aba = aba; ST.explicadas = 0; location.hash = aba; window.scrollTo(0, 0); desenhar();
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
  /* o buscador no topo: digita, Enter, e cai na página de busca com o termo */
  const campo = el("input", { type: "search", placeholder: "Buscar tema, artigo, pessoa…", "aria-label": "Buscar",
    value: ST.busca || "" });
  campo.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") { ST.busca = campo.value; ST.aba = "busca"; location.hash = "busca"; desenhar(); }
  });
  topo.appendChild(el("label", { class: "busca-topo" }, [icone("explorar"), campo]));
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
  const destino = { publicacoes: "/#publicacoes", submissoes: "/#submetidos", aceites: "/#aceites", citacoes: "/#citacoes" }[k.code];
  return kpiNeon({ rotulo: k.rotulo, valor: k.valor, tom: tom, i: i,
    icon: { publicacoes: "livro", submissoes: "submissao", aceites: "aceite", citacoes: "citacao" }[k.code],
    pe: pe, extra: faisca, href: destino, ir_rotulo: "ver no painel" });
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
    palco.appendChild(el("h2", { class: "secao", id: "acervo-" + a.code }, [Icons.tema(a.title, { tam: 34 }),
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
      kpiNeon({ href: "/triagem", ir_rotulo: "triagem", rotulo: "Identificados nas bases", valor: f.identificados, tom: NEON.blue, i: base, icon: "explorar",
        pe: el("span", { text: f.registros + " registro(s) importados" }) }),
      kpiNeon({ href: "/triagem", ir_rotulo: "triagem", rotulo: "Repetições removidas", valor: f.duplicados, tom: NEON.magenta, i: base + 1, icon: "qualidade",
        pe: el("span", { text: "o fluxograma cobra este número" }) }),
      kpiNeon({ href: "/triagem", ir_rotulo: "triagem", rotulo: "Em triagem", valor: f.triados, tom: NEON.cyan, i: base + 2, icon: "submissao",
        pe: el("span", { text: f.pendentes + " ainda sem decisão" }) }),
      kpiNeon({ href: "/triagem", ir_rotulo: "triagem", rotulo: "Incluídos", valor: f.incluidos, tom: NEON.green, i: base + 3, icon: "aceite",
        pe: el("span", { text: f.texto_completo + " em texto completo" }) }),
      kpiNeon({ href: "/triagem", ir_rotulo: "triagem", rotulo: "Kappa da triagem", valor: t.kappa && t.kappa.kappa !== null ? String(t.kappa.kappa).replace(".", ",") : "—",
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

/* ---------------------------------------------------------- temas */
/* Os indicadores que os quatro números não contam, e os seis gráficos
   que faltavam: radar, haltere, corrida de posições, fluxo, mosaico e
   calendário. Cada KPI vem com o `pe` que diz de onde saiu. */
const TOM_NEON = { cyan: NEON.cyan, green: NEON.green, yellow: NEON.yellow, purple: NEON.purple,
  orange: NEON.orange, magenta: NEON.magenta, blue: NEON.blue, red: NEON.red };

/* Para onde cada KPI temático leva: a tela que explica o número. */
const DESTINO_DO_KPI = {
  tempo: { href: "/#tempos", rotulo: "tempos do ciclo" },
  aceite: { href: "/#submissoes", rotulo: "submissões e recusas" },
  acesso_aberto: { href: "/#publicacoes", rotulo: "publicações" },
  internacional: { aba: "mundo", rotulo: "mapa-múndi" },
  tipo: { busca: true, rotulo: "explorar" },
  orientandos: { href: "/#metas", rotulo: "objetivos do ano" },
  revistas: { href: "/#publicacoes", rotulo: "publicações" },
  paises: { aba: "mundo", rotulo: "mapa-múndi" },
};

function destinoDoKpi(k) {
  const d = DESTINO_DO_KPI[k.code];
  if (!d) return {};
  if (d.aba) return { ir: function () { abrirAba(d.aba); }, ir_rotulo: d.rotulo };
  if (d.busca) return { href: "/?q=" + encodeURIComponent(String(k.valor || "")) + "#explorar", ir_rotulo: d.rotulo };
  return { href: d.href, ir_rotulo: d.rotulo };
}

/* O radar da casa é uma figura de 380px para uma coluna de tabela. Aqui
   ele é o cartão inteiro: polígonos preenchidos com brilho, anéis com a
   porcentagem escrita, o valor em cada ponta ao passar o mouse, e a
   legenda que isola uma linha ao clique. */
const NS_SVG = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs, kids) {
  const n = document.createElementNS(NS_SVG, tag);
  Object.keys(attrs || {}).forEach(function (k) { if (attrs[k] !== null && attrs[k] !== undefined) n.setAttribute(k, attrs[k]); });
  (kids || []).forEach(function (k) { if (k) n.appendChild(k); });
  return n;
}
function svgTexto(attrs, texto) { const t = svgEl("text", attrs); t.textContent = texto; return t; }

function radarNeon(axes, series, opts) {
  opts = opts || {};
  const W = 640, H = 500, cx = W / 2, cy = H / 2 + 8, R = Math.min(W, H) / 2 - 74;
  /* a escala vai até o degrau (25, 50, 75, 100) que cobre o maior valor:
     quatro linhas com 30% ficariam num pontinho no centro de um radar de 100 */
  const maior = Math.max(1, ...series.map(function (sr) { return Math.max.apply(null, sr.values); }));
  const max = opts.max || ([25, 50, 75, 100].find(function (d) { return d >= maior; }) || 100);
  const ang = function (i) { return -Math.PI / 2 + 2 * Math.PI * i / axes.length; };
  const ponto = function (i, v) { const r = R * Math.max(0, Math.min(max, v)) / max; return [cx + r * Math.cos(ang(i)), cy + r * Math.sin(ang(i))]; };
  const svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, class: "radar-neon", role: "img", "aria-label": opts.caption || "radar" });
  svg.style.width = "100%"; svg.style.height = "auto";
  const defs = svgEl("defs");
  series.forEach(function (sr, si) {
    const g = svgEl("radialGradient", { id: "rad-" + si, cx: "50%", cy: "50%", r: "70%" });
    g.appendChild(svgEl("stop", { offset: "0%", "stop-color": sr.color, "stop-opacity": ".55" }));
    g.appendChild(svgEl("stop", { offset: "100%", "stop-color": sr.color, "stop-opacity": ".08" }));
    defs.appendChild(g);
  });
  svg.appendChild(defs);
  /* anéis com a porcentagem escrita */
  [1, 2, 3, 4].map(function (k) { return max * k / 4; }).forEach(function (p) {
    const d = axes.map(function (_, i) { const q = ponto(i, p); return (i ? "L" : "M") + q[0].toFixed(1) + "," + q[1].toFixed(1); }).join("") + "Z";
    svg.appendChild(svgEl("path", { d: d, fill: p === max ? "rgba(255,255,255,.02)" : "none", stroke: "rgba(255,255,255," + (p === max ? ".22" : ".1") + ")", "stroke-width": p === max ? 1.4 : 1, "stroke-dasharray": p === max ? null : "3 4" }));
    svg.appendChild(svgTexto({ x: cx + 6, y: cy - R * p / max + 12, class: "anel", "font-size": 11, fill: "rgba(244,247,255,.5)" }, Math.round(p) + "%"));
  });
  /* eixos e rótulos */
  axes.forEach(function (a, i) {
    const fim = ponto(i, max);
    svg.appendChild(svgEl("line", { x1: cx, y1: cy, x2: fim[0], y2: fim[1], stroke: "rgba(255,255,255,.14)", "stroke-width": 1 }));
    const rot = ponto(i, max * 1.16);
    const c = Math.cos(ang(i));
    svg.appendChild(svgTexto({ x: rot[0], y: rot[1] + 5, "text-anchor": Math.abs(c) < 0.2 ? "middle" : (c > 0 ? "start" : "end"),
      "font-size": 14, "font-weight": 700, fill: "rgba(244,247,255,.92)" }, a));
  });
  /* os polígonos, do maior para o menor, para nenhum esconder o outro */
  const grupos = [];
  series.forEach(function (sr, si) {
    const pts = sr.values.map(function (v, i) { return ponto(i, v); });
    const d = pts.map(function (q, i) { return (i ? "L" : "M") + q[0].toFixed(1) + "," + q[1].toFixed(1); }).join("") + "Z";
    const g = svgEl("g", { class: "serie", "data-serie": si });
    g.appendChild(svgEl("path", { d: d, fill: "url(#rad-" + si + ")", stroke: sr.color, "stroke-width": 2.6, "stroke-linejoin": "round", class: "mark", style: "filter:drop-shadow(0 0 8px " + sr.color + ")" }));
    pts.forEach(function (q, i) {
      const dot = svgEl("circle", { cx: q[0], cy: q[1], r: 5.5, fill: sr.color, stroke: "var(--navy-deep)", "stroke-width": 2 });
      const rotulo = svgTexto({ x: q[0], y: q[1] - 11, "text-anchor": "middle", "font-size": 12, "font-weight": 800, fill: sr.color, class: "valor-ponta" }, Math.round(sr.values[i]) + "%");
      const t = svgEl("title"); t.textContent = sr.label + " · " + axes[i] + ": " + sr.values[i] + "%";
      dot.appendChild(t);
      g.appendChild(rotulo); g.appendChild(dot);
    });
    grupos.push(g);
    svg.appendChild(g);
  });
  const caixa = el("div", { class: "radar-caixa" }, [svg]);
  /* legenda que isola: clique numa linha e só ela fica acesa */
  let aceso = null;
  const legenda = el("div", { class: "legenda-radar" }, series.map(function (sr, si) {
    const chipEl = el("button", { type: "button", class: "chip solto", style: "--tom:" + sr.color }, [
      sr.icone && sr.icone !== "linha" ? Icons.tema(sr.label, { icone: sr.icone, tam: 22, tom: sr.color }) : el("i"),
      document.createTextNode(sr.label)]);
    chipEl.addEventListener("click", function () {
      aceso = aceso === si ? null : si;
      grupos.forEach(function (g, gi) { g.classList.toggle("apagado", aceso !== null && gi !== aceso); });
      legenda.querySelectorAll(".chip").forEach(function (c, ci) { c.classList.toggle("apagado", aceso !== null && ci !== aceso); });
    });
    return chipEl;
  }));
  caixa.appendChild(legenda);
  return caixa;
}

/* O haltere: de um período para o outro, com a variação escrita e colorida.
   Verde subiu, vermelho desceu, cinza ficou. A bolinha do "antes" é vazada
   e a do "depois" é cheia: o olho vai para o agora. */
function haltereNeon(items, opts) {
  opts = opts || {};
  const ordenados = items.slice().sort(function (a, b) { return (b.to - b.from) - (a.to - a.from); });
  const linhaH = 44, ML = 210, MR = 80, W = 600, MT = 28, MB = 32;
  const H = MT + MB + ordenados.length * linhaH;
  const max = Math.max(1, ...ordenados.map(function (i) { return Math.max(i.from, i.to); }));
  const X = function (v) { return ML + (W - ML - MR) * v / max; };
  const svg = svgEl("svg", { viewBox: "0 0 " + W + " " + H, class: "haltere-neon", role: "img", "aria-label": opts.caption || "antes e depois" });
  svg.style.width = "100%"; svg.style.height = "auto";
  const passo = max <= 5 ? 1 : (max <= 12 ? 2 : (max <= 30 ? 5 : 10));
  for (let t = 0; t <= max; t += passo) {
    svg.appendChild(svgEl("line", { x1: X(t), x2: X(t), y1: MT - 6, y2: H - MB + 4, stroke: "rgba(255,255,255,.08)" }));
    svg.appendChild(svgTexto({ x: X(t), y: H - MB + 20, "text-anchor": "middle", "font-size": 11, fill: "rgba(244,247,255,.5)" }, String(t)));
  }
  ordenados.forEach(function (it, i) {
    const y = MT + i * linhaH + linhaH / 2;
    const delta = it.to - it.from;
    const tom = delta > 0 ? NEON.green : (delta < 0 ? NEON.red : "rgba(244,247,255,.45)");
    const g = svgEl("g", { class: "linha-haltere", style: "--i:" + i });
    g.appendChild(svgTexto({ x: ML - 14, y: y + 5, "text-anchor": "end", "font-size": 13, "font-weight": 600, fill: "rgba(244,247,255,.9)" }, cortar(it.label, 26)));
    const grad = svgEl("linearGradient", { id: "hal-" + i, x1: "0", x2: "1", y1: "0", y2: "0" });
    grad.appendChild(svgEl("stop", { offset: "0%", "stop-color": "rgba(244,247,255,.35)" }));
    grad.appendChild(svgEl("stop", { offset: "100%", "stop-color": tom }));
    svg.appendChild(svgEl("defs", {}, [grad]));
    if (it.from !== it.to) {
      g.appendChild(svgEl("line", { x1: X(Math.min(it.from, it.to)), x2: X(Math.max(it.from, it.to)), y1: y, y2: y, stroke: "url(#hal-" + i + ")", "stroke-width": 8, "stroke-linecap": "round", class: "mark", style: "filter:drop-shadow(0 0 6px " + tom + ")" }));
    }
    g.appendChild(svgEl("circle", { cx: X(it.from), cy: y, r: 8, fill: "var(--navy-deep)", stroke: "rgba(244,247,255,.6)", "stroke-width": 2.2 }));
    g.appendChild(svgEl("circle", { cx: X(it.to), cy: y, r: 9, fill: tom, stroke: "var(--navy-deep)", "stroke-width": 2, class: "mark", style: "filter:drop-shadow(0 0 8px " + tom + ")" }));
    g.appendChild(svgTexto({ x: X(it.from), y: y - 14, "text-anchor": "middle", "font-size": 11, fill: "rgba(244,247,255,.55)" }, String(it.from)));
    g.appendChild(svgTexto({ x: X(it.to), y: y - 14, "text-anchor": "middle", "font-size": 12, "font-weight": 800, fill: tom }, String(it.to)));
    g.appendChild(svgTexto({ x: W - MR + 14, y: y + 5, "font-size": 13, "font-weight": 800, fill: tom }, (delta > 0 ? "▲ +" : (delta < 0 ? "▼ " : "= ")) + delta));
    const t = svgEl("title"); t.textContent = it.label + ": " + it.from + " → " + it.to;
    g.appendChild(t);
    svg.appendChild(g);
  });
  const legenda = el("div", { class: "legenda-haltere" }, [
    el("span", {}, [el("i", { class: "vazia" }), document.createTextNode(opts.antes || "antes")]),
    el("span", {}, [el("i", { class: "cheia" }), document.createTextNode(opts.depois || "depois")]),
    el("span", {}, [el("i", { style: "background:" + NEON.green }), document.createTextNode("subiu")]),
    el("span", {}, [el("i", { style: "background:" + NEON.red }), document.createTextNode("desceu")]),
  ]);
  return el("div", { class: "haltere-caixa" }, [svg, legenda]);
}

function desenharTemas(palco) {
  const T = D.temas;
  const per = D.periodo;
  palco.appendChild(cabeca("achado", "Temas e indicadores",
    "os KPIs temáticos de " + rotuloDoPeriodo(per.de, per.ate) + " e os gráficos que faltavam"));
  const kpis = el("div", { class: "grade kpis" });
  T.kpis.forEach(function (k, i) {
    const tom = TOM_NEON[k.tom] || NEON.blue;
    const valor = k.valor === null || k.valor === undefined ? "—"
      : (typeof k.valor === "number" ? k.valor : String(k.valor));
    kpis.appendChild(kpiNeon(Object.assign({ rotulo: k.rotulo, valor: valor, tom: tom, i: i, icon: k.icon,
      extra: k.unidade ? el("span", { class: "unidade", text: k.unidade }) : null,
      pe: el("span", { text: k.pe || "" }) }, destinoDoKpi(k))));
  });
  palco.appendChild(kpis);

  const um = el("div", { class: "grade baixo" });
  um.appendChild(glass([
    cabecalho("Radar das linhas", "as quatro mais produtivas, em % dos artigos de cada uma"),
    T.radar.series.length
      ? radarNeon(T.radar.axes, T.radar.series.map(function (s, i) { return { label: s.label, values: s.values, icone: s.icone, color: NEON_SEQ[i % NEON_SEQ.length] }; }),
        { caption: "radar por linha" })
      : el("div", { class: "vazio", text: "sem artigos ligados a linhas" }),
  ], { i: 8 }));
  um.appendChild(glass([
    cabecalho("Haltere: de um período para o outro", per.anterior
      ? "publicados por linha, " + rotuloDoPeriodo(per.anterior[0], per.anterior[1]) + " → " + rotuloDoPeriodo(per.de, per.ate)
      : "sem período anterior para comparar"),
    T.haltere.length
      ? haltereNeon(T.haltere, { caption: "antes e depois por linha",
        antes: per.anterior ? rotuloDoPeriodo(per.anterior[0], per.anterior[1]) : "antes", depois: rotuloDoPeriodo(per.de, per.ate) })
      : el("div", { class: "vazio", text: "nada publicado nos dois períodos" }),
  ], { i: 9 }));
  palco.appendChild(um);

  const dois = el("div", { class: "grade baixo" });
  dois.appendChild(glass([
    cabecalho("Corrida de posições", "a posição de cada linha em publicados, ano a ano"),
    T.bump.series.length
      ? C.bump({ labels: T.bump.labels, caption: "posição por ano",
        series: T.bump.series.map(function (s, i) { return { label: s.label, values: s.values, color: NEON_SEQ[i % NEON_SEQ.length] }; }) })
      : el("div", { class: "vazio", text: "sem publicados nos últimos anos" }),
  ], { i: 10 }));
  dois.appendChild(glass([
    cabecalho("Do desenho à situação", "que tipo de estudo está em que ponto do caminho — todo o acervo"),
    T.sankey.links.length
      ? C.sankey({ nodes: T.sankey.nodes, links: T.sankey.links, height: 360, caption: "tipo de estudo → situação" })
      : el("div", { class: "vazio", text: "sem artigos com situação" }),
  ], { i: 11 }));
  palco.appendChild(dois);

  const tres = el("div", { class: "grade baixo" });
  tres.appendChild(glass([
    cabecalho("Onde se publica", "mosaico das revistas — todo o acervo publicado"),
    T.treemap.length
      ? C.treemap({ items: T.treemap.map(function (t, i) { return { label: t.label, value: t.value, color: NEON_SEQ[i % NEON_SEQ.length] }; }),
        height: 320, caption: "revistas" })
      : el("div", { class: "vazio", text: "nenhum publicado com revista" }),
  ], { i: 12 }));
  tres.appendChild(glass([
    cabecalho("Calendário de " + T.calendario.year, T.calendario.total + " acontecimento(s): publicação, submissão, aceite, triagem e atividade"),
    T.calendario.total
      ? C.calendarHeat({ days: T.calendario.days, year: T.calendario.year, unit: "acontecimentos", caption: "calendário" })
      : el("div", { class: "vazio", text: "nada datado neste ano" }),
  ], { i: 13 }));
  palco.appendChild(tres);
}

/* --------------------------------------------------------- sinais */
/* A curva mensal lida com cálculo. Cada análise tem o seu botão temático;
   o gráfico se desenha em tempo real ao entrar ("Rodar"), e "Auto" passa
   sozinho de uma análise para a outra, com anterior/seguinte. */
const ANALISES = [
  ["curva", "Curva", "subida", "Publicações por mês, com a tendência por cima: média móvel centrada de doze meses (2×12). A tendência é o sinal; o resto é estação e ruído."],
  ["acumulado", "Acumulado", "barras", "O acervo publicado ao fim de cada mês — sobe e nunca desce. É o nível de que a curva mensal é a derivada."],
  ["derivada", "Derivada", "raio", "Diferença central mês a mês: quanto a produção acelera (positivo) ou freia (negativo). A segunda derivada diz se a aceleração está aumentando."],
  ["integral", "Integral e área", "espaco", "Área sob o acumulado, pelo trapézio: artigo-mês — quanto de acervo o laboratório manteve de pé ao longo da janela. A área acumulada mostra como ela cresce."],
  ["decomposicao", "Sinal e ruído", "rede", "Tendência + estação + ruído. A estação é o que sobra, em média, em cada mês do calendário; o ruído é o que nenhuma das duas explica. A razão sinal/ruído diz quanto a curva é mais tendência do que acaso."],
  ["inflexao", "Inflexões", "alvo", "Onde a tendência troca de curvatura: passa a acelerar ou a desacelerar. É a segunda derivada da tendência trocando de sinal — da série crua ela trocaria todo mês."],
  ["limite", "Limite", "tempo", "O teto de uma logística ajustada ao acumulado, por busca em grade — quando o ajuste explica mais do que uma reta. Se não explica, o acumulado ainda cresce em linha e não há teto à vista."],
  ["deriva", "Deriva e projeção", "foguete", "A reta de mínimos quadrados sobre a curva mensal: a deriva é quanto a produção muda, em média, mês após mês, com o intervalo de confiança da inclinação. A projeção segue a deriva a partir da ponta da tendência, tracejada, com a faixa que alarga com a distância."],
];
let relogioAnalise = null;

function pararAnalise() { clearInterval(relogioAnalise); relogioAnalise = null; }

function derivar(v) {
  const n = v.length;
  if (n < 2) return v.map(function () { return 0; });
  return v.map(function (_, i) {
    if (i === 0) return v[1] - v[0];
    if (i === n - 1) return v[n - 1] - v[n - 2];
    return (v[i + 1] - v[i - 1]) / 2;
  });
}

/* o gráfico "roda": as linhas se desenham da esquerda para a direita, as
   colunas crescem do chão e os pontos acendem em sequência */
function rodar(fig) {
  if (SEM_MOVIMENTO) return;
  const caminhos = fig.querySelectorAll("path");
  caminhos.forEach(function (p) {
    let len = 0;
    try { len = p.getTotalLength(); } catch (e) { return; }
    if (!len) return;
    const preenchido = p.getAttribute("fill") && p.getAttribute("fill") !== "none";
    p.style.transition = "none";
    p.style.strokeDasharray = len + " " + len;
    p.style.strokeDashoffset = String(len);
    if (preenchido) p.style.opacity = "0";
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      p.style.transition = "stroke-dashoffset 1.8s ease-out, opacity 1.2s ease-out .5s";
      p.style.strokeDashoffset = "0";
      if (preenchido) p.style.opacity = "";
    }); });
  });
  const pontos = fig.querySelectorAll("circle");
  pontos.forEach(function (c, i) {
    c.style.opacity = "0"; c.style.transition = "opacity .25s";
    setTimeout(function () { c.style.opacity = ""; }, 150 + i * Math.min(60, 1600 / Math.max(1, pontos.length)));
  });
  fig.querySelectorAll("rect.mark").forEach(function (r, i) {
    r.classList.remove("cresce"); void r.getBBox; r.classList.add("cresce");
    r.style.animationDelay = Math.min(1200, i * 22) + "ms";
  });
}

function figuraDaAnalise(code) {
  const S = D.sinais;
  const meses = S.meses;
  const linha = function (label, values, color, extra) { return Object.assign({ label: label, values: values, color: color }, extra || {}); };
  const faixa = function (ic) { return ic && ic.alto ? { band: ic } : {}; };
  const controle = S.controle && S.controle.media !== null ? [
    { valor: S.controle.media, rotulo: "média " + String(S.controle.media).replace(".", ","), cor: NEON.yellow, dash: "2 4" },
    { valor: S.controle.alto, rotulo: "limite de controle (+2σ)", cor: NEON.red },
  ] : [];
  /* toda inflexão ganha a marca; só as três últimas ganham o texto --
     catorze rótulos em cima uns dos outros não se leem */
  const marcasDeInflexao = function (serie) {
    const todas = S.inflexoes || [];
    return todas.map(function (x, k) {
      const acelera = x.sentido.indexOf("acelerar") >= 0;
      return { serie: serie, i: x.i, label: k >= todas.length - 3 ? (acelera ? "▲ acelera" : "▼ desacelera") : "", tone: acelera ? "good" : "critical" };
    });
  };
  switch (code) {
    case "curva":
      return [C.lines({ labels: meses, height: 340, caption: "publicações por mês, tendência com IC 95% e limites de controle",
        limites: controle, marks: marcasDeInflexao(1),
        series: [linha("publicados/mês", S.valores, NEON.cyan, { area: true, width: 2 }),
          linha("tendência (12 meses) · faixa IC 95%", S.tendencia, NEON.orange, faixa(S.tendencia_ic))] })];
    case "acumulado":
      return [C.lines({ labels: meses, height: 340, caption: "acumulado, com o ajuste e o teto",
        max: S.limite && S.limite.K ? S.limite.K * 1.06 : undefined,   /* o teto precisa caber no eixo */
        limites: S.limite && S.limite.K ? [{ valor: S.limite.K, rotulo: "teto K = " + C.fmt(S.limite.K), cor: NEON.red }] : [],
        series: [linha("acervo publicado", S.acumulado, NEON.blue, { area: true })].concat(
          S.limite && S.limite.K ? [linha("ajuste logístico · faixa ± 1,96 σ", S.limite.ajuste, NEON.green, { band: { alto: S.limite.alto, baixo: S.limite.baixo }, dash: "6 5" })] : []) })];
    case "derivada":
      return [
        C.lines({ labels: meses, height: 300, caption: "derivada, suavizada com IC 95%",
          limites: [{ valor: 0, rotulo: "zero: nem acelera nem freia", cor: "rgba(244,247,255,.55)", dash: "2 4" }],
          series: [linha("derivada (pub/mês por mês)", S.derivada, NEON.green, { area: true, width: 1.6 }),
            linha("derivada suavizada (3 meses) · IC 95%", S.derivada_suave, NEON.yellow, faixa(S.derivada_ic))] }),
        C.lines({ labels: meses, height: 200, caption: "segunda derivada",
          limites: [{ valor: 0, rotulo: "", cor: "rgba(244,247,255,.45)", dash: "2 4" }],
          series: [linha("segunda derivada", S.segunda_derivada, NEON.magenta, { area: true })] }),
      ];
    case "integral":
      return [
        C.lines({ labels: meses, height: 280, caption: "área sob o acumulado (a sombra é a integral)",
          series: [linha("acumulado", S.acumulado, NEON.purple, { area: true })] }),
        C.lines({ labels: meses, height: 220, caption: "área acumulada",
          limites: [{ valor: S.integral.area, rotulo: "área total " + C.fmt(Math.round(S.integral.area)) + " artigo-mês", cor: NEON.yellow }],
          series: [linha("área acumulada (artigo-mês)", S.integral.acumulada, NEON.yellow, { area: true })] }),
      ];
    case "decomposicao":
      return [
        C.lines({ labels: meses, height: 260, caption: "observado, tendência e a faixa do ruído",
          limites: controle,
          series: [linha("observado", S.valores, NEON.cyan, { area: true, width: 1.6 }),
            linha("tendência · IC 95%", S.tendencia, NEON.orange, faixa(S.tendencia_ic))] }),
        C.columns({ labels: ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
          values: S.perfil_sazonal, name: "estação (desvio médio do mês)", height: 200, caption: "estação" }),
        C.lines({ labels: meses, height: 200, caption: "ruído, com ± 2 desvios",
          limites: [{ valor: 2 * S.dp_ruido, rotulo: "+2σ", cor: NEON.red }, { valor: -2 * S.dp_ruido, rotulo: "−2σ", cor: NEON.red }, { valor: 0, rotulo: "", cor: "rgba(244,247,255,.45)", dash: "2 4" }],
          series: [linha("ruído", S.ruido, NEON.magenta, { area: true, width: 1.4 })] }),
      ];
    case "inflexao": {
      const seg = derivar(derivar(S.tendencia));
      return [
        C.lines({ labels: meses, height: 280, caption: "tendência com IC 95% e as inflexões marcadas",
          marks: marcasDeInflexao(0),
          series: [linha("tendência", S.tendencia, NEON.orange, Object.assign({ area: true }, faixa(S.tendencia_ic)))] }),
        C.lines({ labels: meses, height: 200, caption: "curvatura da tendência",
          limites: [{ valor: 0, rotulo: "troca de sinal = inflexão", cor: "rgba(244,247,255,.55)", dash: "2 4" }],
          series: [linha("segunda derivada da tendência", seg.map(function (x) { return Math.round(x * 1000) / 1000; }), NEON.magenta, { area: true })] }),
      ];
    }
    case "limite": {
      const series = [linha("acumulado", S.acumulado, NEON.blue, { area: true })];
      const limites = [];
      if (S.limite && S.limite.K) {
        series.push(linha("ajuste logístico · faixa ± 1,96 σ", S.limite.ajuste, NEON.green, { band: { alto: S.limite.alto, baixo: S.limite.baixo }, dash: "6 5" }));
        limites.push({ valor: S.limite.K, rotulo: "teto K = " + C.fmt(S.limite.K) + " (" + String(S.limite.atingido).replace(".", ",") + "% atingido)", cor: NEON.red });
      }
      return [C.lines({ labels: meses, height: 340, caption: "limite", series: series, limites: limites,
        max: S.limite && S.limite.K ? S.limite.K * 1.06 : undefined })];
    }
    case "deriva": {
      const R = S.regressao || {};
      const P = S.projecao || {};
      const figs = [C.lines({ labels: meses, height: 300, caption: "a reta de mínimos quadrados com IC 95%",
        limites: controle,
        series: [linha("publicados/mês", S.valores, NEON.cyan, { area: true, width: 1.6 }),
          linha("deriva: " + (R.b !== null && R.b !== undefined ? (R.b >= 0 ? "+" : "") + String(R.deriva_mes).replace(".", ",") + " por mês" : "—"), R.linha || [], NEON.yellow, { band: R.alto ? { alto: R.alto, baixo: R.baixo } : undefined, width: 3 })] })];
      if (P.valores && P.valores.length > 1) {
        figs.push(C.lines({ labels: P.meses, height: 240, caption: "projeção pela deriva (tracejada): próximos " + (P.valores.length - 1) + " meses",
          limites: S.controle && S.controle.media !== null ? [{ valor: S.controle.media, rotulo: "média histórica", cor: NEON.yellow, dash: "2 4" }] : [],
          series: [linha("projeção · faixa IC 95%", P.valores, NEON.magenta, { band: { alto: P.alto, baixo: P.baixo }, dash: "6 5" })] }));
      }
      return figs;
    }
    default:
      return [el("div", { class: "vazio", text: "análise desconhecida" })];
  }
}

function leituraDaAnalise(code) {
  const S = D.sinais;
  const pt = function (n, casas) { return (Number(n) || 0).toFixed(casas === undefined ? 2 : casas).replace(".", ","); };
  switch (code) {
    case "curva": return "Ritmo dos últimos 12 meses: " + pt(S.ritmo) + " pub/mês"
      + (S.ritmo_antes !== null ? " (antes: " + pt(S.ritmo_antes) + ")" : "") + " · " + S.soma + " publicado(s) na janela"
      + (S.sem_mes ? " · " + S.sem_mes + " só com o ano ficam fora" : "");
    case "acumulado": return "De " + C.fmt(S.base_antes) + " no início da janela a " + C.fmt(S.acumulado[S.acumulado.length - 1]) + " hoje.";
    case "derivada": {
      const u = S.derivada[S.derivada.length - 1];
      return "Último valor: " + pt(u) + " — a produção " + (u > 0 ? "está acelerando" : (u < 0 ? "está freando" : "está estável")) + ".";
    }
    case "integral": return "Área sob o acumulado: " + C.fmt(Math.round(S.integral.area)) + " artigo-mês na janela.";
    case "decomposicao": return S.sinal_ruido === null ? "Sem ruído mensurável."
      : "Razão sinal/ruído " + pt(S.sinal_ruido) + " (desvio da tendência " + pt(S.dp_sinal) + " ÷ desvio do ruído " + pt(S.dp_ruido) + "): "
        + (S.sinal_ruido >= 1 ? "mais sinal do que ruído." : "mais ruído do que sinal.");
    case "inflexao": return S.inflexoes.length
      ? S.inflexoes.length + " inflexão(ões); a última em " + S.inflexoes[S.inflexoes.length - 1].rotulo + ": a tendência " + S.inflexoes[S.inflexoes.length - 1].sentido + "."
      : "Sem inflexão: a tendência não trocou de curvatura na janela.";
    case "limite": return S.limite && S.limite.K
      ? "Teto de " + C.fmt(S.limite.K) + " artigos, " + pt(S.limite.atingido, 0) + "% atingido (R² " + pt(S.limite.r2) + " contra " + pt(S.limite.r2_reta) + " da reta)."
      : "Sem limite à vista: " + (S.limite ? S.limite.porque : "") + ".";
    case "deriva": {
      const R = S.regressao || {};
      if (R.b === null || R.b === undefined) return "Poucos pontos para uma reta.";
      const P = S.projecao || {};
      return "Deriva de " + (R.deriva_mes >= 0 ? "+" : "") + pt(R.deriva_mes, 3) + " pub/mês por mês (" + (R.deriva_ano >= 0 ? "+" : "") + pt(R.deriva_ano) + " por ano; IC 95% da inclinação "
        + pt(R.ic_deriva[0], 3) + " a " + pt(R.ic_deriva[1], 3) + "; R² " + pt(R.r2) + ")"
        + (P.valores && P.valores.length > 1 ? " · em " + (P.valores.length - 1) + " meses a tendência aponta " + pt(P.valores[P.valores.length - 1]) + " pub/mês (faixa " + pt(P.baixo[P.baixo.length - 1]) + " a " + pt(P.alto[P.alto.length - 1]) + ")." : ".");
    }
    default: return "";
  }
}

function desenharSinais(palco) {
  const S = D.sinais;
  palco.appendChild(cabeca("subida", "Sinais e cálculo",
    "a curva mensal de publicações lida com cálculo — " + S.labels[0] + " a " + S.labels[S.labels.length - 1]));

  const kpis = el("div", { class: "grade kpis" }, [
    kpiNeon({ rotulo: "Ritmo (12 meses)", valor: S.ritmo, tom: NEON.cyan, i: 0, icon: "subida",
      ir: function () { ST.analise = "curva"; desenhar(); }, ir_rotulo: "curva",
      extra: el("span", { class: "unidade", text: "publicações por mês" }),
      pe: el("span", { text: S.ritmo_antes !== null ? "antes: " + String(S.ritmo_antes).replace(".", ",") : "sem 12 meses anteriores" }) }),
    kpiNeon({ rotulo: "Sinal / ruído", valor: S.sinal_ruido === null ? "—" : String(S.sinal_ruido).replace(".", ","), tom: NEON.orange, i: 1, icon: "rede",
      ir: function () { ST.analise = "decomposicao"; desenhar(); }, ir_rotulo: "sinal e ruído",
      pe: el("span", { text: S.sinal_ruido === null ? "sem ruído mensurável" : (S.sinal_ruido >= 1 ? "mais sinal do que ruído" : "mais ruído do que sinal") }) }),
    kpiNeon({ rotulo: "Inflexões", valor: S.inflexoes.length, tom: NEON.magenta, i: 2, icon: "alvo",
      ir: function () { ST.analise = "inflexao"; desenhar(); }, ir_rotulo: "inflexões",
      pe: el("span", { text: S.inflexoes.length ? "última em " + S.inflexoes[S.inflexoes.length - 1].rotulo : "a tendência não trocou de curvatura" }) }),
    kpiNeon({ rotulo: "Limite à vista", valor: S.limite && S.limite.K ? S.limite.K : "—", tom: NEON.green, i: 3, icon: "tempo",
      ir: function () { ST.analise = "limite"; desenhar(); }, ir_rotulo: "limite",
      extra: S.limite && S.limite.K ? el("span", { class: "unidade", text: String(S.limite.atingido).replace(".", ",") + "% atingido" }) : null,
      pe: el("span", { text: S.limite && S.limite.K ? "teto do ajuste logístico" : (S.limite ? S.limite.porque : "") }) }),
    kpiNeon({ rotulo: "Área (integral)", valor: Math.round(S.integral.area), tom: NEON.purple, i: 4, icon: "espaco",
      ir: function () { ST.analise = "integral"; desenhar(); }, ir_rotulo: "integral",
      extra: el("span", { class: "unidade", text: "artigo-mês" }), pe: el("span", { text: "sob o acumulado, na janela" }) }),
  ]);
  palco.appendChild(kpis);

  const indice = Math.max(0, ANALISES.findIndex(function (a) { return a[0] === ST.analise; }));
  const atual = ANALISES[indice];
  const botoes = el("div", { class: "analises", role: "tablist" }, ANALISES.map(function (a, i) {
    return el("button", { type: "button", class: "tematico" + (i === indice ? " on" : ""), style: "--tom:" + NEON_SEQ[i % NEON_SEQ.length],
      role: "tab", "aria-selected": i === indice ? "true" : "false",
      onclick: function () { ST.analise = a[0]; desenhar(); } }, [icone(a[2]), el("span", { text: a[1] })]);
  }));
  palco.appendChild(glass([botoes], { i: 5, class: "faixa-botoes" }));

  const figuras = el("div", { class: "figuras" });
  figuraDaAnalise(atual[0]).forEach(function (f) { figuras.appendChild(f); });
  const barra = el("div", { class: "barra-analise" }, [el("i")]);
  const controles = el("div", { class: "controles-analise" }, [
    el("button", { type: "button", text: "◀", "aria-label": "análise anterior", onclick: function () { ST.analise = ANALISES[(indice - 1 + ANALISES.length) % ANALISES.length][0]; desenhar(); } }),
    el("button", { type: "button", class: "rodar", text: "Rodar ▶", onclick: function () { rodar(figuras); } }),
    el("button", { type: "button", class: ST.autoAnalise ? "on" : "", text: ST.autoAnalise ? "Auto: ligado" : "Auto (" + AUTO_ANALISE_SEGUNDOS + " s)",
      onclick: function () { ST.autoAnalise = !ST.autoAnalise; desenhar(); } }),
    el("button", { type: "button", text: "▶", "aria-label": "próxima análise", onclick: function () { ST.analise = ANALISES[(indice + 1) % ANALISES.length][0]; desenhar(); } }),
  ]);
  const cartao = glass([
    cabecalho((indice + 1) + " de " + ANALISES.length + " · " + atual[1], atual[3], controles),
    figuras,
    el("div", { class: "leitura-analise" }, [icone("achado"), document.createTextNode(leituraDaAnalise(atual[0]))]),
    atual[0] === "inflexao" && S.inflexoes.length ? el("div", { class: "linhas-chips" }, S.inflexoes.map(function (x, i) {
      return chip(x.sentido.indexOf("acelerar") >= 0 ? NEON.green : NEON.red, x.rotulo + " · " + x.sentido); })) : null,
    barra,
  ], { i: 6, class: "cartao-analise" });
  palco.appendChild(cartao);
  requestAnimationFrame(function () { rodar(figuras); });

  pararAnalise();
  if (ST.autoAnalise) {
    let decorrido = 0, ultimo = performance.now();
    relogioAnalise = setInterval(function () {
      const agora = performance.now();
      if (!document.hidden) decorrido += agora - ultimo;
      ultimo = agora;
      const k = Math.min(1, decorrido / (AUTO_ANALISE_SEGUNDOS * 1000));
      barra.firstChild.style.width = (k * 100).toFixed(1) + "%";
      if (k >= 1) { ST.analise = ANALISES[(indice + 1) % ANALISES.length][0]; desenhar(); }
    }, 200);
  }
}

/* ---------------------------------------------------------- mundo */
/* O globo em canvas, girando em tempo real. Não é o `Charts.globo`: aquele
   monta um SVG de trezentos caminhos para uma foto parada, e refazê-lo a
   sessenta quadros por segundo seria o navegador ocupado com DOM em vez de
   com o desenho. Aqui é um canvas, e a Terra inteira (4.800 pontos) se
   redesenha num milissegundo.

   O roteiro: gira; a cada tantos segundos escolhe o próximo país que assina
   com o laboratório, viaja até ele (o arco sai da sede), pousa — anéis, o
   país aceso, a ficha ao lado — e volta a girar. */
const TOUR_GIRO_MS = 2600, TOUR_VIAGEM_MS = 1900, TOUR_POUSO_MS = 4800;
let GLOBO = null;

function pararGlobo() { if (GLOBO) { GLOBO.parar(); GLOBO = null; } }

function Globo(canvas, dados, ficha) {
  this.canvas = canvas; this.ctx = canvas.getContext("2d");
  this.dados = dados; this.ficha = ficha;
  this.contorno = D.contorno || [];
  this.sede = dados.sede;
  this.lon0 = this.sede.longitude; this.lat0 = Math.max(-45, Math.min(45, this.sede.latitude));
  this.roteiro = dados.paises.slice().sort(function (a, b) { return b.n - a.n; });
  this.valores = {};
  const self = this;
  dados.paises.forEach(function (p) { self.valores[p.pais] = p.n; });
  this.max = Math.max(1, ...dados.paises.map(function (p) { return p.n; }));
  this.indice = -1; this.alvo = null; this.viagem = null; this.efeitos = [];
  this.fase = SEM_MOVIMENTO ? "parado" : "girando";
  this.girando = !SEM_MOVIMENTO;
  this.proximaParada = performance.now() + TOUR_GIRO_MS;
  this.ultimo = performance.now();
  this.medir();
  this.raf = requestAnimationFrame(this.laco.bind(this));
  this.observador = new ResizeObserver(this.medir.bind(this));
  this.observador.observe(canvas.parentElement);
}
Globo.prototype.medir = function () {
  const largura = Math.max(240, Math.min(720, this.canvas.parentElement.clientWidth || 600));
  const dpr = window.devicePixelRatio || 1;
  this.W = largura; this.H = largura;
  this.canvas.width = Math.round(largura * dpr); this.canvas.height = Math.round(largura * dpr);
  this.canvas.style.width = largura + "px"; this.canvas.style.height = largura + "px";
  this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  this.R = largura / 2 - 10; this.CX = largura / 2; this.CY = largura / 2;
};
Globo.prototype.parar = function () {
  cancelAnimationFrame(this.raf); this.raf = null;
  if (this.observador) this.observador.disconnect();
};
Globo.prototype.projetar = function (lon, lat) {
  const rad = Math.PI / 180;
  const dl = (lon - this.lon0) * rad, la = lat * rad, la0 = this.lat0 * rad;
  const cosC = Math.sin(la0) * Math.sin(la) + Math.cos(la0) * Math.cos(la) * Math.cos(dl);
  return { x: this.CX + this.R * Math.cos(la) * Math.sin(dl),
           y: this.CY - this.R * (Math.cos(la0) * Math.sin(la) - Math.sin(la0) * Math.cos(la) * Math.cos(dl)),
           visivel: cosC > 0, cosC: cosC };
};
Globo.prototype.irPara = function (pais, agora) {
  agora = agora || performance.now();
  this.alvo = pais;
  this.viagem = { t0: agora, de: { lon: this.lon0, lat: this.lat0 }, para: { lon: pais.longitude, lat: Math.max(-55, Math.min(55, pais.latitude)) } };
  this.fase = "viajando";
  this.mostrarFicha(pais, false);
};
Globo.prototype.proximo = function (agora) {
  if (!this.roteiro.length) return;
  this.indice = (this.indice + 1) % this.roteiro.length;
  this.irPara(this.roteiro[this.indice], agora);
};
Globo.prototype.alternar = function () {
  this.girando = !this.girando;
  if (this.girando && this.fase === "parado") { this.fase = "girando"; this.proximaParada = performance.now() + TOUR_GIRO_MS; }
  if (!this.girando && this.fase === "girando") this.fase = "parado";
};
Globo.prototype.mostrarFicha = function (pais, chegou) {
  if (!this.ficha) return;
  this.ficha.innerHTML = "";
  this.ficha.className = "ficha-pais" + (chegou ? " chegou" : " a-caminho");
  const bandeira = (typeof Bandeiras !== "undefined" && pais.iso) ? Bandeiras.get(pais.iso, pais.pais) : null;
  this.ficha.appendChild(el("div", { class: "cabeca-pais" }, [
    bandeira ? el("span", { class: "bandeira" }, [bandeira]) : null,
    el("div", {}, [el("b", { text: pais.pais }), el("small", { text: chegou ? "chegamos" : "a caminho…" })]),
  ]));
  const n = el("div", { class: "n-pais" });
  this.ficha.appendChild(n);
  if (chegou) contar(n, pais.n); else n.textContent = "…";
  this.ficha.appendChild(el("div", { class: "sub", text: "artigo(s) com ao menos um autor de lá" }));
  if (pais.instituicoes && pais.instituicoes.length) {
    this.ficha.appendChild(el("div", { class: "linhas-chips" }, pais.instituicoes.map(function (i, k) {
      return el("span", { class: "chip solto", style: "--tom:" + NEON_SEQ[k % NEON_SEQ.length] + ";--i:" + k }, [Icons.get("instituicao", 13), document.createTextNode(" " + i)]); })));
  }
};
Globo.prototype.laco = function (t) {
  this.raf = requestAnimationFrame(this.laco.bind(this));
  if (document.hidden) { this.ultimo = t; return; }   /* girar um globo que ninguém vê gasta bateria para nada */
  const dt = Math.min(100, t - this.ultimo); this.ultimo = t;
  if (this.fase === "girando") {
    this.lon0 += 9 * dt / 1000;                       /* nove graus por segundo */
    if (this.lon0 > 180) this.lon0 -= 360;
    if (this.girando && t >= this.proximaParada && this.roteiro.length) this.proximo(t);
  } else if (this.fase === "viajando" && this.viagem) {
    const k = Math.min(1, (t - this.viagem.t0) / TOUR_VIAGEM_MS);
    const s = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
    let dLon = this.viagem.para.lon - this.viagem.de.lon;
    while (dLon > 180) dLon -= 360;
    while (dLon < -180) dLon += 360;
    this.lon0 = this.viagem.de.lon + dLon * s;
    this.lat0 = this.viagem.de.lat + (this.viagem.para.lat - this.viagem.de.lat) * s;
    if (k >= 1) {
      this.fase = "pousado"; this.pousadoAte = t + TOUR_POUSO_MS;
      this.efeitos.push({ lon: this.alvo.longitude, lat: this.alvo.latitude, t0: t });
      this.mostrarFicha(this.alvo, true);
    }
  } else if (this.fase === "pousado") {
    if (t >= this.pousadoAte) {
      if (this.girando) { this.fase = "girando"; this.proximaParada = t + TOUR_GIRO_MS; }
      else this.fase = "parado";
    }
  }
  this.desenhar(t);
};
Globo.prototype.desenhar = function (t) {
  const ctx = this.ctx, R = this.R, CX = this.CX, CY = this.CY, self = this;
  ctx.clearRect(0, 0, this.W, this.H);
  /* o brilho por trás do planeta */
  const halo = ctx.createRadialGradient(CX, CY, R * 0.9, CX, CY, R + 10);
  halo.addColorStop(0, "rgba(34,211,238,0)"); halo.addColorStop(1, "rgba(34,211,238,.35)");
  ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(CX, CY, R + 10, 0, Math.PI * 2); ctx.fill();
  /* o oceano */
  const oceano = ctx.createRadialGradient(CX - R * 0.35, CY - R * 0.35, R * 0.1, CX, CY, R);
  oceano.addColorStop(0, "rgba(59,130,246,.45)"); oceano.addColorStop(1, "rgba(7,13,31,.95)");
  ctx.fillStyle = oceano; ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI * 2); ctx.fill();
  /* a grade de meridianos e paralelos */
  ctx.strokeStyle = "rgba(255,255,255,.08)"; ctx.lineWidth = 1;
  for (let lon = -180; lon < 180; lon += 30) this.traco(function (i) { return [lon, -90 + i * 3]; }, 61);
  for (let lat = -60; lat <= 60; lat += 30) this.traco(function (i) { return [-180 + i * 3, lat]; }, 121);
  /* os países */
  const foco = this.alvo && (this.fase === "pousado" || this.fase === "viajando") ? this.alvo.pais : null;
  const pulso = 0.5 + 0.5 * Math.sin(t / 260);
  this.contorno.forEach(function (pais) {
    const n = self.valores[pais.nome] || self.valores[pais.en] || 0;
    const ehFoco = foco && (pais.nome === foco || pais.en === foco);
    const forca = n ? 0.25 + 0.6 * n / self.max : 0;
    (pais.d || []).forEach(function (anel) {
      let atual = [];
      const partes = [];
      anel.forEach(function (pt) {
        const p = self.projetar(pt[0], pt[1]);
        if (p.visivel) atual.push(p); else if (atual.length) { partes.push(atual); atual = []; }
      });
      if (atual.length) partes.push(atual);
      partes.forEach(function (parte) {
        if (parte.length < 2) return;
        ctx.beginPath();
        parte.forEach(function (p, i) { if (i) ctx.lineTo(p.x, p.y); else ctx.moveTo(p.x, p.y); });
        ctx.closePath();
        if (ehFoco) {
          ctx.fillStyle = "rgba(255,122,24," + (0.55 + 0.35 * pulso) + ")";
          ctx.shadowColor = "#FF7A18"; ctx.shadowBlur = 18 + 12 * pulso;
        } else if (n) {
          ctx.fillStyle = "rgba(34,211,238," + forca.toFixed(2) + ")";
          ctx.shadowColor = "#22D3EE"; ctx.shadowBlur = 6;
        } else {
          ctx.fillStyle = "rgba(255,255,255,.07)"; ctx.shadowBlur = 0;
        }
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.strokeStyle = ehFoco ? "#FFB27A" : (n ? "rgba(34,211,238,.7)" : "rgba(255,255,255,.16)");
        ctx.lineWidth = ehFoco ? 1.6 : 0.7;
        ctx.stroke();
      });
    });
  });
  /* o arco da sede até o país em foco */
  if (this.alvo && (this.fase === "viajando" || this.fase === "pousado")) {
    const k = this.fase === "pousado" ? 1 : Math.min(1, (t - this.viagem.t0) / TOUR_VIAGEM_MS);
    this.arco(this.sede, this.alvo, k, t);
  }
  /* os anéis de chegada */
  this.efeitos = this.efeitos.filter(function (e) { return t - e.t0 < 2400; });
  this.efeitos.forEach(function (e) {
    const p = self.projetar(e.lon, e.lat);
    if (!p.visivel) return;
    for (let i = 0; i < 3; i++) {
      const k = ((t - e.t0) / 800 - i * 0.33);
      if (k < 0 || k > 1) continue;
      ctx.beginPath(); ctx.arc(p.x, p.y, 6 + 44 * k, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,122,24," + (1 - k).toFixed(2) + ")"; ctx.lineWidth = 2.5 - 2 * k; ctx.stroke();
    }
  });
  /* as instituições e a sede */
  (this.dados.instituicoes || []).forEach(function (i) {
    const p = self.projetar(i.longitude, i.latitude);
    if (!p.visivel) return;
    ctx.beginPath(); ctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(250,204,21,.85)"; ctx.fill();
  });
  const s = this.projetar(this.sede.longitude, this.sede.latitude);
  if (s.visivel) {
    ctx.beginPath(); ctx.arc(s.x, s.y, 5 + 2 * pulso, 0, Math.PI * 2);
    ctx.fillStyle = "#FACC15"; ctx.shadowColor = "#FACC15"; ctx.shadowBlur = 14; ctx.fill(); ctx.shadowBlur = 0;
    ctx.fillStyle = "rgba(244,247,255,.9)"; ctx.font = "600 11px system-ui, sans-serif";
    ctx.fillText(this.sede.nome, s.x + 9, s.y + 4);
  }
  /* o alfinete e o nome do país em foco */
  if (foco) {
    const p = this.projetar(this.alvo.longitude, this.alvo.latitude);
    if (p.visivel) {
      ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, Math.PI * 2); ctx.fillStyle = "#FF7A18"; ctx.fill();
      ctx.beginPath(); ctx.arc(p.x, p.y, 11 + 3 * pulso, 0, Math.PI * 2); ctx.strokeStyle = "#FF7A18"; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.font = "800 15px system-ui, sans-serif";
      ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 6;
      ctx.fillText(this.alvo.pais + " · " + this.alvo.n, p.x + 16, p.y - 10);
      ctx.shadowBlur = 0;
    }
  }
  /* a borda do planeta por cima de tudo */
  ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(34,211,238,.55)"; ctx.lineWidth = 1.5; ctx.stroke();
};
Globo.prototype.traco = function (ponto, n) {
  const ctx = this.ctx;
  let desenhando = false;
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const pt = ponto(i);
    const p = this.projetar(pt[0], pt[1]);
    if (!p.visivel) { desenhando = false; continue; }
    if (desenhando) ctx.lineTo(p.x, p.y); else ctx.moveTo(p.x, p.y);
    desenhando = true;
  }
  ctx.stroke();
};
/* o arco do grande círculo, desenhado até a fração `k` da viagem, com um
   "pulso de luz" correndo por ele */
Globo.prototype.arco = function (de, para, k, t) {
  const ctx = this.ctx, rad = Math.PI / 180;
  const v = function (lon, lat) { return [Math.cos(lat * rad) * Math.cos(lon * rad), Math.cos(lat * rad) * Math.sin(lon * rad), Math.sin(lat * rad)]; };
  const a = v(de.longitude, de.latitude), b = v(para.longitude, para.latitude);
  const dot = Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]));
  const ang = Math.acos(dot);
  if (ang < 1e-4) return;
  const N = 72;
  const pontos = [];
  for (let i = 0; i <= N; i++) {
    const f = i / N;
    const s1 = Math.sin((1 - f) * ang) / Math.sin(ang), s2 = Math.sin(f * ang) / Math.sin(ang);
    const x = s1 * a[0] + s2 * b[0], y = s1 * a[1] + s2 * b[1], z = s1 * a[2] + s2 * b[2];
    const lat = Math.atan2(z, Math.sqrt(x * x + y * y)) / rad, lon = Math.atan2(y, x) / rad;
    const p = this.projetar(lon, lat);
    /* o arco sobe um pouco acima da superfície: é voo, não estrada */
    const lift = 1 + 0.12 * Math.sin(f * Math.PI);
    pontos.push({ x: this.CX + (p.x - this.CX) * lift, y: this.CY + (p.y - this.CY) * lift, visivel: p.visivel, f: f });
  }
  ctx.save();
  ctx.lineCap = "round";
  const ate = Math.floor(k * N);
  ctx.beginPath();
  let desenhando = false;
  for (let i = 0; i <= ate; i++) {
    const p = pontos[i];
    if (!p.visivel) { desenhando = false; continue; }
    if (desenhando) ctx.lineTo(p.x, p.y); else ctx.moveTo(p.x, p.y);
    desenhando = true;
  }
  ctx.strokeStyle = "rgba(255,122,24,.85)"; ctx.lineWidth = 2.2;
  ctx.shadowColor = "#FF7A18"; ctx.shadowBlur = 10; ctx.stroke();
  /* o pulso de luz que corre pelo arco */
  const pos = pontos[Math.min(ate, Math.floor(((t / 900) % 1) * ate))];
  if (pos && pos.visivel) {
    ctx.beginPath(); ctx.arc(pos.x, pos.y, 4, 0, Math.PI * 2); ctx.fillStyle = "#fff"; ctx.shadowBlur = 16; ctx.fill();
  }
  ctx.restore();
};

let contornoPedido = false;
function pedirContorno() {
  if (contornoPedido) return;
  contornoPedido = true;
  fetch("/api/geo/mundo.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (dados) { D.contorno = (dados || {}).paises || []; if (GLOBO) GLOBO.contorno = D.contorno; })
    .catch(function () { contornoPedido = false; });
}

function desenharMundo(palco) {
  const M = D.mundo;
  pedirContorno();
  palco.appendChild(cabeca("mapa", "Mapa-múndi ao vivo",
    M.paises.length + " país(es) assinam com o laboratório · " + M.artigos_com_pais + " artigo(s) com país · o globo pousa em cada um"));
  const grade = el("div", { class: "grade meio mundo" });
  const canvas = el("canvas", { class: "globo-vivo", "aria-label": "globo com os países que assinam com o laboratório", role: "img" });
  const ficha = el("div", { class: "ficha-pais vazia" }, [el("div", { class: "sub", text: M.paises.length ? "o globo vai pousar no primeiro país em instantes…" : "sem país com coordenada para pousar" })]);
  const controles = el("div", { class: "controles-analise" });
  const bGirar = el("button", { type: "button", text: SEM_MOVIMENTO ? "Girar" : "Pausar", onclick: function () {
    if (!GLOBO) return; GLOBO.alternar(); bGirar.textContent = GLOBO.girando ? "Pausar" : "Girar"; } });
  controles.appendChild(bGirar);
  controles.appendChild(el("button", { type: "button", class: "rodar", text: "Próximo país ▶", onclick: function () { if (GLOBO) GLOBO.proximo(); } }));
  grade.appendChild(glass([
    cabecalho("O globo", "gira a nove graus por segundo; a cada parada, o arco sai da sede e o país acende", controles),
    el("div", { class: "palco-globo" }, [canvas]),
  ], { i: 0, class: "cartao-globo" }));
  const lista = el("ul", { class: "paises" }, M.paises.slice().sort(function (a, b) { return b.n - a.n; }).map(function (p, i) {
    const bandeira = (typeof Bandeiras !== "undefined" && p.iso) ? Bandeiras.get(p.iso, p.pais) : null;
    return el("li", { style: "--i:" + i }, [el("button", { type: "button", onclick: function () { if (GLOBO) GLOBO.irPara(p); } }, [
      bandeira ? el("span", { class: "bandeira" }, [bandeira]) : null,
      el("span", { class: "nome", text: p.pais }),
      el("span", { class: "n", text: C.fmt(p.n) })])]);
  }));
  grade.appendChild(glass([
    cabecalho("Onde pousar", "clique num país para ir direto a ele"),
    ficha,
    M.paises.length ? lista : el("div", { class: "vazio", text: "nenhum país com coordenada ainda — cadastre a instituição de cada integrante" }),
    M.sem_coordenada.length ? el("div", { class: "rodape", text: "sem coordenada: " + M.sem_coordenada.join(", ") }) : null,
    M.instituicoes.length ? el("div", { class: "rodape", text: M.instituicoes.length + " instituição(ões) com coordenada aparecem como pontos amarelos" }) : null,
  ], { i: 1 }));
  palco.appendChild(grade);
  pararGlobo();
  GLOBO = new Globo(canvas, M, ficha);
}

/* ---------------------------------------------------------- busca */
/* Um campo, tudo o que o laboratório tem com aquele nome. Cada resultado
   traz o seu ícone temático e os links para onde ele vive; sem texto, a
   nuvem de temas mostra por onde começar. */
let buscaMarcada = null;
const GRUPOS_DA_BUSCA = [
  ["linhas", "Linhas de pesquisa", "linhas"], ["acervos", "Acervos", "livro"], ["temas", "Temas e segmentos", "achado"],
  ["artigos", "Artigos", "producao"], ["pessoas", "Pessoas", "pessoas"], ["projetos", "Projetos", "projeto"],
];

function linksTematicos(termo) {
  const q = encodeURIComponent(termo);
  return el("div", { class: "links-tema" }, [
    el("a", { href: "https://pubmed.ncbi.nlm.nih.gov/?term=" + q, target: "_blank", rel: "noopener", text: "PubMed" }),
    el("a", { href: "https://openalex.org/works?filter=default.search:" + q, target: "_blank", rel: "noopener", text: "OpenAlex" }),
    el("a", { href: "https://scholar.google.com/scholar?q=" + q, target: "_blank", rel: "noopener", text: "Scholar" }),
    el("a", { href: "/?q=" + q + "#explorar", text: "Painel" }),
    el("a", { href: "/panorama", text: "Panorama" }),
  ]);
}

function resultadoDaBusca(grupo, r, i) {
  const q = encodeURIComponent;
  let titulo, sub, texto, href, tom = NEON_SEQ[i % NEON_SEQ.length];
  switch (grupo) {
    case "artigos":
      titulo = r.titulo; texto = r.titulo;
      sub = [r.ano, r.situacao ? r.situacao.replace("_", " ") : null, r.revista, r.linha].filter(Boolean).join(" · ");
      href = "/?q=" + q(r.titulo) + "#" + (r.situacao === "publicado" ? "publicacoes" : (r.situacao === "em_producao" ? "producao" : "submetidos"));
      break;
    case "pessoas":
      titulo = r.nome; texto = r.papel || "pessoa"; sub = r.papel || ""; href = "/?integrante=" + r.id + "#equipe"; break;
    case "projetos":
      titulo = r.nome; texto = r.nome; sub = r.situacao || ""; href = "/#projetos"; break;
    case "linhas":
      titulo = r.nome; texto = r.nome; sub = r.n + " artigo(s)"; href = "/?linha=" + q(r.nome) + "#linhas"; break;
    case "acervos":
      titulo = r.titulo; texto = r.titulo; sub = r.n + " registro(s)" + (r.linha ? " · " + r.linha : ""); href = "#acervos"; break;
    case "temas":
      titulo = r.tema; texto = r.tema; sub = r.tipo === "segmento" ? "segmento de " + r.acervo_titulo : r.tipo + " · " + r.n + " artigo(s)";
      href = r.tipo === "segmento" ? "#acervos" : "/?q=" + q(r.tema) + "#explorar"; break;
    default: titulo = String(r); texto = titulo; sub = ""; href = "#";
  }
  const icone_ = grupo === "linhas" && r.icone && r.icone !== "linha" ? r.icone : undefined;
  const a = el("a", { class: "resultado", href: href, style: "--i:" + i + ";--tom:" + tom });
  if (grupo === "acervos" || (grupo === "temas" && r.tipo === "segmento")) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault(); ST.aba = "acervos"; location.hash = "acervos"; desenhar();
      const alvo = document.getElementById("acervo-" + (r.code || r.acervo));
      if (alvo) alvo.scrollIntoView({ behavior: SEM_MOVIMENTO ? "auto" : "smooth", block: "start" });
    });
  }
  a.appendChild(Icons.tema(texto, { icone: icone_, tam: 34, tom: tom }));
  a.appendChild(el("div", {}, [el("b", { text: titulo }), el("small", { text: sub })]));
  return a;
}

function desenharBusca(palco) {
  palco.appendChild(cabeca("explorar", "Buscador temático",
    "artigos, pessoas, projetos, linhas, acervos e temas — sem caixa e sem acento"));
  const campo = el("input", { type: "search", class: "campo-busca", value: ST.busca || "", autofocus: true,
    placeholder: "Digite um tema, um nome, uma revista…", "aria-label": "Buscar" });
  const resultados = el("div", { class: "resultados" });
  const cabecalhoBusca = glass([el("label", { class: "busca-grande" }, [icone("explorar"), campo])], { i: 0 });
  palco.appendChild(cabecalhoBusca);
  palco.appendChild(resultados);

  function nuvem() {
    resultados.innerHTML = "";
    const temas = [];
    (D.por_linha.items || []).forEach(function (l) { temas.push({ t: l.label, icone: l.icone !== "linha" ? l.icone : undefined }); });
    (D.acervos || []).forEach(function (a) {
      temas.push({ t: a.title });
      (a.segmentos || []).slice(0, 6).forEach(function (s) { temas.push({ t: s.segmento }); });
    });
    const vistos = {};
    const chips = el("div", { class: "nuvem" }, temas.filter(function (x) {
      if (!x.t || vistos[x.t]) return false; vistos[x.t] = true; return true; }).map(function (x, i) {
      return el("button", { type: "button", class: "tema", style: "--i:" + i + ";--tom:" + NEON_SEQ[i % NEON_SEQ.length],
        onclick: function () { campo.value = x.t; ST.busca = x.t; buscar(); } },
        [Icons.tema(x.t, { icone: x.icone, tam: 26 }), el("span", { text: x.t })]);
    }));
    resultados.appendChild(glass([cabecalho("Por onde começar", "linhas, acervos e segmentos do laboratório — clique num tema"), chips], { i: 1 }));
  }

  async function buscar() {
    const q = campo.value.trim();
    ST.busca = q;
    if (q.length < 2) { nuvem(); return; }
    let r;
    try { r = await api("/api/buscar?q=" + encodeURIComponent(q)); }
    catch (erro) { resultados.innerHTML = ""; resultados.appendChild(glass([el("div", { class: "vazio", text: erro.message })])); return; }
    if (campo.value.trim() !== q) return;    /* já digitou outra coisa */
    resultados.innerHTML = "";
    resultados.appendChild(glass([
      cabecalho(r.total ? r.total + " resultado(s) para “" + q + "”" : "Nada com “" + q + "” no laboratório",
        "e o mesmo termo nas bases, com um clique"),
      linksTematicos(q),
    ], { i: 0 }));
    let n = 1;
    GRUPOS_DA_BUSCA.forEach(function (g) {
      const itens = r[g[0]] || [];
      if (!itens.length) return;
      const lista = el("div", { class: "lista-resultados" }, itens.map(function (item, i) { return resultadoDaBusca(g[0], item, i); }));
      resultados.appendChild(glass([cabecalho(g[1], itens.length + " encontrado(s)", icone(g[2])), lista], { i: n++ }));
    });
  }
  campo.addEventListener("input", function () { clearTimeout(buscaMarcada); buscaMarcada = setTimeout(buscar, 260); });
  campo.addEventListener("keydown", function (ev) { if (ev.key === "Enter") { clearTimeout(buscaMarcada); buscar(); } });
  buscar();
}

/* ------------------------------------------------------------- comum */
function desenhar() {
  desenharLado();
  desenharTopo();
  const palco = document.getElementById("palco");
  palco.innerHTML = "";
  if (!D.pronto) { palco.appendChild(el("div", { class: "vazio", text: "carregando…" })); return; }
  if (ST.aba !== "mundo") pararGlobo();
  if (ST.aba !== "sinais") pararAnalise();
  if (ST.aba === "acervos") desenharAcervos(palco);
  else if (ST.aba === "temas") desenharTemas(palco);
  else if (ST.aba === "sinais") desenharSinais(palco);
  else if (ST.aba === "mundo") desenharMundo(palco);
  else if (ST.aba === "busca") desenharBusca(palco);
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
  const mais = EXPLICA[ST.aba] || [];
  /* o texto é interativo: cada clique em "Mais" (ou no próprio texto)
     revela uma explicação a mais, com a sua animação */
  const explicacoes = el("ul", { class: "explica" }, mais.slice(0, ST.explicadas).map(function (t, i) {
    return el("li", { style: "--i:" + i }, [icone("achado"), document.createTextNode(t)]);
  }));
  const botaoMais = mais.length ? el("button", { type: "button", class: "mais",
    text: ST.explicadas >= mais.length ? "Recolher" : "Mais ▸ " + (mais.length - ST.explicadas),
    onclick: function () { ST.explicadas = ST.explicadas >= mais.length ? 0 : ST.explicadas + 1; desenharApresentacao(); } }) : null;
  const bloco = el("div", { class: "texto" }, [
    el("b", {}, [el("span", { class: "n", text: String(indice + 1) }), document.createTextNode(texto[0]),
      el("small", { text: " · " + (indice + 1) + " de " + ABAS.length })]),
    el("p", { text: texto[1] }), explicacoes]);
  bloco.addEventListener("click", function (ev) {
    if (ev.target.closest("button")) return;
    ST.explicadas = ST.explicadas >= mais.length ? 0 : ST.explicadas + 1; desenharApresentacao();
  });
  caixa.appendChild(bloco);
  const pontos = el("span", { class: "pontos" }, ABAS.map(function (a, i) {
    return el("i", { class: i === indice ? "on" : "", title: a[1], onclick: function () { irPara(i); } }); }));
  caixa.appendChild(el("div", { class: "passos" }, [
    pontos,
    botaoMais,
    el("button", { type: "button", text: "◀ Anterior", onclick: function () { irPara(indice - 1); } }),
    el("button", { type: "button", class: "seguir", text: "Seguir ▶", onclick: function () { irPara(indice + 1); } }),
    el("button", { type: "button", class: ST.auto ? "on" : "", text: ST.auto ? "Auto: ligado" : "Auto (" + AUTO_SEGUNDOS + " s)",
      onclick: function () { ST.auto = !ST.auto; desenharApresentacao(); } }),
  ]));
  const barra = el("div", { class: "barra" }, [el("i")]);
  caixa.appendChild(barra);
  /* o ponteiro em cima da caixa segura o automático: quem está lendo não
     quer a tela trocar no meio da frase */
  caixa.onmouseenter = function () { ST.pausada = true; caixa.classList.add("pausada"); };
  caixa.onmouseleave = function () { ST.pausada = false; caixa.classList.remove("pausada"); };
  if (ST.auto) {
    let decorrido = 0, ultimo = performance.now();
    relogioAuto = setInterval(function () {
      const agora = performance.now();
      if (!ST.pausada) decorrido += agora - ultimo;
      ultimo = agora;
      const k = Math.min(1, decorrido / (AUTO_SEGUNDOS * 1000));
      barra.firstChild.style.width = (k * 100).toFixed(1) + "%";
      if (k >= 1) irPara(indice + 1);
    }, 200);
  }
}

function irPara(indice) {
  const n = ABAS.length;
  ST.aba = ABAS[((indice % n) + n) % n][0];
  ST.explicadas = 0;
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
  const aba = location.hash.replace("#", "").split("?")[0];
  if (ABAS.some(function (a) { return a[0] === aba; })) ST.aba = aba;
  const q = new URLSearchParams(location.search).get("q");
  if (q) { ST.busca = q; ST.aba = "busca"; }
  desenhar();
  carregar();
  ligarAoVivo();
})();
