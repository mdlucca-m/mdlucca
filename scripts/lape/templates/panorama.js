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

/* Principal = a variável está no título (ou alguém a marcou à mão): o
   artigo É sobre ela. Secundária = só aparece no resumo, mencionada.
   Os selos do filtro não trazem esse campo e ficam sem peso nenhum. */
function pesoDaVariavel(v) {
  if (v.principal === undefined || v.principal === null) return "";
  return v.principal ? " principal" : " secundaria";
}

function seloVariavel(v, opts) {
  const conf = opts || {};
  const peso = pesoDaVariavel(v);
  const ondeDiz = peso === " principal"
    ? "Variável principal — " + (v.onde === "escolha de quem leu"
        ? "marcada por quem leu" : "está no título do artigo")
    : peso === " secundaria"
      ? "Variável secundária — aparece no resumo, não no título" : "";
  return el("span", {
    class: "selo-var" + peso + (v.origem === "auto" ? " auto" : "")
      + (ST.variavel === v.code ? " on" : ""),
    style: "--tom:" + corDaVariavel(v.code),
    title: [ondeDiz,
            v.origem === "auto" ? "Reconhecida automaticamente — " + (v.trecho || "")
                                : "Confirmada por quem leu",
            "clique para filtrar"].filter(Boolean).join(" · "),
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
  { id: "equipe", rotulo: "Equipe e ponto", icone: "relogio", grupo: "Equipe" },
];

/* A aba do ponto só aparece para quem pode abri-la. Aba que responde 403
   é pior que aba nenhuma: promete e nega. */
function abasVisiveis() {
  const papel = ((D.usuario || {}).papel) || "leitura";
  const manda = papel === "coordenacao" || papel === "admin";
  return ABAS.filter(function (a) { return a.id !== "equipe" || manda; });
}

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
  abasVisiveis().forEach(function (aba) {
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
/* O Lattes exige captcha e só sai do navegador -- não há como um programa
   buscá-lo. A mesma produção sai da PubMed por programa, e com o que o
   Lattes não tem: DOI conferido, resumo, e a afiliação que vira o país no
   mapa. Este botão existe para que trazer isso não dependa de ninguém
   abrir um terminal. */
function cartaoDaProducao() {
  const prod = D.producao || {};
  const podeGravar = ["coordenacao", "admin"]
    .indexOf(((D.usuario || {}).papel) || "leitura") >= 0;
  const corpo = el("div", {});

  corpo.appendChild(el("div", { class: "selos", style: "margin-bottom:10px" },
    (prod.pesquisadores || []).map(function (p) {
      const rotulo = p.nome + (p.ja_importados ? " · " + p.ja_importados : "");
      const dentro = [Icons.get("pessoa", 12), el("span", { text: rotulo })];
      /* Com o ID Lattes, o selo vira o caminho para conferir se é a
         pessoa certa -- que é a única pergunta que importa aqui. */
      if (!p.link_lattes) {
        return el("span", { class: "selo-var", style: "--tom:" + C.token("--series-1"),
          title: p.papel || "" }, dentro);
      }
      dentro.push(Icons.get("conectar", 11));
      return el("a", { class: "selo-var", style: "--tom:" + C.token("--series-1"),
        href: p.link_lattes, target: "_blank", rel: "noopener",
        title: (p.papel ? p.papel + " · " : "") + "abrir o currículo Lattes" }, dentro);
    })));

  const estado = el("p", { class: "hint", text: prod.artigos_de_base
    ? prod.artigos_de_base + " artigo(s) já vieram das bases, em "
      + (prod.paises_marcados || 0) + " país(es)."
    : "Nada foi trazido das bases ainda." });
  corpo.appendChild(estado);

  if (!podeGravar) {
    corpo.appendChild(el("p", { class: "hint", style: "margin-top:8px",
      text: "Quem traz a produção é a coordenação." }));
    return corpo;
  }

  const botao = el("button", { class: "botao-destino", style: "margin-top:10px" },
    [Icons.get("baixar", 15), el("span", { text: "Trazer a produção da PubMed" })]);
  botao.onclick = async function () {
    botao.disabled = true;
    estado.textContent = "Procurando na PubMed… isto leva alguns segundos.";
    try {
      const r = await api("/api/producao/importar", "POST", {});
      const linhas = (r.pessoas || []).map(function (p) {
        if (p.erro) return p.quem + ": " + p.erro;
        return p.quem + ": " + p.gravado.novos + " novo(s), "
          + p.gravado.ja_havia + " já estava(m)";
      });
      estado.textContent = linhas.join(" · ");
      await recarregar();
    } catch (erro) {
      estado.textContent = "Não deu: " + erro.message;
    } finally { botao.disabled = false; }
  };
  corpo.appendChild(botao);
  corpo.appendChild(el("p", { class: "hint", style: "margin-top:12px", html:
    "<b>E o Lattes?</b> Nenhum programa consegue baixá-lo: o CNPq exige captcha. "
    + "Ele tem o que a PubMed não indexa — capítulos, livros, orientações, "
    + "congressos. Para trazê-lo: abra o currículo pelo selo acima, clique em "
    + "<b>Exportar XML</b>, e ponha o arquivo em <code>data/raw/</code>. O sistema "
    + "acha o dono pelo ID gravado dentro do arquivo — não precisa renomear nada." }));
  return corpo;
}

function verLaboratorio(palco) {
  const lab = D.laboratorio || {};
  palco.appendChild(cabeca("instituicao", lab.nome || "O laboratório",
    "A história da produção, ano a ano. Clique num ano para abrir o que foi feito "
    + "nele e as variáveis que apareceram junto."));

  palco.appendChild(cartao("baixar", "Produção nas bases públicas",
    "O Lattes pede captcha e só sai do navegador. A PubMed entrega a mesma "
    + "produção por programa — com DOI, resumo e a afiliação que preenche o mapa.",
    cartaoDaProducao()));

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
            tituloClicavel(a, 92),
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
          tituloClicavel(a, 64)]);
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
/* O contorno do mundo é grande demais para viajar em toda visita: só é
   buscado quando alguém abre esta aba, e uma vez só. */
let mundoPedido = false;
function pedirMundo() {
  if (mundoPedido) return;
  mundoPedido = true;
  fetch("/api/geo/mundo.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (dados) {
      D.mundo = (dados || {}).paises || [];
      if (ST.aba === "mapa") desenhar();
    })
    .catch(function () { mundoPedido = false; });
}

function verMapa(palco) {
  const paises = ((D.panorama || {}).paises) || { top: [], todos: [] };
  pedirMundo();
  palco.appendChild(cabeca("mapa", "Mapa da produção",
    "De onde vem a produção: o país de quem assina cada artigo — a instituição "
    + "no cadastro, ou a afiliação que veio junto com o artigo da base. "
    + "A cor do país é a quantidade de artigos — quanto mais forte, mais produção."));

  const valores = {};
  (paises.todos || []).forEach(function (x) { valores[x.pais] = x.n; });

  if (!paises.todos.length) {
    palco.appendChild(nota("<b>Nenhum país para mostrar ainda.</b> O artigo não carrega "
      + "país — quem carrega é quem assina. Há dois caminhos, e os dois valem: "
      + "trazer a produção das bases públicas, que vem com a afiliação de cada autor "
      + "(o botão está em <a href='#laboratorio'>O laboratório</a>), ou ligar cada "
      + "integrante à sua instituição na <a href='/app#perfil'>Área do integrante</a>."));
  } else {
    palco.appendChild(el("div", { class: "grade g4" },
      paises.top.map(function (x, i) {
        /* "0 instituição(ões)" não é informação: quando o país veio da
           afiliação do artigo, e não do cadastro, não há instituição
           ligada — e dizer zero parece defeito. */
        const pe = x.instituicoes.length
          ? x.instituicoes.length + " instituição(ões)"
          : (i === 0 ? x.pais : "artigos com autor daqui");
        return indicador(i === 0 ? "País mais produtivo" : x.pais, x.n, pe, "mapa"); })));
  }

  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "mapa", paises.todos.length ? "Onde a produção acontece" : "O mundo, à espera dos dados",
    "Um artigo com autores de dois países conta para os dois — foi produzido nos dois.",
    C.mapaMundi({
      world: D.mundo || [],
      values: valores,
      unit: "artigos",
      file: "mapa-producao",
      emptyMessage: "Nenhum país registrado ainda.",
      emptyHint: "Falta ligar cada coautor à instituição dele.",
      onSelect: function (nome) { ST.busca = nome; ST.aba = "extracao"; desenhar(); },
      table: paises.todos.length ? {
        cols: ["País", "Artigos", "Instituições"],
        rows: paises.todos.map(function (x) {
          return [x.pais, x.n, x.instituicoes.join("; ")]; }),
      } : null,
    }))));
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
/* Para onde o clique leva, na ordem de quem quer LER o artigo:
   o texto completo livre primeiro, a página da editora depois, e as bases
   por último. Mandar quem vai ler para o resumo atrás do paywall quando há
   PDF livre no PMC é o tipo de detalhe que faz a pessoa desistir. */
