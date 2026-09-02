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
             so_multi: false, linha: "", abertos: {}, pais: null };

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
  { id: "projetos", rotulo: "Projetos e extensão", icone: "projeto", grupo: "Contexto" },
  { id: "curvas", rotulo: "Curvas e derivadas", icone: "linhas", grupo: "Análise" },
  { id: "funil", rotulo: "Incidência e prevalência", icone: "processo", grupo: "Análise" },
  { id: "triangulo", rotulo: "Triangulação", icone: "hierarquia", grupo: "Análise" },
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
    (D.laboratorio || {}).logo
      ? el("div", { class: "selo tem-logo" },
          el("img", { class: "logo-img", src: D.laboratorio.logo,
            alt: D.laboratorio.nome || "LAPE" }))
      : el("div", { class: "selo", text: "LP" }),
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
      /* a aba tem nome proprio no HTML: o rotulo muda quando muda a
         redacao, e ai qualquer coisa que aponte para ele quebra */
      "data-aba": aba.id, "aria-current": ST.aba === aba.id ? "page" : null,
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

/* ==================================================================== */
/* Raio-X analítico                                                     */
/*                                                                      */
/* Um indicador sozinho é um número; vários sem a base são vários       */
/* números. Cada medida aqui traz o N que a sustenta e a leitura em     */
/* português — "2,8 variáveis por artigo" não diz nada a quem não sabe  */
/* que acima de 2 a produção é combinatória.                            */
/* ==================================================================== */
function raioX() {
  const r = D.raio_x || { medidas: [], travessia: [] };
  const prontas = r.medidas.filter(function (m) { return m.confiavel; });
  const faltando = r.medidas.filter(function (m) { return !m.confiavel; });

  const bloco = el("div", { style: "margin-top:14px" });
  bloco.appendChild(cartao("achado", "Raio-X analítico",
    "Oito medidas sobre a mesma produção, cada uma com a base que a sustenta. "
    + "Medida sem base não sai com um número pequeno: sai dizendo que ainda "
    + "não dá para dizer.",
    el("div", {}, [
      el("div", { class: "grade g3" }, prontas.map(function (m) {
        return el("div", { class: "medida" }, [
          el("div", { class: "topo" }, [
            Icons.get(m.icone || "achado", 15),
            el("span", { class: "rotulo", text: m.rotulo }),
          ]),
          el("div", { class: "valor" }, [
            el("b", { text: formatarMedida(m.valor) }),
            el("small", { text: m.unidade }),
          ]),
          el("p", { class: "hint", text: m.leitura || "" }),
          el("p", { class: "base", text: "base: " + m.base + " artigo(s)" }),
        ]);
      })),
      faltando.length ? el("div", { class: "sem-base" }, [
        el("b", { text: "Ainda sem base para " + faltando.length + " medida(s)" }),
        el("ul", {}, faltando.map(function (m) {
          return el("li", {}, [
            el("span", { text: m.rotulo + " — " }),
            el("em", { text: m.porque || "" }),
          ]);
        })),
      ]) : null,
    ])));

  /* ---- onde o tempo fica ---- */
  const medidas = (r.travessia || []).filter(function (e) { return e.confiavel; });
  if (medidas.length) {
    const maior = medidas.reduce(function (a, b) { return b.dias > a.dias ? b : a; });
    bloco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
      "relogio", "Onde o tempo fica",
      "Mediana de dias em cada etapa. O maior vão é onde o artigo espera.",
      C.bars({
        items: medidas.map(function (e) {
          return { label: e.etapa, value: Math.round(e.dias) }; }),
        mono: true, unit: "dias",
        table: { cols: ["Etapa", "Dias (mediana)", "Artigos"],
                 rows: medidas.map(function (e) {
                   return [e.etapa, Math.round(e.dias), e.base]; }) },
      }))));
    bloco.appendChild(el("p", { class: "hint", style: "margin-top:-6px",
      text: "Gargalo: " + maior.etapa + ", " + Math.round(maior.dias)
        + " dias na mediana." }));
  }
  return bloco;
}

