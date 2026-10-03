"""Ginástica rítmica: uma aba PRIVADA.

Pedido explícito do Mateus: "crie uma aba que sómente a Maria Helena, eu
e o Vilarino temos acesso", para acompanhar estudos sobre variáveis
psicológicas na ginástica rítmica.

Não reaproveita a tabela `articles`: ela é lida por qualquer integrante
na tela "Artigos", e dar privacidade por linha ali exigiria mexer numa
tela grande e muito usada só para esconder um punhado de registros dela.
Uma tabela dedicada, pequena e isolada resolve sem esse risco.

O acesso é uma LISTA (`ginastica_ritmica_acesso`), não três nomes fixos
no código: quem concede e quem revoga é a própria coordenação, escolhendo
entre os integrantes já cadastrados -- assim ninguém aqui precisa
adivinhar a grafia exata do nome de uma pessoa. `admin` sempre vê: já tem
o banco inteiro na mão, então esconder esta tabela dele não protege nada
e só atrapalha suporte.
"""
from __future__ import annotations

from typing import Any

from .db import Database
from .util import clean_text, to_float, to_int


def tem_acesso(db: Database, member_id: int | None, user_role: str | None = None) -> bool:
    if user_role == "admin":
        return True
    if not member_id:
        return False
    return bool(db.scalar(
        "SELECT 1 FROM ginastica_ritmica_acesso WHERE member_id = ?", (member_id,)))


def conceder(db: Database, member_id: int, concedido_por: int | None) -> None:
    db.execute(
        "INSERT INTO ginastica_ritmica_acesso (member_id, concedido_por) VALUES (?, ?)"
        " ON CONFLICT (member_id) DO NOTHING", (member_id, concedido_por))
    db.conn.commit()


def revogar(db: Database, member_id: int) -> None:
    db.execute("DELETE FROM ginastica_ritmica_acesso WHERE member_id = ?", (member_id,))
    db.conn.commit()


def quem_tem_acesso(db: Database) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT m.id, m.full_name, a.concedido_em"
        "  FROM ginastica_ritmica_acesso a JOIN members m ON m.id = a.member_id"
        " ORDER BY m.full_name")


def listar_estudos(db: Database, limite: int = 400) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT * FROM ginastica_ritmica_estudos"
        " ORDER BY ano_publicacao DESC, titulo LIMIT ?", (limite,))