/* Cada base tem o seu jeito de abrir um artigo, e nenhum deles se
   adivinha: o DOI resolve para a editora, o PMC abre o texto completo de
   graça, o Scopus só abre pelo id dele. Aqui viram botões, um por base,
   com o que existe cadastrado -- e o que não existe simplesmente não
   aparece, em vez de virar um link quebrado. */
function destinosDoArtigo(a) {
  const links = [];
  const doi = String(a.doi || "").replace(/^https?:\/\/(dx\.)?doi\.org\//i, "").trim();
  const pmc = String(a.pmc || "").trim();
  if (doi) {
    links.push({ rotulo: "DOI", chave: "doi", icone: "conectar", editora: true,
      dica: "Abre na página da editora — " + doi,
      url: "https://doi.org/" + encodeURI(doi) });
  }
  if (pmc) {
    links.push({ rotulo: "PMC", chave: "pmc", icone: "baixar", livre: true,
      dica: "Texto completo de graça no PubMed Central — " + pmc,
      url: "https://www.ncbi.nlm.nih.gov/pmc/articles/" + encodeURIComponent(pmc) + "/" });
  } else if (a.oa_url) {
    links.push({ rotulo: "Texto completo", chave: "oa", icone: "baixar", livre: true,
      dica: "Texto completo de graça", url: a.oa_url });
  }
  if (a.pmid) {
    links.push({ rotulo: "PubMed", chave: "pubmed", icone: "explorar",
      dica: "Registro na PubMed — PMID " + a.pmid,
      url: "https://pubmed.ncbi.nlm.nih.gov/" + encodeURIComponent(a.pmid) + "/" });
  }
  if (a.scopus_id) {
    links.push({ rotulo: "Scopus", chave: "scopus", icone: "explorar",
      dica: "Registro na Scopus",
      url: "https://www.scopus.com/record/display.uri?origin=resultslist&eid="
        + encodeURIComponent(a.scopus_id) });
  } else if (doi) {
    /* sem o EID não há link direto: a Scopus só abre o registro pelo id
       dela. Pelo DOI dá para procurar, e a busca vem marcada como busca --
       prometer "abre o artigo" e cair numa lista é pior que avisar. */
    links.push({ rotulo: "Scopus", chave: "scopus", icone: "explorar", busca: true,
      dica: "Sem o id da Scopus cadastrado: procura pelo DOI",
      url: "https://www.scopus.com/results/results.uri?st1="
        + encodeURIComponent(doi) + "&sot=b&sdt=b&sl=" + (doi.length + 4)
        + "&s=" + encodeURIComponent("DOI(" + doi + ")") });
  }
  if (a.wos_id) {
    links.push({ rotulo: "Web of Science", chave: "wos", icone: "explorar",
      dica: "Registro na Web of Science",
      url: "https://www.webofscience.com/wos/woscc/full-record/"
        + encodeURIComponent(a.wos_id) });
  } else if (doi) {
    links.push({ rotulo: "Web of Science", chave: "wos", icone: "explorar", busca: true,
      dica: "Sem o id da Web of Science cadastrado: procura pelo DOI",
      url: "https://www.webofscience.com/wos/woscc/general-search?search_mode=general"
        + "&q=" + encodeURIComponent("DO=(" + doi + ")") });
  }
  if (a.url && !doi) {
    links.push({ rotulo: "Página do artigo", chave: "url", icone: "conectar",
      editora: true, dica: a.url, url: a.url });
  }
  if (!links.length && a.title) {
    links.push({ rotulo: "Procurar no Google Acadêmico", chave: "scholar",
      icone: "explorar", busca: true,
      dica: "Nenhum identificador cadastrado: procura pelo título",
      url: "https://scholar.google.com/scholar?q=" + encodeURIComponent('"' + a.title + '"') });
  }
  return links;
}

/* O clique no título vai para onde o artigo FOI PUBLICADO -- o DOI, que
   resolve para a editora. O texto livre continua a um clique, no botão
   verde ao lado; ele é outra coisa (uma cópia), e trocar um pelo outro
   faria o título mentir sobre onde o trabalho saiu. */
function destinoDoTitulo(destinos) {
  return destinos.find(function (d) { return d.editora; })
    || destinos.find(function (d) { return !d.busca; })
    || destinos[0] || null;
}

/* O título é clicável em toda parte onde ele aparece -- a linha do
   tempo e o organograma inclusive. Quando não há identificador nenhum,
   fica texto: um link que só abre uma busca promete o que não cumpre. */
function tituloClicavel(a, limite) {
  const rotulo = limite ? cortar(a.title, limite) : a.title;
  const destino = destinoDoTitulo(destinosDoArtigo(a));
  if (!destino || destino.busca) return el("span", { text: rotulo });
  return el("a", { class: "titulo-artigo", href: destino.url, target: "_blank",
    rel: "noopener", title: "Abre em " + destino.rotulo,
    onclick: function (ev) { ev.stopPropagation(); } }, [
    el("span", { text: rotulo }), Icons.get("conectar", 11),
  ]);
}

function botoesDeBase(destinos) {
  return el("div", { class: "bases" }, destinos.map(function (d) {
    return el("a", {
      class: "base" + (d.livre ? " livre" : "") + (d.busca ? " busca" : ""),
      href: d.url, target: "_blank", rel: "noopener",
      title: d.dica + (d.busca ? " (abre uma busca, não o artigo)" : ""),
    }, [Icons.get(d.icone, 12), el("span", { text: d.rotulo })]);
  }));
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

  palco.appendChild(legendaDosSelos());
  palco.appendChild(el("div", { id: "tabelas" }));
  redesenharTabelas();
}

/* Sem esta legenda o destaque vira enfeite: quem olha a tabela precisa
   saber o que a marca mais forte está afirmando sobre o artigo. */
function legendaDosSelos() {
  const modelo = function (principal, label) {
    return el("span", { class: "selo-var " + (principal ? "principal" : "secundaria"),
      style: "--tom:" + C.token("--series-1") },
      [Icons.get("alvo", 12), el("span", { text: label })]);
  };
  return el("div", { class: "legenda-selos" }, [
    modelo(true, "Variável principal"),
    el("span", { text: "está no título — o artigo é sobre ela" }),
    modelo(false, "Variável secundária"),
    el("span", { text: "aparece só no resumo — é mencionada" }),
  ]);
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
    const doTitulo = destinoDoTitulo(destinos);
    return el("tr", {}, COLUNAS.map(function (col) {
      if (col.k === "title") {
        return el("td", {}, [
          doTitulo
            ? el("a", { class: "titulo" + (doTitulo.busca ? " incerto" : ""),
                href: doTitulo.url, target: "_blank", rel: "noopener",
                title: doTitulo.busca ? doTitulo.dica : "Abre em " + doTitulo.rotulo },
                [el("span", { text: a.title }),
                 Icons.get(doTitulo.busca ? "explorar" : "conectar", 12)])
            : el("span", { text: a.title }),
          el("small", {}, [
            el("span", { text: [a.authors, a.internal_code].filter(Boolean).join(" · ") }),
            a.open_access ? el("span", { class: "livre", title:
              "Acesso aberto" + (a.oa_status ? " (" + a.oa_status + ")" : "")
              + " — o texto completo está disponível de graça",
              text: "acesso aberto" }) : null,
          ]),
          destinos.length ? botoesDeBase(destinos) : null,
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
/* Equipe e ponto — a leitura da coordenação                            */
/*                                                                      */
/* Hora registrada não é produtividade, e este painel não finge que é:  */
/* as horas de um lado, o que saiu de trabalho do outro. Um ranking de  */
/* horas sozinho ensinaria a ficar sentado, que não é o que se quer.    */
/* ==================================================================== */
let EQUIPE = null;

function horasCurtas(h) {
  if (h === null || h === undefined) return "—";
  if (h < 1) return Math.round(h * 60) + " min";
  const inteiras = Math.floor(h), min = Math.round((h - inteiras) * 60);
  return inteiras + "h" + (min ? String(min).padStart(2, "0") : "");
}

function verEquipe(palco) {
  palco.appendChild(cabeca("relogio", "Equipe e ponto",
    "Quem está no laboratório agora, e quantas horas cada pessoa registrou. "
    + "Hora registrada não é produção — o que saiu de trabalho está ao lado, "
    + "de propósito separado."));

  if (!EQUIPE) {
    palco.appendChild(el("p", { class: "hint", text: "Carregando o ponto da equipe…" }));
    api("/api/ponto/equipe").then(function (dados) {
      EQUIPE = dados;
      if (ST.aba === "equipe") desenhar();
    }).catch(function (erro) {
      EQUIPE = { erro: erro.message, pessoas: [], agora: [], serie: [] };
      if (ST.aba === "equipe") desenhar();
    });
    return;
  }
  if (EQUIPE.erro) {
    palco.appendChild(nota("<b>Não deu para ler o ponto.</b> " + EQUIPE.erro
      + " — esta aba é da coordenação."));
    return;
  }

  const r = EQUIPE.resumo || {};
  palco.appendChild(el("div", { class: "grade g4" }, [
    indicador("No laboratório agora", (EQUIPE.agora || []).length,
      "com entrada em aberto", "pessoas"),
    indicador("Horas hoje", horasCurtas((r.dia || {}).horas), "de todo o laboratório", "relogio"),
    indicador("Horas na semana", horasCurtas((r.semana || {}).horas),
      variacaoCurta((r.semana || {}).variacao), "relogio"),
    indicador("Horas no mês", horasCurtas((r.mes || {}).horas),
      variacaoCurta((r.mes || {}).variacao), "relogio"),
  ]));

  /* ---- quem está dentro, agora ---- */
  const vivos = EQUIPE.agora || [];
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "pessoas", "No laboratório agora (" + vivos.length + ")",
    "Atualiza sozinho quando alguém marca entrada ou saída.",
    vivos.length
      ? el("div", { class: "agora" }, vivos.map(function (x) {
          return el("div", { class: "quem-agora" }, [
            el("span", { class: "pulso-vivo" }),
            el("div", {}, [
              el("b", { text: x.quem }),
              el("small", { text: (x.atividade || "sem anotar o que está fazendo")
                + " · há " + horasCurtas(x.ha_horas) }),
            ]),
          ]);
        }))
      : el("p", { class: "hint", text: "Ninguém com entrada em aberto." }))));

  /* ---- horas por pessoa ---- */
  const pessoas = EQUIPE.pessoas || [];
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "barras", "Horas registradas por pessoa (" + EQUIPE.dias + " dias)",
    "A barra é tempo, não resultado. Quem aparece pouco pode estar trabalhando "
    + "fora do laboratório — o ponto só sabe o que foi marcado.",
    pessoas.length
      ? C.bars({
          /* `bars` lê `items`, não `labels`/`series` como `columns` --
             passar a forma errada não dá erro, desenha "sem dados". */
          items: pessoas.map(function (x) {
            return { label: x.quem, value: x.horas }; }),
          /* Uma cor só: todas as barras são a MESMA medida (horas). Cor
             diferente por barra diria que são coisas diferentes, e quatro
             matizes num ranking viram enfeite que atrapalha a leitura. */
          mono: true, unit: "h",
          table: { cols: ["Pessoa", "Horas", "Dias com registro", "Média por dia",
                          "Sem saída"],
                   rows: pessoas.map(function (x) {
                     return [x.quem, x.horas, x.dias_com_registro, x.media_por_dia,
                             x.esquecidas]; }) },
        })
      : el("p", { class: "hint", text: "Nenhuma hora registrada no período." }))));

  /* ---- a curva do laboratório ---- */
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "linhas", "Horas do laboratório, dia a dia",
    "Dia sem registro entra como zero — série que pula os vazios desenha "
    + "trabalho que não houve.",
    C.lines({
      labels: (EQUIPE.serie || []).map(function (x) { return x.dia.slice(5); }),
      series: [{ name: "Horas registradas",
                 values: (EQUIPE.serie || []).map(function (x) { return x.horas; }) }],
      height: 240, unit: "h",
    }))));

  /* ---- e o que saiu de trabalho no mesmo período ---- */
  const prod = EQUIPE.producao || {};
  palco.appendChild(el("h2", { style: "margin:26px 0 10px;font-size:17px",
    text: "O que saiu de trabalho nos mesmos " + EQUIPE.dias + " dias" }));
  palco.appendChild(el("div", { class: "grade g4" }, [
    indicador("Publicados", prod.publicados || 0, "no período", "producao"),
    indicador("Aceitos", prod.aceitos || 0, "no período", "aceite"),
    indicador("Submetidos", prod.submetidos || 0, "no período", "submissao"),
    indicador("Iniciados", prod.iniciados || 0, "no período", "foguete"),
  ]));
}

function variacaoCurta(v) {
  if (v === null || v === undefined) return "sem base para comparar";
  return (v > 0 ? "▲ " : v < 0 ? "▼ " : "= ") + Math.abs(v).toFixed(0) + "% ante o anterior";
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
     lacunas: verLacunas, extracao: verExtracao,
     equipe: verEquipe }[ST.aba] || verVisao)(palco);
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
