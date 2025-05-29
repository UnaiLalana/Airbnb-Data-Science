import re
import sys
import os
import joblib
import lightgbm
from Columns import ALL_TRAINING_COLUMNS, ALL_AMENITIES_TO_DISPLAY
from geopy.geocoders import Nominatim
from shapely.geometry import Point, Polygon
import json
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QFormLayout, QComboBox, QTextEdit, QTabWidget, QMessageBox, QScrollArea,
    QHBoxLayout, QGroupBox, QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, QSize
import requests


EXCHANGE_RATE_API_KEY = "a5b90bd3bfd8e4a2f16083c5"
EXCHANGE_RATE_API_BASE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/SEK"

COMMON_CURRENCIES = {
    "USD": "United States Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "SEK": "Swedish Krona",  # Base currency
    "DKK": "Danish Krone",
    "NOK": "Norwegian Krone",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "JPY": "Japanese Yen",
    "CHF": "Swiss Franc",
    "INR": "Indian Rupee",
}


class ResultTab(QWidget):
    NEIGH_NAME = ""
    TOP_AMENITIES = [
        'bikes',
        'coffee_maker',
        'outdoor_dining_area',
        'bay_view',
        'beach_access_beachfront',
        'lake_access',
        'pool',
        'private_pool',
        'sauna',
        'hot_tub',
        'bbq_grill',
        'patio_or_balcony',
        'gym',
        'waterfront',
        'air_conditioning',
        'washer',
        'dryer',
        'wifi',
        'kitchen',
        'hdtv_with_netflix',
        'dedicated_workspace',
        'self_check_in'
    ]

    # These are the *words* that showed a high ratio in top listings
    TOP_KEYWORDS_RATIO = [
        'Sköndal', 'tennis', 'Södermalm', 'month', 'beams', 'bicycles',
        'heritage', 'week', 'fruit', 'swedens'
    ]
    # These are general important words from the overall top common list (Image 3)
    # that are still relevant for description/title but not necessarily 'differentiating'
    TOP_KEYWORDS_COMMON = [
        'close', 'minutes', 'walk', 'central', 'located', 'area',
        'kitchen', 'restaurants', 'cozy', 'bed'
    ]

    def __init__(self, parent_app, user_data, predicted_sek_price):
        super().__init__()
        self.parent_app = parent_app
        self.user_data = user_data
        self.predicted_sek_price = predicted_sek_price
        self.exchange_rates = {}

        self.init_ui()
        self._fetch_exchange_rates()
        self._update_currency_display()

    def init_ui(self):
        # Main layout of the ResultTab
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        result_title = QLabel("Prediction Result & Recommendations")
        result_title.setAlignment(Qt.AlignCenter)
        result_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #F01C5C;")
        main_layout.addWidget(result_title)

        # Input Summary Section
        input_summary_group = QGroupBox("Your Listing Summary")
        input_summary_group.setStyleSheet(
            "QGroupBox { font-size: 16px; font-weight: bold; margin-top: 10px; border: 1px solid #cccccc; border-radius: 5px; padding: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #F01C5C; }")
        input_summary_layout = QVBoxLayout(input_summary_group)

        details_text = f"  Address: {self.user_data.get('address', 'N/A')}\n" \
                       f"  Number of Rooms: {self.user_data.get('n_rooms', 'N/A')}\n" \
                       f"  Amenities: {', '.join([a.replace('_', ' ').title() for a in self.user_data.get('amenities_list', ['N/A'])])}\n" \
                       f"  Property Type: {self.user_data.get('property_type', 'N/A')}\n" \
                       f"  Room Type: {self.user_data.get('room_type', 'N/A')}"
        input_details = QLabel(details_text)
        input_details.setWordWrap(True)
        input_summary_layout.addWidget(input_details)
        main_layout.addWidget(input_summary_group)

        # Predicted Price Section
        self.prediction_label = QLabel(f"<b>Predicted Price: SEK {self.predicted_sek_price:,.2f}</b>")
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #008000; margin-top: 20px; margin-bottom: 20px;")
        self.prediction_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(self.prediction_label)

        # Currency Conversion Section (Keep as is)
        currency_h_layout = QHBoxLayout()
        currency_h_layout.setAlignment(Qt.AlignCenter)
        currency_h_layout.addWidget(QLabel("Convert to:"))
        self.currency_combo = QComboBox()
        for code, name in COMMON_CURRENCIES.items():
            self.currency_combo.addItem(f"{code} - {name}", code)
        self.currency_combo.setCurrentText("SEK - Swedish Krona")
        self.currency_combo.setMinimumWidth(200)
        self.currency_combo.currentIndexChanged.connect(self._update_currency_display)
        currency_h_layout.addWidget(self.currency_combo)
        main_layout.addLayout(currency_h_layout)

        self.converted_price_label = QLabel(f"")
        self.converted_price_label.setAlignment(Qt.AlignCenter)
        self.converted_price_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-top: 10px; color: #333333;")
        self.converted_price_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(self.converted_price_label)

        # --- Rebuilding Recommendations Section for Scrollability ---
        recommendations_content_widget = QWidget()
        recommendations_content_layout = QVBoxLayout(recommendations_content_widget)
        recommendations_content_layout.setContentsMargins(10, 10, 10, 10)
        recommendations_content_layout.setSpacing(15)

        # 1. Minimum Nights Recommendation
        min_nights_label = QLabel("<b>Minimum Nights per Stay:</b>")
        min_nights_label.setTextFormat(Qt.RichText)
        min_nights_text = """
        Based on successful listings, a good balance would be to set your minimum nights between <b>1 and 3 nights</b>.
        While many successful listings accept 1-night stays, 2-3 nights are also very common among top performers,
        potentially attracting slightly longer, more stable bookings while still offering flexibility. This also optimizes the
        number of necessary cleanings of the apartment.
        """
        min_nights_details = QLabel(min_nights_text)
        min_nights_details.setWordWrap(True)
        min_nights_details.setTextFormat(Qt.RichText)
        recommendations_content_layout.addWidget(min_nights_label)
        recommendations_content_layout.addWidget(min_nights_details)
        recommendations_content_layout.addSpacing(10)

        # 2. Title and Description Keywords Recommendation
        title_keywords_label = QLabel("<b>Important Keywords for your Title & Description:</b>")
        title_keywords_label.setTextFormat(Qt.RichText)
        title_keywords_text = self._generate_title_keywords_suggestion()
        title_keywords_details = QLabel(title_keywords_text)
        title_keywords_details.setWordWrap(True)
        title_keywords_details.setTextFormat(Qt.RichText)
        recommendations_content_layout.addWidget(title_keywords_label)
        recommendations_content_layout.addWidget(title_keywords_details)
        recommendations_content_layout.addSpacing(10)

        # 3. Amenity Suggestions
        amenity_suggestions_label = QLabel("<b>Suggested Amenities to Stand Out:</b>")
        amenity_suggestions_label.setTextFormat(Qt.RichText)
        amenity_suggestions_text = self._generate_amenity_suggestions()
        amenity_suggestions_details = QLabel(amenity_suggestions_text)
        amenity_suggestions_details.setWordWrap(True)
        amenity_suggestions_details.setTextFormat(Qt.RichText)
        recommendations_content_layout.addWidget(amenity_suggestions_label)
        recommendations_content_layout.addWidget(amenity_suggestions_details)
        recommendations_content_layout.addSpacing(10)

        # 4. General Tips to Stand Out
        general_tips_label = QLabel("<b>General Tips to Stand Out Against Competition:</b>")
        general_tips_label.setTextFormat(Qt.RichText)
        general_tips_text = """
        * <b>High-Quality Photos:</b> Invest in professional photos that showcase your apartment's best features.
        * <b>Responsive Host:</b> Maintain a high host response rate and quick response times.
        * <b>Competitive Pricing:</b> The predicted price is a good starting point; adjust based on seasonality and local events.
        * <b>Exceptional Cleanliness:</b> Ensure your property is spotless. This is consistently a top review factor.
        * <b>Clear Communication:</b> Provide detailed check-in instructions and be available for guest questions.
        * <b>Unique Local Experiences:</b> Highlight nearby attractions, local restaurants, or unique aspects of the neighborhood.
        * <b>Guest-Centric Approach:</b> Provide small touches like a welcome basket, local guide, or essential toiletries.
        """
        general_tips_details = QLabel(general_tips_text)
        general_tips_details.setWordWrap(True)
        general_tips_details.setTextFormat(Qt.RichText)
        recommendations_content_layout.addWidget(general_tips_label)
        recommendations_content_layout.addWidget(general_tips_details)

        recommendations_group = QGroupBox("Recommendations to Stand Out")
        recommendations_group.setStyleSheet(
            "QGroupBox { font-size: 16px; font-weight: bold; margin-top: 5px; border: 1px solid #cccccc; border-radius: 5px; padding: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #007bff; }")
        recommendations_group.setLayout(recommendations_content_layout)

        scroll_area_recommendations = QScrollArea()
        scroll_area_recommendations.setWidgetResizable(True)
        scroll_area_recommendations.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area_recommendations.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area_recommendations.setWidget(recommendations_group)

        main_layout.addWidget(scroll_area_recommendations)
        main_layout.addStretch()

    def _fetch_exchange_rates(self):
        """Fetches exchange rates from the API."""
        try:
            response = requests.get(EXCHANGE_RATE_API_BASE_URL)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()
            if data and data['result'] == 'success':
                self.exchange_rates = data['conversion_rates']
                print("Exchange rates fetched successfully.")
            else:
                error_message = data.get('error-type', 'Unknown error')
                self.parent_app._show_error_message(f"Failed to fetch exchange rates: {error_message}")
                print(f"Failed to fetch exchange rates: {error_message}")
        except requests.exceptions.RequestException as e:
            self.parent_app._show_error_message(f"Network error fetching exchange rates: {e}")
            print(f"Network error fetching exchange rates: {e}")
        except Exception as e:
            self.parent_app._show_error_message(f"An unexpected error occurred while fetching exchange rates: {e}")
            print(f"An unexpected error occurred while fetching exchange rates: {e}")

    def _update_currency_display(self):
        """Converts and displays the price in the selected currency."""
        selected_currency_code = self.currency_combo.currentData()

        if not self.exchange_rates:
            self.converted_price_label.setText("Rates not available.")
            return

        if selected_currency_code in self.exchange_rates:
            exchange_rate = self.exchange_rates[selected_currency_code]
            converted_price = self.predicted_sek_price * exchange_rate
            self.converted_price_label.setText(
                f"Equivalent Price: {selected_currency_code} {converted_price:,.2f}"
            )
        else:
            self.converted_price_label.setText("Conversion not available for selected currency.")
            print(f"Currency code '{selected_currency_code}' not found in fetched rates.")

    def _generate_title_keywords_suggestion(self):
        """Generates suggestions for listing title and description keywords."""
        suggestions = [
            "Consider using keywords that highlight unique aspects or popular features of your listing. Here are some suggestions based on top-performing listings in Stockholm:"]

        ratio_keywords_str = ", ".join([f"<b>{word.replace('_', ' ').title()}</b>" for word in self.TOP_KEYWORDS_RATIO])
        suggestions.append(
            f"-   <b>To stand out:</b> {ratio_keywords_str}. These words appear more frequently in top listings relative to all listings.")

        common_keywords_str = ", ".join(
            [f"<b>{word.replace('_', ' ').title()}</b>" for word in self.TOP_KEYWORDS_COMMON])
        suggestions.append(
            f"-   <b>General important descriptors:</b> {common_keywords_str}. These are frequently used in successful descriptions.")

        suggestions.append(
            "\nAim for a descriptive yet concise title. For example: 'Charming Apartment with [Top Amenity] in " + self.NEIGH_NAME + "'.")

        return "\n".join(suggestions)

    def _generate_amenity_suggestions(self):
        """
        Generates a list of suggested amenities, excluding those the user has already entered.
        It uses ALL_TRAINING_COLUMNS to find the corresponding boolean features.
        """
        user_amenities_list_normalized = {self._normalize_string(a) for a in self.user_data.get('amenities_list', [])}

        suggested_amenities = []
        for top_amenity_feature_original in self.TOP_AMENITIES:
            if self._normalize_string(top_amenity_feature_original) not in user_amenities_list_normalized:
                readable_amenity_name = top_amenity_feature_original.replace('_', ' ').title()
                suggested_amenities.append(readable_amenity_name)

        if suggested_amenities:
            return "Based on top-performing listings, consider adding these amenities to enhance your listing:\n-   " + ", ".join(
                [f"<b>{a}</b>" for a in suggested_amenities])
        else:
            return "Great job! You seem to have included many of the top amenities already."

    def _normalize_string(self, s):
        """
        Normalizes a string by converting to lowercase, replacing spaces/hyphens with underscores,
        removing non-alphanumeric characters (except underscores), and cleaning multiple/leading/trailing underscores.
        """
        s = s.lower()
        s = s.replace(' ', '_').replace('-', '_')
        s = re.sub(r'[^a-z0-9_]', '', s)
        s = re.sub(r'_{2,}', '_', s)
        s = s.strip('_')
        return s


