# Carga interna × perfil de humor e preditores de estado de fadiga

Módulo consolidado que responde diretamente a duas perguntas do estudo:

1. **Como PSE, TRIMP e FC se relacionam com o perfil de humor e cada uma de suas escalas?**
2. **Quais variáveis são mais sensíveis e confiáveis para predizer um estado de fadiga alta vs. baixa?**

## O que foi feito, como e por quê

### (A) Acoplamento carga × humor — nível do atleta
- **Carga interna** por atleta: PSE-sessão (Foster), FC de pico e **TRIMP relativo** (peso `w = %HRR·0,64·e^{1,92·%HRR}`, somado nas 5 fases). Sessões com <3 fases válidas descartadas.
- **Humor** em duas leituras: **tônica** (média do atleta nos dias de HIIT) e **aguda** (Δ pós−pré médio do atleta), para todas as 6 subescalas BRUMS + PTH/TMD, fadiga física (FadFis) e mental (FadMen).
- Correlação de Pearson **no nível do atleta** (unidade = atleta, n=25), com **correção FDR** (Benjamini–Hochberg) sobre a família de 27 pares por leitura.
- *Por quê:* respeita a independência (atleta como unidade), evita pseudo-replicação e controla o erro tipo I ao testar muitos pares.

### (B) Preditores de estado de fadiga — sensibilidade e confiabilidade
- **Alvo:** fadiga **ALTA** (tercil superior) vs. **BAIXA** (tercil inferior) da subescala Fadiga do BRUMS — contraste limpo de estados (n alta=170, baixa=163; cortes 3 e 7).
- **PTH/TMD excluído** dos preditores: contém aritmeticamente a subescala Fadiga (circular).
- Para cada preditor concorrente: **AUC** (Mann–Whitney) com **IC95% por bootstrap agrupado por atleta**; no ponto de **Youden**, **sensibilidade** e **especificidade**.
- **Confiabilidade:** **ICC(2,1)** entre medidas repetidas (estabilidade da medida). O cruzamento *sensibilidade × confiabilidade* localiza os marcadores simultaneamente sensíveis e confiáveis.

## Principais achados

- **Carga e humor são amplamente desacoplados no nível do atleta:** nenhum par carga × humor sobrevive à correção FDR (todos q≈0,71). No acoplamento **agudo**, PSE×Tensão (r=+0,41) e PSE×Confusão (r=+0,40) são significativos só no p bruto (não após FDR) — sinal fraco de que a percepção de esforço acompanha ativação/confusão momentânea. Ou seja, a carga interna prescreve o estímulo, mas **não determina** a resposta de humor — coerente com a literatura de que medidas subjetivas carregam informação que a carga objetiva não captura.
- **Preditores de fadiga alta vs. baixa** (AUC [IC95%] · sens · spec · ICC):
  - **Fadiga física — AUC 0,90** [0,84; 0,95] · 0,85 · 0,83 · ICC 0,28 → **o marcador mais sensível**; ICC baixo é *esperado e desejável* num marcador de estado (ele oscila com a carga).
  - **Fadiga mental — 0,76** [0,56; 0,90] · 0,65 · 0,84 · ICC 0,72 → sensível **e** estável.
  - **Vigor — 0,75** [0,64; 0,85] · 0,85 · 0,56 · ICC 0,48 → sensível (eixo energético).
  - **Depressão — 0,71** [0,59; 0,80] · 0,54 · 0,85 · ICC 0,79 → sensível **e** confiável.
  - Raiva 0,67; Confusão 0,55; **Tensão 0,54** (confiável, ICC 0,83, mas **não discrimina** fadiga).

**Leitura integrada:** o estado de fadiga é melhor sinalizado pelo próprio **eixo energia–fadiga** (fadiga física/mental e vigor), com humor deprimido como marcador sensível e estável adicional; a tensão é estável mas cega para fadiga. Isso reforça — por um caminho independente (classificação/ROC) — o mesmo eixo que emergiu nos modelos mistos, na análise fatorial e na invariância.

## Reproduzir
```bash
python carga_humor.py   # → resultados_carga_humor.json + carga_humor_fig.png
```
Dependências: numpy scipy pandas matplotlib statsmodels pingouin. Dados anonimizados (A01–A27).
