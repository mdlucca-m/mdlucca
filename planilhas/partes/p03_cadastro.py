# ============================================================================
# 3) CADASTRO DE ATLETAS  (identificação + socioeconômico + histórico + saúde)
#    Sem qualquer campo financeiro: nenhuma renda, salário ou valor de bolsa.
# ============================================================================
wsC = wb.create_sheet("Cadastro")
banner(wsC, "CADASTRO DE ATLETAS — FICHA COMPLETA",
       "Uma linha por atleta. Blocos: Identificação · Antropometria (puxada da aba Antropometria) · Contato · "
       "Socioeconômico · Histórico Esportivo · Saúde · Situação.", 65, NAVY2)
nota(wsC, 4, 2, "LGPD — esta aba armazena dados pessoais e de saúde (dados sensíveis). Colete somente o necessário, "
     "com consentimento por escrito do atleta (ou do responsável, se menor), e restrinja o acesso ao arquivo. "
     "Por decisão do usuário, NENHUM dado financeiro do atleta é registrado aqui.", 40)

GRUPOS = [("IDENTIFICAÇÃO", 1, 12, NAVY),
          ("ANTROPOMETRIA (puxada da aba Antropometria)", 13, 17, "1F6F4A"),
          ("CONTATO", 18, 25, BLUE3),
          ("SOCIOECONÔMICO", 26, 44, GOLD),
          ("HISTÓRICO ESPORTIVO", 45, 50, "6B3FA0"),
          ("SAÚDE", 51, 62, RED_T),
          ("SITUAÇÃO", 63, 65, GREY_T)]
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
 # SOCIOECONÔMICO (26-44) — sem campos financeiros
 "Escolaridade","Situação de Estudo","Turno de Estudo","Instituição de Ensino","Trabalha?","Horas de Trabalho / Semana",
 "Ocupação","Nº de Pessoas no Domicílio","Classe Econômica (Critério Brasil)","Tipo de Moradia","Reside com",
 "Transporte para o Treino","Tempo de Deslocamento (min)","Recebe Bolsa / Auxílio?","Benefício Social",
 "Plano de Saúde","Acesso à Internet em Casa","Refeições por Dia","Acompanhamento Nutricional",
 # HISTÓRICO ESPORTIVO (45-50)
 "Idade de Início no Vôlei","Anos de Prática","Anos de Treino de Força","Nível Competitivo Máximo",
 "Clubes Anteriores","Seleções / Convocações",
 # SAÚDE (51-62)
 "Tipo Sanguíneo","Alergias","Medicamentos em Uso","Cirurgias Prévias","Lesões Prévias (região)",
 "Nº de Lesões (12 meses)","Queixa / Dor Atual","Data do Atestado Médico","Validade do Atestado",
 "Situação do Atestado","PAR-Q Respondido?","Usa Óculos / Lentes?",
 # SITUAÇÃO (63-65)
 "Data de Entrada na Equipe","Status","Observações",
 # auxiliar (66)
 "últ. aval."]
cab_tabela(wsC, 7, CAD_H)
larguras(wsC, {"A":9,"B":26,"C":16,"D":13,"E":7,"F":11,"G":13,"H":19,"I":16,"J":8,"K":10,"L":18,
               "M":14,"N":15,"O":12,"P":11,"Q":8,
               "R":15,"S":26,"T":30,"U":18,"V":12,"W":24,"X":18,"Y":13,
               "Z":22,"AA":18,"AB":14,"AC":24,"AD":11,"AE":15,"AF":20,"AG":13,"AH":20,"AI":16,"AJ":18,
               "AK":22,"AL":15,"AM":16,"AN":14,"AO":14,"AP":16,"AQ":12,"AR":18,
               "AS":15,"AT":12,"AU":15,"AV":22,"AW":26,"AX":22,
               "AY":11,"AZ":20,"BA":22,"BB":22,"BC":24,"BD":13,"BE":22,"BF":14,"BG":14,"BH":16,"BI":14,"BJ":14,
               "BK":15,"BL":14,"BM":26,"BN":11})

