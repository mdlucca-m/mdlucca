// Gera o ARTIGO ACADÊMICO UNIFICADO (padrão Qualis A1 / internacional, IMRAD)
// a partir dos dados reproduzidos (dashboard_data.json) e das figuras dos módulos.
// Estrutura: Título · Resumo/Abstract · Introdução (+justificativa, objetivos) ·
// Método (+análise estatística) · Resultados (tabelas e figuras) · Discussão ·
// Conclusão · Referências. Unifica o manuscrito e o documento completo num só.
// Uso: node build_artigo.js  (de dentro de tese/)
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, PageBreak,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, ImageRun, TableOfContents
} = require('docx');

const HERE = __dirname, ROOT = path.dirname(HERE);
const D = JSON.parse(fs.readFileSync(path.join(HERE, 'dashboard_data.json'), 'utf8'));
const REFS = JSON.parse(fs.readFileSync(path.join(HERE, 'referencias.json'), 'utf8'));
const lim = JSON.parse(fs.readFileSync(path.join(ROOT, 'limites_derivadas', 'resultados_limites_derivadas.json'), 'utf8'));

// ---------- helpers ----------
const nf = (x, d = 2) => (x === null || x === undefined || isNaN(x)) ? '—' : Number(x).toFixed(d).replace('.', ',');
const pf = (p) => p === null || p === undefined ? '—' : (p < 0.001 ? '< 0,001' : nf(p, 3));
const sg = (x, d = 2) => (x >= 0 ? '+' : '') + nf(x, d);
const CW = 9360;
const INK = '16273D', TEAL = '0E8C86', MUT = '5B6B82', HEADBG = 'EAF1F7', LINE = 'C9D4E0';

function P(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, ...(opts.run || {}) })];
  return new Paragraph({ children: runs, spacing: { after: opts.after ?? 140, line: opts.line ?? 300, before: opts.before ?? 0 },
    alignment: opts.align ?? AlignmentType.JUSTIFIED, ...opts.p });
}
function H(text, level) { return new Paragraph({ heading: level, spacing: { before: 280, after: 120 }, children: [new TextRun({ text })] }); }
function bold(t) { return new TextRun({ text: t, bold: true }); }
function run(t, o = {}) { return new TextRun({ text: t, ...o }); }
function cell(text, { w, head = false, alignRight = false, b = false } = {}) {
  return new TableCell({ width: { size: w, type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: HEADBG, color: 'auto' } : undefined,
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    children: [new Paragraph({ alignment: alignRight ? AlignmentType.RIGHT : AlignmentType.LEFT, spacing: { after: 0, line: 240 },
      children: [new TextRun({ text: String(text), bold: head || b, size: 17, color: head ? INK : undefined })] })] });
}
function table(headers, rows, widths, aligns) {
  const border = { style: BorderStyle.SINGLE, size: 2, color: LINE };
  const borders = { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border };
  const trh = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, { w: widths[i], head: true, alignRight: aligns[i] === 'r' })) });
  const trs = rows.map(r => new TableRow({ children: r.map((c, i) => cell(c, { w: widths[i], alignRight: aligns[i] === 'r' })) }));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths, borders, rows: [trh, ...trs] });
}
function caption(t) { return new Paragraph({ spacing: { before: 60, after: 180 }, children: [new TextRun({ text: t, italics: true, size: 17, color: MUT })] }); }
function pngSize(file) { const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figA(relFile, cap, base = ROOT, maxWin = 6.4) {
  const file = path.join(base, relFile); const { w, h } = pngSize(file);
  let wPx = Math.round(maxWin * 96); let hPx = Math.round(wPx * h / w);
  const maxHpx = Math.round(8.2 * 96);           // não estourar a altura da página
  if (hPx > maxHpx) { hPx = maxHpx; wPx = Math.round(hPx * w / h); }
  return [ new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(file), transformation: { width: wPx, height: hPx } })] }),
    caption(cap) ];
}

// ---------- data ----------
const A = {}; D.inf.A_aguda.forEach(r => A[r.var] = r);
const conf = D.conf.A_confiabilidade, inv = D.conf.B_invariancia, adv = D.adv, mt = D.mt;
const chP = D.chpred.preditores, iv = D.rob.invmg;
const rocpp = D.roc.pre_vs_pos;

const children = [];

