/* ==========================================================================
   LAPE — mural
   A tela da sala. Roda sozinha, sem ninguém operando: cada slide fica alguns
   segundos, o seguinte entra, e o ciclo recomeça. O conteúdo é o mesmo do
   painel, recortado para o que interessa a quem passa — o que está
   acontecendo agora e o que vem a seguir.

   Três regras que valem para tudo aqui dentro:
   1. Nada rola. O que não cabe na tela vira "e mais N", nunca barra de rolagem.
   2. Nenhuma cor nova. Tom de urgência e cor de marca saem das mesmas rampas
      do tema — o efeito está no movimento e no relevo, não em matiz inventado.
   3. Quem redesenha é o servidor. O SSE avisa, o mural rebusca /api/metrics e
      redesenha só o slide corrente.
   ========================================================================== */
"use strict";

const C = Charts;
let D = JSON.parse(document.getElementById("payload").textContent);

const PARAMS = new URLSearchParams(location.search);
const SEGUNDOS = Math.max(5, Math.min(120, Number(PARAMS.get("t")) || 15));
const AREA = (PARAMS.get("area") || "").trim();   /* recorta o mural numa linha */
/* "Últimos cinco anos" é a janela que o laboratório usa para se olhar: o
   gráfico de publicações por ano e o recorte dos mais citados saem daqui,
   e mudam juntos. `?anos=` abre a janela sem mexer no código. */
const JANELA = Math.max(2, Math.min(20, Number(PARAMS.get("anos")) || 5));

const MESES_EXT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
  "agosto", "setembro", "outubro", "novembro", "dezembro"];
const DIAS_EXT = ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
  "sexta-feira", "sábado"];
const STATUS_ROTULO = {
  em_producao: "Em produção", submetido: "Submetido", em_revisao: "Em avaliação",
  aceito: "Aceito", publicado: "Publicado", rejeitado: "Rejeitado", arquivado: "Arquivado",
};
const TIPO_EVENTO = {
  reuniao: "Reunião", congresso: "Congresso", defesa: "Defesa", qualificacao: "Qualificação",
  coleta: "Coleta de dados", curso: "Curso", palestra: "Palestra", visita: "Visita",
  banca: "Banca", workshop: "Workshop", seminario: "Seminário",
  extensao: "Extensão", visita_tecnica: "Visita técnica", defesa_tese: "Defesa de tese",
};

/* Como cada trabalho de formação se chama. Sem este mapa, o relatório de um
   bolsista de IC era anunciado na parede como "Tese" — e quem passa acredita. */
const TIPO_TRABALHO = {
  tese: "Tese", dissertacao: "Dissertação", tcc: "Trabalho de conclusão",
  relatorio: "Relatório de IC", projeto: "Projeto de pesquisa",
};

const ICONE_EVENTO = {
  reuniao: "reuniao", congresso: "anuncio", seminario: "apresentacao",
  coleta: "experimento", curso: "livro", palestra: "anuncio", workshop: "livro",
  defesa: "tese", defesa_tese: "tese", qualificacao: "tese", banca: "tese",
  extensao: "pessoas", visita_tecnica: "instituicao", visita: "instituicao",
};

/* ------------------------------------------------------------------ datas */
/* Monta a data em horário local a partir das partes. `new Date("2026-03-04")`
   seria lido como UTC e, a oeste de Greenwich, cairia no dia anterior. */
