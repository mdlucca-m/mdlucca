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

/* O contorno dos países pro mapa-múndi: geografia, não dado do
   laboratório, então é buscado uma vez só e fora do payload -- são 70KB
   que nunca mudam e que só a tela "Pelo mundo" precisa, e o navegador
   já guarda em cache (o mesmo arquivo que /panorama e /aovivo usam). Não
   é "atualização automática de dado": é o mesmo tipo de carga que o CSS
   e os ícones, só que sob demanda. */
let mundoGeo = null;
fetch("/api/geo/mundo.json", { credentials: "same-origin" })
  .then(function (r) { return r.ok ? r.json() : null; })
  .then(function (dados) {
    mundoGeo = (dados && dados.paises) || null;
    if (mundoGeo && ROTEIRO[atual] && ROTEIRO[atual].id === "mundo") desenhar(atual, "quieto");
  })
  .catch(function () { /* sem mapa: a tela "Pelo mundo" segue só com o ranking */ });

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
  if (typeof spec.valor === "string") {
    /* texto ("Estudo transversal", "há 3 dias"): entra como está, sem contar */
    numero.textContent = spec.valor;
    numero.classList.add("texto");
  } else {
    numero.dataset.alvo = String(spec.valor === null || spec.valor === undefined ? 0 : spec.valor);
    if (spec.decimais) numero.dataset.decimais = String(spec.decimais);
    if (spec.prefixo) numero.dataset.prefixo = spec.prefixo;
  }
  if (spec.sufixo) numero.dataset.sufixo = spec.sufixo;
  casa.appendChild(topo);
  casa.appendChild(numero);
  if (spec.pe) casa.appendChild(el("div", { class: "pe", html: spec.pe }));
  return casa;
}
function quadro(titulo, icone, corpo, nota, classeExtra) {
  return el("div", { class: classeExtra ? "quadro " + classeExtra : "quadro" }, [
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

  const corpo = [kpis];
  const presenca = faixaPresenca();
  if (presenca) corpo.push(presenca);
  corpo.push(el("div", { class: "painel-duplo" }, [
    quadro("Publicações por ano", "subida", grafico,
      recentes.length ? recentes[0].year + "–" + recentes[recentes.length - 1].year : "", "moldura-viva"),
    quadro("Situação da produção", "processo", rosca, fmt(arts.length) + " artigos", "moldura-viva"),
  ]));

  return escalonar(el("div", { class: "slide" }, corpo));
}

/* Quem bateu ponto e ainda não bateu saída -- o mesmo dado que a tela de
   ponto do integrante usa. Sem gente presente, a faixa nem aparece: um
   quadro "0 no laboratório" o dia inteiro vira ruído, não informação. */
function faixaPresenca() {
  const t = tv();
  const pessoas = (t && t.organograma && t.organograma.people) || [];
  const presentes = pessoas.filter(function (p) { return p.ativo_agora; });
  if (!presentes.length) return null;

  return el("div", { class: "faixa-presenca" }, [
    el("div", { class: "faixa-presenca-titulo" }, [
      el("span", { class: "ponto-vivo" }),
      el("span", { text: presentes.length + " no LAPE agora" }),
    ]),
    el("div", { class: "faixa-presenca-lista" }, presentes.map(function (p) {
      const desde = p.ha_horas !== null && p.ha_horas !== undefined
        ? " · há " + porHoras(p.ha_horas) : "";
      return el("span", { class: "chip-presenca", title: (p.atividade || "presente") + desde }, [
        el("span", { class: "chip-ponto" }),
        el("span", { text: p.full_name }),
      ]);
    })),
  ]);
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
      nome: l.name, icone: l.icone || "linhas",
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
    grafico: (porLinha.length && comArtigo) ? faixasPorLinha(porLinha)
      : vazio(porLinha.length
        ? "As linhas de pesquisa estão cadastradas, e nenhum dos "
          + fmt(arts.length) + " artigos está ligado a uma delas. A linha se "
          + "escolhe na ficha do artigo, no painel."
        : "Nenhuma linha de pesquisa cadastrada."),
  };
}

/* Faixas horizontais, uma por linha, com o nome inteiro e o ícone da
   linha. Era um gráfico de colunas: com duas linhas povoadas e seis
   vazias saíam duas colunas magras num quadro do tamanho da parede, e os
   nomes cortados em "Fibromialgia e doença…". Na horizontal o nome cabe,
   cada linha ATIVA aparece -- com zero, que é informação --, e as três
   situações se empilham na mesma faixa, na ordem em que o artigo anda:
   em produção, em avaliação, publicado. */
function faixasPorLinha(porLinha) {
  const teto = Math.max(1, ...porLinha.map(function (x) { return x.total; }));
  const partes = [
    ["producao", "Em produção", "--series-3"],
    ["avaliacao", "Em avaliação", "--series-2"],
    ["publicados", "Publicados", "--series-1"],
  ];
  const lista = el("ul", { class: "faixas" }, porLinha.map(function (x, i) {
    const trilho = el("div", { class: "trilho-faixa" }, partes.map(function (p) {
      const largura = 100 * x[p[0]] / teto;
      return el("i", { class: "parte", style: "--w:" + largura.toFixed(2) + "%;--c:var(" + p[2] + ")",
        title: p[1] + ": " + fmt(x[p[0]]) }, x[p[0]] && largura >= 9 ? [el("b", { text: fmt(x[p[0]]) })] : []);
    }));
    return el("li", { style: "--i:" + i }, [
      el("div", { class: "quem" }, [Icons.badge(x.icone, null, 26),
        el("span", { text: x.nome, title: x.nome })]),
      trilho,
      el("span", { class: "total", text: fmt(x.total) }),
    ]);
  }));
  const legenda = el("div", { class: "legenda-faixas" }, partes.map(function (p) {
    return el("span", {}, [el("i", { style: "background:var(" + p[2] + ")" }), document.createTextNode(p[1])]);
  }));
  return el("div", { class: "faixas-caixa" }, [lista, legenda]);
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
    quadro(area.titulo, area.icone, area.grafico, area.nota, "moldura-viva"),
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
  /* Quantas pessoas cabem depende da altura da parede: oito cabiam na TV
     e não cabiam no monitor da sala, onde a tabela transbordava o cartão
     e o cabeçalho, fixo no topo, cobria o primeiro nome. A conta usa a
     altura de agora, e o cabeçalho deixou de ser fixo no mural. */
  const CABEM_PESSOAS = Math.max(4, Math.min(8, Math.floor((window.innerHeight - 420) / 54)));
  const equipe = doLape.slice(0, CABEM_PESSOAS);

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
  const porLinha = linhas.slice(0, CABEM_PESSOAS).length ? el("table", { class: "placar" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: "Linha de pesquisa" }), el("th", { text: "Integrantes" }),
    ])),
    el("tbody", {}, linhas.slice(0, CABEM_PESSOAS).map(function (x) {
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

/* ==========================================================================
   As telas da TV — o que a parede acrescenta ao painel
   Vêm de /api/tv (`D.tv`): os indicadores temáticos do ano, o ritmo mensal
   com tendência e projeção, os países que assinam, os acervos com a rotina
   que os atualiza. Sem `D.tv` (o mural exportado em arquivo, ou a rota que
   falhou), essas telas saem do ciclo em vez de aparecer vazias: a parede
   não anuncia o que não tem.
   ========================================================================== */
function tv() { return D.tv || null; }

/* O KPI temático vira um azulejo da parede: número com a unidade embaixo,
   e a frase que diz de onde saiu. Valor em texto ("Estudo transversal")
   entra como texto -- o azulejo não anima o que não é número. */
const TOM_DO_KPI = { tempo: "cyan", aceite: "green", acesso_aberto: "yellow", internacional: "purple",
  tipo: "orange", orientandos: "magenta", revistas: "blue", paises: "cyan" };
const PASTILHA_DO_TOM = { cyan: "azul", green: "bom", yellow: "ambar", purple: "violeta",
  orange: "laranja", magenta: "magenta", blue: "azul" };
const SERIE_DO_TOM = { cyan: 1, green: 3, yellow: 4, purple: 7, orange: 2, magenta: 5, blue: 1 };
function azulejoDoKpi(k) {
  const tom = TOM_DO_KPI[k.code] || "blue";
  const numero = typeof k.valor === "number";
  return tile({
    nome: k.rotulo, icone: k.icon || "achado", serie: SERIE_DO_TOM[tom], pastilha: PASTILHA_DO_TOM[tom],
    valor: numero ? k.valor : (k.valor === null || k.valor === undefined ? "—" : String(k.valor)),
    decimais: numero && Math.round(k.valor) !== k.valor ? 1 : 0,
    sufixo: numero && k.unidade === "%" ? "%" : "",
    pe: (numero && k.unidade && k.unidade !== "%" ? "<b>" + k.unidade + "</b> · " : "") + cortar(k.pe || "", 70),
  });
}

/* Uma lista de frases lida de longe: ícone, negrito e o resto. */
function frases(itens, icone) {
  return el("ul", { class: "frases" }, itens.map(function (t) {
    const texto = typeof t === "string" ? { forte: "", resto: t } : t;
    return el("li", {}, [Icons.badge(texto.icone || icone || "achado", texto.tom || null, null),
      el("span", {}, [texto.forte ? el("b", { text: texto.forte + " " }) : null,
        document.createTextNode(texto.resto || "")])]);
  }));
}

function slideTemas() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Os indicadores temáticos ainda não chegaram.")));
  const kpis = {};
  (t.temas.kpis || []).forEach(function (k) { kpis[k.code] = k; });
  const ordem = ["tempo", "aceite", "acesso_aberto", "internacional", "revistas", "paises"];
  const linha = el("div", { class: "linha-kpi" }, ordem.filter(function (c) { return kpis[c]; })
    .map(function (c) { return azulejoDoKpi(kpis[c]); }));

  const revistas = (t.temas.revistas || []).filter(function (r) { return r.value > 0; });
  const grafico = revistas.length
    ? C.bars({ items: revistas.map(function (r) { return { label: cortar(r.label, 44), value: r.value }; }),
      unit: "artigos", caption: "revistas em que mais se publica", labelWidth: 250, rowH: 40 })
    : vazio("Nenhum artigo publicado com revista informada.");

  const ditos = [];
  if (kpis.tipo && kpis.tipo.valor && kpis.tipo.valor !== "—") {
    ditos.push({ icone: "experimento", forte: "Desenho mais frequente:", resto: kpis.tipo.valor + " — " + (kpis.tipo.pe || "") });
  }
  if (kpis.orientandos) {
    ditos.push({ icone: "orientacao", forte: fmt(kpis.orientandos.valor) + " orientando(s) publicando",
      resto: "em " + (t.periodo.ate || "") + " — " + (kpis.orientandos.pe || "") });
  }
  ["tempo", "aceite", "acesso_aberto", "internacional"].forEach(function (c) {
    const k = kpis[c];
    if (!k) return;
    const valor = k.valor === null || k.valor === undefined ? "sem dado"
      : (k.unidade === "%" ? String(k.valor).replace(".", ",") + "%" : fmt(k.valor) + " " + (k.unidade || ""));
    ditos.push({ icone: k.icon || "achado", forte: k.rotulo + ":", resto: valor + " — " + (k.pe || "") });
  });

  return escalonar(el("div", { class: "slide" }, [
    linha,
    el("div", { class: "painel-duplo" }, [
      quadro("Onde se publica", "citacao", grafico, revistas.length + (revistas.length === 1 ? " revista" : " revistas"), "moldura-viva"),
      quadro("O que os indicadores dizem", "achado", frases(ditos.slice(0, 6)), t.periodo.rotulo || ""),
    ]),
  ]));
}

function slideRitmo() {
  const t = tv();
  const s = t && t.sinais;
  if (!s || !s.labels || !s.labels.length) {
    return escalonar(el("div", { class: "slide" }, vazio("Sem curva mensal ainda: ela nasce com a data de publicação dos artigos.")));
  }
  const proj = s.projecao || { valores: [], alto: [], baixo: [], meses: [] };
  const soma = function (v) { return (v || []).reduce(function (a, b) { return a + (Number(b) || 0); }, 0); };
  const seisMeses = Math.round(soma(proj.valores));
  const deriva = s.deriva_ano === null || s.deriva_ano === undefined ? null : Number(s.deriva_ano);
  const ritmo = Number(s.ritmo) || 0;
  const pe = function (texto) { return texto; };

  const linha = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Ritmo", valor: ritmo, decimais: 2, icone: "subida", serie: 1,
      pe: "publicações por mês" + (s.ritmo_antes !== null && s.ritmo_antes !== undefined
        ? " · antes <b>" + String(Number(s.ritmo_antes).toFixed(2)).replace(".", ",") + "</b>" : "") }),
    tile({ nome: "Deriva por ano", valor: deriva === null ? "—" : Math.abs(deriva), decimais: 2,
      prefixo: deriva === null ? "" : (deriva > 0 ? "+" : deriva < 0 ? "−" : ""),
      icone: deriva !== null && deriva < 0 ? "aviso" : "alvo", serie: deriva !== null && deriva < 0 ? 4 : 3,
      pastilha: deriva !== null && deriva < 0 ? "ambar" : "bom",
      pe: deriva === null ? "sem meses suficientes" : "publicações/mês a " + (deriva < 0 ? "menos" : "mais") + " a cada ano (R² " + String(Number(s.r2 || 0).toFixed(2)).replace(".", ",") + ")" }),
    tile({ nome: "Próximos 6 meses", valor: seisMeses, icone: "prazo", serie: 7, pastilha: "violeta",
      pe: proj.valores && proj.valores.length ? "entre <b>" + Math.round(soma(proj.baixo)) + "</b> e <b>" + Math.round(soma(proj.alto)) + "</b>, pela deriva" : "sem projeção" }),
    tile({ nome: "Acumulado", valor: Math.round(Number(s.acumulado) || 0), icone: "producao", serie: 6, pastilha: "bom",
      pe: "artigos com mês na janela de cinco anos" + (s.limite_k ? " · teto à vista <b>" + Math.round(s.limite_k) + "</b>" : "") }),
  ]);

  const grafico = C.lines({
    labels: s.meses, height: 420, fill: true, caption: "publicações por mês, com a tendência e o intervalo de confiança",
    series: [
      { label: "Publicações", values: s.valores, area: true },
      { label: "Tendência", values: s.tendencia, width: 3,
        band: s.tendencia_alto && s.tendencia_alto.length ? { alto: s.tendencia_alto, baixo: s.tendencia_baixo } : null },
    ],
  });

  const ditos = (s.leituras || []).map(function (l) { return { icone: "achado", resto: l }; });
  /* a inflexão só entra se as leituras não a disseram -- a mesma frase
     duas vezes na parede é a tela gaguejando */
  if (s.inflexao && !ditos.some(function (d) { return /inflex/i.test(d.resto); })) {
    ditos.push({ icone: "subida", tom: s.inflexao.sentido && s.inflexao.sentido.indexOf("acelerar") >= 0 ? "bom" : "alerta",
      forte: "Última inflexão em " + s.inflexao.rotulo + ":", resto: "a tendência " + s.inflexao.sentido + "." });
  }
  if (proj.meses && proj.meses.length) {
    ditos.push({ icone: "prazo", forte: "Projeção:", resto: proj.meses.map(function (m, i) {
      return m + " " + String(Number(proj.valores[i]).toFixed(1)).replace(".", ","); }).join(" · ") });
  }

  return escalonar(el("div", { class: "slide" }, [
    linha,
    el("div", { class: "painel-duplo" }, [
      quadro("Mês a mês, com tendência", "subida", grafico, s.meses[0] + " – " + s.meses[s.meses.length - 1], "moldura-viva"),
      quadro("O que o cálculo diz", "achado", frases(ditos.slice(0, 6)), "regras escritas, não modelo"),
    ]),
  ]));
}

