# Do acervo ao fluxograma: um sistema aberto para revisões sistemáticas com busca versionada, triagem em duplicata e extração conciliada

*Artigo de método / descrição de ferramenta*

**Autoria** — a preencher. **Afiliação** — Laboratório de Psicologia do
Esporte e do Exercício (LAPE), Centro de Ciências da Saúde e do Esporte
(CEFID), Universidade do Estado de Santa Catarina (UDESC).

---

## Resumo

**Objetivo.** Descrever e justificar um sistema aberto que conduz uma
revisão sistemática do primeiro registro recuperado até as figuras que o
periódico exige, mantendo todos os números num único banco de dados.

**Desenvolvimento.** O sistema (LAPE) foi escrito em Python sobre SQLite;
o núcleo de busca, triagem e extração usa apenas a biblioteca padrão. Três
decisões de projeto o organizam: a
estratégia de busca é *declarada uma vez* e traduzida automaticamente para
a sintaxe de cada base; a triagem e a extração são feitas *em duplicata
cega*, com a versão final constituindo um terceiro registro; e toda figura
publicável é *desenhada a partir do banco*, nunca digitada.

**Resultados.** Em 21 de setembro de 2026, 51 buscas executadas
automaticamente na PubMed recuperaram 2.287 registros para cinco acervos
temáticos; as estratégias das demais bases foram geradas e armazenadas,
sem execução, por ausência de chave de acesso ou de interface aberta. O
sistema detectou que nove das buscas executadas haviam sido truncadas no
limite de coleta
— a mais grave recuperou 400 registros de um total de 17.128 existentes na
base — e passou a registrar e exibir a contagem real informada pela base
ao lado do número recolhido. Foram implementadas três fichas de extração
declaradas (20, 48 e 62 campos) e quatro instrumentos de avaliação da
qualidade metodológica, incluindo a MMAT 2018 para conjuntos de desenho
misto. A suíte de testes conta 2.300 casos, nenhum com acesso à rede.

**Conclusão.** Boa parte dos erros de procedimento em revisões
sistemáticas não vem de má-fé nem de desconhecimento do método, mas de
números digitados duas vezes em momentos diferentes e de ferramentas que
silenciam quando não sabem responder. Um sistema que escreve a estratégia,
mede o próprio limite e desenha suas figuras do mesmo banco remove uma
classe inteira dessas falhas sem substituir nenhum julgamento humano.

**Palavras-chave:** revisão sistemática; PRISMA; estratégia de busca;
extração de dados; risco de viés; reprodutibilidade.

---

## 1. O problema: seis ferramentas que não se falam

Uma revisão sistemática conduzida hoje atravessa, tipicamente, seis
ambientes distintos. A estratégia de busca é montada na interface de cada
base e guardada — quando é guardada — num documento à parte. Os resultados
são exportados para um gerenciador de referências e de lá para uma
ferramenta de triagem, que na maioria dos casos é o Rayyan. A triagem
termina, e a ferramenta termina junto: a extração de dados migra para uma
planilha compartilhada. A avaliação do risco de viés vai para uma segunda
planilha, ou para um formulário à parte. O fluxograma PRISMA é desenhado à
mão num editor de imagem, copiando números de tudo o que veio antes. A
tabela de características dos estudos incluídos é digitada uma terceira
vez, para o manuscrito.

Cada transição dessas é uma cópia manual, e toda cópia manual é uma chance
de divergência. Daí vem o defeito mais conhecido da literatura de síntese
— *o fluxograma não fecha com a tabela* —, que raramente indica descuido:
indica apenas que os dois foram escritos em momentos diferentes, a partir
da memória de alguém.

Há um segundo problema, menos discutido e mais grave, porque não deixa
rastro. Ferramentas de busca costumam impor um limite de registros por
consulta. Quando a consulta excede esse limite, elas devolvem o que cabe
— e reportam quantos devolveram, não quantos existem. Uma busca completa e
uma busca truncada produzem exatamente a mesma linha na tela. O número
truncado é então copiado para a tabela de estratégias do manuscrito, onde
passa a afirmar, sobre a literatura, algo que a base nunca disse.