function formatarMedida(valor) {
  if (valor === null || valor === undefined) return "—";
  const n = Number(valor);
  return Number.isInteger(n) ? String(n) : n.toFixed(1).replace(".", ",");
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

  palco.appendChild(raioX());

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

/* ------------------------------------------------------------------ */
/* Citações das bases proprietárias                                     */
/* A PubMed e a OpenAlex são abertas; Scopus e Web of Science não. Elas
   pedem chave, e a chave costuma vir da assinatura da universidade. O que
   este cartão faz de diferente é dizer, ANTES de alguém apertar, o que vai
   impedir a coleta -- porque as três coisas que a impedem (não há chave,
   não há DOI, a chave não vale) devolvem o mesmo "0 atualizados" se a tela
   ficar calada até o fim. */
function cartaoDasCitacoes() {
  const cit = D.citacoes || {};
  const podeGravar = ["coordenacao", "admin"]
    .indexOf(((D.usuario || {}).papel) || "leitura") >= 0;
  const corpo = el("div", {});

  const selos = el("div", { class: "selos", style: "margin-bottom:10px" },
    (cit.fontes || []).map(function (f) {
      const ligada = f.configurada;
      return el("span", {
        class: "selo-var",
        style: "--tom:" + C.token(ligada ? "--good" : "--ink-muted"),
        title: ligada ? "chave presente em " + f.variavel
          : "falta a variável de ambiente " + f.variavel,
      }, [Icons.get(ligada ? "conectar" : "aviso", 12),
        el("span", { text: f.rotulo + (ligada ? " · ligada" : " · sem chave") }),
        f.artigos_com_numero
          ? el("small", { text: " " + f.artigos_com_numero + " artigo(s)" }) : null]);
    }));
  corpo.appendChild(selos);

  const estado = el("p", { class: "hint" });
  function contar() {
    const c = D.citacoes || {};
    const partes = [];
    (c.fontes || []).forEach(function (f) {
      if (f.citacoes) partes.push(f.rotulo + ": " + f.citacoes + " citações");
    });
    estado.textContent = partes.length
      ? partes.join(" · ") + (c.atualizado_em ? " · conferido em " + c.atualizado_em : "")
      : "Nenhum número veio dessas bases ainda.";
  }
  contar();
  corpo.appendChild(estado);

  /* A consulta é por DOI. Sem DOI não há o que perguntar, e este é o
     estado do banco hoje -- dizer isso aqui poupa a rodada inteira. */
  const semChave = (cit.fontes || []).every(function (f) { return !f.configurada; });
  const semDoi = !cit.com_doi;

  if (semDoi && cit.artigos) {
    corpo.appendChild(el("p", { class: "nota-honesta", style: "margin-top:10px", html:
      "<b>Nenhum dos " + cit.artigos + " artigos tem DOI.</b> A consulta às duas bases é "
      + "por DOI — é a única chave que não confunde um artigo com o homônimo de outro "
      + "grupo. Preencha a coluna <code>doi</code> na planilha, ou traga a produção da "
      + "PubMed no cartão acima: ela vem com o DOI conferido." }));
  }

  if (!podeGravar) {
    corpo.appendChild(el("p", { class: "hint", style: "margin-top:8px",
      text: "Quem conecta as bases é a coordenação." }));
    return corpo;
  }

  if (semChave) {
    corpo.appendChild(el("p", { class: "hint", style: "margin-top:10px", html:
      "<b>Como ligar.</b> Ponha as chaves no arquivo <code>.env</code>, na raiz do "
      + "sistema, uma por linha:<br>"
      + "<code>SCOPUS_API_KEY=…</code> — grátis em dev.elsevier.com; a contagem "
      + "completa só sai de dentro da rede da universidade, ou com "
      + "<code>SCOPUS_INST_TOKEN=…</code>, que a biblioteca pede à Elsevier.<br>"
      + "<code>WOS_API_KEY=…</code> — Web of Science Starter API, no portal da "
      + "Clarivate; depende da assinatura da UDESC.<br>"
      + "Depois reinicie o sistema. As chaves ficam só nesta máquina — o "
      + "<code>.env</code> não vai para o repositório." }));
    return corpo;
  }

  const botao = el("button", { class: "botao-destino", style: "margin-top:10px" },
    [Icons.get("atualizar", 15), el("span", { text: "Conferir as citações agora" })]);
  botao.disabled = semDoi;
  botao.onclick = async function () {
    botao.disabled = true;
    estado.textContent = "Perguntando às bases, artigo por artigo… "
      + cit.com_doi + " DOI(s) a conferir.";
    try {
      const r = await api("/api/citacoes/atualizar", "POST", {});
      D.citacoes = r.situacao || D.citacoes;
      const recusadas = Object.keys(r.recusadas || {});
      contar();
      const linha = ["Scopus: " + r.scopus, "WoS: " + r.wos];
      if (r.erros) linha.push(r.erros + " erro(s)");
      estado.textContent = linha.join(" · ") + " — de " + r.consultados + " DOI(s).";
      if (recusadas.length) {
        /* a chave recusada é o único desfecho que não se resolve tentando
           de novo, e é o que a pessoa precisa ler inteiro */
        recusadas.forEach(function (k) {
          corpo.appendChild(el("p", { class: "nota-honesta", style: "margin-top:8px",
            text: r.recusadas[k] }));
        });
      }
      await recarregar();
    } catch (erro) {
      estado.textContent = "Não deu: " + erro.message;
    } finally { botao.disabled = semDoi; }
  };
  corpo.appendChild(botao);
  if (semDoi) {
    corpo.appendChild(el("p", { class: "hint", style: "margin-top:6px",
      text: "O botão liga quando houver ao menos um artigo com DOI." }));
  }
  return corpo;
}

/* ------------------------------------------------------------------ */
/* A marca do laboratório                                               */
/* O arquivo poderia ser copiado à mão para data/logo.png, e por muito
   tempo foi só isso. Mas quem cuida do laboratório usa este sistema pelo
   navegador, num computador Windows, e "abra o terminal e copie o arquivo
   para a pasta data" é um pedido que não se atende sozinho. A imagem entra
   por aqui, do mesmo lugar onde ela já está. */
function cartaoDaMarca() {
  const est = (D.laboratorio || {}).marca || {};
  const podeGravar = ["coordenacao", "admin"]
    .indexOf(((D.usuario || {}).papel) || "leitura") >= 0;
  const corpo = el("div", {});

  const mostra = el("div", { class: "marca-previa" });
  function desenharPrevia() {
    mostra.innerHTML = "";
    const src = (D.laboratorio || {}).logo;
    mostra.appendChild(src
      ? el("img", { class: "logo-img", src: src,
          alt: (D.laboratorio || {}).nome || "LAPE" })
      : el("span", { class: "sem-logo", text: "LP" }));
  }
  desenharPrevia();

  const estado = el("p", { class: "hint" });
  function dizer(texto) { estado.textContent = texto; }
  dizer(est.tem ? "Aparece no painel, no panorama, no mural, na entrada e no convite."
    : "Sem arquivo, as telas ficam com as duas letras.");

  corpo.appendChild(el("div", { class: "marca-linha" }, [mostra, estado]));

  if (est.erro) {
    corpo.appendChild(nota("<b>O arquivo que está lá não entrou.</b> " + est.erro + "."));
  }

  if (!podeGravar) {
    corpo.appendChild(el("p", { class: "hint", style: "margin-top:8px",
      text: "Quem troca a marca é a coordenação." }));
    return corpo;
  }

  const escolher = el("input", { type: "file", accept: ".png,.svg,.webp,.jpg,.jpeg,image/*",
    style: "display:none", id: "arquivoDaMarca" });
  const botao = el("button", { class: "botao-destino", style: "margin-top:10px" },
    [Icons.get("baixar", 15),
     el("span", { text: est.tem ? "Trocar a imagem" : "Enviar a imagem" })]);
  botao.onclick = function () { escolher.click(); };

  escolher.onchange = function () {
    const arquivo = escolher.files && escolher.files[0];
    if (!arquivo) return;
    /* O teto é conferido aqui TAMBÉM, e não só no servidor: mandar 4 MB
       pela rede para ouvir "não" é uma espera que não precisava existir. */
    if (arquivo.size > (est.limite_kb || 512) * 1024) {
      dizer("Esse arquivo tem " + Math.round(arquivo.size / 1024) + " kB e o limite é "
        + (est.limite_kb || 512) + " kB. Ele entra embutido em cada página e em cada "
        + "instantâneo que sai daqui.");
      escolher.value = "";
      return;
    }
    const leitor = new FileReader();
    leitor.onerror = function () { dizer("Não consegui ler o arquivo."); };
    leitor.onload = async function () {
      botao.disabled = true;
      dizer("Enviando…");
      try {
        const r = await api("/api/marca", "POST", { arquivo: String(leitor.result) });
        /* a resposta traz a situação, mas não a imagem: recarregar é o que
           faz a marca nova aparecer nesta tela e no menu ao lado */
        dizer(r.tem ? "Pronto. A marca já está em todas as telas."
          : "O arquivo não entrou.");
        await recarregar();
        desenhar();
      } catch (erro) {
        dizer("Não deu: " + erro.message);
      } finally { botao.disabled = false; escolher.value = ""; }
    };
    leitor.readAsDataURL(arquivo);
  };
  corpo.appendChild(escolher);
  corpo.appendChild(botao);

  if (est.tem) {
    const tirar = el("button", { class: "ghost", style: "margin:10px 0 0 8px" },
      [Icons.get("filtro", 14), el("span", { text: "Tirar" })]);
    tirar.onclick = async function () {
      tirar.disabled = true;
      try {
        await api("/api/marca", "POST", { remover: true });
        await recarregar();
        desenhar();
      } catch (erro) { dizer("Não deu: " + erro.message); }
      finally { tirar.disabled = false; }
    };
    corpo.appendChild(tirar);
  }

  corpo.appendChild(el("p", { class: "hint", style: "margin-top:10px", html:
    "PNG, SVG, WEBP ou JPG, até " + (est.limite_kb || 512) + " kB. O SVG é o que "
    + "não perde nitidez no mural, que roda numa tela grande. A imagem viaja "
    + "<b>dentro</b> de cada página — é o que faz a marca aparecer também no "
    + "instantâneo que você manda por e-mail e no mural rodando sem rede." }));
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

  palco.appendChild(cartao("etiqueta", "A marca do laboratório",
    "O logotipo aparece no painel, no panorama, no mural, na tela de entrada e no "
    + "convite. Sem arquivo, ficam as duas letras.",
    cartaoDaMarca()));

  palco.appendChild(cartao("citacao", "Citações na Scopus e na Web of Science",
    "As duas bases fechadas não deixam contar de fora: pedem chave, e a chave "
    + "vem da assinatura da universidade. Ligadas, elas respondem por DOI.",
    cartaoDasCitacoes()));

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
/* Esta aba tem estado proprio: quais series estao no palco e ate que ano
   a curva ja foi tracada. O estado vive fora da funcao porque `desenhar()`
   esvazia o palco a cada evento do banco -- e um filtro que se perde a
   cada artigo cadastrado nao e filtro. */
const CURVA = { escolhidas: null, quadro: null, tocando: false, animar: true };
let relogioDaCurva = null;

function pararACurva() {
  if (relogioDaCurva) { clearInterval(relogioDaCurva); relogioDaCurva = null; }
  CURVA.tocando = false;
}

function poucoMovimento() {
  return typeof matchMedia === "function"
    && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* O tracado que cresce da esquerda para a direita. Nao e enfeite: e a
   unica forma de ver a ORDEM em que as coisas aconteceram sem ler o eixo
   ponto a ponto. Quem pediu menos movimento recebe a curva pronta. */
function animarTracado(no) {
  if (poucoMovimento()) return;
  const caminhos = no.querySelectorAll("svg.plot path[stroke]");
  Array.prototype.forEach.call(caminhos, function (caminho, i) {
    let comprimento = 0;
    try { comprimento = caminho.getTotalLength(); } catch (erro) { return; }
    if (!comprimento) return;
    caminho.style.strokeDasharray = comprimento;
    caminho.style.strokeDashoffset = comprimento;
    caminho.style.transition = "stroke-dashoffset .6s ease-out " + (i * 0.07) + "s";
    requestAnimationFrame(function () { caminho.style.strokeDashoffset = "0"; });
  });
}

function verCurvas(palco) {
  const p = D.panorama;
  const anos = p.janela.anos.map(String);
  const todas = (p.variaveis || []).filter(function (v) { return v.total > 0; });
  const principais = todas.slice(0, 6).map(function (v) { return v.code; });

  if (CURVA.escolhidas === null) CURVA.escolhidas = principais.slice();
  /* variavel que sumiu do recorte nao pode continuar marcada */
  CURVA.escolhidas = CURVA.escolhidas.filter(function (c) {
    return todas.some(function (v) { return v.code === c; }); });
  if (CURVA.quadro === null || CURVA.quadro > anos.length - 1) {
    CURVA.quadro = anos.length - 1;
  }

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

  if (!todas.length || !todas.some(function (v) { return v.confiavel; })) {
    palco.appendChild(nota("<b>Ainda não há série que sustente derivada.</b> "
      + "Nenhuma variável tem produção em três anos distintos dentro do recorte. "
      + "A história completa do laboratório está no <b>Lattes da equipe</b> — importá-lo "
      + "traz a publicação de cada integrante ano a ano, e estas curvas passam a ter o "
      + "que analisar. Enquanto isso, os cartões abaixo mostram a série crua."));
  }

  if (!todas.length) { curvasSemSerie(palco); return; }

  /* ---- o palco que se redesenha: filtro e navegação mexem só nele ---- */
  const painel = el("div", { class: "curva-palco" });
  palco.appendChild(el("div", { class: "curva-controles" },
    [filtroDeSeries(todas, redesenhar), navegacaoDoTempo(anos, redesenhar)]));
  palco.appendChild(painel);

  function redesenhar(comAnimacao) {
    CURVA.animar = comAnimacao !== false;
    painel.innerHTML = "";
    desenharCurvas(painel, p, anos, todas);
    atualizarControles(todas, anos);
  }
  redesenhar(true);

  /* "Tudo automatizado": ao abrir a aba pela primeira vez a série se
     desenha sozinha, ano a ano. Uma vez -- repetir a cada recarga do
     painel ao vivo seria um gráfico que nunca para quieto. */
  if (!CURVA.jaTocou && anos.length > 2 && !poucoMovimento()) {
    CURVA.jaTocou = true;
    CURVA.quadro = 0;
    tocarACurva(redesenhar);
  }

  curvasSemSerie(palco);
  palco.appendChild(el("div", { style: "margin-top:14px" },
    cartaoDoDendrograma()));
  /* Os dois desenhos vao um embaixo do outro, e nao lado a lado: cada um
     tem a sua largura natural, e em meia coluna a letra sumiria. */
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartaoDoMetodo(p, todas)));
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartaoDaDecisao(todas)));
}

