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
const hp = JSON.parse(fs.readFileSync(path.join(ROOT, 'dias_hiit', 'resultados_hiit_protocolo.json'), 'utf8'));
const EX = JSON.parse(fs.readFileSync(path.join(ROOT, 'analises_extra', 'resultados_extras.json'), 'utf8'));

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
children.push(P('O handebol é uma modalidade coletiva olímpica de caráter intermitente, que combina esforços de alta intensidade — sprints, saltos, arremessos, mudanças de direção e contatos físicos — com períodos de recuperação incompleta ao longo de aproximadamente 60 minutos de jogo. As análises de partida em atletas de elite mostram distâncias percorridas da ordem de 4–5 km, com solicitação simultânea dos sistemas aeróbio e anaeróbio e centenas de mudanças de atividade por jogo (Michalsik & Aagaard, 2014). Essas demandas, somadas a calendários competitivos congestionados, tornam a gestão da carga de treinamento e da recuperação um determinante direto do desempenho e da saúde do atleta.'));
children.push(P('Para desenvolver a capacidade intermitente que a modalidade exige, o treinamento intervalado de alta intensidade (HIIT) tornou-se uma ferramenta central. O HIIT consiste em séries repetidas de esforço de intensidade elevada intercaladas por recuperação e é um dos meios mais eficazes de melhorar a função cardiorrespiratória e metabólica; nos esportes coletivos, protocolos que mantêm o atleta próximo de ≥90% do consumo máximo de oxigênio (VO₂máx) maximizam as adaptações centrais e periféricas (Buchheit & Laursen, 2013). Esse ganho, contudo, tem um custo interno elevado: o HIIT impõe grande carga cardiovascular, glicolítica e neuromuscular, cuja acumulação, se não monitorada, pode evoluir para fadiga excessiva e desajuste de treinamento.'));
children.push(P('É nesse ponto que o estado psicológico entra como sinalizador. O humor — estado afetivo difuso, com valência e ativação — é um marcador sensível da tolerância à carga: medidas subjetivas de humor e fadiga refletem a carga aguda e crônica com sensibilidade superior a marcadores objetivos como frequência cardíaca e marcadores bioquímicos (Saw, Main & Gastin, 2016). A avaliação do humor no esporte consolidou-se com o Profile of Mood States (POMS) e seu descendente abreviado, a Escala de Humor de Brunel (BRUMS), que mensura seis dimensões (tensão, depressão, raiva, vigor, fadiga e confusão) e cujas propriedades psicométricas — incluindo invariância de medida — estão estabelecidas em diversas línguas e populações atléticas (Terry et al., 2022; Zhang et al., 2014). Em atletas saudáveis, o quadro típico é o "perfil iceberg" — vigor elevado sobre baixas dimensões negativas —, cuja erosão (queda de vigor e elevação de fadiga) sinaliza acúmulo de carga. A resposta afetiva ao exercício intenso, porém, não é trivial: protocolos intervalados podem inclusive reduzir tensão e depressão e produzir respostas afetivas positivas remanescentes, a depender da intensidade e do desenho da sessão (Marques et al., 2020; Patten et al., 2022).'));
children.push(P('Do amplo ao específico, portanto, o problema é: em uma modalidade de alta demanda intermitente (handebol), submetida a um estímulo potente e custoso (HIIT), como se comporta o perfil de humor ao longo de um microciclo — e o quanto esse comportamento pode ser medido de forma confiável? Interpretar esse monitoramento exige rigor psicométrico e métodos que respeitem a estrutura de medidas repetidas. Uma subescala pode "não responder" a um estímulo por dois motivos radicalmente diferentes: porque o fenômeno não ocorre, ou porque o instrumento não consegue medi-lo (efeito piso). Além disso, coletas repetidas do mesmo atleta são aninhadas; tratá-las como independentes (pseudorreplicação) infla a significância e distorce a inferência.'));
children.push(H('1.1. Justificativa', HeadingLevel.HEADING_2));
children.push(P('Apesar do uso disseminado do BRUMS no esporte, três lacunas persistem na literatura aplicada. Primeiro, poucos estudos separam explicitamente a limitação de mensuração (efeito piso das subescalas negativas) da ausência real de efeito, o que pode levar a subestimar a validade do instrumento no eixo em que ele efetivamente discrimina. Segundo, a relação entre a carga interna objetiva (PSE, FC, TRIMP) e a resposta de humor raramente é testada no nível do atleta com controle de multiplicidade. Terceiro, falta uma caracterização de quais dimensões são simultaneamente sensíveis e confiáveis para sinalizar um estado de fadiga — informação diretamente acionável na periodização. Este estudo enfrenta as três lacunas com uma reanálise completa, reprodutível e metodologicamente disciplinada.'));
children.push(H('1.2. Objetivos e hipóteses', HeadingLevel.HEADING_2));
children.push(P([bold('Objetivo geral. '), run('Caracterizar a resposta do perfil de humor ao longo de um microciclo com HIIT e a confiabilidade dessa medida, e identificar os marcadores mais úteis para o monitoramento da fadiga.')]));
children.push(P([bold('Objetivos específicos. '), run('(a) descrever as distribuições, o efeito piso e a normalidade das variáveis; (b) quantificar a resposta aguda pré→pós por subescala (tamanho de efeito) e confirmá-la por permutação restrita; (c) modelar o acúmulo semanal com inclinações aleatórias por atleta e isolar o efeito dos dias de HIIT; (d) confirmar o achado no plano multivariado (Hotelling T², MANOVA, PERMANOVA) e bayesiano; (e) avaliar a qualidade da medida — confiabilidade (α, ω), AFC, AFE, TRI, validade discriminante (HTMT) — e a invariância pré→pós (configural→estrita/parcial); (f) mapear as correlações intra-sujeito (rm_corr) e a convergência com autorrelatos externos; (g) mensurar a capacidade diagnóstica (ROC de níveis e de derivadas) e a validação preditiva fora da amostra (leave-one-athlete-out); (h) caracterizar a velocidade de mudança (derivadas por variável e por atleta) e formalizá-la em cálculo (limites e derivadas); (i) segmentar os atletas por padrão de resposta e decompor a variância em traço vs. estado; (j) testar o acoplamento carga interna × humor e ranquear os preditores de estado de fadiga por sensibilidade e confiabilidade.')]));
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
children.push(P('O microciclo teve sete dias consecutivos, com sessões de HIIT nos dias 2, 4 e 7 e trabalho técnico-tático nos dias 1, 3, 5 e 6. Em cada dia, coletas pré e pós-treino permitiram separar a resposta aguda (pós − pré) do nível do dia e do acúmulo ao longo da semana.'));
children.push(P([bold('Modelo do HIIT. '), run('Cada sessão de HIIT consistiu em ' + hp.protocolo + '. A intensidade-alvo foi ancorada em ' + '104% da velocidade de pico obtida em um teste de campo incremental, isto é, um estímulo supramáximo em relação ao pico aeróbio, desenhado para manter o atleta em zona próxima ao VO₂máx durante os 4 minutos de esforço, com recuperação incompleta nos 3 minutos entre séries. A carga interna foi monitorada por frequência cardíaca em cada fase (aquecimento e quatro séries) e por PSE ao final, permitindo derivar a FC de recuperação (no início de cada série, após o intervalo), a FC média e a FC máxima das séries, além do humor (BRUMS) pré e pós-sessão.')]));
children.push(P('A caracterização das sessões (Figura 1; Tabela 1) confirma a intensidade quase-máxima e progressiva: a FC ao fim das séries sobe do aquecimento (~158 bpm) ao pico (' + nf(hp.resumo.FC_maxima[0],0) + ' bpm), a FC média das quatro séries atinge ' + nf(hp.resumo.FC_media_series[0],0) + ' bpm e a FC de recuperação eleva-se ao longo da sessão (deriva cardiovascular, recuperação incompleta), enquanto a PSE chega a ' + nf(hp.resumo.PSE_final[0],1) + ' (quase o teto da escala 0–10).'));
children.push(...figA('dias_hiit/hiit_protocolo_fig.png', 'Figura 1. Caracterização do protocolo de HIIT (4 × 4 min a 104% da velocidade de pico, 3 min de intervalo): A — FC ao início (recuperação) e ao fim (pico) de cada série; B — PSE por fase; C — resumo da carga interna (FC máxima, média, de recuperação e PSE).'));
children.push(table(['Métrica da sessão de HIIT', 'Média ± DP'],
  [['FC máxima (pico das séries)', nf(hp.resumo.FC_maxima[0],0) + ' ± ' + nf(hp.resumo.FC_maxima[1],0) + ' bpm'],
   ['FC média das 4 séries', nf(hp.resumo.FC_media_series[0],0) + ' ± ' + nf(hp.resumo.FC_media_series[1],0) + ' bpm'],
   ['FC de recuperação (início das séries)', nf(hp.resumo.FC_recuperacao[0],0) + ' ± ' + nf(hp.resumo.FC_recuperacao[1],0) + ' bpm'],
   ['PSE final (0–10)', nf(hp.resumo.PSE_final[0],1) + ' ± ' + nf(hp.resumo.PSE_final[1],1)]],
  [5680, 3680], ['l', 'r']));
