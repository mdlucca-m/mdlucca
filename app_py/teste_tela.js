/* Percorre as dez abas num navegador de verdade, como preparador e como
   atleta, no computador e no celular. Teste unitário não pega tela em branco
   nem erro de JavaScript — este pega. */
const { chromium, devices } = require("playwright");
const BASE = process.env.BASE || "http://127.0.0.1:8777";
const PIN = process.env.PIN || "1234";

let falhas = 0, n = 0;
const ok = (c, m, e) => { n++; if (c) console.log("  OK    · " + m);
  else { falhas++; console.log("  FALHA · " + m + (e !== undefined ? "  → " + e : "")); } };

(async () => {
  const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  const erros = [];

  async function nova(dispositivo) {
    const ctx = await b.newContext(dispositivo || { viewport: { width: 1440, height: 1000 } });
    const p = await ctx.newPage();
    p.on("pageerror", e => erros.push("JS: " + e.message));
    /* "Failed to load resource" aparece para todo HTTP 4xx — inclusive os que
       ESTE teste provoca de propósito (o DELETE recusado no console SQL). O que
       interessa aqui é erro de JavaScript, não resposta de erro esperada. */
    p.on("console", m => { if (m.type() === "error"
      && !/favicon|Failed to load resource/.test(m.text()))
      erros.push("console: " + m.text()); });
    return { ctx, p };
  }

  console.log("\n═══ 1 · A PÁGINA SOBE ═══");
  let { ctx, p } = await nova();
  await p.goto(BASE, { waitUntil: "networkidle" });
  await p.waitForTimeout(600);
  let r = await p.evaluate(() => ({
    titulo: document.title,
    abas: [...document.querySelectorAll("#abas button")].map(b => b.textContent.trim()),
    texto: (document.getElementById("pagina")?.innerText || "").length,
    semana: document.getElementById("txtSemana")?.textContent,
  }));
  ok(r.texto > 200, "a tela inicial desenha", r.texto + " caracteres");
  ok(r.abas.length === 6, "o atleta vê 6 abas (as de comando ficam escondidas)", r.abas.join("|"));
  ok(/semana \d+/.test(r.semana || ""), "e o cabeçalho mostra a semana do macrociclo", r.semana);

  console.log("\n═══ 2 · CADASTRO DO ATLETA, PELA TELA ═══");
  await p.click('[data-aba="cadastro"]');
  await p.waitForTimeout(300);
  const preencher = async (campo, valor) => {
    await p.fill(`[data-cad="${campo}"]`, String(valor)).catch(async () =>
      await p.selectOption(`[data-cad="${campo}"]`, String(valor)));
  };
  await preencher("nome", "Rafael Teste da Silva");
  await preencher("nasc", "2000-05-14");
  await p.selectOption('[data-cad="posicao"]', "Central");
  await preencher("estatura", "201");
  await preencher("massa", "95");
  await preencher("anos_pratica", "10");
  await preencher("emergencia", "Ana Teste 41 90000-0000");
  await p.click("#cadEnviar");
  await p.waitForTimeout(900);
  r = await p.evaluate(() => ({
    aviso: document.getElementById("aviso")?.textContent,
    aba: [...document.querySelectorAll("#abas button")].find(b => b.getAttribute("aria-selected") === "true")?.textContent.trim(),
    selecionado: document.getElementById("selAtleta")?.value,
  }));
  ok(/Esta área é sua/.test(r.aviso || ""), "cadastro liberado: entra direto", r.aviso);
  ok(r.aba === "Bem-estar", "e cai na tela de check-in", r.aba);
  ok(!!r.selecionado, "com ele já selecionado no topo", r.selecionado);

  console.log("\n═══ 3 · CHECK-IN E BRUMS ═══");
  await p.evaluate(() => {
    document.querySelectorAll("[data-esc]").forEach(b => { if (b.dataset.v === "3") b.click(); });
    document.querySelectorAll("[data-brums]").forEach(b => { if (b.dataset.v === "1") b.click(); });
  });
  await p.fill("#sonoHoras", "8");
  await p.click("#btBem");
  await p.waitForTimeout(500);
  const av1 = await p.evaluate(() => document.getElementById("aviso")?.textContent);
  ok(/gravado/i.test(av1 || ""), "check-in gravado", av1);
  await p.click("#btBrums");
  await p.waitForTimeout(700);
  const av2 = await p.evaluate(() => document.getElementById("aviso")?.textContent);
  ok(/gravado/i.test(av2 || ""), "e a BRUMS também", av2);

  console.log("\n═══ 4 · MODO PREPARADOR ═══");
  await p.evaluate(pin => { localStorage.setItem("elase.pin", pin); }, PIN);
  await p.reload({ waitUntil: "networkidle" });
  await p.waitForTimeout(600);
  r = await p.evaluate(() => [...document.querySelectorAll("#abas button")].map(b => b.textContent.trim()));
  ok(r.length === 11, "com o PIN aparecem as 11 abas", r.join("|"));
  ok(r.includes("Prescrição") && r.includes("Sistema") && r.includes("SQL"),
     "incluindo as de comando");

  console.log("\n═══ 5 · GERAR O SISTEMA ═══");
  await p.click('[data-aba="sistema"]');
  await p.waitForTimeout(900);
  r = await p.evaluate(() => ({
    temBotao: !!document.getElementById("sisGerar"),
    rotulo: document.getElementById("sisGerar")?.textContent.trim(),
    linhas: document.querySelectorAll("#pagina tbody tr").length,
  }));
  ok(r.temBotao, "a prévia desenha com o botão de gerar", r.rotulo);
  ok(r.linhas >= 4, "e mostra uma linha por semana", r.linhas);
  p.on("dialog", d => d.accept());
  await p.click("#sisGerar");
  await p.waitForTimeout(1500);
  const av3 = await p.evaluate(() => document.getElementById("aviso")?.textContent);
  ok(/sessões prescritas/.test(av3 || ""), "gerou as sessões", av3);

  console.log("\n═══ 6 · A SESSÃO DE HOJE ═══");
  await p.click('[data-aba="sessao"]');
  await p.waitForTimeout(900);
  r = await p.evaluate(() => ({
    texto: (document.getElementById("pagina")?.innerText || "").slice(0, 80).replace(/\n/g, " "),
    temAbrir: !!document.getElementById("btAbrir"),
  }));
  console.log("      " + r.texto);
  if (r.temAbrir) {
    await p.click("#btAbrir");
    await p.waitForTimeout(900);
    r = await p.evaluate(() => ({
      exercicios: document.querySelectorAll(".exercicio").length,
      series: document.querySelectorAll(".serie").length,
      temFechar: !!document.getElementById("btFechar"),
    }));
    ok(r.exercicios > 4, "o treino abriu com os exercícios", r.exercicios);
    ok(r.series > 15, "e as séries para preencher", r.series);
    ok(r.temFechar, "com o check-out disponível");

    await p.evaluate(() => {
      const f = document.querySelector(".serie");
      f.querySelector('[data-f="carga"]').value = "100";
      f.querySelector('[data-f="carga"]').dispatchEvent(new Event("change"));
      f.querySelector('[data-f="reps"]').value = "5";
      f.querySelector('[data-f="reps"]').dispatchEvent(new Event("change"));
      f.querySelector("[data-tique]").click();
    });
    await p.waitForTimeout(600);
    ok(await p.evaluate(() => document.querySelector(".serie").classList.contains("feita")),
       "a série marcada fica verde");
    await p.selectOption("#pse", "7");
    await p.click("#btFechar");
    await p.waitForTimeout(1200);
    const av4 = await p.evaluate(() => document.getElementById("aviso")?.textContent);
    ok(/Treino encerrado/.test(av4 || ""), "e o check-out fecha com a carga", av4);
  } else {
    ok(true, "(hoje não é dia de treino no microciclo gerado — sem sessão a abrir)");
  }

  console.log("\n═══ 7 · ANÁLISE ═══");
  await p.click('[data-aba="analise"]');
  await p.waitForTimeout(1000);
  r = await p.evaluate(() => {
    const t = document.getElementById("pagina")?.innerText || "";
    /* o CSS põe h3, th e .k em caixa alta, e o innerText devolve assim:
       comparar com maiúscula exata falha por motivo nenhum */
    return { acwr: /ACWR/i.test(t), monotonia: /monotonia/i.test(t),
      z: /subescala/i.test(t), prontid: /prontid/i.test(t),
      sujeira: /undefined|NaN|\[object/.test(t) };
  });
  ok(r.acwr && r.monotonia, "ACWR e monotonia na tela");
  ok(r.prontid, "prontidão também");
  ok(r.z, "e a tabela de Z por subescala");
  ok(!r.sujeira, "sem undefined nem NaN");

  console.log("\n═══ 8 · CONSOLE SQL ═══");
  await p.click('[data-aba="sql"]');
  await p.waitForTimeout(400);
  await p.click("#sqlRodar");
  await p.waitForTimeout(700);
  ok(await p.evaluate(() => !!document.querySelector("#sqlSaida table, #sqlSaida .vazio")),
     "a consulta padrão roda e mostra resultado");
  await p.fill("#sqlTxt", "DELETE FROM atletas");
  await p.click("#sqlRodar");
  await p.waitForTimeout(700);
  ok(await p.evaluate(() => /leitura/i.test(document.getElementById("sqlSaida")?.innerText || "")),
     "e um DELETE é recusado com explicação");

  console.log("\n═══ 8b · MOBILIDADE, EDUCATIVO E VÍDEO NA SESSÃO ═══");
  /* O microciclo treina segunda, quarta e sexta. Se hoje for terça, quinta ou
     fim de semana, não há sessão — e o teste mediria o calendário em vez do
     app. Aqui uma sessão de HOJE é criada de propósito, a partir do próprio
     gerador, para a verificação não depender do dia da semana. */
  const criada = await p.evaluate(async () => {
    const hoje = new Date().toISOString().slice(0, 10);
    const ja = await (await fetch(`/api/prescricoes?de=${hoje}&ate=${hoje}`)).json();
    if (ja.length) return "já havia";
    /* o modelo vem das sessões JÁ prescritas: a prévia do gerador volta vazia
       depois que o teste anterior gerou o macrociclo inteiro */
    const todas = await (await fetch("/api/prescricoes")).json();
    const modelo = todas.find(x => x.objetivo === "Força máxima") || todas[0];
    if (!modelo) return "sem modelo";
    await api("/api/prescricoes", {method: "POST", body: JSON.stringify({
      data: hoje, hora: modelo.hora, tipo: modelo.tipo, objetivo: modelo.objetivo,
      bloco: modelo.bloco, notas: modelo.notas, exercicios: modelo.exercicios})});
    return "criada";
  });
  console.log("      sessão de hoje: " + criada);
  await p.click('[data-aba="sessao"]');
  await p.waitForTimeout(1200);
  /* os blocos de exercício só existem DEPOIS do check-in: antes dele a tela
     mostra a tabela de pré-visualização do treino */
  if (await p.evaluate(() => !!document.getElementById("btAbrir"))) {
    await p.click("#btAbrir");
    await p.waitForTimeout(1200);
  }
  r = await p.evaluate(() => {
    const cab = [...document.querySelectorAll(".exercicio > header")];
    const nomes = cab.map(h => h.querySelector("b")?.textContent || "");
    const grupos = cab.map(h => h.querySelectorAll(".pilula")[0]?.textContent || "");
    return {
      total: cab.length,
      mobilidade: grupos.filter(g => /Mobilidade/.test(g)).length,
      educativo: grupos.filter(g => /Educativo/.test(g)).length,
      primeiro: grupos[0] || "",
      dicas: document.querySelectorAll(".dica").length,
      videos: document.querySelectorAll('.exercicio a[href*="youtube"]').length,
      /* a linha de mobilidade não pode ter campo de quilo */
      levesComKg: [...document.querySelectorAll(".serie.leve")]
        .filter(f => f.querySelector('[data-f="carga"]')).length,
      alvoBranco: [...document.querySelectorAll('.exercicio a.pilula')]
        .every(a => a.target === "_blank" && /noopener/.test(a.rel || "")),
    };
  });
  console.log(`      ${r.total} exercícios · ${r.mobilidade} mobilidade · ${r.educativo} educativos`);
  ok(r.mobilidade >= 3, "a sessão traz mobilidade articular", r.mobilidade);
  ok(/Mobilidade/.test(r.primeiro), "e ela vem PRIMEIRO", r.primeiro);
  ok(r.educativo >= 2, "com educativos de LPO", r.educativo);
  ok(r.dicas >= 5, "cada um com a dica técnica na tela", r.dicas);
  ok(r.videos === r.total, "e link de vídeo em todos", `${r.videos}/${r.total}`);
  ok(r.levesComKg === 0, "mobilidade NÃO pede carga em quilos", r.levesComKg);
  ok(r.alvoBranco, "os links de vídeo abrem em aba nova, com rel=noopener");

  console.log("\n═══ 8c · FIXAR UM VÍDEO ═══");
  await p.click('[data-aba="exercicios"]');
  await p.waitForTimeout(900);
  r = await p.evaluate(async () => {
    const campo = document.querySelector('[data-video="Agachamento cossaco"]');
    if (!campo) return {semCampo: true};
    campo.value = "https://www.youtube.com/watch?v=EXEMPLO";
    document.querySelector('[data-salvar="Agachamento cossaco"]').click();
    await new Promise(r => setTimeout(r, 900));
    return {aviso: document.getElementById("aviso")?.textContent};
  });
  ok(/fixado/i.test(r.aviso || ""), "o preparador fixa o vídeo dele", r.aviso);
  r = await p.evaluate(async () => {
    const campo = document.querySelector('[data-video="Hip airplane"]');
    campo.value = "javascript:alert(1)";
    document.querySelector('[data-salvar="Hip airplane"]').click();
    await new Promise(r => setTimeout(r, 900));
    return {aviso: document.getElementById("aviso")?.textContent};
  });
  ok(/http/i.test(r.aviso || ""), "e um endereço que não é http é recusado", r.aviso);

  console.log("\n═══ 9 · TODAS AS ABAS, SEM QUEBRAR ═══");
  const abas = await p.evaluate(() => [...document.querySelectorAll("#abas button")].map(b => b.dataset.aba));
  const ruins = [];
  for (const a of abas) {
    await p.click(`[data-aba="${a}"]`);
    await p.waitForTimeout(700);
    const t = await p.evaluate(() => document.getElementById("pagina")?.innerText || "");
    if (t.trim().length < 40) ruins.push(a + ": vazia");
    if (/Deu erro nesta tela/.test(t)) ruins.push(a + ": erro");
    const m = t.match(/undefined|NaN|\[object [A-Z]/);
    if (m) ruins.push(a + ': mostra "' + m[0] + '"');
  }
  ok(ruins.length === 0, `as ${abas.length} abas desenham`, ruins.join(" | "));
  await ctx.close();

  console.log("\n═══ 10 · CELULAR ═══");
  ({ ctx, p } = await nova(devices["iPhone 13"]));
  await p.goto(BASE, { waitUntil: "networkidle" });
  await p.evaluate(pin => localStorage.setItem("elase.pin", pin), PIN);
  await p.reload({ waitUntil: "networkidle" });
  await p.waitForTimeout(800);
  for (const a of ["inicio", "sessao", "analise", "sistema"]) {
    await p.click(`[data-aba="${a}"]`).catch(() => {});
    await p.waitForTimeout(600);
    const larg = await p.evaluate(() => ({
      doc: document.documentElement.scrollWidth, win: window.innerWidth }));
    ok(larg.doc <= larg.win + 1, `a aba "${a}" não escorre para o lado`, JSON.stringify(larg));
  }
  await ctx.close();

  console.log("\n═══ 11 · ERROS DE JAVASCRIPT ═══");
  ok(erros.length === 0, "nenhum", erros.slice(0, 4).join(" | "));

  await b.close();
  console.log("\n" + (falhas ? "✗ " : "✓ ") + (n - falhas) + "/" + n + " · " + falhas + " falhas\n");
  process.exit(falhas ? 1 : 0);
})();
