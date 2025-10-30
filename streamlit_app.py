import streamlit as st
import subprocess
import os

st.set_page_config(page_title="Smart Health AI", page_icon="🧠", layout="wide")

st.title("🤖 Smart Health AI Assistant")

st.write("This app connects to your Flask backend and provides the same functionality as your AI project.")

# Run your Flask app as a background process if it's not already running
if st.button("Start Flask Backend"):
    subprocess.Popen(["python", "app.py"])  # or your main Flask file name
    st.success("Backend started successfully!")

# Optionally, link to your local or deployed Flask web page
st.markdown("[Open Flask Web App](http://localhost:5000)")

st.info("You can deploy this Streamlit wrapper on Streamlit Cloud. It will automatically install dependencies from requirements.txt.")
