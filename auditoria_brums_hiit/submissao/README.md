# Pacote de submissão

Material de apoio para submissão do manuscrito **BRUMS × HIIT no handebol** a um
periódico. Personalize os campos entre colchetes `[...]` antes de enviar.

## Arquivos

- **`Carta_apresentacao_BRUMS_HIIT.docx`** — carta de apresentação (cover letter)
  ao editor: resume a contribuição, os três achados-âncora (resposta no eixo
  energia–fadiga; forte individualidade; desacoplamento carga↔humor), a
  reprodutibilidade e as declarações padrão (originalidade, autoria, conflitos de
  interesse, ética/Helsinque). Preencher: periódico, cidade/data, nº do parecer do
  CEP, nome/afiliação/e-mail/ORCID do autor correspondente.

- **`Checklist_STROBE_BRUMS_HIIT.docx`** — os 22 itens da diretriz STROBE (estudos
  observacionais) mapeados ao local em que cada um é atendido no pacote. Preencher:
  item 22 (financiamento).

## O que ainda depende do autor

| Campo | Onde |
|---|---|
| Nome do periódico e editor | carta |
| Cidade e data | carta |
| Nº do parecer do Comitê de Ética | carta · STROBE item 9 |
| Autor correspondente (nome, afiliação, e-mail, ORCID) | carta |
| Fonte de financiamento (ou ausência) | STROBE item 22 |

## Como regenerar

`node /tmp/build_submissao.js` (script de build dos dois documentos; requer o
pacote `docx` do npm). O script vive no scratchpad da sessão — copie-o para o
repositório se quiser versioná-lo.
