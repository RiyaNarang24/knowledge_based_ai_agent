import streamlit as st
import json, os, re, html
from typing import List

RULES_FILE = "rules.json"

# ---------- Data Utilities ----------
def load_rules() -> List[dict]:
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except:
            return []
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

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r"[^a-zA-Z,\s]", "", text).strip().lower()

def is_valid_term(term: str) -> bool:
    term = term.strip()
    return (
        len(term) >= 3
        and term.replace(" ", "").isalpha()
        and not re.search(r"(.)\1{2,}", term)
    )

# ---------- Inference Logic ----------
def forward_chain(rules, facts):
    facts = facts[:]
    conclusions = set()
    changed = True
    while changed:
        changed = False
        for r in rules:
            if all(cond in facts for cond in r["if"]) and r["then"] not in facts:
                facts.append(r["then"])
                conclusions.add(r["then"])
                changed = True
    return list(conclusions)

def get_probabilities(rules, facts):
    probs = []
    for r in rules:
        matches = sum(1 for c in r["if"] if c in facts)
        if matches > 0:
            p = int((matches / len(r["if"])) * 100)
            if p >= 30:
                probs.append({"disease": r["then"], "prob": p})
    return sorted(probs, key=lambda x: x["prob"], reverse=True)

def speak(text):
    safe = html.escape(text)
    st.components.v1.html(f"""
        <script>
        const msg = new SpeechSynthesisUtterance({json.dumps(text)});
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(msg);
        </script>
    """, height=0)

# ---------- Page Layout ----------
st.set_page_config(page_title="Smart Health Knowledge Agent", layout="centered")

# Background & container styling
page_bg = """
<style>
body {
  font-family: 'Segoe UI', Tahoma, sans-serif;
  background: linear-gradient(to right, #e3f2fd, #ffffff);
}
div[data-testid="stAppViewContainer"] > section:first-child {
  background: none;
}
.main-container {
  max-width: 800px;
  margin: 40px auto;
  background: white;
  border-radius: 16px;
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
  padding: 30px 40px;
}
button {
  background-color: #1565c0 !important;
  color: white !important;
  border: none !important;
  border-radius: 6px !important;
}
button:hover {
  background-color: #0d47a1 !important;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center; color:#1565c0;'>Smart Health Knowledge Agent 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#555;'>This mini AI guesses your condition from symptoms. You can teach it new rules too!</p>", unsafe_allow_html=True)

    rules = load_rules()

    # ---------- Show Rules ----------
    st.markdown("### 🧩 Known Rules")
    if not rules:
        st.info("No rules found yet.")
    else:
        for i, r in enumerate(rules):
            col1, col2 = st.columns([0.85, 0.15])
            col1.write(f"If {', '.join(r['if'])} → Then: **{r['then']}**")
            if col2.button("❌ Delete", key=f"del_{i}"):
                del rules[i]
                save_rules(rules)
                st.experimental_rerun()

    # ---------- Add Rule ----------
    st.markdown("### 💡 Add a New Rule")
    with st.form("add_rule_form"):
        conds = st.text_input("If parts (comma separated):")
        concl = st.text_input("Then part:")
        submitted = st.form_submit_button("Add Rule")

        if submitted:
            conds_clean = clean_text(conds)
            concl_clean = clean_text(concl)
            if not conds_clean or not concl_clean:
                st.error("Please fill both conditions and conclusion.")
            else:
                conditions = [c.strip() for c in conds_clean.split(",") if c.strip()]
                all_terms = conditions + [concl_clean]
                if all(is_valid_term(t) for t in all_terms):
                    rules.append({"if": conditions, "then": concl_clean})
                    save_rules(rules)
                    st.success("✅ Rule added successfully!")
                    st.experimental_rerun()
                else:
                    st.error("❌ Invalid rule. Use meaningful alphabetic words (≥3 letters, no repeats).")

    # ---------- Inference ----------
    st.markdown("### 🧠 Ask the AI")
    with st.form("infer_form"):
        facts_input = st.text_input("Enter symptoms (comma separated):")
        infer = st.form_submit_button("Infer")

    if infer:
        facts = [f.strip() for f in clean_text(facts_input).split(",") if f.strip()]
        if not facts:
            st.error("Please enter at least one symptom.")
        else:
            conclusions = forward_chain(rules, facts)
            probs = get_probabilities(rules, facts)

            if conclusions:
                msg = f"You may have {', '.join(conclusions)}"
                st.success(f"Possible Condition(s): {', '.join(conclusions)}")
                speak(msg)
            elif probs:
                st.warning("No exact match found. Here are possible conditions:")
                for p in probs:
                    st.markdown(f"- **{p['disease']}** — {p['prob']}%")
                msg = "No exact match found. Possible conditions are: " + ", ".join(
                    [f"{p['disease']} with {p['prob']} percent probability" for p in probs]
                )
                speak(msg)
            else:
                st.info("No condition found. Try different symptoms.")
                speak("No condition found. Try different symptoms.")

    # ---------- Button to Pneumonia App ----------
    st.markdown("""
    <a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
      <button style="padding:10px 20px; background-color:#4CAF50; color:white; border:none; border-radius:6px;">
        Go to Pneumonia Detection App
      </button>
    </a>
    """, unsafe_allow_html=True)

    st.markdown("<footer style='text-align:center; color:gray; margin-top:20px;'>🩺 Student Project — Simple AI Health Assistant</footer>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