/* O ranking dos países: bandeira, nome, barra e número. É a lista do globo
   do ao vivo, parada -- na parede ninguém espera o globo pousar. */
function rankingDePaises(paises) {
  const max = Math.max(1, ...paises.map(function (p) { return Number(p.n) || 0; }));
  return el("ul", { class: "ranking" }, paises.map(function (p, i) {
    const li = el("li", { style: "--w:" + Math.round(100 * (Number(p.n) || 0) / max) + "%;--i:" + i }, [
      el("span", { class: "bandeira" }, [
        typeof Bandeiras !== "undefined" && p.iso ? Bandeiras.get(p.iso, p.pais) : Icons.get("mapa", 18)]),
      el("span", { class: "nome", text: p.pais }),
      el("span", { class: "trilho" }, [el("i")]),
      el("b", { text: fmt(p.n) }),
    ]);
    return li;
  }));
}

function slideMundo() {
  const t = tv();
  const m = t && t.mundo;
  if (!m) return escalonar(el("div", { class: "slide" }, vazio("O mapa dos países ainda não chegou.")));
  const paises = m.paises || [];
  const linha = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Países que assinam", valor: m.n_paises || 0, icone: "mapa", serie: 1, pe: "com ao menos um autor" }),
    tile({ nome: "Fora do Brasil", valor: m.n_fora_do_brasil || 0, icone: "espaco", serie: 7, pastilha: "violeta",
      pe: "colaboração internacional" }),
    tile({ nome: "Artigos com país", valor: m.artigos_com_pais || 0, icone: "producao", serie: 3, pastilha: "bom",
      pe: "autor com afiliação cadastrada" }),
    tile({ nome: "Instituições", valor: m.instituicoes || 0, icone: "instituicao", serie: 4, pastilha: "ambar",
      pe: "com endereço no mapa" }),
  ]);
  /* Com o contorno dos países já carregado, o mapa-múndi de verdade
     substitui a lista -- e usa todo país com produção (m.mapa_paises),
     não só o top 10 que cabe na lista, senão um país de fora do ranking
     apareceria "sem dado" no mapa mesmo tendo artigo. Sem o contorno
     ainda (primeira troca de tela, antes do fetch responder), a lista
     seve de retrato imediato -- ninguém fica olhando pra tela vazia
     esperando 70KB de rede. */
  const ranking = mundoGeo
    ? el("div", { class: "corpo" }, C.mapaMundi({
        world: mundoGeo, values: m.mapa_paises || {}, unit: "artigos",
        caption: "produção por país", emptyMessage: "Nenhum país registrado ainda." }))
    : (paises.length ? rankingDePaises(paises) : vazio("Nenhum país cadastrado nos autores ainda."));
  const instituicoes = [];
  paises.forEach(function (p) {
    (p.instituicoes || []).forEach(function (nome) {
      if (instituicoes.length < 8 && !instituicoes.some(function (x) { return x.resto === nome; })) {
        instituicoes.push({ icone: "instituicao", forte: p.pais + " ·", resto: nome });
      }
    });
  });
  return escalonar(el("div", { class: "slide" }, [
    linha,
    el("div", { class: "painel-duplo igual" }, [
      quadro("Países que assinam com o LAPE", "mapa", ranking,
        "sede: " + ((m.sede && m.sede.nome) || "UDESC / CEFID"), "moldura-viva"),
      quadro("Instituições parceiras", "instituicao",
        instituicoes.length ? frases(instituicoes) : vazio("Nenhuma instituição cadastrada nos autores."),
        m.instituicoes ? fmt(m.instituicoes) + " no mapa" : ""),
    ]),
  ]));
}

