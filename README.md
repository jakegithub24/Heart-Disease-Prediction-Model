# Heart Disease Prediction Model

A machine learning web application that predicts whether a person has heart disease based on various health features. Built with [Streamlit](https://streamlit.io/) for an interactive user interface.

## About the Project

This project uses a Logistic Regression model trained on the UCI Heart Disease dataset to predict the presence of heart disease. The model takes various medical features (like age, cholesterol levels, blood pressure, etc.) as input and outputs a binary classification: either the person has heart disease or not.

The application provides:
- An easy-to-use web interface for making predictions
- Model performance metrics (accuracy on training and test data)
- Visualization of the dataset used for training

## How the Project Works

1. **Data Loading**: The application loads the heart disease dataset from `heart_disease_data.csv`
2. **Model Training**: A Logistic Regression model is trained on the dataset during app startup
3. **User Input**: Users provide comma-separated feature values through the web interface
4. **Prediction**: The model processes the input and predicts whether heart disease is present
5. **Results**: The prediction result is displayed along with model accuracy metrics

## Tech Used

- **Python 3.8+**
- **Streamlit** - Web application framework
- **Scikit-learn** - Machine learning library (Logistic Regression)
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **PIL/Pillow** - Image handling

## Setup Guides

### Windows

1. **Clone the repository**
   ```bash
   git clone https://github.com/611noorsaeed/Heart-Disease-Prodiction-Model.git
   cd Heart-Disease-Prodiction-Model
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv myvenv
   ```

3. **Activate the virtual environment**
   ```bash
   myvenv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. Open your browser and go to `http://localhost:8501`

### Linux

1. **Clone the repository**
   ```bash
   git clone https://github.com/611noorsaeed/Heart-Disease-Prodiction-Model.git
   cd Heart-Disease-Prodiction-Model
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv myvenv
   ```

3. **Activate the virtual environment**
   ```bash
   source myvenv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. Open your browser and go to `http://localhost:8501`

## Future Improvements to be Done

- [ ] Add more machine learning models (Random Forest, SVM, Neural Networks) for comparison
- [ ] Implement cross-validation for more robust model evaluation
- [ ] Add data visualization charts (feature distributions, correlation matrix)
- [ ] Include feature importance analysis
- [ ] Add input validation with helpful error messages
- [ ] Save and load model checkpoints
- [ ] Add a prediction history feature
- [ ] Deploy the app to a cloud platform (Heroku, Streamlit Cloud, etc.)
- [ ] Add unit tests for model and UI components
- [ ] Implement hyperparameter tuning
- [ ] Add support for batch predictions via file upload
- [ ] Build a Flask app for production deployment

## Contribution

Contributions are welcome! If you'd like to improve this project, please:

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Submit a pull request with a detailed description

Please ensure your code follows the existing style and includes appropriate comments.

✨ Coding is Fun!