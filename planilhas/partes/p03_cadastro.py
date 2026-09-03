# ============================================================================
# 3) CADASTRO DE ATLETAS  (identificação + socioeconômico + histórico + saúde)
# ============================================================================
wsC = wb.create_sheet("Cadastro")
banner(wsC, "CADASTRO DE ATLETAS — FICHA COMPLETA",
       "Uma linha por atleta. Blocos: Identificação · Antropometria (puxada da aba Antropometria) · Contato · "
       "Socioeconômico · Histórico Esportivo · Saúde · Situação.", 69, NAVY2)

# --- parâmetro de referência ------------------------------------------------
rotulo(wsC, 4, 2, "Salário mínimo de referência (R$):")
entrada(wsC, 4, 5, 1518.00, 'R$ #,##0.00')
wsC["E4"].comment = Comment("Valor usado para converter a renda familiar em faixas de salários mínimos.\n"
                            "Pré-preenchido com R$ 1.518,00 (salário mínimo nacional de 2025).\n"
                            "ATUALIZE para o valor vigente.", "Planilha")
nota(wsC, 5, 2, "LGPD — esta aba armazena dados pessoais e de saúde (dados sensíveis). Colete somente o necessário, "
     "com consentimento por escrito do atleta (ou do responsável, se menor), e restrinja o acesso ao arquivo.", 40)

GRUPOS = [("IDENTIFICAÇÃO", 1, 12, NAVY),
          ("ANTROPOMETRIA (puxada da aba Antropometria)", 13, 17, "1F6F4A"),
          ("CONTATO", 18, 25, BLUE3),
          ("SOCIOECONÔMICO", 26, 48, GOLD),
          ("HISTÓRICO ESPORTIVO", 49, 54, "6B3FA0"),
          ("SAÚDE", 55, 66, RED_T),
          ("SITUAÇÃO", 67, 69, GREY_T)]
for txt, c1, c2, cor in GRUPOS:
    wsC.merge_cells(start_row=6, start_column=c1, end_row=6, end_column=c2)
    c = wsC.cell(6, c1, txt)
    c.font = Font(name=F, size=9, bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=cor)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = BORDER
wsC.row_dimensions[6].height = 18

CAD_H = [
 # IDENTIFICAÇÃO (1-12)
 "ID","Nome Completo","Nome na Equipe","Data de Nasc.","Idade","Sexo","Nacionalidade","Naturalidade (Cidade/UF)",
 "Documento (RG/CPF)","Nº Camisa","Categoria","Posição",
 # ANTROPOMETRIA automática (13-17)
 "Dominância de Mão","Perna de Impulsão","Estatura (cm)","Massa (kg)","IMC",
 # CONTATO (18-25)
 "Telefone","E-mail","Endereço","Cidade / UF","CEP","Contato de Emergência","Telefone de Emergência","Parentesco",
 # SOCIOECONÔMICO (26-47)
 "Escolaridade","Situação de Estudo","Turno de Estudo","Instituição de Ensino","Trabalha?","Horas de Trabalho / Semana",
 "Ocupação","Renda Familiar (R$)","Nº de Pessoas no Domicílio","Renda per Capita (R$)","Faixa de Renda (SM)",
 "Classe Econômica (Critério Brasil)","Tipo de Moradia","Reside com","Transporte para o Treino",
 "Tempo de Deslocamento (min)","Recebe Bolsa / Auxílio?","Valor da Bolsa (R$)","Benefício Social",
 "Plano de Saúde","Acesso à Internet em Casa","Refeições por Dia","Acompanhamento Nutricional",
 # HISTÓRICO ESPORTIVO (48-53)
 "Idade de Início no Vôlei","Anos de Prática","Anos de Treino de Força","Nível Competitivo Máximo",
 "Clubes Anteriores","Seleções / Convocações",
 # SAÚDE (54-65)
 "Tipo Sanguíneo","Alergias","Medicamentos em Uso","Cirurgias Prévias","Lesões Prévias (região)",
 "Nº de Lesões (12 meses)","Queixa / Dor Atual","Data do Atestado Médico","Validade do Atestado",
 "Situação do Atestado","PAR-Q Respondido?","Usa Óculos / Lentes?",
 # SITUAÇÃO (66-69)
 "Data de Entrada na Equipe","Status","Observações","últ. aval."]
