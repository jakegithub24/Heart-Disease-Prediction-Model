import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(
    BASE_DIR, '..', 'heart_disease_data.csv'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'

# Load data and train model on startup
try:
    heart_data = pd.read_csv(DATA_PATH)
    X = heart_data.drop(columns='target', axis=1)
    Y = heart_data['target']
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.2, stratify=Y, random_state=2)
    model = LogisticRegression(max_iter=500, solver='liblinear')
    model.fit(X_train, Y_train)

    # compute accuracies
    training_data_accuracy = accuracy_score(model.predict(X_train), Y_train)
    test_data_accuracy = accuracy_score(model.predict(X_test), Y_test)

    # Get classification report for metrics
    y_pred = model.predict(X_test)
    report = classification_report(Y_test, y_pred, output_dict=True)

    FEATURES = X.columns.tolist()
    EXAMPLE = X.iloc[0].tolist()
    EXAMPLE_DICT = dict(zip(FEATURES, EXAMPLE))

except Exception as e:
    print(f"Error loading data: {e}")
    FEATURES = []
    EXAMPLE = []
    EXAMPLE_DICT = {}
    training_data_accuracy = 0
    test_data_accuracy = 0
    report = {}

# add jinja filter for percent formatting


@app.template_filter()
def percent(value, digits=1):
    try:
        return f"{value * 100:.{int(digits)}f}%"
    except Exception:
        return value


@app.route('/')
def home():
    """Landing page"""
    return render_template('home.html',
                           test_acc=test_data_accuracy,
                           train_acc=training_data_accuracy,
                           report=report)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Prediction page - handles both form display and submission"""
    if request.method == 'POST':
        try:
            # read form values
            values = []
            for f in FEATURES:
                val = request.form.get(f, '').strip()
                if not val:
                    # fallback: support comma separated single input field
                    raw = request.form.get('raw_input', '')
                    parts = [p.strip()
                             for p in raw.split(',') if p.strip() != '']
                    if len(parts) == len(FEATURES):
                        values = [float(p) for p in parts]
                        break
                    else:
                        return render_template('predict.html',
                                               features=FEATURES,
                                               example=EXAMPLE_DICT,
                                               test_acc=test_data_accuracy,
                                               error=f'Please fill all fields or provide {len(FEATURES)} comma-separated values')
                values.append(float(val))

            arr = np.array(values).reshape(1, -1)
            pred = int(model.predict(arr)[0])
            proba = model.predict_proba(arr)[0][1] if hasattr(
                model, 'predict_proba') else None

            # Store result in session for display
            session['prediction_result'] = {
                'prediction': pred,
                'probability': proba,
                'values': values,
                'features': FEATURES
            }

            return redirect(url_for('predict'))

        except ValueError:
            return render_template('predict.html',
                                   features=FEATURES,
                                   example=EXAMPLE_DICT,
                                   test_acc=test_data_accuracy,
                                   error='Invalid input. Please enter numeric values only.')

    # GET request - show form
    prediction_result = session.pop('prediction_result', None)
    return render_template('predict.html',
                           features=FEATURES,
                           example=EXAMPLE_DICT,
                           test_acc=test_data_accuracy,
                           prediction_result=prediction_result)

# Serve assets folder


@app.route('/assets/<path:filename>')
def assets(filename):
    assets_dir = os.path.join(BASE_DIR, 'assets')
    return send_from_directory(assets_dir, filename)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
