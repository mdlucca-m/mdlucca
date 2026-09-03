# ============================================================================
# 18) BLOCO BASE — 8 semanas de periodização em blocos (força máxima e potência)
# ============================================================================
wsB = wb.create_sheet("Bloco Base")
banner(wsB, "PERIODIZAÇÃO EM BLOCOS — 2 MESES DE PERÍODO DE BASE",
       "Acumulação → Transmutação → Realização, com microciclos de CHOQUE nas semanas 3 e 7 e descarga na semana 4. "
       "Foco em força máxima, força explosiva com movimentos de LPO, agachamento e pliometria.", 18, "9C0006")
larguras(wsB, {"A":8,"B":13,"C":15,"D":17,"E":34,"F":10,"G":11,"H":15,"I":11,"J":26,"K":14,"L":11,
               "M":13,"N":18,"O":11,"P":12,"Q":12,"R":40})

secao(wsB, 4, "PARÂMETROS DO BLOCO", 18, 1)
BL_ID = [("Início do bloco (2ª feira)", date(2026, 9, 7)), ("Sessões de força por semana", 3),
         ("Sessões de quadra por semana", 5), ("Atletas no bloco", 12)]
for i, (lab, val) in enumerate(BL_ID):
    rotulo(wsB, 5 + i, 1, lab)
    entrada(wsB, 5 + i, 3, val, NF_DATE if isinstance(val, date) else '0', largura_merge=2)
wsB.merge_cells(start_row=5, start_column=6, end_row=8, end_column=18)
obj = wsB.cell(5, 6,
    "OBJETIVO DO BLOCO — elevar a força máxima de membros inferiores e a taxa de produção de força, criando a base "
    "sobre a qual a potência será expressa nos blocos competitivos.\n"
    "LÓGICA — a periodização em blocos concentra poucas capacidades por vez, em vez de desenvolver muitas ao mesmo "
    "tempo (Issurin, 2010; Stone et al., 2021). Estudos com esportes coletivos mostram vantagem dos blocos sobre a "
    "periodização tradicional em força, potência e salto (Rønnestad et al., 2018; Manchado et al., 2017).\n"
    "CHOQUE — as semanas 3 e 7 concentram a carga deliberadamente para induzir overreaching funcional; espera-se "
    "queda transitória do CMJ nessas semanas, com supercompensação após a descarga (Micke et al., 2026). MONITORE o "
    "CMJ e o wellness nessas semanas: queda de CMJ acima de 10% por mais de 5 dias exige reduzir a carga.")
obj.font = Font(name=F, size=9, color=NAVY)
obj.fill = PatternFill("solid", fgColor=LIGHT)
obj.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
obj.border = BORDER

secao(wsB, 10, "MATRIZ SEMANA A SEMANA", 18, 1)
BL_H = ["Semana","Data Início","Bloco","Microciclo","Ênfase Principal","Sessões de Força","Séries MMII/Sessão",
        "Agachamento (sér.×reps)","%1RM Agach.","Exercício de LPO","LPO (sér.×reps)","%1RM LPO",
        "Pliometria (contatos/sem)","Intensidade Pliométrica","Índice de Volume","Índice de Intensidade",
        "ACWR Alvo","O que monitorar nesta semana"]
