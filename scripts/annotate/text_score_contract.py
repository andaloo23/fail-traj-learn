"""Explicit identity guarantee, separate from a learned model's raw similarity."""
import math

DIMENSIONS = ('operation','participant_roles','object_identity','destination',
              'physical_result','task_match','environmental_effect','event_order','uncertainty')


def dimension_agreement(item):
    """Explicit equal-weight dimension agreement; material conflict remains a flag."""
    dimensions=item['dimensions']
    if set(dimensions)!=set(DIMENSIONS): raise ValueError('Missing/unexpected dimensions')
    allowed={'equivalent','compatible_difference','contradiction','unresolved','not_applicable'}
    for value in dimensions.values():
        if set(value)!={'a','b','relation'} or value['relation'] not in allowed:
            raise ValueError('Invalid dimension fields/relation')
        if any(value[k] is not None and (not isinstance(value[k],str) or not value[k].strip()) for k in ('a','b')):
            raise ValueError('Invalid dimension assertion')
        if value['relation']=='not_applicable' and (value['a'] is not None or value['b'] is not None):
            raise ValueError('Not applicable must have no assertions')
        if value['relation']!='not_applicable' and value['a'] is None and value['b'] is None:
            raise ValueError('Applicable dimension must have assertions')
        if value['relation'] in ('equivalent','contradiction','unresolved') and (value['a'] is None or value['b'] is None):
            raise ValueError('Correspondence requires two assertions')
    relations=[v['relation'] for v in dimensions.values() if v['relation']!='not_applicable']
    if not relations:raise ValueError('No applicable assertions')
    conflicts=relations.count('contradiction');unresolved=relations.count('unresolved')
    matched=relations.count('equivalent');score=matched/len(relations)
    relation=('contradiction' if conflicts else 'equivalent' if score==1 else 'unresolved' if unresolved else 'compatible_difference')
    return dict(score=score,relation=relation,equivalent_dimensions=matched,applicable_dimensions=len(relations),
                contradictions=conflicts,unresolved_dimensions=unresolved)


def anchored_similarity(left, right, raw):
    if not math.isfinite(float(raw)):
        raise ValueError('Non-finite text score')
    return 1.0 if left == right else min(1.0, max(0.0, float(raw)))


def fact_agreement(item):
    """One-to-one semantic fact Dice. Contradictions remain separately visible."""
    sides = []
    for key in ('facts_a', 'facts_b'):
        facts = item[key]
        ids = [f['id'] for f in facts]
        if not facts or len(set(ids)) != len(ids) or any(not f.get('claim') for f in facts):
            raise ValueError('Facts must be nonempty with unique IDs and claims')
        sides.append(set(ids))
    used_a, used_b, equivalent, contradictions, unresolved = set(), set(), 0, 0, 0
    for match in item['alignments']:
        a, b, relation = match['a_id'], match['b_id'], match['relation']
        if a not in sides[0] or b not in sides[1] or a in used_a or b in used_b:
            raise ValueError('Fact alignments must be valid and one-to-one')
        if relation not in ('equivalent', 'contradiction', 'compatible_difference', 'unresolved'):
            raise ValueError('Invalid fact relation')
        used_a.add(a); used_b.add(b)
        equivalent += relation == 'equivalent'
        contradictions += relation == 'contradiction'
        unresolved += relation == 'unresolved'
    count = len(sides[0]) + len(sides[1])
    score = 2*equivalent/count
    relation = ('contradiction' if contradictions else 'equivalent' if score == 1 else
                'unresolved' if unresolved else 'unrelated' if not item['alignments'] else 'compatible_difference')
    return dict(score=score, relation=relation, equivalent_facts=equivalent,
                left_facts=len(sides[0]), right_facts=len(sides[1]),
                contradictions=contradictions, unresolved_alignments=unresolved)