Este artigo descreve um sistema construído para remover essas duas classes
de falha.

## 2. O princípio: escrito, não digitado

Três decisões de projeto organizam o restante. Elas não são independentes:
as três derivam da mesma observação, de que o erro em revisões sistemáticas
entra quase sempre pela digitação repetida de um número que já existe em
algum lugar.

1. **A estratégia é declarada uma vez.** O vocabulário controlado de cada
   acervo — construto, população, descritores, termos regionais — é escrito
   em um único lugar, em português claro, e a sintaxe de cada base é
   derivada dele. Um termo novo entra numa linha e vale para todas as bases
   simultaneamente.

2. **O que exige duplicata é feito em duplicata de verdade.** Cada pessoa
   preenche a sua triagem e a sua extração sem ver a da outra, e a versão
   final é um terceiro registro, construído a partir das duas. Sem essa
   terceira entidade, "extração em duplicata" degenera em uma pessoa
   conferindo o que a outra digitou — que não é a mesma coisa e não
   satisfaz o método.

3. **Toda figura publicável é derivada do banco.** O fluxograma PRISMA e o
   semáforo de risco de viés são desenhados em SVG, no momento do clique, a
   partir dos mesmos registros que alimentam a tela. Se um número muda, o
   desenho muda junto; não há o que conferir entre eles.

## 3. A busca

### 3.1 Uma estratégia, nove sintaxes

Escrever a mesma estratégia três vezes — uma por base — é garantir que as
três divirjam: alguém acrescenta um termo na estratégia da PubMed, esquece
as outras duas, e o acervo passa a ter três tamanhos diferentes sem que
nada na tela explique por quê.

No sistema, cada acervo declara o seu vocabulário e o tradutor gera a
consulta na sintaxe de nove bases: `"termo"[Title/Abstract]` na PubMed,
`TITLE-ABS-KEY("termo")` na Scopus, `TS=(...)` na Web of Science,
`'termo':ti,ab,kw` na Embase, `TI "termo" OR AB "termo"` nas bases EBSCO
(PsycINFO, CINAHL, SPORTDiscus), `"termo":ti,ab,kw` na Cochrane e
`ti:("termo") OR ab:("termo")` na BVS/LILACS.

A busca é sempre restrita a título, resumo e palavras-chave, nunca "todos
os campos". A razão é medida, não estética: em "todos os campos" a PubMed
traduz a sigla `POMS` para o nome de um periódico de gestão de operações, e
a Scopus localiza o termo na lista de referências de artigos que não são do
assunto. O recorte estreito é o que faz a busca incidir sobre o texto, e
não sobre o que há em volta dele.

Uma consequência prática do vocabulário declarado é que termos inúteis em
uma base e essenciais em outra podem coexistir sem custo. Em um dos acervos
descritos adiante, `"balonmano"`, `"handebol"` e o nome por extenso de um
instrumento na grafia britânica retornam zero registros na PubMed — a base
os descarta silenciosamente, informando-o apenas num campo de aviso que
nenhuma interface exibe. Eles permanecem declarados porque não são para a
PubMed: são para a Scopus, a Web of Science, a SPORTDiscus e a BVS, que
indexam resumo no idioma de origem e catalogam o instrumento pelo nome
completo. Custam nada onde não servem.

### 3.2 As bases que o sistema não alcança

Três bases respondem a consultas por interface programática: PubMed,
Scopus e Web of Science. As outras seis — Embase, PsycINFO, CINAHL,
Cochrane CENTRAL, LILACS/BVS e SPORTDiscus — não têm interface aberta, ou
têm mas a instituição não assina o acesso programático.

