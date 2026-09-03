// Gera os documentos iniciais do banco do app ELASE.
const fs = require("fs"), path = require("path");
const OUT = path.join(__dirname, "seed");
fs.rmSync(OUT, {recursive:true, force:true});
["config","atletas","prescricao","execucao","wellness","testes","antropometria"]
  .forEach(d => fs.mkdirSync(path.join(OUT,d), {recursive:true}));

let seed = 20260904;
const rnd = () => { seed = (seed*1103515245 + 12345) & 0x7fffffff; return seed/0x7fffffff; };
const between = (a,b) => a + rnd()*(b-a);
const pick = a => a[Math.floor(rnd()*a.length)];
const r1 = (v,d=1) => +v.toFixed(d);
const addD = (s,n)=>{const d=new Date(s+"T12:00:00");d.setDate(d.getDate()+n);return d.toISOString().slice(0,10);};
const w = (p,o) => fs.writeFileSync(path.join(OUT,p+".json"), JSON.stringify(o,null,1));

const HOJE = "2026-09-03";
const MACRO = "2026-07-06";          // segunda-feira, âncora das semanas

/* ── ELENCO ─────────────────────────────────────────────────────────────── */
const ELENCO = [
 ["Rafael Monteiro Alves","Rafa","1998-03-14","Levantador",5,196,88,253,325,308,"Destro","Esquerda",11],
 ["Diego Salgado Ferraz","Diego","1996-08-02","Oposto",12,202,95,261,344,326,"Canhoto","Esquerda",12],
 ["Lucas Prado Bittencourt","Lucas","2000-01-27","Ponteiro (Ponta)",7,198,89,255,336,318,"Destro","Esquerda",13],
 ["Bruno Rezende Camargo","Bruninho","1999-11-05","Ponteiro (Ponta)",9,197,87,254,333,315,"Destro","Esquerda",12],
 ["Thiago Nogueira Vasques","Thiago","1995-05-19","Central",4,205,99,265,349,333,"Destro","Direita",10],
 ["Matheus Caldeira Lins","Matheus","2001-09-08","Central",15,203,95,262,345,329,"Destro","Esquerda",14],
 ["Felipe Andrade Rocha","Felipão","2003-02-11","Líbero",2,184,78,238,299,281,"Destro","Direita",12],
 ["Gustavo Peixoto Maia","Gu","1997-07-23","Ponteiro (Ponta)",11,199,91,257,338,320,"Destro","Esquerda",11],
 ["Vinícius Barreto Duarte","Vini","2002-12-03","Levantador",6,192,84,248,318,302,"Destro","Esquerda",13],
 ["André Luiz Sampaio","Dedé","1994-04-30","Oposto",18,201,97,260,343,325,"Destro","Esquerda",10],
 ["Pedro Henrique Coutinho","PH","2004-06-17","Central",3,204,93,263,346,330,"Destro","Direita",13],
 ["Caio Fernandes Bastos","Caio","2001-10-09","Líbero",1,186,79,240,302,284,"Canhoto","Direita",12],
];
const atletas = ELENCO.map((a,i)=>({
  id:"atl_"+String(i+1).padStart(2,"0"), nome:a[0], apelido:a[1], nasc:a[2], posicao:a[3], camisa:a[4],
  estatura:a[5], massa:a[6], alcancePe:a[7], alcanceAtaque:a[8], alcanceBloqueio:a[9],
  dominancia:a[10], pernaImpulsao:a[11], anosPratica:a[12],
  escolaridade: i%3===0 ? "Superior completo" : "Superior em andamento",
  status: i===3 ? "Lesionado" : "Ativo",
  emergencia:"Responsável · (00) 90000-00"+String(i+1).padStart(2,"0")
}));
atletas.forEach(a => w("atletas/"+a.id, a));

