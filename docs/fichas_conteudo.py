#!/usr/bin/env python3
"""O conteúdo das fichas. O desenho está em fichas_treino.py.

    python3 fichas_conteudo.py            # gera todas
    python3 fichas_conteudo.py potencia   # gera uma
"""

import sys

from fichas_treino import (AMBAR, AMBAR_CLARO, VERDE, VERDE_CLARO, gerar,
                           montar_registro)

# ════════════════════════════════════════════════════════════════════════════
# FORÇA PURA — 4 x 4, carga submáxima
# ════════════════════════════════════════════════════════════════════════════
# Cinco exercícios vieram pedidos. Os dois acrescentados fecham os padrões que
# faltavam: PUXAR HORIZONTAL e DOBRA DE QUADRIL. Sem eles a sessão teria duas
# séries de empurrar para cada uma de puxar, e num atleta que ataca centenas de
# bolas por semana esse desequilíbrio escapular cobra caro.
FORCA = {
    "arquivo": "ELASE-treino-forca-pura.pdf",
    "meta_titulo": "ELASE - Treino de forca pura",
    "meta_assunto": "Forca pura 4x4 com carga submaxima",
    "titulo": "Treino de força pura",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "4 séries &times; 4 repetições &nbsp;&middot;&nbsp; "
                 "2 minutos entre séries &nbsp;&middot;&nbsp; carga submáxima",
    "rotulo_carga": "% 1RM",
    "abertura":
        "<b>O que é carga submáxima.</b> É a carga com que você faz as 4 "
        "repetições e ainda <b>sobrariam 2</b> — cerca de 85% do seu máximo. "
        "Força pura não se treina indo até a falha: se a quarta repetição sai "
        "arrastando, a carga está alta demais e o treino virou outra coisa. "
        "Na dúvida, <b>fique leve</b>: o verso explica como achar a carga sem "
        "saber o seu 1RM.",
    "aquecimento_titulo": "Aquecimento — antes do primeiro exercício de cada padrão",
    "aquecimento_nota": "Quatro séries a 85% sem rampa é lesão esperando "
                        "acontecer. Estas séries não contam como treino e não "
                        "devem cansar.",
    "aquecimento_cab": ["CARGA", "SÉRIES", "PAUSA"],
    "aquecimento": [
        ["Barra vazia", "1 × 8", "solta"],
        ["50% da carga de trabalho", "1 × 5", "1 min"],
        ["65% da carga de trabalho", "1 × 3", "1 min"],
        ["75% da carga de trabalho", "1 × 2", "2 min"],
    ],
    "exercicios": [
        ("Agachamento livre", "joelho — o mais neural, por isso vem primeiro",
         "4 × 4", "2 min", "85%"),
        ("Supino reto com barra", "empurrar horizontal", "4 × 4", "2 min", "85%"),
        ("Levantamento terra", "dobra de quadril — ACRESCENTADO",
         "4 × 4", "2 min", "80%"),
        ("Puxador frente (pegada aberta)", "puxar vertical", "4 × 4", "2 min", "85%"),
        ("Desenvolvimento com barra", "empurrar vertical", "4 × 4", "2 min", "85%"),
        ("Remada curvada com barra", "puxar horizontal — ACRESCENTADO",
         "4 × 4", "2 min", "85%"),
        ("Remada alta", "ombro e trapézio — ver a nota do verso",
         "4 × 4", "2 min", "80%"),
    ],
    "nota_tabela":
        "As colunas da direita são para você escrever a carga que <b>realmente</b> "
        "usou em cada série, em quilos. É esse número que vira a sua referência no "
        "próximo ciclo — sem ele, o treino da semana que vem repete o desta.",
    "caixa_duracao":
        "<b>Duração prevista: 75 a 85 minutos</b> com o aquecimento. Se estiver "
        "muito mais rápido, a pausa de 2 minutos não está sendo respeitada — e a "
        "pausa é parte da prescrição, não um intervalo para conversa. É ela que "
        "permite a série seguinte sair com a mesma qualidade.",
    "verso": [
        ("h", "Achar a carga sem saber o seu 1RM"),
        ("p", "Ninguém precisa ter feito teste de máximo para treinar hoje. "
              "Faça assim, no primeiro exercício:"),
        ("espaco", 5),
        ("passos", [
            "Depois do aquecimento, escolha uma carga que <b>pareça</b> dar para "
            "6 repetições boas.",
            "Faça <b>4</b>. Se no fim da quarta você sentiu que ainda faria mais 2 "
            "com técnica limpa, é essa a carga. Mantenha nas quatro séries.",
            "Se sobraria mais de 2, <b>suba</b> de 5 em 5 kg na série seguinte. Se "
            "sobraria menos de 2, <b>desça</b>.",
            "Anote. Na semana que vem você começa daí, e não do zero.",
        ]),
        ("espaco", 8),
        ("tabela", ["O QUE VOCÊ SENTE NO FIM DA 4ª", "EQUIVALE A", "LEITURA"], [
            ("Sobrariam mais 3 repetições", "cerca de 80%", "leve para força pura"),
            ("Sobrariam mais 2 repetições", "cerca de 85%", "É AQUI que a sessão deve ficar"),
            ("Sobraria mais 1 repetição", "cerca de 88%", "pesado — só se o dia estiver bom"),
            ("Não sobraria nenhuma", "cerca de 91%", "falha técnica — não é submáxima"),
        ], [("BACKGROUND", (0, 2), (-1, 2), VERDE_CLARO),
            ("BOX", (0, 2), (-1, 2), 1.1, VERDE)]),
        ("espaco", 6),
        ("pq", "Estes percentuais são orientação, não medida: o mesmo 85% rende "
               "diferente num dia de sono ruim. Quem manda é o que você sente na "
               "barra, e a regra de sobrar 2 repetições vale acima do número da tabela."),
        ("espaco", 12),
        ("h", "Execução — o que muda o resultado"),
        ("notas", [
            ("Remada alta", "É o exercício de maior risco desta ficha para quem "
             "ataca. Pegada na largura dos ombros ou mais ABERTA, e o cotovelo não "
             "passa da linha do ombro. Se der dor ou pinçamento na frente do ombro, "
             "pare e troque por elevação lateral ou face pull — a perda de treino é "
             "zero e o ombro é o que te mantém em quadra."),
            ("Levantamento terra", "Vem depois do agachamento, então a lombar já "
             "chega cansada. Por isso ele está a 80% e não a 85%. Se a sessão "
             "estiver pesando, ele é o PRIMEIRO a reduzir — não o agachamento."),
            ("Supino", "Escápulas presas no banco e pés firmes no chão. Barra "
             "descendo até o peito com controle; quem quica a barra no peito treina "
             "outra coisa."),
            ("Desenvolvimento com barra", "Em pé, glúteo e abdômen apertados. A "
             "barra passa perto do rosto. Se a lombar arqueia para a barra subir, a "
             "carga está alta demais."),
            ("Agachamento", "Profundidade até onde o quadril desce SEM a lombar "
             "arredondar. Quem não desce por falta de tornozelo tem problema de "
             "mobilidade, não de força — e isso se resolve no aquecimento."),
        ]),
        ("espaco", 6),
        ("caixa", "<b>Por que dois exercícios a mais do que os cinco pedidos.</b> "
                  "Supino e desenvolvimento são empurrar; puxador é puxar vertical; "
                  "remada alta é ombro. Faltavam <b>puxar horizontal</b> (remada "
                  "curvada) e <b>dobra de quadril</b> (levantamento terra). Sem eles "
                  "a sessão teria duas séries de empurrar para cada uma de puxar, e "
                  "num atleta que ataca centenas de bolas por semana esse "
                  "desequilíbrio escapular cobra caro. Se precisar cortar para seis, "
                  "corte a <b>remada alta</b> — é a que tem mais risco e menos "
                  "transferência."),
        ("espaco", 12),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# POTÊNCIA — séries curtas, intenção máxima, pausa completa
# ════════════════════════════════════════════════════════════════════════════
# A regra que muda tudo em relação à ficha de força: aqui NÃO se repete o 4 x 4
# com carga alta. Potência é produto de força POR VELOCIDADE, e velocidade cai
# com fadiga. Série longa e pausa curta treinam resistência de força, não
# potência — parecem o mesmo treino no papel e são coisas diferentes no corpo.
POTENCIA = {
    "arquivo": "ELASE-treino-potencia.pdf",
    "meta_titulo": "ELASE - Treino de potencia 4x6",
    "meta_assunto": "Potencia 4x6 com carga leve, velocidade em toda repeticao",
    "titulo": "Treino de potência",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "4 séries &times; 6 repetições &nbsp;&middot;&nbsp; carga leve "
                 "&nbsp;&middot;&nbsp; velocidade em toda repetição",
    "rotulo_carga": "CARGA",
    "abertura":
        "<b>Aqui a carga não é o ponto — a velocidade é.</b> Potência é força "
        "<i>vezes</i> velocidade, e velocidade cai com cansaço. Por isso a carga é "
        "leve e a pausa é longa: cada repetição sai <b>o mais rápido que você "
        "conseguir</b>, e a descida é controlada. <b>Assim que a barra ou o salto "
        "desacelerar, a série acabou</b> — mesmo que faltem repetições no papel. "
        "Terminar a série lenta não treina potência: treina cansaço.",
    "aquecimento_titulo": "Aquecimento — obrigatório antes de qualquer barra",
    "aquecimento_nota": "Arrancar e saltar com o corpo frio é como se machuca. "
                        "Esta parte é o que permite a primeira série já sair rápida.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 a 8 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Agachamento só com o peso do corpo, subida rápida", "2 \u00d7 8",
         "do fraco ao forte"],
        ["Arranco e clean com a barra vazia", "2 \u00d7 3", "antes de pôr peso"],
    ],
    "exercicios": [
        ("Arranco (snatch)", "o mais técnico — para a série quando sair feio",
         "4 \u00d7 6", "3 min", "55%"),
        ("Clean", "tríplice extensão com recepção — mesma regra do arranco",
         "4 \u00d7 6", "3 min", "55%"),
        ("Agachamento com salto", "salto no lugar com barra — acima de 1,0 m/s",
         "4 \u00d7 6", "2 min", "25%"),
        ("Agachamento isométrico", "6 SEGUNDOS empurrando a trava — ver o verso",
         "4 \u00d7 6 s", "2 min", "máx."),
        ("Supino explosivo", "empurrar rápido — o braço do ataque acorda",
         "4 \u00d7 6", "2 min", "40%"),
        ("Puxada fechada", "puxa rápido, solta devagar",
         "4 \u00d7 6", "90 s", "50%"),
    ],
    "nota_tabela":
        "Anote a carga de cada exercício. Se em alguma série a barra saiu lenta, "
        "<b>pare o exercício ali</b> e marque um <b>X</b>. Série lenta não é para "
        "ser insistida: é a informação de que a sessão passou do ponto.",
    "caixa_duracao":
        "<b>Duração prevista: 70 a 80 minutos</b> com o aquecimento. São 144 "
        "repetições no total — este é um treino completo, não um aquecimento "
        "reforçado. Se estiver muito mais rápido, a pausa não está sendo "
        "respeitada, e a pausa aqui é o que garante que a série 4 saia tão rápida "
        "quanto a 1.",
    "verso": [
        ("caixa", "<b>EM DIA DE JOGO, esta ficha não vai inteira.</b> São 144 "
                  "repetições: como treino está certo, como preparação para jogar à "
                  "noite é o contrário do que se quer. Se for dia de jogo, faça "
                  "<b>2 séries em vez de 4</b>, <b>3 repetições em vez de 6</b>, "
                  "corte o isométrico, e termine pelo menos <b>6 horas antes do "
                  "apito</b>. A pergunta que decide: você saiu da sala com vontade "
                  "de fazer mais? Se saiu ofegante, foi longe demais — e isso não "
                  "se conserta até a noite.",
         AMBAR_CLARO, AMBAR),
        ("espaco", 12),
        ("h", "As regras de hoje"),
        ("passos", [
            "<b>Sobe rápido, desce devagar.</b> Vale para todos: a subida é a mais "
            "rápida que você conseguir, a descida é controlada. Descer solto não "
            "treina nada e castiga a articulação.",
            "<b>Intenção máxima, carga baixa.</b> A carga é leve de propósito — ela "
            "existe para você poder ser rápido, não para pesar. Sem 1RM lançado, a "
            "carga certa é a mais pesada com que a subida ainda sai <b>visivelmente "
            "explosiva</b>; quando ela parece só \u201cforte\u201d, está pesado demais.",
            "<b>Não trave a articulação no fim.</b> No supino e na puxada, terminar "
            "o movimento estalando o cotovelo é o único jeito de se machucar num "
            "treino leve. Pare um pouco antes da extensão completa.",
            "<b>Pausa inteira, sempre.</b> É ela que garante que a série seguinte "
            "saia tão rápida quanto a primeira. Encurtar a pausa hoje transforma "
            "ativação em cansaço.",
            "<b>Dormiu mal, acordou com dor ou com o corpo estranho?</b> Pule o "
            "arranco e o clean — são os que exigem técnica, e técnica é a primeira "
            "coisa que some com sono ruim — e avise a comissão. Isso não é "
            "frescura: é informação que muda a escalação.",
        ]),
        ("espaco", 10),
        ("h", "Os dois exercícios que precisam de explicação"),
        ("notas", [
            ("Agachamento isométrico", "Aqui o \u201c4 \u00d7 6\u201d é "
             "<b>4 séries de 6 SEGUNDOS</b>, e não 6 repetições — repetição de "
             "isométrico não existe. Barra travada na altura em que o joelho fica a "
             "uns 110 graus, e você empurra com <b>tudo</b> por 6 segundos, como se "
             "fosse arrancá-la do lugar. Se a sala não tiver trava, faça o "
             "agachamento parando 2 segundos no fundo e subindo o mais rápido que der."),
            ("Arranco e clean", "<b>Seis repetições seguidas é muita coisa para um "
             "levantamento olímpico</b>, e por isso eles estão a 55% e não a 60%: "
             "lá pela quarta a técnica começa a desmanchar, e é justamente aí que "
             "se aprende a errar rápido. A regra vale acima do número da folha: "
             "<b>se a repetição sair feia, a série acabou ali</b> — mesmo na "
             "terceira. Sem 1RM lançado, comece com a barra vazia e suba só "
             "enquanto o movimento continuar bonito."),
        ]),
        ("espaco", 8),
        ("h", "O que continua fora, e por quê"),
        ("notas", [
            ("Caixote e sprint", "Não há onde fazer. O agachamento com salto cobre "
             "a parte que mais interessa — a extensão rápida — e cobre sem a "
             "aterrissagem do caixote, que é carga excêntrica alta e a que mais "
             "deixa dor no dia seguinte."),
        ]),
        ("espaco", 8),
        ("caixa", "<b>Mande a PSE do JOGO também, nos dias em que houver</b> — não "
                  "só a da sala. No voleibol a maior parte da carga da semana vem da "
                  "quadra, e uma análise que só enxerga a sala enxerga menos da "
                  "metade do que o seu corpo levou."),
        ("espaco", 12),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# FORÇA PARA O VOLEIBOL — cada exercício com endereço numa demanda do jogo
# ════════════════════════════════════════════════════════════════════════════
# O que faz uma ficha ser "de vôlei" não é o nome no cabeçalho: é cada exercício
# responder a uma pergunta do jogo. Saltar, aterrissar em apoio assimétrico,
# desacelerar o corpo na queda, atacar com o braço acima da cabeça centenas de
# vezes por semana. Supino ficou de fora por isso — está explicado no verso.
FORCA_VOLEI = {
    "arquivo": "ELASE-forca-para-o-voleibol.pdf",
    "meta_titulo": "ELASE - Forca para o voleibol",
    "meta_assunto": "Oito exercicios de forca, cada um com endereco no jogo",
    "titulo": "Força para o voleibol",
    "titulo_verso": "Por que estes oito",
    "protocolo": "Oito exercícios &nbsp;&middot;&nbsp; carga submáxima "
                 "&nbsp;&middot;&nbsp; cada um com endereço no jogo",
    "rotulo_carga": "CARGA",
    "abertura":
        "<b>Carga submáxima quer dizer: sobrariam 2 repetições.</b> Se a última "
        "sai arrastando, está pesado demais e o treino virou outra coisa. "
        "Os cinco primeiros exercícios são os que constroem o salto e o ataque; "
        "os três últimos são os que te mantêm inteiro para usá-los. "
        "<b>Nenhum dos três últimos é acessório opcional</b> — são a parte da "
        "ficha com mais evidência de reduzir lesão, e a primeira que todo mundo "
        "corta quando o tempo aperta.",
    "aquecimento_titulo": "Aquecimento — antes do primeiro exercício com barra",
    "aquecimento_nota": "Estas séries não contam como treino e não devem cansar.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 min", "a mesma do app"],
        ["Barra vazia no padrão do agachamento", "1 \u00d7 8", "solta"],
        ["55% da carga de trabalho", "1 \u00d7 5", "1 min"],
        ["70% da carga de trabalho", "1 \u00d7 3", "2 min"],
    ],
    "exercicios": [
        ("Agachamento", "a força que sustenta o salto",
         "4 \u00d7 5", "3 min", "80%"),
        ("Stiff (terra romeno)", "cadeia posterior — é ela que freia a aterrissagem",
         "4 \u00d7 6", "2 min", "70%"),
        ("Búlgaro com halteres", "quase todo salto do vôlei sai e cai assimétrico",
         "3 \u00d7 8 cada", "2 min", "RIR 2"),
        ("Desenvolvimento com barra", "o braço do ataque trabalha acima da cabeça",
         "4 \u00d7 5", "2 min", "80%"),
        ("Supino reto com barra", "força de empurrar horizontal — base do bloqueio",
         "4 \u00d7 5", "2 min", "80%"),
        ("Remada unilateral com halter", "o contrapeso das oito séries de empurrar",
         "4 \u00d7 8 cada", "90 s", "RIR 2"),
        ("Nórdico de isquiotibiais", "excêntrica de posterior — desce devagar",
         "3 \u00d7 6", "2 min", "corpo"),
        ("Rotadores externos com elástico", "o manguito: o que mais se cobra e menos se treina",
         "3 \u00d7 15 cada", "60 s", "leve"),
    ],
    "nota_tabela":
        "Anote a carga de cada série, em quilos. É esse número que vira a sua "
        "referência no próximo ciclo — sem ele, o treino da semana que vem repete "
        "o desta.",
    "caixa_duracao":
        "<b>Duração prevista: 85 a 95 minutos</b> com o aquecimento — o supino "
        "acrescentou cerca de 12 minutos. Se o tempo apertar, <b>corte uma série do "
        "agachamento, do supino e da remada</b> (as duas últimas juntas, para a "
        "proporção não piorar) — nunca o nórdico e os rotadores. Eles levam 6 "
        "minutos somados e são a parte da ficha que te mantém jogando.",
    "verso": [
        ("h", "Cada exercício e a pergunta do jogo que ele responde"),
        ("notas", [
            ("Agachamento", "O salto é extensão de quadril e joelho contra o chão, "
             "e é o agachamento que constrói essa força. Profundidade até onde o "
             "quadril desce SEM a lombar arredondar — quem não desce por falta de "
             "tornozelo tem problema de mobilidade, não de força."),
            ("Stiff", "O vôlei cobra mais na descida do que na subida: cada "
             "aterrissagem é a cadeia posterior freando o corpo. Quem só agacha "
             "fica forte para subir e despreparado para cair. Excêntrica lenta, "
             "barra rente à perna, joelho levemente solto."),
            ("Búlgaro", "Quase nenhum salto do jogo sai dos dois pés igualmente, e "
             "quase nenhuma aterrissagem é simétrica. O trabalho unilateral é o que "
             "revela e corrige a diferença entre as pernas — e diferença grande "
             "entre lados é um dos previsores de lesão mais consistentes que existem."),
            ("Desenvolvimento com barra", "O ataque acontece acima da cabeça, e é "
             "ali que a força precisa existir. Em pé, glúteo e abdômen apertados; "
             "se a lombar arqueia para a barra subir, a carga está alta demais."),
            ("Supino", "Empurrar horizontal é a base do bloqueio e do apoio de "
             "braço na queda. Escápulas presas no banco e pés firmes no chão; barra "
             "descendo até o peito com controle — quem quica a barra no peito treina "
             "outra coisa. Amplitude até onde o ombro não rola para a frente."),
            ("Remada unilateral", "Sem puxada horizontal, quem treina muito acima "
             "da cabeça perde posição de escápula — e escápula fora de posição é "
             "como o ombro do atacante começa a doer. Puxa o cotovelo para trás, "
             "não o ombro para cima. <b>Ela está com 4 séries e não 3</b> por causa "
             "do supino: ver a caixa abaixo."),
            ("Nórdico de isquiotibiais", "É a dose com melhor evidência para "
             "reduzir lesão de posterior de coxa. Desça o mais devagar que "
             "conseguir e use as mãos só no fim. Vai dar dor muscular nas primeiras "
             "semanas; isso passa, a lesão que ele evita não."),
            ("Rotadores externos", "O manguito é o que o atacante mais cobra e "
             "menos treina. Carga leve, cotovelo colado no corpo, movimento vindo "
             "do ombro e não do tronco. Três minutos por semana aqui valem mais que "
             "qualquer coisa que se faça depois que o ombro já dói."),
        ]),
        ("espaco", 8),
        ("caixa", "<b>Por que a remada subiu para 4 séries.</b> Com supino e "
                  "desenvolvimento juntos, a sessão passou a ter <b>oito séries de "
                  "empurrar</b>. Num atleta que ataca e bloqueia — trabalho que já é "
                  "todo à frente do corpo — empurrar muito mais do que se puxa leva "
                  "o ombro para a frente e tira a escápula de posição, que é como a "
                  "dor de ombro do atacante começa. Quatro séries de remada contra "
                  "oito de empurrar ainda não é um empate, mas é o mínimo defensável. "
                  "Se você precisar encurtar a sessão, a conta muda junto: cortando "
                  "uma série do supino, corte também uma da remada."),
        ("espaco", 12),
        ("h", "Achar a carga sem saber o seu 1RM"),
        ("passos", [
            "Depois do aquecimento, escolha uma carga que <b>pareça</b> dar para "
            "duas repetições a mais do que as prescritas.",
            "Faça as repetições da folha. Se no fim ainda fariam mais 2 com técnica "
            "limpa, é essa a carga.",
            "Sobraria mais de 2, <b>suba</b> de 5 em 5 kg. Sobraria menos, "
            "<b>desça</b>. Nos exercícios marcados <b>RIR 2</b> a regra é essa "
            "mesma, e não há percentual nenhum a consultar.",
            "Anote. Na semana que vem você começa daí, e não do zero.",
        ]),
        ("espaco", 10),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# ONDA 7 / 5 / 3 / 1 — a prescrição muda de SÉRIE para série
# ════════════════════════════════════════════════════════════════════════════
# Duas decisões que valem mais do que os números:
#
# O "1" é uma repetição a 90%, NÃO um teste de 1RM. Noventa por cento é a carga
# de umas 4 repetições: fazer uma só deixa 3 de reserva. Oito máximos de verdade
# num dia não é treino, é competição — e nenhum deles sairia bom depois do
# terceiro, porque o que limita não é o músculo, é o sistema nervoso.
#
# O afundo para no 3. Unilateral com carga máxima apoia tudo num tornozelo e num
# joelho, com o tronco livre: o ganho da última série não paga o risco dela.
#
# Por isso as colunas de carga desta ficha não são "1ª/2ª/3ª/4ª": cada uma diz
# quantas repetições, a que percentual e com que pausa. É a prescrição inteira
# no cabeçalho, e o corpo da tabela fica todo em branco para o atleta escrever.
FORCA_ONDA = {
    "arquivo": "ELASE-forca-onda-7-5-3-1.pdf",
    "meta_titulo": "ELASE - Forca em onda 7/5/3/1",
    "meta_assunto": "Oito exercicios em onda 7-5-3-1 com carga crescente e pausa proporcional",
    "titulo": "Força em onda — 7 / 5 / 3 / 1",
    "titulo_verso": "Como se faz uma onda",
    "protocolo": "Oito exercícios &nbsp;&middot;&nbsp; 7, 5, 3 e 1 repetição "
                 "&nbsp;&middot;&nbsp; carga sobe, pausa sobe com ela",
    "rotulo_carga": "SEU 1RM",
    "cab_meio": ["SÉRIES", "ENTRE EX.", "SEU 1RM"],
    "escrever_de": 3,
    "cab_series": [
        "7 reps<br/>70%<br/>2 min",
        "5 reps<br/>78%<br/>2,5 min",
        "3 reps<br/>85%<br/>3 min",
        "1 rep<br/>90%<br/>3,5 min",
    ],
    "abertura":
        "<b>A carga sobe a cada série e a pausa sobe com ela</b> — está tudo no "
        "cabeçalho da tabela, de 7 repetições a 70% com 2 minutos até "
        "<b>1 repetição a 90% com 3 minutos e meio</b>. Encurtar a pausa não "
        "economiza tempo: troca a série pesada por uma série cansada. E "
        "<b>o “1” não é teste de máximo</b> — 90% é a carga de umas 4 "
        "repetições, então sobram 3.",
    "aquecimento_titulo": "Aquecimento — antes do primeiro exercício de cada padrão",
    "aquecimento_nota": "A série de 7 a 70% já é a sua rampa dentro do exercício. "
                        "Este aquecimento é o que vem antes da barra, e não deve cansar.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Barra vazia e depois 55% da carga", "1 × 8 e 1 × 5",
         "1 min entre elas"],
    ],
    "exercicios": [
        ("Agachamento livre", "joelho — o mais neural, por isso abre a sessão",
         "4", "3 min", ""),
        ("Supino reto com barra", "empurrar horizontal", "4", "3 min", ""),
        ("Levantamento terra", "dobra de quadril — lombar cansada? corte o 1",
         "4", "3 min", ""),
        ("Barra fixa com carga", "puxar vertical — não dá 7 com peso? use o puxador",
         "4", "3 min", ""),
        ("Desenvolvimento com barra", "empurrar vertical", "4", "3 min", ""),
        ("Remada curvada com barra", "puxar horizontal — o contrapeso do supino",
         "4", "3 min", ""),
        ("Hip thrust", "extensão de quadril — o mais seguro da ficha a 90%",
         "4", "3 min", ""),
        ("Afundo com halteres", "unilateral — <b>PARA NO 3</b>, não faz o 1. Ver o verso",
         "3", "3 min", ""),
    ],
    "nota_tabela":
        "Escreva o seu <b>1RM</b> na coluna estreita e os quilos que realmente usou "
        "nas quatro da direita. Não sabe o seu 1RM? O verso mostra como achar as "
        "cargas sem ele.",
    "caixa_duracao":
        "<b>Duração prevista: 105 a 120 minutos</b> com o aquecimento — oito "
        "exercícios com pausa cheia é uma sessão longa, e vale saber disso antes de "
        "chegar na metade. <b>Se tiver menos de 90 minutos:</b> faça os cinco "
        "primeiros com a onda inteira e os três últimos só até o 3. Corte a série, "
        "nunca a pausa.",
    "verso": [
        ("h", "A onda, série por série"),
        ("grade", ["SÉRIE", "REPS", "% 1RM", "PAUSA DEPOIS", "O QUE ESTA SÉRIE É"], [
            ["1ª", "7", "70%", "2 min",
             "rampa com volume — não deve ser difícil"],
            ["2ª", "5", "78%", "2 min 30 s", "a carga começa a pesar"],
            ["3ª", "3", "85%", "3 min", "a série que mais constrói força"],
            ["4ª", "1", "90%", "3 min 30 s",
             "a mais pesada do dia, com 3 repetições de reserva"],
        ], [0.11, 0.1, 0.12, 0.2, 0.47],
         [("BACKGROUND", (0, 3), (-1, 3), VERDE_CLARO),
          ("BOX", (0, 3), (-1, 3), 1.1, VERDE)]),
        ("espaco", 5),
        ("pq", "Depois da 4ª série vêm <b>3 minutos</b> antes do exercício "
               "seguinte. São 16 repetições por exercício, 128 na sessão."),
        ("espaco", 7),
        ("p", "<b>Intervalo proporcional é isto:</b> a pausa repõe o que a série "
              "gastou, e a de 1 a 90% gasta muito mais sistema nervoso do que a de "
              "7 a 70% — mesmo levando um sexto do tempo. Cortar pausa não encurta "
              "o treino, muda o treino."),
        ("espaco", 7),
        ("caixa", "<b>O “1” é uma repetição a 90%, não um teste de 1RM.</b> "
                  "Noventa por cento é a carga de umas 4 repetições: fazendo uma só, "
                  "sobram 3. Oito máximos de verdade num dia não é treino, é "
                  "competição — e nenhum sairia bom depois do terceiro. <b>Se a sua "
                  "repetição sai tremendo ou com a técnica mudando, a carga passou de "
                  "90%</b>: desça na semana que vem. Teste de máximo tem dia próprio, "
                  "três exercícios no máximo e alguém observando.",
         AMBAR_CLARO, AMBAR),
        ("espaco", 8),
        ("h", "Achar as cargas sem saber o seu 1RM"),
        ("passos", [
            "Comece pela <b>série de 3</b>: qual carga você faria 3 vezes com sobra "
            "de umas 3 repetições? Essa é a 3ª série (85%).",
            "A 1ª é essa carga <b>menos 15%</b>, a 2ª <b>menos 8%</b> e a 4ª é "
            "<b>mais 5%</b>. Com 100 kg na de 3: 85, 92 e 105.",
            "<b>Se a série de 7 for difícil, a conta inteira está alta</b> — desça "
            "tudo 5 kg e siga. Ela é rampa, não é teste.",
            "Anote os quatro. O seu 1RM é a carga da série de 3 <b>dividida por "
            "0,85</b> — e dela sai a onda da semana que vem.",
        ]),
        ("espaco", 8),
        ("h", "Os três exercícios com regra própria"),
        ("notas", [
            ("Afundo com halteres", "<b>Para no 3 — não faz a série de 1.</b> "
             "Unilateral com carga máxima apoia o corpo num tornozelo e num joelho, "
             "com o tronco livre: o ganho não paga o risco. São 7, 5 e 3 <b>em cada "
             "perna</b>, começando pela mais fraca — e a perna boa para no número "
             "que a fraca fez."),
            ("Levantamento terra", "Vem depois do agachamento, com a lombar já "
             "cansada. <b>Se na série de 3 a lombar arredondar ou a barra sair do "
             "corpo, não faça a de 1.</b> Parar no 3 num dia pesado é decisão boa, "
             "não desistência."),
            ("Barra fixa com carga", "Não faz 7 com peso pendurado? Use o puxador "
             "frente com os mesmos percentuais. Faz 7 sem peso mas não com? Onda com "
             "o peso do corpo e menos repetições (5, 4, 3, 2). O que não serve é "
             "trocar de padrão: ela e a remada são as únicas séries de puxar."),
        ]),
        ("espaco", 5),
        ("caixa", "<b>Não repita esta sessão em dois dias seguidos.</b> Oito "
                  "exercícios a 90% é carga neural alta: deixe <b>48 horas</b> antes "
                  "de outra pesada; com jogo em menos de 48 h, faça a de potência."),
        ("espaco", 4),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# POTÊNCIA NA BARRA — os levantamentos básicos levados pela velocidade
# ════════════════════════════════════════════════════════════════════════════
# Quatro exercícios vieram pedidos: supino, agachamento, stiff e terra. Três
# observações que mudaram a prescrição e estão escritas na folha:
#
# O STIFF NÃO É EXERCÍCIO DE POTÊNCIA. É excêntrico por natureza — o que ele
# treina é a descida, o freio. Ele fica, porque tem endereço no vôlei (é a
# cadeia posterior que freia cada aterrissagem), mas entra por último, com carga
# moderada e SEM a regra de velocidade dos outros cinco. Chamá-lo de potência
# seria mentira de folha.
#
# TERRA E STIFF JUNTOS SÃO MUITO QUADRIL. Com o agachamento, três dos quatro
# pedidos são dobra de quadril ou perna. Por isso os dois acrescentados vão para
# cima: push press (potência acima da cabeça, que é onde o ataque acontece) e
# remada curvada explosiva — sem ela a sessão teria supino e push press
# empurrando e nada puxando.
#
# SÉRIE DE 3, NÃO DE 6. Potência é força vezes velocidade, e velocidade cai com
# fadiga dentro da própria série. Série curta é o que mantém a última repetição
# tão rápida quanto a primeira.
POTENCIA_BARRA = {
    "arquivo": "ELASE-potencia-na-barra.pdf",
    "meta_titulo": "ELASE - Potencia na barra",
    "meta_assunto": "Potencia com os levantamentos basicos, carga leve e velocidade",
    "titulo": "Potência na barra",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Seis exercícios &nbsp;&middot;&nbsp; séries curtas "
                 "&nbsp;&middot;&nbsp; a velocidade é a prescrição",
    "rotulo_carga": "CARGA",
    "abertura":
        "<b>Hoje os levantamentos pesados saem leves e rápidos.</b> Potência é "
        "força <i>vezes</i> velocidade, e a velocidade é a parte que falta — por "
        "isso a carga é baixa de propósito. <b>Se você reconhecer a carga como "
        "“pesada”, está errada.</b> Cada repetição sobe o mais rápido "
        "que você conseguir, e <b>quando a barra desacelerar a série acabou</b>, "
        "mesmo faltando repetição no papel. A exceção é o <b>stiff</b>, que fecha "
        "a sessão e não é exercício de velocidade — o verso explica.",
    "aquecimento_titulo": "Aquecimento — obrigatório antes da primeira barra",
    "aquecimento_nota": "Carga leve não dispensa aquecimento: o que machuca aqui "
                        "não é o peso, é a aceleração com o corpo frio.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Agachamento só com o peso do corpo, subida rápida", "2 × 8",
         "do fraco ao forte"],
        ["Barra vazia no padrão de cada exercício", "1 × 5", "antes de pôr peso"],
    ],
    "exercicios": [
        ("Agachamento dinâmico", "desce controlado, <b>sobe explodindo</b>",
         "4 × 3", "2 min", "55%"),
        ("Terra dinâmico", "cada repetição do chão, do zero — ver o verso",
         "4 × 2", "2 min", "60%"),
        ("Push press", "potência acima da cabeça: é onde o ataque acontece",
         "4 × 3", "2 min", "55%"),
        ("Supino explosivo", "empurrar rápido sem travar o cotovelo",
         "4 × 3", "90 s", "45%"),
        ("Remada curvada explosiva", "puxa rápido, solta devagar",
         "4 × 5", "90 s", "50%"),
        ("Stiff (terra romeno)", "<b>este não é de velocidade</b> — desce devagar",
         "3 × 6", "90 s", "60%"),
    ],
    "nota_tabela":
        "Anote a carga de cada exercício, em quilos. Se em alguma série a barra "
        "saiu lenta, <b>pare o exercício ali</b> e marque um <b>X</b>: série lenta "
        "não é para ser insistida, é a informação de que a sessão passou do ponto.",
    "caixa_duracao":
        "<b>Duração prevista: 65 a 75 minutos</b> com o aquecimento. São 82 "
        "repetições — parece pouco perto de um treino de força, e é mesmo: aqui "
        "o que conta não é quanto você fez, é a <b>qualidade de cada repetição</b>. "
        "Se estiver muito mais rápido, a pausa não está sendo respeitada, e é ela "
        "que garante que a quarta série saia tão rápida quanto a primeira.",
    "verso": [
        ("h", "A regra que vale acima de todos os números"),
        ("p", "<b>A velocidade é a prescrição; a carga é só o meio de chegar "
              "nela.</b> Sem 1RM lançado, a carga certa é a mais pesada com que a "
              "subida ainda sai <b>visivelmente explosiva</b> — quando ela começa a "
              "parecer só “forte”, está pesado demais e você desce 5 kg. "
              "Vale para os cinco primeiros; o stiff tem regra própria."),
        ("espaco", 8),
        ("passos", [
            "<b>Sobe rápido, desce controlado.</b> Descer solto não treina nada e "
            "castiga a articulação.",
            "<b>Não trave a articulação no fim.</b> No supino, no push press e na "
            "remada, estalar o cotovelo é o único jeito de se machucar num treino "
            "leve. Pare pouco antes da extensão completa.",
            "<b>Pausa inteira, sempre.</b> Encurtar a pausa transforma potência em "
            "cansaço — e as duas coisas parecem iguais no papel.",
            "<b>Dormiu mal ou acordou com o corpo estranho?</b> Faça só o "
            "agachamento, o supino e a remada, e avise a comissão. Isso não é "
            "frescura: é informação que muda a escalação.",
        ]),
        ("espaco", 10),
        ("h", "Os exercícios que precisam de explicação"),
        ("notas", [
            ("Terra dinâmico", "<b>Cada repetição começa do chão, do zero.</b> Nada "
             "de descer e subir emendado: pousa a barra, solta a tensão, respira e "
             "puxa de novo. Isso é o que treina a saída do chão — que é a parte "
             "lenta do movimento — e é também o que protege a lombar, porque a "
             "repetição emendada com a barra já cansada é onde a coluna arredonda. "
             "São só 2 repetições por série justamente por isso."),
            ("Stiff", "<b>Este não é exercício de potência e não entra na regra da "
             "velocidade.</b> Ele é de descida: no vôlei a cadeia posterior trabalha "
             "mais freando a aterrissagem do que empurrando o salto, e quem só "
             "agacha fica forte para subir e despreparado para cair. Desça contando "
             "<b>3 segundos</b>, barra rente à perna, joelho levemente solto; suba "
             "em ritmo normal. Ele fecha a sessão porque cansa a posterior, e "
             "posterior cansada estraga o terra se vier antes."),
            ("Push press", "A barra sai com um <b>impulso de perna</b> — joelho "
             "dobra uns 10 cm e estende rápido — e o braço termina o movimento. Não "
             "é desenvolvimento lento com ajuda: é a perna jogando a barra para "
             "cima. Glúteo e abdômen apertados; se a lombar arqueia, a carga está "
             "alta demais."),
            ("Terra e stiff na mesma sessão", "Não são repetidos. O terra é do chão "
             "e treina a <b>saída</b>; o stiff tem a perna quase reta e treina a "
             "<b>frenagem</b>, com a posterior esticada. Um é o acelerador, o outro "
             "é o freio — e no vôlei o freio é o que falta na maioria."),
        ]),
        ("espaco", 8),
        ("caixa", "<b>Esta sessão combina com dia de jogo melhor do que a de "
                  "força</b> — carga leve e volume baixo não deixam resíduo. Ainda "
                  "assim, em dia de jogo faça <b>metade das séries</b>, corte o "
                  "stiff e termine pelo menos <b>6 horas antes do apito</b>. A "
                  "pergunta que decide: você saiu da sala com vontade de fazer mais? "
                  "Se saiu ofegante, foi longe demais.",
         AMBAR_CLARO, AMBAR),
        ("espaco", 6),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# REGISTRO DE CARGAS — uma folha por atleta, oito semanas
# ════════════════════════════════════════════════════════════════════════════
# Esta não é uma sessão: é o histórico. A ficha de treino diz o que fazer hoje;
# esta diz o que ele fez nas últimas oito semanas, que é a única coisa capaz de
# responder se ele está progredindo. Oito colunas porque oito semanas é um
# bloco fechado do macrociclo — no fim delas há reteste, e a folha acaba junto.
#
# O que a folha NÃO pede: nada que não seja treino. Sem peso de ninguém a mais
# do que o próprio atleta precisa, sem dado financeiro, sem nada que ele não
# possa deixar em cima do banco da sala.
CINZA_NOTA = "<br/><font size=7.3 color='#5A6672'>%s</font>"
SEMANAS = ["SEM %d<br/>___/___" % i for i in range(1, 9)]

REGISTRO = {
    "arquivo": "ELASE-registro-de-cargas.pdf",
    "layout": montar_registro,
    "meta_titulo": "ELASE - Registro de cargas do atleta",
    "meta_assunto": "Folha individual de cargas e testes, oito semanas",
    "titulo": "Registro de cargas",
    "titulo_verso": "O que fazer com estes números",
    "protocolo": "Uma folha por atleta &nbsp;&middot;&nbsp; oito semanas "
                 "&nbsp;&middot;&nbsp; cargas e testes no mesmo lugar",
    "campos": ["Atleta", "Posição", "Início"],
    "abertura":
        "<b>Esta folha é sua e fica com você.</b> Escreva a <b>maior carga que "
        "você completou com a técnica limpa</b> naquela semana — não a que você "
        "tentou. Uma carga anotada errada para cima vira a sua referência do mês "
        "seguinte, e aí o treino inteiro sai do lugar. <b>No fim das oito "
        "semanas, mande uma foto desta folha para a comissão</b>: é com ela que "
        "a sua progressão é comparada com a do elenco.",
    "matrizes": [
        {
            "titulo": "Cargas — a maior que você completou na semana, em quilos",
            "nota": "Deixe em branco a semana em que não treinou aquele "
                    "exercício. Branco é informação; número inventado não é.",
            "coluna_fixa": "1RM<br/>EST.",
            "colunas": SEMANAS,
            "grupos": [
                ("FORÇA — a carga de trabalho, não o seu máximo", [
                    "Agachamento livre",
                    "Supino reto com barra",
                    "Levantamento terra",
                    "Stiff (terra romeno)",
                    "Desenvolvimento com barra",
                    "Remada curvada com barra",
                    "Barra fixa com carga / puxador",
                    "Hip thrust",
                    "Afundo ou búlgaro" + CINZA_NOTA % "anote as DUAS pernas: E / D",
                ]),
                ("POTÊNCIA — carga leve; o número aqui serve para não subir demais", [
                    "Agachamento dinâmico",
                    "Terra dinâmico",
                    "Push press",
                    "Supino explosivo",
                    "Remada explosiva",
                ]),
                ("O QUE FALTA — escreva o exercício na linha", [
                    "&nbsp;", "&nbsp;", "&nbsp;", "&nbsp;", "&nbsp;",
                ]),
            ],
        },
    ],
    "matrizes_verso": [
        {
            "titulo": "Testes — o que diz se a carga virou salto",
            "nota": "Medidos pela comissão a cada oito semanas, sempre do mesmo "
                    "jeito e de preferência no mesmo horário do dia.",
            "cab_nome": "MEDIDA",
            "larg_nome": 230,
            "colunas": ["RETESTE 1<br/>___/___", "RETESTE 2<br/>___/___",
                        "RETESTE 3<br/>___/___", "RETESTE 4<br/>___/___"],
            "grupos": [
                (None, [
                    "Peso corporal (kg)",
                    "Alcance parado (cm)",
                    "Alcance de ataque (cm)",
                    "Impulsão (cm)",
                    "Salto vertical CMJ (cm)",
                ]),
            ],
            "nota_abaixo":
                "<b>Alcance parado:</b> em pé, braço estendido, sem salto. "
                "<b>Alcance de ataque:</b> com aproximação, ponto mais alto "
                "tocado. <b>Impulsão:</b> a diferença entre os dois — <b>é este o "
                "número que diz se você está saltando mais</b>. <b>CMJ:</b> mãos "
                "na cintura, sem passo.",
        },
    ],
    "verso": [
        ("h", "Quando subir a carga"),
        ("passos", [
            "Suba quando, na <b>última série prescrita</b>, ainda sobrariam 2 "
            "repetições com técnica limpa — e só no exercício em que isso "
            "aconteceu, não em todos de uma vez.",
            "<b>Quanto:</b> 5 kg nos de perna (agachamento, terra, stiff, hip "
            "thrust) e <b>2,5 kg</b> nos de braço (supino, desenvolvimento, "
            "remada). Subir de 10 em 10 é como se perde a técnica.",
            "<b>Duas sessões seguidas sem alcançar a carga da anterior não é "
            "falta de vontade, é fadiga.</b> Desça 10%, refaça essa carga uma "
            "semana e volte a subir dali.",
            "<b>Nunca suba carga e volume na mesma semana.</b> Quando as duas "
            "sobem juntas e algo dói, não há como saber qual das duas foi.",
        ]),
        ("espaco", 8),
        ("h", "O 1RM estimado — para quem nunca fez teste de máximo"),
        ("grade", ["REPETIÇÕES ATÉ PERTO DA FALHA", "MULTIPLIQUE A CARGA POR",
                   "COM 100 KG DÁ"], [
            ["3 repetições", "1,10", "110 kg"],
            ["5 repetições", "1,17", "117 kg"],
            ["7 repetições", "1,23", "123 kg"],
        ], [0.45, 0.3, 0.25]),
        ("espaco", 5),
        ("pq", "<b>Só vale para uma série levada até perto da falha</b> — aquela em "
               "que sobraria no máximo 1 repetição. Nas séries das fichas, que "
               "param com 2 ou 3 de reserva, ela <b>superestima</b>. Não é motivo "
               "para fazer máximo: é só uma referência para a coluna."),
        ("espaco", 9),
        ("h", "O que estes números dizem — e o que não dizem"),
        ("notas", [
            ("Carga subindo e salto parado", "Você ficou mais forte sem ficar mais "
             "rápido — acontece muito. O que falta aí é velocidade, não mais carga: "
             "é para isso que existem as fichas de potência e de pliometria."),
            ("Carga parada por três semanas", "Antes de chamar de platô, olhe sono, "
             "jogos e carga de quadra: força trava por fadiga muito mais vezes do "
             "que por limite."),
            ("Diferença entre as pernas", "No afundo e no búlgaro, anote os dois "
             "lados. Diferença grande e persistente é um dos previsores de lesão "
             "mais consistentes que existem, e só aparece se alguém escrever."),
            ("Peso corporal caindo junto com as cargas", "Procure a comissão. Isso "
             "não é resultado de treino e não se resolve treinando mais."),
        ]),
        ("espaco", 4),
        ("caixa", "<b>Leve esta folha para a sala.</b> Carga que fica na memória "
                  "vira a carga que a gente <i>acha</i> que levantou — e é ela que "
                  "transforma “acho que melhorei” num número."),
        ("espaco", 8),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# PLIOMETRIA — a dose é o contato com o chão
# ════════════════════════════════════════════════════════════════════════════
# A unidade de dose aqui não é série nem repetição: é CONTATO COM O CHÃO. Por
# isso a coluna da carga virou a coluna dos contatos, e o total (96) está na
# folha. O atleta de vôlei já salta centenas de vezes por semana na quadra: a
# pliometria entra por cima disso, e é somando os dois que a tendinopatia
# patelar aparece.
#
# A sessão começa por ATERRISSAGEM e não por salto. Quem se machuca em
# pliometria quase nunca se machuca subindo.
PLIOMETRIA = {
    "arquivo": "ELASE-pliometria.pdf",
    "meta_titulo": "ELASE - Treino de pliometria",
    "meta_assunto": "Pliometria para voleibol, 96 contatos, aterrissagem primeiro",
    "titulo": "Pliometria",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Seis exercícios &nbsp;&middot;&nbsp; 96 contatos com o chão "
                 "&nbsp;&middot;&nbsp; a aterrissagem vem antes do salto",
    "rotulo_carga": "CONTATOS",
    "cab_meio": ["SÉRIES", "PAUSA", "CONTATOS"],
    "larguras": [192, 46, 38, 54],
    "abertura":
        "<b>Aqui a dose não é a carga: é o contato com o chão.</b> Cada vez que o "
        "pé bate no chão é uma dose de impacto, e são <b>96 nesta sessão</b> — "
        "somadas a todas as que você já dá na quadra. Por isso a ordem começa "
        "pela <b>aterrissagem</b>: quem se machuca em pliometria quase nunca se "
        "machuca subindo. <b>Aterrissagem silenciosa, joelho na linha do pé</b>, e "
        "<b>quando o salto baixar ou a queda ficar barulhenta o exercício "
        "acabou</b> — mesmo faltando série.",
    "aquecimento_titulo": "Aquecimento — mais longo que o de sala, e não é opcional",
    "aquecimento_nota": "Saltar com o tendão frio é a forma mais curta de começar "
                        "uma tendinite. Esta parte leva 12 minutos e não se pula.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 min", "a mesma do app"],
        ["Corrida leve e deslocamentos laterais", "4 min", "até suar"],
        ["Agachamento com o peso do corpo, subida rápida", "2 × 8", "sem salto"],
        ["Saltinhos no lugar, bem baixos", "2 × 10", "o corpo entende o ritmo"],
    ],
    "exercicios": [
        ("Aterrissagem do caixote (30 cm)", "desce do caixote e <b>TRAVA</b> — "
         "não é salto, é freio", "3 × 5", "60 s", "15"),
        ("Salto vertical com parada", "salta alto e aterrissa travado, 2 s parado",
         "3 × 5", "90 s", "15"),
        ("Saltinhos de tornozelo (pogo)", "joelho quase reto, contato curto no chão",
         "3 × 10", "60 s", "30"),
        ("Salto sobre barreiras (40 cm)", "pés juntos, o menor tempo possível no chão",
         "3 × 4", "90 s", "12"),
        ("Salto unilateral com parada", "4 em cada perna — aterrissa e segura 2 s",
         "2 × 4 cada", "90 s", "16"),
        ("Aproximação de ataque com salto", "3 passos e salto máximo, sem bola",
         "4 × 2", "2 min", "8"),
    ],
    "nota_tabela":
        "Nas colunas da direita escreva a <b>altura</b> que você usou (caixote, "
        "barreira) e marque um <b>X</b> na série em que o salto baixou ou a "
        "aterrissagem ficou barulhenta — e pare o exercício ali. Salto baixo "
        "repetido não treina potência: treina impacto.",
    "caixa_duracao":
        "<b>Duração prevista: 45 a 55 minutos</b> com o aquecimento. É a sessão "
        "mais curta do conjunto e a que mais exige qualidade: <b>pliometria não é "
        "condicionamento</b>. Se você terminou ofegante e suado, fez de outro "
        "jeito — a pausa estava curta e os saltos saíram baixos.",
    "verso": [
        ("h", "As quatro regras que valem acima dos números"),
        ("passos", [
            "<b>Aterrissagem silenciosa.</b> Barulho é impacto que a articulação "
            "absorveu porque o músculo não absorveu. Caia com joelho e quadril "
            "dobrando, na ponta do pé primeiro e o calcanhar descendo em seguida.",
            "<b>Joelho na linha do pé.</b> Joelho caindo para dentro na aterrissagem "
            "é o mecanismo clássico de lesão de ligamento. Se acontecer, pare a "
            "série: não é questão de força de vontade, é de controle.",
            "<b>Salto baixou, acabou.</b> A pliometria vive da altura e do tempo "
            "curto no chão. Repetição baixa e pesada não é uma versão mais fácil do "
            "exercício — é outro exercício, e esse outro só traz o impacto.",
            "<b>Pausa inteira.</b> 60 a 90 segundos parecem muito para quem não "
            "está ofegante. São exatamente o que permite o salto seguinte sair tão "
            "alto quanto o anterior.",
        ]),
        ("espaco", 9),
        ("h", "Onde esta sessão entra na semana"),
        ("notas", [
            ("Nunca no dia anterior ao jogo", "O cansaço da pliometria não aparece "
             "no mesmo dia: aparece no seguinte, exatamente na perna que você "
             "precisa para saltar."),
            ("Nem no mesmo dia da sessão de força pesada", "E nem depois de um "
             "treino de quadra com muito salto. Se o dia já teve salto, este treino "
             "fica para outro — a quadra conta contatos igual."),
            ("O melhor dia", "Começo da semana, com as pernas descansadas, "
             "<b>antes</b> do treino técnico e não depois. Deixe <b>48 horas</b> "
             "até a próxima sessão de pliometria."),
        ]),
        ("espaco", 9),
        ("h", "Se faltar caixote, barreira ou piso"),
        ("notas", [
            ("Sem caixote", "Um degrau de arquibancada ou um banco firme de 30 a 40 "
             "cm. O que não serve é qualquer coisa que deslize ou balance — e "
             "altura maior não é melhor: acima de 40 cm o que aumenta é o impacto, "
             "não o treino."),
            ("Sem barreiras", "Cones, um elástico preso entre duas cadeiras, ou uma "
             "linha no chão para saltar por cima de um lado para o outro. A altura "
             "importa menos que o tempo curto no chão."),
            ("O piso", "Madeira ou piso de quadra. Em <b>concreto cru, faça metade "
             "dos contatos</b> — 96 saltos no cimento é onde a dor no tendão da "
             "patela começa, e ela leva meses para ir embora."),
        ]),
        ("espaco", 8),
        ("caixa", "<b>Dor no tendão logo abaixo da patela é o sinal de parar</b> — "
                  "principalmente a que aparece no dia seguinte e some ao aquecer, "
                  "que é a que engana. Avise a comissão antes de insistir: "
                  "tendinopatia patelar é a lesão mais comum do voleibol e a mais "
                  "lenta de resolver. E quando for evoluir a sessão, <b>aumente os "
                  "contatos antes de aumentar a altura</b> — nesta ordem, nunca nas "
                  "duas ao mesmo tempo.",
         AMBAR_CLARO, AMBAR),
        ("espaco", 8),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# CONTRASTE — pesado e explosivo no mesmo par, separados pela pausa certa
# ════════════════════════════════════════════════════════════════════════════
# A série pesada deixa o sistema nervoso ligado por alguns minutos, e o salto
# que vem depois sai mais alto do que sairia sozinho. A PAUSA ENTRE OS DOIS é a
# prescrição inteira: cedo demais o atleta pega a fadiga em vez do efeito, tarde
# demais o efeito já passou. Por isso ela ocupa a coluna da pausa com dois
# valores diferentes — depois do pesado e depois do explosivo.
#
# Três decisões que não vieram pedidas:
#
# O STIFF ENTRA DEPOIS DO BLOCO DE SUPINO, não depois dos saltos. Carga alta com
# intenção de velocidade numa dobra de quadril é o exercício de maior risco da
# ficha, e posterior de coxa é o músculo que mais estira no esporte. Com o bloco
# de supino no meio, as pernas chegam nele com 20 minutos de descanso.
#
# UMA PUXADA NO FIM. Supino, flexão e nada puxando é uma sessão inteira à frente
# do corpo — exatamente o que tira a escápula de posição em quem ataca.
#
# O EFEITO DO CONTRASTE É INDIVIDUAL e maior em quem já é forte. A folha diz como
# o atleta percebe se está funcionando, e o que fazer se nunca funcionar.
CONTRASTE = {
    "arquivo": "ELASE-treino-de-contraste.pdf",
    "meta_titulo": "ELASE - Treino de contraste",
    "meta_assunto": "Pares pesado + explosivo, stiff rapido e uma puxada de equilibrio",
    "titulo": "Treino de contraste",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Dois pares pesado + explosivo &nbsp;&middot;&nbsp; stiff rápido "
                 "&nbsp;&middot;&nbsp; a pausa entre os dois é a prescrição",
    "rotulo_carga": "CARGA",
    "numerar": False,
    "larguras": [196, 44, 44, 40],
    "abertura":
        "<b>Cada par é um exercício pesado seguido de um explosivo.</b> A série "
        "pesada deixa o sistema nervoso ligado por alguns minutos, e o salto que "
        "vem depois sai mais alto do que sairia sozinho. <b>O que faz o método "
        "funcionar é a pausa entre os dois:</b> cedo demais você pega a fadiga em "
        "vez do efeito, tarde demais o efeito já passou. A coluna da pausa traz "
        "dois valores — <b>3 min</b> depois do pesado, antes do explosivo, e "
        "<b>2 min 30 s</b> depois do explosivo, antes de recomeçar o par.",
    "aquecimento_titulo": "Aquecimento — e o salto de referência do dia",
    "aquecimento_nota": "O último item não é aquecimento: é a sua régua. Guarde na "
                        "cabeça como foi esse salto — é com ele que você compara "
                        "os saltos de depois do isométrico.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Barra vazia, 55% e 75% no padrão de cada par", "1 × 8, 5 e 3",
         "1 min entre elas"],
        ["<b>3 saltos verticais máximos</b>", "3 saltos", "a sua régua do dia"],
    ],
    "exercicios": [
        ("1A. Isométrico na barra guiada",
         "barra travada, joelho 100–120° — empurra 5 s com <b>tudo</b>",
         "4 × 5 s", "3 min", "máx."),
        ("1B. Agachamento com salto",
         "intenção máxima em cada salto — barra leve ou só o corpo",
         "4 × 4", "2,5 min", "20%"),
        ("2A. Supino partindo do peito",
         "a barra <b>para</b> no peito — nos pinos, ou 2 s com observador",
         "4 × 3", "3 min", "88%"),
        ("2B. Flexão explosiva", "as mãos saem do chão; se não saírem, a mais rápida",
         "4 × 5", "2,5 min", "corpo"),
        ("3. Stiff rápido", "carga alta, 3 repetições, <b>sobe com tudo</b> — "
         "descida controlada", "4 × 3", "2,5 min", "80%"),
        ("4. Remada curvada", "ACRESCENTADA — o contrapeso de supino e flexão",
         "3 × 8", "90 s", "RIR 2"),
    ],
    "nota_tabela":
        "Anote a carga de cada exercício. No <b>1B</b> e no <b>2B</b> marque "
        "também se o salto (ou a flexão) saiu <b>melhor</b> ou <b>pior</b> que o "
        "do aquecimento: é essa marca, e não a carga, que diz se o contraste "
        "funcionou para você naquele dia.",
    "caixa_duracao":
        "<b>Duração prevista: 80 a 90 minutos</b> com o aquecimento — quase tudo "
        "pausa, e aqui a pausa <b>é</b> o treino. <b>Se o tempo apertar, faça 3 "
        "pares em vez de 4</b>; nunca encurte os 3 minutos entre o pesado e o "
        "explosivo, que é o que separa isto de uma sessão de força comum.",
    "verso": [
        ("h", "Um par no relógio"),
        ("grade", ["MOMENTO", "O QUE", "QUANTO", "POR QUÊ"], [
            ["0:00", "Isométrico, empurrando com tudo", "5 s",
             "liga o sistema nervoso"],
            ["0:05", "<b>PAUSA</b>", "3 min",
             "a fadiga some, o efeito fica — é a parte que faz funcionar"],
            ["3:05", "Saltos, intenção máxima", "4 saltos",
             "é aqui que o salto sai mais alto"],
            ["3:15", "Pausa antes de recomeçar o par", "2,5 min",
             "para o próximo isométrico sair inteiro"],
        ], [0.11, 0.33, 0.13, 0.43],
         [("BACKGROUND", (0, 2), (-1, 2), VERDE_CLARO),
          ("BOX", (0, 2), (-1, 2), 1.1, VERDE)]),
        ("espaco", 5),
        ("pq", "Cada par leva uns <b>5 min 45 s</b>. Quatro pares, 23 minutos — e é "
               "assim nos dois blocos."),
        ("espaco", 8),
        ("caixa", "<b>Como saber se o contraste está funcionando em você.</b> O "
                  "salto depois do isométrico tem que parecer <b>melhor</b> que os "
                  "3 saltos do aquecimento. Se parecer pior, a pausa foi curta — "
                  "aumente para 4 ou 5 minutos na próxima série. <b>O efeito é "
                  "individual e aparece mais em quem já é forte:</b> se depois de "
                  "três sessões o salto nunca melhorar, avise a comissão. Para "
                  "você o método não está pagando o tempo que custa, e esse tempo "
                  "rende mais em outra coisa.", VERDE_CLARO, VERDE),
        ("espaco", 8),
        ("h", "Os exercícios, um a um"),
        ("notas", [
            ("Agachamento isométrico", "Barra travada na guiada com o <b>joelho "
             "entre 100 e 120 graus</b> — perto da posição de onde o salto sai, não "
             "lá no fundo. Empurre como se fosse arrancar a barra do lugar, 5 "
             "segundos. Inspire antes e solte o ar no fim; não faça de cabeça baixa."),
            ("Agachamento com salto", "Barra leve ou só o peso do corpo. <b>Se o "
             "salto parecer mais baixo que o normal, tire a barra</b> — carga que "
             "estraga o salto desmonta o método inteiro."),
            ("Supino partindo do peito", "A barra <b>para</b> no peito e sai do "
             "zero: isso tira o efeito elástico e treina a força de partida. Faça "
             "<b>nos pinos do rack</b> na altura do peito, ou com 2 segundos parado "
             "e <b>sempre com alguém observando</b>. A 88% e partindo do zero, "
             "ninguém tira a barra de cima sozinho."),
            ("Stiff rápido", "A 80% a barra não sai rápida de verdade — o que é "
             "rápido é a <b>intenção</b>, e é ela que treina. A <b>descida continua "
             "controlada</b>: stiff solto na descida é como se rompe posterior de "
             "coxa. Ele vem depois do bloco de supino de propósito, para as pernas "
             "chegarem nele com 20 minutos de descanso. Lombar arredondou, acabou."),
            ("Remada curvada", "Não faz parte de nenhum par: está aí porque a "
             "sessão tem supino, flexão e nada puxando. Três séries custam 5 "
             "minutos e evitam que um dia inteiro de empurrar leve o ombro para a "
             "frente — que é como a dor de ombro do atacante começa."),
        ]),
        ("espaco", 6),
        ("caixa", "<b>Sessão neural pesada: 48 horas até a próxima pesada, e não na "
                  "véspera de jogo.</b> O isométrico máximo e o supino a 88% cobram "
                  "do sistema nervoso, e isso aparece no dia seguinte.",
         AMBAR_CLARO, AMBAR),
        ("espaco", 6),
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# CORPO INTEIRO — oito multiarticulares: potência, força e unilateral
# ════════════════════════════════════════════════════════════════════════════
# Força e potência na mesma sessão só funciona com a ordem certa: POTÊNCIA
# PRIMEIRO. Velocidade morre com fadiga, e um push press depois de quatro séries
# de supino a 82% vira um desenvolvimento lento com ajuda de perna — o exercício
# continua no papel e o estímulo some.
#
# O UNILATERAL VEM POR ÚLTIMO porque é o único dos três blocos que continua
# fazendo o trabalho dele cansado: ele não existe para somar carga, existe para
# achar a diferença entre os lados — e é cansado que ela aparece.
#
# A CONTA DOS PADRÕES: 8 séries de empurrar, 10 de puxar e 11 de perna. Em quem
# ataca e bloqueia, puxar um pouco mais do que se empurra é o lado certo para a
# conta pender, e a regra de corte da folha protege as puxadas.
#
# A REMADA ALTA veio pedida e é o exercício de maior risco de ombro da ficha para
# quem ataca. Ela fica, com as regras que reduzem o risco no verso: pegada aberta,
# barra até o esterno, cotovelo nunca acima da linha do ombro, e a troca por face
# pull ao primeiro sinal de pinçamento.
#
# A ELEVAÇÃO PÉLVICA UNILATERAL é a única das oito que não é multiarticular: com o
# joelho dobrado e fixo, é extensão de quadril. Está dito na folha.
#
# Oito multiarticulares com pausa cheia dá quase duas horas, e isso está dito na
# folha com a regra de corte — em vez de prometer 80 minutos e o atleta descobrir
# na metade que não ia dar.
CORPO_INTEIRO = {
    "arquivo": "ELASE-corpo-inteiro-8-multiarticulares.pdf",
    "meta_titulo": "ELASE - Corpo inteiro, oito multiarticulares",
    "meta_assunto": "Potencia, forca e unilateral; empurrar, puxar e perna",
    "titulo": "Corpo inteiro",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Sexta, 09/10 &nbsp;&middot;&nbsp; oito multiarticulares "
                 "&nbsp;&middot;&nbsp; potência, força e unilateral, nesta ordem",
    "rotulo_carga": "CARGA",
    "larguras": [196, 44, 44, 40],
    "abertura":
        "<b>A ordem desta sessão é a prescrição tanto quanto as cargas.</b> "
        "Potência primeiro: velocidade morre com fadiga, e um push press depois do "
        "trabalho pesado de perna vira outro exercício. A força vem no meio, e o "
        "<b>unilateral por último</b> — ele não está ali para somar carga e sim "
        "para <b>achar a diferença entre os seus dois lados</b>. O terra é o mais "
        "pesado do dia e o avanço é o que mais exige equilíbrio: por isso o avanço "
        "vem cedo e o <b>supino entra entre os dois</b>.",
    "aquecimento_titulo": "Aquecimento — antes do primeiro exercício de cada padrão",
    "aquecimento_nota": "O push press é o primeiro da sessão e o mais técnico: o "
                        "ombro precisa chegar nele pronto, não aquecendo nele.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril, ombro e torácica", "6 min",
         "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Rotadores externos com elástico", "2 × 12", "leve, acorda o manguito"],
        ["Barra vazia e 55% no padrão de cada exercício", "1 × 8 e 1 × 5",
         "1 min entre elas"],
    ],
    "exercicios": [
        ("Push press", "potência &middot; empurrar vertical — a perna joga",
         "4 × 3", "2,5 min", "58%"),
        ("Avanço com barra, à frente e atrás", "força &middot; perna — 5 ciclos em CADA perna",
         "4 × 5", "3 min", "RIR 2"),
        ("Supino reto com barra", "força &middot; empurrar horizontal — sobrariam 2 repetições",
         "4 × 5", "2,5 min", "82%"),
        ("Levantamento terra", "força &middot; dobra de quadril — cada repetição do chão",
         "4 × 4", "3 min", "75%"),
        ("Remada alta", "força &middot; ombro — pegada ABERTA, ler o verso antes",
         "3 × 8", "90 s", "RIR 2"),
        ("Puxada unilateral no pulley alto", "unilateral &middot; puxar vertical — 10 em CADA lado",
         "3 × 10", "90 s", "RIR 2"),
        ("Elevação pélvica unilateral", "unilateral &middot; perna — 10 em CADA lado",
         "3 × 10", "90 s", "RIR 2"),
        ("Remada unilateral (serrote)", "unilateral &middot; puxar — 8 em CADA lado",
         "3 × 8", "90 s", "RIR 2"),
    ],
    "nota_tabela":
        "Anote a carga de cada exercício. Nos <b>quatro unilaterais, anote os dois "
        "lados</b> — é a informação desta folha que mais diz sobre risco de lesão.",
    "caixa_duracao":
        "<b>Duração prevista: 95 a 110 minutos</b> — oito multiarticulares com "
        "pausa cheia é sessão longa, e vale saber antes de chegar na metade. "
        "<b>Com menos de 85 minutos:</b> 3 séries em vez de 4 no push press, no "
        "avanço, no supino e no terra. Corte a série, nunca a pausa — e "
        "nunca as puxadas.",
    "verso": [
        ("h", "Por que esta ordem, e não outra"),
        ("grade", ["BLOCO", "O QUE", "POR QUE VEM AQUI"], [
            ["1º", "Potência — push press",
             "velocidade é a primeira coisa que a fadiga leva: com a perna cansada "
             "ele vira um desenvolvimento lento com ajuda de perna"],
            ["2º", "Força — avanço, supino e terra",
             "o avanço é unilateral mas entra aqui porque é exercício de carga, e "
             "vem cedo porque equilíbrio com barra nas costas é o primeiro a piorar "
             "com fadiga. <b>O supino separa o avanço do terra</b>"],
            ["3º", "Ombro e unilateral — remada alta, puxada, elevação pélvica e serrote",
             "carga menor e controle: é o bloco que continua fazendo o trabalho "
             "dele cansado — e é cansado que a diferença entre os lados aparece"],
        ], [0.08, 0.34, 0.58]),
        ("espaco", 4),
        ("caixa", "<b>A conta dos padrões: 8 séries de empurrar, 9 de puxar e 11 "
                  "de perna.</b> Em quem ataca e bloqueia centenas de vezes por "
                  "semana — trabalho que já é todo à frente do corpo — puxar um "
                  "pouco mais do que se empurra é o lado certo para a conta "
                  "pender. <b>Se precisar cortar série, não corte das puxadas.</b>"),
        ("espaco", 4),
        ("h", "Os exercícios"),
        ("notas", [
            ("Push press", "A barra sai com um <b>impulso de perna</b> — joelho "
             "dobra uns 10 cm e estende rápido — e o braço termina. Não é "
             "desenvolvimento lento com ajuda. Se a lombar arqueia para a barra "
             "subir, a carga está alta demais."),
            ("Avanço com barra", "<b>Uma repetição é um passo à frente e um atrás com "
             "a MESMA perna</b>; cinco assim, depois troca. Joelho de trás descendo "
             "em direção ao chão, tronco em pé, passo do tamanho que você controla. "
             "A carga fica perto de um terço do seu agachamento — se precisar olhar "
             "para o chão para não desequilibrar, está pesada. É o exercício que "
             "mais exige equilíbrio da ficha, e por isso vem com a perna descansada."),
            ("Levantamento terra", "<b>Cada repetição começa do chão, do zero</b> — "
             "emendar com a lombar cansada é onde a coluna arredonda. <b>Lombar "
             "arredondou, a série acabou.</b> Está a 75% porque a perna chega nele já "
             "trabalhada pelo avanço."),
            ("Remada alta", "<b>É o exercício de maior risco de ombro desta ficha "
             "para quem ataca</b>, e faz diferença como você faz: pegada na largura "
             "dos ombros ou <b>mais aberta</b>, barra parando na altura do "
             "<b>esterno</b> e não do queixo, e o <b>cotovelo nunca acima da linha "
             "do ombro</b>. Deu dor ou pinçamento, troque por face pull."),
            ("Elevação pélvica unilateral", "Costas apoiadas no banco, <b>um pé no "
             "chão</b> e o outro joelho puxado contra o peito. Sem banco, deitado no "
             "chão. Sobe empurrando pelo <b>calcanhar</b> até o tronco ficar reto, "
             "segura 1 segundo em cima e desce devagar — se a lombar arqueia para "
             "subir mais, você passou do ponto. É a única da ficha que não é "
             "multiarticular: ela está aqui pela extensão de quadril, que é o que "
             "empurra o chão no salto."),
            ("Os três do fim", "<b>Comece pelo lado mais fraco, e o lado bom "
             "para no número que o fraco fez.</b> Na puxada, tronco parado: se o "
             "corpo gira para ajudar, a carga está alta."),
        ]),
        ("espaco", 3),
        ("caixa", "<b>Se você fez o treino de contraste nas últimas 48 horas</b> — "
                  "o do isométrico máximo, saltos e supino a 88% —, mude três "
                  "coisas: <b>avanço em 3 séries</b>, <b>supino a 75%</b> e <b>terra em "
                  "3 séries a 70%</b>. São os mesmos padrões "
                  "pesados duas vezes na mesma semana.", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# TRONCO — cinco exercícios a 4 x 6
# ════════════════════════════════════════════════════════════════════════════
# Os cinco vieram pedidos, e todos ficaram. O que mudou foi a ORDEM: a remada
# alta saiu do meio para o fim (é a de maior risco de ombro de quem ataca) e a
# puxada fechada entrou entre a remada curvada e o stiff — os dois exercícios
# que carregam a lombar. Oito séries de coluna carregada numa sessão só é o
# número que manda nesta ficha, não a dorsal nem o posterior.
TRONCO = {
    "arquivo": "ELASE-tronco-4x6.pdf",
    "meta_titulo": "ELASE - Tronco, cinco exercicios a 4 x 6",
    "meta_assunto": "Um de empurrar, tres de puxar, um de dobra de quadril",
    "titulo": "Tronco",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Quinta, 22/10 &nbsp;&middot;&nbsp; cinco exercícios, todos "
                 "4 × 6 &nbsp;&middot;&nbsp; um de empurrar, três de puxar, um "
                 "de dobra de quadril",
    "rotulo_carga": "CARGA",
    "larguras": [196, 44, 44, 40],
    "abertura":
        "<b>Cinco exercícios no mesmo 4 × 6 — e dois deles seguram a lombar.</b> "
        "A remada curvada é um isométrico de lombar com carga à frente do corpo, e "
        "o stiff é a mesma coluna trabalhando em movimento: <b>oito séries de "
        "coluna carregada numa sessão só</b>. É por isso que a puxada fechada "
        "entra entre os dois, e é por isso que o stiff está a 68% e não a 75%. O "
        "tecido que limita esta ficha não é a dorsal nem o posterior — é a lombar.",
    "aquecimento_titulo": "Aquecimento — antes do primeiro exercício de cada padrão",
    "aquecimento_nota": "O supino abre a sessão e depende de escápula firme: "
                        "manguito e torácica vêm antes dele, não depois.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de torácica, ombro e quadril", "6 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Rotadores externos com elástico", "2 × 12", "leve, acorda o manguito"],
        ["Barra vazia e 55% no padrão de cada exercício", "1 × 8 e 1 × 5",
         "1 min entre elas"],
    ],
    "exercicios": [
        ("Supino reto com barra",
         "força &middot; empurrar horizontal — sobrariam 2 repetições",
         "4 × 6", "2,5 min", "75%"),
        ("Remada curvada com barra",
         "força &middot; puxar horizontal — tronco PARADO, ler o verso",
         "4 × 6", "2,5 min", "RIR 2"),
        ("Puxada fechada no pulley alto",
         "força &middot; puxar vertical — pegada neutra ou supinada",
         "4 × 6", "2 min", "RIR 2"),
        ("Stiff com barra",
         "força &middot; dobra de quadril — excêntrica de 3 s",
         "4 × 6", "2,5 min", "68%"),
        ("Remada alta",
         "força &middot; ombro — pegada ABERTA, ler o verso antes",
         "4 × 6", "90 s", "RIR 2"),
    ],
    "nota_tabela":
        "Anote a carga de cada exercício. Na <b>remada curvada e no stiff, anote "
        "também se a lombar aguentou as quatro séries</b> — é a informação desta "
        "folha que mais decide a próxima. <b>Esta ficha não tem perna, core nem "
        "nada unilateral:</b> nenhum dos cinco acha diferença entre os seus dois "
        "lados, e isso pesa na hora de montar o resto da semana.",
    "caixa_duracao":
        "<b>Duração prevista: 60 a 70 minutos</b> — cinco exercícios, vinte "
        "séries, pausa cheia. <b>Com menos de 50 minutos:</b> 3 séries na puxada "
        "e na remada alta. Corte a série, nunca a pausa — e <b>não corte o stiff "
        "para encaixar mais puxada</b>: ele é a única coisa parecida com perna "
        "que esta ficha tem.",
    "verso": [
        ("h", "Por que a ordem mudou"),
        ("grade", ["", "O QUE", "POR QUE VEM AQUI"], [
            ["1º", "Supino",
             "o único de empurrar, e o que mais precisa de escápula firme. Depois "
             "de três puxadas a base dele já não é a mesma"],
            ["2º", "Remada curvada",
             "a puxada mais pesada e a que mais exige lombar inteira. Vem cedo "
             "por isso"],
            ["3º", "Puxada fechada",
             "<b>está aqui para separar a remada curvada do stiff</b> — é a única "
             "puxada da ficha que não põe carga na coluna"],
            ["4º", "Stiff",
             "a segunda carga de lombar do dia. Vem depois de uma pausa dela, "
             "não colado na primeira"],
            ["5º", "Remada alta",
             "<b>era a 3ª na sua lista.</b> É a de maior risco de ombro da ficha: "
             "vai por último, com carga leve e sem nada depois que ela possa "
             "estragar"],
        ], [0.08, 0.26, 0.66]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 4 séries de empurrar, 12 de puxar, 4 de dobra de "
                  "quadril.</b> Três para um a favor de puxar é o lado certo para "
                  "pender em quem ataca — mas <b>um dia assim corrige, uma semana "
                  "assim só troca o desequilíbrio de lugar</b>. Se o resto da "
                  "semana também puxar, ponha empurrar de volta."),
        ("espaco", 2),
        ("h", "Os exercícios"),
        ("notas", [
            ("Supino a 75%", "Seis a 75% têm de deixar cerca de <b>duas na "
             "reserva</b> — é esse o alvo, não a falha. Se a sexta sobe sozinha, a "
             "carga sobe na próxima; se a quinta já raspa, o 1RM é que está "
             "desatualizado."),
            ("Remada curvada", "<b>Tronco entre 15° e 30° acima da horizontal, e "
             "PARADO.</b> A barra vem ao <b>umbigo</b>, não ao peito. O erro que "
             "todo mundo comete é levantar o tronco para a barra subir — quando "
             "isso acontece a carga está alta demais e o exercício virou meio "
             "levantamento terra. <b>Lombar arredondou, a série acabou.</b>"),
            ("Puxada fechada", "Pegada <b>neutra ou supinada</b>, na largura dos "
             "ombros: para quem ataca, a pronada fechada fecha o espaço do ombro "
             "sem precisar. Puxe até a barra encostar na <b>parte alta do "
             "peito</b>, cotovelo descendo para trás, e volte controlando. "
             "<b>Tronco parado</b> — se o corpo balança, a dorsal parou de "
             "trabalhar e o peso está sendo jogado."),
            ("Stiff a 68%", "Mais leve que o de costume por dois motivos somados: "
             "<b>seis repetições com excêntrica de 3 s</b>, e a lombar chegando "
             "nele com quatro séries de remada curvada atrás. Barra rente à perna, "
             "quadril para trás, joelho quase travado. <b>Desce até onde a lombar "
             "fica reta — nem um centímetro além.</b>"),
            ("Remada alta", "<b>É o exercício de maior risco de ombro desta ficha "
             "para quem ataca</b>, e faz diferença como você faz: pegada na "
             "largura dos ombros ou <b>mais aberta</b>, barra parando na altura do "
             "<b>esterno</b> e não do queixo, e o <b>cotovelo nunca acima da linha "
             "do ombro</b>. Deu dor ou pinçamento, troque por face pull — a ficha "
             "não perde nada."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>Se você fez terra ou agachamento pesado nas últimas 48 "
                  "horas</b>, mude duas coisas: <b>stiff em 3 séries a 60%</b> e "
                  "remada curvada com o peito apoiado no banco inclinado. Remada "
                  "curvada e stiff no mesmo dia já é bastante coluna; <b>somados a "
                  "um terra recente, é bastante demais</b>.", AMBAR_CLARO, AMBAR),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# UNILATERAL E SALTO — sete pedidos e o oitavo por minha conta
# ════════════════════════════════════════════════════════════════════════════
# Os sete cobrem perna unilateral, plano frontal, empurrar vertical, ombro e
# três pliometrias. Deixam de fora puxar, core e DOBRA DE QUADRIL. O oitavo é o
# stiff unilateral porque a falta de posterior não é uma lacuna qualquer nesta
# ficha: são 62 contatos pliométricos, e quem freia aterrissagem é o
# isquiotibial, excentricamente, quase sempre numa perna só.
UNILATERAL_SALTO = {
    "arquivo": "ELASE-unilateral-e-salto.pdf",
    "meta_titulo": "ELASE - Unilateral e salto",
    "meta_assunto": "Plano frontal, unilateral e pliometria; oito exercicios",
    "titulo": "Unilateral e salto",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Sexta, 23/10 &nbsp;&middot;&nbsp; cinco unilaterais e três "
                 "saltos &nbsp;&middot;&nbsp; metade da sessão no plano frontal",
    "rotulo_carga": "CARGA",
    "larguras": [180, 44, 44, 58],
    "abertura":
        "<b>Sete vieram pedidos; o oitavo era meu. Escolhi o stiff unilateral</b>, "
        "e o motivo está na conta: são <b>três exercícios de salto e 62 "
        "contatos</b>, e nenhum exercício de posterior de coxa — que é justamente "
        "quem freia a aterrissagem, numa perna só. Faltava <b>o tecido que os "
        "outros sete mais cobram</b>.",
    "aquecimento_titulo": "Aquecimento — mais longo do que o de costume",
    "aquecimento_nota": "Metade desta ficha acontece no plano frontal, a direção "
                        "que o aquecimento de sala costuma pular: glúteo médio e "
                        "adutor têm de chegar prontos.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e adutor", "6 min",
         "a do app + cossaco"],
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Deslocamento lateral com elástico", "2 × 10 cada",
         "acorda o glúteo médio"],
        ["Saltinhos no lugar e laterais, sem carga", "2 × 10",
         "o tornozelo tem de chegar pronto"],
    ],
    "exercicios": [
        ("Agachamento no banco unilateral",
         "força &middot; perna unilateral — 6 em CADA perna",
         "4 × 6", "2,5 min", "RIR 2"),
        ("Agachamento lateral com barra",
         "força &middot; plano frontal — 6 para CADA lado",
         "3 × 6", "2 min", "RIR 2"),
        ("Desenvolvimento com barra",
         "força &middot; empurrar vertical — SEM perna",
         "4 × 6", "2,5 min", "RIR 2"),
        ("Afundo com salto",
         "pliometria &middot; alternado — 3 de cada perna",
         "3 × 6", "2 min", "sem carga"),
        ("Salto lateral",
         "pliometria &middot; plano frontal — 3 de cada lado",
         "4 × 6", "90 s", "sem carga"),
        ("Agachamento com salto",
         "pliometria &middot; bilateral — sem quicar",
         "4 × 5", "2 min", "sem carga"),
        ("Remada alta",
         "força &middot; ombro — pegada ABERTA, ver o verso",
         "3 × 8", "90 s", "RIR 2"),
        ("Stiff unilateral com halteres",
         "O MISTERIOSO &middot; posterior — 8 em CADA perna",
         "3 × 8", "90 s", "RIR 2"),
    ],
    "nota_tabela":
        "Nada sai por percentual: não existe 1RM honesto de agachamento numa perna "
        "só — tudo por <b>RIR 2</b>. <b>Nos cinco unilaterais, anote os DOIS "
        "lados:</b> é a melhor leitura de assimetria do mês.",
    "caixa_duracao":
        "<b>Duração prevista: 75 a 90 minutos</b> — 28 séries, e unilateral vale "
        "por dois em tempo de sala. <b>Com menos de 65 minutos:</b> agachamento "
        "lateral em 2 séries e salto lateral em 3. Nunca corte a pausa, nem o "
        "stiff.",
    "verso": [
        ("h", "O oitavo, e por que esse"),
        ("caixa", "<b>Stiff unilateral com halteres.</b> Os sete deixam de fora "
                  "puxar, core e dobra de quadril — e a dobra de quadril é a única "
                  "falta que esta ficha <b>cria</b> em vez de só não cobrir: são "
                  "62 aterrissagens, e aterrissagem é posterior de coxa trabalhando "
                  "ao contrário. <b>Perderam para ele:</b> remada unilateral e "
                  "prancha lateral — nenhuma devolve o que os saltos tiram.",
         VERDE_CLARO, VERDE),
        ("espaco", 2),
        ("caixa", "<b>21 séries de perna, 4 de empurrar, 3 de ombro e ZERO de "
                  "puxar.</b> Isto não é corpo inteiro: é um dia de perna com dois "
                  "exercícios de ombro no meio, e tudo bem que seja. O zero é que "
                  "não pode passar batido — a remada alta <b>eleva</b> a escápula, "
                  "não a retrai. <b>O próximo dia de sala precisa ter puxada.</b>"),
        ("caixa", "<b>62 contatos pliométricos num dia só.</b> O sistema reparte "
                  "entre 45 e 140 na SEMANA INTEIRA, conforme o bloco: esta ficha "
                  "gasta de 44% a 138% de uma semana num treino. <b>Com quadra "
                  "pesada no mesmo dia ou no seguinte, salto lateral em 2 "
                  "séries</b> — é o que tem mais contato por série.",
         AMBAR_CLARO, AMBAR),
        ("espaco", 2),
        ("h", "Os exercícios"),
        ("notas", [
            ("Agachamento no banco unilateral", "Pé de apoio chapado, o outro à "
             "frente sem tocar o chão. <b>Senta no banco, não cai nele</b> — toca e "
             "sobe sem largar o peso. A altura certa é a maior que você controla com "
             "o joelho apontando para o segundo dedo. <b>Comece pela perna mais "
             "fraca; o lado bom para no número que o fraco fez.</b>"),
            ("Agachamento lateral com barra", "Pés bem afastados e apontados à "
             "frente. Desce sobre UMA perna com a outra estendida, <b>os dois "
             "calcanhares no chão</b>: se o calcanhar levanta, feche a abertura antes "
             "de diminuir a profundidade. Barra leve — o limite é amplitude."),
            ("Desenvolvimento com barra", "<b>Sem impulso de perna:</b> se o joelho "
             "dobra, virou push press e é outro exercício. Glúteo e abdômen "
             "apertados para a lombar não arquear; a barra passa rente ao rosto e a "
             "cabeça <b>atravessa</b> para a frente dos braços no fim."),
            ("Os três saltos", "<b>Afundo:</b> troca de perna no ar, joelho de "
             "trás descendo sem bater. <b>Lateral:</b> impulsiona numa perna, "
             "aterrissa na outra e <b>para 1 segundo</b> antes de voltar — é o "
             "salto mais parecido com um bloqueio deslocando. <b>Agachamento:</b> "
             "aterrissa, estabiliza e recomeça, sem quicar. Nos três, o <b>joelho "
             "não entra para dentro</b>, e aterrissagem que faz barulho é série "
             "que acabou."),
            ("Remada alta", "<b>O maior risco de ombro desta ficha para quem "
             "ataca</b> — e ficou em 7º, não em 4º como foi listada: assim os três "
             "saltos a separam do desenvolvimento, e o ombro não faz dois "
             "exercícios acima da cabeça colados. Pegada na largura dos ombros ou "
             "<b>mais aberta</b>, barra parando no <b>esterno</b>, <b>cotovelo "
             "nunca acima da linha do ombro</b>. Deu dor, troque por face pull."),
            ("Stiff unilateral — o misterioso", "Em pé numa perna, halteres à "
             "frente, quadril para trás, perna livre estendendo atrás como "
             "contrapeso: <b>tronco e perna de trás formam uma linha</b>. Desce até "
             "onde a lombar fica reta e volta apertando o glúteo. Aqui se erra mais "
             "por amplitude demais do que por carga demais."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>Com jogo nas próximas 48 horas, esta não é a ficha da "
                  "véspera:</b> 21 séries de perna e 62 contatos pedem dois dias "
                  "para sair. A versão de véspera é só o agachamento com salto, "
                  "3 × 3, e o stiff em 2 séries leves.", AMBAR_CLARO, AMBAR),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# FORÇA PURA A e B — 4 x 4, última série até a falha
# ════════════════════════════════════════════════════════════════════════════
# Os sete exercícios vieram agrupados com um ponto depois de "stiff". Uma troca
# só — stiff por remada alta — desfaz dois encontros ruins: terra e stiff na
# mesma sessão (duas dobras de quadril pesadas até a falha) e remada alta colada
# no desenvolvimento (dois exercícios acima da cabeça seguidos).
FALHA_TECNICA = (
    "<b>Falha técnica, não falha muscular.</b> A série acaba na primeira "
    "repetição em que a barra desacelera visivelmente ou a lombar sai da posição "
    "— não quando o peso para de subir. Em barra pesada sobre a coluna, a última "
    "repetição que você <i>consegue</i> fazer costuma ser a primeira que você "
    "não devia ter feito.")

FORCA_4X4_A = {
    "arquivo": "ELASE-forca-pura-A.pdf",
    "meta_titulo": "ELASE - Forca pura A, 4 x 4",
    "meta_assunto": "Terra, supino, barra fixa e remada alta; ultima serie ate a falha",
    "titulo": "Força pura · A",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Primeiro de dois &nbsp;&middot;&nbsp; quatro multiarticulares, "
                 "todos 4 × 4 &nbsp;&middot;&nbsp; a última série vai até a falha",
    "rotulo_carga": "CARGA",
    "larguras": [206, 44, 44, 40],
    "abertura":
        "<b>Quatro repetições é território de força pura: a carga manda e a "
        "técnica é o freio.</b> As três primeiras séries saem com a quarta "
        "repetição difícil mas limpa; <b>só na quarta série você vai até o fim</b> "
        "— e “fim” quer dizer coisas diferentes em cada exercício, que é "
        "o que o verso explica. No terra, fim é a lombar; no supino e na barra "
        "fixa, é o músculo.",
    "aquecimento_titulo": "Aquecimento — rampa de carga, não alongamento",
    "aquecimento_nota": "A 87% não existe primeira série fria. A rampa não é "
                        "aquecimento: é parte do exercício.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de quadril, torácica e ombro", "6 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Rotadores externos com elástico", "2 × 12", "antes do supino"],
        ["Rampa: 40%, 60%, 75% e 85% do 1º exercício", "5, 3, 2 e 1", "2 min entre elas"],
    ],
    "exercicios": [
        ("Levantamento terra",
         "força pura &middot; dobra de quadril — falha TÉCNICA",
         "4 × 4", "3 min", "4RM"),
        ("Supino reto com barra",
         "força pura &middot; empurrar horizontal — com ajudante",
         "4 × 4", "3 min", "87%"),
        ("Barra fixa com carga",
         "força pura &middot; puxar vertical — carga pendurada",
         "4 × 4", "2,5 min", "4RM"),
        ("Remada alta",
         "força &middot; ombro — ler o verso antes de carregar",
         "4 × 4", "2 min", "4RM"),
    ],
    "nota_tabela":
        "Só o supino sai por percentual: terra, barra fixa e remada alta ainda não "
        "têm 1RM no sistema, então a carga deles é o <b>4RM</b> — aquela em que a "
        "quarta repetição sai e a quinta não. <b>Anote o que você usou e quantas "
        "repetições saíram na última série</b>: é esse número que decide a carga "
        "da próxima vez.",
    "caixa_duracao":
        "<b>Duração prevista: 65 a 75 minutos</b> — 16 séries só, mas com pausa de "
        "3 minutos, que a 87% não é luxo: é o que permite a série seguinte existir. "
        "<b>Com menos de 55 minutos:</b> corte a remada alta inteira. Nunca corte "
        "a pausa.",
    "verso": [
        ("h", "O que “falhar” quer dizer em cada um"),
        ("grade", ["EXERCÍCIO", "ATÉ ONDE IR NA ÚLTIMA SÉRIE"], [
            ["Levantamento terra",
             "<b>Falha técnica.</b> A série acaba quando a barra desacelera ou a "
             "lombar arredonda — mesmo que ainda houvesse força. Cada repetição "
             "começa parada no chão"],
            ["Supino reto com barra",
             "<b>Falha muscular, com alguém na barra.</b> É o único da ficha em "
             "que falhar é seguro, e só com ajudante. Sozinho, pare em 1 de sobra"],
            ["Barra fixa com carga",
             "<b>Falha muscular.</b> Falhar aqui custa descer do apoio. Sem queixo "
             "passando a barra, a repetição não conta"],
            ["Remada alta",
             "<b>Falha técnica, e ela chega cedo:</b> a série acaba no primeiro "
             "cotovelo que passa da linha do ombro"],
        ], [0.27, 0.73]),
        ("espaco", 3),
        ("caixa", FALHA_TECNICA, AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Levantamento terra", "<b>Cada repetição começa do chão, do zero.</b> "
             "Emendar com a lombar cansada é onde a coluna arredonda. A 4 "
             "repetições a carga é próxima do seu máximo — é o exercício da ficha "
             "em que parar cedo custa menos do que parar tarde."),
            ("Supino reto com barra", "87% e quatro repetições. <b>Com alguém na "
             "barra</b> — essa é a condição para a quarta série ir até o fim; sem "
             "ajudante, termine com uma repetição de sobra e anote isso."),
            ("Barra fixa com carga", "Pendure a carga no cinto. <b>Queixo passando "
             "a barra</b>, descida controlada até o cotovelo estender. Se quatro "
             "repetições com carga ainda não saem, faça só com o peso do corpo e "
             "anote quantas foram."),
            ("Remada alta", "<b>O maior risco de ombro das duas fichas, e a quatro "
             "repetições é a versão mais pesada dele.</b> Pegada na largura dos "
             "ombros ou mais aberta, barra parando no <b>esterno</b>, "
             "<b>cotovelo nunca acima da linha do ombro</b>."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>Se a remada alta a 4 repetições incomodar o ombro, não "
                  "insista:</b> troque por <b>4 × 8 com 2 repetições de sobra</b>, "
                  "ou por face pull. Força pura no ombro não compra salto nenhum — "
                  "compra só risco em quem ataca centenas de bolas por semana.",
         VERDE_CLARO, VERDE),
        ("espaco", 2),
    ],
}

FORCA_4X4_B = {
    "arquivo": "ELASE-forca-pura-B.pdf",
    "meta_titulo": "ELASE - Forca pura B, 4 x 4",
    "meta_assunto": "Agachamento, desenvolvimento e stiff; ultima serie ate a falha",
    "titulo": "Força pura · B",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Segundo de dois &nbsp;&middot;&nbsp; três multiarticulares, "
                 "todos 4 × 4 &nbsp;&middot;&nbsp; a última série vai até a falha",
    "rotulo_carga": "CARGA",
    "larguras": [206, 44, 44, 40],
    "abertura":
        "<b>Três exercícios, doze séries, e nenhuma delas barata.</b> Esta é a "
        "sessão mais curta das duas e a mais pesada por série: agachamento e stiff "
        "carregam a mesma coluna, e o desenvolvimento entra entre eles de "
        "propósito, para a lombar ter uma pausa de verdade antes do segundo turno. "
        "<b>Em dois dos três, falhar é parar na técnica, não no músculo.</b>",
    "aquecimento_titulo": "Aquecimento — rampa de carga, não alongamento",
    "aquecimento_nota": "A 87% não existe primeira série fria. A rampa não é "
                        "aquecimento: é parte do exercício.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e torácica", "6 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Agachamento profundo sustentado", "3 × 30 s", "abre o fundo do agachamento"],
        ["Rampa: 40%, 60%, 75% e 85% do agachamento", "5, 3, 2 e 1", "2 min entre elas"],
    ],
    "exercicios": [
        ("Agachamento",
         "força pura &middot; perna — falha TÉCNICA",
         "4 × 4", "3 min", "87%"),
        ("Desenvolvimento com barra",
         "força pura &middot; empurrar vertical — SEM perna",
         "4 × 4", "2,5 min", "4RM"),
        ("Stiff com barra",
         "força pura &middot; dobra de quadril — sem tempo lento",
         "4 × 4", "3 min", "87%"),
    ],
    "nota_tabela":
        "Agachamento e stiff saem do seu 1RM; o desenvolvimento ainda não tem "
        "referência no sistema, então vai pelo <b>4RM</b> — a carga em que a quarta "
        "repetição sai e a quinta não. <b>Anote quantas repetições saíram na última "
        "série de cada um.</b>",
    "caixa_duracao":
        "<b>Duração prevista: 55 a 65 minutos</b> — doze séries com 3 minutos de "
        "pausa. Parece pouco tempo de sala para o quanto cansa, e é mesmo: a conta "
        "aqui não é de volume, é de carga. <b>Não encha a sessão com acessório</b> "
        "— o que sobra de energia depois do stiff é o que vai faltar no treino "
        "seguinte.",
    "verso": [
        ("h", "O que “falhar” quer dizer em cada um"),
        ("grade", ["EXERCÍCIO", "ATÉ ONDE IR NA ÚLTIMA SÉRIE"], [
            ["Agachamento",
             "<b>Falha técnica.</b> A série acaba quando a subida desacelera ou o "
             "tronco cai à frente. Com barra nas costas, falhar de verdade é "
             "despejar a barra — e isso não é treino, é acidente"],
            ["Desenvolvimento com barra",
             "<b>Falha muscular.</b> Dá para falhar com segurança, desde que a "
             "barra tenha onde ser apoiada. Se o joelho dobrar para ajudar, a "
             "série já tinha acabado"],
            ["Stiff com barra",
             "<b>Falha técnica, e é a mais cedo das três:</b> a série acaba na "
             "primeira repetição em que a lombar sai da posição, mesmo que a barra "
             "ainda suba"],
        ], [0.27, 0.73]),
        ("espaco", 3),
        ("caixa", FALHA_TECNICA, AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Agachamento", "87% e quatro repetições, dentro do rack com os pinos "
             "na altura certa. Profundidade: a mesma de sempre — <b>encurtar a "
             "descida para subir mais peso não é progresso</b>, é outro exercício."),
            ("Desenvolvimento com barra", "<b>Sem impulso de perna:</b> se o joelho "
             "dobra, virou push press. Glúteo e abdômen apertados para a lombar não "
             "arquear; a barra passa rente ao rosto e a cabeça atravessa para a "
             "frente dos braços no fim."),
            ("Stiff com barra", "<b>Sem excêntrica lenta aqui.</b> Nas outras "
             "fichas o stiff vem com descida de 3 s; a 87% e quatro repetições, "
             "somar tempo sob tensão é somar risco de lombar sem somar força. "
             "Barra rente à perna, quadril para trás, <b>desce só até onde a "
             "lombar fica reta</b>."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>Por que o stiff ficou aqui e não com o terra.</b> Na lista "
                  "que você mandou, terra e stiff caíam na mesma sessão — duas "
                  "dobras de quadril pesadas até a falha, no mesmo dia, na mesma "
                  "lombar. Trocando stiff por remada alta entre as duas fichas, "
                  "cada sessão fica com <b>uma</b> dobra de quadril, e a remada "
                  "alta sai de perto do desenvolvimento. Foi a única mudança.",
         VERDE_CLARO, VERDE),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# REGENERATIVO — corpo inteiro a 70%, seis exercícios
# ════════════════════════════════════════════════════════════════════════════
# A 70% do 1RM dá para fazer umas doze repetições. Fazendo seis, sobra metade —
# e é essa sobra que faz a sessão regenerar em vez de cobrar. O que cansa não é
# o percentual: é a distância até a falha, e aqui ela é enorme de propósito.
REGENERATIVO = {
    "arquivo": "ELASE-regenerativo-70.pdf",
    "meta_titulo": "ELASE - Treino regenerativo a 70%",
    "meta_assunto": "Seis exercicios, corpo inteiro, longe da falha",
    "titulo": "Regenerativo",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Seis exercícios &nbsp;&middot;&nbsp; corpo inteiro a 70% do 1RM "
                 "&nbsp;&middot;&nbsp; nenhuma série perto da falha",
    "rotulo_carga": "CARGA",
    "larguras": [206, 44, 44, 40],
    "abertura":
        "<b>70% do seu 1RM — o número que já está na sua tabela de cargas.</b> A "
        "essa carga você faria umas doze repetições; aqui você faz seis. "
        "<b>Metade sobra, e a sobra é o treino</b>: o que cansa não é o percentual, "
        "é a distância até a falha. Se alguma série ficar difícil, a carga está "
        "errada para hoje — baixe, não insista.",
    "aquecimento_titulo": "Aquecimento — curto, porque a sessão inteira já é leve",
    "aquecimento_nota": "Sem rampa de carga: a primeira série já é a carga de "
                        "trabalho, e ela é leve.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou esteira, ritmo leve", "6 min", "até suar, sem cansar"],
        ["Mobilidade de quadril, torácica e ombro", "5 min", "a mesma do app"],
        ["Barra vazia no padrão de cada exercício", "1 × 8", "sem pausa entre elas"],
    ],
    "exercicios": [
        ("Agachamento", "perna &middot; a profundidade de sempre",
         "3 × 6", "90 s", "70%"),
        ("Supino reto com barra", "empurrar horizontal",
         "3 × 6", "90 s", "70%"),
        ("Remada curvada com barra", "puxar horizontal &middot; tronco parado",
         "3 × 6", "90 s", "70%"),
        ("Stiff com barra", "dobra de quadril &middot; SEM excêntrica lenta",
         "3 × 6", "90 s", "70%"),
        ("Desenvolvimento com barra", "empurrar vertical &middot; sem perna",
         "3 × 6", "90 s", "70%"),
        ("Puxada fechada no pulley alto", "puxar vertical &middot; pegada neutra",
         "3 × 6", "90 s", "70%"),
    ],
    "nota_tabela":
        "Cinco dos seis saem direto da sua tabela de 1RM. Só o <b>desenvolvimento</b> "
        "ainda não tem referência no sistema: nele, use <b>70% da carga que você "
        "usaria para 6 repetições difíceis</b>. Anote tudo — carga leve registrada "
        "é o que prova que a semana foi leve de verdade.",
    "caixa_duracao":
        "<b>Duração prevista: 45 a 50 minutos</b> — 18 séries leves com pausa curta. "
        "Esta é a única ficha em que <b>passar do tempo é sinal de que algo saiu "
        "errado</b>: se você está descansando mais, a carga está pesada demais "
        "para o que esta sessão deveria ser.",
    "verso": [
        ("h", "Como saber se foi regenerativo mesmo"),
        ("caixa", "<b>A prova é amanhã, não hoje.</b> Se você acordar com dor "
                  "muscular nova, esta sessão não regenerou nada — ela treinou, e "
                  "no dia errado. Da próxima vez, 60% em vez de 70%. "
                  "<b>Sessão regenerativa que deixa marca não é regenerativa, é "
                  "uma sessão leve mal dosada.</b>", VERDE_CLARO, VERDE),
        ("espaco", 3),
        ("h", "As três regras"),
        ("grade", ["", "A REGRA", "POR QUÊ"], [
            ["1", "<b>Nenhuma série perto da falha</b>",
             "a sexta repetição tem de parecer a segunda. Se a última custar, "
             "baixe a carga na série seguinte — sem esperar o fim da sessão"],
            ["2", "<b>Sem excêntrica lenta, sem pausa no fundo</b>",
             "tempo sob tensão é justamente o que produz dor muscular, e dor "
             "muscular é o oposto do que se foi buscar aqui"],
            ["3", "<b>Sem acessório, sem “só mais uma”</b>",
             "seis exercícios cobrem o corpo inteiro: perna, empurrar e puxar nas "
             "duas direções, e a dobra de quadril. O que sobra de vontade é para "
             "o treino de força"],
        ], [0.06, 0.32, 0.62]),
        ("espaco", 3),
        ("h", "Quando usar esta ficha"),
        ("caixa", "No dia seguinte a um treino pesado, entre as duas sessões de "
                  "força pura, ou numa semana de jogo em que a sala não pode somar "
                  "fadiga. <b>Ela não substitui o descanso</b> — substitui o dia "
                  "parado para quem fica pior parado do que se movendo."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# FORÇA PURA 2 A 3 — cinco exercícios, pausa de 2 min
# ════════════════════════════════════════════════════════════════════════════
# A pausa é que define esta ficha. Duas a três repetições MÁXIMAS pedem 93 a 95%
# e 3 a 5 min de pausa; com 2 min, a 3ª e a 4ª série despencam. A 88% dá para
# fazer cinco repetições, então duas ou três saem rápidas e com reserva — e aí
# dois minutos bastam. A ordem é a que ele mandou, sem troca.
FORCA_2A3 = {
    "arquivo": "ELASE-forca-pura-2a3.pdf",
    "meta_titulo": "ELASE - Forca pura, 2 a 3 repeticoes",
    "meta_assunto": "Cinco exercicios a 88%, pausa de 2 minutos",
    "titulo": "Força pura · 2 a 3",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Cinco exercícios &nbsp;&middot;&nbsp; 4 × 2-3 repetições "
                 "&nbsp;&middot;&nbsp; 2 minutos de pausa em todos",
    "rotulo_carga": "CARGA",
    "larguras": [206, 44, 44, 40],
    "abertura":
        "<b>Duas ou três repetições rápidas, com sobra — não duas ou três no "
        "limite.</b> A diferença está na pausa: dois minutos. Repetição máxima a "
        "93% pede de 3 a 5 minutos para a série seguinte existir, e com 2 minutos "
        "a terceira e a quarta despencariam. A 88% a barra sobe rápida nas quatro "
        "séries, que é exatamente o que esta sessão vai buscar: <b>velocidade "
        "sob carga alta</b>, não o máximo do dia.",
    "aquecimento_titulo": "Aquecimento — a rampa é parte do exercício",
    "aquecimento_nota": "A 88% não existe primeira série fria. A rampa sobe até "
                        "perto da carga e para: nada de série extra de 10.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Mobilidade de torácica, ombro e quadril", "6 min", "a mesma do app"],
        ["Rotadores externos com elástico", "2 × 12", "antes do supino"],
        ["Rampa: 40%, 60%, 75% e 85%", "5, 3, 2 e 1", "2 min entre elas"],
    ],
    "exercicios": [
        ("Supino reto com barra", "força pura &middot; empurrar horizontal",
         "4 × 2-3", "2 min", "88%"),
        ("Agachamento", "força pura &middot; perna — a profundidade de sempre",
         "4 × 2-3", "2 min", "88%"),
        ("Puxada fechada sentado", "força pura &middot; puxar vertical — tronco parado",
         "4 × 2-3", "2 min", "88%"),
        ("Desenvolvimento com barra", "força pura &middot; empurrar vertical — SEM perna",
         "4 × 2-3", "2 min", "5RM"),
        ("Remada alta com barra", "força &middot; ombro — a técnica trava a carga",
         "4 × 2-3", "2 min", "5RM"),
    ],
    "nota_tabela":
        "Supino, agachamento e puxada fechada saem do seu 1RM. Desenvolvimento e "
        "remada alta ainda não têm referência no sistema: neles use a "
        "<b>carga de 5 repetições</b> e faça 2 ou 3 — sobra o mesmo tanto. "
        "<b>Anote quantas repetições saíram em cada série</b>; três em todas as "
        "quatro é sinal de subir a carga na próxima.",
    "caixa_duracao":
        "<b>Duração prevista: 55 a 65 minutos</b> — 20 séries e no máximo 60 "
        "repetições no total. É pouca repetição e muito peso, e o relógio engana: "
        "<b>o que cansa aqui não aparece na sala, aparece no dia seguinte.</b> Não "
        "acrescente acessório.",
    "verso": [
        ("h", "O que esta ficha é, e o que ela não é"),
        ("grade", ["", "CARGA", "REPETIÇÕES", "PAUSA"], [
            ["<b>Esta ficha</b>",
             "<b>88%</b> — dá para fazer 5",
             "<b>2 ou 3</b>, sobrando 2 ou 3",
             "<b>2 min</b> bastam"],
            ["Força máxima de verdade",
             "93 a 95%",
             "2 ou 3 no limite",
             "3 a 5 min, sem desconto"],
        ], [0.26, 0.26, 0.26, 0.22]),
        ("espaco", 3),
        ("caixa", "<b>Por que a pausa decide a carga, e não o contrário.</b> "
                  "Depois de uma série pesada, o que repõe a energia da próxima "
                  "leva de 3 a 5 minutos. Com 2 minutos, a reposição fica pela "
                  "metade — e a 93% isso aparece na terceira série como repetição "
                  "perdida. A 88% não aparece, porque havia reserva. "
                  "<b>Se você quiser as 2-3 repetições no limite, a pausa tem de "
                  "ir para 3 minutos; mantendo 2, a carga fica em 88%.</b> As duas "
                  "coisas juntas é que não funcionam.", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Supino e agachamento", "<b>Os dois a 88%, e os dois com o rack "
             "montado.</b> A barra tem de subir rápida: se a segunda repetição já "
             "sai lenta, a carga passou do ponto desta ficha. No agachamento, a "
             "profundidade é a de sempre — encurtar a descida para somar peso é "
             "outro exercício, não progresso."),
            ("Puxada fechada sentado", "Pegada <b>neutra ou supinada</b> na largura "
             "dos ombros. Puxe até a barra encostar na <b>parte alta do peito</b>, "
             "cotovelo descendo para trás, e volte controlando. <b>Tronco "
             "parado</b>: a 88% a tentação de jogar o corpo para trás é grande, e "
             "aí a dorsal parou de trabalhar."),
            ("Desenvolvimento com barra", "<b>Sem impulso de perna:</b> se o joelho "
             "dobra, virou push press e a carga não é mais essa. Glúteo e abdômen "
             "apertados para a lombar não arquear; a barra passa rente ao rosto e "
             "a cabeça atravessa para a frente dos braços no fim."),
            ("Remada alta com barra", "Aqui <b>quem trava a carga é a técnica, não "
             "a força</b>: pegada na largura dos ombros ou mais aberta, barra "
             "parando no <b>esterno</b>, <b>cotovelo nunca acima da linha do "
             "ombro</b>. Com essa regra o peso que sobe é menor do que você "
             "aguentaria — e é assim mesmo. Deu dor ou pinçamento, troque por "
             "face pull."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 8 séries de empurrar, 4 de puxar vertical, 4 de "
                  "ombro e 4 de perna.</b> A ficha pende para o lado de empurrar, "
                  "e o desenvolvimento vem colado na remada alta — dois exercícios "
                  "de ombro seguidos, no fim da sessão. Mantive a ordem que você "
                  "mandou; se quiser separar os dois, a puxada fechada passa para "
                  "o 4º lugar e resolve."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# QUADRIL E PLANO FRONTAL — sete exercícios
# ════════════════════════════════════════════════════════════════════════════
# Três vieram sem prescrição (stiff na polia, rotação de tronco e hang clean) e
# dois são quase o mesmo exercício: agachamento lateral com e sem banco. A ordem
# é a dele. O que a ficha acrescenta é (a) prescrição para os três que faltavam,
# (b) uma diferença de execução que faz os dois últimos valerem como dois, e
# (c) a conta dos 52 contatos, todos no mesmo plano.
QUADRIL_FRONTAL = {
    "arquivo": "ELASE-quadril-plano-frontal.pdf",
    "meta_titulo": "ELASE - Quadril e plano frontal",
    "meta_assunto": "Preparacao, hang clean, forca pura e saltos laterais",
    "titulo": "Quadril e plano frontal",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Sete exercícios &nbsp;&middot;&nbsp; preparação, neuromuscular, "
                 "força pura e salto &nbsp;&middot;&nbsp; nesta ordem",
    "rotulo_carga": "CARGA",
    "larguras": [186, 48, 44, 58],
    "abertura":
        "<b>A sessão tem três blocos e eles estão na ordem certa.</b> Os dois "
        "primeiros exercícios são leves de propósito: na polia, eles acordam a "
        "dobra de quadril e o tronco <b>antes</b> do hang clean, que é o mais "
        "técnico do dia e o que mais precisa de corpo pronto. Depois vem a força "
        "pura, e no fim o plano frontal. <b>Nada aqui empurra</b> — é um dia de "
        "quadril, tronco e lateral.",
    "aquecimento_titulo": "Aquecimento — antes dos dois da polia",
    "aquecimento_nota": "Os dois primeiros exercícios já são preparação. Isto aqui "
                        "é o que vem antes deles.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Mobilidade de tornozelo, quadril e torácica", "6 min", "a mesma do app"],
        ["Deslocamento lateral com elástico", "2 × 10 cada", "acorda o glúteo médio"],
        ["Barra vazia no padrão do hang clean", "2 × 5", "antes de carregar"],
    ],
    "exercicios": [
        ("Stiff unilateral na polia",
         "preparação &middot; 8 em CADA perna",
         "3 × 8", "60 s", "RIR 4"),
        ("Rotação de tronco na bola com polia",
         "preparação &middot; tronco — 10 de CADA lado",
         "3 × 10", "60 s", "RIR 4"),
        ("Hang clean",
         "neuromuscular &middot; LPO — a barra decide",
         "5 × 3", "2,5 min", "72%"),
        ("Remada curvada com barra",
         "força pura &middot; puxar — tronco PARADO",
         "4 × 3", "2,5 min", "88%"),
        ("Elevação pélvica",
         "força pura &middot; extensão de quadril",
         "4 × 3", "2,5 min", "5RM"),
        ("Agachamento lateral no banco",
         "potência &middot; plano frontal — com salto lateral",
         "4 × 6-8", "2 min", "sem carga"),
        ("Agachamento lateral com salto",
         "coordenação &middot; plano frontal — sem banco",
         "4 × 6", "90 s", "sem carga"),
    ],
    "nota_tabela":
        "O hang clean sai de <b>72% do seu 1RM de clean</b> e a remada curvada de "
        "88% do dela — as duas já estão na sua tabela de cargas. A elevação "
        "pélvica ainda não tem referência: use a <b>carga de 5 repetições</b> e "
        "faça 3. <b>No stiff unilateral, anote os dois lados.</b> Nos dois "
        "últimos, anote quantos saltos saíram limpos, não quantos você fez.",
    "caixa_duracao":
        "<b>Duração prevista: 70 a 85 minutos</b> — 27 séries em três blocos "
        "bem diferentes. <b>Com menos de 60 minutos:</b> corte o agachamento "
        "lateral sem banco para 2 séries — é o que mais repete o que já foi "
        "feito no exercício anterior. Nunca corte o hang clean nem a pausa dele.",
    "verso": [
        ("h", "Os três blocos, e por que nessa ordem"),
        ("grade", ["", "O QUE", "POR QUE AQUI"], [
            ["1º", "<b>Polia</b> — stiff unilateral e rotação de tronco",
             "leves de propósito. Acordam a dobra de quadril e o tronco antes do "
             "exercício mais técnico do dia, em vez de somar cansaço"],
            ["2º", "<b>Hang clean</b>",
             "o mais neural e o mais técnico: velocidade de barra morre com "
             "fadiga, então ele vem antes da força pura, não depois"],
            ["3º", "<b>Força pura</b> — remada curvada e elevação pélvica",
             "4 × 3 a 88%. Carga alta com poucas repetições cansa pouco em "
             "volume e muito em sistema nervoso — daí virem depois do clean"],
            ["4º", "<b>Plano frontal</b> — os dois agachamentos laterais",
             "por último, como você montou. É a escolha que custa qualidade de "
             "salto e ganha salto sob fadiga — ler a caixa abaixo"],
        ], [0.07, 0.31, 0.62]),
        ("espaco", 3),
        ("caixa", "<b>Os dois últimos são o mesmo movimento, e só valem por dois "
                  "se forem feitos diferente.</b> <b>Com banco:</b> desce até "
                  "tocar, <b>para</b>, e sai no salto lateral — profundo, "
                  "controlado, força. <b>Sem banco:</b> contato curto, sem parada, "
                  "um salto puxando o outro — raso, rápido, coordenação. Feitos "
                  "iguais, são oito séries da mesma coisa.", VERDE_CLARO, VERDE),
        ("caixa", "<b>52 contatos, todos laterais.</b> São 28 no banco e 24 sem "
                  "banco — e ao contrário das outras fichas, todos caem no mesmo "
                  "plano e no mesmo joelho. <b>Se houver quadra pesada no mesmo "
                  "dia ou no seguinte, o sem banco vai para 2 séries.</b> "
                  "Aterrissagem lateral com glúteo médio cansado é onde o joelho "
                  "entra para dentro.", AMBAR_CLARO, AMBAR),
        ("espaco", 2),
        ("h", "Os exercícios"),
        ("notas", [
            ("Os dois da polia", "<b>Stiff unilateral:</b> em pé numa perna, cabo "
             "baixo, quadril para trás, perna livre estendendo atrás como "
             "contrapeso. <b>Rotação de tronco:</b> costas na bola, cabo na altura "
             "do peito, braços estendidos — gira o <b>tronco</b>, não os braços, e "
             "o quadril fica parado. Nos dois, carga leve: eles preparam a sessão, "
             "não são a sessão."),
            ("Hang clean", "Da altura do joelho, com recepção completa. "
             "<b>Velocidade da barra manda: se cair, a série acabou</b>, mesmo "
             "sobrando repetição. 72% do seu clean é leve de propósito — aqui se "
             "treina o gesto rápido, não o máximo."),
            ("Remada curvada com barra", "<b>Tronco entre 15° e 30° acima da "
             "horizontal, e PARADO.</b> A barra vem ao umbigo. A 88% e três "
             "repetições, o erro é levantar o tronco para a barra subir — aí a "
             "carga está alta demais. <b>Lombar arredondou, a série acabou.</b>"),
            ("Elevação pélvica", "Costas no banco, barra sobre o quadril com "
             "proteção. Sobe empurrando pelo <b>calcanhar</b> até o tronco ficar "
             "reto e segura 1 segundo em cima. Se a lombar arqueia para subir "
             "mais, você passou do ponto — a amplitude termina onde o quadril "
             "termina, não onde a lombar continua."),
            ("Os dois agachamentos laterais", "Pés bem afastados, apontados à "
             "frente, <b>os dois calcanhares no chão</b>. Desce sobre uma perna "
             "com a outra estendida, e sai lateralmente. <b>O joelho não entra "
             "para dentro na aterrissagem</b> — se entrar, diminua a distância do "
             "salto antes de diminuir a profundidade. Aterrissagem que faz "
             "barulho é série que acabou."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 8 séries de plano frontal, 7 de quadril, 5 de LPO, "
                  "4 de puxar, 3 de tronco — e ZERO de empurrar.</b> Para um dia "
                  "de quadril e lateral está certo, e é bom que o ombro descanse. "
                  "Só não pode ser o retrato da semana: o próximo dia de sala "
                  "precisa de empurrar."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# FORÇA PURA 90 A 95% — três levantamentos e o bloco específico
# ════════════════════════════════════════════════════════════════════════════
# A ficha de 29/10 dizia: ou 88% com 2 min de pausa, ou 2-3 repetições no limite
# com 3 min. Ele veio com a outra ponta — 90 a 95% —, então a pausa sobe para 4
# min, que é a consequência e não uma escolha minha. Os três têm referência de
# 1RM no sistema, então a ficha inteira sai por percentual. "Exercícios
# específicos" eu li como um bloco a acrescentar, e ele ficou curto de propósito.
FORCA_90_95 = {
    "arquivo": "ELASE-forca-pura-90-95.pdf",
    "meta_titulo": "ELASE - Forca pura 90 a 95 por cento",
    "meta_assunto": "Agachamento, hang pull e supino no limite, mais bloco especifico",
    "titulo": "Força pura · 90 a 95%",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Quatro levantamentos no limite &nbsp;&middot;&nbsp; 4 × 2-3 "
                 "&nbsp;&middot;&nbsp; mais um bloco específico, curto",
    "rotulo_carga": "CARGA",
    "larguras": [196, 46, 44, 48],
    "abertura":
        "<b>Esta é a sessão mais pesada da sua pasta, e a pausa de 4 minutos é "
        "parte da prescrição — não sobra de tempo.</b> A 90-95% duas ou três "
        "repetições são as que existem: a 95% cabem duas, a 90% cabem três ou "
        "quatro. Com pausa curta a terceira e a quarta série não aconteceriam, e "
        "a sessão viraria fadiga sob carga máxima. <b>Dezesseis séries pesadas, "
        "quarenta repetições no dia inteiro</b> — é para ser assim.",
    "aquecimento_titulo": "Aquecimento — a rampa é longa, e é obrigatória",
    "aquecimento_nota": "A 95% a rampa não é aquecimento: é o que torna a primeira "
                        "série possível. Ela sobe em singles e para antes da carga.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Mobilidade de tornozelo, quadril e torácica", "6 min", "a mesma do app"],
        ["Rotadores externos com elástico", "2 × 12", "antes do supino"],
        ["Rampa: 40, 60, 75, 85 e 90%", "5, 3, 2, 1 e 1", "2 a 3 min entre elas"],
    ],
    "exercicios": [
        ("Agachamento livre",
         "força pura &middot; perna — rack com os pinos na altura",
         "4 × 2-3", "4 min", "90-95%"),
        ("Hang pull",
         "força pura &middot; LPO — puxada alta, sem recepção",
         "4 × 2-3", "4 min", "90-95%"),
        ("Supino reto com barra",
         "força pura &middot; empurrar — ALTERNA com o 4",
         "4 × 2-3", "2 min", "90-95%"),
        ("Puxada fechada sentado",
         "força pura &middot; puxar — ALTERNA com o 3",
         "4 × 2-3", "2 min", "90-95%"),
        ("Salto de ataque com aproximação",
         "específico &middot; expressão — aproximação completa",
         "4 × 3", "2 min", "máximo"),
        ("Arremesso de medicine ball",
         "específico &middot; acima da cabeça, com os dois braços",
         "3 × 4", "60 s", "3 kg"),
    ],
    "nota_tabela":
        "<b>A carga sobe dentro da faixa, série a série:</b> 1ª com 3 repetições a "
        "90%, 2ª com 3 a 92%, 3ª com 2 a 94%, 4ª com 2 a 95%. Os quatro "
        "levantamentos já estão na sua tabela de 1RM — o hang pull sai do "
        "<b>clean pull</b>. <b>Supino e puxada fechada são alternados</b>: 2 min "
        "de um para o outro, o que dá 4 min entre as séries de cada um. Anote a "
        "carga e quantas repetições saíram: a 95%, duas limpas valem mais que "
        "três arrastadas.",
    "caixa_duracao":
        "<b>Duração prevista: 75 a 90 minutos</b> — e mais da metade é pausa. "
        "Dezesseis séries pesadas com 4 minutos entre as de cada exercício, e "
        "isso não é desperdício: é o que faz a quarta série valer. <b>Com menos "
        "de 70 minutos, tire um exercício inteiro</b> — nunca encurte a pausa. "
        "Alternar o supino com a puxada é o que fez o quarto levantamento caber "
        "sem alongar a sessão.",
    "verso": [
        ("h", "Por que a pausa dobrou"),
        ("grade", ["FICHA", "CARGA", "REPETIÇÕES", "PAUSA"], [
            ["Força pura · 2 a 3 (29/10)", "88% — dá para fazer 5",
             "2 ou 3, sobrando 2 ou 3", "2 min"],
            ["<b>Esta ficha</b>", "<b>90 a 95%</b>",
             "<b>2 ou 3, no limite</b>", "<b>4 min</b>"],
        ], [0.30, 0.24, 0.26, 0.20]),
        ("espaco", 3),
        ("caixa", "<b>As duas fichas são a mesma escolha vista dos dois lados.</b> "
                  "Repetição no limite e pausa curta não cabem juntas: a 95% o que "
                  "repõe a energia da série seguinte leva de 3 a 5 minutos, e com "
                  "2 a terceira série já perde repetição. Você pediu a carga alta, "
                  "então a pausa veio junto. <b>Se o tempo de sala não permitir 4 "
                  "minutos, a ficha certa é a de 29/10, não esta com pausa "
                  "cortada.</b>", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Agachamento livre", "<b>Rack com os pinos na altura de escapar.</b> "
             "A 95% a diferença entre terminar a série e despejar a barra é uma "
             "repetição, e a decisão tem de estar tomada antes: <b>a série acaba "
             "quando a subida desacelera ou o tronco cai à frente</b>, não quando "
             "a barra para. Profundidade igual à de sempre."),
            ("Hang pull", "Da altura do joelho, <b>puxada alta sem recepção</b> — "
             "tríplice extensão, ombros encolhendo no fim, barra rente ao corpo. "
             "Por não ter recepção, ele aguenta mais carga que o clean: o "
             "percentual aqui é do seu <b>clean pull</b>, não do clean. Se a barra "
             "para de acelerar, a série acabou."),
            ("Supino e puxada, alternados", "<b>Com alguém na barra do supino, "
             "sempre.</b> A 95% é o único levantamento da ficha em que a falha pode "
             "ser completa com segurança, e só por causa do ajudante. Sozinho: pare "
             "com uma repetição de sobra e anote. <b>Na puxada fechada a 90-95% o "
             "corpo tende a subir do banco</b> — trave o apoio das coxas; se mesmo "
             "assim você levanta do assento, a carga passou do ponto, e isso vale "
             "mais que o percentual da tabela. Pegada neutra ou supinada, tronco "
             "parado, barra até a parte alta do peito."),
            ("O bloco específico", "<b>Curto de propósito.</b> Depois de doze "
             "séries no limite, o salto não vai bater a sua melhor marca, e não é "
             "para bater: o que se treina aqui é o <b>gesto logo depois da carga "
             "máxima</b>, com o sistema nervoso ainda acordado. Aproximação "
             "completa, alvo alto, três saltos por série e descanso de verdade "
             "entre elas. <b>Se o salto piorar série após série, o bloco "
             "acabou</b> — pare, não complete."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 4 séries de perna, 4 de LPO, 4 de empurrar, 4 de "
                  "puxar e 7 do bloco específico.</b> Com a puxada fechada os "
                  "padrões fecham — e ela entrou alternada com o supino "
                  "justamente para caber: solta, com 4 minutos de pausa próprios, "
                  "custaria 16 minutos a mais de sala. <b>A próxima sessão pesada "
                  "precisa de pelo menos 48 horas de distância:</b> 90-95% cobra "
                  "no sistema nervoso, não no músculo, e isso não aparece como dor "
                  "no dia seguinte — aparece como barra lenta dois dias depois."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# PUXAR E UNILATERAL — seis exercícios, três blocos
# ════════════════════════════════════════════════════════════════════════════
# Nenhum intervalo veio na lista, então eles são meus. A ordem é a dele, e o
# verso declara a cascata que ela cria: barra fixa ao máximo, remada curvada
# pesada e hang clean dependem todos da mesma pegada e da mesma dorsal, nessa
# ordem. Uma troca resolveria; não apliquei, só escrevi qual é.
PUXAR_UNILATERAL = {
    "arquivo": "ELASE-puxar-e-unilateral.pdf",
    "meta_titulo": "ELASE - Puxar e unilateral",
    "meta_assunto": "Tronco a 4 repeticoes, hang clean leve e perna unilateral",
    "titulo": "Puxar e unilateral",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Seis exercícios &nbsp;&middot;&nbsp; tronco a 4 repetições, "
                 "clean leve e perna unilateral &nbsp;&middot;&nbsp; nesta ordem",
    "rotulo_carga": "CARGA",
    "larguras": [190, 52, 44, 48],
    "abertura":
        "<b>Duas séries de puxar para cada uma de empurrar</b> — oito contra "
        "quatro. Em quem ataca centenas de bolas por semana, é para esse lado que "
        "a conta deve pender, e esta é a primeira ficha da sua pasta em que ela "
        "pende tanto. O preço é que <b>três exercícios seguidos dependem da mesma "
        "pegada</b>: barra fixa ao máximo, remada curvada pesada e hang clean. "
        "O verso diz o que isso custa e qual troca resolveria.",
    "aquecimento_titulo": "Aquecimento — ombro e pegada, nessa ordem",
    "aquecimento_nota": "O desenvolvimento abre a sessão e a barra fixa vem logo "
                        "atrás: o manguito entra aquecido, e a pegada também.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou esteira, ritmo leve", "4 min", "até suar, sem cansar"],
        ["Mobilidade de torácica, ombro e quadril", "6 min", "a mesma do app"],
        ["Rotadores externos com elástico", "2 × 12", "antes do desenvolvimento"],
        ["Barra vazia: desenvolvimento e hang clean", "2 × 5 cada", "o padrão, sem peso"],
    ],
    "exercicios": [
        ("Desenvolvimento com barra",
         "força &middot; empurrar vertical — SEM perna",
         "4 × 4", "2,5 min", "6RM"),
        ("Barra fixa",
         "força &middot; puxar vertical — máximo de repetições",
         "4 × máx.", "2,5 min", "corpo"),
        ("Remada curvada com barra",
         "força &middot; puxar horizontal — tronco PARADO",
         "4 × 4", "2,5 min", "87%"),
        ("Hang clean",
         "técnica &middot; LPO — carga baixa, seis seguidas",
         "4 × 6", "2 min", "60%"),
        ("Agachamento lateral com barra",
         "força &middot; plano frontal — 6 para CADA lado",
         "4 × 6", "90 s", "RIR 2"),
        ("Stiff unilateral com halteres",
         "força &middot; posterior — 6 em CADA perna",
         "4 × 6", "90 s", "RIR 2"),
    ],
    "nota_tabela":
        "Só a remada curvada e o hang clean saem da sua tabela de 1RM — o clean a "
        "<b>60%</b>, que é a carga baixa que você pediu. No desenvolvimento use a "
        "<b>carga de 6 repetições</b> e faça 4. Na barra fixa é o peso do corpo: "
        "<b>passando de 10 repetições na primeira série, ponha carga no cinto.</b> "
        "Anote os dois lados nos dois últimos, e anote quantas repetições saíram "
        "em CADA série de barra fixa — é desse número que sai a progressão dela.",
    "caixa_duracao":
        "<b>Duração prevista: 65 a 80 minutos</b> — 24 séries em três blocos. "
        "<b>Com menos de 55 minutos:</b> hang clean em 3 séries e agachamento "
        "lateral em 3. Não corte a barra fixa nem a remada curvada — são elas que "
        "fazem a conta pender para o lado certo.",
    "verso": [
        ("h", "A cascata da pegada"),
        ("grade", ["", "O QUE", "DE QUE ELE PRECISA"], [
            ["2º", "<b>Barra fixa</b>, ao máximo",
             "pegada, dorsal e bíceps até o fim — é o exercício que mais esvazia "
             "os três"],
            ["3º", "<b>Remada curvada</b>, 4 × 4 a 87%",
             "os mesmos três, agora com carga alta e lombar inteira"],
            ["4º", "<b>Hang clean</b>, 4 × 6",
             "pegada outra vez, e posição de dorso. Em seis repetições seguidas, "
             "a mão costuma soltar antes do resto"],
        ], [0.07, 0.30, 0.63]),
        ("espaco", 3),
        ("caixa", "<b>Quem vem primeiro leva a carga boa; os outros dois levam o "
                  "resto.</b> Do jeito que está, a barra fixa ao máximo esvazia a "
                  "pegada antes da remada pesada e do clean. <b>Se a remada "
                  "curvada é a prioridade do dia, troque a 2ª pela 3ª</b> — remada "
                  "carregada primeiro, barra fixa ao máximo depois, que é quando "
                  "falhar não atrapalha mais ninguém. Mantive a sua ordem; a troca "
                  "é de uma linha.", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Desenvolvimento com barra", "<b>Sem impulso de perna:</b> se o joelho "
             "dobra, virou push press. Glúteo e abdômen apertados para a lombar "
             "não arquear; a barra passa rente ao rosto e a cabeça atravessa para "
             "a frente dos braços no fim."),
            ("Barra fixa — o que é “máximo”", "<b>Falha técnica, não "
             "muscular:</b> a série acaba na primeira repetição em que o queixo "
             "não passa a barra, ou em que o corpo começa a balançar para ajudar. "
             "<b>As repetições vão cair de série para série — é para caírem.</b> "
             "Anote as quatro: 10-7-5-4 numa semana e 10-8-6-5 na outra é "
             "progresso, mesmo com a primeira série igual."),
            ("Remada curvada com barra", "<b>Tronco entre 15° e 30° acima da "
             "horizontal, e PARADO.</b> A barra vem ao umbigo, não ao peito. O erro "
             "é levantar o tronco para a barra subir — aí a carga está alta demais, "
             "e depois da barra fixa ela vai parecer mais alta do que é. "
             "<b>Lombar arredondou, a série acabou.</b>"),
            ("Hang clean a 60%", "Carga baixa e <b>seis repetições seguidas</b>: "
             "aqui não se treina potência, treina-se o padrão repetido até ficar "
             "automático. Da altura do joelho, tríplice extensão, cotovelos "
             "fechando rápido. <b>Se a pegada soltar antes das seis, a série "
             "acabou</b> — magnésio ajuda, repetição mal pega não."),
            ("Os dois últimos", "<b>Agachamento lateral:</b> pés bem afastados e "
             "apontados à frente, desce sobre uma perna com a outra estendida, os "
             "dois calcanhares no chão. <b>Stiff unilateral:</b> em pé numa perna, "
             "quadril para trás, perna livre estendendo atrás como contrapeso. Nos "
             "dois, <b>comece pelo lado mais fraco e o lado bom para no número que "
             "o fraco fez</b>."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 8 séries de puxar, 4 de empurrar, 4 de LPO, 4 de "
                  "plano frontal e 4 de posterior unilateral.</b> Dois para um a "
                  "favor de puxar, que é o que as últimas fichas vinham devendo. "
                  "<b>Nada de agachamento bilateral e nada de dobra de quadril com "
                  "barra</b> — a perna aqui é toda unilateral, e isso é escolha, "
                  "não esquecimento."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# TRÊS COMPLEXOS — tri-sets em sequência, 2 min entre rodadas
# ════════════════════════════════════════════════════════════════════════════
# Isto NÃO é a ficha de contraste. Lá o pesado e o explosivo são separados por
# 3 min para o salto sair potenciado; aqui os três exercícios vêm colados e o
# salto chega cansado — de propósito. São métodos diferentes com nomes
# parecidos, e o verso põe os dois lado a lado.
COMPLEXOS = {
    "arquivo": "ELASE-tres-complexos.pdf",
    "meta_titulo": "ELASE - Tres complexos",
    "meta_assunto": "Tri-sets em sequencia, 2 min entre rodadas, 4 rodadas cada",
    "titulo": "Três complexos",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Três blocos de três exercícios &nbsp;&middot;&nbsp; os três "
                 "colados, sem pausa entre eles &nbsp;&middot;&nbsp; 2 min e volta",
    "rotulo_carga": "CARGA",
    "numerar": False,
    "cab_meio": ["RODADAS", "PAUSA", "CARGA"],
    "larguras": [194, 50, 44, 44],
    "abertura":
        "<b>Cada bloco é um exercício pesado, um de tempo sob tensão e um "
        "explosivo, os três colados.</b> A pausa de 2 "
        "minutos vem só depois do terceiro; são 4 rodadas, e só se passa ao "
        "bloco seguinte quando o anterior acabou. "
        "<b>O salto do fim chega cansado, e é para chegar</b> — treina-se "
        "potência com a perna já carregada.",
    "aquecimento_titulo": "Aquecimento — os três padrões antes do primeiro bloco",
    "aquecimento_nota": "Num complexo não há rampa no meio: quando o bloco começa, "
                        "a carga já está na barra.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta leve e mobilidade de tornozelo, quadril e torácica",
         "10 min", "a do app, sem cansar"],
        ["Barra vazia, 55% e 70% no padrão de cada bloco", "1 × 8, 5 e 3",
         "1 min entre elas"],
        ["3 saltos verticais máximos", "3 saltos", "a sua régua do dia"],
    ],
    "exercicios": [
        ("A1. Agachamento com barra",
         "pesado &middot; perna — a barra fica montada",
         "4 rodadas", "direto", "80%"),
        ("A2. Agachamento isométrico",
         "tempo sob tensão &middot; 40 s parado, joelho a 90°",
         "4 × 40 s", "direto", "corpo"),
        ("A3. Agachamento com salto",
         "explosivo &middot; 10 saltos — 2 min e volta ao A1",
         "4 × 10", "2 min", "corpo"),
        ("B1. Supino reto com barra",
         "pesado &middot; empurrar — com ajudante",
         "4 rodadas", "direto", "80%"),
        ("B2. Prancha com remada",
         "tempo sob tensão &middot; 6 em CADA braço",
         "4 × 6", "direto", "RIR 3"),
        ("B3. Flexão explosiva",
         "explosivo &middot; 6 — 2 min e volta ao B1",
         "4 × 6", "2 min", "corpo"),
        ("C1. Puxada fechada sentado",
         "pesado &middot; puxar — tronco parado",
         "4 rodadas", "direto", "80%"),
        ("C2. Clean",
         "LPO &middot; 6 do chão, uma de cada vez",
         "4 × 6", "direto", "60%"),
        ("C3. Afundo com salto no cabo",
         "explosivo &middot; 6 — 2 min e volta ao C1",
         "4 × 6", "2 min", "leve"),
    ],
    "nota_tabela":
        "<b>“Direto” é sem pausa nenhuma: acabou um, começa o "
        "próximo.</b> Os 2 minutos só existem depois do terceiro de cada bloco. "
        "Agachamento, supino, puxada e clean saem da sua tabela de 1RM. <b>80% é "
        "escolhido para sobreviver a quatro rodadas:</b> se a quarta não sair "
        "limpa, use 75% na próxima — não 85%.",
    "caixa_duracao":
        "<b>Duração prevista: 55 a 65 minutos</b> — 12 rodadas. <b>Com menos de 45 "
        "minutos:</b> 3 rodadas de cada bloco. Corte rodada, nunca exercício.",
    "verso": [
        ("h", "Complexo não é contraste"),
        ("grade", ["", "COMO FICA", "O QUE TREINA"], [
            ["<b>Contraste</b><br/>(a outra ficha)",
             "pesado, <b>3 min de pausa</b>, depois o explosivo",
             "a pausa deixa o sistema nervoso ligado e a fadiga ir embora: o "
             "salto sai <b>mais alto</b> do que sairia sozinho"],
            ["<b>Complexo</b><br/>(esta ficha)",
             "os três <b>colados</b>, 2 min só no fim da rodada",
             "o salto chega cansado: treina-se <b>sustentar potência</b> com a "
             "perna carregada, que é o 4º set de um jogo"],
        ], [0.18, 0.30, 0.52]),
        ("espaco", 3),
        ("caixa", "<b>Os dois métodos são bons e não são o mesmo.</b> Se o que "
                  "você quer hoje é altura de salto, a ficha é a de contraste. "
                  "Se é aguentar saltar no fim do jogo, é esta. <b>O erro seria "
                  "cobrar altura máxima nos saltos daqui</b> — eles vão sair "
                  "abaixo da régua que você mediu no aquecimento, e isso não é "
                  "sinal de nada."),
        ("espaco", 3),
        ("h", "Os blocos"),
        ("notas", [
            ("A — a barra fica montada", "Os três do bloco A usam o mesmo "
             "agachamento: <b>carregado, isométrico e saltado</b>. Monte 80% e "
             "deixe; o isométrico e o salto são sem carga, então só se tira a "
             "barra. <b>No isométrico, 40 segundos parado com o joelho a 90°</b> — "
             "se a coxa começar a tremer antes dos 30 s, a rodada anterior foi "
             "pesada demais."),
            ("B — a prancha é o freio", "<b>Prancha com remada:</b> apoio em "
             "prancha, halteres nas mãos, puxa um de cada vez. O que conta não é "
             "a remada, é <b>o quadril não girar</b> — se ele roda, diminua a "
             "carga. <b>Flexão explosiva:</b> as mãos saem do chão, e a descida é "
             "amortecida; se as mãos pararem de sair, o bloco acabou."),
            ("C — o clean é o ponto de atenção", "<b>Seis cleans do chão dentro "
             "de um complexo, depois de uma puxada pesada, é onde a técnica "
             "cede.</b> Uma repetição de cada vez, barra parada no chão entre "
             "elas, a 60%. <b>Se a recepção sair torta ou o cotovelo atrasar, "
             "troque por hang clean ou corte para 4 repetições</b> — clean "
             "cansado não vale o risco."),
            ("Os saltos", "<b>64 contatos no total</b> — 40 do agachamento com "
             "salto e 24 do afundo. Em todos: <b>joelho não entra para dentro na "
             "aterrissagem</b>, e aterrissagem que faz barulho é rodada que "
             "acabou. O afundo no cabo é leve: o cabo dá direção, não carga."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>Se houver jogo ou quadra pesada nas próximas 48 horas, esta "
                  "não é a ficha.</b> Doze rodadas coladas e 64 contatos cobram "
                  "dois dias — e cobram em perna, que é exatamente o que o jogo "
                  "vai pedir.", AMBAR_CLARO, AMBAR),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# VELOCIDADE — seis exercícios, a barra decide a série
# ════════════════════════════════════════════════════════════════════════════
# A regra de parada desta ficha é o inverso de todas as outras: nas demais a
# série acaba quando a técnica cede; aqui acaba quando a barra fica LENTA, que
# chega muito antes. Por isso 6-8 é alvo, não cota — e por isso a carga fica em
# 50%, onde seis repetições ainda saem rápidas.
VELOCIDADE = {
    "arquivo": "ELASE-velocidade.pdf",
    "meta_titulo": "ELASE - Velocidade",
    "meta_assunto": "Forca-velocidade a 50 por cento; a serie acaba quando a barra desacelera",
    "titulo": "Velocidade",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Seis exercícios &nbsp;&middot;&nbsp; 4 × 6-8 em todos "
                 "&nbsp;&middot;&nbsp; carga leve, intenção máxima",
    "rotulo_carga": "CARGA",
    "larguras": [192, 50, 44, 46],
    "abertura":
        "<b>Esta é a única ficha da sua pasta em que a barra ficar lenta encerra a "
        "série.</b> Nas outras, a série acaba quando a técnica cede; aqui acaba "
        "antes disso, no instante em que a repetição sai mais devagar que a "
        "anterior — mesmo que seja a quinta. <b>6-8 é alvo, não cota.</b> A carga "
        "é leve de propósito: o que se treina é a <b>intenção</b> de mover rápido, "
        "e ela só existe quando o peso permite.",
    "aquecimento_titulo": "Aquecimento — e a referência de velocidade do dia",
    "aquecimento_nota": "A última linha não é aquecimento: são as repetições com "
                        "que você vai comparar todas as outras. Guarde como elas "
                        "saíram.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta leve e mobilidade de quadril, torácica e ombro",
         "10 min", "a do app, sem cansar"],
        ["Ponte de glúteo e deslocamento lateral com elástico",
         "2 × 12", "acorda o quadril"],
        ["Barra vazia e 35% no padrão de cada exercício", "1 × 8 e 1 × 5",
         "já no ritmo rápido"],
        ["<b>3 repetições do 1º exercício na carga do dia</b>", "3 rep",
         "a sua régua de velocidade"],
    ],
    "exercicios": [
        ("Stiff com barra",
         "velocidade &middot; dobra de quadril — SEM descida lenta",
         "4 × 6-8", "2 min", "50%"),
        ("Elevação pélvica",
         "velocidade &middot; extensão de quadril — trava em cima",
         "4 × 6-8", "2 min", "metade"),
        ("Remada fechada sentada",
         "velocidade &middot; puxar horizontal — tronco parado",
         "4 × 6-8", "2 min", "metade"),
        ("Agachamento com salto com peso",
         "velocidade &middot; perna — acima de 1,0 m/s",
         "4 × 6-8", "2 min", "30%"),
        ("Supino saindo do peito",
         "velocidade &middot; empurrar — barra PARADA no peito",
         "4 × 6-8", "2 min", "50%"),
        ("Stiff unilateral com desenvolvimento",
         "controle &middot; 6-8 em CADA perna — sem pressa",
         "4 × 6-8", "90 s", "leve"),
    ],
    "nota_tabela":
        "Stiff, agachamento com salto e supino saem da sua tabela de 1RM. "
        "<b>“Metade”</b> quer dizer metade da carga que você usaria para "
        "6 repetições difíceis — na elevação pélvica e na remada. <b>Anote a carga "
        "e quantas repetições saíram RÁPIDAS</b>, não quantas você fez: é esse "
        "número que diz se a carga da semana que vem sobe ou desce.",
    "caixa_duracao":
        "<b>Duração prevista: 60 a 75 minutos</b> — 24 séries leves com 2 min de "
        "pausa. A pausa parece longa para o peso que está na barra, e é de "
        "propósito: <b>o que se recupera aqui não é o músculo, é a capacidade de "
        "acelerar.</b> Com menos de 50 minutos, 3 séries em cada um.",
    "verso": [
        ("h", "A regra é o inverso das outras fichas"),
        ("grade", ["", "A SÉRIE ACABA QUANDO...", "POR QUÊ"], [
            ["<b>As outras fichas</b>",
             "a técnica cede — a barra desacelera, a lombar sai do lugar",
             "lá o objetivo é carga, e a última repetição boa é a que vale"],
            ["<b>Esta ficha</b>",
             "a <b>velocidade</b> cai, mesmo com técnica perfeita e sobrando força",
             "aqui o objetivo é a aceleração. Repetição lenta não treina "
             "velocidade — treina outra coisa, e cansa para a série seguinte"],
        ], [0.20, 0.34, 0.46]),
        ("espaco", 3),
        ("caixa", "<b>Como saber que a carga está certa:</b> as 6 primeiras "
                  "repetições da 1ª série saem todas no mesmo ritmo. Se a 4ª já "
                  "sai mais devagar, está pesado — tire peso <b>na mesma "
                  "sessão</b>, não na próxima. Se as 8 saem fáceis e iguais, "
                  "ponha peso. <b>Carga que permite 8 repetições lentas é pior "
                  "que carga que permite 5 rápidas.</b>", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Stiff — atenção, é o contrário do de sempre", "Nas outras fichas o "
             "stiff vem com <b>descida de 3 segundos</b>. Aqui não: a descida é "
             "controlada mas normal, e <b>a subida é a mais rápida que você "
             "conseguir</b>. Mesmo exercício, intenção oposta — não faça no "
             "automático."),
            ("Elevação pélvica e remada fechada", "Os dois sem referência de 1RM: "
             "use <b>metade da carga de 6 repetições difíceis</b>. Na elevação "
             "pélvica, suba rápido e <b>trave 1 segundo em cima</b> antes de "
             "descer. Na remada, cotovelo para trás rápido e volta controlada — "
             "<b>tronco parado</b>, senão a velocidade é do corpo, não da carga."),
            ("Agachamento com salto com peso", "30% do seu agachamento, barra ou "
             "halteres. <b>Acima de 1,0 m/s</b>: se o salto começar a ficar baixo, "
             "a série acabou. Aterrissa, estabiliza e recomeça — <b>sem quicar</b>, "
             "e o joelho não entra para dentro."),
            ("Supino saindo do peito", "<b>A barra para no peito, de verdade</b> — "
             "sem quique, sem aproveitar o repique. Cada repetição recomeça do "
             "zero, e é por isso que a carga é menor: o primeiro centímetro é o "
             "exercício inteiro. Com alguém na barra."),
            ("Stiff unilateral com desenvolvimento", "<b>O único que não é de "
             "velocidade.</b> Em pé numa perna, desce no stiff, volta e <b>só "
             "então</b> empurra o halter acima da cabeça — um movimento de cada "
             "vez, sem emendar. Carga leve: aqui o que se treina é não perder o "
             "equilíbrio na transição. Comece pela perna mais fraca."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 12 das 24 séries são de cadeia posterior</b> — "
                  "stiff, elevação pélvica e stiff unilateral. Metade da sessão no "
                  "mesmo tecido, e é a identidade dela. <b>Se o treino anterior "
                  "teve terra ou agachamento pesado, tire a elevação pélvica</b> "
                  "em vez de reduzir todas: é a que mais repete o que os outros "
                  "dois já fazem."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# AGILIDADE POR POSIÇÃO — braço, coordenação e o circuito de cada um
# ════════════════════════════════════════════════════════════════════════════
# Seis exercícios iguais para todo mundo e um sétimo diferente por posição. As
# cinco posições são as mesmas do app (Levantador, Oposto, Ponteiro, Central,
# Líbero). Os circuitos saem do que cada posição faz no jogo, não de uma lista
# genérica de agilidade: o central é quem mais se desloca na rede, o líbero é o
# único que não sabe a direção antes do estímulo, e assim por diante.
AGILIDADE_POSICAO = {
    "arquivo": "ELASE-agilidade-por-posicao.pdf",
    "meta_titulo": "ELASE - Agilidade por posicao",
    "meta_assunto": "Potencia de braco, coordenacao e circuito de mudanca de direcao por posicao",
    "titulo": "Agilidade por posição",
    "titulo_verso": "O circuito da sua posição",
    "protocolo": "Potência de braço, coordenação e mudança de direção "
                 "&nbsp;&middot;&nbsp; os seis primeiros são iguais, o sétimo é "
                 "o seu",
    "rotulo_carga": "CARGA",
    "larguras": [190, 52, 44, 48],
    "abertura":
        "<b>Esta ficha não é condicionamento, e a diferença está na pausa.</b> "
        "Agilidade e mudança de direção treinadas cansado viram outra coisa: o "
        "corpo aprende o padrão lento, que é o oposto do que se foi buscar. "
        "<b>Se você está ofegante, a pausa foi curta.</b> O sétimo exercício é "
        "diferente para cada posição — o seu está no verso, e ele sai do que a "
        "sua posição realmente faz em quadra.",
    "aquecimento_titulo": "Aquecimento — ombro e tornozelo antes de tudo",
    "aquecimento_nota": "Arremesso e mudança de direção com o corpo frio é onde "
                        "ombro e tornozelo se machucam. Aqui o aquecimento não é "
                        "formalidade.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Corrida leve, deslocamento lateral e de costas", "6 min",
         "nos três sentidos, sem cansar"],
        ["Rotadores externos e Y-T-W com elástico", "2 × 12", "o ombro vai arremessar"],
        ["Saltinhos, mudanças de direção curtas e 3 arremessos leves", "5 min",
         "sobe o ritmo até o do treino"],
    ],
    "exercicios": [
        ("Arremesso de medicine ball acima da cabeça",
         "potência &middot; braço — o padrão do saque",
         "4 × 5", "90 s", "3 kg"),
        ("Arremesso rotacional na parede",
         "potência &middot; tronco para o braço — 5 de CADA lado",
         "4 × 5", "90 s", "3 kg"),
        ("Flexão explosiva com batida de mão",
         "potência &middot; empurrar — o braço do bloqueio",
         "4 × 5", "90 s", "corpo"),
        ("Aceleração do braço com elástico",
         "potência &middot; 8 em CADA braço — rápido, não forte",
         "3 × 8", "60 s", "leve"),
        ("Escada de agilidade",
         "coordenação &middot; pé rápido — 4 padrões diferentes",
         "4 ×", "45 s", "corpo"),
        ("Bola na parede, mãos alternadas",
         "coordenação &middot; reação — 30 s sem deixar cair",
         "3 × 30 s", "45 s", "bola"),
        ("Circuito da sua posição",
         "agilidade &middot; mudança de direção — o seu está no verso",
         "4 ×", "2 min", "no verso"),
    ],
    "nota_tabela":
        "<b>Os seis primeiros são iguais para o elenco inteiro; o sétimo é o seu.</b> "
        "Anote a carga do medicine ball e, no circuito, <b>quanto tempo levou cada "
        "passagem</b> — é o único número desta folha que mede agilidade. Se a "
        "quarta passagem estiver mais lenta que a primeira, o treino de agilidade "
        "acabou ali, mesmo que falte série.",
    "caixa_duracao":
        "<b>Duração prevista: 50 a 65 minutos</b> — 26 séries, quase todas curtas. "
        "<b>A pausa é a prescrição:</b> 90 s nos arremessos e 2 min no circuito "
        "não são folga, são o que mantém a velocidade da próxima repetição. Com "
        "menos de 45 minutos, corte a escada e a bola na parede — nunca o "
        "circuito.",
    "verso": [
        ("h", "Quatro passagens, 2 minutos entre elas"),
        ("grade", ["POSIÇÃO", "O CIRCUITO", "POR QUE ESSE"], [
            ["<b>Levantador</b>",
             "Da postura de defesa na <b>1</b>, sprint de 4 m até a <b>2</b>, para "
             "em cima da bola e levanta, volta de costas. <b>6 saídas</b>",
             "é o deslocamento que ele mais repete no jogo, e o que mais exige "
             "<b>parar em cima da bola</b>, não perto dela"],
            ["<b>Oposto</b>",
             "Bloqueio na <b>2</b>, aterrissa, recua 3 m, aproximação completa e "
             "salto de ataque. <b>5 ciclos</b>",
             "bloqueou e ataca na sequência: é a transição que decide o "
             "contra-ataque pela direita"],
            ["<b>Ponteiro</b>",
             "Postura de recepção, passo lateral até o cone, recua 4 m, "
             "aproximação completa e salto. <b>5 ciclos</b>",
             "recebe e ataca no mesmo rally — é a cadeia que mais cobra do "
             "passador-atacante, e a que ninguém treina"],
            ["<b>Central</b>",
             "Bloqueio na <b>3</b>, passada cruzada até a <b>4</b> ou a <b>2</b>, "
             "bloqueio, volta à 3. <b>6 bloqueios</b>",
             "ninguém se desloca mais na rede, e com menos tempo para decidir. "
             "Alterne os lados a cada passagem"],
            ["<b>Líbero</b>",
             "Postura de defesa, alguém aponta a direção, sprint ou queda até o "
             "cone, recupera a postura. <b>6 reações</b>",
             "é a única posição em que a direção <b>não</b> é decidida antes: "
             "quem manda é o estímulo, e por isso o circuito dele precisa de "
             "outra pessoa"],
        ], [0.15, 0.44, 0.41]),
        ("espaco", 3),
        ("caixa", "<b>Recuperação completa entre as passagens.</b> Duas pessoas "
                  "fazem o circuito alternadas: enquanto uma corre, a outra "
                  "descansa — assim os 2 minutos saem sozinhos. <b>Cronometre a "
                  "primeira passagem e compare as outras três.</b> Caiu mais de "
                  "10%, pare: a partir dali você está treinando cansaço, não "
                  "agilidade.", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os seis de todo mundo"),
        ("notas", [
            ("Os dois arremessos", "<b>Acima da cabeça:</b> os dois braços, bola "
             "atrás da nuca, e o arremesso sai do tronco inteiro — joga para a "
             "frente e para longe, não para cima. <b>Rotacional:</b> de lado para "
             "a parede, pé de trás gira, quadril puxa o tronco e o braço vai "
             "junto. É o padrão do ataque sem a bola de verdade — e é o que mais "
             "transfere para a potência de saque."),
            ("Flexão explosiva e elástico", "<b>Flexão:</b> as mãos saem do chão e "
             "batem uma na outra; a descida é amortecida. Se as mãos pararem de "
             "sair, a série acabou. <b>Elástico:</b> preso atrás, cotovelo alto, "
             "o movimento do ataque <b>o mais rápido possível</b> — a carga é "
             "leve de propósito, aqui ninguém está ficando forte, está ficando "
             "rápido."),
            ("Escada e bola na parede", "São <b>coordenação</b>, não "
             "condicionamento: 4 padrões diferentes na escada (dois pés dentro, "
             "in-and-out, lateral, cruzado) e pé rápido com o tronco quieto. A "
             "bola na parede com as mãos alternadas treina o que o jogo cobra do "
             "olho e da mão — comece devagar e só acelere quando parar de cair."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>Nada aqui deve deixar você ofegante.</b> Se o peito arde ou "
                  "a respiração não volta na pausa, a sessão virou condicionamento "
                  "— e condicionamento feito no lugar de agilidade ensina o corpo "
                  "a se mover devagar. Aumente a pausa antes de reduzir o treino."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# PRÉ-COMPETIÇÃO — braço explosivo, 35 minutos, quase nada de volume
# ════════════════════════════════════════════════════════════════════════════
# A regra desta ficha é o que ela NÃO tem: nada de novo, nada de excêntrica
# lenta, nenhuma tentativa máxima e volume minúsculo. Treze séries no total. O
# risco aqui não é treinar de menos, é o atleta achar pouco e acrescentar.
PRE_COMPETICAO = {
    "arquivo": "ELASE-pre-competicao.pdf",
    "meta_titulo": "ELASE - Pre-competicao, braco explosivo",
    "meta_assunto": "Potencia de membros superiores em volume minimo, 1 a 2 dias antes",
    "titulo": "Pré-competição",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Potência de membros superiores &nbsp;&middot;&nbsp; 1 a 2 dias "
                 "antes do jogo &nbsp;&middot;&nbsp; 13 séries no total",
    "rotulo_carga": "CARGA",
    "larguras": [200, 46, 44, 44],
    "abertura":
        "<b>Esta sessão tem de deixar você melhor, não cansado.</b> É a única "
        "ficha da pasta em que fazer a mais estraga o objetivo: o que se busca "
        "aqui é acordar o braço, não treiná-lo. <b>Treze séries, nenhuma "
        "excêntrica lenta, nenhuma tentativa máxima e nenhum exercício que você "
        "não conheça.</b> Se no dia seguinte houver dor muscular nova, a dose "
        "estava errada — e o jogo paga.",
    "aquecimento_titulo": "Aquecimento — curto, porque a sessão também é",
    "aquecimento_nota": "O ombro vai arremessar e empurrar rápido. Ele entra "
                        "pronto, não aquecendo no primeiro arremesso.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta leve e mobilidade de torácica e ombro", "6 min",
         "a do app, sem cansar"],
        ["Rotadores externos e Y-T-W com elástico", "2 × 12", "leve, acorda o manguito"],
        ["3 arremessos leves e 3 flexões normais", "1 série", "sobe o ritmo e para"],
    ],
    "exercicios": [
        ("Arremesso de medicine ball acima da cabeça",
         "explosivo &middot; o padrão do saque — longe, não alto",
         "3 × 4", "2 min", "3 kg"),
        ("Supino saindo do peito",
         "explosivo &middot; barra PARADA no peito, sem quique",
         "3 × 3", "2,5 min", "50%"),
        ("Flexão explosiva com batida de mão",
         "explosivo &middot; empurrar — mãos saem do chão",
         "3 × 4", "90 s", "corpo"),
        ("Aceleração do braço com elástico",
         "velocidade &middot; 6 em CADA braço — rápido, não forte",
         "2 × 6", "60 s", "leve"),
        ("Remada explosiva com halteres",
         "equilíbrio &middot; puxar — para o ombro não ficar só empurrando",
         "2 × 6", "60 s", "leve"),
    ],
    "nota_tabela":
        "Só o supino sai do seu 1RM, e a <b>50%</b> — metade, de propósito: a "
        "barra tem de voar. <b>Anote a carga, mas não tente subir nenhuma hoje.</b> "
        "Esta é a sessão em que repetir a carga da semana passada é o resultado "
        "certo, e bater recorde é o resultado errado.",
    "caixa_duracao":
        "<b>Duração prevista: 30 a 35 minutos</b> — e é para acabar cedo. "
        "<b>No dia do jogo</b>, se houver sala, faça só os dois primeiros "
        "exercícios em 2 séries. <b>O erro mais comum desta ficha é achar pouco "
        "e acrescentar</b> — não acrescente.",
    "verso": [
        ("h", "O que esta ficha não tem, e por quê"),
        ("grade", ["O QUE FICOU DE FORA", "POR QUÊ"], [
            ["<b>Excêntrica lenta</b> (descida de 3 s)",
             "tempo sob tensão é o que mais produz dor muscular — e dor muscular "
             "dois dias antes do jogo custa salto"],
            ["<b>Tentativa máxima</b> (90% ou mais)",
             "carga máxima cobra no sistema nervoso e aparece como barra lenta e "
             "perna pesada <b>dois dias depois</b>, exatamente no jogo"],
            ["<b>Volume</b> (mais de 3 séries por exercício)",
             "o estímulo que acorda o braço já está dado na terceira série. O "
             "resto só gera fadiga que não dá tempo de ir embora"],
            ["<b>Exercício novo</b>",
             "movimento desconhecido sempre deixa dor — e na véspera não há como "
             "saber se deixou até acordar"],
        ], [0.33, 0.67]),
        ("espaco", 3),
        ("caixa", "<b>O teste é no dia seguinte.</b> Se acordar com dor muscular "
                  "nova, com ombro travado ou com a sensação de ter treinado, a "
                  "dose estava errada — avise a comissão, porque a próxima "
                  "pré-competição precisa ser menor. <b>O resultado certo é "
                  "acordar igual ou melhor.</b>", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Arremesso acima da cabeça", "Os dois braços, bola atrás da nuca, e o "
             "arremesso sai do tronco inteiro. <b>Para a frente e para longe, não "
             "para cima.</b> Quatro arremessos por série, cada um com intenção "
             "máxima — e entre eles, tempo para pegar a bola sem pressa."),
            ("Supino saindo do peito", "<b>A barra para no peito de verdade</b>, "
             "sem quique, e sai o mais rápido possível. A 50% a barra parece "
             "leve: é isso mesmo. <b>Três repetições, e a série acaba se a "
             "terceira sair mais devagar que a primeira.</b> Com alguém na barra."),
            ("Flexão e elástico", "<b>Flexão:</b> as mãos saem do chão e batem; "
             "quatro, não mais. <b>Elástico:</b> preso atrás, cotovelo alto, o "
             "movimento do ataque o mais rápido possível — leve, porque aqui "
             "ninguém está ficando forte."),
            ("Remada explosiva", "Está aqui só para o ombro não sair da sessão "
             "tendo feito apenas empurrar. <b>Duas séries leves, puxada rápida e "
             "volta controlada</b>, e acabou."),
        ]),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# FORÇA COMPLETA — para o sub-19 e para quem não compete
# ════════════════════════════════════════════════════════════════════════════
# Enquanto o elenco que compete afina, estes acumulam: é a janela em que dá para
# carregar sem pagar no fim de semana. A ficha serve a dois públicos na mesma
# sala, e por isso traz uma caixa própria para o sub-19 — percentual mais baixo,
# uma repetição a mais na reserva, e nenhuma tentativa máxima.
FORCA_COMPLETA = {
    "arquivo": "ELASE-forca-completa.pdf",
    "meta_titulo": "ELASE - Forca completa",
    "meta_assunto": "Sessao de forca de corpo inteiro para sub-19 e atletas que nao competem",
    "titulo": "Força completa",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Sub-19 e quem não compete &nbsp;&middot;&nbsp; corpo inteiro, "
                 "sete exercícios &nbsp;&middot;&nbsp; a semana de carregar",
    "rotulo_carga": "CARGA",
    "larguras": [200, 46, 44, 44],
    "abertura":
        "<b>Enquanto o elenco que compete afina, vocês carregam.</b> É exatamente "
        "para isto que serve a semana de quem não joga: é a única janela em que dá "
        "para treinar pesado sem pagar no fim de semana. Sete exercícios, corpo "
        "inteiro, 25 séries. <b>Quem é do sub-19 lê a caixa verde do verso antes "
        "de carregar a barra</b> — a ficha é a mesma, a carga não.",
    "aquecimento_titulo": "Aquecimento — rampa antes do agachamento",
    "aquecimento_nota": "A 80% a primeira série não pode ser fria. A rampa sobe "
                        "até perto da carga e para.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta leve e mobilidade de tornozelo, quadril e torácica",
         "10 min", "a do app, sem cansar"],
        ["Rotadores externos com elástico", "2 × 12", "antes do supino"],
        ["Rampa: 40%, 60% e 75% do agachamento", "5, 3 e 2", "2 min entre elas"],
    ],
    "exercicios": [
        ("Agachamento",
         "força &middot; perna — a profundidade de sempre",
         "4 × 5", "3 min", "80%"),
        ("Supino reto com barra",
         "força &middot; empurrar horizontal — com ajudante",
         "4 × 5", "2,5 min", "80%"),
        ("Levantamento terra",
         "força &middot; dobra de quadril — cada repetição do chão",
         "4 × 5", "3 min", "RIR 2"),
        ("Remada curvada com barra",
         "força &middot; puxar horizontal — tronco PARADO",
         "4 × 6", "2 min", "78%"),
        ("Desenvolvimento com barra",
         "força &middot; empurrar vertical — SEM perna",
         "3 × 6", "2 min", "6RM"),
        ("Avanço com barra",
         "força &middot; unilateral — 6 em CADA perna",
         "3 × 6", "2 min", "RIR 2"),
        ("Prancha com remada",
         "core &middot; 8 em CADA braço — quadril parado",
         "3 × 8", "60 s", "RIR 3"),
    ],
    "nota_tabela":
        "Agachamento, supino e remada curvada saem da tabela de 1RM. "
        "<b>Quem não tem 1RM lançado — que é o caso da maioria do sub-19 — usa a "
        "carga de 8 repetições e faz 5</b>; dá quase o mesmo que 80%, com margem. "
        "No terra, no avanço e na prancha vai por repetições na reserva. "
        "<b>Anote os dois lados no avanço e na prancha.</b>",
    "caixa_duracao":
        "<b>Duração prevista: 75 a 90 minutos</b> — 25 séries, quatro delas com "
        "3 minutos de pausa. <b>Com menos de 65 minutos:</b> desenvolvimento e "
        "avanço em 2 séries. Não corte o agachamento nem o terra — são eles que "
        "fazem a semana valer.",
    "verso": [
        ("caixa", "<b>Sub-19: a ficha é a mesma, a carga não.</b> Onde está 80%, "
                  "use <b>75%</b>; onde está RIR 2, pare com <b>3 repetições na "
                  "reserva</b>. E a regra que vale mais que qualquer percentual: "
                  "<b>se a quinta repetição tem forma diferente da primeira, a "
                  "carga está alta</b>, mesmo que o número da planilha diga que "
                  "não. Nenhuma tentativa de máximo nesta semana — nem por "
                  "curiosidade.", VERDE_CLARO, VERDE),
        ("espaco", 3),
        ("h", "Por que esta ordem"),
        ("grade", ["", "O QUE", "POR QUE AQUI"], [
            ["1º e 2º", "Agachamento e supino",
             "os dois mais pesados, com a perna e o peito inteiros. O supino "
             "entra entre o agachamento e o terra <b>de propósito</b>: é a pausa "
             "que a lombar precisa"],
            ["3º", "Levantamento terra",
             "a segunda carga de lombar do dia, depois de uma folga dela. Cada "
             "repetição começa parada no chão"],
            ["4º e 5º", "Remada curvada e desenvolvimento",
             "puxar e empurrar com carga menor, quando a técnica dos grandes já "
             "foi gasta"],
            ["6º e 7º", "Avanço e prancha com remada",
             "unilateral e core no fim, que é quando a diferença entre os dois "
             "lados aparece"],
        ], [0.12, 0.30, 0.58]),
        ("espaco", 3),
        ("h", "Os exercícios"),
        ("notas", [
            ("Agachamento e terra", "<b>Os dois a 4 × 5 no mesmo dia pedem "
             "respeito pela lombar.</b> No agachamento, profundidade igual à de "
             "sempre. No terra, <b>cada repetição começa do chão, do zero</b> — "
             "emendar com a lombar cansada é onde a coluna arredonda, e "
             "<b>lombar arredondou, a série acabou</b>."),
            ("Supino e desenvolvimento", "<b>Supino com alguém na barra.</b> No "
             "desenvolvimento, <b>sem impulso de perna</b>: se o joelho dobra, "
             "virou push press. Glúteo e abdômen apertados para a lombar não "
             "arquear."),
            ("Remada curvada", "<b>Tronco entre 15° e 30° acima da horizontal, e "
             "PARADO.</b> A barra vem ao umbigo. O erro é levantar o tronco para "
             "a barra subir — aí a carga está alta demais e o exercício virou "
             "meio levantamento terra."),
            ("Avanço e prancha", "<b>Avanço:</b> uma repetição é um passo à frente "
             "e a volta, com a mesma perna; seis assim, depois troca. Joelho de "
             "trás descendo em direção ao chão, tronco em pé. <b>Prancha com "
             "remada:</b> o que conta não é a remada, é o <b>quadril não girar</b> "
             "— se ele roda, diminua a carga. Nos dois, comece pelo lado mais "
             "fraco."),
        ]),
        ("espaco", 2),
        ("caixa", "<b>A conta: 11 séries de perna, 7 de empurrar, 7 de puxar.</b> "
                  "É o equilíbrio que uma sessão de corpo inteiro deve ter, e é "
                  "por isso que esta ficha é a base do bloco — as outras da pasta "
                  "pendem para um lado ou outro de propósito, esta não."),
        ("espaco", 2),
    ],
}

# ════════════════════════════════════════════════════════════════════════════
# OS TRÊS DIAS — a última carga, e o mapa até o segundo jogo
# ════════════════════════════════════════════════════════════════════════════
# Com dois jogos, o afunilamento deixa de proteger o primeiro e passa a proteger
# o SEGUNDO, que é onde a fadiga acumulada aparece. Por isso a sessão de hoje é
# mais leve do que um D-3 normal pediria: 12 séries, nada até a falha. O verso é
# o mapa dos três dias e do intervalo entre os dois jogos.
TRES_DIAS = {
    "arquivo": "ELASE-tres-dias.pdf",
    "meta_titulo": "ELASE - Os tres dias ate a competicao",
    "meta_assunto": "Ultima carga em D-3 e o mapa ate o segundo jogo",
    "titulo": "Os três dias",
    "titulo_verso": "O mapa até o segundo jogo",
    "protocolo": "Quarta, 11/11 &nbsp;&middot;&nbsp; a última carga antes do jogo "
                 "&nbsp;&middot;&nbsp; 12 séries, nada até a falha",
    "rotulo_carga": "CARGA",
    "larguras": [200, 46, 44, 44],
    "abertura":
        "<b>Hoje é o último dia em que carga ainda cabe.</b> A 80% e três "
        "repetições, a fadiga some em cerca de 48 horas — dá tempo. A partir de "
        "amanhã não dá mais, e o que for feito aparece no jogo. <b>São dois "
        "jogos, e isso muda o alvo:</b> o afunilamento deixa de proteger o "
        "primeiro e passa a proteger o <b>segundo</b>, que é onde a fadiga "
        "acumulada aparece. Por isso esta sessão é mais leve do que um D-3 "
        "normal pediria.",
    "aquecimento_titulo": "Aquecimento — rampa curta, porque a sessão é curta",
    "aquecimento_nota": "A rampa sobe até perto de 80% e para. Nada de série "
                        "extra: hoje o aquecimento é a maior parte do volume.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta leve e mobilidade de tornozelo, quadril e torácica",
         "10 min", "a do app, sem cansar"],
        ["Rotadores externos com elástico", "2 × 12", "antes do supino"],
        ["Rampa: 45%, 60% e 72% do agachamento", "5, 3 e 2", "2 min entre elas"],
    ],
    "exercicios": [
        ("Agachamento",
         "carga &middot; perna — 3 repetições, nenhuma difícil",
         "3 × 3", "3 min", "80%"),
        ("Agachamento com salto com peso",
         "potência &middot; perna — acima de 1,0 m/s",
         "3 × 4", "2 min", "25%"),
        ("Supino saindo do peito",
         "potência &middot; empurrar — barra PARADA no peito",
         "3 × 3", "2,5 min", "60%"),
        ("Remada curvada com barra",
         "carga &middot; puxar — tronco PARADO",
         "3 × 4", "2 min", "75%"),
    ],
    "nota_tabela":
        "Os quatro saem da sua tabela de 1RM. <b>Nenhuma série vai até a falha, "
        "nem perto dela</b> — se a terceira repetição do agachamento parecer "
        "difícil, tire peso na série seguinte. Hoje a carga certa é a que você "
        "faria mais duas vezes sem mudar nada. <b>Não tente subir nenhuma carga "
        "hoje.</b>",
    "caixa_duracao":
        "<b>Duração prevista: 40 a 45 minutos</b> — 12 séries, e acabou. "
        "<b>Se a quadra de hoje for pesada, faça só o agachamento e o supino</b>, "
        "em 2 séries cada. Entre a sala e a quadra, quem decide é a quadra: "
        "faltando três dias, nenhuma série de sala vale um treino tático ruim.",
    "verso": [
        ("h", "Dia a dia, da quarta ao domingo"),
        ("grade", ["QUANDO", "SALA", "POR QUÊ"], [
            ["<b>Quarta 11/11</b><br/>hoje, D-3",
             "<b>esta ficha</b> — 12 séries, nada até a falha",
             "é a última carga que dá tempo de ir embora. A 80% em 3 repetições, "
             "a fadiga some em ~48 h"],
            ["<b>Quinta 12/11</b><br/>D-2",
             "<b>nada</b>, ou só os dois arremessos de medicine ball",
             "o corpo já não ganha nada aqui — só pode perder. Quadra normal, "
             "sala fechada"],
            ["<b>Sexta 13/11</b><br/>D-1",
             "<b>Pré-competição</b> — 13 séries, 30 min",
             "acorda o braço sem cansar. <b>Se a quadra de sexta for pesada, "
             "pule</b>: a ficha é opcional, o descanso não"],
            ["<b>Sábado 14/11</b><br/>jogo 1",
             "nada além do aquecimento do jogo",
             "—"],
            ["<b>Entre os dois jogos</b>",
             "caminhada leve, mobilidade, <b>zero sala</b>",
             "o segundo jogo é onde a fadiga aparece. Tudo o que for feito aqui "
             "sai do saque e do bloqueio de domingo"],
        ], [0.18, 0.32, 0.50]),
        ("espaco", 3),
        ("caixa", "<b>Dois jogos mudam o alvo.</b> Com um jogo só, o afunilamento "
                  "chega afiado no sábado e o que vier depois não importa. Com "
                  "dois, o que importa é chegar <b>inteiro no domingo</b> — e aí "
                  "o erro caro deixa de ser treinar de menos e passa a ser "
                  "treinar de mais. <b>Na dúvida, em qualquer um dos três dias, "
                  "faça menos.</b>", AMBAR_CLARO, AMBAR),
        ("espaco", 3),
        ("h", "O que não fazer nestes três dias"),
        ("notas", [
            ("Nada de máximo, nada de novo", "<b>Nenhuma tentativa de 1RM, nenhum "
             "exercício que você não conheça e nenhuma excêntrica lenta.</b> "
             "Carga máxima cobra no sistema nervoso por 48 a 72 horas; exercício "
             "novo e descida lenta deixam dor muscular. Os três aparecem "
             "exatamente no fim de semana."),
            ("Nada de “recuperar” treino perdido", "Quem faltou nas "
             "últimas semanas <b>não compensa agora</b> — faz esta mesma sessão, "
             "igual aos outros. Três dias antes de competir, treino atrasado é "
             "prejuízo, não investimento."),
            ("O sono é o treino destes três dias", "O que ainda dá para melhorar "
             "até sábado não está na sala: está em <b>dormir uma hora a mais</b> "
             "nas três noites e em comer normalmente. É o único ganho disponível "
             "neste prazo — e é um ganho real."),
            ("Se alguém chegar dolorido", "<b>Avise a comissão antes de treinar</b>, "
             "não depois. Dor muscular hoje significa que a semana passada "
             "cobrou, e aí esta sessão vira 2 séries de agachamento e mais nada."),
        ]),
        ("espaco", 2),
    ],
}


EXPLOSIVO_ROTACIONAL = {
    "arquivo": "ELASE-explosivo-rotacional.pdf",
    "meta_titulo": "ELASE - Explosivo e rotacional",
    "meta_assunto": "Tres barras explosivas, puxada fechada e fluxo unilateral",
    "titulo": "Explosivo e rotacional",
    "titulo_verso": "O fluxo, os 30% e a regra da série",
    "protocolo": "Quatro exercícios entre 30 e 60% &nbsp;&middot;&nbsp; a barra "
                 "decide a série &nbsp;&middot;&nbsp; 23 séries",
    "rotulo_carga": "CARGA",
    "larguras": [190, 52, 44, 46],
    "abertura":
        "<b>Esta sessão é explosiva, não pesada:</b> quatro exercícios entre 30 "
        "e 60% e um fluxo de coordenação. Nenhuma carga alta. <b>Para quem não "
        "compete</b> — o sub-19 e os quatro do adulto — ela serve já. <b>Para "
        "quem joga sábado e domingo ainda não cabe nestes três dias:</b> trocar "
        "o remo pela puxada deixou a sessão mais leve, mas são <b>23 séries</b> "
        "contra as 12 da ficha <i>Os três dias</i> — volume demais para D-2 e "
        "D-1. Para esses, é a sessão de <b>volta</b>, na segunda ou terça depois "
        "dos dois jogos.",
    "aquecimento_titulo": "Aquecimento — o quadril e o tronco antes da barra",
    "aquecimento_nota": "Metade da sessão é dobra de quadril e a outra metade é "
                        "rotação. O aquecimento prepara as duas, e a rampa do "
                        "clean vale mais que as outras: é o movimento mais "
                        "técnico do dia.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou corda leve e mobilidade de quadril e torácica",
         "10 min", "a do app"],
        ["Rotação no cabo, carga mínima", "2 × 10 cada lado", "acorda o tronco"],
        ["Barra vazia: stiff, remada e clean do meio da coxa",
         "8 de cada", "o padrão antes da carga"],
        ["Rampa do clean: 15% e 25%", "3 e 3", "rápido, não forte"],
    ],
    "exercicios": [
        ("Remada curvada explosiva",
         "explosivo &middot; puxar — a barra decide a série",
         "4 × 5", "2 min", "55%"),
        ("Clean explosivo",
         "explosivo &middot; corpo todo — 30% é velocidade, ver o verso",
         "5 × 3", "2 min", "30%"),
        ("Stiff explosivo",
         "explosivo &middot; posterior — sobe rápido, desce no controle",
         "4 × 5", "2 min", "50%"),
        ("Puxada fechada",
         "explosivo &middot; puxar vertical — volta no controle",
         "4 × 5", "2 min", "60%"),
        ("Rotação no cabo",
         "rotação &middot; 6 de cada lado, soltando rápido",
         "3 × 6", "1 min", "média"),
        ("Fluxo unilateral com halteres",
         "combinado &middot; 4 ciclos em CADA lado — ver o verso",
         "3 × 4", "90 s", "leve"),
    ],
    "nota_tabela":
        "<b>Quatro dos seis saem da sua tabela de 1RM:</b> remada curvada, "
        "clean, stiff e puxada fechada. <b>A rotação e o fluxo não têm "
        "referência</b> — na rotação, a carga certa é a maior com que você ainda "
        "solta o movimento <b>rápido</b> nas seis repetições; no fluxo, halteres "
        "leves, 6 a 10 kg, porque ali o que limita é o equilíbrio e não a força.",
    "caixa_duracao":
        "<b>Duração prevista: 55 a 70 minutos</b> — 23 séries. <b>Se o tempo "
        "apertar, corte a rotação no cabo</b> (o exercício 5): é o menor bloco "
        "do dia e o único que você repõe em qualquer outra sessão da semana. "
        "<b>Não corte o fluxo</b> — ele é o único trabalho de controle do dia.",
    "verso": [
        ("h", "O fluxo unilateral, movimento por movimento"),
        ("grade", ["MOVIMENTO", "COMO SE FAZ", "O QUE ELE COBRA"], [
            ["<b>1. Stiff unilateral</b>",
             "em pé sobre uma perna, os halteres descem pela frente da canela, o "
             "tronco vai até perto do paralelo e a perna livre estende atrás. "
             "Volta em pé.",
             "equilíbrio de quadril e posterior da perna de apoio"],
            ["<b>2. Agachamento lateral</b>",
             "da posição em pé, um passo largo para o lado <b>dessa mesma "
             "perna</b>, senta nesse quadril com o outro joelho estendido e "
             "volta ao centro.",
             "adutor e amplitude de quadril no plano de lado"],
            ["<b>3. Desenvolvimento</b>",
             "de volta ao centro, os dois halteres sobem acima da cabeça, tronco "
             "firme, <b>sem arquear a lombar</b> para ajudar.",
             "ombro e, principalmente, o tronco que acabou de ser desequilibrado"],
        ], [0.22, 0.46, 0.32]),
        ("espaco", 3),
        ("caixa", "<b>Um ciclo são os três em sequência, sem apoiar os halteres "
                  "no chão.</b> Quatro ciclos no mesmo lado, depois troca e faz "
                  "quatro do outro — isso é <b>uma</b> série. São três séries. "
                  "Se o equilíbrio falhar no terceiro ciclo, a carga está alta: "
                  "aqui halter mais leve é progresso, não recuo.",
                  VERDE_CLARO, VERDE),
        ("espaco", 3),
        ("h", "Explosivo muda a regra da série"),
        ("notas", [
            ("Quem encerra a série é a barra", "Nas três barras explosivas "
             "<b>a série acaba quando a barra fica lenta</b>, não quando a "
             "repetição fica difícil. Se a quinta saiu visivelmente mais devagar "
             "que a primeira, pare na quarta na série seguinte — mesma regra da "
             "ficha <i>Velocidade</i>. Treinar devagar com carga leve não treina "
             "nada: não é forte o bastante para carga nem rápido o bastante para "
             "potência."),
            ("Por que 30% no clean", "Trinta por cento é <b>abaixo</b> da faixa "
             "em que o clean produz mais potência, que fica entre 60 e 70%. A "
             "30% a barra quase não tem massa: o exercício vira <b>velocidade e "
             "padrão de movimento</b>, e o limite passa a ser a rapidez com que "
             "você puxa, não o quanto. É uma escolha boa para uma semana em que "
             "a carga nervosa tem de ficar baixa — e é a escolha errada se o que "
             "se quer é potência de pico. Se o objetivo virar potência, suba "
             "para 60-65% e mantenha as 3 repetições."),
            ("Três dobras de quadril seguidas", "Remada curvada, clean e stiff "
             "carregam a lombar na mesma posição de dobra, um atrás do outro. "
             "<b>Mantive a sua ordem</b> porque a 30-55% isso é tranquilo; a "
             "85% eu teria separado. Mesmo assim: no primeiro sinal de lombar "
             "arredondando no stiff, a sessão termina ali, nos exercícios 4 a 6."),
            ("Quem vai falhar primeiro é a pegada", "Com a puxada no lugar do "
             "remo, o dia soma <b>55 repetições de puxar</b> — 20 na remada "
             "curvada, 15 no clean e 20 na puxada fechada. A pegada cede antes "
             "das costas, e aí a série acaba por um motivo que não é o que a "
             "gente queria treinar. <b>Na puxada fechada, use strap assim que a "
             "mão começar a abrir</b>: sem ele o exercício vira treino de "
             "antebraço. Na remada curvada e no clean, não — ali segurar a barra "
             "faz parte do movimento."),
        ]),
        ("espaco", 2),
    ],
}



STIFF_COMBINADOS = {
    "arquivo": "ELASE-stiff-combinados.pdf",
    "meta_titulo": "ELASE - Stiff em dois combinados",
    "meta_assunto": "Stiff com remada na polia e fluxo unilateral com halteres",
    "titulo": "Stiff em dois combinados",
    "titulo_verso": "Os dois, movimento por movimento",
    "protocolo": "Dois exercícios, cinco movimentos &nbsp;&middot;&nbsp; carga leve "
                 "&nbsp;&middot;&nbsp; 8 séries, 35 a 45 minutos",
    "rotulo_carga": "CARGA",
    "larguras": [190, 52, 44, 46],
    "abertura":
        "<b>São dois exercícios, mas cinco movimentos.</b> Nos dois o stiff é a "
        "base: no primeiro ele <b>segura</b> a posição enquanto a remada "
        "acontece dentro dela; no segundo ele <b>abre</b> uma sequência que "
        "continua no agachamento lateral e termina no desenvolvimento. É uma "
        "sessão curta e de controle, não de carga. <b>Combinado não é "
        "complexo:</b> aqui um movimento acontece <i>dentro</i> do outro, com "
        "carga leve, e o que se treina é controle sob fadiga local — na ficha "
        "<i>Três complexos</i> os exercícios são inteiros e em sequência, e na "
        "<i>Contraste</i> há 3 minutos entre o pesado e o explosivo. "
        "<b>Esta ficha não entra nos três dias até os jogos</b> — o motivo está "
        "no verso, e é o stiff unilateral. Serve já para o sub-19 e os quatro do "
        "adulto que não competem, e é uma boa sessão de volta depois do segundo "
        "jogo.",
    "aquecimento_titulo": "Aquecimento — o posterior e o ombro, que é o que os dois cobram",
    "aquecimento_nota": "O aquecimento aqui vale mais que o normal: os dois "
                        "exercícios são combinados, e combinado mal aquecido "
                        "quebra no movimento mais fraco da sequência.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou corda leve e mobilidade de quadril e torácica",
         "10 min", "a do app"],
        ["Ponte de glúteo e bird-dog", "2 × 10", "acorda o posterior"],
        ["Stiff com barra vazia", "2 × 8", "o padrão antes da polia"],
        ["Stiff unilateral sem carga, só equilíbrio", "2 × 5 cada lado",
         "aqui você descobre o lado pior"],
        ["Rotadores externos com elástico", "2 × 12", "antes do desenvolvimento"],
    ],
    "exercicios": [
        ("Stiff com remada na polia",
         "combinado &middot; a remada acontece DENTRO do stiff",
         "4 × 8", "90 s", "média"),
        ("Fluxo unilateral com halteres",
         "combinado &middot; 4 ciclos em CADA lado — ver o verso",
         "4 × 4", "90 s", "leve"),
    ],
    "nota_tabela":
        "<b>Nenhum dos dois sai da tabela de 1RM</b>, e nem deveria: em "
        "movimento combinado quem manda na carga é o <b>elo mais fraco da "
        "sequência</b>, não o mais forte. Na polia, a carga certa é a maior com "
        "que você mantém o tronco parado nas oito remadas — se o tronco sobe "
        "junto, está pesado. No fluxo, halteres de 6 a 10 kg: quem limita ali é "
        "o equilíbrio na perna de apoio e o desenvolvimento no fim, nunca o "
        "stiff do começo.",
    "caixa_duracao":
        "<b>Duração prevista: 35 a 45 minutos</b> — 8 séries, e é curta de "
        "propósito. <b>Se sobrar tempo e vontade, não acrescente exercício: "
        "acrescente uma série em cada um</b> e faça as repetições mais devagar. "
        "O ganho destes dois está na qualidade de cada ciclo, não no número "
        "deles — é a mesma lógica da ficha <i>Regenerativo</i>.",
    "verso": [
        ("h", "1. Stiff com remada na polia"),
        ("grade", ["O QUE FAZER", "COMO", "O ERRO QUE APARECE"], [
            ["<b>A posição</b><br/>é ela que faz o exercício",
             "de frente para a polia baixa, pegada nas duas mãos. Dobra o "
             "quadril até o tronco ficar perto do paralelo, joelhos pouco "
             "dobrados, coluna reta. <b>Fica nessa posição o resto da série.</b>",
             "subir o tronco entre uma remada e outra — aí vira remada curvada "
             "comum e o posterior sai do exercício"],
            ["<b>As 8 remadas</b><br/>é o que se move",
             "sem sair da posição, puxa a polia até perto do umbigo e volta no "
             "controle. Oito vezes. Só os braços e as escápulas se movem.",
             "puxar com o braço e deixar a escápula parada — o movimento começa "
             "na escápula e só depois dobra o cotovelo"],
            ["<b>A volta</b>",
             "só depois da oitava remada o quadril estende e você fica em pé. "
             "Descansa 90 s em pé.",
             "soltar a posição no meio da série. Se precisar disso, a carga "
             "está alta"],
        ], [0.24, 0.42, 0.34]),
        ("espaco", 3),
        ("h", "2. Fluxo unilateral com halteres"),
        ("grade", ["MOVIMENTO", "COMO SE FAZ", "O QUE ELE COBRA"], [
            ["<b>1. Stiff unilateral</b>",
             "sobre uma perna, os halteres descem pela frente da canela, tronco "
             "até perto do paralelo, perna livre estendida atrás.",
             "equilíbrio de quadril e posterior da perna de apoio"],
            ["<b>2. Agachamento lateral</b>",
             "de pé, um passo largo para o lado <b>dessa mesma perna</b>, senta "
             "nesse quadril com o outro joelho estendido e volta ao centro.",
             "adutor e amplitude de quadril no plano de lado"],
            ["<b>3. Desenvolvimento</b>",
             "no centro, os dois halteres sobem acima da cabeça, tronco firme, "
             "<b>sem arquear a lombar</b> para ajudar.",
             "ombro e o tronco que acabou de ser desequilibrado"],
        ], [0.22, 0.44, 0.34]),
        ("espaco", 3),
        ("caixa", "<b>Um ciclo são os três em sequência, sem apoiar os halteres "
                  "no chão.</b> Quatro ciclos num lado, troca, quatro do outro — "
                  "isso é <b>uma</b> série, e são quatro. Se o equilíbrio falhar "
                  "no terceiro ciclo, use halter mais leve.",
                  VERDE_CLARO, VERDE),
        ("espaco", 2),
        ("h", "Por que esta ficha fica fora dos três dias"),
        ("notas", [
            ("O stiff unilateral é o campeão de dor tardia", "De tudo o que há "
             "nas suas fichas, <b>é o que mais produz dor muscular nos dias "
             "seguintes</b>: excêntrica de isquiotibial numa perna só, com "
             "amplitude grande. E a dor não chega no mesmo dia: "
             "<b>ela aparece 24 a 48 horas depois</b>. Feita amanhã, cai em cima "
             "do jogo de sábado; feita na sexta, cai no de domingo. O problema "
             "aqui não é o cansaço — é o atraso."),
            ("O fluxo se repete na ficha Explosivo e rotacional", "É o mesmo "
             "exercício 6 de lá. Se as duas fichas rodarem na mesma semana, ele "
             "aparece duas vezes — <b>o que está bom nesta carga</b>, porque ele "
             "é coordenação e não força. Só não coloque numa terceira: ele rende "
             "frequente e leve, e para de render quando vira volume."),
            ("Anote o lado pior", "No aquecimento dá para sentir qual perna "
             "segura menos o stiff unilateral. <b>Anote qual é</b> e mande com a "
             "PSE: diferença entre lados é a informação mais útil que esta sessão "
             "produz."),
        ]),
        ("espaco", 1),
    ],
}



EXPLOSIVO_COMBINADO = {
    "arquivo": "ELASE-explosivo-combinado.pdf",
    "meta_titulo": "ELASE - Explosivo e combinado",
    "meta_assunto": "Quatro barras explosivas, rotacao e os dois combinados",
    "titulo": "Explosivo e combinado",
    "titulo_verso": "Os combinados e o que decide cada série",
    "protocolo": "Sete exercícios, dez movimentos &nbsp;&middot;&nbsp; a barra "
                 "decide a série &nbsp;&middot;&nbsp; 28 séries",
    "rotulo_carga": "CARGA",
    "larguras": [190, 52, 44, 46],
    "abertura":
        "<b>As duas fichas viraram uma</b>, e o fluxo, que aparecia nas duas, "
        "entra uma vez só: <b>28 séries, 75 a 85 minutos</b>. <b>Repare nos três "
        "stiffs</b> — o explosivo (3), o sustentado na polia (6) e o unilateral "
        "do fluxo (7) — mais a remada curvada (1), que também segura a dobra de "
        "quadril. É o teto de posterior num dia só; a caixa amarela diz o que "
        "cortar. <b>Não entra nos três dias até os jogos</b>, pelo motivo do verso.",
    "aquecimento_titulo": "Aquecimento — quadril, tronco e ombro, porque o dia cobra os três",
    "aquecimento_nota": "A rampa do clean vale mais que as outras: é o movimento "
                        "mais técnico do dia, e é o único que fica pior quando "
                        "entra frio.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou corda, mobilidade de quadril e torácica, rotadores "
         "com elástico", "12 min", "a do app, mais o ombro"],
        ["Barra vazia: stiff, remada e clean do meio da coxa", "8 de cada",
         "o padrão antes da carga"],
        ["Stiff unilateral sem carga e rampa do clean a 15% e 25%",
         "5 cada lado, 3 e 3", "aqui aparece o lado pior"],
    ],
    "exercicios": [
        ("Remada curvada explosiva",
         "explosivo &middot; puxar — a barra decide a série",
         "4 × 5", "2 min", "55%"),
        ("Clean explosivo",
         "explosivo &middot; corpo todo — 30% é velocidade",
         "5 × 3", "2 min", "30%"),
        ("Stiff explosivo",
         "explosivo &middot; posterior — sobe rápido, desce controlado",
         "4 × 5", "2 min", "50%"),
        ("Puxada fechada",
         "explosivo &middot; puxar vertical — volta no controle",
         "4 × 5", "2 min", "60%"),
        ("Rotação no cabo",
         "rotação &middot; 6 de cada lado, soltando rápido",
         "3 × 6", "1 min", "média"),
        ("Stiff com remada na polia",
         "combinado &middot; a remada acontece DENTRO do stiff",
         "4 × 8", "90 s", "média"),
        ("Fluxo unilateral com halteres",
         "combinado &middot; 4 ciclos em CADA lado — ver o verso",
         "4 × 4", "90 s", "leve"),
    ],
    "nota_tabela":
        "<b>Quatro dos sete saem da tabela de 1RM:</b> remada curvada, clean, "
        "stiff e puxada. Nos outros três manda o <b>elo mais fraco</b> — na "
        "rotação, a maior carga que ainda sai rápido; na polia, a maior com que "
        "o tronco fica parado nas oito remadas; no fluxo, 6 a 10 kg.",
    "caixa_duracao":
        "<b>Duração prevista: 75 a 85 minutos</b> — 28 séries. <b>Versão curta, "
        "se não couber:</b> tire a rotação (5) e baixe o stiff explosivo (3) para "
        "2 séries — ficam 23 séries em ~60 min, sem perder exercício nenhum. "
        "<b>Não corte o fluxo nem a puxada.</b>",
    "verso": [
        ("h", "6. Stiff com remada na polia"),
        ("grade", ["O QUE FAZER", "COMO", "O ERRO QUE APARECE"], [
            ["<b>A posição</b><br/>é ela que faz o exercício",
             "de frente para a polia baixa. Dobra o quadril até o tronco ficar "
             "perto do paralelo, joelhos pouco dobrados, coluna reta. <b>Fica "
             "assim o resto da série.</b>",
             "subir o tronco entre uma remada e outra — aí vira remada curvada e "
             "o posterior sai do exercício"],
            ["<b>As 8 remadas</b><br/>é o que se move",
             "sem sair da posição, puxa até perto do umbigo e volta no controle. "
             "Só braços e escápulas se movem.",
             "puxar com o braço e deixar a escápula parada"],
            ["<b>A volta</b>",
             "só depois da oitava o quadril estende. Descansa 90 s em pé.",
             "soltar a posição no meio da série. Se precisar, a carga está alta"],
        ], [0.24, 0.42, 0.34]),
        ("espaco", 2),
        ("h", "7. Fluxo unilateral com halteres"),
        ("grade", ["MOVIMENTO", "COMO SE FAZ", "O QUE ELE COBRA"], [
            ["<b>1. Stiff unilateral</b>",
             "sobre uma perna, os halteres descem pela frente da canela, tronco "
             "até perto do paralelo, perna livre estendida atrás.",
             "equilíbrio de quadril e posterior da perna de apoio"],
            ["<b>2. Agachamento lateral</b>",
             "de pé, passo largo para o lado <b>dessa mesma perna</b>, senta "
             "nesse quadril com o outro joelho estendido, volta ao centro.",
             "adutor e amplitude de quadril no plano de lado"],
            ["<b>3. Desenvolvimento</b>",
             "no centro, os halteres sobem acima da cabeça, <b>sem arquear a "
             "lombar</b> para ajudar.",
             "ombro e o tronco que acabou de ser desequilibrado"],
        ], [0.22, 0.44, 0.34]),
        ("espaco", 2),
        ("caixa", "<b>Um ciclo são os três em sequência, sem apoiar os halteres.</b> "
                  "Quatro ciclos num lado, troca, quatro do outro — isso é "
                  "<b>uma</b> série, e são quatro. <b>Ele cai em último, com 24 "
                  "séries nas pernas antes.</b> Equilíbrio é a primeira coisa que "
                  "a fadiga tira: aqui halter mais leve do que você usaria "
                  "descansado, não mais pesado.", VERDE_CLARO, VERDE),
        ("espaco", 2),
        ("h", "O que decide cada série"),
        ("notas", [
            ("Nas quatro primeiras, quem encerra é a barra", "<b>A série acaba "
             "quando a barra fica lenta</b>, não quando a repetição fica difícil "
             "— mesma regra da ficha <i>Velocidade</i>. E os 30% do clean são "
             "<b>abaixo</b> da faixa de maior potência, que fica em 60-70%: a "
             "essa carga o exercício treina velocidade e padrão, não potência. "
             "Se o alvo virar potência, suba para 60-65% mantendo 3 repetições."),
            ("Três stiffs e uma remada curvada no mesmo dia", "Os quatro carregam "
             "o posterior na mesma posição de dobra. A 30-60% isso passa, mas é "
             "o <b>teto</b> do que cabe numa sessão: <b>não acrescente nenhum "
             "outro exercício de quadril aqui</b>, e no primeiro sinal de lombar "
             "arredondando no stiff da polia, encerre esse exercício e vá para o "
             "fluxo."),
            ("Por que a ficha fica fora dos três dias", "Não é pela carga, é pelo "
             "atraso. O stiff unilateral do fluxo é excêntrica de isquiotibial "
             "numa perna só — o que mais produz dor muscular tardia — e o pico "
             "dela chega <b>24 a 48 horas depois</b>. Feita amanhã, cai em cima "
             "do jogo de sábado; feita na sexta, cai no de domingo. Serve já para "
             "o sub-19 e os quatro do adulto que não competem, e é uma boa sessão "
             "de volta depois do segundo jogo."),
        ]),
        ("espaco", 1),
    ],
}



POTENCIA_VELOCIDADE = {
    "arquivo": "ELASE-potencia-velocidade.pdf",
    "meta_titulo": "ELASE - Potencia e velocidade",
    "meta_assunto": "Seis exercicios entre 50 e 65 por cento, barra rapida",
    "titulo": "Potência e velocidade",
    "titulo_verso": "Quem treina o quê, e a ordem que eu mudaria",
    "protocolo": "Quinta, 12/11 &nbsp;&middot;&nbsp; 4 × 6-8 em todos, entre 50 "
                 "e 55% &nbsp;&middot;&nbsp; a barra decide a série",
    "rotulo_carga": "CARGA",
    "larguras": [190, 52, 44, 46],
    "abertura":
        "<b>As 6-8 repetições mudam o que esta sessão é.</b> Com 3 a 5 ela era "
        "potência de pico; com 6 a 8 vira <b>potência sustentada</b> — são 168 "
        "repetições contra as 96 da versão anterior, 75% a mais. <b>Completa, "
        "ela não cabe mais hoje</b>, a dois dias do jogo. Quem joga sábado faz a "
        "versão da caixa amarela e não faz a <i>Pré-competição</i> amanhã. "
        "<b>Para o sub-19 e os quatro que não competem, ela roda completa.</b>",
    "aquecimento_titulo": "Aquecimento — mais longo que o normal, porque tudo aqui é rápido",
    "aquecimento_nota": "Movimento rápido com músculo frio é onde as lesões "
                        "acontecem. A rampa do clean é a mais importante: é o "
                        "único exercício do dia que piora quando entra frio.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Bicicleta ou corda, mobilidade de quadril e torácica, rotadores "
         "com elástico", "12 min", "a do app, mais o ombro"],
        ["Barra vazia: supino, stiff, remada e clean do meio da coxa",
         "8 de cada", "o padrão antes da carga"],
        ["Rampa do clean: 35% e 50%", "3 e 3", "rápido, não forte"],
    ],
    "exercicios": [
        ("Supino",
         "velocidade &middot; barra PARADA no peito, sobe rápido",
         "4 × 6-8", "2,5 min", "50%"),
        ("Stiff",
         "velocidade &middot; sobe rápido, desce controlado",
         "4 × 6-8", "2 min", "50%"),
        ("Remada curvada",
         "velocidade &middot; tronco PARADO, a barra é que corre",
         "4 × 6-8", "2 min", "55%"),
        ("Clean",
         "potência &middot; 50%, não 65% — o motivo está no verso",
         "4 × 6-8", "3 min", "50%"),
        ("Desenvolvimento com halteres",
         "potência &middot; sobe rápido, desce em 2 tempos",
         "4 × 6-8", "2 min", "média"),
        ("Puxada fechada na polia",
         "velocidade &middot; puxa rápido, volta no controle",
         "4 × 6-8", "2 min", "55%"),
    ],
    "nota_tabela":
        "<b>Cinco dos seis saem da tabela de 1RM</b> — supino, stiff, remada "
        "curvada, clean e puxada fechada. <b>O desenvolvimento com halteres não "
        "tem referência:</b> use o par com que você faz 8 repetições rápidas e "
        "ainda faria mais 2. <b>6 a 8 é teto, não meta:</b> se a sexta já sai "
        "devagar, a série acabou na sexta e está certo.",
    "caixa_duracao":
        "<b>Completa: 75 a 85 minutos, 24 séries, 168 repetições.</b> "
        "<b>Versão D-2, para quem joga sábado: 2 séries de 6 em cada</b>, sem "
        "chegar nas 8 — 12 séries, 40 minutos, as mesmas cargas. A dois dias do "
        "jogo a faixa 6-8 vira 6 fixo: é a repetição extra que cobra, não a "
        "carga. <b>Quem fizer a versão curta não faz a Pré-competição amanhã.</b>",
    "verso": [
        ("h", "Potência e velocidade não são a mesma coisa"),
        ("grade", ["EXERCÍCIO", "O QUE ELE TREINA AQUI", "O QUE ENCERRA A SÉRIE"], [
            ["<b>1. Supino</b> &middot; 50%",
             "velocidade de empurrar. A barra para no peito e sai sem embalo",
             "quando a subida fica visivelmente mais lenta"],
            ["<b>2. Stiff</b> &middot; 50%",
             "velocidade de quadril. A subida é rápida, a descida não",
             "quando o quadril para de estalar para cima"],
            ["<b>3. Remada curvada</b> &middot; 55%",
             "velocidade de puxar. O tronco não se mexe",
             "quando o tronco começa a ajudar a puxada"],
            ["<b>4. Clean</b> &middot; 50%",
             "<b>potência sustentada</b> — não é a faixa de pico, ver abaixo",
             "quando a barra para de subir até a clavícula"],
            ["<b>5. Desenvolvimento</b> &middot; média",
             "<b>potência</b> de ombro, com os dois lados independentes",
             "quando um braço chega depois do outro"],
            ["<b>6. Puxada fechada</b> &middot; 55%",
             "velocidade de puxar vertical, sem balanço de tronco",
             "quando você precisa jogar o corpo para trás"],
        ], [0.22, 0.44, 0.34]),
        ("espaco", 2),
        ("caixa", "<b>A ordem que eu mudaria:</b> o clean em primeiro. Ele está "
                  "em quarto, depois do stiff e da remada curvada, que cansam o "
                  "posterior e a pegada de que ele depende — e com <b>6 a 8</b> "
                  "repetições esses dois cansam bem mais do que cansavam com 4. "
                  "Se puder trocar, a ordem vira <b>4-1-2-3-5-6</b>. Mantive a "
                  "sua na tabela porque a escolha é sua.",
                  AMBAR_CLARO, AMBAR),
        ("espaco", 2),
        ("h", "Três coisas para fechar"),
        ("notas", [
            ("Por que o clean desceu de 65% para 50%", "A faixa de maior "
             "potência do clean, 60 a 70%, <b>vale para 1 a 3 repetições</b>. "
             "Esticada para 6-8 ela tem de descer, porque <b>oito cleans a 65% "
             "deixam de ser clean lá pela quinta</b> — e no levantamento "
             "olímpico as repetições feias são justamente as últimas. Mantive as "
             "6-8 que você pediu e baixei a carga: a 50% com 6-8 o que se treina "
             "é <b>potência sustentada</b>, que é coisa diferente de potência de "
             "pico, e é o que a faixa de repetições que você escolheu entrega."),
            ("Nenhuma série vai até a falha", "Numa sessão de velocidade a falha "
             "não é só desnecessária — <b>ela é o oposto do exercício</b>. "
             "Repetição lenta com carga leve não treina nem carga nem potência: "
             "é tempo gasto a troco de fadiga. Quando a barra desacelera, a série "
             "acabou, mesmo que faltem repetições na folha."),
            ("A pegada vai falhar antes das costas", "Com 6-8, o dia soma <b>84 "
             "repetições de puxar</b> — 28 na remada curvada, 28 no clean e 28 "
             "na puxada. Eram 48 antes. <b>Strap na puxada fechada assim que a "
             "mão abrir</b>; na remada curvada e no clean, não, porque ali "
             "segurar a barra faz parte do movimento — nesses dois, se a pegada "
             "foi, a série acabou."),
        ]),
        ("espaco", 1),
    ],
}

FICHAS = {"forca": FORCA, "potencia": POTENCIA, "volei": FORCA_VOLEI,
          "onda": FORCA_ONDA, "potencia_barra": POTENCIA_BARRA,
          "registro": REGISTRO, "pliometria": PLIOMETRIA,
          "contraste": CONTRASTE, "corpo_inteiro": CORPO_INTEIRO,
          "tronco": TRONCO, "unilateral_salto": UNILATERAL_SALTO,
          "forca_a": FORCA_4X4_A, "forca_b": FORCA_4X4_B,
          "regenerativo": REGENERATIVO, "forca_2a3": FORCA_2A3,
          "quadril_frontal": QUADRIL_FRONTAL, "forca_90_95": FORCA_90_95,
          "puxar_unilateral": PUXAR_UNILATERAL,
          "complexos": COMPLEXOS,
          "velocidade": VELOCIDADE,
          "agilidade_posicao": AGILIDADE_POSICAO,
          "pre_competicao": PRE_COMPETICAO, "forca_completa": FORCA_COMPLETA,
          "tres_dias": TRES_DIAS,
          "explosivo_rotacional": EXPLOSIVO_ROTACIONAL,
          "stiff_combinados": STIFF_COMBINADOS,
          "explosivo_combinado": EXPLOSIVO_COMBINADO,
          "potencia_velocidade": POTENCIA_VELOCIDADE}


def main():
    pedidas = sys.argv[1:] or list(FICHAS)
    for nome in pedidas:
        if nome not in FICHAS:
            print("ficha desconhecida: %s (tenho: %s)" % (nome, ", ".join(FICHAS)))
            return 1
        gerar(FICHAS[nome])
    return 0


if __name__ == "__main__":
    sys.exit(main())