A estratégia dessas seis é montada e **guardada do mesmo modo**, ainda que
o sistema não possa executá-la. Isso não é redundância: uma revisão
sistemática precisa publicar a estratégia de cada base, com a data e o
número de registros. Montada à mão no momento da busca, ela sai diferente
em cada base e ninguém consegue refazê-la um ano depois — que é exatamente
o que o parecerista pede para conferir. A tela apresenta a estratégia
pronta para copiar, indica o que fazer com ela em cada base, e recebe de
volta o arquivo que a base exportar.

Registrar o que o sistema *não* faz também tem função. Uma busca da Embase
que retornasse lista vazia seria indistinguível de "a Embase não tem nada
sobre este assunto" — e alguém escreveria isso numa revisão. O sistema
recusa a busca explicitamente, com instrução, em vez de devolver zero.

### 3.3 O teto: quando 400 não é 400

Ao executar pela primeira vez as estratégias de cinco acervos, a coleta
recuperou 2.287 registros em 51 buscas na PubMed. O acervo de fibromialgia
recolheu 400 registros, e a tela informou "400 achados". A base tem
17.128.

O limite de coleta não é o defeito, e permanece onde estava: ninguém
deseja dezessete mil resumos num acervo de leitura. O defeito era o corte
**silencioso** — uma busca truncada gravava exatamente o mesmo campo que
uma busca concluída.

A correção implementada é a seguinte. Quando uma busca retorna exatamente o
número de registros solicitado — o sinal de que a base tinha mais a
oferecer —, o sistema faz uma segunda consulta, de contagem apenas, e grava
o total informado pela base ao lado do número recolhido. Quando o retorno é
menor que o limite, nenhuma consulta adicional é feita: o que veio já é a
contagem da base, e perguntar de novo custaria uma chamada por busca e
abriria a possibilidade de os dois números divergirem.

Um detalhe de implementação teve consequência desproporcional. O teto é
medido pelos **identificadores** retornados pela consulta, e não pelos
registros efetivamente lidos. A recuperação dos registros completos
ocasionalmente devolve um a menos do que os identificadores solicitados: no
acervo de fibromialgia, uma busca solicitou 400 e leu 396. Medindo pelo
final da fila, essa busca teria passado por completa — e era justamente a
que mais precisava do aviso, pois a base contém 980 registros.

O resultado da auditoria:

| Acervo / segmento | Recolhidos | Na base |
|---|---|---|
| Fibromialgia — busca geral | 400 | 17.128 |
| Fibromialgia — dor e sintomas | 400 | 11.187 |
| Fibromialgia — saúde mental e humor | 400 | 5.809 |
| Fibromialgia — diagnóstico e critérios | 400 | 5.528 |
| Fibromialgia — sono e fadiga | 400 | 4.817 |
| Fibromialgia — exercício e atividade física | 400 | 1.720 |
| Fibromialgia — trabalho e incapacidade | 399 | 1.350 |
| Fibromialgia — tratamento e medicamento | 396 | 980 |
| Humor no esporte — busca geral | 400 | 431 |

O último caso ilustra por que o corte silencioso é perigoso mesmo quando é
pequeno: 400 de 431 parece, e passaria por, um acervo completo.

O número passa a aparecer em três lugares: no terminal, ao fim da
atualização; no painel de progresso; e — porque esse painel desaparece
quando a atualização termina — no cabeçalho do acervo, ao lado do total de
artigos que ele contradiz. No registro de ingestão, um acervo truncado é
gravado como *parcial*: quem consulta o registro para decidir se pode
publicar o número precisa que "ok" signifique que a busca terminou.

## 4. A triagem

### 4.1 Às cegas, e sem voto de maioria

Cada avaliador tem a própria fila, e a referência sai dela assim que ele
decide — mesmo que a revisão ainda aguarde a decisão do outro. É isso que
"às cegas" significa operacionalmente: cada um avança no próprio ritmo, sem
ver o resto.

