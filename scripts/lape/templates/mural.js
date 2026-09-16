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

/* O vínculo de cada pessoa, para a parede dizer quem é quem. Terceira
   cópia deste vocabulário (as outras estão em mapping.VINCULOS e no
   formulário), e há teste que reprova a divergência entre as três. */
const VINCULO_NOME = {
  coordenacao: "Coordenação", professor: "Professor(a)",
  pos_doutorado: "Pós-doutorado", doutorando: "Doutorando(a)",
  mestrando: "Mestrando(a)", bolsista_ic: "Bolsista de IC",
  bolsista_extensao: "Bolsista de extensão", voluntario: "Voluntário(a)",
  graduando: "Graduando(a)", tecnico: "Técnico(a)",
  colaborador: "Colaborador(a) externo",
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
/* A hora, quando existe -- e vazio quando nao.
   "Está cadastrado, mas não aparece": a etiqueta de data mostrava dia e
   mês, e o horário ficava no banco sem chegar à parede. Quem lê o mural
   precisa saber se a qualificação é às 9h ou às 14h, e é justamente para
   isso que o mural existe.
   Meia-noite exata NÃO vira "00:00": o campo aceita só a data, e nesse
   caso a hora gravada é zero por omissão -- escrever "00:00" afirmaria
   uma hora que ninguém marcou. Evento de dia inteiro também não mostra
   hora, mesmo que o horário tenha vindo preenchido. */
function horaDe(iso, diaInteiro) {
  if (diaInteiro) return "";
  const texto = String(iso || "");
  if (texto.length <= 10) return "";
  const hm = texto.slice(11, 16);
  if (!/^\d{2}:\d{2}$/.test(hm) || hm === "00:00") return "";
  return hm;
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
/* As três bases, na ordem em que o laboratório prefere ser contado: Web of
   Science e Scopus são as que a avaliação usa; a OpenAlex é aberta, entra
   sozinha na importação e cobre o que as outras duas só respondem com
   chave. */
const BASES = [
  { campo: "wos_citations", rotulo: "Web of Science", curto: "WoS" },
  { campo: "scopus_citations", rotulo: "Scopus", curto: "Scopus" },
  { campo: "openalex_citations", rotulo: "OpenAlex", curto: "OpenAlex" },
];

function citacoesDe(a, base) { return base ? (a[base.campo] || 0) : 0; }

/* Quantas bases têm número, para a tela poder dizer "e as outras duas
   ainda não responderam" em vez de deixar a impressão de que só existe uma. */
function basesComNumero(arts) {
  return BASES.filter(function (base) {
    return arts.some(function (a) { return (a[base.campo] || 0) > 0; });
  });
}
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
      item.hora ? el("small", { class: "hora", text: item.hora }) : null,
    ].filter(Boolean)),
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
  /* Barras, e não área: a parede é lida de longe e de passagem, e a
     pergunta que se faz dela é "quantos naquele ano", não "qual o
     desenho da curva". Com uma série só, o número vai escrito em cima
     de cada barra -- quem olha do corredor lê o valor sem precisar
     seguir a linha até o eixo. */
  const grafico = recentes.length
    ? C.columns({
      labels: recentes.map(function (r) { return String(r.year); }),
      series: [{ label: "Publicações", values: recentes.map(function (r) { return r.n_articles; }) }],
      /* `fill`: o cartao do mural tem altura propria, e o grafico desenha
         COM ela em vez de desenhar em 460 e encolher para caber. A altura
         aqui e so o que vale se a caixa nao tiver altura nenhuma. */
      fill: true, height: 460, caption: "publicações por ano",
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

  /* Só a pauta, em toda a largura. O quadro ao lado desenhava os doze
     meses seguintes em colunas, e a coordenação pediu que saísse: a
     agenda de um laboratório é rala e irregular, e doze colunas quase
     todas em zero se leem como um laboratório parado -- quando o que a
     tela tinha a dizer eram os três ou quatro compromissos da lista.
     Com a largura inteira cabem dez, em vez de seis. */
  const cabem = 10;
  const pauta = proximos.length
    ? el("ul", { class: "pauta" }, proximos.slice(0, cabem).map(function (e) {
      return linhaDePauta({
        titulo: e.title,
        detalhe: [TIPO_EVENTO[e.kind] || e.kind, e.location_name || e.city,
          e.research_line].filter(Boolean).join(" · "),
        data: e.start_at, dias: diasAte(e.start_at),
        hora: horaDe(e.start_at, e.all_day),
        icone: ICONE_EVENTO[e.kind] || "calendario",
      });
    }))
    : vazio("Nenhum compromisso marcado daqui para a frente.");

  return escalonar(el("div", { class: "slide" }, [
    quadro("Próximos compromissos", "calendario", pauta,
      proximos.length > cabem ? "e mais " + (proximos.length - cabem) : ""),
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

/* O gráfico da produção por linha de pesquisa -- ou, quando a parede está
   filtrada por uma área só, o corte que faz sentido dentro dela. Comparar
   linhas com `?area=` deixaria uma barra sozinha na tela. */
function graficoDasAreas() {
  const arts = artigos();
  if (AREA) {
    const porTipo = contar(arts, function (a) { return a.study_type || "Não informado"; }).slice(0, 8);
    return {
      titulo: "Por tipo de estudo", icone: "barras",
      nota: fmt(arts.length) + " artigos",
      grafico: porTipo.length ? C.columns({
        labels: porTipo.map(function (x) { return cortar(x.label, 22); }),
        series: [{ label: "Artigos", values: porTipo.map(function (x) { return x.value; }) }],
        fill: true, height: 520, caption: "artigos por tipo de estudo",
      }) : vazio("Sem artigos nesta área."),
    };
  }
  const porLinha = (D.research_lines || []).map(function (l) {
    const meus = arts.filter(function (a) { return a.research_line === l.name; });
    return {
      nome: l.name,
      publicados: meus.filter(function (a) { return a.status === "publicado"; }).length,
      avaliacao: meus.filter(function (a) {
        return a.status === "submetido" || a.status === "em_revisao"; }).length,
      producao: meus.filter(function (a) { return a.status === "em_producao"; }).length,
      total: meus.length,
      ativa: l.active !== 0,
    };
  }).filter(function (x) {
    /* Linha encerrada só continua na parede se ainda tiver artigo: a
       produção de quem publicou ali é história do laboratório e não
       desaparece porque a linha saiu da lista de opções. Encerrada e
       vazia é só uma fileira de zeros ocupando a tela. */
    return x.ativa || x.total > 0;
  }).sort(function (a, b) { return b.total - a.total; }).slice(0, 8);

  /* Ter linha cadastrada e ter artigo LIGADO a uma linha são coisas
     diferentes, e a parede precisa distinguir as duas. Com as linhas
     declaradas e nenhum artigo apontando para elas, o gráfico saía: um
     quadro do tamanho da parede, com os nomes das oito linhas no eixo e
     nenhuma barra em cima. Quem olha não lê "ninguém classificou os
     artigos ainda" -- lê "este laboratório não produziu nada", que é o
     contrário do que o dado diz. */
  const comArtigo = porLinha.some(function (x) { return x.total > 0; });

  return {
    titulo: "Publicados, em avaliação e em produção", icone: "barras",
    nota: fmt(arts.length) + " artigos",
    grafico: (porLinha.length && comArtigo) ? C.columns({
      labels: porLinha.map(function (x) { return cortar(x.nome, 22); }),
      series: [
        { label: "Publicados", values: porLinha.map(function (x) { return x.publicados; }) },
        { label: "Em avaliação", values: porLinha.map(function (x) { return x.avaliacao; }) },
        { label: "Em produção", values: porLinha.map(function (x) { return x.producao; }) },
      ],
      mode: "empilhado", fill: true, height: 520, caption: "produção por linha de pesquisa",
    /* Sem número de linhas na frase: `porLinha` já veio cortado em oito,
       e dizer "as 8 linhas" num laboratório que cadastrou onze seria a
       parede errando uma conta que qualquer um ali confere. */
    }) : vazio(porLinha.length
      ? "As linhas de pesquisa estão cadastradas, e nenhum dos "
        + fmt(arts.length) + " artigos está ligado a uma delas. A linha se "
        + "escolhe na ficha do artigo, no painel."
      : "Nenhuma linha de pesquisa cadastrada."),
  };
}

/* Citações e produção por área na mesma tela.
   Esta tela já foi "Os mais citados", com dois quadros de ranking de
   artigo. Os dois saíram a pedido da coordenação: numa parede de
   corredor, uma lista dos artigos campeões diz menos do que ocupa, e o
   número que interessa é o do acervo. O espaço que sobrou é onde a
   produção por área passou a morar -- ela era uma tela só dela, e vinha
   três telas adiante. */
function slideCitados() {
  const arts = artigos();
  const area = graficoDasAreas();

  /* A parede promete "citações na WoS" e "citações na Scopus", e é o
     número DAQUELA base que entra em cada uma -- nunca o da melhor
     fonte, que costuma ser maior e diria outra coisa.

     Zero e "não perguntei a esta base" são coisas diferentes, e é essa
     diferença que já pôs "0 citações" numa parede de laboratório com
     milhares. Por isso o pé de cada número diz qual dos dois é: uma base
     sem nenhum número em nenhum artigo não respondeu -- falta a chave --,
     e a tela fala isso em vez de deixar o zero mentir sozinho. */
  const cores = { wos_citations: { serie: 7, pastilha: "violeta" },
                  scopus_citations: { serie: 4, pastilha: "ambar" } };
  const duas = BASES.filter(function (b) { return cores[b.campo]; }).map(function (b) {
    const total = arts.reduce(function (soma, a) { return soma + citacoesDe(a, b); }, 0);
    const respondeu = arts.some(function (a) { return citacoesDe(a, b) > 0; });
    return tile({ nome: "Citações na " + b.curto, valor: total, icone: "citacao",
      serie: cores[b.campo].serie, pastilha: cores[b.campo].pastilha,
      pe: respondeu ? "no acervo inteiro"
        : "esta base ainda não respondeu — falta a chave" });
  });

  /* "Artigos citados" conta por artigo e pela melhor fonte de cada um:
     um artigo que a OpenAlex conhece e a WoS não continua sendo um
     artigo citado. O pé diz de onde veio, para ninguém somar este
     número com os dois de cima. */
  const citados = arts.filter(function (a) { return citacoes(a) > 0; }).length;
  const responderam = basesComNumero(arts);
  const fonte = responderam.length
    ? "melhor fonte por artigo · " + responderam.map(function (b) { return b.curto; }).join(", ")
    : "nenhuma base respondeu ainda";

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "linha-kpi" }, duas.concat([
      tile({ nome: "Artigos citados", valor: citados, icone: "livro", serie: 1,
        pe: "de <b>" + fmt(arts.length) + "</b> no acervo · " + fonte }),
    ])),
    quadro(area.titulo, area.icone, area.grafico, area.nota),
  ]));
}