ANT = "Antropometria"
for r in range(CAD_F, CAD_L + 1):
    wsC.cell(r, 1,  '=IF($B{0}="","","ATL-"&TEXT(ROW()-{1},"000"))'.format(r, CAD_F - 1))
    wsC.cell(r, 5,  '=IFERROR(DATEDIF($D{0},TODAY(),"Y"),"")'.format(r))
    # última avaliação antropométrica do atleta (coluna auxiliar BN = 66)
    wsC.cell(r, 66, '=IF($B{0}="",0,IFERROR(SUMPRODUCT(MAX(({1}!$B$8:$B$407=$B{0})*{1}!$A$8:$A$407)),0))'.format(r, ANT))
    for col, src in ((15, "F"), (16, "E")):     # estatura, massa
        wsC.cell(r, col, '=IF(OR($B{0}="",$BN{0}=0),"",IFERROR(AVERAGEIFS({1}!${2}$8:${2}$407,'
                         '{1}!$B$8:$B$407,$B{0},{1}!$A$8:$A$407,$BN{0}),""))'.format(r, ANT, src))
    wsC.cell(r, 17, '=IFERROR(ROUND($P{0}/($O{0}/100)^2,1),"")'.format(r))
    wsC.cell(r, 46, '=IFERROR($E{0}-$AS{0},"")'.format(r))                        # anos de prática
    wsC.cell(r, 60, '=IF($BG{0}="","",IF($BG{0}<TODAY(),"VENCIDO",'               # situação do atestado
                    'IF($BG{0}<=TODAY()+30,"Vence em 30 dias","Válido")))'.format(r))
corpo_tabela(wsC, CAD_F, CAD_L, 1, 66)
CALCULADAS = (1, 5, 15, 16, 17, 46, 60, 66)
for r in range(CAD_F, CAD_L + 1):
    for c in range(1, 67):
        if c in CALCULADAS:
            wsC.cell(r, c).font = Font(name=F, size=9, bold=True, color=NAVY2)
            wsC.cell(r, c).fill = PatternFill("solid", fgColor=LIGHT)
        else:
            wsC.cell(r, c).fill = PatternFill("solid", fgColor=GOLD_L)
            wsC.cell(r, c).font = Font(name=F, size=9, color="0000FF")
    for c in (2, 8, 19, 20, 21, 29, 32, 48, 49, 50, 52, 53, 54, 55, 57, 65):
        wsC.cell(r, c).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for c in (4, 58, 59, 63):
        wsC.cell(r, c).number_format = NF_DATE
    wsC.cell(r, 15).number_format = '0.0;;""'
    wsC.cell(r, 16).number_format = '0.0;;""'
    wsC.cell(r, 17).number_format = '0.0;;""'
    wsC.cell(r, 66).number_format = NF_DATE
wsC.column_dimensions["BN"].hidden = True

DVS = [("Sexo","F"),("Categoria","K"),("Posição","L"),("Dominância","M"),("Perna de Impulsão","N"),
       ("Escolaridade","Z"),("Situação de Estudo","AA"),("Turno","AB"),("Sim/Não","AD"),
       ("Classe Econômica","AH"),("Tipo de Moradia","AI"),("Reside com","AJ"),("Transporte","AK"),
       ("Sim/Não","AM"),("Sim/Não","AN"),("Sim/Não","AO"),("Sim/Não","AP"),("Sim/Não","AR"),
       ("Nível Competitivo","AV"),("Tipo Sanguíneo","AY"),("Região Corporal","BC"),("Região Corporal","BE"),
       ("Sim/Não","BI"),("Sim/Não","BJ"),("Status do Atleta","BL")]
for lista, col in DVS:
    dv(wsC, L(lista), "{0}{1}:{0}{2}".format(col, CAD_F, CAD_L))
wsC.conditional_formatting.add("BL{}:BL{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"Ativo"'], fill=PatternFill("solid", fgColor=GREEN),
               font=Font(name=F, size=9, bold=True, color=GREEN_T)))
for txt in ('"Lesionado"', '"Departamento Médico"'):
    wsC.conditional_formatting.add("BL{}:BL{}".format(CAD_F, CAD_L),
        CellIsRule(operator="equal", formula=[txt], fill=PatternFill("solid", fgColor=RED),
                   font=Font(name=F, size=9, bold=True, color=RED_T)))
