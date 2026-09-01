# A base única

Tudo o que o estudo produziu está em **`base/humor_handebol.sqlite`**. Não é preciso abrir planilha
alguma para consultar um resultado.

## Um comando reconstrói tudo

```bash
./atualizar.sh
```

Ele refaz a base canônica a partir da fonte-verdade, recomputa todas as análises, reconstrói o banco,
recolhe o acervo das planilhas, resolve os DOI, reindexa a busca e exporta os CSV.

## Consultar sem escrever SQL

```bash
./scripts/consultar.py resumo                   # visão geral
./scripts/consultar.py dia                      # painel dia a dia
./scripts/consultar.py confronto                # não paramétrica × paramétrica × modelo misto
./scripts/consultar.py resultado --variavel Vigor --sig
./scripts/consultar.py serie Fadiga             # série com piso, derivadas e choques
./scripts/consultar.py perfil --recorte estimulo
./scripts/consultar.py auditoria                # os seis achados
./scripts/consultar.py buscar "efeito de piso"  # busca em tudo, inclusive no acervo
./scripts/consultar.py abas --categoria análise # o que existe nas planilhas antigas
./scripts/consultar.py sql "SELECT ..."         # consulta livre
```

## As três camadas

| Camada | Tabelas | Para que serve |
|---|---|---|
| **Canônica** | `atleta`, `dia`, `variavel`, `registro`, `atleta_dia`, `pre_pos`, `serie_diaria`, `serie_perfil` | Os dados limpos e categorizados. É daqui que sai toda análise. |
| **Resultados** | `resultado`, `prevalencia`, `unidade_analise`, `auditoria`, `referencia` | Todo número dos artigos, em formato longo. Um `SELECT` responde qualquer pergunta. |
| **Acervo** | `fonte`, `aba`, `celula` | As 218 abas das seis planilhas, com procedência, para quando for preciso conferir a origem. |

Vistas prontas: `v_painel_dia`, `v_confronto_vias`, `v_significativos`.

## Proteção de dados

Nenhum nome de atleta existe na base. A codificação `A01`–`A27` acontece na rotina de importação, e o
acervo passa por um raspador que substitui qualquer nome do elenco antes de gravar — verificado ao
fim de cada carga (a última varredura encontrou zero ocorrências). As planilhas de origem **não** são
versionadas.

## Estrutura do resultado

A tabela `resultado` guarda tudo no mesmo formato, o que permite comparar vias de análise:

`dominio` (descritiva, tendência, contraste, associação, categórica, modelo, confiabilidade, série) ·
`via` (não paramétrica, paramétrica, modelo misto, robusta) · `unidade` · `variavel` · `recorte` ·
`teste` · `estatistica` · `p` · `p_ajustado` · `efeito` · `ic_inf`/`ic_sup` · `n` · `artigo`.

Exemplo — tudo o que sustenta uma frase do artigo:

```sql
SELECT via, teste, rotulo_estatistica, estatistica, p, rotulo_efeito, efeito, n
FROM resultado WHERE variavel='Vigor' AND recorte LIKE 'D1%';
```
