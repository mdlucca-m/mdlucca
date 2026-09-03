# ============================================================================
# 16) ANTROPOMETRIA  (perfil restrito ISAK + composição corporal + somatotipo)
# ============================================================================
wsAn = wb.create_sheet("Antropometria")
ANT_F, ANT_L = 8, 407
banner(wsAn, "ANTROPOMETRIA E COMPOSIÇÃO CORPORAL",
       "Avaliações longitudinais. Preencha as medidas em amarelo; densidade, % de gordura, massa magra, índices e "
       "somatotipo são calculados. Sexo e data de nascimento são lidos do Cadastro.", 48, "1F6F4A")
ANT_H = ["Data","Atleta","Momento","Avaliador","Massa (kg)","Estatura (cm)","Estatura Sentado (cm)","Envergadura (cm)",
         # dobras 9-18
         "Tríceps","Subescapular","Bíceps","Peitoral","Axilar Média","Suprailíaca","Supraespinhal","Abdominal",
         "Coxa Medial","Perna Medial",
         # perímetros 19-28
         "Braço Relaxado","Braço Contraído","Antebraço","Tórax","Cintura","Abdômen","Quadril","Coxa (1/3)",
         "Perna","Punho",
         # diâmetros 29-32
         "Biacromial","Biileocristal","Úmero","Fêmur",
         # calculados 33-48
         "Idade na Avaliação","Σ 4 Dobras (mm)","Σ 7 Dobras JP (mm)","Σ 8 Dobras (mm)","Densidade Corporal",
         "% de Gordura","Massa Gorda (kg)","Massa Magra (kg)","IMC","Índice Córmico","Cintura / Estatura",
         "AMB (cm²)","Endomorfia","Mesomorfia","Ectomorfia","Somatotipo Dominante"]
GRUPOS_A = [("IDENTIFICAÇÃO E MEDIDAS BÁSICAS", 1, 8, NAVY),
            ("DOBRAS CUTÂNEAS (mm)", 9, 18, GOLD),
            ("PERÍMETROS (cm)", 19, 28, BLUE3),
            ("DIÂMETROS ÓSSEOS (cm)", 29, 32, "6B3FA0"),
            ("CALCULADOS", 33, 48, "1F6F4A")]
for txt, c1, c2, cor in GRUPOS_A:
    wsAn.merge_cells(start_row=6, start_column=c1, end_row=6, end_column=c2)
    c = wsAn.cell(6, c1, txt)
    c.font = Font(name=F, size=9, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=cor)
    c.alignment = Alignment(horizontal="center", vertical="center"); c.border = BORDER
wsAn.row_dimensions[6].height = 18
cab_tabela(wsAn, 7, ANT_H)
larguras(wsAn, dict([("A",12),("B",24),("C",18),("D",16),("E",11),("F",12),("G",15),("H",15)] +
                    [(get_column_letter(i), 11) for i in range(9, 33)] +
                    [("AG",15),("AH",13),("AI",15),("AJ",13),("AK",14),("AL",12),("AM",13),("AN",13),
                     ("AO",9),("AP",13),("AQ",14),("AR",11),("AS",12),("AT",12),("AU",12),("AV",20)]))
nota(wsAn, 4, 1, "Protocolo: perfil restrito ISAK. Dobras em mm, perímetros e diâmetros em cm.  •  "
     "% de gordura pela equação de 7 dobras de Jackson & Pollock (1978 masculino / 1980 feminino) com conversão de "
     "Siri (1961) — a planilha escolhe a equação pelo sexo cadastrado.  •  Somatotipo pelo método Heath-Carter.  •  "
     "Σ 7 Dobras JP = peitoral + axilar média + tríceps + subescapular + abdominal + suprailíaca + coxa medial.", 48)
wsAn.row_dimensions[4].height = 34

CADR = "Cadastro!$B${}:$B${}".format(CAD_F, CAD_L)
def cadcol(letra):
    return "Cadastro!${0}${1}:${0}${2}".format(letra, CAD_F, CAD_L)

