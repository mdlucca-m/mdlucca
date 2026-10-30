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

FICHAS = {"forca": FORCA, "potencia": POTENCIA, "volei": FORCA_VOLEI,
          "onda": FORCA_ONDA, "potencia_barra": POTENCIA_BARRA,
          "registro": REGISTRO, "pliometria": PLIOMETRIA,
          "contraste": CONTRASTE, "corpo_inteiro": CORPO_INTEIRO,
          "tronco": TRONCO, "unilateral_salto": UNILATERAL_SALTO,
          "forca_a": FORCA_4X4_A, "forca_b": FORCA_4X4_B,
          "regenerativo": REGENERATIVO, "forca_2a3": FORCA_2A3,
          "quadril_frontal": QUADRIL_FRONTAL}


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
