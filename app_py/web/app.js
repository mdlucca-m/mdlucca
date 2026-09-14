"use strict";
/* ELASE — interface do sistema de prescrição e análise.
   Sem framework e sem biblioteca de gráfico: os gráficos são barras e faixas
   em CSS. Menos bonito que Chart.js, e funciona offline, em celular velho e
   atrás de qualquer firewall — que é onde este app vai rodar. */

const E = {
  aba: "inicio", estado: null, me: null, pin: localStorage.getItem("elase.pin") || "",
  presc: [], analise: null, sessao: null, series: {}, brums: {}, bem: {},
  cad: {}, sis: {de: null, ate: null}, sql: "SELECT * FROM sessoes ORDER BY data DESC LIMIT 20",
};

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const fmt = (v, d = 0) => Number.isFinite(+v)
  ? (+v).toLocaleString("pt-BR", {minimumFractionDigits: d, maximumFractionDigits: d}) : "—";
const sig = (v, d = 1) => (v > 0 ? "+" : "") + fmt(v, d);
const hoje = () => new Date().toISOString().slice(0, 10);
const dBR = s => s ? s.slice(8, 10) + "/" + s.slice(5, 7) + "/" + s.slice(0, 4) : "—";
const el = id => document.getElementById(id);

function aviso(msg, tipo = "info") {
  const a = el("aviso");
  a.textContent = msg; a.className = "ver " + tipo;
  clearTimeout(aviso._t);
  aviso._t = setTimeout(() => { a.className = tipo; }, 3600);
}

async function api(rota, opc = {}) {
  const cab = {"Content-Type": "application/json"};
  if (E.pin) cab["X-Pin"] = E.pin;
  const r = await fetch(rota, {...opc, headers: {...cab, ...(opc.headers || {})}});
  let d;
  try { d = await r.json(); } catch { throw new Error("Resposta do servidor não é JSON."); }
  if (!r.ok) throw new Error(d.erro || ("Erro " + r.status));
  return d;
}

const ehTreinador = () => !!E.pin;

/* ── Abas ────────────────────────────────────────────────────────────────── */
const ABAS = [
  {id: "inicio",     rot: "Início"},
  {id: "cadastro",   rot: "Cadastro"},
  {id: "sessao",     rot: "Minha Sessão"},
  {id: "bemestar",   rot: "Bem-estar"},
  {id: "analise",    rot: "Análise"},
  {id: "testes",     rot: "Testes"},
  {id: "elenco",     rot: "Elenco",     chefe: true},
  {id: "prescricao", rot: "Prescrição", chefe: true},
  {id: "sistema",    rot: "Sistema",    chefe: true},
  {id: "sql",        rot: "SQL",        chefe: true},
];

function desenharAbas() {
  el("abas").innerHTML = ABAS
    .filter(a => !a.chefe || ehTreinador())
    .map(a => `<button role="tab" data-aba="${a.id}" class="${a.chefe ? "chefe" : ""}"
       aria-selected="${E.aba === a.id}">${esc(a.rot)}</button>`).join("");
  el("abas").querySelectorAll("[data-aba]").forEach(b =>
    b.onclick = () => { E.aba = b.dataset.aba; desenhar(); });
}

/* ── Carga inicial ───────────────────────────────────────────────────────── */
async function carregar() {
  E.estado = await api("/api/estado");
  const c = E.estado.config;
  // o nome da equipe fica no título; a linha de baixo é a categoria e a
  // temporada. Repetir "ELASE Voleibol Masculino" nas duas linhas era ruído.
  document.querySelector(".marca b").textContent = c.equipe.toUpperCase();
  el("mcCat").textContent = `${c.categoria} · ${c.temporada}`;
  el("txtSemana").textContent = E.estado.semana > 0
    ? `semana ${E.estado.semana} · ciclo ${E.estado.ciclo} · ${E.estado.bloco_atual?.bloco || ""}`
    : "macrociclo ainda não começou";
  const sel = el("selAtleta");
  sel.innerHTML = `<option value="">— escolher atleta —</option>` + E.estado.atletas
    .map(a => `<option value="${a.id}"${String(a.id) === String(E.me) ? " selected" : ""}>
      ${esc(a.apelido)}${a.status !== "Ativo" ? " (" + a.status + ")" : ""}</option>`).join("");
  sel.onchange = () => {
    E.me = sel.value || null;
    localStorage.setItem("elase.me", E.me || "");
    E.analise = null; desenhar();
  };
  if (!E.me) E.me = localStorage.getItem("elase.me") || null;
  if (E.me && !E.estado.atletas.some(a => String(a.id) === String(E.me))) E.me = null;
  sel.value = E.me || "";
}

el("btnPin").onclick = async () => {
  if (ehTreinador()) {
    E.pin = ""; localStorage.removeItem("elase.pin");
    if (ABAS.find(a => a.id === E.aba)?.chefe) E.aba = "inicio";
    aviso("Saiu do modo preparador.", "info"); desenhar(); return;
  }
  const p = prompt("PIN do preparador físico:");
  if (p === null) return;
  E.pin = p;
  try {
    await api("/api/sistema/previa", {method: "POST", body: JSON.stringify({de: 1, ate: 1})});
    localStorage.setItem("elase.pin", p);
    aviso("Modo preparador ligado.", "good"); desenhar();
  } catch (e) { E.pin = ""; aviso(e.message, "crit"); }
};

/* ── Desenho ─────────────────────────────────────────────────────────────── */
const TELAS = {};

async function desenhar() {
  el("btnPin").textContent = ehTreinador() ? "🔓 Preparador" : "🔒 Preparador";
  el("btnPin").classList.toggle("on", ehTreinador());
  desenharAbas();
  const fn = TELAS[E.aba] || TELAS.inicio;
  el("pagina").innerHTML = `<div class="vazio">carregando…</div>`;
  try {
    el("pagina").innerHTML = await fn();
    if (fn.depois) await fn.depois();
  } catch (e) {
    el("pagina").innerHTML = `<div class="cartao acc-risco"><header><h3>Deu erro nesta tela</h3></header>
      <div class="nota" style="--acc:var(--crit)">${esc(e.message)}</div></div>`;
  }
  window.scrollTo({top: 0});
}

function cabeca(titulo, texto) {
  return `<div class="cabeca"><h1>${titulo}</h1><p>${texto}</p></div><div class="regua"></div>`;
}

