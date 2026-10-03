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
