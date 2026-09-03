# ============================================================================
# 20) PRESCRIÇÃO FORÇA — programa das 8 semanas, %1RM, carga e velocidade-alvo
# ============================================================================
wsPQ = wb.create_sheet("Prescrição Força")
PRF_F, PRF_L = 8, 407
banner(wsPQ, "PRESCRIÇÃO E CONTROLE DO TREINO DE FORÇA E POTÊNCIA",
       "As 8 semanas do bloco de base já vêm prescritas. A carga em kg sai de %1RM × 1RM atual do atleta de "
       "referência; a velocidade-alvo sai da tabela carga-velocidade (editável) à direita.", 28, "9C0006")
larguras(wsPQ, {"A":12,"B":9,"C":15,"D":10,"E":22,"F":7,"G":44,"H":18,"I":13,"J":8,"K":9,"L":9,"M":12,"N":14,
                "O":12,"P":13,"Q":15,"R":15,"S":15,"T":16,"U":7,"V":8,"W":10,"X":10,"Y":13,"Z":26,"AA":24,
                "AB":26,"AC":3,"AD":9,"AE":15,"AF":13,"AG":13})
secao(wsPQ, 3, "PARÂMETROS E RESUMO DA SEMANA", 28, 1)
rotulo(wsPQ, 4, 1, "Atleta de referência:")
selPQ = entrada(wsPQ, 4, 3, NOMES[0], largura_merge=4)
selPQ.font = Font(name=F, size=11, bold=True, color="0000FF")
dv(wsPQ, ATLETAS_REF, "C4")
rotulo(wsPQ, 5, 1, "Semana do bloco (1 a 8):")
entrada(wsPQ, 5, 3, 1, '0', largura_merge=2)
FW = '$B${0}:$B${1},$C$5'.format(PRF_F, PRF_L)
kpi(wsPQ, 4, 8,  "EXERCÍCIOS NA SEMANA", '=COUNTIFS({})'.format(FW), '0', NAVY2, 3)
kpi(wsPQ, 4, 11, "SÉRIES TOTAIS", '=SUMIFS($J${0}:$J${1},{2})'.format(PRF_F, PRF_L, FW), '0', NAVY2, 3)
kpi(wsPQ, 4, 14, "REPETIÇÕES TOTAIS", '=SUMIFS($X${0}:$X${1},{2})'.format(PRF_F, PRF_L, FW), NF_UA, NAVY2, 3)
kpi(wsPQ, 4, 17, "TONELAGEM DA SEMANA (kg)", '=SUMIFS($Y${0}:$Y${1},{2})'.format(PRF_F, PRF_L, FW), NF_UA, GOLD, 3)
kpi(wsPQ, 4, 20, "INTENSIDADE MÉDIA RELATIVA",
    '=IFERROR(SUMPRODUCT(($B${0}:$B${1}=$C$5)*$X${0}:$X${1}*$L${0}:$L${1})'
    '/SUMPRODUCT(($B${0}:$B${1}=$C$5)*$X${0}:$X${1}*($L${0}:$L${1}<>"")),0)'.format(PRF_F, PRF_L), NF_PCT, GOLD, 3)
kpi(wsPQ, 4, 23, "CONTATOS PLIOMÉTRICOS",
    '=SUMIFS($X${0}:$X${1},{2},$H${0}:$H${1},"Pliometria")'.format(PRF_F, PRF_L, FW), NF_UA, "6B3FA0", 3)
nota(wsPQ, 6, 1, "Preencha em amarelo o que foi EXECUTADO (carga usada, velocidade obtida, perda de velocidade, RIR e PSE). "
     "A tonelagem usa a carga usada quando informada e, na falta dela, a carga calculada.", 28)

PRF_H = ["Data","Semana do Bloco","Bloco","Sessão","Destinatário","Ordem","Exercício","Objetivo","Ref. VBT",
         "Séries","Reps","%1RM","1RM Atual (kg)","Carga Calculada (kg)","Carga Usada (kg)","Velocidade Alvo (m/s)",
         "Velocidade Obtida (m/s)","Perda de Vel. Limite (%)","Perda de Vel. Obtida (%)","Situação VBT",
         "RIR","PSE","Pausa (s)","Reps Totais","Tonelagem (kg)","Zona de Intensidade","Observações","Ref. 1RM"]