wsC.conditional_formatting.add("BH{}:BH{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"VENCIDO"'], fill=PatternFill("solid", fgColor=RED),
               font=Font(name=F, size=9, bold=True, color=RED_T)))
wsC.conditional_formatting.add("BH{}:BH{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"Vence em 30 dias"'], fill=PatternFill("solid", fgColor=YELL),
               font=Font(name=F, size=9, bold=True, color=YELL_T)))
wsC.conditional_formatting.add("BH{}:BH{}".format(CAD_F, CAD_L),
    CellIsRule(operator="equal", formula=['"Válido"'], fill=PatternFill("solid", fgColor=GREEN),
               font=Font(name=F, size=9, bold=True, color=GREEN_T)))
wsC.freeze_panes = "C8"
wsC.auto_filter.ref = "A7:BM{}".format(CAD_L)

# ---- 12 atletas de exemplo (ELASE Voleibol Masculino Adulto) ---------------
EXEMPLO = [
 ("Rafael Monteiro Alves","Rafa",1998,3,14,"Levantador",5,"Destro","Esquerda",196,
  "Superior em andamento","Cursando","Noturno","Não",0,"Atleta profissional",3,"B1","Própria","Família",
  "Carro próprio",25,"Sim","Não","Sim","Sim",6,"Sim",11,4,"Seleção estadual"),
 ("Diego Salgado Ferraz","Diego",1996,8,2,"Oposto",12,"Canhoto","Esquerda",202,
  "Superior completo","Concluído","—","Não",0,"Atleta profissional",2,"B1","Alugada","Cônjuge",
  "Carro próprio",20,"Sim","Não","Sim","Sim",6,"Sim",12,6,"Seleção nacional Sub-21"),
 ("Lucas Prado Bittencourt","Lucas",2000,1,27,"Ponteiro (Ponta)",7,"Destro","Esquerda",198,
  "Superior em andamento","Cursando","Matutino","Não",0,"Atleta profissional",4,"B2","Própria","Família",
  "Transporte do clube",35,"Sim","Não","Sim","Sim",5,"Sim",13,3,"Seleção estadual"),
 ("Bruno Rezende Camargo","Bruninho",1999,11,5,"Ponteiro (Ponta)",9,"Destro","Esquerda",197,
  "Superior em andamento","Cursando","Noturno","Sim",20,"Estagiário",4,"C1","Alugada","Família",
  "Transporte público",55,"Sim","Sim","Não","Sim",4,"Não",12,3,"—"),
 ("Thiago Nogueira Vasques","Thiago",1995,5,19,"Central",4,"Destro","Direita",205,
  "Superior completo","Concluído","—","Não",0,"Atleta profissional",3,"A","Própria","Família",
  "Carro próprio",18,"Sim","Não","Sim","Sim",6,"Sim",10,8,"Seleção nacional adulta"),
 ("Matheus Caldeira Lins","Matheus",2001,9,8,"Central",15,"Destro","Esquerda",203,
  "Superior em andamento","Cursando","Noturno","Não",0,"Atleta profissional",5,"C1","Cedida","Alojamento do clube",
  "A pé",10,"Sim","Sim","Sim","Sim",5,"Sim",14,2,"—"),
 ("Felipe Andrade Rocha","Felipão",2003,2,11,"Líbero",2,"Destro","Direita",184,
  "Superior em andamento","Cursando","Matutino","Não",0,"Atleta profissional",4,"C2","Alugada","Alojamento do clube",
  "Transporte do clube",30,"Sim","Sim","Não","Sim",5,"Sim",12,2,"Seleção estadual Sub-19"),
 ("Gustavo Peixoto Maia","Gu",1997,7,23,"Ponteiro (Ponta)",11,"Destro","Esquerda",199,
  "Superior completo","Concluído","—","Não",0,"Atleta profissional",2,"B1","Própria","Cônjuge",
  "Carro próprio",22,"Sim","Não","Sim","Sim",6,"Sim",11,7,"—"),
 ("Vinícius Barreto Duarte","Vini",2002,12,3,"Levantador",6,"Destro","Esquerda",192,
  "Superior em andamento","Cursando","Noturno","Não",0,"Atleta profissional",5,"C2","Cedida","Alojamento do clube",
  "A pé",8,"Sim","Sim","Não","Sim",5,"Sim",13,2,"—"),
 ("André Luiz Sampaio","Dedé",1994,4,30,"Oposto",18,"Destro","Esquerda",201,
  "Superior completo","Concluído","—","Não",0,"Atleta profissional",4,"A","Própria","Família",
  "Carro próprio",15,"Sim","Não","Sim","Sim",6,"Sim",10,9,"Seleção nacional adulta"),
 ("Pedro Henrique Coutinho","PH",2004,6,17,"Central",3,"Destro","Direita",204,
  "Ensino Médio completo","Concluído","—","Não",0,"Atleta em formação",6,"D-E","Cedida","Alojamento do clube",
  "A pé",5,"Sim","Sim","Não","Sim",5,"Sim",13,1,"Seleção estadual Sub-21"),
 ("Caio Fernandes Bastos","Caio",2001,10,9,"Líbero",1,"Canhoto","Direita",186,
  "Superior em andamento","Cursando","Matutino","Sim",12,"Auxiliar administrativo",3,"C1","Alugada","Família",
  "Transporte público",45,"Não","Não","Sim","Sim",4,"Não",12,3,"—"),
]
LESOES_EX = [("—",0,"—"),("Entorse de tornozelo D",1,"—"),("—",0,"—"),
             ("Tendinopatia patelar",2,"Dor anterior no joelho D (leve)"),("Lombalgia",1,"—"),
             ("—",0,"—"),("Entorse de tornozelo E",1,"—"),("Tendinopatia de ombro D",1,"—"),
             ("—",0,"—"),("Cirurgia de ombro D (2021)",0,"—"),("—",0,"—"),("Entorse de dedo",1,"—")]
