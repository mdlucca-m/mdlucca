/* Testes do app hospedado: motor + tela, num Chromium emulando iPhone 13.
   Sem banco (claude.use ausente) => modo "neste aparelho", que é o pior caso
   para a tela e o melhor para testar a lógica sem rede. */
const { chromium, devices } = require("playwright");
const http = require("http");
const fs = require("fs");
const path = require("path");

const ARQ = "/home/user/mdlucca/docs/app.html";
const PORTA = 8931;
let falhas = 0, passes = 0;

function ok(cond, nome, extra) {
  if (cond) { passes++; }
  else { falhas++; console.log("  ✗ " + nome + (extra ? "  →  " + extra : "")); }
}
function perto(a, b, tol, nome) {
  const d = Math.abs(a - b);
  ok(d <= tol, nome, `esperado ${b} ± ${tol}, veio ${a}`);
}

/* O mesmo esqueleto que o publicador embrulha em volta da página — copiado da
   leitura do artifact publicado. Servir o arquivo cru mentiria: sem a meta de
   viewport o Chromium usa 980px de largura e nenhum defeito de celular aparece. */
const ESQUELETO_ABRE = `<!doctype html><html><head><meta charset=utf8>` +
  `<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">` +
  `<style>:root{color-scheme:light;box-sizing:border-box;` +
  `padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}` +
  `html{scroll-padding-top:env(safe-area-inset-top,0px)}` +
  `body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;` +
  `background:#faf9f5;color:#141413}img{max-width:100%}` +
  `[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>\n`;
const ESQUELETO_FECHA = `\n</body></html>`;

const servidor = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(ESQUELETO_ABRE + fs.readFileSync(ARQ, "utf8") + ESQUELETO_FECHA);
});

