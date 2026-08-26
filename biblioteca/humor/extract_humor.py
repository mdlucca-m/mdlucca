#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de extração (estilo n8n): biblioteca-enriched.json -> humor-data.json
Segmenta variáveis psicológicas RELACIONADAS AO HUMOR (afetivas) por artigo,
com esporte/modalidade, ano, revista, autores, instrumento e nível de evidência.
Reprodutível: rode após cada atualização da biblioteca.
"""
import json, re, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(BASE, "biblioteca-enriched.json")
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "humor-data.json")

PSY_TOPICS = {'anxiety','mental-health','body-image','disordered-eating','perfectionism',
 'motivation','self-confidence','stress','stress-coping','coping','resilience','well-being',
 'flow','passion','emotion-regulation','mental-toughness','motivational-climate','maltreatment',
 'imagery','attentional-focus','self-esteem'}

# Taxonomia de VARIÁVEIS DE HUMOR (afetivas). Cada uma: rótulo, ícone, grupo, regex, instrumentos.
# grupo: "nucleo" (humor/afeto direto) | "correlato" (autoavaliativo/comportamental ligado ao humor)
MOOD = [
 dict(key="ansiedade", label="Ansiedade", icon="😰", grupo="nucleo",
      rx=r"ansiedad|anxiet|\bstai\b|\bscat\b|\bsca(?:i|s)\b|\bcsai(?:-2| ?2)?\b|state[- ]anxiety|trait[- ]anxiety|competitive anxiety|apreens",
      inst=r"\bstai\b|\bcsai(?:-2| ?2)?\b|\bscat\b|\bsas(?:-2)?\b|gad-7|state-trait"),
 dict(key="depressao", label="Depressão", icon="😔", grupo="nucleo",
      rx=r"depress|\bphq-?9\b|beck depression|\bbdi\b|\bces-?d\b|depressive symptom",
      inst=r"\bphq-?9\b|\bbdi\b|\bces-?d\b|beck"),
 dict(key="humor_poms", label="Estados de humor (POMS/BRUMS)", icon="🎭", grupo="nucleo",
      # NÃO usar "humor" solto (em PT pode ser senso de humor/coping) nem "vigor"/"confusão" (genéricos)
      rx=r"\bmood\b|\bpoms\b|profile of mood|\bbrums\b|estados de humor|mood state|mood disturbance|mood profile|pre-?competition mood|perturba(ç|c)(ão|ao) do humor",
      inst=r"\bpoms\b|\bbrums\b|profile of mood"),
 dict(key="estresse", label="Estresse (psicológico)", icon="😣", grupo="nucleo",
      rx=r"estress|\bstress\b|\bpss\b|perceived stress|psychological stress|\bdass\b|distress psicol",
      inst=r"\bpss\b|\bdass(?:-21)?\b|perceived stress scale|recovery-stress|restq"),
 dict(key="afeto", label="Afeto positivo/negativo", icon="⚖️", grupo="nucleo",
      rx=r"\bafeto\b|\baffect\b|\bpanas\b|positive affect|negative affect|afeto positivo|afeto negativo|emo(ç|c)(ões| oes|oes) positiv",
      inst=r"\bpanas\b"),
 dict(key="bem_estar", label="Bem-estar / QoL", icon="🌱", grupo="nucleo",
      rx=r"bem-estar|well-?being|quality of life|qualidade de vida|\bqol\b|flourish|satisfa(ç|c)(ão|ao) com a vida|life satisfaction|psychological well",
      inst=r"\bqol\b|sf-36|whoqol|panas|swls|satisfaction with life|warwick"),
 dict(key="reg_emocional", label="Regulação emocional", icon="🧘", grupo="nucleo",
      rx=r"regula.{0,8}emo|emotion(al)? regulation|\berq\b|reappraisal|reavalia(ç|c)|supress(ão|ao) emocional|controle emocional",
      inst=r"\berq\b|deep breathing|emotion regulation questionnaire"),
 dict(key="saude_mental", label="Saúde mental (geral/distress)", icon="🧠", grupo="nucleo",
      rx=r"sa(ú|u)de mental|mental health|mental illness|psychological distress|\bghq\b|\bk10\b|mental ill-?health|sofrimento ps(í|i)quico",
      inst=r"\bghq\b|\bk10\b|dass|phq|gad"),
 dict(key="burnout", label="Burnout", icon="🔥", grupo="nucleo",
      rx=r"burnout|esgotamento|\babq\b|athlete burnout|exaust(ão|ao) emocional",
      inst=r"\babq\b|maslach|\bmbi\b"),
 dict(key="autoestima", label="Autoestima", icon="💗", grupo="correlato",
      rx=r"autoestima|self-?esteem|\brses\b|rosenberg|autovalor|self-?worth",
      inst=r"\brses\b|rosenberg"),
 dict(key="imagem_corporal", label="Imagem corporal", icon="🪞", grupo="correlato",
      rx=r"imagem corporal|body image|body dissatisf|insatisfa(ç|c)(ão|ao) corporal|body esteem|drive for thinness|silhouet|body checking",
      inst=r"\bbss\b|\beat-?26\b|body shape questionnaire|\bbsq\b|figure rating"),
 dict(key="transtorno_alimentar", label="Transtorno alimentar", icon="🍽️", grupo="correlato",
      rx=r"transtorno alimentar|eating disorder|disordered eating|\beat-?26\b|\bede-?q?s?\b|\bedi-?3?\b|bulimi|anorex|compuls(ão|ao) alimentar|comportamento alimentar (de risco|transtornad|desordenad)|alimenta(ç|c)(ão|ao) desordenad|atitudes alimentares",
      inst=r"\beat-?26\b|\bede-?q\b|\bede-?qs\b|eating attitudes|eating disorder examination"),
 dict(key="perfeccionismo", label="Perfeccionismo", icon="🎯", grupo="correlato",
      rx=r"perfeccionismo|perfectionism|\bmps\b|\bhf-?mps\b|perfectionist",
      inst=r"\bmps\b|\bhf-?mps\b|\bfmps\b|sport-mps"),
]

def field(e,*keys):
    return " ".join(str(e.get(k,"") or "") for k in keys)

def analyzed_text(e):
    # campos que refletem o que foi MEDIDO/analisado (peso maior)
    return field(e,'variaveis_analisadas','instrumentos','variaveis_biodinamicas','subvar').lower()

def context_text(e):
    return field(e,'title','finding','resumo','sintese').lower()

def is_psy(e):
    v=e.get('variables') or []
    return ('Psico' in v) or (e.get('topic') in PSY_TOPICS)

def main():
    data=json.load(open(SRC,encoding='utf-8'))
    psy=[e for e in data if is_psy(e)]
    out=[]
    for e in psy:
        an=analyzed_text(e); ct=context_text(e); full=an+" "+ct
        vars_hit=[]
        for m in MOOD:
            in_analyzed=bool(re.search(m['rx'],an))
            in_context =bool(re.search(m['rx'],ct))
            if not (in_analyzed or in_context): continue
            inst=bool(re.search(m['inst'],full)) if m.get('inst') else False
            # nível: 'medido' se instrumento citado ou aparece em campos de análise; senão 'mencionado'
            nivel = 'medido' if (inst or in_analyzed) else 'mencionado'
            vars_hit.append(dict(key=m['key'],label=m['label'],icon=m['icon'],grupo=m['grupo'],
                                 nivel=nivel,instrumento=inst))
        if not vars_hit: continue
        mods=e.get('modalities') or []
        out.append(dict(
            doi=e.get('doi'), authors=e.get('authors'), year=e.get('year'),
            journal=e.get('journal'), title=e.get('title'),
            sport=e.get('sport'), modalities=mods, topic=e.get('topic'),
            design=e.get('design'), n=e.get('n'), citations=e.get('citations'),
            finding=e.get('finding'), fulltext=e.get('fulltext','abstract'),
            mood_vars=vars_hit,
            n_mood=len(vars_hit),
            has_nucleo=any(v['grupo']=='nucleo' for v in vars_hit),
        ))
    out.sort(key=lambda x:(-(x['year'] or 0), x['journal'] or ''))
    json.dump(out,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    # relatório
    print(f"psico={len(psy)}  com_humor={len(out)}  nucleo={sum(1 for x in out if x['has_nucleo'])}")
    from collections import Counter
    vc=Counter(); vc_med=Counter()
    for x in out:
        for v in x['mood_vars']:
            vc[v['label']]+=1
            if v['nivel']=='medido': vc_med[v['label']]+=1
    print("\nvariavel  (total / medido)")
    for lab,c in vc.most_common(): print(f"  {c:2d}/{vc_med[lab]:<2d}  {lab}")
    return out

if __name__=="__main__":
    main()
