// Documento ABNT: análise descritiva completa + triangulação (BRUMS · handebol)
const fs = require("fs");
const D = require("docx");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageNumber, Header, Footer
} = D;

const DIR = __dirname;
const d = JSON.parse(fs.readFileSync(DIR + "/data.json", "utf8"));

// ---------- ABNT ----------
const FONT = "Times New Roman";
const BODY = 24;        // 12pt
const SMALL = 20;       // 10pt (tabelas/figuras)
const INK = "000000", GREY = "3f3f3f", RULE = "000000";
const CW = 9505;        // largura de conteúdo em Letter com margens 3/2 cm
const LINE15 = 360;     // 1,5
const INDENT = 709;     // 1,25 cm

function n(x, c = 1) {
  if (x === null || x === undefined || (typeof x === "number" && isNaN(x))) return "–";
  return Number(x).toFixed(c).replace(".", ",");
}
function pf(p) { return p < 0.001 ? "< 0,001" : ("= " + n(p, 3)); }
function ic(lo, hi) { return "[" + n(lo, 2) + "; " + n(hi, 2) + "]"; }
function sgn(x, c = 2) { return (x >= 0 ? "+" : "") + n(x, c); }
function mag(x) { const a = Math.abs(x); return a >= .8 ? "grande" : a >= .5 ? "médio" : a >= .2 ? "pequeno" : "trivial"; }

// runs com **negrito** e *itálico*
function rich(str, o = {}) {
  const base = { font: FONT, size: o.size || BODY, color: o.color || INK, bold: o.bold, italics: o.italics };
  const out = []; const re = /\*\*(.+?)\*\*|\*(.+?)\*/g; let last = 0, m;
  while ((m = re.exec(str))) {
    if (m.index > last) out.push(new TextRun({ ...base, text: str.slice(last, m.index) }));
    if (m[1] != null) out.push(new TextRun({ ...base, text: m[1], bold: true }));
    else out.push(new TextRun({ ...base, text: m[2], italics: true }));
    last = re.lastIndex;
  }
  if (last < str.length) out.push(new TextRun({ ...base, text: str.slice(last) }));
  return out;
}
// parágrafo de corpo ABNT (justificado, 1,5, recuo 1,25, sem espaço)
function P(str) {
  return new Paragraph({
    children: rich(str), alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 0, line: LINE15, lineRule: "auto" },
    indent: { firstLine: INDENT }
  });
}
// parágrafo sem recuo (resumo)
function Pflat(str, o = {}) {
  return new Paragraph({
    children: rich(str, o), alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: o.after || 0, line: LINE15, lineRule: "auto" }
  });
}
function H1(numTitle) {
  return new Paragraph({
    children: [new TextRun({ text: numTitle.toUpperCase(), font: FONT, size: BODY, bold: true, color: INK })],
    spacing: { before: 300, after: 140, line: LINE15, lineRule: "auto" }, keepNext: true
  });
}
function H2(numTitle) {
  return new Paragraph({
    children: [new TextRun({ text: numTitle, font: FONT, size: BODY, bold: true, color: INK })],
    spacing: { before: 200, after: 90, line: LINE15, lineRule: "auto" }, keepNext: true
  });
}
function tblTitle(str) {
  return new Paragraph({
    children: rich(str, { size: SMALL }), alignment: AlignmentType.LEFT,
    spacing: { before: 160, after: 40, line: 240 }, keepNext: true
  });
}
function tblSource(str) {
  return new Paragraph({
    children: rich(str, { size: SMALL, color: GREY }), alignment: AlignmentType.LEFT,
    spacing: { before: 40, after: 180, line: 240 }
  });
}
function figCap(str) {
  return new Paragraph({
    children: rich(str, { size: SMALL }), alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 40, line: 240 }, keepNext: true
  });
}
function figSource(str) {
  return new Paragraph({
    children: rich(str, { size: SMALL, color: GREY }), alignment: AlignmentType.CENTER,
    spacing: { before: 40, after: 180, line: 240 }
  });
}
const RATIOS = {
  "fig_framework.png": 9.6 / 6.4, "fig_traj_facets.png": 1440 / 1200, "fig_sono_traj.png": 9.4 / 3.9,
  "fig_tcar.png": 9.6 / 3.6, "fig_perfil_radar.png": 1470 / 930, "fig_prof_day.png": 8.6 / 4.3,
  "fig_agudo.png": 9.0 / 4.2, "fig_contrast.png": 8.6 / 4.1, "fig_sono_perfil.png": 7.4 / 4.0,
  "fig_ice_index.png": 8.6 / 4.0
};
function figure(file, wPx = 600) {
  const img = fs.readFileSync(DIR + "/" + file);
  const rt = RATIOS[file] || 1.7; const w = wPx, h = Math.round(w / rt);
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 40, after: 0 },
    children: [new ImageRun({ type: "png", data: img, transformation: { width: w, height: h } })]
  });
}

// tabela ABNT aberta
function openTable(headers, rows) {
  const line = { style: BorderStyle.SINGLE, size: 6, color: RULE };
  const none = { style: BorderStyle.NONE };
  const widths = headers.map(h => h.w);
  const hcells = headers.map(h => new TableCell({
    width: { size: h.w, type: WidthType.DXA },
    borders: { top: line, bottom: line, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 70, right: 70 }, verticalAlign: "center",
    children: [new Paragraph({ alignment: h.al || AlignmentType.LEFT, spacing: { after: 0, line: 240 },
      children: [new TextRun({ text: h.t, font: FONT, size: SMALL, bold: true, color: INK })] })]
  }));
  const trs = rows.map((r, ri) => new TableRow({
    children: r.map((c, ci) => new TableCell({
      width: { size: widths[ci], type: WidthType.DXA },
      borders: { top: none, bottom: ri === rows.length - 1 ? line : none, left: none, right: none },
      margins: { top: 30, bottom: 30, left: 70, right: 70 }, verticalAlign: "center",
      children: [new Paragraph({ alignment: c.al || headers[ci].al || AlignmentType.LEFT, spacing: { after: 0, line: 240 },
        children: rich(String(c.t), { size: SMALL, bold: c.bold, color: c.color || INK }) })]
    }))
  }));
  return new Table({
    columnWidths: widths, width: { size: CW, type: WidthType.DXA },
    borders: { top: line, bottom: line, left: none, right: none, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ tableHeader: true, children: hcells }), ...trs]
  });
}
const AL = { L: AlignmentType.LEFT, C: AlignmentType.CENTER, R: AlignmentType.RIGHT };
const FONTE_D = "Fonte: Dados da pesquisa (2026).";
const FONTE_E = "Fonte: Elaborado pelos autores (2026).";

const K = []; // corpo

// ====================== CAPA / TÍTULO ======================
K.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 200, after: 120, line: LINE15, lineRule: "auto" },
  children: [new TextRun({ text: "DINÂMICA DO ESTADO DE HUMOR, DA SONOLÊNCIA E DO ESTRESSE EM UM MICROCICLO DE PRÉ-TEMPORADA DE HANDEBOL: ANÁLISE DESCRITIVA, PERFIS E TRIANGULAÇÃO ESTÍMULO E RESPOSTA", font: FONT, size: 28, bold: true, color: INK })]
}));
K.push(Pflat("[Autoria e afiliação a preencher]", { align: AlignmentType.CENTER, size: 22, after: 200 }));

// RESUMO
K.push(new Paragraph({ children: [new TextRun({ text: "RESUMO", font: FONT, size: BODY, bold: true })], spacing: { before: 120, after: 80, line: LINE15, lineRule: "auto" } }));
K.push(Pflat("**Objetivo:** descrever o comportamento do estado de humor, da sonolência e do estresse percebido ao longo de um microciclo de pré-temporada e identificar quais dimensões respondem a cada estímulo (treinamento intervalado de alta intensidade e jogo amistoso), com integração dos achados por triangulação metodológica. **Método:** vinte e sete atletas de handebol do sexo masculino responderam à Escala de Humor de Brunel (BRUMS), à Escala de Sonolência de Epworth e à Perceived Stress Scale durante sete dias, o que resultou em 456 observações pareadas por atleta. A aptidão aeróbia e neuromuscular foi avaliada por teste de campo (T-CAR) e bateria complementar. A análise combinou estatística descritiva (média, desvio padrão, mediana, mínimo, máximo, coeficiente de variação e intervalo de confiança de 95%), confiabilidade entre dias (coeficiente de correlação intraclasse e ômega de McDonald), classificação dos seis perfis de humor por escores padronizados, correlações de Spearman e contrastes entre tipos de dia com correção por taxa de falsa descoberta. **Resultados:** a fadiga física destacou-se como o marcador mais estável e reprodutível; o afeto negativo diferenciou o estímulo intervalado, percebido como mais aversivo, do jogo; a sonolência acompanhou o perfil de humor, ao passo que o estresse percebido seguiu trajetória própria. **Conclusão:** a triangulação sustenta uma divisão funcional do monitoramento, com a carga física vigiada pela fadiga e o estado psicológico observado pelo afeto e pelo perfil.", { after: 80 }));
K.push(Pflat("**Palavras-chave:** Estado de humor. BRUMS. Fadiga. Pré-temporada. Handebol.", { after: 200 }));

// ====================== 1 INTRODUÇÃO ======================
K.push(H1("1 Introdução"));
K.push(P("O monitoramento do estado psicológico do atleta consolidou-se como recurso central da preparação esportiva contemporânea. Entre os instrumentos disponíveis, a Escala de Humor de Brunel (BRUMS) ocupa posição de destaque, pois traduz em seis dimensões (tensão, depressão, raiva, vigor, fadiga e confusão) um construto sensível às oscilações da carga de treino. A literatura consagra o chamado perfil iceberg, proposto por Morgan (1985), no qual o vigor se sobrepõe às dimensões negativas, como marca de equilíbrio afetivo e de boa adaptação. Estudos posteriores refinaram essa leitura e descreveram uma taxonomia de perfis capaz de captar estados menos favoráveis (PARSONS-SMITH; TERRY; MACHIN, 2017; HAN; PARSONS-SMITH; TERRY, 2020)."));
K.push(P("A pré-temporada representa um período crítico para essa vigilância. Nela, o organismo do atleta enfrenta estímulos de naturezas distintas, entre os quais se destacam o treinamento intervalado de alta intensidade (HIIT) e os jogos amistosos. Cada estímulo impõe demandas específicas, e o humor funciona como sensor precoce dessas demandas, muitas vezes antes que marcadores fisiológicos exibam alterações mensuráveis. Convém reconhecer, porém, que a mera descrição de médias diárias esconde nuances relevantes: uma variável pode oscilar muito e mesmo assim carregar pouca informação útil, ao passo que outra, aparentemente discreta, pode discriminar com precisão o tipo de esforço."));
K.push(P("Diante dessa complexidade, o presente estudo adota a triangulação metodológica como estratégia analítica. Em vez de depositar confiança em um único teste, o trabalho cruza abordagens independentes, entre elas a descrição estatística robusta, a análise de confiabilidade, a classificação de perfis, a exploração de correlações e o contraste entre tipos de dia. Quando caminhos distintos convergem para a mesma conclusão, o achado ganha solidez; quando um resultado isolado não resiste à correção por comparações múltiplas, a interpretação permanece cautelosa e o trata como tendência."));
K.push(P("O objetivo geral consiste em descrever o comportamento do humor, da sonolência e do estresse percebido ao longo do microciclo e em identificar quais medidas respondem a cada estímulo. Como objetivos específicos, o estudo pretende caracterizar a distribuição e a confiabilidade das medidas, classificar os atletas segundo os seis perfis de humor, mensurar a resposta aguda por tipo de dia e integrar as evidências em uma síntese aplicável à prática esportiva."));