/* Os mais citados saíram daqui para a tela `citados`, onde o número é o da
   WoS. Esta ficou com as pessoas -- quem são, não quanto produzem. */
/* Quem trabalha em cada linha. Aqui havia uma rosca de ARTIGOS por linha,
   e a coordenação trocou: a parede do corredor é lida pela própria equipe e
   por quem visita o laboratório, e a pergunta que fazem diante de uma linha
   de pesquisa é "quem toca isso", não "quantos papéis saíram dali" -- que a
   tela das citações já mostra, em barras, ao lado da produção por área.

   Quem está no laboratório e não tem linha declarada entra também, e entra
   nomeado como o que é. Escondê-lo faria a soma das linhas não bater com o
   total da equipe, e quem confere de cabeça acharia que a parede perdeu
   alguém -- sem a parede ter como avisar que não perdeu. Hoje, no banco do
   LAPE, ESTE é o caso de todo mundo: ninguém tem linha declarada.

   Linha sem ninguém não vira fileira vazia; linha declarada que não está
   na lista da coordenação também conta, porque a pessoa está lá de todo
   jeito. Fora do desenho, para poder ser testada de verdade. */
function agrupadosPorLinha(gente, linhas) {
  const porNome = new Map();
  linhas.forEach(function (l) { porNome.set(l.name, []); });
  const semLinha = [];
  gente.forEach(function (m) {
    if (!m.research_line) { semLinha.push(m); return; }
    if (!porNome.has(m.research_line)) porNome.set(m.research_line, []);
    porNome.get(m.research_line).push(m);
  });
  const saida = [];
  porNome.forEach(function (quem, nome) {
    if (quem.length) saida.push({ nome: nome, gente: quem });
  });
  saida.sort(function (a, b) { return b.gente.length - a.gente.length; });
  if (semLinha.length) saida.push({ nome: "Sem linha declarada", gente: semLinha });
  return saida;
}