// ===================== FOLHA DE ROSTO =====================
children.push(
  new Paragraph({ spacing: { before: 600, after: 60 }, children: [new TextRun({ text: 'ARTIGO ORIGINAL · CIÊNCIAS DO ESPORTE', bold: true, color: TEAL, size: 20, characterSpacing: 40 })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: 'Monitoramento psicométrico do humor e da fadiga em atletas de handebol de elite durante um microciclo com treinamento intervalado de alta intensidade (HIIT): resposta de estado, individualidade e desacoplamento da carga interna', bold: true, size: 34, color: INK })] }),
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: 'Psychometric monitoring of mood and fatigue in elite handball athletes across a high-intensity interval training (HIIT) microcycle: a state response, individuality, and internal-load decoupling', italics: true, size: 22, color: MUT })] }),
  new Paragraph({ spacing: { before: 200, after: 60 }, children: [ run('Título resumido (running head): ', { bold: true, size: 20 }), run('Humor, fadiga e HIIT no handebol', { size: 20 }) ] }),
  new Paragraph({ spacing: { after: 60 }, children: [ run('Autoria: ', { bold: true, size: 20 }), run('[Autor(es)] · [Afiliação(ões)] · [Autor correspondente e e-mail]', { size: 20, color: MUT }) ] }),
  new Paragraph({ spacing: { after: 60 }, children: [ run('Financiamento e conflitos de interesse: ', { bold: true, size: 20 }), run('[a declarar]. ', { size: 20, color: MUT }), run('Aprovação ética: ', { bold: true, size: 20 }), run('[nº do parecer do CEP].', { size: 20, color: MUT }) ] }),
  new Paragraph({ spacing: { after: 60 }, children: [ run('Dados e reprodutibilidade: ', { bold: true, size: 20 }), run('atletas anonimizados (A01–A27); todos os valores reproduzidos por código a partir da coleta bruta; bases identificáveis não versionadas.', { size: 20 }) ] }),
  new Paragraph({ children: [new PageBreak()] })
);

