import streamlit as st
import json
import os

# --- File to store rules ---
RULES_FILE = "rules.json"

# --- Load and Save Functions ---
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    return []

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)

# --- Page Config ---
st.set_page_config(page_title="Smart Health Knowledge Agent", page_icon="🤖", layout="centered")

# --- Header ---
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
if rules:
    st.subheader("🧩 Known Rules")
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
    st.info("No rules found yet. Add some below!")

# --- Add New Rule ---
st.subheader("💡 Add a New Rule")
with st.form("add_rule_form"):
    conditions = st.text_input("If parts (comma separated):")
    conclusion = st.text_input("Then part:")
    add_btn = st.form_submit_button("Add Rule")

if add_btn:
    # 🛡️ Validation for empty or junk input
    if not conditions.strip() or not conclusion.strip():
        st.warning("⚠️ Please enter both 'If' and 'Then' parts.")
    elif any(not part.strip().isalpha() for part in conclusion.split()):
        st.error("❌ Please use only letters for your rule (no numbers or symbols).")
    else:
        rules.append({"if": [c.strip() for c in conditions.split(",")], "then": conclusion.strip()})
        save_rules(rules)
        st.success("✅ Rule added successfully!")
        st.rerun()

# --- Infer Section ---
st.subheader("🧠 Ask the AI")
facts = st.text_input("Enter symptoms (comma separated):")
if st.button("Infer"):
    if not facts.strip():
        st.warning("Please enter some symptoms.")
    else:
        # Simple inference
        found = False
        conclusions = []
        facts_list = [f.strip().lower() for f in facts.split(",")]

        for rule in rules:
            if all(cond.lower() in facts_list for cond in rule["if"]):
                conclusions.append(rule["then"])
                found = True

        if found:
            result_text = f"Possible condition(s): {', '.join(conclusions)}"
            st.success(result_text)

            # 🎤 Voice output
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

# --- Pneumonia App Button ---
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
