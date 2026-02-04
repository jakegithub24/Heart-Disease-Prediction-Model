# Flask Heart Disease Prediction App

A simple Flask port of the Streamlit demo. It trains a Logistic Regression on the included `heart_disease_data.csv` on startup and provides a web form to enter features and get a prediction.

## Quick start (Linux)

```bash
cd FlaskApp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000
```

## Notes
- The `assets` folder contains images used by the UI and is served at `/assets/*`.
- This app is for demo purposes only and not intended for clinical use.
