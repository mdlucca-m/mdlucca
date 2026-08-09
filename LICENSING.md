# Licenciamento white-label — vender acesso ao produto

O produto só funciona com uma **licença** assinada por você. Você emite uma
licença para **quem pagar** (ou uma **cortesia grátis** quando quiser), com a
validade que definir. Sem licença válida, a API responde **402** em tudo que não
seja saúde/licença/marca/docs. Ninguém consegue forjar uma licença: você assina
com uma **chave privada** (só sua) e o software valida com a **chave pública**
embutida (Ed25519).

## 1. Uma vez: gerar o seu par de chaves

```bash
python3 scripts/make_license.py --genkey
```
- Salva a **chave privada** em `data/vendor_private.key` — **guarde com segurança
  e NUNCA compartilhe/versione** (é o que autoriza emitir licenças).
- Imprime a **chave pública** — cole em `app/licensing.py`
  (`VENDOR_PUBLIC_KEY_B64 = "..."`) e faça commit. Só a pública vai no produto.

> Já existe um par gerado neste repositório (a pública está embutida). Para uso
> real, gere o **seu** par e substitua a pública. Se perder a privada, não
> conseguirá emitir novas licenças válidas para aquela pública.

## 2. Emitir uma licença (para quem pagou, ou cortesia)

```bash
# cliente pago, 1 ano, com a marca dele
python3 scripts/make_license.py issue --licensee "Academia X" \
    --brand "X Performance" --plan pro --days 365 --out academia_x.key

# cortesia grátis por 30 dias
python3 scripts/make_license.py issue --licensee "Amigo" --plan cortesia --days 30

# acesso perpétuo (sem expirar)
python3 scripts/make_license.py issue --licensee "Sócio" --days 0
```
Entregue o **arquivo `.key`** (ou o token dentro dele) ao cliente.

Campos úteis: `--brand` trava a marca exibida; `--features a,b` limita recursos
(vazio = tudo); `--max-athletes N` grava um limite; `--days 0` = perpétua.

## 3. O cliente ativa

Uma das opções:
```bash
# a) variável de ambiente com o token
export MDLUCCA_LICENSE="<conteudo-do-arquivo.key>"
# b) caminho do arquivo
export MDLUCCA_LICENSE_FILE=/caminho/academia_x.key
# c) copiar para data/license.key
cp academia_x.key data/license.key
```
Confira em `GET /license` (deve mostrar `"valid": true`).

## 4. Marca do cliente (white-label)

Cada licenciado roda com a **marca dele**. Defina em `config/brand.json`:
```json
{ "name": "X Performance", "primary": "#0a84ff", "tagline": "avaliação de atletas" }
```
(ou via variável `MDLUCCA_BRAND='{"name":"..."}'`). Se a licença tiver `brand`,
ela **trava** o nome no valor licenciado. O nome/cor aparecem nos relatórios
(`/r/{token}`) e em `GET /branding`.

## 5. Encerrar / renovar acesso

- **Expiração**: quando `expires` passa, o acesso para sozinho (renove emitindo
  uma nova licença).
- **Perpétua**: use `--days 0` (não expira).
- **Revogar antes da hora**: reative o cliente com uma nova licença de validade
  curta, ou troque o par de chaves (invalida todas as licenças antigas — use só
  em caso extremo).

## Deploy

No servidor, defina `MDLUCCA_LICENSE` (token) nas variáveis de ambiente — o
`data/` é efêmero em alguns hosts, então a variável é o caminho mais seguro.
Veja `DEPLOY.md`.

## Segurança (resumo)

- Chave **privada** = seu cofre. Perdeu, não emite mais; vazou, podem forjar.
- Chave **pública** vai no código (pode ser aberta).
- Licenças são **offline** (validam sem internet). Para revogação fina em tempo
  real, o roadmap prevê uma lista de revogação/consulta online.