cab_tabela(wsB, 11, BL_H)
BL_F = 12
BLOCO_8 = [
 (1,"Acumulação","Incorporação","Adaptação anatômica + técnica de LPO",3,13,"4 × 8",0.65,
  "Power clean a partir do joelho (técnica)","5 × 3",0.55,60,"Baixa (solo, CMJ e saltos horizontais)",0.75,0.62,1.00,
  "Qualidade técnica do power clean e da aterrissagem. Sem busca de carga."),
 (2,"Acumulação","Ordinário","Força máxima de base",3,15,"4 × 6",0.75,
  "Clean pull","4 × 4",0.70,90,"Baixa a média (saltos sobre barreiras 40 cm)",0.88,0.72,1.10,
  "Velocidade média no agachamento a 75% ≥ 0,62 m/s. PSE das sessões de força entre 6 e 7."),
 (3,"Acumulação","CHOQUE","Pico de volume da fase de acumulação",4,18,"5 × 5",0.80,
  "Power clean","5 × 3",0.75,120,"Média (barreiras 50 cm + salto no caixote)",1.00,0.78,1.30,
  "SEMANA DE CHOQUE — espere queda de CMJ e piora do Hooper. Monitore diariamente e não some carga de quadra."),
 (4,"Descarga","Recuperativo","Assimilação e supercompensação",2,8,"3 × 5",0.70,
  "Técnica leve (hang high pull)","3 × 3",0.60,45,"Baixa (qualidade, volume reduzido)",0.45,0.66,0.75,
  "Retorno do CMJ ao valor da semana 1 ou acima. Se não voltar, prolongue a descarga."),
 (5,"Transmutação","Ordinário","Força máxima",3,13,"5 × 4",0.85,
  "Power clean","5 × 2",0.82,90,"Média (drop jump 40 cm)",0.75,0.85,1.10,
  "Reteste indireto do 1RM pela velocidade. Ganho esperado de 3 a 6% no agachamento."),
 (6,"Transmutação","Ordinário","Força-velocidade",3,12,"4 × 3",0.88,
  "Clean pull (carga supramáxima)","4 × 3",0.95,110,"Média a alta (drop jump 40–50 cm + unilaterais)",0.70,0.90,1.15,
  "Introduzir jump squat a 30% 1RM. Velocidade média do jump squat ≥ 1,0 m/s."),
 (7,"Transmutação","CHOQUE","Sobrecarga concentrada de potência",4,15,"4 × 3 (cluster 2+2)",0.90,
  "Power clean","6 × 2",0.88,140,"Alta (drop jump 50 cm + saltos com sobrecarga)",0.85,0.93,1.45,
  "SEGUNDA SEMANA DE CHOQUE. ACWR chega a ~1,45 de propósito; reduza o volume de saltos de quadra para compensar."),
 (8,"Realização","Polimento","Expressão de potência",3,9,"3 × 2",0.92,
  "Power clean","4 × 1–2",0.90,70,"Alta qualidade, volume baixo (CMJ e DJ máximos)",0.42,0.95,0.85,
  "Reteste de CMJ, salto de ataque e 1RM. Espera-se o pico do bloco no fim desta semana."),
]
for i, w in enumerate(BLOCO_8):
    r = BL_F + i
    (sem, bloco, micro, enf, ses, ser, agach, pagach, lpo, slpo, plpo, plio, iplio, vol, inten, acwr, mon) = w
    wsB.cell(r, 1, sem)
    wsB.cell(r, 2, '=IF($C$5="","",$C$5+($A{}-1)*7)'.format(r))
    for c, v in ((3,bloco),(4,micro),(5,enf),(6,ses),(7,ser),(8,agach),(9,pagach),(10,lpo),(11,slpo),
                 (12,plpo),(13,plio),(14,iplio),(15,vol),(16,inten),(17,acwr),(18,mon)):
        wsB.cell(r, c, v)
corpo_tabela(wsB, BL_F, BL_F + 7, 1, 18)
for i in range(8):
    r = BL_F + i
    choque = wsB.cell(r, 4).value == "CHOQUE"
    desc = wsB.cell(r, 3).value == "Descarga"
    base = RED if choque else ("DDEBF7" if desc else (LIGHT if i % 2 == 0 else LIGHT2))
    for c in range(1, 19):
        wsB.cell(r, c).fill = PatternFill("solid", fgColor=base)
        wsB.cell(r, c).font = Font(name=F, size=9, bold=(c in (1, 3, 4)),
                                   color=RED_T if choque else NAVY2)
    for c in (5, 10, 14, 18):
        wsB.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)
    wsB.cell(r, 2).number_format = NF_DATE
    for c in (9, 12, 15, 16):
        wsB.cell(r, c).number_format = NF_PCT
    wsB.cell(r, 17).number_format = NF_DEC
    wsB.row_dimensions[r].height = 34
