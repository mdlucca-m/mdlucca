/* Panorama analítico da produção do LAPE.
 *
 * A régua deste arquivo: cada gráfico responde uma pergunta escrita ao
 * lado dele. Onde o dado não sustenta a resposta, a tela diz isso em
 * português — em vez de desenhar uma curva bonita sobre um ponto só. */

/* A biblioteca de gráficos se expõe como `Charts`; aqui ela é `C`, como no
   painel — a mesma abreviação nos dois arquivos evita ler o mesmo gráfico
   com dois nomes. */
const C = Charts;

const D = { pronto: false };
const ST = { aba: "visao", variavel: null, busca: "", ordem: "ano", desc: true,
             so_multi: false, linha: "", abertos: {} };

async function api(caminho, metodo, corpo) {
  const r = await fetch(caminho, {
    method: metodo || "GET",
    headers: corpo ? { "Content-Type": "application/json" } : {},
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  if (r.status === 401) { location.href = "/entrar?next=/panorama"; throw new Error("entre"); }
  const dados = await r.json().catch(function () { return {}; });
  if (!r.ok) throw new Error(dados.error || ("erro " + r.status));
  return dados;
}

function el(tag, props, filhos) {
  const n = document.createElement(tag);
  Object.entries(props || {}).forEach(function (par) {
    const [k, v] = par;
    if (v === null || v === undefined || v === false) return;
    if (k === "text") n.textContent = v;
    else if (k === "html") n.innerHTML = v;
    else if (k.startsWith("on")) n[k.toLowerCase()] = v;
    else n.setAttribute(k, v === true ? "" : v);
  });
  (Array.isArray(filhos) ? filhos : filhos ? [filhos] : []).forEach(function (f) {
    if (f === null || f === undefined) return;
    n.appendChild(typeof f === "string" ? document.createTextNode(f) : f);
  });
  return n;
}

function aviso(texto) {
  const c = document.getElementById("aviso");
  c.textContent = texto;
  c.style.transform = "translateX(-50%) translateY(0)";
  clearTimeout(aviso._t);
  aviso._t = setTimeout(function () {
    c.style.transform = "translateX(-50%) translateY(140%)"; }, 2800);
}

function cortar(t, n) {
  const s = String(t || "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

/* Cor por variável, com duas regras que brigam entre si e precisam das
   duas:

   1. a MESMA variável tem a MESMA cor em toda a tela — cor que muda de
      gráfico para gráfico obriga a reler a legenda toda vez;
   2. duas variáveis NUNCA dividem a mesma cor.

   A paleta tem oito cores e o vocabulário tem mais de vinte, então
   ciclar o índice quebra a segunda regra em silêncio: foi o que
   aconteceu — "Exercício" e "Saúde mental" saíram as duas verdes no
   mesmo gráfico, e a legenda não ajudava a separar.

   A saída é não ciclar. As oito cores vão para as oito variáveis mais
   presentes na produção (atribuição feita uma vez, a partir do dado, e
   por isso estável na tela inteira); da nona em diante, cinza. Cinza diz
   a verdade: aquela variável não está entre as que a paleta consegue
   distinguir, e a identidade dela vem do rótulo, não da cor. */
const CORES = {};

function montarCores() {
  const ordenadas = ((D.panorama || {}).variaveis || []).slice()
    .sort(function (a, b) { return b.total_geral - a.total_geral; });
  ordenadas.forEach(function (v, i) {
    CORES[v.code] = i < 8 ? C.token("--series-" + (i + 1)) : C.token("--ink-muted");
  });
}

function corDaVariavel(code) {
  return CORES[code] || C.token("--ink-muted");
}

function iconeDaVariavel(code) {
  const v = (D.vocabulario || []).find(function (x) { return x.code === code; });
  return (v && v.icone) || "alvo";
}

function seloVariavel(v, opts) {
  const conf = opts || {};
  return el("span", {
    class: "selo-var" + (v.origem === "auto" ? " auto" : "")
      + (ST.variavel === v.code ? " on" : ""),
    style: "--tom:" + corDaVariavel(v.code),
    title: (v.origem === "auto" ? "Reconhecida automaticamente — " + (v.trecho || "")
            : "Confirmada por quem leu") + " · clique para filtrar",
    onclick: function (ev) {
      ev.stopPropagation();
      ST.variavel = ST.variavel === v.code ? null : v.code;
      if (conf.aoClicar) conf.aoClicar(); else desenhar();
    },
  }, [Icons.get(iconeDaVariavel(v.code), 12), el("span", { text: v.label })]);
}

/* ==================================================================== */
/* navegação                                                            */
/* ==================================================================== */
const ABAS = [
  { id: "visao", rotulo: "Visão geral", icone: "painel", grupo: "" },
  { id: "laboratorio", rotulo: "O laboratório", icone: "instituicao", grupo: "Contexto" },
  { id: "variaveis", rotulo: "Variáveis", icone: "alvo", grupo: "Contexto" },
  { id: "curvas", rotulo: "Curvas e derivadas", icone: "linhas", grupo: "Análise" },
  { id: "rede", rotulo: "Rede temática", icone: "rede", grupo: "Análise" },
  { id: "mapa", rotulo: "Mapa da produção", icone: "mapa", grupo: "Análise" },
  { id: "sintese", rotulo: "Síntese", icone: "aceite", grupo: "Leitura" },
  { id: "lacunas", rotulo: "Lacunas e insights", icone: "explorar", grupo: "Leitura" },
  { id: "extracao", rotulo: "Extração", icone: "dados", grupo: "Leitura" },
];

function montarNav() {
  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  nav.appendChild(el("div", { class: "marca" }, [
    el("div", { class: "selo", text: "LP" }),
    el("div", {}, [
      el("b", { text: "Panorama" }),
      el("small", { text: (D.laboratorio || {}).instituicao || "LAPE" }),
    ]),
  ]));
  let grupoAtual = null;
  ABAS.forEach(function (aba) {
    if (aba.grupo !== grupoAtual) {
      grupoAtual = aba.grupo;
      if (grupoAtual) nav.appendChild(el("div", { class: "grupo", text: grupoAtual }));
    }
    const conta = contaDaAba(aba.id);
    nav.appendChild(el("button", {
      class: ST.aba === aba.id ? "on" : "",
      onclick: function () { ST.aba = aba.id; desenhar(); window.scrollTo(0, 0); },
    }, [
      Icons.get(aba.icone, null),
      el("span", { text: aba.rotulo }),
      conta !== null ? el("span", { class: "n", text: String(conta) }) : null,
    ]));
  });
  nav.appendChild(el("div", { class: "grupo", text: "Ir para" }));
  [["Painel de indicadores", "/painel", "barras"],
   ["Triagem de revisão", "/triagem", "filtro"],
   ["Área do integrante", "/app", "pessoa"]].forEach(function (x) {
    const a = el("a", { href: x[1], style: "text-decoration:none;display:block" });
    a.appendChild(el("button", {}, [Icons.get(x[2], null), el("span", { text: x[0] })]));
    nav.appendChild(a);
  });
}

function contaDaAba(id) {
  const p = D.panorama || {};
  if (id === "variaveis") return (p.variaveis || []).length;
  if (id === "extracao") return (D.artigos || []).length;
  if (id === "lacunas") return ((D.lacunas || {}).achados || []).length;
  if (id === "rede") return ((p.rede || {}).arestas || []).length;
  return null;
}

/* ==================================================================== */
/* peças reutilizadas                                                   */
/* ==================================================================== */
function cabeca(icone, titulo, texto, direita) {
  return el("div", { class: "cabeca" }, [
    el("div", { class: "brasao" }, Icons.get(icone, null)),
    el("div", { style: "flex:1;min-width:240px" }, [
      el("h1", { text: titulo }),
      texto ? el("p", { text: texto }) : null,
    ]),
    direita ? el("div", { class: "direita" }, direita) : null,
  ]);
}

function cartao(icone, titulo, dica, corpo) {
  return el("div", { class: "cartao" }, [
    el("h3", {}, [icone ? Icons.get(icone, null) : null, el("span", { text: titulo })]),
    dica ? el("div", { class: "hint", text: dica }) : null,
    el("div", { class: "corpo" }, corpo),
  ]);
}

function indicador(rotulo, valor, pe, icone) {
  return el("div", { class: "cartao" }, [
    el("div", { style: "display:flex;align-items:center;gap:9px" }, [
      icone ? Icons.get(icone, null) : null,
      el("div", { class: "rotulo", text: rotulo }),
    ]),
    el("div", { class: "numero", style: "margin-top:8px", text: String(valor) }),
    pe ? el("div", { class: "pe", text: pe }) : null,
  ]);
}

function nota(html) {
  return el("div", { class: "nota-honesta", html: html });
}

/* ==================================================================== */
/* 1. visão geral                                                       */
/* ==================================================================== */
function verVisao(palco) {
  const p = D.panorama, s = D.sintese;
  const lab = D.laboratorio || {};
  palco.appendChild(cabeca("painel", "Panorama analítico",
    "O que o laboratório estuda, como isso se move no tempo e o que ainda não foi "
    + "olhado — calculado do banco a cada acesso.",
    [seloAoVivo(),
     el("a", { class: "botao-destino", href: "/painel", text: "Indicadores" })]));

  palco.appendChild(el("div", { class: "tese" }, [
    el("h3", {}, [Icons.get("alvo", null), el("span", { text: "O que este painel responde" })]),
    el("p", { html: "Três perguntas, nesta ordem: <b>o que estudamos</b> — as variáveis "
      + "que aparecem na produção e o peso de cada uma; <b>como isso anda</b> — a curva "
      + "de cada variável no tempo, onde ela acelera, onde perde fôlego e onde cruza "
      + "com outra; e <b>o que falta</b> — o que ficou pela metade, o que nunca foi "
      + "olhado e que ponte entre dois assuntos ninguém atravessou." }),
    el("p", { html: "O recorte é de <b>" + p.janela.corte + "</b> (" + p.janela.de + "–"
      + p.janela.ate + "). Não é gosto: produção de mais de vinte anos atrás foi feita "
      + "com outra equipe, outro financiamento e outra pergunta — misturar tudo numa "
      + "curva só faz a curva não significar nada." }),
  ]));

  const publicados = (s.situacoes || {}).publicado || 0;
  const emAvaliacao = ((s.situacoes || {}).submetido || 0) + ((s.situacoes || {}).em_revisao || 0);
  palco.appendChild(el("div", { class: "grade g4" }, [
    indicador("Artigos no acervo", p.total_artigos, p.no_recorte + " no recorte", "producao"),
    indicador("Variáveis ativas", (p.variaveis || []).length,
      "de " + (D.vocabulario || []).length + " no vocabulário", "alvo"),
    indicador("Integrantes", lab.integrantes || 0, (lab.projetos || 0) + " projeto(s)", "pessoas"),
    indicador("Publicados", publicados, emAvaliacao + " em avaliação", "trofeu"),
  ]));

  /* velocímetros: cada um responde "quanto do caminho já andamos" */
  const emProducao = (s.situacoes || {}).em_producao || 0;
  const totalArt = p.total_artigos || 1;
  palco.appendChild(el("div", { class: "grade g3", style: "margin-top:14px" }, [
    cartao("relogio", "Quanto do acervo já saiu",
      "Publicados sobre o total. É a taxa que diz se o laboratório fecha o que abre.",
      C.gauge({ value: publicados, max: totalArt, unit: "publicados",
                display: publicados + " de " + totalArt })),
    cartao("submissao", "Quanto já foi submetido",
      "Sair da escrita é o primeiro gargalo — e o mais silencioso.",
      C.gauge({ value: totalArt - emProducao, max: totalArt, unit: "fora da escrita",
                display: (totalArt - emProducao) + " de " + totalArt })),
    cartao("rede", "Quão combinatória é a produção",
      "Variáveis por artigo. Acima de 2, o valor está no cruzamento.",
      C.gauge({ value: mediaVariaveis(), max: 4, unit: "variáveis por artigo",
                display: mediaVariaveis().toFixed(1).replace(".", ",") })),
  ]));

  /* funil da produção: onde cada artigo está */
  const etapas = [
    { label: "Em escrita", value: emProducao },
    { label: "Submetidos", value: emAvaliacao },
    { label: "Aceitos", value: (s.situacoes || {}).aceito || 0 },
    { label: "Publicados", value: publicados },
  ];
  palco.appendChild(el("div", { class: "grade g2", style: "margin-top:14px" }, [
    cartao("processo", "O caminho do artigo",
      "Cada degrau é uma etapa vencida. O degrau que encolhe mais é o gargalo.",
      C.funnel({ steps: etapas, file: "funil-producao", height: 250 })),
    cartao("barras", "Peso de cada variável",
      "Quantos artigos tocam cada assunto. Clique para filtrar a tela inteira.",
      C.bars({
        items: (p.variaveis || []).slice(0, 10).map(function (v) {
          return { label: v.label, value: v.total_geral,
                   color: corDaVariavel(v.code),
                   onSelect: function () { ST.variavel = v.code; ST.aba = "variaveis"; desenhar(); } };
        }),
        labelWidth: 190, labelChars: 26, unit: "artigo(s)", file: "peso-variaveis" })),
  ]));

  palco.appendChild(el("h2", { style: "margin:26px 0 12px;font-size:19px",
    text: "O que os números dizem" }));
  palco.appendChild(el("div", { class: "grade g3" },
    (s.achados || []).map(function (a) {
      return el("div", { class: "cartao" }, [
        el("h3", {}, [Icons.get(a.icone || "aceite", null),
                      el("span", { text: a.titulo })]),
        a.numero !== null && a.numero !== undefined
          ? el("div", { class: "numero", style: "margin:10px 0 6px", text: String(a.numero) })
          : null,
        el("div", { class: "hint", style: "line-height:1.6", text: a.texto }),
      ]);
    })));
}

function mediaVariaveis() {
  const total = (D.artigos || []).length || 1;
  const ligacoes = (D.artigos || []).reduce(function (soma, a) {
    return soma + (a.variaveis || []).length; }, 0);
  return ligacoes / total;
}

/* ==================================================================== */
/* 2. o laboratório: linha do tempo que abre em organograma             */
/* ==================================================================== */
function verLaboratorio(palco) {
  const lab = D.laboratorio || {};
  palco.appendChild(cabeca("instituicao", lab.nome || "O laboratório",
    "A história da produção, ano a ano. Clique num ano para abrir o que foi feito "
    + "nele e as variáveis que apareceram junto."));

  palco.appendChild(el("div", { class: "grade g3" }, (D.linhas || []).map(function (l) {
    return el("div", { class: "cartao" }, [
      el("h3", {}, [Icons.get("linha", null), el("span", { text: l.name })]),
      el("div", { class: "hint", style: "margin-top:5px;line-height:1.55",
        text: l.description || l.keywords || "" }),
      el("div", { class: "numero", style: "margin-top:12px", text: String(l.n) }),
      el("div", { class: "pe", text: "artigo(s) ligados a esta linha" }),
    ]);
  })));

  const semLinha = (D.artigos || []).filter(function (a) { return !a.research_line; }).length;
  if (semLinha) {
    palco.appendChild(nota("<b>" + semLinha + " de " + (D.artigos || []).length
      + " artigos não estão ligados a nenhuma linha de pesquisa.</b> "
      + "O organograma abaixo mostra isso como \"sem linha declarada\" — não é falha "
      + "do painel, é campo em branco no cadastro. Ligar cada artigo à sua linha na "
      + "<a href='/app#artigos'>Área do integrante</a> faz esta aba inteira ganhar o "
      + "primeiro nível de hierarquia."));
  }

  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "rede", "Organograma do que se estuda",
    "Linha de pesquisa → variável → artigo. Clique para descer um nível.",
    arvoreHierarquica())));

  palco.appendChild(el("h2", { style: "margin:26px 0 12px;font-size:19px",
    text: "Linha do tempo" }));
  const porAno = {};
  (D.artigos || []).forEach(function (a) {
    if (!a.ano) return;
    (porAno[a.ano] = porAno[a.ano] || []).push(a);
  });
  const anos = Object.keys(porAno).map(Number).sort(function (a, b) { return a - b; });
  if (!anos.length) {
    palco.appendChild(nota("<b>Nenhum artigo com ano de referência.</b> A linha do tempo "
      + "aparece quando houver — e a história completa do laboratório está no Lattes "
      + "da equipe, que o sistema importa."));
    return;
  }
  const trilho = el("div", { class: "trilho" });
  anos.forEach(function (ano) {
    const artigos = porAno[ano];
    const vars = {};
    artigos.forEach(function (a) {
      (a.variaveis || []).forEach(function (v) { vars[v.code] = v; }); });
    const aberto = !!ST.abertos["ano" + ano];
    const marco = el("div", { class: "marco" + (aberto ? " aberto" : "") });
    marco.appendChild(el("div", { class: "bolha" }, Icons.get("prazo", null)));
    marco.appendChild(el("div", {
      class: "topo",
      onclick: function () {
        ST.abertos["ano" + ano] = !aberto;
        desenhar();
      },
    }, [
      el("span", { class: "ano", text: String(ano) }),
      el("span", { class: "titulo",
        text: artigos.length + " artigo(s) · " + Object.keys(vars).length + " variável(is)" }),
      el("span", { class: "conta",
        text: Object.values(vars).slice(0, 3).map(function (v) { return v.label; }).join(" · ") }),
      el("span", { class: "abre", text: "▸" }),
    ]));
    if (aberto) {
      const ramos = el("div", { class: "ramos" });
      artigos.forEach(function (a, i) {
        ramos.appendChild(el("div", {
          class: "ramo", style: "animation-delay:" + (i * 55) + "ms",
        }, [
          Icons.get("producao", null),
          el("div", { class: "txt" }, [
            el("span", { text: cortar(a.title, 92) }),
            el("small", { text: (a.variaveis || []).map(function (v) { return v.label; })
              .join(" · ") || "sem variável reconhecida" }),
          ]),
        ]));
      });
      marco.appendChild(ramos);
    }
    trilho.appendChild(marco);
  });
  palco.appendChild(trilho);
}

function arvoreHierarquica() {
  const linhas = {};
  (D.artigos || []).forEach(function (a) {
    const chave = a.research_line || "Sem linha declarada";
    (linhas[chave] = linhas[chave] || []).push(a);
  });
  const nomes = Object.keys(linhas).sort(function (a, b) {
    return linhas[b].length - linhas[a].length; });
  const escolhida = ST.abertos.linha && linhas[ST.abertos.linha] ? ST.abertos.linha : nomes[0];
  const daLinha = linhas[escolhida] || [];
  const vars = {};
  daLinha.forEach(function (a) {
    (a.variaveis || []).forEach(function (v) {
      (vars[v.code] = vars[v.code] || { label: v.label, code: v.code, artigos: [] })
        .artigos.push(a);
    });
  });
  const codigos = Object.keys(vars).sort(function (a, b) {
    return vars[b].artigos.length - vars[a].artigos.length; });
  const varEscolhida = vars[ST.abertos.variavel] ? ST.abertos.variavel : codigos[0];

  return el("div", { class: "arvore" }, [
    el("div", { class: "coluna" }, [el("div", { class: "cab", text: "Linha de pesquisa" })]
      .concat(nomes.map(function (nome) {
        return el("div", {
          class: "no" + (nome === escolhida ? " on" : ""),
          onclick: function () {
            ST.abertos.linha = nome; ST.abertos.variavel = null; desenhar(); },
        }, [Icons.get("linha", null), el("span", { text: cortar(nome, 24) }),
            el("span", { class: "n", text: String(linhas[nome].length) })]);
      }))),
    el("div", { class: "coluna" }, [el("div", { class: "cab", text: "Variável" })]
      .concat(codigos.length ? codigos.map(function (code) {
        return el("div", {
          class: "no" + (code === varEscolhida ? " on" : ""),
          style: "--tom:" + corDaVariavel(code),
          onclick: function () { ST.abertos.variavel = code; desenhar(); },
        }, [Icons.get(iconeDaVariavel(code), null),
            el("span", { text: cortar(vars[code].label, 22) }),
            el("span", { class: "n", text: String(vars[code].artigos.length) })]);
      }) : [el("div", { class: "hint", text: "Nenhuma variável nesta linha." })])),
    el("div", { class: "coluna" }, [el("div", { class: "cab", text: "Artigos" })]
      .concat(((vars[varEscolhida] || {}).artigos || []).map(function (a) {
        return el("div", { class: "no folha" }, [
          Icons.get("producao", null),
          el("span", { text: cortar(a.title, 64) })]);
      }))),
  ]);
}

/* ==================================================================== */
/* 3. variáveis                                                         */
/* ==================================================================== */
function verVariaveis(palco) {
  const p = D.panorama;
  palco.appendChild(cabeca("alvo", "Variáveis",
    "Cada assunto que a produção do laboratório toca, com o peso e o comportamento "
    + "no tempo. Clique num selo para filtrar a extração por ele.",
    [el("button", {
      text: ST.variavel ? "Limpar filtro" : "Nenhum filtro",
      onclick: function () { ST.variavel = null; desenhar(); },
    })]));

  const porGrupo = {};
  (p.variaveis || []).forEach(function (v) {
    (porGrupo[v.grupo || "Outras"] = porGrupo[v.grupo || "Outras"] || []).push(v); });

  Object.keys(porGrupo).forEach(function (grupo) {
    palco.appendChild(el("h2", { style: "margin:22px 0 10px;font-size:17px", text: grupo }));
    palco.appendChild(el("div", { class: "grade g3" }, porGrupo[grupo].map(function (v) {
      const cor = corDaVariavel(v.code);
      const corpo = [
        el("div", { style: "display:flex;align-items:baseline;gap:10px" }, [
          el("div", { class: "numero", text: String(v.total_geral) }),
          el("div", { class: "hint", text: "artigo(s)" }),
        ]),
        el("div", { style: "margin-top:10px" },
          C.sparkline(v.serie, { color: cor })),
        el("div", { class: "pe", text:
          v.confiavel
            ? v.tendencia + (v.crescimento_ao_ano !== null
                ? " · " + v.crescimento_ao_ano + "%/ano" : "")
            : (v.porque || "série curta") }),
      ];
      if (v.inflexoes && v.inflexoes.length) {
        corpo.push(el("div", { class: "hint", style: "margin-top:6px", text:
          "inflexão em " + v.inflexoes[v.inflexoes.length - 1].ano + ": "
          + v.inflexoes[v.inflexoes.length - 1].leitura }));
      }
      const c = el("div", { class: "cartao", style: "cursor:pointer",
        onclick: function () { ST.variavel = v.code; ST.aba = "extracao"; desenhar(); } }, [
        el("h3", {}, [Icons.get(v.icone || "alvo", null), el("span", { text: v.label })]),
        el("div", { class: "corpo" }, corpo),
      ]);
      c.style.borderLeft = "3px solid " + cor;
      return c;
    })));
  });
}

/* ==================================================================== */
/* 4. curvas e derivadas                                                */
/* ==================================================================== */
function verCurvas(palco) {
  const p = D.panorama;
  const anos = p.janela.anos.map(String);
  const fortes = (p.variaveis || []).filter(function (v) { return v.total > 0; }).slice(0, 6);

  palco.appendChild(cabeca("linhas", "Curvas e derivadas",
    "Como cada variável se comporta no tempo: o sinal depois do filtro, a velocidade "
    + "(quanto sobe por ano) e a aceleração (se a curva abre ou fecha)."));

  palco.appendChild(el("div", { class: "tese" }, [
    el("h3", {}, [Icons.get("qualidade", null), el("span", { text: "Como ler" })]),
    el("p", { html: "A série é anual e discreta, então o que se calcula são "
      + "<b>diferenças finitas centrais</b>, não derivadas contínuas — chamar de "
      + "derivada sem dizer que o passo é de um ano seria rigor de fachada." }),
    el("p", { html: "Antes de derivar, a série passa por uma <b>mediana móvel</b> (um ano "
      + "atípico não arrasta a curva) e por uma suavização. O que sobra da subtração é o "
      + "<b>ruído</b>, mostrado à parte: variável cujo ruído supera o sinal não tem "
      + "tendência para interpretar, por mais bonita que a linha fique." }),
    el("p", { html: "O <b>ponto de inflexão</b> é onde a aceleração troca de sinal — "
      + "onde a curva para de abrir e começa a fechar. É o momento que interessa "
      + "diagnosticar, e quase sempre passa despercebido porque o número ainda sobe." }),
  ]));

  if (!fortes.length || !fortes.some(function (v) { return v.confiavel; })) {
    palco.appendChild(nota("<b>Ainda não há série que sustente derivada.</b> "
      + "Nenhuma variável tem produção em três anos distintos dentro do recorte. "
      + "A história completa do laboratório está no <b>Lattes da equipe</b> — importá-lo "
      + "traz a publicação de cada integrante ano a ano, e estas curvas passam a ter o "
      + "que analisar. Enquanto isso, os cartões abaixo mostram a série crua."));
  }

  /* Os pontos de inflexão marcados NA curva, e não só numa tabela ao lado.
     O ponto só significa alguma coisa em cima da linha que o gerou: numa
     tabela, "2015 — desaceleração" é um número; no gráfico, é o lugar em
     que a curva visivelmente deixa de abrir. */
  const marcas = [];
  fortes.forEach(function (v, si) {
    (v.inflexoes || []).forEach(function (inf) {
      const i = p.janela.anos.indexOf(inf.ano);
      if (i >= 0) {
        marcas.push({ serie: si, i: i, label: String(inf.ano),
                      color: corDaVariavel(v.code),
                      title: v.label + " · " + inf.ano + ": " + inf.leitura });
      }
    });
  });

  palco.appendChild(cartao("linhas", "Todas as variáveis no tempo",
    marcas.length
      ? "Séries filtradas, com os pontos de inflexão marcados sobre a própria curva. "
        + "Onde duas linhas se cruzam, uma passou a outra."
      : "Séries filtradas. Onde duas linhas se cruzam, uma passou a outra.",
    C.lines({
      labels: anos,
      series: fortes.map(function (v) {
        return { label: v.label, values: v.suave, color: corDaVariavel(v.code),
                 area: false }; }),
      marks: marcas,
      height: 340, file: "curvas-variaveis" })));

  const comCurva = fortes.filter(function (v) { return v.confiavel; });
  if (comCurva.length) {
    palco.appendChild(el("div", { class: "grade g2", style: "margin-top:14px" }, [
      cartao("subida", "Velocidade — artigos por ano",
        "Acima de zero a variável cresce; abaixo, encolhe.",
        C.lines({ labels: anos,
          series: comCurva.map(function (v) {
            return { label: v.label, values: v.velocidade, color: corDaVariavel(v.code) }; }),
          height: 240, file: "velocidade" })),
      cartao("raio", "Aceleração — a curva abre ou fecha?",
        "Onde cruza o zero está o ponto de inflexão, marcado no gráfico.",
        C.lines({ labels: anos,
          series: comCurva.map(function (v) {
            return { label: v.label, values: v.aceleracao, color: corDaVariavel(v.code) }; }),
          marks: comCurva.reduce(function (acc, v, si) {
            (v.inflexoes || []).forEach(function (inf) {
              const i = p.janela.anos.indexOf(inf.ano);
              if (i >= 0) acc.push({ serie: si, i: i, color: corDaVariavel(v.code),
                                     title: v.label + ": " + inf.leitura });
            });
            return acc;
          }, []),
          height: 240, file: "aceleracao" })),
    ]));

    const inflexoes = [];
    comCurva.forEach(function (v) {
      (v.inflexoes || []).forEach(function (i) {
        inflexoes.push({ variavel: v.label, code: v.code, ano: i.ano, tipo: i.tipo,
                         leitura: i.leitura }); });
    });
    if (inflexoes.length) {
      palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
        "alvo", "Pontos de inflexão", "Onde cada curva mudou de curvatura.",
        el("table", { class: "dados" }, [
          el("thead", {}, el("tr", {}, ["Ano", "Variável", "O quê", "Leitura"].map(
            function (c) { return el("th", { text: c }); }))),
          el("tbody", {}, inflexoes.sort(function (a, b) { return b.ano - a.ano; })
            .map(function (i) {
              return el("tr", {}, [
                el("td", { class: "num", text: String(i.ano) }),
                el("td", {}, el("span", { class: "selo-var",
                  style: "--tom:" + corDaVariavel(i.code) },
                  [Icons.get(iconeDaVariavel(i.code), 12), el("span", { text: i.variavel })])),
                el("td", { text: i.tipo }),
                el("td", { class: "hint", text: i.leitura }),
              ]);
            })),
        ]))));
    }
  }

  if ((p.cruzamentos || []).length) {
    palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
      "conectar", "Cruzamentos", "Em que ano uma variável passou a outra em volume.",
      el("table", { class: "dados" }, [
        el("thead", {}, el("tr", {}, ["Ano", "Quem passou", "Quem foi passada"].map(
          function (c) { return el("th", { text: c }); }))),
        el("tbody", {}, p.cruzamentos.map(function (x) {
          return el("tr", {}, [
            el("td", { class: "num", text: String(x.ano_cheio) }),
            el("td", { text: x.quem_subiu }),
            el("td", { class: "hint", text: x.quem_desceu }),
          ]);
        })),
      ]))));
  }

  const ruidosas = (p.variaveis || []).filter(function (v) {
    return v.razao_ruido !== null && v.razao_ruido >= 0.5; });
  if (ruidosas.length) {
    palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
      "aviso", "Sinal e ruído", "Quanto o balanço pesa diante da variação real. "
      + "Perto de 1, a linha é quase só ruído.",
      C.bars({ items: ruidosas.map(function (v) {
        return { label: v.label, value: v.razao_ruido, color: corDaVariavel(v.code) }; }),
        labelWidth: 190, unit: "ruído/sinal", file: "ruido" }))));
  }
}

