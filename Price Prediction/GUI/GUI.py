import re
import sys
import os
import joblib
import lightgbm
from geopy.geocoders import Nominatim
from shapely.geometry import Point, Polygon
import json
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QFormLayout, QComboBox, QTextEdit, QTabWidget, QMessageBox, QScrollArea,
    QHBoxLayout  # Added for horizontal layout for currency conversion
)
from PySide6.QtCore import Qt, QSize
import requests  # Added for API calls

# Do NOT hardcode STOCKHOLM_NEIGHBORHOODS_GEOJSON. It will be loaded from the file.

# Hardcoded list of all training columns (sanitized) - THIS IS CORRECT TO BE HERE
ALL_TRAINING_COLUMNS = [
    'host_since', 'host_response_rate', 'host_acceptance_rate', 'host_is_superhost',
    'host_listings_count', 'host_total_listings_count', 'host_has_profile_pic',
    'host_identity_verified', 'latitude', 'longitude', 'accommodates', 'bedrooms', 'beds',
    'minimum_nights', 'maximum_nights', 'availability_30', 'availability_60',
    'availability_90', 'availability_365', 'number_of_reviews', 'review_scores_rating',
    'review_scores_accuracy', 'review_scores_cleanliness', 'review_scores_checkin',
    'review_scores_communication', 'review_scores_location', 'review_scores_value',
    'instant_bookable', 'calculated_host_listings_count', 'reviews_per_month',
    'host_duration_days', 'num_bathrooms', 'is_shared_bath', 'num_amenities',
    'num_host_verifications', 'never_reviewed', 'days_since_last_review',
    'days_since_first_review', 'desc_sentiment', 'col_2_5_years_old',
    'col_5_10_years_old', 'amazon_prime_video', 'and_10_years_old',
    'and_5_10_years_old', 'and_dresser', 'apple_tv', 'chromecast', 'closet',
    'disney', 'espresso_machine', 'every_day_available_at_extra_cost',
    'french_press', 'hbo_max', 'heated', 'nespresso', 'netflix', 'open_24_hours',
    'open_specific_hours', 'pool_cover', 'pour_over_coffee', 'premium_cable',
    'standard_cable', 'stationary_bike', 'tuesday_to_friday_available_at_extra_cost',
    'wardrobe', 'yoga_mat', 'col_55_inch_hdtv_with_apple_tv',
    'col_55_inch_hdtv_with_chromecast', 'col_55_inch_hdtv_with_netflix',
    'air_conditioning', 'arcade_games', 'baby_bath',
    'baby_bath_always_at_the_listing', 'baby_bath_available_upon_request',
    'baby_monitor', 'baby_monitor_available_upon_request', 'baby_safety_gates',
    'babysitter_recommendations', 'backyard', 'baking_sheet', 'barbecue_utensils',
    'bathtub', 'bay_view', 'bbq_grill', 'bbq_grill_charcoal',
    'beach_access_beachfront', 'beach_essentials', 'beach_view', 'bed_linens',
    'bidet', 'bikes', 'blender', 'bluetooth_sound_system', 'board_games',
    'boat_slip', 'body_soap', 'books_and_reading_material',
    'bosch_refrigerator', 'bread_maker', 'breakfast', 'building_staff',
    'canal_view', 'carbon_monoxide_alarm', 'ceiling_fan',
    'central_air_conditioning', 'central_heating', 'changing_table',
    'changing_table_always_at_the_listing',
    'changing_table_available_upon_request', 'children_s_playroom',
    'children_s_bikes', 'children_s_books_and_toys',
    'children_s_books_and_toys_for_ages_0_2_years_old',
    'children_s_books_and_toys_for_ages_0_2_years_old_and_2_5_years_old',
    'children_s_books_and_toys_for_ages_2_5_years_old',
    'children_s_books_and_toys_for_ages_2_5_years_old_and_5_10_years_old',
    'children_s_books_and_toys_for_ages_5_10_years_old',
    'children_s_books_and_toys_for_ages_5_10_years_old_and_10_years_old',
    'children_s_dinnerware', 'city_skyline_view',
    'cleaning_available_during_stay', 'cleaning_products', 'clothing_storage',
    'clothing_storage_closet', 'clothing_storage_closet_and_dresser',
    'clothing_storage_closet_and_wardrobe', 'clothing_storage_dresser',
    'clothing_storage_walk_in_closet',
    'clothing_storage_walk_in_closet_and_closet', 'clothing_storage_wardrobe',
    'clothing_storage_wardrobe_and_dresser', 'coffee', 'coffee_maker',
    'coffee_maker_drip_coffee_maker', 'coffee_maker_espresso_machine',
    'coffee_maker_french_press', 'coffee_maker_nespresso',
    'coffee_maker_pour_over_coffee', 'conditioner', 'cooking_basics',
    'courtyard_view', 'crib', 'crib_always_at_the_listing',
    'crib_available_upon_request', 'dedicated_workspace', 'dining_table',
    'dishes_and_silverware', 'dishwasher', 'double_oven', 'dove_body_soap',
    'dryer', 'dryer_in_building', 'dryer_in_unit',
    'drying_rack_for_clothing', 'electric_stove', 'electrolux_induction_stove',
    'electrolux_refrigerator', 'elevator', 'essentials',
    'ethernet_connection', 'ev_charger', 'ev_charger_level_2',
    'exercise_equipment', 'exercise_equipment_free_weights',
    'exercise_equipment_yoga_mat', 'exterior_security_cameras_on_property',
    'extra_pillows_and_blankets', 'family_fresh_body_soap', 'fire_extinguisher',
    'fire_pit', 'fireplace_guards', 'first_aid_kit',
    'free_driveway_parking_on_premises',
    'free_driveway_parking_on_premises_1_space', 'free_dryer',
    'free_dryer_in_building', 'free_dryer_in_unit', 'free_parking_on_premises',
    'free_street_parking', 'free_washer', 'free_washer_in_building',
    'free_washer_in_unit', 'freezer', 'game_console',
    'game_console_nintendo_switch', 'game_console_ps4', 'game_console_ps5',
    'garden_view', 'gas_stove', 'gym', 'hair_dryer', 'hammock', 'hangers',
    'hdtv', 'hdtv_with_apple_tv', 'hdtv_with_chromecast', 'hdtv_with_netflix',
    'heating', 'heating_split_type_ductless_system', 'high_chair',
    'high_chair_available_upon_request', 'hockey_rink', 'host_greets_you',
    'hot_tub', 'hot_water', 'hot_water_kettle',
    'housekeeping_available_at_extra_cost',
    'housekeeping_available_from_12_00_pm_to_5_00_pm', 'indoor_fireplace',
    'indoor_fireplace_wood_burning', 'induction_stove', 'iron', 'kayak', 'keypad',
    'kitchen', 'kitchenette', 'lake_access', 'lake_view', 'laundromat_nearby',
    'life_size_games', 'lock_on_bedroom_door', 'lockbox',
    'long_term_stays_allowed', 'luggage_dropoff_allowed', 'microwave',
    'miele_induction_stove', 'miele_refrigerator', 'mini_fridge', 'mini_golf',
    'mosquito_net', 'movie_theater', 'noise_decibel_monitors_on_property',
    'other_electric_stove', 'other_induction_stove', 'other_stove',
    'outdoor_dining_area', 'outdoor_furniture', 'outdoor_kitchen',
    'outdoor_playground', 'outdoor_shower', 'outlet_covers', 'oven',
    'pack_n_play_travel_crib', 'pack_n_play_travel_crib_always_at_the_listing',
    'pack_n_play_travel_crib_available_upon_request', 'paid_crib_available_upon_request',
    'paid_dryer_in_building', 'paid_pack_n_play_travel_crib_available_upon_request',
    'paid_parking_garage_off_premises', 'paid_parking_lot_off_premises',
    'paid_parking_lot_on_premises', 'paid_parking_lot_on_premises_1_space',
    'paid_parking_lot_on_premises_2_spaces', 'paid_parking_off_premises',
    'paid_parking_on_premises', 'paid_standalone_high_chair_available_upon_request',
    'paid_street_parking_off_premises', 'paid_washer_in_building',
    'paid_washer_in_unit', 'park_view', 'patio_or_balcony', 'pets_allowed', 'piano',
    'ping_pong_table', 'pocket_wifi', 'pool', 'pool_table', 'pool_view',
    'portable_air_conditioning', 'portable_fans', 'portable_heater',
    'private_backyard', 'private_backyard_fully_fenced',
    'private_backyard_not_fully_fenced', 'private_bbq_grill_charcoal',
    'private_bbq_grill_gas', 'private_entrance', 'private_gym_in_building',
    'private_hot_tub', 'private_living_room', 'private_outdoor_kitchen',
    'private_outdoor_pool_available_seasonally', 'private_patio_or_balcony',
    'private_pool', 'private_sauna', 'radiant_heating', 'record_player',
    'refrigerator', 'resort_access', 'rice_maker', 'room_darkening_shades', 'safe',
    'samsung_refrigerator', 'sauna', 'self_check_in', 'shampoo',
    'shared_backyard', 'shared_backyard_fully_fenced',
    'shared_backyard_not_fully_fenced', 'shared_bbq_grill_charcoal',
    'shared_beach_access', 'shared_beach_access_beachfront',
    'shared_gym_in_building', 'shared_gym_nearby', 'shared_patio_or_balcony',
    'shared_sauna', 'shower_gel', 'siemens_induction_stove', 'siemens_oven',
    'siemens_refrigerator', 'single_level_home', 'single_oven',
    'ski_in_ski_out', 'smart_lock', 'smeg_induction_stove', 'smeg_refrigerator',
    'smeg_stainless_steel_oven', 'smoke_alarm', 'smoking_allowed',
    'sonos_bluetooth_sound_system', 'sonos_sound_system', 'sound_system',
    'sound_system_with_bluetooth_and_aux', 'stainless_steel_double_oven',
    'stainless_steel_electric_stove', 'stainless_steel_induction_stove',
    'stainless_steel_oven', 'stainless_steel_single_oven',
    'standalone_high_chair', 'standalone_high_chair_always_at_the_listing',
    'standalone_high_chair_available_upon_request', 'stove', 'sun_loungers',
    'table_corner_guards', 'toaster', 'trash_compactor', 'tv',
    'tv_with_apple_tv', 'tv_with_chromecast', 'tv_with_netflix',
    'tv_with_standard_cable', 'washer', 'washer_in_building', 'washer_in_unit',
    'waterfront', 'wifi', 'window_ac_unit', 'window_guards', 'wine_glasses',
    'email', 'phone', 'work_email', 'host_location_Amsterdam_Netherlands',
    'host_location_Aspudden_Sweden', 'host_location_Barnvik_Sweden',
    'host_location_Bergsj_Sweden', 'host_location_Enskede_Sweden',
    'host_location_Enskede_rsta_Vant_r_Sweden', 'host_location_Eskilstuna_Sweden',
    'host_location_Falun_Sweden', 'host_location_Goteborg_Sweden',
    'host_location_Gothenburg_Sweden', 'host_location_G_vle_Sweden',
    'host_location_G_teborg_Sweden', 'host_location_Haenertsburg_South_Africa',
    'host_location_Hamburg_Germany', 'host_location_Hammarby_Sweden',
    'host_location_Helsingborg_Sweden', 'host_location_Herf_lge_Denmark',
    'host_location_Hong_Kong', 'host_location_Huddinge_Sweden',
    'host_location_H_sselby_V_llingby_Sweden', 'host_location_India',
    'host_location_J_rf_lla_Sweden', 'host_location_Kampala_Uganda',
    'host_location_Kreuztal_Germany', 'host_location_Link_ping_Sweden',
    'host_location_London_United_Kingdom', 'host_location_Los_Angeles_CA',
    'host_location_Lund_Sweden', 'host_location_Madrid_Spain',
    'host_location_Maglaj_Bosnia_Herzegovina', 'host_location_Malm_Sweden',
    'host_location_Marbella_Spain', 'host_location_Mariefred_Sweden',
    'host_location_Marseille_France', 'host_location_Marshallton_DE',
    'host_location_Milan_Italy', 'host_location_Mississauga_Canada',
    'host_location_Mora_Sweden', 'host_location_Munich_Germany',
    'host_location_M_lnbo_Sweden', 'host_location_Nacka_Sweden',
    'host_location_Nanterre_France', 'host_location_New_York_NY',
    'host_location_Nyk_ping_Sweden', 'host_location_Oslo_Norway',
    'host_location_Palermo_Italy', 'host_location_Reykjav_k_Iceland',
    'host_location_Roanne_France', 'host_location_R_nninge_Sweden',
    'host_location_Saltsj_Duvn_s_Sweden', 'host_location_Sandnes_Norway',
    'host_location_Santa_Ana_El_Salvador', 'host_location_Santa_Monica_CA',
    'host_location_Skarpn_ck_Sweden', 'host_location_Skinnskatteberg_Sweden',
    'host_location_Sk_ne_County_Sweden', 'host_location_Sliema_Malta',
    'host_location_Sollentuna_Sweden', 'host_location_Solna_Sweden',
    'host_location_Sp_nga_Sweden', 'host_location_Stj_rnhov_Sweden',
    'host_location_Stockholm_County_Sweden', 'host_location_Stockholm_Sweden',
    'host_location_Stockholms_l_n_Sweden', 'host_location_Str_msund_Sweden',
    'host_location_Sundbyberg_Sweden', 'host_location_Svedala_Sweden', 'host_location_Sweden',
    'host_location_S_dermanland_County_Sweden', 'host_location_Tyres_Sweden',
    'host_location_Ume_Sweden', 'host_location_United_Kingdom',
    'host_location_Unknown', 'host_location_Uppsala_Sweden',
    'host_location_Varberg_Sweden', 'host_location_Visby_Sweden',
    'host_location_V_rmd_Sweden', 'host_location_V_stra_G_talands_l_n_Sweden',
    'host_location_Z_rich_Switzerland', 'host_location_agesta_Sweden',
    'host_location_lvsj_Sweden', 'host_response_time_a_few_days_or_more',
    'host_response_time_within_a_day', 'host_response_time_within_a_few_hours',
    'host_response_time_within_an_hour',
    'neighbourhood_cleansed_Enskede_rsta_Vant_rs',
    'neighbourhood_cleansed_Farsta', 'neighbourhood_cleansed_H_gersten_Liljeholmens',
    'neighbourhood_cleansed_H_sselby_V_llingby', 'neighbourhood_cleansed_Kungsholmens',
    'neighbourhood_cleansed_Norrmalms', 'neighbourhood_cleansed_Rinkeby_Tensta',
    'neighbourhood_cleansed_Skarpn_cks', 'neighbourhood_cleansed_Sk_rholmens',
    'neighbourhood_cleansed_Sp_nga_Tensta', 'neighbourhood_cleansed_S_dermalms',
    'neighbourhood_cleansed_lvsj', 'neighbourhood_cleansed_stermalms',
    'property_type_Boat', 'property_type_Camper_RV', 'property_type_Entire_cabin',
    'property_type_Entire_condo', 'property_type_Entire_cottage',
    'property_type_Entire_guest_suite', 'property_type_Entire_guesthouse',
    'property_type_Entire_home', 'property_type_Entire_loft',
    'property_type_Entire_rental_unit', 'property_type_Entire_serviced_apartment',
    'property_type_Entire_townhouse', 'property_type_Entire_villa',
    'property_type_Private_room_in_bed_and_breakfast',
    'property_type_Private_room_in_casa_particular',
    'property_type_Private_room_in_condo',
    'property_type_Private_room_in_guest_suite',
    'property_type_Private_room_in_guesthouse',
    'property_type_Private_room_in_home', 'property_type_Private_room_in_hostel',
    'property_type_Private_room_in_loft',
    'property_type_Private_room_in_rental_unit',
    'property_type_Private_room_in_serviced_apartment',
    'property_type_Private_room_in_tiny_home',
    'property_type_Private_room_in_townhouse', 'property_type_Private_room_in_villa',
    'property_type_Room_in_aparthotel', 'property_type_Room_in_boutique_hotel',
    'property_type_Room_in_hostel', 'property_type_Room_in_hotel',
    'property_type_Shared_room_in_condo', 'property_type_Shared_room_in_home',
    'property_type_Shared_room_in_hostel', 'property_type_Tiny_home',
    'room_type_Hotel_room', 'room_type_Private_room', 'room_type_Shared_room'
]