/* ═══ INÍCIO ═══════════════════════════════════════════════════════════════ */
TELAS.inicio = async () => {
  const s = E.estado, b = s.bloco_atual;
  const link = location.origin + "/#cadastro";
  const ativos = s.atletas.filter(a => a.status === "Ativo").length;
  return cabeca("Prescrição e <em>análise</em> de desempenho",
    "Cadastro do atleta, prescrição do treino, execução em quadra e a leitura dos números — no mesmo lugar.") + `
  <div class="ladrilhos">
    <div class="ladrilho acc-carga"><div class="k">Semana da temporada</div>
      <div class="v">${s.semana > 0 ? s.semana : "—"}</div>
      <div class="u">${s.semana > 0 ? `ciclo ${s.ciclo} · posição ${s.posicao}/${s.blocos.length}` : "macrociclo não começou"}</div></div>
    <div class="ladrilho acc-forca"><div class="k">Bloco</div>
      <div class="v" style="font-size:21px">${esc(b?.bloco || "—")}</div>
      <div class="u">${esc(b?.enfase || "")}</div></div>
    <div class="ladrilho acc-bom"><div class="k">Elenco</div>
      <div class="v">${ativos}</div><div class="u">atleta(s) ativo(s)</div></div>
    <div class="ladrilho acc-tec"><div class="k">Microciclo</div>
      <div class="v" style="font-size:21px">${esc(b?.micro || "—")}</div>
      <div class="u">intensidade ${b ? Math.round(b.intensidade * 100) + "%" : "—"} · ${b?.plio ?? "—"} contatos</div></div>
  </div>

  <div class="grade g2">
    <div class="cartao acc-lpo"><header><h3>Link do cadastro</h3>
      <span class="sub">é este que vai para o atleta</span></header>
      <div class="copiavel"><div class="txt" id="lkTxt">${esc(link)}</div>
        <button class="btn primario" id="lkCopiar">Copiar</button></div>
      <div class="nota" style="margin-top:12px">${s.config.cadastro_liberado
        ? `<b>Cadastro liberado.</b> Quem abre o link preenche e <b>entra na área dele na hora</b> — faz
           check-in e registra treino sem esperar por você.`
        : `<b>Cadastro com aprovação.</b> A ficha entra como <b>Pendente</b> e o atleta só usa depois que
           você ativar no Elenco.`}
      <br><br><b>Para o link abrir no celular dele, o servidor precisa estar acessível na rede.</b>
      Rodando em <code>localhost</code> ele só abre nesta máquina. Veja o <b>LEIA-ME</b> — há duas formas:
      a rede do ginásio (mesmo wi-fi) ou uma hospedagem com endereço público.</div></div>

    <div class="cartao acc-humor"><header><h3>A rotina que faz o sistema funcionar</h3></header>
      <div class="rolagem"><table><tbody>
        <tr><td><b>Atleta, de manhã</b></td><td>Check-in do dia: sono, dor, estresse e a BRUMS. 30 segundos.</td></tr>
        <tr><td><b>Atleta, no treino</b></td><td>Abre a sessão, marca carga e repetições de cada série, fecha com a PSE.</td></tr>
        <tr><td><b>Você, semanal</b></td><td>Gera o microciclo na aba <b>Sistema</b> e ajusta o que quiser em <b>Prescrição</b>.</td></tr>
        <tr><td><b>Você, diário</b></td><td><b>Análise</b>: ACWR, monotonia, strain e o Z de humor de cada atleta.</td></tr>
        <tr><td><b>A cada macrociclo</b></td><td>A última sexta é <b>reteste</b> de 1RM e salto — é o que faz o ciclo seguinte valer mais.</td></tr>
      </tbody></table></div></div>
  </div>`;
};
TELAS.inicio.depois = async () => {
  const b = el("lkCopiar");
  if (b) b.onclick = async () => {
    try { await navigator.clipboard.writeText(el("lkTxt").textContent); aviso("Link copiado.", "good"); }
    catch { aviso("Copie o texto à mão — o navegador não deixou.", "crit"); }
  };
};

/* ═══ CADASTRO ═════════════════════════════════════════════════════════════ */
const CAMPOS_CAD = [
  ["nome", "Nome completo", "texto", true, 2],
  ["apelido", "Como prefere ser chamado", "texto", false, 1],
  ["nasc", "Data de nascimento", "data", true, 1],
  ["posicao", "Posição", "opcoes", true, 1],
  ["camisa", "Número da camisa", "num", false, 1],
  ["telefone", "Telefone (WhatsApp)", "texto", false, 1],
  ["estatura", "Estatura (cm)", "num", true, 1],
  ["massa", "Massa corporal (kg)", "num", true, 1],
  ["alcance_pe", "Alcance em pé (cm)", "num", false, 1],
  ["alcance_ataque", "Alcance de ataque (cm)", "num", false, 1],
  ["alcance_bloqueio", "Alcance de bloqueio (cm)", "num", false, 1],
  ["anos_pratica", "Anos de prática no voleibol", "num", true, 1],
  ["dominancia", "Mão dominante", "lista:Destro,Canhoto,Ambidestro", false, 1],
  ["perna_impulsao", "Perna de impulsão", "lista:Esquerda,Direita,Simétrica", false, 1],
  ["escolaridade", "Escolaridade", "lista:Fundamental,Médio completo,Superior em andamento,Superior completo,Pós-graduação", false, 1],
  ["emergencia", "Contato de emergência (nome e telefone)", "texto", true, 2],
  ["lesoes", "Lesões anteriores ou limitações", "texto", false, 2],
  ["obs", "Algo mais que a comissão deva saber", "texto", false, 2],
];

