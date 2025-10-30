import streamlit as st
import json, os, re

RULES_FILE = "rules.json"

# --- Helper functions ---
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return [
        {"if": ["sneezing", "cough", "cold"], "then": "flu"},
        {"if": ["fever", "body pain"], "then": "viral infection"},
        {"if": ["headache", "nausea"], "then": "migraine"},
        {"if": ["rash", "itching"], "then": "allergy"},
        {"if": ["tiredness", "weakness"], "then": "fatigue"},
    ]

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=4)

def clean_text(text):
    return re.sub(r'[^a-zA-Z\s,]', '', text).strip()

def is_valid_input_term(term):
    cleaned_term_alpha = term.replace(" ", "")
    if not cleaned_term_alpha.isalpha():
        return False
    if len(cleaned_term_alpha) < 3:
        return False
    if re.search(r'([a-z])\1{3,}', cleaned_term_alpha):
        return False
    return True

# --- Streamlit App ---
st.title("🧩 Rule-Based Disease Expert System")

# Load existing rules
rules = load_rules()

# --- Section 1: Add Rule ---
st.subheader("➕ Add a New Rule")

conditions_input = st.text_input("Enter conditions (comma-separated):")
conclusion = st.text_input("Enter conclusion:")

if st.button("Add Rule"):
    conditions = [c.strip() for c in clean_text(conditions_input.lower()).split(",") if c.strip()]
    conc = clean_text(conclusion.lower())

    if not is_valid_input_term(conc):
        st.warning("⚠️ Invalid conclusion entered!")
    elif not conditions:
        st.warning("⚠️ Enter at least one valid condition.")
    elif not all(is_valid_input_term(c) for c in conditions):
        st.warning("⚠️ Some conditions are invalid.")
    else:
        rules.append({"if": conditions, "then": conc})
        save_rules(rules)
        st.success("✅ Rule added successfully!")

# --- Section 2: View & Delete Rules ---
st.subheader("📜 Existing Rules")
for i, rule in enumerate(rules):
    st.write(f"**Rule {i+1}:** IF {', '.join(rule['if'])} → THEN {rule['then']}")
    if st.button(f"Delete Rule {i+1}", key=i):
        del rules[i]
        save_rules(rules)
        st.success(f"Rule {i+1} deleted!")
        st.experimental_rerun()

# --- Section 3: Inference ---
st.subheader("🤖 Run Inference")
facts_input = st.text_input("Enter observed symptoms (comma-separated):")
if st.button("Infer Disease"):
    facts = [f.strip() for f in clean_text(facts_input.lower()).split(",") if f.strip()]
    conclusions = set()
    inferred = True

    while inferred:
        inferred = False
        for r in rules:
            if all(cond in facts for cond in r["if"]) and r["then"] not in facts:
                facts.append(r["then"])
                conclusions.add(r["then"])
                inferred = True

    if conclusions:
        st.success(f"✅ Inferred Diseases: {', '.join(conclusions)}")
    else:
        st.info("No direct match found. Showing probable diseases:")
        probs = []
        for r in rules:
            match_count = sum(cond in facts for cond in r["if"])
            if match_count > 0:
                prob = int((match_count / len(r["if"])) * 100)
                if prob >= 30:
                    probs.append((r["then"], prob))
        if probs:
            for d, p in probs:
                st.write(f"- {d}: {p}% probability")
        else:
            st.write("No probable diseases found.")
