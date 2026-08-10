# AFC multigrupo e invariância de medida (semopy)

Testa se a estrutura fatorial do BRUMS é invariante entre **pré** e **pós-treino**.
Reproduzível: `python analise.py`. Fonte: `analises_avancadas/itens_brums.csv`.

- **Configural** — AFC (semopy) ajustada em cada grupo (mesma estrutura, parâmetros
  livres); reporta CFI/TLI/RMSEA/χ² por grupo.
- **Métrica (cargas)** — congruência de **Tucker φ** por fator e global (≥ 0,95 =
  invariante) e teste **ΔCFI** com o grupo pós usando as cargas fixadas na solução
  do pré (limiares de Cheung & Rensvold ΔCFI ≤ 0,01; Chen ΔRMSEA ≤ 0,015).

Restrito aos quatro fatores confiáveis (Depressão, Raiva, Vigor, Fadiga); Tensão e
Confusão são excluídas por variância degenerada (efeito piso), como na AFC.
Figura: `invariancia_multigrupo_fig.png`.