cab_tabela(wsC, 7, CAD_H)
larguras(wsC, {"A":9,"B":26,"C":16,"D":13,"E":7,"F":11,"G":13,"H":19,"I":16,"J":8,"K":10,"L":18,
               "M":14,"N":15,"O":12,"P":11,"Q":8,
               "R":15,"S":26,"T":30,"U":18,"V":12,"W":24,"X":18,"Y":13,
               "Z":22,"AA":18,"AB":14,"AC":24,"AD":11,"AE":15,"AF":20,"AG":16,"AH":13,"AI":15,"AJ":15,
               "AK":20,"AL":16,"AM":18,"AN":22,"AO":15,"AP":16,"AQ":15,"AR":18,"AS":14,"AT":16,"AU":12,"AV":18,
               "AW":15,"AX":12,"AY":15,"AZ":22,"BA":26,"BB":22,
               "BC":11,"BD":20,"BE":22,"BF":22,"BG":24,"BH":13,"BI":22,"BJ":14,"BK":14,"BL":16,"BM":14,"BN":14,
               "BO":15,"BP":14,"BQ":26,"BR":11})

ANT = "Antropometria"
for r in range(CAD_F, CAD_L + 1):
    wsC.cell(r, 1,  '=IF($B{0}="","","ATL-"&TEXT(ROW()-{1},"000"))'.format(r, CAD_F - 1))
    wsC.cell(r, 5,  '=IFERROR(DATEDIF($D{0},TODAY(),"Y"),"")'.format(r))
    # última avaliação antropométrica do atleta (coluna auxiliar BR = 70)
    wsC.cell(r, 70, '=IF($B{0}="",0,IFERROR(SUMPRODUCT(MAX(({1}!$B$8:$B$407=$B{0})*{1}!$A$8:$A$407)),0))'.format(r, ANT))
    for col, src in ((15, "F"), (16, "E")):     # estatura, massa
        wsC.cell(r, col, '=IF(OR($B{0}="",$BR{0}=0),"",IFERROR(AVERAGEIFS({1}!${2}$8:${2}$407,'
                         '{1}!$B$8:$B$407,$B{0},{1}!$A$8:$A$407,$BR{0}),""))'.format(r, ANT, src))
    wsC.cell(r, 17, '=IFERROR(ROUND($P{0}/($O{0}/100)^2,1),"")'.format(r))
    wsC.cell(r, 35, '=IFERROR($AG{0}/$AH{0},"")'.format(r))                       # renda per capita
    wsC.cell(r, 36, '=IF(OR($AG{0}="",$E$4=""),"",IF($AG{0}<=$E$4,"Até 1 SM",'    # faixa em SM
                    'IF($AG{0}<=2*$E$4,"1 a 2 SM",IF($AG{0}<=3*$E$4,"2 a 3 SM",'
                    'IF($AG{0}<=5*$E$4,"3 a 5 SM",IF($AG{0}<=10*$E$4,"5 a 10 SM","Acima de 10 SM"))))))'.format(r))
    wsC.cell(r, 50, '=IFERROR($E{0}-$AW{0},"")'.format(r))                        # anos de prática
    wsC.cell(r, 64, '=IF($BK{0}="","",IF($BK{0}<TODAY(),"VENCIDO",'               # situação do atestado
                    'IF($BK{0}<=TODAY()+30,"Vence em 30 dias","Válido")))'.format(r))
corpo_tabela(wsC, CAD_F, CAD_L, 1, 70)
CALCULADAS = (1, 5, 15, 16, 17, 35, 36, 50, 64, 70)
for r in range(CAD_F, CAD_L + 1):
    for c in range(1, 71):
        if c in CALCULADAS:
            wsC.cell(r, c).font = Font(name=F, size=9, bold=True, color=NAVY2)
            wsC.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
        else:
            wsC.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
            wsC.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    for c in (2, 8, 19, 20, 21, 29, 32, 51, 52, 53, 55, 56, 57, 58, 61, 68):
        wsC.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for c in (4, 62, 63, 67):
        wsC.cell(r, c).number_format = NF_DATE
    wsC.cell(r, 15).number_format = '0.0;;""'
    wsC.cell(r, 16).number_format = '0.0;;""'
    wsC.cell(r, 17).number_format = '0.0;;""'
    for c in (33, 35, 43):
        wsC.cell(r, c).number_format = 'R$ #,##0.00;;""'
    wsC.cell(r, 70).number_format = NF_DATE
wsC.column_dimensions["BR"].hidden = True

DVS = [("Sexo","F"),("Categoria","K"),("Posição","L"),("Dominância","M"),("Perna de Impulsão","N"),
       ("Escolaridade","Z"),("Situação de Estudo","AA"),("Turno","AB"),("Sim/Não","AD"),
       ("Classe Econômica","AK"),("Tipo de Moradia","AL"),("Reside com","AM"),("Transporte","AN"),
       ("Sim/Não","AP"),("Sim/Não","AR"),("Sim/Não","AS"),("Sim/Não","AT"),("Sim/Não","AV"),
       ("Nível Competitivo","AZ"),("Tipo Sanguíneo","BC"),("Região Corporal","BG"),("Região Corporal","BI"),
       ("Sim/Não","BM"),("Sim/Não","BN"),("Status do Atleta","BP")]