/* ── CONFIGURAÇÃO E PERIODIZAÇÃO ────────────────────────────────────────── */
const BIB = [
 ["Agachamento profundo","Força","Agachamento profundo"],["Agachamento frontal","Força","Agachamento frontal"],
 ["Stiff com barra","Força","Stiff com barra"],["Levantamento terra","Força","Levantamento terra"],
 ["Supino sentado","Força","Supino sentado"],["Supino deitado com halteres","Força",null],
 ["Remada serrote","Força","Remada serrote"],["Remada unilateral na polia","Força",null],
 ["Puxada alta","Força",null],["Pullover deitado com haltere","Força",null],
 ["Afundo lateral sem passada","Força",null],["Afundo frontal sem passada","Força",null],
 ["Flexão de joelho unilateral","Força",null],["Elevação de calcanhares","Força",null],
 ["Power clean a partir do joelho","LPO","Power clean"],["Power clean","LPO","Power clean"],
 ["Clean pull","LPO","Clean pull"],["Snatch pull / Hang high pull","LPO","Clean pull"],
 ["Jump shrug","LPO","Power clean"],
 ["Agachamento com salto sob carga (jump squat)","Potência","Agachamento profundo"],
 ["Arremesso de bola","Potência",null],["Salto no caixote","Pliometria",null],
 ["Drop jump 40 cm","Pliometria",null],["Saltos consecutivos sobre barreiras","Pliometria",null],
 ["Salto unilateral com sobrepeso","Pliometria",null],
 ["Nórdico de isquiotibiais (excêntrico)","Força",null],["Rotadores do ombro com elástico","Força",null],
 ["Mobilidade de tornozelo e quadril","Recuperação",null],
 ["Abdominal reto com braços esticados","Força",null],["Dorsal perdigueiro","Força",null],
 ["Abdominal cruzado esticado","Força",null],["Dorsal reto","Força",null],
 ["Complexo I (K1) — recepção, levantamento e ataque","Técnico-Tático",null],
 ["Complexo II (K2) — bloqueio, defesa e contra-ataque","Técnico-Tático",null],
 ["Jogo 6x6 com pontuação diferenciada","Técnico-Tático",null],
 ["Alongamento e liberação miofascial","Recuperação",null],
 ["Sprints de 10 e 20 m com mudança de direção","Potência",null],
];
const BLOCOS = [
 [1,"Acumulação","Incorporação","Adaptação anatômica e técnica de LPO",0.75,0.62,60],
 [2,"Acumulação","Ordinário","Força máxima de base",0.88,0.72,90],
 [3,"Acumulação","CHOQUE","Pico de volume da acumulação",1.00,0.78,120],
 [4,"Descarga","Recuperativo","Assimilação e supercompensação",0.45,0.66,45],
 [5,"Transmutação","Ordinário","Força máxima",0.75,0.85,90],
 [6,"Transmutação","Ordinário","Força-velocidade",0.70,0.90,110],
 [7,"Transmutação","CHOQUE","Sobrecarga concentrada de potência",0.85,0.93,140],
 [8,"Realização","Polimento","Expressão de potência",0.42,0.95,70],
];
w("config/app",{
  equipe:"ELASE Voleibol Masculino", categoria:"Adulto", temporada:"2026", macroInicio:MACRO,
  blocos: BLOCOS.map(b=>({semana:b[0],bloco:b[1],micro:b[2],enfase:b[3],volume:b[4],intensidade:b[5],plio:b[6]})),
  exercicios: BIB.map(b=>({nome:b[0],grupo:b[1],ref1rm:b[2]}))
});

/* ── TESTES E ANTROPOMETRIA ─────────────────────────────────────────────── */
const F1RM = {"Agachamento profundo":1.72,"Agachamento frontal":1.36,"Stiff com barra":1.46,
  "Levantamento terra":2.02,"Supino sentado":1.06,"Remada serrote":0.56,"Power clean":1.06,"Clean pull":1.32};
