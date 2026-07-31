# Perfil de humor, distribuições, variabilidade e robustez

Camada descritiva/exploratória e de **verificação de robustez** do estudo:
perfil de humor (iceberg), distribuições (box plot, histograma, dispersão),
decomposição da variabilidade intra vs. entre indivíduos e entre grupos,
segmentação, e três checagens de robustez — **permutação**, **transformação
logarítmica** e **exclusão do outlier**. Reproduzível: `python perfil_variabilidade.py`
(lê `../modelagem/base_modelagem.csv`).

## 1. Perfil de humor (iceberg) e qui-quadrado

O perfil clássico "iceberg" (vigor acima das subescalas negativas) está presente
em **85,9 % das avaliações pré** e cai para **74,8 % no pós** — a sessão erode o
perfil. O teste de independência confirma a associação perfil × momento:
**χ²(1) = 4,60; p = 0,032; V de Cramér = 0,13** (efeito pequeno, mas
significativo). No painel A vê-se o pico de vigor recuar e a fadiga subir do pré
para o pós — a assinatura da fadiga aguda sobre o perfil.

## 2. Variabilidade: intra vs. entre indivíduos

Decompondo a variância total de cada variável em **entre atletas** e **intra
atleta**:

| Variável | % entre atletas | Leitura |
|---|---|---|
| Depressão | 70,7 | traço — quase toda a variação é de quem é o atleta |
| Tensão | 69,2 | traço |
| PTH (TMD) | 62,1 | predominantemente individual |
| Fadiga | 57,8 | misto |
| Vigor | 57,5 | misto |
| Confusão | 41,4 | mais estado |
| Fadiga física | 40,5 | mais estado (responde à sessão) |
| Raiva | 37,0 | mais estado |

**A maior parte da variância mora entre atletas** — sobretudo nas subescalas de
afeto negativo (traço-estáveis) e no PTH. A **fadiga física** é a mais "de
estado" (só 40 % entre), coerente com ser o marcador que mais responde ao treino.
O painel B mostra isso individualmente: a dispersão dos pontos (médias por atleta)
é a variabilidade **entre**; as barras (DP intra) são a variabilidade **dentro** de
cada atleta.

## 3. Segmentação (k-means, k = 3)

Sobre o perfil-z médio das seis subescalas por atleta:

| Grupo | n | Assinatura |
|---|---|---|
| Resiliente | 20 | perfil-z baixo em todas as negativas, vigor na média |
| Perturbado | 6 | negativas elevadas, vigor um pouco acima |
| Extremo | 1 (A06) | depressão/confusão/fadiga muito altas, vigor muito baixo |

Os grupos explicam **η² = 0,70** da variância do PTH entre atletas — a tipologia
não é ruído: captura ~70 % das diferenças individuais de perturbação. Reproduz a
segmentação 20/6/1 obtida por k-means e agrupamento de Ward nas demais camadas,
com **A06** sempre como o outlier extremo (painéis C e a dispersão D da Fig. 1).

## 4. Robustez — permutação, log e outlier

Três checagens de que as conclusões não dependem de premissas:

- **Permutação (sign-flip pareado, 20 000 reamostragens):** para todas as
  variáveis testadas, o p de permutação **concorda** com o t pareado na decisão.
  Ex.: fadiga física Δ = +1,74 cai completamente fora da distribuição nula
  (p ≈ 0; painel D da Fig. 2). Distribuição-livre, confirma o paramétrico.
- **Transformação logarítmica:** aplicando log às variáveis assimétricas e
  refazendo o teste pré→pós, a **decisão de significância se mantém** em fadiga
  física, PTH, fadiga e vigor — o efeito não é artefato da assimetria/efeito piso.
- **Exclusão do outlier (A06):** removendo o atleta extremo e refazendo os testes
  agudos, as conclusões **se mantêm** (a significância e a direção não mudam; os
  tamanhos de efeito variam pouco) — os achados não são carregados por um único
  atleta.

## Leitura

Esta camada reforça, por vias descritivas e de robustez, os dois pilares do
estudo: (1) a resposta ao HIIT **erode o perfil iceberg** pela via da fadiga
(χ² significativo; queda de vigor e alta de fadiga no perfil), e (2) a resposta é
**dominada pela variabilidade entre indivíduos** — a maior parte da variância é
entre atletas, a tipologia explica 70 % da variação do PTH, e há um perfil atípico
reprodutível (A06). Tudo sobrevive à permutação, à transformação logarítmica e à
exclusão do outlier — as conclusões são **robustas** à família de teste, à forma da
distribuição e a casos influentes.

Figuras: `perfil_fig.png` (A: iceberg pré×pós; B: box plot por subescala; C: histograma do PTH com inset log; D: dispersão vigor×fadiga por grupo) e `variabilidade_fig.png` (A: componentes de variância; B: variabilidade individual do PTH; C: perfis de grupo; D: nula de permutação da fadiga física).
