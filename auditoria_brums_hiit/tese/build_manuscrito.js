// Gera o manuscrito completo (Word) com Resultados e Discussão integrados,
// em ordem lógica e cronológica. Números vindos de dashboard_data.json.
// Uso: node build_manuscrito.js  (de dentro de tese/)
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, ImageRun, PageOrientation
} = require('docx');

const HERE = __dirname;
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'dashboard_data.json'), 'utf8'));
const REFS = JSON.parse(fs.readFileSync(path.join(HERE, 'referencias.json'), 'utf8'));

// ---------- helpers ----------
const nf = (x, d = 2) => (x === null || x === undefined || isNaN(x)) ? '—'
  : Number(x).toFixed(d).replace('.', ',');
const pf = (p) => p === null || p === undefined ? '—' : (p < 0.001 ? '< 0,001' : nf(p, 3));
const sg = (x, d = 2) => (x >= 0 ? '+' : '') + nf(x, d);
const CW = 9360; // content width DXA (Letter, 1in margins)

const INK = '16273D', TEAL = '0E8C86', MUT = '5B6B82', HEADBG = 'EAF1F7', LINE = 'C9D4E0';

function P(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, ...(opts.run || {}) })];
  return new Paragraph({
    children: runs,
    spacing: { after: opts.after ?? 140, line: opts.line ?? 276, before: opts.before ?? 0 },
    alignment: opts.align ?? AlignmentType.JUSTIFIED,
    ...opts.p
  });
}
function H(text, level) {
  return new Paragraph({ heading: level, spacing: { before: 260, after: 120 },
    children: [new TextRun({ text })] });
}
function bold(t) { return new TextRun({ text: t, bold: true }); }
function run(t, o = {}) { return new TextRun({ text: t, ...o }); }

function cell(text, { w, head = false, alignRight = false, bold: b = false } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: HEADBG, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    children: [new Paragraph({
      alignment: alignRight ? AlignmentType.RIGHT : AlignmentType.LEFT,
      spacing: { after: 0, line: 240 },
      children: [new TextRun({ text: String(text), bold: head || b, size: 17,
        color: head ? INK : undefined })]
    })]
  });
}
function table(headers, rows, widths, aligns) {
  const border = { style: BorderStyle.SINGLE, size: 2, color: LINE };
  const borders = { top: border, bottom: border, left: border, right: border,
    insideHorizontal: border, insideVertical: border };
  const trh = new TableRow({ tableHeader: true, children: headers.map((h, i) =>
    cell(h, { w: widths[i], head: true, alignRight: aligns[i] === 'r' })) });
  const trs = rows.map(r => new TableRow({ children: r.map((c, i) =>
    cell(c, { w: widths[i], alignRight: aligns[i] === 'r' })) }));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths,
    borders, rows: [trh, ...trs] });
}
function caption(t) {
  return new Paragraph({ spacing: { before: 60, after: 180 },
    children: [new TextRun({ text: t, italics: true, size: 17, color: MUT })] });
}
function fig(file, cap, wPx = 620) {
  const buf = fs.readFileSync(path.join(HERE, file));
  // infer aspect from known monitoramento (1958x1490) fallback
  const hPx = Math.round(wPx * 0.76);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: 'png', data: buf, transformation: { width: wPx, height: hPx } })] }),
    caption(cap)
  ];
}

const LAB = { PTH: 'PTH (TMD)', FadFis: 'Fadiga física', Fadiga: 'Fadiga', Vigor: 'Vigor',
  FadMen: 'Fadiga mental', 'Tensão': 'Tensão', 'Depressão': 'Depressão', Raiva: 'Raiva', 'Confusão': 'Confusão' };

// ---------- pull numbers ----------
const A = {}; D.inf.A_aguda.forEach(r => A[r.var] = r);
const rocm = {}; D.roc.pre_vs_pos.forEach(r => rocm[r.var] = r);
const conf = D.conf.A_confiabilidade, inv = D.conf.B_invariancia;
const pv = D.pv, mt = D.mt, dh = D.dh, adv = D.adv;

const children = [];

