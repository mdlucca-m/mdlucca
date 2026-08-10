# Os outros questionários — autorrelatos externos ao BRUMS

Além das seis subescalas do BRUMS, a coleta incluiu quatro autorrelatos: **Fadiga
física** (0–10), **Fadiga mental** (0–10), **Estado físico** (0–4) e **Estado
mental** (0–4). Este módulo os trata como uma bateria própria — resposta aguda,
contraste HIIT, convergência com o BRUMS e estabilidade. Reproduzível:
`python outros_questionarios.py` (lê `../modelagem/base_modelagem.csv`).

## A. Resposta aguda pré→pós

| Instrumento | Escala | Pré → Pós | Δ | dz | p (FDR) | Sig.? |
|---|---|---|---|---|---|---|
| Fadiga física | 0–10 | 4,95 → 6,69 | +1,74 | +1,06 | <0,001 | ✔ |
| **Estado físico** | 0–4 | 2,26 → 1,64 | −0,62 | −0,93 | <0,001 | ✔ |
| Fadiga mental | 0–10 | 4,59 → 5,12 | +0,53 | +0,44 | 0,061 | tendência |
| Estado mental | 0–4 | 2,43 → 2,27 | −0,16 | −0,39 | 0,066 | tendência |

Os instrumentos **físicos respondem forte e significativamente** à sessão — a
fadiga física sobe (dz 1,06, o marcador-sentinela) e o estado físico piora (dz
−0,93). Os **mentais apenas tendem** (fadiga mental sobe, estado mental cai, ambos
p≈0,06). Mesmo padrão do BRUMS: a resposta aguda vive no eixo físico/energético.

## B. HIIT vs sem HIIT

No contraste do Δ agudo médio por atleta, **nenhum dos quatro instrumentos difere**
entre dias de HIIT e sem HIIT (todos p(FDR) > 0,39). Coerente com o módulo de
comparação entre dias: o salto agudo é semelhante entre os tipos de dia — a
assinatura do HIIT não está no salto pré→pós.

## C. Convergência com o BRUMS (rm_corr intra-atleta)

Correlação de medidas repetidas (dentro do atleta) de cada externo com as
subescalas do BRUMS e o PTH — os quatro autorrelatos **convergem** com os
construtos do BRUMS:

| Externo | Mais forte com | r | Leitura |
|---|---|---|---|
| Fadiga física | **Fadiga** (BRUMS) | **+0,64** | mede o mesmo cansaço da subescala Fadiga |
| Estado físico | **Fadiga** (BRUMS) | **−0,65** | melhor estado físico ↔ menos fadiga; +0,47 com Vigor |
| Fadiga mental | PTH | +0,47 | acompanha o transtorno total de humor |
| Estado mental | PTH | −0,56 | melhor estado mental ↔ menor perturbação; +0,37 com Vigor |

O item único de **Fadiga física** correlaciona-se fortemente com a subescala
multi-item de **Fadiga** do BRUMS (r = 0,64), e o **Estado físico** é seu espelho
negativo (r = −0,65) e positivo com o **Vigor** (r = 0,47). Os instrumentos
**mentais** ancoram-se no **PTH** e no eixo de afeto (raiva, depressão). Ou seja:
os quatro autorrelatos externos medem, de forma econômica (um item), as mesmas
dimensões que o BRUMS mede com quatro itens — **validade convergente** dentro do
sujeito. Nenhum externo se associa à tensão/confusão (subescalas de piso).

## D. Estabilidade individual (ICC)

| Instrumento | ICC | Perfil |
|---|---|---|
| Fadiga mental | 0,70 | mais traço (estável entre dias) |
| Estado mental | 0,60 | mais traço |
| Fadiga física | 0,41 | mais estado (responde à sessão) |
| Estado físico | 0,39 | mais estado |

Os instrumentos **físicos são mais "de estado"** (ICC ≈ 0,40 — variam com a
sessão), enquanto os **mentais são mais "de traço"** (ICC 0,60–0,70 — dependem
mais de quem é o atleta). Espelha exatamente o achado do BRUMS (fadiga física a
subescala mais responsiva; afeto negativo mais estável).

## Leitura

Incluir os outros questionários **não muda as conclusões — reforça-as por outra
via de medida**: (i) a resposta aguda mora no físico/energético (fadiga física e
estado físico movem-se com dz ~1; os mentais só tendem); (ii) o salto agudo não
distingue HIIT de sem-HIIT; (iii) os autorrelatos convergem com os construtos do
BRUMS dentro do atleta (validade convergente, r 0,47–0,65), com os físicos
ancorados na Fadiga/Vigor e os mentais no PTH; e (iv) os físicos são de estado e
os mentais de traço. Os quatro instrumentos são, portanto, **medidas
complementares e convergentes**, não redundantes nem contraditórias com o BRUMS.

Figura: `outros_questionarios_fig.png` (A: resposta aguda dz; B: média pré×pós; C: convergência rm_corr com o BRUMS; D: ICC).