/* ---- chips: cada variável entra e sai do palco com um toque ---- */
function filtroDeSeries(todas, redesenhar) {
  const caixa = el("div", { class: "filtro-series" });
  caixa.appendChild(el("span", { class: "rotulo-filtro" },
    [Icons.get("filtro", 13), el("span", { text: "Séries no gráfico" })]));

  const rapidos = el("div", { class: "atalhos" });
  [["Todas", function () { return todas.map(function (v) { return v.code; }); }],
   ["Principais", function () {
     return todas.slice(0, 6).map(function (v) { return v.code; }); }],
   ["Só as confiáveis", function () {
     return todas.filter(function (v) { return v.confiavel; })
       .map(function (v) { return v.code; }); }],
   ["Nenhuma", function () { return []; }],
  ].forEach(function (par) {
    rapidos.appendChild(el("button", {
      type: "button", class: "ghost", text: par[0],
      onclick: function () { CURVA.escolhidas = par[1](); redesenhar(true); },
    }));
  });
  caixa.appendChild(rapidos);

  const selos = el("div", { class: "selos", "data-selos-curva": "1" });
  todas.forEach(function (v) {
    const marcado = CURVA.escolhidas.indexOf(v.code) >= 0;
    const selo = el("button", {
      type: "button", class: "selo-var" + (marcado ? " on" : ""),
      "data-code": v.code, style: "--tom:" + corDaVariavel(v.code),
      "aria-pressed": String(marcado),
      title: v.confiavel ? "série confiável" : (v.porque || "sem base para derivada"),
      onclick: function () {
        const i = CURVA.escolhidas.indexOf(v.code);
        if (i >= 0) CURVA.escolhidas.splice(i, 1); else CURVA.escolhidas.push(v.code);
        redesenhar(true);
      },
    }, [Icons.get(iconeDaVariavel(v.code), 12),
        el("span", { text: v.label }),
        el("small", { text: String(v.total) })]);
    selos.appendChild(selo);
  });
  caixa.appendChild(selos);
  return caixa;
}

/* ---- navegação no tempo: passo a passo, ou sozinho ---- */
function navegacaoDoTempo(anos, redesenhar) {
  const caixa = el("div", { class: "nav-tempo" });
  const irPara = function (i) {
    CURVA.quadro = Math.max(0, Math.min(anos.length - 1, i));
    redesenhar(false);
  };
  caixa.appendChild(el("button", {
    type: "button", class: "ghost", title: "Ano anterior", "data-nav": "antes",
    onclick: function () { pararACurva(); irPara(CURVA.quadro - 1); },
  }, [Icons.get("anterior", 14)]));
  caixa.appendChild(el("button", {
    type: "button", class: "primary", "data-nav": "tocar",
    onclick: function () {
      if (CURVA.tocando) { pararACurva(); redesenhar(false); }
      else {
        if (CURVA.quadro >= anos.length - 1) CURVA.quadro = 0;
        tocarACurva(redesenhar);
      }
    },
  }, [Icons.get("tocar", 14), el("span", { text: "Tocar" })]));
  caixa.appendChild(el("button", {
    type: "button", class: "ghost", title: "Próximo ano", "data-nav": "depois",
    onclick: function () { pararACurva(); irPara(CURVA.quadro + 1); },
  }, [Icons.get("proximo", 14)]));

  const cursor = el("input", {
    type: "range", min: "0", max: String(Math.max(0, anos.length - 1)),
    value: String(CURVA.quadro), class: "cursor-ano",
    "aria-label": "Ano até onde a curva é traçada",
    oninput: function (ev) { pararACurva(); irPara(Number(ev.target.value)); },
  });
  caixa.appendChild(cursor);
  caixa.appendChild(el("span", { class: "ano-corrente", "data-ano": "1",
    text: anos[CURVA.quadro] || "—" }));
  return caixa;
}

function tocarACurva(redesenhar) {
  pararACurva();
  CURVA.tocando = true;
  redesenhar(false);
  relogioDaCurva = setInterval(function () {
    const anos = (D.panorama.janela.anos || []).length;
    if (CURVA.quadro >= anos - 1) { pararACurva(); redesenhar(false); return; }
    CURVA.quadro += 1;
    redesenhar(false);
  }, 700);
}

/* Os controles vivem fora do palco que se redesenha — senão o foco do
   teclado saltaria do botão a cada quadro. Então eles se atualizam à mão. */
function atualizarControles(todas, anos) {
  const ano = document.querySelector('[data-ano="1"]');
  if (ano) ano.textContent = anos[CURVA.quadro] || "—";
  const cursor = document.querySelector(".cursor-ano");
  if (cursor) cursor.value = String(CURVA.quadro);
  const tocar = document.querySelector('[data-nav="tocar"]');
  if (tocar) {
    tocar.innerHTML = "";
    tocar.appendChild(Icons.get(CURVA.tocando ? "pausa" : "tocar", 14));
    tocar.appendChild(el("span", { text: CURVA.tocando ? "Pausar" : "Tocar" }));
  }
  const selos = document.querySelector('[data-selos-curva="1"]');
  if (selos) {
    Array.prototype.forEach.call(selos.children, function (selo) {
      const marcado = CURVA.escolhidas.indexOf(selo.getAttribute("data-code")) >= 0;
      selo.classList.toggle("on", marcado);
      selo.setAttribute("aria-pressed", String(marcado));
    });
  }
}