function comoData(iso) {
  if (!iso) return null;
  const texto = String(iso);
  const p = texto.slice(0, 10).split("-");
  if (p.length !== 3) return null;
  const h = texto.length > 10 ? texto.slice(11, 16).split(":") : ["0", "0"];
  const d = new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]),
    Number(h[0]) || 0, Number(h[1]) || 0);
  return isNaN(d.getTime()) ? null : d;
}
function meiaNoite(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
function diasAte(iso) {
  const d = comoData(iso);
  if (!d) return null;
  return Math.round((meiaNoite(d) - meiaNoite(new Date())) / 86400000);
}
function dia(iso) { const d = comoData(iso); return d ? String(d.getDate()) : "—"; }
function mesCurto(iso) {
  const d = comoData(iso);
  return d ? MESES_EXT[d.getMonth()].slice(0, 3) : "";
}
function porExtenso(dias) {
  if (dias === null) return "sem data";
  if (dias === 0) return "hoje";
  if (dias === 1) return "amanhã";
  if (dias === -1) return "ontem";
  if (dias < 0) return "há " + Math.abs(dias) + " dias";
  if (dias < 45) return "em " + dias + " dias";
  const meses = Math.round(dias / 30.44);
  return "em " + meses + (meses === 1 ? " mês" : " meses");
}
/* `porExtenso` conta para a frente: "em 3 dias". Data de início e data de
   submissão contam para trás, e "há 780 dias" não é um número que alguém leia
   de pé, a três metros. Aqui a escala muda com a distância: dias, meses, anos. */
function haQuanto(dias) {
  if (dias === null) return "sem data";
  const d = Math.abs(dias);
  if (d === 0) return "hoje";
  if (d === 1) return "ontem";
  if (d < 45) return "há " + d + " dias";
  const meses = Math.round(d / 30.44);
  if (meses < 18) return "há " + meses + (meses === 1 ? " mês" : " meses");
  const anos = Math.floor(meses / 12);
  const resto = meses % 12;
  return "há " + anos + (anos === 1 ? " ano" : " anos")
    + (resto ? " e " + resto + (resto === 1 ? " mês" : " meses") : "");
}
/* Com o ano por extenso: na parede, "12 mar" de 2023 é lido como este ano. */
function dataCurta(iso) {
  const d = comoData(iso);
  if (!d) return "sem data";
  return d.getDate() + " " + MESES_EXT[d.getMonth()].slice(0, 3) + " " + d.getFullYear();
}

/* O tom acompanha a urgência, e só ela. Vermelho é prazo vencido — nunca
   decoração — para que a cor continue significando alguma coisa na tela. */
function tomDoPrazo(dias) {
  if (dias === null) return "azul";
  if (dias < 0) return "critico";
  if (dias <= 7) return "alerta";
  if (dias <= 30) return "ambar";
  return "azul";
}

/* ------------------------------------------------------------------ apoio */
function el(tag, attrs, kids) { return C.el(tag, attrs, kids); }
function fmt(v) { return C.fmt(v); }
function citacoes(a) {
  return Math.max(a.openalex_citations || 0, a.scopus_citations || 0, a.wos_citations || 0);
}
/* A Web of Science é uma base entre três, e a única que o laboratório
   informa à mão. Onde a tela promete "citações na WoS" é este número que
   entra — nunca o da melhor fonte, que costuma ser maior e diria outra coisa. */
function citacoesWos(a) { return a.wos_citations || 0; }
function cortar(texto, n) {
  const t = String(texto || "");
  return t.length > n ? t.slice(0, n - 1) + "…" : t;
}
function contar(lista, chave) {
  const mapa = new Map();
  lista.forEach(function (item) {
    const k = typeof chave === "function" ? chave(item) : item[chave];
    if (k === null || k === undefined || k === "") return;
    mapa.set(k, (mapa.get(k) || 0) + 1);
  });
  return Array.from(mapa, function (par) { return { label: String(par[0]), value: par[1] }; })
    .sort(function (a, b) { return b.value - a.value; });
}

/* Recorte por área: quando o mural é aberto com ?area=, tudo o que se conta
   passa por aqui, e o selo no topo diz em voz alta qual é o recorte. */
function artigos() {
  const todos = D.articles || [];
  return AREA ? todos.filter(function (a) { return a.research_line === AREA; }) : todos;
}
function pessoas() {
  const todos = D.researchers || [];
  return AREA ? todos.filter(function (p) { return p.research_line === AREA; }) : todos;
}
function projetos() {
  const todos = (D.projects && D.projects.items) || [];
  return AREA ? todos.filter(function (p) { return p.research_line === AREA; }) : todos;
}
function eventos() {
  const todos = (D.agenda && D.agenda.events) || [];
  return AREA ? todos.filter(function (e) { return e.research_line === AREA; }) : todos;
}

function tile(spec) {
  const casa = el("div", { class: "tile" });
  casa.style.setProperty("--tom", "var(--series-" + (spec.serie || 1) + ")");
  if (spec.tom) casa.style.setProperty("--tom", "var(--" + spec.tom + ")");
  const topo = el("div", { class: "topo" }, [
    Icons.badge(spec.icone, spec.pastilha, null),
    el("span", { class: "nome", text: spec.nome }),
  ]);
  const numero = el("div", { class: "n", text: "0" });
  numero.dataset.alvo = String(spec.valor === null || spec.valor === undefined ? 0 : spec.valor);
  if (spec.sufixo) numero.dataset.sufixo = spec.sufixo;
  casa.appendChild(topo);
  casa.appendChild(numero);
  if (spec.pe) casa.appendChild(el("div", { class: "pe", html: spec.pe }));
  return casa;
}
function quadro(titulo, icone, corpo, nota) {
  return el("div", { class: "quadro" }, [
    el("h2", {}, [Icons.badge(icone, null, null), el("span", { text: titulo }),
      nota ? el("small", { text: nota }) : null]),
    el("div", { class: "corpo" }, corpo),
  ]);
}
function vazio(texto) { return el("p", { class: "vazio", text: texto }); }
function escalonar(node) {
  node.classList.add("escalona");
  Array.prototype.forEach.call(node.children, function (filho, i) {
    filho.style.setProperty("--i", String(i));
  });
  return node;
}

/* ==========================================================================
   Prazos — a lista que dá nome ao mural
   Vêm de quatro lugares e são medidos pela mesma régua: data de defesa,
   fim de projeto, fim de bolsa e manuscrito parado em avaliação. Um artigo
   há muito tempo com o periódico é um prazo real, ainda que ninguém o tenha
   escrito numa agenda.
   ========================================================================== */
const ESPERA_LONGA = 120;   /* dias com o periódico antes de virar pendência */

function prazos() {
  const itens = [];
  pessoas().forEach(function (p) {
    if (p.thesis_due_on && (p.thesis_status || "") !== "concluida") {
      itens.push({
        titulo: (TIPO_TRABALHO[p.thesis_kind] || "Trabalho de conclusão") + " — " + p.full_name,
        detalhe: p.thesis_title || "Título em definição",
        data: p.thesis_due_on, dias: diasAte(p.thesis_due_on), icone: "tese",
      });
    }
    if (p.scholarship_until) {
      const d = diasAte(p.scholarship_until);
      if (d !== null && d <= 180) {
        itens.push({
          titulo: "Fim de bolsa — " + p.full_name,
          detalhe: p.scholarship || "Bolsa",
          data: p.scholarship_until, dias: d, icone: "bolsa",
        });
      }
    }
  });
  projetos().forEach(function (p) {
    if (p.status !== "em_andamento" || !p.ended_on) return;
    itens.push({
      titulo: "Encerramento — " + p.name,
      detalhe: [p.funder, p.coordinator].filter(Boolean).join(" · ") || "Projeto",
      data: p.ended_on, dias: diasAte(p.ended_on), icone: "projeto",
    });
  });
  eventos().forEach(function (e) {
    const d = diasAte(e.start_at);
    if (d === null || d < 0 || d > 60) return;
    if (["defesa", "qualificacao", "banca"].indexOf(e.kind) < 0) return;
    itens.push({
      titulo: (TIPO_EVENTO[e.kind] || e.kind) + " — " + e.title,
      detalhe: e.location_name || e.city || "Local a confirmar",
      data: e.start_at, dias: d, icone: "apresentacao",
    });
  });
  /* D.submitted, e não D.articles: só ele traz `last_submitted_on`, a data da
     tentativa em curso. Pela primeira submissão, um artigo reenviado três
     vezes apareceria esperando desde a tentativa que já foi recusada. */
  (D.submitted || []).forEach(function (a) {
    if (AREA && a.research_line !== AREA) return;
    const enviado = a.last_submitted_on || a.first_submission_on;
    const d = diasAte(enviado);
    if (d === null || -d < ESPERA_LONGA) return;
    itens.push({
      titulo: "Sem resposta há " + Math.abs(d) + " dias — " + cortar(a.title, 64),
      detalhe: (a.current_journal || a.journal || "Periódico não informado"),
      data: enviado, dias: null, espera: Math.abs(d), icone: "relogio",
    });
  });

  /* vencido primeiro, depois o mais próximo; a espera longa entra no fim,
     ordenada pela espera, porque não tem data marcada para cobrar */
  const comData = itens.filter(function (x) { return x.dias !== null; })
    .sort(function (a, b) { return a.dias - b.dias; });
  const semData = itens.filter(function (x) { return x.dias === null; })
    .sort(function (a, b) { return b.espera - a.espera; });
  return comData.concat(semData);
}

function linhaDePauta(item) {
  const tom = item.dias === null ? "alerta" : tomDoPrazo(item.dias);
  const li = el("li", {}, [
    el("div", { class: "quando" }, [
      el("b", { text: dia(item.data) }), el("small", { text: mesCurto(item.data) }),
    ]),
    Icons.badge(item.icone, tom, null),
    el("div", { class: "oque" }, [
      el("b", { text: item.titulo }), el("small", { text: item.detalhe }),
    ]),
    el("span", {
      class: "contagem",
      text: item.dias === null ? Math.abs(item.espera) + " dias de espera" : porExtenso(item.dias),
    }),
  ]);
  li.style.setProperty("--tom", "var(--" + tomToken(tom) + ")");
  return li;
}
/* nome do tom -> token do tema (a pastilha faz o mesmo, por CSS) */
function tomToken(tom) {
  const mapa = {
    azul: "series-1", laranja: "series-2", verde: "series-3", ambar: "series-4",
    magenta: "series-5", violeta: "series-7", acento: "accent-strong",
    bom: "good", alerta: "warning", grave: "serious", critico: "critical",
  };
  return mapa[tom] || "accent-strong";
}

/* ==========================================================================
   Slides
   ========================================================================== */
function slideAgora() {
  const o = D.overview || {};
  const arts = artigos();
  const recorte = AREA ? {
    n_published: arts.filter(function (a) { return a.status === "publicado"; }).length,
    n_in_progress: arts.filter(function (a) { return a.status === "em_producao"; }).length,
    n_submitted: arts.filter(function (a) {
      return a.status === "submetido" || a.status === "em_revisao"; }).length,
    n_accepted: arts.filter(function (a) { return a.status === "aceito"; }).length,
  } : o;
  const cit = arts.reduce(function (soma, a) { return soma + citacoes(a); }, 0);
  const ano = new Date().getFullYear();
  const noAno = arts.filter(function (a) { return Number(a.year_published) === ano; }).length;

  const kpis = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Publicados", valor: recorte.n_published, icone: "producao", serie: 1,
      pe: "<b>" + fmt(noAno) + "</b> em " + ano }),
    tile({ nome: "Em produção", valor: recorte.n_in_progress, icone: "experimento", serie: 3,
      pastilha: "verde", pe: "manuscritos em escrita" }),
    tile({ nome: "Em avaliação", valor: recorte.n_submitted, icone: "submissao", serie: 4,
      pastilha: "ambar", pe: "com o periódico agora" }),
    tile({ nome: "Aceitos", valor: recorte.n_accepted, icone: "aceite", serie: 6,
      pastilha: "bom", pe: "aguardando publicação" }),
    tile({ nome: "Citações", valor: cit, icone: "citacao", serie: 7, pastilha: "violeta",
      pe: "melhor fonte por artigo" }),
    tile({ nome: "Pesquisadores", valor: pessoas().filter(function (p) {
      return !p.is_external; }).length, icone: "pessoas", serie: 5, pastilha: "magenta",
      pe: "<b>" + fmt(projetos().filter(function (p) {
        return p.status === "em_andamento"; }).length) + "</b> projetos em andamento" }),
  ]);

  /* full_series é a série inteira, ano a ano; `series` traz só a janela
     configurada. Aqui vale a série longa, cortada na janela do mural. */
  const anos = (D.publications && (D.publications.full_series || D.publications.series)) || [];
  const recentes = anos.slice(-JANELA);
  const grafico = recentes.length
    ? C.area({
      labels: recentes.map(function (r) { return String(r.year); }),
      series: [{ label: "Publicações", values: recentes.map(function (r) { return r.n_articles; }) }],
      height: 460, caption: "publicações por ano",
    })
    : vazio("Sem histórico de publicação ainda.");

  const situacao = contar(arts, function (a) { return STATUS_ROTULO[a.status] || a.status; });
  const rosca = situacao.length
    ? C.donut({ items: situacao, unit: "artigos", caption: "situação" })
    : vazio("Sem artigos cadastrados.");

  return escalonar(el("div", { class: "slide" }, [
    kpis,
    el("div", { class: "painel-duplo" }, [
      quadro("Publicações por ano", "subida", grafico,
        recentes.length ? recentes[0].year + "–" + recentes[recentes.length - 1].year : ""),
      quadro("Situação da produção", "processo", rosca, fmt(arts.length) + " artigos"),
    ]),
  ]));
}

