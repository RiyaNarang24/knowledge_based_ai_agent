from flask import Flask, render_template, request, redirect, url_for
import json, os, re

app = Flask(__name__)

RULES_FILE = "rules.json"


# --- Helper functions ---
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return [{
        "if": ["sneezing", "cough", "cold"],
        "then": "flu"
    }, {
        "if": ["fever", "body pain"],
        "then": "viral infection"
    }, {
        "if": ["headache", "nausea"],
        "then": "migraine"
    }, {
        "if": ["rash", "itching"],
        "then": "allergy"
    }, {
        "if": ["tiredness", "weakness"],
        "then": "fatigue"
    }]


def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=4)


def clean_text(text):
    """Allow only letters and spaces"""
    return re.sub(r'[^a-zA-Z\s,]', '', text).strip()


def is_valid_input_term(term):
    """
    Stricter validation to reject 'rubbish' like 'dd' or 'nnn'.
    Requires a minimum length and rejects patterns with too many repeating characters.
    """
    cleaned_term_alpha = term.replace(" ", "")

    # 1. Must be purely alphabetic
    if not cleaned_term_alpha.isalpha():
        return False

    # 2. Must meet a higher minimum length (e.g., 3 characters)
    if len(cleaned_term_alpha) < 3:
        return False

    # 3. Reject terms with 4 or more identical consecutive letters (e.g., 'dddd', 'aaaa')
    if re.search(r'([a-z])\1{3,}', cleaned_term_alpha):
        return False

    return True


# --- Routes ---
@app.route("/")
def home():
    rules = load_rules()
    return render_template("index.html", rules=rules, results=None)


@app.route("/add_rule", methods=["POST"])
def add_rule():
    conditions_input = clean_text(request.form.get("conditions", "").lower())
    conclusion = clean_text(request.form.get("conclusion", "").lower())

    # Split by commas and clean
    conditions = [c.strip() for c in conditions_input.split(",") if c.strip()]

    # --- STICKTER VALIDATION LOGIC USING is_valid_input_term ---

    # 1. Validate Conclusion
    if not is_valid_input_term(conclusion):
        return redirect(url_for("home"))

    # 2. Validate Conditions: ensure there is at least one condition
    if not conditions:
        return redirect(url_for("home"))

    # 3. Validate each individual condition
    for cond in conditions:
        if not is_valid_input_term(cond):
            return redirect(url_for("home"))

    # --- END STICKTER VALIDATION LOGIC ---

    # If all checks pass, save the new rule
    rules = load_rules()
    rules.append({"if": conditions, "then": conclusion})
    save_rules(rules)

    return redirect(url_for("home"))


@app.route("/delete_rule/<int:index>", methods=["POST"])
def delete_rule(index):
    rules = load_rules()
    if 0 <= index < len(rules):
        del rules[index]
        save_rules(rules)
    return redirect(url_for("home"))


@app.route("/infer", methods=["POST"])
def infer():
    facts_input = clean_text(request.form.get("facts", "").lower())
    facts = [f.strip() for f in facts_input.split(",") if f.strip()]
    rules = load_rules()

    conclusions = set()
    inferred = True

    # Forward chaining
    while inferred:
        inferred = False
        for r in rules:
            if all(cond in facts
                   for cond in r["if"]) and r["then"] not in facts:
                facts.append(r["then"])
                conclusions.add(r["then"])
                inferred = True

    # Probability if no match
    probabilities = []
    if not conclusions:
        for r in rules:
            match_count = sum(cond in facts for cond in r["if"])
            if match_count > 0:
                prob = int((match_count / len(r["if"])) * 100)
                if prob >= 30:  # Only show probabilities 30% or higher
                    probabilities.append({"disease": r["then"], "prob": prob})

    return render_template("index.html",
                           rules=rules,
                           results={
                               "conclusions": list(conclusions),
                               "probabilities": probabilities
                           })


if __name__ == "__main__":
    app.run(debug=True)