/* ---- o desenho propriamente dito ---- */
function desenharCurvas(palco, p, anos, todas) {
  const vivas = todas.filter(function (v) {
    return CURVA.escolhidas.indexOf(v.code) >= 0; });
  if (!vivas.length) {
    palco.appendChild(nota("<b>Nenhuma série no gráfico.</b> Marque ao menos uma "
      + "variável acima — ou use <b>Principais</b> para voltar às seis maiores."));
    return;
  }
  const ate = CURVA.quadro + 1;
  const parcial = ate < anos.length;
  /* o topo do eixo vem da série INTEIRA: durante a plotagem o eixo tem de
     ficar parado, senão a curva parece pular a cada ano novo */
  const teto = vivas.reduce(function (a, v) {
    return Math.max(a, Math.max.apply(null, (v.suave || [0]).concat([0]))); }, 0);

  const marcas = [];
  vivas.forEach(function (v, si) {
    (v.inflexoes || []).forEach(function (inf) {
      const i = p.janela.anos.indexOf(inf.ano);
      if (i >= 0 && i < ate) {
        marcas.push({ serie: si, i: i, label: String(inf.ano),
                      color: corDaVariavel(v.code),
                      title: v.label + " · " + inf.ano + ": " + inf.leitura });
      }
    });
  });

  const grafico = cartao("linhas", "Todas as variáveis no tempo",
    (parcial ? "Traçado até " + anos[CURVA.quadro] + " — o eixo já está na escala do "
       + "período inteiro, então a linha cresce sem o gráfico pular. "
     : marcas.length ? "Séries filtradas, com os pontos de inflexão marcados sobre a "
       + "própria curva. " : "Séries filtradas. ")
    + "Onde duas linhas se cruzam, uma passou a outra.",
    C.lines({
      labels: anos, max: teto,
      series: vivas.map(function (v) {
        return { label: v.label, values: (v.suave || []).slice(0, ate),
                 color: corDaVariavel(v.code), area: false }; }),
      marks: marcas,
      height: 340, file: "curvas-variaveis",
      table: {
        cols: [{ k: "ano", label: "Ano" }].concat(vivas.map(function (v) {
          return { k: v.code, label: v.label, num: true }; })),
        rows: anos.map(function (ano, i) {
          const linha = { ano: ano };
          vivas.forEach(function (v) { linha[v.code] = (v.serie || [])[i]; });
          return linha;
        }),
      },
    }));
  palco.appendChild(grafico);
  if (CURVA.animar) animarTracado(grafico);

  const comCurva = vivas.filter(function (v) { return v.confiavel; });
  if (!comCurva.length) return;

  palco.appendChild(el("div", { class: "grade g2", style: "margin-top:14px" }, [
    cartao("subida", "Velocidade — artigos por ano",
      "Acima de zero a variável cresce; abaixo, encolhe.",
      C.lines({ labels: anos,
        series: comCurva.map(function (v) {
          return { label: v.label, values: (v.velocidade || []).slice(0, ate),
                   color: corDaVariavel(v.code) }; }),
        height: 240, file: "velocidade", larguraReal: 400 })),
    cartao("raio", "Aceleração — a curva abre ou fecha?",
      "Onde cruza o zero está o ponto de inflexão, marcado no gráfico.",
      C.lines({ labels: anos,
        series: comCurva.map(function (v) {
          return { label: v.label, values: (v.aceleracao || []).slice(0, ate),
                   color: corDaVariavel(v.code) }; }),
        marks: comCurva.reduce(function (acc, v, si) {
          (v.inflexoes || []).forEach(function (inf) {
            const i = p.janela.anos.indexOf(inf.ano);
            if (i >= 0 && i < ate) acc.push({ serie: si, i: i, color: corDaVariavel(v.code),
                                              title: v.label + ": " + inf.leitura });
          });
          return acc;
        }, []),
        height: 240, file: "aceleracao", larguraReal: 400 })),
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

/* ---- o que não depende do filtro ---- */
function curvasSemSerie(palco) {
  const p = D.panorama;
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

/* ---- dendrograma: em que ordem os assuntos se juntam ---- */
function cartaoDoDendrograma() {
  const d = D.dendrograma || {};
  if (!d.raiz) {
    return cartao("hierarquia", "Dendrograma dos assuntos",
      "Como as variáveis se agrupam pela produção que dividem.",
      nota("<b>Ainda não dá para agrupar.</b> "
        + (d.porque || "é preciso pelo menos duas variáveis com artigo.")));
  }
  const separadas = (d.altura_maxima || 0) >= 0.999;
  return cartao("hierarquia", "Dendrograma dos assuntos",
    "Agrupamento pela média (UPGMA) sobre a distância 1 − Jaccard: quanto mais à "
    + "esquerda dois ramos se juntam, mais os mesmos artigos os sustentam.",
    el("div", {}, [
      C.dendrograma({ raiz: d.raiz, altura_maxima: d.altura_maxima,
        caption: null, corte: 0.9, corteRotulo: "agendas separadas" }),
      el("p", { class: "leitura", html: separadas
        ? "Há ramos que <b>só se encontram na distância máxima</b> — nenhum artigo em "
          + "comum entre eles. Não é um laboratório com um tema: são agendas paralelas, "
          + "e cada uma sustenta a sua própria série."
        : "Todos os ramos se encontram <b>antes da distância máxima</b>: há artigo "
          + "cruzando cada par de agendas." }),
      el("p", { class: "hint", text: (d.folhas || []).length
        + " variável(is) agrupada(s). A fusão mais baixa é o par que mais divide artigos." }),
    ]));
}

/* ---- organograma do método, no formato de nós ligados ---- */
/* Cada caixa carrega o valor REAL do passo, não um rótulo genérico: um
   fluxograma que diz "suavização" e nada mais é um desenho de manual. O
   que responde à pergunta "de onde saiu esse número" é ver 44 artigos
   virarem 15 séries e 6 curvas confiáveis. */
function cartaoDoMetodo(p, todas) {
  const comSerie = todas.filter(function (v) { return v.confiavel; });
  const inflexoes = todas.reduce(function (a, v) {
    return a + (v.inflexoes || []).length; }, 0);
  return cartao("automacao", "O caminho do dado até a leitura",
    "Cada caixa é um passo do cálculo, com o número que ele produziu agora. "
    + "É o mesmo desenho de caixa-e-fio de um n8n — só que os valores são os desta base.",
    C.fluxo({
      caption: null, file: "metodo",
      nodes: [
        { id: "art", label: "Artigos na base", valor: p.total_artigos || 0,
          nota: "cadastro", tom: "entrada", coluna: 0,
          dica: "Todo o acervo. Só os que carregam variável do vocabulário "
            + "entram numa série." },
        { id: "ser", label: "Séries anuais", valor: todas.length,
          nota: "uma por variável", tom: "passo", coluna: 1 },
        { id: "med", label: "Mediana móvel", valor: "janela 3",
          nota: "tira o pico isolado", tom: "passo", coluna: 2 },
        { id: "sua", label: "Suavização", valor: "1·2·1",
          nota: "média ponderada", tom: "passo", coluna: 3 },
        { id: "vel", label: "Velocidade", valor: "Δ central",
          nota: "artigos por ano", tom: "passo", coluna: 4 },
        { id: "ace", label: "Aceleração", valor: "Δ²",
          nota: "abre ou fecha", tom: "passo", coluna: 5 },
        { id: "rui", label: "Resíduo", valor: "ruído",
          nota: "o que a subtração deixou", tom: "alerta", coluna: 4 },
        { id: "inf", label: "Inflexões", valor: inflexoes,
          nota: "troca de sinal", tom: "saida", coluna: 6 },
        { id: "lei", label: "Curvas legíveis", valor: comSerie.length,
          nota: "de " + todas.length, tom: "saida", coluna: 6 },
      ],
      links: [
        { de: "art", para: "ser" }, { de: "ser", para: "med" },
        { de: "med", para: "sua" }, { de: "sua", para: "vel", tom: "passo" },
        { de: "sua", para: "rui", tom: "alerta" },
        { de: "vel", para: "ace", tom: "passo" },
        { de: "ace", para: "inf", tom: "saida" },
        { de: "rui", para: "lei", rotulo: "ruído < 0,8", tom: "saida" },
      ],
    }));
}

/* ---- a árvore de decisão, com quantas variáveis caem em cada folha ---- */
/* A regra que decide se uma curva pode ser lida está escrita em três
   linhas de Python. Aqui ela vira desenho com a contagem em cada folha --
   e assim quem olha vê POR QUE a maior parte das variáveis não tem curva,
   em vez de descobrir isso um cartão vazio de cada vez. */
function cartaoDaDecisao(todas) {
  const semAnos = todas.filter(function (v) {
    return (v.anos_com_dado || 0) < 3; });
  const comAnos = todas.filter(function (v) { return (v.anos_com_dado || 0) >= 3; });
  const ruidosa = comAnos.filter(function (v) {
    return v.razao_ruido !== null && v.razao_ruido >= 0.8; });
  const limpa = comAnos.filter(function (v) {
    return !(v.razao_ruido !== null && v.razao_ruido >= 0.8); });
  const virou = limpa.filter(function (v) { return (v.inflexoes || []).length; });
  const lisa = limpa.filter(function (v) { return !(v.inflexoes || []).length; });

  return cartao("processo", "A árvore que decide se a curva pode ser lida",
    "As mesmas três perguntas que o cálculo faz, com quantas variáveis caem de cada "
    + "lado. É por aqui que se vê o que falta para uma variável ganhar curva.",
    C.fluxo({
      caption: null, file: "decisao",
      nodes: [
        { id: "raiz", label: "Variáveis", valor: todas.length,
          nota: "no recorte", tom: "entrada", coluna: 0 },
        { id: "q1", label: "3 anos com dado?", valor: comAnos.length + "/" + todas.length,
          nota: "mínimo para série", tom: "decisao", coluna: 1 },
        { id: "curta", label: "Sem série", valor: semAnos.length,
          nota: "falta história", tom: "descarte", coluna: 2,
          dica: "A produção anterior está no Lattes da equipe." },
        { id: "q2", label: "Ruído domina?", valor: ruidosa.length + " de " + comAnos.length,
          nota: "razão ≥ 0,8", tom: "decisao", coluna: 2 },
        { id: "ruido", label: "Só variação", valor: ruidosa.length,
          nota: "sem tendência", tom: "alerta", coluna: 3,
          dica: "A linha existe, mas o que ela desenha é balanço, não tendência." },
        { id: "q3", label: "Tem inflexão?", valor: virou.length + " de " + limpa.length,
          nota: "Δ² troca de sinal", tom: "decisao", coluna: 3 },
        { id: "virada", label: "Curva com virada", valor: virou.length,
          nota: "há ano a explicar", tom: "saida", coluna: 4 },
        { id: "lisa", label: "Tendência lisa", valor: lisa.length,
          nota: "sobe ou desce sem virar", tom: "saida", coluna: 4 },
      ],
      links: [
        { de: "raiz", para: "q1" },
        { de: "q1", para: "curta", rotulo: "não", tom: "descarte" },
        { de: "q1", para: "q2", rotulo: "sim", tom: "saida" },
        { de: "q2", para: "ruido", rotulo: "sim", tom: "alerta" },
        { de: "q2", para: "q3", rotulo: "não", tom: "saida" },
        { de: "q3", para: "virada", rotulo: "sim", tom: "saida" },
        { de: "q3", para: "lisa", rotulo: "não", tom: "passo" },
      ],
    }));
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

/* O rodizio: o mapa passeia sozinho pelos paises, um a um, e para no
   instante em que alguem escolhe um. Numa tela de sala isso e o que faz o
   mapa ser lido -- parado, ele e uma figura; girando, e a pergunta "de onde
   vem isto?" sendo respondida pais a pais. Quem pediu menos movimento
   recebe o mapa parado, e os botoes continuam ali. */
const MAPA = { girando: false, indice: 0 };
let relogioDoMapa = null;
const SEGUNDOS_POR_PAIS = 3200;

function pararORodizio() {
  if (relogioDoMapa) { clearInterval(relogioDoMapa); relogioDoMapa = null; }
  MAPA.girando = false;
}

function girarOMapa(paises, redesenhar) {
  pararORodizio();
  if (paises.length < 2) return;
  MAPA.girando = true;
  redesenhar();
  relogioDoMapa = setInterval(function () {
    /* o palco pode ter sido esvaziado por uma troca de aba ou por um
       evento do banco; sem esta saida o cronometro segue vivo redesenhando
       um elemento que ja nao esta na pagina */
    if (!document.getElementById("palco-mapa")) { pararORodizio(); return; }
    MAPA.indice = (MAPA.indice + 1) % paises.length;
    ST.pais = paises[MAPA.indice].pais;
    redesenhar();
  }, SEGUNDOS_POR_PAIS);
}

/* Os artigos de um pais, pelos ids que vieram no payload -- e nao pela
   palavra "Italia" procurada no titulo, que nao esta la. */
function artigosDoPais(nome) {
  const paises = ((D.panorama || {}).paises || {}).todos || [];
  const achado = paises.find(function (x) { return x.pais === nome; });
  if (!achado) return [];
  const querido = {};
  (achado.artigos || []).forEach(function (id) { querido[id] = true; });
  return (D.artigos || []).filter(function (a) { return querido[a.id]; });
}

/* O que o pais escolhido tem dentro: as variaveis que aparecem nos artigos
   dele, do mais frequente ao menos. E a extracao do laboratorio recortada
   por pais -- a mesma marcacao da aba Extracao, contada. */
function variaveisDoPais(artigos) {
  const conta = new Map();
  artigos.forEach(function (a) {
    (a.variaveis || []).forEach(function (v) {
      const antes = conta.get(v.code) || { code: v.code, label: v.label,
        grupo: v.grupo, icone: v.icone, n: 0, principais: 0 };
      antes.n += 1;
      if (v.principal) antes.principais += 1;
      conta.set(v.code, antes);
    });
  });
  return Array.from(conta.values()).sort(function (a, b) {
    return b.n - a.n || b.principais - a.principais; });
}

function botoesDePais(paises, redesenhar) {
  const caixa = el("div", { class: "botoes-pais", role: "group",
    "aria-label": "Países com produção" });
  paises.forEach(function (x, i) {
    const atual = ST.pais === x.pais;
    caixa.appendChild(el("button", {
      type: "button", class: "chip-pais" + (atual ? " ativo" : ""),
      "data-pais": x.pais, "aria-pressed": atual ? "true" : "false",
      title: x.n + " artigo(s) com autor deste país",
      onclick: function () {
        /* Clicar no país que já está em foco desliga o foco -- é o único
           jeito de ver o mapa inteiro de novo sem recarregar. MAS não
           enquanto o mapa gira: ali o país aceso é escolha do rodízio, não
           da pessoa, e o chip muda debaixo do dedo. Clicar no que acabou de
           acender apagaria justamente o que se quis ver. */
        const escolhaMinha = !MAPA.girando && ST.pais === x.pais;
        pararORodizio();
        if (escolhaMinha) { ST.pais = null; }
        else { ST.pais = x.pais; MAPA.indice = i; }
        redesenhar();
      },
    }, [el("span", { text: x.pais }), el("small", { text: String(x.n) })]));
  });
  return caixa;
}

function controlesDoMapa(paises, redesenhar) {
  const caixa = el("div", { class: "nav-mapa" });
  const irPara = function (i) {
    pararORodizio();
    MAPA.indice = (i + paises.length) % paises.length;
    ST.pais = paises[MAPA.indice].pais;
    redesenhar();
  };
  caixa.appendChild(el("button", {
    type: "button", class: "ghost", title: "País anterior", "data-nav": "antes",
    onclick: function () { irPara(MAPA.indice - 1); },
  }, [Icons.get("anterior", 14)]));
  caixa.appendChild(el("button", {
    type: "button", class: MAPA.girando ? "ghost" : "primary", "data-nav": "girar",
    onclick: function () {
      if (MAPA.girando) { pararORodizio(); redesenhar(); }
      else { girarOMapa(paises, redesenhar); }
    },
  }, [Icons.get(MAPA.girando ? "pausa" : "tocar", 14),
      el("span", { text: MAPA.girando ? "Parar" : "Girar o mapa" })]));
  caixa.appendChild(el("button", {
    type: "button", class: "ghost", title: "Próximo país", "data-nav": "depois",
    onclick: function () { irPara(MAPA.indice + 1); },
  }, [Icons.get("proximo", 14)]));
  if (ST.pais) {
    caixa.appendChild(el("button", {
      type: "button", class: "ghost", "data-nav": "limpar",
      onclick: function () { pararORodizio(); ST.pais = null; redesenhar(); },
    }, [Icons.get("filtro", 14), el("span", { text: "Ver o mundo todo" })]));
  }
  return caixa;
}

/* O recorte do pais, escrito: quantos artigos, quais variaveis, quais
   periodicos, e o caminho para a tabela inteira. E aqui que o clique no
   mapa vira resposta -- antes ele so mudava a cor de um contorno. */
function recorteDoPais(nome, redesenhar) {
  const artigos = artigosDoPais(nome);
  const paises = ((D.panorama || {}).paises || {}).todos || [];
  const ficha = paises.find(function (x) { return x.pais === nome; }) || {};
  const caixa = el("div", { class: "recorte-pais" });

  caixa.appendChild(el("div", { class: "recorte-topo" }, [
    el("h3", {}, [Icons.get("mapa", null), el("span", { text: nome })]),
    el("span", { class: "badge", text: artigos.length + " artigo(s)" }),
    ficha.instituicoes && ficha.instituicoes.length
      ? el("span", { class: "hint", text: ficha.instituicoes.join(" · ") }) : null,
  ]));

  if (!artigos.length) {
    /* O mapa contou N e a lista veio vazia: isso e um desencontro entre o
       payload e a tabela, e dizer "nenhum artigo" esconderia o defeito. */
    caixa.appendChild(nota("<b>O mapa conta " + (ficha.n || 0) + " artigo(s) aqui, "
      + "mas nenhum deles chegou à tabela.</b> O país vem da afiliação de quem "
      + "assina; se a lista está vazia, o vínculo entre o artigo e o país existe "
      + "e o artigo, não — vale recarregar a página."));
    return caixa;
  }

  const vars = variaveisDoPais(artigos);
  if (vars.length) {
    caixa.appendChild(el("p", { class: "hint", style: "margin:10px 0 6px",
      text: "O que se estuda neste país, do mais frequente ao menos:" }));
    caixa.appendChild(el("div", { class: "selos" }, vars.slice(0, 14).map(function (v) {
      return seloVariavel(
        { code: v.code, label: v.label + " · " + v.n, grupo: v.grupo, icone: v.icone,
          principal: v.principais > 0, origem: "confirmada" },
        { aoClicar: function () { ST.aba = "extracao"; desenhar(); } });
    })));
  } else {
    caixa.appendChild(el("p", { class: "hint", style: "margin-top:10px",
      text: "Nenhum artigo deste país tem variável marcada ainda." }));
  }

  const anos = artigos.map(function (a) { return a.ano; }).filter(Boolean).sort();
  const revistas = {};
  artigos.forEach(function (a) {
    if (a.journal) revistas[a.journal] = (revistas[a.journal] || 0) + 1; });
  const quantasRevistas = Object.keys(revistas).length;
  caixa.appendChild(el("p", { class: "hint", style: "margin-top:10px", text:
    (anos.length ? "De " + anos[0] + " a " + anos[anos.length - 1] + ". " : "")
    + (quantasRevistas ? quantasRevistas + " periódico(s) diferente(s). " : "")
    + artigos.filter(function (a) { return a.status === "publicado"; }).length
    + " publicado(s)." }));

  caixa.appendChild(el("button", {
    type: "button", class: "botao-destino", style: "margin-top:12px",
    "data-ir": "extracao",
    onclick: function () { pararORodizio(); ST.aba = "extracao"; desenhar(); },
  }, [Icons.get("dados", 15),
      el("span", { text: "Abrir os " + artigos.length + " artigos na Extração" })]));
  return caixa;
}

function verMapa(palco) {
  const paises = ((D.panorama || {}).paises) || { top: [], todos: [] };
  const todos = paises.todos || [];
  pedirMundo();
  palco.appendChild(cabeca("mapa", "Mapa da produção",
    "De onde vem a produção: o país de quem assina cada artigo — a instituição "
    + "no cadastro, ou a afiliação que veio junto com o artigo da base. "
    + "A cor do país é a quantidade de artigos; clique num país, ou deixe o mapa "
    + "girar, e o recorte dele aparece embaixo."));

  const valores = {};
  todos.forEach(function (x) { valores[x.pais] = x.n; });

  if (!todos.length) {
    palco.appendChild(nota("<b>Nenhum país para mostrar ainda.</b> O artigo não carrega "
      + "país — quem carrega é quem assina. Há dois caminhos, e os dois valem: "
      + "trazer a produção das bases públicas, que vem com a afiliação de cada autor "
      + "(o botão está em <a href='#laboratorio'>O laboratório</a>), ou ligar cada "
      + "integrante à sua instituição na <a href='/app#perfil'>Área do integrante</a>."));
    return;
  }

  /* Um país escolhido numa visita anterior pode não existir mais no recorte
     de hoje. Sem esta limpeza, o mapa ficaria com um foco que não acende
     nada e um recorte vazio embaixo, sem explicação. */
  if (ST.pais && !todos.some(function (x) { return x.pais === ST.pais; })) {
    ST.pais = null;
  }
  if (ST.pais) {
    const onde = todos.findIndex(function (x) { return x.pais === ST.pais; });
    if (onde >= 0) MAPA.indice = onde;
  }

  /* O primeiro cartão dizia "País mais produtivo · 160 · 4 instituição(ões)"
     e não dizia QUAL país: o nome só entrava no rodapé quando não havia
     instituição para pôr ali. O rótulo do cartão é o lugar do nome. */
  palco.appendChild(el("div", { class: "grade g4" },
    paises.top.map(function (x, i) {
      const pe = (i === 0 ? "o país mais produtivo" : "artigos com autor daqui")
        + (x.instituicoes.length
          ? " · " + x.instituicoes.length + " instituição(ões)" : "");
      return indicador(x.pais, x.n, pe, "mapa"); })));

  const palcoMapa = el("div", { id: "palco-mapa", style: "margin-top:14px" });
  palco.appendChild(palcoMapa);

  function redesenhar() {
    palcoMapa.innerHTML = "";
    palcoMapa.appendChild(cartao("mapa",
      ST.pais ? "A produção, com " + ST.pais + " em foco" : "Onde a produção acontece",
      "Um artigo com autores de dois países conta para os dois — foi produzido nos dois.",
      el("div", {}, [
        C.mapaMundi({
          world: D.mundo || [],
          values: valores,
          foco: ST.pais,
          unit: "artigos",
          file: "mapa-producao",
          emptyMessage: "Nenhum país registrado ainda.",
          emptyHint: "Falta ligar cada coautor à instituição dele.",
          onSelect: function (nome) {
            /* mesma regra do chip: com o mapa girando, o clique escolhe;
               parado, ele alterna */
            const escolhaMinha = !MAPA.girando && ST.pais === nome;
            pararORodizio();
            ST.pais = escolhaMinha ? null : nome;
            redesenhar();
          },
          table: {
            cols: ["País", "Artigos", "Instituições"],
            rows: todos.map(function (x) {
              return [x.pais, x.n, x.instituicoes.join("; ")]; }),
          },
        }),
        controlesDoMapa(todos, redesenhar),
        botoesDePais(todos, redesenhar),
      ])));
    if (ST.pais) palcoMapa.appendChild(recorteDoPais(ST.pais, redesenhar));
  }
  redesenhar();

  /* O mapa começa girando: numa tela de sala ninguém aperta nada. Quem
     pediu menos movimento recebe o mapa parado -- e os botões, que são o
     caminho de quem opera, continuam exatamente onde estão. */
  if (!poucoMovimento() && !ST.pais && todos.length > 1) {
    girarOMapa(todos, redesenhar);
  }
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
  /* O recorte por país vem dos ids que o mapa mandou, e não da busca em
     texto. Antes, clicar num país escrevia "Itália" na caixa de busca e a
     busca procurava a palavra no título, no autor e na revista -- onde ela
     não está. A tabela vinha vazia, com o nome do país escrito em cima,
     e nada na tela dizia que a pergunta tinha sido a errada. */
  if (ST.pais) {
    const doPais = {};
    artigosDoPais(ST.pais).forEach(function (a) { doPais[a.id] = true; });
    lista = lista.filter(function (a) { return doPais[a.id]; });
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
    /* O recorte que veio do mapa precisa aparecer AQUI: sem a pastilha, a
       tabela mostra 4 de 138 artigos e nada explica o desaparecimento dos
       outros 134 -- quem chegou pelo mapa sabe por quê, quem voltou a esta
       aba dez minutos depois, não. E ela se desliga no mesmo lugar. */
    ST.pais ? el("button", {
      type: "button", class: "chip-pais ativo", "data-recorte": "pais",
      title: "Mostrar todos os países de novo",
      onclick: function () { ST.pais = null; desenhar(); },
    }, [Icons.get("mapa", 12), el("span", { text: ST.pais }),
        Icons.get("filtro", 11)]) : null,
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
    text: (ST.pais ? "Artigos com autor de " + ST.pais : "Todos os artigos")
      + " (" + todos.length + ")" }));
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
/* Projetos, com a extensão separada                                    */
/*                                                                      */
/* Extensão não é pesquisa com outro nome: outro público, outra entrega */
/* e outra prestação de contas. Numa lista só ela some -- é sempre a    */
/* minoria, e some primeiro.                                            */
/* ==================================================================== */
const SITUACAO_PROJETO = { em_andamento: "Em andamento", concluido: "Concluído",
  suspenso: "Suspenso", planejado: "Planejado" };

function cartaoDeProjeto(p) {
  const periodo = [p.started_on, p.ended_on].filter(Boolean)
    .map(function (d) { return String(d).slice(0, 7).split("-").reverse().join("/"); })
    .join(" – ") || "sem período declarado";
  const corpo = el("div", {}, [
    el("div", { class: "hint", style: "line-height:1.55",
      text: p.description || "Sem descrição cadastrada." }),
    el("div", { class: "linhas-projeto" }, [
      el("div", {}, [el("b", { text: "Coordenação: " }),
        el("span", { text: p.coordinator_name || "—" })]),
      el("div", {}, [el("b", { text: "Período: " }), el("span", { text: periodo })]),
      p.funder ? el("div", {}, [el("b", { text: "Financiamento: " }),
        el("span", { text: p.funder + (p.grant_number ? " · " + p.grant_number : "") })]) : null,
      p.linha ? el("div", {}, [el("b", { text: "Linha: " }),
        el("span", { text: p.linha })]) : null,
    ]),
  ]);
  if (p.equipe.length) {
    corpo.appendChild(el("div", { class: "selos", style: "margin-top:10px" },
      p.equipe.map(function (nome) {
        return el("span", { class: "selo-var", style: "--tom:" + C.token("--series-1") },
          [Icons.get("pessoa", 12), el("span", { text: nome })]);
      })));
  }
  if (p.tipo_deduzido) {
    corpo.appendChild(el("p", { class: "hint", style: "margin-top:9px", text:
      "Reconhecido como extensão pelo nome — o campo de tipo está em branco. "
      + "Preencher o tipo no cadastro tira a adivinhação daqui." }));
  }
  return el("div", { class: "cartao" }, [
    el("h3", {}, [Icons.get(p.extensao ? "pessoas" : "projeto", null),
      el("span", { text: p.name })]),
    el("div", { class: "selos", style: "margin:2px 0 8px" }, [
      el("span", { class: "badge", text: SITUACAO_PROJETO[p.status] || p.status || "—" }),
      p.kind ? el("span", { class: "badge", text: p.kind }) : null,
      el("span", { class: "badge", text: p.artigos + " artigo(s)" }),
    ]),
    el("div", { class: "corpo" }, corpo),
  ]);
}

function verProjetos(palco) {
  const pr = D.projetos || { todos: [], extensao: [], pesquisa: [] };
  palco.appendChild(cabeca("projeto", "Projetos e extensão",
    "A extensão vem primeiro e separada: tem outro público e outra entrega, "
    + "e numa lista única ela desaparece por ser minoria."));

  palco.appendChild(el("div", { class: "grade g4" }, [
    indicador("Projetos de extensão", pr.extensao.length, "cadastrados", "pessoas"),
    indicador("Em andamento", (pr.em_andamento || []).length, "agora", "processo"),
    indicador("Projetos de pesquisa", pr.pesquisa.length, "cadastrados", "projeto"),
    indicador("Pessoas na equipe", pr.pessoas_alcancadas || 0, "somadas nos de extensão",
      "pessoa"),
  ]));

  palco.appendChild(el("h2", { style: "margin:22px 0 10px;font-size:17px",
    text: "Extensão (" + pr.extensao.length + ")" }));
  if (pr.extensao.length) {
    palco.appendChild(el("div", { class: "grade g2" },
      pr.extensao.map(cartaoDeProjeto)));
  } else {
    palco.appendChild(nota("<b>Nenhum projeto de extensão cadastrado ainda.</b> "
      + "O sistema reconhece um projeto como extensão pelo campo <i>tipo</i> — "
      + "basta escrever \"Extensão\" nele, na "
      + "<a href='/app#projetos'>Área do integrante</a>. Enquanto o tipo estiver "
      + "em branco, o nome do projeto é o único indício, e adivinhar não é o "
      + "mesmo que saber."));
  }

  palco.appendChild(el("h2", { style: "margin:26px 0 10px;font-size:17px",
    text: "Pesquisa (" + pr.pesquisa.length + ")" }));
  palco.appendChild(pr.pesquisa.length
    ? el("div", { class: "grade g2" }, pr.pesquisa.map(cartaoDeProjeto))
    : nota("Nenhum projeto de pesquisa cadastrado."));
}

/* ==================================================================== */
/* Triangulação — em quem, com o quê, medindo o quê                     */
/*                                                                      */
/* Um artigo de intervenção só responde de verdade quando responde às   */
/* três perguntas. O valor de olhar assim não é contar cruzamentos      */
/* bonitos: é ver a PERNA QUE FALTA.                                    */
/* ==================================================================== */
function matrizDeCruzamento(m) {
  if (!m.celulas.length) {
    return el("p", { class: "hint", text: "Nenhum cruzamento nesta face." });
  }
  const teto = Math.max.apply(null, m.celulas.map(function (c) { return c.n; }));
  const conta = {};
  m.celulas.forEach(function (c) { conta[c.x + "||" + c.y] = c.n; });
  const cabeca_ = el("tr", {}, [el("th", { text: m.eixo_y + " ↓  /  " + m.eixo_x + " →" })]
    .concat(m.colunas.map(function (x) { return el("th", { class: "num", text: x }); })));
  const corpo = el("tbody", {}, m.linhas.map(function (y) {
    return el("tr", {}, [el("th", { text: y })].concat(m.colunas.map(function (x) {
      const n = conta[x + "||" + y] || 0;
      /* Um matiz só, do fraco ao forte: é magnitude, não identidade.
         Célula vazia fica sem tinta -- zero não é o tom mais claro,
         é a ausência de célula. */
      const tinta = n ? "background:color-mix(in srgb, " + C.token("--accent-strong")
        + " " + Math.round(14 + 62 * n / teto) + "%, transparent)" : null;
      return el("td", { class: "num celula", style: tinta,
        title: n ? y + " × " + x + ": " + n + " artigo(s)" : "sem cruzamento",
        text: n ? String(n) : "" });
    })));
  }));
  return el("div", { class: "rolagem" },
    el("table", { class: "dados matriz" }, [el("thead", {}, cabeca_), corpo]));
}

function verTriangulo(palco) {
  const t = D.triangulacao || { trios: [], faltando: {}, matrizes: [], pernas: {} };
  palco.appendChild(cabeca("hierarquia", "Triangulação",
    "Todo artigo de intervenção responde três perguntas: EM QUEM, COM O QUÊ e "
    + "MEDINDO O QUÊ. Aqui elas aparecem cruzadas — e, principalmente, aparece "
    + "a pergunta que ficou sem resposta."));

  const faltaDesfecho = (t.faltando.desfecho || []).length;
  palco.appendChild(el("div", { class: "grade g4" }, [
    indicador("Triângulos completos", t.completos || 0,
      "de " + (t.com_variavel || 0) + " artigos com variável", "aceite"),
    indicador("Sem desfecho declarado", faltaDesfecho,
      "dizem o que fizeram, não o que mediram", "aviso"),
    indicador("Sem população", (t.faltando.aplicacao || []).length,
      "não dizem em quem", "aviso"),
    indicador("Sem intervenção", (t.faltando.intervencao || []).length,
      "não dizem com o quê", "aviso"),
  ]));

  if (faltaDesfecho) {
    palco.appendChild(nota("<b>" + faltaDesfecho + " artigo(s) dizem o que fizeram "
      + "e não dizem o que mediram.</b> Pode ser o texto (o desfecho está lá e não "
      + "foi reconhecido) ou pode ser o estudo. Nos dois casos é onde olhar primeiro "
      + "— e é o que separa uma triangulação de uma lista."));
  }

  /* ---- os trios, em organograma ---- */
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "hierarquia", "Os trios que o laboratório fecha",
    "Condição → intervenção → desfecho. Clique num artigo e ele abre na base.",
    t.trios.length ? arvoreDeTrios(t.trios)
      : el("p", { class: "hint", text: "Nenhum artigo fecha as três pernas ainda." }))));

  /* ---- as duas faces do triângulo ---- */
  (t.matrizes || []).forEach(function (m) {
    palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
      "rede", m.eixo_x + " × " + m.eixo_y,
      "Uma face do triângulo, achatada. A cor é quantidade — um matiz só.",
      matrizDeCruzamento(m))));
  });

  /* ---- quem está incompleto, e o que tem ---- */
  const incompletos = (t.faltando.desfecho || []).slice(0, 20);
  if (incompletos.length) {
    palco.appendChild(el("h2", { style: "margin:26px 0 10px;font-size:17px",
      text: "Artigos sem desfecho declarado" }));
    palco.appendChild(el("div", { class: "rolagem" }, el("table", { class: "dados" }, [
      el("thead", {}, el("tr", {}, ["Artigo", "O que já tem"].map(function (x) {
        return el("th", { text: x }); }))),
      el("tbody", {}, incompletos.map(function (a) {
        const tem = Object.keys(a.tem || {}).map(function (k) {
          return (t.pernas[k] || k) + ": " + a.tem[k].join(", "); }).join(" · ");
        return el("tr", {}, [
          el("td", {}, tituloClicavel(
            (D.artigos || []).find(function (x) { return x.id === a.id; }) || a, 90)),
          el("td", { text: tem || "—" }),
        ]);
      })),
    ])));
  }
}