function slidePrazos() {
  const lista = prazos();
  const vencidos = lista.filter(function (x) { return x.dias !== null && x.dias < 0; }).length;
  const proximos = lista.filter(function (x) {
    return x.dias !== null && x.dias >= 0 && x.dias <= 30; }).length;
  const primeiro = lista.find(function (x) { return x.dias !== null && x.dias >= 0; });

  const kpis = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Vencidos", valor: vencidos, icone: "aviso", tom: "critical",
      pastilha: "critico", pe: "prazos já passados" }),
    tile({ nome: "Nos próximos 30 dias", valor: proximos, icone: "prazo", tom: "warning",
      pastilha: "alerta", pe: "exigem decisão agora" }),
    tile({ nome: "Total acompanhado", valor: lista.length, icone: "alvo", serie: 1,
      pe: primeiro ? "próximo: <b>" + cortar(primeiro.titulo, 42) + "</b>" : "nada em aberto" }),
  ]);

  const pauta = lista.length
    ? el("ul", { class: "pauta" }, lista.slice(0, 6).map(linhaDePauta))
    : vazio("Nenhum prazo em aberto. Defesas, fins de bolsa e encerramentos de projeto aparecem aqui.");
  const sobra = Math.max(0, lista.length - 6);

  return escalonar(el("div", { class: "slide" }, [
    kpis,
    quadro("Por ordem de urgência", "prazo", pauta,
      sobra ? "e mais " + sobra + " adiante" : ""),
  ]));
}

