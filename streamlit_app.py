import streamlit as st
import json
import os

# --- File to store rules ---
RULES_FILE = "rules.json"

# --- Load & Save functions ---
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return []

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)

# --- Helper function for probability-based matching ---
def find_probable_conditions(rules, facts):
    results = []
    for rule in rules:
        match_count = sum(1 for cond in rule["if"] if cond.lower() in facts)
        if match_count > 0:
            prob = int((match_count / len(rule["if"])) * 100)
            results.append({"disease": rule["then"], "prob": prob})
    results.sort(key=lambda x: x["prob"], reverse=True)
    return [r for r in results if r["prob"] >= 30]  # only show >=30% matches

# --- Streamlit page setup ---
st.set_page_config(page_title="Smart Health Knowledge Agent", page_icon="🤖", layout="centered")

st.markdown(
    "<h1 style='text-align:center;color:#1565c0;'>Smart Health Knowledge Agent 🤖</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#555;'>This mini AI guesses your condition from symptoms. You can teach it new rules too!</p>",
    unsafe_allow_html=True,
)

rules = load_rules()

# --- Show Rules ---
st.subheader("🧩 Known Rules")
if rules:
    for i, r in enumerate(rules):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(f"**If:** {', '.join(r['if'])} → **Then:** {r['then']}")
        with col2:
            if st.button("❌ Delete", key=f"del{i}"):
                rules.pop(i)
                save_rules(rules)
                st.rerun()
else:
    st.info("No rules yet. Add one below!")

# --- Add Rule ---
st.subheader("💡 Add a New Rule")
with st.form("add_rule"):
    conditions = st.text_input("If parts (comma separated):")
    conclusion = st.text_input("Then part:")
    submitted = st.form_submit_button("Add Rule")

if submitted:
    if not conditions.strip() or not conclusion.strip():
        st.warning("⚠️ Please fill both fields.")
    elif any(char.isdigit() or not char.isalpha() for char in conclusion.strip()):
        st.error("❌ Please use only letters in your rule conclusion.")
    elif any(len(word.strip()) < 2 for word in conditions.split(",")):
        st.error("⚠️ Invalid or too short conditions.")
    else:
        rules.append({"if": [c.strip() for c in conditions.split(",")], "then": conclusion.strip()})
        save_rules(rules)
        st.success("✅ Rule added successfully!")
        st.rerun()

# --- Inference Section ---
st.subheader("🧠 Ask the AI")
facts_input = st.text_input("Enter symptoms (comma separated):")

if st.button("Infer"):
    if not facts_input.strip():
        st.warning("Please enter symptoms to infer.")
    else:
        facts = [f.strip().lower() for f in facts_input.split(",")]
        conclusions = []

        # Exact match search
        for rule in rules:
            if all(cond.lower() in facts for cond in rule["if"]):
                conclusions.append(rule["then"])

        if conclusions:
            result_text = f"Possible Condition(s): {', '.join(conclusions)}"
            st.success(result_text)
            st.markdown(
                f"""
                <script>
                const msg = new SpeechSynthesisUtterance("{result_text}");
                window.speechSynthesis.speak(msg);
                </script>
                """,
                unsafe_allow_html=True,
            )
        else:
            probable = find_probable_conditions(rules, facts)
            if probable:
                st.warning("No exact match found. Possible conditions based on similarity:")
                for p in probable:
                    st.markdown(f"- **{p['disease']}** — {p['prob']}% match")

                speech_text = "No exact match found. Possible conditions are: "
                for p in probable:
                    speech_text += f"{p['disease']} with {p['prob']} percent probability. "
                st.markdown(
                    f"""
                    <script>
                    const msg = new SpeechSynthesisUtterance("{speech_text}");
                    window.speechSynthesis.speak(msg);
                    </script>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.error("No condition found. Try different symptoms.")
                st.markdown(
                    """
                    <script>
                    const msg = new SpeechSynthesisUtterance("No condition found. Try different symptoms.");
                    window.speechSynthesis.speak(msg);
                    </script>
                    """,
                    unsafe_allow_html=True,
                )

# --- Pneumonia Detection App Button ---
st.markdown(
    """
    <div style="text-align:center; margin-top:30px;">
        <a href="https://smarthealthai-ncq7kky52fti3ncpsr73mz.streamlit.app/" target="_blank">
            <button style="padding:10px 20px; background-color:#4CAF50; color:white; border:none; border-radius:6px; cursor:pointer;">
                Go to Pneumonia Detection App
            </button>
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Footer ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:gray;'>🩺 Student Project — Simple AI Health Assistant</p>", unsafe_allow_html=True)
