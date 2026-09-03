# ============================================================================
# 21) PERFIL FORÇA-VELOCIDADE-POTÊNCIA  (método de Samozino no salto com carga)
# ============================================================================
wsFV = wb.create_sheet("Perfil F-V-P")
banner(wsFV, "PERFIL FORÇA–VELOCIDADE–POTÊNCIA (SALTO COM CARGA)",
       "Protocolo: squat jump com 0, 20, 40, 60 e 80 kg (ou % da massa corporal). A planilha calcula F0, V0, Pmax e "
       "a inclinação do perfil por regressão linear, pelo método de Samozino/Morin.", 14, "6B3FA0")
larguras(wsFV, {"A":18,"B":16,"C":16,"D":16,"E":16,"F":16,"G":16,"H":16,"I":16,"J":22,"K":20,"L":52,"M":14,"N":14})
secao(wsFV, 3, "PARÂMETROS DO TESTE", 14, 1)
rotulo(wsFV, 4, 1, "Atleta:")
selFV = entrada(wsFV, 4, 3, NOMES[0], largura_merge=4)
selFV.font = Font(name=F, size=12, bold=True, color="0000FF")
dv(wsFV, ATLETAS_REF, "C4")
rotulo(wsFV, 5, 1, "Massa corporal (kg):")
calc(wsFV, 5, 3, '=IFERROR(INDEX(Cadastro!$P${0}:$P${1},MATCH($C$4,Cadastro!$B${0}:$B${1},0)),"")'.format(CAD_F, CAD_L), '0.0')
rotulo(wsFV, 6, 1, "Distância de push-off hPO (m):")
entrada(wsFV, 6, 3, 0.40, '0.00')
wsFV["C6"].comment = Comment("Distância percorrida pelo centro de massa na fase propulsiva: da posição inicial do "
                             "squat jump (≈90° de joelho) até a extensão completa.\nMeça a diferença de altura do "
                             "trocânter maior entre as duas posições. Faixa usual: 0,32 a 0,48 m.\n"
                             "hPO errado desloca todo o perfil — meça, não estime.", "Planilha")
rotulo(wsFV, 7, 1, "SFvopt (N·s/m/kg):")
entrada(wsFV, 7, 3, None, '0.00')
wsFV["C7"].comment = Comment("Inclinação ÓTIMA teórica do perfil força-velocidade do atleta.\nÉ calculada pelo "
                             "método de Samozino/Jiménez-Reyes e sai pronta de softwares como o My Jump ou do "
                             "relatório da sua plataforma de força.\nDeixe em branco se não tiver: F0, V0, Pmax e "
                             "a inclinação real continuam sendo calculados.", "Planilha")

secao(wsFV, 10, "SALTOS COM CARGA PROGRESSIVA", 14, 1)
cab_tabela(wsFV, 11, ["Carga Adicional (kg)","Altura do Salto (cm)","Massa Total (kg)","Força Média (N)",
                      "Força Relativa (N/kg)","Velocidade Média (m/s)","Potência Média (W)","Potência Relativa (W/kg)"])
FV_F, FV_L = 12, 16
for i in range(5):
    r = FV_F + i
    wsFV.cell(r, 1, [0, 20, 40, 60, 80][i])
    wsFV.cell(r, 3, '=IFERROR($C$5+$A{0},"")'.format(r))
    wsFV.cell(r, 4, '=IFERROR($C{0}*9.81*(($B{0}/100)/$C$6+1),"")'.format(r))
    wsFV.cell(r, 5, '=IFERROR($D{0}/$C$5,"")'.format(r))
    wsFV.cell(r, 6, '=IFERROR(SQRT(9.81*($B{0}/100)/2),"")'.format(r))
    wsFV.cell(r, 7, '=IFERROR($D{0}*$F{0},"")'.format(r))
    wsFV.cell(r, 8, '=IFERROR($G{0}/$C$5,"")'.format(r))
corpo_tabela(wsFV, FV_F, FV_L, 1, 8)
for r in range(FV_F, FV_L + 1):
    for c in (1, 2):
        wsFV.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
        wsFV.cell(r, c).font = Font(name=F, size=10, color="0000FF")
        wsFV.cell(r, c).number_format = '0.0'
    for c in range(3, 9):
        wsFV.cell(r, c).font = Font(name=F, size=10, bold=True, color=NAVY2)
        wsFV.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
        wsFV.cell(r, c).number_format = '0.00' if c in (5, 6, 8) else '0.0'
for i, h in enumerate([48.0, 39.0, 32.0, 26.0, 21.0]):
    wsFV.cell(FV_F + i, 2, h)

