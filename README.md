# 🏠 Airbnb Data Science: Sentiment Analysis & Price Prediction

This project addresses two main challenges using Airbnb data:

1. **Sentiment Analysis**: Classifying Airbnb reviews as **positive** or **negative** to help hosts, guests, and platforms gain insights into user experiences.
2. **Price Prediction**: Predicting the nightly price of Airbnb listings based on features such as location, amenities, and review sentiment.

---

## 📊 Project Overview

The project is divided into two main parts:

### 1. Sentiment Analysis

We leverage **transfer learning** by pretraining models on publicly available datasets:

- **IMDB Movie Reviews** – clear polarity-labeled text data

This approach enables better generalization and more effective sentiment classification on Airbnb reviews.

### 2. Price Prediction

We use machine learning regression models to predict Airbnb listing prices. Features include:

- Listing characteristics (location, number of rooms, amenities, etc.)
- Aggregated sentiment scores from guest reviews

This enables more accurate and data-driven pricing strategies for hosts and platforms.

---

## ⚙️ Methodology

- **Data Preprocessing**: Cleaning and transforming text and tabular data.
- **Model Training**:
  - **Sentiment Analysis**: Models like SGDClassifier, Logistic Regression, etc., trained on IMDB and fine-tuned on Airbnb.
  - **Price Prediction**: Regression models (e.g., Linear Regression, Random Forest) trained on Airbnb listing data.
- **Evaluation**: Using metrics such as accuracy, F1-score (for sentiment) and RMSE, MAE (for price prediction).

---

## 🛠️ Technologies Used

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![NLTK](https://img.shields.io/badge/NLTK%20-4B8BBE?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

---

## 📁 Project Structure

- `Price Prediction/` – Contains the files and notebook to predict nightly prices based on features
- `Sentiment Analysis/` – Contains the files and notebook to classify airbnb reviews between positive and negative sentiments

---

## 👥 Authors & Collaborators

This project is being developed by:

- [Unai Lalana](https://github.com/UnaiLalana)
- [Filippo Muscherá](https://github.com/FilippoMuschera)
- [Eneko Isturitz](https://github.com/EnekoIsturitzSesma)
- [Paul Gasnier](https://github.com/TheBloodMan49)
