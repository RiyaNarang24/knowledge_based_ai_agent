# inference_engine.py

def infer_with_explanation(kb, facts):
    """
    kb: list of rules, each rule is {'id':.., 'if': [c1,c2..], 'then': 'X'}
    facts: list of observed facts (title-cased strings)

    Return:
      {
        "conclusions": [list of conclusions],
        "partial": {conclusion: percent, ...},
        "explanation": [text steps]
      }
    """
    facts_set = set([f.title() for f in facts])
    conclusions = []
    explanation = []
    partial = {}

    for rule in kb:
        conditions = [c.title() for c in rule.get("if", [])]
        conclusion = rule.get("then", "").title()
        if not conditions or not conclusion:
            continue
        matched = [c for c in conditions if c in facts_set]
        if len(matched) == len(conditions):
            conclusions.append(conclusion)
            explanation.append(f"Rule R{rule.get('id')}: If {', '.join(conditions)} → {conclusion} fired (all conditions matched).")
        elif matched:
            percent = round((len(matched) / len(conditions)) * 100, 2)
            # store best percent if multiple rules produce same conclusion
            if conclusion not in partial or percent > partial[conclusion]:
                partial[conclusion] = percent

    # deduplicate conclusions while keeping order
    seen = set()
    final_cons = []
    for c in conclusions:
        if c not in seen:
            final_cons.append(c)
            seen.add(c)

    # sort partial by percent descending
    partial_sorted = dict(sorted(partial.items(), key=lambda x: -x[1]))

    return {"conclusions": final_cons, "partial": partial_sorted, "explanation": explanation}
