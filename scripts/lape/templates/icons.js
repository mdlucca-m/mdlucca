/* ==========================================================================
   LAPE — ícones
   SVG inline, traço de 1.75px em currentColor, caixa de 24. Sem fonte de
   ícone e sem rede: o painel abre offline e o ícone acompanha a cor do texto.
   Todo ícone é decorativo (aria-hidden) — o rótulo ao lado é quem nomeia.
   ========================================================================== */
"use strict";

const Icons = (function () {
  const NS = "http://www.w3.org/2000/svg";

  /* Cada verbete é uma lista de primitivas: ["path", "M..."] , ["circle", cx, cy, r],
     ["line", x1, y1, x2, y2], ["rect", x, y, w, h, r]. Traço aberto, sem preenchimento. */
  const SET = {
    /* seções */
    painel: [["path", "M3 12a9 9 0 0 1 18 0"], ["path", "M12 12l4.5-3.5"],
      ["circle", 12, 12, 1.2], ["line", 3, 12, 5, 12], ["line", 19, 12, 21, 12]],
    producao: [["path", "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"],
      ["path", "M14 3v5h5"], ["line", 9, 13, 15, 13], ["line", 9, 17, 13, 17]],
    pessoas: [["circle", 9, 8, 3.2], ["path", "M3 20c0-3.2 2.7-5 6-5s6 1.8 6 5"],
      ["path", "M16.5 5.6a3.2 3.2 0 0 1 0 5.8"], ["path", "M18 15.4c2 .7 3 2.2 3 4.6"]],
    processo: [["path", "M21 12a9 9 0 0 1-14.7 7"], ["path", "M3 12a9 9 0 0 1 14.7-7"],
      ["path", "M17.7 2v3.4h-3.4"], ["path", "M6.3 22v-3.4h3.4"]],
    espaco: [["path", "M12 21s-6.5-5.6-6.5-10.2A6.5 6.5 0 0 1 12 4.3a6.5 6.5 0 0 1 6.5 6.5C18.5 15.4 12 21 12 21z"],
      ["circle", 12, 10.6, 2.4]],
    dados: [["ellipse", 12, 6, 7.5, 3], ["path", "M4.5 6v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"],
      ["path", "M4.5 12v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6"]],

    /* sub-abas e cartões */
    explorar: [["circle", 11, 11, 6.5], ["line", 15.8, 15.8, 21, 21]],
    barras: [["line", 3, 21, 21, 21], ["rect", 5, 12, 3.4, 9, 1], ["rect", 10.3, 7, 3.4, 14, 1],
      ["rect", 15.6, 3.5, 3.4, 17.5, 1]],
    linha: [["path", "M3 17l5-5 4 3 7-8"], ["circle", 8, 12, 1.4], ["circle", 12, 15, 1.4],
      ["circle", 19, 7, 1.4]],
    rede: [["circle", 12, 5, 2.3], ["circle", 5, 18, 2.3], ["circle", 19, 18, 2.3],
      ["line", 10.6, 6.9, 6.4, 15.8], ["line", 13.4, 6.9, 17.6, 15.8], ["line", 7.3, 18, 16.7, 18]],
    calendario: [["rect", 3.5, 5, 17, 16, 2.5], ["line", 3.5, 10, 20.5, 10],
      ["line", 8, 3, 8, 6.5], ["line", 16, 3, 16, 6.5], ["circle", 8.6, 14.5, 1],
      ["circle", 12.8, 14.5, 1]],
    relogio: [["circle", 12, 12, 8.5], ["path", "M12 7v5.3l3.4 2"]],
    submissao: [["path", "M21 3L10.5 13.5"], ["path", "M21 3l-6.8 18-3.7-7.5L3 9.8z"]],
    aceite: [["circle", 12, 12, 8.5], ["path", "M8.2 12.3l2.6 2.6 5-5.4"]],
    citacao: [["path", "M9 7.5C6.6 8.4 5 10.4 5 13.4V17h4.6v-4.4H7.4c0-1.7.7-2.8 2.2-3.4z"],
      ["path", "M18 7.5c-2.4.9-4 2.9-4 5.9V17h4.6v-4.4h-2.2c0-1.7.7-2.8 2.2-3.4z"]],
    projeto: [["path", "M3 7.5A1.5 1.5 0 0 1 4.5 6h4l2 2.5h7A1.5 1.5 0 0 1 19 10v7.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 3 17.5z"],
      ["line", 7, 13, 15, 13]],
    linhas: [["line", 4, 6.5, 20, 6.5], ["line", 4, 12, 20, 12], ["line", 4, 17.5, 14, 17.5],
      ["circle", 20, 17.5, 1.4]],
    achado: [["path", "M12 3l1.9 4.5 4.9.4-3.7 3.2 1.1 4.8L12 13.4 7.8 15.9l1.1-4.8L5.2 7.9l4.9-.4z"],
      ["line", 12, 18, 12, 21]],
    qualidade: [["path", "M12 3l7.5 3v5.4c0 4.4-3.1 8.1-7.5 9.6-4.4-1.5-7.5-5.2-7.5-9.6V6z"],
      ["path", "M9 12l2.2 2.2L15.4 10"]],
    automacao: [["rect", 4, 8.5, 16, 11, 3], ["circle", 9, 13.5, 1.2], ["circle", 15, 13.5, 1.2],
      ["path", "M12 8.5V5"], ["circle", 12, 3.6, 1.3], ["line", 8, 16.8, 16, 16.8]],
    mapa: [["path", "M3 6.5l6-2.5 6 2.5 6-2.5v14l-6 2.5-6-2.5-6 2.5z"], ["line", 9, 4, 9, 18.5],
      ["line", 15, 6.5, 15, 21]],
    tempo: [["line", 4, 12, 20, 12], ["circle", 7.5, 12, 2], ["circle", 13, 12, 2],
      ["circle", 18, 12, 2]],
    alvo: [["circle", 12, 12, 8.5], ["circle", 12, 12, 4.6], ["circle", 12, 12, 1]],
    subida: [["path", "M3 17l6-6 4 3.6L21 6"], ["path", "M15.5 6H21v5.3"]],
    livro: [["path", "M4 5.5A1.5 1.5 0 0 1 5.5 4H11v16H5.5A1.5 1.5 0 0 1 4 18.5z"],
      ["path", "M20 5.5A1.5 1.5 0 0 0 18.5 4H13v16h5.5a1.5 1.5 0 0 0 1.5-1.5z"]],
    raio: [["path", "M13 2L4.5 13.5H11L10 22l8.5-11.5H12z"]],
    aviso: [["path", "M12 4l9 15.5H3z"], ["line", 12, 10, 12, 14.5], ["circle", 12, 17.2, 1]],
    baixar: [["path", "M12 3.5v11"], ["path", "M7.6 10.4L12 14.8l4.4-4.4"],
      ["path", "M4.5 18.5v1a1.5 1.5 0 0 0 1.5 1.5h12a1.5 1.5 0 0 0 1.5-1.5v-1"]],
    atualizar: [["path", "M20.5 12a8.5 8.5 0 1 1-2.6-6.1"], ["path", "M20.5 4v4.6h-4.6"]],
    conectar: [["path", "M10.5 13.5l-2.6 2.6a3.7 3.7 0 0 1-5.2-5.2l2.6-2.6"],
      ["path", "M13.5 10.5l2.6-2.6a3.7 3.7 0 0 1 5.2 5.2l-2.6 2.6"], ["line", 9.5, 14.5, 14.5, 9.5]],

    /* ------------------------------------------------------------------
       Vocabulario do mural: o que esta acontecendo e o que vem a seguir.
       Prazo, reuniao, anuncio, defesa -- cada um com desenho proprio, para
       que a tela se leia de longe, sem depender do rotulo.
       ------------------------------------------------------------------ */
    prazo: [["line", 7, 3, 17, 3], ["line", 7, 21, 17, 21],
      ["path", "M8 3v3.4c0 1.6 1.4 2.6 4 5.6-2.6 3-4 4-4 5.6V21"],
      ["path", "M16 3v3.4c0 1.6-1.4 2.6-4 5.6 2.6 3 4 4 4 5.6V21"]],
    reuniao: [["circle", 8.2, 8, 2.2], ["circle", 15.8, 8, 2.2],
      ["path", "M4.5 14.2c.6-1.7 2-2.6 3.7-2.6s3.1.9 3.7 2.6"],
      ["path", "M12.1 14.2c.6-1.7 2-2.6 3.7-2.6s3.1.9 3.7 2.6"],
      ["line", 3, 17.4, 21, 17.4], ["line", 12, 17.4, 12, 20.5]],
    anuncio: [["path", "M4.5 9.5h3.2L14 5.4v13.2L7.7 14.5H4.5A1.5 1.5 0 0 1 3 13V11a1.5 1.5 0 0 1 1.5-1.5z"],
      ["path", "M17.4 9.2a4.2 4.2 0 0 1 0 5.6"], ["path", "M19.9 6.6a7.6 7.6 0 0 1 0 10.8"],
      ["path", "M8 14.5l1.2 5.6"]],
    tese: [["path", "M2.5 8.5L12 4.5l9.5 4-9.5 4z"],
      ["path", "M6.5 10.6V15c0 1.7 2.5 3 5.5 3s5.5-1.3 5.5-3v-4.4"], ["line", 21.5, 8.5, 21.5, 13.4]],
    bolsa: [["line", 8.6, 10.2, 5.5, 3.5], ["line", 15.4, 10.2, 18.5, 3.5], ["line", 9, 3.5, 15, 3.5],
      ["circle", 12, 15.2, 5.3],
      ["path", "M12 12.6l.85 1.72 1.9.28-1.37 1.34.32 1.89L12 16.94l-1.7.89.32-1.89-1.37-1.34 1.9-.28z"]],
    trofeu: [["path", "M8 4h8v5.4a4 4 0 0 1-8 0z"],
      ["path", "M8 5.6H5.4v1.6a3 3 0 0 0 2.9 3"], ["path", "M16 5.6h2.6v1.6a3 3 0 0 1-2.9 3"],
      ["line", 12, 13.4, 12, 17.2], ["line", 8.5, 20.6, 15.5, 20.6],
      ["path", "M9.8 20.6c.2-2 .9-3.4 2.2-3.4s2 1.4 2.2 3.4"]],
    foguete: [["path", "M12 3c3 2.2 4.6 5.4 4.6 9L12 16.2 7.4 12C7.4 8.4 9 5.2 12 3z"],
      ["circle", 12, 9.2, 1.9], ["path", "M7.4 12L5 13.6l1 3.6 2.6-2"],
      ["path", "M16.6 12L19 13.6l-1 3.6-2.6-2"],
      ["path", "M10.4 18.4c.5 1.3 1.6 2.5 1.6 2.5s1.1-1.2 1.6-2.5"]],
    experimento: [["line", 9.5, 3.4, 14.5, 3.4],
      ["path", "M10.5 3.4v5.3L5.6 18a2 2 0 0 0 1.8 3h9.2a2 2 0 0 0 1.8-3l-4.9-9.3V3.4"],
      ["line", 7.6, 14.6, 16.4, 14.6]],
    sino: [["path", "M12 3.6a5.6 5.6 0 0 1 5.6 5.6c0 4.1 1.4 5.3 1.4 5.3H5s1.4-1.2 1.4-5.3A5.6 5.6 0 0 1 12 3.6z"],
      ["path", "M10.2 17.6a2 2 0 0 0 3.6 0"], ["line", 12, 2, 12, 3.6]],
    apresentacao: [["rect", 3, 4, 18, 12, 2.5], ["line", 7.5, 12.6, 7.5, 10],
      ["line", 11.5, 12.6, 11.5, 7.6], ["line", 15.5, 12.6, 15.5, 9],
      ["line", 12, 16, 12, 19], ["path", "M8.6 21L12 19l3.4 2"]],
    mural: [["rect", 2.5, 4.5, 19, 13, 2.5], ["line", 8, 21, 16, 21], ["line", 12, 17.5, 12, 21],
      ["path", "M6.5 13.4l3-3.4 2.6 2.2 4.4-4.6"]],
    fogo: [["path", "M12 21a5.6 5.6 0 0 0 5.6-5.6c0-4.4-5.6-9-5.6-9s-5.6 4.6-5.6 9A5.6 5.6 0 0 0 12 21z"],
      ["path", "M12 21a2.5 2.5 0 0 0 2.5-2.5c0-2-2.5-4-2.5-4s-2.5 2-2.5 4A2.5 2.5 0 0 0 12 21z"]],
    financiamento: [["circle", 12, 12, 8.4],
      ["path", "M14.7 9.2c-.6-.9-1.6-1.4-2.8-1.4-1.6 0-2.6.8-2.6 1.9 0 2.8 5.5 1.3 5.5 4.2 0 1.2-1.2 2.1-2.9 2.1-1.3 0-2.4-.6-3-1.6"],
      ["line", 12, 5.8, 12, 7.8], ["line", 12, 16.2, 12, 18.2]],
    hierarquia: [["rect", 9, 3, 6, 4.4, 1.4], ["rect", 2.5, 15.6, 6, 4.4, 1.4],
      ["rect", 15.5, 15.6, 6, 4.4, 1.4], ["line", 12, 7.4, 12, 13.4],
      ["path", "M5.5 15.6v-2.2h13v2.2"]],
    orientacao: [["circle", 7, 7.4, 2.6],
      ["path", "M2.8 15.4c0-2.4 1.9-3.8 4.2-3.8s4.2 1.4 4.2 3.8"],
      ["circle", 17.6, 13.4, 2.2], ["path", "M14 20.4c0-2 1.6-3.2 3.6-3.2s3.6 1.2 3.6 3.2"],
      ["line", 12.8, 8.2, 17.2, 8.2], ["path", "M15.4 6.4l1.9 1.8-1.9 1.8"]],
    etiqueta: [["path", "M11.4 3.4H19A1.6 1.6 0 0 1 20.6 5v7.6l-8.2 8.2a1.6 1.6 0 0 1-2.3 0l-7-7a1.6 1.6 0 0 1 0-2.3z"],
      ["circle", 16.4, 7.6, 1.4]],
    filtro: [["path", "M3.5 5h17l-6.6 7.6V19l-3.8 2v-8.4z"]],
    pessoa: [["circle", 12, 8, 3.4], ["path", "M5 20.5c0-3.6 3.1-5.6 7-5.6s7 2 7 5.6"]],
    mensagem: [["path", "M4 5.5h16A1.5 1.5 0 0 1 21.5 7v8a1.5 1.5 0 0 1-1.5 1.5h-8.6L7 20.5v-4H4A1.5 1.5 0 0 1 2.5 15V7A1.5 1.5 0 0 1 4 5.5z"],
      ["line", 7.5, 10.8, 16.5, 10.8], ["line", 7.5, 13.4, 13, 13.4]],
    instituicao: [["path", "M3.5 9.5L12 4l8.5 5.5"], ["line", 5, 9.5, 5, 19.5],
      ["line", 19, 9.5, 19, 19.5], ["line", 9.3, 12.4, 9.3, 17],
      ["line", 14.7, 12.4, 14.7, 17], ["line", 2.5, 20.5, 21.5, 20.5]],

    /* ---- o domínio do laboratório ----
       Não são enfeite: cada um nomeia uma linha de pesquisa ou um objeto
       de estudo do LAPE, e é por eles que a tela deixa de parecer o painel
       de qualquer coisa. Mesmo traço de 1.75 em caixa de 24 dos demais --
       um ícone com outra espessura salta da fila e vira erro de impressão. */
    halteres: [["line", 3, 12, 5, 12], ["line", 19, 12, 21, 12],
      ["rect", 5, 8.6, 3, 6.8, 1.2], ["rect", 16, 8.6, 3, 6.8, 1.2],
      ["line", 8, 12, 16, 12]],
    corrida: [["circle", 15.4, 4.6, 1.9],
      ["path", "M13.6 8.4L10 10.6l1.6 3.4-2.4 5.4"],
      ["path", "M11.6 14l3.6 1.4 1.4 4.4"],
      ["path", "M10 10.6L6.4 9.4"], ["path", "M17.2 9.6l2.6 2.2"]],
    coracao: [["path", "M12 20.4S3.8 15 3.8 9.4a4.4 4.4 0 0 1 8.2-2.3 4.4 4.4 0 0 1 8.2 2.3c0 5.6-8.2 11-8.2 11z"],
      ["path", "M3.4 12.4h4l1.4-2.6 2 5 1.6-3.2 1.2 2 1-1.2h4"]],
    cerebro: [["path", "M12 5.2a3 3 0 0 0-5.6 1.1A2.8 2.8 0 0 0 4.6 9c0 1 .5 1.9 1.2 2.4A2.8 2.8 0 0 0 5 13.8c0 1.5 1.2 2.7 2.7 2.7.4 1.4 1.7 2.3 3.2 2.3.6 0 1.1-.1 1.1-.1V5.2z"],
      ["path", "M12 5.2a3 3 0 0 1 5.6 1.1A2.8 2.8 0 0 1 19.4 9c0 1-.5 1.9-1.2 2.4A2.8 2.8 0 0 1 19 13.8c0 1.5-1.2 2.7-2.7 2.7-.4 1.4-1.7 2.3-3.2 2.3-.6 0-1.1-.1-1.1-.1"],
      ["line", 12, 5.2, 12, 21]],
    dor: [["circle", 12, 12, 3.2],
      ["line", 12, 2.6, 12, 6.2], ["line", 12, 17.8, 12, 21.4],
      ["line", 2.6, 12, 6.2, 12], ["line", 17.8, 12, 21.4, 12],
      ["line", 5.4, 5.4, 7.9, 7.9], ["line", 16.1, 16.1, 18.6, 18.6],
      ["line", 18.6, 5.4, 16.1, 7.9], ["line", 7.9, 16.1, 5.4, 18.6]],
    pulmao: [["path", "M12 3.4v8.2"],
      ["path", "M12 8.6c-1.6 0-2.6-1-3.4-1-1.6 0-2.8 2.2-3.2 4.6-.4 2.6-.2 5.6 1.2 6.4 1.6.9 3.6-.6 4.2-2.6.4-1.4.4-3.4.4-4.8"],
      ["path", "M12 8.6c1.6 0 2.6-1 3.4-1 1.6 0 2.8 2.2 3.2 4.6.4 2.6.2 5.6-1.2 6.4-1.6.9-3.6-.6-4.2-2.6-.4-1.4-.4-3.4-.4-4.8"]],
    fita: [["circle", 12, 9, 5.2], ["path", "M9.2 13.4L7 21.4l5-2.6 5 2.6-2.2-8"],
      ["path", "M10.2 9l1.3 1.4 2.3-2.6"]],
    envelhecimento: [["circle", 11, 6.4, 2.6],
      ["path", "M11 9.6v5.2"], ["path", "M8 12.4h6"],
      ["path", "M11 14.8l-2.6 6.2"], ["path", "M11 14.8l2.2 6.2"],
      ["line", 17.4, 8.6, 17.4, 21], ["path", "M15.6 8.6h3.6"]],
    celula: [["circle", 12, 12, 8.4], ["circle", 12, 12, 3],
      ["circle", 8.4, 8.6, 1], ["circle", 15.8, 9.2, 1], ["circle", 9.2, 16, 1],
      ["circle", 16, 15.4, 1]],
    balanca: [["line", 12, 3.6, 12, 20.4], ["line", 7, 20.4, 17, 20.4],
      ["line", 4.4, 7.4, 19.6, 7.4], ["path", "M4.4 7.4L2 13.4h4.8z"],
      ["path", "M19.6 7.4L17.2 13.4H22z"], ["circle", 12, 5.4, 1.2]],

    /* ------------------------------------------------------------------
       A historia do laboratorio. Um marco de linha do tempo nao e um
       numero: quem le a aba de historia le desenho antes de ler texto, e
       estes seis existem para que cada caixa se reconheca de longe.
       ------------------------------------------------------------------ */
    raizes: [["line", 12, 4.8, 12, 19],
      ["path", "M12 9.6L8.4 6.4"], ["path", "M12 12.6l3.6-3.2"],
      ["circle", 12, 3.4, 1.6], ["circle", 7.2, 5.2, 1.5], ["circle", 16.8, 7.9, 1.5],
      ["path", "M12 19c-1.6 0-2.8.7-3.6 2.1"], ["path", "M12 19c1.6 0 2.8.7 3.6 2.1"]],
    semente: [["line", 7.5, 21, 16.5, 21], ["path", "M12 21v-6.6"],
      ["path", "M12 14.4c0-3.2-2.4-5.2-5.6-5.2 0 3.2 2.4 5.2 5.6 5.2z"],
      ["path", "M12 15c0-3.5 2.6-5.7 6-5.7 0 3.5-2.6 5.7-6 5.7z"]],
    sono: [["path", "M20 14.4A8.2 8.2 0 0 1 9.6 4a8.6 8.6 0 1 0 10.4 10.4z"],
      ["path", "M14.6 3.4h3.8l-3.8 4.2h3.8"]],
    humor: [["circle", 12, 12, 8.5],
      ["path", "M8.4 14.2c.9 1.2 2.1 1.8 3.6 1.8s2.7-.6 3.6-1.8"],
      ["circle", 9.3, 9.8, 1], ["circle", 14.7, 9.8, 1]],
    serenidade: [["circle", 12, 7.4, 3.4],
      ["path", "M3 15c2-1.6 3.4-1.6 5.4 0s3.4 1.6 5.4 0 3.4-1.6 5.2 0"],
      ["path", "M3 19.2c2-1.6 3.4-1.6 5.4 0s3.4 1.6 5.4 0 3.4-1.6 5.2 0"]],
    comunidade: [["path", "M12 11.6S9 9.7 9 8a1.7 1.7 0 0 1 3-1 1.7 1.7 0 0 1 3 1c0 1.7-3 3.6-3 3.6z"],
      ["path", "M3.5 14.6c1.8-1 3.4-.6 4.6.6l3.9 3.9"],
      ["path", "M20.5 14.6c-1.8-1-3.4-.6-4.6.6L12 19.1"],
      ["line", 3.5, 14.6, 3.5, 20.4], ["line", 20.5, 14.6, 20.5, 20.4]],

    /* controles do mural */
    tocar: [["path", "M8 5.2l10 6.8-10 6.8z"]],
    pausa: [["rect", 7.4, 5, 3.4, 14, 1.2], ["rect", 13.2, 5, 3.4, 14, 1.2]],
    proximo: [["path", "M8 5.5l7.5 6.5L8 18.5"], ["line", 17.6, 5.5, 17.6, 18.5]],
    anterior: [["path", "M16 5.5L8.5 12l7.5 6.5"], ["line", 6.4, 5.5, 6.4, 18.5]],
    telaCheia: [["path", "M4 9V5.5A1.5 1.5 0 0 1 5.5 4H9"], ["path", "M15 4h3.5A1.5 1.5 0 0 1 20 5.5V9"],
      ["path", "M20 15v3.5a1.5 1.5 0 0 1-1.5 1.5H15"], ["path", "M9 20H5.5A1.5 1.5 0 0 1 4 18.5V15"]],
  };

  /* Tom padrao de cada icone. E cromo, nao marca de dado: a paleta validada
     continua mandando no grafico, e aqui a cor so ajuda a achar o cartao. */
  const TOM = {
    painel: "azul", producao: "azul", pessoas: "violeta", processo: "ambar",
    espaco: "verde", dados: "azul", explorar: "azul", barras: "azul", linha: "azul",
    rede: "violeta", calendario: "magenta", relogio: "ambar", submissao: "azul",
    aceite: "bom", citacao: "violeta", projeto: "laranja", linhas: "verde",
    achado: "ambar", qualidade: "bom", automacao: "violeta", mapa: "verde",
    tempo: "azul", alvo: "laranja", subida: "bom", livro: "violeta", raio: "ambar",
    aviso: "alerta", baixar: "azul", atualizar: "azul", conectar: "verde",
    prazo: "alerta", reuniao: "magenta", anuncio: "laranja", tese: "violeta",
    bolsa: "ambar", trofeu: "ambar", foguete: "laranja", experimento: "verde",
    sino: "alerta", apresentacao: "azul", mural: "azul", fogo: "laranja",
    financiamento: "bom", hierarquia: "violeta", orientacao: "violeta",
    etiqueta: "magenta", filtro: "azul", pessoa: "violeta", mensagem: "azul",
    instituicao: "verde", tocar: "azul", pausa: "azul", proximo: "azul",
    anterior: "azul", telaCheia: "azul",
    /* o domínio do laboratório */
    halteres: "azul", corrida: "verde", coracao: "magenta", cerebro: "violeta",
    /* "dor" fica em magenta, e nao no tom de alerta: a linha de
       fibromialgia e um assunto de pesquisa, e nao um aviso na tela.
       Os tons de estado ficam reservados para estado. */
    dor: "magenta", pulmao: "azul", fita: "ambar", envelhecimento: "laranja",
    celula: "violeta", balanca: "verde",
    /* a historia */
    raizes: "verde", semente: "verde", sono: "violeta", humor: "ambar",
    serenidade: "azul", comunidade: "magenta",
  };

  function draw(spec) {
    const kind = spec[0];
    const node = document.createElementNS(NS, kind === "ellipse" ? "ellipse" : kind);
    if (kind === "path") node.setAttribute("d", spec[1]);
    else if (kind === "circle") {
      node.setAttribute("cx", spec[1]); node.setAttribute("cy", spec[2]);
      node.setAttribute("r", spec[3]);
    } else if (kind === "ellipse") {
      node.setAttribute("cx", spec[1]); node.setAttribute("cy", spec[2]);
      node.setAttribute("rx", spec[3]); node.setAttribute("ry", spec[4]);
    } else if (kind === "line") {
      node.setAttribute("x1", spec[1]); node.setAttribute("y1", spec[2]);
      node.setAttribute("x2", spec[3]); node.setAttribute("y2", spec[4]);
    } else if (kind === "rect") {
      node.setAttribute("x", spec[1]); node.setAttribute("y", spec[2]);
      node.setAttribute("width", spec[3]); node.setAttribute("height", spec[4]);
      node.setAttribute("rx", spec[5] === undefined ? 2 : spec[5]);
    }
    return node;
  }

  /* Devolve um <svg class="icon">. Nome desconhecido não quebra o painel:
     vira um ponto discreto, e a aba continua legível pelo rótulo. */
  function get(name, size) {
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "icon");
    svg.setAttribute("viewBox", "0 0 24 24");
    /* size null: quem manda no tamanho e o CSS do contexto (1em) */
    if (size !== null) {
      svg.setAttribute("width", size || 18);
      svg.setAttribute("height", size || 18);
    }
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.75");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    (SET[name] || [["circle", 12, 12, 2]]).forEach(function (spec) {
      svg.appendChild(draw(spec));
    });
    return svg;
  }

  /* Versao com presenca: o mesmo tracado sobre uma pastilha colorida, com
     contorno e brilho proprios. Serve de cromo -- cabecalho, KPI, mural --
     e nunca de marca de dado, onde vale a paleta validada. */
  function badge(name, tone, size) {
    const wrap = document.createElement("span");
    wrap.className = "ibadge t-" + (tone || TOM[name] || "azul");
    wrap.setAttribute("aria-hidden", "true");
    if (size) wrap.style.setProperty("--badge", String(size) + "px");
    wrap.appendChild(get(name, null));
    return wrap;
  }

  function has(name) { return Object.prototype.hasOwnProperty.call(SET, name); }
  function names() { return Object.keys(SET); }
  function tone(name) { return TOM[name] || "azul"; }

  return { get: get, badge: badge, has: has, names: names, tone: tone };
})();
