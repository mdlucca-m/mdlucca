# Perfis de humor no handebol de elite — microciclo terminal de pré-temporada

Pipeline reproduzível do artigo *Limites, derivadas e piso de ruído aplicados aos perfis de
humor: comportamento das dimensões do BRUMS e resposta a estímulos distintos na última semana
de pré-temporada de atletas de handebol de elite*.

## O que há aqui

```
dados/     agregados anonimizados em JSON (entrada de tudo o mais)
analise/   rotina que produz o recorte por tipo de estímulo (U_estimulo.json)
figuras/   três roteiros que geram as nove figuras do artigo
texto/     ET.py — todo o texto do artigo como estruturas Python
montar_artigo.py   monta o .docx (texto + tabelas + figuras)
saida/     figuras e .docx gerados (fora do controle de versão)
```

## Como reproduzir

```bash
python3 figuras/UE1.py    # Figuras 1 a 3
python3 figuras/UE2.py    # Figuras 4 a 6
python3 figuras/UE3.py    # Figuras 7 a 9
python3 montar_artigo.py  # saida/ARTIGO_INOVACAO_PERFIS_HUMOR_HANDEBOL.docx
```

Dependências: `numpy`, `scipy`, `matplotlib`, `python-docx`. A variável de ambiente `HH_RAIZ`
sobrepõe a raiz inferida, caso os diretórios sejam movidos.

## Proteção de dados

A base primária contém nomes completos associados a escores de humor e a registros de lesão e
**não** está neste repositório. A substituição por códigos `A01`–`A27` ocorre na rotina de
importação, antes de qualquer análise; apenas os agregados anonimizados em `dados/` foram
versionados. Nenhum arquivo aqui permite reidentificação.

Como consequência, a etapa de importação a partir das planilhas não é reproduzível a partir
deste diretório: o pipeline parte dos JSON derivados. Tudo do `U_*.json` em diante roda.

## O núcleo metodológico

Cada série diária — de médias das subescalas ou de prevalência dos perfis — passa por quatro
etapas antes de qualquer leitura:

1. **Incerteza por ponto** — erro-padrão diário (amostral para médias, binomial para
   prevalências).
2. **Piso de ruído** — média dos sete erros-padrão. Responde a "quanta oscilação a amostragem,
   sozinha, produz nesta série?".
3. **Suavização** — filtro binomial de três pontos (¼, ½, ¼), extremos preservados.
4. **Derivadas** — primeira (velocidade) e segunda (aceleração) da série suavizada, expressas
   em unidades do piso, o que torna comparáveis variáveis de amplitudes distintas.

O veredito é explícito: declara-se variação real quando |Δ D1→D7| supera o piso; caso
contrário, atribui-se a oscilação à flutuação amostral. O mesmo princípio governa o teste de
cruzamento entre duas séries — a inversão só é reconhecida quando a diferença ultrapassa o
limiar combinado antes **e** depois do ponto de troca.

O piso binomial encolhe em prevalências próximas de zero e torna o critério permissivo. O caso
do perfil Everest invertido (dois pares no conjunto inteiro) está assinalado na figura e no
texto como não interpretável.

## Achados que o pipeline sustenta

- Vigor −3,12 e fadiga +3,49 ao longo da semana, ambos acima do piso, com tendência monotônica
  (teste L de Page). A depressão é a única série que não supera o piso.
- A deterioração concentra-se em duas transições (D1→D2 e D6→D7) e deixa um platô entre elas.
- Iceberg 37,0% → 19,0%; barbatana de tubarão 11,1% → 28,6%; faixa de risco 29,6% → 52,4%.
- Inversão **estabelecida** entre vigor e fadiga em D5,03; a troca de posição entre faixa
  favorável e faixa de risco é classificada como divergência, não inversão.
- A distribuição dos perfis **não** difere por tipo de estímulo (χ² = 7,58; p = 0,670), nem a
  das faixas (χ² = 4,45; p = 0,349). As variáveis contínuas diferem — a classificação
  categórica perde resolução onde a diferença existe.
- A migração intradiária para a faixa de risco é robusta no conjunto (27 entram, 9 saem;
  p = 0,005), mas a atribuição a um estímulo específico não sobrevive à correção de Holm.

## Ressalva de delineamento

Os tipos de estímulo não foram distribuídos ao acaso: HIIT em D2, D4 e D7; amistoso em D3 e
D5; técnico/força apenas em D6. O tipo de estímulo confunde-se, portanto, com a posição no
microciclo e com a carga acumulada. Nenhuma inferência sobre especificidade de estímulo é
separável de efeito cumulativo neste desenho.
