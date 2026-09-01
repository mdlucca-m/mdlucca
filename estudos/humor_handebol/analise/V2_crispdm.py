# -*- coding: utf-8 -*-
"""Mapa do estudo sobre o CRISP-DM, com os números vindos da própria base.

As seis fases do CRISP-DM (Chapman et al., 2000) aplicadas ao microciclo terminal
de pré-temporada. Cada fase declara: a pergunta da fase, o que foi feito de fato
neste repositório (arquivo e tabela), o que a IA fez como copiloto e o que ficou
sob decisão humana. A separação importa: o que a IA decide sozinha não é achado.
"""
import os, json, sqlite3
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
c=lambda t:cx.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
N=dict(atleta=c('atleta'),registro=c('registro'),atleta_dia=c('atleta_dia'),pre_pos=c('pre_pos'),
       resultado=c('resultado'),aba=c('aba'),celula=c('celula'),referencia=c('referencia'),
       auditoria=c('auditoria'),significativo=cx.execute(
         "SELECT COUNT(*) FROM resultado WHERE significativo=1").fetchone()[0])
cx.close()
ML=json.load(open(os.path.join(DADOS,"V2_ml.json")))
ML3=json.load(open(os.path.join(DADOS,"V2_ml3.json")))
AUD=json.load(open(os.path.join(DADOS,"V2_audit.json")))
br=lambda x,d=3: f"{x:.{d}f}".replace('.',',').replace('-','−')
bs=lambda x,d=3: ('+' if x>=0 else '−')+f"{abs(x):.{d}f}".replace('.',',')

