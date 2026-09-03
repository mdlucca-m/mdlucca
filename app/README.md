# ELASE Performance — app de prescrição e controle de treino

App de página única (HTML + Chart.js) publicado como Artifact no claude.ai, com banco de dados
compartilhado em tempo real. Equipe **ELASE Voleibol Masculino · Categoria Adulto**.

**Link do app:** https://claude.ai/code/artifact/413ba4ea-45bd-4ed1-bedf-41d98b87217e

## Arquivos

| Arquivo | Uso |
|---|---|
| `elase_app.html` | Código-fonte do app (um arquivo só) |
| `seed_dados_iniciais.js` | Gera os documentos iniciais do banco (elenco, periodização, sessões, testes) |

## Páginas

Barra lateral com ícones; as três últimas só abrem para quem tem permissão de edição no artifact.

1. **Painel ao Vivo** — quem está treinando agora, carga e tonelagem do dia, adesão, ACWR por atleta, últimos registros
2. **Minha Sessão** — check-in com BRUMS, cronômetro, séries editáveis, timer de descanso, check-out com PSE e BRUMS
3. **Área do Atleta** — ficha, antropometria, carga sessão a sessão, volume, TMD antes/depois, CMJ
4. **Evolução** — carga concentrada por bloco, distribuição por tipo, intensidade relativa, contatos, 1RM, potência
5. **Testes de Campo** — 1RM, saltos, velocidade, agilidade; alimenta a carga em kg da prescrição
6. **Prescrição** *(treinador)* — monta a sessão por periodização, publica para a equipe ou para um atleta
7. **Monitoramento** *(treinador)* — mineração de todas as sessões, 33 variáveis, filtros e exportação CSV
8. **Elenco e Configuração** *(treinador)* — cadastro dos atletas e parâmetros da temporada

## Instrumentos de monitoramento

- **BRUMS** (24 itens, 6 subescalas, 0–4) antes e depois de cada sessão, com Distúrbio Total de Humor (TMD)
  = Tensão + Depressão + Raiva + Fadiga + Confusão − Vigor + 100
- **Escala de Sonolência de Karolinska** (1–9) no check-in e no check-out
- **Sono** (horas, qualidade 1–5, latência), **estresse percebido** (0–10) e **dor muscular** (0–10)
- **PSE da sessão** (0–10) no check-out → carga interna em UA = duração × PSE
- Derivados: carga aguda 7 d, crônica 28 d, ACWR, monotonia, strain, tonelagem, intensidade média
  relativa, densidade (kg/min), contatos pliométricos

## Banco de dados

Coleções: `config`, `atletas`, `prescricao`, `execucao`, `wellness`, `testes`, `antropometria`, `coach`.
A execução e o wellness são agregados por atleta e por mês (um documento por atleta/mês), para caber
no limite de 5.000 documentos do artifact.

Controle de acesso por regras do próprio banco — não é só a tela que esconde:

| Caminho | Leitura | Escrita |
|---|---|---|
| (raiz: execução, wellness) | qualquer visualizador | qualquer visualizador |
| `config`, `atletas`, `prescricao`, `testes`, `antropometria` | qualquer visualizador | só quem tem edição |
| `coach` | só quem tem edição | só quem tem edição |

Um atleta com link de leitura registra o próprio treino, mas não consegue gravar em prescrição nem no
elenco — mesmo alterando o código da página no navegador.

## Regerar os dados iniciais

```bash
node seed_dados_iniciais.js     # escreve ./seed/<colecao>/<documento>.json
```