cab_tabela(wsPQ, 7, PRF_H)
F1 = "'Força 1RM'"
for r in range(PRF_F, PRF_L + 1):
    wsPQ.cell(r, 2,  '=IF($A{0}="",0,INT(($A{0}-\'Bloco Base\'!$C$5)/7)+1)'.format(r))
    wsPQ.cell(r, 13, '=IF($AB{0}="","",IFERROR(INDEX({1}!$Q${2}:$Y${3},'
                     'MATCH(IF($E{0}="Equipe (todos)",$C$4,$E{0}),{1}!$P${2}:$P${3},0),'
                     'MATCH($AB{0},{1}!$Q$7:$Y$7,0)),""))'.format(r, F1, RM_F, RM_MAT_L))
    wsPQ.cell(r, 14, '=IFERROR(IF(OR($L{0}="",$M{0}="",$M{0}=0),0,ROUND($L{0}*$M{0}*2,0)/2),0)'.format(r))
    wsPQ.cell(r, 16, '=IFERROR(IF(OR($L{0}="",$I{0}="—",$I{0}=""),"",'
                     'IF($I{0}="Agachamento",INDEX($AE$8:$AE$20,MATCH($L{0},$AD$8:$AD$20,1)),'
                     'IF($I{0}="Supino",INDEX($AF$8:$AF$20,MATCH($L{0},$AD$8:$AD$20,1)),'
                     'IF($I{0}="Terra",INDEX($AG$8:$AG$20,MATCH($L{0},$AD$8:$AD$20,1)),"")))),"")'.format(r))
    wsPQ.cell(r, 20, '=IF(OR($R{0}="",$S{0}=""),"",IF($S{0}>$R{0},"Acima do limite","Dentro do limite"))'.format(r))
    wsPQ.cell(r, 24, '=IFERROR(IF(OR($J{0}="",$K{0}=""),0,$J{0}*$K{0}),0)'.format(r))
    wsPQ.cell(r, 25, '=IFERROR(IF($X{0}=0,0,$X{0}*IF($O{0}="",$N{0},$O{0})),0)'.format(r))
    wsPQ.cell(r, 26, '=IF($L{0}="","",IF($L{0}<0.5,"Balística / Velocidade (<50%)",'
                     'IF($L{0}<0.7,"Velocidade-Força (50–69%)",IF($L{0}<0.8,"Força-Velocidade (70–79%)",'
                     'IF($L{0}<0.9,"Força Máxima (80–89%)","Força Máxima Alta (≥90%)")))))'.format(r))
corpo_tabela(wsPQ, PRF_F, PRF_L, 1, 28)
CALC_PQ = (2, 13, 14, 16, 20, 24, 25, 26)
for r in range(PRF_F, PRF_L + 1):
    for c in range(1, 29):
        if c in CALC_PQ:
            wsPQ.cell(r, c).font = Font(name=F, size=9, bold=(c in (14, 16, 25)), color=NAVY2)
            wsPQ.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
        else:
            wsPQ.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
            wsPQ.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    for c in (5, 7, 8, 26, 27, 28):
        wsPQ.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsPQ.cell(r, 7).font = Font(name=F, size=9, bold=True, color=NAVY)
    wsPQ.cell(r, 1).number_format = NF_DATE
    wsPQ.cell(r, 2).number_format = '0;;""'
    wsPQ.cell(r, 12).number_format = NF_PCT
    for c in (13, 14, 15):
        wsPQ.cell(r, c).number_format = '0.0;;""'
    for c in (16, 17):
        wsPQ.cell(r, c).number_format = '0.00;;""'
    for c in (18, 19):
        wsPQ.cell(r, c).number_format = NF_PCT
    for c in (24, 25):
        wsPQ.cell(r, c).number_format = NF_UA
dv(wsPQ, DEST_REF,               "E{}:E{}".format(PRF_F, PRF_L))
dv(wsPQ, L("Objetivo de Força"), "H{}:H{}".format(PRF_F, PRF_L))
dv(wsPQ, L("Ref. VBT"),          "I{}:I{}".format(PRF_F, PRF_L))
dv(wsPQ, L("Bloco de Treino"),   "C{}:C{}".format(PRF_F, PRF_L))
dv(wsPQ, L("PSE (0-10)"),        "V{}:V{}".format(PRF_F, PRF_L))
dv(wsPQ, "{}!$Q$7:$Y$7".format(F1), "AB{}:AB{}".format(PRF_F, PRF_L))
wsPQ.conditional_formatting.add("T{}:T{}".format(PRF_F, PRF_L),
    CellIsRule(operator="equal", formula=['"Acima do limite"'], fill=PatternFill("solid", fgColor=RED),
               font=Font(name=F, size=9, bold=True, color=RED_T)))
wsPQ.conditional_formatting.add("T{}:T{}".format(PRF_F, PRF_L),
    CellIsRule(operator="equal", formula=['"Dentro do limite"'], fill=PatternFill("solid", fgColor=GREEN),
               font=Font(name=F, size=9, bold=True, color=GREEN_T)))
