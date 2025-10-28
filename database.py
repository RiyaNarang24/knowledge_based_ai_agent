
import sqlite3
import json
import os

SCHEMA = """
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conditions TEXT NOT NULL, -- stored as JSON array
    conclusion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL UNIQUE
);
"""

DEFAULT_RULES = [
    (["Fever", "Cough", "Fatigue"], "Flu"),
    (["Fever", "Headache", "Nausea"], "Dengue"),
    (["Cough", "Shortness Of Breath"], "Asthma"),
    (["Sneezing", "Runny Nose", "Itchy Eyes"], "Allergy"),
    (["Fever", "Sore Throat"], "Throat Infection"),
]


def get_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    # Create DB and tables if they don't exist
    first_time = not os.path.exists(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    for stmt in SCHEMA.strip().split(";"):
        if stmt.strip():
            cur.execute(stmt)
    conn.commit()
    if first_time:
        # insert defaults
        for conds, conclusion in DEFAULT_RULES:
            insert_rule(conn, conds, conclusion)
        # insert known facts from default rules
        facts = set()
        for conds, _ in DEFAULT_RULES:
            facts.update([c.title() for c in conds])
        for f in sorted(facts):
            insert_fact(conn, f)
    conn.close()


def insert_rule(conn, conditions, conclusion):
    # conditions: list -> stored as JSON
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rules (conditions, conclusion) VALUES (?, ?)",
        (json.dumps([c.title() for c in conditions]), conclusion.title())
    )
    conn.commit()


def insert_fact(conn, fact):
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO facts (fact) VALUES (?)", (fact.title(),))
        conn.commit()
    except sqlite3.IntegrityError:
        # already exists
        pass


# helper wrappers for outside modules
def add_rule_db(db_path, conditions, conclusion):
    conn = get_connection(db_path)
    insert_rule(conn, conditions, conclusion)
    conn.close()


def add_fact_db(db_path, fact):
    conn = get_connection(db_path)
    insert_fact(conn, fact)
    conn.close()


def get_all_rules_db(db_path):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, conditions, conclusion FROM rules ORDER BY id")
    rows = cur.fetchall()
    rules = []
    for r in rows:
        try:
            conds = json.loads(r["conditions"])
        except Exception:
            # fallback: parse comma separated
            conds = [c.strip().title() for c in r["conditions"].split(",") if c.strip()]
        rules.append({"id": r["id"], "if": conds, "then": r["conclusion"].title()})
    conn.close()
    return rules


def get_all_facts_db(db_path):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT fact FROM facts ORDER BY fact")
    rows = cur.fetchall()
    facts = [r["fact"] for r in rows]
    conn.close()
    return facts