Quando as opiniões divergem, a referência **não é resolvida por maioria**:
ela fica em conflito, e um terceiro arbitra. A justificativa é assimétrica
e deliberada — incluir por engano custa uma leitura de texto completo;
excluir por engano custa um estudo. Os dois erros não têm o mesmo preço, e
uma média entre eles não é resposta. A arbitragem não apaga voto algum: a
divergência permanece registrada, que é o que torna possível calcular a
concordância depois.

O voto `talvez`, quando unânime, promove a referência à leitura de texto
completo. Na dúvida, lê-se.

Avançar de etapa é um passo explícito, e não automático a cada decisão: a
equipe encerra a triagem, confere o número e só então abre a fase seguinte.
Automatizar isso embaralharia as duas fases no meio do trabalho.

Equipe de um único avaliador é caso legítimo — a revisão de escopo de quem
trabalha sozinho — e o sistema a aceita explicitamente, sem simular um
segundo avaliador.

### 4.2 Duplicatas: duas chaves, e não uma

A mesma referência chega por três bases com três grafias. O sistema
identifica duplicatas por **duas** chaves simultâneas: o DOI normalizado,
quando existe, e o título normalizado acrescido do ano.

As duas valem ao mesmo tempo, e essa é a parte que se erra com frequência.
Se a chave fosse única, com preferência pelo DOI, o mesmo estudo vindo da
Scopus (com DOI) e de uma exportação sem DOI passaria por dois trabalhos
distintos — e a equipe leria o mesmo resumo duas vezes, com o fluxograma
afirmando que são dois. O ano entra na chave de título deliberadamente: o
resumo de congresso e o artigo completo saem com o mesmo título em anos
diferentes, e uni-los ocultaria um dos dois.

A duplicata não é apagada do banco. Ela permanece contabilizada, porque o
PRISMA pede o número de registros removidos por duplicação — e a interface
mostra **por que** dois registros casaram, permitindo desfazer a união,
porque o procedimento erra.

### 4.3 Concordância

O sistema calcula o **kappa de Cohen** entre cada par de avaliadores, com a
leitura qualitativa na escala de Landis e Koch. A concordância bruta
engana: se dois avaliadores excluem 95% de tudo, eles concordam em 95% por
acaso. O kappa desconta o acaso, e é o número que o periódico solicita.

## 5. A extração

### 5.1 Em duplicata de verdade

O desenho repete o da triagem, e pela mesma razão. Cada pessoa preenche a
sua ficha; a versão final é uma terceira entidade, construída a partir das
duas. A alternativa comum — uma pessoa extrai, a outra confere — é
conferência de digitação, e não extração independente.

### 5.2 Três fichas escritas

Uma ficha montada no momento da necessidade sai diferente de uma revisão
para a outra, e o campo que falta só se manifesta quando alguém tenta
preenchê-lo — frequentemente com metade dos estudos já extraídos, quando a
única saída é reler todos. Por isso as fichas ficam escritas no código, e a
revisão escolhe entre elas:

| Ficha | Campos | Destinação |
|---|---|---|
| Padrão | 20 | Revisão de intervenção: população, intervenção, comparador, desfecho |
| Completa | 48 | O que o PRISMA 2020, o manual Cochrane e o JBI pedem que se extraia de cada estudo |
| Completa + temática | 62 | A completa, acrescida dos campos específicos da pergunta da revisão |

A ficha temática **acrescenta** à completa e nunca a substitui. Uma ficha
específica que trocasse a genérica perderia financiamento e tamanho de
efeito para ganhar os construtos do tema — e a revisão deixaria de
responder ao PRISMA para responder à teoria.

Nenhum campo da ficha completa está presente por conveniência. Cada um
responde a uma norma ou a uma falha recorrente:

