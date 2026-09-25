#!/usr/bin/env python3
"""O conteúdo das fichas. O desenho está em fichas_treino.py.

    python3 fichas_conteudo.py            # gera todas
    python3 fichas_conteudo.py potencia   # gera uma
"""

import sys

from fichas_treino import AMBAR, AMBAR_CLARO, VERDE, VERDE_CLARO, gerar

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
    "arquivo": "ELASE-ativacao-potencia-dia-de-jogo.pdf",
    "meta_titulo": "ELASE - Ativacao de potencia (dia de jogo, so academia)",
    "meta_assunto": "Velocidade de movimento com carga baixa, sem salto e sem sprint",
    "titulo": "Potência — dia de jogo",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Carga baixa &nbsp;&middot;&nbsp; intenção máxima "
                 "&nbsp;&middot;&nbsp; volume mínimo",
    "rotulo_carga": "CARGA",
    "abertura":
        "<b>Hoje tem jogo. Isto não é um treino — é uma ativação.</b> Ninguém fica "
        "mais forte em algumas horas; o que dá para fazer é chegar à quadra hoje à "
        "noite com o sistema nervoso <b>já ligado</b>. Seis exercícios, três séries "
        "cada, carga leve: em todos eles a <b>subida é a mais rápida que você "
        "conseguir</b> e a descida é controlada. <b>Saia com vontade de fazer "
        "mais</b> — quem sai cansado transformou a ativação em treino, e isso "
        "cobra no jogo.",
    "aquecimento_titulo": "Aquecimento — mais longo que a parte principal",
    "aquecimento_nota": "Num dia de jogo o aquecimento <b>é</b> a maior parte do "
                        "trabalho. Sem pressa nenhuma aqui.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 a 8 min", "a mesma do app"],
        ["Bicicleta ou esteira, ritmo leve", "5 min", "até suar, sem cansar"],
        ["Agachamento só com o peso do corpo, subida rápida", "2 \u00d7 8",
         "do fraco ao forte"],
        ["Arranco e clean com a barra vazia", "2 \u00d7 3", "antes de pôr peso"],
    ],
    "exercicios": [
        ("Arranco (snatch)", "o mais técnico e o mais neural — vem primeiro, sempre",
         "3 \u00d7 2", "3 min", "60%"),
        ("Clean", "tríplice extensão com recepção — carga que ainda sai limpa",
         "3 \u00d7 2", "3 min", "60%"),
        ("Agachamento com salto", "salto no lugar com barra — acima de 1,0 m/s",
         "3 \u00d7 3", "2 min", "25%"),
        ("Agachamento isométrico", "empurra a trava com TUDO por 4 s — ver o verso",
         "3 \u00d7 4 s", "2 min", "máx."),
        ("Supino explosivo", "empurrar rápido — o braço do ataque acorda",
         "3 \u00d7 3", "2 min", "40%"),
        ("Puxada fechada", "puxa rápido, solta devagar",
         "3 \u00d7 4", "90 s", "50%"),
    ],
    "nota_tabela":
        "Anote a carga de cada exercício. Se em alguma série a barra saiu lenta, "
        "<b>pare o exercício ali</b> e marque um <b>X</b> — num dia de jogo, série "
        "lenta não é para ser insistida.",
    "caixa_duracao":
        "<b>30 a 35 minutos, e pelo menos 6 horas antes do apito.</b> Faltando "
        "menos de 3 horas para o jogo, faça só o aquecimento e o agachamento com "
        "salto, e pare por aí.",
    "verso": [
        ("caixa", "<b>A pergunta que decide tudo hoje: você saiu da sala com "
                  "vontade de fazer mais?</b> Se sim, a ativação foi certa. Se saiu "
                  "ofegante, suado demais ou com a perna pesada, foi longe demais — "
                  "e isso não se conserta até a noite. Na dúvida entre mais uma "
                  "série e parar, <b>pare</b>. Hoje o treino que conta é o jogo.",
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
            "<b>Dormiu mal, acordou com dor ou com o corpo estranho?</b> Faça só o "
            "aquecimento e o agachamento com salto, e avise a comissão — pule o "
            "arranco e o clean, que são os que exigem técnica. Isso não é frescura: "
            "é informação que muda a escalação.",
        ]),
        ("espaco", 10),
        ("h", "Os dois exercícios que precisam de explicação"),
        ("notas", [
            ("Agachamento isométrico", "É <b>isometria curta e máxima</b>, não "
             "permanência: barra travada na altura em que o joelho fica a uns 110 "
             "graus, e você empurra com <b>tudo</b> por 4 segundos, como se fosse "
             "arrancá-la do lugar. Três vezes, e acabou. Permanência longa — ficar "
             "30 segundos segurando — é outro treino, cansa e não tem lugar num dia "
             "de jogo. Se a sala não tiver trava, faça o agachamento parando 2 "
             "segundos no fundo e subindo o mais rápido que der."),
            ("Arranco e clean", "Carga leve o bastante para a <b>recepção sair "
             "limpa</b>. Se você precisa se contorcer para receber a barra, está "
             "pesado — e técnica errada repetida com velocidade é como se aprende a "
             "errar rápido. Duas repetições por série é de propósito: a terceira já "
             "costuma sair pior, e hoje não há nada a ganhar com repetição feia. "
             "Sem 1RM lançado, comece com a barra vazia e suba só enquanto o "
             "movimento continuar bonito."),
        ]),
        ("espaco", 8),
        ("h", "O que continua fora, e por quê"),
        ("notas", [
            ("Caixote e sprint", "Não há onde fazer, e em dia de jogo o caixote "
             "sairia de qualquer forma: a queda é carga excêntrica alta, e é a "
             "excêntrica que deixa fadiga residual e dor no dia seguinte. O "
             "agachamento com salto cobre a parte que interessa hoje, que é a "
             "extensão rápida — e cobre sem a aterrissagem."),
        ]),
        ("espaco", 8),
        ("caixa", "<b>Depois do jogo, mande a PSE do JOGO também</b> — não só a "
                  "desta ativação. No voleibol a maior parte da carga da semana vem "
                  "da quadra, e uma análise que só enxerga a sala enxerga menos da "
                  "metade do que o seu corpo levou."),
        ("espaco", 12),
    ],
}

FICHAS = {"forca": FORCA, "potencia": POTENCIA}


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
