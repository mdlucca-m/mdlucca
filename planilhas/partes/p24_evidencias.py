# ============================================================================
# 24) EVIDÊNCIAS CIENTÍFICAS
# ============================================================================
wsEv = wb.create_sheet("Evidências")
banner(wsEv, "BASE DE EVIDÊNCIAS — PREPARAÇÃO FÍSICA PARA VOLEIBOL",
       "Referências que sustentam as escolhas metodológicas desta planilha: periodização em blocos, LPO, pliometria, "
       "treino baseado em velocidade, perfil força-velocidade, antropometria e controle de carga.", 8, "1F6F4A")
larguras(wsEv, {"A":5,"B":30,"C":66,"D":30,"E":26,"F":72,"G":30,"H":54})
cab_tabela(wsEv, 6, ["Nº","Autores (ano)","Título","Periódico","Tipo de Estudo","Achado Principal",
                     "Onde é aplicado na planilha","Link"])
CS = "https://consensus.app/papers/details/"
EVID = [
("PERIODIZAÇÃO EM BLOCOS",),
("Issurin (2010)","New Horizons for the Methodology and Physiology of Training Periodization","Sports Medicine","Revisão",
 "Base conceitual da periodização em blocos: mesociclos com cargas altamente concentradas em poucas capacidades, em vez do desenvolvimento simultâneo de muitas.",
 "Aba Bloco Base — estrutura acumulação/transmutação/realização", CS+"f382ecd540d75e349364da666ea4c096/"),
("Issurin (2016)","Benefits and Limitations of Block Periodized Training Approaches to Athletes' Preparation","Sports Medicine","Revisão",
 "O modelo em blocos MULTIALVO superou a preparação tradicional em 28 estudos com esportes coletivos, de resistência e de força; o modelo unidirecional concentrado só serve a disciplinas de uma única capacidade.",
 "Bloco Base — escolha do modelo multialvo, e não do concentrado puro", CS+"c45056fdee8e538689e4b3e3cedc15f7/"),
("Stone et al. (2021)","Periodization and Block Periodization in Sports: Emphasis on Strength-Power Training","J Strength Cond Res","Narrativa",
 "Separa PERIODIZAÇÃO (fases e prazos) de PROGRAMAÇÃO (exercícios, volume, intensidade); esportes coletivos precisam da variante de blocos com múltiplos alvos.",
 "Macrociclo, Mesociclo e Bloco Base", CS+"f256bd9422b65ada8b27fd28db364b55/"),
("Rønnestad et al. (2018)","Block periodization of strength and endurance training is superior to traditional periodization in ice hockey players","Scand J Med Sci Sports","ECR",
 "Com volume e intensidade IGUAIS, o grupo em blocos melhorou mais o torque de extensores de joelho e o VO2máx que o grupo tradicional.",
 "Bloco Base — justificativa do modelo", CS+"db1410c0c5ca5209811bb4e58eb7ec1b/"),
("Manchado et al. (2017)","Effects of Two Different Training Periodization Models on Elite Female Team Handball Players","J Strength Cond Res","Longitudinal",
 "Blocos superaram a periodização tradicional em salto agachado (+5,97%), CMJ (+8,76%), preensão manual, 1RM de supino e sprints de 10 e 20 m.",
 "Bloco Base — transferência para esporte coletivo de quadra", CS+"d8c5245dada2544285c48a147bbc308f/"),
("Bartolomei et al. (2014)","A Comparison of Traditional and Block Periodized Strength Training Programs in Trained Athletes","J Strength Cond Res","ECR",
 "Em 15 semanas com volume igual, o grupo em blocos ampliou mais a área sob a curva força-potência de MMSS; sem diferença em MMII.",
 "Bloco Base — expectativa realista de efeito", CS+"51ebe06543295477a6e3b87ed2fffb56/"),
("Painter et al. (2012)","Strength gains: block versus daily undulating periodization weight training among track and field athletes","Int J Sports Physiol Perform","ECR",
 "Sem diferença estatística entre blocos e ondulatório diário, mas os blocos foram mais EFICIENTES: mais ganho por unidade de volume-carga.",
 "Prescrição Força — controle de tonelagem", CS+"37aba2c3463d5db18d9682ba4f77c696/"),
("Gavanda et al. (2019)","The Effect of Block Versus Daily Undulating Periodization on Strength and Performance in Adolescent Football Players","Int J Sports Physiol Perform","ECR",
 "Em 12 semanas com adolescentes, blocos e ondulatório diário produziram ganhos equivalentes de massa muscular, força e potência.",
 "Bloco Base — ressalva para categorias de base (Sub-19)", CS+"8fc30754f83059c691319023497a547a/"),
("Micke et al. (2026)","Block periodization vs. traditional periodization in high-intensity functional training","Front Physiol","Crossover randomizado",
 "Blocos produziram maior ganho de força máxima; houve queda AGUDA do CMJ na semana de carga concentrada, confirmando overreaching funcional.",
 "Semanas 3 e 7 (CHOQUE) — o que esperar e o que monitorar", CS+"cb319ced4f525fccb29ad766c357d07a/"),
("FORÇA E POTÊNCIA NO VOLEIBOL",),
("Berriel et al. (2022)","Does Complex Training Enhance Vertical Jump Performance and Muscle Power in Elite Male Volleyball Players?","Int J Sports Physiol Perform","ECR",
 "Em 4 semanas, salto e potência melhoraram tanto com treino de saltos quanto com treino complexo; acrescentar estímulo pesado NÃO trouxe ganho adicional em atletas de elite.",
 "Prescrição Força — não sobrecarregar o elenco de elite com estímulo pesado desnecessário", CS+"342916b5711d52e1a81ed4f1f87bdecb/"),
("Rong et al. (2024)","Effects of Cluster vs. Traditional Sets Complex Training on Trained Male Volleyball Players","J Sports Sci Med","ECR",
 "Em 6 semanas, séries em CLUSTER produziram melhores CMJ, salto de ataque, T-test e potência de pico, além de menor cortisol de repouso, que séries tradicionais.",
 "Semana 7 do Bloco Base — agachamento em cluster 2+2", CS+"cc1f0acd730e55469151f4ddd60ad2d8/"),
("Cin et al. (2021)","Cluster Resistance Training Results Higher Improvements on Sprint, Agility, Strength and Vertical Jump in Professional Volleyball Players","Turkiye Klinikleri J Sports Sci","ECR",
 "Cluster superou o treino tradicional em 1RM de agachamento, terra, supino e pullover, sprint de 20 m, T-test e salto vertical.",
 "Prescrição Força — configuração de séries", CS+"5d6956f74040559da080d9e04b1cb3cc/"),
("Moussi et al. (2025)","Effects of two periodization models (linear vs. nonlinear) in young adult male volleyball players","J Bodyw Mov Ther","ECR",
 "6 semanas: ambos eficazes. O não linear foi melhor para salto vertical, salto de bloqueio e SJ; o linear, melhor para sprint de 10 m.",
 "Microciclo — variação de intensidade dentro da semana", CS+"9c60d35e1632588d8f6e0bf8707415fd/"),
("Wang et al. (2022)","Effect of Leg Half-Squat Training With Blood Flow Restriction Under Different External Loads in Volleyball Players","Dose-Response","ECR",
 "Carga alta (70% 1RM) foi o que melhorou o salto; carga baixa isolada aumentou pouco a força e não melhorou o salto.",
 "Prescrição Força — justificativa das faixas de 80-90% 1RM", CS+"9f2b4f05a98c52f2827718b3afa7bd36/"),
("Marques et al. (2009)","Physical Fitness Qualities of Professional Volleyball Players: Determination of Positional Differences","J Strength Cond Res","Transversal",
 "Centrais e opostos são os mais altos, pesados e fortes no supino; levantadores têm o pior desempenho no agachamento paralelo.",
 "Cadastro e Prescrição Força — individualização por posição", CS+"7f91b9f3f4aa502db2c5986d5aff1136/"),
("PLIOMETRIA",),
("Sáez de Villarreal et al. (2009)","Determining Variables of Plyometric Training for Improving Vertical Jump Height Performance","J Strength Cond Res","Meta-análise (56 estudos)",
 "Mais de 10 semanas, mais de 20 sessões, programas de alta intensidade com mais de 50 saltos por sessão e a COMBINAÇÃO de tipos de salto (SJ + CMJ + drop jump) maximizam o ganho. Peso adicional não trouxe benefício extra.",
 "Bloco Base e Saltos — dose de contatos por semana", CS+"e60a777fc6a654d29ca1c61c7d29da22/"),
("Sáez-Sáez de Villarreal et al. (2010)","Does plyometric training improve strength performance? A meta-analysis","J Sci Med Sport","Meta-análise",
 "Combinar pliometria COM treino de força supera usar qualquer uma delas isoladamente; mais de 40 saltos por sessão em alta intensidade otimiza o ganho de força.",
 "Sessões A e B — força e pliometria na mesma semana", CS+"049130fbe9d05f56a4810dde0ff51ef8/"),
("Iranpour et al. (2025)","The effects of plyometric training with speed and weight overloads on volleyball players","PLOS One","ECR",
 "Pliometria com sobrecarga de velocidade E de peso foi superior à pliometria simples em salto de ataque, altura de salto e taxa de produção de força.",
 "Sessão B — salto unilateral com sobrepeso e jump squat", CS+"07f5b6752bba54198af3c2d0e5cd9d87/"),
("Yu et al. (2025)","The influence of training surface on the effectiveness of plyometric training in volleyball players","Scientific Reports","ECR",
 "Pliometria na AREIA e na ÁGUA gerou mais ganho de CMJ que no solo; a aquática também superou o solo em sprint, mudança de direção e força máxima.",
 "Aba Saltos — coluna Superfície", CS+"75bc1970db385dd2a7fc798a2d496428/"),
("Atıcı et al. (2025)","Effects of plyometric and agility-based training in adolescent male volleyball players","Ped Phys Cult Sports","Experimental controlado",
 "8 semanas de pliometria: +14,1% no salto vertical, +13,25% na potência de pico e +3,07% no sprint. Agilidade melhora COD, não potência.",
 "Bloco Base — expectativa de ganho em 8 semanas", CS+"97766fe403ed5d0db00747ff1e0c3b71/"),
("Zhou et al. (2024)","Meta-analysis of the effect of plyometric training on youth basketball players","Front Physiol","Meta-análise (24 estudos)",
 "Pliometria de BAIXA frequência (1-2x/semana), ALTO volume (>150 saltos/semana) e de tipo MISTO melhorou salto, sprint, COD e equilíbrio; alta frequência com baixo volume só melhorou o salto.",
 "Saltos — faixas de referência de volume semanal", CS+"127de9c932de5022bf7207226214e479/"),
("LEVANTAMENTO DE PESO OLÍMPICO (LPO) E DERIVADOS",),
("Suchomel et al. (2015)","Weightlifting Pulling Derivatives: Rationale for Implementation and Application","Sports Medicine","Revisão",
 "Clean pull, snatch pull, hang high pull, jump shrug e mid-thigh pull dão estímulo igual ou melhor que os levantamentos completos, com técnica mais simples — ideal para quem não é levantador de peso.",
 "Sessões A e C — escolha de puxadas em vez do clean completo", CS+"e55b8645d8505f2bb685fbf171e41da5/"),
("Suchomel et al. (2017)","Force-Time-Curve Comparison Between Weight-Lifting Derivatives","Int J Sports Physiol Perform","Transversal",
 "O jump shrug produziu maior força relativa, impulso relativo e taxa de produção de força que o hang power clean e o hang high pull.",
 "Biblioteca de Exercícios — seleção de derivados", CS+"832a4d9da8035145b9b54feac5caa891/"),
("Suchomel et al. (2017)","Power-Time Curve Comparison between Weightlifting Derivatives","J Sports Sci Med","Transversal",
 "Cargas de 30-45% 1RM maximizam a potência no jump shrug e no hang high pull; 65-80% 1RM é a faixa ótima para o hang power clean.",
 "Prescrição Força — %1RM prescrito para o LPO", CS+"d4fd5a5594c45196bd8036e06e06ddd5/"),
("Suchomel et al. (2020)","Training With Weightlifting Derivatives: The Effects of Force and Velocity Overload Stimuli","J Strength Cond Res","ECR (10 semanas)",
 "Sobrecarga específica de força e de velocidade nas puxadas produziu os maiores ganhos em força isométrica relativa, sprint e mudança de direção.",
 "Semanas 6 e 7 — clean pull com carga supramáxima (95%)", CS+"bf6021458f755ca3a8d88965905119ed/"),
("Meechan et al. (2025)","The Effect of Load on Subphase Analysis During the Hang Pull","J Strength Cond Res","Transversal",
 "40% 1RM maximiza a velocidade de propulsão e 140% 1RM maximiza a força: o hang pull cabe tanto no mesociclo de força máxima quanto no de força-velocidade.",
 "Semana 6 — justificativa da carga supramáxima", CS+"45131b3cbdca5cfdb31431fdb5b7b004/"),
("James et al. (2022)","Rate of Force Development Adaptations After Weightlifting-Style Training: The Influence of Power Clean Ability","J Strength Cond Res","ECR",
 "Atletas FORTES no power clean melhoram a RFD em cargas leves; atletas FRACOS deslocam-se para o lado da força do perfil. Quem é fraco precisa primeiro de força máxima.",
 "Perfil F-V-P — decisão de ênfase por atleta", CS+"df935f1fd927508eb7134ed0c1a65ea2/"),
("Mehls et al. (2022)","An Examination of Loading Profiles for Youth Athletes Performing the Hang Power Clean","Mont J Sports Sci Med","Transversal",
 "Em jovens, a potência é máxima a ~70% 1RM, mas a velocidade da barra cai em cargas mais leves que em adultos: precisam de mais força antes de treinar pesado.",
 "Categoria Sub-19 — cautela com carga alta", CS+"011fd93e694d529a90e28eae7334b9c4/"),
("TREINAMENTO BASEADO EM VELOCIDADE (VBT)",),
("Weakley et al. (2020)","Velocity-Based Training: From Theory to Application","Strength Cond J","Revisão aplicada",
 "Como montar perfis carga-velocidade, dar feedback objetivo, usar limiares de perda de velocidade e integrar o VBT aos modelos de periodização.",
 "Prescrição Força — colunas de velocidade", CS+"a39766be63eb5ac7a0b76b6229d01c5f/"),
("García Ramos (2023)","Resistance Training Intensity Prescription Methods Based on Lifting Velocity Monitoring","Int J Sports Med","Revisão",
 "Três formas de prescrever %1RM pela velocidade — zonas, relação generalizada e relação INDIVIDUALIZADA — e os fatores que afetam a precisão de cada uma.",
 "Tabela carga-velocidade da aba Prescrição Força", CS+"7f88e021c22957a980dea51d84dd960a/"),
("Balsalobre-Fernández et al. (2021)","The Implementation of Velocity-Based Training Paradigm for Team Sports","Sports","Revisão",
 "Como aplicar VBT em elencos grandes, combinando métricas de velocidade com escalas subjetivas e estimando o 1RM diariamente.",
 "Prescrição Força — uso prático com o elenco todo", CS+"bd88451c5a7955fa8fa376e203a6aa0e/"),
("Hickmott et al. (2022)","The Effect of Load and Volume Autoregulation on Muscular Strength and Hypertrophy","Sports Med Open","Meta-análise",
 "Perda de velocidade ≤ 25% favorece FORÇA (menos fadiga aguda, mais adaptação crônica); perda > 20-25% favorece HIPERTROFIA por acumular mais volume.",
 "Coluna Perda de Velocidade Limite (10-15% no bloco de força)", CS+"0e6bb3b98d875b1392222cf931190cb8/"),
("Jiménez-Reyes et al. (2021)","Differences between adjusted vs. non-adjusted loads in velocity-based training","PeerJ","ECR (8 semanas)",
 "Sem ajuste diário pela velocidade, os atletas treinaram ~15% 1RM mais leve que o programado e não chegaram à intensidade alvo.",
 "Prescrição Força — por que registrar a velocidade obtida", CS+"c8cd652b51485409ae4e353f96d0cecd/"),
("Greig et al. (2023)","The Predictive Validity of Individualised Load-Velocity Relationships for Predicting 1RM","Sports Medicine","Revisão sistemática com meta-análise de dados individuais",
 "A estimativa do 1RM pela velocidade SUPERESTIMA a força real em ~3,7% (SEE ~9,8%). Use teste direto sempre que possível; a velocidade serve para acompanhar tendências.",
 "Força 1RM — ressalva sobre estimativas", CS+"94ecaddd8a3257c1ac5ba343f1a358be/"),
("LeMense et al. (2024)","Validity of Using the Load-Velocity Relationship to Estimate 1RM in the Back Squat","J Strength Cond Res","Revisão sistemática com meta-análise",
 "O método do limiar de velocidade mínima superestima o 1RM no agachamento livre e não é opção confiável de substituição do teste.",
 "Força 1RM — ressalva sobre estimativas", CS+"9f572c3e92ea5983aec88ccbe3db6da9/"),
("Morán-Navarro et al. (2020)","Load-velocity relationship of the deadlift exercise","Eur J Sport Sci","Transversal",
 "Velocidade média no 1RM do terra ≈ 0,24 m/s, consistente entre atletas de força diferente; a potência é máxima a ~60% 1RM.",
 "Tabela carga-velocidade — coluna Terra", CS+"2699a62b8e4350bd918acff60c192346/"),
("PERFIL FORÇA-VELOCIDADE-POTÊNCIA",),
("Morin & Samozino (2016)","Interpreting Power-Force-Velocity Profiles for Individualized and Specific Training","Int J Sports Physiol Perform","Revisão aplicada",
 "Método de campo para calcular F0, V0, Pmax e o desequilíbrio força-velocidade a partir da altura do salto com cargas progressivas e da distância de push-off.",
 "Perfil F-V-P — fórmulas usadas na planilha", CS+"0b47720f42de500d95c89cf488fa6bc6/"),
("Jiménez-Reyes et al. (2017)","Effectiveness of an Individualized Training Based on Force-Velocity Profiling during Jumping","Front Physiol","ECR",
 "Treino individualizado pelo desequilíbrio F-V melhorou o salto (+7 a +14%) mais que um programa igual para todos.",
 "Perfil F-V-P — lógica da recomendação por perfil", CS+"ac9d7b3fb607592887e952929efe8b2e/"),
("Jiménez-Reyes et al. (2019)","Optimized training for jumping performance using the force-velocity imbalance","PLoS ONE","Longitudinal",
 "O tempo necessário para corrigir o perfil é proporcional ao desequilíbrio inicial (12,6 ± 4,6 semanas em média); os ganhos se mantiveram após 3 semanas sem treino específico.",
 "Perfil F-V-P — duração realista da intervenção", CS+"07f17089e4935553836bfe8b6c443414/"),
("Li et al. (2026)","FV profile-based individualized vs. non-individualized strength training: systematic review and meta-analysis","BMC Sports Sci Med Rehabil","Meta-análise",
 "Vantagem grande do treino individualizado para F0, V0, desequilíbrio F-V e altura de salto; SEM efeito sobre Pmax e sprint.",
 "Perfil F-V-P — o que esperar de fato", CS+"bdbc8fc9675a54d29cca3b5eabf701bb/"),
("Lindberg et al. (2021)","Should we individualize training based on force-velocity profiling to improve physical performance?","Scand J Med Sci Sports","ECR (10 semanas)",
 "RESSALVA: não houve diferença entre treinar a favor, contra ou independentemente do perfil ótimo em 40 atletas de esportes coletivos.",
 "Perfil F-V-P — aviso na própria aba", CS+"5eda6a3b427f55098d20848a20b32336/"),
("Solberg et al. (2025)","Force-velocity profile based training to improve vertical jump performance: systematic review and meta-analysis","Scientific Reports","Meta-análise",
 "RESSALVA: os ganhos de salto com treino otimizado foram comparáveis aos do treino não otimizado; permanece incerto se o método é superior.",
 "Perfil F-V-P — aviso na própria aba", CS+"92d673eefa9b57158c87d11c3ec5fe71/"),
("Bobbert et al. (2024)","Is the Force-Velocity Profile for Free Jumping a Sound Basis for Individualized Jump Training Prescriptions?","Med Sci Sports Exerc","Simulação musculoesquelética",
 "RESSALVA: mudanças no perfil podem refletir aprendizado da tarefa (habilidade de saltar com e sem carga) e não adaptação neuromuscular.",
 "Perfil F-V-P — aviso na própria aba", CS+"6ab00db8b08e56fd86ec01c0c1b4054a/"),
("CARGA DE SALTOS E MONITORAMENTO",),
("Skazalski et al. (2018)","A valid and reliable method to measure jump-specific training and competition load in elite volleyball players","Scand J Med Sci Sports","Validação",
 "Dispositivo inercial contou 99,3% dos 3.637 saltos de treinos e jogos, mas superestimou a altura em ~5,5 cm: serve para CONTAR saltos, não para medir salto máximo.",
 "Aba Saltos — como registrar o jump count", CS+"4113ba2b7f9254a78670457ae8f99ac2/"),
("Charlton et al. (2017)","A simple method for quantifying jump loads in volleyball athletes","J Sci Med Sport","Validação",
 "Propõe um índice de carga externa a partir do produto entre número de saltos e energia cinética média.",
 "Aba Saltos — conceito de carga de salto", CS+"9895fbb37b4f5a628d174d7e58c624c4/"),
("Lin et al. (2024)","Quantifying internal and external training loads in collegiate male volleyball players","BMC Sports Sci Med Rehabil","Longitudinal (29 semanas)",
 "Carga interna correlaciona com o número de saltos (ρ = 0,477); MUITOS saltos associam-se a MENOR altura média e a menos saltos acima de 80% do máximo — sinal de fadiga.",
 "Saltos e Carga (PSE) — leitura conjunta", CS+"e05450c06ad55ab29a85378baaaf6adb/"),
("Taylor et al. (2022)","Quantifying External Load and Injury Occurrence in Women's Collegiate Volleyball Players","J Strength Cond Res","Longitudinal",
 "Atletas que se lesionaram tiveram MAIOR VARIABILIDADE da carga (CV 54% vs 41%): a instabilidade da carga importa tanto quanto o volume absoluto.",
 "Saltos — alerta de variação acima de 30% entre semanas", CS+"49131de7b79c5ffa86f91d25bcf2469a/"),
("Wang et al. (2025)","Comparison of external load and specific activities of starters vs. non-starters in men's professional volleyball","J Men's Health","Transversal",
 "Titulares acumulam mais player load, saltos totais e saltos de alta intensidade; centrais lideram os saltos de alta intensidade e os esforços repetidos.",
 "Saltos — controle individual por posição e por minutagem", CS+"8c773e2fbe795c968e9ea5185529f375/"),
("Villarejo-García et al. (2023)","Use, Validity and Reliability of Inertial Movement Units in Volleyball","Sensors","Revisão sistemática",
 "As IMUs têm boa validade para CONTAR saltos; a confiabilidade entre medidas de ALTURA ainda é limitada e contraditória.",
 "Saltos — o que confiar no dado do dispositivo", CS+"9be281c8d4d25bfaa2a0d31a09c1c0f8/"),
("ANTROPOMETRIA E PERFIL DO VOLEIBOLISTA",),
("Sheppard et al. (2009)","An Analysis of Playing Positions in Elite Men's Volleyball","J Strength Cond Res","Transversal (142 atletas)",
 "Centrais executam muito mais saltos de bloqueio e de ataque que levantadores e ponteiros; a seleção adulta supera a de base no CMJ e no salto de ataque RELATIVOS.",
 "Cadastro e Testes — metas por posição", CS+"acb87a06dc0b57e7896f92d25162767f/"),
("Palao et al. (2014)","Anthropometric, Physical, and Age Differences by the Player Position and the Performance Level in Volleyball","J Hum Kinet","Transversal (2.906 atletas)",
 "Normas de estatura, massa, alcance de ataque e alcance de bloqueio por posição em Jogos Olímpicos e Mundiais entre 2000 e 2012.",
 "Testes — referências de alcance por posição", CS+"bed94db8efef54d0b856b82b62dadcaf/"),
("Toselli & Campa (2018)","Anthropometry and Functional Movement Patterns in Elite Male Volleyball Players of Different Competitive Levels","J Strength Cond Res","Transversal",
 "O que separou as duas divisões foram medidas NÃO modificáveis (largura de úmero, estatura) e MODIFICÁVEIS (perímetro de braço contraído e área muscular do braço).",
 "Antropometria — perímetros e área muscular do braço", CS+"5d2c1a9f86b35fd89bf83100980361d1/"),
("Giannopoulos et al. (2017)","Somatotype, Level of Competition, and Performance in Attack in Elite Male Volleyball","J Hum Kinet","Transversal",
 "Atletas da divisão A1 são mais altos, pesados, musculosos e menos endomórficos que os da A2; centrais e opostos são endomorfo-ectomorfos.",
 "Antropometria — somatotipo Heath-Carter", CS+"8eb017eaf75f51948d230ec23aa8d1dd/"),
("De la Rosa et al. (2025)","Positional Profiling of Anthropometric, Baropodometric, and Grip Strength Traits in Male Volleyball Players","J Funct Morphol Kinesiol","Transversal (92 Sub-23)",
 "Centrais, ponteiros e opostos superam líberos e levantadores na maioria das medidas de membro superior; largura da mão e área muscular do braço predizem a preensão manual.",
 "Antropometria — perfil por posição", CS+"7dcedc0290ee5117bc3e007990be1d87/"),
("MÉTODOS CLÁSSICOS DE CONTROLE (já usados na v1 da planilha)",),
("Foster et al. (2001)","A new approach to monitoring exercise training","J Strength Cond Res","Método",
 "Carga interna = PSE da sessão (0-10) × duração em minutos; base também da monotonia e do strain.","Aba Carga (PSE)",""),
("Gabbett (2016)","The training-injury prevention paradox: should athletes be training smarter and harder?","Br J Sports Med","Revisão",
 "Razão entre carga aguda (7 dias) e crônica (28 dias) como ferramenta de gestão de risco; interpretar sempre com o contexto clínico.","Aba Carga (PSE) — ACWR",""),
("Hooper & Mackinnon (1995)","Monitoring overtraining in athletes","Sports Medicine","Revisão",
 "Índice de bem-estar de 4 itens (sono, estresse, fadiga e dor muscular), de 1 a 7 cada.","Aba Wellness",""),
("Sayers et al. (1999)","Cross-validation of three jump power equations","Med Sci Sports Exerc","Validação",
 "Equação de potência de pico a partir da altura do CMJ e da massa corporal.","Aba Testes — Potência de Pico",""),
("Jackson & Pollock (1978)","Generalized equations for predicting body density of men","Br J Nutr","Validação",
 "Equação de densidade corporal por 7 dobras cutâneas, convertida em % de gordura pela equação de Siri (1961).","Aba Antropometria",""),
("Carter & Heath (1990)","Somatotyping: Development and Applications","Cambridge University Press","Livro / método",
 "Método antropométrico de somatotipo (endomorfia, mesomorfia e ectomorfia).","Aba Antropometria — somatotipo",""),
]
EV_F = 7
r = EV_F
n = 0
for item in EVID:
    if len(item) == 1:
        wsEv.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
        c = wsEv.cell(r, 1, item[0])
        c.font = Font(name=F, size=10, bold=True, color=WHITE)
        c.fill = PatternFill("solid", fgColor=NAVY2)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        c.border = BORDER
        wsEv.row_dimensions[r].height = 20
        r += 1
        continue
    n += 1
    aut, tit, rev, tipo, ach, apl, url = item
    for c_, v in ((1, n), (2, aut), (3, tit), (4, rev), (5, tipo), (6, ach), (7, apl)):
        cc = wsEv.cell(r, c_, v)
        cc.font = Font(name=F, size=9, bold=(c_ == 2), color=NAVY2)
        cc.alignment = Alignment(horizontal="left" if c_ > 1 else "center", vertical="top", wrap_text=True, indent=1)
        cc.border = BORDER
        cc.fill = PatternFill("solid", fgColor=LIGHT if n % 2 else LIGHT2)
    lk = wsEv.cell(r, 8, url if url else "—")
    lk.border = BORDER
    lk.fill = PatternFill("solid", fgColor=LIGHT if n % 2 else LIGHT2)
    lk.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    if url:
        lk.hyperlink = url
        lk.font = Font(name=F, size=8, color="0563C1", underline="single")
    else:
        lk.font = Font(name=F, size=8, italic=True, color=GREY_T)
    wsEv.row_dimensions[r].height = 46
    r += 1
EV_L = r - 1
nota(wsEv, EV_L + 2, 2, "Os links levam ao registro do artigo. Referências sem link são obras clássicas de método, "
     "citadas pela fonte original.", 8)
wsEv.freeze_panes = "A7"
wsEv.auto_filter.ref = "A6:H{}".format(EV_L)
