import sys
import os
import joblib
import lightgbm
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QFormLayout, QComboBox, QTextEdit, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt

# Define a list of known amenities.
# IMPORTANT: This list and the feature names derived from it MUST MATCH
# how the model was trained. This is a placeholder.
KNOWN_AMENITIES = [
    'wifi', 'kitchen', 'tv', 'washer', 'dryer', 'air conditioning',
    'heating', 'gym', 'pool', 'parking', 'elevator', 'balcony'
]
# Define the expected feature columns for the model.
# IMPORTANT: The order and names MUST MATCH the training data.
# Address-related features are omitted here due to complexity and lack of info
# on how they were engineered for your model.
MODEL_FEATURES = ['n_rooms'] + [f'amenity_{a.lower().replace(" ", "_").replace("-", "_")}' for a in KNOWN_AMENITIES]


class ApartmentPricePredictor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Apartment Price Predictor")
        self.setMinimumSize(650, 500)  # Slightly increased size

        # Path to the model
        # Assumes GUI.py is in a directory, and one level up is the project root
        # e.g., project_root/scripts/GUI.py and project_root/data/models/model.joblib
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
        self.model_path = os.path.join(project_root, "models", "best_lgbm_model.joblib")

        self.model = self._load_model()

        self.tabs = QTabWidget()
        self.form_tab = QWidget()
        self.tabs.addTab(self.form_tab, "Input Form")

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8; /* Lighter background */
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px; /* Slightly larger base font */
                color: #333333; /* Darker grey for text */
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
                font-weight: 500; /* Slightly bolder labels */
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px 12px; /* More padding */
                border: 1px solid #cccccc; /* Softer border */
                border-radius: 5px; /* Softer radius */
                background-color: #ffffff;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #F01C5C; /* Highlight on focus */
                box-shadow: 0 0 0 2px rgba(240, 28, 92, 0.2); /* Subtle glow */
            }
            QTextEdit {
                min-height: 80px; /* Adjusted height */
                /* max-width: 380px; Removed max-width for better responsiveness */
            }
            QLineEdit, QComboBox {
                min-height: 30px; /* Standard height */
                /* max-width: 350px; Removed max-width */
            }
            QComboBox QAbstractItemView { /* Style dropdown list */
                background-color: #ffffff;
                border: 1px solid #cccccc;
                selection-background-color: #F01C5C;
                selection-color: white;
            }
            QPushButton {
                background-color: #F01C5C;
                color: white;
                padding: 10px 22px; /* More padding */
                border: none;
                border-radius: 5px;
                font-size: 15px; /* Larger font for button */
                font-weight: 600;
                min-width: 120px; /* Minimum width for button */
            }
            QPushButton:hover {
                background-color: #D0104A; /* Darker shade on hover */
            }
            QPushButton:pressed {
                background-color: #B00C3E; /* Even darker on press */
            }
            QFormLayout {
                spacing: 15px; /* Increased spacing */
                label-alignment: Qt.AlignLeft;
            }
            QTabWidget::pane { /* Style for the tab content area */
                border-top: 2px solid #F01C5C;
                background: #f0f4f8;
            }
            QTabBar::tab { /* Style for individual tabs */
                background: #e1e8f0;
                color: #555555;
                border: 1px solid #cccccc;
                border-bottom: none;
                padding: 8px 15px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #f0f4f8; /* Match pane background */
                color: #F01C5C;
                font-weight: 600;
                border-color: #F01C5C;
            }
            QTabBar::tab:hover {
                background: #d1dae3;
            }
        """)

        self.init_form_tab()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def _load_model(self):
        """Loads the pre-trained model."""
        try:
            model = joblib.load(self.model_path)
            print(f"Model loaded successfully from {self.model_path}")
            return model
        except FileNotFoundError:
            self._show_error_message(f"Model file not found at {self.model_path}. Please check the path.")
            return None
        except Exception as e:
            self._show_error_message(f"Error loading model: {e}")
            return None

    def init_form_tab(self):
        """Initializes the input form tab."""
        form_container_widget = QWidget()  # Use a container for better layout control
        layout = QVBoxLayout(form_container_widget)
        layout.setContentsMargins(30, 30, 30, 30)  # Increased margins
        layout.setSpacing(20)  # Increased spacing

        title = QLabel("Apartment Price Predictor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 25px; color: #F01C5C;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)  # Better for responsiveness

        self.address = QLineEdit()
        self.address.setPlaceholderText("e.g., 123 Main St, Anytown")
        form_layout.addRow(QLabel("Address:"), self.address)

        self.n_rooms = QComboBox()
        self.n_rooms.addItems([str(i) for i in range(1, 11)])  # Common range 1-10 rooms
        self.n_rooms.insertItem(0, "")  # Add an empty option as default
        self.n_rooms.setCurrentIndex(0)
        self.n_rooms.setEditable(True)  # Allow typing, but mainly for selection
        self.n_rooms.lineEdit().setPlaceholderText("Select or type number of rooms")
        self.n_rooms.lineEdit().setReadOnly(False)  # Allow editing if needed, though combobox is primary
        form_layout.addRow(QLabel("Number of Rooms:"), self.n_rooms)

        self.amenities = QTextEdit()
        self.amenities.setPlaceholderText("e.g., wifi, kitchen, tv, pool")
        form_layout.addRow(QLabel("Amenities (comma-separated):"), self.amenities)

        layout.addLayout(form_layout)

        submit_button = QPushButton("Predict Price")
        submit_button.clicked.connect(self.process_and_show_results)
        layout.addWidget(submit_button, alignment=Qt.AlignCenter)
        layout.addStretch()  # Add stretch to push content up

        self.form_tab.setLayout(QVBoxLayout())  # Main layout for form_tab
        self.form_tab.layout().addWidget(form_container_widget)  # Add styled container

    def process_and_show_results(self):
        """Gathers data from the form and calls show_results_tab."""
        if not self.model:
            self._show_error_message("Model is not loaded. Cannot make predictions.")
            return

        address_text = self.address.text()
        n_rooms_text = self.n_rooms.currentText()
        amenities_text = self.amenities.toPlainText()

        # Basic Validation
        if not n_rooms_text:
            self._show_error_message("Number of rooms must be specified.")
            return

        try:
            n_rooms_val = int(n_rooms_text)
            if n_rooms_val <= 0:
                raise ValueError("Number of rooms must be positive.")
        except ValueError:
            self._show_error_message("Invalid input for Number of Rooms. Please enter a positive integer.")
            return

        user_data = {
            "address": address_text,
            "n_rooms": n_rooms_val,
            "amenities_str": amenities_text
        }
        self.show_results_tab(user_data)

    def _prepare_input_for_model(self, user_data):
        """
        Prepares the input DataFrame for the model based on user_data.
        IMPORTANT: This function makes assumptions about feature engineering.
        The column names and transformations MUST match how the model was trained.
        """
        input_dict = {}

        # 1. Number of rooms
        input_dict['n_rooms'] = user_data.get('n_rooms', 1)  # Default to 1 if not provided, though validated earlier

        # 2. Amenities (One-Hot Encoding based on KNOWN_AMENITIES)
        user_amenities_list = [a.strip().lower() for a in user_data.get('amenities_str', '').split(',') if a.strip()]

        for known_amenity in KNOWN_AMENITIES:
            feature_name = f'amenity_{known_amenity.lower().replace(" ", "_").replace("-", "_")}'
            if known_amenity.lower() in user_amenities_list:
                input_dict[feature_name] = 1
            else:
                input_dict[feature_name] = 0

        # 3. Address:
        # Processing the address string into meaningful features (e.g., lat/lon, neighborhood category)
        # is complex and depends heavily on how the model was trained.
        # This part is omitted here. If your model uses address-derived features,
        # you'll need to implement the same feature engineering steps here.
        # For now, we are only using features defined in MODEL_FEATURES.
        print(f"Raw input dict for model: {input_dict}")

        # Create a DataFrame with columns in the correct order expected by the model
        # Only include features that are in MODEL_FEATURES
        filtered_input_dict = {key: input_dict.get(key, 0) for key in MODEL_FEATURES}  # Default to 0 for safety

        # Ensure all MODEL_FEATURES are present, even if not in input_dict (e.g. if KNOWN_AMENITIES changes)
        for feature in MODEL_FEATURES:
            if feature not in filtered_input_dict:
                filtered_input_dict[feature] = 0  # Default for missing features (e.g., new amenity not in user input)

        input_df = pd.DataFrame([filtered_input_dict], columns=MODEL_FEATURES)
        print(f"DataFrame sent to model:\n{input_df}")
        return input_df

    def show_results_tab(self, user_data):
        """Creates a new tab to display the prediction results."""
        result_tab_widget = QWidget()
        layout = QVBoxLayout(result_tab_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)  # Align content to the top

        result_title = QLabel("Prediction Result")
        result_title.setAlignment(Qt.AlignCenter)
        result_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #F01C5C;")
        layout.addWidget(result_title)

        # Display user input for confirmation (optional but good UX)
        input_summary_label = QLabel("<b>Input Summary:</b>")
        layout.addWidget(input_summary_label)

        details_text = f"  Address: {user_data.get('address', 'N/A')}\n" \
                       f"  Number of Rooms: {user_data.get('n_rooms', 'N/A')}\n" \
                       f"  Amenities: {user_data.get('amenities_str', 'N/A')}"
        input_details = QLabel(details_text)
        input_details.setWordWrap(True)
        layout.addWidget(input_details)

        # Placeholder for prediction
        prediction_label = QLabel("Calculating prediction...")
        prediction_label.setAlignment(Qt.AlignCenter)
        prediction_label.setStyleSheet("font-size: 18px; margin-top: 20px; margin-bottom: 20px;")
        layout.addWidget(prediction_label)

        try:
            # Prepare input data for the model
            input_df = self._prepare_input_for_model(user_data)

            # Make prediction
            # The model.predict() might return an array, so take the first element.
            predicted_price = self.model.predict(input_df)[0]

            # Display the prediction
            # Format the price nicely, e.g., with a currency symbol and two decimal places.
            prediction_label.setText(f"<b>Predicted Price: ${predicted_price:,.2f}</b>")
            prediction_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #008000; margin-top: 20px;")


        except Exception as e:
            error_msg = f"Error during prediction: {e}"
            print(error_msg)
            prediction_label.setText(f"<span style='color:red;'>Error: Could not make prediction. {e}</span>")
            self._show_error_message(error_msg)  # Also show in a dialog

        layout.addStretch()  # Push content up

        # Add the new result tab and switch to it
        tab_index = self.tabs.addTab(result_tab_widget,
                                     f"Result {self.tabs.count()}")  # self.tabs.count() gives new index before adding
        self.tabs.setCurrentIndex(tab_index)

    def _show_error_message(self, message):
        """Displays an error message in a QMessageBox."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ApartmentPricePredictor()
    window.show()
    sys.exit(app.exec())