wsPQ.freeze_panes = "C8"
wsPQ.auto_filter.ref = "A7:AB{}".format(PRF_L)

# --- tabela de referência carga-velocidade (editável) -----------------------
secao(wsPQ, 6, "TABELA CARGA-VELOCIDADE (editável)", 33, 30)
cab_tabela(wsPQ, 7, ["%1RM", "Agachamento — MPV (m/s)", "Supino — MPV (m/s)", "Terra — MV (m/s)"], col0=30)
LV = [(0.40,1.09,0.94,1.05),(0.45,1.02,0.86,0.98),(0.50,0.96,0.79,0.90),(0.55,0.89,0.72,0.83),
      (0.60,0.83,0.65,0.76),(0.65,0.75,0.58,0.69),(0.70,0.68,0.51,0.62),(0.75,0.62,0.44,0.55),
      (0.80,0.55,0.37,0.48),(0.85,0.47,0.31,0.41),(0.90,0.40,0.24,0.35),(0.95,0.36,0.20,0.29),
      (1.00,0.32,0.17,0.24)]
for i, row in enumerate(LV):
    r = 8 + i
    for j, v in enumerate(row):
        c = wsPQ.cell(r, 30 + j, v)
        c.font = Font(name=F, size=9, color="0000FF")
        c.fill = PatternFill("solid", fgColor=GOLD_L)
        c.border = BORDER
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.number_format = NF_PCT if j == 0 else '0.00'
nt = wsPQ.cell(22, 30, "Valores APROXIMADOS de referência compilados da literatura de treinamento baseado em "
                       "velocidade (velocidade média propulsiva no agachamento completo e no supino; velocidade média "
                       "no terra). A relação carga-velocidade é específica de exercício, equipamento e atleta: "
                       "levante o SEU perfil individual e substitua estes números. Use a velocidade para conferir a "
                       "intensidade da série, não para substituir o teste de 1RM.")
wsPQ.merge_cells(start_row=22, start_column=30, end_row=27, end_column=33)
nt.font = Font(name=F, size=8, italic=True, color=GREY_T)
nt.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
nt.fill = PatternFill("solid", fgColor=LIGHT2); nt.border = BORDER

# --- geração das 8 semanas --------------------------------------------------
BLOCO_INI = date(2026, 9, 7)
PROG = {
 "AGACH":  [(4,8,.65),(4,6,.75),(5,5,.80),(3,5,.70),(5,4,.85),(4,3,.88),(4,3,.90),(3,2,.92)],
 "AGACH2": [(4,8,.50),(4,6,.60),(4,5,.65),(3,5,.55),(4,4,.70),(4,4,.72),(4,3,.75),(3,3,.75)],
 "LPO":    [(5,3,.55),(4,4,.70),(5,3,.75),(3,3,.60),(5,2,.82),(4,3,.95),(6,2,.88),(4,2,.90)],
 "LPO2":   [(4,3,.50),(4,3,.65),(4,3,.70),(3,3,.55),(4,3,.78),(4,3,.85),(5,2,.85),(3,2,.85)],
 "STIFF":  [(4,8,.60),(4,8,.65),(4,6,.70),(3,6,.60),(4,6,.72),(4,5,.75),(4,5,.78),(3,4,.75)],
 "MMSS":   [(4,10,.65),(4,8,.70),(4,8,.75),(3,8,.65),(4,6,.80),(4,6,.82),(4,5,.85),(3,5,.85)],
 "UNILAT": [(3,10,None),(3,10,None),(3,8,None),(2,8,None),(3,8,None),(3,8,None),(3,6,None),(2,6,None)],
 "JUMPSQ": [(0,0,None),(4,4,.20),(4,4,.25),(3,3,.20),(5,4,.30),(5,4,.30),(5,3,.35),(4,3,.30)],
 "PREV":   [(3,10,None),(3,10,None),(3,8,None),(2,10,None),(3,8,None),(3,8,None),(3,6,None),(2,8,None)],
 "MB":     [(3,8,None)] * 8,
 "SPRINT": [(4,1,None),(6,1,None),(0,0,None),(4,1,None),(6,1,None),(6,1,None),(0,0,None),(4,1,None)],
 "CORE":   [(3,25,None),(3,25,None),(3,25,None),(3,20,None),(3,20,None),(3,20,None),(3,20,None),(3,15,None)],
 "AQUEC":  [(1,8,None)] * 8,
}
PLIO_SEM = [60, 90, 120, 45, 90, 110, 140, 70]
for slot, share in (("PLIO1", .40), ("PLIO2", .35), ("PLIO3", .25)):
    PROG[slot] = [(max(1, round(PLIO_SEM[w] * share / 5)), 5, None) for w in range(8)]