secao(wsFV, 18, "RESULTADOS DO PERFIL", 14, 1)
RES = [("F0 — Força teórica máxima (N)", '=IFERROR(INTERCEPT($D${0}:$D${1},$F${0}:$F${1}),"")'.format(FV_F, FV_L), '0'),
       ("F0 relativa (N/kg)", '=IFERROR($C$19/$C$5,"")', '0.00'),
       ("V0 — Velocidade teórica máxima (m/s)", '=IFERROR(-$C$19/$C$22,"")', '0.00'),
       ("Sfv — Inclinação do perfil (N·s/m)", '=IFERROR(SLOPE($D${0}:$D${1},$F${0}:$F${1}),"")'.format(FV_F, FV_L), '0.0'),
       ("Sfv relativa (N·s/m/kg)", '=IFERROR($C$22/$C$5,"")', '0.00'),
       ("Pmax — Potência máxima (W)", '=IFERROR($C$19*$C$21/4,"")', '0'),
       ("Pmax relativa (W/kg)", '=IFERROR($C$24/$C$5,"")', '0.00'),
       ("FVimb — Desequilíbrio F-V (%)", '=IF($C$7="","",IFERROR(ABS($C$23)/ABS($C$7),""))', NF_PCT),
       ("R² da regressão", '=IFERROR(RSQ($D${0}:$D${1},$F${0}:$F${1}),"")'.format(FV_F, FV_L), '0.000')]
for i, (lab, f, nf) in enumerate(RES):
    r = 19 + i
    rotulo(wsFV, r, 1, lab)
    c = calc(wsFV, r, 3, f, nf)
    c.font = Font(name=F, size=11, bold=True, color=NAVY2)
nota(wsFV, 17, 1, "F0 e V0 são EXTRAPOLAÇÕES da reta força-velocidade: dependem muito da distância de push-off (C6) "
     "e da amplitude de cargas testada. Use pelo menos 5 cargas cobrindo uma faixa ampla e confira o R² (linha 27): "
     "abaixo de 0,95, refaça o teste.", 14)
rotulo(wsFV, 28, 1, "PERFIL:")
p = calc(wsFV, 28, 3, '=IF($C$26="","Informe o SFvopt em C7 para classificar",'
                      'IF($C$26<0.9,"Déficit de FORÇA",IF($C$26<=1.1,"Equilibrado","Déficit de VELOCIDADE")))')
p.font = Font(name=F, size=12, bold=True, color=NAVY)
wsFV.merge_cells(start_row=28, start_column=3, end_row=28, end_column=6)
wsFV.merge_cells(start_row=29, start_column=1, end_row=32, end_column=14)
rec = wsFV.cell(29, 1,
  '=IF($C$26="","Sem o SFvopt não é possível estimar o desequilíbrio. Ainda assim, F0, V0 e Pmax servem para '
  'acompanhar a evolução do atleta ao longo dos blocos e para comparar atletas do mesmo elenco na tabela abaixo.",'
  'IF($C$26<0.9,"DÉFICIT DE FORÇA — priorize cargas altas: agachamento e stiff a 80–90% 1RM, LPO (power clean e '
  'clean pull) a 80–90%, 70 a 100% do volume de força na região pesada do perfil. Reduza o volume balístico.",'
  'IF($C$26<=1.1,"PERFIL EQUILIBRADO — mantenha a distribuição mista e busque elevar a Pmax como um todo: alterne '
  'blocos de força máxima (85–90% 1RM) e blocos balísticos (jump squat 30% 1RM + pliometria).",'
  '"DÉFICIT DE VELOCIDADE — priorize o lado rápido do perfil: jump squat a 0–40% 1RM, saltos sem carga, pliometria '
  'reativa (drop jump) e LPO com ênfase em velocidade da barra. Mantenha a força máxima com volume mínimo.")))')
rec.font = Font(name=F, size=10, bold=True, color=NAVY)
rec.fill = PatternFill("solid", fgColor=GOLD_L)
rec.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)
rec.border = BORDER

chFV = ScatterChart(); chFV.title = "Relação Força–Velocidade"; chFV.style = 13
chFV.x_axis.title = "Velocidade média (m/s)"; chFV.y_axis.title = "Força média (N)"
chFV.height = 9; chFV.width = 13; chFV.legend = None
s = Series(Reference(wsFV, min_col=4, min_row=FV_F, max_row=FV_L),
           Reference(wsFV, min_col=6, min_row=FV_F, max_row=FV_L), title="F-v")
s.marker = Marker(symbol="circle", size=8); s.graphicalProperties.line.noFill = True
chFV.series.append(s)
wsFV.add_chart(chFV, "H10")
chPV = ScatterChart(); chPV.title = "Relação Potência–Velocidade"; chPV.style = 13
chPV.x_axis.title = "Velocidade média (m/s)"; chPV.y_axis.title = "Potência média (W)"
chPV.height = 9; chPV.width = 13; chPV.legend = None
s2 = Series(Reference(wsFV, min_col=7, min_row=FV_F, max_row=FV_L),
            Reference(wsFV, min_col=6, min_row=FV_F, max_row=FV_L), title="P-v")
s2.marker = Marker(symbol="triangle", size=8); s2.graphicalProperties.line.noFill = True
chPV.series.append(s2)
wsFV.add_chart(chPV, "H29")

secao(wsFV, 34, "PERFIL F-V DE TODO O ELENCO", 12, 1)
cab_tabela(wsFV, 35, ["Atleta","Massa (kg)","F0 (N)","V0 (m/s)","F0 rel (N/kg)","Pmax (W)","Pmax rel (W/kg)",
                      "Sfv rel (N·s/m/kg)","SFvopt","FVimb (%)","Perfil","Prioridade de Treino"])
