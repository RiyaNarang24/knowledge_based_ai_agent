import streamlit as st
import json, os, re

st.set_page_config(page_title="Smart Health Knowledge Agent", layout="centered")

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
    cleaned = term.replace(" ", "")
    if not cleaned.isalpha() or len(cleaned) < 3:
        return False
    if re.search(r'([a-z])\\1{3,}', cleaned):
        return False
    return True


# --- Style ---
st.markdown("""
    <style>
    body {font-family:'Segoe UI', Tahoma, sans-serif;}
    .main-container {
        max-width:800px;
        margin:30px auto;
        background:white;
        border-radius:16px;
        box-shadow:0 0 20px rgba(0,0,0,0.1);
        padding:30px 40px;
    }
    h1 {text-align:center; color:#1565c0; margin-bottom:10px;}
    p.intro {text-align:center; color:#555;}
    .box {background:#f9fbfd; border-radius:10px; padding:15px; margin:15px 0;}
    input {padding:8px; width:65%; border:1px solid #ccc; border-radius:6px;}
    button, .stButton>button {
        background-color:#1565c0; color:white; border:none;
        padding:8px 14px; border-radius:6px; cursor:pointer;
    }
    .stButton>button:hover {background-color:#0d47a1;}
    .result {
        background:#e8f5e9; padding:15px; border-radius:8px;
        color:#2e7d32; font-weight:bold;
    }
    .probability {
        background:#fffde7; color:#795548;
        padding:10px; border-radius:8px; margin-top:10px;
    }
    footer {text-align:center; color:gray; margin-top:20px; font-size:0.9em;}
    </style>
""", unsafe_allow_html=True)

# --- Main container ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

st.markdown("<h1>Smart Health Knowledge Agent 🤖</h1>", unsafe_allow_html=True)
st.markdown('<p class="intro">This mini AI guesses your condition from symptoms. You can teach it new rules too!</p>', unsafe_allow_html=True)

rules = load_rules()

# --------------------------
# 1️⃣ Known Rules
# --------------------------
st.markdown('<div class="box"><h3>🧩 Known Rules</h3>', unsafe_allow_html=True)
if rules:
    for i, r in enumerate(rules):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**If:** {', '.join(r['if'])} → **Then:** {r['then']}")
        with col2:
            if st.button("❌ Delete", key=f"del_{i}"):
                rules.pop(i)
                save_rules(rules)
                st.experimental_rerun()
else:
    st.write("No rules found.")
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 2️⃣ Add New Rule
# --------------------------
st.markdown('<div class="box"><h3>💡 Add a New Rule</h3>', unsafe_allow_html=True)
conditions_input = st.text_input("If parts (comma separated):", key="conditions")
conclusion_input = st.text_input("Then part:", key="conclusion")

if st.button("Add Rule"):
    conditions = [c.strip() for c in clean_text(conditions_input.lower()).split(",") if c.strip()]
    conclusion = clean_text(conclusion_input.lower())

    if not is_valid_input_term(conclusion):
        st.warning("⚠️ Invalid conclusion entered.")
    elif not conditions:
        st.warning("⚠️ Please enter at least one condition.")
    elif not all(is_valid_input_term(c) for c in conditions):
        st.warning("⚠️ Invalid condition(s) entered.")
    else:
        rules.append({"if": conditions, "then": conclusion})
        save_rules(rules)
        st.success("✅ Rule added successfully!")
        st.experimental_rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 3️⃣ Ask the AI
# --------------------------
st.markdown('<div class="box"><h3>🧠 Ask the AI</h3>', unsafe_allow_html=True)
facts_input = st.text_input("Enter symptoms (comma separated):", key="facts")

if st.button("Infer"):
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
        text = f"Possible Condition(s): {', '.join(conclusions)}"
        st.markdown(f'<div class="result">{text}</div>', unsafe_allow_html=True)
        st.components.v1.html(f"""
            <script>
                const msg = new SpeechSynthesisUtterance("{text}");
                window.speechSynthesis.speak(msg);
            </script>
        """, height=0)
    else:
        probs = []
        for r in rules:
            match_count = sum(cond in facts for cond in r["if"])
            if match_count > 0:
                prob = int((match_count / len(r["if"])) * 100)
                if prob >= 30:
                    probs.append((r["then"], prob))

        if probs:
            st.markdown('<div class="probability"><b>No exact match found.</b><br>Possible conditions:</div>', unsafe_allow_html=True)
            for d, p in probs:
                st.markdown(f"- {d} — {p}%")
            speech_text = "No exact match found. Possible conditions are: " + ", ".join(
                [f"{d} with {p} percent probability" for d, p in probs])
            st.components.v1.html(f"""
                <script>
                    const msg = new SpeechSynthesisUtterance("{speech_text}");
                    window.speechSynthesis.speak(msg);
                </script>
            """, height=0)
        else:
            st.markdown('<div class="result">No condition found. Try different symptoms.</div>', unsafe_allow_html=True)
            st.components.v1.html("""
                <script>
                    const msg = new SpeechSynthesisUtterance("No condition found. Try different symptoms.");
                    window.speechSynthesis.speak(msg);
                </script>
            """, height=0)

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# 4️⃣ Pneumonia App Link
# --------------------------
st.markdown("""
    <a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
      <button style="padding:10px 20px; background-color:#4CAF50; color:white; border:none; border-radius:6px;">
        Go to Pneumonia Detection App
      </button>
    </a>
""", unsafe_allow_html=True)

# --------------------------
# 5️⃣ Footer
# --------------------------
st.markdown('<footer>🩺 Student Project — Simple AI Health Assistant</footer>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
