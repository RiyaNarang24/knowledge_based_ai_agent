# streamlit_app.py
import streamlit as st
import json, os, re
from typing import List

RULES_FILE = "rules.json"

# ---------- Helpers ----------
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
    # allow letters, commas and spaces; lowercase everything
    return re.sub(r"[^a-zA-Z,\s]", "", text).strip().lower()

def has_vowel(s: str) -> bool:
    return bool(re.search(r"[aeiou]", s))

def is_valid_term(term: str) -> bool:
    t = term.strip()
    # must be at least 3 characters
    if len(t) < 3:
        return False
    # must be alphabetic (spaces allowed between words)
    if not t.replace(" ", "").isalpha():
        return False
    # reject three or more identical consecutive characters (e.g., 'aaaa' or 'jjj')
    if re.search(r"(.)\1{2,}", t.replace(" ", "")):
        return False
    # require at least one vowel (to avoid pure consonant gibberish)
    if not has_vowel(t):
        return False
    return True

# ---------- Inference ----------
def forward_chain(rules, facts):
    facts = facts[:]
    conclusions = set()
    changed = True
    while changed:
        changed = False
        for r in rules:
            # rule's preconditions must all be present in facts
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
    # Use safe JSON-encoded string inside a tiny HTML/JS component
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

# ---------- Page config and CSS ----------
st.set_page_config(page_title="Smart Health Knowledge Agent", layout="centered")
st.markdown("""
<style>
/* hide Streamlit header, menu, footer and some top placeholders */
header, footer, [data-testid="stToolbar"], nav[aria-label], .css-1kyxreq, .css-1y4p8pa, .css-1n76uvr { display: none !important; }
.block-container { padding-top: 0rem !important; }
/* main container that looks like your HTML design */
.main-box {
  max-width: 980px;
  margin: 18px auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 6px 26px rgba(0,0,0,0.06);
  padding: 26px;
}
h1 { color: #1565c0; font-weight:700; }
button { background-color: #1565c0 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------- MAIN ----------
st.markdown('<div class="main-box">', unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;'>Smart Health Knowledge Agent 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#555;'>This mini AI guesses your condition from symptoms. You can teach it new rules too!</p>", unsafe_allow_html=True)

# load rules (fresh each run)
rules = load_rules()

# ---------- Known Rules (appear first) ----------
st.markdown("### 🧩 Known Rules")
if not rules:
    st.info("No rules found yet.")
else:
    for i, r in enumerate(rules):
        left, right = st.columns([0.82, 0.18])
        left.markdown(f"If {', '.join(r['if'])} → Then: **{r['then']}**")
        if right.button("❌ Delete", key=f"del_{i}"):
            rules.pop(i)
            save_rules(rules)
            st.success("Rule deleted.")
            # reload rules so UI below reflects change
            rules = load_rules()

st.markdown("---")

# ---------- Add rule form ----------
st.markdown("### 💡 Add a New Rule")
with st.form("add_rule", clear_on_submit=False):
    conds = st.text_input("If parts (comma separated):")
    concl = st.text_input("Then part:")
    submit_add = st.form_submit_button("Add Rule")
    if submit_add:
        conds_clean = clean_text(conds)
        concl_clean = clean_text(concl)
        if not conds_clean or not concl_clean:
            st.error("Please provide both condition(s) and a conclusion.")
        else:
            conditions = [c.strip() for c in conds_clean.split(",") if c.strip()]
            invalid = []
            for t in conditions + [concl_clean]:
                if not is_valid_term(t):
                    invalid.append(t)
            if invalid:
                st.error("Invalid terms detected. Each term must be alphabetic, at least 3 letters, contain a vowel, and not be repetitive. Invalid: " + ", ".join(invalid))
            else:
                rules.append({"if": conditions, "then": concl_clean})
                save_rules(rules)
                st.success("✅ Rule added successfully.")
                rules = load_rules()

st.markdown("---")

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
            speak("No exact match found. Possible conditions are: " + ", ".join([f"{p['disease']} ({p['prob']} percent)" for p in probs]))
        else:
            st.info("No condition found. Try different symptoms.")
            speak("No condition found. Try different symptoms.")

# optional link to Pneumonia Detection App
st.markdown("""
<p style='text-align:center;margin-top:18px;'>
  <a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
    <button style="padding:10px 18px; border-radius:8px;">Go to Pneumonia Detection App</button>
  </a>
</p>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