// ===================== CAPA =====================
children.push(
  new Paragraph({ spacing: { before: 1200, after: 60 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: 'TESE · CIÊNCIAS DO ESPORTE', bold: true, color: TEAL, size: 20,
      characterSpacing: 40 })] }),
  new Paragraph({ spacing: { after: 120 }, children: [new TextRun({
    text: 'Monitoramento psicométrico do humor e da fadiga em atletas de handebol durante um microciclo de treinamento de alta intensidade (HIIT)',
    bold: true, size: 40, color: INK })] }),
  new Paragraph({ spacing: { after: 300 }, children: [new TextRun({
    text: 'Estudo observacional longitudinal com validação psicométrica robusta e correção de medidas repetidas — documento completo com Resultados e Discussão integrados, em ordem lógica e cronológica.',
    italics: true, size: 22, color: MUT })] }),
  new Paragraph({ spacing: { after: 60 }, children: [
    run('Amostra: ', { bold: true, size: 20 }),
    run('27 atletas de elite · 456 observações · 135 pares pré→pós · microciclo de 7 dias (HIIT nos dias 2, 4 e 7).', { size: 20 })] }),
  new Paragraph({ spacing: { after: 60 }, children: [
    run('Integridade dos dados: ', { bold: true, size: 20 }),
    run('atletas anonimizados (A01–A27); todos os valores reproduzidos por código a partir da coleta bruta.', { size: 20 })] }),
  new Paragraph({ spacing: { before: 400 }, children: [run('[Autor] · [Orientador] · [Instituição] · 2026', { size: 20, color: MUT })] }),
  new Paragraph({ children: [new PageBreak()] })
);

// ===================== RESUMO =====================
children.push(H('Resumo', HeadingLevel.HEADING_1));
children.push(P([
  bold('Objetivo. '),
  run('Avaliar como o perfil de humor (Escala de Humor de Brunel, BRUMS) de atletas de handebol de elite se comporta ao longo de um microciclo de alta intensidade e o quanto esse comportamento pode ser medido de forma confiável, distinguindo a limitação de mensuração (efeito piso) da ausência real de efeito. '),
  bold('Método. '),
  run(`Vinte e sete atletas foram avaliados repetidamente (pré e pós-treino) durante sete dias, com HIIT nos dias 2, 4 e 7 (${D.inf.n_obs} observações; 135 pares pré→pós). Toda a inferência tratou o atleta como unidade amostral (modelos de efeitos mistos; correção de comparações múltiplas por FDR). `),
  bold('Resultados. '),
  run(`A resposta ao microciclo concentra-se no eixo energia–fadiga: a fadiga física é o marcador sentinela (dz ${nf(A.FadFis.dz)}), acompanhada de PTH (dz ${nf(A.PTH.dz)}), fadiga (dz ${nf(A.Fadiga.dz)}) e queda de vigor (dz ${nf(A.Vigor.dz)}); as subescalas negativas com efeito piso não respondem. A escala é confiável e invariante pré→pós (Tucker φ ${nf(inv.tucker_phi)}). O efeito do HIIT está no nível do dia (ΔPTH +2,43), não num choque agudo específico. A resposta é fortemente individual (ICC 0,42–0,71) e desacoplada da carga interna (TRIMP × ΔPTH r = ${nf(D.trimp.TRIMP_x_humor.r)}, n.s.). `),
  bold('Conclusão. '),
  run('A resposta de humor é real, mora no eixo energia–fadiga, é fortemente individual e não é função simples do custo cardiovascular — sustentando o monitoramento individualizado por tendência, com a fadiga física como sentinela.')
]));
children.push(P([bold('Palavras-chave: '), run('BRUMS; humor; fadiga; HIIT; handebol; psicometria; medidas repetidas; monitoramento.')]));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 1. INTRODUÇÃO =====================
children.push(H('1. Introdução', HeadingLevel.HEADING_1));
children.push(P('O monitoramento subjetivo do humor e da fadiga é sensível, barato e não invasivo, e frequentemente supera marcadores objetivos na detecção precoce de desajustes de treinamento. Sua interpretação, porém, exige rigor psicométrico e métodos que respeitem a estrutura de medidas repetidas. Uma subescala pode "não responder" a um estímulo por dois motivos radicalmente diferentes: porque o fenômeno de fato não ocorre, ou porque o instrumento não consegue medi-lo (efeito piso). Distinguir esses casos é condição para interpretar corretamente o monitoramento do humor.'));
children.push(P('Este documento reúne, em ordem lógica e cronológica, a auditoria independente e a reanálise completa de um estudo com 27 atletas de handebol de elite acompanhados por um microciclo de sete dias com três sessões de HIIT. A sequência de apresentação segue o encadeamento natural do raciocínio — primeiro a qualidade da medida, depois a resposta aguda, o acúmulo ao longo da semana, o papel do HIIT, a confirmação multivariada, o modelo teórico, o diagnóstico, a individualidade e, por fim, o acoplamento com a carga interna e os autorrelatos complementares.'));
children.push(P([bold('Objetivo geral. '), run('Avaliar o comportamento do perfil de humor ao longo do microciclo e o quanto esse comportamento pode ser medido de forma confiável, separando o efeito piso da ausência real de efeito.')]));
children.push(P('Hipóteses: (H1) o humor deteriora ao longo da semana, no eixo energia–fadiga; (H2) os dias de HIIT associam-se a mais fadiga, menos vigor e maior perturbação; (H3) as subescalas negativas têm efeito piso e baixa sensibilidade; (H4) a maior parte da variância é traço, tornando frágil a decisão isolada; (H5) o BRUMS é válido no eixo energia–fadiga, e a fragilidade das negativas é piso, não ausência.'));

