# -*- coding: utf-8 -*-
"""Consolida a auditoria: linhagem, causa de cada divergência e matriz de reconciliação."""
import json, numpy as np, collections
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(DADOS, exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
S=DADOS
V1=json.load(open(os.path.join(DADOS,"U_base.json"))); V2=json.load(open(f"{S}/V2_base.json"))
Q2=json.load(open(f"{S}/V2_perfis.json"))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','TMD']

# ---- a coluna «Data» autorreferida, contada na fonte, para o achado D2 não depender de memória ----
import openpyxl, datetime, re
UP=os.environ.get("HH_UPLOADS") or "/root/.claude/uploads/4ddb0907-77b2-5876-a286-ef4b6b886e93"
_wb=openpyxl.load_workbook(os.path.join(UP,"ad245c30-Backup__Banco_de_dados_ORIGINAL_INTOCADO_20260723.xlsx"),
                           read_only=True, data_only=True)
_lin=list(_wb['Diário - Treino'].iter_rows(values_only=True))[1:]; _wb.close()
_D0, _DF = datetime.date(2024,4,21), datetime.date(2024,4,27)
def _dia4h(ts): return ts.date() if ts.hour>=4 else ts.date()-datetime.timedelta(days=1)
DATA=dict(linhas=len(_lin),
  nulas=sum(1 for r in _lin if not isinstance(r[2],datetime.datetime)),
  com_data=sum(1 for r in _lin if isinstance(r[2],datetime.datetime)))
DATA['fora_da_semana']=sum(1 for r in _lin if isinstance(r[2],datetime.datetime)
                           and not (_D0<=r[2].date()<=_DF))
DATA['inutilizaveis']=DATA['nulas']+DATA['fora_da_semana']
DATA['difere_do_carimbo']=sum(1 for r in _lin if isinstance(r[2],datetime.datetime)
                              and r[2].date()!=_dia4h(r[0]))
DATA['anteriores_a_2020']=sum(1 for r in _lin if isinstance(r[2],datetime.datetime) and r[2].year<2020)
print(f"coluna «Data»: {DATA['linhas']} linhas · {DATA['nulas']} sem data · "
      f"{DATA['fora_da_semana']} fora da semana · {DATA['inutilizaveis']} inutilizáveis · "
      f"{DATA['difere_do_carimbo']} divergem do carimbo · {DATA['anteriores_a_2020']} anteriores a 2020")
def med(Bd,v,d):
    xs=[p[v] for p in Bd['pares'] if p['dia']==d and p.get(v) is not None]
    return float(np.mean(xs))
CMP={v:{'V1':[med(V1,v,d) for d in range(1,8)], 'V2':[med(V2,v,d) for d in range(1,8)]} for v in SUB}
for v in SUB: CMP[v]['maxdif']=max(abs(a-b) for a,b in zip(CMP[v]['V1'],CMP[v]['V2']))
ACHADOS=[
 dict(id='D1', titulo='Fonte de dados trocada',
      achado='A base usada em todas as gerações anteriores descendia de COLETAS.xlsx, que carrega um '
             'desalinhamento de linhas em 28 registros de dois atletas.',
      correcao='A base V2 parte da aba «Diário - Treino» do export do formulário, designada FONTE-VERDADE '
               'pela auditoria do autor.',
      impacto='Diferença máxima nas médias diárias: 0,30 ponto (PTH em D3). Nenhuma conclusão se inverte.',
      gravidade='média'),
 dict(id='D2', titulo='Coluna de data corrompida',
      achado=(f"A coluna «Data», preenchida pelo respondente, contém datas de nascimento e erros de digitação: "
              f"{DATA['anteriores_a_2020']} registros trazem ano anterior a 2020. Por esse campo, "
              f"{DATA['inutilizaveis']} dos {DATA['linhas']} registros seriam inutilizáveis "
              f"({DATA['fora_da_semana']} caem fora da semana e {DATA['nulas']} estão em branco), e "
              f"{DATA['difere_do_carimbo']} divergem do dia obtido pelo carimbo."),
      correcao='O dia passou a ser definido pelo carimbo de data/hora, com fronteira às 04h00.',
      impacto='Seis registros lançados entre 00h e 01h de 22/04 retornaram ao dia 1, ao qual pertencem: '
              'todos são de atletas que já haviam respondido na noite de 21/04.',
      gravidade='alta'),
 dict(id='D3', titulo='Registros órfãos',
      achado='Quatro registros receberam o rótulo «Não Identificado» na coluna padronizada, o que criou um '
             'vigésimo oitavo atleta fantasma na contagem ingênua.',
      correcao='Dois foram recuperados por correspondência exata no dicionário de variantes e dois pelo nome '
               'curado em COLETAS.xlsx para o mesmo carimbo. Os quatro voltaram aos donos (A01, A01, A04, A07).',
      impacto='O elenco é de 27 atletas, não 28. Nenhum atleta-dia foi criado ou perdido.',
      gravidade='média'),
 dict(id='D4', titulo='Unidade de análise não declarada — a causa raiz',
      achado='As sete gerações de manuscrito misturam quatro unidades de análise distintas sem declará-las. '
             'A mesma classificação, sobre os mesmos dados, produz variações do perfil iceberg entre D1 e D7 '
             'que vão de −0,6 a −18,0 pontos percentuais conforme a unidade escolhida.',
      correcao='Os dois artigos novos declaram o par atleta-dia como unidade única e reportam a matriz de '
               'reconciliação como resultado.',
      impacto='Explica integralmente as divergências que bloqueavam a submissão.',
      gravidade='crítica'),
 dict(id='D5', titulo='Denominadores incompatíveis na comparação D1×D7',
      achado='Uma das gerações comparou 27 atletas em D1 contra 37 registros de apenas 21 atletas em D7.',
      correcao='A comparação passou a ser pareada, restrita aos 21 atletas com as duas medidas, e o contraste '
               'agregado passou a usar um registro por atleta-dia.',
      impacto='A variação do iceberg deixa de ser um artefato de contagem.',
      gravidade='crítica'),
 dict(id='D6', titulo='Janela de coleta do dia 7',
      achado='Em D7 todos os 46 registros ocorrem entre 08h e 14h; não existe medida noturna.',
      correcao='O contraste pré/pós de D7 passa a ser descrito como manhã contra início da tarde.',
      impacto='Não altera número algum, mas corrige a interpretação do custo do último dia.',
      gravidade='baixa'),
]
UNID=[
 dict(sigla='U-R', nome='Registro', n=456,
      regra='Todo formulário respondido conta uma vez; dia civil com fronteira à meia-noite.',
      usada_em='Dashboard da planilha e aba de impacto da auditoria',
      vies='Pondera cada atleta pelo número de respostas: quem respondeu seis vezes num dia pesa seis vezes.'),
 dict(sigla='U-286', nome='Primeiro e último', n=285,
      regra='D1 = um registro; D2 a D7 = primeiro e último do dia.',
      usada_em='Tabelas do Paper 1',
      vies='Pondera duplamente os atletas que responderam duas vezes e simplesmente os que responderam uma.'),
 dict(sigla='U-AD', nome='Par atleta-dia', n=166,
      regra='Um valor por atleta e por dia, média das respostas daquele dia.',
      usada_em='Artigos 1 e 2 (unidade adotada)',
      vies='Cada atleta pesa igual em cada dia; elimina a pseudorreplicação.'),
 dict(sigla='U-PAR', nome='Subamostra pareada', n=143,
      regra='Apenas os 21 atletas com medida em D1 e em D7.',
      usada_em='Uma das gerações intermediárias',
      vies='Sem viés de ponderação, mas perde 22% dos pares e restringe a inferência aos assíduos.'),
]
json.dump(dict(DATA=DATA, ACHADOS=ACHADOS, UNIDADES=UNID, CMP=CMP,
               REC=Q2['REC'], DECISOES=V2['DECISOES'],
               recuperados=V2['recuperados'], nd=V2['nd']),
          open(f"{S}/V2_audit.json",'w'), ensure_ascii=False)
print("gravado: V2_audit.json")
for a in ACHADOS: print(f"  [{a['id']}] {a['gravidade']:8} {a['titulo']}")