const ROTULO_DO_PASSO = { producao: "Produção nas bases", citacoes: "Citações", acervos: "Acervos" };

function slideComparacoes() {
  const t = tv();
  if (!t || !t.comparacoes) return escalonar(el("div", { class: "slide" }, vazio("Comparações ainda não calculadas.")));
  const comp = t.comparacoes;
  const mes_atual = ["—", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][comp.mes_atual] || "—";

  function deltaStatus(n) {
    if (n === 0) return "neutro";
    if (n > 0) return "bom";
    return "alerta";
  }

  const linha = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Publicações " + mes_atual, valor: comp.publicacoes.agora, icone: "publicacao", serie: 2,
      pastilha: deltaStatus(comp.publicacoes.delta), pe: "mês atual" }),
    tile({ nome: "Δ vs. mês anterior", valor: (comp.publicacoes.delta >= 0 ? "+" : "") + comp.publicacoes.delta,
      icone: comp.publicacoes.delta > 0 ? "subida" : "descida", serie: 3,
      pastilha: deltaStatus(comp.publicacoes.delta), pe: "variação percentual" }),
    tile({ nome: "Aceites " + mes_atual, valor: comp.aceites.agora, icone: "aceito", serie: 4,
      pastilha: deltaStatus(comp.aceites.delta), pe: "manuscritos aceitos" }),
    tile({ nome: "Taxa de aceite anual", valor: comp.taxa_aceite_anual + "%", icone: "porcentagem", serie: 7,
      pastilha: comp.taxa_aceite_anual > 50 ? "bom" : "ambar", pe: "aprovação total do ano" }),
  ]);

  const fatos = [
    { icone: "publicacao", tom: "bom", forte: "Publicações em " + mes_atual + ":",
      resto: comp.publicacoes.agora + (comp.publicacoes.delta !== 0 ? " (" + (comp.publicacoes.delta > 0 ? "+" : "") + comp.publicacoes.delta + ")" : "") },
    { icone: "aceito", tom: "bom", forte: "Aceites em " + mes_atual + ":",
      resto: comp.aceites.agora + (comp.aceites.delta !== 0 ? " (" + (comp.aceites.delta > 0 ? "+" : "") + comp.aceites.delta + ")" : "") },
    { icone: "porcentagem", tom: "neutro", forte: "Taxa de aceite anual:",
      resto: comp.taxa_aceite_anual + "% · " + (comp.taxa_aceite_anual > 50 ? "acima da meta" : "abaixo da meta") },
  ];

  return escalonar(el("div", { class: "slide" }, [
    linha,
    quadro("Métricas do mês", "subida", frases(fatos), "comparação com período anterior"),
  ]));
}