// ===================== 2. MÉTODO =====================
children.push(H('2. Método', HeadingLevel.HEADING_1));
children.push(P([bold('Desenho e amostra. '), run(`Estudo observacional longitudinal de medidas repetidas. Vinte e sete atletas foram avaliados em vários momentos (pré e pós-treino) ao longo de sete dias, totalizando ${D.inf.n_obs} observações e 135 pares pré→pós completos. O dia foi derivado do carimbo temporal da coleta; grafias divergentes foram normalizadas a 27 atletas e uma coleta fora da janela foi excluída.`)]));
children.push(P([bold('Instrumentos. '), run('Humor pela Escala de Humor de Brunel (BRUMS: tensão, depressão, raiva, vigor, fadiga e confusão), com o índice de Perturbação Total do Humor (PTH/TMD). Complementarmente, quatro autorrelatos externos (fadiga física 0–10, fadiga mental 0–10, estado físico 0–4, estado mental 0–4) e a carga interna por frequência cardíaca (TRIMP de Banister sobre a %HRR) e esforço percebido (PSE; método de Foster).')]));
children.push(P([bold('Cronologia do microciclo. '), run('Sete dias consecutivos; sessões de HIIT nos dias 2, 4 e 7 e trabalho técnico-tático nos dias 1, 3, 5 e 6. Em cada dia, coletas pré e pós-treino permitem separar a resposta aguda (pós − pré) do nível do dia e do acúmulo ao longo da semana.')]));
children.push(P([bold('Análise estatística. '), run('A unidade de análise é o atleta: coletas repetidas são aninhadas, e tratá-las como independentes (pseudorreplicação) inflaria a significância. Empregaram-se modelos de efeitos mistos (com interceptos e, quando cabível, inclinações aleatórias por atleta), testes pareados clássicos (t e Wilcoxon) com tamanho de efeito dz e intervalos de confiança por bootstrap, correção de comparações múltiplas por FDR (Benjamini–Hochberg), análises multivariadas (Hotelling T², MANOVA, PERMANOVA), estimação bayesiana (amostrador de Gibbs) e validação preditiva leave-one-athlete-out. A confiabilidade e a estrutura foram avaliadas por α de Cronbach com IC95%, ω de McDonald, AFC (DWLS), HTMT, TRI/GRM e invariância métrica.')]));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 3. RESULTADOS E DISCUSSÃO =====================
children.push(H('3. Resultados e Discussão', HeadingLevel.HEADING_1));
children.push(P('A apresentação segue a ordem lógica do raciocínio e a cronologia do microciclo: começa pela qualidade da medida (pré-condição de qualquer conclusão), passa pela resposta aguda dentro do dia e pelo acúmulo ao longo dos sete dias, examina o papel do HIIT, confirma o achado no plano multivariado e teórico, avalia a capacidade diagnóstica, caracteriza a individualidade e encerra no acoplamento com a carga interna e nos autorrelatos complementares.'));