const DATAS_T = ["2026-07-07","2026-08-25"];
atletas.forEach((a,ai)=>{
  const itens=[]; const cmjBase = between(46,57);
  DATAS_T.forEach((d,g)=>{
    Object.entries(F1RM).forEach(([ex,f])=>
      itens.push({data:d,tipo:"1RM",exercicio:ex,unidade:"kg",
        valor: Math.round(a.massa*f*between(0.98,1.02)*(1+g*0.05)/2.5)*2.5}));
    const cmj = r1(cmjBase + g*between(1.4,3.2));
    itens.push({data:d,tipo:"Salto",exercicio:"CMJ",valor:cmj,unidade:"cm"});
    itens.push({data:d,tipo:"Salto",exercicio:"Squat jump",valor:r1(cmj-between(3,5)),unidade:"cm"});
    itens.push({data:d,tipo:"Salto",exercicio:"Drop jump 40 cm",valor:r1(cmj-between(1,3)),unidade:"cm"});
    itens.push({data:d,tipo:"Salto",exercicio:"Salto de ataque",valor:r1(a.alcanceAtaque-a.alcancePe+g*2),unidade:"cm"});
    itens.push({data:d,tipo:"Velocidade",exercicio:"Sprint 10 m",valor:r1(between(1.72,1.90)-g*0.03,2),unidade:"s"});
    itens.push({data:d,tipo:"Agilidade",exercicio:"T-Test",valor:r1(between(9.2,10.2)-g*0.15,2),unidade:"s"});
    itens.push({data:d,tipo:"Potência",exercicio:"Potência de pico (CMJ)",
      valor:Math.round(60.7*cmj+45.3*a.massa-2055),unidade:"W"});
  });
  w("testes/"+a.id,{atletaId:a.id,itens});

  const avaliacoes = DATAS_T.map((d,g)=>{
    const massa=r1(a.massa+(g?between(-1.5,0.8):0));
    const pg=r1(between(8.5,13.5)-g*0.7);
    return {data:d,massa,estatura:a.estatura,pctGordura:pg,massaGorda:r1(massa*pg/100),
      massaMagra:r1(massa*(1-pg/100)),imc:r1(massa/Math.pow(a.estatura/100,2)),
      dobras:{triceps:r1(between(7,11)),subescapular:r1(between(9,13)),suprailiaca:r1(between(8,14)),
        abdominal:r1(between(10,18)),coxa:r1(between(9,15))},obs:g?"Meio da temporada":"Pré-temporada"};
  });
  w("antropometria/"+a.id,{atletaId:a.id,avaliacoes});
});
const rm = (aid,ex)=>{ const t=JSON.parse(fs.readFileSync(path.join(OUT,"testes",aid+".json")));
  const it=t.itens.filter(i=>i.tipo==="1RM"&&i.exercicio===ex).sort((x,y)=>x.data.localeCompare(y.data));
  return it.length?it[it.length-1].valor:0; };

/* ── PRESCRIÇÃO ─────────────────────────────────────────────────────────── */
const SESSAO_A = [
 ["Mobilidade de tornozelo e quadril","Recuperação",1,"8 por exercício",null,null,30,null],
 ["Power clean a partir do joelho","LPO",5,"3",0.75,"Power clean",180,"Parar a série se a barra desacelerar"],
 ["Agachamento profundo","Força",5,"5",0.80,"Agachamento profundo",180,"Exercício-âncora do bloco"],
 ["Stiff com barra","Força",4,"6",0.70,"Stiff com barra",120,"Excêntrica de 3 s"],
 ["Afundo lateral sem passada","Força",3,"8",null,null,90,null],
 ["Nórdico de isquiotibiais (excêntrico)","Força",3,"6",null,null,90,"2× por semana no bloco"],
 ["Abdominal reto com braços esticados","Força",3,"25",null,null,45,null],
];
const SESSAO_B = [
 ["Rotadores do ombro com elástico","Força",3,"15",null,null,60,"Antes de qualquer trabalho de ombro"],
 ["Agachamento com salto sob carga (jump squat)","Potência",4,"4",0.25,"Agachamento profundo",180,"Velocidade acima de 1,0 m/s"],
 ["Drop jump 40 cm","Pliometria",5,"5",null,null,120,"Contato mínimo com o solo"],
 ["Saltos consecutivos sobre barreiras","Pliometria",4,"5",null,null,120,null],
 ["Supino deitado com halteres","Força",4,"8",0.75,"Supino sentado",120,null],
 ["Remada unilateral na polia","Força",4,"8",null,null,120,null],
 ["Arremesso de bola","Potência",3,"8",null,null,90,null],
];
const SESSAO_C = [
 ["Mobilidade de tornozelo e quadril","Recuperação",1,"8 por exercício",null,null,30,null],
 ["Snatch pull / Hang high pull","LPO",4,"3",0.70,"Clean pull",150,null],
 ["Agachamento frontal","Força",4,"5",0.65,"Agachamento frontal",150,null],
 ["Elevação de calcanhares","Força",3,"8",null,null,60,"Descida lenta de 3 s"],
 ["Afundo frontal sem passada","Força",3,"8",null,null,90,null],
 ["Salto unilateral com sobrepeso","Pliometria",3,"5",null,null,120,null],
 ["Sprints de 10 e 20 m com mudança de direção","Potência",6,"1",null,null,120,"Só em semanas sem choque"],
];
const SESSAO_TEC = [
 ["Complexo I (K1) — recepção, levantamento e ataque","Técnico-Tático",1,"20 tentativas",null,null,90,"Meta de 60% de side-out"],
 ["Complexo II (K2) — bloqueio, defesa e contra-ataque","Técnico-Tático",1,"20 séries",null,null,60,null],
 ["Jogo 6x6 com pontuação diferenciada","Técnico-Tático",3,"sets a 15",null,null,120,null],
];
const ex = t => t.map(e=>({nome:e[0],grupo:e[1],series:e[2],reps:e[3],pctRM:e[4],ref1rm:e[5],pausa:e[6],obs:e[7],carga:null}));