FASES=[
 dict(id='negocio', n=1, nome='Entendimento do problema',
  pergunta='O que a comissão técnica precisa decidir, e em que prazo?',
  feito=[f"A pergunta foi fixada em uma forma verificável: como as seis dimensões do humor se comportam ao longo dos sete dias finais de pré-temporada, e se a medida da manhã antecipa o estado da noite.",
         "O desfecho de interesse foi definido como a faixa de risco do perfil de humor, não como escore bruto, porque a comissão age sobre atletas, não sobre médias.",
         "O horizonte de decisão é de horas: a medida da manhã precisa informar a sessão do mesmo dia."],
  copiloto="Formular hipóteses concorrentes e escrever o critério de falseamento de cada uma antes de olhar os dados.",
  humano="A escolha do desfecho clinicamente relevante e do horizonte de decisão. Nenhum modelo decide o que importa para a equipe.",
  artefatos=['texto/A1T.py','texto/A2T.py']),

 dict(id='dados', n=2, nome='Entendimento dos dados',
  pergunta='O que existe de fato, e o que cada linha significa?',
  feito=[f"{N['registro']} registros de {N['atleta']} atletas ao longo de sete dias, de duas coletas diárias a partir do dia 2.",
         f"{N['aba']} abas e {N['celula']:,} células das planilhas de origem foram catalogadas em camada de acervo, com raspagem de nomes próprios na importação.".replace(',','.'),
         "Quatro unidades de análise coexistiam nas versões anteriores: registro (U-R), primeira e última (U-286), par atleta-dia (U-AD) e subamostra pareada (U-PAR).",
         f"{N['auditoria']} achados de auditoria foram registrados, dois deles críticos."],
  copiloto="Ler as sete versões do manuscrito e as seis planilhas em paralelo, reproduzir cada número divergente e localizar a regra que o gerou.",
  humano="A decisão de adotar o par atleta-dia (U-AD) como unidade canônica, e de declarar as outras três em vez de escondê-las.",
  artefatos=['analise/V2_audit.py','scripts/colher_planilhas.py','base/esquema.sql']),

 dict(id='preparacao', n=3, nome='Preparação dos dados',
  pergunta='Como transformar planilhas em uma base que responda perguntas?',
  feito=["A regra do dia fisiológico (virada às 4h) resolveu os registros de madrugada sem descartá-los.",
         "Registros órfãos foram reconciliados por dicionário de variantes do nome e, quando insuficiente, pelo carimbo de tempo curado.",
         f"A base única em SQLite tem três camadas — canônica, de resultados e de acervo — com {N['pre_pos']} pares pré-pós e {N['resultado']} resultados em formato longo.",
         "Anonimização A01–A27 dentro da rotina de importação: nenhum nome sai do script."],
  copiloto="Escrever a rotina de reconciliação, a raspagem de nomes e o esquema de três camadas; verificar que zero nomes completos sobrevivem.",
  humano="A curadoria dos registros ambíguos e a regra da virada às 4h, que é uma decisão de fisiologia, não de programação.",
  artefatos=['analise/base_v2.py','scripts/construir_base.py','atualizar.sh']),

 dict(id='modelagem', n=4, nome='Modelagem',
  pergunta='A medida da manhã antecipa o estado da noite?',
  feito=[f"{ML['n']} pares atleta-dia, {ML['atletas']} atletas, {ML['eventos']} eventos ({br(ML['eventos']/ML['n']*100,1)}%).",
         "Alvo e preditores separados no tempo: a previsão não é circular.",
         "Validação cruzada agrupada por atleta (StratifiedGroupKFold): nenhum atleta aparece ao mesmo tempo no treino e no teste.",
         "Duas linhas de base obrigatórias: a classe majoritária e a regra trivial de já estar em risco pela manhã.",
         "Quatro modelos: árvore de decisão, floresta aleatória, XGBoost e regressão logística."],
  copiloto="Montar a matriz, escrever o protocolo de validação agrupada e rodar o intervalo de confiança por reamostragem agrupada.",
  humano="A exigência de que existisse uma linha de base trivial. Sem ela, uma AUC de 0,80 pareceria descoberta quando é sobretudo persistência do estado matinal.",
  artefatos=['analise/V2_ml.py','analise/V2_ml2.py']),

 dict(id='avaliacao', n=5, nome='Avaliação',
  pergunta='O ganho é real, ou é aritmética do desenho?',
  feito=[f"O ganho de AUC sobre a regra trivial não exclui zero em nenhum modelo (melhor caso, XGBoost: {bs(ML['GANHO']['XGBoost']['m'])}, IC 95% [{bs(ML['GANHO']['XGBoost']['ic'][0])}, {bs(ML['GANHO']['XGBoost']['ic'][1])}]).",
         f"Reversão à média testada em todas as dimensões: o corte pelo PTH é parcialmente mecânico (ρ = {br(ML3['VEREDICTO']['pth']['rho'])}, p < 0,001).",
         f"O corte pela tensão não é mecânico (ρ = {br(ML3['VEREDICTO']['tensao']['rho'])}, p = {br(ML3['VEREDICTO']['tensao']['p'])}) e acrescenta {bs(ML3['VEREDICTO']['ganho_tensao'])} de AUC sobre o PTH sozinho.",
         "No subgrupo acionável — quem começa o dia fora da faixa de risco — o intervalo de confiança exclui o acaso."],
  copiloto="Propor e executar o diagnóstico de reversão à média e a sequência de modelos aninhados antes de qualquer redação.",
  humano="A recusa em relatar a folha mais forte como achado clínico antes do diagnóstico. O modelo não sabe que precisa desconfiar de si.",
  artefatos=['analise/V2_ml3.py']),

 dict(id='implantacao', n=6, nome='Implantação',
  pergunta='Como isso vira rotina da comissão técnica, e não um relatório único?',
  feito=["Um comando reconstrói tudo: base, perfis, análises, banco, acervo e figuras (atualizar.sh).",
         f"Consulta por linha de comando sobre a base única, com busca em texto completo sobre {N['celula']:,} células.".replace(',','.'),
         f"Dois artigos e {N['referencia']} referências com DOI verificado contra o registro do periódico.",
         "Painel de apresentação com as duas trilhas de artigo, a auditoria e esta trilha de modelagem."],
  copiloto="Escrever a automação, o exportador do painel e a resolução de DOI; manter tudo reprodutível a partir da fonte.",
  humano="A decisão sobre o que entra em repositório aberto: as planilhas com nomes reais não acompanham a submissão.",
  artefatos=['atualizar.sh','scripts/consultar.py','painel/painel.html']),
]

# a regra de ouro que atravessa as seis fases
REGRAS=[
 dict(t='A pergunta antes do dado', d='A hipótese e o critério de falseamento são escritos antes de olhar o resultado. O contrário produz achado por garimpo.'),
 dict(t='A unidade de análise é declarada', d='Sete versões divergiam por quatro unidades não declaradas, sem um único erro de aritmética. Declarar a unidade é metade da reprodutibilidade.'),
 dict(t='Toda comparação tem linha de base', d='Um modelo só ganha crédito contra a regra trivial que qualquer preparador aplicaria de cabeça.'),
 dict(t='Validação agrupada por indivíduo', d='Com 27 atletas e 119 observações, dividir por linha e não por atleta infla a AUC pela memorização do atleta.'),
 dict(t='O contraintuitivo é diagnosticado, não narrado', d='A folha mais forte foi submetida ao teste de reversão à média antes de virar frase.'),
 dict(t='O anonimato começa na importação', d='O nome não sai do script. A raspagem é verificada, não presumida.'),
]

saida=dict(FASES=FASES, REGRAS=REGRAS, N=N)
json.dump(saida, open(os.path.join(DADOS,"V2_crispdm.json"),'w'), ensure_ascii=False, indent=1)
for f in FASES:
    print(f"{f['n']}. {f['nome']:<28} {len(f['feito'])} itens · {len(f['artefatos'])} artefatos")
print(f"\n→ {os.path.join(DADOS,'V2_crispdm.json')}")
