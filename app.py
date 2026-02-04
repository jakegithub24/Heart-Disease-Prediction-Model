import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

import streamlit as st
from PIL import Image


# loading the csv data to a Pandas DataFrame
heart_data = pd.read_csv('heart_disease_data.csv')
heart_data.head()
X = heart_data.drop(columns='target', axis=1)
Y = heart_data['target']
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, stratify=Y, random_state=2)
model = LogisticRegression()
# training the LogisticRegression model with Training data
model.fit(X_train, Y_train)

# accuracy on training data
X_train_prediction = model.predict(X_train)
training_data_accuracy = accuracy_score(X_train_prediction, Y_train)


# accuracy on test data
X_test_prediction = model.predict(X_test)
test_data_accuracy = accuracy_score(X_test_prediction, Y_test)

# web app
st.title('Heart Disease Prediction Model')

img = Image.open('heart_img.jpeg')
st.image(img, width=150)

st.markdown("""### Quick prediction ⚡
Enter comma-separated feature values (in the order shown below). You can copy the example from the dataset header.""")
placeholder = ", ".join(X.columns)
st.caption(f"Feature order: {placeholder}")

input_text = st.text_input('Provide comma separated features to predict heart disease', placeholder=placeholder)

if input_text:
    split_input = [s.strip() for s in input_text.split(',') if s.strip() != '']
    expected = X.shape[1]

    if len(split_input) != expected:
        st.warning(f"Expected {expected} values but got {len(split_input)}. Please provide values in this order: {', '.join(X.columns)}")
    else:
        try:
            np_df = np.asarray(split_input, dtype=float)
            reshaped_df = np_df.reshape(1, -1)

            prediction = model.predict(reshaped_df)[0]

            # show probability if available
            prob_text = ""
            if hasattr(model, 'predict_proba'):
                prob = model.predict_proba(reshaped_df)[0][1]
                prob_text = f" (probability: {prob*100:.1f}%)"
                st.metric("Disease probability", f"{prob*100:.1f}%")

            if prediction == 0:
                st.success(f"No heart disease detected ✅{prob_text}")
            else:
                st.error(f"Heart disease detected ❌{prob_text}")

            st.info(f"Model accuracy — Test: {test_data_accuracy:.2%}, Train: {training_data_accuracy:.2%}")

            with st.expander("See parsed input values"):
                for name, val in zip(X.columns, np_df):
                    st.write(f"- **{name}**: {val}")

        except ValueError:
            st.warning("Please ensure all values are numeric and separated by commas.")

st.subheader("About Data")
st.write(heart_data)
st.subheader("Model Performance on Training Data")
st.write(training_data_accuracy)
st.subheader("Model Performance on Test Data")
st.write(test_data_accuracy)