// A sessão que o treinador citou, exatamente como pedida
const SESSAO_04 = ex([
 ["Supino sentado","Força",4,"5",0.85,"Supino sentado",180,"Carga alta, foco em velocidade de barra"],
 ["Levantamento terra","Força",4,"4",0.85,"Levantamento terra",210,"Interromper se a técnica cair"],
 ["Agachamento profundo","Força",5,"4",0.85,"Agachamento profundo",180,"Exercício-âncora"],
 ["Stiff com barra","Força",4,"6",0.72,"Stiff com barra",120,"Excêntrica de 3 s"],
]);

const presc=[]; let ns=0;
const addP = (data,hora,tipo,objetivo,bloco,exs,notas) => {
  const id="ses_"+String(++ns).padStart(3,"0");
  presc.push({id,data,hora,tipo,objetivo,bloco,alvo:"equipe",notas:notas||"",exercicios:exs});
  return id;
};
// 8 semanas: A (seg), B (qua), C (sex) + técnico (ter/qui)
for(let sem=0; sem<9; sem++){
  const seg = addD(MACRO, sem*7);
  if(seg > addD(HOJE,7)) break;
  const b = BLOCOS[Math.min(sem,7)][1];
  addP(seg,          "09:00","Força","Força máxima",b,ex(SESSAO_A));
  addP(addD(seg,1),  "17:00","Técnico-Tático","Técnico-tático",b,ex(SESSAO_TEC));
  addP(addD(seg,2),  "09:00","Potência","Potência",b,ex(SESSAO_B));
  addP(addD(seg,3),  "17:00","Técnico-Tático","Técnico-tático",b,ex(SESSAO_TEC));
  addP(addD(seg,4),  "09:00","LPO","Força-velocidade",b,ex(SESSAO_C));
}
// substitui a sessão de 04/09/2026 pela pedida
const i04 = presc.findIndex(p=>p.data==="2026-09-04");
if(i04>=0){ presc[i04]={...presc[i04],hora:"09:00",tipo:"Força",objetivo:"Força máxima",
  exercicios:SESSAO_04, notas:"Bloco de realização — cargas altas, volume baixo."}; }
else { addP("2026-09-04","09:00","Força","Força máxima","Realização",SESSAO_04,
  "Bloco de realização — cargas altas, volume baixo."); }
presc.forEach(p => w("prescricao/"+p.id, p));

/* ── EXECUÇÃO E WELLNESS ────────────────────────────────────────────────── */
const BRUMS = {"Tensão":["Apreensivo","Nervoso","Ansioso","Preocupado"],
 "Depressão":["Deprimido","Infeliz","Desanimado","Triste"],"Raiva":["Irritado","Zangado","Mal-humorado","Com raiva"],
 "Vigor":["Animado","Com energia","Ativo","Disposto"],"Fadiga":["Esgotado","Sonolento","Cansado","Sem energia"],
 "Confusão":["Confuso","Indeciso","Desnorteado","Inseguro"]};
const mkBrums = (vigor,fadiga,ruim) => { const o={};
  Object.entries(BRUMS).forEach(([g,its])=>its.forEach(it=>{
    o[it] = g==="Vigor" ? Math.max(0,Math.min(4,Math.round(vigor+between(-.6,.6))))
          : g==="Fadiga" ? Math.max(0,Math.min(4,Math.round(fadiga+between(-.6,.6))))
          : Math.max(0,Math.min(4,Math.round(ruim+between(-.5,.5)))); }));
  return o; };
const tmd = b => { const s={}; Object.entries(BRUMS).forEach(([g,its])=>s[g]=its.reduce((a,i)=>a+b[i],0));
  return s["Tensão"]+s["Depressão"]+s["Raiva"]+s["Fadiga"]+s["Confusão"]-s["Vigor"]+100; };