| Campo | Justificativa |
|---|---|
| Financiamento, conflito de interesses, aprovação ética, registro | Exigidos por periódico, e irrecuperáveis depois que a leitura passou |
| Idioma e país da coleta | Sustentam qualquer afirmação sobre a procedência da evidência |
| N recrutado **e** N analisado | Raramente coincidem, e é o segundo que vale |
| Fidedignidade **na amostra** | O coeficiente medido neste estudo, não o do artigo de validação. Separa achado de ruído, e é o campo que mais falta nas revisões de psicologia do esporte |
| Tamanhos de efeito com intervalo de confiança | Valor de *p* isolado não informa magnitude |
| Resultados **não** significativos | Item 10 do PRISMA 2020. Sem campo próprio, a extração copia o resumo — e o resumo relata o que deu certo |
| Outros relatos do mesmo estudo | Dois artigos da mesma coleta são **um** estudo. Sem o campo, a mesma amostra entra duas vezes na síntese |
| Texto completo obtido? | Extração feita apenas pelo resumo não é válida, e precisa ser visível |

Trocar de ficha no meio da revisão não apaga nada: os campos são
identificados por código, e o que já foi extraído permanece vinculado ao
campo de origem. Uma revisão iniciada na ficha padrão e migrada para a
completa ganha o que faltava sem custar releitura.

Enquanto nenhum estudo alcançou a etapa de inclusão, a aba de extração
apresenta a **ficha em branco**, grupo a grupo, com o vocabulário fechado
de cada campo e os domínios do instrumento de qualidade. É o momento
correto de conferi-la e pilotá-la, conforme recomenda o manual Cochrane, e
é quando alterá-la ainda é barato.

### 5.3 Conciliação, e a origem de cada célula

O valor que vale para cada campo tem uma das três origens abaixo, e a
origem acompanha o valor:

| Origem | Situação |
|---|---|
| Acordado | Alguém conciliou as duas extrações e gravou a final |
| Unânime | As duas pessoas escreveram a mesma coisa — e isso **já é** consenso |
| Provisório | Só uma pessoa extraiu, ou as duas divergem e ninguém conciliou |

Exigir confirmação explícita daquilo que ninguém contesta é trabalho
inútil, e trabalho inútil é pulado. A origem viaja junto com o valor porque
a tabela precisa distinguir os casos: célula vazia parece "não se aplica",
quando pode significar "ainda não conferimos".

## 6. Qualidade metodológica: o problema dos desenhos mistos

Os instrumentos são padrão publicado e residem no código, não no banco —
não cabe a cada revisão inventar os seus. O que vai para o banco é a
*cópia* que aquela revisão utiliza, de modo que uma revisão antiga não mude
de instrumento quando o código for atualizado.

| Instrumento | Aplicação |
|---|---|
| RoB 2 (Cochrane) | Ensaios randomizados |
| ROBINS-I | Estudos não randomizados de intervenção |
| JBI — transversais analíticos | Conjuntos exclusivamente transversais |
| MMAT 2018 | Conjuntos de **desenho misto** |

A inclusão da MMAT responde a uma limitação estrutural do modelo de dados,
e vale explicitá-la: o instrumento é **um por revisão**, e há revisões cujos
estudos não compartilham o mesmo desenho. Avaliar um estudo transversal
pela RoB 2 é cobrar randomização de quem não randomizou; avaliar um ensaio
pelo checklist JBI de transversais é deixá-lo sem julgamento.

A MMAT resolve isso por construção: duas questões de triagem aplicáveis a
qualquer estudo, e cinco critérios por categoria de desenho. Cada estudo
responde às duas primeiras e aos cinco da sua categoria; os das demais
recebem *não se aplica*, que é resposta e não lacuna — distinção que
importa, porque lacuna, no semáforo, é um círculo cinza indistinguível de
"ainda não julgado".

A MMAT é o único instrumento implementado sem domínio de julgamento global,
e isso é deliberado: a própria MMAT desaconselha por escrito o cálculo de
um escore único, porque a média oculta **qual** critério falhou — e é o
critério, não a média, que altera a leitura do estudo.