class ApartmentPricePredictor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Apartment Price Predictor")
        self.showMaximized()

        # Path to the model
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
        self.model_path = os.path.join(project_root, "models", "best_lgbm_model.joblib")
        # Path to geojson
        self.geojson_path = os.path.join(project_root, "neighbourhoods.geojson")

        self.model = self._load_model()
        self.stockholm_neighborhoods_geojson = self._load_geojson()

        # Initialize geolocator
        self.geolocator = Nominatim(user_agent="apartment_price_predictor_app")

        self.tabs = QTabWidget()
        self.form_tab = QWidget()
        self.tabs.addTab(self.form_tab, "Input Form")

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #333333;
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
                font-weight: 500;
            }
            QLineEdit, QTextEdit, QComboBox, QCheckBox {
                padding: 8px 12px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #ffffff;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #F01C5C;
            }
            QTextEdit {
                min-height: 80px;
            }
            QLineEdit, QComboBox {
                min-height: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                selection-background-color: #F01C5C;
                selection-color: white;
            }
            QPushButton {
                background-color: #F01C5C;
                color: white;
                padding: 10px 22px;
                border: none;
                border-radius: 5px;
                font-size: 15px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #D0104A;
            }
            QPushButton:pressed {
                background-color: #B00C3E;
            }
            QFormLayout {
                spacing: 15px;
                label-alignment: Qt.AlignLeft;
            }
            QTabWidget::pane {
                border-top: 2px solid #F01C5C;
                background: #f0f4f8;
            }
            QTabBar::tab {
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
                background: #f0f4f8;
                color: #F01C5C;
                font-weight: 600;
                border-color: #F01C5C;
            }
            QTabBar::tab:hover {
                background: #d1dae3;
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                margin-top: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #F01C5C;
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

    def _load_geojson(self):
        """Loads the GeoJSON data from the specified path."""
        try:
            with open(self.geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            print(f"GeoJSON loaded successfully from {self.geojson_path}")
            return geojson_data
        except FileNotFoundError:
            self._show_error_message(f"GeoJSON file not found at {self.geojson_path}. Please check the path.")
            return None
        except json.JSONDecodeError as e:
            self._show_error_message(f"Error decoding GeoJSON from {self.geojson_path}: {e}")
            return None
        except Exception as e:
            self._show_error_message(f"Error loading GeoJSON: {e}")
            return None

    def init_form_tab(self):
        """Initializes the input form tab."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        form_container_widget = QWidget()
        form_layout = QVBoxLayout(form_container_widget)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)

        title = QLabel("Apartment Price Predictor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 25px; color: #F01C5C;")
        form_layout.addWidget(title)

        input_form_layout = QFormLayout()
        input_form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        input_form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        input_form_layout.setSpacing(15)

        # --- Address Field (Moved to be first) ---
        self.address = QLineEdit()
        self.address.setPlaceholderText("e.g., 123 Main St, Stockholm")
        input_form_layout.addRow(QLabel("Address:"), self.address)
        # --- End Address Field ---

        self.n_rooms = QComboBox()
        self.n_rooms.addItems([str(i) for i in range(1, 21)])
        self.n_rooms.insertItem(0, "")
        self.n_rooms.setCurrentIndex(0)
        self.n_rooms.setEditable(True)
        self.n_rooms.setMinimumWidth(150)
        self.n_rooms.lineEdit().setPlaceholderText("Select or type number of rooms")
        self.n_rooms.lineEdit().setReadOnly(False)
        input_form_layout.addRow(QLabel("Number of Rooms:"), self.n_rooms)

        # --- Amenity Selection Section ---
        amenities_group = QGroupBox("Select Amenities:")
        amenities_layout = QVBoxLayout(amenities_group)

        self.amenity_search_bar = QLineEdit()
        self.amenity_search_bar.setPlaceholderText("Search amenities...")
        self.amenity_search_bar.textChanged.connect(self._filter_amenities)
        amenities_layout.addWidget(self.amenity_search_bar)

        self.amenity_checkbox_container = QWidget()
        self.amenity_checkbox_layout = QGridLayout(self.amenity_checkbox_container)
        self.amenity_checkbox_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.amenity_checkbox_layout.setSpacing(5)

        self.amenity_checkboxes = []



        # Filter ALL_TRAINING_COLUMNS to only include relevant amenity columns (or features you want to show)
        # This ensures that only features the model actually uses are selectable as amenities
        available_amenity_cols = [col for col in ALL_TRAINING_COLUMNS if col in ALL_AMENITIES_TO_DISPLAY]

        processed_amenities = {}
        for col in available_amenity_cols:
            display_name = col.replace('amenity_', '').replace('_', ' ').title()
            if display_name not in processed_amenities:
                processed_amenities[display_name] = col

        sorted_display_names = sorted(processed_amenities.keys())

        num_columns = 3
        for i, display_name in enumerate(sorted_display_names):
            original_col_name = processed_amenities[display_name]
            checkbox = QCheckBox(display_name)
            checkbox.setProperty("original_column_name", original_col_name)
            self.amenity_checkboxes.append(checkbox)
            row = i // num_columns
            col = i % num_columns
            self.amenity_checkbox_layout.addWidget(checkbox, row, col)

        amenities_scroll_area = QScrollArea()
        amenities_scroll_area.setWidgetResizable(True)
        amenities_scroll_area.setWidget(self.amenity_checkbox_container)
        amenities_scroll_area.setFixedHeight(300)

        amenities_layout.addWidget(amenities_scroll_area)
        form_layout.addWidget(amenities_group)
        # --- End Amenity Selection Section ---

        # Add input for property_type and room_type
        self.property_type = QComboBox()
        self.property_type.addItems([
            "", "Entire condo", "Entire rental unit", "Private room in home",
            "Entire home", "Private room in rental unit", "Entire guest suite",
            "Private room in condo", "Room in hotel", "Private room in guest suite",
            "Entire townhouse", "Private room in townhouse", "Room in boutique hotel",
            "Entire serviced apartment", "Private room in serviced apartment",
            "Entire loft", "Private room in loft", "Shared room in home",
            "Private room in hostel", "Shared room in hostel", "Entire cabin",
            "Entire guesthouse", "Private room in guesthouse", "Room in aparthotel",
            "Tiny home", "Private room in tiny home", "Entire cottage", "Entire villa",
            "Private room in villa", "Boat", "Camper/RV", "Private room in bed and breakfast",
            "Private room in casa particular", "Shared room in condo"
        ])
        input_form_layout.addRow(QLabel("Property Type:"), self.property_type)

        self.room_type = QComboBox()
        self.room_type.addItems(["", "Entire home/apt", "Private room", "Shared room", "Hotel room"])
        input_form_layout.addRow(QLabel("Room Type:"), self.room_type)

        form_layout.addLayout(input_form_layout)

        submit_button = QPushButton("Predict Price")
        submit_button.clicked.connect(self.process_and_show_results)
        form_layout.addWidget(submit_button, alignment=Qt.AlignCenter)
        form_layout.addStretch()

        scroll_area.setWidget(form_container_widget)

        main_form_tab_layout = QVBoxLayout(self.form_tab)
        main_form_tab_layout.addWidget(scroll_area)

    def _filter_amenities(self, text):
        """Filters amenity checkboxes based on search text."""
        search_text = text.lower()
        for checkbox in self.amenity_checkboxes:
            if search_text in checkbox.text().lower():
                checkbox.setVisible(True)
            else:
                checkbox.setVisible(False)

    def process_and_show_results(self):
        """Gathers data from the form and calls show_results_tab."""
        if not self.model:
            self._show_error_message("Model is not loaded. Cannot make predictions.")
            return
        if not self.stockholm_neighborhoods_geojson:
            self._show_error_message("Neighborhoods GeoJSON is not loaded. Cannot determine location.")
            return
        # Check if the API key is the default placeholder
        if EXCHANGE_RATE_API_KEY == "YOUR_API_KEY":
            self._show_error_message(
                "API Key for ExchangeRate-API is not set. Please replace 'YOUR_API_KEY' in the code "
                "with your actual key from exchangerate-api.com to enable currency conversion."
            )
            # For now, let's proceed to show prediction but currency conversion will fail
            # return

        address_text = self.address.text().strip()
        n_rooms_text = self.n_rooms.currentText().strip()

        # Get selected amenities from checkboxes
        selected_amenities_list = []
        for checkbox in self.amenity_checkboxes:
            if checkbox.isChecked():
                selected_amenities_list.append(checkbox.property("original_column_name"))

        property_type_text = self.property_type.currentText().strip()
        room_type_text = self.room_type.currentText().strip()

        # Basic Validation
        if not address_text:
            self._show_error_message("Address must be specified.")
            return
        if not n_rooms_text:
            self._show_error_message("Number of rooms must be specified.")
            return
        if not property_type_text:
            self._show_error_message("Property Type must be specified.")
            return
        if not room_type_text:
            self._show_error_message("Room Type must be specified.")
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
            "amenities_list": selected_amenities_list,
            "property_type": property_type_text,
            "room_type": room_type_text
        }
        self.show_results_tab(user_data)

    def show_results_tab(self, user_data):
        """Creates a new tab to display the prediction results."""
        predicted_price = None
        try:
            # Prepare input data for the model
            input_df = self._prepare_input_for_model(user_data)

            if input_df is None:
                self._show_error_message("Error preparing input for prediction.")
                return

            # Ensure all columns in ALL_TRAINING_COLUMNS are present, fill missing with 0
            for col in ALL_TRAINING_COLUMNS:
                if col not in input_df.columns:
                    input_df[col] = 0

            # Reorder columns to match training order (important for some models)
            input_df = input_df[ALL_TRAINING_COLUMNS]

            # Make prediction
            predicted_price = self.model.predict(input_df)[0]
            predicted_price = max(0, predicted_price)  # Ensure price is not negative
            predicted_price = round(predicted_price / 5) * 5 # closest multiple of 5



        except Exception as e:
            error_msg = f"Error during prediction: {e}"
            print(error_msg)
            self._show_error_message(error_msg)
            predicted_price = 0  # Default to 0 or some error indicator if prediction fails

        # Create and add the ResultTab
        result_tab_widget = ResultTab(self, user_data, predicted_price)
        tab_index = self.tabs.addTab(result_tab_widget, f"Result {self.tabs.count()}")
        self.tabs.setCurrentIndex(tab_index)

    def _get_coordinates(self, address):
        """
        Geocodes an address to get its latitude and longitude.
        Adds "Stockholm, Sweden" to the address for better accuracy within Stockholm.
        """
        try:
            full_address = f"{address}, Stockholm, Sweden"
            location = self.geolocator.geocode(full_address, timeout=10)
            if location:
                return location.latitude, location.longitude
            else:
                return None, None
        except Exception as e:
            print(f"Error geocoding address '{address}': {e}")
            return None, None

    def _get_neighborhood(self, latitude, longitude):
        """
        Determines the neighborhood based on latitude and longitude using the loaded GeoJSON.
        """
        if not self.stockholm_neighborhoods_geojson:
            return "[Neighborhood]"

        point = Point(longitude, latitude)

        for feature in self.stockholm_neighborhoods_geojson['features']:
            if 'geometry' in feature and 'properties' in feature and 'neighbourhood' in feature['properties']:
                try:
                    geom_type = feature['geometry']['type']
                    coordinates = feature['geometry']['coordinates']

                    if geom_type == 'Polygon':
                        polygon_geometry = Polygon(coordinates[0])
                    elif geom_type == 'MultiPolygon':
                        is_in_polygon = False
                        for poly_coords in coordinates:
                            polygon_geometry = Polygon(poly_coords[0])
                            if polygon_geometry.contains(point):
                                is_in_polygon = True
                                break
                        if is_in_polygon:
                            return feature['properties']['neighbourhood']
                        continue
                    else:
                        print(f"Warning: Unsupported geometry type '{geom_type}' for feature.")
                        continue

                    if polygon_geometry.contains(point):
                        return feature['properties']['neighbourhood']
                except Exception as e:
                    print(f"Error processing GeoJSON feature for neighborhood: {e}")
                    continue
        return "Unknown"

    def _prepare_input_for_model(self, user_data):
        """
        Prepares a pandas DataFrame row from user input suitable for model prediction.
        """
        latitude, longitude = self._get_coordinates(user_data["address"])
        if latitude is None or longitude is None:
            self._show_error_message(f"Could not determine coordinates for address: {user_data['address']}.")
            return None

        neighborhood = self._get_neighborhood(latitude, longitude)
        ResultTab.NEIGH_NAME = neighborhood
        print(f"Address: {user_data['address']}, Lat: {latitude}, Lon: {longitude}, Neighborhood: {neighborhood}")

        input_data = {col: 0 for col in ALL_TRAINING_COLUMNS}

        input_data['latitude'] = latitude
        input_data['longitude'] = longitude
        input_data['accommodates'] = user_data['n_rooms']
        input_data['bedrooms'] = user_data['n_rooms']
        input_data['beds'] = user_data['n_rooms'] * 1.5
        input_data['minimum_nights'] = 1
        input_data['maximum_nights'] = 1125
        input_data['availability_30'] = 20
        input_data['availability_60'] = 40
        input_data['availability_90'] = 60
        input_data['availability_365'] = 200
        input_data['number_of_reviews'] = 0
        input_data['review_scores_rating'] = 0
        input_data['review_scores_accuracy'] = 0
        input_data['review_scores_cleanliness'] = 0
        input_data['review_scores_checkin'] = 0
        input_data['review_scores_communication'] = 0
        input_data['review_scores_location'] = 0
        input_data['review_scores_value'] = 0
        input_data['instant_bookable'] = 0
        input_data['calculated_host_listings_count'] = 1
        input_data['reviews_per_month'] = 0
        input_data['host_duration_days'] = 1000
        input_data['num_bathrooms'] = max(1, user_data['n_rooms'] // 2)
        input_data['is_shared_bath'] = 0
        input_data['num_amenities'] = len(user_data['amenities_list'])
        input_data['num_host_verifications'] = 3
        input_data['never_reviewed'] = 1
        input_data['days_since_last_review'] = 9999
        input_data['days_since_first_review'] = 9999
        input_data['desc_sentiment'] = 0.5

        input_data['host_since'] = 365 * 3
        input_data['host_response_rate'] = 0.95
        input_data['host_acceptance_rate'] = 0.90
        input_data['host_is_superhost'] = 0
        input_data['host_listings_count'] = 1
        input_data['host_total_listings_count'] = 1
        input_data['host_has_profile_pic'] = 1
        input_data['host_identity_verified'] = 1

        # Process amenities - Set corresponding amenity columns to 1 if present
        for amenity_col_name in user_data['amenities_list']:
            if amenity_col_name in input_data:
                input_data[amenity_col_name] = 1
            else:
                print(
                    f"Warning: Selected amenity column '{amenity_col_name}' not found in training columns. This might affect prediction accuracy.")

        # Set one-hot encoded categorical features
        normalized_neighborhood = neighborhood.replace(" ", "_").replace("-", "_").replace("&", "and").lower()
        neighborhood_col = f'neighbourhood_cleansed_{normalized_neighborhood}'
        if neighborhood_col in input_data:
            input_data[neighborhood_col] = 1
        else:
            print(
                f"Warning: Neighborhood column '{neighborhood_col}' not found in training columns. This might affect prediction accuracy.")

        normalized_property_type = user_data['property_type'].replace(" ", "_").replace("/", "_").replace("-",
                                                                                                          "_").lower()
        if normalized_property_type == "entire_home_apt":
            if "property_type_entire_home_apt" in input_data:
                input_data["property_type_entire_home_apt"] = 1
            elif "property_type_entire_home" in input_data:
                input_data["property_type_entire_home"] = 1
            elif "property_type_entire_rental_unit" in input_data:
                input_data["property_type_entire_rental_unit"] = 1
        else:
            prop_col_name = f'property_type_{normalized_property_type}'
            if prop_col_name == 'property_type_hotel_room' and 'property_type_room_in_hotel' in input_data:
                input_data['property_type_room_in_hotel'] = 1
            elif prop_col_name in input_data:
                input_data[prop_col_name] = 1
            else:
                print(
                    f"Warning: Property type column '{prop_col_name}' not found in training columns. This might affect prediction accuracy.")

        normalized_room_type = user_data['room_type'].replace(" ", "_").replace("/", "_").replace("-", "_").lower()
        if normalized_room_type == "entire_home_apt":
            if "room_type_entire_home_apt" in input_data:
                input_data["room_type_entire_home_apt"] = 1
            elif "room_type_entire_home" in input_data:
                input_data["room_type_entire_home"] = 1
        else:
            room_col_name = f'room_type_{normalized_room_type}'
            if room_col_name in input_data:
                input_data[room_col_name] = 1
            else:
                print(
                    f"Warning: Room type column '{room_col_name}' not found in training columns. This might affect prediction accuracy.")

        input_df = pd.DataFrame([input_data])
        return input_df

    def _show_error_message(self, message):
        """Displays an error message box."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("Error")
        msg_box.setInformativeText(message)
        msg_box.setWindowTitle("Error")
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    predictor = ApartmentPricePredictor()
    predictor.show()
    sys.exit(app.exec())