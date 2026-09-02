# Perfis de humor no handebol de elite — microciclo terminal de pré-temporada

Pipeline reproduzível de sete documentos sobre o comportamento das dimensões do BRUMS na
última semana de pré-temporada de vinte e sete atletas de handebol de elite, entre 21 e 27 de
abril de 2024.

| Documento | Arquivo em `saida/` |
|---|---|
| Artigo 1, descritivo-analítico | `ARTIGO_1_DESCRITIVO_HUMOR_HANDEBOL.docx` |
| Artigo 2, inferencial | `ARTIGO_2_INFERENCIAL_HUMOR_HANDEBOL.docx` |
| Anexo metodológico, Estudo 3 e CRISP-DM | `ANEXO_MODELAGEM_CRISP_DM.docx` |
| Relatório de auditoria e otimização | `AUDITORIA_QUALIDADE_E_OTIMIZACAO.docx` |
| Síntese executiva, quatro a seis páginas | `SINTESE_HUMOR_HANDEBOL.docx` |
| Artigo curto, seis páginas, só os perfis | `ARTIGO_CURTO_PERFIS_HUMOR_HANDEBOL.docx` |
| Artigo descritivo e não paramétrico, oito páginas | `ARTIGO_DESCRITIVO_EXPLORATORIO_PERFIS_HUMOR_HANDEBOL.docx` |
| Relatório exploratório completo, por etapa de análise | `RELATORIO_EXPLORATORIO_COMPLETO_PERFIS_HUMOR_HANDEBOL.docx` |

## O que há aqui

```
dados/     agregados anonimizados em JSON, entrada de tudo o mais
base/      banco único em SQLite, com índice de busca em texto completo
analise/   rotinas V2_*.py: base canônica, perfis, séries, inferência, auditoria, modelos
figuras/   roteiros UV*, UM*, UQ*, UP* que geram as 21 figuras
texto/     A1T.py, A2T.py, ANX.py e REFS.py: todo o texto como estruturas Python
scripts/   construção do banco, exportações, montagem dos .docx e conferências
painel/    painel de apresentação em arquivo único
saida/     figuras e .docx gerados, fora do controle de versão
```

## Como reproduzir

```bash
./atualizar.sh        # refaz tudo, do JSON de origem aos quatro .docx
./scripts/consultar.py resumo
```

O comando encadeia oito etapas: base canônica, classificação nos perfis, análises, banco
único, acervo e índice de busca, auditoria de qualidade com reconferência independente,
modelos de árvore, e por fim exportações, painel, figuras e documentos.

Dependências: `numpy`, `scipy`, `statsmodels`, `pandas`, `scikit-learn`, `xgboost`,
`matplotlib`, `openpyxl`, `python-docx`. A variável de ambiente `HH_RAIZ` sobrepõe a raiz
inferida, caso os diretórios sejam movidos.

`montar_artigo.py`, `figuras/UE*.py` e `texto/ET.py` pertencem à primeira geração deste
estudo, anterior à auditoria de procedência, e leem os JSON `U_*.json`. Permanecem no
diretório apenas como registro histórico; **não** integram `atualizar.sh` e não devem ser
executados, porque produzem números que a base auditada já não sustenta.

## Proteção de dados

A base primária contém nomes completos associados a escores de humor e a registros de lesão e
**não** está neste repositório. A substituição por códigos `A01`–`A27` ocorre na rotina de
importação, antes de qualquer análise; apenas os agregados anonimizados em `dados/` foram
versionados. Nenhum arquivo aqui permite reidentificação.

Como consequência, a etapa de importação a partir das planilhas não é reproduzível a partir
deste diretório: o pipeline parte dos JSON derivados.

## O núcleo metodológico

Cada série diária, de médias das subescalas ou de prevalência dos perfis, passa por quatro
etapas antes de qualquer leitura:

1. **Incerteza por ponto** — erro-padrão diário, amostral para médias e binomial para
   prevalências.
2. **Piso de ruído** — média dos sete erros-padrão. Responde a "quanta oscilação a amostragem,
   sozinha, produz nesta série?".
3. **Suavização** — filtro binomial de três pontos (¼, ½, ¼), extremos preservados. O ganho é
   H(ω) = cos²(ω/2), que se anula em Nyquist, a componente que troca de sinal a cada dia.
4. **Derivadas** — primeira (velocidade) e segunda (aceleração) da série suavizada, expressas
   em unidades do piso, o que torna comparáveis variáveis de amplitudes distintas.

O veredito é explícito: declara-se variação real quando |Δ D1→D7| supera o piso; caso
contrário, atribui-se a oscilação à flutuação amostral. O teste de cruzamento entre duas
séries reconhece inversão apenas quando a diferença ultrapassa o limiar combinado antes **e**
depois do ponto de troca, e informa separadamente se a data está determinada, pela largura da
zona de indecisão, isto é, do intervalo em que a diferença permanece dentro do limiar.

O piso binomial encolhe em prevalências próximas de zero e torna o critério permissivo. O caso
do perfil Everest invertido, com dois pares no conjunto inteiro, está assinalado na figura e no
texto como não interpretável.

## Regra de composição do valor diário

A unidade canônica é o par atleta-dia, com 166 casos. O primeiro dia teve coleta única, à
noite, e vale a primeira resposta de cada atleta; as respostas tardias daquela noite são
repetição, e não segunda medida. Do segundo ao sétimo dia valem o primeiro registro do dia,
tomado como pré, e o último, tomado como pós, ainda que o primeiro caia depois do meio-dia por
esquecimento. Ao todo, 285 dos 456 registros compõem os valores diários. A regra foi auditada
contra os carimbos de data e hora em `analise/V2_proto.py`.

## Achados que o pipeline sustenta

- Vigor −4,33 e fadiga +4,28 ao longo da semana, ambos acima do respectivo piso, com tendência
  monotônica pelo teste L de Page. As sete séries superam o próprio piso, com razões que vão de
  7,1 no vigor a 1,6 na depressão.
- A deterioração concentra-se em duas transições, na saída do dia basal e na véspera da
  estreia, e deixa um platô de quatro dias entre elas.
- Iceberg 44,4% → 19,0%; barbatana de tubarão 3,7% → 23,8%; faixa de risco 14,8% → 52,4%.
- Inversão **estabelecida** entre vigor e fadiga, com abscissa em 5,13, porém com zona de
  indecisão de 3,52 dias: a inversão existe, a data não está determinada. A travessia entre
  vigor e perturbação total, em 6,01, é a única nítida do conjunto.
- A distribuição dos perfis **não** difere por tipo de estímulo (χ² = 6,384; p = 0,782), nem a
  das faixas (χ² = 3,030; p = 0,553). Nenhuma das sete variáveis contínuas difere entre os três
  tipos de estímulo na subamostra de vinte e dois atletas presentes em todos eles.
- A migração intradiária para a faixa de risco é robusta no conjunto, com vinte e três entradas
  contra dez saídas, mas a atribuição a um estímulo específico não sobrevive à correção de
  Holm.
- Em um modelo de efeitos aleatórios cruzados, a parcela de variância atribuível ao dia é a
  menor das três em todas as sete variáveis, de 0,6% na depressão a 15,6% no vigor.

## Ressalva de delineamento

Os tipos de estímulo não foram distribuídos ao acaso: HIIT em D2, D4 e D7; amistoso em D3 e
D5; técnico e de força apenas em D6. O tipo de estímulo confunde-se, portanto, com a posição no
microciclo e com a carga acumulada. Nenhuma inferência sobre especificidade de estímulo é
separável de efeito cumulativo neste desenho.