## 7. As saídas

| Arquivo | Conteúdo |
|---|---|
| `prisma.svg` | Fluxograma PRISMA 2020, desenhado a partir dos números do banco |
| `semaforo.svg` | Semáforo de risco de viés: estudos × domínios |
| `caracteristicas.csv` | Tabela de características dos estudos incluídos |
| `exportar` | Referências em RIS, BibTeX ou CSV, por recorte |

O formato vetorial é escolha deliberada: entra no Word e no LaTeX sem
serrilhar e permanece sendo texto, de modo que uma palavra pode ser
corrigida sem redesenhar a figura.

Os recortes de exportação são os incluídos, os que alcançaram texto
completo, os excluídos, os pendentes, os duplicados e o conjunto total —
cada um acompanhado dos votos de quem triou, que é o anexo solicitado na
avaliação por pares.

## 8. Um caso em curso: autodeterminação no handebol

O sistema foi exercitado sobre uma pergunta real: o que a teoria da
autodeterminação já descreveu a respeito de quem joga handebol.

A estratégia declarada isola o construto teórico — necessidades
psicológicas básicas, regulações do continuum, suporte à autonomia, estilo
controlador, e os instrumentos que os medem — de uma estratégia mais ampla
de motivação no handebol. A separação foi medida antes de ser adotada: a
motivação em geral recupera 63 registros na PubMed e a autodeterminação, 27.
Os 36 de diferença são clima motivacional, metas de realização e coesão —
literatura legítima, de outra teoria, e precisamente o que este recorte
pretende deixar de fora. Se a palavra "motivation" integrasse o vocabulário,
o recorte devolveria quase o acervo inteiro sob outro nome.

Os 27 registros foram transferidos do acervo para a revisão sem passar por
arquivo intermediário, preservando a base de origem de cada um — que é o
que o PRISMA solicita por número. A ficha preparada tem 62 campos, dos
quais 10 obrigatórios, e o instrumento de qualidade é a MMAT.

A escolha da MMAT decorreu da composição observada do conjunto, e não de
preferência. A classificação automática, feita a partir dos tipos de
publicação e dos descritores da base, identificou um ensaio randomizado,
uma coorte prospectiva, três validações de instrumento e uma revisão
narrativa; os 21 restantes não receberam classificação e, pelos títulos e
resumos, distribuem-se entre transversais correlacionais e estudos
qualitativos — o que a triagem confirmará estudo a estudo. Nenhum
instrumento de desenho único cobriria esse conjunto.

**Nenhuma decisão de inclusão foi registrada.** Os 27 permanecem na etapa
de título e resumo. A triagem é trabalho de dois avaliadores independentes,
e uma decisão registrada sem que eles a tenham tomado reapareceria adiante
como kappa, como fluxograma e como número publicado. O caso, portanto, está
em fase de protocolo, e é assim que deve ser lido: ele demonstra o
funcionamento do sistema, não resultados sobre a autodeterminação no
handebol.

## 9. Limitações

**O truncamento continua existindo.** Ele deixou de ser silencioso, o que é
uma diferença relevante, mas não se converteu em coleta completa. Um acervo
de 17 mil registros continua sendo recuperado parcialmente — e agora a
interface afirma isso, o que transfere a decisão para a equipe em vez de
ocultá-la.

**Um instrumento por revisão.** A MMAT contorna o problema dos desenhos
mistos, mas não o resolve no modelo de dados: o sistema ainda não permite
associar instrumentos diferentes a estudos diferentes dentro da mesma
revisão. Uma revisão que prefira aplicar RoB 2 aos ensaios e JBI aos
transversais não é contemplada.

**Cobertura automática restrita.** Apenas três bases respondem
programaticamente, e duas delas exigem chave de acesso institucional. No
exercício descrito, apenas a PubMed executou automaticamente; as demais
tiveram a estratégia gerada e armazenada para execução manual. Uma revisão
conduzida somente com o que o sistema alcança sozinho não é uma revisão
completa, e o sistema não deve sugerir que seja.

