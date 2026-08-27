# Busca bibliográfica — PubMed, Scopus e Web of Science

Camada que reexecuta a estratégia de busca nas três bases via API, deduplica e
atualiza a biblioteca SQLite de forma incremental, gravando a proveniência de
cada execução.

```
scripts/
  atualizar_buscas.py     CLI: executa a busca e atualiza a biblioteca
  testar_busca.py         63 verificações ponta a ponta, sem rede
  gerar_schema.py         regenera sql/schema.sql a partir do DDL
  migrate.R              aplica sql/schema.sql
  busca/
    estrategia.py         fonte única dos blocos PCC e das seis sintaxes
    clientes.py           PubMed (E-utilities), Scopus (Search), WoS (Expanded/Starter)
    normalizar.py         registros brutos → esquema `artigo`; deduplicação
    deposito.py           upsert incremental + tabelas de proveniência
    fixtures/             respostas gravadas das três APIs, para o teste
```

## Uso

```bash
# quantos registros cada base declara, sem baixar nada
python3 scripts/atualizar_buscas.py --contar-apenas

# execução completa, gravando as respostas cruas para auditoria
python3 scripts/atualizar_buscas.py \
    --db data/BIBLIOTECA_HANDEBOL.sqlite \
    --bruto data/bruto/2026-08-27

# só uma base, limitado, para verificar credenciais
python3 scripts/atualizar_buscas.py --bases scopus --limite 50

# imprimir as consultas efetivamente submetidas (para o Apêndice A)
python3 scripts/atualizar_buscas.py --imprimir-consultas
```

Ao final o comando imprime a **Tabela 1 do manuscrito já preenchida** a partir
dos dados da execução — recuperados e declarados por base, com a observação de
qualquer base que tenha falhado. Ela deixa de ser digitada à mão, que é a
origem do achado G1 da revisão.

## Credenciais

| Variável | Base | Obrigatória | Onde obter |
|---|---|---|---|
| `NCBI_API_KEY` | PubMed | não — sem ela roda a 3 req/s em vez de 10 | conta NCBI → Settings → API Key Management |
| `NCBI_EMAIL` | PubMed | recomendada pela NLM | — |
| `SCOPUS_API_KEY` | Scopus | **sim** | https://dev.elsevier.com (gratuita para uso acadêmico) |
| `SCOPUS_INSTTOKEN` | Scopus | não — habilita a view `COMPLETE` (resumo e lista completa de autores) | suporte da Elsevier, vinculado à assinatura da instituição |
| `WOS_API_KEY` | Web of Science | **sim** | https://developer.clarivate.com (exige assinatura institucional) |

Sem `SCOPUS_INSTTOKEN` a API responde 401/403 à view `COMPLETE`; o cliente
detecta e cai para `STANDARD` sozinho, mas os registros vêm **sem resumo**.
Como a triagem por título e resumo (§3.6) depende do resumo, vale pedir o
insttoken à biblioteca da instituição antes de rodar a busca definitiva.

No Web of Science o cliente tenta a **Expanded API** primeiro, que devolve
resumo e afiliação; sem entitlement, cai para a **Starter API**, que traz DOI,
PMID e metadados de fonte, mas nem resumo nem país. A fusão na deduplicação
recupera o resumo pela versão do PubMed quando o mesmo estudo aparece nas duas.

## Rede

Os três hosts precisam estar liberados na política de egresso do ambiente:

```
eutils.ncbi.nlm.nih.gov      api.elsevier.com      api.clarivate.com
```

Neste ambiente remoto os três respondem **403 ao CONNECT** — a política atual
não os inclui. Não há contorno a partir da sessão; o host precisa ser liberado
na configuração do ambiente. O cliente distingue esse caso de uma falha de
credencial e o reporta como `rede:` no rendimento por base, em vez de registrar
zero recuperados.

Vale liberar também `api.crossref.org`, necessário para a verificação de DOI
(achado G5).

## Decisões de implementação

**A estratégia é uma coisa só.** Os blocos PCC vivem em `estrategia.py` como
listas de termos; as sintaxes de PubMed, Scopus, WoS e LILACS são *geradas*
delas. Atualizar a busca é editar uma lista, não reescrever seis strings que
divergem em silêncio. As contagens conferem com o declarado no manuscrito:
16 descritores MeSH e 62 termos livres no conceito, 6 e 27 no contexto,
16 termos livres na população, 15 descritores DeCS.

