/* Área do atleta: cadastro, área, check-in, fim de sessão — e a verificação que
   mais importa, que é a PARIDADE do motor com o app da comissão. As duas páginas
   têm cópias do gerador; se divergirem, o atleta treina uma coisa e o preparador
   analisa outra. O teste compara dia a dia. */
const { chromium, devices } = require("playwright");
const http = require("http");
const fs = require("fs");

const DOCS = "/home/user/mdlucca/docs/";
const PORTA = 8945;
let falhas = 0, passes = 0;
function ok(cond, nome, extra) {
  if (cond) passes++;
  else { falhas++; console.log("  ✗ " + nome + (extra ? "  →  " + extra : "")); }
}

/* O mesmo esqueleto que o publicador embrulha em volta da página: sem a meta de
   viewport o Chromium usa 980px e nenhum defeito de celular aparece. */
const ABRE = `<!doctype html><html><head><meta charset=utf8>` +
  `<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">` +
  `<style>:root{color-scheme:light;box-sizing:border-box;` +
  `padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}` +
  `body{margin:0;padding:0;font:14px -apple-system,sans-serif;background:#faf9f5;color:#141413}` +
  `img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>\n`;

const servidor = http.createServer((req, res) => {
  const arq = req.url.indexOf("/app") === 0 ? "app.html" : "atleta.html";
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(ABRE + fs.readFileSync(DOCS + arq, "utf8") + "\n</body></html>");
});

const MACRO = "2026-09-21";                      // uma segunda-feira