function slideAgenda() {
  const agora = new Date();
  const proximos = eventos().filter(function (e) {
    const d = comoData(e.start_at);
    return d && d >= meiaNoite(agora);
  }).sort(function (a, b) { return String(a.start_at).localeCompare(String(b.start_at)); });

  const pauta = proximos.length
    ? el("ul", { class: "pauta" }, proximos.slice(0, 6).map(function (e) {
      return linhaDePauta({
        titulo: e.title,
        detalhe: [TIPO_EVENTO[e.kind] || e.kind, e.location_name || e.city,
          e.research_line].filter(Boolean).join(" · "),
        data: e.start_at, dias: diasAte(e.start_at),
        icone: ICONE_EVENTO[e.kind] || "calendario",
      });
    }))
    : vazio("Nenhum compromisso marcado daqui para a frente.");

  /* doze meses à frente, para a tela mostrar o desenho do semestre */
  const rotulos = [], valores = [];
  for (let i = 0; i < 12; i += 1) {
    const m = new Date(agora.getFullYear(), agora.getMonth() + i, 1);
    const chave = m.getFullYear() + "-" + String(m.getMonth() + 1).padStart(2, "0");
    rotulos.push(MESES_EXT[m.getMonth()].slice(0, 3) + (m.getMonth() === 0 ? "/" + String(m.getFullYear()).slice(2) : ""));
    valores.push(proximos.filter(function (e) {
      return String(e.start_at).slice(0, 7) === chave; }).length);
  }
  const colunas = C.columns({
    labels: rotulos, series: [{ label: "Compromissos", values: valores }],
    height: 430, caption: "compromissos por mês",
  });

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "painel-duplo" }, [
      quadro("Próximos compromissos", "calendario", pauta,
        proximos.length > 6 ? "e mais " + (proximos.length - 6) : ""),
      quadro("Os próximos doze meses", "tempo", colunas),
    ]),
  ]));
}

function slideAreas() {
  /* Com ?area=, comparar linhas de pesquisa deixaria uma barra sozinha na
     tela. Aí o corte que interessa é o de dentro da área: por tipo de estudo. */
  if (AREA) return slideDentroDaArea();
  const linhas = D.research_lines || [];
  const arts = artigos();
  const porLinha = linhas.map(function (l) {
    const meus = arts.filter(function (a) { return a.research_line === l.name; });
    return {
      nome: l.name,
      publicados: meus.filter(function (a) { return a.status === "publicado"; }).length,
      avaliacao: meus.filter(function (a) {
        return a.status === "submetido" || a.status === "em_revisao"; }).length,
      producao: meus.filter(function (a) { return a.status === "em_producao"; }).length,
      citacoes: meus.reduce(function (s, a) { return s + citacoes(a); }, 0),
      pessoas: l.n_members || 0,
      total: meus.length,
    };
  }).sort(function (a, b) { return b.total - a.total; }).slice(0, 8);

  const empilhado = porLinha.length ? C.columns({
    labels: porLinha.map(function (x) { return cortar(x.nome, 22); }),
    series: [
      { label: "Publicados", values: porLinha.map(function (x) { return x.publicados; }) },
      { label: "Em avaliação", values: porLinha.map(function (x) { return x.avaliacao; }) },
      { label: "Em produção", values: porLinha.map(function (x) { return x.producao; }) },
    ],
    mode: "empilhado", height: 520, caption: "produção por linha de pesquisa",
  }) : vazio("Nenhuma linha de pesquisa cadastrada.");

  const teto = Math.max.apply(null, porLinha.map(function (x) { return x.citacoes; }).concat([1]));
  const tabela = el("table", { class: "placar" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "Linha de pesquisa" }), el("th", { text: "Citações" }),
      el("th", { class: "num", text: "Artigos" }), el("th", { class: "num", text: "Pessoas" }),
    ])),
    el("tbody", {}, porLinha.map(function (x, i) {
      const barra = el("i");
      barra.style.setProperty("--pct", (100 * x.citacoes / teto).toFixed(1) + "%");
      const trilho = el("div", { class: "trilho" }, barra);
      trilho.style.setProperty("--tom", "var(--series-" + ((i % 8) + 1) + ")");
      return el("tr", {}, [
        el("td", {}, el("div", { class: "quem" }, [
          Icons.badge("linhas", null, 22), el("span", { text: x.nome })])),
        el("td", {}, el("div", { class: "quem" }, [
          trilho, el("span", { text: fmt(x.citacoes) })])),
        el("td", { class: "num", text: fmt(x.total) }),
        el("td", { class: "num", text: fmt(x.pessoas) }),
      ]);
    })),
  ]);

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "painel-duplo igual" }, [
      quadro("Publicados, em avaliação e em produção", "barras", empilhado,
        fmt(arts.length) + " artigos"),
      quadro("Alcance de cada área", "citacao", tabela, "citações, artigos e equipe"),
    ]),
  ]));
}

/* Segmentação dentro de uma área: mesmos números, outra dimensão. */
function slideDentroDaArea() {
  const arts = artigos();
  const porTipo = contar(arts, function (a) { return a.study_type || "Não informado"; });
  const porPeriodico = contar(arts.filter(function (a) { return a.status === "publicado"; }),
    "journal").slice(0, 8);

  const colunas = porTipo.length ? C.columns({
    labels: porTipo.slice(0, 8).map(function (x) { return cortar(x.label, 22); }),
    series: [{ label: "Artigos", values: porTipo.slice(0, 8).map(function (x) { return x.value; }) }],
    height: 520, caption: "artigos por tipo de estudo",
  }) : vazio("Sem artigos nesta área.");

  const barras = porPeriodico.length ? C.bars({
    items: porPeriodico.map(function (x) { return { label: x.label, value: x.value }; }),
    unit: "publicações", mono: true, labelWidth: 240, rowH: 62, caption: "por periódico",
  }) : vazio("Nenhuma publicação nesta área ainda.");

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "painel-duplo igual" }, [
      quadro("Por tipo de estudo", "barras", colunas, fmt(arts.length) + " artigos"),
      quadro("Onde esta área publica", "livro", barras),
    ]),
  ]));
}

