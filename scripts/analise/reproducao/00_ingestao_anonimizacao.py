# -*- coding: utf-8 -*-
# =============================================================================
# 00 — INGESTÃO E ANONIMIZAÇÃO DOS DADOS BRUTOS  (prova de originalidade)
# -----------------------------------------------------------------------------
# O QUE ESTE SCRIPT FAZ
#   Lê o export ORIGINAL e INTOCADO do formulário eletrônico (Google Forms)
#   com as respostas diárias dos atletas e produz o banco ANONIMIZADO
#   (A01–A27) usado em todas as análises do artigo.
#
# POR QUE ELE É A PROVA DE ORIGINALIDADE
#   - A data/hora de cada resposta vem do CARIMBO AUTOMÁTICO do formulário
#     ("Carimbo de data/hora"), que o respondente NÃO consegue editar. É por
#     ele — e não pela data digitada, sujeita a erro — que cada observação é
#     alocada ao dia e ao momento de coleta. Isso torna a janela de coleta
#     (21–27/04/2024) verificável e imune a manipulação.
#   - As pontuações das escalas são recalculadas item a item a partir das
#     respostas cruas ("2= Moderadamente" -> 2), de forma auditável.
#   - Qualquer pessoa com o arquivo original roda este script e obtém,
#     byte a byte, os mesmos escores usados no artigo.
#
# PRIVACIDADE
#   O arquivo original contém NOMES REAIS (inclusive de menores). Este script
#   os substitui pelos códigos A01–A27 usando uma CHAVE PRIVADA (key.csv) que
#   deve permanecer somente com o pesquisador. O banco de saída (humor_anon.csv)
#   NÃO contém nomes e é o único que deve ser compartilhado.
#
# ENTRADAS (fornecidas localmente pelo pesquisador; NÃO versionar):
#   - COLETAS_original.xlsx  (aba 'Diario'): export bruto do formulário
#   - key.csv                : CHAVE PRIVADA que mapeia nome -> código A01..A27
#                              (colunas: code, name). Mantenha-a fora de
#                              qualquer repositório ou anexo compartilhado.
#
# SAÍDA:
#   - humor_anon.csv : banco anonimizado, uma linha por resposta válida
#
# DEPENDÊNCIAS:  pandas, numpy, openpyxl  (pip install pandas numpy openpyxl)
# USO:           python 00_ingestao_anonimizacao.py
# =============================================================================
import pandas as pd, numpy as np, re, unicodedata

# --- Caminhos (ajuste conforme sua máquina) ---------------------------------
ARQ_BRUTO   = 'COLETAS_original.xlsx'      # export original do formulário
ABA         = 'Diario'                      # aba com o diário diário
ARQ_KEY     = 'key.csv'                     # nome -> A01..A27 (CHAVE PRIVADA)
SAIDA       = 'humor_anon.csv'

# --- Funções utilitárias -----------------------------------------------------
def normaliza(s):
    """Padroniza um nome para comparação: minúsculas, sem acento, sem espaços duplos."""
    s = str(s).strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s)

def digito(x):
    """Extrai o número inicial de rótulos tipo '2= Moderadamente' -> 2. Vazio -> NaN."""
    m = re.match(r'\s*(\d)', str(x))
    return int(m.group(1)) if m else np.nan

# =============================================================================
# 1) CARREGA O DIÁRIO BRUTO
# =============================================================================
d = pd.read_excel(ARQ_BRUTO, sheet_name=ABA)

# Carimbo automático do formulário = fonte da verdade para data/hora
carimbo = pd.to_datetime(d['Carimbo de data/hora'], errors='coerce')

# =============================================================================
# 2) MAPA DE ANONIMIZAÇÃO  (nome -> A01..A27)
#    Os nomes foram digitados com grafias inconsistentes (apelidos, abreviações,
#    ausência de nome do meio). Em vez de exigir grafia exata, casamos cada nome
#    ao código pela MAIOR SOBREPOSIÇÃO DE TOKENS (índice de Jaccard) com os nomes
#    da chave privada key.csv. Isso resolve, de forma determinística, as
#    variações de grafia sem depender de um dicionário externo.
# =============================================================================
key = pd.read_csv(ARQ_KEY)                       # colunas: code, name  (CHAVE PRIVADA)
key.columns = ['code', 'name'][:key.shape[1]]
key = key[key['code'].astype(str).str.match(r'^A\d+$')]

def tokens(nome):
    """Conjunto de palavras do nome, sem acento/pontuação (ex.: 'Fulano B. Sobrenome' -> {fulano,b,sobrenome})."""
    return set(re.sub(r'[^a-z ]', '', normaliza(nome)).split())

KEY_TOKENS = [(c, tokens(n)) for c, n in zip(key['code'], key['name'])]

def para_codigo(nome, limiar=0.34):
    """Retorna o código A01..A27 cujo nome tem maior Jaccard com 'nome' (>= limiar)."""
    T = tokens(nome)
    if not T:
        return None
    melhor_c, melhor_s = None, 0.0
    for c, kt in KEY_TOKENS:
        if not (T & kt):
            continue
        s = len(T & kt) / len(T | kt)            # Jaccard = interseção / união
        if s > melhor_s:
            melhor_s, melhor_c = s, c
    return melhor_c if melhor_s >= limiar else None

d['ID'] = d['Nome'].map(para_codigo)

# =============================================================================
# 3) PONTUAÇÃO DAS ESCALAS (item a item, auditável)
# =============================================================================
def col_item(rotulo):
    """Localiza a coluna cujo nome termina em '[rotulo]' (itens entre colchetes)."""
    for c in d.columns:
        if isinstance(c, str) and '[' in c:
            nome = re.search(r'\[(.*)\]', c).group(1).strip().lower()
            if nome == rotulo.strip().lower():
                return c
    return None

