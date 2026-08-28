/* Triagem de revisão sistemática.
 *
 * A regra que governa este arquivo: nunca fazer a pessoa esperar. Numa
 * revisão de 3.000 referências, meio segundo de espera por decisão são
 * 25 minutos olhando para uma tela parada. Por isso:
 *
 *   - a fila vem em bloco e fica na memória;
 *   - a decisão é aplicada na tela na hora e enviada depois, em fundo;
 *   - se o envio falhar, a decisão volta para a fila e a pessoa é avisada
 *     -- decisão perdida em silêncio seria pior que a espera.
 *
 * Desfazer existe porque a mão erra quando o ritmo é alto, e sem desfazer
 * a pessoa desacelera por medo. */

const ESTADO = {
  revisao: null, etapa: "titulo_resumo", aba: "triar", extraindo: null,
  fila: [], indice: 0, motivos: [], termos: [],
  faltam: 0, jaTriei: 0, eu: null,
  pendentes: [], ultima: null, comecou: null, feitasAgora: 0,
};

async function api(caminho, metodo, corpo) {
  const resposta = await fetch(caminho, {
    method: metodo || "GET",
    headers: corpo ? { "Content-Type": "application/json" } : {},
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  if (resposta.status === 401) {
    location.href = "/entrar?next=/triagem";
    throw new Error("sessão expirada");
  }
  const dados = await resposta.json().catch(function () { return {}; });
  if (!resposta.ok) throw new Error(dados.error || ("erro " + resposta.status));
  return dados;
}

function el(tag, props, filhos) {
  const node = document.createElement(tag);
  Object.entries(props || {}).forEach(function (par) {
    const [chave, valor] = par;
    if (valor === null || valor === undefined || valor === false) return;
    if (chave === "text") node.textContent = valor;
    else if (chave === "html") node.innerHTML = valor;
    else if (chave.startsWith("on")) node[chave.toLowerCase()] = valor;
    else node.setAttribute(chave, valor === true ? "" : valor);
  });
  (Array.isArray(filhos) ? filhos : filhos ? [filhos] : []).forEach(function (filho) {
    if (filho === null || filho === undefined) return;
    node.appendChild(typeof filho === "string" ? document.createTextNode(filho) : filho);
  });
  return node;
}

function aviso(texto, acao) {
  const caixa = document.getElementById("aviso");
  caixa.innerHTML = "";
  caixa.appendChild(el("span", { text: texto }));
  if (acao) caixa.appendChild(el("button", { text: acao.rotulo, onclick: acao.fazer }));
  caixa.classList.add("on");
  clearTimeout(aviso._t);
  aviso._t = setTimeout(function () { caixa.classList.remove("on"); }, acao ? 7000 : 2600);
}

/* -------------------------------------------------------------- realce */
function escapar(texto) {
  return String(texto === null || texto === undefined ? "" : texto)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* O olho acha em um segundo o que a leitura inteira levaria para achar.
   O texto é escapado ANTES de qualquer marcação: título de artigo com
   `<` existe, e um resumo não pode virar HTML. */
function realcar(texto, termos) {
  let saida = escapar(texto);
  (termos || []).forEach(function (t) {
    const alvo = String(t.term || "").trim();
    if (alvo.length < 2) return;
    const padrao = new RegExp("(" + alvo.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
    const classe = t.tone === "excluir" ? "t-exc" : "t-inc";
    saida = saida.replace(padrao, '<mark class="' + classe + '">$1</mark>');
  });
  return saida;
}

/* -------------------------------------------------------------- decidir */
function atual() { return ESTADO.fila[ESTADO.indice] || null; }

function decidir(decisao, motivoId) {
  const ref = atual();
  if (!ref) return;
  const segundos = ESTADO.comecou ? (Date.now() - ESTADO.comecou) / 1000 : null;
  const pendente = {
    ref_id: ref.id, decisao: decisao, motivo_id: motivoId || null,
    segundos: segundos ? Math.round(segundos * 10) / 10 : null,
  };
  ESTADO.ultima = { pendente: pendente, indice: ESTADO.indice, ref: ref };
  ESTADO.pendentes.push(pendente);
  ESTADO.indice += 1;
  ESTADO.faltam = Math.max(0, ESTADO.faltam - 1);
  ESTADO.jaTriei += 1;
  ESTADO.feitasAgora += 1;
  desenhar();
  enviarPendentes();
  if (ESTADO.fila.length - ESTADO.indice <= 8) carregarFila(true);
}

let enviando = false;
async function enviarPendentes() {
  if (enviando || !ESTADO.pendentes.length) return;
  enviando = true;
  const lote = ESTADO.pendentes.splice(0, ESTADO.pendentes.length);
  try {
    await api("/api/revisoes/" + ESTADO.revisao.code + "/decidir", "POST",
              { decisoes: lote });
  } catch (erro) {
    // devolve o lote para a fila de envio: decisão que some sem ninguém
    // ver é o pior defeito possível num sistema de triagem
    ESTADO.pendentes = lote.concat(ESTADO.pendentes);
    aviso("Não consegui gravar " + lote.length + " decisão(ões). Tentando de novo…");
    setTimeout(function () { enviando = false; enviarPendentes(); }, 3000);
    return;
  } finally {
    if (!ESTADO.pendentes.length) enviando = false;
  }
  enviando = false;
  if (ESTADO.pendentes.length) enviarPendentes();
}

function desfazer() {
  if (!ESTADO.ultima) { aviso("Nada para desfazer"); return; }
  const { pendente, indice } = ESTADO.ultima;
  const naFila = ESTADO.pendentes.indexOf(pendente);
  if (naFila >= 0) ESTADO.pendentes.splice(naFila, 1);
  ESTADO.indice = indice;
  ESTADO.faltam += 1;
  ESTADO.jaTriei = Math.max(0, ESTADO.jaTriei - 1);
  ESTADO.feitasAgora = Math.max(0, ESTADO.feitasAgora - 1);
  ESTADO.ultima = null;
  desenhar();
  // Se já tinha ido para o servidor, a decisão continua lá: o desfazer
  // aqui volta a referência para a fila, e a próxima decisão sobrescreve
  // a anterior (a triagem é uma linha por pessoa e referência).
  aviso("Desfeito — decida de novo");
}

/* -------------------------------------------------------------- desenho */
function desenhar() {
  const palco = document.getElementById("palco");
  palco.innerHTML = "";
  desenharAbas();
  if (!ESTADO.revisao) return desenharEscolha(palco);
  if (ESTADO.aba === "conflitos") return desenharConflitos(palco);
  if (ESTADO.aba === "duplicados") return desenharDuplicados(palco);
  if (ESTADO.aba === "extracao") return desenharExtracao(palco);
  if (ESTADO.aba === "prisma") return desenharPrisma(palco);
  if (ESTADO.aba === "importar") return desenharImportar(palco);
  desenharTriagem(palco);
}

function desenharAbas() {
  const barra = document.getElementById("abas");
  barra.innerHTML = "";
  if (!ESTADO.revisao) return;
  document.getElementById("qual").textContent = ESTADO.revisao.title;
  [["triar", "Triar"], ["conflitos", "Conflitos"], ["duplicados", "Duplicados"],
   ["extracao", "Extração"], ["prisma", "PRISMA"],
   ["importar", "Importar"]].forEach(function (par) {
    barra.appendChild(el("button", {
      text: par[1], class: ESTADO.aba === par[0] ? "on" : "",
      onclick: function () { ESTADO.aba = par[0]; desenhar(); },
    }));
  });
}

function desenharTriagem(palco) {
  const ref = atual();
  const total = ESTADO.faltam + ESTADO.jaTriei;
  const feito = total ? (ESTADO.jaTriei / total) * 100 : 0;
  palco.appendChild(el("div", { class: "andar" }, [
    el("div", { class: "barra" }, el("i", { style: "width:" + feito.toFixed(1) + "%" })),
    el("div", { class: "n", html: "<b>" + ESTADO.faltam + "</b> a triar" }),
    el("div", { class: "n", html: "<b>" + ESTADO.jaTriei + "</b> feitas" }),
    ritmo() ? el("div", { class: "n", html: ritmo() }) : null,
  ]));

  if (!ref) {
    palco.appendChild(el("div", { class: "vazio" }, [
      Icons.get("aceite", null),
      el("h3", { text: ESTADO.jaTriei ? "Fila vazia — você triou tudo" : "Nada para triar" }),
      el("p", { text: ESTADO.jaTriei
        ? "Sua parte desta etapa está feita. Veja os conflitos ou o PRISMA."
        : "Importe as buscas das bases para começar." }),
      el("div", { style: "margin-top:18px;display:flex;gap:9px;justify-content:center" }, [
        el("button", { text: "Ver conflitos",
          onclick: function () { ESTADO.aba = "conflitos"; desenhar(); } }),
        el("button", { text: "Importar buscas",
          onclick: function () { ESTADO.aba = "importar"; desenhar(); } }),
      ]),
    ]));
    return;
  }

  ESTADO.comecou = Date.now();
  const fonte = [ref.journal, ref.year, ref.pub_type].filter(Boolean).join(" · ");
  const cartao = el("div", { class: "ref" }, [
    el("div", { class: "meta" }, [
      ref.doi ? el("span", { class: "badge", text: "DOI" }) : null,
      ref.pmid ? el("span", { class: "badge", text: "PubMed" }) : null,
      ref.language ? el("span", { class: "badge", text: ref.language }) : null,
      ref.notes ? el("span", { class: "badge", text: ref.notes }) : null,
    ]),
    el("h2", { html: realcar(ref.title, ESTADO.termos) }),
    ref.authors ? el("div", { class: "autores", text: ref.authors }) : null,
    fonte ? el("div", { class: "fonte", text: fonte }) : null,
    ref.abstract
      ? el("div", { class: "resumo", html: realcar(ref.abstract, ESTADO.termos) })
      : el("div", { class: "sem-resumo", text:
          "Sem resumo neste registro — decida pelo título, ou abra o artigo (A)." }),
    el("div", { class: "fora" }, destinos(ref)),
  ]);
  palco.appendChild(cartao);

  palco.appendChild(el("div", { class: "decidir" }, [
    botao("incluir", "Incluir", "I", function () { decidir("incluir"); }),
    botao("excluir", "Excluir", "E", function () { abrirMotivos(); }),
    botao("talvez", "Talvez", "T", function () { decidir("talvez"); }),
    el("button", { class: "ghost", onclick: desfazer }, [
      el("span", { class: "tecla", text: "Z" }), el("span", { text: "Desfazer" })]),
  ]));
  palco.appendChild(el("div", { id: "motivos" }));
}

function botao(classe, rotulo, tecla, aoClicar) {
  return el("button", { class: classe, onclick: aoClicar }, [
    el("span", { class: "tecla", text: tecla }), el("span", { text: rotulo })]);
}

function destinos(ref) {
  const links = [];
  if (ref.doi) links.push({ rotulo: "Abrir o artigo (A)", url: "https://doi.org/" + encodeURI(ref.doi) });
  else if (ref.url) links.push({ rotulo: "Abrir o artigo (A)", url: ref.url });
  if (ref.pmid) links.push({ rotulo: "PubMed", url: "https://pubmed.ncbi.nlm.nih.gov/" + ref.pmid + "/" });
  if (!links.length && ref.title) {
    links.push({ rotulo: "Procurar o título (A)",
      url: "https://scholar.google.com/scholar?q=" + encodeURIComponent('"' + ref.title + '"') });
  }
  return links.map(function (d) {
    return el("a", { class: "botao-destino", href: d.url, target: "_blank",
      rel: "noopener", text: d.rotulo });
  });
}

function abrirMotivos() {
  const caixa = document.getElementById("motivos");
  if (!caixa) return;
  if (!ESTADO.motivos.length) { decidir("excluir"); return; }
  if (caixa.dataset.aberto === "1") { decidir("excluir"); return; }
  caixa.dataset.aberto = "1";
  caixa.innerHTML = "";
  caixa.appendChild(el("div", { class: "motivos" }, [
    el("h4", { text: "Por que excluir? (o PRISMA pede o motivo)" }),
    el("div", { class: "lista" }, ESTADO.motivos.slice(0, 9).map(function (m, i) {
      return el("button", { onclick: function () { decidir("excluir", m.id); } }, [
        el("span", { class: "tecla", text: String(i + 1) }),
        el("span", { text: m.label })]);
    }).concat([
      el("button", { class: "ghost", text: "Sem motivo (E de novo)",
        onclick: function () { decidir("excluir"); } }),
    ])),
  ]));
}

function ritmo() {
  if (ESTADO.feitasAgora < 3 || !ESTADO.sessaoInicio) return null;
  const minutos = (Date.now() - ESTADO.sessaoInicio) / 60000;
  if (minutos < 0.5) return null;
  const porHora = Math.round((ESTADO.feitasAgora / minutos) * 60);
  const faltamMin = porHora ? Math.round((ESTADO.faltam / porHora) * 60) : null;
  return "<b>" + porHora + "</b>/h" +
    (faltamMin !== null && ESTADO.faltam ? " · faltam ~" + humano(faltamMin) : "");
}

function humano(minutos) {
  if (minutos < 60) return minutos + " min";
  const horas = Math.floor(minutos / 60);
  return horas + " h" + (minutos % 60 ? " " + (minutos % 60) + " min" : "");
}

/* -------------------------------------------------------------- conflitos */
async function desenharConflitos(palco) {
  palco.appendChild(el("p", { class: "hint", text:
    "Onde a equipe divergiu. Aqui — e só aqui — os votos aparecem com nome: "
    + "até haver conflito, a triagem é às cegas." }));
  const alvo = el("div", {});
  palco.appendChild(alvo);
  let dados;
  try {
    dados = await api("/api/revisoes/" + ESTADO.revisao.code + "/conflitos");
  } catch (erro) { alvo.appendChild(el("p", { class: "note erro", text: erro.message })); return; }
  if (!dados.conflitos.length) {
    alvo.appendChild(el("div", { class: "vazio" }, [
      Icons.get("aceite", null), el("h3", { text: "Sem conflitos" }),
      el("p", { text: "Nenhuma divergência pendente nesta etapa." })]));
    return;
  }
  dados.conflitos.forEach(function (c) {
    alvo.appendChild(el("div", { class: "conflito" }, [
      el("h3", { text: c.title }),
      el("div", { class: "hint", text: [c.journal, c.year].filter(Boolean).join(" · ") }),
      el("div", { class: "votos" }, c.votos.map(function (v) {
        return el("div", { class: "voto" }, [
          el("b", { text: v.quem }),
          el("span", { class: "d-" + v.decision, text: rotuloDecisao(v.decision) }),
          v.motivo ? el("div", { class: "hint", text: v.motivo }) : null,
          v.notes ? el("div", { class: "hint", text: v.notes }) : null,
        ]);
      })),
      c.abstract ? el("details", {}, [
        el("summary", { text: "Ver o resumo" }),
        el("div", { class: "resumo", style: "margin-top:10px",
          html: realcar(c.abstract, ESTADO.termos) })]) : null,
      el("div", { class: "decidir" }, [
        el("button", { class: "incluir", text: "Incluir",
          onclick: function () { arbitrar(c.id, "incluir"); } }),
        el("button", { class: "excluir", text: "Excluir",
          onclick: function () { arbitrar(c.id, "excluir"); } }),
      ]),
    ]));
  });
}

function rotuloDecisao(d) {
  return { incluir: "Incluir", excluir: "Excluir", talvez: "Talvez" }[d] || d;
}

async function arbitrar(refId, decisao) {
  try {
    await api("/api/revisoes/" + ESTADO.revisao.code + "/arbitrar", "POST",
              { ref_id: refId, decisao: decisao });
    aviso("Arbitrado: " + rotuloDecisao(decisao));
    desenhar();
  } catch (erro) { aviso(erro.message); }
}

/* -------------------------------------------------------------- duplicados */
/* União automática erra dos dois lados: juntar dois estudos diferentes
   esconde um deles, e deixar de juntar o mesmo estudo faz a equipe ler o
   mesmo resumo duas vezes e infla o PRISMA. Os dois erros são invisíveis
   se ninguém puder olhar — por isso a união fica exposta, com a evidência
   do que casou, e dá para desfazer. */
async function desenharDuplicados(palco) {
  const alvo = el("div", {});
  palco.appendChild(alvo);
  let dados;
  try {
    dados = await api("/api/revisoes/" + ESTADO.revisao.code + "/duplicados");
  } catch (erro) { alvo.appendChild(el("p", { class: "note erro", text: erro.message })); return; }

  alvo.appendChild(el("p", { class: "hint", text:
    "O que o sistema juntou, e por quê. Se juntou errado, separe: o registro "
    + "volta a valer por si e entra na fila de triagem." }));

  if (!dados.unidos.length) {
    alvo.appendChild(el("div", { class: "note info", style: "margin-top:12px",
      text: "Nenhum registro repetido entre as buscas até agora." }));
  }
  dados.unidos.forEach(function (g) {
    alvo.appendChild(el("div", { class: "conflito" }, [
      el("h3", { text: g.ficou.title }),
      el("div", { class: "hint", text: [g.ficou.journal, g.ficou.year, g.ficou.origem]
        .filter(Boolean).join(" · ") + " — este ficou" }),
      el("div", { class: "votos" }, g.repetidos.map(function (r) {
        return el("div", { class: "voto" }, [
          el("b", { text: r.origem || "sem base" }),
          el("div", { text: cortar(r.title, 70) }),
          el("div", { class: "hint", text: "casou por " + r.casou_por }),
          el("button", { class: "ghost", text: "Separar",
            onclick: function () { separar(r.id); } }),
        ]);
      })),
    ]));
  });

  if (dados.suspeitas.length) {
    alvo.appendChild(el("h3", { style: "margin:26px 0 6px", text: "Parecidos, mas não unidos" }));
    alvo.appendChild(el("p", { class: "hint", text:
      "A união exige título idêntico; a realidade traz subtítulo cortado, erro "
      + "de digitação e o mesmo estudo com o ano do online e o do impresso. "
      + "Nada aqui foi unido sozinho — quem decide é quem está lendo." }));
    dados.suspeitas.forEach(function (s) {
      alvo.appendChild(el("div", { class: "conflito" }, [
        el("div", { class: "hint", text: "semelhança " + Math.round(s.semelhanca * 100) + "%" }),
        el("div", { class: "votos" }, [s.a, s.b].map(function (r) {
          return el("div", { class: "voto" }, [
            el("b", { text: r.origem || "sem base" }),
            el("div", { text: cortar(r.title, 80) }),
            el("div", { class: "hint", text: [r.journal, r.year, r.doi]
              .filter(Boolean).join(" · ") }),
          ]);
        })),
        el("div", { class: "decidir" }, [
          el("button", { text: "São o mesmo — unir",
            onclick: function () { unir(s.b.id, s.a.id); } }),
          el("button", { class: "ghost", text: "São diferentes — deixar como está",
            onclick: function (ev) { ev.target.closest(".conflito").remove(); } }),
        ]),
      ]));
    });
  }
}

function cortar(texto, n) {
  const t = String(texto || "");
  return t.length > n ? t.slice(0, n - 1) + "…" : t;
}

async function separar(refId) {
  try {
    await api("/api/revisoes/" + ESTADO.revisao.code + "/duplicados", "POST",
              { ref_id: refId });
    aviso("Separado — voltou para a fila");
    desenhar();
  } catch (erro) { aviso(erro.message); }
}

async function unir(refId, alvoId) {
  try {
    await api("/api/revisoes/" + ESTADO.revisao.code + "/duplicados", "POST",
              { ref_id: refId, unir_a: alvoId });
    aviso("Unidos");
    desenhar();
  } catch (erro) { aviso(erro.message); }
}

/* -------------------------------------------------------------- extração */
/* Depois da triagem vem a parte que ninguém gosta: ler cada estudo e tirar
   dele, campo a campo, o que a revisão precisa. O Rayyan acaba aqui — a
   triagem termina e a ferramenta termina junto.

   O desenho é o mesmo da triagem: cada pessoa preenche a sua, e a versão
   final é uma terceira coisa. Sem isso, "extração em duplicata" vira uma
   pessoa conferindo o que a outra digitou, que não é a mesma coisa. */
async function desenharExtracao(palco) {
  const alvo = el("div", {});
  palco.appendChild(alvo);
  let dados;
  try {
    dados = await api("/api/revisoes/" + ESTADO.revisao.code + "/formulario");
  } catch (erro) { alvo.appendChild(el("p", { class: "note erro", text: erro.message })); return; }

  if (!dados.campos.length) {
    alvo.appendChild(el("div", { class: "solto" }, [
      el("h3", { text: "Preparar a extração" }),
      el("div", { class: "hint", text:
        "Escolha o instrumento de risco de viés. O formulário de extração vem "
        + "com os campos que quase toda revisão precisa — dá para mexer depois." }),
      (function () {
        const escolha = el("select", {}, dados.ferramentas.map(function (f) {
          return el("option", { value: f.codigo,
            text: f.nome + " (" + f.dominios + " domínios)" }); }));
        return el("div", { style: "display:grid;gap:9px;max-width:520px" }, [
          escolha,
          el("button", { class: "primary", text: "Preparar", onclick: async function () {
            try {
              await api("/api/revisoes/" + ESTADO.revisao.code + "/formulario", "POST",
                        { ferramenta: escolha.value });
              desenhar();
            } catch (erro) { aviso(erro.message); }
          } }),
        ]);
      })(),
    ]));
    return;
  }

  const p = dados.progresso;
  alvo.appendChild(el("div", { class: "prisma", style: "margin-bottom:16px" }, [
    caixa("Estudos incluídos", p.incluidos, "para extrair"),
    caixa("Com duas extrações", p.com_duas_extracoes, "prontos para conciliar"),
    caixa("Já conciliados", p.acordados, "vão para a tabela"),
  ]));

  if (!dados.incluidos.length) {
    alvo.appendChild(el("div", { class: "note info", text:
      "Nenhum estudo chegou a incluído ainda. A extração começa quando a "
      + "leitura de texto completo terminar." }));
    return;
  }

  if (ESTADO.extraindo) {
    return formularioDeExtracao(alvo, dados, ESTADO.extraindo);
  }

  alvo.appendChild(el("div", { class: "solto" }, [
    el("h3", { text: "Estudos incluídos" }),
    el("div", { class: "hint", text: "Clique para extrair. O que você escrever "
      + "só aparece para a outra pessoa depois que ela também extrair." }),
    el("table", { class: "simples" }, [
      el("thead", {}, el("tr", {}, ["Estudo", "Extrações", "Conciliado"].map(
        function (c, i) { return el("th", { text: c, style: i ? "text-align:right" : null }); }))),
      el("tbody", {}, dados.incluidos.map(function (r) {
        return el("tr", { style: "cursor:pointer",
          onclick: function () { ESTADO.extraindo = r.id; desenhar(); } }, [
          el("td", {}, [el("div", { text: cortar(r.title, 70) }),
            el("small", { class: "hint", text: [r.journal, r.year].filter(Boolean).join(" · ") })]),
          el("td", { class: "num", text: String(r.extracoes || 0) }),
          el("td", { class: "num", text: r.acordados ? "sim" : "—" }),
        ]);
      })),
    ]),
  ]));

  alvo.appendChild(saidasDaExtracao());
  fetch("/api/revisoes/" + ESTADO.revisao.code + "/semaforo.svg")
    .then(function (r) { return r.text(); })
    .then(function (svg) {
      const moldura = document.getElementById("molduraSemaforo");
      if (moldura) moldura.innerHTML = svg;
    }).catch(function () { /* o botão de baixar continua valendo */ });
}

function saidasDaExtracao() {
  const base = "/api/revisoes/" + ESTADO.revisao.code;
  return el("div", { class: "solto" }, [
    el("h3", { text: "O que sai daqui" }),
    el("div", { class: "hint", text:
      "A tabela de características dos estudos incluídos e o semáforo de risco "
      + "de viés — as duas figuras que a revista pede." }),
    el("div", { class: "moldura", id: "molduraSemaforo" }),
    el("div", { class: "extrair", style: "margin-top:12px" }, [
      el("a", { class: "btn-extrair destaque", href: base + "/semaforo.svg",
        download: "", rel: "noopener" },
        [Icons.get("qualidade", 15), el("span", { text: "Semáforo de risco de viés (SVG)" })]),
      el("a", { class: "btn-extrair", href: base + "/caracteristicas.csv",
        download: "", rel: "noopener" },
        [Icons.get("dados", 15), el("span", { text: "Tabela de características (CSV)" })]),
    ]),
  ]);
}

async function formularioDeExtracao(alvo, dados, refId) {
  const estudo = dados.incluidos.find(function (r) { return r.id === refId; }) || {};
  let atual;
  try {
    atual = await api("/api/revisoes/" + ESTADO.revisao.code + "/extracao?ref_id=" + refId);
  } catch (erro) { alvo.appendChild(el("p", { class: "note erro", text: erro.message })); return; }

  alvo.appendChild(el("button", { class: "ghost", text: "← Voltar à lista",
    onclick: function () { ESTADO.extraindo = null; desenhar(); } }));
  alvo.appendChild(el("h2", { style: "margin:12px 0 4px", text: estudo.title || "" }));
  alvo.appendChild(el("div", { class: "hint", style: "margin-bottom:16px",
    text: [estudo.authors, estudo.journal, estudo.year].filter(Boolean).join(" · ") }));
  if (estudo.doi || estudo.url) {
    alvo.appendChild(el("div", { class: "extrair", style: "margin-bottom:16px" },
      el("a", { class: "btn-extrair", target: "_blank", rel: "noopener",
        href: estudo.doi ? "https://doi.org/" + estudo.doi : estudo.url },
        [Icons.get("livro", 15), el("span", { text: "Abrir o artigo" })])));
  }

  const entradas = {};
  const grupos = [];
  dados.campos.forEach(function (campo) {
    let grupo = grupos.find(function (g) { return g.nome === (campo.grupo || "Geral"); });
    if (!grupo) { grupo = { nome: campo.grupo || "Geral", campos: [] }; grupos.push(grupo); }
    grupo.campos.push(campo);
  });

  grupos.forEach(function (grupo) {
    alvo.appendChild(el("div", { class: "solto" }, [
      el("h3", { text: grupo.nome }),
      el("div", { style: "display:grid;gap:14px;margin-top:10px" },
        grupo.campos.map(function (campo) {
          const valor = atual.minha.valores[campo.code] || "";
          let entrada;
          if (campo.kind === "texto_longo") {
            entrada = el("textarea", { rows: "3" });
            entrada.value = valor;
          } else if (campo.kind === "escolha") {
            entrada = el("select", {}, [el("option", { value: "", text: "—" })].concat(
              String(campo.options || "").split(";").filter(Boolean).map(function (o) {
                return el("option", { value: o.trim(), text: o.trim() }); })));
            entrada.value = valor;
          } else if (campo.kind === "sim_nao") {
            entrada = el("select", {}, ["", "Sim", "Não"].map(function (o) {
              return el("option", { value: o, text: o || "—" }); }));
            entrada.value = valor;
          } else {
            entrada = el("input", { type: campo.kind === "numero" ? "number"
              : campo.kind === "data" ? "date" : "text" });
            entrada.value = valor;
          }
          entradas[campo.code] = entrada;
          return el("label", { style: "display:grid;gap:5px" }, [
            el("span", { style: "font-size:13px;font-weight:600",
              text: campo.label + (campo.required ? " *" : "") }),
            campo.help ? el("small", { class: "hint", text: campo.help }) : null,
            entrada,
          ]);
        })),
    ]));
  });

  // risco de viés
  const riscos = {};
  const julgamentos = dados.ferramenta.julgamentos || [];
  alvo.appendChild(el("div", { class: "solto" }, [
    el("h3", { text: "Risco de viés — " + dados.ferramenta.nome }),
    el("div", { style: "display:grid;gap:14px;margin-top:10px" },
      dados.dominios.map(function (d) {
        const meu = atual.minha.risco[d.code] || {};
        const escolha = el("select", {}, [el("option", { value: "", text: "—" })].concat(
          julgamentos.map(function (j) {
            return el("option", { value: j[0], text: j[1] }); })));
        escolha.value = meu.julgamento || "";
        const nota = el("input", { type: "text", placeholder: "Justificativa (o que no texto sustenta)" });
        nota.value = meu.justificativa || "";
        riscos[d.code] = { escolha: escolha, nota: nota };
        return el("div", { style: "display:grid;gap:5px" }, [
          el("span", { style: "font-size:13px;font-weight:600", text: d.label }),
          el("div", { style: "display:grid;grid-template-columns:minmax(160px,220px) 1fr;gap:8px" },
            [escolha, nota]),
        ]);
      })),
  ]));

  alvo.appendChild(el("div", { class: "decidir" }, [
    el("button", { class: "primary", text: "Gravar minha extração",
      onclick: async function () {
        const valores = {}, risco = {};
        Object.entries(entradas).forEach(function (par) { valores[par[0]] = par[1].value; });
        Object.entries(riscos).forEach(function (par) {
          if (par[1].escolha.value) {
            risco[par[0]] = { julgamento: par[1].escolha.value,
                              justificativa: par[1].nota.value };
          }
        });
        try {
          await api("/api/revisoes/" + ESTADO.revisao.code + "/extracao", "POST",
                    { ref_id: refId, valores: valores, risco: risco });
          aviso("Extração gravada");
          desenhar();
        } catch (erro) { aviso(erro.message); }
      } }),
  ]));

  if (atual.divergencias && atual.divergencias.pronto) {
    alvo.appendChild(conciliar(refId, atual.divergencias));
  } else {
    alvo.appendChild(el("p", { class: "hint", style: "margin-top:14px", text:
      "A comparação com a outra extração aparece aqui quando as duas pessoas "
      + "tiverem preenchido — antes disso, comparar seria comparar com o vazio." }));
  }
}

function conciliar(refId, d) {
  const bloco = el("div", { class: "solto", style: "margin-top:20px" });
  bloco.appendChild(el("h3", { text: "Conciliar" }));
  const pendentes = d.divergencias.filter(function (x) { return !x.resolvida; });
  const pendentesRisco = d.risco_divergente.filter(function (x) { return !x.resolvida; });
  bloco.appendChild(el("div", { class: "hint", text:
    pendentes.length || pendentesRisco.length
      ? "Onde as duas extrações discordam. Escolha o que vale — é o que vai "
        + "para a tabela do artigo."
      : "As duas extrações coincidem no que importa. Onde as duas escreveram a "
        + "mesma coisa, isso já é o consenso: não há o que conciliar." }));

  const escolhas = {}, escolhasRisco = {};
  pendentes.forEach(function (campo) {
    const opcoes = Object.entries(campo.respostas);
    const caixa = el("div", { class: "conflito", style: "margin-top:12px" }, [
      el("h3", { style: "font-size:14px", text: campo.label }),
      el("div", { class: "votos" }, opcoes.map(function (par) {
        return el("div", { class: "voto" }, [
          el("b", { text: par[0] }), el("div", { text: par[1] || "(em branco)" })]);
      })),
    ]);
    const escolha = el("select", {}, opcoes.map(function (par) {
      return el("option", { value: par[1], text: par[0] + ": " + (par[1] || "(em branco)") });
    }).concat([el("option", { value: "__outro__", text: "Outro valor…" })]));
    const outro = el("input", { type: "text", placeholder: "O valor acordado", hidden: true });
    escolha.onchange = function () { outro.hidden = escolha.value !== "__outro__"; };
    escolhas[campo.code] = function () {
      return escolha.value === "__outro__" ? outro.value : escolha.value; };
    caixa.appendChild(el("div", { style: "display:grid;gap:8px;max-width:520px" },
      [escolha, outro]));
    bloco.appendChild(caixa);
  });
  pendentesRisco.forEach(function (dominio) {
    const opcoes = Object.entries(dominio.respostas);
    const escolha = el("select", {}, opcoes.map(function (par) {
      const j = (par[1] || {}).julgamento || "";
      return el("option", { value: j, text: par[0] + ": " + (j || "—") });
    }));
    escolhasRisco[dominio.code] = function () { return escolha.value; };
    bloco.appendChild(el("div", { class: "conflito", style: "margin-top:12px" }, [
      el("h3", { style: "font-size:14px", text: dominio.label }),
      el("div", { style: "max-width:520px" }, escolha),
    ]));
  });

  if (pendentes.length || pendentesRisco.length) {
    bloco.appendChild(el("div", { class: "decidir" }, [
      el("button", { class: "incluir", text: "Gravar o que foi acordado",
        onclick: async function () {
          const valores = {}, risco = {};
          Object.entries(escolhas).forEach(function (par) { valores[par[0]] = par[1](); });
          Object.entries(escolhasRisco).forEach(function (par) {
            if (par[1]()) risco[par[0]] = { julgamento: par[1]() }; });
          try {
            await api("/api/revisoes/" + ESTADO.revisao.code + "/extracao", "POST",
                      { ref_id: refId, acordar: true, valores: valores, risco: risco });
            aviso("Conciliado");
            desenhar();
          } catch (erro) { aviso(erro.message); }
        } }),
    ]));
  }
  return bloco;
}

/* -------------------------------------------------------------- PRISMA */
async function desenharPrisma(palco) {
  const alvo = el("div", {});
  palco.appendChild(alvo);
  let dados, concordancia;
  try {
    dados = await api("/api/revisoes/" + ESTADO.revisao.code);
    concordancia = await api("/api/revisoes/" + ESTADO.revisao.code + "/concordancia")
      .catch(function () { return { pares: [] }; });
  } catch (erro) { alvo.appendChild(el("p", { class: "note erro", text: erro.message })); return; }
  const p = dados.prisma;
  alvo.appendChild(el("p", { class: "hint", text:
    "Todos estes números saem do banco. Nenhum é digitado — é o que faz o "
    + "fluxograma conferir com a planilha na hora de publicar." }));
  alvo.appendChild(el("div", { class: "prisma", style: "margin-top:14px" }, [
    caixa("Identificados", p.identificados, "somando as buscas"),
    caixa("Duplicados removidos", p.duplicados, "mesmo estudo em mais de uma base"),
    caixa("Triados", p.triados, "títulos e resumos únicos"),
    caixa("Excluídos na triagem", p.excluidos_triagem, "com motivo registrado"),
    caixa("Texto completo", p.texto_completo, "passaram da triagem"),
    caixa("Incluídos", p.incluidos, "na síntese"),
  ]));
  if (p.pendentes) {
    alvo.appendChild(el("p", { class: "note info", style: "margin-top:14px",
      text: p.pendentes + " referência(s) ainda sem decisão da equipe." }));
  }

  /* O fluxograma que vai no artigo, desenhado destes mesmos números. Quase
     todo mundo o faz à mão num editor de imagem, copiando de uma planilha
     — e é daí que vem o clássico "o fluxograma não fecha com a tabela". */
  const base = "/api/revisoes/" + ESTADO.revisao.code;
  alvo.appendChild(el("div", { class: "solto", style: "margin-top:16px" }, [
    el("h3", { text: "Fluxograma PRISMA 2020" }),
    el("div", { class: "hint", text:
      "Desenhado agora, destes números. SVG entra no Word e no LaTeX sem "
      + "serrilhar, e continua sendo texto — dá para corrigir uma palavra "
      + "sem redesenhar nada." }),
    el("div", { class: "moldura", id: "molduraPrisma" }),
    el("div", { class: "extrair", style: "margin-top:12px" }, [
      el("a", { class: "btn-extrair destaque", href: base + "/prisma.svg",
        download: "", rel: "noopener" }, [
        Icons.get("baixar", 15), el("span", { text: "Baixar o fluxograma (SVG)" })]),
    ]),
  ]));
  fetch(base + "/prisma.svg").then(function (r) { return r.text(); })
    .then(function (svg) {
      const moldura = document.getElementById("molduraPrisma");
      if (moldura) moldura.innerHTML = svg;
    }).catch(function () { /* o botão de baixar continua valendo */ });

  alvo.appendChild(el("div", { class: "solto" }, [
    el("h3", { text: "Levar as referências embora" }),
    el("div", { class: "hint", text:
      "Um sistema de triagem do qual não se sai é uma jaula. O arquivo leva "
      + "junto o que a equipe decidiu e por quê." }),
    (function () {
      const recorte = el("select", {}, [
        ["incluidos", "Incluídos na síntese"],
        ["texto_completo", "Que chegaram ao texto completo"],
        ["excluidos", "Excluídos, com motivo"],
        ["pendentes", "Ainda sem decisão"],
        ["duplicados", "Removidos por repetição"],
        ["todos", "Tudo"],
      ].map(function (par) {
        return el("option", { value: par[0], text: par[1] }); }));
      const linha = el("div", { class: "extrair", style: "margin-top:12px" });
      [["ris", "RIS (.ris)", "etiqueta"], ["bibtex", "BibTeX (.bib)", "livro"],
       ["csv", "Planilha (CSV)", "dados"]].forEach(function (f) {
        linha.appendChild(el("a", { class: "btn-extrair", href: "#", download: "",
          onclick: function (ev) {
            ev.preventDefault();
            location.href = base + "/exportar?formato=" + f[0] + "&recorte=" + recorte.value;
          } }, [Icons.get(f[2], 15), el("span", { text: f[1] })]));
      });
      return el("div", {}, [
        el("div", { style: "max-width:340px" }, recorte), linha]);
    })(),
  ]));
  if ((p.motivos || []).length) {
    alvo.appendChild(secao("Excluídos, com motivo", p.motivos, ["motivo", "n"],
      ["Motivo", "Quantos"]));
  }
  if ((p.por_base || []).length) {
    alvo.appendChild(secao("De onde vieram", p.por_base,
      ["base", "n", "duplicados"], ["Base", "Registros", "Repetidos"]));
  }
  if ((dados.andamento || []).length) {
    alvo.appendChild(secao("Quem triou o quê", dados.andamento,
      ["quem", "triadas", "incluiu", "excluiu", "em_duvida", "segundos_por_referencia"],
      ["Integrante", "Triadas", "Incluiu", "Excluiu", "Talvez", "Seg./ref."]));
  }
  if ((concordancia.pares || []).length) {
    const linhas = concordancia.pares.map(function (x) {
      return { par: x.a + " × " + x.b, n: x.n, concordancia: x.concordancia,
               kappa: x.kappa, leitura: x.leitura };
    });
    const bloco = secao("Concordância entre avaliadores", linhas,
      ["par", "n", "concordancia", "kappa", "leitura"],
      ["Par", "Refs.", "Bruta", "Kappa", "Leitura"]);
    bloco.appendChild(el("p", { class: "hint", style: "margin-top:10px", text:
      "A concordância bruta engana quando quase tudo é excluído: se as duas "
      + "pessoas excluem 95%, concordam em 95% por acaso. O kappa desconta o "
      + "acaso, e é o número que a revista pede." }));
    alvo.appendChild(bloco);
  }
}

function caixa(rotulo, valor, nota) {
  return el("div", { class: "caixa" }, [
    el("div", { class: "rot", text: rotulo }),
    el("div", { class: "val", text: valor === null || valor === undefined ? "—" : valor }),
    nota ? el("small", { text: nota }) : null,
  ]);
}

function secao(titulo, linhas, campos, cabecalhos) {
  const tabela = el("table", { class: "simples" }, [
    el("thead", {}, el("tr", {}, cabecalhos.map(function (c, i) {
      return el("th", { text: c, style: i ? "text-align:right" : null }); }))),
    el("tbody", {}, linhas.map(function (linha) {
      return el("tr", {}, campos.map(function (campo, i) {
        const valor = linha[campo];
        return el("td", { class: i ? "num" : null,
          text: valor === null || valor === undefined ? "—" : String(valor) });
      }));
    })),
  ]);
  return el("div", { class: "solto", style: "margin-top:16px" }, [
    el("h3", { text: titulo }), tabela]);
}

/* -------------------------------------------------------------- importar */
function desenharImportar(palco) {
  palco.appendChild(el("div", { class: "solto" }, [
    el("h3", { text: "Trazer as buscas das bases" }),
    el("div", { class: "hint", text:
      "Salve o resultado da busca em cada base e solte os arquivos aqui. "
      + "RIS (Scopus, Web of Science, Embase), .nbib (PubMed), .bib (Zotero, "
      + "Mendeley) e CSV — inclusive a exportação do Rayyan, que traz junto a "
      + "triagem que a equipe já fez lá." }),
    (function () {
      const entrada = el("input", { type: "file", multiple: true,
        accept: ".ris,.nbib,.bib,.csv,.txt",
        onchange: function (ev) { mandarArquivos(ev.target.files); } });
      const area = el("label", { class: "arquivo" }, [
        Icons.get("baixar", 30),
        el("div", { style: "margin-top:10px;font-weight:600",
          text: "Escolha os arquivos, ou arraste até aqui" }),
        el("div", { class: "hint", text: "vários de uma vez, de bases diferentes" }),
        entrada,
      ]);
      ["dragenter", "dragover"].forEach(function (evento) {
        area.addEventListener(evento, function (ev) {
          ev.preventDefault(); area.classList.add("sobre"); });
      });
      ["dragleave", "drop"].forEach(function (evento) {
        area.addEventListener(evento, function (ev) {
          ev.preventDefault(); area.classList.remove("sobre"); });
      });
      area.addEventListener("drop", function (ev) { mandarArquivos(ev.dataTransfer.files); });
      return area;
    })(),
    el("div", { id: "resultadoImport", style: "margin-top:16px" }),
  ]));
}

async function mandarArquivos(arquivos) {
  const alvo = document.getElementById("resultadoImport");
  alvo.innerHTML = "";
  for (const arquivo of Array.from(arquivos || [])) {
    const linha = el("div", { class: "note info", style: "margin-bottom:8px",
      text: arquivo.name + ": lendo…" });
    alvo.appendChild(linha);
    try {
      const texto = await arquivo.text();
      const r = await api("/api/revisoes/" + ESTADO.revisao.code + "/importar", "POST",
                          { nome: arquivo.name, conteudo: texto });
      linha.className = "note ok";
      linha.textContent = arquivo.name + " (" + r.formato + "): " + r.novos
        + " nova(s), " + r.duplicados + " repetida(s)"
        + (r.com_triagem_do_rayyan ? ", " + r.com_triagem_do_rayyan
           + " com triagem do Rayyan" : "");
    } catch (erro) {
      linha.className = "note erro";
      linha.textContent = arquivo.name + ": " + erro.message;
    }
  }
  await carregarFila(false);
}

/* -------------------------------------------------------------- escolha */
async function desenharEscolha(palco) {
  const alvo = el("div", {});
  palco.appendChild(alvo);
  const dados = await api("/api/revisoes").catch(function () { return { revisoes: [] }; });
  alvo.appendChild(el("h2", { style: "margin-bottom:6px", text: "Revisões" }));
  alvo.appendChild(el("p", { class: "hint", style: "margin-bottom:18px", text:
    "Escolha uma revisão para triar, ou abra uma nova." }));
  (dados.revisoes || []).forEach(function (r) {
    alvo.appendChild(el("div", { class: "solto" }, [
      el("h3", { text: r.title }),
      el("div", { class: "hint", text: (r.question || "")
        + " · " + r.triados + " triados, " + r.pendentes + " pendentes" }),
      el("button", { class: "primary", text: "Abrir",
        onclick: function () { abrir(r.code); } }),
    ]));
  });
  alvo.appendChild(el("div", { class: "solto" }, [
    el("h3", { text: "Nova revisão" }),
    el("div", { class: "hint", text: "O título e a pergunta bastam para começar." }),
    (function () {
      const titulo = el("input", { placeholder: "Título da revisão" });
      const pergunta = el("input", { placeholder: "Pergunta (opcional)" });
      const quantos = el("select", {}, [
        el("option", { value: "2", text: "2 avaliadores (recomendado)" }),
        el("option", { value: "1", text: "1 avaliador (revisão de escopo)" }),
        el("option", { value: "3", text: "3 avaliadores" }),
      ]);
      return el("div", { style: "display:grid;gap:9px;max-width:460px" }, [
        titulo, pergunta, quantos,
        el("button", { class: "primary", text: "Criar", onclick: async function () {
          if (!titulo.value.trim()) { aviso("Dê um título à revisão"); return; }
          try {
            const r = await api("/api/revisoes", "POST", {
              titulo: titulo.value.trim(), pergunta: pergunta.value.trim(),
              avaliadores: Number(quantos.value) });
            abrir(r.code || r.id);
          } catch (erro) { aviso(erro.message); }
        } }),
      ]);
    })(),
  ]));
}

/* -------------------------------------------------------------- carga */
async function abrir(code) {
  const dados = await api("/api/revisoes/" + code);
  ESTADO.revisao = dados.revisao;
  ESTADO.motivos = dados.motivos || [];
  ESTADO.termos = dados.termos || [];
  ESTADO.aba = "triar";
  ESTADO.sessaoInicio = Date.now();
  ESTADO.feitasAgora = 0;
  history.replaceState(null, "", "/triagem?r=" + encodeURIComponent(code));
  await carregarFila(false);
}

async function carregarFila(acrescentar) {
  if (!ESTADO.revisao) return;
  try {
    const dados = await api("/api/revisoes/" + ESTADO.revisao.code
      + "/fila?etapa=" + ESTADO.etapa + "&limite=60");
    const jaNaTela = new Set(ESTADO.fila.slice(0, ESTADO.indice).map(function (r) { return r.id; }));
    const novas = (dados.fila || []).filter(function (r) { return !jaNaTela.has(r.id); });
    if (acrescentar) {
      const conhecidas = new Set(ESTADO.fila.map(function (r) { return r.id; }));
      ESTADO.fila = ESTADO.fila.concat(
        novas.filter(function (r) { return !conhecidas.has(r.id); }));
    } else {
      ESTADO.fila = novas;
      ESTADO.indice = 0;
    }
    ESTADO.faltam = dados.faltam;
    ESTADO.jaTriei = dados.ja_triei;
    ESTADO.motivos = dados.motivos || ESTADO.motivos;
    ESTADO.termos = dados.termos || ESTADO.termos;
    ESTADO.eu = dados.eu;
  } catch (erro) {
    aviso(erro.message);
  }
  desenhar();
}

/* -------------------------------------------------------------- teclado */
document.addEventListener("keydown", function (ev) {
  const ajuda = document.getElementById("ajuda");
  if (ev.key === "Escape") { ajuda.hidden = true; return; }
  if (ev.key === "?") { ajuda.hidden = !ajuda.hidden; return; }
  const alvo = ev.target;
  if (alvo && /^(INPUT|TEXTAREA|SELECT)$/.test(alvo.tagName)) return;
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (!ESTADO.revisao || ESTADO.aba !== "triar" || !atual()) return;
  const tecla = ev.key.toLowerCase();
  if (tecla === "i") { ev.preventDefault(); decidir("incluir"); }
  else if (tecla === "e") { ev.preventDefault(); abrirMotivos(); }
  else if (tecla === "t") { ev.preventDefault(); decidir("talvez"); }
  else if (tecla === "z") { ev.preventDefault(); desfazer(); }
  else if (tecla === "a") {
    const primeiro = document.querySelector(".ref .fora a");
    if (primeiro) { ev.preventDefault(); window.open(primeiro.href, "_blank", "noopener"); }
  } else if (/^[1-9]$/.test(tecla)) {
    const motivo = ESTADO.motivos[Number(tecla) - 1];
    if (motivo) { ev.preventDefault(); decidir("excluir", motivo.id); }
  }
});

document.getElementById("ajudaBtn").onclick = function () {
  const ajuda = document.getElementById("ajuda");
  ajuda.hidden = !ajuda.hidden;
};
document.getElementById("ajuda").onclick = function (ev) {
  if (ev.target.id === "ajuda") ev.currentTarget.hidden = true;
};

/* Sair no meio com decisão por enviar não pode custar a decisão. */
window.addEventListener("beforeunload", function (ev) {
  if (ESTADO.pendentes.length) { ev.preventDefault(); ev.returnValue = ""; }
});

(async function inicio() {
  const code = new URLSearchParams(location.search).get("r");
  if (code) { try { await abrir(code); return; } catch (erro) { aviso(erro.message); } }
  desenhar();
})();
