# Power BI — BRUMS × HIIT

Pacote pronto para montar o dashboard analítico do estudo no **Power BI Desktop**,
mais os renders em **4K** e **3D**. Todos os números vêm da base canônica e das
análises reproduzíveis — nada é inventado.

## O que tem nesta pasta

| Arquivo | O que é |
|---|---|
| `BRUMS_HIIT_PowerBI.xlsx` | **Dados prontos** — 14 abas: `fato_humor` (456×17), dimensões (`dim_dia`, `dim_momento`), `kpis` e as tabelas analíticas (`resposta_aguda`, `roc_prepos`, `variabilidade`, `derivadas_variavel`, `derivadas_atleta`, `dias_contraste`, `trajetoria_diaria`, `confiabilidade`, `perfil_radar`, `bolhas_4d`). |
| `medidas_DAX.txt` | **Medidas DAX** (KPIs e agregados) para colar no Power BI. |
| `BRUMS_HIIT.pbip` + `BRUMS_HIIT.SemanticModel/` + `BRUMS_HIIT.Report/` | **Projeto PBIP** (formato aberto em texto): modelo semântico TMDL (tabelas, tipos, relações, parâmetro de pasta e algumas medidas) e um relatório com uma página em branco. **Scaffold gerado por código — abra e valide no Power BI Desktop.** |
| `Dashboard_4K.png` | **Dashboard executivo em 4K** (3840×2160): KPIs + resposta aguda + monitoramento diário + radar + variância + ROC. |
| `Graficos_3D_4K.png` | **Analíticos em 3D** (4K): barras 3D da resposta aguda, dispersão 3D do mapa 4D (com cor) e superfície 3D da trajetória semanal. |
| `BRUMS_HIIT_4K_3D.pdf` | Os dois painéis 4K num PDF. |
| `build_*.py` | Geradores reproduzíveis (dados, PBIP, renders 4K/3D). |

---

## Caminho A — abrir o projeto PBIP (rápido)

1. Instale/atualize o **Power BI Desktop** e, em *Arquivo ▸ Opções ▸ Recursos de visualização*, habilite **Power BI Project (.pbip)** e **TMDL**.
2. Abra `BRUMS_HIIT.pbip`.
3. Em *Transformar dados ▸ Gerenciar parâmetros*, ajuste **`PastaDados`** para o caminho **desta pasta** na sua máquina (ex.: `C:\...\HANDEBOL\powerbi`). Clique em **Atualizar**.
4. O modelo carrega as 14 tabelas com as relações já definidas. Monte os visuais como no Caminho B (passo 3 em diante).

> Integridade: o PBIP é um *scaffold* gerado por código e **não foi testado no Power BI Desktop**. Se alguma parte do relatório/modelo precisar de ajuste ao abrir, use o Caminho B — é 100% confiável.

---

## Caminho B — importar o Excel (100% confiável)

1. **Obter dados ▸ Excel** → selecione `BRUMS_HIIT_PowerBI.xlsx` → marque as 14 abas → **Carregar**.
2. Em *Modelo*, crie as relações:
   - `fato_humor[dia]` → `dim_dia[dia]`
   - `fato_humor[momento]` → `dim_momento[momento]`
3. **Medidas**: abra `medidas_DAX.txt` e crie cada medida (*Modelagem ▸ Nova medida*).

### Páginas sugeridas do relatório

**1 · Visão geral (KPIs)**
- 6–8 **cartões**: `dz Fadiga física`, `AUC Fadiga física`, `% Iceberg`, e da aba `kpis` (CFI, HTMT, Tucker φ) via segmentação de `kpis[kpi]` + cartão `KPI valor`.
- **Gráfico de barras** de `resposta_aguda`: eixo Y = `variavel`, X = `dz`; formatação condicional pela medida `Flag sentinela`; rótulo `Rótulo dz (IC95%)`.

**2 · Perfil de humor (radar)**
- Visual **Radar** (importe "Radar Chart" do AppSource) com `perfil_radar[subescala]` e as medidas/valores `pre` e `pos`.

**3 · Monitoramento diário**
- **Gráfico de linhas**: eixo X = `trajetoria_diaria[dia]`, valores = `valor`, legenda = `variavel`. Adicione faixas de alerta (bandas do eixo Y) e um marcador para dias de HIIT (`hiit_dia`).

**4 · Mapa 4D**
- **Gráfico de dispersão**: X = `bolhas_4d[resposta_dz]`, Y = `acumulo_dia`, Tamanho = `pct_entre_atletas`, Legenda/cor = `pct_atletas_positivos`, Detalhe = `variavel`.

**5 · Diagnóstico & variância**
- **ROC**: barras de `roc_prepos[AUC]` por `variavel` (linha de referência em 0,50 e 0,70).
- **Variância**: barras 100% empilhadas de `variabilidade` (`pct_entre_atletas` vs. 100−).

**6 · Confiabilidade**
- **Tabela/barras** de `confiabilidade` (α com IC95%, ω) e destaque da linha 0,70.

### Filtros (segmentações)
Adicione segmentações por `dim_dia[tipo_dia]` (HIIT × técnico-tático), `dim_dia[dia]` e `dim_momento[rotulo]` (Pré/Pós) para recalcular tudo ao vivo.

---

## Renders 4K / 3D

`Dashboard_4K.png` e `Graficos_3D_4K.png` são imagens 3840×2160 (4K) prontas para
projeção/impressão; `BRUMS_HIIT_4K_3D.pdf` reúne as duas. Para regenerar:

```bash
python build_powerbi_data.py   # atualiza o Excel
python build_pbip.py           # regenera o projeto PBIP
python build_4k_3d.py          # regenera os PNGs 4K e o PDF
```

> Observação sobre 3D: gráficos 3D impressionam, mas podem distorcer a leitura de
> valores (perspectiva/oclusão). Aqui eles são um complemento visual — para decisão
> quantitativa, use os visuais 2D do dashboard, que preservam a comparação exata.
