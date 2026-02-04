import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'heart_disease_data.csv'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me'

# Load data and train model on startup
heart_data = pd.read_csv(DATA_PATH)
X = heart_data.drop(columns='target', axis=1)
Y = heart_data['target']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, stratify=Y, random_state=2)
model = LogisticRegression(max_iter=500, solver='liblinear')
model.fit(X_train, Y_train)

# compute accuracies
training_data_accuracy = accuracy_score(model.predict(X_train), Y_train)
test_data_accuracy = accuracy_score(model.predict(X_test), Y_test)

# add jinja filter for percent formatting
@app.template_filter()
def percent(value, digits=0):
    try:
        return f"{value * 100:.{int(digits)}f}%"
    except Exception:
        return value

# example input (first row)
EXAMPLE = X.iloc[0].tolist()
FEATURES = X.columns.tolist()

@app.route('/')
def index():
    return render_template('index.html', features=FEATURES, example=EXAMPLE, test_acc=test_data_accuracy, train_acc=training_data_accuracy)

@app.route('/predict', methods=['POST'])
def predict():
    # read form values (each feature sent individually)
    try:
        values = [float(request.form.get(f, '').strip()) for f in FEATURES]
    except ValueError:
        # fallback: support comma separated single input field
        raw = request.form.get('raw_input', '')
        try:
            parts = [float(p.strip()) for p in raw.split(',') if p.strip() != '']
            if len(parts) != len(FEATURES):
                return render_template('result.html', error=f'Expected {len(FEATURES)} values but got {len(parts)}', features=FEATURES)
            values = parts
        except Exception:
            return render_template('result.html', error='Invalid input. Ensure values are numeric.')

    arr = np.array(values).reshape(1, -1)
    pred = int(model.predict(arr)[0])
    proba = None
    if hasattr(model, 'predict_proba'):
        proba = float(model.predict_proba(arr)[0][1])

    return render_template('result.html', prediction=pred, probability=proba, values=values, features=FEATURES, test_acc=test_data_accuracy, train_acc=training_data_accuracy)

# Serve assets folder (images)
@app.route('/assets/<path:filename>')
def assets(filename):
    assets_dir = os.path.join(BASE_DIR, 'assets')
    return send_from_directory(assets_dir, filename)

if __name__ == '__main__':
    app.run(debug=True)
