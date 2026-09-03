# ============================================================================
# 12) TESTES FÍSICOS  (bateria geral + específica do voleibol)
# ============================================================================
wsT = wb.create_sheet("Testes")
banner(wsT, "AVALIAÇÕES E TESTES FÍSICOS", "Bateria longitudinal. Impulsões, RSI, índice elástico e potência de pico "
       "são calculados automaticamente. Registre a melhor de 3 tentativas nos testes de salto, sprint e arremesso.", 29, "8A5A00")
TST_H = ["Data","Atleta","Momento","Avaliador","Massa (kg)",
         "Alcance em Pé (cm)","Alcance de Ataque (cm)","Alcance de Bloqueio (cm)",
         "Impulsão de Ataque (cm)","Impulsão de Bloqueio (cm)",
         "Squat Jump (cm)","CMJ (cm)","CMJ c/ Braços (cm)","Drop Jump 40 cm (cm)","Tempo de Contato DJ (s)",
         "RSI (m/s)","Índice Elástico (%)","Salto c/ Aproximação (cm)","Potência de Pico — Sayers (W)",
         "Sprint 5 m (s)","Sprint 10 m (s)","T-Test (s)","Sheppard Agility (s)","Arremesso Medicine Ball (m)",
         "Sentar-e-Alcançar (cm)","Yo-Yo IR1 (m)","IMTP Pico de Força (N)","Força Relativa IMTP (N/kg)","Observações"]
GRUPOS_T = [("IDENTIFICAÇÃO", 1, 5, NAVY), ("ALCANCES E IMPULSÕES (específico do voleibol)", 6, 10, "1F6F4A"),
            ("SALTOS E POTÊNCIA", 11, 19, GOLD), ("VELOCIDADE, AGILIDADE E OUTROS", 20, 26, BLUE3),
            ("FORÇA ISOMÉTRICA", 27, 28, RED_T), ("", 29, 29, GREY_T)]
for txt, c1, c2, cor in GRUPOS_T:
    wsT.merge_cells(start_row=6, start_column=c1, end_row=6, end_column=c2)
    c = wsT.cell(6, c1, txt)
    c.font = Font(name=F, size=9, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=cor)
    c.alignment = Alignment(horizontal="center", vertical="center"); c.border = BORDER
wsT.row_dimensions[6].height = 18
cab_tabela(wsT, 7, TST_H)
larguras(wsT, {"A":12,"B":24,"C":18,"D":18,"E":11,"F":14,"G":16,"H":16,"I":15,"J":15,
               "K":13,"L":11,"M":14,"N":15,"O":16,"P":11,"Q":14,"R":16,"S":18,
               "T":12,"U":12,"V":11,"W":16,"X":18,"Y":15,"Z":13,"AA":15,"AB":16,"AC":28})
nota(wsT, 4, 1, "RSI (Reactive Strength Index) = altura do drop jump (m) ÷ tempo de contato (s).  •  "
     "Índice Elástico = (CMJ − Squat Jump) ÷ Squat Jump — quanto o atleta aproveita do ciclo alongamento-encurtamento.  •  "
     "Potência de Pico pela equação de Sayers et al. (1999): P = 60,7 × CMJ(cm) + 45,3 × massa(kg) − 2055.", 29)
wsT.row_dimensions[4].height = 26
for r in range(TST_F, TST_L + 1):
    wsT.cell(r,  9, '=IF(OR($G{0}="",$F{0}=""),"",$G{0}-$F{0})'.format(r))
    wsT.cell(r, 10, '=IF(OR($H{0}="",$F{0}=""),"",$H{0}-$F{0})'.format(r))
    wsT.cell(r, 16, '=IF(OR($N{0}="",$O{0}="",$O{0}=0),"",($N{0}/100)/$O{0})'.format(r))
    wsT.cell(r, 17, '=IF(OR($K{0}="",$L{0}="",$K{0}=0),"",($L{0}-$K{0})/$K{0})'.format(r))
    wsT.cell(r, 19, '=IF(OR($L{0}="",$E{0}=""),"",60.7*$L{0}+45.3*$E{0}-2055)'.format(r))
    wsT.cell(r, 28, '=IF(OR($AA{0}="",$E{0}="",$E{0}=0),"",$AA{0}/$E{0})'.format(r))
corpo_tabela(wsT, TST_F, TST_L, 1, 29)
CALC_T = (9, 10, 16, 17, 19, 28)
for r in range(TST_F, TST_L + 1):
    for c in range(1, 30):
        if c in CALC_T:
            wsT.cell(r, c).font = Font(name=F, size=9, bold=True, color=NAVY2)
            wsT.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
        else:
            wsT.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
            wsT.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    for c in (2, 4, 29):
        wsT.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsT.cell(r, 1).number_format = NF_DATE
    for c in (5, 11, 12, 13, 14, 18, 24, 25):
        wsT.cell(r, c).number_format = '0.0;;""'
    for c in (6, 7, 8, 9, 10, 26):
        wsT.cell(r, c).number_format = '0;;""'
    for c in (15,):
        wsT.cell(r, c).number_format = '0.000;;""'
    for c in (16, 20, 21, 22, 23, 28):
        wsT.cell(r, c).number_format = '0.00;;""'
    wsT.cell(r, 17).number_format = NF_PCT1
    wsT.cell(r, 19).number_format = NF_UA
    wsT.cell(r, 27).number_format = NF_UA
dv(wsT, ATLETAS_REF,          "B{}:B{}".format(TST_F, TST_L))
dv(wsT, L("Momento do Teste"),"C{}:C{}".format(TST_F, TST_L))
wsT.conditional_formatting.add("I{}:I{}".format(TST_F, TST_L),
    ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="A9D08E"))
wsT.conditional_formatting.add("L{}:L{}".format(TST_F, TST_L),
    ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="9CC3E5"))
wsT.freeze_panes = "C8"
wsT.auto_filter.ref = "A7:AC{}".format(TST_L)