function slideAlertas() {
  const t = tv();
  if (!t || !t.alertas) return escalonar(el("div", { class: "slide" }, vazio("Alertas ainda não calculados.")));
  const ale = t.alertas;

  const linha = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Aceites últimos 7d", valor: ale.aceites_ultimos_7d, icone: "aceito", serie: 2, pastilha: "bom",
      pe: "manuscritos aceitos recentemente" }),
    tile({ nome: "Publicações recentes", valor: ale.pubs_recentes, icone: "publicacao", serie: 3, pastilha: "bom",
      pe: "saídos este ano" }),
    tile({ nome: "Revistas em processo", valor: ale.revistas_em_processo.length, icone: "revista", serie: 4, pastilha: "ambar",
      pe: "periódicos com múltiplos artigos" }),
    tile({ nome: "Dias sem submissão", valor: ale.dias_sem_submissao !== null ? ale.dias_sem_submissao : "—",
      icone: "relogio", serie: 7, pastilha: ale.dias_sem_submissao && ale.dias_sem_submissao > 7 ? "alerta" : "neutro",
      pe: "última tentativa de publicação" }),
  ]);

  const fatos = [];
  if (ale.aceites_ultimos_7d > 0) {
    fatos.push({ icone: "aceito", tom: "bom", forte: ale.aceites_ultimos_7d + " aceite" + (ale.aceites_ultimos_7d > 1 ? "s" : "") + " nos últimos 7 dias",
      resto: "Bom momento! Já foram para o prelo." });
  }
  if (ale.revistas_em_processo.length > 0) {
    fatos.push({ icone: "revista", tom: "neutro", forte: "Revistas em processo:",
      resto: ale.revistas_em_processo.slice(0, 3).join(", ") + (ale.revistas_em_processo.length > 3 ? " e mais" : "") });
  }
  if (ale.dias_sem_submissao && ale.dias_sem_submissao > 14) {
    fatos.push({ icone: "alerta", tom: "alerta", forte: "Sem submissões há " + ale.dias_sem_submissao + " dias",
      resto: "Considerar novos artigos para revisão e envio." });
  }

  return escalonar(el("div", { class: "slide" }, [
    linha,
    quadro("Eventos recentes", "alerta", fatos.length ? frases(fatos) : vazio("Nenhum alerta urgente."), "monitoramento contínuo"),
  ]));
}