TELAS.cadastro = async () => {
  const campo = ([id, rot, tipo, obr, larg]) => {
    const v = E.cad[id] ?? "";
    const cls = larg === 2 ? ' class="largo"' : "";
    const marca = obr ? ' <span style="color:var(--warn-i)">•</span>' : "";
    if (tipo === "opcoes" || tipo.startsWith("lista:")) {
      const ops = tipo === "opcoes" ? E.estado.posicoes : tipo.slice(6).split(",");
      return `<label class="c"${cls}><span>${esc(rot)}${marca}</span>
        <select data-cad="${id}"><option value=""></option>
        ${ops.map(o => `<option${o === v ? " selected" : ""}>${esc(o)}</option>`).join("")}</select></label>`;
    }
    const t = tipo === "data" ? "date" : "text";
    const extra = tipo === "num" ? ' inputmode="decimal"' : "";
    return `<label class="c"${cls}><span>${esc(rot)}${marca}</span>
      <input type="${t}" data-cad="${id}" value="${esc(v)}"${extra}></label>`;
  };
  return cabeca("Cadastro do <em>atleta</em>",
    "Dois minutos. Estatura, massa e alcances entram direto no cálculo de salto e de carga.") + `
  <div class="cartao acc-carga">
    <div class="formulario">${CAMPOS_CAD.map(campo).join("")}</div>
    <div class="nota" style="margin-top:14px">Campos com <span style="color:var(--warn-i)">•</span> são
    obrigatórios. Alcance em pé, de ataque e de bloqueio você pode deixar em branco: são medidos com fita na
    quadra e o preparador completa depois.</div>
    <div class="linha" style="margin-top:16px">
      <button class="btn primario" id="cadEnviar">Enviar meu cadastro</button></div>
  </div>
  <div class="cartao acc-tec"><header><h3>O que acontece com o que você escreve</h3></header>
    <div class="rolagem"><table><tbody>
      <tr><td><b>Quem vê</b></td><td>A comissão técnica. Não escreva nada que você não queira que ela leia.</td></tr>
      <tr><td><b>Dinheiro, nunca</b></td><td>O sistema não pergunta salário nem renda — não existe coluna
        para isso no banco de dados.</td></tr>
      <tr><td><b>Para que serve</b></td><td>Contato de emergência e histórico de lesão existem para te
        <b>proteger</b> em quadra.</td></tr>
    </tbody></table></div></div>`;
};
TELAS.cadastro.depois = async () => {
  document.querySelectorAll("[data-cad]").forEach(n =>
    n.oninput = n.onchange = () => { E.cad[n.dataset.cad] = n.value; });
  el("cadEnviar").onclick = async () => {
    const faltam = CAMPOS_CAD.filter(c => c[3] && !String(E.cad[c[0]] || "").trim()).map(c => c[1]);
    if (faltam.length) { aviso("Falta preencher: " + faltam.join(", "), "crit"); return; }
    try {
      const r = await api("/api/cadastro", {method: "POST", body: JSON.stringify(E.cad)});
      E.cad = {};
      await carregar();
      if (r.liberado) {
        E.me = String(r.id);
        localStorage.setItem("elase.me", E.me);
        el("selAtleta").value = E.me;
        aviso("Pronto! Esta área é sua — comece pelo check-in do dia.", "good");
        E.aba = "bemestar";
      } else {
        aviso("Cadastro enviado. O preparador vai ativar o seu acesso.", "good");
        E.aba = "inicio";
      }
      desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  };
};

/* ═══ MINHA SESSÃO ═════════════════════════════════════════════════════════ */
TELAS.sessao = async () => {
  if (!E.me) return semAtleta("registrar o seu treino");
  E.presc = await api(`/api/prescricoes?de=${hoje()}&ate=${hoje()}&atleta=${E.me}`);
  if (!E.presc.length) return cabeca("Minha <em>sessão</em>", "O treino de hoje.") +
    `<div class="cartao"><div class="vazio">Nenhuma sessão prescrita para hoje.
     ${ehTreinador() ? "Gere o microciclo na aba <b>Sistema</b>." : "Fale com o preparador."}</div></div>`;

  const p = E.presc[0];
  const d = await api(`/api/minha-sessao?atleta=${E.me}&prescricao=${p.id}`);
  E.sessao = d.sessao;
  E.series = {};
  (d.series || []).forEach(s => { E.series[s.exercicio + "_" + s.numero] = s; });

  if (!E.sessao) {
    return cabeca("Minha <em>sessão</em>", `${esc(p.objetivo)} · ${esc(p.bloco)}`) + `
    <div class="cartao acc-carga"><header><h3>${esc(p.tipo)} · ${dBR(p.data)}</h3>
      <span class="pilula info">${p.plano.series} séries · ~${p.plano.dur} min</span></header>
      <div class="nota">${esc(p.notas || "")}</div>
      <div class="rolagem" style="margin-top:12px"><table><thead><tr>
        <th>Exercício</th><th>Grupo</th><th class="n">Séries</th><th class="n">Reps</th>
        <th class="n">Pausa</th><th class="n">%1RM</th></tr></thead><tbody>
        ${p.exercicios.map(e => `<tr><td><b>${esc(e.nome)}</b>${e.obs ? `<div class="sub">${esc(e.obs)}</div>` : ""}</td>
          <td>${esc(e.grupo)}</td><td class="n">${e.series}</td><td class="n">${esc(e.reps)}</td>
          <td class="n">${e.pausa}s</td><td class="n">${e.pct_rm ? Math.round(e.pct_rm * 100) + "%" : "—"}</td></tr>`).join("")}
      </tbody></table></div>
      <div class="linha" style="margin-top:16px">
        <button class="btn primario" id="btAbrir">Check-in e começar o treino</button></div>
      <div class="nota" style="margin-top:12px">O check-in registra sono, dor e humor <b>antes</b> de treinar.
      É ele que dá sentido ao número no fim: carga alta com humor bom e carga alta com humor ruim são
      coisas diferentes.</div>
    </div>`;
  }

  const fechada = !!E.sessao.check_out;
  return cabeca("Minha <em>sessão</em>", `${esc(p.objetivo)} · ${esc(p.bloco)}`) + `
  <div class="cartao ${fechada ? "acc-bom" : "acc-carga"}">
    <header><h3>${esc(p.tipo)} · ${dBR(p.data)}</h3>
      ${fechada
        ? `<span class="pilula good">encerrada · ${fmt(E.sessao.carga_ua)} UA</span>
           <span class="pilula">${E.sessao.dur_min} min · PSE ${fmt(E.sessao.pse, 1)}</span>
           <span class="pilula">${fmt(E.sessao.tonelagem)} kg de tonelagem</span>`
        : `<span class="pilula info">em andamento</span>`}</header>
    ${fechada ? `<div class="nota" style="--acc:var(--good)">Sessão encerrada. Os números já estão na Análise.</div>` : ""}
  </div>
  ${p.exercicios.map((e, i) => exercicioHTML(e, i, fechada)).join("")}
  ${fechada ? "" : `<div class="cartao acc-forca"><header><h3>Encerrar o treino</h3></header>
    <label class="c" style="max-width:320px">Como foi o esforço da sessão? (PSE 0 a 10)
      <select id="pse">${[...Array(11).keys()].map(v =>
        `<option value="${v}">${v} — ${["repouso","muito leve","leve","moderado","um pouco difícil","difícil",
          "difícil","muito difícil","muito difícil","quase máximo","máximo"][v]}</option>`).join("")}</select></label>
    <div class="linha" style="margin-top:14px">
      <button class="btn primario" id="btFechar">Check-out</button></div>
    <div class="nota" style="margin-top:12px">A carga da sessão é <b>duração × PSE</b>. Sem o check-out o
    treino não entra na conta da semana — e é essa conta que alimenta ACWR, monotonia e strain.</div></div>`}`;
};

function exercicioHTML(e, i, fechada) {
  let linhas = "";
  for (let s = 1; s <= e.series; s++) {
    const r = E.series[i + "_" + s] || {};
    linhas += `<div class="serie ${r.feita ? "feita" : ""}" data-ex="${i}" data-s="${s}">
      <span class="n">${s}ª</span>
      <input type="number" step="0.5" placeholder="kg" value="${r.carga ?? ""}" data-f="carga" ${fechada ? "disabled" : ""}>
      <input type="number" placeholder="${esc(e.reps)}" value="${r.reps ?? ""}" data-f="reps" ${fechada ? "disabled" : ""}>
      <input type="number" step="0.5" placeholder="RIR" value="${r.rir ?? ""}" data-f="rir" ${fechada ? "disabled" : ""}>
      <input type="number" step="0.01" placeholder="m/s" value="${r.vel ?? ""}" data-f="vel" ${fechada ? "disabled" : ""}>
      <button class="tique ${r.feita ? "on" : ""}" data-tique ${fechada ? "disabled" : ""}>✓</button></div>`;
  }
  return `<div class="exercicio"><header><b>${esc(e.nome)}</b>
      <span class="pilula">${esc(e.grupo)}</span>
      <span class="pilula">${e.series}×${esc(e.reps)}</span>
      <span class="pilula">pausa ${e.pausa}s</span>
      ${e.pct_rm ? `<span class="pilula info">${Math.round(e.pct_rm * 100)}% 1RM</span>` : ""}
      ${e.tempo ? `<span class="pilula">cadência ${esc(e.tempo)}</span>` : ""}</header>
    <div class="cabeserie"><span></span><span>Carga kg</span><span>Reps</span><span>RIR</span><span>Vel m/s</span><span></span></div>
    ${linhas}
    ${e.obs ? `<div class="sub" style="padding:8px 14px 12px">${esc(e.obs)}</div>` : ""}</div>`;
}

TELAS.sessao.depois = async () => {
  const abrir = el("btAbrir");
  if (abrir) abrir.onclick = async () => {
    try {
      const r = await api("/api/sessao/abrir", {method: "POST", body: JSON.stringify({
        atleta_id: +E.me, prescricao_id: E.presc[0].id})});
      aviso("Check-in registrado. Bom treino!", "good");
      desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  };
  const gravar = async (fila) => {
    const d = {sessao_id: E.sessao.id, exercicio: +fila.dataset.ex, numero: +fila.dataset.s,
      feita: fila.classList.contains("feita")};
    fila.querySelectorAll("input").forEach(i => { d[i.dataset.f] = i.value === "" ? null : +i.value; });
    try { await api("/api/sessao/serie", {method: "POST", body: JSON.stringify(d)}); }
    catch (e) { aviso(e.message, "crit"); }
  };
  document.querySelectorAll(".serie").forEach(fila => {
    fila.querySelectorAll("input").forEach(i => i.onchange = () => gravar(fila));
    const t = fila.querySelector("[data-tique]");
    if (t) t.onclick = () => {
      fila.classList.toggle("feita");
      t.classList.toggle("on");
      gravar(fila);
    };
  });
  const fechar = el("btFechar");
  if (fechar) fechar.onclick = async () => {
    try {
      const r = await api("/api/sessao/fechar", {method: "POST", body: JSON.stringify({
        sessao_id: E.sessao.id, pse: +el("pse").value})});
      aviso(`Treino encerrado: ${fmt(r.carga_ua)} UA em ${r.dur_min} min.`, "good");
      E.analise = null; desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  };
};

function semAtleta(oque) {
  return cabeca("Escolha o <em>atleta</em>", `Para ${oque}, selecione o nome no topo da tela.`) +
    `<div class="cartao"><div class="vazio">Nenhum atleta selecionado.
     Use o seletor no topo — ou faça o seu cadastro na aba <b>Cadastro</b>.</div></div>`;
}

/* ═══ BEM-ESTAR ════════════════════════════════════════════════════════════ */
TELAS.bemestar = async () => {
  if (!E.me) return semAtleta("registrar o check-in");
  const escala = (nome, n, de, valor, rot) => `
    <div class="item"><span>${esc(rot)}</span><span class="escala">
      ${[...Array(n).keys()].map(i => i + de).map(v =>
        `<button data-esc="${nome}" data-v="${v}" class="${String(E.bem[nome]) === String(v) ? "on" : ""}">${v}</button>`).join("")}
    </span></div>`;
  const itensBrums = E.estado.brums_itens.map(([sub, itens]) => `
    <div class="sub" style="margin:14px 0 6px;letter-spacing:.12em;text-transform:uppercase">${esc(sub)}</div>
    ${itens.map(i => `<div class="item"><span>${esc(i)}</span><span class="escala">
      ${[0, 1, 2, 3, 4].map(v => `<button data-brums="${esc(i)}" data-v="${v}"
        class="${String(E.brums[i]) === String(v) ? "on" : ""}">${v}</button>`).join("")}
    </span></div>`).join("")}`).join("");

  return cabeca("Check-in do <em>dia</em>",
    "Trinta segundos, de manhã. É o que separa uma carga alta bem tolerada de uma carga alta que vai cobrar.") + `
  <div class="grade g2">
    <div class="cartao acc-carga"><header><h3>Como você está hoje</h3></header>
      ${escala("sono_qual", 5, 1, null, "Qualidade do sono (1 péssima · 5 ótima)")}
      <div class="item"><span>Horas dormidas</span>
        <input type="number" step="0.5" id="sonoHoras" value="${E.bem.sono_horas ?? ""}"
          style="width:90px;text-align:right;border:1px solid var(--line);background:var(--inset);
          border-radius:8px;padding:8px;min-height:42px"></div>
      ${escala("estresse", 11, 0, null, "Estresse (0 nenhum · 10 altíssimo)")}
      ${escala("dor", 11, 0, null, "Dor muscular (0 nenhuma · 10 muita)")}
      ${escala("kss", 9, 1, null, "Sonolência KSS (1 alerta · 9 muito sonolento)")}
      <div class="linha" style="margin-top:14px">
        <button class="btn primario" id="btBem">Gravar o check-in</button></div></div>

    <div class="cartao acc-humor"><header><h3>BRUMS · como você se sente agora</h3>
      <span class="sub">0 nada · 1 um pouco · 2 moderado · 3 bastante · 4 extremo</span></header>
      <div style="max-height:52vh;overflow:auto">${itensBrums}</div>
      <div class="linha" style="margin-top:14px">
        <button class="btn primario" id="btBrums">Gravar o humor</button>
        <span class="sub" id="brumsN">${Object.keys(E.brums).length} de 24 respondidos</span></div>
      <div class="nota" style="margin-top:12px">A BRUMS é comparada com a <b>sua própria</b> base dos últimos
      30 dias, não com a média do elenco. A Fadiga 10 do líbero pode ser a segunda-feira normal do central.</div></div>
  </div>`;
};
TELAS.bemestar.depois = async () => {
  document.querySelectorAll("[data-esc]").forEach(b => b.onclick = () => {
    E.bem[b.dataset.esc] = +b.dataset.v;
    b.parentElement.querySelectorAll("button").forEach(x => x.classList.remove("on"));
    b.classList.add("on");
  });
  document.querySelectorAll("[data-brums]").forEach(b => b.onclick = () => {
    E.brums[b.dataset.brums] = +b.dataset.v;
    b.parentElement.querySelectorAll("button").forEach(x => x.classList.remove("on"));
    b.classList.add("on");
    el("brumsN").textContent = `${Object.keys(E.brums).length} de 24 respondidos`;
  });
  el("btBem").onclick = async () => {
    E.bem.sono_horas = el("sonoHoras").value ? +el("sonoHoras").value : null;
    try {
      await api("/api/wellness", {method: "POST", body: JSON.stringify({atleta_id: +E.me, ...E.bem})});
      aviso("Check-in gravado.", "good"); E.analise = null;
    } catch (e) { aviso(e.message, "crit"); }
  };
  el("btBrums").onclick = async () => {
    const n = Object.keys(E.brums).length;
    if (n < 24) { aviso(`Faltam ${24 - n} itens da BRUMS.`, "crit"); return; }
    try {
      await api("/api/brums", {method: "POST", body: JSON.stringify({
        atleta_id: +E.me, respostas: E.brums, momento: "pre"})});
      aviso("Humor gravado.", "good"); E.brums = {}; E.analise = null; desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  };
};

/* ═══ ANÁLISE ══════════════════════════════════════════════════════════════ */
TELAS.analise = async () => {
  if (!E.me) return semAtleta("ver a análise");
  const a = await api(`/api/analise?atleta=${E.me}`);
  E.analise = a;
  const c = a.carga, z = a.zona;
  const nivel = a.nivel_texto;
  const barraACWR = () => {
    const pos = Math.max(0, Math.min(1, c.acwr / 2)) * 100;
    return `<div class="faixa">
      <div class="zona" style="left:0%;width:40%;background:var(--s1)"></div>
      <div class="zona" style="left:40%;width:25%;background:var(--good)"></div>
      <div class="zona" style="left:65%;width:10%;background:var(--warn)"></div>
      <div class="zona" style="left:75%;width:25%;background:var(--crit)"></div>
      <div class="txt"><span>0,80</span><span>1,30</span><span>1,50</span></div>
      ${c.acwr ? `<div class="marca" style="left:calc(${pos}% - 1.5px)"></div>` : ""}</div>`;
  };
  const maxD = Math.max(1, ...c.diarias);
  return cabeca("Análise de <em>carga e prontidão</em>",
    `${esc(a.atleta.apelido)} · ${esc(a.atleta.posicao || "")} · leitura dele contra ele mesmo.`) + `
  <div class="ladrilhos">
    <div class="ladrilho ${z.c === "crit" ? "acc-risco" : z.c === "warn" ? "acc-forca" : "acc-bom"}">
      <div class="k">ACWR</div><div class="v">${c.acwr ? fmt(c.acwr, 2) : "—"}</div>
      <div class="u">${esc(z.t)}</div></div>
    <div class="ladrilho acc-carga"><div class="k">Carga da semana</div>
      <div class="v">${fmt(c.semanal)}</div><div class="u">UA (duração × PSE)</div></div>
    <div class="ladrilho ${c.monotonia === null && c.semanal > 0 ? "acc-risco" : "acc-forca"}">
      <div class="k">Monotonia</div>
      <div class="v">${c.monotonia === null ? "—" : fmt(c.monotonia, 2)}</div>
      <div class="u">${c.monotonia === null
        ? (c.semanal > 0 ? "carga idêntica todo dia — indefinida, e é o pior caso" : "sem carga na semana")
        : c.monotonia > 2 ? "acima de 2,0 — pouca variação" : "variação adequada"}</div></div>
    <div class="ladrilho acc-tec"><div class="k">Strain</div>
      <div class="v">${c.strain === null ? "—" : fmt(c.strain)}</div>
      <div class="u">monotonia × carga semanal</div></div>
    <div class="ladrilho ${a.nivel === 2 ? "acc-risco" : a.nivel === 1 ? "acc-forca" : "acc-bom"}">
      <div class="k">Prontidão</div>
      <div class="v">${a.prontidao === null ? "—" : fmt(a.prontidao)}</div>
      <div class="u">${esc(nivel[0])}</div></div>
  </div>

  <div class="grade g2">
    <div class="cartao ${z.c === "crit" ? "acc-risco" : "acc-carga"}">
      <header><h3>Razão carga aguda : crônica</h3>
        <span class="pilula ${z.c}">${esc(z.t)}</span></header>
      ${barraACWR()}
      <div class="rolagem" style="margin-top:10px"><table><tbody>
        <tr><td>Aguda (7 dias)</td><td class="n">${fmt(c.aguda)} UA</td></tr>
        <tr><td>Crônica (média semanal de 28 dias)</td><td class="n">${fmt(c.cronica)} UA</td></tr>
        <tr><td>Histórico</td><td class="n">${c.hist_dias} dias</td></tr>
        <tr><td>Sessões registradas</td><td class="n">${c.n}</td></tr>
      </tbody></table></div>
      <div class="nota" style="margin-top:12px">${c.hist_dias < 21
        ? `<b>Menos de 21 dias de histórico.</b> O ACWR ainda não diz nada — a crônica não teve tempo de se
           formar. O número aparece, mas não o use para decidir.`
        : `O ACWR é <b>apoio à decisão, não diagnóstico</b>. A literatura tem crítica metodológica séria a
           ele (Impellizzeri e col., 2020): leia junto com humor, sono e o que você vê na quadra.`}</div></div>

    <div class="cartao acc-carga"><header><h3>Carga dos últimos 7 dias</h3>
      <span class="sub">é a variação que gera a monotonia</span></header>
      <div class="spark">${c.diarias.map(v =>
        `<i style="height:${Math.max(2, v / maxD * 100)}%" title="${fmt(v)} UA"></i>`).join("")}</div>
      <div class="sub" style="margin-top:6px;display:flex;justify-content:space-between">
        <span>7 dias atrás</span><span>hoje</span></div>
      <div class="nota" style="margin-top:12px">Monotonia alta com carga alta é a combinação que a
      literatura associa a mais queixa: todo dia igual não deixa o corpo assimilar. Se a barra for um
      platô, varie — um dia leve de verdade vale mais que dois médios.</div></div>
  </div>

  <div class="cartao ${a.nivel === 2 ? "acc-risco" : a.nivel === 1 ? "acc-forca" : "acc-bom"}">
    <header><h3>Decisão de hoje: ${esc(nivel[0])}</h3></header>
    <div class="nota" style="--acc:${a.nivel === 2 ? "var(--crit)" : a.nivel === 1 ? "var(--warn)" : "var(--good)"}">
      <b>${esc(nivel[2])}</b></div>
    ${a.bandeiras.length ? `<div class="linha" style="margin-top:12px">
      ${a.bandeiras.map(([t, k]) => `<span class="pilula ${k}">${esc(t)}</span>`).join("")}</div>` : ""}
    <div class="rolagem" style="margin-top:12px"><table><thead><tr>
      <th>Componente da prontidão</th><th class="n">0–100</th></tr></thead><tbody>
      ${Object.entries(a.componentes).map(([k, v]) => `<tr>
        <td>${esc({sono: "Sono", alerta: "Alerta (KSS)", dor: "Dor muscular",
          humor: "Humor (TMD)", carga: "Carga (ACWR)"}[k] || k)}</td>
        <td class="n">${fmt(v)}</td></tr>`).join("")}
    </tbody></table></div>
    <div class="nota" style="margin-top:12px">Componente que falta é <b>excluído</b> da média, não contado
    como zero: quem não respondeu a BRUMS não é quem está com o humor péssimo.</div></div>

  <div class="cartao acc-humor"><header><h3>Humor · cada subescala contra a base dele</h3>
    <span class="sub">janela de 30 dias, sem incluir o dia de hoje</span></header>
    <div class="rolagem"><table><thead><tr>
      <th>Subescala</th><th class="n">Hoje</th><th class="n">Base (média ± dp)</th>
      <th class="n">Z</th><th>Faixa normal (quartis)</th></tr></thead><tbody>
      ${a.z.map(x => {
        const cor = x.z === null ? "var(--ink-4)" : Math.abs(x.z) >= 2 ? "var(--crit-i)"
          : Math.abs(x.z) >= 1.5 ? "var(--warn-i)" : Math.abs(x.z) >= 1 ? "var(--blue-2)" : "var(--good-i)";
        const f = x.faixa;
        const dentro = f && x.valor !== null ? (x.valor >= f.inf && x.valor <= f.sup) : null;
        return `<tr><td><b>${esc(x.subescala)}</b>${x.subescala === "Vigor"
            ? `<div class="sub">aqui, cair é que é ruim</div>` : ""}</td>
          <td class="n">${x.valor ?? "—"}</td>
          <td class="n sub">${x.media === null ? "—" : fmt(x.media, 1) + " ± " + fmt(x.desvio || 0, 1)}
            <div class="sub">${x.n} coletas</div></td>
          <td class="n"><b style="color:${cor};font-size:15px">${x.z === null ? "—" : sig(x.z, 2)}</b></td>
          <td>${f ? `<span class="sub mono">${fmt(f.q1)} a ${fmt(f.q3)}</span>
            ${dentro === null ? "" : dentro ? `<span class="pilula good">dentro</span>`
              : `<span class="pilula crit">fora</span>`}` : `<span class="sub">base curta</span>`}</td></tr>`;
      }).join("")}
    </tbody></table></div>
    <div class="nota" style="margin-top:12px">Precisa de <b>6 coletas com variação</b> para existir Z: uma
    base sem desvio não tem desvio padrão, e sem ele não há Z. A <b>faixa por quartis</b> é a segunda
    leitura, e a mais teimosa — um dia muito fora move a média, não move a mediana.</div></div>`;
};

/* ═══ TESTES ═══════════════════════════════════════════════════════════════ */
/* Bateria específica do voleibol. As referências são as do próprio elenco e do
   próprio atleta: norma internacional de salto varia demais por nível, sexo e
   posição para eu cravar um número aqui sem enganar. O que a literatura
   sustenta com firmeza é QUAIS medidas importam — e são estas. */
const BATERIA = [
  {t: "Salto", ex: "CMJ", un: "cm", d: "Salto com contramovimento. Índice de fadiga neuromuscular: queda de 10% da própria base é sinal."},
  {t: "Salto", ex: "SJ", un: "cm", d: "Squat jump, sem contramovimento. CMJ − SJ estima o aproveitamento elástico."},
  {t: "Salto", ex: "Impulsão de ataque", un: "cm", d: "Alcance de ataque menos alcance em pé. É o salto que decide ponto."},
  {t: "Salto", ex: "Impulsão de bloqueio", un: "cm", d: "Alcance de bloqueio menos alcance em pé, sem corrida."},
  {t: "1RM", ex: "Agachamento", un: "kg", d: "Referência do agachamento na prescrição por %1RM."},
  {t: "1RM", ex: "Supino", un: "kg", d: "Referência do supino."},
  {t: "1RM", ex: "Clean", un: "kg", d: "1RM técnico: a maior carga com recepção limpa."},
  {t: "1RM", ex: "Arranco", un: "kg", d: "Idem para o arranco."},
  {t: "Velocidade", ex: "Sprint 10 m", un: "s", d: "Aceleração — o deslocamento do voleibol é curto."},
  {t: "Velocidade", ex: "Sprint 20 m", un: "s", d: "Velocidade máxima atingida em quadra."},
  {t: "Agilidade", ex: "T-test", un: "s", d: "Mudança de direção com deslocamento lateral."},
];

TELAS.testes = async () => {
  if (!E.me) return semAtleta("lançar testes");
  const a = E.estado.atletas.find(x => String(x.id) === String(E.me));
  return cabeca("Testes de <em>campo</em>",
    "A bateria específica do voleibol. O que a literatura sustenta é quais medidas importam — a referência que vale é a evolução dele.") + `
  <div class="cartao acc-salto"><header><h3>Lançar um resultado</h3>
    <span class="sub">${esc(a?.apelido || "")}</span></header>
    <div class="formulario">
      <label class="c">Teste<select id="tsEx">
        ${BATERIA.map(b => `<option value="${esc(b.ex)}" data-t="${esc(b.t)}" data-u="${esc(b.un)}">
          ${esc(b.t)} · ${esc(b.ex)}</option>`).join("")}</select></label>
      <label class="c">Data<input type="date" id="tsData" value="${hoje()}"></label>
      <label class="c">Valor<input type="number" step="0.01" id="tsValor" inputmode="decimal"></label>
    </div>
    <div class="nota" style="margin-top:12px" id="tsDica">${esc(BATERIA[0].d)}</div>
    <div class="linha" style="margin-top:14px">
      <button class="btn primario" id="tsGravar">Gravar resultado</button></div>
    <div class="nota" style="margin-top:12px">O <b>1RM</b> lançado aqui é o que transforma os percentuais da
    prescrição em quilos na tela do atleta. Sem ele, o app mostra o % e deixa o atleta digitar a carga que
    usou — e depois oferece a última dele como ponto de partida.</div></div>

  <div class="cartao acc-tec"><header><h3>A bateria e por que cada item está nela</h3></header>
    <div class="rolagem"><table><thead><tr><th>Tipo</th><th>Teste</th><th>Unidade</th>
      <th>Para que serve</th></tr></thead><tbody>
      ${BATERIA.map(b => `<tr><td>${esc(b.t)}</td><td><b>${esc(b.ex)}</b></td>
        <td class="n">${esc(b.un)}</td><td style="white-space:normal">${esc(b.d)}</td></tr>`).join("")}
    </tbody></table></div>
    <div class="nota" style="margin-top:12px"><b>Por que não há tabela de norma internacional aqui.</b>
    Valores de referência de salto e força variam muito por nível competitivo, sexo, idade e posição —
    publicar uma tabela única daria a impressão de precisão que ela não tem. O que a revisão de atributos
    físicos do voleibol sustenta com firmeza é <i>quais medidas importam</i>, e são estas. A comparação que
    presta é a do atleta com ele mesmo ao longo da temporada, e a dele com o próprio elenco.</div></div>`;
};
TELAS.testes.depois = async () => {
  const sel = el("tsEx");
  sel.onchange = () => { el("tsDica").textContent = BATERIA.find(b => b.ex === sel.value)?.d || ""; };
  el("tsGravar").onclick = async () => {
    const o = sel.selectedOptions[0];
    const v = el("tsValor").value;
    if (!v) { aviso("Informe o valor medido.", "crit"); return; }
    try {
      await api("/api/testes", {method: "POST", body: JSON.stringify({
        atleta_id: +E.me, data: el("tsData").value, tipo: o.dataset.t,
        exercicio: sel.value, valor: +v, unidade: o.dataset.u})});
      aviso("Resultado gravado.", "good");
      el("tsValor").value = "";
    } catch (e) { aviso(e.message, "crit"); }
  };
};

/* ═══ ELENCO ═══════════════════════════════════════════════════════════════ */
TELAS.elenco = async () => {
  const at = E.estado.atletas;
  return cabeca("<em>Elenco</em>", "Quem está no grupo, o que cada ficha tem e o que falta medir.") + `
  <div class="cartao acc-bom"><header><h3>${at.length} atleta(s)</h3>
    <span class="sub">${at.filter(a => a.status === "Pendente").length} pendente(s)</span></header>
    ${at.length ? `<div class="rolagem"><table><thead><tr>
      <th>Atleta</th><th>Posição</th><th class="n">Estatura</th><th class="n">Massa</th>
      <th>Situação</th><th></th></tr></thead><tbody>
      ${at.map(a => `<tr><td><b>${esc(a.apelido)}</b><div class="sub">${esc(a.nome)}</div></td>
        <td>${esc(a.posicao || "—")}</td><td class="n">${a.estatura ? fmt(a.estatura) + " cm" : "—"}</td>
        <td class="n">${a.massa ? fmt(a.massa, 1) + " kg" : "—"}</td>
        <td><span class="pilula ${a.status === "Ativo" ? "good" : a.status === "Pendente" ? "warn" : ""}">${esc(a.status)}</span></td>
        <td style="white-space:nowrap">
          ${a.status !== "Ativo" ? `<button class="btn mini primario" data-ativa="${a.id}">Ativar</button>` : ""}
          ${a.status === "Ativo" ? `<button class="btn mini" data-inativa="${a.id}">Inativar</button>` : ""}
        </td></tr>`).join("")}
    </tbody></table></div>` : `<div class="vazio">Nenhum atleta ainda. Mande o link do cadastro — está na aba Início.</div>`}
  </div>

  <div class="cartao acc-forca"><header><h3>Configuração</h3></header>
    <div class="formulario">
      <label class="c largo">Equipe<input id="cfEquipe" value="${esc(E.estado.config.equipe)}"></label>
      <label class="c">Categoria<input id="cfCat" value="${esc(E.estado.config.categoria)}"></label>
      <label class="c">Início do macrociclo<input type="date" id="cfMacro" value="${esc(E.estado.config.macro_inicio)}"></label>
      <label class="c">PIN do preparador<input id="cfPin" value="${esc(E.estado.config.pin_treinador)}"></label>
      <label class="c">Cadastro<select id="cfLib">
        <option value="1"${E.estado.config.cadastro_liberado ? " selected" : ""}>Liberado — entra na hora</option>
        <option value="0"${!E.estado.config.cadastro_liberado ? " selected" : ""}>Com aprovação — você ativa</option>
      </select></label>
    </div>
    <div class="linha" style="margin-top:14px"><button class="btn primario" id="cfSalvar">Salvar</button></div>
    <div class="nota" style="margin-top:12px">O início do macrociclo tem de ser uma <b>segunda-feira</b>: é
    dele que saem todas as semanas e todo o gerador do Sistema.</div></div>`;
};
TELAS.elenco.depois = async () => {
  const mudar = async (id, status) => {
    try {
      await api("/api/atleta/status", {method: "POST", body: JSON.stringify({id: +id, status})});
      await carregar(); desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  };
  document.querySelectorAll("[data-ativa]").forEach(b => b.onclick = () => mudar(b.dataset.ativa, "Ativo"));
  document.querySelectorAll("[data-inativa]").forEach(b => b.onclick = () => mudar(b.dataset.inativa, "Inativo"));
  el("cfSalvar").onclick = async () => {
    try {
      await api("/api/config", {method: "POST", body: JSON.stringify({
        equipe: el("cfEquipe").value, categoria: el("cfCat").value,
        macro_inicio: el("cfMacro").value, pin_treinador: el("cfPin").value,
        cadastro_liberado: +el("cfLib").value})});
      E.pin = el("cfPin").value;
      localStorage.setItem("elase.pin", E.pin);
      await carregar(); aviso("Configuração salva.", "good"); desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  };
};

/* ═══ PRESCRIÇÃO ═══════════════════════════════════════════════════════════ */
TELAS.prescricao = async () => {
  const de = hoje(), ate = new Date(Date.now() + 28 * 864e5).toISOString().slice(0, 10);
  const ps = await api(`/api/prescricoes?de=${de}&ate=${ate}`);
  return cabeca("<em>Prescrição</em>", "O que está montado daqui para a frente. Gere o microciclo na aba Sistema e ajuste aqui.") + `
  <div class="cartao acc-forca"><header><h3>Próximos 28 dias</h3>
    <span class="pilula info">${ps.length} sessão(ões)</span></header>
    ${ps.length ? `<div class="rolagem"><table><thead><tr>
      <th>Data</th><th>Tipo</th><th>Objetivo</th><th class="n">Exercícios</th>
      <th class="n">Séries</th><th class="n">Min</th><th class="n">UA</th><th class="n">Contatos</th><th></th>
    </tr></thead><tbody>
      ${ps.map(p => `<tr>
        <td class="mono">${dBR(p.data)}<div class="sub">${esc(p.hora)}</div></td>
        <td>${esc(p.tipo)}</td>
        <td>${esc(p.objetivo)}<div class="sub">${esc(p.notas || "")}</div></td>
        <td class="n">${p.exercicios.length}</td><td class="n">${p.plano.series}</td>
        <td class="n">${p.plano.dur}</td><td class="n"><b>${p.plano.ua}</b></td>
        <td class="n">${p.plano.contatos || "—"}</td>
        <td><button class="btn mini perigo" data-del="${p.id}">Excluir</button></td></tr>`).join("")}
    </tbody></table></div>` : `<div class="vazio">Nada prescrito. Vá em <b>Sistema</b> e gere o microciclo.</div>`}
    <div class="nota" style="margin-top:12px">A <b>UA prevista</b> usa a PSE presumida do tipo de sessão. A
    que vale é a do check-out, com a PSE que o atleta informou — e o desvio entre as duas é informação: se a
    sessão de força sai sempre mais pesada do que você previu, a previsão é que está errada.</div></div>`;
};
TELAS.prescricao.depois = async () => {
  document.querySelectorAll("[data-del]").forEach(b => b.onclick = async () => {
    if (!confirm("Excluir esta sessão? Os registros que os atletas já fizeram continuam salvos.")) return;
    try {
      await api("/api/prescricoes/" + b.dataset.del, {method: "DELETE"});
      aviso("Sessão excluída.", "good"); desenhar();
    } catch (e) { aviso(e.message, "crit"); }
  });
};

/* ═══ SISTEMA ══════════════════════════════════════════════════════════════ */
const HORIZONTES = [[4, "4 semanas"], [8, "1 macrociclo"], [16, "2 macrociclos"],
                    [24, "3 macrociclos"], [52, "temporada"]];

TELAS.sistema = async () => {
  const s = E.estado;
  const de = E.sis.de || Math.max(1, s.semana);
  const h = E.sis.h || 8;
  const prev = await api("/api/sistema/previa", {method: "POST",
    body: JSON.stringify({de, ate: de + h - 1})});
  return cabeca("Sistema de <em>treinamento</em>",
    "Gera o microciclo semana após semana. Os blocos são um macrociclo, não a temporada — eles voltam ao começo sem teto.") + `
  <div class="cartao acc-lpo">
    <div class="linha" style="margin-bottom:14px">
      <label class="c" style="max-width:190px">Começar na semana
        <input type="number" id="sisDe" value="${de}" min="1"></label>
      <label class="c" style="max-width:220px">Horizonte
        <select id="sisH">${HORIZONTES.map(([v, r]) =>
          `<option value="${v}"${v === h ? " selected" : ""}>${r}</option>`).join("")}</select></label>
    </div>

    ${prev.sessoes.length ? `<div class="rolagem"><table><thead><tr>
      <th>Semana</th><th>Bloco</th><th class="n">Sessões</th><th class="n">Min</th>
      <th class="n">UA</th><th class="n">Contatos</th><th class="n">Alvo</th><th></th>
    </tr></thead><tbody>
      ${prev.resumo.map(r => {
        const d = r.contatos - r.alvo_contatos;
        const fora = Math.abs(d) > Math.max(8, r.alvo_contatos * 0.15);
        return `<tr><td><b>${r.semana}</b><div class="sub">ciclo ${r.ciclo} · ${r.posicao}</div></td>
          <td>${esc(r.bloco)}<div class="sub">${esc(r.micro)}</div></td>
          <td class="n">${r.sessoes}</td><td class="n">${r.min}</td>
          <td class="n"><b>${fmt(r.ua)}</b></td><td class="n">${r.contatos}</td>
          <td class="n sub">${r.alvo_contatos}</td>
          <td>${r.reteste ? `<span class="pilula info">reteste</span>` : ""}
              ${fora ? `<span class="pilula warn">${sig(d, 0)}</span>` : ""}</td></tr>`;
      }).join("")}
    </tbody></table></div>
    <div class="linha" style="margin-top:14px">
      <button class="btn primario" id="sisGerar">Gerar ${prev.sessoes.length} sessões</button>
      <span class="sub">semanas ${de} a ${de + h - 1}${prev.pulados.length
        ? ` · ${prev.pulados.length} dia(s) pulado(s) por já terem treino` : ""}</span></div>`
    : `<div class="vazio">Todas as datas desse intervalo já têm sessão prescrita.
       Escolha um horizonte maior ou comece mais adiante.</div>`}

    <div class="nota" style="margin-top:14px">Gerar <b>não apaga nada</b>: dia que já tem sessão é pulado.
    Depois de gerar, cada sessão continua editável — regerar não desfaz o seu ajuste.
    <br><br>A última sexta de cada macrociclo é um <b>reteste</b> de 1RM e salto. É ele que faz o ciclo
    seguinte valer mais: os mesmos 85% passam a significar mais quilos porque a referência subiu. Um sistema
    que repete o bloco sem retestar repete também a carga, e a temporada anda parada.</div></div>`;
};
TELAS.sistema.depois = async () => {
  el("sisDe").onchange = () => { E.sis.de = +el("sisDe").value; desenhar(); };
  el("sisH").onchange = () => { E.sis.h = +el("sisH").value; desenhar(); };
  const g = el("sisGerar");
  if (g) g.onclick = async () => {
    const de = +el("sisDe").value, h = +el("sisH").value;
    if (!confirm(`Gerar as sessões das semanas ${de} a ${de + h - 1}?`)) return;
    g.disabled = true;
    try {
      const r = await api("/api/sistema/gerar", {method: "POST",
        body: JSON.stringify({de, ate: de + h - 1})});
      aviso(`${r.criadas} sessões prescritas.`, "good");
      desenhar();
    } catch (e) { aviso(e.message, "crit"); g.disabled = false; }
  };
};

/* ═══ SQL ══════════════════════════════════════════════════════════════════ */
const EXEMPLOS = [
  ["Carga por atleta na semana",
   "SELECT a.apelido, ROUND(SUM(s.carga_ua)) AS ua, COUNT(*) AS sessoes\nFROM sessoes s JOIN atletas a ON a.id = s.atleta_id\nWHERE s.data >= date('now','-7 day') AND s.check_out IS NOT NULL\nGROUP BY a.id ORDER BY ua DESC"],
  ["Tonelagem por exercício",
   "SELECT pe.nome, ROUND(SUM(se.carga * se.reps)) AS kg, COUNT(*) AS series\nFROM series se\nJOIN sessoes s ON s.id = se.sessao_id\nJOIN presc_exercicios pe ON pe.prescricao_id = s.prescricao_id AND pe.ordem = se.exercicio\nWHERE se.feita = 1\nGROUP BY pe.nome ORDER BY kg DESC"],
  ["Humor: TMD por coleta",
   "SELECT a.apelido, b.data,\n  SUM(CASE WHEN b.subescala <> 'Vigor' THEN b.valor ELSE 0 END)\n  - SUM(CASE WHEN b.subescala = 'Vigor' THEN b.valor ELSE 0 END) + 100 AS tmd\nFROM brums b JOIN atletas a ON a.id = b.atleta_id\nWHERE b.momento = 'pre'\nGROUP BY b.atleta_id, b.data ORDER BY b.data DESC"],
  ["Adesão: prescrito × realizado",
   "SELECT p.data, p.tipo, COUNT(s.id) AS fizeram,\n  (SELECT COUNT(*) FROM atletas WHERE status='Ativo') AS elenco\nFROM prescricoes p LEFT JOIN sessoes s ON s.prescricao_id = p.id AND s.check_out IS NOT NULL\nWHERE p.data <= date('now')\nGROUP BY p.id ORDER BY p.data DESC LIMIT 30"],
];

TELAS.sql = async () => cabeca("Console <em>SQL</em>",
  "O banco é SQLite e está aberto para leitura. Toda conta que o app mostra você pode refazer aqui e conferir.") + `
  <div class="cartao acc-tec">
    <label class="c">Consulta
      <textarea id="sqlTxt" rows="8" style="font-family:ui-monospace,monospace;font-size:13px;resize:vertical"
      >${esc(E.sql)}</textarea></label>
    <div class="linha" style="margin-top:12px">
      <button class="btn primario" id="sqlRodar">Rodar</button>
      ${EXEMPLOS.map((e, i) => `<button class="btn mini" data-ex="${i}">${esc(e[0])}</button>`).join("")}
    </div>
    <div class="nota" style="margin-top:12px">Só <b>leitura</b>. A conexão é aberta em modo somente leitura e
    qualquer INSERT, UPDATE ou DROP é recusado antes de chegar ao banco — duas travas, porque uma só não
    basta para algo que fica exposto numa tela.</div>
    <div id="sqlSaida" style="margin-top:14px"></div>
  </div>`;
TELAS.sql.depois = async () => {
  const rodar = async () => {
    E.sql = el("sqlTxt").value;
    try {
      const r = await api("/api/sql", {method: "POST", body: JSON.stringify({sql: E.sql})});
      el("sqlSaida").innerHTML = r.n ? `<div class="rolagem"><table><thead><tr>
        ${r.colunas.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>
        ${r.linhas.map(l => `<tr>${l.map(v => `<td class="${typeof v === "number" ? "n" : ""}">${esc(v)}</td>`).join("")}</tr>`).join("")}
        </tbody></table></div><div class="sub" style="margin-top:8px">${r.n} linha(s)${r.n === 1000 ? " — cortado em 1000" : ""}</div>`
        : `<div class="vazio">A consulta rodou e não devolveu nenhuma linha.</div>`;
    } catch (e) {
      el("sqlSaida").innerHTML = `<div class="nota" style="--acc:var(--crit)">${esc(e.message)}</div>`;
    }
  };
  el("sqlRodar").onclick = rodar;
  document.querySelectorAll("[data-ex]").forEach(b => b.onclick = () => {
    el("sqlTxt").value = EXEMPLOS[+b.dataset.ex][1];
    E.sql = el("sqlTxt").value;
    rodar();
  });
};

/* ── Partida ─────────────────────────────────────────────────────────────── */
(async function () {
  try {
    await carregar();
    const h = location.hash.slice(1);
    if (ABAS.some(a => a.id === h)) E.aba = h;
    await desenhar();
  } catch (e) {
    el("pagina").innerHTML = `<div class="cartao acc-risco">
      <header><h3>Não consegui falar com o servidor</h3></header>
      <div class="nota" style="--acc:var(--crit)">${esc(e.message)}<br><br>
      O servidor está rodando? No terminal: <code>python3 elase.py</code></div></div>`;
  }
})();
