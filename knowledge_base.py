# knowledge_base.py
from database import add_rule_db, add_fact_db, get_all_rules_db, get_all_facts_db

def add_rule_db_wrapper(db_path, conditions, conclusion):
    """
    Adds a rule to DB and also ensures its conditions exist as facts if not present.
    """
    add_rule_db(db_path, conditions, conclusion)
    # optional: add conditions to facts table so they're known facts
    for c in conditions:
        add_fact_db(db_path, c)


# For convenience import functions to be used by app.py
add_rule_db = add_rule_db_wrapper
add_fact_db = add_fact_db
get_all_rules_db = get_all_rules_db
get_all_facts_db = get_all_facts_db
