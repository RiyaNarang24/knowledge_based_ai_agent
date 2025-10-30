# streamlit_app.py (replace your file with this exact content)
import streamlit as st
import json, os, re
from typing import List

RULES_FILE = "rules.json"

# ----------------- Utility Functions -----------------
def load_rules() -> List[dict]:
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
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
    if not text:
        return ""
    # allow only letters, commas and spaces; lower-case
    return re.sub(r"[^a-zA-Z,\s]", "", text).strip().lower()

def has_vowel(s: str) -> bool:
    return bool(re.search(r"[aeiou]", s))

def is_valid_term(term: str) -> bool:
    term = term.strip()
    # 1) minimum length
    if len(term) < 3:
        return False
    # 2) alphabetic (spaces allowed inside multi-word terms)
    if not term.replace(" ", "").isalpha():
        return False
    # 3) no long repeated characters (e.g., 'aaaa' or 'jjjj')
    if re.search(r"(.)\1{2,}", term.replace(" ", "")):  # 3 or more repeats
        return False
    # 4) require at least one vowel — helps block nonsense like "jjhk"
    if not has_vowel(term):
        return False
    return True

# ----------------- Inference Helpers -----------------
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
            p = int((matches / max(1, len(r["if"]))) * 100)
            if p >= 30:
                probs.append({"disease": r["then"], "prob": p})
    return sorted(probs, key=lambda x: x["prob"], reverse=True)

def speak(text: str):
    # small invisible html to trigger browser speech synthesis
    safe = json.dumps(text)
    st.components.v1.html(f"""
      <script>
      const t = {safe};
      if (typeof window !== "undefined" && window.speechSynthesis) {{
        try {{
          window.speechSynthesis.cancel();
          const msg = new SpeechSynthesisUtterance(t);
          window.speechSynthesis.speak(msg);
        }} catch(e){{ console.warn("speech error", e); }}
      }}
      </script>
    """, height=0)

# ----------------- Page config & CSS (remove top white bar) -----------------
st.set_page_config(page_title="Smart Health Knowledge Agent", layout="centered")

# Hide streamlit header/toolbar/footer + reduce top spacing
st.markdown("""
<style>
/* hide header, footer, menu */
header, footer, [data-testid="stToolbar"] {display: none !important;}
/* remove top extra whitespace and push content up */
.block-container {padding-top: 0rem !important;}
/* main visual container style */
.main-box {
  max-width: 880px;
  margin: 24px auto;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 6px 26px rgba(0,0,0,0.06);
  padding: 28px 28px;
}
h1 { color: #1565c0; font-weight:700; }
button { background-color: #1565c0 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- Main UI -----------------
st.markdown('<div class="main-box">', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;'>Smart Health Knowledge Agent 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#555;'>This mini AI guesses your condition from symptoms. You can teach it new rules too!</p>", unsafe_allow_html=True)

rules = load_rules()

# ---------- Rules list & delete ----------
st.markdown("### 🧩 Known Rules")
if not rules:
    st.info("No rules found yet.")
else:
    # render rules in two columns: text left, Delete button right
    for i, r in enumerate(rules):
        c1, c2 = st.columns([0.85, 0.15])
        c1.write(f"If {', '.join(r['if'])} → Then: **{r['then']}**")
        # use a unique key for each delete button
        if c2.button("❌ Delete", key=f"del_{i}"):
            # mark deletion in session_state so we can mutate list outside the iteration
            st.session_state["delete_index"] = i

# perform deletion if requested
if "delete_index" in st.session_state:
    idx = st.session_state.pop("delete_index")
    if 0 <= idx < len(rules):
        rules.pop(idx)
        save_rules(rules)
        st.success("Rule deleted.")
        st.experimental_rerun()

# ---------- Add rule ----------
st.markdown("### 💡 Add a New Rule")
with st.form("add_rule"):
    conds = st.text_input("If parts (comma separated):")
    concl = st.text_input("Then part:")
    submit_add = st.form_submit_button("Add Rule")

    if submit_add:
        conds_clean = clean_text(conds)
        concl_clean = clean_text(concl)

        # validation checks
        if not conds_clean or not concl_clean:
            st.error("Please provide both condition(s) and a conclusion.")
        else:
            conditions = [c.strip() for c in conds_clean.split(",") if c.strip()]
            # check each term with is_valid_term
            invalid = []
            for t in conditions + [concl_clean]:
                if not is_valid_term(t):
                    invalid.append(t)
            if invalid:
                # show friendly message (don't add)
                st.error("Invalid terms detected. Each term must be alphabetic, at least 3 letters, include a vowel, and not be repetitive. Invalid: " + ", ".join(invalid))
            else:
                rules.append({"if": conditions, "then": concl_clean})
                save_rules(rules)
                st.success("✅ Rule added successfully.")
                st.experimental_rerun()

# ---------- Inference ----------
st.markdown("### 🧠 Ask the AI")
with st.form("infer_form"):
    facts_input = st.text_input("Enter symptoms (comma separated):")
    infer_submit = st.form_submit_button("Infer")

if infer_submit:
    facts_clean = clean_text(facts_input)
    facts = [f.strip() for f in facts_clean.split(",") if f.strip()]
    if not facts:
        st.error("Please enter at least one symptom.")
    else:
        conclusions = forward_chain(rules, facts)
        probs = get_probabilities(rules, facts)

        if conclusions:
            st.success(f"Possible Condition(s): {', '.join(conclusions)}")
            speak("You may have " + ", ".join(conclusions))
        elif probs:
            st.warning("No exact match found. Possible conditions:")
            for p in probs:
                st.markdown(f"- **{p['disease']}** — {p['prob']}%")
            speak("No exact match found. Possible conditions are: " + ", ".join([f"{p['disease']} with {p['prob']} percent" for p in probs]))
        else:
            st.info("No condition found. Try different symptoms.")
            speak("No condition found. Try different symptoms.")

# optional link to your other app (keeps your choice)
st.markdown("""<p style='text-align:center;margin-top:18px;'>
<a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
<button style="padding:10px 18px; border-radius:8px;">Go to Pneumonia Detection App</button></a>
</p>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