/* ==================================================================== */
/* 5. rede temática                                                     */
/* ==================================================================== */
function grauNaRede(rede, code) {
  return (rede.arestas || []).filter(function (a) {
    return a.a === code || a.b === code; }).length;
}

function verRede(palco) {
  const rede = (D.panorama || {}).rede || { nos: [], arestas: [] };
  palco.appendChild(cabeca("rede", "Rede temática",
    "Quais variáveis aparecem no mesmo artigo. É o desenho de como os assuntos do "
    + "laboratório se amarram."));

  palco.appendChild(el("div", { class: "tese" }, [
    el("h3", {}, [Icons.get("qualidade", null), el("span", { text: "Por que o Jaccard" })]),
    el("p", { html: "A contagem crua favorece o que é comum: uma variável que aparece "
      + "em tudo aparece junto de tudo. O <b>Jaccard</b> pergunta que fração das "
      + "aparições das duas é compartilhada — e é por ele que se vê o par que anda "
      + "junto de verdade, não o par que apenas é frequente." }),
  ]));

  if (!rede.arestas.length) {
    palco.appendChild(nota("<b>Nenhum artigo com duas variáveis ainda.</b> A rede aparece "
      + "quando houver — é o cruzamento que a desenha."));
    return;
  }

  palco.appendChild(cartao("rede", "Como os assuntos se amarram",
    "O tamanho do nó é o número de artigos; a espessura da linha, quantos eles dividem.",
    C.network({
      /* `weight`, e não `value`: é o nome que a biblioteca lê. Com o campo
         errado o cálculo de posição recebia `undefined`, virava NaN, e o
         SVG saía sem nenhuma linha — sem erro visível na tela. */
      nodes: rede.nos.map(function (n) {
        return { id: n.code, label: n.label, weight: n.n,
                 degree: grauNaRede(rede, n.code), color: corDaVariavel(n.code) }; }),
      links: rede.arestas.map(function (a) {
        return { source: a.a, target: a.b, weight: a.n }; }),
      height: 440, unit: "artigo(s)", file: "rede-tematica" })));

  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "conectar", "Os pares, em números", "Ordenados por quantos artigos dividem.",
    el("table", { class: "dados" }, [
      el("thead", {}, el("tr", {}, ["Par", "Artigos juntos", "Jaccard"].map(function (c, i) {
        return el("th", { text: c, style: i ? "text-align:right" : null }); }))),
      el("tbody", {}, rede.arestas.slice(0, 24).map(function (a) {
        return el("tr", {}, [
          el("td", {}, el("div", { class: "selos" }, [
            el("span", { class: "selo-var", style: "--tom:" + corDaVariavel(a.a) },
              [Icons.get(iconeDaVariavel(a.a), 12), el("span", { text: a.rotulo_a })]),
            el("span", { class: "selo-var", style: "--tom:" + corDaVariavel(a.b) },
              [Icons.get(iconeDaVariavel(a.b), 12), el("span", { text: a.rotulo_b })]),
          ])),
          el("td", { class: "num", text: String(a.n) }),
          el("td", { class: "num", text: a.jaccard.toFixed(2) }),
        ]);
      })),
    ]))));
}

