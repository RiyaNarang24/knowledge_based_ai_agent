import streamlit as st
import json, os, re

RULES_FILE = "rules.json"

# ---------- Helper Functions ----------

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    # Default starter rules
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
    return re.sub(r'[^a-zA-Z,\s]', '', text).strip().lower()

def is_valid_input_term(term):
    term = term.strip().replace(" ", "")
    if not term.isalpha():
        return False
    if len(term) < 3:
        return False
    if re.search(r'([a-z])\1{3,}', term):
        return False
    return True

def infer_facts(facts, rules):
    conclusions = set()
    inferred = True
    while inferred:
        inferred = False
        for r in rules:
            if all(cond in facts for cond in r["if"]) and r["then"] not in facts:
                facts.append(r["then"])
                conclusions.add(r["then"])
                inferred = True

    probabilities = []
    if not conclusions:
        for r in rules:
            match_count = sum(cond in facts for cond in r["if"])
            if match_count > 0:
                prob = int((match_count / len(r["if"])) * 100)
                if prob >= 30:
                    probabilities.append({"disease": r["then"], "prob": prob})
    return list(conclusions), probabilities


# ---------- Streamlit App ----------

st.set_page_config(page_title="Smart Health Knowledge Agent", page_icon="🤖")

st.markdown(
    "<h1 style='text-align:center;color:#1565c0;'>Smart Health Knowledge Agent 🤖</h1>",
    unsafe_allow_html=True
)
st.markdown("<p style='text-align:center;color:#555;'>This mini AI guesses your condition from symptoms. You can teach it new rules too!</p>", unsafe_allow_html=True)

rules = load_rules()

# --- Display Rules ---
st.subheader("🧩 Known Rules")
for i, r in enumerate(rules):
    col1, col2 = st.columns([5,1])
    with col1:
        st.write(f"**If:** {', '.join(r['if'])} → **Then:** {r['then']}")
    with col2:
        if st.button("❌ Delete", key=f"del{i}"):
            del rules[i]
            save_rules(rules)
            st.success("Rule deleted successfully!")
            st.experimental_rerun()

# --- Add Rule Section ---
st.subheader("💡 Add a New Rule")
with st.form("add_rule_form"):
    conditions_input = st.text_input("If parts (comma separated):")
    conclusion = st.text_input("Then part:")
    submitted = st.form_submit_button("Add Rule")

    if submitted:
        conditions_input = clean_text(conditions_input)
        conclusion = clean_text(conclusion)
        conditions = [c.strip() for c in conditions_input.split(",") if c.strip()]

        # stricter validation
        if not conditions or not is_valid_input_term(conclusion):
            st.error("❌ Invalid input! Use only meaningful letters (min 3 characters).")
        elif any(not is_valid_input_term(c) for c in conditions):
            st.error("❌ One or more conditions are invalid. Please recheck.")
        else:
            rules.append({"if": conditions, "then": conclusion})
            save_rules(rules)
            st.success("✅ Rule added successfully!")
            st.experimental_rerun()

# --- Inference Section ---
st.subheader("🧠 Ask the AI")
facts_input = st.text_input("Enter symptoms (comma separated):")
if st.button("Infer"):
    facts = [f.strip() for f in clean_text(facts_input).split(",") if f.strip()]
    if not facts:
        st.warning("Please enter some symptoms.")
    else:
        conclusions, probabilities = infer_facts(facts, rules)
        if conclusions:
            text = f"Possible condition(s): {', '.join(conclusions)}"
            st.success(text)
            st.markdown(f"<script>speechSynthesis.speak(new SpeechSynthesisUtterance('{text}'));</script>", unsafe_allow_html=True)
        elif probabilities:
            st.info("No exact match found. Here are possible conditions based on similarity:")
            for p in probabilities:
                st.write(f"- {p['disease']} — {p['prob']}%")
           speech_text = "No exact match found. Possible conditions are: " + ", ".join(
    [f"{p['disease']} with {p['prob']} percent probability" for p in probabilities]
)

            st.markdown(f"<script>speechSynthesis.speak(new SpeechSynthesisUtterance('{speech_text}'));</script>", unsafe_allow_html=True)
        else:
            st.error("No condition found. Try different symptoms.")
            st.markdown("<script>speechSynthesis.speak(new SpeechSynthesisUtterance('No condition found. Try different symptoms.'));</script>", unsafe_allow_html=True)

# --- Footer ---
st.markdown("<hr><p style='text-align:center;color:gray;'>🩺 Student Project — Simple AI Health Assistant</p>", unsafe_allow_html=True)

# --- Link to Other App ---
st.markdown(
    """<div style="text-align:center;margin-top:20px;">
        <a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
        <button style="padding:10px 20px; background-color:#4CAF50; color:white; border:none; border-radius:6px;">Go to Pneumonia Detection App</button>
        </a>
    </div>""",
    unsafe_allow_html=True
)