# --- START: Currency Conversion Configuration ---
# You need to sign up for a free API key at https://www.exchangerate-api.com/
# and replace 'YOUR_API_KEY' with your actual key.
# Free tier gives 1,500 requests/month, which is enough for local use.
EXCHANGE_RATE_API_KEY = "a5b90bd3bfd8e4a2f16083c5"  # <--- REPLACE WITH YOUR ACTUAL API KEY
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


# --- END: Currency Conversion Configuration ---


class ResultTab(QWidget):
    def __init__(self, parent_app, user_data, predicted_sek_price):
        super().__init__()
        self.parent_app = parent_app  # Reference to the main application for error messages
        self.user_data = user_data
        self.predicted_sek_price = predicted_sek_price
        self.exchange_rates = {}  # To store fetched rates

        self.init_ui()
        self._fetch_exchange_rates()  # Fetch rates when the tab is initialized
        self._update_currency_display()  # Update initial display

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        result_title = QLabel("Prediction Result")
        result_title.setAlignment(Qt.AlignCenter)
        result_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #F01C5C;")
        layout.addWidget(result_title)

        # Display user input for confirmation
        input_summary_label = QLabel("<b>Input Summary:</b>")
        layout.addWidget(input_summary_label)

        details_text = f"  Address: {self.user_data.get('address', 'N/A')}\n" \
                       f"  Number of Rooms: {self.user_data.get('n_rooms', 'N/A')}\n" \
                       f"  Amenities: {self.user_data.get('amenities_str', 'N/A')}\n" \
                       f"  Property Type: {self.user_data.get('property_type', 'N/A')}\n" \
                       f"  Room Type: {self.user_data.get('room_type', 'N/A')}"
        input_details = QLabel(details_text)
        input_details.setWordWrap(True)
        layout.addWidget(input_details)

        # Display initial prediction in SEK
        self.prediction_label = QLabel(f"<b>Predicted Price: SEK {self.predicted_sek_price:,.2f}</b>")
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.prediction_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #008000; margin-top: 20px; margin-bottom: 20px;")
        layout.addWidget(self.prediction_label)

        # --- Currency Conversion Section ---
        currency_h_layout = QHBoxLayout()
        currency_h_layout.setAlignment(Qt.AlignCenter)  # Center the currency controls

        currency_label = QLabel("Convert to:")
        currency_label.setStyleSheet("font-weight: 500;")
        currency_h_layout.addWidget(currency_label)

        self.currency_combo = QComboBox()
        # Populate with common currencies. The order matters for display.
        for code, name in COMMON_CURRENCIES.items():
            self.currency_combo.addItem(f"{code} - {name}", code)
        self.currency_combo.setCurrentText("SEK - Swedish Krona")  # Default to SEK
        self.currency_combo.setMinimumWidth(200)  # Give it some width
        self.currency_combo.currentIndexChanged.connect(self._update_currency_display)  # Connect to selection change

        currency_h_layout.addWidget(self.currency_combo)

        layout.addLayout(currency_h_layout)

        # Label to display converted price
        self.converted_price_label = QLabel(f"")
        self.converted_price_label.setAlignment(Qt.AlignCenter)
        self.converted_price_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-top: 10px; color: #333333;")
        layout.addWidget(self.converted_price_label)
        # --- End Currency Conversion Section ---

        layout.addStretch()  # Push content up

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
        selected_currency_code = self.currency_combo.currentData()  # Get the stored data (currency code)

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