tot = BL_F + 8
for c in range(1, 19):
    wsB.cell(tot, c).fill = PatternFill("solid", fgColor=NAVY2); wsB.cell(tot, c).border = BORDER
    wsB.cell(tot, c).font = Font(name=F, size=9, bold=True, color=WHITE)
    wsB.cell(tot, c).alignment = Alignment(horizontal="center", vertical="center")
wsB.cell(tot, 1, "TOTAL").alignment = Alignment(horizontal="left", vertical="center", indent=1)
wsB.cell(tot, 6, "=SUM(F{}:F{})".format(BL_F, BL_F + 7)).number_format = "0"
wsB.cell(tot, 13, "=SUM(M{}:M{})".format(BL_F, BL_F + 7)).number_format = NF_UA
wsB.cell(tot, 15, "=AVERAGE(O{}:O{})".format(BL_F, BL_F + 7)).number_format = NF_PCT
wsB.cell(tot, 16, "=AVERAGE(P{}:P{})".format(BL_F, BL_F + 7)).number_format = NF_PCT

chB = LineChart(); chB.title = "Dinâmica do Bloco: Volume × Intensidade (índices relativos)"
chB.height = 8; chB.width = 19; chB.y_axis.title = "% relativo"
chB.add_data(Reference(wsB, min_col=15, max_col=16, min_row=11, max_row=BL_F + 7), titles_from_data=True)
chB.set_categories(Reference(wsB, min_col=1, min_row=BL_F, max_row=BL_F + 7))
for s in chB.series:
    s.graphicalProperties.line.width = 28000
wsB.add_chart(chB, "A23")
chB2 = BarChart(); chB2.type = "col"; chB2.title = "Contatos Pliométricos por Semana"
chB2.height = 8; chB2.width = 19; chB2.legend = None; chB2.y_axis.title = "contatos"
chB2.add_data(Reference(wsB, min_col=13, min_row=11, max_row=BL_F + 7), titles_from_data=True)
chB2.set_categories(Reference(wsB, min_col=1, min_row=BL_F, max_row=BL_F + 7))
wsB.add_chart(chB2, "J23")

