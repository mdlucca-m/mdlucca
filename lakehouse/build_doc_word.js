// Documento Word: Triangulação dos resultados (BRUMS · microciclo de pré-temporada)
const fs = require("fs");
const D = require("docx");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageNumber, Header, Footer, TabStopType, TabStopPosition
} = D;

const DIR = __dirname;
const data = JSON.parse(fs.readFileSync(DIR + "/data.json", "utf8"));

// ---------- estilo ----------
const INK = "1a2230", MUT = "5a6b80", ACC = "1b6ec2", LINE = "c9d2dd";
const HEADBG = "1b3a5b", HEADTX = "ffffff", ZEBRA = "eef3f8";
const CW = 9020; // largura de conteúdo (A4, margens de 1440 dxa)
const FONT = "Calibri";

function n(x, d = 1) {
  if (x === null || x === undefined || (typeof x === "number" && isNaN(x))) return "–";
  return Number(x).toFixed(d).replace(".", ",");
}
function pfmt(p) { return p < 0.001 ? "< 0,001" : ("= " + n(p, 3)); }
function sg(x, d = 2) { return (x >= 0 ? "+" : "") + n(x, d); }

// parágrafo de texto: aceita string ou array de runs
function P(content, o = {}) {
  const runs = typeof content === "string"
    ? [new TextRun({ text: content, font: FONT, size: o.size || 21, color: o.color || INK, bold: o.bold, italics: o.italics })]
    : content;
  return new Paragraph({
    children: runs,
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: o.after != null ? o.after : 140, line: o.line || 288, before: o.before || 0 },
    keepNext: o.keepNext, indent: o.indent
  });
}
// runs inline com formatação (negrito por marcador **texto**)
function R(text, o = {}) { return new TextRun({ text, font: FONT, size: o.size || 21, color: o.color || INK, bold: o.bold, italics: o.italics }); }
// converte "texto com **negrito** e *itálico*" numa lista de runs
function rich(str, base = {}) {
  const out = []; const re = /\*\*(.+?)\*\*|\*(.+?)\*/g; let last = 0, m;
  while ((m = re.exec(str))) {
    if (m.index > last) out.push(R(str.slice(last, m.index), base));
    if (m[1] != null) out.push(R(m[1], { ...base, bold: true }));
    else out.push(R(m[2], { ...base, italics: true }));
    last = re.lastIndex;
  }
  if (last < str.length) out.push(R(str.slice(last), base));
  return out;
}
function PR(str, o = {}) { return P(rich(str, { size: o.size, color: o.color }), o); }

function H1(text, num) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 300, after: 130 },
    children: [new TextRun({ text: (num ? num + "   " : "") + text, font: FONT, size: 30, bold: true, color: HEADBG })]
  });
}
function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: FONT, size: 24, bold: true, color: ACC })]
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 },
    children: rich(text, { size: 17, color: MUT, italics: true })
  });
}
function noBorder() {
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  return { top: none, bottom: none, left: none, right: none };
}

// tabela de dados: headers=[{t,w,al}], rows=[[{t,al,bold,color}]]
function DT(headers, rows, o = {}) {
  const thin = { style: BorderStyle.SINGLE, size: 4, color: LINE };
  const cellB = { top: thin, bottom: thin, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } };
  const widths = headers.map(h => h.w);
  const hdr = new TableRow({
    tableHeader: true,
    children: headers.map(h => new TableCell({
      width: { size: h.w, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: HEADBG, color: "auto" },
      margins: { top: 60, bottom: 60, left: 90, right: 90 },
      verticalAlign: "center",
      children: [new Paragraph({
        alignment: h.al || AlignmentType.LEFT, spacing: { after: 0, line: 240 },
        children: [new TextRun({ text: h.t, font: FONT, size: 18, bold: true, color: HEADTX })]
      })]
    }))
  });
  const trs = rows.map((r, ri) => new TableRow({
    children: r.map((c, ci) => new TableCell({
      width: { size: widths[ci], type: WidthType.DXA },
      shading: ri % 2 ? { type: ShadingType.CLEAR, fill: ZEBRA, color: "auto" } : undefined,
      margins: { top: 46, bottom: 46, left: 90, right: 90 },
      verticalAlign: "center",
      children: [new Paragraph({
        alignment: c.al || headers[ci].al || AlignmentType.LEFT, spacing: { after: 0, line: 240 },
        children: rich(String(c.t), { size: 18, bold: c.bold, color: c.color || INK })
      })]
    }))
  }));
  return new Table({
    columnWidths: widths, width: { size: CW, type: WidthType.DXA },
    borders: { top: thin, bottom: thin, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE }, insideHorizontal: thin, insideVertical: { style: BorderStyle.NONE } },
    rows: [hdr, ...trs]
  });
}
function spacer(after = 120) { return new Paragraph({ spacing: { after }, children: [] }); }

function figure(file, capText, wPx = 640) {
  const img = fs.readFileSync(DIR + "/" + file);
  // proporções conhecidas (largura/altura) das figuras geradas
  const ratios = { "fig_traj.png": 8.4 / 4.6, "fig_agudo.png": 8.4 / 4.4, "fig_contrast.png": 8.4 / 4.3, "fig_perfis_dia.png": 8.4 / 4.5, "fig_sono_perfil.png": 7.4 / 4.2 };
  const rt = ratios[file] || 1.8;
  const w = wPx, hgt = Math.round(w / rt);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 120, after: 0 },
      children: [new ImageRun({ type: "png", data: img, transformation: { width: w, height: hgt } })]
    }),
    caption(capText)
  ];
}