function slideDestaques() {
  /* "Quem está produzindo" é uma frase no presente, e a parede é lida por
     quem passa. Alguém que saiu do laboratório escreveu de fato o que
     escreveu -- por isso continua nas tabelas de histórico do painel --,
     mas anunciá-lo hoje como quem está produzindo é dizer uma coisa que
     não é verdade, e ninguém na sala tem como saber que não é.

     `is_external` é o que separa o laboratório de quem assina junto: o
     coautor de outra instituição entra nos artigos e na rede de
     colaboração, e não entra aqui. Esta tela é a do pessoal do LAPE. */
  const doLape = (D.members || []).filter(function (m) {
    return !m.is_external && m.active !== 0 && !m.left_on
      && (!AREA || m.research_line === AREA);
  });
  const equipe = doLape.slice(0, 8);

  /* Quem é quem, e não quanto cada um produziu. Era um ranking de artigos
     por pessoa; a parede fica no corredor do laboratório e ordenar colegas
     por número de publicação ali não informa nada que a equipe já não
     saiba -- só expõe quem entrou este ano ao lado de quem está há dez.
     O que a parede tem a dizer sobre a equipe é quem ela é: o nome, o
     vínculo e a linha em que a pessoa trabalha. */
  /* Oito é o que cabe no cartão sem rolar. A parede não tem quem role: o
     que passa da borda simplesmente não existe para quem olha, e o
     cabeçalho sai junto -- foi o que aconteceu com doze. */
  const elenco = equipe.length ? el("table", { class: "placar" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "Integrante" }), el("th", { text: "Vínculo" }),
    ])),
    el("tbody", {}, equipe.map(function (m) {
      return el("tr", {}, [
        el("td", {}, el("div", { class: "quem" }, [
          Icons.badge("pessoa", null, 22),
          el("span", { text: m.short_name || m.full_name })])),
        /* Sem vínculo declarado fica o travessão. Inventar "Graduando(a)"
           para quem ninguém classificou seria a parede afirmando o que não
           sabe, na frente da própria pessoa. */
        /* Só o nome e o vínculo. A linha de pesquisa também esteve aqui e
           saiu: no cartão de meia largura ela cabia como "Psicologi…", que
           não é informação -- é ruído ocupando a largura que o nome da
           pessoa precisa. Ela voltou ao lado, com a linha inteira e as
           pessoas dela juntas. */
        el("td", { text: VINCULO_NOME[m.role] || "—" }),
      ]);
    })),
  ]) : vazio("Nenhum integrante cadastrado.");

  const linhas = agrupadosPorLinha(doLape, D.research_lines || []);

  /* Oito linhas, e quatro nomes por linha: é o que cabe sem rolar, e a
     parede não tem quem role. O resto vira "+3", que é informação -- ao
     contrário de um nome cortado no meio. */
  const CABEM = 4;
  const porLinha = linhas.slice(0, 8).length ? el("table", { class: "placar" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "Linha de pesquisa" }), el("th", { text: "Integrantes" }),
    ])),
    el("tbody", {}, linhas.slice(0, 8).map(function (x) {
      const nomes = x.gente.map(function (m) { return m.short_name || m.full_name; });
      const mostra = nomes.slice(0, CABEM).join(", ")
        + (nomes.length > CABEM ? " +" + (nomes.length - CABEM) : "");
      return el("tr", {}, [
        el("td", {}, el("div", { class: "quem" }, [
          Icons.badge("linhas", null, 22), el("span", { text: cortar(x.nome, 34) })])),
        el("td", { text: mostra }),
      ]);
    })),
  ]) : vazio("Nenhuma linha de pesquisa com integrante declarado.");

  const arts = artigos();
  const noventa = arts.filter(function (a) {
    const d = diasAte(a.accepted_on || a.published_on);
    return d !== null && d >= -90 && d <= 0;
  }).length;

  return escalonar(el("div", { class: "slide" }, [
    el("div", { class: "linha-kpi" }, [
      tile({ nome: "Aceites em 90 dias", valor: noventa, icone: "trofeu", serie: 4,
        pastilha: "ambar", pe: "aceitos ou publicados" }),
      /* O "Maior índice h" ficava aqui e saiu a pedido da coordenação:
         numa parede lida pela própria equipe, o maior h é sempre da mesma
         pessoa, e anunciá-lo todo dia ao lado da lista de quem é quem faz
         desta tela um pódio -- que é justamente o que ela deixou de ser
         quando o ranking de artigos por pessoa saiu. */
      tile({ nome: "Colaborações", valor: (D.network && D.network.n_edges) || 0,
        icone: "rede", serie: 7, pastilha: "violeta", pe: "pares que assinam juntos" }),
    ]),
    el("div", { class: "painel-duplo igual" }, [
      quadro("Nossa equipe", "pessoas", elenco,
        equipe.length + " de " + fmt(doLape.length) + " integrantes"),
      quadro("Integrantes de cada linha", "linhas", porLinha,
        linhas.length + (linhas.length === 1 ? " linha" : " linhas")),
    ]),
  ]));
}

/* A ordem é a de quem passa na frente da tela: primeiro o retrato de agora,
   depois o que está na mão de alguém (em produção, submetido), depois o que
   já rendeu -- citações e a produção por área, na mesma tela --, depois o
   que vem (agenda e prazos), e por fim quem é a equipe.

   Saíram daqui duas telas, a pedido da coordenação: "Produção por área",
   que virou o gráfico da tela das citações, e "Em andamento", que repetia
   em lista o que os números de "Agora no laboratório" já dizem. Seis telas
   a quinze segundos dão um minuto e meio de volta -- oito davam dois. */
const SLIDES = [
  { id: "agora", titulo: "Agora no laboratório", icone: "painel", montar: slideAgora },
  { id: "bancada", titulo: "Na bancada", icone: "experimento", montar: slideBancada },
  { id: "citados", titulo: "Citações e produção por área", icone: "citacao", montar: slideCitados },
  { id: "agenda", titulo: "O que vem a seguir", icone: "calendario", montar: slideAgenda },
  { id: "prazos", titulo: "Prazos e pendências", icone: "prazo", montar: slidePrazos },
  { id: "destaques", titulo: "Nossa equipe", icone: "pessoas", montar: slideDestaques },
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
