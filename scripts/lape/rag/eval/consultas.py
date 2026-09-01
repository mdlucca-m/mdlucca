# -*- coding: utf-8 -*-
"""Conjunto de avaliacao da recuperacao.

Vinte e seis perguntas sobre o corpus de artigos do laboratorio. Cada uma
traz a cadeia que a resposta precisa conter — em geral um numero, porque
numero nao admite sinonimo e por isso decide sem julgamento humano.

Duas regras presidiram a redacao das perguntas:

1. A pergunta nao repete a cadeia da resposta. Se a consulta contivesse
   "72,3%", o BM25 acertaria por casamento exato e a medida nao diria nada
   sobre recuperacao.
2. A pergunta usa o vocabulario de quem pergunta, nao o do documento.
   "o vigor volta durante a noite?" no lugar de "restituicao noturna do
   vigor". E essa distancia de vocabulario que separa busca semantica de
   busca lexica.

Sem essas duas regras o conjunto mede casamento de cadeia, e nao
recuperacao.
"""
from __future__ import annotations

# (pergunta, cadeias aceitas como resposta, documento esperado)
# O documento e o trecho final da uri; None aceita qualquer um.
CONSULTAS: list[tuple[str, tuple[str, ...], str | None]] = [
    # -------------------------------------------------- achados numericos
    ("quanto do desgaste do dia o descanso da madrugada devolve?",
     ("72,3", "72,3%"), None),
    ("qual a sobra que fica de um dia para o outro na fadiga do corpo?",
     ("0,47",), None),
    ("quantos jogadores pioram de estado entre a manha e o fim do dia?",
     ("27 pares", "entram no risco", "27 pares atleta-dia"), None),
    ("qual a chance de o resultado da migracao ser obra do acaso?",
     ("0,005", "8,03"), None),
    ("qual o desenho de humor mais comum quando se mede cedo?",
     ("38,8", "iceberg"), None),
    ("e quando se mede tarde, qual passa a ser o mais comum?",
     ("28,6", "barbatana"), None),
    ("quanto o grupo perde de energia da primeira a ultima medida?",
     ("3,15", "−3,15"), None),
    ("quanto o cansaco sobe entre o comeco e o fim do periodo?",
     ("3,19", "+3,19"), None),
    ("em que dia as duas curvas do eixo energetico trocam de posicao?",
     ("5,03",), None),
    ("qual proporcao dos atletas ocupa um estado preocupante?",
     ("38,6", "20,5"), None),
    # ------------------------------------------- propriedades da medida
    ("quais perguntas da escala quase todo mundo responde com zero?",
     ("65,7", "51,2", "efeito piso", "piso"), None),
    ("da para confiar na leitura de um unico dia de um atleta?",
     ("0,43", "ICC", "confiabilidade"), None),
    ("quanto precisa mudar para nao ser erro de medida na fadiga do corpo?",
     ("4,90", "menor variacao detectavel", "menor variação detectável"), None),
    ("a tristeza dos jogadores muda ao longo do periodo?",
     ("50,4", "não se move", "nao se move", "0,016"), None),
    # ------------------------------------------- estrutura de associacao
    ("qual dimensao nao combina com as outras do bloco negativo?",
     ("tensão", "0,02"), None),
    ("o indice geral vira medida de que, ao fim do periodo?",
     ("83,3", "fadiga"), None),
    ("alguma dimensao aparece antes das outras e anuncia o que vem?",
     ("precedência", "precedencia", "0,17", "nenhuma"), None),
    ("o quanto o estado de um dia se repete no dia seguinte?",
     ("0,77", "persistência", "persistencia"), None),
    # ------------------------------------------- estimulo e planejamento
    ("qual tipo de sessao cobra o preco mais alto no proprio dia?",
     ("6,65", "técnico", "tecnico"), None),
    ("o dia de jogo desgasta mais ou menos que o treino intervalado?",
     ("amistoso", "melhor humor"), None),
    ("o humor acompanha o volume daquele dia ou o que se acumulou?",
     ("0,86", "acumulad"), None),
    ("qual medida acompanha a carga dentro de cada atleta?",
     ("0,50", "fadiga física", "fadiga fisica"), None),
    # ------------------------------------------- metodo e amostra
    ("quantas pessoas participaram e de que modalidade?",
     ("27 atletas", "handebol"), None),
    ("como as respostas foram agrupadas para virar unidade de analise?",
     ("166", "atleta-dia"), None),
    ("de onde saiu a referencia para transformar em escala padronizada?",
     ("escore T", "norma de atletas", "inversão", "inversao"), None),
    ("que teste apanha uma subida constante que o outro nao apanha?",
     ("Page", "monotônica", "monotonica"), None),
]