PAUSA = {"AGACH":180,"AGACH2":150,"LPO":180,"LPO2":150,"STIFF":120,"MMSS":120,"UNILAT":90,"JUMPSQ":180,
         "PLIO1":120,"PLIO2":120,"PLIO3":120,"PREV":60,"MB":90,"SPRINT":120,"CORE":45,"AQUEC":0}
OBJ = {"AGACH":"Força Máxima","AGACH2":"Força-Velocidade","LPO":"Força-Velocidade","LPO2":"Força-Velocidade",
       "STIFF":"Força Máxima","MMSS":"Força Máxima","UNILAT":"Força Máxima","JUMPSQ":"Potência",
       "PLIO1":"Pliometria","PLIO2":"Pliometria","PLIO3":"Pliometria","PREV":"Preventivo","MB":"Potência",
       "SPRINT":"Velocidade","CORE":"Core","AQUEC":"Aquecimento"}
VL = {"AGACH":(.15,.10),"AGACH2":(.15,.10),"LPO":(.10,.10),"LPO2":(.10,.10),"STIFF":(.20,.15),
      "MMSS":(.20,.15),"JUMPSQ":(.10,.10)}
SESSOES_PRF = [
 ("A", 0, [("Mobilidade de tornozelo e quadril","AQUEC","—",""),
           ("Power clean a partir do joelho","LPO","—","Power clean"),
           ("Agachamento profundo","AGACH","Agachamento","Agachamento profundo"),
           ("Stiff com barra","STIFF","Terra","Stiff com barra"),
           ("Afundo lateral sem passada","UNILAT","—",""),
           ("Nórdico de isquiotibiais (excêntrico)","PREV","—",""),
           ("Abdominal reto com braços esticados + Dorsal perdigueiro","CORE","—","")]),
 ("B", 2, [("Rotadores do ombro com elástico","PREV","—",""),
           ("Agachamento com salto sob carga (jump squat)","JUMPSQ","Agachamento","Agachamento profundo"),
           ("Salto no caixote / Drop jump","PLIO1","—",""),
           ("Saltos consecutivos sobre barreiras","PLIO2","—",""),
           ("Supino deitado com halteres","MMSS","Supino","Supino deitado com halteres"),
           ("Remada unilateral na polia","MMSS","—",""),
           ("Arremesso de bola","MB","—",""),
           ("Abdominal cruzado esticado + Dorsal reto","CORE","—","")]),
 ("C", 4, [("Mobilidade de tornozelo e quadril","AQUEC","—",""),
           ("Snatch pull / Hang high pull","LPO2","—","Clean pull"),
           ("Agachamento sumô no minitramp","AGACH2","Agachamento","Agachamento profundo"),
           ("Elevação de calcanhares","PREV","—",""),
           ("Afundo frontal sem passada com sobrepeso","UNILAT","—",""),
           ("Salto unilateral com sobrepeso","PLIO3","—",""),
           ("Pullover deitado com haltere","MMSS","—",""),
           ("Sprints de 10 e 20 m com mudança de direção","SPRINT","—",""),
           ("Abdominal remador com anilha","CORE","—","")]),
]
BLOCO_NOME = ["Acumulação","Acumulação","Acumulação","Descarga",
              "Transmutação","Transmutação","Transmutação","Realização"]
r = PRF_F
for w in range(8):
    for sess, off, itens in SESSOES_PRF:
        d = BLOCO_INI + timedelta(days=w * 7 + off)
        ordem = 0
        for ex, fam, vbt, ref1rm in itens:
            ser, rep, pct = PROG[fam][w]
            if ser == 0:
                continue
            ordem += 1
            wsPQ.cell(r, 1, d); wsPQ.cell(r, 1).number_format = NF_DATE
            wsPQ.cell(r, 3, BLOCO_NOME[w]); wsPQ.cell(r, 4, sess)
            wsPQ.cell(r, 5, "Equipe (todos)"); wsPQ.cell(r, 6, ordem)
            wsPQ.cell(r, 7, ex); wsPQ.cell(r, 8, OBJ[fam]); wsPQ.cell(r, 9, vbt)
            wsPQ.cell(r, 10, ser); wsPQ.cell(r, 11, rep)
            if pct is not None:
                wsPQ.cell(r, 12, pct)
            if fam in VL:
                wsPQ.cell(r, 18, VL[fam][0 if w < 4 else 1])
            wsPQ.cell(r, 23, PAUSA[fam])
            if ref1rm:
                wsPQ.cell(r, 28, ref1rm)
            r += 1
PRF_USADO = r - 1