**Não há síntese quantitativa.** O sistema não realiza meta-análise nem
implementa avaliação da certeza da evidência (GRADE). Os campos de tamanho
de efeito foram desenhados para que uma meta-análise futura possa ser feita
em outro ambiente a partir do que foi extraído, mas a síntese em si está
fora do escopo.

**O sistema não julga.** Inclusão, exclusão, avaliação de qualidade e
interpretação permanecem integralmente humanas. O que ele faz é impedir
que um número seja digitado duas vezes, e tornar visível o que
habitualmente é silencioso.

**Escala.** O banco é SQLite, adequado a um laboratório, não a uma
plataforma multi-institucional com dezenas de revisões concorrentes.

## 10. Disponibilidade

Código, esquema do banco, estratégias declaradas e suíte de testes estão no
repositório do projeto. A suíte conta 2.300 casos e não acessa a rede, de
modo que pode ser executada em qualquer máquina:

```bash
python3 -m unittest discover -s tests
```

As estratégias de busca, com a data de execução e o número de registros de
cada base, são exportáveis diretamente do sistema no formato que a seção de
métodos exige.

---

### Nota para a equipe antes de submeter

- Definir autoria e ordem, e preencher o bloco de afiliação.
- Conferir todas as referências contra os originais — volume, número,
  páginas e ano — antes do envio.
- Ajustar resumo, palavras-chave e extensão às normas do periódico-alvo;
  muitos periódicos de método exigem resumo estruturado com rótulos
  distintos dos usados aqui.
- Declarar, conforme a política do periódico, as ferramentas de apoio
  utilizadas na condução e na redação.
- Verificar se o periódico exige depósito do código com DOI (Zenodo ou
  equivalente) e, em caso afirmativo, criar a versão citável antes da
  submissão.

---

## Referências

Aromataris E, Munn Z, editores. *JBI Manual for Evidence Synthesis*.
Adelaide: JBI; 2020.

Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, Welch VA,
editores. *Cochrane Handbook for Systematic Reviews of Interventions*.
Versão corrente. Londres: Cochrane.

Hoffmann TC, Glasziou PP, Boutron I, Milne R, Perera R, Moher D, et al.
Better reporting of interventions: template for intervention description
and replication (TIDieR) checklist and guide. *BMJ*. 2014;348:g1687.

Hong QN, Fàbregues S, Bartlett G, Boardman F, Cargo M, Dagenais P, et al.
The Mixed Methods Appraisal Tool (MMAT) version 2018 for information
professionals and researchers. *Education for Information*.
2018;34(4):285-291.

Landis JR, Koch GG. The measurement of observer agreement for categorical
data. *Biometrics*. 1977;33(1):159-174.

Ouzzani M, Hammady H, Fedorowicz Z, Elmagarmid A. Rayyan — a web and mobile
app for systematic reviews. *Systematic Reviews*. 2016;5:210.

Page MJ, McKenzie JE, Bossuyt PM, Boutron I, Hoffmann TC, Mulrow CD, et al.
The PRISMA 2020 statement: an updated guideline for reporting systematic
reviews. *BMJ*. 2021;372:n71.

Ryan RM, Deci EL. *Self-Determination Theory: Basic Psychological Needs in
Motivation, Development, and Wellness*. Nova York: Guilford Press; 2017.

Sterne JA, Hernán MA, Reeves BC, Savović J, Berkman ND, Viswanathan M, et
al. ROBINS-I: a tool for assessing risk of bias in non-randomised studies
of interventions. *BMJ*. 2016;355:i4919.

Sterne JAC, Savović J, Page MJ, Elbers RG, Blencowe NS, Boutron I, et al.
RoB 2: a revised tool for assessing risk of bias in randomised trials.
*BMJ*. 2019;366:l4898.
