# 💬 Sentiment Analysis of Airbnb Reviews using Transfer Learning

This notebook focuses on classifying Airbnb reviews into **positive** or **negative** sentiments. The core idea is to leverage transfer learning by first training a sentiment analysis model on the well-known IMDB movie reviews dataset and then applying this model to Airbnb reviews. Optionally, the model can be further fine-tuned using a small set of Airbnb reviews labeled via zero-shot classification with a Large Language Model (LLM).

---

## 🎯 Project Goal

The primary goal of this project is to build an effective sentiment classifier for Airbnb reviews. This involves:

1.  **Training a robust sentiment analysis model** on the IMDB dataset, which contains a large number of clearly positive and negative movie reviews.
2.  **Transferring the learned knowledge** from the IMDB model to classify the sentiment of Airbnb customer reviews, which are textually similar in nature.
3.  **Exploring fine-tuning** the model using a smaller, targeted set of Airbnb reviews. These labels are proposed to be generated using zero-shot classification techniques with an LLM, providing a cost-effective way to adapt the model to the specific nuances of Airbnb review language.

This approach aims to overcome the challenge of limited labeled data for Airbnb reviews by first learning general sentiment features from a larger, related dataset.

---

## ⚙️ Methodology

The sentiment analysis process is structured as follows:

-   **Data Acquisition**:
    -   Utilizing the IMDB dataset for initial model training, which provides a substantial corpus of labeled positive and negative reviews.
    -   Using a dataset of Airbnb reviews for the application of the trained model and for potential fine-tuning.

-   **Data Preprocessing**:
    -   Standard text cleaning techniques: removing HTML tags, punctuation, special characters, and converting text to lowercase.
    -   Tokenization of review text.
    -   Stop word removal to filter out common words that do not contribute significantly to sentiment.
    -   Vectorization of text data using TF-IDF (Term Frequency-Inverse Document Frequency) to convert text into numerical features suitable for machine learning models.

-   **Model Training & Transfer Learning**:
    -   Training a classification model (e.g., SGDClassifier, Logistic Regression) on the vectorized IMDB review data.
    -   The trained model, having learned to distinguish positive and negative sentiment from movie reviews, is then used directly to predict sentiment on the preprocessed Airbnb reviews.

-   **Fine-tuning (Optional)**:
    -   Generating sentiment labels for a subset of Airbnb reviews using a zero-shot classification approach with an LLM (e.g., Gemini API).
    -   Further training (fine-tuning) the IMDB-trained model on this smaller, domain-specific labeled Airbnb dataset to potentially improve its performance and adapt it more closely to the language used in Airbnb reviews.

-   **Evaluation**:
    -   Assessing model performance on a held-out test set from the IMDB dataset using metrics such as:
        -   Accuracy
        -   Precision, Recall, F1-score
        -   Confusion Matrix
    -   Qualitative analysis of predictions on Airbnb reviews.
    -   If fine-tuning is performed, evaluation will also be done on a held-out set of labeled Airbnb reviews.

---

## 🛠️ Technologies Used

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![NLTK](https://img.shields.io/badge/NLTK-3776AB?style=for-the-badge&logo=nltk&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=matplotlib&logoColor=white)
![Seaborn](https://img.shields.io/badge/Seaborn-3776AB?style=for-the-badge&logo=seaborn&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)

---

## 📓 Notebook Structure

The `SentimentAnalysis.ipynb` notebook is organized into the following key sections:

1.  **Introduction**: Outlines the project idea, including transfer learning from IMDB and the potential for fine-tuning with LLM-labeled Airbnb data.
2.  **Setup and Library Imports**: Imports necessary Python libraries.
3.  **Data Loading and Initial Exploration (IMDB)**: Loads the IMDB movie review dataset and performs an initial analysis.
4.  **Text Preprocessing**: Includes functions for cleaning text (removing HTML, special characters, etc.) and preparing it for vectorization.
5.  **Data Splitting**: Divides the IMDB dataset into training and testing sets.
6.  **Feature Extraction (Vectorization)**: Converts the preprocessed text data into numerical vectors using TF-IDF.
7.  **Model Training**: Trains a sentiment classification model (e.g., SGDClassifier) on the IMDB training data.
8.  **Model Evaluation**: Evaluates the trained model on the IMDB test set using various metrics and visualizations like a confusion matrix.
9.  **Saving and Loading the Model**: Demonstrates how to save the trained model for later use and how to load it back.
10. **Application to Airbnb Reviews**:
    * Loads Airbnb review data.
    * Applies the same preprocessing steps to the Airbnb reviews.
    * Uses the trained IMDB model to predict sentiment on Airbnb reviews.
11. **Analysis of Airbnb Predictions**: Investigates the distribution of predicted sentiments and probabilities for Airbnb reviews.
12. **Visualization of Results**: Includes plots such as the distribution of predicted probabilities for positive and negative reviews on the Airbnb dataset.
13. **(Optional) Fine-tuning Preparation**: Discusses the approach for labeling Airbnb data using zero-shot classification with an LLM for fine-tuning (implementation details might vary).

---

## 🚀 How to Run

1.  **Ensure Prerequisites**:
    * Python 3.x installed.
    * Jupyter Notebook or JupyterLab installed.
    * Required Python libraries installed. You can usually install them via pip:
        ```bash
        pip install pandas numpy nltk scikit-learn matplotlib seaborn
        ```
    * Download necessary NLTK resources (e.g., stopwords, punkt):
        ```python
        import nltk
        nltk.download('stopwords')
        nltk.download('punkt')
        ```

2.  **Download Data**:
    * Ensure the IMDB dataset (`IMDB Dataset.csv` or similar, as used in the notebook) is available in the specified path.
    * Ensure the Airbnb reviews dataset (e.g., `reviews.csv` from an Airbnb data source, as used in the notebook for prediction) is available.

3.  **Open and Run Notebook**:
    * Launch Jupyter Notebook or JupyterLab.
    * Navigate to the directory containing `SentimentAnalysis.ipynb`.
    * Open the notebook.
    * Run the cells sequentially from top to bottom.

---

## 📊 Expected Visualizations

The notebook aims to generate several visualizations to help understand the data and model performance, including:

-   **Confusion Matrix**: For the IMDB dataset evaluation, showing the performance of the classifier in terms of true positives, true negatives, false positives, and false negatives.
-   **Distribution of Predicted Probabilities**: Histograms showing the distribution of the model's predicted probabilities for both positive and negative sentiment classes on the Airbnb review data. This helps in understanding the model's confidence in its predictions and can be useful for setting custom thresholds.