// nota destacada (faixa lateral)
function callout(str, color = ACC) {
  return new Paragraph({
    spacing: { before: 120, after: 160, line: 288 },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color, space: 12 } },
    indent: { left: 200 },
    children: rich(str, { size: 20, color: INK })
  });
}

const PRETTY = {
  "depressao": "depressão", "raiva": "raiva", "fadiga": "fadiga", "confusao": "confusão",
  "vigor": "vigor", "tensao": "tensão", "pth": "PTH", "epworth": "Epworth (sonolência)",
  "pss": "PSS (estresse)"
};
function prettyPar(par) {
  return par.split(" × ").map(s => PRETTY[s.trim()] || s).join(" × ");
}

// ============================ CONTEÚDO ============================
const kids = [];

// -------- Capa --------
kids.push(new Paragraph({ spacing: { before: 400, after: 0 }, children: [] }));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "TRIANGULAÇÃO DOS RESULTADOS", font: FONT, size: 40, bold: true, color: HEADBG })]
}));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 300 },
  children: [new TextRun({ text: "Sensibilidade e resposta do humor, da sonolência e do estresse aos estímulos de um microciclo de pré-temporada", font: FONT, size: 24, italics: true, color: ACC })]
}));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: rich(`Monitoramento do estado de humor (BRUMS) de **${data.n_atletas} atletas** de handebol de alto rendimento ao longo de **${data.n_dias} dias**, com **${data.n_resp} observações** pareadas por atleta`, { size: 20, color: MUT })
}));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 350 },
  children: [new TextRun({ text: "Análise descritiva robusta, segmentação por variável e triangulação metodológica", font: FONT, size: 19, color: MUT })]
}));
kids.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 500 },
  border: { top: { style: BorderStyle.SINGLE, size: 6, color: LINE }, bottom: { style: BorderStyle.SINGLE, size: 6, color: LINE } },
  children: []
}));

// -------- 1. Introdução --------
kids.push(H1("Introdução e objetivo", "1"));
kids.push(PR("O acompanhamento diário do estado de humor por meio da Escala de Humor de Brunel (BRUMS) oferece uma janela sensível para o modo como o atleta responde à carga de treino. Durante um microciclo de pré-temporada, o organismo alterna sessões de alta intensidade intervalada (HIIT) com jogos amistosos, tarefas de força e dias de recuperação relativa. Cada estímulo impõe demandas distintas, e o humor funciona como um marcador precoce dessas demandas, muitas vezes antes que indicadores fisiológicos se tornem evidentes."));
kids.push(PR("Este relatório persegue uma pergunta central: **quais variáveis do humor, da sonolência e do estresse mais respondem a cada estímulo** (HIIT e jogo amistoso), de que maneira essas medidas se comportam ao longo da semana e como os novos perfis de humor se conectam à sonolência e ao estresse nos dias de maior demanda. Para responder com segurança, o estudo recorre à **triangulação**: em vez de confiar em um único teste, cruza métodos independentes (efeitos agudos pareados, contrastes entre tipos de dia, coeficientes de variação, confiabilidade entre dias, classificação de perfis e comparações entre grupos). Quando caminhos analíticos distintos convergem para a mesma direção, o achado adquire robustez; quando um resultado isolado não resiste à correção por múltiplas comparações, o texto o trata como tendência, sem exagero interpretativo."));
kids.push(callout("A triangulação não busca um veredito único. Ela procura o **padrão que sobrevive a vários olhares**, o que reduz o risco de confundir ruído amostral com sinal verdadeiro.", ACC));

// -------- 2. Método --------
kids.push(H1("Delineamento, medidas e estratégia estatística", "2"));
kids.push(PR(`A amostra reúne ${data.n_atletas} atletas do sexo masculino, todos integrantes do mesmo elenco, avaliados em ${data.n_dias} dias consecutivos de um microciclo de pré-temporada. Cada dia recebeu uma classificação de estímulo: linha de base (D1), HIIT (D2, D4 e D7), jogo amistoso (D3 e D5) e força (D6). O humor foi medido pela BRUMS em seis dimensões (tensão, depressão, raiva, vigor, fadiga e confusão), das quais derivam a fadiga física, a perturbação total do humor (PTH) e o próprio perfil. A sonolência diurna foi captada pela Escala de Sonolência de Epworth e o estresse percebido pela Perceived Stress Scale (PSS).`));
kids.push(PR("Em cada dia, a primeira resposta representa o estado **pré** e a última representa o estado **pós**, o que viabiliza a leitura do efeito agudo intra-dia. A estatística acompanha a natureza pareada e não normal dos escores: o teste de Wilcoxon avalia as mudanças pré para pós, com o tamanho de efeito dz de Cohen para medidas repetidas; o contraste entre HIIT e jogo compara as médias por atleta e corrige oito testes simultâneos pelo procedimento de Benjamini-Hochberg (FDR); a confiabilidade entre dias apoia-se no coeficiente de correlação intraclasse ICC(A,1) e ICC(A,k); os grupos de perfil são comparados pelo teste de Kruskal-Wallis; as associações entre variáveis empregam a correlação de Spearman no nível do atleta, o que evita pseudorreplicação."));
kids.push(callout("O estudo trabalha com **grupo único** (todos os atletas recebem os mesmos estímulos), sem grupo controle. Por essa razão, as leituras têm caráter **descritivo e de rastreio**, e não estabelecem relações causais. A magnitude do efeito segue a convenção usual: trivial (dz < 0,20), pequeno (0,20 a 0,49), médio (0,50 a 0,79) e grande (≥ 0,80).", "b0862a"));