def gravar_estudo(db: Database, criado_por: int | None, registro_id: Any = None,
                  titulo: Any = None, autores: Any = None, ano_publicacao: Any = None,
                  study_type: Any = None, qualis: Any = None, fator_impacto: Any = None,
                  observacoes: Any = None) -> int:
    """Cadastra um estudo novo, ou atualiza um existente quando `registro_id`
    vem preenchido -- o mesmo contrato do formulário de Artigos: todo campo
    viaja sempre, e o que a pessoa apagou na tela apaga no banco."""
    campos = {
        "titulo": clean_text(titulo), "autores": clean_text(autores),
        "ano_publicacao": to_int(ano_publicacao), "study_type": clean_text(study_type),
        "qualis": clean_text(qualis), "fator_impacto": to_float(fator_impacto),
        "observacoes": clean_text(observacoes),
    }
    estudo_id = to_int(registro_id)
    if estudo_id:
        db.execute(
            "UPDATE ginastica_ritmica_estudos SET titulo = ?, autores = ?,"
            " ano_publicacao = ?, study_type = ?, qualis = ?, fator_impacto = ?,"
            " observacoes = ?, atualizado_em = datetime('now') WHERE id = ?",
            (*campos.values(), estudo_id))
        db.conn.commit()
        return estudo_id
    if not campos["titulo"]:
        raise ValueError("título é obrigatório")
    novo_id = db.execute(
        "INSERT INTO ginastica_ritmica_estudos"
        " (titulo, autores, ano_publicacao, study_type, qualis, fator_impacto,"
        "  observacoes, criado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (*campos.values(), criado_por)).lastrowid
    db.conn.commit()
    return novo_id


def excluir_estudo(db: Database, estudo_id: int) -> bool:
    cursor = db.execute("DELETE FROM ginastica_ritmica_estudos WHERE id = ?", (estudo_id,))
    if cursor.rowcount:
        db.conn.commit()
    return bool(cursor.rowcount)


# ----------------------------------------------------------------------
# Estudos achados numa busca aberta na web (pedido do Mateus: "pesquisa
# e cadastra uns estudos"), em variáveis psicológicas na ginástica
# rítmica -- ansiedade, imagem corporal/transtornos alimentares,
# automotivação/autoconceito, autoestima, perfeccionismo e estressores.
#
# NÃO é uma busca sistemática reproduzível (sem acesso a PubMed/Scopus/
# WoS/CINAHL neste ambiente, só busca aberta na web) -- é apoio de
# triagem para a equipe conferir com acesso institucional, igual à
# atualização que fizemos para o Andrade et al. 2023. Título, autores,
# ano e o link/DOI vêm de fontes reais e conferidas; periódico, Qualis e
# fator de impacto ficam de fora quando não puderam ser confirmados --
# um número chutado é pior que nenhum (mesmo princípio da Ana, ver
# ana.py). `study_type` só entra quando o delineamento é claro no
# resumo; desenho quase-experimental, por exemplo, fica sem rótulo para
# não ser lido como ensaio randomizado.
ESTUDOS_SEMEADOS: tuple[dict[str, Any], ...] = (
    {
        "titulo": "In the pitfall of expectations: an exploratory analysis of "
                  "stressors in elite rhythmic gymnastics",
        "autores": "Kovács, Krisztina; Kéringer, Johanna; Rácz, József; "
                   "Gyömbér, Noémi; Németh, Krisztina",
        "ano_publicacao": 2022,
        "observacoes": "Entrevistas semiestruturadas com ginastas, técnicos e pais sobre "
                       "estressores e clima do esporte; os três grupos relataram um "
                       "ambiente percebido como prejudicial, e corpo magro associado a "
                       "sucesso. Frontiers in Psychology, DOI: 10.3389/fpsyg.2022.955232 "
                       "— https://doi.org/10.3389/fpsyg.2022.955232",
    },
    {
        "titulo": "Body image and attitudinal aspects of eating disorders in "
                  "rhythmic gymnasts",
        "autores": "Salbach, Harriet; Klinkowski, Nora; Pfeiffer, Ernst; "
                   "Lehmkuhl, Ulrike; Korte, Alexander",
        "ano_publicacao": 2007,
        "study_type": "Estudo transversal",
        "observacoes": "Compara 50 ginastas de elite (seleção alemã), 58 pacientes com "
                       "anorexia nervosa e 56 alunas de ensino médio no Eating Disorder "
                       "Inventory-2; sem alteração atitudinal relevante de TA nas "
                       "ginastas, mas leve distorção de imagem corporal no abdômen. "
                       "PMID 17652951 — https://pubmed.ncbi.nlm.nih.gov/17652951/ "
                       "(periódico/Qualis/fator de impacto não conferidos aqui).",
    },
    {
        "titulo": "Body Dissatisfaction among Young Girls in Recreational "
                  "Rhythmic Gymnastics",
        "autores": "Núñez, B. P.; Sánchez-Lastra, M. A.; Diz, J. C.; Ayán-Pérez, C.",
        "ano_publicacao": 2024,
        "study_type": "Estudo transversal",
        "observacoes": "88 meninas de 6-11 anos praticantes de GR vs. 88 controles "
                       "pareadas por idade; sem diferença significativa de insatisfação "
                       "corporal entre os grupos. Children, 11(6), "
                       "DOI: 10.3390/children11060696 — https://doi.org/10.3390/children11060696",
    },
    {
        "titulo": "Prevalence of eating disorder, body image dissatisfaction and "
                  "musculoskeletal complaints among former Spanish rhythmic "
                  "gymnasts: a retrospective study",
        "autores": "Portas-Núñez, Belén; Blanco-Martínez, Nerea; "
                   "Sánchez-Lastra, Miguel Adriano; Diz-Gómez, José Carlos; "
                   "Ayán-Pérez, Carlos",
        "ano_publicacao": 2026,
        "study_type": "Estudo transversal",
        "observacoes": "Estudo retrospectivo com ex-ginastas espanholas; 10,6% acima do "
                       "limiar de transtorno alimentar e 68,1% relataram insatisfação "
                       "corporal. The Physician and Sportsmedicine, v. 54, n. 2 — "
                       "https://pubmed.ncbi.nlm.nih.gov/41327901/",
    },
    {
        "titulo": "Motivation, Self-Concept and Discipline in Young Adolescents Who "
                  "Practice Rhythmic Gymnastics. An Intervention",
        "autores": "González-Valero, Gabriel; Zurita-Ortega, Félix; "
                   "Ubago-Jiménez, José Luis; Puertas-Molero, Pilar",
        "ano_publicacao": 2020,
        "observacoes": "Intervenção quase-experimental (estratégias TARGET) com 104 "
                       "adolescentes (60 controle, 44 experimental); grupo intervenção "
                       "melhorou clima de tarefa, autoconceito físico, disciplina e "
                       "flexibilidade. Sem tipo de estudo declarado aqui -- é "
                       "quase-experimental, não randomizado. Children, 7(9), 135, "
                       "DOI: 10.3390/children7090135 — https://doi.org/10.3390/children7090135",
    },
    {
        "titulo": "Self-Perceptions and Self-Esteem in Adolescent Rhythmic Gymnasts: "
                  "Is Training Level a Determinant?",
        "autores": "Mastrogianni, Angeliki; Psychountaki, Maria; Donti, Olyvia",
        "ano_publicacao": 2020,
        "study_type": "Estudo transversal",
        "observacoes": "100 ginastas (32 competitivas, 68 recreativas), 13-15 anos; "
                       "competitivas pontuaram mais alto em relação com os pais e "
                       "autovalor global. Science of Gymnastics Journal, 12(3), 357-366 "
                       "— https://journals.uni-lj.si/sgj/article/view/11739",
    },
    {
        "titulo": "Quality of life and level of perfectionism of rhythmic "
                  "gymnastics athletes",
        "autores": "Buzzi, Pâmela Calvo; Carignano, Fernanda Shizue Nishida; "
                   "Felipe, Daniele Fernanda; Oliveira, Leonardo Pestillo de",
        "ano_publicacao": 2025,
        "study_type": "Estudo transversal",
        "observacoes": "36 atletas do Paraná (juvenil e adulto); correlação "
                       "significativa entre qualidade de vida e perfeccionismo na "
                       "categoria adulta (r = 0,70; p = 0,007). Motriz, 31(1) — "
                       "https://www.periodicos.rc.biblioteca.unesp.br/index.php/motriz/article/view/19251",
    },
    {
        "titulo": "Competitive State Anxiety and Performance in Young Female "
                  "Rhythmic Gymnasts",
        "autores": "Tsopani, D.; Dallas, G.; Skordilis, E. K.",
        "ano_publicacao": 2011,
        "study_type": "Estudo transversal",
        "observacoes": "86 ginastas de 11-12 anos responderam ao CSAI-2 uma hora antes "
                       "da competição; autoconfiança foi a única preditora significativa "
                       "de desempenho. Perceptual and Motor Skills, 112(2), 549-560, "
                       "DOI: 10.2466/05.09.20.PMS.112.2.549-560 (confirmado via PubMed, "
                       "PMID 21667763) — https://doi.org/10.2466/05.09.20.PMS.112.2.549-560",
    },
    # ------------------------------------------------------------------
    # Segunda rodada (pedido do Mateus: "atualize a revisão... uma revisão
    # bibliométrica"), agora via PubMed (mcp__PubMed__search_articles),
    # que indexa periódicos reais de ciência do esporte e psicologia e dá
    # DOI/PMID conferíveis -- melhor que a busca aberta na web da primeira
    # rodada. Ainda NÃO é a base completa do PRISMA que o Mateus mandou
    # (EMBASE/WoS/Scopus/CINAHL seguem fora de alcance aqui); o memorando
    # em docx entregue junto desta atualização documenta as buscas feitas
    # e a triagem, título a título.
    {
        "titulo": "Do Different Interdependencies within a Sport Affect the "
                  "Perceived Motivational Climate, Use of Spontaneous Self-Talk, "
                  "Positivity or Precompetitive Anxiety?",
        "autores": "Gómez-Landero, Luis Arturo; Santos-Rosa, Francisco Javier; "
                   "Reguera-López-de-la-Osa, Xoana; Cervelló, Eduardo",
        "ano_publicacao": 2025,
        "study_type": "Estudo transversal",
        "observacoes": "76 ginastas seniores (41 da modalidade individual, 35 em "
                       "conjunto); conjunto percebeu clima mais ego-envolvido e maior "
                       "rivalidade interna, com mais autofala positiva no treino; "
                       "autoconfiança foi menor nas ginastas da modalidade individual. "
                       "Journal of Human Kinetics, 102, 227-240, DOI: 10.5114/jhk/204776 "
                       "— https://doi.org/10.5114/jhk/204776 (PubMed, PMID 42211797)",
    },
    {
        "titulo": "Positive and negative spontaneous self-talk and performance in "
                  "gymnastics: The role of contextual, personal and situational factors",
        "autores": "Santos-Rosa, Francisco J.; Montero-Carretero, Carlos; "
                   "Gómez-Landero, Luis Arturo; Torregrossa, Miquel; Cervelló, Eduardo",
        "ano_publicacao": 2022,
        "observacoes": "258 ginastas (conjuntos), 14-20 anos, medidas pré e "
                       "pós-competição; autofala espontânea positiva foi predita pelo "
                       "clima de tarefa e pela positividade, e por sua vez predisse "
                       "autoconfiança e desempenho; autofala negativa associou-se a "
                       "maior ansiedade cognitiva e somática. Sem tipo de estudo "
                       "declarado aqui -- medidas repetidas em torno de uma única "
                       "competição, não um desenho transversal simples. PLoS ONE, "
                       "17(3), e0265809, DOI: 10.1371/journal.pone.0265809 — "
                       "https://doi.org/10.1371/journal.pone.0265809 (PubMed, PMID 35325003)",
    },
    {
        "titulo": "Goal orientations and sport motivation, differences between the "
                  "athletes of competitive and non-competitive rhythmic gymnastics",
        "autores": "Koumpoula, M.; Tsopani, D.; Flessas, K.; Chairopoulou, C.",
        "ano_publicacao": 2011,
        "study_type": "Estudo transversal",
        "observacoes": "98 ginastas (40 competitivas, 58 não competitivas), 14 anos ou "
                       "mais; as não competitivas apresentaram mais regulação "
                       "introjetada e amotivação, e menos orientação ao ego; ambos os "
                       "grupos com alta orientação à tarefa. Journal of Sports Medicine "
                       "and Physical Fitness, 51(3), 480-488 (DOI não disponível no "
                       "PubMed) — https://pubmed.ncbi.nlm.nih.gov/21904288/",
    },
    {
        "titulo": "Predictors of attainment in rhythmic sportive gymnastics",
        "autores": "Hume, P. A.; Hopkins, W. G.; Robinson, D. M.; Robinson, S. M.; "
                   "Hollings, S. C.",
        "ano_publicacao": 1993,
        "study_type": "Estudo transversal",
        "observacoes": "106 ginastas de 7-27 anos; entre os correlatos psicológicos de "
                       "desempenho, destacaram-se preparação mental, motivação por "
                       "criatividade e dimensões de prazer com a prática, enquanto "
                       "ansiedade-depressão recente se associou negativamente ao "
                       "desempenho. Journal of Sports Medicine and Physical Fitness, "
                       "33(4), 367-377 (DOI não disponível no PubMed) — "
                       "https://pubmed.ncbi.nlm.nih.gov/8035585/",
    },
    {
        "titulo": "Resilience, stress and injuries in the context of the Brazilian "
                  "elite rhythmic gymnastics",
        "autores": "Codonhato, Renan; Rubio, Victor; Oliveira, Paulo Márcio Pereira; "
                   "Resende, Camila Ferezin; Rosa, Bruna Akawana Martins; Pujals, "
                   "Constanza; Fiorese, Lenamar",
        "ano_publicacao": 2018,
        "observacoes": "8 atletas da seleção brasileira de ginástica rítmica "
                       "acompanhadas ao longo do ciclo olímpico 2015-2016; níveis de "
                       "estresse e recuperação relativamente estáveis na temporada, sem "
                       "correlação direta entre os escores de resiliência, estresse e "
                       "recuperação -- mas o suporte social foi apontado como o "
                       "principal fator psicológico de resiliência. Sem tipo de estudo "
                       "declarado aqui -- acompanhamento observacional repetido, não um "
                       "ensaio controlado, ainda que o PubMed também o rotule como "
                       "'Clinical Trial'. PLoS ONE, 13(12), e0210174, "
                       "DOI: 10.1371/journal.pone.0210174 — "
                       "https://doi.org/10.1371/journal.pone.0210174 (PubMed, PMID 30596793)",
    },
    {
        "titulo": "Mental imagery and performance in aerobic, artistic, acrobatics, "
                  "trampoline and tumbling, and rhythmic gymnasts: a systematic review",
        "autores": "Yang, Wenxin",
        "ano_publicacao": 2026,
        "study_type": "Revisão sistemática",
        "observacoes": "Revisão sistemática (PubMed, Scopus, Web of Science) com 16 "
                       "estudos incluídos entre ginastas competitivos de todas as "
                       "modalidades da FIG, rítmica entre elas; evidência mista -- "
                       "alguns estudos controlados mostram ganho de desempenho com "
                       "imagética, outros não, apesar de melhora em variáveis "
                       "psicológicas como autoconfiança; qualidade metodológica dos "
                       "estudos primários majoritariamente baixa a moderada (RoB 2 e "
                       "ROBINS-I). Frontiers in Psychology, 17, 1803261, "
                       "DOI: 10.3389/fpsyg.2026.1803261 — "
                       "https://doi.org/10.3389/fpsyg.2026.1803261 (PubMed, PMID 41890922)",
    },
    {
        "titulo": "Are they too perfect to eat healthy? Association between eating "
                  "disorder symptoms and perfectionism in adolescent rhythmic gymnasts",
        "autores": "Donti, Olyvia; Donti, Anastasia; Gaspari, Vasiliki; Pleksida, "
                   "Paraskevi; Psychountaki, Maria",
        "ano_publicacao": 2021,
        "study_type": "Estudo transversal",
        "observacoes": "89 ginastas de 13-15 anos (41 internacionais, 48 recreativas); "
                       "41,46% das internacionais e 14,58% das recreativas pontuaram "
                       "≥20 no EAT-26; o nível internacional também pontuou mais alto "
                       "em perfeccionismo esportivo (reações negativas à imperfeição, "
                       "padrões pessoais); experiência de treino associou-se "
                       "negativamente a sintomas de transtorno alimentar nas "
                       "internacionais. Eating Behaviors, 41, 101514, "
                       "DOI: 10.1016/j.eatbeh.2021.101514 — "
                       "https://doi.org/10.1016/j.eatbeh.2021.101514 (PubMed, PMID 33964708)",
    },
    {
        "titulo": "Understanding Eating Disorders in Elite Gymnastics: Ethical and "
                  "Conceptual Challenges",
        "autores": "Tan, Jacinta Oon Ai; Calitri, Raff; Bloodworth, Andrew; "
                   "McNamee, Michael J.",
        "ano_publicacao": 2016,
        "study_type": "Revisão",
        "observacoes": "Artigo de revisão que também traz dados próprios "
                       "qualitativos e quantitativos sobre padrão de sintomas de "
                       "transtorno alimentar, sintomas depressivos e autoestima em "
                       "ginastas britânicas de nível nacional/internacional em "
                       "acrobática, tumbling e rítmica. Clinics in Sports Medicine, "
                       "35(2), 275-292, DOI: 10.1016/j.csm.2015.10.002 — "
                       "https://doi.org/10.1016/j.csm.2015.10.002 (PubMed, PMID 26832977)",
    },
    {
        "titulo": "Relations between female students' personality traits and "
                  "reported handicaps to rhythmic gymnastics performance",
        "autores": "Ferrand, Claude; Champely, Stephane; Brunel, Philippe C.",
        "ano_publicacao": 2005,
        "study_type": "Estudo transversal",
        "observacoes": "74 estudantes francesas de educação física antes de um "
                       "exame competitivo de ginástica rítmica; ansiedade-traço "
                       "associou-se negativamente a entraves de desempenho ligados a "
                       "compromissos sociais e de trabalho, e autoconsciência pública "
                       "associou-se a entraves ligados a família e amigos; autoestima "
                       "não explicou variância significativa em nenhuma categoria de "
                       "entrave. Psychological Reports, 96(2), 361-373, "
                       "DOI: 10.2466/pr0.96.2.361-373 — "
                       "https://doi.org/10.2466/pr0.96.2.361-373 (PubMed, PMID 15941110)",
    },
    {
        "titulo": "Characteristics of respiratory pattern and anxiety in rhythmic "
                  "gymnasts",
        "autores": "Akai, Lena; Ishizaki, Sakuko; Matsuoka, Masao; Homma, Ikuo",
        "ano_publicacao": 2010,
        "study_type": "Estudo transversal",
        "observacoes": "13 ginastas universitárias comparadas a 26 estudantes de "
                       "medicina não atletas; ginastas pontuaram mais alto em "
                       "ansiedade-traço e ansiedade-estado (STAI), com correlação "
                       "positiva entre ambos os tipos de ansiedade e a variação no "
                       "padrão respiratório durante reinalação de CO2. Advances in "
                       "Experimental Medicine and Biology, 669, 329-332, "
                       "DOI: 10.1007/978-1-4419-5692-7_67 — "
                       "https://doi.org/10.1007/978-1-4419-5692-7_67 (PubMed, PMID 20217376)",
    },
    {
        "titulo": "The medical and psychological support for the child athletes "
                  "during different periods of the training cycle",
        "autores": "Stepanenko, N. P.; Levitskaia, T. E.; Matveeva, E. A.; "
                   "Zaitsev, A. A.; Konovalov, A. B.; Tren'kaeva, N. A.; "
                   "Akimova, K. K.; Kremeno, S. V.; Dostovalova, O. V.; "
                   "Merzliakova, N. V.",
        "ano_publicacao": 2014,
        "observacoes": "42 atletas russas de ginástica rítmica de 8-15 anos, "
                       "divididas em dois grupos (com e sem carga de treino durante o "
                       "tratamento restaurador); a carga física adicional associou-se "
                       "a alterações negativas nas esferas hormonal e psicológica, e o "
                       "tratamento restaurador ajudou a normalizar esses parâmetros. "
                       "Sem tipo de estudo declarado aqui -- comparação entre dois "
                       "grupos sem alocação aleatória clara. Voprosy Kurortologii, "
                       "Fizioterapii, i Lechebnoi Fizicheskoi Kultury, n. 6, 30-33 "
                       "(resumo em inglês no PubMed; artigo completo em russo, "
                       "periódico/Qualis/fator de impacto não conferidos aqui) — "
                       "https://pubmed.ncbi.nlm.nih.gov/25730932/",
    },
    # ------------------------------------------------------------------
    # Terceira rodada: o Mateus mandou a planilha de verdade da própria
    # revisão (CSV/XLSX exportados do Mendeley/Bibliometrix, com 40
    # artigos já triados pela equipe -- autor, ano, DOI, país, fator de
    # impacto e as "variáveis" que o próprio grupo já tinha anotado). É a
    # base mais confiável que entrou aqui até agora, porque veio de busca
    # institucional real (EMBASE/WoS/Scopus/PubMed), não de web aberta.
    # Sete títulos já estavam cadastrados (rodadas 1 e 2) e por isso não
    # se repetem; um (habilidades psicomotoras/tempo de reação) ficou de
    # fora por não tratar de variável psicológica. O campo "observações"
    # reaproveita, quando existia, a própria anotação de "variáveis" que
    # a equipe já tinha escrito na planilha -- não é uma leitura nova
    # feita aqui. Duas entradas (Borrione et al. 2013 e a de nutrição em
    # espanhol) tinham DOI/periódico visivelmente trocados na planilha
    # (apontando para outro artigo da própria planilha); esses campos
    # ficaram em branco aqui em vez de reproduzir o erro.
    {
        "titulo": "Effects of competitiveness in rhythmic gymnastics: a "
                  "qualitative research",
        "autores": "Esposito, Giovanni",
        "ano_publicacao": 2024,
        "fator_impacto": 0.4,
        "observacoes": "24 ginastas de 13-20 anos (grupo profissional e grupo "
                       "não profissional) responderam a um questionário de 22 "
                       "itens sobre fatores cognitivos, comportamento alimentar e "
                       "motivação para o esporte; sofrimento psicológico foi maior "
                       "no grupo profissional, associado a estresse, dieta e "
                       "pressão dos técnicos -- os autores atribuem o sofrimento à "
                       "relação técnico-atleta, não à ginástica rítmica em si. "
                       "Acta Kinesiologica, DOI: 10.51371/issn.1840-2976.2024.18.4.7 "
                       "— https://doi.org/10.51371/issn.1840-2976.2024.18.4.7",
    },
    {
        "titulo": "Effects of Rhythmic Gymnastics on Joint Attention and "
                  "Emotional Problems of Autistic Children: A Preliminary "
                  "Investigation",
        "autores": "Duan, Guanting; Han, Qing; Yao, Mingyan; Li, Ran",
        "ano_publicacao": 2022,
        "observacoes": "Estudo de caso único (desenho A-B-A) com duas crianças "
                       "autistas de 6 anos; a ginástica rítmica adaptada ajudou a "
                       "desenvolver atenção compartilhada responsiva e reduziu "
                       "problemas emocionais. Foge do escopo de 'ginasta' para "
                       "'ginástica como intervenção', por isso entra à parte das "
                       "demais. Computational Intelligence and Neuroscience, "
                       "DOI: 10.1155/2022/2596095 — https://doi.org/10.1155/2022/2596095",
    },
    {
        "titulo": "Psychopathology in elite rhythmic gymnasts and anorexia "
                  "nervosa patients",
        "autores": "Klinkowski, Nora",
        "ano_publicacao": 2008,
        "fator_impacto": 4.8,
        "study_type": "Estudo transversal",
        "observacoes": "Compara ginastas de elite (n=51), pacientes internadas "
                       "com anorexia nervosa (n=55) e colegiais (n=53) no Symptom "
                       "Checklist (SCL-90-R); as ginastas não mostraram sofrimento "
                       "psicológico comparável ao das pacientes com AN, apesar do "
                       "físico magro -- depressão foi o que melhor discriminou os "
                       "três grupos. European Child & Adolescent Psychiatry, "
                       "DOI: 10.1007/s00787-007-0643-y — https://doi.org/10.1007/s00787-007-0643-y",
    },
    {
        "titulo": "\"It's Always the Judge's Fault\": Attention, Emotion "
                  "Recognition, and Expertise in Rhythmic Gymnastics Assessment",
        "autores": "van Bokhorst, Lindsey G.; Knapová, Lenka; Majoranc, Kim; "
                   "Szebeni, Zea K.; Táborský, Adam; Tomić, Dragana; Cañadas, Elena",
        "ano_publicacao": 2016,
        "fator_impacto": 2.9,
        "observacoes": "Protocolo de estudo (não traz amostra própria nesta "
                       "versão) sobre como o reconhecimento de emoções e a "
                       "capacidade atencional de juízas de ginástica rítmica "
                       "influenciam a precisão da nota dada -- é sobre a psicologia "
                       "de quem julga, não de quem compete. Frontiers in "
                       "Psychology, DOI: 10.3389/fpsyg.2016.01008 — "
                       "https://doi.org/10.3389/fpsyg.2016.01008",
    },
    {
        "titulo": "Use of video observation and motor imagery on jumping "
                  "performance in national rhythmic gymnastics athletes",
        "autores": "Battaglia, C.; D'Artibale, E.; Fiorilli, G.; Piazza, M.; "
                   "Tsopani, D.; Giombini, A.; Calcagno, G.; di Cagno, A.",
        "ano_publicacao": 2014,
        "fator_impacto": 1.9,
        "study_type": "Ensaio controlado randomizado",
        "observacoes": "72 ginastas divididas em grupo experimental (observação "
                       "de vídeo + imagética motora PETTLEP associada à prática "
                       "física) e grupo controle (só prática física), 6 semanas; "
                       "desempenho de salto melhorou mais no grupo experimental, e "
                       "a capacidade de gerar imagética correlacionou-se com o "
                       "ganho. Human Movement Science, DOI: 10.1016/j.humov.2014.10.001 "
                       "— https://doi.org/10.1016/j.humov.2014.10.001",
    },
    {
        "titulo": "Comparison of dissociative experiences between rhythmic "
                  "gymnasts and female dancers",
        "autores": "Thomson, Paula; Kibarska, Lilia Alexieva; Jaque, S. Victoria",
        "ano_publicacao": 2011,
        "fator_impacto": 3.1,
        "study_type": "Estudo transversal",
        "observacoes": "Ginastas de elite da Bulgária e dos EUA e bailarinas "
                       "profissionais da Bulgária, Canadá e EUA respondem à "
                       "Dissociative Experience Scale-II; as duas populações de "
                       "elite (não o grupo controle) pontuaram na faixa patológica "
                       "para transtornos dissociativos, com ginastas relatando "
                       "maior capacidade de ignorar a dor. International Journal "
                       "of Sport and Exercise Psychology, "
                       "DOI: 10.1080/1612197X.2011.614850 — "
                       "https://doi.org/10.1080/1612197X.2011.614850",
    },
    {
        "titulo": "Association between parenting practices and competitive "
                  "trait anxiety in female gymnasts",
        "autores": "Fink, Anja; Fischler, Katharina; Raschner, Christian; "
                   "Hildebrandt, Carolin; Ledochowski, Larissa; Kopp, Martin",
        "ano_publicacao": 2013,
        "fator_impacto": 0.6,
        "study_type": "Estudo transversal",
        "observacoes": "170 ginastas austríacas (artística e rítmica), 114 delas "
                       "com 12 anos; comportamento parental diretivo influenciou a "
                       "ansiedade-traço competitiva -- ginastas de rítmica "
                       "relataram mais pressão e comportamento diretivo dos pais "
                       "do que as de artística, e maior distância entre práticas "
                       "parentais percebidas e desejadas. International Journal of "
                       "Sport Psychology, DOI: 10.7352/IJSP2013.44.515 — "
                       "https://doi.org/10.7352/IJSP2013.44.515",
    },
    {
        "titulo": "Resilience in Youth Sport: A Qualitative Investigation of "
                  "Gymnastics Coach and Athlete Perceptions",
        "autores": "White, Rhiannon L.; Bennie, Andrew",
        "ano_publicacao": 2015,
        "fator_impacto": 2.1,
        "observacoes": "22 ginastas jovens e sete técnicas australianas em "
                       "entrevistas semiestruturadas; relações interpessoais e "
                       "comportamentos positivos dos técnicos ajudaram as ginastas "
                       "a superar falhas e desenvolver resiliência, autoeficácia e "
                       "autoestima -- sem recorte específico de rítmica x "
                       "artística declarado no resumo. International Journal of "
                       "Sports Science & Coaching, DOI: 10.1260/1747-9541.10.2-3.379 "
                       "— https://doi.org/10.1260/1747-9541.10.2-3.379",
    },
    {
        "titulo": "Determinants of competitive performance in rhythmic "
                  "gymnastics. a review",
        "autores": "Bobo-Arce, Marta A.; Méndez-Rial, Belia",
        "ano_publicacao": 2013,
        "fator_impacto": 0.4,
        "study_type": "Revisão",
        "observacoes": "Revisão crítica da literatura sobre preditores de "
                       "desempenho em ginástica rítmica, agrupados em condição "
                       "física/biológica, aspectos técnicos, fatores psicológicos "
                       "(processos atencionais, ansiedade-traço e de estado, "
                       "autoconsciência, autoeficácia), processo de treino e "
                       "outras dimensões; conclui que poucos estudos têm "
                       "perspectiva global sobre o que prediz o desempenho. "
                       "Journal of Human Sport and Exercise, "
                       "DOI: 10.4100/jhse.2013.8.Proc3.18 — "
                       "https://doi.org/10.4100/jhse.2013.8.Proc3.18",
    },
    {
        "titulo": "Body image perception and satisfaction in elite rhythmic "
                  "gymnasts: a controlled study",
        "autores": "Borrione, P.; Battaglia, C.; Fiorilli, G.; Moffa, S.; "
                   "Despina, T.; Piazza, M.; Calcagno, G.; Di Cagno, A.",
        "ano_publicacao": 2013,
        "fator_impacto": 0.6,
        "study_type": "Estudo transversal",
        "observacoes": "81 ginastas de elite (20 internacionais, 61 nacionais) e "
                       "80 controles pareadas; as ginastas de elite tiveram "
                       "percepção da própria imagem corporal mais realista "
                       "(correspondente ao IMC real) do que ginastas de nível "
                       "mais baixo e outras atletas, embora a amostra toda tenha "
                       "expressado insatisfação significativa com a própria "
                       "imagem. Medicina dello Sport, 66(1), 61-70 (DOI na "
                       "planilha original apontava para outro artigo -- não "
                       "reproduzido aqui) — "
                       "https://www.minervamedica.it/en/journals/medicina-dello-sport/article.php?cod=R26Y2013N01A0061",
    },
    {
        "titulo": "Comparison of anthropometric indicators in rhythmic "
                  "gymnastics athletes satisfied and dissatisfied with body image",
        "autores": "Zanlorenci, Suellem",
        "ano_publicacao": 2020,
        "study_type": "Estudo transversal",
        "observacoes": "38 atletas de ginástica rítmica do Oeste do Paraná, "
                       "divididas por satisfação com a imagem corporal (Body "
                       "Shape Questionnaire); as insatisfeitas apresentaram IMC, "
                       "dobras cutâneas e percentual de gordura mais altos, mesmo "
                       "controlando nível econômico e maturação sexual. "
                       "Motricidade, DOI: 10.6063/motricidade.19232 — "
                       "https://doi.org/10.6063/motricidade.19232",
    },
    {
        "titulo": "Nutritional, anthropometrical and psychological aspects in "
                  "rhythmic gymnastics",
        "autores": "San Mauro Martín, Ismael; Cevallos, Vanesa; "
                   "Pina-Ordúñez, Diana; Garicano-Vilar, Elena",
        "ano_publicacao": 2016,
        "fator_impacto": 1.1,
        "observacoes": "25 ginastas adultas espanholas; levantamento de "
                       "antropometria, hábitos alimentares e imagem corporal -- "
                       "título do próprio artigo já cita explicitamente o aspecto "
                       "psicológico. Nutrición Hospitalaria, 33(4), 383, "
                       "DOI: 10.20960/nh.383 (confirmado via PubMed, PMID "
                       "27571660) — https://doi.org/10.20960/nh.383",
    },
    {
        "titulo": "The associations of body image perception with serum "
                  "resistin levels in highly trained adolescent estonian "
                  "rhythmic gymnasts",
        "autores": "Remmel, Liina; Jürimäe, Jaak; Tamm, Anna Liisa; "
                   "Purge, Priit; Tillmann, Vallo",
        "ano_publicacao": 2021,
        "fator_impacto": 4.8,
        "study_type": "Estudo transversal",
        "observacoes": "33 ginastas estonianas de alto rendimento e 20 controles "
                       "não treinadas, 14-18 anos; sem diferença na pontuação "
                       "total do Body Attitude Test entre os grupos, mas nas "
                       "ginastas a pontuação correlacionou-se positivamente com o "
                       "nível sérico de resistina (r=0,35) -- resistina e IMC "
                       "explicaram 40,8% da variabilidade na percepção de imagem "
                       "corporal. Nutrients, DOI: 10.3390/nu13093147 — "
                       "https://doi.org/10.3390/nu13093147",
    },
    {
        "titulo": "Psychological recreation of overcoming failures and "
                  "achieving success by young rhythmic gymnasts aged 6-8",
        "autores": "Golenkova, Julia; Kravchuk, Tatyana; Sanzharova, Nina; "
                   "Potop, Vladimir; Filon, Karina",
        "ano_publicacao": 2023,
        "fator_impacto": 2.1,
        "study_type": "Ensaio controlado",
        "observacoes": "20 meninas ucranianas de 6-8 anos (Kharkiv), divididas "
                       "em grupo experimental e controle; treino psicológico "
                       "(Sports Motivation Scale, State-Trait Anxiety Inventory "
                       "for Children) elevado à motivação para alcançar sucesso e "
                       "melhorou o desempenho técnico em elementos de 'risco' com "
                       "objeto. Physical Culture Recreation and Rehabilitation, "
                       "DOI: 10.15561/physcult.2023.0101 — "
                       "https://doi.org/10.15561/physcult.2023.0101",
    },
    {
        "titulo": "The Body Shape of Pubertal Rhythmic Gymnasts: The "
                  "Association with BMI, Eating Disorder Risks, and Perfectionism",
        "autores": "Marković, Andrea; Aleksić Veljković, Aleksandra; "
                   "Vukadinović Jurišić, Mila; Obradović, Anja; Đurović, Dušanka",
        "ano_publicacao": 2023,
        "fator_impacto": 0.7,
        "study_type": "Estudo transversal",
        "observacoes": "40 ginastas sérvias de nível nacional, ~12,8 anos; "
                       "perfeccionismo, IMC, horas de treino, experiência de "
                       "treino, risco de transtorno alimentar (EAT-26), idade e "
                       "experiência explicaram 64,2% da variância na "
                       "insatisfação com a forma do corpo (BSQ) -- ginastas com "
                       "BSQ mais alto usam mais dieta/comportamento compensatório. "
                       "Physical Education and Sport, DOI: 10.22190/FUPES230223007M "
                       "— https://doi.org/10.22190/FUPES230223007M",
    },
    {
        "titulo": "Understanding overuse injuries in rhythmic gymnastics: A "
                  "12-month ethnographic study",
        "autores": "Cavallerio, Francesca; Wadey, Ross; "
                   "Wagstaff, Christopher Robert David",
        "ano_publicacao": 2016,
        "fator_impacto": 3.3,
        "observacoes": "Etnografia de 12 meses num clube italiano de elite (16 "
                       "ginastas, 3 técnicas, 1 fisioterapeuta, 22 pais e a "
                       "presidente do clube); examina como a cultura do esporte -- "
                       "não só a carga física -- molda a ocorrência e a "
                       "experiência de lesões por uso excessivo, com histórias "
                       "etnográficas contrastando a leitura da ginasta e da "
                       "técnica sobre a mesma sessão. Psychology of Sport and "
                       "Exercise, DOI: 10.1016/j.psychsport.2016.05.002 — "
                       "https://doi.org/10.1016/j.psychsport.2016.05.002",
    },
    {
        "titulo": "Evaluation of eating attitudes and body image perception of "
                  "rhythmic gymnastics athletes",
        "autores": "Buzzi, Pamela Calvo; Nishida, Fernanda Shizue; "
                   "de Oliveira, Leonardo Pestillo; Felipe, Daniele Fernanda",
        "ano_publicacao": 2023,
        "observacoes": "36 atletas (juvenil e adulto); abordagem quantitativa, "
                       "observacional e transversal sobre imagem corporal e "
                       "distúrbios alimentares -- mesmo grupo de pesquisa do "
                       "estudo sobre qualidade de vida e perfeccionismo já "
                       "cadastrado nesta aba (Buzzi et al., 2025), mas é um "
                       "artigo diferente. RBONE — Revista Brasileira de Obesidade, "
                       "Nutrição e Emagrecimento (DOI não informado) — "
                       "https://www.rbone.com.br/index.php/rbone/en/article/view/2234",
    },
    {
        "titulo": "Resilience and optimism in rhythmic gymnastics",
        "autores": "Serrano-Nortes, Elena; Gómez Díaz, Magdalena; "
                   "Reche-García, Cristina",
        "ano_publicacao": 2021,
        "fator_impacto": 1.2,
        "observacoes": "29 ginastas espanholas, 13-20 anos; 24,8% com alta "
                       "resiliência e só 20,7% com alto otimismo (62,1% com "
                       "otimismo baixo), medidos pela Escala de Resiliência "
                       "adaptada ao espanhol e pelo LOT-R. Retos, 41, 581-588, "
                       "DOI: 10.47197/retos.v0i41.83086 — "
                       "https://doi.org/10.47197/retos.v0i41.83086",
    },
    {
        "titulo": "Stress in rhythmic gymnastics refereeing: A systematic review",
        "autores": "Debien, Paula Barreiros; Noce, Franco; "
                   "Debien, Jurema Barreiros Prado; da Costa, Varley Teoldo",
        "ano_publicacao": 2014,
        "observacoes": "Revisão sistemática sobre o estresse na arbitragem de "
                       "ginástica rítmica -- é sobre a psicologia de quem julga a "
                       "prova, não de quem compete, mas entra no escopo de "
                       "'variáveis psicológicas associadas à ginástica rítmica' "
                       "em sentido amplo. Revista da Educação Física, "
                       "DOI: 10.4025/reveducfis.v25i3.22031 — "
                       "https://doi.org/10.4025/reveducfis.v25i3.22031",
        "study_type": "Revisão sistemática",
    },
    {
        "titulo": "Psychological Intervention in a Rhythmic Gymnastics Team: "
                  "A Case Study",
        "autores": "Alvarez, Octavio; Falco, Coral; Estevan, Isaac; "
                   "Molina-Garcia, Javier; Castillo, Isabel",
        "ano_publicacao": 2013,
        "fator_impacto": 0.6,
        "observacoes": "Estudo de caso com 7 atletas espanholas da seleção "
                       "nacional sênior, 15-21 anos; 14 sessões em grupo entre "
                       "setembro e dezembro, com foco em clima motivacional, "
                       "orientação a metas, coesão, liderança do técnico e "
                       "habilidades psicológicas -- reduziu o clima ego-envolvido "
                       "e a orientação ao ego, e aumentou o clima envolvido na "
                       "tarefa. Revista de Psicología del Deporte, 22(2), 395-401 "
                       "(DOI não disponível) — "
                       "https://archives.rpd-online.com/rt/printerFriendly/v22-n2-alvarez-falco-estevan-molina-garcia-castillo/0.html",
    },
    {
        "titulo": "A Comparative Study in (Resilience and Immunity) "
                  "Psychological and the Level of Skillful Performance in Some "
                  "Ball Skills in Rhythmic Gymnastics Between Students of the "
                  "Second and Third Stages",
        "autores": "Dhahi, Nuha Mohsin; Shihab, Muhammad Hamza",
        "ano_publicacao": 2022,
        "fator_impacto": 0.2,
        "study_type": "Estudo transversal",
        "observacoes": "135 estudantes de educação física da Universidade de "
                       "Bagdá (segundo e terceiro ano); não houve diferença de "
                       "resiliência nem de imunidade psicológica entre as turmas, "
                       "mas as mais avançadas tiveram melhor desempenho técnico "
                       "em habilidades de bola. Revista Iberoamericana de "
                       "Psicología del Ejercicio y el Deporte, "
                       "DOI: 10.37310/jpesm.2023.10.2.10 — "
                       "https://doi.org/10.37310/jpesm.2023.10.2.10",
    },
    {
        "titulo": "Evaluation and analysis of psychological skills related to "
                  "athletic performance in rhythmic gymnasts",
        "autores": "Jaenes Sanchez, Jose Carlos; Carmona Marquez, Jose; "
                   "Lopa Peralto, Estefania",
        "ano_publicacao": 2010,
        "fator_impacto": 0.8,
        "observacoes": "86 ginastas (todas as categorias); ginastas que "
                       "trabalham com psicólogo esportivo como parte do "
                       "treinamento pontuaram mais alto em controle do estresse, "
                       "avaliação de desempenho e habilidade mental, medidos "
                       "pelo CPRD. Revista Iberoamericana de Psicología del "
                       "Ejercicio y el Deporte, 5, 15-28 (DOI não disponível) — "
                       "https://www.redalyc.org/pdf/3111/311126267002.pdf",
    },
    {
        "titulo": "Body and Performance in Rhythmic Gymnastics: Science or Belief?",
        "autores": "de Oliveira, Laura; Costa, Vítor Ricci; "
                   "Antualpa, Kizzy Fernandes; Nunomura, Myrian",
        "ano_publicacao": 2023,
        "fator_impacto": 0.7,
        "observacoes": "28 ginastas brasileiras de 13-16 anos, em entrevistas e "
                       "análise temática; a insatisfação com o corpo é reforçada "
                       "por técnicos, juízas e outras atletas, que sustentam a "
                       "crença de um tipo de corpo 'ideal' ligado a melhor "
                       "desempenho -- técnicos usam o peso na balança para guiar "
                       "emagrecimento, e as ginastas relataram uso de laxantes e "
                       "restrição calórica autoimposta. Science of Gymnastics "
                       "Journal, DOI: 10.52165/sgj.13.3.311-321 — "
                       "https://doi.org/10.52165/sgj.13.3.311-321",
    },
    {
        "titulo": "Sources of Organizational Stress Among Youth Rhythmic "
                  "Gymnasts: An Interpretative Phenomenological Analysis",
        "autores": "Penna, Eduardo Macedo; Filho, Edson; Bentes, Livia Maria "
                   "Neves; Ferreira, Renato Melo; Pires, Daniel Alvarez",
        "ano_publicacao": 2023,
        "fator_impacto": 0.7,
        "observacoes": "6 ginastas brasileiras de ~15 anos, em entrevistas "
                       "semiestruturadas; aprisionamento no esporte ('sport "
                       "entrapment'), gestão do tempo e preocupação com a imagem "
                       "corporal apareceram como estressores, somados à pressão "
                       "de técnicos, colegas e pais -- as atletas relataram "
                       "ansiedade competitiva antes, durante e depois da "
                       "competição. Science of Gymnastics Journal, "
                       "DOI: 10.52165/sgj.15.3.427-439 — "
                       "https://doi.org/10.52165/sgj.15.3.427-439",
    },
    {
        "titulo": "Risks of Eating and Image Disorders are Correlated with "
                  "Energy and Macronutrient Inadequacies in Youth Rhythmic "
                  "Gymnastics",
        "autores": "Jardim, Maria Letícia; Valencio, Ana Clara Justino; "
                   "Menegassi, Lizia Nardi; da Silva, Ricardo Azevedo; "
                   "Carteri, R. B.",
        "ano_publicacao": 2022,
        "fator_impacto": 0.7,
        "study_type": "Estudo transversal",
        "observacoes": "18 atletas brasileiras de nível nacional, 12-19 anos; "
                       "risco de transtorno alimentar e distorção de imagem "
                       "corporal correlacionaram-se com o IMC e, inversamente, "
                       "com a ingestão de carboidrato, lipídio e energia por "
                       "quilo de peso -- reforça a importância de acompanhamento "
                       "nutricional multidisciplinar. Science of Gymnastics "
                       "Journal, DOI: 10.52165/sgj.14.1.85-96 — "
                       "https://doi.org/10.52165/sgj.14.1.85-96",
    },
    {
        "titulo": "Sports Profile of Elite Athletes in Rhythmic Gymnastics",
        "autores": "Ivanova, Ivanova Vesela",
        "ano_publicacao": 2022,
        "fator_impacto": 1.2,
        "observacoes": "63 ginastas de elite dos EUA, Singapura e Taiwan; "
                       "comparação de perfil esportivo (comprometimento, "
                       "qualidades psicológicas, habilidades técnicas e mentais) "
                       "entre as três seleções -- ginastas de Singapura e Taiwan "
                       "relataram mais dificuldade de comunicação com o técnico, "
                       "mas maior autoconsciência para melhorar; as dos EUA "
                       "mostraram falhas de consistência no treino. Science of "
                       "Gymnastics Journal, DOI: 10.52165/sgj.14.1.73-83 — "
                       "https://doi.org/10.52165/sgj.14.1.73-83",
    },
    {
        "titulo": "Social Physique Anxiety, Disturbed Eating Attitudes and "
                  "Behaviors, and Perceived Pressure for Thin Body in "
                  "Competitive Rhythmic and Aerobic Gymnasts",
        "autores": "Ioannidou, Christina; Venetsanou, Fotini",
        "ano_publicacao": 2019,
        "fator_impacto": 0.7,
        "study_type": "Estudo transversal",
        "observacoes": "41 ginastas de rítmica e 49 de aeróbica, nível "
                       "competitivo; sem diferença entre as duas modalidades em "
                       "ansiedade de físico social (SPA) nem em comportamento "
                       "alimentar perturbado (DEAB), mas atletas de aeróbica "
                       "sentiram mais pressão dos pais para ter corpo magro; "
                       "40% da amostra combinada apresentou DEAB, e essas atletas "
                       "tiveram SPA e pressão percebida significativamente "
                       "maiores. Science of Gymnastics Journal, "
                       "DOI: 10.52165/sgj.11.3.331-342 — "
                       "https://doi.org/10.52165/sgj.11.3.331-342",
    },
    {
        "titulo": "Evaluation of an Intervention Program on Body Esteem, "
                  "Eating Attitudes and Pressure to be Thin in Rhythmic "
                  "Gymnastics Athletes",
        "autores": "Kosmidou, Evdoksia; Fachantidou-Tsiligiroglou, A.",
        "ano_publicacao": 2015,
        "study_type": "Ensaio controlado",
        "observacoes": "49 ginastas gregas (29 grupo intervenção, 20 controle), "
                       "programa de 3 meses; o grupo intervenção aumentou "
                       "autoestima corporal e reduziu atitudes alimentares de "
                       "risco e pressão percebida para emagrecer, enquanto o "
                       "grupo controle piorou nesses mesmos indicadores -- "
                       "primeira intervenção controlada do tipo aplicada à "
                       "ginástica rítmica na Grécia. Science of Gymnastics "
                       "Journal, DOI: 10.52165/sgj.7.3.23-36 — "
                       "https://doi.org/10.52165/sgj.7.3.23-36",
    },
    {
        "titulo": "Performance Level, Abilities and Psychological "
                  "Characteristics in Young Junior Rhythmic Gymnasts: The Role "
                  "of Sport Experience",
        "autores": "Zisi, Vasiliki; Giannitsopoulou, Evgenia; "
                   "Vassiliadou, Olga; Pollatou, Elisana; Kioumourtzoglou, Efthimis",
        "ano_publicacao": 2009,
        "fator_impacto": 0.7,
        "study_type": "Estudo transversal",
        "observacoes": "33 ginastas gregas de elite, 11-12 anos, classificadas em "
                       "três níveis de desempenho; o nível mais alto superou o "
                       "mais baixo apenas em agrupamento de memória e "
                       "autoconfiança, diferença explicada pela experiência "
                       "esportiva -- motivação intrínseca ficou modesta, "
                       "atribuída ao momento da coleta (três meses antes das "
                       "competições). International Quarterly of Sport Science, "
                       "4, 1-13 (DOI não disponível; periódico corrigido nesta "
                       "atualização -- a planilha original trazia 'Science of "
                       "Gymnastics Journal') — "
                       "https://www.researchgate.net/publication/234106492_PERFORMANCE_LEVEL_ABILITIES_AND_PSYCHOLOGICAL_CHARACTERISTICS_IN_YOUNG_JUNIOR_RHYTHMIC_GYMNASTS_THE_ROLE_OF_SPORT_EXPERIENCE",
    },
    {
        "titulo": "The Precompetitive Anxiety Impacts Immediately Actual "
                  "Gymnastics' Performance or Sustain During Routine's Outcomes "
                  "Over the Execution Time",
        "autores": "Nassib, Sarra Hammoudi; Mkaouer, Bessem; "
                   "Riahi, Sabra Hammoudi; Wali, Sameh Menzli; Nassib, Sabri",
        "ano_publicacao": 2017,
        "fator_impacto": 1.3,
        "study_type": "Estudo transversal",
        "observacoes": "16 ginastas tunisianas de nível internacional, ~14 anos; "
                       "ansiedade cognitiva e somática (CSAI-2) foram maiores em "
                       "competição do que em treino, com autoconfiança estável "
                       "entre as duas situações -- o efeito da ansiedade sobre o "
                       "desempenho foi maior na rotina de corda do que na de "
                       "maças. Sport Sciences for Health, "
                       "DOI: 10.1007/s11332-017-0347-8 — "
                       "https://doi.org/10.1007/s11332-017-0347-8",
    },
    {
        "titulo": "Assessment of Nutritional-Dietary Status, Body Composition, "
                  "Eating Behavior, and Perceived Image in Rhythmic Gymnastics "
                  "Athletes",
        "autores": "Martínez-Rodríguez, A.; Reche-García, C.; "
                   "Martínez-Fernández, M. D. C.; Martínez-Sanz, J. M.",
        "ano_publicacao": 2020,
        "study_type": "Estudo transversal",
        "observacoes": "33 ginastas espanholas (juvenil e adulto); risco de "
                       "transtorno alimentar, estado nutricional, composição "
                       "corporal, comportamento alimentar e preocupações "
                       "percebidas com a imagem corporal (anotação da própria "
                       "equipe na planilha original). Nutrición Hospitalaria, "
                       "37(6), 1217-1225, DOI: 10.20960/nh.03141 (confirmado via "
                       "PubMed, PMID 33155479; periódico corrigido nesta "
                       "atualização -- a planilha original trazia, no lugar do "
                       "nome do periódico, a tradução do próprio título) — "
                       "https://doi.org/10.20960/nh.03141",
    },
    {
        "titulo": "Developing Social Skills Through Rhythmic Gymnastics in "
                  "American Sport",
        "autores": "Pushkina, Natalia",
        "ano_publicacao": 2024,
        "observacoes": "Estudo de caso de métodos mistos com alunas da "
                       "Vitrychenko Gymnastics Academy (Illinois, EUA), seus "
                       "técnicos e os pais; a ginástica rítmica apareceu ligada "
                       "ao desenvolvimento de disciplina, autoconfiança, "
                       "inteligência emocional, autodisciplina e adaptabilidade, "
                       "entre outras habilidades sociais -- fatores internos "
                       "(motivação pessoal) e externos (estilo do técnico, apoio "
                       "parental) foram identificados como influências. Futurity "
                       "of Social Sciences, 2(2), 79-102, "
                       "DOI: 10.57125/FS.2024.06.20.05 (periódico confirmado "
                       "nesta atualização -- a planilha original não o "
                       "informava) — https://doi.org/10.57125/FS.2024.06.20.05",
    },
    {
        "titulo": "Examination of Rhythmic Gymnasts Attitudes Towards Healthy "
                  "Nutrition and Social Physique Concerns",
        "autores": "Dogan, Duygu",
        "ano_publicacao": 2025,
        "study_type": "Estudo transversal",
        "observacoes": "90 ginastas turcas de rítmica, todas as categorias; "
                       "examina atitudes em relação à alimentação saudável e "
                       "preocupação com o físico social -- encontrado na busca no "
                       "Bibliometrix/Web of Science da equipe, fora da planilha "
                       "principal de 40 artigos. Science of Gymnastics Journal, "
                       "DOI: 10.52165/sgj.17.2.317-329 — "
                       "https://doi.org/10.52165/sgj.17.2.317-329",
    },
)


def semear_estudos_iniciais(db: Database, criado_por: int | None = None) -> dict[str, Any]:
    """Cadastra `ESTUDOS_SEMEADOS`, pulando quem já está no banco pelo
    título -- seguro de rodar de novo quando a busca for refeita."""
    novos, ja_existiam = [], []
    for estudo in ESTUDOS_SEMEADOS:
        if db.scalar("SELECT 1 FROM ginastica_ritmica_estudos WHERE titulo = ?",
                     (estudo["titulo"],)):
            ja_existiam.append(estudo["titulo"])
            continue
        gravar_estudo(db, criado_por=criado_por, **estudo)
        novos.append(estudo["titulo"])
    return {"novos": novos, "ja_existiam": ja_existiam}