for lista, col in DVS:
    dv(wsC, L(lista), "{0}{1}:{0}{2}".format(col, CAD_F, CAD_L))
wsC.conditional_formatting.add("BP{}:BP{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"Ativo"'], fill=PatternFill("solid", fgColor=GREEN),
               font=Font(name=F, size=9, bold=True, color=GREEN_T)))
for txt in ('"Lesionado"', '"Departamento Médico"'):
    wsC.conditional_formatting.add("BP{}:BP{}".format(CAD_F, CAD_L),
        CellIsRule(operator="equal", formula=[txt], fill=PatternFill("solid", fgColor=RED),
                   font=Font(name=F, size=9, bold=True, color=RED_T)))
wsC.conditional_formatting.add("BL{}:BL{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"VENCIDO"'], fill=PatternFill("solid", fgColor=RED),
               font=Font(name=F, size=9, bold=True, color=RED_T)))
wsC.conditional_formatting.add("BL{}:BL{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"Vence em 30 dias"'], fill=PatternFill("solid", fgColor=YELL),
               font=Font(name=F, size=9, bold=True, color=YELL_T)))
wsC.conditional_formatting.add("BL{}:BL{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"Válido"'], fill=PatternFill("solid", fgColor=GREEN),
               font=Font(name=F, size=9, bold=True, color=GREEN_T)))
wsC.freeze_panes = "C8"
wsC.auto_filter.ref = "A7:BQ{}".format(CAD_L)

# ---- 12 atletas de exemplo (voleibol masculino adulto) ---------------------
EXEMPLO = [
 ("Rafael Monteiro Alves","Rafa",1998,3,14,"Levantador",5,"Destro","Esquerda",196,7,"Superior em andamento",
  "Cursando","Noturno","Não",0,"Atleta profissional",7800,3,"B1","Própria","Família","Carro próprio",25,
  "Sim",2500,"Não","Sim","Sim",6,"Sim",11,4,"Seleção estadual"),
 ("Diego Salgado Ferraz","Diego",1996,8,2,"Oposto",12,"Canhoto","Esquerda",202,9,"Superior completo",
  "Concluído","—","Não",0,"Atleta profissional",9500,2,"B1","Alugada","Cônjuge","Carro próprio",20,
  "Sim",3200,"Não","Sim","Sim",6,"Sim",12,6,"Seleção nacional Sub-21"),
 ("Lucas Prado Bittencourt","Lucas",2000,1,27,"Ponteiro (Ponta)",7,"Destro","Esquerda",198,6,"Superior em andamento",
  "Cursando","Matutino","Não",0,"Atleta profissional",6200,4,"B2","Própria","Família","Transporte do clube",35,
  "Sim",2000,"Não","Sim","Sim",5,"Sim",13,3,"Seleção estadual"),
 ("Bruno Rezende Camargo","Bruninho",1999,11,5,"Ponteiro (Ponta)",9,"Destro","Esquerda",197,5,"Superior em andamento",
  "Cursando","Noturno","Sim",20,"Estagiário",5400,4,"C1","Alugada","Família","Transporte público",55,
  "Sim",1600,"Sim","Não","Sim",4,"Não",12,3,"—"),
 ("Thiago Nogueira Vasques","Thiago",1995,5,19,"Central",4,"Destro","Direita",205,8,"Superior completo",
  "Concluído","—","Não",0,"Atleta profissional",11000,3,"A","Própria","Família","Carro próprio",18,
  "Sim",4000,"Não","Sim","Sim",6,"Sim",10,8,"Seleção nacional adulta"),
 ("Matheus Caldeira Lins","Matheus",2001,9,8,"Central",15,"Destro","Esquerda",203,7,"Superior em andamento",
  "Cursando","Noturno","Não",0,"Atleta profissional",5800,5,"C1","Cedida","Alojamento do clube","A pé",10,
  "Sim",1800,"Sim","Sim","Sim",5,"Sim",14,2,"—"),
 ("Felipe Andrade Rocha","Felipão",2003,2,11,"Líbero",2,"Destro","Direita",184,4,"Superior em andamento",
  "Cursando","Matutino","Não",0,"Atleta profissional",4200,4,"C2","Alugada","Alojamento do clube","Transporte do clube",30,
  "Sim",1500,"Sim","Não","Sim",5,"Sim",12,2,"Seleção estadual Sub-19"),
 ("Gustavo Peixoto Maia","Gu",1997,7,23,"Ponteiro (Ponta)",11,"Destro","Esquerda",199,7,"Superior completo",
  "Concluído","—","Não",0,"Atleta profissional",8300,2,"B1","Própria","Cônjuge","Carro próprio",22,
  "Sim",2800,"Não","Sim","Sim",6,"Sim",11,7,"—"),
 ("Vinícius Barreto Duarte","Vini",2002,12,3,"Levantador",6,"Destro","Esquerda",192,6,"Superior em andamento",
  "Cursando","Noturno","Não",0,"Atleta profissional",4800,5,"C2","Cedida","Alojamento do clube","A pé",8,
  "Sim",1500,"Sim","Não","Sim",5,"Sim",13,2,"—"),
 ("André Luiz Sampaio","Dedé",1994,4,30,"Oposto",18,"Destro","Esquerda",201,8,"Superior completo",
  "Concluído","—","Não",0,"Atleta profissional",12500,4,"A","Própria","Família","Carro próprio",15,
  "Sim",4500,"Não","Sim","Sim",6,"Sim",10,9,"Seleção nacional adulta"),
 ("Pedro Henrique Coutinho","PH",2004,6,17,"Central",3,"Destro","Direita",204,6,"Ensino Médio completo",
  "Concluído","—","Não",0,"Atleta em formação",3600,6,"D-E","Cedida","Alojamento do clube","A pé",5,
  "Sim",1200,"Sim","Não","Sim",5,"Sim",13,1,"Seleção estadual Sub-21"),
 ("Caio Fernandes Bastos","Caio",2001,10,9,"Líbero",1,"Canhoto","Direita",186,4,"Superior em andamento",
  "Cursando","Matutino","Sim",12,"Auxiliar administrativo",5100,3,"C1","Alugada","Família","Transporte público",45,
  "Não",0,"Não","Sim","Sim",4,"Não",12,3,"—"),
]
LESOES_EX = [("—",0,"—"),("Entorse de tornozelo D",1,"—"),("—",0,"—"),
             ("Tendinopatia patelar",2,"Dor anterior no joelho D (leve)"),("Lombalgia",1,"—"),
             ("—",0,"—"),("Entorse de tornozelo E",1,"—"),("Tendinopatia de ombro D",1,"—"),
             ("—",0,"—"),("Cirurgia de ombro D (2021)",0,"—"),("—",0,"—"),("Entorse de dedo",1,"—")]
