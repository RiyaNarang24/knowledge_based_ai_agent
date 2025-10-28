from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Create database if not exists
DB_FILE = 'knowledge_base.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conditions TEXT,
                        conclusion TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fact TEXT)''')
init_db()

# Allowed domain words (only meaningful knowledge terms)
ALLOWED_WORDS = {
    "rain", "cloudy", "sunny", "windy", "storm", "wet", "dry",
    "cold", "hot", "humid", "snow", "clear", "fog", "mist"
}

@app.route('/')
def index():
    with sqlite3.connect(DB_FILE) as conn:
        rules = conn.execute("SELECT * FROM rules").fetchall()
        facts = conn.execute("SELECT fact FROM facts").fetchall()
    rules_list = [{"id": r[0], "if": r[1].split(','), "then": r[2]} for r in rules]
    facts_list = [f[0] for f in facts]
    return render_template('index.html', rules=rules_list, known_facts=facts_list)

@app.route('/add_rule', methods=['POST'])
def add_rule():
    conditions = request.form['conditions'].strip().lower()
    conclusion = request.form['conclusion'].strip().lower()

    # Simple validations
    if not conditions or not conclusion:
        message = "⚠️ Both condition and conclusion are required!"
    elif any(char.isdigit() for char in conditions + conclusion):
        message = "⚠️ Rule should not contain numbers!"
    elif len(conditions) < 3 or len(conclusion) < 3:
        message = "⚠️ Please enter meaningful words!"
    else:
        # Split multiple conditions by comma
        cond_list = [c.strip() for c in conditions.split(',') if c.strip()]

        # Check if all words are in allowed domain
        for cond in cond_list + [conclusion]:
            if cond not in ALLOWED_WORDS:
                message = f"⚠️ '{cond}' is not recognized. Use valid weather terms!"
                break
        else:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO rules (conditions, conclusion) VALUES (?, ?)", (conditions, conclusion))
            message = "✅ Rule added successfully!"

    with sqlite3.connect(DB_FILE) as conn:
        rules = conn.execute("SELECT * FROM rules").fetchall()
        facts = conn.execute("SELECT fact FROM facts").fetchall()
    rules_list = [{"id": r[0], "if": r[1].split(','), "then": r[2]} for r in rules]
    facts_list = [f[0] for f in facts]

    return render_template('index.html', rules=rules_list, known_facts=facts_list, message=message)

@app.route('/add_fact', methods=['POST'])
def add_fact():
    fact = request.form['fact'].strip().lower()
    if not fact:
        message = "⚠️ Please enter a fact!"
    elif fact not in ALLOWED_WORDS:
        message = f"⚠️ '{fact}' is not recognized. Use valid weather terms!"
    else:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO facts (fact) VALUES (?)", (fact,))
        message = "✅ Fact added successfully!"

    with sqlite3.connect(DB_FILE) as conn:
        rules = conn.execute("SELECT * FROM rules").fetchall()
        facts = conn.execute("SELECT fact FROM facts").fetchall()
    rules_list = [{"id": r[0], "if": r[1].split(','), "then": r[2]} for r in rules]
    facts_list = [f[0] for f in facts]

    return render_template('index.html', rules=rules_list, known_facts=facts_list, message=message)

@app.route('/infer', methods=['POST'])
def infer():
    facts_input = request.form['facts'].strip().lower().split(',')
    facts_input = [f.strip() for f in facts_input if f.strip()]
    conclusions = []
    explanations = []

    with sqlite3.connect(DB_FILE) as conn:
        rules = conn.execute("SELECT conditions, conclusion FROM rules").fetchall()

    for conds, conclusion in rules:
        cond_list = [c.strip() for c in conds.split(',')]
        if all(c in facts_input for c in cond_list):
            conclusions.append(conclusion)
            explanations.append(f"If {', '.join(cond_list)} → then {conclusion}")

    results = {
        "conclusions": conclusions,
        "explanation": explanations
    }

    with sqlite3.connect(DB_FILE) as conn:
        rules_all = conn.execute("SELECT * FROM rules").fetchall()
        facts_all = conn.execute("SELECT fact FROM facts").fetchall()
    rules_list = [{"id": r[0], "if": r[1].split(','), "then": r[2]} for r in rules_all]
    facts_list = [f[0] for f in facts_all]

    return render_template('index.html', rules=rules_list, known_facts=facts_list, results=results)

if __name__ == '__main__':
    app.run(debug=True)