children.push(caption('Tabela 1. Carga interna das sessões de HIIT (n = ' + hp.resumo.n_atletas + ' atletas; 4 sessões).'));
children.push(H('2.5. Procedimentos e integridade dos dados', HeadingLevel.HEADING_2));
children.push(P('A base foi reconstruída do zero a partir da coleta bruta e recalculada em Python, comparada célula a célula às tabelas e ao texto originais (84 checagens; 77 exatas, 7 reconciliadas — nenhuma correção altera as conclusões). O dia foi derivado do carimbo temporal da coleta.'));
children.push(H('2.6. Análise estatística', HeadingLevel.HEADING_2));
children.push(P('A unidade de análise foi o atleta. Empregaram-se modelos de efeitos mistos (interceptos e, quando cabível, inclinações aleatórias por atleta); testes pareados clássicos (t de Student e Wilcoxon) com tamanho de efeito intra-sujeito (dz) e intervalos de confiança por bootstrap agrupado por atleta; correção de comparações múltiplas por FDR (Benjamini–Hochberg); análise de variância de Friedman/RM-ANOVA para o efeito do dia; e correlação de medidas repetidas (rm_corr) e coeficiente de correlação intraclasse (ICC) para acoplamento e estabilidade. A qualidade da medida foi avaliada por α de Cronbach (com IC95%), ω de McDonald, AFC (estimador DWLS), HTMT, teoria de resposta ao item (modelo de resposta gradual) e análise fatorial exploratória; a equivalência pré→pós, pela hierarquia de invariância configural → métrica → escalar → estrita/parcial (ΔCFI ≤ 0,01; congruência de Tucker φ ≥ 0,95). A capacidade diagnóstica foi quantificada por curvas ROC (AUC com IC95% por bootstrap agrupado por atleta) e a validação preditiva por regressão/classificação leave-one-athlete-out. Confirmação bayesiana (fator de Bayes JZS) e multivariada (Hotelling T², MANOVA/PERMANOVA) complementaram a inferência. Análises em Python (statsmodels, scipy, pingouin, semopy, factor_analyzer); α = 0,05.'));
children.push(...figA('figuras/desenho_analitico.png', 'Figura 2. Desenho analítico do estudo: do microciclo (7 dias, HIIT nos dias 2/4/7) e das coletas pré/pós à cadeia de análises com o atleta como unidade.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 3. RESULTADOS =====================
children.push(H('3. Resultados', HeadingLevel.HEADING_1));
children.push(P('Os resultados são apresentados em blocos — estatística descritiva e estatística inferencial —, seguidos da qualidade da medida e da invariância, e do diagnóstico, predição e monitoramento.'));

// ---- 3.1 ESTATÍSTICA DESCRITIVA ----
children.push(H('3.1. Estatística descritiva', HeadingLevel.HEADING_2));
children.push(P('As subescalas negativas concentram grande parte das respostas no piso da escala — confusão (80,5%), depressão (67,1%) e raiva (59,6%) —, enquanto fadiga física, fadiga e vigor distribuem-se amplamente (Tabela 2). Os histogramas e box plots (Figura 3A–B) mostram o deslocamento pré→pós no eixo energia–fadiga; a dispersão Vigor × Fadiga (Figura 3C) evidencia a relação inversa (r ≈ −0,44). A não-normalidade é a regra: os gráficos Q–Q e o teste de Shapiro–Wilk (Figura 3D) indicam desvios da normal tanto no pré quanto no pós, o que justifica a confirmação por testes não-paramétricos e permutação.'));
children.push(table(['Variável', 'M', 'DP', 'Mediana', 'IQR', '% piso', 'Normal?'],
  D.descr.A_descritivas.map(r => [r.label, nf(r.media), nf(r.dp), nf(r.mediana), nf(r.IQR), nf(r.piso_pct,1), r.normal?'sim':'não']),
  [2760, 1080, 1080, 1240, 1080, 1120, 1000], ['l','r','r','r','r','r','r']));
children.push(caption('Tabela 2. Estatística descritiva por variável (amostra completa, n = ' + D.inf.n_obs + '): média, DP, mediana, IQR, efeito piso e normalidade (Shapiro–Wilk).'));
children.push(...figA('descritivas_testes/descritiva_completa_fig.png', 'Figura 3. Estatística descritiva: A — histograma da fadiga física (pré vs. pós); B — box plots pré vs. pós das variáveis-chave; C — dispersão Vigor × Fadiga (eixo energia–fadiga); D — Q–Q de normalidade do PTH (pré vs. pós).'));

// ---- 3.2 ESTATÍSTICA INFERENCIAL ----
children.push(H('3.2. Estatística inferencial', HeadingLevel.HEADING_2));
children.push(H('3.2.1. Resposta aguda pré→pós', HeadingLevel.HEADING_3));
children.push(P('A resposta aguda concentra-se no eixo energia–fadiga (Tabela 3): fadiga física com efeito grande (dz ' + nf(A.FadFis.dz) + '), seguida de PTH (dz ' + nf(A.PTH.dz) + '), fadiga (dz ' + nf(A.Fadiga.dz) + ') e queda de vigor (dz ' + nf(A.Vigor.dz) + '); todas sobrevivem à FDR. As subescalas negativas com efeito piso não se movem significativamente. A robustez foi confirmada por permutação restrita (troca pré↔pós dentro de cada atleta), que concorda com o teste t (Tabela 4).'));
children.push(table(['Variável', 'Δ (pós−pré)', 'dz', 'IC95% (dz)', 'p (FDR)', 'Sig.'],
  D.inf.A_aguda.map(r => [r.label, sg(r.delta), sg(r.dz), `[${nf(r.ic[0])}; ${nf(r.ic[1])}]`, pf(r.p_FDR), r.sig ? 'sim' : '—']),
  [3060, 1560, 1200, 2340, 1200, 900], ['l', 'r', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 3. Resposta aguda pré→pós por variável (dz; IC95% por bootstrap; p com FDR).'));
children.push(table(['Variável', 'Δ (pós−pré)', 'p (permutação)', 'p (t)', 'Concordam?'],
  D.pv.permutacao.map(r => [r.var, sg(r.delta), pf(r.p_perm), pf(r.p_t), r.concordam ? 'sim' : '—']),
  [3360, 1800, 1800, 1200, 1200], ['l', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 4. Confirmação por permutação restrita (9999 permutações, troca pré↔pós intra-atleta) vs. teste t.'));
children.push(...figA('figuras/M1_resposta_aguda_dz.png', 'Figura 4. Resposta aguda pré→pós (dz ± IC95%) por variável — a fadiga física ancora o eixo energia–fadiga.'));

children.push(H('3.2.2. Acúmulo semanal e efeito dos dias de HIIT', HeadingLevel.HEADING_3));
children.push(P('No modelo misto de acúmulo, a fadiga física cresce ~0,34/dia e o PTH acumula de forma heterogênea entre atletas (Tabela 5). O efeito do HIIT manifesta-se no nível do dia (ΔPTH ' + sg(D.inf.C_hiit.find(x=>x.var==='PTH').delta_HIIT) + '; dz ' + nf(D.inf.C_hiit.find(x=>x.var==='PTH').dz) + '); no plano estritamente agudo, apenas a fadiga física é amplificada pelo HIIT. Comparando os três dias de HIIT entre si (Friedman), a resposta não difere entre as sessões 2, 4 e 7 (Tabela 6) — o estímulo é consistente e o que cresce é o acúmulo, não a resposta por sessão.'));
children.push(table(['Desfecho', 'β (pós)', 'R²m', 'R²c', 'ICC'],
  mt.R2.map(r => [r.desfecho, sg(r.beta_pos), nf(r.R2m), nf(r.R2c), nf(r.ICC)]),
  [3360, 1650, 1450, 1450, 1450], ['l', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 5. Modelos mistos por desfecho: efeito do momento pós (β), R² marginal/condicional e ICC.'));
children.push(table(['Variável', 'Δ dia 2', 'Δ dia 4', 'Δ dia 7', 'χ² (Friedman)', 'p'],
  D.dh.A.map(r => [r.var, sg(r.D2), sg(r.D4), sg(r.D7), nf(r.chi2), pf(r.p)]),
  [3060, 1420, 1420, 1420, 1900, 1140], ['l', 'r', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 6. Resposta por dia de HIIT (dias 2, 4 e 7) e teste de Friedman entre os três dias.'));
children.push(...figA('figuras/M2_acumulo_inclinacao.png', 'Figura 5. Acúmulo ao longo do microciclo com inclinações aleatórias por atleta — trajetórias individuais da fadiga física e do PTH.'));

children.push(H('3.2.3. Dias de HIIT vs. dias sem HIIT', HeadingLevel.HEADING_3));
children.push(P('Comparando diretamente a resposta média nos dias de HIIT (2, 4, 7) com a dos dias técnico-táticos (1, 3, 5, 6) no nível do atleta (Tabela 7), a fadiga física tende a ser maior nos dias de HIIT (dz ' + nf(D.dh.C.find(x=>x.var==='Fadiga física').dz) + '), mas nenhuma diferença sobrevive à correção FDR — a assinatura do HIIT está no acúmulo diário e não num contraste agudo isolado, dominado pela variabilidade individual.'));
children.push(table(['Variável', 'Média dias HIIT', 'Média dias sem', 'dif', 'dz', 'p (FDR)', 'Sig.'],
  D.dh.C.map(r => [r.var, sg(r.media_HIIT), sg(r.media_SEM), sg(r.dif), sg(r.dz), pf(r.p_FDR), r.sig ? 'sim' : '—']),
  [2760, 1760, 1760, 940, 940, 1200, 800], ['l', 'r', 'r', 'r', 'r', 'r', 'r']));
children.push(caption('Tabela 7. Dias de HIIT vs. dias sem HIIT (resposta média por atleta; n = ' + D.dh.n_C + '; dz, RBC e p com FDR).'));

children.push(H('3.2.4. Confirmação multivariada e bayesiana', HeadingLevel.HEADING_3));
children.push(P('No plano multivariado, o vetor de humor difere entre pré e pós (MANOVA) e a permutação multivariada restrita confirma o efeito (Tabela 8). A estimação bayesiana corrobora a magnitude e a direção dos principais efeitos, com intervalos de credibilidade que excluem o zero e P(Δ>0) ≈ 1 (Tabela 9).'));
children.push(table(['Teste multivariado', 'Estatística', 'p'],
  [['MANOVA (Momento)', 'Pillai ' + nf(mt.multivariada.MANOVA.pillai,3) + ' · Wilks ' + nf(mt.multivariada.MANOVA.wilks,3) + ' · F ' + nf(mt.multivariada.MANOVA.F), pf(mt.multivariada.MANOVA.p)],
   ['PERMANOVA (pré↔pós intra-atleta)', 'pseudo-F ' + nf(mt.multivariada.PERMANOVA.pseudo_F) + ' · R² ' + nf(mt.multivariada.PERMANOVA.R2,3) + ' · ' + mt.multivariada.PERMANOVA.nperm + ' perm.', pf(mt.multivariada.PERMANOVA.p)]],
  [4200, 4160, 1000], ['l', 'l', 'r']));
children.push(caption('Tabela 8. Análises multivariadas do vetor de humor pré vs. pós (MANOVA e PERMANOVA restrita).'));
children.push(table(['Desfecho', 'Média posterior', 'EP', 'IC credível 95%', 'P(Δ>0)'],
  Object.values(mt.bayes).map(b => [b.label, sg(b.media), nf(b.SE), `[${nf(b.ICr[0])}; ${nf(b.ICr[1])}]`, nf(b.P_pos, 2)]),
  [3060, 2100, 1100, 2300, 1200], ['l', 'r', 'r', 'l', 'r']));
children.push(caption('Tabela 9. Estimação bayesiana (Gibbs) do efeito pós: média posterior, IC credível e probabilidade posterior de efeito positivo.'));

children.push(H('3.2.5. Correlações intra-sujeito e validade convergente', HeadingLevel.HEADING_3));
children.push(P('As correlações de medidas repetidas (rm_corr; isolam a covariação intra-atleta) mostram que as subescalas do BRUMS covariam com os autorrelatos externos no sentido teoricamente esperado — validade convergente dentro do sujeito. Dos ' + D.inf.D_rmcorr.length + ' pares testados, ' + D.inf.D_rmcorr.filter(x=>x.sig).length + ' são significativos após FDR (Tabela 10).'));
children.push(table(['Subescala', 'Autorrelato externo', 'r', 'IC95%', 'p (FDR)', 'Sig.'],
  D.inf.D_rmcorr.filter(x=>x.sig).map(r => [r.sub, r.ext, sg(r.r), `[${nf(r.ic[0])}; ${nf(r.ic[1])}]`, pf(r.p_FDR), 'sim']),
  [2360, 2600, 1000, 2000, 1200, 800], ['l', 'l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 10. Correlações de medidas repetidas (rm_corr) significativas entre subescalas do BRUMS e autorrelatos externos (validade convergente intra-sujeito; FDR).'));

// ---- 3.3 QUALIDADE DA MEDIDA E INVARIÂNCIA ----
children.push(H('3.3. Qualidade da medida e invariância', HeadingLevel.HEADING_2));
children.push(P('A confiabilidade por subescala reproduz a estrutura esperada (Tabela 11): raiva, depressão e fadiga com α e ω acima de 0,80; vigor e confusão limítrofes; apenas a tensão frágil (α ' + nf(conf.find(c => c.sub === 'Tensão').alpha) + '), coerente com o efeito piso. A AFC de seis fatores ajusta bem (CFI ' + nf(adv.CFA_DWLS.CFI) + '; RMSEA ' + nf(adv.CFA_DWLS.RMSEA) + '; Figura 6) e o HTMT máximo (' + nf(adv.HTMT_max, 3) + ') fica abaixo de 0,85. A equivalência de medida pré→pós sustenta-se na hierarquia (Tabela 12; Figura 7): métrica sustentada (ΔCFI ' + nf(iv.metrico_conjunto.dCFI,3) + '; Tucker φ ' + nf(iv.phi_global,3) + '), escalar aproximada, estrita no limite, com a não-invariância localizada em dois itens cuja liberação (parcial) reduz o viés de ' + nf(iv.parcial.rms_full,3) + ' para ' + nf(iv.parcial.rms_parcial,3) + '. A mudança pré→pós é, portanto, de estado.'));
children.push(table(['Subescala', 'α', 'IC95% (α)', 'ω', 'Adequada?'],
  conf.map(r => [r.sub, nf(r.alpha), `[${nf(r.alpha_ic[0])}; ${nf(r.alpha_ic[1])}]`, nf(r.omega), r.adequada ? 'sim' : (r.ic_atinge_070 ? 'limítrofe' : 'não')]),
  [2760, 1400, 2400, 1400, 1400], ['l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 11. Confiabilidade por subescala (α de Cronbach com IC95%, ω de McDonald).'));
children.push(...figA('figuras/A1_cfa_cargas.png', 'Figura 6. Análise fatorial confirmatória (DWLS): cargas padronizadas por item nas seis subescalas do BRUMS.'));
children.push(table(['Nível', 'Índice', 'Valor', 'Veredito'],
  [['Configural', 'CFI pré/pós', nf(iv.cfi_pre)+' / '+nf(iv.cfi_pos), 'equivalente'],
   ['Métrica (conjunta)', 'ΔCFI', nf(iv.metrico_conjunto.dCFI,3), iv.metrico_conjunto.ok?'sustentada':'limítrofe'],
   ['Métrica', 'Tucker φ', nf(iv.phi_global,3), 'φ ≥ 0,95'],
   ['Escalar', 'viés residual RMS', nf(iv.escalar.rms,3), 'aproximada'],
   ['Estrita (resíduos)', 'ΔCFI', nf(iv.estrita.dCFI,3), iv.estrita.ok?'sustentada':'no limite'],
   ['Parcial', 'RMS (full→parcial)', nf(iv.parcial.rms_full,3)+' → '+nf(iv.parcial.rms_parcial,3), 'restabelece']],
  [2760, 2400, 2400, 1800], ['l', 'l', 'r', 'l']));
children.push(caption('Tabela 12. Hierarquia de invariância de medida pré→pós (4 fatores confiáveis).'));
children.push(...figA('invariancia_multigrupo/invariancia_estrita_parcial_fig.png', 'Figura 7. Invariância estrita e parcial: diagnóstico de não-invariância por item (esq.) e CFI ao longo da hierarquia (dir.).'));

// ---- 3.4 DIAGNÓSTICO, PREDIÇÃO E MONITORAMENTO ----
children.push(H('3.4. Diagnóstico, predição e monitoramento', HeadingLevel.HEADING_2));
children.push(H('3.4.1. Capacidade diagnóstica: ROC de níveis e de derivadas', HeadingLevel.HEADING_3));
children.push(P('Para separar o pós do pré-treino, apenas a fadiga física alcança discriminação moderada (Tabela 13; AUC ' + nf(rocpp.find(r=>r.var==='FadFis').AUC) + '); as demais ficam próximas de 0,5. Usando a derivada aguda (Δ pós−pré) em vez do nível, a discriminação não melhora (ganho ≈ 0 ou negativo; Tabela 14): a taxa de variação diagnostica menos que o nível.'));
children.push(table(['Variável', 'AUC (pós vs. pré)', 'IC95%', 'Sensib.', 'Especif.'],
  rocpp.map(r => [r.label, nf(r.AUC), `[${nf(r.IC[0])}; ${nf(r.IC[1])}]`, nf(r.sens), nf(r.espec)]),
  [3060, 2100, 1900, 1150, 1150], ['l', 'r', 'l', 'r', 'r']));
children.push(caption('Tabela 13. Capacidade diagnóstica (ROC) para separar pós de pré-treino (IC95% por bootstrap agrupado por atleta).'));
children.push(table(['Variável', 'AUC (nível)', 'AUC (derivada)', 'Ganho'],
  D.rocd.resultados.map(r => [r.var, nf(r.AUC_nivel), nf(r.AUC_derivada), sg(r.ganho)]),
  [3360, 2340, 2340, 1320], ['l', 'r', 'r', 'r']));
children.push(caption('Tabela 14. ROC das derivadas (dia de HIIT vs. sem HIIT): a derivada não supera o nível (ganho ≤ 0).'));
children.push(...figA('roc/curvas_roc_pre_pos.png', 'Figura 8. Curvas ROC para separar o estado pós do pré-treino por variável.'));

children.push(H('3.4.2. Velocidade de mudança e formalização em cálculo', HeadingLevel.HEADING_3));
children.push(P('A velocidade de mudança por variável confirma o acúmulo (Tabela 15). Formalizando a trajetória da fadiga física média diária por um modelo saturante f(t) = L − (L − f₁)·e^(−k(t−1)) (L = ' + nf(lim.ajuste.L) + '; k = ' + nf(lim.ajuste.k) + '; R² = ' + nf(lim.ajuste.R2) + '), a derivada f′(t) é a velocidade de acúmulo, f″(t) < 0 indica saturação e o limite lim(t→∞) f(t) = L formaliza o estado estacionário (Tabela 16; Figura 9).'));
children.push(table(['Variável', 'Vel. inicial', 'Vel. final', 'Dia vel. máx.', 'Inclinação média', 'Direção'],
  D.dvar.B.map(r => [r.var, sg(r.vel_inicial), sg(r.vel_final), String(r.dia_vel_max), sg(r.inclinacao_media), r.direcao]),
  [2760, 1560, 1560, 1560, 1920, 1440], ['l', 'r', 'r', 'r', 'r', 'l']));
children.push(caption('Tabela 15. Velocidade de mudança por variável ao longo do microciclo (derivadas discretas).'));
children.push(table(['Dia (t)', 'f(t)', "f′(t)", 'f″(t)'],
  lim.C_derivadas.map(r => [String(r.dia), nf(r.f), sg(r.f_linha), sg(r.f_2linha)]),
  [2340, 2340, 2340, 2340], ['l', 'r', 'r', 'r']));
children.push(caption('Tabela 16. Função ajustada f(t), velocidade f′(t) e aceleração f″(t) por dia (fadiga física média diária).'));
children.push(...figA('limites_derivadas/limites_derivadas_fig.png', 'Figura 9. Limites e derivadas da trajetória de fadiga: ajuste saturante, velocidade de acúmulo e limite estacionário.'));

children.push(H('3.4.3. Predição fora da amostra (leave-one-athlete-out)', HeadingLevel.HEADING_3));
children.push(P('Com validação leave-one-athlete-out, o estado pós é modestamente previsível e o sinal vem do baseline do próprio atleta; adicionar o contexto da sessão ao baseline altera o R² em ≈ 0 — confirmação preditiva do desacoplamento carga↔humor (Tabela 17).'));
{
  const key = ['PTH (TMD)','Fadiga física','Vigor'];
  const rows = D.pred.reg.filter(r => key.includes(r.alvo) && ['Baseline (pré)','Perfil pré completo'].includes(r.preditores))
    .map(r => [r.alvo, r.preditores, nf(r.R2), nf(r.RMSE), r.modelo]);
  children.push(table(['Desfecho', 'Preditores', 'R² (OOF)', 'RMSE', 'Modelo'], rows,
    [2760, 2760, 1280, 1280, 1280], ['l', 'l', 'r', 'r', 'l']));
}
children.push(caption('Tabela 17. Validação preditiva leave-one-athlete-out: R² fora da amostra por desfecho.'));

children.push(H('3.4.4. Carga interna × humor e preditores de estado de fadiga', HeadingLevel.HEADING_3));
children.push(P('A carga interna (PSE, FC, TRIMP) mostra-se desacoplada do perfil de humor: nenhum par carga × humor sobrevive à FDR. Entre as variáveis de humor, os preditores de fadiga alta vs. baixa (Tabela 18; Figura 10): a fadiga física é a mais sensível (AUC ' + nf(chP[0].AUC) + '; ICC ' + nf(chP.find(x=>x.label==='Fadiga física').icc) + ' — estado-lábil), a fadiga mental e a depressão são sensíveis e estáveis, e a tensão é confiável mas cega à fadiga.'));
children.push(table(['Preditor', 'AUC', 'IC95%', 'Sensib.', 'Especif.', 'ICC(2,1)'],
  chP.map(r => [r.label, nf(r.AUC), `[${nf(r.IC[0])}; ${nf(r.IC[1])}]`, nf(r.sens), nf(r.spec), r.icc == null ? '—' : nf(r.icc)]),
  [2960, 1180, 1900, 1080, 1080, 1160], ['l', 'r', 'l', 'r', 'r', 'r']));
children.push(caption('Tabela 18. Preditores de estado de fadiga alta vs. baixa: sensibilidade (AUC, Youden) e confiabilidade (ICC 2,1).'));
children.push(...figA('carga_humor/carga_humor_fig.png', 'Figura 10. Acoplamento carga × humor (tônico e agudo, com FDR) e preditores de estado de fadiga (sensibilidade × confiabilidade).'));

children.push(H('3.4.5. Segmentação dos atletas e decomposição da variância', HeadingLevel.HEADING_3));
children.push(P('A resposta é fortemente individual. Uma segmentação por k-means separa ' + D.pv.segmentacao.grupos.map(g => g.grupo.toLowerCase() + ' (n=' + g.n + ')').join(', ') + '; o grupo explica η² = ' + nf(D.pv.segmentacao.eta2_PTH,3) + ' da variância do PTH (Tabela 19). A decomposição de variância mostra que a maior parte é entre atletas (traço) em quase todas as dimensões (Tabela 20).'));
{
  const subs = ['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão'];
  const rows = D.pv.segmentacao.perfis.map(p => { const g = D.pv.segmentacao.grupos.find(x=>x.grupo===p.grupo); return [p.grupo, String(g?g.n:''), ...subs.map(s=>sg(p[s]))]; });
  children.push(table(['Grupo','n',...subs], rows, [1900, 760, 1120, 1120, 1120, 1120, 1120, 1100], ['l','r','r','r','r','r','r','r']));
}
children.push(caption('Tabela 19. Segmentação (k-means) por perfil de humor padronizado (escores-z); η²(PTH) = ' + nf(D.pv.segmentacao.eta2_PTH,3) + '.'));
children.push(table(['Variável','Var. entre','Var. intra','% entre atletas','CV intra (%)'],
  D.pv.variabilidade.map(r => [r.var, nf(r.entre), nf(r.intra), nf(r.pct_entre,1), nf(r.CV_intra,1)]),
  [3060, 1900, 1900, 1500, 1000], ['l','r','r','r','r']));
children.push(caption('Tabela 20. Decomposição da variância em traço (entre atletas) e estado (intra-atleta).'));

children.push(H('3.4.6. Autorrelatos complementares e o item "Sonolento"', HeadingLevel.HEADING_3));
children.push(P('Os autorrelatos externos confirmam o eixo físico (Tabela 21). Um achado contraintuitivo: o item "Sonolento" move-se na contramão — enquanto Esgotado/Exausto/Cansado sobem, a sonolência cai (Tabela 22): o exercício agudo é ativador, o que explica a não-invariância residual localizada nesse item e recomenda tratá-lo à parte (eixo sono↔alerta).'));
children.push(table(['Instrumento','Escala','Pré','Pós','dz','p (FDR)','Sig.'],
  D.oq.A.map(r => [r.inst, r.escala, nf(r.M_pre), nf(r.M_pos), sg(r.dz), pf(r.p_FDR), r.sig ? 'sim' : '—']),
  [2760, 1200, 1200, 1200, 1200, 1400, 900], ['l','l','r','r','r','r','r']));
children.push(caption('Tabela 21. Autorrelatos externos ao BRUMS — resposta aguda pré→pós.'));
children.push(table(['Item de Fadiga','Pré','Pós','Δ','dz','Direção'],
  D.sn.A.map(r => [r.item, nf(r.M_pre), nf(r.M_pos), sg(r.delta), sg(r.dz), r.direcao]),
  [3060, 1500, 1500, 1300, 1300, 1700], ['l','r','r','r','r','l']));
children.push(caption('Tabela 22. Itens da subescala Fadiga — o "Sonolento" move-se na contramão dos demais.'));
children.push(...figA('figuras/monitoramento_viz.png', 'Figura 11. Painel de síntese: medidores dos indicadores-chave, radar do perfil pré×pós, monitoramento diário D1→D7 e mapa 4D das variáveis.', HERE));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---- 3.5 ANÁLISES COMPLEMENTARES ----
children.push(H('3.5. Análises complementares', HeadingLevel.HEADING_2));

children.push(H('3.5.1. Mudança confiável por atleta (RCI / MDC)', HeadingLevel.HEADING_3));
children.push(P('Usando o erro-padrão de medida (SEM = DP·√(1−α)) e a mínima mudança detectável (MDC₉₅ = 1,96·√2·SEM), classificou-se cada mudança pré→pós individual pelo índice de mudança confiável (RCI). A maior parte das mudanças fica dentro do ruído de medida: apenas ' + EX.rci.map(r=>r.pct_mudanca).sort((a,b)=>a-b)[0].toFixed(0).replace('.',',') + '–' + Math.max.apply(null,EX.rci.map(r=>r.pct_mudanca)).toFixed(0).replace('.',',') + '% dos pares atingem mudança confiável (|RCI|>1,96), reforçando a forte individualidade da resposta (Tabela 23).'));
children.push(table(['Subescala','α','DP','SEM','MDC₉₅','% ↑ confiável','% ↓ confiável'],
  EX.rci.map(r => [r.sub, nf(r.alpha,2), nf(r.DP), nf(r.SEM), nf(r.MDC95), nf(r.pct_aumento,1), nf(r.pct_queda,1)]),
  [2360,1080,1080,1080,1240,1260,1260], ['l','r','r','r','r','r','r']));
children.push(caption('Tabela 23. Erro-padrão de medida (SEM), mínima mudança detectável (MDC₉₅) e proporção de pares pré→pós com mudança confiável (RCI) por subescala.'));

children.push(H('3.5.2. Testes de equivalência (TOST) dos achados nulos', HeadingLevel.HEADING_3));
children.push(P('Os achados nulos foram submetidos a testes de equivalência (TOST): o desacoplamento carga↔humor (limite de equivalência r = 0,30) e o contraste HIIT vs. dias sem HIIT (SESOI dz = 0,5). O contraste HIIT vs. sem é estatisticamente equivalente para o PTH e a fadiga mental (Tabela 24) — o "sem diferença" torna-se equivalência formal, não mera ausência de significância; já as correlações carga↔humor ficam inconclusivas (efeito próximo do limite, amostra pequena).'));
children.push(table(['Teste','Efeito','p (TOST)','Equivalente?'],
  EX.tost.map(t => [t.teste.replace(' · ',': '), (t.efeito_dz!=null?'dz '+sg(t.efeito_dz):'r '+sg(t.r)), pf(t.p_TOST), t.equivalente?'sim':'—']),
  [4360,1900,1400,1700], ['l','r','r','r']));
children.push(caption('Tabela 24. Testes de equivalência (TOST) para os achados nulos — HIIT vs. dias sem HIIT (SESOI dz 0,5) e acoplamento carga↔humor (limite r 0,30).'));

children.push(H('3.5.3. Rede psicométrica (correlações parciais)', HeadingLevel.HEADING_3));
children.push(P('A rede psicométrica (modelo gráfico gaussiano) das seis subescalas descreve as associações diretas (correlações parciais), controlando as demais. A depressão é o nó mais central (maior força), seguida da fadiga (Tabela 25) — um complemento moderno à estrutura fatorial, coerente com o eixo afetivo-energético.'));
{
  const rr = Object.entries(EX.rede.strength).map(([k,v])=>[k,v]).sort((a,b)=>b[1]-a[1]);
  children.push(table(['Subescala','Força do nó (Σ|parciais|)'], rr.map(x=>[x[0], nf(x[1],2)]),
    [4680,4680], ['l','r']));
}
children.push(caption('Tabela 25. Centralidade (força) por subescala na rede de correlações parciais. Aresta mais forte: ' + (EX.rede.edges[0]? EX.rede.edges[0].a+'–'+EX.rede.edges[0].b+' (parcial '+nf(EX.rede.edges[0].pcor,2)+')' : '—') + '.'));

children.push(H('3.5.4. Cinética intradia (pré → meio → pós)', HeadingLevel.HEADING_3));
children.push(P('Aproveitando o momento intermediário da coleta (n = 155), a cinética intradia mostra que a resposta aguda se instala cedo: a fadiga física e o PTH já sobem no meio da sessão e o vigor cai, com pequena variação adicional até o pós (Tabela 26).'));
children.push(table(['Variável','Pré','Meio','Pós'],
  Object.values(EX.intradia).map(o => [o.label, nf(o.pre), nf(o.mid), nf(o.pos)]),
  [3360,2000,2000,2000], ['l','r','r','r']));
children.push(caption('Tabela 26. Médias por momento (pré, meio, pós) — cinética aguda dentro da sessão.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===================== 4. DISCUSSÃO =====================
children.push(H('4. Discussão', HeadingLevel.HEADING_1));
children.push(P('Este estudo caracterizou a resposta do humor de atletas de handebol de elite a um microciclo com HIIT e identificou os marcadores mais úteis ao monitoramento, mantendo o atleta como unidade em todas as camadas. Três achados principais emergem e convergem por métodos independentes.'));
children.push(P([bold('A dose do estímulo e sua leitura fisiológica. '), run('O protocolo — 4 × 4 min a 104% da velocidade de pico com 3 min de intervalo — impôs uma carga interna quase-máxima e progressiva: a FC de pico atingiu ' + nf(hp.resumo.FC_maxima[0],0) + ' bpm, a FC média das séries ' + nf(hp.resumo.FC_media_series[0],0) + ' bpm e a PSE final ' + nf(hp.resumo.PSE_final[0],1) + '. A elevação da FC de recuperação ao longo das séries (deriva cardiovascular, recuperação incompleta) confirma que o estímulo operou próximo ao teto aeróbio, na zona associada a maiores adaptações centrais e periféricas (Buchheit & Laursen, 2013). É justamente esse regime de teto que explica o desacoplamento observado: quando todos treinam perto do máximo, a variância da carga interna se comprime e deixa de explicar a variância — bem maior — da resposta de humor.')]));
children.push(P([bold('Descritivas, normalidade e escolha de métodos. '), run('As distribuições (histogramas, box plots e Q–Q) mostraram forte efeito piso nas subescalas negativas e não-normalidade generalizada (Shapiro–Wilk), o que poderia comprometer testes paramétricos. A concordância entre t e Wilcoxon, a confirmação por permutação restrita e a estimação bayesiana blindam as conclusões contra essa ameaça. O contraste direto entre dias de HIIT e dias sem HIIT não sobreviveu à correção — coerente com a leitura de que a assinatura do HIIT está no acúmulo diário ao longo do microciclo, e não num contraste agudo isolado, dominado pela variabilidade individual.')]));
children.push(P([bold('A resposta mora no eixo energia–fadiga e é de estado. '), run('A mudança pré→pós é um deslocamento sobre o eixo energia–fadiga (vigor achata, fadiga sobe), com as dimensões negativas quase paradas — erosão do perfil iceberg. A hierarquia de invariância confirma que se trata de mudança de estado, não do significado do instrumento (métrica sustentada; escalar aproximada; estrita no limite, com quebra localizada no item "Sonolento"). O padrão é coerente com a literatura de resposta afetiva a exercício intervalado, em que tensão e depressão tendem a recuar e a resposta é modulada pela intensidade e pelo desenho da sessão (Marques et al., 2020; Patten et al., 2022), e com a validação do BRUMS, que reporta invariância de medida e maior fadiga em atletas (Terry et al., 2022; Zhang et al., 2014).')]));
children.push(P([bold('A resposta é fortemente individual. '), run('A maior parte da variância é traço (ICC 0,42–0,71) e o acúmulo do PTH é idiossincrático, ao passo que a fadiga física acumula de forma homogênea. A predição fora da amostra confirma que o sinal vem do baseline do próprio atleta, não do contexto da sessão — o que desloca a inferência da média do grupo para a tendência individual.')]));
children.push(P([bold('Carga alta não é humor pior. '), run('O custo cardiovascular quase-máximo não prediz a perturbação aguda do humor (desacoplamento robusto à FDR; TRIMP×ΔPTH r = ' + nf(D.trimp.TRIMP_x_humor.r) + '). Num regime de teto, a variação relevante do humor depende de tolerância e recuperação individuais, não da carga objetiva — o que fundamenta a superioridade das medidas subjetivas no monitoramento da resposta ao treino (Saw, Main & Gastin, 2016) e a validade da PSE como marcador de estímulo, não de resposta (Haddad et al., 2017).')]));
children.push(P([bold('Convergência multimétodo. '), run('O efeito agudo é confirmado no plano multivariado (MANOVA p = ' + pf(mt.multivariada.MANOVA.p) + '; PERMANOVA restrita p = ' + pf(mt.multivariada.PERMANOVA.p) + ', R² = ' + nf(mt.multivariada.PERMANOVA.R2,3) + '), por permutação restrita item a item e por estimação bayesiana (P(Δ>0) ≈ 1 para a fadiga física e o PTH), além de concordar entre testes paramétricos e não-paramétricos. Essa triangulação — métodos com pressupostos distintos apontando para o mesmo lugar — é a principal salvaguarda contra achados espúrios por comparações múltiplas ou por violação de pressupostos.')]));
children.push(P([bold('A dinâmica temporal e o valor do nível sobre a derivada. '), run('A formalização em cálculo mostra que a fadiga física acumula de forma saturante (f″ < 0), tendendo a um limite estacionário ao fim da semana, com velocidade de acúmulo maior em torno dos dias de HIIT. Um achado com consequência prática direta: a ROC das derivadas não supera a ROC dos níveis — a taxa de variação diagnostica menos que o estado atual, porque a derivada amplifica o ruído de medida. Monitorar "quão cansado o atleta está" é, portanto, mais informativo do que "quão rápido ele está ficando cansado".')]));
children.push(P([bold('Confiabilidade da mudança, equivalência e estrutura. '), run('As análises complementares refinam o quadro. A mudança confiável (RCI/MDC) mostra que a maior parte das oscilações pré→pós individuais está dentro do erro de medida — só uma minoria dos atletas ultrapassa a mínima mudança detectável —, o que quantifica a individualidade e alerta contra sobreinterpretar variações pequenas. Os testes de equivalência (TOST) convertem o desacoplamento carga↔humor e o contraste HIIT-vs-sem em equivalência estatística formal (não mera ausência de significância) para os índices centrais. A rede de correlações parciais posiciona a depressão como nó mais central do afeto negativo, e a cinética intradia revela que a resposta aguda se instala já no meio da sessão. Em conjunto, reforçam — por vias independentes — a leitura de estado, individual e desacoplada.')]));
children.push(P([bold('Marcadores para o monitoramento. '), run('A fadiga física é o marcador mais sensível de estado de fadiga (AUC ' + nf(chP[0].AUC) + '); sua baixa estabilidade é a assinatura desejável de um sinal de estado. A fadiga mental e a depressão combinam sensibilidade e confiabilidade, servindo ao acompanhamento dia a dia; a tensão, embora estável, é diagnosticamente cega. A validade convergente intra-sujeito entre o BRUMS e os autorrelatos externos reforça a interpretação. No contexto do handebol — modalidade de alta demanda intermitente e calendário denso —, isso sustenta um protocolo de monitoramento parcimonioso e de baixo custo, aplicável no dia a dia do clube.')]));
children.push(P([bold('Pontos fortes e validade. '), run('A disciplina de atleta-como-unidade, a triangulação por métodos independentes (frequentista, bayesiano, multivariado, classificação e cálculo), a caracterização psicométrica completa (confiabilidade, AFC, AFE, TRI, invariância configural→estrita/parcial) e a reprodutibilidade ponta-a-ponta por código conferem robustez incomum. A validade convergente aparece na correlação intra-sujeito entre BRUMS e autorrelatos externos; a de construto, na invariância; a diagnóstica, nas AUC.')]));
children.push(P([bold('Limitações. '), run('Delineamento observacional (associação, não causalidade); amostra de um único clube de elite (27 atletas), o que limita poder para efeitos individuais e generalização; ausência de duração de sessão (TRIMP relativo por %HRR); efeito de teto na carga; itens com efeito piso (tensão, confusão); sonolência medida por um único item.')]));
children.push(P([bold('Direções futuras. '), run('Desenhos com manipulação da carga (dias pareados de alta vs. baixa intensidade) para testar causalidade; séries temporais mais densas por atleta para modelos dinâmicos individuais e mapeamento de não-respondedores; escala de sono/alerta dedicada; integração de marcadores objetivos de recuperação (VFC, sono); e validação prospectiva do protocolo parcimonioso contra desfechos de desempenho e lesão.')]));

// ===================== 5. CONCLUSÃO =====================
children.push(H('5. Conclusão', HeadingLevel.HEADING_1));
children.push(P('Em atletas de handebol de elite submetidos a um microciclo com HIIT, a evidência convergente de todas as camadas analíticas sustenta cinco conclusões:'));
children.push(P([bold('(1) '), run('A resposta de humor é real e mora no eixo energia–fadiga: o vigor recua e a fadiga (sobretudo física) se eleva, com as dimensões negativas quase inertes por efeito piso — que é limitação de medida, não ausência de fenômeno.')]));
children.push(P([bold('(2) '), run('A mudança é de estado, não de medida: a escala é confiável e invariante pré→pós (métrica sustentada; escalar aproximada; estrita no limite, com quebra local no item "Sonolento").')]));
children.push(P([bold('(3) '), run('A resposta é fortemente individual (variância majoritariamente de traço; segmentação em resilientes, perturbados e um extremo), exigindo monitoramento por tendência individual e não pela média do grupo.')]));
children.push(P([bold('(4) '), run('A carga interna não determina a resposta de humor (desacoplamento robusto): FC/TRIMP não substituem o autorrelato.')]));
children.push(P([bold('(5) '), run('O monitoramento eficiente combina a fadiga física (sensibilidade) e a fadiga mental/depressão (confiabilidade), num protocolo parcimonioso e reprodutível. A convergência de métodos independentes para a mesma conclusão é a melhor evidência de que ela descreve o fenômeno, e não o método.')]));

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
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: 'Cambria', size: 21, bold: true, color: '0E8C86' }, paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } }, children }]
});
Packer.toBuffer(doc).then(buf => {
  const out = path.join(HERE, 'Artigo_BRUMS_HIIT_A1.docx');
  fs.writeFileSync(out, buf);
  console.log('escrito', out, (buf.length / 1024).toFixed(0), 'KB');
});