for i, a in enumerate(EXEMPLO):
    r = CAD_F + i
    (nome, apel, ay, am, ad, pos, cam, dom, perna, est, esc, sit, turno, trab, horas, ocup,
     pes, classe, mor, reside, transp, desloc, bolsa, benef, plano, net, refs, nutri,
     ini, forca, selec) = a
    V = {2:nome, 3:apel, 4:date(ay,am,ad), 6:"Masculino", 7:"Brasileira", 8:"—", 9:"—", 10:cam,
         11:"Adulto", 12:pos, 13:dom, 14:perna,
         18:"(00) 90000-00{:02d}".format(i+1), 19:"atleta{}@elase.com.br".format(i+1), 20:"—",
         21:"—", 22:"—", 23:"Responsável / familiar", 24:"(00) 90000-10{:02d}".format(i+1), 25:"—",
         26:esc, 27:sit, 28:turno, 29:"—", 30:trab, 31:horas, 32:ocup, 33:pes,
         34:classe, 35:mor, 36:reside, 37:transp, 38:desloc, 39:bolsa, 40:benef,
         41:plano, 42:net, 43:refs, 44:nutri, 45:ini, 47:forca,
         48:"Superliga B" if i % 3 else "Superliga A", 49:"—", 50:selec,
         51:"O+", 52:"—", 53:"—", 54:LESOES_EX[i][0] if "Cirurgia" in LESOES_EX[i][0] else "—",
         55:LESOES_EX[i][0], 56:LESOES_EX[i][1], 57:LESOES_EX[i][2],
         58:date(2026,1,12), 59:date(2027,1,12), 61:"Sim", 62:"Não" if i % 4 else "Sim",
         63:date(2026,1,5), 64:"Lesionado" if i == 3 else "Ativo", 65:"EXEMPLO — substituir"}
    for c, v in V.items():
        wsC.cell(r, c, v)
        if isinstance(v, date):
            wsC.cell(r, c).number_format = NF_DATE
NOMES = [a[0] for a in EXEMPLO]
EST_EX = {a[0]: a[9] for a in EXEMPLO}
POS_EX = {a[0]: a[5] for a in EXEMPLO}
