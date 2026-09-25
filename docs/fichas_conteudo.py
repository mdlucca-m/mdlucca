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
    "meta_titulo": "ELASE - Ativacao de potencia (dia de jogo)",
    "meta_assunto": "Velocidade de movimento com carga baixa, na manha do jogo",
    "titulo": "Potência — dia de jogo",
    "titulo_verso": "Como usar esta ficha",
    "protocolo": "Carga baixa &nbsp;&middot;&nbsp; velocidade máxima "
                 "&nbsp;&middot;&nbsp; volume mínimo",
    "rotulo_carga": "CARGA",
    "abertura":
        "<b>Hoje tem jogo. Isto não é um treino — é uma ativação.</b> Ninguém fica "
        "mais forte em algumas horas; o que dá para fazer é chegar à quadra hoje à "
        "noite com o sistema nervoso <b>já ligado</b>. Carga baixa, série curta, "
        "volume pequeno, cada repetição o mais rápido que você conseguir. "
        "<b>Saia da sala com vontade de fazer mais</b> — quem sai cansado "
        "transformou a ativação em treino, e isso cobra no jogo.",
    "aquecimento_titulo": "Aquecimento — mais longo que a parte principal",
    "aquecimento_nota": "Num dia de jogo o aquecimento <b>é</b> a maior parte do "
                        "trabalho. Sem pressa nenhuma aqui.",
    "aquecimento_cab": ["O QUE", "QUANTO", "OBSERVAÇÃO"],
    "aquecimento": [
        ["Mobilidade de tornozelo, quadril e ombro", "6 a 8 min", "a mesma do app"],
        ["Corrida leve e deslocamentos laterais", "4 min", "até suar, sem cansar"],
        ["Saltinhos no lugar, subindo de intensidade", "2 \u00d7 8", "do fraco ao forte"],
        ["Padrão da barra com bastão ou barra vazia", "2 \u00d7 5", "lembrar o gesto"],
    ],
    "exercicios": [
        ("Agachamento com salto sob carga",
         "o que mais acorda a perna — acima de 1,0 m/s",
         "3 \u00d7 3", "2 min", "25%"),
        ("Puxada alta com barra (snatch pull)",
         "tríplice extensão rápida, sem recepção — menos técnica, mesmo estímulo",
         "3 \u00d7 3", "2 min", "50%"),
        ("Salto vertical máximo (CMJ)", "salto livre, com braço — 9 contatos",
         "3 \u00d7 3", "90 s", "corpo"),
        ("Salto no caixote 40 cm", "subir saltando, DESCER ANDANDO — 9 contatos",
         "3 \u00d7 3", "90 s", "corpo"),
        ("Supino explosivo", "empurrar rápido — o braço do ataque também acorda",
         "3 \u00d7 3", "2 min", "40%"),
        ("Arremesso de medicine ball acima da cabeça",
         "extensão de tudo junto, sem freio no fim",
         "3 \u00d7 4", "60 s", "3 kg"),
        ("Aceleração de 10 metros", "saída rápida, para e volta andando",
         "4 \u00d7 1", "90 s", "corpo"),
    ],
    "nota_tabela":
        "Anote a carga dos exercícios com barra e a altura do caixote. Se em "
        "alguma série a barra saiu lenta ou o salto ficou baixo, <b>pare o "
        "exercício ali</b> e marque um <b>X</b> — num dia de jogo, série lenta não "
        "é para ser insistida.",
    "caixa_duracao":
        "<b>35 a 40 minutos, e pelo menos 6 horas antes do apito.</b> Faltando "
        "menos de 3 horas para o jogo, faça só o aquecimento e os saltos livres "
        "(item 3) e pare por aí.",
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
            "<b>Intenção máxima, carga baixa.</b> A carga é leve de propósito — "
            "ela existe para você poder ser rápido, não para pesar. Sem 1RM "
            "lançado, a carga certa é a mais pesada com que o gesto ainda sai "
            "<b>visivelmente explosivo</b>; quando ele parece só \u201cforte\u201d, "
            "está pesado demais para hoje.",
            "<b>Pausa inteira, sempre.</b> É ela que garante que a série seguinte "
            "saia tão rápida quanto a primeira. Encurtar a pausa hoje transforma "
            "ativação em cansaço.",
            "<b>Série que saiu lenta, exercício encerrado.</b> Não insista para "
            "completar o número no papel: repetição lenta ensina o corpo a ser "
            "lento, e hoje isso vai para dentro do jogo.",
            "<b>Nenhum exercício novo.</b> Dia de jogo não é dia de aprender "
            "movimento — se você nunca fez algum destes, pule e faça o salto livre "
            "no lugar.",
            "<b>Dormiu mal, acordou com dor ou com o corpo estranho?</b> Faça só o "
            "aquecimento e os saltos livres, e avise a comissão. Isso não é "
            "frescura: é informação que muda a escalação.",
        ]),
        ("espaco", 10),
        ("h", "O que saiu desta ficha por causa do jogo"),
        ("notas", [
            ("Drop jump", "É o melhor exercício da semana para reatividade e o pior "
             "para hoje: a queda do caixote é carga excêntrica alta, e é a "
             "excêntrica que deixa fadiga residual e dor no dia seguinte. Volta na "
             "próxima sessão de sala."),
            ("Arranco e clean completos", "Viraram <b>puxada alta</b>. A parte que "
             "interessa hoje — a extensão rápida de tornozelo, joelho e quadril — "
             "está toda na puxada. O que sai é a recepção embaixo da barra: a parte "
             "técnica, a que mais cansa e a única que pode dar errado. Em dia de "
             "jogo não se arrisca técnica."),
            ("Volume", "Caiu de 4 séries para 3, e de 36 contatos de salto para 18. "
             "Potência responde a intensidade, não a volume: três séries rápidas "
             "valem mais hoje que seis arrastadas."),
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