/* ==================================================================== */
/* 6. mapa                                                              */
/* ==================================================================== */
function verMapa(palco) {
  const paises = ((D.panorama || {}).paises) || { top: [], todos: [] };
  palco.appendChild(cabeca("mapa", "Mapa da produção",
    "De onde vem a produção: o país da instituição de quem assina cada artigo."));

  if (!paises.todos.length) {
    palco.appendChild(nota("<b>Nenhum país para mostrar ainda.</b> O artigo não carrega "
      + "país — quem carrega é a instituição de quem assina. Assim que os integrantes e "
      + "coautores externos estiverem ligados às suas instituições na "
      + "<a href='/app#perfil'>Área do integrante</a>, as bolhas aparecem sozinhas."));
    palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
      "mapa", "O mundo, à espera dos dados",
      "O mapa fica aqui pronto; o que falta é a instituição de cada coautor.",
      C.mapaMundi({ points: [], height: 440,
        emptyMessage: "Nenhum país registrado ainda." }))));
    return;
  }
  palco.appendChild(el("div", { class: "grade g4" },
    paises.top.map(function (x, i) {
      return indicador(i === 0 ? "País mais produtivo" : x.pais, x.n,
        x.instituicoes.length + " instituição(ões)", "mapa"); })));
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "mapa", "Os cinco mais produtivos",
    "Um artigo com autores de dois países conta para os dois — foi produzido nos dois.",
    C.mapaMundi({ points: paises.top.filter(function (x) { return x.latitude !== null; })
      .map(function (x, i) {
        return { label: x.pais, lat: x.latitude, lon: x.longitude, value: x.n,
                 color: C.token("--series-" + ((i % 8) + 1)) }; }),
      height: 440, unit: "artigo(s)", file: "mapa-producao" }))));
}