function slideAndamento() {
  const emCurso = projetos().filter(function (p) { return p.status === "em_andamento"; });
  const hoje = new Date();
  const cartoes = emCurso.map(function (p) {
    const ini = comoData(p.started_on), fim = comoData(p.ended_on);
    let pct = null;
    if (ini && fim && fim > ini) {
      pct = Math.max(0, Math.min(100, 100 * (hoje - ini) / (fim - ini)));
    }
    return { p: p, pct: pct, dias: diasAte(p.ended_on) };
  }).sort(function (a, b) {
    if (a.dias === null) return 1;
    if (b.dias === null) return -1;
    return a.dias - b.dias;
  });

  const tabela = cartoes.length ? el("table", { class: "placar" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "Projeto" }), el("th", { text: "Andamento" }),
      el("th", { class: "num", text: "Equipe" }), el("th", { class: "num", text: "Prazo" }),
    ])),
    el("tbody", {}, cartoes.slice(0, 7).map(function (x) {
      const tom = tomDoPrazo(x.dias);
      const barra = el("i");
      barra.style.setProperty("--pct", (x.pct === null ? 0 : x.pct).toFixed(1) + "%");
      const trilho = el("div", { class: "trilho" }, barra);
      trilho.style.setProperty("--tom", "var(--" + tomToken(tom) + ")");
      /* projeto sem data de término não ganha barra: uma barra vazia seria
         lida como "parado", e o que há é ausência de prazo, não de trabalho */
      const andamento = x.pct === null
        ? el("span", { text: x.p.started_on ? "desde " + mesCurto(x.p.started_on) + "/"
            + String(x.p.started_on).slice(0, 4) : "sem datas" })
        : el("div", { class: "quem" }, [trilho, el("span", { text: Math.round(x.pct) + "%" })]);
      return el("tr", {}, [
        el("td", {}, el("div", { class: "quem" }, [
          Icons.badge("projeto", tom, 22), el("span", { text: x.p.name })])),
        el("td", {}, andamento),
        el("td", { class: "num", text: fmt(x.p.n_members || 0) }),
        el("td", { class: "num", text: x.dias === null ? "—" : porExtenso(x.dias) }),
      ]);
    })),
  ]) : vazio("Nenhum projeto em andamento cadastrado.");

  const arts = artigos();
  const etapas = [
    { label: "Em produção", value: arts.filter(function (a) { return a.status === "em_producao"; }).length },
    { label: "Em avaliação", value: arts.filter(function (a) {
      return a.status === "submetido" || a.status === "em_revisao"; }).length },
    { label: "Aceito", value: arts.filter(function (a) { return a.status === "aceito"; }).length },
    { label: "Publicado", value: arts.filter(function (a) { return a.status === "publicado"; }).length },
  ];
  /* Barras, e não funil: os quatro números são um retrato de agora, não um
     fluxo. "52% da etapa anterior" compararia coisas que não se sucedem —
     um artigo publicado em 2019 não saiu dos 41 que estão em escrita hoje. */
  const retrato = etapas.some(function (e) { return e.value; })
    ? C.bars({
      items: etapas.map(function (e, i) { return { label: e.label, value: e.value,
        color: C.ord(i) }; }),
      unit: "artigos", labelWidth: 190, rowH: 96, caption: "situação dos manuscritos",
    })
    : vazio("Sem manuscritos em andamento.");

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "painel-duplo igual" }, [
      quadro("Projetos em andamento", "projeto", tabela,
        cartoes.length > 7 ? "e mais " + (cartoes.length - 7) : fmt(cartoes.length) + " ativos"),
      quadro("Do rascunho ao prelo", "processo", retrato),
    ]),
  ]));
}

/* ==========================================================================
   Na bancada — o que está sendo escrito e o que está com o periódico
   Duas listas de nome e data. É o quadro que a sala olha para saber de quem
   é a vez: um manuscrito começado há dois anos e um enviado há cinco meses
   são conversas diferentes, e a data é o que separa uma da outra.
   ========================================================================== */
function linhaDeArtigo(item) {
  const li = el("li", {}, [
    el("div", { class: "quando" }, [
      el("b", { text: dia(item.data) }), el("small", { text: mesCurto(item.data) }),
    ]),
    Icons.badge(item.icone, item.tom, null),
    el("div", { class: "oque" }, [
      el("b", { text: item.titulo }), el("small", { text: item.detalhe }),
    ]),
    el("span", { class: "contagem", text: item.contagem || haQuanto(item.dias) }),
  ]);
  li.style.setProperty("--tom", "var(--" + tomToken(item.tom) + ")");
  return li;
}

/* Sem data no fim da fila, e não no começo: a lista é cronológica, e um
   artigo sem data de início não é o mais antigo — é o que ninguém datou.
   Ordenar em texto ISO ordena em tempo, e sem depender de fuso. */
function emOrdemDeData(lista, campo) {
  return lista.slice().sort(function (a, b) {
    const x = a[campo], y = b[campo];
    if (!x && !y) return String(a.title || "").localeCompare(String(b.title || ""), "pt-BR");
    if (!x) return 1;
    if (!y) return -1;
    return String(x).localeCompare(String(y));
  });
}

function slideBancada() {
  const arts = artigos();
  const producao = emOrdemDeData(arts.filter(function (a) {
    return a.status === "em_producao"; }), "started_on");
  const submetidos = emOrdemDeData(arts.filter(function (a) {
    return a.status === "submetido" || a.status === "em_revisao"; }), "first_submission_on");

  const listaProducao = producao.length
    ? el("ul", { class: "pauta" }, producao.slice(0, 6).map(function (a) {
      return linhaDeArtigo({
        titulo: a.title, data: a.started_on, dias: diasAte(a.started_on),
        detalhe: (a.started_on ? "início em " + dataCurta(a.started_on)
          : "sem data de início registrada")
          + (a.lead_name ? " · " + a.lead_name : ""),
        icone: "experimento", tom: "verde",
      });
    }))
    : vazio("Nenhum manuscrito em escrita no momento.");

  const listaSubmetidos = submetidos.length
    ? el("ul", { class: "pauta" }, submetidos.slice(0, 6).map(function (a) {
      const espera = diasAte(a.first_submission_on);
      /* âmbar é a cor de "em avaliação" no mural inteiro. Passada a espera
         longa, o tom sobe — e sobe acompanhado das palavras "sem resposta":
         no escuro, âmbar e alerta são quase a mesma cor, e uma distinção que
         ninguém enxerga a três metros não é distinção, é ruído. */
      const demorado = espera !== null && Math.abs(espera) > ESPERA_LONGA;
      return linhaDeArtigo({
        titulo: a.title, data: a.first_submission_on, dias: espera,
        detalhe: (a.first_submission_on
          ? "submetido em " + dataCurta(a.first_submission_on)
          : "sem data de submissão registrada")
          + (a.journal ? " · " + a.journal : ""),
        /* as palavras vão na pastilha, e não no fim da linha de detalhe:
           lá o nome do periódico corta primeiro, e o que sumiria com as
           reticências é justamente o que a cor está tentando dizer */
        contagem: demorado ? haQuanto(espera) + " sem resposta" : null,
        icone: "submissao", tom: demorado ? "grave" : "ambar",
      });
    }))
    : vazio("Nenhum manuscrito com o periódico agora.");

  const sobraP = Math.max(0, producao.length - 6);
  const sobraS = Math.max(0, submetidos.length - 6);

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "painel-duplo igual" }, [
      quadro("Artigos em produção", "experimento", listaProducao,
        sobraP ? fmt(producao.length) + " ao todo · e mais " + sobraP
          : fmt(producao.length) + " em escrita"),
      quadro("Artigos submetidos", "submissao", listaSubmetidos,
        sobraS ? fmt(submetidos.length) + " ao todo · e mais " + sobraS
          : fmt(submetidos.length) + " com o periódico"),
    ]),
  ]));
}