// ===================== RESUMO / ABSTRACT =====================
children.push(H('Resumo', HeadingLevel.HEADING_1));
children.push(P([
  bold('Objetivo. '), run('Caracterizar como o perfil de humor (Escala de Humor de Brunel, BRUMS) de atletas de handebol de elite responde a um microciclo com HIIT — em magnitude, dimensões e confiabilidade de medida — e identificar quais variáveis melhor predizem um estado de fadiga, respeitando a estrutura de medidas repetidas. '),
  bold('Método. '), run(`Estudo observacional longitudinal; 27 atletas avaliados repetidamente (pré/pós-treino) por sete dias, com HIIT nos dias 2, 4 e 7 (${D.inf.n_obs} observações; 135 pares pré→pós). Inferência com o atleta como unidade (modelos mistos; FDR), tamanhos de efeito intra-sujeito (dz), bootstrap agrupado por atleta, psicometria (α, ω, AFC, AFE, TRI), invariância configural→estrita/parcial, ROC e validação preditiva leave-one-athlete-out. `),
  bold('Resultados. '), run(`A resposta concentra-se no eixo energia–fadiga (fadiga física dz ${nf(A.FadFis.dz)}; PTH dz ${nf(A.PTH.dz)}; vigor dz ${nf(A.Vigor.dz)}); as subescalas negativas com efeito piso não respondem. A medida é confiável e invariante pré→pós (Tucker φ ${nf(inv.tucker_phi)}; ΔCFI métrico ${nf(iv.metrico_conjunto.dCFI,3)}). A fadiga física é o marcador mais sensível para o estado de fadiga (AUC ${nf(chP[0].AUC)}); fadiga mental e depressão são sensíveis e confiáveis. A carga interna não prediz o humor (nenhum par sobrevive à FDR; TRIMP×ΔPTH r = ${nf(D.trimp.TRIMP_x_humor.r)}). `),
  bold('Conclusão. '), run('A resposta de humor é real, de estado (não artefato de medida), fortemente individual e não redutível ao custo cardiovascular; o monitoramento eficiente combina a fadiga física (sensibilidade) e a fadiga mental/depressão (confiabilidade).')
]));
children.push(P([bold('Palavras-chave: '), run('humor; fadiga; treinamento intervalado de alta intensidade; handebol; psicometria; medidas repetidas.')]));
children.push(H('Abstract', HeadingLevel.HEADING_1));
children.push(P([
  bold('Objective. '), run('To characterise how the mood profile (Brunel Mood Scale, BRUMS) of elite handball athletes responds to a HIIT microcycle — in magnitude, dimensions and measurement reliability — and to identify which variables best predict a fatigue state, while respecting the repeated-measures structure. '),
  bold('Methods. '), run(`Longitudinal observational study; 27 athletes assessed repeatedly (pre/post) over seven days with HIIT on days 2, 4 and 7 (${D.inf.n_obs} observations; 135 pre→post pairs). Analyses used the athlete as the unit (mixed models; FDR), within-subject effect sizes (dz), athlete-clustered bootstrap, psychometrics (α, ω, CFA, EFA, IRT), configural→strict/partial invariance, ROC and leave-one-athlete-out prediction. `),
  bold('Results. '), run(`Responses concentrate on the energy–fatigue axis (physical fatigue dz ${nf(A.FadFis.dz)}; total mood disturbance dz ${nf(A.PTH.dz)}; vigour dz ${nf(A.Vigor.dz)}); floor-effect negative subscales do not respond. The measure is reliable and invariant pre→post (Tucker's φ ${nf(inv.tucker_phi)}). Physical fatigue is the most sensitive fatigue-state marker (AUC ${nf(chP[0].AUC)}); mental fatigue and depression are both sensitive and reliable. Internal load does not predict mood. `),
  bold('Conclusion. '), run('The mood response is a genuine state shift, strongly individual and not reducible to cardiovascular cost; efficient monitoring combines physical fatigue (sensitivity) with mental fatigue/depression (reliability).')
]));
children.push(P([bold('Keywords: '), run('mood; fatigue; high-intensity interval training; handball; psychometrics; repeated measures.')]));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 1. INTRODUÇÃO =====================
children.push(H('1. Introdução', HeadingLevel.HEADING_1));
children.push(P('O monitoramento do estado psicológico de atletas tornou-se parte central da gestão da carga de treinamento. Medidas subjetivas de humor e fadiga são sensíveis, de baixo custo e não invasivas e, em revisões sistemáticas, refletem a carga aguda e crônica com sensibilidade superior a marcadores objetivos como frequência cardíaca e marcadores bioquímicos (Saw, Main & Gastin, 2016). A Escala de Humor de Brunel (BRUMS) — versão abreviada do POMS — é um dos instrumentos mais utilizados para esse fim, com propriedades psicométricas estabelecidas em diferentes idiomas e populações atléticas (Terry et al., 2022; Zhang et al., 2014).'));
children.push(P('O treinamento intervalado de alta intensidade (HIIT) é um estímulo potente e cada vez mais presente em modalidades intermitentes como o handebol. Sua resposta afetiva, porém, não é trivial: protocolos intervalados podem reduzir tensão e depressão e produzir respostas afetivas positivas remanescentes, a depender da intensidade e do desenho da sessão (Marques et al., 2020; Patten et al., 2022). Em atletas, o quadro clássico é o "perfil iceberg" — vigor elevado sobre baixas dimensões negativas — cuja erosão sinaliza acúmulo de fadiga.'));
children.push(P('Interpretar esse monitoramento, contudo, exige rigor psicométrico e métodos que respeitem a estrutura de medidas repetidas. Uma subescala pode "não responder" a um estímulo por dois motivos radicalmente diferentes: porque o fenômeno não ocorre, ou porque o instrumento não consegue medi-lo (efeito piso). Além disso, coletas repetidas do mesmo atleta são aninhadas; tratá-las como independentes (pseudorreplicação) infla a significância e distorce a inferência.'));
children.push(H('1.1. Justificativa', HeadingLevel.HEADING_2));
children.push(P('Apesar do uso disseminado do BRUMS no esporte, três lacunas persistem na literatura aplicada. Primeiro, poucos estudos separam explicitamente a limitação de mensuração (efeito piso das subescalas negativas) da ausência real de efeito, o que pode levar a subestimar a validade do instrumento no eixo em que ele efetivamente discrimina. Segundo, a relação entre a carga interna objetiva (PSE, FC, TRIMP) e a resposta de humor raramente é testada no nível do atleta com controle de multiplicidade. Terceiro, falta uma caracterização de quais dimensões são simultaneamente sensíveis e confiáveis para sinalizar um estado de fadiga — informação diretamente acionável na periodização. Este estudo enfrenta as três lacunas com uma reanálise completa, reprodutível e metodologicamente disciplinada.'));
children.push(H('1.2. Objetivos e hipóteses', HeadingLevel.HEADING_2));
children.push(P([bold('Objetivo geral. '), run('Caracterizar a resposta do perfil de humor ao longo de um microciclo com HIIT e a confiabilidade dessa medida, e identificar os marcadores mais úteis para o monitoramento da fadiga.')]));
children.push(P([bold('Objetivos específicos. '), run('(a) quantificar a resposta aguda e o acúmulo semanal por subescala; (b) isolar o efeito dos dias de HIIT; (c) avaliar confiabilidade e invariância de medida pré→pós; (d) mensurar a capacidade diagnóstica e preditiva das variáveis; (e) testar o acoplamento carga interna × humor e ranquear preditores de estado de fadiga por sensibilidade e confiabilidade.')]));
children.push(P('Hipóteses: (H1) o humor deteriora ao longo da semana, no eixo energia–fadiga; (H2) os dias de HIIT associam-se a mais fadiga, menos vigor e maior perturbação; (H3) as subescalas negativas têm efeito piso e baixa sensibilidade; (H4) a maior parte da variância é traço, tornando frágil a decisão isolada; (H5) o BRUMS é válido e invariante no eixo energia–fadiga, e a fragilidade das negativas é piso, não ausência.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 2. MÉTODO =====================
children.push(H('2. Método', HeadingLevel.HEADING_1));
children.push(H('2.1. Delineamento e aspectos éticos', HeadingLevel.HEADING_2));
children.push(P('Estudo observacional longitudinal de medidas repetidas, conduzido em contexto ecológico de treinamento. O protocolo respeitou os princípios da Declaração de Helsinque; os participantes forneceram consentimento informado e o estudo foi aprovado pelo comitê de ética institucional [nº do parecer].'));
children.push(H('2.2. Participantes', HeadingLevel.HEADING_2));
children.push(P(`Vinte e sete atletas de handebol de elite foram acompanhados durante um microciclo de sete dias consecutivos, totalizando ${D.inf.n_obs} observações e 135 pares pré→pós completos. Grafias divergentes de identificação foram normalizadas a 27 atletas e uma coleta fora da janela temporal foi excluída; os dados foram anonimizados (A01–A27).`));
children.push(H('2.3. Instrumentos', HeadingLevel.HEADING_2));
children.push(P([bold('Humor. '), run('Escala de Humor de Brunel (BRUMS), com as seis subescalas (tensão, depressão, raiva, vigor, fadiga e confusão) e o índice de Perturbação Total do Humor (PTH/TMD = soma das negativas − vigor). '), bold('Autorrelatos complementares. '), run('Fadiga física (0–10), fadiga mental (0–10), estado físico (0–4) e estado mental (0–4). '), bold('Carga interna. '), run('Esforço percebido da sessão (PSE; método de Foster) e carga por frequência cardíaca (TRIMP de Banister ponderado pela reserva de FC, %HRR).')]));
children.push(H('2.4. Protocolo do microciclo e do HIIT', HeadingLevel.HEADING_2));
children.push(P('Sete dias consecutivos, com sessões de HIIT nos dias 2, 4 e 7 e trabalho técnico-tático nos dias 1, 3, 5 e 6. Em cada dia, coletas pré e pós-treino permitiram separar a resposta aguda (pós − pré) do nível do dia e do acúmulo ao longo da semana. As sessões de HIIT foram quase-máximas (FC de pico 181–184 bpm; %HRR 0,87–0,91; PSE final 9,3–9,6).'));
children.push(H('2.5. Procedimentos e integridade dos dados', HeadingLevel.HEADING_2));
children.push(P('A base foi reconstruída do zero a partir da coleta bruta e recalculada em Python, comparada célula a célula às tabelas e ao texto originais (84 checagens; 77 exatas, 7 reconciliadas — nenhuma correção altera as conclusões). O dia foi derivado do carimbo temporal da coleta.'));
children.push(H('2.6. Análise estatística', HeadingLevel.HEADING_2));
children.push(P('A unidade de análise foi o atleta. Empregaram-se modelos de efeitos mistos (interceptos e, quando cabível, inclinações aleatórias por atleta); testes pareados clássicos (t de Student e Wilcoxon) com tamanho de efeito intra-sujeito (dz) e intervalos de confiança por bootstrap agrupado por atleta; correção de comparações múltiplas por FDR (Benjamini–Hochberg); análise de variância de Friedman/RM-ANOVA para o efeito do dia; e correlação de medidas repetidas (rm_corr) e coeficiente de correlação intraclasse (ICC) para acoplamento e estabilidade. A qualidade da medida foi avaliada por α de Cronbach (com IC95%), ω de McDonald, AFC (estimador DWLS), HTMT, teoria de resposta ao item (modelo de resposta gradual) e análise fatorial exploratória; a equivalência pré→pós, pela hierarquia de invariância configural → métrica → escalar → estrita/parcial (ΔCFI ≤ 0,01; congruência de Tucker φ ≥ 0,95). A capacidade diagnóstica foi quantificada por curvas ROC (AUC com IC95% por bootstrap agrupado por atleta) e a validação preditiva por regressão/classificação leave-one-athlete-out. Confirmação bayesiana (fator de Bayes JZS) e multivariada (Hotelling T², MANOVA/PERMANOVA) complementaram a inferência. Análises em Python (statsmodels, scipy, pingouin, semopy, factor_analyzer); α = 0,05.'));
children.push(...figA('figuras/desenho_analitico.png', 'Figura 1. Desenho analítico do estudo: do microciclo (7 dias, HIIT nos dias 2/4/7) e das coletas pré/pós à cadeia de análises com o atleta como unidade.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 3. RESULTADOS =====================
children.push(H('3. Resultados', HeadingLevel.HEADING_1));

children.push(H('3.1. Qualidade da medida: distribuições, efeito piso e confiabilidade', HeadingLevel.HEADING_2));
children.push(P('As subescalas negativas concentram grande parte das respostas no piso da escala — confusão (80,5%), depressão (67,1%) e raiva (59,6%) —, enquanto fadiga física, fadiga e vigor distribuem-se amplamente (Tabela 1). A não-normalidade é a regra (Shapiro–Wilk), mas testes paramétricos e não-paramétricos concordam nas 11 variáveis. A confiabilidade reproduz a estrutura esperada (Tabela 2): raiva, depressão e fadiga com α e ω acima de 0,80; vigor e confusão limítrofes; apenas a tensão frágil (α ' + nf(conf.find(c => c.sub === 'Tensão').alpha) + '), coerente com o forte efeito piso. A AFC de seis fatores ajusta bem (CFI ' + nf(adv.CFA_DWLS.CFI) + '; RMSEA ' + nf(adv.CFA_DWLS.RMSEA) + ') e o HTMT máximo (' + nf(adv.HTMT_max, 3) + ') fica abaixo de 0,85.'));
children.push(table(['Variável', 'M', 'DP', '% piso', 'Normal?'],
  D.descr.A_descritivas.map(r => [r.label, nf(r.media), nf(r.dp), nf(r.piso_pct, 1), r.normal ? 'sim' : 'não']),
  [3360, 1500, 1500, 1500, 1500], ['l', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 1. Descritivas (amostra completa), efeito piso e normalidade por variável.'));
children.push(table(['Subescala', 'α', 'IC95% (α)', 'ω', 'Adequada?'],
  conf.map(r => [r.sub, nf(r.alpha), `[${nf(r.alpha_ic[0])}; ${nf(r.alpha_ic[1])}]`, nf(r.omega), r.adequada ? 'sim' : (r.ic_atinge_070 ? 'limítrofe' : 'não')]),
  [2760, 1400, 2400, 1400, 1400], ['l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 2. Confiabilidade por subescala (α de Cronbach com IC95%, ω de McDonald).'));
children.push(...figA('figuras/A1_cfa_cargas.png', 'Figura 2. Análise fatorial confirmatória (DWLS): cargas padronizadas por item nas seis subescalas do BRUMS.'));

children.push(H('3.2. Resposta aguda pré→pós', HeadingLevel.HEADING_2));
children.push(P('A resposta aguda concentra-se no eixo energia–fadiga (Tabela 3): fadiga física com efeito grande (dz ' + nf(A.FadFis.dz) + '), seguida de PTH (dz ' + nf(A.PTH.dz) + '), fadiga (dz ' + nf(A.Fadiga.dz) + ') e queda de vigor (dz ' + nf(A.Vigor.dz) + '); todas sobrevivem à FDR. As subescalas negativas com efeito piso não se movem significativamente.'));
children.push(table(['Variável', 'Δ (pós−pré)', 'dz', 'IC95% (dz)', 'p (FDR)', 'Sig.'],
  D.inf.A_aguda.map(r => [r.label, sg(r.delta), sg(r.dz), `[${nf(r.ic[0])}; ${nf(r.ic[1])}]`, pf(r.p_FDR), r.sig ? 'sim' : '—']),
  [3060, 1560, 1200, 2340, 1200, 900], ['l', 'r', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 3. Resposta aguda pré→pós por variável (tamanho de efeito intra-sujeito dz; IC95% por bootstrap; p com FDR).'));
children.push(...figA('figuras/M1_resposta_aguda_dz.png', 'Figura 3. Resposta aguda pré→pós (dz ± IC95%) por variável — a fadiga física ancora o eixo energia–fadiga.'));

children.push(H('3.3. Acúmulo semanal e efeito dos dias de HIIT', HeadingLevel.HEADING_2));
children.push(P('No modelo misto de acúmulo, a fadiga física cresce ~0,34/dia e o PTH acumula de forma heterogênea entre atletas. O efeito do HIIT manifesta-se no nível do dia (Tabela 4): ΔPTH ' + sg(D.inf.C_hiit.find(x=>x.var==='PTH').delta_HIIT) + ' (dz ' + nf(D.inf.C_hiit.find(x=>x.var==='PTH').dz) + '); no plano estritamente agudo, apenas a fadiga física é amplificada pelo HIIT (interação Condição×Momento significativa só para ela). Os coeficientes do modelo (β do momento pós, R² marginal/condicional, ICC) constam da Tabela 4.'));
children.push(table(['Desfecho', 'β (pós)', 'R²m', 'R²c', 'ICC'],
  mt.R2.map(r => [r.desfecho, sg(r.beta_pos), nf(r.R2m), nf(r.R2c), nf(r.ICC)]),
  [3360, 1650, 1450, 1450, 1450], ['l', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 4. Modelos mistos por desfecho: efeito do momento pós (β), variância explicada marginal (R²m) e condicional (R²c) e ICC (proporção de variância entre atletas).'));
children.push(...figA('figuras/M2_acumulo_inclinacao.png', 'Figura 4. Acúmulo ao longo do microciclo com inclinações aleatórias por atleta — trajetórias individuais da fadiga física e do PTH.'));

children.push(H('3.4. Confiabilidade da mudança: invariância de medida pré→pós', HeadingLevel.HEADING_2));
children.push(P('A equivalência de medida entre pré e pós foi testada na hierarquia completa (Tabela 5). A invariância métrica sustenta-se (modelo conjunto ΔCFI ' + nf(iv.metrico_conjunto.dCFI,3) + '; Tucker φ ' + nf(iv.phi_global,3) + '); a escalar é aproximada (viés residual de intercepto RMS ' + nf(iv.escalar.rms,3) + '), com o deslocamento da média latente concentrado em fadiga (' + sg(iv.escalar.kappa.Fadiga) + ') e vigor (' + sg(iv.escalar.kappa.Vigor) + '); a estrita fica no limite (ΔCFI ' + nf(iv.estrita.dCFI,3) + '), com a não-invariância localizada em dois itens, cuja liberação (invariância parcial) reduz o viés de ' + nf(iv.parcial.rms_full,3) + ' para ' + nf(iv.parcial.rms_parcial,3) + '. A mudança pré→pós é, portanto, de estado, não artefato do instrumento.'));
children.push(table(['Nível', 'Índice', 'Valor', 'Veredito'],
  [['Configural', 'CFI pré/pós', nf(iv.cfi_pre)+' / '+nf(iv.cfi_pos), 'equivalente'],
   ['Métrica (conjunta)', 'ΔCFI', nf(iv.metrico_conjunto.dCFI,3), iv.metrico_conjunto.ok?'sustentada':'limítrofe'],
   ['Métrica', 'Tucker φ', nf(iv.phi_global,3), 'φ ≥ 0,95'],
   ['Escalar', 'viés residual RMS', nf(iv.escalar.rms,3), 'aproximada'],
   ['Estrita (resíduos)', 'ΔCFI', nf(iv.estrita.dCFI,3), iv.estrita.ok?'sustentada':'no limite'],
   ['Parcial', 'RMS (full→parcial)', nf(iv.parcial.rms_full,3)+' → '+nf(iv.parcial.rms_parcial,3), 'restabelece']],
  [2760, 2400, 2400, 1800], ['l', 'l', 'r', 'l']));
children.push(caption('Tabela 5. Hierarquia de invariância de medida pré→pós (4 fatores confiáveis; tensão/confusão excluídas por variância degenerada).'));
children.push(...figA('invariancia_multigrupo/invariancia_estrita_parcial_fig.png', 'Figura 5. Invariância estrita e parcial: diagnóstico de não-invariância por item (esq.) e CFI ao longo da hierarquia configural→estrita (dir.).'));

children.push(H('3.5. Capacidade diagnóstica (curvas ROC)', HeadingLevel.HEADING_2));
children.push(P('Para separar o pós do pré-treino, apenas a fadiga física alcança discriminação moderada (Tabela 6; AUC ' + nf(rocpp.find(r=>r.var==='FadFis').AUC) + '); as demais ficam próximas de 0,5. Para separar dia de HIIT de dia sem HIIT, nenhuma variável isolada supera AUC ≈ 0,58 — a variabilidade individual domina a classificação num único dia.'));
children.push(table(['Variável', 'AUC (pós vs. pré)', 'IC95%', 'Sensib.', 'Especif.'],
  rocpp.map(r => [r.label, nf(r.AUC), `[${nf(r.IC[0])}; ${nf(r.IC[1])}]`, nf(r.sens), nf(r.espec)]),
  [3060, 2100, 1900, 1150, 1150], ['l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 6. Capacidade diagnóstica (ROC) para separar pós de pré-treino (AUC com IC95% por bootstrap agrupado por atleta).'));
children.push(...figA('roc/curvas_roc_pre_pos.png', 'Figura 6. Curvas ROC para separar o estado pós do pré-treino por variável.'));

children.push(H('3.6. Predição fora da amostra (leave-one-athlete-out)', HeadingLevel.HEADING_2));
children.push(P('Com validação leave-one-athlete-out (o modelo nunca vê o atleta que prevê), o estado pós é modestamente previsível e o sinal vem do baseline do próprio atleta; adicionar o contexto da sessão (HIIT, dia) ao baseline altera o R² em ≈ 0 — confirmação preditiva do desacoplamento carga↔humor (Tabela 7).'));
{
  const key = ['PTH (TMD)','Fadiga física','Vigor'];
  const rows = D.pred.reg.filter(r => key.includes(r.alvo) && ['Baseline (pré)','Perfil pré completo'].includes(r.preditores))
    .map(r => [r.alvo, r.preditores, nf(r.R2), nf(r.RMSE), r.modelo]);
  children.push(table(['Desfecho', 'Preditores', 'R² (OOF)', 'RMSE', 'Modelo'], rows,
    [2760, 2760, 1280, 1280, 1280], ['l', 'l', 'r', 'r', 'l']));
}
children.push(caption('Tabela 7. Validação preditiva leave-one-athlete-out: variância explicada fora da amostra (R² OOF) por desfecho.'));

children.push(H('3.7. Carga interna × humor e preditores de estado de fadiga', HeadingLevel.HEADING_2));
children.push(P('A carga interna (PSE, FC, TRIMP) mostra-se desacoplada do perfil de humor: nenhum par carga × humor sobrevive à FDR, nas leituras tônica e aguda. Entre as variáveis de humor, os preditores de um estado de fadiga alta vs. baixa (tercis; PTH excluído por circularidade) ordenam-se por sensibilidade e confiabilidade (Tabela 8; Figura 7): a fadiga física é a mais sensível (AUC ' + nf(chP[0].AUC) + '; ICC ' + nf(chP.find(x=>x.label==='Fadiga física').icc) + ' — estado-lábil), a fadiga mental e a depressão são sensíveis e estáveis, e a tensão, apesar de a mais confiável, é cega à fadiga.'));
children.push(table(['Preditor', 'AUC', 'IC95%', 'Sensib.', 'Especif.', 'ICC(2,1)'],
  chP.map(r => [r.label, nf(r.AUC), `[${nf(r.IC[0])}; ${nf(r.IC[1])}]`, nf(r.sens), nf(r.spec), r.icc == null ? '—' : nf(r.icc)]),
  [2960, 1180, 1900, 1080, 1080, 1160], ['l', 'r', 'l', 'r', 'r', 'r']));
children.push(caption('Tabela 8. Preditores de estado de fadiga alta vs. baixa: sensibilidade (AUC, Youden) e confiabilidade (ICC 2,1).'));
children.push(...figA('carga_humor/carga_humor_fig.png', 'Figura 7. Acoplamento carga × humor (tônico e agudo, com FDR) e preditores de estado de fadiga no plano sensibilidade (AUC) × confiabilidade (ICC).'));

children.push(H('3.8. Formalização em cálculo: limites e derivadas do acúmulo', HeadingLevel.HEADING_2));
children.push(P('Ajustando à fadiga física média diária um modelo saturante f(t) = L − (L − f₁)·e^(−k(t−1)) (L = ' + nf(lim.ajuste.L) + '; k = ' + nf(lim.ajuste.k) + '; R² = ' + nf(lim.ajuste.R2) + '), a derivada f′(t) é a velocidade de acúmulo e f″(t) < 0 indica saturação; o limite lim(t→∞) f(t) = L formaliza o estado estacionário (Tabela 9). Coerentemente, a ROC das derivadas mostra que a taxa de variação diagnostica menos que o nível — monitorar "quão cansado" supera "quão rápido está ficando cansado".'));
children.push(table(['Dia (t)', 'f(t)', "f′(t)", 'f″(t)'],
  lim.C_derivadas.map(r => [String(r.dia), nf(r.f), sg(r.f_linha), sg(r.f_2linha)]),
  [2340, 2340, 2340, 2340], ['l', 'r', 'r', 'r']));
children.push(caption('Tabela 9. Função ajustada f(t), velocidade f′(t) e aceleração f″(t) por dia (fadiga física média diária).'));
children.push(...figA('limites_derivadas/limites_derivadas_fig.png', 'Figura 8. Limites e derivadas da trajetória de fadiga: ajuste saturante, velocidade de acúmulo e limite estacionário.'));
children.push(...figA('figuras/monitoramento_viz.png', 'Figura 9. Painel de síntese: medidores dos indicadores-chave, radar do perfil pré×pós (erosão do iceberg), monitoramento diário D1→D7 e mapa 4D das variáveis.', HERE));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 4. DISCUSSÃO =====================
children.push(H('4. Discussão', HeadingLevel.HEADING_1));
children.push(P('Este estudo caracterizou a resposta do humor de atletas de handebol de elite a um microciclo com HIIT e identificou os marcadores mais úteis ao monitoramento, mantendo o atleta como unidade em todas as camadas. Três achados principais emergem e convergem por métodos independentes.'));
children.push(P([bold('A resposta mora no eixo energia–fadiga e é de estado. '), run('A mudança pré→pós é um deslocamento sobre o eixo energia–fadiga (vigor achata, fadiga sobe), com as dimensões negativas quase paradas — erosão do perfil iceberg. A hierarquia de invariância confirma que se trata de mudança de estado, não do significado do instrumento (métrica sustentada; escalar aproximada; estrita no limite, com quebra localizada no item "Sonolento"). O padrão é coerente com a literatura de resposta afetiva a exercício intervalado, em que tensão e depressão tendem a recuar e a resposta é modulada pela intensidade e pelo desenho da sessão (Marques et al., 2020; Patten et al., 2022), e com a validação do BRUMS, que reporta invariância de medida e maior fadiga em atletas (Terry et al., 2022; Zhang et al., 2014).')]));
children.push(P([bold('A resposta é fortemente individual. '), run('A maior parte da variância é traço (ICC 0,42–0,71) e o acúmulo do PTH é idiossincrático, ao passo que a fadiga física acumula de forma homogênea. A predição fora da amostra confirma que o sinal vem do baseline do próprio atleta, não do contexto da sessão — o que desloca a inferência da média do grupo para a tendência individual.')]));
children.push(P([bold('Carga alta não é humor pior. '), run('O custo cardiovascular quase-máximo não prediz a perturbação aguda do humor (desacoplamento robusto à FDR; TRIMP×ΔPTH r = ' + nf(D.trimp.TRIMP_x_humor.r) + '). Num regime de teto, a variação relevante do humor depende de tolerância e recuperação individuais, não da carga objetiva — o que fundamenta a superioridade das medidas subjetivas no monitoramento da resposta ao treino (Saw, Main & Gastin, 2016) e a validade da PSE como marcador de estímulo, não de resposta (Haddad et al., 2017).')]));
children.push(P([bold('Marcadores para o monitoramento. '), run('A fadiga física é o marcador mais sensível de estado de fadiga (AUC ' + nf(chP[0].AUC) + '); sua baixa estabilidade é a assinatura desejável de um sinal de estado. A fadiga mental e a depressão combinam sensibilidade e confiabilidade, servindo ao acompanhamento dia a dia; a tensão, embora estável, é diagnosticamente cega. Isso sustenta um protocolo parcimonioso e de baixo custo.')]));
children.push(P([bold('Pontos fortes e validade. '), run('A disciplina de atleta-como-unidade, a triangulação por métodos independentes (frequentista, bayesiano, multivariado, classificação e cálculo), a caracterização psicométrica completa (confiabilidade, AFC, AFE, TRI, invariância configural→estrita/parcial) e a reprodutibilidade ponta-a-ponta por código conferem robustez incomum. A validade convergente aparece na correlação intra-sujeito entre BRUMS e autorrelatos externos; a de construto, na invariância; a diagnóstica, nas AUC.')]));
children.push(P([bold('Limitações. '), run('Delineamento observacional (associação, não causalidade); amostra de um único clube de elite (27 atletas), o que limita poder para efeitos individuais e generalização; ausência de duração de sessão (TRIMP relativo por %HRR); efeito de teto na carga; itens com efeito piso (tensão, confusão); sonolência medida por um único item.')]));
children.push(P([bold('Direções futuras. '), run('Desenhos com manipulação da carga (dias pareados de alta vs. baixa intensidade) para testar causalidade; séries temporais mais densas por atleta para modelos dinâmicos individuais e mapeamento de não-respondedores; escala de sono/alerta dedicada; integração de marcadores objetivos de recuperação (VFC, sono); e validação prospectiva do protocolo parcimonioso contra desfechos de desempenho e lesão.')]));

// ===================== 5. CONCLUSÃO =====================
children.push(H('5. Conclusão', HeadingLevel.HEADING_1));
children.push(P('O microciclo com HIIT desloca o humor de atletas de elite de forma real e específica sobre o eixo energia–fadiga — erodindo o vigor e elevando a fadiga física —, um efeito de estado (não de medida), fortemente individual e não redutível ao custo cardiovascular da sessão. O monitoramento eficiente depende de escolher os marcadores certos: a fadiga física pela sensibilidade e a fadiga mental e a depressão pela confiabilidade. A convergência de todas as camadas analíticas para a mesma conclusão é a melhor evidência de que ela descreve o fenômeno, e não o método.'));

// ===================== REFERÊNCIAS =====================
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H('Referências', HeadingLevel.HEADING_1));
REFS.forEach(r => children.push(new Paragraph({ spacing: { after: 100, line: 260 }, alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text: r, size: 19 })] })));

// ===================== DOC =====================
const doc = new Document({
  creator: 'BRUMS × HIIT', title: 'Artigo — BRUMS × HIIT no handebol (formato A1)',
  styles: { default: { document: { run: { font: 'Calibri', size: 22, color: INK } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Cambria', size: 30, bold: true, color: '122438' }, paragraph: { spacing: { before: 320, after: 140 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Cambria', size: 24, bold: true, color: '245C8B' }, paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 1 } },
    ] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } }, children }]
});
Packer.toBuffer(doc).then(buf => {
  const out = path.join(HERE, 'Artigo_BRUMS_HIIT_A1.docx');
  fs.writeFileSync(out, buf);
  console.log('escrito', out, (buf.length / 1024).toFixed(0), 'KB');
});