/* ==================================================================== */
/* 7. síntese  8. lacunas                                               */
/* ==================================================================== */
function verSintese(palco) {
  const s = D.sintese || { achados: [] };
  palco.appendChild(cabeca("aceite", "Síntese",
    "As leituras que o dado sustenta, escritas — com o número que as sustenta ao lado, "
    + "para que possam ser contestadas."));
  palco.appendChild(el("div", { class: "grade g2" }, (s.achados || []).map(function (a) {
    return el("div", { class: "tese", style: "margin:0" }, [
      el("h3", {}, [Icons.get(a.icone || "aceite", null), el("span", { text: a.titulo })]),
      a.numero !== null && a.numero !== undefined
        ? el("div", { class: "numero", style: "margin:8px 0", text: String(a.numero) }) : null,
      el("p", { text: a.texto }),
    ]);
  })));
}

function verLacunas(palco) {
  const l = D.lacunas || { achados: [] };
  palco.appendChild(cabeca("explorar", "Lacunas e insights",
    "O que não está lá — que é mais difícil de ver do que o que está."));
  palco.appendChild(el("div", { class: "tese" }, [
    el("h3", {}, [Icons.get("alvo", null), el("span", { text: "Como usar esta aba" })]),
    el("p", { html: "Um painel mostra a produção. A pergunta que faz um laboratório andar "
      + "é a outra: <b>o que ficou de fora</b>, o que ficou pela metade, e que ponte "
      + "ninguém atravessou ainda. Nada aqui é acusação — é mapa." }),
  ]));
  if (!(l.achados || []).length) {
    palco.appendChild(nota("Nenhuma lacuna detectável com o cadastro atual."));
    return;
  }
  palco.appendChild(el("div", { class: "grade g2" }, l.achados.map(function (a) {
    return el("div", { class: "cartao" }, [
      el("h3", {}, [Icons.get(a.icone || "explorar", null), el("span", { text: a.titulo })]),
      el("div", { class: "hint", style: "margin-top:4px;line-height:1.6", text: a.texto }),
      el("div", { class: "corpo" }, el("div", { style: "display:grid;gap:6px" },
        (a.itens || []).map(function (i) {
          return el("div", { style: "display:flex;gap:9px;align-items:baseline;"
            + "padding:7px 10px;border-radius:8px;background:var(--surface)" }, [
            el("span", { style: "font-size:13px;font-weight:600", text: i.rotulo }),
            el("small", { class: "hint", style: "margin-left:auto", text: i.grupo || "" }),
          ]);
        }))),
    ]);
  })));
}