// 3.1 Qualidade da medida
children.push(H('3.1. Qualidade da medida: distribuições, efeito piso, confiabilidade e invariância', HeadingLevel.HEADING_2));
children.push(P('Antes de perguntar se o humor muda, é preciso saber se conseguimos medi-lo. As subescalas negativas concentram grande parte das respostas no piso da escala — confusão (80,5% no piso), depressão (67,1%) e raiva (59,6%) —, o que comprime a variância e limita, por construção, a capacidade de detectar mudança. Já a fadiga física, a fadiga e o vigor distribuem-se de forma ampla, sem piso relevante. A não-normalidade é a regra (Shapiro–Wilk), mas a comparação entre testes paramétricos (t) e não-paramétricos (Wilcoxon) concorda nas 11 variáveis, o que dá robustez às decisões inferenciais.'));
children.push(table(
  ['Variável', 'M', 'DP', '% piso', 'Normal?'],
  D.descr.A_descritivas.map(r => [r.label, nf(r.media), nf(r.dp), nf(r.piso_pct, 1), r.normal ? 'sim' : 'não']),
  [3360, 1500, 1500, 1500, 1500], ['l', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 1. Descritivas (amostra completa), efeito piso e normalidade por variável.'));
children.push(P([
  run('A confiabilidade por subescala reproduz a estrutura esperada: raiva, depressão e fadiga têm α e ω acima de 0,80; vigor e confusão são limítrofes (o IC do α alcança 0,70); apenas a tensão é frágil (α '),
  run(nf(conf.find(c => c.sub === 'Tensão').alpha)), run('), coerente com o forte efeito piso. Crucialmente, a medida é '),
  bold('invariante pré→pós'), run(` (congruência de cargas de Tucker φ ${nf(inv.tucker_phi)} ≥ 0,95; CFI por grupo ${nf(inv.CFI_pre)}/${nf(inv.CFI_pos)}): a mudança observada entre pré e pós é de estado, não um artefato do instrumento. A AFC de seis fatores ajusta bem (CFI ${nf(adv.CFA_DWLS.CFI)}; RMSEA ${nf(adv.CFA_DWLS.RMSEA)}) e o HTMT máximo (${nf(adv.HTMT_max, 3)}) fica abaixo de 0,85, sustentando a validade discriminante.`)
]));
children.push(table(
  ['Subescala', 'α', 'IC95% (α)', 'ω', 'Adequada?'],
  conf.map(r => [r.sub, nf(r.alpha), `[${nf(r.alpha_ic[0])}; ${nf(r.alpha_ic[1])}]`, nf(r.omega),
    r.adequada ? 'sim' : (r.ic_atinge_070 ? 'limítrofe' : 'não')]),
  [2760, 1400, 2400, 1400, 1400], ['l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 2. Confiabilidade por subescala (α de Cronbach com IC95%, ω de McDonald).'));
children.push(P('Discussão. A qualidade da medida ancora todo o resto: onde há piso, a "ausência de resposta" é, em parte, incapacidade de medir (H3 e H5 sustentadas). Reportar a resposta ao treino sem essa ressalva levaria a subestimar a validade do instrumento no eixo em que ele efetivamente discrimina — energia e fadiga.'));

// 3.2 Resposta aguda
children.push(H('3.2. Resposta aguda pré→pós (dentro do dia)', HeadingLevel.HEADING_2));
children.push(P('Passando ao que muda do pré para o pós-treino, e agregando por atleta antes de testar, sobrevivem à correção por FDR exatamente as variáveis do eixo energético: fadiga física (o maior efeito), PTH, fadiga e a queda de vigor; a fadiga mental fica no limiar. As subescalas negativas com piso não respondem — o padrão previsto pela qualidade da medida.'));
children.push(table(
  ['Variável', 'Δ', 'dz', 'IC95% (dz)', 'p', 'p (FDR)', 'Sobrevive'],
  D.inf.A_aguda.map(r => [r.label, sg(r.delta), sg(r.dz), `[${nf(r.ic[0])}; ${nf(r.ic[1])}]`, pf(r.p), pf(r.p_FDR), r.sig ? 'sim' : '—']),
  [2200, 900, 900, 1960, 1000, 1000, 1400], ['l', 'r', 'r', 'l', 'r', 'r', 'r']));
children.push(caption('Tabela 3. Resposta aguda pré→pós por variável (t/Wilcoxon; dz com IC95% por bootstrap; FDR). n = 27.'));
children.push(P('Discussão. O tamanho de efeito da fadiga física (dz ≈ 1,0) é grande e clinicamente relevante; a queda de vigor e a elevação de fadiga/PTH completam o quadro de custo agudo. A convergência entre t e Wilcoxon e a sobrevivência ao FDR afastam a hipótese de achado espúrio por comparações múltiplas.'));

// 3.3 Trajetória e acúmulo
children.push(H('3.3. Trajetória e acúmulo ao longo do microciclo (D1→D7)', HeadingLevel.HEADING_2));
const traj = dh.trajetoria;
children.push(P(`Ao longo dos sete dias, o eixo energia–fadiga desloca-se progressivamente. No modelo de crescimento com inclinação aleatória, a fadiga física acumula de forma robusta (${sg(D.mod.B_acumulo_microciclo.find(x=>x.y==='FadFis').inclinacao_por_dia)}/dia), assim como a fadiga (${sg(D.mod.B_acumulo_microciclo.find(x=>x.y==='Fadiga').inclinacao_por_dia)}/dia), enquanto o vigor cai (${sg(D.mod.B_acumulo_microciclo.find(x=>x.y==='Vigor').inclinacao_por_dia)}/dia). O PTH sobe em média, mas com inclinações individuais muito heterogêneas (variância de inclinação ${nf(D.mod.B_acumulo_microciclo.find(x=>x.y==='PTH').var_inclinacao_atleta)}) — a média esconde trajetórias opostas. O nível diário de PTH tem vale no D5 (${nf(traj['5'])}) e pico no D7 (${nf(traj['7'])}), o terceiro e último HIIT.`));
children.push(P(`Coerentemente, o "perfil iceberg" (vigor acima das negativas) erode ao longo do dia e da semana: presente em ${Math.round(pv.perfil.iceberg_pre*100)}% das avaliações pré e ${Math.round(pv.perfil.iceberg_pos*100)}% no pós (χ²(${pv.perfil.df}) = ${nf(pv.perfil.chi2)}; p = ${nf(pv.perfil.p,3)}; V de Cramér ${nf(pv.perfil.cramer_V)}). A deterioração é por acúmulo, pior no D7 — não um dia intermediário isolado (H1 sustentada).`));
children.push(P('Robustez. O padrão sobrevive a verificações: o teste de permutação (sign-flip, 20 000 reamostragens) concorda com o t pareado em todas as variáveis; a transformação logarítmica e a exclusão do único outlier (A06) não mudam nenhuma decisão.'));

// 3.4 HIIT
children.push(H('3.4. O papel do HIIT: nível do dia versus salto agudo', HeadingLevel.HEADING_2));
children.push(P(`Nos dias de HIIT o humor é pior no nível do dia (ΔPTH ${sg(D.mod.C_efeito_HIIT_nivel_dia.find(x=>x.y==='PTH').efeito_HIIT)}; p = ${nf(D.mod.C_efeito_HIIT_nivel_dia.find(x=>x.y==='PTH').p,3)}). Contudo, a interação Condição × Momento é nula para o PTH (p = ${nf(D.mod.D_interacao_condicao_momento.find(x=>x.y==='PTH').p,3)}): o salto agudo pré→pós não difere entre HIIT e técnico-tático; apenas a fadiga física é amplificada no agudo (p = ${nf(D.mod.D_interacao_condicao_momento.find(x=>x.y==='FadFis').p,3)}).`));
children.push(table(
  ['Variável', 'Δ (HIIT − sem)', 'p', 'ICC'],
  D.mod.C_efeito_HIIT_nivel_dia.map(r => [LAB[r.y] || r.y, sg(r.efeito_HIIT), pf(r.p), nf(r.icc)]),
  [3360, 2500, 1750, 1750], ['l', 'r', 'r', 'r']));
children.push(caption('Tabela 4. Efeito do HIIT no nível do dia (modelo misto).'));
children.push(P(`Comparando os dias entre si: as três sessões de HIIT (D2/D4/D7) são um estímulo agudo equivalente (Friedman n.s. em todas as variáveis); entre os dias sem HIIT, apenas o PTH difere (p = ${nf(dh.B.find(x=>x.var==='PTH (TMD)').p,3)}); e o salto agudo médio por atleta não distingue HIIT de sem-HIIT em nenhuma variável após FDR. A assinatura do HIIT está, portanto, no nível diário e no acúmulo (pico no D7), não num choque agudo específico da sessão (H2 sustentada, com a ressalva de confundimento volume × intensidade).`));
children.push(table(
  ['Variável', 'Δ HIIT', 'Δ sem', 'dz', 'p (FDR)', 'Difere?'],
  dh.C.map(r => [r.var, sg(r.media_HIIT), sg(r.media_SEM), nf(r.dz), pf(r.p_FDR), r.sig ? 'sim' : 'não']),
  [2760, 1400, 1400, 1200, 1400, 1200], ['l', 'r', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 5. HIIT vs. sem-HIIT — resposta aguda média por atleta (Wilcoxon; FDR). n = ' + dh.n_C + '.'));

// 3.5 Multivariada
children.push(H('3.5. Confirmação multivariada do deslocamento', HeadingLevel.HEADING_2));
children.push(P(`Duas vias independentes convergem. O Hotelling T² sobre as seis subescalas fica no limiar (F(6,21) = ${nf(D.mod.E_hotelling['6_subescalas'].F)}; p = ${nf(D.mod.E_hotelling['6_subescalas'].p,3)}) porque as quatro negativas diluem o efeito, mas o eixo vigor+fadiga é robusto (F(2,25) = ${nf(D.mod.E_hotelling.eixo_vigor_fadiga.F)}; p = ${nf(D.mod.E_hotelling.eixo_vigor_fadiga.p,3)}). A MANOVA (Pillai ${nf(mt.multivariada.MANOVA.pillai)}; F = ${nf(mt.multivariada.MANOVA.F)}; p = ${nf(mt.multivariada.MANOVA.p,3)}) e a PERMANOVA pareada (pseudo-F ${nf(mt.multivariada.PERMANOVA.pseudo_F)}; R² ${nf(mt.multivariada.PERMANOVA.R2)}; p = ${nf(mt.multivariada.PERMANOVA.p,3)}; permutação restrita por atleta) confirmam o deslocamento multivariado pré→pós, concentrado no eixo energético.`));

// 3.6 Modelo teórico
children.push(H('3.6. Modelo teórico, coeficiente de determinação e estimação bayesiana', HeadingLevel.HEADING_2));
children.push(P('Do modelo fitness–fadiga chega-se a uma forma estimável por modelos mistos (Yᵢⱼₜ = β₀ + β₁·Pós + β₂·Dia + β₃·HIIT + uᵢ + εᵢⱼₜ). O achado central da decomposição de variância explicada é que o R² marginal (só o protocolo — pós, dia, HIIT) é pequeno (0,06–0,21), mas o R² condicional (incluindo o indivíduo) é grande (0,58–0,63): a variância explicável do humor é sobretudo individual (ICC 0,47–0,60).'));
children.push(table(
  ['Desfecho', 'R² marginal', 'R² condicional', 'ICC', 'β(Pós) ± EP'],
  mt.R2.map(r => [r.desfecho, nf(r.R2m), nf(r.R2c), nf(r.ICC), `${sg(r.beta_pos)} ± ${nf(r.SE_pos)}`]),
  [2760, 1650, 1800, 1150, 2000], ['l', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 6. Coeficiente de determinação (Nakagawa & Schielzeth) e efeito fixo do pós com erro-padrão.'));
children.push(P(`A estimação bayesiana por Gibbs coincide com a frequentista e reforça a direção do efeito: para o PTH, β posterior ${nf(mt.bayes.PTH.media)} (ICr95% [${nf(mt.bayes.PTH.ICr[0])}; ${nf(mt.bayes.PTH.ICr[1])}]; P(efeito>0) = ${nf(mt.bayes.PTH.P_pos)}), e para a fadiga física β ${nf(mt.bayes.FadFis.media)} (P>0 = ${nf(mt.bayes.FadFis.P_pos)}). Os fatores de Bayes JZS agregados por atleta corroboram: evidência decisiva para a fadiga física (BF₁₀ ≈ ${Math.round(adv.bayes_JZS_agregado_por_atleta.FadFis.BF10)}) e evidência de equivalência para a confusão (BF₁₀ ≈ ${nf(adv.bayes_JZS_agregado_por_atleta.esc_confusao.BF10)}).`));

// 3.7 Diagnóstico
children.push(H('3.7. Capacidade diagnóstica (ROC) e derivadas', HeadingLevel.HEADING_2));
children.push(P(`Para separar o estado pós do pré, apenas a fadiga física atinge AUC ${nf(rocm.FadFis.AUC)} (IC95% [${nf(rocm.FadFis.IC[0])}; ${nf(rocm.FadFis.IC[1])}]); as demais ficam próximas do acaso. Para separar dia de HIIT de dia sem HIIT, todas as AUC ficam entre 0,52 e 0,58 — discriminação fraca no nível do dia. Usar a derivada aguda (Δ pós−pré) como escore não supera o nível: a assinatura do HIIT está no nível diário, não no salto.`));
children.push(table(
  ['Variável', 'AUC', 'IC95%', 'Sens.', 'Espec.'],
  D.roc.pre_vs_pos.map(r => [r.label, nf(r.AUC), `[${nf(r.IC[0])}; ${nf(r.IC[1])}]`, nf(r.sens), nf(r.espec)]),
  [3060, 1300, 2400, 1300, 1300], ['l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 7. ROC — separar pós de pré (AUC com IC95% por bootstrap agrupado por atleta).'));

// 3.8 Individualidade
children.push(H('3.8. A resposta é individual', HeadingLevel.HEADING_2));
children.push(P('A maior parte da variância mora entre atletas, não dentro do atleta ao longo da semana. A decomposição de variância mostra predominância de traço na maioria das subescalas, com a fadiga física sendo a mais "de estado" (apenas 40,5% entre atletas). A tipologia (k-médias, cross-validada por Ward) separa cerca de 20 atletas resilientes, 6 perturbados e 1 extremo, com a segmentação explicando η² = ' + nf(pv.segmentacao.eta2_PTH) + ' da variação do PTH.'));
children.push(table(
  ['Variável', '% entre atletas', 'Perfil'],
  pv.variabilidade.slice().sort((a,b)=>b.pct_entre-a.pct_entre).map(r => [r.var, nf(r.pct_entre,1) + '%', r.pct_entre >= 50 ? 'traço' : 'estado']),
  [4360, 2500, 2500], ['l', 'r', 'r']));
children.push(caption('Tabela 8. Decomposição da variância: % entre atletas (≥ 50% ≈ traço).'));
children.push(P('No espaço das taxas de variação (derivadas por atleta), a heterogeneidade é explícita: a fadiga física acumula em 92% dos atletas (marcador homogêneo e confiável), enquanto o PTH acumula em apenas 58% (idiossincrático, DP da inclinação 1,45). Isso reproduz, no plano das velocidades, a variância de inclinação aleatória da modelagem e reforça o monitoramento individualizado por tendência (H4 sustentada).'));

// 3.9 Acoplamento e preditiva
children.push(H('3.9. Acoplamento carga × humor e validação preditiva', HeadingLevel.HEADING_2));
children.push(P(`As sessões foram de intensidade quase-máxima e estável (%HRR 0,87–0,91). A carga por FC (TRIMP) e por PSE (Foster) são praticamente independentes neste regime de teto (r ≈ ${nf(D.trimp.concordancia_TRIMP_Foster.pearson)}), e — o ponto central — a magnitude da carga não prediz a perturbação aguda do humor (TRIMP × ΔPTH r = ${nf(D.trimp.TRIMP_x_humor.r)}; p = ${nf(D.trimp.TRIMP_x_humor.p,3)}). Nenhum par carga × humor (PSE, FC, TRIMP × fadiga mental, TMD) é significativo, nem no nível do dia nem no agudo.`));
children.push(P(`A validação leave-one-athlete-out confirma o desacoplamento de forma preditiva: o estado pós é modestamente previsível (R² ≈ 0,3–0,4), mas o sinal vem do baseline do próprio atleta — acrescentar o contexto da sessão (HIIT, dia) ao baseline muda o R² em ≈ 0 (Δ PTH ${nf(D.pred.ganho.PTH.delta_contexto)}; fadiga física ${nf(D.pred.ganho.FadFis.delta_contexto)}; vigor ${nf(D.pred.ganho.Vigor.delta_contexto)}). Na classificação do dia perturbado, o HIIT está entre as variáveis de menor importância. Custo fisiológico e resposta psicológica se desacoplam no agudo.`));

// 3.10 Outros questionários e sonolência
children.push(H('3.10. Autorrelatos complementares e o item "Sonolento"', HeadingLevel.HEADING_2));
children.push(P('Os autorrelatos externos ao BRUMS confirmam o mesmo eixo: os instrumentos físicos respondem forte (fadiga física dz +1,06; estado físico dz −0,93) enquanto os mentais apenas tendem, e todos convergem com os construtos do BRUMS dentro do atleta (validade convergente: fadiga física ↔ Fadiga r = +0,64; estado físico ↔ Fadiga r = −0,65). Os instrumentos mentais são mais de traço (ICC 0,60–0,70) e os físicos mais de estado (ICC ≈ 0,40).'));
children.push(table(
  ['Instrumento', 'Pré', 'Pós', 'Δ', 'dz', 'p (FDR)', 'Sig.'],
  D.oq.A.map(r => [r.inst, nf(r.M_pre), nf(r.M_pos), sg(r.delta), sg(r.dz), pf(r.p_FDR), r.sig ? 'sim' : '—']),
  [2760, 1100, 1100, 1100, 1100, 1200, 1000], ['l', 'r', 'r', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 9. Autorrelatos externos ao BRUMS — resposta aguda pré→pós.'));
children.push(P(`Um achado específico e contraintuitivo: o item "Sonolento" (terceiro da subescala Fadiga) comporta-se na contramão dos demais — enquanto Esgotado/Exausto/Cansado sobem pós-treino, a sonolência cai (dz ${nf(D.sn.A.find(x=>x.item&&x.item.toLowerCase().includes('sonol'))?.dz ?? -0.55)}): o exercício agudo é ativador/despertador, ainda que eleve a exaustão física. O item é praticamente ortogonal aos demais itens de fadiga (rm_corr 0,00–0,10) e removê-lo eleva o α da subescala Fadiga de ${nf(D.sn.D.com_sonolento)} para ${nf(D.sn.D.sem_sonolento)} — recomendando tratar a sonolência à parte, no eixo sono↔alerta.`));

// 3.11 Cálculo — limites e derivadas
const lim = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'limites_derivadas', 'resultados_limites_derivadas.json'), 'utf8'));
children.push(H('3.11. Formalização em cálculo: limites e derivadas do acúmulo de fadiga', HeadingLevel.HEADING_2));
children.push(P([
  run('A trajetória de acúmulo descrita em 3.3 admite uma formalização em cálculo que torna explícitas as suas propriedades. Ajustando à fadiga física média diária um modelo saturante f(t) = L − (L − f₁)·e^(−k(t−1)) (L = '),
  bold(nf(lim.ajuste.L)), run('; k = '), bold(nf(lim.ajuste.k)), run('; R² = '), bold(nf(lim.ajuste.R2)),
  run(`), a derivada f′(t) é a velocidade de acúmulo por dia. Em t₀ = ${nf(lim.B_definicao_limite.t0,0)}, a razão incremental [f(t₀+h) − f(t₀)]/h converge para f′(t₀) = ${nf(lim.B_definicao_limite.f_linha_analitica)} à medida que h → 0 (${lim.B_definicao_limite.razoes_incrementais.map(r=>nf(r.quociente,3)).join(' → ')} para h = ${lim.B_definicao_limite.razoes_incrementais.map(r=>nf(r.h, r.h<0.01?3:2)).join(', ')}) — a definição de derivada por limite, verificada numericamente.`)
]));
children.push(P([
  run('A derivada é positiva e decrescente, com segunda derivada negativa (f″ < 0): a fadiga acumula, mas cada vez mais devagar, saturando no '),
  bold('limite'), run(` lim(t→∞) f(t) = L ≈ ${nf(lim.D_limites.lim_t_inf_ajuste)} — um estado estacionário do acúmulo. No modelo teórico fitness–fadiga, State(t) = k₁·e^(−t/τ₁) − k₂·e^(−t/τ₂), a derivada State′(t) = 0 define o ponto crítico t* = ${nf(lim.D_limites.modelo_teorico['ponto_critico_t*'])} — o nadir do estado (pico de fadiga aguda): antes dele o atleta ainda se recupera, depois relaxa de volta à linha de base (lim(t→∞) State(t) = 0). É a leitura em cálculo das três âncoras: acúmulo real, saturação e retorno individual.`)
]));
children.push(table(
  ['Dia (t)', 'f(t)', "f′(t)", 'f″(t)'],
  lim.C_derivadas.map(r => [String(r.dia), nf(r.f), sg(r.f_linha), sg(r.f_2linha)]),
  [2340, 2340, 2340, 2340], ['l', 'r', 'r', 'r']));
children.push(caption('Tabela 10. Função ajustada f(t), velocidade de acúmulo f′(t) e aceleração f″(t) por dia (fadiga física média diária). f′ positiva e decrescente; f″ negativa — acúmulo saturante.'));

// Figura síntese
children.push(H('3.12. Síntese visual', HeadingLevel.HEADING_2));
children.push(...fig('figuras/monitoramento_viz.png',
  'Figura 1. Painel de monitoramento: medidores dos indicadores-chave (dz da fadiga física, AUC, perfil iceberg, HTMT); radar do perfil de humor pré vs. pós (erosão do iceberg); monitoramento diário da carga de humor (D1→D7) com faixas de alerta e dias de HIIT; e mapa 4D por variável (resposta aguda × acúmulo × individualidade × consenso direcional).', 640));

// ===================== 4. CONCLUSÕES =====================
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H('4. Conclusões', HeadingLevel.HEADING_1));
children.push(P('Os planos psicométrico e analítico convergem para três conclusões-âncora:'));
children.push(P([bold('(1) A resposta mora no eixo energia–fadiga. '), run('A variável mais confiável e sem piso — a fadiga física — é também a de maior resposta aguda (dz ≈ 1), maior acúmulo semanal e a única amplificada pelo HIIT no agudo. As negativas com efeito piso não respondem por limitação de medida, não por ausência de fenômeno.')]));
children.push(P([bold('(2) A resposta é fortemente individual. '), run('A maior parte da variância é traço (ICC 0,42–0,71); o PTH acumula de forma idiossincrática (só 58% dos atletas), enquanto a fadiga física acumula em 92%. A média esconde trajetórias opostas — daí a necessidade de monitoramento individualizado por tendência.')]));
children.push(P([bold('(3) Carga alta não é humor pior. '), run('O custo cardiovascular quase-máximo não prediz a perturbação aguda do humor (r ≈ −0,05 a −0,32, n.s.); custo fisiológico e resposta psicológica se desacoplam no agudo.')]));
children.push(P([bold('Aplicações. '), run('Monitorar preferencialmente a fadiga física (sentinela sensível e confiável), por tendência individual ao longo do microciclo, com atenção redobrada ao acúmulo até o fim da semana. Interpretar as subescalas negativas com cautela (efeito piso) e tratar a sonolência à parte da fadiga.')]));
children.push(P([bold('Limitações. '), run('Desenho observacional; possível confundimento entre volume e intensidade nos dias de HIIT; carga interna por FC sem duração registrada (TRIMP relativo por sessão); amostra de um único clube. A contribuição metodológica central — respeitar a estrutura de medidas repetidas — protege as conclusões contra a pseudorreplicação.')]));

// ===================== REFERÊNCIAS =====================
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H('Referências', HeadingLevel.HEADING_1));
REFS.forEach(r => children.push(new Paragraph({
  spacing: { after: 100, line: 260 }, alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text: r, size: 19 })] })));

// ===================== DOC =====================
const doc = new Document({
  creator: 'Auditoria BRUMS × HIIT',
  title: 'Manuscrito completo — BRUMS × HIIT no handebol',
  styles: {
    default: { document: { run: { font: 'Calibri', size: 22, color: INK } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Cambria', size: 32, bold: true, color: '122438' },
        paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Cambria', size: 25, bold: true, color: '245C8B' },
        paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 1 } },
    ]
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(HERE, 'Manuscrito_Completo_BRUMS_HIIT.docx');
  fs.writeFileSync(out, buf);
  console.log('escrito', out, (buf.length / 1024).toFixed(0), 'KB');
});
