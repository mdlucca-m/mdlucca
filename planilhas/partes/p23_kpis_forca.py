# ============================================================================
# 23) KPIs FORÇA — painel de acompanhamento do bloco de força e potência
# ============================================================================
wsK = wb.create_sheet("KPIs Força")
banner(wsK, "KPIs DE FORÇA E POTÊNCIA — ACOMPANHAMENTO DO BLOCO",
       "Indicadores de carga (tonelagem, intensidade relativa, contatos pliométricos) e de evolução (1RM relativo, "
       "CMJ, potência de pico). Altere a semana em C4 para atualizar os cartões.", 20, "9C0006")
larguras(wsK, {"A":22,"B":16,"C":13,"D":15,"E":16,"F":18,"G":18,"H":16,"I":16,"J":3,
               "K":13,"L":13,"M":13,"N":13,"O":13,"P":13,"Q":13,"R":13,"S":13,"T":13})
PQ = "'Prescrição Força'"
rotulo(wsK, 4, 1, "Semana do bloco (1 a 8):")
entrada(wsK, 4, 3, 1, '0', largura_merge=2)
FK = "{0}!$B${1}:$B${2},$C$4".format(PQ, PRF_F, PRF_L)
kpi(wsK, 6, 1,  "TONELAGEM DA SEMANA (kg)", '=SUMIFS({0}!$Y${1}:$Y${2},{3})'.format(PQ, PRF_F, PRF_L, FK), NF_UA, "9C0006", 3)
kpi(wsK, 6, 4,  "REPETIÇÕES TOTAIS", '=SUMIFS({0}!$X${1}:$X${2},{3})'.format(PQ, PRF_F, PRF_L, FK), NF_UA, NAVY2, 3)
kpi(wsK, 6, 7,  "INTENSIDADE MÉDIA RELATIVA",
    '=IFERROR(SUMPRODUCT(({0}!$B${1}:$B${2}=$C$4)*{0}!$X${1}:$X${2}*{0}!$L${1}:$L${2})'
    '/SUMPRODUCT(({0}!$B${1}:$B${2}=$C$4)*{0}!$X${1}:$X${2}*({0}!$L${1}:$L${2}<>"")),0)'.format(PQ, PRF_F, PRF_L),
    NF_PCT, GOLD, 3)
kpi(wsK, 6, 10, "CONTATOS PLIOMÉTRICOS",
    '=SUMIFS({0}!$X${1}:$X${2},{3},{0}!$H${1}:$H${2},"Pliometria")'.format(PQ, PRF_F, PRF_L, FK), NF_UA, "6B3FA0", 3)
kpi(wsK, 6, 13, "1RM MÉDIO — AGACHAMENTO (kg)",
    '=IFERROR(AVERAGEIF(\'Força 1RM\'!$Q${0}:$Q${1},">0"),0)'.format(RM_F, RM_MAT_L), '0.0;;""', NAVY2, 3)
kpi(wsK, 6, 16, "FORÇA RELATIVA MÉDIA (× massa)", '=IFERROR(AVERAGEIF($C$31:$C$70,">0"),0)', NF_DEC, NAVY2, 3)
kpi(wsK, 6, 19, "Δ CMJ MÉDIO DO BLOCO", '=IFERROR(AVERAGEIF($F$31:$F$70,"<>0"),0)', '+0.0%;-0.0%;""', GOLD, 2)

secao(wsK, 9, "CARGA DE FORÇA POR SEMANA DO BLOCO", 9, 1)
cab_tabela(wsK, 10, ["Semana","Bloco","Séries","Repetições","Tonelagem (kg)","Intensidade Média Relativa",
                     "Contatos Pliométricos","Exercícios Prescritos","Tonelagem por Exercício"])
KW_F, KW_L = 11, 18
for i in range(8):
    r = KW_F + i
    wsK.cell(r, 1, i + 1)
    wsK.cell(r, 2, '=IFERROR(INDEX(\'Bloco Base\'!$C$12:$C$19,MATCH($A{},\'Bloco Base\'!$A$12:$A$19,0)),"")'.format(r))
    wsK.cell(r, 3, '=SUMIFS({0}!$J${1}:$J${2},{0}!$B${1}:$B${2},$A{3})'.format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 4, '=SUMIFS({0}!$X${1}:$X${2},{0}!$B${1}:$B${2},$A{3})'.format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 5, '=SUMIFS({0}!$Y${1}:$Y${2},{0}!$B${1}:$B${2},$A{3})'.format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 6, '=IFERROR(SUMPRODUCT(({0}!$B${1}:$B${2}=$A{3})*{0}!$X${1}:$X${2}*{0}!$L${1}:$L${2})'
                   '/SUMPRODUCT(({0}!$B${1}:$B${2}=$A{3})*{0}!$X${1}:$X${2}*({0}!$L${1}:$L${2}<>"")),0)'
             .format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 7, '=SUMIFS({0}!$X${1}:$X${2},{0}!$B${1}:$B${2},$A{3},{0}!$H${1}:$H${2},"Pliometria")'
             .format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 8, '=COUNTIFS({0}!$B${1}:$B${2},$A{3})'.format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 9, '=IFERROR($E{0}/$H{0},0)'.format(r))