for r in range(ANT_F, ANT_L + 1):
    # idade na data da avaliação
    wsAn.cell(r, 33, '=IFERROR(DATEDIF(INDEX({1},MATCH($B{0},{2},0)),$A{0},"Y"),"")'.format(r, cadcol("D"), CADR))
    wsAn.cell(r, 34, '=IF(COUNT($I{0},$K{0},$J{0},$N{0})<4,"",$I{0}+$K{0}+$J{0}+$N{0})'.format(r))
    wsAn.cell(r, 35, '=IF(COUNT($L{0},$M{0},$I{0},$J{0},$P{0},$N{0},$Q{0})<7,"",'
                     '$L{0}+$M{0}+$I{0}+$J{0}+$P{0}+$N{0}+$Q{0})'.format(r))
    wsAn.cell(r, 36, '=IF(COUNT($I{0},$J{0},$K{0},$O{0},$P{0},$Q{0},$R{0},$N{0})<8,"",'
                     '$I{0}+$J{0}+$K{0}+$O{0}+$P{0}+$Q{0}+$R{0}+$N{0})'.format(r))
    # densidade corporal — Jackson & Pollock 7 dobras, por sexo
    wsAn.cell(r, 37, '=IF(OR($AI{0}="",$AG{0}=""),"",IF(IFERROR(INDEX({1},MATCH($B{0},{2},0)),"")="Feminino",'
                     '1.097-0.00046971*$AI{0}+0.00000056*$AI{0}^2-0.00012828*$AG{0},'
                     '1.112-0.00043499*$AI{0}+0.00000055*$AI{0}^2-0.00028826*$AG{0}))'
                     .format(r, cadcol("F"), CADR))
    wsAn.cell(r, 38, '=IF(OR($AK{0}="",$AK{0}=0),"",495/$AK{0}-450)'.format(r))
    wsAn.cell(r, 39, '=IF(OR($AL{0}="",$E{0}=""),"",$E{0}*$AL{0}/100)'.format(r))
    wsAn.cell(r, 40, '=IF(OR($AM{0}="",$E{0}=""),"",$E{0}-$AM{0})'.format(r))
    wsAn.cell(r, 41, '=IFERROR($E{0}/($F{0}/100)^2,"")'.format(r))
    wsAn.cell(r, 42, '=IFERROR($G{0}/$F{0}*100,"")'.format(r))
    wsAn.cell(r, 43, '=IFERROR($W{0}/$F{0},"")'.format(r))
    # área muscular do braço
    wsAn.cell(r, 44, '=IF(OR($S{0}="",$I{0}=""),"",($S{0}-PI()*$I{0}/10)^2/(4*PI())'
                     '-IF(IFERROR(INDEX({1},MATCH($B{0},{2},0)),"")="Feminino",6.5,10))'
                     .format(r, cadcol("F"), CADR))
    # Heath-Carter
    wsAn.cell(r, 45, '=IF(OR($I{0}="",$J{0}="",$O{0}="",$F{0}=""),"",'
                     '-0.7182+0.1451*(($I{0}+$J{0}+$O{0})*(170.18/$F{0}))'
                     '-0.00068*(($I{0}+$J{0}+$O{0})*(170.18/$F{0}))^2'
                     '+0.0000014*(($I{0}+$J{0}+$O{0})*(170.18/$F{0}))^3)'.format(r))
    wsAn.cell(r, 46, '=IF(OR($AE{0}="",$AF{0}="",$T{0}="",$AA{0}="",$F{0}=""),"",'
                     '0.858*$AE{0}+0.601*$AF{0}+0.188*($T{0}-$I{0}/10)+0.161*($AA{0}-$R{0}/10)'
                     '-0.131*$F{0}+4.5)'.format(r))
    wsAn.cell(r, 47, '=IF(OR($E{0}="",$F{0}=""),"",IF($F{0}/$E{0}^(1/3)>=40.75,0.732*($F{0}/$E{0}^(1/3))-28.58,'
                     'IF($F{0}/$E{0}^(1/3)>=38.25,0.463*($F{0}/$E{0}^(1/3))-17.63,0.1)))'.format(r))
    wsAn.cell(r, 48, '=IF(OR($AS{0}="",$AT{0}="",$AU{0}=""),"",'
                     'IF(AND($AT{0}>=$AS{0},$AT{0}>=$AU{0}),"Mesomorfo dominante",'
                     'IF(AND($AU{0}>=$AS{0},$AU{0}>=$AT{0}),"Ectomorfo dominante","Endomorfo dominante")))'.format(r))
corpo_tabela(wsAn, ANT_F, ANT_L, 1, 48)
for r in range(ANT_F, ANT_L + 1):
    for c in range(1, 49):
        if c >= 33:
            wsAn.cell(r, c).font = Font(name=F, size=9, bold=(c in (38, 40, 48)), color=NAVY2)
            wsAn.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
        else:
            wsAn.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
            wsAn.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    for c in (2, 4, 48):
        wsAn.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsAn.cell(r, 1).number_format = NF_DATE
    for c in range(5, 33):
        wsAn.cell(r, c).number_format = '0.0;;""'
    for c in (33, 34, 35, 36):
        wsAn.cell(r, c).number_format = '0;;""'
    wsAn.cell(r, 37).number_format = '0.0000;;""'
    for c in (38, 39, 40, 41, 42, 44, 45, 46, 47):
        wsAn.cell(r, c).number_format = '0.0;;""'
    wsAn.cell(r, 43).number_format = '0.00;;""'
dv(wsAn, ATLETAS_REF,           "B{}:B{}".format(ANT_F, ANT_L))
dv(wsAn, L("Momento do Teste"), "C{}:C{}".format(ANT_F, ANT_L))
wsAn.conditional_formatting.add("AL{}:AL{}".format(ANT_F, ANT_L),
    ColorScaleRule(start_type="num", start_value=6, start_color=GREEN, mid_type="num", mid_value=14,
                   mid_color=YELL, end_type="num", end_value=22, end_color=RED))
wsAn.freeze_panes = "C8"
wsAn.auto_filter.ref = "A7:AV{}".format(ANT_L)