function arvoreDeTrios(trios) {
  /* Organograma: a condição abre as intervenções, que abrem os desfechos.
     A mesma condição repetida em cada linha viraria ruído -- agrupar é o
     que faz a hierarquia dizer alguma coisa. */
  const porAplicacao = {};
  trios.forEach(function (t) {
    const nivel1 = porAplicacao[t.aplicacao] = porAplicacao[t.aplicacao] || {};
    (nivel1[t.intervencao] = nivel1[t.intervencao] || []).push(t);
  });
  const caixa = el("div", { class: "arvore-trios" });
  Object.keys(porAplicacao).forEach(function (aplicacao) {
    const galho = el("div", { class: "galho" });
    galho.appendChild(el("div", { class: "no n1" }, [
      Icons.get("alvo", 14), el("span", { text: aplicacao })]));
    Object.keys(porAplicacao[aplicacao]).forEach(function (intervencao) {
      const sub = el("div", { class: "sub" });
      sub.appendChild(el("div", { class: "no n2" }, [
        Icons.get("experimento", 13), el("span", { text: intervencao })]));
      porAplicacao[aplicacao][intervencao].forEach(function (t) {
        const folha = el("div", { class: "no n3" }, [
          Icons.get("qualidade", 13),
          el("span", { text: t.desfecho }),
          el("span", { class: "n", text: String(t.n) }),
        ]);
        const artigos = el("div", { class: "artigos-trio" }, t.artigos.map(function (a) {
          const cheio = (D.artigos || []).find(function (x) { return x.id === a.id; });
          return el("div", {}, tituloClicavel(cheio || { title: a.titulo }, 80));
        }));
        sub.appendChild(folha);
        sub.appendChild(artigos);
      });
      galho.appendChild(sub);
    });
    caixa.appendChild(galho);
  });
  return caixa;
}

