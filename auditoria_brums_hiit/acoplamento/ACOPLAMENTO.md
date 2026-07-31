# Acoplamento carga interna × humor — PSE · FC · TRIMP · Fadiga mental · TMD

Os cinco marcadores relacionados no **nível do atleta** (dias de HIIT), em duas
leituras: **tônico** (médias do atleta) e **agudo** (Δ pós−pré médio). n = 25
atletas casados entre BRUMS e FC/PSE. Reproduzível: `python acoplamento.py`.

## Tônico — médias do atleta nos dias de HIIT

Correlações **carga × humor** (todas não significativas):

| | Fadiga mental | TMD (PTH) |
|---|---|---|
| PSE | r=+0,03 (p=0,87) | r=+0,20 (p=0,33) |
| FC (pico) | r=−0,30 (p=0,14) | r=−0,18 (p=0,40) |
| TRIMP | r=−0,29 (p=0,15) | r=−0,09 (p=0,66) |

## Agudo — Δ pós−pré médio do atleta

| | Δ Fadiga mental | Δ TMD |
|---|---|---|
| PSE | r=−0,04 (p=0,86) | r=−0,02 (p=0,93) |
| FC (pico) | r=+0,08 (p=0,69) | r=+0,11 (p=0,59) |
| TRIMP | r=−0,11 (p=0,62) | r=−0,32 (p=0,12) |

## Leitura

**Nenhum** par carga × humor (PSE, FC, TRIMP × fadiga mental, TMD) atinge
significância — nem no nível do dia (tônico), nem na resposta da sessão (agudo).
As únicas associações fortes na matriz são **humor × humor**: fadiga mental ↔ TMD
(r = 0,64 tônico; r = 0,51 no agudo, ambos p<0,05), o que é esperado — a fadiga
mental compõe e acompanha a perturbação total.

Ou seja, **entre atletas**, quem teve maior carga interna (por esforço percebido,
por FC de pico ou por TRIMP) não teve pior humor. Isso converge com todo o
restante do estudo: a resposta de humor ao HIIT é real e mora no eixo
energia–fadiga, mas **não é função do custo fisiológico da sessão** — é governada
por fatores individuais (traço, contexto), não pela dose de carga.

> Nota de nível de análise: este módulo é **entre atletas**. O acoplamento
> **intra-sujeito** no nível do dia (rmcorr — ver `estatistica_inferencial/` e a
> seção 5.15 do manuscrito) existe para alguns pares; as duas leituras não se
> contradizem: dentro do atleta, dias mais intensos acompanham mais fadiga; entre
> atletas, a magnitude da carga não ordena o humor. Figuras: `heatmap_acoplamento.png`.