for i, a in enumerate(EXEMPLO):
    r = CAD_F + i
    (nome, apel, ay, am, ad, pos, cam, dom, perna, est, cam2, esc, sit, turno, trab, horas, ocup,
     renda, pes, classe, mor, reside, transp, desloc, bolsa, vbolsa, benef, plano, net, refs, nutri,
     ini, forca, selec) = a
    V = {2:nome, 3:apel, 4:date(ay,am,ad), 6:"Masculino", 7:"Brasileira", 8:"—", 9:"—", 10:cam,
         11:"Adulto", 12:pos, 13:dom, 14:perna,
         18:"(00) 90000-00{:02d}".format(i+1), 19:"atleta{}@clube.com.br".format(i+1), 20:"—",
         21:"—", 22:"—", 23:"Responsável / familiar", 24:"(00) 90000-10{:02d}".format(i+1), 25:"—",
         26:esc, 27:sit, 28:turno, 29:"—", 30:trab, 31:horas, 32:ocup, 33:renda, 34:pes,
         37:classe, 38:mor, 39:reside, 40:transp, 41:desloc, 42:bolsa, 43:vbolsa, 44:benef,
         45:plano, 46:net, 47:refs, 48:nutri, 49:ini, 51:forca,
         52:"Superliga B" if i % 3 else "Superliga A", 53:"—", 54:selec,
         55:"O+", 56:"—", 57:"—", 58:LESOES_EX[i][0] if "Cirurgia" in LESOES_EX[i][0] else "—",
         59:LESOES_EX[i][0], 60:LESOES_EX[i][1], 61:LESOES_EX[i][2],
         62:date(2026,1,12), 63:date(2027,1,12), 65:"Sim", 66:"Não" if i % 4 else "Sim",
         67:date(2026,1,5), 68:"Lesionado" if i == 3 else "Ativo", 69:"EXEMPLO — substituir"}
    for c, v in V.items():
        wsC.cell(r, c, v)
        if isinstance(v, date):
            wsC.cell(r, c).number_format = NF_DATE
NOMES = [a[0] for a in EXEMPLO]
EST_EX = {a[0]: a[9] for a in EXEMPLO}
POS_EX = {a[0]: a[5] for a in EXEMPLO}