corpo_tabela(wsK, KW_F, KW_L, 1, 9)
for r in range(KW_F, KW_L + 1):
    for c in range(1, 10):
        wsK.cell(r, c).font = Font(name=F, size=9, bold=(c in (1, 5)), color=NAVY2)
        wsK.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT if (r - KW_F) % 2 == 0 else LIGHT2)
    wsK.cell(r, 2).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for c in (3, 4, 5, 7, 8, 9):
        wsK.cell(r, c).number_format = NF_UA
    wsK.cell(r, 6).number_format = NF_PCT
wsK.conditional_formatting.add("E{}:E{}".format(KW_F, KW_L),
    ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="F4B183"))

cB = BarChart(); cB.type = "col"; cB.title = "Tonelagem × Intensidade Média Relativa por Semana"
cB.height = 9; cB.width = 20; cB.y_axis.title = "Tonelagem (kg)"; cB.y_axis.majorGridlines = None
cB.add_data(Reference(wsK, min_col=5, min_row=10, max_row=KW_L), titles_from_data=True)
cB.set_categories(Reference(wsK, min_col=1, min_row=KW_F, max_row=KW_L))
cL = LineChart()
cL.add_data(Reference(wsK, min_col=6, min_row=10, max_row=KW_L), titles_from_data=True)
cL.y_axis.axId = 200; cL.y_axis.title = "% de 1RM"; cL.y_axis.crosses = "max"
cL.series[0].graphicalProperties.line.width = 30000
cB += cL
wsK.add_chart(cB, "K10")
cP = BarChart(); cP.type = "col"; cP.title = "Contatos Pliométricos por Semana"
cP.height = 9; cP.width = 20; cP.legend = None; cP.y_axis.title = "contatos"
cP.add_data(Reference(wsK, min_col=7, min_row=10, max_row=KW_L), titles_from_data=True)
cP.set_categories(Reference(wsK, min_col=1, min_row=KW_F, max_row=KW_L))
wsK.add_chart(cP, "K29")

secao(wsK, 20, "DISTRIBUIÇÃO DE REPETIÇÕES POR ZONA DE INTENSIDADE (bloco completo)", 9, 1)
cab_tabela(wsK, 21, ["Zona de Intensidade","Repetições","% do Total","Séries"])
ZONAS = ["Balística / Velocidade (<50%)","Velocidade-Força (50–69%)","Força-Velocidade (70–79%)",
         "Força Máxima (80–89%)","Força Máxima Alta (≥90%)"]
KZ_F = 22
for i, z in enumerate(ZONAS):
    r = KZ_F + i
    wsK.cell(r, 1, z)
    wsK.cell(r, 2, '=SUMIFS({0}!$X${1}:$X${2},{0}!$Z${1}:$Z${2},$A{3})'.format(PQ, PRF_F, PRF_L, r))
    wsK.cell(r, 3, '=IFERROR($B{0}/SUM($B${1}:$B${2}),0)'.format(r, KZ_F, KZ_F + 4))
    wsK.cell(r, 4, '=SUMIFS({0}!$J${1}:$J${2},{0}!$Z${1}:$Z${2},$A{3})'.format(PQ, PRF_F, PRF_L, r))
KZ_L = KZ_F + 4
corpo_tabela(wsK, KZ_F, KZ_L, 1, 4)
for r in range(KZ_F, KZ_L + 1):
    for c in range(1, 5):
        wsK.cell(r, c).font = Font(name=F, size=9, color=NAVY2)
        wsK.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT if (r - KZ_F) % 2 == 0 else LIGHT2)
    wsK.cell(r, 1).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsK.cell(r, 2).number_format = NF_UA; wsK.cell(r, 4).number_format = NF_UA
    wsK.cell(r, 3).number_format = NF_PCT
cZ = BarChart(); cZ.type = "bar"; cZ.title = "Repetições por Zona de Intensidade"
cZ.height = 7; cZ.width = 20; cZ.legend = None
cZ.add_data(Reference(wsK, min_col=2, min_row=21, max_row=KZ_L), titles_from_data=True)
cZ.set_categories(Reference(wsK, min_col=1, min_row=KZ_F, max_row=KZ_L))
wsK.add_chart(cZ, "K48")

secao(wsK, 29, "EVOLUÇÃO POR ATLETA", 9, 1)
cab_tabela(wsK, 30, ["Atleta","1RM Agachamento (kg)","Força Relativa (× massa)","CMJ Inicial (cm)","CMJ Atual (cm)",
                     "Δ CMJ","Potência de Pico Atual (W)","Perfil F-V","Prioridade"])
