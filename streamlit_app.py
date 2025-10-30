# streamlit_app.py
import streamlit as st
import json
import os
import re
import subprocess
import html
from typing import List

RULES_FILE = "rules.json"


def load_rules() -> List[dict]:
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    # default rules
    return [
        {"if": ["sneezing", "cough", "cold"], "then": "flu"},
        {"if": ["fever", "body pain"], "then": "viral infection"},
        {"if": ["headache", "nausea"], "then": "migraine"},
        {"if": ["rash", "itching"], "then": "allergy"},
        {"if": ["tiredness", "weakness"], "then": "fatigue"},
    ]


def save_rules(rules: List[dict]):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=4)


def clean_text(text: str) -> str:
    if text is None:
        return ""
    # Allow letters, commas and spaces; remove other characters
    return re.sub(r"[^a-zA-Z\s,]", "", text).strip()


def is_valid_input_term(term: str) -> bool:
    """
    Validate a single term:
    - purely alphabetic (after removing spaces)
    - length >= 3
    - not containing 4 or more identical consecutive letters
    """
    if not term:
        return False
    cleaned = term.replace(" ", "")
    if not cleaned.isalpha():
        return False
    if len(cleaned) < 3:
        return False
    if re.search(r"([a-zA-Z])\1{3,}", cleaned):
        return False
    return True


def forward_chain_infer(rules: List[dict], facts: List[str]):
    facts = facts[:]
    conclusions = set()
    inferred = True
    while inferred:
        inferred = False
        for r in rules:
            if all(cond in facts for cond in r["if"]) and (r["then"] not in facts):
                facts.append(r["then"])
                conclusions.add(r["then"])
                inferred = True
    return list(conclusions), facts


def compute_probabilities(rules: List[dict], facts: List[str], min_pct=30):
    probs = []
    for r in rules:
        match_count = sum(1 for cond in r["if"] if cond in facts)
        if match_count > 0:
            pct = int((match_count / len(r["if"])) * 100)
            if pct >= min_pct:
                probs.append({"disease": r["then"], "prob": pct})
    # sort descending by prob
    probs.sort(key=lambda x: x["prob"], reverse=True)
    return probs


def speak_text(text: str):
    # escape text for embedding in HTML/JS
    safe = html.escape(text)
    html_snippet = f"""
    <script>
    // Speak text
    const msg = new SpeechSynthesisUtterance({json.dumps(text)});
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(msg);
    </script>
    """
    st.components.v1.html(html_snippet, height=0)


st.set_page_config(page_title="Smart Health Knowledge Agent", layout="centered")

st.title("Smart Health Knowledge Agent 🤖")
st.markdown("This mini AI guesses your condition from symptoms. You can teach it new rules too.")

rules = load_rules()

# top row: known rules + delete button
st.subheader("🧩 Known Rules")
if not rules:
    st.info("No rules found. Add some using the form below.")
else:
    for i, r in enumerate(rules):
        rule_text = f"If {', '.join(r['if'])} → Then: {r['then']}"
        cols = st.columns([0.85, 0.15])
        cols[0].markdown(f"**{rule_text}**")
        if cols[1].button(f"Delete {i}", key=f"del_{i}"):
            # remove rule and save
            del rules[i]
            save_rules(rules)
            st.experimental_rerun()

st.markdown("---")

# Add rule section
st.subheader("💡 Add a New Rule")
with st.form("add_rule_form", clear_on_submit=False):
    conditions_input = st.text_input("If parts (comma separated)", placeholder="e.g. cough, fever")
    conclusion_input = st.text_input("Then part", placeholder="e.g. viral infection")
    add_sub = st.form_submit_button("Add Rule")

if add_sub:
    conds_raw = clean_text(conditions_input.lower())
    conclusion = clean_text(conclusion_input.lower())
    conditions = [c.strip() for c in conds_raw.split(",") if c.strip()]

    # validation
    if not conditions:
        st.error("You must provide at least one condition (comma-separated).")
    elif not conclusion:
        st.error("You must provide a conclusion (e.g. 'flu').")
    else:
        # verify all terms are valid
        bad_terms = []
        for t in conditions + [conclusion]:
            if not is_valid_input_term(t):
                bad_terms.append(t)
        if bad_terms:
            st.error(
                "Some terms look invalid and were not accepted: "
                + ", ".join(bad_terms)
                + ".\nTerms must be alphabetic, >= 3 letters, and not repeated characters."
            )
        else:
            # add rule
            rules.append({"if": conditions, "then": conclusion})
            save_rules(rules)
            st.success("✅ Rule added successfully!")
            st.experimental_rerun()

st.markdown("---")

# Inference section
st.subheader("🧠 Ask the AI")
with st.form("infer_form", clear_on_submit=False):
    facts_input = st.text_input("Enter observed symptoms (comma separated)", placeholder="e.g. cough, sneezing")
    infer_sub = st.form_submit_button("Infer")

if infer_sub:
    facts_raw = clean_text(facts_input.lower())
    facts = [f.strip() for f in facts_raw.split(",") if f.strip()]

    if not facts:
        st.error("Please enter at least one symptom to infer.")
    else:
        # run forward chaining
        conclusions, final_facts = forward_chain_infer(rules, facts)
        probabilities = compute_probabilities(rules, final_facts, min_pct=30)

        if conclusions:
            st.success("Possible Condition(s): " + ", ".join(conclusions))
            # speak
            speak_text("You may have " + ", ".join(conclusions))
        elif probabilities:
            st.warning("No exact match found. Here are likely conditions:")
            for p in probabilities:
                st.markdown(f"- **{p['disease']}** — {p['prob']}%")
            # create speech description
            speech_text = "No exact match found. Possible conditions are: " + ", ".join(
                [f"{p['disease']} with {p['prob']} percent probability" for p in probabilities]
            )
            speak_text(speech_text)
        else:
            st.info("No exact conclusions. Try more symptoms or different words.")
            speak_text("No condition found. Try different symptoms.")

st.markdown("---")

# small helper: link to pneumonia detection app (optional)
st.markdown(
    """
    <div style="margin-top:6px;">
      <a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
        <button style="padding:10px 20px; background-color:#4CAF50; color:white; border:none; border-radius:6px;">
          Go to Pneumonia Detection App
        </button>
      </a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("🩺 Student Project — Simple AI Health Assistant")