secao(wsB, 40, "SESSÕES-MODELO DA SEMANA (A, B e C) — exercícios do seu programa + LPO e pliometria", 18, 1)
cab_tabela(wsB, 41, ["Sessão","Dia","Ordem","Exercício","Objetivo","Ref. VBT","Observação de execução"])
SESSOES_BLOCO = [
 ("A — Força MMII + LPO","Segunda", [
   ("Mobilidade de tornozelo e quadril","Aquecimento","—","6 exercícios × 8 rep, antes da barra"),
   ("Power clean a partir do joelho","Força explosiva (LPO)","—","Interromper a série se a velocidade da barra cair visivelmente"),
   ("Agachamento profundo","Força máxima","Agachamento","Exercício-âncora do bloco; controlar pela velocidade média"),
   ("Stiff com barra","Força máxima (cadeia posterior)","Terra","Excêntrica de 3 s nas semanas 1 a 4"),
   ("Afundo lateral sem passada","Força unilateral","—","Do seu programa (Séries 1, 3 e 7)"),
   ("Nórdico de isquiotibiais (excêntrico)","Preventivo","—","3 × 6, 2x por semana durante todo o bloco"),
   ("Abdominal reto com braços esticados + Dorsal perdigueiro","Core","—","3 × 25, do seu programa (Série 1)")]),
 ("B — Potência, pliometria e MMSS","Quarta", [
   ("Rotadores do ombro com elástico","Preventivo (ativação)","—","3 × 15, antes de qualquer trabalho de ombro"),
   ("Agachamento com salto sob carga (jump squat)","Potência","Agachamento","30% 1RM a partir da semana 6; pausa completa"),
   ("Salto no caixote / Drop jump","Pliometria","—","Do seu programa (Série 5); altura conforme a matriz semanal"),
   ("Saltos consecutivos sobre barreiras","Pliometria","—","Contato mínimo com o solo; contar os contatos"),
   ("Supino deitado com halteres","Força MMSS","Supino","Do seu programa (Série 1)"),
   ("Remada unilateral na polia","Força MMSS","—","Do seu programa (Séries 2, 5 e 7)"),
   ("Arremesso de bola","Potência MMSS","—","Do seu programa (Série 6)"),
   ("Abdominal cruzado esticado + Dorsal reto","Core","—","3 × 25, do seu programa (Série 2)")]),
 ("C — Força-velocidade e unilateral","Sexta", [
   ("Mobilidade de tornozelo e quadril","Aquecimento","—","—"),
   ("Snatch pull / Hang high pull","Força explosiva (LPO)","—","Puxadas sem fase de recepção: mesmo estímulo de tripla extensão, técnica mais simples"),
   ("Agachamento sumô no minitramp","Força-velocidade","Agachamento","Do seu programa (Série 2)"),
   ("Elevação de calcanhares","Preventivo (tornozelo)","—","Do seu programa (Séries 4, 6 e 8); descida lenta de 3 s"),
   ("Afundo frontal sem passada com sobrepeso","Força unilateral","—","Do seu programa (Séries 2, 4 e 8)"),
   ("Salto unilateral com sobrepeso","Pliometria unilateral","—","Do seu programa (Série 6)"),
   ("Pullover deitado com haltere","Força MMSS","—","Do seu programa (Série 2)"),
   ("Sprints de 10 e 20 m com mudança de direção","Velocidade","—","Só nas semanas sem choque"),
   ("Abdominal remador com anilha","Core","—","3 × 20, do seu programa (Série 6)")]),
]
r = 42
for nome, dia, itens in SESSOES_BLOCO:
    ini = r
    for i, (ex, objx, vbt, obs) in enumerate(itens, start=1):
        wsB.cell(r, 1, nome if i == 1 else "")
        wsB.cell(r, 2, dia if i == 1 else "")
        wsB.cell(r, 3, i); wsB.cell(r, 4, ex); wsB.cell(r, 5, objx); wsB.cell(r, 6, vbt); wsB.cell(r, 7, obs)
        r += 1
    wsB.merge_cells(start_row=ini, start_column=1, end_row=r - 1, end_column=1)
    wsB.merge_cells(start_row=ini, start_column=2, end_row=r - 1, end_column=2)
SESS_L = r - 1
corpo_tabela(wsB, 42, SESS_L, 1, 7)
for rr in range(42, SESS_L + 1):
    for c in range(1, 8):
        wsB.cell(rr, c).font = Font(name=F, size=9, color=NAVY2)
        wsB.cell(rr, c).fill = PatternFill("solid", fgColor=LIGHT if (rr % 2) else LIGHT2)
    for c in (1, 4, 5, 7):
        wsB.cell(rr, c).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)
    wsB.cell(rr, 4).font = Font(name=F, size=9, bold=True, color=NAVY)
    wsB.cell(rr, 1).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
wsB.column_dimensions["D"].width = 46
wsB.column_dimensions["E"].width = 28
wsB.column_dimensions["G"].width = 62
nota(wsB, SESS_L + 2, 1, "As sessões A, B e C já estão prescritas semana a semana na aba 'Prescrição Força', com "
     "séries, repetições, %1RM, carga calculada e velocidade-alvo para o atleta de referência.", 18)
wsB.freeze_panes = "A12"
