from flask import Flask, render_template, request, redirect, url_for
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os

app = Flask(__name__)

# -------------------------------
# 📘 RULE-BASED SYSTEM
# -------------------------------
rules = [
    {"if": ["sneezing", "cough", "cold"], "then": "flu"},
    {"if": ["fever", "body pain"], "then": "viral infection"},
    {"if": ["headache", "nausea"], "then": "migraine"},
    {"if": ["rash", "itching"], "then": "allergy"},
    {"if": ["tiredness", "weakness"], "then": "fatigue"}
]

# Helper function for reasoning
def infer_from_rules(facts):
    conclusions = set()
    for rule in rules:
        if all(cond in facts for cond in rule["if"]):
            conclusions.add(rule["then"])
    return list(conclusions)

# -------------------------------
# 🧠 CNN IMAGE-BASED DETECTOR
# -------------------------------
# Load your trained CNN model
MODEL_PATH = "disease_model.h5"
cnn_model = None
class_labels = ['covid', 'malaria', 'normal', 'pneumonia', 'tuberculosis']  # update this after training

if os.path.exists(MODEL_PATH):
    cnn_model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ CNN Model loaded successfully.")
else:
    print("⚠️ CNN model not found. Only rule-based diagnosis will work.")

def predict_image(img_path):
    """Predict disease from uploaded image."""
    try:
        img = image.load_img(img_path, target_size=(128, 128))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = x / 255.0

        preds = cnn_model.predict(x)[0]
        class_idx = np.argmax(preds)
        confidence = round(preds[class_idx] * 100, 2)
        return class_labels[class_idx], confidence
    except Exception as e:
        print("Error predicting image:", e)
        return None, 0

# -------------------------------
# 🌐 ROUTES
# -------------------------------
@app.route('/')
def index():
    return render_template('index.html', rules=rules, results=None)

@app.route('/add_rule', methods=['POST'])
def add_rule():
    conditions = request.form.get('conditions', '').lower().split(',')
    conclusion = request.form.get('conclusion', '').strip().lower()
    conditions = [c.strip() for c in conditions if c.strip().isalpha()]

    if conditions and conclusion.isalpha():
        rules.append({"if": conditions, "then": conclusion})
    return redirect(url_for('index'))

@app.route('/delete_rule/<int:index>', methods=['POST'])
def delete_rule(index):
    if 0 <= index < len(rules):
        rules.pop(index)
    return redirect(url_for('index'))

@app.route('/infer', methods=['POST'])
def infer():
    user_facts = request.form.get('facts', '').lower().split(',')
    user_facts = [f.strip() for f in user_facts if f.strip().isalpha()]
    conclusions = infer_from_rules(user_facts)
    image_result = None
    confidence = None

    # Handle uploaded image
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            path = os.path.join("static", file.filename)
            file.save(path)
            if cnn_model:
                image_result, confidence = predict_image(path)

    final_result = conclusions.copy()
    if image_result:
        final_result.append(f"{image_result} ({confidence}% confidence)")

    return render_template('index.html', rules=rules,
                           results={'conclusions': final_result})

# -------------------------------
# 🚀 RUN APP
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