KA_F = 31
KA_L = KA_F + (CAD_L - CAD_F)
TS = "Testes"
def _prim(r):
    return ('SUMPRODUCT(MIN((Testes!$B${1}:$B${2}=$A{0})*Testes!$A${1}:$A${2}'
            '+(Testes!$B${1}:$B${2}<>$A{0})*100000))').format(r, TST_F, TST_L)
def _ult(r):
    return 'SUMPRODUCT(MAX((Testes!$B${1}:$B${2}=$A{0})*Testes!$A${1}:$A${2}))'.format(r, TST_F, TST_L)
def _teste(r, col, quando):
    return ('=IF($A{0}="",0,IFERROR(AVERAGEIFS(Testes!${3}${1}:${3}${2},Testes!$B${1}:$B${2},$A{0},'
            'Testes!$A${1}:$A${2},{4}),0))').format(r, TST_F, TST_L, col, quando)
for i in range(CAD_L - CAD_F + 1):
    r = KA_F + i
    a = CAD_F + i
    wsK.cell(r, 1, '=IF(Cadastro!$B{0}="","",Cadastro!$B{0})'.format(a))
    wsK.cell(r, 2, '=IF($A{0}="",0,IFERROR(INDEX(\'Força 1RM\'!$Q${1}:$Q${2},'
                   'MATCH($A{0},\'Força 1RM\'!$P${1}:$P${2},0)),0))'.format(r, RM_F, RM_MAT_L))
    wsK.cell(r, 3, '=IF($A{0}="",0,IFERROR($B{0}/INDEX(Cadastro!$P${1}:$P${2},'
                   'MATCH($A{0},Cadastro!$B${1}:$B${2},0)),0))'.format(r, CAD_F, CAD_L))
    wsK.cell(r, 4, _teste(r, "L", _prim(r)))
    wsK.cell(r, 5, _teste(r, "L", _ult(r)))
    wsK.cell(r, 6, '=IF(OR($D{0}=0,$E{0}=0),0,$E{0}/$D{0}-1)'.format(r))
    wsK.cell(r, 7, _teste(r, "S", _ult(r)))
    wsK.cell(r, 8, '=IF($A{0}="","",IFERROR(INDEX(\'Perfil F-V-P\'!$K${1}:$K${2},'
                   'MATCH($A{0},\'Perfil F-V-P\'!$A${1}:$A${2},0)),""))'.format(r, FVE_F, FVE_L))
    wsK.cell(r, 9, '=IF($A{0}="","",IFERROR(INDEX(\'Perfil F-V-P\'!$L${1}:$L${2},'
                   'MATCH($A{0},\'Perfil F-V-P\'!$A${1}:$A${2},0)),""))'.format(r, FVE_F, FVE_L))
corpo_tabela(wsK, KA_F, KA_L, 1, 9)
for r in range(KA_F, KA_L + 1):
    for c in range(1, 10):
        wsK.cell(r, c).font = Font(name=F, size=9, bold=(c in (3, 6)), color=NAVY2)
        wsK.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT if (r - KA_F) % 2 == 0 else LIGHT2)
    for c in (1, 8, 9):
        wsK.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for c in (2, 4, 5):
        wsK.cell(r, c).number_format = '0.0;;""'
    wsK.cell(r, 3).number_format = NF_DEC
    wsK.cell(r, 6).number_format = '+0.0%;-0.0%;""'
    wsK.cell(r, 7).number_format = NF_UA
wsK.conditional_formatting.add("F{}:F{}".format(KA_F, KA_L),
    CellIsRule(operator="greaterThan", formula=["0.03"], fill=PatternFill("solid", fgColor=GREEN),
               font=Font(name=F, size=9, bold=True, color=GREEN_T)))
wsK.conditional_formatting.add("F{}:F{}".format(KA_F, KA_L),
    CellIsRule(operator="lessThan", formula=["-0.05"], fill=PatternFill("solid", fgColor=RED),
               font=Font(name=F, size=9, bold=True, color=RED_T)))
wsK.conditional_formatting.add("C{}:C{}".format(KA_F, KA_L),
    ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="A9D08E"))
KA_CH = min(KA_L, KA_F + 19)
cC = BarChart(); cC.type = "col"; cC.title = "CMJ: primeiro teste × teste mais recente (cm)"
cC.height = 9; cC.width = 20
cC.add_data(Reference(wsK, min_col=4, max_col=5, min_row=30, max_row=KA_CH), titles_from_data=True)
cC.set_categories(Reference(wsK, min_col=1, min_row=KA_F, max_row=KA_CH))
wsK.add_chart(cC, "K67")
cFR = BarChart(); cFR.type = "bar"; cFR.title = "Força Relativa no Agachamento (× massa corporal)"
cFR.height = 10; cFR.width = 20; cFR.legend = None
cFR.add_data(Reference(wsK, min_col=3, min_row=30, max_row=KA_CH), titles_from_data=True)
cFR.set_categories(Reference(wsK, min_col=1, min_row=KA_F, max_row=KA_CH))
wsK.add_chart(cFR, "K86")
wsK.freeze_panes = "A11"