**Scopus não indexa com MeSH.** A estratégia do Apêndice A submete
`KEY("Stress, Psychological")` ao Scopus — descritor MeSH em forma invertida,
que praticamente nunca casa num índice de palavras-chave de autor. A geração
usa uma lista própria de termos de assunto (`CONCEITO_ASSUNTO`) para as bases
que indexam assim, e mantém o MeSH só onde ele existe, que é o PubMed.

**Envio por POST.** A consulta do PubMed tem ~3,2 mil caracteres, acima do que
muitos intermediários aceitam em URL. Tanto o `esearch` quanto o `efetch` vão
por POST, como a NLM recomenda para termos longos, e a paginação usa o
histórico do servidor (`WebEnv`/`query_key`) em vez de repetir a consulta.

**Paginação por cursor no Scopus.** É a única forma de passar do registro
5.000; `start` satura antes disso.

**Deduplicação na ordem declarada no protocolo (§3.11)**: DOI → PMID → título
normalizado. Ao fundir, o registro sobrevivente só recebe valores em campos
vazios, e o campo `fonte` acumula as bases de origem (`PubMed; Web of Science`),
o que torna a sobreposição entre bases mensurável em vez de invisível. Títulos
com menos de 16 caracteres normalizados não disparam fusão, para evitar falso
positivo.

**A busca nunca sobrescreve curadoria.** O upsert toca apenas os campos
bibliográficos; `variaveis_analisadas`, `instrumentos`, `sintese`,
`desenho_estudo` e os demais campos de extração ficam intactos. Verificado no
teste.

**Proveniência gravada.** Cada execução escreve uma linha em `busca_execucao`
(com o texto integral das consultas submetidas), uma por base em
`busca_rendimento` e uma por duplicata em `busca_duplicata`, com o critério que
a identificou. A view `v_rendimento_por_base` serve a Tabela 1; as duplicatas
sustentam o diagrama PRISMA.

## Testes

```bash
python3 scripts/testar_busca.py     # 63 verificações, sem rede
```

Cobre: contagem de termos por bloco e balanceamento das quatro sintaxes;
parsing das quatro formas de resposta (PubMed XML, Scopus JSON, WoS Starter,
WoS Expanded); dedução de país por afiliação; normalização de DOI e de título;
os três critérios de deduplicação isoladamente; fusão de campos entre bases;
idempotência da recarga; preservação de campos de curadoria; e a geração da
Tabela 1.

As fixtures em `busca/fixtures/` reproduzem a estrutura real de cada API sobre
artigos que existem — verificados no PubMed — de modo que uma mudança de
formato de resposta apareça como falha de teste, e não como campo vazio na
biblioteca.

Validado também contra a biblioteca entregue de 2.445 artigos: os índices
únicos de DOI e PMID são criados sem conflito, registros já existentes são
reconhecidos por DOI e atualizados em vez de duplicados.

## Nota sobre `migrate.R`

O `sql/schema.sql` é gerado de `scripts/busca/deposito.py` por
`scripts/gerar_schema.py`, e não deve ser editado à mão.

O `migrate.R` foi corrigido em três pontos que impediriam a aplicação correta
desse arquivo:

1. **Instruções descartadas em silêncio.** O aplicador dividia o SQL por `;` e
   pulava qualquer bloco começando com `--`. Como o cabeçalho de comentário do
   `schema.sql` fica grudado na primeira instrução, a tabela `artigo` — a
   principal — seria pulada sem erro. Agora as linhas de comentário são
   removidas antes de o bloco ser avaliado.
2. **`on.exit` no nível superior.** Fora de uma função, `on.exit` roda ao fim
   da expressão de nível superior, não ao fim do script, de modo que a conexão
   podia ser fechada cedo. A migração passou a viver dentro de `migrar()`.
3. **Sem transação.** Um erro no meio deixava o banco parcialmente migrado.
   Agora tudo roda em transação, com `ROLLBACK` no caminho de erro, e o script
   aborta se o backup falhar em vez de seguir e alterar o banco.

Falha explicitamente se o schema contiver blocos `BEGIN ... END;` (gatilhos),
que um separador por `;` partiria ao meio.