/* ==========================================================================
   Os mais citados — na Web of Science
   Duas leituras do mesmo acervo: a obra que pesa desde sempre e a que está
   pesando agora. Sem a segunda, um artigo de 2009 esconderia para sempre o
   que o laboratório publicou depois.
   ========================================================================== */
function placarDeCitacoes(lista) {
  return el("table", { class: "placar citado" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "Artigo" }), el("th", { class: "num", text: "Ano" }),
      el("th", { class: "num", text: "Citações WoS" }),
    ])),
    el("tbody", {}, lista.map(function (a, i) {
      return el("tr", {}, [
        el("td", {}, el("div", { class: "quem" }, [
          el("span", { class: "posto", text: String(i + 1) }),
          el("span", { title: a.title, text: a.title }),
        ])),
        el("td", { class: "num", text: a.year_published ? String(a.year_published) : "—" }),
        el("td", { class: "num forte", text: fmt(citacoesWos(a)) }),
      ]);
    })),
  ]);
}

/* Do mais citado ao menos citado, e só quem tem citação: um artigo com zero
   não está no fim do pódio, está fora dele. `desdeOAno` recorta a janela —
   e recorta pelo ano de publicação, que é o que o rótulo da tela promete. */
function maisCitados(arts, desdeOAno) {
  return arts.filter(function (a) {
    if (citacoesWos(a) <= 0) return false;
    if (!desdeOAno) return true;
    return Number(a.year_published) >= desdeOAno;
  }).sort(function (a, b) { return citacoesWos(b) - citacoesWos(a); });
}

function slideCitados() {
  const arts = artigos();
  const comWos = maisCitados(arts);
  const corte = new Date().getFullYear() - (JANELA - 1);
  const recentes = maisCitados(arts, corte);

  const totalWos = arts.reduce(function (s, a) { return s + citacoesWos(a); }, 0);
  const totalMelhor = arts.reduce(function (s, a) { return s + citacoes(a); }, 0);

  /* O caso do acervo sem WoS preenchida não é "zero citações": é um campo em
     branco. Dizer "0" na parede seria mentir sobre o laboratório, então a tela
     conta o que há nas outras bases e diz de onde viria o número que falta. */
  const semWos = !comWos.length;
  const recado = semWos
    ? vazio(totalMelhor
      ? "Nenhum artigo com citações da Web of Science registradas. Nas outras bases "
        + "o acervo soma " + fmt(totalMelhor) + " citações; o número da WoS entra "
        + "pela planilha, na coluna citacoes_wos."
      : "Ainda sem citações registradas em nenhuma base.")
    : null;

  const kpis = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Citações na WoS", valor: totalWos, icone: "citacao", serie: 7,
      pastilha: "violeta", pe: "no acervo inteiro" }),
    tile({ nome: "Artigos citados", valor: comWos.length, icone: "livro", serie: 1,
      pe: "de <b>" + fmt(arts.length) + "</b> no acervo" }),
    tile({ nome: "Mais citado", valor: comWos.length ? citacoesWos(comWos[0]) : 0,
      icone: "trofeu", serie: 6, pastilha: "bom",
      pe: comWos.length ? cortar(comWos[0].title, 46) : "sem citações ainda" }),
  ]);

  return escalonar(el("div", { class: "slide" }, [
    kpis,
    el("div", { class: "painel-duplo igual" }, [
      quadro("Artigos mais citados", "fogo",
        recado || placarDeCitacoes(comWos.slice(0, 6)),
        semWos ? "" : "todos os anos"),
      quadro("Mais citados nos últimos " + JANELA + " anos", "subida",
        recentes.length ? placarDeCitacoes(recentes.slice(0, 6))
          : vazio(semWos ? "Sem citações da WoS para o período."
            : "Nenhum artigo publicado de " + corte + " para cá tem citações na WoS."),
        recentes.length ? "publicados de " + corte + " a " + new Date().getFullYear() : ""),
    ]),
  ]));
}

/* Os mais citados saíram daqui para a tela `citados`, onde o número é o da
   WoS. Esta ficou com as pessoas: quem assina, quanto, e com quem. */
function slideDestaques() {
  const arts = artigos();

  const equipe = (D.members || []).filter(function (m) {
    return !m.is_external && (!AREA || m.research_line === AREA);
  }).slice(0, 8);
  const ranking = equipe.length ? C.bars({
    items: equipe.map(function (m) {
      return { label: m.short_name || m.full_name, value: m.n_articles || 0,
        note: (m.n_published || 0) + " publicados" };
    }),
    unit: "artigos", mono: true, labelWidth: 200, rowH: 54, caption: "produção por pessoa",
  }) : vazio("Nenhum integrante com produção registrada.");

  const porLinha = contar(arts, "research_line").slice(0, 6);
  const reparte = porLinha.length
    ? C.donut({ items: porLinha, unit: "artigos", caption: "por linha de pesquisa" })
    : vazio("Sem linha de pesquisa informada nos artigos.");

  const noventa = arts.filter(function (a) {
    const d = diasAte(a.accepted_on || a.published_on);
    return d !== null && d >= -90 && d <= 0;
  }).length;

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "linha-kpi" }, [
      tile({ nome: "Aceites em 90 dias", valor: noventa, icone: "trofeu", serie: 4,
        pastilha: "ambar", pe: "aceitos ou publicados" }),
      tile({ nome: "Colaborações", valor: (D.network && D.network.n_edges) || 0,
        icone: "rede", serie: 7, pastilha: "violeta", pe: "pares que assinam juntos" }),
      tile({ nome: "Maior índice h", valor: (D.overview || {}).best_h_index || 0, icone: "subida",
        serie: 6, pastilha: "bom", pe: "no laboratório" }),
    ]),
    el("div", { class: "painel-duplo igual" }, [
      quadro("Produção por integrante", "pessoas", ranking,
        equipe.length + " de "
          + fmt((D.members || []).filter(function (m) { return !m.is_external; }).length)
          + " integrantes"),
      quadro("Onde a produção está", "linhas", reparte, fmt(arts.length) + " artigos"),
    ]),
  ]));
}