function slideSazonalidade() {
  const t = tv();
  if (!t || !t.sazonalidade) return escalonar(el("div", { class: "slide" }, vazio("Sazonalidade ainda não calculada.")));
  const saz = t.sazonalidade;

  const linha = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Mês de pico (pub)", valor: saz.picos_publicacao[0] ? saz.picos_publicacao[0].mes : "—",
      icone: "calendario", serie: 2, pastilha: "bom", pe: "mais publicações" }),
    tile({ nome: "N publicações", valor: saz.picos_publicacao[0] ? saz.picos_publicacao[0].n : 0,
      icone: "publicacao", serie: 3, pastilha: "bom", pe: "no melhor mês" }),
    tile({ nome: "Mês de pico (aceite)", valor: saz.picos_aceite[0] ? saz.picos_aceite[0].mes : "—",
      icone: "aceito", serie: 4, pastilha: "ambar", pe: "mais aceitos" }),
    tile({ nome: "N aceites", valor: saz.picos_aceite[0] ? saz.picos_aceite[0].n : 0,
      icone: "aceito", serie: 7, pastilha: "ambar", pe: "no melhor mês" }),
  ]);

  const fatos = [];
  if (saz.picos_publicacao.length > 0) {
    const picos = saz.picos_publicacao.slice(0, 3).map(function (p) { return p.mes + " (" + p.n + ")"; }).join(", ");
    fatos.push({ icone: "calendario", tom: "bom", forte: "Sazonalidade de publicações:",
      resto: "picos em " + picos });
  }
  if (saz.picos_aceite.length > 0) {
    const picos = saz.picos_aceite.slice(0, 3).map(function (p) { return p.mes + " (" + p.n + ")"; }).join(", ");
    fatos.push({ icone: "aceito", tom: "neutro", forte: "Sazonalidade de aceites:",
      resto: "picos em " + picos });
  }

  return escalonar(el("div", { class: "slide" }, [
    linha,
    quadro("Padrões anuais", "calendario", fatos.length ? frases(fatos) : vazio("Nenhum padrão detectado."), "tendências por mês"),
  ]));
}

function slidePareto() {
  const t = tv();
  const linhas = (t && t.linhas || []).filter(function (l) { return (l.artigos || 0) > 0; });
  if (linhas.length < 3) return escalonar(el("div", { class: "slide" }, vazio("Poucas linhas com artigos para uma leitura 80/20.")));

  const dados = linhas
    .map(function (l) { return { nome: l.nome, valor: l.artigos }; })
    .sort(function (a, b) { return b.valor - a.valor; });

  const total = dados.reduce(function (s, d) { return s + d.valor; }, 0);
  let acumulado = 0, linhasAte80 = 0;
  for (let i = 0; i < dados.length; i++) {
    acumulado += dados[i].valor;
    if (acumulado / total <= 0.8 || linhasAte80 === 0) linhasAte80 = i + 1;
    if (acumulado / total > 0.8) break;
  }

  const fig = ChartsEnhanced.pareto(dados);
  const corpo = el("div", { class: "corpo" }, fig);

  return escalonar(el("div", { class: "slide painel-duplo igual" }, [
    quadro("Pareto: Produção por Linha (80/20)", "subida", corpo, null, "moldura-viva"),
    quadro("Leitura", "subida", frases([
      { icone: "subida", tom: "bom", forte: linhasAte80 + " de " + dados.length + " linha(s) somam 80% dos artigos",
        resto: "linha vermelha marca esse ponto de corte" },
      { icone: "publicacao", tom: "neutro", forte: dados[0].nome,
        resto: dados[0].valor + " artigo(s) — a linha mais produtiva" },
    ])),
  ]));
}

function slideSunburst() {
  const t = tv();
  if (!t || !t.mundo) return escalonar(el("div", { class: "slide" }, vazio("Sunburst ainda não disponível.")));

  const mundo = t.mundo;
  const top_paises = (mundo.paises || []).slice(0, 6).map(function (p) {
    return { nome: p.pais, valor: parseInt(p.n) || 1 };
  });

  if (!top_paises.length) {
    return escalonar(el("div", { class: "slide" }, vazio("Sem dados de países.")));
  }

  const fig = ChartsEnhanced.sunburst(top_paises, 150);
  const corpo = el("div", { class: "corpo" }, fig);

  return escalonar(el("div", { class: "slide painel-duplo igual" }, [
    quadro("Sunburst: Colaboração internacional", "mapa", corpo, null, "moldura-viva"),
    quadro("Top 6", "mapa", frases(top_paises.slice(0, 6).map(function (p, i) {
      return { icone: "mapa", tom: ["bom", "ambar", "neutro"][i % 3] || "neutro",
        forte: (i + 1) + ". " + p.nome, resto: p.valor + " artigos" };
    }))),
  ]));
}

function slideTernario() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Triangulação ainda não disponível.")));

  const dados = (window.triangulacao_data || []).slice(0, 10);
  if (!dados.length) {
    return escalonar(el("div", { class: "slide" }, vazio("Sem dados de triangulação (variáveis de pesquisa não configuradas).")));
  }

  const fig = ChartsEnhanced.ternario(dados);
  const corpo = el("div", { class: "corpo" }, fig);

  return escalonar(el("div", { class: "slide" }, [
    quadro("Triangulação: Aplicação × Intervenção × Desfecho", "experimento", corpo, "análise de 3 dimensões"),
  ]));
}

function slideArvoreDecisoes() {
  const t = tv();
  if (!t || !(t.linhas || []).length) return escalonar(el("div", { class: "slide" }, vazio("Linhas de pesquisa ainda não carregadas.")));

  const linhas = t.linhas.slice(0, 8);
  const raiz = el("div", { class: "arvore-decisoes" }, linhas.map(function(linha) {
    const artigos = linha.artigos || 0;
    const taxa = Math.round((linha.taxa_publicacao || 0) * 100);
    const cor = taxa >= 80 ? "bom" : (taxa >= 60 ? "ambar" : "alerta");

    return el("div", { class: "galho" }, [
      el("div", { class: "nodo", style: "--taxa:" + taxa + "%", "data-status": cor }, [
        Icons.badge("linhas", null, 24),
        el("div", { class: "dados" }, [
          el("strong", { text: linha.nome }),
          el("span", { text: artigos + " artigos" }),
          el("span", { text: taxa + "% publicados" }),
        ]),
      ]),
    ]);
  }));

  return escalonar(el("div", { class: "slide" }, [
    quadro("Árvore de Pesquisa", "linhas", raiz, "produtividade por linha (ramificações crescem com volume)"),
  ]));
}