(async () => {
  await new Promise(r => servidor.listen(PORTA, r));
  const navegador = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const ctx = await navegador.newContext(Object.assign({}, devices["iPhone 13"]));
  const pag = await ctx.newPage();

  const erros = [];
  pag.on("console", m => { if (m.type() === "error") erros.push(m.text()); });
  pag.on("pageerror", e => erros.push("pageerror: " + e.message));

  await pag.goto(`http://127.0.0.1:${PORTA}/`, { waitUntil: "load" });
  await pag.waitForTimeout(400);

  console.log("\n── Motor ──────────────────────────────────────────────");

  const m = await pag.evaluate(() => {
    const R = {};
    // "30 s" é permanência, não 30 repetições
    R.seg30s = segundosDeTrabalho("30 s");
    R.seg30seg = segundosDeTrabalho("30 segundos");
    R.seg8lado = segundosDeTrabalho("8 cada lado");
    R.seg3 = segundosDeTrabalho("3");
    R.segVazio = segundosDeTrabalho("");

    // Spearman sem empates: r = 1 - 6Σd²/(n(n²-1)); a=1..7, b troca dois pares
    const a = [1,2,3,4,5,6,7], b = [1,3,2,4,5,7,6];   // Σd² = 4
    R.sp = spearman(a, b);
    R.spCurto = spearman([1,2,3,4,5], [1,2,3,4,5]);   // < 6 pares → null

    // Postos com empate recebem a média
    R.postos = postos([10, 20, 20, 30]);

    // Desvio amostral (n−1)
    R.desvio = desvio([2, 4, 4, 4, 5, 5, 7, 9]);
    R.desvio1 = desvio([5]);

    // Quartis: menos de 5 pontos não é faixa
    R.q4 = quartis([1,2,3,4]);
    R.q5 = quartis([1,2,3,4,5]);

    // Monotonia indefinida com carga idêntica todo dia
    const iguais = [];
    for (let i = 0; i < 7; i++) iguais.push({ data: maisDias("2026-09-20", -i), carga_ua: 300 });
    R.cargaIgual = carga(iguais, "2026-09-20");

    // Carga com variação
    const varia = [
      { data: "2026-09-14", carga_ua: 400 }, { data: "2026-09-16", carga_ua: 600 },
      { data: "2026-09-18", carga_ua: 300 }, { data: "2026-09-20", carga_ua: 500 },
    ];
    R.cargaVaria = carga(varia, "2026-09-20");

    // Zona do ACWR só existe com 21 dias de histórico
    R.zonaCurta = zonaACWR(1.1, 10);
    R.zonaIdeal = zonaACWR(1.1, 30);
    R.zonaRisco = zonaACWR(1.7, 30);
    R.zonaSub = zonaACWR(0.5, 30);

    // Z móvel: a janela NÃO inclui o próprio ponto
    const datas = [], vals = [];
    for (let i = 0; i < 8; i++) { datas.push(maisDias("2026-09-01", i)); vals.push(10 + (i % 3)); }
    vals[7] = 40;                                     // salto no último
    R.zs = zMovel(datas, vals, 30, 5);

    // Geração do sistema: contatos por semana contra o alvo do bloco
    const bl = BLOCOS_PADRAO;
    const g = gerarSistema(bl, "2026-09-21", 1, 8, []);
    const porSem = {};
    for (const s of g.sessoes) {
      const sem = semanaDe(s.data, "2026-09-21");
      const p = planoSessao(s.exercicios, s.tipo, s.dur_prev);
      porSem[sem] = porSem[sem] || { contatos: 0, n: 0, min: 0, series: 0 };
      porSem[sem].contatos += p.contatos;
      porSem[sem].min += p.dur;
      porSem[sem].series += p.series;
      porSem[sem].n++;
    }
    R.semanas = Object.keys(porSem).map(k => ({
      sem: +k, contatos: porSem[k].contatos, alvo: bl[(+k - 1) % bl.length].plio,
      n: porSem[k].n, min: porSem[k].min,
    }));
    R.totalSessoes = g.sessoes.length;

    // Regerar não sobrescreve dia ocupado
    const g2 = gerarSistema(bl, "2026-09-21", 1, 1, ["2026-09-21"]);
    R.pulados = g2.pulados.length;
    R.geradas2 = g2.sessoes.length;

    // Toda sessão abre com mobilidade das três articulações
    const prim = g.sessoes[0].exercicios;
    R.primMob = prim.filter(e => e.grupo === "Mobilidade").map(e => e.nome);
    R.primEdu = prim.filter(e => e.grupo === "Educativo").length;
    R.mobAntesDaBarra = prim.findIndex(e => e.grupo === "LPO" || e.pct_rm) >
                        prim.map(e => e.grupo).lastIndexOf("Mobilidade");

    // A semana de reteste não perde contatos: a B carrega a semana inteira
    const sem8 = g.sessoes.filter(s => semanaDe(s.data, "2026-09-21") === 8);
    R.reteste = sem8.map(s => ({ tipo: s.tipo, obj: s.objetivo,
      contatos: planoSessao(s.exercicios, s.tipo).contatos }));

    // Mobilidade e educativo não somam contato nem tonelagem
    R.planoMob = planoSessao(blocoMobilidade("A"), "Mobilidade");

    // Ficha do WhatsApp
    const ficha = [
      "🏐 CADASTRO ELASE VOLEIBOL", "",
      "1. Nome completo — João da Silva Pereira",
      "2. Como prefere ser chamado — Joca",
      "3. Data de nascimento — 14/03/2001",
      "4. Posição — ponta",
      "5. Número da camisa — 12",
      "6. Telefone (WhatsApp) — (41) 99999-0000",
      "7. Estatura em cm — 198,5",
      "8. Massa corporal em kg — 92",
      "9. Anos de prática no voleibol — 11",
      "10. Mão dominante — destro",
      "11. Perna de impulsão — ",
      "12. Contato de emergência — Maria (41) 98888-0000",
      "13. Lesões anteriores ou limitações — ombro direito 2024",
      "14. Algo mais que a comissão deva saber — ",
      "15. Escolaridade — superior em andamento",
    ].join("\n");
    R.wa = lerWA(ficha);

    // Ficha com valor ilegível: fica em branco E é reportado, nunca chutado
    R.waRuim = lerWA("1. Nome completo — Pedro\n7. Estatura em cm — alto\n3. Data de nascimento — ontem");

    // Duas fichas coladas juntas
    R.waDuas = lerVariasWA(ficha + "\n" + ficha.replace("João da Silva Pereira", "Outro Atleta")).length;

    // Prontidão: componente ausente é EXCLUÍDO, não vira zero
    const semNada = prontidao([], { w: {}, b: {} }, "2026-09-20");
    R.prSemNada = { valor: semNada.valor, comps: Object.keys(semNada.componentes) };
    const soDor = prontidao([], { w: { "2026-09-20": { dor: 0 } }, b: {} }, "2026-09-20");
    R.prSoDor = { valor: soDor.valor, comps: Object.keys(soDor.componentes) };

    // Bandeira crítica quando a carga é idêntica todos os dias
    const prIgual = prontidao(iguais, { w: {}, b: {} }, "2026-09-20");
    R.prIgual = prIgual.bandeiras.map(b => b[1]);

    // BRUMS: TMD = negativas − Vigor + 100
    const vals24 = new Array(24).fill(0);
    BRUMS_LISTA.forEach((x, i) => { if (x[1] === "Vigor") vals24[i] = 4; });
    const pd = brumsPorData({ b: { "2026-09-20|pre": vals24 } }, "pre");
    R.tmd = pd["2026-09-20"].TMD;             // 0 − 16 + 100 = 84
    R.vigor = pd["2026-09-20"].Vigor;

    // Z do humor exige 6 coletas COM variação
    const diario = { w: {}, b: {} };
    for (let i = 0; i < 5; i++) {
      const v = new Array(24).fill(1);
      diario.b[maisDias("2026-09-01", i) + "|pre"] = v;
    }
    R.zPoucas = zHoje(diario).map(z => z.z);

    return R;
  });

  ok(m.seg30s === 30, "'30 s' conta como 30 segundos", m.seg30s);
  ok(m.seg30seg === 30, "'30 segundos' também", m.seg30seg);
  ok(m.seg8lado === 32, "'8 cada lado' = 8 reps × 4 s", m.seg8lado);
  ok(m.seg3 === 12, "'3' = 3 reps × 4 s", m.seg3);
  ok(m.segVazio === 24, "sem número cai no padrão de 6 reps", m.segVazio);

  perto(m.sp.r, 0.9286, 0.001, "Spearman sem empates bate a fórmula");
  ok(m.sp.n === 7, "Spearman conta os pares", m.sp.n);
  ok(m.spCurto === null, "menos de 6 pares não conclui nada");
  ok(JSON.stringify(m.postos) === "[1,2.5,2.5,4]", "empate recebe o posto médio", JSON.stringify(m.postos));
  perto(m.desvio, 2.13809, 0.0001, "desvio é amostral (n−1)");
  ok(m.desvio1 === 0, "com n<2 não existe desvio");
  ok(m.q4 === null, "menos de 5 pontos não é faixa");
  ok(m.q5 && m.q5.mediana === 3, "quartis com 5 pontos", JSON.stringify(m.q5));

  ok(m.cargaIgual.monotonia === null, "carga idêntica → monotonia INDEFINIDA, não zero",
     String(m.cargaIgual.monotonia));
  ok(m.cargaIgual.monotonia_indefinida === true, "a tela é avisada da indefinição");
  ok(m.cargaIgual.strain === null, "sem monotonia não há strain");
  ok(m.cargaIgual.semanal === 2100, "semanal soma os 7 dias", m.cargaIgual.semanal);
  ok(m.cargaVaria.monotonia > 0, "com variação a monotonia existe", m.cargaVaria.monotonia);
  perto(m.cargaVaria.aguda, 1800, 0.01, "aguda = 7 dias");
  perto(m.cargaVaria.cronica, 450, 0.01, "crônica = 28 dias ÷ 4");
  perto(m.cargaVaria.acwr, 4, 0.01, "ACWR = aguda ÷ crônica");

  ok(m.zonaCurta.t === "Histórico curto", "abaixo de 21 dias não há zona", m.zonaCurta.t);
  ok(m.zonaIdeal.c === "good", "1,10 é zona ideal");
  ok(m.zonaRisco.c === "crit", "1,70 é risco elevado");
  ok(m.zonaSub.c === "info", "0,50 é subcarga");

  ok(m.zs.slice(0, 5).every(z => z === null), "sem base mínima não sai Z");
  ok(m.zs[7] !== null && m.zs[7] > 3, "o salto do último dia aparece como Z alto", m.zs[7]);

  console.log("\n── Periodização ───────────────────────────────────────");
  ok(m.totalSessoes === 24, "8 semanas × 3 sessões", m.totalSessoes);
  for (const s of m.semanas) {
    const erro = Math.abs(s.contatos - s.alvo) / s.alvo;
    ok(erro <= 0.16, `semana ${s.sem}: contatos perto do alvo`,
       `${s.contatos} vs alvo ${s.alvo} (${(erro * 100).toFixed(0)}%)`);
    ok(s.min >= 45 && s.min <= 420, `semana ${s.sem}: duração semanal plausível`, s.min + " min");
  }
  ok(m.pulados === 1 && m.geradas2 === 2, "dia ocupado é PULADO, nunca sobrescrito",
     `pulados ${m.pulados}, geradas ${m.geradas2}`);
  ok(m.primMob.length === 4, "toda sessão abre com 4 mobilizações", m.primMob.length);
  ok(m.primMob.join(" ").match(/tornozelo/i) && m.primMob.join(" ").match(/quadril/i)
     && m.primMob.join(" ").match(/bastão|torácica/i),
     "tornozelo, quadril e ombro/torácica na mesma sessão", m.primMob.join(" · "));
  ok(m.primEdu === 4, "na acumulação o educativo é treino (4 exercícios)", m.primEdu);
  ok(m.mobAntesDaBarra === true, "mobilidade e educativo vêm ANTES da barra");
  const cRet = m.reteste.find(r => /Reteste/.test(r.obj));
  ok(!!cRet, "a semana 8 tem reteste");
  ok(m.reteste.reduce((a, r) => a + r.contatos, 0) >= 60,
     "a semana de reteste não perde os contatos do bloco",
     m.reteste.map(r => r.contatos).join("+"));
  ok(m.planoMob.contatos === 0, "mobilidade não gera contato pliométrico", m.planoMob.contatos);
  ok(m.planoMob.dur > 0 && m.planoMob.dur < 20, "mas entra na duração", m.planoMob.dur + " min");

  console.log("\n── Ficha do WhatsApp ──────────────────────────────────");
  ok(m.wa.dados.nome === "João da Silva Pereira", "nome", m.wa.dados.nome);
  ok(m.wa.dados.nasc === "2001-03-14", "data vira aaaa-mm-dd", m.wa.dados.nasc);
  ok(m.wa.dados.posicao === "Ponteiro (Ponta)", "'ponta' casa com Ponteiro (Ponta)", m.wa.dados.posicao);
  ok(m.wa.dados.estatura === 198.5, "vírgula decimal preservada", m.wa.dados.estatura);
  ok(m.wa.dados.dominancia === "Destro", "'destro' casa", m.wa.dados.dominancia);
  ok(m.wa.dados.perna_impulsao === "", "campo vazio fica vazio");
  ok(m.wa.faltam.length === 0, "nada obrigatório faltando", JSON.stringify(m.wa.faltam));
  ok(m.waRuim.dados.estatura === null, "'alto' NÃO vira número");
  ok(m.waRuim.naoLidos.length === 2, "o que não deu para ler é reportado",
     JSON.stringify(m.waRuim.naoLidos));
  ok(m.waRuim.faltam.length > 0, "e o obrigatório que sumiu é cobrado");
  ok(m.waDuas === 2, "duas fichas coladas juntas são separadas", m.waDuas);

  console.log("\n── Prontidão e humor ──────────────────────────────────");
  ok(m.prSemNada.comps.length === 1 && m.prSemNada.comps[0] === "carga",
     "sem coleta só a carga entra", JSON.stringify(m.prSemNada.comps));
  ok(m.prSoDor.valor === 100, "dor 0 + carga sem histórico = 100, não diluído por zeros",
     m.prSoDor.valor);
  ok(m.prIgual.indexOf("crit") >= 0, "carga idêntica levanta bandeira crítica",
     JSON.stringify(m.prIgual));
  ok(m.tmd === 84, "TMD = negativas − Vigor + 100", m.tmd);
  ok(m.vigor === 16, "Vigor soma os 4 itens", m.vigor);
  ok(m.zPoucas.every(z => z === null), "5 coletas ainda não dão Z");

  console.log("\n── Tela ───────────────────────────────────────────────");

  // Nenhum campo de dinheiro em lugar nenhum
  const textoTodo = await pag.evaluate(() => document.documentElement.innerHTML.toLowerCase());
  ok(!/sal[áa]rio|renda|remunera|pagamento|mensalidade/.test(textoTodo),
     "nenhum campo de dinheiro na página inteira");

  ok(erros.length === 0, "nenhum erro de console no arranque", erros.join(" | "));

  // Abas públicas presentes, abas da comissão escondidas
  const abas = await pag.$$eval("#navRolo button", bs => bs.map(b => b.textContent.trim()));
  ok(abas.includes("Início") && abas.includes("Sessão") && abas.includes("Análise"),
     "abas públicas visíveis", abas.join(" · "));
  ok(!abas.includes("Prescrição") && !abas.includes("Elenco"),
     "abas da comissão escondidas antes do PIN", abas.join(" · "));
  ok(abas.some(a => /Comissão/.test(a)), "há porta para a comissão");

  // Entrar com o PIN
  await pag.click('#navRolo button[data-aba="__pin"]');
  await pag.fill("#pinCampo", "9999");
  await pag.click("#btPin");
  ok(await pag.isVisible("#avPin"), "PIN errado é recusado");
  await pag.fill("#pinCampo", "1234");
  await pag.click("#btPin");
  await pag.waitForTimeout(250);
  const abas2 = await pag.$$eval("#navRolo button", bs => bs.map(b => b.textContent.trim()));
  ok(abas2.includes("Prescrição") && abas2.includes("Sistema"),
     "com o PIN as abas da comissão aparecem", abas2.join(" · "));

  // Cadastrar um atleta pela ficha do WhatsApp
  await pag.click('#navRolo button[data-aba="whatsapp"]');
  await pag.fill("#waTexto", [
    "1. Nome completo — Rafael Moreira", "2. Como prefere ser chamado — Rafa",
    "3. Data de nascimento — 02/05/1999", "4. Posição — central",
    "5. Número da camisa — 7", "7. Estatura em cm — 201",
    "8. Massa corporal em kg — 95", "9. Anos de prática no voleibol — 12",
    "12. Contato de emergência — Ana (41) 97777-0000",
  ].join("\n"));
  await pag.click("#btLerWA");
  await pag.waitForTimeout(200);
  ok(await pag.isVisible('[data-import="0"]'), "a ficha lida vira um cartão");
  /* O valor lido não pode estar fora do quadro: uma tabela que rola esconde a
     coluna do número, e quem confere a ficha vê só os rótulos. */
  const valoresCortados = await pag.$$eval(".rolagem.estreita td.num", tds =>
    tds.filter(td => {
      const caixa = td.getBoundingClientRect();
      const pai = td.closest(".rolagem").getBoundingClientRect();
      return caixa.right > pai.right + 1;
    }).map(td => td.textContent.trim()));
  ok(valoresCortados.length === 0, "nenhum valor da ficha fica fora do quadro",
     valoresCortados.slice(0, 5).join(" | "));
  await pag.click('[data-import="0"]');
  await pag.waitForTimeout(300);

  // Gerar as semanas
  await pag.click('#navRolo button[data-aba="sistema"]');
  await pag.waitForTimeout(200);
  await pag.fill("#sisDe", "1");
  await pag.fill("#sisAte", "2");
  await pag.waitForTimeout(150);
  await pag.click("#btGerar");
  await pag.waitForTimeout(1400);
  const diag = await pag.evaluate(() => ({
    n: prescricoes().length, datas: prescricoes().map(p => p.data),
    de: UI.sisDe, ate: UI.sisAte, macro: cfg().macro_inicio,
  }));
  ok(diag.n === 6, "2 semanas geram 6 sessões", JSON.stringify(diag));

  /* Regressão do toque perdido: digitar num campo e tocar NO PRIMEIRO TOQUE
     num botão tem de valer. O `change` do campo dispara no blur, ou seja no
     instante do toque; se a tela for redesenhada ali, o clique não nasce. */
  await pag.fill("#sisAte", "4");                // digita, e tudo que vem depois
  await pag.tap("#btGerar");                     // é UM toque só, de verdade
  await pag.waitForTimeout(1400);
  const depoisDoToque = await pag.evaluate(() => prescricoes().length);
  ok(depoisDoToque === 12, "o primeiro toque depois de digitar num campo vale",
     `${depoisDoToque} sessões (esperado 12: semanas 1 a 4)`);

  /* O início do macrociclo é encaixado na segunda-feira: os dias de treino são
     contados a partir dele (0, 2, 4), e começar numa quarta jogaria o treino
     para quarta, sexta e domingo sem ninguém pedir. */
  await pag.click('#navRolo button[data-aba="ajustes"]');
  await pag.waitForTimeout(200);
  const hoje = await pag.evaluate(() => hojeISO());
  await pag.fill("#cfMacro", hoje);
  await pag.click("#btCfg");
  await pag.waitForTimeout(600);
  const macroGravado = await pag.evaluate(() => cfg().macro_inicio);
  const ehSegunda = await pag.evaluate(m => new Date(m + "T00:00:00").getDay() === 1, macroGravado);
  ok(ehSegunda, "o início do macrociclo é encaixado numa segunda-feira", macroGravado);
  await pag.waitForTimeout(1200);

  // Semear a sessão de hoje com o próprio gerador, para poder treiná-la
  await pag.evaluate(async () => {
    const s = gerarSistema(blocos(), hojeISO(), 1, 1, []).sessoes[0];
    await Store.set("prescricoes", hojeISO(), {
      data: hojeISO(), hora: s.hora, tipo: s.tipo, objetivo: s.objetivo,
      bloco: s.bloco, notas: s.notas, exercicios: s.exercicios });
  });
  await pag.waitForTimeout(300);
  const temHoje = await pag.evaluate(() => !!prescDoDia(hojeISO()));
  ok(temHoje, "há sessão prescrita para hoje");

  // A sessão: check-in, séries, check-out
  await pag.click('#navRolo button[data-aba="sessao"]');
  await pag.waitForTimeout(250);
  ok(await pag.isVisible("#btCheckin"), "a sessão de hoje abre com check-in");
  const exVisiveis = await pag.$$eval(".ex", e => e.length);
  ok(exVisiveis > 8, "os exercícios aparecem antes do check-in", exVisiveis);
  const temDica = await pag.$$eval(".ex .dica", e => e.length);
  ok(temDica > 0, "a instrução técnica aparece junto do exercício", temDica);

  await pag.click("#btCheckin");
  await pag.waitForTimeout(400);
  const ticks = await pag.$$(".tick");
  ok(ticks.length > 0, "depois do check-in aparecem as séries", ticks.length);

  /* Campo extra aparece só onde a prescrição pediu. Hoje é sessão A, de força:
     tem RIR prescrito em acessório, e não tem velocidade de barra. */
  const extras = await pag.evaluate(() => ({
    rir: document.querySelectorAll('[data-campo="rir"]').length,
    vel: document.querySelectorAll('[data-campo="vel"]').length,
  }));
  ok(extras.rir > 0, "a sessão de força pede RIR onde prescreveu RIR", extras.rir);
  ok(extras.vel === 0, "e não pede velocidade onde não prescreveu", extras.vel);

  /* Preenche o RIR da MESMA série que já foi marcada acima — tocar no ✓ de novo
     a desmarcaria, e a tonelagem cairia para zero. */
  const campoRir = await pag.$('[data-campo="rir"]');
  const chaveRir = await campoRir.getAttribute("data-serie");
  await campoRir.fill("2");
  await pag.click("#fechamento");           // tira o foco: o change dispara no blur
  await pag.waitForTimeout(400);
  const serieComRir = await pag.evaluate(c => {
    const a = meuAtleta(); return sessaoDe(a.id, hojeISO()).series[c];
  }, chaveRir);
  ok(serieComRir && serieComRir.rir === 2, "o RIR é gravado na série",
     JSON.stringify(serieComRir));
  ok(!("vel" in serieComRir),
     "e a velocidade não vira campo vazio no banco", JSON.stringify(serieComRir));

  // Preencher a primeira série com carga real de um exercício com barra
  const campos = await pag.$$('input[data-campo="carga"]');
  if (campos.length) {
    await campos[0].fill("100");
    const reps = await pag.$$('input[data-campo="reps"]');
    await reps[0].fill("5");
    const chave = await campos[0].getAttribute("data-serie");
    await pag.click(`[data-tick="${chave}"]`);
    await pag.waitForTimeout(300);
  }

  // Encerrar sem PSE é recusado
  await pag.evaluate(() => document.getElementById("fechamento").scrollIntoView());
  const btFechar = await pag.$("#btFechar");
  ok(await btFechar.isDisabled(), "sem PSE o botão de encerrar fica travado");
  await pag.click('[data-pse="7"]');
  await pag.waitForTimeout(120);
  ok(!(await btFechar.isDisabled()), "com PSE escolhida o botão libera");

  // Duração absurda é recusada — é o check-out esquecido
  await pag.fill("#durFim", "480");
  await pag.click("#btFechar");
  await pag.waitForTimeout(250);
  ok(await pag.isVisible("#avFechar"), "duração acima do teto é recusada");
  const aindaAberta = await pag.evaluate(() => {
    const a = meuAtleta(); return !sessaoDe(a.id, hojeISO()).check_out;
  });
  ok(aindaAberta, "e a sessão continua aberta");

  await pag.fill("#durFim", "75");
  await pag.click("#btFechar");
  await pag.waitForTimeout(600);

  const s = await pag.evaluate(() => {
    const a = meuAtleta(); return sessaoDe(a.id, hojeISO());
  });
  ok(!!s.check_out, "o check-out grava");
  ok(s.dur_min === 75 && s.pse === 7, "duração e PSA gravadas", `${s.dur_min} min, PSE ${s.pse}`);
  ok(s.carga_ua === 525, "carga = duração × PSE", s.carga_ua);
  ok(s.tonelagem === 500, "tonelagem = carga × reps das séries feitas", s.tonelagem);

  // Bem-estar e BRUMS
  await pag.click('#navRolo button[data-aba="bemestar"]');
  await pag.waitForTimeout(250);
  await pag.click('[data-escala="sq"] [data-v="4"]');
  await pag.fill("#wSh", "7,5");
  await pag.click('[data-escala="dor"] [data-v="3"]');
  await pag.click('[data-escala="es"] [data-v="2"]');
  await pag.click('[data-escala="kss"] [data-v="3"]');
  await pag.click("#btWell");
  await pag.waitForTimeout(400);
  const w = await pag.evaluate(() => {
    const a = meuAtleta(); return diarioDe(a.id).w[hojeISO()];
  });
  ok(w && w.sq === 4 && w.dor === 3 && w.kss === 3 && w.sh === 7.5,
     "check-in de bem-estar grava tudo", JSON.stringify(w));

  // BRUMS incompleta é recusada
  await pag.click('[data-brums="0"] [data-v="1"]');
  await pag.click("#btBrums");
  await pag.waitForTimeout(250);
  ok(await pag.isVisible("#avBrums"), "BRUMS com item faltando é recusada");
  await pag.evaluate(() => {
    for (let i = 0; i < 24; i++) {
      const b = document.querySelector(`[data-brums="${i}"] [data-v="2"]`);
      b.click();
    }
  });
  await pag.click("#btBrums");
  await pag.waitForTimeout(500);
  const temBrums = await pag.evaluate(() => {
    const a = meuAtleta(); return !!diarioDe(a.id).b[hojeISO() + "|pre"];
  });
  ok(temBrums, "BRUMS inteira grava");

  // Análise
  await pag.click('#navRolo button[data-aba="analise"]');
  await pag.waitForTimeout(400);
  const txtAnalise = await pag.innerText("#s-analise");
  ok(/Hist[óo]rico curto|—/.test(txtAnalise),
     "com 1 sessão o ACWR não finge diagnóstico");
  ok(/Spearman|6 dias/.test(txtAnalise), "a recusa da correlação é explicada");
  ok(/exclu[íi]do/i.test(txtAnalise), "a regra do componente ausente está na tela");
  const temGrafico = await pag.$$eval("#s-analise svg", e => e.length);
  ok(temGrafico >= 1, "o gráfico de carga desenha", temGrafico);
  const comps = await pag.$$eval(".pares div", ds => ds.map(d => d.textContent.trim()));
  ok(comps.length === 5, "os 5 componentes da prontidão aparecem", comps.length);
  ok(comps.every(t => /\d/.test(t.replace(/peso \d+%/, "")) || /sem coleta/.test(t)),
     "cada componente mostra o valor ou diz que não houve coleta", JSON.stringify(comps));
  const compsCortados = await pag.$$eval(".pares b", bs =>
    bs.filter(b => b.getBoundingClientRect().right >
                   b.closest(".cartao").getBoundingClientRect().right).length);
  ok(compsCortados === 0, "nenhum valor de componente fica fora do cartão", compsCortados);
  // O rótulo direto do gráfico tem de caber dentro do desenho
  const rotuloFora = await pag.$$eval("#s-analise svg text.valor", ts =>
    ts.filter(t => {
      const c = t.getBoundingClientRect(), s = t.closest("svg").getBoundingClientRect();
      return c.left < s.left - 1 || c.right > s.right + 1 || c.top < s.top - 1;
    }).length);
  ok(rotuloFora === 0, "o rótulo do gráfico fica dentro do desenho", rotuloFora);

  // Testes / 1RM, e o percentual virando quilo na sessão
  await pag.click('#navRolo button[data-aba="testes"]');
  await pag.waitForTimeout(250);
  await pag.fill("#tEx", "Agachamento");
  await pag.fill("#tValor", "150");
  await pag.click("#btTeste");
  await pag.waitForTimeout(400);
  const rm = await pag.evaluate(() => melhor1RM(meuAtleta().id, "Agachamento"));
  ok(rm === 150, "1RM lançado", rm);

  console.log("\n── As mensagens da área do atleta ─────────────────────");
  /* O laço inteiro: o atleta manda check-in, humor e PSE pelo WhatsApp, e isso
     tem de virar dado aqui dentro sem digitação. Colados TODOS DE UMA VEZ, que
     é como chegam de um elenco. */
  await pag.click('#navRolo button[data-aba="whatsapp"]');
  await pag.waitForTimeout(250);
  const ontem = await pag.evaluate(() => maisDias(hojeISO(), -3));
  const dBR = await pag.evaluate(d => dataBR(d), ontem);
  const brums24 = await pag.evaluate(() =>
    BRUMS_LISTA.map((x, i) => `${i+1}. ${x[0]} — ${x[1] === "Vigor" ? 3 : 1}`).join("\n"));
  const colada = [
    `🏐 CHECK-IN ELASE VOLEIBOL`, `Rafa · ${dBR}`, ``,
    `1. Sono (1 a 5) — 5`, `2. Horas dormidas — 8,5`, `3. Dor (0 a 10) — 2`,
    `4. Estresse (0 a 10) — 1`, `5. Sonolência KSS (1 a 9) — 2`, ``,
    `🏐 HUMOR ELASE VOLEIBOL`, `Rafa · ${dBR}`, ``, brums24, ``,
    `🏐 FIM DE SESSÃO ELASE VOLEIBOL`, `Rafa · ${dBR}`, ``,
    `1. Duração em minutos — 90`, `2. PSE (0 a 10) — 6`, `3. Tipo da sessão — Quadra`,
  ].join("\n");
  await pag.fill("#waTexto", colada);
  await pag.click("#btLerWA");
  await pag.waitForTimeout(400);

  const cartoes = await pag.$$eval("#waSaida [data-import]", bs => bs.length);
  ok(cartoes === 3, "as três mensagens coladas juntas são separadas", cartoes);
  const resumoWA = await pag.textContent("#waSaida .nota");
  ok(/check-in/i.test(resumoWA) && /humor/i.test(resumoWA) && /fim de sess/i.test(resumoWA),
     "e a tela diz o que leu de cada tipo", resumoWA.trim().replace(/\s+/g, " "));
  const donoSugerido = await pag.inputValue('[data-dono="0"]');
  const idAtleta = await pag.evaluate(() => ativos()[0].id);
  ok(donoSugerido === idAtleta, "o apelido do cabeçalho já escolhe o atleta");

  for (const i of [0, 1, 2]){
    await pag.click(`[data-import="${i}"]`);
    await pag.waitForTimeout(400);
  }
  const lancado = await pag.evaluate(d => {
    const a = ativos()[0], diario = diarioDe(a.id);
    const ses = sessoesDe(a.id).find(s => s.data === d);
    return {w: diario.w[d], b: diario.b[d + "|pre"], ses};
  }, ontem);
  ok(lancado.w && lancado.w.sq === 5 && lancado.w.dor === 2 && lancado.w.kss === 2,
     "o check-in do WhatsApp vira wellness", JSON.stringify(lancado.w));
  ok(lancado.w.sh === 8.5, "com a vírgula decimal lida certo", lancado.w.sh);
  ok(Array.isArray(lancado.b) && lancado.b.length === 24,
     "o humor vira as 24 respostas", lancado.b && lancado.b.length);
  ok(lancado.ses && lancado.ses.dur_min === 90 && lancado.ses.pse === 6,
     "a PSE vira sessão", JSON.stringify(lancado.ses && {d: lancado.ses.dur_min, p: lancado.ses.pse}));
  ok(lancado.ses.carga_ua === 540, "com a carga calculada — 90 × 6", lancado.ses.carga_ua);
  ok(lancado.ses.tonelagem === 0,
     "e tonelagem ZERO, porque ninguém mediu série nenhuma", lancado.ses.tonelagem);

  // Uma mensagem sem data no cabeçalho não pode ser lançada às cegas
  await pag.fill("#waTexto", "🏐 CHECK-IN ELASE VOLEIBOL\nRafa\n\n1. Sono (1 a 5) — 4\n3. Dor (0 a 10) — 2\n5. Sonolência KSS (1 a 9) — 3");
  await pag.click("#btLerWA");
  await pag.waitForTimeout(350);
  const semDataBloqueado = await pag.$eval('[data-import="0"]', b => b.disabled);
  ok(semDataBloqueado, "mensagem sem data no cabeçalho não é lançada");
  ok(/sem a data/i.test(await pag.textContent("#waSaida")), "e a tela diz por quê");

  // Valor fora da escala é recusado, não truncado
  await pag.fill("#waTexto", `🏐 CHECK-IN ELASE VOLEIBOL\nRafa · ${dBR}\n\n1. Sono (1 a 5) — 9\n3. Dor (0 a 10) — 2\n5. Sonolência KSS (1 a 9) — 3`);
  await pag.click("#btLerWA");
  await pag.waitForTimeout(350);
  const txtFora = await pag.textContent("#waSaida");
  ok(/Não consegui entender/i.test(txtFora) && /Sono/.test(txtFora),
     "sono 9 numa escala de 1 a 5 é reportado, não aceito");

  console.log("\n── Ajustar a sessão à mão ─────────────────────────────");
  await pag.click('#navRolo button[data-aba="prescricao"]');
  await pag.waitForTimeout(400);
  const hojeId = await pag.evaluate(() => hojeISO());
  const antes = await pag.evaluate(d => {
    const p = Store.get("prescricoes", d);
    return {n: p.exercicios.length, series0: p.exercicios[0].series};
  }, hojeId);
  await pag.click(`[data-editar-presc="${hojeId}"]`);
  await pag.waitForTimeout(450);
  ok(await pag.isVisible("#btGravarPresc"), "o editor abre");
  const camposEd = await pag.$$eval('[data-ed="0"]', e => e.length);
  ok(camposEd === 4, "cada exercício tem séries, reps, pausa e %", camposEd);

  // Digitar NÃO pode redesenhar: o campo perderia o foco a cada letra
  await pag.fill('[data-ed="0"][data-campo="series"]', "5");
  await pag.fill('[data-ed="0"][data-campo="reps"]', "12");
  const focoMantido = await pag.evaluate(() =>
    document.activeElement.getAttribute("data-campo"));
  ok(focoMantido === "reps", "o foco fica no campo enquanto se digita", focoMantido);
  const rascunho = await pag.evaluate(() => ({s: UI.rascunho[0].series, r: UI.rascunho[0].reps}));
  ok(rascunho.s === 5 && rascunho.r === "12", "e o rascunho acompanha", JSON.stringify(rascunho));

  // Nada foi gravado ainda
  const naoGravou = await pag.evaluate(d => Store.get("prescricoes", d).exercicios[0].series, hojeId);
  ok(naoGravou === antes.series0, "enquanto edita, o documento no banco fica intacto",
     `${naoGravou} (era ${antes.series0})`);

  // Tirar, acrescentar e mover
  await pag.click('[data-tirar-ex="0"]');
  await pag.waitForTimeout(350);
  ok((await pag.evaluate(() => UI.rascunho.length)) === antes.n - 1, "tirar exercício funciona");
  await pag.selectOption("#novoEx", "Push press");
  await pag.click("#btAddEx");
  await pag.waitForTimeout(350);
  const ultimo = await pag.evaluate(() => UI.rascunho[UI.rascunho.length-1].nome);
  ok(ultimo === "Push press", "acrescentar do catálogo funciona", ultimo);
  await pag.click(`[data-mover="${await pag.evaluate(() => UI.rascunho.length - 1)}:-1"]`);
  await pag.waitForTimeout(350);
  const penultimo = await pag.evaluate(() => UI.rascunho[UI.rascunho.length-2].nome);
  ok(penultimo === "Push press", "mover para cima funciona", penultimo);

  // Sair sem gravar sai sem gravar
  await pag.click("#btCancelarPresc");
  await pag.waitForTimeout(500);
  const depoisCancelar = await pag.evaluate(d =>
    Store.get("prescricoes", d).exercicios.length, hojeId);
  ok(depoisCancelar === antes.n, "sair sem gravar não muda nada", depoisCancelar);

  // Gravar grava
  await pag.click(`[data-editar-presc="${hojeId}"]`);
  await pag.waitForTimeout(400);
  await pag.fill('[data-ed="0"][data-campo="series"]', "6");
  await pag.fill('[data-ed="0"][data-campo="pct_rm"]', "70");
  await pag.click('[data-tirar-ex="1"]');
  await pag.waitForTimeout(350);
  await pag.click("#btGravarPresc");
  await pag.waitForTimeout(900);
  const gravado = await pag.evaluate(d => {
    const p = Store.get("prescricoes", d);
    return {n: p.exercicios.length, series: p.exercicios[0].series, pct: p.exercicios[0].pct_rm};
  }, hojeId);
  ok(gravado.n === antes.n - 1 && gravado.series === 6 && gravado.pct === 0.7,
     "gravar grava séries, % e a remoção", JSON.stringify(gravado));

  // % em branco é "sem percentual", não zero
  const semPct = await pag.evaluate(() => {
    UI.rascunho = [{nome:"x", grupo:"Força", series:3, reps:"8", pausa:90, pct_rm:0.8}];
    aplicarEdicao(0, "pct_rm", "");
    return UI.rascunho[0].pct_rm;
  });
  ok(semPct === null, "percentual apagado vira 'sem percentual', não 0%", semPct);

  console.log("\n── Prescrição individual ──────────────────────────────");
  const idIndiv = await pag.evaluate(async d => {
    const a = ativos()[0], base = Store.get("prescricoes", d);
    const docId = idPresc(d, a.id);
    await Store.set("prescricoes", docId, Object.assign({}, base,
      {atleta_id: a.id, notas: "plano individual",
       exercicios: base.exercicios.slice(0, 4)}));
    render();
    return docId;
  }, hojeId);
  await pag.waitForTimeout(500);
  const qualSessao = await pag.evaluate(d => {
    const a = ativos()[0];
    return {dele: prescDoDia(d, a.id).exercicios.length,
            equipe: prescDoDia(d).exercicios.length,
            individual: ehIndividual(prescDoDia(d, a.id))};
  }, hojeId);
  ok(qualSessao.dele === 4 && qualSessao.equipe > 4 && qualSessao.individual,
     "o plano individual substitui o da equipe só para aquele atleta",
     JSON.stringify(qualSessao));
  const outro = await pag.evaluate(d => {
    const fake = "aNaoExiste";
    return prescDoDia(d, fake).exercicios.length;
  }, hojeId);
  ok(outro === qualSessao.equipe, "e os outros continuam com o da equipe", outro);
  await pag.evaluate(async id => { await Store.remover("prescricoes", id); render(); }, idIndiv);
  await pag.waitForTimeout(400);

  console.log("\n── Massa ao longo do tempo ────────────────────────────");
  await pag.click('#navRolo button[data-aba="testes"]');
  await pag.waitForTimeout(400);
  await pag.selectOption("#tTipo", "Massa");
  await pag.fill("#tEx", "Massa corporal");
  await pag.fill("#tValor", "97,5");
  await pag.selectOption("#tUni", "kg");
  await pag.click("#btTeste");
  await pag.waitForTimeout(600);
  const massaNova = await pag.evaluate(() => ativos()[0].massa);
  ok(massaNova === 97.5, "a pesagem de hoje vira a massa do atleta", massaNova);
  const forcaDepois = await pag.evaluate(() => {
    const a = ativos()[0];
    return melhor1RM(a.id, "Agachamento") / a.massa;
  });
  ok(Math.abs(forcaDepois - 150/97.5) < 0.001,
     "e a força relativa passa a dividir pelo peso de hoje", forcaDepois);

  console.log("\n── Anamnese ───────────────────────────────────────────");
  await pag.click('#navRolo button[data-aba="whatsapp"]');
  await pag.waitForTimeout(350);
  const anMsg = await pag.evaluate(d => [
    "🏐 ANAMNESE ELASE VOLEIBOL", `Rafa · ${d}`, "",
    "1. PAR-Q 1 — não", "2. PAR-Q 2 — não", "3. PAR-Q 3 — não", "4. PAR-Q 4 — não",
    "5. PAR-Q 5 — sim", "6. PAR-Q 6 — não", "7. PAR-Q 7 — não",
    "8. Condições de saúde — Asma", "9. Cirurgias — nenhuma",
    "10. Medicação contínua — bombinha", "11. Alergias — nenhuma",
    "12. Lesões anteriores — Ombro|Direito|2026|45|Em tratamento",
    "13. Regiões que costumam doer — Lombar; Ombro",
    "14. Horas de sono habitual — 7,5", "15. Fuma — não", "16. Álcool — Raramente",
    "17. Anos de musculação — 6", "18. Experiência com levantamento olímpico — iniciante",
  ].join("\n"), dBR);
  await pag.fill("#waTexto", anMsg);
  await pag.click("#btLerWA");
  await pag.waitForTimeout(400);
  const txtAn = await pag.textContent("#waSaida");
  ok(/Anamnese/.test(txtAn), "a anamnese é reconhecida");
  ok(/liberação médica/i.test(txtAn),
     "o 'sim' no PAR-Q aparece como liberação médica antes de carga");
  await pag.click('[data-import="0"]');
  await pag.waitForTimeout(500);
  const anGravada = await pag.evaluate(() => anamneseDe(ativos()[0].id));
  ok(!!anGravada, "a anamnese grava");
  ok(anGravada.parq5 === true && anGravada.anos_muscu === 6 && anGravada.exp_lpo === "Iniciante",
     "com os valores certos", JSON.stringify([anGravada.parq5, anGravada.anos_muscu, anGravada.exp_lpo]));
  ok(anGravada.lesoes.length === 1 && anGravada.lesoes[0].status === "Em tratamento",
     "e a lesão decodificada", JSON.stringify(anGravada.lesoes));

  // Ela precisa aparecer onde o preparador decide
  await pag.click('#navRolo button[data-aba="inicio"]');
  await pag.waitForTimeout(400);
  const txtIni = await pag.innerText("#s-inicio");
  ok(/Saúde declarada/i.test(txtIni), "a saúde declarada sobe para o Início");
  ok(/liberação médica/i.test(txtIni), "com a bandeira crítica à vista");
  await pag.click('#navRolo button[data-aba="elenco"]');
  await pag.waitForTimeout(400);
  const txtEle = await pag.innerText("#s-elenco");
  ok(/Em tratamento/.test(txtEle), "e a lesão aparece na ficha do elenco");

  console.log("\n── Desempenho ─────────────────────────────────────────");
  await pag.click('#navRolo button[data-aba="desempenho"]');
  await pag.waitForTimeout(400);
  const txtDes = await pag.innerText("#s-desempenho");
  ok(/Força relativa/i.test(txtDes), "a aba de desempenho abre");
  const forcaRel = await pag.evaluate(() => {
    const a = ativos()[0];
    return {rm: melhor1RM(a.id, "Agachamento"), massa: a.massa};
  });
  ok(forcaRel.rm === 150 && forcaRel.massa === 97.5,
     "o 1RM e a massa (já a da pesagem de hoje) estão lá", JSON.stringify(forcaRel));
  ok(txtDes.indexOf("1,54") >= 0, "força relativa = 150 ÷ 97,5 = 1,54×",
     txtDes.replace(/\s+/g, " ").slice(0, 200));
  ok(/poucos dados/i.test(txtDes),
     "com um atleta só, a posição no elenco se recusa a existir");
  ok(/Uma medida só não é evolução|Sem reteste/i.test(txtDes),
     "e um 1RM só não vira curva de evolução");

  // Com um segundo reteste a curva aparece
  await pag.evaluate(async () => {
    const a = ativos()[0], lista = testesDe(a.id).slice();
    lista.push({data: maisDias(hojeISO(), -60), tipo: "1RM", exercicio: "Agachamento",
                valor: 132.5, unidade: "kg"});
    lista.push({data: maisDias(hojeISO(), -60), tipo: "Salto", exercicio: "CMJ",
                valor: 52, unidade: "cm"});
    lista.push({data: hojeISO(), tipo: "Salto", exercicio: "CMJ", valor: 57.5, unidade: "cm"});
    await Store.set("testes", a.id, {lista});
    render();     // no modo local a gravação não redesenha sozinha
  });
  await pag.waitForTimeout(600);
  const svgs = await pag.$$eval("#s-desempenho svg", e => e.length);
  ok(svgs >= 2, "com dois pontos, as curvas desenham", svgs);
  const txtDes2 = await pag.innerText("#s-desempenho");
  ok(/\+17,5 kg/.test(txtDes2), "e a curva diz o ganho: 132,5 → 150 kg",
     (txtDes2.match(/[+−]\d+[,.]\d+ kg/) || [""])[0]);
  ok(/\+5,5 cm/.test(txtDes2), "o salto também: 52 → 57,5 cm",
     (txtDes2.match(/[+−]\d+[,.]\d+ cm/) || [""])[0]);
  // Rótulos dentro do desenho
  const foraDoSvg = await pag.$$eval("#s-desempenho svg text", ts =>
    ts.filter(t => {
      const c = t.getBoundingClientRect(), s = t.closest("svg").getBoundingClientRect();
      return c.width > 0 && (c.left < s.left - 1 || c.right > s.right + 1 || c.top < s.top - 1);
    }).length);
  ok(foraDoSvg === 0, "nenhum rótulo escapa do desenho", foraDoSvg);

  console.log("\n── Cópia de segurança ─────────────────────────────────");
  await pag.click('#navRolo button[data-aba="ajustes"]');
  await pag.waitForTimeout(400);
  const pacote = await pag.evaluate(() => montarBackup());
  ok(pacote.formato === "elase-backup", "a cópia tem formato declarado", pacote.formato);
  ok(Object.keys(pacote.colecoes).length === 8, "e todas as coleções",
     Object.keys(pacote.colecoes).join(","));
  ok(Object.keys(pacote.colecoes.atletas).length === 1
     && Object.keys(pacote.colecoes.anamnese).length === 1,
     "com o atleta e a anamnese dentro");
  const tamanho = await pag.evaluate(() => JSON.stringify(montarBackup()).length);
  ok(tamanho > 1000, "a cópia tem conteúdo de verdade", tamanho + " bytes");

  // Um arquivo errado NÃO pode ser restaurado por cima da temporada
  const recusas = await pag.evaluate(() => [
    validarBackup(null),
    validarBackup({formato: "outra-coisa"}),
    validarBackup({formato: "elase-backup"}),
    validarBackup({formato: "elase-backup", colecoes: {invasor: {}}}),
    validarBackup({formato: "elase-backup", colecoes: {atletas: {a1: "texto"}}}),
    validarBackup({formato: "elase-backup", colecoes: {atletas: {a1: {nome: "ok"}}}}),
  ]);
  ok(recusas.slice(0, 5).every(r => r.length > 0), "arquivo errado é recusado com motivo",
     JSON.stringify(recusas));
  ok(recusas[5] === "", "e uma cópia válida passa");

  // Restaurar de verdade: apaga e traz de volta
  await pag.evaluate(async p => {
    const a = ativos()[0];
    await Store.remover("atletas", a.id);
    await Store.remover("anamnese", a.id);
    window.__pacote = p;
  }, pacote);
  await pag.waitForTimeout(400);
  ok((await pag.evaluate(() => atletas().length)) === 0, "o elenco foi apagado");
  await pag.evaluate(async () => {
    for (const col of Object.keys(window.__pacote.colecoes))
      for (const id of Object.keys(window.__pacote.colecoes[col])){
        const corpo = Object.assign({}, window.__pacote.colecoes[col][id]);
        delete corpo.id;
        await Store.set(col, id, corpo);
      }
  });
  await pag.waitForTimeout(600);
  const depoisRestauro = await pag.evaluate(() => {
    const a = atletas()[0];
    return a ? {nome: a.nome, massa: a.massa, anamnese: !!anamneseDe(a.id),
                testes: testesDe(a.id).length} : null;
  });
  ok(depoisRestauro && depoisRestauro.nome === "Rafael Moreira",
     "e volta inteiro da cópia", JSON.stringify(depoisRestauro));
  ok(depoisRestauro.anamnese && depoisRestauro.testes >= 3,
     "com anamnese e testes juntos", JSON.stringify(depoisRestauro));

  // Layout no celular
  const larguraDemais = await pag.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  ok(larguraDemais <= 1, "não há rolagem horizontal da página", larguraDemais + "px");

  const alvosPequenos = await pag.$$eval("button:not([hidden]), a.bt, input, select", els =>
    els.filter(e => {
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.height < 38;
    }).map(e => (e.id || e.className || e.tagName) + ":" + Math.round(e.getBoundingClientRect().height)));
  ok(alvosPequenos.length === 0, "todo alvo de toque tem pelo menos 38px",
     alvosPequenos.slice(0, 6).join(", "));

  // O tema é pintado, não herdado
  const fundo = await pag.evaluate(() => getComputedStyle(document.body).backgroundColor);
  ok(fundo !== "rgba(0, 0, 0, 0)" && fundo !== "transparent", "o body pinta o próprio fundo", fundo);

  ok(erros.length === 0, "nenhum erro de console no fluxo inteiro", erros.join(" | "));

  const PASTA = "/tmp/claude-0/-home-user/02bc64c7-556e-5b07-a28e-82ffa0d966cd/scratchpad/";
  await pag.click('#navRolo button[data-aba="inicio"]');
  await pag.waitForTimeout(350);
  await pag.screenshot({ path: PASTA + "tela-inicio.png", fullPage: true });
  await pag.click('#navRolo button[data-aba="analise"]');
  await pag.waitForTimeout(350);
  await pag.screenshot({ path: PASTA + "tela-analise.png", fullPage: true });
  await pag.click('#navRolo button[data-aba="sessao"]');
  await pag.waitForTimeout(350);
  await pag.screenshot({ path: PASTA + "tela-sessao.png", fullPage: false });

  console.log(`\n${passes} passaram, ${falhas} falharam.\n`);
  await navegador.close();
  servidor.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