// ====================== 2 MÉTODO ======================
K.push(H1("2 Método"));
K.push(H2("2.1 Amostra e delineamento"));
K.push(P(`Participaram do estudo ${d.meta.n_atletas} atletas de handebol do sexo masculino, todos integrantes do mesmo elenco, avaliados ao longo de ${d.meta.n_dias} dias consecutivos de um microciclo de pré-temporada. O delineamento observacional de grupo único acompanhou a rotina real da equipe, sem manipulação experimental e sem grupo de comparação. Cada dia recebeu uma classificação de estímulo conforme a sessão predominante, a saber: linha de base técnico-tática (D1), HIIT (D2, D4 e D7), jogo amistoso (D3 e D5) e força (D6). O conjunto reuniu ${d.meta.n_resp} observações pareadas por atleta, o que confere densidade adequada às análises intra-dia e entre dias.`));
K.push(P(`A avaliação da aptidão física recorreu a uma bateria complementar aplicada em ${d.meta.n_fisico} atletas, distribuídos em subgrupos de referência (controle, n = ${d.meta.n_ctrl}; experimental, n = ${d.meta.n_exp}). Por respeito à fronteira de anonimização, esse conjunto físico manteve esquema de identificação próprio, sem junção artificial com os códigos do banco de humor. As leituras físicas, portanto, descrevem uma amostra correlata, e não a mesma unidade de análise do humor.`));

K.push(H2("2.2 Instrumentos"));
K.push(P("O estado de humor foi mensurado pela BRUMS, validada para o português (ROHLFS et al., 2008), em suas seis dimensões, das quais derivam a fadiga física, a perturbação total do humor (PTH) e a classificação do perfil. A sonolência diurna foi avaliada pela Escala de Sonolência de Epworth, e o estresse percebido, pela Perceived Stress Scale (PSS). A aptidão aeróbia foi estimada pelo teste de campo T-CAR, que fornece o pico de velocidade, a frequência cardíaca máxima e o número de repetições completadas. A bateria complementar incluiu o salto com contramovimento (CMJ) e o teste de Baker, além de medidas antropométricas."));

K.push(H2("2.3 Classificação dos perfis de humor"));
K.push(P("A classificação seguiu a taxonomia dos seis perfis descritos por Parsons-Smith, Terry e Machin (2017). Cada uma das seis subescalas foi padronizada na amostra e convertida em escore T (T = 50 + 10z), o que preserva a forma do perfil em uma métrica de leitura direta. A atribuição de cada observação a um perfil obedeceu ao critério do centroide canônico mais próximo, mensurado pela menor distância euclidiana quadrática sobre as seis subescalas padronizadas. Para cada perfil, o estudo reportou indicadores-chave de desempenho descritivo, entre eles a prevalência, o índice-iceberg (definido como o vigor padronizado menos a média das dimensões negativas padronizadas) e a PTH, que resume o perfil em um único número."));

K.push(H2("2.4 Análise estatística"));
K.push(P("A descrição de cada variável incluiu média, desvio padrão, mediana, mínimo, máximo, coeficiente de variação e intervalo de confiança de 95% da média. A confiabilidade entre dias apoiou-se no coeficiente de correlação intraclasse, nas formulações ICC(A,1), para uma medida isolada, e ICC(A,k), para a média da semana, ambas acompanhadas do respectivo intervalo de confiança. A consistência interna das dimensões recorreu ao ômega de McDonald. As mudanças pré para pós foram avaliadas pelo teste de Wilcoxon, com o tamanho de efeito dz de Cohen para medidas repetidas e intervalo de confiança obtido por reamostragem. O contraste entre HIIT e jogo comparou as médias por atleta e ajustou oito testes simultâneos pelo procedimento de Benjamini-Hochberg. As associações entre variáveis empregaram a correlação de Spearman no nível do atleta, o que evita a pseudorreplicação, e os grupos de perfil foram comparados pelo teste de Kruskal-Wallis. Toda a cadeia analítica foi construída sobre um repositório reprodutível, com sementes fixas e verificação de determinismo."));

// Figura 1 — organograma / framework
K.push(figCap("**Figura 1** – Organograma do framework analítico descritivo, da coleta à síntese"));
K.push(figure("fig_framework.png", 600));
K.push(figSource(FONTE_E));

