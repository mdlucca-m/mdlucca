# ============================================================================
# 22) SALTOS — carga de saltos (pliometria + quadra + jogo)
# ============================================================================
wsS2 = wb.create_sheet("Saltos")
SLT_F, SLT_L = 8, 807
banner(wsS2, "CARGA DE SALTOS — PLIOMETRIA, QUADRA E JOGO",
       "O salto é a carga externa que mais explica lesão por sobrecarga no voleibol. Registre TODOS os saltos: "
       "contatos pliométricos da musculação, saltos de treino de quadra e saltos de jogo.", 13, "6B3FA0")
larguras(wsS2, {"A":12,"B":8,"C":24,"D":20,"E":34,"F":16,"G":14,"H":20,"I":15,"J":17,"K":18,"L":16,"M":26,"N":3,
                "O":24,"P":15,"Q":14,"R":13,"S":15,"T":18,"U":11,"V":22})
SLT_H = ["Data","Semana","Atleta","Origem","Exercício / Contexto","Nº de Saltos ou Contatos","Intensidade",
         "Superfície","Altura da Caixa (cm)","Altura Média do Salto (cm)","% de Saltos > 80% do Máx",
         "Qualidade Técnica (1-5)","Observações"]
cab_tabela(wsS2, 7, SLT_H)
rotulo(wsS2, 4, 15, "Semana de referência:")
entrada(wsS2, 4, 18, '=IFERROR(MAX(1,INT((TODAY()-Macrociclo!$C$11)/7)+1),1)', '0')
nota(wsS2, 4, 1, "Referências de dose: programas pliométricos com mais de 10 semanas, mais de 20 sessões e mais de 50 "
     "saltos por sessão, combinando tipos de salto, maximizam o ganho de impulsão (Sáez de Villarreal et al., 2009). "
     "Em temporada, equipes universitárias masculinas chegam a ~466 saltos semanais no mesociclo competitivo "
     "(Lin et al., 2024). O alerta aqui é o SALTO SEMANAL e a variação brusca em relação à semana anterior.", 13)
wsS2.row_dimensions[4].height = 30
for r in range(SLT_F, SLT_L + 1):
    wsS2.cell(r, 2, '=IF($A{0}="",0,INT(($A{0}-Macrociclo!$C$11)/7)+1)'.format(r))
corpo_tabela(wsS2, SLT_F, SLT_L, 1, 13)
for r in range(SLT_F, SLT_L + 1):
    for c in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13):
        wsS2.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
        wsS2.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    wsS2.cell(r, 2).font = Font(name=F, size=9, bold=True, color=NAVY2)
    wsS2.cell(r, 2).fill = PatternFill("solid", fgColor=LIGHT)
    for c in (3, 4, 5, 13):
        wsS2.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsS2.cell(r, 1).number_format = NF_DATE
    wsS2.cell(r, 2).number_format = '0;;""'
    for c in (6, 9, 10):
        wsS2.cell(r, c).number_format = '0;;""'
    wsS2.cell(r, 11).number_format = NF_PCT
dv(wsS2, ATLETAS_REF,          "C{}:C{}".format(SLT_F, SLT_L))
dv(wsS2, L("Origem do Salto"), "D{}:D{}".format(SLT_F, SLT_L))
dv(wsS2, L("Intensidade"),     "G{}:G{}".format(SLT_F, SLT_L))
dv(wsS2, L("Superfície"),      "H{}:H{}".format(SLT_F, SLT_L))

secao(wsS2, 5, "RESUMO SEMANAL POR ATLETA", 22, 15)
cab_tabela(wsS2, 7, ["Atleta","Pliometria","Quadra","Jogo","Total da Semana","Semana Anterior","Variação",
                     "Situação"], col0=15)
SLT_RF = SLT_F
SLT_RL = SLT_F + (CAD_L - CAD_F)
for i in range(CAD_L - CAD_F + 1):
    r = SLT_RF + i
    a = CAD_F + i
    wsS2.cell(r, 15, '=IF(Cadastro!$B{0}="","",Cadastro!$B{0})'.format(a))
    for j, orig in enumerate(["Pliometria", "Treino de quadra", "Jogo"]):
        wsS2.cell(r, 16 + j, '=IF($O{0}="",0,SUMIFS($F${1}:$F${2},$C${1}:$C${2},$O{0},'
                             '$B${1}:$B${2},$R$4,$D${1}:$D${2},"{3}"))'.format(r, SLT_F, SLT_L, orig))
    wsS2.cell(r, 19, '=SUM($P{0}:$R{0})+IF($O{0}="",0,SUMIFS($F${1}:$F${2},$C${1}:$C${2},$O{0},'
                     '$B${1}:$B${2},$R$4,$D${1}:$D${2},"Musculação"))'.format(r, SLT_F, SLT_L))
    wsS2.cell(r, 20, '=IF($O{0}="",0,SUMIFS($F${1}:$F${2},$C${1}:$C${2},$O{0},$B${1}:$B${2},$R$4-1))'
             .format(r, SLT_F, SLT_L))
    wsS2.cell(r, 21, '=IF($T{0}=0,0,$S{0}/$T{0}-1)'.format(r))
    wsS2.cell(r, 22, '=IF($O{0}="","",IF($S{0}=0,"Sem registro",IF($U{0}>0.3,"ALERTA — aumento acima de 30%",'
                     'IF($S{0}>600,"Volume semanal muito alto",IF($S{0}>=350,"Volume alto",'
                     'IF($S{0}>=150,"Volume adequado","Volume baixo"))))))'.format(r))
corpo_tabela(wsS2, SLT_RF, SLT_RL, 15, 22)
for r in range(SLT_RF, SLT_RL + 1):
    for c in range(15, 23):
        wsS2.cell(r, c).font = Font(name=F, size=9, bold=(c == 19), color=NAVY2)
        wsS2.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT if (r - SLT_RF) % 2 == 0 else LIGHT2)
    for c in (15, 22):
        wsS2.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for c in range(16, 21):
        wsS2.cell(r, c).number_format = NF_UA
    wsS2.cell(r, 21).number_format = '+0%;-0%;""'
for txt, fill, ft in [('"Volume adequado"', GREEN, GREEN_T), ('"Volume alto"', YELL, YELL_T),
                      ('"Volume semanal muito alto"', RED, RED_T),
                      ('"ALERTA — aumento acima de 30%"', RED, RED_T), ('"Volume baixo"', "DDEBF7", NAVY2)]:
    wsS2.conditional_formatting.add("V{}:V{}".format(SLT_RF, SLT_RL),
        CellIsRule(operator="equal", formula=[txt], fill=PatternFill("solid", fgColor=fill),
                   font=Font(name=F, size=9, bold=True, color=ft)))
chS = BarChart(); chS.type = "col"; chS.grouping = "stacked"; chS.overlap = 100
chS.title = "Saltos da Semana por Atleta (origem)"; chS.height = 9; chS.width = 20
chS.add_data(Reference(wsS2, min_col=16, max_col=18, min_row=7, max_row=min(SLT_RL, SLT_RF + 19)),
             titles_from_data=True)
chS.set_categories(Reference(wsS2, min_col=15, min_row=SLT_RF, max_row=min(SLT_RL, SLT_RF + 19)))
wsS2.add_chart(chS, "X7")
wsS2.freeze_panes = "C8"
wsS2.auto_filter.ref = "A7:M{}".format(SLT_L)