/* A ordem é a de quem passa na frente da tela: primeiro o retrato de agora,
   depois o que está na mão de alguém (em produção, submetido), depois o que
   já rendeu (citações), depois o que vem (agenda e prazos), e por fim os
   cortes por área e por pessoa. */
const SLIDES = [
  { id: "agora", titulo: "Agora no laboratório", icone: "painel", montar: slideAgora },
  { id: "bancada", titulo: "Na bancada", icone: "experimento", montar: slideBancada },
  { id: "citados", titulo: "Os mais citados", icone: "fogo", montar: slideCitados },
  { id: "agenda", titulo: "O que vem a seguir", icone: "calendario", montar: slideAgenda },
  { id: "prazos", titulo: "Prazos e pendências", icone: "prazo", montar: slidePrazos },
  { id: "areas", titulo: "Produção por área", icone: "linhas", montar: slideAreas },
  { id: "andamento", titulo: "Em andamento", icone: "projeto", montar: slideAndamento },
  { id: "destaques", titulo: "Quem está produzindo", icone: "pessoas", montar: slideDestaques },
];

/* ?slides=agora,prazos escolhe quais telas entram no ciclo */
function ciclo() {
  const pedido = (PARAMS.get("slides") || "").split(",").map(function (s) { return s.trim(); })
    .filter(Boolean);
  if (!pedido.length) return SLIDES;
  const escolhidos = pedido.map(function (id) {
    return SLIDES.find(function (s) { return s.id === id; });
  }).filter(Boolean);
  return escolhidos.length ? escolhidos : SLIDES;
}
const ROTEIRO = ciclo();

/* ==========================================================================
   Motor: quem troca a tela
   ========================================================================== */
const palco = document.getElementById("palco");
const barra = document.getElementById("barra");
let atual = 0;
let pausado = false;
let inicio = 0;
let restante = SEGUNDOS * 1000;
let quadroAnim = null;

function desenhar(indice, direcao) {
  const slide = ROTEIRO[indice];
  const antigo = palco.firstElementChild;
  if (antigo) {
    antigo.classList.add("saindo");
    const morto = antigo;
    setTimeout(function () { if (morto.parentNode) morto.remove(); }, 320);
  }
  let node;
  try {
    node = slide.montar();
  } catch (erro) {
    /* um slide com defeito não pode parar o mural: ele avisa e o ciclo segue */
    console.error("falha ao montar o slide " + slide.id, erro);
    node = el("div", { class: "slide" },
      vazio("Não foi possível montar esta tela: " + erro.message));
  }
  palco.appendChild(node);
  document.getElementById("tituloSlide").textContent = slide.titulo;
  const casaIcone = document.getElementById("tituloIcone");
  casaIcone.textContent = "";
  casaIcone.appendChild(Icons.badge(slide.icone, null, 34));
  marcarPontos(indice);
  animarNumeros(node);
  animarGraficos(node);
  if (direcao !== "quieto") reiniciarRelogio();
}

function marcarPontos(indice) {
  const casa = document.getElementById("pontos");
  casa.textContent = "";
  ROTEIRO.forEach(function (s, i) {
    casa.appendChild(el("button", {
      class: i === indice ? "on" : "", type: "button", title: s.titulo,
      "aria-label": s.titulo, "aria-selected": String(i === indice), role: "tab",
      onclick: function () { ir(i); },
    }));
  });
}

/* Números sobem até o valor: um efeito curto, que também deixa claro que a
   tela está viva e não é uma foto esquecida no projetor. */
function animarNumeros(escopo) {
  const lento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  escopo.querySelectorAll(".tile .n").forEach(function (node) {
    const alvo = Number(node.dataset.alvo) || 0;
    const sufixo = node.dataset.sufixo || "";
    if (lento || alvo === 0) { node.textContent = fmt(alvo) + sufixo; return; }
    const duracao = 900;
    const partida = performance.now();
    (function passo(agora) {
      const t = Math.min(1, (agora - partida) / duracao);
      const suave = 1 - Math.pow(1 - t, 3);
      node.textContent = fmt(Math.round(alvo * suave)) + sufixo;
      if (t < 1) requestAnimationFrame(passo);
    })(partida);
  });
}

/* O gráfico se revela da esquerda para a direita; rosca e radar surgem por
   escala, porque um corte lateral num círculo fica torto. */
function animarGraficos(escopo) {
  escopo.querySelectorAll("svg.plot").forEach(function (svg, i) {
    svg.classList.add(svg.classList.contains("round") ? "surge" : "revela");
    svg.style.animationDelay = (140 + i * 110) + "ms";
  });
}

function reiniciarRelogio() {
  restante = SEGUNDOS * 1000;
  inicio = performance.now();
  if (quadroAnim) cancelAnimationFrame(quadroAnim);
  quadroAnim = requestAnimationFrame(tique);
}
function tique(agora) {
  if (!pausado) {
    const gasto = agora - inicio;
    const fracao = Math.min(1, gasto / (SEGUNDOS * 1000));
    barra.style.width = (fracao * 100).toFixed(2) + "%";
    if (fracao >= 1) { avancar(1); return; }
  } else {
    inicio = agora - (SEGUNDOS * 1000 - restante);
  }
  if (!pausado) restante = SEGUNDOS * 1000 - (agora - inicio);
  quadroAnim = requestAnimationFrame(tique);
}
function avancar(passo) {
  atual = (atual + passo + ROTEIRO.length) % ROTEIRO.length;
  desenhar(atual);
}
function ir(indice) { atual = indice; desenhar(atual); }
function alternarPausa() {
  pausado = !pausado;
  desenharControles();
  if (!pausado) inicio = performance.now() - (SEGUNDOS * 1000 - restante);
}

