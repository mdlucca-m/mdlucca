# ============================================================================
# 19) FORÇA 1RM — testes diretos e estimados + matriz de 1RM atual
# ============================================================================
wsR = wb.create_sheet("Força 1RM")
RM_F, RM_L = 8, 407
banner(wsR, "CONTROLE DE FORÇA MÁXIMA (1RM)",
       "Registre testes diretos ou séries até a falha técnica: a planilha estima o 1RM por Epley e Brzycki. A matriz "
       "à direita mantém o 1RM ATUAL de cada atleta e alimenta o cálculo de carga da aba Prescrição Força.", 26, "9C0006")
RM_H = ["Data","Semana","Atleta","Exercício","Método","Carga (kg)","Repetições","1RM Epley (kg)","1RM Brzycki (kg)",
        "1RM Adotado (kg)","Massa Corporal (kg)","Força Relativa (×massa)","Velocidade Média (m/s)","Observações"]
cab_tabela(wsR, 7, RM_H)
larguras(wsR, {"A":12,"B":8,"C":24,"D":30,"E":24,"F":11,"G":11,"H":13,"I":14,"J":14,"K":16,"L":15,"M":16,"N":24,
               "O":3,"P":24,"Q":14,"R":14,"S":13,"T":14,"U":13,"V":15,"W":13,"X":12,"Y":13,"Z":15})
nota(wsR, 4, 1, "Epley: 1RM = carga × (1 + reps/30).  •  Brzycki: 1RM = carga ÷ (1,0278 − 0,0278 × reps).  "
     "Ambas perdem precisão acima de ~10 repetições — use 3 a 6 repetições.  "
     "A estimativa do 1RM pela velocidade da barra tende a SUPERESTIMAR a força real (Greig et al., 2023; "
     "LeMense et al., 2024): sempre que possível, teste o 1RM diretamente.", 14)
wsR.row_dimensions[4].height = 30
for r in range(RM_F, RM_L + 1):
    wsR.cell(r, 2, '=IF($A{0}="",0,INT(($A{0}-Macrociclo!$C$11)/7)+1)'.format(r))
    wsR.cell(r, 8, '=IF(OR($F{0}="",$G{0}=""),"",ROUND($F{0}*(1+$G{0}/30),1))'.format(r))
    wsR.cell(r, 9, '=IF(OR($F{0}="",$G{0}="",$G{0}>36),"",ROUND($F{0}/(1.0278-0.0278*$G{0}),1))'.format(r))
    wsR.cell(r, 10, '=IF($E{0}="Direto (1RM real)",$F{0},IF(OR($H{0}="",$I{0}=""),"",'
                    'ROUND(AVERAGE($H{0},$I{0}),1)))'.format(r))
    wsR.cell(r, 11, '=IF($C{0}="","",IFERROR(INDEX(Cadastro!$P${1}:$P${2},MATCH($C{0},Cadastro!$B${1}:$B${2},0)),""))'
             .format(r, CAD_F, CAD_L))
    wsR.cell(r, 12, '=IFERROR($J{0}/$K{0},"")'.format(r))
corpo_tabela(wsR, RM_F, RM_L, 1, 14)
for r in range(RM_F, RM_L + 1):
    for c in (1, 3, 4, 5, 6, 7, 13, 14):
        wsR.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
        wsR.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    for c in (2, 8, 9, 10, 11, 12):
        wsR.cell(r, c).font = Font(name=F, size=9, bold=(c == 10), color=NAVY2)
        wsR.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
    for c in (3, 4, 5, 14):
        wsR.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsR.cell(r, 1).number_format = NF_DATE
    wsR.cell(r, 2).number_format = '0;;""'
    for c in (6, 8, 9, 10, 11):
        wsR.cell(r, c).number_format = '0.0;;""'
    wsR.cell(r, 12).number_format = '0.00;;""'
    wsR.cell(r, 13).number_format = '0.00;;""'
EX_1RM = ["Agachamento profundo","Agachamento frontal","Stiff com barra","Levantamento terra",
          "Supino sentado","Supino deitado com halteres","Remada serrote","Power clean","Clean pull"]
dv(wsR, ATLETAS_REF,       "C{}:C{}".format(RM_F, RM_L))
dv(wsR, L("Método de 1RM"),"E{}:E{}".format(RM_F, RM_L))
dv(wsR, "'Força 1RM'!$Q$7:$Y$7", "D{}:D{}".format(RM_F, RM_L))

secao(wsR, 5, "1RM ATUAL POR ATLETA (última avaliação registrada, em kg)", 25, 16)
cab_tabela(wsR, 7, ["Atleta"] + EX_1RM, col0=16)
for i in range(CAD_L - CAD_F + 1):
    r = RM_F + i
    a = CAD_F + i
    wsR.cell(r, 16, '=IF(Cadastro!$B{0}="","",Cadastro!$B{0})'.format(a))
    for j in range(9):
        cl = get_column_letter(17 + j)
        wsR.cell(r, 17 + j,
          '=IF($P{0}="",0,IFERROR(AVERAGEIFS($J${1}:$J${2},$C${1}:$C${2},$P{0},$D${1}:$D${2},{3}$7,'
          '$A${1}:$A${2},SUMPRODUCT(MAX(($C${1}:$C${2}=$P{0})*($D${1}:$D${2}={3}$7)*$A${1}:$A${2}))),0))'
          .format(r, RM_F, RM_L, cl))
RM_MAT_L = RM_F + (CAD_L - CAD_F)
corpo_tabela(wsR, RM_F, RM_MAT_L, 16, 25)
for r in range(RM_F, RM_MAT_L + 1):
    for c in range(16, 26):
        wsR.cell(r, c).font = Font(name=F, size=9, bold=(c > 16), color=NAVY2)
        wsR.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT if (r - RM_F) % 2 == 0 else LIGHT2)
        wsR.cell(r, c).number_format = '0.0;;""'
    wsR.cell(r, 16).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsR.cell(r, 16).number_format = "General"
wsR.conditional_formatting.add("Q{}:Q{}".format(RM_F, RM_MAT_L),
    ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="A9D08E"))
wsR.freeze_panes = "C8"