function slideSankey() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados não disponíveis.")));

  /* As mesmas 5 fases do Framework de Pesquisa -- aqui como funil real
     (Charts.funnel, com dica ao passar o mouse e "% da etapa anterior"),
     em vez das 3 caixas antigas que nem chegavam a mostrar "aceito" e
     contavam "submetido" duas vezes (uma dentro de "em produção", outra
     sozinha). */
  const FASES = [
    { id: "em_producao", label: "Em Produção" },
    { id: "submetido", label: "Submetido" },
    { id: "em_revisao", label: "Em Revisão" },
    { id: "aceito", label: "Aceito" },
    { id: "publicado", label: "Publicado" },
  ];
  const contagem = {};
  FASES.forEach(function (f) { contagem[f.id] = 0; });
  let rejeitados = 0;
  artigos().forEach(function (a) {
    if (contagem.hasOwnProperty(a.status)) contagem[a.status]++;
    else if (a.status === "rejeitado" || a.status === "arquivado") rejeitados++;
  });

  const total = FASES.reduce(function (s, f) { return s + contagem[f.id]; }, 0);
  if (!total) return escalonar(el("div", { class: "slide" }, vazio("Nenhum artigo cadastrado ainda.")));

  const etapas = FASES.map(function (f) { return { label: f.label, value: contagem[f.id] }; });
  const grafico = C.funnel({ steps: etapas, unit: "artigos", height: 440, rowH: 78 });
  const corpo = el("div", { class: "corpo" }, grafico);

  const notas = [
    { icone: "processo", forte: total + " artigo(s) no fluxo", resto: "da escrita à publicação" },
  ];
  if (rejeitados > 0) {
    notas.push({ icone: "aviso", tom: "alerta", forte: rejeitados + " rejeitado(s) ou arquivado(s)",
      resto: "fora do fluxo principal" });
  }

  return escalonar(el("div", { class: "slide painel-duplo igual" }, [
    quadro("Fluxo de Publicação", "processo", corpo, "do conceito ao artigo publicado", "moldura-viva"),
    quadro("Leitura", "processo", frases(notas)),
  ]));
}

function slideRadarModular() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados não disponíveis.")));

  const hoje = new Date();
  const ano_atual = hoje.getFullYear();
  const mes_atual = hoje.getMonth() + 1;

  const publicados_ano = artigos().filter(function(a) {
    return a.year_published === ano_atual && a.status === "publicado";
  }).length;

  const em_producao = artigos().filter(function(a) {
    return a.status === "em_producao";
  }).length;

  const equipe = pessoas().filter(function(m) { return !m.is_external; }).length;
  const coautores = pessoas().filter(function(m) { return m.is_external; }).length;

  const modulos = el("div", { class: "radar-modular" }, [
    el("div", { class: "modulo", "data-tipo": "kpi" }, [
      el("div", { class: "icone-grande" }, Icons.badge("producao", null, 48)),
      el("div", { class: "valor", text: publicados_ano }),
      el("div", { class: "descricao", text: "Publicados em " + ano_atual }),
    ]),
    el("div", { class: "modulo", "data-tipo": "alerta" }, [
      el("div", { class: "icone-grande" }, Icons.badge("relogio", null, 48)),
      el("div", { class: "valor", text: em_producao }),
      el("div", { class: "descricao", text: "Em produção agora" }),
    ]),
    el("div", { class: "modulo", "data-tipo": "team" }, [
      el("div", { class: "icone-grande" }, Icons.badge("pessoas", null, 48)),
      el("div", { class: "valor", text: equipe }),
      el("div", { class: "descricao", text: "Pesquisadores LAPE" }),
    ]),
    el("div", { class: "modulo", "data-tipo": "team" }, [
      el("div", { class: "icone-grande" }, Icons.badge("pessoas", null, 48)),
      el("div", { class: "valor", text: coautores }),
      el("div", { class: "descricao", text: "Coautores externos" }),
    ]),
  ]);

  return escalonar(el("div", { class: "slide" }, [
    quadro("Indicadores Principais", "painel", modulos, "4 métricas centrais do laboratório"),
  ]));
}

function slideHeatmapTimeline() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Dados não disponíveis.")));

  const hoje = new Date();
  const ano_atual = hoje.getFullYear();
  const meses_ext = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

  const atividade_por_mes = Array(12).fill(0);
  artigos().forEach(function(a) {
    if (a.year_published === ano_atual && a.published_on) {
      const mes = new Date(a.published_on).getMonth();
      atividade_por_mes[mes]++;
    }
  });

  const max_atividade = Math.max.apply(null, atividade_por_mes) || 1;

  const timeline = el("div", { class: "heatmap-timeline" }, [
    el("div", { class: "linha-temporal" }, meses_ext.map(function(mes, idx) {
      const valor = atividade_por_mes[idx];
      const intensidade = Math.round(valor * 100 / max_atividade);
      const status = valor === 0 ? "vazio" : (intensidade >= 80 ? "quente" : (intensidade >= 50 ? "morno" : "frio"));

      return el("div", { class: "celula", "data-status": status, style: "--intensidade:" + intensidade + "%" }, [
        el("div", { class: "mes", text: mes }),
        el("div", { class: "num", text: valor || "—" }),
      ]);
    })),
  ]);

  return escalonar(el("div", { class: "slide" }, [
    quadro("Atividade Temporal", "calendario", timeline, "artigos publicados por mês (intensidade visual)"),
  ]));
}