/* ------------------------------------------------------------- controles */
function desenharControles() {
  const casa = document.getElementById("controles");
  casa.textContent = "";
  [
    { icone: "anterior", titulo: "Tela anterior", acao: function () { avancar(-1); } },
    { icone: pausado ? "tocar" : "pausa", titulo: pausado ? "Retomar" : "Pausar",
      acao: alternarPausa },
    { icone: "proximo", titulo: "Próxima tela", acao: function () { avancar(1); } },
    { icone: "telaCheia", titulo: "Tela cheia", acao: telaCheia },
  ].forEach(function (b) {
    casa.appendChild(el("button", {
      type: "button", title: b.titulo, "aria-label": b.titulo, onclick: b.acao,
    }, Icons.get(b.icone, 17)));
  });
}
function telaCheia() {
  if (document.fullscreenElement) document.exitFullscreen();
  else if (document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen().catch(function () {});
  }
}

document.addEventListener("keydown", function (ev) {
  if (ev.key === " ") { ev.preventDefault(); alternarPausa(); }
  else if (ev.key === "ArrowRight") avancar(1);
  else if (ev.key === "ArrowLeft") avancar(-1);
  else if (ev.key === "f" || ev.key === "F") telaCheia();
});

/* os controles somem sozinhos: numa tela de sala, o cursor não fica parado
   em cima de um botão para sempre */
let sumico = null;
const mural = document.getElementById("mural");
document.addEventListener("mousemove", function () {
  mural.classList.add("mexeu");
  clearTimeout(sumico);
  sumico = setTimeout(function () { mural.classList.remove("mexeu"); }, 2600);
});

/* --------------------------------------------------------------- relógio */
function relogio() {
  const agora = new Date();
  document.getElementById("hora").textContent =
    String(agora.getHours()).padStart(2, "0") + ":" + String(agora.getMinutes()).padStart(2, "0");
  document.getElementById("data").textContent =
    DIAS_EXT[agora.getDay()] + ", " + agora.getDate() + " de " + MESES_EXT[agora.getMonth()];
}

/* ------------------------------------------------------------------ fita */
/* Duas cópias da mesma sequência, e a animação anda -50%: o laço fecha sem
   emenda visível. */
function desenharFita() {
  const casa = document.getElementById("fita");
  casa.textContent = "";
  const itens = [];
  eventos().forEach(function (e) {
    const d = diasAte(e.start_at);
    if (d !== null && d >= 0 && d <= 90) {
      itens.push({ icone: "calendario", forte: e.title, resto: porExtenso(d) });
    }
  });
  prazos().slice(0, 8).forEach(function (p) {
    itens.push({ icone: p.icone, forte: cortar(p.titulo, 60),
      resto: p.dias === null ? p.espera + " dias de espera" : porExtenso(p.dias) });
  });
  if (!itens.length) {
    itens.push({ icone: "painel", forte: "LAPE", resto: "sem compromissos registrados" });
  }
  const bloco = function () {
    return itens.slice(0, 12).map(function (x) {
      return el("span", {}, [Icons.get(x.icone, 15), el("b", { text: x.forte }),
        document.createTextNode(" · " + x.resto)]);
    });
  };
  bloco().forEach(function (n) { casa.appendChild(n); });
  bloco().forEach(function (n) { casa.appendChild(n); });
}

/* ------------------------------------------------------- tempo real (SSE) */
let fonte = null;
let pedidoPendente = null;
function abrirStream() {
  if (!window.EventSource) return;
  try {
    fonte = new EventSource("/api/stream");
  } catch (erro) { return; }
  fonte.addEventListener("pronto", function () { marcarVivo(true); });
  fonte.addEventListener("mudanca", function () {
    /* várias mudanças seguidas geram uma recarga só */
    clearTimeout(pedidoPendente);
    pedidoPendente = setTimeout(rebuscar, 900);
  });
  fonte.onerror = function () { marcarVivo(false); };
}
function marcarVivo(ligado, piscar) {
  const selo = document.getElementById("seloVivo");
  selo.hidden = !ligado;
  selo.classList.toggle("vivo", ligado);
  if (piscar) {
    selo.classList.remove("piscou");
    void selo.offsetWidth;
    selo.classList.add("piscou");
    document.getElementById("seloTexto").textContent = "atualizado agora";
    setTimeout(function () {
      document.getElementById("seloTexto").textContent = "ao vivo";
    }, 6000);
  }
}
function rebuscar() {
  fetch("/api/metrics", { credentials: "same-origin" })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error(r.status)); })
    .then(function (novo) {
      D = novo;
      desenharFita();
      desenhar(atual, "quieto");
      marcarVivo(true, true);
    })
    .catch(function () { /* sem rede: a tela segue com o último dado bom */ });
}

/* ---------------------------------------------------------------- arranque */
function comecar() {
  const o = D.overview || {};
  document.getElementById("labNome").textContent = o.lab_name || "LAPE";
  document.getElementById("labSub").textContent = o.institution || "";
  document.title = (o.lab_name || "LAPE") + " — Mural";
  /* O logotipo do laboratório, quando há arquivo; o ícone, quando não há.
     Nunca um espaço vazio: a marca fica na tela o tempo todo, e um buraco
     no canto superior esquerdo é a primeira coisa que a sala repara. */
  const marca = document.getElementById("marcaIcone");
  if (o.lab_logo) {
    marca.classList.add("tem-logo");
    marca.appendChild(el("img", { class: "logo-img", src: o.lab_logo,
      alt: o.lab_name || "LAPE" }));
  } else {
    marca.appendChild(Icons.get("mural", null));
  }

  if (AREA) {
    const selo = document.getElementById("seloFiltro");
    selo.hidden = false;
    selo.textContent = "";
    selo.appendChild(Icons.get("filtro", 14));
    selo.appendChild(document.createTextNode(" " + AREA));
  }

  relogio();
  setInterval(relogio, 15000);
  desenharFita();
  desenharControles();
  desenhar(0);
  abrirStream();
}
comecar();