const exec={}, well={};
atletas.forEach(a=>{
  presc.filter(p=>p.data<HOJE).forEach(p=>{
    if(a.status==="Lesionado" && p.data>="2026-08-24") return;
    if(rnd()<0.07) return;                       // faltas
    const mes=p.data.slice(0,7);
    const k=a.id+"__"+mes;
    exec[k]=exec[k]||{atletaId:a.id,mes,sessoes:{}};
    const semIdx = Math.floor((new Date(p.data)-new Date(MACRO))/6048e5);
    const B = BLOCOS[Math.min(Math.max(semIdx,0),7)];
    const choque = B[2]==="CHOQUE";
    const dur = p.tipo==="Técnico-Tático" ? Math.round(between(85,105)) : Math.round(between(58,82));
    const pse = Math.max(2,Math.min(10, Math.round((p.tipo==="Técnico-Tático"?7:6.4) + (choque?1.3:0) + between(-1,1))));
    const min = String(+p.hora.slice(3) + Math.floor(rnd()*7)).padStart(2,"0");
    const inicio = new Date(`${p.data}T${p.hora.slice(0,2)}:${min}:00-03:00`);
    const fim = new Date(inicio.getTime()+dur*60000);
    const series=[]; let ton=0, contatos=0;
    p.exercicios.forEach((e,i)=>{
      const base = e.pctRM && e.ref1rm ? Math.round(e.pctRM*rm(a.id,e.ref1rm)*2)/2 : 0;
      for(let s=1;s<=e.series;s++){
        const reps = parseInt(e.reps,10) || 0;
        const carga = base ? Math.round((base*between(0.97,1.03))*2)/2 : null;
        series.push({ex:i,s,carga,reps:reps||null,rir:base?Math.max(0,Math.round(between(0,3))):null,
          vel:base?r1(between(0.42,0.92),2):null,ok:true});
        if(carga && reps) ton += carga*reps;
        if(e.grupo==="Pliometria" && reps) contatos += reps;
      }
    });
    const vigorPre = choque ? between(1.6,2.4) : between(2.2,3.1);
    const bp = mkBrums(vigorPre, choque?between(1.4,2.2):between(0.7,1.5), between(0.2,1.0));
    const bo = mkBrums(Math.max(0,vigorPre-between(0.4,1.2)),
                       Math.min(4,(choque?2.4:1.4)+between(0.5,1.4)), between(0.3,1.2));
    exec[k].sessoes[p.id]={ sid:p.id, data:p.data, tipo:p.tipo, objetivo:p.objetivo, bloco:p.bloco,
      semana:semIdx+1, checkIn:inicio.toISOString(), checkOut:fim.toISOString(), durMin:dur,
      pse, cargaUA:dur*pse, tonelagem:Math.round(ton), contatos, series,
      brumsPre:bp, tmdPre:tmd(bp), brumsPos:bo, tmdPos:tmd(bo),
      sono:{horas:r1(between(6.2,8.6)),qualidade:Math.round(between(3,5)),latencia:Math.round(between(8,32))},
      kssPre:Math.round(between(2,5)), kssPos:Math.round(between(4,8)),
      estresse:Math.round(between(1,5)), dorPre:Math.round(between(0,4)), dorPos:Math.round(between(1,6)),
      obs: rnd()<0.12 ? "Leve incômodo no ombro direito no supino." : "" };
    const wk=a.id+"__"+mes;
    well[wk]=well[wk]||{atletaId:a.id,mes,dias:{}};
    well[wk].dias[p.data]={sono:Math.round(between(3,5)),horas:r1(between(6.2,8.6)),
      estresse:Math.round(between(1,5)),dor:Math.round(between(0,4)),
      kss:Math.round(between(2,5)),tmd:tmd(bp)};
  });
});
Object.entries(exec).forEach(([k,v])=>w("execucao/"+k,v));
Object.entries(well).forEach(([k,v])=>w("wellness/"+k,v));

const conta = d => fs.readdirSync(path.join(OUT,d)).length;
console.log("documentos gerados:",
  ["config","atletas","prescricao","execucao","wellness","testes","antropometria"]
    .map(d=>`${d}=${conta(d)}`).join("  "),
  "\ntotal =", ["config","atletas","prescricao","execucao","wellness","testes","antropometria"]
    .reduce((a,d)=>a+conta(d),0));