(async () => {
  await new Promise(r => servidor.listen(PORTA, r));
  const navegador = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
  const ctx = await navegador.newContext(Object.assign({}, devices["iPhone 13"]));
  const pag = await ctx.newPage();
  const erros = [];
  pag.on("console", m => { if (m.type() === "error") erros.push(m.text()); });
  pag.on("pageerror", e => erros.push("pageerror: " + e.message));

  await pag.goto(`http://127.0.0.1:${PORTA}/atleta?m=${MACRO}&p=5541999990000`,
    { waitUntil: "load" });
  await pag.waitForTimeout(400);

  console.log("\n── Paridade com o app da comissão ─────────────────────");

  const doAtleta = await pag.evaluate(m => {
    const fora = {};
    for (let i = 0; i < 60; i++) {
      const d = maisDias(m, i);
      const s = sessaoDoDia(d, m);
      fora[d] = s ? { tipo: s.tipo, objetivo: s.objetivo, reteste: s.reteste,
        exs: s.exercicios.map(e => [e.nome, e.grupo, e.series, e.reps, e.pausa, e.pct_rm]) } : null;
    }
    return fora;
  }, MACRO);

  const pag2 = await ctx.newPage();
  const errosApp = [];
  pag2.on("pageerror", e => errosApp.push(e.message));
  await pag2.goto(`http://127.0.0.1:${PORTA}/app`, { waitUntil: "load" });
  await pag2.waitForTimeout(400);
  const doApp = await pag2.evaluate(m => {
    const g = gerarSistema(BLOCOS_PADRAO, m, 1, 9, []);
    const fora = {};
    for (const s of g.sessoes)
      fora[s.data] = { tipo: s.tipo, objetivo: s.objetivo,
        reteste: /Reteste/.test(s.objetivo),
        exs: s.exercicios.map(e => [e.nome, e.grupo, e.series, e.reps, e.pausa, e.pct_rm]) };
    return fora;
  }, MACRO);

  let diasTreino = 0, divergentes = [];
  for (const dia of Object.keys(doAtleta)) {
    const a = doAtleta[dia], b = doApp[dia] || null;
    if (a) diasTreino++;
    if (JSON.stringify(a) !== JSON.stringify(b)) divergentes.push(dia);
  }
  ok(diasTreino === 26, "60 dias trazem 26 sessões de sala (3 por semana)", diasTreino);
  ok(divergentes.length === 0,
     "as duas páginas geram EXATAMENTE a mesma sessão em cada dia",
     divergentes.slice(0, 4).join(", "));
  ok(errosApp.length === 0, "o app da comissão abre sem erro", errosApp.join(" | "));
  await pag2.close();

  console.log("\n── Cadastro ───────────────────────────────────────────");

  /* O invariante é não existir CAMPO de dinheiro — não é não existir a palavra.
     A página promete, em texto, que não pergunta salário nem renda; uma varredura
     no HTML inteiro reprovava justamente a promessa. O que se checa é cada
     controle: nome, id, placeholder e o rótulo que o acompanha. */
    const camposDinheiro = await pag.$$eval("input, select, textarea", els =>
    els.map(e => {
      const rot = e.id ? (document.querySelector(`label[for="${e.id}"]`) || {}).textContent || "" : "";
      return [e.name, e.id, e.placeholder, rot].join(" ").toLowerCase();
    }).filter(t => /sal[áa]rio|renda|remunera|pagamento|mensalidade|pix|banco|r\$/.test(t)));
  ok(camposDinheiro.length === 0, "nenhum campo pede dinheiro",
     camposDinheiro.join(" | "));
  ok(await pag.isVisible("#c-nome"), "a página abre no cadastro");
  ok(!(await pag.isVisible("#navRolo button")), "sem ficha não há abas ainda");

  // Enviar vazio é recusado, e o foco vai para o primeiro campo que falta
  await pag.click("#btEntrar");
  await pag.waitForTimeout(200);
  ok(await pag.isVisible("#avCad"), "cadastro vazio é recusado");
  const focoNome = await pag.evaluate(() => document.activeElement.id);
  ok(focoNome === "c-nome", "o foco vai para o primeiro campo que falta", focoNome);

  await pag.fill("#c-nome", "Rafael Moreira dos Santos");
  await pag.fill("#c-nasc", "1999-05-02");
  await pag.selectOption("#c-posicao", "Central");
  await pag.fill("#c-estatura", "201");
  await pag.fill("#c-massa", "95");
  await pag.fill("#c-anos", "12");
  await pag.fill("#c-emerg", "Ana (41) 97777-0000");
  await pag.click("#btEntrar");
  await pag.waitForTimeout(500);

  ok(await pag.isVisible("#btEu"), "depois do cadastro aparece o nome no topo");
  const nomeTopo = await pag.textContent("#btEu");
  ok(nomeTopo.trim() === "Rafael", "o apelido sai do primeiro nome quando não informado", nomeTopo);
  const abas = await pag.$$eval("#navRolo button", bs => bs.map(b => b.textContent.trim()));
  ok(abas.join(" ") === "Hoje Check-in Minha semana Meus dados",
     "a área do atleta abre com as quatro abas", abas.join(" · "));

  const ficha = await pag.textContent("#textoEnvio");
  ok(/^🏐 CADASTRO ELASE VOLEIBOL/.test(ficha), "a ficha sai no formato que o app lê");
  ok(/1\. Nome completo — Rafael Moreira dos Santos/.test(ficha), "nome na linha 1");
  ok(/3\. Data de nascimento — 02\/05\/1999/.test(ficha), "data em dd/mm/aaaa",
     (ficha.match(/3\..*/) || [""])[0]);
  ok(/4\. Posição — Central/.test(ficha), "posição na linha 4");
  const linkWA = await pag.getAttribute("a.bt.zap", "href");
  ok(linkWA.indexOf("https://wa.me/5541999990000?text=") === 0,
     "o botão do WhatsApp já aponta para o preparador", linkWA.slice(0, 44));

  /* A ficha do atleta tem de ser lida pelo app da comissão sem perda: é o mesmo
     formato dos dois lados, e é aqui que se prova. */
  const pag3 = await ctx.newPage();
  await pag3.goto(`http://127.0.0.1:${PORTA}/app`, { waitUntil: "load" });
  await pag3.waitForTimeout(300);
  const lido = await pag3.evaluate(t => lerWA(t), ficha);
  ok(lido.dados.nome === "Rafael Moreira dos Santos", "o app lê o nome", lido.dados.nome);
  ok(lido.dados.nasc === "1999-05-02", "o app lê a data de volta em aaaa-mm-dd", lido.dados.nasc);
  ok(lido.dados.posicao === "Central", "o app lê a posição", lido.dados.posicao);
  ok(lido.dados.estatura === 201 && lido.dados.massa === 95, "o app lê as medidas",
     `${lido.dados.estatura} / ${lido.dados.massa}`);
  ok(lido.faltam.length === 0, "nada obrigatório se perde no caminho",
     JSON.stringify(lido.faltam));
  await pag3.close();

  console.log("\n── A área ─────────────────────────────────────────────");

  const hoje = await pag.evaluate(() => hojeISO());
  const eDiaDeSala = await pag.evaluate(m => !!sessaoDoDia(hojeISO(), m), MACRO);
  const txtHoje = await pag.innerText("#s-hoje");
  if (eDiaDeSala) {
    ok(/min|séries/i.test(txtHoje), "o dia de sala mostra a sessão");
  } else {
    ok(/não tem sala|Próxima sessão/i.test(txtHoje),
       "num dia sem sala a página diz isso e mostra a próxima", txtHoje.slice(0, 60));
  }
  ok(/check-in/i.test(txtHoje), "o check-in é oferecido na abertura");

  // Minha semana: sete dias, e a mobilidade das três articulações
  await pag.click('[data-ir="semana"]');
  await pag.waitForTimeout(350);
  const dias = await pag.$$eval("#s-semana .pares div", ds => ds.length);
  ok(dias === 7, "a semana mostra os sete dias", dias);
  const txtSem = await pag.innerText("#s-semana");
  ok(/tornozelo/i.test(txtSem) && /quadril/i.test(txtSem) && /ombro/i.test(txtSem),
     "tornozelo, quadril e ombro aparecem na mobilidade");
  const dicas = await pag.$$eval("#s-semana .ex .dica", e => e.length);
  ok(dicas >= 10, "a instrução técnica acompanha cada exercício de mobilidade", dicas);

  console.log("\n── Check-in ───────────────────────────────────────────");
  await pag.click('[data-ir="checkin"]');
  await pag.waitForTimeout(350);
  await pag.click("#btWell");
  await pag.waitForTimeout(200);
  ok(await pag.isVisible("#avWell"), "check-in incompleto é recusado");

  await pag.click('[data-escala="sq"] [data-v="4"]');
  await pag.fill("#wSh", "7,5");
  await pag.click('[data-escala="dor"] [data-v="3"]');
  await pag.click('[data-escala="es"] [data-v="2"]');
  await pag.click('[data-escala="kss"] [data-v="3"]');
  await pag.click("#btWell");
  await pag.waitForTimeout(500);
  const msgW = await pag.textContent("#textoEnvio");
  ok(/^🏐 CHECK-IN ELASE VOLEIBOL/.test(msgW), "a mensagem de check-in sai numerada");
  ok(/1\. Sono \(1 a 5\) — 4/.test(msgW), "sono na linha 1");
  ok(/2\. Horas dormidas — 7,5/.test(msgW), "a vírgula decimal é preservada");
  ok(/3\. Dor \(0 a 10\) — 3/.test(msgW), "dor na linha 3");
  ok(msgW.indexOf("Rafael") > 0, "a mensagem diz de quem é");

  // BRUMS: incompleta é recusada, e o número que falta é dito
  await pag.click('[data-brums="0"] [data-v="1"]');
  await pag.click("#btBrums");
  await pag.waitForTimeout(250);
  ok(await pag.isVisible("#avBrums"), "BRUMS com item faltando é recusada");
  const avB = await pag.textContent("#avBrums");
  ok(/23 itens/.test(avB), "e diz quantos faltam", avB);

  await pag.evaluate(() => {
    for (let i = 0; i < 24; i++) document.querySelector(`[data-brums="${i}"] [data-v="2"]`).click();
  });
  await pag.click("#btBrums");
  await pag.waitForTimeout(500);
  const msgB = await pag.textContent("#textoEnvio");
  ok(/^🏐 HUMOR ELASE VOLEIBOL/.test(msgB), "a BRUMS vira mensagem");
  ok(msgB.split("\n").filter(l => /^\d+\. /.test(l)).length === 24,
     "com os 24 itens", msgB.split("\n").filter(l => /^\d+\. /.test(l)).length);

  console.log("\n── Fim de sessão ──────────────────────────────────────");
  await pag.click('[data-ir="hoje"]');
  await pag.waitForTimeout(300);
  await pag.click('[data-ir="fim"]');
  await pag.waitForTimeout(350);
  const btFim = await pag.$("#btFim");
  ok(await btFim.isDisabled(), "sem PSE o botão fica travado");
  await pag.click('[data-pse="7"]');
  await pag.waitForTimeout(150);
  ok(!(await btFim.isDisabled()), "com PSE escolhida libera");
  await pag.fill("#durFim", "480");
  await pag.click("#btFim");
  await pag.waitForTimeout(250);
  ok(await pag.isVisible("#avFim"), "duração de 8 horas é recusada");
  await pag.fill("#durFim", "75");
  await pag.click("#btFim");
  await pag.waitForTimeout(500);
  const msgF = await pag.textContent("#textoEnvio");
  ok(/^🏐 FIM DE SESSÃO ELASE VOLEIBOL/.test(msgF), "a PSE vira mensagem");
  ok(/1\. Duração em minutos — 75/.test(msgF), "duração na linha 1");
  ok(/2\. PSE \(0 a 10\) — 7/.test(msgF), "PSE na linha 2");

  console.log("\n── O laço fecha? ──────────────────────────────────────");
  /* As três mensagens que o atleta acabou de produzir, coladas juntas no app da
     comissão. É o teste que importa: não que cada lado funcione sozinho, mas
     que o que sai de um entre no outro sem perda. */
  const pag4 = await ctx.newPage();
  await pag4.goto(`http://127.0.0.1:${PORTA}/app`, { waitUntil: "load" });
  await pag4.waitForTimeout(300);
  const volta = await pag4.evaluate(t => {
    const msgs = separarMensagens(t).map(lerMensagemWA).filter(m => !m.vazio);
    return msgs.map(m => ({tipo:m.tipo, quem:m.quem, data:m.data, faltam:m.faltam,
      naoLidos:m.naoLidos, dados:m.dados}));
  }, [msgW, msgB, msgF].join("\n\n"));

  ok(volta.length === 3, "as três mensagens do atleta são separadas pelo app", volta.length);
  ok(volta.map(v => v.tipo).join(",") === "checkin,humor,sessao",
     "e cada uma é reconhecida pelo tipo", volta.map(v => v.tipo).join(","));
  ok(volta.every(v => v.quem === "Rafael"), "todas sabem de quem são",
     volta.map(v => v.quem).join(","));
  ok(volta.every(v => v.data === hoje), "e de que dia", volta.map(v => v.data).join(","));
  ok(volta.every(v => v.faltam.length === 0 && v.naoLidos.length === 0),
     "nada se perde no caminho",
     JSON.stringify(volta.map(v => [v.faltam, v.naoLidos])));
  const ci = volta[0].dados;
  ok(ci.sq === 4 && ci.sh === 7.5 && ci.dor === 3 && ci.es === 2 && ci.kss === 3,
     "o check-in chega com os cinco valores", JSON.stringify(ci));
  ok(volta[1].dados.vals.length === 24 && volta[1].dados.vals.every(v => v === 2),
     "a BRUMS chega inteira");
  const fs_ = volta[2].dados;
  ok(fs_.dur === 75 && fs_.pse === 7, "a PSE chega com duração e intensidade",
     JSON.stringify(fs_));
  await pag4.close();

  console.log("\n── Meus dados ─────────────────────────────────────────");
  await pag.click('[data-ir="meus"]');
  await pag.waitForTimeout(350);
  const txtMeus = await pag.innerText("#s-meus");
  ok(/Rafael Moreira dos Santos/.test(txtMeus), "a ficha aparece de volta");
  ok(/201/.test(txtMeus) && /95/.test(txtMeus), "com as medidas");

  // 1RM: o percentual vira quilo na tela do atleta
  await pag.fill('[data-rm="Agachamento"]', "150");
  await pag.click("#btRM");
  await pag.waitForTimeout(400);
  ok(await pag.isVisible("#avRM"), "o 1RM grava");
  const viraQuilo = await pag.evaluate(m => {
    const s = sessaoDoDia("2026-09-21", m);           // semana 1: agachamento a 62%
    const e = s.exercicios.find(x => x.nome === "Agachamento");
    return {pct: e.pct_rm, alvo: Math.round(S.rm["Agachamento"] * e.pct_rm / 2.5) * 2.5};
  }, MACRO);
  ok(viraQuilo.alvo === 92.5, "62% de 150 kg vira 92,5 kg, arredondado à anilha",
     JSON.stringify(viraQuilo));

  // Persistência: recarregar não perde a área
  await pag.reload({ waitUntil: "load" });
  await pag.waitForTimeout(400);
  ok(await pag.isVisible("#btEu"), "recarregar mantém o atleta dentro da área");
  const rmDepois = await pag.evaluate(() => S.rm["Agachamento"]);
  ok(rmDepois === 150, "e mantém o 1RM", rmDepois);

  console.log("\n── Celular ────────────────────────────────────────────");
  const sobra = await pag.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  ok(sobra <= 1, "não há rolagem horizontal da página", sobra + "px");
  const pequenos = await pag.$$eval("button:not([hidden]), a.bt, input, select", els =>
    els.filter(e => {
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.height < 36;
    }).map(e => (e.id || e.className || e.tagName) + ":" + Math.round(e.getBoundingClientRect().height)));
  ok(pequenos.length === 0, "todo alvo de toque tem pelo menos 36px", pequenos.slice(0, 6).join(", "));
  const fundo = await pag.evaluate(() => getComputedStyle(document.body).backgroundColor);
  ok(fundo !== "rgba(0, 0, 0, 0)", "o body pinta o próprio fundo", fundo);
  ok(erros.length === 0, "nenhum erro de console no fluxo inteiro", erros.join(" | "));

  const PASTA = "/tmp/claude-0/-home-user/02bc64c7-556e-5b07-a28e-82ffa0d966cd/scratchpad/";
  await pag.click('[data-ir="hoje"]');
  await pag.waitForTimeout(300);
  await pag.screenshot({ path: PASTA + "atleta-hoje.png", fullPage: false });

  // E a página sem ficha, que é o que o atleta vê ao abrir o link pela 1ª vez
  const nova = await ctx.newPage();
  await nova.goto(`http://127.0.0.1:${PORTA}/atleta?m=${MACRO}`, { waitUntil: "load" });
  await nova.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await nova.reload({ waitUntil: "load" });
  await nova.waitForTimeout(300);
  await nova.screenshot({ path: PASTA + "atleta-cadastro.png", fullPage: false });
  await nova.close();

  console.log(`\n${passes} passaram, ${falhas} falharam.\n`);
  await navegador.close();
  servidor.close();
  process.exit(falhas ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