/* ==================================================================== */
/* 9. extração                                                          */
/* ==================================================================== */
function destinosDoArtigo(a) {
  const links = [];
  const doi = String(a.doi || "").replace(/^https?:\/\/(dx\.)?doi\.org\//i, "").trim();
  if (doi) links.push({ rotulo: "DOI", url: "https://doi.org/" + encodeURI(doi) });
  if (a.pmid) links.push({ rotulo: "PubMed",
    url: "https://pubmed.ncbi.nlm.nih.gov/" + encodeURIComponent(a.pmid) + "/" });
  if (a.scopus_id) links.push({ rotulo: "Scopus",
    url: "https://www.scopus.com/record/display.uri?origin=resultslist&eid="
      + encodeURIComponent(a.scopus_id) });
  if (a.wos_id) links.push({ rotulo: "Web of Science",
    url: "https://www.webofscience.com/wos/woscc/full-record/" + encodeURIComponent(a.wos_id) });
  if (a.url && !doi) links.push({ rotulo: "Link", url: a.url });
  if (!links.length && a.title) {
    links.push({ rotulo: "Procurar", busca: true,
      url: "https://scholar.google.com/scholar?q=" + encodeURIComponent('"' + a.title + '"') });
  }
  return links;
}

function artigosFiltrados(soMulti) {
  let lista = (D.artigos || []).slice();
  if (soMulti) {
    lista = lista.filter(function (a) { return (a.variaveis || []).length > 1; });
  }
  if (ST.variavel) {
    lista = lista.filter(function (a) {
      return (a.variaveis || []).some(function (v) { return v.code === ST.variavel; }); });
  }
  if (ST.linha) {
    lista = lista.filter(function (a) { return a.research_line === ST.linha; });
  }
  const busca = ST.busca.trim().toLowerCase();
  if (busca) {
    lista = lista.filter(function (a) {
      return [a.title, a.authors, a.journal, a.doi,
              (a.variaveis || []).map(function (v) { return v.label; }).join(" ")]
        .join(" ").toLowerCase().indexOf(busca) >= 0; });
  }
  const chave = ST.ordem;
  lista.sort(function (a, b) {
    let x = a[chave], y = b[chave];
    if (chave === "variaveis") { x = (a.variaveis || []).length; y = (b.variaveis || []).length; }
    if (x === null || x === undefined) x = chave === "ano" ? -1 : "";
    if (y === null || y === undefined) y = chave === "ano" ? -1 : "";
    const r = typeof x === "number" && typeof y === "number"
      ? x - y : String(x).localeCompare(String(y), "pt-BR");
    return ST.desc ? -r : r;
  });
  return lista;
}

function verExtracao(palco) {
  palco.appendChild(cabeca("dados", "Extração",
    "Todos os artigos com o que há de relevante, marcados pela variável que cada um "
    + "estuda. Clique no título e o artigo abre na base.",
    [el("div", { class: "acoes" }, [
      el("a", { class: "botao-destino", href: "/api/panorama/extracao.csv",
        download: "", rel: "noopener" },
        [Icons.get("dados", 15), el("span", { text: "CSV" })]),
      el("a", { class: "botao-destino", href: "/api/panorama/extracao.xlsx",
        download: "", rel: "noopener" },
        [Icons.get("baixar", 15), el("span", { text: "Excel (xlsx)" })]),
    ])]));

  const busca = el("input", { type: "search", placeholder: "Filtrar por título, autor, revista…",
    value: ST.busca });
  busca.oninput = function () { ST.busca = busca.value; redesenharTabelas(); };
  const linha = el("select", {}, [el("option", { value: "", text: "Todas as linhas" })]
    .concat((D.linhas || []).map(function (l) {
      return el("option", { value: l.name, text: l.name }); })));
  linha.value = ST.linha;
  linha.onchange = function () { ST.linha = linha.value; redesenharTabelas(); };

  palco.appendChild(el("div", { class: "tab-topo" }, [
    busca, linha,
    el("div", { class: "selos", style: "flex:1" },
      (D.panorama.variaveis || []).slice(0, 12).map(function (v) {
        return seloVariavel({ code: v.code, label: v.label, origem: "confirmada" },
          { aoClicar: redesenharTabelas }); })),
  ]));

  palco.appendChild(el("div", { id: "tabelas" }));
  redesenharTabelas();
}

function redesenharTabelas() {
  const alvo = document.getElementById("tabelas");
  if (!alvo) return;
  alvo.innerHTML = "";

  const todos = artigosFiltrados(false);
  const multi = artigosFiltrados(true);

  alvo.appendChild(el("h2", { style: "margin:8px 0 10px;font-size:17px",
    text: "Todos os artigos (" + todos.length + ")" }));
  alvo.appendChild(tabelaDeArtigos(todos));

  alvo.appendChild(el("h2", { style: "margin:26px 0 6px;font-size:17px",
    text: "Artigos com mais de uma variável (" + multi.length + ")" }));
  alvo.appendChild(el("p", { class: "hint", style: "margin-bottom:10px", text:
    "São estes que amarram a produção: um artigo que mede três coisas ao mesmo tempo é "
    + "o que permite ver como as três se relacionam ao longo do tempo." }));
  alvo.appendChild(multi.length ? tabelaDeArtigos(multi)
    : nota("Nenhum artigo com mais de uma variável no filtro atual."));
}

const COLUNAS = [
  { k: "title", rotulo: "Artigo", larga: true },
  { k: "variaveis", rotulo: "Variáveis" },
  { k: "research_line", rotulo: "Linha" },
  { k: "status", rotulo: "Situação" },
  { k: "journal", rotulo: "Periódico" },
  { k: "ano", rotulo: "Ano", num: true },
  { k: "submission_attempts", rotulo: "Tentativas", num: true },
];
const SITUACAO = { em_producao: "Em escrita", submetido: "Submetido",
  em_revisao: "Em revisão", aceito: "Aceito", publicado: "Publicado",
  rejeitado: "Rejeitado", arquivado: "Arquivado" };

function tabelaDeArtigos(lista) {
  const corpo = el("tbody", {}, lista.map(function (a) {
    const destinos = destinosDoArtigo(a);
    const principal = destinos[0];
    return el("tr", {}, COLUNAS.map(function (col) {
      if (col.k === "title") {
        return el("td", {}, [
          principal
            ? el("a", { class: "titulo", href: principal.url, target: "_blank",
                rel: "noopener",
                title: principal.busca ? "Sem DOI cadastrado: procura pelo título"
                                       : "Abrir em " + principal.rotulo },
                [el("span", { text: a.title }),
                 Icons.get(principal.busca ? "explorar" : "conectar", 12)])
            : el("span", { text: a.title }),
          el("small", { text: [a.authors, a.internal_code].filter(Boolean).join(" · ") }),
          destinos.length > 1 ? el("small", {}, destinos.slice(1).map(function (d) {
            return el("a", { href: d.url, target: "_blank", rel: "noopener",
              style: "margin-right:9px;font-size:11.5px", text: d.rotulo }); })) : null,
        ]);
      }
      if (col.k === "variaveis") {
        return el("td", {}, el("div", { class: "selos" },
          (a.variaveis || []).map(function (v) {
            return seloVariavel(v, { aoClicar: redesenharTabelas }); })));
      }
      if (col.k === "status") {
        return el("td", {}, el("span", { class: "badge",
          text: SITUACAO[a.status] || a.status || "—" }));
      }
      const valor = a[col.k];
      return el("td", { class: col.num ? "num" : null,
        text: valor === null || valor === undefined || valor === "" ? "—" : String(valor) });
    }));
  }));

  return el("div", { class: "rolagem" }, el("table", { class: "dados" }, [
    el("thead", {}, el("tr", {}, COLUNAS.map(function (col) {
      const seta = ST.ordem === col.k ? (ST.desc ? " ▼" : " ▲") : "";
      return el("th", {
        class: col.num ? "num" : null,
        style: col.num ? "text-align:right" : null,
        text: col.rotulo + seta,
        onclick: function () {
          if (ST.ordem === col.k) ST.desc = !ST.desc;
          else { ST.ordem = col.k; ST.desc = true; }
          redesenharTabelas();
        },
      });
    }))),
    corpo,
  ]));
}

/* ==================================================================== */
function desenhar() {
  montarNav();
  const palco = document.getElementById("palco");
  palco.innerHTML = "";
  if (!D.pronto) {
    palco.appendChild(el("p", { class: "hint", text: "Carregando o panorama…" }));
    return;
  }
  ({ visao: verVisao, laboratorio: verLaboratorio, variaveis: verVariaveis,
     curvas: verCurvas, rede: verRede, mapa: verMapa, sintese: verSintese,
     lacunas: verLacunas, extracao: verExtracao }[ST.aba] || verVisao)(palco);
}

/* ==================================================================== */
/* ao vivo                                                              */
/* ==================================================================== */
/* O painel se redesenha quando o banco muda. A conexão é a mesma do
   painel de indicadores (`/api/stream`), e o gatilho é o `change_log`:
   alguém cadastra um artigo na Área do integrante e o Panorama recalcula
   as curvas sem ninguém apertar nada.
 *
 * Duas cautelas que a experiência com o painel ensinou:
 *   - recarregar a cada evento faria o Panorama recalcular vinte vezes
 *     numa importação de planilha. Há uma espera curta que junta a rajada
 *     numa recarga só;
 *   - a aba aberta e a posição da rolagem são preservadas. Um painel que
 *     salta para o topo a cada mudança é um painel que ninguém consegue
 *     ler enquanto a equipe trabalha. */
let fonteDeEventos = null;
let recargaMarcada = null;
let aoVivo = true;

function ligarAoVivo() {
  if (!aoVivo || typeof EventSource === "undefined") return;
  try { fonteDeEventos = new EventSource("/api/stream"); } catch (erro) { return; }
  fonteDeEventos.addEventListener("pronto", function () { marcarPulso("ao vivo"); });
  fonteDeEventos.addEventListener("mudanca", function (ev) {
    let evento = "";
    try { evento = (JSON.parse(ev.data) || {}).event || ""; } catch (erro) { evento = ""; }
    marcarPulso(evento || "mudança");
    clearTimeout(recargaMarcada);
    recargaMarcada = setTimeout(recarregar, 1200);
  });
  fonteDeEventos.addEventListener("error", function () { marcarPulso("reconectando"); });
}

function desligarAoVivo() {
  if (fonteDeEventos) { fonteDeEventos.close(); fonteDeEventos = null; }
  clearTimeout(recargaMarcada);
}

async function recarregar() {
  const rolagem = window.scrollY;
  try {
    const dados = await api("/api/panorama");
    Object.assign(D, dados, { pronto: true });
    montarCores();
    desenhar();
    window.scrollTo(0, rolagem);
    marcarPulso("atualizado agora");
  } catch (erro) { /* o EventSource reconecta sozinho */ }
}

function marcarPulso(texto) {
  const alvo = document.getElementById("pulso");
  if (!alvo) return;
  alvo.textContent = texto;
  alvo.classList.add("batendo");
  setTimeout(function () { alvo.classList.remove("batendo"); }, 900);
}

function seloAoVivo() {
  const caixa = el("span", { class: "pulso" + (aoVivo ? " on" : ""), title:
    "O painel se redesenha quando alguém cadastra algo. Clique para desligar." }, [
    el("i", {}), el("span", { id: "pulso", text: aoVivo ? "ao vivo" : "parado" }),
  ]);
  caixa.onclick = function () {
    aoVivo = !aoVivo;
    if (aoVivo) { ligarAoVivo(); } else { desligarAoVivo(); }
    desenhar();
  };
  return caixa;
}

(async function inicio() {
  desenhar();
  try {
    const dados = await api("/api/panorama");
    Object.assign(D, dados, { pronto: true });
    montarCores();
    ligarAoVivo();
    const hash = location.hash.replace("#", "");
    if (ABAS.some(function (a) { return a.id === hash; })) ST.aba = hash;
    desenhar();
  } catch (erro) {
    document.getElementById("palco").appendChild(
      el("p", { class: "note erro", text: erro.message }));
  }
})();

window.addEventListener("hashchange", function () {
  const hash = location.hash.replace("#", "");
  if (ABAS.some(function (a) { return a.id === hash; })) { ST.aba = hash; desenhar(); }
});
