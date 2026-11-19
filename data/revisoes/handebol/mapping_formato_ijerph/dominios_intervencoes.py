"""Domínio psicológico dos desfechos de cada intervenção (base da Figura 7B).

Classificação feita a partir dos desfechos conferidos em intervencoes_detalhe.EST. Siglas:
M motivação e autoeficácia; A ansiedade e estresse; S sono, bem-estar e recuperação; H habilidades mentais e
enfrentamento; U humor e afeto; G processos de grupo e sociais; B burnout e saúde mental.
Estudos sem desfecho psicológico (apenas desempenho) recebem conjunto vazio.
"""
DOMINIOS = [("M", "Motivação e autoeficácia", 80), ("A", "Ansiedade e estresse", 72),
            ("S", "Sono, bem-estar e recuperação", 52), ("H", "Habilidades mentais e enfrentamento", 45),
            ("U", "Humor e afeto", 36), ("G", "Processos de grupo e sociais", 17), ("B", "Burnout e saúde mental", 14)]
DOM = {2: "", 16: "AG", 50: "MU", 57: "U", 61: "MAS", 81: "", 89: "SU", 94: "MSU", 107: "S", 111: "S",
       119: "MU", 127: "M", 128: "M", 132: "S", 145: "", 153: "HS", 170: "AH", 171: "MG", 173: "AH", 174: "S",
       179: "", 192: "U", 196: "M", 199: "HU"}