class ApartmentPricePredictor(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Apartment Price Predictor")
        self.setMinimumSize(700, 550)  # Increased size for better layout

        # Path to the model
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
        self.model_path = os.path.join(project_root, "models", "best_lgbm_model.joblib")
        # Path to geojson
        self.geojson_path = os.path.join(project_root, "neighbourhoods.geojson")

        self.model = self._load_model()
        self.stockholm_neighborhoods_geojson = self._load_geojson()  # Load geojson

        # Initialize geolocator
        self.geolocator = Nominatim(user_agent="apartment_price_predictor_app")

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
                /* max-width: 380px; This was removed for better responsiveness */
            }
            QLineEdit, QComboBox {
                min-height: 30px; /* Standard height */
                /* max-width: 350px; This was removed for better responsiveness */
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
                spacing: 15px; /* Increased spacing between rows */
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
        # Use a QScrollArea for the form to ensure all content is visible if the window is small
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        form_container_widget = QWidget()  # Container for the actual form elements
        form_layout = QVBoxLayout(form_container_widget)
        form_layout.setContentsMargins(30, 30, 30, 30)  # Increased margins
        form_layout.setSpacing(20)  # Increased spacing between sections

        title = QLabel("Apartment Price Predictor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 25px; color: #F01C5C;")
        form_layout.addWidget(title)

        # Create a QFormLayout for input fields
        input_form_layout = QFormLayout()
        input_form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)  # Allow rows to wrap for responsiveness
        input_form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)  # Fields take available space
        input_form_layout.setSpacing(15)  # Spacing between rows in the form

        self.address = QLineEdit()
        self.address.setPlaceholderText("e.g., 123 Main St, Stockholm")
        input_form_layout.addRow(QLabel("Address:"), self.address)

        self.n_rooms = QComboBox()
        self.n_rooms.addItems([str(i) for i in range(1, 21)])  # Increased range to 1-20
        self.n_rooms.insertItem(0, "")  # Add an empty option as default
        self.n_rooms.setCurrentIndex(0)
        self.n_rooms.setEditable(True)  # Allow typing, but mainly for selection
        self.n_rooms.setMinimumWidth(150)
        self.n_rooms.lineEdit().setPlaceholderText("Select or type number of rooms")
        # Ensure the line edit within the QComboBox is not read-only, if direct typing is desired
        self.n_rooms.lineEdit().setReadOnly(False)
        input_form_layout.addRow(QLabel("Number of Rooms:"), self.n_rooms)

        self.amenities = QTextEdit()
        self.amenities.setPlaceholderText("e.g., wifi, kitchen, tv, pool")
        input_form_layout.addRow(QLabel("Amenities (comma-separated):"), self.amenities)

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

        form_layout.addLayout(input_form_layout)  # Add the QFormLayout to the main QVBoxLayout

        submit_button = QPushButton("Predict Price")
        submit_button.clicked.connect(self.process_and_show_results)
        form_layout.addWidget(submit_button, alignment=Qt.AlignCenter)
        form_layout.addStretch()  # Add stretch to push content up and prevent overlap if window is resized

        scroll_area.setWidget(form_container_widget)  # Set the form container as the scroll area's widget

        main_form_tab_layout = QVBoxLayout(self.form_tab)
        main_form_tab_layout.addWidget(scroll_area)  # Add the scroll area to the form tab's layout

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
            # You might want to return here or proceed without currency conversion
            # For now, let's proceed to show prediction but currency conversion will fail
            # return

        address_text = self.address.text().strip()
        n_rooms_text = self.n_rooms.currentText().strip()
        amenities_text = self.amenities.toPlainText().strip()
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
            "amenities_str": amenities_text,
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
            return "Unknown"

        point = Point(longitude, latitude)  # Shapely uses (longitude, latitude)

        for feature in self.stockholm_neighborhoods_geojson['features']:
            if 'geometry' in feature and 'properties' in feature and 'neighbourhood' in feature['properties']:
                try:
                    # Handle both Polygon and MultiPolygon geometries
                    geom_type = feature['geometry']['type']
                    coordinates = feature['geometry']['coordinates']

                    if geom_type == 'Polygon':
                        polygon_geometry = Polygon(coordinates[0])
                    elif geom_type == 'MultiPolygon':
                        # For MultiPolygon, check each polygon within it
                        is_in_polygon = False
                        for poly_coords in coordinates:
                            polygon_geometry = Polygon(poly_coords[0])  # Assuming simple interior rings
                            if polygon_geometry.contains(point):
                                is_in_polygon = True
                                break
                        if is_in_polygon:
                            return feature['properties']['neighbourhood']
                        continue  # If not found in any part of MultiPolygon, move to next feature
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
        print(f"Address: {user_data['address']}, Lat: {latitude}, Lon: {longitude}, Neighborhood: {neighborhood}")

        # Initialize all feature columns to 0 or default values
        input_data = {col: 0 for col in ALL_TRAINING_COLUMNS}

        # Set specific numerical features
        input_data['latitude'] = latitude
        input_data['longitude'] = longitude
        input_data['accommodates'] = user_data['n_rooms']  # Assuming n_rooms is proxy for accommodates
        input_data['bedrooms'] = user_data['n_rooms']  # Assuming n_rooms is proxy for bedrooms
        input_data['beds'] = user_data['n_rooms'] * 1.5  # A common heuristic for beds
        input_data['minimum_nights'] = 1  # Default value, can be made user input
        input_data['maximum_nights'] = 1125  # Default value (365 * 3), can be made user input
        input_data['availability_30'] = 20  # Default value, can be made user input
        input_data['availability_60'] = 40
        input_data['availability_90'] = 60
        input_data['availability_365'] = 200
        input_data['number_of_reviews'] = 0  # No reviews yet, as per initial prompt context
        input_data['review_scores_rating'] = 0
        input_data['review_scores_accuracy'] = 0
        input_data['review_scores_cleanliness'] = 0
        input_data['review_scores_checkin'] = 0
        input_data['review_scores_communication'] = 0
        input_data['review_scores_location'] = 0
        input_data['review_scores_value'] = 0
        input_data['instant_bookable'] = 0  # Default to not instant bookable
        input_data['calculated_host_listings_count'] = 1  # Assuming this is the only listing for host
        input_data['reviews_per_month'] = 0  # No reviews
        input_data['host_duration_days'] = 1000  # Example host duration
        input_data['num_bathrooms'] = max(1, user_data['n_rooms'] // 2)  # Heuristic for bathrooms
        input_data['is_shared_bath'] = 0
        input_data['num_amenities'] = len(user_data['amenities_str'].split(',')) if user_data['amenities_str'] else 0
        input_data['num_host_verifications'] = 3  # Example number
        input_data['never_reviewed'] = 1  # Assuming new listing
        input_data['days_since_last_review'] = 9999  # Large number for never reviewed
        input_data['days_since_first_review'] = 9999  # Large number for never reviewed
        input_data['desc_sentiment'] = 0.5  # Neutral sentiment

        # Set host-related features (example values, these would ideally come from more input)
        input_data['host_since'] = 365 * 3  # Example: host joined 3 years ago
        input_data['host_response_rate'] = 0.95
        input_data['host_acceptance_rate'] = 0.90
        input_data['host_is_superhost'] = 0
        input_data['host_listings_count'] = 1
        input_data['host_total_listings_count'] = 1
        input_data['host_has_profile_pic'] = 1
        input_data['host_identity_verified'] = 1

        # Process amenities - Set corresponding amenity columns to 1 if present
        if user_data['amenities_str']:
            amenities_list = [re.sub(r'[^a-z0-9_]', '', a.strip().lower().replace(' ', '_')) for a in
                              user_data['amenities_str'].split(',')]
            for amenity in amenities_list:
                # Map some common amenity inputs to potential training columns
                if amenity == 'wifi' and 'wifi' in input_data:
                    input_data['wifi'] = 1
                elif amenity == 'kitchen' and 'kitchen' in input_data:
                    input_data['kitchen'] = 1
                elif amenity == 'tv' and 'tv' in input_data:
                    input_data['tv'] = 1
                elif amenity == 'pool' and 'pool' in input_data:
                    input_data['pool'] = 1
                elif amenity == 'air_conditioning' and 'air_conditioning' in input_data:
                    input_data['air_conditioning'] = 1
                elif amenity == 'heating' and 'heating' in input_data:
                    input_data['heating'] = 1
                elif amenity == 'washer' and 'washer' in input_data:
                    input_data['washer'] = 1
                elif amenity == 'dryer' and 'dryer' in input_data:
                    input_data['dryer'] = 1
                elif amenity == 'essentials' and 'essentials' in input_data:
                    input_data['essentials'] = 1
                elif amenity == 'shampoo' and 'shampoo' in input_data:
                    input_data['shampoo'] = 1
                elif amenity == 'hangers' and 'hangers' in input_data:
                    input_data['hangers'] = 1
                elif amenity == 'iron' and 'iron' in input_data:
                    input_data['iron'] = 1
                elif amenity == 'hair_dryer' and 'hair_dryer' in input_data:
                    input_data['hair_dryer'] = 1
                elif amenity == 'private_entrance' and 'private_entrance' in input_data:
                    input_data['private_entrance'] = 1
                elif amenity == 'fireplace' and 'indoor_fireplace' in input_data:
                    input_data['indoor_fireplace'] = 1
                elif amenity == 'gym' and 'gym' in input_data:
                    input_data['gym'] = 1
                elif amenity == 'hot_tub' and 'hot_tub' in input_data:
                    input_data['hot_tub'] = 1
                elif amenity == 'free_parking' and 'free_parking_on_premises' in input_data:
                    input_data['free_parking_on_premises'] = 1
                elif amenity == 'self_check_in' and 'self_check_in' in input_data:
                    input_data['self_check_in'] = 1
                # Add more amenity mappings as needed, based on your ALL_TRAINING_COLUMNS

        # Set one-hot encoded categorical features
        # For neighborhood
        neighborhood_col = f'neighbourhood_cleansed_{neighborhood.replace(" ", "_").replace("-", "_").replace("&", "and")}'
        if neighborhood_col in input_data:
            input_data[neighborhood_col] = 1
        else:
            print(
                f"Warning: Neighborhood column '{neighborhood_col}' not found in training columns. This might affect prediction accuracy.")

        # For property_type
        # Clean and map property type to match possible training columns
        property_type_cleaned = user_data['property_type'].replace(" ", "_").replace("/", "_").lower()
        # Handle "Entire home/apt" which is often mapped to "Entire home" or "Entire rental unit"
        if property_type_cleaned == "entire_home_apt":
            if "property_type_Entire_home" in input_data:
                input_data["property_type_Entire_home"] = 1
            elif "property_type_Entire_rental_unit" in input_data:
                input_data["property_type_Entire_rental_unit"] = 1
        else:
            prop_col_name = f'property_type_{user_data["property_type"].replace(" ", "_").replace("/", "_").replace("-", "_")}'
            # Special handling for "Hotel room" in property_type if it sometimes appears as "Room in hotel"
            if prop_col_name == 'property_type_Hotel_room' and 'property_type_Room_in_hotel' in input_data:
                input_data['property_type_Room_in_hotel'] = 1
            elif prop_col_name in input_data:
                input_data[prop_col_name] = 1
            else:
                print(
                    f"Warning: Property type column '{prop_col_name}' not found in training columns. This might affect prediction accuracy.")

        # For room_type
        room_type_cleaned = user_data['room_type'].replace(" ", "_").replace("/", "_").lower()
        if room_type_cleaned == "entire_home_apt":  # Map "Entire home/apt" to "Entire_home_apt" if it exists, or just "Entire home"
            if "room_type_Entire_home_apt" in input_data:
                input_data["room_type_Entire_home_apt"] = 1
            elif "room_type_Entire_home" in input_data:  # Fallback
                input_data["room_type_Entire_home"] = 1
        else:
            room_col_name = f'room_type_{user_data["room_type"].replace(" ", "_").replace("/", "_").replace("-", "_")}'
            if room_col_name in input_data:
                input_data[room_col_name] = 1
            else:
                print(
                    f"Warning: Room type column '{room_col_name}' not found in training columns. This might affect prediction accuracy.")

        # Create a DataFrame from the prepared input data
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