// -------- 3. Descritiva --------
kids.push(H1("Análise descritiva do estado de humor", "3"));
kids.push(PR("A leitura descritiva estabelece o ponto de partida. A Tabela 1 resume cada dimensão pela média, pelo desvio padrão, pela amplitude observada e pelo coeficiente de variação (CV), que expressa a dispersão relativa ao redor da média."));
{
  const rows = data.desc.map(r => [
    { t: r.lab, bold: true }, { t: n(r.media, 1), al: AlignmentType.CENTER },
    { t: n(r.dp, 1), al: AlignmentType.CENTER },
    { t: (r.minimo < 0 ? "−" + Math.abs(r.minimo) : r.minimo) + "–" + r.maximo, al: AlignmentType.CENTER },
    { t: n(r.cv, 0) + "%", al: AlignmentType.CENTER }
  ]);
  kids.push(DT([
    { t: "Dimensão", w: 2600 }, { t: "Média", w: 1400, al: AlignmentType.CENTER },
    { t: "DP", w: 1400, al: AlignmentType.CENTER }, { t: "Amplitude", w: 1810, al: AlignmentType.CENTER },
    { t: "CV", w: 1810, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 1.** Estatística descritiva das dimensões do humor (escores BRUMS, 0 a 16)."));
}
kids.push(PR("Dois padrões saltam à vista. De um lado, as dimensões de **ativação e fadiga** (vigor, fadiga e a fadiga física derivada) apresentam médias intermediárias e dispersão relativa contida, o que as torna leituras estáveis e confiáveis. De outro, as dimensões **negativas** (tensão, depressão, raiva e confusão) exibem médias baixas e desvios amplos: muitos atletas pontuam próximo de zero em vários dias, e essa concentração no piso amplia o CV, ainda que a oscilação absoluta seja modesta. A PTH, por combinar todas as dimensões, ocupa uma posição intermediária e resume o clima afetivo do grupo."));
kids.push(PR("A trajetória semanal (Figura 1) traduz esse retrato estático em movimento. O vigor decresce de forma quase monotônica ao longo do microciclo, enquanto a fadiga sobe no sentido oposto; as duas curvas se cruzam por volta do quarto dia, marco clássico do acúmulo de carga. A PTH descreve um padrão em zigue-zague que merece destaque: eleva-se nos dias de HIIT (D2 e D4), recua nos dias de jogo (D3 e D5) e dispara no fechamento da semana (D7). Os pontos de inflexão assinalados na figura evidenciam que a perturbação do humor não cresce de modo uniforme, mas responde ao tipo de estímulo de cada dia."));
kids.push(...figure("fig_traj.png", "**Figura 1.** Trajetória diária do vigor, da fadiga, da tensão e da PTH ao longo do microciclo. Círculos vazados assinalam pontos de inflexão (máximos e mínimos locais). O rótulo de cada dia indica o tipo de estímulo."));

// -------- 4. Variação e confiabilidade --------
kids.push(H1("Variação e confiabilidade por variável", "4"));
kids.push(PR("A utilidade de um marcador para monitorar carga depende de duas propriedades: variação suficiente para captar mudanças reais e estabilidade suficiente para que a leitura seja reprodutível. A Tabela 2 decompõe o coeficiente de variação em vários recortes e acrescenta o ICC(A,1), que quantifica a concordância entre os dias da semana."));
kids.push(PR("Os recortes do CV respondem à pergunta sobre onde a variabilidade se concentra. O **CV intra-dia** compara a primeira e a última resposta do mesmo atleta no mesmo dia; o **CV pré e pós do dia** contrasta a dispersão no início e no fim da jornada; o **CV pré e pós da semana** confronta o primeiro dia (D1) com o último (D7); e o **CV da semana** mede a oscilação das médias diárias do grupo."));
{
  const rows = data.cv.map(r => [
    { t: r.lab, bold: true },
    { t: n(r.media, 2), al: AlignmentType.CENTER },
    { t: n(r.cv_total, 0) + "%", al: AlignmentType.CENTER },
    { t: n(r.cv_intradia, 0) + "%", al: AlignmentType.CENTER },
    { t: n(r.cv_pre_dia, 0) + " / " + n(r.cv_pos_dia, 0), al: AlignmentType.CENTER },
    { t: n(r.cv_pre_sem, 0) + " / " + n(r.cv_pos_sem, 0), al: AlignmentType.CENTER },
    { t: n(r.cv_semana, 0) + "%", al: AlignmentType.CENTER },
    { t: n(r.icc, 2), al: AlignmentType.CENTER, bold: true, color: r.icc >= 0.75 ? "1b7a3d" : r.icc >= 0.5 ? "b0862a" : "b03030" }
  ]);
  kids.push(DT([
    { t: "Dimensão", w: 1560 },
    { t: "Média", w: 900, al: AlignmentType.CENTER },
    { t: "CV total", w: 1000, al: AlignmentType.CENTER },
    { t: "CV intra-dia", w: 1120, al: AlignmentType.CENTER },
    { t: "CV pré/pós dia", w: 1360, al: AlignmentType.CENTER },
    { t: "CV pré/pós sem.", w: 1360, al: AlignmentType.CENTER },
    { t: "CV sem.", w: 900, al: AlignmentType.CENTER },
    { t: "ICC(A,1)", w: 820, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 2.** Coeficiente de variação (%) em quatro recortes e confiabilidade entre dias. Cores do ICC: verde ≥ 0,75 (substancial), âmbar 0,50 a 0,74 (moderado), vermelho < 0,50 (fraco)."));
}
kids.push(PR("A **fadiga física** reúne o melhor conjunto de propriedades para monitorar carga: apresenta o menor CV total, dispersão intra-dia contida e confiabilidade apreciável entre dias. Por reunir estabilidade e reprodutibilidade, ela se firma como o indicador mais indicado para dosar a carga interna do treino. A fadiga e o vigor a acompanham de perto, com CV moderado e ICC substancial."));
kids.push(PR("As dimensões negativas revelam o efeito oposto. Depressão, confusão e raiva ostentam CV elevado justamente por partirem de valores baixos, condição na qual pequenas variações absolutas se traduzem em grandes variações relativas. Esse comportamento reduz a leitura individual dia a dia e recomenda o uso dessas dimensões **em conjunto**, seja pela PTH, seja pela classificação de perfil. A PTH ilustra bem a distinção entre os recortes: mantém CV intra-dia mínimo, o que a torna estável dentro do dia, mas exibe CV semanal alto, sinal de que responde com nitidez à progressão da carga ao longo dos sete dias."));
{
  const rows = data.icc.map(r => [
    { t: r.lab, bold: true },
    { t: n(r.icc1, 2), al: AlignmentType.CENTER },
    { t: n(r.icck, 2), al: AlignmentType.CENTER },
    { t: r.label, al: AlignmentType.CENTER }
  ]);
  kids.push(DT([
    { t: "Dimensão", w: 2600 },
    { t: "ICC(A,1)", w: 1810, al: AlignmentType.CENTER },
    { t: "ICC(A,k)", w: 1810, al: AlignmentType.CENTER },
    { t: "Interpretação", w: 2800, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 3.** Confiabilidade entre dias por dimensão do humor. ICC(A,1) refere-se a uma medida isolada; ICC(A,k) refere-se à média da semana."));
}
kids.push(PR("A leitura conjunta das duas tabelas de confiabilidade reforça a conclusão. Uma única medida diária já oferece concordância moderada a substancial para a maioria das dimensões, e a média semanal, expressa pelo ICC(A,k), eleva de forma expressiva essa concordância. Em termos práticos, uma leitura pontual serve para o alerta imediato, ao passo que a média de vários dias entrega uma estimativa muito mais fiel do estado do atleta."));

// -------- 5. Resposta aguda --------
kids.push(H1("Resposta aguda pré para pós, por tipo de dia", "5"));
kids.push(PR("A resposta aguda mede o quanto o estado do atleta se altera entre o início e o fim do dia. A Tabela 4 apresenta o efeito pré para pós de cada dimensão no conjunto da amostra, com o valor de p do teste de Wilcoxon, o tamanho de efeito dz e a respectiva magnitude."));
{
  const rows = data.prepos.map(r => [
    { t: r.lab, bold: true },
    { t: n(r.pre, 2), al: AlignmentType.CENTER },
    { t: n(r.pos, 2), al: AlignmentType.CENTER },
    { t: (r.pct >= 0 ? "+" : "") + r.pct + "%", al: AlignmentType.CENTER },
    { t: "p " + pfmt(r.p), al: AlignmentType.CENTER, color: r.p < 0.05 ? "1b7a3d" : MUT },
    { t: sg(r.dz), al: AlignmentType.CENTER, bold: true },
    { t: r.mag, al: AlignmentType.CENTER }
  ]);
  kids.push(DT([
    { t: "Dimensão", w: 1820 },
    { t: "Pré", w: 1000, al: AlignmentType.CENTER },
    { t: "Pós", w: 1000, al: AlignmentType.CENTER },
    { t: "Δ%", w: 900, al: AlignmentType.CENTER },
    { t: "p (Wilcoxon)", w: 1600, al: AlignmentType.CENTER },
    { t: "dz", w: 900, al: AlignmentType.CENTER },
    { t: "Magnitude", w: 1800, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 4.** Efeito agudo intra-dia (média pré e pós de todos os atleta-dias), no conjunto da amostra."));
}
kids.push(PR("O panorama geral confirma o custo agudo do treino: a fadiga e a fadiga física sobem de maneira consistente entre o início e o fim do dia, ao passo que o vigor recua. A PTH acompanha essa deterioração, o que sinaliza uma piora global do humor ao longo da jornada. As dimensões negativas ensaiam altas de menor porte, coerentes com um desconforto afetivo discreto."));
kids.push(PR("O passo seguinte separa esse efeito agudo por tipo de estímulo (Figura 2). A distinção é reveladora. No **jogo amistoso**, a assinatura é quase pura fadiga: a fadiga física dispara, o vigor cede um pouco, mas as dimensões negativas praticamente não se movem. No **HIIT**, ao custo físico soma-se um componente afetivo: além da fadiga física, aparecem elevações de tensão, de PTH e das negativas. O maior efeito agudo isolado de toda a série é o da fadiga física no HIIT, de magnitude grande, seguido pela fadiga física no jogo, de magnitude média."));
kids.push(...figure("fig_agudo.png", "**Figura 2.** Tamanho de efeito agudo (dz, pré para pós) de cada dimensão no HIIT e no jogo amistoso. Valores acima de zero indicam piora (mais fadiga ou mais afeto negativo); abaixo de zero, queda de vigor."));
{
  const order = ["vigor", "fadiga", "fadfisica", "tensao", "depressao", "raiva", "confusao", "pth"];
  const labs = { vigor: "Vigor", fadiga: "Fadiga", fadfisica: "Fadiga física", tensao: "Tensão", depressao: "Depressão", raiva: "Raiva", confusao: "Confusão", pth: "PTH" };
  const byvt = {}; data.acute.forEach(a => { (byvt[a.var] = byvt[a.var] || {})[a.tipo] = a; });
  const rows = order.map(k => {
    const hi = byvt[k].HIIT, jo = byvt[k].Jogo, ou = byvt[k].Outro;
    return [
      { t: labs[k], bold: true },
      { t: sg(hi.dz) + (hi.sig ? " *" : ""), al: AlignmentType.CENTER, color: hi.sig ? "1b7a3d" : INK },
      { t: sg(jo.dz) + (jo.sig ? " *" : ""), al: AlignmentType.CENTER, color: jo.sig ? "1b7a3d" : INK },
      { t: sg(ou.dz) + (ou.sig ? " *" : ""), al: AlignmentType.CENTER, color: ou.sig ? "1b7a3d" : INK }
    ];
  });
  kids.push(DT([
    { t: "Dimensão", w: 2620 },
    { t: "HIIT (dz)", w: 2130, al: AlignmentType.CENTER },
    { t: "Jogo (dz)", w: 2130, al: AlignmentType.CENTER },
    { t: "Outro (dz)", w: 2140, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 5.** Efeito agudo dz por tipo de dia. O asterisco (*) marca p < 0,05 no teste de Wilcoxon pareado por atleta."));
}
kids.push(PR("A Tabela 5 detalha esses efeitos e acrescenta os dias de outra natureza (linha de base e força). A fadiga física alcança significância nos três contextos, prova de que responde a qualquer demanda. O vigor cai de modo significativo nos dias de outra natureza, quando o repouso relativo evidencia o desgaste acumulado. Já a PTH atinge significância no HIIT, o que a confirma como termômetro sensível do estímulo intervalado."));

// -------- 6. Contraste HIIT x jogo --------
kids.push(H1("Contraste direto entre HIIT e jogo amistoso", "6"));
kids.push(PR("Se o efeito agudo mostra o que acontece dentro de cada dia, o contraste direto responde a uma pergunta complementar: qual estímulo pesa mais sobre cada dimensão? A Figura 3 ordena as dimensões pela diferença padronizada entre a média no HIIT e a média no jogo, calculada com pareamento por atleta. Valores positivos apontam escores maiores no HIIT."));
kids.push(...figure("fig_contrast.png", "**Figura 3.** Contraste HIIT menos jogo (dz), pareado por atleta. Em laranja, as dimensões com p < 0,05 nominal; em cinza, as demais. Nenhuma diferença sobrevive à correção por FDR (oito testes)."));
{
  const rows = data.contrast.slice().sort((a, b) => b.dz - a.dz).map(r => [
    { t: r.lab, bold: true },
    { t: n(r.hiit, 2), al: AlignmentType.CENTER },
    { t: n(r.jogo, 2), al: AlignmentType.CENTER },
    { t: sg(r.dz), al: AlignmentType.CENTER, bold: true },
    { t: r.mag, al: AlignmentType.CENTER },
    { t: "p " + pfmt(r.p), al: AlignmentType.CENTER, color: r.p < 0.05 ? "b0862a" : MUT },
    { t: "q " + pfmt(r.fdr), al: AlignmentType.CENTER, color: r.sig_fdr ? "1b7a3d" : MUT }
  ]);
  kids.push(DT([
    { t: "Dimensão", w: 1760 },
    { t: "Média HIIT", w: 1300, al: AlignmentType.CENTER },
    { t: "Média jogo", w: 1300, al: AlignmentType.CENTER },
    { t: "dz", w: 900, al: AlignmentType.CENTER },
    { t: "Magnitude", w: 1400, al: AlignmentType.CENTER },
    { t: "p", w: 1180, al: AlignmentType.CENTER },
    { t: "q (FDR)", w: 1180, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 6.** Contraste HIIT versus jogo por dimensão. p refere-se ao teste nominal; q refere-se ao valor corrigido por Benjamini-Hochberg."));
}
kids.push(PR("O padrão que emerge tem coerência interna notável. As dimensões que mais separam os dois estímulos são todas **afetivas**: raiva, PTH, depressão e confusão ficam de 0,45 a 0,47 desvios acima no HIIT, magnitude que se classifica entre pequena e média. A tensão as segue de perto. Em sentido contrário, o **custo físico** quase não distingue os dois contextos: fadiga, fadiga física e vigor apresentam diferenças triviais, o que revela uma carga interna semelhante entre correr o HIIT e disputar o jogo."));
kids.push(PR("Convém, porém, ler esse resultado com o rigor que ele exige. Nenhuma das oito diferenças resiste isolada à correção por FDR, uma vez que a comparação simultânea de várias dimensões infla a chance de falsos positivos. Por isso, o achado vale como **conjunto convergente**, e não como diferença individual confirmada. Ainda assim, a coerência do padrão (quatro dimensões afetivas apontam na mesma direção, com magnitudes próximas) confere-lhe credibilidade que um único teste positivo não teria. A mensagem prática é direta: o jogo desgasta o corpo sem adoecer o humor, ao passo que o HIIT cobra os dois preços."));

// -------- 7. Perfis --------
kids.push(H1("Perfis de humor: classificação e prevalência", "7"));
kids.push(PR("Além das dimensões isoladas, o humor pode ser lido pela forma do perfil, isto é, pela combinação simultânea das seis dimensões. A classificação adotada segue a taxonomia de Parsons-Smith e distingue seis perfis. O **iceberg** (vigor alto, negativas baixas) e a **superfície** (perfil achatado) representam estados favoráveis. O **submerso** descreve um recolhimento generalizado. A **barbatana de tubarão** isola uma fadiga muito elevada com o restante normal, assinatura de sobrecarga física. O **iceberg invertido** e o **everest invertido** espelham o perfil saudável e sinalizam pior estado psicológico."));
{
  const rows = data.prof_week.map(r => [
    { t: r.perfil, bold: true },
    { t: n(r.prev, 1) + "%", al: AlignmentType.CENTER },
    { t: String(r.n), al: AlignmentType.CENTER }
  ]);
  kids.push(DT([
    { t: "Perfil", w: 3800 },
    { t: "Prevalência na semana", w: 2810, al: AlignmentType.CENTER },
    { t: "N (respostas)", w: 2410, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 7.** Prevalência de cada perfil no conjunto das respostas do microciclo (n = " + data.n_resp + ")."));
}
kids.push(PR("No cômputo da semana, os perfis favoráveis predominam com folga: o iceberg e a superfície respondem, somados, por cerca de dois terços das observações. Esse retrato tranquiliza quanto ao estado geral do elenco, mas não elimina a presença dos perfis de risco e de sobrecarga, que aparecem com frequência suficiente para justificar acompanhamento."));
kids.push(PR("A prevalência ganha muito significado quando se distribui por dia (Tabela 8 e Figura 4), pois é aí que a ligação com o tipo de estímulo se revela. A **barbatana de tubarão** cresce ao longo da semana e atinge o pico no D7, um dia de HIIT, o que a confirma como marca de sobrecarga física acumulada. O **submerso** comparece com mais força nos dias de jogo (D3 e D5), padrão compatível com o recolhimento afetivo que segue o desgaste competitivo. Os perfis favoráveis, embora dominantes, cedem espaço justamente nos dias de maior carga."));
{
  const dcols = [1, 2, 3, 4, 5, 6, 7];
  const porder = ["Iceberg", "Superfície", "Submerso", "Barbatana de tubarão", "Everest invertido", "Iceberg invertido"];
  const rows = porder.map(p => [{ t: p, bold: true }, ...dcols.map((d, i) => ({ t: n(data.prof_day[p][i], 0), al: AlignmentType.CENTER }))]);
  kids.push(DT([
    { t: "Perfil", w: 2902 },
    ...dcols.map(d => ({ t: "D" + d, w: 874, al: AlignmentType.CENTER }))
  ], rows));
  kids.push(caption("**Tabela 8.** Prevalência (%) de cada perfil por dia. D2, D4 e D7 são dias de HIIT; D3 e D5, de jogo amistoso."));
}
kids.push(...figure("fig_perfis_dia.png", "**Figura 4.** Prevalência diária dos perfis mais informativos. A barbatana (sobrecarga) sobe rumo ao fim da semana; o submerso destaca-se nos dias de jogo; o iceberg (favorável) recua nos dias de maior carga. Círculos vazados marcam inflexões."));

// -------- 8. Associações --------
kids.push(H1("Associações e correlações entre as medidas", "8"));
kids.push(PR("A triangulação também examina como as medidas se relacionam entre si. As correlações a seguir foram calculadas no nível do atleta, o que respeita a independência das observações e evita a inflação artificial que resultaria de tratar cada resposta como um caso separado. A Tabela 9 apresenta as associações mais fortes entre as próprias dimensões do humor."));
{
  const rows = data.spearman.map(r => [
    { t: prettyPar(r.par), bold: true },
    { t: n(r.rho, 2), al: AlignmentType.CENTER, bold: true },
    { t: "p " + pfmt(r.p), al: AlignmentType.CENTER, color: r.p < 0.05 ? "1b7a3d" : MUT }
  ]);
  kids.push(DT([
    { t: "Par de dimensões", w: 4200 },
    { t: "ρ (Spearman)", w: 2410, al: AlignmentType.CENTER },
    { t: "p", w: 2410, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 9.** Correlações de Spearman entre dimensões do humor (nível do atleta)."));
}
kids.push(PR("As dimensões negativas caminham juntas, o que confirma a coesão do bloco afetivo: depressão, raiva, confusão e fadiga correlacionam-se de forma positiva e apreciável entre si. Essa convergência sustenta o uso da PTH como resumo único do afeto negativo. O par vigor e fadiga associa-se em sentido inverso, relação esperada entre ativação e cansaço."));
kids.push(PR("A Tabela 10 estende a análise às medidas de sonolência e de estresse, o que aproxima o humor de dois marcadores externos ao BRUMS. Aqui reside uma das descobertas mais úteis do estudo."));
{
  const rows = data.wcorr.map(r => [
    { t: prettyPar(r.par), bold: true },
    { t: n(r.rho, 2), al: AlignmentType.CENTER, bold: true },
    { t: "p " + pfmt(r.p), al: AlignmentType.CENTER, color: r.p < 0.05 ? "1b7a3d" : MUT }
  ]);
  kids.push(DT([
    { t: "Par (medida × humor)", w: 4200 },
    { t: "ρ (Spearman)", w: 2410, al: AlignmentType.CENTER },
    { t: "p", w: 2410, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 10.** Correlações de Spearman entre sonolência (Epworth), estresse (PSS) e dimensões do humor."));
}
kids.push(PR("A sonolência associa-se de modo positivo à fadiga e à PTH e de modo negativo ao vigor, o que a coloca dentro do mesmo eixo do custo físico do treino. O estresse percebido, por sua vez, mostra vínculos fracos e pouco consistentes com o humor. Essa diferença antecipa um resultado que a próxima seção detalha: sono e humor formam um bloco acoplado, ao passo que o estresse percebido corre por fora."));

// -------- 9. Sono e estresse --------
kids.push(H1("Sonolência e estresse: por tipo de dia e por perfil", "9"));
kids.push(PR("Esta seção fecha a triangulação ao ligar a sonolência e o estresse aos dois recortes que mais interessam: o tipo de estímulo e o perfil de humor. A Tabela 11 compara Epworth e PSS entre os tipos de dia e traz o contraste HIIT versus jogo pareado por atleta."));
{
  const rows = data.wb_daytype.map(r => [
    { t: r.medida, bold: true },
    { t: n(r.outro, 1), al: AlignmentType.CENTER },
    { t: n(r.hiit, 1), al: AlignmentType.CENTER, color: "b85c1a" },
    { t: n(r.jogo, 1), al: AlignmentType.CENTER, color: ACC },
    { t: sg(r.dz), al: AlignmentType.CENTER, bold: true },
    { t: "p " + pfmt(r.p) + (r.sig ? " *" : ""), al: AlignmentType.CENTER, color: r.sig ? "1b7a3d" : MUT }
  ]);
  kids.push(DT([
    { t: "Medida", w: 1900 },
    { t: "Outro", w: 1180, al: AlignmentType.CENTER },
    { t: "HIIT", w: 1180, al: AlignmentType.CENTER },
    { t: "Jogo", w: 1180, al: AlignmentType.CENTER },
    { t: "dz (H×J)", w: 1380, al: AlignmentType.CENTER },
    { t: "p", w: 2200, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 11.** Sonolência e estresse por tipo de dia, com contraste HIIT versus jogo (dz pareado). O asterisco marca p < 0,05."));
}
kids.push(PR("A sonolência sobe de forma discreta nos dias de carga, sem separar o HIIT do jogo. O estresse percebido, ao contrário, apresenta um efeito robusto: o PSS recua no dia de jogo em relação ao HIIT, com significância estatística. Apesar do alto volume que a partida impõe, o atleta a percebe como menos estressante do que a sessão intervalada, resultado que reforça o caráter aversivo do HIIT já sugerido pelos contrastes afetivos."));
kids.push(PR("A Tabela 12 desloca o olhar para o perfil de humor e agrupa as observações em três blocos: favorável (iceberg e superfície), neutro e de risco ou sobrecarga (perfis invertidos e barbatana). O teste de Kruskal-Wallis avalia se sonolência e estresse diferem entre os três grupos."));
{
  const rows = data.wb_profile.map(r => [
    { t: r.medida, bold: true },
    { t: n(r.favoravel, 1), al: AlignmentType.CENTER, color: "1b7a3d" },
    { t: n(r.neutro, 1), al: AlignmentType.CENTER, color: "b0862a" },
    { t: n(r.risco, 1), al: AlignmentType.CENTER, color: "b03030" },
    { t: n(r.H, 2), al: AlignmentType.CENTER },
    { t: "p " + pfmt(r.p) + (r.sig ? " *" : ""), al: AlignmentType.CENTER, color: r.sig ? "1b7a3d" : MUT }
  ]);
  kids.push(DT([
    { t: "Medida", w: 1900 },
    { t: "Favorável", w: 1360, al: AlignmentType.CENTER },
    { t: "Neutro", w: 1200, al: AlignmentType.CENTER },
    { t: "Risco", w: 1200, al: AlignmentType.CENTER },
    { t: "H", w: 1160, al: AlignmentType.CENTER },
    { t: "p", w: 2200, al: AlignmentType.CENTER }
  ], rows));
  kids.push(caption("**Tabela 12.** Sonolência e estresse por grupo de perfil de humor, com teste de Kruskal-Wallis. O asterisco marca p < 0,05."));
}
kids.push(...figure("fig_sono_perfil.png", "**Figura 5.** Média de sonolência (Epworth) e de estresse (PSS) por grupo de perfil de humor. A sonolência cresce do grupo favorável ao de risco; o estresse permanece estável.", 560));
kids.push(PR("O desfecho é claro e robusto. A sonolência acompanha o perfil: eleva-se do grupo favorável ao grupo de risco, com diferença significativa pelo teste de Kruskal-Wallis. O estresse percebido, por outro lado, não distingue os três grupos, pois permanece praticamente idêntico entre eles. Sono e humor, portanto, integram um mesmo bloco funcional, ao passo que o estresse percebido segue uma dinâmica própria, desacoplada da forma do perfil."));

// -------- 10. Síntese --------
kids.push(H1("Síntese da triangulação: três eixos de resposta", "10"));
kids.push(PR("O cruzamento de todos os métodos reduz a complexidade das oito variáveis a três eixos independentes de resposta ao estímulo. Cada eixo reúne evidências convergentes e possui uma função prática distinta no monitoramento."));
kids.push(PR([R("Eixo 1, custo físico e sonolência. ", { bold: true, color: "b85c1a" }), R("A fadiga física, a fadiga e a PTH sobem no efeito agudo, acumulam ao longo da semana e reúnem o maior sinal com a melhor reprodutibilidade. Respondem à carga em si, tanto no HIIT quanto no jogo, e por isso servem para dosar a carga interna do treino.")]));
kids.push(PR([R("Eixo 2, afeto e aversão. ", { bold: true, color: "b03030" }), R("A tensão, a depressão, a raiva e a confusão separam o HIIT (aversivo) do jogo (engajador), pois ficam mais altas na sessão intervalada. A direção converge entre os métodos, embora nenhuma dimensão resista sozinha à correção por FDR. Este eixo discrimina o tipo de estímulo e informa sobre o estado psicológico.")]));
kids.push(PR([R("Eixo 3, estresse percebido. ", { bold: true, color: ACC }), R("O PSS mantém-se estável na semana, recua no dia de jogo com efeito robusto e não segue os perfis de humor. A sonolência, ao contrário, acompanha o perfil. Este eixo lembra que o estresse percebido carrega informação própria, que os demais marcadores não capturam.")]));
kids.push(callout("Em conjunto, o painel sugere uma divisão de trabalho no monitoramento: **vigiar a fadiga física para a carga** e **observar o afeto e o perfil para o estado psicológico**, com atenção reforçada aos dias de HIIT no fecho da semana, quando a sobrecarga física se acumula e o desconforto afetivo se acentua.", "1b7a3d"));

// -------- 11. Limitações --------
kids.push(H1("Considerações metodológicas e limitações", "11"));
kids.push(PR("A interpretação dos resultados requer três cautelas. Em primeiro lugar, o estudo trabalha com grupo único, sem controle, de modo que as leituras descrevem e rastreiam, mas não estabelecem causa. Em segundo lugar, o pequeno número de comparações significativas que sobrevivem à correção por FDR recomenda prudência: os padrões afetivos valem como tendência convergente, e a confirmação exigiria amostra maior. Em terceiro lugar, a associação entre perfis de risco e desfechos clínicos de lesão ou de saúde mental é plausível à luz da literatura, porém não foi validada aqui, pois o microciclo não dispõe de desfechos vinculados."));
kids.push(PR("Essas ressalvas não diminuem o valor do trabalho; ao contrário, delimitam com honestidade o que a evidência sustenta. O estudo demonstra a **viabilidade de um rastreio** sensível e reprodutível, capaz de identificar quais variáveis respondem a cada estímulo, quando o risco se concentra e quais atletas merecem acompanhamento individual. A etapa seguinte natural consiste em um estudo prospectivo, com registro sistemático de lesões e de indicadores de saúde mental, que permita transformar a viabilidade demonstrada em validação causal."));
kids.push(spacer(60));
kids.push(new Paragraph({
  border: { top: { style: BorderStyle.SINGLE, size: 6, color: LINE } },
  spacing: { before: 120, after: 40 }, children: []
}));
kids.push(P([R("Nota técnica. ", { bold: true, size: 17, color: MUT }), R("Todos os números deste relatório derivam da camada gold de um lakehouse local e reprodutível (Delta Lake e DuckDB), com sementes fixas e verificação de determinismo e idempotência. As tabelas an_tri_* alimentam simultaneamente este documento e a aba de triangulação do painel interativo, o que garante consistência entre os dois materiais.", { size: 17, color: MUT, italics: true })], { align: AlignmentType.LEFT, after: 0 }));

// ============================ MONTAGEM ============================
const doc = new Document({
  creator: "Monitoramento BRUMS — Handebol",
  title: "Triangulação dos resultados",
  styles: {
    default: { document: { run: { font: FONT, size: 21, color: INK } } }
  },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT, spacing: { after: 0 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE } },
          children: [new TextRun({ text: "Triangulação dos resultados · BRUMS · microciclo de pré-temporada", font: FONT, size: 15, color: MUT })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 0 },
          children: [new TextRun({ children: ["Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], font: FONT, size: 15, color: MUT })]
        })]
      })
    },
    children: kids
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(DIR + "/Triangulacao_resultados.docx", buf);
  console.log("OK ->", DIR + "/Triangulacao_resultados.docx", buf.length, "bytes");
});