// Tabela 1 — microciclo (treinos diários)
K.push(tblTitle("**Tabela 1** – Caracterização do microciclo de pré-temporada: sessões, carga interna e recuperação percebida ao longo dos sete dias"));
{
  const rows = [
    ["D1", "21/04", "Técnico-tática (base)", "–", "–", "–", "–", "4,7", "13,5"],
    ["D2", "22/04", "HIIT", "79,5", "84,0", "8,3", "201,7", "6,0", "11,4"],
    ["D3", "23/04", "Jogo amistoso", "–", "–", "–", "–", "6,4", "11,4"],
    ["D4", "24/04", "HIIT", "77,6", "79,6", "8,5", "205,7", "7,1", "11,1"],
    ["D5", "25/04", "Jogo amistoso", "–", "–", "–", "–", "6,0", "11,6"],
    ["D6", "26/04", "Força", "–", "–", "–", "–", "6,4", "11,7"],
    ["D7", "27/04", "HIIT", "75,7", "75,2", "8,9", "215,8", "7,6", "9,0"]
  ].map(r => r.map((c, i) => ({ t: c, al: i <= 2 ? AL.L : AL.C, bold: i === 0 })));
  K.push(openTable([
    { t: "Dia", w: 640, al: AL.L }, { t: "Data", w: 820, al: AL.L }, { t: "Sessão", w: 2100, al: AL.L },
    { t: "%FCmáx", w: 1080, al: AL.C }, { t: "TRIMP", w: 1000, al: AL.C }, { t: "PSE", w: 900, al: AL.C },
    { t: "sPSE", w: 1080, al: AL.C }, { t: "Fad. fís.", w: 1080, al: AL.C }, { t: "TQR", w: 805, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: carga interna quantificada apenas nos dias de HIIT (%FCmáx, TRIMP de Banister, PSE 0–10 e sPSE em unidades arbitrárias); fadiga física percebida (0–10) e qualidade total de recuperação (TQR, 6–20) registradas em todos os dias. " + FONTE_D));

// ====================== 3 RESULTADOS ======================
K.push(H1("3 Resultados"));

// 3.1 descritiva humor
K.push(H2("3.1 Estatística descritiva do estado de humor"));
K.push(P("A descrição das dimensões do humor estabelece o ponto de partida da análise. A Tabela 2 reúne, para cada dimensão, as medidas de tendência central e de dispersão, além do intervalo de confiança de 95% da média, o que permite avaliar de modo simultâneo o nível típico e a variabilidade de cada construto."));
K.push(tblTitle("**Tabela 2** – Estatística descritiva das dimensões do humor (escores BRUMS, 0 a 16)"));
{
  const rows = d.mood_desc.map(r => [
    { t: r.lab, bold: true, al: AL.L },
    { t: n(r.media, 1), al: AL.C }, { t: n(r.dp, 1), al: AL.C }, { t: n(r.mediana, 1), al: AL.C },
    { t: n(r.minimo, 0), al: AL.C }, { t: n(r.maximo, 0), al: AL.C }, { t: n(r.cv, 0) + "%", al: AL.C },
    { t: ic(r.ic_lo, r.ic_hi), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Dimensão", w: 1805, al: AL.L }, { t: "Média", w: 950, al: AL.C }, { t: "DP", w: 850, al: AL.C },
    { t: "Mediana", w: 1050, al: AL.C }, { t: "Mín.", w: 750, al: AL.C }, { t: "Máx.", w: 750, al: AL.C },
    { t: "CV", w: 900, al: AL.C }, { t: "IC 95% da média", w: 2450, al: AL.C }
  ], rows));
}
K.push(tblSource(FONTE_D));
K.push(P("A leitura da tabela revela dois agrupamentos nítidos. As dimensões de ativação e de cansaço, ou seja, o vigor, a fadiga e a fadiga física, apresentam médias intermediárias, medianas próximas das médias e dispersão relativa contida, o que sugere leituras estáveis. Em contraste, as dimensões negativas, a tensão, a depressão, a raiva e a confusão, exibem médias baixas e medianas ainda menores, com desvios amplos. Esse quadro reflete a concentração de muitos escores próximos de zero, fenômeno que amplia o coeficiente de variação sem que a oscilação absoluta seja expressiva. A reflexão pertinente aqui diz respeito à interpretação: um coeficiente de variação elevado em uma dimensão de piso não indica instabilidade do atleta, mas sim a assimetria natural de um construto que raramente se manifesta em repouso."));

// 3.2 confiabilidade
K.push(H2("3.2 Confiabilidade entre as medidas"));
K.push(P("A utilidade de um marcador para o monitoramento depende da sua reprodutibilidade. A Tabela 3 apresenta a confiabilidade entre dias, expressa pelo ICC(A,1) e pelo ICC(A,k), acompanhados dos respectivos intervalos de confiança, e complementa a leitura com o ômega de McDonald, que estima a consistência interna de cada dimensão."));
K.push(tblTitle("**Tabela 3** – Confiabilidade entre dias (ICC) e consistência interna (ômega) das dimensões do humor"));
{
  const rows = d.mood_desc.map(r => [
    { t: r.lab, bold: true, al: AL.L },
    { t: n(r.icc1, 2), al: AL.C }, { t: ic(r.icc1_lo, r.icc1_hi), al: AL.C },
    { t: n(r.icck, 2), al: AL.C }, { t: ic(r.icck_lo, r.icck_hi), al: AL.C },
    { t: r.omega != null ? n(r.omega, 2) : "–", al: AL.C }
  ]);
  K.push(openTable([
    { t: "Dimensão", w: 2005, al: AL.L },
    { t: "ICC(A,1)", w: 1200, al: AL.C }, { t: "IC 95%", w: 1900, al: AL.C },
    { t: "ICC(A,k)", w: 1200, al: AL.C }, { t: "IC 95%", w: 1900, al: AL.C },
    { t: "Ômega", w: 1300, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: ICC(A,1) refere-se a uma medida isolada; ICC(A,k), à média da semana; casos completos (n = " + d.mood_desc[0].icc_n + "). " + FONTE_D));
K.push(P("Os resultados sustentam uma conclusão de ordem prática. Uma única medida diária já oferece concordância moderada a substancial para a maior parte das dimensões, e a média semanal eleva de modo expressivo essa concordância, com valores de ICC(A,k) próximos do teto. Em termos aplicados, isso significa que uma leitura pontual serve ao alerta imediato, ao passo que a agregação de vários dias entrega uma estimativa muito mais fiel do estado do atleta. A consistência interna, por sua vez, mostra-se satisfatória, o que respalda o emprego das dimensões tanto de forma isolada quanto combinada na perturbação total do humor."));

// 3.3 sono e estresse descritiva
K.push(H2("3.3 Sonolência e estresse percebido"));
K.push(P("A Tabela 4 descreve a sonolência diurna e o estresse percebido, medidas externas ao BRUMS que ampliam o retrato do estado do atleta. Além das estatísticas usuais, a tabela informa a confiabilidade entre dias da sonolência, cuja estrutura repetida permite o cálculo do ICC."));
K.push(tblTitle("**Tabela 4** – Estatística descritiva da sonolência (Epworth) e do estresse percebido (PSS)"));
{
  const rows = d.wb_desc.map(r => [
    { t: r.lab, bold: true, al: AL.L },
    { t: n(r.media, 1), al: AL.C }, { t: n(r.dp, 1), al: AL.C }, { t: n(r.mediana, 1), al: AL.C },
    { t: n(r.minimo, 0), al: AL.C }, { t: n(r.maximo, 0), al: AL.C },
    { t: ic(r.ic_lo, r.ic_hi), al: AL.C },
    { t: r.icc1 != null ? n(r.icc1, 2) + " " + ic(r.icc1_lo, r.icc1_hi) : "–", al: AL.C }
  ]);
  K.push(openTable([
    { t: "Medida", w: 2400, al: AL.L }, { t: "Média", w: 850, al: AL.C }, { t: "DP", w: 750, al: AL.C },
    { t: "Mediana", w: 950, al: AL.C }, { t: "Mín.", w: 700, al: AL.C }, { t: "Máx.", w: 700, al: AL.C },
    { t: "IC 95%", w: 1355, al: AL.C }, { t: "ICC(A,1) [IC]", w: 1800, al: AL.C }
  ], rows));
}
K.push(tblSource(FONTE_D));
K.push(P("A sonolência situou-se em faixa leve a moderada e apresentou confiabilidade substancial entre dias, o que a credencia como marcador estável de recuperação. O estresse percebido manteve nível intermediário e dispersão moderada. A comparação entre as duas medidas antecipa um contraste que as seções seguintes aprofundam: a sonolência integra o mesmo eixo do cansaço físico, ao passo que o estresse percebido guarda dinâmica própria."));

// 3.4 T-CAR
K.push(H2("3.4 Aptidão aeróbia e neuromuscular (T-CAR)"));
K.push(P("A caracterização física recorreu ao teste de campo T-CAR e a uma bateria complementar. A Tabela 5 detalha todas as métricas do T-CAR na condição pré e pós, com o tamanho de efeito da adaptação e o respectivo intervalo de confiança."));
K.push(tblTitle("**Tabela 5** – Descritiva e adaptação (pré→pós) das métricas do T-CAR e da bateria neuromuscular"));
{
  const all = d.tcar.concat(d.neuro);
  const rows = all.map(r => [
    { t: r.lab + " (" + r.unit + ")", bold: true, al: AL.L },
    { t: n(r.pre.media, 1) + " ± " + n(r.pre.dp, 1), al: AL.C },
    { t: n(r.pre.minimo, 1) + " a " + n(r.pre.maximo, 1), al: AL.C },
    { t: n(r.pos.media, 1) + " ± " + n(r.pos.dp, 1), al: AL.C },
    { t: sgn(r.dz), al: AL.C, bold: true }, { t: ic(r.dz_lo, r.dz_hi), al: AL.C },
    { t: r.mag, al: AL.C }, { t: "p " + pf(r.p), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Métrica", w: 2500, al: AL.L }, { t: "Pré (M±DP)", w: 1250, al: AL.C },
    { t: "Amplitude pré", w: 1150, al: AL.C }, { t: "Pós (M±DP)", w: 1250, al: AL.C },
    { t: "dz", w: 750, al: AL.C }, { t: "IC 95%", w: 1300, al: AL.C },
    { t: "Magn.", w: 700, al: AL.C }, { t: "p", w: 605, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: amostra física (n = " + d.meta.n_fisico + "), esquema de anonimização independente. p do teste de Wilcoxon pareado; IC 95% do dz por reamostragem. " + FONTE_D));
K.push(figCap("**Figura 2** – Adaptação pré→pós das principais métricas do T-CAR"));
K.push(figure("fig_tcar.png", 600));
K.push(figSource(FONTE_E));
K.push(P("O pico de velocidade progrediu de forma expressiva entre os dois momentos, com efeito grande, o que evidencia a resposta aeróbia ao período de trabalho. A frequência cardíaca máxima permaneceu praticamente estável, comportamento esperado para um parâmetro de teto fisiológico, ao passo que o número de repetições completadas cresceu de maneira relevante. A bateria neuromuscular acompanhou a mesma direção adaptativa, com melhora do salto vertical e redução do tempo total no teste de Baker. Convém observar que essa amostra física constitui grupo correlato, e não a mesma unidade das análises de humor, razão pela qual as duas leituras dialogam sem se sobrepor."));
K.push(tblTitle("**Tabela 6** – Caracterização antropométrica e carga percebida da sessão de HIIT"));
{
  const rows = d.anthro.concat(d.carga).map(r => [
    { t: r.lab + " (" + r.unit + ")", bold: true, al: AL.L },
    { t: n(r.media, 1), al: AL.C }, { t: n(r.dp, 1), al: AL.C }, { t: n(r.mediana, 1), al: AL.C },
    { t: n(r.minimo, 1) + " a " + n(r.maximo, 1), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Variável", w: 3200, al: AL.L }, { t: "Média", w: 1400, al: AL.C },
    { t: "DP", w: 1300, al: AL.C }, { t: "Mediana", w: 1600, al: AL.C }, { t: "Amplitude", w: 2005, al: AL.C }
  ], rows));
}
K.push(tblSource(FONTE_D));

// 3.5 trajetória
K.push(H2("3.5 Trajetória semanal e pontos de inflexão"));
K.push(P("A descrição estática ganha sentido quando se observa a evolução ao longo dos sete dias. A Figura 3 apresenta a trajetória de cada dimensão em painéis separados, o que evita a sobreposição de linhas e destaca os pontos de inflexão, isto é, os máximos e mínimos locais em que a tendência muda de direção."));
K.push(figCap("**Figura 3** – Trajetória diária das dimensões do humor, com pontos de inflexão assinalados"));
K.push(figure("fig_traj_facets.png", 600));
K.push(figSource(FONTE_E));
K.push(P("O vigor decresce de modo quase monotônico, enquanto a fadiga percorre o caminho inverso. A perturbação total do humor descreve um padrão em serrote de leitura eloquente: eleva-se nos dias de HIIT, recua nos dias de jogo e dispara no encerramento da semana. As dimensões negativas oscilam em faixa estreita, com repiques discretos nos dias de maior demanda. A Figura 4 estende a mesma lógica à sonolência e ao estresse, que sobem levemente nos dias de carga sem romper a estabilidade geral."));
K.push(figCap("**Figura 4** – Trajetória diária da sonolência (Epworth) e do estresse percebido (PSS)"));
K.push(figure("fig_sono_traj.png", 600));
K.push(figSource(FONTE_E));

// 3.6 perfis
K.push(H2("3.6 Perfis de humor: assinatura, prevalência e indicadores"));
K.push(P("Para além das dimensões isoladas, o humor pode ser lido pela forma do perfil, que combina as seis subescalas em um padrão único. A Figura 5 apresenta a assinatura dos seis perfis em escores T, com a faixa normal situada entre 40 e 60. O iceberg exibe o vigor elevado sobre negativas rebaixadas; a superfície mantém o padrão achatado; o submerso reúne todas as dimensões abaixo da média; a barbatana de tubarão isola um pico de fadiga; o iceberg invertido e o everest invertido espelham o perfil saudável e sinalizam pior estado psicológico."));
K.push(figCap("**Figura 5** – Assinatura dos seis perfis de humor em escores T (T = 50 + 10z)"));
K.push(figure("fig_perfil_radar.png", 600));
K.push(figSource(FONTE_E));
K.push(P("A Tabela 7 quantifica cada perfil por meio de indicadores-chave: a prevalência no conjunto das respostas, o número de atletas que assumiram o perfil ao menos uma vez, o índice-iceberg, o vigor médio, a fadiga média e a perturbação total do humor. Esses indicadores permitem classificar os atletas e comparar os perfis segundo o seu significado clínico."));
K.push(tblTitle("**Tabela 7** – Indicadores descritivos dos seis perfis de humor"));
{
  const rows = d.prof_kpi.map(r => [
    { t: r.perfil, bold: true, al: AL.L },
    { t: n(r.prev, 1) + "%", al: AL.C }, { t: String(r.n), al: AL.C }, { t: r.n_atletas + "/27", al: AL.C },
    { t: sgn(r.indice), al: AL.C }, { t: n(r.vigor, 1), al: AL.C }, { t: n(r.fad, 1), al: AL.C },
    { t: sgn(r.tmd, 1), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Perfil", w: 2350, al: AL.L }, { t: "Prev.", w: 900, al: AL.C }, { t: "N obs.", w: 850, al: AL.C },
    { t: "Atletas", w: 1000, al: AL.C }, { t: "Índice-iceberg", w: 1500, al: AL.C },
    { t: "Vigor", w: 800, al: AL.C }, { t: "Fadiga", w: 900, al: AL.C }, { t: "PTH", w: 1205, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: índice-iceberg = vigor padronizado − média das negativas padronizadas; PTH = perturbação total do humor. Base de respostas (atleta-dia). " + FONTE_D));
K.push(P("O grupo revela-se dominado por perfis favoráveis, uma vez que o iceberg e a superfície respondem, somados, por cerca de dois terços das observações. Ainda assim, os perfis de risco e de sobrecarga comparecem com frequência que justifica vigilância. O índice-iceberg ordena com clareza os perfis do mais saudável ao mais desfavorável, o que confirma a sua utilidade como métrica-resumo para a triagem individual."));
K.push(P("A distribuição dos perfis ao longo dos dias revela a conexão com o tipo de estímulo. A Tabela 8 apresenta a prevalência diária de cada perfil, e a Figura 6 destaca os perfis mais reativos. A barbatana de tubarão cresce ao longo da semana e atinge o pico no sétimo dia, coerente com a sobrecarga física acumulada. O submerso comparece com mais força nos dias de jogo, padrão compatível com o recolhimento afetivo que segue o desgaste competitivo."));
K.push(tblTitle("**Tabela 8** – Prevalência (%) de cada perfil de humor por dia do microciclo"));
{
  const porder = ["Iceberg", "Superfície", "Submerso", "Barbatana de tubarão", "Everest invertido", "Iceberg invertido"];
  const rows = porder.map(p => [{ t: p, bold: true, al: AL.L }, ...[0,1,2,3,4,5,6].map(i => ({ t: n(d.prof_day[p][i], 0), al: AL.C }))]);
  K.push(openTable([
    { t: "Perfil", w: 3100, al: AL.L },
    ...[1,2,3,4,5,6,7].map(dd => ({ t: "D" + dd, w: 915, al: AL.C }))
  ], rows));
}
K.push(tblSource("Nota: D2, D4 e D7 são dias de HIIT; D3 e D5, de jogo amistoso. " + FONTE_D));
K.push(figCap("**Figura 6** – Prevalência diária dos perfis reativos ao estímulo, com pontos de inflexão"));
K.push(figure("fig_prof_day.png", 560));
K.push(figSource(FONTE_E));
K.push(P("O índice-iceberg do grupo, apresentado na Figura 7 com o respectivo intervalo de confiança, sintetiza a deterioração afetiva ao longo da semana. O indicador parte de valor elevado no primeiro dia, oscila conforme o estímulo e recua no encerramento, o que traduz o efeito acumulado da carga sobre o equilíbrio entre vigor e afeto negativo."));
K.push(figCap("**Figura 7** – Índice-iceberg do grupo por dia (vigor − média das negativas), com IC 95%"));
K.push(figure("fig_ice_index.png", 560));
K.push(figSource(FONTE_E));

// 3.7 resposta aguda
K.push(H2("3.7 Resposta aguda pré→pós por tipo de dia"));
K.push(P("A resposta aguda mensura a alteração do estado do atleta entre o início e o fim do dia. A Tabela 9 apresenta o efeito pré para pós de cada dimensão no conjunto da amostra, com o valor de p, o tamanho de efeito e a magnitude correspondente."));
K.push(tblTitle("**Tabela 9** – Efeito agudo intra-dia (pré→pós) das dimensões do humor"));
{
  const rows = d.prepos.map(r => [
    { t: r.lab, bold: true, al: AL.L },
    { t: n(r.pre, 2), al: AL.C }, { t: n(r.pos, 2), al: AL.C },
    { t: (r.pct >= 0 ? "+" : "") + r.pct + "%", al: AL.C },
    { t: "p " + pf(r.p), al: AL.C }, { t: sgn(r.dz), al: AL.C, bold: true }, { t: r.mag, al: AL.C }
  ]);
  K.push(openTable([
    { t: "Dimensão", w: 2000, al: AL.L }, { t: "Pré", w: 1100, al: AL.C }, { t: "Pós", w: 1100, al: AL.C },
    { t: "Variação", w: 1200, al: AL.C }, { t: "p (Wilcoxon)", w: 1700, al: AL.C },
    { t: "dz", w: 900, al: AL.C }, { t: "Magnitude", w: 1505, al: AL.C }
  ], rows));
}
K.push(tblSource(FONTE_D));
K.push(P("O panorama confirma o custo agudo do esforço. A fadiga e a fadiga física sobem de maneira consistente ao longo da jornada, enquanto o vigor recua, e a perturbação total do humor acompanha essa piora global. As dimensões negativas ensaiam altas de menor porte. A Figura 8 separa esse efeito por tipo de estímulo e revela um contraste esclarecedor: no jogo, a assinatura é quase pura fadiga; no HIIT, ao custo físico soma-se um componente afetivo, com repiques de tensão, de perturbação do humor e das negativas."));
K.push(figCap("**Figura 8** – Efeito agudo dz por dimensão no HIIT e no jogo amistoso"));
K.push(figure("fig_agudo.png", 590));
K.push(figSource(FONTE_E));

// 3.8 exploratória
K.push(H2("3.8 Análises exploratórias: associações e correlações"));
K.push(P("A exploração das relações entre as medidas complementa a descrição. As correlações foram calculadas no nível do atleta, o que preserva a independência das observações. A Tabela 10 apresenta as associações mais fortes entre as próprias dimensões do humor, e a Tabela 11 estende a análise à sonolência e ao estresse."));
K.push(tblTitle("**Tabela 10** – Correlações de Spearman entre dimensões do humor (nível do atleta)"));
{
  const PR = { depressao: "depressão", raiva: "raiva", fadiga: "fadiga", confusao: "confusão", vigor: "vigor", tensao: "tensão" };
  const pretty = s => s.split(" × ").map(x => PR[x.trim()] || x).join(" × ");
  const rows = d.spearman.map(r => [
    { t: pretty(r.par), bold: true, al: AL.L }, { t: n(r.rho, 2), al: AL.C, bold: true },
    { t: "p " + pf(r.p), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Par de dimensões", w: 4700, al: AL.L }, { t: "ρ (rô)", w: 2400, al: AL.C }, { t: "p", w: 2405, al: AL.C }
  ], rows));
}
K.push(tblSource(FONTE_D));
K.push(tblTitle("**Tabela 11** – Correlações de Spearman entre sonolência, estresse e humor"));
{
  const PR = { epworth: "Epworth", pss: "PSS", fadiga: "fadiga", vigor: "vigor", pth: "PTH" };
  const pretty = s => s.split(" × ").map(x => PR[x.trim()] || x).join(" × ");
  const rows = d.wcorr.map(r => [
    { t: pretty(r.par), bold: true, al: AL.L }, { t: n(r.rho, 2), al: AL.C, bold: true },
    { t: "p " + pf(r.p), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Par (medida × humor)", w: 4700, al: AL.L }, { t: "ρ (rô)", w: 2400, al: AL.C }, { t: "p", w: 2405, al: AL.C }
  ], rows));
}
K.push(tblSource(FONTE_D));
K.push(P("As dimensões negativas caminham juntas, o que confirma a coesão do bloco afetivo e respalda o uso da perturbação total do humor como resumo. O par vigor e fadiga associa-se em sentido inverso, relação esperada entre ativação e cansaço. Quanto às medidas externas, a sonolência vincula-se de modo positivo à fadiga e à perturbação do humor e de modo negativo ao vigor, o que a situa no eixo do custo físico. O estresse percebido, por outro lado, revela vínculos fracos e pouco consistentes com o humor, indício de que percorre trajetória autônoma."));

// ====================== 4 TRIANGULAÇÃO ======================
K.push(H1("4 Triangulação estímulo e resposta"));
K.push(P("A etapa final integra as evidências para responder à pergunta central: quais medidas respondem a cada estímulo. A triangulação cruza o efeito agudo, o contraste entre tipos de dia, a variabilidade, a confiabilidade e a classificação de perfis, o que confere robustez às conclusões que sobrevivem a mais de um olhar."));

K.push(H2("4.1 Contraste direto entre HIIT e jogo amistoso"));
K.push(P("O contraste direto ordena as dimensões pela diferença padronizada entre a média no HIIT e a média no jogo, com pareamento por atleta. A Figura 9 e a Tabela 12 apresentam esse ordenamento e informam o valor de p nominal e o valor corrigido pela taxa de falsa descoberta."));
K.push(figCap("**Figura 9** – Contraste HIIT menos jogo (dz), pareado por atleta"));
K.push(figure("fig_contrast.png", 560));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 12** – Contraste HIIT versus jogo amistoso por dimensão do humor"));
{
  const rows = d.contrast.slice().sort((a, b) => b.dz - a.dz).map(r => [
    { t: r.lab, bold: true, al: AL.L },
    { t: n(r.hiit, 2), al: AL.C }, { t: n(r.jogo, 2), al: AL.C },
    { t: sgn(r.dz), al: AL.C, bold: true }, { t: r.mag, al: AL.C },
    { t: "p " + pf(r.p), al: AL.C }, { t: "q " + pf(r.fdr), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Dimensão", w: 1900, al: AL.L }, { t: "Média HIIT", w: 1350, al: AL.C }, { t: "Média jogo", w: 1350, al: AL.C },
    { t: "dz", w: 900, al: AL.C }, { t: "Magnitude", w: 1400, al: AL.C }, { t: "p", w: 1300, al: AL.C },
    { t: "q (FDR)", w: 1305, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: dz positivo indica escore maior no HIIT; q corrigido por Benjamini-Hochberg (oito testes). " + FONTE_D));
K.push(P("O padrão exibe coerência interna notável. As dimensões que mais separam os dois estímulos são todas afetivas, pois a raiva, a perturbação do humor, a depressão e a confusão ficam de meio desvio a acima no HIIT, com magnitude pequena a média. Em sentido oposto, o custo físico quase não distingue os dois contextos, o que revela carga interna semelhante entre correr o HIIT e disputar o jogo. Cabe uma ressalva metodológica importante: nenhuma diferença resiste isolada à correção por comparações múltiplas, razão pela qual o achado vale como conjunto convergente, e não como diferença individual confirmada. Ainda assim, a concordância de quatro dimensões afetivas na mesma direção confere credibilidade que um único teste positivo não alcançaria. A mensagem aplicada é direta: o jogo desgasta o corpo sem adoecer o humor, enquanto o HIIT cobra os dois preços."));

K.push(H2("4.2 Sonolência e estresse por tipo de dia e por perfil"));
K.push(P("A Tabela 13 compara a sonolência e o estresse entre os tipos de dia, com o contraste HIIT versus jogo pareado por atleta. A Tabela 14 e a Figura 10 deslocam o olhar para o perfil de humor e agrupam as observações em três blocos, a saber, favorável, neutro e de risco ou sobrecarga."));
K.push(tblTitle("**Tabela 13** – Sonolência e estresse por tipo de dia, com contraste HIIT × jogo"));
{
  const rows = d.wb_daytype.map(r => [
    { t: r.medida, bold: true, al: AL.L },
    { t: n(r.outro, 1), al: AL.C }, { t: n(r.hiit, 1), al: AL.C }, { t: n(r.jogo, 1), al: AL.C },
    { t: sgn(r.dz), al: AL.C, bold: true }, { t: "p " + pf(r.p) + (r.sig ? " *" : ""), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Medida", w: 2400, al: AL.L }, { t: "Outro", w: 1300, al: AL.C }, { t: "HIIT", w: 1300, al: AL.C },
    { t: "Jogo", w: 1300, al: AL.C }, { t: "dz (H×J)", w: 1400, al: AL.C }, { t: "p", w: 1805, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: o asterisco indica p < 0,05. " + FONTE_D));
K.push(tblTitle("**Tabela 14** – Sonolência e estresse por grupo de perfil de humor (Kruskal-Wallis)"));
{
  const rows = d.wb_profile.map(r => [
    { t: r.medida, bold: true, al: AL.L },
    { t: n(r.favoravel, 1), al: AL.C }, { t: n(r.neutro, 1), al: AL.C }, { t: n(r.risco, 1), al: AL.C },
    { t: n(r.H, 2), al: AL.C }, { t: "p " + pf(r.p) + (r.sig ? " *" : ""), al: AL.C }
  ]);
  K.push(openTable([
    { t: "Medida", w: 2400, al: AL.L }, { t: "Favorável", w: 1450, al: AL.C }, { t: "Neutro", w: 1300, al: AL.C },
    { t: "Risco", w: 1300, al: AL.C }, { t: "H", w: 1150, al: AL.C }, { t: "p", w: 1905, al: AL.C }
  ], rows));
}
K.push(tblSource("Nota: o asterisco indica p < 0,05. " + FONTE_D));
K.push(figCap("**Figura 10** – Sonolência e estresse por grupo de perfil de humor"));
K.push(figure("fig_sono_perfil.png", 520));
K.push(figSource(FONTE_E));
K.push(P("Dois desfechos robustos emergem. Em primeiro lugar, o estresse percebido recua no dia de jogo em relação ao HIIT, com significância estatística, o que reforça o caráter aversivo do estímulo intervalado já sugerido pelos contrastes afetivos. Em segundo lugar, a sonolência acompanha o perfil, pois se eleva do grupo favorável ao grupo de risco de maneira significativa, ao passo que o estresse não distingue os três grupos. Sono e humor, portanto, integram um mesmo bloco funcional, enquanto o estresse percebido segue dinâmica autônoma."));

K.push(H2("4.3 Síntese: os três eixos de resposta"));
K.push(P("O cruzamento de todos os métodos reduz a complexidade das oito variáveis a três eixos independentes de resposta ao estímulo, cada qual com função prática distinta. O primeiro eixo, do custo físico e da sonolência, reúne a fadiga física, a fadiga e a perturbação do humor, que sobem no efeito agudo, acumulam ao longo da semana e concentram o maior sinal com a melhor reprodutibilidade. Esse eixo responde à carga em si e serve para dosá-la. O segundo eixo, do afeto e da aversão, reúne a tensão, a depressão, a raiva e a confusão, que separam o HIIT do jogo e informam sobre o estado psicológico, ainda que a diferença não se confirme variável a variável. O terceiro eixo, do estresse percebido, mostra-se estável na semana, recua no dia de jogo e não segue os perfis, o que revela uma informação própria que os demais marcadores não capturam."));
K.push(P("A reflexão final que decorre desse quadro aponta para uma divisão de trabalho no monitoramento. A comissão técnica encontra na fadiga física o melhor termômetro da carga interna, pela sua estabilidade e reprodutibilidade, e no afeto e no perfil o melhor retrato do estado psicológico. A atenção redobra nos dias de HIIT do encerramento da semana, quando a sobrecarga física se acumula e o desconforto afetivo se acentua de modo simultâneo."));


// ====================== 5 SENSIBILIDADE: DOIS CAMINHOS ======================
K.push(H1("5 Análise de sensibilidade: dois caminhos (n = 19 e n = 27)"));
K.push(P("Dos 27 atletas, apenas 19 responderam nos sete dias. Como a análise de variância de medidas repetidas exige desenho balanceado, o resultado principal deste estudo repousa sobre esses 19 casos completos, sem qualquer imputação. Convém, porém, examinar a robustez dessa escolha, pois a decisão de aproveitar ou não os oito atletas com dias ausentes altera o poder estatístico. Esta seção confronta dois caminhos e acrescenta um terceiro como árbitro."));
K.push(P("O primeiro caminho mantém os 19 casos completos. O segundo recupera os 27 atletas e preenche cada dia ausente com a média do grupo naquele dia, procedimento simples porém consequente. O terceiro caminho, tomado como referência por não impor suposições artificiais, ajusta um modelo misto aos 27 atletas com os dados efetivamente observados, no qual o dia entra como efeito fixo e o atleta como efeito aleatório."));
K.push(figCap("**Figura 11** – Estatística F por variável nos caminhos n = 19 (sem imputação) e n = 27 (imputado). A estrela marca o efeito de dia significativo (ANOVA com correção de Greenhouse-Geisser)"));
K.push(figure("fig_twopath.png", 600));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 15** – Omnibus do efeito de dia pelos três caminhos"));
(function(){
  var O=d.twopath.omni, MX={}; d.twopath.mixed.forEach(function(x){MX[x.var]=x;});
  var chk=function(b){return b? "sim":"não";};
  var rows=O.map(function(o){var m=MX[o.var];return [
    {t:o.lab,bold:true,al:AL.L},
    {t:n(o.n19.F,1),al:AL.C},{t:n(o.n19.np2,2),al:AL.C},
    {t:n(o.n27.F,1),al:AL.C},{t:n(o.n27.np2,2),al:AL.C},
    {t:m.p==null?"–":("p "+pf(m.p)),al:AL.C},
    {t:(o.n19.sigA?"19":"·")+" · "+(o.n27.sigA?"27":"·")+" · "+(m.sig?"M":"·"),al:AL.C,bold:true}
  ];});
  K.push(openTable([
    {t:"Variável",w:2005,al:AL.L},
    {t:"F (n19)",w:1250,al:AL.C},{t:"η²ₚ (n19)",w:1250,al:AL.C},
    {t:"F (n27)",w:1250,al:AL.C},{t:"η²ₚ (n27)",w:1250,al:AL.C},
    {t:"p (misto)",w:1250,al:AL.C},{t:"Efeito de dia",w:1250,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: n19 = casos completos sem imputação; n27 = imputado pela média do dia; misto = modelo misto n = 27 sem imputação (efeito de dia por teste de Wald). Na última coluna, 19/27/M indicam em quais caminhos o efeito de dia é significativo. " + FONTE_D));
K.push(P("A leitura conjunta traz tranquilidade quanto ao essencial e cautela quanto ao detalhe. A direção e a hierarquia das variáveis permanecem idênticas nos três caminhos: a fadiga física lidera com folga e o vigor a acompanha. As duas vias omnibus, a paramétrica com correção de esfericidade e a de Friedman, concordam integralmente sobre quais variáveis têm efeito de dia. O que oscila é a contagem no limiar, de seis variáveis em n = 19 para sete em n = 27, e a magnitude do F."));
K.push(P("A explicação para essa oscilação é instrutiva. A imputação pela média do dia coloca o valor ausente exatamente sobre a média, o que encolhe de forma artificial a variância de erro e eleva o F sem elevar na mesma proporção o tamanho de efeito. Por isso o F da fadiga física salta de 13,0 em n = 19 para 20,9 em n = 27 imputado, ao passo que o η²ₚ mal se move, de 0,42 para 0,45. A perturbação total do humor ilustra a fronteira: fica aquém do limiar em n = 19 e o cruza em n = 27. Um ponto merece destaque: o modelo misto, que não imputa nada, também acusa a sétima variável como significativa, o que mostra que o ganho não é mero artefato da imputação, e sim reflexo do maior poder da amostra completa."));
K.push(P("A recomendação que decorre desta análise é dupla. Convém relatar o caminho de casos completos como resultado principal, por ser o mais conservador e livre de suposições, e apresentar o modelo misto como a via correta para aproveitar os 27 atletas quando o objetivo for maximizar o poder. A imputação pela média do dia, embora simples, deve ser evitada como base de inferência, justamente porque infla a estatística de teste. A transparência sobre o tamanho da amostra e o tratamento dos dias ausentes é, portanto, parte inseparável do relato."));


// ---------- 5.1 Padronização interna × externa (ilustrativa) ----------
K.push(H2("5.1 Padronização dos perfis: referência interna × externa (ilustrativa)"));
K.push(P("A classificação dos perfis de humor deste estudo padroniza cada subescala contra a média e o desvio padrão da própria amostra, ou seja, adota uma referência interna. Convém examinar o quanto essa escolha condiciona os rótulos, pois a alternativa seria padronizar contra uma referência externa, isto é, contra normas de uma população. A Tabela 16 apresenta, a título ilustrativo, o contraste entre a prevalência dos perfis obtida pela referência interna e por uma referência externa representativa das normas adultas do BRUMS. Convém frisar que os valores externos empregados são ilustrativos, não reproduzem verbatim nenhuma tabela publicada e servem apenas para evidenciar o efeito da escolha; para uma análise definitiva bastaria substituí-los pelas normas oficiais (Terry, Lane e Fogarty, 2003; ou as normas brasileiras de Rohlfs et al., 2008)."));
(function(){
  var IN=d.norm.interno, EX=d.norm.externo;
  var PORD=["Iceberg","Superfície","Submerso","Barbatana de tubarão","Everest invertido","Iceberg invertido"];
  var wk=function(D,p){var f=D.week.find(function(w){return w.perfil===p;});return f?f.prev:0;};
  var rows=PORD.map(function(p){return [{t:p,bold:true,al:AL.L},{t:n(wk(IN,p),1)+"%",al:AL.C},{t:n(wk(EX,p),1)+"%",al:AL.C}];});
  K.push(tblTitle("**Tabela 16** – Prevalência dos perfis de humor sob padronização interna e externa (ilustrativa)"));
  K.push(openTable([{t:"Perfil",w:4705,al:AL.L},{t:"Interno (amostra)",w:2400,al:AL.C},{t:"Externo (ilustrativo)",w:2400,al:AL.C}], rows));
  K.push(tblSource("Nota: interno = z contra a média/DP da amostra; externo = z contra referência ilustrativa de normas adultas do BRUMS. " + FONTE_D));
})();
K.push(P("O contraste é instrutivo. Sob a referência interna, a média da amostra corresponde ao ponto neutro, de modo que o elenco se distribui em torno dos perfis favoráveis, com predomínio de iceberg e superfície. Sob a referência externa, ancorada em uma população de vigor mais elevado, os escores absolutos desta equipe situam-se abaixo da referência e a maioria das respostas migra para o perfil submerso. A lição metodológica é direta: o rótulo do perfil é relativo à referência adotada e não deve ser lido como categoria absoluta."));
K.push(P("Um ponto tranquiliza quanto à leitura dinâmica do estudo. Embora a prevalência absoluta mude de forma expressiva entre as duas referências, a direção da migração ao longo da semana permanece a mesma nos dois modos, pois o perfil iceberg recua de D1 a D7 tanto na padronização interna quanto na externa. Assim, a interpretação central, a erosão do estado favorável conforme a carga se acumula, é robusta à escolha da referência, ainda que os rótulos absolutos dependam dela. Por essa razão, o estudo relata os perfis como descrição transversal do próprio elenco, e não como norma populacional."));


// ---------- 5.2 Confirmação por métodos convergentes ----------
K.push(H2("5.2 Confirmação da triangulação por métodos convergentes"));
K.push(P("A robustez de uma triangulação depende de os seus valores resistirem a mais de uma via de cálculo. Por isso, cada contraste e cada efeito agudo foi reavaliado por três caminhos independentes, a saber, o teste de Wilcoxon pareado, um teste de permutação por troca de sinais e o intervalo de confiança de 95% do tamanho de efeito obtido por reamostragem. A concordância entre as três vias serve de selo de confiança. O acordo foi elevado: 7 dos 8 contrastes e 23 dos 24 efeitos agudos apontaram no mesmo sentido pelas três abordagens."));
K.push(tblTitle("**Tabela 17** – Confirmação do contraste HIIT versus jogo por três vias independentes"));
(function(){
  var C=d.triconf.contrast.slice().sort(function(a,b){return b.dz-a.dz;});
  var rows=C.map(function(c){return [
    {t:c.lab,bold:true,al:AL.L},{t:sgn(c.dz),al:AL.C,bold:true},
    {t:"["+n(c.ic[0],2)+"; "+n(c.ic[1],2)+"]",al:AL.C},
    {t:"p "+pf(c.p_wilcoxon),al:AL.C,color:c.p_wilcoxon<.05?"1b7a3d":GREY},
    {t:"p "+pf(c.p_perm),al:AL.C,color:c.p_perm<.05?"1b7a3d":GREY},
    {t:c.concordam?"sim":"parcial",al:AL.C}
  ];});
  K.push(openTable([{t:"Variável",w:2005,al:AL.L},{t:"dz",w:1000,al:AL.C},{t:"IC 95% do dz",w:1900,al:AL.C},
    {t:"Wilcoxon",w:1500,al:AL.C},{t:"Permutação",w:1500,al:AL.C},{t:"Três vias",w:1600,al:AL.C}], rows));
})();
K.push(tblSource("Nota: dz positivo indica escore maior no HIIT; IC 95% por bootstrap; permutação por troca de sinais (sign-flip). " + FONTE_D));
K.push(P("As três dimensões afetivas que separam os estímulos, a raiva, a perturbação total do humor e a depressão, apresentaram intervalo de confiança do tamanho de efeito inteiramente acima de zero e permutação significativa, o que reforça o achado para além do teste original. A confusão ficou no limiar, com concordância apenas parcial entre as vias. Nenhum contraste sobrevive à correção por comparações múltiplas, resultado esperado com oito testes, de modo que o conjunto vale como padrão convergente e não como diferença individual confirmada. A associação entre sono e perfil recebeu igual reforço: além do teste de Kruskal-Wallis, uma prova de tendência de Kendall para grupos ordenados confirmou que o grupo de risco é o mais sonolento."));
K.push(P("Uma propriedade matemática esclarece o alcance da análise de padronização apresentada na Seção 5.1. Os tamanhos de efeito padronizados e o coeficiente intraclasse são invariantes à padronização linear por variável, pois subtrair uma média e dividir por um desvio padrão constante cancela no numerador e no denominador do dz. A verificação numérica confirmou a igualdade: raiva, perturbação do humor e depressão produzem o mesmo dz nos escores brutos e nos escores padronizados por referência externa, com diferença inferior a um milésimo de milésimo. Assim, apenas as partes que dependem do rótulo do perfil variam com a referência adotada, ao passo que o núcleo quantitativo da triangulação permanece o mesmo."));

// ---------- 5.3 Tabela das associações e relações significativas ----------
K.push(H2("5.3 Síntese das associações e relações significativas"));
K.push(P("A Tabela 18 reúne, em um único quadro, as associações e as relações que alcançaram significância estatística ao longo do estudo. A consolidação facilita a leitura de conjunto e evidencia que os achados relevantes se concentram em três frentes: o contraste afetivo entre estímulos, o acoplamento entre sono e humor e a coesão interna das dimensões negativas."));
(function(){
  var rows=[];
  var PR={depressao:"depressão",raiva:"raiva",fadiga:"fadiga",confusao:"confusão",vigor:"vigor",tensao:"tensão",pth:"PTH",epworth:"Epworth",pss:"PSS"};
  var pretty=function(p){return p.split(" × ").map(function(x){return PR[x.trim()]||x;}).join(" × ");};
  // contrastes HIIT×jogo confirmados
  d.triconf.contrast.forEach(function(c){ if(c.p_wilcoxon<.05){ rows.push([
    {t:c.lab+" (HIIT × jogo)",al:AL.L},{t:"contraste",al:AL.C},{t:"dz "+sgn(c.dz),al:AL.C,bold:true},
    {t:"IC ["+n(c.ic[0],2)+"; "+n(c.ic[1],2)+"]",al:AL.C},{t:"Wilcoxon+perm.+IC",al:AL.C}]); }});
  // PSS por tipo de dia
  var pss=d.wb_daytype.find(function(w){return w.medida==="PSS";});
  if(pss && pss.sig) rows.push([{t:"Estresse (PSS): jogo < HIIT",al:AL.L},{t:"contraste",al:AL.C},
    {t:"dz "+sgn(pss.dz),al:AL.C,bold:true},{t:"p "+pf(pss.p),al:AL.C},{t:"Wilcoxon pareado",al:AL.C}]);
  // sono × perfil (Epworth) — interno
  var e=d.triconf.prof_int.epworth;
  rows.push([{t:"Sonolência (Epworth) × grupo de perfil",al:AL.L},{t:"tendência",al:AL.C},
    {t:"τ "+sgn(e.kendall_tau),al:AL.C,bold:true},{t:"p "+pf(e.kendall_p)+" · Kruskal "+pf(e.kruskal_p),al:AL.C},{t:"Kendall + Kruskal",al:AL.C}]);
  // correlações humor × humor significativas
  d.spearman.forEach(function(sp){ if(sp.p<.05) rows.push([
    {t:pretty(sp.par),al:AL.L},{t:"correlação",al:AL.C},{t:"ρ "+sgn(sp.rho),al:AL.C,bold:true},
    {t:"p "+pf(sp.p),al:AL.C},{t:"Spearman (atleta)",al:AL.C}]); });
  // sono/estresse × humor significativas
  d.wcorr.forEach(function(wc){ if(wc.p<.05) rows.push([
    {t:pretty(wc.par),al:AL.L},{t:"correlação",al:AL.C},{t:"ρ "+sgn(wc.rho),al:AL.C,bold:true},
    {t:"p "+pf(wc.p),al:AL.C},{t:"Spearman (atleta)",al:AL.C}]); });
  K.push(tblTitle("**Tabela 18** – Associações e relações estatisticamente significativas do estudo"));
  K.push(openTable([{t:"Relação",w:3205,al:AL.L},{t:"Tipo",w:1300,al:AL.C},{t:"Estimativa",w:1300,al:AL.C},
    {t:"IC / p",w:2400,al:AL.C},{t:"Método",w:1300,al:AL.C}], rows));
})();
K.push(tblSource("Nota: dz = tamanho de efeito para medidas repetidas; ρ = correlação de Spearman no nível do atleta; τ = tau de Kendall para tendência entre grupos ordenados. Apenas relações com p < 0,05. " + FONTE_D));
K.push(P("O quadro consolidado confirma a leitura central do estudo. O afeto negativo, com destaque para a raiva, a depressão e a perturbação total do humor, é o que distingue o HIIT do jogo. O estresse percebido recua no dia de jogo. A sonolência acompanha o perfil de humor, com o grupo de risco mais sonolento. E as dimensões negativas correlacionam-se entre si de forma consistente, o que sustenta o uso da perturbação total do humor como resumo do afeto. Nenhuma dessas relações isoladas sobrevive de modo automático à correção por múltiplas comparações, porém a convergência entre métodos e entre pares confere ao conjunto uma credibilidade que um teste solitário não alcançaria."));

// ====================== 6 MODELOS COMPLEMENTARES E ANÁLISE SEGMENTADA ======================
K.push(H1("6 Modelos complementares e análise segmentada"));
K.push(P("As seções anteriores estabeleceram a descrição, a triangulação e a robustez do achado central. Esta parte acrescenta cinco camadas de modelagem que refinam a leitura sem contradizê-la. A primeira examina se o efeito agudo depende do tipo de dia por meio de um modelo fatorial. A segunda descreve a dinâmica de um dia para o seguinte com um modelo autorregressivo de painel e com um modelo linear generalizado. A terceira audita a estrutura real das sessões de treino e normaliza a carga. A quarta repete a bateria dentro de cada estrato de estímulo. A quinta ajusta o humor pelo pico de velocidade e reúne as regressões. Todas as análises respeitam o mesmo desenho de grupo único, de modo que as leituras permanecem descritivas e de rastreio."));

// ---------- 6.1 Fatorial ----------
K.push(H2("6.1 Análise fatorial: momento e tipo de dia"));
K.push(P("Um modelo fatorial de dois fatores intra-sujeito pergunta se o efeito agudo do treino, medido do pré para o pós, depende do tipo de dia. O primeiro fator é o momento, com dois níveis, e o segundo é o tipo de dia, com três níveis, a saber, HIIT, jogo e força. Cabe uma ressalva de desenho: como o estudo é observacional, esta é uma análise fatorial de fatores observados, e não um experimento com alocação aleatória, razão pela qual o tipo de dia guarda confundimento com o dia e com a carga acumulada. A Figura 12 ilustra a interação para a perturbação total do humor, e a Tabela 19 resume os efeitos por dimensão."));
K.push(figCap("**Figura 12** – Interação Momento × Tipo de dia na perturbação total do humor. As linhas não paralelas sinalizam interação"));
K.push(figure("fig_fatorial.png", 520));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 19** – Análise fatorial Momento × Tipo de dia: tamanho de efeito (η²ₚ) por dimensão"));
(function(){
  var rm=d.fac.rm, MX={}; d.fac.mixed.forEach(function(x){MX[x.dim]=x;});
  var get=function(dim,fac){var r=rm.find(function(x){return x.dim===dim&&x.fator===fac;});return r||{};};
  var dims=d.fac.dims;
  var rows=dims.map(function(dm){
    var mo=get(dm.dim,"Momento (pré/pós)"),tp=get(dm.dim,"Tipo de dia"),it=get(dm.dim,"Momento × Tipo de dia"),mx=MX[dm.dim]||{};
    return [
      {t:dm.lab,bold:true,al:AL.L},
      {t:n(mo.eta2p,2)+(mo.sig?" *":""),al:AL.C,color:mo.sig?"1b7a3d":INK},
      {t:n(tp.eta2p,2)+(tp.sig?" *":""),al:AL.C,color:tp.sig?"1b7a3d":INK},
      {t:n(it.eta2p,2)+(it.sig?" *":""),al:AL.C,bold:it.sig,color:it.sig?"1b7a3d":INK},
      {t:(mx.p_interacao==null?"–":("p "+pf(mx.p_interacao)))+(mx.sig_interacao?" *":""),al:AL.C}
    ];
  });
  K.push(openTable([
    {t:"Dimensão",w:2505,al:AL.L},{t:"Momento",w:1750,al:AL.C},{t:"Tipo de dia",w:1750,al:AL.C},
    {t:"Interação",w:1750,al:AL.C},{t:"Misto p(int.)",w:1750,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: η²ₚ = eta quadrado parcial (rm-ANOVA, casos completos, n = " + d.fac.n_complete + "); p por correção de Greenhouse-Geisser; * indica p < 0,05. Última coluna: interação no modelo misto com os 27 atletas. " + FONTE_D));
K.push(P("O resultado desenha uma divisão nítida. O momento produz efeito forte e uniforme sobre o eixo físico, pois a fadiga física, a fadiga, o vigor e a perturbação total do humor pioram do pré para o pós de maneira semelhante em qualquer tipo de dia. Já a interação entre momento e tipo de dia concentra-se no eixo afetivo, uma vez que a depressão, a raiva e a perturbação do humor respondem de modo específico ao estímulo, com significância confirmada tanto na análise de casos completos quanto no modelo misto dos 27 atletas. Em síntese, o corpo paga um preço parecido em qualquer sessão, ao passo que o afeto reage conforme o tipo de dia, exatamente a leitura da triangulação, agora sob um único modelo."));

// ---------- 6.2 AR1 + GLM ----------
K.push(H2("6.2 Dinâmica de painel: persistência e razão de taxas"));
K.push(P("Dois modelos descrevem a dinâmica do estado ao longo dos dias. O primeiro é um autorregressivo de painel de defasagem um, com intercepto aleatório por atleta, cujo coeficiente mede a persistência, isto é, a fração do estado de um dia que se transfere para o dia seguinte. Convém registrar que, em painéis com poucas medidas no tempo, esse coeficiente tende a ser subestimado, razão pela qual a leitura vale pela ordem de grandeza. O segundo é um modelo linear generalizado de Poisson, ajustado por equações de estimação generalizadas com erros robustos por atleta, que trata as subescalas como contagens e informa a razão de taxas por tipo de dia e por momento. A Tabela 20 apresenta a persistência e a Tabela 21 as razões de taxas significativas."));
K.push(tblTitle("**Tabela 20** – Persistência de um dia para o seguinte (autorregressivo de painel, defasagem um)"));
(function(){
  var rows=d.dyn.ar1.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},{t:sgn(r.beta1),al:AL.C,bold:true},
    {t:"["+n(r.ic_lo,2)+"; "+n(r.ic_hi,2)+"]",al:AL.C},
    {t:"p "+pf(r.p),al:AL.C,color:r.sig?"1b7a3d":GREY},
    {t:r.icc==null?"–":n(r.icc,2),al:AL.C},{t:r.forca,al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2205,al:AL.L},{t:"β₁",w:1300,al:AL.C},{t:"IC 95%",w:2000,al:AL.C},
    {t:"p",w:1400,al:AL.C},{t:"ICC",w:1300,al:AL.C},{t:"Persistência",w:1300,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: β₁ = coeficiente de defasagem um; ICC = correlação intraclasse do intercepto aleatório. " + FONTE_D));
K.push(tblTitle("**Tabela 21** – Razão de taxas (IRR) do modelo linear generalizado de Poisson (efeitos significativos)"));
(function(){
  var rows=d.dyn.glm.filter(function(g){return g.sig;}).map(function(g){return [
    {t:g.dim_lab,bold:true,al:AL.L},{t:g.preditor,al:AL.L},
    {t:n(g.irr,2),al:AL.C,bold:true},{t:"["+n(g.ic_lo,2)+"; "+n(g.ic_hi,2)+"]",al:AL.C},
    {t:"p "+pf(g.p),al:AL.C,color:"1b7a3d"}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2005,al:AL.L},{t:"Preditor",w:2400,al:AL.L},{t:"IRR",w:1200,al:AL.C},
    {t:"IC 95%",w:2400,al:AL.C},{t:"p",w:1500,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: IRR = razão de taxas (referência: dia de jogo e momento pré); IRR acima de um indica taxa maior que a referência; erros-padrão robustos por atleta. " + FONTE_D));
K.push(P("Os dois modelos reforçam a estrutura de dois eixos. A persistência mais alta cabe à fadiga e à perturbação total do humor, o que traduz o acúmulo do cansaço de um dia para o outro e concorda com o efeito crônico já descrito. O vigor e as dimensões negativas reiniciam mais entre os dias, com persistência baixa. O modelo generalizado, por sua vez, mostra que o eixo afetivo responde de forma específica ao estímulo, pois o HIIT eleva a depressão, a raiva e a confusão em relação ao jogo, ao passo que o momento pós rebaixa o vigor e eleva a fadiga. Contagem, persistência e interação convergem para a mesma conclusão."));

// ---------- 6.3 Cargas segmentadas + dose ----------
K.push(H2("6.3 Segmentação das sessões e resposta à dose de carga"));
K.push(P("A auditoria da estrutura de treino corrigiu um ponto importante. O rótulo único por dia, tal como HIIT, jogo ou força, nomeia apenas a sessão definidora e colapsa os dias que reuniram mais de uma sessão em períodos diferentes. A Tabela 22 recompõe a estrutura real, confirmada na fonte, e informa a duração, a carga acumulada e a carga interna planejada por dia. A carga interna planejada seguiu o método da percepção de esforço da sessão, com o valor do HIIT ancorado no esforço percebido de fato medido e os demais tipos estimados por valores nominais ajustáveis, uma vez que o esforço percebido por sessão não foi coletado nas sessões técnicas, de força e de jogo."));
K.push(tblTitle("**Tabela 22** – Estrutura segmentada do microciclo e carga por dia"));
(function(){
  var rows=d.load.carga_raw.map(function(c){return [
    {t:"D"+c.dia,bold:true,al:AL.C},{t:c.data,al:AL.C},{t:String(c.n_sessoes),al:AL.C},
    {t:c.conteudo,al:AL.L},{t:n(c.horas,1)+" h",al:AL.C},{t:n(c.carga_acum_h,1)+" h",al:AL.C},
    {t:String(Math.round(c.srpe)),al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dia",w:705,al:AL.C},{t:"Data",w:1100,al:AL.C},{t:"Sessões",w:900,al:AL.C},
    {t:"Composição real",w:3400,al:AL.L},{t:"Horas",w:1000,al:AL.C},{t:"Acum.",w:1100,al:AL.C},{t:"sRPE",w:1300,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: composição confirmada na fonte; sRPE = carga interna planejada em unidades arbitrárias (duração × esforço percebido nominal); monotonia de Foster = " + n(d.load.monotonia,2) + "; strain = " + Math.round(d.load.strain) + ". " + FONTE_D));
K.push(P("Sobre essa base contínua, um modelo dose-resposta substitui o rótulo categórico por duas cargas interpretáveis, a saber, a carga aguda do próprio dia e a carga acumulada na semana, com intercepto aleatório por atleta. A Figura 13 e a Tabela 23 apresentam os coeficientes padronizados."));
K.push(figCap("**Figura 13** – Efeito da carga cumulativa sobre cada dimensão (coeficiente padronizado)"));
K.push(figure("fig_dose.png", 520));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 23** – Modelo dose-resposta: carga aguda e carga cumulativa por dimensão"));
(function(){
  var rows=d.dose.dose.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},
    {t:sgn(r.beta_agudo)+(r.sig_agudo?" *":""),al:AL.C,color:r.sig_agudo?"1b7a3d":INK},
    {t:sgn(r.beta_cum)+(r.sig_cum?" *":""),al:AL.C,bold:r.sig_cum,color:r.sig_cum?"1b7a3d":INK},
    {t:r.domina,al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2905,al:AL.L},{t:"β carga aguda",w:2200,al:AL.C},
    {t:"β carga cumulativa",w:2200,al:AL.C},{t:"Domina",w:2200,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: β = coeficiente padronizado por desvio padrão de carga; * indica p < 0,05. Validação: a qualidade total de recuperação cai quando a carga acumulada sobe (ρ de Spearman = " + n(d.dose.valid.rho_acum_tqr,2) + "). A razão aguda para crônica não foi calculada, pois a janela crônica de vinte e oito dias não cabe em sete dias. " + FONTE_D));
K.push(P("A leitura dose-resposta esclarece o mecanismo. O eixo físico e energético é governado pela carga cumulativa, pois o vigor cai e a fadiga e a perturbação do humor sobem à medida que a carga se acumula na semana, comportamento coerente com a persistência do modelo autorregressivo. O afeto, em contraste, responde mais ao componente agudo do dia. O ganho da segmentação está justamente nessa separação: em vez de tratar o dia como um rótulo, o modelo passa a ler o volume do dia e o acúmulo, o que distingue a carga aguda do custo crônico."));

// ---------- 6.4 Estratos ----------
K.push(H2("6.4 Análise estratificada: dias de HIIT e dias sem HIIT"));
K.push(P("A repetição da bateria dentro de cada estrato separa o que é próprio do HIIT do que é geral ao microciclo. O primeiro estrato reúne os três dias de HIIT e o segundo os quatro dias sem HIIT, e em cada um se compara o primeiro ao último dia com a mesma triangulação de três vias. A Figura 14 confronta os tamanhos de efeito e a Tabela 24 detalha a concordância entre as vias."));
K.push(figCap("**Figura 14** – Tamanho de efeito do primeiro ao último dia, por estrato de estímulo"));
K.push(figure("fig_estratos.png", 560));
K.push(figSource(FONTE_E));
K.push(tblTitle("**Tabela 24** – Contraste primeiro para último dia por estrato, com triangulação de três vias"));
(function(){
  var tri=d.strata.tri, dims=d.strata.dims;
  var order=[]; dims.forEach(function(dm){ ["HIIT","SemHIIT"].forEach(function(es){ var r=tri.find(function(x){return x.dim===dm.dim&&x.estrato===es;}); if(r) order.push(r); }); });
  var rows=order.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},{t:r.estrato==="HIIT"?"HIIT":"sem HIIT",al:AL.C},
    {t:sgn(r.dz),al:AL.C,bold:true},{t:"["+n(r.ic[0],2)+"; "+n(r.ic[1],2)+"]",al:AL.C},
    {t:r.p_wilcoxon==null?"–":("p "+pf(r.p_wilcoxon)),al:AL.C},{t:"p "+pf(r.p_perm),al:AL.C},
    {t:r.concordam?"sim":"·",al:AL.C,bold:true,color:r.concordam?"1b7a3d":GREY}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:1905,al:AL.L},{t:"Estrato",w:1200,al:AL.C},{t:"dz",w:1000,al:AL.C},
    {t:"IC 95%",w:1800,al:AL.C},{t:"Wilcoxon",w:1300,al:AL.C},{t:"Permut.",w:1300,al:AL.C},{t:"3 vias",w:1000,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: dz positivo indica escore maior no último dia do estrato; IC 95% por bootstrap; três vias = concordância entre IC, Wilcoxon e permutação. " + FONTE_D));
K.push(P("A comparação revela o que muda ao isolar os estratos. O vigor cai nos dois grupos de dias, com confirmação das três vias, o que torna a queda de energia inespecífica ao estímulo. Já a subida da fadiga triangula apenas nos dias de HIIT, ao passo que nos dias sem HIIT permanece como tendência, o que reforça o HIIT como motor do eixo energia e fadiga. O afeto negativo não se altera do primeiro ao último dia dentro de nenhum estrato, coerente com a leitura de que o afeto separa tipos de dia, e não o curso ao longo deles. Quanto ao perfil dominante, os dias de HIIT concentram o perfil de superfície e os dias sem HIIT concentram o perfil iceberg."));

// ---------- 6.5 PV log + regressões ----------
K.push(H2("6.5 Ajuste pelo pico de velocidade e regressões"));
K.push(P("A última camada relaciona a aptidão aeróbia ao humor e reúne as regressões. O ajuste do humor pelo pico de velocidade do T-CAR foi conduzido em duas formas, a linear e a logarítmica, para verificar se a relação apresenta curvatura. A Tabela 25 confronta as duas. A regressão logística de duas caudas, por sua vez, testa quais marcadores discriminam o perfil de risco, e a Tabela 26 apresenta as razões de chance."));
K.push(tblTitle("**Tabela 25** – Ajuste do humor pelo pico de velocidade: linear versus logarítmico"));
(function(){
  var rows=d.strata.pv_log.map(function(r){return [
    {t:r.dim_lab,bold:true,al:AL.L},{t:sgn(r.spearman),al:AL.C,bold:true},
    {t:n(r.r2_lin,2),al:AL.C},{t:n(r.r2_log,2),al:AL.C},{t:r.melhor,al:AL.C}
  ];});
  K.push(openTable([
    {t:"Dimensão",w:2505,al:AL.L},{t:"ρ (PV)",w:1600,al:AL.C},{t:"R² linear",w:1800,al:AL.C},
    {t:"R² log",w:1800,al:AL.C},{t:"Melhor",w:1800,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: ρ = correlação de Spearman entre pico de velocidade e humor (pares casados, n = 25); melhor = ajuste com menor critério de informação de Akaike. " + FONTE_D));
K.push(tblTitle("**Tabela 26** – Regressão logística de duas caudas: risco de perfil por marcador"));
(function(){
  var rows=d.strata.logit.map(function(r){return [
    {t:r.preditor,bold:true,al:AL.L},{t:n(r.OR,2),al:AL.C,bold:true},
    {t:"["+n(r.ic_lo,2)+"; "+n(r.ic_hi,2)+"]",al:AL.C},
    {t:"p "+pf(r.p),al:AL.C,color:r.sig?"1b7a3d":GREY}
  ];});
  K.push(openTable([
    {t:"Marcador",w:2905,al:AL.L},{t:"Razão de chance",w:1800,al:AL.C},
    {t:"IC 95%",w:2800,al:AL.C},{t:"p (bicaudal)",w:2000,al:AL.C}
  ], rows));
})();
K.push(tblSource("Nota: razão de chance por desvio padrão do marcador; p de duas caudas; modelo com Epworth, PSS e fadiga padronizados. " + FONTE_D));
K.push(P("Os dois procedimentos fecham o quadro com coerência. O ajuste pelo pico de velocidade mostra-se essencialmente linear, uma vez que a forma logarítmica não melhora a explicação em nenhuma dimensão, e a relação mais forte confirma-se na fadiga física, que decresce de modo linear conforme a aptidão aeróbia aumenta. A regressão logística, por seu turno, aponta a fadiga como o marcador que discrimina o perfil de risco, ao passo que a sonolência e o estresse percebido não distinguem os grupos. O conjunto reitera a mensagem que atravessa todo o estudo: o sinal reside no eixo da energia e da fadiga, tanto para dosar a carga quanto para sinalizar o risco."));


// ====================== 6 CONSIDERAÇÕES ======================
K.push(H1("7 Considerações finais"));
K.push(P("O estudo descreveu, com riqueza de detalhes, o comportamento do humor, da sonolência e do estresse ao longo de um microciclo de pré-temporada e identificou quais medidas respondem a cada estímulo. A triangulação metodológica revelou-se fértil, pois permitiu distinguir os achados robustos das meras tendências e organizar as evidências em três eixos de leitura direta para a prática esportiva."));
K.push(P("Três cautelas delimitam o alcance das conclusões. Em primeiro lugar, o delineamento de grupo único, sem controle, confere às leituras caráter descritivo e de rastreio, e não causal. Em segundo lugar, o pequeno número de contrastes que sobrevivem à correção por comparações múltiplas recomenda prudência, de modo que os padrões afetivos valem como tendência convergente. Em terceiro lugar, a associação entre perfis de risco e desfechos clínicos de lesão ou de saúde mental permanece plausível à luz da literatura, embora não tenha sido validada neste microciclo, que não dispõe de desfechos vinculados."));
K.push(P("Longe de fragilizar o trabalho, essas ressalvas delimitam com honestidade o que a evidência sustenta. O estudo demonstra a viabilidade de um rastreio sensível e reprodutível, capaz de apontar quais variáveis respondem a cada estímulo, quando o risco se concentra e quais atletas merecem acompanhamento individual. O passo seguinte consiste em um estudo prospectivo, com registro sistemático de lesões e de indicadores de saúde mental, que converta a viabilidade demonstrada em validação de maior alcance."));

// ====================== REFERÊNCIAS ======================
K.push(H1("Referências"));
const REFS = [
  "HAN, C.; PARSONS-SMITH, R. L.; TERRY, P. C. Mood profiling in Singapore: cross-cultural validation and potential applications of mood profile clusters. Frontiers in Psychology, v. 11, art. 665, 2020.",
  "MORGAN, W. P. Selected psychological factors limiting performance: a mental health model. In: CLARKE, D. H.; ECKERT, H. M. (Ed.). Limits of human performance. Champaign: Human Kinetics, 1985. p. 70-80.",
  "PARSONS-SMITH, R. L.; TERRY, P. C.; MACHIN, M. A. Identification and description of novel mood profile clusters. Frontiers in Psychology, v. 8, art. 1958, 2017.",
  "ROHLFS, I. C. P. M. et al. A Escala de Humor de Brunel (Brums): instrumento para detecção precoce da síndrome do excesso de treinamento. Revista Brasileira de Medicina do Esporte, v. 14, n. 3, p. 176-181, 2008.",
  "TERRY, P. C.; LANE, A. M.; FOGARTY, G. J. Construct validity of the Profile of Mood States-Adolescents for use with adults. Psychology of Sport and Exercise, v. 4, n. 2, p. 125-139, 2003."
];
REFS.forEach(r => K.push(new Paragraph({
  children: rich(r, { size: BODY }), alignment: AlignmentType.LEFT,
  spacing: { before: 0, after: 120, line: LINE15, lineRule: "auto" }
})));

// nota final
K.push(new Paragraph({ spacing: { before: 200, after: 60 }, border: { top: { style: BorderStyle.SINGLE, size: 4, color: "999999" } }, children: [] }));
K.push(Pflat("Nota técnica: todos os números derivam da camada gold de um repositório reprodutível (Delta Lake e DuckDB), com sementes fixas e verificação de determinismo, idempotência e reconciliação. As mesmas tabelas alimentam este documento e a aba de triangulação do painel interativo.", { size: SMALL, color: GREY }));

// ====================== MONTAGEM ======================
const doc = new Document({
  creator: "Monitoramento BRUMS — Handebol",
  title: "Análise descritiva e triangulação (BRUMS)",
  styles: { default: { document: { run: { font: FONT, size: BODY, color: INK } } } },
  numbering: { config: [] },
  sections: [{
    properties: { page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1701, right: 1134, bottom: 1134, left: 1701 }
    } },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: SMALL, color: GREY })]
    })] }) },
    children: K
  }]
});
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(DIR + "/Analise_Descritiva_Triangulacao_ABNT.docx", buf);
  console.log("OK ->", buf.length, "bytes");
});