/* ==================================================================== */
/* Incidência e prevalência                                             */
/*                                                                      */
/* A leitura é a da epidemiologia, e cabe porque a pergunta é a mesma.  */
/* Incidência: casos NOVOS no ano sobre quem estava em risco de virar   */
/* caso -- aceite e rejeição só acontecem com artigo em avaliação.      */
/* Prevalência: a fatia da carteira em cada situação NUM INSTANTE.      */
/* ==================================================================== */
const COR_ESTADO = {
  "em produção": "--ord-1", "em avaliação": "--ord-2",
  "aceito": "--ord-3", "publicado": "--ord-4",
  "rejeitado": "--critical", "arquivado": "--ink-muted",
};

function verFunil(palco) {
  const inc = D.incidencia || { serie: [] };
  const prev = D.prevalencia || { serie: [], estados: [] };
  palco.appendChild(cabeca("processo", "Incidência e prevalência",
    "Duas perguntas diferentes sobre a mesma carteira. Incidência: quantos "
    + "artigos VIRARAM aceitos, rejeitados ou publicados no ano, sobre quantos "
    + "podiam virar. Prevalência: quantos ESTÃO em cada situação hoje."));

  const hoje = prev.hoje || { estados: {}, fracao: {}, total: 0 };
  palco.appendChild(nota("<b>Por que não é a mesma coisa.</b> Contar aceites "
    + "sobre o acervo inteiro dá uma taxa que <i>cai sozinha</i> toda vez que "
    + "alguém começa um artigo novo — e não foi isso que aconteceu. Aceite e "
    + "rejeição só podem acontecer com artigo que está em avaliação; publicação, "
    + "só com artigo já aceito. É esse o denominador."));

  /* ---- prevalência de hoje ---- */
  palco.appendChild(el("div", { class: "grade g4", style: "margin-top:14px" },
    (prev.estados || []).filter(function (e) { return hoje.estados[e]; })
      .map(function (estado) {
        return indicador(estado[0].toUpperCase() + estado.slice(1),
          hoje.estados[estado],
          (hoje.fracao[estado] || 0).toFixed(1).replace(".", ",") + "% da carteira",
          estado === "publicado" ? "producao" : estado === "rejeitado" ? "aviso" : "processo");
      })));
  if (!hoje.total) {
    palco.appendChild(nota("<b>Nenhum artigo com data para situar no tempo.</b> "
      + "A prevalência é reconstruída das datas de início, submissão, aceite e "
      + "publicação — sem elas não dá para dizer onde o artigo estava em cada ano."));
  }

  /* ---- a carteira ao longo do tempo ---- */
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "processo", "Prevalência: onde a carteira estava, ano a ano",
    "Cada coluna é o dia 31 daquele ano. Reconstruído das datas, não do "
    + "estado de hoje — o estado de hoje não sabe onde o artigo estava em 2019.",
    C.columns({
      labels: prev.serie.map(function (x) { return String(x.ano); }),
      mode: "empilhado",
      series: (prev.estados || []).map(function (estado) {
        return { label: estado, color: C.token(COR_ESTADO[estado] || "--ink-muted"),
                 values: prev.serie.map(function (x) { return x.estados[estado] || 0; }) };
      }),
      height: 300, unit: "artigos",
      table: { cols: ["Ano"].concat(prev.estados || []),
               rows: prev.serie.map(function (x) {
                 return [x.ano].concat((prev.estados || []).map(function (e) {
                   return x.estados[e] || 0; })); }) },
    }))));

  /* ---- incidência: as taxas ---- */
  const comRisco = inc.serie.filter(function (x) { return x.em_risco_decisao > 0; });
  palco.appendChild(el("div", { style: "margin-top:14px" }, cartao(
    "linhas", "Incidência: quantos viraram caso, sobre quantos podiam virar",
    "Por 100 artigos em risco no ano. Anos sem ninguém em risco não entram — "
    + "taxa sem denominador não é zero, é ausência.",
    comRisco.length
      ? C.lines({
          labels: comRisco.map(function (x) { return String(x.ano); }),
          series: [
            { name: "Aceite", values: comRisco.map(function (x) { return x.taxa_aceite; }) },
            { name: "Rejeição", values: comRisco.map(function (x) { return x.taxa_rejeicao; }) },
            { name: "Publicação", values: comRisco.map(function (x) { return x.taxa_publicacao; }) },
          ],
          height: 280, unit: "%",
        })
      : el("p", { class: "hint", text: "Nenhum artigo esteve em avaliação nesta janela." }))));

  /* ---- a tabela, com o denominador à vista ---- */
  const linhas = inc.serie.filter(function (x) {
    return x.submetidos || x.aceitos || x.rejeitados || x.publicados; });
  if (linhas.length) {
    palco.appendChild(el("h2", { style: "margin:26px 0 10px;font-size:17px",
      text: "Ano a ano, com o denominador à vista" }));
    const corpo = el("tbody", {}, linhas.map(function (x) {
      return el("tr", {}, [
        el("td", { text: String(x.ano) }),
        el("td", { class: "num", text: String(x.em_risco_decisao) }),
        el("td", { class: "num", text: String(x.aceitos) }),
        el("td", { class: "num", text: String(x.rejeitados) }),
        el("td", { class: "num", text: String(x.publicados) }),
        el("td", { class: "num",
          text: x.taxa_aceite === null ? "—" : x.taxa_aceite.toFixed(1).replace(".", ",") + "%" }),
        el("td", { text: x.confiavel ? "" : (x.porque || "") }),
      ]);
    }));
    palco.appendChild(el("div", { class: "rolagem" }, el("table", { class: "dados" }, [
      el("thead", {}, el("tr", {}, ["Ano", "Em risco", "Aceitos", "Rejeitados",
        "Publicados", "Taxa de aceite", "Ressalva"].map(function (t, i) {
        return el("th", { class: i >= 1 && i <= 5 ? "num" : null, text: t }); }))),
      corpo,
    ])));
  }
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
  /* O relogio da curva aponta para um palco que esta prestes a ser
     esvaziado. Sem parar aqui, sair da aba deixa um cronometro vivo
     redesenhando um elemento que ja saiu da pagina. */
  pararACurva();
  pararORodizio();
  const palco = document.getElementById("palco");
  palco.innerHTML = "";
  if (!D.pronto) {
    palco.appendChild(el("p", { class: "hint", text: "Carregando o panorama…" }));
    return;
  }
  ({ visao: verVisao, laboratorio: verLaboratorio, variaveis: verVariaveis,
     curvas: verCurvas, rede: verRede, mapa: verMapa, sintese: verSintese,
     lacunas: verLacunas, extracao: verExtracao, funil: verFunil,
     triangulo: verTriangulo, projetos: verProjetos,
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