FVE_F = 36
FVE_L = FVE_F + (CAD_L - CAD_F)
for i in range(CAD_L - CAD_F + 1):
    r = FVE_F + i
    a = CAD_F + i
    wsFV.cell(r, 1, '=IF(Cadastro!$B{0}="","",Cadastro!$B{0})'.format(a))
    wsFV.cell(r, 2, '=IF($A{0}="","",IFERROR(Cadastro!$P{1},""))'.format(r, a))
    wsFV.cell(r, 5, '=IFERROR($C{0}/$B{0},"")'.format(r))
    wsFV.cell(r, 6, '=IFERROR($C{0}*$D{0}/4,"")'.format(r))
    wsFV.cell(r, 7, '=IFERROR($F{0}/$B{0},"")'.format(r))
    wsFV.cell(r, 8, '=IFERROR(-$E{0}/$D{0},"")'.format(r))
    wsFV.cell(r, 10, '=IF(OR($I{0}="",$H{0}=""),"",IFERROR(ABS($H{0})/ABS($I{0}),""))'.format(r))
    wsFV.cell(r, 11, '=IF($J{0}="","",IF($J{0}<0.9,"Déficit de FORÇA",'
                     'IF($J{0}<=1.1,"Equilibrado","Déficit de VELOCIDADE")))'.format(r))
    wsFV.cell(r, 12, '=IF($K{0}="","",IF($K{0}="Déficit de FORÇA","Cargas altas: 80–90% 1RM + LPO pesado",'
                     'IF($K{0}="Equilibrado","Misto: alternar força máxima e balístico",'
                     '"Balístico: 0–40% 1RM, jump squat e pliometria reativa")))'.format(r))
corpo_tabela(wsFV, FVE_F, FVE_L, 1, 12)
for r in range(FVE_F, FVE_L + 1):
    for c in range(1, 13):
        if c in (3, 4, 9):
            wsFV.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
            wsFV.cell(r, c).font = Font(name=F, size=9, color="0000FF")
        else:
            wsFV.cell(r, c).font = Font(name=F, size=9, bold=(c == 11), color=NAVY2)
            wsFV.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT if (r - FVE_F) % 2 == 0 else LIGHT2)
    for c in (1, 11, 12):
        wsFV.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for c in (2, 3, 6):
        wsFV.cell(r, c).number_format = '0.0;;""'
    for c in (4, 5, 7, 8, 9):
        wsFV.cell(r, c).number_format = '0.00;;""'
    wsFV.cell(r, 10).number_format = NF_PCT
for txt, fill, ft in [('"Equilibrado"', GREEN, GREEN_T), ('"Déficit de FORÇA"', "FCE4D6", "C55A11"),
                      ('"Déficit de VELOCIDADE"', "DDEBF7", NAVY2)]:
    wsFV.conditional_formatting.add("K{}:K{}".format(FVE_F, FVE_L),
        CellIsRule(operator="equal", formula=[txt], fill=PatternFill("solid", fgColor=fill),
                   font=Font(name=F, size=9, bold=True, color=ft)))
chEQ = ScatterChart(); chEQ.title = "Elenco: Força relativa (F0/kg) × Velocidade (V0)"
chEQ.x_axis.title = "F0 relativa (N/kg)"; chEQ.y_axis.title = "V0 (m/s)"
chEQ.height = 10; chEQ.width = 16; chEQ.legend = None
sE = Series(Reference(wsFV, min_col=4, min_row=FVE_F, max_row=FVE_L),
            Reference(wsFV, min_col=5, min_row=FVE_F, max_row=FVE_L), title="Atletas")
sE.marker = Marker(symbol="diamond", size=9); sE.graphicalProperties.line.noFill = True
chEQ.series.append(sE)
wsFV.add_chart(chEQ, "N35")
wsFV.merge_cells(start_row=FVE_L + 2, start_column=1, end_row=FVE_L + 6, end_column=12)
cav = wsFV.cell(FVE_L + 2, 1,
  "LEIA ANTES DE USAR — o treino individualizado pelo desequilíbrio F-V mostrou bons resultados em alguns estudos "
  "(Jiménez-Reyes et al., 2017 e 2019) e ganhos de F0, V0 e altura de salto em meta-análises recentes, mas ensaios "
  "controlados independentes não reproduziram a superioridade sobre um programa bem feito não individualizado "
  "(Lindberg et al., 2021; Solberg et al., 2025), e há questionamento de que parte do efeito seja aprendizado da "
  "tarefa e não adaptação neuromuscular (Bobbert et al., 2024). Use o perfil como MAIS UMA informação para decidir "
  "a ênfase do bloco — não como regra única de prescrição. A base continua sendo elevar a força máxima e a Pmax.")
cav.font = Font(name=F, size=9, color=RED_T)
cav.fill = PatternFill("solid", fgColor="FDECEA"); cav.border = BORDER
cav.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)
wsFV.freeze_panes = "A11"