function slideAcervos() {
  const t = tv();
  if (!t) return escalonar(el("div", { class: "slide" }, vazio("Os acervos ainda não chegaram.")));
  const acervos = t.acervos || [];
  const registros = acervos.reduce(function (a, b) { return a + (b.total || 0); }, 0);
  const segmentos = acervos.reduce(function (a, b) { return a + (b.segmentos || 0); }, 0);
  const rodados = acervos.filter(function (a) { return a.rodada_em; });
  const ultima = rodados.length ? rodados.map(function (a) { return a.rodada_em; }).sort().pop() : null;
  const linha = el("div", { class: "linha-kpi" }, [
    tile({ nome: "Acervos", valor: acervos.length, icone: "livro", serie: 1, pe: "bibliotecas temáticas abertas" }),
    tile({ nome: "Registros", valor: registros, icone: "producao", serie: 3, pastilha: "bom", pe: "artigos lidos das bases" }),
    tile({ nome: "Segmentos", valor: segmentos, icone: "linhas", serie: 4, pastilha: "ambar", pe: "recortes de leitura" }),
    tile({ nome: "Última rodada", valor: ultima ? haQuanto(diasAte(ultima)) : "—", icone: "relogio", serie: 7, pastilha: "violeta",
      pe: ultima ? dataCurta(ultima) : "nenhuma busca rodou ainda" }),
  ]);
  const CABEM = 8;
  const tabela = acervos.length ? el("table", { class: "placar" }, [
    el("thead", {}, el("tr", {}, [el("th", { text: "Acervo" }), el("th", { text: "Registros" }),
      el("th", { text: "Segmentos" }), el("th", { text: "Bases" })])),
    el("tbody", {}, acervos.slice(0, CABEM).map(function (a) {
      return el("tr", {}, [
        el("td", {}, el("div", { class: "quem" }, [Icons.badge("livro", null, 22), el("span", { text: cortar(a.title, 40) })])),
        el("td", { text: fmt(a.total) }), el("td", { text: fmt(a.segmentos) }),
        el("td", { text: a.bases ? a.bases_ok + " de " + a.bases + " ok" : "—" }),
      ]);
    })),
  ]) : vazio("Nenhum acervo instalado.");

  const r = t.rotina || {};
  const passos = (r.passos || []).map(function (p) {
    const tom = p.status === "erro" ? "critico" : (p.vencido ? "alerta" : (p.ultima_boa ? "bom" : "azul"));
    const quando = p.ultima_boa ? "rodou " + haQuanto(diasAte(p.ultima_boa))
      + (p.trouxe !== null && p.trouxe !== undefined ? " e trouxe " + fmt(p.trouxe) : "") : "ainda não rodou";
    const proxima = p.proxima ? " · volta " + porExtenso(diasAte(p.proxima)) : "";
    return { icone: "processo", tom: tom, forte: (ROTULO_DO_PASSO[p.passo] || p.rotulo || p.passo) + ":",
      resto: quando + " · a cada " + p.intervalo_h + " h" + proxima + (p.status === "erro" && p.mensagem ? " · " + cortar(p.mensagem, 60) : "") };
  });
  passos.unshift({ icone: r.ligada ? "tocar" : "pausa", tom: r.ligada ? "bom" : "alerta",
    forte: r.ligada ? "Rotina ligada:" : "Rotina desligada:",
    resto: r.ligada ? "produção e citações a cada dia, acervos a cada semana, sem ninguém apertar botão."
      : "os passos só rodam quando alguém pede na área do integrante." });

  return escalonar(el("div", { class: "slide" }, [
    linha,
    el("div", { class: "painel-duplo igual" }, [
      quadro("Cada acervo", "livro", tabela, acervos.length > CABEM ? "e mais " + (acervos.length - CABEM) : ""),
      quadro("Rotina automática", "processo", frases(passos), r.ligada ? "ligada" : "desligada"),
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
/* `apresenta` é a frase que fica embaixo do título enquanto a tela está
   na parede: diz o que se está vendo, para quem chegou agora. É texto
   de apresentação, e não leitura dos dados. */
const SLIDES = [
  { id: "agora", titulo: "Agora no laboratório", icone: "painel", montar: slideAgora,
    apresenta: "Os números de hoje: publicados, em produção, em avaliação, aceitos, citações e a equipe — e a produção ano a ano." },
  { id: "bancada", titulo: "Na bancada", icone: "experimento", montar: slideBancada,
    apresenta: "O que está sendo medido agora: coletas em andamento, participantes e instrumentos." },
  { id: "citados", titulo: "Citações e produção por área", icone: "citacao", montar: slideCitados,
    apresenta: "Quanto o acervo é citado em cada base, e como a produção se reparte pelas linhas de pesquisa." },
  { id: "agenda", titulo: "O que vem a seguir", icone: "calendario", montar: slideAgenda,
    apresenta: "Defesas, reuniões, cursos e visitas nos próximos dias, na ordem em que acontecem." },
  { id: "prazos", titulo: "Prazos e pendências", icone: "prazo", montar: slidePrazos,
    apresenta: "Datas de defesa, fim de projeto e de bolsa, e manuscritos parados há muito tempo com a revista." },
  { id: "destaques", titulo: "Nossa equipe", icone: "pessoas", montar: slideDestaques,
    apresenta: "Quem faz o laboratório: nome, vínculo e a linha em que cada pessoa trabalha." },
  /* As quatro da TV: só entram no ciclo quando `D.tv` chegou. */
  { id: "temas", titulo: "Temas e indicadores", icone: "achado", montar: slideTemas, tv: true,
    apresenta: "O que os quatro números não contam: quanto tempo leva publicar, quanto é aceito, quanto é aberto, com quem se publica e onde." },
  { id: "ritmo", titulo: "Ritmo da produção", icone: "subida", montar: slideRitmo, tv: true,
    apresenta: "A curva mensal lida com cálculo: o ritmo, a deriva por ano, a tendência com a faixa de confiança e o que os próximos seis meses devem trazer." },
  { id: "mundo", titulo: "Pelo mundo", icone: "mapa", montar: slideMundo, tv: true,
    apresenta: "Os países que assinam com o laboratório e as instituições parceiras, por número de artigos." },
  { id: "acervos", titulo: "Acervos e rotina", icone: "livro", montar: slideAcervos, tv: true,
    apresenta: "As bibliotecas temáticas: quantos registros, em quantos segmentos, e a rotina que as atualiza sozinha." },
  { id: "alertas", titulo: "Alertas e eventos", icone: "alerta", montar: slideAlertas, tv: true,
    apresenta: "Aceites recentes, revistas em processo, e dias desde a última submissão." },
  { id: "sazonalidade", titulo: "Padrões anuais", icone: "calendario", montar: slideSazonalidade, tv: true,
    apresenta: "Sazonalidade detectada: meses de pico para publicações e aceites." },
  { id: "pareto", titulo: "Análise Pareto", icone: "subida", montar: slidePareto, tv: true,
    apresenta: "Regra 80/20: onde o maior impacto vem de menos esforço. Linha vermelha marca o ponto crítico." },
  { id: "sunburst", titulo: "Colaboração global", icone: "mapa", montar: slideSunburst, tv: true,
    apresenta: "Hierarquia radial mostrando os 6 países principais com maior número de artigos colaborativos." },
  { id: "arvore", titulo: "Árvore de Pesquisa", icone: "linhas", montar: slideArvoreDecisoes, tv: true,
    apresenta: "Ramificações crescentes: cada linha de pesquisa como um galho, com produtividade e taxa de publicação." },
  { id: "sankey", titulo: "Fluxo de Publicação", icone: "processo", montar: slideSankey, tv: true,
    apresenta: "Funil da escrita à publicação: quantos artigos estão em cada uma das cinco fases, e que fração passa de uma para a próxima." },
  { id: "radar", titulo: "Indicadores Principais", icone: "painel", montar: slideRadarModular, tv: true,
    apresenta: "4 métricas centrais em grande escala: artigos publicados este ano, em produção, equipe LAPE e coautores." },
  { id: "heatmap", titulo: "Atividade Temporal", icone: "calendario", montar: slideHeatmapTimeline, tv: true,
    apresenta: "Mapa de calor dos 12 meses: meses mais quentes significam mais artigos publicados naquele período." },
  /* Slides 3D avançados com gráficos interativos e animações */
  { id: "linhas-3d", titulo: "Linhas de Pesquisa 3D", icone: "linhas", montar: slidePesquisasLinhas3D, tv: true,
    apresenta: "Árvore radial 3D mostrando cada linha de pesquisa com volume de artigos, taxa de publicação e colaborações." },
  { id: "organograma", titulo: "Organograma da Equipe", icone: "pessoas", montar: slideOrganograma3D, tv: true,
    apresenta: "Hierarquia visual com indicador de 'ponto' em tempo real: quem está presente agora, ausente, ou online." },
  { id: "framework", titulo: "Framework de Pesquisa", icone: "processo", montar: slideFrameworkN8n, tv: true,
    apresenta: "Fluxo estilo n8n: em produção → submetido → em revisão → aceito → publicado, com o gargalo real destacado." },
  { id: "kpis-analytics", titulo: "KPIs Analíticos 4K", icone: "painel", montar: slideKPIsAnalyticos, tv: true,
    apresenta: "4 métricas centrais em grande escala: taxa de aceite, dias até publicação, citações/artigo, produtividade equipe." },
  { id: "citacoes-bases", titulo: "Citações em Tempo Real", icone: "citacao", montar: slideCitacoesBases, tv: true,
    apresenta: "Citações sincronizadas com OpenAlex (e Scopus/Web of Science quando configuradas): total, média por linha de pesquisa e os artigos mais citados." },
];

/* As paletas de fundo, as mesmas do ao vivo. A escolha é lida de
   `?paleta=` ou de `lape-paleta` no navegador -- que é onde o ao vivo
   grava a dele: quem escolhe lá escolhe aqui. `?paleta=claro` volta ao
   tema claro da casa. */
const PALETAS = [
  ["marinho", "Marinho", "#0b1533"], ["aurora", "Aurora", "#1d1440"], ["oceano", "Oceano", "#0a3140"],
  ["grafite", "Grafite", "#1a1e28"], ["brasa", "Brasa", "#2f170e"], ["claro", "Claro", "#f4f6fb"],
];
function paletaEscolhida() {
  const pedida = (PARAMS.get("paleta") || "").trim();
  if (pedida) return pedida;
  let guardada = null;
  try { guardada = localStorage.getItem("lape-paleta"); } catch (e) { /* janela privada */ }
  return guardada || "marinho";
}
function aplicarPaleta(code) {
  const raiz = document.documentElement;
  if (!PALETAS.some(function (p) { return p[0] === code; })) code = "marinho";
  if (code === "claro") { raiz.removeAttribute("data-paleta"); raiz.setAttribute("data-theme", "light"); }
  else { raiz.setAttribute("data-paleta", code); raiz.setAttribute("data-theme", "dark"); }
  try { localStorage.setItem("lape-paleta", code); } catch (e) { /* ignora */ }
  const casa = document.getElementById("paletas");
  if (!casa) return;
  casa.textContent = "";
  PALETAS.forEach(function (p) {
    casa.appendChild(el("button", { type: "button", title: p[1], "aria-label": "Paleta " + p[1],
      class: p[0] === code ? "on" : "", style: "--amostra:" + p[2],
      onclick: function () { aplicarPaleta(p[0]); } }));
  });
}

/* ?slides=agora,prazos escolhe quais telas entram no ciclo */
function ciclo() {
  const disponiveis = SLIDES.filter(function (s) { return !s.tv || D.tv; });
  const pedido = (PARAMS.get("slides") || "").split(",").map(function (s) { return s.trim(); })
    .filter(Boolean);
  if (!pedido.length) return disponiveis;
  const escolhidos = pedido.map(function (id) {
    return disponiveis.find(function (s) { return s.id === id; });
  }).filter(Boolean);
  return escolhidos.length ? escolhidos : disponiveis;
}
const ROTEIRO = ciclo();   /* o ciclo de partida; `refazerRoteiro` o troca quando a TV chega */

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
  /* Marca TODOS os filhos atuais para sair, não só o primeiro -- se a troca
     de slide acontecer mais rápido que os 320ms da animação (cliques
     seguidos nos pontos), sobras que ficaram para trás também são
     removidas aqui, em vez de se acumularem escondidas atrás do slide
     novo para sempre. */
  Array.from(palco.children).forEach(function (antigo) {
    antigo.classList.add("saindo");
    setTimeout(function () { if (antigo.parentNode) antigo.remove(); }, 320);
  });
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
  const apresenta = document.getElementById("apresenta");
  if (apresenta) apresenta.textContent = slide.apresenta || "";
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
    if (node.dataset.alvo === undefined) return;   /* azulejo de texto */
    const alvo = Number(node.dataset.alvo) || 0;
    const sufixo = node.dataset.sufixo || "";
    const prefixo = node.dataset.prefixo || "";
    const decimais = Number(node.dataset.decimais) || 0;
    /* com decimais o número é escrito como no país: vírgula, não ponto */
    const escreve = function (v) {
      return prefixo + (decimais ? v.toFixed(decimais).replace(".", ",") : fmt(Math.round(v))) + sufixo;
    };
    if (lento || alvo === 0) { node.textContent = escreve(alvo); return; }
    const duracao = 900;
    const partida = performance.now();
    (function passo(agora) {
      const t = Math.min(1, (agora - partida) / duracao);
      const suave = 1 - Math.pow(1 - t, 3);
      node.textContent = escreve(alvo * suave);
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

/* Sem atualização automática por propósito: os dados só mudam quando a
   página é recarregada (F5) por quem está de frente para o computador
   ligado na TV -- ninguém mais tem esse acesso, então o mural nunca
   troca o que está mostrando sozinho, mesmo que o banco mude enquanto
   ele gira as telas. */

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
  aplicarPaleta(paletaEscolhida());
  const seguir = document.getElementById("seguir");
  if (seguir) {
    seguir.textContent = "";
    seguir.appendChild(document.createTextNode("Seguir "));
    seguir.appendChild(Icons.get("proximo", 15));
    seguir.onclick = function () { avancar(1); };
  }
  desenharControles();
  desenhar(0);
}
comecar();