# --- 3a) BRUMS-24: 6 subescalas (0–16 cada), 4 itens por subescala -----------
BRUMS = {
 'Tensao':    ['Apavorado', 'Ansioso', 'Preocupado', 'Tenso'],
 'Depressao': ['Deprimido', 'Desanimado', 'Triste', 'Infeliz'],
 'Raiva':     ['Irritado', 'Zangado', 'Com Raiva', 'Mal-humorado'],
 'Vigor':     ['Animado', 'Com disposição', 'Com Energia', 'Alerta'],
 'Fadiga':    ['Esgotado', 'Exausto', 'Sonolento', 'Cansado'],
 'Confusao':  ['Confuso', 'Inseguro', 'Desorientado', 'Indeciso'],
}
for sub, itens in BRUMS.items():
    cols = [col_item(i) for i in itens]
    d[sub] = d[cols].apply(lambda s: s.map(digito)).sum(axis=1)

# Perturbação Total do Humor (PTH/TMD) = soma das negativas - vigor
d['TMD'] = d['Tensao'] + d['Depressao'] + d['Raiva'] + d['Fadiga'] + d['Confusao'] - d['Vigor']

# --- 3b) Fadiga física e mental (itens únicos 0–10) --------------------------
d['FadFisica'] = pd.to_numeric(d['Qual seu nível de FADIGA FÍSICA no momento?'], errors='coerce')
d['FadMental'] = pd.to_numeric(d['Qual seu nível de FADIGA MENTAL no momento?'], errors='coerce')

# --- 3c) Sonolência (Epworth, versão de 6 itens, 0–18) -----------------------
#   As 6 situações são as 6 colunas que começam por 'Situação Probabilidade de cochilar'.
ep_cols = [c for c in d.columns if isinstance(c, str) and c.startswith('Situação Probabilidade de cochilar')]
d['Epworth'] = d[ep_cols].apply(lambda s: s.map(digito)).sum(axis=1, min_count=len(ep_cols))

# --- 3d) Estresse percebido (PSS-14, 0–56) -----------------------------------
#   14 itens; os itens 4,5,6,7,9,10,13 são POSITIVOS (redação favorável) e
#   têm pontuação INVERTIDA (4 - valor). Aqui identificamos os 14 itens pela
#   ordem em que aparecem no formulário (logo após o bloco Epworth).
pss_cols = [c for c in d.columns if isinstance(c, str) and c.strip().startswith('[Você tem')]
pss_cols = pss_cols[:14]
REVERSOS = {4, 5, 6, 7, 9, 10, 13}               # posições (1..14) de pontuação invertida
pss_num = d[pss_cols].apply(lambda s: s.map(digito))
for i, c in enumerate(pss_cols, start=1):
    if i in REVERSOS:
        pss_num[c] = 4 - pss_num[c]
d['PSS'] = pss_num.sum(axis=1, min_count=14)

# =============================================================================
# 4) DATAÇÃO E MOMENTO PELO CARIMBO AUTOMÁTICO
#    Dia 1 = 21/04 (linha de base). Dias 2..7 = 22..27/04 (dias de treino).
#    Registro isolado fora da janela (ex.: 29/04) é descartado.
# =============================================================================
dia0 = pd.Timestamp('2024-04-21')
d['data'] = carimbo.dt.normalize()
d['dia']  = (d['data'] - dia0).dt.days + 1
d['hora'] = carimbo

janela = (d['dia'] >= 1) & (d['dia'] <= 7)       # 21 a 27/04
b = d[janela].copy().sort_values(['dia', 'ID', 'hora']).reset_index(drop=True)

# 'seq' = ordem da resposta dentro do mesmo atleta-dia (0 = primeira do dia)
b['seq'] = b.groupby(['dia', 'ID']).cumcount()

# 'momento': primeira resposta do dia = 'pre'; última = 'pos'; intermediárias = 'mid'.
b['nrec'] = b.groupby(['dia', 'ID'])['hora'].transform('count')
b['momento'] = 'mid'
b.loc[b['seq'] == 0, 'momento'] = 'pre'
b.loc[(b['seq'] == b['nrec'] - 1) & (b['nrec'] > 1), 'momento'] = 'pos'

# =============================================================================
# 5) EXPORTA O BANCO ANONIMIZADO COMPLETO (todas as respostas válidas)
#    Este arquivo é a base "bruta anonimizada": preserva TODOS os registros.
#    A redução para o desenho analítico (baseline único + pré/pós) é feita no
#    script 01, de forma transparente e reversível.
# =============================================================================
COLS = ['ID', 'data', 'dia', 'seq', 'momento',
        'Tensao', 'Depressao', 'Raiva', 'Vigor', 'Fadiga', 'Confusao', 'TMD',
        'FadFisica', 'FadMental', 'Epworth', 'PSS']
b[COLS].to_csv(SAIDA, index=False)

# --- Relatório de auditoria da ingestão -------------------------------------
print('=' * 60)
print('INGESTÃO CONCLUÍDA')
print('=' * 60)
print('Registros na janela 21–27/04:', len(b))
print('Atletas anonimizados (IDs):  ', b['ID'].nunique())
print('Registros por dia (carimbo):')
print(b.groupby('dia').size().to_string())
nao_map = b['ID'].isna().sum()
if nao_map:
    print(f'[atenção] {nao_map} registros sem nome mapeado — verifique o dicionário.')
print(f'\n[salvo] {SAIDA}')
